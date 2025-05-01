from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QGroupBox, QLineEdit, QCheckBox, QDateEdit, QLabel, QMessageBox
from PyQt5.QtCore import pyqtSignal, QDate, Qt
from datetime import datetime
from PyQt5.QtGui import QBrush, QColor

class LayoutTab(QWidget):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        super().__init__()
        self.project_data = project_data
        self.app_config = app_config
        self.setup_ui()
        self._load_initial_data()
        self._connect_signals()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Define a standard width for all labels
        LABEL_WIDTH = 120  # Consistent with other labels

        # Chart Settings Group
        chart_group = QGroupBox("Chart Settings")
        chart_layout = QGridLayout()
        chart_layout.setHorizontalSpacing(10)
        chart_layout.setVerticalSpacing(5)
        chart_label = QLabel("Chart Start Date:")
        chart_label.setFixedWidth(LABEL_WIDTH)
        self.chart_start_date = QDateEdit()
        self.chart_start_date.setCalendarPopup(True)
        self.chart_start_date.setDate(QDate.currentDate())
        chart_layout.addWidget(chart_label, 0, 0)
        chart_layout.addWidget(self.chart_start_date, 0, 1)
        chart_layout.setColumnStretch(1, 1)
        chart_group.setLayout(chart_layout)
        layout.addWidget(chart_group)

        # Dimensions Group
        dim_group = QGroupBox("Dimensions")
        dim_layout = QGridLayout()
        dim_layout.setHorizontalSpacing(10)
        dim_layout.setVerticalSpacing(5)
        self.outer_width = QLineEdit(str(self.app_config.general.svg_width))
        self.outer_width.setToolTip("Total width of the chart in pixels")
        self.outer_height = QLineEdit(str(self.app_config.general.svg_height))
        self.outer_height.setToolTip("Total height of the chart in pixels")
        width_label = QLabel("Outer Width:")
        width_label.setFixedWidth(LABEL_WIDTH)
        height_label = QLabel("Outer Height:")
        height_label.setFixedWidth(LABEL_WIDTH)
        dim_layout.addWidget(width_label, 0, 0)
        dim_layout.addWidget(self.outer_width, 0, 1)
        dim_layout.addWidget(height_label, 1, 0)
        dim_layout.addWidget(self.outer_height, 1, 1)
        dim_layout.setColumnStretch(1, 1)
        dim_group.setLayout(dim_layout)
        layout.addWidget(dim_group)

        # Margins Group
        margins_group = QGroupBox("Margins")
        margins_layout = QGridLayout()
        margins_layout.setHorizontalSpacing(10)
        margins_layout.setVerticalSpacing(5)
        self.margin_top = QLineEdit("10")
        self.margin_bottom = QLineEdit("10")
        self.margin_left = QLineEdit("10")
        self.margin_right = QLineEdit("10")
        top_label = QLabel("Margin Top:")
        top_label.setFixedWidth(LABEL_WIDTH)
        bottom_label = QLabel("Margin Bottom:")
        bottom_label.setFixedWidth(LABEL_WIDTH)
        left_label = QLabel("Margin Left:")
        left_label.setFixedWidth(LABEL_WIDTH)
        right_label = QLabel("Margin Right:")
        right_label.setFixedWidth(LABEL_WIDTH)
        margins_layout.addWidget(top_label, 0, 0)
        margins_layout.addWidget(self.margin_top, 0, 1)
        margins_layout.addWidget(bottom_label, 1, 0)
        margins_layout.addWidget(self.margin_bottom, 1, 1)
        margins_layout.addWidget(left_label, 2, 0)
        margins_layout.addWidget(self.margin_left, 2, 1)
        margins_layout.addWidget(right_label, 3, 0)
        margins_layout.addWidget(self.margin_right, 3, 1)
        margins_layout.setColumnStretch(1, 1)
        margins_group.setLayout(margins_layout)
        layout.addWidget(margins_group)

        # Header/Footer Group
        hf_group = QGroupBox("Header/Footer")
        hf_layout = QGridLayout()
        hf_layout.setHorizontalSpacing(10)
        hf_layout.setVerticalSpacing(5)
        self.header_height = QLineEdit("50")
        self.footer_height = QLineEdit("50")
        self.header_text = QLineEdit("")
        self.footer_text = QLineEdit("")
        self.num_rows = QLineEdit("5")
        header_height_label = QLabel("Header Height:")
        header_height_label.setFixedWidth(LABEL_WIDTH)
        footer_height_label = QLabel("Footer Height:")
        footer_height_label.setFixedWidth(LABEL_WIDTH)
        header_text_label = QLabel("Header Text:")
        header_text_label.setFixedWidth(LABEL_WIDTH)
        footer_text_label = QLabel("Footer Text:")
        footer_text_label.setFixedWidth(LABEL_WIDTH)
        num_rows_label = QLabel("Number of Rows:")
        num_rows_label.setFixedWidth(LABEL_WIDTH)
        hf_layout.addWidget(header_height_label, 0, 0)
        hf_layout.addWidget(self.header_height, 0, 1)
        hf_layout.addWidget(footer_height_label, 1, 0)
        hf_layout.addWidget(self.footer_height, 1, 1)
        hf_layout.addWidget(header_text_label, 2, 0)
        hf_layout.addWidget(self.header_text, 2, 1)
        hf_layout.addWidget(footer_text_label, 3, 0)
        hf_layout.addWidget(self.footer_text, 3, 1)
        hf_layout.addWidget(num_rows_label, 4, 0)
        hf_layout.addWidget(self.num_rows, 4, 1)
        hf_layout.setColumnStretch(1, 1)
        hf_group.setLayout(hf_layout)
        layout.addWidget(hf_group)

        # Gridlines Group
        grid_group = QGroupBox("Gridlines")
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(10)
        grid_layout.setVerticalSpacing(5)

        # Create separate labels for gridlines
        horizontal_label = QLabel("Horizontal Gridlines:")
        horizontal_label.setFixedWidth(LABEL_WIDTH)
        vertical_label = QLabel("Vertical Gridlines:")
        vertical_label.setFixedWidth(LABEL_WIDTH)

        # Create checkboxes without text
        self.horizontal_gridlines = QCheckBox()
        self.vertical_gridlines = QCheckBox()

        # Add labels and checkboxes to the layout
        grid_layout.addWidget(horizontal_label, 0, 0)
        grid_layout.addWidget(self.horizontal_gridlines, 0, 1, alignment=Qt.AlignLeft)  # Align checkbox to the left
        grid_layout.addWidget(vertical_label, 1, 0)
        grid_layout.addWidget(self.vertical_gridlines, 1, 1, alignment=Qt.AlignLeft)  # Align checkbox to the left

        # Allow the second column to stretch, ensuring checkboxes align with other input fields
        grid_layout.setColumnStretch(1, 1)

        grid_group.setLayout(grid_layout)
        layout.addWidget(grid_group)

        layout.addStretch()
        self.setLayout(layout)

    def _connect_signals(self):
        for widget in [self.outer_width, self.outer_height, self.margin_top, self.margin_bottom,
                       self.margin_left, self.margin_right, self.header_height, self.footer_height,
                       self.header_text, self.footer_text, self.num_rows]:
            widget.textChanged.connect(self._sync_data_if_not_initializing)
        self.chart_start_date.dateChanged.connect(self._sync_data_if_not_initializing)
        self.horizontal_gridlines.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridlines.stateChanged.connect(self._sync_data_if_not_initializing)

    def _load_initial_data(self):
        self._initializing = True
        frame_config = self.project_data.frame_config

        # Load Chart Start Date
        start_date = getattr(frame_config, "chart_start_date", QDate.currentDate().toString("yyyy-MM-dd"))
        if not start_date:
            start_date = QDate.currentDate().toString("yyyy-MM-dd")
        try:
            date = datetime.strptime(start_date, "%Y-%m-%d")
            self.chart_start_date.setDate(QDate(date.year, date.month, date.day))
        except ValueError:
            self.chart_start_date.setDate(QDate.currentDate())

        # Load Dimensions
        self.outer_width.setText(str(getattr(frame_config, "outer_width", self.app_config.general.svg_width)))
        self.outer_height.setText(str(getattr(frame_config, "outer_height", self.app_config.general.svg_height)))

        # Load Margins
        margins = getattr(frame_config, "margins", (10, 10, 10, 10))
        if not margins or len(margins) != 4:
            margins = (10, 10, 10, 10)
        self.margin_top.setText(str(margins[0]))
        self.margin_bottom.setText(str(margins[1]))
        self.margin_left.setText(str(margins[2]))
        self.margin_right.setText(str(margins[3]))

        # Load Header and Footer
        self.header_height.setText(str(getattr(frame_config, "header_height", 50)))
        self.footer_height.setText(str(getattr(frame_config, "footer_height", 50)))
        self.header_text.setText(str(getattr(frame_config, "header_text", "")))
        self.footer_text.setText(str(getattr(frame_config, "footer_text", "")))

        # Load Number of Rows
        self.num_rows.setText(str(getattr(frame_config, "num_rows", 5)))

        # Load Gridlines
        self.horizontal_gridlines.setChecked(getattr(frame_config, "horizontal_gridlines", False))
        self.vertical_gridlines.setChecked(getattr(frame_config, "vertical_gridlines", False))

        self._initializing = False

    def _sync_data(self):
        try:
            frame_config = {}
            frame_config["chart_start_date"] = self.chart_start_date.date().toString("yyyy-MM-dd")

            # Validate and collect dimensions
            outer_width = float(self.outer_width.text() or self.app_config.general.svg_width)
            if outer_width <= 0:
                self.outer_width.setStyleSheet("background-color: #ffcccc")
                raise ValueError("Outer Width must be positive")
            self.outer_width.setStyleSheet("")
            frame_config["outer_width"] = outer_width

            outer_height = float(self.outer_height.text() or self.app_config.general.svg_height)
            if outer_height <= 0:
                self.outer_height.setStyleSheet("background-color: #ffcccc")
                raise ValueError("Outer Height must be positive")
            self.outer_height.setStyleSheet("")
            frame_config["outer_height"] = outer_height

            # Validate and collect margins
            margins = [
                float(self.margin_top.text() or 10),
                float(self.margin_bottom.text() or 10),
                float(self.margin_left.text() or 10),
                float(self.margin_right.text() or 10)
            ]
            for i, (margin, widget) in enumerate(zip(margins, [self.margin_top, self.margin_bottom, self.margin_left, self.margin_right])):
                if margin < 0:
                    widget.setStyleSheet("background-color: #ffcccc")
                    raise ValueError(f"Margin {'Top' if i == 0 else 'Bottom' if i == 1 else 'Left' if i == 2 else 'Right'} must be non-negative")
                widget.setStyleSheet("")
            frame_config["margins"] = tuple(margins)

            # Validate and collect header/footer
            header_height = float(self.header_height.text() or 50)
            if header_height <= 0:
                self.header_height.setStyleSheet("background-color: #ffcccc")
                raise ValueError("Header Height must be positive")
            self.header_height.setStyleSheet("")
            frame_config["header_height"] = header_height

            footer_height = float(self.footer_height.text() or 50)
            if footer_height <= 0:
                self.footer_height.setStyleSheet("background-color: #ffcccc")
                raise ValueError("Footer Height must be positive")
            self.footer_height.setStyleSheet("")
            frame_config["footer_height"] = footer_height

            frame_config["header_text"] = self.header_text.text() or ""
            frame_config["footer_text"] = self.footer_text.text() or ""

            # Validate and collect number of rows
            num_rows = int(self.num_rows.text() or 5)
            if num_rows <= 0:
                self.num_rows.setStyleSheet("background-color: #ffcccc")
                raise ValueError("Number of Rows must be positive")
            self.num_rows.setStyleSheet("")
            frame_config["num_rows"] = num_rows

            # Collect gridlines
            frame_config["horizontal_gridlines"] = self.horizontal_gridlines.isChecked()
            frame_config["vertical_gridlines"] = self.vertical_gridlines.isChecked()

            # Update project data
            self.project_data.frame_config = type(self.project_data.frame_config)(**frame_config)
        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            self._sync_data()