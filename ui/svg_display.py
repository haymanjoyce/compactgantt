from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QScrollArea, QPushButton, QHBoxLayout, QLabel, QApplication
)
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPalette
from PyQt5.QtCore import Qt, QSize
import os
from config.app_config import AppConfig
from ui.window_utils import move_window_to_screen_center, move_window_to_screen_right_of

# --- Custom Centered Scroll Area ---
class CenteredScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.centerContent()

    def centerContent(self):
        widget = self.widget()
        if widget is None:
            return
        area_w = self.viewport().width()
        area_h = self.viewport().height()
        w = widget.width()
        h = widget.height()
        x = max((area_w - w) // 2, 0)
        y = max((area_h - h) // 2, 0)
        widget.move(x, y)

# --- Zoomable SVG Widget ---
class ZoomableSvgWidget(QSvgRenderer):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._zoom = 1.0

    def setZoom(self, zoom):
        self._zoom = zoom
        self.update_size()
        self.update()

    def zoomIn(self):
        self.setZoom(self._zoom * 1.2)

    def zoomOut(self):
        self.setZoom(self._zoom / 1.2)

    def update_size(self):
        base = self.defaultSize()
        self.setFixedSize(int(base.width() * self._zoom), int(base.height() * self._zoom))

    def sizeHint(self):
        base = self.defaultSize()
        return QSize(int(base.width() * self._zoom), int(base.height() * self._zoom))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.scale(self._zoom, self._zoom)
        self.render(painter)

# --- Main SVG Display Window ---
class FitToWindowSvgDisplay(QDialog):
    def __init__(self, app_config, initial_path=None, reference_window=None):
        super().__init__()
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

        # Add zoom buttons (optional, for manual zoom)
        zoom_in_btn = QPushButton("Zoom In")
        zoom_out_btn = QPushButton("Zoom Out")
        fit_btn = QPushButton("Fit to Window")
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_out_btn.clicked.connect(self.zoom_out)
        fit_btn.clicked.connect(self.fit_to_window)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(zoom_in_btn)
        btn_layout.addWidget(zoom_out_btn)
        btn_layout.addWidget(fit_btn)

        self.layout = QVBoxLayout()
        self.layout.addLayout(btn_layout)
        self.layout.addWidget(self.scroll_area)
        self.setLayout(self.layout)

        self._zoom = 1.0
        self._fit_to_window = True
        self._svg_size = QSize(1, 1)

        if initial_path and os.path.exists(initial_path):
            self.load_svg(initial_path)

        # Try to open on screen 2 (index 1)
        app = QApplication.instance()
        screens = app.screens()
        if len(screens) > 1:
            move_window_to_screen_center(self, screen_number=2, width=width, height=height)
        else:
            # Open to the right of DataEntryWindow on screen 1
            if reference_window is not None:
                move_window_to_screen_right_of(self, reference_window, screen_number=0, width=width, height=height)
            else:
                move_window_to_screen_center(self, screen_number=2, width=width, height=height)

    def load_svg(self, svg_path):
        absolute_path = os.path.abspath(svg_path)
        if os.path.exists(absolute_path):
            self.svg_renderer.load(absolute_path)
            self._svg_size = self.svg_renderer.defaultSize()
            self._zoom = 1.0
            self._fit_to_window = True
            self.update_image()
            self.show()
        else:
            print(f"SVG file not found: {absolute_path}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._fit_to_window:
            self.update_image()

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

    def zoom_out(self):
        self._fit_to_window = False
        self._zoom /= 1.2
        self.update_image()

    def fit_to_window(self):
        self._fit_to_window = True
        self.update_image()

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
#     win = FitToWindowSvgDisplay(DummyConfig(), initial_path="svg/gantt_chart.svg")
#     win.show()
#     sys.exit(app.exec_())
