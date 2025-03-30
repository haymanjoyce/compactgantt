"""
Purpose: Defines DataEntryWindow, handles user input via tabs and UI interactions.
Why: Provides a clean interface for Gantt chart data entry, relying on ProjectData for logic.
"""

from PyQt5.QtWidgets import (QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
                             QFileDialog, QTabWidget, QAction, QApplication, QToolBar, QMessageBox,
                             QLineEdit, QLabel, QGridLayout, QPushButton, QCheckBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QDate
from data_model import ProjectData, FrameConfig
from config import Config
from datetime import datetime, timedelta
import json

class DataEntryWindow(QMainWindow):
    data_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project Planning Tool")
        self.setGeometry(100, 100, Config.DATA_ENTRY_WIDTH, Config.DATA_ENTRY_HEIGHT)
        self.project_data = ProjectData()

        # Menu bar
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("File")
        self.save_action = QAction("Save Project", self)
        self.save_action.triggered.connect(self.save_to_json)
        self.file_menu.addAction(self.save_action)
        self.load_action = QAction("Load Project", self)
        self.load_action.triggered.connect(self.load_from_json)
        self.file_menu.addAction(self.load_action)

        # Toolbar
        self.toolbar = QToolBar("Tools")
        self.addToolBar(self.toolbar)
        style = QApplication.style()
        self.generate_tool = QAction(QIcon(style.standardIcon(style.SP_ArrowRight)), "Generate Gantt Chart", self)
        self.generate_tool.triggered.connect(self._emit_data_updated)
        self.toolbar.addAction(self.generate_tool)

        # Central widget and tabs
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        # Layout tab
        self.layout_tab = QWidget()
        self.setup_layout_tab()
        self.tabs.addTab(self.layout_tab, "Layout")

        # Time Frames tab
        self.time_frames_tab = QWidget()
        self.setup_time_frames_tab()
        self.tabs.addTab(self.time_frames_tab, "Time Frames")

        # Tasks tab
        self.tasks_tab = QWidget()
        self.setup_tasks_tab()
        self.tabs.addTab(self.tasks_tab, "Tasks")

        # Connectors tab
        self.connectors_tab = QWidget()
        self.setup_connectors_tab()
        self.tabs.addTab(self.connectors_tab, "Connectors")

        # Swimlanes tab
        self.swimlanes_tab = QWidget()
        self.setup_swimlanes_tab()
        self.tabs.addTab(self.swimlanes_tab, "Swimlanes")

        # Pipes tab
        self.pipes_tab = QWidget()
        self.setup_pipes_tab()
        self.tabs.addTab(self.pipes_tab, "Pipes")

        # Curtains tab
        self.curtains_tab = QWidget()
        self.setup_curtains_tab()
        self.tabs.addTab(self.curtains_tab, "Curtains")

        # Text Boxes tab
        self.text_boxes_tab = QWidget()
        self.setup_text_boxes_tab()
        self.tabs.addTab(self.text_boxes_tab, "Text Boxes")

        self._load_initial_data()

    def setup_tasks_tab(self):
        tasks_layout = QVBoxLayout()
        self.tasks_table = QTableWidget(5, 5)
        self.tasks_table.setHorizontalHeaderLabels(["Task ID", "Task Name", "Start Date", "Finish Date", "Row Number"])
        tasks_layout.addWidget(self.tasks_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Task")
        remove_btn = QPushButton("Remove Task")
        add_btn.clicked.connect(self._add_task_row)
        remove_btn.clicked.connect(self._remove_task_row)
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        tasks_layout.addLayout(btn_layout)
        self.tasks_tab.setLayout(tasks_layout)

    def setup_layout_tab(self):
        layout = QGridLayout()
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
        layout.addWidget(QLabel("Top Margin:"), 4, 0)
        self.top_margin_input = QLineEdit(str(self.project_data.frame_config.margins[0]))
        layout.addWidget(self.top_margin_input, 4, 1)
        layout.addWidget(QLabel("Right Margin:"), 5, 0)
        self.right_margin_input = QLineEdit(str(self.project_data.frame_config.margins[1]))
        layout.addWidget(self.right_margin_input, 5, 1)
        layout.addWidget(QLabel("Bottom Margin:"), 6, 0)
        self.bottom_margin_input = QLineEdit(str(self.project_data.frame_config.margins[2]))
        layout.addWidget(self.bottom_margin_input, 6, 1)
        layout.addWidget(QLabel("Left Margin:"), 7, 0)
        self.left_margin_input = QLineEdit(str(self.project_data.frame_config.margins[3]))
        layout.addWidget(self.left_margin_input, 7, 1)
        layout.addWidget(QLabel("Header Text:"), 8, 0)
        self.header_text_input = QLineEdit(self.project_data.frame_config.header_text)
        layout.addWidget(self.header_text_input, 8, 1)
        layout.addWidget(QLabel("Footer Text:"), 9, 0)
        self.footer_text_input = QLineEdit(self.project_data.frame_config.footer_text)
        layout.addWidget(self.footer_text_input, 9, 1)
        layout.addWidget(QLabel("Upper Scale Height:"), 10, 0)
        self.upper_scale_height_input = QLineEdit(str(self.project_data.frame_config.upper_scale_height))
        layout.addWidget(self.upper_scale_height_input, 10, 1)
        layout.addWidget(QLabel("Lower Scale Height:"), 11, 0)
        self.lower_scale_height_input = QLineEdit(str(self.project_data.frame_config.lower_scale_height))
        layout.addWidget(self.lower_scale_height_input, 11, 1)
        layout.addWidget(QLabel("Number of Rows:"), 12, 0)
        self.num_rows_input = QLineEdit(str(self.project_data.frame_config.num_rows))
        layout.addWidget(self.num_rows_input, 12, 1)
        layout.addWidget(QLabel("Horizontal Gridlines:"), 13, 0)
        self.horizontal_gridlines_input = QCheckBox()
        self.horizontal_gridlines_input.setChecked(self.project_data.frame_config.horizontal_gridlines)
        layout.addWidget(self.horizontal_gridlines_input, 13, 1)
        layout.addWidget(QLabel("Vertical Gridlines:"), 14, 0)
        self.vertical_gridlines_input = QCheckBox()
        self.vertical_gridlines_input.setChecked(self.project_data.frame_config.vertical_gridlines)
        layout.addWidget(self.vertical_gridlines_input, 14, 1)
        self.layout_tab.setLayout(layout)

    def setup_time_frames_tab(self):
        tf_layout = QVBoxLayout()
        self.time_frames_table = QTableWidget(2, 5)
        self.time_frames_table.setHorizontalHeaderLabels(["Start Date", "Finish Date", "Width (%)",
                                                         "Upper Scale Intervals", "Lower Scale Intervals"])
        tf_layout.addWidget(self.time_frames_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Time Frame")
        remove_btn = QPushButton("Remove Time Frame")
        add_btn.clicked.connect(self._add_time_frame_row)
        remove_btn.clicked.connect(self._remove_time_frame_row)
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        tf_layout.addLayout(btn_layout)
        self.time_frames_tab.setLayout(tf_layout)

    def setup_connectors_tab(self):
        conn_layout = QVBoxLayout()
        self.connectors_table = QTableWidget(2, 2)
        self.connectors_table.setHorizontalHeaderLabels(["From Task ID", "To Task ID"])
        conn_layout.addWidget(self.connectors_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Connector")
        remove_btn = QPushButton("Remove Connector")
        add_btn.clicked.connect(self._add_connector_row)
        remove_btn.clicked.connect(self._remove_connector_row)
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        conn_layout.addLayout(btn_layout)
        self.connectors_tab.setLayout(conn_layout)

    def setup_swimlanes_tab(self):
        sl_layout = QVBoxLayout()
        self.swimlanes_table = QTableWidget(2, 4)
        self.swimlanes_table.setHorizontalHeaderLabels(["From Row Number", "To Row Number", "Title", "Colour"])
        sl_layout.addWidget(self.swimlanes_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Swimlane")
        remove_btn = QPushButton("Remove Swimlane")
        add_btn.clicked.connect(self._add_swimlane_row)
        remove_btn.clicked.connect(self._remove_swimlane_row)
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        sl_layout.addLayout(btn_layout)
        self.swimlanes_tab.setLayout(sl_layout)

    def setup_pipes_tab(self):
        pipes_layout = QVBoxLayout()
        self.pipes_table = QTableWidget(2, 2)
        self.pipes_table.setHorizontalHeaderLabels(["Date", "Colour"])
        pipes_layout.addWidget(self.pipes_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Pipe")
        remove_btn = QPushButton("Remove Pipe")
        add_btn.clicked.connect(self._add_pipe_row)
        remove_btn.clicked.connect(self._remove_pipe_row)
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        pipes_layout.addLayout(btn_layout)
        self.pipes_tab.setLayout(pipes_layout)

    def setup_curtains_tab(self):
        curtains_layout = QVBoxLayout()
        self.curtains_table = QTableWidget(2, 3)
        self.curtains_table.setHorizontalHeaderLabels(["From Date", "To Date", "Colour"])
        curtains_layout.addWidget(self.curtains_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Curtain")
        remove_btn = QPushButton("Remove Curtain")
        add_btn.clicked.connect(self._add_curtain_row)
        remove_btn.clicked.connect(self._remove_curtain_row)
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        curtains_layout.addLayout(btn_layout)
        self.curtains_tab.setLayout(curtains_layout)

    def setup_text_boxes_tab(self):
        tb_layout = QVBoxLayout()
        self.text_boxes_table = QTableWidget(2, 4)
        self.text_boxes_table.setHorizontalHeaderLabels(["Text", "X Coordinate", "Y Coordinate", "Colour"])
        tb_layout.addWidget(self.text_boxes_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Text Box")
        remove_btn = QPushButton("Remove Text Box")
        add_btn.clicked.connect(self._add_text_box_row)
        remove_btn.clicked.connect(self._remove_text_box_row)
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        tb_layout.addLayout(btn_layout)
        self.text_boxes_tab.setLayout(tb_layout)

    def _add_task_row(self):
        row_count = self.tasks_table.rowCount()
        self.tasks_table.insertRow(row_count)
        today = QDate.currentDate().toString("yyyy-MM-dd")
        self.tasks_table.setItem(row_count, 0, QTableWidgetItem(str(row_count + 1)))
        self.tasks_table.setItem(row_count, 1, QTableWidgetItem(f"Task {row_count + 1}"))
        self.tasks_table.setItem(row_count, 2, QTableWidgetItem(today))
        self.tasks_table.setItem(row_count, 3, QTableWidgetItem(today))
        self.tasks_table.setItem(row_count, 4, QTableWidgetItem("1"))
        self._sync_data()

    def _remove_task_row(self):
        if self.tasks_table.rowCount() > 1:
            self.tasks_table.removeRow(self.tasks_table.rowCount() - 1)
            self._sync_data()

    def _add_time_frame_row(self):
        row_count = self.time_frames_table.rowCount()
        self.time_frames_table.insertRow(row_count)
        today = QDate.currentDate().toString("yyyy-MM-dd")
        if row_count == 0:
            start_date = today
            end_date = (datetime.strptime(today, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")
        else:
            last_end = self.time_frames_table.item(row_count - 1, 1).text()
            start_date = (datetime.strptime(last_end, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")
        self.time_frames_table.setItem(row_count, 0, QTableWidgetItem(start_date))
        self.time_frames_table.setItem(row_count, 1, QTableWidgetItem(end_date))
        self.time_frames_table.setItem(row_count, 2, QTableWidgetItem(str(100 / (row_count + 1))))
        self.time_frames_table.setItem(row_count, 3, QTableWidgetItem("months"))
        self.time_frames_table.setItem(row_count, 4, QTableWidgetItem("weeks"))
        self._sync_data()

    def _remove_time_frame_row(self):
        if self.time_frames_table.rowCount() > 1:
            self.time_frames_table.removeRow(self.time_frames_table.rowCount() - 1)
            self._sync_data()

    def _add_connector_row(self):
        row_count = self.connectors_table.rowCount()
        self.connectors_table.insertRow(row_count)
        self.connectors_table.setItem(row_count, 0, QTableWidgetItem("1"))
        self.connectors_table.setItem(row_count, 1, QTableWidgetItem("2"))
        self._sync_data()

    def _remove_connector_row(self):
        if self.connectors_table.rowCount() > 1:
            self.connectors_table.removeRow(self.connectors_table.rowCount() - 1)
            self._sync_data()

    def _add_swimlane_row(self):
        row_count = self.swimlanes_table.rowCount()
        self.swimlanes_table.insertRow(row_count)
        self.swimlanes_table.setItem(row_count, 0, QTableWidgetItem("1"))
        self.swimlanes_table.setItem(row_count, 1, QTableWidgetItem("2"))
        self.swimlanes_table.setItem(row_count, 2, QTableWidgetItem(f"Swimlane {row_count + 1}"))
        self.swimlanes_table.setItem(row_count, 3, QTableWidgetItem("lightblue"))
        self._sync_data()

    def _remove_swimlane_row(self):
        if self.swimlanes_table.rowCount() > 1:
            self.swimlanes_table.removeRow(self.swimlanes_table.rowCount() - 1)
            self._sync_data()

    def _add_pipe_row(self):
        row_count = self.pipes_table.rowCount()
        self.pipes_table.insertRow(row_count)
        today = QDate.currentDate().toString("yyyy-MM-dd")
        self.pipes_table.setItem(row_count, 0, QTableWidgetItem(today))
        self.pipes_table.setItem(row_count, 1, QTableWidgetItem("red"))
        self._sync_data()

    def _remove_pipe_row(self):
        if self.pipes_table.rowCount() > 1:
            self.pipes_table.removeRow(self.pipes_table.rowCount() - 1)
            self._sync_data()

    def _add_curtain_row(self):
        row_count = self.curtains_table.rowCount()
        self.curtains_table.insertRow(row_count)
        today = QDate.currentDate().toString("yyyy-MM-dd")
        self.curtains_table.setItem(row_count, 0, QTableWidgetItem(today))
        self.curtains_table.setItem(row_count, 1, QTableWidgetItem(today))
        self.curtains_table.setItem(row_count, 2, QTableWidgetItem("gray"))
        self._sync_data()

    def _remove_curtain_row(self):
        if self.curtains_table.rowCount() > 1:
            self.curtains_table.removeRow(self.curtains_table.rowCount() - 1)
            self._sync_data()

    def _add_text_box_row(self):
        row_count = self.text_boxes_table.rowCount()
        self.text_boxes_table.insertRow(row_count)
        self.text_boxes_table.setItem(row_count, 0, QTableWidgetItem(f"Text {row_count + 1}"))
        self.text_boxes_table.setItem(row_count, 1, QTableWidgetItem("100"))
        self.text_boxes_table.setItem(row_count, 2, QTableWidgetItem("100"))
        self.text_boxes_table.setItem(row_count, 3, QTableWidgetItem("black"))
        self._sync_data()

    def _remove_text_box_row(self):
        if self.text_boxes_table.rowCount() > 1:
            self.text_boxes_table.removeRow(self.text_boxes_table.rowCount() - 1)
            self._sync_data()

    def _load_initial_data(self):
        # Tasks
        tasks_data = self.project_data.get_table_data("tasks")
        self.tasks_table.setRowCount(len(tasks_data))
        for row_idx, row_data in enumerate(tasks_data):
            for col_idx, value in enumerate(row_data):
                self.tasks_table.setItem(row_idx, col_idx, QTableWidgetItem(value))

        # Layout
        self.outer_width_input.setText(str(self.project_data.frame_config.outer_width))
        self.outer_height_input.setText(str(self.project_data.frame_config.outer_height))
        self.header_height_input.setText(str(self.project_data.frame_config.header_height))
        self.footer_height_input.setText(str(self.project_data.frame_config.footer_height))
        self.top_margin_input.setText(str(self.project_data.frame_config.margins[0]))
        self.right_margin_input.setText(str(self.project_data.frame_config.margins[1]))
        self.bottom_margin_input.setText(str(self.project_data.frame_config.margins[2]))
        self.left_margin_input.setText(str(self.project_data.frame_config.margins[3]))
        self.header_text_input.setText(self.project_data.frame_config.header_text)
        self.footer_text_input.setText(self.project_data.frame_config.footer_text)
        self.upper_scale_height_input.setText(str(self.project_data.frame_config.upper_scale_height))
        self.lower_scale_height_input.setText(str(self.project_data.frame_config.lower_scale_height))
        self.num_rows_input.setText(str(self.project_data.frame_config.num_rows))
        self.horizontal_gridlines_input.setChecked(self.project_data.frame_config.horizontal_gridlines)
        self.vertical_gridlines_input.setChecked(self.project_data.frame_config.vertical_gridlines)

        # Time Frames
        tf_data = self.project_data.get_table_data("time_frames")
        self.time_frames_table.setRowCount(len(tf_data) if tf_data else 1)
        if tf_data:
            for row_idx, row_data in enumerate(tf_data):
                for col_idx, value in enumerate(row_data):
                    self.time_frames_table.setItem(row_idx, col_idx, QTableWidgetItem(value))
        else:
            today = QDate.currentDate().toString("yyyy-MM-dd")
            self.time_frames_table.setItem(0, 0, QTableWidgetItem(today))
            self.time_frames_table.setItem(0, 1, QTableWidgetItem(today))
            self.time_frames_table.setItem(0, 2, QTableWidgetItem("100"))
            self.time_frames_table.setItem(0, 3, QTableWidgetItem("days"))
            self.time_frames_table.setItem(0, 4, QTableWidgetItem("weeks"))

        # Connectors
        conn_data = self.project_data.get_table_data("connectors")
        self.connectors_table.setRowCount(len(conn_data))
        for row_idx, row_data in enumerate(conn_data):
            for col_idx, value in enumerate(row_data):
                self.connectors_table.setItem(row_idx, col_idx, QTableWidgetItem(value))

        # Swimlanes
        sl_data = self.project_data.get_table_data("swimlanes")
        self.swimlanes_table.setRowCount(len(sl_data))
        for row_idx, row_data in enumerate(sl_data):
            for col_idx, value in enumerate(row_data):
                self.swimlanes_table.setItem(row_idx, col_idx, QTableWidgetItem(value))

        # Pipes
        pipes_data = self.project_data.get_table_data("pipes")
        self.pipes_table.setRowCount(len(pipes_data))
        for row_idx, row_data in enumerate(pipes_data):
            for col_idx, value in enumerate(row_data):
                self.pipes_table.setItem(row_idx, col_idx, QTableWidgetItem(value))

        # Curtains
        curtains_data = self.project_data.get_table_data("curtains")
        self.curtains_table.setRowCount(len(curtains_data))
        for row_idx, row_data in enumerate(curtains_data):
            for col_idx, value in enumerate(row_data):
                self.curtains_table.setItem(row_idx, col_idx, QTableWidgetItem(value))

        # Text Boxes
        tb_data = self.project_data.get_table_data("text_boxes")
        self.text_boxes_table.setRowCount(len(tb_data))
        for row_idx, row_data in enumerate(tb_data):
            for col_idx, value in enumerate(row_data):
                self.text_boxes_table.setItem(row_idx, col_idx, QTableWidgetItem(value))

    def _extract_table_data(self, table):
        data = []
        for row in range(table.rowCount()):
            row_data = []
            for col in range(table.columnCount()):
                item = table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data

    def _sync_data(self):
        try:
            # Sync Layout
            margins = (
                float(self.top_margin_input.text() or 0),
                float(self.right_margin_input.text() or 0),
                float(self.bottom_margin_input.text() or 0),
                float(self.left_margin_input.text() or 0)
            )
            self.project_data.frame_config = FrameConfig(
                float(self.outer_width_input.text() or 0),
                float(self.outer_height_input.text() or 0),
                float(self.header_height_input.text() or 0),
                float(self.footer_height_input.text() or 0),
                margins,
                int(self.num_rows_input.text() or 1),
                float(self.upper_scale_height_input.text() or 0),
                float(self.lower_scale_height_input.text() or 0),
                self.header_text_input.text(),
                self.footer_text_input.text(),
                self.horizontal_gridlines_input.isChecked(),
                self.vertical_gridlines_input.isChecked()
            )

            # Sync and validate Time Frames
            tf_data = self._extract_table_data(self.time_frames_table)
            if not tf_data:
                raise ValueError("At least one time frame is required")

            # Convert to datetime and sort by start date
            time_frames = []
            for row in tf_data:
                start = row[0] or "2025-01-01"
                end = row[1] or "2025-01-01"
                width = float(row[2] or 0) / 100
                upper = row[3] or "days"
                lower = row[4] or "days"
                start_dt = datetime.strptime(start, "%Y-%m-%d")
                end_dt = datetime.strptime(end, "%Y-%m-%d")
                if end_dt < start_dt:
                    raise ValueError(f"Time frame '{start}' to '{end}' has end date before start date")
                time_frames.append((start_dt, end_dt, width, upper, lower))
            time_frames.sort(key=lambda x: x[0])  # Sort by start date

            # Check for overlaps and continuity
            total_width = 0
            for i, (start_dt, end_dt, width, upper, lower) in enumerate(time_frames):
                total_width += width
                # Overlap check
                for j, (other_start, other_end, _, _, _) in enumerate(time_frames):
                    if i != j and not (end_dt < other_start or start_dt > other_end):
                        raise ValueError(f"Time frame '{start_dt.strftime('%Y-%m-%d')}' to '{end_dt.strftime('%Y-%m-%d')}' overlaps with another time frame")
                # Continuity check
                if i > 0:
                    prev_end = time_frames[i-1][1]
                    expected_start = prev_end + timedelta(days=1)
                    if start_dt != expected_start:
                        raise ValueError(f"Time frame '{start_dt.strftime('%Y-%m-%d')}' does not start immediately after previous end '{prev_end.strftime('%Y-%m-%d')}'")
            if total_width > 1.0:
                raise ValueError(f"Total time frame width ({total_width*100}%) exceeds 100%")

            # Add validated time frames
            self.project_data.time_frames.clear()
            for start_dt, end_dt, width, upper, lower in time_frames:
                self.project_data.add_time_frame(start_dt.strftime("%Y-%m-%d"), end_dt.strftime("%Y-%m-%d"),
                                                width, upper, lower)

            # Sync other tables
            self.project_data.update_from_table("tasks", self._extract_table_data(self.tasks_table))
            self.project_data.update_from_table("connectors", self._extract_table_data(self.connectors_table))
            self.project_data.update_from_table("swimlanes", self._extract_table_data(self.swimlanes_table))
            self.project_data.update_from_table("pipes", self._extract_table_data(self.pipes_table))
            self.project_data.update_from_table("curtains", self._extract_table_data(self.curtains_table))
            self.project_data.update_from_table("text_boxes", self._extract_table_data(self.text_boxes_table))

            self.data_updated.emit(self.project_data.to_json())
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))

    def _emit_data_updated(self):
        self._sync_data()
        print("Emitting data:", self.project_data.to_json())  # Debug

    def save_to_json(self):
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