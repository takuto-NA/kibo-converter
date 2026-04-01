# Responsibility: Main application window wiring form, run panel, file dialogs, and background jobs.

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kibo_converter.application.job_executor import ImageConversionWorker, ImageJobThreadController
from kibo_converter.application.job_persistence import JobPersistenceError, load_job_definition_from_json_file, save_job_definition_to_json_file
from kibo_converter.application.progress_reporter import ProgressSnapshot
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.job_result import FileResultRecord, JobRunSummary
from kibo_converter.ui.job_form import JobFormWidget
from kibo_converter.ui.job_run_panel import JobRunPanelWidget
from kibo_converter.ui.view_models import build_job_definition_from_form_state, format_job_summary_text


class MainWindow(QWidget):
    """Primary UI for configuring and running conversion jobs."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Kibo Converter")
        self._active_thread_controller: ImageJobThreadController | None = None
        self._active_worker: ImageConversionWorker | None = None

        self._job_form = JobFormWidget()
        self._job_run_panel = JobRunPanelWidget()

        self._run_button = QPushButton("Run conversion")
        self._save_job_button = QPushButton("Save job settings…")
        self._load_job_button = QPushButton("Load job settings…")

        self._run_button.clicked.connect(self._handle_run_clicked)
        self._save_job_button.clicked.connect(self._handle_save_job_clicked)
        self._load_job_button.clicked.connect(self._handle_load_job_clicked)
        self._job_form.input_folder_changed.connect(self._browse_input_folder)
        self._job_form.output_folder_changed.connect(self._browse_output_folder)
        self._job_run_panel.cancel_requested.connect(self._handle_cancel_requested)

        title = QLabel("Kibo Converter")
        title_font = title.font()
        title_font.setPointSize(title_font.pointSize() + 2)
        title_font.setBold(True)
        title.setFont(title_font)
        subtitle = QLabel("Batch-convert HEIC and other images without freezing the UI.")
        subtitle.setWordWrap(True)

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(self._run_button)
        buttons_row.addWidget(self._save_job_button)
        buttons_row.addWidget(self._load_job_button)
        buttons_row.addStretch(1)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self._job_form)
        layout.addLayout(buttons_row)
        layout.addWidget(self._job_run_panel)
        self.setLayout(layout)

    def _browse_input_folder(self) -> None:
        """Open a folder dialog and write the selection into the input field."""
        starting_directory = self._safe_existing_directory_from_path_text(
            self._job_form.browse_input_folder_line_edit().text()
        )
        selected_directory = QFileDialog.getExistingDirectory(self, "Select input folder", starting_directory)
        if not selected_directory:
            return
        self._job_form.browse_input_folder_line_edit().setText(selected_directory)

    def _browse_output_folder(self) -> None:
        """Open a folder dialog and write the selection into the output field."""
        starting_directory = self._safe_existing_directory_from_path_text(
            self._job_form.browse_output_folder_line_edit().text()
        )
        selected_directory = QFileDialog.getExistingDirectory(self, "Select output folder", starting_directory)
        if not selected_directory:
            return
        self._job_form.browse_output_folder_line_edit().setText(selected_directory)

    def _safe_existing_directory_from_path_text(self, path_text: str) -> str:
        """Return path_text if it points to an existing directory, else empty string."""
        candidate_path = Path(path_text.strip())
        if candidate_path.is_dir():
            return str(candidate_path)
        return ""

    def _handle_run_clicked(self) -> None:
        """Validate form state and start a background conversion job."""
        if self._active_thread_controller is not None:
            QMessageBox.information(self, "Busy", "A job is already running.")
            return

        try:
            form_state = self._job_form.read_form_state()
            job_definition = build_job_definition_from_form_state(form_state)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid job settings", str(exc))
            return

        log_file_path = self._default_log_file_path(job_definition)
        self._start_job_thread(job_definition=job_definition, log_file_path=log_file_path)

    def _default_log_file_path(self, job_definition: JobDefinition) -> Path:
        """Pick a default JSONL log path next to the output folder."""
        return job_definition.output_rules.output_directory_path / "kibo_converter_run.jsonl"

    def _start_job_thread(self, *, job_definition: JobDefinition, log_file_path: Path) -> None:
        """Wire worker signals and start the background thread."""
        controller = ImageJobThreadController()
        worker = controller.start_job(job_definition=job_definition, log_file_path=log_file_path)

        self._active_thread_controller = controller
        self._active_worker = worker

        self._run_button.setEnabled(False)
        self._job_run_panel.set_running_state(is_running=True)
        self._job_run_panel.set_status_text("Running conversion…")
        self._job_run_panel.set_progress(completed=0, total=0)
        self._job_run_panel.append_log_line(f"Log file: {log_file_path}")
        self._job_run_panel.append_log_line("Starting preflight checks and scanning the input folder.")

        worker.preflight_failed.connect(self._handle_preflight_failed)
        worker.progress_updated.connect(self._handle_progress_updated)
        worker.file_result_emitted.connect(self._handle_file_result)
        worker.job_finished.connect(self._handle_job_finished)

    def _handle_preflight_failed(self, message: str) -> None:
        """Show a preflight failure and reset UI state."""
        self._job_run_panel.append_log_line(f"Preflight failed: {message}")
        QMessageBox.critical(self, "Cannot start job", message)
        self._job_run_panel.set_status_text("Cannot start conversion")
        self._reset_ui_after_job_end()

    def _handle_progress_updated(self, snapshot: object) -> None:
        """Update progress UI from worker thread via queued signal delivery."""
        if not isinstance(snapshot, ProgressSnapshot):
            return
        self._job_run_panel.set_progress(completed=snapshot.completed_file_count, total=snapshot.total_file_count)

    def _handle_file_result(self, record: object) -> None:
        """Append a short line for each file result."""
        if not isinstance(record, FileResultRecord):
            return
        line = f"{record.status.value}: {record.source_path}"
        if record.error_summary:
            line += f" | {record.error_summary}"
        self._job_run_panel.append_log_line(line)

    def _handle_job_finished(self, summary: object) -> None:
        """Show final counts and reset UI state."""
        if isinstance(summary, JobRunSummary):
            self._job_run_panel.set_status_text(format_job_summary_text(summary))
            self._job_run_panel.append_log_line("Conversion finished.")
        self._reset_ui_after_job_end()

    def _reset_ui_after_job_end(self) -> None:
        """Re-enable controls after the worker thread stops."""
        self._active_thread_controller = None
        self._active_worker = None
        self._run_button.setEnabled(True)
        self._job_run_panel.set_running_state(is_running=False)

    def _handle_cancel_requested(self) -> None:
        """Forward cancellation to the active worker."""
        if self._active_worker is None:
            return
        self._job_run_panel.set_status_text("Cancelling…")
        self._active_worker.request_cancel()

    def _handle_save_job_clicked(self) -> None:
        """Save the current form state as a JSON job file."""
        try:
            form_state = self._job_form.read_form_state()
            job_definition = build_job_definition_from_form_state(form_state)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid job settings", str(exc))
            return

        default_path = Path.home() / "kibo_job.json"
        selected_filter = "JSON job (*.json)"
        file_path_text, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save job",
            str(default_path),
            selected_filter,
        )
        if not file_path_text:
            return

        try:
            save_job_definition_to_json_file(job_definition, Path(file_path_text))
        except OSError as exc:
            QMessageBox.critical(self, "Save failed", str(exc))
            return

        QMessageBox.information(self, "Saved", f"Job saved to:\n{file_path_text}")

    def _handle_load_job_clicked(self) -> None:
        """Load a JSON job file and apply it to the form fields."""
        default_path = Path.home()
        file_path_text, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Load job",
            str(default_path),
            "JSON job (*.json)",
        )
        if not file_path_text:
            return

        try:
            job_definition = load_job_definition_from_json_file(Path(file_path_text))
        except JobPersistenceError as exc:
            QMessageBox.critical(self, "Invalid job file", str(exc))
            return

        self._job_form.apply_job_definition(job_definition)
        QMessageBox.information(self, "Loaded", f"Job loaded from:\n{file_path_text}")
