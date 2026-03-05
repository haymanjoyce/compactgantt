from typing import List, Set, Dict, Any, Optional
from datetime import datetime
from models import Task, Swimlane
from config.date_config import DateConfig
from utils.conversion import (
    is_valid_internal_date,
    parse_internal_date,
    compare_internal_dates,
    safe_int,
    display_to_internal_date,
)


def _to_internal_date(date_str: str, date_config: Optional[DateConfig] = None) -> str:
    """Convert date to internal format (yyyy-mm-dd). If already internal, return as-is; else try display format."""
    if not date_str or not date_str.strip():
        return date_str
    if is_valid_internal_date(date_str):
        return date_str
    config = date_config or DateConfig()
    try:
        return display_to_internal_date(date_str.strip(), config)
    except ValueError:
        return date_str


class DataValidator:
    @staticmethod
    def validate_task(
        task: Task, used_ids: Set[int], date_config: Optional[DateConfig] = None,
        swimlanes: Optional[List[Swimlane]] = None
    ) -> List[str]:
        errors = []
        # Normalize task_id and swimlane_row to int to handle legacy data with string values
        task_id = safe_int(task.task_id)
        swimlane_row = safe_int(task.swimlane_row)
        # Normalize dates to internal format (yyyy-mm-dd) using date_config when not already internal
        start_date = _to_internal_date(task.start_date, date_config)
        finish_date = _to_internal_date(task.finish_date, date_config)
        
        if task_id <= 0:
            errors.append("Task ID must be positive")
        if task_id in used_ids:
            errors.append("Task ID must be unique")
        if not is_valid_internal_date(start_date):
            errors.append("Invalid start date format (should be yyyy-mm-dd)")
        if not is_valid_internal_date(finish_date):
            errors.append("Invalid finish date format (should be yyyy-mm-dd)")
        
        # Check if finish date is earlier than start date (only if both dates are valid)
        # compare_internal_dates(finish, start) is True when finish < start (invalid)
        if is_valid_internal_date(start_date) and is_valid_internal_date(finish_date):
            if compare_internal_dates(finish_date, start_date) is True:
                errors.append("Finish date must be on or after start date")
        
        if swimlanes is not None:
            swimlane_lookup = {s.swimlane_id: s for s in swimlanes}
            if not task.swimlane_id or task.swimlane_id not in swimlane_lookup:
                errors.append("Task swimlane_id does not match any swimlane")
            else:
                parent = swimlane_lookup[task.swimlane_id]
                if swimlane_row < 1 or swimlane_row > parent.row_count:
                    errors.append(
                        f"Swimlane row {swimlane_row} is out of range for swimlane (1\u2013{parent.row_count})"
                    )
        else:
            if swimlane_row <= 0:
                errors.append("Swimlane row must be positive")
        return errors

    @staticmethod
    def validate_date_format(date_str: str) -> List[str]:
        errors = []
        if not is_valid_internal_date(date_str):
            errors.append("Invalid date format (should be yyyy-mm-dd)")
        return errors

    @staticmethod
    def validate_positive_number(value: float, field_name: str) -> List[str]:
        errors = []
        if value <= 0:
            errors.append(f"{field_name} must be positive")
        return errors

    @staticmethod
    def validate_non_negative_integer_string(value: str, field_name: str) -> List[str]:
        """Validate that a string represents a non-negative integer.
        
        Args:
            value: The string value to validate
            field_name: The name of the field (for error messages)
            
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        try:
            # Check for empty string first
            if not value.strip():
                errors.append(f"{field_name} must be a non-negative number")
                return errors
            # Then try to convert and validate
            num_value = int(value)
            if num_value < 0:
                errors.append(f"{field_name} must be a non-negative number")
        except ValueError:
            # Conversion failed - not a valid number
            errors.append(f"{field_name} must be a valid number")
        return errors

    @staticmethod
    def validate_unique_id(id_value: int, used_ids: Set[int], entity_name: str) -> List[str]:
        errors = []
        if id_value in used_ids:
            errors.append(f"{entity_name} ID must be unique")
        return errors 
