# Responsibility: Unit tests for preflight checks before a conversion job starts.

from __future__ import annotations

from pathlib import Path

import pytest

from kibo_converter.application import job_preflight
from kibo_converter.application.job_preflight import JobPreflightError, run_job_preflight
from kibo_converter.constants import JOB_SCHEMA_VERSION_CURRENT
from kibo_converter.domain.file_selection import FileSelectionRules
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.output_rules import CollisionPolicy, OutputRules
from kibo_converter.domain.processing_steps import ImageOutputFormat, ResizeOptions
from kibo_converter.infrastructure.image_reader_writer import HeifSupportInitializationError


def _build_job_definition(
    *,
    input_directory_path: Path,
    output_directory_path: Path,
    included_extensions_lower_case: frozenset[str],
) -> JobDefinition:
    return JobDefinition(
        schema_version=JOB_SCHEMA_VERSION_CURRENT,
        selection_rules=FileSelectionRules(
            input_directory_path=input_directory_path,
            included_file_extensions_lower_case=included_extensions_lower_case,
            include_subdirectories_recursively=True,
        ),
        output_format=ImageOutputFormat.PNG,
        resize_options=ResizeOptions(max_edge_pixels=None),
        output_rules=OutputRules(
            output_directory_path=output_directory_path,
            collision_policy=CollisionPolicy.KEEP_BOTH_OUTPUTS,
        ),
    )


def test_preflight_does_not_require_heif_for_non_heic_job(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_directory_path = tmp_path / "input"
    output_directory_path = tmp_path / "output"
    input_directory_path.mkdir()
    output_directory_path.mkdir()

    job_definition = _build_job_definition(
        input_directory_path=input_directory_path,
        output_directory_path=output_directory_path,
        included_extensions_lower_case=frozenset({".png"}),
    )

    def _unexpected_heif_registration_call() -> None:
        raise AssertionError("HEIF registration should not be required for a PNG-only job.")

    monkeypatch.setattr(
        job_preflight,
        "ensure_heif_support_registered",
        _unexpected_heif_registration_call,
    )

    run_job_preflight(job_definition)


def test_preflight_requires_heif_when_heic_is_in_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_directory_path = tmp_path / "input"
    output_directory_path = tmp_path / "output"
    input_directory_path.mkdir()
    output_directory_path.mkdir()

    job_definition = _build_job_definition(
        input_directory_path=input_directory_path,
        output_directory_path=output_directory_path,
        included_extensions_lower_case=frozenset({".heic"}),
    )

    def _failing_heif_registration() -> None:
        raise HeifSupportInitializationError("missing heif runtime")

    monkeypatch.setattr(
        job_preflight,
        "ensure_heif_support_registered",
        _failing_heif_registration,
    )

    with pytest.raises(JobPreflightError, match="HEIC"):
        run_job_preflight(job_definition)


def test_preflight_rejects_unwritable_output_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_directory_path = tmp_path / "input"
    output_directory_path = tmp_path / "output"
    input_directory_path.mkdir()
    output_directory_path.mkdir()

    job_definition = _build_job_definition(
        input_directory_path=input_directory_path,
        output_directory_path=output_directory_path,
        included_extensions_lower_case=frozenset({".png"}),
    )

    monkeypatch.setattr(job_preflight, "is_output_directory_writable", lambda path: False)

    with pytest.raises(JobPreflightError, match="書き込み"):
        run_job_preflight(job_definition)
