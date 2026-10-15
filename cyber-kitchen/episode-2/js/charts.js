// ----- charts on real time -----
// All of these share one time axis: the last three minutes, sliding left, with "now" at the same
// place in every chart and marked by a yellow line.
const NOW_X = 252, PER_SECOND = NOW_X / WINDOW;
const timeX = t => NOW_X - (clock - t) * PER_SECOND;
const WAIT_COLOR = "var(--ready)", WORK_COLOR = "#8d949b", OWN_COLOR = "var(--eating)", USE_COLOR = "#3987e5";
function timeChart(height, draw) {
  const svg = el("svg", { class: "chart", viewBox: `0 0 300 ${height + 30}` });
  el("rect", { class: "chart-track", x: 0, y: 12, width: 300, height, rx: 3 }, svg);
  for (let t = Math.max(0, Math.ceil((clock - WINDOW) / 30) * 30); timeX(t) < 300; t += 30) {
    el("path", { d: `M${timeX(t)} 12v${height + 4}`, stroke: "var(--hairline)" }, svg);
    text(clockText(t), { x: timeX(t), y: height + 27, "text-anchor": "middle" }, svg);
  }
  draw((start, end, y, h, fill) => {
    const x1 = Math.max(0, timeX(start)), x2 = Math.min(NOW_X, timeX(end ?? clock));
    if (x2 > x1) el("rect", { x: x1, y: 12 + y, width: Math.max(x2 - x1, 1), height: h, fill }, svg);
  });
  el("path", { d: `M${NOW_X} 2v${height + 14}`, stroke: "var(--menu)", "stroke-width": 2.5 }, svg);
  text("now", { x: NOW_X + 4, y: 9, style: "fill: var(--menu)" }, svg);
  return svg;
}
// a reading over time: a strip that is filled while a thing is in use, or as tall as a queue is long
function readingTimeline(g) {
  const top = Math.max(1, ...g.changes.map(change => change[1]));
  return timeChart(36, span => g.changes.forEach(([time, value], i) => {
    if (value) span(time, g.changes[i + 1]?.[0], 36 - 36 * value / top, 36 * value / top, USE_COLOR);
  }));
}
// one thin bar per stay, as long as the stay lasted; stays that overlap are stacked
function staysTimeline(stays, target) {
  const rows = [], placed = stays.map(one => {
    let row = rows.findIndex(end => end <= one.start);
    if (row < 0) row = rows.length < 9 ? rows.length : 8;
    rows[row] = one.end ?? Infinity;
    return row;
  });
  const color = one => !target ? WORK_COLOR : (one.end ?? clock) - one.start <= target ? "var(--eating)" : "var(--waiting)";
  return timeChart(Math.max(rows.length, 4) * 7 + 2, span => stays.forEach((one, i) => span(one.start, one.end, 2 + placed[i] * 7, 5, color(one))));
}
// the parts of one ticket's or one party's time, end to end
function partsTimeline(start, parts) {
  return timeChart(18, span => {
    for (const [seconds, fill] of parts) {
      if (seconds) span(start, start + seconds, 3, 12, fill);
      start += seconds;
    }
  });
}

// bars over time, with a dashed line at the target
function barChart(values, target, good, format) {
  const svg = el("svg", { class: "chart", viewBox: "0 0 300 86" });
  if (!values.length) { text("No history yet.", { x: 0, y: 46 }, svg); return svg; }
  const top = Math.max(target || 0, ...values, 1e-9) * 1.18, width = 300 / Math.max(values.length, 20);
  values.forEach((v, i) => el("rect", {
    x: i * width + 1, y: 80 - 72 * v / top, width: width - 2, height: 72 * v / top + 0.5, rx: 1.5,
    fill: !target ? "#8d949b" : good(v) ? "var(--eating)" : "var(--waiting)" }, svg));
  el("path", { d: "M0 80.5H300", stroke: "var(--text-muted)" }, svg);
  if (target) {
    const y = 80 - 72 * target / top;
    el("path", { d: `M0 ${y}H300`, stroke: "var(--ready)", "stroke-width": 1.5, "stroke-dasharray": "5 4" }, svg);
    text(format(target), { x: 300, y: y - 3, "text-anchor": "end" }, svg);
  }
  return svg;
}
// one bar per part, with marks for the average and the target
function rowChart(rows) {
  const svg = el("svg", { class: "chart", viewBox: `0 0 300 ${rows.length * 26}` });
  const top = Math.max(1e-9, ...rows.flatMap(row => [row.value, row.average, row.target || 0])) * 1.1, x = v => 84 + 170 * v / top;
  rows.forEach((row, i) => {
    const y = i * 26 + 8;
    text(row.label, { x: 0, y: y + 9 }, svg);
    el("rect", { class: "chart-track", x: 84, y, width: 170, height: 10, rx: 3 }, svg);
    el("rect", { x: 84, y, width: 170 * row.value / top, height: 10, rx: 3, fill: !row.target ? "#8d949b" : row.value <= row.target ? "var(--eating)" : "var(--waiting)" }, svg);
    if (row.target) el("path", { d: `M${x(row.target)} ${y - 4}v18`, stroke: "var(--ready)", "stroke-width": 2 }, svg);
    if (row.average) el("path", { d: `M${x(row.average)} ${y - 3}v16`, stroke: "#fff", "stroke-width": 2 }, svg);
    text(clockText(row.value), { x: 300, y: y + 9, "text-anchor": "end" }, svg);
  });
  return svg;
}
