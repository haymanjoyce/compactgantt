from PyQt5.QtWidgets import QMainWindow, QTabWidget, QToolBar, QAction, QFileDialog, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QDate
from data_model import ProjectData
from app_config import AppConfig
from data_model import FrameConfig
from .tabs.layout_tab import LayoutTab
from .tabs.tasks_tab import TasksTab
from .tabs.time_frames_tab import TimeFramesTab
from .tabs.connectors_tab import ConnectorsTab
from .tabs.swimlanes_tab import SwimlanesTab
from .tabs.pipes_tab import PipesTab
from .tabs.curtains_tab import CurtainsTab
from .tabs.text_boxes_tab import TextBoxesTab
import json

class DataEntryWindow(QMainWindow):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data):
        super().__init__()
        self.setWindowTitle("Project Planning Tool")
        self.setMinimumSize(600, 400)
        self.project_data = project_data  # Use passed project_data instance
        self.app_config = AppConfig()  # Initialize centralized config
        self.setup_ui()
        self._connect_signals()

    def setup_ui(self):
        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu("File")
        self.save_action = QAction("Save Project", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_to_json)
        file_menu.addAction(self.save_action)
        self.load_action = QAction("Load Project", self)
        self.load_action.setShortcut("Ctrl+O")
        self.load_action.triggered.connect(self.load_from_json)
        file_menu.addAction(self.load_action)

        self.toolbar = QToolBar("Tools")
        self.addToolBar(self.toolbar)
        style = self.style()
        self.generate_tool = QAction(QIcon(style.standardIcon(style.SP_ArrowRight)), "Generate Gantt Chart", self)
        self.generate_tool.setShortcut("Ctrl+G")
        self.generate_tool.triggered.connect(self._emit_data_updated)
        self.toolbar.addAction(self.generate_tool)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        self.tab_widget = QTabWidget()
        self.layout_tab = LayoutTab(self.project_data, self.app_config)
        self.time_frames_tab = TimeFramesTab(self.project_data, self.app_config)
        self.tasks_tab = TasksTab(self.project_data, self.app_config)
        self.connectors_tab = ConnectorsTab(self.project_data, self.app_config)
        self.swimlanes_tab = SwimlanesTab(self.project_data, self.app_config)
        self.pipes_tab = PipesTab(self.project_data, self.app_config)
        self.curtains_tab = CurtainsTab(self.project_data, self.app_config)
        self.text_boxes_tab = TextBoxesTab(self.project_data, self.app_config)
        self.tab_widget.addTab(self.layout_tab, "Layout")
        self.tab_widget.addTab(self.time_frames_tab, "Time Frames")
        self.tab_widget.addTab(self.tasks_tab, "Tasks")
        self.tab_widget.addTab(self.connectors_tab, "Connectors")
        self.tab_widget.addTab(self.swimlanes_tab, "Swimlanes")
        self.tab_widget.addTab(self.pipes_tab, "Pipes")
        self.tab_widget.addTab(self.curtains_tab, "Curtains")
        self.tab_widget.addTab(self.text_boxes_tab, "Text Boxes")
        self.setCentralWidget(self.tab_widget)

    def _connect_signals(self):
        for tab in [self.layout_tab, self.time_frames_tab, self.tasks_tab, self.connectors_tab,
                    self.swimlanes_tab, self.pipes_tab, self.curtains_tab, self.text_boxes_tab]:
            tab.data_updated.connect(self.data_updated.emit)

    def save_to_json(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "JSON Files (*.json)")
        if file_path:
            try:
                json_str = json.dumps(self.project_data.to_json(), indent=4)
                with open(file_path, "w") as jsonfile:
                    jsonfile.write(json_str)
                QMessageBox.information(self, "Success", "Project saved successfully!")
                self.status_bar.showMessage("Project saved successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving JSON: {e}")
                self.status_bar.showMessage("Error saving project")

    def load_from_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "JSON Files (*.json)")
        if file_path:
            try:
                with open(file_path, "r") as jsonfile:
                    data = json.load(jsonfile)
                self.project_data.__init__()  # Reset existing project_data
                self.project_data.frame_config = FrameConfig(**data.get("frame_config", {}))
                self.project_data.time_frames = data.get("time_frames", [])
                for task in data.get("tasks", []):
                    self.project_data.add_task(
                        task["task_id"], task["task_name"], task["start_date"],
                        task["finish_date"], task["row_number"], task.get("is_milestone", False),
                        task.get("label_placement", "Inside"), task.get("label_hide", "No"),
                        task.get("label_alignment", "Left"), task.get("label_horizontal_offset", 1.0),
                        task.get("label_vertical_offset", 0.5), task.get("label_text_colour", "black"),
                        task.get("task_order", float(len(self.project_data.tasks) + 1))
                    )
                self.project_data.connectors = data.get("connectors", [])
                self.project_data.swimlanes = data.get("swimlanes", [])
                self.project_data.pipes = data.get("pipes", [])
                self.project_data.curtains = data.get("curtains", [])
                self.project_data.text_boxes = data.get("text_boxes", [])
                for tab in [self.time_frames_tab, self.layout_tab, self.tasks_tab, self.connectors_tab,
                            self.swimlanes_tab, self.pipes_tab, self.curtains_tab, self.text_boxes_tab]:
                    tab._load_initial_data()
                self.data_updated.emit(self.project_data.to_json())
                QMessageBox.information(self, "Success", "Project loaded successfully!")
                self.status_bar.showMessage("Project loaded successfully")  # User feedback
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading JSON: {e}")
                self.status_bar.showMessage("Error loading project")

    def _emit_data_updated(self):
        self.data_updated.emit(self.project_data.to_json())