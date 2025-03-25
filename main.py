"""
Purpose: Launches the app, ties everything together.
Why: Keeps the startup logic separate, making it easy to test or swap UIs later.
"""


import sys
from PyQt5.QtWidgets import QApplication
from data_entry import DataEntryWindow

def main():
    app = QApplication(sys.argv)
    window = DataEntryWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()


# TODO:
#  output svg to svg folder
#  Validation: Check CSV dimensions against table size before importing.
#  UI Feedback: Use QMessageBox for errors instead of print.
#  Menu Bar: Move import/export to a File menu (self.menuBar().addMenu("File")) for a cleaner UI.
#  svg calculations
#  tabs
#  interface for non tabular data
#  menu bar
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
