from PyQt5.QtWidgets import QWidget, QTableWidget, QVBoxLayout, QPushButton, QGridLayout, QHeaderView, QTableWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush
from datetime import datetime
from ..table_utils import add_row, remove_row

class CurtainsTab(QWidget):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        super().__init__()
        self.project_data = project_data
        self.app_config = app_config
        self.table_config = app_config.get_table_config("curtains")
        self.setup_ui()
        self._load_initial_data()
        self.curtains_table.itemChanged.connect(self._sync_data_if_not_initializing)
        self._initializing = False

    def setup_ui(self):
        layout = QVBoxLayout()
        self.curtains_table = QTableWidget(self.app_config.general.curtains_rows, len(self.table_config.columns))
        self.curtains_table.setHorizontalHeaderLabels([col.name for col in self.table_config.columns])
        self.curtains_table.setSortingEnabled(True)
        self.curtains_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.curtains_table)

        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Curtain")
        remove_btn = QPushButton("Remove Curtain")
        add_btn.clicked.connect(lambda: add_row(self.curtains_table, "curtains", self.app_config.tables, self))
        remove_btn.clicked.connect(lambda: remove_row(self.curtains_table, "curtains", self.app_config.tables, self))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _load_initial_data(self):
        table_data = self.project_data.get_table_data("curtains")
        row_count = max(len(table_data), self.table_config.min_rows)
        self.curtains_table.setRowCount(row_count)
        self._initializing = True

        if table_data:
            for row_idx, row_data in enumerate(table_data):
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    self.curtains_table.setItem(row_idx, col_idx, item)
        else:
            for row_idx in range(row_count):
                defaults = self.table_config.default_generator(row_idx, {})
                for col_idx, default in enumerate(defaults):
                    item = QTableWidgetItem(str(default))
                    self.curtains_table.setItem(row_idx, col_idx, item)

        self._initializing = False

    def _sync_data(self):
        curtains_data = self._extract_table_data()
        invalid_cells = set()
        for row_idx, row in enumerate(curtains_data):
            from_date = row[0] or ""
            to_date = row[1] or ""
            colour = row[2] or self.app_config.general.default_curtain_color

            # Validate From Date
            try:
                from_dt = datetime.strptime(from_date, "%Y-%m-%d") if from_date else None
            except ValueError:
                invalid_cells.add((row_idx, 0, "invalid format"))
                from_dt = None

            # Validate To Date
            try:
                to_dt = datetime.strptime(to_date, "%Y-%m-%d") if to_date else None
            except ValueError:
                invalid_cells.add((row_idx, 1, "invalid format"))
                to_dt = None

            # Validate date order
            if from_dt and to_dt and to_dt < from_dt:
                invalid_cells.add((row_idx, 1, "before-from"))

            # Validate Colour
            if not colour:
                invalid_cells.add((row_idx, 2, "empty"))

        self.curtains_table.blockSignals(True)
        for row_idx in range(self.curtains_table.rowCount()):
            for col in range(self.curtains_table.columnCount()):
                item = self.curtains_table.item(row_idx, col)
                tooltip = ""
                if item:
                    if (row_idx, col, "invalid format") in invalid_cells:
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Curtain {row_idx + 1}: {'From' if col == 0 else 'To'} Date must be yyyy-MM-dd"
                    elif (row_idx, col, "before-from") in invalid_cells:
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Curtain {row_idx + 1}: To Date must be on or after From Date"
                    elif (row_idx, col, "empty") in invalid_cells:
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Curtain {row_idx + 1}: Colour must be specified"
                    else:
                        item.setBackground(QBrush())
                else:
                    item = QTableWidgetItem("")
                    item.setBackground(QBrush(Qt.yellow))
                    tooltip = f"Curtain {row_idx + 1}: {'From Date' if col == 0 else 'To Date' if col == 1 else 'Colour'} required"
                    self.curtains_table.setItem(row_idx, col, item)
                item.setToolTip(tooltip)
        self.curtains_table.blockSignals(False)

        if invalid_cells:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", "Fix highlighted cells in Curtains tab")
            return

        self.project_data.update_from_table("curtains", curtains_data)

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            self._sync_data()

    def _extract_table_data(self):
        data = []
        for row in range(self.curtains_table.rowCount()):
            row_data = []
            for col in range(self.curtains_table.columnCount()):
                item = self.curtains_table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data