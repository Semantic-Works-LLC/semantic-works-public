// ---------- Scorecard view ----------
// The owner's figures for the whole restaurant, read from the same engine as the other two views:
// nine boxes, three by three. Each box is its own selectable figure with its own card and charts, and
// is outlined by how it stands against its target: green on target, amber a little off, red off.
// Figures with no target are kept for the record and stay plain.
const scoreStatic = $("score-static"), SX = 16, SCORE_GAP_LIMIT = 2;
let scoreAt = -1, scoreNow = null;
const scoreT = () => scoreAt === clock ? scoreNow : (scoreAt = clock, scoreNow = desEngine.telemetry());   // once per tick, however many boxes ask
const scoreFinished = () => desEngine.departed + desEngine.abandoned;
const scoreHappy = () => scoreFinished() ? desEngine.happy / scoreFinished() : 0;
const scoreGap = () => { const t = scoreT(); return t.sample ? t.averageL - t.predictedL : 0; };
const one = value => value.toFixed(1), FOR_THE_RECORD = "No target: kept for the record.";
// a figure that is watched by a gauge: bars for each 15 seconds, then the same reading on the clock
function scoreSpec(g, { objective, measure, value, unit, verdict, target = 0, good, format = one, lead = FOR_THE_RECORD, numbers, what }) {
  return {
    objective, measure, value, unit, verdict, numbers,
    notes: [lead, trend(g.history.at(-1), clock ? g.sum / clock : 0, format)],
    chartTitle: `${what} every 15 seconds`, timelineTitle: `${what} on the clock`,
    chart: barChart(g.history, target, good, format),
    caption: `Each bar is 15 seconds of service, oldest on the left.${target ? " Dashed line: the target." : ""}`,
    timeline: readingTimeline(g),
    timelineCaption: "On the clock: the taller the strip, the higher the figure. " + NOW_NOTE,
  };
}
const NO_TARGET = ["No target", "none"];
// The wait for food as it is now, not over the whole run: the average over the parties served in the last
// three minutes. With no cook or no waiter on shift no food can be served at all, and with parties waiting
// for food and nothing served in those three minutes none is being served: the wait is Infinity. null: nothing to say yet.
const scoreFoodLog = [];
let scoreFoodSeen = { done: 0, total: 0 }, scoreFoodAt = -1, scoreFoodNow = null;
function scoreFoodWait() {
  if (scoreFoodAt === clock) return scoreFoodNow;   // once per tick
  const food = desEngine.waits.food;
  if (food.done > scoreFoodSeen.done) scoreFoodLog.push({ at: clock, served: food.done - scoreFoodSeen.done, waited: food.total - scoreFoodSeen.total });
  scoreFoodSeen = { done: food.done, total: food.total };
  while (scoreFoodLog.length && scoreFoodLog[0].at < clock - WINDOW) scoreFoodLog.shift();
  const served = scoreFoodLog.reduce((sum, one) => sum + one.served, 0), waited = scoreFoodLog.reduce((sum, one) => sum + one.waited, 0);
  const waiting = [...desEngine.parties.values()].some(party => party.timestamps.orderPlaced !== undefined && party.timestamps.foodServed === undefined);
  const staffed = desEngine.resources.cooks.capacity > 0 && desEngine.resources.waiters.capacity > 0;
  scoreFoodAt = clock;
  return scoreFoodNow = !staffed || (waiting && !served) ? Infinity : served ? waited / served : null;
}
const SCORE = [
  { label: "Events so far", name: "Events so far", purpose: "How many events the simulation has processed. Everything that happens in the restaurant is one: a party arriving, a cook starting a dish, food reaching a table.",
    read: () => desRecent.filter(event => event.timestamp > clock - 15).length, value: () => desEngine.eventsProcessed.toLocaleString("en-US"),
    spec: (g, me) => scoreSpec(g, { what: "Events", format: v => Math.round(v), objective: "Know how much is going on.", measure: "Count of events processed since the start. The charts show how many fell in the latest 15 seconds.",
                                    value: me.value(), unit: "events since the start", verdict: NO_TARGET }) },
  { label: "λ · arrivals per minute", name: "Arrivals per minute", purpose: "How fast parties come in. Parties turned away at the door are not counted.",
    read: () => Number(one(scoreT().lambda * 60)), value: () => one(scoreT().lambda * 60),
    spec: (g, me) => scoreSpec(g, { what: "Arrivals", objective: "Know how much business is coming through the door.", measure: "Parties that walked in during the last three minutes, per minute.",
                                    value: me.value(), unit: "parties per minute", verdict: NO_TARGET }) },
  { label: "L · in the building now", name: "Parties in the building now", purpose: "How many parties are inside at this moment, from the door to leaving.",
    read: () => desEngine.parties.size, value: () => desEngine.parties.size,
    spec: (g, me) => scoreSpec(g, { what: "Parties", objective: "Know how full the restaurant is.", measure: "Number of parties inside, counted from walking in until leaving.",
                                    value: me.value(), unit: "parties inside now", verdict: NO_TARGET }) },
  { label: "L · average", name: "Parties in the building, average", purpose: "The average number of parties inside over the last three minutes.",
    read: () => Number(one(scoreT().averageL)), value: () => one(scoreT().averageL),
    spec: (g, me) => scoreSpec(g, { what: "Average", objective: "Know how full the restaurant has been lately.", measure: "Number of parties inside, averaged over the last three minutes.",
                                    value: me.value(), unit: "parties inside, on average", verdict: NO_TARGET }) },
  { label: "W · average time inside", name: "Average time inside", purpose: "How long a party stays, from walking in to leaving.",
    read: () => Math.round(scoreT().W), value: () => scoreT().sample ? clockText(scoreT().W) : "–",
    spec: (g, me) => scoreSpec(g, { what: "Time inside", format: clockText, objective: "Know how long a visit takes.", measure: "Time from walking in to leaving, averaged over the parties that left in the last three minutes.",
                                    value: me.value(), unit: "per party, on average", verdict: NO_TARGET }) },
  { label: "λ × W · predicted L", name: "Parties in the building, predicted", purpose: "How many parties Little's Law says should be inside: arrivals per minute times the time each one stays.",
    read: () => Number(one(scoreT().predictedL)), value: () => scoreT().sample ? one(scoreT().predictedL) : "–",
    spec: (g, me) => scoreSpec(g, { what: "Prediction", objective: "Know how full the restaurant should be if it is keeping up.", measure: "Arrival rate times average time inside, both over the last three minutes.",
                                    value: me.value(), unit: "parties expected inside", verdict: NO_TARGET }) },
  { label: "Gap · average L, λ × W", name: "Gap between average and predicted", purpose: "How far the parties actually inside are from the prediction. A gap that stays above zero means parties are piling up faster than they leave.",
    read: () => Number(one(Math.abs(scoreGap()))),
    value: () => { const t = scoreT(), gap = scoreGap(); return t.sample ? `${gap >= 0 ? "+" : "−"}${one(Math.abs(gap))} (${percent(Math.abs(gap) / (t.averageL || 1))})` : "–"; },
    verdict: () => scoreT().sample ? atMost(Math.abs(scoreGap()), SCORE_GAP_LIMIT) : ["No history yet", "none"],
    spec: (g, me) => scoreSpec(g, { what: "Gap", target: SCORE_GAP_LIMIT, good: v => v <= SCORE_GAP_LIMIT, lead: `Target: at most ${SCORE_GAP_LIMIT} parties apart.`,
                                    objective: "The restaurant keeps up with arrivals: parties leave as fast as they come.", measure: "Average parties inside minus the prediction, over the last three minutes. The charts show its size, above or below.",
                                    value: me.value(), unit: "parties apart", verdict: me.verdict() }) },
  { label: "Average wait for food", name: "Average wait for food", purpose: "How long a party waits from placing its order until the food is on the table.",
    read: () => { const wait = scoreFoodWait(); return Number.isFinite(wait) ? Math.round(wait) : 0; },
    value: () => { const wait = scoreFoodWait(); return wait === null ? "\u2013" : wait === Infinity ? "\u221e" : clockText(wait); },
    verdict: () => { const wait = scoreFoodWait(); return wait === null ? ["No history yet", "none"] : wait === Infinity ? ["Off target", "bad"] : atMost(wait, DES_CONFIG.targets.food); },
    spec: (g, me) => ({
      ...desTimeSpec(desEngine.waits.food, DES_CONFIG.targets.food, { chartTitle: "Wait time by party", timelineTitle: "Wait time on the clock",
                     objective: "The food reaches the table before the guests lose patience.",
                     measure: "Time from the order being taken to the food being served, averaged over the parties served in the last three minutes. It is \u221e while no food is being served: no cook or no waiter on shift, or parties waiting and nothing served." }),
      value: me.value(), unit: scoreFoodWait() === Infinity ? "no food is being served" : "on average, over the last three minutes", verdict: me.verdict(),
    }) },
  { label: "Happy visits", name: "Happy visits", purpose: "The share of seated parties that dined with every wait within its target.",
    read: scoreHappy, value: () => scoreFinished() ? percent(scoreHappy()) : "–",
    verdict: () => scoreFinished() ? atLeast(scoreHappy(), DES_CONFIG.targets.happy) : ["No history yet", "none"],
    spec: (g, me) => scoreSpec(g, { what: "Happy share", format: percent, target: DES_CONFIG.targets.happy, good: v => v >= DES_CONFIG.targets.happy, lead: `Target: at least ${percent(DES_CONFIG.targets.happy)}.`,
                                    objective: "Parties leave happy.", measure: "Share of seated parties that dined with their waits for a table, to order and for the food all within target. A party that left without eating is not happy.",
                                    value: me.value(), unit: `happy, ${desEngine.happy} of ${scoreFinished()} so far`, verdict: me.verdict(),
                                    numbers: [["Dined", desEngine.departed], ["Gave up", desEngine.abandoned], ["Turned away", desEngine.balked]] }) },
];
const SCORE_EDGE = { good: "won", warn: "near", bad: "lost", none: "" };
SCORE.forEach((tile, i) => {
  const x = SX + (i % 3) * 139, y = 30 + Math.floor(i / 3) * 56, g = el("g", {}, scoreStatic);
  el("rect", { class: "score-ring", x: x - 3, y: y - 3, width: 137, height: 56, rx: 8 }, g);   // the selection outline, drawn just outside the tile so its own edge still shows
  tile.box = el("rect", { class: "des-stage score-tile", x, y, width: 131, height: 50, rx: 6 }, g);
  text(tile.label, { class: "des-tile-label", x: x + 8, y: y + 41 }, g);
  tile.text = text("", { class: "des-tile-value", x: x + 8, y: y + 24 }, g);
  tile.verdict ||= () => NO_TARGET;
  const g15 = tile.read && gauge(tile.read);
  tile.info = desAttach(g, { nodes: [], kind: "Scorecard", name: tile.name, purpose: tile.purpose, metrics: () => tile.spec(g15, tile) });
});
// the footnote, in small type: what this page is, and what the six Little's Law boxes are about
["This is the dashboard of the key business objectives, measured over the last three minutes.",
 "Little's Law: the average number of parties inside equals how fast they arrive times how",
 "long each one stays (L = λ × W). When the measured average keeps rising above that",
 "prediction, parties are piling up faster than they leave: the restaurant is not keeping up.",
].forEach((line, i) => text(line, { class: "small-label", x: SX + 204.5, y: 208 + i * 8, style: "font-size: 5.7px; text-anchor: middle" }, scoreStatic));
function drawScore() {
  for (const tile of SCORE) {
    setText(tile.text, tile.value());
    const edge = "des-stage score-tile " + SCORE_EDGE[tile.verdict()[1]];
    if (tile.box.getAttribute("class") !== edge) tile.box.setAttribute("class", edge);
  }
}
