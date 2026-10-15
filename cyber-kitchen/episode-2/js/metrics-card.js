function renderMetrics() {
  const box = $("metrics");
  if (!selected || !$("panel").classList.contains("open")) return box.replaceChildren();
  const add = (tag, className, content, parent) => {
    const node = document.createElement(tag);
    node.className = className; node.textContent = content;
    parent.appendChild(node);
    return node;
  };
  const card = document.createElement("div"); card.className = "about metrics";
  add("span", "kind", "Metrics", card);
  const spec = metricsFor(selected);
  const list = add("dl", "", "", card);
  for (const [label, value] of [["Objective", spec.objective], ["How it is measured", spec.measure]]) { add("dt", "", label, list); add("dd", "", value, list); }
  const headline = add("div", "metric-value", "", card);
  add("b", "", spec.value, headline);
  add("span", "", spec.unit, headline);
  add("i", "verdict " + spec.verdict[1], spec.verdict[0], headline).style.fontStyle = "normal";
  for (const note of spec.notes) if (note) add("p", "metric-note", note, card);
  card.appendChild(spec.chart);
  add("p", "metric-note", spec.caption, card);
  card.appendChild(spec.timeline);
  add("p", "metric-note", spec.timelineCaption, card);
  if (spec.numbers) {
    const numbers = add("dl", "", "", card);
    for (const [label, value] of spec.numbers) { add("dt", "", label, numbers); add("dd", "", value, numbers); }
  }
  box.replaceChildren(card);
}
