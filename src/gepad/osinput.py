"""Picks the input backend for the current OS.

Both backends expose the same names, so nothing above this module has to
know which platform it is running on.
"""

import sys

if sys.platform == "darwin":
    from .macinput import (clamp_to_displays, click_left, cursor_position,
                           display_center_at, key_down, key_up, move_mouse,
                           tap_key)
elif sys.platform == "win32":
    from .wininput import (clamp_to_displays, click_left, cursor_position,
                           display_center_at, key_down, key_up, move_mouse,
                           tap_key)
else:
    raise ImportError(
        f"gepad has no input backend for {sys.platform!r} - "
        "macOS and Windows only.")

__all__ = ["clamp_to_displays", "click_left", "cursor_position",
           "display_center_at", "key_down", "key_up", "move_mouse", "tap_key"]
