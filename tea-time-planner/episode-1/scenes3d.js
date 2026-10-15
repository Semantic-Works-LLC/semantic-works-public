// 3D scenes: the sandwich plate (Food view) and the set table (Table layout view).
// Uses globals from index.html: SANDWICHES, GUEST_HAIR, GUEST_DRESS, rng, store.

// three.js r128 is inlined in index.html, so it is already loaded: nothing is fetched from the internet.
function loadThree() {
  if (!loadThree.p) loadThree.p = window.THREE ? Promise.resolve() : Promise.reject(new Error("three.js is missing from index.html"));
  return loadThree.p;
}

// Renderer + camera orbiting a pivot: drag to rotate/tilt, wheel to zoom.
function makeViewer(host, o) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
  renderer.outputEncoding = THREE.sRGBEncoding;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  host.prepend(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 200);

  scene.add(new THREE.HemisphereLight(0xfff6ea, 0xb89a78, 0.62));
  const sun = new THREE.DirectionalLight(0xffffff, 0.6);
  sun.position.set(...(o.sun || [4, 8, 5]));
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  const e = o.shadowExtent || 4;
  Object.assign(sun.shadow.camera, { left: -e, right: e, top: e, bottom: -e, far: 60 });
  sun.shadow.bias = -0.0004;
  scene.add(sun);

  const pivot = new THREE.Group();
  scene.add(pivot);

  const st = { rotY: o.rotY ?? 0.4, tilt: o.tilt ?? 0.75, dist: o.dist, dragging: false, idleAt: 0, anim: null };

  // Keep the camera where it was across live reloads, still moving if it was spinning.
  const camKey = o.key && "cam:" + o.key;
  const saved = camKey && store.get(camKey, null);
  if (saved) {
    Object.assign(st, { rotY: saved.rotY, tilt: saved.tilt, dist: saved.dist });
    if (saved.spinning) st.idleAt = -1e9;
  }
  const save = () => camKey && store.set(camKey, {
    rotY: st.rotY, tilt: st.tilt, dist: st.dist,
    spinning: !!o.autoSpin && !st.dragging && !st.anim && performance.now() - st.idleAt > (o.idleDelay || 2500),
  });
  setInterval(save, 300);
  window.addEventListener("pagehide", save);
  let lx = 0, ly = 0;
  host.addEventListener("pointerdown", ev => {
    if (ev.target.closest("button")) return;
    st.dragging = true; st.anim = null;
    lx = ev.clientX; ly = ev.clientY;
    host.setPointerCapture(ev.pointerId);
  });
  host.addEventListener("pointermove", ev => {
    if (!st.dragging) return;
    st.rotY += (ev.clientX - lx) * 0.01;
    st.tilt = Math.max(0.08, Math.min(1.5, st.tilt + (ev.clientY - ly) * 0.006));
    lx = ev.clientX; ly = ev.clientY;
  });
  const stop = () => { st.dragging = false; st.idleAt = performance.now(); };
  host.addEventListener("pointerup", stop);
  host.addEventListener("pointercancel", stop);
  host.addEventListener("wheel", ev => {
    ev.preventDefault();
    st.dist = Math.max(o.minDist, Math.min(o.maxDist, st.dist * (1 + ev.deltaY * 0.001)));
  }, { passive: false });

  function resize() {
    const w = host.clientWidth, h = host.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  new ResizeObserver(resize).observe(host);
  resize();

  // smoothly move to a preset camera angle
  function goTo(target) { st.anim = { ...target }; st.idleAt = performance.now(); }

  function frame(t) {
    requestAnimationFrame(frame);
    if (!host.offsetParent) return; // view hidden
    if (st.anim) {
      let done = true;
      for (const k of ["rotY", "tilt", "dist"]) {
        if (st.anim[k] === undefined) continue;
        const d = st.anim[k] - st[k];
        st[k] += d * 0.12;
        if (Math.abs(d) > 0.002) done = false;
      }
      if (done) st.anim = null;
    } else if (o.autoSpin && !st.dragging && t - st.idleAt > (o.idleDelay || 2500)) {
      st.rotY += o.spinSpeed || 0.0025;
      if (o.idleTilt) {
        // drift gently between two flattering angles, never below the table
        const [lo, hi] = o.idleTilt, mid = (lo + hi) / 2, amp = (hi - lo) / 2;
        const target = mid + amp * Math.sin(t / 14000 * Math.PI * 2);
        st.tilt += (target - st.tilt) * 0.004;
      }
    }
    pivot.rotation.y = st.rotY;
    if (o.onFrame) o.onFrame(t);
    // pull back on narrow screens so the whole scene fits
    const fit = Math.max(1, (o.fitAspect || 1.1) / Math.max(0.4, camera.aspect));
    camera.position.set(0, Math.sin(st.tilt) * st.dist * fit, Math.cos(st.tilt) * st.dist * fit);
    camera.lookAt(0, o.targetY || 0, 0);
    renderer.render(scene, camera);
  }
  requestAnimationFrame(frame);
  return { scene, pivot, camera, st, goTo };
}

// ---------- shared building blocks ----------
const MAT = {};
function mat(name) {
  if (MAT[name]) return MAT[name];
  const std = (color, extra) => new THREE.MeshStandardMaterial({ color, roughness: 0.6, ...extra });
  const glass = (color, opacity) => new THREE.MeshStandardMaterial({
    color, transparent: true, opacity, roughness: 0.05, metalness: 0.1, depthWrite: false, side: THREE.DoubleSide });
  const make = {
    porcelain: () => std(0xffffff, { roughness: 0.3 }),
    porcelainDS: () => std(0xffffff, { roughness: 0.3, side: THREE.DoubleSide }),
    gold: () => std(0xc9a46a, { roughness: 0.35, metalness: 0.6 }),
    silver: () => std(0xdfe3e8, { roughness: 0.22, metalness: 0.9 }),
    linen: () => std(0xfbf8f2, { roughness: 0.95 }),
    wood: () => std(0xb98552, { roughness: 0.7 }),
    chair: () => std(0xd8c3a0, { roughness: 0.75 }),
    floor: () => std(0xeadcc6, { roughness: 1 }),
    bread: () => std(0xe8cd98, { roughness: 0.95 }),
    glass: () => glass(0xdff0f6, 0.26),
    glassLid: () => glass(0xd5e8ef, 0.45),
    water: () => glass(0xcfe6f0, 0.35),
    skin: () => std(0xf2cfae, { roughness: 0.8 }),
    green: () => std(0x6c9a4a, { roughness: 0.8 }),
    leaf: () => std(0x5f8f4a, { roughness: 0.8 }),
    scone: () => std(0xe3bc85, { roughness: 0.95 }),
    sconeTop: () => std(0xc58a45, { roughness: 0.9 }),
    choux: () => std(0xd9a35f, { roughness: 0.85 }),
    chocolate: () => std(0x4a2a1a, { roughness: 0.35 }),
    whiteGlaze: () => std(0xf7f1e6, { roughness: 0.35 }),
    jam: () => std(0xa8202c, { roughness: 0.25 }),
    cream: () => std(0xf6e7bb, { roughness: 0.7 }),
    lemon: () => std(0xf2d64b, { roughness: 0.6 }),
    sugar: () => std(0xffffff, { roughness: 0.9 }),
    candle: () => std(0xfffbf0, { roughness: 0.6 }),
    flame: () => new THREE.MeshBasicMaterial({ color: 0xffc35a }),
    pearl: () => std(0xf8f3ea, { roughness: 0.15, metalness: 0.25 }),
  };
  return (MAT[name] = make[name] ? make[name]() : std(name));
}
function add(parent, geo, material, x = 0, y = 0, z = 0, shadow = true) {
  const m = new THREE.Mesh(geo, typeof material === "string" || typeof material === "number" ? mat(material) : material);
  m.position.set(x, y, z);
  m.castShadow = shadow;
  m.receiveShadow = true;
  parent.add(m);
  return m;
}
function group(parent, x = 0, y = 0, z = 0, rotY = 0) {
  const g = new THREE.Group();
  g.position.set(x, y, z);
  g.rotation.y = rotY;
  parent.add(g);
  return g;
}

function fillingTexture(layer, seed) {
  const c = document.createElement("canvas");
  c.width = 256; c.height = 64;
  const g = c.getContext("2d"), r = rng(seed);
  g.fillStyle = layer.color; g.fillRect(0, 0, 256, 64);
  layer.flecks.forEach(col => {
    g.fillStyle = col;
    for (let i = 0; i < 70; i++) {
      g.beginPath();
      g.ellipse(r() * 256, r() * 64, 2 + r() * 4, 1.5 + r() * 3, r() * 3, 0, Math.PI * 2);
      g.fill();
    }
  });
  const t = new THREE.CanvasTexture(c);
  t.encoding = THREE.sRGBEncoding;
  return t;
}

const fillingMats = new Map();
// One finger sandwich: bread, layers, bread. B is bread thickness; layer heights scale with it.
function makeFinger(sw, L, W, B) {
  if (!fillingMats.has(sw.id)) {
    fillingMats.set(sw.id, sw.layers.map((l, li) =>
      new THREE.MeshStandardMaterial({ map: fillingTexture(l, sw.id * 10 + li), roughness: 0.8 })));
  }
  const mats = fillingMats.get(sw.id);
  const g = new THREE.Group();
  const k = B / 0.17;
  let y = 0;
  const layer = (h, material, inset) => {
    add(g, new THREE.BoxGeometry(L * (1 - inset), h, W * (1 - inset)), material, 0, y + h / 2, 0);
    y += h;
  };
  layer(B, "bread", 0);
  sw.layers.forEach((l, li) => layer(l.h * k, mats[li], 0.03));
  layer(B, "bread", 0);
  return g;
}

// ---------- Food view: plate of finger sandwiches ----------
const Plate3D = (function () {
  let started = false;
  function start() {
    if (started) return;
    started = true;
    loadThree().then(build).catch(err => { console.error(err);
      document.querySelector("#plate3d .hint").textContent = "Couldn't load the 3D library (offline?)";
    });
  }
  function build() {
    const v = makeViewer(document.getElementById("plate3d"),
      { key: "plate", dist: 8.6, tilt: 0.75, minDist: 4.5, maxDist: 16, autoSpin: true, targetY: 0.1 });
    const P = v.pivot;

    add(P, new THREE.CylinderGeometry(3.1, 2.7, 0.14, 72), "porcelain", 0, -0.07, 0);
    const rim = add(P, new THREE.TorusGeometry(3.02, 0.07, 12, 96), "porcelain", 0, 0.02, 0);
    rim.rotation.x = Math.PI / 2;
    const band = add(P, new THREE.TorusGeometry(2.78, 0.018, 8, 96), "gold", 0, 0.005, 0);
    band.rotation.x = Math.PI / 2;

    const n = SANDWICHES.length * 3;
    SANDWICHES.forEach((sw, si) => {
      for (let k = 0; k < 3; k++) {
        const a = (si * 3 + k) / n * Math.PI * 2;
        const f = makeFinger(sw, 1.4, 0.44, 0.17);
        f.position.set(Math.cos(a) * 1.9, 0, Math.sin(a) * 1.9);
        f.rotation.y = -a;
        P.add(f);
      }
    });

    // a little sprig of dill in the middle
    const r = rng(3);
    for (let i = 0; i < 18; i++) {
      const a = r() * Math.PI * 2, d = r() * 0.35;
      add(P, new THREE.SphereGeometry(0.06 + r() * 0.05, 8, 6), "green",
        Math.cos(a) * d, 0.06 + r() * 0.12, Math.sin(a) * d);
    }
  }
  return { start };
})();

// Double-wall glass teapot with tea inside; returns its group.
function teapot(T, x, z, rotY, teaColor) {
  const g = group(T, x, 0.01, z, rotY);
  add(g, new THREE.CylinderGeometry(0.17, 0.17, 0.4, 40, 1, true), "glass", 0, 0.2, 0, false);
  add(g, new THREE.CylinderGeometry(0.14, 0.14, 0.36, 40, 1, true), "glass", 0, 0.2, 0, false); // double wall
  add(g, new THREE.CylinderGeometry(0.17, 0.17, 0.01, 40), "glass", 0, 0.005, 0, false);
  add(g, new THREE.CylinderGeometry(0.135, 0.135, 0.26, 40),
    new THREE.MeshStandardMaterial({ color: teaColor, transparent: true, opacity: 0.85, roughness: 0.1 }), 0, 0.15, 0);
  add(g, new THREE.CylinderGeometry(0.175, 0.175, 0.03, 40), "glassLid", 0, 0.415, 0, false);
  add(g, new THREE.SphereGeometry(0.03, 12, 8), "glassLid", 0, 0.45, 0, false);
  const spout = add(g, new THREE.CylinderGeometry(0.022, 0.04, 0.22, 16, 1, true), "glass", 0.22, 0.24, 0, false);
  spout.rotation.z = -0.9;
  const handle = add(g, new THREE.TorusGeometry(0.1, 0.018, 8, 20, Math.PI), "glassLid", -0.17, 0.21, 0, false);
  handle.rotation.z = Math.PI / 2;
  return g;
}

// ---------- Table layout view: British afternoon tea table ----------
const Table3D = (function () {
  let started = false, viewer = null, guests = [];

  function start() {
    if (started) return;
    started = true;
    loadThree().then(build).catch(err => { console.error(err);
      document.querySelector("#table3d .hint").textContent = "Couldn't load the 3D library (offline?)";
    });
  }

  // Each place, built facing the table: guest sits at +z, looks toward -z, right hand is +x.
  function placeSetting(T, x, z, rotY) {
    const g = group(T, x, 0.01, z, rotY);

    // tea plate with a folded white napkin on it
    add(g, new THREE.CylinderGeometry(0.32, 0.27, 0.03, 48), "porcelain", 0, 0.015, 0);
    const band = add(g, new THREE.TorusGeometry(0.28, 0.006, 6, 48), "gold", 0, 0.031, 0);
    band.rotation.x = Math.PI / 2;
    add(g, new THREE.BoxGeometry(0.3, 0.025, 0.19), "linen", 0, 0.045, 0.02);

    // fork on the left, knife on the right with the blade facing the plate
    const fork = group(g, -0.42, 0.012, 0);
    add(fork, new THREE.BoxGeometry(0.028, 0.008, 0.2), "silver", 0, 0, 0.06);
    add(fork, new THREE.BoxGeometry(0.036, 0.006, 0.04), "silver", 0, 0, -0.06);
    for (let t = 0; t < 4; t++) add(fork, new THREE.BoxGeometry(0.006, 0.006, 0.07), "silver", -0.0135 + t * 0.009, 0, -0.11);
    const knife = group(g, 0.42, 0.012, 0);
    add(knife, new THREE.BoxGeometry(0.03, 0.012, 0.12), "silver", 0, 0, 0.08);
    add(knife, new THREE.BoxGeometry(0.024, 0.004, 0.16), "silver", -0.003, 0, -0.06);

    // cup on saucer, top right, handle at about 4 o'clock, teaspoon on the saucer
    const cs = group(g, 0.5, 0, -0.42);
    add(cs, new THREE.CylinderGeometry(0.19, 0.15, 0.024, 40), "porcelain", 0, 0.012, 0);
    const sband = add(cs, new THREE.TorusGeometry(0.175, 0.006, 6, 40), "gold", 0, 0.025, 0);
    sband.rotation.x = Math.PI / 2;
    const cup = group(cs, 0, 0.02, 0, -0.5);
    const profile = [[0, 0], [0.055, 0], [0.065, 0.015], [0.085, 0.08], [0.095, 0.105]].map(p => new THREE.Vector2(p[0], p[1]));
    add(cup, new THREE.LatheGeometry(profile, 40), "porcelainDS");
    const tea = add(cup, new THREE.CircleGeometry(0.085, 32), 0x9a4a22, 0, 0.075, 0, false);
    tea.rotation.x = -Math.PI / 2;
    const rimC = add(cup, new THREE.TorusGeometry(0.095, 0.004, 6, 40), "gold", 0, 0.105, 0);
    rimC.rotation.x = Math.PI / 2;
    const handle = add(cup, new THREE.TorusGeometry(0.035, 0.01, 8, 16, Math.PI), "porcelain", 0.095, 0.06, 0);
    handle.rotation.z = -Math.PI / 2;
    const spoon = group(cs, 0.02, 0.025, 0.12, 1.2);
    add(spoon, new THREE.BoxGeometry(0.012, 0.005, 0.13), "silver", 0, 0, 0);
    const bowl = add(spoon, new THREE.SphereGeometry(0.02, 12, 8), "silver", 0, 0, -0.075);
    bowl.scale.set(1, 0.3, 1.4);
  }

  function chairAndGuest(T, x, z, rotY, i) {
    const g = group(T, x, 0, z, rotY);
    add(g, new THREE.BoxGeometry(0.7, 0.08, 0.7), "chair", 0, -0.9, 1.15);
    for (const [lx, lz] of [[-0.3, 0.85], [0.3, 0.85], [-0.3, 1.45], [0.3, 1.45]])
      add(g, new THREE.BoxGeometry(0.06, 1.4, 0.06), "chair", lx, -1.6, lz);
    // curved back that comes up to table height (the table top is at y = 0)
    const backMat = mat("chair").clone();
    backMat.side = THREE.DoubleSide;
    const R = 0.4, H = 0.86, ARC = 1.7;
    add(g, new THREE.CylinderGeometry(R, R, H, 32, 1, true, -ARC / 2, ARC), backMat, 0, -0.86 + H / 2, 1.15);
    const rail = group(g, 0, -0.01, 1.15, -(Math.PI / 2 - ARC / 2));
    const top = add(rail, new THREE.TorusGeometry(R, 0.03, 8, 32, ARC), "chair");
    top.rotation.x = Math.PI / 2;

    // a simple seated girl
    const p = group(g, 0, 0, 1.12);
    add(p, new THREE.CylinderGeometry(0.2, 0.3, 1.5, 24), GUEST_DRESS_HEX[i], 0, -0.12, 0);
    add(p, new THREE.SphereGeometry(0.21, 20, 14), GUEST_DRESS_HEX[i], 0, 0.62, 0);
    add(p, new THREE.SphereGeometry(0.24, 24, 16), "skin", 0, 0.98, 0);
    const hair = add(p, new THREE.SphereGeometry(0.26, 24, 16), GUEST_HAIR_HEX[i], 0, 1.04, 0.05);
    hair.scale.set(1, 1, 0.95);
    guests.push(p);
  }

  function cakeStand(T, x, z, rotY) {
    const g = group(T, x, 0.01, z, rotY);
    add(g, new THREE.CylinderGeometry(0.012, 0.012, 1.4, 12), "silver", 0, 0.7, 0);
    const finial = add(g, new THREE.TorusGeometry(0.06, 0.009, 8, 24), "silver", 0, 1.47, 0);
    add(g, new THREE.SphereGeometry(0.024, 12, 8), "silver", 0, 1.4, 0);
    finial.rotation.y = 0.4;
    const tiers = [[0.42, 0.03], [0.34, 0.6], [0.26, 1.12]];
    tiers.forEach(([r, y]) => {
      add(g, new THREE.CylinderGeometry(r, r * 0.85, 0.025, 48), "porcelain", 0, y, 0);
      const b = add(g, new THREE.TorusGeometry(r - 0.01, 0.006, 6, 48), "gold", 0, y + 0.013, 0);
      b.rotation.x = Math.PI / 2;
    });

    // bottom: finger sandwiches
    for (let i = 0; i < 10; i++) {
      const a = i / 10 * Math.PI * 2;
      const f = makeFinger(SANDWICHES[i % SANDWICHES.length], 0.26, 0.085, 0.032);
      f.position.set(Math.cos(a) * 0.24, 0.043, Math.sin(a) * 0.24);
      f.rotation.y = -a;
      g.add(f);
    }
    // middle: scones
    [[0, 0], ...[0, 1, 2, 3, 4].map(k => [Math.cos(k * 1.2566) * 0.2, Math.sin(k * 1.2566) * 0.2])].forEach(([sx, sz]) => {
      add(g, new THREE.CylinderGeometry(0.068, 0.075, 0.08, 24), "scone", sx, 0.653, sz);
      add(g, new THREE.CylinderGeometry(0.06, 0.068, 0.018, 24), "sconeTop", sx, 0.7, sz);
    });
    // top: mini éclairs (chocolate + white) and macarons
    const ecl = [[-0.1, 0.06, "chocolate"], [-0.1, -0.06, "whiteGlaze"], [0.02, 0.13, "whiteGlaze"], [0.02, -0.13, "chocolate"]];
    ecl.forEach(([ex, ez, glaze], k) => {
      const e = group(g, ex, 1.165, ez, k * 0.4);
      const body = add(e, new THREE.CylinderGeometry(0.025, 0.025, 0.12, 12), "choux");
      body.rotation.z = Math.PI / 2;
      add(e, new THREE.SphereGeometry(0.025, 12, 8), "choux", -0.06, 0, 0);
      add(e, new THREE.SphereGeometry(0.025, 12, 8), "choux", 0.06, 0, 0);
      add(e, new THREE.BoxGeometry(0.13, 0.012, 0.034), glaze, 0, 0.022, 0);
    });
    const macColors = [0xf4b6c6, 0xb9e0c8, 0xf7e199, 0xc9b6e8];
    macColors.forEach((c, k) => {
      const a = k / 4 * Math.PI * 2 + 0.6, mx = 0.13 + Math.cos(a) * 0.05, mz = Math.sin(a) * 0.06;
      add(g, new THREE.CylinderGeometry(0.038, 0.04, 0.02, 20), c, mx, 1.145, mz);
      add(g, new THREE.CylinderGeometry(0.034, 0.034, 0.012, 20), "cream", mx, 1.161, mz);
      add(g, new THREE.CylinderGeometry(0.04, 0.038, 0.02, 20), c, mx, 1.177, mz);
    });
  }

  function bowlWith(T, x, z, fill) {
    const g = group(T, x, 0.01, z);
    add(g, new THREE.CylinderGeometry(0.085, 0.065, 0.065, 32, 1, true), "porcelainDS", 0, 0.033, 0);
    add(g, new THREE.CylinderGeometry(0.065, 0.065, 0.005, 32), "porcelain", 0, 0.003, 0);
    add(g, new THREE.CylinderGeometry(0.078, 0.078, 0.01, 32), fill, 0, 0.05, 0);
    const sp = group(g, 0.04, 0.085, 0, 0.3);
    const h = add(sp, new THREE.BoxGeometry(0.13, 0.005, 0.012), "silver", 0.04, 0, 0);
    h.rotation.z = 0.35;
  }

  function milkAndSugar(T, x, z) {
    // milk jug
    const j = group(T, x, 0.01, z - 0.42);
    const prof = [[0, 0], [0.06, 0], [0.075, 0.03], [0.07, 0.12], [0.065, 0.15], [0.075, 0.17]].map(p => new THREE.Vector2(p[0], p[1]));
    add(j, new THREE.LatheGeometry(prof, 32), "porcelainDS");
    const jh = add(j, new THREE.TorusGeometry(0.04, 0.01, 8, 16, Math.PI), "porcelain", -0.075, 0.09, 0);
    jh.rotation.z = Math.PI / 2;
    const milk = add(j, new THREE.CircleGeometry(0.066, 24), 0xfffdf6, 0, 0.14, 0, false);
    milk.rotation.x = -Math.PI / 2;
    // sugar bowl with cubes
    const s = group(T, x, 0.01, z + 0.42);
    add(s, new THREE.CylinderGeometry(0.09, 0.07, 0.08, 32, 1, true), "porcelainDS", 0, 0.04, 0);
    add(s, new THREE.CylinderGeometry(0.07, 0.07, 0.005, 32), "porcelain", 0, 0.003, 0);
    const r = rng(5);
    for (let i = 0; i < 7; i++) {
      const c = add(s, new THREE.BoxGeometry(0.03, 0.03, 0.03), "sugar",
        (r() - 0.5) * 0.09, 0.07 + r() * 0.02, (r() - 0.5) * 0.09);
      c.rotation.set(r(), r(), r());
    }
    // lemon slices on a little dish
    const l = group(T, x, 0.01, z);
    add(l, new THREE.CylinderGeometry(0.11, 0.09, 0.015, 32), "porcelain", 0, 0.008, 0);
    [[-0.035, 0], [0.035, 0.02], [0, -0.04]].forEach(([lx, lz]) =>
      add(l, new THREE.CylinderGeometry(0.035, 0.035, 0.008, 20), "lemon", lx, 0.02, lz));
  }

  function bouquet(T, x, z, seed) {
    const g = group(T, x, 0.01, z);
    add(g, new THREE.CylinderGeometry(0.1, 0.085, 0.34, 32, 1, true), "glass", 0, 0.17, 0, false);
    add(g, new THREE.CylinderGeometry(0.09, 0.08, 0.2, 24), "water", 0, 0.1, 0, false);
    const r = rng(seed);
    for (let i = 0; i < 7; i++) {
      const s = add(g, new THREE.CylinderGeometry(0.006, 0.006, 0.5, 6), "green", (r() - 0.5) * 0.08, 0.3, (r() - 0.5) * 0.08);
      s.rotation.set((r() - 0.5) * 0.4, 0, (r() - 0.5) * 0.4);
    }
    const cols = [0xf19bb3, 0xf7c6d4, 0xf4a259, 0xfff3b0, 0xc9a3e6, 0xf6828c];
    const center = new THREE.Vector3(0, 0.5, 0);
    for (let i = 0; i < 12; i++) {
      // blooms on a dome above the vase
      const a = r() * Math.PI * 2, el = 0.25 + r() * 1.1;
      const dir = new THREE.Vector3(Math.cos(a) * Math.cos(el), Math.sin(el), Math.sin(a) * Math.cos(el));
      const pos = center.clone().addScaledVector(dir, 0.16 + r() * 0.05);
      const b = group(g, pos.x, pos.y, pos.z);
      b.quaternion.setFromUnitVectors(new THREE.Vector3(0, 0, 1), dir);
      const c = cols[(i + seed) % cols.length];
      for (let p = 0; p < 6; p++) {
        const pa = p / 6 * Math.PI * 2;
        const petal = add(b, new THREE.SphereGeometry(0.035, 10, 8), c, Math.cos(pa) * 0.035, Math.sin(pa) * 0.035, 0);
        petal.scale.set(1, 1, 0.45);
      }
      add(b, new THREE.SphereGeometry(0.02, 10, 8), 0xf2c94c, 0, 0, 0.01);
    }
    for (let i = 0; i < 10; i++) {
      const a = r() * Math.PI * 2;
      const lf = add(g, new THREE.SphereGeometry(0.05, 10, 8), "leaf", Math.cos(a) * 0.17, 0.38 + r() * 0.1, Math.sin(a) * 0.17);
      lf.scale.set(1.6, 0.35, 0.8);
      lf.rotation.y = -a;
    }
  }

  // floating candle in a glass cylinder, pearls sunk at the bottom
  function candle(T, x, z, height, seed) {
    const g = group(T, x, 0.01, z);
    add(g, new THREE.CylinderGeometry(0.08, 0.08, height, 32, 1, true), "glass", 0, height / 2, 0, false);
    add(g, new THREE.CylinderGeometry(0.08, 0.08, 0.008, 32), "glass", 0, 0.004, 0, false);
    const water = height * 0.75;
    add(g, new THREE.CylinderGeometry(0.075, 0.075, water, 32), "water", 0, water / 2, 0, false);
    const r = rng(seed);
    for (let i = 0; i < 14; i++) {
      const a = r() * Math.PI * 2, d = r() * 0.055;
      add(g, new THREE.SphereGeometry(0.014 + r() * 0.006, 12, 8), "pearl", Math.cos(a) * d, 0.02 + (i > 8 ? 0.025 : 0), Math.sin(a) * d);
    }
    add(g, new THREE.CylinderGeometry(0.055, 0.055, 0.045, 24), "candle", 0, water + 0.01, 0);
    add(g, new THREE.CylinderGeometry(0.002, 0.002, 0.02, 6), 0x333333, 0, water + 0.04, 0, false);
    const flame = add(g, new THREE.SphereGeometry(0.012, 10, 8), "flame", 0, water + 0.06, 0, false);
    flame.scale.set(1, 2, 1);
    const glow = new THREE.PointLight(0xffb85c, 0.25, 0.8);
    glow.position.set(0, water + 0.08, 0);
    g.add(glow);
  }

  function build() {
    const host = document.getElementById("table3d");
    viewer = makeViewer(host, { key: "table", dist: 11, tilt: 0.95, rotY: 0, minDist: 3, maxDist: 26, shadowExtent: 5, targetY: -0.1, fitAspect: 1.5, sun: [3, 10, 4],
      autoSpin: true, spinSpeed: 0.0009, idleDelay: 6000, idleTilt: [0.6, 1.05] });
    const T = viewer.pivot;

    // floor, table, white tablecloth with a drop
    const floor = add(T, new THREE.CircleGeometry(10, 64), "floor", 0, -2.32, 0, false);
    floor.rotation.x = -Math.PI / 2;
    add(T, new THREE.BoxGeometry(6, 0.1, 3.8), "wood", 0, -0.07, 0);
    for (const [lx, lz] of [[-2.8, -1.7], [2.8, -1.7], [-2.8, 1.7], [2.8, 1.7]])
      add(T, new THREE.BoxGeometry(0.15, 2.2, 0.15), "wood", lx, -1.22, lz);
    add(T, new THREE.BoxGeometry(6.3, 0.02, 4.1), "linen", 0, 0, 0);
    add(T, new THREE.BoxGeometry(6.3, 0.45, 0.02), "linen", 0, -0.215, 2.05);
    add(T, new THREE.BoxGeometry(6.3, 0.45, 0.02), "linen", 0, -0.215, -2.05);
    add(T, new THREE.BoxGeometry(0.02, 0.45, 4.1), "linen", 3.15, -0.215, 0);
    add(T, new THREE.BoxGeometry(0.02, 0.45, 4.1), "linen", -3.15, -0.215, 0);

    // 7 places: 3 on each long side, 1 at the head
    const places = [
      [-2, -1.35, Math.PI], [0, -1.35, Math.PI], [2, -1.35, Math.PI],
      [2.45, 0, Math.PI / 2],
      [2, 1.35, 0], [0, 1.35, 0], [-2, 1.35, 0],
    ];
    places.forEach(([x, z, rot], i) => {
      placeSetting(T, x, z, rot);
      chairAndGuest(T, x, z, rot, i);
    });

    // down the middle of the table
    bouquet(T, -2.4, 0, 1);
    candle(T, -2.4, -0.5, 0.32, 11);
    candle(T, -2.4, 0.5, 0.24, 12);
    cakeStand(T, -1.55, 0, 0.3);
    bowlWith(T, -1.15, -0.5, "jam");
    bowlWith(T, -1.15, 0.5, "cream");
    teapot(T, -0.75, 0, -Math.PI / 2, 0x9a3a18);   // African Nectar
    milkAndSugar(T, -0.4, 0);
    teapot(T, -0.05, 0, Math.PI / 2, 0xc08a2a);    // Palais des Thés
    bowlWith(T, 0.35, -0.5, "jam");
    bowlWith(T, 0.35, 0.5, "cream");
    cakeStand(T, 0.75, 0, 1.2);
    bouquet(T, 1.6, 0, 4);
    candle(T, 1.6, -0.5, 0.24, 13);
    candle(T, 1.6, 0.5, 0.32, 14);

    setGuests(store.get("showGuests", true));
  }

  function setGuests(on) {
    guests.forEach(g => (g.visible = on));
    store.set("showGuests", on);
    const b = document.getElementById("guestBtn");
    if (b) b.setAttribute("aria-pressed", on);
  }

  const PRESETS = {
    angle: { rotY: 0, tilt: 0.95, dist: 11 },
    top: { rotY: 0, tilt: 1.5, dist: 12 },
    guest: { rotY: 0, tilt: 0.32, dist: 6.5 },
  };
  function preset(name) { if (viewer) viewer.goTo(PRESETS[name]); }

  return { start, preset, toggleGuests: () => setGuests(!store.get("showGuests", true)) };
})();

// ---------- Drinks view: tea, Coke, wine ----------
const Drinks3D = (function () {
  let started = false;
  const steam = [], bubbles = [];

  function start() {
    if (started) return;
    started = true;
    loadThree().then(build).catch(err => {
      console.error(err);
      document.querySelector("#drinks3d .hint").textContent = "Couldn't load the 3D library (offline?)";
    });
  }

  function glassMat(color, opacity) {
    return new THREE.MeshStandardMaterial({ color, transparent: true, opacity, roughness: 0.15, metalness: 0.1, side: THREE.DoubleSide, depthWrite: false });
  }

  function bottle(T, x, z, kind, rotZ = 0, y = 0.01) {
    const look = {
      red: { glass: 0x2a0a10, cap: 0x6b1424 },
      white: { glass: 0x7d9446, cap: 0xd4af37 },
      champagne: { glass: 0x1d3a26, cap: 0xd4af37 },
    }[kind];
    const g = group(T, x, y, z);
    g.rotation.z = rotZ;
    const prof = [[0, 0], [0.12, 0], [0.125, 0.02], [0.125, 0.6], [0.11, 0.68], [0.05, 0.78], [0.04, 0.8], [0.04, 0.93], [0.045, 0.95], [0, 0.95]]
      .map(p => new THREE.Vector2(p[0], p[1]));
    add(g, new THREE.LatheGeometry(prof, 32),
      new THREE.MeshStandardMaterial({ color: look.glass, roughness: 0.15, metalness: 0.2, transparent: true, opacity: 0.92 }));
    add(g, new THREE.CylinderGeometry(0.127, 0.127, 0.2, 32, 1, true), "linen", 0, 0.32, 0);
    add(g, new THREE.CylinderGeometry(0.128, 0.128, 0.03, 32, 1, true), look.cap, 0, 0.44, 0);
    const capH = kind === "champagne" ? 0.2 : 0.12;
    add(g, new THREE.CylinderGeometry(0.046, 0.046, capH, 20), look.cap, 0, 0.95 - capH / 2 + 0.005, 0);
    return g;
  }

  function wineGlass(T, x, z, wine) {
    const g = group(T, x, 0.01, z);
    const prof = [[0, 0], [0.07, 0], [0.07, 0.006], [0.008, 0.012], [0.006, 0.15], [0.04, 0.17], [0.07, 0.23], [0.068, 0.33]]
      .map(p => new THREE.Vector2(p[0], p[1]));
    add(g, new THREE.LatheGeometry(prof, 32), glassMat(0xe8f3f8, 0.3), 0, 0, 0, false);
    if (wine) add(g, new THREE.CylinderGeometry(0.062, 0.035, 0.07, 24), glassMat(wine, 0.85), 0, 0.2, 0, false);
  }

  function flute(T, x, z) {
    const g = group(T, x, 0.01, z);
    const prof = [[0, 0], [0.055, 0], [0.055, 0.006], [0.006, 0.012], [0.005, 0.13], [0.03, 0.16], [0.036, 0.3], [0.034, 0.4]]
      .map(p => new THREE.Vector2(p[0], p[1]));
    add(g, new THREE.LatheGeometry(prof, 32), glassMat(0xe8f3f8, 0.3), 0, 0, 0, false);
    add(g, new THREE.CylinderGeometry(0.031, 0.026, 0.18, 20), glassMat(0xf3dd8a, 0.75), 0, 0.24, 0, false);
    const bm = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.8 });
    for (let i = 0; i < 7; i++) {
      const b = add(g, new THREE.SphereGeometry(0.004, 6, 4), bm, (Math.random() - 0.5) * 0.03, 0.16, (Math.random() - 0.5) * 0.03, false);
      bubbles.push({ m: b, base: 0.16, top: 0.33, phase: i / 7, speed: 0.7 + Math.random() * 0.5 });
    }
  }

  function iceBucket(T, x, z) {
    const g = group(T, x, 0.01, z);
    const prof = [[0, 0], [0.18, 0], [0.2, 0.04], [0.23, 0.38], [0.25, 0.4]].map(p => new THREE.Vector2(p[0], p[1]));
    add(g, new THREE.LatheGeometry(prof, 40), new THREE.MeshStandardMaterial({ color: 0xe6e9ed, roughness: 0.3, metalness: 0.35, side: THREE.DoubleSide }));
    for (const sx of [-1, 1]) {
      const h = add(g, new THREE.TorusGeometry(0.05, 0.008, 8, 16, Math.PI), "silver", sx * 0.235, 0.3, 0);
      h.rotation.z = sx * -Math.PI / 2;
      h.rotation.y = Math.PI / 2;
    }
    // ice, then two champagne bottles leaning out
    const ice = glassMat(0xf4fbff, 0.6);
    for (let i = 0; i < 26; i++) {
      const a = Math.random() * Math.PI * 2, d = Math.random() * 0.19;
      const c = add(g, new THREE.BoxGeometry(0.05, 0.05, 0.05), ice, Math.cos(a) * d, 0.28 + Math.random() * 0.09, Math.sin(a) * d, false);
      c.rotation.set(Math.random(), Math.random(), Math.random());
    }
    bottle(g, -0.07, 0, "champagne", 0.28, 0.03);
    bottle(g, 0.08, 0.02, "champagne", -0.22, 0.03);
  }

  function cokeCan(T, x, z) {
    const g = group(T, x, 0.01, z);
    add(g, new THREE.CylinderGeometry(0.065, 0.065, 0.2, 32), 0xc8102e, 0, 0.1, 0);
    add(g, new THREE.CylinderGeometry(0.058, 0.065, 0.015, 32), "silver", 0, 0.207, 0);
    add(g, new THREE.CylinderGeometry(0.066, 0.066, 0.025, 32, 1, true), 0xffffff, 0, 0.1, 0);
  }

  // a puff of steam rising from each teapot lid
  function addSteam(pot) {
    for (let i = 0; i < 10; i++) {
      const m = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0, depthWrite: false });
      const p = add(pot, new THREE.SphereGeometry(0.035, 10, 8), m, 0, 0.47, 0, false);
      steam.push({ m: p, phase: i / 10, seed: Math.random() * 6 });
    }
  }

  function animate(t) {
    steam.forEach(s => {
      const k = (t / 3200 + s.phase) % 1;
      s.m.position.set(Math.sin(k * 5 + s.seed) * 0.04, 0.47 + k * 0.5, Math.cos(k * 4 + s.seed) * 0.03);
      s.m.scale.setScalar(0.6 + k * 1.8);
      s.m.material.opacity = 0.28 * Math.min(1, k * 4) * (1 - k);
    });
    bubbles.forEach(b => {
      const k = (t / 1500 * b.speed + b.phase) % 1;
      b.m.position.y = b.base + k * (b.top - b.base);
    });
  }

  function build() {
    const v = makeViewer(document.getElementById("drinks3d"), {
      key: "drinks", dist: 4.6, tilt: 0.5, rotY: 0, minDist: 2, maxDist: 10, shadowExtent: 2.5, targetY: 0.3,
      autoSpin: true, spinSpeed: 0.0012, idleDelay: 5000, idleTilt: [0.35, 0.7], fitAspect: 1.2, sun: [2, 6, 3],
      onFrame: animate,
    });
    const T = v.pivot;
    // round side table with a white cloth
    add(T, new THREE.CylinderGeometry(1.65, 1.65, 0.04, 72), "linen", 0, -0.01, 0);
    add(T, new THREE.CylinderGeometry(1.66, 1.66, 0.3, 72, 1, true), "linen", 0, -0.16, 0);
    add(T, new THREE.CylinderGeometry(0.12, 0.2, 1.6, 24), "wood", 0, -1.1, 0);

    bottle(T, -1.15, -0.5, "red");
    bottle(T, -0.88, -0.62, "red");
    addSteam(teapot(T, -0.32, -0.55, -Math.PI / 2, 0x9a3a18));   // African Nectar
    addSteam(teapot(T, 0.32, -0.55, -Math.PI / 2, 0xc08a2a));    // Palais des Thés
    bottle(T, 0.88, -0.62, "white");
    bottle(T, 1.15, -0.5, "white");

    cokeCan(T, -0.95, 0.3);
    wineGlass(T, -0.6, 0.45, 0x5a0f1c);
    wineGlass(T, -0.38, 0.6, 0xe9dc9a);
    flute(T, 0.05, 0.62);
    flute(T, 0.25, 0.5);
    iceBucket(T, 0.85, 0.3);
  }

  return { start };
})();
