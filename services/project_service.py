from repositories.project_repository import JsonProjectRepository
from validators.validators import DataValidator
from typing import List, Set
import logging
from models.time_frame import TimeFrame
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

    def validate_time_frame(self, time_frame, used_ids):
        return self.validator.validate_time_frame(time_frame, used_ids)

    def validate_task(self, task, used_ids):
        return self.validator.validate_task(task, used_ids)

    def update_from_table(self, project_data, key: str, data: List[List[str]]) -> List[str]:
        errors = []
        try:
            if key == "time_frames":
                new_time_frames = []
                used_ids: Set[int] = set()
                for row_idx, row in enumerate(data, 1):
                    try:
                        time_frame_id = int(row[0])
                        finish_date_display = row[1]
                        # Convert display format to internal format
                        finish_date_internal = display_to_internal_date(finish_date_display)
                        width_proportion = float(row[2]) / 100
                        tf = TimeFrame(
                            time_frame_id=time_frame_id,
                            finish_date=finish_date_internal,  # Store in internal format
                            width_proportion=width_proportion
                        )
                        row_errors = self.validator.validate_time_frame(tf, used_ids)
                        if not row_errors:
                            new_time_frames.append(tf)
                            used_ids.add(tf.time_frame_id)
                        else:
                            errors.extend(f"Row {row_idx}: {err}" for err in row_errors)
                    except (ValueError, IndexError) as e:
                        errors.append(f"Row {row_idx}: {str(e)}")
                if not errors:
                    project_data.time_frames = sorted(new_time_frames, key=lambda x: x.time_frame_id)
            elif key == "tasks":
                new_tasks = []
                used_ids: Set[int] = set()
                for row_idx, row in enumerate(data, 1):
                    try:
                        # extract_table_data already skips checkbox column, so data is 0-indexed
                        # Column order: ID, Order, Row, Name, Start Date, Finish Date, Label, Label Placement, Label Alignment, Horiz Offset, Label Colour
                        # Convert display format to internal format for dates
                        start_date_internal = display_to_internal_date(row[4])  # Start Date is at index 4
                        finish_date_internal = display_to_internal_date(row[5])  # Finish Date is at index 5
                        task = Task(
                            task_id=safe_int(row[0]),  # ID is at index 0
                            task_order=safe_float(row[1]),  # Order is at index 1
                            row_number=safe_int(row[2], 1),  # Row is at index 2
                            task_name=row[3],  # Name is at index 3
                            start_date=start_date_internal,  # Store in internal format
                            finish_date=finish_date_internal,  # Store in internal format
                            label_hide=row[6],  # Label is at index 6 (No = Hide, Yes = Show)
                            label_placement=row[7],  # Label Placement is at index 7
                            label_alignment=row[8],  # Label Alignment is at index 8
                            label_horizontal_offset=safe_float(row[9], 1.0),  # Horiz Offset is at index 9
                            label_text_colour=row[10]  # Label Colour is at index 10
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
                    t.label_hide, t.label_placement, t.label_alignment,
                    str(t.label_horizontal_offset), t.label_text_colour]
                   for t in project_data.tasks]
        elif key == "time_frames":
            print("DEBUG: project_data.time_frames =", project_data.time_frames)
            return [[str(tf.time_frame_id), 
                    internal_to_display_date(tf.finish_date),  # Convert to display format
                    str(tf.width_proportion * 100)]
                   for tf in sorted(project_data.time_frames, key=lambda x: x.time_frame_id)]
        return getattr(project_data, key, [])

    # Add more high-level project operations as needed
