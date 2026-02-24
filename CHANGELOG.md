# Changelog

All notable changes to Compact Gantt will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-02-23

### Changed
- **Excel is now the sole project file format** — JSON project save/load removed.
  File menu simplified to **"Save Project"** (Ctrl+S) and **"Open Project"** (Ctrl+O),
  both operating on `.xlsx` files. Internal `to_json`/`from_json` on `ProjectData` are
  retained for the chart rendering pipeline and are not user-facing.

---

## [1.3.0] - 2026-02-23

### Added
- **Per-swimlane background colour** — set a colour tint on any swimlane via the
  Swimlane Properties detail form; tint renders behind gridlines and task bars.
  Persists in both JSON and Excel (new `Background Color` column in Swimlanes sheet).

### Changed
- **Excel column names aligned to UI labels** — Tasks sheet `Row` → `Chart Row`;
  Swimlanes sheet `Row Count` → `Chart Row Count`. Old names still accepted on import
  for backward compatibility with existing files.

### Fixed
- Blank `fill_color` field on a task no longer produces an invalid SVG `fill=""`
  attribute; falls back to the default blue.
- `label_placement` renderer fallback corrected from `"Outside"` to `"Inside"` to
  match the Task model default.

---

## [1.0.0] - 2025-01-21

### Added
- **Crash Reporting System**
  - User-initiated crash report sending with email integration
  - Automatic crash report generation and local storage
  - Crash report dialog with options to send, view, or copy report
  - Support for both web-based (Gmail) and local email clients
  - Configurable crash report email recipient
  - Crash reports include system information, stack traces, and timestamps

- **ID Badge Display**
  - Toggle to display task and milestone IDs on the chart
  - ID badges appear on the left side of tasks and milestones
  - Configurable badge font size and vertical alignment
  - Badges float above all other chart elements for visibility
  - Control toggle available on Links tab

- **Date Format Preferences**
  - Separate date format settings for data entry UI and chart display
  - Preferences tab renamed from "Windows" to "Preferences"
  - Date format changes apply immediately across all tabs
  - Centralized date parsing in GanttChartService

- **Version Management**
  - Centralized version information in `version.py` (single source of truth)
  - Version badge in README.md synced from version.py
  - Utility script to update README badge automatically

- **Logging System**
  - Centralized logging configuration
  - Log rotation (5MB max, 5 backups)
  - Separate crash report directory
  - Application logs stored in `logs/app.log`

- **Export Enhancements**
  - PNG export with transparent background (ideal for overlays)
  - JPEG export with white opaque background
  - Export confirmation dialogs
  - Status tips on file menu items explaining background options

- **Single Instance Detection**
  - File-based locking to prevent multiple instances
  - Bring existing instance to front when attempting to launch second instance
  - Cross-platform support (Windows, Linux, macOS)

- **Task Management Improvements**
  - Default sorting by ID in links table
  - Improved task ID uniqueness and auto-increment
  - Better handling of multiple row selection and movement

### Changed
- **Tab Organization**
  - Reorganized tabs in content-first logical order:
    Swimlanes → Tasks → Links → Pipes → Curtains → Notes → Layout → Timeline → Titles → Typography → Preferences
  - Preferences tab renamed from "Windows" tab

- **Code Architecture**
  - Refactored rendering methods for better maintainability
  - Extracted common methods and template patterns
  - Migrated to key-based column lookups instead of positional indexing
  - Improved use of dataclasses throughout codebase

- **Date Handling**
  - Centralized date parsing and formatting
  - Separate date configurations for UI and chart display
  - Improved date validation and error handling

- **Error Handling**
  - Improved error messages and user feedback
  - Better validation for data entry fields
  - Enhanced error highlighting in tables

### Fixed
- Fixed link ID uniqueness and incrementing issues
- Fixed date format refresh across all tabs when preferences change
- Fixed pipe label positioning and alignment
- Fixed SVG rendering padding inconsistencies
- Fixed task selection persistence when moving multiple rows
- Fixed missing fields in tasks table
- Fixed column visibility issues across multiple tabs
- Fixed Windows taskbar icon display (custom logo instead of Python logo)
- Fixed import errors in timeline tab

### Security
- Updated dependencies to address security vulnerabilities
- Removed hardcoded credentials and sensitive data

### Documentation
- Comprehensive README.md with features, usage, and architecture
- TESTING_GUIDE.md for manual and automated testing
- Code comments and docstrings improved throughout
- Architecture guidelines for dataclass usage

### Technical
- Centralized logging configuration
- Improved code organization and structure
- Enhanced error handling and logging
- Better separation of concerns
- Removed test/debugging code from production builds

---

## [1.1.0] - 2026-02-02

### Added
- ROADMAP.md for refactor, features, and bugs backlog

### Changed
- Relicensed project under GPL v3 for PyQt compliance (was proprietary)
- LICENSE, COPYRIGHT, and README updated; PyQt5 acknowledgment added

### Fixed
- Valid column now shows 'Yes' for valid tasks (validator compared dates incorrectly: was erroring when finish >= start instead of when finish < start)
- Removed temporary debug logging from Valid column flow (update_tasks, _update_valid_column_only, _update_table_row_from_task)

---

## [1.1.1] - 2026-01-28

### Fixed
- Task tab: when Start or Finish date is changed, the other date field's min/max constraint now updates immediately (fixed row lookup so the correct task row is found)

---

## [1.1.2] - 2026-02-21

### Fixed
- Tasks tab: detail form now looks up the selected task by ID instead of by positional index, so the correct task is always shown after an auto-sort triggered by swimlane changes
- Swimlanes tab: detail form now looks up the selected swimlane by ID instead of by positional index
- Tasks tab: `_move_down` selection restoration was looking up moved tasks via `Name` column `UserRole` (never set); now mirrors `_move_up` and uses the `ID` column text
- Tasks tab: `_on_item_changed` used hardcoded positional column indices (`== 1` for ID, `== 2` for Row) instead of key-based name checks; now uses `col_name`
- Tasks tab: `_on_item_changed` date-fallback guard called `cellWidget` with the logical column index instead of the visible column index; now uses `col`
- Tasks tab: removed dead `_extract_row_data_from_table` (referenced non-existent `self.detail_label`, stale column map) and the already-stubbed `_extract_table_data`; both superseded by `_task_from_table_row`
- Task model: `label_placement` default was `"Outside"` but the UI consistently treats `"Inside"` as the default; corrected in both the dataclass field and `from_dict()` fallback
- Task model: added `Task.to_dict()` so serialisation is co-located with `from_dict()`, matching all other models; the inline block in `project.py` had a bug where `label_horizontal_offset` was only omitted when `!= 1.0` (should be `!= 0.0`, the actual default), which silently dropped offset values of `1.0` on save
- Excel import: `_read_swimlanes_sheet` re-read the header row on every cell iteration (O(rows × cols)); now reads it once before the loop

---

## [1.2.0] - 2026-02-22

### Changed

- **Swimlanes tab — column layout**
  - ID column moved left of Title (standard convention)
  - "Row Count" renamed to "Minimum Row Count" and moved right of Title
  - Lane Order column hidden in UI (retained in Excel)

- **Swimlanes tab — delete with cascade**
  - Deleting a swimlane now shows a confirmation popup listing the swimlane name and number of child tasks before proceeding
  - All child tasks are deleted along with the swimlane (irreversible once confirmed)

- **Swimlanes tab — new swimlane default**
  - A new swimlane is created with one default task so the Add Task workflow is immediately available
  - Minimum Row Count defaults to 1 on creation

- **Tasks tab — swimlane header rows**
  - Swimlane groups are now divided by non-editable, greyed-out, bold header rows displaying the swimlane name
  - Header rows are non-selectable and rendered dynamically from the swimlane list

- **Tasks tab — column changes**
  - "Row" column renamed to "Chart Row" (UI only; Excel schema unchanged)
  - Lane ID column hidden (swimlane membership now visually communicated by header rows; retained in Excel)

- **Tasks tab — Add Task constraints**
  - Add Task button disabled when no task row is selected
  - New task inherits Chart Row, Start Date, and Finish Date from the selected task
  - New task is inserted immediately below the selected task after sort

- **Tasks tab — Move Up / Move Down constraints**
  - Move Up and Move Down buttons disabled when the selected task is already at the top or bottom of its swimlane
  - Tasks cannot be moved past a swimlane header boundary

- **Tasks tab — Duplicate**
  - Duplicated task is inserted immediately below the original after sort
  - All fields inherited including Chart Row and swimlane membership

## [1.2.1] - 2026-02-22

### Changed

- **Swimlanes tab**: "Minimum Row Count" column renamed to "Chart Row Count"
- **Tasks tab**: "Show IDs on chart" checkbox moved from Links tab to Tasks tab toolbar
- **Tasks tab — Move Up / Move Down**: now operate chart-relative with no swimlane boundary constraint; Move Up is blocked only at chart row 1, Move Down has no upper limit

### Fixed

- Tasks tab: Move Up / Move Down buttons now correctly enable when multiple task rows are selected
- Tasks tab: Duplicate task now copies all fields to the new task (fill colour, label settings, date format were previously lost); appends " [Duplicate]" to the duplicated task name

---

## [1.4.1] - 2026-02-24

### Changed
- **Menubars replaced with button toolbars** on both windows.
  - *Chart Data Window:* "Open Project" and "Save Project" buttons appear in a
    strip at the top of the window; "Update Chart" button remains at the bottom.
  - *Chart Display Window:* "Save PNG" and "Save JPEG" export buttons appear at
    the top, clearly separated from the zoom/fit view controls at the bottom.
  - All existing keyboard shortcuts preserved (Ctrl+O, Ctrl+S, Ctrl+Shift+S,
    Ctrl+Shift+J).

---

## [Unreleased]

### Planned
- Additional export formats
- Enhanced chart customization options
- Performance optimizations
- Additional keyboard shortcuts

---

[1.4.1]: https://github.com/richardhaymanjoyce/compact_gantt/releases/tag/v1.4.1
[1.4.0]: https://github.com/richardhaymanjoyce/compact_gantt/releases/tag/v1.4.0
[1.3.0]: https://github.com/richardhaymanjoyce/compact_gantt/releases/tag/v1.3.0
[1.2.1]: https://github.com/richardhaymanjoyce/compact_gantt/releases/tag/v1.2.1
[1.1.2]: https://github.com/richardhaymanjoyce/compact_gantt/releases/tag/v1.1.2
[1.1.1]: https://github.com/richardhaymanjoyce/compact_gantt/releases/tag/v1.1.1
[1.1.0]: https://github.com/richardhaymanjoyce/compact_gantt/releases/tag/v1.1.0
[1.0.0]: https://github.com/richardhaymanjoyce/compact_gantt/releases/tag/v1.0.0
