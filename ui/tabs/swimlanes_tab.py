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
        
        # Create table with columns: Select, ID, Row Count, Name
        headers = [col.name for col in self.table_config.columns]
        self.swimlanes_table = QTableWidget(0, len(headers))
        self.swimlanes_table.setHorizontalHeaderLabels(headers)
        
        # Table styling
        self.swimlanes_table.setAlternatingRowColors(False)
        self.swimlanes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.swimlanes_table.setSelectionMode(QTableWidget.SingleSelection)
        self.swimlanes_table.setShowGrid(True)
        self.swimlanes_table.verticalHeader().setVisible(False)
        
        # Add bottom border to header row and gridline styling
        self.swimlanes_table.setStyleSheet(self.app_config.general.table_stylesheet)
        
        # Column sizing
        header = self.swimlanes_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Select
        self.swimlanes_table.setColumnWidth(0, 50)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Row Count
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Name
        
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
        logging.debug(f"_on_detail_form_changed: _updating_form={self._updating_form}, _selected_swimlane_id={self._selected_swimlane_id}, _selected_row={self._selected_row}")
        if self._updating_form or self._selected_swimlane_id is None:
            logging.debug(f"_on_detail_form_changed: Early return - _updating_form={self._updating_form}, _selected_swimlane_id={self._selected_swimlane_id}")
            return
        
        if hasattr(self, 'detail_label_position') and self.detail_label_position:
            current_value = self.detail_label_position.currentText()
            logging.debug(f"_on_detail_form_changed: Triggering sync for swimlane_id={self._selected_swimlane_id}, label_position={current_value}")
        
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
        
        row = selected_rows[0].row()
        self._selected_row = row
        
        # Track the swimlane ID for this row (using key-based access)
        id_col = self._get_column_index("ID")
        if id_col is not None:
            id_item = self.swimlanes_table.item(row, id_col)
            if id_item:
                self._selected_swimlane_id = safe_int(id_item.text())
                logging.debug(f"_on_table_selection_changed: Selected row={row}, swimlane_id={self._selected_swimlane_id}")
            else:
                self._selected_swimlane_id = None
                logging.debug(f"_on_table_selection_changed: Selected row={row}, but no ID item found")
        else:
            self._selected_swimlane_id = None
            logging.debug(f"_on_table_selection_changed: Selected row={row}, but ID column not found")
        
        self._populate_detail_form(row)

    def _move_up(self):
        """Move selected row(s) up by one position."""
        # Get all checked rows (using checkboxes, consistent with Remove)
        checked_rows = []
        for row in range(self.swimlanes_table.rowCount()):
            checkbox_widget = self.swimlanes_table.cellWidget(row, 0)
            if checkbox_widget and isinstance(checkbox_widget, CheckBoxWidget):
                if checkbox_widget.checkbox.isChecked():
                    checked_rows.append(row)
        
        if not checked_rows:
            QMessageBox.information(self, "No Selection", "Please select row(s) to move up by checking their checkboxes.")
            return
        
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
            
            # Checkboxes maintain their state after swap (they're swapped with the row)
        finally:
            self.swimlanes_table.blockSignals(False)
            self.swimlanes_table.setSortingEnabled(was_sorting)
        
        # Sync data to update project_data
        self._sync_data_if_not_initializing()

    def _move_down(self):
        """Move selected row(s) down by one position."""
        # Get all checked rows (using checkboxes, consistent with Remove)
        checked_rows = []
        for row in range(self.swimlanes_table.rowCount()):
            checkbox_widget = self.swimlanes_table.cellWidget(row, 0)
            if checkbox_widget and isinstance(checkbox_widget, CheckBoxWidget):
                if checkbox_widget.checkbox.isChecked():
                    checked_rows.append(row)
        
        if not checked_rows:
            QMessageBox.information(self, "No Selection", "Please select row(s) to move down by checking their checkboxes.")
            return
        
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
            
            # Checkboxes maintain their state after swap (they're swapped with the row)
        finally:
            self.swimlanes_table.blockSignals(False)
            self.swimlanes_table.setSortingEnabled(was_sorting)
        
        # Sync data to update project_data
        self._sync_data_if_not_initializing()

    def _swap_table_rows(self, row1: int, row2: int):
        """Swap two table rows by exchanging all cell contents and widgets."""
        num_cols = self.swimlanes_table.columnCount()
        
        # Save checkbox states before removing widgets
        checkbox1_state = False
        checkbox2_state = False
        checkbox_widget1 = self.swimlanes_table.cellWidget(row1, 0)
        checkbox_widget2 = self.swimlanes_table.cellWidget(row2, 0)
        if checkbox_widget1 and isinstance(checkbox_widget1, CheckBoxWidget):
            checkbox1_state = checkbox_widget1.checkbox.isChecked()
        if checkbox_widget2 and isinstance(checkbox_widget2, CheckBoxWidget):
            checkbox2_state = checkbox_widget2.checkbox.isChecked()
        
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
        
        # Recreate checkboxes with swapped states (column 0 only)
        checkbox1_new = CheckBoxWidget()
        checkbox1_new.checkbox.setChecked(checkbox2_state)
        self.swimlanes_table.setCellWidget(row1, 0, checkbox1_new)
        
        checkbox2_new = CheckBoxWidget()
        checkbox2_new.checkbox.setChecked(checkbox1_state)
        self.swimlanes_table.setCellWidget(row2, 0, checkbox2_new)

    def _connect_signals(self):
        self.swimlanes_table.itemChanged.connect(self._on_item_changed)
        self.swimlanes_table.selectionModel().selectionChanged.connect(self._on_table_selection_changed)
    
    def _get_column_index(self, column_name: str) -> Optional[int]:
        """Get the column index for a given column name."""
        for idx, col_config in enumerate(self.table_config.columns):
            if col_config.name == column_name:
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
            # Add checkbox first (Select column)
            checkbox_widget = CheckBoxWidget()
            self.swimlanes_table.setCellWidget(row_idx, 0, checkbox_widget)

            # Use helper method to populate row from Swimlane object
            swimlane = swimlanes[row_idx]
            self._update_table_row_from_swimlane(row_idx, swimlane)
        
        # No sorting - order is explicit
        
        self._initializing = False
        
        # Disable detail form if no swimlanes exist or no selection
        if row_count == 0 or self._selected_swimlane_id is None:
            self._clear_detail_form()

    def _update_table_row_from_swimlane(self, row_idx: int, swimlane: Swimlane) -> None:
        """Populate a table row from a Swimlane object."""
        # Get column indices using key-based access
        id_col = self._get_column_index("ID")
        row_count_col = self._get_column_index("Row Count")
        title_col = self._get_column_index("Title")  # Changed from "Name"
        
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
            
            logging.debug(f"_swimlane_from_table_row(row_idx={row_idx}): swimlane_id={swimlane_id}, _selected_swimlane_id={self._selected_swimlane_id}")
            
            # Check if this swimlane's ID matches the one in the detail form
            if (self._selected_swimlane_id is not None and 
                swimlane_id == self._selected_swimlane_id and
                hasattr(self, 'detail_label_position') and 
                self.detail_label_position):
                label_position = self.detail_label_position.currentText()
                logging.debug(f"_swimlane_from_table_row(row_idx={row_idx}): Matched by ID, using detail form value: label_position={label_position}")
            else:
                # Get from existing swimlane (key-based lookup by ID)
                existing_swimlane = next((s for s in self.project_data.swimlanes if s.swimlane_id == swimlane_id), None)
                if existing_swimlane:
                    label_position = existing_swimlane.label_position if hasattr(existing_swimlane, 'label_position') else "Bottom Right"
                    logging.debug(f"_swimlane_from_table_row(row_idx={row_idx}): Using existing swimlane value: label_position={label_position}")
                else:
                    logging.debug(f"_swimlane_from_table_row(row_idx={row_idx}): No match, using default: label_position={label_position}")
            
            logging.debug(f"_swimlane_from_table_row(row_idx={row_idx}): Final swimlane - id={swimlane_id}, title={title}, label_position={label_position}")
            
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
        
        logging.debug(f"_sync_data_impl: Starting sync, _selected_swimlane_id={self._selected_swimlane_id}, _selected_row={self._selected_row}")
        
        try:
            # Extract Swimlane objects from table rows (order matters!)
            swimlanes = []
            for row_idx in range(self.swimlanes_table.rowCount()):
                try:
                    swimlane = self._swimlane_from_table_row(row_idx)
                    if swimlane:
                        swimlanes.append(swimlane)
                        logging.debug(f"_sync_data_impl: Extracted swimlane id={swimlane.swimlane_id}, label_position={swimlane.label_position}")
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
            logging.debug(f"_sync_data_impl: Updating project_data.swimlanes with {len(swimlanes)} swimlanes")
            for s in swimlanes:
                logging.debug(f"_sync_data_impl: Final swimlane id={s.swimlane_id}, title={s.title}, label_position={s.label_position}")
            self.project_data.swimlanes = swimlanes
            logging.debug(f"_sync_data_impl: Sync complete")
        except Exception as e:
            # Catch any unexpected exceptions during sync
            logging.error(f"Error in _sync_data_impl: {e}", exc_info=True)
            raise  # Re-raise so BaseTab can show error message
