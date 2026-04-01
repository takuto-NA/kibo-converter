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
            "Choose the source folder that contains HEIC or other images, decide where converted files "
            "should go, then pick how duplicates should be handled."
        )
        self._guidance_label.setWordWrap(True)

        self._input_folder_line_edit = QLineEdit()
        self._input_folder_line_edit.setPlaceholderText("Select the folder that contains HEIC or other image files")
        self._input_folder_browse_button = QPushButton("Browse…")
        self._output_folder_line_edit = QLineEdit()
        self._output_folder_line_edit.setPlaceholderText("Select the folder where converted images will be saved")
        self._output_folder_browse_button = QPushButton("Browse…")

        self._extensions_line_edit = QLineEdit(".heic,.heif,.png,.jpg,.jpeg,.webp")
        self._extensions_line_edit.setPlaceholderText("Example: .heic,.png,.jpg")
        self._include_subfolders_checkbox = QCheckBox("Include subfolders")
        self._include_subfolders_checkbox.setChecked(True)

        self._output_format_combo = QComboBox()
        for output_format in ImageOutputFormat:
            self._output_format_combo.addItem(output_format.value.upper(), userData=output_format)

        self._resize_enabled_checkbox = QCheckBox("Resize (max edge)")
        self._resize_enabled_checkbox.setChecked(False)
        self._max_edge_spin = QSpinBox()
        self._max_edge_spin.setRange(1, 20000)
        self._max_edge_spin.setValue(2048)
        self._max_edge_spin.setSuffix(" px")
        self._max_edge_spin.setEnabled(False)

        self._collision_policy_combo = QComboBox()
        self._collision_policy_combo.addItem(
            "Replace the existing converted file",
            userData=CollisionPolicy.OVERWRITE_EXISTING_OUTPUT,
        )
        self._collision_policy_combo.addItem(
            "Keep both and create a unique name when needed",
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

        layout = QVBoxLayout()
        group = QGroupBox("Job settings")
        form = QFormLayout()
        layout.addWidget(self._guidance_label)
        form.addRow(QLabel("Input folder"), input_row)
        form.addRow(QLabel("Output folder"), output_row)
        form.addRow(QLabel("Extensions"), self._extensions_line_edit)
        form.addRow(self._include_subfolders_checkbox)
        form.addRow(QLabel("Output format"), self._output_format_combo)

        resize_row = QHBoxLayout()
        resize_row.addWidget(self._resize_enabled_checkbox)
        resize_row.addWidget(self._max_edge_spin)
        form.addRow(QLabel("Resize"), resize_row)

        form.addRow(QLabel("Collision policy"), self._collision_policy_combo)
        group.setLayout(form)
        layout.addWidget(group)
        self.setLayout(layout)

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
            raise ValueError("Internal error: output format combo returned invalid data.")
        if not isinstance(collision_policy, CollisionPolicy):
            raise ValueError("Internal error: collision policy combo returned invalid data.")

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
