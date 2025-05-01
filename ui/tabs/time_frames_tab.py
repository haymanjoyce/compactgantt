# File: ui/tabs/time_frames_tab.py
from PyQt5.QtWidgets import QWidget, QTableWidget, QVBoxLayout, QPushButton, QGridLayout, QMessageBox, QHeaderView, QTableWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QBrush
from datetime import datetime, timedelta
import logging
from ..table_utils import add_row, remove_row, show_context_menu, insert_row_with_id

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
                if row_idx < len(table_data):
                    row_data = table_data[row_idx]
                else:
                    context = {"max_time_frame_id": len(table_data) + row_idx}
                    row_data = self.table_config.default_generator(row_idx, context)
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    if col_idx == 0:  # Time Frame ID is read-only
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
        logging.debug("Starting _sync_data")
        try:
            tf_data = self._extract_table_data()
            if not tf_data:
                raise ValueError("At least one time frame is required")
            invalid_cells = set()
            time_frame_ids = set()

            for row_idx, row in enumerate(tf_data):
                time_frame_id = row[0] or ""
                end = row[1] or ""
                width = row[2] or ""

                logging.debug(f"Validating row {row_idx}: {row}")
                # Validate Time Frame ID
                try:
                    tf_id = int(time_frame_id)
                    if tf_id <= 0:
                        invalid_cells.add((row_idx, 0, "non-positive"))
                    elif tf_id in time_frame_ids:
                        invalid_cells.add((row_idx, 0, "duplicate"))
                    time_frame_ids.add(tf_id)
                except (ValueError, TypeError):
                    invalid_cells.add((row_idx, 0, "invalid"))
                    logging.warning(f"Invalid time_frame_id in row {row_idx}: {time_frame_id}")

                # Validate Finish Date
                try:
                    if end:
                        datetime.strptime(end, "%Y-%m-%d")
                    else:
                        invalid_cells.add((row_idx, 1, "empty"))
                        continue
                except ValueError:
                    invalid_cells.add((row_idx, 1, "invalid format"))
                    logging.warning(f"Invalid finish_date in row {row_idx}: {end}")
                    continue

                # Validate Width
                try:
                    width_val = float(width) / 100
                    if width_val <= 0:
                        invalid_cells.add((row_idx, 2, "non-positive"))
                except (ValueError, TypeError):
                    invalid_cells.add((row_idx, 2, "invalid"))
                    logging.warning(f"Invalid width in row {row_idx}: {width}")
                    continue

                # Removed Date Order Validation: No longer checking if end_dt < prev_end

            logging.debug(f"Invalid cells: {invalid_cells}")
            self.time_frames_table.blockSignals(True)
            for row_idx in range(self.time_frames_table.rowCount()):
                for col in range(self.time_frames_table.columnCount()):
                    item = self.time_frames_table.item(row_idx, col)
                    tooltip = ""
                    if item and item.text():
                        if (row_idx, col, "invalid") in invalid_cells:
                            item.setBackground(QBrush(Qt.yellow))
                            tooltip = f"Time Frame {row_idx + 1}: {'Time Frame ID' if col == 0 else 'Width'} must be a number"
                        elif (row_idx, col, "non-positive") in invalid_cells:
                            item.setBackground(QBrush(Qt.yellow))
                            tooltip = f"Time Frame {row_idx + 1}: {'Time Frame ID' if col == 0 else 'Width'} must be positive"
                        elif (row_idx, col, "duplicate") in invalid_cells:
                            item.setBackground(QBrush(Qt.yellow))
                            tooltip = f"Time Frame {row_idx + 1}: Time Frame ID must be unique"
                        elif (row_idx, col, "invalid format") in invalid_cells:
                            item.setBackground(QBrush(Qt.yellow))
                            tooltip = f"Time Frame {row_idx + 1}: Finish Date must be yyyy-MM-dd"
                        elif (row_idx, col, "empty") in invalid_cells:
                            item.setBackground(QBrush(Qt.yellow))
                            tooltip = f"Time Frame {row_idx + 1}: Finish Date required"
                        else:
                            item.setBackground(QBrush())
                    else:
                        item = QTableWidgetItem("")
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Time Frame {row_idx + 1}: {'Time Frame ID' if col == 0 else 'Finish Date' if col == 1 else 'Width'} required"
                        if col == 0:
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                        self.time_frames_table.setItem(row_idx, col, item)
                    item.setToolTip(tooltip)
            self.time_frames_table.blockSignals(False)

            if invalid_cells:
                logging.debug("Invalid cells detected, raising error")
                raise ValueError("Fix highlighted cells in Time Frames tab")

            # Update project_data.time_frames
            new_time_frames = []
            for row in tf_data:
                try:
                    new_time_frames.append({
                        "time_frame_id": int(row[0]),
                        "finish_date": row[1],
                        "width_proportion": float(row[2]) / 100
                    })
                except (ValueError, TypeError) as e:
                    logging.warning(f"Skipping invalid row {row}: {e}")
                    continue
            self.project_data.time_frames = sorted(new_time_frames, key=lambda x: x["time_frame_id"])

            logging.debug("Emitting data_updated signal")
            self.data_updated.emit(self.project_data.to_json())
            logging.debug("_sync_data completed successfully")
        except Exception as e:
            logging.error(f"Error in _sync_data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to sync data: {e}")

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            logging.debug("Calling _sync_data from itemChanged")
            self._sync_data()

    def _extract_table_data(self):
        logging.debug("Extracting table data")
        data = []
        for row in range(self.time_frames_table.rowCount()):
            row_data = []
            for col in range(self.time_frames_table.columnCount()):
                item = self.time_frames_table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        logging.debug(f"Extracted table data: {data}")
        return data