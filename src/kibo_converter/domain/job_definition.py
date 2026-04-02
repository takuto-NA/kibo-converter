"""Responsibility: Immutable job definition contract with job type and grouped settings views."""

from __future__ import annotations

from dataclasses import dataclass

from kibo_converter.constants import JOB_SCHEMA_VERSION_CURRENT
from kibo_converter.domain.file_selection import FileSelectionRules
from kibo_converter.domain.job_types import JobType
from kibo_converter.domain.job_ui_models import ImageConversionJobSettings, SharedJobSettings
from kibo_converter.domain.output_rules import OutputRules
from kibo_converter.domain.processing_steps import ImageOutputFormat, ResizeOptions


@dataclass(frozen=True, slots=True)
class JobDefinition:
    """User-defined batch job: selection, processing, and output rules."""

    schema_version: int
    selection_rules: FileSelectionRules
    output_format: ImageOutputFormat
    resize_options: ResizeOptions
    output_rules: OutputRules
    job_type: JobType = JobType.IMAGE_CONVERSION

    def validate(self) -> None:
        """Raise ValueError when the job cannot be executed."""
        if self.schema_version != JOB_SCHEMA_VERSION_CURRENT:
            raise ValueError(
                f"Unsupported schema_version: {self.schema_version}. "
                f"Expected: {JOB_SCHEMA_VERSION_CURRENT}."
            )
        if self.job_type != JobType.IMAGE_CONVERSION:
            raise ValueError(f"Unsupported job_type: {self.job_type.value}.")
        self.selection_rules.validate()
        self.resize_options.validate()
        self.output_rules.validate()

    @property
    def shared_settings(self) -> SharedJobSettings:
        """Grouped shared settings for job-centered UI composition."""
        return SharedJobSettings(
            input_directory_path=self.selection_rules.input_directory_path,
            output_directory_path=self.output_rules.output_directory_path,
            collision_policy=self.output_rules.collision_policy,
        )

    @property
    def image_conversion_settings(self) -> ImageConversionJobSettings:
        """Grouped image-specific settings for job-centered UI composition."""
        return ImageConversionJobSettings(
            included_file_extensions_lower_case=self.selection_rules.included_file_extensions_lower_case,
            include_subdirectories_recursively=self.selection_rules.include_subdirectories_recursively,
            output_format=self.output_format,
            resize_options=self.resize_options,
        )
