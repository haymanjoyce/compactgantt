import sys

from PyQt5.QtWidgets import QApplication

from gui import DataEntryWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DataEntryWindow()
    window.show()
    sys.exit(app.exec_())
