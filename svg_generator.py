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
        self.data = {"frame_config": {}, "time_frames": [], "tasks": []}
        self.start_date = None

    @pyqtSlot(dict)
    def generate_svg(self, data):
        try:
            self.data = data
            width = self.data["frame_config"].get("outer_width", 800)
            height = self.data["frame_config"].get("outer_height", 600)
            self.dwg = svgwrite.Drawing(filename=os.path.abspath(os.path.join(self.output_folder, self.output_filename)),
                                        size=(width, height))
            self.start_date = self._set_time_scale()
            self.render()
            svg_path = os.path.abspath(os.path.join(self.output_folder, self.output_filename))
            self.svg_generated.emit(svg_path)
            return svg_path
        except Exception as e:
            print(f"SVG generation failed: {e}")
            raise ValueError(f"SVG generation failed: {e}")

    def _calculate_time_range(self):
        dates = []
        for task in self.data.get("tasks", []):
            start_date_str = task["start_date"]
            finish_date_str = task["finish_date"]
            if start_date_str:
                try:
                    dates.append(datetime.strptime(start_date_str, "%Y-%m-%d"))
                except ValueError:
                    pass  # Skip invalid dates
            if finish_date_str:
                try:
                    dates.append(datetime.strptime(finish_date_str, "%Y-%m-%d"))
                except ValueError:
                    pass  # Skip invalid dates

        if not dates:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return today, today + timedelta(days=30)
        return min(dates), max(dates)

    def _set_time_scale(self):
        start_date, _ = self._calculate_time_range()
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

    def render_tasks(self, x, y, width, height, start_date, end_date, num_rows):
        total_days = max((end_date - start_date).days, 1)
        tf_time_scale = width / total_days if total_days > 0 else width
        row_height = height / num_rows if num_rows > 0 else height
        task_height = row_height * 0.8

        for task in self.data.get("tasks", []):
            start_date_str = task["start_date"]
            finish_date_str = task["finish_date"]
            is_milestone = task.get("is_milestone", False)
            if not start_date_str and not finish_date_str:
                continue

            date_to_use = start_date_str if start_date_str else finish_date_str
            task_start = datetime.strptime(date_to_use, "%Y-%m-%d")
            task_finish = task_start
            if not is_milestone and start_date_str and finish_date_str:
                task_start = datetime.strptime(start_date_str, "%Y-%m-%d")
                task_finish = datetime.strptime(finish_date_str, "%Y-%m-%d")

            if task_finish < start_date or task_start > end_date:
                continue
            row_num = min(max(task.get("row_number", 1) - 1, 0), num_rows - 1)
            x_start = x + max((task_start - start_date).days, 0) * tf_time_scale
            x_end = x + min((task_finish - start_date).days, total_days) * tf_time_scale
            width_task = tf_time_scale if task_start == task_finish else max(x_end - x_start, tf_time_scale)
            y_task = y + row_num * row_height

            if is_milestone:
                half_size = task_height / 2
                center_x = x_start
                center_y = y_task + row_height * 0.5
                for other_task in self.data.get("tasks", []):
                    if other_task["row_number"] == task["row_number"] and other_task != task:
                        other_start_str = other_task["start_date"]
                        other_finish_str = other_task["finish_date"]
                        other_date = other_start_str if other_start_str else other_finish_str
                        other_start = datetime.strptime(other_date, "%Y-%m-%d")
                        other_finish = other_start
                        if not other_task.get("is_milestone", False) and other_start_str and other_finish_str:
                            other_start = datetime.strptime(other_start_str, "%Y-%m-%d")
                            other_finish = datetime.strptime(other_finish_str, "%Y-%m-%d")
                        if task_start == other_start:
                            center_x = x_start + half_size
                            break
                        elif task_start == other_finish:
                            center_x = x_end - half_size
                            break
                points = [
                    (center_x, center_y - half_size),  # Top
                    (center_x + half_size, center_y),  # Right
                    (center_x, center_y + half_size),  # Bottom
                    (center_x - half_size, center_y)   # Left
                ]
                self.dwg.add(self.dwg.polygon(points=points, fill="red", stroke="black", stroke_width=1))
                self.dwg.add(self.dwg.text(task.get("task_name", "Unnamed"),
                                           insert=(center_x + half_size + 5, center_y),
                                           font_size="10", fill="black"))
            else:
                if x_start < x + width:
                    self.dwg.add(self.dwg.rect(insert=(x_start, y_task), size=(width_task, task_height),
                                               fill="blue"))
                    self.dwg.add(self.dwg.text(task.get("task_name", "Unnamed"),
                                               insert=(x_start + 5, y_task + task_height * 0.4),
                                               font_size="10", fill="white"))

    def render_scales_and_rows(self, x, y, width, height, start_date, end_date):
        total_days = max((end_date - start_date).days, 1)
        tf_time_scale = width / total_days if total_days > 0 else width

        scale_configs = [
            ("years", Config.SCALE_PROPORTION_YEARS),
            ("months", Config.SCALE_PROPORTION_MONTHS),
            ("weeks", Config.SCALE_PROPORTION_WEEKS),
            ("days", Config.SCALE_PROPORTION_DAYS)
        ]
        row_frame_proportion = 1.0
        total_scale_proportion = sum(p for _, p in scale_configs)
        total_height_units = row_frame_proportion + total_scale_proportion
        row_frame_height = height * (row_frame_proportion / total_height_units)
        scale_heights = [(interval, height * (proportion / total_height_units)) for interval, proportion in scale_configs]

        current_y = y
        for interval, scale_height in scale_heights:
            self.dwg.add(self.dwg.rect(insert=(x, current_y), size=(width, scale_height),
                                       fill="lightgrey", stroke="black", stroke_width=1))
            self.render_scale_interval(x, current_y, width, scale_height, start_date, end_date, interval, tf_time_scale)
            current_y += scale_height

        row_y = current_y
        num_rows = self.data["frame_config"].get("num_rows", 1)
        self.dwg.add(self.dwg.rect(insert=(x, row_y), size=(width, row_frame_height),
                                   fill="none", stroke="purple", stroke_width=1))

        if self.data["frame_config"].get("horizontal_gridlines", False):
            for i in range(num_rows + 1):
                y_pos = row_y + i * (row_frame_height / num_rows)
                self.dwg.add(self.dwg.line((x, y_pos), (x + width, y_pos), stroke="gray", stroke_width=1))

        if self.data["frame_config"].get("vertical_gridlines", False):
            for interval, _ in scale_configs:
                current_date = self.next_period(start_date, interval)
                while current_date <= end_date:
                    x_pos = x + (current_date - start_date).days * tf_time_scale
                    if x <= x_pos <= x + width:
                        self.dwg.add(self.dwg.line((x_pos, row_y), (x_pos, row_y + row_frame_height),
                                                   stroke="gray", stroke_width=1))
                    current_date = self.next_period(current_date, interval)

        self.render_tasks(x, row_y, width, row_frame_height, start_date, end_date, num_rows)

    def next_period(self, date, interval):
        if interval == "days":
            return date + timedelta(days=1)
        elif interval == "weeks":
            days_to_monday = (7 - date.weekday()) % 7 or 7
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
        year, week_num, weekday = date.isocalendar()
        jan1 = datetime(year, 1, 1)
        days_to_thursday = (3 - jan1.weekday()) % 7
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
            if x <= x_pos <= x + width and interval_width >= Config.MIN_INTERVAL_WIDTH:
                self.dwg.add(self.dwg.line((x_pos, y), (x_pos, y + height),
                                           stroke="black", stroke_width=1))
            if prev_x < x + width and x_pos > x:
                label_x = (max(x, prev_x) + min(x + width, x_pos)) / 2
                label_y = y + height / 2
                label = ""
                if interval == "years":
                    if interval_width >= Config.FULL_LABEL_WIDTH:
                        label = current_date.strftime("%Y")
                    elif interval_width >= Config.SHORT_LABEL_WIDTH:
                        label = current_date.strftime("%y")
                elif interval == "months":
                    if interval_width >= Config.FULL_LABEL_WIDTH:
                        label = current_date.strftime("%b")
                    elif interval_width >= Config.SHORT_LABEL_WIDTH:
                        label = current_date.strftime("%b")[0]
                elif interval == "weeks":
                    week_num = current_date.isocalendar()[1]
                    week_end = self.get_week_end_date(current_date)
                    if interval_width >= Config.FULL_LABEL_WIDTH:
                        label = f"{week_num:02d} ({week_end.strftime('%d')})"
                    elif interval_width >= Config.SHORT_LABEL_WIDTH:
                        label = f"{week_num:02d}"
                elif interval == "days":
                    if interval_width >= Config.FULL_LABEL_WIDTH:
                        label = current_date.strftime("%a")
                    elif interval_width >= Config.SHORT_LABEL_WIDTH:
                        label = current_date.strftime("%a")[0]
                if label:
                    self.dwg.add(self.dwg.text(label, insert=(label_x, label_y), text_anchor="middle",
                                               font_size="10", dominant_baseline="middle"))
            prev_x = x_pos
            current_date = next_date

    def render(self):
        os.makedirs(self.output_folder, exist_ok=True)
        self.start_date = self._set_time_scale()
        self.render_outer_frame()
        self.render_header()
        self.render_footer()
        self.render_inner_frame()
        self.render_time_frames()
        self.dwg.save()