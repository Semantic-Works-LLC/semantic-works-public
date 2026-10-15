// ---------- selection ----------
// One object can be selected at a time; its "about" card is shown in the side panel.
let selected = null;
const fixedObjects = [];   // tables and equipment: always present, so they are always in the list
function selectable(nodes, info) {
  info.nodes = [].concat(nodes);
  if (!["Guests", "Waiter", "Cook", "Flow step"].includes(info.kind)) fixedObjects.push(info);
  info.nodes.forEach(node => {
    node.setAttribute("data-selectable", "");
    node.addEventListener("click", e => { e.stopPropagation(); select(info); });
  });
  return info;
}
function select(info) {
  if (selected) selected.nodes.forEach(node => node.removeAttribute("data-selected"));
  selected = info;
  if (info) { info.nodes.forEach(node => node.setAttribute("data-selected", "")); setPanel(true); setPicker(false); }
  renderCard();
}
function setPanel(open) {
  $("panel").classList.toggle("open", open);
  renderMetrics();
  $("panel-toggle").setAttribute("aria-pressed", open);
  $("panel-toggle").textContent = open ? "Hide details" : "Show details";
}
let liveRows = [];
function setPicker(open) {
  $("picker").hidden = !open;
  $("picker-toggle").setAttribute("aria-expanded", open);
  if (open) { $("picker-filter").value = ""; updateActorList(); $("picker-filter").focus(); }
}
function renderCard() {
  const about = $("about");
  about.replaceChildren();
  liveRows = [];
  if (!selected) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "Nothing selected. Click a table, a person, a ticket or a piece of equipment in the live view, or use the \u{1F50D} button at the top to pick one by name.";
    about.appendChild(empty);
  } else {
    const card = document.createElement("div"); card.className = "about";
    const kind = document.createElement("span"); kind.className = "kind"; kind.textContent = selected.kind;
    const name = document.createElement("h3"); name.textContent = selected.name;
    const list = document.createElement("dl");
    // the about card holds only what does not change; anything live belongs to the metrics below it
    const rows = [["What it is", selected.what], ["Purpose", selected.purpose], ["Why it is here", selected.why],
                  ...(selected.extra || []).filter(row => typeof row[1] !== "function")];
    for (const [label, value] of rows) {
      const dt = document.createElement("dt"); dt.textContent = label;
      const dd = document.createElement("dd");
      if (typeof value === "function") liveRows.push([dd, value]); else dd.textContent = value;
      list.append(dt, dd);
    }
    card.append(kind, name, list);
    about.appendChild(card);
    $("panel").querySelector(".panel-inner").scrollTop = 0;
  }
  updateNow();
  renderMetrics();
}
function updateNow() {
  for (const [dd, fn] of liveRows) {
    const value = fn();
    if (dd.textContent !== value) dd.textContent = value;
  }
}
