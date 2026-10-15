// ---------- drawing the moving parts ----------
function drawBoards() {
  boardsDirty = false;
  const railG = $("rail"), passG = $("pass");
  railG.replaceChildren(); passG.replaceChildren();
  tickets.forEach(t => t.info.nodes = []);
  if (selected && selected.kind === "Order ticket") selected.nodes = [];
  const clickable = (ticket, parent) => {
    const g = el("g", { "data-selectable": "" }, parent);
    g.addEventListener("click", e => { e.stopPropagation(); select(ticket.info); });
    if (ticket.info === selected) g.setAttribute("data-selected", "");
    ticket.info.nodes = [g];
    return g;
  };
  rail.slice(0, 5).forEach((t, i) => {
    const y = 233 + i * 15, g = clickable(t, railG);
    el("rect", { class: "ticket", x: 774, y, width: 32, height: 13, rx: 1.5 }, g);
    text(t.table.id, { class: "ticket-text", x: 790, y: y + 6.5 }, g);
  });
  if (rail.length > 5) text("+" + (rail.length - 5), { class: "small-label", x: 810, y: 318 }, railG);
  pass.slice(0, 6).forEach((o, i) => {
    const x = 790 + (i % 2) * 30, y = 442 + Math.floor(i / 2) * 23, g = clickable(o, passG);
    el("circle", { class: "dish", cx: x, cy: y, r: 10, fill: "#f2f2f2", stroke: "#b9b9b9", "stroke-width": 1.5 }, g);
    text(o.table.id, { class: "ticket-text", x, y }, g);
  });
}

function draw() {
  for (const party of parties) for (const m of party.members) {
    m.el.setAttribute("cx", m.x); m.el.setAttribute("cy", m.y);
  }
  for (const s of [...waiters, ...cooks]) {
    s.g.setAttribute("transform", `translate(${s.x} ${s.y})`);
    s.ticket.setAttribute("visibility", s.carry === "ticket" ? "visible" : "hidden");
    s.tray.setAttribute("visibility", s.carry === "plates" ? "visible" : "hidden");
  }
  for (const station of stations) {
    station.flame.style.opacity = station.on ? 0.65 + 0.35 * Math.sin(clock * 10) : 0;
    station.bar.setAttribute("width", 50 * station.progress);
  }
  if (boardsDirty) drawBoards();
  if (view === "loop") drawLoop();
  updateNow();
  const inside = parties.filter(p => p.state !== "queue").reduce((sum, p) => sum + p.size, 0);
  $("s-clock").textContent = clockText(clock);
  $("s-guests").textContent = inside;
  $("s-queue").textContent = parties.filter(p => p.state === "queue").length;
  $("s-rail").textContent = rail.length;
  $("s-cooking").textContent = cooks.filter(c => ["toStation", "working", "waitStation"].includes(c.state)).length;
  $("s-pass").textContent = pass.length;
  $("s-served").textContent = served;
  $("s-lost").textContent = turnedAway;
}
