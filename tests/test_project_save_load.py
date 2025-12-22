#!/usr/bin/env python3
"""
Standalone test script to verify that all FrameConfig fields are correctly saved and loaded.
This test can run without pytest or PyQt5 dependencies.
"""

import sys
import json
import tempfile
import os
from pathlib import Path

# Ensure project root is in sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock PyQt5 for testing without GUI dependencies
class MockQDate:
    @staticmethod
    def currentDate():
        class MockDate:
            def toString(self, format_str):
                return "2025-01-01"
        return MockDate()

sys.modules['PyQt5'] = type(sys)('PyQt5')
sys.modules['PyQt5.QtCore'] = type(sys)('PyQt5.QtCore')
sys.modules['PyQt5.QtCore'].QDate = MockQDate

from models.project import ProjectData
from models.frame import FrameConfig
from repositories.project_repository import ProjectRepository


def test_frame_config_all_fields_saved():
    """Test that all FrameConfig fields are saved to JSON."""
    print("Testing: All FrameConfig fields are saved to JSON...")
    project = ProjectData()
    
    # Set all FrameConfig fields to non-default values
    project.frame_config.outer_width = 1000
    project.frame_config.outer_height = 800
    project.frame_config.header_height = 30
    project.frame_config.footer_height = 25
    project.frame_config.margins = (15, 20, 25, 30)
    project.frame_config.num_rows = 5
    project.frame_config.header_text = "Test Header Text"
    project.frame_config.footer_text = "Test Footer Text"
    project.frame_config.horizontal_gridlines = False
    project.frame_config.vertical_gridline_years = False
    project.frame_config.vertical_gridline_months = False
    project.frame_config.vertical_gridline_weeks = True
    project.frame_config.vertical_gridline_days = True
    project.frame_config.chart_start_date = "2025-01-15"
    
    # Convert to JSON
    json_data = project.to_json()
    
    # Verify frame_config is in the JSON
    assert "frame_config" in json_data, "frame_config should be in JSON output"
    
    frame_config_data = json_data["frame_config"]
    
    # Verify all fields are present
    expected_fields = {
        "outer_width": 1000,
        "outer_height": 800,
        "header_height": 30,
        "footer_height": 25,
        "margins": (15, 20, 25, 30),  # vars() preserves tuple type
        "num_rows": 5,
        "header_text": "Test Header Text",
        "footer_text": "Test Footer Text",
        "horizontal_gridlines": False,
        "vertical_gridline_years": False,
        "vertical_gridline_months": False,
        "vertical_gridline_weeks": True,
        "vertical_gridline_days": True,
        "chart_start_date": "2025-01-15"
    }
    
    for field_name, expected_value in expected_fields.items():
        assert field_name in frame_config_data, f"Field '{field_name}' should be in saved frame_config"
        # For margins, check that it's a tuple (vars preserves it) or can be converted
        if field_name == "margins":
            margins_value = frame_config_data[field_name]
            if isinstance(margins_value, list):
                margins_value = tuple(margins_value)
            assert margins_value == expected_value, \
                f"Field '{field_name}' should be {expected_value}, got {frame_config_data[field_name]}"
        else:
            assert frame_config_data[field_name] == expected_value, \
                f"Field '{field_name}' should be {expected_value}, got {frame_config_data[field_name]}"
    
    print("  [PASSED]")
    return True


def test_frame_config_all_fields_loaded():
    """Test that all FrameConfig fields are correctly loaded from JSON."""
    print("Testing: All FrameConfig fields are loaded from JSON...")
    
    # Create test data with all fields
    test_data = {
        "frame_config": {
            "outer_width": 1200,
            "outer_height": 900,
            "header_height": 40,
            "footer_height": 35,
            "margins": [20, 25, 30, 35],  # JSON stores as list
            "num_rows": 7,
            "header_text": "Loaded Header",
            "footer_text": "Loaded Footer",
            "horizontal_gridlines": True,
            "vertical_gridline_years": False,
            "vertical_gridline_months": False,
            "vertical_gridline_weeks": True,
            "vertical_gridline_days": False,
            "chart_start_date": "2025-02-20"
        },
        "tasks": [],
        "connectors": [],
        "swimlanes": [],
        "pipes": [],
        "curtains": [],
        "text_boxes": []
    }
    
    # Load from JSON
    loaded_project = ProjectData.from_json(test_data)
    
    # Verify all fields are loaded correctly
    assert loaded_project.frame_config.outer_width == 1200
    assert loaded_project.frame_config.outer_height == 900
    assert loaded_project.frame_config.header_height == 40
    assert loaded_project.frame_config.footer_height == 35
    assert loaded_project.frame_config.margins == (20, 25, 30, 35)  # Should be converted to tuple
    assert loaded_project.frame_config.num_rows == 7
    assert loaded_project.frame_config.header_text == "Loaded Header"
    assert loaded_project.frame_config.footer_text == "Loaded Footer"
    assert loaded_project.frame_config.horizontal_gridlines == True
    assert loaded_project.frame_config.vertical_gridline_years == False
    assert loaded_project.frame_config.vertical_gridline_months == False
    assert loaded_project.frame_config.vertical_gridline_weeks == True
    assert loaded_project.frame_config.vertical_gridline_days == False
    assert loaded_project.frame_config.chart_start_date == "2025-02-20"
    
    print("  [PASSED]")
    return True


def test_frame_config_save_and_load_roundtrip():
    """Test that saving and loading preserves all FrameConfig fields."""
    print("Testing: Save and load roundtrip preserves all fields...")
    
    repository = ProjectRepository()
    
    # Create project with custom FrameConfig
    original_project = ProjectData()
    original_project.frame_config.outer_width = 1500
    original_project.frame_config.outer_height = 1000
    original_project.frame_config.header_height = 50
    original_project.frame_config.footer_height = 45
    original_project.frame_config.margins = (12, 15, 18, 21)
    original_project.frame_config.num_rows = 10
    original_project.frame_config.header_text = "Roundtrip Header"
    original_project.frame_config.footer_text = "Roundtrip Footer"
    original_project.frame_config.horizontal_gridlines = False
    original_project.frame_config.vertical_gridline_years = True
    original_project.frame_config.vertical_gridline_months = False
    original_project.frame_config.vertical_gridline_weeks = True
    original_project.frame_config.vertical_gridline_days = False
    original_project.frame_config.chart_start_date = "2025-03-01"
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    
    try:
        repository.save(temp_file, original_project)
        
        # Load from file
        loaded_project = repository.load(temp_file, ProjectData)
        
        # Verify all fields match
        assert loaded_project.frame_config.outer_width == original_project.frame_config.outer_width
        assert loaded_project.frame_config.outer_height == original_project.frame_config.outer_height
        assert loaded_project.frame_config.header_height == original_project.frame_config.header_height
        assert loaded_project.frame_config.footer_height == original_project.frame_config.footer_height
        assert loaded_project.frame_config.margins == original_project.frame_config.margins
        assert loaded_project.frame_config.num_rows == original_project.frame_config.num_rows
        assert loaded_project.frame_config.header_text == original_project.frame_config.header_text
        assert loaded_project.frame_config.footer_text == original_project.frame_config.footer_text
        assert loaded_project.frame_config.horizontal_gridlines == original_project.frame_config.horizontal_gridlines
        assert loaded_project.frame_config.vertical_gridline_years == original_project.frame_config.vertical_gridline_years
        assert loaded_project.frame_config.vertical_gridline_months == original_project.frame_config.vertical_gridline_months
        assert loaded_project.frame_config.vertical_gridline_weeks == original_project.frame_config.vertical_gridline_weeks
        assert loaded_project.frame_config.vertical_gridline_days == original_project.frame_config.vertical_gridline_days
        assert loaded_project.frame_config.chart_start_date == original_project.frame_config.chart_start_date
        
        print("  [PASSED]")
        return True
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_frame_config_defaults_on_missing_fields():
    """Test that missing fields in JSON use FrameConfig defaults."""
    print("Testing: Missing fields use FrameConfig defaults...")
    
    # Create test data with only some fields
    test_data = {
        "frame_config": {
            "outer_width": 800,
            "outer_height": 600,
            # Missing other fields - should use defaults
        },
        "tasks": [],
        "connectors": [],
        "swimlanes": [],
        "pipes": [],
        "curtains": [],
        "text_boxes": []
    }
    
    # Load from JSON
    loaded_project = ProjectData.from_json(test_data)
    
    # Verify defaults are used for missing fields
    assert loaded_project.frame_config.outer_width == 800  # From JSON
    assert loaded_project.frame_config.outer_height == 600  # From JSON
    assert loaded_project.frame_config.header_height == 20  # Default
    assert loaded_project.frame_config.footer_height == 20  # Default
    assert loaded_project.frame_config.margins == (10, 10, 10, 10)  # Default
    assert loaded_project.frame_config.num_rows == 1  # Default
    assert loaded_project.frame_config.header_text == ""  # Default
    assert loaded_project.frame_config.footer_text == ""  # Default
    assert loaded_project.frame_config.horizontal_gridlines == True  # Default
    assert loaded_project.frame_config.vertical_gridline_years == True  # Default
    assert loaded_project.frame_config.vertical_gridline_months == True  # Default
    assert loaded_project.frame_config.vertical_gridline_weeks == False  # Default
    assert loaded_project.frame_config.vertical_gridline_days == False  # Default
    assert loaded_project.frame_config.chart_start_date == "2024-12-30"  # Default
    
    print("  [PASSED]")
    return True


def test_frame_config_margins_tuple_conversion():
    """Test that margins are correctly converted from list (JSON) to tuple."""
    print("Testing: Margins tuple conversion...")
    
    # JSON stores tuples as lists
    test_data = {
        "frame_config": {
            "margins": [5, 10, 15, 20]  # List in JSON
        },
        "tasks": [],
        "connectors": [],
        "swimlanes": [],
        "pipes": [],
        "curtains": [],
        "text_boxes": []
    }
    
    loaded_project = ProjectData.from_json(test_data)
    
    # Should be converted to tuple
    assert isinstance(loaded_project.frame_config.margins, tuple), \
        "margins should be converted to tuple"
    assert loaded_project.frame_config.margins == (5, 10, 15, 20)
    
    print("  [PASSED]")
    return True


def test_frame_config_backward_compatibility():
    """Test that old project files with header_height=50 and vertical_gridlines still load correctly."""
    print("Testing: Backward compatibility with old defaults...")
    
    # Simulate an old project file with old default header_height and old vertical_gridlines format
    test_data = {
        "frame_config": {
            "header_height": 50,  # Old default
            "footer_height": 50,  # Old default
            "header_text": "",
            "footer_text": "",
            "vertical_gridlines": True  # Old format - should be migrated to individual flags
        },
        "tasks": [],
        "connectors": [],
        "swimlanes": [],
        "pipes": [],
        "curtains": [],
        "text_boxes": []
    }
    
    loaded_project = ProjectData.from_json(test_data)
    
    # Should preserve old values, not use new defaults
    assert loaded_project.frame_config.header_height == 50
    assert loaded_project.frame_config.footer_height == 50
    
    # Old vertical_gridlines=True should be migrated to all individual flags being True
    assert loaded_project.frame_config.vertical_gridline_years == True
    assert loaded_project.frame_config.vertical_gridline_months == True
    assert loaded_project.frame_config.vertical_gridline_weeks == True
    assert loaded_project.frame_config.vertical_gridline_days == True
    
    print("  [PASSED]")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Project Save/Load Functionality")
    print("=" * 60)
    print()
    
    tests = [
        ("All fields saved", test_frame_config_all_fields_saved),
        ("All fields loaded", test_frame_config_all_fields_loaded),
        ("Save/load roundtrip", test_frame_config_save_and_load_roundtrip),
        ("Defaults on missing fields", test_frame_config_defaults_on_missing_fields),
        ("Margins tuple conversion", test_frame_config_margins_tuple_conversion),
        ("Backward compatibility", test_frame_config_backward_compatibility),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"  [FAILED]")
        except AssertionError as e:
            failed += 1
            print(f"  [FAILED]: {e}")
        except Exception as e:
            failed += 1
            print(f"  [ERROR]: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("[SUCCESS] All tests passed!")
        return 0
    else:
        print("[FAILURE] Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

