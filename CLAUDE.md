# Compact Gantt — Claude Code Guide

## Project Overview

PyQt5 desktop application for creating compact Gantt charts. Outputs SVG with PNG/JPEG export. Uses Excel (`.xlsx`) as the project file format.

## Development Setup

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Running Tests

```bash
# Syntax and import validation (no PyQt5 required)
python tests/test_refactor_syntax.py

# Project save/load integration tests
python tests/test_project_save_load.py
```

## Building the Executable

```bash
# Recommended: use build.bat (activates venv automatically)
build.bat

# Manual:
python -m PyInstaller compactgantt.spec
```

Output: `dist/CompactGantt.exe`

## Key Architecture Rules

- **All models are dataclasses** with named fields (`models/task.py`, `models/link.py`, `models/swimlane.py`, `models/pipe.py`, `models/curtain.py`, `models/note.py`). Never use positional lists/arrays for data entities.
- **Excel is the sole project file format** — `.xlsx` via `repositories/excel_repository.py`. JSON serialization exists internally for the rendering pipeline only, not as a user-facing format.
- **Single source of truth for version**: `version.py`. Run `python update_readme_version.py` after bumping the version.
- **Column lookups are key-based**, not positional index based. Use `_get_column_index` / `_get_column_name_from_item` from `ui/tabs/base_tab.py`.

## Project Structure

```
main.py                     # Entry point
version.py                  # App version (single source of truth)
build.bat / compactgantt.spec  # Build tooling

models/                     # Data structures (all dataclasses)
  task.py, link.py, swimlane.py, pipe.py, curtain.py, note.py
  project.py, frame.py

repositories/
  excel_repository.py       # Excel import/export

services/
  gantt_chart_service.py    # SVG chart generation

ui/
  main_window.py            # Main data entry window
  svg_display.py            # Chart preview window
  table_utils.py            # Shared table helpers
  tabs/                     # One file per tab
    base_tab.py             # Shared tab base class
    tasks_tab.py, swimlanes_tab.py, links_tab.py,
    pipes_tab.py, curtains_tab.py, notes_tab.py,
    layout_tab.py, timeline_tab.py, titles_tab.py,
    typography_tab.py, preferences_tab.py

config/app_config.py        # Application configuration
validators/                 # Data validation
utils/                      # Utility functions
tests/                      # Automated tests
```

## Tab Order

Swimlanes → Tasks → Links → Pipes → Curtains → Notes → Layout → Timeline → Titles → Typography → Preferences

## Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| Save Project | Ctrl+S |
| Open Project | Ctrl+O |
| Add Task | Ctrl+N |
| Delete Task(s) | Delete |
| Save PNG (transparent) | Ctrl+Shift+S |
| Save JPEG (opaque) | Ctrl+Shift+J |
| Zoom In | Ctrl++ |
| Zoom Out | Ctrl+- |
| Fit to Window | Ctrl+0 |

## Coding Conventions

- Python 3.8+ compatible
- Use `@dataclass` for all new data entities
- Tab-based UI: each tab is a separate class in `ui/tabs/`
- Logging via centralized config; logs go to `logs/app.log`
- Application uses file-based single-instance locking
