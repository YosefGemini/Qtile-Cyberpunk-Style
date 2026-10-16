"""Key bindings and mouse bindings."""

from libqtile.config import Click, Drag, Key
from libqtile.lazy import lazy

from modules.functions import window_to_next_group, window_to_prev_group
from modules.groups import groups
from modules.settings import home, mod, mod1, mod2

keys = [
    # SUPER + FUNCTION KEYS
    Key([mod], "m", lazy.window.toggle_fullscreen()),
    Key([mod], "q", lazy.window.kill()),
    Key([mod], "t", lazy.spawn("xterm")),
    Key([mod], "v", lazy.spawn("pavucontrol")),
    Key([mod], "Escape", lazy.spawn("xkill")),
    Key([mod], "Return", lazy.spawn("alacritty")),

    # SUPER + SHIFT KEYS
    Key([mod, "shift"], "r", lazy.restart()),
    Key([mod, "shift"], "Return", lazy.spawn("dolphin")),
    Key(
        [mod, "shift"],
        "d",
        lazy.spawn(
            "dmenu_run -i -nb '#191919' -nf '#ff1493' -sb '#ff1493' "
            "-sf '#191919' -fn 'NotoMonoRegular:bold:pixelsize=15'"
        ),
    ),

    # CONTROL + ALT KEYS
    Key(["mod1", "control"], "o", lazy.spawn(home + "/.config/qtile/scripts/picom-toggle.sh")),
    Key(["mod1", "control"], "t", lazy.spawn("xterm")),
    Key(["mod1", "control"], "Right", lazy.screen.next_group()),
    Key(["mod1", "control"], "Left", lazy.screen.prev_group()),

    # ALT + ... KEYS
    Key(["mod1"], "space", lazy.widget["keyboardlayout"].next_keyboard()),
    Key(["mod1"], "p", lazy.spawn("pamac-manager")),
    Key(["mod1"], "f", lazy.spawn("firedragon")),
    Key(["mod1"], "m", lazy.spawn("pcmanfm")),
    Key(["mod1"], "w", lazy.spawn("garuda-welcome")),
    Key(["mod1"], "F1", lazy.spawn("nwggrid -p -o 0.4")),  # mostrar aplicaciones
    Key(["mod1"], "F2", lazy.spawn("gmrun")),  # ejecutar comando
    Key(["mod1"], "F4", lazy.window.kill()),  # cerrar ventana

    # QTILE LAYOUT KEYS
    Key([mod], "space", lazy.next_layout()),

    # CHANGE FOCUS
    Key([mod], "Up", lazy.layout.up()),
    Key([mod], "Down", lazy.layout.down()),
    Key([mod], "Left", lazy.layout.left()),
    Key([mod], "Right", lazy.layout.right()),

    # RESIZE / MOVE MAIN PANE (MonadTall commands)
    Key([mod, "control"], "Right", lazy.layout.grow()),
    Key([mod, "control"], "Left", lazy.layout.shrink()),
    Key([mod, "control"], "Up", lazy.layout.shuffle_up()),
    Key([mod, "control"], "Down", lazy.layout.shuffle_down()),

    # FLIP LAYOUT FOR MONADTALL/MONADWIDE
    Key([mod, "shift"], "f", lazy.layout.flip()),

    # MOVE WINDOWS UP OR DOWN MONADTALL/MONADWIDE LAYOUT
    Key([mod, "shift"], "Up", lazy.layout.shuffle_up()),
    Key([mod, "shift"], "Down", lazy.layout.shuffle_down()),
    Key([mod, "shift"], "Left", lazy.layout.swap_left()),
    Key([mod, "shift"], "Right", lazy.layout.swap_right()),

    # CONTROL + SHIFT KEYS
    Key([mod2, "shift"], "Escape", lazy.spawn("lxtask")),

    # SCREENSHOTS
    Key([], "Print", lazy.spawn("flameshot full -p " + home + "/Pictures")),
    Key([mod2], "Print", lazy.spawn("flameshot full -p " + home + "/Pictures")),
    Key([mod, "shift"], "s", lazy.spawn("flameshot gui")),

    # TOGGLE FLOATING LAYOUT
    Key([mod, "shift"], "space", lazy.window.toggle_floating()),

    # MULTIMEDIA KEYS - BRIGHTNESS
    Key([], "XF86MonBrightnessUp", lazy.spawn("brightnessctl s +5%")),
    Key([], "XF86MonBrightnessDown", lazy.spawn("brightnessctl s 5%-")),

    # MULTIMEDIA KEYS - VOLUME
    Key([], "XF86AudioMute", lazy.spawn("amixer -q set Master toggle")),
    Key([], "XF86AudioLowerVolume", lazy.spawn("amixer -q set Master 5%-")),
    Key([], "XF86AudioRaiseVolume", lazy.spawn("amixer -q set Master 5%+")),

    # MULTIMEDIA KEYS - PLAYER
    Key([], "XF86AudioPlay", lazy.spawn("playerctl play-pause")),
    Key([], "XF86AudioNext", lazy.spawn("playerctl next")),
    Key([], "XF86AudioPrev", lazy.spawn("playerctl previous")),
    Key([], "XF86AudioStop", lazy.spawn("playerctl stop")),

    # SHUTDOWN QTILE
    Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
]

# Group navigation and window-to-group bindings (defined once, not per group).
for i in groups:
    keys.extend(
        [
            Key([mod], i.name, lazy.group[i.name].toscreen()),
            Key([mod, "control"], i.name, lazy.window.togroup(i.name)),
            Key(
                [mod, "shift"],
                i.name,
                lazy.window.togroup(i.name),
                lazy.group[i.name].toscreen(),
            ),
        ]
    )

keys.extend(
    [
        Key([mod], "Tab", lazy.screen.next_group()),
        Key([mod, "shift"], "Tab", lazy.screen.prev_group()),
    ]
)

# Drag floating layouts and window moving with the mouse.
mouse = [
    Drag(
        [mod],
        "Button1",
        lazy.window.set_position_floating(),
        start=lazy.window.get_position(),
    ),
    Drag(
        [mod],
        "Button3",
        lazy.window.set_size_floating(),
        start=lazy.window.get_size(),
    ),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]
