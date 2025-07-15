from typing import Union, Optional
from datetime import datetime

def safe_int(value: Union[str, int, float, None], default: int = 0) -> int:
    """Safely convert a value to int, returning default if conversion fails."""
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_float(value: Union[str, int, float, None], default: float = 0.0) -> float:
    """Safely convert a value to float, returning default if conversion fails."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def display_to_internal_date(display_date: str) -> str:
    """
    Convert date from dd/mm/yyyy display format to yyyy-mm-dd internal format.
    
    Args:
        display_date: Date string in dd/mm/yyyy format
        
    Returns:
        Date string in yyyy-mm-dd format
        
    Raises:
        ValueError: If the date format is invalid
    """
    if not display_date or not display_date.strip():
        return ""
    
    try:
        # Parse dd/mm/yyyy format
        date_obj = datetime.strptime(display_date.strip(), "%d/%m/%Y")
        # Return in yyyy-mm-dd format
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format. Expected dd/mm/yyyy, got: {display_date}")

def internal_to_display_date(internal_date: str) -> str:
    """
    Convert date from yyyy-mm-dd internal format to dd/mm/yyyy display format.
    
    Args:
        internal_date: Date string in yyyy-mm-dd format
        
    Returns:
        Date string in dd/mm/yyyy format
        
    Raises:
        ValueError: If the date format is invalid
    """
    if not internal_date or not internal_date.strip():
        return ""
    
    try:
        # Parse yyyy-mm-dd format
        date_obj = datetime.strptime(internal_date.strip(), "%Y-%m-%d")
        # Return in dd/mm/yyyy format
        return date_obj.strftime("%d/%m/%Y")
    except ValueError:
        raise ValueError(f"Invalid date format. Expected yyyy-mm-dd, got: {internal_date}")

def is_valid_display_date(date_str: str) -> bool:
    """
    Check if a date string is in valid dd/mm/yyyy format.
    
    Args:
        date_str: Date string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not date_str or not date_str.strip():
        return False
    
    try:
        datetime.strptime(date_str.strip(), "%d/%m/%Y")
        return True
    except ValueError:
        return False

def is_valid_internal_date(date_str: str) -> bool:
    """
    Check if a date string is in valid yyyy-mm-dd format.
    
    Args:
        date_str: Date string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not date_str or not date_str.strip():
        return False
    
    try:
        datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return True
    except ValueError:
        return False