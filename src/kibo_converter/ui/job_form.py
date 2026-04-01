# Responsibility: Widgets for editing job parameters before execution.

from __future__ import annotations

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
from kibo_converter.domain.output_rules import CollisionPolicy
from kibo_converter.domain.processing_steps import ImageOutputFormat
from kibo_converter.ui.view_models import JobFormState


class JobFormWidget(QWidget):
    """Collect user inputs required to build a JobDefinition."""

    input_folder_changed = pyqtSignal()
    output_folder_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._guidance_label = QLabel(
            "次の順で選んでください（HEIC などの画像を想定）。"
            "（1）変換元のフォルダと対象の拡張子 →（2）保存先 →（3）形式やリサイズ →"
            "（4）同じ名前のファイルが既にあるときの扱い。"
        )
        self._guidance_label.setWordWrap(True)

        self._input_folder_line_edit = QLineEdit()
        self._input_folder_line_edit.setPlaceholderText("HEIC などの画像が入っているフォルダを選びます")
        self._input_folder_browse_button = QPushButton("参照…")
        self._output_folder_line_edit = QLineEdit()
        self._output_folder_line_edit.setPlaceholderText("変換後の画像を保存するフォルダを選びます")
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
        group = QGroupBox("変換設定")
        form = QFormLayout()
        layout.addWidget(self._guidance_label)
        form.addRow(QLabel("1. 入力元フォルダ"), input_row)
        form.addRow(QLabel("対象にする拡張子"), self._extensions_line_edit)
        form.addRow("", self._extensions_hint_label)
        form.addRow(self._include_subfolders_checkbox)
        form.addRow(QLabel("2. 出力先フォルダ"), output_row)
        form.addRow(QLabel("3. 出力形式"), self._output_format_combo)
        form.addRow(QLabel("リサイズ"), resize_row)
        form.addRow(QLabel("4. 同じ名前の出力ファイルがあるとき"), self._collision_policy_combo)
        group.setLayout(form)
        layout.addWidget(group)
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
