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
# Fast smoke tests — syntax and import validation (no PyQt5 required)
python tests/test_smoke.py

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
- **New row IDs are always `max(existing IDs) + 1`**, defaulting to 1 for an empty table. Never use gap-filling (smallest unused integer) logic. This rule applies to `add_row()` in `ui/table_utils.py` and to any tab method that predicts the next ID ahead of calling `add_row()`.

## Swimlane Row Model (v1.5.0+)

Task rows are **swimlane-relative**, not absolute:

- `task.swimlane_row` — 1-based row index within the task's parent swimlane (stored in Excel as `Swimlane Row`)
- `task.swimlane_id` — ID of the parent swimlane (stored in Excel as `Swimlane ID`)
- **Absolute chart row** is computed at render time only: `swimlane_start_row(task.swimlane_id) + task.swimlane_row - 1`
- `_build_swimlane_start_rows()` in `GanttChartService` builds a `{swimlane_id: start_row}` lookup once per render pass
- **Orphaned tasks** (`swimlane_id` not in any swimlane) are excluded from chart rendering entirely
- **Out-of-range tasks** (`swimlane_row > swimlane.row_count`) are clamped to row 1 of their swimlane at render time
- `DataValidator.validate_task()` accepts an optional `swimlanes` list for swimlane-aware validation (orphaned → error, out-of-range → error)
- **Add Task inherits `swimlane_id`** from the selected task (`_add_task()` in `ui/tabs/tasks_tab.py`). The new task's ID is predicted as `max(t.task_id for t in project_data.tasks) + 1` before calling `add_row()`, and `swimlane_id` is patched directly onto the object in `project_data.tasks` after `add_row()` returns (which already called `_sync_data()` internally).
- **Deleting the last task in a swimlane is blocked** by `_remove_tasks()` in `ui/tabs/tasks_tab.py`. It counts tasks per `swimlane_id` before delegating to `remove_row()`, and shows a blocking message naming the affected swimlane if any would be left empty.

## Links Tab Patterns

- **`_add_link()` bypasses `add_row()`** (`ui/tabs/links_tab.py`). It inserts a blank row directly so it can (a) assign `max(existing IDs) + 1` by scanning all rows via `used_ids` set, and (b) restore the exact pre-insert sort column and direction. Sort restore order: `setSortingEnabled` → `sortByColumn` → `blockSignals(False)` — the unblock must come last so no signals fire during the sort.
- **`_sync_data_impl` write-back is ID-based, not positional.** After extracting links from the table and updating `project_data`, computed fields (task names, valid status) are written back by building a `{link_id: visual_row}` lookup from the current table state, then calling `_update_table_row_from_link(visual_row, link, …)`. Never use `enumerate(links)` as row indices — list position and visual row diverge under any non-default sort.
- **`_sync_data_impl` does not impose a sort.** It must not call `sortItems` or `sortByColumn`. Sort state is managed by `_add_link` and `_load_initial_data_impl` only.

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

Swimlanes → Tasks → Links → Pipes → Curtains → Notes → Layout → Timeline → Titles → Typography → Style → Preferences

## Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| Save Project | Ctrl+S |
| Open Project | Ctrl+O |
| Add Task | Ctrl+N |
| Delete Task(s) | Delete |
| Zoom In | Ctrl++ |
| Zoom Out | Ctrl+- |
| Fit to Window | Ctrl+0 |

## Coding Conventions

- Python 3.8+ compatible
- Use `@dataclass` for all new data entities
- Tab-based UI: each tab is a separate class in `ui/tabs/`
- Logging via centralized config; logs go to `logs/app.log`
- Application uses file-based single-instance locking
