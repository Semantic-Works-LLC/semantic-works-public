// What guests can order. Each dish belongs to the station that makes it.
const MENU = {
  stove: ["Grilled salmon", "Steak frites", "Mushroom risotto", "Chicken parmesan", "Pasta carbonara", "Caesar salad"],
  oven: ["Margherita pizza", "Pepperoni pizza", "Four cheese pizza"],
};
const PIZZA_CHANCE = 0.3, COFFEE_CHANCE = 0.4;
const tickets = [];   // every order that has been taken and not yet delivered
const delivered = []; // the most recent delivered orders, newest first
let ticketCount = 0;

function makeTicket(table, waiter) {
  const counts = new Map(), add = item => counts.set(item, (counts.get(item) || 0) + 1);
  const ticket = { id: ticketCount + 1, spent: {}, table, waiter, claimed: false, stage: "carried", created: clock, since: clock, stove: 0, oven: 0, coffee: 0 };
  for (let i = 0; i < table.party.size; i++) {
    const kind = Math.random() < PIZZA_CHANCE ? "oven" : "stove";
    add(MENU[kind][Math.floor(Math.random() * MENU[kind].length)]);
    ticket[kind]++;
    if (Math.random() < COFFEE_CHANCE) ticket.coffee++;
  }
  if (ticket.coffee) counts.set("Coffee", ticket.coffee);
  const lines = [...counts].map(([item, n]) => `${n} × ${item}`).join("\n");
  const guests = table.party.size;
  ticket.lines = lines;
  table.party.ticket = ticket;
  ticket.info = {
    nodes: [], kind: "Order ticket", name: `Ticket ${++ticketCount} for table ${table.id}`, listName: `Ticket ${ticketCount}`,
    what: `A paper slip with the order from table ${table.id} (${guests} ${guests === 1 ? "guest" : "guests"}), written by ${waiter.name} at ${clockText(clock)}.`,
    purpose: "Tells the kitchen exactly what to cook and which table it is for.",
    why: "It is how an order travels from the guests to the cooks. Following one ticket shows where a table's waiting time goes.",
    extra: [
      ["On the ticket", lines],
      ["Time since the order was taken", () => clockText((ticket.delivered ?? clock) - ticket.created)],
    ],
  };
  tickets.push(ticket);
  ticket.info.subject = ticket;
  ticket.stay = stay(orderStays);
  return ticket;
}
function moveTicket(ticket, stage) {
  ticket.spent[ticket.stage] = clock - ticket.since;   // how long each stage took, for the metrics
  if (stage === "done") { servedOrders.push(clock - ticket.created); ticket.stay.end = clock; }
  ticket.stage = stage; ticket.since = clock; boardsDirty = true;
}
const servedOrders = [];   // seconds from order taken to food served, for every delivered order

const rail = [];   // order tickets waiting for a cook
const pass = [];   // finished orders waiting for a waiter
let boardsDirty = true;
