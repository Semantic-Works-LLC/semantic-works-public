function releaseStation(station) { station.on = false; station.busy = false; station.progress = 0; }

// The stations an order needs, in the order the cook visits them. Times are invented.
function stepsFor(cook, ticket) {
  const steps = [];
  if (ticket.stove) steps.push({ station: cook.stove, time: 4 + ticket.stove * 1.3 });
  if (ticket.oven) steps.push({ station: pizzaOven, time: 4 + ticket.oven * 1.0 });
  if (ticket.coffee) steps.push({ station: coffeeMachine, time: 1 + ticket.coffee * 0.5 });
  return steps;
}
function nextStep(c) {
  const step = c.steps[0];
  if (!step) { c.station = null; c.carry = "plates"; go(c, PASS_COOK); c.state = "toPass"; return; }
  if (step.station.busy) { c.state = "waitStation"; return; }   // shared oven or coffee machine is taken
  c.steps.shift();
  c.station = step.station; c.stepTime = step.time;
  c.station.busy = true; c.station.table = c.job.table;
  go(c, c.station); c.state = "toStation";
}

function updateCook(c, dt) {
  if (!advance(c, dt)) return;
  if (c.state === "working") c.station.progress = 1 - Math.max(0, c.timer - dt) / c.cookTime;
  if (c.timer > 0) { c.timer -= dt; if (c.timer > 0) return; }
  switch (c.state) {
    case "idle": {
      const ticket = rail.find(t => !t.claimed);
      if (!ticket) { if (c.at !== c.home) go(c, c.home); return; }
      ticket.claimed = true; c.job = ticket;
      go(c, RAIL_COOK); c.state = "toRail"; return;
    }
    case "toRail":
      c.timer = 0.5; c.state = "grabbing"; return;
    case "grabbing":
      rail.splice(rail.indexOf(c.job), 1);
      c.job.cook = c; moveTicket(c.job, "cooking");
      c.steps = stepsFor(c, c.job);
      c.carry = "ticket"; return nextStep(c);
    case "waitStation":
      return nextStep(c);
    case "toStation":
      c.station.on = true;
      c.cookTime = c.timer = c.stepTime;
      c.state = "working"; return;
    case "working":
      releaseStation(c.station);
      c.carry = "plates"; return nextStep(c);
    case "toPass":
      c.timer = 0.4; c.state = "plating"; return;
    case "plating":
      c.job.claimed = false;
      pass.push(c.job); moveTicket(c.job, "pass");
      c.carry = null; c.state = "idle"; return;
  }
}
