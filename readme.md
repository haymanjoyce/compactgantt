# Compact Gantt

A PyQt5-based tool for creating compact Gantt charts with SVG output.

## Features

- **Chart Configuration**
  - Customizable chart dimensions, margins, and gridlines
  - Configurable header and footer with custom text
  - Multiple time scales (years, months, weeks, days) with independent visibility and gridline controls
  - Horizontal and vertical gridline customization

- **Task Management**
  - Add, remove, and duplicate tasks
  - Task properties: ID, Order, Row, Name, Start Date, Finish Date
  - Task formatting: Label visibility (Show/Hide) and placement (Inside/Outside)
  - Numeric sorting for ID, Order, and Row columns
  - Chronological sorting for Start Date and Finish Date columns
  - Default sort by Task ID

- **Data Management**
  - Import/export project data as JSON
  - Save and load project configurations
  - Data validation with error highlighting

- **User Interface**
  - Tab-based interface for organized configuration
  - Window positioning preferences
  - Real-time chart preview with SVG output

## Quick Start

```bash
# Install dependencies
pip install -r requirements-minimal.txt

# Run the application
python main.py
```

## Requirements

- Python 3.8+
- PyQt5
- svgwrite

## Usage

1. **Launch the application** - Two windows will open: the data entry window and the SVG display window
2. **Configure chart settings** in the various tabs:
   - **Windows**: Configure window positioning and preferences
   - **Layout**: Set chart dimensions, margins, and number of rows
   - **Titles**: Configure header and footer text and heights
   - **Scales**: Control time scale visibility (years, months, weeks, days)
   - **Grid**: Configure horizontal and vertical gridline display
   - **Tasks**: Add and manage tasks with dates, formatting, and properties
3. **Add tasks** in the Tasks tab:
   - Click "Add Task" to create a new task
   - Fill in task details (Name, Start Date, Finish Date, Row, etc.)
   - Configure label visibility and placement in the Task Formatting section
   - Use "Duplicate Task" to copy selected tasks with new IDs
4. **Click "Update Image"** to generate the SVG chart

## Tabs Overview

- **Windows**: Window positioning and screen preferences
- **Layout**: Chart dimensions, margins, and row configuration
- **Titles**: Header and footer settings
- **Scales**: Time scale visibility and configuration
- **Grid**: Gridline display options
- **Tasks**: Task management and formatting
- **Connectors**: Task dependency connectors (placeholder)
- **Swimlanes**: Swimlane configuration
- **Pipes**: Pipe elements (placeholder)
- **Curtains**: Curtain elements (placeholder)
- **Text Boxes**: Text annotation elements (placeholder)

## Keyboard Shortcuts

- **Ctrl+S**: Save project to JSON
- **Ctrl+O**: Load project from JSON

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python tests/test_project_save_load.py
```

## Project Structure

- `ui/` - User interface components
  - `tabs/` - Tab widgets (Layout, Tasks, Titles, etc.)
  - `table_utils.py` - Table utility functions
  - `main_window.py` - Main application window
  - `svg_display.py` - SVG preview window
- `services/` - Business logic
  - `gantt_chart_service.py` - SVG chart generation
- `models/` - Data structures
  - `project.py` - Project data model
  - `task.py` - Task model
  - `frame.py` - Frame configuration
- `repositories/` - File I/O
  - `project_repository.py` - JSON save/load
- `config/` - Configuration
  - `app_config.py` - Application configuration
- `validators/` - Data validation
- `utils/` - Utility functions
- `tests/` - Test files
