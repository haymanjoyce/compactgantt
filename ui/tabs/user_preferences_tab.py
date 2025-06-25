from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLineEdit, 
                           QLabel, QMessageBox, QComboBox, QSpinBox)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UserPreferencesTab(QWidget):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        super().__init__()
        self.project_data = project_data
        self.app_config = app_config
        self._initializing = True
        self.setup_ui()
        self._load_initial_data()
        self._connect_signals()
        self._initializing = False

    def setup_ui(self):
        layout = QVBoxLayout()
        LABEL_WIDTH = 150  # Consistent label width

        # Data Entry Window Positioning Group
        data_entry_group = self._create_data_entry_positioning_group(LABEL_WIDTH)
        layout.addWidget(data_entry_group)

        # SVG Display Window Positioning Group
        svg_display_group = self._create_svg_display_positioning_group(LABEL_WIDTH)
        layout.addWidget(svg_display_group)

        self.setLayout(layout)

    def _create_data_entry_positioning_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Data Entry Window Positioning")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Screen selection
        screen_label = QLabel("Screen:")
        screen_label.setFixedWidth(label_width)
        self.data_entry_screen_spinbox = QSpinBox()
        self.data_entry_screen_spinbox.setMinimum(0)
        self.data_entry_screen_spinbox.setMaximum(10)  # Reasonable max for number of screens
        self.data_entry_screen_spinbox.setToolTip("Screen number (0 = primary screen)")

        # Position selection
        position_label = QLabel("Position:")
        position_label.setFixedWidth(label_width)
        self.data_entry_position_combo = QComboBox()
        self.data_entry_position_combo.addItems(["center", "top_left", "top_right", "bottom_left", "bottom_right", "custom"])
        self.data_entry_position_combo.setToolTip("Window position on the selected screen")

        # Custom X position
        x_label = QLabel("Custom X Position:")
        x_label.setFixedWidth(label_width)
        self.data_entry_custom_x = QSpinBox()
        self.data_entry_custom_x.setMinimum(0)
        self.data_entry_custom_x.setMaximum(9999)
        self.data_entry_custom_x.setToolTip("Custom X coordinate (used when position is 'custom')")

        # Custom Y position
        y_label = QLabel("Custom Y Position:")
        y_label.setFixedWidth(label_width)
        self.data_entry_custom_y = QSpinBox()
        self.data_entry_custom_y.setMinimum(0)
        self.data_entry_custom_y.setMaximum(9999)
        self.data_entry_custom_y.setToolTip("Custom Y coordinate (used when position is 'custom')")

        layout.addWidget(screen_label, 0, 0)
        layout.addWidget(self.data_entry_screen_spinbox, 0, 1)
        layout.addWidget(position_label, 1, 0)
        layout.addWidget(self.data_entry_position_combo, 1, 1)
        layout.addWidget(x_label, 2, 0)
        layout.addWidget(self.data_entry_custom_x, 2, 1)
        layout.addWidget(y_label, 3, 0)
        layout.addWidget(self.data_entry_custom_y, 3, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_svg_display_positioning_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("SVG Display Window Positioning")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Screen selection
        screen_label = QLabel("Screen:")
        screen_label.setFixedWidth(label_width)
        self.svg_display_screen_spinbox = QSpinBox()
        self.svg_display_screen_spinbox.setMinimum(0)
        self.svg_display_screen_spinbox.setMaximum(10)  # Reasonable max for number of screens
        self.svg_display_screen_spinbox.setToolTip("Screen number (0 = primary screen)")

        # Position selection
        position_label = QLabel("Position:")
        position_label.setFixedWidth(label_width)
        self.svg_display_position_combo = QComboBox()
        self.svg_display_position_combo.addItems(["center", "top_left", "top_right", "bottom_left", "bottom_right", "custom"])
        self.svg_display_position_combo.setToolTip("Window position on the selected screen")

        # Custom X position
        x_label = QLabel("Custom X Position:")
        x_label.setFixedWidth(label_width)
        self.svg_display_custom_x = QSpinBox()
        self.svg_display_custom_x.setMinimum(0)
        self.svg_display_custom_x.setMaximum(9999)
        self.svg_display_custom_x.setToolTip("Custom X coordinate (used when position is 'custom')")

        # Custom Y position
        y_label = QLabel("Custom Y Position:")
        y_label.setFixedWidth(label_width)
        self.svg_display_custom_y = QSpinBox()
        self.svg_display_custom_y.setMinimum(0)
        self.svg_display_custom_y.setMaximum(9999)
        self.svg_display_custom_y.setToolTip("Custom Y coordinate (used when position is 'custom')")

        layout.addWidget(screen_label, 0, 0)
        layout.addWidget(self.svg_display_screen_spinbox, 0, 1)
        layout.addWidget(position_label, 1, 0)
        layout.addWidget(self.svg_display_position_combo, 1, 1)
        layout.addWidget(x_label, 2, 0)
        layout.addWidget(self.svg_display_custom_x, 2, 1)
        layout.addWidget(y_label, 3, 0)
        layout.addWidget(self.svg_display_custom_y, 3, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _connect_signals(self):
        self.data_entry_screen_spinbox.valueChanged.connect(self._sync_data_if_not_initializing)
        self.data_entry_position_combo.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.data_entry_custom_x.valueChanged.connect(self._sync_data_if_not_initializing)
        self.data_entry_custom_y.valueChanged.connect(self._sync_data_if_not_initializing)
        self.svg_display_screen_spinbox.valueChanged.connect(self._sync_data_if_not_initializing)
        self.svg_display_position_combo.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.svg_display_custom_x.valueChanged.connect(self._sync_data_if_not_initializing)
        self.svg_display_custom_y.valueChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data(self):
        try:
            # Load window positioning settings
            self.data_entry_screen_spinbox.setValue(self.app_config.general.data_entry_screen)
            self.data_entry_position_combo.setCurrentText(self.app_config.general.data_entry_position)
            self.data_entry_custom_x.setValue(self.app_config.general.data_entry_x)
            self.data_entry_custom_y.setValue(self.app_config.general.data_entry_y)
            self.svg_display_screen_spinbox.setValue(self.app_config.general.svg_display_screen)
            self.svg_display_position_combo.setCurrentText(self.app_config.general.svg_display_position)
            self.svg_display_custom_x.setValue(self.app_config.general.svg_display_x)
            self.svg_display_custom_y.setValue(self.app_config.general.svg_display_y)

        except Exception as e:
            logging.error(f"Error in _load_initial_data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load initial data: {e}")

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            self._sync_data()

    def _sync_data(self):
        try:
            # Update app config
            self.app_config.general.data_entry_screen = self.data_entry_screen_spinbox.value()
            self.app_config.general.data_entry_position = self.data_entry_position_combo.currentText()
            self.app_config.general.data_entry_x = self.data_entry_custom_x.value()
            self.app_config.general.data_entry_y = self.data_entry_custom_y.value()
            self.app_config.general.svg_display_screen = self.svg_display_screen_spinbox.value()
            self.app_config.general.svg_display_position = self.svg_display_position_combo.currentText()
            self.app_config.general.svg_display_x = self.svg_display_custom_x.value()
            self.app_config.general.svg_display_y = self.svg_display_custom_y.value()

            # Emit data updated signal
            self.data_updated.emit({
                'data_entry_screen': self.app_config.general.data_entry_screen,
                'data_entry_position': self.app_config.general.data_entry_position,
                'data_entry_x': self.app_config.general.data_entry_x,
                'data_entry_y': self.app_config.general.data_entry_y,
                'svg_display_screen': self.app_config.general.svg_display_screen,
                'svg_display_position': self.app_config.general.svg_display_position,
                'svg_display_x': self.app_config.general.svg_display_x,
                'svg_display_y': self.app_config.general.svg_display_y
            })

        except Exception as e:
            logging.error(f"Error in _sync_data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to save data: {e}")
