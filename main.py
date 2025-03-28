"""
Purpose: Launches the app, ties everything together.
Why: Keeps the startup logic separate, making it easy to test or swap UIs later.

Notes on Signals/Slots Integration:

1) data_entry.py: Emits data_updated with self.project_data.to_json() whenever data is synced (e.g., after adding/removing rows, saving, or generating the chart).
2) svg_generator.py: Receives this JSON dict via generate_svg and renders it into an SVG, emitting svg_generated.
3) svg_display.py: Updates the display based on the SVG path from svg_generated.

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


# TODO:
#  import and export xlsx
#  non-tabular UI for project start/end dates
#  error dialogues
#  add “New Project” or “Exit” to the File menu
#  auto-name CSV/SVG files or add a "Save As" history.
#  Validation: Check table dimensions against table size before importing.
#  UI Feedback: Use QMessageBox for errors instead of print.
#  Table Flexibility: Let users resize the table (add/remove rows/columns).
#  Add shortcuts (e.g., Ctrl+R for “Add Row”), non-tabular UI, or start the Gantt SVG?
#  svg calculations
#  interface for non tabular data
#  dynamic update
#  export raster and pdf
#  print
#  try except
#  packaging (.exe, PyPI)
#  logging
#  testing
#  documentation
#  versioning
#  licensing
#  internationalization
#  accessibility
