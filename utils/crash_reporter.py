"""Crash reporting and telemetry system."""
import sys
import os
import traceback
import platform
import logging
import urllib.parse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import QMessageBox, QApplication, QPushButton
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices, QClipboard


logger = logging.getLogger(__name__)


class CrashReporter:
    """Handles crash detection, reporting, and telemetry."""
    
    def __init__(self, app_name: str = "Compact Gantt", app_version: str = "1.0.0", 
                 enable_reporting: bool = True, crash_report_email: str = ""):
        """Initialize crash reporter.
        
        Args:
            app_name: Application name
            app_version: Application version
            enable_reporting: Whether crash reporting is enabled
            crash_report_email: Email address for crash report recipient (optional)
        """
        self.app_name = app_name
        self.app_version = app_version
        self.enable_reporting = enable_reporting
        self.crash_report_email = crash_report_email
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
        crash_filepath = None
        if self.enable_reporting:
            crash_filepath = self._save_crash_report(crash_report)
            crash_report['filepath'] = crash_filepath
        
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
                crash_filepath = None
                if self.enable_reporting:
                    crash_filepath = self._save_crash_report(crash_report)
                    crash_report['filepath'] = crash_filepath
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
    
    def _save_crash_report(self, crash_report: Dict[str, Any]) -> Optional[Path]:
        """Save crash report to file.
        
        Args:
            crash_report: Crash report dictionary
            
        Returns:
            Path to saved crash report file, or None if save failed
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
            return filepath
        except Exception as e:
            logger.error(f"Failed to save crash report: {e}", exc_info=True)
            return None
    
    def _show_crash_dialog(self, crash_report: Dict[str, Any]):
        """Show user-friendly crash dialog with options to send, view, or copy report.
        
        Args:
            crash_report: Crash report dictionary (may include 'filepath' key)
        """
        try:
            app = QApplication.instance()
            if app is None:
                return  # No Qt application running
            
            crash_filepath = crash_report.get('filepath')
            message = (
                f"An unexpected error occurred in {self.app_name}.\n\n"
                f"Error: {crash_report['exception_type']}\n"
                f"{crash_report['exception_message']}\n\n"
                "The error has been logged. You can send a crash report to help improve the application."
            )
            
            if crash_filepath:
                message += f"\n\nCrash report saved to:\n{crash_filepath}"
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("Application Error")
            msg_box.setText("An unexpected error occurred")
            msg_box.setInformativeText(message)
            
            # Add custom buttons
            send_button = QPushButton("Send Report")
            view_button = QPushButton("View Report")
            copy_button = QPushButton("Copy to Clipboard")
            ok_button = msg_box.addButton(QMessageBox.Ok)
            
            if crash_filepath:
                msg_box.addButton(send_button, QMessageBox.ActionRole)
                msg_box.addButton(view_button, QMessageBox.ActionRole)
                msg_box.addButton(copy_button, QMessageBox.ActionRole)
            
            msg_box.setDefaultButton(ok_button)
            msg_box.exec_()
            
            # Handle button clicks
            clicked_button = msg_box.clickedButton()
            if clicked_button == send_button:
                self._open_email_client(crash_report, crash_filepath)
            elif clicked_button == view_button:
                self._open_crash_report_file(crash_filepath)
            elif clicked_button == copy_button:
                self._copy_crash_report_to_clipboard(crash_report, crash_filepath)
        except Exception as e:
            # Fallback if dialog fails
            logger.error(f"Failed to show crash dialog: {e}", exc_info=True)
            print(f"\n{'='*80}")
            print(f"CRASH REPORT")
            print(f"{'='*80}")
            print(f"Error: {crash_report['exception_type']}")
            print(f"Message: {crash_report['exception_message']}")
            crash_filepath = crash_report.get('filepath')
            if crash_filepath:
                print(f"See crash report in: {crash_filepath}")
            else:
                print(f"See crash report in: {self.crashes_dir}")
            print(f"{'='*80}\n")
    
    def _open_email_client(self, crash_report: Dict[str, Any], crash_filepath: Optional[Path]):
        """Open default email client with pre-filled crash report.
        
        Args:
            crash_report: Crash report dictionary
            crash_filepath: Path to crash report file
        """
        try:
            # Build email subject
            subject = f"{self.app_name} Crash Report - {crash_report['exception_type']}"
            
            # Build email body
            body_lines = [
                f"Crash Report for {self.app_name}",
                "",
                f"Version: {crash_report['app_version']}",
                f"Timestamp: {crash_report['timestamp']}",
                f"Exception Type: {crash_report['exception_type']}",
                f"Exception Message: {crash_report['exception_message']}",
                "",
                "System Information:",
            ]
            for key, value in crash_report['system_info'].items():
                body_lines.append(f"  {key}: {value}")
            
            body_lines.append("")
            body_lines.append("Please attach the crash report file from:")
            if crash_filepath:
                body_lines.append(str(crash_filepath))
            else:
                body_lines.append(str(self.crashes_dir))
            
            body = "\n".join(body_lines)
            
            # Copy email content to clipboard
            app = QApplication.instance()
            if app:
                clipboard = app.clipboard()
                email_content = f"Subject: {subject}\n\n{body}"
                clipboard.setText(email_content)
            
            # Show instructions dialog
            recipient = self.crash_report_email if self.crash_report_email else ""
            
            instructions = (
                "Email content has been copied to your clipboard.\n\n"
                "To send the crash report:\n"
                "1. Open your email (Gmail, Outlook, etc.)\n"
                "2. Paste the content (Ctrl+V)\n"
                "3. Attach the crash report file:\n"
            )
            
            if crash_filepath:
                instructions += f"   {crash_filepath}\n\n"
            else:
                instructions += f"   {self.crashes_dir}\n\n"
            
            if recipient:
                instructions += f"4. Send to: {recipient}\n\n"
                instructions += "Click 'Open Gmail' to open Gmail compose page, or click 'OK' to continue manually."
            else:
                instructions += "4. Enter the recipient email address\n\n"
                instructions += "Click 'Open Gmail' to open Gmail compose page, or click 'OK' to continue manually."
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Send Crash Report")
            msg_box.setText("Email content copied to clipboard")
            msg_box.setInformativeText(instructions)
            
            # Add buttons
            open_gmail_button = QPushButton("Open Gmail")
            ok_button = msg_box.addButton(QMessageBox.Ok)
            msg_box.addButton(open_gmail_button, QMessageBox.ActionRole)
            msg_box.setDefaultButton(ok_button)
            
            msg_box.exec_()
            
            # Handle button clicks
            clicked_button = msg_box.clickedButton()
            if clicked_button == open_gmail_button:
                # Open Gmail compose page
                if recipient:
                    gmail_url = f"https://mail.google.com/mail/?view=cm&to={urllib.parse.quote(recipient)}&su={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                else:
                    gmail_url = f"https://mail.google.com/mail/?view=cm&su={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
                QDesktopServices.openUrl(QUrl(gmail_url))
                # Don't try mailto: if user clicked "Open Gmail" - we've already provided the solution
            else:
                # User clicked OK - try mailto: as fallback for users with local email clients
                try:
                    params = {
                        'subject': subject,
                        'body': body,
                    }
                    if recipient:
                        mailto_url = f"mailto:{recipient}?{urllib.parse.urlencode(params)}"
                    else:
                        mailto_url = f"mailto:?{urllib.parse.urlencode(params)}"
                    # Try mailto, but don't show error if it fails
                    QDesktopServices.openUrl(QUrl(mailto_url))
                except Exception:
                    pass  # Ignore mailto failures
            
            logger.info(f"Prepared crash report email (copied to clipboard)")
        except Exception as e:
            logger.error(f"Failed to prepare email: {e}", exc_info=True)
            # Fallback: show message
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Email Client")
            msg_box.setText("Could not prepare email automatically.")
            if crash_filepath:
                msg_box.setInformativeText(
                    f"Please send an email with the crash report file attached:\n{crash_filepath}"
                )
            msg_box.exec_()
    
    def _open_crash_report_file(self, crash_filepath: Optional[Path]):
        """Open crash report file in default text editor.
        
        Args:
            crash_filepath: Path to crash report file
        """
        if not crash_filepath or not crash_filepath.exists():
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("File Not Found")
            msg_box.setText("Crash report file not found.")
            msg_box.exec_()
            return
        
        try:
            if sys.platform == 'win32':
                os.startfile(str(crash_filepath))
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', str(crash_filepath)])
            else:  # Linux
                subprocess.run(['xdg-open', str(crash_filepath)])
            logger.info(f"Opened crash report file: {crash_filepath}")
        except Exception as e:
            logger.error(f"Failed to open crash report file: {e}", exc_info=True)
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Error")
            msg_box.setText(f"Could not open crash report file:\n{crash_filepath}")
            msg_box.exec_()
    
    def _copy_crash_report_to_clipboard(self, crash_report: Dict[str, Any], crash_filepath: Optional[Path]):
        """Copy crash report content to clipboard.
        
        Args:
            crash_report: Crash report dictionary
            crash_filepath: Path to crash report file
        """
        try:
            app = QApplication.instance()
            if app is None:
                return
            
            clipboard = app.clipboard()
            
            # Build clipboard text
            text_lines = [
                f"{self.app_name} Crash Report",
                "=" * 80,
                "",
                f"Timestamp: {crash_report['timestamp']}",
                f"Version: {crash_report['app_version']}",
                f"Exception Type: {crash_report['exception_type']}",
                f"Exception Message: {crash_report['exception_message']}",
                "",
                "System Information:",
                "-" * 80,
            ]
            for key, value in crash_report['system_info'].items():
                text_lines.append(f"  {key}: {value}")
            
            text_lines.append("")
            if 'traceback' in crash_report:
                text_lines.append("Traceback:")
                text_lines.append("-" * 80)
                text_lines.append(crash_report['traceback'])
            elif 'context' in crash_report:
                text_lines.append("Context:")
                text_lines.append("-" * 80)
                text_lines.append(f"  {crash_report['context']}")
            
            if crash_filepath:
                text_lines.append("")
                text_lines.append(f"Full crash report file: {crash_filepath}")
            
            clipboard.setText("\n".join(text_lines))
            logger.info("Copied crash report to clipboard")
            
            # Show confirmation
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle("Copied")
            msg_box.setText("Crash report copied to clipboard.")
            msg_box.exec_()
        except Exception as e:
            logger.error(f"Failed to copy crash report to clipboard: {e}", exc_info=True)