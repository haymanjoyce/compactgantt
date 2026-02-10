# Compact Gantt

A browser-based Gantt chart app. Enter tasks in the spreadsheet, validate, and view the chart. No backend, no build step.

## Quick Start

1. Open [https://haymanjoyce.github.io/compactgantt](https://haymanjoyce.github.io/compactgantt) (or open `index.html` locally).
2. Enter your tasks in the spreadsheet (ID, Task Name, Start Date, End Date, Row, Lane).
3. Click **Validate**, then export to PNG, SVG, or Excel.

**Run locally:** Clone the repo and open `index.html` in a modern browser. No server required.

## Features

- **Spreadsheet** – Excel-like data entry (ID, Task Name, Start Date, End Date, Row, Lane).
- **Validation** – Checks positive/unique IDs, valid dates, end ≥ start, non-empty names.
- **Gantt chart** – D3-rendered SVG with swimlanes and color-coded lanes.
- **Import/Export** – Excel (.xlsx) import and export.
- **Image export** – PNG (transparent) and SVG download.

## Browser support

Chrome 90+, Firefox 88+, Safari 14+, Edge 90+. Requires JavaScript enabled.

## Template

Use **Export Excel** with your data (or empty) to get a file with the correct columns. Re-import with **Import Excel**.

## License

MIT.
