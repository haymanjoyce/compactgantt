from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLineEdit, 
                           QLabel, QMessageBox, QDateEdit, QCheckBox, QComboBox)
from PyQt5.QtCore import pyqtSignal, Qt, QDate
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta
import logging
from .base_tab import BaseTab
from utils.conversion import internal_to_display_date, display_to_internal_date

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

        # Timeframe Group
        timeframe_group = self._create_timeframe_group(LABEL_WIDTH)
        layout.addWidget(timeframe_group)

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

        # Height
        height_label = QLabel("Outer Height:")
        height_label.setFixedWidth(label_width)
        self.outer_height = QLineEdit(str(self.app_config.general.outer_height))
        self.outer_height.setToolTip("Total height of the chart in pixels")

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
        self.num_rows = QLineEdit(str(self.app_config.general.tasks_rows))
        self.num_rows.setToolTip("Number of rows in the chart")

        # Show Row Numbers (using combobox instead of checkbox)
        row_numbers_label = QLabel("Row Numbers:")
        row_numbers_label.setFixedWidth(label_width)
        self.show_row_numbers = QComboBox()
        self.show_row_numbers.addItems(["No", "Yes"])
        self.show_row_numbers.setToolTip("Display row numbers on the left side of each row")

        # Show Row Gridlines (using combobox instead of checkbox)
        row_gridlines_label = QLabel("Show Row Gridlines:")
        row_gridlines_label.setFixedWidth(label_width)
        self.show_row_gridlines = QComboBox()
        self.show_row_gridlines.addItems(["No", "Yes"])
        self.show_row_gridlines.setToolTip("Display horizontal gridlines at row boundaries")

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
            input_field = QLineEdit("10")
            input_field.setToolTip(f"{label_text.strip(':')} margin in pixels")
            layout.addWidget(label, i, 0)
            layout.addWidget(input_field, i, 1)
            self.margin_inputs.append(input_field)

        self.margin_top, self.margin_bottom, self.margin_left, self.margin_right = self.margin_inputs
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_timeframe_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Timeframe")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Start Date
        start_label = QLabel("Start Date:")
        start_label.setFixedWidth(label_width)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM/yyyy")
        self.start_date.setToolTip("Start date of the chart timeline (dd/mm/yyyy)")

        # Finish Date
        finish_label = QLabel("Finish Date:")
        finish_label.setFixedWidth(label_width)
        self.finish_date = QDateEdit()
        self.finish_date.setCalendarPopup(True)
        self.finish_date.setDisplayFormat("dd/MM/yyyy")
        self.finish_date.setToolTip("Finish date of the chart timeline (dd/mm/yyyy)")

        layout.addWidget(start_label, 0, 0)
        layout.addWidget(self.start_date, 0, 1)
        layout.addWidget(finish_label, 1, 0)
        layout.addWidget(self.finish_date, 1, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _connect_signals(self):
        self.outer_width.textChanged.connect(self._sync_data_if_not_initializing)
        self.outer_height.textChanged.connect(self._sync_data_if_not_initializing)
        self.num_rows.textChanged.connect(self._sync_data_if_not_initializing)
        self.show_row_numbers.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.show_row_gridlines.currentTextChanged.connect(self._sync_data_if_not_initializing)
        for margin in self.margin_inputs:
            margin.textChanged.connect(self._sync_data_if_not_initializing)
        self.start_date.dateChanged.connect(self._sync_data_if_not_initializing)
        self.finish_date.dateChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data_impl(self):
        frame_config = self.project_data.frame_config

        # Load Dimensions
        self.outer_width.setText(str(frame_config.outer_width))
        self.outer_height.setText(str(frame_config.outer_height))
        self.num_rows.setText(str(frame_config.num_rows))
        show_row_numbers = getattr(frame_config, 'show_row_numbers', False)
        self.show_row_numbers.setCurrentText("Yes" if show_row_numbers else "No")
        self.show_row_gridlines.setCurrentText("Yes" if frame_config.horizontal_gridlines else "No")

        # Load Margins
        margins = frame_config.margins
        self.margin_top.setText(str(margins[0]))
        self.margin_bottom.setText(str(margins[1]))
        self.margin_left.setText(str(margins[2]))
        self.margin_right.setText(str(margins[3]))

        # Load Timeframe dates
        start_date_str = getattr(frame_config, 'chart_start_date', '2024-12-30')
        finish_date_str = getattr(frame_config, 'chart_end_date', None)
        
        # If finish_date doesn't exist, calculate default (30 days after start)
        if not finish_date_str:
            try:
                start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
                finish_dt = start_dt + timedelta(days=30)
                finish_date_str = finish_dt.strftime("%Y-%m-%d")
            except ValueError:
                finish_date_str = "2025-01-29"
        
        # Convert internal format (yyyy-mm-dd) to QDate
        try:
            start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
            finish_dt = datetime.strptime(finish_date_str, "%Y-%m-%d")
            self.start_date.setDate(QDate(start_dt.year, start_dt.month, start_dt.day))
            self.finish_date.setDate(QDate(finish_dt.year, finish_dt.month, finish_dt.day))
        except ValueError:
            # Fallback to defaults if parsing fails
            default_start = QDate(2024, 12, 30)
            default_finish = QDate(2025, 1, 29)
            self.start_date.setDate(default_start)
            self.finish_date.setDate(default_finish)

    def _sync_data_impl(self):
        # Validate numeric inputs
        numeric_fields = {
            "outer_width": self.outer_width.text(),
            "outer_height": self.outer_height.text(),
            "num_rows": self.num_rows.text(),
            "margin_top": self.margin_top.text(),
            "margin_bottom": self.margin_bottom.text(),
            "margin_left": self.margin_left.text(),
            "margin_right": self.margin_right.text()
        }

        for field_name, value in numeric_fields.items():
            try:
                # Check for empty string first
                if not value.strip():
                    raise ValueError(f"{field_name.replace('_', ' ').title()} must be a non-negative number")
                # Then try to convert and validate
                num_value = int(value)
                if num_value < 0:
                    raise ValueError(f"{field_name.replace('_', ' ').title()} must be a non-negative number")
            except ValueError as e:
                if "must be a" not in str(e):
                    raise ValueError(f"{field_name.replace('_', ' ').title()} must be a valid number")
                raise

        # Validate date range
        start_qdate = self.start_date.date()
        finish_qdate = self.finish_date.date()
        if finish_qdate <= start_qdate:
            raise ValueError("Finish date must be after start date")

        # Update frame config
        self.project_data.frame_config.outer_width = int(self.outer_width.text())
        self.project_data.frame_config.outer_height = int(self.outer_height.text())
        self.project_data.frame_config.margins = (
            int(self.margin_top.text()),
            int(self.margin_bottom.text()),
            int(self.margin_left.text()),
            int(self.margin_right.text())
        )
        self.project_data.frame_config.num_rows = int(self.num_rows.text())
        self.project_data.frame_config.show_row_numbers = self.show_row_numbers.currentText() == "Yes"
        self.project_data.frame_config.horizontal_gridlines = self.show_row_gridlines.currentText() == "Yes"
        
        # Update timeframe dates (convert QDate to internal format yyyy-mm-dd)
        start_date_str = start_qdate.toString("yyyy-MM-dd")
        finish_date_str = finish_qdate.toString("yyyy-MM-dd")
        self.project_data.frame_config.chart_start_date = start_date_str
        self.project_data.frame_config.chart_end_date = finish_date_str