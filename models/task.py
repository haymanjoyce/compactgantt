from dataclasses import dataclass
from typing import Dict, Any, Optional
from config.date_config import DateConfig
from utils.conversion import safe_int, safe_float, is_valid_internal_date, display_to_internal_date


def _date_to_internal(date_str: str, date_config: Optional[DateConfig] = None) -> str:
    """Convert date to internal format (yyyy-mm-dd). If already internal or empty, return as-is."""
    if not date_str or not date_str.strip():
        return date_str
    if is_valid_internal_date(date_str):
        return date_str
    config = date_config or DateConfig()
    try:
        return display_to_internal_date(date_str.strip(), config)
    except ValueError:
        return date_str


@dataclass
class Task:
    task_id: int
    task_name: str
    start_date: str
    finish_date: str
    swimlane_row: int
    swimlane_id: int = 0
    is_milestone: bool = False
    label_placement: str = "Inside"
    label_hide: str = "Yes"  # Deprecated: kept for backward compatibility, use label_content instead
    label_content: str = "Name only"  # Options: "None", "Name only", "Date only", "Name and Date"
    label_alignment: str = "Centre"  # Default to Centre (always used for inside labels)
    label_horizontal_offset: float = 0.0
    label_text_colour: str = "black"
    fill_color: str = "blue"  # Fill color for task bar or milestone circle
    date_format: Optional[str] = None  # Optional task-specific date format (e.g., "dd/MM/yyyy", "MM/dd/yyyy", etc.), None uses global format

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        # Load dates and convert to internal format (yyyy-mm-dd) when in display format
        # so validation and chart logic work consistently
        start_date = _date_to_internal(data.get("start_date", ""))
        finish_date = _date_to_internal(data.get("finish_date", ""))
        
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
            swimlane_row=safe_int(data.get("swimlane_row"), default=1),
            swimlane_id=safe_int(data.get("swimlane_id"), default=0),
            is_milestone=data.get("is_milestone", False),
            label_placement=data.get("label_placement", "Inside"),
            label_hide=data.get("label_hide", "Yes"),  # Keep for backward compatibility
            label_content=label_content,
            label_alignment=data.get("label_alignment", "Centre"),
            label_horizontal_offset=safe_float(data.get("label_horizontal_offset"), default=0.0),
            label_text_colour=data.get("label_text_colour", "black"),
            fill_color=data.get("fill_color", "blue"),
            date_format=data.get("date_format")  # Optional task-specific date format
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert Task to dictionary (for JSON serialization)."""
        result: Dict[str, Any] = {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "start_date": self.start_date,
            "finish_date": self.finish_date,
            "swimlane_row": self.swimlane_row,
            "swimlane_id": self.swimlane_id,
            "label_placement": self.label_placement,
            "label_hide": self.label_hide,  # Keep for backward compatibility
            "label_content": self.label_content,
        }
        # Only save non-default optional values to reduce JSON size
        if self.is_milestone:
            result["is_milestone"] = True
        if self.label_alignment != "Centre":
            result["label_alignment"] = self.label_alignment
        if self.label_horizontal_offset != 0.0:
            result["label_horizontal_offset"] = self.label_horizontal_offset
        if self.label_text_colour != "black":
            result["label_text_colour"] = self.label_text_colour
        if self.fill_color != "blue":
            result["fill_color"] = self.fill_color
        if self.date_format:
            result["date_format"] = self.date_format
        return result