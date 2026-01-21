from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLineEdit, 
                           QLabel, QMessageBox, QSpinBox, QComboBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from typing import Dict, Any
import logging
from .base_tab import BaseTab
from config.date_config import DATE_FORMAT_OPTIONS, DateConfig

# Logging is configured centrally in utils/logging_config.py

class PreferencesTab(BaseTab):
    def setup_ui(self):
        layout = QVBoxLayout()
        LABEL_WIDTH = 150  # Consistent label width

        # Data Entry Window Group (Positioning + Date Format)
        data_entry_group = self._create_window_group(
            "Chart Data Window", 
            "data_entry", 
            LABEL_WIDTH,
            self.app_config.general.ui_date_config
        )
        layout.addWidget(data_entry_group)

        # SVG Display Window Group (Positioning + Date Format)
        svg_display_group = self._create_window_group(
            "Chart Display Window", 
            "svg_display", 
            LABEL_WIDTH,
            self.app_config.general.chart_date_config
        )
        layout.addWidget(svg_display_group)

        # Add stretch at the end to push all groups to the top
        layout.addStretch(1)

        self.setLayout(layout)

    def _create_window_group(self, title: str, prefix: str, label_width: int, date_config: DateConfig) -> QGroupBox:
        """Create a group box with positioning and date format settings.
        
        Args:
            title: Group box title
            prefix: Prefix for widget names (e.g., "data_entry", "svg_display")
            label_width: Fixed width for labels
            date_config: DateConfig instance for initializing date format selection
        """
        group = QGroupBox(title)
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Screen selection
        screen_label = QLabel("Screen:")
        screen_label.setFixedWidth(label_width)
        screen_spinbox = QSpinBox()
        screen_spinbox.setMinimum(1)  # 1-based indexing (Microsoft style)
        screen_spinbox.setMaximum(10)
        screen_spinbox.setToolTip("Screen number (1 = primary screen)")
        setattr(self, f"{prefix}_screen_spinbox", screen_spinbox)

        # X position
        x_label = QLabel("X Position:")
        x_label.setFixedWidth(label_width)
        custom_x = QSpinBox()
        custom_x.setMinimum(0)
        custom_x.setMaximum(50000)
        custom_x.setSuffix(" px")
        custom_x.setToolTip("X coordinate in pixels (window left edge position)")
        setattr(self, f"{prefix}_custom_x", custom_x)

        # Y position
        y_label = QLabel("Y Position:")
        y_label.setFixedWidth(label_width)
        custom_y = QSpinBox()
        custom_y.setMinimum(0)
        custom_y.setMaximum(50000)
        custom_y.setSuffix(" px")
        custom_y.setToolTip("Y coordinate in pixels (window top edge position)")
        setattr(self, f"{prefix}_custom_y", custom_y)

        # Date Format
        date_format_label = QLabel("Date Format:")
        date_format_label.setFixedWidth(label_width)
        date_format_combo = QComboBox()
        # Populate with format options from DATE_FORMAT_OPTIONS (key-based lookup)
        format_names = list(DATE_FORMAT_OPTIONS.keys())
        date_format_combo.addItems(format_names)
        
        # Set current selection based on date_config
        current_format_name = date_config.get_format_name()
        if current_format_name and current_format_name in format_names:
            date_format_combo.setCurrentText(current_format_name)
        else:
            # Default to first format if no match found
            date_format_combo.setCurrentIndex(0)
        
        date_format_combo.setToolTip("Date format for this window")
        setattr(self, f"{prefix}_date_format_combo", date_format_combo)

        # Layout widgets
        row = 0
        layout.addWidget(screen_label, row, 0)
        layout.addWidget(screen_spinbox, row, 1)
        row += 1
        layout.addWidget(x_label, row, 0)
        layout.addWidget(custom_x, row, 1)
        row += 1
        layout.addWidget(y_label, row, 0)
        layout.addWidget(custom_y, row, 1)
        row += 1
        layout.addWidget(date_format_label, row, 0)
        layout.addWidget(date_format_combo, row, 1)
        
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _get_screen_specification(self, screen_number: int) -> str:
        """Get screen specification information for the given screen number."""
        try:
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app is None:
                return "No application instance available"
            
            screens = app.screens()
            if screen_number >= len(screens):
                return f"Screen {screen_number} not available (max: {len(screens) - 1})"
            
            screen = screens[screen_number]
            geometry = screen.geometry()
            size = screen.size()
            logical_dpi = screen.logicalDotsPerInch()
            physical_dpi = screen.physicalDotsPerInch()
            device_pixel_ratio = screen.devicePixelRatio()
            
            # Get screen name if available
            screen_name = screen.name() if hasattr(screen, 'name') else f"Screen {screen_number}"
            
            spec = f"{screen_name} • {size.width()}×{size.height()} • {logical_dpi:.0f} DPI"
            if device_pixel_ratio != 1.0:
                spec += f" • {device_pixel_ratio:.1f}x scaling"
            
            return spec
            
        except Exception as e:
            logging.error(f"Error getting screen specification: {e}")
            return f"Error getting screen info: {e}"

    def _update_screen_specifications(self):
        """Update screen specification labels for both positioning groups."""
        for prefix in ["data_entry", "svg_display"]:
            screen_spinbox = getattr(self, f"{prefix}_screen_spinbox")
            if hasattr(self, f"{prefix}_screen_spec_label"):
                screen_spec_label = getattr(self, f"{prefix}_screen_spec_label")
                screen_number = screen_spinbox.value()
                spec = self._get_screen_specification(screen_number)
                screen_spec_label.setText(spec)

    def _connect_signals(self):
        # Connect signals for both window groups (key-based iteration)
        window_groups = {
            "data_entry": "ui_date_config",
            "svg_display": "chart_date_config"
        }
        
        for prefix, date_config_attr in window_groups.items():
            screen_spinbox = getattr(self, f"{prefix}_screen_spinbox")
            custom_x = getattr(self, f"{prefix}_custom_x")
            custom_y = getattr(self, f"{prefix}_custom_y")
            date_format_combo = getattr(self, f"{prefix}_date_format_combo")
            
            screen_spinbox.valueChanged.connect(self._sync_data_if_not_initializing)
            custom_x.valueChanged.connect(self._sync_data_if_not_initializing)
            custom_y.valueChanged.connect(self._sync_data_if_not_initializing)
            date_format_combo.currentTextChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data_impl(self):
        # Store initial date formats for change detection
        self._previous_ui_date_format = self.app_config.general.ui_date_config.get_format_name()
        self._previous_chart_date_format = self.app_config.general.chart_date_config.get_format_name()
        
        # Load window positioning and date format settings for both groups (key-based)
        window_groups = {
            "data_entry": ("ui_date_config",),
            "svg_display": ("chart_date_config",)
        }
        
        for prefix, (date_config_attr,) in window_groups.items():
            screen_spinbox = getattr(self, f"{prefix}_screen_spinbox")
            custom_x = getattr(self, f"{prefix}_custom_x")
            custom_y = getattr(self, f"{prefix}_custom_y")
            date_format_combo = getattr(self, f"{prefix}_date_format_combo")
            
            # Load positioning settings
            # Convert from 0-based (internal) to 1-based (display)
            screen_value = getattr(self.app_config.general, f"{prefix}_screen") + 1
            screen_spinbox.setValue(screen_value)
            custom_x.setValue(getattr(self.app_config.general, f"{prefix}_x"))
            custom_y.setValue(getattr(self.app_config.general, f"{prefix}_y"))
            
            # Load date format setting
            date_config = getattr(self.app_config.general, date_config_attr)
            current_format_name = date_config.get_format_name()
            if current_format_name and current_format_name in DATE_FORMAT_OPTIONS:
                date_format_combo.setCurrentText(current_format_name)

    def _sync_data_impl(self):
        # Update app config for both window groups (key-based)
        window_groups = {
            "data_entry": "ui_date_config",
            "svg_display": "chart_date_config"
        }
        
        for prefix, date_config_attr in window_groups.items():
            screen_spinbox = getattr(self, f"{prefix}_screen_spinbox")
            custom_x = getattr(self, f"{prefix}_custom_x")
            custom_y = getattr(self, f"{prefix}_custom_y")
            date_format_combo = getattr(self, f"{prefix}_date_format_combo")
            
            # Update positioning settings
            # Convert from 1-based (display) to 0-based (internal)
            screen_value = screen_spinbox.value() - 1
            setattr(self.app_config.general, f"{prefix}_screen", screen_value)
            setattr(self.app_config.general, f"{prefix}_x", custom_x.value())
            setattr(self.app_config.general, f"{prefix}_y", custom_y.value())
            
            # Update date format setting
            selected_format_name = date_format_combo.currentText()
            if selected_format_name in DATE_FORMAT_OPTIONS:
                new_date_config = DateConfig.from_format_name(selected_format_name)
                setattr(self.app_config.general, date_config_attr, new_date_config)

        # Save settings to persist between sessions
        self.app_config.save_settings()

        # Check if date formats changed by comparing with previous values
        ui_date_format_changed = False
        chart_date_format_changed = False
        
        # Get previous format names (if available) to detect changes
        old_ui_format = getattr(self, '_previous_ui_date_format', None)
        old_chart_format = getattr(self, '_previous_chart_date_format', None)
        
        current_ui_format = self.app_config.general.ui_date_config.get_format_name()
        current_chart_format = self.app_config.general.chart_date_config.get_format_name()
        
        if old_ui_format is not None and old_ui_format != current_ui_format:
            ui_date_format_changed = True
        if old_chart_format is not None and old_chart_format != current_chart_format:
            chart_date_format_changed = True
        
        # Store current formats for next comparison
        self._previous_ui_date_format = current_ui_format
        self._previous_chart_date_format = current_chart_format

        # Emit data updated signal
        self.data_updated.emit({
            'data_entry_screen': self.app_config.general.data_entry_screen,
            'data_entry_x': self.app_config.general.data_entry_x,
            'data_entry_y': self.app_config.general.data_entry_y,
            'svg_display_screen': self.app_config.general.svg_display_screen,
            'svg_display_x': self.app_config.general.svg_display_x,
            'svg_display_y': self.app_config.general.svg_display_y,
            'ui_date_format_changed': ui_date_format_changed,
            'chart_date_format_changed': chart_date_format_changed
        })
