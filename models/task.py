from dataclasses import dataclass
from typing import Dict, Any, Optional
from utils.conversion import safe_int, safe_float


@dataclass
class Task:
    task_id: int
    task_name: str
    start_date: str
    finish_date: str
    row_number: int
    is_milestone: bool = False
    label_placement: str = "Outside"
    label_hide: str = "Yes"  # Deprecated: kept for backward compatibility, use label_content instead
    label_content: str = "Name only"  # Options: "None", "Name only", "Date only", "Name and Date"
    label_alignment: str = "Centre"  # Default to Centre (always used for inside labels)
    label_horizontal_offset: float = 0.0
    label_text_colour: str = "black"
    fill_color: str = "blue"  # Fill color for task bar or milestone circle
    date_format: Optional[str] = None  # Optional task-specific date format (e.g., "dd/MM/yyyy", "MM/dd/yyyy", etc.), None uses global format

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        # Don't auto-populate dates when loading from JSON
        # Auto-population should only happen in the UI when user enters data
        # This preserves invalid dates (empty strings) so they remain visible as empty fields
        start_date = data.get("start_date", "")
        finish_date = data.get("finish_date", "")
        
        # Removed auto-population logic - dates are loaded as-is from JSON
        
        # Backward compatibility: migrate label_hide to label_content
        label_content = data.get("label_content")
        if label_content is None:
            # Migrate from old label_hide field
            label_hide = data.get("label_hide", "Yes")
            if label_hide == "No":
                label_content = "None"
            else:
                label_content = "Name only"  # Default for old files
        else:
            label_content = label_content  # Use new field if present
        
        return cls(
            task_id=safe_int(data.get("task_id"), default=0),
            task_name=data.get("task_name", ""),
            start_date=start_date,
            finish_date=finish_date,
            row_number=safe_int(data.get("row_number"), default=0),
            is_milestone=data.get("is_milestone", False),
            label_placement=data.get("label_placement", "Outside"),
            label_hide=data.get("label_hide", "Yes"),  # Keep for backward compatibility
            label_content=label_content,
            label_alignment=data.get("label_alignment", "Centre"),
            label_horizontal_offset=safe_float(data.get("label_horizontal_offset"), default=0.0),
            label_text_colour=data.get("label_text_colour", "black"),
            fill_color=data.get("fill_color", "blue"),
            date_format=data.get("date_format")  # Optional task-specific date format
        ) 