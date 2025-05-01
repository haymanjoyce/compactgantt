# File: ui/tabs/time_frames_tab.py
from PyQt5.QtWidgets import QWidget, QTableWidget, QVBoxLayout, QPushButton, QGridLayout, QMessageBox, QHeaderView, QTableWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QBrush
from datetime import datetime, timedelta
import logging
from ..table_utils import add_row, remove_row, show_context_menu, _extract_table_data, CheckBoxWidget

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
        logging.debug("Setting up TimeFramesTab UI")
        layout = QVBoxLayout()
        self.time_frames_table = QTableWidget(self.table_config.min_rows, len(self.table_config.columns))
        self.time_frames_table.setHorizontalHeaderLabels([col.name for col in self.table_config.columns])
        self.time_frames_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.time_frames_table.customContextMenuRequested.connect(
            lambda pos: show_context_menu(pos, self.time_frames_table, "time_frames", self, self.app_config.tables))
        self.time_frames_table.setSortingEnabled(True)
        self.time_frames_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.time_frames_table.setColumnWidth(0, 80)  # Time Frame ID
        self.time_frames_table.resizeColumnsToContents()
        layout.addWidget(self.time_frames_table)

        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Time Frame")
        remove_btn = QPushButton("Remove Time Frame")
        add_btn.clicked.connect(lambda: add_row(self.time_frames_table, "time_frames", self.app_config.tables, self))
        remove_btn.clicked.connect(lambda: remove_row(self.time_frames_table, "time_frames", self.app_config.tables, self))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        logging.debug("TimeFramesTab UI setup complete")

    def _load_initial_data(self):
        logging.debug("Starting _load_initial_data")
        try:
            table_data = self.project_data.get_table_data("time_frames")
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
            logging.debug("_load_initial_data completed")
        except Exception as e:
            logging.error(f"Error in _load_initial_data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load initial data: {e}")

    def _sync_data(self):
        time_frames_data = self._extract_table_data()
        invalid_cells = set()
        
        # Create a mapping of column names to indices
        header_to_index = {self.time_frames_table.horizontalHeaderItem(i).text(): i 
                          for i in range(self.time_frames_table.columnCount())}
        
        # Create a mapping of column names to validators
        validators = {col.name: col.validator for col in self.table_config.columns if col.validator}
        
        for row_idx, row in enumerate(time_frames_data):
            for col_name, validator in validators.items():
                if col_name not in header_to_index:
                    continue
                    
                col_idx = header_to_index[col_name]
                value = row[col_idx - 1]  # Adjust index because _extract_table_data skips checkbox column
                
                try:
                    if not validator(value):
                        invalid_cells.add((row_idx, col_idx))
                        if col_name == "Time Frame ID":
                            logging.warning(f"Invalid Time Frame ID in row {row_idx}: {value}")
                        elif col_name == "Finish Date":
                            logging.warning(f"Invalid Finish Date in row {row_idx}: {value}")
                        elif col_name == "Width (%)":
                            logging.warning(f"Invalid Width in row {row_idx}: {value}")
                except (ValueError, TypeError) as e:
                    invalid_cells.add((row_idx, col_idx))
                    logging.warning(f"Validation error in {col_name} at row {row_idx}: {e}")

        # Highlight invalid cells
        self.time_frames_table.blockSignals(True)
        for row in range(self.time_frames_table.rowCount()):
            for col in range(self.time_frames_table.columnCount()):
                item = self.time_frames_table.item(row, col)
                if item:
                    if (row, col) in invalid_cells:
                        item.setBackground(QBrush(Qt.yellow))
                        col_name = self.time_frames_table.horizontalHeaderItem(col).text()
                        if col_name == "Time Frame ID":
                            item.setToolTip("Time Frame ID must be a positive number")
                        elif col_name == "Finish Date":
                            item.setToolTip("Date must be in YYYY-MM-DD format")
                        elif col_name == "Width (%)":
                            item.setToolTip("Width must be a positive number")
                    else:
                        item.setBackground(QBrush())
                        item.setToolTip("")
        self.time_frames_table.blockSignals(False)

        if invalid_cells:
            QMessageBox.critical(self, "Error", "Please fix highlighted cells")
            return

        self.project_data.update_from_table("time_frames", time_frames_data)
        self.data_updated.emit(self.project_data.to_json())

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            logging.debug("Calling _sync_data from itemChanged")
            self._sync_data()

    def _extract_table_data(self):
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