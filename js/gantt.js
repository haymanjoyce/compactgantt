/**
 * D3 Gantt chart: renders tasks into SVG (swimlanes, time axis, bars).
 */
const GanttChart = {
  margin: { top: 24, right: 20, bottom: 32, left: 12 },
  barHeight: 24,
  padding: 4,

  render(containerSelector, tasks, options) {
    const container = document.querySelector(containerSelector);
    if (!container || typeof d3 === "undefined") return;

    const opts = options || {};
    const width = opts.width != null ? opts.width : Math.max(400, container.clientWidth - 24);
    const height = opts.height != null ? opts.height : 320;

    if (tasks.length === 0) {
      container.innerHTML = "<div class=\"p-4 text-gray-500\">Add tasks in the spreadsheet and click Validate to see the chart.</div>";
      return;
    }

    const sorted = [...tasks].sort((a, b) => (a.lane - b.lane) || (a.row - b.row));
    const lanes = [...new Set(sorted.map((t) => t.lane))].sort((a, b) => a - b);
    const dateExtent = [
      d3.min(sorted, (t) => new Date(t.start)),
      d3.max(sorted, (t) => new Date(t.end))
    ];
    if (dateExtent[0].getTime() === dateExtent[1].getTime()) {
      dateExtent[0].setDate(dateExtent[0].getDate() - 1);
      dateExtent[1].setDate(dateExtent[1].getDate() + 1);
    }

    const innerWidth = width - this.margin.left - this.margin.right;
    const rowHeight = this.barHeight + this.padding;
    const chartHeight = lanes.length * rowHeight;
    const innerHeight = chartHeight;

    const xScale = d3.scaleTime().domain(dateExtent).range([0, innerWidth]);
    const yScale = d3.scaleBand().domain(lanes.map(String)).range([0, innerHeight]).padding(0.1);

    const svg = d3.select(container).selectAll("svg").data([1]);
    const svgEnter = svg.enter().append("svg").attr("class", "gantt-svg");
    const g = svgEnter.append("g").attr("transform", `translate(${this.margin.left},${this.margin.top})`);
    g.append("g").attr("class", "gantt-axis");
    g.append("g").attr("class", "gantt-grid");
    g.append("g").attr("class", "gantt-lanes");
    g.append("g").attr("class", "gantt-bars");

    const merged = svgEnter.merge(svg);
    merged.attr("width", width).attr("height", height);
    const gUpdate = merged.select("g").attr("transform", `translate(${this.margin.left},${this.margin.top})`);

    const axisG = gUpdate.select(".gantt-axis");
    const axis = d3.axisTop(xScale).ticks(8).tickSize(-innerHeight);
    axisG.call(axis).attr("class", "gantt-axis");
    axisG.selectAll("text").attr("class", "gantt-axis text");

    const gridG = gUpdate.select(".gantt-grid");
    gridG.selectAll("*").remove();
    gridG.call(
      d3.axisTop(xScale)
        .ticks(8)
        .tickSize(-innerHeight)
        .tickFormat("")
    );

    const lanesG = gUpdate.select(".gantt-lanes");
    const laneRects = lanesG.selectAll("rect.lane-band").data(lanes);
    laneRects.enter().append("rect").attr("class", "lane-band").merge(laneRects)
      .attr("y", (d) => yScale(String(d)))
      .attr("x", 0)
      .attr("width", innerWidth)
      .attr("height", yScale.bandwidth())
      .attr("class", (d) => `lane-band lane-${d}`);
    laneRects.exit().remove();

    const barsG = gUpdate.select(".gantt-bars");
    const bars = barsG.selectAll("rect.gantt-bar").data(sorted, (d) => d.id + "-" + (d.start || "") + "-" + (d.end || ""));
    bars.enter().append("rect").attr("class", "gantt-bar").merge(bars)
      .attr("x", (d) => xScale(new Date(d.start)))
      .attr("y", (d) => {
        const laneY = yScale(String(d.lane));
        const bandHeight = yScale.bandwidth();
        return laneY + (bandHeight - Math.min(this.barHeight, bandHeight - 2)) / 2;
      })
      .attr("width", (d) => Math.max(2, xScale(new Date(d.end)) - xScale(new Date(d.start))))
      .attr("height", (d) => Math.min(this.barHeight, yScale.bandwidth() - 2))
      .attr("rx", 3)
      .attr("class", (d) => `gantt-bar lane-${d.lane}`)
      .each(function(d) {
        this._task = d;
      });
    bars.exit().remove();

    const titles = barsG.selectAll("title").data(sorted, (d) => d.id + "-" + (d.start || "") + "-" + (d.end || ""));
    titles.enter().append("title").merge(titles).text((d) => `${d.name} (${d.start} → ${d.end})`);
    titles.exit().remove();
  }
};
