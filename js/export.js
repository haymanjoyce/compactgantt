/**
 * PNG and SVG export for the Gantt chart.
 */
function exportPNG(containerId, filename) {
  const el = document.getElementById(containerId || "gantt");
  if (!el) return;
  if (typeof html2canvas === "undefined") {
    alert("Export PNG requires html2canvas. Load it from CDN.");
    return;
  }
  html2canvas(el, { backgroundColor: null, scale: 2 }).then((canvas) => {
    canvas.toBlob((blob) => {
      if (typeof saveAs === "undefined") {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename || "gantt-chart.png";
        a.click();
        URL.revokeObjectURL(url);
      } else {
        saveAs(blob, filename || "gantt-chart.png");
      }
    });
  });
}

function exportSVG(containerId, filename) {
  const el = document.getElementById(containerId || "gantt");
  if (!el) return;
  const svg = el.querySelector("svg");
  if (!svg) {
    alert("No chart to export. Add tasks and update the chart first.");
    return;
  }
  const serializer = new XMLSerializer();
  const str = serializer.serializeToString(svg);
  const blob = new Blob([str], { type: "image/svg+xml;charset=utf-8" });
  if (typeof saveAs !== "undefined") {
    saveAs(blob, filename || "gantt-chart.svg");
  } else {
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "gantt-chart.svg";
    a.click();
    URL.revokeObjectURL(url);
  }
}
