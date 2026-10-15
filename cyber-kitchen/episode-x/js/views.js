// ---------- switching views ----------
// The blue button in the middle of the top line names the view that is on screen and opens a menu of
// the views, numbered. All three views draw the one engine.
const VIEWS = [
  { key: "des", node: "desview", short: "Floor Plan" },
  { key: "graph", node: "desgraph", short: "Process Map" },
  { key: "score", node: "scoreview", short: "Scorecard" },
];
const VIEW_NODE = Object.fromEntries(VIEWS.map(one => [one.key, one.node]));
let view = "des";
function setViewMenu(open) {
  $("view-menu").hidden = !open;
  $("view-toggle").setAttribute("aria-expanded", open);
}
VIEWS.forEach((one, i) => {
  const item = document.createElement("button");
  item.className = "view-item"; item.dataset.view = one.key; item.setAttribute("role", "menuitemradio");
  const number = document.createElement("b"); number.textContent = i + 1;
  item.append(number, one.short);
  item.addEventListener("click", () => { setView(one.key); setViewMenu(false); });
  $("view-menu").appendChild(item);
});
function setView(next) {
  view = next;
  keep("view", next);
  const index = VIEWS.findIndex(one => one.key === view), label = `View ${index + 1}: ${VIEWS[index].short}. Choose a view`;
  for (const one of VIEWS) {
    $(one.node).toggleAttribute("hidden", one.key !== view);
  }
  for (const item of $("view-menu").children) item.setAttribute("aria-checked", item.dataset.view === view);
  $("view-toggle").title = label;
  $("view-toggle").setAttribute("aria-label", label);
  $("view-name").textContent = VIEWS[index].short;
  history.replaceState(null, "", index ? "#" + view : location.pathname);
  // a hidden view is not drawn, so start its tokens afresh next time
  for (const tokens of [desTokens, graphTokens]) {
    tokens.forEach(token => token.g.remove());
    tokens.clear();
  }
  desFresh = graphFresh = true;
  applyZoom();   // each view keeps its own zoom
  renderLegend();
}
