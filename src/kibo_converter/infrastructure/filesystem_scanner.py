# Responsibility: Enumerate files under an input folder matching extension rules.

from __future__ import annotations

from pathlib import Path

from kibo_converter.domain.file_selection import FileSelectionRules


def list_matching_files(selection_rules: FileSelectionRules) -> list[Path]:
    """Return sorted file paths that match the configured extensions."""
    root = selection_rules.input_directory_path
    if not root.is_dir():
        return []

    allowed = selection_rules.included_file_extensions_lower_case
    matches: list[Path] = []

    if selection_rules.include_subdirectories_recursively:
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() in allowed:
                matches.append(path)
    else:
        for path in root.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower() in allowed:
                matches.append(path)

    matches.sort(key=lambda p: str(p).lower())
    return matches
