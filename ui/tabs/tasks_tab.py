from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                           QHBoxLayout, QComboBox, QHeaderView, QTableWidgetItem, 
                           QMessageBox, QGroupBox, QSizePolicy, QLabel, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush
from typing import List, Dict, Any
from datetime import datetime
import logging
from ui.table_utils import NumericTableWidgetItem, DateTableWidgetItem, add_row, remove_row, renumber_task_orders, CheckBoxWidget, highlight_table_errors, extract_table_data
from .base_tab import BaseTab

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TasksTab(BaseTab):
    data_updated = pyqtSignal(dict)

    def __init__(self, project_data, app_config):
        self.table_config = app_config.get_table_config("tasks")
        self._selected_row = None  # Track currently selected row
        self._updating_form = False  # Prevent circular updates
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
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addStretch()  # Push buttons to the left
        
        # Create group box for table
        table_group = QGroupBox("Tasks")
        table_group_layout = QVBoxLayout()
        table_group_layout.setSpacing(5)
        table_group_layout.setContentsMargins(5, 10, 5, 5)
        
        # Create table - show: Select, ID, Order, Row, Name, Start Date, Finish Date
        headers = [col.name for col in self.table_config.columns]
        visible_columns = ["Select", "ID", "Order", "Row", "Name", "Start Date", "Finish Date"]
        visible_indices = [headers.index(col) for col in visible_columns if col in headers]
        
        self.tasks_table = QTableWidget(0, len(visible_indices))
        visible_headers = [headers[i] for i in visible_indices]
        self.tasks_table.setHorizontalHeaderLabels(visible_headers)
        
        # Store mapping of visible column index to actual column index
        self._column_mapping = {vis_idx: actual_idx for vis_idx, actual_idx in enumerate(visible_indices)}
        self._reverse_column_mapping = {actual_idx: vis_idx for vis_idx, actual_idx in enumerate(visible_indices)}
        
        # Enhanced table styling
        self.tasks_table.setAlternatingRowColors(True)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tasks_table.setSelectionMode(QTableWidget.SingleSelection)  # Single selection for detail form
        self.tasks_table.setShowGrid(True)
        self.tasks_table.verticalHeader().setVisible(False)
        
        # Column sizing
        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Select
        self.tasks_table.setColumnWidth(0, 50)
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # ID
        self.tasks_table.setColumnWidth(1, 50)
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Order
        self.tasks_table.setColumnWidth(2, 60)
        header.setSectionResizeMode(3, QHeaderView.Fixed)  # Row
        self.tasks_table.setColumnWidth(3, 50)
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Name
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Start Date
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Finish Date
        
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
                # row_data structure: [ID, Order, Row, Name, Start Date, Finish Date, Label, Placement]
                if len(row_data) >= 8:
                    self.detail_label.setCurrentText(str(row_data[6]) if row_data[6] else "Yes")
                    self.detail_placement.setCurrentText(str(row_data[7]) if row_data[7] else "Inside")
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
        if item is None:
            return
        
        col = item.column()
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
        
        # Update UserRole for date columns (Start Date, Finish Date)
        if col_name in ["Start Date", "Finish Date"]:
            try:
                val_str = item.text().strip()
                if val_str:
                    date_obj = datetime.strptime(val_str, "%d/%m/%Y")
                    item.setData(Qt.UserRole, date_obj)
                else:
                    item.setData(Qt.UserRole, None)
            except (ValueError, AttributeError):
                item.setData(Qt.UserRole, None)
        # Update UserRole for numeric columns (ID, Order, Row)
        elif actual_col_idx == 1:  # Task ID
            try:
                val_str = item.text().strip()
                item.setData(Qt.UserRole, int(val_str) if val_str else 0)
            except (ValueError, AttributeError):
                item.setData(Qt.UserRole, 0)
        elif actual_col_idx == 2:  # Task Order
            try:
                val_str = item.text().strip()
                item.setData(Qt.UserRole, float(val_str) if val_str else 0.0)
            except (ValueError, AttributeError):
                item.setData(Qt.UserRole, 0.0)
        elif actual_col_idx == 3:  # Row number
            try:
                val_str = item.text().strip()
                item.setData(Qt.UserRole, int(val_str) if val_str else 1)
            except (ValueError, AttributeError):
                item.setData(Qt.UserRole, 1)
        
        # Trigger sync
        self._sync_data_if_not_initializing()

    def _load_initial_data(self):
        self._load_initial_data_impl()

    def _load_initial_data_impl(self):
        table_data = self.project_data.get_table_data("tasks")
        row_count = max(len(table_data), self.table_config.min_rows)
        self.tasks_table.setRowCount(row_count)
        self._initializing = True

        headers = [col.name for col in self.table_config.columns]
        
        # Create a mapping from column name to index in row_data from get_table_data
        # row_data structure: [ID, Order, Row, Name, Start Date, Finish Date, Label, Placement]
        row_data_column_map = {
            "ID": 0,
            "Order": 1,
            "Row": 2,
            "Name": 3,
            "Start Date": 4,
            "Finish Date": 5,
            "Label": 6,
            "Placement": 7
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
                        elif actual_col_idx in (1, 2, 3):  # ID, Order, Row are numeric
                            item = NumericTableWidgetItem(str(value))
                        else:
                            item = QTableWidgetItem(str(value))
                        
                        if actual_col_idx == 1:  # Task ID read-only
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                            # Ensure UserRole is set for numeric sorting
                            try:
                                item.setData(Qt.UserRole, int(str(value).strip()) if str(value).strip() else 0)
                            except (ValueError, AttributeError):
                                item.setData(Qt.UserRole, 0)
                        elif actual_col_idx == 2:  # Task Order numeric
                            # Ensure UserRole is set for numeric sorting
                            try:
                                item.setData(Qt.UserRole, float(str(value).strip()) if str(value).strip() else 0.0)
                            except (ValueError, AttributeError):
                                item.setData(Qt.UserRole, 0.0)
                        elif actual_col_idx == 3:  # Row number numeric
                            # Ensure UserRole is set for numeric sorting
                            try:
                                item.setData(Qt.UserRole, int(str(value).strip()) if str(value).strip() else 1)
                            except (ValueError, AttributeError):
                                item.setData(Qt.UserRole, 1)
                        
                        self.tasks_table.setItem(row_idx, vis_col_idx, item)
            else:
                # New row - use defaults
                context = {
                    "max_task_id": len(table_data),  # Maximum existing task ID, not len + row_idx
                    "max_task_order": len(table_data)  # Maximum existing task order, not len + row_idx
                }
                defaults = self.table_config.default_generator(row_idx, context)
                # defaults structure: [False, ID, Order, Row, Name, Start Date, Finish Date, Label, Placement]
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
                                # Ensure UserRole is set for numeric sorting
                                try:
                                    item.setData(Qt.UserRole, int(str(default).strip()) if str(default).strip() else 0)
                                except (ValueError, AttributeError):
                                    item.setData(Qt.UserRole, 0)
                            elif actual_col_idx == 2:  # Task Order numeric
                                # Ensure UserRole is set for numeric sorting
                                try:
                                    item.setData(Qt.UserRole, float(str(default).strip()) if str(default).strip() else 0.0)
                                except (ValueError, AttributeError):
                                    item.setData(Qt.UserRole, 0.0)
                            elif actual_col_idx == 3:  # Row number numeric
                                # Ensure UserRole is set for numeric sorting
                                try:
                                    item.setData(Qt.UserRole, int(str(default).strip()) if str(default).strip() else 1)
                                except (ValueError, AttributeError):
                                    item.setData(Qt.UserRole, 1)
                            
                            self.tasks_table.setItem(row_idx, vis_col_idx, item)

        renumber_task_orders(self.tasks_table)
        # Find the Order column for sorting
        order_col_vis_idx = None
        for vis_idx, actual_idx in self._column_mapping.items():
            if headers[actual_idx] == "Order":
                order_col_vis_idx = vis_idx
                break
        if order_col_vis_idx is not None:
            self.tasks_table.sortByColumn(order_col_vis_idx, Qt.AscendingOrder)
        
        self._initializing = False
        self._sync_data()

    def _sync_data(self):
        self._sync_data_impl()

    def _sync_data_impl(self):
        logging.debug("Starting _sync_data in TasksTab")
        
        # Reconstruct full table data from visible columns + detail form
        headers = [col.name for col in self.table_config.columns]
        full_table_data = []
        
        # Create mapping from column name to index in get_table_data result
        row_data_column_map = {
            "ID": 0,
            "Order": 1,
            "Row": 2,
            "Name": 3,
            "Start Date": 4,
            "Finish Date": 5,
            "Label": 6,
            "Placement": 7
        }
        
        for row in range(self.tasks_table.rowCount()):
            full_row = []
            
            # NOTE: update_from_table expects data WITHOUT checkbox column
            # Column order expected: ID, Order, Row, Name, Start Date, Finish Date, Label, Placement
            
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
                                "max_task_order": len(table_data) + row
                            }
                            defaults = self.table_config.default_generator(row, context)
                            # defaults structure: [False, ID, Order, Row, Name, Start Date, Finish Date, Label, Placement]
                            # defaults[0] is checkbox, so Label is at defaults[7], Placement is at defaults[8]
                            if col_name == "Label":
                                if len(defaults) > 7:
                                    full_row.append(str(defaults[7]))
                                else:
                                    full_row.append("Yes")
                            elif col_name == "Placement":
                                if len(defaults) > 8:
                                    full_row.append(str(defaults[8]))
                                else:
                                    full_row.append("Inside")
                            else:
                                full_row.append("")
            
            full_table_data.append(full_row)
        
        errors = self.project_data.update_from_table("tasks", full_table_data)
        highlight_table_errors(self.tasks_table, errors)
        logging.debug("_sync_data in TasksTab completed")

    def _sync_data_if_not_initializing(self):
        if not self._initializing:
            logging.debug("Calling _sync_data from itemChanged")
            self._sync_data()

    def _extract_table_data(self) -> List[List[str]]:
        # This is now handled in _sync_data_impl
        return []
