from PyQt5.QtWidgets import QWidget, QTableWidget, QVBoxLayout, QPushButton, QGridLayout, QHeaderView, QTableWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush
from ..table_utils import add_row, remove_row

class SwimlanesTab(QWidget):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        super().__init__()
        self.project_data = project_data
        self.app_config = app_config
        self.table_config = app_config.get_table_config("swimlanes")
        self.setup_ui()
        self._load_initial_data()
        self.swimlanes_table.itemChanged.connect(self._sync_data_if_not_initializing)
        self._initializing = False

    def setup_ui(self):
        layout = QVBoxLayout()
        self.swimlanes_table = QTableWidget(2, len(self.table_config.columns))
        self.swimlanes_table.setHorizontalHeaderLabels([col.name for col in self.table_config.columns])
        self.swimlanes_table.setSortingEnabled(True)
        self.swimlanes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.swimlanes_table)

        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Swimlane")
        remove_btn = QPushButton("Remove Swimlane")
        add_btn.clicked.connect(lambda: add_row(self.swimlanes_table, "swimlanes", self.app_config.tables, self))
        remove_btn.clicked.connect(lambda: remove_row(self.swimlanes_table, "swimlanes", self.app_config.tables, self))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _load_initial_data(self):
        table_data = self.project_data.get_table_data("swimlanes")
        row_count = max(len(table_data), self.table_config.min_rows)
        self.swimlanes_table.setRowCount(row_count)
        self._initializing = True

        if table_data:
            for row_idx, row_data in enumerate(table_data):
                for col_idx, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    self.swimlanes_table.setItem(row_idx, col_idx, item)
        else:
            for row_idx in range(row_count):
                defaults = self.table_config.default_generator(row_idx, {})
                for col_idx, default in enumerate(defaults):
                    item = QTableWidgetItem(str(default))
                    self.swimlanes_table.setItem(row_idx, col_idx, item)

        self._initializing = False

    def _sync_data(self):
        swimlanes_data = self._extract_table_data()
        invalid_cells = set()
        for row_idx, row in enumerate(swimlanes_data):
            from_row = row[0] or "1"
            to_row = row[1] or "1"
            title = row[2] or ""
            colour = row[3] or "lightblue"

            # Validate From Row Number
            try:
                from_row_int = int(from_row)
                if from_row_int <= 0:
                    invalid_cells.add((row_idx, 0, "non-positive"))
            except ValueError:
                invalid_cells.add((row_idx, 0, "invalid"))

            # Validate To Row Number
            try:
                to_row_int = int(to_row)
                if to_row_int <= 0:
                    invalid_cells.add((row_idx, 1, "non-positive"))
                elif from_row_int and to_row_int < from_row_int:
                    invalid_cells.add((row_idx, 1, "less-than-from"))
            except ValueError:
                invalid_cells.add((row_idx, 1, "invalid"))

            # Validate Colour
            if not colour:
                invalid_cells.add((row_idx, 3, "empty"))

        self.swimlanes_table.blockSignals(True)
        for row_idx in range(self.swimlanes_table.rowCount()):
            for col in range(self.swimlanes_table.columnCount()):
                item = self.swimlanes_table.item(row_idx, col)
                tooltip = ""
                if item:
                    if (row_idx, col, "invalid") in invalid_cells:
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Swimlane {row_idx + 1}: {'From' if col == 0 else 'To'} Row Number must be a number"
                    elif (row_idx, col, "non-positive") in invalid_cells:
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Swimlane {row_idx + 1}: {'From' if col == 0 else 'To'} Row Number must be positive"
                    elif (row_idx, col, "less-than-from") in invalid_cells:
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Swimlane {row_idx + 1}: To Row Number must be on or after From Row Number"
                    elif (row_idx, col, "empty") in invalid_cells:
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Swimlane {row_idx + 1}: Colour must be specified"
                    else:
                        item.setBackground(QBrush())
                else:
                    item = QTableWidgetItem("")
                    item.setBackground(QBrush(Qt.yellow))
                    tooltip = f"Swimlane {row_idx + 1}: {'From Row Number' if col == 0 else 'To Row Number' if col == 1 else 'Title' if col == 2 else 'Colour'} required"
                    self.swimlanes_table.setItem(row_idx, col, item)
                item.setToolTip(tooltip)
        self.swimlanes_table.blockSignals(False)

        if invalid_cells:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", "Fix highlighted cells in Swimlanes tab")
            return

        self.project_data.update_from_table("swimlanes", swimlanes_data)

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            self._sync_data()

    def _extract_table_data(self):
        data = []
        for row in range(self.swimlanes_table.rowCount()):
            row_data = []
            for col in range(self.swimlanes_table.columnCount()):
                item = self.swimlanes_table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data