from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLineEdit, 
                           QCheckBox, QDateEdit, QLabel, QMessageBox)
from PyQt5.QtCore import pyqtSignal, QDate, Qt
from datetime import datetime
from typing import Dict, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LayoutTab(QWidget):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        super().__init__()
        self.project_data = project_data
        self.app_config = app_config
        self._initializing = True
        self.setup_ui()
        self._load_initial_data()
        self._connect_signals()
        self._initializing = False

    def setup_ui(self):
        layout = QVBoxLayout()
        LABEL_WIDTH = 120  # Consistent label width

        # Chart Settings Group
        chart_group = self._create_chart_settings_group(LABEL_WIDTH)
        layout.addWidget(chart_group)

        # Dimensions Group
        dim_group = self._create_dimensions_group(LABEL_WIDTH)
        layout.addWidget(dim_group)

        # Margins Group
        margins_group = self._create_margins_group(LABEL_WIDTH)
        layout.addWidget(margins_group)

        # Header/Footer Group
        header_footer_group = self._create_header_footer_group(LABEL_WIDTH)
        layout.addWidget(header_footer_group)

        # Grid Settings Group
        grid_group = self._create_grid_settings_group()
        layout.addWidget(grid_group)

        self.setLayout(layout)

    def _create_chart_settings_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Chart Settings")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        chart_label = QLabel("Chart Start Date:")
        chart_label.setFixedWidth(label_width)
        self.chart_start_date = QDateEdit()
        self.chart_start_date.setCalendarPopup(True)
        self.chart_start_date.setDate(QDate.currentDate())

        layout.addWidget(chart_label, 0, 0)
        layout.addWidget(self.chart_start_date, 0, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

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

        # Number of Rows
        rows_label = QLabel("Number of Rows:")
        rows_label.setFixedWidth(label_width)
        self.num_rows = QLineEdit(str(self.app_config.general.tasks_rows))
        self.num_rows.setToolTip("Number of rows in the chart")

        layout.addWidget(width_label, 0, 0)
        layout.addWidget(self.outer_width, 0, 1)
        layout.addWidget(height_label, 1, 0)
        layout.addWidget(self.outer_height, 1, 1)
        layout.addWidget(rows_label, 2, 0)
        layout.addWidget(self.num_rows, 2, 1)
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

    def _create_header_footer_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Header/Footer")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Header settings
        header_height_label = QLabel("Header Height:")
        header_height_label.setFixedWidth(label_width)
        self.header_height = QLineEdit("50")
        self.header_height.setToolTip("Height of the header section in pixels")

        header_text_label = QLabel("Header Text:")
        header_text_label.setFixedWidth(label_width)
        self.header_text = QLineEdit()
        self.header_text.setToolTip("Text to display in the header")

        # Footer settings
        footer_height_label = QLabel("Footer Height:")
        footer_height_label.setFixedWidth(label_width)
        self.footer_height = QLineEdit("50")
        self.footer_height.setToolTip("Height of the footer section in pixels")

        footer_text_label = QLabel("Footer Text:")
        footer_text_label.setFixedWidth(label_width)
        self.footer_text = QLineEdit()
        self.footer_text.setToolTip("Text to display in the footer")

        layout.addWidget(header_height_label, 0, 0)
        layout.addWidget(self.header_height, 0, 1)
        layout.addWidget(header_text_label, 1, 0)
        layout.addWidget(self.header_text, 1, 1)
        layout.addWidget(footer_height_label, 2, 0)
        layout.addWidget(self.footer_height, 2, 1)
        layout.addWidget(footer_text_label, 3, 0)
        layout.addWidget(self.footer_text, 3, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_grid_settings_group(self) -> QGroupBox:
        group = QGroupBox("Grid Settings")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        self.horizontal_gridlines = QCheckBox("Show Horizontal Gridlines")
        self.vertical_gridlines = QCheckBox("Show Vertical Gridlines")
        self.horizontal_gridlines.setToolTip("Display horizontal gridlines in the chart")
        self.vertical_gridlines.setToolTip("Display vertical gridlines in the chart")

        layout.addWidget(self.horizontal_gridlines, 0, 0)
        layout.addWidget(self.vertical_gridlines, 1, 0)
        group.setLayout(layout)
        return group

    def _connect_signals(self):
        # Connect all input widgets to _sync_data
        self.chart_start_date.dateChanged.connect(self._sync_data_if_not_initializing)
        self.outer_width.textChanged.connect(self._sync_data_if_not_initializing)
        self.outer_height.textChanged.connect(self._sync_data_if_not_initializing)
        self.num_rows.textChanged.connect(self._sync_data_if_not_initializing)
        for margin in self.margin_inputs:
            margin.textChanged.connect(self._sync_data_if_not_initializing)
        self.header_height.textChanged.connect(self._sync_data_if_not_initializing)
        self.footer_height.textChanged.connect(self._sync_data_if_not_initializing)
        self.header_text.textChanged.connect(self._sync_data_if_not_initializing)
        self.footer_text.textChanged.connect(self._sync_data_if_not_initializing)
        self.horizontal_gridlines.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridlines.stateChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data(self):
        try:
            frame_config = self.project_data.frame_config

            # Load Chart Start Date
            start_date = frame_config.chart_start_date
            try:
                date = datetime.strptime(start_date, "%Y-%m-%d")
                self.chart_start_date.setDate(QDate(date.year, date.month, date.day))
            except ValueError:
                self.chart_start_date.setDate(QDate.currentDate())

            # Load Dimensions
            self.outer_width.setText(str(frame_config.outer_width))
            self.outer_height.setText(str(frame_config.outer_height))
            self.num_rows.setText(str(frame_config.num_rows))

            # Load Margins
            margins = frame_config.margins
            self.margin_top.setText(str(margins[0]))
            self.margin_bottom.setText(str(margins[1]))
            self.margin_left.setText(str(margins[2]))
            self.margin_right.setText(str(margins[3]))

            # Load Header and Footer
            self.header_height.setText(str(frame_config.header_height))
            self.footer_height.setText(str(frame_config.footer_height))
            self.header_text.setText(frame_config.header_text)
            self.footer_text.setText(frame_config.footer_text)

            # Load Gridlines
            self.horizontal_gridlines.setChecked(frame_config.horizontal_gridlines)
            self.vertical_gridlines.setChecked(frame_config.vertical_gridlines)

        except Exception as e:
            logging.error(f"Error in _load_initial_data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load initial data: {e}")

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            self._sync_data()

    def _sync_data(self):
        try:
            # Validate numeric inputs
            numeric_fields = {
                "outer_width": self.outer_width.text(),
                "outer_height": self.outer_height.text(),
                "header_height": self.header_height.text(),
                "footer_height": self.footer_height.text(),
                "num_rows": self.num_rows.text(),
                "margin_top": self.margin_top.text(),
                "margin_bottom": self.margin_bottom.text(),
                "margin_left": self.margin_left.text(),
                "margin_right": self.margin_right.text()
            }

            for field_name, value in numeric_fields.items():
                try:
                    if not value.strip() or int(value) <= 0:
                        raise ValueError(f"{field_name.replace('_', ' ').title()} must be a positive number")
                except ValueError as e:
                    if "must be a positive number" not in str(e):
                        raise ValueError(f"{field_name.replace('_', ' ').title()} must be a valid number")
                    raise

            # Update frame config
            self.project_data.frame_config.chart_start_date = self.chart_start_date.date().toString("yyyy-MM-dd")
            self.project_data.frame_config.outer_width = int(self.outer_width.text())
            self.project_data.frame_config.outer_height = int(self.outer_height.text())
            self.project_data.frame_config.margins = (
                int(self.margin_top.text()),
                int(self.margin_bottom.text()),
                int(self.margin_left.text()),
                int(self.margin_right.text())
            )
            self.project_data.frame_config.header_height = int(self.header_height.text())
            self.project_data.frame_config.footer_height = int(self.footer_height.text())
            self.project_data.frame_config.header_text = self.header_text.text()
            self.project_data.frame_config.footer_text = self.footer_text.text()
            self.project_data.frame_config.num_rows = int(self.num_rows.text())
            self.project_data.frame_config.horizontal_gridlines = self.horizontal_gridlines.isChecked()
            self.project_data.frame_config.vertical_gridlines = self.vertical_gridlines.isChecked()

        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))