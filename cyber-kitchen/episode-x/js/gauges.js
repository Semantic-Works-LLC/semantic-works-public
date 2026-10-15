// ---------- gauges ----------
// A gauge watches one yes/no or how-many reading of the engine (is this stove in use? how full is this
// pool?) and keeps its average over the whole run and over each 15-second slice of it.
let clock = 0;        // simulated seconds; the one clock of the page, which the engine is run up to
const WINDOW = 180;   // seconds of the past that the charts on real time show
const BUCKET = 15, KEEP = 40;
const gauges = [];
let bucketTime = 0;
function gauge(read) {
  const g = { read, sum: 0, acc: 0, history: [], changes: [] };
  gauges.push(g);
  return g;
}
// Runs every tick, whichever view is showing.
function sampleGauges(dt) {
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
