// ---------- the work as steps ----------
// The simulation seen as work: a party and its order (guests, then a ticket, then food) go through
// these steps. A waiting step is a queue. Each step keeps count of how long parties spend in it.
const KIND_WHAT = {
  wait: "A waiting step. Nothing is being done for the party here: it is held up until a resource is free.",
  work: "A working step. Something is being done for the party here.",
  move: "A walking step. The party or its order is being moved from one place to another.",
};
const FORM_TEXT = {
  guests: "A party of guests.",
  ticket: "The party's order, as a paper ticket.",
  plates: "The party's order, as plates of food.",
};
const STEPS = [
  { key: "door", name: "Queue for a table", kind: "wait", form: "guests",
    uses: "Needs a free table that fits the party.",
    purpose: "A party that has arrived waits outside until a table that fits it is free. At most three parties wait; later arrivals are turned away.",
    why: "Time here is lost business. It grows when tables turn over slowly, so a delay in any later step ends up here." },
  { key: "walkIn", name: "Walk to the table", kind: "move", form: "guests",
    uses: "Holds a table.",
    purpose: "The party walks from the door to its table.",
    why: "Short, and set by the layout of the room." },
  { key: "menu", name: "Read the menu", kind: "work", form: "guests",
    uses: "Holds a table.",
    purpose: "The guests read the menu and decide what to order.",
    why: "The guests set this pace, not the staff." },
  { key: "wantOrder", name: "Wait to order", kind: "wait", form: "guests",
    uses: "Holds a table. Needs a waiter.",
    purpose: "The guests have decided and wait for a waiter to come. This includes the waiter's walk to the table.",
    why: "Pure waiting for a waiter. It grows when the waiters are busy carrying tickets and plates." },
  { key: "ordering", name: "Order", kind: "work", form: "guests",
    uses: "Holds a table and a waiter.",
    purpose: "A waiter writes down the order at the table.",
    why: "Quick, but it needs a waiter standing at the table." },
  { key: "toRail", name: "Ticket to the rail", kind: "move", form: "ticket",
    uses: "Holds a table and a waiter.",
    purpose: "The waiter carries the ticket to the order rail and hangs it there.",
    why: "Walking time for a waiter. A shorter path, or orders sent to the kitchen without walking, would remove it." },
  { key: "rail", name: "Ticket on the rail", kind: "wait", form: "ticket",
    uses: "Holds a table. Needs a cook.",
    purpose: "The ticket hangs on the rail until a cook is free to take it. This includes the cook's walk to the rail.",
    why: "Pure waiting for a cook. Tickets piling up here mean the kitchen is behind." },
  { key: "cooking", name: "Cook", kind: "work", form: "ticket",
    uses: "Holds a table, a cook, and the stove, pizza oven or coffee machine the order needs.",
    purpose: "One cook prepares the whole order: stove dishes, then pizza, then coffee, and carries the plates to the pass. This includes any wait for the shared pizza oven or coffee machine.",
    why: "The main working step in the kitchen. One cook does a whole order alone, so two cooks means at most two orders at once." },
  { key: "pass", name: "Plates on the pass", kind: "wait", form: "plates",
    uses: "Holds a table. Needs a waiter.",
    purpose: "Finished plates sit on the pass until a waiter collects them. This includes the waiter's walk to the pass.",
    why: "Food gets cold here. It grows when the waiters are busy." },
  { key: "deliver", name: "Plates to the table", kind: "move", form: "plates",
    uses: "Holds a table and a waiter.",
    purpose: "A waiter carries the plates to the table and serves them.",
    why: "Walking time for a waiter, set by how far the table is from the pass." },
  { key: "eating", name: "Eat", kind: "work", form: "guests",
    uses: "Holds a table.",
    purpose: "The guests eat their meal.",
    why: "What the guests came for, and the longest step. The table is held the whole time." },
  { key: "leaving", name: "Leave", kind: "move", form: "guests",
    uses: "Nothing. The table is already free for the next party.",
    purpose: "The party walks out through the front door.",
    why: "The end of the flow. Nothing here holds anyone else up." },
];
const FLOW = Object.fromEntries(STEPS.map(step => [step.key, step]));
STEPS.forEach(step => {
  step.done = 0; step.total = 0; step.history = []; step.stays = [];
  step.info = {
    kind: "Flow step", name: step.name,
    what: KIND_WHAT[step.kind], purpose: step.purpose, why: step.why,
    extra: [
      ["What flows through", FORM_TEXT[step.form]],
      ["Resources", step.uses],
      ["Time spent here", () => step.done ? `${clockText(step.total / step.done)} on average, over ${step.done} so far.` : "No party has finished this step yet."],
    ],
  };
});

// "Wait for food" in the service view covers all the kitchen steps at once, so it has a card of its own.
const WAIT_FOR_FOOD = {
  kind: "Flow step", name: "Wait for food", subject: { key: "waitForFood" },
  what: KIND_WHAT.wait,
  purpose: "The guests have ordered and wait at their table while the ticket goes to the kitchen, the food is cooked, and a waiter brings it.",
  why: "The longest wait the guests have. Everything the kitchen and the waiters do with an order shows up here as time at the table.",
  extra: [["What flows through", FORM_TEXT.guests], ["Resources", "Holds a table. Needs, in turn, a waiter, a cook with the equipment, and a waiter again."]],
};

// Which step a party is in, read from the state the simulation already keeps.
const PARTY_STEP = { queue: "door", arriving: "walkIn", leaving: "leaving" };
const TABLE_STEP = { reserved: "walkIn", reading: "menu", ready: "wantOrder", ordering: "ordering", waiting: "ordering", eating: "eating" };
const TICKET_STEP = { carried: "toRail", rail: "rail", cooking: "cooking", pass: "pass", delivering: "deliver", done: "eating" };
// While the order is in the kitchen the guests are not in any kitchen step: they wait at their table.
const KITCHEN_STEPS = ["toRail", "rail", "cooking", "pass", "deliver"];
function stepOf(party) {
  if (party.state !== "seated") return PARTY_STEP[party.state];
  return party.ticket ? TICKET_STEP[party.ticket.stage] : TABLE_STEP[party.table.status];
}
