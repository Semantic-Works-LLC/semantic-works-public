// where a waiter or cook stands for each thing they do (the second number shifts a second person aside)
const dockUnder = box => ({ x: box.x + 82, y: LOOP.dock });
const WAITER_SPOT = {
  toTable: dockUnder(PARTY_BOXES[3]), taking: dockUnder(PARTY_BOXES[4]),
  toRail: { x: 600, y: 330 }, hanging: { x: 600, y: 356 },
  toPass: { x: 892, y: 330 }, picking: { x: 892, y: 356 },
  toServe: { x: 892, y: LOOP.dock }, serving: { x: PARTY_BOXES[5].x + 40, y: LOOP.dock },
};
const COOK_SPOT = {
  toRail: { x: 688, y: 442 }, grabbing: { x: 688, y: 442 },
  waitStation: { x: KITCHEN.x + 150, y: KITCHEN.y + 28 },
  toPass: { x: 808, y: 442 }, plating: { x: 808, y: 442 },
};
const loopTokens = new Map();
let loopSlots = {}, loopFresh = true, loopLast = 0;
const loopToken = (key, info, build) => viewToken(loopTokens, "loop-tokens", key, info, build);
function put(token, x, y, from) {
  token.tx = x; token.ty = y;
  if (token.x !== null) return;
  const start = loopFresh ? null : from;
  token.x = start ? start.x : x;
  token.y = start && start.y != null ? start.y : y;
}
// the next free spot in a grid of spots that starts at (x, y)
function gridSpot(key, x, y, perRow) {
  const i = loopSlots[key] = (loopSlots[key] || 0) + 1;
  return [x + ((i - 1) % perRow) * 24, y + Math.floor((i - 1) / perRow) * 25];
}
const boxAverage = box => box.steps.reduce((sum, key) => sum + (FLOW[key].done ? FLOW[key].total / FLOW[key].done : 0), 0);

function drawLoop() {
  trackFlow(0);
  const now = performance.now(), ease = 1 - Math.exp(-Math.min(now - loopLast, 100) / 160);
  loopLast = now;
  loopSlots = {};
  for (const token of loopTokens.values()) token.live = false;
  for (const party of [...parties].sort((a, b) => a.stepSince - b.stepSince)) {
    const box = BOX_OF[party.step], token = loopToken("p" + party.id, party.info, g => partyToken(g, party));
    put(token, ...gridSpot(box.key, box.x + 17, LOOP.y + 58, 5), { x: -20 });
    token.also = [party.ticket?.info, party.table?.info];
  }
  // staff first, because an order that is being carried or cooked travels with its waiter or cook
  for (const w of waiters) {
    const spot = WAITER_SPOT[w.state], token = loopToken(w.name, w.info, staffToken("W" + w.number, true));
    if (spot) put(token, spot.x + (loopSlots["w" + w.state] = (loopSlots["w" + w.state] || 0) + 1) * 24 - 24, spot.y);
    else put(token, ...gridSpot("freeWaiters", FREE_AREAS.waiter.x + 28, FREE_AREAS.waiter.y + 31, 6));
  }
  for (const c of cooks) {
    const atStation = c.state === "toStation" || c.state === "working";
    const spot = atStation ? c.station.spot : COOK_SPOT[c.state], token = loopToken(c.name, c.info, staffToken("C" + c.number, false));
    if (spot) put(token, spot.x + (atStation ? 0 : (loopSlots["c" + c.state] = (loopSlots["c" + c.state] || 0) + 1) * 24 - 24), spot.y);
    else put(token, ...gridSpot("freeCooks", FREE_AREAS.cook.x + 28, FREE_AREAS.cook.y + 31, 6));
  }
  const waiting = ticket => ticket.stage === "rail" || ticket.stage === "pass";
  for (const ticket of [...tickets].sort((a, b) => a.since - b.since)) {
    const token = loopToken("k" + ticket.id, ticket.info, (g, token) => orderToken(g, token, ticket));
    token.home = loopTokens.get("p" + ticket.table.party.id);
    if (waiting(ticket)) {
      const queue = LOOP_QUEUES[ticket.stage];
      put(token, ...gridSpot(queue.step, queue.x + 19, queue.y + 62, 4), token.home);
    } else {
      const carrier = loopTokens.get((ticket.stage === "cooking" ? ticket.cook : ticket.waiter).name);
      put(token, carrier.tx + 17, carrier.ty - 11, token.home);
    }
    showAsFood(token, ticket.stage === "pass" || ticket.stage === "delivering" || onItsWayToPass(ticket));
  }
  glideTokens(loopTokens, ease);
  for (const box of PARTY_BOXES) setText(box.avg, boxAverage(box) ? "avg " + clockText(boxAverage(box)) : "");
  for (const queue of Object.values(LOOP_QUEUES)) {
    const step = FLOW[queue.step];
    setText(queue.avg, step.done ? "avg " + clockText(step.total / step.done) : "");
  }
  setText(kitchenAvg, FLOW.cooking.done ? "avg " + clockText(FLOW.cooking.total / FLOW.cooking.done) : "");
  for (const station of stations) station.loopBar.setAttribute("width", 51 * station.progress);
  for (const [kind, area] of Object.entries(FREE_AREAS)) setText(area.total, `\u00b7 ${TEAM[kind].wanted} in total`);
  for (const table of tables) if (table.mini.getAttribute("class") !== "table " + table.status) table.mini.setAttribute("class", "table " + table.status);
  loopFresh = false;
}
