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
    leader_line_horizontal_default: float = 10.0  # Fixed pixel offset for outside labels
    label_horizontal_offset_factor: float = 0.0
    label_text_width_factor: float = 0.55
    text_vertical_alignment_factor: float = 0.7  # Vertical position for all text (0.0=top, 0.5=center, 1.0=bottom). Used for header, footer, scales, and task labels.

    # Font sizes
    task_font_size: int = 10  # Font size for task labels
    scale_font_size: int = 10  # Font size for scale labels
    header_footer_font_size: int = 10  # Font size for header and footer text

    def __post_init__(self):
        # Validate positive integers
        for field_name in ["outer_width", "outer_height", "full_label_width", 
                          "short_label_width", "tasks_rows", "pipes_rows", "curtains_rows",
                          "task_font_size", "scale_font_size", "header_footer_font_size"]:
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")

        # Validate floats
        for field_name in ["scale_proportion_years", "scale_proportion_months",
                          "scale_proportion_weeks", "scale_proportion_days",
                          "leader_line_vertical_default", "leader_line_horizontal_default",
                          "label_horizontal_offset_factor",
                          "label_text_width_factor", "text_vertical_alignment_factor"]:
            value = getattr(self, field_name)
            if not isinstance(value, float) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative float")

