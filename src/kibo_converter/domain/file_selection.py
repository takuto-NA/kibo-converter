# Responsibility: Rules for selecting input files from a folder (extensions, recursion).

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileSelectionRules:
    """Which files under the input folder are included in the job."""

    input_directory_path: Path
    included_file_extensions_lower_case: frozenset[str]
    include_subdirectories_recursively: bool

    def validate(self) -> None:
        """Raise ValueError when selection rules are unusable."""
        if not self.included_file_extensions_lower_case:
            raise ValueError("At least one file extension must be included.")
