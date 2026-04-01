# Responsibility: Verify filesystem scanning respects default exclusion rules.

from __future__ import annotations

from pathlib import Path

from kibo_converter.domain.file_selection import FileSelectionRules
from kibo_converter.infrastructure.filesystem_scanner import list_matching_files_with_exclusion_count


def test_appledouble_sidecar_is_excluded_and_real_heic_is_kept(tmp_path: Path) -> None:
    """Guard: macOS ._*.HEIC must not be treated as conversion targets when a real file exists."""
    (tmp_path / "._IMG_4602.HEIC").write_bytes(b"not a real image")
    (tmp_path / "IMG_4602.HEIC").write_bytes(b"not a real image")

    selection_rules = FileSelectionRules(
        input_directory_path=tmp_path,
        included_file_extensions_lower_case=frozenset({".heic"}),
        include_subdirectories_recursively=False,
    )
    paths, excluded_count = list_matching_files_with_exclusion_count(selection_rules)

    assert excluded_count == 1
    assert paths == [tmp_path / "IMG_4602.HEIC"]


def test_thumbs_db_is_excluded_when_db_extension_is_allowed(tmp_path: Path) -> None:
    """Guard: Thumbs.db must not be converted even if '.db' is in the allowed extension list."""
    (tmp_path / "Thumbs.db").write_bytes(b"x")

    selection_rules = FileSelectionRules(
        input_directory_path=tmp_path,
        included_file_extensions_lower_case=frozenset({".db"}),
        include_subdirectories_recursively=False,
    )
    paths, excluded_count = list_matching_files_with_exclusion_count(selection_rules)

    assert excluded_count == 1
    assert paths == []
