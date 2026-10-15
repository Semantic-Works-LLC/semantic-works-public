// ---------- pipeline graph ----------
// The pipeline view: the DES engine's pipeline drawn as a graph of steps, in the order the engine moves a
// party through them, with the fork where an order is split into parts and the join where they come
// back together. A step is one box. If the step needs something (a table, a waiter, a cook, a piece of
// equipment, the order's other parts), the left part of its box is a dashed grey area where parties wait
// until all of it is there; then they move to the middle and the step runs. A step that needs nothing
// has no waiting area. The resources themselves are on the DES view. A third passive renderer of the
// same engine (after the floor plan and the dashboard of the DES view).
const graphStatic = $("graph-static");
// One line, left to right. The three kitchen parts are stacked in one column, with the main line through the middle one.
// Three sections under one another, divided by lines across the map: Resources (a fifth of the height),
// Process (three fifths) and Outcomes (a fifth).
const GRAPH_TOP_Y = 64, GRAPH_HEIGHT = 680;   // 64: as far from the top of the picture as from its sides
const GRAPH_SECTION = { resources: GRAPH_TOP_Y, process: GRAPH_TOP_Y + 0.2 * GRAPH_HEIGHT, outcomes: GRAPH_TOP_Y + 0.8 * GRAPH_HEIGHT, end: GRAPH_TOP_Y + GRAPH_HEIGHT };
const GB = { h: 96, gap: 32, rows: [0, 1, 2].map(i => GRAPH_SECTION.process + 34 + i * 128), wait: 48 };   // 32 between boxes, so the arrows have room; the rows sit in the middle of the Process section
// the resources along the top (drawn further down, once the boxes can be: see GRAPH_TOP)
const graphMetersLayer = el("g", {}, graphStatic);
const graphSectionLayer = el("g", {}, graphStatic);   // the lines and headings of the three sections
const GB_WIDTH = { seating: 106, browsing: 74, ordering: 106, planning: 106, part: 8 + 2 * GB.wait + 8, plating: 106, running: 120, dining: 54 };   // a kitchen part is its waiting area and as much again beside it
const GRAPH = {};
const GRAPH_STRIPE = "#eab308";   // one colour for every step: a step with nothing to wait for is still just a step

// the places for tokens in one area of a box
const graphArea = (x, y, per, more, rows = 3, rowPitch = 18) => ({ x, y, per, rows, rowPitch, more });
function graphSpot(area, n) {
  const i = Math.min(n, area.per * area.rows - 1);
  return { x: area.x + (i % area.per) * 18.5, y: area.y + Math.floor(i / area.per) * area.rowPitch };
}
function graphBox(key, x, y, w) {
  const task = DES_TASKS[key], { h } = GB, g = el("g", { "data-step": key }, graphStatic);
  const fit = from => Math.floor((w - from - 13.5) / 18.5) + 1;   // how many tokens fit in a row from there to the right edge
  el("rect", { class: "des-stage graph-node", x, y, width: w, height: h, rx: 6 }, g);
  el("rect", { x: x + 1.5, y: y + 6, width: 4, height: h - 12, rx: 2, fill: GRAPH_STRIPE }, g);
  // the name at the right, so the waiting area can run the full height; a label says itself where it goes onto a second line
  task.label.split("\n").forEach((line, i) => text(line, { class: "line-name task-name", x: x + w - 7, y: y + 16 + i * 12, style: "text-anchor: end" }, g));
  const box = GRAPH[key] = { key, task, label: task.label.replace("\n", " "), g, x, y, cx: x + w / 2, cy: y + h / 2, right: x + w, bottom: y + h };
  const more = ax => text("", { class: "task-avg", x: ax, y: y + h - 4 }, g);
  if (task.queue) {   // the waiting area: everything the step needs has to be there before it starts
    el("rect", { class: "task-zone queue", x: x + 8, y: y + 6, width: GB.wait, height: h - 12, rx: 12 }, g);
    box.wait = graphArea(x + 22.5, y + 18, 2, text("", { class: "task-avg", x: x + GB.wait, y: y + h - 9 }, g), 4, 19);
    box.active = graphArea(x + 73, y + 39, fit(73), more(x + w - 5));
  } else box.active = graphArea(x + 19, y + 39, fit(19), more(x + w - 5));
  desAttach(g, task.info);
  return box;
}
// the ways out. A way out is drawn as the same box as a step or a resource, with its name at the top
// right and its count in the middle; its edge is green for a visit that ended well and red for one that did not.
const GRAPH_OUTCOME = { w: 108, h: 74 };
function graphEnd(key, x, y, label, info, kind) {
  const g = el("g", { "data-step": key }, graphStatic);   // an outcome can be pinned too, to see where parties come to it from
  const w = GRAPH_OUTCOME.w, h = GRAPH_OUTCOME.h;
  el("rect", { class: "des-stage graph-node", x, y, width: w, height: h, rx: 6 }, g);
  el("rect", { x: x + 1.5, y: y + 6, width: 4, height: h - 12, rx: 2, fill: kind === "won" ? "var(--eating)" : "var(--waiting)" }, g);
  text(label, { class: "line-name task-name", x: x + w - 7, y: y + 16, style: "text-anchor: end" }, g);
  desAttach(g, info);
  return GRAPH[key] = { key, label, g, x, y, cx: x + w / 2, cy: y + h / 2, right: x + w, bottom: y + h, count: text("", { class: "des-stage-count", x: x + w / 2, y: y + h / 2 + 6, style: "font-size: 14px" }, g) };
}
// Where the process starts: a small filled circle, as in a state diagram, with an arrow into the first step.
// It stands for the door: selecting it shows who has arrived.
function graphStart(x, y) {
  const r = 8, g = el("g", { "data-step": "source" }, graphStatic);
  el("title", {}, g).textContent = "Start: parties arrive here";
  el("circle", { r: 14, cx: x, cy: y, fill: "transparent" }, g);   // a bigger target
  el("circle", { class: "graph-node graph-start", cx: x, cy: y, r }, g);
  desAttach(g, desArrivalsInfo);
  return GRAPH.source = { key: "source", label: "start", g, x: x - r, y: y - r, cx: x, cy: y, right: x + r, bottom: y + r };
}
const GRAPH_PARTS = Object.keys(DES_CONFIG.parts);
const GRAPH_OUT_Y = (GRAPH_SECTION.outcomes + GRAPH_SECTION.end - 74) / 2;   // the row of ways out, in the middle of the Outcomes section
// The first three steps go down one column, to save width: the door and Get a table on the top row, then
// View menu under it and Order under that. From Order the line turns up to the middle row and runs on to the right.
const GRAPH_LEAD = 70;   // room on the left for the start and for the way down to "turned away"
graphStart(16 + GRAPH_LEAD / 2, GB.rows[0] + GB.h / 2 - 16);
graphEnd("away", 16, GRAPH_OUT_Y, "turned away", DES_OUTCOME.away.info, "lost");
let graphX = 16 + GRAPH_LEAD + GB.gap;
["seating", "browsing", "ordering"].forEach((key, row) => graphBox(key, graphX + (GB_WIDTH.seating - GB_WIDTH[key]) / 2, GB.rows[row], GB_WIDTH[key]));
graphX += GB_WIDTH.seating + GB.gap;
for (const key of ["planning", "part", "plating", "running", "dining"]) {
  const w = GB_WIDTH[key];
  if (key === "part") GRAPH_PARTS.forEach((kind, i) => graphBox(kind, graphX, GB.rows[i], w));
  else graphBox(key, graphX, GB.rows[1], w);
  graphX += w + GB.gap;
}
// four ways to leave: turned away at the door; having dined; or having given up, either because nobody
// came to take the order or because the food took too long
graphEnd("out", GRAPH.dining.right - GRAPH_OUTCOME.w, GRAPH_OUT_Y, "dined", DES_OUTCOME.out.info, "won");   // against the right edge of the map; the arrow still comes straight down from Dining
graphEnd("noorder", Math.max(GRAPH.ordering.cx - GRAPH_OUTCOME.w / 2, GRAPH.away.right + 16), GRAPH_OUT_Y, "left: slow waiter", DES_OUTCOME.noorder.info, "lost");
graphEnd("hungry", GRAPH.out.x - 16 - GRAPH_OUTCOME.w, GRAPH_OUT_Y, "left: slow kitchen", DES_OUTCOME.hungry.info, "lost");   // beside it, still under Running

// ----- arrows, and the same lines as lists of points for the tokens to follow
const graphEdges = [];
function graphArrow(from, to, ...points) {
  const line = el("path", { class: "loop-arrow", "marker-end": "url(#graph-arrow)", style: "stroke-width: 1.5",
                            d: points.map(([x, y], i) => `${i ? "L" : "M"}${x} ${y}`).join("") }, graphStatic);
  const base = points.map(([x, y]) => ({ x, y }));   // as laid out; `points` is where it is drawn now, which differs while a step is pinned
  graphEdges.push({ from, to, line, base, points: base });
}
const across = (a, b) => graphArrow(a, b, [GRAPH[a].right + 1, GRAPH[b].cy], [GRAPH[b].x - 3, GRAPH[b].cy]);
const down = (a, b) => graphArrow(a, b, [GRAPH[a].cx, GRAPH[a].bottom + 1], [GRAPH[b].cx, GRAPH[b].y - 3]);
for (const [a, b] of [["plating", "running"], ["running", "dining"]]) across(a, b);
graphArrow("source", "seating", [GRAPH.source.right + 1, GRAPH.source.cy], [GRAPH.seating.x - 3, GRAPH.source.cy]);   // from the start into the first step
down("seating", "browsing"); down("browsing", "ordering");
{ // out of Order sideways, up to the middle row, and into Plan
  const turn = GRAPH.ordering.right + GB.gap / 2;
  graphArrow("ordering", "planning", [GRAPH.ordering.right + 1, GRAPH.ordering.cy], [turn, GRAPH.ordering.cy], [turn, GRAPH.planning.cy], [GRAPH.planning.x - 3, GRAPH.planning.cy]);
}
graphArrow("dining", "out", [GRAPH.dining.cx, GRAPH.dining.bottom + 1], [GRAPH.dining.cx, GRAPH.out.y - 3]);
// a seated party that waits too long walks out. Waiting to order: straight down from Ordering.
graphArrow("ordering", "noorder", [GRAPH.ordering.cx, GRAPH.ordering.bottom + 1], [GRAPH.ordering.cx, GRAPH.noorder.y - 3]);
// Waiting for the food: from wherever the order is before the food is run, along one line to the exit.
const hungryY = GRAPH.hungry.cy;
graphArrow("planning", "hungry", [GRAPH.planning.cx, GRAPH.planning.bottom + 1], [GRAPH.planning.cx, hungryY], [GRAPH.hungry.x - 3, hungryY]);
graphArrow("plating", "hungry", [GRAPH.plating.cx, GRAPH.plating.bottom + 1], [GRAPH.plating.cx, hungryY], [GRAPH.hungry.x - 3, hungryY]);   // drawn over the same line, so it stands by itself when Plating is pinned
graphArrow("running", "hungry", [GRAPH.running.cx, GRAPH.running.bottom + 1], [GRAPH.running.cx, GRAPH.hungry.y - 3]);
// a party that finds the line at the door full is turned away: out of Get a table on its left, under the way in, and down
graphArrow("seating", "away", [GRAPH.seating.x - 1, GRAPH.seating.cy + 16], [GRAPH.source.cx, GRAPH.seating.cy + 16], [GRAPH.source.cx, GRAPH.away.y - 3]);
for (const kind of GRAPH_PARTS) {   // the fork out of planning and the join into plating
  const part = GRAPH[kind], out = GRAPH.planning.right + GB.gap / 2, back = part.right + GB.gap / 2;
  if (part.cy === GRAPH.planning.cy) { across("planning", kind); across(kind, "plating"); continue; }   // the middle part is straight on
  graphArrow("planning", kind, [GRAPH.planning.right + 1, GRAPH.planning.cy], [out, GRAPH.planning.cy], [out, part.cy], [part.x - 3, part.cy]);
  graphArrow(kind, "plating", [part.right + 1, part.cy], [back, part.cy], [back, GRAPH.plating.cy], [GRAPH.plating.x - 3, GRAPH.plating.cy]);
}
const graphCentre = key => ({ x: GRAPH[key].cx + (GRAPH[key].dx || 0), y: GRAPH[key].cy + (GRAPH[key].dy || 0) });
let graphRoute = makeRouter(graphEdges, graphCentre);   // while a step is pinned, only the arrows that are shown can be followed

// ----- drawing
const graphTokens = new Map(), graphSeen = new Map();
const graphKnown = new Set();   // the parties that were in the building at the last frame
const graphBalks = [];          // parties turned away at the door since the last frame: they never get inside, so the engine's state never holds them
desEngine.subscribe(event => { if (event.type === "PARTY_BALKED") graphBalks.push(event.entityId); });
// A token that only passes: it sets off from one box along the arrow to another and is gone when it gets there.
function graphPasser(key, from, to, info, build) {
  if (graphTokens.has(key) || !graphRoute(from, to)) return;
  const token = viewToken(graphTokens, "graph-parties", key, info, build), start = graphCentre(from);
  token.x = start.x; token.y = start.y; token.at = from;
  headFor(token, to, graphRoute);
  token.tx = token.route.at(-1).x; token.ty = token.route.at(-1).y;
  token.going = true;
}
let graphFresh = true, graphLast = 0;

// ----- pinning a step
// A pinned step is shown by itself with only what leads into it and out of it, so its neighbourhood can
// be watched. Above it stand the resources it needs, as boxes with a violet edge. Nothing in them moves:
// each unit is a square, lit blue while it is allocated.
let graphPinned = null, graphShown = null, graphPools = [];   // shown: the boxes on screen while a step is pinned
const graphPinLayer = el("g", {}, graphStatic);
const GRAPH_PARTY_COLOUR = "#b9bcc0";   // parties are grey wherever they are drawn
// Actors are the people: parties, waiters and cooks. They have a grey edge. Resources are the things they
// use: tables and kitchen equipment. They have a violet one.
const graphIsActor = id => id === "parties" || DES_STAFF.includes(id);
const graphEdgeColour = id => graphIsActor(id) ? GRAPH_PARTY_COLOUR : GRAPH_RESOURCE.stripe;
const graphArrowHead = id => `url(#graph-arrow-${graphIsActor(id) ? "actor" : "resource"})`;
const GRAPH_RESOURCE = { w: 124, h: 74, stripe: "#a78bfa" };   // violet for every kind of resource; blue is kept for buttons
const GRAPH_APART = 64;   // a pinned view has room to spare: this much between the pinned box and what stands around it
function graphPin(key) {
  for (const pool of graphPools) pool.info.nodes.splice(pool.info.nodes.indexOf(pool.g), 1);   // the old boxes are gone
  graphPinned = key; graphPools = [];
  graphPinLayer.replaceChildren();
  // a pinned step shows what leads into it and out of it; a pinned resource ("res:waiters") shows the steps that need it
  // a pinned party ("party:P12") shows the steps it takes part in, with an arrow to the one it is at
  // all the parties together ("parties") show the same steps, with every party at the one it sees itself at
  const res = graphPinnedResource(key), party = graphPinnedParty(key), everyone = key === "parties", ring = Boolean(res || party || everyone);   // ring: the pinned thing in the middle, steps around it
  // under a party, or all of them, stand the outcomes a visit can end in (one party is already inside, so it cannot be turned away)
  const ends = everyone ? GRAPH_EXITS : party ? GRAPH_EXITS.slice(1) : [];
  graphShown = party || everyone ? new Set([...GRAPH_PARTY_STEPS, ...ends]) : res ? new Set(Object.keys(DES_TASKS).filter(step => (DES_QUEUE_NEEDS[DES_TASKS[step].queue] || []).includes(res)))
    : key && new Set([key, ...graphEdges.filter(edge => edge.to === key).map(edge => edge.from), ...graphEdges.filter(edge => edge.from === key).map(edge => edge.to)]);
  const places = key && !ring ? graphStepPlaces(key) : {};
  for (const box of Object.values(GRAPH)) {
    box.g.style.display = !key || graphShown.has(box.key) ? "" : "none";
    box.dx = key ? 0 : graphAcross(GRAPH_COLUMN[box.key]);
    box.dy = key ? 0 : GRAPH_EXITS.includes(box.key) ? graphSpare : graphSpare / 2;   // on the whole map the steps sit in the middle of their section and the ways out at the bottom
    if (ring && graphShown.has(box.key)) {   // around a pinned resource or party, each step goes to its place on the ring
      // parties: the steps of a visit over the top, from left to right, and the outcomes along the bottom, also from left to right
      const end = ends.indexOf(box.key), step = GRAPH_PARTY_STEPS.indexOf(box.key);
      const place = end >= 0 ? graphRingAt(-Math.PI * (ends.length - end) / (ends.length + 1)) : ends.length ? graphRingAt(Math.PI * (1 - step / (GRAPH_PARTY_STEPS.length - 1)))
        : graphRingPlace([...graphShown].indexOf(box.key), graphShown.size);
      box.dx = place.x - box.cx; box.dy = place.y - box.cy;
    }
    const place = key && !ring && places[box.key];   // around a pinned step, door or outcome
    if (place) { box.dx = place.x - box.x; box.dy = place.y - box.y; }
    box.g.setAttribute("transform", `translate(${box.dx} ${box.dy})`);
  }
  for (const edge of graphEdges) {
    edge.line.style.display = !key || edge.from === key || edge.to === key ? "" : "none";   // pinned: only the arrows to it and from it
    const last = edge.base.length - 1;   // an arrow leaves with the box it starts at and arrives with the box it ends at
    // each point moves with the box it belongs to: the ones in line with the arrow's end with the box it ends at, the rest with the box it starts at
    edge.points = edge.base.map((point, i) => ({ x: point.x + (i === last || point.x === edge.base[last].x ? GRAPH[edge.to].dx : GRAPH[edge.from].dx),
                                                 y: point.y + (key ? 0 : point.y >= GRAPH_SECTION.outcomes ? graphSpare : graphSpare / 2) }));
    // around a pinned step the boxes are not where the arrows were laid out for: draw each arrow afresh between the two boxes
    if (key && !ring && edge.line.style.display !== "none") edge.points = graphLink(edge.from, edge.to);
    edge.line.setAttribute("d", edge.points.map((point, i) => `${i ? "L" : "M"}${point.x} ${point.y}`).join(""));
  }
  graphRoute = makeRouter(graphEdges.filter(edge => edge.line.style.display !== "none"), graphCentre);
  graphMetersLayer.style.display = graphSectionLayer.style.display = key ? "none" : "";
  graphOutcomesMarks.setAttribute("transform", `translate(0 ${graphSpare})`);
  graphFullHeight.setAttribute("height", GRAPH_HEIGHT + graphSpare);
  graphFullHeight.setAttribute("width", GRAPH_SPAN.right - GRAPH_SPAN.left + graphWide);
  for (const rule of graphSectionLayer.querySelectorAll("path")) rule.setAttribute("d", `M${GRAPH_SPAN.left} ${rule.dataset.y}H${GRAPH_SPAN.right + graphWide}`);   // the lines run the full width
  GRAPH_TOP.forEach((pool, i) => {   // and the boxes along the top spread out over it
    pool.g.setAttribute("transform", `translate(${graphAcross(i)} 0)`);
    for (const button of pool.buttons) button.g.setAttribute("transform", `translate(${button.x + graphAcross(i)} ${button.y})`);
  });
  // the frame the picture is measured in grows with it; a pinned picture may reach past the map's own edges
  $("desgraph").dataset.frame = key ? "-400 -300 2000 1600" : `0 52 ${GRAPH_SPAN.right + 12 + graphWide} ${GRAPH_HEIGHT + 24 + graphSpare}`;
  $("desgraph").setAttribute("preserveAspectRatio", key ? "xMidYMid" : "xMidYMin");   // the whole map hangs from the top of its card; a pinned step sits in the middle
  if (party) graphPartyOverSteps(party);
  else if (everyone) graphPartiesOverSteps();
  else if (res) graphResourceOverSteps(res);
  else if (key && GRAPH[key].task) graphResourceBoxes(GRAPH[key]);   // the door and the exits need nothing
  if (key && !ring) graphPinBadge(GRAPH[key].right + GRAPH[key].dx - 1, GRAPH[key].bottom + GRAPH[key].dy - 1);
  graphTokens.forEach(token => token.g.remove());   // start the tokens afresh in the new picture
  graphTokens.clear(); graphSeen.clear(); graphFresh = true;
  refitView();
}
// One resource as a box: a violet edge, its name, and a square per unit that is lit while the unit is
// allocated (waiters and cooks have spare places for when more are put on shift). The other parts of an
// order are drawn the same way with a grey edge: one square per order waiting at the step, lit while
// that order is still short of a part. Used along the top of the whole map and above a pinned step.
function graphResourceBox(parent, id, x, y, withNote, w = GRAPH_RESOURCE.w) {
  const parts = id === "parts", everyone = id === "parties", res = parts || everyone ? null : DES_RES[id];
  const info = parts ? desPartsInfo : everyone ? desPartiesInfo : res.info, stripe = parts ? "#898781" : graphEdgeColour(id);
  const { h } = GRAPH_RESOURCE, perRow = Math.floor((w - 18) / 13), g = el("g", {}, parent);
  el("rect", { class: "des-stage graph-node", x, y, width: w, height: h, rx: 6 }, g);
  el("rect", { x: x + 1.5, y: y + 6, width: 4, height: h - 12, rx: 2, fill: stripe }, g);
  text(parts ? "Other parts of order" : everyone ? "Parties" : res.name, { class: "line-name task-name", x: x + w - 7, y: y + 16, style: "text-anchor: end" }, g);
  desAttach(g, info);
  const count = parts ? 16 : everyone ? 3 * perRow : desEngine.resources[id].units.length;
  const squares = Array.from({ length: count }, (_, k) => el("rect", { class: "study-unit" + (parts ? " part" : everyone ? " party" : ""), x: x + 14 + (k % perRow) * 13, y: y + 28 + Math.floor(k / perRow) * 13, width: 10, height: 10, rx: 2 }, g));
  // each unit can be picked by its own square: table 7 here is the same table 7 as on the floor plan
  if (res) squares.forEach((square, k) => {
    const unit = res.units[k];
    desAttach(square, unit.info);
    square.toggleAttribute("data-selected", unit.info === selected);
    el("title", {}, square).textContent = unit.name;
  });
  // a square of the Parties box stands for whichever party is in that place now: clicking it selects that party
  if (everyone) for (const square of squares) {
    square.setAttribute("data-selectable", "");
    square.style.display = "none";
    el("title", {}, square);
    square.addEventListener("click", e => { e.stopPropagation(); if (desEngine.parties.has(square.dataset.party)) select(desPartyInfo(square.dataset.party)); });
  }
  return { id, parts, everyone, info, g, squares, note: withNote ? text("", { class: "task-avg", x: x + w - 7, y: y + h - 6 }, g) : null };
}
const GRAPH_SPAN = { left: 16, right: Math.max(...Object.values(GRAPH).map(box => box.right)) };
const graphFullHeight = el("rect", { x: GRAPH_SPAN.left, y: GRAPH_SECTION.resources, width: GRAPH_SPAN.right - GRAPH_SPAN.left, height: GRAPH_HEIGHT, fill: "none", style: "pointer-events: none" }, graphSectionLayer);   // nothing to see: it gives the picture its full height, so the sections keep their shares
const graphOutcomesMarks = el("g", {}, graphSectionLayer);   // the Outcomes line and heading, which go down with the section
for (const [name, y] of [["ACTORS & RESOURCES", GRAPH_SECTION.resources], ["TASKS", GRAPH_SECTION.process], ["OUTCOMES", GRAPH_SECTION.outcomes]]) {
  const parent = y === GRAPH_SECTION.outcomes ? graphOutcomesMarks : graphSectionLayer;
  if (y > GRAPH_SECTION.resources) el("path", { "data-y": y, d: `M${GRAPH_SPAN.left} ${y}H${GRAPH_SPAN.right}`, stroke: "var(--hairline)", "stroke-width": 1.5 }, parent);
  // Resources and Process are named at the top of their sections; Outcomes at the very bottom of its own, mirroring Resources
  text(name, { class: "zone-label", x: GRAPH_SPAN.left, y: parent === graphOutcomesMarks ? GRAPH_SECTION.end - 3 : y + 18, style: "font-size: 10px" }, parent);
}
// The map fills the height of its card. Resources stays at the top and Outcomes goes down to the bottom
// edge; the Process section takes the height in between, with the steps in the middle of it. `graphSpare`
// is how much taller the card is than the map as laid out, in the map's own units.
const GRAPH_EXITS = ["away", "noorder", "hungry", "out"];
// A card that is wider than the map spreads the columns of the map out instead: `graphWide` is how much
// wider, and each of the seven columns stands that many sixths further right than the one before.
let graphSpare = 0, graphWide = 0, graphStale = true;   // stale: the layout has to be brought up to date before the next frame is drawn
function graphMeasure() {
  const card = $("desgraph").parentNode, wide = card.clientWidth - 24, high = card.clientHeight - 24;   // 24: the card's padding
  if (wide <= 0 || high <= 0) return;   // not on screen: keep the layout there is
  const width = GRAPH_SPAN.right - GRAPH_SPAN.left + 24, height = GRAPH_HEIGHT + 24;
  const spare = Math.max(0, Math.round(width * high / wide - height)), more = Math.max(0, Math.round(height * wide / high - width));
  if (spare === graphSpare && more === graphWide) return;
  graphSpare = spare; graphWide = more; graphStale = true;
}
// the column a box stands in on the whole map, from the door (0) to Dining (6); a way out stands under the step it is reached from
const GRAPH_COLUMN = { source: 0, seating: 1, browsing: 1, ordering: 1, planning: 2, stoves: 3, oven: 3, coffee: 3, plating: 4, running: 5, dining: 6, away: 0, noorder: 1, hungry: 5, out: 6 };
const graphAcross = column => graphWide * column / 6;
let graphMeasureSoon = 0;
new ResizeObserver(() => { clearTimeout(graphMeasureSoon); graphMeasureSoon = setTimeout(graphMeasure, 150); }).observe($("desgraph").parentNode);   // the window, or the details panel, changed the card
// Along the top: the parties in the building, then every resource, each drawn as the same box a pinned
// step shows, with a square per party or per unit. Seven boxes that together run the full width; waiters
// and cooks have minus and plus above them.
const GRAPH_TOP_BOX = { w: 116, gap: 9 };
const GRAPH_TOP = ["parties", ...Object.keys(DES_RES)].map((id, i, all) => {
  const { w, gap } = GRAPH_TOP_BOX, total = all.length * w + (all.length - 1) * gap;
  const x = (GRAPH_SPAN.left + GRAPH_SPAN.right - total) / 2 + i * (w + gap), y = (GRAPH_SECTION.resources + GRAPH_SECTION.process - GRAPH_RESOURCE.h) / 2;   // in the middle of the section, top to bottom
  const buttons = [];   // minus and plus, which move with their box
  if (DES_STAFF.includes(id)) [["\u2212", -1, `One ${DES_RES[id].one.toLowerCase()} fewer`], ["+", 1, `One more ${DES_RES[id].one.toLowerCase()}`]].forEach(([sign, by, label], k) => {
    const button = el("g", { class: "loop-button", role: "button", "aria-label": label, transform: `translate(${x + w - 40 + k * 22} ${y - 24})` }, graphMetersLayer);
    el("title", {}, button).textContent = label;
    el("rect", { width: 18, height: 18, rx: 5 }, button);
    text(sign, { x: 9, y: 9.5, style: "font-size: 13px" }, button);
    button.addEventListener("click", e => { e.stopPropagation(); desEngine.changeCapacity(id, by); });
    buttons.push({ g: button, x: x + w - 40 + k * 22, y: y - 24 });
  });
  return { ...graphResourceBox(graphMetersLayer, id, x, y, false, w), buttons };
});
// The mark of what is pinned: a small grey badge with a pin on it, on the bottom right corner of the box.
// It sits on the corner itself, half outside, so it covers nothing inside the box. Being pinned is not
// being selected: the selection outline may be on something else.
function graphPinBadge(x, y) {
  const g = el("g", { transform: `translate(${x} ${y})`, style: "pointer-events: none" }, graphPinLayer);
  el("title", {}, g).textContent = "Pinned";
  el("circle", { r: 9, fill: "#6a737b", stroke: "#0d0d0d", "stroke-width": 1.5 }, g);   // grey: it states a fact, it is not a button
  el("path", { d: "M-2.500 -5h5l-1 3.500l2.500 2.500h-8l2.500 -2.500zM0 1v4.500", fill: "#fff", stroke: "#fff", "stroke-width": 1.2, "stroke-linejoin": "round", "stroke-linecap": "round" }, g);
}
// What can be pinned besides a box of the map: a resource ("res:cooks") or one unit of it ("unit:cooks:0").
const graphPinnedUnit = key => typeof key === "string" && key.startsWith("unit:") ? { pool: key.split(":")[1], index: Number(key.split(":")[2]) } : null;
const graphPinnedParty = key => typeof key === "string" && key.startsWith("party:") ? key.slice(6) : null;
// What a party sees of its own visit: the five steps it takes part in or waits for in person. The kitchen
// is out of its sight, so from placing its order until a waiter picks the food up it is waiting for "Food to table".
const GRAPH_PARTY_STEPS = ["seating", "browsing", "ordering", "running", "dining"];
function graphPartyPlace(party) {   // the step the party is at, and whether it is waiting there or being served
  const [key, area] = GRAPH_PLACE[party.state] || [];
  return GRAPH_PARTY_STEPS.includes(key) ? [key, area] : ["running", "wait"];
}
// A pinned party stands in the middle as a box of its own, with the steps it takes part in over the top and
// the outcomes its visit can end in along the bottom. Nothing
// moves as the party goes on: an arrow points from the party to the step it is at right now, dashed while it
// waits there and solid while it is served. When the party leaves it stays pinned, until it is unpinned by hand.
function graphPartyOverSteps(id) {
  const { w, h } = GRAPH_RESOURCE, x = GRAPH_RING.x - w / 2, y = GRAPH_RING.y - h / 2, info = desPartyInfo(id), g = el("g", {}, graphPinLayer);
  el("rect", { class: "des-stage graph-node", x, y, width: w, height: h, rx: 6 }, g);
  el("rect", { x: x + 1.5, y: y + 6, width: 4, height: h - 12, rx: 2, fill: GRAPH_PARTY_COLOUR }, g);
  text(info.name, { class: "line-name task-name", x: x + w - 7, y: y + 16, style: "text-anchor: end" }, g);
  desAttach(g, info);
  g.toggleAttribute("data-selected", info === selected);
  el("rect", { class: "study-unit party", x: x + 14, y: y + 26, width: 18, height: 18, rx: 3 }, g);
  const pool = { id: "party", party: id, info, g, squares: [], links: {}, note: text("", { class: "task-avg", x: x + w - 7, y: y + h - 6 }, g) };
  graphPools.push(pool);
  graphPinBadge(x + w - 1, y + h - 1);
  for (const key of graphShown) {
    const at = graphCentre(key), a = graphEdgePoint(GRAPH_RING, at, w / 2, h / 2, 1), b = graphEdgePoint(at, GRAPH_RING, ...graphHalf(GRAPH[key]), 3);
    pool.links[key] = el("path", { class: "loop-arrow", "marker-end": "url(#graph-arrow)", style: "stroke-width: 1.5; stroke-dasharray: 4 3; display: none", d: `M${a.x} ${a.y}L${b.x} ${b.y}` }, graphPinLayer);
  }
}
const graphPinnedResource = key => typeof key === "string" && key.startsWith("res:") ? key.slice(4) : graphPinnedUnit(key)?.pool ?? null;
const GRAPH_TASK_STEP = { table: "seating", order: "ordering", deliver: "running", plan: "planning", plate: "plating" };   // the step a unit is at, from the job it holds (a kitchen part is named after its step)
const GRAPH_TASK_WORDS = { table: "Taken by", order: "Taking the order of", deliver: "Running food to", plan: "Planning the order of", plate: "Plating for", stoves: "Cooking for", oven: "Baking for", coffee: "Making coffee for" };
// One unit by itself, as a box: lit while it is allocated, with what it is doing underneath.
function graphUnitBox(parent, id, index, x, y) {
  const unit = DES_RES[id].units[index], { w, h } = GRAPH_RESOURCE, g = el("g", {}, parent);
  el("rect", { class: "des-stage graph-node", x, y, width: w, height: h, rx: 6 }, g);
  el("rect", { x: x + 1.5, y: y + 6, width: 4, height: h - 12, rx: 2, fill: graphEdgeColour(id) }, g);
  text(unit.name, { class: "line-name task-name", x: x + w - 7, y: y + 16, style: "text-anchor: end" }, g);
  desAttach(g, unit.info);
  g.toggleAttribute("data-selected", unit.info === selected);
  const square = el("rect", { class: "study-unit", x: x + 14, y: y + 26, width: 18, height: 18, rx: 3 }, g);
  return { id, unit: index, info: unit.info, g, squares: [square], links: {}, note: text("", { class: "task-avg", x: x + w - 7, y: y + h - 6 }, g) };
}
// A pinned resource stands in the middle, with the steps that need it all around it: in the order of the
// process, clockwise from its left. An arrow runs from it into each step. Nothing else is drawn: whatever
// is pinned, the only lines are the ones to it and from it.
const GRAPH_RING = { x: 600, y: 380, rx: 270, ry: 195 };
const graphRingAt = angle => ({ x: GRAPH_RING.x + GRAPH_RING.rx * Math.cos(angle), y: GRAPH_RING.y - GRAPH_RING.ry * Math.sin(angle) });
function graphRingPlace(i, n) {
  return graphRingAt(n === 1 ? 0 : Math.PI * (1 - 2 * i / n));   // one step alone stands to the right
}
// where the straight line from the middle of one box to the middle of another leaves the first box
function graphEdgePoint(from, to, halfW, halfH, clear) {
  const dx = to.x - from.x, dy = to.y - from.y, t = Math.min(dx ? (halfW + clear) / Math.abs(dx) : Infinity, dy ? (halfH + clear) / Math.abs(dy) : Infinity);
  return { x: from.x + dx * t, y: from.y + dy * t };
}
const graphHalf = box => [(box.right - box.x) / 2, (box.bottom - box.y) / 2];
function graphResourceOverSteps(id) {
  const { w, h } = GRAPH_RESOURCE, x = GRAPH_RING.x - w / 2, y = GRAPH_RING.y - h / 2, one = graphPinnedUnit(graphPinned);
  const pool = one ? graphUnitBox(graphPinLayer, id, one.index, x, y) : graphResourceBox(graphPinLayer, id, x, y, true);
  graphPools.push(pool);
  graphPinBadge(x + w - 1, y + h - 1);
  for (const key of graphShown) {
    const box = GRAPH[key], at = graphCentre(key);
    const a = graphEdgePoint(GRAPH_RING, at, w / 2, h / 2, 1), b = graphEdgePoint(at, GRAPH_RING, ...graphHalf(box), 3);
    const link = el("path", { class: "loop-arrow", "marker-end": graphArrowHead(id), style: `stroke-width: 1.5; stroke: ${graphEdgeColour(id)}; stroke-dasharray: 4 3`, d: `M${a.x} ${a.y}L${b.x} ${b.y}` }, graphPinLayer);
    if (pool.links) pool.links[key] = link;   // one unit: the arrow to the step it is at right now is drawn solid
  }
}
// Where everything stands around a pinned step: the step in the middle, what leads into it in a column
// on its left, the steps it leads to in a column on its right, so that the work reads from left to right
// along one line, and the outcomes it can end in in a row underneath. A pinned outcome is at the bottom,
// with the steps that lead to it in a row above it. (Its resources go on top: see graphResourceBoxes.)
function graphStepPlaces(key) {
  const size = k => ({ w: GRAPH[k].right - GRAPH[k].x, h: GRAPH[k].bottom - GRAPH[k].y }), pinned = size(key), places = {};
  const from = graphEdges.filter(edge => edge.to === key).map(edge => edge.from), to = graphEdges.filter(edge => edge.from === key).map(edge => edge.to);
  const column = (keys, x, alignRight) => {   // one under another, around the middle line
    let y = GRAPH_RING.y - (keys.reduce((sum, k) => sum + size(k).h, 0) + (keys.length - 1) * GB.gap) / 2;
    for (const k of keys) { places[k] = { x: alignRight ? x - size(k).w : x, y }; y += size(k).h + GB.gap; }
  };
  const row = (keys, y) => {   // side by side, around the middle
    let x = GRAPH_RING.x - (keys.reduce((sum, k) => sum + size(k).w, 0) + (keys.length - 1) * GB.gap) / 2;
    for (const k of keys) { places[k] = { x, y }; x += size(k).w + GB.gap; }
  };
  if (GRAPH_EXITS.includes(key)) {
    row(from, GRAPH_RING.y - GB.h / 2);
    places[key] = { x: GRAPH_RING.x - pinned.w / 2, y: GRAPH_RING.y + GB.h / 2 + GRAPH_APART };
    return places;
  }
  places[key] = { x: GRAPH_RING.x - pinned.w / 2, y: GRAPH_RING.y - pinned.h / 2 };
  column(from, places[key].x - GRAPH_APART, true);
  column(to.filter(k => !GRAPH_EXITS.includes(k)), places[key].x + pinned.w + GRAPH_APART, false);
  const lowest = Math.max(...Object.entries(places).map(([k, place]) => place.y + size(k).h));
  row(to.filter(k => GRAPH_EXITS.includes(k)), lowest + GRAPH_APART);
  return places;
}
// An arrow between two boxes where they stand now: down into an outcome, sideways otherwise, with one turn in the middle if they are not in line.
function graphLink(from, to) {
  const rect = k => ({ x: GRAPH[k].x + GRAPH[k].dx, right: GRAPH[k].right + GRAPH[k].dx, y: GRAPH[k].y + GRAPH[k].dy, bottom: GRAPH[k].bottom + GRAPH[k].dy,
                       cx: GRAPH[k].cx + GRAPH[k].dx, cy: (GRAPH[k].y + GRAPH[k].bottom) / 2 + GRAPH[k].dy }), a = rect(from), b = rect(to);
  if (GRAPH_EXITS.includes(to)) {
    const turn = (a.bottom + b.y) / 2;
    return a.cx === b.cx ? [{ x: a.cx, y: a.bottom + 1 }, { x: b.cx, y: b.y - 3 }] : [{ x: a.cx, y: a.bottom + 1 }, { x: a.cx, y: turn }, { x: b.cx, y: turn }, { x: b.cx, y: b.y - 3 }];
  }
  const turn = (a.right + b.x) / 2;
  return a.cy === b.cy ? [{ x: a.right + 1, y: a.cy }, { x: b.x - 3, y: b.cy }] : [{ x: a.right + 1, y: a.cy }, { x: turn, y: a.cy }, { x: turn, y: b.cy }, { x: b.x - 3, y: b.cy }];
}
function graphResourceBoxes(box) {
  // what the step waits for: its resources (violet edge) and, for the step where an order's parts come
  // back together, the other parts of the order (grey edge: a precondition of another kind). They stand
  // in a row on top, above everything that is shown, each with an arrow down into the step.
  const needs = [...(box.task.queue ? DES_QUEUE_NEEDS[box.task.queue] : []), ...(box.task.join ? ["parts"] : [])];
  const { w, h } = GRAPH_RESOURCE, total = needs.length * w + (needs.length - 1) * 16, cx = box.cx + box.dx, top = box.y + box.dy;
  const y = Math.min(...Object.values(GRAPH).filter(one => graphShown.has(one.key)).map(one => one.y + one.dy)) - h - GRAPH_APART;
  needs.forEach((id, i) => {
    const parts = id === "parts", stripe = parts ? "#898781" : graphEdgeColour(id), x = cx - total / 2 + i * (w + 16);
    graphPools.push(graphResourceBox(graphPinLayer, id, x, y, true));
    const door = cx + (i - (needs.length - 1) / 2) * 30, bend = top - 22;
    const link = [[x + w / 2, y + h + 1], [x + w / 2, bend], [door, bend], [door, top - 3]];
    el("path", { class: "loop-arrow", "marker-end": parts ? "url(#graph-arrow)" : graphArrowHead(id), style: `stroke-width: 1.5; stroke: ${stripe}; stroke-dasharray: 4 3`,
                 d: link.map(([px, py], k) => `${k ? "L" : "M"}${px} ${py}`).join("") }, graphPinLayer);
  });
}
// the preconditions of a pinned step, as they stand right now
function graphDrawPools(s, pools = graphPools) {
  for (const pool of pools) {
    if (pool.parts) {   // the orders waiting at the step: first the ones still short of a part, then the complete ones
      const parties = [...s.parties.values()], short = parties.filter(party => party.state === "COOKING" && Object.values(party.parts).includes("done")).length;
      const complete = parties.filter(party => party.state === "WAITING_FOR_PLATING").length;
      setText(pool.note, `${short} of ${short + complete} short of a part`);
      pool.squares.forEach((square, k) => {
        square.style.display = k < short + complete ? "" : "none";
        square.classList.toggle("used", k < short);
      });
      continue;
    }
    if (pool.everyone) {   // one square per party in the building, in the order they came in
      const ids = [...s.parties.keys()];
      if (pool.note) setText(pool.note, `${ids.length} in the building`);
      pool.squares.forEach((square, k) => {
        const id = ids[k];
        square.style.display = id ? "" : "none";
        if (!id) return;
        if (square.dataset.party !== id) { square.dataset.party = id; square.firstChild.textContent = desPartyInfo(id).name; }
        square.toggleAttribute("data-selected", selected !== null && desPartyInfos.get(id) === selected);
      });
      continue;
    }
    if (pool.party) {   // one party by itself: what it is doing or waiting for, and at which steps
      const party = s.parties.get(pool.party);
      if (!party) {   // it has left: it stays pinned until it is unpinned, with its arrow on how the visit ended
        const gone = pool.info.party, end = gone.gaveUp === "order" ? "noorder" : gone.gaveUp === "food" ? "hungry" : "out";
        setText(pool.note, "Visit over");
        for (const [key, link] of Object.entries(pool.links)) { link.style.display = key === end ? "" : "none"; link.style.strokeDasharray = "none"; }
        continue;
      }
      const stage = DES_STAGE[party.state], [at, area] = graphPartyPlace(party);
      // whatever the kitchen is doing, "waiting for the food" is all the party knows
      setText(pool.note, at === "running" && area === "wait" ? "Waiting for the food" : stage.queue ? "Waiting for " + desEngine.missing(stage.queue).map(need => DES_MISSING[need][1]).join(" + ") : stage.name);
      for (const [key, link] of Object.entries(pool.links)) {   // an arrow only to where the party is now: solid while it is served there, dashed while it waits
        link.style.display = key === at ? "" : "none";
        link.style.strokeDasharray = area === "active" ? "none" : "4 3";
      }
      continue;
    }
    const r = s.resources[pool.id];
    if (pool.unit !== undefined) {   // one unit by itself: what it is doing, and at which step
      const held = r.units[pool.unit], at = held ? GRAPH_TASK_STEP[held.task] || held.task : null;
      pool.squares[0].classList.toggle("used", Boolean(held));
      pool.squares[0].classList.toggle("out", held === DES_OUT);
      setText(pool.note, held === false ? "Not on shift" : held === DES_OUT ? desOutWords(pool.id).state : held ? `${GRAPH_TASK_WORDS[held.task]} party ${s.parties.get(held.party)?.number ?? "that left"}` : "Free");
      for (const [key, link] of Object.entries(pool.links)) { link.style.strokeDasharray = key === at ? "none" : "4 3"; link.style.opacity = key === at ? 1 : 0.45; }
      continue;
    }
    if (pool.note) setText(pool.note, `${r.capacity - r.allocated} of ${r.capacity} free`);
    pool.squares.forEach((square, k) => {
      square.style.display = r.units[k] === false ? "none" : "";   // not on shift
      square.classList.toggle("used", Boolean(r.units[k]));
      square.classList.toggle("out", r.units[k] === DES_OUT);   // off sick, broken down or out of use: one red line through it
    });
  }
}
// which box of the pipeline a selected object can be pinned as: a step by its card, the door or an exit by the box that was clicked
// All the parties pinned: the Parties box in the middle, the steps a party takes part in around it, a line to each.
function graphPartiesOverSteps() {
  const { w, h } = GRAPH_RESOURCE, x = GRAPH_RING.x - w / 2, y = GRAPH_RING.y - h / 2;
  graphPools.push(graphResourceBox(graphPinLayer, "parties", x, y, true));
  graphPinBadge(x + w - 1, y + h - 1);
  for (const key of graphShown) {
    const at = graphCentre(key), a = graphEdgePoint(GRAPH_RING, at, w / 2, h / 2, 1), b = graphEdgePoint(at, GRAPH_RING, ...graphHalf(GRAPH[key]), 3);
    el("path", { class: "loop-arrow", "marker-end": "url(#graph-arrow)", style: "stroke-width: 1.5; stroke-dasharray: 4 3", d: `M${a.x} ${a.y}L${b.x} ${b.y}` }, graphPinLayer);
  }
}
let graphClicked = null;
for (const box of Object.values(GRAPH)) box.g.addEventListener("click", () => { graphClicked = box.key; }, true);
function graphPinTarget(info) {
  const step = Object.keys(DES_TASKS).find(key => DES_TASKS[key].info === info);
  // a resource is pinned as itself, and so is one of its units (table 7, a cook)
  if (info === desPartiesInfo) return "parties";
  for (const [id, one] of desPartyInfos) if (one === info) return "party:" + id;   // also one that has left: its visit can still be looked at
  for (const id in DES_RES) {
    if (DES_RES[id].info === info) return "res:" + id;
    const index = DES_RES[id].units.findIndex(unit => unit.info === info);
    if (index >= 0) return `unit:${id}:${index}`;
  }
  return step || (graphClicked && GRAPH[graphClicked].g.isConnected && info.nodes.includes(GRAPH[graphClicked].g) ? graphClicked : null);
}
// (The right-click menu is with the other actions, in actions.js: it offers whatever the Actions tab does.)
const graphPartyToken = party => g => {
  el("circle", { r: 13, fill: "transparent" }, g);   // a bigger target: tokens are small and they move
  el("rect", { class: "token-box", x: -8.5, y: -7, width: 17, height: 14, rx: 3 }, g);   // plain grey: colour means a table's state elsewhere
  text(party.number, { class: "token-text", style: "fill: #111; font-size: 8px" }, g);
};
// which box and which of its areas a party is in, from its state
const GRAPH_PLACE = {
  WAITING_FOR_TABLE: ["seating", "wait"], READING_MENU: ["browsing", "active"], WAITING_FOR_WAITER_ORDER: ["ordering", "wait"], ORDERING: ["ordering", "active"],
  WAITING_FOR_COOK: ["planning", "wait"], PLANNING: ["planning", "active"], WAITING_FOR_PLATING: ["plating", "wait"], PLATING: ["plating", "active"],
  WAITING_FOR_WAITER_DELIVER: ["running", "wait"], FOOD_RUNNING: ["running", "active"], EATING_AND_BILLING: ["dining", "active"],
};

function drawGraph() {
  if (graphStale) { graphMeasure(); graphStale = false; graphPin(graphPinned); }   // the card changed size: lay the map out for it
  const follow = graphPinnedParty(graphPinned);   // a pinned party: only its own tokens are shown
  const frame = performance.now(), seconds = Math.min(Math.max(frame - graphLast, 0), 100) / 1000, ease = 1 - Math.exp(-seconds / 0.16);
  graphLast = frame;
  const s = desEngine.snapshot(), here = {};
  const seenBefore = new Map(graphSeen);   // where each party was at the last frame, whatever this frame does with its parts
  for (const token of graphTokens.values()) token.live = false;
  const one = graphPinnedUnit(graphPinned), mine = one && s.resources[one.pool].units[one.index];   // with one unit pinned: only the party it works for, at the step it is at
  const stand = (key, area, party, since, tokenKey, held) => {
    if (one && !(mine && mine.party === party.id && area === "active" && key === (GRAPH_TASK_STEP[mine.task] || mine.task))) return;
    if (!graphShown || graphShown.has(key)) ((here[key] ||= { wait: [], active: [] })[area]).push({ party, since, tokenKey, held }); };
  // a party turned away goes from the door to its way out
  for (const id of graphBalks.splice(0)) {
    if (!graphFresh && (!graphShown || graphShown.has("away"))) graphPasser(id + "/away", !graphShown || graphShown.has("source") ? "source" : "seating", "away", DES_OUTCOME.away.info, graphPartyToken({ number: Number(id.slice(1)) }));
  }
  // with the door pinned, a party that is seated at once is already past the boxes that are shown: let it be seen going in
  if (graphPinned === "source" && !graphFresh) {
    for (const party of s.parties.values()) {
      if (!graphKnown.has(party.id) && party.state !== "WAITING_FOR_TABLE") graphPasser(party.id + "/in", "source", "seating", desPartyInfo(party.id), graphPartyToken(party));
    }
  }
  graphKnown.clear();
  for (const id of s.parties.keys()) graphKnown.add(id);
  for (const party of s.parties.values()) {
    if (follow || graphPinned === "parties") {   // a pinned party, or all of them: one token each, at the step the party sees itself at
      if (!follow || party.id === follow) stand(...graphPartyPlace(party), party, party.since, party.id);
      continue;
    }
    if (party.state !== "COOKING") { stand(...GRAPH_PLACE[party.state], party, party.since, party.id); continue; }
    let done = 0;
    for (const [kind, state] of Object.entries(party.parts)) {
      if (state === "queued") stand(kind, "wait", party, party.queued[kind].since, `${party.id}/${kind}`);
      if (state === "cooking") stand(kind, "active", party, s.resources[kind].units[party.held[kind + ":" + kind]].since, `${party.id}/${kind}`);
      if (state === "done") done++;
    }
    // some parts are done and others are not: the order waits at plating for the rest
    if (done) stand("plating", "wait", party, party.since, `${party.id}/held`, true);
  }
  for (const box of Object.values(GRAPH)) {
    if (!box.active) continue;
    for (const part of ["wait", "active"]) {
      const area = box[part];
      if (!area) continue;
      const list = (here[box.key]?.[part] || []).sort((a, b) => Boolean(a.held) - Boolean(b.held) || a.since - b.since);   // orders ready to plate first, then the ones still short of parts
      list.forEach(({ party, tokenKey, held }, n) => {
        const spot = graphSpot(area, n);
        spot.x += box.dx || 0; spot.y += box.dy || 0;   // the box may stand aside while a step is pinned, or lower on a tall card
        const token = viewToken(graphTokens, "graph-parties", tokenKey, desPartyInfo(party.id), graphPartyToken(party));   // an order still short of a part looks like any other waiting token
        if (token.x === null) {   // a new token appears where its party was last seen, or at the door
          const seen = seenBefore.get(party.id) || { x: GRAPH.source.cx + (GRAPH.source.dx || 0), y: GRAPH.source.cy + (GRAPH.source.dy || 0), key: "source" };
          // a held order simply shows up in the waiting area (its done parts fly in to it); so does a token that comes from a box that is not shown
          const inPlace = graphFresh || held || Boolean(graphShown && !graphShown.has(seen.key));
          token.x = inPlace ? spot.x : seen.x; token.y = inPlace ? spot.y : seen.y; token.at = inPlace ? box.key : seen.key;
        }
        token.tx = spot.x; token.ty = spot.y;
        headFor(token, box.key, graphRoute);   // go there along the arrows
        if (!held) graphSeen.set(party.id, { x: spot.x, y: spot.y, key: box.key });
      });
      setText(area.more, list.length > area.per * area.rows ? `+${list.length - area.per * area.rows}` : "");
    }
  }
  for (const id of [...graphSeen.keys()]) if (!s.parties.has(id)) graphSeen.delete(id);
  if (graphPinned) graphDrawPools(s);
  for (const [key, token] of graphTokens) {
    if (!token.live) {
      // leaving the picture is also done along the arrows: a party that has dined goes out of the door,
      // and a part that is done goes to plating, where its order is waiting
      const gaveUp = desGaveUp.has(key.split("/")[0]);   // its party walked out: leave by that exit if an arrow leads there, else just go
      let exit = gaveUp ? (token.at === "ordering" ? "noorder" : ["planning", "plating", "running"].includes(token.at) ? "hungry" : null)
        : token.at === "dining" ? "out" : GRAPH_PARTS.includes(token.at) ? "plating" : null;
      if (graphShown && !(graphShown.has(exit) && (token.at === graphPinned || exit === graphPinned))) exit = null;   // while a step is pinned, only its own arrows are there to follow
      if (exit) { headFor(token, exit, graphRoute); token.tx = token.route.at(-1)?.x ?? token.x; token.ty = token.route.at(-1)?.y ?? token.y; token.going = true; }
      if (!token.going || !token.route.length) { token.g.remove(); graphTokens.delete(key); continue; }
    }
    moveToken(token, seconds, ease);
    token.g.setAttribute("transform", `translate(${token.x.toFixed(1)} ${token.y.toFixed(1)})`);
    token.g.toggleAttribute("data-selected", selected !== null && token.info === selected);
  }
  graphDrawPools(s, GRAPH_TOP);
  setText(GRAPH.out.count, s.departed);
  setText(GRAPH.noorder.count, s.abandonedFor.order);
  setText(GRAPH.hungry.count, s.abandonedFor.food);
  setText(GRAPH.away.count, s.balked);
  graphFresh = false;
}
