from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLineEdit, 
                           QLabel, QMessageBox, QComboBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from typing import Dict, Any
import logging
from .base_tab import BaseTab
from validators.validators import DataValidator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TypographyTab(BaseTab):
    def setup_ui(self):
        layout = QVBoxLayout()
        LABEL_WIDTH = 120  # Consistent label width

        # Font Family Group
        font_family_group = self._create_font_family_group(LABEL_WIDTH)
        layout.addWidget(font_family_group)

        # Font Sizes Group
        font_sizes_group = self._create_font_sizes_group(LABEL_WIDTH)
        layout.addWidget(font_sizes_group)

        # Vertical Alignment Group
        vertical_alignment_group = self._create_vertical_alignment_group(LABEL_WIDTH)
        layout.addWidget(vertical_alignment_group)

        # Add stretch at the end to push all groups to the top
        layout.addStretch(1)

        self.setLayout(layout)

    def _create_font_family_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Font Family")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Font Family
        font_family_label = QLabel("Font Family:")
        font_family_label.setFixedWidth(label_width)
        self.font_family = QComboBox()
        self.font_family.addItems(["Arial", "Helvetica", "Times New Roman", "Courier New", "Verdana", "Georgia", "Palatino"])
        self.font_family.setToolTip("Font family for all text elements")

        layout.addWidget(font_family_label, 0, 0)
        layout.addWidget(self.font_family, 0, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_font_sizes_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Font Sizes")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Task Labels
        task_font_size_label = QLabel("Task Labels:")
        task_font_size_label.setFixedWidth(label_width)
        self.task_font_size = QLineEdit("10")
        self.task_font_size.setToolTip("Font size for task labels in pixels")
        validator = QIntValidator(6, 72, self)
        self.task_font_size.setValidator(validator)

        # Scale Labels
        scale_font_size_label = QLabel("Scale Labels:")
        scale_font_size_label.setFixedWidth(label_width)
        self.scale_font_size = QLineEdit("10")
        self.scale_font_size.setToolTip("Font size for scale labels in pixels")
        self.scale_font_size.setValidator(validator)

        # Header & Footer
        header_footer_font_size_label = QLabel("Header & Footer:")
        header_footer_font_size_label.setFixedWidth(label_width)
        self.header_footer_font_size = QLineEdit("10")
        self.header_footer_font_size.setToolTip("Font size for header and footer text in pixels")
        self.header_footer_font_size.setValidator(validator)

        # Row Numbers
        row_number_font_size_label = QLabel("Row Numbers:")
        row_number_font_size_label.setFixedWidth(label_width)
        self.row_number_font_size = QLineEdit("10")
        self.row_number_font_size.setToolTip("Font size for row numbers in pixels")
        self.row_number_font_size.setValidator(validator)

        # Notes
        note_font_size_label = QLabel("Notes:")
        note_font_size_label.setFixedWidth(label_width)
        self.note_font_size = QLineEdit("10")
        self.note_font_size.setToolTip("Font size for notes in pixels")
        self.note_font_size.setValidator(validator)

        # Swimlanes
        swimlane_font_size_label = QLabel("Swimlanes:")
        swimlane_font_size_label.setFixedWidth(label_width)
        self.swimlane_font_size = QLineEdit("10")
        self.swimlane_font_size.setToolTip("Font size for swimlane labels in pixels")
        self.swimlane_font_size.setValidator(validator)

        layout.addWidget(task_font_size_label, 0, 0)
        layout.addWidget(self.task_font_size, 0, 1)
        layout.addWidget(scale_font_size_label, 1, 0)
        layout.addWidget(self.scale_font_size, 1, 1)
        layout.addWidget(header_footer_font_size_label, 2, 0)
        layout.addWidget(self.header_footer_font_size, 2, 1)
        layout.addWidget(row_number_font_size_label, 3, 0)
        layout.addWidget(self.row_number_font_size, 3, 1)
        layout.addWidget(note_font_size_label, 4, 0)
        layout.addWidget(self.note_font_size, 4, 1)
        layout.addWidget(swimlane_font_size_label, 5, 0)
        layout.addWidget(self.swimlane_font_size, 5, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_vertical_alignment_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Vertical Adjustment")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        double_validator = QDoubleValidator(0.0, 1.0, 2, self)
        double_validator.setNotation(QDoubleValidator.StandardNotation)

        # Scale Labels
        scale_alignment_label = QLabel("Scale Labels:")
        scale_alignment_label.setFixedWidth(label_width)
        self.scale_vertical_alignment = QLineEdit("0.7")
        self.scale_vertical_alignment.setToolTip("Vertical position for scale labels (0.0=top, 0.5=center, 1.0=bottom)")
        self.scale_vertical_alignment.setValidator(double_validator)

        # Task Labels
        task_alignment_label = QLabel("Task Labels:")
        task_alignment_label.setFixedWidth(label_width)
        self.task_vertical_alignment = QLineEdit("0.7")
        self.task_vertical_alignment.setToolTip("Vertical position for task labels (0.0=top, 0.5=center, 1.0=bottom)")
        self.task_vertical_alignment.setValidator(double_validator)

        # Row Numbers
        row_number_alignment_label = QLabel("Row Numbers:")
        row_number_alignment_label.setFixedWidth(label_width)
        self.row_number_vertical_alignment = QLineEdit("0.7")
        self.row_number_vertical_alignment.setToolTip("Vertical position for row numbers (0.0=top, 0.5=center, 1.0=bottom)")
        self.row_number_vertical_alignment.setValidator(double_validator)

        # Header & Footer
        header_footer_alignment_label = QLabel("Header & Footer:")
        header_footer_alignment_label.setFixedWidth(label_width)
        self.header_footer_vertical_alignment = QLineEdit("0.7")
        self.header_footer_vertical_alignment.setToolTip("Vertical position for header and footer text (0.0=top, 0.5=center, 1.0=bottom)")
        self.header_footer_vertical_alignment.setValidator(double_validator)

        # Swimlanes - Top
        swimlane_top_alignment_label = QLabel("Swimlanes (Top):")
        swimlane_top_alignment_label.setFixedWidth(label_width)
        self.swimlane_top_vertical_alignment = QLineEdit("0.7")
        self.swimlane_top_vertical_alignment.setToolTip("Vertical position for top swimlane labels (0.0=top, 0.5=center, 1.0=bottom)")
        self.swimlane_top_vertical_alignment.setValidator(double_validator)

        # Swimlanes - Bottom
        swimlane_bottom_alignment_label = QLabel("Swimlanes (Bottom):")
        swimlane_bottom_alignment_label.setFixedWidth(label_width)
        self.swimlane_bottom_vertical_alignment = QLineEdit("0.7")
        self.swimlane_bottom_vertical_alignment.setToolTip("Vertical position for bottom swimlane labels (0.0=top, 0.5=center, 1.0=bottom)")
        self.swimlane_bottom_vertical_alignment.setValidator(double_validator)

        layout.addWidget(scale_alignment_label, 0, 0)
        layout.addWidget(self.scale_vertical_alignment, 0, 1)
        layout.addWidget(task_alignment_label, 1, 0)
        layout.addWidget(self.task_vertical_alignment, 1, 1)
        layout.addWidget(row_number_alignment_label, 2, 0)
        layout.addWidget(self.row_number_vertical_alignment, 2, 1)
        layout.addWidget(header_footer_alignment_label, 3, 0)
        layout.addWidget(self.header_footer_vertical_alignment, 3, 1)
        layout.addWidget(swimlane_top_alignment_label, 4, 0)
        layout.addWidget(self.swimlane_top_vertical_alignment, 4, 1)
        layout.addWidget(swimlane_bottom_alignment_label, 5, 0)
        layout.addWidget(self.swimlane_bottom_vertical_alignment, 5, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _connect_signals(self):
        # Font Family
        self.font_family.currentTextChanged.connect(self._sync_data_if_not_initializing)
        
        # Font Sizes
        self.task_font_size.textChanged.connect(self._sync_data_if_not_initializing)
        self.scale_font_size.textChanged.connect(self._sync_data_if_not_initializing)
        self.header_footer_font_size.textChanged.connect(self._sync_data_if_not_initializing)
        self.row_number_font_size.textChanged.connect(self._sync_data_if_not_initializing)
        self.note_font_size.textChanged.connect(self._sync_data_if_not_initializing)
        self.swimlane_font_size.textChanged.connect(self._sync_data_if_not_initializing)
        
        # Vertical Adjustment
        self.scale_vertical_alignment.textChanged.connect(self._sync_data_if_not_initializing)
        self.task_vertical_alignment.textChanged.connect(self._sync_data_if_not_initializing)
        self.row_number_vertical_alignment.textChanged.connect(self._sync_data_if_not_initializing)
        self.header_footer_vertical_alignment.textChanged.connect(self._sync_data_if_not_initializing)
        self.swimlane_top_vertical_alignment.textChanged.connect(self._sync_data_if_not_initializing)
        self.swimlane_bottom_vertical_alignment.textChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data_impl(self):
        chart_config = self.app_config.general.chart

        # Load Font Family
        font_family = chart_config.font_family
        index = self.font_family.findText(font_family)
        if index >= 0:
            self.font_family.setCurrentIndex(index)
        else:
            self.font_family.setCurrentText("Arial")

        # Load Font Sizes
        self.task_font_size.setText(str(chart_config.task_font_size))
        self.scale_font_size.setText(str(chart_config.scale_font_size))
        self.header_footer_font_size.setText(str(chart_config.header_footer_font_size))
        self.row_number_font_size.setText(str(chart_config.row_number_font_size))
        self.note_font_size.setText(str(chart_config.note_font_size))
        self.swimlane_font_size.setText(str(chart_config.swimlane_font_size))

        # Load Vertical Adjustment
        self.scale_vertical_alignment.setText(str(chart_config.scale_vertical_alignment_factor))
        self.task_vertical_alignment.setText(str(chart_config.task_vertical_alignment_factor))
        self.row_number_vertical_alignment.setText(str(chart_config.row_number_vertical_alignment_factor))
        self.header_footer_vertical_alignment.setText(str(chart_config.header_footer_vertical_alignment_factor))
        self.swimlane_top_vertical_alignment.setText(str(chart_config.swimlane_top_vertical_alignment_factor))
        self.swimlane_bottom_vertical_alignment.setText(str(chart_config.swimlane_bottom_vertical_alignment_factor))

    def _sync_data_impl(self):
        chart_config = self.app_config.general.chart

        # Validate numeric inputs - skip validation if field is empty (intermediate editing state)
        numeric_fields = {
            "task_font_size": self.task_font_size.text(),
            "scale_font_size": self.scale_font_size.text(),
            "header_footer_font_size": self.header_footer_font_size.text(),
            "row_number_font_size": self.row_number_font_size.text(),
            "note_font_size": self.note_font_size.text(),
            "swimlane_font_size": self.swimlane_font_size.text(),
        }

        for field_name, value in numeric_fields.items():
            # Skip validation for empty strings (intermediate editing state)
            if not value.strip():
                continue
            display_name = field_name.replace('_', ' ').title()
            errors = DataValidator.validate_non_negative_integer_string(value, display_name)
            if errors:
                raise ValueError(errors[0])  # Raise first error

        # Validate vertical adjustment factors
        alignment_fields = {
            "scale_vertical_alignment": self.scale_vertical_alignment.text(),
            "task_vertical_alignment": self.task_vertical_alignment.text(),
            "row_number_vertical_alignment": self.row_number_vertical_alignment.text(),
            "header_footer_vertical_alignment": self.header_footer_vertical_alignment.text(),
            "swimlane_top_vertical_alignment": self.swimlane_top_vertical_alignment.text(),
            "swimlane_bottom_vertical_alignment": self.swimlane_bottom_vertical_alignment.text(),
        }

        for field_name, value in alignment_fields.items():
            # Skip validation for empty strings (intermediate editing state)
            if not value.strip():
                continue
            try:
                float_value = float(value)
                if float_value < 0.0 or float_value > 1.0:
                    display_name = field_name.replace('_', ' ').title()
                    raise ValueError(f"{display_name} must be between 0.0 and 1.0")
            except ValueError as e:
                if "must be between" in str(e):
                    raise
                display_name = field_name.replace('_', ' ').title()
                raise ValueError(f"{display_name} must be a valid number between 0.0 and 1.0")

        # Update chart config - use current values as defaults for empty fields
        chart_config.font_family = self.font_family.currentText()
        
        chart_config.task_font_size = int(self.task_font_size.text()) if self.task_font_size.text().strip() else chart_config.task_font_size
        chart_config.scale_font_size = int(self.scale_font_size.text()) if self.scale_font_size.text().strip() else chart_config.scale_font_size
        chart_config.header_footer_font_size = int(self.header_footer_font_size.text()) if self.header_footer_font_size.text().strip() else chart_config.header_footer_font_size
        chart_config.row_number_font_size = int(self.row_number_font_size.text()) if self.row_number_font_size.text().strip() else chart_config.row_number_font_size
        chart_config.note_font_size = int(self.note_font_size.text()) if self.note_font_size.text().strip() else chart_config.note_font_size
        chart_config.swimlane_font_size = int(self.swimlane_font_size.text()) if self.swimlane_font_size.text().strip() else chart_config.swimlane_font_size

        chart_config.scale_vertical_alignment_factor = float(self.scale_vertical_alignment.text()) if self.scale_vertical_alignment.text().strip() else chart_config.scale_vertical_alignment_factor
        chart_config.task_vertical_alignment_factor = float(self.task_vertical_alignment.text()) if self.task_vertical_alignment.text().strip() else chart_config.task_vertical_alignment_factor
        chart_config.row_number_vertical_alignment_factor = float(self.row_number_vertical_alignment.text()) if self.row_number_vertical_alignment.text().strip() else chart_config.row_number_vertical_alignment_factor
        chart_config.header_footer_vertical_alignment_factor = float(self.header_footer_vertical_alignment.text()) if self.header_footer_vertical_alignment.text().strip() else chart_config.header_footer_vertical_alignment_factor
        chart_config.swimlane_top_vertical_alignment_factor = float(self.swimlane_top_vertical_alignment.text()) if self.swimlane_top_vertical_alignment.text().strip() else chart_config.swimlane_top_vertical_alignment_factor
        chart_config.swimlane_bottom_vertical_alignment_factor = float(self.swimlane_bottom_vertical_alignment.text()) if self.swimlane_bottom_vertical_alignment.text().strip() else chart_config.swimlane_bottom_vertical_alignment_factor

