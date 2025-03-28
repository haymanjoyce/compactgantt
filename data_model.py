"""
Purpose: Manages Gantt chart data and layout structure, independent of UI or rendering logic.
Why: Centralizes data logic, making it reusable and easier to maintain/test.
"""

from dataclasses import dataclass
from datetime import datetime
import json  # Kept for JSON serialization intent; used implicitly by to_json/from_json

@dataclass
class TimeFrame:
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    width_proportion: float  # 0.0 to 1.0, fraction of inner_frame width
    magnification: float     # e.g., 1.0 for normal, 0.5 for half-scale

    def validate(self):
        try:
            datetime.strptime(self.start_date, "%Y-%m-%d")
            datetime.strptime(self.end_date, "%Y-%m-%d")
            assert 0 <= self.width_proportion <= 1.0
            assert self.magnification > 0
        except (ValueError, AssertionError):
            raise ValueError("Invalid TimeFrame data")

@dataclass
class FrameConfig:
    outer_width: float   # Total width in pixels
    outer_height: float  # Total height in pixels
    header_height: float # Height of header_frame
    footer_height: float # Height of footer_frame
    margins: tuple[float, float, float, float]  # (top, right, bottom, left)

    @property
    def inner_height(self):
        return self.outer_height - self.header_height - self.footer_height - self.margins[0] - self.margins[2]

    def validate(self):
        assert self.outer_width > 0 and self.outer_height > 0
        assert 0 <= self.header_height < self.outer_height
        assert 0 <= self.footer_height < self.outer_height
        assert self.inner_height > 0

class ProjectData:
    def __init__(self):
        self.frame_config = FrameConfig(outer_width=800, outer_height=600, header_height=50, footer_height=50, margins=(10, 10, 10, 10))
        self.time_frames = []  # List of TimeFrame objects
        self.tasks = []  # List of dicts: {"name": str, "start": str, "duration": float}

    def add_time_frame(self, start_date, end_date, width_proportion, magnification=1.0):
        """Add a time frame with validation."""
        tf = TimeFrame(start_date, end_date, width_proportion, magnification)
        tf.validate()
        total_width = sum(tf.width_proportion for tf in self.time_frames) + width_proportion
        if total_width > 1.0:
            raise ValueError("Total width proportion exceeds 1.0")
        self.time_frames.append(tf)

    def add_task(self, name, start_date, duration):
        """Add a task with validation."""
        try:
            if start_date:
                datetime.strptime(start_date, "%Y-%m-%d")
            if duration:
                float(duration)
            self.tasks.append({"name": name, "start": start_date, "duration": float(duration) if duration else 0})
        except ValueError as e:
            raise ValueError(f"Invalid task data: {e}")

    def to_json(self):
        """Serialize data to JSON-compatible dict."""
        return {
            "frame_config": {
                "outer_width": self.frame_config.outer_width,
                "outer_height": self.frame_config.outer_height,
                "header_height": self.frame_config.header_height,
                "footer_height": self.frame_config.footer_height,
                "margins": list(self.frame_config.margins)  # Convert tuple to list for JSON
            },
            "time_frames": [
                {"start_date": tf.start_date, "end_date": tf.end_date,
                 "width_proportion": tf.width_proportion, "magnification": tf.magnification}
                for tf in self.time_frames
            ],
            "tasks": self.tasks
        }

    @classmethod
    def from_json(cls, data):
        """Load data from JSON dict."""
        instance = cls()
        margins = data["frame_config"]["margins"]
        if not (isinstance(margins, (list, tuple)) and len(margins) == 4 and all(isinstance(x, (int, float)) for x in margins)):
            raise ValueError("Margins must be a tuple of 4 floats")
        instance.frame_config = FrameConfig(
            data["frame_config"]["outer_width"], data["frame_config"]["outer_height"],
            data["frame_config"]["header_height"], data["frame_config"]["footer_height"],
            (float(margins[0]), float(margins[1]), float(margins[2]), float(margins[3]))  # Explicitly cast to satisfy type hint
        )
        instance.time_frames = [
            TimeFrame(tf["start_date"], tf["end_date"], tf["width_proportion"], tf["magnification"])
            for tf in data.get("time_frames", [])
        ]
        instance.tasks = data.get("tasks", [])
        for task in instance.tasks:
            if "start" in task and task["start"]:
                datetime.strptime(task["start"], "%Y-%m-%d")
            if "duration" in task and task["duration"]:
                float(task["duration"])
        return instance

    def get_table_data(self, table_type):
        """Return data formatted for a specific table."""
        if table_type == "tasks":
            return [[t["name"], t["start"], str(t["duration"])] for t in self.tasks]
        return []

    def update_from_table(self, table_type, table_data):
        """Update data from table input."""
        if table_type == "tasks":
            self.tasks.clear()
            for row in table_data:
                self.add_task(row[0], row[1], row[2])