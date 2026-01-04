from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                           QHBoxLayout, QHeaderView, QTableWidgetItem, 
                           QMessageBox, QGroupBox, QSizePolicy, QComboBox, QLabel, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from ui.table_utils import NumericTableWidgetItem, add_row, remove_row, CheckBoxWidget, DateTableWidgetItem
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
        add_btn.clicked.connect(lambda: add_row(self.curtains_table, "curtains", self.app_config.tables, self, "ID"))
        
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
        self.curtains_table.setSelectionMode(QTableWidget.SingleSelection)
        self.curtains_table.setShowGrid(True)
        self.curtains_table.verticalHeader().setVisible(False)
        
        # Add bottom border to header row
        self.curtains_table.setStyleSheet(self.app_config.general.table_header_stylesheet)
        
        # Column sizing
        header = self.curtains_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Select
        self.curtains_table.setColumnWidth(0, 50)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Start Date
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # End Date
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Name
        
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
        
        row = selected_rows[0].row()
        self._selected_row = row
        self._populate_detail_form(row)

    def _populate_detail_form(self, row: int):
        """Populate detail form with data from selected curtain."""
        self._updating_form = True
        
        try:
            # Get Curtain object directly from project_data
            if row < len(self.project_data.curtains):
                curtain = self.project_data.curtains[row]
                self.detail_color.setCurrentText(curtain.color if curtain.color else "red")
            else:
                # Use defaults if curtain doesn't exist
                self.detail_color.setCurrentText("red")
        finally:
            self._updating_form = False

    def _clear_detail_form(self):
        """Clear the detail form when no curtain is selected."""
        self._updating_form = True
        try:
            self.detail_color.setCurrentText("red")
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
            self.curtains_table.itemChanged.disconnect(self._on_item_changed)
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
            
            # Update UserRole for date columns - use normalize_display_date for flexible formats
            if col_name in ["Start Date", "End Date"]:
                try:
                    val_str = item.text().strip()
                    if val_str:
                        try:
                            # Use normalize_display_date to handle flexible formats
                            normalized = normalize_display_date(val_str)
                            date_obj = datetime.strptime(normalized, "%d/%m/%Y")
                            item.setData(Qt.UserRole, date_obj)
                        except ValueError:
                            # Invalid date format - set UserRole to None
                            item.setData(Qt.UserRole, None)
                    else:
                        item.setData(Qt.UserRole, None)
                except Exception as e:
                    # Catch any unexpected exceptions during date processing
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
            # Add checkbox first (Select column)
            checkbox_widget = CheckBoxWidget()
            self.curtains_table.setCellWidget(row_idx, 0, checkbox_widget)

            # Use helper method to populate row from Curtain object
            curtain = curtains[row_idx]
            self._update_table_row_from_curtain(row_idx, curtain)
        
        # Sort by ID by default
        id_col = self._get_column_index("ID")
        if id_col is not None:
            self.curtains_table.sortItems(id_col, Qt.AscendingOrder)
        
        self._initializing = False

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
        
        # Update Start Date column
        if start_date_col is not None:
            start_date_display = internal_to_display_date(curtain.start_date) if curtain.start_date else ""
            item = self.curtains_table.item(row_idx, start_date_col)
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
                self.curtains_table.setItem(row_idx, start_date_col, item)
        
        # Update End Date column
        if end_date_col is not None:
            end_date_display = internal_to_display_date(curtain.end_date) if curtain.end_date else ""
            item = self.curtains_table.item(row_idx, end_date_col)
            if item:
                item.setText(end_date_display)
                try:
                    if end_date_display and end_date_display.strip():
                        date_obj = datetime.strptime(end_date_display, "%d/%m/%Y")
                        item.setData(Qt.UserRole, date_obj)
                    else:
                        item.setData(Qt.UserRole, None)
                except (ValueError, AttributeError):
                    item.setData(Qt.UserRole, None)
            else:
                item = DateTableWidgetItem(end_date_display)
                try:
                    if end_date_display and end_date_display.strip():
                        date_obj = datetime.strptime(end_date_display, "%d/%m/%Y")
                        item.setData(Qt.UserRole, date_obj)
                    else:
                        item.setData(Qt.UserRole, None)
                except (ValueError, AttributeError):
                    item.setData(Qt.UserRole, None)
                self.curtains_table.setItem(row_idx, end_date_col, item)
        
        # Update Name column
        if name_col is not None:
            item = self.curtains_table.item(row_idx, name_col)
            if item:
                item.setText(curtain.name if curtain.name else "")
            else:
                item = QTableWidgetItem(curtain.name if curtain.name else "")
                self.curtains_table.setItem(row_idx, name_col, item)

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
            
            # Extract Start Date (convert from display format to internal format)
            start_date_item = self.curtains_table.item(row_idx, start_date_col)
            if not start_date_item or not start_date_item.text().strip():
                return None
            try:
                start_date_internal = display_to_internal_date(start_date_item.text())
            except ValueError:
                # Invalid date format - return None to skip this row
                return None
            
            # Extract End Date (convert from display format to internal format)
            end_date_item = self.curtains_table.item(row_idx, end_date_col)
            if not end_date_item or not end_date_item.text().strip():
                return None
            try:
                end_date_internal = display_to_internal_date(end_date_item.text())
            except ValueError:
                # Invalid date format - return None to skip this row
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

