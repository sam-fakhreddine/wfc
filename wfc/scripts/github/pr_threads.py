#!/usr/bin/env python3
"""
PR Review Thread Manager

Fetches, comments on, and resolves GitHub PR review threads via GraphQL.
Used by wfc-pr-comments after applying fixes.

owner and repo are OPTIONAL everywhere — auto-detected from the current
directory's git remote when omitted.

Usage:
    # Fetch all unresolved threads (with IDs)
    python pr_threads.py fetch <pr_number>
    python pr_threads.py fetch <owner> <repo> <pr_number>   # explicit

    # Reply to a thread and resolve it (owner/repo not needed)
    python pr_threads.py resolve <thread_id> --message "Fixed in <commit>"

    # Bulk resolve from a JSON manifest
    python pr_threads.py bulk-resolve <manifest.json>
    python pr_threads.py bulk-resolve <owner> <repo> <manifest.json>  # explicit
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from wfc.scripts.github.gh_helpers import (
    GHError,
    detect_current_pr,
    detect_repo,
    gh_graphql,
)

_FETCH_QUERY = """
query($owner: String!, $repo: String!, $number: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $number) {
      number
      title
      headRefName
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          comments(first: 1) {
            nodes {
              id
              body
              author { login }
              createdAt
            }
          }
        }
      }
    }
  }
}
"""

_RESOLVE_MUTATION = """
mutation($threadId: ID!) {
  resolveReviewThread(input: {threadId: $threadId}) {
    thread {
      id
      isResolved
    }
  }
}
"""

_REPLY_QUERY = """
mutation($commentId: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $commentId, body: $body}) {
    comment {
      id
    }
  }
}
"""


@dataclass
class ReviewThread:
    id: str
    is_resolved: bool
    is_outdated: bool
    path: str
    line: Optional[int]
    comment_id: str
    author: str
    body: str


def fetch_threads(
    pr_number: Optional[int] = None,
    owner: Optional[str] = None,
    repo: Optional[str] = None,
) -> list[ReviewThread]:
    """Fetch all review threads for a PR. Auto-detects all args if omitted."""
    repo_info = detect_repo()
    if owner is None:
        owner = repo_info.owner
    if repo is None:
        repo = repo_info.name
    if pr_number is None:
        pr_number = detect_current_pr()

    data = gh_graphql(_FETCH_QUERY, owner=owner, repo=repo, number=pr_number)
    nodes = data["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    threads = []
    for node in nodes:
        if not node["comments"]["nodes"]:
            continue
        comment = node["comments"]["nodes"][0]
        threads.append(
            ReviewThread(
                id=node["id"],
                is_resolved=node["isResolved"],
                is_outdated=node["isOutdated"],
                path=node["path"],
                line=node.get("line"),
                comment_id=comment["id"],
                author=comment["author"]["login"],
                body=comment["body"],
            )
        )
    return threads


def reply_to_thread(thread_id: str, message: str) -> str:
    """Post a reply to a review thread. Returns the new comment ID."""
    data = gh_graphql(_REPLY_QUERY, commentId=thread_id, body=message)
    return data["data"]["addPullRequestReviewThreadReply"]["comment"]["id"]


def resolve_thread(thread_id: str) -> bool:
    """Resolve a review thread. Returns True on success."""
    data = gh_graphql(_RESOLVE_MUTATION, threadId=thread_id)
    return data["data"]["resolveReviewThread"]["thread"]["isResolved"]


def reply_and_resolve(thread_id: str, message: str) -> dict:
    """Post a reply to a thread and then resolve it."""
    reply_id = reply_to_thread(thread_id, message)
    resolved = resolve_thread(thread_id)
    return {"reply_id": reply_id, "resolved": resolved}


def bulk_resolve(
    manifest_path: str,
    owner: Optional[str] = None,
    repo: Optional[str] = None,
) -> list[dict]:
    """
    Resolve threads from a JSON manifest.

    owner/repo are accepted for API compat but not used — GraphQL mutations
    only need thread IDs.

    Manifest format:
    [
      {
        "thread_id": "PRRT_...",
        "message": "Fixed in abc1234: <description>",
        "action": "fixed"  // or "responded" or "skip"
      }
    ]
    """
    manifest = json.loads(Path(manifest_path).read_text())
    results = []
    for item in manifest:
        if item.get("action") == "skip":
            results.append({"thread_id": item["thread_id"], "status": "skipped"})
            continue
        try:
            result = reply_and_resolve(item["thread_id"], item["message"])
            results.append(
                {
                    "thread_id": item["thread_id"],
                    "status": "resolved" if result["resolved"] else "failed",
                    **result,
                }
            )
            print(f"✅ Resolved {item['thread_id'][:20]}...")
        except Exception as e:
            results.append({"thread_id": item["thread_id"], "status": "error", "error": str(e)})
            print(f"❌ Failed {item['thread_id'][:20]}...: {e}", file=sys.stderr)
    return results


def print_threads(threads: list[ReviewThread], unresolved_only: bool = True) -> None:
    """Print threads as a formatted table."""
    filtered = [t for t in threads if not t.is_resolved] if unresolved_only else threads
    print(f"\n{'#':<4} {'Thread ID':<30} {'File:Line':<45} {'Author':<20} {'Status'}")
    print("-" * 120)
    for i, t in enumerate(filtered, 1):
        status = "OUTDATED" if t.is_outdated else ("RESOLVED" if t.is_resolved else "OPEN")
        loc = f"{t.path}:{t.line or '?'}"
        print(f"{i:<4} {t.id:<30} {loc:<45} {t.author:<20} {status}")
        print(f"     {t.body[:100].strip()}")
        print()


def _parse_fetch_args(positional: list[str]) -> tuple[Optional[str], Optional[str], Optional[int]]:
    """
    Accept one of:
      <pr_number>
      <owner> <repo> <pr_number>
    Returns (owner, repo, pr_number) with None where auto-detect applies.
    """
    if len(positional) == 1:
        return None, None, int(positional[0])
    elif len(positional) == 3:
        return positional[0], positional[1], int(positional[2])
    else:
        print(
            "Usage: fetch <pr_number>  OR  fetch <owner> <repo> <pr_number>",
            file=sys.stderr,
        )
        sys.exit(1)


def _parse_bulk_args(positional: list[str]) -> tuple[Optional[str], Optional[str], str]:
    """
    Accept one of:
      <manifest.json>
      <owner> <repo> <manifest.json>
    Returns (owner, repo, manifest_path).
    """
    if len(positional) == 1:
        return None, None, positional[0]
    elif len(positional) == 3:
        return positional[0], positional[1], positional[2]
    else:
        print(
            "Usage: bulk-resolve <manifest.json>  OR  bulk-resolve <owner> <repo> <manifest.json>",
            file=sys.stderr,
        )
        sys.exit(1)


def _cmd_fetch(args) -> None:
    owner, repo, pr_number = _parse_fetch_args(args.args)
    threads = fetch_threads(pr_number, owner=owner, repo=repo)
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "id": t.id,
                        "is_resolved": t.is_resolved,
                        "path": t.path,
                        "line": t.line,
                        "author": t.author,
                        "body": t.body[:200],
                    }
                    for t in threads
                ],
                indent=2,
            )
        )
    else:
        unresolved = [t for t in threads if not t.is_resolved]
        num = pr_number or "?"
        print(f"PR #{num}: {len(threads)} total, {len(unresolved)} unresolved")
        print_threads(threads)


def _cmd_resolve(args) -> None:
    result = reply_and_resolve(args.thread_id, args.message)
    if result["resolved"]:
        print(f"✅ Thread resolved. Reply ID: {result['reply_id']}")
    else:
        print("❌ Thread not resolved", file=sys.stderr)
        sys.exit(1)


def _cmd_bulk_resolve(args) -> None:
    owner, repo, manifest = _parse_bulk_args(args.args)
    results = bulk_resolve(manifest, owner=owner, repo=repo)
    resolved = sum(1 for r in results if r["status"] == "resolved")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed = sum(1 for r in results if r["status"] in ("failed", "error"))
    print(f"\nDone: {resolved} resolved, {skipped} skipped, {failed} failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="GitHub PR review thread manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect repo + PR from current branch:
  python pr_threads.py fetch 42
  python pr_threads.py fetch 42 --json

  # Explicit owner/repo:
  python pr_threads.py fetch sam-fakhreddine wfc 42

  # Resolve a single thread (owner/repo not needed):
  python pr_threads.py resolve PRRT_abc123 --message "Fixed in a1b2c3: removed unused import"

  # Bulk resolve from manifest (auto-detect repo):
  python pr_threads.py bulk-resolve /tmp/manifest.json

  # Bulk resolve from manifest (explicit):
  python pr_threads.py bulk-resolve sam-fakhreddine wfc /tmp/manifest.json
""",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser(
        "fetch",
        help="List review threads",
        description="Usage: fetch <pr_number>  OR  fetch <owner> <repo> <pr_number>",
    )
    p_fetch.add_argument(
        "args",
        nargs="+",
        metavar="[owner repo] pr_number",
        help="PR number, or owner repo PR number",
    )
    p_fetch.add_argument("--json", action="store_true", help="Output as JSON")
    p_fetch.set_defaults(func=_cmd_fetch)

    p_resolve = sub.add_parser("resolve", help="Reply to and resolve a single thread")
    p_resolve.add_argument("thread_id", help="GraphQL thread node ID (PRRT_...)")
    p_resolve.add_argument(
        "--message", required=True, help="Reply message to post before resolving"
    )
    p_resolve.set_defaults(func=_cmd_resolve)

    p_bulk = sub.add_parser(
        "bulk-resolve",
        help="Resolve threads from a JSON manifest",
        description="Usage: bulk-resolve <manifest.json>  OR  bulk-resolve <owner> <repo> <manifest.json>",
    )
    p_bulk.add_argument(
        "args",
        nargs="+",
        metavar="[owner repo] manifest.json",
        help="Path to JSON manifest, optionally preceded by owner and repo",
    )
    p_bulk.set_defaults(func=_cmd_bulk_resolve)

    parsed = parser.parse_args()
    try:
        parsed.func(parsed)
    except GHError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
