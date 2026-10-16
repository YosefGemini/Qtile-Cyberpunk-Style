##########################
# title: Qtile config.py #
# author: YosefGemini    #
##########################
# Entry point only. Each part of the configuration now lives in its own
# module under modules/ so the file stays readable and maintainable.
#   settings.py  - keys, paths, backend detection
#   theme.py     - colours, fonts, layout theme
#   functions.py - helper callbacks
#   keys.py      - key and mouse bindings
#   groups.py    - workspaces
#   layouts.py   - layouts and floating rules
#   widgets.py   - bar widgets
#   screens.py   - screen generation + monitor arrangement
#   hooks.py     - startup hooks and window rules

import modules.hooks  # noqa: F401  (importing registers the hooks)
from modules.groups import groups  # noqa: F401
from modules.keys import keys, mouse  # noqa: F401
from modules.layouts import floating_layout, layouts  # noqa: F401
from modules.screens import generate_screens  # noqa: F401
from modules.theme import widget_defaults  # noqa: F401

dgroups_key_binder = None
dgroups_app_rules = []

follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
auto_fullscreen = True
focus_on_window_activation = "smart"

# Keep screens in sync when monitors are plugged/unplugged or rearranged.
reconfigure_screens = True

wmname = "LG3D"
main = None
