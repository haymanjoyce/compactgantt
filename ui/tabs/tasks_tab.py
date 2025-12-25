from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                           QHBoxLayout, QComboBox, QHeaderView, QTableWidgetItem, 
                           QMessageBox, QGroupBox, QSizePolicy, QLabel, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from typing import List, Dict, Any
from datetime import datetime
import logging

# Read-only cell background color (light gray)
READ_ONLY_BG = QColor(240, 240, 240)
from ui.table_utils import NumericTableWidgetItem, DateTableWidgetItem, add_row, remove_row, CheckBoxWidget, highlight_table_errors, extract_table_data
from .base_tab import BaseTab

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TasksTab(BaseTab):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        self.table_config = app_config.get_table_config("tasks")
        self._selected_row = None  # Track currently selected row
        self._updating_form = False  # Prevent circular updates
        self._syncing = False  # Prevent recursive syncs
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
        
        # Add bottom border to header row
        self.tasks_table.setStyleSheet("""
            QHeaderView::section {
                border-bottom: 1px solid #c0c0c0;
                border-top: none;
                border-left: none;
                border-right: none;
            }
        """)
        
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
        
        # Label (Show/Hide)
        label_label = QLabel("Label:")
        label_label.setFixedWidth(LABEL_WIDTH)
        self.detail_label = QComboBox()
        self.detail_label.addItems(["No", "Yes"])
        self.detail_label.setToolTip("Show task label (No = Hide, Yes = Show)")
        self.detail_label.currentTextChanged.connect(self._on_detail_form_changed)
        
        # Placement
        placement_label = QLabel("Placement:")
        placement_label.setFixedWidth(LABEL_WIDTH)
        self.detail_placement = QComboBox()
        self.detail_placement.addItems(["Inside", "Outside"])
        self.detail_placement.setToolTip("Label placement (Inside or Outside task bar)")
        self.detail_placement.currentTextChanged.connect(self._on_detail_form_changed)
        
        # Layout form fields vertically (like titles tab)
        layout.addWidget(label_label, 0, 0)
        layout.addWidget(self.detail_label, 0, 1)
        layout.addWidget(placement_label, 1, 0)
        layout.addWidget(self.detail_placement, 1, 1)
        
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
            # Get data from project_data for the selected row
            table_data = self.project_data.get_table_data("tasks")
            if row < len(table_data):
                row_data = table_data[row]
                # row_data structure: [ID, Row, Name, Start Date, Finish Date, Label, Placement]
                if len(row_data) >= 7:
                    self.detail_label.setCurrentText(str(row_data[5]) if row_data[5] else "Yes")
                    self.detail_placement.setCurrentText(str(row_data[6]) if row_data[6] else "Inside")
        finally:
            self._updating_form = False

    def _clear_detail_form(self):
        """Clear the detail form when no task is selected."""
        self._updating_form = True
        try:
            self.detail_label.setCurrentText("Yes")
            self.detail_placement.setCurrentText("Inside")
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
    
    def _on_item_changed(self, item):
        """Handle item changes - update UserRole for numeric and date columns to maintain proper sorting."""
        logging.debug("_on_item_changed: START")
        
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
                        # Try parsing with flexible date format (handles both single and double digit days/months)
                        try:
                            date_obj = datetime.strptime(val_str, "%d/%m/%Y")
                            logging.debug(f"_on_item_changed: Parsed date successfully: {date_obj}")
                        except ValueError as ve:
                            logging.debug(f"_on_item_changed: First parse failed: {ve}, trying normalization")
                            # Try alternative format in case of single digits
                            try:
                                # Normalize single-digit days/months to double digits
                                parts = val_str.split('/')
                                if len(parts) == 3:
                                    day = parts[0].zfill(2)
                                    month = parts[1].zfill(2)
                                    year = parts[2]
                                    normalized = f"{day}/{month}/{year}"
                                    logging.debug(f"_on_item_changed: Normalized date: {normalized}")
                                    date_obj = datetime.strptime(normalized, "%d/%m/%Y")
                                    logging.debug(f"_on_item_changed: Parsed normalized date: {date_obj}")
                                else:
                                    logging.debug(f"_on_item_changed: Invalid parts count: {len(parts)}")
                                    date_obj = None
                            except (ValueError, IndexError) as e:
                                logging.debug(f"_on_item_changed: Normalization failed: {e}")
                                date_obj = None
                        
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
                item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
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
        table_data = self.project_data.get_table_data("tasks")
        row_count = max(len(table_data), self.table_config.min_rows)
        self.tasks_table.setRowCount(row_count)
        self._initializing = True

        headers = [col.name for col in self.table_config.columns]
        
        # Create a mapping from column name to index in row_data from get_table_data
        # row_data structure: [ID, Row, Name, Start Date, Finish Date, Label, Placement, Valid]
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
        
        for row_idx in range(row_count):
            # Add checkbox first (Select column)
            if 0 in self._column_mapping:  # Select column
                checkbox_widget = CheckBoxWidget()
                self.tasks_table.setCellWidget(row_idx, 0, checkbox_widget)

            if row_idx < len(table_data):
                row_data = table_data[row_idx]
                # Populate visible columns
                for vis_col_idx, actual_col_idx in self._column_mapping.items():
                    if actual_col_idx == 0:  # Skip Select, already handled
                        continue
                    
                    col_config = self.table_config.columns[actual_col_idx]
                    col_name = col_config.name
                    
                    # Map column name to row_data index
                    if col_name in row_data_column_map:
                        value_idx = row_data_column_map[col_name]
                        if value_idx < len(row_data):
                            value = row_data[value_idx]
                        else:
                            value = ""
                    else:
                        value = ""
                    
                    # Create widget/item for this column (regardless of whether it was in the map)
                    if col_config.widget_type == "combo":
                        combo = QComboBox()
                        combo.addItems(col_config.combo_items)
                        combo.setCurrentText(str(value) or col_config.combo_items[0])
                        combo.currentTextChanged.connect(self._sync_data_if_not_initializing)
                        self.tasks_table.setCellWidget(row_idx, vis_col_idx, combo)
                    else:
                        # Handle text and numeric columns
                        if col_name in ["Start Date", "Finish Date"]:
                            # Date columns - use DateTableWidgetItem for chronological sorting
                            item = DateTableWidgetItem(str(value))
                            # Set UserRole with datetime object for sorting
                            try:
                                if value and str(value).strip():
                                    # Convert from display format (dd/mm/yyyy) to datetime
                                    date_obj = datetime.strptime(str(value).strip(), "%d/%m/%Y")
                                    item.setData(Qt.UserRole, date_obj)
                                else:
                                    item.setData(Qt.UserRole, None)
                            except (ValueError, AttributeError):
                                item.setData(Qt.UserRole, None)
                        elif actual_col_idx in (1, 2):  # ID, Row are numeric
                            item = NumericTableWidgetItem(str(value))
                        else:
                            item = QTableWidgetItem(str(value))
                        
                        if actual_col_idx == 1:  # Task ID read-only
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                            # Ensure UserRole is set for numeric sorting
                            try:
                                item.setData(Qt.UserRole, int(str(value).strip()) if str(value).strip() else 0)
                            except (ValueError, AttributeError):
                                item.setData(Qt.UserRole, 0)
                        elif actual_col_idx == 2:  # Row number numeric
                            # Ensure UserRole is set for numeric sorting
                            try:
                                item.setData(Qt.UserRole, int(str(value).strip()) if str(value).strip() else 1)
                            except (ValueError, AttributeError):
                                item.setData(Qt.UserRole, 1)
                        elif col_name == "Valid":  # Valid column - read-only text
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                        
                        self.tasks_table.setItem(row_idx, vis_col_idx, item)
            else:
                # New row - use defaults
                context = {
                    "max_task_id": len(table_data)  # Maximum existing task ID, not len + row_idx
                }
                defaults = self.table_config.default_generator(row_idx, context)
                # defaults structure: [False, ID, Row, Name, Start Date, Finish Date, Label, Placement]
                # defaults[0] is checkbox, defaults[1] is ID (actual_col_idx 1), etc.
                
                for vis_col_idx, actual_col_idx in self._column_mapping.items():
                    if actual_col_idx == 0:  # Skip Select
                        continue
                    
                    # defaults includes checkbox at 0, so actual_col_idx maps directly to defaults[actual_col_idx]
                    default_idx = actual_col_idx
                    if default_idx < len(defaults):
                        default = defaults[default_idx]
                        col_config = self.table_config.columns[actual_col_idx]
                        col_name = col_config.name
                        
                        if col_config.widget_type == "combo":
                            combo = QComboBox()
                            combo.addItems(col_config.combo_items)
                            combo.setCurrentText(str(default))
                            combo.currentTextChanged.connect(self._sync_data_if_not_initializing)
                            self.tasks_table.setCellWidget(row_idx, vis_col_idx, combo)
                        else:
                            if col_name in ["Start Date", "Finish Date"]:
                                # Date columns - use DateTableWidgetItem for chronological sorting
                                item = DateTableWidgetItem(str(default))
                                # Set UserRole with datetime object for sorting
                                try:
                                    if default and str(default).strip():
                                        date_obj = datetime.strptime(str(default).strip(), "%d/%m/%Y")
                                        item.setData(Qt.UserRole, date_obj)
                                    else:
                                        item.setData(Qt.UserRole, None)
                                except (ValueError, AttributeError):
                                    item.setData(Qt.UserRole, None)
                            elif actual_col_idx in (1, 2, 3):
                                item = NumericTableWidgetItem(str(default))
                            else:
                                item = QTableWidgetItem(str(default))
                            
                            if actual_col_idx == 1:  # Task ID read-only
                                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                                item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                                # Ensure UserRole is set for numeric sorting
                                try:
                                    item.setData(Qt.UserRole, int(str(default).strip()) if str(default).strip() else 0)
                                except (ValueError, AttributeError):
                                    item.setData(Qt.UserRole, 0)
                            elif actual_col_idx == 2:  # Row number numeric
                                # Ensure UserRole is set for numeric sorting
                                try:
                                    item.setData(Qt.UserRole, int(str(default).strip()) if str(default).strip() else 1)
                                except (ValueError, AttributeError):
                                    item.setData(Qt.UserRole, 1)
                            
                            self.tasks_table.setItem(row_idx, vis_col_idx, item)

        # Find the ID column for sorting (default sort by ID)
        id_col_vis_idx = None
        for vis_idx, actual_idx in self._column_mapping.items():
            if headers[actual_idx] == "ID":
                id_col_vis_idx = vis_idx
                break
        if id_col_vis_idx is not None:
            self.tasks_table.sortByColumn(id_col_vis_idx, Qt.AscendingOrder)
        
        # Ensure all read-only cells have proper styling
        self._ensure_read_only_styling()
        
        self._initializing = False
        self._sync_data()

    def _sync_data(self):
        self._sync_data_impl()

    def _sync_data_impl(self):
        """Synchronize table data with project_data."""
        logging.debug("_sync_data_impl: START")
        try:
            logging.debug("Starting _sync_data in TasksTab")
            
            # Reconstruct full table data from visible columns + detail form
            headers = [col.name for col in self.table_config.columns]
            full_table_data = []
            
            # Create mapping from column name to index in get_table_data result
            row_data_column_map = {
                "ID": 0,
                "Row": 1,
                "Name": 2,
                "Start Date": 3,
                "Finish Date": 4,
                "Label": 5,
                "Placement": 6
            }
            
            for row in range(self.tasks_table.rowCount()):
                full_row = []
                
                # NOTE: update_from_table expects data WITHOUT checkbox column
                # Column order expected: ID, Row, Name, Start Date, Finish Date, Label, Placement, Valid
                
                # Reconstruct row data from visible columns (skip checkbox column)
                for actual_col_idx in range(1, len(headers)):  # Skip Select column (index 0)
                    col_name = headers[actual_col_idx]
                    
                    if actual_col_idx in self._reverse_column_mapping:
                        # Visible column - get from table
                        vis_col_idx = self._reverse_column_mapping[actual_col_idx]
                        item = self.tasks_table.item(row, vis_col_idx)
                        widget = self.tasks_table.cellWidget(row, vis_col_idx)
                        
                        if widget and isinstance(widget, QComboBox):
                            full_row.append(widget.currentText())
                        elif item:
                            full_row.append(item.text())
                        else:
                            full_row.append("")
                    else:
                        # Hidden column (Label, Placement) - get from detail form if this is selected row
                        if row == self._selected_row:
                            if col_name == "Label":
                                full_row.append(self.detail_label.currentText())
                            elif col_name == "Placement":
                                full_row.append(self.detail_placement.currentText())
                            else:
                                full_row.append("")
                        else:
                            # Not selected row - get from stored data or defaults
                            table_data = self.project_data.get_table_data("tasks")
                            if row < len(table_data):
                                # Row exists in stored data - get from there
                                stored_row = table_data[row]
                                if col_name in row_data_column_map:
                                    value_idx = row_data_column_map[col_name]
                                    if value_idx < len(stored_row):
                                        full_row.append(stored_row[value_idx])
                                    else:
                                        full_row.append("")
                                else:
                                    full_row.append("")
                            else:
                                # New row created from defaults - get Label and Placement from defaults
                                context = {
                                    "max_task_id": len(table_data) + row,
                                }
                                defaults = self.table_config.default_generator(row, context)
                                # defaults structure: [False, ID, Row, Name, Start Date, Finish Date, Label, Placement, Valid]
                                # defaults[0] is checkbox, so Label is at defaults[6], Placement is at defaults[7], Valid is at defaults[8]
                                if col_name == "Label":
                                    if len(defaults) > 6:
                                        full_row.append(str(defaults[6]))
                                    else:
                                        full_row.append("Yes")
                                elif col_name == "Placement":
                                    if len(defaults) > 7:
                                        full_row.append(str(defaults[7]))
                                    else:
                                        full_row.append("Inside")
                                elif col_name == "Valid":
                                    if len(defaults) > 8:
                                        full_row.append(str(defaults[8]))
                                    else:
                                        full_row.append("Yes")
                                else:
                                    full_row.append("")
                
                full_table_data.append(full_row)
            
            logging.debug("_sync_data_impl: About to call update_from_table")
            errors = self.project_data.update_from_table("tasks", full_table_data)
            logging.debug(f"_sync_data_impl: update_from_table completed, errors={errors}")
            
            # No longer highlight errors - Valid column shows validation status
            # Update only the Valid column without reloading the entire table
            logging.debug("_sync_data_impl: About to call _update_valid_column_only")
            self._update_valid_column_only()
            logging.debug("_sync_data_impl: _update_valid_column_only completed")
            
            logging.debug("_sync_data in TasksTab completed")
            logging.debug("_sync_data_impl: END (success)")
        except Exception as e:
            logging.error(f"Error in _sync_data_impl: {e}", exc_info=True)
            # Don't crash - log and continue

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
                    item.setBackground(QBrush(READ_ONLY_BG))
        
        if valid_col_vis_idx is not None:
            for row in range(self.tasks_table.rowCount()):
                item = self.tasks_table.item(row, valid_col_vis_idx)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(READ_ONLY_BG))

    def _update_valid_column_only(self):
        """Update only the Valid column without reloading the entire table."""
        logging.debug("_update_valid_column_only: START")
        try:
            # Check if table is valid and has rows
            if not self.tasks_table or self.tasks_table.rowCount() == 0:
                logging.debug("_update_valid_column_only: Table invalid or empty, returning")
                return
                
            logging.debug(f"_update_valid_column_only: Table has {self.tasks_table.rowCount()} rows")
            
            # Get updated data from project_data
            table_data = self.project_data.get_table_data("tasks")
            logging.debug(f"_update_valid_column_only: Got {len(table_data)} rows from project_data")
            
            headers = [col.name for col in self.table_config.columns]
            
            # Find Valid column visible index
            valid_col_vis_idx = None
            for vis_idx, act_idx in self._column_mapping.items():
                if act_idx < len(headers) and headers[act_idx] == "Valid":
                    valid_col_vis_idx = vis_idx
                    break
            
            if valid_col_vis_idx is None:
                logging.debug("_update_valid_column_only: Valid column not found, returning")
                return
            
            logging.debug(f"_update_valid_column_only: Valid column visible index: {valid_col_vis_idx}")
            
            # Block signals to prevent recursive updates
            was_blocked = self.tasks_table.signalsBlocked()
            logging.debug(f"_update_valid_column_only: Blocking signals (was_blocked={was_blocked})")
            self.tasks_table.blockSignals(True)
            
            try:
                # Temporarily disconnect itemChanged to prevent issues
                was_connected = False
                logging.debug("_update_valid_column_only: Disconnecting itemChanged signal")
                try:
                    self.tasks_table.itemChanged.disconnect(self._on_item_changed)
                    was_connected = True
                    logging.debug("_update_valid_column_only: itemChanged signal disconnected")
                except Exception as e:
                    logging.debug(f"_update_valid_column_only: Failed to disconnect signal: {e}")
                    pass  # Signal might not be connected
                
                try:
                    # Update Valid column for each row
                    logging.debug("_update_valid_column_only: Starting row updates")
                    for row_idx in range(self.tasks_table.rowCount()):
                        if row_idx < len(table_data):
                            # Get Valid value from updated data
                            row_data = table_data[row_idx]
                            valid_value = row_data[7] if len(row_data) > 7 else "Yes"  # Valid is at index 7 in row_data
                            logging.debug(f"_update_valid_column_only: Row {row_idx}, valid_value={valid_value}")
                            
                            # Update the Valid cell
                            item = self.tasks_table.item(row_idx, valid_col_vis_idx)
                            if item:
                                logging.debug(f"_update_valid_column_only: Updating existing item at row {row_idx}")
                                item.setText(str(valid_value))
                            else:
                                logging.debug(f"_update_valid_column_only: Creating new item at row {row_idx}")
                                # Create item if it doesn't exist
                                item = QTableWidgetItem(str(valid_value))
                                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                                item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                                self.tasks_table.setItem(row_idx, valid_col_vis_idx, item)
                                logging.debug(f"_update_valid_column_only: Created item at row {row_idx}")
                    
                    logging.debug("_update_valid_column_only: Completed row updates")
                finally:
                    # Reconnect itemChanged signal
                    if was_connected:
                        logging.debug("_update_valid_column_only: Reconnecting itemChanged signal")
                        try:
                            self.tasks_table.itemChanged.connect(self._on_item_changed)
                            logging.debug("_update_valid_column_only: itemChanged signal reconnected")
                        except Exception as e:
                            logging.debug(f"_update_valid_column_only: Failed to reconnect signal: {e}")
                            pass  # Signal might already be connected
            finally:
                # Restore previous signal blocking state
                self.tasks_table.blockSignals(was_blocked)
                logging.debug(f"_update_valid_column_only: Restored signal blocking state (was_blocked={was_blocked})")
            
            logging.debug("_update_valid_column_only: END (success)")
        except Exception as e:
            logging.error(f"_update_valid_column_only: Error: {e}", exc_info=True)
            # Don't crash - just log the error

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
        
        # Get current table data to find max ID
        table_data = self.project_data.get_table_data("tasks")
        used_ids = set()
        for row_data in table_data:
            if row_data and len(row_data) > 0:
                try:
                    used_ids.add(int(row_data[0]))  # ID is at index 0
                except (ValueError, TypeError):
                    continue
        
        # Also check IDs in the table itself
        id_col_idx = None
        headers = [col.name for col in self.table_config.columns]
        for vis_idx, actual_idx in self._column_mapping.items():
            if headers[actual_idx] == "ID":
                id_col_idx = vis_idx
                break
        
        if id_col_idx is not None:
            for row in range(self.tasks_table.rowCount()):
                item = self.tasks_table.item(row, id_col_idx)
                if item and item.text():
                    try:
                        used_ids.add(int(item.text()))
                    except (ValueError, TypeError):
                        continue
        
        # Find next available ID
        next_id = 1
        while next_id in used_ids:
            next_id += 1
        
        # Create mapping from column name to index in get_table_data result
        row_data_column_map = {
            "ID": 0,
            "Row": 1,
            "Name": 2,
            "Start Date": 3,
            "Finish Date": 4,
            "Label": 5,
            "Placement": 6
        }
        
        # Disable sorting and block signals during duplication
        was_sorting = self.tasks_table.isSortingEnabled()
        self.tasks_table.setSortingEnabled(False)
        self.tasks_table.blockSignals(True)
        
        try:
            # Sort checked rows in reverse order to avoid index shifting issues
            checked_rows_sorted = sorted(checked_rows, reverse=True)
            
            # Collect all row data first
            rows_to_duplicate = []
            for orig_row_idx in checked_rows_sorted:
                # Get the full row data from stored data
                if orig_row_idx < len(table_data):
                    orig_row_data = list(table_data[orig_row_idx])  # Make a copy
                else:
                    # Row not in stored data, extract from table
                    orig_row_data = self._extract_row_data_from_table(orig_row_idx)
                
                if not orig_row_data or len(orig_row_data) < 8:
                    continue
                
                # Create new row data with new ID
                new_row_data = list(orig_row_data)  # Make a copy
                new_row_data[0] = str(next_id)  # Set new ID
                next_id += 1
                while next_id in used_ids:
                    next_id += 1
                used_ids.add(int(new_row_data[0]))
                
                rows_to_duplicate.append((orig_row_idx, new_row_data))
            
            # Insert rows in reverse order (from bottom to top) to maintain indices
            for orig_row_idx, new_row_data in rows_to_duplicate:
                # Insert new row right after the original
                new_row_idx = orig_row_idx + 1
                self.tasks_table.insertRow(new_row_idx)
                
                # Add checkbox
                checkbox_widget = CheckBoxWidget()
                self.tasks_table.setCellWidget(new_row_idx, 0, checkbox_widget)
                
                # Populate visible columns with duplicated data
                headers = [col.name for col in self.table_config.columns]
                for vis_col_idx, actual_col_idx in self._column_mapping.items():
                    if actual_col_idx == 0:  # Skip Select, already handled
                        continue
                    
                    col_config = self.table_config.columns[actual_col_idx]
                    col_name = col_config.name
                    
                    # Get value from new_row_data
                    if col_name in row_data_column_map:
                        value_idx = row_data_column_map[col_name]
                        if value_idx < len(new_row_data):
                            value = new_row_data[value_idx]
                        else:
                            value = ""
                    else:
                        value = ""
                    
                    # Format Order value to remove .0 if it's a whole number
                    if actual_col_idx == 2:  # Task Order
                        try:
                            order_float = float(str(value).strip()) if str(value).strip() else 0.0
                            if order_float == int(order_float):
                                value = str(int(order_float))
                            else:
                                value = str(order_float)
                        except (ValueError, AttributeError):
                            pass  # Keep original value if conversion fails
                    
                    # Create widget/item for this column
                    if col_config.widget_type == "combo":
                        combo = QComboBox()
                        combo.addItems(col_config.combo_items)
                        combo.setCurrentText(str(value) or col_config.combo_items[0])
                        combo.currentTextChanged.connect(self._sync_data_if_not_initializing)
                        self.tasks_table.setCellWidget(new_row_idx, vis_col_idx, combo)
                    else:
                        # Handle text and numeric columns
                        if col_name in ["Start Date", "Finish Date"]:
                            item = DateTableWidgetItem(str(value))
                            try:
                                if value and str(value).strip():
                                    date_obj = datetime.strptime(str(value).strip(), "%d/%m/%Y")
                                    item.setData(Qt.UserRole, date_obj)
                                else:
                                    item.setData(Qt.UserRole, None)
                            except (ValueError, AttributeError):
                                item.setData(Qt.UserRole, None)
                        elif actual_col_idx in (1, 2):  # ID, Row are numeric
                            item = NumericTableWidgetItem(str(value))
                        else:
                            item = QTableWidgetItem(str(value))
                        
                        if actual_col_idx == 1:  # Task ID read-only
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                            try:
                                item.setData(Qt.UserRole, int(str(value).strip()) if str(value).strip() else 0)
                            except (ValueError, AttributeError):
                                item.setData(Qt.UserRole, 0)
                        elif actual_col_idx == 2:  # Row number numeric
                            try:
                                item.setData(Qt.UserRole, int(str(value).strip()) if str(value).strip() else 1)
                            except (ValueError, AttributeError):
                                item.setData(Qt.UserRole, 1)
                        elif col_name == "Valid":  # Valid column - read-only text
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                        
                        self.tasks_table.setItem(new_row_idx, vis_col_idx, item)
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
 