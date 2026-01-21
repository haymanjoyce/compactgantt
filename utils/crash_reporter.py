"""Crash reporting and telemetry system."""
import sys
import traceback
import platform
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import QMessageBox, QApplication
from PyQt5.QtCore import Qt


logger = logging.getLogger(__name__)


class CrashReporter:
    """Handles crash detection, reporting, and telemetry."""
    
    def __init__(self, app_name: str = "Compact Gantt", app_version: str = "1.0.0", 
                 enable_reporting: bool = True):
        """Initialize crash reporter.
        
        Args:
            app_name: Application name
            app_version: Application version
            enable_reporting: Whether crash reporting is enabled
        """
        self.app_name = app_name
        self.app_version = app_version
        self.enable_reporting = enable_reporting
        self.crashes_dir = Path(__file__).parent.parent / "logs" / "crashes"
        self.crashes_dir.mkdir(parents=True, exist_ok=True)
        self._original_excepthook = sys.excepthook
        self._qt_exception_occurred = False
        
    def install_handlers(self):
        """Install global exception handlers."""
        sys.excepthook = self._handle_exception
        
        # Install Qt exception handler
        try:
            from PyQt5.QtCore import qInstallMessageHandler
            qInstallMessageHandler(self._handle_qt_message)
        except ImportError:
            pass  # Qt message handler not available
    
    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle unhandled Python exceptions.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        # Don't handle KeyboardInterrupt or SystemExit
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        if issubclass(exc_type, SystemExit):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Generate crash report
        crash_report = self._generate_crash_report(exc_type, exc_value, exc_traceback)
        
        # Save crash report
        if self.enable_reporting:
            self._save_crash_report(crash_report)
        
        # Log the exception
        logger.critical(
            f"Unhandled exception: {exc_type.__name__}: {exc_value}",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        
        # Show user-friendly dialog
        self._show_crash_dialog(crash_report)
        
        # Call original exception handler
        self._original_excepthook(exc_type, exc_value, exc_traceback)
    
    def _handle_qt_message(self, msg_type, context, message):
        """Handle Qt messages (warnings, critical errors).
        
        Args:
            msg_type: Qt message type
            context: Message context
            message: Message text
        """
        # Only handle critical Qt errors
        if msg_type == Qt.CriticalMsg:
            if not self._qt_exception_occurred:
                self._qt_exception_occurred = True
                logger.critical(f"Qt Critical Error: {message} (Context: {context})")
                # Generate a crash report for Qt errors
                crash_report = self._generate_qt_crash_report(message, context)
                if self.enable_reporting:
                    self._save_crash_report(crash_report)
                self._show_crash_dialog(crash_report)
    
    def _generate_crash_report(self, exc_type, exc_value, exc_traceback) -> Dict[str, Any]:
        """Generate a crash report dictionary.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
            
        Returns:
            Dictionary containing crash report data
        """
        timestamp = datetime.now().isoformat()
        
        # Get system information
        system_info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
        }
        
        # Get PyQt5 version if available
        try:
            import PyQt5
            system_info["pyqt5_version"] = PyQt5.QtCore.PYQT_VERSION_STR
        except Exception:
            system_info["pyqt5_version"] = "Unknown"
        
        # Format traceback
        traceback_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        traceback_text = "".join(traceback_lines)
        
        return {
            "timestamp": timestamp,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "exception_type": exc_type.__name__,
            "exception_message": str(exc_value),
            "traceback": traceback_text,
            "system_info": system_info,
        }
    
    def _generate_qt_crash_report(self, message: str, context) -> Dict[str, Any]:
        """Generate a crash report for Qt errors.
        
        Args:
            message: Qt error message
            context: Qt message context
            
        Returns:
            Dictionary containing crash report data
        """
        timestamp = datetime.now().isoformat()
        
        system_info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "python_version": platform.python_version(),
        }
        
        try:
            import PyQt5
            system_info["pyqt5_version"] = PyQt5.QtCore.PYQT_VERSION_STR
        except Exception:
            system_info["pyqt5_version"] = "Unknown"
        
        return {
            "timestamp": timestamp,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "exception_type": "QtCriticalError",
            "exception_message": message,
            "context": str(context),
            "system_info": system_info,
        }
    
    def _save_crash_report(self, crash_report: Dict[str, Any]):
        """Save crash report to file.
        
        Args:
            crash_report: Crash report dictionary
        """
        try:
            timestamp_str = crash_report["timestamp"].replace(":", "-").split(".")[0]
            filename = f"crash_{timestamp_str}.txt"
            filepath = self.crashes_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"{self.app_name} Crash Report\n")
                f.write("=" * 80 + "\n\n")
                f.write(f"Timestamp: {crash_report['timestamp']}\n")
                f.write(f"Version: {crash_report['app_version']}\n")
                f.write(f"Exception Type: {crash_report['exception_type']}\n")
                f.write(f"Exception Message: {crash_report['exception_message']}\n\n")
                
                f.write("System Information:\n")
                f.write("-" * 80 + "\n")
                for key, value in crash_report['system_info'].items():
                    f.write(f"  {key}: {value}\n")
                f.write("\n")
                
                if 'traceback' in crash_report:
                    f.write("Traceback:\n")
                    f.write("-" * 80 + "\n")
                    f.write(crash_report['traceback'])
                elif 'context' in crash_report:
                    f.write("Context:\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"  {crash_report['context']}\n")
                
                f.write("\n" + "=" * 80 + "\n")
            
            logger.info(f"Crash report saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save crash report: {e}", exc_info=True)
    
    def _show_crash_dialog(self, crash_report: Dict[str, Any]):
        """Show user-friendly crash dialog.
        
        Args:
            crash_report: Crash report dictionary
        """
        try:
            app = QApplication.instance()
            if app is None:
                return  # No Qt application running
            
            message = (
                f"An unexpected error occurred in {self.app_name}.\n\n"
                f"Error: {crash_report['exception_type']}\n"
                f"{crash_report['exception_message']}\n\n"
                "The error has been logged. If this problem persists, "
                "please report it with the crash report file from the logs/crashes directory."
            )
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Application Error")
            msg_box.setText("An unexpected error occurred")
            msg_box.setInformativeText(message)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.exec_()
        except Exception as e:
            # Fallback if dialog fails
            logger.error(f"Failed to show crash dialog: {e}", exc_info=True)
            print(f"\n{'='*80}")
            print(f"CRASH REPORT")
            print(f"{'='*80}")
            print(f"Error: {crash_report['exception_type']}")
            print(f"Message: {crash_report['exception_message']}")
            print(f"See crash report in: {self.crashes_dir}")
            print(f"{'='*80}\n")
