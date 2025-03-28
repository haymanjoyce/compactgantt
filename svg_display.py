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
        """Load and display an SVG file from the given path."""
        absolute_path = os.path.abspath(svg_path)
        if os.path.exists(absolute_path):
            print(f"Loading SVG from: {absolute_path}")
            try:
                self.svg_widget.load(absolute_path)
                # Optionally resize to match SVG (uncomment if needed)
                # svg_size = self.svg_widget.renderer().defaultSize()
                # self.resize(svg_size.width(), svg_size.height())
                self.svg_widget.update()
                self.show()
            except Exception as e:
                print(f"Failed to load SVG: {e}")
        else:
            print(f"SVG file not found: {absolute_path}")