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
from models.pipe import Pipe
from utils.conversion import safe_int, display_to_internal_date, internal_to_display_date, normalize_display_date

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PipesTab(BaseTab):
    data_updated = pyqtSignal(dict)
    

    def __init__(self, project_data, app_config):
        self.table_config = app_config.get_table_config("pipes")
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
        
        add_btn = QPushButton("Add Pipe")
        add_btn.setToolTip("Add a new pipe")
        add_btn.setMinimumWidth(120)
        add_btn.clicked.connect(lambda: add_row(self.pipes_table, "pipes", self.app_config.tables, self, "ID"))
        
        remove_btn = QPushButton("Remove Pipe")
        remove_btn.setToolTip("Remove selected pipe(s)")
        remove_btn.setMinimumWidth(120)
        remove_btn.clicked.connect(lambda: remove_row(self.pipes_table, "pipes", 
                                                    self.app_config.tables, self))
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addStretch()  # Push buttons to the left
        
        # Create group box for table
        table_group = QGroupBox("Pipes")
        table_group_layout = QVBoxLayout()
        table_group_layout.setSpacing(5)
        table_group_layout.setContentsMargins(5, 10, 5, 5)
        
        # Create table with all columns: Select, ID, Date, Color, Name
        headers = [col.name for col in self.table_config.columns]
        self.pipes_table = QTableWidget(0, len(headers))
        self.pipes_table.setHorizontalHeaderLabels(headers)
        
        # Table styling
        self.pipes_table.setAlternatingRowColors(False)
        self.pipes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.pipes_table.setSelectionMode(QTableWidget.SingleSelection)
        self.pipes_table.setShowGrid(True)
        self.pipes_table.verticalHeader().setVisible(False)
        
        # Add bottom border to header row and gridline styling
        self.pipes_table.setStyleSheet(self.app_config.general.table_stylesheet)
        
        # Column sizing
        header = self.pipes_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Select
        self.pipes_table.setColumnWidth(0, 50)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Date
        self.pipes_table.setColumnWidth(2, 110)  # Fixed width for date (dd/mm/yyyy format)
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Name
        
        # Enable horizontal scroll bar
        self.pipes_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.pipes_table.setSortingEnabled(True)
        
        # Set table size policy
        self.pipes_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        table_group_layout.addLayout(toolbar)
        table_group_layout.addWidget(self.pipes_table)
        table_group.setLayout(table_group_layout)
        
        # Add table group with stretch factor so it expands to fill available space
        layout.addWidget(table_group, 1)
        
        # Create detail form group box
        detail_group = self._create_detail_form()
        layout.addWidget(detail_group)
        
        self.setLayout(layout)

    def _create_detail_form(self) -> QGroupBox:
        """Create the detail form for editing pipe color."""
        group = QGroupBox("Pipe Formatting")
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
        self.detail_color.setToolTip("Color of the pipe line")
        self.detail_color.currentTextChanged.connect(self._on_detail_form_changed)
        # Disable by default - will be enabled when a pipe is selected
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
        selected_rows = self.pipes_table.selectionModel().selectedRows()
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
        """Populate detail form with data from selected pipe."""
        self._updating_form = True
        
        try:
            # Get Pipe object directly from project_data
            if row < len(self.project_data.pipes):
                pipe = self.project_data.pipes[row]
                self.detail_color.setCurrentText(pipe.color if pipe.color else "red")
                # Enable detail form widgets when a valid pipe is selected
                self._set_detail_form_enabled(self._detail_form_widgets, True)
            else:
                # Use defaults if pipe doesn't exist
                self.detail_color.setCurrentText("red")
                self._set_detail_form_enabled(self._detail_form_widgets, False)
        finally:
            self._updating_form = False

    def _clear_detail_form(self):
        """Clear the detail form when no pipe is selected."""
        self._updating_form = True
        try:
            self.detail_color.setCurrentText("red")
            # Disable detail form widgets when no pipe is selected
            self._set_detail_form_enabled(self._detail_form_widgets, False)
        finally:
            self._updating_form = False

    def _on_detail_form_changed(self):
        """Handle changes in detail form - update selected pipe."""
        if self._updating_form or self._selected_row is None:
            return
        
        # Trigger sync to update the data
        self._sync_data_if_not_initializing()

    def _connect_signals(self):
        self.pipes_table.itemChanged.connect(self._on_item_changed)
        self.pipes_table.selectionModel().selectionChanged.connect(self._on_table_selection_changed)
    
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
        """Handle item changes - update UserRole for numeric and date columns."""
        if item is None:
            return
        
        # CRITICAL: Disconnect signal BEFORE modifying item to prevent infinite loop
        was_connected = False
        try:
            self.pipes_table.itemChanged.disconnect(self._on_item_changed)
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
            
            # Skip date column - QDateEdit widget handles its own changes via dateChanged signal
            if col_name == "Date":
                # Check if this is actually a QDateEdit widget (shouldn't trigger itemChanged)
                date_widget = self.pipes_table.cellWidget(row, col_idx)
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
                    self.pipes_table.itemChanged.connect(self._on_item_changed)
                except:
                    pass

    def _load_initial_data_impl(self):
        """Load initial data into the table using Pipe objects directly."""
        pipes = self.project_data.pipes
        row_count = len(pipes)
        self.pipes_table.setRowCount(row_count)
        self._initializing = True

        for row_idx in range(row_count):

            # Use helper method to populate row from Pipe object
            pipe = pipes[row_idx]
            self._update_table_row_from_pipe(row_idx, pipe)
        
        # Sort by ID by default
        id_col = self._get_column_index("ID")
        if id_col is not None:
            self.pipes_table.sortItems(id_col, Qt.AscendingOrder)
        
        self._initializing = False
        
        # Disable detail form if no pipes exist or no selection
        if row_count == 0 or self._selected_row is None:
            self._clear_detail_form()

    def _update_table_row_from_pipe(self, row_idx: int, pipe: Pipe) -> None:
        """Populate a table row from a Pipe object."""
        headers = [col.name for col in self.table_config.columns]
        
        # Get column indices
        id_col = self._get_column_index("ID")
        date_col = self._get_column_index("Date")
        name_col = self._get_column_index("Name")
        
        # Update ID column
        if id_col is not None:
            item = self.pipes_table.item(row_idx, id_col)
            if item:
                item.setText(str(pipe.pipe_id))
                item.setData(Qt.UserRole, pipe.pipe_id)
            else:
                item = NumericTableWidgetItem(str(pipe.pipe_id))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                item.setData(Qt.UserRole, pipe.pipe_id)
                self.pipes_table.setItem(row_idx, id_col, item)
        
        # Update Date column (QDateEdit widget)
        if date_col is not None:
            date_widget = self.pipes_table.cellWidget(row_idx, date_col)
            if date_widget and isinstance(date_widget, QDateEdit):
                # Update existing QDateEdit widget
                if pipe.date:
                    try:
                        date_dt = datetime.strptime(pipe.date, "%Y-%m-%d")
                        date_qdate = QDate(date_dt.year, date_dt.month, date_dt.day)
                        date_widget.blockSignals(True)
                        date_widget.setDate(date_qdate)
                        date_widget.blockSignals(False)
                    except ValueError:
                        date_widget.blockSignals(True)
                        date_widget.setDate(QDate.currentDate())
                        date_widget.blockSignals(False)
                else:
                    date_widget.blockSignals(True)
                    date_widget.setDate(QDate.currentDate())
                    date_widget.blockSignals(False)
                # Reconnect signal (disconnect first to avoid duplicates)
                try:
                    date_widget.dateChanged.disconnect()
                except:
                    pass
                if hasattr(self, '_sync_data_if_not_initializing'):
                    date_widget.dateChanged.connect(self._sync_data_if_not_initializing)
            else:
                # Create QDateEdit if it doesn't exist
                date_widget = DateEditWidget()
                if pipe.date:
                    try:
                        date_dt = datetime.strptime(pipe.date, "%Y-%m-%d")
                        date_qdate = QDate(date_dt.year, date_dt.month, date_dt.day)
                        date_widget.setDate(date_qdate)
                    except ValueError:
                        date_widget.setDate(QDate.currentDate())
                else:
                    date_widget.setDate(QDate.currentDate())
                if hasattr(self, '_sync_data_if_not_initializing'):
                    date_widget.dateChanged.connect(self._sync_data_if_not_initializing)
                self.pipes_table.setCellWidget(row_idx, date_col, date_widget)
        
        # Update Name column
        if name_col is not None:
            item = self.pipes_table.item(row_idx, name_col)
            if item:
                item.setText(pipe.name if pipe.name else "")
            else:
                item = QTableWidgetItem(pipe.name if pipe.name else "")
                self.pipes_table.setItem(row_idx, name_col, item)

    def _pipe_from_table_row(self, row_idx: int) -> Optional[Pipe]:
        """Extract a Pipe object from a table row."""
        try:
            id_col = self._get_column_index("ID")
            date_col = self._get_column_index("Date")
            name_col = self._get_column_index("Name")
            
            if id_col is None or date_col is None:
                return None
            
            # Extract ID
            id_item = self.pipes_table.item(row_idx, id_col)
            if not id_item:
                return None
            pipe_id = safe_int(id_item.text())
            if pipe_id <= 0:
                return None
            
            # Extract Date from QDateEdit widget or fallback to text item
            date_widget = self.pipes_table.cellWidget(row_idx, date_col)
            if date_widget and isinstance(date_widget, QDateEdit):
                # Read from QDateEdit widget
                date_qdate = date_widget.date()
                date_internal = date_qdate.toString("yyyy-MM-dd")
            else:
                # Fallback to text-based item (for backward compatibility)
                date_item = self.pipes_table.item(row_idx, date_col)
                if not date_item or not date_item.text().strip():
                    return None
                try:
                    date_internal = display_to_internal_date(date_item.text())
                except ValueError:
                    # Invalid date format - return None to skip this row
                    return None
            
            # Get Color from detail form if this row is selected, otherwise from existing pipe
            color = "red"
            if row_idx == self._selected_row and hasattr(self, 'detail_color') and self.detail_color:
                color = self.detail_color.currentText()
            else:
                existing_pipe = next((p for p in self.project_data.pipes if p.pipe_id == pipe_id), None)
                if existing_pipe and existing_pipe.color:
                    color = existing_pipe.color
            
            # Extract Name
            name = ""
            if name_col is not None:
                name_item = self.pipes_table.item(row_idx, name_col)
                if name_item:
                    name = name_item.text().strip()
            
            return Pipe(
                pipe_id=pipe_id,
                date=date_internal,
                color=color,
                name=name
            )
        except (ValueError, AttributeError, Exception) as e:
            logging.error(f"Error extracting pipe from table row {row_idx}: {e}")
            return None

    def _sync_data_impl(self):
        """Extract data from table and update project_data using Pipe objects directly."""
        if self._initializing:
            return
        
        try:
            # Extract Pipe objects from table rows
            pipes = []
            for row_idx in range(self.pipes_table.rowCount()):
                try:
                    pipe = self._pipe_from_table_row(row_idx)
                    if pipe:
                        pipes.append(pipe)
                except Exception as e:
                    # Log error for this specific row but continue processing other rows
                    logging.error(f"Error extracting pipe from row {row_idx}: {e}")
                    continue
            
            # Update project data with Pipe objects directly
            self.project_data.pipes = pipes
            
            # Update detail form if a row is selected
            if self._selected_row is not None and self._selected_row < len(pipes):
                self._populate_detail_form(self._selected_row)
        except Exception as e:
            # Catch any unexpected exceptions during sync
            logging.error(f"Error in _sync_data_impl: {e}", exc_info=True)
            raise  # Re-raise so BaseTab can show error message

