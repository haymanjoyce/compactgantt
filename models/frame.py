from dataclasses import dataclass
from typing import Tuple


@dataclass
class FrameConfig:
    outer_width: int = 800
    outer_height: int = 600
    header_height: int = 20
    footer_height: int = 20
    margins: Tuple[int, int, int, int] = (10, 10, 10, 10)
    num_rows: int = 1
    header_text: str = ""
    footer_text: str = ""
    horizontal_gridlines: bool = True
    vertical_gridline_years: bool = True
    vertical_gridline_months: bool = True
    vertical_gridline_weeks: bool = False
    vertical_gridline_days: bool = False
    chart_start_date: str = "2024-12-30"
    show_years: bool = True
    show_months: bool = True
    show_weeks: bool = True
    show_days: bool = True
