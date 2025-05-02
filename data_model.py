from typing import List, Dict, Any, Optional, Set
from models import FrameConfig, TimeFrame, Task
from validators import DataValidator
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProjectData:
    def __init__(self):
        self.frame_config: FrameConfig = FrameConfig()
        self.time_frames: List[TimeFrame] = []
        self.tasks: List[Task] = []
        self.connectors: List[List[str]] = []
        self.swimlanes: List[List[str]] = []
        self.pipes: List[List[str]] = []
        self.curtains: List[List[str]] = []
        self.text_boxes: List[List[str]] = []
        self.validator = DataValidator()

    def add_time_frame(self, time_frame_id: int, finish_date: str, width_proportion: float) -> List[str]:
        time_frame = TimeFrame(time_frame_id, finish_date, width_proportion)
        used_ids = {tf.time_frame_id for tf in self.time_frames}
        errors = self.validator.validate_time_frame(time_frame, used_ids)
        if not errors:
            self.time_frames.append(time_frame)
            self.time_frames.sort(key=lambda x: x.time_frame_id)
        return errors

    def add_task(self, task_id: int, task_name: str, start_date: str, finish_date: str, 
                row_number: int, is_milestone: bool = False, label_placement: str = "Inside",
                label_hide: str = "No", label_alignment: str = "Left",
                label_horizontal_offset: float = 1.0, label_vertical_offset: float = 0.5,
                label_text_colour: str = "black", task_order: float = 1.0) -> List[str]:
        task = Task(
            task_id=task_id,
            task_order=task_order,
            task_name=task_name,
            start_date=start_date,
            finish_date=finish_date,
            row_number=row_number,
            is_milestone=is_milestone,
            label_placement=label_placement,
            label_hide=label_hide,
            label_alignment=label_alignment,
            label_horizontal_offset=label_horizontal_offset,
            label_vertical_offset=label_vertical_offset,
            label_text_colour=label_text_colour
        )
        used_ids = {t.task_id for t in self.tasks}
        errors = self.validator.validate_task(task, used_ids)
        if not errors:
            self.tasks.append(task)
        return errors

    def update_from_table(self, key: str, data: List[List[str]]) -> List[str]:
        errors = []
        try:
            if key == "time_frames":
                new_time_frames = []
                used_ids: Set[int] = set()
                for row_idx, row in enumerate(data, 1):
                    try:
                        # The order in the table is: Time Frame ID, Finish Date, Width (%)
                        time_frame_id = int(row[0])  # First column
                        finish_date = row[1]         # Second column
                        width_proportion = float(row[2]) / 100  # Third column
                        
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
                    self.time_frames = sorted(new_time_frames, key=lambda x: x.time_frame_id)
            else:
                setattr(self, key, data)
        except Exception as e:
            logging.error(f"Error in update_from_table: {e}", exc_info=True)
            errors.append(f"Internal error: {str(e)}")
        return errors

    def get_table_data(self, key: str) -> List[List[str]]:
        if key == "tasks":
            return [[str(t.task_id), str(t.task_order), t.task_name, t.start_date, t.finish_date,
                    str(t.row_number), t.label_placement, t.label_hide, t.label_alignment,
                    str(t.label_horizontal_offset), str(t.label_vertical_offset), t.label_text_colour]
                   for t in self.tasks]
        elif key == "time_frames":
            return [[str(tf.time_frame_id), tf.finish_date, str(tf.width_proportion * 100)]
                   for tf in sorted(self.time_frames, key=lambda x: x.time_frame_id)]
        return getattr(self, key, [])

    def to_json(self) -> Dict[str, Any]:
        return {
            "frame_config": vars(self.frame_config),
            "time_frames": [tf.to_dict() for tf in sorted(self.time_frames, key=lambda x: x.time_frame_id)],
            "tasks": [vars(task) for task in self.tasks],
            "connectors": self.connectors,
            "swimlanes": self.swimlanes,
            "pipes": self.pipes,
            "curtains": self.curtains,
            "text_boxes": self.text_boxes
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'ProjectData':
        project = cls()
        project.frame_config = FrameConfig(**data.get("frame_config", {}))
        
        # Load time frames
        for tf_data in data.get("time_frames", []):
            project.time_frames.append(TimeFrame.from_dict(tf_data))
        
        # Load tasks
        for task_data in data.get("tasks", []):
            project.tasks.append(Task.from_dict(task_data))
        
        # Load other data
        project.connectors = data.get("connectors", [])
        project.swimlanes = data.get("swimlanes", [])
        project.pipes = data.get("pipes", [])
        project.curtains = data.get("curtains", [])
        project.text_boxes = data.get("text_boxes", [])
        
        return project