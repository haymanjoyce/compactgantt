from repositories.project_repository import JsonProjectRepository
from validators.validators import DataValidator
from typing import List, Set
import logging
from models.time_frame import TimeFrame

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
            return [[str(tf.time_frame_id), tf.finish_date, str(tf.width_proportion * 100)]
                   for tf in sorted(project_data.time_frames, key=lambda x: x.time_frame_id)]
        return getattr(project_data, key, [])

    # Add more high-level project operations as needed
