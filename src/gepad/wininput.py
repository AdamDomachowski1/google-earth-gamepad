"""Windows layer: synthetic mouse and keyboard events (SendInput).

The mac backend posts Quartz events; here the equivalent is SendInput,
which enters the same queue a real mouse and keyboard do. Cursor moves
go in as absolute virtual-desktop coordinates so they land correctly on
a multi-monitor setup.
"""

import ctypes
import time
from ctypes import wintypes

_user32 = ctypes.WinDLL("user32", use_last_error=True)

_ULONG_PTR = (ctypes.c_uint64 if ctypes.sizeof(ctypes.c_void_p) == 8
              else ctypes.c_ulong)

_INPUT_MOUSE = 0
_INPUT_KEYBOARD = 1

_MOUSEEVENTF_MOVE = 0x0001
_MOUSEEVENTF_LEFTDOWN = 0x0002
_MOUSEEVENTF_LEFTUP = 0x0004
_MOUSEEVENTF_ABSOLUTE = 0x8000
_MOUSEEVENTF_VIRTUALDESK = 0x4000

_KEYEVENTF_EXTENDEDKEY = 0x0001
_KEYEVENTF_KEYUP = 0x0002
_KEYEVENTF_SCANCODE = 0x0008

_MAPVK_VK_TO_VSC = 0

# Keys that a real keyboard sends with the extended-key prefix. Page
# Up/Down are among them, and the flight simulator's thrust is bound to
# exactly those, so getting this wrong is not a corner case.
_EXTENDED = {0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28, 0x2D, 0x2E}

_MONITOR_DEFAULTTONULL = 0
_MONITOR_DEFAULTTOPRIMARY = 1

_SM_XVIRTUALSCREEN = 76
_SM_YVIRTUALSCREEN = 77
_SM_CXVIRTUALSCREEN = 78
_SM_CYVIRTUALSCREEN = 79


class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG),
                ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", _ULONG_PTR)]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", _ULONG_PTR)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", _MOUSEINPUT), ("ki", _KEYBDINPUT)]


class _INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]


class _RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


class _MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", _RECT),
                ("rcWork", _RECT), ("dwFlags", wintypes.DWORD)]


_user32.SendInput.argtypes = (wintypes.UINT, ctypes.POINTER(_INPUT),
                              ctypes.c_int)
_user32.SendInput.restype = wintypes.UINT
_user32.GetCursorPos.argtypes = (ctypes.POINTER(wintypes.POINT),)
_user32.MonitorFromPoint.argtypes = (wintypes.POINT, wintypes.DWORD)
_user32.MonitorFromPoint.restype = wintypes.HANDLE
_user32.GetMonitorInfoW.argtypes = (wintypes.HANDLE,
                                    ctypes.POINTER(_MONITORINFO))
_user32.MapVirtualKeyW.argtypes = (wintypes.UINT, wintypes.UINT)
_user32.MapVirtualKeyW.restype = wintypes.UINT


def _set_dpi_aware():
    """Ask for real pixels.

    Without this the process is virtualized on a scaled display and the
    cursor coordinates we read back do not match the ones we write, so
    the yoke would sit off-center."""
    ctx = getattr(_user32, "SetProcessDpiAwarenessContext", None)
    if ctx and ctx(ctypes.c_void_p(-4)):    # per-monitor aware v2
        return
    try:
        ctypes.WinDLL("shcore").SetProcessDpiAwareness(2)
        return
    except (AttributeError, OSError):
        pass
    _user32.SetProcessDPIAware()


_set_dpi_aware()


def _send(*inputs):
    arr = (_INPUT * len(inputs))(*inputs)
    _user32.SendInput(len(inputs), arr, ctypes.sizeof(_INPUT))


def cursor_position():
    p = wintypes.POINT()
    _user32.GetCursorPos(ctypes.byref(p))
    return float(p.x), float(p.y)


def _bounds_at(x, y, default=_MONITOR_DEFAULTTONULL):
    """(left, top, width, height) of the monitor containing (x, y)."""
    mon = _user32.MonitorFromPoint(
        wintypes.POINT(int(x), int(y)), default)
    if not mon:
        return None
    info = _MONITORINFO()
    info.cbSize = ctypes.sizeof(_MONITORINFO)
    if not _user32.GetMonitorInfoW(mon, ctypes.byref(info)):
        return None
    r = info.rcMonitor
    return (float(r.left), float(r.top),
            float(r.right - r.left), float(r.bottom - r.top))


def _primary_bounds():
    return _bounds_at(0, 0, _MONITOR_DEFAULTTOPRIMARY)


def display_center_at(x, y):
    """Center of the display containing point (x, y)."""
    left, top, w, h = _bounds_at(x, y) or _primary_bounds()
    return left + w / 2.0, top + h / 2.0


def clamp_to_displays(x, y, from_x, from_y):
    """Keep (x, y) on a real display.

    A point on any monitor passes through unchanged, so the cursor can
    still cross between them; one that landed in dead space gets clamped
    to the monitor it came from."""
    if _bounds_at(x, y):
        return x, y
    left, top, w, h = _bounds_at(from_x, from_y) or _primary_bounds()
    return (min(max(x, left), left + w - 1.0),
            min(max(y, top), top + h - 1.0))


def move_mouse(x, y):
    vx = _user32.GetSystemMetrics(_SM_XVIRTUALSCREEN)
    vy = _user32.GetSystemMetrics(_SM_YVIRTUALSCREEN)
    vw = _user32.GetSystemMetrics(_SM_CXVIRTUALSCREEN)
    vh = _user32.GetSystemMetrics(_SM_CYVIRTUALSCREEN)
    # Absolute mouse input is normalized to 0..65535 across the whole
    # virtual desktop, not to pixels.
    nx = round((x - vx) * 65535.0 / max(vw - 1, 1))
    ny = round((y - vy) * 65535.0 / max(vh - 1, 1))
    _send(_INPUT(type=_INPUT_MOUSE, mi=_MOUSEINPUT(
        dx=int(nx), dy=int(ny), mouseData=0,
        dwFlags=(_MOUSEEVENTF_MOVE | _MOUSEEVENTF_ABSOLUTE
                 | _MOUSEEVENTF_VIRTUALDESK),
        time=0, dwExtraInfo=0)))


def click_left():
    """Left mouse click wherever the cursor is right now."""
    for flag in (_MOUSEEVENTF_LEFTDOWN, _MOUSEEVENTF_LEFTUP):
        _send(_INPUT(type=_INPUT_MOUSE, mi=_MOUSEINPUT(
            dx=0, dy=0, mouseData=0, dwFlags=flag, time=0, dwExtraInfo=0)))
        time.sleep(0.01)


def _post_key(code, down):
    flags = 0 if down else _KEYEVENTF_KEYUP
    if code in _EXTENDED:
        flags |= _KEYEVENTF_EXTENDEDKEY
    _send(_INPUT(type=_INPUT_KEYBOARD, ki=_KEYBDINPUT(
        wVk=code, wScan=_user32.MapVirtualKeyW(code, _MAPVK_VK_TO_VSC),
        dwFlags=flags, time=0, dwExtraInfo=0)))


def key_down(code):
    _post_key(code, True)


def key_up(code):
    _post_key(code, False)


def tap_key(code, shift=False):
    if shift:
        _post_key(0x10, True)       # VK_SHIFT
    _post_key(code, True)
    time.sleep(0.004)
    _post_key(code, False)
    if shift:
        _post_key(0x10, False)
