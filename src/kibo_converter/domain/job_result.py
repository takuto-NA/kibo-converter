# Responsibility: Represent per-file outcomes and aggregated job run results.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class FileResultStatus(str, Enum):
    """Terminal status for a single source file in a job run."""

    SUCCESS = "success"
    FAILURE = "failure"
    SKIPPED_DUPLICATE_OUTPUT = "skipped_duplicate_output"
    SKIPPED_CANCELLED = "skipped_cancelled"
    SKIPPED_FILTERED_INPUT = "skipped_filtered_input"


@dataclass(slots=True)
class FileResultRecord:
    """One line of audit information for a processed file."""

    source_path: Path
    target_path: Path | None
    status: FileResultStatus
    error_code: str | None
    error_summary: str | None
    error_detail: str | None
    started_at: datetime
    finished_at: datetime


@dataclass(slots=True)
class JobRunSummary:
    """Aggregated counters after a job completes or is cancelled."""

    total_files: int = 0
    excluded_by_filter_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    skipped_count: int = 0
    skipped_filtered_input_count: int = 0
    cancelled_count: int = 0
    file_results: list[FileResultRecord] = field(default_factory=list)
