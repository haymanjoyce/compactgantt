from PyQt5.QtWidgets import QWidget, QTableWidget, QVBoxLayout, QPushButton, QGridLayout, QHeaderView, QTableWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush
from ..table_utils import add_row, remove_row

class ConnectorsTab(QWidget):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        super().__init__()
        self.project_data = project_data
        self.app_config = app_config
        self.table_config = app_config.get_table_config("connectors")
        self.setup_ui()
        self._load_initial_data()
        self.connectors_table.itemChanged.connect(self._sync_data_if_not_initializing)
        self._initializing = False

    def setup_ui(self):
        layout = QVBoxLayout()
        self.connectors_table = QTableWidget(2, len(self.table_config.columns))
        self.connectors_table.setHorizontalHeaderLabels([col.name for col in self.table_config.columns])
        self.connectors_table.setSortingEnabled(True)
        self.connectors_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.connectors_table)

        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Connector")
        remove_btn = QPushButton("Remove Connector")
        add_btn.clicked.connect(lambda: add_row(self.connectors_table, "connectors", self.app_config.tables, self))
        remove_btn.clicked.connect(lambda: remove_row(self.connectors_table, "connectors", self.app_config.tables, self))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _load_initial_data(self):
        table_data = self.project_data.get_table_data("connectors")
        row_count = max(len(table_data), self.table_config.min_rows)
        self.connectors_table.setRowCount(row_count)
        self._initializing = True

        if table_data:
            for row_idx, row_data in enumerate(table_data):
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    self.connectors_table.setItem(row_idx, col_idx, item)
        else:
            for row_idx in range(row_count):
                defaults = self.table_config.default_generator(row_idx, {})
                for col_idx, default in enumerate(defaults):
                    item = QTableWidgetItem(str(default))
                    self.connectors_table.setItem(row_idx, col_idx, item)

        self._initializing = False

    def _sync_data(self):
        connectors_data = self._extract_table_data()
        invalid_cells = set()
        for row_idx, row in enumerate(connectors_data):
            from_task_id = row[0] or "0"
            to_task_id = row[1] or "0"
            try:
                from_task_id = int(from_task_id)
                to_task_id = int(to_task_id)
                if from_task_id <= 0:
                    invalid_cells.add((row_idx, 0, "non-positive"))
                if to_task_id <= 0:
                    invalid_cells.add((row_idx, 1, "non-positive"))
                if from_task_id == to_task_id:
                    invalid_cells.add((row_idx, 1, "same-id"))
            except ValueError:
                invalid_cells.add((row_idx, 0, "invalid"))
                invalid_cells.add((row_idx, 1, "invalid"))

        self.connectors_table.blockSignals(True)
        for row_idx in range(self.connectors_table.rowCount()):
            for col in (0, 1):
                item = self.connectors_table.item(row_idx, col)
                tooltip = ""
                if item:
                    if (row_idx, col, "invalid") in invalid_cells:
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Connector {row_idx + 1}: {'From' if col == 0 else 'To'} Task ID must be a number"
                    elif (row_idx, col, "non-positive") in invalid_cells:
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Connector {row_idx + 1}: {'From' if col == 0 else 'To'} Task ID must be positive"
                    elif (row_idx, col, "same-id") in invalid_cells:
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Connector {row_idx + 1}: From and To Task IDs must be different"
                    else:
                        item.setBackground(QBrush())
                else:
                    item = QTableWidgetItem("0")
                    item.setBackground(QBrush(Qt.yellow))
                    tooltip = f"Connector {row_idx + 1}: {'From' if col == 0 else 'To'} Task ID required"
                    self.connectors_table.setItem(row_idx, col, item)
                item.setToolTip(tooltip)
        self.connectors_table.blockSignals(False)

        if invalid_cells:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", "Fix highlighted cells in Connectors tab")
            return

        self.project_data.update_from_table("connectors", connectors_data)

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            self._sync_data()

    def _extract_table_data(self):
        data = []
        for row in range(self.connectors_table.rowCount()):
            row_data = []
            for col in range(self.connectors_table.columnCount()):
                item = self.connectors_table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data