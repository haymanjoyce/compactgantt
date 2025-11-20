from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Callable, Any, Tuple, Optional
from PyQt5.QtCore import QDate
import logging
from utils.conversion import internal_to_display_date, display_to_internal_date, is_valid_display_date

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class GeneralConfig:
    # Window settings (for application window sizes)
    data_entry_width: int = 400
    data_entry_height: int = 500
    svg_display_width: int = 800
    svg_display_height: int = 600

    # Window positioning settings
    data_entry_screen: int = 0  # Which screen to display on (0 = primary screen)
    data_entry_position: str = "center"  # Options: "center", "top_left", "top_right", "bottom_left", "bottom_right", "custom"
    data_entry_x: int = 100  # Custom X position (used when position is "custom")
    data_entry_y: int = 100  # Custom Y position (used when position is "custom")

    # SVG display window positioning settings
    svg_display_screen: int = 1  # Which screen to display on (1 = secondary screen if available)
    svg_display_position: str = "center"  # Options: "center", "top_left", "top_right", "bottom_left", "bottom_right", "custom"
    svg_display_x: int = 100  # Custom X position (used when position is "custom")
    svg_display_y: int = 100  # Custom Y position (used when position is "custom")

    # SVG/image generation settings (for chart resolution)
    outer_width: int = 600      # Main SVG/chart width in pixels (user-facing)
    outer_height: int = 400     # Main SVG/chart height in pixels (user-facing)

    # SVG generation settings
    svg_output_folder: str = "svg"
    svg_output_filename: str = "gantt_chart.svg"

    # Scale proportions
    scale_proportion_years: float = 0.05
    scale_proportion_months: float = 0.05
    scale_proportion_weeks: float = 0.05
    scale_proportion_days: float = 0.05

    # Scale label thresholds
    full_label_width: int = 50
    short_label_width: int = 20
    min_interval_width: int = 5

    # Default table row counts
    tasks_rows: int = 20         # Default number of rows for new charts
    pipes_rows: int = 3
    curtains_rows: int = 3

    # Default colors and label settings
    default_curtain_color: str = "red"
    leader_line_vertical_default: float = 0.5
    leader_line_horizontal_default: float = 10.0  # Fixed pixel offset for outside labels
    label_vertical_offset_factor: float = 0.3
    label_horizontal_offset_factor: float = 0.0
    label_text_width_factor: float = 0.55
    scale_label_vertical_alignment_factor: float = 0.7  # Vertical position within scale interval (0.0=top, 0.5=center, 1.0=bottom)

    def __post_init__(self):
        # Validate positive integers
        for field_name in ["data_entry_width", "data_entry_height", "svg_display_width",
                          "svg_display_height", "outer_width", "outer_height",
                          "full_label_width", "short_label_width", "min_interval_width",
                          "tasks_rows", "pipes_rows", "curtains_rows", "data_entry_screen",
                          "data_entry_x", "data_entry_y", "svg_display_screen",
                          "svg_display_x", "svg_display_y"]:
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")

        # Validate position string
        valid_positions = ["center", "top_left", "top_right", "bottom_left", "bottom_right", "custom"]
        if self.data_entry_position not in valid_positions:
            raise ValueError(f"data_entry_position must be one of: {valid_positions}")
        if self.svg_display_position not in valid_positions:
            raise ValueError(f"svg_display_position must be one of: {valid_positions}")

        # Validate floats
        for field_name in ["scale_proportion_years", "scale_proportion_months",
                          "scale_proportion_weeks", "scale_proportion_days",
                          "leader_line_vertical_default", "leader_line_horizontal_default",
                          "label_vertical_offset_factor", "label_horizontal_offset_factor",
                          "label_text_width_factor", "scale_label_vertical_alignment_factor"]:
            value = getattr(self, field_name)
            if not isinstance(value, float) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative float")

@dataclass
class TableColumnConfig:
    name: str
    default_value: Any = None
    widget_type: str = "text"  # Options: "text", "combo", "date", "checkbox"
    combo_items: List[str] = field(default_factory=list)
    validator: Optional[Callable[[Any], bool]] = None  # Make validator optional

@dataclass
class TableConfig:
    key: str
    columns: List[TableColumnConfig]
    min_rows: int
    default_generator: Callable[[int, Dict[str, Any]], List[Any]]

@dataclass
class AppConfig:
    general: GeneralConfig = field(default_factory=GeneralConfig)
    tables: Dict[str, TableConfig] = field(default_factory=dict)

    def __post_init__(self):
        # Define default value generators
        def time_frames_default(row_idx: int, context: Dict[str, Any]) -> List[Any]:
            logging.debug(f"Generating time_frames_default for row {row_idx}, context: {context}")
            try:
                # Default time frames:
                # #1: 25% width, finishes 5 Jan 2025
                # #2: 25% width, finishes 2 Feb 2025
                # #3: 25% width, finishes 4 May 2025
                # #4: 25% width, finishes 2 Oct 2025
                defaults = [
                    {"id": 1, "finish_date": "2025-01-05", "width": 25},
                    {"id": 2, "finish_date": "2025-02-02", "width": 25},
                    {"id": 3, "finish_date": "2025-05-04", "width": 25},
                    {"id": 4, "finish_date": "2025-10-02", "width": 25}
                ]
                
                if row_idx < len(defaults):
                    default = defaults[row_idx]
                    time_frame_id = default["id"]
                    internal_date = default["finish_date"]
                    finish_date = internal_to_display_date(internal_date)
                    width = default["width"]
                else:
                    # Fallback for additional rows beyond the 4 defaults
                    max_time_frame_id = context.get("max_time_frame_id", 0)
                    time_frame_id = max_time_frame_id + 1
                    internal_date = QDate.currentDate().addDays(7 * (row_idx + 1)).toString("yyyy-MM-dd")
                    finish_date = internal_to_display_date(internal_date)
                    width = int(round(100.0 / max(1, row_idx + 2)))
                
                return [
                    False,  # Checkbox state (unchecked by default)
                    str(time_frame_id),
                    finish_date,
                    str(width)  # Always use str for consistency
                ]
            except Exception as e:
                logging.error(f"Error in time_frames_default: {e}", exc_info=True)                                                                              
                return [
                    False,  # Checkbox state (unchecked by default)
                    str(context.get("max_time_frame_id", 0) + 1),
                    internal_to_display_date(QDate.currentDate().toString("yyyy-MM-dd")),                                                                       
                    "50.0"
                ]

        def tasks_default(row_idx: int, context: Dict[str, Any]) -> List[Any]:
            # Default tasks:
            # #1 - Row 1, Design, 5 Jan 25, 5 Mar 25, Inside
            # #2 - Row 2, Tender, 6 Mar 25, 15 May 25, Inside
            # #3 - Row 2, Contract Award, 7 Mar 25, 7 Mar 25, Outside (milestone)
            # #4 - Row 3, Construct, 8 Mar 25, 15 Aug 25, Inside
            # #5 - Row 4, Planned Completion, 16 Aug 25, 16 Aug 25, Outside (milestone)
            defaults = [
                {"name": "Design", "start": "2025-01-01", "finish": "2025-03-05", "row": 1, "placement": "Inside"},
                {"name": "Tender", "start": "2025-03-06", "finish": "2025-05-15", "row": 2, "placement": "Inside"},
                {"name": "Contract Award", "start": "2025-05-16", "finish": "2025-05-16", "row": 2, "placement": "Outside"},
                {"name": "Construct", "start": "2025-05-17", "finish": "2025-06-15", "row": 3, "placement": "Inside"},
                {"name": "Planned Completion", "start": "2025-06-16", "finish": "2025-06-16", "row": 4, "placement": "Outside"}
            ]
            
            if row_idx < len(defaults):
                default = defaults[row_idx]
                task_id = context.get("max_task_id", 0) + row_idx + 1
                task_order = context.get("max_task_order", 0) + row_idx + 1
                return [
                    str(task_id),
                    str(task_order),
                    str(default["row"]),
                    default["name"],
                    internal_to_display_date(default["start"]),
                    internal_to_display_date(default["finish"]),
                    "Yes",  # Label shown
                    default["placement"]
                ]
            else:
                # Fallback for additional rows beyond the 5 defaults
                task_id = context.get("max_task_id", 0) + 1
                task_order = context.get("max_task_order", 0) + 1
                row_number = str(row_idx + 1)
                internal_start = QDate.currentDate().toString("yyyy-MM-dd")
                internal_finish = QDate.currentDate().toString("yyyy-MM-dd")
                return [
                    str(task_id),
                    str(task_order),
                    row_number,
                    "New Task",
                    internal_to_display_date(internal_start),
                    internal_to_display_date(internal_finish),
                    "Yes",
                    "Outside"
                ]

        def connectors_default(row_idx: int, context: Dict[str, Any]) -> List[Any]:
            return ["1", "2"]

        def swimlanes_default(row_idx: int, context: Dict[str, Any]) -> List[Any]:
            return ["1", "2", f"Swimlane {row_idx + 1}", "lightblue"]

        def pipes_default(row_idx: int, context: Dict[str, Any]) -> List[Any]:
            internal_date = QDate.currentDate().toString("yyyy-MM-dd")
            return [internal_to_display_date(internal_date), "red"]

        def curtains_default(row_idx: int, context: Dict[str, Any]) -> List[Any]:
            internal_date = QDate.currentDate().toString("yyyy-MM-dd")
            return [
                internal_to_display_date(internal_date),
                internal_to_display_date(internal_date), "gray"
            ]

        def text_boxes_default(row_idx: int, context: Dict[str, Any]) -> List[Any]:
            return [f"Text {row_idx + 1}", "100", "100", "black"]

        # Define robust date validator function
        def validate_display_date(x):
            """Validate date in dd/mm/yyyy format."""
            if not x or not str(x).strip():
                return False
            return is_valid_display_date(str(x).strip())

        # Define table configurations
        self.tables = {
            "time_frames": TableConfig(
                key="time_frames",
                columns=[
                    TableColumnConfig("Select", widget_type="checkbox"),  # No validator needed
                    TableColumnConfig(
                        name="Time Frame ID",
                        validator=lambda x: int(x) > 0 if x else False
                    ),
                    TableColumnConfig(
                        name="Finish Date",
                        validator=validate_display_date
                    ),
                    TableColumnConfig(
                        name="Width (%)",
                        validator=lambda x: x.isdigit() and int(x) > 0 if x else False
                    )
                ],
                min_rows=4,
                default_generator=time_frames_default
            ),
            "tasks": TableConfig(
                key="tasks",
                columns=[
                    TableColumnConfig("Select", widget_type="checkbox"),
                    TableColumnConfig("ID", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("Order", validator=lambda x: float(x) > 0 if x else False),
                    TableColumnConfig("Row", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("Name"),
                    TableColumnConfig("Start Date", validator=validate_display_date),
                    TableColumnConfig("Finish Date", validator=validate_display_date),
                    TableColumnConfig("Label", widget_type="combo", combo_items=["No", "Yes"], default_value="Yes"),
                    TableColumnConfig("Placement", widget_type="combo", combo_items=["Inside", "Outside"])
                ],
                min_rows=5,
                default_generator=lambda row_idx, context: [False] + tasks_default(row_idx, context)
            ),
            "connectors": TableConfig(
                key="connectors",
                columns=[
                    TableColumnConfig("Select", widget_type="checkbox"),
                    TableColumnConfig("From Task ID", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("To Task ID", validator=lambda x: int(x) > 0 if x else False)
                ],
                min_rows=0,
                default_generator=lambda row_idx, context: [False] + connectors_default(row_idx, context)
            ),
            "swimlanes": TableConfig(
                key="swimlanes",
                columns=[
                    TableColumnConfig("Select", widget_type="checkbox"),
                    TableColumnConfig("From Row Number", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("To Row Number", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("Title"),
                    TableColumnConfig("Colour")
                ],
                min_rows=0,
                default_generator=lambda row_idx, context: [False] + swimlanes_default(row_idx, context)
            ),
            "pipes": TableConfig(
                key="pipes",
                columns=[
                    TableColumnConfig("Select", widget_type="checkbox"),
                    TableColumnConfig("Date", validator=validate_display_date),
                    TableColumnConfig("Colour")
                ],
                min_rows=0,
                default_generator=lambda row_idx, context: [False] + pipes_default(row_idx, context)
            ),
            "curtains": TableConfig(
                key="curtains",
                columns=[
                    TableColumnConfig("Select", widget_type="checkbox"),
                    TableColumnConfig("From Date", validator=validate_display_date),
                    TableColumnConfig("To Date", validator=validate_display_date),
                    TableColumnConfig("Colour")
                ],
                min_rows=0,
                default_generator=lambda row_idx, context: [False] + curtains_default(row_idx, context)
            ),
            "text_boxes": TableConfig(
                key="text_boxes",
                columns=[
                    TableColumnConfig("Select", widget_type="checkbox"),
                    TableColumnConfig("Text"),
                    TableColumnConfig("X Coordinate", validator=lambda x: float(x) >= 0 if x else False),
                    TableColumnConfig("Y Coordinate", validator=lambda x: float(x) >= 0 if x else False),
                    TableColumnConfig("Colour")
                ],
                min_rows=0,
                default_generator=lambda row_idx, context: [False] + text_boxes_default(row_idx, context)
            )
        }

    def get_table_config(self, key: str) -> TableConfig:
        return self.tables.get(key, None)
