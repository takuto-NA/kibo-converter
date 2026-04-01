# Responsibility: Shared pytest fixtures for HEIC samples and Qt application lifecycle.

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture(scope="session")
def qapplication_session(qapp):
    """Expose shared QApplication for UI tests."""
    return qapp


def _try_create_heic_file(target_path: Path) -> bool:
    """
    Create a minimal HEIC file for integration tests.

    Returns True when the file was written successfully.
    """
    try:
        from pillow_heif import register_heif_opener

        register_heif_opener()
    except Exception:
        return False

    image = Image.new("RGB", (64, 64), color=(200, 30, 40))
    try:
        image.save(target_path, format="HEIF")
    except Exception:
        return False
    return target_path.is_file()


@pytest.fixture
def heic_sample_path(tmp_path: Path) -> Path:
    """Provide a HEIC file path; skip test if HEIC encoding is unavailable."""
    heic_path = tmp_path / "generated_sample.heic"
    if _try_create_heic_file(heic_path):
        return heic_path

    fixture_path = Path(__file__).resolve().parent / "fixtures" / "images" / "sample_iphone.heic"
    if fixture_path.is_file():
        return fixture_path

    pytest.skip("HEIC encoding unavailable and no sample_iphone.heic fixture present.")
