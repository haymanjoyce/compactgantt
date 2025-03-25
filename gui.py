import os

from PyQt5.QtWidgets import QMainWindow, QTableWidget, QPushButton, QVBoxLayout, QWidget, QDialog
from PyQt5.QtSvg import QSvgWidget
import svgwrite

from PyQt5.QtWidgets import QMainWindow, QTableWidget, QPushButton, QVBoxLayout, QWidget, QDialog, QTabWidget


class DataEntryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Data")
        self.setGeometry(100, 100, 400, 300)

        # Central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # First tab for data entry
        self.data_entry_tab = QWidget()
        self.data_entry_layout = QVBoxLayout(self.data_entry_tab)
        self.table = QTableWidget(5, 3)
        self.table.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])
        self.data_entry_layout.addWidget(self.table)
        self.generate_btn = QPushButton("Generate SVG")
        self.generate_btn.clicked.connect(self.generate_and_show_svg)
        self.data_entry_layout.addWidget(self.generate_btn)
        self.tab_widget.addTab(self.data_entry_tab, "Data Entry")

        # Additional tabs can be added here
        # Example: Second tab
        self.second_tab = QWidget()
        self.second_tab_layout = QVBoxLayout(self.second_tab)
        self.second_tab_layout.addWidget(QPushButton("Second Tab Content"))
        self.tab_widget.addTab(self.second_tab, "Second Tab")

    def generate_and_show_svg(self):

        # Ensure the svg directory exists
        svg_dir = "svg"
        os.makedirs(svg_dir, exist_ok=True)

        # Extract data from table
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "0")
            data.append(row_data)

        # Generate SVG (example: simple text-based SVG)
        svg_path = os.path.join(svg_dir, "output.svg")
        dwg = svgwrite.Drawing("output.svg", size=("400px", "300px"))
        for i, row in enumerate(data):
            dwg.add(dwg.text(f"Row {i}: {row}", insert=(10, 20 + i * 20), fill="black"))
        dwg.save()

        # Show SVG in new window
        self.svg_window = SVGDisplayWindow(svg_path)
        self.svg_window.show()


class SVGDisplayWindow(QDialog):
    def __init__(self, svg_path):
        super().__init__()
        self.setWindowTitle("SVG Display")
        self.setGeometry(150, 150, 400, 300)

        # Load and display SVG
        self.svg_widget = QSvgWidget(svg_path)
        self.svg_widget.setGeometry(0, 0, 400, 300)
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.svg_widget)
        self.setLayout(self.layout)
