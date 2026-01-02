from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QGridLayout, QCheckBox, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt
from .base_tab import BaseTab

class GridTab(BaseTab):
    def setup_ui(self):
        layout = QVBoxLayout()
        vertical_group = self._create_vertical_gridlines_group()
        layout.addWidget(vertical_group)
        
        # Add stretch at the end to push all groups to the top
        layout.addStretch(1)
        
        self.setLayout(layout)

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
        group.setLayout(layout)
        return group

    def _connect_signals(self):
        self.vertical_gridline_years.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridline_months.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridline_weeks.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridline_days.stateChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data_impl(self):
        frame_config = self.project_data.frame_config
        self.vertical_gridline_years.setChecked(frame_config.vertical_gridline_years)
        self.vertical_gridline_months.setChecked(frame_config.vertical_gridline_months)
        self.vertical_gridline_weeks.setChecked(frame_config.vertical_gridline_weeks)
        self.vertical_gridline_days.setChecked(frame_config.vertical_gridline_days)

    def _sync_data_impl(self):
        self.project_data.frame_config.vertical_gridline_years = self.vertical_gridline_years.isChecked()
        self.project_data.frame_config.vertical_gridline_months = self.vertical_gridline_months.isChecked()
        self.project_data.frame_config.vertical_gridline_weeks = self.vertical_gridline_weeks.isChecked()
        self.project_data.frame_config.vertical_gridline_days = self.vertical_gridline_days.isChecked()
        self.data_updated.emit({
            "vertical_gridline_years": self.vertical_gridline_years.isChecked(),
            "vertical_gridline_months": self.vertical_gridline_months.isChecked(),
            "vertical_gridline_weeks": self.vertical_gridline_weeks.isChecked(),
            "vertical_gridline_days": self.vertical_gridline_days.isChecked()
        })
