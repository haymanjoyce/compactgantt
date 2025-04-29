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
    def __init__(self, task_id, task_name, start_date, finish_date, row_number, is_milestone=False,
                 label_placement="Inside", label_hide="No", label_alignment="Left",
                 label_horizontal_offset=1.0, label_vertical_offset=0.5, label_text_colour="black", task_order=1.0):
        self.task_id = task_id
        self.task_order = task_order
        self.task_name = task_name
        self.start_date = start_date
        self.finish_date = finish_date
        self.row_number = row_number
        self.is_milestone = is_milestone
        self.label_placement = label_placement
        self.label_hide = label_hide
        self.label_alignment = label_alignment
        self.label_horizontal_offset = label_horizontal_offset
        self.label_vertical_offset = label_vertical_offset
        self.label_text_colour = label_text_colour

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

    def add_time_frame(self, time_frame_id, finish_date, width_proportion):
        self.time_frames.append({
            "time_frame_id": time_frame_id,
            "finish_date": finish_date,
            "width_proportion": width_proportion
        })

    def add_task(self, task_id, task_name, start_date, finish_date, row_number, is_milestone=False,
                 label_placement="Inside", label_hide="No", label_alignment="Left",
                 label_horizontal_offset=1.0, label_vertical_offset=0.5, label_text_colour="black", task_order=1.0):
        self.tasks.append(Task(task_id, task_name, start_date, finish_date, row_number, is_milestone,
                              label_placement, label_hide, label_alignment,
                              label_horizontal_offset, label_vertical_offset, label_text_colour, task_order))

    def update_from_table(self, key, data):
        if key == "connectors":
            valid_connectors = []
            task_ids = {task.task_id for task in self.tasks}
            for row in data:
                try:
                    from_id, to_id = int(row[0]), int(row[1])
                    if from_id > 0 and to_id > 0 and from_id in task_ids and to_id in task_ids and from_id != to_id:
                        valid_connectors.append(row)
                except (ValueError, TypeError):
                    pass
            setattr(self, key, valid_connectors)
        elif key == "time_frames":
            # Preserve existing time_frame_id where possible
            new_time_frames = []
            existing_ids = {tf["time_frame_id"]: tf for tf in self.time_frames}
            for row in data:
                time_frame_id = int(row[0]) if row[0] else len(new_time_frames) + 1
                if time_frame_id in existing_ids:
                    new_time_frames.append({
                        "time_frame_id": time_frame_id,
                        "finish_date": row[1],
                        "width_proportion": float(row[2]) / 100
                    })
                else:
                    new_time_frames.append({
                        "time_frame_id": time_frame_id,
                        "finish_date": row[1],
                        "width_proportion": float(row[2]) / 100
                    })
            self.time_frames = sorted(new_time_frames, key=lambda x: x["time_frame_id"])
        else:
            setattr(self, key, data)

    def get_table_data(self, key):
        if key == "tasks":
            return [[t.task_id, str(t.task_order), t.task_name, t.start_date, t.finish_date, str(t.row_number),
                     t.label_placement, t.label_hide, t.label_alignment,
                     str(t.label_horizontal_offset), str(t.label_vertical_offset), t.label_text_colour]
                    for t in self.tasks]
        elif key == "time_frames":
            return [[str(tf["time_frame_id"]), tf["finish_date"], str(tf["width_proportion"] * 100)]
                    for tf in sorted(self.time_frames, key=lambda x: x["time_frame_id"])]
        return getattr(self, key, [])

    def to_json(self):
        return {
            "frame_config": vars(self.frame_config),
            "time_frames": sorted(self.time_frames, key=lambda x: x["time_frame_id"]),
            "tasks": [{"task_id": t.task_id, "task_order": t.task_order, "task_name": t.task_name,
                       "start_date": t.start_date, "finish_date": t.finish_date, "row_number": t.row_number,
                       "is_milestone": t.is_milestone, "label_placement": t.label_placement,
                       "label_hide": t.label_hide, "label_alignment": t.label_alignment,
                       "label_horizontal_offset": t.label_horizontal_offset,
                       "label_vertical_offset": t.label_vertical_offset, "label_text_colour": t.label_text_colour}
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
        time_frames = data.get("time_frames", [])
        for idx, tf in enumerate(time_frames, 1):
            # Assign time_frame_id for legacy JSONs lacking it
            time_frame_id = tf.get("time_frame_id", idx)
            project.add_time_frame(
                time_frame_id,
                tf.get("finish_date", "2025-01-01"),
                tf.get("width_proportion", 1.0)
            )
        for task in data.get("tasks", []):
            project.add_task(
                task["task_id"], task["task_name"], task["start_date"],
                task["finish_date"], task["row_number"], task.get("is_milestone", False),
                task.get("label_placement", "Inside"), task.get("label_hide", "No"),
                task.get("label_alignment", "Left"), task.get("label_horizontal_offset", 1.0),
                task.get("label_vertical_offset", 0.5), task.get("label_text_colour", "black"),
                task.get("task_order", float(len(project.tasks) + 1))
            )
        project.connectors = data.get("connectors", [])
        project.swimlanes = data.get("swimlanes", [])
        project.pipes = data.get("pipes", [])
        project.curtains = data.get("curtains", [])
        project.text_boxes = data.get("text_boxes", [])
        return project