# Responsibility: Immutable job definition contract validated before execution or persistence.

from __future__ import annotations

from dataclasses import dataclass

from kibo_converter.constants import JOB_SCHEMA_VERSION_CURRENT
from kibo_converter.domain.file_selection import FileSelectionRules
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

    def validate(self) -> None:
        """Raise ValueError when the job cannot be executed."""
        if self.schema_version != JOB_SCHEMA_VERSION_CURRENT:
            raise ValueError(
                f"Unsupported schema_version: {self.schema_version}. "
                f"Expected: {JOB_SCHEMA_VERSION_CURRENT}."
            )
        self.selection_rules.validate()
        self.resize_options.validate()
        self.output_rules.validate()
