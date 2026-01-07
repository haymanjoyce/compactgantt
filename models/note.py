from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class Note:
    """Represents a note that can be positioned anywhere on the chart."""
    note_id: int
    x: int  # X coordinate relative to chart area origin (pixels)
    y: int  # Y coordinate relative to chart area origin (pixels)
    width: int  # Width of note (pixels)
    height: int  # Height of note (pixels)
    text: str = ""  # Text content (supports wrapping)
    text_align: str = "Center"  # Horizontal text alignment: Left, Center, Right
    vertical_align: str = "Middle"  # Vertical text alignment: Top, Middle, Bottom
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Note':
        """Create Note from dictionary (for JSON deserialization)."""
        # Backward compatibility: support old list format
        if isinstance(data, list):
            # Old format: [Text, X, Y, Color] - convert to dict format
            if len(data) >= 3:
                return cls(
                    note_id=0,  # No ID in old format
                    x=int(float(data[1])) if data[1] else 0,  # Convert float to int for backward compatibility
                    y=int(float(data[2])) if data[2] else 0,  # Convert float to int for backward compatibility
                    width=100,  # Default width
                    height=50,  # Default height
                    text=str(data[0]) if data[0] else ""
                )
            else:
                return cls(note_id=0, x=0, y=0, width=100, height=50, text="")
        
        # Support both old "textbox_id" and new "note_id" field names
        note_id = data.get("note_id", data.get("textbox_id", 0))
        
        return cls(
            note_id=int(note_id),
            x=int(data.get("x", 0)),
            y=int(data.get("y", 0)),
            width=int(data.get("width", 100)),
            height=int(data.get("height", 50)),
            text=data.get("text", ""),
            text_align=data.get("text_align", "Center"),
            vertical_align=data.get("vertical_align", "Middle")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Note to dictionary (for JSON serialization)."""
        result = {
            "note_id": self.note_id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }
        # Only save non-default values to reduce JSON size
        if self.text:
            result["text"] = self.text
        if self.text_align != "Center":
            result["text_align"] = self.text_align
        if self.vertical_align != "Middle":
            result["vertical_align"] = self.vertical_align
        return result

