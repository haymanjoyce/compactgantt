from dataclasses import dataclass

@dataclass
class ChartConfig:
    """Configuration for chart/SVG generation and rendering."""
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

    # Default table row counts
    tasks_rows: int = 20         # Default number of rows for new charts
    pipes_rows: int = 3
    curtains_rows: int = 3

    # Default colors and label settings
    default_curtain_color: str = "red"
    leader_line_vertical_default: float = 0.5
    leader_line_horizontal_default: float = 3.0  # Default close offset for outside labels (base distance before user offset)
    label_horizontal_offset_factor: float = 0.0
    label_text_width_factor: float = 0.55
    scale_vertical_alignment_factor: float = 0.7  # Vertical position for scale labels (0.0=top, 0.5=center, 1.0=bottom)
    task_vertical_alignment_factor: float = 0.7  # Vertical position for task labels (0.0=top, 0.5=center, 1.0=bottom)
    row_number_vertical_alignment_factor: float = 0.7  # Vertical position for row numbers (0.0=top, 0.5=center, 1.0=bottom)
    header_footer_vertical_alignment_factor: float = 0.7  # Vertical position for header and footer text (0.0=top, 0.5=center, 1.0=bottom)
    swimlane_top_vertical_alignment_factor: float = 0.7  # Vertical position for top swimlane labels (0.0=top, 0.5=center, 1.0=bottom)
    swimlane_bottom_vertical_alignment_factor: float = 0.7  # Vertical position for bottom swimlane labels (0.0=top, 0.5=center, 1.0=bottom)
    
    # Frame border settings
    frame_border_width_heavy: float = 1.0  # Outer frame border width
    frame_border_width_light: float = 0.5  # Header, footer, scale, and row frame border width
    frame_border_color: str = "grey"  # Border color for all frames
    
    # Font settings
    font_family: str = "Arial"  # Font family for all text elements
    
    # Font sizes
    task_font_size: int = 10  # Font size for task labels
    scale_font_size: int = 10  # Font size for scale labels
    header_footer_font_size: int = 10  # Font size for header and footer text
    row_number_font_size: int = 10  # Font size for row numbers
    note_font_size: int = 10  # Font size for notes
    swimlane_font_size: int = 10  # Font size for swimlane labels

    def __post_init__(self):
        # Validate positive integers
        for field_name in ["outer_width", "outer_height", "full_label_width", 
                          "short_label_width", "tasks_rows", "pipes_rows", "curtains_rows",
                          "task_font_size", "scale_font_size", "header_footer_font_size",
                          "row_number_font_size", "note_font_size", "swimlane_font_size"]:
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")

        # Validate floats
        for field_name in ["scale_proportion_years", "scale_proportion_months",
                          "scale_proportion_weeks", "scale_proportion_days",
                          "leader_line_vertical_default", "leader_line_horizontal_default",
                          "label_horizontal_offset_factor",
                          "label_text_width_factor", "scale_vertical_alignment_factor",
                          "task_vertical_alignment_factor", "row_number_vertical_alignment_factor",
                          "header_footer_vertical_alignment_factor", "swimlane_top_vertical_alignment_factor",
                          "swimlane_bottom_vertical_alignment_factor",
                          "frame_border_width_heavy", "frame_border_width_light"]:
            value = getattr(self, field_name)
            if not isinstance(value, float) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative float")
        
        # Validate font_family is a non-empty string
        if not isinstance(self.font_family, str) or not self.font_family.strip():
            raise ValueError("font_family must be a non-empty string")

