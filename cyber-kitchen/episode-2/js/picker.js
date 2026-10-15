// The always-present list of moving actors: staff, guest parties and open orders.
const actorRows = new Map();
function updateActorList() {
  if ($("picker").hidden) return;
  const query = $("picker-filter").value.trim().toLowerCase();
  const groups = [
    ["Order tickets, open", "orders", () => tickets.map(t => t.info), "No open orders."],
    ["Order tickets, delivered (last 10)", "delivered", () => delivered.map(t => t.info), "Nothing delivered yet."],
    ["Waiters", "waiters", () => waiters.map(s => s.info)],
    ["Cooks", "cooks", () => cooks.map(s => s.info)],
    ["Guest parties", "guests", () => parties.map(p => p.info), "No guests at the moment."],
    ["Tables", "tables", () => fixedObjects.filter(o => o.kind === "Table")],
    ["Hand-off points", "handoff", () => fixedObjects.filter(o => o.kind === "Hand-off point" || o.kind === "Entrance")],
    ["Kitchen equipment", "equipment", () => fixedObjects.filter(o => o.kind === "Kitchen equipment")],
  ];
  const list = $("actor-list");
  for (const [title, key, getInfos, emptyText] of groups) {
    let box = list.querySelector(`[data-group="${key}"]`);
    if (!box) {
      const group = document.createElement("details"); group.open = key !== "delivered";
      group.appendChild(document.createElement("summary"));
      box = document.createElement("div"); box.dataset.group = key;
      group.appendChild(box); list.appendChild(group);
    }
    const infos = getInfos();
    const heading = `${title} (${infos.length})`, summary = box.previousSibling;
    if (summary.textContent !== heading) summary.textContent = heading;
    box.parentNode.hidden = query !== "" && !infos.some(i => (i.listName || i.name).toLowerCase().includes(query));
    for (const [info, row] of actorRows) {
      if (row.parentNode === box && !infos.includes(info)) { row.remove(); actorRows.delete(info); }
    }
    let none = box.querySelector(".none");
    if (!infos.length && !none && emptyText) {
      none = document.createElement("p"); none.className = "none"; none.textContent = emptyText; box.appendChild(none);
    } else if (infos.length && none) none.remove();
    for (const info of infos) {
      let row = actorRows.get(info);
      if (!row) {
        row = document.createElement("button"); row.className = "actor";
        row.textContent = info.listName || info.name;
        row.addEventListener("click", () => select(info));
        actorRows.set(info, row);
        box.appendChild(row);
      }
      row.setAttribute("aria-pressed", info === selected);
      row.hidden = !row.textContent.toLowerCase().includes(query);
    }
  }
}
const clockText = t => Math.floor(t / 60) + ":" + String(Math.floor(t % 60)).padStart(2, "0");
