// ---------- switching views ----------
let view = "floor";
const VIEW_NODE = { floor: "view", loop: "loop" };
const VIEW_NAME = { floor: "restaurant floor", loop: "service: party states, queues and staff" };
const otherView = () => view === "floor" ? "loop" : "floor";
function setView(next) {
  view = next;
  // the button always shows where the next click goes
  const label = `Show the ${VIEW_NAME[otherView()]}`;
  for (const name in VIEW_NODE) {
    $(VIEW_NODE[name]).toggleAttribute("hidden", name !== view);
    $("icon-" + name).toggleAttribute("hidden", name === view);
  }
  $("view-toggle").title = label;
  $("view-toggle").setAttribute("aria-label", label);
  $("subtitle").textContent = `Live view of the ${VIEW_NAME[view]} \u2014 simulated`;
  history.replaceState(null, "", view === "floor" ? location.pathname : "#" + view);
  // the hidden view is not drawn, so start its tokens afresh next time
  loopTokens.forEach(token => token.g.remove());
  loopTokens.clear();
  loopFresh = true;
}
