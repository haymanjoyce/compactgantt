from PyQt5.QtWidgets import QTableWidgetItem, QComboBox, QCheckBox, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt, QDate
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class NumericTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        self_data = self.data(Qt.UserRole)
        other_data = other.data(Qt.UserRole)
        if self_data is not None and other_data is not None:
            try:
                return float(self_data) < float(other_data)
            except (TypeError, ValueError):
                pass
        return super().__lt__(other)

class CheckBoxWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setAlignment(Qt.AlignCenter)
        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("""
            QCheckBox {
                padding: 2px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
        """)
        layout.addWidget(self.checkbox)
        self.setLayout(layout)

def add_row(table, table_key, table_configs, parent, id_field_name, row_index=None):
    """Add a row to a table with proper ID and sorting handling."""
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

        # Add checkbox first
        checkbox_widget = CheckBoxWidget()
        table.setCellWidget(row_index, 0, checkbox_widget)

        # Add ID
        id_item = QTableWidgetItem(str(next_id))
        id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)  # Make ID read-only
        table.setItem(row_index, id_column, id_item)

        # Add default values for other columns
        finish_date = QDate.currentDate().addDays(7).toString("yyyy-MM-dd")
        width = "50.0"

        # Find column indices
        for i in range(table.columnCount()):
            header_text = table.horizontalHeaderItem(i).text()
            if header_text == "Finish Date":
                table.setItem(row_index, i, QTableWidgetItem(finish_date))
            elif header_text == "Width (%)":
                table.setItem(row_index, i, QTableWidgetItem(width))

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
        task_orders = []
        for row in range(table.rowCount()):
            item = table.item(row, 1)  # Task Order column
            try:
                task_orders.append((row, float(item.text()) if item and item.text() else 0.0))
            except ValueError:
                task_orders.append((row, 0.0))
        task_orders.sort(key=lambda x: x[1])
        for new_order, (row, _) in enumerate(task_orders, 1):
            item = table.item(row, 1)
            if not item:
                item = NumericTableWidgetItem()
                table.setItem(row, 1, item)
            item.setText(str(new_order))
            item.setData(Qt.UserRole, float(new_order))
        table.blockSignals(False)
        table.setSortingEnabled(was_sorting)
        logging.debug("renumber_task_orders completed")
    except Exception as e:
        logging.error(f"Error in renumber_task_orders: {e}", exc_info=True)
        raise