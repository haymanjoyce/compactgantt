import svgwrite
from datetime import datetime, timedelta
import calendar
import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from config import Config

class GanttChartGenerator(QObject):
    svg_generated = pyqtSignal(str)

    def __init__(self, output_folder: str = Config.SVG_OUTPUT_FOLDER,
                 output_filename: str = Config.SVG_OUTPUT_FILENAME):
        super().__init__()
        self.output_folder = output_folder
        self.output_filename = output_filename
        self.dwg = None
        self.data = {"frame_config": {}, "time_frames": [], "tasks": []}  # type: dict
        self.start_date = None

    def generate_svg(self, data):
        try:
            self.data = data
            print("Data received:", self.data)
            width = self.data["frame_config"].get("outer_width", 800)
            height = self.data["frame_config"].get("outer_height", 600)
            self.dwg = svgwrite.Drawing(filename=os.path.abspath(os.path.join(self.output_folder, self.output_filename)),
                                        size=(width, height))
            self.start_date = self._set_time_scale()
            print("Start date set:", self.start_date)
            self.render()
            svg_path = os.path.abspath(os.path.join(self.output_folder, self.output_filename))
            print("SVG path:", svg_path)
            self.svg_generated.emit(svg_path)
            return svg_path
        except Exception as e:
            print(f"SVG generation failed: {e}")
            raise ValueError(f"SVG generation failed: {e}")

    def _calculate_time_range(self):
        if not (self.data["time_frames"] or self.data["tasks"]):
            return datetime.now(), datetime.now() + timedelta(days=7)
        dates = [datetime.strptime(self.data["frame_config"]["chart_start_date"], "%Y-%m-%d")]
        for tf in self.data.get("time_frames", []):
            dates.append(datetime.strptime(tf["finish_date"], "%Y-%m-%d"))
        for task in self.data.get("tasks", []):
            dates.append(datetime.strptime(task["start_date"], "%Y-%m-%d"))
            dates.append(datetime.strptime(task["finish_date"], "%Y-%m-%d"))
        if len(dates) == 1:
            return dates[0], dates[0] + timedelta(days=7)
        return min(dates), max(dates) + timedelta(days=1)

    def _set_time_scale(self):
        start_date, _ = self._calculate_time_range()
        print("Time range:", start_date, _)
        return start_date

    def render_outer_frame(self):
        width = self.data["frame_config"].get("outer_width", 800)
        height = self.data["frame_config"].get("outer_height", 600)
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(width, height), fill="white", stroke="black", stroke_width=2))

    def render_header(self):
        margins = self.data["frame_config"].get("margins", (10, 10, 10, 10))
        width = self.data["frame_config"].get("outer_width", 800) - margins[1] - margins[3]
        height = self.data["frame_config"].get("header_height", 50)
        self.dwg.add(self.dwg.rect(insert=(margins[3], margins[0]), size=(width, height),
                                   fill="lightgray", stroke="black", stroke_width=1))
        header_text = self.data["frame_config"].get("header_text", "")
        if header_text:
            self.dwg.add(self.dwg.text(header_text,
                                       insert=(margins[3] + width / 2, margins[0] + height / 2),
                                       text_anchor="middle", font_size="14"))

    def render_footer(self):
        margins = self.data["frame_config"].get("margins", (10, 10, 10, 10))
        width = self.data["frame_config"].get("outer_width", 800) - margins[1] - margins[3]
        height = self.data["frame_config"].get("footer_height", 50)
        y = self.data["frame_config"].get("outer_height", 600) - margins[2] - height
        self.dwg.add(self.dwg.rect(insert=(margins[3], y), size=(width, height),
                                   fill="lightgray", stroke="black", stroke_width=1))
        footer_text = self.data["frame_config"].get("footer_text", "")
        if footer_text:
            self.dwg.add(self.dwg.text(footer_text,
                                       insert=(margins[3] + width / 2, y + height / 2),
                                       text_anchor="middle", font_size="14"))

    def render_inner_frame(self):
        margins = self.data["frame_config"].get("margins", (10, 10, 10, 10))
        width = self.data["frame_config"].get("outer_width", 800) - margins[1] - margins[3]
        y = margins[0] + self.data["frame_config"].get("header_height", 50)
        height = (self.data["frame_config"].get("outer_height", 600) -
                  self.data["frame_config"].get("header_height", 50) -
                  self.data["frame_config"].get("footer_height", 50) - margins[0] - margins[2])
        self.dwg.add(self.dwg.rect(insert=(margins[3], y), size=(width, height),
                                   fill="none", stroke="blue", stroke_width=1, stroke_dasharray="4"))

    def render_time_frames(self):
        margins = self.data["frame_config"].get("margins", (10, 10, 10, 10))
        inner_y = margins[0] + self.data["frame_config"].get("header_height", 50)
        inner_width = self.data["frame_config"].get("outer_width", 800) - margins[1] - margins[3]
        inner_height = (self.data["frame_config"].get("outer_height", 600) -
                        self.data["frame_config"].get("header_height", 50) -
                        self.data["frame_config"].get("footer_height", 50) - margins[0] - margins[2])
        x_offset = margins[3]
        chart_start = datetime.strptime(self.data["frame_config"]["chart_start_date"], "%Y-%m-%d")
        prev_end = chart_start

        for tf in self.data.get("time_frames", []):
            tf_width = inner_width * tf.get("width_proportion", 1.0)
            tf_end = datetime.strptime(tf["finish_date"], "%Y-%m-%d")
            self.dwg.add(self.dwg.rect(insert=(x_offset, inner_y), size=(tf_width, inner_height),
                                       fill="none", stroke="red", stroke_width=1))
            self.render_scales_and_rows(x_offset, inner_y, tf_width, inner_height, prev_end, tf_end)
            x_offset += tf_width
            prev_end = tf_end + timedelta(days=1)

    def render_tasks(self):
        pass

    def render_scales_and_rows(self, x, y, width, height, start_date, end_date):
        total_days = max((end_date - start_date).days, 1)
        tf_time_scale = width / total_days if total_days > 0 else width

        # Define all scales and their proportions relative to row_frame
        scale_configs = [
            ("years", Config.SCALE_PROPORTION_YEARS),
            ("months", Config.SCALE_PROPORTION_MONTHS),
            ("weeks", Config.SCALE_PROPORTION_WEEKS),
            ("days", Config.SCALE_PROPORTION_DAYS)
        ]

        # Keep all scales active (no dropping)
        active_scales = scale_configs

        # Calculate heights: row_frame gets 1 unit, scales get their proportions relative to it
        row_frame_proportion = 1.0
        total_scale_proportion = sum(p for _, p in active_scales)
        total_height_units = row_frame_proportion + total_scale_proportion
        row_frame_height = height * (row_frame_proportion / total_height_units)
        scale_heights = [(interval, height * (proportion / total_height_units)) for interval, proportion in active_scales]

        # Render scales
        current_y = y
        for interval, scale_height in scale_heights:
            self.dwg.add(self.dwg.rect(insert=(x, current_y), size=(width, scale_height),
                                       fill="lightgrey", stroke="black", stroke_width=1))
            self.render_scale_interval(x, current_y, width, scale_height, start_date, end_date, interval, tf_time_scale)
            current_y += scale_height

        # Row Frame
        row_y = current_y
        num_rows = self.data["frame_config"].get("num_rows", 1)
        row_height = row_frame_height / num_rows if num_rows > 0 else row_frame_height
        self.dwg.add(self.dwg.rect(insert=(x, row_y), size=(width, row_frame_height),
                                   fill="none", stroke="purple", stroke_width=1))

        # Render tasks
        for task in self.data.get("tasks", []):
            task_start = datetime.strptime(task["start_date"], "%Y-%m-%d")
            task_finish = datetime.strptime(task["finish_date"], "%Y-%m-%d")
            if not (task_finish < start_date or task_start > end_date):
                row_num = min(task.get("row_number", 1) - 1, num_rows - 1)
                x_start = x + max((task_start - start_date).days, 0) * tf_time_scale
                x_end = x + min((task_finish - start_date).days, total_days) * tf_time_scale
                width_task = max(x_end - x_start, 0)
                y_task = row_y + row_num * row_height
                if width_task > 0 and x_start < x + width:
                    self.dwg.add(self.dwg.rect(insert=(x_start, y_task), size=(width_task, row_height * 0.8), fill="blue"))
                    self.dwg.add(self.dwg.text(task.get("task_name", "Unnamed"),
                                               insert=(x_start + 5, y_task + row_height * 0.4),
                                               font_size="10", fill="white"))

        # Row frame gridlines
        if self.data["frame_config"].get("horizontal_gridlines", False):
            for i in range(num_rows + 1):
                y_pos = row_y + i * row_height
                self.dwg.add(self.dwg.line((x, y_pos), (x + width, y_pos), stroke="gray", stroke_width=1))

        if self.data["frame_config"].get("vertical_gridlines", False):
            for interval, _ in active_scales:
                current_date = start_date
                current_date = self.next_period(current_date, interval)
                while current_date <= end_date:
                    x_pos = x + (current_date - start_date).days * tf_time_scale
                    if x <= x_pos <= x + width:
                        self.dwg.add(self.dwg.line((x_pos, row_y), (x_pos, row_y + row_frame_height),
                                                   stroke="gray", stroke_width=1))
                    current_date = self.next_period(current_date, interval)

    def next_period(self, date, interval):
        if interval == "days":
            return date + timedelta(days=1)
        elif interval == "weeks":
            days_to_monday = (7 - date.weekday()) % 7 or 7  # Move to next Monday
            return date + timedelta(days=days_to_monday)
        elif interval == "months":
            year, month = date.year, date.month + 1
            if month > 12:
                month = 1
                year += 1
            return datetime(year, month, 1)
        elif interval == "years":
            return datetime(date.year + 1, 1, 1)
        return date

    def get_week_end_date(self, date):
        """Calculate the Sunday end date for the ISO week containing the given date."""
        year, week_num, weekday = date.isocalendar()
        jan1 = datetime(year, 1, 1)
        days_to_thursday = (3 - jan1.weekday()) % 7  # Thursday is weekday 3 (0=Mon)
        first_thursday = jan1 + timedelta(days=days_to_thursday)
        week1_start = first_thursday - timedelta(days=3)
        week_start = week1_start + timedelta(days=(week_num - 1) * 7)
        return week_start + timedelta(days=6)

    def render_scale_interval(self, x, y, width, height, start_date, end_date, interval, tf_time_scale):
        current_date = start_date
        prev_x = x
        while current_date <= end_date:
            next_date = self.next_period(current_date, interval)
            x_pos = x + (next_date - start_date).days * tf_time_scale
            interval_width = x_pos - prev_x if x_pos <= x + width else (x + width) - prev_x
            # Draw vertical line only if interval_width >= MIN_INTERVAL_WIDTH and within time_frame
            if x <= x_pos <= x + width and interval_width >= Config.MIN_INTERVAL_WIDTH:
                self.dwg.add(self.dwg.line((x_pos, y), (x_pos, y + height),
                                           stroke="black", stroke_width=1))
            # Label if interval intersects time_frame
            if prev_x < x + width and x_pos > x:
                label_x = (max(x, prev_x) + min(x + width, x_pos)) / 2
                label_y = y + height / 2
                label = ""
                if interval == "years":
                    if interval_width >= Config.FULL_LABEL_WIDTH:
                        label = current_date.strftime("%Y")
                    elif interval_width >= Config.SHORT_LABEL_WIDTH:
                        label = current_date.strftime("%y")
                    elif interval_width >= Config.MIN_INTERVAL_WIDTH:
                        label = ""
                elif interval == "months":
                    if interval_width >= Config.FULL_LABEL_WIDTH:
                        label = current_date.strftime("%b")
                    elif interval_width >= Config.SHORT_LABEL_WIDTH:
                        label = current_date.strftime("%b")[0]
                    elif interval_width >= Config.MIN_INTERVAL_WIDTH:
                        label = ""
                elif interval == "weeks":
                    week_num = current_date.isocalendar()[1]
                    week_end = self.get_week_end_date(current_date)
                    if interval_width >= Config.FULL_LABEL_WIDTH:
                        label = f"{week_num:02d} ({week_end.strftime('%d')})"
                    elif interval_width >= Config.SHORT_LABEL_WIDTH:
                        label = f"{week_num:02d}"
                    elif interval_width >= Config.MIN_INTERVAL_WIDTH:
                        label = ""
                elif interval == "days":
                    if interval_width >= Config.FULL_LABEL_WIDTH:
                        label = current_date.strftime("%a")
                    elif interval_width >= Config.SHORT_LABEL_WIDTH:
                        label = current_date.strftime("%a")[0]
                    elif interval_width >= Config.MIN_INTERVAL_WIDTH:
                        label = ""
                if label:
                    self.dwg.add(self.dwg.text(label, insert=(label_x, label_y), text_anchor="middle",
                                               font_size="10", dominant_baseline="middle"))
            prev_x = x_pos
            current_date = next_date

    def render(self):
        os.makedirs(self.output_folder, exist_ok=True)
        self.start_date = self._set_time_scale()
        print("Starting render")
        self.render_outer_frame()
        self.render_header()
        self.render_footer()
        self.render_inner_frame()
        self.render_time_frames()
        self.render_tasks()
        self.dwg.save()
        print(f"SVG saved to: {os.path.join(self.output_folder, self.output_filename)}")