# Responsibility: Validate environment and paths before a long-running conversion job starts.

from __future__ import annotations

from pathlib import Path

from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.infrastructure.image_reader_writer import HeifSupportInitializationError, ensure_heif_support_registered


class JobPreflightError(Exception):
    """Raised when a job cannot start due to invalid paths or missing dependencies."""


def run_job_preflight(job_definition: JobDefinition) -> None:
    """
    Validate that the job can start.

    Raises JobPreflightError when the environment cannot satisfy the job.
    """
    job_definition.validate()

    input_directory = job_definition.selection_rules.input_directory_path
    if not input_directory.is_dir():
        raise JobPreflightError(
            f"入力フォルダが存在しないか、フォルダではありません: {input_directory}"
        )

    output_directory = job_definition.output_rules.output_directory_path
    try:
        output_directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise JobPreflightError(f"出力フォルダを作成できません: {output_directory}") from exc

    if not is_output_directory_writable(output_directory):
        raise JobPreflightError(f"出力フォルダに書き込みできません: {output_directory}")

    if not _job_requires_heif_support(job_definition):
        return

    try:
        ensure_heif_support_registered()
    except HeifSupportInitializationError as exc:
        raise JobPreflightError(
            "このPCでは HEIC/HEIF を読むための環境が見つかりません（pillow-heif / libheif など）。"
        ) from exc


def is_output_directory_writable(output_directory_path: Path) -> bool:
    """Return True when the directory exists and appears writable."""
    if not output_directory_path.is_dir():
        return False
    probe_file_path = output_directory_path / ".kibo_converter_write_probe"
    try:
        probe_file_path.write_text("", encoding="utf-8")
        probe_file_path.unlink(missing_ok=True)
        return True
    except OSError:
        return False


def _job_requires_heif_support(job_definition: JobDefinition) -> bool:
    """Return True when selected extensions require HEIC/HEIF decoding support."""
    included_extensions = job_definition.selection_rules.included_file_extensions_lower_case
    heif_extensions = {".heic", ".heif"}
    return bool(included_extensions.intersection(heif_extensions))
