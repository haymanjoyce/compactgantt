import sys
from PyQt5.QtWidgets import QApplication
from ui.data_entry_window import DataEntryWindow
from models.project import ProjectData
from services.gantt_chart_service import GanttChartService
from config.app_config import AppConfig
from ui.svg_display import FitToWindowSvgDisplay


def main():
    app = QApplication(sys.argv)
    app_config = AppConfig()  # Single instance
    project_data = ProjectData()
    gantt_chart_service = GanttChartService()
    svg_display = FitToWindowSvgDisplay(app_config)
    data_entry = DataEntryWindow(project_data, svg_display)  # Pass project_data and svg_display

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