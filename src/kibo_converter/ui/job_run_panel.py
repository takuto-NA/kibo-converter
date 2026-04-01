# Responsibility: Show job execution progress, errors, and cancellation controls.

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class JobRunPanelWidget(QWidget):
    """Displays progress and recent errors while a job runs."""

    cancel_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._status_label = QLabel("Ready to start")
        self._helper_label = QLabel(
            "Press Run after you finish the settings above. Progress, errors, and cancellations appear here."
        )
        self._helper_label.setWordWrap(True)
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 1)
        self._progress_bar.setValue(0)

        self._log_view = QPlainTextEdit()
        self._log_view.setReadOnly(True)

        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.setEnabled(False)
        self._cancel_button.clicked.connect(self.cancel_requested.emit)

        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)
        buttons_row.addWidget(self._cancel_button)

        layout = QVBoxLayout()
        layout.addWidget(self._status_label)
        layout.addWidget(self._helper_label)
        layout.addWidget(self._progress_bar)
        layout.addWidget(self._log_view)
        layout.addLayout(buttons_row)
        self.setLayout(layout)

    def set_running_state(self, *, is_running: bool) -> None:
        """Enable or disable controls appropriate for running state."""
        self._cancel_button.setEnabled(is_running)
        if is_running:
            self._helper_label.setText("Run in progress. You can cancel safely; completed files stay written.")
        else:
            self._helper_label.setText(
                "Press Run after you finish the settings above. Progress, errors, and cancellations appear here."
            )

    def set_status_text(self, text: str) -> None:
        """Update the single-line status label."""
        self._status_label.setText(text)

    def set_progress(self, *, completed: int, total: int) -> None:
        """Update progress bar range and value."""
        safe_total = max(total, 0)
        self._progress_bar.setRange(0, max(safe_total, 1))
        self._progress_bar.setValue(min(completed, safe_total))

    def append_log_line(self, line: str) -> None:
        """Append one log line to the read-only console."""
        self._log_view.appendPlainText(line)

    def status_text(self) -> str:
        """Expose the visible status text for tests and UI integrations."""
        return self._status_label.text()

    def helper_text(self) -> str:
        """Expose the visible helper text for tests."""
        return self._helper_label.text()

    def cancel_button(self) -> QPushButton:
        """Expose the cancel button for tests."""
        return self._cancel_button
