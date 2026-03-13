"""
Slice 7 smoke test — Style tab end-to-end verification.

Checks (no GUI interaction needed):
  1. Load POAP__TTP_30_1_.xlsx, render SVG, confirm colours come from config
  2. Change one colour, re-render, confirm the changed colour appears in SVG
  3. Save to Excel, reload, confirm the changed colour persists in chart_config
  4. Confirm zero hardcoded colour literals remain in gantt_chart_service.py
"""

import sys
import os
import re
import tempfile
import shutil

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# PyQt5 application required for QFont/QFontMetrics inside GanttChartService
from PyQt5.QtWidgets import QApplication
_app = QApplication.instance() or QApplication(sys.argv)

PASS = "[PASSED]"
FAIL = "[FAILED]"

results = []

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    msg = f"  {status} {label}"
    if not condition and detail:
        msg += f"\n         detail: {detail}"
    results.append((condition, msg))
    print(msg)


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
POAP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "tmp", "POAP__TTP_30_1_.xlsx")

from config.app_config import AppConfig
from repositories.excel_repository import ExcelRepository
from models.project import ProjectData
from services.gantt_chart_service import GanttChartService

print("=" * 60)
print("Slice 7 Smoke Test")
print("=" * 60)

# ---------------------------------------------------------------------------
# Check 4 first (static): zero hardcoded colour literals in service
# ---------------------------------------------------------------------------
print("\nCheck 4: Zero hardcoded colour literals in gantt_chart_service.py")
service_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "services", "gantt_chart_service.py")
with open(service_path, "r") as f:
    service_src = f.read()

HARDCODED_PATTERN = re.compile(
    r'''(?:fill|stroke)\s*=\s*["'](white|lightgrey|grey|darkgrey|black|#[0-9a-fA-F]{3,6})["']'''
)
hardcoded_hits = HARDCODED_PATTERN.findall(service_src)
check("Zero hardcoded colour literals in gantt_chart_service.py",
      len(hardcoded_hits) == 0,
      f"Found: {hardcoded_hits}")

# ---------------------------------------------------------------------------
# Check 1: Load POAP file, render SVG, confirm colours come from config
# ---------------------------------------------------------------------------
print("\nCheck 1: Load POAP file and render SVG")

app_config = AppConfig()
repo = ExcelRepository()

try:
    project = repo.load(POAP_PATH, ProjectData)
    loaded_ok = True
except Exception as e:
    loaded_ok = False
    check("POAP file loads without error", False, str(e))

if loaded_ok:
    check("POAP file loads without error", True)

    # Sync loaded chart_config colours into app_config (mirrors load_from_excel flow)
    chart_cfg = app_config.general.chart
    pc = project.chart_config
    for field in [
        "chart_background_color", "header_footer_background_color",
        "swimlane_label_color", "swimlane_divider_color",
        "scale_background_color", "scale_tick_color",
        "gridline_horizontal_color", "gridline_vertical_color",
        "task_stroke_color", "milestone_stroke_color",
        "outside_label_text_color", "outside_label_line_color",
    ]:
        setattr(chart_cfg, field, getattr(pc, field))

    # Render to a temp folder
    tmp_dir = tempfile.mkdtemp()
    svc = GanttChartService(app_config=app_config,
                            output_folder=tmp_dir,
                            output_filename="test_render.svg")
    svg_path = os.path.join(tmp_dir, "test_render.svg")

    try:
        svc.generate_svg(project.to_json())
        render_ok = os.path.exists(svg_path) and os.path.getsize(svg_path) > 0
    except Exception as e:
        render_ok = False
        check("SVG renders without error", False, str(e))

    if render_ok:
        check("SVG renders without error", True)

        with open(svg_path, "r", encoding="utf-8") as f:
            svg_src = f.read()

        # Confirm SVG contains the expected default background colour
        expected_bg = chart_cfg.chart_background_color  # e.g. "white"
        check("SVG contains chart background colour from config",
              expected_bg in svg_src,
              f"Expected '{expected_bg}' to appear in SVG")

        # Confirm SVG does NOT contain literal hardcoded strings we replaced
        # (spot-check: fill="lightgrey" as bare string attribute should not appear
        # unless it is the actual config value — if config IS lightgrey that's fine,
        # we instead confirm the pattern is config-driven by changing it below)
        check("SVG renders with correct header/footer colour",
              chart_cfg.header_footer_background_color in svg_src,
              f"Expected '{chart_cfg.header_footer_background_color}' in SVG")

    # ---------------------------------------------------------------------------
    # Check 2: Change a colour, re-render, confirm it appears in SVG
    # ---------------------------------------------------------------------------
    print("\nCheck 2: Change a colour, re-render, verify it appears in SVG")

    CHANGED_COLOUR = "red"
    original_colour = chart_cfg.chart_background_color

    # Change chart background colour on the app_config singleton
    chart_cfg.chart_background_color = CHANGED_COLOUR

    svg_path2 = os.path.join(tmp_dir, "test_render2.svg")
    svc2 = GanttChartService(app_config=app_config,
                             output_folder=tmp_dir,
                             output_filename="test_render2.svg")
    try:
        svc2.generate_svg(project.to_json())
        render2_ok = os.path.exists(svg_path2) and os.path.getsize(svg_path2) > 0
    except Exception as e:
        render2_ok = False
        check("Re-render with changed colour succeeds", False, str(e))

    if render2_ok:
        check("Re-render with changed colour succeeds", True)
        with open(svg_path2, "r", encoding="utf-8") as f:
            svg_src2 = f.read()
        check("Changed colour appears in re-rendered SVG",
              CHANGED_COLOUR in svg_src2,
              f"Expected '{CHANGED_COLOUR}' in SVG after colour change")

    # ---------------------------------------------------------------------------
    # Check 3: Save to Excel, reload, confirm changed colour persists
    # ---------------------------------------------------------------------------
    print("\nCheck 3: Save to Excel, reload, verify colour persists")

    # Sync app_config colour changes into project_data before saving
    # (mirrors _sync_chart_config_to_project_data in main_window)
    for field in [
        "chart_background_color", "header_footer_background_color",
        "swimlane_label_color", "swimlane_divider_color",
        "scale_background_color", "scale_tick_color",
        "gridline_horizontal_color", "gridline_vertical_color",
        "task_stroke_color", "milestone_stroke_color",
        "outside_label_text_color", "outside_label_line_color",
    ]:
        setattr(project.chart_config, field, getattr(chart_cfg, field))

    saved_path = os.path.join(tmp_dir, "test_save.xlsx")
    try:
        repo.save(saved_path, project)
        save_ok = os.path.exists(saved_path)
    except Exception as e:
        save_ok = False
        check("Project saves to Excel without error", False, str(e))

    if save_ok:
        check("Project saves to Excel without error", True)

        try:
            reloaded = repo.load(saved_path, ProjectData)
            reload_ok = True
        except Exception as e:
            reload_ok = False
            check("Reloaded project loads without error", False, str(e))

        if reload_ok:
            check("Reloaded project loads without error", True)
            persisted = reloaded.chart_config.chart_background_color
            check("Changed colour persists after save/reload",
                  persisted == CHANGED_COLOUR,
                  f"Expected '{CHANGED_COLOUR}', got '{persisted}'")

    # Restore original colour (cleanup)
    chart_cfg.chart_background_color = original_colour

    shutil.rmtree(tmp_dir, ignore_errors=True)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
passed = sum(1 for ok, _ in results if ok)
failed = sum(1 for ok, _ in results if not ok)
print(f"Results: {passed} passed, {failed} failed")
if failed == 0:
    print("[SUCCESS] All Slice 7 smoke tests passed!")
else:
    print("[FAILURE] Some checks failed — see details above.")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
