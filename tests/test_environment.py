#!/usr/bin/env python3
"""
Comprehensive test script for Compact Gantt application.
This script tests the environment setup, imports, and basic functionality.
"""

import sys
import os
import traceback
from pathlib import Path

# Add the parent directory to the Python path so we can import project modules
# This allows the test to run from the tests/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_python_version():
    """Test that Python version is 3.8+."""
    print("Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} is too old. Need 3.8+")
        return False

def test_imports():
    """Test that all required modules can be imported."""
    print("\nTesting imports...")
    
    required_modules = [
        'PyQt5.QtWidgets',
        'PyQt5.QtCore', 
        'PyQt5.QtGui',
        'svgwrite',
        'json',
        'logging',
        'typing'
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import: {failed_imports}")
        return False
    
    print("✓ All required modules imported successfully")
    return True

def test_project_imports():
    """Test that all project modules can be imported."""
    print("\nTesting project imports...")
    
    project_modules = [
        'config.app_config',
        'models.project',
        'models.frame',
        'models.task',
        'models.time_frame',
        'services.gantt_chart_service',
        'services.project_service',
        'services.task_service',
        'services.time_frame_service',
        'repositories.project_repository',
        'ui.data_entry_window',
        'ui.svg_display',
        'ui.tabs.titles_tab',
        'ui.tabs.layout_tab',
        'ui.tabs.tasks_tab',
        'ui.tabs.time_frames_tab',
        'ui.tabs.scales_tab',
        'ui.tabs.grid_tab',
        'ui.tabs.swimlanes_tab',
        'ui.tabs.user_preferences_tab',
        'validators.validators',
        'utils.conversion'
    ]
    
    failed_imports = []
    
    for module in project_modules:
        try:
            __import__(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n❌ Failed to import project modules: {failed_imports}")
        return False
    
    print("✓ All project modules imported successfully")
    return True

def test_file_structure():
    """Test that all required files and directories exist."""
    print("\nTesting file structure...")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'README.md',
        'config/app_config.py',
        'models/project.py',
        'services/gantt_chart_service.py',
        'ui/data_entry_window.py',
        'ui/svg_display.py',
        'ui/tabs/titles_tab.py',
        'assets/logo.png'
    ]
    
    required_dirs = [
        'config',
        'models', 
        'services',
        'ui',
        'ui/tabs',
        'repositories',
        'validators',
        'utils',
        'assets',
        'svg',
        'logs'
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
            print(f"✗ Missing file: {file_path}")
        else:
            print(f"✓ {file_path}")
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            missing_dirs.append(dir_path)
            print(f"✗ Missing directory: {dir_path}")
        else:
            print(f"✓ {dir_path}")
    
    if missing_files or missing_dirs:
        print(f"\n❌ Missing files: {missing_files}")
        print(f"❌ Missing directories: {missing_dirs}")
        return False
    
    print("✓ All required files and directories exist")
    return True

def test_basic_functionality():
    """Test basic functionality without GUI."""
    print("\nTesting basic functionality...")
    
    try:
        # Test config loading
        from config.app_config import AppConfig
        config = AppConfig()
        print("✓ AppConfig loaded successfully")
        
        # Test project data creation
        from models.project import ProjectData
        project_data = ProjectData()
        print("✓ ProjectData created successfully")
        
        # Test services creation
        from services.gantt_chart_service import GanttChartService
        gantt_service = GanttChartService()
        print("✓ GanttChartService created successfully")
        
        # Test repository creation
        from repositories.project_repository import JsonProjectRepository
        repo = JsonProjectRepository()
        print("✓ JsonProjectRepository created successfully")
        
        # Test utility functions
        from utils.conversion import safe_int, safe_float
        assert safe_int("123") == 123
        assert safe_int("abc", 0) == 0
        assert safe_float("123.45") == 123.45
        assert safe_float("abc", 0.0) == 0.0
        print("✓ Utility functions work correctly")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_gui_creation():
    """Test that GUI components can be created."""
    print("\nTesting GUI creation...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from ui.data_entry_window import DataEntryWindow
        from ui.svg_display import FitToWindowSvgDisplay
        from models.project import ProjectData
        from config.app_config import AppConfig
        
        # Create QApplication
        app = QApplication(sys.argv)
        print("✓ QApplication created successfully")
        
        # Create project data and config
        project_data = ProjectData()
        app_config = AppConfig()
        print("✓ Project data and config created")
        
        # Create SVG display
        svg_display = FitToWindowSvgDisplay(app_config)
        print("✓ SVG display created successfully")
        
        # Create data entry window
        data_entry = DataEntryWindow(project_data, svg_display)
        print("✓ Data entry window created successfully")
        
        # Test that tabs exist
        assert hasattr(data_entry, 'titles_tab')
        assert hasattr(data_entry, 'layout_tab')
        assert hasattr(data_entry, 'tasks_tab')
        assert hasattr(data_entry, 'time_frames_tab')
        print("✓ All required tabs exist")
        
        return True
        
    except Exception as e:
        print(f"✗ GUI creation test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🧪 Starting Comprehensive Compact Gantt Tests\n")
    print("=" * 60)
    
    tests = [
        ("Python Version", test_python_version),
        ("Required Imports", test_imports),
        ("Project Imports", test_project_imports),
        ("File Structure", test_file_structure),
        ("Basic Functionality", test_basic_functionality),
        ("GUI Creation", test_gui_creation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\nTo run the application:")
        print("  python main.py")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues before running the application.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 