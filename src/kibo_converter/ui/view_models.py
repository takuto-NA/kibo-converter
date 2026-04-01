# Responsibility: Map UI state to domain JobDefinition and interpret job results for display.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kibo_converter.constants import JOB_SCHEMA_VERSION_CURRENT
from kibo_converter.domain.file_selection import FileSelectionRules
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.job_result import JobRunSummary
from kibo_converter.domain.output_rules import CollisionPolicy, OutputRules
from kibo_converter.domain.processing_steps import ImageOutputFormat, ResizeOptions


@dataclass(slots=True)
class JobFormState:
    """Mutable snapshot of user-editable job fields."""

    input_directory_path_text: str
    output_directory_path_text: str
    included_extensions_text: str
    include_subfolders: bool
    output_format: ImageOutputFormat
    max_edge_pixels_enabled: bool
    max_edge_pixels: int
    collision_policy: CollisionPolicy


def parse_extensions_from_comma_separated_text(extensions_text: str) -> frozenset[str]:
    """Parse '.heic, .png' style input into normalized lowercase extensions with leading dot."""
    normalized: set[str] = set()
    for raw_part in extensions_text.split(","):
        part = raw_part.strip().lower()
        if not part:
            continue
        if not part.startswith("."):
            part = f".{part}"
        normalized.add(part)
    return frozenset(normalized)


def build_job_definition_from_form_state(form_state: JobFormState) -> JobDefinition:
    """Build a validated JobDefinition from UI state; raises ValueError on invalid input."""
    input_directory_path_text = form_state.input_directory_path_text.strip()
    output_directory_path_text = form_state.output_directory_path_text.strip()
    if not input_directory_path_text:
        raise ValueError("Input folder is required. Select the folder that contains your source images.")
    if not output_directory_path_text:
        raise ValueError("Output folder is required. Select where converted images should be written.")

    input_directory_path = Path(input_directory_path_text)
    output_directory_path = Path(output_directory_path_text)
    extensions = parse_extensions_from_comma_separated_text(form_state.included_extensions_text)
    max_edge_pixels: int | None
    if form_state.max_edge_pixels_enabled:
        max_edge_pixels = form_state.max_edge_pixels
    else:
        max_edge_pixels = None

    selection_rules = FileSelectionRules(
        input_directory_path=input_directory_path,
        included_file_extensions_lower_case=extensions,
        include_subdirectories_recursively=form_state.include_subfolders,
    )
    resize_options = ResizeOptions(max_edge_pixels=max_edge_pixels)
    output_rules = OutputRules(
        output_directory_path=output_directory_path,
        collision_policy=form_state.collision_policy,
    )

    job_definition = JobDefinition(
        schema_version=JOB_SCHEMA_VERSION_CURRENT,
        selection_rules=selection_rules,
        output_format=form_state.output_format,
        resize_options=resize_options,
        output_rules=output_rules,
    )
    job_definition.validate()
    return job_definition


def format_job_summary_text(summary: JobRunSummary) -> str:
    """Human-readable summary line for the job run panel."""
    return (
        f"Completed {summary.success_count} successfully, "
        f"{summary.failure_count} failed, "
        f"{summary.skipped_count} skipped, "
        f"{summary.cancelled_count} cancelled "
        f"out of {summary.total_files} files."
    )
