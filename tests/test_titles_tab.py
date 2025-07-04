#!/usr/bin/env python3
"""
Test script specifically for the new Titles tab functionality.
This verifies that the combined header/footer tab works correctly.
"""

import sys
import os
from pathlib import Path
# Add the parent directory to the Python path so we can import project modules
sys.path.insert(0, str(Path(__file__).parent.parent))
from PyQt5.QtWidgets import QApplication
from models.project import ProjectData
from config.app_config import AppConfig
from ui.tabs.titles_tab import TitlesTab

def test_titles_tab_creation():
    """Test that TitlesTab can be created successfully."""
    print("Testing TitlesTab creation...")
    
    try:
        project_data = ProjectData()
        app_config = AppConfig()
        titles_tab = TitlesTab(project_data, app_config)
        
        # Test that all expected UI elements exist
        assert hasattr(titles_tab, 'header_height')
        assert hasattr(titles_tab, 'header_text')
        assert hasattr(titles_tab, 'footer_height')
        assert hasattr(titles_tab, 'footer_text')
        
        print("✓ TitlesTab created successfully with all UI elements")
        return True
        
    except Exception as e:
        print(f"✗ TitlesTab creation failed: {e}")
        return False

def test_titles_tab_data_loading():
    """Test that TitlesTab loads initial data correctly."""
    print("\nTesting TitlesTab data loading...")
    
    try:
        project_data = ProjectData()
        app_config = AppConfig()
        
        # Set some test data
        project_data.frame_config.header_height = 75
        project_data.frame_config.header_text = "Test Header"
        project_data.frame_config.footer_height = 60
        project_data.frame_config.footer_text = "Test Footer"
        
        titles_tab = TitlesTab(project_data, app_config)
        
        # Check that data was loaded correctly
        assert titles_tab.header_height.text() == "75"
        assert titles_tab.header_text.text() == "Test Header"
        assert titles_tab.footer_height.text() == "60"
        assert titles_tab.footer_text.text() == "Test Footer"
        
        print("✓ TitlesTab data loading works correctly")
        return True
        
    except Exception as e:
        print(f"✗ TitlesTab data loading failed: {e}")
        return False

def test_titles_tab_data_sync():
    """Test that TitlesTab syncs data correctly."""
    print("\nTesting TitlesTab data synchronization...")
    
    try:
        project_data = ProjectData()
        app_config = AppConfig()
        titles_tab = TitlesTab(project_data, app_config)
        
        # Simulate user input
        titles_tab.header_height.setText("80")
        titles_tab.header_text.setText("New Header")
        titles_tab.footer_height.setText("65")
        titles_tab.footer_text.setText("New Footer")
        
        # Trigger data sync
        titles_tab._sync_data()
        
        # Check that project data was updated
        assert project_data.frame_config.header_height == 80
        assert project_data.frame_config.header_text == "New Header"
        assert project_data.frame_config.footer_height == 65
        assert project_data.frame_config.footer_text == "New Footer"
        
        print("✓ TitlesTab data synchronization works correctly")
        return True
        
    except Exception as e:
        print(f"✗ TitlesTab data synchronization failed: {e}")
        return False

def test_titles_tab_validation():
    """Test that TitlesTab validates input correctly."""
    print("\nTesting TitlesTab validation...")
    
    try:
        project_data = ProjectData()
        app_config = AppConfig()
        titles_tab = TitlesTab(project_data, app_config)
        
        # Test invalid height values
        invalid_values = ["", "0", "-5", "abc"]
        invalid_failed = False
        for value in invalid_values:
            print(f"Testing invalid value: '{value}'")
            titles_tab.header_height.setText(value)
            try:
                titles_tab._sync_data()
                print(f"✗ Validation failed - should have rejected: '{value}'")
                invalid_failed = True
            except ValueError as e:
                print(f"✓ Correctly rejected invalid value: '{value}' with error: {e}")
        
        # Test valid values
        valid_values = ["10", "50", "100"]
        valid_failed = False
        for value in valid_values:
            print(f"Testing valid value: '{value}'")
            titles_tab.header_height.setText(value)
            try:
                titles_tab._sync_data()
                print(f"✓ Correctly accepted valid value: '{value}'")
            except ValueError as e:
                print(f"✗ Validation failed - should have accepted: '{value}' with error: {e}")
                valid_failed = True
        
        if invalid_failed or valid_failed:
            return False
        print("✓ TitlesTab validation works correctly")
        return True
        
    except Exception as e:
        print(f"✗ TitlesTab validation test failed: {e}")
        return False

def main():
    """Run all TitlesTab tests."""
    print("🧪 Testing New Titles Tab Functionality\n")
    print("=" * 50)
    
    # Create QApplication first
    app = QApplication(sys.argv)
    
    tests = [
        ("TitlesTab Creation", test_titles_tab_creation),
        ("Data Loading", test_titles_tab_data_loading),
        ("Data Synchronization", test_titles_tab_data_sync),
        ("Input Validation", test_titles_tab_validation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All TitlesTab tests passed! The new combined tab is working correctly.")
        return 0
    else:
        print("⚠️  Some TitlesTab tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 