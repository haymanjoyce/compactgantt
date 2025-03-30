"""
Defines SVGDisplayWindow, handles SVG rendering.
Why: Separates the output UI into its own module. It’s reusable for any SVG display need, not tied to the data entry.
"""

from PyQt5.QtWidgets import QDialog, QVBoxLayout
from PyQt5.QtSvg import QSvgWidget
import os
from config import Config

class SVGDisplayWindow(QDialog):
    def __init__(self, initial_path=None):
        super().__init__()
        self.setWindowTitle("SVG Display")
        # Start with default size, adjust in load_svg
        self.setGeometry(150, 150, Config.SVG_DISPLAY_WIDTH, Config.SVG_DISPLAY_HEIGHT)

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
