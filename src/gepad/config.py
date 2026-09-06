"""Gamepad mapping configuration.

SDL numbers the axes and buttons of the same pad differently depending on
the backend - IOKit on macOS, XInput on Windows - so the platform-specific
ones are picked below. If yours differ, run `just debug` and adjust.

Earth's flight simulator only takes thrust (Page Up/Down) from the
keyboard; roll and pitch come from the mouse. There is nothing else to
bind - no rudder, flaps, brakes or landing gear.
"""

import sys

_WINDOWS = sys.platform == "win32"

AX_ROLL = 0        # left stick X  -> roll (moves the cursor)
AX_PITCH = 1       # left stick Y  -> pitch (moves the cursor)

if _WINDOWS:
    AX_LT = 2      # left trigger  -> decrease thrust
    AX_RT = 5      # right trigger -> increase thrust
    BTN_ESC = 6    # Back/View
else:
    AX_LT = 4
    AX_RT = 5
    BTN_ESC = 4    # "ARM"/View

BTN_A = 0

# A is a left mouse click, in flight mode as well as cursor mode.
# Add more buttons to the tuple if you want a second one.
CLICK_BUTTONS = (BTN_A,)

# D-pad. In SDL it is usually a "hat" - that is what XInput reports on
# Windows - but plenty of pads (the Xbox Series controller on macOS among
# them) report it as ordinary buttons instead, so both are supported. The
# numbers below are only the button fallback; check with `just debug`.
#   up   -> switch between flight mode and cursor mode
#   left -> calibrate RADIUS (cursor mode)
BTN_DPAD_UP = 11
BTN_DPAD_DOWN = 12
BTN_DPAD_LEFT = 13

DEADZONE = 0.12
RADIUS = 260       # px from the screen center at full stick deflection.
                   # Starting value only - d-pad LEFT recalibrates it live.
MIN_RADIUS = 20    # a calibration smaller than this is a stray press
CURSOR_SPEED = 900 # px/s at full stick deflection, cursor mode
INVERT_PITCH = False
RATE_HZ = 60

# Yoke inertia, seconds (flight mode). Arcade-tight; raise SMOOTH_OUT
# toward 0.5 for a heavier plane, set both to 0 for an instant yoke.
SMOOTH_IN = 0.03   # deflecting away from the center
SMOOTH_OUT = 0.10  # relaxing back toward it

# Keycodes: Windows virtual-key codes, or macOS virtual keycodes.
if _WINDOWS:
    KEY = {
        "pageup": 0x21,    # increase thrust
        "pagedown": 0x22,  # decrease thrust
        "esc": 0x1B,
    }
else:
    KEY = {
        "pageup": 116,
        "pagedown": 121,
        "esc": 53,
    }
