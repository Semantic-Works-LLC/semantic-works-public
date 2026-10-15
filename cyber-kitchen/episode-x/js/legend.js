// ---------- legend ----------
// What the marks on the picture mean. Each view has its own legend; it is the Legend section of the
// details panel and changes with the view.
const legendMark = inner => `<svg viewBox="0 0 28 20" aria-hidden="true">${inner}</svg>`;
const legendBox = (stripe, extra = "") => legendMark(`<rect x="1" y="1" width="26" height="18" rx="3" fill="#0d0d0d" stroke="#2c2c2a" stroke-width="1.5"/><rect x="2.500" y="3.500" width="3" height="13" rx="1.500" fill="${stripe}"/>${extra}`);
const LEGENDS = {
  des: [
    ['<i class="ring free"></i>', "Free table"],
    ['<i class="ring" style="--c: var(--menu)"></i>', "Table: reading the menu"],
    ['<i class="ring" style="--c: var(--ready)"></i>', "Table: wants to order, or ordering"],
    ['<i class="ring" style="--c: var(--waiting)"></i>', "Table: waiting for the food"],
    ['<i class="ring" style="--c: var(--eating)"></i>', "Table: eating"],
    ['<i class="dot waiter">W</i>', "Waiter"],
    ['<i class="dot cook">C</i>', "Cook"],
    ['<i class="dot guest"></i>', "Guest"],
    [legendMark('<rect x="5" y="3" width="18" height="14" rx="3" fill="#3a3f45" stroke="#6a737b"/><path d="M7 15L21 5" stroke="#ef4444" stroke-width="2.4" stroke-linecap="round"/>'), "Red line across a table or a machine: out of service. A waiter or cook who is off sick is not on the floor"],
  ],
  // the process map's legend follows its three sections: a string is a section heading, with a line saying what the section is
  graph: [
    ["Actors & resources", "Who is in the restaurant, and what it has to work with: parties, staff, tables and kitchen equipment."],
    [legendBox("#b9bcc0"), "Grey edge: actors. The people: parties, waiters and cooks"],
    [legendBox("#a78bfa"), "Violet edge: resources. The things they use: tables, stoves, the pizza oven and the coffee machine"],
    [legendMark('<rect x="9" y="5" width="10" height="10" rx="2" fill="none" stroke="#6a737b" stroke-width="1"/><path d="M10.500 6.500l7 7M17.500 6.500l-7 7" stroke="#6a737b" stroke-width="1.2" stroke-linecap="round"/>'), "Crossed square: one that is active. A party in the building, or a waiter, cook, table or machine that is taken right now"],
    [legendMark('<rect x="9" y="5" width="10" height="10" rx="2" fill="none" stroke="#6a737b" stroke-width="1"/>'), "Hollow square: one that is free"],
    [legendMark('<rect x="9" y="5" width="10" height="10" rx="2" fill="none" stroke="#6a737b" stroke-width="1"/><path d="M10.500 13.500l7 -7" stroke="#ef4444" stroke-width="1.6" stroke-linecap="round"/>'), "Red line: one that is out of service. A person off sick, a machine broken down, a table closed"],
    ["Tasks", "What is done for a party, step by step, from the door to the end of the meal."],
    [legendBox("#eab308"), "Step: something that is done for a party. Every party passes through the steps in the same order"],
    [legendMark('<rect x="2" y="2" width="24" height="16" rx="6" fill="#0d0d0d" stroke="var(--text-muted)" stroke-width="1.5" stroke-dasharray="4 3"/>'), "Waiting area inside a step: parties wait here until everything the step needs is free, then move to the middle and the step runs. Where parties pile up is where the restaurant is short of something"],
    [legendMark('<rect x="6" y="4" width="16" height="12" rx="3" fill="#b9bcc0" stroke="#0d0d0d"/><text x="14" y="13" text-anchor="middle" font-size="8" font-weight="700" fill="#111">12</text>'), "Party, or one part of its order while it is being made"],
    [legendBox("#898781"), "The other parts of an order, which Plating also waits for"],
    ["Outcomes", "How visits end. Each box counts the parties that ended that way since the start."],
    [legendBox("var(--eating)"), "Green edge: the visit ended well. The party dined"],
    [legendBox("var(--waiting)"), "Red edge: the visit was lost. The party was turned away at the door, or left without eating"],
  ],
  score: [
    ["Figures", "Each box is one figure for the whole restaurant. Click one for its details and metrics."],
    ["Colour", "The colour of a box's outline says how the figure stands against its objective."],
    [legendMark('<rect x="1" y="1" width="26" height="18" rx="3" fill="#0d0d0d" stroke="var(--eating)" stroke-width="1.5"/>'), "Green: on target"],
    [legendMark('<rect x="1" y="1" width="26" height="18" rx="3" fill="#0d0d0d" stroke="var(--ready)" stroke-width="1.5"/>'), "Orange: a little off target, within a quarter of it"],
    [legendMark('<rect x="1" y="1" width="26" height="18" rx="3" fill="#0d0d0d" stroke="var(--waiting)" stroke-width="1.5"/>'), "Red: off target"],
    [legendMark('<rect x="1" y="1" width="26" height="18" rx="3" fill="#0d0d0d" stroke="#2c2c2a" stroke-width="1.5"/>'), "Grey: no target. The figure is kept for the record, or has no history yet"],
  ],
};
function renderLegend() {
  const box = document.createElement("div");
  let list = null;
  for (const [mark, label] of LEGENDS[view]) {
    if (!mark.startsWith("<")) {   // a section: its heading, then what the section is
      const heading = document.createElement("h4"), about = document.createElement("p");
      heading.className = "section"; heading.textContent = mark;
      about.className = "legend-about"; about.textContent = label;
      box.append(heading, about);
      list = null;
      continue;
    }
    if (!list) box.appendChild(list = document.createElement("ul"));
    const item = document.createElement("li"), sample = document.createElement("span"), words = document.createElement("span");
    sample.innerHTML = mark;   // fixed markup from the table above
    words.textContent = label;
    item.append(sample, words);
    list.appendChild(item);
  }
  $("legend").replaceChildren(box);
}
