// ---------- toolbar: the speed menu and the zoom ----------
// Speed: one button that opens a menu of speeds and shows the one in force.
const SPEEDS = [1, 2, 4, 8, 16];
function setSpeedMenu(open) {
  $("speed-menu").hidden = !open;
  $("speed-toggle").setAttribute("aria-expanded", open);
}
function setSpeed(next) {
  speed = next;
  keep("speed", next);
  $("speed-label").textContent = next + "×";
  $("speed-toggle").title = `Speed: ${next}×. Choose a speed`;
  $("speed-toggle").setAttribute("aria-label", $("speed-toggle").title);
  for (const item of $("speed-menu").children) item.setAttribute("aria-checked", Number(item.dataset.speed) === next);
}
for (const value of SPEEDS) {
  const item = document.createElement("button");
  item.className = "view-item"; item.dataset.speed = value; item.setAttribute("role", "menuitemradio");
  item.textContent = value + "×";
  item.addEventListener("click", () => { setSpeed(value); setSpeedMenu(false); });
  $("speed-menu").appendChild(item);
}
$("speed-toggle").addEventListener("click", e => { e.stopPropagation(); setPicker(false); setViewMenu(false); setSpeedMenu($("speed-menu").hidden); });
$("speed-menu").addEventListener("click", e => e.stopPropagation());

// Zoom: works the same on every view, by showing a smaller part of the picture. Each view keeps its
// own zoom. Plus and minus zoom about the middle of what is showing, and two fingers on the trackpad
// zoom about the pointer; when zoomed in, drag to move
// around; the fit button shows the whole picture again.
const ZOOM_STEP = 1.5, ZOOM_MAX = 8;
const zooms = {};   // per view: how many times enlarged, and the point of the picture at the middle
function zoomState() {
  const svg = $(VIEW_NODE[view]);
  if (!svg.dataset.whole) {
    // The whole picture is what is actually drawn, with a small margin, not the frame it was designed in:
    // a view that leaves part of its frame empty then fills the space it is given. Measured the first
    // time the view is on screen, and never wider than the designed frame.
    svg.dataset.frame ||= svg.getAttribute("viewBox");   // the frame the view was designed in
    const [fx, fy, fw, fh] = svg.dataset.frame.split(" ").map(Number), drawn = svg.getBBox(), margin = 12;
    if (!drawn.width || !drawn.height) return { svg, x: fx, y: fy, w: fw, h: fh, zoom: { k: 1, cx: fx + fw / 2, cy: fy + fh / 2 } };   // not on screen yet
    const left = Math.max(fx, drawn.x - margin), top = Math.max(fy, drawn.y - margin);
    const right = Math.min(fx + fw, drawn.x + drawn.width + margin), bottom = Math.min(fy + fh, drawn.y + drawn.height + margin);
    svg.dataset.whole = `${left} ${top} ${right - left} ${bottom - top}`;
  }
  const [x, y, w, h] = svg.dataset.whole.split(" ").map(Number);
  return { svg, x, y, w, h, zoom: zooms[view] ||= { k: 1, cx: x + w / 2, cy: y + h / 2 } };
}
// Show one state of the zoom: how many times enlarged, and the point at the middle.
function showZoom(svg, x, y, w, h, shown) {
  const width = w / shown.k, height = h / shown.k;
  const cx = Math.min(Math.max(shown.cx, x + width / 2), x + w - width / 2);   // never show past the edge of the picture
  const cy = Math.min(Math.max(shown.cy, y + height / 2), y + h - height / 2);
  svg.setAttribute("viewBox", `${cx - width / 2} ${cy - height / 2} ${width} ${height}`);
  return { cx, cy };
}
// Bring the picture to the zoom it should have: at once, or gliding there so the eye can follow.
const ZOOM_GLIDE = 280;   // milliseconds
let zoomGlide = 0;
function applyZoom(glide = false) {
  const { svg, x, y, w, h, zoom } = zoomState(), from = zoom.shown || { k: zoom.k, cx: zoom.cx, cy: zoom.cy };
  const width = w / zoom.k, height = h / zoom.k;
  zoom.cx = Math.min(Math.max(zoom.cx, x + width / 2), x + w - width / 2);
  zoom.cy = Math.min(Math.max(zoom.cy, y + height / 2), y + h - height / 2);
  svg.classList.toggle("zoomed", zoom.k > 1);
  $("zoom-in").disabled = zoom.k >= ZOOM_MAX;
  $("zoom-out").disabled = $("zoom-fit").disabled = zoom.k <= 1;
  cancelAnimationFrame(zoomGlide);
  if (!glide) { zoom.shown = { k: zoom.k, cx: zoom.cx, cy: zoom.cy }; showZoom(svg, x, y, w, h, zoom.shown); return; }
  const started = performance.now(), key = view;
  const step = now => {
    if (view !== key) return;   // the view was switched meanwhile; it is shown at its own zoom
    const t = Math.min((now - started) / ZOOM_GLIDE, 1), e = 1 - (1 - t) ** 3;   // ease out
    zoom.shown = { k: from.k * (zoom.k / from.k) ** e, cx: from.cx + (zoom.cx - from.cx) * e, cy: from.cy + (zoom.cy - from.cy) * e };
    showZoom(svg, x, y, w, h, zoom.shown);
    if (t < 1) zoomGlide = requestAnimationFrame(step);
  };
  zoomGlide = requestAnimationFrame(step);
}
// What a view draws has changed: measure the whole picture again and show all of it.
function refitView() {
  delete $(VIEW_NODE[view]).dataset.whole;
  delete zooms[view];
  applyZoom();
}
function zoomBy(factor) {
  const { zoom } = zoomState();
  zoom.k = Math.min(ZOOM_MAX, Math.max(1, zoom.k * factor));
  if (zoom.k < 1.01) zoom.k = 1;
  applyZoom(true);
}
function zoomFit() {
  zoomState().zoom.k = 1;
  applyZoom(true);
}
$("zoom-in").addEventListener("click", () => zoomBy(ZOOM_STEP));
$("zoom-out").addEventListener("click", () => zoomBy(1 / ZOOM_STEP));
$("zoom-fit").addEventListener("click", zoomFit);

// dragging a zoomed picture moves it; a drag does not count as a click on what is under the pointer
let zoomDrag = null, zoomDragged = false;
for (const id of Object.values(VIEW_NODE)) {
  const svg = $(id);
  svg.addEventListener("pointerdown", e => {
    const { zoom } = zoomState();
    if (zoom.k > 1 && e.button === 0) zoomDrag = { x: e.clientX, y: e.clientY, cx: zoom.cx, cy: zoom.cy, moved: false };
  });
  // two fingers on the trackpad (or the mouse wheel, or a pinch) zoom in and out about the point under the pointer
  svg.addEventListener("wheel", e => {
    e.preventDefault();
    const { zoom } = zoomState(), before = zoom.k;
    const at = new DOMPoint(e.clientX, e.clientY).matrixTransform(svg.getScreenCTM().inverse());   // the point of the picture under the pointer
    zoom.k = Math.min(ZOOM_MAX, Math.max(1, before * Math.exp(-e.deltaY * (e.ctrlKey ? 0.01 : 0.003))));
    zoom.cx = at.x + (zoom.cx - at.x) * before / zoom.k;   // that point stays where it is on screen
    zoom.cy = at.y + (zoom.cy - at.y) * before / zoom.k;
    applyZoom();
  }, { passive: false });
  svg.addEventListener("click", e => {
    if (!zoomDragged) return;
    zoomDragged = false;
    e.stopPropagation();
  }, true);
}
window.addEventListener("pointermove", e => {
  if (!zoomDrag) return;
  const { svg, w, h, zoom } = zoomState(), box = svg.getBoundingClientRect();
  const scale = Math.min(box.width / (w / zoom.k), box.height / (h / zoom.k));   // screen pixels per unit of the picture
  if (Math.abs(e.clientX - zoomDrag.x) + Math.abs(e.clientY - zoomDrag.y) > 4) zoomDrag.moved = true;
  if (!zoomDrag.moved) return;
  zoom.cx = zoomDrag.cx - (e.clientX - zoomDrag.x) / scale;
  zoom.cy = zoomDrag.cy - (e.clientY - zoomDrag.y) / scale;
  applyZoom();
});
window.addEventListener("pointerup", () => {
  zoomDragged = Boolean(zoomDrag && zoomDrag.moved);
  zoomDrag = null;
  if (zoomDragged) setTimeout(() => { zoomDragged = false; }, 0);   // only the click that ends this drag is swallowed
});
