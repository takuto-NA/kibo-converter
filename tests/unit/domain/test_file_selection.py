# Responsibility: Unit tests for file selection rule validation.

from __future__ import annotations

from pathlib import Path

import pytest

from kibo_converter.domain.file_selection import FileSelectionRules


def test_file_selection_requires_at_least_one_extension() -> None:
    selection_rules = FileSelectionRules(
        input_directory_path=Path("C:/input"),
        included_file_extensions_lower_case=frozenset(),
        include_subdirectories_recursively=True,
    )

    with pytest.raises(ValueError, match="At least one file extension"):
        selection_rules.validate()


def test_file_selection_accepts_current_directory_path() -> None:
    selection_rules = FileSelectionRules(
        input_directory_path=Path("."),
        included_file_extensions_lower_case=frozenset({".png"}),
        include_subdirectories_recursively=True,
    )

    selection_rules.validate()
