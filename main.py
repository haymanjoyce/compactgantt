import sys
import os
import msvcrt  # For Windows file locking
import atexit
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSharedMemory
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from ui.main_window import MainWindow
from models.project import ProjectData
from services.gantt_chart_service import GanttChartService
from config.app_config import AppConfig
from ui.svg_display import SvgDisplay
from utils.logging_config import setup_logging
from utils.crash_reporter import CrashReporter
import logging


# Global lock file handle
_lock_file = None
_lock_file_path = None


def acquire_lock():
    """Try to acquire a file-based lock. Returns True if lock acquired, False otherwise."""
    global _lock_file, _lock_file_path
    
    # Use temp directory for lock file
    temp_dir = Path(os.environ.get('TEMP', os.environ.get('TMP', '/tmp')))
    _lock_file_path = temp_dir / "compact_gantt_instance.lock"
    
    try:
        # Try to create/open the lock file exclusively
        _lock_file = open(_lock_file_path, 'w')
        try:
            # Try to acquire exclusive lock (non-blocking)
            msvcrt.locking(_lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            # Successfully acquired lock - write PID
            _lock_file.write(str(os.getpid()))
            _lock_file.flush()
            # Register cleanup
            atexit.register(release_lock)
            return True
        except IOError:
            # Lock is held by another process
            _lock_file.close()
            _lock_file = None
            return False
    except Exception as e:
        # Failed to create lock file
        print(f"Warning: Could not create lock file: {e}")
        if _lock_file:
            _lock_file.close()
            _lock_file = None
        return False


def release_lock():
    """Release the file lock."""
    global _lock_file, _lock_file_path
    if _lock_file:
        try:
            msvcrt.locking(_lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            _lock_file.close()
            if _lock_file_path and _lock_file_path.exists():
                _lock_file_path.unlink()
        except Exception:
            pass
        _lock_file = None


def notify_existing_instance():
    """Send a message to the existing instance to bring itself to front."""
    # Need a minimal QApplication for QLocalSocket to work
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    socket = QLocalSocket()
    socket.connectToServer("compact_gantt_single_instance")
    if socket.waitForConnected(1000):
        socket.write(b"activate")
        socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        return True
    return False


def main():
    # Set up centralized logging first
    setup_logging(logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Check for existing instance using file lock BEFORE creating QApplication
    lock_acquired = acquire_lock()
    if not lock_acquired:
        # Another instance is running - notify it and exit immediately
        print("Another instance of Compact Gantt is already running.")
        notify_existing_instance()
        os._exit(0)  # Force immediate exit, bypassing cleanup handlers
    
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    
    # Set up crash reporting after QApplication is created
    app_config = AppConfig()  # Create early to get crash reporting preference
    app_version = "1.0.0"  # TODO: Move to config or version file
    crash_reporter = CrashReporter(
        app_name="Compact Gantt",
        app_version=app_version,
        enable_reporting=app_config.general.enable_crash_reporting
    )
    crash_reporter.install_handlers()

    # After crash_reporter.install_handlers()
    if False:  # Set to True to test, then back to False
        raise ValueError("Test crash reporting")

    logger.info(f"Crash reporting {'enabled' if app_config.general.enable_crash_reporting else 'disabled'}")
    
    # Also set up QSharedMemory for backward compatibility with notification system
    shared_memory = QSharedMemory("compact_gantt_single_instance")
    if not shared_memory.create(1):
        # Shouldn't happen if file lock worked, but be safe
        if shared_memory.error() == QSharedMemory.AlreadyExists:
            release_lock()
            os._exit(0)
    
    # Set up local server to receive activation requests from other instances
    local_server = QLocalServer()
    if local_server.listen("compact_gantt_single_instance"):
        def handle_new_connection():
            """Handle connection from another instance trying to start."""
            socket = local_server.nextPendingConnection()
            if socket:
                socket.readyRead.connect(lambda: activate_window_and_close_socket(socket))
        
        def activate_window_and_close_socket(socket):
            """Bring window to front and close the socket."""
            # Find and activate the main window
            for window in app.allWindows():
                if isinstance(window, MainWindow):
                    window.raise_()
                    window.activateWindow()
                    window.showNormal()  # Restore if minimized
                    break
            socket.close()
            socket.deleteLater()
        
        local_server.newConnection.connect(handle_new_connection)
    else:
        # Server already exists - another instance is running
        # This shouldn't happen if file lock worked, but be safe
        shared_memory.detach()
        release_lock()
        os._exit(0)
    
    # Set AppUserModelID on Windows to prevent grouping with Python
    if sys.platform == 'win32':
        try:
            import ctypes
            # Set a unique AppUserModelID so Windows doesn't group with Python
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('com.richardhaymanjoyce.compactgantt.1')
        except Exception:
            pass  # Fail silently if this doesn't work
    
    # Use ICO so Windows taskbar shows the custom logo
    icon_path = Path(__file__).parent / "assets" / "favicon.ico"
    app.setWindowIcon(QIcon(str(icon_path)))
    # app_config already created above for crash reporter
    project_data = ProjectData(app_config)  # Pass the shared instance
    gantt_chart_service = GanttChartService(app_config)  # Pass the shared instance
    svg_display = SvgDisplay(app_config)
    data_entry = MainWindow(project_data, svg_display, app_config)  # Pass project_data, svg_display, and app_config

    def handle_svg_path(svg_path):
        if svg_path:
            svg_display.load_svg(svg_path)
        else:
            print("No SVG generated due to invalid data")

    data_entry.data_updated.connect(gantt_chart_service.generate_svg)
    gantt_chart_service.svg_generated.connect(handle_svg_path)
    data_entry.show()
    
    # Clean up on exit
    exit_code = app.exec_()
    local_server.close()
    shared_memory.detach()
    release_lock()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()