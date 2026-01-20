from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                           QHBoxLayout, QHeaderView, QTableWidgetItem, 
                           QMessageBox, QGroupBox, QSizePolicy, QComboBox, QLabel, QGridLayout, QDateEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QBrush, QColor
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from ui.table_utils import NumericTableWidgetItem, add_row, remove_row, CheckBoxWidget, DateTableWidgetItem, DateEditWidget
from .base_tab import BaseTab
from models.curtain import Curtain
from utils.conversion import safe_int, display_to_internal_date, internal_to_display_date, normalize_display_date

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CurtainsTab(BaseTab):
    data_updated = pyqtSignal(dict)
    

    def __init__(self, project_data, app_config):
        self.table_config = app_config.get_table_config("curtains")
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
        
        add_btn = QPushButton("Add Curtain")
        add_btn.setToolTip("Add a new curtain")
        add_btn.setMinimumWidth(120)
        add_btn.clicked.connect(lambda: add_row(self.curtains_table, "curtains", self.app_config.tables, self, "ID", date_config=self.app_config.general.ui_date_config))
        
        remove_btn = QPushButton("Remove Curtain")
        remove_btn.setToolTip("Remove selected curtain(s)")
        remove_btn.setMinimumWidth(120)
        remove_btn.clicked.connect(lambda: remove_row(self.curtains_table, "curtains", 
                                                    self.app_config.tables, self))
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addStretch()  # Push buttons to the left
        
        # Create group box for table
        table_group = QGroupBox("Curtains")
        table_group_layout = QVBoxLayout()
        table_group_layout.setSpacing(5)
        table_group_layout.setContentsMargins(5, 10, 5, 5)
        
        # Create table with all columns: Select, ID, Start Date, End Date, Color, Name
        headers = [col.name for col in self.table_config.columns]
        self.curtains_table = QTableWidget(0, len(headers))
        self.curtains_table.setHorizontalHeaderLabels(headers)
        
        # Table styling
        self.curtains_table.setAlternatingRowColors(False)
        self.curtains_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.curtains_table.setSelectionMode(QTableWidget.ExtendedSelection)  # Extended selection for bulk operations, detail form shows first selected
        self.curtains_table.setShowGrid(True)
        self.curtains_table.verticalHeader().setVisible(False)
        
        # Add bottom border to header row and gridline styling
        self.curtains_table.setStyleSheet(self.app_config.general.table_stylesheet)
        
        # Column sizing - use key-based lookups instead of positional indices
        header = self.curtains_table.horizontalHeader()
        
        # Find columns by name and set their sizing
        id_col = None
        start_date_col = None
        end_date_col = None
        name_col = None
        
        for i in range(self.curtains_table.columnCount()):
            header_text = self.curtains_table.horizontalHeaderItem(i).text()
            if header_text == "ID":
                id_col = i
            elif header_text == "Start Date":
                start_date_col = i
            elif header_text == "End Date":
                end_date_col = i
            elif header_text == "Name":
                name_col = i
        
        if id_col is not None:
            header.setSectionResizeMode(id_col, QHeaderView.ResizeToContents)
        if start_date_col is not None:
            header.setSectionResizeMode(start_date_col, QHeaderView.ResizeToContents)
        if end_date_col is not None:
            header.setSectionResizeMode(end_date_col, QHeaderView.ResizeToContents)
        if name_col is not None:
            header.setSectionResizeMode(name_col, QHeaderView.Stretch)
        
        # Enable horizontal scroll bar
        self.curtains_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.curtains_table.setSortingEnabled(True)
        
        # Set table size policy
        self.curtains_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        table_group_layout.addLayout(toolbar)
        table_group_layout.addWidget(self.curtains_table)
        table_group.setLayout(table_group_layout)
        
        # Add table group with stretch factor so it expands to fill available space
        layout.addWidget(table_group, 1)
        
        # Create detail form group box
        detail_group = self._create_detail_form()
        layout.addWidget(detail_group)
        
        self.setLayout(layout)

    def _create_detail_form(self) -> QGroupBox:
        """Create the detail form for editing curtain color."""
        group = QGroupBox("Curtain Formatting")
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        LABEL_WIDTH = 120
        
        # Color
        color_label = QLabel("Color:")
        color_label.setFixedWidth(LABEL_WIDTH)
        self.detail_color = QComboBox()
        self.detail_color.addItems(["blue", "red", "green", "yellow", "orange", "purple", "gray", "black", "cyan", "magenta", "brown"])
        self.detail_color.setToolTip("Color of the curtain lines and hatching")
        self.detail_color.currentTextChanged.connect(self._on_detail_form_changed)
        # Disable by default - will be enabled when a curtain is selected
        self.detail_color.setEnabled(False)
        
        # Store list of detail form widgets for easy enable/disable
        self._detail_form_widgets = [self.detail_color]
        
        layout.addWidget(color_label, 0, 0)
        layout.addWidget(self.detail_color, 0, 1)
        layout.setColumnStretch(1, 1)
        
        group.setLayout(layout)
        return group

    def _on_table_selection_changed(self):
        """Handle table selection changes - populate detail form."""
        selected_rows = self.curtains_table.selectionModel().selectedRows()
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
        """Populate detail form with data from selected curtain."""
        self._updating_form = True
        
        try:
            # Get Curtain object directly from project_data
            if row < len(self.project_data.curtains):
                curtain = self.project_data.curtains[row]
                self.detail_color.setCurrentText(curtain.color if curtain.color else "red")
                # Enable detail form widgets when a valid curtain is selected
                self._set_detail_form_enabled(self._detail_form_widgets, True)
            else:
                # Use defaults if curtain doesn't exist
                self.detail_color.setCurrentText("red")
                self._set_detail_form_enabled(self._detail_form_widgets, False)
        finally:
            self._updating_form = False

    def _clear_detail_form(self):
        """Clear the detail form when no curtain is selected."""
        self._updating_form = True
        try:
            self.detail_color.setCurrentText("red")
            # Disable detail form widgets when no curtain is selected
            self._set_detail_form_enabled(self._detail_form_widgets, False)
        finally:
            self._updating_form = False

    def _on_detail_form_changed(self):
        """Handle changes in detail form - update selected curtain."""
        if self._updating_form or self._selected_row is None:
            return
        
        # Trigger sync to update the data
        self._sync_data_if_not_initializing()

    def _connect_signals(self):
        self.curtains_table.itemChanged.connect(self._on_item_changed)
        self.curtains_table.selectionModel().selectionChanged.connect(self._on_table_selection_changed)
    
    def _on_item_changed(self, item):
        """Handle item changes - update UserRole for numeric and date columns."""
        if item is None:
            return
        
        # CRITICAL: Disconnect signal BEFORE modifying item to prevent infinite loop
        was_connected = False
        try:
            self.curtains_table.itemChanged.disconnect(self._on_item_changed)
            was_connected = True
        except:
            pass  # Signal might not be connected
        
        try:
            # Get column name (key) from item
            col_name = self._get_column_name_from_item(item)
            if col_name is None:
                return
            
            # Get row and column index
            row = item.row()
            col_idx = item.column()
            
            # Don't trigger sync for ID column changes (it's read-only)
            if col_name == "ID":
                return
            
            # Skip date columns - QDateEdit widgets handle their own changes via dateChanged signal
            if col_name in ["Start Date", "End Date"]:
                # Check if this is actually a QDateEdit widget (shouldn't trigger itemChanged)
                date_widget = self.curtains_table.cellWidget(row, col_idx)
                if isinstance(date_widget, QDateEdit):
                    # QDateEdit handles its own changes, skip processing
                    return
                # Fallback: if it's a text item (backward compatibility), process it
                try:
                    val_str = item.text().strip()
                    if val_str:
                        try:
                            normalized = normalize_display_date(val_str)
                            date_obj = datetime.strptime(normalized, "%d/%m/%Y")
                            item.setData(Qt.UserRole, date_obj)
                        except ValueError:
                            item.setData(Qt.UserRole, None)
                    else:
                        item.setData(Qt.UserRole, None)
                except Exception as e:
                    logging.error(f"Error processing date in _on_item_changed: {e}")
                    item.setData(Qt.UserRole, None)
            
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
                    self.curtains_table.itemChanged.connect(self._on_item_changed)
                except:
                    pass

    def _load_initial_data_impl(self):
        """Load initial data into the table using Curtain objects directly."""
        curtains = self.project_data.curtains
        row_count = len(curtains)
        self.curtains_table.setRowCount(row_count)
        self._initializing = True

        for row_idx in range(row_count):

            # Use helper method to populate row from Curtain object
            curtain = curtains[row_idx]
            self._update_table_row_from_curtain(row_idx, curtain)
        
        # Sort by ID by default
        id_col = self._get_column_index("ID")
        if id_col is not None:
            self.curtains_table.sortItems(id_col, Qt.AscendingOrder)
        
        self._initializing = False
        
        # Disable detail form if no curtains exist or no selection
        if row_count == 0 or self._selected_row is None:
            self._clear_detail_form()

    def _update_table_row_from_curtain(self, row_idx: int, curtain: Curtain) -> None:
        """Populate a table row from a Curtain object."""
        headers = [col.name for col in self.table_config.columns]
        
        # Get column indices
        id_col = self._get_column_index("ID")
        start_date_col = self._get_column_index("Start Date")
        end_date_col = self._get_column_index("End Date")
        name_col = self._get_column_index("Name")
        
        # Update ID column
        if id_col is not None:
            item = self.curtains_table.item(row_idx, id_col)
            if item:
                item.setText(str(curtain.curtain_id))
                item.setData(Qt.UserRole, curtain.curtain_id)
            else:
                item = NumericTableWidgetItem(str(curtain.curtain_id))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                item.setData(Qt.UserRole, curtain.curtain_id)
                self.curtains_table.setItem(row_idx, id_col, item)
        
        # Update Start Date column (QDateEdit widget)
        if start_date_col is not None:
            date_widget = self.curtains_table.cellWidget(row_idx, start_date_col)
            if date_widget and isinstance(date_widget, QDateEdit):
                # Update existing QDateEdit widget
                if curtain.start_date:
                    try:
                        start_dt = datetime.strptime(curtain.start_date, "%Y-%m-%d")
                        start_qdate = QDate(start_dt.year, start_dt.month, start_dt.day)
                        date_widget.blockSignals(True)
                        date_widget.setDate(start_qdate)
                        date_widget.blockSignals(False)
                    except ValueError:
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
                date_widget.dateChanged.connect(lambda date, w=date_widget: self._update_curtain_date_constraints(widget=w))
                date_widget.dateChanged.connect(self._sync_data_if_not_initializing)
            else:
                # Create QDateEdit if it doesn't exist
                from ui.table_utils import create_date_widget
                date_widget = create_date_widget(curtain.start_date if curtain.start_date else "", self.app_config.general.ui_date_config)
                date_widget.dateChanged.connect(lambda date, w=date_widget: self._update_curtain_date_constraints(widget=w))
                date_widget.dateChanged.connect(self._sync_data_if_not_initializing)
                self.curtains_table.setCellWidget(row_idx, start_date_col, date_widget)
        
        # Update End Date column (QDateEdit widget)
        if end_date_col is not None:
            date_widget = self.curtains_table.cellWidget(row_idx, end_date_col)
            if date_widget and isinstance(date_widget, QDateEdit):
                # Update existing QDateEdit widget
                if curtain.end_date:
                    try:
                        end_dt = datetime.strptime(curtain.end_date, "%Y-%m-%d")
                        end_qdate = QDate(end_dt.year, end_dt.month, end_dt.day)
                        date_widget.blockSignals(True)
                        date_widget.setDate(end_qdate)
                        date_widget.blockSignals(False)
                    except ValueError:
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
                date_widget.dateChanged.connect(lambda date, w=date_widget: self._update_curtain_date_constraints(widget=w))
                date_widget.dateChanged.connect(self._sync_data_if_not_initializing)
            else:
                # Create QDateEdit if it doesn't exist
                from ui.table_utils import create_date_widget
                date_widget = create_date_widget(curtain.end_date if curtain.end_date else "", self.app_config.general.ui_date_config)
                date_widget.dateChanged.connect(lambda date, w=date_widget: self._update_curtain_date_constraints(widget=w))
                date_widget.dateChanged.connect(self._sync_data_if_not_initializing)
                self.curtains_table.setCellWidget(row_idx, end_date_col, date_widget)
        
        # Update date constraints after setting both dates
        self._update_curtain_date_constraints(row_idx=row_idx)
        
        # Update Name column
        if name_col is not None:
            item = self.curtains_table.item(row_idx, name_col)
            if item:
                item.setText(curtain.name if curtain.name else "")
            else:
                item = QTableWidgetItem(curtain.name if curtain.name else "")
                self.curtains_table.setItem(row_idx, name_col, item)
    
    def _update_curtain_date_constraints(self, widget=None, row_idx=None):
        """Update date constraints for a curtain row to prevent invalid date ranges.
        
        For curtains: finish must come after start (like timeframe fields).
        
        Args:
            widget: QDateEdit widget that triggered the update (optional)
            row_idx: Row index (optional, will be found from widget if not provided)
        """
        start_date_col = self._get_column_index("Start Date")
        end_date_col = self._get_column_index("End Date")
        
        if start_date_col is None or end_date_col is None:
            return
        
        # Find row index if not provided
        if row_idx is None and widget is not None:
            # Search for the widget in the table to find its row
            for r in range(self.curtains_table.rowCount()):
                if (self.curtains_table.cellWidget(r, start_date_col) == widget or
                    self.curtains_table.cellWidget(r, end_date_col) == widget):
                    row_idx = r
                    break
            if row_idx is None:
                return
        
        if row_idx is None:
            return
        
        start_widget = self.curtains_table.cellWidget(row_idx, start_date_col)
        end_widget = self.curtains_table.cellWidget(row_idx, end_date_col)
        
        if not isinstance(start_widget, QDateEdit) or not isinstance(end_widget, QDateEdit):
            return
        
        start_qdate = start_widget.date()
        end_qdate = end_widget.date()
        
        # Block signals to prevent recursive updates
        end_widget.blockSignals(True)
        start_widget.blockSignals(True)
        
        # For curtains: finish must come after start (like timeframe fields)
        # Set constraints FIRST
        min_end_date = start_qdate.addDays(1)
        end_widget.setMinimumDate(min_end_date)
        max_start_date = end_qdate.addDays(-1)
        start_widget.setMaximumDate(max_start_date)
        
        # THEN validate and correct if dates are invalid (handles manual typing that bypasses constraints)
        if end_qdate <= start_qdate:
            end_widget.setDate(min_end_date)
            end_qdate = min_end_date  # Update for constraint recalculation
        
        # Recalculate constraints with corrected dates
        min_end_date = start_qdate.addDays(1)
        end_widget.setMinimumDate(min_end_date)
        max_start_date = end_qdate.addDays(-1)
        start_widget.setMaximumDate(max_start_date)
        
        start_widget.blockSignals(False)
        end_widget.blockSignals(False)

    def _curtain_from_table_row(self, row_idx: int) -> Optional[Curtain]:
        """Extract a Curtain object from a table row."""
        try:
            id_col = self._get_column_index("ID")
            start_date_col = self._get_column_index("Start Date")
            end_date_col = self._get_column_index("End Date")
            name_col = self._get_column_index("Name")
            
            if id_col is None or start_date_col is None or end_date_col is None:
                return None
            
            # Extract ID
            id_item = self.curtains_table.item(row_idx, id_col)
            if not id_item:
                return None
            curtain_id = safe_int(id_item.text())
            if curtain_id <= 0:
                return None
            
            # Extract Start Date from QDateEdit widget or fallback to text item (key-based)
            from ui.table_utils import extract_date_from_cell
            start_date_internal = extract_date_from_cell(self.curtains_table, row_idx, start_date_col, self.app_config.general.ui_date_config)
            if not start_date_internal:
                return None
            
            # Extract End Date from QDateEdit widget or fallback to text item (key-based)
            end_date_internal = extract_date_from_cell(self.curtains_table, row_idx, end_date_col, self.app_config.general.ui_date_config)
            if not end_date_internal:
                return None
            
            # Get Color from detail form if this row is selected, otherwise from existing curtain
            color = "red"
            if row_idx == self._selected_row and hasattr(self, 'detail_color') and self.detail_color:
                color = self.detail_color.currentText()
            else:
                existing_curtain = next((c for c in self.project_data.curtains if c.curtain_id == curtain_id), None)
                if existing_curtain and existing_curtain.color:
                    color = existing_curtain.color
            
            # Extract Name
            name = ""
            if name_col is not None:
                name_item = self.curtains_table.item(row_idx, name_col)
                if name_item:
                    name = name_item.text().strip()
            
            return Curtain(
                curtain_id=curtain_id,
                start_date=start_date_internal,
                end_date=end_date_internal,
                color=color,
                name=name
            )
        except (ValueError, AttributeError, Exception) as e:
            logging.error(f"Error extracting curtain from table row {row_idx}: {e}")
            return None

    def _sync_data_impl(self):
        """Extract data from table and update project_data using Curtain objects directly."""
        if self._initializing:
            return
        
        try:
            # Extract Curtain objects from table rows
            curtains = []
            for row_idx in range(self.curtains_table.rowCount()):
                try:
                    curtain = self._curtain_from_table_row(row_idx)
                    if curtain:
                        curtains.append(curtain)
                except Exception as e:
                    # Log error for this specific row but continue processing other rows
                    logging.error(f"Error extracting curtain from row {row_idx}: {e}")
                    continue
            
            # Update project data with Curtain objects directly
            self.project_data.curtains = curtains
            
            # Update detail form if a row is selected
            if self._selected_row is not None and self._selected_row < len(curtains):
                self._populate_detail_form(self._selected_row)
        except Exception as e:
            # Catch any unexpected exceptions during sync
            logging.error(f"Error in _sync_data_impl: {e}", exc_info=True)
            raise  # Re-raise so BaseTab can show error message
    
    def _refresh_date_widgets(self):
        """Refresh all date widgets with current date format from config."""
        start_date_col = self._get_column_index("Start Date")
        end_date_col = self._get_column_index("End Date")
        
        for row in range(self.curtains_table.rowCount()):
            # Refresh Start Date widget
            if start_date_col is not None:
                widget = self.curtains_table.cellWidget(row, start_date_col)
                if widget and isinstance(widget, QDateEdit):
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
                    new_widget.dateChanged.connect(lambda date, w=new_widget: self._update_curtain_date_constraints(widget=w))
                    new_widget.dateChanged.connect(self._sync_data_if_not_initializing)
                    
                    # Replace widget
                    self.curtains_table.setCellWidget(row, start_date_col, new_widget)
            
            # Refresh End Date widget
            if end_date_col is not None:
                widget = self.curtains_table.cellWidget(row, end_date_col)
                if widget and isinstance(widget, QDateEdit):
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
                    new_widget.dateChanged.connect(lambda date, w=new_widget: self._update_curtain_date_constraints(widget=w))
                    new_widget.dateChanged.connect(self._sync_data_if_not_initializing)
                    
                    # Replace widget
                    self.curtains_table.setCellWidget(row, end_date_col, new_widget)

