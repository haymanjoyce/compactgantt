from PyQt5.QtWidgets import (QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
                             QFileDialog, QTabWidget, QAction, QApplication, QToolBar, QMessageBox,
                             QLineEdit, QLabel, QGridLayout, QPushButton, QCheckBox, QDateEdit, QComboBox,
                             QMenu, QGroupBox, QHeaderView, QScrollArea)
from PyQt5.QtGui import QIcon, QBrush
from PyQt5.QtCore import QDate, pyqtSignal, Qt
from data_model import ProjectData, FrameConfig
from config import Config
from datetime import datetime, timedelta
import json


class NumericTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        self_data = self.data(Qt.UserRole)
        other_data = other.data(Qt.UserRole)
        if self_data is not None and other_data is not None:
            try:
                return float(self_data) < float(other_data)
            except (TypeError, ValueError):
                pass
        return super().__lt__(other)


class DataEntryWindow(QMainWindow):
    data_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Project Planning Tool")
        self.setMinimumSize(600, 400)
        self.project_data = ProjectData()
        self._initializing = True

        # Table configurations for each tab
        self.table_configs = {
            "time_frames": {
                "columns": ["Finish Date", "Width (%)"],
                "defaults": lambda row: [
                    (QDate.currentDate().addDays(7 * (row + 1))).toString("yyyy-MM-dd"),
                    str(100 / (row + 2))
                ],
                "min_rows": 1
            },
            "tasks": {
                "columns": ["Task ID", "Task Order", "Task Name", "Start Date", "Finish Date", "Row Number",
                            "Label Placement", "Label Hide", "Label Alignment",
                            "Horiz Offset", "Vert Offset", "Label Colour"],
                "defaults": lambda task_id, task_order: [
                    str(task_id),  # Task ID
                    str(task_order),  # Task Order
                    "New Task",    # Task Name
                    QDate.currentDate().toString("yyyy-MM-dd"),  # Start Date
                    QDate.currentDate().toString("yyyy-MM-dd"),  # Finish Date
                    "1",  # Row Number
                    {"type": "combo", "items": ["Inside", "To left", "To right", "Above", "Below"], "default": "Inside"},
                    "No",  # Label Hide
                    {"type": "combo", "items": ["Left", "Centre", "Right"], "default": "Left"},
                    "1.0",  # Horiz Offset
                    "0.5",  # Vert Offset
                    "black"  # Label Colour
                ],
                "min_rows": 1
            },
            "connectors": {
                "columns": ["From Task ID", "To Task ID"],
                "defaults": lambda row: ["1", "2"],
                "min_rows": 0
            },
            "swimlanes": {
                "columns": ["From Row Number", "To Row Number", "Title", "Colour"],
                "defaults": lambda row: ["1", "2", f"Swimlane {row + 1}", "lightblue"],
                "min_rows": 0
            },
            "pipes": {
                "columns": ["Date", "Colour"],
                "defaults": lambda row: [QDate.currentDate().toString("yyyy-MM-dd"), "red"],
                "min_rows": 0
            },
            "curtains": {
                "columns": ["From Date", "To Date", "Colour"],
                "defaults": lambda row: [
                    QDate.currentDate().toString("yyyy-MM-dd"),
                    QDate.currentDate().toString("yyyy-MM-dd"),
                    "gray"
                ],
                "min_rows": 0
            },
            "text_boxes": {
                "columns": ["Text", "X Coordinate", "Y Coordinate", "Colour"],
                "defaults": lambda row: [f"Text {row + 1}", "100", "100", "black"],
                "min_rows": 0
            }
        }

        # Menu bar
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("File")
        self.save_action = QAction("Save Project", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_to_json)
        self.file_menu.addAction(self.save_action)
        self.load_action = QAction("Load Project", self)
        self.load_action.setShortcut("Ctrl+O")
        self.load_action.triggered.connect(self.load_from_json)
        self.file_menu.addAction(self.load_action)

        # Toolbar
        self.toolbar = QToolBar("Tools")
        self.addToolBar(self.toolbar)
        style = QApplication.style()
        self.generate_tool = QAction(QIcon(style.standardIcon(style.SP_ArrowRight)), "Generate Gantt Chart", self)
        self.generate_tool.setShortcut("Ctrl+G")
        self.generate_tool.triggered.connect(self._emit_data_updated)
        self.toolbar.addAction(self.generate_tool)

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        # Central widget and tabs
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.tabs = QTabWidget()
        self.layout.addWidget(self.tabs)

        self.layout_tab = QWidget()
        self.setup_layout_tab()
        self.tabs.addTab(self.layout_tab, "Layout")
        self.time_frames_tab = QWidget()
        self.setup_time_frames_tab()
        self.tabs.addTab(self.time_frames_tab, "Time Frames")
        self.tasks_tab = QWidget()
        self.setup_tasks_tab()
        self.tabs.addTab(self.tasks_tab, "Tasks")
        self.connectors_tab = QWidget()
        self.setup_connectors_tab()
        self.tabs.addTab(self.connectors_tab, "Connectors")
        self.swimlanes_tab = QWidget()
        self.setup_swimlanes_tab()
        self.tabs.addTab(self.swimlanes_tab, "Swimlanes")
        self.pipes_tab = QWidget()
        self.setup_pipes_tab()
        self.tabs.addTab(self.pipes_tab, "Pipes")
        self.curtains_tab = QWidget()
        self.setup_curtains_tab()
        self.tabs.addTab(self.curtains_tab, "Curtains")
        self.text_boxes_tab = QWidget()
        self.setup_text_boxes_tab()
        self.tabs.addTab(self.text_boxes_tab, "Text Boxes")

        self._load_initial_data()
        self._initializing = False

    def setup_layout_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        # Dimensions group
        dim_group = QGroupBox("Dimensions")
        dim_layout = QGridLayout()
        dim_layout.addWidget(QLabel("Outer Width:"), 0, 0)
        self.outer_width_input = QLineEdit(str(self.project_data.frame_config.outer_width))
        dim_layout.addWidget(self.outer_width_input, 0, 1)
        dim_layout.addWidget(QLabel("Outer Height:"), 1, 0)
        self.outer_height_input = QLineEdit(str(self.project_data.frame_config.outer_height))
        dim_layout.addWidget(self.outer_height_input, 1, 1)
        dim_layout.addWidget(QLabel("Header Height:"), 2, 0)
        self.header_height_input = QLineEdit(str(self.project_data.frame_config.header_height))
        dim_layout.addWidget(self.header_height_input, 2, 1)
        dim_layout.addWidget(QLabel("Footer Height:"), 3, 0)
        self.footer_height_input = QLineEdit(str(self.project_data.frame_config.footer_height))
        dim_layout.addWidget(self.footer_height_input, 3, 1)
        dim_group.setLayout(dim_layout)
        layout.addWidget(dim_group)

        # Margins group
        margins_group = QGroupBox("Margins")
        margins_layout = QGridLayout()
        margins_layout.addWidget(QLabel("Top:"), 0, 0)
        self.top_margin_input = QLineEdit(str(self.project_data.frame_config.margins[0]))
        margins_layout.addWidget(self.top_margin_input, 0, 1)
        margins_layout.addWidget(QLabel("Right:"), 1, 0)
        self.right_margin_input = QLineEdit(str(self.project_data.frame_config.margins[1]))
        margins_layout.addWidget(self.right_margin_input, 1, 1)
        margins_layout.addWidget(QLabel("Bottom:"), 2, 0)
        self.bottom_margin_input = QLineEdit(str(self.project_data.frame_config.margins[2]))
        margins_layout.addWidget(self.bottom_margin_input, 2, 1)
        margins_layout.addWidget(QLabel("Left:"), 3, 0)
        self.left_margin_input = QLineEdit(str(self.project_data.frame_config.margins[3]))
        margins_layout.addWidget(self.left_margin_input, 3, 1)
        margins_group.setLayout(margins_layout)
        layout.addWidget(margins_group)

        # Text group
        text_group = QGroupBox("Text")
        text_layout = QGridLayout()
        text_layout.addWidget(QLabel("Header Text:"), 0, 0)
        self.header_text_input = QLineEdit(self.project_data.frame_config.header_text)
        text_layout.addWidget(self.header_text_input, 0, 1)
        text_layout.addWidget(QLabel("Footer Text:"), 1, 0)
        self.footer_text_input = QLineEdit(self.project_data.frame_config.footer_text)
        text_layout.addWidget(self.footer_text_input, 1, 1)
        text_group.setLayout(text_layout)
        layout.addWidget(text_group)

        # Gridlines group
        grid_group = QGroupBox("Gridlines")
        grid_layout = QGridLayout()
        grid_layout.addWidget(QLabel("Horizontal:"), 0, 0)
        self.horizontal_gridlines_input = QCheckBox()
        self.horizontal_gridlines_input.setChecked(self.project_data.frame_config.horizontal_gridlines)
        grid_layout.addWidget(self.horizontal_gridlines_input, 0, 1)
        grid_layout.addWidget(QLabel("Vertical:"), 1, 0)
        self.vertical_gridlines_input = QCheckBox()
        self.vertical_gridlines_input.setChecked(self.project_data.frame_config.vertical_gridlines)
        grid_layout.addWidget(self.vertical_gridlines_input, 1, 1)
        grid_group.setLayout(grid_layout)
        layout.addWidget(grid_group)

        # Setup group
        setup_group = QGroupBox("Setup")
        setup_layout = QGridLayout()
        setup_layout.addWidget(QLabel("Chart Start Date:"), 0, 0)
        self.chart_start_date_input = QDateEdit()
        self.chart_start_date_input.setCalendarPopup(True)
        self.chart_start_date_input.setDisplayFormat("yyyy-MM-dd")
        self.chart_start_date_input.setDate(
            QDate.fromString(self.project_data.frame_config.chart_start_date, "yyyy-MM-dd"))
        setup_layout.addWidget(self.chart_start_date_input, 0, 1)
        setup_layout.addWidget(QLabel("Number of Rows:"), 1, 0)
        self.num_rows_input = QLineEdit(str(self.project_data.frame_config.num_rows))
        setup_layout.addWidget(self.num_rows_input, 1, 1)
        setup_group.setLayout(setup_layout)
        layout.addWidget(setup_group)

        layout.addStretch()
        scroll.setWidget(content_widget)
        scroll_layout = QVBoxLayout()
        scroll_layout.addWidget(scroll)
        self.layout_tab.setLayout(scroll_layout)

    def setup_time_frames_tab(self):
        tf_layout = QVBoxLayout()
        self.time_frames_table = QTableWidget(2, 2)
        self.time_frames_table.setHorizontalHeaderLabels(self.table_configs["time_frames"]["columns"])
        self.time_frames_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.time_frames_table.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(pos, self.time_frames_table, "time_frames"))
        self.time_frames_table.setSortingEnabled(True)
        self.time_frames_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.time_frames_table.resizeColumnsToContents()
        tf_layout.addWidget(self.time_frames_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Time Frame")
        remove_btn = QPushButton("Remove Time Frame")
        add_btn.clicked.connect(lambda: self._add_row(self.time_frames_table, "time_frames"))
        remove_btn.clicked.connect(lambda: self._remove_row(self.time_frames_table, "time_frames"))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        tf_layout.addLayout(btn_layout)
        self.time_frames_tab.setLayout(tf_layout)
        self.time_frames_table.itemChanged.connect(self._sync_data_if_not_initializing)

    def setup_tasks_tab(self):
        tasks_layout = QVBoxLayout()
        self.tasks_table = QTableWidget(5, 12)  # +1 for Task Order
        self.tasks_table.setHorizontalHeaderLabels(self.table_configs["tasks"]["columns"])
        self.tasks_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tasks_table.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(pos, self.tasks_table, "tasks"))
        self.tasks_table.setSortingEnabled(True)
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tasks_table.setColumnWidth(0, 80)   # Task ID
        self.tasks_table.setColumnWidth(1, 80)   # Task Order
        self.tasks_table.setColumnWidth(2, 150)  # Task Name
        self.tasks_table.setColumnWidth(6, 120)  # Label Placement
        self.tasks_table.setColumnWidth(8, 100)  # Label Alignment
        self.tasks_table.setColumnWidth(9, 80)   # Horiz Offset
        self.tasks_table.setColumnWidth(10, 80)  # Vert Offset
        tasks_layout.addWidget(self.tasks_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Task")
        remove_btn = QPushButton("Remove Task")
        add_btn.clicked.connect(lambda: self._add_row(self.tasks_table, "tasks"))
        remove_btn.clicked.connect(lambda: self._remove_row(self.tasks_table, "tasks"))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        tasks_layout.addLayout(btn_layout)
        self.tasks_tab.setLayout(tasks_layout)
        self.tasks_table.itemChanged.connect(self._sync_data_if_not_initializing)
        # Default sort by Task Order (column 1)
        self.tasks_table.sortByColumn(1, Qt.AscendingOrder)

    def setup_connectors_tab(self):
        conn_layout = QVBoxLayout()
        self.connectors_table = QTableWidget(2, 2)
        self.connectors_table.setHorizontalHeaderLabels(self.table_configs["connectors"]["columns"])
        self.connectors_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.connectors_table.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(pos, self.connectors_table, "connectors"))
        self.connectors_table.setSortingEnabled(True)
        self.connectors_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.connectors_table.resizeColumnsToContents()
        conn_layout.addWidget(self.connectors_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Connector")
        remove_btn = QPushButton("Remove Connector")
        add_btn.clicked.connect(lambda: self._add_row(self.connectors_table, "connectors"))
        remove_btn.clicked.connect(lambda: self._remove_row(self.connectors_table, "connectors"))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        conn_layout.addLayout(btn_layout)
        self.connectors_tab.setLayout(conn_layout)
        self.connectors_table.itemChanged.connect(self._sync_data_if_not_initializing)

    def setup_swimlanes_tab(self):
        sl_layout = QVBoxLayout()
        self.swimlanes_table = QTableWidget(2, 4)
        self.swimlanes_table.setHorizontalHeaderLabels(self.table_configs["swimlanes"]["columns"])
        self.swimlanes_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.swimlanes_table.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(pos, self.swimlanes_table, "swimlanes"))
        self.swimlanes_table.setSortingEnabled(True)
        self.swimlanes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.swimlanes_table.resizeColumnsToContents()
        sl_layout.addWidget(self.swimlanes_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Swimlane")
        remove_btn = QPushButton("Remove Swimlane")
        add_btn.clicked.connect(lambda: self._add_row(self.swimlanes_table, "swimlanes"))
        remove_btn.clicked.connect(lambda: self._remove_row(self.swimlanes_table, "swimlanes"))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        sl_layout.addLayout(btn_layout)
        self.swimlanes_tab.setLayout(sl_layout)
        self.swimlanes_table.itemChanged.connect(self._sync_data_if_not_initializing)

    def setup_pipes_tab(self):
        pipes_layout = QVBoxLayout()
        self.pipes_table = QTableWidget(2, 2)
        self.pipes_table.setHorizontalHeaderLabels(self.table_configs["pipes"]["columns"])
        self.pipes_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.pipes_table.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(pos, self.pipes_table, "pipes"))
        self.time_frames_table.setSortingEnabled(True)
        self.pipes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.pipes_table.resizeColumnsToContents()
        pipes_layout.addWidget(self.pipes_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Pipe")
        remove_btn = QPushButton("Remove Pipe")
        add_btn.clicked.connect(lambda: self._add_row(self.pipes_table, "pipes"))
        remove_btn.clicked.connect(lambda: self._remove_row(self.pipes_table, "pipes"))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        pipes_layout.addLayout(btn_layout)
        self.pipes_tab.setLayout(pipes_layout)
        self.pipes_table.itemChanged.connect(self._sync_data_if_not_initializing)

    def setup_curtains_tab(self):
        curtains_layout = QVBoxLayout()
        self.curtains_table = QTableWidget(2, 3)
        self.curtains_table.setHorizontalHeaderLabels(self.table_configs["curtains"]["columns"])
        self.curtains_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.curtains_table.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(pos, self.curtains_table, "curtains"))
        self.curtains_table.setSortingEnabled(True)
        self.curtains_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.curtains_table.resizeColumnsToContents()
        curtains_layout.addWidget(self.curtains_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Curtain")
        remove_btn = QPushButton("Remove Curtain")
        add_btn.clicked.connect(lambda: self._add_row(self.curtains_table, "curtains"))
        remove_btn.clicked.connect(lambda: self._remove_row(self.curtains_table, "curtains"))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        curtains_layout.addLayout(btn_layout)
        self.curtains_tab.setLayout(curtains_layout)
        self.curtains_table.itemChanged.connect(self._sync_data_if_not_initializing)

    def setup_text_boxes_tab(self):
        tb_layout = QVBoxLayout()
        self.text_boxes_table = QTableWidget(2, 4)
        self.text_boxes_table.setHorizontalHeaderLabels(self.table_configs["text_boxes"]["columns"])
        self.text_boxes_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.text_boxes_table.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(pos, self.text_boxes_table, "text_boxes"))
        self.text_boxes_table.setSortingEnabled(True)
        self.text_boxes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.text_boxes_table.resizeColumnsToContents()
        tb_layout.addWidget(self.text_boxes_table)
        btn_layout = QGridLayout()
        add_btn = QPushButton("Add Text Box")
        remove_btn = QPushButton("Remove Text Box")
        add_btn.clicked.connect(lambda: self._add_row(self.text_boxes_table, "text_boxes"))
        remove_btn.clicked.connect(lambda: self._remove_row(self.text_boxes_table, "text_boxes"))
        btn_layout.addWidget(add_btn, 0, 0)
        btn_layout.addWidget(remove_btn, 0, 1)
        tb_layout.addLayout(btn_layout)
        self.text_boxes_tab.setLayout(tb_layout)
        self.text_boxes_table.itemChanged.connect(self._sync_data_if_not_initializing)

    def _add_row(self, table, config_key):
        config = self.table_configs.get(config_key, {})
        row_count = table.rowCount()
        # Disable sorting and signals to prevent reordering or premature sync
        was_sorting = table.isSortingEnabled()
        table.setSortingEnabled(False)
        table.blockSignals(True)
        print(f"Adding row to {config_key}, row_count={row_count}, sorting={was_sorting}")  # Debug
        table.insertRow(row_count)
        if config_key == "tasks":
            # Compute next task_id
            max_task_id = 0
            for row in range(row_count):
                item = table.item(row, 0)
                if item and item.text().isdigit():
                    max_task_id = max(max_task_id, int(item.text()))
            task_id = max_task_id + 1
            # Compute task_order (max + 1)
            max_task_order = 0
            for row in range(row_count):
                item = table.item(row, 1)
                try:
                    max_task_order = max(max_task_order, float(item.text()) if item and item.text() else 0)
                except ValueError:
                    pass
            task_order = max_task_order + 1
            defaults = config.get("defaults", lambda x, y: [])(task_id, task_order)
            print(f"Adding task ID={task_id}, Task Order={task_order}, defaults={defaults}")  # Debug
        else:
            defaults = config.get("defaults", lambda x: [])(row_count)
        # Set all cells
        for col, default in enumerate(defaults):
            if isinstance(default, dict) and default.get("type") == "combo":
                combo = QComboBox()
                combo.addItems(default["items"])
                combo.setCurrentText(default["default"])
                table.setCellWidget(row_count, col, combo)
            else:
                if config_key == "tasks" and col in (0, 1):  # Task ID, Task Order
                    item = NumericTableWidgetItem(str(default))
                else:
                    item = QTableWidgetItem(str(default))
                if config_key == "tasks" and col == 0:  # Make Task ID read-only
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setData(Qt.UserRole, int(default))  # Numeric for Task ID sorting
                elif config_key == "tasks" and col == 1:  # Task Order numeric
                    item.setData(Qt.UserRole, float(default))  # Numeric for Task Order sorting
                table.setItem(row_count, col, item)
        # Renumber Task Orders to integers
        if config_key == "tasks":
            self._renumber_task_orders(table)
        # Re-enable signals and sorting, then sync
        table.blockSignals(False)
        table.setSortingEnabled(was_sorting)
        table.sortByColumn(1, Qt.AscendingOrder)  # Sort by Task Order
        table.itemChanged.connect(self._sync_data_if_not_initializing)
        print(f"Added row, new row_count={table.rowCount()}, sorting={table.isSortingEnabled()}")  # Debug
        self._sync_data_if_not_initializing()

    def _remove_row(self, table, config_key):
        config = self.table_configs.get(config_key, {})
        min_rows = config.get("min_rows", 1)
        if table.rowCount() > min_rows:
            table.removeRow(table.rowCount() - 1)
            if config_key == "tasks":
                self._renumber_task_orders(table)
            self._sync_data_if_not_initializing()

    def _show_context_menu(self, pos, table, config_key):
        menu = QMenu()
        insert_action = QAction("Insert Row Above", self)
        delete_action = QAction("Delete Row", self)
        row_index = table.indexAt(pos).row()  # 0-based index (Row 1 = 0, Row 8 = 7)
        if row_index < 0 or row_index >= table.rowCount():  # Clicked outside rows
            row_index = 0  # Insert at top (Row 1)
        insert_action.triggered.connect(lambda: self._insert_row(table, config_key, row_index))
        delete_action.triggered.connect(lambda: self._delete_row(table, config_key, row_index))
        menu.addAction(insert_action)
        menu.addAction(delete_action)
        menu.exec_(table.viewport().mapToGlobal(pos))

    def _insert_row(self, table, config_key, row_index):
        config = self.table_configs.get(config_key, {})
        was_sorting = table.isSortingEnabled()
        table.setSortingEnabled(False)
        table.blockSignals(True)
        print(f"Inserting above row {row_index + 1}, config_key={config_key}")
        table.insertRow(row_index)
        if config_key == "tasks":
            # Compute next task_id
            max_task_id = 0
            for row in range(table.rowCount()):
                if row != row_index:
                    item = table.item(row, 0)
                    if item and item.text().isdigit():
                        max_task_id = max(max_task_id, int(item.text()))
            task_id = max_task_id + 1
            # Compute task_order (interpolate between prev and current)
            prev_order = 0
            curr_order = float('inf')
            if row_index > 0:
                prev_item = table.item(row_index - 1, 1)
                prev_order = float(prev_item.text()) if prev_item and prev_item.text() else row_index
            if row_index < table.rowCount() - 1:
                curr_item = table.item(row_index + 1, 1)
                curr_order = float(curr_item.text()) if curr_item and curr_item.text() else row_index + 1
            task_order = (prev_order + curr_order) / 2 if curr_order != float('inf') else prev_order + 1
            defaults = config.get("defaults", lambda x, y: [])(task_id, task_order)
            print(f"Inserting task ID={task_id}, Task Order={task_order}, defaults={defaults}")
        else:
            defaults = config.get("defaults", lambda x: [])(table.rowCount())
        for col, default in enumerate(defaults):
            if isinstance(default, dict) and default.get("type") == "combo":
                combo = QComboBox()
                combo.addItems(default["items"])
                combo.setCurrentText(default["default"])
                table.setCellWidget(row_index, col, combo)
            else:
                if config_key == "tasks" and col in (0, 1):  # Task ID, Task Order
                    item = NumericTableWidgetItem(str(default))
                else:
                    item = QTableWidgetItem(str(default))
                if config_key == "tasks" and col == 0:  # Make Task ID read-only
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setData(Qt.UserRole, int(default))  # Numeric for Task ID sorting
                elif config_key == "tasks" and col == 1:  # Task Order numeric
                    item.setData(Qt.UserRole, float(default))  # Numeric for Task Order sorting
                table.setItem(row_index, col, item)
        # Renumber Task Orders to integers
        if config_key == "tasks":
            self._renumber_task_orders(table)
        table.blockSignals(False)
        table.sortByColumn(1, Qt.AscendingOrder)  # Sort by Task Order
        table.setSortingEnabled(was_sorting)
        table.itemChanged.connect(self._sync_data_if_not_initializing)
        print(f"Inserted row, new row_count={table.rowCount()}, sorting={table.isSortingEnabled()}")  # Debug
        self._sync_data_if_not_initializing()

    def _delete_row(self, table, config_key, row_index):
        config = self.table_configs.get(config_key, {})
        min_rows = config.get("min_rows", 1)
        if table.rowCount() > min_rows:
            was_sorting = table.isSortingEnabled()
            table.setSortingEnabled(False)
            table.removeRow(row_index)
            if config_key == "tasks":
                self._renumber_task_orders(table)
            table.setSortingEnabled(was_sorting)
            self._sync_data_if_not_initializing()

    def _renumber_task_orders(self, table):
        # Collect tasks with their current Task Order
        tasks = []
        for row in range(table.rowCount()):
            task_id_item = table.item(row, 0)
            task_order_item = table.item(row, 1)
            try:
                task_order = float(task_order_item.text()) if task_order_item and task_order_item.text() else row + 1
            except ValueError:
                task_order = row + 1
            tasks.append((row, task_order))
        # Sort by Task Order
        tasks.sort(key=lambda x: x[1])
        # Renumber to sequential integers starting from 1
        table.blockSignals(True)
        for i, (row, _) in enumerate(tasks, 1):
            item = NumericTableWidgetItem(str(i))
            item.setData(Qt.UserRole, float(i))
            table.setItem(row, 1, item)
        table.blockSignals(False)
        print(f"Renumbered Task Orders: {[table.item(row, 1).text() for row in range(table.rowCount())]}")  # Debug

    def _sync_data(self):
        try:
          # Validate Layout tab
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
                self.header_text_input.text(),
                self.footer_text_input.text(),
                self.horizontal_gridlines_input.isChecked(),
                self.vertical_gridlines_input.isChecked(),
                self.chart_start_date_input.date().toString("yyyy-MM-dd")
            )

            # Validate Time Frames
            tf_data = self._extract_table_data(self.time_frames_table)
            if not tf_data:
                raise ValueError("At least one time frame is required")
            time_frames = []
            chart_start = datetime.strptime(self.project_data.frame_config.chart_start_date, "%Y-%m-%d")
            prev_end = chart_start
            for i, row in enumerate(tf_data):
                end = row[0] or "2025-01-01"
                width = float(row[1] or 0) / 100
                end_dt = datetime.strptime(end, "%Y-%m-%d")
                if end_dt < prev_end:
                    raise ValueError(
                        f"Time frame {i + 1} finish date '{end}' is before previous end '{prev_end.strftime('%Y-%m-%d')}'")
                time_frames.append((prev_end, end_dt, width))
                prev_end = end_dt + timedelta(days=1)
            self.project_data.time_frames.clear()
            for _, end_dt, width in time_frames:
                self.project_data.add_time_frame(end_dt.strftime("%Y-%m-%d"), width)

            # Validate Tasks and apply highlights/tooltips
            tasks_data = self._extract_table_data(self.tasks_table)
            # Debug: Log sort order if Task ID or Task Order column is sorted
            sort_col = self.tasks_table.horizontalHeader().sortIndicatorSection()
            sort_order = self.tasks_table.horizontalHeader().sortIndicatorOrder()
            if sort_col == 0:
                print(f"Task ID sorted: {'Ascending' if sort_order == Qt.AscendingOrder else 'Descending'}, data={tasks_data}")
            elif sort_col == 1:
                print(f"Task Order sorted: {'Ascending' if sort_order == Qt.AscendingOrder else 'Descending'}, data={tasks_data}")

            # Track invalid cells with reasons for tooltips
            invalid_cells = set()  # (row, col, reason)

            # Validate Task Order
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
            for k in non_unique_orders:
                for row_idx, row in enumerate(tasks_data):
                    try:
                        if float(row[1] or 0) == k:
                            invalid_cells.add((row_idx, 1, "non-unique"))
                    except ValueError:
                        pass
            print(f"Non-unique Task Orders: {non_unique_orders}")  # Debug

            # Validate dates and row numbers
            has_errors = False
            for row_idx, row in enumerate(tasks_data):
                task_id = int(row[0] or 0)
                start_date_raw = row[3] or ""
                finish_date_raw = row[4] or ""

                # Date validation
                if not start_date_raw and not finish_date_raw:
                    invalid_cells.add((row_idx, 3, "both-empty"))
                    invalid_cells.add((row_idx, 4, "both-empty"))
                    has_errors = True
                else:
                    start_valid = True
                    finish_valid = True
                    start_dt = None
                    finish_dt = None
                    if start_date_raw:
                        try:
                            start_dt = datetime.strptime(start_date_raw, "%Y-%m-%d")
                        except ValueError:
                            invalid_cells.add((row_idx, 3, "invalid format"))
                            start_valid = False
                            has_errors = True
                    if finish_date_raw:
                        try:
                            finish_dt = datetime.strptime(finish_date_raw, "%Y-%m-%d")
                        except ValueError:
                            invalid_cells.add((row_idx, 4, "invalid format"))
                            finish_valid = False
                            has_errors = True
                    if start_valid and finish_valid and start_dt and finish_dt and start_dt > finish_dt:
                        invalid_cells.add((row_idx, 3, "start-after-finish"))
                        invalid_cells.add((row_idx, 4, "start-after-finish"))
                        has_errors = True

                # Row Number validation
                try:
                    row_number = float(row[5] or 1)
                    if row_number <= 0:
                        invalid_cells.add((row_idx, 5, "non-positive"))
                        has_errors = True
                    elif row_number != int(row_number):
                        invalid_cells.add((row_idx, 5, "non-integer"))
                        has_errors = True
                    elif row_number > self.project_data.frame_config.num_rows:
                        invalid_cells.add((row_idx, 5, "exceeds-num-rows"))
                        has_errors = True
                except ValueError:
                    invalid_cells.add((row_idx, 5, "invalid"))
                    has_errors = True

            # Validate Connectors
            connectors_data = self._extract_table_data(self.connectors_table)
            invalid_connector_cells = set()  # (row, col, reason)
            task_ids = {int(row[0]) for row in tasks_data if row[0].isdigit()}  # Valid Task IDs
            connector_pairs = set()  # Track From -> To pairs for duplicates

            for row_idx, row in enumerate(connectors_data):
                from_id, to_id = row[0], row[1]

                # From Task ID (col 0)
                try:
                    from_id_val = int(from_id) if from_id else 0
                    if from_id_val <= 0:
                        invalid_connector_cells.add((row_idx, 0, "non-positive"))
                    elif from_id_val not in task_ids:
                        invalid_connector_cells.add((row_idx, 0, "invalid-task"))
                    elif from_id_val == int(to_id or 0):
                        invalid_connector_cells.add((row_idx, 0, "self-reference"))
                except ValueError:
                    invalid_connector_cells.add((row_idx, 0, "invalid"))

                # To Task ID (col 1)
                try:
                    to_id_val = int(to_id) if to_id else 0
                    if to_id_val <= 0:
                        invalid_connector_cells.add((row_idx, 1, "non-positive"))
                    elif to_id_val not in task_ids:
                        invalid_connector_cells.add((row_idx, 1, "invalid-task"))
                    elif to_id_val == int(from_id or 0):
                        invalid_connector_cells.add((row_idx, 1, "self-reference"))
                except ValueError:
                    invalid_connector_cells.add((row_idx, 1, "invalid"))

                # Check for duplicate connectors
                if from_id and to_id and (from_id, to_id) in connector_pairs:
                    invalid_connector_cells.add((row_idx, 0, "duplicate"))
                    invalid_connector_cells.add((row_idx, 1, "duplicate"))
                else:
                    connector_pairs.add((from_id, to_id))

            # Apply highlights and tooltips for Connectors
            self.connectors_table.blockSignals(True)
            for row_idx in range(self.connectors_table.rowCount()):
                for col in (0, 1):
                    item = self.connectors_table.item(row_idx, col)
                    tooltip = ""
                    if item:
                        if any((row_idx, col, reason) in invalid_connector_cells for reason in ["non-positive"]):
                            item.setBackground(QBrush(Qt.yellow))
                            tooltip = f"Connector {row_idx + 1}: {'From' if col == 0 else 'To'} Task ID must be positive"
                        elif any((row_idx, col, reason) in invalid_connector_cells for reason in ["invalid"]):
                            item.setBackground(QBrush(Qt.yellow))
                            tooltip = f"Connector {row_idx + 1}: {'From' if col == 0 else 'To'} Task ID must be an integer"
                        elif any((row_idx, col, reason) in invalid_connector_cells for reason in ["invalid-task"]):
                            item.setBackground(QBrush(Qt.yellow))
                            tooltip = f"Connector {row_idx + 1}: {'From' if col == 0 else 'To'} Task ID does not exist"
                        elif any((row_idx, col, reason) in invalid_connector_cells for reason in ["self-reference"]):
                            item.setBackground(QBrush(Qt.yellow))
                            tooltip = f"Connector {row_idx + 1}: From and To Task IDs cannot be the same"
                        elif any((row_idx, col, reason) in invalid_connector_cells for reason in ["duplicate"]):
                            item.setBackground(QBrush(Qt.yellow))
                            tooltip = f"Connector {row_idx + 1}: Duplicate connector"
                        else:
                            item.setBackground(QBrush())
                    else:
                        item = QTableWidgetItem("")
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Connector {row_idx + 1}: {'From' if col == 0 else 'To'} Task ID required"
                        self.connectors_table.setItem(row_idx, col, item)
                    item.setToolTip(tooltip)
            self.connectors_table.blockSignals(False)

            # Prevent SVG generation if connector errors exist
            if invalid_connector_cells:
                has_errors = True

            # Apply highlights and tooltips for Tasks
            self.tasks_table.blockSignals(True)
            for row_idx in range(self.tasks_table.rowCount()):
                task_id = self.tasks_table.item(row_idx, 0).text() if self.tasks_table.item(row_idx,
                                                                                            0) else "Unknown"

                # Task Order (col 1)
                item = self.tasks_table.item(row_idx, 1)
                tooltip = ""
                if item:
                    try:
                        task_order = float(item.text() or 0)
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
                    self.tasks_table.setItem(row_idx, 1, item)
                item.setToolTip(tooltip)

                # Start Date (col 3)
                item = self.tasks_table.item(row_idx, 3)
                tooltip = ""
                if item:
                    if any((row_idx, 3, reason) in invalid_cells for reason in ["invalid format"]):
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Task {task_id}: Start Date must be yyyy-MM-dd"
                    elif any((row_idx, 3, reason) in invalid_cells for reason in ["start-after-finish"]):
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Task {task_id}: Start Date cannot be after Finish Date"
                    elif any((row_idx, 3, reason) in invalid_cells for reason in ["both-empty"]):
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Task {task_id}: Start or Finish Date required"
                    else:
                        item.setBackground(QBrush())
                else:
                    item = QTableWidgetItem("")
                    if any((row_idx, 3, reason) in invalid_cells for reason in ["both-empty"]):
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Task {task_id}: Start or Finish Date required"
                    self.tasks_table.setItem(row_idx, 3, item)
                item.setToolTip(tooltip)

                # Finish Date (col 4)
                item = self.tasks_table.item(row_idx, 4)
                tooltip = ""
                if item:
                    if any((row_idx, 4, reason) in invalid_cells for reason in ["invalid format"]):
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Task {task_id}: Finish Date must be yyyy-MM-dd"
                    elif any((row_idx, 4, reason) in invalid_cells for reason in ["start-after-finish"]):
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Task {task_id}: Finish Date cannot be before Start Date"
                    elif any((row_idx, 4, reason) in invalid_cells for reason in ["both-empty"]):
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Task {task_id}: Start or Finish Date required"
                    else:
                        item.setBackground(QBrush())
                else:
                    item = QTableWidgetItem("")
                    if any((row_idx, 4, reason) in invalid_cells for reason in ["both-empty"]):
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Task {task_id}: Start or Finish Date required"
                    self.tasks_table.setItem(row_idx, 4, item)
                item.setToolTip(tooltip)

                # Row Number (col 5)
                item = self.tasks_table.item(row_idx, 5)
                tooltip = ""
                if item:
                    if any((row_idx, 5, reason) in invalid_cells for reason in ["non-positive"]):
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Task {task_id}: Row Number must be positive"
                    elif any((row_idx, 5, reason) in invalid_cells for reason in ["non-integer", "invalid"]):
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Task {task_id}: Row Number must be an integer"
                    elif any((row_idx, 5, reason) in invalid_cells for reason in ["exceeds-num-rows"]):
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Task {task_id}: Row Number cannot exceed {self.project_data.frame_config.num_rows}"
                    else:
                        item.setBackground(QBrush())
                else:
                    item = QTableWidgetItem("1")
                    if any((row_idx, 5, reason) in invalid_cells for reason in
                           ["non-positive", "non-integer", "invalid", "exceeds-num-rows"]):
                        item.setBackground(QBrush(Qt.yellow))
                        tooltip = f"Task {task_id}: Row Number must be a positive integer"
                    self.tasks_table.setItem(row_idx, 5, item)
                item.setToolTip(tooltip)

            self.tasks_table.blockSignals(False)
            print(f"Highlighted cells: {list(invalid_cells)}")  # Debug

            # Process tasks only if no errors
            if has_errors:
                self.status_bar.showMessage("Fix highlighted cells to generate chart")
                self.data_updated.emit({})  # Signal empty data to prevent Gantt chart generation
                return

            self.project_data.tasks.clear()
            for row in tasks_data:
                task_id = int(row[0] or 0)
                task_order = float(row[1] or 0)
                task_name = row[2] or "Unnamed"
                start_date_raw = row[3] or QDate.currentDate().toString("yyyy-MM-dd")
                finish_date_raw = row[4] or QDate.currentDate().toString("yyyy-MM-dd")
                row_number = int(row[5] or 1)
                label_placement = row[6] or "Inside"
                label_hide = row[7] or "No"
                label_alignment = row[8] or "Left"
                label_horizontal_offset = float(row[9] or 1.0)
                label_vertical_offset = float(row[10] or 0.5)
                label_text_colour = row[11] or "black"

                is_milestone = bool(start_date_raw) != bool(finish_date_raw)
                start_date_json = start_date_raw
                finish_date_json = finish_date_raw
                render_start = start_date_raw if start_date_raw else finish_date_raw
                render_finish = finish_date_raw if finish_date_raw else start_date_raw

                self.project_data.add_task(task_id, task_name, render_start, render_finish, row_number, is_milestone,
                                          label_placement, label_hide, label_alignment,
                                          label_horizontal_offset, label_vertical_offset, label_text_colour)
                self.project_data.tasks[-1].start_date = start_date_json
                self.project_data.tasks[-1].finish_date = finish_date_json

            self.project_data.update_from_table("connectors", self._extract_table_data(self.connectors_table))
            self.project_data.update_from_table("swimlanes", self._extract_table_data(self.swimlanes_table))
            self.project_data.update_from_table("pipes", self._extract_table_data(self.pipes_table))
            self.project_data.update_from_table("curtains", self._extract_table_data(self.curtains_table))
            self.project_data.update_from_table("text_boxes", self._extract_table_data(self.text_boxes_table))

            self.status_bar.showMessage("Chart data ready")
            self.data_updated.emit(self.project_data.to_json())

        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
            self.data_updated.emit({})  # Ensure no crash

    def _load_initial_data(self):
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
        self.num_rows_input.setText(str(self.project_data.frame_config.num_rows))
        self.horizontal_gridlines_input.setChecked(self.project_data.frame_config.horizontal_gridlines)
        self.vertical_gridlines_input.setChecked(self.project_data.frame_config.vertical_gridlines)
        self.chart_start_date_input.setDate(QDate.fromString(self.project_data.frame_config.chart_start_date, "yyyy-MM-dd"))

        tf_data = self.project_data.get_table_data("time_frames")
        self.time_frames_table.setRowCount(len(tf_data) if tf_data else 1)
        if tf_data:
            for row_idx, row_data in enumerate(tf_data):
                for col_idx, value in enumerate(row_data):
                    self.time_frames_table.setItem(row_idx, col_idx, QTableWidgetItem(value))
        else:
            today = QDate.currentDate().toString("yyyy-MM-dd")
            self.time_frames_table.setItem(0, 0, QTableWidgetItem(today))
            self.time_frames_table.setItem(0, 1, QTableWidgetItem("100"))

        tasks_data = self.project_data.get_table_data("tasks")
        self.tasks_table.setRowCount(len(tasks_data))
        for row_idx, task in enumerate(tasks_data):
            task_id = task[0] if task[0] else str(row_idx + 1)
            item = NumericTableWidgetItem(task_id)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setData(Qt.UserRole, int(task_id))
            self.tasks_table.setItem(row_idx, 0, item)
            # Task Order: Use row index + 1 if not present (for old data)
            task_order = str(row_idx + 1) if len(task) <= 1 or not task[1] else task[1]
            item = NumericTableWidgetItem(task_order)
            item.setData(Qt.UserRole, float(task_order))
            self.tasks_table.setItem(row_idx, 1, item)
            self.tasks_table.setItem(row_idx, 2, QTableWidgetItem(task[1] if len(task) > 1 else ""))  # task_name
            self.tasks_table.setItem(row_idx, 3, QTableWidgetItem(task[2] if len(task) > 2 else ""))  # start_date
            self.tasks_table.setItem(row_idx, 4, QTableWidgetItem(task[3] if len(task) > 3 else ""))  # finish_date
            self.tasks_table.setItem(row_idx, 5, QTableWidgetItem(task[4] if len(task) > 4 else ""))  # row_number
            combo_placement = QComboBox()
            combo_placement.addItems(["Inside", "To left", "To right", "Above", "Below"])
            combo_placement.setCurrentText(task[5] if len(task) > 5 else "Inside")
            self.tasks_table.setCellWidget(row_idx, 6, combo_placement)
            self.tasks_table.setItem(row_idx, 7, QTableWidgetItem(task[6] if len(task) > 6 else ""))  # label_hide
            combo_alignment = QComboBox()
            combo_alignment.addItems(["Left", "Centre", "Right"])
            combo_alignment.setCurrentText(task[7] if len(task) > 7 else "Left")
            self.tasks_table.setCellWidget(row_idx, 8, combo_alignment)
            self.tasks_table.setItem(row_idx, 9, QTableWidgetItem(task[8] if len(task) > 8 else ""))  # label_horizontal_offset
            self.tasks_table.setItem(row_idx, 10, QTableWidgetItem(task[9] if len(task) > 9 else ""))  # label_vertical_offset
            self.tasks_table.setItem(row_idx, 11, QTableWidgetItem(task[10] if len(task) > 10 else ""))  # label_text_colour
        # Renumber Task Orders for loaded data
        self._renumber_task_orders(self.tasks_table)
        self.tasks_table.sortByColumn(1, Qt.AscendingOrder)

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            self._sync_data()

    def save_to_json(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "JSON Files (*.json)")
        if file_path:
            try:
                self._sync_data()
                json_str = json.dumps(self.project_data.to_json(), indent=4)
                with open(file_path, "w") as jsonfile:
                    jsonfile.write(json_str)
                QMessageBox.information(self, "Success", "Project saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving JSON: {e}")

    def load_from_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "r") as jsonfile:
                    data = json.load(jsonfile)
                self._initializing = True
                self.project_data = ProjectData.from_json(data)
                self._load_initial_data()
                self._initializing = False
                self.data_updated.emit(self.project_data.to_json())
                QMessageBox.information(self, "Success", "Project loaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading JSON: {e}")

    def _emit_data_updated(self):
        self._sync_data()

    def _extract_table_data(self, table):
        data = []
        for row in range(table.rowCount()):
            row_data = []
            for col in range(table.columnCount()):
                widget = table.cellWidget(row, col)
                if widget and isinstance(widget, QComboBox):
                    row_data.append(widget.currentText())
                else:
                    item = table.item(row, col)
                    row_data.append(item.text() if item else "")
            data.append(row_data)
        return data