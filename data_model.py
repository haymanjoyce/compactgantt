"""
Purpose: Manages Gantt chart data and layout structure, independent of UI or rendering logic.
Why: Centralizes data logic, making it reusable and easier to maintain/test.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import json

@dataclass
class FrameConfig:
    outer_width: float
    outer_height: float
    header_height: float
    footer_height: float
    margins: tuple[float, float, float, float]  # (top, right, bottom, left)
    num_rows: int
    header_text: str
    footer_text: str
    horizontal_gridlines: bool
    vertical_gridlines: bool
    chart_start_date: str  # YYYY-MM-DD

    @property
    def inner_height(self):
        from config import Config
        return (self.outer_height - self.header_height - self.footer_height -
                self.margins[0] - self.margins[2])

    def validate(self):
        assert self.outer_width > 0 and self.outer_height > 0
        assert 0 <= self.header_height < self.outer_height
        assert 0 <= self.footer_height < self.outer_height
        assert self.num_rows > 0 and isinstance(self.num_rows, int)
        assert self.inner_height > 0, "Inner height must be positive"
        assert isinstance(self.header_text, str) and isinstance(self.footer_text, str)
        assert isinstance(self.horizontal_gridlines, bool) and isinstance(self.vertical_gridlines, bool)
        datetime.strptime(self.chart_start_date, "%Y-%m-%d")

@dataclass
class TimeFrame:
    finish_date: str  # YYYY-MM-DD
    width_proportion: float  # 0.0 to 1.0

    def validate(self):
        try:
            datetime.strptime(self.finish_date, "%Y-%m-%d")
            assert 0 <= self.width_proportion <= 1.0
        except (ValueError, AssertionError) as e:
            raise ValueError(f"Invalid TimeFrame data: {e}")

@dataclass
class Task:
    task_id: int
    task_name: str
    start_date: str  # YYYY-MM-DD
    finish_date: str  # YYYY-MM-DD
    row_number: int

    def validate(self):
        try:
            assert self.task_id > 0 and isinstance(self.task_id, int)
            assert isinstance(self.task_name, str)
            datetime.strptime(self.start_date, "%Y-%m-%d")
            datetime.strptime(self.finish_date, "%Y-%m-%d")
            assert self.row_number > 0 and isinstance(self.row_number, int)
        except (ValueError, AssertionError):
            raise ValueError("Invalid Task data")

@dataclass
class Connector:
    from_task_id: int
    to_task_id: int

    def validate(self):
        assert self.from_task_id > 0 and isinstance(self.from_task_id, int)
        assert self.to_task_id > 0 and isinstance(self.to_task_id, int)

@dataclass
class Swimlane:
    from_row_number: int
    to_row_number: int
    title: str
    colour: str

    def validate(self):
        assert self.from_row_number > 0 and isinstance(self.from_row_number, int)
        assert self.to_row_number >= self.from_row_number and isinstance(self.to_row_number, int)
        assert isinstance(self.title, str)
        assert isinstance(self.colour, str)

@dataclass
class Pipe:
    date: str  # YYYY-MM-DD
    colour: str

    def validate(self):
        datetime.strptime(self.date, "%Y-%m-%d")
        assert isinstance(self.colour, str)

@dataclass
class Curtain:
    from_date: str  # YYYY-MM-DD
    to_date: str    # YYYY-MM-DD
    colour: str

    def validate(self):
        datetime.strptime(self.from_date, "%Y-%m-%d")
        datetime.strptime(self.to_date, "%Y-%m-%d")
        assert isinstance(self.colour, str)

@dataclass
class TextBox:
    text: str
    x_coordinate: float
    y_coordinate: float
    colour: str

    def validate(self):
        assert isinstance(self.text, str)
        assert isinstance(self.x_coordinate, (int, float))
        assert isinstance(self.y_coordinate, (int, float))
        assert isinstance(self.colour, str)

class ProjectData:
    def __init__(self):
        self.frame_config = FrameConfig(800, 600, 50, 50, (10, 10, 10, 10), 1, "", "", False, False, "2025-01-01")
        self.time_frames = []
        self.tasks = []
        self.connectors = []
        self.swimlanes = []
        self.pipes = []
        self.curtains = []
        self.text_boxes = []

    def add_time_frame(self, finish_date, width_proportion):
        tf = TimeFrame(finish_date, width_proportion)
        tf.validate()
        if sum(tf.width_proportion for tf in self.time_frames) + width_proportion > 1.0:
            raise ValueError("Total width proportion exceeds 1.0")
        self.time_frames.append(tf)

    def add_task(self, task_id, task_name, start_date, finish_date, row_number):
        task = Task(task_id, task_name, start_date, finish_date, row_number)
        task.validate()
        self.tasks.append(task)

    def add_connector(self, from_task_id, to_task_id):
        conn = Connector(from_task_id, to_task_id)
        conn.validate()
        self.connectors.append(conn)

    def add_swimlane(self, from_row_number, to_row_number, title, colour):
        sl = Swimlane(from_row_number, to_row_number, title, colour)
        sl.validate()
        self.swimlanes.append(sl)

    def add_pipe(self, date, colour):
        pipe = Pipe(date, colour)
        pipe.validate()
        self.pipes.append(pipe)

    def add_curtain(self, from_date, to_date, colour):
        curtain = Curtain(from_date, to_date, colour)
        curtain.validate()
        self.curtains.append(curtain)

    def add_text_box(self, text, x_coordinate, y_coordinate, colour):
        tb = TextBox(text, x_coordinate, y_coordinate, colour)
        tb.validate()
        self.text_boxes.append(tb)

    def to_json(self):
        return {
            "frame_config": {
                "outer_width": self.frame_config.outer_width,
                "outer_height": self.frame_config.outer_height,
                "header_height": self.frame_config.header_height,
                "footer_height": self.frame_config.footer_height,
                "margins": list(self.frame_config.margins),
                "num_rows": self.frame_config.num_rows,
                "header_text": self.frame_config.header_text,
                "footer_text": self.frame_config.footer_text,
                "horizontal_gridlines": self.frame_config.horizontal_gridlines,
                "vertical_gridlines": self.frame_config.vertical_gridlines,
                "chart_start_date": self.frame_config.chart_start_date
            },
            "time_frames": [
                {"finish_date": tf.finish_date, "width_proportion": tf.width_proportion}
                for tf in self.time_frames
            ],
            "tasks": [
                {"task_id": t.task_id, "task_name": t.task_name,
                 "start_date": t.start_date, "finish_date": t.finish_date,
                 "row_number": t.row_number}
                for t in self.tasks
            ],
            "connectors": [
                {"from_task_id": c.from_task_id, "to_task_id": c.to_task_id}
                for c in self.connectors
            ],
            "swimlanes": [
                {"from_row_number": s.from_row_number, "to_row_number": s.to_row_number,
                 "title": s.title, "colour": s.colour}
                for s in self.swimlanes
            ],
            "pipes": [
                {"date": p.date, "colour": p.colour}
                for p in self.pipes
            ],
            "curtains": [
                {"from_date": c.from_date, "to_date": c.to_date, "colour": c.colour}
                for c in self.curtains
            ],
            "text_boxes": [
                {"text": tb.text, "x_coordinate": tb.x_coordinate,
                 "y_coordinate": tb.y_coordinate, "colour": tb.colour}
                for tb in self.text_boxes
            ]
        }

    @classmethod
    def from_json(cls, data):
        instance = cls()
        margins = data["frame_config"]["margins"]
        if not (isinstance(margins, (list, tuple)) and len(margins) == 4 and all(isinstance(x, (int, float)) for x in margins)):
            raise ValueError("Margins must be a tuple of 4 floats")
        instance.frame_config = FrameConfig(
            data["frame_config"]["outer_width"], data["frame_config"]["outer_height"],
            data["frame_config"]["header_height"], data["frame_config"]["footer_height"],
            (float(margins[0]), float(margins[1]), float(margins[2]), float(margins[3])),
            data["frame_config"].get("num_rows", 1),
            data["frame_config"].get("header_text", ""),
            data["frame_config"].get("footer_text", ""),
            data["frame_config"].get("horizontal_gridlines", False),
            data["frame_config"].get("vertical_gridlines", False),
            data["frame_config"].get("chart_start_date", "2025-01-01")
        )
        instance.time_frames = [
            TimeFrame(tf["finish_date"], tf["width_proportion"])
            for tf in data.get("time_frames", [])
        ]
        instance.tasks = [
            Task(t["task_id"], t["task_name"], t["start_date"], t["finish_date"], t["row_number"])
            for t in data.get("tasks", [])
        ]
        instance.connectors = [
            Connector(c["from_task_id"], c["to_task_id"])
            for c in data.get("connectors", [])
        ]
        instance.swimlanes = [
            Swimlane(s["from_row_number"], s["to_row_number"], s["title"], s["colour"])
            for s in data.get("swimlanes", [])
        ]
        instance.pipes = [
            Pipe(p["date"], p["colour"])
            for p in data.get("pipes", [])
        ]
        instance.curtains = [
            Curtain(c["from_date"], c["to_date"], c["colour"])
            for c in data.get("curtains", [])
        ]
        instance.text_boxes = [
            TextBox(tb["text"], tb["x_coordinate"], tb["y_coordinate"], tb["colour"])
            for tb in data.get("text_boxes", [])
        ]
        return instance

    def get_table_data(self, table_type):
        if table_type == "time_frames":
            return [[tf.finish_date, str(tf.width_proportion * 100)]
                    for tf in self.time_frames]
        elif table_type == "tasks":
            return [[str(t.task_id), t.task_name, t.start_date, t.finish_date, str(t.row_number)]
                    for t in self.tasks]
        elif table_type == "connectors":
            return [[str(c.from_task_id), str(c.to_task_id)] for c in self.connectors]
        elif table_type == "swimlanes":
            return [[str(s.from_row_number), str(s.to_row_number), s.title, s.colour]
                    for s in self.swimlanes]
        elif table_type == "pipes":
            return [[p.date, p.colour] for p in self.pipes]
        elif table_type == "curtains":
            return [[c.from_date, c.to_date, c.colour] for c in self.curtains]
        elif table_type == "text_boxes":
            return [[tb.text, str(tb.x_coordinate), str(tb.y_coordinate), tb.colour]
                    for tb in self.text_boxes]
        return []

    def update_from_table(self, table_type, table_data):
        if table_type == "time_frames":
            self.time_frames.clear()
            for row in table_data:
                width = float(row[1] or 0) / 100
                self.add_time_frame(row[0] or "2025-01-01", width)
        elif table_type == "connectors":
            self.connectors.clear()
            for row in table_data:
                self.add_connector(int(row[0]), int(row[1]))
        elif table_type == "swimlanes":
            self.swimlanes.clear()
            for row in table_data:
                self.add_swimlane(int(row[0]), int(row[1]), row[2], row[3])
        elif table_type == "pipes":
            self.pipes.clear()
            for row in table_data:
                self.add_pipe(row[0], row[1])
        elif table_type == "curtains":
            self.curtains.clear()
            for row in table_data:
                self.add_curtain(row[0], row[1], row[2])
        elif table_type == "text_boxes":
            self.text_boxes.clear()
            for row in table_data:
                self.add_text_box(row[0], float(row[1]), float(row[2]), row[3])

