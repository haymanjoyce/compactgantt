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
        self.data = {"frame_config": {}, "tasks": []}
        self.font = QFont("Arial", self.config.general.task_font_size)
        self.font_metrics = QFontMetrics(self.font)
        logging.debug("GanttChartService initialized")

    def _get_frame_config(self, key: str, default):
        """Get a value from frame_config with a default fallback."""
        return self.data["frame_config"].get(key, default)

    @pyqtSlot(dict)
    def generate_svg(self, data):
        logging.debug("Starting generate_svg")
        if not data or "frame_config" not in data:
            logging.warning("Skipping SVG generation: Invalid or empty data")
            self.svg_generated.emit("")
            return
        try:
            self.data = data
            logging.debug(f"Data keys: {list(data.keys())}")
            logging.debug(f"Number of tasks in incoming data: {len(data.get('tasks', []))}")
            if data.get('tasks'):
                logging.debug(f"First task sample: {data['tasks'][0] if len(data['tasks']) > 0 else 'N/A'}")
            width = data["frame_config"].get("outer_width", self.config.general.outer_width)
            height = data["frame_config"].get("outer_height", self.config.general.outer_height)
            self.dwg = svgwrite.Drawing(
                filename=os.path.abspath(os.path.join(self.output_folder, self.output_filename)),
                size=(width, height))
            self.render()
            svg_path = os.path.abspath(os.path.join(self.output_folder, self.output_filename))
            logging.debug(f"SVG generated at: {svg_path}")
            self.svg_generated.emit(svg_path)
            return svg_path
        except Exception as e:
            logging.error(f"SVG generation failed: {e}", exc_info=True)
            self.svg_generated.emit("")
            return

    def _parse_date_safe(self, date_str: str) -> datetime:
        """Safely parse a date string, returning None if invalid."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            return None

    def render_outer_frame(self):
        width = self._get_frame_config("outer_width", self.config.general.outer_width)
        height = self._get_frame_config("outer_height", self.config.general.outer_height)
        # Render background first
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(width, height), fill="white", stroke="none"))
        logging.debug("Outer frame rendered")

    def render_outer_frame_border(self):
        """Render outer frame border last so it appears on top of all other elements."""
        width = self._get_frame_config("outer_width", self.config.general.outer_width)
        height = self._get_frame_config("outer_height", self.config.general.outer_height)
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(width, height), fill="none", stroke="black", stroke_width=2))
        logging.debug("Outer frame border rendered")

    def render_header(self):
        margins = self._get_frame_config("margins", (10, 10, 10, 10))
        width = self._get_frame_config("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        height = self._get_frame_config("header_height", 20)
        self.dwg.add(self.dwg.rect(insert=(margins[3], margins[0]), size=(width, height),
                                   fill="lightgray", stroke="grey", stroke_width=1))
        header_text = self._get_frame_config("header_text", "")
        if header_text:
            header_y = margins[0] + height * self.config.general.text_vertical_alignment_factor
            self.dwg.add(self.dwg.text(header_text,
                                       insert=(margins[3] + width / 2, header_y),
                                       text_anchor="middle", font_size=str(self.config.general.header_footer_font_size), dominant_baseline="middle"))
        logging.debug("Header rendered")

    def render_footer(self):
        margins = self._get_frame_config("margins", (10, 10, 10, 10))
        width = self._get_frame_config("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        height = self._get_frame_config("footer_height", 20)
        y = self._get_frame_config("outer_height", self.config.general.outer_height) - margins[2] - height
        self.dwg.add(self.dwg.rect(insert=(margins[3], y), size=(width, height),
                                   fill="lightgray", stroke="grey", stroke_width=1))
        footer_text = self._get_frame_config("footer_text", "")
        if footer_text:
            footer_y = y + height * self.config.general.text_vertical_alignment_factor
            self.dwg.add(self.dwg.text(footer_text,
                                       insert=(margins[3] + width / 2, footer_y),
                                       text_anchor="middle", font_size=str(self.config.general.header_footer_font_size), dominant_baseline="middle"))
        logging.debug("Footer rendered")

    def render_inner_frame(self):
        margins = self._get_frame_config("margins", (10, 10, 10, 10))
        width = self._get_frame_config("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        header_height = self._get_frame_config("header_height", 20)
        footer_height = self._get_frame_config("footer_height", 20)
        y = margins[0] + header_height
        height = (self._get_frame_config("outer_height", self.config.general.outer_height) -
                  header_height - footer_height - margins[0] - margins[2])
        # Removed inner frame border - was used for layout debugging
        # self.dwg.add(self.dwg.rect(insert=(margins[3], y), size=(width, height),
        #                            fill="none", stroke="blue", stroke_width=1, stroke_dasharray="4"))
        logging.debug("Inner frame rendered")

    def render_single_timeline(self):
        """Render a single continuous timeline instead of multiple time frames."""
        logging.debug("Starting render_single_timeline")
        margins = self._get_frame_config("margins", (10, 10, 10, 10))
        header_height = self._get_frame_config("header_height", 20)
        footer_height = self._get_frame_config("footer_height", 20)
        outer_width = self._get_frame_config("outer_width", self.config.general.outer_width)
        outer_height = self._get_frame_config("outer_height", self.config.general.outer_height)
        inner_y = margins[0] + header_height
        inner_width = outer_width - margins[1] - margins[3]
        inner_height = outer_height - header_height - footer_height - margins[0] - margins[2]
        
        # Get chart start and end dates from frame config
        chart_start_str = self._get_frame_config("chart_start_date", "2024-12-30")
        chart_end_str = self._get_frame_config("chart_end_date", None)
        
        # If chart_end_date doesn't exist, calculate default (30 days after start)
        if not chart_end_str:
            try:
                start_dt = datetime.strptime(chart_start_str, "%Y-%m-%d")
                end_dt = start_dt + timedelta(days=30)
                chart_end_str = end_dt.strftime("%Y-%m-%d")
            except ValueError:
                chart_end_str = "2025-01-29"
        
        chart_start = datetime.strptime(chart_start_str, "%Y-%m-%d")
        chart_end = datetime.strptime(chart_end_str, "%Y-%m-%d")
        
        # Render scales, rows, and tasks in one continuous timeline
        row_y, row_frame_height = self.render_scales_and_rows(margins[3], inner_y, inner_width, inner_height, chart_start, chart_end)
        # Render links after tasks, using row frame position and height
        self.render_links(margins[3], row_y, inner_width, row_frame_height, chart_start, chart_end)
        logging.debug("render_single_timeline completed")


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
        """Render a label inside a task bar, with truncation if needed.
        
        This method renders white text centered horizontally within the specified task width.
        The text is automatically truncated with ellipsis if it doesn't fit within the width.
        
        Args:
            task_name: The full task name (will be truncated if needed)
            x_start: The absolute x position where the task starts (in pixels)
            width_task: The total width of the task in pixels (for centering and truncation)
            label_y_base: The y position for the label baseline (in pixels)
        """
        task_name_display = self._truncate_text_to_fit(task_name, width_task)
        label_x = x_start + width_task / 2
        logging.debug(f"_render_inside_label: text='{task_name_display}', x={label_x}, y={label_y_base}, width={width_task}, original_text='{task_name}'")
        self.dwg.add(self.dwg.text(task_name_display, insert=(label_x, label_y_base),
                                   font_size=str(self.config.general.task_font_size), font_family="Arial", fill="white",
                                   text_anchor="middle", dominant_baseline="middle"))
        logging.debug(f"  Text element added to SVG at position ({label_x}, {label_y_base})")


    def _render_outside_label(self, task_name: str, attachment_x: float, attachment_y: float,
                             label_y_base: float):
        """Render a label outside a task/milestone with a leader line to the right."""
        label_horizontal_offset = self.config.general.leader_line_horizontal_default
        label_x = attachment_x + label_horizontal_offset  # Fixed pixel offset, no time scaling
        self.dwg.add(self.dwg.text(task_name, insert=(label_x, label_y_base), 
                                   font_size=str(self.config.general.task_font_size), font_family="Arial", fill="black",
                                   text_anchor="start", dominant_baseline="middle"))
        self.dwg.add(self.dwg.line((label_x, attachment_y), (attachment_x, attachment_y),
                                   stroke="black", stroke_width=1))

    def render_tasks(self, x, y, width, height, start_date, end_date, num_rows):
        """Render all tasks that overlap with the timeline date range.
        
        Args:
            x: The absolute x position of the timeline (in pixels)
            y: The absolute y position of the timeline (in pixels)
            width: The width of the timeline (in pixels)
            height: The height of the timeline (in pixels)
            start_date: The start date of the timeline (datetime)
            end_date: The end date of the timeline (datetime)
            num_rows: The number of rows in the Gantt chart
        """
        logging.debug(f"render_tasks called: Rendering tasks from {start_date} to {end_date}")
        tasks = self.data.get("tasks", [])
        logging.debug(f"Number of tasks in data: {len(tasks)}")
        if not tasks:
            logging.warning("No tasks found in data! Tasks list is empty.")
        total_days = max((end_date - start_date).days, 1)
        time_scale = width / total_days if total_days > 0 else width
        row_height = height / num_rows if num_rows > 0 else height
        task_height = row_height * 0.8
        font_size = self.config.general.task_font_size

        for task in tasks:
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
            x_start = x + max((task_start - start_date).days, 0) * time_scale
            x_end = x + min((task_finish - start_date).days + 1, total_days) * time_scale
            width_task = time_scale if task_start == task_finish else max(x_end - x_start, time_scale)
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
                self.dwg.add(self.dwg.polygon(points=points, fill="red", stroke="black", stroke_width=0.5))
                
                if not label_hide and label_placement == "Outside":
                    # Use proportional positioning: center_y is at row_height * 0.5, apply factor to row_height
                    label_y_base = y_task + row_height * self.config.general.text_vertical_alignment_factor
                    milestone_right = center_x + half_size
                    self._render_outside_label(task_name, milestone_right, center_y, label_y_base)
            else:
                if x_start < x + width:
                    y_offset = (row_height - task_height) / 2
                    rect_y = y_task + y_offset
                    logging.debug(f"Rendering task bar for '{task_name}': x={x_start}, y={rect_y}, width={width_task}, height={task_height}, row={row_num}, y_task={y_task}")
                    self.dwg.add(self.dwg.rect(insert=(x_start, rect_y), size=(width_task, task_height), fill="blue", stroke="black", stroke_width=0.5))
                    
                    if not label_hide:
                        # Use proportional positioning within task bar
                        label_y_base = rect_y + task_height * self.config.general.text_vertical_alignment_factor
                        logging.debug(f"  Calculated label_y_base={label_y_base} for task '{task_name}' (rect_y={rect_y}, task_height={task_height}, alignment_factor={self.config.general.text_vertical_alignment_factor})")
                        
                        if label_placement == "Inside":
                            # Simple inside label rendering - no multi-time-frame logic needed
                            self._render_inside_label(task_name, x_start, width_task, label_y_base)
                        elif label_placement == "Outside":
                            self._render_outside_label(task_name, x_end, rect_y + task_height / 2, 
                                                      label_y_base)

    def _get_task_position(self, task_id: int, x, y, width, height, start_date, end_date, num_rows):
        """Get the position and dimensions of a task by its ID.
        
        Returns:
            dict with keys: x_start, x_end, y_center, row_num, is_milestone, or None if not found
        """
        total_days = max((end_date - start_date).days, 1)
        time_scale = width / total_days if total_days > 0 else width
        row_height = height / num_rows if num_rows > 0 else height
        task_height = row_height * 0.8
        
        for task in self.data.get("tasks", []):
            if task.get("task_id") != task_id:
                continue
                
            start_date_str = task.get("start_date", "")
            finish_date_str = task.get("finish_date", "")
            is_milestone = task.get("is_milestone", False) or (start_date_str and finish_date_str and start_date_str == finish_date_str)
            
            if not start_date_str and not finish_date_str:
                return None
            
            try:
                date_to_use = start_date_str if start_date_str else finish_date_str
                task_start = datetime.strptime(date_to_use, "%Y-%m-%d")
                task_finish = task_start
                if not is_milestone and start_date_str and finish_date_str:
                    task_start = datetime.strptime(start_date_str, "%Y-%m-%d")
                    task_finish = datetime.strptime(finish_date_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                return None
            
            if task_finish < start_date or task_start > end_date:
                return None
            
            row_num = min(max(task.get("row_number", 1) - 1, 0), num_rows - 1)
            x_start = x + max((task_start - start_date).days, 0) * time_scale
            x_end = x + min((task_finish - start_date).days + 1, total_days) * time_scale
            width_task = time_scale if task_start == task_finish else max(x_end - x_start, time_scale)
            y_task = y + row_num * row_height
            
            if is_milestone:
                half_size = task_height / 2
                center_x = x_end if finish_date_str else x_start
                center_y = y_task + row_height * 0.5
                return {
                    "x_start": center_x - half_size,
                    "x_end": center_x + half_size,
                    "y_center": center_y,
                    "row_num": row_num,
                    "is_milestone": True
                }
            else:
                y_offset = (row_height - task_height) / 2
                rect_y = y_task + y_offset
                return {
                    "x_start": x_start,
                    "x_end": x_end,
                    "y_center": y_task + row_height * 0.5,
                    "row_num": row_num,
                    "is_milestone": False
                }
        
        return None

    def _render_arrowhead(self, x: float, y: float, direction: str = "left", size: float = 5):
        """Render an arrowhead at the specified position.
        
        Args:
            x, y: Position of arrowhead tip
            direction: "left", "right", "up", or "down"
            size: Size of arrowhead in pixels
        """
        if direction == "left":
            # Tip at (x, y), base to the left (flipped horizontally from previous)
            points = [(x, y), (x - size, y - size/2), (x - size, y + size/2)]
        elif direction == "right":
            # Tip at (x, y), base to the right (flipped horizontally from previous)
            points = [(x, y), (x + size, y - size/2), (x + size, y + size/2)]
        elif direction == "up":
            points = [(x, y), (x - size/2, y + size), (x + size/2, y + size)]
        else:  # down
            points = [(x, y), (x - size/2, y - size), (x + size/2, y - size)]
        
        self.dwg.add(self.dwg.polygon(points=points, fill="black", stroke="none"))

    def render_links(self, x, row_y, width, row_frame_height, start_date, end_date):
        """Render links between tasks according to Finish-to-Start (FS) dependency rules.
        
        Links show workflow dependencies from source to target with routing based on positions:
        - Same row: Horizontal line
        - Different rows, no gap: Single vertical segment if aligned (< 2px), otherwise V-H-V
        - Different rows, gap: V-H-V pattern (vertical-horizontal-vertical)
        
        Args:
            x: The absolute x position of the timeline (in pixels)
            row_y: The absolute y position where the row frame starts (after scales, in pixels)
            width: The width of the timeline (in pixels)
            row_frame_height: The height of the row frame (in pixels)
            start_date: The start date of the timeline (datetime)
            end_date: The end date of the timeline (datetime)
        """
        num_rows = self._get_frame_config("num_rows", 1)
        links = self.data.get("links", [])
        
        if not links:
            return
        
        # Calculate row height for vertical positioning
        row_height = row_frame_height / num_rows if num_rows > 0 else row_frame_height
        
        for link in links:
            if len(link) < 6:  # Now expects: [ID, From Task ID, From Task Name, To Task ID, To Task Name, Valid]
                continue
            
            # Check if link is valid (if Valid field exists and is "No", skip rendering)
            if len(link) >= 6 and str(link[5]).strip().lower() == "no":  # Valid is at index 5
                continue  # Skip invalid links
            
            try:
                from_task_id = int(link[1])  # From Task ID is at index 1
                to_task_id = int(link[3])   # To Task ID is at index 3
            except (ValueError, TypeError):
                continue
            
            # Get positions for both tasks - use row_y and row_frame_height for correct vertical positioning
            from_task = self._get_task_position(from_task_id, x, row_y, width, row_frame_height, start_date, end_date, num_rows)
            to_task = self._get_task_position(to_task_id, x, row_y, width, row_frame_height, start_date, end_date, num_rows)
            
            if not from_task or not to_task:
                continue  # Skip if either task not found
            
            # Determine connection points based on task type (milestone vs regular task)
            # For milestones: use center point (center_x = x_start + half_size, or calculated from date)
            # For regular tasks: use right edge (predecessor) and left edge (successor)
            from_is_milestone = from_task.get("is_milestone", False)
            to_is_milestone = to_task.get("is_milestone", False)
            
            if from_is_milestone:
                # Milestone: use center point
                # For milestones, x_start and x_end represent the left and right edges of the diamond
                # Center is at (x_start + x_end) / 2
                origin_x = (from_task["x_start"] + from_task["x_end"]) / 2
            else:
                # Regular task: use right edge
                origin_x = from_task["x_end"]
            
            origin_y = from_task["y_center"]
            
            if to_is_milestone:
                # Milestone: use center point
                term_x = (to_task["x_start"] + to_task["x_end"]) / 2
            else:
                # Regular task: use left edge
                term_x = to_task["x_start"]
            
            term_y = to_task["y_center"]
            
            # Determine routing based on positions
            same_row = from_task["row_num"] == to_task["row_num"]
            same_date = abs(origin_x - term_x) < 1.0  # Very close horizontally (within 1 pixel)
            has_gap = term_x > origin_x  # Successor starts after predecessor finishes
            
            # Calculate link path according to spec
            if same_row:
                # Case 1: Same Row
                if same_date:
                    # 1a. No Gap (Bars Touch) - Skip rendering (no line/arrow needed)
                    # Tasks/milestones are delineated by their 0.5px borders instead
                    continue
                else:
                    # 1b. Positive Gap/Lag (Bars Separated)
                    self.dwg.add(self.dwg.line((origin_x, origin_y), (term_x, term_y),
                                              stroke="black", stroke_width=1.5))
                    self._render_arrowhead(term_x, term_y, "left", 5)
            else:
                # Different rows
                if same_date:
                    # Case 2a/3a: No Gap (Aligned Vertically)
                    # Check if alignment is perfect enough to collapse to single vertical segment
                    if abs(origin_x - term_x) < 2.0:
                        # Perfect alignment - single vertical segment
                        if to_task["row_num"] > from_task["row_num"]:
                            # Successor below - downward arrow
                            self.dwg.add(self.dwg.line((origin_x, origin_y), (term_x, term_y),
                                                      stroke="black", stroke_width=1.5))
                            self._render_arrowhead(term_x, term_y, "down", 5)
                        else:
                            # Successor above - upward arrow
                            self.dwg.add(self.dwg.line((origin_x, origin_y), (term_x, term_y),
                                                      stroke="black", stroke_width=1.5))
                            self._render_arrowhead(term_x, term_y, "up", 5)
                    else:
                        # Not perfectly aligned - use V-H-V pattern
                        # Calculate row midpoint y
                        mid_y = (origin_y + term_y) / 2
                        
                        if to_task["row_num"] > from_task["row_num"]:
                            # Successor below - V-H-V downward
                            self.dwg.add(self.dwg.line((origin_x, origin_y), (origin_x, mid_y),
                                                      stroke="black", stroke_width=1.5))
                            self.dwg.add(self.dwg.line((origin_x, mid_y), (term_x, mid_y),
                                                      stroke="black", stroke_width=1.5))
                            self.dwg.add(self.dwg.line((term_x, mid_y), (term_x, term_y),
                                                      stroke="black", stroke_width=1.5))
                            self._render_arrowhead(term_x, term_y, "down", 5)
                        else:
                            # Successor above - V-H-V upward
                            self.dwg.add(self.dwg.line((origin_x, origin_y), (origin_x, mid_y),
                                                      stroke="black", stroke_width=1.5))
                            self.dwg.add(self.dwg.line((origin_x, mid_y), (term_x, mid_y),
                                                      stroke="black", stroke_width=1.5))
                            self.dwg.add(self.dwg.line((term_x, mid_y), (term_x, term_y),
                                                      stroke="black", stroke_width=1.5))
                            self._render_arrowhead(term_x, term_y, "up", 5)
                else:
                    # Case 2b/3b: Positive Gap/Lag (Successor Starts Later)
                    # V-H-V pattern
                    # Calculate row midpoint y
                    mid_y = (origin_y + term_y) / 2
                    
                    if to_task["row_num"] > from_task["row_num"]:
                        # Successor below - V-H-V downward
                        # Segment 1: Vertical down from origin to row midpoint
                        # Segment 2: Horizontal right to align with successor
                        # Segment 3: Vertical down to termination
                        self.dwg.add(self.dwg.line((origin_x, origin_y), (origin_x, mid_y),
                                                  stroke="black", stroke_width=1.5))
                        self.dwg.add(self.dwg.line((origin_x, mid_y), (term_x, mid_y),
                                                  stroke="black", stroke_width=1.5))
                        self.dwg.add(self.dwg.line((term_x, mid_y), (term_x, term_y),
                                                  stroke="black", stroke_width=1.5))
                        self._render_arrowhead(term_x, term_y, "down", 5)
                    else:
                        # Successor above - V-H-V upward
                        # Segment 1: Vertical up from origin to row midpoint
                        # Segment 2: Horizontal right to align with successor
                        # Segment 3: Vertical up to termination
                        self.dwg.add(self.dwg.line((origin_x, origin_y), (origin_x, mid_y),
                                                  stroke="black", stroke_width=1.5))
                        self.dwg.add(self.dwg.line((origin_x, mid_y), (term_x, mid_y),
                                                  stroke="black", stroke_width=1.5))
                        self.dwg.add(self.dwg.line((term_x, mid_y), (term_x, term_y),
                                                  stroke="black", stroke_width=1.5))
                        self._render_arrowhead(term_x, term_y, "up", 5)

    def render_scales_and_rows(self, x, y, width, height, start_date, end_date):
        logging.debug(f"Rendering scales and rows from {start_date} to {end_date}")
        total_days = max((end_date - start_date).days, 1)
        time_scale = width / total_days if total_days > 0 else width

        # Get scale visibility settings from frame_config
        show_years = self._get_frame_config("show_years", True)
        show_months = self._get_frame_config("show_months", True)
        show_weeks = self._get_frame_config("show_weeks", True)
        show_days = self._get_frame_config("show_days", True)

        # Build scale configs list, filtering by visibility
        all_scale_configs = [
            ("years", self.config.general.scale_proportion_years, show_years),
            ("months", self.config.general.scale_proportion_months, show_months),
            ("weeks", self.config.general.scale_proportion_weeks, show_weeks),
            ("days", self.config.general.scale_proportion_days, show_days)
        ]
        
        # Filter to only include visible scales
        scale_configs = [(interval, proportion) for interval, proportion, visible in all_scale_configs if visible]
        
        row_frame_proportion = 1.0
        total_scale_proportion = sum(p for _, p in scale_configs)
        total_height_units = row_frame_proportion + total_scale_proportion
        row_frame_height = height * (row_frame_proportion / total_height_units)
        scale_heights = [(interval, height * (proportion / total_height_units)) for interval, proportion in scale_configs]

        current_y = y
        for interval, scale_height in scale_heights:
            self.dwg.add(self.dwg.rect(insert=(x, current_y), size=(width, scale_height),
                                       fill="lightgrey", stroke="grey", stroke_width=1))
            self.render_scale_interval(x, current_y, width, scale_height, start_date, end_date, interval, time_scale)
            current_y += scale_height

        row_y = current_y
        num_rows = self._get_frame_config("num_rows", 1)
        self.dwg.add(self.dwg.rect(insert=(x, row_y), size=(width, row_frame_height),
                                   fill="none", stroke="grey", stroke_width=1))

        if self._get_frame_config("horizontal_gridlines", False):
            for i in range(1, num_rows):  # Exclude first and last to avoid overlapping row frame border
                y_pos = row_y + i * (row_frame_height / num_rows)
                self.dwg.add(self.dwg.line((x, y_pos), (x + width, y_pos), stroke="#d3d3d3", stroke_width=1))

        # Render vertical gridlines based on individual interval settings
        # Define line weights for visual hierarchy: larger intervals = thicker lines
        interval_line_weights = {
            "years": 3.0,
            "months": 2.0,
            "weeks": 1.5,
            "days": 1.0
        }
        
        # Check which intervals should have gridlines (independent of scale visibility)
        vertical_gridline_intervals = []
        if self._get_frame_config("vertical_gridline_years", False):
            vertical_gridline_intervals.append("years")
        if self._get_frame_config("vertical_gridline_months", False):
            vertical_gridline_intervals.append("months")
        if self._get_frame_config("vertical_gridline_weeks", False):
            vertical_gridline_intervals.append("weeks")
        if self._get_frame_config("vertical_gridline_days", False):
            vertical_gridline_intervals.append("days")
        
        # Handle backward compatibility: if old vertical_gridlines flag exists, use all visible scales
        if not vertical_gridline_intervals and self._get_frame_config("vertical_gridlines", False):
            # Old format - use all visible scale intervals
            vertical_gridline_intervals = [interval for interval, _ in scale_configs]
        
        # Render gridlines for each enabled interval
        for interval in vertical_gridline_intervals:
            line_weight = interval_line_weights.get(interval, 1.0)
            current_date = self.next_period(start_date, interval)
            prev_x = x
            while current_date <= end_date:
                x_pos = x + (current_date - start_date).days * time_scale
                interval_width = x_pos - prev_x if x_pos <= x + width else (x + width) - prev_x
                if x <= x_pos <= x + width:
                    self.dwg.add(self.dwg.line((x_pos, row_y), (x_pos, row_y + row_frame_height),
                                               stroke="#d3d3d3", stroke_width=line_weight))
                prev_x = x_pos
                current_date = self.next_period(current_date, interval)

        self.render_tasks(x, row_y, width, row_frame_height, start_date, end_date, num_rows)
        
        # Return row frame position and height for use by other rendering functions
        return row_y, row_frame_height

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


    def render_scale_interval(self, x, y, width, height, start_date, end_date, interval, time_scale):
        logging.debug(f"Rendering scale interval: {interval}")
        current_date = start_date
        prev_x = x
        while current_date <= end_date:
            next_date = self.next_period(current_date, interval)
            x_pos = x + (next_date - start_date).days * time_scale
            interval_width = x_pos - prev_x if x_pos <= x + width else (x + width) - prev_x
            # Draw increment border only if it doesn't align with scale border edges
            if x < x_pos < x + width:
                self.dwg.add(self.dwg.line((x_pos, y), (x_pos, y + height),
                                           stroke="gray", stroke_width=0.5))
            if prev_x < x + width and x_pos > x:
                label_x = (max(x, prev_x) + min(x + width, x_pos)) / 2
                label_y = y + height * self.config.general.text_vertical_alignment_factor
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
                    if interval_width >= self.config.general.short_label_width:
                        label = f"{week_num:02d}"
                elif interval == "days":
                    if interval_width >= self.config.general.full_label_width:
                        label = current_date.strftime("%a")
                    elif interval_width >= self.config.general.short_label_width:
                        label = current_date.strftime("%a")[0]
                if label:
                    self.dwg.add(self.dwg.text(label, insert=(label_x, label_y), text_anchor="middle",
                                               font_size=str(self.config.general.scale_font_size), dominant_baseline="middle"))
            prev_x = x_pos
            current_date = next_date

    def render(self):
        logging.debug("Starting render")
        os.makedirs(self.output_folder, exist_ok=True)
        self.render_outer_frame()  # Background only
        self.render_header()
        self.render_footer()
        self.render_inner_frame()
        self.render_single_timeline()
        self.render_outer_frame_border()  # Border rendered last
        self.dwg.save()
        logging.debug("Render completed")