from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QGridLayout, QCheckBox, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt
from .base_tab import BaseTab

class GridTab(BaseTab):
    def setup_ui(self):
        layout = QVBoxLayout()
        horizontal_group = self._create_horizontal_gridlines_group()
        vertical_group = self._create_vertical_gridlines_group()
        layout.addWidget(horizontal_group)
        layout.addWidget(vertical_group)
        self.setLayout(layout)

    def _create_horizontal_gridlines_group(self) -> QGroupBox:
        group = QGroupBox("Horizontal Gridlines")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        self.horizontal_gridlines = QCheckBox("Show Row Gridlines")
        self.horizontal_gridlines.setToolTip("Display horizontal gridlines at row boundaries")

        layout.addWidget(self.horizontal_gridlines, 0, 0)
        layout.setRowStretch(1, 1)  # Add row stretch after the last field
        group.setLayout(layout)
        return group

    def _create_vertical_gridlines_group(self) -> QGroupBox:
        group = QGroupBox("Vertical Gridlines")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        self.vertical_gridline_years = QCheckBox("Show Years Gridlines")
        self.vertical_gridline_months = QCheckBox("Show Months Gridlines")
        self.vertical_gridline_weeks = QCheckBox("Show Weeks Gridlines")
        self.vertical_gridline_days = QCheckBox("Show Days Gridlines")
        
        self.vertical_gridline_years.setToolTip("Display vertical gridlines at year boundaries")
        self.vertical_gridline_months.setToolTip("Display vertical gridlines at month boundaries")
        self.vertical_gridline_weeks.setToolTip("Display vertical gridlines at week boundaries")
        self.vertical_gridline_days.setToolTip("Display vertical gridlines at day boundaries")

        layout.addWidget(self.vertical_gridline_years, 0, 0)
        layout.addWidget(self.vertical_gridline_months, 1, 0)
        layout.addWidget(self.vertical_gridline_weeks, 2, 0)
        layout.addWidget(self.vertical_gridline_days, 3, 0)
        layout.setRowStretch(4, 1)  # Add row stretch after the last field
        group.setLayout(layout)
        return group

    def _connect_signals(self):
        self.horizontal_gridlines.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridline_years.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridline_months.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridline_weeks.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridline_days.stateChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data_impl(self):
        frame_config = self.project_data.frame_config
        self.horizontal_gridlines.setChecked(frame_config.horizontal_gridlines)
        
        # Handle backward compatibility: if old vertical_gridlines exists, migrate to new format
        if hasattr(frame_config, 'vertical_gridlines') and not hasattr(frame_config, 'vertical_gridline_years'):
            # Old format - migrate to new individual flags
            old_value = frame_config.vertical_gridlines
            frame_config.vertical_gridline_years = old_value
            frame_config.vertical_gridline_months = old_value
            frame_config.vertical_gridline_weeks = old_value
            frame_config.vertical_gridline_days = old_value
            # Optionally remove old attribute (but not necessary, it won't hurt)
        
        # Load individual flags (with defaults if not present)
        self.vertical_gridline_years.setChecked(getattr(frame_config, 'vertical_gridline_years', True))
        self.vertical_gridline_months.setChecked(getattr(frame_config, 'vertical_gridline_months', True))
        self.vertical_gridline_weeks.setChecked(getattr(frame_config, 'vertical_gridline_weeks', False))
        self.vertical_gridline_days.setChecked(getattr(frame_config, 'vertical_gridline_days', False))

    def _sync_data_impl(self):
        self.project_data.frame_config.horizontal_gridlines = self.horizontal_gridlines.isChecked()
        self.project_data.frame_config.vertical_gridline_years = self.vertical_gridline_years.isChecked()
        self.project_data.frame_config.vertical_gridline_months = self.vertical_gridline_months.isChecked()
        self.project_data.frame_config.vertical_gridline_weeks = self.vertical_gridline_weeks.isChecked()
        self.project_data.frame_config.vertical_gridline_days = self.vertical_gridline_days.isChecked()
        self.data_updated.emit({
            "horizontal_gridlines": self.horizontal_gridlines.isChecked(),
            "vertical_gridline_years": self.vertical_gridline_years.isChecked(),
            "vertical_gridline_months": self.vertical_gridline_months.isChecked(),
            "vertical_gridline_weeks": self.vertical_gridline_weeks.isChecked(),
            "vertical_gridline_days": self.vertical_gridline_days.isChecked()
        })
