"""gepad - fly the Google Earth flight simulator with an Xbox pad (macOS).

Google Earth never touches the gamepad. The script reads it via SDL (pygame)
and synthesizes mouse/keyboard events through Quartz, so the crash-prone HID
path in libgoogleearth_pro never runs.

Earth's simulator takes roll and pitch from the mouse and thrust from
Page Up/Down; that is the whole flight model, so that is all we send.

Usage:
    1. Google Earth Pro -> flight simulator (Cmd+Opt+A), joystick UNCHECKED.
    2. just fly   (or: just debug -> live view of axes and buttons)
    3. The pad starts in cursor mode: left stick moves the cursor.
       A is a left click, in both modes.
    4. D-pad UP switches to flight mode (and back). Exit: Ctrl+C.

Mapping, deadzone and sensitivity live in config.py.
"""

import math
import sys
import time

import pygame

from . import config as cfg
from .macinput import (clamp_to_displays, click_left, cursor_position,
                       display_center_at, key_down, key_up, move_mouse,
                       tap_key)


# --- pad reading ------------------------------------------------------

def dead(v, dz=cfg.DEADZONE):
    if abs(v) < dz:
        return 0.0
    return (abs(v) - dz) / (1.0 - dz) * (1.0 if v > 0 else -1.0)


def pressed(js, btn):
    return btn < js.get_numbuttons() and bool(js.get_button(btn))


def dpad_x(js):
    """D-pad horizontal: 1 right, -1 left, 0 centered."""
    for h in range(js.get_numhats()):
        x = js.get_hat(h)[0]
        if x:
            return x
    return -1 if pressed(js, cfg.BTN_DPAD_LEFT) else 0


def dpad_y(js):
    """D-pad vertical: 1 up, -1 down, 0 centered.

    Reads the SDL hat when the pad has one, and falls back to the d-pad
    buttons when it does not - the Xbox Series controller on macOS
    reports no hat at all."""
    for h in range(js.get_numhats()):
        y = js.get_hat(h)[1]
        if y:
            return y
    return pressed(js, cfg.BTN_DPAD_UP) - pressed(js, cfg.BTN_DPAD_DOWN)


class KeyHolder:
    """Holds one of two keys down while the axis is deflected."""

    def __init__(self, key_pos, key_neg, threshold=0.08):
        self.key_pos = key_pos
        self.key_neg = key_neg
        self.threshold = threshold
        self.held = None

    def update(self, amount):
        want = None
        if amount > self.threshold:
            want = self.key_pos
        elif amount < -self.threshold:
            want = self.key_neg
        if want == self.held:
            return
        if self.held is not None:
            key_up(self.held)
        if want is not None:
            key_down(want)
        self.held = want

    def release(self):
        if self.held is not None:
            key_up(self.held)
            self.held = None


# --- modes ------------------------------------------------------------

def run_debug(js):
    print("Move the axes and press buttons. Ctrl+C to quit.\n")
    while True:
        pygame.event.clear()
        axes = [round(js.get_axis(i), 2) for i in range(js.get_numaxes())]
        btns = [i for i in range(js.get_numbuttons()) if js.get_button(i)]
        hats = [js.get_hat(i) for i in range(js.get_numhats())]
        print(f"\raxes={axes}  pressed={btns}  dpad={hats}      ",
              end="", flush=True)
        time.sleep(0.08)


def run_fly(js):
    """Two modes, toggled with d-pad UP.

    Flight mode: the cursor is pinned to the center of the display and the
    left stick deflects it like a yoke, so Earth reads it as roll/pitch.
    Cursor mode (the default, and where the pad starts): the left stick
    drives the cursor freely across the screen. A is a left click in
    both modes, and d-pad LEFT calibrates the yoke radius."""
    cx, cy = display_center_at(*cursor_position())
    radius = cfg.RADIUS
    # RT -> Page Up (faster), LT -> Page Down (slower); the key stays
    # held down for as long as the trigger is pressed.
    throttle = KeyHolder(cfg.KEY["pageup"], cfg.KEY["pagedown"])
    prev_dpad = 0
    prev_dpad_x = 0
    prev_esc = False
    prev_click = False
    flying = False
    last = time.perf_counter()
    period = 1.0 / cfg.RATE_HZ

    print(f"Ready. Screen center: ({cx:.0f}, {cy:.0f}). Ctrl+C to quit.")
    print("Starting in CURSOR mode - left stick moves the cursor, "
          "A is a left click. D-pad UP switches to flight mode, "
          "D-pad LEFT calibrates the yoke radius.")

    try:
        while True:
            now = time.perf_counter()
            dt = now - last
            last = now
            # clear() pumps SDL and keeps the queue from growing all flight
            pygame.event.clear()

            # D-pad up switches modes; it fires once per press and works in
            # both, so the pad never needs the trackpad to get going.
            d = dpad_y(js)
            if d == 1 and prev_dpad != 1:
                flying = not flying
                if flying:
                    # center = middle of the display the cursor is on
                    cx, cy = display_center_at(*cursor_position())
                    print(f">>> FLIGHT mode - center ({cx:.0f}, {cy:.0f})",
                          flush=True)
                else:
                    throttle.release()
                    print(">>> CURSOR mode - left stick moves the cursor",
                          flush=True)
            prev_dpad = d

            # D-pad left calibrates the yoke: whatever the cursor is at
            # is taken as full deflection, so the yoke never travels
            # further from the center than the user just proved is safe.
            dx_pad = dpad_x(js)
            if dx_pad == -1 and prev_dpad_x != -1:
                if flying:
                    print(">>> calibration works in CURSOR mode only - "
                          "d-pad UP first", flush=True)
                else:
                    x, y = cursor_position()
                    ox, oy = display_center_at(x, y)
                    r = math.hypot(x - ox, y - oy)
                    if r < cfg.MIN_RADIUS:
                        print(f">>> calibration ignored - only {r:.0f} px "
                              f"from the center (minimum {cfg.MIN_RADIUS})",
                              flush=True)
                    else:
                        radius = r
                        print(f">>> RADIUS calibrated to {radius:.0f} px. Put "
                              f"RADIUS = {radius:.0f} in config.py to keep it.",
                              flush=True)
            prev_dpad_x = dx_pad

            # Escape works in both modes - it leaves the simulator and
            # closes Earth's dialogs.
            esc = pressed(js, cfg.BTN_ESC)
            if esc and not prev_esc:
                tap_key(cfg.KEY["esc"])
            prev_esc = esc

            # A clicks in both modes, so you can grab the map window
            # without dropping out of flight mode.
            click = any(pressed(js, b) for b in cfg.CLICK_BUTTONS)
            if click and not prev_click:
                click_left()
            prev_click = click

            if flying:
                pitch = dead(js.get_axis(cfg.AX_PITCH))
                if cfg.INVERT_PITCH:
                    pitch = -pitch
                move_mouse(cx + dead(js.get_axis(cfg.AX_ROLL)) * radius,
                           cy + pitch * radius)

                rt = (js.get_axis(cfg.AX_RT) + 1.0) / 2.0
                lt = (js.get_axis(cfg.AX_LT) + 1.0) / 2.0
                throttle.update(rt if rt > lt else -lt)
            else:
                # Cursor mode: the stick is a velocity, not a position, so
                # you can reach anything on the screen.
                dx = dead(js.get_axis(cfg.AX_ROLL))
                dy = dead(js.get_axis(cfg.AX_PITCH))
                if dx or dy:
                    x, y = cursor_position()
                    move_mouse(*clamp_to_displays(
                        x + dx * cfg.CURSOR_SPEED * dt,
                        y + dy * cfg.CURSOR_SPEED * dt, x, y))

            sleep = period - (time.perf_counter() - now)
            if sleep > 0:
                time.sleep(sleep)
    finally:
        throttle.release()


def main():
    debug = "--debug" in sys.argv[1:]
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        sys.exit("No gamepad found. Pair it and check in Game Controllers.")

    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"Pad: {js.get_name()}  axes={js.get_numaxes()} "
          f"buttons={js.get_numbuttons()}")

    try:
        run_debug(js) if debug else run_fly(js)
    except KeyboardInterrupt:
        print("\nBye.")


if __name__ == "__main__":
    main()
