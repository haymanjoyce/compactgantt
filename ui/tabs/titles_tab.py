from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLineEdit, 
                           QLabel, QMessageBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QIntValidator
from typing import Dict, Any
import logging
from .base_tab import BaseTab
from validators.validators import DataValidator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TitlesTab(BaseTab):
    def setup_ui(self):
        layout = QVBoxLayout()
        LABEL_WIDTH = 120  # Consistent label width

        # Header Group
        header_group = self._create_header_group(LABEL_WIDTH)
        layout.addWidget(header_group)

        # Footer Group
        footer_group = self._create_footer_group(LABEL_WIDTH)
        layout.addWidget(footer_group)

        # Add stretch at the end to push all groups to the top
        layout.addStretch(1)

        self.setLayout(layout)

    def _create_header_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Header Settings")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Header height
        header_height_label = QLabel("Header Height:")
        header_height_label.setFixedWidth(label_width)
        self.header_height = QLineEdit("20")
        self.header_height.setToolTip("Height of the header section in pixels (0 to hide header)")
        # Add validator to only allow non-negative integers
        validator = QIntValidator(0, 999999, self)
        self.header_height.setValidator(validator)

        # Header text
        header_text_label = QLabel("Header Text:")
        header_text_label.setFixedWidth(label_width)
        self.header_text = QLineEdit("Header text")
        self.header_text.setToolTip("Text to display in the header")

        layout.addWidget(header_height_label, 0, 0)
        layout.addWidget(self.header_height, 0, 1)
        layout.addWidget(header_text_label, 1, 0)
        layout.addWidget(self.header_text, 1, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_footer_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Footer Settings")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Footer height
        footer_height_label = QLabel("Footer Height:")
        footer_height_label.setFixedWidth(label_width)
        self.footer_height = QLineEdit("20")
        self.footer_height.setToolTip("Height of the footer section in pixels (0 to hide footer)")
        # Add validator to only allow non-negative integers
        validator = QIntValidator(0, 999999, self)
        self.footer_height.setValidator(validator)

        # Footer text
        footer_text_label = QLabel("Footer Text:")
        footer_text_label.setFixedWidth(label_width)
        self.footer_text = QLineEdit("Footer text")
        self.footer_text.setToolTip("Text to display in the footer")

        layout.addWidget(footer_height_label, 0, 0)
        layout.addWidget(self.footer_height, 0, 1)
        layout.addWidget(footer_text_label, 1, 0)
        layout.addWidget(self.footer_text, 1, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _connect_signals(self):
        # Header signals
        self.header_height.textChanged.connect(self._sync_data_if_not_initializing)
        self.header_text.textChanged.connect(self._sync_data_if_not_initializing)
        
        # Footer signals
        self.footer_height.textChanged.connect(self._sync_data_if_not_initializing)
        self.footer_text.textChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data_impl(self):
        frame_config = self.project_data.frame_config

        # Load Header settings
        self.header_height.setText(str(frame_config.header_height))
        # Use default if empty, otherwise use saved value
        header_text = frame_config.header_text if frame_config.header_text else "Header text"
        self.header_text.setText(header_text)

        # Load Footer settings
        self.footer_height.setText(str(frame_config.footer_height))
        # Use default if empty, otherwise use saved value
        footer_text = frame_config.footer_text if frame_config.footer_text else "Footer text"
        self.footer_text.setText(footer_text)

    def _sync_data_impl(self):
        # Validate numeric inputs
        numeric_fields = {
            "header_height": self.header_height.text(),
            "footer_height": self.footer_height.text(),
        }

        for field_name, value in numeric_fields.items():
            display_name = field_name.replace('_', ' ').title()
            errors = DataValidator.validate_non_negative_integer_string(value, display_name)
            if errors:
                raise ValueError(errors[0])  # Raise first error

        # Update frame config
        self.project_data.frame_config.header_height = int(self.header_height.text())
        self.project_data.frame_config.header_text = self.header_text.text()
        self.project_data.frame_config.footer_height = int(self.footer_height.text())
        self.project_data.frame_config.footer_text = self.footer_text.text()

        # Emit data updated signal
        self.data_updated.emit({
            'header_height': self.project_data.frame_config.header_height,
            'header_text': self.project_data.frame_config.header_text,
            'footer_height': self.project_data.frame_config.footer_height,
            'footer_text': self.project_data.frame_config.footer_text
        }) 