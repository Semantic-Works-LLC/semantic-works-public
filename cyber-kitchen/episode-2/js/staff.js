// ---------- staff ----------
function makeStaff(kind, label, number, home, speed) {
  const g = el("g", {}, $("staff"));
  const dark = kind === "waiter";
  if (!dark) el("rect", { x: -6, y: -17, width: 12, height: 9, rx: 3, fill: "#fff", stroke: "#0d0d0d", "stroke-width": 1 }, g);
  el("circle", { class: "person", r: 10, fill: dark ? "#0d0d0d" : "#fff", stroke: dark ? "#fff" : "#0d0d0d", "stroke-width": dark ? 2 : 1 }, g);
  text(label, { class: "staff-label", fill: dark ? "#fff" : "#0d0d0d" }, g);
  const ticket = el("g", { visibility: "hidden" }, g);
  el("rect", { class: "ticket", x: 8, y: -16, width: 12, height: 14, rx: 1.5 }, ticket);
  const tray = el("g", { visibility: "hidden" }, g);
  el("circle", { cx: 15, cy: -9, r: 9, fill: "#8d949b", stroke: "#0d0d0d", "stroke-width": 1 }, tray);
  el("circle", { cx: 12, cy: -10, r: 3.5, fill: "#f2f2f2" }, tray);
  el("circle", { cx: 18, cy: -8, r: 3.5, fill: "#f2f2f2" }, tray);
  el("circle", { r: 17, fill: "transparent" }, g);   // bigger click target for a moving person
  const s = { kind, number, g, ticket, tray, home, speed, x: home.x, y: home.y, at: home, path: [], state: "idle", timer: 0, job: null, carry: null };
  s.name = `${ABOUT_STAFF[kind].kind} ${number}`;
  s.info = selectable(g, { ...ABOUT_STAFF[kind], name: s.name });
  return s;
}
const ABOUT_STAFF = {
  waiter: {
    kind: "Waiter",
    what: "A member of the front-of-house staff.",
    purpose: "Takes orders at the tables, hangs the ticket on the order rail, then carries finished plates from the pass to the guests.",
    why: "The only link between guests and kitchen. Everything guests ask for and receive goes through a waiter, so too few waiters means orange and red tables.",
  },
  cook: {
    kind: "Cook",
    what: "A member of the kitchen staff.",
    purpose: "Takes a ticket from the rail, cooks the order at a stove or the pizza oven, makes coffee if the order has one, and puts the plates on the pass.",
    why: "Turns orders into food. How fast the cooks work sets how long guests wait for their meal.",
  },
};
function go(s, target) {
  s.path = s.kind === "cook" ? [target] : route(s.at, target);
  s.at = target;
}
function advance(s, dt) {
  let step = s.speed * dt;
  while (s.path.length && step > 0) {
    const p = s.path[0], dist = Math.hypot(p.x - s.x, p.y - s.y);
    if (moveToward(s, p.x, p.y, step)) s.path.shift();
    step -= dist;
  }
  return s.path.length === 0;
}

const waiters = [
  makeStaff("waiter", "W", 1, { x: 760, y: 350 }, 130),
  makeStaff("waiter", "W", 2, { x: 760, y: 392 }, 130),
];
const cooks = [
  makeStaff("cook", "C", 1, { x: 960, y: 300 }, 110),
  makeStaff("cook", "C", 2, { x: 960, y: 420 }, 110),
];
cooks.forEach((c, i) => c.stove = stoves[i]);

// The number of waiters and cooks can be changed while the simulation runs, from none to six of each.
const STAFF_MAX = 6;
const TEAM = {
  waiter: { members: waiters, wanted: 2, label: "W", speed: 130, home: i => ({ x: 760 - Math.floor(i / 2) * 32, y: 350 + (i % 2) * 42 }) },
  cook: { members: cooks, wanted: 2, label: "C", speed: 110, home: i => ({ x: 960 - Math.floor(i / 2) * 40, y: 300 + (i % 2) * 120 }) },
};
function changeStaff(kind, by) {
  const team = TEAM[kind], wanted = Math.min(STAFF_MAX, Math.max(0, team.wanted + by));
  if (wanted === team.wanted) return;
  team.wanted = wanted;
  const leaving = team.members.find(s => s.leaving);
  if (by > 0 && leaving) { leaving.leaving = false; return; }   // someone was on the way out: keep them
  if (by > 0) {
    let number = 1;
    while (team.members.some(s => s.number === number)) number++;
    const s = makeStaff(kind, team.label, number, team.home(number - 1), team.speed);
    if (kind === "cook") s.stove = stoves[(number - 1) % stoves.length];   // extra cooks share the two stoves
    enrol(s);
    team.members.push(s);
    return;
  }
  // one fewer: whoever is free goes at once, otherwise the last one goes after finishing the job in hand
  const staying = team.members.filter(s => !s.leaving);
  (staying.findLast(s => s.state === "idle") || staying.at(-1)).leaving = true;
}
function dismiss(s) {
  const members = TEAM[s.kind].members;
  members.splice(members.indexOf(s), 1);
  gauges.splice(gauges.indexOf(s.gauge), 1);
  s.g.remove();
  if (selected === s.info) select(null);
}
