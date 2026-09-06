# Feature Spec: Task Fill Pattern (v2)

> **Status: implemented and shipped in v1.6.1.** This is the original design
> document, kept as a record of intent. It is written in the imperative
> ("Add ...") because it predates the work; nothing here is outstanding.
> The "already implemented" notes refer to the earlier `fill_pattern`-only
> version of the feature, which this spec extended with `pattern_color`.

## Overview
Add `fill_pattern` and `pattern_color` fields to tasks, allowing task bars to be rendered
with a pattern fill. The pattern tile consists of a background rectangle in the task's
fill colour, with pattern lines/dots drawn in the pattern colour. Solid remains the
default. Both fields sit in the task formatting group.

## Valid Pattern Values (`fill_pattern`)
- `solid` (default — current behaviour, no change to rendering)
- `hatch` (diagonal lines, bottom-left to top-right: /)
- `cross-hatch` (diagonal lines both directions: X)
- `horizontal` (horizontal lines)
- `vertical` (vertical lines)
- `dots` (small filled circles)

## Valid Pattern Color Values (`pattern_color`)
- Same set of named colour options as `fill_color` (same dropdown list).
- Default: `"white"`.
- This is the colour of the pattern lines/dots, drawn over the fill colour background.

## Data Model
- `fill_pattern: str = "solid"` — already implemented.
- Add `pattern_color: str = "white"` field to the Task dataclass.
- Both fields are backward-compatible: absent or blank values in Excel default to
  `"solid"` and `"white"` respectively.

## Excel Persistence
- `Fill Pattern` column — already implemented.
- Add `Pattern Color` column to the Tasks worksheet in `excel_repository.py`, alongside
  `Fill Pattern` in the task formatting columns.
- On read: if the column is absent or the cell is blank, default to `"white"`.
- On write: write the string value as-is.

## UI
- `Fill Pattern` dropdown — already implemented.
- Add `Pattern Color` dropdown (QComboBox) to the task formatting panel in
  `tasks_tab.py`, directly below `Fill Pattern`. Use the same colour options as the
  existing `Fill Color` dropdown.
- Behaviour consistent with `Fill Color`: selecting a value updates the task immediately
  via `_sync_data()`.

## SVG Rendering (`gantt_chart_service.py`)
- Each SVG `<pattern>` tile must contain:
  1. A background `<rect>` filling the full tile, filled with the task's `fill_color`.
  2. The pattern lines or dots drawn in `pattern_color`.
- Pattern density constants remain in `ChartConfig` (already implemented):
  `fill_pattern_line_spacing`, `fill_pattern_stroke_width`, `fill_pattern_dot_radius`.
- Generate one pattern def per unique (`fill_pattern`, `fill_color`, `pattern_color`)
  triple actually used in the chart. Pattern ID format:
  `pattern-TYPE-FILLCOLOR-PATCOLOR` e.g. `pattern-hatch-green-white`.
- For `solid`, no pattern def is needed — render as today.
- Apply the pattern fill to the task bar rectangle in place of the solid fill.
- Milestone shapes (circles/diamonds) are unaffected — solid fill only.

## Backward Compatibility
- Existing project files with no `Pattern Color` column must load without error, all
  tasks defaulting to `"white"`.
- Existing project files with no `Fill Pattern` column continue to default to `"solid"`.
- No changes to any other tab or model.

## Slices for Implementation
1. **Model + Excel**: Add `pattern_color` field to Task dataclass and read/write in
   `excel_repository.py`. (`fill_pattern` already done.)
2. **UI**: Add `Pattern Color` dropdown to `tasks_tab.py` formatting panel.
3. **Rendering**: Fix `_add_pattern_defs` in `gantt_chart_service.py` — add background
   rect to each pattern tile, use `pattern_color` for strokes/dots, update pattern ID to
   include pattern color, update `_make_pattern_id` signature accordingly.
