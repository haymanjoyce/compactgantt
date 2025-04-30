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
        was_sorting = table.isSortingEnabled()
        sort_col = table.horizontalHeader().sortIndicatorSection()
        sort_order = table.horizontalHeader().sortIndicatorOrder()

        table.setSortingEnabled(False)
        table.blockSignals(True)
        # Disconnect itemChanged to prevent premature _sync_data
        if table_key == "tasks":
            try:
                table.itemChanged.disconnect()
                logging.debug("Disconnected itemChanged signal")
            except Exception:
                logging.debug("No itemChanged connection to disconnect")

        table_config = table_configs.get(table_key)
        print("table_config:", table_config)
        if not table_config:
            logging.error(f"No table config found for key: {table_key}")
            table.blockSignals(False)
            table.setSortingEnabled(was_sorting)
            return
        row_idx = table.rowCount()
        table.insertRow(row_idx)

        context = context or {}
        if table_key == "tasks":
            max_task_id = 0
            max_task_order = 0
            for row in range(table.rowCount() - 1):
                item_id = table.item(row, 0)
                item_order = table.item(row, 1)
                if item_id and item_id.text().isdigit():
                    max_task_id = max(max_task_id, int(item_id.text()))
                if item_order:
                    try:
                        max_task_order = max(max_task_order, float(item_order.text()))
                    except ValueError:
                        pass
                context["max_task_id"] = max_task_id
                context["max_task_order"] = max_task_order

        defaults = table_config.default_generator(row_idx, context)
        print("defaults:", defaults)
        for col_idx, default in enumerate(defaults):
            col_config = table_config.columns[col_idx]
            if col_config.widget_type == "combo":
                combo = QComboBox()
                combo.addItems(col_config.combo_items)
                combo.setCurrentText(str(default) or col_config.combo_items[0])
                table.setCellWidget(row_idx, col_idx, combo)
                logging.debug(f"Set QComboBox for row {row_idx}, col {col_idx} with value {combo.currentText()}")
            else:
                item = NumericTableWidgetItem(str(default)) if col_idx in (0, 1) else QTableWidgetItem(str(default))
                if table_key == "time_frames" and col_idx == 0:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if table_key == "tasks" and col_idx == 0:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    item.setData(Qt.UserRole, int(default) if str(default).isdigit() else 0)
                elif table_key == "tasks" and col_idx == 1:
                    item.setData(Qt.UserRole, float(default) if default else 0.0)
                table.setItem(row_idx, col_idx, item)
        print("add_row: row added successfully")

        if table_key == "tasks":
            renumber_task_orders(table)

        logging.debug("Table state after adding row:")
        for col_idx in range(table.columnCount()):
            widget = table.cellWidget(row_idx, col_idx)
            item = table.item(row_idx, col_idx)
            logging.debug(f"Row {row_idx}, Col {col_idx}: Widget={type(widget).__name__ if widget else None}, Item={item.text() if item else None}")

        table.blockSignals(False)

        # Reconnect itemChanged
        if table_key == "tasks":
            table.itemChanged.connect(parent._sync_data_if_not_initializing)
            logging.debug("Reconnected itemChanged signal")

        parent._sync_data_if_not_initializing()

        table.setSortingEnabled(was_sorting)
        if was_sorting:
            table.sortByColumn(sort_col, sort_order)

        logging.debug("Table state after sorting:")
        for col_idx in range(table.columnCount()):
            widget = table.cellWidget(row_idx, col_idx)
            item = table.item(row_idx, col_idx)
            logging.debug(f"Row {row_idx}, Col {col_idx}: Widget={type(widget).__name__ if widget else None}, Item={item.text() if item else None}")
    except Exception as e:
        print("add_row exception:", e)
        logging.error(f"Error in add_row: {e}", exc_info=True)
        table.blockSignals(False)
        table.setSortingEnabled(was_sorting)
        raise

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
        add_action.triggered.connect(lambda: add_row(table, table_key, table_configs, parent))
        remove_action.triggered.connect(lambda: remove_row(table, table_key, table_configs, parent))
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


def insert_row(table, config_key, table_configs, tab, row_index):
    config = table_configs.get(config_key, None)
    if not config:
        return

    # Save current sort state
    was_sorting = table.isSortingEnabled()
    sort_col = table.horizontalHeader().sortIndicatorSection()
    sort_order = table.horizontalHeader().sortIndicatorOrder()

    table.setSortingEnabled(False)
    table.blockSignals(True)
    table.insertRow(row_index)

    context = {}
    if config_key == "tasks":
        max_task_id = 0
        max_task_order = 0
        # Always iterate over the underlying data, not the sorted view
        for row in range(table.rowCount()):
            if row != row_index:
                item_id = table.item(row, 0)
                item_order = table.item(row, 1)
                if item_id and item_id.text().isdigit():
                    max_task_id = max(max_task_id, int(item_id.text()))
                if item_order:
                    try:
                        max_task_order = max(max_task_order, float(item_order.text()))
                    except ValueError:
                        pass
        context = {"max_task_id": max_task_id, "max_task_order": max_task_order}

    defaults = config.default_generator(row_index, context)
    for col_idx, default in enumerate(defaults):
        col_config = config.columns[col_idx]
        if col_config.widget_type == "combo":
            combo = QComboBox()
            combo.addItems(col_config.combo_items)
            combo.setCurrentText(str(default))
            table.setCellWidget(row_index, col_idx, combo)
        else:
            item = NumericTableWidgetItem(str(default)) if config_key == "tasks" and col_idx in (0, 1) else QTableWidgetItem(str(default))
            if config_key == "tasks" and col_idx == 0:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setData(Qt.UserRole, int(default))
            elif config_key == "tasks" and col_idx == 1:
                item.setData(Qt.UserRole, float(default))
            table.setItem(row_index, col_idx, item)

    if config_key == "tasks":
        renumber_task_orders(table)
    table.blockSignals(False)

    # Restore sorting and reapply previous sort state
    table.setSortingEnabled(was_sorting)
    if was_sorting:
        table.sortByColumn(sort_col, sort_order)
    if config_key == "tasks":
        tab._sync_data_if_not_initializing()


def delete_row(table, config_key, table_configs, tab, row_index):
    config = table_configs.get(config_key, None)
    if not config:
        return
    if table.rowCount() > config.min_rows:
        table.removeRow(row_index)
        if config_key == "tasks":
            renumber_task_orders(table)
        tab._sync_data_if_not_initializing()