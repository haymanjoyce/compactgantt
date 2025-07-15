# File: ui/tabs/time_frames_tab.py
from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                           QGridLayout, QMessageBox, QHeaderView, QTableWidgetItem, QLabel, QDateEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QBrush, QIntValidator
from datetime import datetime
import logging
from ..table_utils import add_row, remove_row, CheckBoxWidget, highlight_table_errors, extract_table_data
from typing import List, Set, Tuple
from .base_tab import BaseTab
from utils.conversion import internal_to_display_date, display_to_internal_date

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TimeFramesTab(BaseTab):
    def __init__(self, project_data, app_config):
        self.table_config = app_config.get_table_config("time_frames")
        super().__init__(project_data, app_config)

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # --- Add Chart Start Date field above the table ---
        chart_start_layout = QGridLayout()
        chart_start_label = QLabel("Chart Start Date:")
        self.chart_start_date = QDateEdit()
        self.chart_start_date.setCalendarPopup(True)
        self.chart_start_date.setDate(QDate.currentDate())
        chart_start_layout.addWidget(chart_start_label, 0, 0)
        chart_start_layout.addWidget(self.chart_start_date, 0, 1)
        layout.addLayout(chart_start_layout)

        # Create table
        self.time_frames_table = QTableWidget(0, len(self.table_config.columns))
        headers = [col.name for col in self.table_config.columns]
        self.time_frames_table.setHorizontalHeaderLabels(headers)
        self.time_frames_table.setSortingEnabled(True)
        self.time_frames_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.time_frames_table)

        # Create buttons
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Time Frame")
        remove_btn = QPushButton("Remove Time Frame")
        add_btn.clicked.connect(lambda: add_row(self.time_frames_table, "time_frames", self.app_config.tables, self, "Time Frame ID"))
        remove_btn.clicked.connect(lambda: remove_row(self.time_frames_table, "time_frames", 
                                                    self.app_config.tables, self))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _connect_signals(self):
        self.time_frames_table.itemChanged.connect(self._sync_data_if_not_initializing)
        self.chart_start_date.dateChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data_impl(self):
        logging.debug("Starting _load_initial_data")
        try:
            # --- Load Chart Start Date ---
            frame_config = self.project_data.frame_config
            start_date = frame_config.chart_start_date
            try:
                date = datetime.strptime(start_date, "%Y-%m-%d")
                self.chart_start_date.setDate(QDate(date.year, date.month, date.day))
            except Exception:
                self.chart_start_date.setDate(QDate.currentDate())

            table_data = self.project_data.project_service.get_table_data(self.project_data, "time_frames")
            print("DEBUG: table_data =", table_data)
            self._initializing = True
            self.time_frames_table.clearContents()
            was_sorting = self.time_frames_table.isSortingEnabled()
            self.time_frames_table.setSortingEnabled(False)
            row_count = max(len(table_data), self.table_config.min_rows)
            self.time_frames_table.setRowCount(row_count)

            # Find the index of the Width (%) column (skip checkbox column)
            width_col_index = None
            for idx, col in enumerate(self.table_config.columns):
                if col.name == "Width (%)":
                    width_col_index = idx
                    break

            for row_idx in range(row_count):
                # Add checkbox first
                checkbox_widget = CheckBoxWidget()
                self.time_frames_table.setCellWidget(row_idx, 0, checkbox_widget)

                if row_idx < len(table_data):
                    row_data = table_data[row_idx]
                    # Start from column 1 since column 0 is checkbox
                    for col_idx, value in enumerate(row_data, start=1):
                        # Only convert to int for the Width (%) column
                        if width_col_index is not None and col_idx == width_col_index:
                            item = QTableWidgetItem(str(int(float(value))) if value else "0")
                        else:
                            item = QTableWidgetItem(str(value))
                        if col_idx == 1:  # Time Frame ID is read-only
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        self.time_frames_table.setItem(row_idx, col_idx, item)
                else:
                    context = {"max_time_frame_id": len(table_data) + row_idx}
                    defaults = self.table_config.default_generator(row_idx, context)
                    # Skip the first default (checkbox state) and start from index 1
                    for col_idx, default in enumerate(defaults[1:], start=1):
                        # Only convert to int for the Width (%) column
                        if width_col_index is not None and col_idx == width_col_index:
                            item = QTableWidgetItem(str(int(float(default))) if default else "0")
                        else:
                            item = QTableWidgetItem(str(default))
                        if col_idx == 1:  # Time Frame ID is read-only
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        self.time_frames_table.setItem(row_idx, col_idx, item)

            self.time_frames_table.setSortingEnabled(was_sorting)
            self._initializing = False
            self._sync_data()
        except Exception as e:
            logging.error(f"Error in _load_initial_data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load initial data: {e}")

    def _sync_data_impl(self):
        # --- Save Chart Start Date ---
        self.project_data.frame_config.chart_start_date = self.chart_start_date.date().toString("yyyy-MM-dd")

        time_frames_data = self._extract_table_data()
        # --- Simple validation for total width ---
        total_width = 0.0
        width_col_index = None
        for idx, col in enumerate(self.table_config.columns):
            if col.name == "Width (%)":
                width_col_index = idx - 1  # Subtract 1 because _extract_table_data skips the checkbox column
                break
        if width_col_index is not None:
            for row in time_frames_data:
                try:
                    width_val = float(row[width_col_index])
                    total_width += width_val
                except (ValueError, IndexError):
                    continue
            if total_width > 100.0:
                QMessageBox.warning(self, "Invalid Time Frames", f"Total width of all time frames exceeds 100% ({total_width:.2f}%). Please adjust the values.")
                return  # Prevent further processing

        errors = self.project_data.project_service.update_from_table(self.project_data, "time_frames", time_frames_data)
        
        # Use common error highlighting function
        highlight_table_errors(self.time_frames_table, errors)

    def _extract_table_data(self) -> List[List[str]]:
        """Extract data from table, skipping the checkbox column."""
        return extract_table_data(self.time_frames_table, include_widgets=False)