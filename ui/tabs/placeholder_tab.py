from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import Qt

class PlaceholderTab(QWidget):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config, tab_name):
        super().__init__()
        self.project_data = project_data
        self.app_config = app_config
        self.tab_name = tab_name
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        label = QLabel(f"{self.tab_name} functionality will be implemented in a future version.")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)

    def _load_initial_data(self):
        pass  # Placeholder method to maintain interface compatibility
