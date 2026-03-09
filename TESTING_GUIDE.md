# Compact Gantt - Testing Guide

## 🧪 Automated Testing

### 1. Syntax and Import Tests
Run validation tests (no PyQt5 required):
```bash
python tests/test_smoke.py
```

This will test:
- Python syntax validation for all modules
- Import validation
- DateConfig functionality
- BaseTab method availability

### 2. Project Save/Load Tests
Test Excel project data persistence:
```bash
python tests/test_project_save_load.py
```

## 🖱️ Manual Testing Checklist

### Application Startup
- [ ] Application launches without errors
- [ ] Main data entry window appears
- [ ] SVG display window appears (or opens when needed)
- [ ] Window positioning works correctly
- [ ] Logo appears in window title bar

### File Menu Operations
- [ ] **Save Project (Ctrl+S)**
  - [ ] Opens file dialog
  - [ ] Saves project data to Excel (.xlsx) file
  - [ ] Shows success message

- [ ] **Open Project (Ctrl+O)**
  - [ ] Opens file dialog
  - [ ] Loads project data from Excel (.xlsx) file
  - [ ] Updates all tabs with loaded data
  - [ ] Shows success message

### Tab Navigation
- [ ] All tabs are accessible and clickable
- [ ] Tab order is correct: Swimlanes → Tasks → Links → Pipes → Curtains → Notes → Layout → Timeline → Titles → Typography → Preferences

### Preferences Tab
- [ ] **Data Entry Window Settings**
  - [ ] Screen selection works
  - [ ] X/Y position coordinates work
  - [ ] Changes apply immediately to data entry window
  - [ ] Date format selection works

- [ ] **SVG Display Window Settings**
  - [ ] Screen selection works
  - [ ] X/Y position coordinates work
  - [ ] Changes apply immediately to SVG display window
  - [ ] Date format selection works

### Layout Tab
- [ ] **Chart Dimensions**
  - [ ] Width field accepts numeric input
  - [ ] Height field accepts numeric input
  - [ ] Validation works for invalid inputs

- [ ] **Margins**
  - [ ] All margin fields (left, right, top, bottom) work
  - [ ] Validation works for negative values

- [ ] **Grid Settings**
  - [ ] Grid enabled checkbox works
  - [ ] Grid color picker works
  - [ ] Grid line width field works

- [ ] **Start Date**
  - [ ] Date picker opens correctly
  - [ ] Selected date is saved

### Titles Tab (New Combined Tab)
- [ ] **Header Settings Group**
  - [ ] Header Height field works and validates
  - [ ] Header Text field works
  - [ ] Tooltips display correctly

- [ ] **Footer Settings Group**
  - [ ] Footer Height field works and validates
  - [ ] Footer Text field works
  - [ ] Tooltips display correctly

- [ ] **Data Persistence**
  - [ ] Changes are saved to project data
  - [ ] Data is restored when loading projects

### Scales Tab
- [ ] **Scale Settings**
  - [ ] All scale checkboxes work (years, months, weeks, days)
  - [ ] Scale color pickers work
  - [ ] Scale line width fields work

### Grid Tab
- [ ] **Grid Settings**
  - [ ] Grid enabled checkbox works
  - [ ] Grid color picker works
  - [ ] Grid line width field works

### Time Frames Tab
- [ ] **Table Operations**
  - [ ] Add row button works
  - [ ] Remove row button works
  - [ ] Table is sortable by clicking headers

- [ ] **Data Entry**
  - [ ] Time Frame ID auto-generates correctly
  - [ ] Finish date picker works
  - [ ] Width percentage field works and validates
  - [ ] Invalid data shows visual feedback

- [ ] **Data Validation**
  - [ ] Empty required fields show errors
  - [ ] Invalid dates show errors
  - [ ] Invalid percentages show errors

### Tasks Tab
- [ ] **Table Operations**
  - [ ] Add row button works
  - [ ] Remove row button works
  - [ ] Table is sortable

- [ ] **Data Entry**
  - [ ] Task ID auto-generates correctly
  - [ ] Task order field works
  - [ ] Task name field works
  - [ ] Start date picker works
  - [ ] Finish date picker works
  - [ ] Row number field works
  - [ ] All label options work (placement, alignment, offsets, colors)

- [ ] **Data Validation**
  - [ ] Date validation works (finish after start)
  - [ ] Required field validation works
  - [ ] Numeric field validation works

### SVG Generation
- [ ] **Update Image Button**
  - [ ] Button is clickable
  - [ ] Generates SVG when clicked
  - [ ] SVG display window shows the generated chart
  - [ ] Chart displays correctly with all entered data

- [ ] **Chart Content**
  - [ ] Header text appears correctly
  - [ ] Footer text appears correctly
  - [ ] Time frames display with correct proportions
  - [ ] Tasks display in correct positions
  - [ ] Scales display correctly
  - [ ] Grid lines appear (if enabled)

### Error Handling
- [ ] **Invalid Data**
  - [ ] Application doesn't crash with invalid input
  - [ ] Error messages are displayed appropriately
  - [ ] Invalid fields are highlighted

- [ ] **File Operations**
  - [ ] Error handling for file save/load failures
  - [ ] Appropriate error messages for file issues

### Performance
- [ ] **Responsiveness**
  - [ ] UI remains responsive during operations
  - [ ] Large datasets don't cause freezing
  - [ ] SVG generation is reasonably fast

- [ ] **Memory Usage**
  - [ ] No memory leaks during extended use
  - [ ] Application can handle multiple operations

## 🐛 Common Issues to Check

### Visual Issues
- [ ] All UI elements are properly aligned
- [ ] Text is readable and not cut off
- [ ] Colors are appropriate and accessible
- [ ] Windows resize correctly

### Data Issues
- [ ] Data persists between tab switches
- [ ] Data is correctly saved and loaded
- [ ] Auto-generated IDs are unique
- [ ] Date calculations are accurate

### Integration Issues
- [ ] All tabs work together correctly
- [ ] Changes in one tab affect others appropriately
- [ ] SVG generation uses all tab data correctly

## 📝 Test Data Suggestions

### Basic Test Project
```
Layout:
- Width: 800, Height: 600
- Margins: 20, 20, 20, 20
- Start Date: 2025-01-01

Titles:
- Header: "Project Timeline"
- Footer: "Generated by Compact Gantt"

Time Frames:
- TF1: 2025-01-15, 30%
- TF2: 2025-02-15, 40%
- TF3: 2025-03-15, 30%

Tasks:
- Task1: "Planning", 2025-01-01 to 2025-01-10, Row 1
- Task2: "Development", 2025-01-11 to 2025-02-20, Row 2
- Task3: "Testing", 2025-02-21 to 2025-03-10, Row 3
```

### Edge Cases to Test
- [ ] Empty project (no time frames or tasks)
- [ ] Single time frame with multiple tasks
- [ ] Tasks spanning multiple time frames
- [ ] Very long task names
- [ ] Very short time periods
- [ ] Very large numbers in dimensions

## 🚀 Running the Tests

1. **Start with automated tests:**
   ```bash
   python tests/test_smoke.py
   python tests/test_project_save_load.py
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```

3. **Follow the manual testing checklist above**

4. **Document any issues found**

## 📊 Test Results Template

```
Test Date: _______________
Tester: _________________

✅ Passed Tests:
- [List passed tests]

❌ Failed Tests:
- [List failed tests with details]

🐛 Bugs Found:
- [List bugs with steps to reproduce]

💡 Suggestions:
- [List improvement suggestions]

Overall Status: [PASS/FAIL]
```

## 🔧 Troubleshooting

### Common Problems
1. **Import errors**: Check that all dependencies are installed
2. **GUI not appearing**: Check PyQt5 installation
3. **SVG not generating**: Check that all required data is entered
4. **Window positioning issues**: Check screen configuration

### Getting Help
- Check the logs in the `logs/` directory
- Review error messages in the console
- Verify file permissions for save/load operations 