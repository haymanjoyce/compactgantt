from typing import List, Dict, Any, Set
from models import FrameConfig, Task, Link, Pipe, Curtain, Swimlane, Note
from validators import DataValidator
from datetime import datetime
import logging
from config.app_config import AppConfig
from config.chart_config import ChartConfig
from utils.conversion import safe_int, safe_float, display_to_internal_date, internal_to_display_date, parse_internal_date

# Logging is configured centrally in utils/logging_config.py

class ProjectData:
    def __init__(self, app_config=None):
        """Initialize ProjectData with optional AppConfig.
        
        Args:
            app_config: Optional AppConfig instance. If None, creates a new instance for fallback.
                       Should pass the shared instance from main() to ensure consistency.
        """
        if app_config is None:
            app_config = AppConfig()  # Fallback only - prefer passing shared instance
        self.frame_config = FrameConfig(num_rows=app_config.general.tasks_rows)
        # Initialize chart_config from app_config (for typography and other chart settings)
        self.chart_config = ChartConfig(
            font_family=app_config.general.chart.font_family,
            task_font_size=app_config.general.chart.task_font_size,
            scale_font_size=app_config.general.chart.scale_font_size,
            header_footer_font_size=app_config.general.chart.header_footer_font_size,
            row_number_font_size=app_config.general.chart.row_number_font_size,
            note_font_size=app_config.general.chart.note_font_size,
            swimlane_font_size=app_config.general.chart.swimlane_font_size,
            scale_vertical_alignment_factor=app_config.general.chart.scale_vertical_alignment_factor,
            task_vertical_alignment_factor=app_config.general.chart.task_vertical_alignment_factor,
            row_number_vertical_alignment_factor=app_config.general.chart.row_number_vertical_alignment_factor,
            header_footer_vertical_alignment_factor=app_config.general.chart.header_footer_vertical_alignment_factor,
            swimlane_top_vertical_alignment_factor=app_config.general.chart.swimlane_top_vertical_alignment_factor,
            swimlane_bottom_vertical_alignment_factor=app_config.general.chart.swimlane_bottom_vertical_alignment_factor
        )
        self.tasks: List[Task] = []
        self.links: List[Link] = []
        self.swimlanes: List[Swimlane] = []
        self.pipes: List[Pipe] = []
        self.curtains: List[Curtain] = []
        self.notes: List[Note] = []
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
                "label_hide": task.label_hide,  # Keep for backward compatibility
                "label_content": task.label_content,
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
            if task.date_format:
                task_dict["date_format"] = task.date_format
            tasks_data.append(task_dict)
        
        # FrameConfig: save all fields (all are necessary)
        # Convert Link objects to dictionaries for JSON (Valid field is excluded as it's calculated)
        links_data = [link.to_dict() for link in self.links]
        pipes_data = [pipe.to_dict() for pipe in self.pipes]
        curtains_data = [curtain.to_dict() for curtain in self.curtains]
        swimlanes_data = [swimlane.to_dict() for swimlane in self.swimlanes]
        notes_data = [note.to_dict() for note in self.notes]
        
        # Serialize chart_config (only typography-related fields to keep JSON size manageable)
        chart_config_data = {
            "font_family": self.chart_config.font_family,
            "task_font_size": self.chart_config.task_font_size,
            "scale_font_size": self.chart_config.scale_font_size,
            "header_footer_font_size": self.chart_config.header_footer_font_size,
            "row_number_font_size": self.chart_config.row_number_font_size,
            "note_font_size": self.chart_config.note_font_size,
            "swimlane_font_size": self.chart_config.swimlane_font_size,
            "scale_vertical_alignment_factor": self.chart_config.scale_vertical_alignment_factor,
            "task_vertical_alignment_factor": self.chart_config.task_vertical_alignment_factor,
            "row_number_vertical_alignment_factor": self.chart_config.row_number_vertical_alignment_factor,
            "header_footer_vertical_alignment_factor": self.chart_config.header_footer_vertical_alignment_factor,
            "swimlane_top_vertical_alignment_factor": self.chart_config.swimlane_top_vertical_alignment_factor,
            "swimlane_bottom_vertical_alignment_factor": self.chart_config.swimlane_bottom_vertical_alignment_factor
        }
        
        return {
            "frame_config": vars(self.frame_config),
            "chart_config": chart_config_data,
            "tasks": tasks_data,
            "links": links_data,
            "swimlanes": swimlanes_data,
            "pipes": pipes_data,
            "curtains": curtains_data,
            "notes": notes_data
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'ProjectData':
        project = cls()
        frame_config_data = data.get("frame_config", {})
        # Convert margins list back to tuple (JSON converts tuples to lists)
        if "margins" in frame_config_data and isinstance(frame_config_data["margins"], list):
            frame_config_data["margins"] = tuple(frame_config_data["margins"])
        
        project.frame_config = FrameConfig(**frame_config_data)
        
        # Load chart_config (backward compatibility: use defaults if not present)
        chart_config_data = data.get("chart_config", {})
        if chart_config_data:
            # Update project's chart_config with loaded values (only typography fields)
            for key in ["font_family", "task_font_size", "scale_font_size", "header_footer_font_size",
                       "row_number_font_size", "note_font_size", "swimlane_font_size",
                       "scale_vertical_alignment_factor", "task_vertical_alignment_factor",
                       "row_number_vertical_alignment_factor", "header_footer_vertical_alignment_factor",
                       "swimlane_top_vertical_alignment_factor", "swimlane_bottom_vertical_alignment_factor"]:
                if key in chart_config_data:
                    setattr(project.chart_config, key, chart_config_data[key])
            
            # Handle backward compatibility: if old swimlane_vertical_alignment_factor exists, use it for both
            if "swimlane_vertical_alignment_factor" in chart_config_data and "swimlane_top_vertical_alignment_factor" not in chart_config_data:
                old_factor = chart_config_data["swimlane_vertical_alignment_factor"]
                project.chart_config.swimlane_top_vertical_alignment_factor = old_factor
                project.chart_config.swimlane_bottom_vertical_alignment_factor = old_factor
            
            # Handle backward compatibility: if old text_box_font_size exists, map it to note_font_size
            if "text_box_font_size" in chart_config_data and "note_font_size" not in chart_config_data:
                project.chart_config.note_font_size = chart_config_data["text_box_font_size"]
        
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
        
        # Load notes - convert dicts to Note objects (with backward compatibility for old formats)
        # Support both "notes" and old "text_boxes" key names
        notes_data = data.get("notes", data.get("text_boxes", []))
        if notes_data and isinstance(notes_data[0], dict):
            project.notes = [Note.from_dict(note_data) for note_data in notes_data if isinstance(note_data, dict)]
        elif notes_data and isinstance(notes_data[0], list):
            # Backward compatibility: old list format
            project.notes = [Note.from_dict(note_data) for note_data in notes_data if isinstance(note_data, list)]
        else:
            project.notes = []
        
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
                        from_finish = parse_internal_date(from_finish_date)
                        to_start = parse_internal_date(to_start_date)
                        if from_finish and to_start:
                            link.valid = "No" if to_start < from_finish else "Yes"
                        else:
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
                            from_finish = parse_internal_date(from_finish_date)
                            to_start = parse_internal_date(to_start_date)
                            if from_finish and to_start:
                                link.valid = "No" if to_start < from_finish else "Yes"
                            else:
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
