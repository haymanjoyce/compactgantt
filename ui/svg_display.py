from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QScrollArea, QPushButton, QHBoxLayout, QLabel, QApplication, QStatusBar, QWidget, QAction, QFileDialog, QMessageBox
)
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPalette
from pathlib import Path
from PyQt5.QtCore import Qt, QSize
import os
from config.app_config import AppConfig
from ui.window_utils import move_window_according_to_preferences

# --- Main SVG Display Window ---
class SvgDisplay(QMainWindow):
    def __init__(self, app_config, initial_path=None, reference_window=None):
        super().__init__()
        
        # Set window flags to match MainWindow (minimize, maximize, close)
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | 
                           Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        
        self.setWindowTitle("Compact Gantt | Chart Display Window")
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "favicon.ico"
        self.setWindowIcon(QIcon(str(icon_path)))

        width = app_config.general.svg_display_width
        height = app_config.general.svg_display_height
        self.resize(width, height)
        
        # Store SVG path for saving
        self._svg_path = None

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
        btn_layout.setContentsMargins(0, 4, 0, 0)
        btn_layout.addWidget(self.zoom_in_btn)
        btn_layout.addWidget(self.zoom_out_btn)
        btn_layout.addWidget(self.fit_btn)

        # Create central widget
        central_widget = QWidget()
        self.layout = QVBoxLayout(central_widget)
        self.layout.addWidget(self.scroll_area)  # Graphic first
        self.layout.addLayout(btn_layout)  # Buttons below the graphic
        self.setCentralWidget(central_widget)
        
        # Create menu bar
        self.menu_bar = self.menuBar()
        file_menu = self.menu_bar.addMenu("File")
        
        self.save_png_action = QAction("Save Image (PNG)", self)
        self.save_png_action.setShortcut("Ctrl+Shift+S")
        self.save_png_action.triggered.connect(lambda: self.save_as_raster("PNG"))
        file_menu.addAction(self.save_png_action)
        
        self.save_jpeg_action = QAction("Save Image (JPEG)", self)
        self.save_jpeg_action.setShortcut("Ctrl+Shift+J")
        self.save_jpeg_action.triggered.connect(lambda: self.save_as_raster("JPEG"))
        file_menu.addAction(self.save_jpeg_action)
        
        # Create status bar using reserved area (like MainWindow)
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                border-top: 1px solid #D3D3D3;
                padding: 3px;
                background: #F8F9FA;
            }
        """)
        self.status_bar.showMessage("100%")

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
            self._svg_path = absolute_path  # Store path for saving
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
            # Update _zoom to match the new fit scale so zooming continues smoothly
            area_size = self.scroll_area.viewport().size()
            if self._svg_size.width() > 0 and self._svg_size.height() > 0:
                fit_scale = min(
                    area_size.width() / self._svg_size.width(),
                    area_size.height() / self._svg_size.height(),
                    1.0
                )
                self._zoom = fit_scale
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
        # Update _zoom to match the current fit scale so zooming continues smoothly
        area_size = self.scroll_area.viewport().size()
        if self._svg_size.width() > 0 and self._svg_size.height() > 0:
            fit_scale = min(
                area_size.width() / self._svg_size.width(),
                area_size.height() / self._svg_size.height(),
                1.0
            )
            self._zoom = fit_scale
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

    def save_as_raster(self, format_type="PNG"):
        """Save the SVG as a raster image (PNG or JPEG)."""
        if not self._svg_path or not self.svg_renderer.isValid():
            QMessageBox.warning(self, "No Image", "No SVG image loaded to save.")
            return
        
        # Determine file extension and filter based on format
        if format_type == "JPEG":
            default_ext = ".jpg"
            file_filter = "JPEG Images (*.jpg *.jpeg)"
        else:  # PNG
            default_ext = ".png"
            file_filter = "PNG Images (*.png)"
        
        # Show file dialog for saving
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Save Image As {format_type}",
            "",
            file_filter
        )
        
        if not file_path:
            return
        
        # Ensure correct extension
        if not file_path.endswith(default_ext):
            file_path += default_ext
        
        try:
            # Render SVG at native size for high quality
            native_size = self._svg_size
            pixmap = QPixmap(native_size)
            pixmap.fill(Qt.white)  # White background for raster formats
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            self.svg_renderer.render(painter)
            painter.end()
            
            # Save the pixmap
            if pixmap.save(file_path, format_type):
                self.status_bar.showMessage(f"Image saved as {format_type}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to save image to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving image: {str(e)}")
