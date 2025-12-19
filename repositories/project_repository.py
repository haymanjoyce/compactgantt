import json
from typing import Any, Type
from models.frame import FrameConfig
from models.task import Task
from repositories.interfaces.repository import ProjectRepository

class JsonProjectRepository(ProjectRepository):
    def load(self, file_path: str, project_data_cls: Type) -> Any:
        with open(file_path, "r") as f:
            data = json.load(f)
        return project_data_cls.from_json(data)

    def save(self, file_path: str, project_data: Any) -> None:
        with open(file_path, "w") as f:
            json.dump(project_data.to_json(), f, indent=4)
