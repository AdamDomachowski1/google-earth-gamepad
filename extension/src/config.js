/* gepad - mapping and tuning.
 *
 * The Web Gamepad API normalises every pad it recognises to its "standard"
 * layout, so these numbers are far tamer than the SDL ones the Python port
 * has to cope with: the d-pad is four ordinary buttons rather than a hat
 * that half the pads decline to report, and the triggers are analogue
 * buttons with a .value in [0, 1] instead of axes that idle at -1.
 *
 * Everything here is overridable from the popup and stored in
 * chrome.storage.sync; these are only the values a fresh install starts at.
 */

globalThis.gepad = globalThis.gepad || {};

gepad.DEFAULTS = {
  // --- mapping (standard gamepad layout) ---
  axRoll: 0, //  left stick X
  axPitch: 1, //  left stick Y
  btnClick: 0, //  A
  btnEsc: 8, //  View / Back
  btnLT: 6, //  left trigger  -> decrease thrust
  btnRT: 7, //  right trigger -> increase thrust
  btnArm: 12, //  d-pad up     -> arm / disarm
  btnYokeMode: 15, //  d-pad right  -> mouse yoke <-> arrow keys

  // --- tuning ---
  deadzone: 0.12,
  // How far the yoke swings from the centre of the map at full deflection,
  // as a fraction of the map's half-size. Unlike the desktop port this
  // needs no calibration ritual: the canvas tells us its own size, so the
  // yoke physically cannot leave the window.
  radiusFrac: 0.35,
  invertPitch: false,

  // Yoke inertia, seconds. Deflecting away from centre is quick, drifting
  // back is slower; that asymmetry is what makes it fly like a plane
  // rather than a cursor. Set both to 0 for an instant yoke.
  smoothIn: 0.03,
  smoothOut: 0.1,

  triggerThreshold: 0.08,

  // "mouse" flies the analogue yoke by synthesising pointer moves.
  // "keys" falls back to Earth's arrow-key controls - digital, but it
  // survives anything that ignores synthetic mouse input.
  yokeMode: "mouse",

  hud: true,
};

gepad.cfg = Object.assign({}, gepad.DEFAULTS);

/** Load stored settings and keep gepad.cfg in step with the popup. */
gepad.loadSettings = function (onChange) {
  chrome.storage.sync.get(gepad.DEFAULTS, (stored) => {
    Object.assign(gepad.cfg, stored);
    if (onChange) onChange();
  });
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== "sync") return;
    for (const [key, { newValue }] of Object.entries(changes)) {
      if (newValue !== undefined) gepad.cfg[key] = newValue;
    }
    if (onChange) onChange();
  });
};
