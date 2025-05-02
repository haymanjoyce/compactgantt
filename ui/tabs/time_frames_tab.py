# File: ui/tabs/time_frames_tab.py
from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                           QGridLayout, QMessageBox, QHeaderView, QTableWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QBrush
from datetime import datetime
import logging
from ..table_utils import add_row, remove_row, CheckBoxWidget
from typing import List, Set, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TimeFramesTab(QWidget):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        super().__init__()
        self.project_data = project_data
        self.app_config = app_config
        self.table_config = app_config.get_table_config("time_frames")
        self.setup_ui()
        self._load_initial_data()
        self.time_frames_table.itemChanged.connect(self._sync_data_if_not_initializing)
        self._initializing = False
        logging.debug("TimeFramesTab initialized")

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Create table
        self.time_frames_table = QTableWidget(0, len(self.table_config.columns))  # Remove +1 since checkbox column is already in config
        headers = [col.name for col in self.table_config.columns]  # Use column names directly from config
        self.time_frames_table.setHorizontalHeaderLabels(headers)
        self.time_frames_table.setSortingEnabled(True)
        self.time_frames_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.time_frames_table)

        # Create buttons
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Time Frame")
        remove_btn = QPushButton("Remove Time Frame")
        add_btn.clicked.connect(lambda: add_row(self.time_frames_table, "time_frames", 
                                              self.app_config.tables, self))
        remove_btn.clicked.connect(lambda: remove_row(self.time_frames_table, "time_frames", 
                                                    self.app_config.tables, self))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _load_initial_data(self):
        logging.debug("Starting _load_initial_data")
        try:
            table_data = self.project_data.project_service.get_table_data(self.project_data, "time_frames")
            self._initializing = True
            self.time_frames_table.clearContents()
            was_sorting = self.time_frames_table.isSortingEnabled()
            self.time_frames_table.setSortingEnabled(False)
            row_count = max(len(table_data), self.table_config.min_rows)
            self.time_frames_table.setRowCount(row_count)

            for row_idx in range(row_count):
                # Add checkbox first
                checkbox_widget = CheckBoxWidget()
                self.time_frames_table.setCellWidget(row_idx, 0, checkbox_widget)

                if row_idx < len(table_data):
                    row_data = table_data[row_idx]
                    # Start from column 1 since column 0 is checkbox
                    for col_idx, value in enumerate(row_data, start=1):
                        item = QTableWidgetItem(str(value))
                        if col_idx == 1:  # Time Frame ID is read-only
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        self.time_frames_table.setItem(row_idx, col_idx, item)
                else:
                    context = {"max_time_frame_id": len(table_data) + row_idx}
                    defaults = self.table_config.default_generator(row_idx, context)
                    # Skip the first default (checkbox state) and start from index 1
                    for col_idx, default in enumerate(defaults[1:], start=1):
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

    def _sync_data(self):
        time_frames_data = self._extract_table_data()
        errors = self.project_data.project_service.update_from_table(self.project_data, "time_frames", time_frames_data)
        
        # Clear all highlights first
        self.time_frames_table.blockSignals(True)
        for row in range(self.time_frames_table.rowCount()):
            for col in range(1, self.time_frames_table.columnCount()):  # Skip checkbox column
                item = self.time_frames_table.item(row, col)
                if item:
                    item.setBackground(QBrush())
                    item.setToolTip("")
        
        # Highlight cells with errors
        if errors:
            for error in errors:
                if error.startswith("Row"):
                    try:
                        row_str = error.split(":")[0].replace("Row ", "")
                        row_idx = int(row_str) - 1
                        # Highlight the entire row
                        for col in range(1, self.time_frames_table.columnCount()):
                            item = self.time_frames_table.item(row_idx, col)
                            if item:
                                item.setBackground(QBrush(Qt.yellow))
                                item.setToolTip(error.split(":", 1)[1].strip())
                    except (ValueError, IndexError):
                        logging.error(f"Failed to parse error message: {error}")
                        continue
            
            QMessageBox.critical(self, "Error", "\n".join(errors))
        
        self.time_frames_table.blockSignals(False)

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            logging.debug("Calling _sync_data from itemChanged")
            self._sync_data()

    def _extract_table_data(self) -> List[List[str]]:
        """Extract data from table, skipping the checkbox column."""
        data = []
        for row in range(self.time_frames_table.rowCount()):
            row_data = []
            # Start from column 1 to skip checkbox column
            for col in range(1, self.time_frames_table.columnCount()):
                item = self.time_frames_table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data