# Responsibility: Unit tests for job-centered candidate review and output preview building.

from __future__ import annotations

from pathlib import Path

from PIL import Image

from kibo_converter.application.job_preview import build_job_preview_snapshot
from kibo_converter.constants import JOB_SCHEMA_VERSION_CURRENT
from kibo_converter.domain.file_selection import FileSelectionRules
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.job_types import JobType
from kibo_converter.domain.job_ui_models import CandidateReviewStatus, OutputPreviewAction
from kibo_converter.domain.output_rules import CollisionPolicy, OutputRules
from kibo_converter.domain.processing_steps import ImageOutputFormat, ResizeOptions


def _write_png_image(path: Path, *, color: tuple[int, int, int] = (20, 40, 60)) -> None:
    image = Image.new("RGB", (16, 16), color=color)
    image.save(path, format="PNG")


def _build_image_job_definition(
    *,
    input_directory_path: Path,
    output_directory_path: Path,
    collision_policy: CollisionPolicy = CollisionPolicy.KEEP_BOTH_OUTPUTS,
) -> JobDefinition:
    return JobDefinition(
        schema_version=JOB_SCHEMA_VERSION_CURRENT,
        selection_rules=FileSelectionRules(
            input_directory_path=input_directory_path,
            included_file_extensions_lower_case=frozenset({".png"}),
            include_subdirectories_recursively=False,
        ),
        output_format=ImageOutputFormat.PNG,
        resize_options=ResizeOptions(max_edge_pixels=None),
        output_rules=OutputRules(
            output_directory_path=output_directory_path,
            collision_policy=collision_policy,
        ),
        job_type=JobType.IMAGE_CONVERSION,
    )


def test_build_job_preview_snapshot_classifies_candidates_and_outputs(tmp_path: Path) -> None:
    input_directory_path = tmp_path / "input"
    output_directory_path = tmp_path / "output"
    input_directory_path.mkdir()
    output_directory_path.mkdir()

    valid_png_path = input_directory_path / "valid.png"
    broken_png_path = input_directory_path / "broken.png"
    unsupported_text_path = input_directory_path / "notes.txt"
    appledouble_png_path = input_directory_path / "._valid.png"

    _write_png_image(valid_png_path)
    broken_png_path.write_bytes(b"not-a-real-png")
    unsupported_text_path.write_text("hello", encoding="utf-8")
    appledouble_png_path.write_bytes(b"sidecar")

    snapshot = build_job_preview_snapshot(
        _build_image_job_definition(
            input_directory_path=input_directory_path,
            output_directory_path=output_directory_path,
        )
    )

    candidates_by_name = {item.source_path.name: item for item in snapshot.candidate_items}

    assert candidates_by_name["valid.png"].status == CandidateReviewStatus.INCLUDED
    assert candidates_by_name["valid.png"].is_selected is True
    assert candidates_by_name["broken.png"].status == CandidateReviewStatus.ERROR
    assert candidates_by_name["notes.txt"].status == CandidateReviewStatus.EXCLUDED
    assert candidates_by_name["._valid.png"].status == CandidateReviewStatus.EXCLUDED

    assert len(snapshot.output_preview_items) == 1
    assert snapshot.output_preview_items[0].source_path == valid_png_path
    assert snapshot.output_preview_items[0].action == OutputPreviewAction.CREATE_NEW


def test_build_job_preview_snapshot_respects_manual_exclusion(tmp_path: Path) -> None:
    input_directory_path = tmp_path / "input"
    output_directory_path = tmp_path / "output"
    input_directory_path.mkdir()
    output_directory_path.mkdir()

    included_png_path = input_directory_path / "valid.png"
    _write_png_image(included_png_path)

    snapshot = build_job_preview_snapshot(
        _build_image_job_definition(
            input_directory_path=input_directory_path,
            output_directory_path=output_directory_path,
        ),
        manually_excluded_source_paths=frozenset({included_png_path}),
    )

    assert snapshot.candidate_items[0].status == CandidateReviewStatus.EXCLUDED_BY_USER
    assert snapshot.candidate_items[0].is_selected is False
    assert snapshot.output_preview_items == []


def test_build_job_preview_snapshot_marks_existing_output_as_overwrite(tmp_path: Path) -> None:
    input_directory_path = tmp_path / "input"
    output_directory_path = tmp_path / "output"
    input_directory_path.mkdir()
    output_directory_path.mkdir()

    included_png_path = input_directory_path / "valid.png"
    _write_png_image(included_png_path, color=(99, 11, 22))
    _write_png_image(output_directory_path / "valid.png", color=(1, 2, 3))

    snapshot = build_job_preview_snapshot(
        _build_image_job_definition(
            input_directory_path=input_directory_path,
            output_directory_path=output_directory_path,
            collision_policy=CollisionPolicy.OVERWRITE_EXISTING_OUTPUT,
        )
    )

    assert snapshot.output_preview_items[0].action == OutputPreviewAction.OVERWRITE
