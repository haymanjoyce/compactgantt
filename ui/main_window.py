from PyQt5.QtWidgets import QMainWindow, QTabWidget, QAction, QFileDialog, QMessageBox, QWidget, QPushButton, QVBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QDate
import logging
import os
from config.app_config import AppConfig
from .tabs.layout_tab import LayoutTab
from .tabs.tasks_tab import TasksTab
from .tabs.placeholder_tab import PlaceholderTab
from .tabs.links_tab import LinksTab
from .tabs.pipes_tab import PipesTab
from .tabs.curtains_tab import CurtainsTab
from repositories.project_repository import ProjectRepository
from repositories.excel_repository import ExcelRepository
from models.project import ProjectData  # Import here to avoid circular import
from ui.window_utils import move_window_according_to_preferences
from .tabs.windows_tab import WindowsTab
from .tabs.titles_tab import TitlesTab
from .tabs.timeline_tab import TimelineTab
from .tabs.swimlanes_tab import SwimlanesTab
from .tabs.text_boxes_tab import TextBoxesTab
from .tabs.typography_tab import TypographyTab

class MainWindow(QMainWindow):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, svg_display=None, app_config=None):
        super().__init__()
        self.setWindowTitle("Compact Gantt | Chart Data Window")
        # Use ICO so Windows title bar matches taskbar icon
        self.setWindowIcon(QIcon("assets/favicon.ico"))
        self.setMinimumSize(600, 700)
        self.project_data = project_data  # Use passed project_data instance
        self.app_config = app_config if app_config else AppConfig()  # Use passed instance or create new
        self.repository = ProjectRepository()
        self.excel_repository = ExcelRepository()
        self.svg_display = svg_display  # Reference to SVG display window
        self.resize(self.app_config.general.data_entry_width, self.app_config.general.data_entry_height)
        move_window_according_to_preferences(
            self,
            self.app_config,
            width=self.app_config.general.data_entry_width,
            height=self.app_config.general.data_entry_height
        )
        self.setup_ui()

    def resizeEvent(self, event):
        """Handle window resize events - save new dimensions to config."""
        super().resizeEvent(event)
        # Update config with new window dimensions
        self.app_config.general.window.data_entry_width = self.width()
        self.app_config.general.window.data_entry_height = self.height()
        # Save settings to persist across sessions
        self.app_config.save_settings()

    def setup_ui(self):
        # Create menu bar
        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu("File")
        self.save_action = QAction("Save Project (JSON)", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.save_to_json)
        file_menu.addAction(self.save_action)
        
        self.save_excel_action = QAction("Save Project (Excel)", self)
        self.save_excel_action.triggered.connect(self.save_to_excel)
        file_menu.addAction(self.save_excel_action)
        
        file_menu.addSeparator()
        
        self.load_action = QAction("Load Project (JSON)", self)
        self.load_action.setShortcut("Ctrl+O")
        self.load_action.triggered.connect(self.load_from_json)
        file_menu.addAction(self.load_action)
        
        self.load_excel_action = QAction("Load Project (Excel)", self)
        self.load_excel_action.triggered.connect(self.load_from_excel)
        file_menu.addAction(self.load_excel_action)

        # Create central widget to hold everything
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Create and setup tab widget
        self.tab_widget = QTabWidget()
        self._create_all_tabs()
        self._add_all_tabs()
        main_layout.addWidget(self.tab_widget)

        # Create Update Image button at the bottom
        self.update_image_button = QPushButton("Update Chart")
        self.update_image_button.setStyleSheet("""
            QPushButton {
                padding: 8px;
            }
        """)
        self.update_image_button.clicked.connect(self._emit_data_updated)
        main_layout.addWidget(self.update_image_button)

        self.setCentralWidget(central_widget)
        # Create and style the status bar to match SVG display
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                border-top: 1px solid #D3D3D3;
                padding: 3px;
                background: #F8F9FA;
            }
        """)
        self.status_bar.showMessage("Ready")

    def _create_all_tabs(self):
        self.windows_tab = WindowsTab(self.project_data, self.app_config)
        self.windows_tab.data_updated.connect(self._on_windows_updated)
        self.layout_tab = LayoutTab(self.project_data, self.app_config)
        self.titles_tab = TitlesTab(self.project_data, self.app_config)
        self.timeline_tab = TimelineTab(self.project_data, self.app_config)
        self.tasks_tab = TasksTab(self.project_data, self.app_config)
        self.tasks_tab.data_updated.connect(self._on_data_updated)
        self.links_tab = LinksTab(self.project_data, self.app_config)
        self.links_tab.data_updated.connect(self._on_data_updated)
        self.swimlanes_tab = SwimlanesTab(self.project_data, self.app_config)
        self.pipes_tab = PipesTab(self.project_data, self.app_config)
        self.curtains_tab = CurtainsTab(self.project_data, self.app_config)
        self.text_boxes_tab = TextBoxesTab(self.project_data, self.app_config)
        self.typography_tab = TypographyTab(self.project_data, self.app_config)

    def _add_all_tabs(self):
        self.tab_widget.addTab(self.windows_tab, "Windows")
        self.tab_widget.addTab(self.layout_tab, "Layout")
        self.tab_widget.addTab(self.titles_tab, "Titles")
        self.tab_widget.addTab(self.timeline_tab, "Timeline")
        self.tab_widget.addTab(self.tasks_tab, "Tasks")
        self.tab_widget.addTab(self.links_tab, "Links")
        self.tab_widget.addTab(self.swimlanes_tab, "Swimlanes")
        self.tab_widget.addTab(self.pipes_tab, "Pipes")
        self.tab_widget.addTab(self.curtains_tab, "Curtains")
        self.tab_widget.addTab(self.text_boxes_tab, "Text Boxes")
        self.tab_widget.addTab(self.typography_tab, "Typography")

    def save_to_json(self):
        # Use last directory if available, otherwise use empty string (current directory)
        directory = self.app_config.general.window.last_json_directory if self.app_config.general.window.last_json_directory else ""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Project", directory, "JSON Files (*.json)")
        if file_path:
            try:
                self.repository.save(file_path, self.project_data)
                # Update last directory from the saved file path
                self.app_config.general.window.last_json_directory = os.path.dirname(file_path)
                self.app_config.save_settings()
                QMessageBox.information(self, "Success", "Project saved successfully!")
                self.status_bar.showMessage("Project saved successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving JSON: {e}")
                self.status_bar.showMessage("Error saving project")

    def load_from_json(self):
        # Use last directory if available, otherwise use empty string (current directory)
        directory = self.app_config.general.window.last_json_directory if self.app_config.general.window.last_json_directory else ""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Project", directory, "JSON Files (*.json)")
        if file_path:
            try:
                loaded_project = self.repository.load(file_path, ProjectData)
                self.project_data = loaded_project  # Use the loaded instance

                # Update last directory from the loaded file path
                self.app_config.general.window.last_json_directory = os.path.dirname(file_path)
                self.app_config.save_settings()

                # Re-create all tabs with the new project_data
                self._create_all_tabs()
                self.tab_widget.clear()
                self._add_all_tabs()

                self.data_updated.emit(self.project_data.to_json())
                QMessageBox.information(self, "Success", "Project loaded successfully!")
                self.status_bar.showMessage("Project loaded successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading JSON: {e}")
                self.status_bar.showMessage("Error loading project")

    def save_to_excel(self):
        # Use last directory if available, otherwise use empty string (current directory)
        directory = self.app_config.general.window.last_excel_directory if self.app_config.general.window.last_excel_directory else ""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Project as Excel", directory, "Excel Files (*.xlsx)")
        if file_path:
            try:
                # Ensure file has .xlsx extension
                if not file_path.endswith('.xlsx'):
                    file_path += '.xlsx'
                
                # Sync all tabs before saving
                self._sync_all_tabs()
                
                self.excel_repository.save(file_path, self.project_data)
                # Update last directory from the saved file path
                self.app_config.general.window.last_excel_directory = os.path.dirname(file_path)
                self.app_config.save_settings()
                QMessageBox.information(self, "Success", "Project saved to Excel successfully!")
                self.status_bar.showMessage("Project saved to Excel successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error saving Excel: {e}")
                self.status_bar.showMessage("Error saving project to Excel")
                logging.error(f"Error saving to Excel: {e}", exc_info=True)

    def load_from_excel(self):
        # Use last directory if available, otherwise use empty string (current directory)
        directory = self.app_config.general.window.last_excel_directory if self.app_config.general.window.last_excel_directory else ""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Project from Excel", directory, "Excel Files (*.xlsx)")
        if file_path:
            try:
                loaded_project = self.excel_repository.load(file_path, ProjectData)
                self.project_data = loaded_project  # Use the loaded instance

                # Update last directory from the loaded file path
                self.app_config.general.window.last_excel_directory = os.path.dirname(file_path)
                self.app_config.save_settings()

                # Re-create all tabs with the new project_data
                self._create_all_tabs()
                self.tab_widget.clear()
                self._add_all_tabs()

                self.data_updated.emit(self.project_data.to_json())
                QMessageBox.information(self, "Success", "Project loaded from Excel successfully!")
                self.status_bar.showMessage("Project loaded from Excel successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading Excel: {e}")
                self.status_bar.showMessage("Error loading project from Excel")
                logging.error(f"Error loading from Excel: {e}", exc_info=True)

    def _sync_all_tabs(self):
        """Sync all tabs to ensure project_data is up to date."""
        try:
            if hasattr(self.layout_tab, '_sync_data'):
                self.layout_tab._sync_data()
            if hasattr(self.titles_tab, '_sync_data'):
                self.titles_tab._sync_data()
            if hasattr(self.timeline_tab, '_sync_data'):
                self.timeline_tab._sync_data()
            if hasattr(self.tasks_tab, '_sync_data'):
                self.tasks_tab._sync_data()
            if hasattr(self.links_tab, '_sync_data'):
                self.links_tab._sync_data()
            if hasattr(self.swimlanes_tab, '_sync_data'):
                self.swimlanes_tab._sync_data()
            if hasattr(self.pipes_tab, '_sync_data'):
                self.pipes_tab._sync_data()
            if hasattr(self.curtains_tab, '_sync_data'):
                self.curtains_tab._sync_data()
            if hasattr(self.text_boxes_tab, '_sync_data'):
                self.text_boxes_tab._sync_data()
            if hasattr(self.typography_tab, '_sync_data'):
                self.typography_tab._sync_data()
        except Exception as e:
            logging.error(f"Error syncing tab data: {e}", exc_info=True)
            # Continue anyway - emit with whatever data we have

    def _emit_data_updated(self):
        """Only called when Update Image button is clicked"""
        # Sync all tabs to ensure project_data is up to date
        self._sync_all_tabs()
        
        self.data_updated.emit(self.project_data.to_json())

    def _on_data_updated(self, data):
        """Handle updates from tabs that trigger chart refresh."""
        # The emitting tab already synced its data; just emit to refresh the chart
        self.data_updated.emit(self.project_data.to_json())

    def _on_windows_updated(self, data):
        """Handle updates from windows tab"""
        # Reposition data entry window if positioning preferences changed
        if any(key in data for key in ['data_entry_screen', 'data_entry_x', 'data_entry_y']):
            move_window_according_to_preferences(
                self,
                self.app_config,
                width=self.app_config.general.data_entry_width,
                height=self.app_config.general.data_entry_height
            )
        
        # Reposition SVG display window if positioning preferences changed
        if any(key in data for key in ['svg_display_screen', 'svg_display_x', 'svg_display_y']):
            if self.svg_display:
                move_window_according_to_preferences(
                    self.svg_display,
                    self.app_config,
                    width=self.app_config.general.svg_display_width,
                    height=self.app_config.general.svg_display_height,
                    window_type="svg_display"
                )

