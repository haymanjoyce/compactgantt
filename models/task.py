from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Task:
    task_id: int
    task_name: str
    start_date: str
    finish_date: str
    row_number: int
    is_milestone: bool = False
    label_placement: str = "Outside"
    label_hide: str = "Yes"
    label_alignment: str = "Centre"  # Default to Centre (always used for inside labels)
    label_horizontal_offset: float = 0.0
    label_text_colour: str = "black"
    fill_color: str = "blue"  # Fill color for task bar or milestone circle

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        # Don't auto-populate dates when loading from JSON
        # Auto-population should only happen in the UI when user enters data
        # This preserves invalid dates (empty strings) so they remain visible as empty fields
        start_date = data.get("start_date", "")
        finish_date = data.get("finish_date", "")
        
        # Removed auto-population logic - dates are loaded as-is from JSON
        
        return cls(
            task_id=data["task_id"],
            task_name=data["task_name"],
            start_date=start_date,
            finish_date=finish_date,
            row_number=data["row_number"],
            is_milestone=data.get("is_milestone", False),
            label_placement=data.get("label_placement", "Outside"),
            label_hide=data.get("label_hide", "Yes"),
            label_alignment=data.get("label_alignment", "Centre"),
            label_horizontal_offset=data.get("label_horizontal_offset", 0.0),
            label_text_colour=data.get("label_text_colour", "black"),
            fill_color=data.get("fill_color", "blue")
        ) 