"""Startup hooks and window rules."""

import subprocess

from libqtile import hook, qtile

from modules.settings import backend_is_wayland, home, is_main_output

floating_types = ["notification", "toolbar", "splash", "dialog"]


@hook.subscribe.startup_once
def start_once():
    if not backend_is_wayland():
        from modules.screens import arrange_monitors

        arrange_monitors()
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


@hook.subscribe.screens_reconfigured
def focus_main_screen():
    """Focus the laptop panel after screens are (re)configured."""
    if not qtile.screens:
        return
    for screen in qtile.screens:
        output = getattr(screen, "output", None)
        port = getattr(output, "port", None)
        if is_main_output(port):
            try:
                if qtile.current_screen is not screen:
                    qtile.focus_screen(screen.index, warp=False)
            except Exception:
                pass
            return
