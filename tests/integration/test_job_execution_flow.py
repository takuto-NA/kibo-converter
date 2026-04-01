# Responsibility: Integration tests for background job execution and Qt signal wiring.

from __future__ import annotations

from pathlib import Path

import pytest
from PyQt6.QtCore import QCoreApplication

from kibo_converter.application.job_executor import ImageConversionWorker, ImageJobThreadController
from kibo_converter.constants import JOB_SCHEMA_VERSION_CURRENT
from kibo_converter.domain.file_selection import FileSelectionRules
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.output_rules import CollisionPolicy, OutputRules
from kibo_converter.domain.processing_steps import ImageOutputFormat, ResizeOptions


@pytest.fixture
def qapplication_instance(qapp):
    """Ensure Qt application exists for thread and signal delivery."""
    return qapp


def test_worker_finishes_with_zero_files(qtbot, tmp_path: Path, qapplication_instance: QCoreApplication) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    output_dir.mkdir()

    job_definition = JobDefinition(
        schema_version=JOB_SCHEMA_VERSION_CURRENT,
        selection_rules=FileSelectionRules(
            input_directory_path=input_dir,
            included_file_extensions_lower_case=frozenset({".png"}),
            include_subdirectories_recursively=False,
        ),
        output_format=ImageOutputFormat.PNG,
        resize_options=ResizeOptions(max_edge_pixels=None),
        output_rules=OutputRules(
            output_directory_path=output_dir,
            collision_policy=CollisionPolicy.OVERWRITE_EXISTING_OUTPUT,
        ),
    )

    worker = ImageConversionWorker(job_definition=job_definition, log_file_path=None)

    with qtbot.waitSignal(worker.job_finished, timeout=10_000) as blocker:
        worker.run_conversion_job()

    summary = blocker.args[0]
    assert summary.total_files == 0


def test_worker_finishes_with_zero_matches_when_only_appledouble_sidecars_exist(
    qtbot,
    tmp_path: Path,
    qapplication_instance: QCoreApplication,
) -> None:
    """Real-world: ._*.HEIC must not be conversion targets; they must not count as failures."""
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    output_dir.mkdir()
    (input_dir / "._IMG_9999.HEIC").write_bytes(b"x")

    job_definition = JobDefinition(
        schema_version=JOB_SCHEMA_VERSION_CURRENT,
        selection_rules=FileSelectionRules(
            input_directory_path=input_dir,
            included_file_extensions_lower_case=frozenset({".heic"}),
            include_subdirectories_recursively=False,
        ),
        output_format=ImageOutputFormat.PNG,
        resize_options=ResizeOptions(max_edge_pixels=None),
        output_rules=OutputRules(
            output_directory_path=output_dir,
            collision_policy=CollisionPolicy.OVERWRITE_EXISTING_OUTPUT,
        ),
    )

    worker = ImageConversionWorker(job_definition=job_definition, log_file_path=None)

    with qtbot.waitSignal(worker.job_finished, timeout=10_000) as blocker:
        worker.run_conversion_job()

    summary = blocker.args[0]
    assert summary.total_files == 0
    assert summary.excluded_by_filter_count == 1
    assert summary.failure_count == 0


def test_thread_controller_runs_job_without_blocking_ui(qtbot, tmp_path: Path, qapplication_instance: QCoreApplication) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    output_dir.mkdir()

    job_definition = JobDefinition(
        schema_version=JOB_SCHEMA_VERSION_CURRENT,
        selection_rules=FileSelectionRules(
            input_directory_path=input_dir,
            included_file_extensions_lower_case=frozenset({".png"}),
            include_subdirectories_recursively=False,
        ),
        output_format=ImageOutputFormat.PNG,
        resize_options=ResizeOptions(max_edge_pixels=None),
        output_rules=OutputRules(
            output_directory_path=output_dir,
            collision_policy=CollisionPolicy.OVERWRITE_EXISTING_OUTPUT,
        ),
    )

    controller = ImageJobThreadController()
    worker = controller.start_job(job_definition=job_definition, log_file_path=None)

    with qtbot.waitSignal(worker.job_finished, timeout=10_000):
        pass

    assert controller.wait_until_finished(timeout_milliseconds=10_000) is True
