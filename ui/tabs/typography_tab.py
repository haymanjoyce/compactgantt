from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLabel, 
                           QMessageBox, QComboBox, QSpinBox)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict, Any
import logging
from .base_tab import BaseTab

# Logging is configured centrally in utils/logging_config.py

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
        self.task_font_size = QSpinBox()
        self.task_font_size.setMinimum(6)
        self.task_font_size.setMaximum(72)
        self.task_font_size.setValue(10)
        self.task_font_size.setSuffix(" px")
        self.task_font_size.setToolTip("Font size for task labels in pixels")

        # Scale Labels
        scale_font_size_label = QLabel("Scale Labels:")
        scale_font_size_label.setFixedWidth(label_width)
        self.scale_font_size = QSpinBox()
        self.scale_font_size.setMinimum(6)
        self.scale_font_size.setMaximum(72)
        self.scale_font_size.setValue(10)
        self.scale_font_size.setSuffix(" px")
        self.scale_font_size.setToolTip("Font size for scale labels in pixels")

        # Header & Footer
        header_footer_font_size_label = QLabel("Header & Footer:")
        header_footer_font_size_label.setFixedWidth(label_width)
        self.header_footer_font_size = QSpinBox()
        self.header_footer_font_size.setMinimum(6)
        self.header_footer_font_size.setMaximum(72)
        self.header_footer_font_size.setValue(10)
        self.header_footer_font_size.setSuffix(" px")
        self.header_footer_font_size.setToolTip("Font size for header and footer text in pixels")

        # Row Numbers
        row_number_font_size_label = QLabel("Row Numbers:")
        row_number_font_size_label.setFixedWidth(label_width)
        self.row_number_font_size = QSpinBox()
        self.row_number_font_size.setMinimum(6)
        self.row_number_font_size.setMaximum(72)
        self.row_number_font_size.setValue(10)
        self.row_number_font_size.setSuffix(" px")
        self.row_number_font_size.setToolTip("Font size for row numbers in pixels")

        # Notes
        note_font_size_label = QLabel("Notes:")
        note_font_size_label.setFixedWidth(label_width)
        self.note_font_size = QSpinBox()
        self.note_font_size.setMinimum(6)
        self.note_font_size.setMaximum(72)
        self.note_font_size.setValue(10)
        self.note_font_size.setSuffix(" px")
        self.note_font_size.setToolTip("Font size for notes in pixels")

        # Swimlanes
        swimlane_font_size_label = QLabel("Swimlanes:")
        swimlane_font_size_label.setFixedWidth(label_width)
        self.swimlane_font_size = QSpinBox()
        self.swimlane_font_size.setMinimum(6)
        self.swimlane_font_size.setMaximum(72)
        self.swimlane_font_size.setValue(10)
        self.swimlane_font_size.setSuffix(" px")
        self.swimlane_font_size.setToolTip("Font size for swimlane labels in pixels")

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

        # Scale Labels
        scale_alignment_label = QLabel("Scale Labels:")
        scale_alignment_label.setFixedWidth(label_width)
        self.scale_vertical_alignment = QSpinBox()
        self.scale_vertical_alignment.setMinimum(0)
        self.scale_vertical_alignment.setMaximum(100)
        self.scale_vertical_alignment.setValue(70)
        self.scale_vertical_alignment.setSuffix("%")
        self.scale_vertical_alignment.setToolTip("Vertical position for scale labels (0-100%, where 0=top, 50=center, 100=bottom)")

        # Task Labels
        task_alignment_label = QLabel("Task Labels:")
        task_alignment_label.setFixedWidth(label_width)
        self.task_vertical_alignment = QSpinBox()
        self.task_vertical_alignment.setMinimum(0)
        self.task_vertical_alignment.setMaximum(100)
        self.task_vertical_alignment.setValue(70)
        self.task_vertical_alignment.setSuffix("%")
        self.task_vertical_alignment.setToolTip("Vertical position for task labels (0-100%, where 0=top, 50=center, 100=bottom)")

        # Row Numbers
        row_number_alignment_label = QLabel("Row Numbers:")
        row_number_alignment_label.setFixedWidth(label_width)
        self.row_number_vertical_alignment = QSpinBox()
        self.row_number_vertical_alignment.setMinimum(0)
        self.row_number_vertical_alignment.setMaximum(100)
        self.row_number_vertical_alignment.setValue(70)
        self.row_number_vertical_alignment.setSuffix("%")
        self.row_number_vertical_alignment.setToolTip("Vertical position for row numbers (0-100%, where 0=top, 50=center, 100=bottom)")

        # Header & Footer
        header_footer_alignment_label = QLabel("Header & Footer:")
        header_footer_alignment_label.setFixedWidth(label_width)
        self.header_footer_vertical_alignment = QSpinBox()
        self.header_footer_vertical_alignment.setMinimum(0)
        self.header_footer_vertical_alignment.setMaximum(100)
        self.header_footer_vertical_alignment.setValue(70)
        self.header_footer_vertical_alignment.setSuffix("%")
        self.header_footer_vertical_alignment.setToolTip("Vertical position for header and footer text (0-100%, where 0=top, 50=center, 100=bottom)")

        # Swimlanes - Top
        swimlane_top_alignment_label = QLabel("Swimlanes (Top):")
        swimlane_top_alignment_label.setFixedWidth(label_width)
        self.swimlane_top_vertical_alignment = QSpinBox()
        self.swimlane_top_vertical_alignment.setMinimum(0)
        self.swimlane_top_vertical_alignment.setMaximum(100)
        self.swimlane_top_vertical_alignment.setValue(70)
        self.swimlane_top_vertical_alignment.setSuffix("%")
        self.swimlane_top_vertical_alignment.setToolTip("Vertical position for top swimlane labels (0-100%, where 0=top, 50=center, 100=bottom)")

        # Swimlanes - Bottom
        swimlane_bottom_alignment_label = QLabel("Swimlanes (Bottom):")
        swimlane_bottom_alignment_label.setFixedWidth(label_width)
        self.swimlane_bottom_vertical_alignment = QSpinBox()
        self.swimlane_bottom_vertical_alignment.setMinimum(0)
        self.swimlane_bottom_vertical_alignment.setMaximum(100)
        self.swimlane_bottom_vertical_alignment.setValue(70)
        self.swimlane_bottom_vertical_alignment.setSuffix("%")
        self.swimlane_bottom_vertical_alignment.setToolTip("Vertical position for bottom swimlane labels (0-100%, where 0=top, 50=center, 100=bottom)")

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
        self.task_font_size.valueChanged.connect(self._sync_data_if_not_initializing)
        self.scale_font_size.valueChanged.connect(self._sync_data_if_not_initializing)
        self.header_footer_font_size.valueChanged.connect(self._sync_data_if_not_initializing)
        self.row_number_font_size.valueChanged.connect(self._sync_data_if_not_initializing)
        self.note_font_size.valueChanged.connect(self._sync_data_if_not_initializing)
        self.swimlane_font_size.valueChanged.connect(self._sync_data_if_not_initializing)
        
        # Vertical Adjustment
        self.scale_vertical_alignment.valueChanged.connect(self._sync_data_if_not_initializing)
        self.task_vertical_alignment.valueChanged.connect(self._sync_data_if_not_initializing)
        self.row_number_vertical_alignment.valueChanged.connect(self._sync_data_if_not_initializing)
        self.header_footer_vertical_alignment.valueChanged.connect(self._sync_data_if_not_initializing)
        self.swimlane_top_vertical_alignment.valueChanged.connect(self._sync_data_if_not_initializing)
        self.swimlane_bottom_vertical_alignment.valueChanged.connect(self._sync_data_if_not_initializing)

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
        self.task_font_size.setValue(chart_config.task_font_size)
        self.scale_font_size.setValue(chart_config.scale_font_size)
        self.header_footer_font_size.setValue(chart_config.header_footer_font_size)
        self.row_number_font_size.setValue(chart_config.row_number_font_size)
        self.note_font_size.setValue(chart_config.note_font_size)
        self.swimlane_font_size.setValue(chart_config.swimlane_font_size)

        # Load Vertical Adjustment (convert from decimal 0.0-1.0 to percent 0-100)
        self.scale_vertical_alignment.setValue(int(chart_config.scale_vertical_alignment_factor * 100))
        self.task_vertical_alignment.setValue(int(chart_config.task_vertical_alignment_factor * 100))
        self.row_number_vertical_alignment.setValue(int(chart_config.row_number_vertical_alignment_factor * 100))
        self.header_footer_vertical_alignment.setValue(int(chart_config.header_footer_vertical_alignment_factor * 100))
        self.swimlane_top_vertical_alignment.setValue(int(chart_config.swimlane_top_vertical_alignment_factor * 100))
        self.swimlane_bottom_vertical_alignment.setValue(int(chart_config.swimlane_bottom_vertical_alignment_factor * 100))

    def _sync_data_impl(self):
        chart_config = self.app_config.general.chart

        # Note: QSpinBox handles validation automatically for font sizes (6-72 range) and vertical adjustment (0-100 range), so no need for manual validation

        # Update chart config
        chart_config.font_family = self.font_family.currentText()
        
        # Font sizes from QSpinBox (no need to check for empty since spinbox always has a value)
        chart_config.task_font_size = self.task_font_size.value()
        chart_config.scale_font_size = self.scale_font_size.value()
        chart_config.header_footer_font_size = self.header_footer_font_size.value()
        chart_config.row_number_font_size = self.row_number_font_size.value()
        chart_config.note_font_size = self.note_font_size.value()
        chart_config.swimlane_font_size = self.swimlane_font_size.value()

        # Convert percent (0-100) from QSpinBox to decimal (0.0-1.0) for internal storage
        chart_config.scale_vertical_alignment_factor = self.scale_vertical_alignment.value() / 100.0
        chart_config.task_vertical_alignment_factor = self.task_vertical_alignment.value() / 100.0
        chart_config.row_number_vertical_alignment_factor = self.row_number_vertical_alignment.value() / 100.0
        chart_config.header_footer_vertical_alignment_factor = self.header_footer_vertical_alignment.value() / 100.0
        chart_config.swimlane_top_vertical_alignment_factor = self.swimlane_top_vertical_alignment.value() / 100.0
        chart_config.swimlane_bottom_vertical_alignment_factor = self.swimlane_bottom_vertical_alignment.value() / 100.0

