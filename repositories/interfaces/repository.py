from abc import ABC, abstractmethod
from typing import Any

class ProjectRepository(ABC):
    @abstractmethod
    def load(self, file_path: str) -> Any:
        pass

    @abstractmethod
    def save(self, file_path: str, data: Any) -> None:
        pass
