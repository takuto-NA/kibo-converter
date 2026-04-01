# Responsibility: UI tests for form clarity and beginner-friendly defaults.

from __future__ import annotations

from kibo_converter.ui.job_form import JobFormWidget


def test_job_form_has_clear_placeholders_and_guidance(qtbot) -> None:
    widget = JobFormWidget()
    qtbot.addWidget(widget)

    assert widget.browse_input_folder_line_edit().placeholderText() != ""
    assert widget.browse_output_folder_line_edit().placeholderText() != ""
    assert "HEIC" in widget.form_guidance_text()


def test_job_form_keeps_resize_input_disabled_until_enabled(qtbot) -> None:
    widget = JobFormWidget()
    qtbot.addWidget(widget)

    assert widget.resize_spin_box().isEnabled() is False

    widget.resize_checkbox().setChecked(True)

    assert widget.resize_spin_box().isEnabled() is True
