from PyQt5.QtWidgets import QDialog, QVBoxLayout
from PyQt5.QtSvg import QSvgWidget
import os
from app_config import AppConfig


class SVGDisplayWindow(QDialog):
    def __init__(self, app_config, initial_path=None):
        super().__init__()
        self.setWindowTitle("SVG Display")
        self.setGeometry(150, 150, app_config.general.svg_display_width, app_config.general.svg_display_height)

        self.svg_widget = QSvgWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.svg_widget)
        self.setLayout(self.layout)

        if initial_path and os.path.exists(initial_path):
            self.load_svg(initial_path)

    def load_svg(self, svg_path):
        print("Received SVG path:", svg_path)  # Debug
        absolute_path = os.path.abspath(svg_path)
        if os.path.exists(absolute_path):
            print(f"Loading SVG from: {absolute_path}")
            self.svg_widget.load(absolute_path)
            self.show()
        else:
            print(f"SVG file not found: {absolute_path}")