from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                           QHBoxLayout, QHeaderView, QTableWidgetItem, 
                           QMessageBox, QGroupBox, QSizePolicy, QLabel, QGridLayout, QPlainTextEdit, QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from typing import List, Dict, Any, Optional
import logging
from ui.table_utils import NumericTableWidgetItem, add_row, remove_row, CheckBoxWidget
from .base_tab import BaseTab
from models.text_box import TextBox
from utils.conversion import safe_int

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TextBoxesTab(BaseTab):
    data_updated = pyqtSignal(dict)
    

    def __init__(self, project_data, app_config):
        self.table_config = app_config.get_table_config("text_boxes")
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
        
        add_btn = QPushButton("Add Text Box")
        add_btn.setToolTip("Add a new text box")
        add_btn.setMinimumWidth(120)
        add_btn.clicked.connect(lambda: add_row(self.text_boxes_table, "text_boxes", self.app_config.tables, self, "ID"))
        
        remove_btn = QPushButton("Remove Text Box")
        remove_btn.setToolTip("Remove selected text box(es)")
        remove_btn.setMinimumWidth(120)
        remove_btn.clicked.connect(lambda: remove_row(self.text_boxes_table, "text_boxes", 
                                                    self.app_config.tables, self))
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addStretch()  # Push buttons to the left
        
        # Create group box for table
        table_group = QGroupBox("Text Boxes")
        table_group_layout = QVBoxLayout()
        table_group_layout.setSpacing(5)
        table_group_layout.setContentsMargins(5, 10, 5, 5)
        
        # Create table with all columns: Select, ID, X, Y, Width, Height
        headers = [col.name for col in self.table_config.columns]
        self.text_boxes_table = QTableWidget(0, len(headers))
        self.text_boxes_table.setHorizontalHeaderLabels(headers)
        
        # Table styling
        self.text_boxes_table.setAlternatingRowColors(False)
        self.text_boxes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.text_boxes_table.setSelectionMode(QTableWidget.SingleSelection)
        self.text_boxes_table.setShowGrid(True)
        self.text_boxes_table.verticalHeader().setVisible(False)
        
        # Add bottom border to header row and gridline styling
        self.text_boxes_table.setStyleSheet(self.app_config.general.table_stylesheet)
        
        # Column sizing
        header = self.text_boxes_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Select
        self.text_boxes_table.setColumnWidth(0, 50)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # X
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Y
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Width
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Height
        # Text Align and Vertical Align columns use ResizeToContents (handled by table_utils)
        # Text Preview column (last column) uses Stretch to take remaining width
        text_preview_col = self._get_column_index("Text Preview")
        if text_preview_col is not None:
            header.setSectionResizeMode(text_preview_col, QHeaderView.Stretch)  # Text Preview
        
        # Enable horizontal scroll bar
        self.text_boxes_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.text_boxes_table.setSortingEnabled(True)
        
        # Set table size policy
        self.text_boxes_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        table_group_layout.addLayout(toolbar)
        table_group_layout.addWidget(self.text_boxes_table)
        table_group.setLayout(table_group_layout)
        
        # Add table group with stretch factor so it expands to fill available space
        layout.addWidget(table_group, 1)
        
        # Create detail form group box
        detail_group = self._create_detail_form()
        layout.addWidget(detail_group)
        
        self.setLayout(layout)

    def _create_detail_form(self) -> QGroupBox:
        """Create the detail form for editing text box content."""
        self.detail_group = QGroupBox("Text Box Content")  # Store reference for title updates
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Text (large text area) - read-only by default, spans full width
        self.detail_text = QPlainTextEdit()
        self.detail_text.setToolTip("Text content for the text box (supports text wrapping)")
        self.detail_text.setMinimumHeight(100)
        self.detail_text.setReadOnly(True)  # Start as read-only
        
        # Edit and Save buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        self.edit_button = QPushButton("Edit")
        self.edit_button.setToolTip("Enable editing of text content")
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.edit_button.setEnabled(False)  # Disabled until a text box is selected
        
        self.save_button = QPushButton("Save")
        self.save_button.setToolTip("Save text content changes")
        self.save_button.clicked.connect(self._on_save_clicked)
        self.save_button.setEnabled(False)  # Disabled until Edit is clicked
        
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        
        # Store list of detail form widgets for easy enable/disable
        # Note: detail_text uses setReadOnly() separately, so we only include the Edit button here
        self._detail_form_widgets = [self.edit_button]
        
        layout.addWidget(self.detail_text, 0, 0)  # Text area spans full width
        layout.addLayout(button_layout, 1, 0)  # Buttons below text area
        layout.setColumnStretch(0, 1)  # Make column 0 stretch
        layout.setRowStretch(0, 1)  # Allow text area to expand vertically
        
        self.detail_group.setLayout(layout)
        return self.detail_group

    def _on_table_selection_changed(self):
        """Handle table selection changes - populate detail form."""
        selected_rows = self.text_boxes_table.selectionModel().selectedRows()
        if not selected_rows:
            self._selected_row = None
            self._clear_detail_form()
            return
        
        row = selected_rows[0].row()
        self._selected_row = row
        self._populate_detail_form(row)

    def _populate_detail_form(self, row: int):
        """Populate detail form with data from selected text box."""
        self._updating_form = True
        
        try:
            # Block signals to prevent recursive updates
            self.detail_text.blockSignals(True)
            
            # Get TextBox object directly from project_data
            if row < len(self.project_data.text_boxes):
                textbox = self.project_data.text_boxes[row]
                self.detail_text.setPlainText(textbox.text if textbox.text else "")
                # Update group box title to show which text box is selected
                self.detail_group.setTitle(f"Text Box {textbox.textbox_id}")
                # Enable Edit button only when a valid text box exists
                self._set_detail_form_enabled(self._detail_form_widgets, True)
            else:
                # Use defaults if textbox doesn't exist
                self.detail_text.setPlainText("")
                self.detail_group.setTitle("Text Box Content")
                # Disable Edit button when no valid text box exists
                self._set_detail_form_enabled(self._detail_form_widgets, False)
            
            # Reset to read-only mode and button states
            self.detail_text.setReadOnly(True)
            self.save_button.setEnabled(False)
        finally:
            self.detail_text.blockSignals(False)
            self._updating_form = False

    def _clear_detail_form(self):
        """Clear the detail form when no text box is selected."""
        self._updating_form = True
        try:
            # Block signals to prevent recursive updates
            self.detail_text.blockSignals(True)
            self.detail_text.setPlainText("")
            self.detail_text.setReadOnly(True)
            self.detail_group.setTitle("Text Box Content")  # Reset title when no selection
            # Disable detail form widgets when no text box is selected
            self._set_detail_form_enabled(self._detail_form_widgets, False)
            self.save_button.setEnabled(False)
        finally:
            self.detail_text.blockSignals(False)
            self._updating_form = False

    def _on_edit_clicked(self):
        """Enable editing of text content."""
        # Safety check: only allow editing if a valid text box is selected
        if self._selected_row is None or self._selected_row >= len(self.project_data.text_boxes):
            return
        
        self.detail_text.setReadOnly(False)
        self.edit_button.setEnabled(False)
        self.save_button.setEnabled(True)
        self.detail_text.setFocus()  # Give focus to text editor
    
    def _on_save_clicked(self):
        """Save text content and disable editing."""
        # Sync the data
        self._sync_data_if_not_initializing()
        
        # Update Text Preview column in table after saving text
        if self._selected_row is not None and self._selected_row < len(self.project_data.text_boxes):
            textbox = self.project_data.text_boxes[self._selected_row]
            self._update_table_row_from_textbox(self._selected_row, textbox)
        
        # Return to read-only mode
        self.detail_text.setReadOnly(True)
        self.edit_button.setEnabled(True)
        self.save_button.setEnabled(False)

    def _connect_signals(self):
        self.text_boxes_table.itemChanged.connect(self._on_item_changed)
        self.text_boxes_table.selectionModel().selectionChanged.connect(self._on_table_selection_changed)
    
    def _get_column_index(self, column_name: str) -> Optional[int]:
        """Get the column index for a given column name."""
        for idx, col_config in enumerate(self.table_config.columns):
            if col_config.name == column_name:
                return idx
        return None
    
    def _truncate_text(self, text: str, max_length: int = 80) -> str:
        """Truncate text to max_length and add ellipsis if needed."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
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
            self.text_boxes_table.itemChanged.disconnect(self._on_item_changed)
            was_connected = True
        except:
            pass  # Signal might not be connected
        
        try:
            # Get column name (key) from item
            col_name = self._get_column_name_from_item(item)
            if col_name is None:
                return
            
            # Don't trigger sync for read-only columns (ID, Text Preview)
            if col_name in ["ID", "Text Preview"]:
                return
            
            # Update UserRole for numeric columns (X, Y, Width, Height)
            if col_name in ["X", "Y", "Width", "Height"]:
                try:
                    val_str = item.text().strip()
                    if val_str:
                        try:
                            val_int = int(val_str)
                            item.setData(Qt.UserRole, val_int)
                        except ValueError:
                            # Invalid numeric format - set UserRole to None
                            item.setData(Qt.UserRole, None)
                    else:
                        item.setData(Qt.UserRole, None)
                except Exception as e:
                    # Catch any unexpected exceptions during numeric processing
                    logging.error(f"Error processing numeric value in _on_item_changed: {e}")
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
                    self.text_boxes_table.itemChanged.connect(self._on_item_changed)
                except:
                    pass

    def _load_initial_data_impl(self):
        """Load initial data into the table using TextBox objects directly."""
        text_boxes = self.project_data.text_boxes
        row_count = len(text_boxes)
        self.text_boxes_table.setRowCount(row_count)
        self._initializing = True

        for row_idx in range(row_count):
            # Add checkbox first (Select column)
            checkbox_widget = CheckBoxWidget()
            self.text_boxes_table.setCellWidget(row_idx, 0, checkbox_widget)

            # Use helper method to populate row from TextBox object
            textbox = text_boxes[row_idx]
            self._update_table_row_from_textbox(row_idx, textbox)
        
        # Sort by ID by default
        id_col = self._get_column_index("ID")
        if id_col is not None:
            self.text_boxes_table.sortItems(id_col, Qt.AscendingOrder)
        
        self._initializing = False
        
        # Clear detail form if table is empty
        if row_count == 0:
            self._clear_detail_form()

    def _update_table_row_from_textbox(self, row_idx: int, textbox: TextBox) -> None:
        """Populate a table row from a TextBox object."""
        # Get column indices
        id_col = self._get_column_index("ID")
        x_col = self._get_column_index("X")
        y_col = self._get_column_index("Y")
        width_col = self._get_column_index("Width")
        height_col = self._get_column_index("Height")
        
        # Update ID column
        if id_col is not None:
            item = self.text_boxes_table.item(row_idx, id_col)
            if item:
                item.setText(str(textbox.textbox_id))
                item.setData(Qt.UserRole, textbox.textbox_id)
            else:
                item = NumericTableWidgetItem(str(textbox.textbox_id))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                item.setData(Qt.UserRole, textbox.textbox_id)
                self.text_boxes_table.setItem(row_idx, id_col, item)
        
        # Update X column
        if x_col is not None:
            item = self.text_boxes_table.item(row_idx, x_col)
            if item:
                item.setText(str(textbox.x))
                item.setData(Qt.UserRole, textbox.x)
            else:
                item = NumericTableWidgetItem(str(textbox.x))
                item.setData(Qt.UserRole, textbox.x)
                self.text_boxes_table.setItem(row_idx, x_col, item)
        
        # Update Y column
        if y_col is not None:
            item = self.text_boxes_table.item(row_idx, y_col)
            if item:
                item.setText(str(textbox.y))
                item.setData(Qt.UserRole, textbox.y)
            else:
                item = NumericTableWidgetItem(str(textbox.y))
                item.setData(Qt.UserRole, textbox.y)
                self.text_boxes_table.setItem(row_idx, y_col, item)
        
        # Update Width column
        if width_col is not None:
            item = self.text_boxes_table.item(row_idx, width_col)
            if item:
                item.setText(str(textbox.width))
                item.setData(Qt.UserRole, textbox.width)
            else:
                item = NumericTableWidgetItem(str(textbox.width))
                item.setData(Qt.UserRole, textbox.width)
                self.text_boxes_table.setItem(row_idx, width_col, item)
        
        # Update Height column
        if height_col is not None:
            item = self.text_boxes_table.item(row_idx, height_col)
            if item:
                item.setText(str(textbox.height))
                item.setData(Qt.UserRole, textbox.height)
            else:
                item = NumericTableWidgetItem(str(textbox.height))
                item.setData(Qt.UserRole, textbox.height)
                self.text_boxes_table.setItem(row_idx, height_col, item)
        
        # Update Text Align column (combo box)
        text_align_col = self._get_column_index("Text Align")
        if text_align_col is not None:
            combo = self.text_boxes_table.cellWidget(row_idx, text_align_col)
            if combo and isinstance(combo, QComboBox):
                # Find the index of the current value
                index = combo.findText(textbox.text_align)
                if index >= 0:
                    combo.setCurrentIndex(index)
            elif not combo:
                # Create combo box if it doesn't exist (shouldn't happen if table_utils is used)
                combo = QComboBox()
                combo.addItems(["Left", "Center", "Right"])
                combo.setCurrentText(textbox.text_align)
                combo.currentTextChanged.connect(self._sync_data_if_not_initializing)
                self.text_boxes_table.setCellWidget(row_idx, text_align_col, combo)
        
        # Update Vertical Align column (combo box)
        vertical_align_col = self._get_column_index("Vertical Align")
        if vertical_align_col is not None:
            combo = self.text_boxes_table.cellWidget(row_idx, vertical_align_col)
            if combo and isinstance(combo, QComboBox):
                # Find the index of the current value
                index = combo.findText(textbox.vertical_align)
                if index >= 0:
                    combo.setCurrentIndex(index)
            elif not combo:
                # Create combo box if it doesn't exist (shouldn't happen if table_utils is used)
                combo = QComboBox()
                combo.addItems(["Top", "Middle", "Bottom"])
                combo.setCurrentText(textbox.vertical_align)
                combo.currentTextChanged.connect(self._sync_data_if_not_initializing)
                self.text_boxes_table.setCellWidget(row_idx, vertical_align_col, combo)
        
        # Update Text Preview column (read-only, truncated text)
        text_preview_col = self._get_column_index("Text Preview")
        if text_preview_col is not None:
            full_text = textbox.text if textbox.text else ""
            display_text = self._truncate_text(full_text)
            item = self.text_boxes_table.item(row_idx, text_preview_col)
            if item:
                item.setText(display_text)
                item.setToolTip(full_text)  # Show full text in tooltip
            else:
                item = QTableWidgetItem(display_text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Read-only
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                item.setToolTip(full_text)  # Show full text in tooltip
                self.text_boxes_table.setItem(row_idx, text_preview_col, item)

    def _textbox_from_table_row(self, row_idx: int) -> Optional[TextBox]:
        """Extract a TextBox object from a table row."""
        try:
            id_col = self._get_column_index("ID")
            x_col = self._get_column_index("X")
            y_col = self._get_column_index("Y")
            width_col = self._get_column_index("Width")
            height_col = self._get_column_index("Height")
            
            text_align_col = self._get_column_index("Text Align")
            vertical_align_col = self._get_column_index("Vertical Align")
            
            if id_col is None or x_col is None or y_col is None or width_col is None or height_col is None:
                return None
            
            # Extract ID
            id_item = self.text_boxes_table.item(row_idx, id_col)
            if not id_item:
                return None
            textbox_id = safe_int(id_item.text())
            if textbox_id <= 0:
                return None
            
            # Extract X
            x_item = self.text_boxes_table.item(row_idx, x_col)
            if not x_item or not x_item.text().strip():
                return None
            x = safe_int(x_item.text())
            if x is None or x < 0:
                return None
            
            # Extract Y
            y_item = self.text_boxes_table.item(row_idx, y_col)
            if not y_item or not y_item.text().strip():
                return None
            y = safe_int(y_item.text())
            if y is None or y < 0:
                return None
            
            # Extract Width
            width_item = self.text_boxes_table.item(row_idx, width_col)
            if not width_item or not width_item.text().strip():
                return None
            width = safe_int(width_item.text())
            if width is None or width <= 0:
                return None
            
            # Extract Height
            height_item = self.text_boxes_table.item(row_idx, height_col)
            if not height_item or not height_item.text().strip():
                return None
            height = safe_int(height_item.text())
            if height is None or height <= 0:
                return None
            
            # Get Text from detail form if this row is selected, otherwise from existing textbox
            text = ""
            if row_idx == self._selected_row and hasattr(self, 'detail_text') and self.detail_text:
                text = self.detail_text.toPlainText()
            else:
                existing_textbox = next((tb for tb in self.project_data.text_boxes if tb.textbox_id == textbox_id), None)
                if existing_textbox and existing_textbox.text:
                    text = existing_textbox.text
            
            # Extract Text Align
            text_align = "Center"  # Default
            if text_align_col is not None:
                combo = self.text_boxes_table.cellWidget(row_idx, text_align_col)
                if combo and isinstance(combo, QComboBox):
                    text_align = combo.currentText()
                else:
                    # Fallback to existing value if combo doesn't exist
                    existing_textbox = next((tb for tb in self.project_data.text_boxes if tb.textbox_id == textbox_id), None)
                    if existing_textbox:
                        text_align = existing_textbox.text_align
            
            # Extract Vertical Align
            vertical_align = "Middle"  # Default
            if vertical_align_col is not None:
                combo = self.text_boxes_table.cellWidget(row_idx, vertical_align_col)
                if combo and isinstance(combo, QComboBox):
                    vertical_align = combo.currentText()
                else:
                    # Fallback to existing value if combo doesn't exist
                    existing_textbox = next((tb for tb in self.project_data.text_boxes if tb.textbox_id == textbox_id), None)
                    if existing_textbox:
                        vertical_align = existing_textbox.vertical_align
            
            return TextBox(
                textbox_id=textbox_id,
                x=x,
                y=y,
                width=width,
                height=height,
                text=text,
                text_align=text_align,
                vertical_align=vertical_align
            )
        except (ValueError, AttributeError, Exception) as e:
            logging.error(f"Error extracting textbox from table row {row_idx}: {e}")
            return None

    def _sync_data_impl(self):
        """Extract data from table and update project_data using TextBox objects directly."""
        if self._initializing:
            return
        
        try:
            # Extract TextBox objects from table rows
            text_boxes = []
            for row_idx in range(self.text_boxes_table.rowCount()):
                try:
                    textbox = self._textbox_from_table_row(row_idx)
                    if textbox:
                        text_boxes.append(textbox)
                except Exception as e:
                    # Log error for this specific row but continue processing other rows
                    logging.error(f"Error extracting textbox from row {row_idx}: {e}")
                    continue
            
            # Update project data with TextBox objects directly
            self.project_data.text_boxes = text_boxes
            
            # Only update detail form if change came from table (not from detail form itself)
            # We can detect this by checking if _updating_form is False (meaning user edited table, not form)
            if self._selected_row is not None and self._selected_row < len(text_boxes) and not self._updating_form:
                self._populate_detail_form(self._selected_row)
        except Exception as e:
            # Catch any unexpected exceptions during sync
            logging.error(f"Error in _sync_data_impl: {e}", exc_info=True)
            raise  # Re-raise so BaseTab can show error message

