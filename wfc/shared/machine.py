"""Idempotent machine identity for audit trails and deduplication."""

import functools
import getpass
import hashlib
import platform
import uuid
from pathlib import Path


@functools.lru_cache(maxsize=1)
def machine_id() -> str:
    """Derive an 8-char hex fingerprint for this machine.

    Fallback chain:
    1. /etc/machine-id (Linux/systemd)
    2. uuid.getnode() MAC address (if not random)
    3. platform.node() + platform.machine() + getpass.getuser()
    """
    machine_id_path = Path("/etc/machine-id")
    try:
        if machine_id_path.exists():
            content = machine_id_path.read_text().strip()
            if content:
                return hashlib.sha256(content.encode()).hexdigest()[:8]
    except OSError:
        pass

    mac = uuid.getnode()
    if not (mac >> 40) & 1:
        return hashlib.sha256(str(mac).encode()).hexdigest()[:8]

    identity = platform.node() + platform.machine() + getpass.getuser()
    return hashlib.sha256(identity.encode()).hexdigest()[:8]
