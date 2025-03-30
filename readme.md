# Project Planning Tool

## Purpose
This tool helps users create compact, visually rich Gantt charts, packing extensive project-planning details into a single, customizable page.

## Quick Start
1. Ensure Python 3.8+ and PyQt5 are installed: `pip install PyQt5 svgwrite`.
2. Clone the repo: `git clone <repo-url>`.
3. Navigate to the directory: `cd haymanjoyce-gantt_02`.
4. Run the tool: `python main.py`.
5. Use the "Generate Gantt Chart" toolbar button to see your chart in SVG.

## Requirements
- Python 3.8+
- PyQt5 (`pip install PyQt5`)
- svgwrite (`pip install svgwrite`)

## Problem
Existing tools fall short because:

- Only one task fits per row.
- Magnification can’t vary across the timeline.
- Labels and connectors lack selective placement.
- Dimensions are hard to control for paper/slide fit.
- Hand-drawn charts (e.g., in PowerPoint) are slow and error-prone.
- Typical Gantt charts are visually unappealing.

## Chart Design

### Layout Components

 - outer_frame - control of overall dimensions of inked area; user can apply un-inked margins (i.e. offsets)
 - header - sits at top of outer_frame; full width of outer_frame; only one header row available (design decision)
 - footer - sits at bottom of outer_frame; full width of outer_frame; only one footer row available (design decision)
 - inner_frame - sits between header_frame and footer_frame; full width of outer_frame
 - time_frame - sits inside inner_frame; time_frames able to show chart at different levels of magnification
 - upper_scale - sits inside time_frame; shows the timescale; full width of time_frame; placed at top of time_frame
 - lower_scale - sits inside time_frame; shows the timescale; full width of time_frame; placed below upper_scale
 - row_frame - sits inside a time_frame; contains rows; full width of inner_frame; placed below lower_scale
 - row - sits inside row_frame; can be multiple rows; full width of row_frame; users defines number of rows
 - swimlane - sits in inner_frame; can be used to group rows visually; full width of inner_frame

### Subcomponents

 - gridlines - applied to row_frame; can be horizontal, vertical, or both
 - task - multiple tasks can be assigned to a row
 - milestone - assigned to a row
 - connector - line showing flow of logic between a task and/or milestone
 - text_box - user defined text boxes; can be placed anywhere
 - curtain - user defined time interval; can be placed anywhere inside a row_frame
 - pipe - user defined time point; can be placed anywhere inside a row_frame

### Design Notes

 - If there is one time_frame in the inner_frame, then it is the same width as the inner_frame
 - If there are multiple time_frames in the inner_frame, then they are stacked horizontally (i.e., left to right)
 - The width of the time_frame is defined by the user as a proportion of the inner_frame width
 - The first time_frame from the left will, typically, be the most detailed (i.e., highest magnification)
 - All time_frames must have the same number of rows 
 - The user can define the number of rows in the row_frame
 - First time frame (leftmost) is typically the most detailed (highest magnification)
 - Subsequent time frames may use lower magnification for broader overviews
 - A curtain may start in one time_frame and end in another
 - Time frames are contiguous (i.e., no gaps between them)
 - Time frames cannot overlap

## User Interface Requirements

 - Tabs and fields on data entry window:
   - layout tab (list)
     - top margin
     - right margin
     - bottom margin
     - left margin
     - outer width
     - outer height
     - header height - integer
     - footer height - integer
     - header text - string
     - footer text - string
     - upper scale height - integer
     - lower scale height - integer
     - number of rows - integer
     - horizontal gridlines - yes/no
     - vertical gridlines - yes/no
   - time frames tab (table)
     - start date - date
     - finish date - date
     - width - percentage
     - upper scale intervals - for example, days, weeks, months, years
     - lower scale intervals - for example, days, weeks, months, years
   - tasks tab (table)
     - task id - integer
     - task name - string
     - start date - date
     - finish date - date
     - row number - integer
   - connectors tab (table)
     - from task id - integer
     - to task id - integer
   - swimlanes tab (table)
     - from row number - integer
     - to row number - integer
     - title - string
     - colour - string
   - pipes tab (table)
     - date - date
     - colour - string
   - curtains tab (table)
     - from date - date
     - to date - date
     - colour - string
   - text boxes tab (table)
     - text - string
     - x coordinate - float
     - y coordinate - float
     - colour - string

## Signals & Slots Notes

 - data_entry.py: Emits data_updated with self.project_data.to_json() whenever data is synced (e.g., after adding/removing rows, saving, or generating the chart).
 - svg_generator.py: Receives this JSON dict via generate_svg and renders it into an SVG, emitting svg_generated.
 - svg_display.py: Updates the display based on the SVG path from svg_generated.

## Files

 - main.py: Entry point for the application.
 - data_model.py: Defines the data model for the project data.
 - data_entry.py: Handles the data entry window and user input.
 - svg_generator.py: Generates the SVG file based on user input.
 - svg_display.py: Displays the generated SVG file.
 - config.py: Configuration settings for the application.
 - .gitignore: Specifies files to ignore in version control.
 - LICENSE: License information for the project.
 - requirements.txt: Lists the required Python packages for the project.
 - README.md: Documentation for the project.

## Folders

 - gantt_02/: Main project directory.
 - docs/: Directory for additional documentation.
 - tests/: Directory for unit tests.
 - assets/: Directory for assets like icons and images.
 - resources/: Directory for resources like SVG templates or stylesheets.
 - examples/: Directory for example SVG files or screenshots.
 - scripts/: Directory for utility scripts or command-line tools.
 - data/: Directory for sample data files or templates.
 - logs/: Directory for log files.
 - svg/: Directory for generated SVG files.

## License

TBD (To be determined — see Packaging & Distribution for plans).

## To Do

### Chart Design

 - [x] layout (outer_frame, header, footer, inner_frame, upper_scale, lower_scale, row_frame, row)
 - [x] timeframes
 - [ ] scales
 - [x] gridlines
 - [ ] tasks
 - [ ] milestones
 - [ ] connectors
 - [ ] text boxes
 - [ ] curtains
 - [ ] pipes
 - [ ] swimlanes

### User Interface

 - [x] data entry window
 - [x] data entry tabs
 - [x] data entry tables
 - [ ] data entry fields
 - [x] data entry buttons
 - [ ] table sorting
 - [ ] table filtering
 - [ ] table searching
 - [ ] table editing (add, edit, delete)
 - [ ] window resizing
 - [ ] window scrolling
 - [x] window zooming
 - [ ] shortcuts

### File Input & Output

 - [x] import and export JSON
 - [ ] import and export xlsx
 - [ ] import and export svg
 - [ ] print to pdf
 - [ ] print to raster

### Production

 - [ ] logging
 - [ ] testing
 - [ ] error handling (including try and except)

### Packaging & Distribution

 - [ ] setup.py
 - [ ] requirements.txt
 - [ ] windows executable
 - [ ] PyPI package
 - [ ] documentation
 - [ ] versioning
 - [ ] licensing
 - [ ] internationalization
 - [ ] accessibility
