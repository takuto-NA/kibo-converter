"""Responsibility: Build pre-run candidate review and output preview snapshots for supported jobs."""

from __future__ import annotations

from pathlib import Path

from kibo_converter.application.job_executor import build_default_target_path
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.job_types import JobType
from kibo_converter.domain.job_ui_models import (
    CandidateReviewItem,
    CandidateReviewStatus,
    JobPreviewSnapshot,
    OutputPreviewAction,
    OutputPreviewItem,
)
from kibo_converter.infrastructure import filesystem_scanner
from kibo_converter.infrastructure.image_reader_writer import (
    HeifSupportInitializationError,
    apply_exif_orientation,
    encode_image_to_bytes,
    open_image,
    resize_to_max_edge,
)
from kibo_converter.infrastructure.input_path_filter import is_path_excluded_by_default_scan_rules
from kibo_converter.infrastructure.output_collision_resolver import resolve_target_path


_UNSUPPORTED_EXTENSION_REASON_TEXT = "このジョブでは未対応の拡張子です。"
_DEFAULT_SCAN_EXCLUSION_REASON_TEXT = "OS 付随ファイルのため既定で対象外です。"
_MANUAL_EXCLUSION_REASON_TEXT = "ユーザーが今回の実行対象から外しました。"
_INCLUDED_REASON_TEXT = "このジョブの変換対象です。"


def build_job_preview_snapshot(
    job_definition: JobDefinition,
    *,
    manually_excluded_source_paths: frozenset[Path] = frozenset(),
) -> JobPreviewSnapshot:
    """Build candidate review rows and output preview rows for the current job."""
    job_definition.validate()
    if job_definition.job_type != JobType.IMAGE_CONVERSION:
        raise ValueError(f"Unsupported job_type for preview: {job_definition.job_type.value}")

    candidate_items: list[CandidateReviewItem] = []
    output_preview_items: list[OutputPreviewItem] = []
    excluded_by_filter_count = 0
    image_settings = job_definition.image_conversion_settings

    all_files = filesystem_scanner.list_all_files_under_root(
        root=job_definition.selection_rules.input_directory_path,
        include_subdirectories_recursively=image_settings.include_subdirectories_recursively,
    )
    for source_path in all_files:
        extension_lower_case = source_path.suffix.lower()
        if extension_lower_case not in image_settings.included_file_extensions_lower_case:
            candidate_items.append(
                CandidateReviewItem(
                    source_path=source_path,
                    extension_lower_case=extension_lower_case,
                    status=CandidateReviewStatus.EXCLUDED,
                    reason=_UNSUPPORTED_EXTENSION_REASON_TEXT,
                    is_selected=False,
                )
            )
            continue

        if is_path_excluded_by_default_scan_rules(source_path):
            excluded_by_filter_count += 1
            candidate_items.append(
                CandidateReviewItem(
                    source_path=source_path,
                    extension_lower_case=extension_lower_case,
                    status=CandidateReviewStatus.EXCLUDED,
                    reason=_DEFAULT_SCAN_EXCLUSION_REASON_TEXT,
                    is_selected=False,
                )
            )
            continue

        if source_path in manually_excluded_source_paths:
            candidate_items.append(
                CandidateReviewItem(
                    source_path=source_path,
                    extension_lower_case=extension_lower_case,
                    status=CandidateReviewStatus.EXCLUDED_BY_USER,
                    reason=_MANUAL_EXCLUSION_REASON_TEXT,
                    is_selected=False,
                )
            )
            continue

        try:
            output_preview_items.append(_build_image_output_preview_item(job_definition, source_path=source_path))
        except (OSError, ValueError, HeifSupportInitializationError) as exc:
            candidate_items.append(
                CandidateReviewItem(
                    source_path=source_path,
                    extension_lower_case=extension_lower_case,
                    status=CandidateReviewStatus.ERROR,
                    reason=str(exc) or type(exc).__name__,
                    is_selected=False,
                )
            )
            continue

        candidate_items.append(
            CandidateReviewItem(
                source_path=source_path,
                extension_lower_case=extension_lower_case,
                status=CandidateReviewStatus.INCLUDED,
                reason=_INCLUDED_REASON_TEXT,
                is_selected=True,
            )
        )

    return JobPreviewSnapshot(
        candidate_items=candidate_items,
        output_preview_items=output_preview_items,
        excluded_by_filter_count=excluded_by_filter_count,
    )


def _build_image_output_preview_item(
    job_definition: JobDefinition,
    *,
    source_path: Path,
) -> OutputPreviewItem:
    image = open_image(source_path)
    image = apply_exif_orientation(image)
    max_edge_pixels = job_definition.resize_options.max_edge_pixels
    if max_edge_pixels is not None:
        image = resize_to_max_edge(image, max_edge_pixels)

    encoded_image_bytes = encode_image_to_bytes(image, job_definition.output_format)
    desired_target_path = build_default_target_path(
        source_path=source_path,
        output_format=job_definition.output_format,
        output_directory_path=job_definition.output_rules.output_directory_path,
    )
    resolution = resolve_target_path(
        desired_target_path=desired_target_path,
        encoded_output_bytes=encoded_image_bytes,
        collision_policy=job_definition.output_rules.collision_policy,
    )
    return OutputPreviewItem(
        source_path=source_path,
        target_path=resolution.final_target_path,
        action=_output_preview_action_from_resolution_action(resolution.action),
        note=_preview_note_from_resolution_action(resolution.action),
    )


def _output_preview_action_from_resolution_action(resolution_action: str) -> OutputPreviewAction:
    if resolution_action == "create_new":
        return OutputPreviewAction.CREATE_NEW
    if resolution_action == "overwrite":
        return OutputPreviewAction.OVERWRITE
    if resolution_action == "write_unique_name":
        return OutputPreviewAction.WRITE_UNIQUE_NAME
    if resolution_action == "skip_identical_existing_output":
        return OutputPreviewAction.SKIP_IDENTICAL_EXISTING_OUTPUT
    raise ValueError(f"Unsupported resolution action: {resolution_action}")


def _preview_note_from_resolution_action(resolution_action: str) -> str:
    if resolution_action == "create_new":
        return "新しい出力ファイルを作成します。"
    if resolution_action == "overwrite":
        return "既存の出力ファイルを上書きします。"
    if resolution_action == "write_unique_name":
        return "同名ファイルがあるため別名で保存します。"
    if resolution_action == "skip_identical_existing_output":
        return "同じ内容の出力が既にあるため書き込みを省略します。"
    raise ValueError(f"Unsupported resolution action: {resolution_action}")
