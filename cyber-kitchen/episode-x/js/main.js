// ---------- main loop ----------
// One simulation: the DES engine. The page keeps the clock and tells the engine what time it is; the
// two views only draw what the engine holds.
let speed = 1, paused = false, last = performance.now(), lastListUpdate = 0;

function tick(dt) {
  clock += dt;
  desEngine.runUntil(clock);
  sampleGauges(dt);
}
function draw() {
  if (view === "des") drawDes();
  if (view === "graph") drawGraph();
  if (view === "score") drawScore();
}
function frame(now) {
  const dt = Math.min((now - last) / 1000, 0.1);
  last = now;
  if (!paused) for (let i = 0; i < speed; i++) tick(dt);
  draw();
  if (now - lastListUpdate > 400) { lastListUpdate = now; updateActorList(); renderMetrics(); renderEvents(); renderActions(); }
  requestAnimationFrame(frame);
}

function setPaused(next) {
  paused = next;
  keep("paused", paused);
  $("icon-pause").toggleAttribute("hidden", paused);   // the button shows what a click will do
  $("icon-play").toggleAttribute("hidden", !paused);
  $("pause").title = paused ? "Resume" : "Pause";
  $("pause").setAttribute("aria-label", $("pause").title);
  $("pause").setAttribute("aria-pressed", paused);
}
$("pause").addEventListener("click", () => setPaused(!paused));
$("panel-toggle").addEventListener("click", () => setPanel(!$("panel").classList.contains("open")));
$("desview").addEventListener("click", () => select(null));
$("desgraph").addEventListener("click", () => select(null));
$("scoreview").addEventListener("click", () => select(null));
$("view-toggle").addEventListener("click", e => { e.stopPropagation(); setPicker(false); setSpeedMenu(false); setViewMenu($("view-menu").hidden); });
$("view-menu").addEventListener("click", e => e.stopPropagation());
$("picker-toggle").addEventListener("click", e => { e.stopPropagation(); setViewMenu(false); setSpeedMenu(false); setPicker($("picker").hidden); });
$("picker-filter").addEventListener("input", updateActorList);
$("picker").addEventListener("click", e => e.stopPropagation());
document.addEventListener("click", () => { setPicker(false); setViewMenu(false); setSpeedMenu(false); });
document.addEventListener("keydown", e => { if (e.key === "Escape") { setPicker(false); setViewMenu(false); setSpeedMenu(false); } });

// Start the page the way it was left: paused or running, at the same speed, on the same view, with the
// details panel, its sections and its tab as they were. An address that names a view wins over the remembered one.
const left = { ...prefs, folds: { ...prefs.folds } };   // read before the calls below write the page's opening state over it
renderCard();
setSpeed(SPEEDS.includes(left.speed) ? left.speed : 1);
setView(location.hash.slice(1) in VIEW_NODE ? location.hash.slice(1) : left.view in VIEW_NODE ? left.view : "des");
for (const key in folds) setFold(key, left.folds[key] === true);
setTab(["about", "metrics", "actions"].includes(left.tab) ? left.tab : "about");
setPanel(left.panel === true);
setPaused(left.paused === true);
requestAnimationFrame(frame);
