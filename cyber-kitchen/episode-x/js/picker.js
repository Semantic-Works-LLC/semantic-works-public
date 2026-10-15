// ---------- picking an object by name ----------
// The list behind the target button: everything in the engine that has a card, in groups.
const pickerRows = new Map();
const onShift = id => DES_RES[id].units.filter((_, i) => desEngine.resources[id].units[i] !== false).map(unit => unit.info);
const PICKER_GROUPS = [
  ["Parties", "parties", () => [...desEngine.parties.keys()].map(desPartyInfo), "No parties at the moment."],
  ["Steps", "steps", () => Object.values(DES_TASKS).map(task => task.info)],
  ["Tables", "tables", () => DES_RES.tables.units.map(unit => unit.info)],
  ["Waiters", "waiters", () => onShift("waiters"), "No waiters on shift."],
  ["Cooks", "cooks", () => onShift("cooks"), "No cooks on shift."],
  ["Kitchen equipment", "equipment", () => ["stoves", "oven", "coffee"].flatMap(id => DES_RES[id].units.map(unit => unit.info))],
  ["Resource pools", "pools", () => Object.values(DES_RES).map(res => res.info)],
  ["Outcomes", "outcomes", () => [desPartiesInfo, desArrivalsInfo, ...Object.values(DES_OUTCOME).map(outcome => outcome.info)]],
  ["Scorecard", "score", () => SCORE.map(tile => tile.info)],
];
function updateActorList() {
  if ($("picker").hidden) return;
  const query = $("picker-filter").value.trim().toLowerCase(), list = $("actor-list");
  for (const [title, key, getInfos, emptyText] of PICKER_GROUPS) {
    let box = list.querySelector(`[data-group="${key}"]`);
    if (!box) {
      const group = document.createElement("details"); group.open = true;
      group.appendChild(document.createElement("summary"));
      box = document.createElement("div"); box.dataset.group = key;
      group.appendChild(box); list.appendChild(group);
    }
    const infos = getInfos(), heading = `${title} (${infos.length})`, summary = box.previousSibling;
    if (summary.textContent !== heading) summary.textContent = heading;
    box.parentNode.hidden = query !== "" && !infos.some(info => info.name.toLowerCase().includes(query));
    for (const [info, row] of pickerRows) {
      if (row.parentNode === box && !infos.includes(info)) { row.remove(); pickerRows.delete(info); }
    }
    let none = box.querySelector(".none");
    if (!infos.length && !none && emptyText) {
      none = document.createElement("p"); none.className = "none"; none.textContent = emptyText; box.appendChild(none);
    } else if (infos.length && none) none.remove();
    for (const info of infos) {
      let row = pickerRows.get(info);
      if (!row) {
        row = document.createElement("button"); row.className = "actor";
        row.textContent = info.name;
        row.addEventListener("click", () => select(info));
        pickerRows.set(info, row);
        box.appendChild(row);
      }
      row.setAttribute("aria-pressed", info === selected);
      row.hidden = !row.textContent.toLowerCase().includes(query);
    }
  }
}
