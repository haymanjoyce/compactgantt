"""
Purpose: Generates an SVG Gantt chart from ProjectData.
Why: Visualizes the layout structure and tasks for project planning.
"""

import svgwrite
from datetime import datetime, timedelta
import os
from PyQt5.QtCore import QObject, pyqtSignal
from config import Config

class GanttChartGenerator(QObject):
    svg_generated = pyqtSignal(str)  # Signal to emit the SVG file path

    def __init__(self, output_folder: str = Config.SVG_OUTPUT_FOLDER, output_filename: str = Config.SVG_OUTPUT_FILENAME):
        """Initialize the Gantt chart generator."""
        super().__init__()
        self.output_folder = output_folder
        self.output_filename = output_filename
        self.dwg = None  # Initialized in generate_svg
        self.row_height = 30
        self.time_scale = None
        self.data = {"frame_config": {}, "time_frames": [], "tasks": []}  # Default empty data

    def generate_svg(self, data):
        """Generate the SVG Gantt chart from the provided data."""
        try:
            self.data = data  # Expecting dict with frame_config, time_frames, tasks
            width = self.data["frame_config"]["outer_width"]
            height = self.data["frame_config"]["outer_height"]
            self.dwg = svgwrite.Drawing(filename=os.path.abspath(os.path.join(self.output_folder, self.output_filename)),
                                      size=(width, height))
            self.render()
            svg_path = os.path.abspath(os.path.join(self.output_folder, self.output_filename))
            self.svg_generated.emit(svg_path)  # type: ignore[attr-defined]  # Suppress PyCharm warning
            return svg_path
        except Exception as e:
            raise ValueError(f"SVG generation failed: {e}")

    def _calculate_time_range(self):
        """Determine the date range based on time_frames and tasks."""
        if not (self.data["time_frames"] or self.data["tasks"]):
            return datetime.now(), datetime.now() + timedelta(days=7)

        dates = []
        for tf in self.data["time_frames"]:
            dates.append(datetime.strptime(tf["start_date"], "%Y-%m-%d"))
            dates.append(datetime.strptime(tf["end_date"], "%Y-%m-%d"))
        for task in self.data["tasks"]:
            if task["start"]:
                start = datetime.strptime(task["start"], "%Y-%m-%d")
                dates.append(start)
                if task["duration"]:
                    end = start + timedelta(days=float(task["duration"]))
                    dates.append(end)

        if not dates:
            return datetime.now(), datetime.now() + timedelta(days=7)

        min_date = min(dates)
        max_date = max(dates)
        return min_date - timedelta(days=1), max_date + timedelta(days=1)

    def _set_time_scale(self):
        """Calculate pixels per day based on the time range."""
        start_date, end_date = self._calculate_time_range()
        total_days = (end_date - start_date).days
        margins = self.data["frame_config"]["margins"]
        chart_width = self.data["frame_config"]["outer_width"] - margins[1] - margins[3]
        self.time_scale = chart_width / total_days if total_days > 0 else 1
        return start_date, end_date

    def render_time_scale(self):
        """Draw the time scale at the top of the chart."""
        start_date, end_date = self._set_time_scale()
        margins = self.data["frame_config"]["margins"]
        y = margins[0] + self.data["frame_config"]["header_height"] - 20
        current_date = start_date

        while current_date <= end_date:
            x = margins[3] + (current_date - start_date).days * self.time_scale
            self.dwg.add(self.dwg.line((x, y), (x, self.data["frame_config"]["outer_height"] - margins[2]),
                                      stroke="gray", stroke_width=0.5))
            if (current_date - start_date).days % 5 == 0:
                self.dwg.add(self.dwg.text(
                    current_date.strftime("%Y-%m-%d"),
                    insert=(x, y - 5),
                    text_anchor="middle",
                    font_size="10"
                ))
            current_date += timedelta(days=1)

    def render_layout(self):
        """Render the outer frame, header, footer, and time frames."""
        margins = self.data["frame_config"]["margins"]
        width = self.data["frame_config"]["outer_width"]
        height = self.data["frame_config"]["outer_height"]

        # Outer frame (boundary)
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(width, height), fill="white", stroke="black"))

        # Header frame
        self.dwg.add(self.dwg.rect(insert=(margins[3], margins[0]),
                                  size=(width - margins[1] - margins[3], self.data["frame_config"]["header_height"]),
                                  fill="lightgray"))

        # Footer frame
        footer_y = height - self.data["frame_config"]["footer_height"] - margins[2]
        self.dwg.add(self.dwg.rect(insert=(margins[3], footer_y),
                                  size=(width - margins[1] - margins[3], self.data["frame_config"]["footer_height"]),
                                  fill="lightgray"))

        # Time frames
        inner_y = margins[0] + self.data["frame_config"]["header_height"]
        inner_width = width - margins[1] - margins[3]
        inner_height = height - self.data["frame_config"]["header_height"] - self.data["frame_config"]["footer_height"] - margins[0] - margins[2]
        x_offset = margins[3]
        for tf in self.data["time_frames"]:
            tf_width = inner_width * tf["width_proportion"]
            self.dwg.add(self.dwg.rect(insert=(x_offset, inner_y), size=(tf_width, inner_height), fill="none", stroke="blue"))
            x_offset += tf_width

    def render_tasks(self):
        """Render task bars based on start date and duration."""
        start_date, _ = self._set_time_scale()
        margins = self.data["frame_config"]["margins"]
        inner_y = margins[0] + self.data["frame_config"]["header_height"]
        inner_height = self.data["frame_config"]["outer_height"] - self.data["frame_config"]["header_height"] - self.data["frame_config"]["footer_height"] - margins[0] - margins[2]
        row_height = inner_height / max(1, len(self.data["tasks"]))

        for i, task in enumerate(self.data["tasks"]):
            name = task["name"] or f"Task {i + 1}"
            start = task["start"]
            duration = float(task["duration"]) if task["duration"] else 0

            self.dwg.add(self.dwg.text(
                name,
                insert=(5, inner_y + (i + 0.5) * row_height + 5),
                font_size="12"
            ))

            if start and duration:
                start_dt = datetime.strptime(start, "%Y-%m-%d")
                x = margins[3] + (start_dt - start_date).days * self.time_scale
                width = duration * self.time_scale
                y = inner_y + i * row_height
                self.dwg.add(self.dwg.rect(
                    insert=(x, y),
                    size=(width, row_height * 0.8),
                    fill="blue"
                ))

    def render(self):
        """Render the full Gantt chart."""
        os.makedirs(self.output_folder, exist_ok=True)
        self.render_layout()
        self.render_tasks()
        self.render_time_scale()
        self.dwg.save()
        print(f"SVG saved to: {os.path.join(self.output_folder, self.output_filename)}")