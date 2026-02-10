# Compact Gantt - Complete Specification

## Project Overview
Modern, client-side web application for creating Gantt charts. 100% browser-based, no backend required. Works locally and can be deployed to GitHub Pages for free.

---

## Architecture

### Technology Stack
- **Data Entry**: jSpreadsheet CE (MIT license) - Excel-like spreadsheet in browser
- **Gantt Visualization**: Frappe Gantt (MIT license) - Modern, beautiful charts
- **Excel Import/Export**: SheetJS (Apache 2.0) - Read/write Excel files in browser
- **Image Export**: html2canvas (MIT) - Export to PNG
- **Styling**: TailwindCSS via CDN
- **No build step**: All libraries via CDN, works by opening index.html

### File Structure
```
compactgantt/
├── index.html              # Single-page application
├── css/
│   └── styles.css          # Custom styles
├── js/
│   ├── app.js              # Main application controller
│   ├── spreadsheet.js      # Spreadsheet initialization & handling
│   ├── validation.js       # Data validation logic
│   ├── gantt.js            # Gantt chart rendering
│   ├── excel.js            # Excel import/export
│   └── export.js           # PNG/SVG export
├── examples/
│   └── template.xlsx       # Excel template for users
├── README.md               # Documentation
├── LICENSE                 # MIT License
└── .gitignore
```

---

## Features (MVP - Keep It Simple)

### Core Features
1. **Spreadsheet Data Entry**
   - Columns: ID, Task Name, Start Date, End Date, Row, Lane (Swimlane)
   - Excel-like interface (copy/paste, undo/redo)
   - Date picker for date columns
   - Numeric validation for ID, Row, Lane

2. **Data Validation**
   - Real-time validation as user types
   - Error highlighting in spreadsheet cells
   - Validation panel showing all errors
   - Rules:
     * Task ID must be positive integer
     * Task ID must be unique
     * Start Date must be valid date (YYYY-MM-DD)
     * End Date must be valid date (YYYY-MM-DD)
     * End Date must be >= Start Date
     * Row must be positive integer
     * Lane must be positive integer
     * Task Name cannot be empty

3. **Gantt Chart Visualization**
   - Visual timeline of all tasks
   - Grouped by swimlanes
   - Color-coded by lane
   - Interactive (hover to see task details)
   - Auto-scales to fit date range
   - Swimlane dividers

4. **Excel Import/Export**
   - Import: Upload .xlsx file to populate spreadsheet
   - Export: Download current data as .xlsx
   - Template file provided for users

5. **Image Export**
   - Export to PNG (transparent or white background)
   - Export to SVG (vector, scalable): implement via Frappe Gantt's SVG output if available, or by serializing the chart's SVG element and triggering download
   - Download directly from browser

### UI Layout
```
┌─────────────────────────────────────────────────────┐
│  Header: "Compact Gantt" + Controls                 │
│  [Import Excel] [Export Excel] [Validate] [Export]  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Spreadsheet (jSpreadsheet)                         │
│  Add/Delete rows, edit cells                        │
│                                                      │
├─────────────────────────────────────────────────────┤
│  Validation Panel (collapsible)                     │
│  ✓ No errors found / ⚠ 3 errors found               │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Gantt Chart (Frappe Gantt)                         │
│  Visual timeline                                    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Data Model

### Task Object
```javascript
{
  id: 1,                    // Unique positive integer
  name: "Task Name",        // Non-empty string
  start: "2026-02-01",      // Date in YYYY-MM-DD format
  end: "2026-02-15",        // Date in YYYY-MM-DD format, >= start
  row: 1,                   // Positive integer for ordering
  lane: 1                   // Positive integer for swimlane grouping
}
```

### Spreadsheet Columns
| Column | Type | Validation | Description |
|--------|------|------------|-------------|
| ID | Number | Positive, Unique | Task identifier |
| Task Name | Text | Non-empty | Task description |
| Start Date | Date | Valid date | Task start (YYYY-MM-DD) |
| End Date | Date | Valid date, >= Start | Task end (YYYY-MM-DD) |
| Row | Number | Positive | Display order within lane |
| Lane | Number | Positive | Swimlane assignment |

---

## Validation Rules (Ported from Python)

```javascript
// From validators/validators.py in compact_gantt

class DataValidator {
  
  // Validate single task
  static validateTask(task, usedIds) {
    const errors = [];
    
    // ID validation
    if (!task.id || task.id <= 0) {
      errors.push("Task ID must be positive");
    }
    if (usedIds.has(task.id)) {
      errors.push("Task ID must be unique");
    }
    
    // Name validation
    if (!task.name || task.name.trim() === "") {
      errors.push("Task name cannot be empty");
    }
    
    // Date validation
    if (!this.isValidDate(task.start)) {
      errors.push("Invalid start date format (should be YYYY-MM-DD)");
    }
    if (!this.isValidDate(task.end)) {
      errors.push("Invalid end date format (should be YYYY-MM-DD)");
    }
    
    // Date comparison
    if (this.isValidDate(task.start) && this.isValidDate(task.end)) {
      if (new Date(task.end) < new Date(task.start)) {
        errors.push("End date must be on or after start date");
      }
    }
    
    // Row validation
    if (!task.row || task.row <= 0) {
      errors.push("Row number must be positive");
    }
    
    // Lane validation
    if (!task.lane || task.lane <= 0) {
      errors.push("Lane number must be positive");
    }
    
    return errors;
  }
  
  // Validate all tasks
  static validateAll(tasks) {
    const usedIds = new Set();
    const results = [];
    
    tasks.forEach((task, index) => {
      const errors = this.validateTask(task, usedIds);
      if (errors.length > 0) {
        results.push({ index, task, errors });
      }
      usedIds.add(task.id);
    });
    
    return results;
  }
  
  // Helper: Check if valid YYYY-MM-DD date
  static isValidDate(dateString) {
    if (!dateString) return false;
    const regex = /^\d{4}-\d{2}-\d{2}$/;
    if (!regex.test(dateString)) return false;
    const date = new Date(dateString);
    return date instanceof Date && !isNaN(date);
  }
}
```

---

## User Workflows

### Workflow 1: Create New Chart
1. Open index.html in browser
2. Enter tasks in spreadsheet
3. Click "Validate" to check for errors
4. View Gantt chart (auto-updates)
5. Export to Excel or PNG/SVG

### Workflow 2: Import from Excel
1. Click "Import Excel"
2. Select .xlsx file
3. Data populates spreadsheet
4. Validation runs automatically
5. Fix any errors highlighted
6. View/export chart

### Workflow 3: Export
1. **Excel**: Click "Export Excel" → download .xlsx
2. **PNG**: Click "Export" → "PNG" → download image
3. **SVG**: Click "Export" → "SVG" → download vector

---

## Implementation Details

### Data Flow
- **Spreadsheet → app data**: Use jSpreadsheet's get-data API (see [jSpreadsheet CE docs](https://jspreadsheet.com/)) to read all rows, then map columns to task fields (ID, Task Name, Start Date, End Date, Row, Lane) for validation and Gantt.

### jSpreadsheet Configuration
```javascript
jspreadsheet(document.getElementById('spreadsheet'), {
    data: [[]],  // Start empty
    columns: [
        { 
            title: 'ID', 
            type: 'numeric', 
            width: 60 
        },
        { 
            title: 'Task Name', 
            type: 'text', 
            width: 250 
        },
        { 
            title: 'Start Date', 
            type: 'calendar', 
            width: 120,
            options: { format: 'YYYY-MM-DD' }
        },
        { 
            title: 'End Date', 
            type: 'calendar', 
            width: 120,
            options: { format: 'YYYY-MM-DD' }
        },
        { 
            title: 'Row', 
            type: 'numeric', 
            width: 60 
        },
        { 
            title: 'Lane', 
            type: 'numeric', 
            width: 60 
        }
    ],
    minDimensions: [6, 10],  // Min columns and rows
    allowInsertRow: true,
    allowManualInsertRow: true,
    allowDeleteRow: true,
    allowRenameColumn: false
});
```

### Frappe Gantt Configuration
- **Sort order**: Sort tasks by `lane` then `row` before passing to the Gantt so swimlanes and order within lane display correctly.

```javascript
// Sort by lane, then row
tasks.sort((a, b) => (a.lane - b.lane) || (a.row - b.row));

// Generate Gantt tasks
const ganttTasks = tasks.map(task => ({
    id: `task-${task.id}`,
    name: task.name,
    start: task.start,
    end: task.end,
    progress: 0,
    custom_class: `lane-${task.lane}`
}));

// Render
const gantt = new Gantt("#gantt", ganttTasks, {
    view_mode: 'Day',
    bar_height: 30,
    bar_corner_radius: 3,
    arrow_curve: 5,
    padding: 18,
    date_format: 'YYYY-MM-DD'
});
```

### Excel Import (SheetJS)
```javascript
function importExcel(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        const json = XLSX.utils.sheet_to_json(firstSheet);
        
        // Populate spreadsheet
        populateSpreadsheet(json);
        
        // Validate
        validateData();
    };
    reader.readAsArrayBuffer(file);
}
```

### PNG Export (html2canvas)
```javascript
function exportPNG() {
    const ganttElement = document.getElementById('gantt');
    html2canvas(ganttElement, {
        backgroundColor: null,  // Transparent
        scale: 2  // High quality
    }).then(canvas => {
        canvas.toBlob(blob => {
            saveAs(blob, 'gantt-chart.png');
        });
    });
}
```

---

## Styling Guidelines

### Color Palette
```css
:root {
    --primary: #3b82f6;      /* Blue for actions */
    --success: #10b981;      /* Green for valid */
    --error: #ef4444;        /* Red for errors */
    --warning: #f59e0b;      /* Orange for warnings */
    --gray-50: #f9fafb;
    --gray-100: #f3f4f6;
    --gray-600: #4b5563;
    --gray-900: #111827;
}
```

### Lane Colors (Swimlanes)
```css
.lane-1 { background-color: #93c5fd; }  /* Light blue */
.lane-2 { background-color: #86efac; }  /* Light green */
.lane-3 { background-color: #fde68a; }  /* Light yellow */
.lane-4 { background-color: #fca5a5; }  /* Light red */
.lane-5 { background-color: #c4b5fd; }  /* Light purple */
/* Repeat or generate more as needed */
```

### Responsive Design
- Desktop: Full layout with spreadsheet + chart side by side
- Tablet: Stacked layout
- Mobile: Scrollable, focus on one section at a time

---

## Deployment

### Local Use
1. Clone repository
2. Open `index.html` in any modern browser
3. No server needed - works offline after initial load

### Web Deployment (GitHub Pages)
1. Go to repository Settings → Pages
2. Source: Deploy from `main` branch
3. Access at: `https://haymanjoyce.github.io/compactgantt`
4. Updates automatically on push to main

### Alternative Hosting
- Netlify: Drag & drop folder
- Vercel: Connect GitHub repo
- Cloudflare Pages: Connect GitHub repo
- All free for static sites

---

## Browser Support

### Minimum Requirements
- Chrome 90+ ✅
- Firefox 88+ ✅
- Safari 14+ ✅
- Edge 90+ ✅

### Not Supported
- Internet Explorer (any version) ❌
- Very old mobile browsers ❌

### Required Features
- ES6 JavaScript
- Canvas API (for PNG export)
- FileReader API (for Excel import)
- LocalStorage (for future features)

---

## Dependencies (All via CDN)

```html
<!-- jSpreadsheet -->
<script src="https://cdn.jsdelivr.net/npm/jspreadsheet-ce@4/dist/index.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/jspreadsheet-ce@4/dist/jspreadsheet.min.css">

<!-- jSuites (required by jSpreadsheet) -->
<script src="https://cdn.jsdelivr.net/npm/jsuites@4/dist/jsuites.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/jsuites@4/dist/jsuites.min.css">

<!-- Frappe Gantt -->
<script src="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/frappe-gantt@0.6.1/dist/frappe-gantt.min.css">

<!-- SheetJS -->
<script src="https://cdn.sheetjs.com/xlsx-0.20.0/package/dist/xlsx.full.min.js"></script>

<!-- html2canvas -->
<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>

<!-- FileSaver.js -->
<script src="https://cdn.jsdelivr.net/npm/file-saver@2.0.5/dist/FileSaver.min.js"></script>

<!-- TailwindCSS -->
<script src="https://cdn.tailwindcss.com"></script>
```

**Total Bundle Size**: ~800KB (first load only, then cached)

---

## Future Enhancements (Not in MVP)

### Phase 2
- Task dependencies (arrows showing links)
- Milestone markers (pipes)
- Date range highlights (curtains)
- Text annotations (notes)

### Phase 3
- Theme customization (colors, fonts)
- Chart customization (gridlines, margins)
- Multiple views (day/week/month)
- Print optimization

### Phase 4
- LocalStorage for auto-save
- Multiple projects
- Collaboration features (if backend added later)
- API for integrations

---

## Success Metrics

### MVP Success Criteria
1. ✅ User can create Gantt chart in < 2 minutes
2. ✅ Works offline (after first load)
3. ✅ Zero server costs
4. ✅ Validation catches all errors from old Python app
5. ✅ Exports match quality of old app
6. ✅ No installation required

### Performance Targets
- Initial page load: < 2 seconds
- Spreadsheet interaction: < 50ms response
- Chart render: < 500ms for 100 tasks
- Excel import: < 1 second for 1000 rows
- PNG export: < 2 seconds

---

## Testing Strategy

### Manual Testing Checklist
- [ ] Create tasks manually
- [ ] Import Excel file
- [ ] Validation catches all error types
- [ ] Gantt renders correctly
- [ ] Swimlanes display properly
- [ ] Export Excel works
- [ ] Export PNG works
- [ ] Export SVG works
- [ ] Works in Chrome, Firefox, Safari
- [ ] Works on mobile (basic functionality)

### Test Data
Create example.xlsx with:
- Valid tasks
- Invalid tasks (for testing validation)
- Multiple swimlanes
- Date range spanning months

---

## Documentation (README.md)

### Include
1. Screenshot of app
2. Quick start (3 steps max)
3. Feature list
4. Excel template download link
5. Browser requirements
6. How to deploy to GitHub Pages
7. License
8. Contributing guidelines

### Example Quick Start
```markdown
## Quick Start

1. Open https://haymanjoyce.github.io/compactgantt
2. Enter your tasks in the spreadsheet
3. Export to PNG or Excel

**Or run locally**: Just download and open `index.html`
```

---

## License

MIT License (permissive, allows commercial use)

---

## Git Ignore

```
.DS_Store
Thumbs.db
*.swp
*.swo
*~
.vscode/
.idea/
node_modules/
```

---

## Summary

This is a **complete rewrite** as a modern web application:
- ❌ No Python
- ❌ No PyQt5  
- ❌ No backend
- ❌ No build process
- ✅ 100% browser-based
- ✅ Works locally AND on web
- ✅ Free to host
- ✅ Simple, focused feature set
- ✅ Maintains validation logic from original
- ✅ Better looking charts
- ✅ Easier to use

**Total Development Effort**: ~8-12 hours for MVP

---

END OF SPECIFICATION

