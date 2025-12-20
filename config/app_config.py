from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Callable, Any, Tuple, Optional
from PyQt5.QtCore import QDate
import logging
import json
import os
from pathlib import Path
from utils.conversion import internal_to_display_date, display_to_internal_date, is_valid_display_date
from config.window_config import WindowConfig
from config.chart_config import ChartConfig

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class GeneralConfig:
    """General configuration that composes window and chart configs for backward compatibility."""
    window: WindowConfig = field(default_factory=WindowConfig)
    chart: ChartConfig = field(default_factory=ChartConfig)

    # Backward compatibility properties - delegate to window and chart configs
    @property
    def data_entry_width(self) -> int:
        return self.window.data_entry_width

    @property
    def data_entry_height(self) -> int:
        return self.window.data_entry_height

    @property
    def svg_display_width(self) -> int:
        return self.window.svg_display_width

    @property
    def svg_display_height(self) -> int:
        return self.window.svg_display_height

    @property
    def data_entry_screen(self) -> int:
        return self.window.data_entry_screen

    @data_entry_screen.setter
    def data_entry_screen(self, value: int):
        self.window.data_entry_screen = value

    @property
    def data_entry_x(self) -> int:
        return self.window.data_entry_x

    @data_entry_x.setter
    def data_entry_x(self, value: int):
        self.window.data_entry_x = value

    @property
    def data_entry_y(self) -> int:
        return self.window.data_entry_y

    @data_entry_y.setter
    def data_entry_y(self, value: int):
        self.window.data_entry_y = value

    @property
    def svg_display_screen(self) -> int:
        return self.window.svg_display_screen

    @svg_display_screen.setter
    def svg_display_screen(self, value: int):
        self.window.svg_display_screen = value

    @property
    def svg_display_x(self) -> int:
        return self.window.svg_display_x

    @svg_display_x.setter
    def svg_display_x(self, value: int):
        self.window.svg_display_x = value

    @property
    def svg_display_y(self) -> int:
        return self.window.svg_display_y

    @svg_display_y.setter
    def svg_display_y(self, value: int):
        self.window.svg_display_y = value

    @property
    def outer_width(self) -> int:
        return self.chart.outer_width

    @property
    def outer_height(self) -> int:
        return self.chart.outer_height

    @property
    def svg_output_folder(self) -> str:
        return self.chart.svg_output_folder

    @property
    def svg_output_filename(self) -> str:
        return self.chart.svg_output_filename

    @property
    def scale_proportion_years(self) -> float:
        return self.chart.scale_proportion_years

    @property
    def scale_proportion_months(self) -> float:
        return self.chart.scale_proportion_months

    @property
    def scale_proportion_weeks(self) -> float:
        return self.chart.scale_proportion_weeks

    @property
    def scale_proportion_days(self) -> float:
        return self.chart.scale_proportion_days

    @property
    def full_label_width(self) -> int:
        return self.chart.full_label_width

    @property
    def short_label_width(self) -> int:
        return self.chart.short_label_width

    @property
    def tasks_rows(self) -> int:
        return self.chart.tasks_rows

    @property
    def pipes_rows(self) -> int:
        return self.chart.pipes_rows

    @property
    def curtains_rows(self) -> int:
        return self.chart.curtains_rows

    @property
    def default_curtain_color(self) -> str:
        return self.chart.default_curtain_color

    @property
    def leader_line_vertical_default(self) -> float:
        return self.chart.leader_line_vertical_default

    @property
    def leader_line_horizontal_default(self) -> float:
        return self.chart.leader_line_horizontal_default

    @property
    def label_horizontal_offset_factor(self) -> float:
        return self.chart.label_horizontal_offset_factor

    @property
    def label_text_width_factor(self) -> float:
        return self.chart.label_text_width_factor

    @property
    def text_vertical_alignment_factor(self) -> float:
        return self.chart.text_vertical_alignment_factor

    @property
    def task_font_size(self) -> int:
        return self.chart.task_font_size

    @property
    def scale_font_size(self) -> int:
        return self.chart.scale_font_size

    @property
    def header_footer_font_size(self) -> int:
        return self.chart.header_footer_font_size

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
        # Load settings first, before initializing tables
        self._load_settings()
        
        # Define default value generators
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

    def _get_settings_file(self) -> str:
        """Get path to settings file."""
        if os.name == 'nt':  # Windows
            config_dir = Path(os.getenv('APPDATA', '')) / 'compact_gantt'
        else:  # Linux/Mac
            config_dir = Path.home() / '.config' / 'compact_gantt'
        config_dir.mkdir(parents=True, exist_ok=True)
        return str(config_dir / 'settings.json')

    def _load_settings(self):
        """Load window settings from file if it exists."""
        settings_file = self._get_settings_file()
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                    if 'window' in data:
                        self.general.window = WindowConfig(**data['window'])
            except Exception as e:
                logging.warning(f"Failed to load settings: {e}")

    def save_settings(self):
        """Save window settings to file."""
        settings_file = self._get_settings_file()
        try:
            data = {
                'window': {
                    'data_entry_width': self.general.window.data_entry_width,
                    'data_entry_height': self.general.window.data_entry_height,
                    'data_entry_screen': self.general.window.data_entry_screen,
                    'data_entry_x': self.general.window.data_entry_x,
                    'data_entry_y': self.general.window.data_entry_y,
                    'svg_display_width': self.general.window.svg_display_width,
                    'svg_display_height': self.general.window.svg_display_height,
                    'svg_display_screen': self.general.window.svg_display_screen,
                    'svg_display_x': self.general.window.svg_display_x,
                    'svg_display_y': self.general.window.svg_display_y,
                }
            }
            with open(settings_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
