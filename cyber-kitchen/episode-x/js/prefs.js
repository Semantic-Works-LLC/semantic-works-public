// ---------- remembering how the page was left ----------
// Whether it was paused, the speed, the view, whether the details panel was open, which of its sections
// were unfolded and which tab was showing are kept in the browser's local storage, so the page comes back
// the way it was left. The simulation itself is not kept: it starts again from the beginning.
const PREFS_KEY = "cyber-kitchen.ui";
const prefs = (() => {
  try { return JSON.parse(localStorage.getItem(PREFS_KEY)) || {}; } catch (error) { return {}; }   // storage is off, or what is in it cannot be read
})();
function keep(name, value) {
  prefs[name] = value;
  try { localStorage.setItem(PREFS_KEY, JSON.stringify(prefs)); } catch (error) { /* storage is off: it lasts for this page only */ }
}
