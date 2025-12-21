from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QScrollArea, QPushButton, QHBoxLayout, QLabel, QApplication, QStatusBar
)
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPalette
from PyQt5.QtCore import Qt, QSize
import os
from config.app_config import AppConfig
from ui.window_utils import move_window_according_to_preferences

# --- Main SVG Display Window ---
class SvgDisplay(QDialog):
    def __init__(self, app_config, initial_path=None, reference_window=None):
        super().__init__()
        
        # Set window flags to match MainWindow (minimize, maximize, close)
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | 
                           Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        
        self.setWindowTitle("SVG Display")
        self.setWindowIcon(QIcon("assets/logo.png"))

        width = app_config.general.svg_display_width
        height = app_config.general.svg_display_height
        self.resize(width, height)

        self.svg_renderer = QSvgRenderer()
        self.svg_label = QLabel()
        self.svg_label.setAlignment(Qt.AlignCenter)
        self.svg_label.setBackgroundRole(QPalette.Base)
        self.svg_label.setSizePolicy(self.svg_label.sizePolicy().horizontalPolicy(), self.svg_label.sizePolicy().verticalPolicy())

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(self.svg_label)
        self.scroll_area.setWidgetResizable(True)

        # Create zoom control buttons with styling
        self.zoom_in_btn = QPushButton("Zoom In")
        self.zoom_out_btn = QPushButton("Zoom Out")
        self.fit_btn = QPushButton("Fit to Window")
        
        # Add keyboard shortcuts
        self.zoom_in_btn.setShortcut("Ctrl++")
        self.zoom_out_btn.setShortcut("Ctrl+-")
        self.fit_btn.setShortcut("Ctrl+0")
        
        # Add tooltips
        self.zoom_in_btn.setToolTip("Zoom in (Ctrl++)")
        self.zoom_out_btn.setToolTip("Zoom out (Ctrl+-)")
        self.fit_btn.setToolTip("Fit to window (Ctrl+0)")
        
        # Connect signals
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.fit_btn.clicked.connect(self.fit_to_window)
        
        # Style buttons to match Update Image button in main window
        button_style = """
            QPushButton {
                padding: 8px;
            }
        """
        self.zoom_in_btn.setStyleSheet(button_style)
        self.zoom_out_btn.setStyleSheet(button_style)
        self.fit_btn.setStyleSheet(button_style)
        
        # Store button style for reuse
        self._button_style = button_style
        
        # Create button layout with spacing
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.setContentsMargins(8, 8, 8, 8)
        btn_layout.addWidget(self.zoom_in_btn)
        btn_layout.addWidget(self.zoom_out_btn)
        btn_layout.addWidget(self.fit_btn)

        # Create status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                border-top: 1px solid #D3D3D3;
                padding: 3px;
                background: #F8F9FA;
            }
        """)
        self.status_bar.showMessage("100%")

        self.layout = QVBoxLayout()
        self.layout.addLayout(btn_layout)
        self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(self.status_bar)  # Add status bar at the bottom
        self.setLayout(self.layout)

        self._zoom = 1.0
        self._fit_to_window = True
        self._svg_size = QSize(1, 1)

        if initial_path and os.path.exists(initial_path):
            self.load_svg(initial_path)
        else:
            # Initialize zoom label even if no SVG loaded
            self._update_zoom_label()

        # Position window according to user preferences
        move_window_according_to_preferences(
            self,
            app_config,
            width=width,
            height=height,
            window_type="svg_display"
        )

    def load_svg(self, svg_path):
        absolute_path = os.path.abspath(svg_path)
        if os.path.exists(absolute_path):
            self.svg_renderer.load(absolute_path)
            self._svg_size = self.svg_renderer.defaultSize()
            self._zoom = 1.0
            self._fit_to_window = True
            self.update_image()
            self._update_button_states()
            self._update_zoom_label()
            self.show()
        else:
            print(f"SVG file not found: {absolute_path}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._fit_to_window:
            self.update_image()
            self._update_zoom_label()

    def update_image(self):
        if self._fit_to_window:
            # Fit SVG to window, but do not scale up beyond native size
            area_size = self.scroll_area.viewport().size()
            scale = min(
                area_size.width() / self._svg_size.width(),
                area_size.height() / self._svg_size.height(),
                1.0  # Never scale up beyond native size
            )
        else:
            scale = self._zoom

        render_size = QSize(
            int(self._svg_size.width() * scale),
            int(self._svg_size.height() * scale)
        )
        pixmap = QPixmap(render_size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        self.svg_renderer.render(painter)
        painter.end()
        self.svg_label.setPixmap(pixmap)
        self.svg_label.resize(render_size)

    def zoom_in(self):
        self._fit_to_window = False
        self._zoom *= 1.2
        self.update_image()
        self._update_button_states()
        self._update_zoom_label()

    def zoom_out(self):
        self._fit_to_window = False
        self._zoom /= 1.2
        self.update_image()
        self._update_button_states()
        self._update_zoom_label()

    def fit_to_window(self):
        self._fit_to_window = True
        self.update_image()
        self._update_button_states()
        self._update_zoom_label()
    
    def _update_button_states(self):
        """Update button appearance based on current state."""
        # All buttons use the same style regardless of state
        # Use the stored button style to maintain consistency
        self.fit_btn.setStyleSheet(self._button_style)
    
    def _update_zoom_label(self):
        """Update zoom percentage display in status bar."""
        if self._fit_to_window:
            # Calculate actual scale when fitting
            area_size = self.scroll_area.viewport().size()
            if self._svg_size.width() > 0 and self._svg_size.height() > 0:
                scale = min(
                    area_size.width() / self._svg_size.width(),
                    area_size.height() / self._svg_size.height(),
                    1.0
                )
                self.status_bar.showMessage(f"{int(scale * 100)}% (Fit)")
            else:
                self.status_bar.showMessage("Fit")
        else:
            self.status_bar.showMessage(f"{int(self._zoom * 100)}%")

    def center_scroll_area_on_svg(self):
        area = self.scroll_area
        widget = self.svg_label
        h_bar = area.horizontalScrollBar()
        v_bar = area.verticalScrollBar()
        widget_center_x = widget.width() // 2
        widget_center_y = widget.height() // 2
        viewport_width = area.viewport().width()
        viewport_height = area.viewport().height()
        h_bar.setValue(widget_center_x - viewport_width // 2)
        v_bar.setValue(widget_center_y - viewport_height // 2)

# --- Example usage (uncomment for standalone test) ---
# if __name__ == "__main__":
#     import sys
#     class DummyConfig:
#         class General:
#             svg_display_width = 1200
#             svg_display_height = 800
#         general = General()
#     app = QApplication(sys.argv)
#     win = SvgDisplay(DummyConfig(), initial_path="svg/gantt_chart.svg")
#     win.show()
#     sys.exit(app.exec_())
