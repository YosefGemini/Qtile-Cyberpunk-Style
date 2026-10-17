"""Startup hooks and window rules."""

import subprocess

from libqtile import hook, qtile

from modules import monitor_layout as ml
from modules.settings import backend_is_wayland, home

floating_types = ["notification", "toolbar", "splash", "dialog"]


@hook.subscribe.startup_once
def start_once():
    # Apply the saved monitor layout (or the automatic one) and arrange outputs.
    ml.startup_layout()
    subprocess.call([home + "/.config/qtile/scripts/autostart.sh"])


@hook.subscribe.startup
def start_always():
    if not backend_is_wayland():
        subprocess.Popen(["xsetroot", "-cursor_name", "left_ptr"])


@hook.subscribe.client_new
def set_floating(window):
    try:
        if (
            window.window.get_wm_transient_for()
            or window.window.get_wm_type() in floating_types
        ):
            window.floating = True
    except AttributeError:
        pass


def focus_primary():
    outputs = ml.list_outputs()
    if not outputs:
        return
    primary = ml.effective_primary(ml.load_layout(), outputs)
    if not primary:
        return

    by_rect = {
        (info.x, info.y, info.width, info.height): info.name for info in outputs
    }
    for screen in qtile.screens:
        output = getattr(screen, "output", None)
        if output is None:
            continue
        name = output.port
        if not name:
            name = by_rect.get(
                (output.rect.x, output.rect.y, output.rect.width, output.rect.height)
            )
        if name == primary:
            try:
                if qtile.current_screen is not screen:
                    qtile.focus_screen(screen.index, warp=False)
            except Exception:
                pass
            return


@hook.subscribe.screens_reconfigured
def on_screens_reconfigured():
    # Re-apply saved settings only when the set of connected outputs changed.
    ml.on_outputs_changed()
    focus_primary()
