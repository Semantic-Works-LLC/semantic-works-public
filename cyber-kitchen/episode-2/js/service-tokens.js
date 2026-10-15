// The things on the restaurant floor can be selected in the service view too: one object, drawn in two places.
const floorObject = name => fixedObjects.find(o => o.name === name);
function alsoSelectable(node, info) {
  info.nodes.push(node);
  node.setAttribute("data-selectable", "");
  node.addEventListener("click", e => { e.stopPropagation(); select(info); });
}
for (const [name, key] of [["Front door", "door"], ["Order rail", "rail"], ["Pass table", "pass"]]) floorObject(name).subject = key;

// ---------- tokens ----------
// In the service view every moving thing is a token with a place to be; each frame it glides part of the way there.
function setText(node, value) { if (node.textContent !== String(value)) node.textContent = value; }
function viewToken(tokens, layer, key, info, build) {
  let token = tokens.get(key);
  if (!token) {
    token = { key, info, also: [], x: null, g: el("g", { "data-selectable": "" }, $(layer)) };
    build(token.g, token);
    token.g.addEventListener("click", e => { e.stopPropagation(); select(info); });
    tokens.set(key, token);
  }
  token.live = true;
  return token;
}
const partyToken = (g, party) => {
  el("circle", { class: "guest", r: 9, fill: party.color }, g);
  text(party.size, { class: "token-text", style: "fill: #fff" }, g);
};
const orderToken = (g, token, ticket) => {
  token.paper = el("rect", { class: "ticket", x: -8, y: -9, width: 16, height: 18, rx: 2 }, g);
  token.dish = el("circle", { class: "dish", r: 9, fill: "#f2f2f2", stroke: "#b9b9b9", "stroke-width": 1.5 }, g);
  text(ticket.table.id, { class: "token-text" }, g);
};
function showAsFood(token, food) {
  token.paper.setAttribute("visibility", food ? "hidden" : "visible");
  token.dish.setAttribute("visibility", food ? "visible" : "hidden");
}
// Move every token part of the way to its place, and see off the ones that have left the simulation.
function glideTokens(tokens, ease) {
  for (const token of tokens.values()) {
    if (!token.live) {
      // an order goes back to its party; a party leaves at the right edge
      token.tx = token.home ? token.home.x : 1240;
      token.ty = token.home ? token.home.y : token.y;
      if (Math.abs(token.tx - token.x) + Math.abs(token.ty - token.y) < 4) { token.g.remove(); tokens.delete(token.key); continue; }
    }
    token.x += (token.tx - token.x) * ease;
    token.y += (token.ty - token.y) * ease;
    token.g.setAttribute("transform", `translate(${token.x.toFixed(1)} ${token.y.toFixed(1)})`);
    token.g.toggleAttribute("data-selected", selected !== null && (token.info === selected || token.also.includes(selected)));
  }
}
const staffToken = (label, dark) => g => {
  el("circle", { class: "person", r: 10, fill: dark ? "#0d0d0d" : "#fff", stroke: dark ? "#fff" : "#0d0d0d", "stroke-width": dark ? 2 : 1 }, g);
  text(label, { class: "token-text", style: `fill: ${dark ? "#fff" : "#0d0d0d"}` }, g);
};
