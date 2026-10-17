"""Screen generation.

Instead of hardcoding three ``Screen`` objects (which caused the bar to land
on the wrong monitor when the output order changed), we use qtile's
``generate_screens`` hook. It is called every time the set of monitors
changes, so one bar is always created for each *real* output.

The system tray is kept on the built-in laptop panel (or the first output when
no laptop panel is connected). The *logical* primary screen used for focus and
ordering is managed by :mod:`modules.monitor_layout`.

Screen objects are cached per output so that a screen reconfigure reuses the
same objects instead of building duplicates. Without the cache qtile leaks the
previous system tray widget and raises
``ConfigError: Only one Systray can be used.``
"""

from libqtile import bar
from libqtile.config import Screen

from modules import monitor_layout as ml
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


def _resolved_names(outputs):
    """Map qtile Outputs to real port names (X11 reports port=None)."""
    infos = ml.list_outputs()
    by_rect = {
        (info.x, info.y, info.width, info.height): info.name for info in infos
    }

    names = []
    for output in outputs:
        name = output.port
        if not name:
            rect = getattr(output, "rect", None)
            if rect is not None:
                name = by_rect.get(
                    (rect.x, rect.y, rect.width, rect.height)
                )
        names.append(name)
    return names


def generate_screens(outputs):
    """Build one Screen per connected output (called by qtile)."""
    if not outputs:
        screen = _screen_cache.get("__default__")
        if screen is None:
            screen = _make_screen(show_tray=True)
            _screen_cache["__default__"] = screen
        return [screen]

    names = _resolved_names(outputs)
    has_laptop = any(is_main_output(name) for name in names if name)

    screens = []
    for index, _output in enumerate(outputs):
        name = names[index]
        key = name or "__index_%d__" % index
        screen = _screen_cache.get(key)
        if screen is None:
            if has_laptop:
                show_tray = is_main_output(name)
            else:
                show_tray = index == 0
            screen = _make_screen(show_tray=show_tray)
            _screen_cache[key] = screen
        screens.append(screen)
    return screens
