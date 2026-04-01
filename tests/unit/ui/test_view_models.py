# Responsibility: Tests for user-facing summary strings built from domain summaries.

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from kibo_converter.domain.job_result import FileResultRecord, FileResultStatus, JobRunSummary
from kibo_converter.ui.view_models import (
    describe_file_result_status_for_user,
    format_file_result_line_for_user,
    format_job_summary_text,
)


def test_format_job_summary_text_explains_zero_matches_with_only_excluded_files() -> None:
    summary = JobRunSummary(
        total_files=0,
        excluded_by_filter_count=1,
        success_count=0,
        failure_count=0,
        skipped_count=0,
        skipped_filtered_input_count=0,
        cancelled_count=0,
    )
    text = format_job_summary_text(summary)
    assert "変換対象" in text
    assert "除外" in text or "._" in text


def test_format_job_summary_text_shows_attention_when_failures_exist() -> None:
    summary = JobRunSummary(
        total_files=2,
        excluded_by_filter_count=0,
        success_count=1,
        failure_count=1,
        skipped_count=0,
        skipped_filtered_input_count=0,
        cancelled_count=0,
    )
    text = format_job_summary_text(summary)
    assert "要確認" in text
    assert "失敗 1" in text


def test_format_file_result_line_uses_japanese_labels() -> None:
    record = FileResultRecord(
        source_path=Path("C:/in/x.HEIC"),
        target_path=Path("C:/out/x.png"),
        status=FileResultStatus.SUCCESS,
        error_code=None,
        error_summary=None,
        error_detail=None,
        started_at=datetime.now(timezone.utc),
        finished_at=datetime.now(timezone.utc),
    )
    line = format_file_result_line_for_user(record)
    assert "成功" in line
    assert FileResultStatus.SUCCESS.value not in line


def test_describe_file_result_status_maps_unknown_enum_safely() -> None:
    assert "成功" in describe_file_result_status_for_user(FileResultStatus.SUCCESS)
