// ---------- metrics ----------
// For the selected object: what it is for, how that is measured, the number so far, how it compares
// with its target and its own history, and a chart. Every target here is invented, like the timings.
const TARGET = {
  order: 60,        // seconds from order taken to food served
  door: 30, wantOrder: 15, ordering: 5, rail: 15, cooking: 25, pass: 10,   // seconds in a step
  equipment: 0.8,   // share of time in use, at most
  staff: 0.85,      // share of time busy, at most
  table: 0.7,       // share of time occupied, at least
};
const percent = share => Math.round(100 * share) + "%";
const mean = list => list.length ? list.reduce((sum, n) => sum + n, 0) / list.length : 0;
const stepAverage = key => FLOW[key].done ? FLOW[key].total / FLOW[key].done : 0;
// time a party has spent in a step so far, whether it has left the step or is still in it
const spentIn = (party, key) => party.spent[key] ?? (party.step === key ? clock - party.stepSince : 0);
const atMost = (value, target) => value <= target ? ["On target", "good"] : value <= target * 1.25 ? ["A little over target", "warn"] : ["Over target", "bad"];
const atLeast = (value, target) => value >= target ? ["On target", "good"] : value >= target * 0.75 ? ["A little under target", "warn"] : ["Under target", "bad"];
const trend = (latest, average, format) => latest === undefined ? "No full 15-second slice yet."
  : `Latest 15 seconds: ${format(latest)}, ${Math.abs(latest - average) < 0.02 * (average || 1) ? "the same as" : latest > average ? "above" : "below"} its average so far.`;

function useMetrics(g, limit, { objective, measure, lowIsFine, numbers }) {
  const average = clock ? g.sum / clock : 0, target = lowIsFine ? `at most ${percent(limit)}` : `at least ${percent(limit)}`;
  return {
    objective, measure, numbers,
    value: percent(average), unit: "of the time so far",
    verdict: lowIsFine ? (average <= limit ? ["Within the limit", "good"] : ["Over the limit", "bad"]) : atLeast(average, limit),
    notes: [`Target: ${target}.`, trend(g.history.at(-1), average, percent)],
    chart: barChart(g.history, limit, v => lowIsFine ? v <= limit : v >= limit, percent),
    caption: "Each bar is 15 seconds of service, oldest on the left. Dashed line: the target.",
    timeline: readingTimeline(g),
    timelineCaption: "On the clock: blue while it is in use. " + NOW_NOTE,
  };
}
function timeMetrics(key, { objective, measure, numbers }) {
  const step = FLOW[key], average = stepAverage(key), target = TARGET[key], last = step.history.at(-1);
  return {
    objective, measure, numbers,
    value: step.done ? clockText(average) : "–", unit: `on average, over ${step.done} so far`,
    verdict: !step.done ? ["No history yet", "none"] : target ? atMost(average, target) : ["No target", "none"],
    notes: [target ? `Target: at most ${clockText(target)}.` : "No target: this time is not ours to shorten.",
            last === undefined ? "" : `Latest: ${clockText(last)}, ${last > average ? "above" : "at or below"} the average so far.`],
    chart: barChart(step.history, target, v => !target || v <= target, clockText),
    caption: `Each bar is one party, the latest ${KEEP} at most, oldest on the left.${target ? " Dashed line: the target." : ""}`,
    timeline: staysTimeline(step.stays, target),
    timelineCaption: `On the clock: one thin bar per party, from when it entered to when it left; parties here at the same time are stacked.${target ? " Green: within the target. Red: over it." : ""} ` + NOW_NOTE,
  };
}
const NOW_NOTE = "The yellow line is now, and the last three minutes slide past it.";
const STEP_OBJECTIVE = {
  walkIn: "Get the party from the door to its table without delay. The room layout sets this time.",
  menu: "Let the guests take the time they want with the menu.",
  wantOrder: "Have a waiter at the table soon after the guests are ready to order.",
  ordering: "Write the order down quickly once the waiter is at the table.",
  cooking: "Turn a ticket into food as fast as the kitchen can.",
  eating: "Let the guests take the time they want over the meal.",
  leaving: "Let the party out. The room layout sets this time.",
};
const QUEUE_METRICS = {
  door: { objective: "Nobody waits outside for long, and nobody is turned away.", what: "a party waits outside before it gets a table" },
  rail: { objective: "A cook takes each ticket soon after it is hung, so the kitchen never falls behind.", what: "a ticket hangs on the rail before a cook takes it" },
  pass: { objective: "Finished food is collected while it is hot.", what: "an order sits on the pass before a waiter takes it" },
};

function metricsFor(info) {
  const it = info.subject;
  switch (info.kind) {
    case "Order ticket": {
      const total = (it.delivered ?? clock) - it.created, average = mean(servedOrders);
      const stage = (key, step, label) => ({ label, value: it.spent[key] ?? (it.stage === key ? clock - it.since : 0), average: stepAverage(step), target: TARGET[step] });
      return {
        objective: "To be closed as soon as possible: the guests are waiting from the moment it is written.",
        measure: "Time from the order being taken to the food being served. The clock stops when the food reaches the table.",
        value: clockText(total), unit: it.delivered ? "closed" : "and counting",
        verdict: atMost(total, TARGET.order),
        notes: [`Target: at most ${clockText(TARGET.order)}.`,
                servedOrders.length ? `Average of the ${servedOrders.length} orders served so far: ${clockText(average)}. This one is ${total > average ? "above" : "at or below"} it.` : "No order has been served yet."],
        chart: rowChart([stage("carried", "toRail", "To the rail"), stage("rail", "rail", "On the rail"), stage("cooking", "cooking", "Cooking"),
                         stage("pass", "pass", "On the pass"), stage("delivering", "deliver", "To the table")]),
        caption: "Where this order's time went. Bar: this order. White mark: average order so far. Orange mark: target, where there is one.",
        timeline: partsTimeline(it.created, [["carried", WORK_COLOR], ["rail", WAIT_COLOR], ["cooking", WORK_COLOR], ["pass", WAIT_COLOR], ["delivering", WORK_COLOR]]
          .map(([key, fill]) => [it.spent[key] ?? (it.stage === key ? clock - it.since : 0), fill])),
        timelineCaption: "On the clock: this order from taken to served. Orange: waiting on the rail or the pass. Grey: being carried or cooked. " + NOW_NOTE,
      };
    }
    case "Guests": {
      const food = it.ticket ? (it.ticket.delivered ?? clock) - it.ticket.created : 0;
      const rows = [
        { label: "For a table", value: spentIn(it, "door"), average: stepAverage("door"), target: TARGET.door },
        { label: "To order", value: spentIn(it, "wantOrder"), average: stepAverage("wantOrder"), target: TARGET.wantOrder },
        { label: "For the food", value: food, average: mean(servedOrders), target: TARGET.order },
      ];
      const sum = field => rows.reduce((total, row) => total + row[field], 0);
      return {
        objective: "To be served without waiting on the staff. Time with the menu and time eating are theirs to enjoy and are not counted.",
        measure: "Time spent waiting for a table, waiting for a waiter to take the order, and waiting for the food, added up.",
        value: clockText(sum("value")), unit: "waiting so far",
        verdict: atMost(sum("value"), sum("target")),
        notes: [`Target: at most ${clockText(sum("target"))} in all.`, `Average party so far: ${clockText(sum("average"))}. This one is ${sum("value") > sum("average") ? "above" : "at or below"} it.`],
        chart: rowChart(rows),
        caption: "Bar: this party. White mark: average so far. Orange mark: target.",
        timeline: partsTimeline(it.start ?? clock, [["door", WAIT_COLOR], ["walkIn", WORK_COLOR], ["menu", OWN_COLOR], ["wantOrder", WAIT_COLOR], ["ordering", WORK_COLOR],
                                           ...KITCHEN_STEPS.map(key => [key, WAIT_COLOR]), ["eating", OWN_COLOR], ["leaving", WORK_COLOR]]
          .map(([key, fill]) => [spentIn(it, key), fill])),
        timelineCaption: "On the clock: this party's visit. Orange: waiting for a table, a waiter or the food. Green: their own time with the menu and the meal. Grey: walking and ordering. " + NOW_NOTE,
        numbers: [["Time with the menu (not counted)", clockText(spentIn(it, "menu"))], ["Time eating (not counted)", clockText(spentIn(it, "eating"))]],
      };
    }
    case "Table":
      return useMetrics(it.gauge, TARGET.table, {
        objective: "To have guests at it. A free table earns nothing.",
        measure: "Share of the time the table is taken, from the moment a party is sent to it until that party finishes eating.",
        numbers: [["Parties seated", it.seated], ["Guests seated", it.guests],
                  ["Seats filled, on average", it.seated ? percent(it.guests / (it.seated * it.capacity)) : "–"]],
      });
    case "Waiter":
      return useMetrics(it.gauge, TARGET.staff, {
        lowIsFine: true,
        objective: "To be free often enough that no table and no plate waits. A waiter who is always busy means guests are waiting.",
        measure: "Share of the time spent on a job: walking to a table, taking an order, carrying a ticket or carrying food.",
        numbers: [["Orders taken", it.counts.taking || 0], ["Orders served", it.counts.serving || 0]],
      });
    case "Cook":
      return useMetrics(it.gauge, TARGET.staff, {
        lowIsFine: true,
        objective: "To be free often enough that tickets do not pile up on the rail. A cook who is always busy means orders are waiting.",
        measure: "Share of the time spent on an order: fetching the ticket, cooking, waiting for equipment, or carrying food to the pass.",
        numbers: [["Orders cooked", it.counts.plating || 0]],
      });
    case "Kitchen equipment":
      return useMetrics(it.gauge, TARGET.equipment, {
        lowIsFine: true,
        objective: "To be used, but not beyond the share of time recommended for it. Here that is taken to be 80%.",
        measure: "Share of the time it is taken by a cook, from the moment the cook claims it until the cooking on it is done.",
      });
    case "Entrance":
    case "Hand-off point": {
      const length = QUEUE_LENGTH[it], lost = partyCount + turnedAway ? turnedAway / (partyCount + turnedAway) : 0;
      const numbers = [["Average number waiting", (clock ? length.sum / clock : 0).toFixed(1)]];
      if (it === "door") numbers.push(["Parties turned away", `${turnedAway} (${percent(lost)} of arrivals)`]);
      return timeMetrics(it, { objective: QUEUE_METRICS[it].objective, measure: `How long ${QUEUE_METRICS[it].what}.`, numbers });
    }
    case "Flow step":
      if (it.key === "waitForFood") {
        const served = servedOrders.length, average = mean(servedOrders), last = servedOrders.at(-1);
        return {
          objective: "The food arrives soon after the order is taken.",
          measure: "Time from the order being taken to the food being served, for each order. It is the same clock the tickets use.",
          value: served ? clockText(average) : "\u2013", unit: `on average, over ${served} so far`,
          verdict: served ? atMost(average, TARGET.order) : ["No history yet", "none"],
          notes: [`Target: at most ${clockText(TARGET.order)}.`,
                  served ? `Latest: ${clockText(last)}, ${last > average ? "above" : "at or below"} the average so far.` : ""],
          chart: barChart(servedOrders.slice(-KEEP), TARGET.order, v => v <= TARGET.order, clockText),
          caption: `Each bar is one order served, the latest ${KEEP} at most, oldest on the left. Dashed line: the target.`,
          timeline: staysTimeline(orderStays, TARGET.order),
          timelineCaption: "On the clock: one thin bar per order, from taken to served; orders open at the same time are stacked. Green: within the target. Red: over it. " + NOW_NOTE,
        };
      }
      return timeMetrics(it.key, { objective: STEP_OBJECTIVE[it.key], measure: "How long a party spends in this step, from entering it to leaving it." });
  }
}
