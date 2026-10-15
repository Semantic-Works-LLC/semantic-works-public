// ---------- tokens that follow the arrows ----------
// Used by the graph views. A view gives the arrows it has drawn as edges, each with the points of its
// line. When a token has to go from one node to another, it is sent along the arrows that lead there,
// corner by corner. It leaves its node at the edge where the arrow starts and enters the last one at
// the edge where the arrow ends; a node it only passes through, it crosses through the centre.
// `centreOf` gives the centre of a node by its key.
function makeRouter(edges, centreOf) {
  const leaving = {};
  for (const edge of edges) (leaving[edge.from] ||= []).push(edge);
  // the arrows to follow from one node to another (fewest arrows), as one list of points; null if there is no way
  const route = (from, to) => {
    const cameBy = new Map([[from, null]]), queue = [from];
    while (queue.length) {
      const at = queue.shift();
      if (at === to) break;
      for (const edge of leaving[at] || []) if (!cameBy.has(edge.to)) { cameBy.set(edge.to, edge); queue.push(edge.to); }
    }
    if (from === to || !cameBy.has(to)) return null;
    const points = [];
    for (let edge = cameBy.get(to); edge; edge = cameBy.get(edge.from)) {
      points.unshift(...edge.points);
      if (edge.from !== from) points.unshift(centreOf(edge.from));   // a node it only passes through: straight across its centre
    }
    return points;
  };
  route.centreOf = centreOf;
  return route;
}
// Tell a token which node it now belongs in. If it is still on its way somewhere, it finishes that way
// first, crosses that node through the centre, and carries on from there: it never leaves the arrows.
function headFor(token, key, route) {
  if (token.at === key) return;
  const onward = (token.at && route(token.at, key)) || [];
  const under = token.route && token.route.length;
  if (!under && !onward.length && token.tx !== undefined) { token.x = token.tx; token.y = token.ty; }   // no arrow leads there: appear in place rather than cut across
  token.route = under ? [...token.route, route.centreOf(token.at), ...onward] : onward;
  token.at = key;
}
// Move a token for one frame: along its route while it has one, then gliding to its place (tx, ty).
// It moves at a steady pace that the eye can follow, and speeds up only when it has a long way to catch up.
function moveToken(token, seconds, ease) {
  const route = token.route;
  if (!route || !route.length) {
    token.x += (token.tx - token.x) * ease;
    token.y += (token.ty - token.y) * ease;
    return;
  }
  let left = Math.hypot(route[0].x - token.x, route[0].y - token.y);
  for (let i = 1; i < route.length; i++) left += Math.hypot(route[i].x - route[i - 1].x, route[i].y - route[i - 1].y);
  let step = Math.max(left / 0.7, 150) * seconds;
  while (step > 0 && route.length) {
    const next = route[0], distance = Math.hypot(next.x - token.x, next.y - token.y);
    if (distance <= step) { token.x = next.x; token.y = next.y; route.shift(); step -= distance; continue; }
    token.x += (next.x - token.x) * step / distance;
    token.y += (next.y - token.y) * step / distance;
    step = 0;
  }
}
