from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton,
                           QHBoxLayout, QComboBox, QHeaderView, QTableWidgetItem,
                           QMessageBox, QGroupBox, QSizePolicy, QLabel, QGridLayout, QLineEdit, QSpinBox, QDateEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QBrush, QColor, QFont
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
import logging
from utils.conversion import normalize_display_date, safe_int, display_to_internal_date, internal_to_display_date, parse_internal_date
from models import Task
from config.date_config import DATE_FORMAT_OPTIONS

from ui.table_utils import NumericTableWidgetItem, DateTableWidgetItem, DateEditWidget, add_row, remove_row, CheckBoxWidget, highlight_table_errors, extract_table_data
from .base_tab import BaseTab

# Logging is configured centrally in utils/logging_config.py

# Custom data role for marking swimlane header rows
SWIMLANE_HEADER_ROLE = Qt.UserRole + 101

class TasksTab(BaseTab):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        self.table_config = app_config.get_table_config("tasks")
        self._selected_row = None  # Track currently selected row
        self._selected_task_id = None  # Track selected task ID for detail form matching
        self._updating_form = False  # Prevent circular updates
        self._syncing = False  # Prevent recursive syncs
        self._detail_form_widgets = []  # Will be populated in _create_detail_form
        super().__init__(project_data, app_config)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create toolbar with buttons
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        
        self.add_btn = QPushButton("Add Task")
        self.add_btn.setToolTip("Add a new task to the chart (Ctrl+N)")
        self.add_btn.setMinimumWidth(100)
        self.add_btn.setEnabled(False)  # Disabled until a task row is selected
        self.add_btn.clicked.connect(self._add_task)
        
        remove_btn = QPushButton("Remove Task")
        remove_btn.setToolTip("Remove selected task(s) from the chart (Delete)")
        remove_btn.setMinimumWidth(100)
        remove_btn.clicked.connect(lambda: remove_row(self.tasks_table, "tasks", 
                                                    self.app_config.tables, self))
        
        duplicate_btn = QPushButton("Duplicate Task")
        duplicate_btn.setToolTip("Duplicate selected task(s) with new IDs")
        duplicate_btn.setMinimumWidth(100)
        duplicate_btn.clicked.connect(self._duplicate_tasks)
        
        self.move_up_btn = QPushButton("Move Up")
        self.move_up_btn.setToolTip("Move selected task up by one chart row")
        self.move_up_btn.setMinimumWidth(100)
        self.move_up_btn.setEnabled(False)  # Disabled until a task at a movable position is selected
        self.move_up_btn.clicked.connect(self._move_up)

        self.move_down_btn = QPushButton("Move Down")
        self.move_down_btn.setToolTip("Move selected task down by one chart row")
        self.move_down_btn.setMinimumWidth(100)
        self.move_down_btn.setEnabled(False)  # Disabled until a task at a movable position is selected
        self.move_down_btn.clicked.connect(self._move_down)

        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addWidget(duplicate_btn)
        toolbar.addWidget(self.move_up_btn)
        toolbar.addWidget(self.move_down_btn)
        toolbar.addStretch()  # Push buttons to the left
        
        # Create group box for table
        table_group = QGroupBox("Tasks")
        table_group_layout = QVBoxLayout()
        table_group_layout.setSpacing(5)
        table_group_layout.setContentsMargins(5, 10, 5, 5)
        
        # Create table - show: Lane, ID, Row, Name, Start Date, Finish Date, Valid
        headers = [col.name for col in self.table_config.columns]
        visible_columns = ["ID", "Chart Row", "Name", "Start Date", "Finish Date", "Valid"]
        visible_indices = [headers.index(col) for col in visible_columns if col in headers]
        
        self.tasks_table = QTableWidget(0, len(visible_indices))
        visible_headers = [headers[i] for i in visible_indices]
        self.tasks_table.setHorizontalHeaderLabels(visible_headers)
        
        # Store mapping of visible column index to actual column index
        self._column_mapping = {vis_idx: actual_idx for vis_idx, actual_idx in enumerate(visible_indices)}
        self._reverse_column_mapping = {actual_idx: vis_idx for vis_idx, actual_idx in enumerate(visible_indices)}
        
        # Enhanced table styling
        self.tasks_table.setAlternatingRowColors(False)  # Disabled to avoid conflict with read-only cell backgrounds
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tasks_table.setSelectionMode(QTableWidget.ExtendedSelection)  # Extended selection for bulk operations, detail form shows first selected
        self.tasks_table.setShowGrid(True)
        self.tasks_table.verticalHeader().setVisible(False)
        
        # Add bottom border to header row and gridline styling
        self.tasks_table.setStyleSheet(self.app_config.general.table_stylesheet)

        # Column sizing - use key-based lookups instead of positional indices
        header = self.tasks_table.horizontalHeader()
        
        # Find columns by name and set their sizing
        lane_col = None
        id_col = None
        row_col = None
        name_col = None
        start_date_col = None
        finish_date_col = None
        valid_col = None
        
        for i in range(self.tasks_table.columnCount()):
            header_text = self.tasks_table.horizontalHeaderItem(i).text()
            if header_text == "Lane":
                lane_col = i
            elif header_text == "ID":
                id_col = i
            elif header_text == "Chart Row":
                row_col = i
            elif header_text == "Name":
                name_col = i
            elif header_text == "Start Date":
                start_date_col = i
            elif header_text == "Finish Date":
                finish_date_col = i
            elif header_text == "Valid":
                valid_col = i
        
        if lane_col is not None:
            header.setSectionResizeMode(lane_col, QHeaderView.Fixed)
            self.tasks_table.setColumnWidth(lane_col, 60)
        if id_col is not None:
            header.setSectionResizeMode(id_col, QHeaderView.Fixed)
            self.tasks_table.setColumnWidth(id_col, 50)
        if row_col is not None:
            header.setSectionResizeMode(row_col, QHeaderView.Fixed)
            self.tasks_table.setColumnWidth(row_col, 50)
        if name_col is not None:
            header.setSectionResizeMode(name_col, QHeaderView.Stretch)
        if start_date_col is not None:
            header.setSectionResizeMode(start_date_col, QHeaderView.ResizeToContents)
        if finish_date_col is not None:
            header.setSectionResizeMode(finish_date_col, QHeaderView.ResizeToContents)
        if valid_col is not None:
            header.setSectionResizeMode(valid_col, QHeaderView.ResizeToContents)

        # Enable horizontal scroll bar
        self.tasks_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tasks_table.setSortingEnabled(False)  # Disable user sorting - automatic sort by Lane, Row, Finish Date
        
        # Set table size policy
        self.tasks_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        table_group_layout.addLayout(toolbar)
        table_group_layout.addWidget(self.tasks_table)
        table_group.setLayout(table_group_layout)
        
        # Add table group with stretch factor so it expands to fill available space
        layout.addWidget(table_group, 1)  # Stretch factor of 1 makes it expand
        
        # Create detail form group box
        detail_group = self._create_detail_form()
        layout.addWidget(detail_group)  # No stretch factor - stays at natural size
        
        # Removed addStretch() - we want the table to expand, not push everything to top

        self.setLayout(layout)

    def _create_detail_form(self) -> QGroupBox:
        """Create the detail form for editing formatting-related fields."""
        group = QGroupBox("Task Formatting")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        LABEL_WIDTH = 120
        
        # Label Content
        label_label = QLabel("Label Content:")
        label_label.setFixedWidth(LABEL_WIDTH)
        self.detail_label_content = QComboBox()
        self.detail_label_content.addItems(["None", "Name only", "Date only", "Name and Date"])
        self.detail_label_content.setToolTip("What to display in the task label")
        self.detail_label_content.currentTextChanged.connect(self._on_detail_form_changed)
        self.detail_label_content.setEnabled(False)
        
        # Label Placement
        placement_label = QLabel("Label Placement:")
        placement_label.setFixedWidth(LABEL_WIDTH)
        self.detail_placement = QComboBox()
        self.detail_placement.addItems(["Inside", "Outside"])
        self.detail_placement.setToolTip("Label placement (Inside or Outside task bar)")
        self.detail_placement.currentTextChanged.connect(self._on_detail_form_changed)
        self.detail_placement.setEnabled(False)
        
        # Label Offset
        offset_label = QLabel("Label Offset:")
        offset_label.setFixedWidth(LABEL_WIDTH)
        self.detail_offset = QSpinBox()
        self.detail_offset.setMinimum(0)
        self.detail_offset.setMaximum(300)
        self.detail_offset.setValue(0)
        self.detail_offset.setSuffix(" px")
        self.detail_offset.setToolTip("Additional horizontal offset for outside labels in pixels. Leader line appears when offset > 0.")
        self.detail_offset.valueChanged.connect(self._on_detail_form_changed)
        self.detail_offset.setEnabled(False)
        
        # Fill Color
        color_label = QLabel("Fill Color:")
        color_label.setFixedWidth(LABEL_WIDTH)
        self.detail_fill_color = QComboBox()
        self.detail_fill_color.addItems(["blue", "red", "green", "yellow", "orange", "purple", "gray", "black", "white", "cyan", "magenta", "brown"])
        self.detail_fill_color.setToolTip("Fill color for task bar or milestone circle")
        self.detail_fill_color.currentTextChanged.connect(self._on_detail_form_changed)
        self.detail_fill_color.setEnabled(False)
        
        # Date Format
        date_format_label = QLabel("Date Format:")
        date_format_label.setFixedWidth(LABEL_WIDTH)
        self.detail_date_format = QComboBox()
        self.detail_date_format.setEditable(True)  # Allow custom formats
        # Add "Use Global" as first option (None), then all available formats
        self.detail_date_format.addItem("Use Global")
        for format_name in DATE_FORMAT_OPTIONS.keys():
            self.detail_date_format.addItem(format_name)
        self.detail_date_format.setToolTip("Date format for this task's labels. 'Use Global' uses the chart's default date format. You can also enter a custom Qt format (e.g., 'M', 'MMM', 'dd MMM yyyy').")
        self.detail_date_format.currentTextChanged.connect(self._on_detail_form_changed)
        self.detail_date_format.setEnabled(False)
        
        # Store list of detail form widgets for easy enable/disable
        self._detail_form_widgets = [self.detail_label_content, self.detail_placement, self.detail_offset, self.detail_fill_color, self.detail_date_format]
        
        # Layout form fields vertically (like titles tab)
        layout.addWidget(label_label, 0, 0)
        layout.addWidget(self.detail_label_content, 0, 1)
        layout.addWidget(placement_label, 1, 0)
        layout.addWidget(self.detail_placement, 1, 1)
        layout.addWidget(offset_label, 2, 0)
        layout.addWidget(self.detail_offset, 2, 1)
        layout.addWidget(color_label, 3, 0)
        layout.addWidget(self.detail_fill_color, 3, 1)
        layout.addWidget(date_format_label, 4, 0)
        layout.addWidget(self.detail_date_format, 4, 1)
        
        layout.setColumnStretch(1, 1)
        
        group.setLayout(layout)
        return group

    def _on_table_selection_changed(self):
        """Handle table selection changes - populate detail form."""
        selected_rows = self.tasks_table.selectionModel().selectedRows()

        # Enable Add Task only when exactly one non-header task row is selected
        add_enabled = (
            len(selected_rows) == 1
            and not self._is_header_row(selected_rows[0].row())
        )
        if hasattr(self, 'add_btn'):
            self.add_btn.setEnabled(add_enabled)

        # Update Move Up / Move Down button states based on chart row position
        if hasattr(self, 'move_up_btn') and hasattr(self, 'move_down_btn'):
            task_rows = [r for r in selected_rows if not self._is_header_row(r.row())]
            if task_rows:
                tasks = [self._task_from_table_row(r.row()) for r in task_rows]
                tasks = [t for t in tasks if t is not None]
                self.move_up_btn.setEnabled(any(t.row_number > 1 for t in tasks))
                self.move_down_btn.setEnabled(bool(tasks))
            else:
                self.move_up_btn.setEnabled(False)
                self.move_down_btn.setEnabled(False)

        if not selected_rows:
            self._selected_row = None
            self._selected_task_id = None
            self._clear_detail_form()
            return

        # Show detail form only when exactly one row is selected
        if len(selected_rows) == 1:
            row = selected_rows[0].row()
            self._selected_row = row

            # Track the task ID for this row (using key-based access)
            id_col = self._get_column_index("ID")
            if id_col is not None:
                id_item = self.tasks_table.item(row, id_col)
                if id_item:
                    self._selected_task_id = safe_int(id_item.text())
                else:
                    self._selected_task_id = None
            else:
                self._selected_task_id = None

            self._populate_detail_form(row)
        else:
            # Multiple rows selected - clear detail form
            self._selected_row = None
            self._selected_task_id = None
            self._clear_detail_form()

    def _populate_detail_form(self, row: int):
        """Populate detail form with data from selected task."""
        self._updating_form = True

        try:
            # Look up task by task_id from the ID column rather than by positional
            # index, since the table display order may differ from project_data.tasks.
            task = None
            id_col = self._get_column_index("ID")
            if id_col is not None:
                id_item = self.tasks_table.item(row, id_col)
                if id_item:
                    try:
                        task_id = int(id_item.text())
                        task = next((t for t in self.project_data.tasks if t.task_id == task_id), None)
                    except (ValueError, TypeError):
                        pass

            if task is not None:
                self.detail_label_content.setCurrentText(task.label_content if task.label_content else "Name only")
                self.detail_placement.setCurrentText(task.label_placement if task.label_placement else "Inside")
                self.detail_offset.setValue(int(task.label_horizontal_offset) if task.label_horizontal_offset is not None else 0)
                self.detail_fill_color.setCurrentText(task.fill_color if task.fill_color else "blue")
                # Set date format: "Use Global" if None, otherwise the format name
                if task.date_format:
                    self.detail_date_format.setCurrentText(task.date_format)
                else:
                    self.detail_date_format.setCurrentText("Use Global")
                # Enable detail form widgets when a valid task is selected
                self._set_detail_form_enabled(self._detail_form_widgets, True)
            else:
                # Use defaults if task cannot be found
                self.detail_label_content.setCurrentText("Name only")
                self.detail_placement.setCurrentText("Inside")
                self.detail_offset.setValue(0)
                self.detail_fill_color.setCurrentText("blue")
                self.detail_date_format.setCurrentText("Use Global")
                self._set_detail_form_enabled(self._detail_form_widgets, False)
        finally:
            self._updating_form = False

    def _clear_detail_form(self):
        """Clear the detail form when no task is selected."""
        self._updating_form = True
        try:
            self.detail_label_content.setCurrentText("Name only")
            self.detail_placement.setCurrentText("Inside")
            self.detail_offset.setValue(0)
            self.detail_fill_color.setCurrentText("blue")
            self.detail_date_format.setCurrentText("Use Global")
            # Disable detail form widgets when no task is selected
            self._set_detail_form_enabled(self._detail_form_widgets, False)
        finally:
            self._updating_form = False

    def _on_detail_form_changed(self):
        """Handle changes in detail form - update selected task."""
        if self._updating_form or self._selected_row is None:
            return
        
        # Trigger sync to update the data
        self._sync_data_if_not_initializing()

    def _connect_signals(self):
        self._item_changed_connection = self.tasks_table.itemChanged.connect(self._on_item_changed)
        self.tasks_table.selectionModel().selectionChanged.connect(self._on_table_selection_changed)

    def _get_column_index(self, column_name: str) -> Optional[int]:
        """Return the visible column index for column_name by searching visible table headers.

        Overrides BaseTab._get_column_index so callers can pass the result directly to
        item()/cellWidget() without a second _reverse_column_mapping lookup.
        """
        for i in range(self.tasks_table.columnCount()):
            header = self.tasks_table.horizontalHeaderItem(i)
            if header and header.text() == column_name:
                return i
        return None
    
    def _get_swimlane_info_for_row(self, row_number: int) -> Tuple[Optional[int], Optional[str]]:
        """
        Get swimlane order and name for a given row number.
        
        Args:
            row_number: The row number (1-based) to find swimlane for
            
        Returns:
            Tuple of (swimlane_order, swimlane_name) or (None, None) if not found
        """
        if not row_number or row_number < 1:
            return (None, None)
        
        swimlanes = self.project_data.swimlanes
        if not swimlanes:
            return (None, None)
        
        # Calculate which swimlane contains this row
        # Swimlanes are ordered in the list, and each spans row_count rows
        current_first_row = 1  # 1-based
        
        for order, swimlane in enumerate(swimlanes, start=1):
            first_row = current_first_row
            last_row = current_first_row + swimlane.row_count - 1
            
            if first_row <= row_number <= last_row:
                # Found the swimlane containing this row
                swimlane_name = swimlane.title if swimlane.title else ""
                # Truncate name if too long (e.g., 20 characters)
                if len(swimlane_name) > 20:
                    swimlane_name = swimlane_name[:17] + "..."
                return (order, swimlane_name)
            
            current_first_row += swimlane.row_count
        
        # Row number is outside all swimlanes
        return (None, None)
    
    def _is_header_row(self, row_idx: int) -> bool:
        """Return True if the given table row is a swimlane header row."""
        item = self.tasks_table.item(row_idx, 0)
        return item is not None and bool(item.data(SWIMLANE_HEADER_ROLE))

    def _insert_swimlane_header_row(self, row_idx: int, swimlane_name: str) -> None:
        """Populate row_idx as a non-editable, greyed-out, bold swimlane header row."""
        header_color = QColor("#d0d0d0")
        name_col = self._get_column_index("Name")
        bold_font = QFont()
        bold_font.setBold(True)
        for col_idx in range(self.tasks_table.columnCount()):
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsEnabled)  # Not selectable, not editable
            item.setBackground(QBrush(header_color))
            item.setData(SWIMLANE_HEADER_ROLE, True)
            if col_idx == name_col:
                item.setText(swimlane_name)
                item.setFont(bold_font)
            self.tasks_table.setItem(row_idx, col_idx, item)

    def _truncate_tooltip_text(self, text: str, max_length: int = 50) -> str:
        """Truncate text to max_length and add ellipsis if needed for tooltip display."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    def _refresh_swimlane_columns_for_row(self, row_idx: int):
        """Refresh Lane column for a specific row with tooltip showing swimlane name."""
        if self._is_header_row(row_idx):
            return
        # Get row_number directly from the table's Row column (not from task object,
        # since task might not be updated yet when this is called during editing)
        row_col = self._get_column_index("Chart Row")

        if row_col is None:
            return

        row_item = self.tasks_table.item(row_idx, row_col)
        if row_item is None:
            return

        # Get row_number from the table item (use UserRole if available, otherwise parse text)
        row_number = row_item.data(Qt.UserRole)
        if row_number is None:
            try:
                row_number = safe_int(row_item.text(), 1)
            except (ValueError, AttributeError):
                row_number = 1

        if not row_number or row_number < 1:
            return

        lane_col = self._get_column_index("Lane")

        # Get swimlane info for this row_number
        swimlane_order, swimlane_name = self._get_swimlane_info_for_row(row_number)

        # Update Lane column
        if lane_col is not None:
            order_text = str(swimlane_order) if swimlane_order is not None else ""
            # Prepare tooltip text: show swimlane name (truncated if long) or "Unhomed"
            if swimlane_name:
                tooltip_text = self._truncate_tooltip_text(swimlane_name, 50)
            else:
                tooltip_text = "Unhomed"

            item = self.tasks_table.item(row_idx, lane_col)
            if item:
                item.setText(order_text)
                item.setToolTip(tooltip_text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))  # Set background color
            else:
                item = QTableWidgetItem(order_text)
                item.setToolTip(tooltip_text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                self.tasks_table.setItem(row_idx, lane_col, item)
    
    def _refresh_all_swimlane_columns(self):
        """Refresh Lane column for all rows (useful when swimlanes are updated)."""
        # Re-sort after swimlane changes since lane order affects task ordering
        # The sort will repopulate all rows via _update_table_row_from_task, which calls
        # _refresh_swimlane_columns_for_row to set tooltips correctly
        self._sort_tasks_by_swimlane_and_row()
    
    def _get_task_sort_key(self, task: Task) -> Tuple[int, int, str]:
        """
        Get sort key for task: (swimlane_order, row_number, finish_date).
        Used for sorting tasks by swimlane order (Lane), then row number, then finish date.
        Empty finish dates sort to the end (after valid dates).
        """
        swimlane_order, _ = self._get_swimlane_info_for_row(task.row_number)
        # Use 9999 for tasks outside swimlanes (sort to end)
        swimlane_order = swimlane_order if swimlane_order is not None else 9999
        # Use 'ZZZZ-ZZ-ZZ' for empty finish dates to sort them to the end (after valid dates)
        finish_date = task.finish_date if task.finish_date else "ZZZZ-ZZ-ZZ"
        return (swimlane_order, task.row_number, finish_date)
    
    def _sort_tasks_by_swimlane_and_row(self):
        """Sort tasks by swimlane order, row number, finish date.

        Inserts a non-editable swimlane header row before each swimlane group.
        """
        was_sorting = self.tasks_table.isSortingEnabled()
        self.tasks_table.setSortingEnabled(False)

        try:
            # Capture currently selected task IDs (skip header rows)
            selected_task_ids: Set[int] = set()
            id_col = self._get_column_index("ID")
            if id_col is not None:
                selected_row_indices = {idx.row() for idx in self.tasks_table.selectionModel().selectedRows()}
                for row_idx in range(self.tasks_table.rowCount()):
                    if self._is_header_row(row_idx) or row_idx not in selected_row_indices:
                        continue
                    item = self.tasks_table.item(row_idx, id_col)
                    if item:
                        try:
                            selected_task_ids.add(int(item.text()))
                        except (ValueError, TypeError):
                            pass

            # Sort tasks from project_data
            tasks = list(self.project_data.tasks)
            tasks.sort(key=self._get_task_sort_key)

            # Group tasks by swimlane order
            swimlane_tasks: Dict[int, List[Task]] = {}
            orphan_tasks: List[Task] = []
            for task in tasks:
                order, _ = self._get_swimlane_info_for_row(task.row_number)
                if order is not None:
                    swimlane_tasks.setdefault(order, []).append(task)
                else:
                    orphan_tasks.append(task)

            swimlanes = self.project_data.swimlanes
            # One header row per swimlane + one row per task
            total_rows = len(swimlanes) + len(tasks)

            self.tasks_table.blockSignals(True)
            self.tasks_table.setRowCount(0)
            self.tasks_table.setRowCount(total_rows)

            rows_to_select: List[int] = []
            current_row = 0

            for order, swimlane in enumerate(swimlanes, start=1):
                swimlane_name = swimlane.title if swimlane.title else f"Lane {order}"
                self._insert_swimlane_header_row(current_row, swimlane_name)
                current_row += 1
                for task in swimlane_tasks.get(order, []):
                    self._update_table_row_from_task(current_row, task)
                    if task.task_id in selected_task_ids:
                        rows_to_select.append(current_row)
                    current_row += 1

            for task in orphan_tasks:
                self._update_table_row_from_task(current_row, task)
                if task.task_id in selected_task_ids:
                    rows_to_select.append(current_row)
                current_row += 1

            # Trim any excess rows (safety net)
            if current_row < self.tasks_table.rowCount():
                self.tasks_table.setRowCount(current_row)

            self.tasks_table.blockSignals(False)

            # Restore selection
            for row_idx in rows_to_select:
                self.tasks_table.selectRow(row_idx)

        finally:
            self.tasks_table.setSortingEnabled(was_sorting)
    
    def _task_from_table_row(self, row_idx: int) -> Optional[Task]:
        """
        Extract a Task object from a table row.
        Returns None if the row is a swimlane header row or is invalid/incomplete.
        """
        if self._is_header_row(row_idx):
            return None
        try:
            # Get column indices by name (visible indices via overridden _get_column_index)
            id_col = self._get_column_index("ID")
            row_col = self._get_column_index("Chart Row")
            name_col = self._get_column_index("Name")
            start_date_col = self._get_column_index("Start Date")
            finish_date_col = self._get_column_index("Finish Date")

            if id_col is None or row_col is None or name_col is None:
                return None

            # Extract ID, Row, Name
            id_item = self.tasks_table.item(row_idx, id_col)
            row_item = self.tasks_table.item(row_idx, row_col)
            name_item = self.tasks_table.item(row_idx, name_col)
            
            if not id_item or not row_item or not name_item:
                return None
            
            task_id = safe_int(id_item.text())
            row_number = safe_int(row_item.text(), 1)
            task_name = name_item.text().strip()
            
            if task_id <= 0:
                return None
            
            # Extract dates from QDateEdit widgets or fallback to text items (key-based)
            from ui.table_utils import extract_date_from_cell
            start_date_internal = ""
            start_date_conversion_failed = False
            if start_date_col is not None:
                extracted = extract_date_from_cell(self.tasks_table, row_idx, start_date_col, self.app_config.general.ui_date_config)
                if extracted:
                    start_date_internal = extracted
                else:
                    # Check if there's a text item that failed to parse (conversion failed)
                    start_date_item = self.tasks_table.item(row_idx, start_date_col)
                    if start_date_item and start_date_item.text().strip():
                        start_date_conversion_failed = True

            finish_date_internal = ""
            finish_date_conversion_failed = False
            if finish_date_col is not None:
                extracted = extract_date_from_cell(self.tasks_table, row_idx, finish_date_col, self.app_config.general.ui_date_config)
                if extracted:
                    finish_date_internal = extracted
                else:
                    # Check if there's a text item that failed to parse (conversion failed)
                    finish_date_item = self.tasks_table.item(row_idx, finish_date_col)
                    if finish_date_item and finish_date_item.text().strip():
                        finish_date_conversion_failed = True

            # Fallback: read directly from QDateEdit when extract_date_from_cell returned None
            # (e.g. newly added row where widget may not be reported yet by cellWidget in some Qt builds)
            if not start_date_internal and start_date_col is not None:
                widget = self.tasks_table.cellWidget(row_idx, start_date_col)
                if widget and isinstance(widget, QDateEdit):
                    start_date_internal = widget.date().toString("yyyy-MM-dd")
            if not finish_date_internal and finish_date_col is not None:
                widget = self.tasks_table.cellWidget(row_idx, finish_date_col)
                if widget and isinstance(widget, QDateEdit):
                    finish_date_internal = widget.date().toString("yyyy-MM-dd")
            
            # Auto-populate missing date field for milestones (if only one date is provided)
            # Only auto-populate if the field was actually empty (not if conversion failed)
            if start_date_internal and not finish_date_internal and not finish_date_conversion_failed:
                finish_date_internal = start_date_internal  # Auto-populate finish date
            elif finish_date_internal and not start_date_internal and not start_date_conversion_failed:
                start_date_internal = finish_date_internal  # Auto-populate start date
            
            # Extract Label Content, Placement, Offset, Fill Color, and Date Format from detail form if this is the selected row
            # Otherwise, get from existing Task object
            label_content = "Name only"
            label_placement = "Inside"
            label_horizontal_offset = 0.0
            fill_color = "blue"
            date_format = None
            
            if self._selected_task_id is not None and task_id == self._selected_task_id:
                # Use values from detail form
                if self.detail_label_content:
                    label_content = self.detail_label_content.currentText()
                if self.detail_placement:
                    label_placement = self.detail_placement.currentText()
                if self.detail_offset:
                    # QSpinBox handles validation automatically (0-300 range), so no need for manual validation
                    # Convert to float (model uses float but offset should be integer pixels)
                    label_horizontal_offset = float(self.detail_offset.value())
                if self.detail_fill_color:
                    fill_color = self.detail_fill_color.currentText()
                if self.detail_date_format:
                    # Convert "Use Global" to None, otherwise use the format name
                    date_format_text = self.detail_date_format.currentText()
                    date_format = None if date_format_text == "Use Global" else date_format_text
            else:
                # Get from existing Task object if available (look up by task_id)
                existing_task = next((t for t in self.project_data.tasks if t.task_id == task_id), None)
                if existing_task:
                    label_content = existing_task.label_content if hasattr(existing_task, 'label_content') and existing_task.label_content else "Name only"
                    label_placement = existing_task.label_placement
                    label_horizontal_offset = existing_task.label_horizontal_offset if hasattr(existing_task, 'label_horizontal_offset') else 0.0
                    fill_color = existing_task.fill_color if hasattr(existing_task, 'fill_color') else "blue"
                    date_format = existing_task.date_format if hasattr(existing_task, 'date_format') else None
            
            # Create Task object
            task = Task(
                task_id=task_id,
                task_name=task_name,
                start_date=start_date_internal,
                finish_date=finish_date_internal,
                row_number=row_number,
                label_hide="Yes" if label_content != "None" else "No",  # Keep for backward compatibility
                label_content=label_content,
                label_placement=label_placement,
                label_alignment="Centre",
                label_horizontal_offset=label_horizontal_offset,
                label_text_colour="black",
                fill_color=fill_color,
                date_format=date_format
            )
            
            return task
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Error extracting task from table row {row_idx}: {e}")
            return None
    
    def _update_table_row_from_task(self, row_idx: int, task: Task) -> None:
        """
        Populate a table row from a Task object.
        Uses column name mapping instead of positional indices.
        """
        # Get column indices by name (visible indices via overridden _get_column_index)
        id_col = self._get_column_index("ID")
        row_col = self._get_column_index("Chart Row")
        name_col = self._get_column_index("Name")
        start_date_col = self._get_column_index("Start Date")
        finish_date_col = self._get_column_index("Finish Date")
        lane_col = self._get_column_index("Lane")
        valid_col = self._get_column_index("Valid")
        
        # Block signals to prevent recursive updates
        was_blocked = self.tasks_table.signalsBlocked()
        self.tasks_table.blockSignals(True)
        try:
            # Update ID column (read-only)
            if id_col is not None:
                item = self.tasks_table.item(row_idx, id_col)
                if item:
                    item.setText(str(task.task_id))
                    item.setData(Qt.UserRole, task.task_id)
                else:
                    item = NumericTableWidgetItem(str(task.task_id))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                    item.setData(Qt.UserRole, task.task_id)
                    self.tasks_table.setItem(row_idx, id_col, item)

            # Update Row column
            if row_col is not None:
                item = self.tasks_table.item(row_idx, row_col)
                if item:
                    item.setText(str(task.row_number))
                    item.setData(Qt.UserRole, task.row_number)
                else:
                    item = NumericTableWidgetItem(str(task.row_number))
                    item.setData(Qt.UserRole, task.row_number)
                    self.tasks_table.setItem(row_idx, row_col, item)

            # Update Name column
            if name_col is not None:
                item = self.tasks_table.item(row_idx, name_col)
                if item:
                    item.setText(task.task_name)
                else:
                    item = QTableWidgetItem(task.task_name)
                    self.tasks_table.setItem(row_idx, name_col, item)

            # Update Start Date column (QDateEdit widget)
            if start_date_col is not None:
                date_widget = self.tasks_table.cellWidget(row_idx, start_date_col)
                if date_widget and isinstance(date_widget, QDateEdit):
                    # Update existing QDateEdit widget
                    if task.start_date:
                        start_dt = parse_internal_date(task.start_date)
                        if start_dt:
                            start_qdate = QDate(start_dt.year, start_dt.month, start_dt.day)
                            date_widget.blockSignals(True)
                            date_widget.setDate(start_qdate)
                            date_widget.blockSignals(False)
                        else:
                            date_widget.blockSignals(True)
                            date_widget.setDate(QDate.currentDate())
                            date_widget.blockSignals(False)
                    else:
                        date_widget.blockSignals(True)
                        date_widget.setDate(QDate.currentDate())
                        date_widget.blockSignals(False)
                    # Reconnect signals (disconnect first to avoid duplicates)
                    try:
                        date_widget.dateChanged.disconnect()
                    except:
                        pass
                    date_widget.dateChanged.connect(lambda date, w=date_widget: self._update_task_date_constraints(widget=w))
                    date_widget.dateChanged.connect(self._sync_data_if_not_initializing)
                else:
                    # Create QDateEdit if it doesn't exist
                    from ui.table_utils import create_date_widget
                    date_widget = create_date_widget(task.start_date if task.start_date else "", self.app_config.general.ui_date_config)
                date_widget.dateChanged.connect(lambda date, w=date_widget: self._update_task_date_constraints(widget=w))
                date_widget.dateChanged.connect(self._sync_data_if_not_initializing)
                self.tasks_table.setCellWidget(row_idx, start_date_col, date_widget)

            # Update Finish Date column (QDateEdit widget)
            if finish_date_col is not None:
                date_widget = self.tasks_table.cellWidget(row_idx, finish_date_col)
                if date_widget and isinstance(date_widget, QDateEdit):
                    # Update existing QDateEdit widget
                    if task.finish_date:
                        finish_dt = parse_internal_date(task.finish_date)
                        if finish_dt:
                            finish_qdate = QDate(finish_dt.year, finish_dt.month, finish_dt.day)
                            date_widget.blockSignals(True)
                            date_widget.setDate(finish_qdate)
                            date_widget.blockSignals(False)
                        else:
                            date_widget.blockSignals(True)
                            date_widget.setDate(QDate.currentDate())
                            date_widget.blockSignals(False)
                    else:
                        date_widget.blockSignals(True)
                        date_widget.setDate(QDate.currentDate())
                        date_widget.blockSignals(False)
                    # Reconnect signals (disconnect first to avoid duplicates)
                    try:
                        date_widget.dateChanged.disconnect()
                    except:
                        pass
                    date_widget.dateChanged.connect(lambda date, w=date_widget: self._update_task_date_constraints(widget=w))
                    date_widget.dateChanged.connect(self._sync_data_if_not_initializing)
                else:
                    # Create QDateEdit if it doesn't exist
                    from ui.table_utils import create_date_widget
                    date_widget = create_date_widget(task.finish_date if task.finish_date else "", self.app_config.general.ui_date_config)
                    date_widget.dateChanged.connect(lambda date, w=date_widget: self._update_task_date_constraints(widget=w))
                    date_widget.dateChanged.connect(self._sync_data_if_not_initializing)
                    self.tasks_table.setCellWidget(row_idx, finish_date_col, date_widget)

            # Update date constraints after setting both dates
            self._update_task_date_constraints(row_idx=row_idx)

            # Update Lane column (read-only, calculated) - will be handled by _refresh_swimlane_columns_for_row
            # We call it here to ensure tooltip is set correctly
            self._refresh_swimlane_columns_for_row(row_idx)

            # Update Valid column (calculate valid status)
            if valid_col is not None:
                used_ids = {safe_int(t.task_id) for t in self.project_data.tasks if t.task_id != task.task_id}
                row_errors = self.project_data.validator.validate_task(
                    task, used_ids, self.app_config.general.ui_date_config
                )
                valid_status = "No" if row_errors else "Yes"

                item = self.tasks_table.item(row_idx, valid_col)
                if item:
                    item.setText(valid_status)
                else:
                    item = QTableWidgetItem(valid_status)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                    self.tasks_table.setItem(row_idx, valid_col, item)
        finally:
            self.tasks_table.blockSignals(was_blocked)
    
    def _update_task_date_constraints(self, widget=None, row_idx=None):
        """Update date constraints for a task row to prevent invalid date ranges.
        
        For tasks: finish can be same as start (milestone) but not before start.
        
        Args:
            widget: QDateEdit widget that triggered the update (optional)
            row_idx: Row index (optional, will be found from widget if not provided)
        """
        start_date_col = self._get_column_index("Start Date")
        finish_date_col = self._get_column_index("Finish Date")

        if start_date_col is None or finish_date_col is None:
            return

        # Find row index if not provided
        if row_idx is None and widget is not None:
            # Search for the widget in the table to find its row
            for r in range(self.tasks_table.rowCount()):
                if (self.tasks_table.cellWidget(r, start_date_col) == widget or
                        self.tasks_table.cellWidget(r, finish_date_col) == widget):
                    row_idx = r
                    break
            if row_idx is None:
                return

        if row_idx is None:
            return

        start_widget = self.tasks_table.cellWidget(row_idx, start_date_col)
        finish_widget = self.tasks_table.cellWidget(row_idx, finish_date_col)
        
        if not isinstance(start_widget, QDateEdit) or not isinstance(finish_widget, QDateEdit):
            return
        
        start_qdate = start_widget.date()
        finish_qdate = finish_widget.date()
        
        # Block signals to prevent recursive updates
        finish_widget.blockSignals(True)
        start_widget.blockSignals(True)
        
        # For tasks: finish can be same as start (milestone), but not before
        # Set constraints FIRST
        finish_widget.setMinimumDate(start_qdate)
        start_widget.setMaximumDate(finish_qdate)
        
        # THEN validate and correct if dates are invalid (handles manual typing that bypasses constraints)
        if finish_qdate < start_qdate:
            finish_widget.setDate(start_qdate)
            finish_qdate = start_qdate  # Update for constraint recalculation
        
        # Recalculate constraints with corrected dates
        finish_widget.setMinimumDate(start_qdate)
        start_widget.setMaximumDate(finish_qdate)
        
        start_widget.blockSignals(False)
        finish_widget.blockSignals(False)
    
    def _on_item_changed(self, item):
        """Handle item changes - update UserRole for numeric and date columns to maintain proper sorting."""
        # Skip auto-population during initialization to preserve invalid dates
        if self._initializing:
            return
        
        # CRITICAL: Disconnect signal BEFORE modifying item to prevent infinite loop
        was_connected = False
        try:
            self.tasks_table.itemChanged.disconnect(self._on_item_changed)
            was_connected = True
        except:
            pass  # Signal might not be connected
        
        try:
            if item is None:
                return
            
            col = item.column()
            row = item.row()
            
            headers = [col.name for col in self.table_config.columns]
            
            # Find which actual column this visible column maps to
            actual_col_idx = None
            for vis_idx, act_idx in self._column_mapping.items():
                if vis_idx == col:
                    actual_col_idx = act_idx
                    break
            
            if actual_col_idx is None:
                return
            
            col_name = headers[actual_col_idx] if actual_col_idx < len(headers) else ""
            
            # Skip date columns - QDateEdit widgets handle their own changes via dateChanged signal
            if col_name in ["Start Date", "Finish Date"]:
                # Check if this is actually a QDateEdit widget (shouldn't trigger itemChanged)
                # But handle gracefully if it does
                date_widget = self.tasks_table.cellWidget(row, col)
                if isinstance(date_widget, QDateEdit):
                    # QDateEdit handles its own changes, skip processing
                    return
                # Fallback: if it's a text item (backward compatibility), process it
                try:
                    val_str = item.text().strip()
                    if val_str:
                        try:
                            # Use normalize_display_date to handle flexible formats
                            normalized = normalize_display_date(val_str)
                            date_obj = datetime.strptime(normalized, "%d/%m/%Y")
                            
                            # Auto-populate the other date field for milestones (if only one date is provided)
                            other_col_name = "Finish Date" if col_name == "Start Date" else "Start Date"
                            other_col_idx = self._get_column_index(other_col_name)
                            if other_col_idx is not None:
                                other_date_widget = self.tasks_table.cellWidget(row, other_col_idx)
                                if isinstance(other_date_widget, QDateEdit):
                                    # Auto-populate the other QDateEdit widget
                                    other_qdate = QDate(date_obj.year, date_obj.month, date_obj.day)
                                    other_date_widget.blockSignals(True)
                                    other_date_widget.setDate(other_qdate)
                                    other_date_widget.blockSignals(False)
                                else:
                                    # Fallback to text item
                                    other_date_item = self.tasks_table.item(row, other_col_idx)
                                    if other_date_item:
                                        other_date_text = other_date_item.text().strip()
                                        if not other_date_text:
                                            other_date_item.setText(normalized)
                                            other_date_item.setData(Qt.UserRole, date_obj)
                                    else:
                                        other_date_item = DateTableWidgetItem(normalized)
                                        other_date_item.setData(Qt.UserRole, date_obj)
                                        self.tasks_table.setItem(row, other_col_idx, other_date_item)
                        except ValueError as e:
                            date_obj = None
                        
                        # Check if UserRole already has the same value to avoid unnecessary updates
                        current_role = item.data(Qt.UserRole)
                        if current_role != date_obj:
                            item.setData(Qt.UserRole, date_obj)
                    else:
                        item.setData(Qt.UserRole, None)
                except (ValueError, AttributeError, Exception) as e:
                    logging.error(f"_on_item_changed: Error parsing date: {e}", exc_info=True)
                    item.setData(Qt.UserRole, None)
            # Update UserRole for numeric columns (ID, Row)
            elif col_name == "ID":
                # Ensure Task ID is read-only with gray background
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                try:
                    val_str = item.text().strip()
                    item.setData(Qt.UserRole, int(val_str) if val_str else 0)
                except (ValueError, AttributeError):
                    item.setData(Qt.UserRole, 0)
            elif col_name == "Chart Row":
                try:
                    val_str = item.text().strip()
                    item.setData(Qt.UserRole, int(val_str) if val_str else 1)
                    # Refresh swimlane columns when row number changes
                    self._refresh_swimlane_columns_for_row(row)
                except (ValueError, AttributeError):
                    item.setData(Qt.UserRole, 1)
                    # Refresh swimlane columns even if parsing failed
                    self._refresh_swimlane_columns_for_row(row)
            
            # Don't trigger sync for Valid column changes (it's read-only and auto-calculated)
            if actual_col_idx < len(headers) and headers[actual_col_idx] != "Valid":
                # Trigger sync with error handling to prevent crashes
                if not self._syncing:
                    try:
                        self._syncing = True
                        try:
                            self._sync_data_if_not_initializing()
                        except Exception as e:
                            logging.error(f"_on_item_changed: Error in sync: {e}", exc_info=True)
                    finally:
                        self._syncing = False
        except Exception as e:
            logging.error(f"_on_item_changed: Unexpected error: {e}", exc_info=True)
            raise
        finally:
            # Reconnect itemChanged signal
            if was_connected:
                try:
                    self.tasks_table.itemChanged.connect(self._on_item_changed)
                except Exception:
                    pass  # Signal might already be connected

    def _load_initial_data(self):
        self._load_initial_data_impl()

    def _load_initial_data_impl(self):
        """Load initial data into the table using Task objects directly."""
        # Get Task objects directly from project_data
        tasks = self.project_data.tasks
        row_count = len(tasks)
        self.tasks_table.setRowCount(row_count)
        self._initializing = True

        for row_idx in range(row_count):
            # Use helper method to populate row from Task object
            task = tasks[row_idx]
            self._update_table_row_from_task(row_idx, task)
        
        # Sort by lane order, row number, then finish date (inserts swimlane header rows)
        self._sort_tasks_by_swimlane_and_row()

        # Ensure all read-only cells have proper styling
        self._ensure_read_only_styling()

        self._initializing = False

        # Disable detail form if no tasks exist or no selection
        if row_count == 0 or self._selected_row is None:
            self._clear_detail_form()

        # Calculate and update Valid column for all rows
        self._update_valid_column_only()

        # Refresh Lane columns to ensure tooltips are up-to-date after initial load and sort
        for row_idx in range(self.tasks_table.rowCount()):
            if not self._is_header_row(row_idx):
                self._refresh_swimlane_columns_for_row(row_idx)

    def _sync_data(self):
        self._sync_data_impl()

    def _sync_data_impl(self):
        """Extract data from table and update project_data using Task objects directly."""
        try:
            # Avoid emitting during initialization to prevent recursive updates
            if self._initializing:
                return
            
            # Extract Task objects from table rows
            tasks = []
            for row_idx in range(self.tasks_table.rowCount()):
                task = self._task_from_table_row(row_idx)
                if task:
                    tasks.append(task)
            
            # Update project data with Task objects directly
            errors = self.project_data.update_tasks(tasks)
            
            # Update only the Valid column (computed field) - don't overwrite user-edited fields
            self._update_valid_column_only()
        except Exception as e:
            logging.error(f"Error in _sync_data_impl: {e}", exc_info=True)

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            self._sync_data()
    
    def _ensure_read_only_styling(self):
        """Ensure all read-only cells (ID, Valid, Lane) have proper styling."""
        id_col = self._get_column_index("ID")
        valid_col = self._get_column_index("Valid")

        if id_col is not None:
            for row in range(self.tasks_table.rowCount()):
                if self._is_header_row(row):
                    continue
                item = self.tasks_table.item(row, id_col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(self.app_config.general.read_only_bg_color))

        if valid_col is not None:
            for row in range(self.tasks_table.rowCount()):
                if self._is_header_row(row):
                    continue
                item = self.tasks_table.item(row, valid_col)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
    
    def _refresh_date_widgets(self):
        """Refresh all date widgets with current date format from config."""
        start_date_col = self._get_column_index("Start Date")
        finish_date_col = self._get_column_index("Finish Date")

        for row in range(self.tasks_table.rowCount()):
            # Refresh Start Date widget
            if start_date_col is not None:
                widget = self.tasks_table.cellWidget(row, start_date_col)
                if widget and isinstance(widget, QDateEdit):
                    # Get current date from widget
                    current_date = widget.date()
                    current_date_str = current_date.toString("yyyy-MM-dd")

                    # Disconnect old signals
                    try:
                        widget.dateChanged.disconnect()
                    except:
                        pass

                    # Create new widget with updated format
                    from ui.table_utils import create_date_widget
                    new_widget = create_date_widget(current_date_str, self.app_config.general.ui_date_config)

                    # Reconnect signals (including constraint updates)
                    new_widget.dateChanged.connect(lambda date, w=new_widget: self._update_task_date_constraints(widget=w))
                    new_widget.dateChanged.connect(self._sync_data_if_not_initializing)

                    # Replace widget
                    self.tasks_table.setCellWidget(row, start_date_col, new_widget)

            # Refresh Finish Date widget
            if finish_date_col is not None:
                widget = self.tasks_table.cellWidget(row, finish_date_col)
                if widget and isinstance(widget, QDateEdit):
                    # Get current date from widget
                    current_date = widget.date()
                    current_date_str = current_date.toString("yyyy-MM-dd")

                    # Disconnect old signals
                    try:
                        widget.dateChanged.disconnect()
                    except:
                        pass

                    # Create new widget with updated format
                    from ui.table_utils import create_date_widget
                    new_widget = create_date_widget(current_date_str, self.app_config.general.ui_date_config)

                    # Reconnect signals (including constraint updates)
                    new_widget.dateChanged.connect(lambda date, w=new_widget: self._update_task_date_constraints(widget=w))
                    new_widget.dateChanged.connect(self._sync_data_if_not_initializing)

                    # Replace widget
                    self.tasks_table.setCellWidget(row, finish_date_col, new_widget)

            # Update date constraints after refreshing both widgets
            if start_date_col is not None or finish_date_col is not None:
                self._update_task_date_constraints(row_idx=row)

    def _update_valid_column_only(self):
        """Update only the Valid column without reloading the entire table."""
        try:
            # Check if table is valid and has rows
            if not self.tasks_table or self.tasks_table.rowCount() == 0:
                return
            
            # Find Valid and ID column indices
            valid_col = self._get_column_index("Valid")
            id_col = self._get_column_index("ID")

            if valid_col is None:
                return

            if id_col is None:
                logging.error("_update_valid_column_only: Could not find ID column")
                return

            # Create a mapping of task_id to task for quick lookup
            task_map = {safe_int(task.task_id): task for task in self.project_data.tasks}

            # Block signals to prevent recursive updates
            was_blocked = self.tasks_table.signalsBlocked()
            self.tasks_table.blockSignals(True)

            try:
                # Temporarily disconnect itemChanged to prevent issues
                was_connected = False
                try:
                    self.tasks_table.itemChanged.disconnect(self._on_item_changed)
                    was_connected = True
                except Exception:
                    pass

                try:
                    # Build used_ids set from all tasks for validation
                    used_ids: Set[int] = {safe_int(task.task_id) for task in self.project_data.tasks}
                    logging.debug(f"_update_valid_column_only: Found {len(used_ids)} tasks in project_data. Task IDs: {sorted(used_ids)}")

                    # For each table row, find the corresponding task by task_id
                    for row_idx in range(self.tasks_table.rowCount()):
                        # Skip swimlane header rows
                        if self._is_header_row(row_idx):
                            continue
                        # Extract task_id from ID column
                        id_item = self.tasks_table.item(row_idx, id_col)
                        if not id_item:
                            logging.debug(f"_update_valid_column_only: Row {row_idx}: No ID item found at column {id_col}")
                            # Set Valid to "No" - missing ID
                            valid_status = "No"
                            item = self.tasks_table.item(row_idx, valid_col)
                            if item:
                                item.setText(valid_status)
                            else:
                                item = QTableWidgetItem(valid_status)
                                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                                self.tasks_table.setItem(row_idx, valid_col, item)
                            continue

                        try:
                            task_id = safe_int(id_item.text())
                            if task_id <= 0:
                                logging.debug(f"_update_valid_column_only: Row {row_idx}: Invalid task_id '{id_item.text()}' (must be > 0)")
                                # Set Valid to "No" - invalid ID
                                valid_status = "No"
                                item = self.tasks_table.item(row_idx, valid_col)
                                if item:
                                    item.setText(valid_status)
                                else:
                                    item = QTableWidgetItem(valid_status)
                                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                                    item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                                    self.tasks_table.setItem(row_idx, valid_col, item)
                                continue
                        except (ValueError, TypeError) as e:
                            logging.debug(f"_update_valid_column_only: Row {row_idx}: Failed to parse task_id '{id_item.text()}': {e}")
                            # Set Valid to "No" - parse error
                            valid_status = "No"
                            item = self.tasks_table.item(row_idx, valid_col)
                            if item:
                                item.setText(valid_status)
                            else:
                                item = QTableWidgetItem(valid_status)
                                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                                self.tasks_table.setItem(row_idx, valid_col, item)
                            continue

                        # Find the task in project_data by task_id
                        task = task_map.get(task_id)
                        if not task:
                            logging.warning(f"_update_valid_column_only: Row {row_idx}: Task with task_id={task_id} not found in project_data.tasks. Available task_ids: {sorted(task_map.keys())}")
                            # Set Valid to "No" - task not found
                            valid_status = "No"
                            item = self.tasks_table.item(row_idx, valid_col)
                            if item:
                                item.setText(valid_status)
                            else:
                                item = QTableWidgetItem(valid_status)
                                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                                self.tasks_table.setItem(row_idx, valid_col, item)
                            continue

                        # Calculate valid status (exclude current task from used_ids for uniqueness check)
                        task_used_ids = used_ids - {safe_int(task.task_id)}
                        row_errors = self.project_data.validator.validate_task(
                            task, task_used_ids, self.app_config.general.ui_date_config
                        )
                        valid_status = "No" if row_errors else "Yes"

                        if row_errors:
                            logging.debug(f"_update_valid_column_only: Row {row_idx}: Task {task_id} validation failed: {row_errors}")
                        else:
                            logging.debug(f"_update_valid_column_only: Row {row_idx}: Task {task_id} validation passed")

                        # Update the Valid cell
                        item = self.tasks_table.item(row_idx, valid_col)
                        if item:
                            item.setText(str(valid_status))
                        else:
                            item = QTableWidgetItem(str(valid_status))
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                            self.tasks_table.setItem(row_idx, valid_col, item)
                finally:
                    # Reconnect itemChanged signal
                    if was_connected:
                        try:
                            self.tasks_table.itemChanged.connect(self._on_item_changed)
                        except Exception:
                            pass
            finally:
                self.tasks_table.blockSignals(was_blocked)
        except Exception as e:
            logging.error(f"_update_valid_column_only: Error: {e}", exc_info=True)

    def _add_task(self):
        """Add a new task below the selected task, inheriting Chart Row, Start Date, and Finish Date."""
        if self._selected_row is None:
            return  # Button should be disabled, but guard defensively

        task = self._task_from_table_row(self._selected_row)
        default_row_number = task.row_number if task else 1
        default_start_date = task.start_date if task else None
        default_finish_date = task.finish_date if task else None

        add_row(self.tasks_table, "tasks", self.app_config.tables, self, "ID",
                default_row_number=default_row_number,
                default_start_date=default_start_date,
                default_finish_date=default_finish_date,
                date_config=self.app_config.general.ui_date_config)

    def _duplicate_tasks(self):
        """Duplicate selected tasks with new IDs."""
        # Get all selected rows
        selected_rows = self.tasks_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select task(s) to duplicate.")
            return
        
        checked_rows = [row.row() for row in selected_rows]
        
        # Get all used task IDs from project_data
        used_ids = {task.task_id for task in self.project_data.tasks}
        
        # Also check IDs currently in the table
        id_col = self._get_column_index("ID")
        if id_col is not None:
            for row in range(self.tasks_table.rowCount()):
                item = self.tasks_table.item(row, id_col)
                if item and item.text():
                    try:
                        used_ids.add(int(item.text()))
                    except (ValueError, TypeError):
                        continue
        
        # Find next available ID
        next_id = 1
        while next_id in used_ids:
            next_id += 1
        
        # Extract Task objects from checked rows and create duplicates
        tasks_to_duplicate = []
        for row_idx in checked_rows:
            original_task = self._task_from_table_row(row_idx)
            if not original_task:
                continue
            
            # Create a new Task object with a new ID
            new_task = Task(
                task_id=next_id,
                task_name=original_task.task_name + " [Duplicate]",
                start_date=original_task.start_date,
                finish_date=original_task.finish_date,
                row_number=original_task.row_number,
                is_milestone=original_task.is_milestone,
                label_placement=original_task.label_placement,
                label_hide=original_task.label_hide,  # Keep for backward compatibility
                label_content=original_task.label_content if hasattr(original_task, 'label_content') else "Name only",
                label_alignment=original_task.label_alignment,
                label_horizontal_offset=original_task.label_horizontal_offset,
                label_text_colour=original_task.label_text_colour,
                fill_color=original_task.fill_color,
                date_format=original_task.date_format if hasattr(original_task, 'date_format') else None
            )
            tasks_to_duplicate.append((row_idx, new_task))
            used_ids.add(next_id)
            
            # Find next available ID
            next_id += 1
            while next_id in used_ids:
                next_id += 1
        
        if not tasks_to_duplicate:
            return
        
        # Disable sorting and block signals during duplication
        was_sorting = self.tasks_table.isSortingEnabled()
        self.tasks_table.setSortingEnabled(False)
        self.tasks_table.blockSignals(True)
        
        try:
            # Sort checked rows in reverse order to avoid index shifting issues
            tasks_to_duplicate_sorted = sorted(tasks_to_duplicate, key=lambda x: x[0], reverse=True)
            
            # Insert new rows and populate them
            for orig_row_idx, new_task in tasks_to_duplicate_sorted:
                # Insert new row right after the original
                new_row_idx = orig_row_idx + 1
                self.tasks_table.insertRow(new_row_idx)
                
                # Populate the new row from the Task object
                self._update_table_row_from_task(new_row_idx, new_task)
        finally:
            self.tasks_table.blockSignals(False)
            self.tasks_table.setSortingEnabled(was_sorting)
        
        # Pre-register new tasks in project_data so _task_from_table_row can find their
        # detail-form fields (fill_color, label_content, etc.) during _sync_data
        for _, new_task in tasks_to_duplicate:
            self.project_data.tasks.append(new_task)

        # Sync data to update project_data, then re-sort to restore header rows
        self._sync_data()
        self._sort_tasks_by_swimlane_and_row()
    
    def _move_up(self):
        """Move selected task(s) up by one row (decrease row_number by 1)."""
        # Get all selected rows
        selected_rows = self.tasks_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select task(s) to move up.")
            return
        
        checked_rows = [row.row() for row in selected_rows]
        
        # Block signals and disable sorting during move
        self.tasks_table.blockSignals(True)
        was_sorting = self.tasks_table.isSortingEnabled()
        self.tasks_table.setSortingEnabled(False)
        
        try:
            moved_tasks = []
            row_col = self._get_column_index("Chart Row")

            if row_col is None:
                return

            # Process each checked row
            for row_idx in checked_rows:
                task = self._task_from_table_row(row_idx)
                if task is None:
                    continue

                # Block if already at chart row 1
                if task.row_number <= 1:
                    continue

                # Decrease row_number by 1
                new_row_number = task.row_number - 1

                # Update the row number in the table
                row_item = self.tasks_table.item(row_idx, row_col)
                if row_item:
                    row_item.setText(str(new_row_number))
                    row_item.setData(Qt.UserRole, new_row_number)

                # Update task object
                task.row_number = new_row_number
                moved_tasks.append((row_idx, task))

            if not moved_tasks:
                QMessageBox.information(self, "Cannot Move", "Selected task(s) are already at chart row 1.")
                return

            # Refresh swimlane columns for moved tasks
            for row_idx, _ in moved_tasks:
                self._refresh_swimlane_columns_for_row(row_idx)

        finally:
            self.tasks_table.blockSignals(False)
            self.tasks_table.setSortingEnabled(was_sorting)

        # Sync data first to update project_data with new row_numbers
        self._sync_data()

        # Re-sort after syncing
        self._sort_tasks_by_swimlane_and_row()

        # Keep selection on moved tasks - find the new row index after sorting
        if moved_tasks:
            moved_task_ids = {task.task_id for _, task in moved_tasks}
            id_col = self._get_column_index("ID")

            if id_col is not None:
                for row_idx in range(self.tasks_table.rowCount()):
                    item = self.tasks_table.item(row_idx, id_col)
                    if item:
                        try:
                            task_id = int(item.text())
                            if task_id in moved_task_ids:
                                # Select and scroll to first moved task
                                self.tasks_table.selectRow(row_idx)
                                self.tasks_table.scrollToItem(self.tasks_table.item(row_idx, id_col))
                                break
                        except (ValueError, TypeError):
                            continue
    
    def _move_down(self):
        """Move selected task(s) down by one row (increase row_number by 1)."""
        # Get all selected rows
        selected_rows = self.tasks_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select task(s) to move down.")
            return
        
        checked_rows = [row.row() for row in selected_rows]
        
        # Block signals and disable sorting during move
        self.tasks_table.blockSignals(True)
        was_sorting = self.tasks_table.isSortingEnabled()
        self.tasks_table.setSortingEnabled(False)
        
        try:
            moved_tasks = []
            row_col = self._get_column_index("Chart Row")

            if row_col is None:
                return

            # Process each checked row
            for row_idx in checked_rows:
                task = self._task_from_table_row(row_idx)
                if task is None:
                    continue

                # Increase row_number by 1
                new_row_number = task.row_number + 1

                # Update the row number in the table
                row_item = self.tasks_table.item(row_idx, row_col)
                if row_item:
                    row_item.setText(str(new_row_number))
                    row_item.setData(Qt.UserRole, new_row_number)

                # Update task object
                task.row_number = new_row_number
                moved_tasks.append((row_idx, task))

            if not moved_tasks:
                return

            # Refresh swimlane columns for moved tasks
            for row_idx, _ in moved_tasks:
                self._refresh_swimlane_columns_for_row(row_idx)

        finally:
            self.tasks_table.blockSignals(False)
            self.tasks_table.setSortingEnabled(was_sorting)

        # Sync data first to update project_data with new row_numbers
        self._sync_data()

        # Re-sort after syncing
        self._sort_tasks_by_swimlane_and_row()

        # Keep selection on moved tasks - find the new row index after sorting
        if moved_tasks:
            moved_task_ids = {task.task_id for _, task in moved_tasks}
            id_col = self._get_column_index("ID")

            if id_col is not None:
                for row_idx in range(self.tasks_table.rowCount()):
                    item = self.tasks_table.item(row_idx, id_col)
                    if item:
                        try:
                            task_id = int(item.text())
                            if task_id in moved_task_ids:
                                # Select and scroll to first moved task
                                self.tasks_table.selectRow(row_idx)
                                self.tasks_table.scrollToItem(self.tasks_table.item(row_idx, id_col))
                                break
                        except (ValueError, TypeError):
                            continue

