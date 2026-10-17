"""Global settings, paths and backend/session detection."""

import os
import shutil

mod = "mod4"
mod1 = "alt"
mod2 = "control"

home = os.path.expanduser("~")
config_dir = os.path.join(home, ".config", "qtile")

# Persisted monitor layout (see modules/monitor_layout.py).
MONITOR_LAYOUT_FILE = os.path.join(config_dir, "monitor_layout.txt")

# Laptop panel port prefixes, used to pick the "main" screen. Works for both
# X11 (RandR names) and Wayland (wlroots names).
MAIN_OUTPUT_PREFIXES = ("eDP", "LVDS", "DSI", "panel")


def has_xrandr() -> bool:
    return shutil.which("xrandr") is not None


def has_wlr_randr() -> bool:
    return shutil.which("wlr-randr") is not None


def backend_is_wayland() -> bool:
    """Return True when qtile is running on the Wayland backend.

    Falls back to environment variables while the compositor is still
    starting up (e.g. before ``qtile.core`` exists).
    """
    try:
        from libqtile import qtile

        core = getattr(qtile, "core", None)
        if core is not None and getattr(core, "name", None):
            return core.name == "wayland"
    except Exception:
        pass

    if os.environ.get("WAYLAND_DISPLAY"):
        return True
    return os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"


def is_main_output(port) -> bool:
    """True when an output name looks like the built-in laptop panel."""
    port = port or ""
    return any(port.startswith(prefix) for prefix in MAIN_OUTPUT_PREFIXES)
