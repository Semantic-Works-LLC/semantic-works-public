// ---------- DES views: the one engine, and the cards for everything in it ----------
// The DES view (floor plan and dashboard) and the pipeline view are three renderers of this one
// engine. The cards and metrics for its parties, resources, queues and stages are defined here once,
// so the same object is selected whichever picture it was clicked in.
const desEngine = new DESEngine(DES_CONFIG);
const DES_EVENTS_KEPT = 300;
const desRecent = [];   // the latest events, newest first, kept by subscribing to the engine
const desPartyInfos = new Map();   // the card of every party there has been, by id; a party keeps its card after it has left
const desGaveUp = new Set();   // parties that walked out without eating, so a view can show them leaving that way
desEngine.subscribe(event => {
  desRecent.unshift(event);
  if (desRecent.length > DES_EVENTS_KEPT) desRecent.pop();
  if (event.type === "PARTY_ABANDONED") desGaveUp.add(event.entityId);
});   // (A party that has left keeps its card: if it was selected or pinned it stays so, and its card says the visit is over.)

function desAttach(node, info) {
  info.nodes.push(node);
  node.setAttribute("data-selectable", "");
  node.addEventListener("click", e => { e.stopPropagation(); select(info); });
  return info;
}
const desMean = stats => stats.done ? stats.total / stats.done : 0;

// a card about a time: how long parties wait in a queue or spend in a stage
function desTimeSpec(stats, target, { objective, measure, numbers, lead = [], chartTitle = "Time by party", timelineTitle = "Time on the clock" }) {
  const mean = desMean(stats), last = stats.history.at(-1);
  return {
    objective, measure, numbers,
    value: stats.done ? clockText(mean) : "–", unit: `on average, over ${stats.done} so far`,
    verdict: !stats.done ? ["No history yet", "none"] : target ? atMost(mean, target) : ["No target", "none"],
    notes: [...lead, target ? `Target: at most ${clockText(target)}.` : "No target: this time is not ours to shorten.",
            last === undefined ? "" : `Latest: ${clockText(last)}, ${last > mean ? "above" : "at or below"} the average so far.`],
    chartTitle, timelineTitle,
    chart: barChart(stats.history, target, v => !target || v <= target, clockText),
    caption: `Each bar is one party, the latest ${DES_KEEP} at most, oldest on the left.${target ? " Dashed line: the target." : ""}`,
    timeline: staysTimeline(stats.stays, target),
    timelineCaption: `On the clock: one thin bar per party, from entering to leaving; parties here at the same time are stacked.${target ? " Green: within the target. Red: over it." : ""} ` + NOW_NOTE,
  };
}

// ----- resources: pools and their units
const DES_RES = {
  tables: { name: "Tables", one: "Table", kind: "Table", objective: "Tables are taken. A free table earns nothing.", poolMeasure: "Share of the twelve tables that are taken, averaged over time.", unitMeasure: "Share of the time this table is taken, from a party being seated at it until that party leaves.",
            about: "Where a party sits. Seized when the party is let in and held through the menu, the order, the wait for the food and the meal; released when the party leaves.",
            why: "Tables are what the restaurant has to sell. A table held by a slow visit is not there for the next party." },
  waiters: { name: "Waiters", one: "Waiter", kind: "Waiter", objective: "Waiters are busy, but free often enough that no party waits to order and no food stands on the pass.", poolMeasure: "Share of the waiters on shift who are taking an order or running food, averaged over time.", unitMeasure: "Share of the time this waiter is taking an order or running food.",
             about: "Front-of-house labour. Seized for one task at a time, taking an order or running food, and released straight after.",
             why: "Parties wait in the order queue and food waits on the pass whenever every waiter is taken." },
  cooks: { name: "Cooks", one: "Cook", kind: "Cook", objective: "Cooks are busy, but free often enough that no order waits on the rail and no part of an order waits for a cook.", poolMeasure: "Share of the cooks on shift who are planning, cooking or plating, averaged over time.", unitMeasure: "Share of the time this cook is planning, cooking or plating.",
           about: "Kitchen labour. Seized for one job at a time: planning an order, making one part of it, or plating it. Two cooks can work on parts of the same order at once.",
           why: "Tickets wait on the rail, and parts wait at the equipment, whenever every cook is taken." },
  stoves: { name: "Stoves", one: "Stove", kind: "Kitchen equipment", objective: "The stoves are used, but one is free when an order's stove dishes are ready to cook.", poolMeasure: "Share of the two stoves in use, averaged over time.", unitMeasure: "Share of the time this stove is in use.",
            about: "A burner on the range. Seized, together with a cook, while an order's stove dishes are cooked.",
            why: "One order per burner at a time. With more cooks than burners, the burners become the limit." },
  oven: { name: "Pizza oven", one: "Pizza oven", kind: "Kitchen equipment", objective: "The pizza oven is used, but free when the next order's pizzas are ready to bake.", poolMeasure: "Share of the time the pizza oven is in use.", unitMeasure: "Share of the time the pizza oven is in use.",
          about: "The brick oven. Seized, together with a cook, while an order's pizzas bake.",
          why: "There is one, so orders with pizza take turns." },
  coffee: { name: "Coffee machine", one: "Coffee machine", kind: "Kitchen equipment", objective: "The coffee machine is used, but free when the next order's coffees are ready to be made.", poolMeasure: "Share of the time the coffee machine is in use.", unitMeasure: "Share of the time the coffee machine is in use.",
            about: "The coffee machine. Seized, together with a cook, while an order's coffees are made.",
            why: "There is one. It is quick, but orders still take turns." },
};
const DES_TASK_TEXT = { table: "seated at it", order: "taking the order of", deliver: "running the food of", plan: "planning the order of",
                        plate: "plating the order of", stoves: "cooking for", oven: "baking for", coffee: "making coffee for" };
for (const [id, res] of Object.entries(DES_RES)) {
  const pool = desEngine.resources[id], limit = DES_CONFIG.useTargets[id], lowIsFine = limit.atMost !== undefined;
  const target = lowIsFine ? limit.atMost : limit.atLeast, single = pool.capacity === 1;
  const objective = res.objective;
  res.id = id;
  res.gauge = gauge(() => pool.capacity ? pool.allocated / pool.capacity : 0);
  res.info = {
    nodes: [], kind: "Resource pool", name: res.name,
    what: single ? "A resource pool with one unit." : `A resource pool of ${pool.capacity} units.`,
    purpose: res.about, why: res.why,
    metrics: () => ({ ...useMetrics(res.gauge, target, {
      lowIsFine, objective,
      measure: res.poolMeasure,
      numbers: [["In use now", `${pool.allocated} of ${pool.capacity}`]],
    }), chartTitle: "Use every 15 seconds", timelineTitle: "Use on the clock" }),
  };
  res.units = pool.units.map((_, i) => {
    const unit = { gauge: gauge(() => Boolean(pool.units[i])), name: single ? res.one : `${res.one} ${i + 1}` };
    unit.info = {
      nodes: [], kind: res.kind, name: unit.name,
      what: (single ? `The only unit of the ${res.name.toLowerCase()} pool` : `Unit ${i + 1} of the ${res.name.toLowerCase()} pool`)
        + (id === "tables" ? `. It seats ${DES_CONFIG.tables[i]}.` : "."),
      purpose: res.about, why: res.why,
      metrics: () => {
        const holder = pool.units[i];
        return { ...useMetrics(unit.gauge, target, {
          lowIsFine, objective, measure: res.unitMeasure,
          numbers: [["Now", (holder ? `${DES_TASK_TEXT[holder.task][0].toUpperCase() + DES_TASK_TEXT[holder.task].slice(1)} party ${holder.party.slice(1)}.` : holder === DES_OUT ? desOutWords(id).state + "." : "Free.")
                            + (pool.goingOut.has(i) ? ` ${desOutWords(id).state} once this is done.` : "")]],
        }), chartTitle: "Use every 15 seconds", timelineTitle: "Use on the clock" };
      },
    };
    return unit;
  });
}

// what being out of service is called for each kind of resource, and the two actions that go with it
function desOutWords(id) {
  if (DES_STAFF.includes(id)) return { state: "Off sick", out: "Call in sick", back: "Back to work", outDoes: "Takes this person off the floor, as if they had called in sick. If they are in the middle of a task, they finish it first.", backDoes: "Brings this person back to work." };
  if (id === "tables") return { state: "Out of use", out: "Close table", back: "Open table", outDoes: "Takes this table out of use. If a party is at it, they finish their visit first.", backDoes: "Puts this table back in use." };
  return { state: "Broken down", out: "Break down", back: "Fix", outDoes: "Declares this machine broken. If it is in the middle of a job, the job is finished first.", backDoes: "Fixes this machine, so it can be used again." };
}
// which unit of which resource a card is about, if it is about one
function desUnitOf(info) {
  for (const id in DES_RES) {
    const index = DES_RES[id].units.findIndex(unit => unit.info === info);
    if (index >= 0) return { id, index };
  }
  return null;
}

// ----- FIFO queues
const DES_QUEUE = {
  host: { name: "Host queue", waits: "a table that fits them", about: "Parties at the door, waiting for a free table that fits them. A party that finds three already waiting goes away." },
  order: { name: "Order queue", waits: "a waiter to take the order", about: "Parties that have read the menu and wait for a waiter." },
  plan: { name: "Ticket rail", waits: "a cook to plan the order", about: "Orders that have reached the kitchen and wait for a cook to plan them." },
  // the three kitchen queues are named after the task they stand in front of, not after its equipment:
  // a part waits here for everything the task needs, a cook as much as the stove, oven or machine
  stoves: { name: "Cook-on-stove queue", short: "Cook on stove", waits: "a cook and a stove", about: "The stove parts of planned orders, waiting to be cooked. Cooking needs a cook and a free burner at the same time." },
  oven: { name: "Bake-pizza queue", short: "Bake pizza", waits: "a cook and the oven", about: "The pizza parts of planned orders, waiting to be baked. Baking needs a cook and the oven at the same time." },
  coffee: { name: "Make-coffee queue", short: "Make coffee", waits: "a cook and the coffee machine", about: "The coffee parts of planned orders, waiting to be made. Making coffee needs a cook and the machine at the same time." },
  plate: { name: "Plating queue", waits: "a cook to plate it", about: "Orders whose parts are all done, waiting for a cook to plate them." },
  run: { name: "Pass", waits: "a waiter to run the food", about: "Plated food waiting for a waiter. It is getting cold here, so running food comes before taking orders." },
};
// what a queue is short of, in words: for a card (long) or under a node (short)
const DES_MISSING = { tables: ["a table that fits", "table"], waiters: ["a waiter", "waiter"], cooks: ["a cook", "cook"],
                      stoves: ["a stove", "stove"], oven: ["the oven", "oven"], coffee: ["the coffee machine", "machine"] };
const desMissingText = (pools, long) => long ? pools.map(pool => DES_MISSING[pool][0]).join(" and ") + (pools.length > 1 ? ", both taken" : "")
  : pools.length > 1 ? `for ${DES_MISSING[pools[0]][1]} + ${DES_MISSING[pools[1]][1]}` : "waiting for " + DES_MISSING[pools[0]][1];
// how the waiting in a queue so far splits by what was missing, biggest share first
function desBlockedRows(id) {
  const causes = Object.entries(desEngine.blocked[id]), total = causes.reduce((sum, [, seconds]) => sum + seconds, 0);
  if (DES_QUEUE_NEEDS[id].length < 2 || !total) return [];
  return causes.sort((a, b) => b[1] - a[1]).map(([cause, seconds]) => [`Of the waiting so far, missing ${desMissingText(cause.split("+"), true)}`, percent(seconds / total)]);
}
for (const [id, queue] of Object.entries(DES_QUEUE)) {
  queue.id = id;
  queue.info = {
    nodes: [], kind: "FIFO queue", name: queue.name,
    what: "A first-in, first-out buffer. A party stands here while the resource it needs is fully taken.",
    purpose: queue.about,
    why: "A queue is unserved demand. Where one grows is where the restaurant is short of capacity.",
    metrics: () => desTimeSpec(desEngine.queueStats[id], DES_CONFIG.queueTargets[id], {
      objective: `Nobody waits long for ${queue.waits}.`,
      measure: `Time from joining this queue to getting ${queue.waits}. A party that does not have to wait counts as 0:00.`,
      numbers: [["Waiting now", desEngine.queues[id].length],
                ...(desEngine.queues[id].length ? [["Missing right now", desMissingText(desEngine.missing(id), true)]] : []),
                ...desBlockedRows(id),
                ...(id === "host" ? [["Turned away", `${desEngine.balked} of ${desEngine.arrived + desEngine.balked} arrivals`]] : [])],
    }),
  };
}

// ----- the states a party goes through, in order; a queue state shares its queue's card
const DES_STAGES = [
  { state: "WAITING_FOR_TABLE", label: "Host Q", queue: "host" },
  { state: "READING_MENU", label: "Browsing", name: "Browsing the menu", kind: "delay", about: "The party reads the menu. A delay: it needs nobody and nothing but the table it already holds." },
  { state: "WAITING_FOR_WAITER_ORDER", label: "Order Q", queue: "order" },
  { state: "ORDERING", label: "Ordering", name: "Ordering", kind: "task", needs: "a waiter", about: "A waiter takes the party's order. The waiter is seized for the task and released when it is done." },
  { state: "WAITING_FOR_COOK", label: "Rail", queue: "plan" },
  { state: "PLANNING", label: "Planning", name: "Planning the order", kind: "task", needs: "a cook", about: "A cook reads the order and splits it into parts: stove dishes, pizzas, coffees." },
  { state: "COOKING", label: "Cooking", name: "Cooking", kind: "parallel", about: "The order's parts are made in parallel, each by a cook on its own equipment. The stage lasts until the last part is done, and includes any wait for a cook or for equipment." },
  { state: "WAITING_FOR_PLATING", label: "Plate Q", queue: "plate" },
  { state: "PLATING", label: "Plating", name: "Plating", kind: "task", needs: "a cook", about: "A cook plates the finished order and puts it on the pass." },
  { state: "WAITING_FOR_WAITER_DELIVER", label: "Pass", queue: "run" },
  { state: "FOOD_RUNNING", label: "Running", name: "Running the food", kind: "task", needs: "a waiter", about: "A waiter carries the food from the pass to the table." },
  { state: "EATING_AND_BILLING", label: "Dining", name: "Dining", kind: "delay", about: "The party eats and pays. A delay: it needs nothing but the table." },
];
const DES_STAGE = {};
for (const stage of DES_STAGES) {
  DES_STAGE[stage.state] = stage;
  if (stage.queue) { stage.info = DES_QUEUE[stage.queue].info; continue; }
  stage.info = {
    nodes: [], kind: "Pipeline stage", name: stage.name,
    what: stage.kind === "delay" ? "A delay: time passes for the party, and no shared resource is used."
      : stage.kind === "task" ? `A task: it seizes ${stage.needs}, takes its time, and releases them.` : "A stage in which the order is split into parts that are worked at the same time.",
    purpose: stage.about,
    why: "Every party passes through the stages in the same order. Counting who is in each shows where the work in progress sits.",
    metrics: () => desTimeSpec(desEngine.stateStats[stage.state] ??= desEngine.stats(), 0, {
      objective: stage.kind === "delay" ? "Let the guests take the time they want." : "Do the work in the time it takes; the waiting before it is what we try to shorten.",
      measure: "Time a party spends in this stage, from entering it to leaving it.",
      numbers: [["Parties here now", [...desEngine.parties.values()].filter(party => party.state === stage.state).length]],
    }),
  };
}

// ----- tasks, as the pipeline view draws them: one box holds the waiting for what the task needs and the task itself
const DES_TASKS = {
  seating: { name: "Get a table", label: "Get a\ntable", objective: "Seat every party that walks in at a table that fits it, without making it wait at the door.",
             measure: "Time a party stands at the door, from arriving until a table that fits it is free. A party seated at once counts as 0:00.",
             kind: "task", queue: "host", instant: true,
             about: "The party is given a table. If none that fits is free it waits at the door; a party that finds three already waiting goes away.",
             needs: "A table that fits the party. It is kept until the party leaves." },
  browsing: { name: "Browsing the menu", label: "View\nmenu", objective: "Let the guests choose what they want in their own time.",
              measure: "Time from sitting down until the guests are ready to order.",
              kind: "delay", state: "READING_MENU",
              about: "The party reads the menu.", needs: "Nothing new: there is a menu for everyone. The party holds its table." },
  ordering: { name: "Ordering", label: "Order", objective: "Take the order the moment the guests are ready, and get it to the kitchen.",
              measure: "Time from the guests being ready to order until a waiter is free and starts taking the order. A party served at once counts as 0:00.",
              kind: "task", queue: "order", state: "ORDERING",
              about: "A waiter takes the party's order.", needs: "A waiter, for as long as the task lasts." },
  planning: { name: "Planning the order", label: "Plan", objective: "Split each order into its parts as soon as it reaches the kitchen, so cooking can start.",
              measure: "Time an order waits on the rail, from being taken at the table until a cook is free and starts planning it. An order picked up at once counts as 0:00.",
              kind: "task", queue: "plan", state: "PLANNING",
              about: "A cook reads the order and splits it into parts: stove dishes, pizzas, coffees. The parts are then made in parallel.", needs: "A cook, for as long as the task lasts." },
  stoves: { name: "Cook on stove", label: "Use\nstove", objective: "Cook the order's stove dishes as soon as the order is planned, so they are not what holds the order up.",
            measure: "Time from the order being planned until a cook and a stove are both free and cooking starts. An order that starts at once counts as 0:00.",
            kind: "task", queue: "stoves", part: "stoves",
            about: "A cook cooks the order's stove dishes. Only for orders that have any.", needs: "A cook and a stove, both at the same moment." },
  oven: { name: "Bake pizza", label: "Bake\npizza", objective: "Bake the order's pizzas as soon as the order is planned, so they are not what holds the order up.",
          measure: "Time from the order being planned until a cook and the pizza oven are both free and baking starts. An order that starts at once counts as 0:00.",
          kind: "task", queue: "oven", part: "oven",
          about: "A cook bakes the order's pizzas. Only for orders that have any.", needs: "A cook and the pizza oven, both at the same moment." },
  coffee: { name: "Make coffee", label: "Make\ncoffee", objective: "Make the order's coffees as soon as the order is planned, so they are not what holds the order up.",
            measure: "Time from the order being planned until a cook and the coffee machine are both free and the coffees are started. An order that starts at once counts as 0:00.",
            kind: "task", queue: "coffee", part: "coffee",
            about: "A cook makes the order's coffees. Only for orders that have any.", needs: "A cook and the coffee machine, both at the same moment." },
  plating: { name: "Plating", label: "Plate\nfood", objective: "Get cooked food out of the kitchen and onto the pass as soon as the whole order is ready.",
             measure: "Time from the order's last part being done until a cook is free and starts plating. Waiting for the other parts is not counted here: it shows in the party's wait for the food.",
             kind: "task", queue: "plate", state: "PLATING", join: true,
             about: "A cook plates the finished order and puts it on the pass.", needs: "Every part of the order done, and then a cook." },
  running: { name: "Running the food", label: "Food\nto table", objective: "Deliver the food from the pass to the table while it is hot.",
             measure: "Time the food stands on the pass, from being plated until a waiter is free and takes it. Food taken at once counts as 0:00.",
             kind: "task", queue: "run", state: "FOOD_RUNNING",
             about: "A waiter carries the food from the pass to the table.", needs: "A waiter, for as long as the task lasts." },
  dining: { name: "Dining", label: "Dining", objective: "Let the guests enjoy the meal in their own time.",
            measure: "Time from the food being served until the party gets up to leave.",
            kind: "delay", state: "EATING_AND_BILLING",
            about: "The party eats and pays.", needs: "Nothing new. The party still holds its table." },
};
// orders with some parts done and others still being made: they cannot be plated yet
const desHeldForParts = () => [...desEngine.parties.values()].filter(party => party.state === "COOKING" && Object.values(party.parts).includes("done"));
for (const [key, task] of Object.entries(DES_TASKS)) {
  task.key = key;
  const work = () => task.part ? desEngine.partStats[task.part] : (desEngine.stateStats[task.state] ??= desEngine.stats());
  const doing = () => [...desEngine.parties.values()].filter(party => task.part ? party.parts?.[task.part] === "cooking" : task.state && party.state === task.state).length;
  task.info = {
    nodes: [], name: task.name,
    purpose: task.about,
    extra: [["Needs", task.needs]],
    metrics: () => {
      const taking = task.instant ? desEngine.stats() : work(), took = taking.done ? clockText(desMean(taking)) : "\u2013";
      const titles = task.queue ? { chartTitle: "Wait time by party", timelineTitle: "Wait time on the clock" } : {};
      if (!task.queue) return desTimeSpec(taking, 0, { ...titles, objective: task.objective, measure: task.measure, numbers: [["Parties here now", doing()]] });
      const waiting = desEngine.queues[task.queue].length, held = task.join ? desHeldForParts().length : 0, gate = waiting ? desMissingText(desEngine.missing(task.queue), true) : "";
      return desTimeSpec(desEngine.queueStats[task.queue], DES_CONFIG.queueTargets[task.queue], {
        lead: [waiting ? `Waiting now: ${waiting}, for ${gate}.` : "Waiting now: nobody.",
               ...(held ? [`Also held back: ${held} ${held === 1 ? "order" : "orders"} waiting for other parts to be done.`] : [])],
        ...titles, objective: task.objective, measure: task.measure,
        numbers: [["Waiting now", waiting], ["Held up by", waiting ? gate : "Nothing: nobody is waiting."],
                  ...(task.join ? [["Orders waiting for other parts", held]] : []),
                  ...desBlockedRows(task.queue),
                  ...(task.instant ? [["Time the step itself takes", "None: once a table is free the party is seated at once."]]
                    : [["Being done now", doing()], ["Time the step itself takes, on average", took]])],
      });
    },
  };
}

// ----- the other thing Plating waits for: the rest of the order. A precondition, but not a resource, with a card of its own.
const desPartsGauge = gauge(() => desHeldForParts().length);
const desPartsInfo = {
  nodes: [], kind: "Precondition", name: "Other parts of the order",
  what: "A condition a step waits for that is not a resource: every part of the order has to be done.",
  purpose: "An order is split into parts, stove dishes, pizzas and coffees, which are made at the same time. Plating can start only when the last of them is finished.",
  why: "An order is as slow as its slowest part. Orders held here have food ready that is getting cold while another part is still being made.",
  extra: [["Needed by", "Plating."]],
  metrics: () => {
    const g = desPartsGauge, now = desHeldForParts(), mean = clock ? g.sum / clock : 0;
    return {
      objective: "Few orders standing with some parts done and others not.",
      measure: "How many orders are short of a part, counted from the moment their first part is done until their last one is.",
      value: now.length, unit: now.length === 1 ? "order short of a part now" : "orders short of a part now",
      verdict: ["No target", "none"],
      notes: [`On average so far: ${mean.toFixed(1)}.`,
              now.length ? `Now: ${now.map(party => `party ${party.number} (still to come: ${Object.entries(party.parts).filter(([, state]) => state !== "done").map(([kind]) => DES_RES[kind].one.toLowerCase()).join(", ")})`).join("; ")}.` : ""],
      chartTitle: "Orders every 15 seconds", timelineTitle: "Orders on the clock",
      chart: barChart(g.history, 0),   // no target, so nothing to judge the bars by
      caption: "Each bar is 15 seconds of service, oldest on the left: the average number of orders short of a part.",
      timeline: readingTimeline(g),
      timelineCaption: "On the clock: how many orders were short of a part. " + NOW_NOTE,
    };
  },
};

// ----- outcomes: the four ways a visit ends, each with its own card
// How many parties ended this way in the latest 15 seconds: read every tick, it notices the count going up.
function desOutcomeGauge(count) {
  const times = [];
  let seen = 0;
  return gauge(() => {
    for (const total = count(); seen < total; seen++) times.push(clock);
    while (times.length && times[0] <= clock - 15) times.shift();
    return times.length;
  });
}
const desCame = () => desEngine.arrived + desEngine.balked;
const DES_OUTCOME = {
  away: { name: "Turned away", count: () => desEngine.balked, of: desCame, ofWhat: "parties that came to the door",
          purpose: "A party that comes to the door and finds three parties already waiting for a table does not join the line: it goes somewhere else.",
          objective: "Turn nobody away: every party that comes to the door gets in.",
          measure: "Parties turned away at the door, counted since the start. The charts show how many in each 15 seconds." },
  noorder: { name: "Left: slow waiter", count: () => desEngine.abandonedFor.order, of: () => desEngine.arrived, ofWhat: "parties that walked in",
             purpose: "A seated party that has read the menu and waits too long for a waiter to take its order gets up and leaves without eating.",
             objective: "Lose no party for want of a waiter: every order is taken before the guests lose patience.",
             measure: "Parties that left while waiting to order, counted since the start. The charts show how many in each 15 seconds." },
  hungry: { name: "Left: slow kitchen", count: () => desEngine.abandonedFor.food, of: () => desEngine.arrived, ofWhat: "parties that walked in",
            purpose: "A party that has ordered and waits too long for its food gets up and leaves without eating. The work already done on its order is wasted.",
            objective: "Lose no party to a slow kitchen: the food reaches the table before the guests lose patience.",
            measure: "Parties that left while waiting for their food, counted since the start. The charts show how many in each 15 seconds." },
  out: { name: "Dined", count: () => desEngine.departed, of: () => desEngine.arrived, ofWhat: "parties that walked in",
         purpose: "A party that was served, ate, paid and left. This is the outcome the restaurant is there for.",
         objective: "Every party that walks in dines.",
         measure: "Parties that finished their meal and left, counted since the start. The charts show how many in each 15 seconds." },
};
for (const outcome of Object.values(DES_OUTCOME)) {
  const g = desOutcomeGauge(outcome.count);
  outcome.info = {
    nodes: [], kind: "Outcome", name: outcome.name, purpose: outcome.purpose,
    metrics: () => {
      const count = outcome.count(), of = outcome.of();
      return scoreSpec(g, {
        what: "Parties", format: value => value.toFixed(1), objective: outcome.objective, measure: outcome.measure,
        value: count, unit: count === 1 ? "party so far" : "parties so far", verdict: ["No target", "none"],
        numbers: [[`Share of the ${outcome.ofWhat}`, of ? percent(count / of) : "\u2013"],
                  ...(outcome === DES_OUTCOME.out ? [["Of them happy, every wait within its target", count ? percent(desEngine.happy / count) : "\u2013"]] : [])],
      });
    },
  };
}

// ----- the door: parties arriving
const desArrivalsGauge = gauge(() => Number((desEngine.telemetry().lambda * 60).toFixed(1)));
const desArrivalsInfo = {
  nodes: [], kind: "Start", name: "Parties arriving",
  purpose: "Parties come to the door. One that finds a free table, or room to wait, walks in; one that finds three parties already waiting is turned away.",
  metrics: () => {
    const came = desEngine.arrived + desEngine.balked, rate = desEngine.telemetry().lambda * 60;
    return scoreSpec(desArrivalsGauge, {
      what: "Arrivals", objective: "Know how much business comes to the door, and how much of it gets in.",
      measure: "Parties that walked in during the last three minutes, per minute. Parties turned away are counted separately, below.",
      value: rate.toFixed(1), unit: "parties per minute walking in", verdict: ["No target", "none"],
      numbers: [["Came to the door", came], ["Walked in", desEngine.arrived], ["Turned away", desEngine.balked],
                ["Share turned away", came ? percent(desEngine.balked / came) : "\u2013"]],
    });
  },
};

// ----- everyone in the building: the parties, as a group
const desPartiesGauge = gauge(() => desEngine.parties.size);
const desPartiesInfo = {
  nodes: [], kind: "Parties", name: "Parties",
  purpose: "The parties in the building right now, from walking in until leaving. They are who everything else is here for.",
  metrics: () => {
    const parties = [...desEngine.parties.values()], waiting = desEngine.queues.host.length, t = desEngine.telemetry();
    return scoreSpec(desPartiesGauge, {
      what: "Parties", objective: "Know who is in the restaurant, and get each of them through their visit.",
      measure: "Number of parties in the building, counted from walking in until leaving. The charts show the average in each 15 seconds.",
      value: parties.length, unit: parties.length === 1 ? "party in the building now" : "parties in the building now", verdict: ["No target", "none"],
      numbers: [["Waiting at the door", waiting], ["Seated", parties.length - waiting], ["Guests in the building", parties.reduce((sum, party) => sum + party.size, 0)],
                ["Average time inside, last three minutes", t.sample ? clockText(t.W) : "\u2013"]],
    });
  },
};

// ----- a party
const DES_LOG_COLOR = state => DES_STAGE[state]?.queue ? WAIT_COLOR : DES_STAGE[state]?.kind === "delay" ? OWN_COLOR : WORK_COLOR;
function desPartyInfo(id) {
  let info = desPartyInfos.get(id);
  if (info) return info;
  const first = desEngine.parties.get(id), live = () => desEngine.parties.get(id);
  info = {
    nodes: [], kind: "Party", party: first, name: `Party ${first.number}: ${first.size === 1 ? "1 guest" : first.size + " guests"}`,
    what: "A customer party: the entity that flows through the system, from arriving to departing.",
    purpose: "To be seated, order, be served, eat and leave, without waiting longer than we think is reasonable.",
    why: "A party that leaves happy is what the restaurant produces. Every resource and queue here exists to move parties along.",
    metrics: () => {
      const party = live() || first, over = !live(), t = party.timestamps;   // after the visit the party is no longer in the engine, but what it went through is still on it
      const now = over ? t.departed : desEngine.currentTime, targets = DES_CONFIG.targets, waits = desEngine.waits;
      const rows = [
        { label: "For a table", value: party.queued.host ? now - party.queued.host.since : party.metrics.tableWaitDuration, average: desMean(waits.table), target: targets.table },
        { label: "To order", value: party.queued.order ? now - party.queued.order.since : party.metrics.orderWaitDuration, average: desMean(waits.order), target: targets.order },
        { label: "For the food", value: t.orderPlaced === undefined ? 0 : (t.foodServed ?? now) - t.orderPlaced, average: desMean(waits.food), target: targets.food },
      ];
      const met = rows.filter(row => row.value <= row.target).length, stage = DES_STAGE[party.state];
      const parts = party.state === "COOKING" ? ` (${Object.entries(party.parts).map(([kind, state]) => `${DES_RES[kind].one.toLowerCase()}: ${state}`).join(", ")})` : "";
      const ended = party.gaveUp === "order" ? "left without eating: nobody came to take the order" : party.gaveUp === "food" ? "left without eating: the food took too long" : "dined and left";
      return {
        objective: "Every wait within its target, so the party leaves happy.",
        measure: "Time waiting for a table, time waiting for a waiter to take the order, and time from the order being placed to the food being served.",
        value: clockText(now - t.arrival), unit: over ? "in the building; the visit is over" : "in the building so far",
        verdict: over ? (party.happy ? ["Happy visit", "good"] : ["Not a happy visit", "bad"]) : met === rows.length ? ["Happy so far", "good"] : ["Not a happy visit", "bad"],
        notes: [over ? `Visit over: ${ended} at ${clockText(t.departed)}.` : `Now: ${stage.queue ? DES_QUEUE[stage.queue].name : stage.name}${parts}.`],
        chartTitle: "Waits", timelineTitle: "Visit on the clock",
        chart: rowChart(rows),
        caption: "Bar: this party. White mark: average so far. Orange mark: target.",
        timeline: partsTimeline(t.arrival, party.log.slice(0, over ? -1 : undefined).map(([state, since], i) => [(party.log[i + 1]?.[1] ?? now) - since, DES_LOG_COLOR(state)])),
        timelineCaption: "On the clock: this party's visit. Orange: in a queue. Green: the guests' own time. Grey: staff working for them. " + NOW_NOTE,
        numbers: [["Arrived at", clockText(t.arrival)],
                  ...(over ? [["Left at", clockText(t.departed)]] : []),
                  ["Table", over ? "Given back." : party.table === null ? "None yet." : `Table ${party.table + 1}, which seats ${DES_CONFIG.tables[party.table]}.`],
                  ["Holds now", Object.keys(party.held).map(key => DES_RES[key.split(":")[0]].one).join(", ") || "Nothing."],
                  ...(party.parts ? Object.entries(party.parts).map(([kind, state]) => [`Part of the order: ${DES_RES[kind].one.toLowerCase()}`, state[0].toUpperCase() + state.slice(1) + "."]) : []),
                  ["Ordered", party.order ? party.order.lines : "Nothing yet."]],
      };
    },
  };
  desPartyInfos.set(id, info);
  return info;
}
