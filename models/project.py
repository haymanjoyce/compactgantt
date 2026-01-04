from typing import List, Dict, Any, Set
from models import FrameConfig, Task, Link, Pipe, Curtain, Swimlane, TextBox
from validators import DataValidator
from datetime import datetime
import logging
from config.app_config import AppConfig
from utils.conversion import safe_int, safe_float, display_to_internal_date, internal_to_display_date

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ProjectData:
    def __init__(self):
        app_config = AppConfig()
        self.frame_config = FrameConfig(num_rows=app_config.general.tasks_rows)
        self.tasks: List[Task] = []
        self.links: List[Link] = []
        self.swimlanes: List[Swimlane] = []
        self.pipes: List[Pipe] = []
        self.curtains: List[Curtain] = []
        self.text_boxes: List[TextBox] = []
        self.validator = DataValidator()

    def to_json(self) -> Dict[str, Any]:
        for t in self.tasks:
            assert hasattr(t, "__dict__"), f"Non-class instance in self.tasks: {t} ({type(t)})"
        
        # Serialize tasks with only necessary fields (exclude redundant defaults)
        tasks_data = []
        for task in self.tasks:
            task_dict = {
                "task_id": task.task_id,
                "task_name": task.task_name,
                "start_date": task.start_date,
                "finish_date": task.finish_date,
                "row_number": task.row_number,
                "label_placement": task.label_placement,
                "label_hide": task.label_hide,
            }
            # Only save is_milestone if it's explicitly True (auto-detected from dates otherwise)
            if task.is_milestone:
                task_dict["is_milestone"] = True
            # Only save non-default values to reduce JSON size
            if task.label_alignment != "Centre":
                task_dict["label_alignment"] = task.label_alignment
            if task.label_horizontal_offset != 1.0:
                task_dict["label_horizontal_offset"] = task.label_horizontal_offset
            if task.label_text_colour != "black":
                task_dict["label_text_colour"] = task.label_text_colour
            if task.fill_color != "blue":
                task_dict["fill_color"] = task.fill_color
            tasks_data.append(task_dict)
        
        # FrameConfig: save all fields (all are necessary)
        # Convert Link objects to dictionaries for JSON (Valid field is excluded as it's calculated)
        links_data = [link.to_dict() for link in self.links]
        pipes_data = [pipe.to_dict() for pipe in self.pipes]
        curtains_data = [curtain.to_dict() for curtain in self.curtains]
        swimlanes_data = [swimlane.to_dict() for swimlane in self.swimlanes]
        text_boxes_data = [textbox.to_dict() for textbox in self.text_boxes]
        
        return {
            "frame_config": vars(self.frame_config),
            "tasks": tasks_data,
            "links": links_data,
            "swimlanes": swimlanes_data,
            "pipes": pipes_data,
            "curtains": curtains_data,
            "text_boxes": text_boxes_data
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'ProjectData':
        project = cls()
        frame_config_data = data.get("frame_config", {})
        # Convert margins list back to tuple (JSON converts tuples to lists)
        if "margins" in frame_config_data and isinstance(frame_config_data["margins"], list):
            frame_config_data["margins"] = tuple(frame_config_data["margins"])
        
        project.frame_config = FrameConfig(**frame_config_data)
        
        # Load tasks
        for task_data in data.get("tasks", []):
            project.tasks.append(Task.from_dict(task_data))
        
        # Load links - convert dicts to Link objects
        links_data = data.get("links", [])
        project.links = [Link.from_dict(link_data) for link_data in links_data if isinstance(link_data, dict)]
        
        # Load pipes - convert dicts to Pipe objects (with backward compatibility for old list format)
        pipes_data = data.get("pipes", [])
        if pipes_data and isinstance(pipes_data[0], dict):
            project.pipes = [Pipe.from_dict(pipe_data) for pipe_data in pipes_data if isinstance(pipe_data, dict)]
        else:
            # Backward compatibility: old list format
            project.pipes = []
        
        # Load curtains - convert dicts to Curtain objects (with backward compatibility for old list format)
        curtains_data = data.get("curtains", [])
        if curtains_data and isinstance(curtains_data[0], dict):
            project.curtains = [Curtain.from_dict(curtain_data) for curtain_data in curtains_data if isinstance(curtain_data, dict)]
        else:
            # Backward compatibility: old list format
            project.curtains = []
        
        # Load swimlanes - convert dicts to Swimlane objects (with backward compatibility for old list format)
        swimlanes_data = data.get("swimlanes", [])
        if swimlanes_data and isinstance(swimlanes_data[0], dict):
            project.swimlanes = [Swimlane.from_dict(swimlane_data) for swimlane_data in swimlanes_data if isinstance(swimlane_data, dict)]
        else:
            # Backward compatibility: old list format
            project.swimlanes = []
        
        # Load text boxes - convert dicts to TextBox objects (with backward compatibility for old list format)
        text_boxes_data = data.get("text_boxes", [])
        if text_boxes_data and isinstance(text_boxes_data[0], dict):
            project.text_boxes = [TextBox.from_dict(textbox_data) for textbox_data in text_boxes_data if isinstance(textbox_data, dict)]
        elif text_boxes_data and isinstance(text_boxes_data[0], list):
            # Backward compatibility: old list format
            project.text_boxes = [TextBox.from_dict(textbox_data) for textbox_data in text_boxes_data if isinstance(textbox_data, list)]
        else:
            project.text_boxes = []
        
        return project
    
    def update_links(self, links: List[Link]) -> List[str]:
        """
        Update links from a list of Link objects directly.
        This method calculates valid status for each link based on task dates.
        
        Args:
            links: List of Link objects to update
            
        Returns:
            List of error messages (empty if no errors)
        """
        errors = []
        try:
            # Calculate valid status for each link
            for link in links:
                from_task = next((t for t in self.tasks if t.task_id == link.from_task_id), None)
                to_task = next((t for t in self.tasks if t.task_id == link.to_task_id), None)
                
                if from_task and to_task:
                    from_finish_date = from_task.finish_date or from_task.start_date
                    to_start_date = to_task.start_date or to_task.finish_date
                    
                    if from_finish_date and to_start_date:
                        try:
                            from_finish = datetime.strptime(from_finish_date, "%Y-%m-%d")
                            to_start = datetime.strptime(to_start_date, "%Y-%m-%d")
                            link.valid = "No" if to_start < from_finish else "Yes"
                        except (ValueError, TypeError):
                            link.valid = "No"
                    else:
                        link.valid = "No"
                else:
                    link.valid = "No"
            
            # Populate task names
            task_name_map = {task.task_id: task.task_name for task in self.tasks}
            for link in links:
                link.from_task_name = task_name_map.get(link.from_task_id, "")
                link.to_task_name = task_name_map.get(link.to_task_id, "")
            
            self.links = links
        except Exception as e:
            logging.error(f"Error in update_links: {e}", exc_info=True)
            errors.append(f"Internal error: {str(e)}")
        return errors
    
    def update_tasks(self, tasks: List[Task]) -> List[str]:
        """
        Update tasks from a list of Task objects directly.
        This method validates each task and updates the tasks list.
        
        Args:
            tasks: List of Task objects to update
            
        Returns:
            List of error messages (empty if no errors)
        """
        errors = []
        try:
            # Validate each task
            used_ids: Set[int] = set()
            for task in tasks:
                row_errors = self.validator.validate_task(task, used_ids)
                if row_errors:
                    errors.extend([f"Task {task.task_id}: {err}" for err in row_errors])
                if not row_errors:
                    used_ids.add(task.task_id)
            
            # Update tasks list
            self.tasks = tasks
        except Exception as e:
            logging.error(f"Error in update_tasks: {e}", exc_info=True)
            errors.append(f"Internal error: {str(e)}")
        return errors

    def get_table_data(self, key: str) -> List[List[str]]:
        """Get table data for a given key. Returns list of rows."""
        if key == "tasks":
            return [[str(t.task_id), str(t.row_number), t.task_name, 
                    internal_to_display_date(t.start_date),  # Convert to display format
                    internal_to_display_date(t.finish_date),  # Convert to display format
                    t.label_hide, t.label_placement]
                   for t in self.tasks]
        elif key == "links":
            # Create a mapping of task_id to task_name for quick lookup
            task_name_map = {task.task_id: task.task_name for task in self.tasks}
            
            result = []
            for link in self.links:
                # Populate task names
                link.from_task_name = task_name_map.get(link.from_task_id, "")
                link.to_task_name = task_name_map.get(link.to_task_id, "")
                
                # Calculate valid status if not already set
                if link.valid is None:
                    from_task = next((t for t in self.tasks if t.task_id == link.from_task_id), None)
                    to_task = next((t for t in self.tasks if t.task_id == link.to_task_id), None)
                    
                    if from_task and to_task:
                        from_finish_date = from_task.finish_date or from_task.start_date
                        to_start_date = to_task.start_date or to_task.finish_date
                        
                        if from_finish_date and to_start_date:
                            try:
                                from_finish = datetime.strptime(from_finish_date, "%Y-%m-%d")
                                to_start = datetime.strptime(to_start_date, "%Y-%m-%d")
                                link.valid = "No" if to_start < from_finish else "Yes"
                            except (ValueError, TypeError):
                                link.valid = "No"
                        else:
                            link.valid = "No"
                    else:
                        link.valid = "No"
                
                # Table format: [ID, From Task ID, From Task Name, To Task ID, To Task Name, Valid, Line Color, Line Style]
                result.append([
                    str(link.link_id),
                    str(link.from_task_id),
                    link.from_task_name or "",
                    str(link.to_task_id),
                    link.to_task_name or "",
                    link.valid or "Yes",
                    link.line_color,
                    link.line_style
                ])
            return result
        return getattr(self, key, [])
