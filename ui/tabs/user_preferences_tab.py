from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLineEdit, 
                           QLabel, QMessageBox, QSpinBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont
from typing import Dict, Any
import logging
from .base_tab import BaseTab

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UserPreferencesTab(BaseTab):
    def setup_ui(self):
        layout = QVBoxLayout()
        LABEL_WIDTH = 150  # Consistent label width

        # Data Entry Window Positioning Group
        data_entry_group = self._create_positioning_group(
            "Data Entry Window Positioning", 
            "data_entry", 
            LABEL_WIDTH
        )
        layout.addWidget(data_entry_group)

        # SVG Display Window Positioning Group
        svg_display_group = self._create_positioning_group(
            "SVG Display Window Positioning", 
            "svg_display", 
            LABEL_WIDTH
        )
        layout.addWidget(svg_display_group)

        self.setLayout(layout)

    def _create_positioning_group(self, title: str, prefix: str, label_width: int) -> QGroupBox:
        """Generic factory method to create positioning groups."""
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
        custom_x.setMaximum(9999)
        custom_x.setToolTip("X coordinate in pixels")
        setattr(self, f"{prefix}_custom_x", custom_x)

        # Y position
        y_label = QLabel("Y Position:")
        y_label.setFixedWidth(label_width)
        custom_y = QSpinBox()
        custom_y.setMinimum(0)
        custom_y.setMaximum(9999)
        custom_y.setToolTip("Y coordinate in pixels")
        setattr(self, f"{prefix}_custom_y", custom_y)

        layout.addWidget(screen_label, 0, 0)
        layout.addWidget(screen_spinbox, 0, 1)
        layout.addWidget(x_label, 1, 0)
        layout.addWidget(custom_x, 1, 1)
        layout.addWidget(y_label, 2, 0)
        layout.addWidget(custom_y, 2, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(3, 1)  # Add row stretch after the last field
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
            screen_spec_label = getattr(self, f"{prefix}_screen_spec_label")
            
            screen_number = screen_spinbox.value()
            spec = self._get_screen_specification(screen_number)
            screen_spec_label.setText(spec)

    def _connect_signals(self):
        # Connect signals for both positioning groups
        for prefix in ["data_entry", "svg_display"]:
            screen_spinbox = getattr(self, f"{prefix}_screen_spinbox")
            custom_x = getattr(self, f"{prefix}_custom_x")
            custom_y = getattr(self, f"{prefix}_custom_y")
            
            screen_spinbox.valueChanged.connect(self._sync_data_if_not_initializing)
            custom_x.valueChanged.connect(self._sync_data_if_not_initializing)
            custom_y.valueChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data_impl(self):
        # Load window positioning settings for both groups
        for prefix in ["data_entry", "svg_display"]:
            screen_spinbox = getattr(self, f"{prefix}_screen_spinbox")
            custom_x = getattr(self, f"{prefix}_custom_x")
            custom_y = getattr(self, f"{prefix}_custom_y")
            
            # Convert from 0-based (internal) to 1-based (display)
            screen_value = getattr(self.app_config.general, f"{prefix}_screen") + 1
            screen_spinbox.setValue(screen_value)
            custom_x.setValue(getattr(self.app_config.general, f"{prefix}_x"))
            custom_y.setValue(getattr(self.app_config.general, f"{prefix}_y"))

    def _sync_data_impl(self):
        # Update app config for both positioning groups
        for prefix in ["data_entry", "svg_display"]:
            screen_spinbox = getattr(self, f"{prefix}_screen_spinbox")
            custom_x = getattr(self, f"{prefix}_custom_x")
            custom_y = getattr(self, f"{prefix}_custom_y")
            
            # Convert from 1-based (display) to 0-based (internal)
            screen_value = screen_spinbox.value() - 1
            setattr(self.app_config.general, f"{prefix}_screen", screen_value)
            setattr(self.app_config.general, f"{prefix}_x", custom_x.value())
            setattr(self.app_config.general, f"{prefix}_y", custom_y.value())

        # Save settings to persist between sessions
        self.app_config.save_settings()

        # Emit data updated signal
        self.data_updated.emit({
            'data_entry_screen': self.app_config.general.data_entry_screen,
            'data_entry_x': self.app_config.general.data_entry_x,
            'data_entry_y': self.app_config.general.data_entry_y,
            'svg_display_screen': self.app_config.general.svg_display_screen,
            'svg_display_x': self.app_config.general.svg_display_x,
            'svg_display_y': self.app_config.general.svg_display_y
        })
