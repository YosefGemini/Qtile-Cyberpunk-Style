"""Bar widgets.

The widget set, order, colours, fonts and decorations match the original
configuration. The system tray widget is selected per backend: ``Systray`` on
X11 and ``StatusNotifier`` on Wayland (libqtile's ``Systray`` is X11-only).
"""

from libqtile.lazy import lazy
from qtile_extras import widget
from qtile_extras.widget.decorations import PowerLineDecoration, RectDecoration

from modules.functions import only_app_name
from modules.monitor_widget import MonitorLayout
from modules.settings import backend_is_wayland
from modules.theme import colors


def _tray_widget():
    if backend_is_wayland():
        return widget.StatusNotifier(icon_size=14, padding=4)
    return widget.Systray(icon_size=14, padding=4)


def build_widgets(show_tray=True):
    widgets_list = [
        widget.Sep(
            linewidth=0,
            background=colors[7],
            decorations=[PowerLineDecoration(path="forward_slash")],
        ),
        widget.Image(
            filename="~/.config/qtile/icons/garuda-yellow.svg",
            iconsize=9,
            width=24,  # <-- Añade un ancho fijo para delimitar el espacio
            background=colors[1],
            mouse_callbacks={"Button1": lazy.spawn("jgmenu_run")},
            decorations=[PowerLineDecoration(path="forward_slash")],
        ),
        widget.Sep(
            linewidth=0,
            background=colors[7],
            decorations=[PowerLineDecoration(path="forward_slash")],
        ),
        widget.GroupBox(
            font="RobotoMono Nerd Font Bold",
            fontsize=13,
            margin_y=2,
            margin_x=3,
            padding_y=2,
            padding_x=3,
            borderwidth=3,
            disable_drag=True,
            active=colors[7],
            inactive=colors[8],
            rounded=True,
            highlight_method="block",
            urgent_alert_method="block",
            urgent_border=colors[0],
            this_current_screen_border=colors[4],
            block_highlight_text_color=colors[1],
            background=colors[1],
            decorations=[PowerLineDecoration(path="forward_slash", padding_y=5)],
        ),
        widget.Sep(
            linewidth=0,
            padding=2,
            background=colors[1],
            decorations=[PowerLineDecoration(path="forward_slash", padding_y=5)],
        ),
        widget.Sep(
            linewidth=0,
            padding=-7,
            background=colors[7],
            decorations=[PowerLineDecoration(path="forward_slash")],
        ),
        widget.WindowName(
            fontsize=12,
            foreground=colors[4],
            padding=5,
            format="{name}",
            parse_text=only_app_name,
            decorations=[PowerLineDecoration(path="forward_slash", padding_y=5)],
        ),
        # widget.Net(
        #     foreground=colors[15],
        #     background=colors[1],
        #     font="DS-Digital Bold",
        #     fontsize=15,
        #     format="\uf1eb   {down} \u2193\u2191 {up}",
        #     interface="wlo1",
        #     padding_y=5,
        #     decorations=[PowerLineDecoration(path="forward_slash", padding_y=5)],
        # ),
        widget.CPU(
            background=colors[7],
            foreground=colors[1],
            font="DS-Digital Bold",
            fontsize=15,
            format="\uf2db   {freq_current}Ghz {load_percent}%",
            decorations=[PowerLineDecoration(path="forward_slash", padding_y=5)],
        ),
        widget.ThermalSensor(
            background=colors[4],
            foreground=colors[1],
            font="DS-Digital Bold",
            format="\u26a1\ufe0e {temp:.0f}{unit}",
            fontsize=15,
            decorations=[PowerLineDecoration(path="forward_slash", padding_y=5)],
        ),
        widget.NvidiaSensors(
            background=colors[1],
            foreground=colors[15],
            font="DS-Digital Bold",
            format="\U0001f5ad {temp} \u00b0C {perf}",
            # format="󰢮  {temp} \u00b0C",
            fontsize=14,
            decorations=[PowerLineDecoration(path="forward_slash", padding_y=5)],
        ),
        widget.Memory(
            measure_mem="G",
            foreground=colors[1],
            format="\U0001f5b4 {MemUsed:.1f}G/{MemTotal:.1f}G",
            background=colors[7],
            font="DS-Digital Bold",
            fontsize=15,
            decorations=[PowerLineDecoration(path="forward_slash", padding_y=5)],
        ),
        widget.DF(
            format="\u26c1 {uf:.1f}{m} {r:.0f}%",
            visible_on_warn=False,
            foreground=colors[1],
            background=colors[4],
            font="DS-Digital Bold",
            fontsize=15,
            decorations=[PowerLineDecoration(path="forward_slash", padding_y=5)],
        ),
        widget.CurrentLayoutIcon(
            foreground=colors[15],
            background=colors[1],
            padding=2,
            scale=0.6,
            decorations=[PowerLineDecoration(path="forward_slash", padding_y=5)],
        ),
        widget.CurrentLayout(
            foreground=colors[15],
            background=colors[1],
            font="DS-Digital Bold",
            fontsize=15,
            padding_y=5,
            padding_x=3,
            decorations=[PowerLineDecoration(path="forward_slash", padding_y=5)],
        ),
        widget.KeyboardLayout(
            display_map={"us": "\U0001f1fa\U0001f1f8 US", "latam": "\U0001f1f2\U0001f1fd LATAM"},
            background=colors[15],
            foreground=colors[1],
            configured_keyboards=["us", "latam"],
            fontsize=14,
            decorations=[PowerLineDecoration(path="forward_slash", padding_y=5)],
        ),
        widget.Sep(
            linewidth=0,
            padding_x=2,
            padding_y=5,
            background=colors[15],
            foreground=colors[15],
        ),
        # widget.BatteryIcon(
        #     padding=4,
        #     scale=1,
        # ),
        widget.UPowerWidget(
            battery="BAT0",
            show_short_text=False,
            update_interval=5,
            low_percentage=0.15,
            low_foreground=colors[2],   
        )
    ]

    if show_tray:
        widgets_list.append(_tray_widget())

    widgets_list.extend(
        [
            widget.Sep(
                linewidth=2,
                padding=5,
                foreground=colors[15],
            ),
            widget.Clock(
                foreground=colors[7],
                fontsize=15,
                format="%a %d %b %H:%M",
                decorations=[
                    RectDecoration(
                        colour=colors[1],
                        border_colour=colors[10],
                        border_width=3,
                        padding_y=2,
                        radius=4,
                        filled=True,
                    )
                ],
            ),
            widget.Sep(
                linewidth=2,
                padding=5,
                foreground=colors[15],
            ),
            MonitorLayout(
                foreground=colors[15],
                fontsize=13,
                padding=5,
                decorations=[PowerLineDecoration(path="forward_slash", padding_y=5)],
            ),
            widget.CurrentScreen(
                font="DS-Digital Bold",
                foreground=colors[1],
                fontsize=18,
                decorations=[
                    RectDecoration(
                        colour=colors[1],
                        radius=[10, 0, 0, 10],
                        filled=True,
                    )
                ],
            ),
            widget.QuickExit(
                font="RobotoMono Nerd Font Bold",
                fontsize=18,
                countdown_format="{} Sec",
                default_text="\u23fc",
                background=colors[2],
                padding=5,
            ),
        ]
    )

    return widgets_list
