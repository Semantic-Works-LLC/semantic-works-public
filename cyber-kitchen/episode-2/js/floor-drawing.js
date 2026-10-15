// ---------- static drawing ----------
const floor = $("floor"), furniture = $("furniture");
el("rect", { x: 60, y: 70, width: 730, height: 600, fill: "var(--floor-dining)" }, floor);
el("rect", { x: 790, y: 70, width: 390, height: 600, fill: "var(--floor-kitchen)" }, floor);
// outer walls, with a gap for the front door
el("path", { class: "wall", d: "M60 245 V70 H1180 V670 H60 V295" }, floor);
// wall between dining room and kitchen, with gaps for the order rail and the pass
el("path", { class: "wall", d: "M790 70 V230 M790 310 V425 M790 505 V670" }, floor);
text("DINING ROOM", { class: "zone-label", x: 76, y: 94 }, floor);
text("KITCHEN", { class: "zone-label", x: 806, y: 94 }, floor);
text("ENTRANCE", { class: "small-label", x: 30, y: 236, "text-anchor": "middle" }, floor);

// front door
const doorG = el("g", {}, furniture);
el("rect", { x: 48, y: 245, width: 24, height: 50, fill: "transparent" }, doorG);
el("rect", { x: 57, y: 247, width: 6, height: 46, rx: 3, fill: "#8a6a4a" }, doorG);
selectable(doorG, {
  kind: "Entrance", name: "Front door",
  what: "The way in and out of the dining room.",
  purpose: "Guests arrive and leave here. When no free table fits a party, they wait outside by the door.",
  why: "It is where demand shows up. A queue here means the room is full, and parties who give up are lost business.",
});

// order rail (in the wall opening) and the small pass table
const railG = el("g", {}, furniture);
el("rect", { x: 772, y: 228, width: 36, height: 84, fill: "transparent" }, railG);
el("rect", { class: "steel", x: 784, y: 230, width: 12, height: 80, rx: 3 }, railG);
text("ORDER RAIL", { class: "small-label", x: 806, y: 224 }, railG);
selectable(railG, {
  kind: "Hand-off point", name: "Order rail",
  what: "A rail in the wall between the dining room and the kitchen that holds paper order tickets.",
  purpose: "A waiter hangs each ticket here after taking an order. A cook takes the oldest ticket when free.",
  why: "It passes orders from the dining room to the kitchen without waiters and cooks having to meet. Tickets piling up here mean the kitchen is behind.",
});
const passG = el("g", {}, furniture);
el("rect", { x: 772, y: 425, width: 66, height: 80, rx: 5, fill: "var(--wood)", stroke: "#8a6a4a", "stroke-width": 2 }, passG);
text("PASS", { class: "small-label", x: 805, y: 520, "text-anchor": "middle" }, passG);
selectable(passG, {
  kind: "Hand-off point", name: "Pass table",
  what: "A small table in the opening between the kitchen and the dining room.",
  purpose: "Cooks put finished plates here. A waiter collects them and takes them to the guests.",
  why: "It passes food from the kitchen back to the dining room. Plates sitting here are getting cold, so a full pass means the waiters are behind.",
});

// kitchen equipment
// scenery: drawn for context, not part of the simulation, and not selectable
function equipment(label, x, y, width) {
  el("rect", { class: "steel", x, y, width, height: 36, rx: 3 }, furniture);
  text(label, { class: "small-label", x: x + width / 2, y: y + 22, "text-anchor": "middle" }, furniture);
}
equipment("PREP COUNTER", 900, 78, 200);
equipment("SINK", 850, 626, 110);
equipment("FRIDGE", 980, 626, 120);
el("rect", { class: "steel", x: 1110, y: 140, width: 62, height: 320, rx: 4 }, furniture);
text("STOVES", { class: "small-label", x: 1141, y: 132, "text-anchor": "middle" }, furniture);
