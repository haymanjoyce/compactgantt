from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                           QHBoxLayout, QHeaderView, QTableWidgetItem, 
                           QMessageBox, QGroupBox, QSizePolicy, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from typing import List, Dict, Any
import logging
from ui.table_utils import NumericTableWidgetItem, add_row, remove_row, CheckBoxWidget, extract_table_data, highlight_table_errors
from .base_tab import BaseTab

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LinksTab(BaseTab):
    data_updated = pyqtSignal(dict)
    
    # Read-only cell background color (light gray)
    READ_ONLY_BG = QColor(240, 240, 240)

    def __init__(self, project_data, app_config):
        self.table_config = app_config.get_table_config("links")
        super().__init__(project_data, app_config)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create toolbar with buttons
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        
        add_btn = QPushButton("Add Link")
        add_btn.setToolTip("Add a new link")
        add_btn.setMinimumWidth(120)
        add_btn.clicked.connect(lambda: add_row(self.links_table, "links", self.app_config.tables, self, "ID"))
        
        remove_btn = QPushButton("Remove Link")
        remove_btn.setToolTip("Remove selected link(s)")
        remove_btn.setMinimumWidth(120)
        remove_btn.clicked.connect(lambda: remove_row(self.links_table, "links", 
                                                    self.app_config.tables, self))
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addStretch()  # Push buttons to the left
        
        # Create group box for table
        table_group = QGroupBox("Links")
        table_group_layout = QVBoxLayout()
        table_group_layout.setSpacing(5)
        table_group_layout.setContentsMargins(5, 10, 5, 5)
        
        # Create table with all columns: Select, From Task ID, To Task ID
        headers = [col.name for col in self.table_config.columns]
        self.links_table = QTableWidget(0, len(headers))
        self.links_table.setHorizontalHeaderLabels(headers)
        
        # Table styling
        self.links_table.setAlternatingRowColors(False)  # Disabled to avoid conflict with read-only cell backgrounds
        self.links_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.links_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.links_table.setShowGrid(True)
        self.links_table.verticalHeader().setVisible(False)
        
        # Add bottom border to header row
        self.links_table.setStyleSheet("""
            QHeaderView::section {
                border-bottom: 1px solid #c0c0c0;
                border-top: none;
                border-left: none;
                border-right: none;
            }
        """)
        
        # Column sizing
        header = self.links_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Select
        self.links_table.setColumnWidth(0, 50)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # From Task ID
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # From Task Name
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # To Task ID
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # To Task Name
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Valid
        
        # Enable horizontal scroll bar
        self.links_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.links_table.setSortingEnabled(True)
        
        # Set table size policy
        self.links_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        table_group_layout.addLayout(toolbar)
        table_group_layout.addWidget(self.links_table)
        table_group.setLayout(table_group_layout)
        
        layout.addWidget(table_group)
        self.setLayout(layout)

    def _connect_signals(self):
        self.links_table.itemChanged.connect(self._on_item_changed)
    
    def _on_item_changed(self, item):
        """Handle item changes - update UserRole for numeric columns to maintain proper sorting."""
        if item is None:
            return
        
        col = item.column()
        col_config = self.table_config.columns[col] if col < len(self.table_config.columns) else None
        
        # Don't trigger sync for Valid or ID column changes (they're read-only and auto-calculated)
        if col_config and col_config.name in ["Valid", "ID"]:
            return
        
        # Update UserRole for numeric columns (ID, From Task ID, To Task ID)
        if col_config and col_config.name in ["ID", "From Task ID", "To Task ID"]:
            try:
                val_str = item.text().strip()
                item.setData(Qt.UserRole, int(val_str) if val_str else 0)
            except (ValueError, AttributeError):
                item.setData(Qt.UserRole, 0)
        
        # Trigger sync
        self._sync_data_if_not_initializing()

    def _load_initial_data_impl(self):
        table_data = self.project_data.get_table_data("links")
        row_count = max(len(table_data), self.table_config.min_rows)
        self.links_table.setRowCount(row_count)
        self._initializing = True

        headers = [col.name for col in self.table_config.columns]
        
        for row_idx in range(row_count):
            # Add checkbox first (Select column)
            checkbox_widget = CheckBoxWidget()
            self.links_table.setCellWidget(row_idx, 0, checkbox_widget)

            if row_idx < len(table_data):
                row_data = table_data[row_idx]
                # row_data structure: [ID, From Task ID, From Task Name, To Task ID, To Task Name, Valid]
                for col_idx in range(1, len(headers)):  # Skip Select column (index 0)
                    col_config = self.table_config.columns[col_idx]
                    col_name = col_config.name
                    
                    # Get value from row_data (index 0 = ID, index 1 = From Task ID, index 2 = From Task Name, index 3 = To Task ID, index 4 = To Task Name, index 5 = Valid)
                    value_idx = col_idx - 1  # Adjust for missing Select column in row_data
                    value = row_data[value_idx] if value_idx < len(row_data) else ""
                    
                    # Create appropriate widget/item based on column type
                    if col_config.widget_type == "combo":
                        combo = QComboBox()
                        combo.addItems(col_config.combo_items)
                        if value:
                            idx = combo.findText(str(value))
                            if idx >= 0:
                                combo.setCurrentIndex(idx)
                        combo.currentTextChanged.connect(self._sync_data_if_not_initializing)
                        self.links_table.setCellWidget(row_idx, col_idx, combo)
                    else:
                        # ID column - read-only numeric
                        if col_name == "ID":
                            item = NumericTableWidgetItem(str(value))
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                            item.setBackground(QBrush(self.READ_ONLY_BG))  # Gray background
                            try:
                                item.setData(Qt.UserRole, int(str(value).strip()) if str(value).strip() else 0)
                            except (ValueError, AttributeError):
                                item.setData(Qt.UserRole, 0)
                        # Numeric columns (From Task ID, To Task ID)
                        elif col_name in ["From Task ID", "To Task ID"]:
                            item = NumericTableWidgetItem(str(value))
                            try:
                                item.setData(Qt.UserRole, int(str(value).strip()) if str(value).strip() else 0)
                            except (ValueError, AttributeError):
                                item.setData(Qt.UserRole, 0)
                        # Name columns (From Task Name, To Task Name) - read-only with truncation
                        elif col_name in ["From Task Name", "To Task Name"]:
                            item = QTableWidgetItem(self._truncate_text(str(value)))
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                            item.setBackground(QBrush(self.READ_ONLY_BG))  # Gray background
                            item.setToolTip(str(value))  # Show full text in tooltip
                        # Valid column - read-only text
                        elif col_name == "Valid":
                            item = QTableWidgetItem(str(value) if value else "Yes")
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                            item.setBackground(QBrush(self.READ_ONLY_BG))  # Gray background
                        else:
                            item = QTableWidgetItem(str(value))
                        self.links_table.setItem(row_idx, col_idx, item)
            else:
                # New row - use defaults
                context = {
                    "max_id": len(table_data)  # Maximum existing link ID
                }
                defaults = self.table_config.default_generator(row_idx, context)
                # defaults structure: [False, ID, From Task ID, From Task Name, To Task ID, To Task Name, Valid]
                # defaults[0] is checkbox, defaults[1] is ID (col_idx 1), etc.
                
                for col_idx in range(1, len(headers)):  # Skip Select column (index 0)
                    col_config = self.table_config.columns[col_idx]
                    col_name = col_config.name
                    
                    # defaults includes checkbox at 0, so col_idx maps to defaults[col_idx]
                    default_idx = col_idx
                    if default_idx < len(defaults):
                        default = defaults[default_idx]
                    else:
                        default = ""
                    
                    if col_config.widget_type == "combo":
                        combo = QComboBox()
                        combo.addItems(col_config.combo_items)
                        combo.setCurrentText(str(default))
                        combo.currentTextChanged.connect(self._sync_data_if_not_initializing)
                        self.links_table.setCellWidget(row_idx, col_idx, combo)
                    else:
                        # ID column - read-only numeric
                        if col_name == "ID":
                            item = NumericTableWidgetItem(str(default))
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                            item.setBackground(QBrush(self.READ_ONLY_BG))  # Gray background
                            try:
                                item.setData(Qt.UserRole, int(str(default).strip()) if str(default).strip() else 0)
                            except (ValueError, AttributeError):
                                item.setData(Qt.UserRole, 0)
                        # Numeric columns (From Task ID, To Task ID)
                        elif col_name in ["From Task ID", "To Task ID"]:
                            item = NumericTableWidgetItem(str(default))
                            try:
                                item.setData(Qt.UserRole, int(str(default).strip()) if str(default).strip() else 0)
                            except (ValueError, AttributeError):
                                item.setData(Qt.UserRole, 0)
                        # Name columns (From Task Name, To Task Name) - read-only with truncation
                        elif col_name in ["From Task Name", "To Task Name"]:
                            item = QTableWidgetItem(self._truncate_text(str(default)))
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                            item.setBackground(QBrush(self.READ_ONLY_BG))  # Gray background
                            item.setToolTip(str(default))  # Show full text in tooltip
                        # Valid column - read-only text
                        elif col_name == "Valid":
                            item = QTableWidgetItem(str(default) if default else "Yes")
                            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                            item.setBackground(QBrush(self.READ_ONLY_BG))  # Gray background
                        else:
                            item = QTableWidgetItem(str(default))
                        self.links_table.setItem(row_idx, col_idx, item)
        
        # Sort by ID by default
        self.links_table.sortItems(1, Qt.AscendingOrder)  # Column 1 = ID
        
        self._initializing = False

    def _sync_data_impl(self):
        """Extract data from table and update project_data."""
        # Avoid emitting during initialization to prevent recursive updates
        if self._initializing:
            return
        
        # Extract table data (excludes checkbox column)
        data = extract_table_data(self.links_table)
        
        # data structure: [[ID, From Task ID, From Task Name, To Task ID, To Task Name, Valid], ...]
        # Note: Valid field will be recalculated in update_from_table
        errors = self.project_data.update_from_table("links", data)
        
        # Update Valid column for rows that have changed, without full reload
        # This preserves user input in progress
        self._update_valid_column_only()
        
        # Don't emit data_updated here - chart will update when user clicks "Update Chart" button
        # This matches the behavior of the tasks tab
    
    def _truncate_text(self, text: str, max_length: int = 50) -> str:
        """Truncate text to max_length and add ellipsis if needed."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    def _update_valid_column_only(self):
        """Update only the Valid column and task name columns without reloading the entire table."""
        # Get updated data from project_data
        table_data = self.project_data.get_table_data("links")
        valid_col_idx = 6  # Valid is column 6 (after Select, ID, From Task ID, From Task Name, To Task ID, To Task Name)
        from_name_col_idx = 3  # From Task Name is column 3
        to_name_col_idx = 5  # To Task Name is column 5
        
        # Block signals to prevent recursive updates
        self.links_table.blockSignals(True)
        
        # Update Valid column and task name columns for each row
        for row_idx in range(self.links_table.rowCount()):
            if row_idx < len(table_data):
                # Get values from updated data
                row_data = table_data[row_idx]
                valid_value = row_data[5] if len(row_data) > 5 else "Yes"  # Valid is at index 5 in row_data
                from_name = row_data[2] if len(row_data) > 2 else ""  # From Task Name is at index 2
                to_name = row_data[4] if len(row_data) > 4 else ""  # To Task Name is at index 4
                
                # Update the Valid cell
                item = self.links_table.item(row_idx, valid_col_idx)
                if item:
                    item.setText(valid_value)
                else:
                    # Create item if it doesn't exist
                    item = QTableWidgetItem(valid_value)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(self.READ_ONLY_BG))  # Gray background
                    self.links_table.setItem(row_idx, valid_col_idx, item)
                
                # Update From Task Name cell
                from_name_item = self.links_table.item(row_idx, from_name_col_idx)
                if from_name_item:
                    from_name_item.setText(self._truncate_text(from_name))
                    from_name_item.setToolTip(from_name)
                elif from_name:
                    from_name_item = QTableWidgetItem(self._truncate_text(from_name))
                    from_name_item.setFlags(from_name_item.flags() & ~Qt.ItemIsEditable)
                    from_name_item.setBackground(QBrush(self.READ_ONLY_BG))  # Gray background
                    from_name_item.setToolTip(from_name)
                    self.links_table.setItem(row_idx, from_name_col_idx, from_name_item)
                
                # Update To Task Name cell
                to_name_item = self.links_table.item(row_idx, to_name_col_idx)
                if to_name_item:
                    to_name_item.setText(self._truncate_text(to_name))
                    to_name_item.setToolTip(to_name)
                elif to_name:
                    to_name_item = QTableWidgetItem(self._truncate_text(to_name))
                    to_name_item.setFlags(to_name_item.flags() & ~Qt.ItemIsEditable)
                    to_name_item.setBackground(QBrush(self.READ_ONLY_BG))  # Gray background
                    to_name_item.setToolTip(to_name)
                    self.links_table.setItem(row_idx, to_name_col_idx, to_name_item)
        
        self.links_table.blockSignals(False)

