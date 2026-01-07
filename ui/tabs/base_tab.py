from PyQt5.QtWidgets import QWidget, QMessageBox
from PyQt5.QtCore import pyqtSignal
import logging

class BaseTab(QWidget):
    """Base class for all tab widgets to eliminate code duplication."""
    
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        super().__init__()
        self.project_data = project_data
        self.app_config = app_config
        self._initializing = True
        self.setup_ui()
        self._load_initial_data()
        self._initializing = False
        self._connect_signals()

    def setup_ui(self):
        """Override this method to set up the UI for each tab."""
        raise NotImplementedError("Subclasses must implement setup_ui")

    def _load_initial_data(self):
        """Override this method to load initial data for each tab."""
        try:
            self._load_initial_data_impl()
        except Exception as e:
            logging.error(f"Error in _load_initial_data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load initial data: {e}")

    def _load_initial_data_impl(self):
        """Override this method to implement specific data loading logic."""
        pass

    def _connect_signals(self):
        """Override this method to connect signals for each tab."""
        pass

    def _sync_data_if_not_initializing(self):
        """Common method to prevent data sync during initialization."""
        if not self._initializing:
            self._sync_data()

    def _sync_data(self):
        """Override this method to implement specific data synchronization logic."""
        try:
            self._sync_data_impl()
        except ValueError as e:
            # Validation errors are expected user input errors - show message but don't crash
            logging.error(f"Error in _sync_data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save data: {e}")
        except Exception as e:
            # Unexpected errors - log, show message, and re-raise for tests
            logging.error(f"Error in _sync_data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save data: {e}")
            raise  # Re-raise the exception so tests can catch it

    def _sync_data_impl(self):
        """Override this method to implement specific data sync logic."""
        pass
    
    def _set_detail_form_enabled(self, widgets, enabled):
        """Helper method to enable/disable multiple detail form widgets.
        
        Args:
            widgets: List of QWidget objects (QComboBox, QLineEdit, etc.) to enable/disable.
                     Can also be a single widget or None (will be safely ignored).
            enabled: Boolean indicating whether widgets should be enabled
        """
        if widgets is None:
            return
        if not isinstance(widgets, list):
            widgets = [widgets]
        for widget in widgets:
            if widget is not None:
                widget.setEnabled(enabled)