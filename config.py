"""
Purpose: Centralizes configuration settings for the Gantt Chart Application.
Why: Makes it easy to adjust sizes, paths, and defaults without changing core code.
"""

class Config:
    # Window settings
    DATA_ENTRY_WIDTH = 800
    DATA_ENTRY_HEIGHT = 500
    SVG_DISPLAY_WIDTH = 800
    SVG_DISPLAY_HEIGHT = 400

    # SVG generation settings
    SVG_WIDTH = 800
    SVG_HEIGHT = 400
    SVG_OUTPUT_FOLDER = "svg"
    SVG_OUTPUT_FILENAME = "gantt_chart.svg"

    # Scale proportions (relative to row_frame height within time_frame)
    SCALE_PROPORTION_YEARS = 0.2   # e.g., 20% of row_frame height
    SCALE_PROPORTION_MONTHS = 0.2
    SCALE_PROPORTION_WEEKS = 0.2
    SCALE_PROPORTION_DAYS = 0.2

    # Scale label thresholds (in pixels)
    FULL_LABEL_WIDTH = 50          # Width for full labels (e.g., "2025", "02 (12)")
    SHORT_LABEL_WIDTH = 20         # Width for short labels (e.g., "25", "02")
    MIN_INTERVAL_WIDTH = 5         # Minimum width for separators and blank labels

    # Default table row counts
    TASKS_ROWS = 5
    PIPES_ROWS = 3
    CURTAINS_ROWS = 3

    # Default colors
    DEFAULT_CURTAIN_COLOR = "red"