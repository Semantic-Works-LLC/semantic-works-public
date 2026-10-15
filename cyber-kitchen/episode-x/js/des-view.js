// ---------- Floor plan view ----------
// A passive renderer of the one DES engine: the restaurant's physical layout and who is where in it.
// The resource meters are on the process map and the operations figures on the scorecard. It only reads the
// engine's snapshots and events; nothing here is derived from where a sprite is, and movement on the
// floor plan is interpolation for the eye. Everything drawn can be selected.
const desStatic = $("des-static"), desFloor = $("des-floor-static");
const desProgress = (since, until, now) => until === null ? 0 : Math.min(1, (now - since) / Math.max(until - since, 1e-9));
const DES_TABLE_CLASS = {
  READING_MENU: "reading", WAITING_FOR_WAITER_ORDER: "ready", ORDERING: "ordering", WAITING_FOR_COOK: "waiting", PLANNING: "waiting", COOKING: "waiting",
  WAITING_FOR_PLATING: "waiting", PLATING: "waiting", WAITING_FOR_WAITER_DELIVER: "waiting", FOOD_RUNNING: "waiting", EATING_AND_BILLING: "eating",
};
// a node whose party changes from frame to frame: clicking it selects whoever is shown in it
function desPartySlot(g) {
  const slot = { g, id: null };
  g.setAttribute("data-selectable", "");
  g.addEventListener("click", e => { e.stopPropagation(); if (slot.id && desEngine.parties.has(slot.id)) select(desPartyInfo(slot.id)); });
  return slot;
}
function desShowSlot(slot, id) {
  slot.id = id || null;
  slot.g.setAttribute("visibility", id ? "visible" : "hidden");
  slot.g.toggleAttribute("data-selected", Boolean(id) && selected !== null && desPartyInfos.get(id) === selected);
}

// ----- the physical floor plan, in the floor view's own coordinates (the group is drawn at half size)
const desBig = "font-size: 19px";
el("rect", { x: 60, y: 70, width: 730, height: 600, fill: "var(--floor-dining)" }, desFloor);
el("rect", { x: 790, y: 70, width: 390, height: 600, fill: "var(--floor-kitchen)" }, desFloor);
el("path", { class: "wall", d: "M60 245 V70 H1180 V670 H60 V295" }, desFloor);
el("path", { class: "wall", d: "M790 70 V230 M790 310 V425 M790 505 V670" }, desFloor);
text("DINING ROOM", { class: "zone-label", x: 76, y: 100, style: desBig }, desFloor);
text("KITCHEN", { class: "zone-label", x: 806, y: 100, style: desBig }, desFloor);
function desFloorObject(info, draw) {
  const g = el("g", {}, desFloor);
  draw(g);
  desAttach(g, info);
  return g;
}
desFloorObject(DES_QUEUE.host.info, g => {
  el("rect", { x: 0, y: 225, width: 76, height: 80, fill: "transparent" }, g);
  // the waiting area outside, where parties line up for a table: select it for the host queue
  // a plain rectangle against the side of the building, with its name inside it, under where the parties stand
  el("rect", { class: "des-rail", x: -6, y: 308, width: 66, height: 274, fill: "transparent", stroke: "#6a737b", "stroke-width": 2 }, g);
  ["WAITING", "AREA"].forEach((word, i) => text(word, { class: "small-label", x: 27, y: 558 + i * 14, "text-anchor": "middle", style: "font-size: 12px; text-anchor: middle" }, g));
  // the door seen from above: hinged at the top of the opening and swung open to the outside, with the arc it sweeps
  el("path", { d: "M60 295 A50 50 0 0 1 11.700 257.900", fill: "none", stroke: "#8a6a4a", "stroke-width": 1.5, "stroke-dasharray": "4 4" }, g);
  el("path", { d: "M60 245 L11.700 257.900", fill: "none", stroke: "#c89a6a", "stroke-width": 7, "stroke-linecap": "round" }, g);
});
desFloorObject(DES_QUEUE.plan.info, g => {
  el("rect", { class: "steel", x: 772, y: 230, width: 66, height: 80, rx: 5 }, g);   // the same size as the pass table below it
  ["TICKET", "RAIL"].forEach((word, i) => text(word, { class: "small-label", x: 846, y: 266 + i * 18, style: "font-size: 16px" }, g));   // close to its right; the cook stands beyond the words
});
desFloorObject(DES_QUEUE.run.info, g => {
  el("rect", { class: "steel", x: 772, y: 425, width: 66, height: 80, rx: 5 }, g);   // a kitchen surface, the same steel as the ticket rail
  ["PASS", "TABLE"].forEach((word, i) => text(word, { class: "small-label", x: 846, y: 461 + i * 18, style: "font-size: 16px" }, g));
});
el("rect", { class: "steel", x: 1110, y: 140, width: 62, height: 320, rx: 4 }, desFloor);
text("STOVES", { class: "small-label", x: 1141, y: 130, "text-anchor": "middle", style: "font-size: 16px" }, desFloor);
// equipment: where the cook stands, the glow while it is in use, and the progress bar
const desOutMark = (g, x1, y1, x2, y2) => el("path", { class: "out-mark", d: `M${x1} ${y1}L${x2} ${y2}`, visibility: "hidden" }, g);   // one red line across something that is out of service
function desEquipment(unit, stand, glow, barX, barY, draw, across) {
  const g = desFloorObject(unit.info, draw);
  const flame = el(glow.tag, { class: "flame", ...glow.attrs }, g);
  el("rect", { class: "progress-track", x: barX, y: barY, width: 50, height: 5, rx: 2.5 }, g);
  return { stand, flame, bar: el("rect", { class: "progress-bar", x: barX, y: barY, width: 0, height: 5, rx: 2.5 }, g), out: desOutMark(g, ...across) };
}
const DES_EQUIPMENT = {
  stoves: [200, 400].map((y, i) => desEquipment(DES_RES.stoves.units[i], { x: 1085, y }, { tag: "circle", attrs: { cx: 1141, cy: y, r: 14 } }, 1116, y + 28,
    g => el("circle", { class: "burner", cx: 1141, cy: y, r: 20 }, g), [1121, y + 20, 1161, y - 20])),
  oven: [desEquipment(DES_RES.oven.units[0], { x: 1072, y: 610 }, { tag: "path", attrs: { d: "M1114 630 V608 A20 20 0 0 1 1154 608 V630 Z" } }, 1109, 644, g => {
    el("rect", { class: "steel", x: 1096, y: 560, width: 76, height: 100, rx: 6 }, g);   // steel, like the coffee machine beside it
    el("path", { d: "M1108 632 V606 A26 26 0 0 1 1160 606 V632 Z", fill: "#23272b", stroke: "#6a737b", "stroke-width": 1.5 }, g);
    text("PIZZA OVEN", { class: "small-label", x: 1134, y: 550, "text-anchor": "middle", style: "font-size: 15px" }, g);
  }, [1102, 654, 1166, 566])],
  // beside the pizza oven and the same size, clear of the pass
  coffee: [desEquipment(DES_RES.coffee.units[0], { x: 936, y: 610 }, { tag: "circle", attrs: { cx: 998, cy: 616, r: 8, style: "fill: #6b3d1e" } }, 973, 644, g => {
    el("rect", { class: "steel", x: 960, y: 560, width: 76, height: 100, rx: 6 }, g);
    el("rect", { x: 970, y: 570, width: 56, height: 22, rx: 3, fill: "#23272b" }, g);
    el("circle", { cx: 998, cy: 616, r: 12, fill: "#23272b", stroke: "#6a737b", "stroke-width": 1 }, g);   // dark, not white: white on this floor means a cook
    text("COFFEE", { class: "small-label", x: 998, y: 550, "text-anchor": "middle", style: "font-size: 15px" }, g);
  }, [966, 654, 1030, 566])],
};
// the tables stand where they do in the restaurant floor view; only their geometry is taken from it
const desFloorTables = tables.map((place, i) => {
  const g = desFloorObject(DES_RES.tables.units[i].info, g => {
    place.seats.forEach(seat => el("circle", { class: "seat", cx: seat.x, cy: seat.y, r: 9 }, g));
    if (place.type === "six") el("rect", { class: "table-top", x: place.x - 55, y: place.y - 28, width: 110, height: 56, rx: 6 }, g);
    if (place.type === "round") el("circle", { class: "table-top", cx: place.x, cy: place.y, r: 32 }, g);
    if (place.type === "two") el("rect", { class: "table-top", x: place.x - 27, y: place.y - 27, width: 54, height: 54, rx: 6 }, g);
    text(i + 1, { class: "table-num", x: place.x, y: place.y, style: "font-size: 22px" }, g);
  });
  g.setAttribute("class", "table free");
  const reach = place.type === "six" ? [50, 24] : place.type === "round" ? [22, 22] : [23, 23];
  return { g, place, out: desOutMark(g, place.x - reach[0], place.y + reach[1], place.x + reach[0], place.y - reach[1]) };
});
const desRailTickets = Array.from({ length: 5 }, (_, i) => {
  const slot = desPartySlot(el("g", { visibility: "hidden" }, desFloor)), y = 233 + i * 15;
  el("rect", { class: "ticket", x: 789, y, width: 32, height: 13, rx: 1.5 }, slot.g);
  slot.label = text("", { class: "ticket-text", x: 805, y: y + 6.5, style: "font-size: 11px" }, slot.g);
  return slot;
});
const desPassDishes = Array.from({ length: 6 }, (_, i) => {
  const slot = desPartySlot(el("g", { visibility: "hidden" }, desFloor)), x = 790 + (i % 2) * 30, y = 442 + Math.floor(i / 2) * 23;
  el("circle", { class: "dish", cx: x, cy: y, r: 10, fill: "#f2f2f2", stroke: "#b9b9b9", "stroke-width": 1.5 }, slot.g);
  slot.label = text("", { class: "ticket-text", x, y, style: "font-size: 11px" }, slot.g);
  return slot;
});
const DES_HOME = { waiters: i => ({ x: 760 - Math.floor(i / 2) * 34, y: 350 + (i % 2) * 42 }), cooks: i => ({ x: 960 - Math.floor(i / 2) * 40, y: 300 + (i % 2) * 120 }) };

// ----- drawing: read a snapshot, render it
const desTokens = new Map();
let desFresh = true, desLast = 0;
const desGuestToken = () => g => el("circle", { class: "guest", r: 10, fill: "#b9bcc0" }, g);   // every guest the same grey, as the parties are on the process map
const desStaffToken = (label, dark) => g => {
  if (!dark) el("rect", { x: -8, y: -24, width: 16, height: 12, rx: 4, fill: "#fff", stroke: "#0d0d0d", "stroke-width": 1 }, g);
  el("circle", { class: "person", r: 14, fill: dark ? "#0d0d0d" : "#fff", stroke: dark ? "#fff" : "#0d0d0d", "stroke-width": dark ? 2.5 : 1.5 }, g);
  text(label, { class: "token-text", style: `font-size: 13px; fill: ${dark ? "#fff" : "#0d0d0d"}` }, g);
};
function desPlace(token, x, y, from) {
  token.tx = x; token.ty = y;
  if (token.x !== null) return;
  token.x = desFresh || !from ? x : from.x; token.y = desFresh || !from ? y : from.y;
}

function drawDes() {
  const frame = performance.now(), ease = 1 - Math.exp(-Math.min(frame - desLast, 100) / 160);
  desLast = frame;
  const s = desEngine.snapshot(), now = s.time;

  // floor plan: guests
  for (const token of desTokens.values()) token.live = false;
  for (const party of s.parties.values()) {
    const table = desFloorTables[party.table], slot = s.queues.host.indexOf(party.id);
    for (let k = 0; k < party.size; k++) {
      const token = viewToken(desTokens, "des-floor-tokens", `${party.id}:${k}`, desPartyInfo(party.id), desGuestToken(party));
      if (table) desPlace(token, table.place.seats[k].x, table.place.seats[k].y, DOOR);
      else desPlace(token, 18 + (k % 2) * 20, 330 + slot * 76 + Math.floor(k / 2) * 19, OUTSIDE);
      token.home = OUTSIDE;   // a party that has departed walks out of the door
    }
  }
  desFloorTables.forEach((table, i) => {
    const unit = s.resources.tables.units[i], name = "table " + (unit ? DES_TABLE_CLASS[s.parties.get(unit.party).state] : "free");
    if (table.g.getAttribute("class") !== name) table.g.setAttribute("class", name);
    table.out.setAttribute("visibility", unit === DES_OUT ? "visible" : "hidden");
  });
  // floor plan: staff stand where their task is; a waiter running food is as far along as the task is
  s.resources.waiters.units.forEach((unit, i) => {
    if (unit === false || unit === DES_OUT) return;   // not on shift, or off sick: not on the floor
    const token = viewToken(desTokens, "des-floor-tokens", "waiter" + i, DES_RES.waiters.units[i].info, desStaffToken("W", true));
    const home = DES_HOME.waiters(i), at = unit && tables[s.parties.get(unit.party).table].sp;
    if (!unit) desPlace(token, home.x, home.y);
    else if (unit.task === "deliver") {
      const k = desProgress(unit.since, unit.until, now);
      desPlace(token, PASS_WAITER.x + (at.x - PASS_WAITER.x) * k, PASS_WAITER.y + (at.y - PASS_WAITER.y) * k);
    } else desPlace(token, at.x, at.y);
  });
  s.resources.cooks.units.forEach((unit, i) => {
    if (unit === false || unit === DES_OUT) return;   // not on shift, or off sick: not on the floor
    const token = viewToken(desTokens, "des-floor-tokens", "cook" + i, DES_RES.cooks.units[i].info, desStaffToken("C", false));
    const home = DES_HOME.cooks(i), party = unit && s.parties.get(unit.party);
    // at the equipment it is using for that party (found from the equipment's side: the party may have walked out meanwhile)
    const at = !unit ? home : unit.task === "plan" ? RAIL_COOK : unit.task === "plate" ? PASS_COOK
      : DES_EQUIPMENT[unit.task][Math.max(0, s.resources[unit.task].units.findIndex(one => one && one.party === unit.party))].stand;
    desPlace(token, at.x, at.y);
  });
  glideTokens(desTokens, ease);
  for (const kind in DES_EQUIPMENT) {
    DES_EQUIPMENT[kind].forEach((equipment, i) => {
      const unit = s.resources[kind].units[i];
      equipment.flame.style.opacity = unit ? 0.65 + 0.35 * Math.sin(now * 10) : 0;
      equipment.out.setAttribute("visibility", unit === DES_OUT ? "visible" : "hidden");
      equipment.bar.setAttribute("width", unit ? 50 * desProgress(unit.since, unit.until, now) : 0);
    });
  }
  const tableOf = id => s.parties.get(id).table + 1;
  desRailTickets.forEach((slot, i) => { const id = s.queues.plan[i]; desShowSlot(slot, id); if (id) setText(slot.label, tableOf(id)); });
  desPassDishes.forEach((slot, i) => { const id = s.queues.run[i]; desShowSlot(slot, id); if (id) setText(slot.label, tableOf(id)); });

  desFresh = false;
}
