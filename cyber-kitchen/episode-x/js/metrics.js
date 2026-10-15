// ---------- metrics ----------
// What every metrics card is built from. Each selectable object brings its own card (info.metrics).
const percent = share => Math.round(100 * share) + "%";
const atMost = (value, target) => value <= target ? ["On target", "good"] : value <= target * 1.25 ? ["A little over target", "warn"] : ["Over target", "bad"];
const atLeast = (value, target) => value >= target ? ["On target", "good"] : value >= target * 0.75 ? ["A little under target", "warn"] : ["Under target", "bad"];
const trend = (latest, average, format) => latest === undefined ? "No full 15-second slice yet."
  : `Latest 15 seconds: ${format(latest)}, ${Math.abs(latest - average) < 0.02 * (average || 1) ? "the same as" : latest > average ? "above" : "below"} its average so far.`;

function useMetrics(g, limit, { objective, measure, lowIsFine, numbers }) {
  const average = clock ? g.sum / clock : 0, target = lowIsFine ? `at most ${percent(limit)}` : `at least ${percent(limit)}`;
  return {
    objective, measure, numbers,
    value: percent(average), unit: "of the time so far",
    verdict: lowIsFine ? (average <= limit ? ["Within the limit", "good"] : ["Over the limit", "bad"]) : atLeast(average, limit),
    notes: [`Target: ${target}.`, trend(g.history.at(-1), average, percent)],
    chartTitle: "Use every 15 seconds", timelineTitle: "Use on the clock",
    chart: barChart(g.history, limit, v => lowIsFine ? v <= limit : v >= limit, percent),
    caption: "Each bar is 15 seconds of service, oldest on the left. Dashed line: the target.",
    timeline: readingTimeline(g),
    timelineCaption: "On the clock: blue while it is in use. " + NOW_NOTE,
  };
}
const NOW_NOTE = "The yellow line is now, and the last three minutes slide past it.";
const metricsFor = info => info.metrics();
