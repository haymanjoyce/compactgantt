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
    def handle_svg_path(svg_path):
        if svg_path:  # Only load if path is non-empty
            svg_display.load_svg(svg_path)
        else:
            print("No SVG generated due to invalid data")

    data_entry.data_updated.connect(svg_generator.generate_svg)
    svg_generator.svg_generated.connect(handle_svg_path)  # Use wrapper to check path

    # Show the data entry window
    data_entry.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()