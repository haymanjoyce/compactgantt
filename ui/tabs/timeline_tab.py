from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLabel, 
                           QDateEdit, QCheckBox)
from PyQt5.QtCore import pyqtSignal, Qt, QDate
from datetime import datetime, timedelta
import logging
from utils.conversion import parse_internal_date
from .base_tab import BaseTab

# Logging is configured centrally in utils/logging_config.py

class TimelineTab(BaseTab):
    def setup_ui(self):
        layout = QVBoxLayout()
        LABEL_WIDTH = 120  # Consistent label width

        # Timeframe Group
        timeframe_group = self._create_timeframe_group(LABEL_WIDTH)
        layout.addWidget(timeframe_group)

        # Scales Group
        scales_group = self._create_scales_group()
        layout.addWidget(scales_group)

        # Vertical Gridlines Group
        vertical_gridlines_group = self._create_vertical_gridlines_group()
        layout.addWidget(vertical_gridlines_group)

        # Add stretch at the end to push all groups to the top
        layout.addStretch(1)

        self.setLayout(layout)

    def _create_timeframe_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Timeframe")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        # Get date format from config (UI date config for data entry)
        date_format = self.app_config.general.ui_date_config.get_qt_format()
        date_format_display = self.app_config.general.ui_date_config.get_python_format().replace("%", "").lower()
        
        # Start Date
        start_label = QLabel("Start Date:")
        start_label.setFixedWidth(label_width)
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat(date_format)
        self.start_date.setToolTip(f"Start date of the chart timeline ({date_format_display})")

        # Finish Date
        finish_label = QLabel("Finish Date:")
        finish_label.setFixedWidth(label_width)
        self.finish_date = QDateEdit()
        self.finish_date.setCalendarPopup(True)
        self.finish_date.setDisplayFormat(date_format)
        self.finish_date.setToolTip(f"Finish date of the chart timeline ({date_format_display})")

        layout.addWidget(start_label, 0, 0)
        layout.addWidget(self.start_date, 0, 1)
        layout.addWidget(finish_label, 1, 0)
        layout.addWidget(self.finish_date, 1, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_scales_group(self) -> QGroupBox:
        group = QGroupBox("Scales")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        self.show_years = QCheckBox("Show Years")
        self.show_months = QCheckBox("Show Months")
        self.show_weeks = QCheckBox("Show Weeks")
        self.show_days = QCheckBox("Show Days")
        
        self.show_years.setToolTip("Display the years scale in the chart")
        self.show_months.setToolTip("Display the months scale in the chart")
        self.show_weeks.setToolTip("Display the weeks scale in the chart")
        self.show_days.setToolTip("Display the days scale in the chart")

        layout.addWidget(self.show_years, 0, 0)
        layout.addWidget(self.show_months, 1, 0)
        layout.addWidget(self.show_weeks, 2, 0)
        layout.addWidget(self.show_days, 3, 0)
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
        group.setLayout(layout)
        return group

    def _connect_signals(self):
        # Connect date signals with constraint updates
        self.start_date.dateChanged.connect(self._update_date_constraints)
        self.start_date.dateChanged.connect(self._sync_data_if_not_initializing)
        self.finish_date.dateChanged.connect(self._update_date_constraints)
        self.finish_date.dateChanged.connect(self._sync_data_if_not_initializing)
        self.show_years.stateChanged.connect(self._sync_data_if_not_initializing)
        self.show_months.stateChanged.connect(self._sync_data_if_not_initializing)
        self.show_weeks.stateChanged.connect(self._sync_data_if_not_initializing)
        self.show_days.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridline_years.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridline_months.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridline_weeks.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridline_days.stateChanged.connect(self._sync_data_if_not_initializing)
    
    def _update_date_constraints(self):
        """Update date constraints to prevent invalid date ranges."""
        start_qdate = self.start_date.date()
        finish_qdate = self.finish_date.date()
        
        # Set finish date minimum to start date + 1 day
        min_finish_date = start_qdate.addDays(1)
        self.finish_date.setMinimumDate(min_finish_date)
        
        # Set start date maximum to finish date - 1 day
        max_start_date = finish_qdate.addDays(-1)
        self.start_date.setMaximumDate(max_start_date)

    def _load_initial_data_impl(self):
        frame_config = self.project_data.frame_config

        # Load Timeframe dates
        start_date_str = getattr(frame_config, 'chart_start_date', '2024-12-30')
        finish_date_str = getattr(frame_config, 'chart_end_date', None)
        
        # If finish_date doesn't exist, calculate default (30 days after start)
        if not finish_date_str:
            start_dt = parse_internal_date(start_date_str)
            if start_dt:
                finish_dt = start_dt + timedelta(days=30)
                finish_date_str = finish_dt.strftime("%Y-%m-%d")
            else:
                finish_date_str = "2025-01-29"
        
        # Convert internal format (yyyy-mm-dd) to QDate
        start_dt = parse_internal_date(start_date_str)
        finish_dt = parse_internal_date(finish_date_str)
        if start_dt and finish_dt:
            start_qdate = QDate(start_dt.year, start_dt.month, start_dt.day)
            finish_qdate = QDate(finish_dt.year, finish_dt.month, finish_dt.day)
            
            # Set dates (block signals temporarily to avoid constraint updates during initial load)
            self.start_date.blockSignals(True)
            self.finish_date.blockSignals(True)
            self.start_date.setDate(start_qdate)
            self.finish_date.setDate(finish_qdate)
            self.start_date.blockSignals(False)
            self.finish_date.blockSignals(False)
            
            # Update constraints after setting dates
            self._update_date_constraints()
        else:
            # Fallback to defaults if parsing fails
            default_start = QDate(2024, 12, 30)
            default_finish = QDate(2025, 1, 29)
            self.start_date.blockSignals(True)
            self.finish_date.blockSignals(True)
            self.start_date.setDate(default_start)
            self.finish_date.setDate(default_finish)
            self.start_date.blockSignals(False)
            self.finish_date.blockSignals(False)
            self._update_date_constraints()

        # Load Scales
        self.show_years.setChecked(getattr(frame_config, 'show_years', True))
        self.show_months.setChecked(getattr(frame_config, 'show_months', True))
        self.show_weeks.setChecked(getattr(frame_config, 'show_weeks', True))
        self.show_days.setChecked(getattr(frame_config, 'show_days', True))

        # Load Vertical Gridlines
        self.vertical_gridline_years.setChecked(frame_config.vertical_gridline_years)
        self.vertical_gridline_months.setChecked(frame_config.vertical_gridline_months)
        self.vertical_gridline_weeks.setChecked(frame_config.vertical_gridline_weeks)
        self.vertical_gridline_days.setChecked(frame_config.vertical_gridline_days)

    def _sync_data_impl(self):
        # Validate date range
        start_qdate = self.start_date.date()
        finish_qdate = self.finish_date.date()
        if finish_qdate <= start_qdate:
            raise ValueError("Finish date must be after start date")

        # Update timeframe dates (convert QDate to internal format yyyy-mm-dd)
        start_date_str = start_qdate.toString("yyyy-MM-dd")
        finish_date_str = finish_qdate.toString("yyyy-MM-dd")
        self.project_data.frame_config.chart_start_date = start_date_str
        self.project_data.frame_config.chart_end_date = finish_date_str

        # Update Scales
        self.project_data.frame_config.show_years = self.show_years.isChecked()
        self.project_data.frame_config.show_months = self.show_months.isChecked()
        self.project_data.frame_config.show_weeks = self.show_weeks.isChecked()
        self.project_data.frame_config.show_days = self.show_days.isChecked()
    
    def _refresh_date_widgets(self):
        """Refresh date widgets with current date format from config."""
        # Get current dates
        start_date = self.start_date.date()
        finish_date = self.finish_date.date()
        start_date_str = start_date.toString("yyyy-MM-dd")
        finish_date_str = finish_date.toString("yyyy-MM-dd")
        
        # Disconnect signals temporarily
        self.start_date.blockSignals(True)
        self.finish_date.blockSignals(True)
        
        # Update display format
        date_format = self.app_config.general.ui_date_config.get_qt_format()
        self.start_date.setDisplayFormat(date_format)
        self.finish_date.setDisplayFormat(date_format)
        
        # Restore dates
        self.start_date.setDate(start_date)
        self.finish_date.setDate(finish_date)
        
        # Re-enable signals
        self.start_date.blockSignals(False)
        self.finish_date.blockSignals(False)
        
        # Update constraints after format change
        self._update_date_constraints()

        # Update Vertical Gridlines
        self.project_data.frame_config.vertical_gridline_years = self.vertical_gridline_years.isChecked()
        self.project_data.frame_config.vertical_gridline_months = self.vertical_gridline_months.isChecked()
        self.project_data.frame_config.vertical_gridline_weeks = self.vertical_gridline_weeks.isChecked()
        self.project_data.frame_config.vertical_gridline_days = self.vertical_gridline_days.isChecked()

        # Removed data_updated.emit() for consistency with Layout tab - user must click "Update Chart"

