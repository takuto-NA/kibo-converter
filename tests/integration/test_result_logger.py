# Responsibility: Integration tests for JSONL logging helpers.

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from kibo_converter.domain.job_result import FileResultRecord, FileResultStatus
from kibo_converter.infrastructure.result_logger import append_file_result_json_line, write_job_summary_json_line


def test_append_file_result_json_line_writes_one_json_object_per_line(tmp_path: Path) -> None:
    log_path = tmp_path / "run.jsonl"
    started_at = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    finished_at = datetime(2020, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
    record = FileResultRecord(
        source_path=Path("C:/in/a.heic"),
        target_path=Path("C:/out/a.png"),
        status=FileResultStatus.SUCCESS,
        error_code=None,
        error_summary=None,
        error_detail=None,
        started_at=started_at,
        finished_at=finished_at,
    )

    append_file_result_json_line(log_path, record)

    text = log_path.read_text(encoding="utf-8").strip()
    payload = json.loads(text)
    assert payload["event_type"] == "file_result"
    assert payload["status"] == FileResultStatus.SUCCESS.value


def test_write_job_summary_json_line_appends_summary(tmp_path: Path) -> None:
    log_path = tmp_path / "run.jsonl"
    write_job_summary_json_line(
        log_path,
        total_files=3,
        excluded_by_filter_count=1,
        success_count=2,
        failure_count=1,
        skipped_count=0,
        skipped_filtered_input_count=0,
        cancelled_count=0,
    )

    text = log_path.read_text(encoding="utf-8").strip()
    payload = json.loads(text)
    assert payload["event_type"] == "job_summary"
    assert payload["total_files"] == 3
    assert payload["excluded_by_filter_count"] == 1
