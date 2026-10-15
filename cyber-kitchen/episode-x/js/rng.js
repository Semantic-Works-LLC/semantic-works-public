// Seeded, reproducible random numbers (mulberry32). Same seed = the same run.
// A seed for one named stream: the run's seed mixed with the stream's name, so changing one part of
// the model does not shift another part's draws.
function streamSeed(seed, name) {
  let h = (0x811c9dc5 ^ (seed >>> 0)) >>> 0;
  for (let i = 0; i < name.length; i++) h = Math.imul(h ^ name.charCodeAt(i), 0x01000193) >>> 0;
  h = Math.imul(h ^ (h >>> 16), 0x85ebca6b) >>> 0;
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35) >>> 0;
  return (h ^ (h >>> 16)) >>> 0 || 1;
}
class Rng {
  constructor(seed) { this.s = seed >>> 0 || 1; }
  next() {
    let t = (this.s = (this.s + 0x6d2b79f5) >>> 0);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  uniform(a, b) { return a + (b - a) * this.next(); }
  triangular(min, mode, max) {
    const u = this.next(), c = max > min ? (mode - min) / (max - min) : 0.5;
    return u < c ? min + Math.sqrt(u * (max - min) * (mode - min)) : max - Math.sqrt((1 - u) * (max - min) * (max - mode));
  }
  // Draw from a spec: a number, or { dist: "uniform" | "triangular", ... }.
  draw(spec) {
    if (typeof spec === "number") return spec;
    if (spec.dist === "uniform") return this.uniform(spec.min, spec.max);
    if (spec.dist === "triangular") return this.triangular(spec.min, spec.mode, spec.max);
    throw new Error(`unknown distribution: ${JSON.stringify(spec)}`);
  }
}
