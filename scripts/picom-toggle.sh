#!/bin/bash
# Toggle the picom compositor. X11 only: on Wayland qtile is the compositor.

if [ -n "$WAYLAND_DISPLAY" ] || [ "$XDG_SESSION_TYPE" = "wayland" ]; then
  notify-send "picom" "picom is not used on Wayland" 2>/dev/null || true
  exit 0
fi

if pgrep -x picom >/dev/null; then
  killall picom
else
  picom -b --config "$HOME/.config/picom/picom-blur.conf"
fi
