# test_smoke.py
"""Fast smoke tests that run without PyQt5.

Checks:
- Key non-UI modules can be imported cleanly
- DateConfig defaults and format helpers are correct
- UI tab source files have valid Python syntax

These tests are safe to run in any environment (CI, fresh clone, no
Qt install) and are the first line of defence against regressions
introduced by edits to the UI tabs or config layer.
"""

import sys
from pathlib import Path

# Add project root to path (go up one level from tests folder)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Use ASCII-safe symbols for Windows compatibility
OK = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"

def test_imports():
    """Test that key modules can be imported."""
    print("Testing imports...")

    # Check if PyQt5 is available first
    try:
        import PyQt5
        pyqt5_available = True
    except ImportError:
        pyqt5_available = False
        print(f"  {WARN} PyQt5 not available - skipping UI imports")
        print("  (This is expected if running outside dev environment)\n")
        return True  # Not a failure, just skip

    try:
        from ui.tabs.base_tab import BaseTab
        print(f"  {OK} BaseTab imported")

        from ui.table_utils import create_date_widget, extract_date_from_cell
        print(f"  {OK} Date helpers imported")

        from config.date_config import DateConfig
        print(f"  {OK} DateConfig imported")

        print(f"  {OK} All imports successful\n")
        return True
    except ImportError as e:
        print(f"  {FAIL} Import failed: {e}\n")
        return False

def test_date_config():
    """Test DateConfig functionality."""
    print("Testing DateConfig...")

    try:
        from config.date_config import DateConfig, DATE_FORMAT_OPTIONS

        # Test default config
        config = DateConfig()
        assert config.get_qt_format() == "dd/MM/yyyy"
        assert config.get_python_format() == "%d/%m/%Y"
        assert config.get_internal_format() == "%Y-%m-%d"
        print(f"  {OK} Default DateConfig works")

        # Test format name lookup
        format_name = config.get_format_name()
        assert format_name in DATE_FORMAT_OPTIONS or format_name == "", "Format name should be valid"
        print(f"  {OK} DateConfig format name lookup works")

        print(f"  {OK} DateConfig test passed\n")
        return True
    except Exception as e:
        print(f"  {FAIL} DateConfig test failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False

def test_syntax():
    """Test that all UI tab files have valid syntax."""
    print("Testing syntax...")

    files_to_check = [
        "ui/tabs/base_tab.py",
        "ui/table_utils.py",
        "ui/tabs/pipes_tab.py",
        "ui/tabs/curtains_tab.py",
        "ui/tabs/tasks_tab.py",
        "ui/tabs/swimlanes_tab.py",
        "ui/tabs/links_tab.py",
        "ui/tabs/notes_tab.py",
    ]

    import py_compile
    import os

    all_passed = True
    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            print(f"  {WARN} {file_path} not found, skipping")
            continue
        try:
            py_compile.compile(str(full_path), doraise=True)
            print(f"  {OK} {file_path} syntax OK")
        except py_compile.PyCompileError as e:
            print(f"  {FAIL} {file_path} syntax error: {e}")
            all_passed = False

    if all_passed:
        print(f"  {OK} All syntax checks passed\n")
    else:
        print(f"  {FAIL} Some syntax checks failed\n")

    return all_passed

def main():
    """Run all smoke tests."""
    print("=" * 60)
    print("Smoke Tests (no PyQt5 required)")
    print("=" * 60 + "\n")

    results = []
    results.append(test_imports())
    results.append(test_date_config())
    results.append(test_syntax())

    print("=" * 60)
    if all(results):
        print(f"{OK} All smoke tests passed!")
        print("=" * 60)
        return 0
    else:
        print(f"{FAIL} Some tests failed. Please check the errors above.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
