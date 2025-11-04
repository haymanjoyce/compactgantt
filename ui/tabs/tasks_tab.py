from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                           QGridLayout, QComboBox, QHeaderView, QTableWidgetItem, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush
from typing import List, Dict, Any
import logging
from ui.table_utils import NumericTableWidgetItem, add_row, remove_row, renumber_task_orders, CheckBoxWidget, highlight_table_errors, extract_table_data
from .base_tab import BaseTab

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TasksTab(BaseTab):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        self.table_config = app_config.get_table_config("tasks")
        super().__init__(project_data, app_config)

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
        add_btn.clicked.connect(lambda: add_row(self.tasks_table, "tasks", self.app_config.tables, self, "ID"))
        remove_btn.clicked.connect(lambda: remove_row(self.tasks_table, "tasks", 
                                                    self.app_config.tables, self))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def _connect_signals(self):
        self._item_changed_connection = self.tasks_table.itemChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data(self):
        self._load_initial_data_impl()

    def _load_initial_data_impl(self):
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
                    col_config = self.table_config.columns[col_idx]
                    if col_config.widget_type == "combo":
                        combo = QComboBox()
                        combo.addItems(col_config.combo_items)
                        combo.setCurrentText(str(value) or col_config.combo_items[0])
                        self.tasks_table.setCellWidget(row_idx, col_idx, combo)
                    else:
                        # Columns 1 (ID), 2 (Order), and 3 (Row) are numeric    
                        item = (NumericTableWidgetItem(str(value))
                               if col_idx in (1, 2, 3) else QTableWidgetItem(str(value)))                                                                       

                        if col_idx == 1:  # Task ID read-only
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            item.setData(Qt.UserRole, int(value) if str(value).isdigit() else 0)
                        elif col_idx == 2:  # Task Order numeric
                            item.setData(Qt.UserRole, float(value) if value else 0.0)
                        elif col_idx == 3:  # Row number numeric
                            item.setData(Qt.UserRole, int(value) if str(value).isdigit() else 1)
                        self.tasks_table.setItem(row_idx, col_idx, item)
            else:
                context = {
                    "max_task_id": len(table_data) + row_idx,
                    "max_task_order": len(table_data) + row_idx
                }
                defaults = self.table_config.default_generator(row_idx, context)
                # Skip the first default (checkbox state) and start from index 1
                for col_idx, default in enumerate(defaults[1:], start=1):
                    col_config = self.table_config.columns[col_idx]
                    if col_config.widget_type == "combo":
                        combo = QComboBox()
                        combo.addItems(col_config.combo_items)
                        combo.setCurrentText(str(default))
                        self.tasks_table.setCellWidget(row_idx, col_idx, combo)
                    else:
                        # Columns 1 (ID), 2 (Order), and 3 (Row) are numeric
                        item = (NumericTableWidgetItem(str(default)) 
                               if col_idx in (1, 2, 3) else QTableWidgetItem(str(default)))
                        if col_idx == 1:  # Task ID read-only
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            item.setData(Qt.UserRole, int(default) if str(default).isdigit() else 0)
                        elif col_idx == 2:  # Task Order numeric
                            item.setData(Qt.UserRole, float(default) if default else 0.0)
                        elif col_idx == 3:  # Row number numeric
                            item.setData(Qt.UserRole, int(default) if str(default).isdigit() else 1)
                        self.tasks_table.setItem(row_idx, col_idx, item)

        renumber_task_orders(self.tasks_table)
        # Find the Order column for sorting
        order_column = None
        for i in range(self.tasks_table.columnCount()):
            if self.tasks_table.horizontalHeaderItem(i).text() == "Order":
                order_column = i
                break
        if order_column is not None:
            self.tasks_table.sortByColumn(order_column, Qt.AscendingOrder)  # Sort by Task Order
        self._initializing = False

    def _sync_data(self):
        self._sync_data_impl()

    def _sync_data_impl(self):
        logging.debug("Starting _sync_data in TasksTab")
        tasks_data = self._extract_table_data()
        errors = self.project_data.project_service.update_from_table(self.project_data, "tasks", tasks_data)
        
        # Use common error highlighting function
        highlight_table_errors(self.tasks_table, errors)
        logging.debug("_sync_data in TasksTab completed")

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            logging.debug("Calling _sync_data from itemChanged")
            self._sync_data()

    def _extract_table_data(self) -> List[List[str]]:
        return extract_table_data(self.tasks_table, include_widgets=True)