# File: gantt_chart_service.py
import svgwrite
from datetime import datetime, timedelta
import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QFontMetrics
from config.app_config import AppConfig
import logging
from models.link import Link
from utils.conversion import is_valid_internal_date
from models.pipe import Pipe
from models.curtain import Curtain
from models.swimlane import Swimlane
from models.note import Note

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class GanttChartService(QObject):
    svg_generated = pyqtSignal(str)

    def __init__(self, app_config=None, output_folder: str = None, output_filename: str = None):
        super().__init__()
        self.config = app_config if app_config else AppConfig()  # Use passed instance or create new
        self.output_folder = output_folder or self.config.general.svg_output_folder
        self.output_filename = output_filename or self.config.general.svg_output_filename
        self.dwg = None
        self.data = {"frame_config": {}, "tasks": []}
        self.font = QFont(self.config.general.font_family, self.config.general.task_font_size)
        self.font_metrics = QFontMetrics(self.font)
        logging.debug("GanttChartService initialized")

    def _get_frame_config(self, key: str, default):
        """Get a value from frame_config with a default fallback."""
        return self.data["frame_config"].get(key, default)

    @pyqtSlot(dict)
    def generate_svg(self, data):
        logging.debug("Starting generate_svg")
        # Update font and font_metrics to use current config values
        self.font = QFont(self.config.general.font_family, self.config.general.task_font_size)
        self.font_metrics = QFontMetrics(self.font)
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
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(width, height), fill="none", 
                                   stroke=self.config.general.frame_border_color, 
                                   stroke_width=self.config.general.frame_border_width_heavy))
        logging.debug("Outer frame border rendered")

    def render_header(self):
        margins = self._get_frame_config("margins", (10, 10, 10, 10))
        width = self._get_frame_config("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        height = self._get_frame_config("header_height", 20)
        
        # Skip rendering if height is 0
        if height <= 0:
            logging.debug("Header skipped (height is 0)")
            return
        
        self.dwg.add(self.dwg.rect(insert=(margins[3], margins[0]), size=(width, height),
                                   fill="lightgrey", 
                                   stroke=self.config.general.frame_border_color, 
                                   stroke_width=self.config.general.frame_border_width_light))
        header_text = self._get_frame_config("header_text", "")
        if header_text:
            header_y = margins[0] + height * self.config.general.header_footer_vertical_alignment_factor
            self.dwg.add(self.dwg.text(header_text,
                                       insert=(margins[3] + width / 2, header_y),
                                       text_anchor="middle", font_size=str(self.config.general.header_footer_font_size), font_family=self.config.general.font_family, dominant_baseline="middle"))
        logging.debug("Header rendered")

    def render_footer(self):
        margins = self._get_frame_config("margins", (10, 10, 10, 10))
        width = self._get_frame_config("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        height = self._get_frame_config("footer_height", 20)
        
        # Skip rendering if height is 0
        if height <= 0:
            logging.debug("Footer skipped (height is 0)")
            return
        
        y = self._get_frame_config("outer_height", self.config.general.outer_height) - margins[2] - height
        self.dwg.add(self.dwg.rect(insert=(margins[3], y), size=(width, height),
                                   fill="lightgrey", 
                                   stroke=self.config.general.frame_border_color, 
                                   stroke_width=self.config.general.frame_border_width_light))
        footer_text = self._get_frame_config("footer_text", "")
        if footer_text:
            footer_y = y + height * self.config.general.header_footer_vertical_alignment_factor
            self.dwg.add(self.dwg.text(footer_text,
                                       insert=(margins[3] + width / 2, footer_y),
                                       text_anchor="middle", font_size=str(self.config.general.header_footer_font_size), font_family=self.config.general.font_family, dominant_baseline="middle"))
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

    def _format_label_text(self, task_name: str, start_date_str: str, finish_date_str: str, 
                          label_content: str, is_milestone: bool) -> str:
        """Format label text based on label_content option.
        
        Args:
            task_name: The task name
            start_date_str: Start date in internal format (yyyy-mm-dd)
            finish_date_str: Finish date in internal format (yyyy-mm-dd)
            label_content: One of "None", "Name only", "Date only", "Name and Date"
            is_milestone: Whether this is a milestone (single date)
            
        Returns:
            Formatted label text, or empty string if label_content is "None"
        """
        from utils.conversion import internal_to_display_date
        
        if label_content == "None":
            return ""
        elif label_content == "Name only":
            return task_name
        elif label_content == "Date only":
            if is_milestone:
                # For milestones, show single date
                date_str = start_date_str if start_date_str else finish_date_str
                return internal_to_display_date(date_str) if date_str else ""
            else:
                # For tasks, show date range
                start_display = internal_to_display_date(start_date_str) if start_date_str else ""
                finish_display = internal_to_display_date(finish_date_str) if finish_date_str else ""
                if start_display and finish_display:
                    if start_display == finish_display:
                        return start_display
                    else:
                        return f"{start_display} - {finish_display}"
                elif start_display:
                    return start_display
                elif finish_display:
                    return finish_display
                else:
                    return ""
        elif label_content == "Name and Date":
            if is_milestone:
                # For milestones: "Task Name (01/01/2025)"
                date_str = start_date_str if start_date_str else finish_date_str
                date_display = internal_to_display_date(date_str) if date_str else ""
                if date_display:
                    return f"{task_name} ({date_display})"
                else:
                    return task_name
            else:
                # For tasks: "Task Name (01/01/2025 - 31/01/2025)"
                start_display = internal_to_display_date(start_date_str) if start_date_str else ""
                finish_display = internal_to_display_date(finish_date_str) if finish_date_str else ""
                if start_display and finish_display:
                    if start_display == finish_display:
                        return f"{task_name} ({start_display})"
                    else:
                        return f"{task_name} ({start_display} - {finish_display})"
                elif start_display:
                    return f"{task_name} ({start_display})"
                elif finish_display:
                    return f"{task_name} ({finish_display})"
                else:
                    return task_name
        else:
            # Default fallback: use name only
            return task_name

    def _get_inside_label_text_color(self, fill_color: str) -> str:
        """Determine text color for inside labels based on fill color.
        
        Args:
            fill_color: The fill color of the task/milestone
            
        Returns:
            "black" for light backgrounds (yellow, white, cyan, orange, magenta),
            "white" for all other backgrounds
        """
        # Normalize color name to lowercase for comparison
        fill_color_lower = fill_color.lower() if fill_color else "blue"
        
        # Colors that need black text for visibility
        light_colors = {"yellow", "white", "cyan", "orange", "magenta"}
        
        if fill_color_lower in light_colors:
            return "black"
        else:
            return "white"

    def _render_inside_label(self, task_name: str, x_start: float, width_task: float, 
                             label_y_base: float, fill_color: str = "blue"):
        """Render a label inside a task bar, with truncation if needed.
        
        This method renders text centered horizontally within the specified task width.
        Text color is automatically determined based on the fill color for optimal visibility.
        The text is automatically truncated with ellipsis if it doesn't fit within the width.
        
        Args:
            task_name: The full task name (will be truncated if needed)
            x_start: The absolute x position where the task starts (in pixels)
            width_task: The total width of the task in pixels (for centering and truncation)
            label_y_base: The y position for the label baseline (in pixels)
            fill_color: The fill color of the task (used to determine text color)
        """
        task_name_display = self._truncate_text_to_fit(task_name, width_task)
        label_x = x_start + width_task / 2
        text_color = self._get_inside_label_text_color(fill_color)
        logging.debug(f"_render_inside_label: text='{task_name_display}', x={label_x}, y={label_y_base}, width={width_task}, fill_color={fill_color}, text_color={text_color}, original_text='{task_name}'")
        self.dwg.add(self.dwg.text(task_name_display, insert=(label_x, label_y_base),
                                   font_size=str(self.config.general.task_font_size), font_family=self.config.general.font_family, fill=text_color,
                                   text_anchor="middle", dominant_baseline="middle"))
        logging.debug(f"  Text element added to SVG at position ({label_x}, {label_y_base})")


    def _render_outside_label(self, task_name: str, attachment_x: float, attachment_y: float,
                             label_y_base: float, label_horizontal_offset: float = 0.0):
        """Render a label outside a task/milestone with optional leader line.
        
        Args:
            task_name: The label text to display
            attachment_x: The x position where the label attaches to the task/milestone
            attachment_y: The y position for the leader line (if shown)
            label_y_base: The y position for the label text baseline
            label_horizontal_offset: Additional offset beyond default close offset (default 0.0)
        """
        # Default close offset from config (always applied)
        default_close_offset = self.config.general.leader_line_horizontal_default
        
        # Total distance = default close offset + user-specified offset
        total_offset = default_close_offset + label_horizontal_offset
        label_x = attachment_x + total_offset  # Fixed pixel offset, no time scaling
        
        # Render label text
        self.dwg.add(self.dwg.text(task_name, insert=(label_x, label_y_base), 
                                   font_size=str(self.config.general.task_font_size), font_family=self.config.general.font_family, fill="black",
                                   text_anchor="start", dominant_baseline="middle"))
        
        # Render leader line only if user offset > 0
        if label_horizontal_offset > 0:
            self.dwg.add(self.dwg.line((label_x, attachment_y), (attachment_x, attachment_y),
                                       stroke="black", stroke_width=0.5))

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
            # Backward compatibility: if label_content is missing, use label_hide
            label_content = task.get("label_content")
            if label_content is None:
                # Migrate from old label_hide field
                label_hide = task.get("label_hide", "Yes")
                label_content = "None" if label_hide == "No" else "Name only"
            label_hide = label_content == "None"  # For rendering logic compatibility
            task_name = task.get("task_name", "Unnamed")
            fill_color = task.get("fill_color", "blue")  # Get fill color, default to blue
            label_horizontal_offset = task.get("label_horizontal_offset", 0.0)  # Get label offset, default to 0.0
            
            # Format label text based on label_content
            label_text = self._format_label_text(task_name, start_date_str, finish_date_str, label_content, is_milestone)
            
            if not start_date_str and not finish_date_str:
                continue

            # Validate that both dates are valid
            # Skip task if either date is invalid (empty or invalid format)
            # This matches the validation logic which requires both dates to be valid
            if not is_valid_internal_date(start_date_str):
                logging.warning(f"Skipping task {task.get('task_name', 'Unknown')} due to invalid start date: {start_date_str}")
                continue
            if not is_valid_internal_date(finish_date_str):
                logging.warning(f"Skipping task {task.get('task_name', 'Unknown')} due to invalid finish date: {finish_date_str}")
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

            # Skip invalid tasks where finish date is before start date
            if task_finish < task_start:
                continue

            if task_finish < start_date or task_start > end_date:
                continue
            
            # Skip tasks with row numbers beyond available rows (don't clamp to last row)
            task_row = task.get("row_number", 1)
            if task_row > num_rows:
                continue
            
            row_num = task_row - 1  # Convert to 0-based index
            x_start = x + max((task_start - start_date).days, 0) * time_scale
            x_end = x + min((task_finish - start_date).days + 1, total_days) * time_scale
            width_task = time_scale if task_start == task_finish else max(x_end - x_start, time_scale)
            y_task = y + row_num * row_height

            if is_milestone:
                half_size = task_height / 2
                center_x = x_end if finish_date_str else x_start
                center_y = y_task + row_height * 0.5
                
                # Render as a circle - use fill_color from task
                self.dwg.add(self.dwg.circle(center=(center_x, center_y), r=half_size, 
                                             fill=fill_color, stroke="black", stroke_width=0.5))
                
                if not label_hide and label_placement == "Outside":
                    # Use proportional positioning: center_y is at row_height * 0.5, apply factor to row_height
                    label_y_base = y_task + row_height * self.config.general.task_vertical_alignment_factor
                    milestone_right = center_x + half_size
                    self._render_outside_label(label_text, milestone_right, center_y, label_y_base, label_horizontal_offset)
            else:
                if x_start < x + width:
                    y_offset = (row_height - task_height) / 2
                    rect_y = y_task + y_offset
                    logging.debug(f"Rendering task bar for '{task_name}': x={x_start}, y={rect_y}, width={width_task}, height={task_height}, row={row_num}, y_task={y_task}")
                    corner_radius = 3
                    self.dwg.add(self.dwg.rect(insert=(x_start, rect_y), size=(width_task, task_height), 
                                              fill=fill_color, stroke="black", stroke_width=0.5,
                                              rx=corner_radius, ry=corner_radius))
                    
                    if not label_hide:
                        # Use proportional positioning within task bar
                        label_y_base = rect_y + task_height * self.config.general.task_vertical_alignment_factor
                        logging.debug(f"  Calculated label_y_base={label_y_base} for task '{task_name}' (rect_y={rect_y}, task_height={task_height}, alignment_factor={self.config.general.task_vertical_alignment_factor})")
                        
                        if label_placement == "Inside":
                            # Simple inside label rendering - no multi-time-frame logic needed
                            self._render_inside_label(label_text, x_start, width_task, label_y_base, fill_color)
                        elif label_placement == "Outside":
                            self._render_outside_label(label_text, x_end, rect_y + task_height / 2, 
                                                      label_y_base, label_horizontal_offset)

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
            
            # Skip invalid tasks where finish date is before start date
            if task_finish < task_start:
                return None
            
            if task_finish < start_date or task_start > end_date:
                return None
            
            # Skip tasks with row numbers beyond available rows (don't clamp to last row)
            task_row = task.get("row_number", 1)
            if task_row > num_rows:
                return None
            
            row_num = task_row - 1  # Convert to 0-based index
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

    def _render_arrowhead(self, x: float, y: float, direction: str = "left", size: float = 5, color: str = "black"):
        """Render an arrowhead at the specified position.
        
        Args:
            x, y: Position of arrowhead tip
            direction: "left", "right", "up", or "down"
            size: Size of arrowhead in pixels
            color: Color of the arrowhead (default: "black")
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
        
        self.dwg.add(self.dwg.polygon(points=points, fill=color, stroke="none"))

    def render_pipes(self, x, row_y, width, row_frame_height, start_date, end_date):
        """Render vertical pipe lines at specific dates.
        
        Args:
            x: The absolute x position of the timeline (in pixels)
            row_y: The absolute y position of the row frame (in pixels)
            width: The width of the timeline (in pixels)
            row_frame_height: The height of the row frame (in pixels)
            start_date: The start date of the timeline (datetime)
            end_date: The end date of the timeline (datetime)
        """
        pipes_data = self.data.get("pipes", [])
        if not pipes_data:
            return
        
        total_days = max((end_date - start_date).days, 1)
        time_scale = width / total_days if total_days > 0 else width
        
        for pipe_data in pipes_data:
            # Convert dict to Pipe object if needed
            if isinstance(pipe_data, dict):
                pipe = Pipe.from_dict(pipe_data)
            else:
                pipe = pipe_data
            
            # Validate date
            if not is_valid_internal_date(pipe.date):
                continue
            
            try:
                pipe_date = datetime.strptime(pipe.date, "%Y-%m-%d")
            except (ValueError, TypeError):
                continue
            
            # Skip if pipe date is outside timeline range
            if pipe_date < start_date or pipe_date > end_date:
                continue
            
            # Calculate x position for the pipe
            x_pos = x + (pipe_date - start_date).days * time_scale
            
            # Only render if within visible area
            if x <= x_pos <= x + width:
                # Draw vertical line spanning all rows
                self.dwg.add(self.dwg.line(
                    (x_pos, row_y),
                    (x_pos, row_y + row_frame_height),
                    stroke=pipe.color if pipe.color else "red",
                    stroke_width=1.0
                ))
                
                # Render name if provided (rotated 90 degrees along the line)
                if pipe.name:
                    # Position name at top of the line, rotated 90 degrees
                    name_group = self.dwg.g(transform=f"translate({x_pos}, {row_y}) rotate(-90)")
                    self.dwg.add(name_group)
                    name_group.add(self.dwg.text(
                        pipe.name,
                        insert=(0, 0),
                        text_anchor="start",
                        dominant_baseline="middle",
                        font_size=str(self.config.general.task_font_size),
                        font_family=self.config.general.font_family,
                        fill=pipe.color if pipe.color else "red"
                    ))

    def render_swimlanes(self, x, row_y, width, row_frame_height, num_rows):
        """Render swimlanes (horizontal dividers and labels).
        
        Args:
            x: The absolute x position of the timeline (in pixels)
            row_y: The absolute y position of the row frame (in pixels)
            width: The width of the timeline (in pixels)
            row_frame_height: The height of the row frame (in pixels)
            num_rows: The number of rows in the chart
        """
        swimlanes_data = self.data.get("swimlanes", [])
        if not swimlanes_data:
            return
        
        # Convert dicts to Swimlane objects if needed
        swimlanes = []
        for swimlane_data in swimlanes_data:
            if isinstance(swimlane_data, dict):
                swimlanes.append(Swimlane.from_dict(swimlane_data))
            else:
                swimlanes.append(swimlane_data)
        
        if not swimlanes:
            return
        
        # Calculate row height
        row_height = row_frame_height / num_rows if num_rows > 0 else row_frame_height
        
        # Calculate first/last rows from table order (swimlanes stack vertically)
        current_first_row = 1  # 1-based
        
        # Render dividers and labels for each swimlane (order matters!)
        for swimlane in swimlanes:
            # Calculate first and last row for this swimlane based on table order
            first_row = current_first_row
            last_row = current_first_row + swimlane.row_count - 1
            
            # Validate row numbers
            if first_row < 1 or last_row > num_rows:
                # Skip invalid swimlanes, but continue to next
                current_first_row += swimlane.row_count
                continue
            
            # Convert to 0-based for calculations
            first_row_0based = first_row - 1
            last_row_0based = last_row - 1
            
            # Render divider at the bottom of the swimlane (except if it meets the row frame bottom border)
            # The divider is at the boundary between last_row and last_row + 1
            if last_row < num_rows:
                # Calculate Y position for divider (at the bottom boundary of the swimlane)
                # This is the same Y position as a row divider would use
                divider_y = row_y + last_row * row_height
                self.dwg.add(self.dwg.line(
                    (x, divider_y),
                    (x + width, divider_y),
                    stroke="grey",
                    stroke_width=0.5
                ))
            
            # Render label based on label_position
            if swimlane.title:
                # Calculate the swimlane area bounds
                swimlane_top = row_y + first_row_0based * row_height
                swimlane_bottom = row_y + (last_row_0based + 1) * row_height
                
                # Determine position based on label_position
                offset = 5  # Fixed 5px offset from edges
                label_position = swimlane.label_position if hasattr(swimlane, 'label_position') else "Bottom Right"
                
                # Get vertical adjustment factors from config (separate for top and bottom)
                # Align labels with the row they occupy (first or last row of swimlane)
                if label_position in ["Bottom Right", "Bottom Left"]:
                    # Bottom labels: align with the last row of the swimlane
                    row_top = row_y + last_row_0based * row_height
                    vertical_factor = self.config.general.swimlane_bottom_vertical_alignment_factor
                    label_y = row_top + row_height * vertical_factor
                elif label_position in ["Top Left", "Top Right"]:
                    # Top labels: align with the first row of the swimlane
                    row_top = row_y + first_row_0based * row_height
                    vertical_factor = self.config.general.swimlane_top_vertical_alignment_factor
                    label_y = row_top + row_height * vertical_factor
                else:
                    # Default to bottom positioning
                    row_top = row_y + last_row_0based * row_height
                    vertical_factor = self.config.general.swimlane_bottom_vertical_alignment_factor
                    label_y = row_top + row_height * vertical_factor
                
                if label_position == "Bottom Right":
                    label_x = x + width - offset
                    text_anchor = "end"
                    dominant_baseline = "middle"
                elif label_position == "Bottom Left":
                    label_x = x + offset
                    text_anchor = "start"
                    dominant_baseline = "middle"
                elif label_position == "Top Left":
                    label_x = x + offset
                    text_anchor = "start"
                    dominant_baseline = "middle"
                elif label_position == "Top Right":
                    label_x = x + width - offset
                    text_anchor = "end"
                    dominant_baseline = "middle"
                else:
                    # Default to Bottom Right if invalid
                    label_x = x + width - offset
                    row_top = row_y + last_row_0based * row_height
                    vertical_factor = self.config.general.swimlane_bottom_vertical_alignment_factor
                    label_y = row_top + row_height * vertical_factor
                    text_anchor = "end"
                    dominant_baseline = "middle"
                
                # Create text element
                text_element = self.dwg.text(
                    swimlane.title,
                    insert=(label_x, label_y),
                    fill="grey",
                    font_size=str(self.config.general.swimlane_font_size) + "px",
                    font_family=f"{self.config.general.font_family}, sans-serif",
                    text_anchor=text_anchor,
                    dominant_baseline=dominant_baseline
                )
                self.dwg.add(text_element)
            
            # Move to next swimlane's starting position
            current_first_row += swimlane.row_count

    def render_curtains(self, x, row_y, width, row_frame_height, start_date, end_date):
        """Render curtains (two vertical lines with hatched pattern between them).
        
        Args:
            x: The absolute x position of the timeline (in pixels)
            row_y: The absolute y position of the row frame (in pixels)
            width: The width of the timeline (in pixels)
            row_frame_height: The height of the row frame (in pixels)
            start_date: The start date of the timeline (datetime)
            end_date: The end date of the timeline (datetime)
        """
        curtains_data = self.data.get("curtains", [])
        if not curtains_data:
            return
        
        total_days = max((end_date - start_date).days, 1)
        time_scale = width / total_days if total_days > 0 else width
        
        for curtain_data in curtains_data:
            # Convert dict to Curtain object if needed
            if isinstance(curtain_data, dict):
                curtain = Curtain.from_dict(curtain_data)
            else:
                curtain = curtain_data
            
            # Validate dates
            if not is_valid_internal_date(curtain.start_date) or not is_valid_internal_date(curtain.end_date):
                continue
            
            try:
                curtain_start = datetime.strptime(curtain.start_date, "%Y-%m-%d")
                curtain_end = datetime.strptime(curtain.end_date, "%Y-%m-%d")
            except (ValueError, TypeError):
                continue
            
            # Skip if curtain is completely outside timeline range
            if curtain_end < start_date or curtain_start > end_date:
                continue
            
            # Calculate x positions for the curtain lines
            x_start = x + (curtain_start - start_date).days * time_scale
            x_end = x + (curtain_end - start_date).days * time_scale
            
            # Clamp to visible area
            x_start_visible = max(x, min(x_start, x + width))
            x_end_visible = max(x, min(x_end, x + width))
            
            # Draw filled rectangle with semi-transparent fill (less saturated)
            if x_start_visible < x_end_visible:
                curtain_color = curtain.color if curtain.color else "red"
                self.dwg.add(self.dwg.rect(
                    insert=(x_start_visible, row_y),
                    size=(x_end_visible - x_start_visible, row_frame_height),
                    fill=curtain_color,
                    fill_opacity=0.3,  # Semi-transparent fill (less saturated)
                    stroke="none"
                ))
            
            # Draw left vertical line (border)
            if x <= x_start <= x + width:
                self.dwg.add(self.dwg.line(
                    (x_start, row_y),
                    (x_start, row_y + row_frame_height),
                    stroke=curtain.color if curtain.color else "red",
                    stroke_width=1.0
                ))
            
            # Draw right vertical line (border)
            if x <= x_end <= x + width:
                self.dwg.add(self.dwg.line(
                    (x_end, row_y),
                    (x_end, row_y + row_frame_height),
                    stroke=curtain.color if curtain.color else "red",
                    stroke_width=1.0
                ))
            
            # Render name if provided (rotated 90 degrees along the start line)
            if curtain.name and x <= x_start <= x + width:
                name_group = self.dwg.g(transform=f"translate({x_start}, {row_y}) rotate(-90)")
                self.dwg.add(name_group)
                name_group.add(self.dwg.text(
                    curtain.name,
                    insert=(0, 0),
                    text_anchor="start",
                    dominant_baseline="middle",
                    font_size=str(self.config.general.task_font_size),
                    font_family=self.config.general.font_family,
                    fill=curtain.color if curtain.color else "red"
                ))

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
        links_data = self.data.get("links", [])
        
        if not links_data:
            return
        
        # Convert dicts to Link objects (links come from to_json() as dicts)
        links = []
        tasks_data = self.data.get("tasks", [])
        # Create task map for quick lookup
        task_map = {}
        for task_item in tasks_data:
            if isinstance(task_item, dict):
                task_id = task_item.get("task_id")
            else:
                task_id = getattr(task_item, "task_id", None)
            if task_id:
                task_map[task_id] = task_item
        
        for link_item in links_data:
            if isinstance(link_item, dict):
                link = Link.from_dict(link_item)
                # Calculate valid status (similar to update_links in project.py)
                from_task_dict = task_map.get(link.from_task_id)
                to_task_dict = task_map.get(link.to_task_id)
                
                if from_task_dict and to_task_dict:
                    if isinstance(from_task_dict, dict):
                        from_finish_date = from_task_dict.get("finish_date") or from_task_dict.get("start_date")
                    else:
                        from_finish_date = getattr(from_task_dict, "finish_date", None) or getattr(from_task_dict, "start_date", None)
                    
                    if isinstance(to_task_dict, dict):
                        to_start_date = to_task_dict.get("start_date") or to_task_dict.get("finish_date")
                    else:
                        to_start_date = getattr(to_task_dict, "start_date", None) or getattr(to_task_dict, "finish_date", None)
                    
                    if from_finish_date and to_start_date:
                        try:
                            from_finish = datetime.strptime(from_finish_date, "%Y-%m-%d")
                            to_start = datetime.strptime(to_start_date, "%Y-%m-%d")
                            link.valid = "No" if to_start < from_finish else "Yes"
                        except (ValueError, TypeError):
                            link.valid = "No"
                    else:
                        link.valid = "No"
                else:
                    link.valid = "No"
                
                links.append(link)
            elif hasattr(link_item, 'link_id'):  # Already a Link object
                links.append(link_item)
            # Skip legacy list format
        
        # Calculate row height for vertical positioning
        row_height = row_frame_height / num_rows if num_rows > 0 else row_frame_height
        
        for link in links:
            # Skip invalid links (valid is None, "No", or any value other than "Yes")
            if link.valid != "Yes":
                continue
            
            # Get style properties
            line_color = link.line_color or "black"
            line_style = link.line_style or "solid"
            link_routing = link.link_routing or "auto"
            
            # Map line style to SVG stroke-dasharray
            stroke_dasharray = None
            if line_style == "dotted":
                stroke_dasharray = "2,2"
            elif line_style == "dashed":
                stroke_dasharray = "5,5"
            # "solid" uses None (no dasharray)
            
            from_task_id = link.from_task_id
            to_task_id = link.to_task_id
            
            # Helper function to create line with style
            def create_line(start, end):
                """Create a line with the link's style properties."""
                line_attrs = {
                    "stroke": line_color,
                    "stroke_width": 1.5,
                    "stroke_linecap": "round"  # Rounded ends for polished appearance
                }
                if stroke_dasharray:
                    line_attrs["stroke_dasharray"] = stroke_dasharray
                return self.dwg.line(start, end, **line_attrs)
            
            # Helper function to add circle marker at origin point
            def add_origin_marker():
                """Add a small circle marker at the link origin point."""
                origin_circle = self.dwg.circle(
                    center=(origin_x, origin_y),
                    r=1.5,  # 1.5 pixel radius (3 pixel diameter) - similar size to arrowhead
                    fill=line_color,
                    stroke=line_color,
                    stroke_width=1
                )
                self.dwg.add(origin_circle)
            
            # Get positions for both tasks - use row_y and row_frame_height for correct vertical positioning
            from_task = self._get_task_position(link.from_task_id, x, row_y, width, row_frame_height, start_date, end_date, num_rows)
            to_task = self._get_task_position(link.to_task_id, x, row_y, width, row_frame_height, start_date, end_date, num_rows)
            
            if not from_task or not to_task:
                continue  # Skip if either task not found
            
            # Get actual task dates to check if they touch on the same date
            from_task_data = None
            to_task_data = None
            for task in self.data.get("tasks", []):
                if task.get("task_id") == link.from_task_id:
                    from_task_data = task
                if task.get("task_id") == link.to_task_id:
                    to_task_data = task
            
            if not from_task_data or not to_task_data:
                continue
            
            # Check if predecessor finishes on same date as successor starts
            from_finish_date_str = from_task_data.get("finish_date", "")
            to_start_date_str = to_task_data.get("start_date", "")
            
            # Determine connection points based on task type (milestone vs regular task)
            # For milestones: use appropriate corner based on link direction
            # For regular tasks: use right edge (predecessor) and left edge (successor)
            from_is_milestone = from_task.get("is_milestone", False)
            to_is_milestone = to_task.get("is_milestone", False)
            
            # Calculate milestone half_size if needed (for corner calculations)
            # half_size = task_height / 2, where task_height = row_height * 0.8
            row_height = row_frame_height / num_rows if num_rows > 0 else row_frame_height
            task_height = row_height * 0.8
            milestone_half_size = task_height / 2
            
            # Determine preliminary positions to calculate link direction
            # We'll refine these based on milestone corners
            if from_is_milestone:
                from_center_x = (from_task["x_start"] + from_task["x_end"]) / 2
            else:
                from_center_x = from_task["x_end"]
            
            if to_is_milestone:
                to_center_x = (to_task["x_start"] + to_task["x_end"]) / 2
            else:
                to_center_x = to_task["x_start"]
            
            # Determine routing based on positions and dates
            same_row = from_task["row_num"] == to_task["row_num"]
            successor_below = to_task["row_num"] > from_task["row_num"]
            successor_above = to_task["row_num"] < from_task["row_num"]
            link_goes_right = to_center_x > from_center_x
            
            # Calculate connection points for milestones based on link direction
            # For circles, connection points are on the circumference
            if from_is_milestone:
                # Origin (From Milestone): choose point on circle circumference based on link direction
                from_center_x = (from_task["x_start"] + from_task["x_end"]) / 2
                from_center_y = from_task["y_center"]
                milestone_radius = milestone_half_size  # Circle radius
                
                if same_row and link_goes_right:
                    # Link goes rightward - use rightmost point on circle
                    origin_x = from_center_x + milestone_radius
                    origin_y = from_center_y
                elif successor_below:
                    # Link goes downward - use bottommost point on circle
                    origin_x = from_center_x
                    origin_y = from_center_y + milestone_radius
                elif successor_above:
                    # Link goes upward - use topmost point on circle
                    origin_x = from_center_x
                    origin_y = from_center_y - milestone_radius
                else:
                    # Fallback to center (shouldn't happen in FS dependencies)
                    origin_x = from_center_x
                    origin_y = from_center_y
            else:
                # Regular task: use right edge
                origin_x = from_task["x_end"]
                origin_y = from_task["y_center"]
            
            if to_is_milestone:
                # Termination (To Milestone): choose point on circle circumference based on link approach direction
                to_center_x = (to_task["x_start"] + to_task["x_end"]) / 2
                to_center_y = to_task["y_center"]
                milestone_radius = milestone_half_size  # Circle radius
                
                if same_row and link_goes_right:
                    # Link approaches from left - use leftmost point on circle
                    term_x = to_center_x - milestone_radius
                    term_y = to_center_y
                elif successor_below:
                    # Link approaches from above - use topmost point on circle
                    term_x = to_center_x
                    term_y = to_center_y - milestone_radius
                elif successor_above:
                    # Link approaches from below - use bottommost point on circle
                    term_x = to_center_x
                    term_y = to_center_y + milestone_radius
                else:
                    # Fallback to center (shouldn't happen in FS dependencies)
                    term_x = to_center_x
                    term_y = to_center_y
            else:
                # Regular task: use left edge
                term_x = to_task["x_start"]
                term_y = to_task["y_center"]
            
            # Check if predecessor finishes on same date as successor starts (actual date comparison)
            same_date = False
            if from_finish_date_str and to_start_date_str:
                try:
                    from_finish_date = datetime.strptime(from_finish_date_str, "%Y-%m-%d")
                    to_start_date = datetime.strptime(to_start_date_str, "%Y-%m-%d")
                    same_date = from_finish_date == to_start_date
                except (ValueError, TypeError):
                    # If date parsing fails, fall back to pixel-based check
                    same_date = abs(origin_x - term_x) < 1.0
            else:
                # Fall back to pixel-based check if dates are missing
                same_date = abs(origin_x - term_x) < 1.0
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
                    # Check if gap is too small to render link (suppress for close elements)
                    gap_days = 0
                    if from_finish_date_str and to_start_date_str:
                        try:
                            from_finish_date = datetime.strptime(from_finish_date_str, "%Y-%m-%d")
                            to_start_date = datetime.strptime(to_start_date_str, "%Y-%m-%d")
                            gap_days = (to_start_date - from_finish_date).days
                        except (ValueError, TypeError):
                            pass  # If date parsing fails, proceed with rendering
                    
                    # Determine suppression threshold based on task/milestone types
                    should_suppress = False
                    if from_is_milestone and to_is_milestone:
                        # Milestone to Milestone: suppress if gap < 6 days (≤ 5 days)
                        should_suppress = gap_days < 6
                    elif from_is_milestone or to_is_milestone:
                        # Task to Milestone or Milestone to Task: suppress if gap < 4 days (≤ 3 days)
                        should_suppress = gap_days < 4
                    else:
                        # Task to Task: suppress if gap ≤ 3 days
                        should_suppress = gap_days <= 3
                    
                    if should_suppress:
                        # Skip rendering for close elements on same row
                        continue
                    
                    # Render link for elements with sufficient gap
                    # Shorten line by arrowhead size so it ends at arrowhead base
                    arrow_size = 5
                    line_end_x = term_x - arrow_size  # Arrow points left, base is to the right
                    self.dwg.add(create_line((origin_x, origin_y), (line_end_x, term_y)))
                    self._render_arrowhead(term_x, term_y, "left", arrow_size, line_color)
                    add_origin_marker()
            else:
                # Different rows
                if same_date:
                    # Case 2a/3a: No Gap (Aligned Vertically)
                    # Check if alignment is perfect enough to collapse to single vertical segment
                    if abs(origin_x - term_x) < 2.0:
                        # Perfect alignment - single vertical segment
                        if to_task["row_num"] > from_task["row_num"]:
                            # Successor below - downward arrow
                            # Shorten line by arrowhead size so it ends at arrowhead base
                            arrow_size = 5
                            line_end_y = term_y - arrow_size  # Arrow points down, base is above
                            self.dwg.add(create_line((origin_x, origin_y), (term_x, line_end_y)))
                            self._render_arrowhead(term_x, term_y, "down", arrow_size, line_color)
                            add_origin_marker()
                        else:
                            # Successor above - upward arrow
                            # Shorten line by arrowhead size so it ends at arrowhead base
                            arrow_size = 5
                            line_end_y = term_y + arrow_size  # Arrow points up, base is below
                            self.dwg.add(create_line((origin_x, origin_y), (term_x, line_end_y)))
                            self._render_arrowhead(term_x, term_y, "up", arrow_size, line_color)
                            add_origin_marker()
                    else:
                        # Not perfectly aligned - use routing pattern
                        arrow_size = 5
                        
                        if link_routing == "HV":
                            # Horizontal-Vertical: Go horizontal first, then vertical
                            if to_task["row_num"] > from_task["row_num"]:
                                # Successor below - H-V downward
                                line_end_y = term_y - arrow_size  # Arrow points down, base is above
                                self.dwg.add(create_line((origin_x, origin_y), (term_x, origin_y)))
                                self.dwg.add(create_line((term_x, origin_y), (term_x, line_end_y)))
                                self._render_arrowhead(term_x, term_y, "down", arrow_size, line_color)
                            else:
                                # Successor above - H-V upward
                                line_end_y = term_y + arrow_size  # Arrow points up, base is below
                                self.dwg.add(create_line((origin_x, origin_y), (term_x, origin_y)))
                                self.dwg.add(create_line((term_x, origin_y), (term_x, line_end_y)))
                                self._render_arrowhead(term_x, term_y, "up", arrow_size, line_color)
                            add_origin_marker()
                        elif link_routing == "VH":
                            # Vertical-Horizontal: Go vertical first, then horizontal
                            # Determine arrow direction based on link direction (left/right)
                            if link_goes_right:
                                # Link goes right - arrow points left (into task)
                                line_end_x = term_x - arrow_size  # Arrow points left, base is to the right
                                self.dwg.add(create_line((origin_x, origin_y), (origin_x, term_y)))
                                self.dwg.add(create_line((origin_x, term_y), (line_end_x, term_y)))
                                self._render_arrowhead(term_x, term_y, "left", arrow_size, line_color)
                            else:
                                # Link goes left (shouldn't happen in FS, but handle gracefully)
                                line_end_x = term_x + arrow_size  # Arrow points right, base is to the left
                                self.dwg.add(create_line((origin_x, origin_y), (origin_x, term_y)))
                                self.dwg.add(create_line((origin_x, term_y), (line_end_x, term_y)))
                                self._render_arrowhead(term_x, term_y, "right", arrow_size, line_color)
                            add_origin_marker()
                        else:
                            # Auto: Use V-H-V pattern (default behavior)
                            # Calculate row midpoint y
                            mid_y = (origin_y + term_y) / 2
                            
                            if to_task["row_num"] > from_task["row_num"]:
                                # Successor below - V-H-V downward
                                # Shorten final vertical segment so it ends at arrowhead base
                                line_end_y = term_y - arrow_size  # Arrow points down, base is above
                                self.dwg.add(create_line((origin_x, origin_y), (origin_x, mid_y)))
                                self.dwg.add(create_line((origin_x, mid_y), (term_x, mid_y)))
                                self.dwg.add(create_line((term_x, mid_y), (term_x, line_end_y)))
                                self._render_arrowhead(term_x, term_y, "down", arrow_size, line_color)
                            else:
                                # Successor above - V-H-V upward
                                line_end_y = term_y + arrow_size  # Arrow points up, base is below
                                self.dwg.add(create_line((origin_x, origin_y), (origin_x, mid_y)))
                                self.dwg.add(create_line((origin_x, mid_y), (term_x, mid_y)))
                                self.dwg.add(create_line((term_x, mid_y), (term_x, line_end_y)))
                                self._render_arrowhead(term_x, term_y, "up", arrow_size, line_color)
                            add_origin_marker()
                else:
                    # Case 2b/3b: Positive Gap/Lag (Successor Starts Later)
                    arrow_size = 5
                    
                    if link_routing == "HV":
                        # Horizontal-Vertical: Go horizontal first, then vertical
                        if to_task["row_num"] > from_task["row_num"]:
                            # Successor below - H-V downward
                            line_end_y = term_y - arrow_size  # Arrow points down, base is above
                            self.dwg.add(create_line((origin_x, origin_y), (term_x, origin_y)))
                            self.dwg.add(create_line((term_x, origin_y), (term_x, line_end_y)))
                            self._render_arrowhead(term_x, term_y, "down", arrow_size, line_color)
                        else:
                            # Successor above - H-V upward
                            line_end_y = term_y + arrow_size  # Arrow points up, base is below
                            self.dwg.add(create_line((origin_x, origin_y), (term_x, origin_y)))
                            self.dwg.add(create_line((term_x, origin_y), (term_x, line_end_y)))
                            self._render_arrowhead(term_x, term_y, "up", arrow_size, line_color)
                        add_origin_marker()
                    elif link_routing == "VH":
                        # Vertical-Horizontal: Go vertical first, then horizontal
                        # Determine arrow direction based on link direction (left/right)
                        if link_goes_right:
                            # Link goes right - arrow points left (into task)
                            line_end_x = term_x - arrow_size  # Arrow points left, base is to the right
                            self.dwg.add(create_line((origin_x, origin_y), (origin_x, term_y)))
                            self.dwg.add(create_line((origin_x, term_y), (line_end_x, term_y)))
                            self._render_arrowhead(term_x, term_y, "left", arrow_size, line_color)
                        else:
                            # Link goes left (shouldn't happen in FS, but handle gracefully)
                            line_end_x = term_x + arrow_size  # Arrow points right, base is to the left
                            self.dwg.add(create_line((origin_x, origin_y), (origin_x, term_y)))
                            self.dwg.add(create_line((origin_x, term_y), (line_end_x, term_y)))
                            self._render_arrowhead(term_x, term_y, "right", arrow_size, line_color)
                        add_origin_marker()
                    else:
                        # Auto: Use V-H-V pattern (default behavior)
                        # Calculate row midpoint y
                        mid_y = (origin_y + term_y) / 2
                        
                        if to_task["row_num"] > from_task["row_num"]:
                            # Successor below - V-H-V downward
                            # Segment 1: Vertical down from origin to row midpoint
                            # Segment 2: Horizontal right to align with successor
                            # Segment 3: Vertical down to termination (shortened to arrowhead base)
                            line_end_y = term_y - arrow_size  # Arrow points down, base is above
                            self.dwg.add(create_line((origin_x, origin_y), (origin_x, mid_y)))
                            self.dwg.add(create_line((origin_x, mid_y), (term_x, mid_y)))
                            self.dwg.add(create_line((term_x, mid_y), (term_x, line_end_y)))
                            self._render_arrowhead(term_x, term_y, "down", arrow_size, line_color)
                        else:
                            # Successor above - V-H-V upward
                            # Segment 1: Vertical up from origin to row midpoint
                            # Segment 2: Horizontal right to align with successor
                            # Segment 3: Vertical up to termination (shortened to arrowhead base)
                            line_end_y = term_y + arrow_size  # Arrow points up, base is below
                            self.dwg.add(create_line((origin_x, origin_y), (origin_x, mid_y)))
                            self.dwg.add(create_line((origin_x, mid_y), (term_x, mid_y)))
                            self.dwg.add(create_line((term_x, mid_y), (term_x, line_end_y)))
                            self._render_arrowhead(term_x, term_y, "up", arrow_size, line_color)
                        add_origin_marker()

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
                                       fill="lightgrey", 
                                       stroke=self.config.general.frame_border_color, 
                                       stroke_width=self.config.general.frame_border_width_light))
            self.render_scale_interval(x, current_y, width, scale_height, start_date, end_date, interval, time_scale)
            current_y += scale_height

        row_y = current_y
        num_rows = self._get_frame_config("num_rows", 1)
        # Render row frame with only left and right borders (top/bottom borders overlap with scale and footer)
        # Draw left border
        self.dwg.add(self.dwg.line((x, row_y), (x, row_y + row_frame_height),
                                   stroke=self.config.general.frame_border_color,
                                   stroke_width=self.config.general.frame_border_width_light))
        # Draw right border
        self.dwg.add(self.dwg.line((x + width, row_y), (x + width, row_y + row_frame_height),
                                   stroke=self.config.general.frame_border_color,
                                   stroke_width=self.config.general.frame_border_width_light))
        
        # Conditionally add top border if header is 0 and no scales are shown
        header_height = self._get_frame_config("header_height", 20)
        if header_height <= 0 and len(scale_configs) == 0:
            # Draw top border
            self.dwg.add(self.dwg.line((x, row_y), (x + width, row_y),
                                       stroke=self.config.general.frame_border_color,
                                       stroke_width=self.config.general.frame_border_width_light))
        
        # Conditionally add bottom border if footer is 0
        footer_height = self._get_frame_config("footer_height", 20)
        if footer_height <= 0:
            # Draw bottom border
            self.dwg.add(self.dwg.line((x, row_y + row_frame_height), (x + width, row_y + row_frame_height),
                                       stroke=self.config.general.frame_border_color,
                                       stroke_width=self.config.general.frame_border_width_light))

        if self._get_frame_config("horizontal_gridlines", False):
            for i in range(1, num_rows):  # Exclude first and last to avoid overlapping row frame border
                y_pos = row_y + i * (row_frame_height / num_rows)
                self.dwg.add(self.dwg.line((x, y_pos), (x + width, y_pos), stroke="lightgrey", stroke_width=0.5))
        
        # Render row numbers if enabled (after gridlines, before tasks)
        if self._get_frame_config("show_row_numbers", False):
            row_height = row_frame_height / num_rows if num_rows > 0 else row_frame_height
            for i in range(num_rows):
                # Calculate Y position using the same alignment factor as scales
                row_top = row_y + i * row_height
                row_center_y = row_top + row_height * self.config.general.row_number_vertical_alignment_factor
                # Position text 5px from left edge
                text_x = x + 5
                # Create text element with grey color
                text_element = self.dwg.text(
                    str(i + 1),  # 1-based row number
                    insert=(text_x, row_center_y),
                    fill="grey",
                    font_size=str(self.config.general.row_number_font_size) + "px",
                    font_family=f"{self.config.general.font_family}, sans-serif",
                    text_anchor="start",
                    dominant_baseline="middle"
                )
                self.dwg.add(text_element)

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
                                               stroke="lightgrey", stroke_width=line_weight))
                prev_x = x_pos
                current_date = self.next_period(current_date, interval)

        # Render swimlanes (after gridlines, before pipes/curtains/tasks)
        self.render_swimlanes(x, row_y, width, row_frame_height, num_rows)
        
        # Render pipes and curtains (after swimlanes, before tasks)
        self.render_pipes(x, row_y, width, row_frame_height, start_date, end_date)
        self.render_curtains(x, row_y, width, row_frame_height, start_date, end_date)
        
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
                                           stroke="grey", stroke_width=0.5))
            if prev_x < x + width and x_pos > x:
                label_x = (max(x, prev_x) + min(x + width, x_pos)) / 2
                label_y = y + height * self.config.general.scale_vertical_alignment_factor
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
                                               font_size=str(self.config.general.scale_font_size), font_family=self.config.general.font_family, dominant_baseline="middle"))
            prev_x = x_pos
            current_date = next_date

    def _wrap_text_to_lines(self, text: str, max_width: float, font_size: int = 10) -> list:
        """Wrap text into lines that fit within max_width, handling both explicit line breaks and word wrapping.
        
        Args:
            text: The text to wrap
            max_width: Maximum width in pixels for each line
            font_size: Font size in pixels (default 10 for text boxes)
            
        Returns:
            List of text lines that fit within max_width
        """
        if font_size is None:
            font_size = self.config.general.note_font_size
        # Create font metrics for note font
        note_font = QFont(self.config.general.font_family, font_size)
        note_font_metrics = QFontMetrics(note_font)
        
        lines = []
        # First, split by explicit line breaks (newlines)
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                # Empty line - preserve it
                lines.append("")
                continue
            
            # Word wrap this paragraph
            words = paragraph.split()
            current_line = ""
            
            for word in words:
                # Test if adding this word would exceed max_width
                test_line = current_line + (" " if current_line else "") + word
                test_width = note_font_metrics.horizontalAdvance(test_line)
                
                if test_width <= max_width:
                    # Word fits - add it to current line
                    current_line = test_line
                else:
                    # Word doesn't fit
                    if current_line:
                        # Save current line and start new one
                        lines.append(current_line)
                        current_line = word
                    else:
                        # Single word is too long - truncate it
                        # Find how many characters fit
                        char_count = 0
                        for i in range(1, len(word) + 1):
                            if note_font_metrics.horizontalAdvance(word[:i]) <= max_width:
                                char_count = i
                            else:
                                break
                        if char_count > 0:
                            lines.append(word[:char_count])
                            # Handle remaining characters in next iteration
                            remaining = word[char_count:]
                            if remaining:
                                # Recursively handle remaining part
                                remaining_lines = self._wrap_text_to_lines(remaining, max_width, font_size)
                                lines.extend(remaining_lines)
                        else:
                            # Even first character doesn't fit - add empty line and skip
                            lines.append("")
                        current_line = ""
            
            # Add remaining line if any
            if current_line:
                lines.append(current_line)
        
        return lines

    def render_notes(self):
        """Render notes (rectangles with text) above all other elements.
        
        Notes are positioned absolutely on the chart and render last so they appear on top.
        Supports multi-line text with word wrapping and explicit line breaks.
        """
        notes = self.data.get("notes", [])
        if not notes:
            return
        
        logging.debug(f"Rendering {len(notes)} notes")
        
        # Create font for notes
        note_font = QFont(self.config.general.font_family, self.config.general.note_font_size)
        note_font_metrics = QFontMetrics(note_font)
        line_height = note_font_metrics.height()
        
        for note_data in notes:
            # Convert dict to Note object if needed
            if isinstance(note_data, dict):
                note = Note.from_dict(note_data)
            else:
                note = note_data
            
            if not note or not note.text:
                continue
            
            # Render rectangle with border and background
            self.dwg.add(self.dwg.rect(
                insert=(note.x, note.y),
                size=(note.width, note.height),
                fill="white",
                stroke="grey",
                stroke_width=0.5
            ))
            
            # Wrap text into lines that fit within the note width
            # Leave some padding (e.g., 2px on each side)
            # Note: Qt font metrics may measure text wider than SVG renders,
            # so we add a small correction factor to account for this mismatch
            padding = 2
            font_metrics_correction = 1.2  # Adjust if SVG renders more compactly than Qt measures
            available_width = max(1, (note.width - (2 * padding)) * font_metrics_correction)
            logging.debug(f"Note width: {note.width}, padding: {padding}, available_width: {available_width} (with {font_metrics_correction}x correction)")
            text_lines = self._wrap_text_to_lines(note.text, available_width, font_size=self.config.general.note_font_size)
            logging.debug(f"Wrapped text into {len(text_lines)} lines: {text_lines}")
            
            if not text_lines:
                continue
            
            # Calculate horizontal alignment and text_x position
            text_align = note.text_align
            if text_align == "Left":
                text_x = note.x + padding
                text_anchor = "start"
            elif text_align == "Right":
                text_x = note.x + note.width - padding
                text_anchor = "end"
            else:  # Center (default)
                text_x = note.x + note.width / 2
                text_anchor = "middle"
            
            # Calculate vertical alignment and start_y position
            vertical_align = note.vertical_align
            total_text_height = len(text_lines) * line_height
            
            if vertical_align == "Top":
                start_y = note.y + padding + line_height * 0.75  # 0.75 for baseline adjustment
            elif vertical_align == "Bottom":
                start_y = note.y + note.height - total_text_height - padding + line_height * 0.75
            else:  # Middle (default)
                start_y = note.y + (note.height - total_text_height) / 2 + line_height * 0.75
            
            # Render each line
            for i, line in enumerate(text_lines):
                line_y = start_y + (i * line_height)
                self.dwg.add(self.dwg.text(
                    line,
                    insert=(text_x, line_y),
                    font_size=str(self.config.general.note_font_size) + "px",
                    font_family=self.config.general.font_family,
                    fill="black",
                    text_anchor=text_anchor,
                    dominant_baseline="auto"
                ))

    def render(self):
        logging.debug("Starting render")
        os.makedirs(self.output_folder, exist_ok=True)
        self.render_outer_frame()  # Background only
        self.render_header()
        self.render_footer()
        self.render_inner_frame()
        self.render_single_timeline()
        self.render_notes()  # Render notes after all other elements
        self.render_outer_frame_border()  # Border rendered last
        self.dwg.save()
        logging.debug("Render completed")