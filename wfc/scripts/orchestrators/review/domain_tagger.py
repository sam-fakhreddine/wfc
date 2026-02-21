"""Domain relevance tagging for diff files."""

from __future__ import annotations

from .diff_manifest import ChangeHunk

DOMAIN_KEYWORDS = {
    "security": [
        "auth",
        "password",
        "token",
        "jwt",
        "session",
        "cookie",
        "crypto",
        "hash",
        "bcrypt",
        "secret",
        "credential",
        "api_key",
        "oauth",
        "permission",
        "role",
        "access",
        "sanitize",
        "escape",
        "validate",
        "injection",
        "xss",
        "csrf",
        "sql",
        "eval",
        "exec",
        "pickle",
        "yaml.load",
        "xml",
        "ldap",
        "shell",
        "command",
    ],
    "performance": [
        "query",
        "database",
        "db",
        "select",
        "join",
        "index",
        "cache",
        "redis",
        "memcache",
        "prefetch",
        "batch",
        "loop",
        "for ",
        "while ",
        "n+1",
        "pagination",
        "limit",
        "timeout",
        "async",
        "await",
        "thread",
        "pool",
        "worker",
        "celery",
        "queue",
    ],
    "correctness": [
        "null",
        "none",
        "undefined",
        "optional",
        "raise",
        "exception",
        "error",
        "assert",
        "validate",
        "check",
        "if ",
        "else",
        "try",
        "catch",
        "except",
        "finally",
        "return",
        "type",
        "cast",
        "isinstance",
        "bool",
        "int",
        "str",
        "list",
        "dict",
    ],
    "reliability": [
        "retry",
        "timeout",
        "deadline",
        "circuit",
        "fallback",
        "graceful",
        "recover",
        "close",
        "cleanup",
        "context",
        "with ",
        "finally",
        "lock",
        "mutex",
        "semaphore",
        "connection",
        "resource",
        "leak",
        "memory",
        "file",
        "handle",
        "transaction",
        "commit",
        "rollback",
    ],
    "maintainability": [
        "class",
        "function",
        "def ",
        "const ",
        "refactor",
        "rename",
        "duplicate",
        "dry",
        "solid",
        "comment",
        "docstring",
        "todo",
        "fixme",
        "import",
        "export",
        "module",
        "package",
    ],
}


def tag_file_domains(file_path: str, hunks: list[ChangeHunk]) -> list[str]:
    """
    Tag a file with relevant reviewer domains.

    Args:
        file_path: Path to the file
        hunks: List of change hunks in this file

    Returns:
        List of relevant domain tags (e.g., ["security", "performance"])
    """
    domains = set()

    path_lower = file_path.lower()

    if any(
        keyword in path_lower for keyword in ["auth", "security", "crypto", "password", "token"]
    ):
        domains.add("security")

    if any(keyword in path_lower for keyword in ["database", "db", "query", "model", "cache"]):
        domains.add("performance")

    if any(keyword in path_lower for keyword in ["test", "spec"]):
        domains.add("correctness")

    if any(keyword in path_lower for keyword in ["config", "settings", "env"]):
        domains.add("reliability")

    all_content = ""
    for hunk in hunks:
        all_content += hunk.context_before + " "
        all_content += hunk.change_summary + " "
        all_content += " ".join(hunk.raw_diff_lines)

    content_lower = all_content.lower()

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in content_lower:
                domains.add(domain)
                break

    if "import " in all_content or "from " in all_content:
        domains.add("reliability")

    if any(
        pattern in content_lower
        for pattern in ["select ", "insert ", "update ", "delete ", "query"]
    ):
        domains.add("performance")

    if any(
        pattern in content_lower
        for pattern in [
            "if not ",
            "raise ",
            "except ",
            "assert ",
            "validate",
        ]
    ):
        domains.add("correctness")

    return sorted(list(domains))
