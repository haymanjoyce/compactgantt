"""
Purpose: Manages Gantt chart data (tasks, pipes, curtains) and handles data structure, independent of UI or rendering logic
Why: Centralizes data logic, making it reusable and easier to maintain/test.
"""


from datetime import datetime

class ProjectData:
    def __init__(self):
        self.tasks = []  # List of dicts: {"name": str, "start": str, "duration": float}
        self.pipes = []  # List of dicts: {"name": str, "date": str}
        self.curtains = []  # List of dicts: {"name": str, "start_date": str, "end_date": str, "color": str}

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

    def add_pipe(self, name, date):
        """Add a pipe with validation."""
        try:
            if date:
                datetime.strptime(date, "%Y-%m-%d")
            self.pipes.append({"name": name, "date": date})
        except ValueError as e:
            raise ValueError(f"Invalid pipe data: {e}")

    def add_curtain(self, name, start_date, end_date, color):
        """Add a curtain with date validation."""
        try:
            if start_date:
                datetime.strptime(start_date, "%Y-%m-%d")
            if end_date:
                datetime.strptime(end_date, "%Y-%m-%d")
            self.curtains.append({"name": name, "start_date": start_date, "end_date": end_date, "color": color or "gray"})
        except ValueError as e:
            raise ValueError(f"Invalid curtain data: {e}")

    def to_json(self):
        """Serialize data to JSON-compatible dict."""
        return {
            "tasks": self.tasks,
            "pipes": self.pipes,
            "curtains": self.curtains
        }

    @classmethod
    def from_json(cls, data):
        """Load data from JSON dict."""
        instance = cls()
        instance.tasks = data.get("tasks", [])
        instance.pipes = data.get("pipes", [])
        instance.curtains = data.get("curtains", [])
        for task in instance.tasks:
            if "start" in task and task["start"]:
                datetime.strptime(task["start"], "%Y-%m-%d")
            if "duration" in task and task["duration"]:
                float(task["duration"])
        for pipe in instance.pipes:
            if "date" in pipe and pipe["date"]:
                datetime.strptime(pipe["date"], "%Y-%m-%d")
        for curtain in instance.curtains:
            if "start_date" in curtain and curtain["start_date"]:
                datetime.strptime(curtain["start_date"], "%Y-%m-%d")
            if "end_date" in curtain and curtain["end_date"]:
                datetime.strptime(curtain["end_date"], "%Y-%m-%d")
        return instance

    def get_table_data(self, table_type):
        """Return data formatted for a specific table."""
        if table_type == "tasks":
            return [[t["name"], t["start"], str(t["duration"])] for t in self.tasks]
        elif table_type == "pipes":
            return [[p["name"], p["date"]] for p in self.pipes]
        elif table_type == "curtains":
            return [[c["name"], c["start_date"], c["end_date"], c["color"]] for c in self.curtains]
        return []

    def update_from_table(self, table_type, table_data):
        """Update data from table input."""
        if table_type == "tasks":
            self.tasks.clear()
            for row in table_data:
                self.add_task(row[0], row[1], row[2])
        elif table_type == "pipes":
            self.pipes.clear()
            for row in table_data:
                self.add_pipe(row[0], row[1])
        elif table_type == "curtains":
            self.curtains.clear()
            for row in table_data:
                self.add_curtain(row[0], row[1], row[2], row[3])