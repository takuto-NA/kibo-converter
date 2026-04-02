"""Responsibility: Show pre-run candidate files and let the user exclude individual items."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHeaderView, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from kibo_converter.domain.job_ui_models import CandidateReviewItem, CandidateReviewStatus


class CandidateReviewPanelWidget(QWidget):
    """Table of included, excluded, and errored candidates before execution."""

    selection_changed = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._updating_table = False
        self._source_path_by_row: dict[int, Path] = {}
        self._status_by_row: dict[int, CandidateReviewStatus] = {}
        self._table_widget = QTableWidget(0, 5)
        self._table_widget.setHorizontalHeaderLabels(["実行", "ファイル", "拡張子", "判定", "理由"])
        header = self._table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._table_widget.itemChanged.connect(self._handle_item_changed)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("変換候補一覧"))
        layout.addWidget(self._table_widget)
        self.setLayout(layout)

    def set_candidate_items(self, candidate_items: list[CandidateReviewItem]) -> None:
        """Replace all rows with the latest candidate review result."""
        self._updating_table = True
        self._source_path_by_row.clear()
        self._status_by_row.clear()
        self._table_widget.setRowCount(len(candidate_items))
        for row_index, candidate_item in enumerate(candidate_items):
            self._source_path_by_row[row_index] = candidate_item.source_path
            self._status_by_row[row_index] = candidate_item.status

            selection_item = QTableWidgetItem()
            selection_item.setFlags(
                Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
            )
            if candidate_item.status not in (
                CandidateReviewStatus.INCLUDED,
                CandidateReviewStatus.EXCLUDED_BY_USER,
            ):
                selection_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            selection_item.setCheckState(
                Qt.CheckState.Checked if candidate_item.is_selected else Qt.CheckState.Unchecked
            )
            self._table_widget.setItem(row_index, 0, selection_item)
            self._table_widget.setItem(row_index, 1, QTableWidgetItem(str(candidate_item.source_path)))
            self._table_widget.setItem(row_index, 2, QTableWidgetItem(candidate_item.extension_lower_case))
            self._table_widget.setItem(row_index, 3, QTableWidgetItem(candidate_item.status.value))
            self._table_widget.setItem(row_index, 4, QTableWidgetItem(candidate_item.reason))
        self._updating_table = False

    def _handle_item_changed(self, item: QTableWidgetItem) -> None:
        if self._updating_table:
            return
        if item.column() != 0:
            return
        self.selection_changed.emit(self.manually_excluded_source_paths())

    def manually_excluded_source_paths(self) -> frozenset[Path]:
        """Return included rows that the user has unchecked."""
        manually_excluded_source_paths: set[Path] = set()
        for row_index, source_path in self._source_path_by_row.items():
            if self._status_by_row[row_index] not in (
                CandidateReviewStatus.INCLUDED,
                CandidateReviewStatus.EXCLUDED_BY_USER,
            ):
                continue
            selection_item = self._table_widget.item(row_index, 0)
            if selection_item is None:
                continue
            if selection_item.checkState() != Qt.CheckState.Checked:
                manually_excluded_source_paths.add(source_path)
        return frozenset(manually_excluded_source_paths)

    def set_row_checked(self, row_index: int, is_checked: bool) -> None:
        """Update one row checkbox for tests and future UI integrations."""
        selection_item = self._table_widget.item(row_index, 0)
        if selection_item is None:
            raise IndexError(f"Candidate review row does not exist: {row_index}")
        selection_item.setCheckState(Qt.CheckState.Checked if is_checked else Qt.CheckState.Unchecked)

    def row_count(self) -> int:
        """Expose visible row count for tests."""
        return self._table_widget.rowCount()
