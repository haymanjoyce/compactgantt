"""
Purpose: Defines DataEntryWindow, handles user input via tabs and UI interactions.
Why: Provides a clean interface for Gantt chart data entry, relying on ProjectData for logic.
"""

from PyQt5.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QFileDialog, QTabWidget, QAction, QApplication, QToolBar, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDate, pyqtSignal
from data_model import ProjectData
from config import Config
import json

class DataEntryWindow(QMainWindow):
    data_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gantt Chart Data Entry")
        self.setGeometry(100, 100, Config.DATA_ENTRY_WIDTH, Config.DATA_ENTRY_HEIGHT)
        self.project_data = ProjectData()

        # Menu bar setup
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("File")
        self.save_action = QAction("Save Project", self)
        self.save_action.triggered.connect(self.save_to_json)
        self.file_menu.addAction(self.save_action)
        self.load_action = QAction("Load Project", self)  # Fixed typo: 'clazz' → 'QAction'
        self.load_action.triggered.connect(self.load_from_json)
        self.file_menu.addAction(self.load_action)

        self.tools_menu = self.menu_bar.addMenu("Tools")
        self.add_row_action = QAction("Add Row to Current Tab", self)
        self.add_row_action.triggered.connect(self.add_row)
        self.tools_menu.addAction(self.add_row_action)
        self.remove_row_action = QAction("Remove Last Row from Current Tab", self)
        self.remove_row_action.triggered.connect(self.remove_row)
        self.tools_menu.addAction(self.remove_row_action)
        self.generate_action = QAction("Generate Gantt Chart", self)
        self.generate_action.triggered.connect(self._emit_data_updated)
        self.tools_menu.addAction(self.generate_action)

        # Toolbar setup
        self.toolbar = QToolBar("Tools")
        self.addToolBar(self.toolbar)
        style = QApplication.style()
        self.add_row_tool = QAction(QIcon(style.standardIcon(style.SP_FileIcon)), "Add Row", self)
        self.add_row_tool.triggered.connect(self.add_row)
        self.toolbar.addAction(self.add_row_tool)
        self.remove_row_tool = QAction(QIcon(style.standardIcon(style.SP_TrashIcon)), "Remove Row", self)
        self.remove_row_tool.triggered.connect(self.remove_row)
        self.toolbar.addAction(self.remove_row_tool)
        self.generate_tool = QAction(QIcon(style.standardIcon(style.SP_ArrowRight)), "Generate Gantt Chart", self)
        self.generate_tool.triggered.connect(self._emit_data_updated)
        self.toolbar.addAction(self.generate_tool)

        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Tab widget for multiple tables
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Tasks table
        self.tasks_table = QTableWidget(Config.TASKS_ROWS, 3)
        self.tasks_table.setHorizontalHeaderLabels(["Task Name", "Start Date", "Duration (days)"])
        self.tabs.addTab(self.tasks_table, "Tasks")

        # Pipes table
        self.pipes_table = QTableWidget(Config.PIPES_ROWS, 2)
        self.pipes_table.setHorizontalHeaderLabels(["Pipe Name", "Date"])
        self.tabs.addTab(self.pipes_table, "Pipes")

        # Curtains table
        self.curtains_table = QTableWidget(Config.CURTAINS_ROWS, 4)
        self.curtains_table.setHorizontalHeaderLabels(["Curtain Name", "Start Date", "End Date", "Color"])
        self.tabs.addTab(self.curtains_table, "Curtains")

        self._load_initial_data()

    def _load_initial_data(self):
        """Populate tables with default or loaded data."""
        for table, data, tab_name in [
            (self.tasks_table, self.project_data.get_table_data("tasks"), "tasks"),
            (self.pipes_table, self.project_data.get_table_data("pipes"), "pipes"),
            (self.curtains_table, self.project_data.get_table_data("curtains"), "curtains")
        ]:
            table.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                for col_idx, value in enumerate(row_data):
                    table.setItem(row_idx, col_idx, QTableWidgetItem(value))

    def add_row(self):
        """Add a row to the current tab’s table and update ProjectData."""
        current_table = self.tabs.currentWidget()
        current_rows = current_table.rowCount()
        current_table.insertRow(current_rows)
        today = QDate.currentDate().toString("yyyy-MM-dd")
        if current_table == self.tasks_table:
            current_table.setItem(current_rows, 0, QTableWidgetItem(f"Task {current_rows + 1}"))
            current_table.setItem(current_rows, 1, QTableWidgetItem(today))
            current_table.setItem(current_rows, 2, QTableWidgetItem("1"))
        elif current_table == self.pipes_table:
            current_table.setItem(current_rows, 0, QTableWidgetItem(f"Pipe {current_rows + 1}"))
            current_table.setItem(current_rows, 1, QTableWidgetItem(today))
        elif current_table == self.curtains_table:
            current_table.setItem(current_rows, 0, QTableWidgetItem(f"Curtain {current_rows + 1}"))
            current_table.setItem(current_rows, 1, QTableWidgetItem(today))
            current_table.setItem(current_rows, 2, QTableWidgetItem(today))
            current_table.setItem(current_rows, 3, QTableWidgetItem(Config.DEFAULT_CURTAIN_COLOR))
        self._sync_data()

    def remove_row(self):
        """Remove the last row from the current tab’s table and update ProjectData."""
        current_table = self.tabs.currentWidget()
        if current_table.rowCount() > 1:
            current_table.removeRow(current_table.rowCount() - 1)
            self._sync_data()

    def _extract_table_data(self, table):
        """Extract data from a given table."""
        data = []
        for row in range(table.rowCount()):
            row_data = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data

    def _sync_data(self):
        """Sync table data with ProjectData and emit signal."""
        try:
            self.project_data.update_from_table("tasks", self._extract_table_data(self.tasks_table))
            self.project_data.update_from_table("pipes", self._extract_table_data(self.pipes_table))
            self.project_data.update_from_table("curtains", self._extract_table_data(self.curtains_table))
            self.data_updated.emit(self.project_data.to_json())
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))

    def _emit_data_updated(self):
        """Helper to sync data and emit the signal when generating Gantt chart."""
        self._sync_data()

    def save_to_json(self):
        """Save ProjectData to a JSON file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "JSON Files (*.json)")
        if file_path:
            try:
                self._sync_data()
                json_str = json.dumps(self.project_data.to_json(), indent=4)
                with open(file_path, "w") as jsonfile:
                    jsonfile.write(json_str)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving JSON: {e}")

    def load_from_json(self):
        """Load data into ProjectData and refresh tables."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "r") as jsonfile:
                    data = json.load(jsonfile)
                self.project_data = ProjectData.from_json(data)
                self._load_initial_data()
                self.data_updated.emit(self.project_data.to_json())
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading JSON: {e}")