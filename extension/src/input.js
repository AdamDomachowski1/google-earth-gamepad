/* gepad - the synthetic input layer.
 *
 * This is the browser's answer to macinput.py, and it is where the one real
 * risk of the whole approach lives. Events built in JavaScript carry
 * isTrusted: false. Ordinary listeners receive them regardless, so Earth
 * should never notice - but if it ever starts checking, the escape hatch is
 * a chrome.debugger build driving CDP's Input.dispatchMouseEvent, whose
 * events are indistinguishable from a real mouse. Nothing above this file
 * would have to change.
 *
 * Two dialects go out for every gesture: Pointer Events and the older Mouse
 * Events. Earth is a WebAssembly canvas app and we cannot see which one it
 * listens for, so we send both and let it ignore the half it does not want.
 */

(() => {
  let cached = null;

  /** querySelector that also descends into open shadow roots. */
  function deepQuery(selector, root) {
    const hit = root.querySelector(selector);
    if (hit) return hit;
    for (const el of root.querySelectorAll("*")) {
      if (el.shadowRoot) {
        const found = deepQuery(selector, el.shadowRoot);
        if (found) return found;
      }
    }
    return null;
  }

  /* The element every synthetic event is aimed at. Earth buries its canvas
   * inside web components, and the app may not have painted one yet, so the
   * lookup is lazy and re-runs whenever the cached node leaves the document.
   * Events bubble, so hitting the canvas also reaches any listener parked on
   * document or window - aiming higher would miss the canvas itself. */
  gepad.target = function () {
    if (cached && cached.isConnected) return cached;
    // Only ever cache a real canvas. Caching the body fallback would pin us
    // to it for good - body stays connected forever, so the lookup would
    // never run again and every event would miss the canvas that Earth
    // painted a second after we first looked.
    cached = deepQuery("canvas", document);
    return cached || document.body;
  };

  /** Whether the map canvas has actually been found (for the HUD). */
  gepad.hasCanvas = () => !!gepad.target().matches?.("canvas");

  /** Bounding box of the map, falling back to the viewport. */
  gepad.mapRect = function () {
    const el = gepad.target();
    const r = el.getBoundingClientRect();
    if (r.width > 1 && r.height > 1) return r;
    return { left: 0, top: 0, width: innerWidth, height: innerHeight };
  };

  function mouseInit(x, y, extra) {
    return Object.assign(
      {
        bubbles: true,
        cancelable: true,
        composed: true,
        view: window,
        clientX: x,
        clientY: y,
        screenX: x,
        screenY: y,
        pointerId: 1,
        pointerType: "mouse",
        isPrimary: true,
        button: 0,
        buttons: 0,
      },
      extra,
    );
  }

  gepad.movePointer = function (x, y, dx, dy) {
    const el = gepad.target();
    const init = mouseInit(x, y, { movementX: dx, movementY: dy });
    el.dispatchEvent(new PointerEvent("pointermove", init));
    el.dispatchEvent(new MouseEvent("mousemove", init));
  };

  gepad.clickAt = function (x, y) {
    const el = gepad.target();
    const down = mouseInit(x, y, { buttons: 1 });
    const up = mouseInit(x, y, { buttons: 0 });
    el.dispatchEvent(new PointerEvent("pointerdown", down));
    el.dispatchEvent(new MouseEvent("mousedown", down));
    el.dispatchEvent(new PointerEvent("pointerup", up));
    el.dispatchEvent(new MouseEvent("mouseup", up));
    el.dispatchEvent(new MouseEvent("click", up));
  };

  const KEYS = {
    pageup: { key: "PageUp", code: "PageUp", keyCode: 33 },
    pagedown: { key: "PageDown", code: "PageDown", keyCode: 34 },
    esc: { key: "Escape", code: "Escape", keyCode: 27 },
    up: { key: "ArrowUp", code: "ArrowUp", keyCode: 38 },
    down: { key: "ArrowDown", code: "ArrowDown", keyCode: 40 },
    left: { key: "ArrowLeft", code: "ArrowLeft", keyCode: 37 },
    right: { key: "ArrowRight", code: "ArrowRight", keyCode: 39 },
  };

  function dispatchKey(type, name) {
    const k = KEYS[name];
    const ev = new KeyboardEvent(type, {
      key: k.key,
      code: k.code,
      bubbles: true,
      cancelable: true,
      composed: true,
      view: window,
    });
    // keyCode and which are absent from KeyboardEventInit, so the
    // constructor leaves them at 0. Plenty of code - Emscripten's own key
    // handling included - still reads them, so define them by hand.
    for (const prop of ["keyCode", "which"]) {
      Object.defineProperty(ev, prop, { get: () => k.keyCode });
    }
    gepad.target().dispatchEvent(ev);
  }

  gepad.keyDown = (name) => dispatchKey("keydown", name);
  gepad.keyUp = (name) => dispatchKey("keyup", name);
  gepad.tapKey = (name) => {
    dispatchKey("keydown", name);
    dispatchKey("keyup", name);
  };
})();
