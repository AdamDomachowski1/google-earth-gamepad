# gepad — browser

Fly the Google Earth flight simulator with a gamepad, in Chrome. No Python,
no SDL, no Accessibility permission, no OS-specific code — the Gamepad API
reads the pad and the page receives synthetic pointer and key events.

Since June 2026 the flight simulator lives in the web build too, with the
same flight model the desktop app exposes: roll and pitch from the mouse,
thrust from Page Up/Down. So this does everything the macOS port does, on
every platform Chrome runs on.

## Install

Nothing to build — the folder loads as it stands.

1. Open `chrome://extensions` (paste it in the address bar; the menu route
   is ⋮ → Extensions → Manage Extensions).
2. Turn on **Developer mode**, top right.
3. Click **Load unpacked** and pick this `extension/` folder — the one with
   `manifest.json` directly inside it, not the repository root:

   ```
   ~/Desktop/google-earth-gamepad/extension
   ```

4. Optional: click the puzzle-piece icon in the toolbar and pin **gepad**,
   so the settings panel is one click away.

The extension only ever runs on `earth.google.com`; it has no access to any
other site and asks for no permission beyond storing your settings.

**After editing any file** press the ↻ reload button on the gepad card in
`chrome://extensions`, then reload the Earth tab. Content scripts are
injected at page load, so the tab reload is the half people forget.

If something misbehaves, the content script logs to the Earth tab's own
console (F12); the popup has a separate console, reached by right-clicking
inside it → Inspect.

## macOS: let Chrome see the pad

**System Settings → Privacy & Security → Input Monitoring → add Google
Chrome**, then quit and reopen Chrome.

Do this before anything else. Without it Chrome sees no gamepad at all —
`navigator.getGamepads()` stays empty, the HUD sits on `NO PAD`, and every
online gamepad tester comes up blank too. macOS gates `IOHIDManager` behind
this permission, and although the wording only mentions keyboards, it covers
every HID device, controllers included.

The confusing part is that the pad is plainly working: the desktop port in
`../src/gepad` still flies fine, because SDL supports both the raw HID path
and Apple's GameController framework and quietly falls back to whichever one
it is allowed to use. Chrome only has the gated path, so it comes up empty
while everything else on the machine is happy. macOS 26 tightened this
further, and Chrome has carried a
[separate long-standing Xbox-on-macOS bug](https://issues.chromium.org/issues/400455006)
for years — so a pad that works everywhere else is no evidence at all that
Chrome can see it.

## Fly

1. `earth.google.com` → **Explore Earth** → **Tools** → **Flight simulator**
2. Press any button on the pad so Chrome reveals it (the API hides gamepads
   until the page has seen one press). The HUD, bottom left, stops saying
   `NO PAD`.
3. **D-pad up** arms. Fly.

| Pad | Action |
|---|---|
| Left stick | roll / pitch (yoke, self-centring) |
| RT / LT | thrust up / down (Page Up/Down, held) |
| A | left click |
| View / Back | Escape |
| D-pad up | arm / disarm |
| D-pad right | swap yoke between mouse and arrow keys |

The physical mouse is never touched, so the cursor stays yours — that is why
there is no cursor mode here, and no radius calibration either: the canvas
reports its own size, so the yoke cannot leave the window. **Escape on the
real keyboard always disarms**, whatever the pad is doing.

Click the toolbar icon for deadzone, yoke travel, inertia and mapping. That
panel also carries a live axis/button readout — the replacement for
`just debug`.

⚠️ Clicking **inside** the simulation toggles Earth between mouse-guided and
keyboard flight controls. If the yoke stops responding after a click, press
A again to toggle mouse control back on.

## If the HUD says NO PAD

In order:

1. **Input Monitoring** — see above. This is the usual answer on macOS.
2. **Press a button on the pad, not the mouse.** Gamepads stay hidden from a
   document until it has seen a gamepad press; a click will not do.
3. **Click the map first.** Chrome gives no gamepads to an unfocused
   document, so the tab must have focus when you press.
4. **Do not diagnose from the console.** Typing into DevTools focuses
   DevTools, so `navigator.getGamepads()` typed by hand reports an empty
   list however well the pad works. Use `gepad.probeIn(5)`, which defers the
   reading long enough to click back into the page and reports
   `document.hasFocus()` alongside it. The HUD is the honest indicator.
5. **Check the popup.** It reads the pad in its own document, so if it fills
   in and the Earth tab does not, the problem is focus rather than the pad.

`gepad.probe()` reports the canvas, its rect, the pads and the current mode.
The content script runs in its own world, so pick `gepad` in DevTools'
context dropdown — in the page's own world there is no `gepad`.

## If the yoke does nothing

Synthetic events carry `isTrusted: false`. Ordinary listeners receive them
regardless, so this should not matter — but Earth is a WebAssembly canvas
app and cannot be inspected from outside. Two fallbacks, in order:

1. **D-pad right** switches the yoke to Earth's arrow keys. If thrust works
   but the yoke does not, keyboard events land and pointer events do not.
2. If neither lands, the fix is a `chrome.debugger` build driving CDP's
   `Input.dispatchMouseEvent`, whose events are genuinely trusted. Only
   `src/input.js` would change; it is the only file that talks to the page.

## Layout

- `src/config.js` — mapping, tuning, and the storage bridge to the popup
- `src/input.js` — synthetic pointer/keyboard events (the `macinput.py` role)
- `src/pad.js` — pad reading, deadzone, yoke inertia, held-key state
- `src/hud.js` — the on-screen readout, in a shadow root
- `src/main.js` — arm/disarm and the frame loop
- `popup.html` / `popup.js` — settings and the live pad readout
