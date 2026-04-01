# Responsibility: Rules for selecting input files from a folder (extensions, recursion).

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FileSelectionRules:
    """
    Which files under the input folder are included in the job.

    Note: After extension matching, the infrastructure scanner may drop known OS
    sidecar files (for example AppleDouble `._*`) so they never become conversion
    targets. That behavior lives in `filesystem_scanner` / `input_path_filter`.
    """

    input_directory_path: Path
    included_file_extensions_lower_case: frozenset[str]
    include_subdirectories_recursively: bool

    def validate(self) -> None:
        """Raise ValueError when selection rules are unusable."""
        if not self.included_file_extensions_lower_case:
            raise ValueError("対象にする拡張子を1つ以上指定してください。")
