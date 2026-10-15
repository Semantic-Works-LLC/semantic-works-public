// A station is somewhere a cook stands and works: it glows while in use and shows progress.
function makeStation(standX, standY, glow, barX, barY) {
  const station = { x: standX, y: standY, on: false, busy: false, progress: 0 };
  station.flame = el(glow.tag, { class: "flame", ...glow.attrs }, furniture);
  el("rect", { class: "progress-track", x: barX, y: barY, width: 50, height: 5, rx: 2.5 }, furniture);
  station.bar = el("rect", { class: "progress-bar", x: barX, y: barY, width: 0, height: 5, rx: 2.5 }, furniture);
  return station;
}

const stoves = [200, 400].map((y, i) => {
  const burner = el("circle", { class: "burner", cx: 1141, cy: y, r: 20 }, furniture);
  const stove = makeStation(1085, y, { tag: "circle", attrs: { cx: 1141, cy: y, r: 14 } }, 1116, y + 28);
  stove.name = `stove ${i + 1}`; stove.verb = "Cooking";
  stove.info = selectable(burner, {
    kind: "Kitchen equipment", name: `Stove ${i + 1}`,
    what: `A cooking burner on the range. It is cook ${i + 1}'s own station.`,
    purpose: "Where most orders are cooked. It glows and the bar under it fills while an order is on.",
    why: "The stoves are the kitchen's main capacity: one order per stove at a time, so two stoves means at most two orders cooking here at once.",
  });
  return stove;
});

// pizza oven: a brick dome with a glowing mouth
const ovenG = el("g", {}, furniture);
el("rect", { x: 1096, y: 560, width: 76, height: 100, rx: 6, fill: "#7a4a3a", stroke: "#a86a55", "stroke-width": 1.5 }, ovenG);
el("path", { d: "M1108 632 V606 A26 26 0 0 1 1160 606 V632 Z", fill: "#23272b", stroke: "#a86a55", "stroke-width": 1.5 }, ovenG);
text("PIZZA OVEN", { class: "small-label", x: 1134, y: 552, "text-anchor": "middle" }, ovenG);
const pizzaOven = makeStation(1072, 610,
  { tag: "path", attrs: { d: "M1114 630 V608 A20 20 0 0 1 1154 608 V630 Z" } }, 1109, 644);

// coffee machine: a small unit by the pass, with a cup under the spout
const coffeeG = el("g", {}, furniture);
el("rect", { class: "steel", x: 800, y: 548, width: 44, height: 56, rx: 4 }, coffeeG);
el("rect", { x: 807, y: 555, width: 30, height: 14, rx: 2, fill: "#23272b" }, coffeeG);
el("circle", { cx: 822, cy: 584, r: 8, fill: "#f2f2f2", stroke: "#0d0d0d", "stroke-width": 1 }, coffeeG);
text("COFFEE", { class: "small-label", x: 822, y: 540, "text-anchor": "middle" }, coffeeG);
const coffeeMachine = makeStation(866, 576,
  { tag: "circle", attrs: { cx: 822, cy: 584, r: 5.5, style: "fill: #6b3d1e" } }, 797, 609);
pizzaOven.name = "the pizza oven"; pizzaOven.verb = "Baking pizza";
coffeeMachine.name = "the coffee machine"; coffeeMachine.verb = "Making coffee";
pizzaOven.info = selectable(ovenG, {
  kind: "Kitchen equipment", name: "Pizza oven",
  what: "A brick oven in the corner of the kitchen.",
  purpose: "Bakes the pizza orders. Its mouth glows and the bar fills while a pizza is in.",
  why: "Pizza needs its own high heat, and it keeps those orders off the stoves. There is only one, so pizza orders cannot overlap.",
});
coffeeMachine.info = selectable(coffeeG, {
  kind: "Kitchen equipment", name: "Coffee machine",
  what: "A coffee machine beside the pass table.",
  purpose: "Makes the coffee that goes out with an order. The cup fills while it brews.",
  why: "Drinks are a quick extra sale. It sits by the pass so coffee is the last stop before the order goes out.",
});
const stations = [...stoves, pizzaOven, coffeeMachine];
