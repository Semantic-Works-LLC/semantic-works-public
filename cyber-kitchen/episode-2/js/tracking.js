// A stay is one visit to a step, from start to end on the simulation clock; end is null while it lasts.
const WINDOW = 180;   // seconds of the past that the charts on real time show
function stay(list) {
  while (list.length && list[0].end !== null && list[0].end < clock - WINDOW) list.shift();
  const one = { start: clock, end: null };
  list.push(one);
  return one;
}
const orderStays = [];   // one stay per order, from order taken to food served
function leaveStep(party) {
  if (!party.step) return;
  const step = FLOW[party.step];
  const spent = clock - party.stepSince;
  party.stay.end = clock;
  step.done++; step.total += spent;
  step.history.push(spent);
  if (step.history.length > KEEP) step.history.shift();
  party.spent[party.step] = spent;
}
// A gauge watches one yes/no or how-many reading of the simulation (is this stove in use? how long is
// this queue?) and keeps its average over the whole service and over each 15-second slice of it.
const BUCKET = 15, KEEP = 40;
const gauges = [];
let bucketTime = 0;
function gauge(read) {
  const g = { read, sum: 0, acc: 0, history: [], changes: [] };
  gauges.push(g);
  return g;
}
tables.forEach(t => { t.gauge = gauge(() => t.status !== "free"); t.seated = 0; t.guests = 0; t.was = "free"; t.info.subject = t; });
function enrol(s) { s.gauge = gauge(() => s.state !== "idle"); s.counts = {}; s.was = "idle"; s.info.subject = s; }
[...waiters, ...cooks].forEach(enrol);
stations.forEach(station => { station.gauge = gauge(() => station.busy); station.info.subject = station; });
STEPS.forEach(step => { step.info.subject = step; });
const QUEUE_LENGTH = {
  door: gauge(() => parties.filter(p => p.state === "queue").length),
  rail: gauge(() => rail.length),
  pass: gauge(() => pass.length),
};
// Runs every tick, whichever view is showing: all the measuring that the metrics are built from.
function trackFlow(dt) {
  for (const party of parties) {
    const key = stepOf(party);
    if (party.step === key) continue;
    leaveStep(party);
    party.step = key; party.stepSince = clock;
    party.start ??= clock;
    party.stay = stay(FLOW[key].stays);
  }
  for (const s of [...waiters, ...cooks]) {
    if (s.state === s.was) continue;
    s.counts[s.was] = (s.counts[s.was] || 0) + 1;   // how many times each activity was completed
    s.was = s.state;
  }
  for (const t of tables) {
    if (t.status === t.was) continue;
    if (t.status === "reading") { t.seated++; t.guests += t.party.size; }
    t.was = t.status;
  }
  for (const g of gauges) {
    const reading = Number(g.read());
    g.sum += reading * dt; g.acc += reading * dt;
    if (reading === g.last) continue;
    g.changes.push([clock, g.last = reading]);   // when the reading changed, for the charts on real time
    while (g.changes.length > 2 && g.changes[1][0] < clock - WINDOW) g.changes.shift();
  }
  bucketTime += dt;
  if (bucketTime < BUCKET) return;
  for (const g of gauges) {
    g.history.push(g.acc / bucketTime);
    if (g.history.length > KEEP) g.history.shift();
    g.acc = 0;
  }
  bucketTime = 0;
}
// the cook has finished and is walking the food to the pass
const onItsWayToPass = ticket => ticket.stage === "cooking" && (ticket.cook.state === "toPass" || ticket.cook.state === "plating");
