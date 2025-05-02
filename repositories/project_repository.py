import json
from typing import Any
from models.frame import FrameConfig
from models.time_frame import TimeFrame
from models.task import Task
from repositories.interfaces.repository import ProjectRepository
from data_model import ProjectData

class JsonProjectRepository(ProjectRepository):
    def load(self, file_path: str) -> ProjectData:
        with open(file_path, "r") as f:
            data = json.load(f)
        return ProjectData.from_json(data)

    def save(self, file_path: str, project_data: ProjectData) -> None:
        with open(file_path, "w") as f:
            json.dump(project_data.to_json(), f, indent=4)
