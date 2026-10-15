// ---------- tokens ----------
// Every moving thing in a view is a token with a place to be; each frame it glides part of the way there.
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
