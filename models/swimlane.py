from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Swimlane:
    """Represents a horizontal swimlane spanning multiple rows.
    
    The swimlane's position (first_row/last_row) is determined by its order
    in the list and the row_count of preceding swimlanes.
    """
    swimlane_id: int
    row_count: int  # Number of rows the swimlane spans
    title: str = ""  # Optional label displayed in swimlane (renamed from 'name')
    label_position: str = "Bottom Right"  # Position: "Bottom Right", "Bottom Left", "Top Left", "Top Right"
    background_color: str = ""  # Optional background tint (empty = no background)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Swimlane':
        """Create Swimlane from dictionary (for JSON deserialization)."""
        return cls(
            swimlane_id=int(data["swimlane_id"]),
            row_count=int(data.get("row_count", 1)),
            title=data.get("title", ""),
            label_position=data.get("label_position", "Bottom Right"),
            background_color=data.get("background_color", ""),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Swimlane to dictionary (for JSON serialization)."""
        result = {
            "swimlane_id": self.swimlane_id,
            "row_count": self.row_count,
        }
        # Only save non-default values to reduce JSON size
        if self.title:
            result["title"] = self.title
        # Always save label_position to ensure it persists (even if default)
        result["label_position"] = self.label_position
        if self.background_color:
            result["background_color"] = self.background_color
        return result

