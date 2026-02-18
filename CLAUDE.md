# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

No build step. Open `index.html` directly in a browser (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+). No server required. All dependencies are CDN-loaded on first open.

There are no tests, no linter, and no package.json.

## Architecture

Single-page application with zero build tooling. All JS files are loaded as classic scripts (not ES modules) in `index.html` — globals are shared across files.

**Script load order matters:** `spreadsheet.js` → `validation.js` → `gantt.js` → `excel.js` → `export.js` → `app.js`. Each file exposes globals consumed by `app.js`.

### Data Flow

```
jSpreadsheet (DOM) → getTasksFromSpreadsheet() → DataValidator.validateAll() → GanttChart.render()
```

1. `spreadsheet.js` — Initializes jSpreadsheet CE and exposes `getTasksFromSpreadsheet()`, `setSpreadsheetData()`. Holds the singleton `spreadsheetInstance`. The `parseCellDate()` function normalizes Date objects, ISO strings, and plain strings to `YYYY-MM-DD`.

2. `validation.js` — `DataValidator` object with `validateAll(tasks)` and `validateTask(task, usedIds)`. Pure logic, no DOM access.

3. `gantt.js` — `GanttChart.render(containerSelector, tasks, options)` uses D3 v7 to render an SVG into `#gantt`. Sorts tasks by `lane` then `row`. Uses `scaleBand` per lane for y-axis, `scaleTime` for x-axis.

4. `app.js` — IIFE controller. Wires button event listeners to the above modules. Calls `validateAndShow()` + `updateChart()` together. On validate, only tasks that pass `DataValidator.validateTask` individually are passed to `GanttChart.render`.

5. `excel.js` — `importExcel(file, callback)` and `exportExcel(tasks, filename)` using SheetJS (`XLSX` global).

6. `export.js` — `exportPNG(containerId, filename)` via html2canvas, `exportSVG(containerId, filename)` via XMLSerializer.

### Task Data Model

```javascript
{ id: Number, name: String, start: "YYYY-MM-DD", end: "YYYY-MM-DD", row: Number, lane: Number }
```

Spreadsheet columns are indexed via `COL` constant in `spreadsheet.js`: `{ID:0, TASK_NAME:1, START_DATE:2, END_DATE:3, ROW:4, LANE:5}`.

### Lane Colors

Lanes 1–8 are styled with CSS classes `.lane-1` through `.lane-8` defined in `css/styles.css`. These classes are applied both to SVG `<rect>` bars in the Gantt and to swimlane background bands.

## Key Constraints

- **No ES modules** — `import`/`export` syntax breaks the app. All new code must use globals or IIFEs.
- **No bundler** — Adding npm packages requires a CDN link in `index.html`.
- **CDN-only dependencies** — jSpreadsheet CE v4, D3 v7, SheetJS xlsx-0.20.0, html2canvas 1.4.1, FileSaver.js 2.0.5, jSuites v4, TailwindCSS.
- The `width` passed to `GanttChart.render` uses `container.clientWidth - 24` when `opts.width` is null — rendering before the container has layout will produce a narrow chart.
