"""
Purpose: Generates an SVG Gantt chart from ProjectData.
Why: Visualizes tasks, pipes, and curtains with a time scale for project planning.
"""


import svgwrite
from datetime import datetime, timedelta
import os
from PyQt5.QtCore import QObject, pyqtSignal  # Ensure correct import
from config import Config


class GanttChartGenerator(QObject):
    svg_generated = pyqtSignal(str)  # Signal to emit the SVG file path

    def __init__(self, width=Config.SVG_WIDTH, height=Config.SVG_HEIGHT, output_folder=Config.SVG_OUTPUT_FOLDER, output_filename=Config.SVG_OUTPUT_FILENAME):
        """Initialize the Gantt chart generator with dimensions."""
        super().__init__()
        self.width = width
        self.height = height
        self.output_folder = output_folder
        self.output_filename = output_filename
        self.dwg = None  # Initialized in generate_svg
        self.margin = 50
        self.row_height = 30
        self.time_scale = None
        self.data = {"tasks": [], "pipes": [], "curtains": []}  # Default empty data

    def generate_svg(self, data):
        """Generate the SVG Gantt chart from the provided data."""
        try:
            self.data = {  # Update data instead of defining it
                "tasks": data.get("tasks", []),
                "pipes": data.get("pipes", []),
                "curtains": data.get("curtains", [])
            }
            self.dwg = svgwrite.Drawing(filename=os.path.join(self.output_folder, self.output_filename), size=(self.width, self.height))
            self.render()
            # svg_path = os.path.join(self.output_folder, self.output_filename)
            svg_path = os.path.abspath(os.path.join(self.output_folder, self.output_filename))  # Use absolute path
            self.svg_generated.emit(svg_path)  # Emit signal with the SVG file path
            return svg_path
        except Exception as e:
            raise ValueError(f"SVG generation failed: {e}")


    def _calculate_time_range(self):
        """Determine the date range based on tasks, pipes, and curtains."""
        if not (self.data["tasks"] or self.data["pipes"] or self.data["curtains"]):
            return datetime.now(), datetime.now() + timedelta(days=7)

        dates = []
        for task in self.data["tasks"]:
            if task["start"]:
                start = datetime.strptime(task["start"], "%Y-%m-%d")
                dates.append(start)
                if task["duration"]:
                    end = start + timedelta(days=float(task["duration"]))
                    dates.append(end)
        for pipe in self.data["pipes"]:
            if pipe["date"]:
                dates.append(datetime.strptime(pipe["date"], "%Y-%m-%d"))
        for curtain in self.data["curtains"]:
            if curtain["start_date"]:
                dates.append(datetime.strptime(curtain["start_date"], "%Y-%m-%d"))
            if curtain["end_date"]:
                dates.append(datetime.strptime(curtain["end_date"], "%Y-%m-%d"))

        if not dates:
            return datetime.now(), datetime.now() + timedelta(days=7)

        min_date = min(dates)
        max_date = max(dates)
        return min_date - timedelta(days=1), max_date + timedelta(days=1)

    def _set_time_scale(self):
        """Calculate pixels per day based on the time range."""
        start_date, end_date = self._calculate_time_range()
        total_days = (end_date - start_date).days
        chart_width = self.width - 2 * self.margin
        self.time_scale = chart_width / total_days if total_days > 0 else 1
        return start_date, end_date

    def render_time_scale(self):
        """Draw the time scale at the top of the chart."""
        start_date, end_date = self._set_time_scale()
        current_date = start_date
        y = self.margin - 20

        while current_date <= end_date:
            x = self.margin + (current_date - start_date).days * self.time_scale
            self.dwg.add(self.dwg.line((x, y), (x, self.height - self.margin), stroke="gray", stroke_width=0.5))
            if (current_date - start_date).days % 5 == 0:
                self.dwg.add(self.dwg.text(
                    current_date.strftime("%Y-%m-%d"),
                    insert=(x, y - 5),
                    text_anchor="middle",
                    font_size="10"
                ))
            current_date += timedelta(days=1)

    def render_tasks(self):
        """Render task bars based on start date and duration."""
        start_date, _ = self._set_time_scale()
        y_offset = self.margin

        for i, task in enumerate(self.data["tasks"]):
            name = task["name"] or f"Task {i + 1}"
            start = task["start"]
            duration = float(task["duration"]) if task["duration"] else 0

            self.dwg.add(self.dwg.text(
                name,
                insert=(5, y_offset + self.row_height // 2 + 5),
                font_size="12"
            ))

            if start and duration:
                start_dt = datetime.strptime(start, "%Y-%m-%d")
                x = self.margin + (start_dt - start_date).days * self.time_scale
                width = duration * self.time_scale
                self.dwg.add(self.dwg.rect(
                    insert=(x, y_offset),
                    size=(width, self.row_height),
                    fill="blue"
                ))

            y_offset += self.row_height

    def render_pipes(self):
        """Render vertical dashed lines for pipes."""
        start_date, _ = self._set_time_scale()
        y_top = self.margin - 20
        y_bottom = self.height - self.margin

        for i, pipe in enumerate(self.data["pipes"]):
            name = pipe["name"] or f"Pipe {i + 1}"
            date = pipe["date"]

            if date:
                date_dt = datetime.strptime(date, "%Y-%m-%d")
                x = self.margin + (date_dt - start_date).days * self.time_scale
                self.dwg.add(self.dwg.line(
                    (x, y_top),
                    (x, y_bottom),
                    stroke="red",
                    stroke_width=1,
                    stroke_dasharray="4,4"
                ))
                self.dwg.add(self.dwg.text(
                    name,
                    insert=(x, y_top - 5),
                    text_anchor="middle",
                    font_size="10",
                    fill="red"
                ))

    def render_curtains(self):
        """Render shaded areas between start and end dates."""
        start_date, _ = self._set_time_scale()
        y_top = self.margin
        y_bottom = self.height - self.margin

        for i, curtain in enumerate(self.data["curtains"]):
            name = curtain["name"] or f"Curtain {i + 1}"
            start_date_str = curtain.get("start_date", "")
            end_date_str = curtain.get("end_date", "")
            color = curtain.get("color", "gray")

            if not start_date_str or not end_date_str:
                continue

            try:
                start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
                x_start = self.margin + (start_dt - start_date).days * self.time_scale
                width = (end_dt - start_dt).days * self.time_scale

                x_start = max(self.margin, min(x_start, self.width - self.margin))
                width = max(1, min(width, self.width - x_start - self.margin))

                if width >= 0:
                    self.dwg.add(self.dwg.rect(
                        insert=(x_start, y_top),
                        size=(width, y_bottom - y_top),
                        fill=color
                    ))
                    self.dwg.add(self.dwg.text(
                        name,
                        insert=(x_start + width / 2, (y_top + y_bottom) / 2),
                        text_anchor="middle",
                        font_size="12",
                        fill="black"
                    ))
            except ValueError:
                pass  # Silently skip invalid dates

    def render(self):
        """Render the full Gantt chart."""
        os.makedirs(self.output_folder, exist_ok=True)
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(self.width, self.height), fill="white"))
        self.render_curtains()
        self.render_tasks()
        self.render_pipes()
        self.render_time_scale()
        self.dwg.save()
        print(f"SVG saved to: {os.path.join(self.output_folder, self.output_filename)}")  # Added for feedback

def generate_svg(data, output_folder="svg", output_filename="gantt_chart.svg"):
    """Legacy function for compatibility."""
    generator = GanttChartGenerator(output_folder=output_folder, output_filename=output_filename)
    return generator.generate_svg(data)
