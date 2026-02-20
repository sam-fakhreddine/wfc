"""CLAUDE.md Remediation Orchestrator.

Chains the 5 pipeline agents in sequence:
  1. Context Mapper  (local, deterministic)
  2. Analyst         (LLM or heuristic fallback)
  3. Fixer           (LLM or minimal trim fallback)
  4. QA Validator    (rule-based + optional LLM)
  5. Reporter        (LLM or rule-based fallback)

The orchestrator is fail-open: errors in any agent are logged and the pipeline
continues with safe defaults. The original file is NEVER modified automatically —
the caller is responsible for writing the rewritten content.

Usage (no LLM):
    from wfc.scripts.orchestrators.claude_md.orchestrator import remediate
    result = remediate("/path/to/project")
    print(result.report)

Usage (with Anthropic SDK):
    import anthropic
    client = anthropic.Anthropic()

    def make_response_fn(system_prompt: str):
        def fn(user_message: str) -> str:
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=8192,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return msg.content[0].text
        return fn

    result = remediate(
        "/path/to/project",
        analyst_response_fn=make_response_fn(ANALYST_PROMPT),
        fixer_response_fn=make_response_fn(FIXER_PROMPT),
        qa_response_fn=make_response_fn(QA_VALIDATOR_PROMPT),
        reporter_response_fn=make_response_fn(REPORTER_PROMPT),
    )
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .analyst import analyze
from .context_mapper import map_project
from .fixer import fix
from .qa_validator import validate
from .reporter import report
from .schemas import ExtractedFile, RemediationResult

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2


@dataclass
class PipelineConfig:
    """Configuration for the remediation pipeline."""

    max_qa_retries: int = _MAX_RETRIES
    skip_if_grade_a: bool = True


def remediate(
    project_root: str | Path,
    *,
    analyst_response_fn: Callable[[str], str] | None = None,
    fixer_response_fn: Callable[[str], str] | None = None,
    qa_response_fn: Callable[[str], str] | None = None,
    reporter_response_fn: Callable[[str], str] | None = None,
    config: PipelineConfig | None = None,
) -> RemediationResult:
    """Run the full CLAUDE.md remediation pipeline.

    Args:
        project_root: Path to the project root directory containing CLAUDE.md.
        analyst_response_fn: Callable(prompt) -> response for the Analyst agent.
        fixer_response_fn: Callable(prompt) -> response for the Fixer agent.
        qa_response_fn: Callable(prompt) -> response for the QA Validator.
        reporter_response_fn: Callable(prompt) -> response for the Reporter.
        config: Pipeline configuration.

    Returns:
        RemediationResult. Call result.succeeded to check overall success.
        The original file is NOT modified — the caller writes result.rewritten_content
        after reviewing the report.
    """
    cfg = config or PipelineConfig()
    root = Path(project_root).resolve()
    claude_md_path = root / "CLAUDE.md"

    logger.info("Phase 1: Context Mapper — %s", root)
    try:
        manifest = map_project(root)
    except Exception:
        logger.exception("Context Mapper failed")
        return RemediationResult(
            project_root=str(root),
            claude_md_path=str(claude_md_path),
            grade_before="?",
            grade_after="?",
            verdict="FAIL",
            original_lines=0,
            rewritten_lines=0,
            original_instructions=0,
            rewritten_instructions=0,
            rewritten_content=None,
            error="Context Mapper failed — see logs",
        )

    original_lines = manifest.get("claude_md", {}).get("total_lines", 0)

    try:
        original_content = (
            claude_md_path.read_text(errors="replace") if claude_md_path.exists() else ""
        )
    except OSError:
        original_content = ""

    logger.info("Phase 2: Analyst")
    try:
        diagnosis = analyze(original_content, manifest, response_fn=analyst_response_fn)
    except Exception:
        logger.exception("Analyst failed; using minimal diagnosis")
        diagnosis = {
            "overall_grade": "C",
            "rewrite_recommended": True,
            "rewrite_scope": "full",
            "issues": [],
            "instruction_budget_analysis": {
                "claude_md_instructions": 0,
                "budget_status": "unknown",
            },
        }

    grade_before = diagnosis.get("overall_grade", "?")
    original_instructions = diagnosis.get("instruction_budget_analysis", {}).get(
        "claude_md_instructions", 0
    )

    if cfg.skip_if_grade_a and grade_before == "A":
        logger.info("Grade A — no rewrite needed")
        return RemediationResult(
            project_root=str(root),
            claude_md_path=str(claude_md_path),
            grade_before="A",
            grade_after="A",
            verdict="PASS",
            original_lines=original_lines,
            rewritten_lines=original_lines,
            original_instructions=original_instructions,
            rewritten_instructions=original_instructions,
            rewritten_content=None,
            report="No rewrite needed — file is grade A.",
        )

    revision_notes = ""
    fixer_output: dict = {}
    validation: dict = {}

    for attempt in range(cfg.max_qa_retries + 1):
        logger.info("Phase 3: Fixer (attempt %d)", attempt + 1)
        try:
            fixer_output = fix(
                original_content,
                manifest,
                diagnosis,
                response_fn=fixer_response_fn,
                revision_notes=revision_notes,
            )
        except Exception:
            logger.exception("Fixer failed on attempt %d", attempt + 1)
            fixer_output = {
                "rewritten_content": original_content,
                "changelog": ["[ERROR] Fixer failed — original preserved"],
                "migration_plan": "",
                "extracted_files": [],
                "metrics": {"original_lines": original_lines, "rewritten_lines": original_lines},
            }

        logger.info("Phase 4: QA Validator (attempt %d)", attempt + 1)
        try:
            validation = validate(
                original_content,
                manifest,
                diagnosis,
                fixer_output,
                response_fn=qa_response_fn,
            )
        except Exception:
            logger.exception("QA Validator failed; treating as PASS_WITH_NOTES")
            validation = {
                "verdict": "PASS_WITH_NOTES",
                "final_recommendation": "ship",
                "revision_notes": "",
                "budget_check": {},
            }

        verdict = validation.get("verdict", "PASS")
        if verdict != "FAIL":
            break

        revision_notes = validation.get("revision_notes", "")
        logger.info("QA returned FAIL — retrying Fixer (notes: %s)", revision_notes)

    logger.info("Phase 5: Reporter")
    try:
        final_report = report(
            manifest,
            diagnosis,
            fixer_output,
            validation,
            response_fn=reporter_response_fn,
        )
    except Exception:
        logger.exception("Reporter failed; generating minimal report")
        final_report = f"Remediation complete. Grade: {grade_before}. Verdict: {verdict}."

    rewritten_content = fixer_output.get("rewritten_content") or None
    if validation.get("verdict") == "FAIL":
        rewritten_content = None

    extracted = [
        ExtractedFile(path=f["path"], content=f["content"])
        for f in fixer_output.get("extracted_files", [])
        if isinstance(f, dict) and "path" in f and "content" in f
    ]

    metrics = fixer_output.get("metrics", {})
    rewritten_lines = metrics.get("rewritten_lines", original_lines)
    rewritten_instructions = metrics.get(
        "rewritten_instructions",
        diagnosis.get("instruction_budget_analysis", {}).get("claude_md_instructions", 0),
    )

    if rewritten_content:
        new_lines = len(rewritten_content.splitlines())
        if new_lines < 100 and rewritten_instructions < 50:
            grade_after = "A"
        elif new_lines < 200 and rewritten_instructions < 80:
            grade_after = "B"
        else:
            grade_after = "C"
    else:
        grade_after = grade_before

    return RemediationResult(
        project_root=str(root),
        claude_md_path=str(claude_md_path),
        grade_before=grade_before,
        grade_after=grade_after,
        verdict=validation.get("verdict", "PASS"),
        original_lines=original_lines,
        rewritten_lines=rewritten_lines,
        original_instructions=original_instructions,
        rewritten_instructions=rewritten_instructions,
        rewritten_content=rewritten_content,
        extracted_files=extracted,
        migration_plan=fixer_output.get("migration_plan", ""),
        changelog=fixer_output.get("changelog", []),
        report=final_report,
    )
