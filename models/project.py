from typing import List, Dict, Any, Set
from models import FrameConfig, Task, Link
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
        self.swimlanes: List[List[str]] = []
        self.pipes: List[List[str]] = []
        self.curtains: List[List[str]] = []
        self.text_boxes: List[List[str]] = []
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
            # Only save non-default values for backward compatibility fields
            if task.label_alignment != "Centre":
                task_dict["label_alignment"] = task.label_alignment
            if task.label_horizontal_offset != 1.0:
                task_dict["label_horizontal_offset"] = task.label_horizontal_offset
            if task.label_text_colour != "black":
                task_dict["label_text_colour"] = task.label_text_colour
            tasks_data.append(task_dict)
        
        # FrameConfig: save all fields (all are necessary)
        # Convert Link objects to dictionaries for JSON (Valid field is excluded as it's calculated)
        links_data = [link.to_dict() for link in self.links]
        
        return {
            "frame_config": vars(self.frame_config),
            "tasks": tasks_data,
            "links": links_data,
            "swimlanes": self.swimlanes,
            "pipes": self.pipes,
            "curtains": self.curtains,
            "text_boxes": self.text_boxes
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'ProjectData':
        project = cls()
        frame_config_data = data.get("frame_config", {})
        # Convert margins list back to tuple (JSON converts tuples to lists)
        if "margins" in frame_config_data and isinstance(frame_config_data["margins"], list):
            frame_config_data["margins"] = tuple(frame_config_data["margins"])
        
        # Handle backward compatibility: migrate old vertical_gridlines to new individual flags
        if "vertical_gridlines" in frame_config_data and "vertical_gridline_years" not in frame_config_data:
            old_value = frame_config_data.pop("vertical_gridlines")
            frame_config_data["vertical_gridline_years"] = old_value
            frame_config_data["vertical_gridline_months"] = old_value
            frame_config_data["vertical_gridline_weeks"] = old_value
            frame_config_data["vertical_gridline_days"] = old_value
        
        project.frame_config = FrameConfig(**frame_config_data)
        
        # Load tasks
        for task_data in data.get("tasks", []):
            project.tasks.append(Task.from_dict(task_data))
        
        # Load links - convert dicts to Link objects
        links_data = data.get("links", [])
        project.links = []
        for link_data in links_data:
            if isinstance(link_data, dict):
                project.links.append(Link.from_dict(link_data))
            else:
                # Legacy list format - skip (shouldn't happen after migration)
                continue
        project.swimlanes = data.get("swimlanes", [])
        project.pipes = data.get("pipes", [])
        project.curtains = data.get("curtains", [])
        project.text_boxes = data.get("text_boxes", [])
        
        return project
    
    def update_from_table(self, key: str, data: List[List[str]]) -> List[str]:
        """Update project data from table data. Returns list of validation errors."""
        errors = []
        try:
            if key == "tasks":
                new_tasks = []
                used_ids: Set[int] = set()
                for row_idx, row in enumerate(data, 1):
                    try:
                        # Skip validation for empty rows (ID is empty or 0, or row is too short)
                        # Now expects: [ID, Row, Name, Start Date, Finish Date, Label, Placement, Valid]
                        if not row or len(row) < 7:
                            continue
                        
                        # Check if ID field is empty - skip this row
                        task_id_str = str(row[0]).strip() if len(row) > 0 else ""
                        if not task_id_str or safe_int(task_id_str) <= 0:
                            continue
                        
                        # extract_table_data already skips checkbox column, so data is 0-indexed
                        # Column order: ID, Row, Name, Start Date, Finish Date, Label, Placement, Valid
                        # Handle backward compatibility: check if row has Order column (old format)
                        # If row[1] is numeric and row[2] is also numeric, assume old format with Order
                        has_order = False
                        if len(row) > 2:
                            try:
                                float(row[1])
                                int(row[2])
                                has_order = True  # Old format with Order column
                            except (ValueError, TypeError):
                                pass
                        
                        # Adjust indices based on whether Order column exists
                        if has_order:
                            # Old format: [ID, Order, Row, Name, Start Date, Finish Date, Label, Placement, Valid?]
                            row_idx = 2
                            name_idx = 3
                            start_date_idx = 4
                            finish_date_idx = 5
                            label_idx = 6
                            placement_idx = 7
                            valid_idx = 8 if len(row) > 8 else None
                        else:
                            # New format: [ID, Row, Name, Start Date, Finish Date, Label, Placement, Valid]
                            row_idx = 1
                            name_idx = 2
                            start_date_idx = 3
                            finish_date_idx = 4
                            label_idx = 5
                            placement_idx = 6
                            valid_idx = 7 if len(row) > 7 else None
                        
                        # Convert display format to internal format for dates (handles empty strings and invalid formats)
                        start_date_internal = ""
                        if len(row) > start_date_idx and row[start_date_idx].strip():
                            try:
                                start_date_internal = display_to_internal_date(row[start_date_idx])
                            except ValueError:
                                start_date_internal = ""  # Invalid date format - set to empty
                        
                        finish_date_internal = ""
                        if len(row) > finish_date_idx and row[finish_date_idx].strip():
                            try:
                                finish_date_internal = display_to_internal_date(row[finish_date_idx])
                            except ValueError:
                                finish_date_internal = ""  # Invalid date format - set to empty
                        # Convert old placement values to new ones for backward compatibility
                        placement_value = row[placement_idx] if len(row) > placement_idx else "Outside"
                        if placement_value in ["To left", "To right"]:
                            placement_value = "Outside"
                        try:
                            task = Task(
                                task_id=safe_int(row[0]),  # ID is at index 0
                                row_number=safe_int(row[row_idx], 1),  # Row
                                task_name=row[name_idx] if len(row) > name_idx else "",  # Name
                                start_date=start_date_internal,  # Store in internal format
                                finish_date=finish_date_internal,  # Store in internal format
                                label_hide=row[label_idx] if len(row) > label_idx else "Yes",  # Label (No = Hide, Yes = Show)
                                label_placement=placement_value,  # Placement
                                label_alignment="Centre",  # Always use Centre for inside labels (backward compatibility)
                                label_horizontal_offset=1.0,  # Default value (backward compatibility - now uses config value)
                                label_text_colour="black"  # Default color (backward compatibility - not used in rendering)
                            )
                            # Validate task and set Valid field
                            row_errors = self.validator.validate_task(task, used_ids)
                            valid_status = "No" if row_errors else "Yes"
                            
                            # Ensure row has Valid field at the correct index
                            if has_order:
                                # Old format: ensure 9 elements [ID, Order, Row, Name, Start Date, Finish Date, Label, Placement, Valid]
                                while len(row) < 9:
                                    row.append("")
                                row[8] = valid_status
                            else:
                                # New format: ensure 8 elements [ID, Row, Name, Start Date, Finish Date, Label, Placement, Valid]
                                while len(row) < 8:
                                    row.append("")
                                row[7] = valid_status
                            
                            # Save task regardless of validity (like links)
                            new_tasks.append(task)
                            if not row_errors:
                                used_ids.add(task.task_id)
                        except Exception as e:
                            logging.warning(f"Error creating task in row {row_idx}: {e}")
                            # Set Valid to "No" and try to save minimal task data
                            if has_order:
                                while len(row) < 9:
                                    row.append("")
                                row[8] = "No"
                            else:
                                while len(row) < 8:
                                    row.append("")
                                row[7] = "No"
                            # Try to save task with minimal data
                            try:
                                task = Task(
                                    task_id=safe_int(row[0], 0),
                                    row_number=safe_int(row[row_idx] if has_order else row[1], 1),
                                    task_name=row[name_idx] if len(row) > name_idx else "",
                                    start_date="",
                                    finish_date="",
                                    label_hide=row[label_idx] if len(row) > label_idx else "Yes",
                                    label_placement=row[placement_idx] if len(row) > placement_idx else "Outside"
                                )
                                new_tasks.append(task)
                            except:
                                pass  # Skip if we can't create task at all
                    except ValueError as e:
                        # Handle date conversion errors - set Valid to "No" but still try to save
                        error_msg = str(e)
                        # Ensure row has Valid field
                        if has_order:
                            while len(row) < 9:
                                row.append("")
                            row[8] = "No"
                        else:
                            while len(row) < 8:
                                row.append("")
                            row[7] = "No"
                        # Still try to create and save the task if possible
                        try:
                            task = Task(
                                task_id=safe_int(row[0], 0),
                                row_number=safe_int(row[row_idx] if has_order else row[1], 1),
                                task_name=row[name_idx] if len(row) > name_idx else "",
                                start_date="",
                                finish_date="",
                                label_hide=row[label_idx] if len(row) > label_idx else "Yes",
                                label_placement=row[placement_idx] if len(row) > placement_idx else "Outside"
                            )
                            new_tasks.append(task)
                        except:
                            pass  # Skip if we can't create task
                    except (IndexError, AttributeError) as e:
                        # Set Valid to "No" for index errors
                        if has_order:
                            while len(row) < 9:
                                row.append("")
                            row[8] = "No"
                        else:
                            while len(row) < 8:
                                row.append("")
                            row[7] = "No"
                        # Try to save task if we have at least an ID
                        try:
                            task_id = safe_int(row[0], 0)
                            if task_id > 0:
                                task = Task(
                                    task_id=task_id,
                                    row_number=1,
                                    task_name="",
                                    start_date="",
                                    finish_date="",
                                    label_hide="Yes",
                                    label_placement="Outside"
                                )
                                new_tasks.append(task)
                        except:
                            pass
                
                # Always save tasks (regardless of validation errors)
                self.tasks = new_tasks
                logging.debug(f"Updated tasks: {len(new_tasks)} tasks saved (with Valid field set)")
                # Return empty errors list (no error dialogs)
                errors = []
            elif key == "links":
                # Convert table rows to Link objects
                new_links = []
                for row_idx, row in enumerate(data, 1):
                    try:
                        # Skip empty rows
                        # Table format: [ID, From Task ID, From Task Name, To Task ID, To Task Name, Valid, Line Color, Line Style]
                        # (Note: extract_table_data excludes Select checkbox, so indices start at 0)
                        if not row or len(row) < 4:  # Minimum: ID, From Task ID, To Task ID
                            continue
                        
                        # Extract core fields
                        link_id = safe_int(row[0])  # ID at index 0
                        from_task_id = safe_int(row[1])  # From Task ID at index 1
                        to_task_id = safe_int(row[3])  # To Task ID at index 3
                        
                        if link_id <= 0 or from_task_id <= 0 or to_task_id <= 0:
                            # Invalid IDs - skip this row
                            continue
                        
                        # Extract style fields (with defaults)
                        line_color = str(row[6]).strip() if len(row) > 6 and row[6] else "black"  # Line Color at index 6
                        line_style = str(row[7]).strip() if len(row) > 7 and row[7] else "solid"  # Line Style at index 7
                        
                        # Create Link instance
                        link = Link(
                            link_id=link_id,
                            from_task_id=from_task_id,
                            to_task_id=to_task_id,
                            line_color=line_color,
                            line_style=line_style,
                            from_task_name=str(row[2]).strip() if len(row) > 2 else "",  # From Task Name at index 2
                            to_task_name=str(row[4]).strip() if len(row) > 4 else ""     # To Task Name at index 4
                        )
                        
                        # Calculate valid status (Finish-to-Start validation)
                        from_task = next((t for t in self.tasks if t.task_id == from_task_id), None)
                        to_task = next((t for t in self.tasks if t.task_id == to_task_id), None)
                        
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
                        
                        new_links.append(link)
                    except (ValueError, TypeError, IndexError) as e:
                        errors.append(f"Row {row_idx}: {str(e)}")
                
                # Always update links (even if some are invalid)
                self.links = new_links
            else:
                setattr(self, key, data)
        except Exception as e:
            logging.error(f"Error in update_from_table: {e}", exc_info=True)
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
