// ---------- floor plan ----------
const DOOR = { x: 60, y: 270, aisle: 270 };
const OUTSIDE = { x: -20, y: 270 };
const RAIL_COOK = { x: 926, y: 270 };     // where a cook takes it
const PASS_WAITER = { x: 762, y: 465 };   // dining-room side of the small table
const PASS_COOK = { x: 926, y: 465 };     // kitchen side of the small table

const SEATS = {
  six:   [[-36, -42], [-36, 42], [0, -42], [0, 42], [36, -42], [36, 42]],
  round: [[0, -45], [0, 45], [-45, 0], [45, 0]],
  two:   [[-40, 0], [40, 0]],
};
const LAYOUT = [
  ["six", "six", "round", "two"],
  ["round", "six", "six", "round"],
  ["six", "round", "six", "two"],
];
const COLS = [190, 330, 470, 610], ROWS = [170, 370, 565];
const SERVICE = [{ dy: 72, aisle: 270 }, { dy: -72, aisle: 270 }, { dy: -72, aisle: 465 }];

// The twelve tables: where each stands, its seats, and where a waiter stands to serve it.
const tables = [];
LAYOUT.forEach((row, r) => row.forEach((type, c) => {
  const x = COLS[c], y = ROWS[r];
  tables.push({ type, x, y, capacity: SEATS[type].length, seats: SEATS[type].map(([dx, dy]) => ({ x: x + dx, y: y + dy })), sp: { x, y: y + SERVICE[r].dy } });
}));
