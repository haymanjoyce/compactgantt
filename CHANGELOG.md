# Changelog

All notable changes to Compact Gantt will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [Unreleased]

### Planned
- Additional export formats
- Enhanced chart customization options
- Performance optimizations
- Additional keyboard shortcuts

---

[1.1.1]: https://github.com/richardhaymanjoyce/compact_gantt/releases/tag/v1.1.1
[1.1.0]: https://github.com/richardhaymanjoyce/compact_gantt/releases/tag/v1.1.0
[1.0.0]: https://github.com/richardhaymanjoyce/compact_gantt/releases/tag/v1.0.0
