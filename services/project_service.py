from models.frame import FrameConfig
from models.time_frame import TimeFrame
from models.task import Task
from repositories.project_repository import JsonProjectRepository
from validators.validators import DataValidator

class ProjectService:
    def __init__(self, repository=None):
        self.repository = repository or JsonProjectRepository()
        self.validator = DataValidator()

    def load_project(self, file_path):
        return self.repository.load(file_path)

    def save_project(self, file_path, project_data):
        self.repository.save(file_path, project_data)

    def validate_time_frame(self, time_frame, used_ids):
        return self.validator.validate_time_frame(time_frame, used_ids)

    def validate_task(self, task, used_ids):
        return self.validator.validate_task(task, used_ids)

    # Add more high-level project operations as needed
