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
        # Normalize dates: if only one date is provided, auto-populate the other (milestone behavior)
        start_date = data.get("start_date", "")
        finish_date = data.get("finish_date", "")
        
        # Auto-populate missing date field for milestones (if only one date is provided)
        if start_date and not finish_date:
            finish_date = start_date  # Auto-populate finish date
        elif finish_date and not start_date:
            start_date = finish_date  # Auto-populate start date
        
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