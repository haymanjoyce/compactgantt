# File: gantt_chart_service.py
import svgwrite
from datetime import datetime, timedelta
import os
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QFontMetrics
from config.app_config import AppConfig
import logging
from models.link import Link
from models.task import Task
from utils.conversion import is_valid_internal_date
from models.pipe import Pipe
from models.curtain import Curtain
from models.swimlane import Swimlane
from models.note import Note

# Logging is configured centrally in utils/logging_config.py

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

    def _get_frame_config(self, key: str, default):
        """Get a value from frame_config with a default fallback."""
        return self.data["frame_config"].get(key, default)

    @pyqtSlot(dict)
    def generate_svg(self, data):
        # Update font and font_metrics to use current config values
        self.font = QFont(self.config.general.font_family, self.config.general.task_font_size)
        self.font_metrics = QFontMetrics(self.font)
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
            self.render()
            svg_path = os.path.abspath(os.path.join(self.output_folder, self.output_filename))
            self.svg_generated.emit(svg_path)
            return svg_path
        except Exception as e:
            logging.error(f"SVG generation failed: {e}", exc_info=True)
            self.svg_generated.emit("")
            return

    def _parse_internal_date(self, date_str: str) -> datetime:
        """Safely parse an internal date string (yyyy-mm-dd), returning None if invalid."""
        if not date_str:
            return None
        fmt = "%Y-%m-%d"
        try:
            fmt = self.config.general.chart_date_config.get_internal_format()
        except Exception:
            pass  # Fallback to default
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except (ValueError, TypeError):
            return None
    
    def _convert_to_model_object(self, data, model_class):
        """Convert data to model object, handling both dict and object inputs.
        
        Args:
            data: Either a dict or an instance of model_class
            model_class: The model class (e.g., Pipe, Curtain, Swimlane, Task, Link, Note)
            
        Returns:
            Instance of model_class
        """
        if isinstance(data, dict):
            return model_class.from_dict(data)
        elif isinstance(data, model_class):
            return data
        else:
            # Unexpected type - try to convert anyway
            logging.warning(f"Unexpected data type for {model_class.__name__}: {type(data)}")
            return model_class.from_dict(data) if hasattr(model_class, 'from_dict') else data

    def render_outer_frame(self):
        width = self._get_frame_config("outer_width", self.config.general.outer_width)
        height = self._get_frame_config("outer_height", self.config.general.outer_height)
        # Render background first
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(width, height), fill="white", stroke="none"))

    def render_outer_frame_border(self):
        """Render outer frame border last so it appears on top of all other elements."""
        width = self._get_frame_config("outer_width", self.config.general.outer_width)
        height = self._get_frame_config("outer_height", self.config.general.outer_height)
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(width, height), fill="none", 
                                   stroke=self.config.general.frame_border_color, 
                                   stroke_width=self.config.general.frame_border_width_heavy))

    def render_header(self):
        margins = self._get_frame_config("margins", (10, 10, 10, 10))
        width = self._get_frame_config("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        height = self._get_frame_config("header_height", 20)
        
        # Skip rendering if height is 0
        if height <= 0:
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

    def render_footer(self):
        margins = self._get_frame_config("margins", (10, 10, 10, 10))
        width = self._get_frame_config("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        height = self._get_frame_config("footer_height", 20)
        
        # Skip rendering if height is 0
        if height <= 0:
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

    def render_single_timeline(self):
        """Render a single continuous timeline instead of multiple time frames."""
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
        chart_start_dt = self._parse_internal_date(chart_start_str)
        if not chart_end_str and chart_start_dt:
            chart_end_str = (chart_start_dt + timedelta(days=30)).strftime("%Y-%m-%d")
        
        chart_start = chart_start_dt or self._parse_internal_date("2024-12-30")
        chart_end = self._parse_internal_date(chart_end_str) if chart_end_str else None
        if not chart_start or not chart_end:
            logging.warning("Invalid chart start/end date; aborting render")
            return
        
        # Render scales, rows, and tasks in one continuous timeline
        row_y, row_frame_height = self.render_scales_and_rows(margins[3], inner_y, inner_width, inner_height, chart_start, chart_end)
        # Render links after tasks, using row frame position and height
        self.render_links(margins[3], row_y, inner_width, row_frame_height, chart_start, chart_end)


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
                          label_content: str, is_milestone: bool, task_date_format: Optional[str] = None) -> str:
        """Format label text based on label_content option.
        
        Args:
            task_name: The task name
            start_date_str: Start date in internal format (yyyy-mm-dd)
            finish_date_str: Finish date in internal format (yyyy-mm-dd)
            label_content: One of "None", "Name only", "Date only", "Name and Date"
            is_milestone: Whether this is a milestone (single date)
            task_date_format: Optional task-specific date format name (e.g., "dd/MM/yyyy"), None uses global chart format
            
        Returns:
            Formatted label text, or empty string if label_content is "None"
        """
        from utils.conversion import internal_to_display_date
        from config.date_config import DateConfig, DATE_FORMAT_OPTIONS
        
        # Use task-specific date format if provided, otherwise use chart_date_config
        if task_date_format and task_date_format in DATE_FORMAT_OPTIONS:
            # Create DateConfig from task-specific format
            date_config = DateConfig.from_format_name(task_date_format)
        else:
            # Use chart_date_config for date formatting in chart labels (global default)
            date_config = self.config.general.chart_date_config
        
        if label_content == "None":
            return ""
        elif label_content == "Name only":
            return task_name
        elif label_content == "Date only":
            if is_milestone:
                # For milestones, show single date
                date_str = start_date_str if start_date_str else finish_date_str
                return internal_to_display_date(date_str, date_config) if date_str else ""
            else:
                # For tasks, show date range
                start_display = internal_to_display_date(start_date_str, date_config) if start_date_str else ""
                finish_display = internal_to_display_date(finish_date_str, date_config) if finish_date_str else ""
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
                date_display = internal_to_display_date(date_str, date_config) if date_str else ""
                if date_display:
                    return f"{task_name} ({date_display})"
                else:
                    return task_name
            else:
                # For tasks: "Task Name (01/01/2025 - 31/01/2025)"
                start_display = internal_to_display_date(start_date_str, date_config) if start_date_str else ""
                finish_display = internal_to_display_date(finish_date_str, date_config) if finish_date_str else ""
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

    def _render_id_badge(self, id_text: str, anchor_x: float, center_y: float, element_height: float, place_left: bool = True):
        """Render a small ID badge near a task or milestone.
        
        Args:
            id_text: Text to display (e.g., "#12")
            anchor_x: Reference x position (start of bar or milestone center)
            center_y: Reference y position (bar center or milestone center)
            element_height: Height of the task/milestone element (for vertical alignment)
            place_left: If True, place badge to the left; otherwise to the right
        """
        if not id_text:
            return
        
        font_size = max(self.config.general.chart.id_badge_font_size, 8)
        pad_x = 3
        pad_y = 2
        margin = 4  # gap from the bar/circle
        vertical_factor = self.config.general.chart.id_badge_vertical_alignment_factor
        text_vertical_factor = self.config.general.chart.id_badge_text_vertical_alignment_factor
        
        # Use font metrics for the configured font size
        temp_font = QFont(self.config.general.font_family, font_size)
        temp_metrics = QFontMetrics(temp_font)
        text_width = temp_metrics.horizontalAdvance(id_text)
        text_height = font_size * 1.2
        badge_w = text_width + pad_x * 2
        badge_h = text_height + pad_y * 2
        
        rect_x = anchor_x - badge_w - margin if place_left else anchor_x + margin
        # Apply vertical alignment factor: 0.0=top, 0.5=center, 1.0=bottom relative to element height
        badge_center_y = center_y - element_height * (0.5 - vertical_factor)
        rect_y = badge_center_y - badge_h / 2
        
        # Background + border - add to overlay group so badges float above all other artifacts
        self.id_badge_overlay.add(self.dwg.rect(
            insert=(rect_x, rect_y),
            size=(badge_w, badge_h),
            rx=2, ry=2,
            fill="#f8f8f8",
            stroke="#555",
            stroke_width=0.6
        ))
        
        text_x = rect_x + pad_x
        # Calculate text position within badge using the factor
        # 0.0 = top of badge, 0.5 = center, 1.0 = bottom of badge
        text_y = rect_y + badge_h * text_vertical_factor
        self.id_badge_overlay.add(self.dwg.text(
            id_text,
            insert=(text_x, text_y),
            font_size=str(font_size),
            font_family=self.config.general.font_family,
            fill="#111",
            dominant_baseline="middle",
            text_anchor="start"
        ))

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
        self.dwg.add(self.dwg.text(task_name_display, insert=(label_x, label_y_base),
                                   font_size=str(self.config.general.task_font_size), font_family=self.config.general.font_family, fill=text_color,
                                   text_anchor="middle", dominant_baseline="middle"))


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

    def _extract_task_info(self, task: dict) -> dict:
        """Extract task information using key-based lookups.
        
        Args:
            task: Task dictionary with key-based fields
            
        Returns:
            Dictionary with extracted task info: start_date_str, finish_date_str, is_milestone,
            label_placement, label_content, label_hide, task_name, fill_color, label_horizontal_offset,
            label_text, task_row, task_id, date_format
        """
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
        task_row = task.get("row_number", 1)
        task_id = task.get("task_id")
        date_format = task.get("date_format")  # Get task-specific date format, None uses global
        
        # Format label text based on label_content, using task-specific date format if provided
        label_text = self._format_label_text(task_name, start_date_str, finish_date_str, label_content, is_milestone, task_date_format=date_format)
        
        return {
            "start_date_str": start_date_str,
            "finish_date_str": finish_date_str,
            "is_milestone": is_milestone,
            "label_placement": label_placement,
            "label_content": label_content,
            "label_hide": label_hide,
            "task_name": task_name,
            "fill_color": fill_color,
            "label_horizontal_offset": label_horizontal_offset,
            "label_text": label_text,
            "task_row": task_row,
            "task_id": task_id,
            "date_format": date_format
        }
    
    def _validate_and_parse_task_dates(self, task_info: dict, start_date: datetime, end_date: datetime, num_rows: int) -> tuple:
        """Validate and parse task dates, checking if task should be rendered.
        
        Args:
            task_info: Dictionary with task information from _extract_task_info()
            start_date: Timeline start date
            end_date: Timeline end date
            num_rows: Number of rows in chart
            
        Returns:
            Tuple of (task_start, task_finish) as datetime objects, or (None, None) if invalid
        """
        start_date_str = task_info["start_date_str"]
        finish_date_str = task_info["finish_date_str"]
        is_milestone = task_info["is_milestone"]
        task_name = task_info["task_name"]
        task_row = task_info["task_row"]
        
        if not start_date_str and not finish_date_str:
            return (None, None)
        
        # Validate that both dates are valid
        if not is_valid_internal_date(start_date_str):
            logging.warning(f"Skipping task {task_name} due to invalid start date: {start_date_str}")
            return (None, None)
        if not is_valid_internal_date(finish_date_str):
            logging.warning(f"Skipping task {task_name} due to invalid finish date: {finish_date_str}")
            return (None, None)
        
        # Parse dates using centralized helper
        date_to_use = start_date_str if start_date_str else finish_date_str
        task_start = self._parse_internal_date(date_to_use)
        task_finish = task_start
        if not is_milestone and start_date_str and finish_date_str:
            task_start = self._parse_internal_date(start_date_str)
            task_finish = self._parse_internal_date(finish_date_str)
        if not task_start or not task_finish:
            logging.warning(f"Skipping task {task_name} due to invalid date(s)")
            return (None, None)
        
        # Skip invalid tasks where finish date is before start date
        if task_finish < task_start:
            return (None, None)
        
        # Skip tasks outside timeline range
        if task_finish < start_date or task_start > end_date:
            return (None, None)
        
        # Skip tasks with row numbers beyond available rows
        if task_row > num_rows:
            return (None, None)
        
        return (task_start, task_finish)
    
    def _calculate_task_geometry(self, task_start: datetime, task_finish: datetime, task_row: int,
                                 x: float, y: float, width: float, height: float,
                                 start_date: datetime, end_date: datetime, num_rows: int,
                                 time_scale: float, row_height: float, task_height: float) -> dict:
        """Calculate task position and dimensions.
        
        Args:
            task_start: Task start date (datetime)
            task_finish: Task finish date (datetime)
            task_row: Task row number (1-based)
            x, y: Timeline position
            width, height: Timeline dimensions
            start_date, end_date: Timeline date range
            num_rows: Number of rows
            time_scale: Pixels per day
            row_height: Height per row
            task_height: Height of task bar
            
        Returns:
            Dictionary with: x_start, x_end, width_task, y_task, row_num
        """
        total_days = max((end_date - start_date).days, 1)
        row_num = task_row - 1  # Convert to 0-based index
        x_start = x + max((task_start - start_date).days, 0) * time_scale
        x_end = x + min((task_finish - start_date).days + 1, total_days) * time_scale
        width_task = time_scale if task_start == task_finish else max(x_end - x_start, time_scale)
        y_task = y + row_num * row_height
        
        return {
            "x_start": x_start,
            "x_end": x_end,
            "width_task": width_task,
            "y_task": y_task,
            "row_num": row_num
        }
    
    def _render_milestone(self, center_x: float, center_y: float, half_size: float, fill_color: str,
                         label_text: str, label_hide: bool, label_placement: str,
                         label_horizontal_offset: float, y_task: float, row_height: float,
                         task_id=None, show_ids: bool = False):
        """Render a milestone as a circle.
        
        Args:
            center_x, center_y: Center position of milestone
            half_size: Half the size of the milestone (radius)
            fill_color: Fill color for milestone
            label_text: Text to display in label
            label_hide: Whether to hide label
            label_placement: Label placement ("Inside" or "Outside")
            label_horizontal_offset: Horizontal offset for label
            y_task: Y position of task row
            row_height: Height of task row
        """
        # Render as a circle - use fill_color from task
        self.dwg.add(self.dwg.circle(center=(center_x, center_y), r=half_size, 
                                     fill=fill_color, stroke="black", stroke_width=0.5))
        
        # Always render ID badge if enabled
        if show_ids:
            # Anchor at left edge of the milestone so spacing matches tasks
            self._render_id_badge(f"#{task_id}" if task_id else "", center_x - half_size, center_y, element_height=half_size * 2, place_left=True)
        
        if not label_hide and label_placement == "Outside":
            # Use proportional positioning: center_y is at row_height * 0.5, apply factor to row_height
            label_y_base = y_task + row_height * self.config.general.task_vertical_alignment_factor
            milestone_right = center_x + half_size
            self._render_outside_label(label_text, milestone_right, center_y, label_y_base, label_horizontal_offset)
    
    def _render_single_task(self, x_start: float, x_end: float, width_task: float, y_task: float,
                           task_height: float, row_height: float, fill_color: str,
                           label_text: str, label_hide: bool, label_placement: str,
                           label_horizontal_offset: float, x: float, width: float,
                           task_id=None, show_ids: bool = False):
        """Render a single task bar.
        
        Args:
            x_start, x_end: Task start and end x positions
            width_task: Width of task bar
            y_task: Y position of task row
            task_height: Height of task bar
            row_height: Height of task row
            fill_color: Fill color for task
            label_text: Text to display in label
            label_hide: Whether to hide label
            label_placement: Label placement ("Inside" or "Outside")
            label_horizontal_offset: Horizontal offset for label
            x, width: Timeline boundaries
        """
        if x_start < x + width:
            y_offset = (row_height - task_height) / 2
            rect_y = y_task + y_offset
            corner_radius = 3
            self.dwg.add(self.dwg.rect(insert=(x_start, rect_y), size=(width_task, task_height), 
                                      fill=fill_color, stroke="black", stroke_width=0.5,
                                      rx=corner_radius, ry=corner_radius))
            
            # Render ID badge if enabled
            if show_ids:
                self._render_id_badge(f"#{task_id}" if task_id else "", x_start, rect_y + task_height / 2, element_height=task_height, place_left=True)
            
            if not label_hide:
                # Use proportional positioning within task bar
                label_y_base = rect_y + task_height * self.config.general.task_vertical_alignment_factor
                
                if label_placement == "Inside":
                    # Simple inside label rendering - no multi-time-frame logic needed
                    self._render_inside_label(label_text, x_start, width_task, label_y_base, fill_color)
                elif label_placement == "Outside":
                    self._render_outside_label(label_text, x_end, rect_y + task_height / 2, 
                                              label_y_base, label_horizontal_offset)

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
        tasks = self.data.get("tasks", [])
        show_ids = getattr(self.config.general, "show_ids_on_chart", False)
        if not tasks:
            logging.warning("No tasks found in data! Tasks list is empty.")
            return
        
        # Calculate scales and dimensions
        total_days = max((end_date - start_date).days, 1)
        time_scale = width / total_days if total_days > 0 else width
        row_height = height / num_rows if num_rows > 0 else height
        task_height = row_height * 0.8

        for task in tasks:
            # Extract task information using key-based lookups
            task_info = self._extract_task_info(task)
            
            # Validate and parse dates
            task_start, task_finish = self._validate_and_parse_task_dates(
                task_info, start_date, end_date, num_rows
            )
            if not task_start or not task_finish:
                continue
            
            # Calculate task geometry
            geometry = self._calculate_task_geometry(
                task_start, task_finish, task_info["task_row"],
                x, y, width, height, start_date, end_date, num_rows,
                time_scale, row_height, task_height
            )
            
            # Render milestone or regular task
            task_id = task_info.get("task_id")
            if task_info["is_milestone"]:
                half_size = task_height / 2
                finish_date_str = task_info["finish_date_str"]
                center_x = geometry["x_end"] if finish_date_str else geometry["x_start"]
                center_y = geometry["y_task"] + row_height * 0.5
                
                self._render_milestone(
                    center_x, center_y, half_size, task_info["fill_color"],
                    task_info["label_text"], task_info["label_hide"], task_info["label_placement"],
                    task_info["label_horizontal_offset"], geometry["y_task"], row_height,
                    task_id=task_id, show_ids=show_ids
                )
            else:
                self._render_single_task(
                    geometry["x_start"], geometry["x_end"], geometry["width_task"],
                    geometry["y_task"], task_height, row_height, task_info["fill_color"],
                    task_info["label_text"], task_info["label_hide"], task_info["label_placement"],
                    task_info["label_horizontal_offset"], x, width,
                    task_id=task_id, show_ids=show_ids
                )

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
            
            date_to_use = start_date_str if start_date_str else finish_date_str
            task_start = self._parse_internal_date(date_to_use)
            task_finish = task_start
            if not is_milestone and start_date_str and finish_date_str:
                task_start = self._parse_internal_date(start_date_str)
                task_finish = self._parse_internal_date(finish_date_str)
            if not task_start or not task_finish:
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
            pipe = self._convert_to_model_object(pipe_data, Pipe)
            
            # Validate date
            if not is_valid_internal_date(pipe.date):
                continue
            
            pipe_date = self._parse_internal_date(pipe.date)
            if not pipe_date:
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

    def _extract_swimlanes(self) -> list:
        """Extract and convert swimlane data to Swimlane objects.
        
        Returns:
            List of Swimlane objects, empty list if no swimlanes
        """
        swimlanes_data = self.data.get("swimlanes", [])
        if not swimlanes_data:
            return []
        
        # Convert dicts to Swimlane objects if needed
        swimlanes = []
        for swimlane_data in swimlanes_data:
            swimlanes.append(self._convert_to_model_object(swimlane_data, Swimlane))
        
        return swimlanes
    
    def _calculate_swimlane_row_positions(self, swimlane, current_first_row: int, num_rows: int) -> tuple:
        """Calculate first and last row positions for a swimlane.
        
        Args:
            swimlane: Swimlane object
            current_first_row: Current first row (1-based)
            num_rows: Total number of rows
            
        Returns:
            Tuple of (first_row, last_row, is_valid) where is_valid indicates if swimlane is within bounds
        """
        first_row = current_first_row
        last_row = current_first_row + swimlane.row_count - 1
        
        # Validate row numbers
        is_valid = first_row >= 1 and last_row <= num_rows
        
        return (first_row, last_row, is_valid)
    
    def _render_swimlane_divider(self, x: float, width: float, divider_y: float):
        """Render a horizontal divider line for a swimlane.
        
        Args:
            x: X position
            width: Width of divider
            divider_y: Y position of divider
        """
        self.dwg.add(self.dwg.line(
            (x, divider_y),
            (x + width, divider_y),
            stroke="grey",
            stroke_width=0.5
        ))
    
    def _calculate_swimlane_label_position(self, label_position: str, x: float, width: float,
                                          row_y: float, first_row_0based: int, last_row_0based: int,
                                          row_height: float) -> dict:
        """Calculate label position and attributes for a swimlane.
        
        Args:
            label_position: Position string ("Top Left", "Top Right", "Bottom Left", "Bottom Right")
            x: X position of timeline
            width: Width of timeline
            row_y: Y position of row frame
            first_row_0based: First row index (0-based)
            last_row_0based: Last row index (0-based)
            row_height: Height of a row
            
        Returns:
            Dictionary with label_x, label_y, text_anchor, dominant_baseline
        """
        offset = 5  # Fixed 5px offset from edges
        
        # Determine if label is top or bottom
        is_top = label_position.startswith("Top")
        is_bottom = label_position.startswith("Bottom")
        
        # Calculate Y position based on top/bottom
        if is_bottom:
            # Bottom labels: align with the last row of the swimlane
            row_top = row_y + last_row_0based * row_height
            vertical_factor = self.config.general.swimlane_bottom_vertical_alignment_factor
        elif is_top:
            # Top labels: align with the first row of the swimlane
            row_top = row_y + first_row_0based * row_height
            vertical_factor = self.config.general.swimlane_top_vertical_alignment_factor
        else:
            # Default to bottom positioning
            row_top = row_y + last_row_0based * row_height
            vertical_factor = self.config.general.swimlane_bottom_vertical_alignment_factor
        
        label_y = row_top + row_height * vertical_factor
        
        # Determine X position and text attributes based on left/right
        if label_position.endswith("Right"):
            label_x = x + width - offset
            text_anchor = "end"
        elif label_position.endswith("Left"):
            label_x = x + offset
            text_anchor = "start"
        else:
            # Default to right if invalid
            label_x = x + width - offset
            text_anchor = "end"
        
        return {
            "label_x": label_x,
            "label_y": label_y,
            "text_anchor": text_anchor,
            "dominant_baseline": "middle"
        }
    
    def _render_swimlane_label(self, title: str, label_x: float, label_y: float,
                               text_anchor: str, dominant_baseline: str):
        """Render a swimlane label text element.
        
        Args:
            title: Label text
            label_x, label_y: Position coordinates
            text_anchor: Text anchor ("start", "end", "middle")
            dominant_baseline: Baseline alignment
        """
        text_element = self.dwg.text(
            title,
            insert=(label_x, label_y),
            fill="grey",
            font_size=str(self.config.general.swimlane_font_size) + "px",
            font_family=f"{self.config.general.font_family}, sans-serif",
            text_anchor=text_anchor,
            dominant_baseline=dominant_baseline
        )
        self.dwg.add(text_element)

    def render_swimlanes(self, x, row_y, width, row_frame_height, num_rows):
        """Render swimlanes (horizontal dividers and labels).
        
        Args:
            x: The absolute x position of the timeline (in pixels)
            row_y: The absolute y position of the row frame (in pixels)
            width: The width of the timeline (in pixels)
            row_frame_height: The height of the row frame (in pixels)
            num_rows: The number of rows in the chart
        """
        # Extract swimlanes
        swimlanes = self._extract_swimlanes()
        if not swimlanes:
            return
        
        # Calculate row height
        row_height = row_frame_height / num_rows if num_rows > 0 else row_frame_height
        
        # Calculate first/last rows from table order (swimlanes stack vertically)
        current_first_row = 1  # 1-based
        
        # Render dividers and labels for each swimlane (order matters!)
        for swimlane in swimlanes:
            # Calculate row positions
            first_row, last_row, is_valid = self._calculate_swimlane_row_positions(
                swimlane, current_first_row, num_rows
            )
            
            if not is_valid:
                # Skip invalid swimlanes, but continue to next
                current_first_row += swimlane.row_count
                continue
            
            # Convert to 0-based for calculations
            first_row_0based = first_row - 1
            last_row_0based = last_row - 1
            
            # Render divider at the bottom of the swimlane (except if it meets the row frame bottom border)
            if last_row < num_rows:
                divider_y = row_y + last_row * row_height
                self._render_swimlane_divider(x, width, divider_y)
            
            # Render label if title exists
            if swimlane.title:
                label_position = swimlane.label_position if hasattr(swimlane, 'label_position') else "Bottom Right"
                label_info = self._calculate_swimlane_label_position(
                    label_position, x, width, row_y, first_row_0based, last_row_0based, row_height
                )
                self._render_swimlane_label(
                    swimlane.title,
                    label_info["label_x"],
                    label_info["label_y"],
                    label_info["text_anchor"],
                    label_info["dominant_baseline"]
                )
            
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
            curtain = self._convert_to_model_object(curtain_data, Curtain)
            
            # Validate dates
            if not is_valid_internal_date(curtain.start_date) or not is_valid_internal_date(curtain.end_date):
                continue
            
            curtain_start = self._parse_internal_date(curtain.start_date)
            curtain_end = self._parse_internal_date(curtain.end_date)
            if not curtain_start or not curtain_end:
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

    def _build_task_map(self) -> dict:
        """Build a task map for quick lookup using task_id as key.
        
        Returns:
            Dictionary mapping task_id to task data (dict or object)
        """
        task_map = {}
        tasks_data = self.data.get("tasks", [])
        for task_item in tasks_data:
            if isinstance(task_item, dict):
                task_id = task_item.get("task_id")
            else:
                task_id = getattr(task_item, "task_id", None)
            if task_id:
                task_map[task_id] = task_item
        return task_map
    
    def _extract_and_validate_links(self, task_map: dict) -> list:
        """Extract links from data and validate them using task_map.
        
        Args:
            task_map: Dictionary mapping task_id to task data
            
        Returns:
            List of validated Link objects
        """
        links = []
        links_data = self.data.get("links", [])
        
        for link_item in links_data:
            link = self._convert_to_model_object(link_item, Link)
            # Calculate valid status using key-based lookups
            from_task_dict = task_map.get(link.from_task_id)
            to_task_dict = task_map.get(link.to_task_id)
            
            if from_task_dict and to_task_dict:
                # Extract dates using key-based lookups
                if isinstance(from_task_dict, dict):
                    from_finish_date = from_task_dict.get("finish_date") or from_task_dict.get("start_date")
                else:
                    from_finish_date = getattr(from_task_dict, "finish_date", None) or getattr(from_task_dict, "start_date", None)
                
                if isinstance(to_task_dict, dict):
                    to_start_date = to_task_dict.get("start_date") or to_task_dict.get("finish_date")
                else:
                    to_start_date = getattr(to_task_dict, "start_date", None) or getattr(to_task_dict, "finish_date", None)
                
                if from_finish_date and to_start_date:
                    from_finish = self._parse_internal_date(from_finish_date)
                    to_start = self._parse_internal_date(to_start_date)
                    if from_finish and to_start:
                        link.valid = "No" if to_start < from_finish else "Yes"
                    else:
                        link.valid = "No"
                else:
                    link.valid = "No"
            else:
                link.valid = "No"
            
            links.append(link)
            # Skip legacy list format
        
        return links
    
    def _get_link_style_properties(self, link) -> dict:
        """Extract style properties from link.
        
        Args:
            link: Link object
            
        Returns:
            Dictionary with line_color, line_style, link_routing, stroke_dasharray
        """
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
        
        return {
            "line_color": line_color,
            "line_style": line_style,
            "link_routing": link_routing,
            "stroke_dasharray": stroke_dasharray
        }
    
    def _calculate_milestone_connection_point(self, center_x: float, center_y: float, 
                                             milestone_radius: float, link_routing: str,
                                             same_row: bool, successor_below: bool, 
                                             successor_above: bool, link_goes_right: bool,
                                             is_origin: bool) -> tuple:
        """Calculate connection point on milestone circle circumference.
        
        Args:
            center_x, center_y: Center of milestone circle
            milestone_radius: Radius of milestone circle
            link_routing: Routing type ("auto", "HV", "VH")
            same_row: Whether tasks are on same row
            successor_below: Whether successor is below predecessor
            successor_above: Whether successor is above predecessor
            link_goes_right: Whether link goes rightward
            is_origin: True for origin point, False for termination point
            
        Returns:
            Tuple of (x, y) connection point
        """
        if link_routing == "HV":
            if is_origin:
                # HV routing: always use right side midpoint for origin (horizontal first)
                return (center_x + milestone_radius, center_y)
            else:
                # HV routing: use top/bottom/left based on approach direction
                if same_row and link_goes_right:
                    # Horizontal approach - use left side
                    return (center_x - milestone_radius, center_y)
                elif successor_below:
                    # Vertical approach from above - use top
                    return (center_x, center_y - milestone_radius)
                elif successor_above:
                    # Vertical approach from below - use bottom
                    return (center_x, center_y + milestone_radius)
                else:
                    return (center_x, center_y)
        elif link_routing == "VH":
            if is_origin:
                # VH routing: use top/bottom based on successor position (vertical first)
                if successor_below:
                    return (center_x, center_y + milestone_radius)
                elif successor_above:
                    return (center_x, center_y - milestone_radius)
                else:
                    # Same row - use right side (fallback)
                    return (center_x + milestone_radius, center_y)
            else:
                # VH routing: use left side for horizontal approach, top/bottom for vertical
                if same_row or link_goes_right:
                    # Horizontal approach - use left side
                    return (center_x - milestone_radius, center_y)
                elif successor_below:
                    # Vertical approach from above - use top
                    return (center_x, center_y - milestone_radius)
                elif successor_above:
                    # Vertical approach from below - use bottom
                    return (center_x, center_y + milestone_radius)
                else:
                    return (center_x, center_y)
        else:
            # Auto routing
            if is_origin:
                if same_row and link_goes_right:
                    # Link goes rightward - use rightmost point
                    return (center_x + milestone_radius, center_y)
                elif successor_below:
                    # Link goes downward - use bottommost point
                    return (center_x, center_y + milestone_radius)
                elif successor_above:
                    # Link goes upward - use topmost point
                    return (center_x, center_y - milestone_radius)
                else:
                    return (center_x, center_y)
            else:
                if same_row and link_goes_right:
                    # Link approaches from left - use leftmost point
                    return (center_x - milestone_radius, center_y)
                elif successor_below:
                    # Link approaches from above - use topmost point
                    return (center_x, center_y - milestone_radius)
                elif successor_above:
                    # Link approaches from below - use bottommost point
                    return (center_x, center_y + milestone_radius)
                else:
                    return (center_x, center_y)
    
    def _calculate_connection_points(self, from_task: dict, to_task: dict, 
                                    link_routing: str, row_height: float) -> dict:
        """Calculate origin and termination connection points for a link.
        
        Args:
            from_task: Position dictionary for source task
            to_task: Position dictionary for target task
            link_routing: Routing type ("auto", "HV", "VH")
            row_height: Height of a row
            
        Returns:
            Dictionary with origin_x, origin_y, term_x, term_y, same_row, same_date,
            successor_below, successor_above, link_goes_right, from_is_milestone, to_is_milestone
        """
        from_is_milestone = from_task.get("is_milestone", False)
        to_is_milestone = to_task.get("is_milestone", False)
        
        # Calculate milestone half_size
        task_height = row_height * 0.8
        milestone_half_size = task_height / 2
        
        # Determine preliminary positions to calculate link direction
        if from_is_milestone:
            from_center_x = (from_task["x_start"] + from_task["x_end"]) / 2
        else:
            from_center_x = from_task["x_end"]
        
        if to_is_milestone:
            to_center_x = (to_task["x_start"] + to_task["x_end"]) / 2
        else:
            to_center_x = to_task["x_start"]
        
        # Determine routing info
        same_row = from_task["row_num"] == to_task["row_num"]
        successor_below = to_task["row_num"] > from_task["row_num"]
        successor_above = to_task["row_num"] < from_task["row_num"]
        link_goes_right = to_center_x > from_center_x
        
        # Calculate origin point
        if from_is_milestone:
            from_center_x = (from_task["x_start"] + from_task["x_end"]) / 2
            from_center_y = from_task["y_center"]
            origin_x, origin_y = self._calculate_milestone_connection_point(
                from_center_x, from_center_y, milestone_half_size, link_routing,
                same_row, successor_below, successor_above, link_goes_right, True
            )
        else:
            # Regular task: use right edge
            origin_x = from_task["x_end"]
            origin_y = from_task["y_center"]
        
        # Calculate termination point
        if to_is_milestone:
            to_center_x = (to_task["x_start"] + to_task["x_end"]) / 2
            to_center_y = to_task["y_center"]
            term_x, term_y = self._calculate_milestone_connection_point(
                to_center_x, to_center_y, milestone_half_size, link_routing,
                same_row, successor_below, successor_above, link_goes_right, False
            )
        else:
            # Regular task: use left edge
            term_x = to_task["x_start"]
            term_y = to_task["y_center"]
        
        return {
            "origin_x": origin_x,
            "origin_y": origin_y,
            "term_x": term_x,
            "term_y": term_y,
            "same_row": same_row,
            "successor_below": successor_below,
            "successor_above": successor_above,
            "link_goes_right": link_goes_right,
            "from_is_milestone": from_is_milestone,
            "to_is_milestone": to_is_milestone
        }
    
    def _get_task_date_strings(self, from_task_id: int, to_task_id: int) -> dict:
        """Get finish/start date strings for link validation.
        
        Args:
            from_task_id: Source task ID
            to_task_id: Target task ID
            
        Returns:
            Dictionary with from_finish_date_str, to_start_date_str
        """
        from_task_data = None
        to_task_data = None
        for task in self.data.get("tasks", []):
            task_id = task.get("task_id")
            if task_id == from_task_id:
                from_task_data = task
            if task_id == to_task_id:
                to_task_data = task
        
        from_finish_date_str = from_task_data.get("finish_date", "") if from_task_data else ""
        to_start_date_str = to_task_data.get("start_date", "") if to_task_data else ""
        
        return {
            "from_finish_date_str": from_finish_date_str,
            "to_start_date_str": to_start_date_str,
            "from_task_data": from_task_data,
            "to_task_data": to_task_data
        }
    
    def _should_suppress_same_row_link(self, from_finish_date_str: str, to_start_date_str: str,
                                       from_is_milestone: bool, to_is_milestone: bool) -> bool:
        """Determine if same-row link should be suppressed due to small gap.
        
        Args:
            from_finish_date_str: Finish date string of source task
            to_start_date_str: Start date string of target task
            from_is_milestone: Whether source is milestone
            to_is_milestone: Whether target is milestone
            
        Returns:
            True if link should be suppressed, False otherwise
        """
        gap_days = 0
        if from_finish_date_str and to_start_date_str:
            from_finish_date = self._parse_internal_date(from_finish_date_str)
            to_start_date = self._parse_internal_date(to_start_date_str)
            if from_finish_date and to_start_date:
                gap_days = (to_start_date - from_finish_date).days
        
        # Determine suppression threshold based on task/milestone types
        if from_is_milestone and to_is_milestone:
            # Milestone to Milestone: suppress if gap < 6 days (≤ 5 days)
            return gap_days < 6
        elif from_is_milestone or to_is_milestone:
            # Task to Milestone or Milestone to Task: suppress if gap < 4 days (≤ 3 days)
            return gap_days < 4
        else:
            # Task to Task: suppress if gap ≤ 3 days
            return gap_days <= 3
    
    def _create_link_line(self, start: tuple, end: tuple, line_color: str, 
                         stroke_dasharray: str) -> object:
        """Create a styled line element for a link.
        
        Args:
            start: Start point (x, y)
            end: End point (x, y)
            line_color: Line color
            stroke_dasharray: SVG stroke-dasharray value (None for solid)
            
        Returns:
            SVG line element
        """
        line_attrs = {
            "stroke": line_color,
            "stroke_width": 1.5,
            "stroke_linecap": "round"
        }
        if stroke_dasharray:
            line_attrs["stroke_dasharray"] = stroke_dasharray
        return self.dwg.line(start, end, **line_attrs)
    
    def _add_origin_marker(self, origin_x: float, origin_y: float, line_color: str):
        """Add a small circle marker at the link origin point.
        
        Args:
            origin_x, origin_y: Origin point coordinates
            line_color: Color for marker
        """
        origin_circle = self.dwg.circle(
            center=(origin_x, origin_y),
            r=1.5,  # 1.5 pixel radius (3 pixel diameter)
            fill=line_color,
            stroke=line_color,
            stroke_width=1
        )
        self.dwg.add(origin_circle)
    
    def _render_same_row_link(self, origin_x: float, origin_y: float, term_x: float, term_y: float,
                              from_finish_date_str: str, to_start_date_str: str,
                              from_is_milestone: bool, to_is_milestone: bool,
                              line_color: str, stroke_dasharray: str) -> bool:
        """Render link for same-row scenario.
        
        Args:
            origin_x, origin_y: Origin point coordinates
            term_x, term_y: Termination point coordinates
            from_finish_date_str: Finish date string of source task
            to_start_date_str: Start date string of target task
            from_is_milestone: Whether source is milestone
            to_is_milestone: Whether target is milestone
            line_color: Line color
            stroke_dasharray: SVG stroke-dasharray value
            
        Returns:
            True if link was rendered, False if suppressed or skipped
        """
        # Check if same date
        same_date = False
        if from_finish_date_str and to_start_date_str:
            from_finish_date = self._parse_internal_date(from_finish_date_str)
            to_start_date = self._parse_internal_date(to_start_date_str)
            if from_finish_date and to_start_date:
                same_date = from_finish_date == to_start_date
            else:
                same_date = abs(origin_x - term_x) < 1.0
        else:
            same_date = abs(origin_x - term_x) < 1.0
        
        if same_date:
            # No Gap (Bars Touch) - Skip rendering
            return False
        
        # Check if should suppress due to small gap
        if self._should_suppress_same_row_link(from_finish_date_str, to_start_date_str,
                                               from_is_milestone, to_is_milestone):
            return False
        
        # Render link for elements with sufficient gap
        arrow_size = 5
        line_end_x = term_x - arrow_size  # Arrow points left, base is to the right
        self.dwg.add(self._create_link_line((origin_x, origin_y), (line_end_x, term_y),
                                            line_color, stroke_dasharray))
        self._render_arrowhead(term_x, term_y, "left", arrow_size, line_color)
        self._add_origin_marker(origin_x, origin_y, line_color)
        return True
    
    def _render_different_rows_link(self, origin_x: float, origin_y: float, 
                                   term_x: float, term_y: float,
                                   from_finish_date_str: str, to_start_date_str: str,
                                   same_row: bool, successor_below: bool,
                                   link_routing: str, link_goes_right: bool,
                                   from_task_row: int, to_task_row: int,
                                   line_color: str, stroke_dasharray: str) -> bool:
        """Render link for different-rows scenario.
        
        Args:
            origin_x, origin_y: Origin point coordinates
            term_x, term_y: Termination point coordinates
            from_finish_date_str: Finish date string of source task
            to_start_date_str: Start date string of target task
            same_row: Whether tasks are on same row (should be False)
            successor_below: Whether successor is below predecessor
            link_routing: Routing type ("auto", "HV", "VH")
            link_goes_right: Whether link goes rightward
            from_task_row: Row number of source task
            to_task_row: Row number of target task
            line_color: Line color
            stroke_dasharray: SVG stroke-dasharray value
            
        Returns:
            True if link was rendered, False if skipped
        """
        # Check if same date
        same_date = False
        if from_finish_date_str and to_start_date_str:
            from_finish_date = self._parse_internal_date(from_finish_date_str)
            to_start_date = self._parse_internal_date(to_start_date_str)
            if from_finish_date and to_start_date:
                same_date = from_finish_date == to_start_date
            else:
                same_date = abs(origin_x - term_x) < 1.0
        else:
            same_date = abs(origin_x - term_x) < 1.0
        
        arrow_size = 5
        
        if same_date:
            # No Gap (Aligned Vertically)
            if abs(origin_x - term_x) < 2.0:
                # Perfect alignment - single vertical segment
                if to_task_row > from_task_row:
                    # Successor below - downward arrow
                    line_end_y = term_y - arrow_size
                    self.dwg.add(self._create_link_line((origin_x, origin_y), (term_x, line_end_y),
                                                        line_color, stroke_dasharray))
                    self._render_arrowhead(term_x, term_y, "down", arrow_size, line_color)
                else:
                    # Successor above - upward arrow
                    line_end_y = term_y + arrow_size
                    self.dwg.add(self._create_link_line((origin_x, origin_y), (term_x, line_end_y),
                                                        line_color, stroke_dasharray))
                    self._render_arrowhead(term_x, term_y, "up", arrow_size, line_color)
                self._add_origin_marker(origin_x, origin_y, line_color)
                return True
            else:
                # Not perfectly aligned - use routing pattern
                return self._render_routed_link(origin_x, origin_y, term_x, term_y,
                                               successor_below, link_routing, link_goes_right,
                                               to_task_row, from_task_row,
                                               arrow_size, line_color, stroke_dasharray)
        else:
            # Positive Gap/Lag - use routing pattern
            return self._render_routed_link(origin_x, origin_y, term_x, term_y,
                                           successor_below, link_routing, link_goes_right,
                                           to_task_row, from_task_row,
                                           arrow_size, line_color, stroke_dasharray)
    
    def _render_routed_link(self, origin_x: float, origin_y: float, term_x: float, term_y: float,
                           successor_below: bool, link_routing: str, link_goes_right: bool,
                           to_task_row: int, from_task_row: int,
                           arrow_size: float, line_color: str, stroke_dasharray: str) -> bool:
        """Render link using specified routing pattern.
        
        Args:
            origin_x, origin_y: Origin point coordinates
            term_x, term_y: Termination point coordinates
            successor_below: Whether successor is below predecessor
            link_routing: Routing type ("auto", "HV", "VH")
            link_goes_right: Whether link goes rightward
            to_task_row: Row number of target task
            from_task_row: Row number of source task
            arrow_size: Size of arrowhead
            line_color: Line color
            stroke_dasharray: SVG stroke-dasharray value
            
        Returns:
            True if link was rendered
        """
        if link_routing == "HV":
            # Horizontal-Vertical: Go horizontal first, then vertical
            if to_task_row > from_task_row:
                # Successor below - H-V downward
                line_end_y = term_y - arrow_size
                self.dwg.add(self._create_link_line((origin_x, origin_y), (term_x, origin_y),
                                                    line_color, stroke_dasharray))
                self.dwg.add(self._create_link_line((term_x, origin_y), (term_x, line_end_y),
                                                    line_color, stroke_dasharray))
                self._render_arrowhead(term_x, term_y, "down", arrow_size, line_color)
            else:
                # Successor above - H-V upward
                line_end_y = term_y + arrow_size
                self.dwg.add(self._create_link_line((origin_x, origin_y), (term_x, origin_y),
                                                    line_color, stroke_dasharray))
                self.dwg.add(self._create_link_line((term_x, origin_y), (term_x, line_end_y),
                                                    line_color, stroke_dasharray))
                self._render_arrowhead(term_x, term_y, "up", arrow_size, line_color)
            self._add_origin_marker(origin_x, origin_y, line_color)
        elif link_routing == "VH":
            # Vertical-Horizontal: Go vertical first, then horizontal
            if link_goes_right:
                # Link goes right - arrow points left (into task)
                line_end_x = term_x - arrow_size
                self.dwg.add(self._create_link_line((origin_x, origin_y), (origin_x, term_y),
                                                    line_color, stroke_dasharray))
                self.dwg.add(self._create_link_line((origin_x, term_y), (line_end_x, term_y),
                                                    line_color, stroke_dasharray))
                self._render_arrowhead(term_x, term_y, "left", arrow_size, line_color)
            else:
                # Link goes left (shouldn't happen in FS, but handle gracefully)
                line_end_x = term_x + arrow_size
                self.dwg.add(self._create_link_line((origin_x, origin_y), (origin_x, term_y),
                                                    line_color, stroke_dasharray))
                self.dwg.add(self._create_link_line((origin_x, term_y), (line_end_x, term_y),
                                                    line_color, stroke_dasharray))
                self._render_arrowhead(term_x, term_y, "right", arrow_size, line_color)
            self._add_origin_marker(origin_x, origin_y, line_color)
        else:
            # Auto: Use V-H-V pattern (default behavior)
            mid_y = (origin_y + term_y) / 2
            
            if to_task_row > from_task_row:
                # Successor below - V-H-V downward
                line_end_y = term_y - arrow_size
                self.dwg.add(self._create_link_line((origin_x, origin_y), (origin_x, mid_y),
                                                    line_color, stroke_dasharray))
                self.dwg.add(self._create_link_line((origin_x, mid_y), (term_x, mid_y),
                                                    line_color, stroke_dasharray))
                self.dwg.add(self._create_link_line((term_x, mid_y), (term_x, line_end_y),
                                                    line_color, stroke_dasharray))
                self._render_arrowhead(term_x, term_y, "down", arrow_size, line_color)
            else:
                # Successor above - V-H-V upward
                line_end_y = term_y + arrow_size
                self.dwg.add(self._create_link_line((origin_x, origin_y), (origin_x, mid_y),
                                                    line_color, stroke_dasharray))
                self.dwg.add(self._create_link_line((origin_x, mid_y), (term_x, mid_y),
                                                    line_color, stroke_dasharray))
                self.dwg.add(self._create_link_line((term_x, mid_y), (term_x, line_end_y),
                                                    line_color, stroke_dasharray))
                self._render_arrowhead(term_x, term_y, "up", arrow_size, line_color)
            self._add_origin_marker(origin_x, origin_y, line_color)
        
        return True

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
        
        # Build task map and extract/validate links using key-based lookups
        task_map = self._build_task_map()
        links = self._extract_and_validate_links(task_map)
        
        # Calculate row height for vertical positioning
        row_height = row_frame_height / num_rows if num_rows > 0 else row_frame_height
        
        for link in links:
            # Skip invalid links
            if link.valid != "Yes":
                continue
            
            # Get style properties
            style_props = self._get_link_style_properties(link)
            line_color = style_props["line_color"]
            stroke_dasharray = style_props["stroke_dasharray"]
            link_routing = style_props["link_routing"]
            
            # Get task positions
            from_task = self._get_task_position(link.from_task_id, x, row_y, width, row_frame_height, start_date, end_date, num_rows)
            to_task = self._get_task_position(link.to_task_id, x, row_y, width, row_frame_height, start_date, end_date, num_rows)
            
            if not from_task or not to_task:
                continue  # Skip if either task not found
            
            # Get task date strings for validation
            date_info = self._get_task_date_strings(link.from_task_id, link.to_task_id)
            from_finish_date_str = date_info["from_finish_date_str"]
            to_start_date_str = date_info["to_start_date_str"]
            
            if not date_info["from_task_data"] or not date_info["to_task_data"]:
                continue
            
            # Calculate connection points
            connection_info = self._calculate_connection_points(
                from_task, to_task, link_routing, row_height
            )
            
            # Render link based on same row or different rows
            if connection_info["same_row"]:
                self._render_same_row_link(
                    connection_info["origin_x"], connection_info["origin_y"],
                    connection_info["term_x"], connection_info["term_y"],
                    from_finish_date_str, to_start_date_str,
                    connection_info["from_is_milestone"], connection_info["to_is_milestone"],
                    line_color, stroke_dasharray
                )
            else:
                self._render_different_rows_link(
                    connection_info["origin_x"], connection_info["origin_y"],
                    connection_info["term_x"], connection_info["term_y"],
                    from_finish_date_str, to_start_date_str,
                    connection_info["same_row"], connection_info["successor_below"],
                    link_routing, connection_info["link_goes_right"],
                    from_task["row_num"], to_task["row_num"],
                    line_color, stroke_dasharray
                )

    def _build_scale_configs(self) -> list:
        """Build list of visible scale configurations.
        
        Returns:
            List of tuples (interval, proportion) for visible scales
        """
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
        return [(interval, proportion) for interval, proportion, visible in all_scale_configs if visible]
    
    def _calculate_scale_heights(self, scale_configs: list, height: float) -> tuple:
        """Calculate heights for scales and row frame.
        
        Args:
            scale_configs: List of (interval, proportion) tuples
            height: Total available height
            
        Returns:
            Tuple of (row_frame_height, scale_heights_list)
        """
        row_frame_proportion = 1.0
        total_scale_proportion = sum(p for _, p in scale_configs)
        total_height_units = row_frame_proportion + total_scale_proportion
        row_frame_height = height * (row_frame_proportion / total_height_units)
        scale_heights = [(interval, height * (proportion / total_height_units)) for interval, proportion in scale_configs]
        return (row_frame_height, scale_heights)
    
    def _render_scale_backgrounds(self, x: float, start_y: float, width: float, 
                                  scale_heights: list, start_date: datetime, end_date: datetime,
                                  time_scale: float) -> float:
        """Render scale backgrounds and return the y position after all scales.
        
        Args:
            x: X position
            start_y: Starting Y position
            width: Width of scales
            scale_heights: List of (interval, height) tuples
            start_date: Timeline start date
            end_date: Timeline end date
            time_scale: Pixels per day
            
        Returns:
            Y position after all scales (where row frame starts)
        """
        current_y = start_y
        for interval, scale_height in scale_heights:
            self.dwg.add(self.dwg.rect(insert=(x, current_y), size=(width, scale_height),
                                       fill="lightgrey", 
                                       stroke=self.config.general.frame_border_color, 
                                       stroke_width=self.config.general.frame_border_width_light))
            self.render_scale_interval(x, current_y, width, scale_height, start_date, end_date, interval, time_scale)
            current_y += scale_height
        return current_y
    
    def _render_row_frame_borders(self, x: float, row_y: float, width: float, 
                                  row_frame_height: float, scale_configs: list):
        """Render row frame borders (left, right, and conditional top/bottom).
        
        Args:
            x: X position
            row_y: Y position of row frame
            width: Width of row frame
            row_frame_height: Height of row frame
            scale_configs: List of scale configs (to check if scales exist)
        """
        # Render left and right borders
        self.dwg.add(self.dwg.line((x, row_y), (x, row_y + row_frame_height),
                                   stroke=self.config.general.frame_border_color,
                                   stroke_width=self.config.general.frame_border_width_light))
        self.dwg.add(self.dwg.line((x + width, row_y), (x + width, row_y + row_frame_height),
                                   stroke=self.config.general.frame_border_color,
                                   stroke_width=self.config.general.frame_border_width_light))
        
        # Conditionally add top border if header is 0 and no scales are shown
        header_height = self._get_frame_config("header_height", 20)
        if header_height <= 0 and len(scale_configs) == 0:
            self.dwg.add(self.dwg.line((x, row_y), (x + width, row_y),
                                       stroke=self.config.general.frame_border_color,
                                       stroke_width=self.config.general.frame_border_width_light))
        
        # Conditionally add bottom border if footer is 0
        footer_height = self._get_frame_config("footer_height", 20)
        if footer_height <= 0:
            self.dwg.add(self.dwg.line((x, row_y + row_frame_height), (x + width, row_y + row_frame_height),
                                       stroke=self.config.general.frame_border_color,
                                       stroke_width=self.config.general.frame_border_width_light))
    
    def _render_horizontal_gridlines(self, x: float, row_y: float, width: float,
                                    row_frame_height: float, num_rows: int):
        """Render horizontal gridlines between rows.
        
        Args:
            x: X position
            row_y: Y position of row frame
            width: Width of gridlines
            row_frame_height: Height of row frame
            num_rows: Number of rows
        """
        if not self._get_frame_config("horizontal_gridlines", False):
            return
        
        for i in range(1, num_rows):  # Exclude first and last to avoid overlapping row frame border
            y_pos = row_y + i * (row_frame_height / num_rows)
            self.dwg.add(self.dwg.line((x, y_pos), (x + width, y_pos), stroke="lightgrey", stroke_width=0.5))
    
    def _render_row_numbers(self, x: float, row_y: float, row_frame_height: float, num_rows: int):
        """Render row numbers if enabled.
        
        Args:
            x: X position
            row_y: Y position of row frame
            row_frame_height: Height of row frame
            num_rows: Number of rows
        """
        if not self._get_frame_config("show_row_numbers", False):
            return
        
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
    
    def _get_vertical_gridline_intervals(self) -> list:
        """Get list of intervals that should have vertical gridlines.
        
        Returns:
            List of interval strings ("years", "months", "weeks", "days")
        """
        intervals = []
        if self._get_frame_config("vertical_gridline_years", False):
            intervals.append("years")
        if self._get_frame_config("vertical_gridline_months", False):
            intervals.append("months")
        if self._get_frame_config("vertical_gridline_weeks", False):
            intervals.append("weeks")
        if self._get_frame_config("vertical_gridline_days", False):
            intervals.append("days")
        return intervals
    
    def _render_vertical_gridlines(self, x: float, row_y: float, width: float,
                                   row_frame_height: float, start_date: datetime, end_date: datetime,
                                   time_scale: float):
        """Render vertical gridlines for enabled intervals.
        
        Args:
            x: X position
            row_y: Y position of row frame
            width: Width of timeline
            row_frame_height: Height of row frame
            start_date: Timeline start date
            end_date: Timeline end date
            time_scale: Pixels per day
        """
        # Define line weights for visual hierarchy: larger intervals = thicker lines
        interval_line_weights = {
            "years": 3.0,
            "months": 2.0,
            "weeks": 1.5,
            "days": 1.0
        }
        
        vertical_gridline_intervals = self._get_vertical_gridline_intervals()
        
        # Render gridlines for each enabled interval
        for interval in vertical_gridline_intervals:
            line_weight = interval_line_weights.get(interval, 1.0)
            current_date = self.next_period(start_date, interval)
            prev_x = x
            while current_date <= end_date:
                x_pos = x + (current_date - start_date).days * time_scale
                if x <= x_pos <= x + width:
                    self.dwg.add(self.dwg.line((x_pos, row_y), (x_pos, row_y + row_frame_height),
                                               stroke="lightgrey", stroke_width=line_weight))
                prev_x = x_pos
                current_date = self.next_period(current_date, interval)

    def render_scales_and_rows(self, x, y, width, height, start_date, end_date):
        """Render time scales, row frame, gridlines, and row numbers.
        
        Also renders swimlanes, pipes, curtains, and tasks.
        
        Args:
            x: X position
            y: Y position
            width: Width
            height: Height
            start_date: Timeline start date
            end_date: Timeline end date
            
        Returns:
            Tuple of (row_y, row_frame_height)
        """
        # Calculate time scale
        total_days = max((end_date - start_date).days, 1)
        time_scale = width / total_days if total_days > 0 else width

        # Build scale configurations
        scale_configs = self._build_scale_configs()
        
        # Calculate heights
        row_frame_height, scale_heights = self._calculate_scale_heights(scale_configs, height)
        
        # Render scale backgrounds
        row_y = self._render_scale_backgrounds(x, y, width, scale_heights, start_date, end_date, time_scale)
        
        # Get number of rows
        num_rows = self._get_frame_config("num_rows", 1)
        
        # Render row frame borders
        self._render_row_frame_borders(x, row_y, width, row_frame_height, scale_configs)
        
        # Render horizontal gridlines
        self._render_horizontal_gridlines(x, row_y, width, row_frame_height, num_rows)
        
        # Render row numbers
        self._render_row_numbers(x, row_y, row_frame_height, num_rows)
        
        # Render vertical gridlines
        self._render_vertical_gridlines(x, row_y, width, row_frame_height, start_date, end_date, time_scale)

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
        
        # Create font for notes
        note_font = QFont(self.config.general.font_family, self.config.general.note_font_size)
        note_font_metrics = QFontMetrics(note_font)
        line_height = note_font_metrics.height()
        
        for note_data in notes:
            # Convert dict to Note object if needed
            note = self._convert_to_model_object(note_data, Note)
            
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
            # Font metrics correction: Qt and SVG font rendering scale proportionately with font size,
            # so a fixed factor (1.2) works across all font sizes. This accounts for the consistent
            # difference between Qt's QFontMetrics measurement and SVG's actual text rendering.
            font_metrics_correction = 1.2  # Adjust if SVG renders more compactly than Qt measures
            available_width = max(1, (note.width - (2 * padding)) * font_metrics_correction)
            text_lines = self._wrap_text_to_lines(note.text, available_width, font_size=self.config.general.note_font_size)
            
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
        os.makedirs(self.output_folder, exist_ok=True)
        # Create overlay group for ID badges (rendered last to appear on top)
        self.id_badge_overlay = self.dwg.g()
        self.render_outer_frame()  # Background only
        self.render_header()
        self.render_footer()
        self.render_inner_frame()
        self.render_single_timeline()
        self.render_notes()  # Render notes after all other elements
        # Add ID badge overlay last (before border) so badges float above all other artifacts
        self.dwg.add(self.id_badge_overlay)
        self.render_outer_frame_border()  # Border rendered last
        self.dwg.save()