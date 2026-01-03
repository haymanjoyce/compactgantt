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
    name: str = ""  # Optional label displayed in bottom-right corner
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Swimlane':
        """Create Swimlane from dictionary (for JSON deserialization)."""
        # Backward compatibility: support old first_row/last_row format
        if "first_row" in data and "last_row" in data:
            first_row = int(data["first_row"])
            last_row = int(data["last_row"])
            row_count = last_row - first_row + 1
        else:
            row_count = int(data.get("row_count", 1))
        return cls(
            swimlane_id=int(data["swimlane_id"]),
            row_count=row_count,
            name=data.get("name", "")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Swimlane to dictionary (for JSON serialization)."""
        result = {
            "swimlane_id": self.swimlane_id,
            "row_count": self.row_count,
        }
        # Only save non-default values to reduce JSON size
        if self.name:
            result["name"] = self.name
        return result

