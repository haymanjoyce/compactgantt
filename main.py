import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from pathlib import Path
from ui.main_window import MainWindow
from models.project import ProjectData
from services.gantt_chart_service import GanttChartService
from config.app_config import AppConfig
from ui.svg_display import SvgDisplay


def main():
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    # Use ICO so Windows taskbar shows the custom logo
    icon_path = Path(__file__).parent / "assets" / "favicon.ico"
    app.setWindowIcon(QIcon(str(icon_path)))
    app_config = AppConfig()  # Single instance
    project_data = ProjectData()
    gantt_chart_service = GanttChartService(app_config)  # Pass the shared instance
    svg_display = SvgDisplay(app_config)
    data_entry = MainWindow(project_data, svg_display, app_config)  # Pass project_data, svg_display, and app_config

    def handle_svg_path(svg_path):
        if svg_path:
            svg_display.load_svg(svg_path)
        else:
            print("No SVG generated due to invalid data")

    data_entry.data_updated.connect(gantt_chart_service.generate_svg)
    gantt_chart_service.svg_generated.connect(handle_svg_path)
    data_entry.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()