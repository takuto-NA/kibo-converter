# Responsibility: UI tests for output preview table behavior.

from __future__ import annotations

from pathlib import Path

from kibo_converter.domain.job_ui_models import OutputPreviewAction, OutputPreviewItem
from kibo_converter.ui.output_preview_panel import OutputPreviewPanelWidget


def test_output_preview_panel_populates_rows(qtbot) -> None:
    widget = OutputPreviewPanelWidget()
    qtbot.addWidget(widget)

    widget.set_output_preview_items(
        [
            OutputPreviewItem(
                source_path=Path("C:/input/a.png"),
                target_path=Path("C:/output/a.webp"),
                action=OutputPreviewAction.CREATE_NEW,
                note="新しい出力ファイルを作成します。",
            )
        ]
    )

    assert widget.row_count() == 1
