# Responsibility: Append structured JSON lines for per-file and job-level audit logs.

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from kibo_converter.domain.job_result import FileResultRecord


def _path_to_str(path: Path | None) -> str | None:
    if path is None:
        return None
    return str(path)


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat()


def append_file_result_json_line(log_file_path: Path, record: FileResultRecord) -> None:
    """Append one JSON line describing a single file result."""
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "event_type": "file_result",
        "source_path": _path_to_str(record.source_path),
        "target_path": _path_to_str(record.target_path),
        "status": record.status.value,
        "error_code": record.error_code,
        "error_summary": record.error_summary,
        "error_detail": record.error_detail,
        "started_at": _serialize_datetime(record.started_at),
        "finished_at": _serialize_datetime(record.finished_at),
    }
    with log_file_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def write_job_summary_json_line(
    log_file_path: Path,
    *,
    total_files: int,
    success_count: int,
    failure_count: int,
    skipped_count: int,
    cancelled_count: int,
) -> None:
    """Append a summary line for the whole job run."""
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "event_type": "job_summary",
        "total_files": total_files,
        "success_count": success_count,
        "failure_count": failure_count,
        "skipped_count": skipped_count,
        "cancelled_count": cancelled_count,
    }
    with log_file_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def file_result_record_to_dict(record: FileResultRecord) -> dict[str, Any]:
    """Convert a record to a plain dict for tests or export."""
    data = asdict(record)
    data["status"] = record.status.value
    data["source_path"] = str(record.source_path)
    data["target_path"] = str(record.target_path) if record.target_path else None
    data["started_at"] = _serialize_datetime(record.started_at)
    data["finished_at"] = _serialize_datetime(record.finished_at)
    return data
