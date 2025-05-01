from PyQt5.QtWidgets import QTableWidgetItem, QMenu, QComboBox, QAction
from PyQt5.QtCore import Qt
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

def add_row(table, table_key, table_configs, parent, context=None):
    print(f"add_row called for {table_key}")
    logging.debug(f"Starting add_row for table_key: {table_key}, context: {context}")
    try:
        # Calculate next ID for tables that need unique IDs
        if context is None and table_key == "time_frames":
            max_id = 0
            for row in range(table.rowCount()):
                item = table.item(row, 0)  # ID is always in first column
                try:
                    if item and item.text():
                        max_id = max(max_id, int(item.text()))
                except (ValueError, TypeError):
                    logging.warning(f"Invalid ID in row {row}: {item.text() if item else 'None'}")
                    continue
            context = {"max_time_frame_id": max_id}
            logging.debug(f"Calculated max_time_frame_id: {max_id}, context: {context}")

        was_sorting = table.isSortingEnabled()
        table.setSortingEnabled(False)
        table.blockSignals(True)

        table_config = table_configs.get(table_key)
        if not table_config:
            logging.error(f"No table config found for key: {table_key}")
            return

        row_idx = table.rowCount()
        table.insertRow(row_idx)

        defaults = table_config.default_generator(row_idx, context or {})
        for col_idx, default in enumerate(defaults):
            col_config = table_config.columns[col_idx]
            if col_config.widget_type == "combo":
                combo = QComboBox()
                combo.addItems(col_config.combo_items)
                combo.setCurrentText(str(default) or col_config.combo_items[0])
                table.setCellWidget(row_idx, col_idx, combo)
            else:
                item = QTableWidgetItem(str(default))
                if table_key == "time_frames" and col_idx == 0:  # Time Frame ID column
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        table.blockSignals(False)
        table.setSortingEnabled(was_sorting)
        
        # Sync data
        parent._sync_data()

    except Exception as e:
        logging.error(f"Error in add_row: {e}", exc_info=True)
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(parent, "Error", f"Failed to add row: {e}")
    finally:
        table.blockSignals(False)
        table.setSortingEnabled(was_sorting)

def remove_row(table, table_key, table_configs, parent):
    logging.debug(f"Starting remove_row for table_key: {table_key}")
    try:
        selected_rows = sorted(set(index.row() for index in table.selectedIndexes()), reverse=True)
        table_config = table_configs.get(table_key)
        if not selected_rows and table.rowCount() > table_config.min_rows:
            selected_rows = [table.rowCount() - 1]
        for row in selected_rows:
            if table.rowCount() > table_config.min_rows:
                table.removeRow(row)
        parent._sync_data()
        logging.debug("remove_row completed")
    except Exception as e:
        logging.error(f"Error in remove_row: {e}", exc_info=True)
        raise

def show_context_menu(pos, table, table_key, parent, table_configs):
    logging.debug(f"Showing context menu for table_key: {table_key}")
    try:
        menu = QMenu()
        add_action = QAction("Add Row", parent)
        remove_action = QAction("Remove Selected Row(s)", parent)
        
        # Use insert_row_with_id for all tables, it will handle IDs appropriately
        add_action.triggered.connect(
            lambda: insert_row_with_id(table, table_key, table_configs, parent))
        remove_action.triggered.connect(
            lambda: remove_row(table, table_key, table_configs, parent))
            
        menu.addAction(add_action)
        menu.addAction(remove_action)
        menu.exec_(table.viewport().mapToGlobal(pos))
        logging.debug("Context menu shown")
    except Exception as e:
        logging.error(f"Error in show_context_menu: {e}", exc_info=True)
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

def insert_row_with_id(table, table_key, table_configs, parent, row_index=None, id_column=0):
    """
    Insert a row into a table with proper ID handling.
    
    Args:
        table: QTableWidget - The table to add a row to
        table_key: str - The key identifying the table type
        table_configs: dict - Configuration for all tables
        parent: QWidget - The parent widget (tab) containing the table
        row_index: int or None - Index where to insert the row. If None, adds to end
        id_column: int - The column index containing the ID (default 0)
    """
    logging.debug(f"Starting insert_row_with_id for {table_key}")
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

        # Calculate next ID and prepare context
        context = {}
        max_id = 0
        
        # Calculate max ID from existing rows
        for row in range(table.rowCount()):
            item = table.item(row, id_column)
            try:
                if item and item.text():
                    max_id = max(max_id, int(item.text()))
            except (ValueError, TypeError):
                logging.warning(f"Invalid ID in row {row}: {item.text() if item else 'None'}")
                continue

        # Add task-specific context for task orders
        if table_key == "tasks":
            max_task_order = 0
            for row in range(table.rowCount()):
                item_order = table.item(row, 1)  # Task order column
                if item_order:
                    try:
                        max_task_order = max(max_task_order, float(item_order.text()))
                    except ValueError:
                        pass
            context["max_task_order"] = max_task_order

        # Set the max ID in context
        context[f"max_{table_key.rstrip('s')}_id"] = max_id

        # Insert the row at specified index or append
        if row_index is None:
            row_index = table.rowCount()
        table.insertRow(row_index)

        # Generate and set defaults
        defaults = config.default_generator(row_index, context)
        for col_idx, default in enumerate(defaults):
            col_config = config.columns[col_idx]
            if col_config.widget_type == "combo":
                combo = QComboBox()
                combo.addItems(col_config.combo_items)
                combo.setCurrentText(str(default) or col_config.combo_items[0])
                table.setCellWidget(row_index, col_idx, combo)
            else:
                item = NumericTableWidgetItem(str(default)) if col_idx in (0, 1) else QTableWidgetItem(str(default))
                if table_key in ["time_frames", "tasks"] and col_idx == 0:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if table_key == "tasks" and col_idx == 0:
                    item.setData(Qt.UserRole, int(default) if str(default).isdigit() else 0)
                elif table_key == "tasks" and col_idx == 1:
                    item.setData(Qt.UserRole, float(default) if default else 0.0)
                table.setItem(row_index, col_idx, item)

        # Handle task-specific operations
        if table_key == "tasks":
            renumber_task_orders(table)

        # Restore table state
        table.blockSignals(False)
        table.setSortingEnabled(was_sorting)
        if was_sorting:
            table.sortByColumn(sort_col, sort_order)

        # Sync data
        parent._sync_data()
        logging.debug(f"Row inserted successfully at index {row_index}")

    except Exception as e:
        logging.error(f"Error in insert_row_with_id: {e}", exc_info=True)
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(parent, "Error", f"Failed to insert row: {e}")
    finally:
        table.blockSignals(False)
        table.setSortingEnabled(was_sorting)