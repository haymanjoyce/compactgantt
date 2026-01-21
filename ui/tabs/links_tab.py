from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                           QHBoxLayout, QHeaderView, QTableWidgetItem, 
                           QMessageBox, QGroupBox, QSizePolicy, QComboBox, QLabel, QGridLayout, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from ui.table_utils import NumericTableWidgetItem, add_row, remove_row, CheckBoxWidget, extract_table_data, highlight_table_errors
from .base_tab import BaseTab
from models.link import Link
from utils.conversion import safe_int, parse_internal_date

# Logging is configured centrally in utils/logging_config.py

class LinksTab(BaseTab):
    data_updated = pyqtSignal(dict)
    

    def __init__(self, project_data, app_config):
        self.table_config = app_config.get_table_config("links")
        self._selected_row = None  # Track currently selected row
        self._updating_form = False  # Prevent circular updates
        self._detail_form_widgets = []  # Will be populated in _create_detail_form
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
        
        self.show_ids_checkbox = QCheckBox("Show IDs on chart")
        self.show_ids_checkbox.setChecked(self.app_config.general.show_ids_on_chart)
        self.show_ids_checkbox.toggled.connect(self._on_show_ids_toggled)
        self.show_ids_checkbox.setToolTip("Display task/milestone IDs on the chart when linking")
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addWidget(self.show_ids_checkbox)
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
        self.links_table.setSelectionMode(QTableWidget.SingleSelection)  # Single selection for detail form
        self.links_table.setShowGrid(True)
        self.links_table.verticalHeader().setVisible(False)
        
        # Add bottom border to header row and gridline styling
        self.links_table.setStyleSheet(self.app_config.general.table_stylesheet)
        
        # Column sizing - use key-based lookups instead of positional indices
        header = self.links_table.horizontalHeader()
        
        # Find columns by name and set their sizing
        id_col = None
        from_task_id_col = None
        from_task_name_col = None
        to_task_id_col = None
        to_task_name_col = None
        valid_col = None
        
        for i in range(self.links_table.columnCount()):
            header_text = self.links_table.horizontalHeaderItem(i).text()
            if header_text == "ID":
                id_col = i
            elif header_text == "From Task ID":
                from_task_id_col = i
            elif header_text == "From Task Name":
                from_task_name_col = i
            elif header_text == "To Task ID":
                to_task_id_col = i
            elif header_text == "To Task Name":
                to_task_name_col = i
            elif header_text == "Valid":
                valid_col = i
        
        if id_col is not None:
            header.setSectionResizeMode(id_col, QHeaderView.ResizeToContents)
        if from_task_id_col is not None:
            header.setSectionResizeMode(from_task_id_col, QHeaderView.ResizeToContents)
        if from_task_name_col is not None:
            header.setSectionResizeMode(from_task_name_col, QHeaderView.Stretch)
        if to_task_id_col is not None:
            header.setSectionResizeMode(to_task_id_col, QHeaderView.ResizeToContents)
        if to_task_name_col is not None:
            header.setSectionResizeMode(to_task_name_col, QHeaderView.Stretch)
        if valid_col is not None:
            header.setSectionResizeMode(valid_col, QHeaderView.ResizeToContents)
        
        # Enable horizontal scroll bar
        self.links_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.links_table.setSortingEnabled(True)
        
        # Set table size policy
        self.links_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        table_group_layout.addLayout(toolbar)
        table_group_layout.addWidget(self.links_table)
        table_group.setLayout(table_group_layout)
        
        # Add table group with stretch factor so it expands to fill available space
        layout.addWidget(table_group, 1)  # Stretch factor of 1 makes it expand
        
        # Create detail form group box
        detail_group = self._create_detail_form()
        layout.addWidget(detail_group)  # No stretch factor - stays at natural size
        
        self.setLayout(layout)

    def _create_detail_form(self) -> QGroupBox:
        """Create the detail form for editing link style fields."""
        group = QGroupBox("Link Style")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        LABEL_WIDTH = 120
        
        # Line Color
        color_label = QLabel("Line Color:")
        color_label.setFixedWidth(LABEL_WIDTH)
        self.detail_line_color = QComboBox()
        self.detail_line_color.addItems(["black", "red"])
        self.detail_line_color.setToolTip("Color of the link line and arrowhead")
        self.detail_line_color.currentTextChanged.connect(self._on_detail_form_changed)
        self.detail_line_color.setEnabled(False)
        
        # Line Style
        style_label = QLabel("Line Style:")
        style_label.setFixedWidth(LABEL_WIDTH)
        self.detail_line_style = QComboBox()
        self.detail_line_style.addItems(["solid", "dotted", "dashed"])
        self.detail_line_style.setToolTip("Style of the link line (solid, dotted, or dashed)")
        self.detail_line_style.currentTextChanged.connect(self._on_detail_form_changed)
        self.detail_line_style.setEnabled(False)
        
        # Link Routing
        routing_label = QLabel("Link Routing:")
        routing_label.setFixedWidth(LABEL_WIDTH)
        self.detail_link_routing = QComboBox()
        self.detail_link_routing.addItems(["auto", "HV", "VH"])
        self.detail_link_routing.setToolTip("Routing pattern: Auto (automatic), HV (horizontal then vertical), or VH (vertical then horizontal)")
        self.detail_link_routing.currentTextChanged.connect(self._on_detail_form_changed)
        self.detail_link_routing.setEnabled(False)
        
        # Store list of detail form widgets for easy enable/disable
        self._detail_form_widgets = [self.detail_line_color, self.detail_line_style, self.detail_link_routing]
        
        # Layout form fields vertically (like tasks tab)
        layout.addWidget(color_label, 0, 0)
        layout.addWidget(self.detail_line_color, 0, 1)
        layout.addWidget(style_label, 1, 0)
        layout.addWidget(self.detail_line_style, 1, 1)
        layout.addWidget(routing_label, 2, 0)
        layout.addWidget(self.detail_link_routing, 2, 1)
        
        layout.setColumnStretch(1, 1)
        
        group.setLayout(layout)
        return group

    def _on_table_selection_changed(self):
        """Handle table selection changes - populate detail form."""
        selected_rows = self.links_table.selectionModel().selectedRows()
        if not selected_rows:
            self._selected_row = None
            self._clear_detail_form()
            return
        
        # Show detail form only when exactly one row is selected
        if len(selected_rows) == 1:
            row = selected_rows[0].row()
            self._selected_row = row
            self._populate_detail_form(row)
        else:
            # Multiple rows selected - clear detail form
            self._selected_row = None
            self._clear_detail_form()

    def _populate_detail_form(self, row: int):
        """Populate detail form with data from selected link."""
        self._updating_form = True
        
        try:
            # Get link ID from the table row (works even after sorting)
            id_col = self._get_column_index("ID")
            if id_col is None:
                self._set_detail_form_enabled(self._detail_form_widgets, False)
                return
            
            id_item = self.links_table.item(row, id_col)
            if not id_item:
                self._set_detail_form_enabled(self._detail_form_widgets, False)
                return
            
            link_id = safe_int(id_item.text())
            if link_id <= 0:
                self._set_detail_form_enabled(self._detail_form_widgets, False)
                return
            
            # Find the link in project_data by ID (key-based access)
            link = None
            for l in self.project_data.links:
                if l.link_id == link_id:
                    link = l
                    break
            
            if link:
                self.detail_line_color.setCurrentText(link.line_color if link.line_color else "black")
                self.detail_line_style.setCurrentText(link.line_style if link.line_style else "solid")
                self.detail_link_routing.setCurrentText(link.link_routing if link.link_routing else "auto")
                # Enable detail form widgets when a valid link is selected
                self._set_detail_form_enabled(self._detail_form_widgets, True)
            else:
                # Use defaults if link not found
                self.detail_line_color.setCurrentText("black")
                self.detail_line_style.setCurrentText("solid")
                self.detail_link_routing.setCurrentText("auto")
                self._set_detail_form_enabled(self._detail_form_widgets, False)
        finally:
            self._updating_form = False

    def _clear_detail_form(self):
        """Clear the detail form when no link is selected."""
        self._updating_form = True
        try:
            self.detail_line_color.setCurrentText("black")
            self.detail_line_style.setCurrentText("solid")
            self.detail_link_routing.setCurrentText("auto")
            # Disable detail form widgets when no link is selected
            self._set_detail_form_enabled(self._detail_form_widgets, False)
        finally:
            self._updating_form = False

    def _on_detail_form_changed(self):
        """Handle changes in detail form - update selected link."""
        if self._updating_form or self._selected_row is None:
            return
        
        # Trigger sync to update the data
        self._sync_data_if_not_initializing()

    def _connect_signals(self):
        self.links_table.itemChanged.connect(self._on_item_changed)
        self.links_table.selectionModel().selectionChanged.connect(self._on_table_selection_changed)
    
    def _on_item_changed(self, item):
        """Handle item changes - update UserRole for numeric columns to maintain proper sorting."""
        if item is None:
            return
        
        col = item.column()
        row = item.row()
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
        
        # Immediately update task name when a task ID is entered
        if col_config and col_config.name == "From Task ID":
            self._update_task_name_immediately(row, "From")
        elif col_config and col_config.name == "To Task ID":
            self._update_task_name_immediately(row, "To")
        
        # Trigger sync
        self._sync_data_if_not_initializing()

    def _update_task_name_immediately(self, row: int, direction: str):
        """Update task name field immediately when task ID is entered."""
        # Build task name mapping
        task_name_map = {task.task_id: task.task_name for task in self.project_data.tasks}
        
        # Get column indices
        if direction == "From":
            id_col = self._get_column_index("From Task ID")
            name_col = self._get_column_index("From Task Name")
        else:  # "To"
            id_col = self._get_column_index("To Task ID")
            name_col = self._get_column_index("To Task Name")
        
        if id_col is None or name_col is None:
            return
        
        # Get task ID from the table
        id_item = self.links_table.item(row, id_col)
        if not id_item:
            return
        
        task_id = safe_int(id_item.text())
        if task_id <= 0:
            # Clear the name if invalid ID
            task_name = ""
        else:
            # Look up task name
            task_name = task_name_map.get(task_id, "")
        
        # Update the name field
        self.links_table.blockSignals(True)
        try:
            name_item = self.links_table.item(row, name_col)
            display_text = self._truncate_text(task_name)
            if name_item:
                name_item.setText(display_text)
                name_item.setToolTip(task_name)
            else:
                name_item = QTableWidgetItem(display_text)
                name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                name_item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                name_item.setToolTip(task_name)
                self.links_table.setItem(row, name_col, name_item)
        finally:
            self.links_table.blockSignals(False)

    def _ensure_unique_link_ids(self, links: List[Link]) -> None:
        """Ensure all link IDs are unique by reassigning duplicates.
        
        Args:
            links: List of Link objects to fix
        """
        if not links:
            return
        
        # Collect all used IDs
        used_ids = set()
        duplicates = []
        
        for link in links:
            if link.link_id in used_ids or link.link_id <= 0:
                # Mark as duplicate or invalid
                duplicates.append(link)
            else:
                used_ids.add(link.link_id)
        
        # Reassign duplicate IDs
        if duplicates:
            next_id = 1
            for link in duplicates:
                while next_id in used_ids:
                    next_id += 1
                link.link_id = next_id
                used_ids.add(next_id)
                logging.warning(f"Fixed duplicate link ID: reassigned to {next_id}")

    def _load_initial_data_impl(self):
        """Load initial data into the table using Link objects directly."""
        # Get Link objects directly from project_data
        links = self.project_data.links
        row_count = len(links)
        self.links_table.setRowCount(row_count)
        self._initializing = True
        # Sync checkbox from config
        self.show_ids_checkbox.setChecked(self.app_config.general.show_ids_on_chart)

        # Create task name mapping
        task_name_map = {task.task_id: task.task_name for task in self.project_data.tasks}
        
        # Ensure all link IDs are unique before loading
        self._ensure_unique_link_ids(links)
        
        for row_idx in range(row_count):

            # Use helper method to populate row from Link object
            link = links[row_idx]
            self._update_table_row_from_link(row_idx, link, task_name_map)
        
        # Sort by ID in ascending order by default (using key-based column lookup)
        id_col = self._get_column_index("ID")
        if id_col is not None:
            self.links_table.sortItems(id_col, Qt.AscendingOrder)
        
        self._initializing = False
        
        # Disable detail form if no links exist or no selection
        if row_count == 0 or self._selected_row is None:
            self._clear_detail_form()
        
        # Calculate and update Valid column for all rows (including those populated from defaults)
        self._update_valid_column_only()

    def _sync_data_impl(self):
        """Extract data from table and update project_data using Link objects directly."""
        # Avoid emitting during initialization to prevent recursive updates
        if self._initializing:
            return
        
        # Persist checkbox state into config
        self.app_config.general.show_ids_on_chart = self.show_ids_checkbox.isChecked()
        
        # Extract Link objects from table rows
        links = []
        for row_idx in range(self.links_table.rowCount()):
            link = self._link_from_table_row(row_idx)
            if link:
                links.append(link)
        
        # Ensure all link IDs are unique before updating project data
        self._ensure_unique_link_ids(links)
        
        # Update project data with Link objects directly
        errors = self.project_data.update_links(links)
        
        # Update table rows with computed fields (task names, valid status)
        # Also update IDs in case they were reassigned
        task_name_map = {task.task_id: task.task_name for task in self.project_data.tasks}
        self.links_table.blockSignals(True)
        try:
            for row_idx, link in enumerate(links):
                if row_idx < self.links_table.rowCount():
                    # Update computed fields in the table, including ID if it was reassigned
                    self._update_table_row_from_link(row_idx, link, task_name_map)
        finally:
            self.links_table.blockSignals(False)
        
        # Sort by ID in ascending order after sync (using key-based column lookup)
        id_col = self._get_column_index("ID")
        if id_col is not None:
            self.links_table.sortItems(id_col, Qt.AscendingOrder)
        
        # Re-populate detail form if a row is currently selected
        # This ensures the detail form is enabled when a new link becomes valid
        if self._selected_row is not None and self._selected_row < self.links_table.rowCount():
            self._populate_detail_form(self._selected_row)
        
        # Don't emit data_updated here - chart will update when user clicks "Update Chart" button
        # This matches the behavior of the tasks tab
    
    def _on_show_ids_toggled(self, checked: bool):
        """Handle toggle for showing IDs on chart."""
        if self._initializing:
            return
        self.app_config.general.show_ids_on_chart = checked
        # Notify main window to refresh chart
        self.data_updated.emit({"chart_config_changed": True})
    
    def _truncate_text(self, text: str, max_length: int = 50) -> str:
        """Truncate text to max_length and add ellipsis if needed."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    def _link_from_table_row(self, row_idx: int) -> Optional[Link]:
        """
        Extract a Link object from a table row.
        Returns None if the row is invalid or incomplete.
        """
        try:
            # Get column indices by name
            id_col = self._get_column_index("ID")
            from_id_col = self._get_column_index("From Task ID")
            to_id_col = self._get_column_index("To Task ID")
            
            if id_col is None or from_id_col is None or to_id_col is None:
                return None
            
            # Extract ID fields
            id_item = self.links_table.item(row_idx, id_col)
            from_id_item = self.links_table.item(row_idx, from_id_col)
            to_id_item = self.links_table.item(row_idx, to_id_col)
            
            if not id_item or not from_id_item or not to_id_item:
                return None
            
            link_id = safe_int(id_item.text())
            from_task_id = safe_int(from_id_item.text())
            to_task_id = safe_int(to_id_item.text())
            
            if link_id <= 0 or from_task_id <= 0 or to_task_id <= 0:
                return None
            
            # Extract style fields from detail form if this is the selected row
            # Otherwise, get from existing Link object
            line_color = "black"
            line_style = "solid"
            link_routing = "auto"
            
            if row_idx == self._selected_row:
                # Use values from detail form
                if self.detail_line_color:
                    line_color = self.detail_line_color.currentText()
                if self.detail_line_style:
                    line_style = self.detail_line_style.currentText()
                if self.detail_link_routing:
                    link_routing = self.detail_link_routing.currentText()
            else:
                # Get from existing Link object if available
                if row_idx < len(self.project_data.links):
                    existing_link = self.project_data.links[row_idx]
                    line_color = existing_link.line_color
                    line_style = existing_link.line_style
                    link_routing = existing_link.link_routing
            
            # Create Link object
            link = Link(
                link_id=link_id,
                from_task_id=from_task_id,
                to_task_id=to_task_id,
                line_color=line_color,
                line_style=line_style,
                link_routing=link_routing
            )
            
            return link
        except (ValueError, TypeError, AttributeError) as e:
            logging.error(f"Error extracting link from table row {row_idx}: {e}")
            return None
    
    def _update_table_row_from_link(self, row_idx: int, link: Link, task_name_map: Dict[int, str]) -> None:
        """
        Populate a table row from a Link object.
        Uses column name mapping instead of positional indices.
        """
        # Update task names
        link.from_task_name = task_name_map.get(link.from_task_id, "")
        link.to_task_name = task_name_map.get(link.to_task_id, "")
        
        # Get column indices by name
        id_col = self._get_column_index("ID")
        from_id_col = self._get_column_index("From Task ID")
        from_name_col = self._get_column_index("From Task Name")
        to_id_col = self._get_column_index("To Task ID")
        to_name_col = self._get_column_index("To Task Name")
        valid_col = self._get_column_index("Valid")
        
        # Block signals to prevent recursive updates
        self.links_table.blockSignals(True)
        try:
            # Update ID column
            if id_col is not None:
                item = self.links_table.item(row_idx, id_col)
                if item:
                    item.setText(str(link.link_id))
                    item.setData(Qt.UserRole, link.link_id)
                else:
                    item = NumericTableWidgetItem(str(link.link_id))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                    item.setData(Qt.UserRole, link.link_id)
                    self.links_table.setItem(row_idx, id_col, item)
            
            # Update From Task ID column
            if from_id_col is not None:
                item = self.links_table.item(row_idx, from_id_col)
                if item:
                    item.setText(str(link.from_task_id))
                    item.setData(Qt.UserRole, link.from_task_id)
                else:
                    item = NumericTableWidgetItem(str(link.from_task_id))
                    item.setData(Qt.UserRole, link.from_task_id)
                    self.links_table.setItem(row_idx, from_id_col, item)
            
            # Update From Task Name column
            if from_name_col is not None:
                item = self.links_table.item(row_idx, from_name_col)
                display_text = self._truncate_text(link.from_task_name or "")
                if item:
                    item.setText(display_text)
                    item.setToolTip(link.from_task_name or "")
                else:
                    item = QTableWidgetItem(display_text)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                    item.setToolTip(link.from_task_name or "")
                    self.links_table.setItem(row_idx, from_name_col, item)
            
            # Update To Task ID column
            if to_id_col is not None:
                item = self.links_table.item(row_idx, to_id_col)
                if item:
                    item.setText(str(link.to_task_id))
                    item.setData(Qt.UserRole, link.to_task_id)
                else:
                    item = NumericTableWidgetItem(str(link.to_task_id))
                    item.setData(Qt.UserRole, link.to_task_id)
                    self.links_table.setItem(row_idx, to_id_col, item)
            
            # Update To Task Name column
            if to_name_col is not None:
                item = self.links_table.item(row_idx, to_name_col)
                display_text = self._truncate_text(link.to_task_name or "")
                if item:
                    item.setText(display_text)
                    item.setToolTip(link.to_task_name or "")
                else:
                    item = QTableWidgetItem(display_text)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                    item.setToolTip(link.to_task_name or "")
                    self.links_table.setItem(row_idx, to_name_col, item)
            
            # Update Valid column
            if valid_col is not None:
                # Calculate valid status if not already set
                if link.valid is None:
                    # Check if both task IDs are provided
                    if link.from_task_id <= 0 or link.to_task_id <= 0:
                        link.valid = "No"
                    else:
                        from_task = next((t for t in self.project_data.tasks if t.task_id == link.from_task_id), None)
                        to_task = next((t for t in self.project_data.tasks if t.task_id == link.to_task_id), None)
                        
                        if from_task and to_task:
                            from_finish_date = from_task.finish_date or from_task.start_date
                            to_start_date = to_task.start_date or to_task.finish_date
                            
                            if from_finish_date and to_start_date:
                                from_finish = parse_internal_date(from_finish_date)
                                to_start = parse_internal_date(to_start_date)
                                if from_finish and to_start:
                                    link.valid = "No" if to_start < from_finish else "Yes"
                                else:
                                    link.valid = "No"
                            else:
                                link.valid = "No"
                        else:
                            link.valid = "No"
                
                item = self.links_table.item(row_idx, valid_col)
                valid_value = link.valid or "No"  # Default to "No" instead of "Yes"
                if item:
                    item.setText(valid_value)
                else:
                    item = QTableWidgetItem(valid_value)
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                    self.links_table.setItem(row_idx, valid_col, item)
        finally:
            self.links_table.blockSignals(False)
    
    def _update_valid_column_only(self):
        """Update only the Valid column and task name columns without reloading the entire table."""
        # Get Link objects directly from project_data
        links = self.project_data.links
        task_name_map = {task.task_id: task.task_name for task in self.project_data.tasks}
        
        # Block signals to prevent recursive updates
        self.links_table.blockSignals(True)
        
        try:
            # Update Valid column and task name columns for each row using Link objects
            for row_idx in range(self.links_table.rowCount()):
                if row_idx < len(links):
                    link = links[row_idx]
                    # Use the helper method to update the row with computed fields
                    self._update_table_row_from_link(row_idx, link, task_name_map)
        finally:
            self.links_table.blockSignals(False)

