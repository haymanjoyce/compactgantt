/**
 * Excel import/export via SheetJS.
 */
function importExcel(file, onData) {
  if (typeof XLSX === "undefined") {
    alert("Excel import requires SheetJS. Load it from CDN.");
    return;
  }
  const reader = new FileReader();
  reader.onload = function(e) {
    try {
      const data = new Uint8Array(e.target.result);
      const workbook = XLSX.read(data, { type: "array" });
      const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
      const json = XLSX.utils.sheet_to_json(firstSheet, { header: 1 });
      const rows = jsonToTaskRows(json);
      if (typeof onData === "function") onData(rows);
    } catch (err) {
      console.error("Import Excel", err);
      alert("Could not read the Excel file. Check the format.");
    }
  };
  reader.readAsArrayBuffer(file);
}

function jsonToTaskRows(json) {
  if (!Array.isArray(json) || json.length === 0) return [];
  const header = json[0];
  const idIdx = findCol(header, "id");
  const nameIdx = findCol(header, "task name", "task name");
  const startIdx = findCol(header, "start", "start date");
  const endIdx = findCol(header, "end", "end date");
  const rowIdx = findCol(header, "row");
  const laneIdx = findCol(header, "lane");

  const rows = [];
  for (let i = 1; i < json.length; i++) {
    const r = json[i];
    if (!Array.isArray(r) && typeof r !== "object") continue;
    const arr = Array.isArray(r) ? r : [r[idIdx], r[nameIdx], r[startIdx], r[endIdx], r[rowIdx], r[laneIdx]];
    const id = cellVal(arr[idIdx]);
    const name = cellVal(arr[nameIdx]);
    const start = cellVal(arr[startIdx]);
    const end = cellVal(arr[endIdx]);
    const rowNum = cellVal(arr[rowIdx]);
    const lane = cellVal(arr[laneIdx]);
    if (id === "" && !name && start === "" && end === "" && rowNum === "" && lane === "") continue;
    rows.push({
      id: id !== "" ? Number(id) : i,
      name: name != null ? String(name) : "",
      start: start != null ? formatDate(start) : "",
      end: end != null ? formatDate(end) : "",
      row: rowNum !== "" ? Number(rowNum) : 1,
      lane: lane !== "" ? Number(lane) : 1
    });
  }
  return rows;
}

function findCol(header, ...names) {
  if (!Array.isArray(header)) return -1;
  const lower = names.map((n) => String(n).toLowerCase());
  for (let i = 0; i < header.length; i++) {
    const h = String(header[i] || "").toLowerCase().trim();
    if (lower.some((n) => h === n || h.replace(/\s+/g, " ").indexOf(n) !== -1)) return i;
  }
  return -1;
}

function cellVal(v) {
  if (v == null) return "";
  if (typeof v === "number" && !isNaN(v)) return v;
  return String(v).trim();
}

function formatDate(v) {
  if (v == null) return "";
  if (typeof v === "number" && v > 0) {
    const d = new Date((v - 25569) * 86400 * 1000);
    if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10);
  }
  const s = String(v).trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
  const d = new Date(s);
  return isNaN(d.getTime()) ? s : d.toISOString().slice(0, 10);
}

function exportExcel(tasks, filename) {
  if (typeof XLSX === "undefined") {
    alert("Excel export requires SheetJS. Load it from CDN.");
    return;
  }
  const headers = ["ID", "Task Name", "Start Date", "End Date", "Row", "Lane"];
  const rows = (tasks || []).map((t) => [t.id, t.name, t.start, t.end, t.row, t.lane]);
  const data = [headers, ...rows];
  const ws = XLSX.utils.aoa_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Tasks");
  XLSX.writeFile(wb, filename || "gantt-tasks.xlsx");
}
