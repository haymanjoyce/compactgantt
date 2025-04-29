from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QCheckBox, QPushButton, QDateEdit, QLabel
from PyQt5.QtCore import pyqtSignal, QDate
from datetime import datetime
from app_config import AppConfig


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
        form_layout = QFormLayout()

        # Chart Start Date
        self.chart_start_date = QDateEdit()
        self.chart_start_date.setCalendarPopup(True)
        self.chart_start_date.setDate(QDate.currentDate())
        form_layout.addRow("Chart Start Date:", self.chart_start_date)

        # Outer Dimensions
        self.outer_width = QLineEdit(str(self.app_config.general.svg_width))
        self.outer_height = QLineEdit(str(self.app_config.general.svg_height))
        form_layout.addRow("Outer Width:", self.outer_width)
        form_layout.addRow("Outer Height:", self.outer_height)

        # Margins (Top, Bottom, Left, Right)
        self.margin_top = QLineEdit("10")
        self.margin_bottom = QLineEdit("10")
        self.margin_left = QLineEdit("10")
        self.margin_right = QLineEdit("10")
        form_layout.addRow("Margin Top:", self.margin_top)
        form_layout.addRow("Margin Bottom:", self.margin_bottom)
        form_layout.addRow("Margin Left:", self.margin_left)
        form_layout.addRow("Margin Right:", self.margin_right)

        # Header and Footer Heights
        self.header_height = QLineEdit("50")
        self.footer_height = QLineEdit("50")
        form_layout.addRow("Header Height:", self.header_height)
        form_layout.addRow("Footer Height:", self.footer_height)

        # Header and Footer Text
        self.header_text = QLineEdit("")
        self.footer_text = QLineEdit("")
        form_layout.addRow("Header Text:", self.header_text)
        form_layout.addRow("Footer Text:", self.footer_text)

        # Number of Rows
        self.num_rows = QLineEdit("5")
        form_layout.addRow("Number of Rows:", self.num_rows)

        # Gridlines
        self.horizontal_gridlines = QCheckBox("Show Horizontal Gridlines")
        self.vertical_gridlines = QCheckBox("Show Vertical Gridlines")
        form_layout.addRow("", self.horizontal_gridlines)
        form_layout.addRow("", self.vertical_gridlines)

        layout.addLayout(form_layout)

        # Apply Button
        self.apply_button = QPushButton("Apply")
        layout.addWidget(self.apply_button)
        layout.addStretch()
        self.setLayout(layout)

    def _connect_signals(self):
        # Connect text changes for immediate updates
        for widget in [self.outer_width, self.outer_height, self.margin_top, self.margin_bottom,
                       self.margin_left, self.margin_right, self.header_height, self.footer_height,
                       self.header_text, self.footer_text, self.num_rows]:
            widget.textChanged.connect(self._sync_data_if_not_initializing)
        self.chart_start_date.dateChanged.connect(self._sync_data_if_not_initializing)
        self.horizontal_gridlines.stateChanged.connect(self._sync_data_if_not_initializing)
        self.vertical_gridlines.stateChanged.connect(self._sync_data_if_not_initializing)
        self.apply_button.clicked.connect(self._sync_data_if_not_initializing)

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
            # Collect data for FrameConfig
            frame_config = {}

            # Chart Start Date
            frame_config["chart_start_date"] = self.chart_start_date.date().toString("yyyy-MM-dd")

            # Outer Dimensions
            outer_width = float(self.outer_width.text() or self.app_config.general.svg_width)
            if outer_width <= 0:
                raise ValueError("Outer Width must be positive")
            frame_config["outer_width"] = outer_width

            outer_height = float(self.outer_height.text() or self.app_config.general.svg_height)
            if outer_height <= 0:
                raise ValueError("Outer Height must be positive")
            frame_config["outer_height"] = outer_height

            # Margins
            margins = [
                float(self.margin_top.text() or 10),
                float(self.margin_bottom.text() or 10),
                float(self.margin_left.text() or 10),
                float(self.margin_right.text() or 10)
            ]
            if any(m < 0 for m in margins):
                raise ValueError("Margins must be non-negative")
            frame_config["margins"] = tuple(margins)

            # Header and Footer
            header_height = float(self.header_height.text() or 50)
            if header_height <= 0:
                raise ValueError("Header Height must be positive")
            frame_config["header_height"] = header_height

            footer_height = float(self.footer_height.text() or 50)
            if footer_height <= 0:
                raise ValueError("Footer Height must be positive")
            frame_config["footer_height"] = footer_height

            frame_config["header_text"] = self.header_text.text() or ""
            frame_config["footer_text"] = self.footer_text.text() or ""

            # Number of Rows
            num_rows = int(self.num_rows.text() or 5)
            if num_rows <= 0:
                raise ValueError("Number of Rows must be positive")
            frame_config["num_rows"] = num_rows

            # Gridlines
            frame_config["horizontal_gridlines"] = self.horizontal_gridlines.isChecked()
            frame_config["vertical_gridlines"] = self.vertical_gridlines.isChecked()

            # Update ProjectData.frame_config
            self.project_data.frame_config = type(self.project_data.frame_config)(**frame_config)
            self.data_updated.emit(self.project_data.to_json())
        except ValueError as e:
            print(f"Validation error in LayoutTab: {e}")
            # Optionally, show a warning to the user
            # from PyQt5.QtWidgets import QMessageBox
            # QMessageBox.critical(self, "Error", str(e))

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            self._sync_data()