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

    # Default table row counts
    TASKS_ROWS = 5
    PIPES_ROWS = 3
    CURTAINS_ROWS = 3

    # Default colors
    DEFAULT_CURTAIN_COLOR = "red"