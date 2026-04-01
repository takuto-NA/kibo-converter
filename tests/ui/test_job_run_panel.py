# Responsibility: UI tests for execution panel clarity and state transitions.

from __future__ import annotations

from kibo_converter.ui.job_run_panel import JobRunPanelWidget


def test_job_run_panel_starts_with_clear_ready_state(qtbot) -> None:
    widget = JobRunPanelWidget()
    qtbot.addWidget(widget)

    assert "準備完了" in widget.status_text()
    assert "変換を実行" in widget.helper_text()


def test_job_run_panel_running_state_enables_cancel_button(qtbot) -> None:
    widget = JobRunPanelWidget()
    qtbot.addWidget(widget)

    widget.set_running_state(is_running=True)

    assert widget.cancel_button().isEnabled() is True
