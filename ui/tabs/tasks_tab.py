from PyQt5.QtWidgets import QWidget, QTableWidget, QVBoxLayout, QPushButton, QGridLayout, QComboBox, QHeaderView, QTableWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush
from ..table_utils import NumericTableWidgetItem, add_row, remove_row, renumber_task_orders
import logging

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
        self.tasks_table = QTableWidget(self.app_config.general.tasks_rows, len(self.table_config.columns))
        self.tasks_table.setHorizontalHeaderLabels([col.name for col in self.table_config.columns])
        self.tasks_table.setSortingEnabled(True)
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tasks_table.setColumnWidth(0, 80)  # Task ID
        self.tasks_table.setColumnWidth(1, 80)  # Task Order
        self.tasks_table.setColumnWidth(2, 150)  # Task Name
        self.tasks_table.setColumnWidth(6, 120)  # Label Placement
        self.tasks_table.setColumnWidth(8, 100)  # Label Alignment
        self.tasks_table.setColumnWidth(9, 80)  # Horiz Offset
        self.tasks_table.setColumnWidth(10, 80)  # Vert Offset
        layout.addWidget(self.tasks_table)

        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Task")
        remove_btn = QPushButton("Remove Task")
        add_btn.clicked.connect(lambda: add_row(self.tasks_table, "tasks", self.app_config.tables, self))
        remove_btn.clicked.connect(lambda: remove_row(self.tasks_table, "tasks", self.app_config.tables, self))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _load_initial_data(self):
        table_data = self.project_data.get_table_data("tasks")
        row_count = max(len(table_data), self.table_config.min_rows)
        self.tasks_table.setRowCount(row_count)
        self._initializing = True

        if table_data:
            for row_idx, row_data in enumerate(table_data):
                for col_idx, value in enumerate(row_data):
                    col_config = self.table_config.columns[col_idx]
                    if col_config.widget_type == "combo":
                        combo = QComboBox()
                        combo.addItems(col_config.combo_items)
                        combo.setCurrentText(str(value) or col_config.combo_items[0])
                        self.tasks_table.setCellWidget(row_idx, col_idx, combo)
                    else:
                        item = NumericTableWidgetItem(str(value)) if col_idx in (0, 1) else QTableWidgetItem(str(value))
                        if col_idx == 0:  # Task ID read-only
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            item.setData(Qt.UserRole, int(value) if str(value).isdigit() else 0)
                        elif col_idx == 1:  # Task Order numeric
                            item.setData(Qt.UserRole, float(value) if value else 0.0)
                        self.tasks_table.setItem(row_idx, col_idx, item)
        else:
            max_task_id = 0
            max_task_order = 0
            for row_idx in range(row_count):
                defaults = self.table_config.default_generator(row_idx, {
                    "max_task_id": max_task_id,
                    "max_task_order": max_task_order
                })
                max_task_id += 1
                max_task_order += 1
                for col_idx, default in enumerate(defaults):
                    col_config = self.table_config.columns[col_idx]
                    if col_config.widget_type == "combo":
                        combo = QComboBox()
                        combo.addItems(col_config.combo_items)
                        combo.setCurrentText(str(default))
                        self.tasks_table.setCellWidget(row_idx, col_idx, combo)
                    else:
                        item = NumericTableWidgetItem(str(default)) if col_idx in (0, 1) else QTableWidgetItem(str(default))
                        if col_idx == 0:
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            item.setData(Qt.UserRole, int(default) if str(default).isdigit() else 0)
                        elif col_idx == 1:
                            item.setData(Qt.UserRole, float(default) if default else 0.0)
                        self.tasks_table.setItem(row_idx, col_idx, item)

        renumber_task_orders(self.tasks_table)
        self.tasks_table.sortByColumn(1, Qt.AscendingOrder)
        self._initializing = False

    def _sync_data(self):
        logging.debug("Starting _sync_data in TasksTab")
        tasks_data = self._extract_table_data()
        invalid_cells = set()
        task_order_counts = {}
        for row_idx, row in enumerate(tasks_data):
            try:
                task_order = float(row[1] or 0)
                task_order_counts[task_order] = task_order_counts.get(task_order, 0) + 1
                if task_order <= 0:
                    invalid_cells.add((row_idx, 1, "non-positive"))
            except ValueError:
                invalid_cells.add((row_idx, 1, "invalid"))

        non_unique_orders = {k for k, v in task_order_counts.items() if v > 1}
        self.tasks_table.blockSignals(True)
        for row_idx in range(self.tasks_table.rowCount()):
            for col in range(self.tasks_table.columnCount()):
                col_config = self.table_config.columns[col]
                if col_config.widget_type == "combo":
                    current_widget = self.tasks_table.cellWidget(row_idx, col)
                    if not isinstance(current_widget, QComboBox):
                        combo = QComboBox()
                        combo.addItems(col_config.combo_items)
                        value = tasks_data[row_idx][col] if row_idx < len(tasks_data) else col_config.combo_items[0]
                        combo.setCurrentText(value or col_config.combo_items[0])
                        self.tasks_table.setCellWidget(row_idx, col, combo)
                        logging.debug(f"Set QComboBox in _sync_data for row {row_idx}, col {col} with value {combo.currentText()}")
                else:
                    item = self.tasks_table.item(row_idx, col)
                    tooltip = ""
                    task_id = self.tasks_table.item(row_idx, 0).text() if self.tasks_table.item(row_idx, 0) else "Unknown"
                    if col == 1:  # Task Order column
                        if item and item.text():
                            try:
                                task_order = float(item.text())
                                if task_order in non_unique_orders:
                                    item.setBackground(QBrush(Qt.yellow))
                                    tooltip = f"Task {task_id}: Task Order must be unique"
                                elif task_order <= 0:
                                    item.setBackground(QBrush(Qt.yellow))
                                    tooltip = f"Task {task_id}: Task Order must be positive"
                                else:
                                    item.setBackground(QBrush())
                            except ValueError:
                                item.setBackground(QBrush(Qt.yellow))
                                tooltip = f"Task {task_id}: Task Order must be a number"
                        else:
                            item = NumericTableWidgetItem("0")
                            item.setData(Qt.UserRole, 0.0)
                            item.setBackground(QBrush(Qt.yellow))
                            tooltip = f"Task {task_id}: Task Order required"
                            self.tasks_table.setItem(row_idx, col, item)
                        item.setToolTip(tooltip)
        self.tasks_table.blockSignals(False)

        if invalid_cells:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", "Fix highlighted cells in Tasks tab")
            return

        self.project_data.update_from_table("tasks", tasks_data)
        logging.debug("_sync_data in TasksTab completed")

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            logging.debug("Calling _sync_data from itemChanged")
            self._sync_data()

    def _extract_table_data(self):
        data = []
        for row in range(self.tasks_table.rowCount()):
            row_data = []
            for col in range(self.tasks_table.columnCount()):
                widget = self.tasks_table.cellWidget(row, col)
                if widget and isinstance(widget, QComboBox):
                    row_data.append(widget.currentText())
                else:
                    item = self.tasks_table.item(row, col)
                    row_data.append(item.text() if item else "")
            data.append(row_data)
        return data