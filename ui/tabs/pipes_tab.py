from PyQt5.QtWidgets import QWidget, QTableWidget, QVBoxLayout, QPushButton, QGridLayout, QHeaderView, QTableWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush
from datetime import datetime
from ..table_utils import add_row, remove_row

class PipesTab(QWidget):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        super().__init__()
        self.project_data = project_data
        self.app_config = app_config
        self.table_config = app_config.get_table_config("pipes")
        self.setup_ui()
        self._load_initial_data()
        self.pipes_table.itemChanged.connect(self._sync_data_if_not_initializing)
        self._initializing = False

    def setup_ui(self):
        layout = QVBoxLayout()
        self.pipes_table = QTableWidget(self.app_config.general.pipes_rows, len(self.table_config.columns))
        self.pipes_table.setHorizontalHeaderLabels([col.name for col in self.table_config.columns])
        self.pipes_table.setSortingEnabled(True)
        self.pipes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.pipes_table)

        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Pipe")
        remove_btn = QPushButton("Remove Pipe")
        add_btn.clicked.connect(lambda: add_row(self.pipes_table, "pipes", self.app_config.tables, self))
        remove_btn.clicked.connect(lambda: remove_row(self.pipes_table, "pipes", self.app_config.tables, self))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _load_initial_data(self):
        table_data = self.project_data.get_table_data("pipes")
        row_count = max(len(table_data), self.table_config.min_rows)
        self.pipes_table.setRowCount(row_count)
        self._initializing = True

        if table_data:
            for row_idx, row_data in enumerate(table_data):
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    self.pipes_table.setItem(row_idx, col_idx, item)
        else:
            for row_idx in range(row_count):
                defaults = self.table_config.default_generator(row_idx, {})
                for col_idx, default in enumerate(defaults):
                    item = QTableWidgetItem(str(default))
                    self.pipes_table.setItem(row_idx, col_idx, item)

        self._initializing = False

    def _sync_data(self):
        pipes_data = self._extract_table_data()
        invalid_cells = set()
        for row_idx, row in enumerate(pipes_data):
            date = row[0] or ""
            colour = row[1] or "red"

            # Validate Date
            try:
                datetime.strptime(date, "%Y-%m-%d") if date else None
            except ValueError:
                invalid_cells.add((row_idx, 0, "invalid format"))

            # Validate Colour
            if not colour:
                invalid_cells.add((row_idx, 1, "empty"))

        self.pipes_table.blockSignals(True)
        for row_idx in range(self.pipes_table.rowCount()):
            for col in range(self.pipes_table.columnCount()):
                item = self.pipes_table.item(row_idx, col)
                tooltip = ""
                if item:
                    if (row_idx, col, "invalid format") in invalid_cells:
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Pipe {row_idx + 1}: Date must be yyyy-MM-dd"
                    elif (row_idx, col, "empty") in invalid_cells:
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Pipe {row_idx + 1}: Colour must be specified"
                    else:
                        item.setBackground(QBrush())
                else:
                    item = QTableWidgetItem("")
                    item.setBackground(QBrush(Qt.yellow))
                    tooltip = f"Pipe {row_idx + 1}: {'Date' if col == 0 else 'Colour'} required"
                    self.pipes_table.setItem(row_idx, col, item)
                item.setToolTip(tooltip)
        self.pipes_table.blockSignals(False)

        if invalid_cells:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", "Fix highlighted cells in Pipes tab")
            return

        self.project_data.update_from_table("pipes", pipes_data)

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            self._sync_data()

    def _extract_table_data(self):
        data = []
        for row in range(self.pipes_table.rowCount()):
            row_data = []
            for col in range(self.pipes_table.columnCount()):
                item = self.pipes_table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data