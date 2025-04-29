from PyQt5.QtWidgets import QTableWidgetItem, QMenu, QComboBox, QAction
from PyQt5.QtCore import Qt
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    logging.debug(f"Starting add_row for table_key: {table_key}, context: {context}")
    try:
        table_config = table_configs.get(table_key)
        if not table_config:
            logging.error(f"No table config found for key: {table_key}")
            return
        row_idx = table.rowCount()
        table.insertRow(row_idx)
        context = context or {}
        defaults = table_config.default_generator(row_idx, context)
        logging.debug(f"Generated defaults for row {row_idx}: {defaults}")
        for col_idx, default in enumerate(defaults):
            item = QTableWidgetItem(str(default))
            if table_key == "time_frames" and col_idx == 0:  # Make Time Frame ID read-only
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row_idx, col_idx, item)
        logging.debug(f"Row {row_idx} added successfully")
    except Exception as e:
        logging.error(f"Error in add_row: {e}", exc_info=True)
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
    was_sorting = table.isSortingEnabled()
    table.setSortingEnabled(False)
    table.blockSignals(True)
    table.insertRow(row_index)

    context = {}
    if config_key == "tasks":
        max_task_id = 0
        max_task_order = 0
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
        if isinstance(default, dict) and default.get("type") == "combo":
            combo = QComboBox()
            combo.addItems(default["items"])
            combo.setCurrentText(default["default"])
            table.setCellWidget(row_index, col_idx, combo)
        else:
            item = NumericTableWidgetItem(str(default)) if config_key == "tasks" and col_idx in (0,
                                                                                                 1) else QTableWidgetItem(
                str(default))
            if config_key == "tasks" and col_idx == 0:
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setData(Qt.UserRole, int(default))
            elif config_key == "tasks" and col_idx == 1:
                item.setData(Qt.UserRole, float(default))
            table.setItem(row_index, col_idx, item)

    if config_key == "tasks":
        renumber_task_orders(table)
    table.blockSignals(False)
    table.setSortingEnabled(was_sorting)
    if config_key == "tasks":
        table.sortByColumn(1, Qt.AscendingOrder)
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