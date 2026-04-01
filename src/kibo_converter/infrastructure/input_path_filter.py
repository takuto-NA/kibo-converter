# Responsibility: Decide whether a path should be excluded from batch input scanning by default rules.

from __future__ import annotations

from pathlib import Path

# Guard: macOS AppleDouble sidecar files on non-HFS volumes (e.g. ._IMG_1234.HEIC).
_EXCLUDED_FILENAME_PREFIX_APPLEDOUBLE = "._"

# Exact names to ignore regardless of extension (case-insensitive match on stem+suffix parts).
_EXCLUDED_EXACT_LOWER_NAMES = frozenset(
    {
        ".ds_store",
        "thumbs.db",
        "desktop.ini",
    }
)


def is_path_excluded_by_default_scan_rules(candidate_path: Path) -> bool:
    """
    Return True when the file should not be converted.

    These are common non-image sidecar or OS metadata files that may still share
    an image-like extension after copying from another OS.
    """
    name = candidate_path.name
    if name.startswith(_EXCLUDED_FILENAME_PREFIX_APPLEDOUBLE):
        return True
    if name.lower() in _EXCLUDED_EXACT_LOWER_NAMES:
        return True
    return False
