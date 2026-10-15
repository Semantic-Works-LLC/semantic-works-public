// ---------- main loop ----------
let speed = 1, paused = false, last = performance.now(), lastListUpdate = 0;

function tick(dt) {
  clock += dt;
  nextArrival -= dt;
  if (nextArrival <= 0) { spawnParty(); nextArrival = rand(5, 10); }
  [...parties].forEach(p => updateParty(p, dt));
  tables.forEach(t => updateTable(t, dt));
  for (const s of [...waiters, ...cooks]) if (s.leaving && s.state === "idle") dismiss(s);
  waiters.forEach(w => updateWaiter(w, dt));
  cooks.forEach(c => updateCook(c, dt));
  trackFlow(dt);
}
function frame(now) {
  const dt = Math.min((now - last) / 1000, 0.1);
  last = now;
  if (!paused) for (let i = 0; i < speed; i++) tick(dt);
  draw();
  if (now - lastListUpdate > 400) { lastListUpdate = now; updateActorList(); renderMetrics(); }
  requestAnimationFrame(frame);
}

$("pause").addEventListener("click", e => {
  paused = !paused;
  e.target.textContent = paused ? "Resume" : "Pause";
  e.target.setAttribute("aria-pressed", paused);
});
document.querySelectorAll(".speed").forEach(button => button.addEventListener("click", () => {
  speed = Number(button.dataset.speed);
  document.querySelectorAll(".speed").forEach(b => b.setAttribute("aria-pressed", b === button));
}));

$("panel-toggle").addEventListener("click", () => setPanel(!$("panel").classList.contains("open")));
$("panel-close").addEventListener("click", () => setPanel(false));
$("view").addEventListener("click", () => select(null));
$("loop").addEventListener("click", () => select(null));
$("view-toggle").addEventListener("click", () => setView(otherView()));
$("picker-toggle").addEventListener("click", e => { e.stopPropagation(); setPicker($("picker").hidden); });
$("picker-filter").addEventListener("input", updateActorList);
$("picker").addEventListener("click", e => e.stopPropagation());
document.addEventListener("click", () => setPicker(false));
document.addEventListener("keydown", e => { if (e.key === "Escape") setPicker(false); });

tables.forEach(t => setStatus(t, "free"));
renderCard();
if (location.hash === "#loop") setView("loop");
requestAnimationFrame(frame);
