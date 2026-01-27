from dataclasses import dataclass
from typing import Dict


# Mapping of display names to (qt_format, python_format) tuples
DATE_FORMAT_OPTIONS: Dict[str, tuple] = {
    "dd/MM/yyyy": ("dd/MM/yyyy", "%d/%m/%Y"),  # British/European (e.g., 01/01/2025)
    "MM/dd/yyyy": ("MM/dd/yyyy", "%m/%d/%Y"),  # US (e.g., 01/01/2025)
    "yyyy-MM-dd": ("yyyy-MM-dd", "%Y-%m-%d"),  # ISO (e.g., 2025-01-01)
    "dd-MM-yyyy": ("dd-MM-yyyy", "%d-%m-%Y"),  # European with dashes (e.g., 01-01-2025)
    "dd MMM yyyy": ("dd MMM yyyy", "%d %b %Y"),  # Long format (e.g., 01 Jan 2025)
}


@dataclass
class DateConfig:
    """Configuration for date formats used throughout the application.
    
    This centralizes date format strings to ensure consistency across:
    - UI date pickers (Qt QDateEdit)
    - Date parsing and validation (Python strptime/strftime)
    - Excel import/export
    - Internal storage (always ISO format: yyyy-mm-dd)
    """
    # Qt format string for QDateEdit displayFormat (e.g., "dd/MM/yyyy")
    display_format_qt: str = "dd/MM/yyyy"
    
    # Python format string for strptime/strftime (e.g., "%d/%m/%Y")
    display_format_python: str = "%d/%m/%Y"
    
    # Internal storage format (ISO format, always yyyy-mm-dd)
    internal_format: str = "%Y-%m-%d"
    
    def get_qt_format(self) -> str:
        """Get Qt format string for QDateEdit widgets."""
        return self.display_format_qt
    
    def get_python_format(self) -> str:
        """Get Python format string for strptime/strftime operations."""
        return self.display_format_python
    
    def get_internal_format(self) -> str:
        """Get internal storage format (always ISO: yyyy-mm-dd)."""
        return self.internal_format
    
    @staticmethod
    def _qt_to_python_format(qt_format: str) -> str:
        """Convert Qt date format string to Python strftime format string.
        
        Qt format -> Python format mappings:
        - d, dd -> %d (day)
        - M -> %m (month number, 1-12)
        - MM -> %m (month number, 01-12)
        - MMM -> %b (abbreviated month name, Jan-Dec)
        - MMMM -> %B (full month name, January-December)
        - yy -> %y (2-digit year)
        - yyyy -> %Y (4-digit year)
        
        Args:
            qt_format: Qt date format string (e.g., "M", "MMM", "dd/MM/yyyy")
            
        Returns:
            Python strftime format string (e.g., "%m", "%b", "%d/%m/%Y")
        """
        # Mapping of Qt format patterns to Python format
        # Order matters: longer patterns must come before shorter ones
        replacements = [
            ("yyyy", "%Y"),  # 4-digit year (must come before yy)
            ("yy", "%y"),    # 2-digit year
            ("MMMM", "%B"),  # Full month name (must come before MMM)
            ("MMM", "%b"),   # Abbreviated month name (must come before MM)
            ("MM", "%m"),    # 2-digit month (must come before M)
            ("M", "%m"),     # 1-digit month
            ("dd", "%d"),    # 2-digit day (must come before d)
            ("d", "%d"),     # 1-digit day
        ]
        
        python_format = qt_format
        for qt_pattern, py_pattern in replacements:
            python_format = python_format.replace(qt_pattern, py_pattern)
        
        return python_format
    
    @classmethod
    def from_custom_format(cls, qt_format: str) -> 'DateConfig':
        """Create DateConfig from a custom Qt format string.
        
        Args:
            qt_format: Custom Qt date format string (e.g., "M", "MMM", "dd MMM yyyy")
            
        Returns:
            DateConfig instance with the specified custom format
        """
        python_format = cls._qt_to_python_format(qt_format)
        return cls(
            display_format_qt=qt_format,
            display_format_python=python_format,
            internal_format="%Y-%m-%d"  # Always ISO format for internal storage
        )
    
    @classmethod
    def from_format_name(cls, format_name: str) -> 'DateConfig':
        """Create DateConfig from a format name (predefined or custom).
        
        First checks if format_name is in DATE_FORMAT_OPTIONS.
        If not found, treats it as a custom Qt format string.
        
        Args:
            format_name: Format name from DATE_FORMAT_OPTIONS or custom Qt format string
            
        Returns:
            DateConfig instance with the specified format
        """
        # Check if it's a predefined format
        if format_name in DATE_FORMAT_OPTIONS:
            qt_format, python_format = DATE_FORMAT_OPTIONS[format_name]
            return cls(
                display_format_qt=qt_format,
                display_format_python=python_format,
                internal_format="%Y-%m-%d"  # Always ISO format for internal storage
            )
        
        # Otherwise, treat as custom Qt format
        return cls.from_custom_format(format_name)
    
    def get_format_name(self) -> str:
        """Get the format name (key) that matches this DateConfig's formats.
        
        Returns:
            Format name if found in DATE_FORMAT_OPTIONS, or None if no match
        """
        for format_name, (qt_fmt, py_fmt) in DATE_FORMAT_OPTIONS.items():
            if self.display_format_qt == qt_fmt and self.display_format_python == py_fmt:
                return format_name
        return None
