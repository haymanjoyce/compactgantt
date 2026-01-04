from dataclasses import dataclass, field
from PyQt5.QtGui import QColor


@dataclass
class UIConfig:
    """Configuration for UI styling and appearance."""
    # Read-only cell background color (light gray)
    read_only_bg_color: QColor = field(default_factory=lambda: QColor(240, 240, 240))
    
    # Table header border color
    table_header_border_color: str = "#c0c0c0"
    
    @property
    def table_header_stylesheet(self) -> str:
        """Generate table header stylesheet with border styling."""
        return f"""
            QHeaderView::section {{
                border-bottom: 1px solid {self.table_header_border_color};
                border-top: none;
                border-left: none;
                border-right: none;
            }}
        """

