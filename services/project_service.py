from repositories.project_repository import JsonProjectRepository
from validators.validators import DataValidator
from typing import List, Set
import logging
from models.task import Task
from utils.conversion import safe_int, safe_float, display_to_internal_date, internal_to_display_date

class ProjectService:
    def __init__(self, repository=None):
        self.repository = repository or JsonProjectRepository()
        self.validator = DataValidator()

    def load_project(self, file_path, project_data_cls):
        return self.repository.load(file_path, project_data_cls)

    def save_project(self, file_path, project_data):
        self.repository.save(file_path, project_data)

    def validate_task(self, task, used_ids):
        return self.validator.validate_task(task, used_ids)

    def update_from_table(self, project_data, key: str, data: List[List[str]]) -> List[str]:
        errors = []
        try:
            if key == "tasks":
                new_tasks = []
                used_ids: Set[int] = set()
                for row_idx, row in enumerate(data, 1):
                    try:
                        # extract_table_data already skips checkbox column, so data is 0-indexed
                        # Column order: ID, Order, Row, Name, Start Date, Finish Date, Label, Placement
                        # Convert display format to internal format for dates
                        start_date_internal = display_to_internal_date(row[4])  # Start Date is at index 4
                        finish_date_internal = display_to_internal_date(row[5])  # Finish Date is at index 5
                        # Convert old placement values to new ones for backward compatibility
                        placement_value = row[7]  # Placement is at index 7
                        if placement_value in ["To left", "To right"]:
                            placement_value = "Outside"
                        task = Task(
                            task_id=safe_int(row[0]),  # ID is at index 0
                            task_order=safe_float(row[1]),  # Order is at index 1
                            row_number=safe_int(row[2], 1),  # Row is at index 2
                            task_name=row[3],  # Name is at index 3
                            start_date=start_date_internal,  # Store in internal format
                            finish_date=finish_date_internal,  # Store in internal format
                            label_hide=row[6],  # Label is at index 6 (No = Hide, Yes = Show)
                            label_placement=placement_value,  # Placement is at index 7
                            label_alignment="Centre",  # Always use Centre for inside labels (backward compatibility)
                            label_horizontal_offset=1.0,  # Default value (backward compatibility - now uses config value)
                            label_text_colour="black"  # Default color (backward compatibility - not used in rendering)
                        )
                        row_errors = self.validator.validate_task(task, used_ids)
                        if not row_errors:
                            new_tasks.append(task)
                            used_ids.add(task.task_id)
                        else:
                            errors.extend(f"Row {row_idx}: {err}" for err in row_errors)
                    except (ValueError, IndexError) as e:
                        errors.append(f"Row {row_idx}: {str(e)}")
                if not errors:
                    project_data.tasks = new_tasks
            else:
                setattr(project_data, key, data)
        except Exception as e:
            logging.error(f"Error in update_from_table: {e}", exc_info=True)
            errors.append(f"Internal error: {str(e)}")
        return errors

    def get_table_data(self, project_data, key: str) -> List[List[str]]:
        if key == "tasks":
            return [[str(t.task_id), str(t.task_order), str(t.row_number), t.task_name, 
                    internal_to_display_date(t.start_date),  # Convert to display format
                    internal_to_display_date(t.finish_date),  # Convert to display format
                    t.label_hide, t.label_placement]
                   for t in project_data.tasks]
        return getattr(project_data, key, [])

    # Add more high-level project operations as needed
