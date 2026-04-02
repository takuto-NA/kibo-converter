# Responsibility: Unit tests for JSON job persistence and fail-safe loading.

from __future__ import annotations

from pathlib import Path

import pytest

from kibo_converter.application.job_persistence import (
    JobPersistenceError,
    job_definition_to_dict,
    load_job_definition_from_json_file,
    save_job_definition_to_json_file,
)
from kibo_converter.constants import JOB_SCHEMA_VERSION_CURRENT
from kibo_converter.domain.file_selection import FileSelectionRules
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.job_types import JobType
from kibo_converter.domain.output_rules import CollisionPolicy, OutputRules
from kibo_converter.domain.processing_steps import ImageOutputFormat, ResizeOptions


def _minimal_job_definition() -> JobDefinition:
    return JobDefinition(
        schema_version=JOB_SCHEMA_VERSION_CURRENT,
        selection_rules=FileSelectionRules(
            input_directory_path=Path("C:/input"),
            included_file_extensions_lower_case=frozenset({".heic"}),
            include_subdirectories_recursively=True,
        ),
        output_format=ImageOutputFormat.PNG,
        resize_options=ResizeOptions(max_edge_pixels=None),
        output_rules=OutputRules(
            output_directory_path=Path("C:/output"),
            collision_policy=CollisionPolicy.KEEP_BOTH_OUTPUTS,
        ),
        job_type=JobType.IMAGE_CONVERSION,
    )


def test_save_load_roundtrip(tmp_path: Path) -> None:
    original = _minimal_job_definition()
    file_path = tmp_path / "job.json"

    save_job_definition_to_json_file(original, file_path)
    loaded = load_job_definition_from_json_file(file_path)

    assert job_definition_to_dict(loaded) == job_definition_to_dict(original)


def test_malformed_json_rejected(tmp_path: Path) -> None:
    file_path = tmp_path / "bad.json"
    file_path.write_text("{not json", encoding="utf-8")

    with pytest.raises(JobPersistenceError, match="読み取れません"):
        load_job_definition_from_json_file(file_path)


def test_unknown_schema_version_rejected(tmp_path: Path) -> None:
    file_path = tmp_path / "future.json"
    file_path.write_text('{"schema_version": 999999}', encoding="utf-8")

    with pytest.raises(JobPersistenceError, match="999999"):
        load_job_definition_from_json_file(file_path)


def test_missing_required_field_rejected(tmp_path: Path) -> None:
    file_path = tmp_path / "missing.json"
    file_path.write_text(
        '{"schema_version": '
        + str(JOB_SCHEMA_VERSION_CURRENT)
        + ', "selection_rules": {"input_directory_path": "C:/in"}}',
        encoding="utf-8",
    )

    with pytest.raises(JobPersistenceError):
        load_job_definition_from_json_file(file_path)


def test_empty_input_directory_path_text_rejected(tmp_path: Path) -> None:
    file_path = tmp_path / "empty-path.json"
    file_path.write_text(
        """
{
  "schema_version": 1,
  "selection_rules": {
    "input_directory_path": "   ",
    "included_file_extensions": [".heic"],
    "include_subdirectories_recursively": true
  },
  "output_format": "png",
  "resize_options": {
    "max_edge_pixels": null
  },
  "output_rules": {
    "output_directory_path": "C:/output",
    "collision_policy": "keep_both_outputs"
  }
}
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(JobPersistenceError, match="input_directory_path"):
        load_job_definition_from_json_file(file_path)


def test_job_definition_to_dict_writes_job_type_and_grouped_settings() -> None:
    payload = job_definition_to_dict(_minimal_job_definition())

    assert payload["job_type"] == JobType.IMAGE_CONVERSION.value
    assert payload["shared_settings"]["input_directory_path"] == "C:/input"
    assert payload["shared_settings"]["output_directory_path"] == "C:/output"
    assert payload["shared_settings"]["collision_policy"] == "keep_both_outputs"
    assert payload["image_conversion_settings"]["output_format"] == "png"
    assert payload["image_conversion_settings"]["included_file_extensions"] == [".heic"]


def test_load_legacy_flat_job_definition_without_job_type(tmp_path: Path) -> None:
    file_path = tmp_path / "legacy-job.json"
    file_path.write_text(
        """
{
  "schema_version": 1,
  "selection_rules": {
    "input_directory_path": "C:/input",
    "included_file_extensions": [".heic", ".jpg"],
    "include_subdirectories_recursively": true
  },
  "output_format": "png",
  "resize_options": {
    "max_edge_pixels": 1600
  },
  "output_rules": {
    "output_directory_path": "C:/output",
    "collision_policy": "keep_both_outputs"
  }
}
""".strip(),
        encoding="utf-8",
    )

    loaded = load_job_definition_from_json_file(file_path)

    assert loaded.job_type == JobType.IMAGE_CONVERSION
    assert loaded.shared_settings.input_directory_path == Path("C:/input")
    assert loaded.shared_settings.output_directory_path == Path("C:/output")
    assert loaded.image_conversion_settings.output_format == ImageOutputFormat.PNG
    assert loaded.image_conversion_settings.included_file_extensions_lower_case == frozenset(
        {".heic", ".jpg"}
    )


def test_load_legacy_payload_even_when_only_one_grouped_section_exists(tmp_path: Path) -> None:
    file_path = tmp_path / "mixed-job.json"
    file_path.write_text(
        """
{
  "schema_version": 1,
  "job_type": "image_conversion",
  "shared_settings": {
    "input_directory_path": "C:/ignored-by-legacy",
    "output_directory_path": "C:/ignored-by-legacy",
    "collision_policy": "keep_both_outputs"
  },
  "selection_rules": {
    "input_directory_path": "C:/input",
    "included_file_extensions": [".heic"],
    "include_subdirectories_recursively": false
  },
  "output_format": "webp",
  "resize_options": {
    "max_edge_pixels": null
  },
  "output_rules": {
    "output_directory_path": "C:/output",
    "collision_policy": "overwrite_existing_output"
  }
}
""".strip(),
        encoding="utf-8",
    )

    loaded = load_job_definition_from_json_file(file_path)

    assert loaded.output_format == ImageOutputFormat.WEBP
    assert loaded.output_rules.collision_policy == CollisionPolicy.OVERWRITE_EXISTING_OUTPUT
