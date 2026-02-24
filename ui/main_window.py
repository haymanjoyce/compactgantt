from PyQt5.QtWidgets import QMainWindow, QTabWidget, QFileDialog, QMessageBox, QWidget, QPushButton, QVBoxLayout, QHBoxLayout
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
from repositories.excel_repository import ExcelRepository
from models.project import ProjectData  # Import here to avoid circular import
from ui.window_utils import move_window_according_to_preferences
from .tabs.preferences_tab import PreferencesTab
from .tabs.titles_tab import TitlesTab
from .tabs.timeline_tab import TimelineTab
from .tabs.swimlanes_tab import SwimlanesTab
from .tabs.notes_tab import NotesTab
from .tabs.typography_tab import TypographyTab

class MainWindow(QMainWindow):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, svg_display=None, app_config=None):
        super().__init__()
        self.setWindowTitle("Compact Gantt | Chart Data Window")
        # Use ICO so Windows title bar matches taskbar icon
        from pathlib import Path
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "favicon.ico"
        self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(600, 700)
        self.project_data = project_data  # Use passed project_data instance
        self.app_config = app_config if app_config else AppConfig()  # Use passed instance or create new
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
        # Create central widget to hold everything
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Top toolbar: project file actions
        self.open_btn = QPushButton("Open Project")
        self.save_btn = QPushButton("Save Project")
        self.open_btn.setShortcut("Ctrl+O")
        self.save_btn.setShortcut("Ctrl+S")
        self.open_btn.setToolTip("Open project from Excel (Ctrl+O)")
        self.save_btn.setToolTip("Save project to Excel (Ctrl+S)")
        self.open_btn.clicked.connect(self.load_from_excel)
        self.save_btn.clicked.connect(self.save_to_excel)
        btn_style = "QPushButton { padding: 8px; }"
        self.open_btn.setStyleSheet(btn_style)
        self.save_btn.setStyleSheet(btn_style)

        file_toolbar = QHBoxLayout()
        file_toolbar.setSpacing(8)
        file_toolbar.setContentsMargins(0, 0, 0, 4)
        file_toolbar.addWidget(self.open_btn)
        file_toolbar.addWidget(self.save_btn)
        file_toolbar.addStretch()
        main_layout.addLayout(file_toolbar)

        # Create and setup tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setMovable(True)  # Enable drag-and-drop tab reordering
        # Connect to tab moved signal to save order when user reorders tabs
        self.tab_widget.tabBar().tabMoved.connect(self._on_tab_moved)
        self._create_all_tabs()
        self._add_all_tabs()
        # Temporarily block signals during restore to avoid triggering save
        self.tab_widget.tabBar().blockSignals(True)
        self._restore_tab_order()  # Restore saved tab order
        self.tab_widget.tabBar().blockSignals(False)
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
        self.preferences_tab = PreferencesTab(self.project_data, self.app_config)
        self.preferences_tab.data_updated.connect(self._on_preferences_updated)
        self.layout_tab = LayoutTab(self.project_data, self.app_config)
        self.titles_tab = TitlesTab(self.project_data, self.app_config)
        self.timeline_tab = TimelineTab(self.project_data, self.app_config)
        self.tasks_tab = TasksTab(self.project_data, self.app_config)
        self.tasks_tab.data_updated.connect(self._on_data_updated)
        self.links_tab = LinksTab(self.project_data, self.app_config)
        self.links_tab.data_updated.connect(self._on_data_updated)
        self.swimlanes_tab = SwimlanesTab(self.project_data, self.app_config)
        self.swimlanes_tab.data_updated.connect(self._on_swimlanes_updated)
        self.pipes_tab = PipesTab(self.project_data, self.app_config)
        self.curtains_tab = CurtainsTab(self.project_data, self.app_config)
        self.notes_tab = NotesTab(self.project_data, self.app_config)
        self.typography_tab = TypographyTab(self.project_data, self.app_config)

    def _add_all_tabs(self):
        """Add all tabs to the tab widget in saved order (or default if no saved order)."""
        # Create a mapping of tab names to tab widgets for easy lookup
        self._tab_map = {
            "Preferences": self.preferences_tab,
            "Layout": self.layout_tab,
            "Titles": self.titles_tab,
            "Timeline": self.timeline_tab,
            "Tasks": self.tasks_tab,
            "Links": self.links_tab,
            "Swimlanes": self.swimlanes_tab,
            "Pipes": self.pipes_tab,
            "Curtains": self.curtains_tab,
            "Notes": self.notes_tab,
            "Typography": self.typography_tab,
        }
        
        # Get saved order if available and valid
        saved_order = self.app_config.general.window.tab_order
        expected_tabs = set(self._tab_map.keys())
        saved_tabs = set(saved_order)
        
        # Determine which order to use
        if saved_tabs == expected_tabs:
            # Use saved order - add tabs directly in saved order
            tab_order = saved_order
        else:
            # Use default order (dictionary insertion order)
            tab_order = list(self._tab_map.keys())
        
        # Add tabs in the determined order
        for tab_name in tab_order:
            widget = self._tab_map[tab_name]
            self.tab_widget.addTab(widget, tab_name)
    
    def _restore_tab_order(self):
        """Restore tab order from saved preferences (only needed if tabs were added in wrong order)."""
        saved_order = self.app_config.general.window.tab_order
        
        # Validate that saved order contains all expected tabs
        expected_tabs = set(self._tab_map.keys())
        saved_tabs = set(saved_order)
        
        # If saved order is missing tabs or has extra tabs, use default order
        if saved_tabs != expected_tabs:
            logging.warning(f"Tab order mismatch. Expected: {expected_tabs}, Got: {saved_tabs}. Using default order.")
            return
        
        # Check if tabs are already in the correct order
        current_order = [self.tab_widget.tabText(i) for i in range(self.tab_widget.count())]
        if current_order == saved_order:
            # Already in correct order, nothing to do
            return
        
        # Store the current tab name (label) to restore selection after reordering
        current_index = self.tab_widget.currentIndex()
        current_tab_name = self.tab_widget.tabText(current_index) if current_index >= 0 else None
        
        # Remove all tabs explicitly (this properly unparents widgets)
        # Using removeTab() instead of clear() ensures widgets are properly disconnected
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        
        # Re-add tabs in saved order using the widget mapping
        for tab_name in saved_order:
            widget = self._tab_map[tab_name]
            self.tab_widget.addTab(widget, tab_name)
        
        # Restore selection by finding the tab with the saved tab name
        if current_tab_name:
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == current_tab_name:
                    self.tab_widget.setCurrentIndex(i)
                    break
        else:
            # If no tab was selected, select the first one
            if self.tab_widget.count() > 0:
                self.tab_widget.setCurrentIndex(0)
    
    def _on_tab_moved(self, from_index: int, to_index: int):
        """Handle tab moved event - save new tab order."""
        # Get current tab order
        current_order = []
        for i in range(self.tab_widget.count()):
            current_order.append(self.tab_widget.tabText(i))
        
        # Update config with new order
        self.app_config.general.window.tab_order = current_order
        # Save to settings file
        self.app_config.save_settings()

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

                # Sync chart_config from loaded project_data to app_config
                self._sync_chart_config_from_project_data()
                
                # Re-create all tabs with the new project_data
                self._create_all_tabs()
                self.tab_widget.clear()
                self._add_all_tabs()
                self._restore_tab_order()  # Restore saved tab order

                self.data_updated.emit(self.project_data.to_json())
                QMessageBox.information(self, "Success", "Project loaded from Excel successfully!")
                self.status_bar.showMessage("Project loaded from Excel successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading Excel: {e}")
                self.status_bar.showMessage("Error loading project from Excel")
                logging.error(f"Error loading from Excel: {e}", exc_info=True                )
    
    def _on_swimlanes_updated(self, data):
        """Handle updates from swimlanes tab - refresh swimlane columns in tasks table."""
        if hasattr(self.tasks_tab, '_refresh_all_swimlane_columns'):
            self.tasks_tab._refresh_all_swimlane_columns()
    
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
            if hasattr(self.notes_tab, '_sync_data'):
                self.notes_tab._sync_data()
            if hasattr(self.typography_tab, '_sync_data'):
                self.typography_tab._sync_data()
            # After syncing typography tab, sync chart_config to project_data
            self._sync_chart_config_to_project_data()
        except Exception as e:
            logging.error(f"Error syncing tab data: {e}", exc_info=True)
            # Continue anyway - emit with whatever data we have
    
    def _sync_chart_config_to_project_data(self):
        """Sync chart_config from app_config to project_data (for saving)."""
        chart_config = self.app_config.general.chart
        self.project_data.chart_config.font_family = chart_config.font_family
        self.project_data.chart_config.task_font_size = chart_config.task_font_size
        self.project_data.chart_config.scale_font_size = chart_config.scale_font_size
        self.project_data.chart_config.header_footer_font_size = chart_config.header_footer_font_size
        self.project_data.chart_config.row_number_font_size = chart_config.row_number_font_size
        self.project_data.chart_config.note_font_size = chart_config.note_font_size
        self.project_data.chart_config.swimlane_font_size = chart_config.swimlane_font_size
        self.project_data.chart_config.scale_vertical_alignment_factor = chart_config.scale_vertical_alignment_factor
        self.project_data.chart_config.task_vertical_alignment_factor = chart_config.task_vertical_alignment_factor
        self.project_data.chart_config.row_number_vertical_alignment_factor = chart_config.row_number_vertical_alignment_factor
        self.project_data.chart_config.header_footer_vertical_alignment_factor = chart_config.header_footer_vertical_alignment_factor
        self.project_data.chart_config.swimlane_top_vertical_alignment_factor = chart_config.swimlane_top_vertical_alignment_factor
        self.project_data.chart_config.swimlane_bottom_vertical_alignment_factor = chart_config.swimlane_bottom_vertical_alignment_factor
    
    def _sync_chart_config_from_project_data(self):
        """Sync chart_config from project_data to app_config (after loading)."""
        chart_config = self.app_config.general.chart
        chart_config.font_family = self.project_data.chart_config.font_family
        chart_config.task_font_size = self.project_data.chart_config.task_font_size
        chart_config.scale_font_size = self.project_data.chart_config.scale_font_size
        chart_config.header_footer_font_size = self.project_data.chart_config.header_footer_font_size
        chart_config.row_number_font_size = self.project_data.chart_config.row_number_font_size
        chart_config.note_font_size = self.project_data.chart_config.note_font_size
        chart_config.swimlane_font_size = self.project_data.chart_config.swimlane_font_size
        chart_config.scale_vertical_alignment_factor = self.project_data.chart_config.scale_vertical_alignment_factor
        chart_config.task_vertical_alignment_factor = self.project_data.chart_config.task_vertical_alignment_factor
        chart_config.row_number_vertical_alignment_factor = self.project_data.chart_config.row_number_vertical_alignment_factor
        chart_config.header_footer_vertical_alignment_factor = self.project_data.chart_config.header_footer_vertical_alignment_factor
        chart_config.swimlane_top_vertical_alignment_factor = self.project_data.chart_config.swimlane_top_vertical_alignment_factor
        chart_config.swimlane_bottom_vertical_alignment_factor = self.project_data.chart_config.swimlane_bottom_vertical_alignment_factor

    def _emit_data_updated(self):
        """Only called when Update Image button is clicked"""
        # Sync all tabs to ensure project_data is up to date
        self._sync_all_tabs()
        
        self.data_updated.emit(self.project_data.to_json())

    def _on_data_updated(self, data):
        """Handle updates from tabs that trigger chart refresh."""
        # The emitting tab already synced its data; just emit to refresh the chart
        self.data_updated.emit(self.project_data.to_json())

    def _on_preferences_updated(self, data):
        """Handle updates from preferences tab"""
        # Handle date format changes for UI date config (affects data entry tabs)
        if data.get('ui_date_format_changed'):
            # Notify tabs that use ui_date_config to refresh their date widgets
            if hasattr(self, 'tasks_tab') and hasattr(self.tasks_tab, '_refresh_date_widgets'):
                self.tasks_tab._refresh_date_widgets()
            if hasattr(self, 'pipes_tab') and hasattr(self.pipes_tab, '_refresh_date_widgets'):
                self.pipes_tab._refresh_date_widgets()
            if hasattr(self, 'curtains_tab') and hasattr(self.curtains_tab, '_refresh_date_widgets'):
                self.curtains_tab._refresh_date_widgets()
            if hasattr(self, 'timeline_tab') and hasattr(self.timeline_tab, '_refresh_date_widgets'):
                self.timeline_tab._refresh_date_widgets()
        
        # Handle date format changes for chart date config (affects SVG display)
        if data.get('chart_date_format_changed'):
            # Chart date format is used in rendering, not in UI widgets
            # No action needed here as it's used during SVG generation
            pass
        
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
    
    def _on_swimlanes_updated(self, data):
        """Handle updates from swimlanes tab - refresh swimlane columns in tasks table."""
        if hasattr(self.tasks_tab, '_refresh_all_swimlane_columns'):
            self.tasks_tab._refresh_all_swimlane_columns()

