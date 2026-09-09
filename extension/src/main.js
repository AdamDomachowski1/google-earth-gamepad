/* gepad - the main loop.
 *
 * Two states, not the desktop port's two modes. Cursor mode existed only
 * because the Python version hijacked the system cursor and you needed a way
 * to get it back; here the real mouse is untouched throughout, so the pad is
 * simply armed or it is not.
 *
 * Armed:   left stick is the yoke, triggers are thrust, A clicks, View is
 *          Escape. Disarm with d-pad up, or the physical Escape key.
 * Off:     the pad does nothing at all.
 */

(() => {
  const yoke = new gepad.Yoke();
  const edge = new gepad.Edge();
  const throttle = new gepad.KeyHolder("pageup", "pagedown");
  // Fallback yoke: Earth's own arrow-key controls, for the day synthetic
  // pointer events stop landing. Digital, so it flies like a staircase.
  const rollKeys = new gepad.KeyHolder("right", "left");
  const pitchKeys = new gepad.KeyHolder("down", "up");

  let hud = null;
  let armed = false;
  let last = performance.now();
  let px = 0;
  let py = 0;

  function releaseAll() {
    throttle.release();
    rollKeys.release();
    pitchKeys.release();
  }

  function setArmed(on) {
    if (armed === on) return;
    armed = on;
    console.log(`[gepad] ${on ? "ARMED" : "off"}`);
    // Never leave a key held down across a state change - Earth would go on
    // applying thrust to a plane nobody is flying any more.
    releaseAll();
    yoke.center();
    if (on) {
      const r = gepad.mapRect();
      px = r.left + r.width / 2;
      py = r.top + r.height / 2;
    }
  }

  function frame(now) {
    requestAnimationFrame(frame);
    // A backgrounded tab stops rAF; clamp so the first frame back does not
    // teleport the yoke through a second's worth of easing.
    const dt = Math.min((now - last) / 1000, 0.1);
    last = now;

    const cfg = gepad.cfg;
    const pad = gepad.readPad();
    if (!pad) {
      setArmed(false);
      hud.render({ armed, pad, x: 0, y: 0 });
      return;
    }

    if (edge.rose("arm", gepad.down(pad, cfg.btnArm))) setArmed(!armed);

    if (edge.rose("mode", gepad.down(pad, cfg.btnYokeMode))) {
      releaseAll();
      cfg.yokeMode = cfg.yokeMode === "mouse" ? "keys" : "mouse";
      chrome.storage.sync.set({ yokeMode: cfg.yokeMode });
    }

    let x = 0;
    let y = 0;

    if (armed) {
      let pitch = gepad.dead(gepad.axis(pad, cfg.axPitch));
      if (cfg.invertPitch) pitch = -pitch;
      [x, y] = yoke.update(gepad.dead(gepad.axis(pad, cfg.axRoll)), pitch, dt);

      // Recomputed every frame so the yoke tracks a resized window and a
      // radius changed from the popup without needing to be re-armed.
      const r = gepad.mapRect();
      const cx = r.left + r.width / 2;
      const cy = r.top + r.height / 2;
      const radius = (cfg.radiusFrac * Math.min(r.width, r.height)) / 2;
      const nx = cx + x * radius;
      const ny = cy + y * radius;

      if (cfg.yokeMode === "mouse") {
        gepad.movePointer(nx, ny, nx - px, ny - py);
      } else {
        rollKeys.update(x);
        pitchKeys.update(y);
      }
      px = nx;
      py = ny;

      const rt = gepad.button(pad, cfg.btnRT);
      const lt = gepad.button(pad, cfg.btnLT);
      throttle.update(rt > lt ? rt : -lt);

      // A clicks where Earth believes the pointer is. Clicking inside the
      // simulation toggles Earth between mouse-guided and keyboard flight,
      // so this doubles as the fix when the yoke goes unresponsive.
      if (edge.rose("click", gepad.down(pad, cfg.btnClick))) {
        gepad.clickAt(px, py);
      }
      if (edge.rose("esc", gepad.down(pad, cfg.btnEsc))) gepad.tapKey("esc");
    }

    hud.render({
      armed,
      pad,
      x,
      y,
      yokeMode: cfg.yokeMode,
      throttle: throttle.held === "pageup" ? "+" : throttle.held ? "-" : "0",
    });
  }

  /* Call gepad.probe() from the console to see what the loop sees. The
   * content script runs in its own world, so pick "gepad" in DevTools'
   * context dropdown first - in the page's own world there is no `gepad`. */
  gepad.probe = function () {
    const r = gepad.mapRect();
    const pads = [...(navigator.getGamepads?.() ?? [])].filter(Boolean);
    return {
      canvas: gepad.hasCanvas() ? gepad.target() : "NOT FOUND (using body)",
      rect: `${Math.round(r.width)}x${Math.round(r.height)} at ${Math.round(r.left)},${Math.round(r.top)}`,
      pads: pads.map((p) => `${p.id} [${p.mapping || "non-standard"}]`),
      armed,
      yokeMode: gepad.cfg.yokeMode,
    };
  };

  /* Chrome hands out no gamepads to an unfocused document, and typing into
   * the console focuses DevTools - so calling probe() by hand always reports
   * an empty pad list, however well the pad works. This defers the reading
   * long enough to click back into the page first. */
  gepad.probeIn = function (seconds = 5) {
    console.log(`[gepad] probing in ${seconds}s - click the map now`);
    setTimeout(() => {
      console.log(`[gepad] focused: ${document.hasFocus()}`, gepad.probe());
    }, seconds * 1000);
  };

  function start() {
    hud = new gepad.Hud();
    console.log(
      "[gepad] loaded. d-pad up arms; gepad.probe() for diagnostics.",
      gepad.probe(),
    );

    // Escape on the real keyboard always disarms. isTrusted keeps our own
    // synthetic Escape from bouncing back and disarming the pad.
    addEventListener(
      "keydown",
      (e) => {
        if (e.isTrusted && e.key === "Escape") setArmed(false);
      },
      true,
    );
    // Held keys are owned by the tab; drop them before it goes away.
    addEventListener("blur", () => releaseAll());
    addEventListener("pagehide", () => releaseAll());

    // Polling alone is enough to fly, but the pad stays invisible to this
    // document until it sees a gamepad button press - a mouse click will
    // not do. These two make that moment audible in the console, which is
    // the difference between "not paired" and "not yet gestured".
    addEventListener("gamepadconnected", (e) =>
      console.log(`[gepad] pad connected: ${e.gamepad.id} [${e.gamepad.mapping || "non-standard"}]`),
    );
    addEventListener("gamepaddisconnected", (e) =>
      console.log(`[gepad] pad disconnected: ${e.gamepad.id}`),
    );

    requestAnimationFrame(frame);
  }

  gepad.loadSettings();
  start();
})();
