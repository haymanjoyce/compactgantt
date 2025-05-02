from PyQt5.QtWidgets import QMainWindow, QTabWidget, QToolBar, QAction, QFileDialog, QMessageBox, QWidget, QSizePolicy, QPushButton, QVBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QDate, QObject
from config.app_config import AppConfig
from models import FrameConfig, TimeFrame, Task
from .tabs.layout_tab import LayoutTab
from .tabs.tasks_tab import TasksTab
from .tabs.time_frames_tab import TimeFramesTab
from .tabs.placeholder_tab import PlaceholderTab
from repositories.project_repository import JsonProjectRepository
from models.project import ProjectData  # Import here to avoid circular import
import json

class DataEntryWindow(QMainWindow):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data):
        super().__init__()
        self.setWindowTitle("Compact Gantt")
        self.setWindowIcon(QIcon("assets/logo.png"))  # Add window icon
        self.setMinimumSize(600, 400)
        self.project_data = project_data  # Use passed project_data instance
        self.app_config = AppConfig()  # Initialize centralized config
        self.repository = JsonProjectRepository()  # Add this line
        self.setup_ui()
        # No longer connecting signals for automatic updates

    def setup_ui(self):
        # Create menu bar
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

        # Create central widget to hold everything
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Create and setup tab widget
        self.tab_widget = QTabWidget()
        self.layout_tab = LayoutTab(self.project_data, self.app_config)
        self.time_frames_tab = TimeFramesTab(self.project_data, self.app_config)
        self.tasks_tab = TasksTab(self.project_data, self.app_config)
        
        # Create placeholder tabs
        self.connectors_tab = PlaceholderTab(self.project_data, self.app_config, "Connectors")
        self.swimlanes_tab = PlaceholderTab(self.project_data, self.app_config, "Swimlanes")
        self.pipes_tab = PlaceholderTab(self.project_data, self.app_config, "Pipes")
        self.curtains_tab = PlaceholderTab(self.project_data, self.app_config, "Curtains")
        self.text_boxes_tab = PlaceholderTab(self.project_data, self.app_config, "Text Boxes")
        
        self.tab_widget.addTab(self.layout_tab, "Layout")
        self.tab_widget.addTab(self.time_frames_tab, "Time Frames")
        self.tab_widget.addTab(self.tasks_tab, "Tasks")
        self.tab_widget.addTab(self.connectors_tab, "Connectors")
        self.tab_widget.addTab(self.swimlanes_tab, "Swimlanes")
        self.tab_widget.addTab(self.pipes_tab, "Pipes")
        self.tab_widget.addTab(self.curtains_tab, "Curtains")
        self.tab_widget.addTab(self.text_boxes_tab, "Text Boxes")
        
        main_layout.addWidget(self.tab_widget)

        # Create Update Image button at the bottom
        self.update_image_button = QPushButton("Update Image")
        self.update_image_button.setStyleSheet("""
            QPushButton {
                padding: 8px;
            }
        """)
        self.update_image_button.clicked.connect(self._emit_data_updated)
        main_layout.addWidget(self.update_image_button)

        self.setCentralWidget(central_widget)
        # Create and style the status bar
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                border-top: 1px solid #D3D3D3;
                padding: 3px;
                background: #F8F9FA;
            }
        """)
        self.status_bar.showMessage("Ready")

    def save_to_json(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Project", "", "JSON Files (*.json)")
        if file_path:
            try:
                self.repository.save(file_path, self.project_data)
                QMessageBox.information(self, "Success", "Project saved successfully!")
                self.status_bar.showMessage("Project saved successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving JSON: {e}")
                self.status_bar.showMessage("Error saving project")

    def load_from_json(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Project", "", "JSON Files (*.json)")
        if file_path:
            try:
                loaded_project = self.repository.load(file_path, ProjectData)
                self.project_data.__dict__.update(loaded_project.__dict__)
                # Only reload data for implemented tabs
                for tab in [self.time_frames_tab, self.layout_tab, self.tasks_tab]:
                    tab._load_initial_data()
                self.data_updated.emit(self.project_data.to_json())
                QMessageBox.information(self, "Success", "Project loaded successfully!")
                self.status_bar.showMessage("Project loaded successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading JSON: {e}")
                self.status_bar.showMessage("Error loading project")

    def _emit_data_updated(self):
        """Only called when Update Image button is clicked"""
        self.data_updated.emit(self.project_data.to_json())