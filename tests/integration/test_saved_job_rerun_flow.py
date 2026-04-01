# Responsibility: Integration tests for saving and reloading job JSON outside the UI.

from __future__ import annotations

from pathlib import Path

from kibo_converter.application.job_persistence import load_job_definition_from_json_file, save_job_definition_to_json_file
from kibo_converter.constants import JOB_SCHEMA_VERSION_CURRENT
from kibo_converter.domain.file_selection import FileSelectionRules
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.output_rules import CollisionPolicy, OutputRules
from kibo_converter.domain.processing_steps import ImageOutputFormat, ResizeOptions


def test_saved_job_can_be_reloaded_and_matches(tmp_path: Path) -> None:
    input_dir = tmp_path / "in"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    output_dir.mkdir()

    original = JobDefinition(
        schema_version=JOB_SCHEMA_VERSION_CURRENT,
        selection_rules=FileSelectionRules(
            input_directory_path=input_dir,
            included_file_extensions_lower_case=frozenset({".heic", ".png"}),
            include_subdirectories_recursively=True,
        ),
        output_format=ImageOutputFormat.PNG,
        resize_options=ResizeOptions(max_edge_pixels=2048),
        output_rules=OutputRules(
            output_directory_path=output_dir,
            collision_policy=CollisionPolicy.KEEP_BOTH_OUTPUTS,
        ),
    )

    job_path = tmp_path / "job.json"
    save_job_definition_to_json_file(original, job_path)
    reloaded = load_job_definition_from_json_file(job_path)

    assert reloaded.selection_rules.input_directory_path == original.selection_rules.input_directory_path
    assert reloaded.output_rules.collision_policy == original.output_rules.collision_policy
    assert reloaded.resize_options.max_edge_pixels == original.resize_options.max_edge_pixels
