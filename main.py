"""
Purpose: Launches the app, ties everything together.
Why: Keeps the startup logic separate, making it easy to test or swap UIs later.
"""


import sys
from PyQt5.QtWidgets import QApplication
from data_entry import DataEntryWindow
from svg_generator import GanttChartGenerator
from svg_display import SVGDisplayWindow


def main():
    app = QApplication(sys.argv)

    # Create instances
    data_entry = DataEntryWindow()
    svg_generator = GanttChartGenerator()
    svg_display = SVGDisplayWindow()

    # Connect signals and slots
    data_entry.data_updated.connect(svg_generator.generate_svg)
    svg_generator.svg_generated.connect(svg_display.load_svg)  # Only connect load_svg

    # Show the data entry window
    data_entry.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

