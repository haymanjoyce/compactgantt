from PyQt5.QtWidgets import QTableWidgetItem, QComboBox, QCheckBox, QWidget, QHBoxLayout, QMessageBox, QSpinBox, QDateEdit
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QBrush, QColor
from datetime import datetime
from typing import Optional
import logging
from config.ui_config import UIConfig
from config.date_config import DateConfig
from utils.conversion import parse_internal_date

# Read-only cell background color (light gray) - centralized in UIConfig
_ui_config = UIConfig()
READ_ONLY_BG = _ui_config.read_only_bg_color

# Logging is configured centrally in utils/logging_config.py

class NumericTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        """Compare items numerically using UserRole data for proper numeric sorting."""
        self_data = self.data(Qt.UserRole)
        other_data = other.data(Qt.UserRole) if other else None
        
        # Try numeric comparison if both have UserRole data
        if self_data is not None and other_data is not None:
            try:
                return float(self_data) < float(other_data)
            except (TypeError, ValueError):
                pass
        
        # Fallback: try to parse text as numbers
        try:
            self_text = self.text().strip()
            other_text = other.text().strip() if other else ""
            if self_text and other_text:
                return float(self_text) < float(other_text)
        except (ValueError, AttributeError):
            pass
        
        # Final fallback: text comparison
        return super().__lt__(other)

class DateTableWidgetItem(QTableWidgetItem):
    def __init__(self, text: str = "", date_config: Optional[DateConfig] = None):
        """Initialize DateTableWidgetItem with optional DateConfig.
        
        Args:
            text: Initial text for the item
            date_config: Optional DateConfig instance. If None, uses default.
        """
        super().__init__(text)
        self._date_config = date_config or DateConfig()
    
    def __lt__(self, other):
        """Compare items by date for proper chronological sorting."""
        self_data = self.data(Qt.UserRole)
        other_data = other.data(Qt.UserRole) if other else None
        
        # Try date comparison if both have UserRole data (datetime objects)
        if self_data is not None and other_data is not None:
            try:
                if isinstance(self_data, datetime) and isinstance(other_data, datetime):
                    return self_data < other_data
            except (TypeError, ValueError):
                pass
        
        # Fallback: try to parse text as dates using config format
        try:
            self_text = self.text().strip()
            other_text = other.text().strip() if other else ""
            if self_text and other_text:
                date_format = self._date_config.get_python_format()
                self_date = datetime.strptime(self_text, date_format)
                other_date = datetime.strptime(other_text, date_format)
                return self_date < other_date
        except (ValueError, AttributeError):
            pass
        
        # Final fallback: text comparison
        return super().__lt__(other)

class CheckBoxWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.checkbox = QCheckBox()
        layout.addWidget(self.checkbox, alignment=Qt.AlignCenter)
        self.setLayout(layout)

class DateEditWidget(QDateEdit):
    """QDateEdit widget for use in table cells with calendar popup."""
    def __init__(self, parent=None, date_config: Optional[DateConfig] = None):
        """Initialize DateEditWidget with optional DateConfig.
        
        Args:
            parent: Parent widget
            date_config: Optional DateConfig instance. If None, uses default.
        """
        super().__init__(parent)
        self._date_config = date_config or DateConfig()
        self.setCalendarPopup(True)
        self.setDisplayFormat(self._date_config.get_qt_format())
        self.setDate(QDate.currentDate())

def create_date_widget(internal_date: str, date_config: DateConfig) -> DateEditWidget:
    """Create a DateEditWidget from an internal date string (yyyy-mm-dd format).
    
    Args:
        internal_date: Date string in yyyy-mm-dd format (ISO format)
        date_config: DateConfig instance for date formatting
        
    Returns:
        DateEditWidget with date set (or current date if invalid/empty)
    """
    from utils.conversion import display_to_internal_date
    
    widget = DateEditWidget(date_config=date_config)
    if internal_date and internal_date.strip():
        date_dt = parse_internal_date(internal_date)
        if date_dt:
            date_qdate = QDate(date_dt.year, date_dt.month, date_dt.day)
            widget.setDate(date_qdate)
        else:
            widget.setDate(QDate.currentDate())
    else:
        widget.setDate(QDate.currentDate())
    return widget

def extract_date_from_cell(table, row: int, col: int, date_config: DateConfig) -> Optional[str]:
    """Extract date from QDateEdit widget or text item, returning internal format (yyyy-mm-dd).
    
    Uses key-based approach: checks for QDateEdit widget first, then falls back to text item.
    
    Args:
        table: QTableWidget containing the cell
        row: Row index (0-based)
        col: Column index (0-based)
        date_config: DateConfig instance for date parsing
        
    Returns:
        Date string in yyyy-mm-dd format if found, None otherwise
    """
    from utils.conversion import display_to_internal_date
    
    # Try QDateEdit widget first (preferred method)
    widget = table.cellWidget(row, col)
    if widget and isinstance(widget, QDateEdit):
        return widget.date().toString("yyyy-MM-dd")
    
    # Fallback to text item (for backward compatibility)
    item = table.item(row, col)
    if item and item.text().strip():
        try:
            return display_to_internal_date(item.text(), date_config)
        except ValueError:
            return None
    return None

def highlight_table_errors(table, errors):
    """
    Common function to highlight errors in table rows.
    
    Args:
        table: QTableWidget to highlight
        errors: List of error messages
    """
    # Clear all highlights first
    table.blockSignals(True)
    for row in range(table.rowCount()):
        for col in range(table.columnCount()):
            item = table.item(row, col)
            if item:
                item.setBackground(QBrush())
                item.setToolTip("")
    
    # Highlight cells with errors
    if errors:
        for error in errors:
            if error.startswith("Row"):
                try:
                    row_str = error.split(":")[0].replace("Row ", "")
                    row_idx = int(row_str) - 1
                    # Highlight the entire row
                    for col in range(table.columnCount()):
                        item = table.item(row_idx, col)
                        if item:
                            item.setBackground(QBrush(Qt.yellow))
                            item.setToolTip(error.split(":", 1)[1].strip())
                except (ValueError, IndexError):
                    logging.error(f"Failed to parse error message: {error}")
                    continue
        
        QMessageBox.critical(table.parent(), "Error", "\n".join(errors))
    
    table.blockSignals(False)

def extract_table_data(table, include_widgets=True, date_config: Optional[DateConfig] = None):
    """
    Common function to extract data from table, skipping the checkbox column.
    
    Args:
        table: QTableWidget to extract data from
        include_widgets: Whether to handle widget cells (like QComboBox, QDateEdit)
        date_config: Optional DateConfig instance. If None, uses default.
    
    Returns:
        List of lists containing table data
    """
    # Use default config if not provided (backward compatibility)
    if date_config is None:
        date_config = DateConfig()
    
    data = []
    for row in range(table.rowCount()):
        row_data = []
        # Extract data from all columns
        for col in range(table.columnCount()):
            if include_widgets:
                widget = table.cellWidget(row, col)
                if widget and isinstance(widget, QComboBox):
                    row_data.append(widget.currentText())
                elif widget and isinstance(widget, QDateEdit):
                    # Format date using config format
                    date_format = date_config.get_qt_format()
                    row_data.append(widget.date().toString(date_format))
                else:
                    item = table.item(row, col)
                    row_data.append(item.text() if item else "")
            else:
                item = table.item(row, col)
                row_data.append(item.text() if item else "")
        data.append(row_data)
    return data

def add_row(table, table_key, table_configs, parent, id_field_name, row_index=None, default_row_number=None, date_config: Optional[DateConfig] = None, default_start_date: Optional[str] = None, default_finish_date: Optional[str] = None):
    """Add a row to a table with proper ID and sorting handling, using generic default value logic.

    Args:
        default_row_number: Optional default row number for tasks table (if None, defaults to 1)
        default_start_date: Optional start date string in internal format "yyyy-MM-dd" to pre-fill Start Date widget
        default_finish_date: Optional finish date string in internal format "yyyy-MM-dd" to pre-fill Finish Date widget
    """
    try:
        config = table_configs.get(table_key)
        if not config:
            logging.error(f"No table config found for key: {table_key}")
            return

        # Save current sort state
        was_sorting = table.isSortingEnabled()
        sort_col = table.horizontalHeader().sortIndicatorSection()
        sort_order = table.horizontalHeader().sortIndicatorOrder()
        
        table.setSortingEnabled(False)
        table.blockSignals(True)

        # Find the ID column index using the provided id_field_name (key-based lookup)
        id_column = None
        for i in range(table.columnCount()):
            header_item = table.horizontalHeaderItem(i)
            if header_item and header_item.text() == id_field_name:
                id_column = i
                break

        if id_column is None:
            available_columns = []
            for i in range(table.columnCount()):
                header_item = table.horizontalHeaderItem(i)
                available_columns.append(header_item.text() if header_item else f"Column {i}")
            error_msg = f"Could not find ID column '{id_field_name}' in table. Available columns: {available_columns}"
            logging.error(error_msg)
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(parent, "Error", error_msg)
            table.blockSignals(False)
            table.setSortingEnabled(was_sorting)
            return

        # Calculate next available ID
        used_ids = set()
        for row in range(table.rowCount()):
            item = table.item(row, id_column)
            try:
                if item and item.text():
                    used_ids.add(int(item.text()))
            except (ValueError, TypeError):
                continue

        # Find the next available ID
        next_id = 1
        while next_id in used_ids:
            next_id += 1

        # Insert the row at specified index or append
        if row_index is None:
            row_index = table.rowCount()
        table.insertRow(row_index)

        # Special handling for links table - both fields should be editable and blank
        is_links_table = (table_key == "links")

        # Set default values for each column
        for col_idx in range(table.columnCount()):
            header_text = table.horizontalHeaderItem(col_idx).text()
            col_config = None
            if hasattr(config, "columns"):
                # Find the config for this column by name (not by index, since visible columns may be a subset)
                for col in config.columns:
                    if col.name == header_text:
                        col_config = col
                        break

            # Set ID column - use header text to identify it (key-based, not positional)
            if header_text == id_field_name:
                # For links, ID should be auto-generated and read-only (like tasks)
                if is_links_table:
                    id_item = NumericTableWidgetItem(str(next_id))
                    id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                    id_item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                    id_item.setData(Qt.UserRole, int(next_id))
                else:
                    id_item = NumericTableWidgetItem(str(next_id))
                    id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
                    id_item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                    id_item.setData(Qt.UserRole, int(next_id))
                table.setItem(row_index, col_idx, id_item)
            # Valid column for links and tasks - read-only text (check BEFORE combo box to ensure it's never a combo)
            elif header_text == "Valid":
                # Default to "No" for links (will be calculated when both task IDs are entered)
                # Default to "Yes" for tasks (will be calculated based on validation)
                default_value = "No" if is_links_table else "Yes"
                item = QTableWidgetItem(default_value)  # Will be calculated later
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                table.setItem(row_index, col_idx, item)
            # Combo box column
            elif col_config and getattr(col_config, "widget_type", None) == "combo":
                combo = QComboBox()
                combo.addItems(col_config.combo_items)
                combo.setCurrentIndex(0)  # Use first item as default
                # Connect signal to sync data when combo box value changes
                if hasattr(parent, '_sync_data_if_not_initializing'):
                    combo.currentTextChanged.connect(parent._sync_data_if_not_initializing)
                table.setCellWidget(row_index, col_idx, combo)
            # Date column - check by column name for tasks, pipes, and curtains tables
            elif header_text in ["Start Date", "Finish Date", "Date", "End Date"]:
                # Use provided date_config or default
                if date_config is None:
                    date_config = DateConfig()
                date_edit = DateEditWidget(date_config=date_config)
                # Use inherited default dates if provided, otherwise default to today
                inherited_date = None
                if header_text == "Start Date" and default_start_date:
                    inherited_date = QDate.fromString(default_start_date, "yyyy-MM-dd")
                elif header_text == "Finish Date" and default_finish_date:
                    inherited_date = QDate.fromString(default_finish_date, "yyyy-MM-dd")
                if inherited_date and inherited_date.isValid():
                    date_edit.setDate(inherited_date)
                else:
                    date_edit.setDate(QDate.currentDate())  # Default to today
                # Connect signal to sync data when date changes
                if hasattr(parent, '_sync_data_if_not_initializing'):
                    date_edit.dateChanged.connect(parent._sync_data_if_not_initializing)
                # Connect constraint updates for tasks and curtains (Start/Finish Date columns)
                if header_text in ["Start Date", "Finish Date"] and hasattr(parent, '_update_task_date_constraints'):
                    date_edit.dateChanged.connect(lambda date, w=date_edit: parent._update_task_date_constraints(widget=w))
                elif header_text in ["Start Date", "End Date"] and hasattr(parent, '_update_curtain_date_constraints'):
                    date_edit.dateChanged.connect(lambda date, w=date_edit: parent._update_curtain_date_constraints(widget=w))
                table.setCellWidget(row_index, col_idx, date_edit)
            # Numeric column - check by column name for tasks table (Chart Row) - ID handled above
            elif header_text == "Chart Row":
                # Use provided default_row_number if available (for tasks), otherwise default to 1
                row_value = default_row_number if default_row_number is not None else 1
                item = NumericTableWidgetItem(str(row_value))
                item.setData(Qt.UserRole, row_value)
                table.setItem(row_index, col_idx, item)
            # Numeric column - check by column name for swimlanes table (Minimum Row Count)
            elif header_text == "Minimum Row Count":
                item = NumericTableWidgetItem("1")  # Default minimum row count
                item.setData(Qt.UserRole, 1)
                table.setItem(row_index, col_idx, item)
            # Numeric columns for notes (X, Y, Width, Height) - use QSpinBox widgets
            elif header_text in ["X", "Y"]:
                spinbox = QSpinBox()
                spinbox.setMinimum(0)
                spinbox.setMaximum(5000)
                spinbox.setValue(0)
                spinbox.setSuffix(" px")
                if hasattr(parent, '_sync_data_if_not_initializing'):
                    spinbox.valueChanged.connect(parent._sync_data_if_not_initializing)
                table.setCellWidget(row_index, col_idx, spinbox)
            elif header_text in ["Width", "Height"]:
                spinbox = QSpinBox()
                spinbox.setMinimum(1)
                spinbox.setMaximum(5000)
                spinbox.setValue(100)
                spinbox.setSuffix(" px")
                if hasattr(parent, '_sync_data_if_not_initializing'):
                    spinbox.valueChanged.connect(parent._sync_data_if_not_initializing)
                table.setCellWidget(row_index, col_idx, spinbox)
            # Numeric column for links (From Task ID, To Task ID) - both should be editable
            elif is_links_table and header_text in ["From Task ID", "To Task ID"]:
                item = NumericTableWidgetItem("")
                item.setData(Qt.UserRole, 0)
                table.setItem(row_index, col_idx, item)
            # Name columns for links (From Task Name, To Task Name) - read-only text
            elif is_links_table and header_text in ["From Task Name", "To Task Name"]:
                item = QTableWidgetItem("")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                table.setItem(row_index, col_idx, item)
            # Lane column for tasks table - read-only text
            elif header_text == "Lane":
                item = QTableWidgetItem("")  # Will be populated by tasks_tab
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                table.setItem(row_index, col_idx, item)
            # Text Preview column for text boxes - read-only text
            elif header_text == "Text Preview":
                item = QTableWidgetItem("")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                table.setItem(row_index, col_idx, item)
            # Numeric column (optional: check for numeric type)
            elif col_config and getattr(col_config, "widget_type", None) == "numeric":
                item = NumericTableWidgetItem("")
                table.setItem(row_index, col_idx, item)
            # Generic text column
            else:
                item = QTableWidgetItem("")
                table.setItem(row_index, col_idx, item)

        # Set initial date constraints for tasks and curtains tables
        # This ensures constraints are active immediately when a new row is created
        if table_key == "tasks" and hasattr(parent, '_update_task_date_constraints'):
            # Find Start Date and Finish Date columns
            start_date_col = None
            finish_date_col = None
            for col_idx in range(table.columnCount()):  # Check all columns
                header_text = table.horizontalHeaderItem(col_idx).text()
                if header_text == "Start Date":
                    start_date_col = col_idx
                elif header_text == "Finish Date":
                    finish_date_col = col_idx
            
            if start_date_col is not None and finish_date_col is not None:
                # Set constraints for the new row
                parent._update_task_date_constraints(row_idx=row_index)
        
        elif table_key == "curtains" and hasattr(parent, '_update_curtain_date_constraints'):
            # Find Start Date and End Date columns
            start_date_col = None
            end_date_col = None
            for col_idx in range(table.columnCount()):
                header_text = table.horizontalHeaderItem(col_idx).text()
                if header_text == "Start Date":
                    start_date_col = col_idx
                elif header_text == "End Date":
                    end_date_col = col_idx
            
            if start_date_col is not None and end_date_col is not None:
                # Set constraints for the new row
                parent._update_curtain_date_constraints(row_idx=row_index)

        # Restore table state
        table.blockSignals(False)
        table.setSortingEnabled(was_sorting)
        if was_sorting:
            table.sortByColumn(sort_col, sort_order)

        # Sync data
        parent._sync_data()
        
        # Tasks table specific: sort and select the new task
        if table_key == "tasks" and hasattr(parent, '_sort_tasks_by_swimlane_and_row'):
            # Store the new task ID before sorting
            new_task_id = next_id
            
            # Sort the table to place new task in correct position
            parent._sort_tasks_by_swimlane_and_row()
            
            # Find and select the new task after sorting
            id_col = None
            for i in range(table.columnCount()):
                header_item = table.horizontalHeaderItem(i)
                if header_item and header_item.text() == id_field_name:
                    id_col = i
                    break
            
            if id_col is not None:
                for row_idx in range(table.rowCount()):
                    item = table.item(row_idx, id_col)
                    if item:
                        try:
                            task_id = int(item.text())
                            if task_id == new_task_id:
                                # Select the row and scroll to it
                                table.selectRow(row_idx)
                                table.scrollToItem(item)
                                break
                        except (ValueError, TypeError):
                            continue
        
        # Refresh Order/Lane column if parent has this method (for swimlanes table)
        if hasattr(parent, '_refresh_order_column'):
            parent._refresh_order_column()
        elif hasattr(parent, '_refresh_lane_column'):
            parent._refresh_lane_column()
        

    except Exception as e:
        logging.error(f"Error in add_row: {e}", exc_info=True)
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(parent, "Error", f"Failed to add row: {e}")
    finally:
        table.blockSignals(False)
        table.setSortingEnabled(was_sorting)

def remove_row(table, table_key, table_configs, parent):
    """Remove selected rows from the table."""
    try:
        table_config = table_configs.get(table_key)
        if not table_config:
            return

        # Get all selected rows
        selected_rows = table.selectionModel().selectedRows()
        if not selected_rows:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(parent, "No Selection", "Please select rows to remove.")
            return
        
        checked_rows = [row.row() for row in selected_rows]

        # Sort in reverse order to avoid index shifting
        checked_rows.sort(reverse=True)

        # Check if we can remove the rows
        if checked_rows and table.rowCount() - len(checked_rows) >= table_config.min_rows:
            for row in checked_rows:
                table.removeRow(row)
            parent._sync_data()
            
            # Refresh Lane column if parent has this method (for swimlanes table)
            if hasattr(parent, '_refresh_lane_column'):
                parent._refresh_lane_column()
            
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(parent, "Cannot Remove", 
                              f"Cannot remove all selected rows. Table must have at least {table_config.min_rows} row(s).")
    except Exception as e:
        logging.error(f"Error in remove_row: {e}", exc_info=True)
        raise
