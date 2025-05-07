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
- **Layout Tab**: Chart settings (dimensions, margins, header/footer, gridlines, start date, etc.)
- **Time Frames Tab**: Time Frame ID (auto-generated, unique), Finish date, Width percentage.
- **Tasks Tab**: Task ID (auto-generated), Task order, Task name, Start/finish date, Row number, label options, etc.
- **Other Tabs**: Connectors, Swimlanes, Pipes, Curtains, and Text Boxes are currently placeholders for future development.

## Files
- `main.py`: Application entry point.
- `config/app_config.py`: Application settings (window sizes, SVG dimensions).
- `ui/data_entry_window.py`: Main GUI window with tabs.
- `ui/svg_display.py`: Displays SVG output.
- `ui/table_utils.py`: Table widget utilities (row insertion, removal, etc.).
- `ui/tabs/layout_tab.py`: Layout tab for chart settings.
- `ui/tabs/time_frames_tab.py`: Time Frames tab for time spans.
- `ui/tabs/tasks_tab.py`: Tasks tab for task entry.
- `ui/tabs/placeholder_tab.py`: Placeholder for unimplemented tabs.
- `services/gantt_chart_service.py`: Generates SVG Gantt charts.
- `services/project_service.py`: Project-level business logic.
- `services/task_service.py`: Task-related business logic.
- `services/time_frame_service.py`: Time frame-related business logic.
- `models/frame.py`: Frame configuration data structure.
- `models/time_frame.py`: Time frame data structure.
- `models/task.py`: Task data structure.
- `models/project.py`: Project data structure (ProjectData).
- `repositories/project_repository.py`: Handles file I/O for projects.
- `repositories/interfaces/repository.py`: Repository interface definition.
- `validators/validators.py`: Data validation logic.
- `utils/conversion.py`: Utility functions for safe type conversion (`safe_int`, `safe_float`).
- `requirements.txt`: Python dependencies.
- `README.md`: This documentation.

## Folders
- `ui/`: User interface modules and utilities.
- `ui/tabs/`: Tab-specific UI implementations.
- `services/`: Business logic and orchestration.
- `models/`: Data structures and serialization.
- `repositories/`: File I/O and persistence logic.
- `validators/`: Data validation logic.
- `utils/`: Utility/helper functions used throughout the codebase.
- `config/`: Application configuration.
- `svg/`: Generated SVG output.
- `docs/`: Documentation and images for README.
- `examples/`: Example project files and demo data.

## Project Architecture

This project follows a layered architecture to ensure maintainability, testability, and clear separation of concerns:

- **UI Layer (`ui/`)**: Handles all user interaction and presentation logic. The UI layer does not contain any business logic or data manipulation; it delegates these responsibilities to the service layer.
- **Service Layer (`services/`)**: Contains all business logic, validation, and orchestration. Services act as intermediaries between the UI and the data model, ensuring that all data manipulation and validation is centralized and consistent.
- **Model Layer (`models/`)**: Defines the core data structures and provides serialization/deserialization methods. Models are pure representations of data and do not contain business logic or file I/O.
- **Repository Layer (`repositories/`)**: Responsible for all file I/O and data persistence. Repositories handle saving and loading data, using the model's serialization methods.

**Development Guideline:**  
All future development should continue to honor this separation.  
- The UI should never contain business logic or direct data manipulation.
- All business rules and data updates should go through the service layer.
- Models should remain focused on data representation.
- File I/O should be handled exclusively by repositories.

This structure makes the codebase easier to maintain, extend, and test as the project evolves.

## Utility Functions

The `utils/` package contains helper functions for use throughout the codebase. For example:

- **`utils/conversion.py`**:  
  - `safe_int(val, default=0)`: Safely convert a value to `int`, returning `default` if conversion fails.
  - `safe_float(val, default=0.0)`: Safely convert a value to `float`, returning `default` if conversion fails.

These are used in the service layer and elsewhere to robustly handle user input and data conversion.