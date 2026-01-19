from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                             QHBoxLayout, QHeaderView, QTableWidgetItem, 
                             QMessageBox, QGroupBox, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from typing import List, Dict, Any, Optional
import logging
from ui.table_utils import NumericTableWidgetItem, add_row, remove_row, CheckBoxWidget
from .base_tab import BaseTab
from models.swimlane import Swimlane
from utils.conversion import safe_int

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SwimlanesTab(BaseTab):
    data_updated = pyqtSignal(dict)
    

    def __init__(self, project_data, app_config):
        self.table_config = app_config.get_table_config("swimlanes")
        self._selected_row = None  # Track currently selected row
        self._selected_swimlane_id = None  # Track selected swimlane ID for detail form matching
        self._updating_form = False  # Prevent circular updates
        self.detail_label_position = None  # Will be initialized in setup_ui
        self._detail_form_widgets = []  # Will be populated in _create_detail_form
        super().__init__(project_data, app_config)

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create toolbar with buttons
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        
        add_btn = QPushButton("Add Swimlane")
        add_btn.setToolTip("Add a new swimlane at the end")
        add_btn.setMinimumWidth(120)
        add_btn.clicked.connect(lambda: add_row(self.swimlanes_table, "swimlanes", self.app_config.tables, self, "ID"))
        
        remove_btn = QPushButton("Remove Swimlane")
        remove_btn.setToolTip("Remove selected swimlane(s)")
        remove_btn.setMinimumWidth(120)
        remove_btn.clicked.connect(lambda: remove_row(self.swimlanes_table, "swimlanes", 
                                                    self.app_config.tables, self))
        
        move_up_btn = QPushButton("Move Up")
        move_up_btn.setToolTip("Move selected swimlane(s) up")
        move_up_btn.setMinimumWidth(100)
        move_up_btn.clicked.connect(self._move_up)
        
        move_down_btn = QPushButton("Move Down")
        move_down_btn.setToolTip("Move selected swimlane(s) down")
        move_down_btn.setMinimumWidth(100)
        move_down_btn.clicked.connect(self._move_down)
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addWidget(move_up_btn)
        toolbar.addWidget(move_down_btn)
        toolbar.addStretch()  # Push buttons to the left
        
        # Create group box for table
        table_group = QGroupBox("Swimlanes")
        table_group_layout = QVBoxLayout()
        table_group_layout.setSpacing(5)
        table_group_layout.setContentsMargins(5, 10, 5, 5)
        
        # Create table with all columns
        headers = [col.name for col in self.table_config.columns]
        self.swimlanes_table = QTableWidget(0, len(headers))
        self.swimlanes_table.setHorizontalHeaderLabels(headers)
        
        # Find ID column index and move it to the end (after Title)
        id_col = headers.index("ID") if "ID" in headers else None
        title_col = headers.index("Title") if "Title" in headers else None
        if id_col is not None and title_col is not None:
            # Move ID column to be after Title (at the end)
            header = self.swimlanes_table.horizontalHeader()
            # Move ID to the last position
            last_col = self.swimlanes_table.columnCount() - 1
            if id_col < last_col:
                header.moveSection(id_col, last_col)
        
        # Table styling
        self.swimlanes_table.setAlternatingRowColors(False)
        self.swimlanes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.swimlanes_table.setSelectionMode(QTableWidget.ExtendedSelection)  # Extended selection for bulk operations, detail form shows first selected
        self.swimlanes_table.setShowGrid(True)
        self.swimlanes_table.verticalHeader().setVisible(False)
        
        # Add bottom border to header row and gridline styling
        self.swimlanes_table.setStyleSheet(self.app_config.general.table_stylesheet)
        
        # Column sizing - find columns by name (key-based, not positional)
        header = self.swimlanes_table.horizontalHeader()
        
        # Find Lane column by name
        lane_col = None
        for i in range(self.swimlanes_table.columnCount()):
            if self.swimlanes_table.horizontalHeaderItem(i).text() == "Lane":
                lane_col = i
                break
        
        if lane_col is not None:
            header.setSectionResizeMode(lane_col, QHeaderView.Fixed)  # Lane
            self.swimlanes_table.setColumnWidth(lane_col, 60)
        
        # Find Row Count, Title, and ID columns by name (after move)
        row_count_col = None
        title_col = None
        id_col = None
        for i in range(self.swimlanes_table.columnCount()):
            col_name = self.swimlanes_table.horizontalHeaderItem(i).text()
            if col_name == "Row Count":
                row_count_col = i
            elif col_name == "Title":
                title_col = i
            elif col_name == "ID":
                id_col = i
        
        if row_count_col is not None:
            header.setSectionResizeMode(row_count_col, QHeaderView.ResizeToContents)  # Row Count
        if title_col is not None:
            header.setSectionResizeMode(title_col, QHeaderView.Stretch)  # Title
        if id_col is not None:
            header.setSectionResizeMode(id_col, QHeaderView.ResizeToContents)  # ID (at end)
        
        # Enable horizontal scroll bar
        self.swimlanes_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        # DISABLE sorting - order matters for swimlanes
        self.swimlanes_table.setSortingEnabled(False)
        
        # Set table size policy
        self.swimlanes_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        table_group_layout.addLayout(toolbar)
        table_group_layout.addWidget(self.swimlanes_table)
        table_group.setLayout(table_group_layout)
        
        # Add table group with stretch factor so it expands to fill available space
        layout.addWidget(table_group, 1)
        
        # Create detail form group box (empty for now, reserved for future properties)
        detail_group = self._create_detail_form()
        layout.addWidget(detail_group)
        
        self.setLayout(layout)

    def _create_detail_form(self) -> QGroupBox:
        """Create the detail form for editing swimlane properties."""
        from PyQt5.QtWidgets import QLabel, QComboBox, QGridLayout
        
        group = QGroupBox("Swimlane Properties")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        LABEL_WIDTH = 120
        
        # Label Position
        position_label = QLabel("Label Position:")
        position_label.setFixedWidth(LABEL_WIDTH)
        self.detail_label_position = QComboBox()
        self.detail_label_position.addItems(["Bottom Right", "Bottom Left", "Top Left", "Top Right"])
        self.detail_label_position.setToolTip("Position of the swimlane title label")
        self.detail_label_position.currentTextChanged.connect(self._on_detail_form_changed)
        # Disable by default - will be enabled when a swimlane is selected
        self.detail_label_position.setEnabled(False)
        
        # Store list of detail form widgets for easy enable/disable
        self._detail_form_widgets = [self.detail_label_position]
        
        layout.addWidget(position_label, 0, 0)
        layout.addWidget(self.detail_label_position, 0, 1)
        layout.setColumnStretch(1, 1)
        
        group.setLayout(layout)
        return group
    
    def _on_detail_form_changed(self):
        """Handle changes in detail form - update selected swimlane."""
        if self._updating_form or self._selected_swimlane_id is None:
            return
        
        # Trigger sync to update the data
        self._sync_data_if_not_initializing()
    
    def _populate_detail_form(self, row: int):
        """Populate detail form with data from selected swimlane."""
        self._updating_form = True
        
        try:
            if row < len(self.project_data.swimlanes):
                swimlane = self.project_data.swimlanes[row]
                label_position = swimlane.label_position if hasattr(swimlane, 'label_position') else "Bottom Right"
                self.detail_label_position.setCurrentText(label_position)
                # Enable detail form widgets when a valid swimlane is selected
                self._set_detail_form_enabled(self._detail_form_widgets, True)
            else:
                self.detail_label_position.setCurrentText("Bottom Right")
                self._set_detail_form_enabled(self._detail_form_widgets, False)
        finally:
            self._updating_form = False
    
    def _clear_detail_form(self):
        """Clear the detail form when no swimlane is selected."""
        self._updating_form = True
        try:
            self.detail_label_position.setCurrentText("Bottom Right")
            # Disable detail form widgets when no swimlane is selected
            self._set_detail_form_enabled(self._detail_form_widgets, False)
        finally:
            self._updating_form = False
    
    def _on_table_selection_changed(self):
        """Handle table selection changes - populate detail form."""
        selected_rows = self.swimlanes_table.selectionModel().selectedRows()
        if not selected_rows:
            self._selected_row = None
            self._selected_swimlane_id = None
            self._clear_detail_form()
            return
        
        # Show detail form only when exactly one row is selected
        if len(selected_rows) == 1:
            row = selected_rows[0].row()
            self._selected_row = row
            
            # Track the swimlane ID for this row (using key-based access)
            id_col = self._get_column_index("ID")
            if id_col is not None:
                id_item = self.swimlanes_table.item(row, id_col)
                if id_item:
                    self._selected_swimlane_id = safe_int(id_item.text())
                else:
                    self._selected_swimlane_id = None
            else:
                self._selected_swimlane_id = None
            
            self._populate_detail_form(row)
        else:
            # Multiple rows selected - clear detail form
            self._selected_row = None
            self._selected_swimlane_id = None
            self._clear_detail_form()

    def _move_up(self):
        """Move selected row(s) up by one position."""
        # Get all selected rows
        selected_rows = self.swimlanes_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select row(s) to move up.")
            return
        
        checked_rows = [row.row() for row in selected_rows]
        
        # Store selected swimlane IDs before moving (for selection restoration)
        id_col = self._get_column_index("ID")
        selected_swimlane_ids = set()
        if id_col is not None:
            for row_idx in checked_rows:
                item = self.swimlanes_table.item(row_idx, id_col)
                if item:
                    try:
                        swimlane_id = int(item.text())
                        selected_swimlane_ids.add(swimlane_id)
                    except (ValueError, TypeError):
                        continue
        
        # Get sorted row indices
        row_indices = sorted(checked_rows)
        
        # Check if any row is already at the top
        if row_indices[0] == 0:
            QMessageBox.information(self, "Cannot Move", "Selected row(s) are already at the top.")
            return
        
        # Block signals and disable sorting during move
        self.swimlanes_table.blockSignals(True)
        was_sorting = self.swimlanes_table.isSortingEnabled()
        self.swimlanes_table.setSortingEnabled(False)
        
        try:
            # Move rows from top to bottom to avoid index shifting issues
            for row_idx in row_indices:
                if row_idx > 0:
                    # Swap rows by moving current row up
                    self._swap_table_rows(row_idx, row_idx - 1)
        finally:
            self.swimlanes_table.blockSignals(False)
            self.swimlanes_table.setSortingEnabled(was_sorting)
        
        # Refresh Lane column after move
        self._refresh_lane_column()
        
        # Sync data to update project_data
        self._sync_data_if_not_initializing()
        
        # Restore selection on moved rows
        if selected_swimlane_ids and id_col is not None:
            selection_model = self.swimlanes_table.selectionModel()
            selection_model.clearSelection()
            first_selected = True
            for row_idx in range(self.swimlanes_table.rowCount()):
                item = self.swimlanes_table.item(row_idx, id_col)
                if item:
                    try:
                        swimlane_id = int(item.text())
                        if swimlane_id in selected_swimlane_ids:
                            # Select the entire row using selection model (adds to selection, doesn't replace)
                            row_index = self.swimlanes_table.model().index(row_idx, 0)
                            selection_model.select(row_index, selection_model.Select | selection_model.Rows)
                            # Scroll to first selected row
                            if first_selected:
                                self.swimlanes_table.scrollToItem(item)
                                first_selected = False
                    except (ValueError, TypeError):
                        continue

    def _move_down(self):
        """Move selected row(s) down by one position."""
        # Get all selected rows
        selected_rows = self.swimlanes_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "No Selection", "Please select row(s) to move down.")
            return
        
        checked_rows = [row.row() for row in selected_rows]
        
        # Store selected swimlane IDs before moving (for selection restoration)
        id_col = self._get_column_index("ID")
        selected_swimlane_ids = set()
        if id_col is not None:
            for row_idx in checked_rows:
                item = self.swimlanes_table.item(row_idx, id_col)
                if item:
                    try:
                        swimlane_id = int(item.text())
                        selected_swimlane_ids.add(swimlane_id)
                    except (ValueError, TypeError):
                        continue
        
        # Get sorted row indices (reverse order for moving down)
        row_indices = sorted(checked_rows, reverse=True)
        max_row = self.swimlanes_table.rowCount() - 1
        
        # Check if the highest selected row is already at the bottom
        if max_row < 0 or row_indices[0] >= max_row:
            QMessageBox.information(self, "Cannot Move", "Selected row(s) are already at the bottom.")
            return
        
        # Block signals and disable sorting during move
        self.swimlanes_table.blockSignals(True)
        was_sorting = self.swimlanes_table.isSortingEnabled()
        self.swimlanes_table.setSortingEnabled(False)
        
        try:
            # Move rows from bottom to top to avoid index shifting issues
            for row_idx in row_indices:
                if row_idx < max_row:
                    # Swap rows by moving current row down
                    self._swap_table_rows(row_idx, row_idx + 1)
        finally:
            self.swimlanes_table.blockSignals(False)
            self.swimlanes_table.setSortingEnabled(was_sorting)
        
        # Refresh Lane column after move
        self._refresh_lane_column()
        
        # Sync data to update project_data
        self._sync_data_if_not_initializing()
        
        # Restore selection on moved rows
        if selected_swimlane_ids and id_col is not None:
            selection_model = self.swimlanes_table.selectionModel()
            selection_model.clearSelection()
            first_selected = True
            for row_idx in range(self.swimlanes_table.rowCount()):
                item = self.swimlanes_table.item(row_idx, id_col)
                if item:
                    try:
                        swimlane_id = int(item.text())
                        if swimlane_id in selected_swimlane_ids:
                            # Select the entire row using selection model (adds to selection, doesn't replace)
                            row_index = self.swimlanes_table.model().index(row_idx, 0)
                            selection_model.select(row_index, selection_model.Select | selection_model.Rows)
                            # Scroll to first selected row
                            if first_selected:
                                self.swimlanes_table.scrollToItem(item)
                                first_selected = False
                    except (ValueError, TypeError):
                        continue

    def _swap_table_rows(self, row1: int, row2: int):
        """Swap two table rows by exchanging all cell contents and widgets."""
        num_cols = self.swimlanes_table.columnCount()
        
        # Collect all items from both rows
        items1 = [self.swimlanes_table.takeItem(row1, col) for col in range(num_cols)]
        items2 = [self.swimlanes_table.takeItem(row2, col) for col in range(num_cols)]
        
        # Remove all widgets from both rows
        for col in range(num_cols):
            widget1 = self.swimlanes_table.cellWidget(row1, col)
            widget2 = self.swimlanes_table.cellWidget(row2, col)
            if widget1:
                self.swimlanes_table.removeCellWidget(row1, col)
            if widget2:
                self.swimlanes_table.removeCellWidget(row2, col)
        
        # Set items in swapped positions
        for col in range(num_cols):
            if items2[col]:
                self.swimlanes_table.setItem(row1, col, items2[col])
            if items1[col]:
                self.swimlanes_table.setItem(row2, col, items1[col])

    def _refresh_lane_column(self):
        """Refresh the Lane column for all rows based on their current positions."""
        lane_col = self._get_column_index("Lane")
        if lane_col is None:
            return
        
        for row_idx in range(self.swimlanes_table.rowCount()):
            lane_value = row_idx + 1  # 1-based order
            item = self.swimlanes_table.item(row_idx, lane_col)
            if item:
                item.setText(str(lane_value))
                # Ensure it's read-only
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
            else:
                item = NumericTableWidgetItem(str(lane_value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                self.swimlanes_table.setItem(row_idx, lane_col, item)
    
    def _connect_signals(self):
        self.swimlanes_table.itemChanged.connect(self._on_item_changed)
        self.swimlanes_table.selectionModel().selectionChanged.connect(self._on_table_selection_changed)
    
    def _get_column_index(self, column_name: str) -> Optional[int]:
        """Get the column index for a given column name (searches actual table headers)."""
        for idx in range(self.swimlanes_table.columnCount()):
            header_text = self.swimlanes_table.horizontalHeaderItem(idx).text()
            if header_text == column_name:
                return idx
        return None
    
    def _get_column_name_from_item(self, item) -> Optional[str]:
        """Get the column name (key) from a table item."""
        if item is None:
            return None
        try:
            col_idx = item.column()
            if not isinstance(col_idx, int) or col_idx < 0 or col_idx >= len(self.table_config.columns):
                return None
            return self.table_config.columns[col_idx].name
        except (IndexError, AttributeError):
            return None
    
    def _on_item_changed(self, item):
        """Handle item changes - update UserRole for numeric columns."""
        if item is None:
            return
        
        # CRITICAL: Disconnect signal BEFORE modifying item to prevent infinite loop
        was_connected = False
        try:
            self.swimlanes_table.itemChanged.disconnect(self._on_item_changed)
            was_connected = True
        except:
            pass  # Signal might not be connected
        
        try:
            # Get column name (key) from item
            col_name = self._get_column_name_from_item(item)
            if col_name is None:
                return
            
            # Don't trigger sync for ID column changes (it's read-only)
            if col_name == "ID":
                return
            
            # Update UserRole for numeric columns (ID, Row Count)
            if col_name in ["ID", "Row Count"]:
                try:
                    val_str = item.text().strip()
                    item.setData(Qt.UserRole, int(val_str) if val_str else 0)
                except (ValueError, AttributeError):
                    item.setData(Qt.UserRole, 0)
            
            # Trigger sync
            self._sync_data_if_not_initializing()
        except Exception as e:
            # Catch any unexpected exceptions to prevent crashes
            logging.error(f"Error in _on_item_changed: {e}", exc_info=True)
            # Don't re-raise - just log and continue
        finally:
            # Reconnect signal if it was connected
            if was_connected:
                try:
                    self.swimlanes_table.itemChanged.connect(self._on_item_changed)
                except:
                    pass

    def _load_initial_data_impl(self):
        """Load initial data into the table using Swimlane objects directly."""
        swimlanes = self.project_data.swimlanes
        row_count = len(swimlanes)
        self.swimlanes_table.setRowCount(row_count)
        self._initializing = True

        for row_idx in range(row_count):

            # Use helper method to populate row from Swimlane object
            swimlane = swimlanes[row_idx]
            self._update_table_row_from_swimlane(row_idx, swimlane)
        
        # No sorting - order is explicit
        
        self._initializing = False
        
        # Disable detail form if no swimlanes exist or no selection
        if row_count == 0 or self._selected_swimlane_id is None:
            self._clear_detail_form()
        
        # Refresh Lane column to ensure all rows have correct lane values
        self._refresh_lane_column()

    def _update_table_row_from_swimlane(self, row_idx: int, swimlane: Swimlane) -> None:
        """Populate a table row from a Swimlane object."""
        # Get column indices using key-based access
        lane_col = self._get_column_index("Lane")
        id_col = self._get_column_index("ID")
        row_count_col = self._get_column_index("Row Count")
        title_col = self._get_column_index("Title")  # Changed from "Name"
        
        # Update Lane column (read-only, calculated from row position)
        if lane_col is not None:
            lane_value = row_idx + 1  # 1-based order
            item = self.swimlanes_table.item(row_idx, lane_col)
            if item:
                item.setText(str(lane_value))
                # Ensure it's read-only even if item already exists
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
            else:
                item = NumericTableWidgetItem(str(lane_value))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                self.swimlanes_table.setItem(row_idx, lane_col, item)
        
        # Update ID column
        if id_col is not None:
            item = self.swimlanes_table.item(row_idx, id_col)
            if item:
                item.setText(str(swimlane.swimlane_id))
                item.setData(Qt.UserRole, swimlane.swimlane_id)
            else:
                item = NumericTableWidgetItem(str(swimlane.swimlane_id))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                item.setData(Qt.UserRole, swimlane.swimlane_id)
                self.swimlanes_table.setItem(row_idx, id_col, item)
        
        # Update Row Count column
        if row_count_col is not None:
            item = self.swimlanes_table.item(row_idx, row_count_col)
            if item:
                item.setText(str(swimlane.row_count))
                item.setData(Qt.UserRole, swimlane.row_count)
            else:
                item = NumericTableWidgetItem(str(swimlane.row_count))
                item.setData(Qt.UserRole, swimlane.row_count)
                self.swimlanes_table.setItem(row_idx, row_count_col, item)
        
        # Update Title column (changed from Name)
        title_col = self._get_column_index("Title")
        if title_col is not None:
            item = self.swimlanes_table.item(row_idx, title_col)
            if item:
                item.setText(swimlane.title if swimlane.title else "")
            else:
                item = QTableWidgetItem(swimlane.title if swimlane.title else "")
                self.swimlanes_table.setItem(row_idx, title_col, item)

    def _swimlane_from_table_row(self, row_idx: int) -> Optional[Swimlane]:
        """Extract a Swimlane object from a table row."""
        try:
            # Get column indices using key-based access
            id_col = self._get_column_index("ID")
            row_count_col = self._get_column_index("Row Count")
            title_col = self._get_column_index("Title")  # Changed from "Name"
            
            if id_col is None or row_count_col is None:
                return None
            
            # Extract ID
            id_item = self.swimlanes_table.item(row_idx, id_col)
            if not id_item:
                return None
            swimlane_id = safe_int(id_item.text())
            if swimlane_id <= 0:
                return None
            
            # Extract Row Count
            row_count_item = self.swimlanes_table.item(row_idx, row_count_col)
            if not row_count_item or not row_count_item.text().strip():
                return None
            row_count = safe_int(row_count_item.text())
            if row_count <= 0:
                return None
            
            # Extract Title (changed from Name)
            title = ""
            if title_col is not None:
                title_item = self.swimlanes_table.item(row_idx, title_col)
                if title_item:
                    title = title_item.text().strip()
            
            # Get label_position from detail form if this swimlane ID matches the selected one
            # Otherwise, get from existing Swimlane object
            # Use key-based matching by ID instead of row index for reliability
            label_position = "Bottom Right"
            
            # Check if this swimlane's ID matches the one in the detail form
            if (self._selected_swimlane_id is not None and 
                swimlane_id == self._selected_swimlane_id and
                hasattr(self, 'detail_label_position') and 
                self.detail_label_position):
                label_position = self.detail_label_position.currentText()
            else:
                # Get from existing swimlane (key-based lookup by ID)
                existing_swimlane = next((s for s in self.project_data.swimlanes if s.swimlane_id == swimlane_id), None)
                if existing_swimlane:
                    label_position = existing_swimlane.label_position if hasattr(existing_swimlane, 'label_position') else "Bottom Right"
            
            return Swimlane(
                swimlane_id=swimlane_id,
                row_count=row_count,
                title=title,
                label_position=label_position
            )
        except (ValueError, AttributeError, Exception) as e:
            logging.error(f"Error extracting swimlane from table row {row_idx}: {e}")
            return None

    def _validate_swimlanes(self, swimlanes: List[Swimlane]) -> List[str]:
        """Validate swimlanes and return list of error messages."""
        errors = []
        
        # Check each swimlane has valid row_count
        for swimlane in swimlanes:
            if swimlane.row_count <= 0:
                errors.append(f"Swimlane ID {swimlane.swimlane_id}: Row Count must be greater than 0")
        
        return errors

    def _sync_data_impl(self):
        """Extract data from table and update project_data using Swimlane objects directly."""
        if self._initializing:
            return
        
        
        try:
            # Extract Swimlane objects from table rows (order matters!)
            swimlanes = []
            for row_idx in range(self.swimlanes_table.rowCount()):
                try:
                    swimlane = self._swimlane_from_table_row(row_idx)
                    if swimlane:
                        swimlanes.append(swimlane)
                except Exception as e:
                    # Log error for this specific row but continue processing other rows
                    logging.error(f"Error extracting swimlane from row {row_idx}: {e}")
                    continue
            
            # Validate all swimlanes
            validation_errors = self._validate_swimlanes(swimlanes)
            
            if validation_errors:
                error_msg = "Validation errors:\n" + "\n".join(validation_errors)
                QMessageBox.warning(self, "Validation Error", error_msg)
                # Don't update project_data if validation fails
                return
            
            # Update project data with Swimlane objects directly (order is preserved)
            self.project_data.swimlanes = swimlanes
            
            # Refresh Lane column after sync (in case rows were added/removed)
            self._refresh_lane_column()
            
            # Emit data_updated signal so other tabs (like Tasks) can refresh swimlane-dependent columns
            self.data_updated.emit({})
            
        except Exception as e:
            # Catch any unexpected exceptions during sync
            logging.error(f"Error in _sync_data_impl: {e}", exc_info=True)
            raise  # Re-raise so BaseTab can show error message
