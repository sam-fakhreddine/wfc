#!/usr/bin/env python3
"""
GitHub CLI helper utilities.

Provides auto-detection of owner/repo/PR, robust error handling, and
common GitHub operations so callers never need to construct raw gh commands.

All public functions raise GHError on failure — never return None silently.

Usage as library:
    from wfc.scripts.github.gh_helpers import detect_repo, detect_current_pr, get_pr_info

Usage as CLI (quick diagnostics):
    python gh_helpers.py info          # Show detected repo + current PR
    python gh_helpers.py checks        # Show PR check status
    python gh_helpers.py request-review copilot-pull-request-reviewer[bot]
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import Any, Optional


class GHError(RuntimeError):
    """Raised when a gh CLI call fails or returns unexpected output."""

    def __init__(self, message: str, stderr: str = "", returncode: int = 0):
        super().__init__(message)
        self.stderr = stderr
        self.returncode = returncode


def _run_gh(
    args: list[str],
    *,
    input_data: Optional[str] = None,
    timeout: int = 30,
    retries: int = 2,
    retry_delay: float = 2.0,
) -> str:
    """
    Run a gh CLI command and return stdout.

    Retries on transient failures (rate limit, network timeout).
    Raises GHError on persistent failure.
    """
    cmd = ["gh"] + args

    for attempt in range(retries + 1):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                input=input_data,
            )
        except subprocess.TimeoutExpired:
            if attempt < retries:
                time.sleep(retry_delay)
                continue
            raise GHError(f"gh command timed out after {timeout}s: {' '.join(cmd)}")

        if result.returncode == 0:
            return result.stdout

        stderr = result.stderr.strip()

        transient = any(
            kw in stderr.lower()
            for kw in ("rate limit", "timeout", "connection reset", "temporary", "503", "502")
        )
        if transient and attempt < retries:
            time.sleep(retry_delay * (attempt + 1))
            continue

        if (
            "authentication" in stderr.lower()
            or "401" in stderr
            or "not logged in" in stderr.lower()
        ):
            raise GHError(
                "GitHub authentication failed. Run: gh auth login",
                stderr=stderr,
                returncode=result.returncode,
            )

        raise GHError(
            f"gh {args[0]} failed (exit {result.returncode}): {stderr or '(no stderr)'}",
            stderr=stderr,
            returncode=result.returncode,
        )

    raise GHError(f"gh command failed after {retries + 1} attempts: {' '.join(cmd)}")


def gh_api(
    path: str, *, method: str = "GET", fields: Optional[dict] = None, timeout: int = 30
) -> Any:
    """
    Call the GitHub REST API via `gh api`.

    Returns parsed JSON. Raises GHError on failure.

    Example:
        data = gh_api("/repos/owner/repo/pulls/42")
        data = gh_api("/repos/owner/repo/pulls/42/requested_reviewers",
                      method="POST", fields={"reviewers": ["copilot-pull-request-reviewer[bot]"]})
    """
    args = ["api", path, "--method", method]
    if fields:
        for key, value in fields.items():
            if isinstance(value, (list, dict)):
                args += ["--field", f"{key}={json.dumps(value)}"]
            else:
                args += ["-f", f"{key}={value}"]

    raw = _run_gh(args, timeout=timeout)
    try:
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        raise GHError(f"gh api returned non-JSON output: {raw[:200]}") from exc


def gh_graphql(query: str, *, timeout: int = 30, **variables: Any) -> dict:
    """
    Execute a GitHub GraphQL query via `gh api graphql`.

    Raises GHError on HTTP or GraphQL-level errors.
    """
    args = ["api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if isinstance(value, int):
            args += ["-F", f"{key}={value}"]
        else:
            args += ["-f", f"{key}={value}"]

    raw = _run_gh(args, timeout=timeout)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GHError(f"GraphQL response is not JSON: {raw[:200]}") from exc

    if "errors" in data:
        messages = "; ".join(e.get("message", str(e)) for e in data["errors"])
        raise GHError(f"GraphQL errors: {messages}")

    return data


@dataclass
class RepoInfo:
    owner: str
    name: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


_repo_cache: Optional[RepoInfo] = None


def detect_repo() -> RepoInfo:
    """
    Auto-detect the current GitHub repo (owner + name).

    Uses `gh repo view` which reads from the current directory's git remote.
    Result is cached for the process lifetime.

    Raises GHError if not in a GitHub repo.
    """
    global _repo_cache
    if _repo_cache is not None:
        return _repo_cache

    try:
        raw = _run_gh(["repo", "view", "--json", "owner,name"])
        data = json.loads(raw)
        _repo_cache = RepoInfo(owner=data["owner"]["login"], name=data["name"])
        return _repo_cache
    except (json.JSONDecodeError, KeyError) as exc:
        raise GHError("Could not parse repo info from gh repo view") from exc


_pr_cache: Optional[int] = None


def detect_current_pr() -> int:
    """
    Auto-detect the PR number for the current branch.

    Uses `gh pr view` from the current directory.
    Raises GHError if no open PR is found for the current branch.
    """
    global _pr_cache
    if _pr_cache is not None:
        return _pr_cache

    try:
        raw = _run_gh(["pr", "view", "--json", "number"])
        data = json.loads(raw)
        _pr_cache = data["number"]
        return _pr_cache
    except GHError as exc:
        raise GHError(
            "No open PR found for the current branch. Create one with: gh pr create"
        ) from exc
    except (json.JSONDecodeError, KeyError) as exc:
        raise GHError("Could not parse PR number from gh pr view") from exc


@dataclass
class PRInfo:
    number: int
    title: str
    state: str
    head_ref: str
    base_ref: str
    mergeable: str
    merge_state: str
    url: str
    draft: bool
    body: str


def get_pr_info(pr_number: Optional[int] = None, *, repo: Optional[RepoInfo] = None) -> PRInfo:
    """Fetch metadata for a PR. Auto-detects PR and repo if not given."""
    if pr_number is None:
        pr_number = detect_current_pr()
    if repo is None:
        repo = detect_repo()

    fields = (
        "number,title,state,headRefName,baseRefName,mergeable,mergeStateStatus,url,isDraft,body"
    )
    raw = _run_gh(["pr", "view", str(pr_number), "--repo", repo.full_name, "--json", fields])
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GHError("Could not parse PR info") from exc

    return PRInfo(
        number=d["number"],
        title=d["title"],
        state=d["state"],
        head_ref=d["headRefName"],
        base_ref=d["baseRefName"],
        mergeable=d.get("mergeable", "UNKNOWN"),
        merge_state=d.get("mergeStateStatus", "UNKNOWN"),
        url=d["url"],
        draft=d.get("isDraft", False),
        body=d.get("body", ""),
    )


@dataclass
class CheckRun:
    name: str
    status: str
    conclusion: str
    url: str


def get_pr_checks(
    pr_number: Optional[int] = None, *, repo: Optional[RepoInfo] = None
) -> list[CheckRun]:
    """Fetch CI check runs for a PR."""
    if pr_number is None:
        pr_number = detect_current_pr()
    if repo is None:
        repo = detect_repo()

    raw = _run_gh(
        [
            "pr",
            "checks",
            str(pr_number),
            "--repo",
            repo.full_name,
            "--json",
            "name,status,conclusion,link",
        ]
    )
    try:
        items = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise GHError("Could not parse check runs") from exc

    return [
        CheckRun(
            name=item["name"],
            status=item["status"],
            conclusion=item.get("conclusion") or "",
            url=item.get("link") or "",
        )
        for item in items
    ]


def wait_for_checks(
    pr_number: Optional[int] = None,
    *,
    repo: Optional[RepoInfo] = None,
    timeout: int = 300,
    poll_interval: int = 15,
) -> list[CheckRun]:
    """
    Poll until all checks complete or timeout is reached.

    Returns the final check list. Does NOT raise on failed checks —
    let the caller decide what to do with failures.
    """
    if pr_number is None:
        pr_number = detect_current_pr()
    if repo is None:
        repo = detect_repo()

    deadline = time.time() + timeout
    while time.time() < deadline:
        checks = get_pr_checks(pr_number, repo=repo)
        pending = [c for c in checks if c.status in ("queued", "in_progress")]
        if not pending:
            return checks
        print(
            f"  ⏳ {len(pending)} check(s) still running… (waiting {poll_interval}s)",
            file=sys.stderr,
        )
        time.sleep(poll_interval)

    return get_pr_checks(pr_number, repo=repo)


COPILOT_REVIEWER = "copilot-pull-request-reviewer[bot]"


def request_review(
    reviewer: str,
    pr_number: Optional[int] = None,
    *,
    repo: Optional[RepoInfo] = None,
) -> None:
    """
    Request a review from a user or bot.

    For Copilot, use reviewer=COPILOT_REVIEWER or reviewer="copilot" (auto-expanded).
    """
    if pr_number is None:
        pr_number = detect_current_pr()
    if repo is None:
        repo = detect_repo()

    if reviewer.lower() == "copilot":
        reviewer = COPILOT_REVIEWER

    gh_api(
        f"/repos/{repo.full_name}/pulls/{pr_number}/requested_reviewers",
        method="POST",
        fields={"reviewers": [reviewer]},
    )


def request_team_review(
    team_slug: str,
    pr_number: Optional[int] = None,
    *,
    repo: Optional[RepoInfo] = None,
) -> None:
    """Request a review from a GitHub team."""
    if pr_number is None:
        pr_number = detect_current_pr()
    if repo is None:
        repo = detect_repo()

    gh_api(
        f"/repos/{repo.full_name}/pulls/{pr_number}/requested_reviewers",
        method="POST",
        fields={"team_reviewers": [team_slug]},
    )


def add_pr_comment(
    body: str,
    pr_number: Optional[int] = None,
    *,
    repo: Optional[RepoInfo] = None,
) -> str:
    """
    Add a general comment to a PR (not a review thread reply).
    Returns the URL of the created comment.
    """
    if pr_number is None:
        pr_number = detect_current_pr()
    if repo is None:
        repo = detect_repo()

    result = gh_api(
        f"/repos/{repo.full_name}/issues/{pr_number}/comments",
        method="POST",
        fields={"body": body},
    )
    return result.get("html_url", "")


def add_labels(
    labels: list[str],
    pr_number: Optional[int] = None,
    *,
    repo: Optional[RepoInfo] = None,
) -> None:
    """Add labels to a PR/issue."""
    if pr_number is None:
        pr_number = detect_current_pr()
    if repo is None:
        repo = detect_repo()

    gh_api(
        f"/repos/{repo.full_name}/issues/{pr_number}/labels",
        method="POST",
        fields={"labels": labels},
    )


def _cmd_info(_args) -> None:
    repo = detect_repo()
    pr = get_pr_info()
    print(f"Repo:      {repo.full_name}")
    print(f"PR:        #{pr.number} — {pr.title}")
    print(f"Branch:    {pr.head_ref} → {pr.base_ref}")
    print(f"State:     {pr.state} | Mergeable: {pr.mergeable} | Merge state: {pr.merge_state}")
    print(f"Draft:     {pr.draft}")
    print(f"URL:       {pr.url}")


def _cmd_checks(args) -> None:
    pr_number = int(args.pr) if getattr(args, "pr", None) else None
    checks = get_pr_checks(pr_number)
    failed = [c for c in checks if c.conclusion == "failure"]
    passed = [c for c in checks if c.conclusion == "success"]
    pending = [c for c in checks if c.status in ("queued", "in_progress")]

    print(f"\n{'Status':<12} {'Name':<45} {'URL'}")
    print("-" * 100)
    for c in sorted(checks, key=lambda c: (c.conclusion != "failure", c.name)):
        icon = "❌" if c.conclusion == "failure" else "✅" if c.conclusion == "success" else "⏳"
        print(f"{icon} {c.status:<10} {c.name:<45} {c.url}")

    print(f"\n✅ {len(passed)}  ❌ {len(failed)}  ⏳ {len(pending)}")
    if failed:
        sys.exit(1)


def _cmd_request_review(args) -> None:
    reviewer = args.reviewer
    request_review(reviewer)
    display = COPILOT_REVIEWER if reviewer.lower() == "copilot" else reviewer
    print(f"✅ Review requested from: {display}")


def _cmd_comment(args) -> None:
    url = add_pr_comment(args.body)
    print(f"✅ Comment posted: {url}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub helper utilities")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("info", help="Show detected repo + current PR").set_defaults(func=_cmd_info)

    p_checks = sub.add_parser("checks", help="Show PR check status")
    p_checks.add_argument("--pr", help="PR number (auto-detect if omitted)")
    p_checks.set_defaults(func=_cmd_checks)

    p_review = sub.add_parser("request-review", help="Request a review")
    p_review.add_argument("reviewer", help='Reviewer login or "copilot"')
    p_review.set_defaults(func=_cmd_request_review)

    p_comment = sub.add_parser("comment", help="Add a PR comment")
    p_comment.add_argument("body", help="Comment body text")
    p_comment.set_defaults(func=_cmd_comment)

    parsed = parser.parse_args()
    try:
        parsed.func(parsed)
    except GHError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
