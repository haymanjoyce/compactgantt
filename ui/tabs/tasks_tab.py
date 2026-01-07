from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                           QHBoxLayout, QComboBox, QHeaderView, QTableWidgetItem, 
                           QMessageBox, QGroupBox, QSizePolicy, QLabel, QGridLayout, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QIntValidator
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import logging
from utils.conversion import normalize_display_date, safe_int, display_to_internal_date, internal_to_display_date
from models import Task

from ui.table_utils import NumericTableWidgetItem, DateTableWidgetItem, add_row, remove_row, CheckBoxWidget, highlight_table_errors, extract_table_data
from .base_tab import BaseTab
from validators.validators import DataValidator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TasksTab(BaseTab):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        self.table_config = app_config.get_table_config("tasks")
        self._selected_row = None  # Track currently selected row
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
        
        add_btn = QPushButton("Add Task")
        add_btn.setToolTip("Add a new task to the chart (Ctrl+N)")
        add_btn.setMinimumWidth(100)
        add_btn.clicked.connect(lambda: add_row(self.tasks_table, "tasks", self.app_config.tables, self, "ID"))
        
        remove_btn = QPushButton("Remove Task")
        remove_btn.setToolTip("Remove selected task(s) from the chart (Delete)")
        remove_btn.setMinimumWidth(100)
        remove_btn.clicked.connect(lambda: remove_row(self.tasks_table, "tasks", 
                                                    self.app_config.tables, self))
        
        duplicate_btn = QPushButton("Duplicate Task")
        duplicate_btn.setToolTip("Duplicate selected task(s) with new IDs")
        duplicate_btn.setMinimumWidth(100)
        duplicate_btn.clicked.connect(self._duplicate_tasks)
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addWidget(duplicate_btn)
        toolbar.addStretch()  # Push buttons to the left
        
        # Create group box for table
        table_group = QGroupBox("Tasks")
        table_group_layout = QVBoxLayout()
        table_group_layout.setSpacing(5)
        table_group_layout.setContentsMargins(5, 10, 5, 5)
        
        # Create table - show: Select, ID, Row, Name, Start Date, Finish Date, Valid
        headers = [col.name for col in self.table_config.columns]
        visible_columns = ["Select", "ID", "Row", "Name", "Start Date", "Finish Date", "Valid"]
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
        self.tasks_table.setSelectionMode(QTableWidget.SingleSelection)  # Single selection for detail form
        self.tasks_table.setShowGrid(True)
        self.tasks_table.verticalHeader().setVisible(False)
        
        # Add bottom border to header row and gridline styling
        self.tasks_table.setStyleSheet(self.app_config.general.table_stylesheet)
        
        # Column sizing
        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Select
        self.tasks_table.setColumnWidth(0, 50)
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # ID
        self.tasks_table.setColumnWidth(1, 50)
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Row
        self.tasks_table.setColumnWidth(2, 50)
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Name
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Start Date
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Finish Date
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Valid

        # Enable horizontal scroll bar
        self.tasks_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tasks_table.setSortingEnabled(True)
        
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
        self.detail_offset = QLineEdit("0")
        self.detail_offset.setToolTip("Additional horizontal offset for outside labels in pixels. Leader line appears when offset > 0.")
        # Add validator to only allow non-negative integers
        validator = QIntValidator(0, 999999, self)
        self.detail_offset.setValidator(validator)
        self.detail_offset.textChanged.connect(self._on_detail_form_changed)
        self.detail_offset.setEnabled(False)
        
        # Fill Color
        color_label = QLabel("Fill Color:")
        color_label.setFixedWidth(LABEL_WIDTH)
        self.detail_fill_color = QComboBox()
        self.detail_fill_color.addItems(["blue", "red", "green", "yellow", "orange", "purple", "gray", "black", "white", "cyan", "magenta", "brown"])
        self.detail_fill_color.setToolTip("Fill color for task bar or milestone circle")
        self.detail_fill_color.currentTextChanged.connect(self._on_detail_form_changed)
        self.detail_fill_color.setEnabled(False)
        
        # Store list of detail form widgets for easy enable/disable
        self._detail_form_widgets = [self.detail_label_content, self.detail_placement, self.detail_offset, self.detail_fill_color]
        
        # Layout form fields vertically (like titles tab)
        layout.addWidget(label_label, 0, 0)
        layout.addWidget(self.detail_label_content, 0, 1)
        layout.addWidget(placement_label, 1, 0)
        layout.addWidget(self.detail_placement, 1, 1)
        layout.addWidget(offset_label, 2, 0)
        layout.addWidget(self.detail_offset, 2, 1)
        layout.addWidget(color_label, 3, 0)
        layout.addWidget(self.detail_fill_color, 3, 1)
        
        layout.setColumnStretch(1, 1)
        
        group.setLayout(layout)
        return group

    def _on_table_selection_changed(self):
        """Handle table selection changes - populate detail form."""
        selected_rows = self.tasks_table.selectionModel().selectedRows()
        if not selected_rows:
            self._selected_row = None
            self._clear_detail_form()
            return
        
        row = selected_rows[0].row()
        self._selected_row = row
        self._populate_detail_form(row)

    def _populate_detail_form(self, row: int):
        """Populate detail form with data from selected task."""
        self._updating_form = True
        
        try:
            # Get Task object directly from project_data
            if row < len(self.project_data.tasks):
                task = self.project_data.tasks[row]
                self.detail_label_content.setCurrentText(task.label_content if task.label_content else "Name only")
                self.detail_placement.setCurrentText(task.label_placement if task.label_placement else "Inside")
                self.detail_offset.setText(str(int(task.label_horizontal_offset)) if task.label_horizontal_offset is not None else "0")
                self.detail_fill_color.setCurrentText(task.fill_color if task.fill_color else "blue")
                # Enable detail form widgets when a valid task is selected
                self._set_detail_form_enabled(self._detail_form_widgets, True)
            else:
                # Use defaults if task doesn't exist
                self.detail_label_content.setCurrentText("Name only")
                self.detail_placement.setCurrentText("Inside")
                self.detail_offset.setText("0")
                self.detail_fill_color.setCurrentText("blue")
                self._set_detail_form_enabled(self._detail_form_widgets, False)
        finally:
            self._updating_form = False

    def _clear_detail_form(self):
        """Clear the detail form when no task is selected."""
        self._updating_form = True
        try:
            self.detail_label_content.setCurrentText("Name only")
            self.detail_placement.setCurrentText("Inside")
            self.detail_offset.setText("0")
            self.detail_fill_color.setCurrentText("blue")
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
        """Get the column index for a given column name (in actual column list, not visible)."""
        for idx, col_config in enumerate(self.table_config.columns):
            if col_config.name == column_name:
                return idx
        return None
    
    def _task_from_table_row(self, row_idx: int) -> Optional[Task]:
        """
        Extract a Task object from a table row.
        Returns None if the row is invalid or incomplete.
        """
        try:
            # Get column indices by name
            id_col = self._get_column_index("ID")
            row_col = self._get_column_index("Row")
            name_col = self._get_column_index("Name")
            start_date_col = self._get_column_index("Start Date")
            finish_date_col = self._get_column_index("Finish Date")
            
            if id_col is None or row_col is None or name_col is None:
                return None
            
            # Map to visible column indices
            id_vis_col = self._reverse_column_mapping.get(id_col)
            row_vis_col = self._reverse_column_mapping.get(row_col)
            name_vis_col = self._reverse_column_mapping.get(name_col)
            start_date_vis_col = self._reverse_column_mapping.get(start_date_col) if start_date_col else None
            finish_date_vis_col = self._reverse_column_mapping.get(finish_date_col) if finish_date_col else None
            
            if id_vis_col is None or row_vis_col is None or name_vis_col is None:
                return None
            
            # Extract ID, Row, Name
            id_item = self.tasks_table.item(row_idx, id_vis_col)
            row_item = self.tasks_table.item(row_idx, row_vis_col)
            name_item = self.tasks_table.item(row_idx, name_vis_col)
            
            if not id_item or not row_item or not name_item:
                return None
            
            task_id = safe_int(id_item.text())
            row_number = safe_int(row_item.text(), 1)
            task_name = name_item.text().strip()
            
            if task_id <= 0:
                return None
            
            # Extract dates (convert from display format to internal format)
            start_date_internal = ""
            start_date_conversion_failed = False
            if start_date_vis_col is not None:
                start_date_item = self.tasks_table.item(row_idx, start_date_vis_col)
                if start_date_item and start_date_item.text().strip():
                    try:
                        start_date_internal = display_to_internal_date(start_date_item.text())
                    except ValueError:
                        start_date_internal = ""
                        start_date_conversion_failed = True  # Track that conversion failed
            
            finish_date_internal = ""
            finish_date_conversion_failed = False
            if finish_date_vis_col is not None:
                finish_date_item = self.tasks_table.item(row_idx, finish_date_vis_col)
                if finish_date_item and finish_date_item.text().strip():
                    try:
                        finish_date_internal = display_to_internal_date(finish_date_item.text())
                    except ValueError:
                        finish_date_internal = ""
                        finish_date_conversion_failed = True  # Track that conversion failed
            
            # Auto-populate missing date field for milestones (if only one date is provided)
            # Only auto-populate if the field was actually empty (not if conversion failed)
            if start_date_internal and not finish_date_internal and not finish_date_conversion_failed:
                finish_date_internal = start_date_internal  # Auto-populate finish date
            elif finish_date_internal and not start_date_internal and not start_date_conversion_failed:
                start_date_internal = finish_date_internal  # Auto-populate start date
            
            # Extract Label Content, Placement, Offset, and Fill Color from detail form if this is the selected row
            # Otherwise, get from existing Task object
            label_content = "Name only"
            label_placement = "Inside"
            label_horizontal_offset = 0.0
            fill_color = "blue"
            
            if row_idx == self._selected_row:
                # Use values from detail form
                if self.detail_label_content:
                    label_content = self.detail_label_content.currentText()
                if self.detail_placement:
                    label_placement = self.detail_placement.currentText()
                if self.detail_offset:
                    # Validate using centralized validator
                    offset_text = self.detail_offset.text()
                    errors = DataValidator.validate_non_negative_integer_string(offset_text, "Label Offset")
                    if errors:
                        # Invalid input - use default value
                        label_horizontal_offset = 0.0
                    else:
                        # Valid input - convert to int then float (model uses float but offset should be integer pixels)
                        label_horizontal_offset = float(int(offset_text)) if offset_text.strip() else 0.0
                if self.detail_fill_color:
                    fill_color = self.detail_fill_color.currentText()
            else:
                # Get from existing Task object if available (look up by task_id)
                existing_task = next((t for t in self.project_data.tasks if t.task_id == task_id), None)
                if existing_task:
                    label_content = existing_task.label_content if hasattr(existing_task, 'label_content') and existing_task.label_content else "Name only"
                    label_placement = existing_task.label_placement
                    label_horizontal_offset = existing_task.label_horizontal_offset if hasattr(existing_task, 'label_horizontal_offset') else 0.0
                    fill_color = existing_task.fill_color if hasattr(existing_task, 'fill_color') else "blue"
            
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
                fill_color=fill_color
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
        # Get column indices by name
        id_col = self._get_column_index("ID")
        row_col = self._get_column_index("Row")
        name_col = self._get_column_index("Name")
        start_date_col = self._get_column_index("Start Date")
        finish_date_col = self._get_column_index("Finish Date")
        valid_col = self._get_column_index("Valid")
        
        # Map to visible column indices
        id_vis_col = self._reverse_column_mapping.get(id_col) if id_col is not None else None
        row_vis_col = self._reverse_column_mapping.get(row_col) if row_col is not None else None
        name_vis_col = self._reverse_column_mapping.get(name_col) if name_col is not None else None
        start_date_vis_col = self._reverse_column_mapping.get(start_date_col) if start_date_col is not None else None
        finish_date_vis_col = self._reverse_column_mapping.get(finish_date_col) if finish_date_col is not None else None
        valid_vis_col = self._reverse_column_mapping.get(valid_col) if valid_col is not None else None
        
        # Block signals to prevent recursive updates
        was_blocked = self.tasks_table.signalsBlocked()
        self.tasks_table.blockSignals(True)
        try:
            # Update ID column
            if id_vis_col is not None:
                item = self.tasks_table.item(row_idx, id_vis_col)
                if item:
                    item.setText(str(task.task_id))
                    item.setData(Qt.UserRole, task.task_id)
                else:
                    item = NumericTableWidgetItem(str(task.task_id))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                    item.setData(Qt.UserRole, task.task_id)
                    self.tasks_table.setItem(row_idx, id_vis_col, item)
            
            # Update Row column
            if row_vis_col is not None:
                item = self.tasks_table.item(row_idx, row_vis_col)
                if item:
                    item.setText(str(task.row_number))
                    item.setData(Qt.UserRole, task.row_number)
                else:
                    item = NumericTableWidgetItem(str(task.row_number))
                    item.setData(Qt.UserRole, task.row_number)
                    self.tasks_table.setItem(row_idx, row_vis_col, item)
            
            # Update Name column
            if name_vis_col is not None:
                item = self.tasks_table.item(row_idx, name_vis_col)
                if item:
                    item.setText(task.task_name)
                else:
                    item = QTableWidgetItem(task.task_name)
                    self.tasks_table.setItem(row_idx, name_vis_col, item)
            
            # Update Start Date column
            if start_date_vis_col is not None:
                start_date_display = internal_to_display_date(task.start_date)
                item = self.tasks_table.item(row_idx, start_date_vis_col)
                if item:
                    item.setText(start_date_display)
                    try:
                        if start_date_display and start_date_display.strip():
                            date_obj = datetime.strptime(start_date_display, "%d/%m/%Y")
                            item.setData(Qt.UserRole, date_obj)
                        else:
                            item.setData(Qt.UserRole, None)
                    except (ValueError, AttributeError):
                        item.setData(Qt.UserRole, None)
                else:
                    item = DateTableWidgetItem(start_date_display)
                    try:
                        if start_date_display and start_date_display.strip():
                            date_obj = datetime.strptime(start_date_display, "%d/%m/%Y")
                            item.setData(Qt.UserRole, date_obj)
                        else:
                            item.setData(Qt.UserRole, None)
                    except (ValueError, AttributeError):
                        item.setData(Qt.UserRole, None)
                    self.tasks_table.setItem(row_idx, start_date_vis_col, item)
            
            # Update Finish Date column
            if finish_date_vis_col is not None:
                finish_date_display = internal_to_display_date(task.finish_date)
                item = self.tasks_table.item(row_idx, finish_date_vis_col)
                if item:
                    item.setText(finish_date_display)
                    try:
                        if finish_date_display and finish_date_display.strip():
                            date_obj = datetime.strptime(finish_date_display, "%d/%m/%Y")
                            item.setData(Qt.UserRole, date_obj)
                        else:
                            item.setData(Qt.UserRole, None)
                    except (ValueError, AttributeError):
                        item.setData(Qt.UserRole, None)
                else:
                    item = DateTableWidgetItem(finish_date_display)
                    try:
                        if finish_date_display and finish_date_display.strip():
                            date_obj = datetime.strptime(finish_date_display, "%d/%m/%Y")
                            item.setData(Qt.UserRole, date_obj)
                        else:
                            item.setData(Qt.UserRole, None)
                    except (ValueError, AttributeError):
                        item.setData(Qt.UserRole, None)
                    self.tasks_table.setItem(row_idx, finish_date_vis_col, item)
            
            # Update Valid column (calculate valid status)
            if valid_vis_col is not None:
                used_ids = {t.task_id for t in self.project_data.tasks if t.task_id != task.task_id}
                row_errors = self.project_data.validator.validate_task(task, used_ids)
                valid_status = "No" if row_errors else "Yes"
                
                item = self.tasks_table.item(row_idx, valid_vis_col)
                if item:
                    item.setText(valid_status)
                else:
                    item = QTableWidgetItem(valid_status)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                    self.tasks_table.setItem(row_idx, valid_vis_col, item)
        finally:
            self.tasks_table.blockSignals(was_blocked)
    
    def _on_item_changed(self, item):
        """Handle item changes - update UserRole for numeric and date columns to maintain proper sorting."""
        logging.debug("_on_item_changed: START")
        
        # Skip auto-population during initialization to preserve invalid dates
        if self._initializing:
            return
        
        # CRITICAL: Disconnect signal BEFORE modifying item to prevent infinite loop
        was_connected = False
        try:
            self.tasks_table.itemChanged.disconnect(self._on_item_changed)
            was_connected = True
            logging.debug("_on_item_changed: Disconnected signal at start")
        except:
            pass  # Signal might not be connected
        
        try:
            if item is None:
                logging.debug("_on_item_changed: item is None, returning")
                return
            
            col = item.column()
            row = item.row()
            logging.debug(f"_on_item_changed: row={row}, col={col}")
            
            headers = [col.name for col in self.table_config.columns]
            
            # Find which actual column this visible column maps to
            actual_col_idx = None
            for vis_idx, act_idx in self._column_mapping.items():
                if vis_idx == col:
                    actual_col_idx = act_idx
                    break
            
            if actual_col_idx is None:
                logging.debug(f"_on_item_changed: actual_col_idx is None for col={col}, returning")
                return
            
            col_name = headers[actual_col_idx] if actual_col_idx < len(headers) else ""
            logging.debug(f"_on_item_changed: col_name={col_name}, actual_col_idx={actual_col_idx}")
            
            # Update UserRole for date columns (Start Date, Finish Date)
            if col_name in ["Start Date", "Finish Date"]:
                logging.debug(f"_on_item_changed: Processing date column: {col_name}")
                try:
                    val_str = item.text().strip()
                    logging.debug(f"_on_item_changed: date value='{val_str}'")
                    if val_str:
                        try:
                            # Use normalize_display_date to handle flexible formats
                            normalized = normalize_display_date(val_str)
                            date_obj = datetime.strptime(normalized, "%d/%m/%Y")
                            logging.debug(f"_on_item_changed: Parsed date successfully: {date_obj}")
                            
                            # Auto-populate the other date field for milestones (if only one date is provided)
                            other_col_name = "Finish Date" if col_name == "Start Date" else "Start Date"
                            other_col_idx = self._get_column_index(other_col_name)
                            if other_col_idx is not None:
                                other_col_vis_idx = self._reverse_column_mapping.get(other_col_idx)
                                if other_col_vis_idx is not None:
                                    other_date_item = self.tasks_table.item(row, other_col_vis_idx)
                                    if other_date_item:
                                        other_date_text = other_date_item.text().strip()
                                        if not other_date_text:
                                            # Other date field is empty - auto-populate it with the same date
                                            other_date_item.setText(normalized)
                                            other_date_item.setData(Qt.UserRole, date_obj)
                                            logging.debug(f"_on_item_changed: Auto-populated {other_col_name} with {normalized}")
                                    else:
                                        # Other date item doesn't exist - create it
                                        other_date_item = DateTableWidgetItem(normalized)
                                        other_date_item.setData(Qt.UserRole, date_obj)
                                        self.tasks_table.setItem(row, other_col_vis_idx, other_date_item)
                                        logging.debug(f"_on_item_changed: Created and auto-populated {other_col_name} with {normalized}")
                        except ValueError as e:
                            logging.debug(f"_on_item_changed: Date parsing failed: {e}")
                            date_obj = None
                            # Date is invalid - ensure validation will catch this
                            # The invalid text remains in the cell, which will cause
                            # _task_from_table_row() to set the date to "" when converting
                        
                        # Check if UserRole already has the same value to avoid unnecessary updates
                        current_role = item.data(Qt.UserRole)
                        if current_role != date_obj:
                            logging.debug(f"_on_item_changed: Setting UserRole with date_obj={date_obj} (was {current_role})")
                            item.setData(Qt.UserRole, date_obj)
                            logging.debug(f"_on_item_changed: UserRole set successfully")
                        else:
                            logging.debug(f"_on_item_changed: UserRole already set to {date_obj}, skipping")
                    else:
                        logging.debug("_on_item_changed: Empty date value, setting UserRole to None")
                        item.setData(Qt.UserRole, None)
                except (ValueError, AttributeError, Exception) as e:
                    logging.error(f"_on_item_changed: Error parsing date: {e}", exc_info=True)
                    item.setData(Qt.UserRole, None)
            # Update UserRole for numeric columns (ID, Row)
            elif actual_col_idx == 1:  # Task ID
                logging.debug("_on_item_changed: Processing Task ID column")
                # Ensure Task ID is read-only with gray background
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))  # Gray background
                try:
                    val_str = item.text().strip()
                    item.setData(Qt.UserRole, int(val_str) if val_str else 0)
                except (ValueError, AttributeError):
                    item.setData(Qt.UserRole, 0)
            elif actual_col_idx == 2:  # Row number
                logging.debug("_on_item_changed: Processing Row column")
                try:
                    val_str = item.text().strip()
                    item.setData(Qt.UserRole, int(val_str) if val_str else 1)
                except (ValueError, AttributeError):
                    item.setData(Qt.UserRole, 1)
            
            # Don't trigger sync for Valid column changes (it's read-only and auto-calculated)
            if actual_col_idx < len(headers) and headers[actual_col_idx] != "Valid":
                logging.debug(f"_on_item_changed: Column is not Valid, checking if should sync")
                # Trigger sync with error handling to prevent crashes
                if not self._syncing:
                    logging.debug("_on_item_changed: Not syncing, proceeding with sync")
                    try:
                        self._syncing = True
                        logging.debug("_on_item_changed: Set _syncing=True")
                        
                        try:
                            logging.debug("_on_item_changed: Calling _sync_data_if_not_initializing")
                            self._sync_data_if_not_initializing()
                            logging.debug("_on_item_changed: _sync_data_if_not_initializing completed")
                        except Exception as e:
                            logging.error(f"_on_item_changed: Error in sync: {e}", exc_info=True)
                    finally:
                        self._syncing = False
                        logging.debug("_on_item_changed: Set _syncing=False")
                else:
                    logging.debug("_on_item_changed: Already syncing, skipping")
            else:
                logging.debug("_on_item_changed: Column is Valid, skipping sync")
            
            logging.debug("_on_item_changed: END (success)")
        except Exception as e:
            logging.error(f"_on_item_changed: Unexpected error: {e}", exc_info=True)
            raise
        finally:
            # Reconnect itemChanged signal
            if was_connected:
                logging.debug("_on_item_changed: Reconnecting itemChanged signal")
                try:
                    self.tasks_table.itemChanged.connect(self._on_item_changed)
                    logging.debug("_on_item_changed: itemChanged signal reconnected")
                except Exception as e:
                    logging.debug(f"_on_item_changed: Failed to reconnect signal: {e}")
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
            # Add checkbox first (Select column)
            if 0 in self._column_mapping:  # Select column
                checkbox_widget = CheckBoxWidget()
                self.tasks_table.setCellWidget(row_idx, 0, checkbox_widget)

            # Use helper method to populate row from Task object
            task = tasks[row_idx]
            self._update_table_row_from_task(row_idx, task)
        
        # Sort by ID by default
        headers = [col.name for col in self.table_config.columns]
        id_col_vis_idx = None
        for vis_idx, actual_idx in self._column_mapping.items():
            if headers[actual_idx] == "ID":
                id_col_vis_idx = vis_idx
                break
        if id_col_vis_idx is not None:
            self.tasks_table.sortItems(id_col_vis_idx, Qt.AscendingOrder)
        
        # Ensure all read-only cells have proper styling
        self._ensure_read_only_styling()
        
        self._initializing = False
        
        # Disable detail form if no tasks exist or no selection
        if row_count == 0 or self._selected_row is None:
            self._clear_detail_form()
        
        # Calculate and update Valid column for all rows
        self._update_valid_column_only()

    def _sync_data(self):
        self._sync_data_impl()

    def _sync_data_impl(self):
        """Extract data from table and update project_data using Task objects directly."""
        logging.debug("_sync_data_impl: START")
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
            
            logging.debug("_sync_data_impl: END (success)")
        except Exception as e:
            logging.error(f"Error in _sync_data_impl: {e}", exc_info=True)

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            logging.debug("Calling _sync_data from itemChanged")
            self._sync_data()
    
    def _ensure_read_only_styling(self):
        """Ensure all read-only cells (Task ID, Valid) have proper styling."""
        headers = [col.name for col in self.table_config.columns]
        id_col_vis_idx = None
        valid_col_vis_idx = None
        
        for vis_idx, act_idx in self._column_mapping.items():
            if act_idx == 1:  # Task ID column
                id_col_vis_idx = vis_idx
            elif act_idx < len(headers) and headers[act_idx] == "Valid":
                valid_col_vis_idx = vis_idx
        
        if id_col_vis_idx is not None:
            for row in range(self.tasks_table.rowCount()):
                item = self.tasks_table.item(row, id_col_vis_idx)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
        
        if valid_col_vis_idx is not None:
            for row in range(self.tasks_table.rowCount()):
                item = self.tasks_table.item(row, valid_col_vis_idx)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(self.app_config.general.read_only_bg_color))

    def _update_valid_column_only(self):
        """Update only the Valid column without reloading the entire table."""
        logging.debug("_update_valid_column_only: START")
        try:
            # Check if table is valid and has rows
            if not self.tasks_table or self.tasks_table.rowCount() == 0:
                logging.debug("_update_valid_column_only: Table invalid or empty, returning")
                return
            
            # Find Valid column visible index
            valid_col = self._get_column_index("Valid")
            valid_col_vis_idx = self._reverse_column_mapping.get(valid_col) if valid_col is not None else None
            
            if valid_col_vis_idx is None:
                logging.debug("_update_valid_column_only: Valid column not found, returning")
                return
            
            # Create a mapping of task_id to task for quick lookup
            task_map = {task.task_id: task for task in self.project_data.tasks}
            
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
                    # Get ID column to extract task_id from each row
                    id_col = self._get_column_index("ID")
                    id_vis_col = self._reverse_column_mapping.get(id_col) if id_col is not None else None
                    
                    if id_vis_col is None:
                        return
                    
                    # Build used_ids set from all tasks for validation
                    used_ids: Set[int] = set(task.task_id for task in self.project_data.tasks)
                    
                    # For each table row, find the corresponding task by task_id
                    for row_idx in range(self.tasks_table.rowCount()):
                        # Extract task_id from table
                        id_item = self.tasks_table.item(row_idx, id_vis_col)
                        if not id_item:
                            continue
                        
                        try:
                            task_id = safe_int(id_item.text())
                            if task_id <= 0:
                                continue
                        except (ValueError, TypeError):
                            continue
                        
                        # Find the task in project_data by task_id
                        task = task_map.get(task_id)
                        if not task:
                            continue
                        
                        # Calculate valid status (exclude current task from used_ids for uniqueness check)
                        task_used_ids = used_ids - {task.task_id}
                        row_errors = self.project_data.validator.validate_task(task, task_used_ids)
                        valid_status = "No" if row_errors else "Yes"
                        
                        # Update the Valid cell
                        item = self.tasks_table.item(row_idx, valid_col_vis_idx)
                        if item:
                            item.setText(str(valid_status))
                        else:
                            item = QTableWidgetItem(str(valid_status))
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                            self.tasks_table.setItem(row_idx, valid_col_vis_idx, item)
                finally:
                    # Reconnect itemChanged signal
                    if was_connected:
                        try:
                            self.tasks_table.itemChanged.connect(self._on_item_changed)
                        except Exception:
                            pass
            finally:
                self.tasks_table.blockSignals(was_blocked)
            
            logging.debug("_update_valid_column_only: END (success)")
        except Exception as e:
            logging.error(f"_update_valid_column_only: Error: {e}", exc_info=True)

    def _extract_table_data(self) -> List[List[str]]:
        # This is now handled in _sync_data_impl
        return []

    def _duplicate_tasks(self):
        """Duplicate selected tasks with new IDs."""
        # Get all checked rows
        checked_rows = []
        for row in range(self.tasks_table.rowCount()):
            checkbox_widget = self.tasks_table.cellWidget(row, 0)
            if checkbox_widget and isinstance(checkbox_widget, CheckBoxWidget):
                if checkbox_widget.checkbox.isChecked():
                    checked_rows.append(row)
        
        if not checked_rows:
            QMessageBox.information(self, "No Selection", "Please select task(s) to duplicate by checking their checkboxes.")
            return
        
        # Get all used task IDs from project_data
        used_ids = {task.task_id for task in self.project_data.tasks}
        
        # Also check IDs currently in the table
        id_col = self._get_column_index("ID")
        id_vis_col = self._reverse_column_mapping.get(id_col) if id_col is not None else None
        if id_vis_col is not None:
            for row in range(self.tasks_table.rowCount()):
                item = self.tasks_table.item(row, id_vis_col)
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
                task_name=original_task.task_name,
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
                fill_color=original_task.fill_color
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
                
                # Add checkbox
                checkbox_widget = CheckBoxWidget()
                self.tasks_table.setCellWidget(new_row_idx, 0, checkbox_widget)
                
                # Populate the new row from the Task object
                self._update_table_row_from_task(new_row_idx, new_task)
        finally:
            self.tasks_table.blockSignals(False)
            self.tasks_table.setSortingEnabled(was_sorting)
        
        # Sync data to update project_data
        self._sync_data()

    def _extract_row_data_from_table(self, row_idx):
        """Extract full row data from table for a given row index."""
        headers = [col.name for col in self.table_config.columns]
        row_data_column_map = {
            "ID": 0,
            "Row": 1,
            "Name": 2,
            "Start Date": 3,
            "Finish Date": 4,
            "Label": 5,
            "Placement": 6,
            "Valid": 7
        }
        
        full_row = []
        # Reconstruct row data from visible columns (skip checkbox column)
        for actual_col_idx in range(1, len(headers)):  # Skip Select column (index 0)
            col_name = headers[actual_col_idx]
            
            if actual_col_idx in self._reverse_column_mapping:
                # Visible column - get from table
                vis_col_idx = self._reverse_column_mapping[actual_col_idx]
                item = self.tasks_table.item(row_idx, vis_col_idx)
                widget = self.tasks_table.cellWidget(row_idx, vis_col_idx)
                
                if widget and isinstance(widget, QComboBox):
                    full_row.append(widget.currentText())
                elif item:
                    full_row.append(item.text())
                else:
                    full_row.append("")
            else:
                # Hidden column (Label, Placement) - get from detail form if this is selected row
                if row_idx == self._selected_row:
                    if col_name == "Label":
                        full_row.append(self.detail_label.currentText())
                    elif col_name == "Placement":
                        full_row.append(self.detail_placement.currentText())
                    else:
                        full_row.append("")
                else:
                    # Get from stored data
                    table_data = self.project_data.get_table_data("tasks")
                    if row_idx < len(table_data):
                        stored_row = table_data[row_idx]
                        if col_name in row_data_column_map:
                            value_idx = row_data_column_map[col_name]
                            if value_idx < len(stored_row):
                                full_row.append(stored_row[value_idx])
                            else:
                                full_row.append("")
                        else:
                            full_row.append("")
                    else:
                        full_row.append("")
        
        return full_row
 