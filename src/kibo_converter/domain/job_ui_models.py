"""Responsibility: Define job-centered UI data models for shared settings, image settings, candidates, and output preview."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from kibo_converter.domain.output_rules import CollisionPolicy
from kibo_converter.domain.processing_steps import ImageOutputFormat, ResizeOptions


@dataclass(frozen=True, slots=True)
class SharedJobSettings:
    """Settings reused across different job types."""

    input_directory_path: Path
    output_directory_path: Path
    collision_policy: CollisionPolicy


@dataclass(frozen=True, slots=True)
class ImageConversionJobSettings:
    """Image-conversion-specific settings edited in the job-specific panel."""

    included_file_extensions_lower_case: frozenset[str]
    include_subdirectories_recursively: bool
    output_format: ImageOutputFormat
    resize_options: ResizeOptions


class CandidateReviewStatus(str, Enum):
    """How one candidate file should be presented before execution."""

    INCLUDED = "included"
    EXCLUDED = "excluded"
    EXCLUDED_BY_USER = "excluded_by_user"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class CandidateReviewItem:
    """One input file candidate shown to the user before a run starts."""

    source_path: Path
    extension_lower_case: str
    status: CandidateReviewStatus
    reason: str
    is_selected: bool


class OutputPreviewAction(str, Enum):
    """How one output path is expected to behave before execution starts."""

    CREATE_NEW = "create_new"
    OVERWRITE = "overwrite"
    WRITE_UNIQUE_NAME = "write_unique_name"
    SKIP_IDENTICAL_EXISTING_OUTPUT = "skip_identical_existing_output"


@dataclass(frozen=True, slots=True)
class OutputPreviewItem:
    """One predicted output entry shown before the run starts."""

    source_path: Path
    target_path: Path
    action: OutputPreviewAction
    note: str


@dataclass(frozen=True, slots=True)
class JobPreviewSnapshot:
    """Preview result shown before execution starts."""

    candidate_items: list[CandidateReviewItem]
    output_preview_items: list[OutputPreviewItem]
    excluded_by_filter_count: int = 0
