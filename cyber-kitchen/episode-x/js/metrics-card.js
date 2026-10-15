// The Metrics tab, in sections with small headings: how the objective is measured, then one section
// per chart, then the target with the number so far and whether it is on target. What is happening
// now and the other numbers are underneath.
function renderMetrics() {
  const box = $("metrics");
  if (!metricsShowing()) return box.replaceChildren();
  const add = (tag, className, content, parent) => {
    const node = document.createElement(tag);
    node.className = className; node.textContent = content;
    parent.appendChild(node);
    return node;
  };
  const card = document.createElement("div"); card.className = "about metrics";
  const spec = metricsFor(selected);
  if (spec.measure) { add("h4", "section", "How it is measured", card); add("p", "measure", spec.measure, card); }
  // each chart is a section: a short heading, the chart on a grey ground so it reads as a picture, then what it shows
  for (const [title, chart, caption] of [[spec.chartTitle, spec.chart, spec.caption], [spec.timelineTitle, spec.timeline, spec.timelineCaption]]) {
    const figure = add("figure", "figure", "", card);
    add("h4", "section", title, figure);
    add("div", "plot", "", figure).appendChild(chart);
    add("figcaption", "metric-note", caption, figure);
  }
  const target = spec.notes.find(isTargetNote);
  add("h4", "section", "Target", card);
  if (target) add("p", "measure", target.replace(/^Target: /, "").replace(/^./, first => first.toUpperCase()), card);
  const headline = add("div", "metric-value", "", card);
  add("b", "", spec.value, headline);
  add("span", "", spec.unit, headline);
  add("i", "verdict " + spec.verdict[1], spec.verdict[0], headline).style.fontStyle = "normal";
  for (const note of spec.notes) if (note && note !== target) add("p", "metric-note", note, card);
  if (spec.numbers) {
    const numbers = add("dl", "", "", card);
    for (const [label, value] of spec.numbers) { add("dt", "", label, numbers); add("dd", "", value, numbers); }
  }
  box.replaceChildren(card);
}
