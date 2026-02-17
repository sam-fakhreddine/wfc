"""Finding deduplication with exact fingerprinting.

Deduplicates findings across multiple reviewers using SHA-256 fingerprints
with line-number tolerance bucketing. When duplicates are found, findings
are merged: highest severity wins, all unique descriptions and remediations
are preserved, and the reviewer count (k) is tracked for the consensus score.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DeduplicatedFinding:
    """A finding after deduplication across reviewers."""

    fingerprint: str
    file: str
    line_start: int
    line_end: int
    category: str
    severity: float
    confidence: float
    description: str
    descriptions: list[str]
    remediation: list[str]
    reviewer_ids: list[str]
    k: int


class Fingerprinter:
    """Deduplicate findings across reviewers using SHA-256 fingerprinting."""

    @staticmethod
    def normalize_line(line_start: int) -> int:
        """Normalize line number to +/-3 tolerance bucket."""
        return (line_start // 3) * 3

    def compute_fingerprint(self, file_path: str, line_start: int, category: str) -> str:
        """Compute the SHA-256 fingerprint hash for a finding."""
        normalized = self.normalize_line(line_start)
        raw = f"{file_path}:{normalized}:{category}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def deduplicate(
        self,
        findings: list[dict],
        reviewer_id_map: dict[str, list[dict]] | None = None,
    ) -> list[DeduplicatedFinding]:
        """Deduplicate findings across reviewers.

        Args:
            findings: Flat list of finding dicts (each must have reviewer_id).
            reviewer_id_map: Alternative input mapping reviewer_id to findings.
                If provided, *findings* is ignored and reviewer_id is taken
                from the map keys.

        Returns:
            List of DeduplicatedFinding sorted by severity descending.
        """
        if reviewer_id_map is not None:
            flat: list[dict] = []
            for rid, flist in reviewer_id_map.items():
                for f in flist:
                    flat.append({**f, "reviewer_id": rid})
        else:
            flat = list(findings)

        if not flat:
            return []

        required_keys = {"file", "line_start", "category"}
        valid: list[dict] = []
        for f in flat:
            if not required_keys.issubset(f.keys()):
                missing = required_keys - f.keys()
                logger.warning(
                    "Skipping malformed finding (missing keys: %s): %r",
                    sorted(missing),
                    f,
                )
                continue
            valid.append(f)
        flat = valid

        if not flat:
            return []

        buckets: dict[str, list[dict]] = {}
        for f in flat:
            fp = self.compute_fingerprint(
                f.get("file", ""),
                f.get("line_start", 0),
                f.get("category", "unknown"),
            )
            buckets.setdefault(fp, []).append(f)

        results: list[DeduplicatedFinding] = []
        for fp, group in buckets.items():
            results.append(self._merge(fp, group))

        results.sort(key=lambda r: r.severity, reverse=True)
        return results

    @staticmethod
    def _unique_values(items: list[dict], key: str, default: str = "") -> list[str]:
        """Collect unique non-empty values for *key* across items, preserving order."""
        seen: set[str] = set()
        result: list[str] = []
        for item in items:
            val = item.get(key, default)
            if val and val not in seen:
                seen.add(val)
                result.append(val)
        return result

    @staticmethod
    def _merge(fingerprint: str, group: list[dict]) -> DeduplicatedFinding:
        """Merge a group of duplicate findings into one."""
        group_sorted = sorted(group, key=lambda f: f.get("severity", 0), reverse=True)
        primary = group_sorted[0]

        descriptions = Fingerprinter._unique_values(group_sorted, "description")
        remediations = Fingerprinter._unique_values(group_sorted, "remediation")
        reviewer_ids = Fingerprinter._unique_values(group_sorted, "reviewer_id", default="unknown")

        max_severity = max(f.get("severity", 0) for f in group)
        max_confidence = max(f.get("confidence", 0) for f in group)

        line_end = primary.get("line_end", primary.get("line_start", 0))

        return DeduplicatedFinding(
            fingerprint=fingerprint,
            file=primary.get("file", ""),
            line_start=primary.get("line_start", 0),
            line_end=line_end,
            category=primary.get("category", "unknown"),
            severity=max_severity,
            confidence=max_confidence,
            description=primary.get("description", ""),
            descriptions=descriptions,
            remediation=remediations,
            reviewer_ids=reviewer_ids,
            k=len(reviewer_ids),
        )
