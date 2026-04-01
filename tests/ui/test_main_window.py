# Responsibility: Smoke tests for main window construction and basic widgets.

from __future__ import annotations

from kibo_converter.ui.main_window import MainWindow


def test_main_window_constructs(qtbot) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    assert window.windowTitle() == "Kibo Converter"
