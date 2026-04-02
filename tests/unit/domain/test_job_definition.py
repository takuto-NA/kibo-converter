# Responsibility: Unit tests for JobDefinition validation rules.

from __future__ import annotations

import pytest

from kibo_converter.constants import JOB_SCHEMA_VERSION_CURRENT
from kibo_converter.domain.file_selection import FileSelectionRules
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.job_types import JobType
from kibo_converter.domain.job_ui_models import ImageConversionJobSettings, SharedJobSettings
from kibo_converter.domain.output_rules import CollisionPolicy, OutputRules
from kibo_converter.domain.processing_steps import ImageOutputFormat, ResizeOptions


def test_job_definition_rejects_wrong_schema_version() -> None:
    selection_rules = FileSelectionRules(
        input_directory_path=__import__("pathlib").Path("C:/in"),
        included_file_extensions_lower_case=frozenset({".heic"}),
        include_subdirectories_recursively=False,
    )
    job_definition = JobDefinition(
        schema_version=999,
        selection_rules=selection_rules,
        output_format=ImageOutputFormat.PNG,
        resize_options=ResizeOptions(max_edge_pixels=None),
        output_rules=OutputRules(
            output_directory_path=__import__("pathlib").Path("C:/out"),
            collision_policy=CollisionPolicy.KEEP_BOTH_OUTPUTS,
        ),
    )

    with pytest.raises(ValueError, match="schema_version"):
        job_definition.validate()


def test_job_definition_accepts_current_schema_version() -> None:
    pathlib = __import__("pathlib")
    selection_rules = FileSelectionRules(
        input_directory_path=pathlib.Path("C:/in"),
        included_file_extensions_lower_case=frozenset({".heic"}),
        include_subdirectories_recursively=True,
    )
    job_definition = JobDefinition(
        schema_version=JOB_SCHEMA_VERSION_CURRENT,
        selection_rules=selection_rules,
        output_format=ImageOutputFormat.PNG,
        resize_options=ResizeOptions(max_edge_pixels=1024),
        output_rules=OutputRules(
            output_directory_path=pathlib.Path("C:/out"),
            collision_policy=CollisionPolicy.OVERWRITE_EXISTING_OUTPUT,
        ),
    )

    job_definition.validate()


def test_job_definition_exposes_shared_and_image_specific_settings() -> None:
    pathlib = __import__("pathlib")
    selection_rules = FileSelectionRules(
        input_directory_path=pathlib.Path("C:/in"),
        included_file_extensions_lower_case=frozenset({".heic", ".png"}),
        include_subdirectories_recursively=True,
    )
    resize_options = ResizeOptions(max_edge_pixels=1024)
    output_rules = OutputRules(
        output_directory_path=pathlib.Path("C:/out"),
        collision_policy=CollisionPolicy.KEEP_BOTH_OUTPUTS,
    )
    job_definition = JobDefinition(
        schema_version=JOB_SCHEMA_VERSION_CURRENT,
        selection_rules=selection_rules,
        output_format=ImageOutputFormat.WEBP,
        resize_options=resize_options,
        output_rules=output_rules,
        job_type=JobType.IMAGE_CONVERSION,
    )

    assert job_definition.shared_settings == SharedJobSettings(
        input_directory_path=pathlib.Path("C:/in"),
        output_directory_path=pathlib.Path("C:/out"),
        collision_policy=CollisionPolicy.KEEP_BOTH_OUTPUTS,
    )
    assert job_definition.image_conversion_settings == ImageConversionJobSettings(
        included_file_extensions_lower_case=frozenset({".heic", ".png"}),
        include_subdirectories_recursively=True,
        output_format=ImageOutputFormat.WEBP,
        resize_options=resize_options,
    )
