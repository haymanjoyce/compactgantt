/**
 * jSpreadsheet CE initialization and task data access.
 */
let spreadsheetInstance = null;

const COL = { ID: 0, TASK_NAME: 1, START_DATE: 2, END_DATE: 3, ROW: 4, LANE: 5 };

function initSpreadsheet(containerId) {
  const el = document.getElementById(containerId);
  if (!el) return null;

  const options = {
    data: [[]],
    columns: [
      { title: "ID", type: "numeric", width: 60 },
      { title: "Task Name", type: "text", width: 250 },
      { title: "Start Date", type: "calendar", width: 120, options: { format: "YYYY-MM-DD" } },
      { title: "End Date", type: "calendar", width: 120, options: { format: "YYYY-MM-DD" } },
      { title: "Row", type: "numeric", width: 60 },
      { title: "Lane", type: "numeric", width: 60 }
    ],
    minDimensions: [6, 10],
    allowInsertRow: true,
    allowManualInsertRow: true,
    allowDeleteRow: true,
    allowRenameColumn: false
  };

  if (typeof jspreadsheet !== "undefined") {
    spreadsheetInstance = jspreadsheet(el, options);
  }
  return spreadsheetInstance;
}

function getTasksFromSpreadsheet() {
  const tasks = [];
  if (!spreadsheetInstance) return tasks;

  try {
    const data = spreadsheetInstance.getData ? spreadsheetInstance.getData() : getDataFromTable();
    if (!Array.isArray(data)) return tasks;

    for (let i = 0; i < data.length; i++) {
      const row = data[i];
      if (!Array.isArray(row) || row.length < 6) continue;
      const id = parseCellNum(row[COL.ID]);
      const name = parseCellStr(row[COL.TASK_NAME]);
      const start = parseCellDate(row[COL.START_DATE]);
      const end = parseCellDate(row[COL.END_DATE]);
      const rowNum = parseCellNum(row[COL.ROW]);
      const lane = parseCellNum(row[COL.LANE]);
      if (id == null && !name && start == null && end == null && rowNum == null && lane == null) continue;
      tasks.push({
        id: id != null ? id : i + 1,
        name: name != null ? name : "",
        start: start != null ? start : "",
        end: end != null ? end : "",
        row: rowNum != null ? rowNum : 1,
        lane: lane != null ? lane : 1
      });
    }
  } catch (e) {
    console.warn("getTasksFromSpreadsheet", e);
  }
  return tasks;
}

function getDataFromTable() {
  const container = document.getElementById("spreadsheet");
  if (!container) return [];
  const table = container.querySelector("table");
  if (!table) return [];
  const tbody = table.querySelector("tbody") || table;
  const rows = tbody.querySelectorAll("tr");
  const out = [];
  rows.forEach((tr) => {
    const cells = tr.querySelectorAll("td");
    if (cells.length < 6) return;
    const row = [];
    cells.forEach((td, c) => {
      const input = td.querySelector("input");
      const val = input ? input.value : (td.textContent || "").trim();
      row.push(val);
    });
    out.push(row);
  });
  return out;
}

function parseCellNum(v) {
  if (v == null || v === "") return null;
  const n = Number(v);
  return isNaN(n) ? null : n;
}

function parseCellStr(v) {
  if (v == null) return null;
  const s = String(v).trim();
  return s === "" ? null : s;
}

function parseCellDate(v) {
  if (v == null || v === "") return null;
  if (v instanceof Date) return isNaN(v.getTime()) ? null : v.toISOString().slice(0, 10);
  const s = String(v).trim();
  if (s === "") return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
  if (s.indexOf("T") !== -1) return s.slice(0, 10);
  const d = new Date(s);
  return isNaN(d.getTime()) ? null : d.toISOString().slice(0, 10);
}

function setSpreadsheetData(rows) {
  if (!spreadsheetInstance || !spreadsheetInstance.setData) return;
  const data = Array.isArray(rows) && rows.length > 0
    ? rows.map((r) => [
        r.id != null ? r.id : "",
        r.name != null ? r.name : "",
        r.start != null ? r.start : "",
        r.end != null ? r.end : "",
        r.row != null ? r.row : "",
        r.lane != null ? r.lane : ""
      ])
    : [[]];
  spreadsheetInstance.setData(data);
}
