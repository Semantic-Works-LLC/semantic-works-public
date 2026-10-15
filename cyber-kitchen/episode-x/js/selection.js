// ---------- selection and the details panel ----------
// One object can be selected at a time. The details panel is made of sections that fold away, each a
// card with a header: Selection (what is selected, with About, Metrics and Actions tabs), Event stream and Legend.
// Sections start folded. The panel remembers which sections are open and which tab is showing, so
// they stay as they were left while the selection and the view change.
let selected = null;
const folds = { selection: false, events: false, legend: false };   // which sections are open
let detailsTab = "about";                             // the tab showing in the Selection section
function select(info) {
  if (selected) selected.nodes.forEach(node => node.removeAttribute("data-selected"));
  selected = info;
  if (info) { info.nodes.forEach(node => node.setAttribute("data-selected", "")); setPanel(true); setFold("selection", true); setPicker(false); }   // selecting opens the panel and its Selection section
  renderCard();
}
function setPanel(open) {
  keep("panel", open);
  $("panel").classList.toggle("open", open);
  $("panel-divider").classList.toggle("open", open);
  renderMetrics();
  $("panel-toggle").setAttribute("aria-pressed", open);
  $("panel-toggle").title = open ? "Hide details" : "Show details";
  $("panel-toggle").setAttribute("aria-label", $("panel-toggle").title);
  $("icon-collapse").toggleAttribute("hidden", !open);   // the arrow shows which way a click will push the panel
  $("icon-expand").toggleAttribute("hidden", open);
}
function setFold(key, open) {
  folds[key] = open;
  keep("folds", { ...folds });
  const section = document.querySelector(`.fold[data-fold="${key}"]`), button = section.querySelector(".fold-toggle");
  section.querySelector(".fold-body").hidden = !open;
  button.setAttribute("aria-expanded", open);
  button.setAttribute("aria-label", `${open ? "Collapse" : "Expand"} ${section.querySelector("h3").textContent}`);
  renderMetrics();
  renderEvents();
}
function setTab(tab) {
  detailsTab = tab;
  keep("tab", tab);
  for (const button of $("tabs").children) button.setAttribute("aria-selected", button.dataset.tab === tab);
  $("about").hidden = Boolean(selected) && tab !== "about";   // with nothing selected there are no tabs, only the hint
  $("metrics").hidden = !selected || tab !== "metrics";
  $("actions").hidden = !selected || tab !== "actions";
  renderMetrics();
  renderActions();
}
// the metrics are redrawn several times a second, so only when they can be seen
const metricsShowing = () => Boolean(selected) && $("panel").classList.contains("open") && folds.selection && detailsTab === "metrics";
function setPicker(open) {
  $("picker").hidden = !open;
  $("picker-toggle").setAttribute("aria-expanded", open);
  if (open) { $("picker-filter").value = ""; updateActorList(); $("picker-filter").focus(); }
}
function renderCard() {
  const about = $("about"), head = $("selected-head");
  about.replaceChildren(); head.replaceChildren();
  $("tabs").hidden = !selected;
  if (!selected) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "Nothing selected. Click anything in the live view, or use the target button at the top to pick one by name.";
    about.appendChild(empty);
  } else {
    const name = document.createElement("h3"); name.textContent = selected.name;
    head.appendChild(name);   // only the name; what kind of thing it is, is the first line of About
    const card = document.createElement("div"); card.className = "about";
    const list = document.createElement("dl");
    // the About tab holds only what does not change; anything live belongs to the Metrics tab
    const rows = [["Kind", selected.kind], ["What it is", selected.what], ["Purpose", selected.purpose], ["Why it is here", selected.why],
                  ...(selected.extra || []).filter(row => typeof row[1] !== "function")].filter(row => row[1]);
    const spec = metricsFor(selected);
    if (spec.objective) rows.push(["Objective", spec.objective]);   // what this object is for, last on the card
    for (const [label, value] of rows) {
      const dt = document.createElement("dt"); dt.textContent = label;
      const dd = document.createElement("dd");
      dd.textContent = value;
      list.append(dt, dd);
    }
    card.appendChild(list);
    about.appendChild(card);
  }
  setTab(detailsTab);   // the same tab as before, for the new selection
}
const isTargetNote = note => /^(Target|No target)/.test(note || "");   // which of a card's notes states its target
// The event stream: what the engine has just done, newest first. About thirty lines show; the rest
// can be scrolled to. While it is scrolled away from the top it stands still, so it can be read.
function renderEvents() {
  const box = $("events");
  if (folds.events) setText($("events-total"), `${desEngine.snapshot().eventsProcessed.toLocaleString("en-US")} events processed`);
  if (!folds.events || !$("panel").classList.contains("open") || box.scrollTop > 0) return;
  const lines = desRecent.map(event => `${event.timestamp.toFixed(1).padStart(7)}  ${event.type.padEnd(22)} ${event.entityId.padEnd(5)} ${event.resourceId || ""}`).join("\n");
  if (box.textContent !== lines) box.textContent = lines;
}
// folding a section by its header, and switching tabs
for (const section of document.querySelectorAll(".fold")) {
  section.querySelector("header").addEventListener("click", () => setFold(section.dataset.fold, !folds[section.dataset.fold]));
}
for (const button of $("tabs").children) button.addEventListener("click", () => setTab(button.dataset.tab));
