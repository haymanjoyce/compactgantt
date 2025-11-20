# File: gantt_chart_service.py
import svgwrite
from datetime import datetime, timedelta
import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QFontMetrics
from config.app_config import AppConfig
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GanttChartService(QObject):
    svg_generated = pyqtSignal(str)

    def __init__(self, output_folder: str = None, output_filename: str = None):
        super().__init__()
        self.config = AppConfig()
        self.output_folder = output_folder or self.config.general.svg_output_folder
        self.output_filename = output_filename or self.config.general.svg_output_filename
        self.dwg = None
        self.data = {"frame_config": {}, "time_frames": [], "tasks": []}
        self.start_date = None
        self.font = QFont("Arial", 10)
        self.font_metrics = QFontMetrics(self.font)
        logging.debug("GanttChartService initialized")

    @pyqtSlot(dict)
    def generate_svg(self, data):
        logging.debug("Starting generate_svg")
        if not data or "frame_config" not in data:
            logging.warning("Skipping SVG generation: Invalid or empty data")
            self.svg_generated.emit("")
            return
        try:
            self.data = data
            width = data["frame_config"].get("outer_width", self.config.general.outer_width)
            height = data["frame_config"].get("outer_height", self.config.general.outer_height)
            self.dwg = svgwrite.Drawing(
                filename=os.path.abspath(os.path.join(self.output_folder, self.output_filename)),
                size=(width, height))
            self.start_date = self._set_time_scale()
            self.render()
            svg_path = os.path.abspath(os.path.join(self.output_folder, self.output_filename))
            logging.debug(f"SVG generated at: {svg_path}")
            self.svg_generated.emit(svg_path)
            return svg_path
        except Exception as e:
            logging.error(f"SVG generation failed: {e}", exc_info=True)
            self.svg_generated.emit("")
            return

    def _calculate_time_range(self):
        logging.debug("Calculating time range")
        dates = []
        for task in self.data.get("tasks", []):
            start_date_str = task.get("start_date", "")
            finish_date_str = task.get("finish_date", "")
            if start_date_str:
                try:
                    dates.append(datetime.strptime(start_date_str, "%Y-%m-%d"))
                except (ValueError, TypeError):
                    pass
            if finish_date_str:
                try:
                    dates.append(datetime.strptime(finish_date_str, "%Y-%m-%d"))
                except (ValueError, TypeError):
                    pass

        if not dates:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return today, today + timedelta(days=30)
        return min(dates), max(dates) + timedelta(days=1)

    def _set_time_scale(self):
        start_date, _ = self._calculate_time_range()
        logging.debug(f"Time scale set with start_date: {start_date}")
        return start_date

    def render_outer_frame(self):
        width = self.data["frame_config"].get("outer_width", self.config.general.outer_width)
        height = self.data["frame_config"].get("outer_height", self.config.general.outer_height)
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(width, height), fill="white", stroke="black", stroke_width=2))
        logging.debug("Outer frame rendered")

    def render_header(self):
        margins = self.data["frame_config"].get("margins", (10, 10, 10, 10))
        width = self.data["frame_config"].get("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        height = self.data["frame_config"].get("header_height", 50)
        self.dwg.add(self.dwg.rect(insert=(margins[3], margins[0]), size=(width, height),
                                   fill="lightgray", stroke="black", stroke_width=1))
        header_text = self.data["frame_config"].get("header_text", "")
        if header_text:
            self.dwg.add(self.dwg.text(header_text,
                                       insert=(margins[3] + width / 2, margins[0] + height / 2),
                                       text_anchor="middle", font_size="14"))
        logging.debug("Header rendered")

    def render_footer(self):
        margins = self.data["frame_config"].get("margins", (10, 10, 10, 10))
        width = self.data["frame_config"].get("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        height = self.data["frame_config"].get("footer_height", 50)
        y = self.data["frame_config"].get("outer_height", self.config.general.outer_height) - margins[2] - height
        self.dwg.add(self.dwg.rect(insert=(margins[3], y), size=(width, height),
                                   fill="lightgray", stroke="black", stroke_width=1))
        footer_text = self.data["frame_config"].get("footer_text", "")
        if footer_text:
            self.dwg.add(self.dwg.text(footer_text,
                                       insert=(margins[3] + width / 2, y + height / 2),
                                       text_anchor="middle", font_size="14"))
        logging.debug("Footer rendered")

    def render_inner_frame(self):
        margins = self.data["frame_config"].get("margins", (10, 10, 10, 10))
        width = self.data["frame_config"].get("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        y = margins[0] + self.data["frame_config"].get("header_height", 50)
        height = (self.data["frame_config"].get("outer_height", self.config.general.outer_height) -
                  self.data["frame_config"].get("header_height", 50) -
                  self.data["frame_config"].get("footer_height", 50) - margins[0] - margins[2])
        self.dwg.add(self.dwg.rect(insert=(margins[3], y), size=(width, height),
                                   fill="none", stroke="blue", stroke_width=1, stroke_dasharray="4"))
        logging.debug("Inner frame rendered")

    def render_time_frames(self):
        logging.debug("Starting render_time_frames")
        margins = self.data["frame_config"].get("margins", (10, 10, 10, 10))
        inner_y = margins[0] + self.data["frame_config"].get("header_height", 50)
        inner_width = self.data["frame_config"].get("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        inner_height = (self.data["frame_config"].get("outer_height", self.config.general.outer_height) -
                        self.data["frame_config"].get("header_height", 50) -
                        self.data["frame_config"].get("footer_height", 50) - margins[0] - margins[2])
        x_offset = margins[3]
        chart_start = datetime.strptime(self.data["frame_config"]["chart_start_date"], "%Y-%m-%d")
        prev_end = chart_start

        # Sort time frames by finish_date to ensure chronological rendering
        time_frames = self.data.get("time_frames", [])
        sorted_time_frames = sorted(
            time_frames,
            key=lambda tf: datetime.strptime(tf["finish_date"], "%Y-%m-%d")
        )
        logging.debug(f"Sorted time frames by finish_date: {[tf['finish_date'] for tf in sorted_time_frames]}")

        for tf in sorted_time_frames:
            tf_width = inner_width * tf.get("width_proportion", 1.0)
            tf_end = datetime.strptime(tf["finish_date"], "%Y-%m-%d")
            self.dwg.add(self.dwg.rect(insert=(x_offset, inner_y), size=(tf_width, inner_height),
                                       fill="none", stroke="red", stroke_width=1))
            self.render_scales_and_rows(x_offset, inner_y, tf_width, inner_height, prev_end, tf_end)
            x_offset += tf_width
            prev_end = tf_end + timedelta(days=1)
        logging.debug("render_time_frames completed")

    def _truncate_text_to_fit(self, text: str, max_width: float) -> str:
        """Truncate text to fit within max_width, adding ellipsis if needed."""
        text_width = self.font_metrics.horizontalAdvance(text)
        if text_width <= max_width:
            return text
        
        left, right = 1, len(text)
        while left <= right:
            mid = (left + right) // 2
            test_text = text[:mid] + "…"
            if self.font_metrics.horizontalAdvance(test_text) <= max_width:
                left = mid + 1
            else:
                right = mid - 1
        return text[:right] + "…" if right > 0 else ""

    def _render_inside_label(self, task_name: str, x_start: float, width_task: float, 
                             label_y_base: float):
        """Render a label inside a task bar, with truncation if needed."""
        task_name_display = self._truncate_text_to_fit(task_name, width_task)
        label_x = x_start + width_task / 2
        self.dwg.add(self.dwg.text(task_name_display, insert=(label_x, label_y_base),
                                   font_size="10", font_family="Arial", fill="white",
                                   text_anchor="middle"))

    def _render_outside_label(self, task_name: str, attachment_x: float, attachment_y: float,
                             label_y_base: float):
        """Render a label outside a task/milestone with a leader line to the right."""
        label_horizontal_offset = self.config.general.leader_line_horizontal_default
        label_x = attachment_x + label_horizontal_offset  # Fixed pixel offset, no time scaling
        self.dwg.add(self.dwg.text(task_name, insert=(label_x, label_y_base), 
                                   font_size="10", font_family="Arial", fill="black",
                                   text_anchor="start"))
        self.dwg.add(self.dwg.line((label_x, attachment_y), (attachment_x, attachment_y),
                                   stroke="black", stroke_width=1))

    def render_tasks(self, x, y, width, height, start_date, end_date, num_rows):
        logging.debug(f"Rendering tasks from {start_date} to {end_date}")
        total_days = max((end_date - start_date).days, 1)
        tf_time_scale = width / total_days if total_days > 0 else width
        row_height = height / num_rows if num_rows > 0 else height
        task_height = row_height * 0.8
        font_size = 10

        for task in self.data.get("tasks", []):
            start_date_str = task.get("start_date", "")
            finish_date_str = task.get("finish_date", "")
            # A task is a milestone if explicitly marked or if start_date equals finish_date
            is_milestone = task.get("is_milestone", False) or (start_date_str and finish_date_str and start_date_str == finish_date_str)
            label_placement = task.get("label_placement", "Outside")
            # Convert old placement values to new ones for backward compatibility
            if label_placement in ["To left", "To right"]:
                label_placement = "Outside"
            label_hide = task.get("label_hide", "Yes") == "No"
            task_name = task.get("task_name", "Unnamed")
            
            if not start_date_str and not finish_date_str:
                continue

            # Try to parse dates, skip task if dates are invalid
            try:
                date_to_use = start_date_str if start_date_str else finish_date_str
                task_start = datetime.strptime(date_to_use, "%Y-%m-%d")
                task_finish = task_start
                if not is_milestone and start_date_str and finish_date_str:
                    task_start = datetime.strptime(start_date_str, "%Y-%m-%d")
                    task_finish = datetime.strptime(finish_date_str, "%Y-%m-%d")
            except (ValueError, TypeError) as e:
                logging.warning(f"Skipping task {task.get('task_name', 'Unknown')} due to invalid date: {e}")
                continue

            if task_finish < start_date or task_start > end_date:
                continue
            
            row_num = min(max(task.get("row_number", 1) - 1, 0), num_rows - 1)
            x_start = x + max((task_start - start_date).days, 0) * tf_time_scale
            x_end = x + min((task_finish - start_date).days + 1, total_days) * tf_time_scale
            width_task = tf_time_scale if task_start == task_finish else max(x_end - x_start, tf_time_scale)
            y_task = y + row_num * row_height

            if is_milestone:
                half_size = task_height / 2
                center_x = x_end if finish_date_str else x_start
                center_y = y_task + row_height * 0.5
                points = [
                    (center_x, center_y - half_size),
                    (center_x + half_size, center_y),
                    (center_x, center_y + half_size),
                    (center_x - half_size, center_y)
                ]
                self.dwg.add(self.dwg.polygon(points=points, fill="red", stroke="black", stroke_width=1))
                
                if not label_hide and label_placement == "Outside":
                    label_y_base = center_y + font_size * self.config.general.label_vertical_offset_factor
                    milestone_right = center_x + half_size
                    self._render_outside_label(task_name, milestone_right, center_y, label_y_base)
            else:
                if x_start < x + width:
                    y_offset = (row_height - task_height) / 2
                    rect_y = y_task + y_offset
                    self.dwg.add(self.dwg.rect(insert=(x_start, rect_y), size=(width_task, task_height), fill="blue"))
                    
                    if not label_hide:
                        label_y_base = rect_y + task_height / 2 + font_size * self.config.general.label_vertical_offset_factor
                        if label_placement == "Inside":
                            self._render_inside_label(task_name, x_start, width_task, label_y_base)
                        elif label_placement == "Outside":
                            self._render_outside_label(task_name, x_end, rect_y + task_height / 2, 
                                                      label_y_base)

    def render_scales_and_rows(self, x, y, width, height, start_date, end_date):
        logging.debug(f"Rendering scales and rows from {start_date} to {end_date}")
        total_days = max((end_date - start_date).days, 1)
        tf_time_scale = width / total_days if total_days > 0 else width

        scale_configs = [
            ("years", self.config.general.scale_proportion_years),
            ("months", self.config.general.scale_proportion_months),
            ("weeks", self.config.general.scale_proportion_weeks),
            ("days", self.config.general.scale_proportion_days)
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
        logging.debug(f"Rendering scale interval: {interval}")
        current_date = start_date
        prev_x = x
        while current_date <= end_date:
            next_date = self.next_period(current_date, interval)
            x_pos = x + (next_date - start_date).days * tf_time_scale
            interval_width = x_pos - prev_x if x_pos <= x + width else (x + width) - prev_x
            if x <= x_pos <= x + width and interval_width >= self.config.general.min_interval_width:
                self.dwg.add(self.dwg.line((x_pos, y), (x_pos, y + height),
                                           stroke="black", stroke_width=1))
            if prev_x < x + width and x_pos > x:
                label_x = (max(x, prev_x) + min(x + width, x_pos)) / 2
                label_y = y + height / 2
                label = ""
                if interval == "years":
                    if interval_width >= self.config.general.full_label_width:
                        label = current_date.strftime("%Y")
                    elif interval_width >= self.config.general.short_label_width:
                        label = current_date.strftime("%y")
                elif interval == "months":
                    if interval_width >= self.config.general.full_label_width:
                        label = current_date.strftime("%b")
                    elif interval_width >= self.config.general.short_label_width:
                        label = current_date.strftime("%b")[0]
                elif interval == "weeks":
                    week_num = current_date.isocalendar()[1]
                    week_end = self.get_week_end_date(current_date)
                    if interval_width >= self.config.general.full_label_width:
                        label = f"{week_num:02d} ({week_end.strftime('%d')})"
                    elif interval_width >= self.config.general.short_label_width:
                        label = f"{week_num:02d}"
                elif interval == "days":
                    if interval_width >= self.config.general.full_label_width:
                        label = current_date.strftime("%a")
                    elif interval_width >= self.config.general.short_label_width:
                        label = current_date.strftime("%a")[0]
                if label:
                    self.dwg.add(self.dwg.text(label, insert=(label_x, label_y), text_anchor="middle",
                                               font_size="10", dominant_baseline="middle"))
            prev_x = x_pos
            current_date = next_date

    def render(self):
        logging.debug("Starting render")
        os.makedirs(self.output_folder, exist_ok=True)
        self.start_date = self._set_time_scale()
        self.render_outer_frame()
        self.render_header()
        self.render_footer()
        self.render_inner_frame()
        self.render_time_frames()
        self.dwg.save()
        logging.debug("Render completed")