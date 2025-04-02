from datetime import datetime

class FrameConfig:
    def __init__(self, outer_width=800, outer_height=600, header_height=50, footer_height=50,
                 margins=(10, 10, 10, 10), num_rows=1, header_text="", footer_text="",
                 horizontal_gridlines=True, vertical_gridlines=True, chart_start_date="2025-01-01"):
        self.outer_width = outer_width
        self.outer_height = outer_height
        self.header_height = header_height
        self.footer_height = footer_height
        self.margins = margins
        self.num_rows = num_rows
        self.header_text = header_text
        self.footer_text = footer_text
        self.horizontal_gridlines = horizontal_gridlines
        self.vertical_gridlines = vertical_gridlines
        self.chart_start_date = chart_start_date

class Task:
    def __init__(self, task_id, task_name, start_date, finish_date, row_number, is_milestone=False):
        print(f"Task init: id={task_id}, name={task_name}, start={start_date}, finish={finish_date}, row={row_number}, milestone={is_milestone}")
        self.task_id = task_id
        self.task_name = task_name
        self.start_date = start_date
        self.finish_date = finish_date
        self.row_number = row_number
        self.is_milestone = is_milestone

class ProjectData:
    def __init__(self):
        self.frame_config = FrameConfig()
        self.time_frames = []
        self.tasks = []
        self.connectors = []
        self.swimlanes = []
        self.pipes = []
        self.curtains = []
        self.text_boxes = []

    def add_time_frame(self, finish_date, width_proportion):
        self.time_frames.append({"finish_date": finish_date, "width_proportion": width_proportion})

    def add_task(self, task_id, task_name, start_date, finish_date, row_number, is_milestone=False):
        print(f"add_task called: id={task_id}")
        task = Task(task_id, task_name, start_date, finish_date, row_number, is_milestone)
        self.tasks.append(task)
        print(f"Task {task_id} appended to tasks")

    def update_from_table(self, key, data):
        setattr(self, key, data)

    def get_table_data(self, key):
        if key == "tasks":
            return [[t.task_id, t.task_name, t.start_date, t.finish_date, str(t.row_number)] for t in self.tasks]
        return getattr(self, key, [])

    def to_json(self):
        return {
            "frame_config": vars(self.frame_config),
            "time_frames": self.time_frames,
            "tasks": [{"task_id": t.task_id, "task_name": t.task_name, "start_date": t.start_date,
                       "finish_date": t.finish_date, "row_number": t.row_number, "is_milestone": t.is_milestone}
                      for t in self.tasks],
            "connectors": self.connectors,
            "swimlanes": self.swimlanes,
            "pipes": self.pipes,
            "curtains": self.curtains,
            "text_boxes": self.text_boxes
        }

    @classmethod
    def from_json(cls, data):
        project = cls()
        project.frame_config = FrameConfig(**data.get("frame_config", {}))
        project.time_frames = data.get("time_frames", [])
        for task in data.get("tasks", []):
            project.add_task(task["task_id"], task["task_name"], task["start_date"],
                            task["finish_date"], task["row_number"], task.get("is_milestone", False))
        project.connectors = data.get("connectors", [])
        project.swimlanes = data.get("swimlanes", [])
        project.pipes = data.get("pipes", [])
        project.curtains = data.get("curtains", [])
        project.text_boxes = data.get("text_boxes", [])
        return project