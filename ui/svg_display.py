from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QPushButton, QHBoxLayout, QWidget, QFileDialog, QMessageBox
)
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QImage
from pathlib import Path
from PyQt5.QtCore import Qt, QUrl
import os
import tempfile
import re
import logging
from config.app_config import AppConfig
from ui.window_utils import move_window_according_to_preferences

# --- Main SVG Display Window ---
class SvgDisplay(QMainWindow):
    def __init__(self, app_config, initial_path=None, reference_window=None):
        super().__init__()

        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint |
                           Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)

        self.setWindowTitle("Compact Gantt | Chart Display Window")
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "favicon.ico"
        self.setWindowIcon(QIcon(str(icon_path)))

        width = app_config.general.svg_display_width
        height = app_config.general.svg_display_height
        self.resize(width, height)

        self._svg_path = None

        self.web_view = QWebEngineView()

        button_style = "QPushButton { padding: 8px; }"

        self.save_svg_btn = QPushButton("Save SVG")
        self.save_image_btn = QPushButton("Save Image")
        self.save_svg_btn.setToolTip("Save as SVG")
        self.save_image_btn.setToolTip("Save as JPEG or PNG")
        self.save_svg_btn.clicked.connect(self.save_as_svg)
        self.save_image_btn.clicked.connect(self.save_as_raster)
        self.save_svg_btn.setStyleSheet(button_style)
        self.save_image_btn.setStyleSheet(button_style)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.setContentsMargins(0, 4, 0, 0)
        btn_layout.addWidget(self.save_svg_btn)
        btn_layout.addWidget(self.save_image_btn)

        central_widget = QWidget()
        self.layout = QVBoxLayout(central_widget)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.addWidget(self.web_view)
        self.layout.addLayout(btn_layout)
        self.setCentralWidget(central_widget)

        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                border-top: 1px solid #D3D3D3;
                padding: 3px;
                background: #F8F9FA;
            }
        """)

        if initial_path and os.path.exists(initial_path):
            self.load_svg(initial_path)

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
            self._svg_path = absolute_path
            with open(absolute_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            html = (
                "<!DOCTYPE html>"
                "<html><head><style>"
                "html, body { margin: 0; padding: 0; background: #ffffff; }"
                "</style></head><body>"
                + svg_content
                + "</body></html>"
            )
            base_url = QUrl.fromLocalFile(os.path.dirname(absolute_path) + "/")
            self.web_view.setHtml(html, base_url)
            if not self.isVisible():
                self.show()
        else:
            logging.warning(f"SVG file not found: {absolute_path}")

    def save_as_svg(self):
        if not self._svg_path or not os.path.exists(self._svg_path):
            QMessageBox.warning(self, "No Image", "No SVG image loaded to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save SVG", "", "SVG Files (*.svg)"
        )
        if not file_path:
            return

        if not file_path.lower().endswith(".svg"):
            file_path += ".svg"

        try:
            with open(self._svg_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            QMessageBox.information(self, "SVG Saved", f"SVG successfully saved:\n{file_path}")
            self.status_bar.showMessage("SVG saved")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving SVG: {str(e)}")

    def save_as_raster(self):
        if not self._svg_path or not os.path.exists(self._svg_path):
            QMessageBox.warning(self, "No Image", "No SVG image loaded to save.")
            return

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Image",
            "",
            "JPEG Images (*.jpg *.jpeg);;PNG Images (*.png)"
        )
        if not file_path:
            return

        if "PNG" in selected_filter:
            format_type = "PNG"
            if not file_path.lower().endswith(".png"):
                file_path += ".png"
        else:
            format_type = "JPEG"
            if not (file_path.lower().endswith(".jpg") or file_path.lower().endswith(".jpeg")):
                file_path += ".jpg"

        try:
            renderer = QSvgRenderer(self._svg_path)
            if not renderer.isValid():
                QMessageBox.warning(self, "Error", "Could not load SVG for export.")
                return
            native_size = renderer.defaultSize()

            if format_type == "PNG":
                try:
                    with open(self._svg_path, 'r', encoding='utf-8') as f:
                        svg_content = f.read()
                    pattern = r'<rect(?=[^>]*fill="white")(?=[^>]*x="0")(?=[^>]*y="0")[^>]*?/>'
                    modified_content = re.sub(pattern, '', svg_content, count=1)
                    temp_svg = tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False, encoding='utf-8')
                    temp_svg.write(modified_content)
                    temp_svg.close()
                    temp_renderer = QSvgRenderer(temp_svg.name)
                    image = QImage(native_size, QImage.Format_ARGB32)
                    image.fill(Qt.transparent)
                    painter = QPainter(image)
                    painter.setRenderHint(QPainter.Antialiasing)
                    temp_renderer.render(painter)
                    painter.end()
                    os.unlink(temp_svg.name)
                    success = image.save(file_path, format_type)
                except Exception as e:
                    logging.warning(f"Failed to modify SVG for transparency: {e}")
                    image = QImage(native_size, QImage.Format_ARGB32)
                    image.fill(Qt.transparent)
                    painter = QPainter(image)
                    painter.setRenderHint(QPainter.Antialiasing)
                    renderer.render(painter)
                    painter.end()
                    success = image.save(file_path, format_type)
            else:  # JPEG
                pixmap = QPixmap(native_size)
                pixmap.fill(Qt.white)
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                renderer.render(painter)
                painter.end()
                success = pixmap.save(file_path, format_type)

            if success:
                QMessageBox.information(
                    self,
                    "Image Saved",
                    f"Image successfully saved as {format_type}:\n{file_path}"
                )
                self.status_bar.showMessage(f"Image saved as {format_type}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to save image to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving image: {str(e)}")
