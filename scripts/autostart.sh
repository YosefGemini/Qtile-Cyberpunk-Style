#!/bin/bash
# Session-aware autostart for qtile.
#
# On X11 we additionally start the compositor (picom), the wallpaper setter
# (feh) and X11-only helpers. On Wayland qtile is itself the compositor, so
# those tools are skipped (picom/feh/numlockx/xsetroot do not work there).

function run {
  if ! pgrep -x "$1" >/dev/null; then
    "$@" &
  fi
}

if [ -n "$WAYLAND_DISPLAY" ] || [ "$XDG_SESSION_TYPE" = "wayland" ]; then
  SESSION=wayland
else
  SESSION=x11
fi

# Common to both backends.
run dunst
run nm-applet
run blueman-applet

if [ "$SESSION" = "x11" ]; then
  numlockx on &
  run lxsession
  run pamac-tray
  run volumeicon

  if ! pgrep -x picom >/dev/null; then
    picom --config "$HOME/.config/picom/picom-blur.conf" --daemon
  fi

  if command -v feh >/dev/null; then
    feh --bg-fill /usr/share/wallpapers/garuda-wallpapers/CyberPunkER.webp
  fi
else
  # Wayland: set the wallpaper with a Wayland-native tool if present.
  if command -v swaybg >/dev/null; then
    run swaybg -i /usr/share/wallpapers/garuda-wallpapers/CyberPunkER.webp -m fill
  fi
fi
