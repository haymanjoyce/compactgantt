from PyQt5.QtWidgets import QTableWidgetItem, QComboBox, QCheckBox, QWidget, QHBoxLayout, QMessageBox
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QBrush, QColor
from datetime import datetime
import logging

# Read-only cell background color (light gray)
READ_ONLY_BG = QColor(240, 240, 240)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
        
        # Fallback: try to parse text as dates (dd/mm/yyyy format)
        try:
            self_text = self.text().strip()
            other_text = other.text().strip() if other else ""
            if self_text and other_text:
                self_date = datetime.strptime(self_text, "%d/%m/%Y")
                other_date = datetime.strptime(other_text, "%d/%m/%Y")
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
        for col in range(1, table.columnCount()):  # Skip checkbox column
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
                    for col in range(1, table.columnCount()):
                        item = table.item(row_idx, col)
                        if item:
                            item.setBackground(QBrush(Qt.yellow))
                            item.setToolTip(error.split(":", 1)[1].strip())
                except (ValueError, IndexError):
                    logging.error(f"Failed to parse error message: {error}")
                    continue
        
        QMessageBox.critical(table.parent(), "Error", "\n".join(errors))
    
    table.blockSignals(False)

def extract_table_data(table, include_widgets=True):
    """
    Common function to extract data from table, skipping the checkbox column.
    
    Args:
        table: QTableWidget to extract data from
        include_widgets: Whether to handle widget cells (like QComboBox)
    
    Returns:
        List of lists containing table data
    """
    data = []
    for row in range(table.rowCount()):
        row_data = []
        # Start from column 1 to skip checkbox column
        for col in range(1, table.columnCount()):
            if include_widgets:
                widget = table.cellWidget(row, col)
                if widget and isinstance(widget, QComboBox):
                    row_data.append(widget.currentText())
                else:
                    item = table.item(row, col)
                    row_data.append(item.text() if item else "")
            else:
                item = table.item(row, col)
                row_data.append(item.text() if item else "")
        data.append(row_data)
    return data

def add_row(table, table_key, table_configs, parent, id_field_name, row_index=None):
    """Add a row to a table with proper ID and sorting handling, using generic default value logic."""
    logging.debug(f"Starting add_row for {table_key}")
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

        # Find the ID column index using the provided id_field_name
        id_column = None
        for i in range(table.columnCount()):
            if table.horizontalHeaderItem(i).text() == id_field_name:
                id_column = i
                break

        if id_column is None:
            logging.error(f"Could not find ID column: {id_field_name}")
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

        # Add checkbox first (assume first column is always checkbox)
        checkbox_widget = CheckBoxWidget()
        table.setCellWidget(row_index, 0, checkbox_widget)

        # Special handling for links table - both fields should be editable and blank
        is_links_table = (table_key == "links")
        
        # Prepare context for default_generator if available
        context = {"max_id": next_id}
        if hasattr(config, "default_generator"):
            defaults = config.default_generator(row_index, context)
            # For links, we want blank From/To Task IDs but Valid should default to "Yes"
            # ID (index 0) is already set by default_generator
            if is_links_table:
                if len(defaults) >= 6:
                    defaults[1] = ""  # From Task ID - blank (index 1)
                    defaults[2] = ""  # From Task Name - blank (index 2, will be populated from task lookup)
                    defaults[3] = ""  # To Task ID - blank (index 3)
                    defaults[4] = ""  # To Task Name - blank (index 4, will be populated from task lookup)
                    defaults[5] = "Yes"  # Valid - default to "Yes" (index 5)
                    # ID (index 0) is already set by default_generator
                else:
                    # Ensure we have 6 elements: [ID, From Task ID, From Task Name, To Task ID, To Task Name, Valid]
                    defaults = [str(next_id), "", "", "", "", "Yes"]
        else:
            # If no generator, use empty strings except Valid column for links
            defaults = [""] * (table.columnCount() - 1)  # Exclude checkbox column
            # Set Valid column default to "Yes" for links
            if is_links_table and len(defaults) >= 6:
                defaults[5] = "Yes"  # Index 5 in defaults (0=ID, 1=From Task ID, 2=From Task Name, 3=To Task ID, 4=To Task Name, 5=Valid)

        # Set default values for each column (skip checkbox column)
        for col_idx in range(1, table.columnCount()):
            header_text = table.horizontalHeaderItem(col_idx).text()
            col_config = None
            if hasattr(config, "columns"):
                # Find the config for this column (config.columns includes "Select" at index 0)
                try:
                    col_config = config.columns[col_idx]
                except (IndexError, AttributeError):
                    pass

            # Use default from generator if available, else empty string
            default = ""
            if defaults and col_idx < len(defaults):
                default = defaults[col_idx]  # defaults already includes checkbox at index 0

            # Set ID column - use NumericTableWidgetItem for numeric sorting
            if col_idx == id_column:
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
            # Combo box column
            elif col_config and getattr(col_config, "widget_type", None) == "combo":
                combo = QComboBox()
                combo.addItems(col_config.combo_items)
                combo.setCurrentText(str(default) if default else col_config.combo_items[0])
                # Connect signal to sync data when combo box value changes
                if hasattr(parent, '_sync_data_if_not_initializing'):
                    combo.currentTextChanged.connect(parent._sync_data_if_not_initializing)
                table.setCellWidget(row_index, col_idx, combo)
            # Valid column for links - read-only text
            elif is_links_table and header_text == "Valid":
                item = QTableWidgetItem(str(default) if default else "Yes")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                table.setItem(row_index, col_idx, item)
            # Date column - check by column name for tasks table (Start Date, Finish Date)
            elif header_text in ["Start Date", "Finish Date"]:
                item = DateTableWidgetItem(str(default))
                # Set UserRole with datetime object for sorting
                try:
                    if default and str(default).strip():
                        date_obj = datetime.strptime(str(default).strip(), "%d/%m/%Y")
                        item.setData(Qt.UserRole, date_obj)
                    else:
                        item.setData(Qt.UserRole, None)
                except (ValueError, AttributeError):
                    item.setData(Qt.UserRole, None)
                table.setItem(row_index, col_idx, item)
            # Numeric column - check by column name for tasks table (ID, Order, Row)
            elif header_text in ["ID", "Order", "Row"]:
                item = NumericTableWidgetItem(str(default))
                # Set UserRole for numeric sorting
                try:
                    if header_text == "Order":
                        item.setData(Qt.UserRole, float(str(default).strip()) if str(default).strip() else 0.0)
                    else:  # ID or Row
                        item.setData(Qt.UserRole, int(str(default).strip()) if str(default).strip() else (0 if header_text == "ID" else 1))
                except (ValueError, AttributeError):
                    item.setData(Qt.UserRole, 0.0 if header_text == "Order" else (0 if header_text == "ID" else 1))
                table.setItem(row_index, col_idx, item)
            # Numeric column for links (From Task ID, To Task ID) - both should be editable
            elif is_links_table and header_text in ["From Task ID", "To Task ID"]:
                item = NumericTableWidgetItem(str(default))
                try:
                    item.setData(Qt.UserRole, int(str(default).strip()) if str(default).strip() else 0)
                except (ValueError, AttributeError):
                    item.setData(Qt.UserRole, 0)
                table.setItem(row_index, col_idx, item)
            # Name columns for links (From Task Name, To Task Name) - read-only text
            elif is_links_table and header_text in ["From Task Name", "To Task Name"]:
                item = QTableWidgetItem(str(default) if default else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make read-only
                item.setBackground(QBrush(READ_ONLY_BG))  # Gray background
                table.setItem(row_index, col_idx, item)
            # Numeric column (optional: check for numeric type)
            elif col_config and getattr(col_config, "widget_type", None) == "numeric":
                item = NumericTableWidgetItem(str(default))
                table.setItem(row_index, col_idx, item)
            # Generic text column
            else:
                item = QTableWidgetItem(str(default))
                table.setItem(row_index, col_idx, item)

        # Restore table state
        table.blockSignals(False)
        table.setSortingEnabled(was_sorting)
        if was_sorting:
            table.sortByColumn(sort_col, sort_order)

        # Sync data
        parent._sync_data()
        logging.debug(f"Row added successfully at index {row_index}")

    except Exception as e:
        logging.error(f"Error in add_row: {e}", exc_info=True)
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(parent, "Error", f"Failed to add row: {e}")
    finally:
        table.blockSignals(False)
        table.setSortingEnabled(was_sorting)

def remove_row(table, table_key, table_configs, parent):
    """Remove checked rows from the table."""
    logging.debug(f"Starting remove_row for table_key: {table_key}")
    try:
        table_config = table_configs.get(table_key)
        if not table_config:
            return

        # Get all checked rows
        checked_rows = []
        for row in range(table.rowCount()):
            checkbox_widget = table.cellWidget(row, 0)
            if checkbox_widget and isinstance(checkbox_widget, CheckBoxWidget):
                if checkbox_widget.checkbox.isChecked():
                    checked_rows.append(row)

        # Sort in reverse order to avoid index shifting
        checked_rows.sort(reverse=True)

        # Check if we can remove the rows
        if checked_rows and table.rowCount() - len(checked_rows) >= table_config.min_rows:
            for row in checked_rows:
                table.removeRow(row)
            parent._sync_data()
            logging.debug(f"Removed {len(checked_rows)} rows")
        elif not checked_rows:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(parent, "No Selection", "Please select rows to remove by checking their checkboxes.")
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(parent, "Cannot Remove", 
                              f"Cannot remove all selected rows. Table must have at least {table_config.min_rows} row(s).")
    except Exception as e:
        logging.error(f"Error in remove_row: {e}", exc_info=True)
        raise

def renumber_task_orders(table):
    logging.debug("Starting renumber_task_orders")
    try:
        was_sorting = table.isSortingEnabled()
        table.setSortingEnabled(False)
        table.blockSignals(True)
        
        # Find the Task Order column index
        order_column = None
        for i in range(table.columnCount()):
            if table.horizontalHeaderItem(i).text() == "Order":
                order_column = i
                break
        
        if order_column is None:
            logging.error("Could not find Order column")
            return
            
        task_orders = []
        for row in range(table.rowCount()):
            item = table.item(row, order_column)  # Task Order column
            try:
                task_orders.append((row, float(item.text()) if item and item.text() else 0.0))
            except ValueError:
                task_orders.append((row, 0.0))
        task_orders.sort(key=lambda x: x[1])
        for new_order, (row, _) in enumerate(task_orders, 1):
            item = table.item(row, order_column)
            if not item:
                item = NumericTableWidgetItem()
                table.setItem(row, order_column, item)
            item.setText(str(new_order))
            item.setData(Qt.UserRole, float(new_order))
        table.blockSignals(False)
        table.setSortingEnabled(was_sorting)
        logging.debug("renumber_task_orders completed")
    except Exception as e:
        logging.error(f"Error in renumber_task_orders: {e}", exc_info=True)
        raise