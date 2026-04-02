"""Responsibility: Show expected output paths and write actions before execution starts."""

from __future__ import annotations

from PyQt6.QtWidgets import QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from kibo_converter.domain.job_ui_models import OutputPreviewItem


class OutputPreviewPanelWidget(QWidget):
    """Table of predicted output files before the job runs."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._table_widget = QTableWidget(0, 4)
        self._table_widget.setHorizontalHeaderLabels(["入力", "出力", "動作", "補足"])
        header = self._table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("出力プレビュー"))
        layout.addWidget(self._table_widget)
        self.setLayout(layout)

    def set_output_preview_items(self, output_preview_items: list[OutputPreviewItem]) -> None:
        """Replace all preview rows."""
        self._table_widget.setRowCount(len(output_preview_items))
        for row_index, output_preview_item in enumerate(output_preview_items):
            self._table_widget.setItem(row_index, 0, QTableWidgetItem(str(output_preview_item.source_path)))
            self._table_widget.setItem(row_index, 1, QTableWidgetItem(str(output_preview_item.target_path)))
            self._table_widget.setItem(row_index, 2, QTableWidgetItem(output_preview_item.action.value))
            self._table_widget.setItem(row_index, 3, QTableWidgetItem(output_preview_item.note))

    def row_count(self) -> int:
        """Expose visible row count for tests."""
        return self._table_widget.rowCount()
