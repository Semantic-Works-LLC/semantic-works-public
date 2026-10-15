// ---------- the width of the details panel ----------
// The divider between the picture and the details can be dragged. The width is kept when the panel
// is collapsed and expanded, and across reloads of the page (in the browser's local storage).
const PANEL_WIDTH = { key: "cyber-kitchen.details-width", standard: 340, least: 260 };
function setPanelWidth(width, keep) {
  const most = Math.max(PANEL_WIDTH.least, document.querySelector(".workspace").clientWidth - 320);   // always leave room for the picture
  const px = Math.round(Math.min(Math.max(width, PANEL_WIDTH.least), most));
  document.documentElement.style.setProperty("--panel-width", px + "px");
  if (keep) try { localStorage.setItem(PANEL_WIDTH.key, px); } catch (error) { /* storage is off: the width lasts for this page only */ }
  return px;
}
{
  let saved = NaN;
  try { saved = Number(localStorage.getItem(PANEL_WIDTH.key)); } catch (error) { /* storage is off */ }
  setPanelWidth(saved || PANEL_WIDTH.standard, false);
  const divider = $("panel-divider"), workspace = document.querySelector(".workspace");
  let drag = null;
  divider.addEventListener("pointerdown", e => {
    drag = { x: e.clientX, width: $("panel").getBoundingClientRect().width };
    divider.setPointerCapture(e.pointerId);
    divider.classList.add("dragging"); workspace.classList.add("resizing");
    e.preventDefault();
  });
  divider.addEventListener("pointermove", e => { if (drag) setPanelWidth(drag.width + (drag.x - e.clientX), false); });   // dragging left makes the details wider
  const drop = e => {
    if (!drag) return;
    setPanelWidth(drag.width + (drag.x - e.clientX), true);
    drag = null;
    divider.classList.remove("dragging"); workspace.classList.remove("resizing");
  };
  divider.addEventListener("pointerup", drop);
  divider.addEventListener("pointercancel", drop);
  divider.addEventListener("dblclick", () => setPanelWidth(PANEL_WIDTH.standard, true));   // back to the standard width
  window.addEventListener("resize", () => setPanelWidth(parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--panel-width")) || PANEL_WIDTH.standard, false));
}
