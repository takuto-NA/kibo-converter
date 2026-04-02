"""Responsibility: Compose shared job settings and image-specific settings for the current job."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from kibo_converter.domain.job_definition import JobDefinition
from kibo_converter.domain.job_types import JobType
from kibo_converter.domain.job_ui_models import SharedJobSettings
from kibo_converter.domain.output_rules import CollisionPolicy
from kibo_converter.domain.processing_steps import ImageOutputFormat
from kibo_converter.ui.view_models import JobFormState


class JobFormWidget(QWidget):
    """Collect user inputs required to build a JobDefinition."""

    input_folder_changed = pyqtSignal()
    output_folder_changed = pyqtSignal()
    form_state_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._guidance_label = QLabel(
            "現在のジョブは画像変換です。"
            "（1）共通設定で入力元と出力先を選ぶ →"
            "（2）画像変換設定で拡張子や出力形式を決める。"
        )
        self._guidance_label.setWordWrap(True)

        self._input_folder_line_edit = QLineEdit()
        self._input_folder_line_edit.setPlaceholderText("今回の入力ファイルが入っているフォルダを選びます")
        self._input_folder_browse_button = QPushButton("参照…")
        self._output_folder_line_edit = QLineEdit()
        self._output_folder_line_edit.setPlaceholderText("変換後のファイルを保存するフォルダを選びます")
        self._output_folder_browse_button = QPushButton("参照…")

        self._extensions_line_edit = QLineEdit(".heic,.heif,.png,.jpg,.jpeg,.webp")
        self._extensions_line_edit.setPlaceholderText("例: .heic,.png,.jpg")
        self._extensions_hint_label = QLabel(
            "通常はこのままで問題ありません。対象にしたい拡張子だけが変換されます。"
        )
        self._extensions_hint_label.setWordWrap(True)
        self._include_subfolders_checkbox = QCheckBox("下のフォルダもまとめて対象にする")
        self._include_subfolders_checkbox.setChecked(True)

        self._output_format_combo = QComboBox()
        for output_format in ImageOutputFormat:
            self._output_format_combo.addItem(output_format.value.upper(), userData=output_format)

        self._resize_enabled_checkbox = QCheckBox("長い辺を指定して縮小する")
        self._resize_enabled_checkbox.setChecked(False)
        self._max_edge_spin = QSpinBox()
        self._max_edge_spin.setRange(1, 20000)
        self._max_edge_spin.setValue(2048)
        self._max_edge_spin.setSuffix(" px")
        self._max_edge_spin.setEnabled(False)

        self._collision_policy_combo = QComboBox()
        self._collision_policy_combo.addItem(
            "同名の出力があるときは上書きする",
            userData=CollisionPolicy.OVERWRITE_EXISTING_OUTPUT,
        )
        self._collision_policy_combo.addItem(
            "同名の出力があるときは別名で保存する",
            userData=CollisionPolicy.KEEP_BOTH_OUTPUTS,
        )

        self._input_folder_browse_button.clicked.connect(self._emit_input_folder_signal)
        self._output_folder_browse_button.clicked.connect(self._emit_output_folder_signal)
        self._resize_enabled_checkbox.toggled.connect(self._max_edge_spin.setEnabled)
        self._wire_form_state_changed_signal()

        input_row = QHBoxLayout()
        input_row.addWidget(self._input_folder_line_edit)
        input_row.addWidget(self._input_folder_browse_button)

        output_row = QHBoxLayout()
        output_row.addWidget(self._output_folder_line_edit)
        output_row.addWidget(self._output_folder_browse_button)

        resize_row = QHBoxLayout()
        resize_row.addWidget(self._resize_enabled_checkbox)
        resize_row.addWidget(self._max_edge_spin)

        layout = QVBoxLayout()
        layout.addWidget(self._guidance_label)

        self._shared_settings_group = QGroupBox("共通設定")
        shared_settings_form_layout = QFormLayout()
        shared_settings_form_layout.addRow(QLabel("入力元フォルダ"), input_row)
        shared_settings_form_layout.addRow(QLabel("出力先フォルダ"), output_row)
        shared_settings_form_layout.addRow(
            QLabel("同じ名前の出力ファイルがあるとき"),
            self._collision_policy_combo,
        )
        self._shared_settings_group.setLayout(shared_settings_form_layout)

        self._image_job_settings_group = QGroupBox("画像変換設定")
        image_job_settings_form_layout = QFormLayout()
        image_job_settings_form_layout.addRow(QLabel("対象にする拡張子"), self._extensions_line_edit)
        image_job_settings_form_layout.addRow("", self._extensions_hint_label)
        image_job_settings_form_layout.addRow(self._include_subfolders_checkbox)
        image_job_settings_form_layout.addRow(QLabel("出力形式"), self._output_format_combo)
        image_job_settings_form_layout.addRow(QLabel("リサイズ"), resize_row)
        self._image_job_settings_group.setLayout(image_job_settings_form_layout)

        layout.addWidget(self._shared_settings_group)
        layout.addWidget(self._image_job_settings_group)
        self.setLayout(layout)

    def set_interaction_enabled(self, enabled: bool) -> None:
        """Enable or disable editing while a job runs or when the UI should be read-only."""
        self._guidance_label.setEnabled(enabled)
        self._input_folder_line_edit.setEnabled(enabled)
        self._input_folder_browse_button.setEnabled(enabled)
        self._output_folder_line_edit.setEnabled(enabled)
        self._output_folder_browse_button.setEnabled(enabled)
        self._extensions_line_edit.setEnabled(enabled)
        self._extensions_hint_label.setEnabled(enabled)
        self._include_subfolders_checkbox.setEnabled(enabled)
        self._output_format_combo.setEnabled(enabled)
        self._resize_enabled_checkbox.setEnabled(enabled)
        self._max_edge_spin.setEnabled(enabled and self._resize_enabled_checkbox.isChecked())
        self._collision_policy_combo.setEnabled(enabled)

    def form_guidance_text(self) -> str:
        """Return the short explanatory text shown above the form."""
        return self._guidance_label.text()

    def current_job_type(self) -> JobType:
        """Return the job type currently configured by this form."""
        return JobType.IMAGE_CONVERSION

    def _wire_form_state_changed_signal(self) -> None:
        """Emit a single signal whenever any visible form control changes."""
        self._input_folder_line_edit.textChanged.connect(self.form_state_changed.emit)
        self._output_folder_line_edit.textChanged.connect(self.form_state_changed.emit)
        self._extensions_line_edit.textChanged.connect(self.form_state_changed.emit)
        self._include_subfolders_checkbox.toggled.connect(self.form_state_changed.emit)
        self._output_format_combo.currentIndexChanged.connect(self.form_state_changed.emit)
        self._resize_enabled_checkbox.toggled.connect(self.form_state_changed.emit)
        self._max_edge_spin.valueChanged.connect(self.form_state_changed.emit)
        self._collision_policy_combo.currentIndexChanged.connect(self.form_state_changed.emit)

    def _emit_input_folder_signal(self) -> None:
        self.input_folder_changed.emit()

    def _emit_output_folder_signal(self) -> None:
        self.output_folder_changed.emit()

    def browse_input_folder_line_edit(self) -> QLineEdit:
        """Expose input path editor for folder dialogs."""
        return self._input_folder_line_edit

    def browse_output_folder_line_edit(self) -> QLineEdit:
        """Expose output path editor for folder dialogs."""
        return self._output_folder_line_edit

    def resize_checkbox(self) -> QCheckBox:
        """Expose resize toggle for UI tests and wiring."""
        return self._resize_enabled_checkbox

    def resize_spin_box(self) -> QSpinBox:
        """Expose resize value editor for UI tests."""
        return self._max_edge_spin

    def read_shared_settings(self) -> SharedJobSettings:
        """Return grouped shared settings for shell UI coordination."""
        collision_policy = self._collision_policy_combo.currentData()
        if not isinstance(collision_policy, CollisionPolicy):
            raise ValueError("内部エラー: 重複時の扱いの選択が不正です。")
        input_directory_path_text = self._input_folder_line_edit.text().strip()
        output_directory_path_text = self._output_folder_line_edit.text().strip()
        return SharedJobSettings(
            input_directory_path=Path(input_directory_path_text),
            output_directory_path=Path(output_directory_path_text),
            collision_policy=collision_policy,
        )

    def read_form_state(self) -> JobFormState:
        """Return a snapshot of current form values."""
        output_format = self._output_format_combo.currentData()
        collision_policy = self._collision_policy_combo.currentData()
        if not isinstance(output_format, ImageOutputFormat):
            raise ValueError("内部エラー: 出力形式の選択が不正です。")
        if not isinstance(collision_policy, CollisionPolicy):
            raise ValueError("内部エラー: 重複時の扱いの選択が不正です。")

        return JobFormState(
            input_directory_path_text=self._input_folder_line_edit.text().strip(),
            output_directory_path_text=self._output_folder_line_edit.text().strip(),
            included_extensions_text=self._extensions_line_edit.text().strip(),
            include_subfolders=self._include_subfolders_checkbox.isChecked(),
            output_format=output_format,
            max_edge_pixels_enabled=self._resize_enabled_checkbox.isChecked(),
            max_edge_pixels=int(self._max_edge_spin.value()),
            collision_policy=collision_policy,
        )

    def apply_job_definition(self, job_definition: JobDefinition) -> None:
        """Populate the form from a loaded JobDefinition."""
        selection_rules = job_definition.selection_rules
        self._input_folder_line_edit.setText(str(selection_rules.input_directory_path))
        self._output_folder_line_edit.setText(str(job_definition.output_rules.output_directory_path))

        extensions_sorted = sorted(selection_rules.included_file_extensions_lower_case)
        self._extensions_line_edit.setText(",".join(extensions_sorted))
        self._include_subfolders_checkbox.setChecked(selection_rules.include_subdirectories_recursively)

        output_format = job_definition.output_format
        for index in range(self._output_format_combo.count()):
            if self._output_format_combo.itemData(index) == output_format:
                self._output_format_combo.setCurrentIndex(index)
                break

        max_edge_pixels = job_definition.resize_options.max_edge_pixels
        if max_edge_pixels is None:
            self._resize_enabled_checkbox.setChecked(False)
        else:
            self._resize_enabled_checkbox.setChecked(True)
            self._max_edge_spin.setValue(int(max_edge_pixels))

        collision_policy = job_definition.output_rules.collision_policy
        for index in range(self._collision_policy_combo.count()):
            if self._collision_policy_combo.itemData(index) == collision_policy:
                self._collision_policy_combo.setCurrentIndex(index)
                break
