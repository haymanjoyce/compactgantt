from repositories.project_repository import JsonProjectRepository
from validators.validators import DataValidator
from typing import List, Set
import logging
from models.time_frame import TimeFrame
from models.task import Task
from utils.conversion import safe_int, safe_float

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
                        finish_date = row[1]
                        width_proportion = float(row[2]) / 100
                        tf = TimeFrame(
                            time_frame_id=time_frame_id,
                            finish_date=finish_date,
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
                        task = Task(
                            task_id=safe_int(row[0]),
                            task_order=safe_float(row[1]),
                            task_name=row[2],
                            start_date=row[3],
                            finish_date=row[4],
                            row_number=safe_int(row[5], 1),
                            label_placement=row[6],
                            label_hide=row[7],
                            label_alignment=row[8],
                            label_horizontal_offset=safe_float(row[9], 1.0),
                            label_vertical_offset=safe_float(row[10], 0.5),
                            label_text_colour=row[11]
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
            return [[str(t.task_id), str(t.task_order), t.task_name, t.start_date, t.finish_date,
                    str(t.row_number), t.label_placement, t.label_hide, t.label_alignment,
                    str(t.label_horizontal_offset), str(t.label_vertical_offset), t.label_text_colour]
                   for t in project_data.tasks]
        elif key == "time_frames":
            print("DEBUG: project_data.time_frames =", project_data.time_frames)
            return [[str(tf.time_frame_id), tf.finish_date, str(tf.width_proportion * 100)]
                   for tf in sorted(project_data.time_frames, key=lambda x: x.time_frame_id)]
        return getattr(project_data, key, [])

    # Add more high-level project operations as needed
