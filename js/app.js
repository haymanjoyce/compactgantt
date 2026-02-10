/**
 * Compact Gantt - Main application controller.
 */
(function() {
  function getTasks() {
    return getTasksFromSpreadsheet ? getTasksFromSpreadsheet() : [];
  }

  function validateAndShow() {
    const tasks = getTasks();
    const results = DataValidator.validateAll(tasks);
    const summaryEl = document.getElementById("validation-summary");
    const errorsEl = document.getElementById("validation-errors");
    const panel = document.getElementById("validation-panel");
    if (!summaryEl || !errorsEl || !panel) return;

    if (results.length === 0) {
      summaryEl.textContent = "✓ No errors found.";
      errorsEl.classList.add("hidden");
      errorsEl.innerHTML = "";
      panel.classList.remove("invalid");
      panel.classList.add("valid");
    } else {
      summaryEl.textContent = "⚠ " + results.length + " row(s) with errors.";
      errorsEl.classList.remove("hidden");
      errorsEl.innerHTML = results
        .map(
          (r) =>
            "Row " + r.index + ": " + (r.errors && r.errors.length ? r.errors.join("; ") : "")
        )
        .join("\n");
      panel.classList.remove("valid");
      panel.classList.add("invalid");
    }
    return { tasks, results };
  }

  function updateChart() {
    const tasks = getTasks();
    const validTasks = tasks.filter((t) => {
      const idSet = new Set();
      tasks.forEach((x) => {
        const id = Number(x.id);
        if (!isNaN(id) && id > 0) idSet.add(id);
      });
      idSet.delete(Number(t.id));
      const single = DataValidator.validateTask(t, idSet);
      return single.length === 0;
    });
    GanttChart.render("#gantt", validTasks, { width: null, height: 320 });
  }

  function onValidate() {
    validateAndShow();
    updateChart();
  }

  function onImportExcel(file) {
    if (!file) return;
    importExcel(file, function(rows) {
      setSpreadsheetData(rows);
      validateAndShow();
      updateChart();
    });
  }

  function onExportExcel() {
    const tasks = getTasks();
    exportExcel(tasks, "gantt-tasks.xlsx");
  }

  function onExportPNG() {
    exportPNG("gantt", "gantt-chart.png");
  }

  function onExportSVG() {
    exportSVG("gantt", "gantt-chart.svg");
  }

  function init() {
    initSpreadsheet("spreadsheet");

    document.getElementById("btn-validate").addEventListener("click", onValidate);
    document.getElementById("btn-export-excel").addEventListener("click", onExportExcel);
    document.getElementById("btn-export-png").addEventListener("click", onExportPNG);
    document.getElementById("btn-export-svg").addEventListener("click", onExportSVG);

    const fileInput = document.getElementById("file-excel");
    document.getElementById("btn-import-excel").addEventListener("click", function() {
      fileInput.click();
    });
    fileInput.addEventListener("change", function() {
      const file = fileInput.files && fileInput.files[0];
      if (file) onImportExcel(file);
      fileInput.value = "";
    });

    validateAndShow();
    updateChart();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
