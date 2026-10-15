// ---------- helpers ----------
const NS = "http://www.w3.org/2000/svg";
const $ = id => document.getElementById(id);
const rand = (a, b) => a + Math.random() * (b - a);

function el(name, attrs, parent) {
  const node = document.createElementNS(NS, name);
  for (const key in attrs) node.setAttribute(key, attrs[key]);
  if (parent) parent.appendChild(node);
  return node;
}
function text(content, attrs, parent) {
  const node = el("text", attrs, parent);
  node.textContent = content;
  return node;
}
function moveToward(o, tx, ty, step) {
  const dx = tx - o.x, dy = ty - o.y, dist = Math.hypot(dx, dy);
  if (dist <= step || dist === 0) { o.x = tx; o.y = ty; return true; }
  o.x += dx / dist * step; o.y += dy / dist * step;
  return false;
}
function pathLength(path) {
  let len = 0;
  for (let i = 1; i < path.length; i++) len += Math.hypot(path[i].x - path[i - 1].x, path[i].y - path[i - 1].y);
  return len;
}
function pointAt(path, d) {
  for (let i = 1; i < path.length; i++) {
    const a = path[i - 1], b = path[i], seg = Math.hypot(b.x - a.x, b.y - a.y);
    if (seg > 0 && d <= seg) return { x: a.x + (b.x - a.x) * d / seg, y: a.y + (b.y - a.y) * d / seg };
    d -= seg;
  }
  return path[path.length - 1];
}
