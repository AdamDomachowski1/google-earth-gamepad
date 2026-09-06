"""Gamepad mapping configuration. Axis/button numbers follow the SDL2
standard for Xbox controllers. If yours differ, run `just debug` and adjust.

Earth's flight simulator only takes thrust (Page Up/Down) from the
keyboard; roll and pitch come from the mouse. There is nothing else to
bind - no rudder, flaps, brakes or landing gear.
"""

AX_ROLL = 0        # left stick X  -> roll (moves the cursor)
AX_PITCH = 1       # left stick Y  -> pitch (moves the cursor)
AX_LT = 4          # left trigger  -> decrease thrust
AX_RT = 5          # right trigger -> increase thrust

BTN_A = 0
BTN_ESC = 4        # "ARM"/View. Check the number with `just debug`.

# A is a left mouse click, in flight mode as well as cursor mode.
# Add more buttons to the tuple if you want a second one.
CLICK_BUTTONS = (BTN_A,)

# D-pad. In SDL it is usually a "hat", but plenty of pads (the Xbox Series
# controller on macOS among them) report it as ordinary buttons instead, so
# both are supported. If your numbers differ, check them with `just debug`.
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

# macOS virtual keycodes
KEY = {
    "pageup": 116,     # increase thrust
    "pagedown": 121,   # decrease thrust
    "esc": 53,
}
