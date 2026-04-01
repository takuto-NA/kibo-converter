# Responsibility: Enumerate files under an input folder matching extension rules.

from __future__ import annotations

from pathlib import Path

from kibo_converter.domain.file_selection import FileSelectionRules
from kibo_converter.infrastructure.input_path_filter import is_path_excluded_by_default_scan_rules


def list_matching_files(selection_rules: FileSelectionRules) -> list[Path]:
    """Return sorted file paths that match the configured extensions."""
    paths, _excluded = list_matching_files_with_exclusion_count(selection_rules)
    return paths


def list_matching_files_with_exclusion_count(
    selection_rules: FileSelectionRules,
) -> tuple[list[Path], int]:
    """
    Return matching paths and how many candidates were excluded by default rules.

    Extension-only matches that are known OS sidecars (e.g. ._*.HEIC) are dropped
    so they do not appear as conversion failures.
    """
    root = selection_rules.input_directory_path
    if not root.is_dir():
        return [], 0

    allowed = selection_rules.included_file_extensions_lower_case
    matches: list[Path] = []
    excluded_count = 0

    if selection_rules.include_subdirectories_recursively:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in allowed:
                continue
            if is_path_excluded_by_default_scan_rules(path):
                excluded_count += 1
                continue
            matches.append(path)
    else:
        for path in root.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower() not in allowed:
                continue
            if is_path_excluded_by_default_scan_rules(path):
                excluded_count += 1
                continue
            matches.append(path)

    matches.sort(key=lambda p: str(p).lower())
    return matches, excluded_count
