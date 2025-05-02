from typing import List, Set, Dict, Any
from datetime import datetime
from models.frame import TimeFrame, Task


class DataValidator:
    @staticmethod
    def validate_time_frame(time_frame: TimeFrame, used_ids: Set[int]) -> List[str]:
        errors = []
        if time_frame.time_frame_id <= 0:
            errors.append("Time Frame ID must be positive")
        if time_frame.time_frame_id in used_ids:
            errors.append("Time Frame ID must be unique")
        try:
            datetime.strptime(time_frame.finish_date, "%Y-%m-%d")
        except ValueError:
            errors.append("Invalid date format")
        if time_frame.width_proportion <= 0:
            errors.append("Width proportion must be positive")
        return errors

    @staticmethod
    def validate_task(task: Task, used_ids: Set[int]) -> List[str]:
        errors = []
        if task.task_id <= 0:
            errors.append("Task ID must be positive")
        if task.task_id in used_ids:
            errors.append("Task ID must be unique")
        try:
            datetime.strptime(task.start_date, "%Y-%m-%d")
            datetime.strptime(task.finish_date, "%Y-%m-%d")
        except ValueError:
            errors.append("Invalid date format")
        if task.row_number <= 0:
            errors.append("Row number must be positive")
        if task.task_order <= 0:
            errors.append("Task order must be positive")
        return errors

    @staticmethod
    def validate_date_format(date_str: str) -> List[str]:
        errors = []
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            errors.append("Invalid date format (should be YYYY-MM-DD)")
        return errors

    @staticmethod
    def validate_positive_number(value: float, field_name: str) -> List[str]:
        errors = []
        if value <= 0:
            errors.append(f"{field_name} must be positive")
        return errors

    @staticmethod
    def validate_unique_id(id_value: int, used_ids: Set[int], entity_name: str) -> List[str]:
        errors = []
        if id_value in used_ids:
            errors.append(f"{entity_name} ID must be unique")
        return errors 

