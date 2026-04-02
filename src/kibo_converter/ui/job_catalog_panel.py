"""Responsibility: Show available and upcoming job types at the launcher entry point."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from kibo_converter.domain.job_catalog import JobCatalogEntry, build_default_job_catalog
from kibo_converter.domain.job_types import JobAvailability, JobType


class JobCatalogPanelWidget(QWidget):
    """Selectable list of current and future job types."""

    job_selected = pyqtSignal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._catalog_entries = build_default_job_catalog()
        self._list_widget = QListWidget()
        self._detail_label = QLabel()
        self._detail_label.setWordWrap(True)

        self._populate_list_widget()
        self._list_widget.currentItemChanged.connect(self._handle_current_item_changed)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("ジョブ一覧"))
        layout.addWidget(self._list_widget)
        layout.addWidget(self._detail_label)
        self.setLayout(layout)

        if self._list_widget.count() > 0:
            self._list_widget.setCurrentRow(0)

    def _populate_list_widget(self) -> None:
        for entry in self._catalog_entries:
            suffix = ""
            if entry.availability == JobAvailability.COMING_SOON:
                suffix = "（近日対応）"
            item = QListWidgetItem(f"{entry.display_name}{suffix}")
            item.setData(Qt.ItemDataRole.UserRole, entry.job_type.value)
            if entry.availability != JobAvailability.AVAILABLE:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable & ~Qt.ItemFlag.ItemIsEnabled)
            self._list_widget.addItem(item)

    def _handle_current_item_changed(
        self,
        current_item: QListWidgetItem | None,
        _previous_item: QListWidgetItem | None,
    ) -> None:
        if current_item is None:
            self._detail_label.setText("")
            return
        selected_job_type = JobType(current_item.data(Qt.ItemDataRole.UserRole))
        entry = next(entry for entry in self._catalog_entries if entry.job_type == selected_job_type)
        self._detail_label.setText(
            f"{entry.short_description}\n"
            f"入力: {entry.input_format_summary}\n"
            f"出力: {entry.output_format_summary}\n"
            f"{entry.note}"
        )
        self.job_selected.emit(selected_job_type)

    def current_job_type(self) -> JobType:
        """Return the currently selected available job type."""
        current_item = self._list_widget.currentItem()
        if current_item is None:
            return JobType.IMAGE_CONVERSION
        return JobType(current_item.data(Qt.ItemDataRole.UserRole))

    def job_titles(self) -> list[str]:
        """Expose visible job titles for tests."""
        return [self._list_widget.item(index).text() for index in range(self._list_widget.count())]
