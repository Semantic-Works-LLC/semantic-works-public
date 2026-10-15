// ---------- floor plan ----------
const AISLES = [270, 465];           // horizontal walkways between table rows
const CORRIDORS = [85, 735];         // vertical walkways at the left and right of the room
const DOOR = { x: 60, y: 270, aisle: 270 };
const OUTSIDE = { x: -20, y: 270 };
const RAIL_WAITER = { x: 762, y: 270 };   // where a waiter hangs the order ticket
const RAIL_COOK = { x: 818, y: 270 };     // where a cook takes it
const PASS_WAITER = { x: 762, y: 465 };   // dining-room side of the small table
const PASS_COOK = { x: 850, y: 465 };     // kitchen side of the small table
const PARTY_COLORS = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"];

const SEATS = {
  six:   [[-36, -42], [-36, 42], [0, -42], [0, 42], [36, -42], [36, 42]],
  round: [[0, -45], [0, 45], [-45, 0], [45, 0]],
  two:   [[-40, 0], [40, 0]],
};
const PLATE_INSET = { six: 23, round: 24, two: 24 };
const LAYOUT = [
  ["six", "six", "round", "two"],
  ["round", "six", "six", "round"],
  ["six", "round", "six", "two"],
];
const COLS = [190, 330, 470, 610], ROWS = [170, 370, 565];
const SERVICE = [{ dy: 72, aisle: 270 }, { dy: -72, aisle: 270 }, { dy: -72, aisle: 465 }];

// Walk along the aisles: out to the aisle, along a corridor if the aisle changes, then in.
function route(a, b) {
  const pts = [];
  if (a.aisle != null) pts.push({ x: a.x, y: a.aisle });
  if (a.aisle == null || b.aisle == null || a.aisle !== b.aisle) {
    let cx = CORRIDORS[1];
    if (a.aisle != null && b.aisle != null) {
      const cost = c => Math.abs(a.x - c) + Math.abs(b.x - c);
      cx = cost(CORRIDORS[0]) < cost(CORRIDORS[1]) ? CORRIDORS[0] : CORRIDORS[1];
    }
    pts.push({ x: cx, y: a.aisle ?? a.y });
    pts.push({ x: cx, y: b.aisle ?? b.y });
  }
  if (b.aisle != null) pts.push({ x: b.x, y: b.aisle });
  pts.push({ x: b.x, y: b.y });
  return pts;
}
