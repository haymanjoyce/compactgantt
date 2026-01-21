from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Callable, Any, Tuple, Optional
from PyQt5.QtCore import QDate
from PyQt5.QtGui import QColor
import logging
import json
import os
from pathlib import Path
from utils.conversion import internal_to_display_date, display_to_internal_date, is_valid_display_date
from config.window_config import WindowConfig
from config.chart_config import ChartConfig
from config.ui_config import UIConfig
from config.date_config import DateConfig

# Logging is configured centrally in utils/logging_config.py

@dataclass
class GeneralConfig:
    """General configuration that composes window, chart, UI, and date configs for backward compatibility."""
    window: WindowConfig = field(default_factory=WindowConfig)
    chart: ChartConfig = field(default_factory=ChartConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    ui_date_config: DateConfig = field(default_factory=DateConfig)  # Date format for data entry UI (tables, date pickers, Excel)
    chart_date_config: DateConfig = field(default_factory=DateConfig)  # Date format for chart display (task labels)
    show_ids_on_chart: bool = False  # Toggle to show task/milestone IDs on the chart
    enable_crash_reporting: bool = True  # Enable crash reporting and telemetry
    crash_report_email: str = "haymanjoyce@gmail.com"  # Email address for crash report recipient (optional)

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
    def scale_vertical_alignment_factor(self) -> float:
        return self.chart.scale_vertical_alignment_factor

    @property
    def task_vertical_alignment_factor(self) -> float:
        return self.chart.task_vertical_alignment_factor

    @property
    def row_number_vertical_alignment_factor(self) -> float:
        return self.chart.row_number_vertical_alignment_factor

    @property
    def header_footer_vertical_alignment_factor(self) -> float:
        return self.chart.header_footer_vertical_alignment_factor

    @property
    def swimlane_top_vertical_alignment_factor(self) -> float:
        return self.chart.swimlane_top_vertical_alignment_factor

    @property
    def swimlane_bottom_vertical_alignment_factor(self) -> float:
        return self.chart.swimlane_bottom_vertical_alignment_factor

    @property
    def font_family(self) -> str:
        return self.chart.font_family

    @property
    def task_font_size(self) -> int:
        return self.chart.task_font_size

    @property
    def scale_font_size(self) -> int:
        return self.chart.scale_font_size

    @property
    def header_footer_font_size(self) -> int:
        return self.chart.header_footer_font_size

    @property
    def row_number_font_size(self) -> int:
        return self.chart.row_number_font_size

    @property
    def note_font_size(self) -> int:
        return self.chart.note_font_size

    @property
    def swimlane_font_size(self) -> int:
        return self.chart.swimlane_font_size

    @property
    def frame_border_width_heavy(self) -> float:
        return self.chart.frame_border_width_heavy

    @property
    def frame_border_width_light(self) -> float:
        return self.chart.frame_border_width_light

    @property
    def frame_border_color(self) -> str:
        return self.chart.frame_border_color
    
    @property
    def read_only_bg_color(self) -> QColor:
        return self.ui.read_only_bg_color
    
    @property
    def table_header_stylesheet(self) -> str:
        return self.ui.table_header_stylesheet
    
    @property
    def table_stylesheet(self) -> str:
        return self.ui.table_stylesheet

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

@dataclass
class AppConfig:
    general: GeneralConfig = field(default_factory=GeneralConfig)
    tables: Dict[str, TableConfig] = field(default_factory=dict)

    def __post_init__(self):
        # Load settings first, before initializing tables
        self._load_settings()
        
        # Define robust date validator function using DateConfig
        def validate_display_date(x):
            """Validate date in configured display format."""
            if not x or not str(x).strip():
                return False
            return is_valid_display_date(str(x).strip(), self.general.ui_date_config)

        # Define table configurations
        self.tables = {
            "tasks": TableConfig(
                key="tasks",
                columns=[
                    TableColumnConfig("ID", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("Row", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("Name"),
                    TableColumnConfig("Start Date", validator=validate_display_date),
                    TableColumnConfig("Finish Date", validator=validate_display_date),
                    TableColumnConfig("Lane", widget_type="text"),  # Read-only, calculated from swimlanes
                    TableColumnConfig("Label", widget_type="combo", combo_items=["No", "Yes"], default_value="Yes"),
                    TableColumnConfig("Placement", widget_type="combo", combo_items=["Inside", "Outside"]),
                    TableColumnConfig("Valid", widget_type="text", default_value="Yes")
                ],
                min_rows=0  # Allow users to delete all rows
            ),
            "links": TableConfig(
                key="links",
                columns=[
                    TableColumnConfig("ID", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("From Task ID", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("From Task Name", widget_type="text"),
                    TableColumnConfig("To Task ID", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("To Task Name", widget_type="text"),
                    TableColumnConfig("Valid", widget_type="text", default_value="Yes")
                ],
                min_rows=0  # Allow users to delete all rows
            ),
            "swimlanes": TableConfig(
                key="swimlanes",
                columns=[
                    TableColumnConfig("Lane", widget_type="text"),  # Read-only, calculated from row position
                    TableColumnConfig("ID", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("Row Count", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("Title")
                ],
                min_rows=0
            ),
            "pipes": TableConfig(
                key="pipes",
                columns=[
                    TableColumnConfig("ID", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("Date", validator=validate_display_date),
                    TableColumnConfig("Name")
                ],
                min_rows=0
            ),
            "curtains": TableConfig(
                key="curtains",
                columns=[
                    TableColumnConfig("ID", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("Start Date", validator=validate_display_date),
                    TableColumnConfig("End Date", validator=validate_display_date),
                    TableColumnConfig("Name")
                ],
                min_rows=0
            ),
            "notes": TableConfig(
                key="notes",
                columns=[
                    TableColumnConfig("ID", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("X", validator=lambda x: int(x) >= 0 if x else False),
                    TableColumnConfig("Y", validator=lambda x: int(x) >= 0 if x else False),
                    TableColumnConfig("Width", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("Height", validator=lambda x: int(x) > 0 if x else False),
                    TableColumnConfig("Text Align", widget_type="combo", combo_items=["Left", "Center", "Right"], default_value="Center"),
                    TableColumnConfig("Vertical Align", widget_type="combo", combo_items=["Top", "Middle", "Bottom"], default_value="Middle"),
                    TableColumnConfig("Text Preview", widget_type="text")
                ],
                min_rows=0
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
                        window_data = data['window'].copy()
                        # Handle tab_order separately if it exists
                        if 'tab_order' in window_data:
                            # tab_order is already a list, no conversion needed
                            pass
                        self.general.window = WindowConfig(**window_data)
                    # Load general settings
                    if 'general' in data:
                        general_data = data['general']
                        if isinstance(general_data, dict):
                            self.general.show_ids_on_chart = general_data.get('show_ids_on_chart', self.general.show_ids_on_chart)
                            self.general.enable_crash_reporting = general_data.get('enable_crash_reporting', self.general.enable_crash_reporting)
                            self.general.crash_report_email = general_data.get('crash_report_email', self.general.crash_report_email)
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
                    'last_json_directory': self.general.window.last_json_directory,
                    'last_excel_directory': self.general.window.last_excel_directory,
                    'tab_order': self.general.window.tab_order,
                },
                'general': {
                    'show_ids_on_chart': self.general.show_ids_on_chart,
                    'enable_crash_reporting': self.general.enable_crash_reporting,
                    'crash_report_email': self.general.crash_report_email,
                }
            }
            with open(settings_file, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
