// ---------- guests ----------
const GUEST_SPEED = 85, FOLLOW_GAP = 17, MAX_QUEUE = 3;
const SIZE_WEIGHTS = [[1, 1], [2, 4], [3, 2], [4, 4], [5, 1.5], [6, 2]];
const parties = [];
let partyCount = 0, nextArrival = 0.5, served = 0, turnedAway = 0, clock = 0;

function pickSize() {
  let r = Math.random() * SIZE_WEIGHTS.reduce((sum, w) => sum + w[1], 0);
  for (const [size, weight] of SIZE_WEIGHTS) { if ((r -= weight) <= 0) return size; }
  return 2;
}
function findTable(size) {
  const fits = tables.filter(t => t.status === "free" && t.capacity >= size);
  if (!fits.length) return null;
  const smallest = Math.min(...fits.map(t => t.capacity));
  const best = fits.filter(t => t.capacity === smallest);
  return best[Math.floor(Math.random() * best.length)];
}
function seatParty(party, table) {
  party.table = table; table.party = party;
  setStatus(table, "reserved");
  const lead = party.members[0];
  party.path = [{ x: lead.x, y: lead.y }, DOOR, ...route(DOOR, table.sp)];
  party.length = pathLength(party.path);
  party.d = 0; party.state = "arriving";
}
function spawnParty() {
  const size = pickSize(), table = findTable(size);
  const queued = parties.filter(p => p.state === "queue").length;
  if (!table && queued >= MAX_QUEUE) { turnedAway++; return; }
  const color = PARTY_COLORS[partyCount++ % PARTY_COLORS.length];
  const party = { id: partyCount, size, color, spent: {}, state: "queue", members: [] };
  for (let i = 0; i < size; i++) {
    const m = { x: OUTSIDE.x - i * 6, y: OUTSIDE.y };
    m.el = el("circle", { class: "guest", r: 8, fill: color }, $("guests"));
    party.members.push(m);
  }
  party.info = selectable(party.members.map(m => m.el), {
    kind: "Guests", name: `Party ${partyCount}: ${size === 1 ? "1 guest" : size + " guests"}`, listName: `Party ${partyCount}`,
    what: size === 1 ? "One customer." : `${size} customers who came together and share a table.`,
    purpose: "They come to eat: sit down, read the menu, order, wait, eat and leave.",
    why: "Guests are the reason the restaurant exists. Everything else here is about serving them well and quickly enough that they come back.",
    extra: [["What they ordered", () => party.ticket ? party.ticket.lines : "Nothing yet."]],
  });
  parties.push(party);
  party.info.subject = party;
  if (table) seatParty(party, table);
}

function updateParty(party, dt) {
  const walk = GUEST_SPEED * dt;
  if (party.state === "queue") {
    const slot = parties.filter(p => p.state === "queue").indexOf(party);
    const table = findTable(party.size);
    if (table) return seatParty(party, table);
    party.members.forEach((m, i) => moveToward(m, 18 + (i % 2) * 20, 330 + slot * 80 + Math.floor(i / 2) * 19, walk * 1.5));
  } else if (party.state === "arriving" || party.state === "leaving") {
    party.d += walk;
    party.members.forEach((m, i) => {
      const p = pointAt(party.path, Math.max(0, party.d - i * FOLLOW_GAP));
      moveToward(m, p.x, p.y, walk * 1.6);
    });
    if (party.d < party.length + (party.size - 1) * FOLLOW_GAP + 10) return;
    if (party.state === "arriving") {
      party.state = "seated";
      setStatus(party.table, "reading");
      party.table.timer = rand(5, 9);
    } else {
      if (selected === party.info) select(null);
      leaveStep(party);
      party.members.forEach(m => m.el.remove());
      parties.splice(parties.indexOf(party), 1);
    }
  } else if (party.state === "seated") {
    party.members.forEach((m, i) => moveToward(m, party.table.seats[i].x, party.table.seats[i].y, walk * 1.5));
  }
}

function updateTable(table, dt) {
  if (table.status !== "reading" && table.status !== "eating") return;
  table.timer -= dt;
  if (table.timer > 0) return;
  if (table.status === "reading") return setStatus(table, "ready");
  // finished eating: the party walks out and the table is free again
  const party = table.party;
  party.path = [table.sp, ...route(table.sp, DOOR), OUTSIDE];
  party.length = pathLength(party.path);
  party.d = 0; party.state = "leaving";
  table.party = null;
  setStatus(table, "free");
  served++;
}
