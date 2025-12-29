import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from typing import Any, Type, Dict, List
from datetime import datetime
from models.project import ProjectData
from models.frame import FrameConfig
from models.task import Task
from models.link import Link
from utils.conversion import internal_to_display_date, display_to_internal_date


class ExcelRepository:
    """Repository for Excel (XLSX) import/export functionality."""
    
    def save(self, file_path: str, project_data: ProjectData) -> None:
        """Export project data to Excel file with worksheets for each tab."""
        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet
        
        # Create worksheets for each tab
        self._create_layout_sheet(wb, project_data.frame_config)
        self._create_titles_sheet(wb, project_data.frame_config)
        self._create_scales_sheet(wb, project_data.frame_config)
        self._create_grid_sheet(wb, project_data.frame_config)
        self._create_tasks_sheet(wb, project_data.tasks)
        self._create_links_sheet(wb, project_data.links)
        self._create_swimlanes_sheet(wb, project_data.swimlanes)
        self._create_pipes_sheet(wb, project_data.pipes)
        self._create_curtains_sheet(wb, project_data.curtains)
        self._create_text_boxes_sheet(wb, project_data.text_boxes)
        
        wb.save(file_path)
    
    def load(self, file_path: str, project_data_cls: Type) -> ProjectData:
        """Import project data from Excel file."""
        wb = openpyxl.load_workbook(file_path, data_only=True)
        
        # Create new project instance
        project = project_data_cls()
        
        # Load data from each worksheet
        frame_config_data = {}
        
        # Load Layout sheet
        if "Layout" in wb.sheetnames:
            layout_data = self._read_key_value_sheet(wb["Layout"])
            frame_config_data.update(layout_data)
        
        # Load Titles sheet
        if "Titles" in wb.sheetnames:
            titles_data = self._read_key_value_sheet(wb["Titles"])
            frame_config_data.update(titles_data)
        
        # Load Scales sheet
        if "Scales" in wb.sheetnames:
            scales_data = self._read_key_value_sheet(wb["Scales"])
            frame_config_data.update(scales_data)
        
        # Load Grid sheet
        if "Grid" in wb.sheetnames:
            grid_data = self._read_key_value_sheet(wb["Grid"])
            frame_config_data.update(grid_data)
        
        # Convert margins list to tuple if present
        if "margins" in frame_config_data and isinstance(frame_config_data["margins"], list):
            frame_config_data["margins"] = tuple(frame_config_data["margins"])
        
        # Create FrameConfig
        project.frame_config = FrameConfig(**frame_config_data)
        
        # Load Tasks sheet
        if "Tasks" in wb.sheetnames:
            project.tasks = self._read_tasks_sheet(wb["Tasks"])
        
        # Load Links sheet - using header-based mapping instead of positional arrays
        if "Links" in wb.sheetnames:
            project.links = self._read_links_sheet(wb["Links"])
        
        if "Swimlanes" in wb.sheetnames:
            project.swimlanes = self._read_table_sheet(wb["Swimlanes"])
        
        if "Pipes" in wb.sheetnames:
            project.pipes = self._read_table_sheet(wb["Pipes"])
        
        if "Curtains" in wb.sheetnames:
            project.curtains = self._read_table_sheet(wb["Curtains"])
        
        if "Text Boxes" in wb.sheetnames:
            project.text_boxes = self._read_table_sheet(wb["Text Boxes"])
        
        return project
    
    def _create_layout_sheet(self, wb: Workbook, frame_config: FrameConfig) -> None:
        """Create Layout worksheet with chart dimensions, margins, and rows."""
        ws = wb.create_sheet("Layout")
        
        # Header
        ws.append(["Field", "Value"])
        self._format_header_row(ws, 1)
        
        # Layout fields
        ws.append(["Outer Width", frame_config.outer_width])
        ws.append(["Outer Height", frame_config.outer_height])
        ws.append(["Number of Rows", frame_config.num_rows])
        ws.append(["Margin Top", frame_config.margins[0]])
        ws.append(["Margin Right", frame_config.margins[1]])
        ws.append(["Margin Bottom", frame_config.margins[2]])
        ws.append(["Margin Left", frame_config.margins[3]])
        ws.append(["Chart Start Date", internal_to_display_date(frame_config.chart_start_date)])
        ws.append(["Chart End Date", internal_to_display_date(frame_config.chart_end_date)])
        
        # Auto-adjust column widths
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 15
    
    def _create_titles_sheet(self, wb: Workbook, frame_config: FrameConfig) -> None:
        """Create Titles worksheet with header and footer settings."""
        ws = wb.create_sheet("Titles")
        
        # Header
        ws.append(["Field", "Value"])
        self._format_header_row(ws, 1)
        
        # Title fields
        ws.append(["Header Height", frame_config.header_height])
        ws.append(["Header Text", frame_config.header_text])
        ws.append(["Footer Height", frame_config.footer_height])
        ws.append(["Footer Text", frame_config.footer_text])
        
        # Auto-adjust column widths
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 30
    
    def _create_scales_sheet(self, wb: Workbook, frame_config: FrameConfig) -> None:
        """Create Scales worksheet with scale visibility settings."""
        ws = wb.create_sheet("Scales")
        
        # Header
        ws.append(["Field", "Value"])
        self._format_header_row(ws, 1)
        
        # Scale fields
        ws.append(["Show Years", "Yes" if frame_config.show_years else "No"])
        ws.append(["Show Months", "Yes" if frame_config.show_months else "No"])
        ws.append(["Show Weeks", "Yes" if frame_config.show_weeks else "No"])
        ws.append(["Show Days", "Yes" if frame_config.show_days else "No"])
        
        # Auto-adjust column widths
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 10
    
    def _create_grid_sheet(self, wb: Workbook, frame_config: FrameConfig) -> None:
        """Create Grid worksheet with gridline settings."""
        ws = wb.create_sheet("Grid")
        
        # Header
        ws.append(["Field", "Value"])
        self._format_header_row(ws, 1)
        
        # Grid fields
        ws.append(["Horizontal Gridlines", "Yes" if frame_config.horizontal_gridlines else "No"])
        ws.append(["Vertical Gridline Years", "Yes" if frame_config.vertical_gridline_years else "No"])
        ws.append(["Vertical Gridline Months", "Yes" if frame_config.vertical_gridline_months else "No"])
        ws.append(["Vertical Gridline Weeks", "Yes" if frame_config.vertical_gridline_weeks else "No"])
        ws.append(["Vertical Gridline Days", "Yes" if frame_config.vertical_gridline_days else "No"])
        
        # Auto-adjust column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 10
    
    def _create_tasks_sheet(self, wb: Workbook, tasks: List[Task]) -> None:
        """Create Tasks worksheet with task data as a table.
        
        Only saves visible/editable fields that match the UI table columns.
        Redundant fields (Is Milestone, Label Alignment, Label Horizontal Offset, Label Text Colour)
        are excluded as they are either auto-calculated or have default values.
        """
        ws = wb.create_sheet("Tasks")
        
        # Headers - only include fields that are visible/editable in UI
        headers = ["ID", "Row", "Name", "Start Date", "Finish Date", "Label", "Placement"]
        ws.append(headers)
        self._format_header_row(ws, 1)
        
        # Task rows - only save visible/editable fields
        for task in tasks:
            row = [
                task.task_id,
                task.row_number,
                task.task_name,
                internal_to_display_date(task.start_date),
                internal_to_display_date(task.finish_date),
                task.label_hide,
                task.label_placement
            ]
            ws.append(row)
        
        # Auto-adjust column widths
        for col_idx, header in enumerate(headers, 1):
            col_letter = openpyxl.utils.get_column_letter(col_idx)
            if header == "Name":
                ws.column_dimensions[col_letter].width = 15
            elif header in ["Start Date", "Finish Date"]:
                ws.column_dimensions[col_letter].width = 12
            else:
                ws.column_dimensions[col_letter].width = 10
    
    def _create_links_sheet(self, wb: Workbook, links: List[Link]) -> None:
        """Create Links worksheet."""
        ws = wb.create_sheet("Links")
        
        # Define headers explicitly (excluding Valid field as it's calculated)
        headers = ["ID", "From Task ID", "From Task Name", "To Task ID", "To Task Name", "Line Color", "Line Style"]
        ws.append(headers)
        self._format_header_row(ws, 1)
        
        # Write link data (Valid field is excluded as it's calculated)
        for link in links:
            ws.append([
                str(link.link_id),
                str(link.from_task_id),
                link.from_task_name or "",
                str(link.to_task_id),
                link.to_task_name or "",
                link.line_color,
                link.line_style
            ])
        
        # Auto-adjust column widths
        for col in ws.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[col_letter].width = adjusted_width
    
    def _create_swimlanes_sheet(self, wb: Workbook, swimlanes: List[List[str]]) -> None:
        """Create Swimlanes worksheet."""
        ws = wb.create_sheet("Swimlanes")
        if swimlanes:
            if len(swimlanes) > 0:
                ws.append(swimlanes[0] if len(swimlanes[0]) > 0 else ["Start", "End", "Label", "Color"])
                self._format_header_row(ws, 1)
                for row in swimlanes[1:] if len(swimlanes) > 1 else []:
                    ws.append(row)
            else:
                ws.append(["Start", "End", "Label", "Color"])
                self._format_header_row(ws, 1)
        else:
            ws.append(["Start", "End", "Label", "Color"])
            self._format_header_row(ws, 1)
    
    def _create_pipes_sheet(self, wb: Workbook, pipes: List[List[str]]) -> None:
        """Create Pipes worksheet."""
        ws = wb.create_sheet("Pipes")
        if pipes:
            if len(pipes) > 0:
                ws.append(pipes[0] if len(pipes[0]) > 0 else ["Date", "Color"])
                self._format_header_row(ws, 1)
                for row in pipes[1:] if len(pipes) > 1 else []:
                    ws.append(row)
            else:
                ws.append(["Date", "Color"])
                self._format_header_row(ws, 1)
        else:
            ws.append(["Date", "Color"])
            self._format_header_row(ws, 1)
    
    def _create_curtains_sheet(self, wb: Workbook, curtains: List[List[str]]) -> None:
        """Create Curtains worksheet."""
        ws = wb.create_sheet("Curtains")
        if curtains:
            if len(curtains) > 0:
                ws.append(curtains[0] if len(curtains[0]) > 0 else ["Start Date", "End Date", "Color"])
                self._format_header_row(ws, 1)
                for row in curtains[1:] if len(curtains) > 1 else []:
                    ws.append(row)
            else:
                ws.append(["Start Date", "End Date", "Color"])
                self._format_header_row(ws, 1)
        else:
            ws.append(["Start Date", "End Date", "Color"])
            self._format_header_row(ws, 1)
    
    def _create_text_boxes_sheet(self, wb: Workbook, text_boxes: List[List[str]]) -> None:
        """Create Text Boxes worksheet."""
        ws = wb.create_sheet("Text Boxes")
        if text_boxes:
            if len(text_boxes) > 0:
                ws.append(text_boxes[0] if len(text_boxes[0]) > 0 else ["Text", "X", "Y", "Color"])
                self._format_header_row(ws, 1)
                for row in text_boxes[1:] if len(text_boxes) > 1 else []:
                    ws.append(row)
            else:
                ws.append(["Text", "X", "Y", "Color"])
                self._format_header_row(ws, 1)
        else:
            ws.append(["Text", "X", "Y", "Color"])
            self._format_header_row(ws, 1)
    
    def _format_header_row(self, ws, row_num: int) -> None:
        """Format header row with bold font and background color."""
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF")
        
        for cell in ws[row_num]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
    
    def _read_key_value_sheet(self, ws) -> Dict[str, Any]:
        """Read a key-value pair worksheet (Layout, Titles, Scales, Grid)."""
        data = {}
        for row in ws.iter_rows(min_row=2, values_only=True):  # Skip header row
            if row[0] and row[1] is not None:
                key = str(row[0]).strip()
                value = row[1]
                
                # Convert value based on key
                if key in ["Outer Width", "Outer Height", "Number of Rows", "Header Height", "Footer Height",
                           "Margin Top", "Margin Right", "Margin Bottom", "Margin Left"]:
                    try:
                        value = int(value) if value is not None else 0
                    except (ValueError, TypeError):
                        value = 0
                elif key in ["Show Years", "Show Months", "Show Weeks", "Show Days",
                             "Horizontal Gridlines", "Vertical Gridline Years", "Vertical Gridline Months",
                             "Vertical Gridline Weeks", "Vertical Gridline Days"]:
                    value = str(value).strip().lower() in ["yes", "true", "1", 1, True]
                elif key in ["Chart Start Date", "Chart End Date"]:
                    # Convert from display format (dd/mm/yyyy) to internal format (yyyy-mm-dd)
                    # Handle both string dates and Excel date serial numbers
                    try:
                        if value:
                            if isinstance(value, datetime):
                                # Excel date serial number converted to datetime
                                value = value.strftime("%Y-%m-%d")
                            else:
                                # String date - convert from display format
                                value = display_to_internal_date(str(value))
                    except (ValueError, AttributeError):
                        pass  # Keep original value if conversion fails
                elif key in ["Header Text", "Footer Text"]:
                    value = str(value) if value is not None else ""
                
                # Map to frame_config field names
                field_map = {
                    "Outer Width": "outer_width",
                    "Outer Height": "outer_height",
                    "Number of Rows": "num_rows",
                    "Margin Top": "margins",
                    "Margin Right": "margins",
                    "Margin Bottom": "margins",
                    "Margin Left": "margins",
                    "Header Height": "header_height",
                    "Header Text": "header_text",
                    "Footer Height": "footer_height",
                    "Footer Text": "footer_text",
                    "Show Years": "show_years",
                    "Show Months": "show_months",
                    "Show Weeks": "show_weeks",
                    "Show Days": "show_days",
                    "Horizontal Gridlines": "horizontal_gridlines",
                    "Vertical Gridline Years": "vertical_gridline_years",
                    "Vertical Gridline Months": "vertical_gridline_months",
                    "Vertical Gridline Weeks": "vertical_gridline_weeks",
                    "Vertical Gridline Days": "vertical_gridline_days",
                    "Chart Start Date": "chart_start_date",
                    "Chart End Date": "chart_end_date"
                }
                
                field_name = field_map.get(key)
                if field_name:
                    if field_name == "margins":
                        # Handle margins tuple
                        if "margins" not in data:
                            data["margins"] = [0, 0, 0, 0]
                        margin_map = {
                            "Margin Top": 0,
                            "Margin Right": 1,
                            "Margin Bottom": 2,
                            "Margin Left": 3
                        }
                        margin_idx = margin_map.get(key)
                        if margin_idx is not None:
                            data["margins"][margin_idx] = value
                    else:
                        data[field_name] = value
        
        # Convert margins list to tuple
        if "margins" in data and isinstance(data["margins"], list):
            data["margins"] = tuple(data["margins"])
        
        return data
    
    def _read_tasks_sheet(self, ws) -> List[Task]:
        """Read Tasks worksheet and return list of Task objects."""
        tasks = []
        headers = None
        
        for row_idx, row in enumerate(ws.iter_rows(values_only=True), 1):
            if row_idx == 1:
                # Header row
                headers = [str(cell).strip() if cell else "" for cell in row]
                continue
            
            if not any(row):  # Skip empty rows
                continue
            
            # Create task dict from row data
            task_data = {}
            for col_idx, value in enumerate(row):
                if col_idx < len(headers) and headers[col_idx]:
                    header = headers[col_idx]
                    
                    # Map Excel headers to task fields
                    if header == "ID":
                        task_data["task_id"] = int(value) if value is not None else 0
                    elif header == "Row":
                        task_data["row_number"] = int(value) if value is not None else 1
                    elif header == "Name":
                        task_data["task_name"] = str(value) if value is not None else ""
                    elif header == "Start Date":
                        # Convert from display format to internal format
                        # Handle both string dates and Excel date serial numbers
                        try:
                            if value:
                                if isinstance(value, datetime):
                                    # Excel date serial number converted to datetime
                                    task_data["start_date"] = value.strftime("%Y-%m-%d")
                                else:
                                    # String date - convert from display format
                                    task_data["start_date"] = display_to_internal_date(str(value))
                            else:
                                task_data["start_date"] = ""
                        except (ValueError, AttributeError):
                            task_data["start_date"] = ""
                    elif header == "Finish Date":
                        # Convert from display format to internal format
                        # Handle both string dates and Excel date serial numbers
                        try:
                            if value:
                                if isinstance(value, datetime):
                                    # Excel date serial number converted to datetime
                                    task_data["finish_date"] = value.strftime("%Y-%m-%d")
                                else:
                                    # String date - convert from display format
                                    task_data["finish_date"] = display_to_internal_date(str(value))
                            else:
                                task_data["finish_date"] = ""
                        except (ValueError, AttributeError):
                            task_data["finish_date"] = ""
                    elif header == "Label":
                        task_data["label_hide"] = str(value) if value is not None else "Yes"
                    elif header == "Placement":
                        task_data["label_placement"] = str(value) if value is not None else "Outside"
                    elif header == "Is Milestone":
                        task_data["is_milestone"] = str(value).strip().lower() in ["yes", "true", "1"]
                    elif header == "Label Alignment":
                        task_data["label_alignment"] = str(value) if value is not None else "Centre"
                    elif header == "Label Horizontal Offset":
                        task_data["label_horizontal_offset"] = float(value) if value is not None else 1.0
                    elif header == "Label Text Colour":
                        task_data["label_text_colour"] = str(value) if value is not None else "black"
            
            # Only create task if we have required fields
            if "task_id" in task_data and task_data["task_id"] > 0:
                try:
                    task = Task.from_dict(task_data)
                    tasks.append(task)
                except (KeyError, ValueError) as e:
                    # Skip invalid tasks
                    continue
        
        return tasks
    
    def _read_links_sheet(self, ws) -> List[Link]:
        """Read Links worksheet and return list of Link objects using header-based mapping.
        
        This method uses header-based mapping instead of positional arrays to avoid
        index brittleness when columns are added, removed, or reordered.
        """
        links = []
        headers = None
        
        for row_idx, row in enumerate(ws.iter_rows(values_only=True), 1):
            if row_idx == 1:
                # Header row
                headers = [str(cell).strip() if cell else "" for cell in row]
                continue
            
            if not any(row):  # Skip empty rows
                continue
            
            # Create link dict from row data using header mapping
            link_data = {}
            for col_idx, value in enumerate(row):
                if col_idx < len(headers) and headers[col_idx]:
                    header = headers[col_idx]
                    
                    # Map Excel headers to link fields
                    if header == "ID":
                        link_data["link_id"] = int(value) if value is not None else 0
                    elif header == "From Task ID":
                        link_data["from_task_id"] = int(value) if value is not None else 0
                    elif header == "From Task Name":
                        link_data["from_task_name"] = str(value) if value is not None else ""
                    elif header == "To Task ID":
                        link_data["to_task_id"] = int(value) if value is not None else 0
                    elif header == "To Task Name":
                        link_data["to_task_name"] = str(value) if value is not None else ""
                    elif header == "Line Color":
                        link_data["line_color"] = str(value) if value is not None else "black"
                    elif header == "Line Style":
                        link_data["line_style"] = str(value) if value is not None else "solid"
            
            # Only create link if we have required fields
            if ("link_id" in link_data and link_data["link_id"] > 0 and
                "from_task_id" in link_data and link_data["from_task_id"] > 0 and
                "to_task_id" in link_data and link_data["to_task_id"] > 0):
                try:
                    link = Link.from_dict(link_data)
                    links.append(link)
                except (KeyError, ValueError) as e:
                    # Skip invalid links
                    continue
        
        return links
    
    def _read_table_sheet(self, ws) -> List[List[str]]:
        """Read a table worksheet (Links, Swimlanes, Pipes, Curtains, Text Boxes)."""
        data = []
        for row in ws.iter_rows(values_only=True):
            if any(row):  # Only add non-empty rows
                data.append([str(cell) if cell is not None else "" for cell in row])
        return data[1:] if len(data) > 1 else []  # Skip header row

