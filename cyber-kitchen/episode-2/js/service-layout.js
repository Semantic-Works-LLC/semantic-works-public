// ---------- service view ----------
// The second view of the same simulation. Top row: the states a party goes through, left to right.
// Below: the two queues, modelled as things of their own (the order rail and the pass), and the
// cooking between them. Waiters shuttle between the party states and the queues; cooks shuttle
// between the queues and the stations.
const PARTY_BOXES = [
  { name: "At the door", steps: ["door"] }, { name: "Walk in", steps: ["walkIn"] },
  { name: "Read menu", steps: ["menu"] }, { name: "Wait to order", steps: ["wantOrder"] },
  { name: "Order", steps: ["ordering"] }, { name: "Wait for food", steps: KITCHEN_STEPS },
  { name: "Eat", steps: ["eating"] }, { name: "Leave", steps: ["leaving"] },
];
const LOOP = { x0: 24, w: 130, pitch: 146, y: 84, h: 150, dock: 254 };
const LOOP_QUEUES = {
  rail: { name: "Order rail", x: 618, y: 292, w: 110, h: 124, step: "rail", object: "Order rail" },
  pass: { name: "Pass", x: 764, y: 292, w: 110, h: 124, step: "pass", object: "Pass table" },
};
const KITCHEN = { x: 608, y: 470, w: 276, h: 196 };
const loopStatic = $("loop-static");
const BOX_OF = {};
PARTY_BOXES.forEach((box, i) => {
  box.x = LOOP.x0 + i * LOOP.pitch;
  box.steps.forEach(key => BOX_OF[key] = box);
  box.key = "box" + i;
  const g = el("g", { class: "step work" }, loopStatic);
  if (box.steps[0] === "door") alsoSelectable(g, floorObject("Front door"));
  else selectable(g, box.steps.length === 1 ? FLOW[box.steps[0]].info : WAIT_FOR_FOOD);
  el("rect", { class: "flow-box", x: box.x, y: LOOP.y, width: LOOP.w, height: LOOP.h, rx: 6 }, g);
  text(box.name, { class: "line-name", x: box.x + LOOP.w / 2, y: LOOP.y + 20 }, g);
  box.avg = text("", { class: "line-avg", x: box.x + LOOP.w / 2, y: LOOP.y + 35 }, g);
  if (i) el("path", { class: "line-arrow", d: `M${box.x - 12} ${LOOP.y + 12}l8 5l-8 5z` }, loopStatic);
});
for (const queue of Object.values(LOOP_QUEUES)) {
  const g = el("g", { class: "step wait" }, loopStatic);
  el("rect", { class: "flow-box", x: queue.x, y: queue.y, width: queue.w, height: queue.h, rx: 18 }, g);
  text("QUEUE", { class: "line-tag", x: queue.x + queue.w / 2, y: queue.y + 15 }, g);
  text(queue.name, { class: "line-name", x: queue.x + queue.w / 2, y: queue.y + 30 }, g);
  queue.avg = text("", { class: "line-avg", x: queue.x + queue.w / 2, y: queue.y + 43 }, g);
  alsoSelectable(g, floorObject(queue.object));
}
// the path of an order: down from Order to the rail, through the kitchen, and up from the pass
for (const d of ["M650 236V288", "M650 420V466", "M846 466V420", "M846 288V236"]) {
  el("path", { class: "loop-arrow", d, "marker-end": "url(#loop-arrow)" }, loopStatic);
}
text("ticket", { class: "small-label", x: 644, y: 266, "text-anchor": "end" }, loopStatic);
text("food", { class: "small-label", x: 852, y: 266 }, loopStatic);
const kitchenG = el("g", { class: "step work" }, loopStatic);
el("rect", { class: "flow-box", x: KITCHEN.x, y: KITCHEN.y, width: KITCHEN.w, height: KITCHEN.h, rx: 6 }, kitchenG);
text("Cook", { class: "line-name", x: KITCHEN.x + 30, y: KITCHEN.y + 20 }, kitchenG);
const kitchenAvg = text("", { class: "line-avg", x: KITCHEN.x + 30, y: KITCHEN.y + 35 }, kitchenG);
selectable(kitchenG, FLOW.cooking.info);
stations.forEach((station, i) => {
  const x = KITCHEN.x + 6 + i * 67, y = KITCHEN.y + 62, name = station.info.name.replace(" machine", "");
  station.spot = { x: x + 22, y: y + 62 };
  const slot = el("g", {}, kitchenG);
  el("rect", { class: "loop-station", x, y, width: 63, height: 126, rx: 5 }, slot);
  text(name, { class: "line-avg", x: x + 31.5, y: y + 16 }, slot);
  el("rect", { class: "progress-track", x: x + 6, y: y + 24, width: 51, height: 5, rx: 2.5 }, slot);
  station.loopBar = el("rect", { class: "progress-bar", x: x + 6, y: y + 24, width: 0, height: 5, rx: 2.5 }, slot);
  alsoSelectable(slot, station.info);
});
// the twelve tables, coloured as on the floor plan
el("rect", { class: "loop-area", x: 24, y: 292, width: 326, height: 374, rx: 8 }, loopStatic);
text("TABLES", { class: "zone-label", x: 36, y: 314, style: "font-size: 10px" }, loopStatic);
text("colour shows what the party is doing; small number is seats", { class: "small-label", x: 36, y: 654 }, loopStatic);
tables.forEach((table, i) => {
  const x = 40 + (i % 4) * 76, y = 328 + Math.floor(i / 4) * 102;
  table.mini = el("g", { class: "table free" }, loopStatic);
  el("rect", { class: "table-top", x, y, width: 66, height: 86, rx: 6 }, table.mini);
  text(table.id, { class: "table-num", x: x + 33, y: y + 44, style: "font-size: 18px" }, table.mini);
  text(table.capacity, { class: "table-num", x: x + 54, y: y + 13, style: "font-size: 10px; font-weight: 500" }, table.mini);
  alsoSelectable(table.mini, table.info);
});
const FREE_AREAS = {
  waiter: { x: 366, y: 318, label: "WAITERS, FREE", one: "waiter" },
  cook: { x: 366, y: 528, label: "COOKS, FREE", one: "cook" },
};
for (const [kind, area] of Object.entries(FREE_AREAS)) {
  el("rect", { class: "loop-area", x: area.x, y: area.y, width: 200, height: 62, rx: 8 }, loopStatic);
  text(area.label, { class: "zone-label", x: area.x, y: area.y - 9, style: "font-size: 10px" }, loopStatic);
  area.total = text("", { class: "small-label", x: area.x + (kind === "waiter" ? 106 : 93), y: area.y - 9 }, loopStatic);
  [["\u2212", -1, `One ${area.one} fewer`], ["+", 1, `One more ${area.one}`]].forEach(([sign, by, label], i) => {
    const g = el("g", { class: "loop-button", role: "button", "aria-label": label, transform: `translate(${area.x + 156 + i * 24} ${area.y - 24})` }, loopStatic);
    el("title", {}, g).textContent = label;
    el("rect", { width: 20, height: 20, rx: 5 }, g);
    text(sign, { x: 10, y: 10.5 }, g);
    g.addEventListener("click", e => { e.stopPropagation(); changeStaff(kind, by); });
  });
}
