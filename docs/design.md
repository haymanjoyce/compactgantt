# Gantt Chart Design Notes

## Overview
A brief intro to the app’s purpose: a PyQt5-based Gantt chart generator that renders SVG output from user-defined time frames and tasks. Configurable via `config.py`, it balances flexibility with a clean, readable visual structure.

## Scales
Four time scales (years, months, weeks, days) render as horizontal bands within each time frame, stacked above a row frame. Heights are 20% of row frame height (`SCALE_PROPORTION_*` in `config.py`), with total height split dynamically (row frame = 1 unit, scales proportional). Scales are light grey rectangles with black borders. Intervals mark end dates with vertical lines if width >= `MIN_INTERVAL_WIDTH` (5px), else no lines. Labels center in intervals, showing only if intersecting the time frame: >= `FULL_LABEL_WIDTH` (50px) for full labels (e.g., "2025", "Jan", "02 (12)", "Wed"), >= `SHORT_LABEL_WIDTH` (20px) for short (e.g., "25", "J", "02", "W"), >= `MIN_INTERVAL_WIDTH` for blank, < `MIN_INTERVAL_WIDTH` no label or separator. Weeks use ISO 8601 (Week 1 has first Thursday), with Sunday ends via `get_week_end_date`. Text is 10-point, middle-aligned.

## Signals and Slots
The app uses PyQt5’s signals and slots for asynchronous communication between components. The `GanttChartGenerator` (a `QObject`) emits an `svg_generated` signal (string path) when SVG rendering completes in `generate_svg`. This decouples generation from display, allowing a UI thread (e.g., a main window) to connect a slot (e.g., `update_svg_display`) to receive the path and load the SVG without blocking. The signal is triggered post-render, ensuring the file is ready.

## Frame Structure
The SVG is divided into an outer frame (white, black border), header (light grey, top), footer (light grey, bottom), and inner frame (blue dashed border). Time frames (red borders) span the inner frame horizontally, sized by `width_proportion`. Margins (default 10px) and header/footer heights (50px) are configurable in `frame_config`. The row frame (purple border) below scales holds tasks, with optional gridlines.

## Tasks
Tasks render as blue rectangles within the row frame, positioned by `start_date` and `finish_date` relative to the time frame’s start, scaled by `tf_time_scale` (width/days). Height is 80% of row height, with 10-point white text labels (e.g., "Unnamed"). Rows are indexed (1-based), clipped to `num_rows`.

## Time Frame Logic
Time frames sequence left-to-right, starting from `chart_start_date`, with each ending at its `finish_date` (next frame starts the following day). Widths are proportional to `inner_width` via `width_proportion`. Scales and tasks align to each frame’s date range.

## Configuration
Settings live in `config.py`: window sizes, SVG dimensions, output paths, scale proportions, label thresholds (`FULL_LABEL_WIDTH`, etc.), and defaults (e.g., `num_rows = 1`). This centralizes tweaks without altering core logic.

## Future Considerations
- Task styling (colors, patterns)?
- Interactive zooming/panning?
- Export options beyond SVG?