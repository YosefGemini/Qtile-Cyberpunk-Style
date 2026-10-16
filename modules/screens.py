"""Screen generation and monitor auto-arrangement.

Instead of hardcoding three ``Screen`` objects (which caused the bar to land
on the wrong monitor when the output order changed), we use qtile's
``generate_screens`` hook. It is called every time the set of monitors
changes, so one bar is always created for each *real* output.

- The laptop panel (``eDP-*``/``LVDS-*``/...) is treated as the main screen
  and is the only one that gets the system tray.
- If only one monitor is connected, it automatically becomes the main screen.
- On X11 the monitors are laid out with ``xrandr`` at startup (best mode per
  output, laptop as primary, DisplayPort panels to the left and HDMI panels
  to the right).

Screen objects are cached per output so that a screen reconfigure reuses the
same objects instead of building duplicates. Without the cache qtile leaks
the previous system tray widget and raises
``ConfigError: Only one Systray can be used.``
"""

import re
import subprocess

from libqtile import bar
from libqtile.config import Screen

from modules.settings import is_main_output
from modules.widgets import build_widgets

BAR_SIZE = 30
BAR_BACKGROUND = "#00000000"

# output identity -> Screen (kept stable across reconfigures)
_screen_cache = {}


def _make_screen(show_tray):
    return Screen(
        top=bar.Bar(
            widgets=build_widgets(show_tray=show_tray),
            size=BAR_SIZE,
            background=BAR_BACKGROUND,
        )
    )


def generate_screens(outputs):
    """Build one Screen per connected output (called by qtile)."""
    if not outputs:
        screen = _screen_cache.get("__default__")
        if screen is None:
            screen = _make_screen(show_tray=True)
            _screen_cache["__default__"] = screen
        return [screen]

    has_main = any(is_main_output(o.port) for o in outputs)

    screens = []
    for i, output in enumerate(outputs):
        key = output.port or "__index_%d__" % i
        screen = _screen_cache.get(key)
        if screen is None:
            main = is_main_output(output.port) if has_main else (i == 0)
            screen = _make_screen(show_tray=main)
            _screen_cache[key] = screen
        screens.append(screen)
    return screens


def _connected_outputs():
    try:
        out = subprocess.check_output(["xrandr", "--query"], text=True, stderr=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []
    return re.findall(r"^(\S+) connected", out, flags=re.MULTILINE)


def arrange_monitors():
    """Arrange connected X11 monitors with xrandr.

    Laptop panel becomes primary, ``DP-*`` outputs go to the left and the
    remaining external outputs to the right, each at its preferred mode.
    No-op on Wayland or when fewer than two outputs are connected.
    """
    ports = _connected_outputs()
    if len(ports) < 2:
        return

    mains = [p for p in ports if is_main_output(p)]
    main = mains[0] if mains else ports[0]
    others = [p for p in ports if p != main]

    left = [p for p in others if p.startswith("DP")]
    right = [p for p in others if p not in left]

    args = ["xrandr", "--output", main, "--auto", "--primary"]
    prev = main
    for port in left:
        args += ["--output", port, "--auto", "--left-of", prev]
        prev = port
    prev = main
    for port in right:
        args += ["--output", port, "--auto", "--right-of", prev]
        prev = port

    try:
        subprocess.call(args)
    except FileNotFoundError:
        pass
