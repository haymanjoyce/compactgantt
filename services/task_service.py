from typing import List, Set
from models.task import Task
from validators.validators import DataValidator

class TaskService:
    def __init__(self):
        self.validator = DataValidator()

    def add_task(self, project_data, task_id: int, task_name: str, start_date: str, 
                finish_date: str, row_number: int, is_milestone: bool = False, 
                label_placement: str = "Inside", label_hide: str = "Yes", 
                label_alignment: str = "Left", label_horizontal_offset: float = 1.0, 
                label_text_colour: str = "black", 
                task_order: float = 1.0) -> List[str]:
        """
        Add a new task to the project data.
        Returns a list of validation errors, if any.
        """
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
            label_text_colour=label_text_colour
        )
        used_ids = {t.task_id for t in project_data.tasks}
        errors = self.validator.validate_task(task, used_ids)
        if not errors:
            project_data.tasks.append(task)
        return errors

    def update_task_order(self, project_data, task_id: int, new_order: float) -> List[str]:
        """
        Update the order of a specific task.
        Returns a list of validation errors, if any.
        """
        errors = []
        if new_order <= 0:
            errors.append("Task order must be positive")
            return errors

        for task in project_data.tasks:
            if task.task_id == task_id:
                task.task_order = new_order
                break
        return errors

    def delete_task(self, project_data, task_id: int) -> List[str]:
        """
        Delete a task from the project data.
        Returns a list of errors, if any.
        """
        errors = []
        project_data.tasks = [t for t in project_data.tasks if t.task_id != task_id]
        return errors

    def get_task_by_id(self, project_data, task_id: int) -> Task:
        """
        Get a task by its ID.
        Returns None if not found.
        """
        for task in project_data.tasks:
            if task.task_id == task_id:
                return task
        return None

    def get_tasks_in_order(self, project_data) -> List[Task]:
        """
        Get all tasks sorted by task_order.
        """
        return sorted(project_data.tasks, key=lambda x: x.task_order)

    def validate_task_dates(self, start_date: str, finish_date: str) -> List[str]:
        """
        Validate task dates.
        Returns a list of validation errors, if any.
        """
        errors = []
        errors.extend(self.validator.validate_date_format(start_date))
        errors.extend(self.validator.validate_date_format(finish_date))
        return errors
