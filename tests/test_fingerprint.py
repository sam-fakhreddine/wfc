"""Tests for finding deduplication with exact fingerprinting."""

from __future__ import annotations

from wfc.scripts.orchestrators.review.fingerprint import DeduplicatedFinding, Fingerprinter


def _finding(
    file: str = "src/app.py",
    line_start: int = 10,
    line_end: int | None = None,
    category: str = "injection",
    severity: float = 7.0,
    confidence: float = 8.0,
    description: str = "SQL injection risk",
    remediation: str | None = "Use parameterized queries",
    reviewer_id: str = "security",
) -> dict:
    f = {
        "file": file,
        "line_start": line_start,
        "category": category,
        "severity": severity,
        "confidence": confidence,
        "description": description,
        "reviewer_id": reviewer_id,
    }
    if line_end is not None:
        f["line_end"] = line_end
    if remediation is not None:
        f["remediation"] = remediation
    return f


class TestFingerprinting:
    """Basic fingerprint computation tests."""

    def setup_method(self):
        self.fp = Fingerprinter()

    def test_same_inputs_same_fingerprint(self):
        a = self.fp.compute_fingerprint("src/app.py", 10, "injection")
        b = self.fp.compute_fingerprint("src/app.py", 10, "injection")
        assert a == b

    def test_different_file_different_fingerprint(self):
        a = self.fp.compute_fingerprint("src/app.py", 10, "injection")
        b = self.fp.compute_fingerprint("src/other.py", 10, "injection")
        assert a != b

    def test_different_category_different_fingerprint(self):
        a = self.fp.compute_fingerprint("src/app.py", 10, "injection")
        b = self.fp.compute_fingerprint("src/app.py", 10, "resource_leak")
        assert a != b

    def test_lines_within_tolerance_same_fingerprint(self):
        """Lines 10 and 11 both normalize to 9 (10//3*3=9, 11//3*3=9)."""
        a = self.fp.compute_fingerprint("src/app.py", 10, "injection")
        b = self.fp.compute_fingerprint("src/app.py", 11, "injection")
        assert a == b

    def test_lines_outside_tolerance_different_fingerprint(self):
        """Lines 10 and 15: 10//3*3=9, 15//3*3=15 -> different."""
        a = self.fp.compute_fingerprint("src/app.py", 10, "injection")
        b = self.fp.compute_fingerprint("src/app.py", 15, "injection")
        assert a != b

    def test_normalize_line(self):
        assert Fingerprinter.normalize_line(0) == 0
        assert Fingerprinter.normalize_line(1) == 0
        assert Fingerprinter.normalize_line(2) == 0
        assert Fingerprinter.normalize_line(3) == 3
        assert Fingerprinter.normalize_line(10) == 9
        assert Fingerprinter.normalize_line(11) == 9
        assert Fingerprinter.normalize_line(12) == 12
        assert Fingerprinter.normalize_line(15) == 15

    def test_fingerprint_is_hex_sha256(self):
        fp = self.fp.compute_fingerprint("f.py", 1, "bug")
        assert len(fp) == 64
        assert all(c in "0123456789abcdef" for c in fp)


class TestDeduplication:
    """Merging logic tests."""

    def setup_method(self):
        self.fp = Fingerprinter()

    def test_two_reviewers_same_issue_merged(self):
        findings = [
            _finding(reviewer_id="security", severity=8.0, description="Leak found"),
            _finding(reviewer_id="reliability", severity=7.0, description="Resource leak"),
        ]
        result = self.fp.deduplicate(findings)
        assert len(result) == 1
        assert result[0].k == 2
        assert set(result[0].reviewer_ids) == {"security", "reliability"}

    def test_three_reviewers_same_issue_merged(self):
        findings = [
            _finding(reviewer_id="security", severity=8.0),
            _finding(reviewer_id="reliability", severity=7.0),
            _finding(reviewer_id="correctness", severity=6.0),
        ]
        result = self.fp.deduplicate(findings)
        assert len(result) == 1
        assert result[0].k == 3

    def test_different_issues_no_merging(self):
        findings = [
            _finding(file="a.py", category="injection", reviewer_id="security"),
            _finding(file="b.py", category="resource_leak", reviewer_id="reliability"),
        ]
        result = self.fp.deduplicate(findings)
        assert len(result) == 2
        assert all(r.k == 1 for r in result)

    def test_severity_takes_maximum(self):
        findings = [
            _finding(reviewer_id="security", severity=6.0),
            _finding(reviewer_id="reliability", severity=9.0),
        ]
        result = self.fp.deduplicate(findings)
        assert result[0].severity == 9.0

    def test_confidence_takes_maximum(self):
        findings = [
            _finding(reviewer_id="security", confidence=5.0),
            _finding(reviewer_id="reliability", confidence=9.0),
        ]
        result = self.fp.deduplicate(findings)
        assert result[0].confidence == 9.0

    def test_primary_description_from_highest_severity(self):
        findings = [
            _finding(reviewer_id="security", severity=6.0, description="Low sev desc"),
            _finding(reviewer_id="reliability", severity=9.0, description="High sev desc"),
        ]
        result = self.fp.deduplicate(findings)
        assert result[0].description == "High sev desc"

    def test_all_unique_descriptions_preserved(self):
        findings = [
            _finding(reviewer_id="security", description="Desc A"),
            _finding(reviewer_id="reliability", description="Desc B"),
            _finding(reviewer_id="correctness", description="Desc A"),
        ]
        result = self.fp.deduplicate(findings)
        assert sorted(result[0].descriptions) == ["Desc A", "Desc B"]

    def test_all_unique_remediations_preserved(self):
        findings = [
            _finding(reviewer_id="security", remediation="Fix A"),
            _finding(reviewer_id="reliability", remediation="Fix B"),
            _finding(reviewer_id="correctness", remediation="Fix A"),
        ]
        result = self.fp.deduplicate(findings)
        assert sorted(result[0].remediation) == ["Fix A", "Fix B"]

    def test_reviewer_ids_all_listed(self):
        findings = [
            _finding(reviewer_id="security"),
            _finding(reviewer_id="reliability"),
            _finding(reviewer_id="performance"),
        ]
        result = self.fp.deduplicate(findings)
        assert set(result[0].reviewer_ids) == {"security", "reliability", "performance"}

    def test_reviewer_id_map_input_mode(self):
        """reviewer_id_map input produces identical results to flat list."""
        sec_finding = _finding(reviewer_id="security", severity=8.0)
        rel_finding = _finding(reviewer_id="reliability", severity=7.0)

        flat_result = self.fp.deduplicate([sec_finding, rel_finding])

        sec_no_rid = {k: v for k, v in sec_finding.items() if k != "reviewer_id"}
        rel_no_rid = {k: v for k, v in rel_finding.items() if k != "reviewer_id"}

        map_result = self.fp.deduplicate(
            [],
            reviewer_id_map={"security": [sec_no_rid], "reliability": [rel_no_rid]},
        )

        assert len(flat_result) == len(map_result)
        assert flat_result[0].k == map_result[0].k
        assert flat_result[0].fingerprint == map_result[0].fingerprint
        assert set(flat_result[0].reviewer_ids) == set(map_result[0].reviewer_ids)


class TestEdgeCases:
    """Edge case handling."""

    def setup_method(self):
        self.fp = Fingerprinter()

    def test_empty_findings(self):
        assert self.fp.deduplicate([]) == []

    def test_single_finding(self):
        result = self.fp.deduplicate([_finding()])
        assert len(result) == 1
        assert result[0].k == 1
        assert isinstance(result[0], DeduplicatedFinding)

    def test_missing_line_end(self):
        finding = _finding(line_end=None)
        result = self.fp.deduplicate([finding])
        assert result[0].line_end == result[0].line_start

    def test_missing_remediation(self):
        finding = _finding(remediation=None)
        result = self.fp.deduplicate([finding])
        assert result[0].remediation == []

    def test_reviewer_id_map_empty(self):
        assert self.fp.deduplicate([], reviewer_id_map={}) == []

    def test_malformed_finding_missing_all_required_keys_skipped(self):
        """A finding missing 'file', 'line_start', and 'category' is skipped."""
        malformed = {"description": "no required keys", "severity": 8.0, "reviewer_id": "security"}
        result = self.fp.deduplicate([malformed])
        assert result == []

    def test_malformed_finding_missing_one_key_skipped(self):
        """A finding missing 'category' alone is skipped and does not abort dedup."""
        malformed = {
            "file": "app.py",
            "line_start": 10,
            "description": "no category",
            "reviewer_id": "security",
        }
        good = _finding(file="b.py", category="injection", reviewer_id="reliability")
        result = self.fp.deduplicate([malformed, good])
        assert len(result) == 1
        assert result[0].file == "b.py"

    def test_malformed_finding_does_not_abort_valid_findings(self):
        """Mix of malformed and valid findings: valid ones are returned, malformed skipped."""
        findings = [
            _finding(file="a.py", category="injection", reviewer_id="security"),
            {
                "description": "malformed - missing file/line_start/category",
                "severity": 9.0,
                "reviewer_id": "reliability",
            },
            _finding(file="b.py", category="resource_leak", reviewer_id="correctness"),
        ]
        result = self.fp.deduplicate(findings)
        assert len(result) == 2
        files = {r.file for r in result}
        assert files == {"a.py", "b.py"}

    def test_all_malformed_findings_returns_empty(self):
        """When every finding is malformed, the result is an empty list."""
        findings = [
            {"description": "bad1", "reviewer_id": "security"},
            {"file": "x.py", "reviewer_id": "reliability"},
        ]
        result = self.fp.deduplicate(findings)
        assert result == []


class TestSorting:
    """Results sorted by severity descending."""

    def setup_method(self):
        self.fp = Fingerprinter()

    def test_sorted_by_severity_descending(self):
        findings = [
            _finding(file="a.py", category="low", severity=3.0, reviewer_id="r1"),
            _finding(file="b.py", category="high", severity=9.0, reviewer_id="r2"),
            _finding(file="c.py", category="mid", severity=6.0, reviewer_id="r3"),
        ]
        result = self.fp.deduplicate(findings)
        severities = [r.severity for r in result]
        assert severities == [9.0, 6.0, 3.0]

    def test_merged_severity_affects_sort(self):
        """After merging, the max severity determines sort position."""
        findings = [
            _finding(file="a.py", category="low", severity=2.0, reviewer_id="r1"),
            _finding(file="b.py", category="mid", severity=5.0, reviewer_id="r2"),
            _finding(file="b.py", category="mid", severity=8.0, reviewer_id="r3"),
        ]
        result = self.fp.deduplicate(findings)
        assert len(result) == 2
        assert result[0].severity == 8.0
        assert result[1].severity == 2.0
