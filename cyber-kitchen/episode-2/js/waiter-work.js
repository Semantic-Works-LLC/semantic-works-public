function nextWaiterJob() {
  const order = pass.find(o => !o.claimed);
  if (order) { order.claimed = true; return { type: "deliver", order, table: order.table }; }
  const table = tables.filter(t => t.status === "ready" && !t.claimed).sort((a, b) => a.since - b.since)[0];
  if (table) { table.claimed = true; return { type: "order", table }; }
  return null;
}

function updateWaiter(w, dt) {
  if (!advance(w, dt)) return;
  if (w.timer > 0) { w.timer -= dt; if (w.timer > 0) return; }
  switch (w.state) {
    case "idle":
      w.job = nextWaiterJob();
      if (!w.job) { if (w.at !== w.home) go(w, w.home); return; }
      if (w.job.type === "order") { go(w, w.job.table.sp); w.state = "toTable"; }
      else { go(w, PASS_WAITER); w.state = "toPass"; }
      return;
    case "toTable":
      setStatus(w.job.table, "ordering"); w.timer = 2.5; w.state = "taking"; return;
    case "taking":
      w.job.ticket = makeTicket(w.job.table, w);
      w.carry = "ticket"; go(w, RAIL_WAITER); w.state = "toRail"; return;
    case "toRail":
      w.timer = 0.5; w.state = "hanging"; return;
    case "hanging":
      rail.push(w.job.ticket); moveTicket(w.job.ticket, "rail");
      w.job.table.claimed = false;
      setStatus(w.job.table, "waiting");
      w.carry = null; w.state = "idle"; return;
    case "toPass":
      w.timer = 0.6; w.state = "picking"; return;
    case "picking":
      pass.splice(pass.indexOf(w.job.order), 1);
      w.job.order.waiter = w; moveTicket(w.job.order, "delivering");
      w.carry = "plates"; go(w, w.job.table.sp); w.state = "toServe"; return;
    case "toServe":
      w.timer = 1.5; w.state = "serving"; return;
    case "serving":
      setStatus(w.job.table, "eating");
      w.job.table.timer = rand(14, 22);
      w.job.order.delivered = clock; moveTicket(w.job.order, "done");
      tickets.splice(tickets.indexOf(w.job.order), 1);
      delivered.unshift(w.job.order);
      if (delivered.length > 10) delivered.pop();
      w.carry = null; w.state = "idle"; return;
  }
}
