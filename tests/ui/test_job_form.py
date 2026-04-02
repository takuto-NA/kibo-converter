# Responsibility: UI tests for form clarity and beginner-friendly defaults.

from __future__ import annotations

from pathlib import Path

from kibo_converter.ui.job_form import JobFormWidget
from kibo_converter.domain.job_types import JobType
from kibo_converter.domain.job_ui_models import SharedJobSettings
from kibo_converter.domain.output_rules import CollisionPolicy


def test_job_form_has_clear_placeholders_and_guidance(qtbot) -> None:
    widget = JobFormWidget()
    qtbot.addWidget(widget)

    assert widget.browse_input_folder_line_edit().placeholderText() != ""
    assert widget.browse_output_folder_line_edit().placeholderText() != ""
    assert "画像変換" in widget.form_guidance_text()
    assert widget.current_job_type() == JobType.IMAGE_CONVERSION


def test_job_form_keeps_resize_input_disabled_until_enabled(qtbot) -> None:
    widget = JobFormWidget()
    qtbot.addWidget(widget)

    assert widget.resize_spin_box().isEnabled() is False

    widget.resize_checkbox().setChecked(True)

    assert widget.resize_spin_box().isEnabled() is True


def test_job_form_exposes_shared_settings_snapshot(qtbot) -> None:
    widget = JobFormWidget()
    qtbot.addWidget(widget)

    widget.browse_input_folder_line_edit().setText("C:/input")
    widget.browse_output_folder_line_edit().setText("C:/output")

    assert widget.read_shared_settings() == SharedJobSettings(
        input_directory_path=Path("C:/input"),
        output_directory_path=Path("C:/output"),
        collision_policy=CollisionPolicy.OVERWRITE_EXISTING_OUTPUT,
    )
