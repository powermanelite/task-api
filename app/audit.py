import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

DEFAULT_LOG_PATH = "task_audit.log"


def write_audit_entry(event: str, task_id: UUID) -> None:
    """Append a timestamped line to the audit log (run as a background task)."""
    path = Path(os.environ.get("TASK_AUDIT_LOG", DEFAULT_LOG_PATH))
    timestamp = datetime.now(timezone.utc).isoformat()
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{timestamp} {event} task_id={task_id}\n")
