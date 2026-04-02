"""Responsibility: Compose the launcher-style shell UI, preview panels, and execution flow."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from kibo_converter.application.job_executor import ImageConversionWorker, ImageJobThreadController
from kibo_converter.application.job_preview import build_job_preview_snapshot
from kibo_converter.application.job_persistence import JobPersistenceError, load_job_definition_from_json_file, save_job_definition_to_json_file
from kibo_converter.application.progress_reporter import ProgressSnapshot
from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.job_result import FileResultRecord, JobRunSummary
from kibo_converter.domain.job_types import JobType
from kibo_converter.domain.job_ui_models import JobPreviewSnapshot
from kibo_converter.domain.output_rules import CollisionPolicy
from kibo_converter.ui.candidate_review_panel import CandidateReviewPanelWidget
from kibo_converter.ui.job_form import JobFormWidget
from kibo_converter.ui.job_catalog_panel import JobCatalogPanelWidget
from kibo_converter.ui.job_run_panel import JobRunPanelWidget
from kibo_converter.ui.output_preview_panel import OutputPreviewPanelWidget
from kibo_converter.ui.view_models import (
    build_job_definition_from_form_state,
    format_file_result_line_for_user,
    format_job_summary_text,
)


class MainWindow(QWidget):
    """Primary UI for configuring and running conversion jobs."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Kibo Converter")
        self._active_thread_controller: ImageJobThreadController | None = None
        self._active_worker: ImageConversionWorker | None = None
        self._latest_preview_snapshot = JobPreviewSnapshot(candidate_items=[], output_preview_items=[])
        self._manually_excluded_source_paths: frozenset[Path] = frozenset()

        self._job_catalog_panel = JobCatalogPanelWidget()
        self._job_form = JobFormWidget()
        self._candidate_review_panel = CandidateReviewPanelWidget()
        self._output_preview_panel = OutputPreviewPanelWidget()
        self._job_run_panel = JobRunPanelWidget()

        self._run_button = QPushButton("変換を実行")
        self._run_button.setDefault(True)
        self._save_job_button = QPushButton("設定を保存…")
        self._load_job_button = QPushButton("設定を読み込み…")

        self._run_button.clicked.connect(self._handle_run_clicked)
        self._save_job_button.clicked.connect(self._handle_save_job_clicked)
        self._load_job_button.clicked.connect(self._handle_load_job_clicked)
        self._job_catalog_panel.job_selected.connect(self._handle_job_selected)
        self._job_form.input_folder_changed.connect(self._browse_input_folder)
        self._job_form.output_folder_changed.connect(self._browse_output_folder)
        self._job_form.form_state_changed.connect(self._refresh_preview_panels)
        self._candidate_review_panel.selection_changed.connect(self._handle_candidate_selection_changed)
        self._job_run_panel.cancel_requested.connect(self._handle_cancel_requested)

        title = QLabel("Kibo Converter")
        title_font = title.font()
        title_font.setPointSize(title_font.pointSize() + 2)
        title_font.setBold(True)
        title.setFont(title_font)
        subtitle = QLabel(
            "左のジョブ一覧から今回やりたい変換を選び、"
            "右側で共通設定・ジョブ固有設定・候補一覧・出力プレビューを確認します。"
        )
        subtitle.setWordWrap(True)
        self._selected_job_summary_label = QLabel()
        self._selected_job_summary_label.setWordWrap(True)
        self._update_selected_job_summary()

        buttons_row = QHBoxLayout()
        buttons_row.addWidget(self._run_button)
        buttons_row.addWidget(self._save_job_button)
        buttons_row.addWidget(self._load_job_button)
        buttons_row.addStretch(1)

        preview_tabs = QTabWidget()
        preview_tabs.addTab(self._candidate_review_panel, "候補一覧")
        preview_tabs.addTab(self._output_preview_panel, "出力プレビュー")
        preview_tabs.addTab(self._job_run_panel, "実行ログ")

        workspace_widget = QWidget()
        workspace_layout = QVBoxLayout()
        workspace_layout.addWidget(title)
        workspace_layout.addWidget(subtitle)
        workspace_layout.addWidget(self._selected_job_summary_label)
        workspace_layout.addWidget(self._job_form)
        workspace_layout.addLayout(buttons_row)
        workspace_layout.addWidget(preview_tabs)
        workspace_widget.setLayout(workspace_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._job_catalog_panel)
        splitter.addWidget(workspace_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout = QHBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)
        self._refresh_preview_panels()

    def current_job_type(self) -> JobType:
        """Expose the selected job type for tests and integrations."""
        return self._job_catalog_panel.current_job_type()

    def job_catalog_titles(self) -> list[str]:
        """Expose visible catalog titles for tests."""
        return self._job_catalog_panel.job_titles()

    def candidate_review_row_count(self) -> int:
        """Expose preview candidate row count for tests."""
        return self._candidate_review_panel.row_count()

    def output_preview_row_count(self) -> int:
        """Expose preview output row count for tests."""
        return self._output_preview_panel.row_count()

    def _browse_input_folder(self) -> None:
        """Open a folder dialog and write the selection into the input field."""
        starting_directory = self._safe_existing_directory_from_path_text(
            self._job_form.browse_input_folder_line_edit().text()
        )
        selected_directory = QFileDialog.getExistingDirectory(self, "入力フォルダを選ぶ", starting_directory)
        if not selected_directory:
            return
        self._job_form.browse_input_folder_line_edit().setText(selected_directory)

    def _browse_output_folder(self) -> None:
        """Open a folder dialog and write the selection into the output field."""
        starting_directory = self._safe_existing_directory_from_path_text(
            self._job_form.browse_output_folder_line_edit().text()
        )
        selected_directory = QFileDialog.getExistingDirectory(self, "出力フォルダを選ぶ", starting_directory)
        if not selected_directory:
            return
        self._job_form.browse_output_folder_line_edit().setText(selected_directory)

    def _safe_existing_directory_from_path_text(self, path_text: str) -> str:
        """Return path_text if it points to an existing directory, else empty string."""
        candidate_path = Path(path_text.strip())
        if candidate_path.is_dir():
            return str(candidate_path)
        return ""

    def _output_folder_has_any_entries(self, output_directory_path: Path) -> bool:
        """Return True when the output folder already contains files or subfolders (best-effort)."""
        try:
            return any(output_directory_path.iterdir())
        except OSError:
            return False

    def _confirm_overwrite_policy_with_nonempty_output_folder(
        self,
        *,
        output_directory_path: Path,
    ) -> bool:
        """
        Guard: warn before overwrite when the output folder is not empty.

        Returns True when the user accepts the risk or when confirmation is unnecessary.
        """
        if not self._output_folder_has_any_entries(output_directory_path):
            return True
        reply = QMessageBox.question(
            self,
            "上書きの確認",
            "出力フォルダに、すでにファイルやフォルダがあります。\n"
            "「同名の出力があるときは上書きする」を選んでいる場合、"
            "同名の出力ファイルが置き換わることがあります。\n\n"
            "このまま続行しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _handle_run_clicked(self) -> None:
        """Validate form state and start a background conversion job."""
        if self._active_thread_controller is not None:
            QMessageBox.information(self, "実行中", "すでに変換が動いています。終わるまでお待ちください。")
            return

        try:
            form_state = self._job_form.read_form_state()
            job_definition = build_job_definition_from_form_state(form_state)
        except ValueError as exc:
            QMessageBox.warning(self, "設定を確認してください", str(exc))
            return

        if self.current_job_type() != JobType.IMAGE_CONVERSION:
            QMessageBox.information(self, "未対応", "現在実行できるのは画像変換ジョブのみです。")
            return

        if job_definition.output_rules.collision_policy == CollisionPolicy.OVERWRITE_EXISTING_OUTPUT:
            if not self._confirm_overwrite_policy_with_nonempty_output_folder(
                output_directory_path=job_definition.output_rules.output_directory_path,
            ):
                return

        log_file_path = self._default_log_file_path(job_definition)
        self._start_job_thread(
            job_definition=job_definition,
            log_file_path=log_file_path,
            source_paths_override=self._selected_source_paths_from_preview(),
            excluded_by_filter_count_override=self._latest_preview_snapshot.excluded_by_filter_count,
        )

    def _default_log_file_path(self, job_definition: JobDefinition) -> Path:
        """Pick a default JSONL log path next to the output folder."""
        return job_definition.output_rules.output_directory_path / "kibo_converter_run.jsonl"

    def _start_job_thread(
        self,
        *,
        job_definition: JobDefinition,
        log_file_path: Path,
        source_paths_override: list[Path] | None,
        excluded_by_filter_count_override: int,
    ) -> None:
        """Wire worker signals and start the background thread."""
        controller = ImageJobThreadController()
        worker = controller.start_job(
            job_definition=job_definition,
            log_file_path=log_file_path,
            source_paths_override=source_paths_override,
            excluded_by_filter_count_override=excluded_by_filter_count_override,
        )

        self._active_thread_controller = controller
        self._active_worker = worker

        self._run_button.setEnabled(False)
        self._save_job_button.setEnabled(False)
        self._load_job_button.setEnabled(False)
        self._job_form.set_interaction_enabled(False)
        self._job_run_panel.set_running_state(is_running=True)
        self._job_run_panel.set_status_text("実行中…")
        self._job_run_panel.set_progress(completed=0, total=0)
        self._job_run_panel.append_log_line(f"ログファイル: {log_file_path}")
        self._job_run_panel.append_log_line("事前チェックと入力フォルダのスキャンを開始します。")

        worker.preflight_failed.connect(self._handle_preflight_failed)
        worker.progress_updated.connect(self._handle_progress_updated)
        worker.file_result_emitted.connect(self._handle_file_result)
        worker.job_finished.connect(self._handle_job_finished)

    def _handle_preflight_failed(self, message: str) -> None:
        """Show a preflight failure and reset UI state."""
        self._job_run_panel.append_log_line(f"開始できませんでした: {message}")
        QMessageBox.critical(
            self,
            "変換を開始できません",
            f"{message}\n\n"
            "入力・出力のパス、フォルダの存在、書き込み権限、HEIC が必要なときは HEIC 対応環境かを確認してください。",
        )
        self._job_run_panel.set_status_text("開始できませんでした（設定か環境を確認）")
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
        self._job_run_panel.append_log_line(format_file_result_line_for_user(record))

    def _handle_job_finished(self, summary: object) -> None:
        """Show final counts and reset UI state."""
        if isinstance(summary, JobRunSummary):
            self._job_run_panel.set_status_text(format_job_summary_text(summary))
            self._job_run_panel.append_log_line("変換ジョブが終了しました。")
        self._reset_ui_after_job_end()

    def _reset_ui_after_job_end(self) -> None:
        """Re-enable controls after the worker thread stops."""
        self._active_thread_controller = None
        self._active_worker = None
        self._run_button.setEnabled(True)
        self._save_job_button.setEnabled(True)
        self._load_job_button.setEnabled(True)
        self._job_form.set_interaction_enabled(True)
        self._job_run_panel.set_running_state(is_running=False)
        self._refresh_preview_panels()

    def _handle_job_selected(self, job_type: object) -> None:
        """Refresh visible descriptions when the selected job changes."""
        if not isinstance(job_type, JobType):
            return
        self._update_selected_job_summary()
        self._refresh_preview_panels()

    def _update_selected_job_summary(self) -> None:
        """Update the sentence describing the selected job and current capability scope."""
        if self.current_job_type() == JobType.IMAGE_CONVERSION:
            self._selected_job_summary_label.setText(
                "選択中のジョブ: 画像変換。入力形式は .heic / .heif / .png / .jpg / .jpeg / .webp、"
                "出力形式は PNG / JPEG / WEBP です。"
            )
            return
        self._selected_job_summary_label.setText("選択中のジョブは近日対応です。")

    def _handle_candidate_selection_changed(self, manually_excluded_source_paths: object) -> None:
        """Refresh only the output preview when the user excludes individual candidates."""
        if not isinstance(manually_excluded_source_paths, frozenset):
            return
        if manually_excluded_source_paths == self._manually_excluded_source_paths:
            return
        self._manually_excluded_source_paths = manually_excluded_source_paths
        self._refresh_preview_panels()

    def _refresh_preview_panels(self) -> None:
        """Rebuild candidate review and output preview from the current form state."""
        try:
            form_state = self._job_form.read_form_state()
            job_definition = build_job_definition_from_form_state(form_state)
        except ValueError:
            self._latest_preview_snapshot = JobPreviewSnapshot(candidate_items=[], output_preview_items=[])
            self._candidate_review_panel.set_candidate_items([])
            self._output_preview_panel.set_output_preview_items([])
            return

        if self.current_job_type() != JobType.IMAGE_CONVERSION:
            self._latest_preview_snapshot = JobPreviewSnapshot(candidate_items=[], output_preview_items=[])
            self._candidate_review_panel.set_candidate_items([])
            self._output_preview_panel.set_output_preview_items([])
            return

        snapshot = build_job_preview_snapshot(
            job_definition,
            manually_excluded_source_paths=self._manually_excluded_source_paths,
        )
        self._latest_preview_snapshot = snapshot
        self._candidate_review_panel.set_candidate_items(snapshot.candidate_items)
        self._output_preview_panel.set_output_preview_items(snapshot.output_preview_items)

    def _selected_source_paths_from_preview(self) -> list[Path]:
        """Return user-selected included source paths for execution."""
        return [
            candidate_item.source_path
            for candidate_item in self._latest_preview_snapshot.candidate_items
            if candidate_item.is_selected
        ]

    def _handle_cancel_requested(self) -> None:
        """Forward cancellation to the active worker."""
        if self._active_worker is None:
            return
        self._job_run_panel.set_status_text("キャンセル処理中…")
        self._active_worker.request_cancel()

    def _handle_save_job_clicked(self) -> None:
        """Save the current form state as a JSON job file."""
        if self._active_thread_controller is not None:
            QMessageBox.information(self, "実行中", "変換中は設定の保存はできません。終わってからお試しください。")
            return

        try:
            form_state = self._job_form.read_form_state()
            job_definition = build_job_definition_from_form_state(form_state)
        except ValueError as exc:
            QMessageBox.warning(self, "設定を確認してください", str(exc))
            return

        default_path = Path.home() / "kibo_job.json"
        selected_filter = "JSON ジョブ (*.json)"
        file_path_text, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "設定を保存",
            str(default_path),
            selected_filter,
        )
        if not file_path_text:
            return

        try:
            save_job_definition_to_json_file(job_definition, Path(file_path_text))
        except OSError as exc:
            QMessageBox.critical(self, "保存に失敗しました", str(exc))
            return

        QMessageBox.information(self, "保存しました", f"次のファイルに保存しました:\n{file_path_text}")

    def _handle_load_job_clicked(self) -> None:
        """Load a JSON job file and apply it to the form fields."""
        if self._active_thread_controller is not None:
            QMessageBox.information(self, "実行中", "変換中は設定の読み込みはできません。終わってからお試しください。")
            return

        default_path = Path.home()
        file_path_text, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "設定を読み込み",
            str(default_path),
            "JSON ジョブ (*.json)",
        )
        if not file_path_text:
            return

        try:
            job_definition = load_job_definition_from_json_file(Path(file_path_text))
        except JobPersistenceError as exc:
            QMessageBox.critical(self, "設定ファイルが読めません", str(exc))
            return

        self._job_form.apply_job_definition(job_definition)
        QMessageBox.information(self, "読み込みました", f"次のファイルから読み込みました:\n{file_path_text}")
