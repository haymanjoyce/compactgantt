# Compact Gantt

## Purpose
This tool creates compact Gantt charts using PyQt5 and SVG output, allowing multiple tasks per row, customizable zoom, and flexible label placement.

## Features
- **Customizable Charts**: Define chart dimensions, margins, header/footer text, and gridlines.
- **Time Frames**: Set time spans with unique IDs, finish dates, and proportional widths.
- **Tasks and Milestones**: Add tasks (rectangles) and milestones (diamonds) with customizable labels (placement, alignment, offsets, colors).
- **Scales**: Display years, months, weeks, and days with dynamic labels based on available space.
- **GUI**: Enter data via tabs (Layout, Time Frames, Tasks, Connectors, Swimlanes, Pipes, Curtains, Text Boxes) with sortable tables, add/remove rows, and visual feedback for invalid data.
- **Output**: Generate and display SVG charts; import/export project data as JSON.

## Example
See a hand-drawn sample of the desired output:

![Sample POAP](docs/images/Sample%20POAP.png)

## Quick Start
1. Ensure Python 3.8+ is installed.
2. Clone the repo: `git clone https://github.com/haymanjoyce/gantt_02.git`.
3. Navigate to the directory: `cd haymanjoyce-gantt_02`.
4. Install dependencies: `pip install -r requirements.txt`.
5. Run the tool: `python main.py`.
6. In the GUI, enter data (e.g., time frame from 2025-01-01 to 2025-02-01), then click "Generate Gantt Chart" to view the SVG.

## Requirements
- Python 3.8+
- PyQt5 (`pip install PyQt5`)
- svgwrite (`pip install svgwrite`)

## Data Entry Tabs
- **Layout Tab**:
  - Outer width/height (e.g., 800, 600)
  - Header/footer height (e.g., 50)
  - Margins (top, right, bottom, left; e.g., 10)
  - Header/footer text (e.g., "Project Timeline")
  - Number of rows (e.g., 1)
  - Horizontal/vertical gridlines (Yes/No)
  - Start date (e.g., 2025-01-01)
- **Time Frames Tab**:
  - Time Frame ID (auto-generated, unique)
  - Finish date (e.g., 2025-02-01)
  - Width percentage (e.g., 100%)
- **Tasks Tab**:
  - Task ID (auto-generated)
  - Task order (e.g., 1.0)
  - Task name (e.g., "Design Phase")
  - Start/finish date (e.g., 2025-01-05, 2025-01-15)
  - Row number (e.g., 1)
  - Label placement (Inside, To left, To right, Above, Below)
  - Label hide (Yes/No)
  - Label alignment (Left, Centre, Right)
  - Label horizontal/vertical offset (e.g., 1.0, 0.5)
  - Label text color (e.g., "#FF0000")
- **Connectors Tab**:
  - From Task ID (e.g., 1)
  - To Task ID (e.g., 2)
- **Swimlanes Tab**:
  - From Row Number (e.g., 1)
  - To Row Number (e.g., 2)
  - Title (e.g., "Swimlane 1")
  - Color (e.g., "lightblue")
- **Pipes Tab**:
  - Date (e.g., 2025-01-10)
  - Color (e.g., "red")
- **Curtains Tab**:
  - From Date (e.g., 2025-01-01)
  - To Date (e.g., 2025-01-15)
  - Color (e.g., "gray")
- **Text Boxes Tab**:
  - Text (e.g., "Note")
  - X Coordinate (e.g., 100)
  - Y Coordinate (e.g., 100)
  - Color (e.g., "black")

## Files
- `main.py`: Application entry point.
- `data_model.py`: Defines data structures (`FrameConfig`, `Task`, `ProjectData`).
- `app_config.py`: Application settings (window sizes, SVG dimensions).
- `svg_generator.py`: Generates SVG Gantt charts.
- `svg_display.py`: Displays SVG output.
- `ui/data_entry_window.py`: Main GUI window with tabs.
- `ui/tabs/layout_tab.py`: Layout tab for chart settings.
- `ui/tabs/time_frames_tab.py`: Time Frames tab for time spans.
- `ui/tabs/tasks_tab.py`: Tasks tab for task entry.
- `ui/tabs/connectors_tab.py`: Connectors tab for task dependencies.
- `ui/tabs/swimlanes_tab.py`: Swimlanes tab for row grouping.
- `ui/tabs/pipes_tab.py`: Pipes tab for vertical lines.
- `ui/tabs/curtains_tab.py`: Curtains tab for date range highlights.
- `ui/tabs/text_boxes_tab.py`: Text Boxes tab for custom text.
- `ui/table_utils.py`: Table utilities (row insertion, context menus).
- `requirements.txt`: Python dependencies.
- `readme.md`: This documentation.

## Folders
- `ui/`: User interface modules.
- `ui/tabs/`: Tab-specific UI implementations.
- `svg/`: Generated SVG output.
- `examples/`: Sample images (e.g., `Sample POAP.png`).