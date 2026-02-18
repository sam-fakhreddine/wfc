#!/usr/bin/env python3
"""
PR Review Thread Manager

Fetches, comments on, and resolves GitHub PR review threads via GraphQL.
Used by wfc-pr-comments after applying fixes.

Usage:
    # Fetch all unresolved threads (with IDs)
    python pr_threads.py fetch <owner> <repo> <pr_number>

    # Reply to a thread and resolve it
    python pr_threads.py resolve <owner> <repo> <thread_id> --message "Fixed in <commit>"

    # Bulk resolve from a JSON manifest
    python pr_threads.py bulk-resolve <owner> <repo> <manifest.json>
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

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


def _gh_graphql(query: str, **variables) -> dict:
    """Execute a GitHub GraphQL query via gh CLI."""
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        if isinstance(value, int):
            args += ["-F", f"{key}={value}"]
        else:
            args += ["-f", f"{key}={value}"]
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gh graphql failed: {result.stderr}")
    data = json.loads(result.stdout)
    if "errors" in data:
        raise RuntimeError(f"GraphQL errors: {data['errors']}")
    return data


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


def fetch_threads(owner: str, repo: str, pr_number: int) -> list[ReviewThread]:
    """Fetch all unresolved review threads for a PR."""
    data = _gh_graphql(_FETCH_QUERY, owner=owner, repo=repo, number=pr_number)
    nodes = data["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
    threads = []
    for node in nodes:
        if not node["comments"]["nodes"]:
            continue
        comment = node["comments"]["nodes"][0]
        threads.append(ReviewThread(
            id=node["id"],
            is_resolved=node["isResolved"],
            is_outdated=node["isOutdated"],
            path=node["path"],
            line=node.get("line"),
            comment_id=comment["id"],
            author=comment["author"]["login"],
            body=comment["body"],
        ))
    return threads


def reply_to_thread(thread_id: str, message: str) -> str:
    """Post a reply to a review thread. Returns the new comment ID."""
    data = _gh_graphql(_REPLY_QUERY, commentId=thread_id, body=message)
    return data["data"]["addPullRequestReviewThreadReply"]["comment"]["id"]


def resolve_thread(thread_id: str) -> bool:
    """Resolve a review thread. Returns True on success."""
    data = _gh_graphql(_RESOLVE_MUTATION, threadId=thread_id)
    return data["data"]["resolveReviewThread"]["thread"]["isResolved"]


def reply_and_resolve(thread_id: str, message: str) -> dict:
    """Post a reply to a thread and then resolve it."""
    reply_id = reply_to_thread(thread_id, message)
    resolved = resolve_thread(thread_id)
    return {"reply_id": reply_id, "resolved": resolved}


def bulk_resolve(owner: str, repo: str, manifest_path: str) -> list[dict]:
    """
    Resolve threads from a JSON manifest.

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
            results.append({
                "thread_id": item["thread_id"],
                "status": "resolved" if result["resolved"] else "failed",
                **result,
            })
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


def _cmd_fetch(args):
    owner, repo, pr_number = args.owner, args.repo, int(args.pr_number)
    threads = fetch_threads(owner, repo, pr_number)
    if args.json:
        print(json.dumps([{
            "id": t.id,
            "is_resolved": t.is_resolved,
            "path": t.path,
            "line": t.line,
            "author": t.author,
            "body": t.body[:200],
        } for t in threads], indent=2))
    else:
        unresolved = [t for t in threads if not t.is_resolved]
        print(f"PR #{pr_number}: {len(threads)} total, {len(unresolved)} unresolved")
        print_threads(threads)


def _cmd_resolve(args):
    result = reply_and_resolve(args.thread_id, args.message)
    if result["resolved"]:
        print(f"✅ Thread resolved. Reply ID: {result['reply_id']}")
    else:
        print("❌ Thread not resolved", file=sys.stderr)
        sys.exit(1)


def _cmd_bulk_resolve(args):
    results = bulk_resolve(args.owner, args.repo, args.manifest)
    resolved = sum(1 for r in results if r["status"] == "resolved")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    failed = sum(1 for r in results if r["status"] in ("failed", "error"))
    print(f"\nDone: {resolved} resolved, {skipped} skipped, {failed} failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub PR review thread manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch", help="List all review threads")
    p_fetch.add_argument("owner")
    p_fetch.add_argument("repo")
    p_fetch.add_argument("pr_number")
    p_fetch.add_argument("--json", action="store_true", help="Output as JSON")
    p_fetch.set_defaults(func=_cmd_fetch)

    p_resolve = sub.add_parser("resolve", help="Reply to and resolve a single thread")
    p_resolve.add_argument("thread_id", help="GraphQL thread node ID (PRRT_...)")
    p_resolve.add_argument("--message", required=True, help="Reply message to post before resolving")
    p_resolve.set_defaults(func=_cmd_resolve)

    p_bulk = sub.add_parser("bulk-resolve", help="Resolve threads from a JSON manifest")
    p_bulk.add_argument("owner")
    p_bulk.add_argument("repo")
    p_bulk.add_argument("manifest", help="Path to JSON manifest file")
    p_bulk.set_defaults(func=_cmd_bulk_resolve)

    args = parser.parse_args()
    args.func(args)
