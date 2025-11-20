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
        self._rendered_inside_labels = set()  # Track tasks that have had inside labels rendered
        self._time_frame_info = []  # Store time frame positions and date ranges for span calculation
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

    def _parse_date_safe(self, date_str: str) -> datetime:
        """Safely parse a date string, returning None if invalid."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            return None

    def _calculate_time_range(self):
        logging.debug("Calculating time range")
        dates = []
        for task in self.data.get("tasks", []):
            for date_str in [task.get("start_date", ""), task.get("finish_date", "")]:
                parsed_date = self._parse_date_safe(date_str)
                if parsed_date:
                    dates.append(parsed_date)

        if not dates:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return today, today + timedelta(days=30)
        return min(dates), max(dates) + timedelta(days=1)

    def _set_time_scale(self):
        start_date, _ = self._calculate_time_range()
        logging.debug(f"Time scale set with start_date: {start_date}")
        return start_date

    def render_outer_frame(self):
        width = self._get_frame_config("outer_width", self.config.general.outer_width)
        height = self._get_frame_config("outer_height", self.config.general.outer_height)
        self.dwg.add(self.dwg.rect(insert=(0, 0), size=(width, height), fill="white", stroke="black", stroke_width=2))
        logging.debug("Outer frame rendered")

    def render_header(self):
        margins = self._get_frame_config("margins", (10, 10, 10, 10))
        width = self._get_frame_config("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        height = self._get_frame_config("header_height", 50)
        self.dwg.add(self.dwg.rect(insert=(margins[3], margins[0]), size=(width, height),
                                   fill="lightgray", stroke="black", stroke_width=1))
        header_text = self._get_frame_config("header_text", "")
        if header_text:
            self.dwg.add(self.dwg.text(header_text,
                                       insert=(margins[3] + width / 2, margins[0] + height / 2),
                                       text_anchor="middle", font_size="14"))
        logging.debug("Header rendered")

    def render_footer(self):
        margins = self._get_frame_config("margins", (10, 10, 10, 10))
        width = self._get_frame_config("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        height = self._get_frame_config("footer_height", 50)
        y = self._get_frame_config("outer_height", self.config.general.outer_height) - margins[2] - height
        self.dwg.add(self.dwg.rect(insert=(margins[3], y), size=(width, height),
                                   fill="lightgray", stroke="black", stroke_width=1))
        footer_text = self._get_frame_config("footer_text", "")
        if footer_text:
            self.dwg.add(self.dwg.text(footer_text,
                                       insert=(margins[3] + width / 2, y + height / 2),
                                       text_anchor="middle", font_size="14"))
        logging.debug("Footer rendered")

    def render_inner_frame(self):
        margins = self._get_frame_config("margins", (10, 10, 10, 10))
        width = self._get_frame_config("outer_width", self.config.general.outer_width) - margins[1] - margins[3]
        header_height = self._get_frame_config("header_height", 50)
        footer_height = self._get_frame_config("footer_height", 50)
        y = margins[0] + header_height
        height = (self._get_frame_config("outer_height", self.config.general.outer_height) -
                  header_height - footer_height - margins[0] - margins[2])
        self.dwg.add(self.dwg.rect(insert=(margins[3], y), size=(width, height),
                                   fill="none", stroke="blue", stroke_width=1, stroke_dasharray="4"))
        logging.debug("Inner frame rendered")

    def render_time_frames(self):
        logging.debug("Starting render_time_frames")
        margins = self._get_frame_config("margins", (10, 10, 10, 10))
        header_height = self._get_frame_config("header_height", 50)
        footer_height = self._get_frame_config("footer_height", 50)
        outer_width = self._get_frame_config("outer_width", self.config.general.outer_width)
        outer_height = self._get_frame_config("outer_height", self.config.general.outer_height)
        inner_y = margins[0] + header_height
        inner_width = outer_width - margins[1] - margins[3]
        inner_height = outer_height - header_height - footer_height - margins[0] - margins[2]
        chart_start = datetime.strptime(self.data["frame_config"]["chart_start_date"], "%Y-%m-%d")

        # Sort time frames by finish_date to ensure chronological rendering
        time_frames = self.data.get("time_frames", [])
        sorted_time_frames = sorted(
            time_frames,
            key=lambda tf: datetime.strptime(tf["finish_date"], "%Y-%m-%d")
        )
        logging.debug(f"Sorted time frames by finish_date: {[tf['finish_date'] for tf in sorted_time_frames]}")

        # ========================================================================
        # PASS 1: Pre-calculate all time frame positions
        # ========================================================================
        # This pass calculates and stores the x position and date range for each time frame
        # BEFORE we start rendering. This is critical because:
        # - Tasks can span multiple time frames
        # - Inside labels need to be centered on the TOTAL task span across all time frames
        # - When render_tasks() is called, it needs access to ALL time frame info to calculate
        #   the total span correctly, not just the current time frame being rendered
        # Without this pre-calculation, labels would only center relative to the first time frame
        # segment, not the complete task length in pixels across all segments.
        # ========================================================================
        x_offset = margins[3]
        prev_end = chart_start
        
        for tf in sorted_time_frames:
            tf_width = inner_width * tf.get("width_proportion", 1.0)
            tf_end = datetime.strptime(tf["finish_date"], "%Y-%m-%d")
            
            # Store time frame info: absolute x position, width, and date range
            # This info will be used by _calculate_total_task_span() to compute
            # the total pixel span of tasks that cross multiple time frames
            self._time_frame_info.append({
                "x": x_offset,
                "width": tf_width,
                "start_date": prev_end,
                "end_date": tf_end
            })
            
            x_offset += tf_width
            prev_end = tf_end + timedelta(days=1)

        # ========================================================================
        # PASS 2: Render each time frame
        # ========================================================================
        # Now that all time frame positions are known, we can render each time frame.
        # When render_tasks() is called for a time frame, it can access the complete
        # _time_frame_info list to calculate total task spans for proper label centering.
        #
        # IMPORTANT: Inside labels for multi-time-frame tasks are rendered only in the
        # LAST time frame segment where the task appears. This ensures:
        # - All task bar segments are rendered first (so labels appear on top)
        # - Labels are centered correctly on the total task span
        # - Labels appear only once (not duplicated in each segment)
        # ========================================================================
        x_offset = margins[3]
        prev_end = chart_start
        
        for tf in sorted_time_frames:
            tf_width = inner_width * tf.get("width_proportion", 1.0)
            tf_end = datetime.strptime(tf["finish_date"], "%Y-%m-%d")
            
            # Draw the time frame border
            self.dwg.add(self.dwg.rect(insert=(x_offset, inner_y), size=(tf_width, inner_height),
                                       fill="none", stroke="red", stroke_width=1))
            
            # Render scales, rows, and tasks for this time frame
            # Note: render_tasks() will use the pre-calculated _time_frame_info to
            # center inside labels on the total task span across all time frames.
            # Labels are rendered only in the last time frame segment where each task appears.
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
                                   font_size="10", font_family="Arial", fill="white",
                                   text_anchor="middle"))
        logging.debug(f"  Text element added to SVG at position ({label_x}, {label_y_base})")

    def _calculate_total_task_span(self, task_start: datetime, task_finish: datetime) -> tuple:
        """Calculate the total task span across all time frames in absolute pixel coordinates.
        
        This method is used when a task spans multiple time frames and has an "Inside" label.
        It calculates where the task starts and ends in absolute pixel coordinates across
        all time frames, so the label can be centered on the complete task length.
        
        The calculation accounts for different time scales (pixels per day) in each time frame,
        ensuring accurate pixel positioning even when time frames have different widths or
        date ranges.
        
        Args:
            task_start: The task's start date (datetime object)
            task_finish: The task's finish date (datetime object)
            
        Returns:
            Tuple of (total_x_start, total_width) in absolute pixel coordinates, where:
            - total_x_start: The absolute x position where the task starts (leftmost point)
            - total_width: The total pixel width of the task across all time frames
            Returns None if the task doesn't overlap with any time frames.
            
        Note:
            This method relies on _time_frame_info being pre-populated by render_time_frames()
            in its first pass. Without complete time frame info, labels would only center
            relative to the first time frame segment, not the total task span.
            
            The calculation matches the exact logic used in render_tasks() for consistency,
            ensuring that label positions align perfectly with task bar segments.
        """
        total_x_start = None
        total_x_end = None
        
        logging.debug(f"_calculate_total_task_span called for task {task_start} to {task_finish}, time_frame_info count: {len(self._time_frame_info)}")
        
        # Iterate through all time frames to find where the task appears
        for idx, tf_info in enumerate(self._time_frame_info):
            tf_start = tf_info["start_date"]
            tf_end = tf_info["end_date"]
            tf_x = tf_info["x"]  # Absolute x position of this time frame
            tf_width = tf_info["width"]  # Width of this time frame in pixels
            
            # Skip time frames that don't overlap with the task
            if task_finish < tf_start or task_start > tf_end:
                logging.debug(f"  Time frame {idx}: {tf_start} to {tf_end} - no overlap (task: {task_start} to {task_finish})")
                continue
            
            logging.debug(f"  Time frame {idx}: {tf_start} to {tf_end} - OVERLAPS")
            
            # Calculate the task segment within this time frame
            # Each time frame may have a different time scale (pixels per day)
            tf_total_days = max((tf_end - tf_start).days, 1)
            tf_time_scale = tf_width / tf_total_days if tf_total_days > 0 else tf_width
            
            # Find the actual date range of the task segment in this time frame
            segment_start_date = max(task_start, tf_start)
            segment_end_date = min(task_finish, tf_end)
            
            # Calculate the pixel positions of this segment within the time frame
            # Match the exact logic used in render_tasks() for consistency:
            # - Calculate from time frame start date, not segment start
            # - Use min() to cap at time frame width (same as render_tasks uses total_days)
            segment_x_start = tf_x + max((segment_start_date - tf_start).days, 0) * tf_time_scale
            segment_x_end = tf_x + min((segment_end_date - tf_start).days + 1, tf_total_days) * tf_time_scale
            
            logging.debug(f"    Segment: {segment_start_date} to {segment_end_date}, x={segment_x_start} to {segment_x_end}, width={segment_x_end - segment_x_start}")
            
            # Track the leftmost and rightmost positions across all time frames
            if total_x_start is None:
                total_x_start = segment_x_start  # First segment's start
            total_x_end = segment_x_end  # Keep updating to the last segment's end
        
        if total_x_start is not None and total_x_end is not None:
            total_width = total_x_end - total_x_start
            logging.debug(f"Calculated total span: start={total_x_start}, end={total_x_end}, width={total_width} for task {task_start} to {task_finish}")
            return (total_x_start, total_width)
        
        logging.debug(f"No total span calculated for task {task_start} to {task_finish} (no overlapping time frames)")
        return None

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
        """Render all tasks that overlap with the current time frame.
        
        This method is called once per time frame during Pass 2 of render_time_frames().
        It renders task bars (rectangles) and labels for all tasks that overlap with
        the current time frame's date range.
        
        For tasks that span multiple time frames:
        - Task bar segments are rendered in each overlapping time frame
        - Inside labels are rendered ONLY in the LAST time frame segment (to appear on top)
        - Outside labels are rendered in each time frame segment (to the right of each segment)
        
        Args:
            x: The absolute x position of the current time frame (in pixels)
            y: The absolute y position of the current time frame (in pixels)
            width: The width of the current time frame (in pixels)
            height: The height of the current time frame (in pixels)
            start_date: The start date of the current time frame (datetime)
            end_date: The end date of the current time frame (datetime)
            num_rows: The number of rows in the Gantt chart
        """
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
                    logging.debug(f"Rendering task bar for '{task_name}': x={x_start}, y={rect_y}, width={width_task}, height={task_height}, row={row_num}, y_task={y_task}")
                    self.dwg.add(self.dwg.rect(insert=(x_start, rect_y), size=(width_task, task_height), fill="blue"))
                    
                    if not label_hide:
                        # Calculate label_y_base based on row position (same for all time frames for this task)
                        # This ensures the label appears at the correct vertical position regardless of which
                        # time frame segment we're rendering
                        label_y_base = rect_y + task_height / 2 + font_size * self.config.general.label_vertical_offset_factor
                        logging.debug(f"  Calculated label_y_base={label_y_base} for task '{task_name}' (rect_y={rect_y}, task_height={task_height}, font_size={font_size}, offset_factor={self.config.general.label_vertical_offset_factor})")
                        
                        if label_placement == "Inside":
                            # ========================================================================
                            # INSIDE LABEL RENDERING LOGIC FOR MULTI-TIME-FRAME TASKS
                            # ========================================================================
                            # When a task spans multiple time frames, the inside label must:
                            # 1. Appear only ONCE (not duplicated in each time frame segment)
                            # 2. Be centered on the TOTAL task span in pixels across all time frames
                            # 3. Be rendered AFTER all task bar segments (to appear on top)
                            #
                            # Strategy: Render the label only when we're processing the LAST time frame
                            # segment where the task appears. This ensures:
                            # - All task bar segments are already rendered (so label appears on top)
                            # - The label is centered correctly on the total span
                            # - The label appears only once
                            #
                            # Detection of last segment: Check if task_finish is within or at the end
                            # of the current time frame (end_date). If so, this is the last segment.
                            # ========================================================================
                            task_id = task.get("task_id")
                            
                            # Check if task_id is present (required for tracking rendered labels)
                            if task_id is None:
                                logging.warning(f"Task '{task_name}' has no task_id, cannot track label rendering. Rendering in current time frame.")
                                # Fallback: render in current time frame segment
                                self._render_inside_label(task_name, x_start, width_task, label_y_base)
                            elif task_id not in self._rendered_inside_labels:
                                # Calculate the total task span across all time frames in absolute pixel coordinates
                                # This uses the pre-calculated _time_frame_info from render_time_frames() pass 1
                                total_span = self._calculate_total_task_span(task_start, task_finish)
                                
                                if total_span:
                                    # Task spans multiple time frames: need to determine if this is the last segment
                                    # The last segment is where the task finishes (task_finish is within or at end_date)
                                    # We add 1 day to end_date to account for inclusive end dates
                                    is_last_segment = task_finish <= end_date
                                    
                                    if is_last_segment:
                                        # This is the last time frame segment where the task appears
                                        # Render the label now, centered on the total span across all segments
                                        # This ensures the label appears on top of all task bar segments
                                        total_x_start, total_width = total_span
                                        logging.debug(f"Rendering inside label for task {task_id} '{task_name}' at total span (last segment): x={total_x_start}, width={total_width}, y={label_y_base}")
                                        self._render_inside_label(task_name, total_x_start, total_width, label_y_base)
                                        # Mark as rendered to prevent duplicate labels
                                        self._rendered_inside_labels.add(task_id)
                                    else:
                                        # Not the last segment yet - skip label rendering for now
                                        # It will be rendered when we process the last segment
                                        logging.debug(f"Skipping label for task {task_id} '{task_name}' - not in last segment (task_finish={task_finish}, end_date={end_date})")
                                else:
                                    # Fallback: either task is in single time frame or calculation failed
                                    # For single time frame tasks, render immediately (this IS the last segment)
                                    logging.warning(f"Could not calculate total span for task {task_id} '{task_name}', rendering in current time frame. Time frame info count: {len(self._time_frame_info)}")
                                    self._render_inside_label(task_name, x_start, width_task, label_y_base)
                                    # Mark as rendered to prevent duplicate labels
                                    self._rendered_inside_labels.add(task_id)
                            # If label already rendered, skip (prevents duplicate labels in each time frame segment)
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
        num_rows = self._get_frame_config("num_rows", 1)
        self.dwg.add(self.dwg.rect(insert=(x, row_y), size=(width, row_frame_height),
                                   fill="none", stroke="purple", stroke_width=1))

        if self._get_frame_config("horizontal_gridlines", False):
            for i in range(num_rows + 1):
                y_pos = row_y + i * (row_frame_height / num_rows)
                self.dwg.add(self.dwg.line((x, y_pos), (x + width, y_pos), stroke="gray", stroke_width=1))

        if self._get_frame_config("vertical_gridlines", False):
            for interval, _ in scale_configs:
                current_date = self.next_period(start_date, interval)
                prev_x = x
                while current_date <= end_date:
                    x_pos = x + (current_date - start_date).days * tf_time_scale
                    interval_width = x_pos - prev_x if x_pos <= x + width else (x + width) - prev_x
                    if x <= x_pos <= x + width and interval_width >= self.config.general.min_interval_width:
                        self.dwg.add(self.dwg.line((x_pos, row_y), (x_pos, row_y + row_frame_height),
                                                   stroke="gray", stroke_width=1))
                    prev_x = x_pos
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
                label_y = y + height * self.config.general.scale_label_vertical_alignment_factor
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
                                               font_size="10", dominant_baseline="middle"))
            prev_x = x_pos
            current_date = next_date

    def render(self):
        logging.debug("Starting render")
        os.makedirs(self.output_folder, exist_ok=True)
        self.start_date = self._set_time_scale()
        self._rendered_inside_labels.clear()  # Reset tracking for new render
        self._time_frame_info.clear()  # Reset time frame info
        self.render_outer_frame()
        self.render_header()
        self.render_footer()
        self.render_inner_frame()
        self.render_time_frames()
        self.dwg.save()
        logging.debug("Render completed")