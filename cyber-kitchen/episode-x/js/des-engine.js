// ---------- DES engine ----------
// The sole source of operational truth for the DES view. A clock, a priority queue of events (a
// min-heap), resource pools, FIFO queues and the state machine of every party. It has no DOM, no
// coordinates and no animation frame: it can be stepped one event at a time, run to a given time, or
// run headless. Renderers subscribe to its events and read snapshots; they never write.
//
// It started from the specification's three pools (tables, waiters, stoves) and was brought up to the
// whole restaurant: tables of different sizes, cooks, the pizza oven and the coffee machine, an order
// that is planned and then made as parts in parallel, and parties turned away when the door queue is full.
// Every time is in simulated seconds, to match the page's clock. Every number is invented.
const DES_CONFIG = {
  seed: 1,
  tables: [6, 6, 4, 2, 4, 6, 6, 4, 6, 4, 6, 2],   // seats of each table, in the order they stand on the floor
  capacity: { waiters: 2, cooks: 2, stoves: 2, oven: 1, coffee: 1 },
  hostQueueMax: 3,                                              // a party that finds this many waiting goes away
  interarrival: { dist: "uniform", min: 5, max: 10 },
  partySize: [[1, 1], [2, 4], [3, 2], [4, 4], [5, 1.5], [6, 2]],   // [guests, weight]
  pizzaChance: 0.3, coffeeChance: 0.4,                          // per guest
  dishes: {
    stoves: ["Grilled salmon", "Steak frites", "Mushroom risotto", "Chicken parmesan", "Pasta carbonara", "Caesar salad"],
    oven: ["Margherita pizza", "Pepperoni pizza", "Four cheese pizza"],
  },
  menu: { dist: "uniform", min: 5, max: 9 },                    // delay: reading the menu
  order: { dist: "triangular", min: 4, mode: 6, max: 9 },       // a waiter takes the order
  plan: 2,                                                      // a cook plans the order
  parts: {                                                      // each part needs a cook and one unit of the equipment
    stoves: { base: 4, perItem: 1.3 }, oven: { base: 4, perItem: 1.0 }, coffee: { base: 1, perItem: 0.5 },
  },
  plate: 2,                                                     // a cook plates the finished order
  run: { dist: "triangular", min: 4, mode: 6, max: 9 },         // a waiter runs the food
  dine: { dist: "uniform", min: 14, max: 22 },                  // delay: eating and billing
  // patience: a seated party that waits longer than this walks out without eating
  orderPatience: { dist: "uniform", min: 45, max: 90 },         // for a waiter to come and take the order
  foodPatience: { dist: "uniform", min: 90, max: 150 },         // for the food, counted from the order being placed
  // what we think is reasonable: waits a visit should stay within, queue waits, and shares of time in use
  targets: { table: 30, order: 15, food: 60, happy: 0.8 },
  queueTargets: { host: 30, order: 15, plan: 15, stoves: 10, oven: 10, coffee: 10, plate: 10, run: 10 },
  useTargets: { tables: { atLeast: 0.7 }, waiters: { atMost: 0.85 }, cooks: { atMost: 0.85 }, stoves: { atMost: 0.8 }, oven: { atMost: 0.8 }, coffee: { atMost: 0.8 } },
  arrivalsUntil: Infinity,                                      // close the door at this time, to let the system drain
};
const DES_KEEP = 40, DES_WINDOW = 180;
const DES_OUT = 0;   // a unit that is out of service; like null and false it is falsy, so "is it in use?" stays a plain truth test
const DES_STAFF = ["waiters", "cooks"], DES_STAFF_MAX = 6;   // pools whose size can be changed while the engine runs
// what a party in each queue is waiting for; a kitchen part needs its cook and its equipment at the same moment
const DES_QUEUE_NEEDS = { host: ["tables"], order: ["waiters"], plan: ["cooks"], stoves: ["cooks", "stoves"], oven: ["cooks", "oven"], coffee: ["cooks", "coffee"], plate: ["cooks"], run: ["waiters"] };
const DES_PART_EVENTS = { stoves: ["SEIZE_STOVE", "COOK_COMPLETE"], oven: ["SEIZE_OVEN", "BAKE_COMPLETE"], coffee: ["SEIZE_COFFEE", "COFFEE_COMPLETE"] };

class DESEngine {
  constructor(config = DES_CONFIG) {
    this.config = config;
    this.currentTime = 0;
    this.heap = [];           // the priority event queue, ordered by (timestamp, sequence)
    this.sequence = 0;
    this.eventsProcessed = 0;
    this.subscribers = [];
    this.streams = {};
    this.resources = {};      // pools; a unit is null when free, else { party, task, since, until }
    for (const [id, capacity] of [["tables", config.tables.length], ...Object.entries(config.capacity)]) {
      // a unit is null when free, an object when seized, false when it is not on shift (staff pools have spare places),
      // and DES_OUT when it is out of service: a person off sick, a machine broken down, a table out of use
      const places = DES_STAFF.includes(id) ? DES_STAFF_MAX : capacity;
      this.resources[id] = { capacity, allocated: 0, units: Array.from({ length: places }, (_, i) => i < capacity ? null : false), busyArea: 0, capArea: 0, since: 0, leaving: 0, goingOut: new Set() };
    }
    // FIFO buffers of party ids, each with what it has measured
    this.queues = {}; this.queueStats = {};
    this.blocked = {}; this.blockedSince = 0;   // party-seconds of waiting in each queue, by what was missing
    for (const id in config.queueTargets) { this.queues[id] = []; this.queueStats[id] = this.stats(); this.blocked[id] = {}; }
    this.parties = new Map();   // active parties by id
    this.stateStats = {};       // time spent in each state
    this.partStats = {};        // time each kitchen part takes, once a cook and its equipment have it
    for (const kind in config.parts) this.partStats[kind] = this.stats();
    this.arrived = 0; this.departed = 0; this.balked = 0; this.happy = 0; this.abandoned = 0; this.abandonedFor = { order: 0, food: 0 };
    this.ghosts = new Map();    // parties that walked out while a cook was still working on their order: the work in hand is finished, then dropped
    // telemetry: what the HUD is computed from
    this.arrivalLog = []; this.departureLog = []; this.wipLog = [[0, 0]];
    this.waits = { table: this.stats(), order: this.stats(), food: this.stats() };
    this.cycleTimes = this.stats();
    this.scheduleEvent(this.draw("arrival", config.interarrival), "PARTY_ARRIVED", "P1");
  }

  // ----- the dispatcher
  subscribe(fn) { this.subscribers.push(fn); }
  scheduleEvent(timestamp, type, entityId, resourceId, metadata) {
    const event = { id: "E" + ++this.sequence, seq: this.sequence, timestamp, type, entityId, resourceId, metadata };
    const h = this.heap;
    h.push(event);
    for (let i = h.length - 1; i > 0;) {
      const parent = (i - 1) >> 1;
      if (!this.before(h[i], h[parent])) break;
      [h[i], h[parent]] = [h[parent], h[i]];
      i = parent;
    }
  }
  before(a, b) { return a.timestamp !== b.timestamp ? a.timestamp < b.timestamp : a.seq < b.seq; }
  pop() {
    const h = this.heap, top = h[0], last = h.pop();
    if (h.length) {
      h[0] = last;
      for (let i = 0; ;) {
        const l = 2 * i + 1, r = l + 1;
        let m = i;
        if (l < h.length && this.before(h[l], h[m])) m = l;
        if (r < h.length && this.before(h[r], h[m])) m = r;
        if (m === i) break;
        [h[i], h[m]] = [h[m], h[i]];
        i = m;
      }
    }
    return top;
  }
  // Process the next event: advance the clock to it, apply its state transition, tell the subscribers.
  step() {
    if (!this.heap.length) return null;
    const event = this.pop();
    this.accrueBlocked(event.timestamp);
    this.currentTime = event.timestamp;
    this.processEvent(event);
    this.eventsProcessed++;
    for (const fn of this.subscribers) fn(event, this);
    return event;
  }
  // Process every event up to a time. How the caller slices time does not change the event sequence.
  runUntil(time) {
    while (this.heap.length && this.heap[0].timestamp <= time) this.step();
    if (time > this.currentTime) this.currentTime = time;
  }
  // Run with no renderer at all until nothing is left to do (needs arrivalsUntil to be finite).
  runToEnd() { while (this.step()); }

  // ----- randomness: one named, seeded stream per kind of draw
  rng(name) { return this.streams[name] ??= new Rng(streamSeed(this.config.seed, "des:" + name)); }
  draw(name, spec) { return this.rng(name).draw(spec); }

  // ----- measuring
  stats() { return { done: 0, total: 0, history: [], stays: [] }; }
  record(stats, seconds) {
    stats.done++; stats.total += seconds;
    stats.history.push(seconds);
    if (stats.history.length > DES_KEEP) stats.history.shift();
  }
  stay(stats) {
    const list = stats.stays;
    while (list.length && list[0].end !== null && list[0].end < this.currentTime - DES_WINDOW) list.shift();
    const one = { start: this.currentTime, end: null };
    list.push(one);
    return one;
  }

  // What the parties in a queue are missing right now: the pools it needs that have no unit free.
  // (At the door a table may be free and still not fit; then the tables are what is missing.)
  missing(id) {
    const short = DES_QUEUE_NEEDS[id].filter(pool => !this.available(pool));
    return short.length ? short : DES_QUEUE_NEEDS[id].slice(0, 1);
  }
  // Nothing changes between two events, so the waiting since the last one is charged to what was missing then.
  accrueBlocked(until) {
    const seconds = until - this.blockedSince;
    this.blockedSince = until;
    if (seconds <= 0) return;
    for (const id in this.queues) {
      if (!this.queues[id].length) continue;
      const cause = this.missing(id).join("+");
      this.blocked[id][cause] = (this.blocked[id][cause] || 0) + this.queues[id].length * seconds;
    }
  }

  // ----- resources
  available(id) { return this.resources[id].allocated < this.resources[id].capacity; }
  accrue(resource) {
    resource.busyArea += resource.allocated * (this.currentTime - resource.since);
    resource.capArea += resource.capacity * (this.currentTime - resource.since);
    resource.since = this.currentTime;
  }
  seize(id, party, task, unit) {
    const resource = this.resources[id];
    if (resource.allocated >= resource.capacity) throw new Error(`${id}: seized beyond capacity`);
    unit ??= resource.units.indexOf(null);
    if (resource.units[unit] !== null) throw new Error(`${id}: unit ${unit} seized while taken`);
    this.accrue(resource);
    resource.allocated++;
    resource.units[unit] = { party: party.id, task, since: this.currentTime, until: null };
    party.held[id + ":" + task] = unit;
    return unit;
  }
  release(id, party, task) {
    const resource = this.resources[id], unit = party.held[id + ":" + task];
    if (unit === undefined || resource.units[unit]?.party !== party.id) throw new Error(`${id}: ${party.id} released a unit it does not hold`);
    this.accrue(resource);
    resource.allocated--;
    resource.units[unit] = null;
    if (resource.goingOut.delete(unit)) { resource.capacity--; resource.units[unit] = DES_OUT; }   // went sick or broke down during the task: out now it is done
    else if (resource.leaving) { resource.leaving--; resource.capacity--; resource.units[unit] = false; }   // was asked to go: leaves now the task is done
    delete party.held[id + ":" + task];
  }
  // Take one unit out of service, or bring it back: a person goes off sick, a machine breaks down, a table
  // is taken out of use. A free unit goes at once; a busy one finishes the task it is on first. It keeps
  // its place, so it can be seen and brought back.
  setOut(id, unit, out) {
    const resource = this.resources[id], state = resource.units[unit];
    this.accrue(resource);
    if (out) {
      if (state === null) { resource.units[unit] = DES_OUT; resource.capacity--; }
      else if (state && !resource.goingOut.has(unit)) resource.goingOut.add(unit);
      else return false;
    } else if (resource.goingOut.delete(unit)) { /* had not gone yet: stays */ }
    else if (state === DES_OUT) { resource.units[unit] = null; resource.capacity++; }
    else return false;
    const event = { id: "E" + ++this.sequence, seq: this.sequence, timestamp: this.currentTime, type: out ? "UNIT_OUT" : "UNIT_BACK", entityId: "-", resourceId: `${id} ${unit + 1}` };
    for (const fn of this.subscribers) fn(event, this);
    this.dispatchTables();
    this.dispatchWaiters();
    this.dispatchKitchen();
    return true;
  }
  // Change how many waiters or cooks are on shift, by one, while the engine runs. One more starts at
  // once. One fewer: a free one leaves at once; if all are busy, the next to finish a task leaves.
  changeCapacity(id, by) {
    const resource = this.resources[id];
    this.accrue(resource);
    if (by > 0) {
      if (resource.leaving) resource.leaving--;   // someone was about to go: they stay
      else {
        const place = resource.units.indexOf(false);
        if (place < 0) return false;
        resource.units[place] = null; resource.capacity++;
      }
    } else {
      if (resource.capacity - resource.leaving <= 0) return false;
      const free = resource.units.lastIndexOf(null);
      if (free < 0) resource.leaving++;
      else { resource.units[free] = false; resource.capacity--; }
    }
    const event = { id: "E" + ++this.sequence, seq: this.sequence, timestamp: this.currentTime, type: by > 0 ? "CAPACITY_UP" : "CAPACITY_DOWN", entityId: "-", resourceId: id };
    for (const fn of this.subscribers) fn(event, this);
    this.dispatchWaiters();
    this.dispatchKitchen();
    return true;
  }
  // a timed task or delay: the party's event fires when it is over; the units it holds know when too
  after(party, seconds, type, resourceId, metadata) {
    const until = this.currentTime + seconds;
    party.until = until;
    this.scheduleEvent(until, type, party.id, resourceId, metadata);
    return until;
  }

  // ----- queues: every request for a resource goes through one, even if it does not have to wait
  enqueue(id, party) {
    this.queues[id].push(party.id);
    party.queued[id] = { since: this.currentTime, stay: this.stay(this.queueStats[id]) };
  }
  dequeue(id, party) {
    const queue = this.queues[id], entry = party.queued[id], waited = this.currentTime - entry.since;
    queue.splice(queue.indexOf(party.id), 1);
    entry.stay.end = this.currentTime;
    delete party.queued[id];
    this.record(this.queueStats[id], waited);
    return waited;
  }
  // The smallest free table that seats the party, or -1.
  tableFor(party) {
    let best = -1;
    this.resources.tables.units.forEach((unit, i) => {
      const seats = this.config.tables[i];
      if (unit === null && seats >= party.size && (best < 0 || seats < this.config.tables[best])) best = i;
    });
    return best;
  }
  // Seat everyone in the host queue who fits a free table, oldest first.
  dispatchTables() {
    for (const id of [...this.queues.host]) {
      const party = this.parties.get(id), table = this.tableFor(party);
      if (table < 0) continue;
      this.record(this.waits.table, party.metrics.tableWaitDuration = this.dequeue("host", party));
      party.table = this.seize("tables", party, "table", table);
      this.scheduleEvent(this.currentTime, "SEIZE_TABLE", party.id, "tables");
    }
  }
  // A free waiter takes the next job: running food first (it is getting cold), then taking an order.
  dispatchWaiters() {
    while (this.available("waiters") && (this.queues.run.length || this.queues.order.length)) {
      const deliver = this.queues.run.length > 0, party = this.parties.get((deliver ? this.queues.run : this.queues.order)[0]);
      const waited = this.dequeue(deliver ? "run" : "order", party);
      if (!deliver) this.record(this.waits.order, party.metrics.orderWaitDuration = waited);
      this.seize("waiters", party, deliver ? "deliver" : "order");
      this.scheduleEvent(this.currentTime, deliver ? "SEIZE_WAITER_DELIVER" : "SEIZE_WAITER_ORDER", party.id, "waiters");
    }
  }
  // A free cook takes the next kitchen job: plating first, then the parts of orders already planned,
  // then planning a new order. A part starts only when a cook and its equipment are both free, and
  // seizes both at once, so nobody holds one while waiting for the other.
  dispatchKitchen() {
    for (const job of ["plate", "stoves", "oven", "coffee", "plan"]) {
      const equipment = this.config.parts[job] ? job : null;
      while (this.queues[job].length && this.available("cooks") && (!equipment || this.available(equipment))) {
        const party = this.parties.get(this.queues[job][0]);
        this.dequeue(job, party);
        this.seize("cooks", party, job);
        if (equipment) this.seize(equipment, party, job);
        this.scheduleEvent(this.currentTime, equipment ? DES_PART_EVENTS[job][0] : job === "plan" ? "SEIZE_COOK_PLAN" : "SEIZE_COOK_PLATE", party.id, equipment || "cooks");
      }
    }
  }

  // ----- the entity state machine
  setState(party, state) {
    if (party.state) {
      this.record(this.stateStats[party.state] ??= this.stats(), this.currentTime - party.since);
      party.stateStay.end = this.currentTime;
    }
    party.state = state; party.since = this.currentTime; party.until = null;
    party.log.push([state, this.currentTime]);
    party.stateStay = this.stay(this.stateStats[state] ??= this.stats());
  }
  wip(change) {
    const log = this.wipLog;
    log.push([this.currentTime, log.at(-1)[1] + change]);
    while (log.length > 2 && log[1][0] < this.currentTime - 600) log.shift();
  }
  // time a task takes, and tell the units doing it when it ends
  task(party, seconds, type, pools, task, metadata) {
    const until = this.after(party, seconds, type, pools[0], metadata);
    for (const id of pools) this.resources[id].units[party.held[id + ":" + task]].until = until;
  }
  writeOrder(party) {
    const config = this.config, rng = this.rng("order"), counts = new Map();
    const add = item => counts.set(item, (counts.get(item) || 0) + 1);
    party.order = { stoves: 0, oven: 0, coffee: 0 };
    for (let i = 0; i < party.size; i++) {
      const kind = rng.next() < config.pizzaChance ? "oven" : "stoves";
      add(config.dishes[kind][Math.floor(rng.next() * config.dishes[kind].length)]);
      party.order[kind]++;
      if (rng.next() < config.coffeeChance) party.order.coffee++;
    }
    if (party.order.coffee) counts.set("Coffee", party.order.coffee);
    party.order.lines = [...counts].map(([item, n]) => `${n} × ${item}`).join("\n");
  }
  processEvent(event) {
    const config = this.config, now = this.currentTime;
    let party = this.parties.get(event.entityId);
    if (!party && event.type !== "PARTY_ARRIVED") {   // the party is gone: only work still in hand for it matters
      const ghost = this.ghosts.get(event.entityId);
      if (ghost) this.processGhost(event, ghost);
      return;
    }
    switch (event.type) {
      case "PARTY_ARRIVED": {
        let pick = this.rng("size").next() * config.partySize.reduce((sum, [, weight]) => sum + weight, 0), size = 2;
        for (const [guests, weight] of config.partySize) { if ((pick -= weight) <= 0) { size = guests; break; } }
        party = { id: event.entityId, number: Number(event.entityId.slice(1)), size, state: null, since: now, until: null, table: null, held: {}, queued: {},
                  order: null, parts: null, log: [], timestamps: { arrival: now },
                  metrics: { tableWaitDuration: 0, orderWaitDuration: 0, kitchenWaitDuration: 0, totalCycleTime: 0 } };
        const next = now + this.draw("arrival", config.interarrival);
        if (next <= config.arrivalsUntil) this.scheduleEvent(next, "PARTY_ARRIVED", "P" + (party.number + 1));
        if (this.tableFor(party) < 0 && this.queues.host.length >= config.hostQueueMax) {
          this.balked++;
          this.scheduleEvent(now, "PARTY_BALKED", party.id, undefined, { size });
          break;
        }
        this.arrived++;
        this.parties.set(party.id, party);
        this.arrivalLog.push(now);
        this.wip(1);
        this.setState(party, "WAITING_FOR_TABLE");
        this.enqueue("host", party);
        this.dispatchTables();
        break;
      }
      // (PARTY_BALKED needs nothing: the party never came in, so the event stops at the check above. It is there for the renderers and the count.)
      case "SEIZE_TABLE":
        party.timestamps.seated = now;
        this.setState(party, "READING_MENU");
        this.after(party, this.draw("menu", config.menu), "MENU_READ_COMPLETE");
        break;
      case "MENU_READ_COMPLETE":
        this.setState(party, "WAITING_FOR_WAITER_ORDER");
        this.scheduleEvent(now + this.draw("orderPatience", config.orderPatience), "ORDER_PATIENCE_OUT", party.id);
        this.enqueue("order", party);
        this.dispatchWaiters();
        break;
      case "SEIZE_WAITER_ORDER":
        this.setState(party, "ORDERING");
        this.task(party, this.draw("order", config.order), "RELEASE_WAITER_ORDER", ["waiters"], "order");
        break;
      case "RELEASE_WAITER_ORDER":
        this.release("waiters", party, "order");
        this.writeOrder(party);
        party.timestamps.orderPlaced = now;
        this.setState(party, "WAITING_FOR_COOK");
        this.scheduleEvent(now + this.draw("foodPatience", config.foodPatience), "FOOD_PATIENCE_OUT", party.id);
        this.enqueue("plan", party);   // the ticket rail
        this.dispatchKitchen();
        this.dispatchWaiters();
        break;
      case "ORDER_PATIENCE_OUT":
        // still nobody to take the order, and no waiter on the way: the party walks out
        if (party.queued.order) this.abandon(party, "order");
        break;
      case "FOOD_PATIENCE_OUT":
        // still no food, and none on its way to the table: the party walks out
        if (party.timestamps.foodServed === undefined && party.held["waiters:deliver"] === undefined) this.abandon(party, "food");
        break;
      case "SEIZE_COOK_PLAN":
        this.setState(party, "PLANNING");
        this.task(party, config.plan, "PLAN_COMPLETE", ["cooks"], "plan");
        break;
      case "PLAN_COMPLETE":
        this.release("cooks", party, "plan");
        party.timestamps.cookStarted = now;
        this.setState(party, "COOKING");
        party.parts = {};   // one part per kind of equipment the order needs; they are made in parallel
        for (const kind in config.parts) if (party.order[kind]) { party.parts[kind] = "queued"; this.enqueue(kind, party); }
        this.dispatchKitchen();
        break;
      case "SEIZE_STOVE": case "SEIZE_OVEN": case "SEIZE_COFFEE": {
        const kind = event.resourceId, spec = config.parts[kind];
        party.parts[kind] = "cooking";
        (party.partStays ||= {})[kind] = this.stay(this.partStats[kind]);
        this.task(party, spec.base + spec.perItem * party.order[kind], DES_PART_EVENTS[kind][1], [kind, "cooks"], kind);
        break;
      }
      case "COOK_COMPLETE": case "BAKE_COMPLETE": case "COFFEE_COMPLETE": {
        const kind = event.resourceId;
        this.release(kind, party, kind);
        this.release("cooks", party, kind);
        party.parts[kind] = "done";
        this.record(this.partStats[kind], now - party.partStays[kind].start);
        party.partStays[kind].end = now;
        if (Object.values(party.parts).every(state => state === "done")) {
          this.setState(party, "WAITING_FOR_PLATING");
          this.enqueue("plate", party);
        }
        this.dispatchKitchen();
        break;
      }
      case "SEIZE_COOK_PLATE":
        this.setState(party, "PLATING");
        this.task(party, config.plate, "PLATE_COMPLETE", ["cooks"], "plate");
        break;
      case "PLATE_COMPLETE":
        this.release("cooks", party, "plate");
        party.timestamps.foodReady = now;
        this.setState(party, "WAITING_FOR_WAITER_DELIVER");
        this.enqueue("run", party);   // the pass
        this.dispatchWaiters();
        this.dispatchKitchen();
        break;
      case "SEIZE_WAITER_DELIVER":
        this.setState(party, "FOOD_RUNNING");
        this.task(party, this.draw("run", config.run), "RELEASE_WAITER_DELIVER", ["waiters"], "deliver");
        break;
      case "RELEASE_WAITER_DELIVER":
        this.release("waiters", party, "deliver");
        party.timestamps.foodServed = now;
        this.record(this.waits.food, party.metrics.kitchenWaitDuration = now - party.timestamps.orderPlaced);
        this.setState(party, "EATING_AND_BILLING");
        this.after(party, this.draw("dine", config.dine), "DINING_COMPLETE");
        this.dispatchWaiters();
        break;
      case "DINING_COMPLETE":
        this.scheduleEvent(now, "RELEASE_TABLE", party.id, "tables");
        break;
      case "RELEASE_TABLE":
        this.release("tables", party, "table"); party.table = null;
        this.scheduleEvent(now, "PARTY_DEPARTED", party.id);
        this.dispatchTables();   // the table goes straight to whoever in the host queue it fits
        break;
      case "PARTY_DEPARTED": {
        const m = party.metrics, targets = config.targets;
        party.timestamps.departed = now;
        m.totalCycleTime = now - party.timestamps.arrival;
        this.record(this.cycleTimes, m.totalCycleTime);
        this.setState(party, "DEPARTED");
        party.stateStay.end = now;
        party.happy = m.tableWaitDuration <= targets.table && m.orderWaitDuration <= targets.order && m.kitchenWaitDuration <= targets.food;
        if (party.happy) this.happy++;
        this.parties.delete(party.id);
        this.departed++;
        this.departureLog.push([now, m.totalCycleTime]);
        this.wip(-1);
        break;
      }
    }
  }

  // A party gives up waiting for its food. It leaves every queue it stands in and gives its table back.
  // Whatever a cook is doing for it at that moment is finished and then thrown away.
  abandon(party, reason) {
    const now = this.currentTime;
    party.gaveUp = reason; this.abandonedFor[reason]++;
    for (const id in party.queued) this.dequeue(id, party);
    this.release("tables", party, "table"); party.table = null;
    party.timestamps.departed = now;
    party.metrics.totalCycleTime = now - party.timestamps.arrival;
    this.setState(party, "ABANDONED");
    party.stateStay.end = now;
    this.parties.delete(party.id);
    this.abandoned++;
    this.departureLog.push([now, party.metrics.totalCycleTime]);
    this.wip(-1);
    if (Object.keys(party.held).length) this.ghosts.set(party.id, party);
    this.scheduleEvent(now, "PARTY_ABANDONED", party.id, undefined, { reason });
    this.dispatchTables();
    this.dispatchKitchen();
    this.dispatchWaiters();
  }
  // Events for a party that has walked out: release what the kitchen was using for it.
  processGhost(event, ghost) {
    const task = { SEIZE_COOK_PLAN: "plan", PLAN_COMPLETE: "plan", SEIZE_COOK_PLATE: "plate", PLATE_COMPLETE: "plate" }[event.type]
      || (this.config.parts[event.resourceId] ? event.resourceId : null);
    if (!task || ghost.held["cooks:" + task] === undefined) return;
    if (this.config.parts[task]) this.release(task, ghost, task);
    this.release("cooks", ghost, task);
    if (!Object.keys(ghost.held).length) this.ghosts.delete(ghost.id);
    this.dispatchKitchen();
  }

  // ----- what renderers read: a snapshot of the state, and the telemetry
  snapshot() {
    const resources = {};
    for (const id in this.resources) {
      const r = this.resources[id];
      resources[id] = { capacity: r.capacity, allocated: r.allocated, units: r.units.map(unit => unit && { ...unit }),
                        leaving: r.leaving, goingOut: [...r.goingOut],
                        average: (() => { const cap = r.capArea + r.capacity * (this.currentTime - r.since); return cap ? (r.busyArea + r.allocated * (this.currentTime - r.since)) / cap : 0; })() };
    }
    const queues = {};
    for (const id in this.queues) queues[id] = [...this.queues[id]];
    return {
      time: this.currentTime, resources, queues,
      parties: new Map([...this.parties].map(([id, party]) => [id, { ...party }])),
      arrived: this.arrived, departed: this.departed, balked: this.balked, happy: this.happy, abandoned: this.abandoned, abandonedFor: { ...this.abandonedFor },
      eventsProcessed: this.eventsProcessed, pending: this.heap.length,
    };
  }
  // Rolling figures over the last `window` seconds, for the operations HUD and Little's Law (L = lambda x W).
  telemetry(window = DES_WINDOW) {
    const now = this.currentTime, from = Math.max(0, now - window), span = now - from;
    while (this.arrivalLog.length && this.arrivalLog[0] < now - 600) this.arrivalLog.shift();
    while (this.departureLog.length && this.departureLog[0][0] < now - 600) this.departureLog.shift();
    const arrivals = this.arrivalLog.filter(t => t > from).length, cycles = this.departureLog.filter(([t]) => t > from).map(([, cycle]) => cycle);
    let area = 0;   // time-average of the work in progress over the window
    this.wipLog.forEach(([t, level], i) => {
      const end = this.wipLog[i + 1]?.[0] ?? now;
      if (end > from) area += level * (end - Math.max(t, from));
    });
    const lambda = span ? arrivals / span : 0, W = cycles.length ? cycles.reduce((sum, c) => sum + c, 0) / cycles.length : 0;
    return { L: this.parties.size, averageL: span ? area / span : 0, lambda, W, predictedL: lambda * W, sample: cycles.length };
  }
}
