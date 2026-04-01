# Responsibility: Thin UI mapping/presentation helpers that convert form state to JobDefinition and format user-facing text; this is not a heavy Qt MVVM layer.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from kibo_converter.constants import JOB_SCHEMA_VERSION_CURRENT
from kibo_converter.domain.file_selection import FileSelectionRules
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.job_result import FileResultRecord, FileResultStatus, JobRunSummary
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
        raise ValueError(
            "入力フォルダを指定してください。変換元の画像が入っているフォルダを選びます。"
        )
    if not output_directory_path_text:
        raise ValueError(
            "出力フォルダを指定してください。変換後の画像を保存する場所を選びます。"
        )

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


_FILE_STATUS_DESCRIPTIONS_JA: dict[FileResultStatus, str] = {
    FileResultStatus.SUCCESS: "成功",
    FileResultStatus.FAILURE: "要確認の失敗",
    FileResultStatus.SKIPPED_DUPLICATE_OUTPUT: "安全にスキップ（同じ内容の出力が既にある）",
    FileResultStatus.SKIPPED_CANCELLED: "キャンセルにより未処理",
    FileResultStatus.SKIPPED_FILTERED_INPUT: "安全にスキップ（入力の除外ルール）",
}


def describe_file_result_status_for_user(status: FileResultStatus) -> str:
    """Return a short Japanese label for a file result status (not raw enum values)."""
    return _FILE_STATUS_DESCRIPTIONS_JA[status]


def format_file_result_line_for_user(record: FileResultRecord) -> str:
    """Build one log line for the run panel using user-oriented wording."""
    label = describe_file_result_status_for_user(record.status)
    line = f"{label}: {record.source_path}"
    if record.error_summary:
        line += f" | {record.error_summary}"
    return line


def format_job_summary_text(summary: JobRunSummary) -> str:
    """Human-readable summary line for the job run panel (Japanese)."""
    excluded_fragment = ""
    if summary.excluded_by_filter_count > 0:
        excluded_fragment = (
            f"スキャン時に除外 {summary.excluded_by_filter_count} 件"
            "（例: macOS の ._ ファイル、.DS_Store）。 "
        )

    if summary.total_files == 0:
        if summary.excluded_by_filter_count > 0:
            return (
                "変換対象の画像がありませんでした。"
                f"{excluded_fragment}"
                "拡張子（例: `.heic`）と入力フォルダに、本当に画像があるか確認してください。"
            )
        return (
            "変換対象の画像がありませんでした。"
            "拡張子の設定と入力フォルダを確認してください。"
        )

    attention_needed = summary.failure_count > 0
    status_word = "要確認" if attention_needed else "完了"

    duplicate_skipped = summary.skipped_count
    filtered_skipped = summary.skipped_filtered_input_count

    body = (
        f"{status_word}: 成功 {summary.success_count}、"
        f"要確認の失敗 {summary.failure_count}、"
        f"安全にスキップ（重複） {duplicate_skipped}、"
        f"安全にスキップ（入力フィルタ） {filtered_skipped}、"
        f"キャンセル {summary.cancelled_count} "
        f"／ 対象 {summary.total_files} 件。"
    )
    if summary.excluded_by_filter_count > 0:
        body += f" {excluded_fragment.strip()}"
    return body
