"""Quartz layer: synthetic mouse and keyboard events (macOS)."""

import time

import Quartz

_SRC = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStateHIDSystemState)


def cursor_position():
    ev = Quartz.CGEventCreate(None)
    p = Quartz.CGEventGetLocation(ev)
    return p.x, p.y


def _bounds_at(x, y):
    """Bounds of the display containing point (x, y), or None."""
    err, ids, cnt = Quartz.CGGetDisplaysWithPoint((x, y), 4, None, None)
    return Quartz.CGDisplayBounds(ids[0]) if err == 0 and cnt else None


def display_center_at(x, y):
    """Center of the display containing point (x, y)."""
    b = _bounds_at(x, y) or Quartz.CGDisplayBounds(Quartz.CGMainDisplayID())
    return (b.origin.x + b.size.width / 2.0,
            b.origin.y + b.size.height / 2.0)


def clamp_to_displays(x, y, from_x, from_y):
    """Keep (x, y) on a real display.

    A point on any display passes through unchanged, so the cursor can
    still cross between monitors; one that landed in dead space gets
    clamped to the display it came from."""
    if _bounds_at(x, y):
        return x, y
    b = _bounds_at(from_x, from_y) or Quartz.CGDisplayBounds(
        Quartz.CGMainDisplayID())
    return (min(max(x, b.origin.x), b.origin.x + b.size.width - 1.0),
            min(max(y, b.origin.y), b.origin.y + b.size.height - 1.0))


def move_mouse(x, y):
    ev = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventMouseMoved, (x, y), Quartz.kCGMouseButtonLeft)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)


def click_left():
    """Left mouse click wherever the cursor is right now."""
    x, y = cursor_position()
    for kind in (Quartz.kCGEventLeftMouseDown, Quartz.kCGEventLeftMouseUp):
        ev = Quartz.CGEventCreateMouseEvent(
            None, kind, (x, y), Quartz.kCGMouseButtonLeft)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)
        time.sleep(0.01)


def _post_key(code, down):
    ev = Quartz.CGEventCreateKeyboardEvent(_SRC, code, down)
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)


def key_down(code):
    _post_key(code, True)


def key_up(code):
    _post_key(code, False)


def tap_key(code, shift=False):
    flags = Quartz.kCGEventFlagMaskShift if shift else 0
    for down in (True, False):
        ev = Quartz.CGEventCreateKeyboardEvent(_SRC, code, down)
        if flags:
            Quartz.CGEventSetFlags(ev, flags)
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, ev)
        time.sleep(0.004)
