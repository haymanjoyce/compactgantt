from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class Link:
    """Represents a dependency link between two tasks."""
    link_id: int
    from_task_id: int
    to_task_id: int
    line_color: str = "black"
    line_style: str = "solid"
    
    # Computed/derived fields (not stored, populated when needed)
    from_task_name: Optional[str] = None
    to_task_name: Optional[str] = None
    valid: Optional[str] = None  # "Yes" or "No" - calculated from task dates
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Link':
        """Create Link from dictionary (for JSON deserialization)."""
        return cls(
            link_id=int(data["link_id"]),
            from_task_id=int(data["from_task_id"]),
            to_task_id=int(data["to_task_id"]),
            line_color=data.get("line_color", "black"),
            line_style=data.get("line_style", "solid"),
            from_task_name=data.get("from_task_name"),  # May be None
            to_task_name=data.get("to_task_name"),      # May be None
            valid=None  # Never stored, always calculated
        )
    
    def to_dict(self, include_computed: bool = False) -> Dict[str, Any]:
        """Convert Link to dictionary (for JSON serialization)."""
        result = {
            "link_id": self.link_id,
            "from_task_id": self.from_task_id,
            "to_task_id": self.to_task_id,
            "line_color": self.line_color,
            "line_style": self.line_style
        }
        # Only include computed fields if explicitly requested (for debugging)
        if include_computed:
            if self.from_task_name:
                result["from_task_name"] = self.from_task_name
            if self.to_task_name:
                result["to_task_name"] = self.to_task_name
        return result

