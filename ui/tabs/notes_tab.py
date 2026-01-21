from PyQt5.QtWidgets import (QWidget, QTableWidget, QVBoxLayout, QPushButton, 
                           QHBoxLayout, QHeaderView, QTableWidgetItem, 
                           QMessageBox, QGroupBox, QSizePolicy, QLabel, QGridLayout, QPlainTextEdit, QComboBox, QSpinBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from typing import List, Dict, Any, Optional
import logging
from ui.table_utils import NumericTableWidgetItem, add_row, remove_row, CheckBoxWidget
from .base_tab import BaseTab
from models.note import Note
from utils.conversion import safe_int

# Logging is configured centrally in utils/logging_config.py

class NotesTab(BaseTab):
    data_updated = pyqtSignal(dict)
    

    def __init__(self, project_data, app_config):
        self.table_config = app_config.get_table_config("notes")
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
        
        add_btn = QPushButton("Add Note")
        add_btn.setToolTip("Add a new note")
        add_btn.setMinimumWidth(120)
        add_btn.clicked.connect(lambda: add_row(self.notes_table, "notes", self.app_config.tables, self, "ID"))
        
        remove_btn = QPushButton("Remove Note")
        remove_btn.setToolTip("Remove selected note(s)")
        remove_btn.setMinimumWidth(120)
        remove_btn.clicked.connect(lambda: remove_row(self.notes_table, "notes", 
                                                    self.app_config.tables, self))
        
        toolbar.addWidget(add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addStretch()  # Push buttons to the left
        
        # Create group box for table
        table_group = QGroupBox("Notes")
        table_group_layout = QVBoxLayout()
        table_group_layout.setSpacing(5)
        table_group_layout.setContentsMargins(5, 10, 5, 5)
        
        # Create table with all columns: Select, ID, X, Y, Width, Height
        headers = [col.name for col in self.table_config.columns]
        self.notes_table = QTableWidget(0, len(headers))
        self.notes_table.setHorizontalHeaderLabels(headers)
        
        # Table styling
        self.notes_table.setAlternatingRowColors(False)
        self.notes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.notes_table.setSelectionMode(QTableWidget.ExtendedSelection)  # Extended selection for bulk operations, detail form shows first selected
        self.notes_table.setShowGrid(True)
        self.notes_table.verticalHeader().setVisible(False)
        
        # Add bottom border to header row and gridline styling
        self.notes_table.setStyleSheet(self.app_config.general.table_stylesheet)
        
        # Column sizing
        header = self.notes_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Select
        self.notes_table.setColumnWidth(0, 50)
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
        self.notes_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.notes_table.setSortingEnabled(True)
        
        # Set table size policy
        self.notes_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        table_group_layout.addLayout(toolbar)
        table_group_layout.addWidget(self.notes_table)
        table_group.setLayout(table_group_layout)
        
        # Add table group with stretch factor so it expands to fill available space
        layout.addWidget(table_group, 1)
        
        # Create detail form group box
        detail_group = self._create_detail_form()
        layout.addWidget(detail_group)
        
        self.setLayout(layout)

    def _create_detail_form(self) -> QGroupBox:
        """Create the detail form for editing note content."""
        self.detail_group = QGroupBox("Note Content")  # Store reference for title updates
        layout = QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Text (large text area) - read-only by default, spans full width
        self.detail_text = QPlainTextEdit()
        self.detail_text.setToolTip("Text content for the note (supports text wrapping)")
        self.detail_text.setMinimumHeight(100)
        self.detail_text.setReadOnly(True)  # Start as read-only
        
        # Edit and Save buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        self.edit_button = QPushButton("Edit")
        self.edit_button.setToolTip("Enable editing of text content")
        self.edit_button.clicked.connect(self._on_edit_clicked)
        self.edit_button.setEnabled(False)  # Disabled until a note is selected
        
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
        selected_rows = self.notes_table.selectionModel().selectedRows()
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
        """Populate detail form with data from selected note."""
        self._updating_form = True
        
        try:
            # Block signals to prevent recursive updates
            self.detail_text.blockSignals(True)
            
            # Get Note object directly from project_data
            if row < len(self.project_data.notes):
                note = self.project_data.notes[row]
                self.detail_text.setPlainText(note.text if note.text else "")
                # Update group box title to show which note is selected
                self.detail_group.setTitle(f"Note {note.note_id}")
                # Enable Edit button only when a valid note exists
                self._set_detail_form_enabled(self._detail_form_widgets, True)
            else:
                # Use defaults if note doesn't exist
                self.detail_text.setPlainText("")
                self.detail_group.setTitle("Note Content")
                # Disable Edit button when no valid note exists
                self._set_detail_form_enabled(self._detail_form_widgets, False)
            
            # Reset to read-only mode and button states
            self.detail_text.setReadOnly(True)
            self.save_button.setEnabled(False)
        finally:
            self.detail_text.blockSignals(False)
            self._updating_form = False

    def _clear_detail_form(self):
        """Clear the detail form when no note is selected."""
        self._updating_form = True
        try:
            # Block signals to prevent recursive updates
            self.detail_text.blockSignals(True)
            self.detail_text.setPlainText("")
            self.detail_text.setReadOnly(True)
            self.detail_group.setTitle("Note Content")  # Reset title when no selection
            # Disable detail form widgets when no note is selected
            self._set_detail_form_enabled(self._detail_form_widgets, False)
            self.save_button.setEnabled(False)
        finally:
            self.detail_text.blockSignals(False)
            self._updating_form = False

    def _on_edit_clicked(self):
        """Enable editing of text content."""
        # Safety check: only allow editing if a valid note is selected
        if self._selected_row is None or self._selected_row >= len(self.project_data.notes):
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
        if self._selected_row is not None and self._selected_row < len(self.project_data.notes):
            note = self.project_data.notes[self._selected_row]
            self._update_table_row_from_note(self._selected_row, note)
        
        # Return to read-only mode
        self.detail_text.setReadOnly(True)
        self.edit_button.setEnabled(True)
        self.save_button.setEnabled(False)

    def _connect_signals(self):
        self.notes_table.itemChanged.connect(self._on_item_changed)
        self.notes_table.selectionModel().selectionChanged.connect(self._on_table_selection_changed)
    
    def _truncate_text(self, text: str, max_length: int = 80) -> str:
        """Truncate text to max_length and add ellipsis if needed."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    def _on_item_changed(self, item):
        """Handle item changes - update UserRole for numeric columns."""
        if item is None:
            return
        
        # CRITICAL: Disconnect signal BEFORE modifying item to prevent infinite loop
        was_connected = False
        try:
            self.notes_table.itemChanged.disconnect(self._on_item_changed)
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
            
            # Note: X, Y, Width, Height are now QSpinBox widgets, not items
            # They handle their own validation and trigger sync via valueChanged signal
            # No need to process them here
            
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
                    self.notes_table.itemChanged.connect(self._on_item_changed)
                except:
                    pass

    def _load_initial_data_impl(self):
        """Load initial data into the table using Note objects directly."""
        notes = self.project_data.notes
        row_count = len(notes)
        self.notes_table.setRowCount(row_count)
        self._initializing = True

        for row_idx in range(row_count):

            # Use helper method to populate row from Note object
            note = notes[row_idx]
            self._update_table_row_from_note(row_idx, note)
        
        # Sort by ID by default
        id_col = self._get_column_index("ID")
        if id_col is not None:
            self.notes_table.sortItems(id_col, Qt.AscendingOrder)
        
        self._initializing = False
        
        # Clear detail form if table is empty
        if row_count == 0:
            self._clear_detail_form()

    def _update_table_row_from_note(self, row_idx: int, note: Note) -> None:
        """Populate a table row from a Note object."""
        # Get column indices
        id_col = self._get_column_index("ID")
        x_col = self._get_column_index("X")
        y_col = self._get_column_index("Y")
        width_col = self._get_column_index("Width")
        height_col = self._get_column_index("Height")
        
        # Update ID column
        if id_col is not None:
            item = self.notes_table.item(row_idx, id_col)
            if item:
                item.setText(str(note.note_id))
                item.setData(Qt.UserRole, note.note_id)
            else:
                item = NumericTableWidgetItem(str(note.note_id))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                item.setData(Qt.UserRole, note.note_id)
                self.notes_table.setItem(row_idx, id_col, item)
        
        # Update X column (QSpinBox widget)
        if x_col is not None:
            spinbox = self.notes_table.cellWidget(row_idx, x_col)
            if spinbox and isinstance(spinbox, QSpinBox):
                spinbox.setValue(note.x)
            else:
                spinbox = QSpinBox()
                spinbox.setMinimum(0)
                spinbox.setMaximum(5000)
                spinbox.setValue(note.x)
                spinbox.setSuffix(" px")
                spinbox.valueChanged.connect(self._sync_data_if_not_initializing)
                self.notes_table.setCellWidget(row_idx, x_col, spinbox)
        
        # Update Y column (QSpinBox widget)
        if y_col is not None:
            spinbox = self.notes_table.cellWidget(row_idx, y_col)
            if spinbox and isinstance(spinbox, QSpinBox):
                spinbox.setValue(note.y)
            else:
                spinbox = QSpinBox()
                spinbox.setMinimum(0)
                spinbox.setMaximum(5000)
                spinbox.setValue(note.y)
                spinbox.setSuffix(" px")
                spinbox.valueChanged.connect(self._sync_data_if_not_initializing)
                self.notes_table.setCellWidget(row_idx, y_col, spinbox)
        
        # Update Width column (QSpinBox widget)
        if width_col is not None:
            spinbox = self.notes_table.cellWidget(row_idx, width_col)
            if spinbox and isinstance(spinbox, QSpinBox):
                spinbox.setValue(note.width)
            else:
                spinbox = QSpinBox()
                spinbox.setMinimum(1)
                spinbox.setMaximum(5000)
                spinbox.setValue(note.width)
                spinbox.setSuffix(" px")
                spinbox.valueChanged.connect(self._sync_data_if_not_initializing)
                self.notes_table.setCellWidget(row_idx, width_col, spinbox)
        
        # Update Height column (QSpinBox widget)
        if height_col is not None:
            spinbox = self.notes_table.cellWidget(row_idx, height_col)
            if spinbox and isinstance(spinbox, QSpinBox):
                spinbox.setValue(note.height)
            else:
                spinbox = QSpinBox()
                spinbox.setMinimum(1)
                spinbox.setMaximum(5000)
                spinbox.setValue(note.height)
                spinbox.setSuffix(" px")
                spinbox.valueChanged.connect(self._sync_data_if_not_initializing)
                self.notes_table.setCellWidget(row_idx, height_col, spinbox)
        
        # Update Text Align column (combo box)
        text_align_col = self._get_column_index("Text Align")
        if text_align_col is not None:
            combo = self.notes_table.cellWidget(row_idx, text_align_col)
            if combo and isinstance(combo, QComboBox):
                # Find the index of the current value
                index = combo.findText(note.text_align)
                if index >= 0:
                    combo.setCurrentIndex(index)
            elif not combo:
                # Create combo box if it doesn't exist (shouldn't happen if table_utils is used)
                combo = QComboBox()
                combo.addItems(["Left", "Center", "Right"])
                combo.setCurrentText(note.text_align)
                combo.currentTextChanged.connect(self._sync_data_if_not_initializing)
                self.notes_table.setCellWidget(row_idx, text_align_col, combo)
        
        # Update Vertical Align column (combo box)
        vertical_align_col = self._get_column_index("Vertical Align")
        if vertical_align_col is not None:
            combo = self.notes_table.cellWidget(row_idx, vertical_align_col)
            if combo and isinstance(combo, QComboBox):
                # Find the index of the current value
                index = combo.findText(note.vertical_align)
                if index >= 0:
                    combo.setCurrentIndex(index)
            elif not combo:
                # Create combo box if it doesn't exist (shouldn't happen if table_utils is used)
                combo = QComboBox()
                combo.addItems(["Top", "Middle", "Bottom"])
                combo.setCurrentText(note.vertical_align)
                combo.currentTextChanged.connect(self._sync_data_if_not_initializing)
                self.notes_table.setCellWidget(row_idx, vertical_align_col, combo)
        
        # Update Text Preview column (read-only, truncated text)
        text_preview_col = self._get_column_index("Text Preview")
        if text_preview_col is not None:
            full_text = note.text if note.text else ""
            display_text = self._truncate_text(full_text)
            item = self.notes_table.item(row_idx, text_preview_col)
            if item:
                item.setText(display_text)
                item.setToolTip(full_text)  # Show full text in tooltip
            else:
                item = QTableWidgetItem(display_text)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Read-only
                item.setBackground(QBrush(self.app_config.general.read_only_bg_color))
                item.setToolTip(full_text)  # Show full text in tooltip
                self.notes_table.setItem(row_idx, text_preview_col, item)

    def _note_from_table_row(self, row_idx: int) -> Optional[Note]:
        """Extract a Note object from a table row."""
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
            id_item = self.notes_table.item(row_idx, id_col)
            if not id_item:
                return None
            note_id = safe_int(id_item.text())
            if note_id <= 0:
                return None
            
            # Extract X (from QSpinBox widget)
            x_widget = self.notes_table.cellWidget(row_idx, x_col)
            if x_widget and isinstance(x_widget, QSpinBox):
                x = x_widget.value()
            else:
                return None
            if x < 0:
                return None
            
            # Extract Y (from QSpinBox widget)
            y_widget = self.notes_table.cellWidget(row_idx, y_col)
            if y_widget and isinstance(y_widget, QSpinBox):
                y = y_widget.value()
            else:
                return None
            if y < 0:
                return None
            
            # Extract Width (from QSpinBox widget)
            width_widget = self.notes_table.cellWidget(row_idx, width_col)
            if width_widget and isinstance(width_widget, QSpinBox):
                width = width_widget.value()
            else:
                return None
            if width <= 0:
                return None
            
            # Extract Height (from QSpinBox widget)
            height_widget = self.notes_table.cellWidget(row_idx, height_col)
            if height_widget and isinstance(height_widget, QSpinBox):
                height = height_widget.value()
            else:
                return None
            if height <= 0:
                return None
            
            # Get Text from detail form if this row is selected, otherwise from existing note
            text = ""
            if row_idx == self._selected_row and hasattr(self, 'detail_text') and self.detail_text:
                text = self.detail_text.toPlainText()
            else:
                existing_note = next((n for n in self.project_data.notes if n.note_id == note_id), None)
                if existing_note and existing_note.text:
                    text = existing_note.text
            
            # Extract Text Align
            text_align = "Center"  # Default
            if text_align_col is not None:
                combo = self.notes_table.cellWidget(row_idx, text_align_col)
                if combo and isinstance(combo, QComboBox):
                    text_align = combo.currentText()
                else:
                    # Fallback to existing value if combo doesn't exist
                    existing_note = next((n for n in self.project_data.notes if n.note_id == note_id), None)
                    if existing_note:
                        text_align = existing_note.text_align
            
            # Extract Vertical Align
            vertical_align = "Middle"  # Default
            if vertical_align_col is not None:
                combo = self.notes_table.cellWidget(row_idx, vertical_align_col)
                if combo and isinstance(combo, QComboBox):
                    vertical_align = combo.currentText()
                else:
                    # Fallback to existing value if combo doesn't exist
                    existing_note = next((n for n in self.project_data.notes if n.note_id == note_id), None)
                    if existing_note:
                        vertical_align = existing_note.vertical_align
            
            return Note(
                note_id=note_id,
                x=x,
                y=y,
                width=width,
                height=height,
                text=text,
                text_align=text_align,
                vertical_align=vertical_align
            )
        except (ValueError, AttributeError, Exception) as e:
            logging.error(f"Error extracting note from table row {row_idx}: {e}")
            return None

    def _sync_data_impl(self):
        """Extract data from table and update project_data using Note objects directly."""
        if self._initializing:
            return
        
        try:
            # Extract Note objects from table rows
            notes = []
            for row_idx in range(self.notes_table.rowCount()):
                try:
                    note = self._note_from_table_row(row_idx)
                    if note:
                        notes.append(note)
                except Exception as e:
                    # Log error for this specific row but continue processing other rows
                    logging.error(f"Error extracting note from row {row_idx}: {e}")
                    continue
            
            # Update project data with Note objects directly
            self.project_data.notes = notes
            
            # Only update detail form if change came from table (not from detail form itself)
            # We can detect this by checking if _updating_form is False (meaning user edited table, not form)
            if self._selected_row is not None and self._selected_row < len(notes) and not self._updating_form:
                self._populate_detail_form(self._selected_row)
        except Exception as e:
            # Catch any unexpected exceptions during sync
            logging.error(f"Error in _sync_data_impl: {e}", exc_info=True)
            raise  # Re-raise so BaseTab can show error message

