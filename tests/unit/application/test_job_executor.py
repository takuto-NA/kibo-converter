# Responsibility: Unit and integration-style tests for worker cancellation and per-file continuation.

from __future__ import annotations

from pathlib import Path

from PIL import Image

from kibo_converter.application.job_executor import ImageConversionWorker
from kibo_converter.constants import JOB_SCHEMA_VERSION_CURRENT
from kibo_converter.domain.file_selection import FileSelectionRules
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.job_result import FileResultStatus
from kibo_converter.domain.output_rules import CollisionPolicy, OutputRules
from kibo_converter.domain.processing_steps import ImageOutputFormat, ResizeOptions


def _build_png_job_definition(input_directory_path: Path, output_directory_path: Path) -> JobDefinition:
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
            collision_policy=CollisionPolicy.OVERWRITE_EXISTING_OUTPUT,
        ),
    )


def test_worker_continues_after_one_file_fails(qtbot, tmp_path: Path) -> None:
    input_directory_path = tmp_path / "input"
    output_directory_path = tmp_path / "output"
    input_directory_path.mkdir()
    output_directory_path.mkdir()

    valid_png_path = input_directory_path / "valid.png"
    broken_png_path = input_directory_path / "broken.png"

    Image.new("RGB", (16, 16), color=(120, 40, 20)).save(valid_png_path, format="PNG")
    broken_png_path.write_bytes(b"not a real png")

    job_definition = _build_png_job_definition(input_directory_path, output_directory_path)
    worker = ImageConversionWorker(job_definition=job_definition, log_file_path=None)

    with qtbot.waitSignal(worker.job_finished, timeout=10_000) as blocker:
        worker.run_conversion_job()

    summary = blocker.args[0]
    assert summary.total_files == 2
    assert summary.success_count == 1
    assert summary.failure_count == 1
    assert (output_directory_path / "valid.png").is_file()


def test_worker_stops_starting_new_files_after_cancellation_request(qtbot, tmp_path: Path) -> None:
    input_directory_path = tmp_path / "input"
    output_directory_path = tmp_path / "output"
    input_directory_path.mkdir()
    output_directory_path.mkdir()

    for file_index in range(3):
        image_path = input_directory_path / f"image_{file_index}.png"
        Image.new("RGB", (16, 16), color=(file_index * 10, 10, 10)).save(image_path, format="PNG")

    job_definition = _build_png_job_definition(input_directory_path, output_directory_path)
    worker = ImageConversionWorker(job_definition=job_definition, log_file_path=None)

    processed_paths: list[Path] = []
    original_process_single_source_file = worker._process_single_source_file

    def _process_and_cancel(*, source_path: Path):
        processed_paths.append(source_path)
        if len(processed_paths) == 1:
            worker.request_cancel()
        return original_process_single_source_file(source_path=source_path)

    worker._process_single_source_file = _process_and_cancel  # type: ignore[method-assign]

    with qtbot.waitSignal(worker.job_finished, timeout=10_000) as blocker:
        worker.run_conversion_job()

    summary = blocker.args[0]
    assert len(processed_paths) == 1
    assert summary.success_count == 1
    assert summary.cancelled_count == 2
    assert summary.file_results[-1].status == FileResultStatus.SKIPPED_CANCELLED


def test_worker_can_run_only_selected_source_paths(qtbot, tmp_path: Path) -> None:
    input_directory_path = tmp_path / "input"
    output_directory_path = tmp_path / "output"
    input_directory_path.mkdir()
    output_directory_path.mkdir()

    selected_png_path = input_directory_path / "selected.png"
    skipped_png_path = input_directory_path / "skipped.png"
    Image.new("RGB", (16, 16), color=(30, 40, 50)).save(selected_png_path, format="PNG")
    Image.new("RGB", (16, 16), color=(60, 70, 80)).save(skipped_png_path, format="PNG")

    job_definition = _build_png_job_definition(input_directory_path, output_directory_path)
    worker = ImageConversionWorker(
        job_definition=job_definition,
        log_file_path=None,
        source_paths_override=[selected_png_path],
    )

    with qtbot.waitSignal(worker.job_finished, timeout=10_000) as blocker:
        worker.run_conversion_job()

    summary = blocker.args[0]
    assert summary.total_files == 1
    assert summary.success_count == 1
    assert (output_directory_path / "selected.png").is_file()
    assert (output_directory_path / "skipped.png").exists() is False


def test_worker_with_empty_source_override_runs_zero_files(qtbot, tmp_path: Path) -> None:
    input_directory_path = tmp_path / "input"
    output_directory_path = tmp_path / "output"
    input_directory_path.mkdir()
    output_directory_path.mkdir()

    Image.new("RGB", (16, 16), color=(30, 40, 50)).save(input_directory_path / "selected.png", format="PNG")

    job_definition = _build_png_job_definition(input_directory_path, output_directory_path)
    worker = ImageConversionWorker(
        job_definition=job_definition,
        log_file_path=None,
        source_paths_override=[],
    )

    with qtbot.waitSignal(worker.job_finished, timeout=10_000) as blocker:
        worker.run_conversion_job()

    summary = blocker.args[0]
    assert summary.total_files == 0
    assert summary.success_count == 0
    assert (output_directory_path / "selected.png").exists() is False


def test_worker_override_can_keep_preview_excluded_count(qtbot, tmp_path: Path) -> None:
    input_directory_path = tmp_path / "input"
    output_directory_path = tmp_path / "output"
    input_directory_path.mkdir()
    output_directory_path.mkdir()

    selected_png_path = input_directory_path / "selected.png"
    Image.new("RGB", (16, 16), color=(30, 40, 50)).save(selected_png_path, format="PNG")

    job_definition = _build_png_job_definition(input_directory_path, output_directory_path)
    worker = ImageConversionWorker(
        job_definition=job_definition,
        log_file_path=None,
        source_paths_override=[selected_png_path],
        excluded_by_filter_count_override=2,
    )

    with qtbot.waitSignal(worker.job_finished, timeout=10_000) as blocker:
        worker.run_conversion_job()

    summary = blocker.args[0]
    assert summary.total_files == 1
    assert summary.excluded_by_filter_count == 2
