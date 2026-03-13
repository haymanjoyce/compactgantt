from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLabel,
                           QComboBox)
from PyQt5.QtCore import Qt
import logging
from .base_tab import BaseTab

# Logging is configured centrally in utils/logging_config.py

# Named colours available on all Style tab dropdowns.
# Extends the tasks-tab Fill Color list with grey variants needed by style defaults.
STYLE_COLOURS = [
    "white", "lightgrey", "grey", "darkgrey", "black",
    "blue", "red", "green", "yellow", "orange",
    "purple", "cyan", "magenta", "brown",
    "lightblue", "lightgreen", "lightyellow", "lightpink",
    "transparent",
]


class StyleTab(BaseTab):
    def setup_ui(self):
        layout = QVBoxLayout()
        LABEL_WIDTH = 160

        layout.addWidget(self._create_chart_group(LABEL_WIDTH))
        layout.addWidget(self._create_header_footer_group(LABEL_WIDTH))
        layout.addWidget(self._create_swimlane_group(LABEL_WIDTH))
        layout.addWidget(self._create_scale_group(LABEL_WIDTH))
        layout.addWidget(self._create_gridlines_group(LABEL_WIDTH))
        layout.addWidget(self._create_tasks_group(LABEL_WIDTH))
        layout.addStretch(1)

        self.setLayout(layout)

    def _make_colour_combo(self, current_value: str, tooltip: str) -> QComboBox:
        combo = QComboBox()
        combo.addItems(STYLE_COLOURS)
        # If the stored value isn't in the list, add it so it displays correctly
        if current_value and current_value not in STYLE_COLOURS:
            combo.addItem(current_value)
        combo.setCurrentText(current_value)
        combo.setToolTip(tooltip)
        return combo

    def _create_chart_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Chart")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        bg_label = QLabel("Background Colour:")
        bg_label.setFixedWidth(label_width)
        self.chart_background_color = self._make_colour_combo(
            "white", "Background colour for the chart area")

        layout.addWidget(bg_label, 0, 0)
        layout.addWidget(self.chart_background_color, 0, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_header_footer_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Header & Footer")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        bg_label = QLabel("Background Colour:")
        bg_label.setFixedWidth(label_width)
        self.header_footer_background_color = self._make_colour_combo(
            "lightgrey", "Background colour for the header and footer bands")

        layout.addWidget(bg_label, 0, 0)
        layout.addWidget(self.header_footer_background_color, 0, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_swimlane_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Swimlane")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        label_colour_label = QLabel("Label Text Colour:")
        label_colour_label.setFixedWidth(label_width)
        self.swimlane_label_color = self._make_colour_combo(
            "grey", "Colour for swimlane label text")

        divider_colour_label = QLabel("Row Divider Colour:")
        divider_colour_label.setFixedWidth(label_width)
        self.swimlane_divider_color = self._make_colour_combo(
            "grey", "Colour for the horizontal divider line between swimlanes")

        layout.addWidget(label_colour_label, 0, 0)
        layout.addWidget(self.swimlane_label_color, 0, 1)
        layout.addWidget(divider_colour_label, 1, 0)
        layout.addWidget(self.swimlane_divider_color, 1, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_scale_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Scale")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        bg_label = QLabel("Band Background Colour:")
        bg_label.setFixedWidth(label_width)
        self.scale_background_color = self._make_colour_combo(
            "lightgrey", "Background colour for the scale band")

        tick_label = QLabel("Tick/Divider Colour:")
        tick_label.setFixedWidth(label_width)
        self.scale_tick_color = self._make_colour_combo(
            "grey", "Colour for scale tick/divider lines")

        layout.addWidget(bg_label, 0, 0)
        layout.addWidget(self.scale_background_color, 0, 1)
        layout.addWidget(tick_label, 1, 0)
        layout.addWidget(self.scale_tick_color, 1, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_gridlines_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Gridlines")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        h_label = QLabel("Horizontal Colour:")
        h_label.setFixedWidth(label_width)
        self.gridline_horizontal_color = self._make_colour_combo(
            "lightgrey", "Colour for horizontal gridlines between rows")

        v_label = QLabel("Vertical Colour:")
        v_label.setFixedWidth(label_width)
        self.gridline_vertical_color = self._make_colour_combo(
            "lightgrey", "Colour for vertical gridlines")

        layout.addWidget(h_label, 0, 0)
        layout.addWidget(self.gridline_horizontal_color, 0, 1)
        layout.addWidget(v_label, 1, 0)
        layout.addWidget(self.gridline_vertical_color, 1, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _create_tasks_group(self, label_width: int) -> QGroupBox:
        group = QGroupBox("Tasks")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)

        bar_stroke_label = QLabel("Bar Stroke Colour:")
        bar_stroke_label.setFixedWidth(label_width)
        self.task_stroke_color = self._make_colour_combo(
            "black", "Stroke colour for task bars")

        milestone_stroke_label = QLabel("Milestone Stroke Colour:")
        milestone_stroke_label.setFixedWidth(label_width)
        self.milestone_stroke_color = self._make_colour_combo(
            "black", "Stroke colour for milestone circles")

        outside_text_label = QLabel("Outside Label Text Colour:")
        outside_text_label.setFixedWidth(label_width)
        self.outside_label_text_color = self._make_colour_combo(
            "black", "Colour for outside label text")

        outside_line_label = QLabel("Outside Label Line Colour:")
        outside_line_label.setFixedWidth(label_width)
        self.outside_label_line_color = self._make_colour_combo(
            "black", "Colour for the leader line connecting outside labels")

        layout.addWidget(bar_stroke_label, 0, 0)
        layout.addWidget(self.task_stroke_color, 0, 1)
        layout.addWidget(milestone_stroke_label, 1, 0)
        layout.addWidget(self.milestone_stroke_color, 1, 1)
        layout.addWidget(outside_text_label, 2, 0)
        layout.addWidget(self.outside_label_text_color, 2, 1)
        layout.addWidget(outside_line_label, 3, 0)
        layout.addWidget(self.outside_label_line_color, 3, 1)
        layout.setColumnStretch(1, 1)
        group.setLayout(layout)
        return group

    def _connect_signals(self):
        self.chart_background_color.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.header_footer_background_color.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.swimlane_label_color.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.swimlane_divider_color.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.scale_background_color.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.scale_tick_color.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.gridline_horizontal_color.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.gridline_vertical_color.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.task_stroke_color.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.milestone_stroke_color.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.outside_label_text_color.currentTextChanged.connect(self._sync_data_if_not_initializing)
        self.outside_label_line_color.currentTextChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data_impl(self):
        chart_config = self.app_config.general.chart

        self.chart_background_color.setCurrentText(chart_config.chart_background_color)
        self.header_footer_background_color.setCurrentText(chart_config.header_footer_background_color)
        self.swimlane_label_color.setCurrentText(chart_config.swimlane_label_color)
        self.swimlane_divider_color.setCurrentText(chart_config.swimlane_divider_color)
        self.scale_background_color.setCurrentText(chart_config.scale_background_color)
        self.scale_tick_color.setCurrentText(chart_config.scale_tick_color)
        self.gridline_horizontal_color.setCurrentText(chart_config.gridline_horizontal_color)
        self.gridline_vertical_color.setCurrentText(chart_config.gridline_vertical_color)
        self.task_stroke_color.setCurrentText(chart_config.task_stroke_color)
        self.milestone_stroke_color.setCurrentText(chart_config.milestone_stroke_color)
        self.outside_label_text_color.setCurrentText(chart_config.outside_label_text_color)
        self.outside_label_line_color.setCurrentText(chart_config.outside_label_line_color)

    def _sync_data_impl(self):
        chart_config = self.app_config.general.chart

        chart_config.chart_background_color = self.chart_background_color.currentText()
        chart_config.header_footer_background_color = self.header_footer_background_color.currentText()
        chart_config.swimlane_label_color = self.swimlane_label_color.currentText()
        chart_config.swimlane_divider_color = self.swimlane_divider_color.currentText()
        chart_config.scale_background_color = self.scale_background_color.currentText()
        chart_config.scale_tick_color = self.scale_tick_color.currentText()
        chart_config.gridline_horizontal_color = self.gridline_horizontal_color.currentText()
        chart_config.gridline_vertical_color = self.gridline_vertical_color.currentText()
        chart_config.task_stroke_color = self.task_stroke_color.currentText()
        chart_config.milestone_stroke_color = self.milestone_stroke_color.currentText()
        chart_config.outside_label_text_color = self.outside_label_text_color.currentText()
        chart_config.outside_label_line_color = self.outside_label_line_color.currentText()
