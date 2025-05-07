from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                           QGridLayout, QComboBox, QHeaderView, QTableWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush
from typing import List, Dict, Any
import logging
from ui.table_utils import NumericTableWidgetItem, add_row, remove_row, renumber_task_orders, CheckBoxWidget

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TasksTab(QWidget):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        super().__init__()
        self.project_data = project_data
        self.app_config = app_config
        self.table_config = app_config.get_table_config("tasks")
        self.setup_ui()
        self._load_initial_data()
        self._item_changed_connection = self.tasks_table.itemChanged.connect(self._sync_data_if_not_initializing)
        self._initializing = False

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Create table
        self.tasks_table = QTableWidget(0, len(self.table_config.columns))
        headers = [col.name for col in self.table_config.columns]
        self.tasks_table.setHorizontalHeaderLabels(headers)

        # Set all columns to resize to contents
        header = self.tasks_table.horizontalHeader()
        for i in range(self.tasks_table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        # Enable horizontal scroll bar
        self.tasks_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tasks_table.setSortingEnabled(True)
        layout.addWidget(self.tasks_table)

        # Create buttons
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Task")
        remove_btn = QPushButton("Remove Task")
        add_btn.clicked.connect(lambda: add_row(self.tasks_table, "tasks", self.app_config.tables, self, "Task ID"))
        remove_btn.clicked.connect(lambda: remove_row(self.tasks_table, "tasks", 
                                                    self.app_config.tables, self))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _load_initial_data(self):
        table_data = self.project_data.project_service.get_table_data(self.project_data, "tasks")
        row_count = max(len(table_data), self.table_config.min_rows)
        self.tasks_table.setRowCount(row_count)
        self._initializing = True

        for row_idx in range(row_count):
            # Add checkbox first
            checkbox_widget = CheckBoxWidget()
            self.tasks_table.setCellWidget(row_idx, 0, checkbox_widget)

            if row_idx < len(table_data):
                row_data = table_data[row_idx]
                # Start from column 1 since column 0 is checkbox
                for col_idx, value in enumerate(row_data, start=1):
                    col_config = self.table_config.columns[col_idx - 1]
                    if col_config.widget_type == "combo":
                        combo = QComboBox()
                        combo.addItems(col_config.combo_items)
                        combo.setCurrentText(str(value) or col_config.combo_items[0])
                        self.tasks_table.setCellWidget(row_idx, col_idx, combo)
                    else:
                        item = (NumericTableWidgetItem(str(value)) 
                               if col_idx in (1, 2) else QTableWidgetItem(str(value)))
                        if col_idx == 1:  # Task ID read-only
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            item.setData(Qt.UserRole, int(value) if str(value).isdigit() else 0)
                        elif col_idx == 2:  # Task Order numeric
                            item.setData(Qt.UserRole, float(value) if value else 0.0)
                        self.tasks_table.setItem(row_idx, col_idx, item)
            else:
                context = {
                    "max_task_id": len(table_data) + row_idx,
                    "max_task_order": len(table_data) + row_idx
                }
                defaults = self.table_config.default_generator(row_idx, context)
                # Skip the first default (checkbox state) and start from index 1
                for col_idx, default in enumerate(defaults[1:], start=1):
                    col_config = self.table_config.columns[col_idx - 1]
                    if col_config.widget_type == "combo":
                        combo = QComboBox()
                        combo.addItems(col_config.combo_items)
                        combo.setCurrentText(str(default))
                        self.tasks_table.setCellWidget(row_idx, col_idx, combo)
                    else:
                        item = (NumericTableWidgetItem(str(default)) 
                               if col_idx in (1, 2) else QTableWidgetItem(str(default)))
                        if col_idx == 1:  # Task ID read-only
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            item.setData(Qt.UserRole, int(default) if str(default).isdigit() else 0)
                        elif col_idx == 2:  # Task Order numeric
                            item.setData(Qt.UserRole, float(default) if default else 0.0)
                        self.tasks_table.setItem(row_idx, col_idx, item)

        renumber_task_orders(self.tasks_table)
        self.tasks_table.sortByColumn(2, Qt.AscendingOrder)  # Sort by Task Order
        self._initializing = False

    def _sync_data(self):
        logging.debug("Starting _sync_data in TasksTab")
        tasks_data = self._extract_table_data()
        errors = self.project_data.project_service.update_from_table(self.project_data, "tasks", tasks_data)
        
        # Clear all highlights first
        self.tasks_table.blockSignals(True)
        for row in range(self.tasks_table.rowCount()):
            for col in range(1, self.tasks_table.columnCount()):  # Skip checkbox column
                item = self.tasks_table.item(row, col)
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
                        for col in range(1, self.tasks_table.columnCount()):
                            item = self.tasks_table.item(row_idx, col)
                            if item:
                                item.setBackground(QBrush(Qt.yellow))
                                item.setToolTip(error.split(":", 1)[1].strip())
                    except (ValueError, IndexError):
                        logging.error(f"Failed to parse error message: {error}")
                        continue
            
            QMessageBox.critical(self, "Error", "\n".join(errors))

        self.tasks_table.blockSignals(False)
        logging.debug("_sync_data in TasksTab completed")

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            logging.debug("Calling _sync_data from itemChanged")
            self._sync_data()

    def _extract_table_data(self) -> List[List[str]]:
        data = []
        for row in range(self.tasks_table.rowCount()):
            row_data = []
            # Start from column 1 to skip checkbox column
            for col in range(1, self.tasks_table.columnCount()):
                widget = self.tasks_table.cellWidget(row, col)
                if widget and isinstance(widget, QComboBox):
                    row_data.append(widget.currentText())
                else:
                    item = self.tasks_table.item(row, col)
                    row_data.append(item.text() if item else "")
            data.append(row_data)
        return data