# Responsibility: Smoke tests for main window construction and basic widgets.

from __future__ import annotations

from kibo_converter.ui.main_window import MainWindow
from kibo_converter.domain.job_types import JobType


def test_main_window_constructs(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    assert window.windowTitle() == "Kibo Converter"


def test_main_window_defaults_to_image_job_with_catalog_entries(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.current_job_type() == JobType.IMAGE_CONVERSION
    catalog_titles = window.job_catalog_titles()
    assert any("画像変換" in title for title in catalog_titles)
    assert any("動画変換" in title for title in catalog_titles)
    assert any("文書変換" in title for title in catalog_titles)


def test_main_window_starts_with_candidate_and_output_panels(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.candidate_review_row_count() == 0
    assert window.output_preview_row_count() == 0
