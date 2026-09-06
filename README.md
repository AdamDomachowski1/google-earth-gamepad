# gepad

Fly the Google Earth flight simulator with an Xbox controller on macOS.

Google Earth never touches the gamepad — the script reads it via SDL
(pygame) and synthesizes mouse/keyboard events through Quartz, so the
crash-prone HID path in `libgoogleearth_pro` never runs.

**Google Earth Pro (desktop) only.** The flight simulator lives in Earth
Pro; the browser version has no simulator, so neither the thrust keys nor
the mouse-flown yoke do anything there.

## Requirements

- macOS, [uv](https://docs.astral.sh/uv/), [just](https://just.systems/)
- Permissions: System Settings → Privacy & Security → Accessibility
  → add Terminal (or the IDE you run it from)

## Usage

```sh
just install       # once: uv sync
just check         # is the gamepad visible?
just debug         # live view of axis/button numbers (for mapping)
just fly           # start (opens in cursor mode)
```

1. Open the flight simulator (Google Earth Pro: Cmd+Opt+A, joystick
   support **unchecked**).
2. `just fly`. The pad starts in **cursor mode** — steer with the left
   stick and press **A** to click into the map window.
3. **D-pad UP** switches to **flight mode** (and back). Exit: Ctrl+C.

## Modes

**Cursor mode** (the default) — the pad is an ordinary mouse: the left
stick moves the cursor freely at `CURSOR_SPEED` px/s. No flight keys are
sent, so this is where you click into the map window or out of a dialog.

**Flight mode** — the cursor is pinned to the center of the display and
the left stick deflects it like a yoke; releasing it returns to center.
This is what Earth reads as roll and pitch.

A is a left click in **both** modes, so you can grab the map window back
without dropping out of flight mode.

## Calibrating the yoke

The yoke's travel — `RADIUS`, how far the cursor swings from the center at
full stick deflection — has to fit inside the Earth window, and the edge
you have least room toward is what limits it. Rather than guessing a
number, measure it:

1. Stay in **cursor mode** (the pad starts there).
2. Drive the cursor toward the tightest edge, as far from the center as
   you consider safe.
3. Press **d-pad LEFT**. The distance from the center of the display to
   the cursor becomes the new radius, and it is printed in the terminal.

It applies immediately, so switch to flight mode and try it. The value
lasts for that run; to keep it, copy the printed number into `RADIUS` in
`config.py`. A press closer than `MIN_RADIUS` (20 px) to the center is
ignored as a stray press.

## Mapping

Edit `src/gepad/config.py` - axis and button numbers, keycodes,
`DEADZONE`, `RADIUS` (sensitivity) and `INVERT_PITCH`. Run `just debug`
to read off the numbers your pad reports.

| Pad | Flight mode | Cursor mode |
|---|---|---|
| Left stick | roll / pitch (yoke, centered) | moves the cursor |
| RT / LT | thrust up / down (Page Up/Down, held) | — |
| A | left mouse click | left mouse click |
| "ARM" / View | Escape | Escape |
| D-pad up | switch modes | switch modes |
| D-pad left | — | calibrate the yoke radius |

That is the entire flight model Earth exposes: roll and pitch from the
mouse, thrust from Page Up/Down. There is no rudder, no flaps, no brakes
and no landing gear to bind.

⚠️ Clicking **inside** the simulation toggles Earth between mouse-guided
and keyboard flight controls. If the yoke stops responding after a click,
press A again to toggle mouse control back on.

In flight mode the cursor follows the stick directly: `RADIUS` px from the
center of the display at full deflection — see **Calibrating the yoke**
above. Set `INVERT_PITCH = True` in `config.py` for pull-back-to-climb.

`BTN_ESC` is set to button 4 (View/Back on the SDL2 Xbox layout). If the
button you want sits elsewhere on your pad, run `just debug`, press it,
and put its number there.

## Layout

- `config.py` - all mapping and tuning constants
- `macinput.py` - the Quartz layer (synthetic mouse/keyboard events)
- `main.py` - pad reading, the two modes and the main loop
