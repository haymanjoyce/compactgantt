from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLineEdit, 
                           QLabel, QMessageBox)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HeaderTab(QWidget):
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
        LABEL_WIDTH = 120  # Consistent label width

        # Header Group
        header_group = self._create_header_group(LABEL_WIDTH)
        layout.addWidget(header_group)

        self.setLayout(layout)

    def _create_header_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Header Settings")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Header height
        header_height_label = QLabel("Header Height:")
        header_height_label.setFixedWidth(label_width)
        self.header_height = QLineEdit("50")
        self.header_height.setToolTip("Height of the header section in pixels")

        # Header text
        header_text_label = QLabel("Header Text:")
        header_text_label.setFixedWidth(label_width)
        self.header_text = QLineEdit()
        self.header_text.setToolTip("Text to display in the header")

        layout.addWidget(header_height_label, 0, 0)
        layout.addWidget(self.header_height, 0, 1)
        layout.addWidget(header_text_label, 1, 0)
        layout.addWidget(self.header_text, 1, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _connect_signals(self):
        self.header_height.textChanged.connect(self._sync_data_if_not_initializing)
        self.header_text.textChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data(self):
        try:
            frame_config = self.project_data.frame_config

            # Load Header settings
            self.header_height.setText(str(frame_config.header_height))
            self.header_text.setText(frame_config.header_text)

        except Exception as e:
            logging.error(f"Error in _load_initial_data: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to load initial data: {e}")

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            self._sync_data()

    def _sync_data(self):
        try:
            # Validate numeric inputs
            numeric_fields = {
                "header_height": self.header_height.text(),
            }

            for field_name, value in numeric_fields.items():
                try:
                    if not value.strip() or int(value) <= 0:
                        raise ValueError(f"{field_name.replace('_', ' ').title()} must be a positive number")
                except ValueError as e:
                    if "must be a positive number" not in str(e):
                        raise ValueError(f"{field_name.replace('_', ' ').title()} must be a valid number")
                    raise

            # Update frame config
            self.project_data.frame_config.header_height = int(self.header_height.text())
            self.project_data.frame_config.header_text = self.header_text.text()

            # Emit data updated signal
            self.data_updated.emit({
                'header_height': self.project_data.frame_config.header_height,
                'header_text': self.project_data.frame_config.header_text
            })

        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
