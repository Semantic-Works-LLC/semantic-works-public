// ---------- actions on the selected object ----------
// The Actions tab of the Selection section. Pin and unpin show a step, a resource or one unit of it by
// itself on the Process Map. The other two take one unit out of service and bring it back: a waiter or
// cook goes off sick, a machine breaks down, a table is closed.
// Each action is one line: its button, then what the button does. Only the actions that apply to the
// selected object right now are listed; the out-of-service pair is worded for what is selected.
const actionUnit = () => selected && desUnitOf(selected);
const actionWords = () => desOutWords(actionUnit().id);   // only asked for when a unit is selected
const actionState = () => { const unit = actionUnit(), pool = unit && desEngine.resources[unit.id]; return unit && { ...unit, state: pool.units[unit.index], going: pool.goingOut.has(unit.index) }; };
const ACTIONS = [
  { key: "pin", label: () => "Pin",
    does: () => "Shows this by itself on the Process Map: a step with what leads into it and out of it and the resources it needs; a resource, or one table, waiter, cook or machine, with the steps it takes part in; a party, or all the parties, with the steps of a visit.",
    can: () => { const target = graphPinTarget(selected); return Boolean(target) && graphPinned !== target; },
    run: () => { const target = graphPinTarget(selected); if (view !== "graph") setView("graph"); graphPin(target); } },
  { key: "unpin", label: () => "Unpin", does: () => "Goes back to the whole Process Map.",
    can: () => { const target = graphPinTarget(selected); return Boolean(target) && graphPinned === target; },
    run: () => graphPin(null) },
  { key: "out", label: () => actionWords().out, does: () => actionWords().outDoes,
    can: () => { const unit = actionState(); return Boolean(unit) && unit.state !== false && unit.state !== DES_OUT && !unit.going; },
    run: () => { const unit = actionUnit(); desEngine.setOut(unit.id, unit.index, true); } },
  { key: "back", label: () => actionWords().back, does: () => actionWords().backDoes,
    can: () => { const unit = actionState(); return Boolean(unit) && (unit.state === DES_OUT || unit.going); },
    run: () => { const unit = actionUnit(); desEngine.setOut(unit.id, unit.index, false); } },
];
function renderActions() {
  const box = $("actions");
  if (!selected || box.hidden) { box.dataset.shown = ""; return box.replaceChildren(); }
  // only the actions that apply right now are listed; the list is rebuilt only when that set changes
  const apply = ACTIONS.filter(action => action.can()), shown = apply.map(action => action.key).join() || "none";
  if (box.dataset.shown !== shown) {
    box.dataset.shown = shown;
    box.replaceChildren(...apply.map(action => {
      const row = document.createElement("div"), button = document.createElement("button"), words = document.createElement("span");
      row.className = "action";
      button.dataset.action = action.key;
      button.addEventListener("click", () => { if (action.can()) action.run(); renderActions(); });
      row.append(button, words);
      return row;
    }));
    if (!apply.length) {
      const none = document.createElement("p");
      none.className = "empty"; none.textContent = "No actions apply to this right now.";
      box.appendChild(none);
    }
  }
  for (const action of apply) {
    const button = box.querySelector(`[data-action=${action.key}]`);
    setText(button, action.label());
    setText(button.nextSibling, action.does());
  }
}

// ---------- the right-click menu ----------
// Right-click anything that can be selected, on any view: it becomes the selection, and the menu offers
// the same actions as the Actions tab, the ones that apply to it right now, and nothing about any other
// object: pinning this one unpins whatever was pinned, and Unpin is offered only on the pinned thing itself.
const actionMenu = document.createElement("div");
actionMenu.className = "actors"; actionMenu.id = "graph-menu"; actionMenu.hidden = true; actionMenu.setAttribute("role", "menu");
document.body.appendChild(actionMenu);
for (const node of ["desview", "desgraph", "scoreview"]) {   // the three pictures (the list of views is not set up yet when this runs)
  $(node).addEventListener("contextmenu", e => {
    const target = e.target.closest("[data-selectable]"), items = [];
    actionMenu.hidden = true;   // an earlier menu does not stay up
    if (target) {
      target.dispatchEvent(new MouseEvent("click", { bubbles: true }));   // select it, the way a click would
      for (const action of ACTIONS) {
        if (selected && action.can()) items.push([action.label(), action.run]);   // no name: the menu is always about the thing that was clicked
      }
    }
    if (!items.length) return;
    e.preventDefault();
    actionMenu.replaceChildren(...items.map(([label, act]) => {
      const item = document.createElement("button");
      item.className = "view-item"; item.setAttribute("role", "menuitem"); item.textContent = label;
      item.addEventListener("click", () => { actionMenu.hidden = true; act(); renderActions(); });
      return item;
    }));
    actionMenu.style.left = Math.min(e.clientX, innerWidth - 240) + "px"; actionMenu.style.top = Math.min(e.clientY, innerHeight - 40 * items.length - 20) + "px";
    actionMenu.hidden = false;
  });
}
document.addEventListener("click", () => { actionMenu.hidden = true; });
document.addEventListener("keydown", e => { if (e.key === "Escape") actionMenu.hidden = true; });
