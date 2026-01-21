from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLineEdit, 
                           QLabel, QMessageBox, QComboBox, QSpinBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIntValidator
from typing import Dict, Any, Tuple
import logging
from .base_tab import BaseTab
from validators.validators import DataValidator

# Logging is configured centrally in utils/logging_config.py

class LayoutTab(BaseTab):
    def setup_ui(self):
        layout = QVBoxLayout()
        LABEL_WIDTH = 120  # Consistent label width

        # Dimensions Group
        dim_group = self._create_dimensions_group(LABEL_WIDTH)
        layout.addWidget(dim_group)

        # Margins Group
        margins_group = self._create_margins_group(LABEL_WIDTH)
        layout.addWidget(margins_group)

        # Rows Group
        rows_group = self._create_rows_group(LABEL_WIDTH)
        layout.addWidget(rows_group)

        # Add stretch at the end to push all groups to the top
        layout.addStretch(1)

        self.setLayout(layout)

    def _create_dimensions_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Dimensions")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Width
        width_label = QLabel("Outer Width:")
        width_label.setFixedWidth(label_width)
        self.outer_width = QLineEdit(str(self.app_config.general.outer_width))
        self.outer_width.setToolTip("Total width of the chart in pixels")
        # Add validator to only allow non-negative integers
        validator = QIntValidator(0, 999999, self)
        self.outer_width.setValidator(validator)

        # Height
        height_label = QLabel("Outer Height:")
        height_label.setFixedWidth(label_width)
        self.outer_height = QLineEdit(str(self.app_config.general.outer_height))
        self.outer_height.setToolTip("Total height of the chart in pixels")
        # Add validator to only allow non-negative integers
        validator = QIntValidator(0, 999999, self)
        self.outer_height.setValidator(validator)

        layout.addWidget(width_label, 0, 0)
        layout.addWidget(self.outer_width, 0, 1)
        layout.addWidget(height_label, 1, 0)
        layout.addWidget(self.outer_height, 1, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_rows_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Rows")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Number of Rows
        rows_label = QLabel("Number of Rows:")
        rows_label.setFixedWidth(label_width)
        self.num_rows = QSpinBox()
        self.num_rows.setMinimum(0)
        self.num_rows.setMaximum(200)
        self.num_rows.setValue(self.app_config.general.tasks_rows)
        self.num_rows.setToolTip("Number of rows in the chart")

        # Show Row Numbers (using combobox instead of checkbox)
        row_numbers_label = QLabel("Row Numbers:")
        row_numbers_label.setFixedWidth(label_width)
        self.show_row_numbers = QComboBox()
        self.show_row_numbers.addItems(["No", "Yes"])
        self.show_row_numbers.setToolTip("Display row numbers on the left side of each row")

        # Row Dividers (using combobox instead of checkbox)
        row_gridlines_label = QLabel("Row Dividers:")
        row_gridlines_label.setFixedWidth(label_width)
        self.show_row_gridlines = QComboBox()
        self.show_row_gridlines.addItems(["No", "Yes"])
        self.show_row_gridlines.setToolTip("Show horizontal lines dividing rows")

        layout.addWidget(rows_label, 0, 0)
        layout.addWidget(self.num_rows, 0, 1)
        layout.addWidget(row_numbers_label, 1, 0)
        layout.addWidget(self.show_row_numbers, 1, 1)
        layout.addWidget(row_gridlines_label, 2, 0)
        layout.addWidget(self.show_row_gridlines, 2, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_margins_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Margins")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Create margin inputs
        margin_labels = ["Top:", "Bottom:", "Left:", "Right:"]
        self.margin_inputs = []
        for i, label_text in enumerate(margin_labels):
            label = QLabel(label_text)
            label.setFixedWidth(label_width)
            input_field = QSpinBox()
            input_field.setMinimum(0)
            input_field.setMaximum(300)
            input_field.setValue(10)
            input_field.setSuffix(" px")
            input_field.setToolTip(f"{label_text.strip(':')} margin in pixels")
            layout.addWidget(label, i, 0)
            layout.addWidget(input_field, i, 1)
            self.margin_inputs.append(input_field)

        self.margin_top, self.margin_bottom, self.margin_left, self.margin_right = self.margin_inputs
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _connect_signals(self):
        self.outer_width.textChanged.connect(self._sync_data_if_not_initializing)
        self.outer_height.textChanged.connect(self._sync_data_if_not_initializing)
        self.num_rows.valueChanged.connect(self._sync_data_if_not_initializing)
        self.show_row_numbers.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.show_row_gridlines.currentTextChanged.connect(self._sync_data_if_not_initializing)
        for margin in self.margin_inputs:
            margin.valueChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data_impl(self):
        frame_config = self.project_data.frame_config

        # Load Dimensions
        self.outer_width.setText(str(frame_config.outer_width))
        self.outer_height.setText(str(frame_config.outer_height))
        self.num_rows.setValue(frame_config.num_rows)
        show_row_numbers = getattr(frame_config, 'show_row_numbers', False)
        self.show_row_numbers.setCurrentText("Yes" if show_row_numbers else "No")
        self.show_row_gridlines.setCurrentText("Yes" if frame_config.horizontal_gridlines else "No")

        # Load Margins
        margins = frame_config.margins
        self.margin_top.setValue(margins[0])
        self.margin_bottom.setValue(margins[1])
        self.margin_left.setValue(margins[2])
        self.margin_right.setValue(margins[3])

    def _sync_data_impl(self):
        # Validate numeric inputs - skip validation if field is empty (intermediate editing state)
        # Note: QSpinBox handles validation automatically for margins (0-300 range) and num_rows (0-200 range), so no need for manual validation
        numeric_fields = {
            "outer_width": self.outer_width.text(),
            "outer_height": self.outer_height.text()
        }

        for field_name, value in numeric_fields.items():
            # Skip validation for empty strings (intermediate editing state)
            if not value.strip():
                continue
            display_name = field_name.replace('_', ' ').title()
            errors = DataValidator.validate_non_negative_integer_string(value, display_name)
            if errors:
                raise ValueError(errors[0])  # Raise first error

        # Update frame config - use current values from frame_config as defaults for empty fields
        frame_config = self.project_data.frame_config
        self.project_data.frame_config.outer_width = int(self.outer_width.text()) if self.outer_width.text().strip() else frame_config.outer_width
        self.project_data.frame_config.outer_height = int(self.outer_height.text()) if self.outer_height.text().strip() else frame_config.outer_height
        # Margins from QSpinBox (no need to check for empty since spinbox always has a value)
        self.project_data.frame_config.margins = (
            self.margin_top.value(),
            self.margin_bottom.value(),
            self.margin_left.value(),
            self.margin_right.value()
        )
        # Number of rows from QSpinBox (no need to check for empty since spinbox always has a value)
        self.project_data.frame_config.num_rows = self.num_rows.value()
        self.project_data.frame_config.show_row_numbers = self.show_row_numbers.currentText() == "Yes"
        self.project_data.frame_config.horizontal_gridlines = self.show_row_gridlines.currentText() == "Yes"