// ---------- helpers ----------
const NS = "http://www.w3.org/2000/svg";
const $ = id => document.getElementById(id);

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
const clockText = t => Math.floor(t / 60) + ":" + String(Math.floor(t % 60)).padStart(2, "0");
