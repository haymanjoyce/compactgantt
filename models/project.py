from typing import List, Dict, Any, Optional, Set
from models import FrameConfig, Task
from validators import DataValidator
import logging
from services.project_service import ProjectService
from services.task_service import TaskService
from config.app_config import AppConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProjectData:
    def __init__(self):
        app_config = AppConfig()
        self.frame_config = FrameConfig(num_rows=app_config.general.tasks_rows)
        self.tasks: List[Task] = []
        self.connectors: List[List[str]] = []
        self.swimlanes: List[List[str]] = []
        self.pipes: List[List[str]] = []
        self.curtains: List[List[str]] = []
        self.text_boxes: List[List[str]] = []
        self.validator = DataValidator()
        self.project_service = ProjectService()
        self.task_service = TaskService()

    def to_json(self) -> Dict[str, Any]:
        for t in self.tasks:
            assert hasattr(t, "__dict__"), f"Non-class instance in self.tasks: {t} ({type(t)})"
        return {
            "frame_config": vars(self.frame_config),
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
        frame_config_data = data.get("frame_config", {})
        # Convert margins list back to tuple (JSON converts tuples to lists)
        if "margins" in frame_config_data and isinstance(frame_config_data["margins"], list):
            frame_config_data["margins"] = tuple(frame_config_data["margins"])
        project.frame_config = FrameConfig(**frame_config_data)
        
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
