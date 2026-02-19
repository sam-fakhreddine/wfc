"""FileProvider: writes JSON-lines to a session-scoped file."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wfc.observability.events import ObservabilityEvent

from . import ObservabilityProvider

logger = logging.getLogger(__name__)


class FileProvider(ObservabilityProvider):
    """Writes events and snapshots as JSON-lines to a file."""

    MAX_BUFFER_SIZE = 10000

    def __init__(self, output_dir: str, session_id: str):
        self._output_dir = Path(output_dir)
        safe_id = Path(session_id.replace("\\", "/")).name or "default"
        self._session_id = safe_id
        self._buffer: list[str] = []
        self._file_path: Path | None = None

    def _ensure_file(self) -> Path:
        if self._file_path is None:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            self._file_path = self._output_dir / f"wfc-{self._session_id}-{ts}.jsonl"
        return self._file_path

    def on_event(self, event: ObservabilityEvent) -> None:
        data = event.to_dict()
        self._buffer.append(json.dumps(data, default=str))
        if len(self._buffer) > self.MAX_BUFFER_SIZE:
            self._buffer = self._buffer[-self.MAX_BUFFER_SIZE :]

    def on_metric_snapshot(self, snapshot: dict[str, Any]) -> None:
        data = {"_type": "metric_snapshot", **snapshot}
        self._buffer.append(json.dumps(data, default=str))

    def flush(self) -> None:
        if not self._buffer:
            return
        to_write = self._buffer[:]
        self._buffer.clear()
        try:
            path = self._ensure_file()
            chunk = "\n".join(to_write) + "\n"
            with open(path, "a") as f:
                f.write(chunk)
        except OSError:
            logger.debug("FileProvider flush failed — dropping %d events", len(to_write))

    def close(self) -> None:
        self.flush()
