/* gepad - reading the pad, and the two little state machines that turn
 * stick and trigger positions into something Earth understands. */

/** Rescale past the deadzone so the usable travel still spans 0..1. */
gepad.dead = function (v, dz = gepad.cfg.deadzone) {
  const a = Math.abs(v);
  if (a < dz) return 0;
  return ((a - dz) / (1 - dz)) * Math.sign(v);
};

/* Chrome hands out a sparse array with a hole for every unplugged slot, and
 * exposes nothing at all until the page has seen a button press - so a null
 * here means "press something", not "no pad". */
gepad.readPad = function () {
  for (const p of navigator.getGamepads?.() ?? []) {
    if (p && p.connected) return p;
  }
  return null;
};

/** Analogue value of a button; triggers report 0..1, the rest 0 or 1. */
gepad.button = function (pad, i) {
  const b = pad.buttons[i];
  if (b == null) return 0;
  return typeof b === "object" ? b.value : b;
};

gepad.down = (pad, i) => gepad.button(pad, i) > 0.5;

gepad.axis = (pad, i) => pad.axes[i] ?? 0;

/** Fires once per press rather than once per frame. */
gepad.Edge = class {
  constructor() {
    this.prev = {};
  }
  rose(name, now) {
    const was = this.prev[name] === true;
    this.prev[name] = now;
    return now && !was;
  }
};

/* The stick position, filtered so the yoke has some inertia. Each axis
 * chases the stick with an exponential approach; deflecting away from the
 * centre is quick, drifting back to it is slower. */
gepad.Yoke = class {
  constructor() {
    this.x = 0;
    this.y = 0;
  }

  center() {
    this.x = this.y = 0;
  }

  _step(cur, target, dt) {
    const tau =
      Math.abs(target) < Math.abs(cur) ? gepad.cfg.smoothOut : gepad.cfg.smoothIn;
    if (tau <= 0) return target;
    cur += (target - cur) * (1 - Math.exp(-dt / tau));
    // the approach is asymptotic - snap the last fraction home
    return Math.abs(cur) < 1e-3 ? 0 : cur;
  }

  update(tx, ty, dt) {
    this.x = this._step(this.x, tx, dt);
    this.y = this._step(this.y, ty, dt);
    return [this.x, this.y];
  }
};

/** Holds one of two keys down while the axis is deflected. */
gepad.KeyHolder = class {
  constructor(keyPos, keyNeg) {
    this.keyPos = keyPos;
    this.keyNeg = keyNeg;
    this.held = null;
  }

  update(amount) {
    const t = gepad.cfg.triggerThreshold;
    let want = null;
    if (amount > t) want = this.keyPos;
    else if (amount < -t) want = this.keyNeg;
    if (want === this.held) return;
    if (this.held) gepad.keyUp(this.held);
    if (want) gepad.keyDown(want);
    this.held = want;
  }

  release() {
    if (this.held) {
      gepad.keyUp(this.held);
      this.held = null;
    }
  }
};
