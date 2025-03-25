"""
Purpose: Defines DataEntryWindow, handles user input and button actions.
Why: Isolates the input UI logic. It imports generate_svg and SVGDisplayWindow to delegate tasks, keeping it focused on UI.
"""


from PyQt5.QtWidgets import QMainWindow, QTableWidget, QPushButton, QVBoxLayout, QWidget, QFileDialog, QTableWidgetItem
from svg_display import SVGDisplayWindow
from svg_generator import generate_svg
import csv

class DataEntryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Data")
        self.setGeometry(100, 100, 400, 300)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.table = QTableWidget(5, 3)
        self.table.setHorizontalHeaderLabels(["Column 1", "Column 2", "Column 3"])
        self.layout.addWidget(self.table)

        # Generate SVG button
        self.generate_btn = QPushButton("Generate SVG")
        self.generate_btn.clicked.connect(self.generate_and_show_svg)
        self.layout.addWidget(self.generate_btn)

        # Import CSV button
        self.import_btn = QPushButton("Import CSV")
        self.import_btn.clicked.connect(self.import_csv)
        self.layout.addWidget(self.import_btn)

        # Export CSV button
        self.export_btn = QPushButton("Export CSV")
        self.export_btn.clicked.connect(self.export_csv)
        self.layout.addWidget(self.export_btn)

        # Initialize svg_window attribute
        self.svg_window = None

    def generate_and_show_svg(self):
        data = self._get_table_data()
        svg_path = generate_svg(data)
        self.svg_window = SVGDisplayWindow(svg_path)
        self.svg_window.show()

    def _get_table_data(self):
        """Helper to extract data from the table."""
        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data

    def import_csv(self):
        """Import data from a CSV file into the table."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, newline='') as csvfile:
                    reader = csv.reader(csvfile)
                    data = list(reader)
                    # Adjust table size if needed
                    self.table.setRowCount(len(data))
                    self.table.setColumnCount(len(data[0]) if data else 3)
                    # Populate table
                    for row_idx, row_data in enumerate(data):
                        for col_idx, value in enumerate(row_data):
                            self.table.setItem(row_idx, col_idx, QTableWidgetItem(value))
            except Exception as e:
                print(f"Error importing CSV: {e}")

    def export_csv(self):
        """Export table data to a CSV file."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if file_path:
            try:
                data = self._get_table_data()
                with open(file_path, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerows(data)
            except Exception as e:
                print(f"Error exporting CSV: {e}")

