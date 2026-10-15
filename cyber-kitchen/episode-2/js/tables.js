// tables
const tables = [];
LAYOUT.forEach((row, r) => row.forEach((type, c) => {
  const x = COLS[c], y = ROWS[r], id = tables.length + 1;
  const g = el("g", { class: "table free" }, furniture);
  const table = {
    id, type, x, y, g, status: "free", party: null, timer: 0, since: 0, claimed: false,
    capacity: SEATS[type].length,
    seats: SEATS[type].map(([dx, dy]) => ({ x: x + dx, y: y + dy })),
    sp: { x, y: y + SERVICE[r].dy, aisle: SERVICE[r].aisle },
  };
  table.seats.forEach(s => el("circle", { class: "seat", cx: s.x, cy: s.y, r: 9 }, g));
  if (type === "six") el("rect", { class: "table-top", x: x - 55, y: y - 28, width: 110, height: 56, rx: 6 }, g);
  if (type === "round") el("circle", { class: "table-top", cx: x, cy: y, r: 32 }, g);
  if (type === "two") el("rect", { class: "table-top", x: x - 27, y: y - 27, width: 54, height: 54, rx: 6 }, g);
  table.plates = table.seats.map(s => {
    const dist = Math.hypot(s.x - x, s.y - y), k = (dist - PLATE_INSET[type]) / dist;
    return el("circle", { class: "plate", cx: x + (s.x - x) * k, cy: y + (s.y - y) * k, r: 5 }, g);
  });
  text(id, { class: "table-num", x, y }, g);
  const bubble = el("g", { class: "bubble" }, g);
  const bx = type === "six" ? x + 55 : x + 30, by = y - 30;
  el("circle", { cx: bx, cy: by, r: 9, fill: "var(--ready)", stroke: "#0d0d0d", "stroke-width": 1.5 }, bubble);
  text("!", { x: bx, y: by, fill: "#0d0d0d", "font-size": 12, "font-weight": 700, "text-anchor": "middle", "dominant-baseline": "central" }, bubble);
  table.title = el("title", {}, g);
  const shape = { six: "rectangular", round: "round", two: "small square" }[type];
  table.info = selectable(g, {
    kind: "Table", name: `Table ${id}`,
    what: `A ${shape} table that seats ${table.capacity}.`,
    purpose: "Where a party of guests sits, orders and eats. Its colour shows what stage the party is at.",
    why: "Tables are what the restaurant has to sell. Each time one is filled and freed again it earns money, and its size decides which parties it can take.",
    extra: [["Order at this table", () => !table.party ? "Nobody is sitting here." : table.party.ticket ? table.party.ticket.lines : "Not ordered yet."]],
  });
  tables.push(table);
}));

const STATUS_TEXT = {
  free: "free", reserved: "guests arriving", reading: "reading the menu", ready: "wants to order",
  ordering: "ordering", waiting: "waiting for food", eating: "eating",
};
function setStatus(table, status) {
  table.status = status;
  table.since = clock;
  table.g.setAttribute("class", "table " + status);
  table.title.textContent = `Table ${table.id} (seats ${table.capacity}): ${STATUS_TEXT[status]}`;
  table.plates.forEach((p, i) => p.classList.toggle("on", status === "eating" && table.party && i < table.party.size));
}
