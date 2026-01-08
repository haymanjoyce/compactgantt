from dataclasses import dataclass, field
from typing import List

@dataclass
class WindowConfig:
    """Configuration for application window sizes and positioning."""
    # Main window (data entry) settings
    data_entry_width: int = 850  # Increased to accommodate all tabs without horizontal scrolling
    data_entry_height: int = 600
    data_entry_screen: int = 0  # Which screen to display on (0 = primary screen)
    data_entry_x: int = 100  # X position in pixels
    data_entry_y: int = 100  # Y position in pixels

    # SVG display window settings
    svg_display_width: int = 800
    svg_display_height: int = 600
    svg_display_screen: int = 0  # Which screen to display on (0 = primary screen)
    svg_display_x: int = 100  # X position in pixels
    svg_display_y: int = 100  # Y position in pixels

    # Last file directories (for file dialogs)
    last_json_directory: str = ""  # Last directory used for JSON file operations
    last_excel_directory: str = ""  # Last directory used for Excel file operations
    
    # Tab order (list of tab names in preferred order)
    tab_order: List[str] = field(default_factory=lambda: [
        "Windows", "Layout", "Titles", "Timeline", "Tasks", "Links", 
        "Swimlanes", "Pipes", "Curtains", "Notes", "Typography"
    ])

    def __post_init__(self):
        # Validate positive integers
        for field_name in ["data_entry_width", "data_entry_height", "svg_display_width",
                          "svg_display_height", "data_entry_screen", "data_entry_x", 
                          "data_entry_y", "svg_display_screen", "svg_display_x", "svg_display_y"]:
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")

