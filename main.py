import sys
from PyQt5.QtWidgets import QApplication
from ui.data_entry_window import DataEntryWindow
from models.project import ProjectData
from services.gantt_chart_service import GanttChartService
from ui.svg_display import SVGDisplayWindow
from config.app_config import AppConfig


def main():
    app = QApplication(sys.argv)
    app_config = AppConfig()  # Single instance
    project_data = ProjectData()
    data_entry = DataEntryWindow(project_data)  # Pass project_data
    gantt_chart_service = GanttChartService()
    svg_display = SVGDisplayWindow(app_config)

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