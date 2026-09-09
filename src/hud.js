/* gepad - the on-screen readout.
 *
 * It lives in a shadow root attached to <html> so that neither Earth's
 * stylesheet nor ours can reach into the other, and it never takes pointer
 * events, so it cannot swallow a click meant for the map. The stick square
 * is the useful part: it shows the filtered yoke, so you can watch the
 * inertia settle and tell a dead pad apart from a dead synthetic-event path.
 */

gepad.Hud = class {
  constructor() {
    this.host = document.createElement("div");
    this.host.style.cssText =
      "position:fixed;left:0;top:0;width:0;height:0;z-index:2147483647;";
    const root = this.host.attachShadow({ mode: "open" });
    root.innerHTML = `
      <style>
        .panel {
          position: fixed; left: 12px; bottom: 12px;
          display: flex; align-items: center; gap: 10px;
          padding: 8px 10px; border-radius: 8px;
          background: rgba(16, 18, 22, 0.82);
          border: 1px solid rgba(255, 255, 255, 0.14);
          color: #e8eaed; pointer-events: none;
          font: 12px/1.35 ui-monospace, SFMono-Regular, Menlo, monospace;
          -webkit-font-smoothing: antialiased;
        }
        .stick {
          position: relative; width: 40px; height: 40px; flex: none;
          border-radius: 5px; background: rgba(255, 255, 255, 0.06);
          border: 1px solid rgba(255, 255, 255, 0.16);
        }
        .dot {
          position: absolute; width: 7px; height: 7px; border-radius: 50%;
          left: 50%; top: 50%; margin: -3.5px 0 0 -3.5px; background: #8ab4f8;
        }
        .text { display: flex; flex-direction: column; gap: 2px; }
        .badge { font-weight: 700; letter-spacing: 0.06em; }
        .on { color: #81c995; }
        .off { color: #9aa0a6; }
        .sub { color: #9aa0a6; white-space: nowrap; }
      </style>
      <div class="panel">
        <div class="stick"><div class="dot"></div></div>
        <div class="text">
          <div class="badge"></div>
          <div class="sub"></div>
        </div>
      </div>`;
    this.panel = root.querySelector(".panel");
    this.dot = root.querySelector(".dot");
    this.badge = root.querySelector(".badge");
    this.sub = root.querySelector(".sub");
    this.last = "";
    (document.body || document.documentElement).appendChild(this.host);
  }

  render({ armed, pad, yokeMode, x, y, throttle }) {
    this.panel.style.display = gepad.cfg.hud ? "" : "none";
    if (!gepad.cfg.hud) return;

    this.dot.style.transform = `translate(${(x * 16).toFixed(1)}px, ${(
      y * 16
    ).toFixed(1)}px)`;

    const state = !pad ? "NO PAD" : armed ? "ARMED" : "OFF";
    // Losing the canvas is the failure that looks exactly like "nothing
    // happens", so it gets said out loud rather than left to the console.
    const detail = !pad
      ? "press a button on the pad"
      : !gepad.hasCanvas()
        ? "no map canvas found"
        : armed
          ? `${yokeMode === "mouse" ? "yoke" : "keys"} · thrust ${throttle}`
          : "d-pad up to arm";
    const key = `${state}|${detail}`;
    if (key === this.last) return;
    this.last = key;

    this.badge.textContent = state;
    this.badge.className = `badge ${armed ? "on" : "off"}`;
    this.sub.textContent = detail;
  }
};
