"""
Purpose: Defines DataEntryWindow, handles user input via tabs and UI interactions.
Why: Provides a clean interface for Gantt chart data entry, relying on ProjectData for logic.
"""

from PyQt5.QtWidgets import (QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
                             QFileDialog, QTabWidget, QAction, QApplication, QToolBar, QMessageBox,
                             QLineEdit, QLabel, QGridLayout, QPushButton)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QDate, pyqtSignal
from data_model import ProjectData, FrameConfig
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
        self.load_action = QAction("Load Project", self)
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

        # Tab widget for tables
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Tasks table
        self.tasks_table = QTableWidget(Config.TASKS_ROWS, 3)
        self.tasks_table.setHorizontalHeaderLabels(["Task Name", "Start Date", "Duration (days)"])
        self.tabs.addTab(self.tasks_table, "Tasks")

        # Layout tab
        self.layout_tab = QWidget()
        self.setup_layout_tab()
        self.tabs.addTab(self.layout_tab, "Layout")

        self._load_initial_data()

    def setup_layout_tab(self):
        """Set up the Layout tab for FrameConfig and TimeFrames."""
        layout = QGridLayout()

        # FrameConfig inputs
        layout.addWidget(QLabel("Outer Width:"), 0, 0)
        self.outer_width_input = QLineEdit(str(self.project_data.frame_config.outer_width))
        layout.addWidget(self.outer_width_input, 0, 1)

        layout.addWidget(QLabel("Outer Height:"), 1, 0)
        self.outer_height_input = QLineEdit(str(self.project_data.frame_config.outer_height))
        layout.addWidget(self.outer_height_input, 1, 1)

        layout.addWidget(QLabel("Header Height:"), 2, 0)
        self.header_height_input = QLineEdit(str(self.project_data.frame_config.header_height))
        layout.addWidget(self.header_height_input, 2, 1)

        layout.addWidget(QLabel("Footer Height:"), 3, 0)
        self.footer_height_input = QLineEdit(str(self.project_data.frame_config.footer_height))
        layout.addWidget(self.footer_height_input, 3, 1)

        layout.addWidget(QLabel("Margins (top, right, bottom, left):"), 4, 0)
        self.margins_input = QLineEdit(", ".join(map(str, self.project_data.frame_config.margins)))
        layout.addWidget(self.margins_input, 4, 1)

        # TimeFrames table
        self.time_frames_table = QTableWidget(2, 4)  # Start with 2 rows
        self.time_frames_table.setHorizontalHeaderLabels(["Start Date", "End Date", "Width Proportion", "Magnification"])
        layout.addWidget(self.time_frames_table, 5, 0, 1, 2)

        add_tf_btn = QPushButton("Add Time Frame")
        remove_tf_btn = QPushButton("Remove Time Frame")
        add_tf_btn.clicked.connect(lambda: self.time_frames_table.insertRow(self.time_frames_table.rowCount()))
        remove_tf_btn.clicked.connect(lambda: self.time_frames_table.removeRow(self.time_frames_table.rowCount() - 1) if self.time_frames_table.rowCount() > 1 else None)
        layout.addWidget(add_tf_btn, 6, 0)
        layout.addWidget(remove_tf_btn, 6, 1)

        self.layout_tab.setLayout(layout)

    def _load_initial_data(self):
        """Populate tables with default or loaded data."""
        for table, data, tab_name in [
            (self.tasks_table, self.project_data.get_table_data("tasks"), "tasks")
        ]:
            table.setRowCount(len(data))
            for row_idx, row_data in enumerate(data):
                for col_idx, value in enumerate(row_data):
                    table.setItem(row_idx, col_idx, QTableWidgetItem(value))
        # Populate layout tab
        self.outer_width_input.setText(str(self.project_data.frame_config.outer_width))
        self.outer_height_input.setText(str(self.project_data.frame_config.outer_height))
        self.header_height_input.setText(str(self.project_data.frame_config.header_height))
        self.footer_height_input.setText(str(self.project_data.frame_config.footer_height))
        self.margins_input.setText(", ".join(map(str, self.project_data.frame_config.margins)))
        self.time_frames_table.setRowCount(len(self.project_data.time_frames))
        for i, tf in enumerate(self.project_data.time_frames):
            self.time_frames_table.setItem(i, 0, QTableWidgetItem(tf.start_date))
            self.time_frames_table.setItem(i, 1, QTableWidgetItem(tf.end_date))
            self.time_frames_table.setItem(i, 2, QTableWidgetItem(str(tf.width_proportion)))
            self.time_frames_table.setItem(i, 3, QTableWidgetItem(str(tf.magnification)))

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
        elif current_table == self.time_frames_table:
            current_table.setItem(current_rows, 0, QTableWidgetItem(today))
            current_table.setItem(current_rows, 1, QTableWidgetItem(today))
            current_table.setItem(current_rows, 2, QTableWidgetItem("0.5"))
            current_table.setItem(current_rows, 3, QTableWidgetItem("1.0"))
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
            # Update tasks
            self.project_data.update_from_table("tasks", self._extract_table_data(self.tasks_table))

            # Update frame_config
            margins = [float(x.strip()) for x in self.margins_input.text().split(",")]
            self.project_data.frame_config = FrameConfig(
                float(self.outer_width_input.text()), float(self.outer_height_input.text()),
                float(self.header_height_input.text()), float(self.footer_height_input.text()),
                (margins[0], margins[1], margins[2], margins[3])
            )

            # Update time_frames
            self.project_data.time_frames.clear()
            for row in range(self.time_frames_table.rowCount()):
                start = self.time_frames_table.item(row, 0).text() if self.time_frames_table.item(row, 0) else ""
                end = self.time_frames_table.item(row, 1).text() if self.time_frames_table.item(row, 1) else ""
                width_item = self.time_frames_table.item(row, 2)
                width = width_item.text().strip() if width_item else "0"  # Strip whitespace
                mag_item = self.time_frames_table.item(row, 3)
                mag = mag_item.text().strip() if mag_item else "1.0"  # Strip whitespace

                # Debug print to see what’s being passed
                print(f"Row {row}: width='{width}', mag='{mag}'")

                try:
                    width_float = float(width)
                except ValueError:
                    width_float = 0.0  # Fallback to 0.0 if conversion fails
                try:
                    mag_float = float(mag)
                except ValueError:
                    mag_float = 1.0  # Fallback to 1.0 if conversion fails

                self.project_data.add_time_frame(start, end, width_float, mag_float)

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