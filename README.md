# YosefGemini Qtile Configuration

A modular [qtile](http://qtile.org) configuration with automatic multi-monitor
handling that works on **both X11 and Wayland**, plus an installer that creates
an isolated Python environment so it keeps working on Arch Linux.

```
config.py          # thin entry point
modules/           # settings, theme, functions, keys, groups,
                   # layouts, widgets, screens, hooks
scripts/           # autostart.sh, picom-toggle.sh, qtile-venv
icons/             # bar icons
install.sh         # installer (Arch Linux)
LICENSE            # MIT License
.gitignore         # keeps caches, venvs and backups out of the repo
```

The visual appearance (colours, fonts, bar layout, decorations) is unchanged
from the original single-file configuration.

---

## Quick start (Arch Linux)

```bash
git clone <your-repo-url> ~/.config/qtile
cd ~/.config/qtile
./install.sh
```

Then log out and pick **Qtile (custom)** (X11) or **Qtile (custom, Wayland)**
in your display manager.

After the first install, apply changes by editing the files under
`~/.config/qtile/modules/` and pressing `Super+Ctrl+R` (qtile reload) or
`Super+Shift+R` (full restart). Modules are reloaded automatically.

### Storage required

| Item | Size |
|------|------|
| `~/.local/share/qtile/venv` (isolated environment, reuses system libs) | ~28 MB |
| `~/.config/qtile` (config + icons) | <1 MB |
| pip build cache (first install only) | ~10 MB |

Measured: `du -sh ~/.local/share/qtile/venv` → **28 MB**.

The environment uses `--system-site-packages`, so it **reuses** the system
`pywayland`, `pywlroots`, `cairocffi`, etc., and only overrides the broken
`xcffib`. A fully isolated environment (building `pywlroots` from source)
would need ~400–600 MB plus build tooling, which is avoided on purpose.

---

## Problems solved

### 1. qtile would not start on X11 *or* Wayland

**Symptom:** choosing the Qtile session shows a black/blank screen and the
session exits immediately. `qtile --version` itself crashes with:

```
cairocffi/ffi.py:26:  ffi.include(xcb_ffi)
TypeError: ffi.include() expects an argument that is also of type cffi.FFI, not 'FFI'
```

**Cause:** On 2026-10-15 Arch updated `python-xcffib` from `1.6.2-1` to
`1.7.0-1`. xcffib 1.7.0 switched to cffi "API mode", so `xcffib.ffi.ffi` is a
`_cffi_backend.FFI` that `cairocffi` cannot `ffi.include()`. That import
failure happens inside `libqtile` itself, so **no backend can start**. Upstream
xcffib reverted the change in 1.7.1, but Arch shipped the broken 1.7.0 (the
package was flagged out-of-date the same day).

**Solution:** `install.sh` creates `~/.local/share/qtile/venv` and pins
`xcffib==1.6.2` (the last known-good release) inside it. The session entries
launch qtile through `scripts/qtile-venv`, which uses that environment. The
system package is left untouched.

**When Arch ships a fixed xcffib (>= 1.7.1):** remove the pin and the venv:

```bash
rm -rf ~/.local/share/qtile/venv
# then edit install.sh and drop the xcffib pin line
```

### 2. Multi-monitor management (order forgotten, wrong/"false" screen)

**Symptom:** after every login the monitor order was lost; you had to run
`xrandr` manually. With the previous config (three hardcoded `Screen` objects)
the bar could be attached to the wrong monitor, and on Wayland the main screen
was mapped to a non-existent ("false") screen, showing nothing.

**Cause:** qtile matches the `screens` list to physical outputs **by index**,
and the index order is not stable. Hardcoding three `Screen` objects also
created as many system-tray widgets as screens.

**Solution:** `modules/screens.py` uses qtile's `generate_screens(outputs)`
hook, which is called every time the monitor set changes. It builds exactly
**one bar per real output**, so:

- the bar always lands on a real monitor (no more "false screen");
- the laptop panel (`eDP-*` / `LVDS-*` / `DSI-*` / `panel`) is the main screen
  and it is focused on startup;
- **if only one monitor is connected it automatically becomes the main
  screen** (X11 and Wayland);
- only the main screen gets the system tray (avoids
  `ConfigError: Only one Systray can be used.`).

On **X11** the outputs are also arranged automatically at startup by
`arrange_monitors()`, which reads `xrandr --query` and applies:

```bash
xrandr --output eDP-1   --auto --primary \
       --output DP-1    --auto --left-of  eDP-1 \
       --output HDMI-A-1 --auto --right-of eDP-1
```

Every output is set to its **preferred (best) mode** with `--auto`. The exact
ports are detected at runtime, so it also works on other machines: the laptop
panel is primary, `DP-*` panels go on the left and the rest on the right.

On **Wayland** qtile (wlroots) owns the output layout; the bar mapping is
correct regardless, which is what caused the blank screen before. Output
*positioning* on Wayland is done by the compositor - install `wlr-randr` and
run it in `scripts/autostart.sh` if you need to move outputs around.

Screen objects are cached per output so a reconfigure reuses them instead of
creating duplicate trays.

### 3. Application icons / system tray in the bar

**Symptom:** tray icons (nm-applet, blueman, etc.) did not appear.

**Cause:** libqtile's `Systray` widget is X11-only
(`supported_backends = {"x11"}`). On Wayland it is silently removed and no
tray exists. On X11 the previous config instantiated one `Systray` per screen,
which conflicts.

**Solution:** `modules/widgets.py` picks the tray per backend:

- **X11** → `qtile_extras.widget.Systray` (identical to before);
- **Wayland** → `qtile_extras.widget.StatusNotifier` (the DBus
  StatusNotifierItem protocol), which needs `dbus-fast` (installed into the
  venv by `install.sh`).

The tray is only added to the main screen (see Problem 2).

### 4. picom

**Symptom:** picom did not start / errored, and on Wayland it hung.

**Cause:** the old autostart used
`picom --config .config/picom/picom-blur.conf --experimental-backends`.
`--experimental-backends` was **removed** in picom 10+ (you run v13), and the
config path was **relative**, so it only worked when the working directory
happened to be `$HOME`. picom was also launched unconditionally on Wayland,
where an X11 compositor cannot work.

**Solution:** `scripts/autostart.sh` now:

- uses an **absolute** path (`$HOME/.config/picom/picom-blur.conf`);
- drops the removed `--experimental-backends` flag (uses `--daemon`);
- starts picom, `feh`, `numlockx`, `lxsession`, `pamac-tray` and `volumeicon`
  **only on X11**;
- on Wayland it only starts Wayland-compatible helpers (and `swaybg` for the
  wallpaper when available).

`scripts/picom-toggle.sh` reports that picom is not used on Wayland instead of
trying to start it.

### 5. Everything lived in one 1100-line `config.py`

**Solution:** the configuration is split into a `modules/` package
(`settings`, `theme`, `functions`, `keys`, `groups`, `layouts`, `widgets`,
`screens`, `hooks`). `config.py` is now ~40 lines and only wires the modules
together. qtile reloads the modules automatically on config reload.

### 6. Repeated `KB command error ... No such command`

**Symptom:** the log filled with `grow_right`, `increase_ratio`, `delete`,
`add` errors.

**Cause:** the resize bindings called commands from other layouts
(`Tile`/`Bsp`). qtile 0.37's `MonadTall` only exposes: `grow`, `shrink`,
`normalize`, `flip`, `maximize`, `reset`, `set_ratio`, `shuffle_{up,down,left,right}`,
`swap`, `swap_left`, `swap_right`, `swap_main`, `grow_main`, `shrink_main`,
`up`, `down`, `left`, `right`, `next`, `previous`.

**Solution:** `modules/keys.py` maps `Super+Ctrl+←/→` to `shrink`/`grow` and
`Super+Ctrl+↑/↓` to `shuffle_up`/`shuffle_down` (valid for MonadTall).

### 7. `AttributeError: 'NoneType' object has no attribute 'split'`

**Symptom:** the `WindowName` widget raised an exception while a window was
still mapping.

**Cause:** `only_app_name()` (used as `parse_text`) assumed the window title
was always a string.

**Solution:** `modules/functions.py` returns `""` when the title is `None`.

### 8. Duplicate key/mouse definitions

The old file defined `mouse` twice; the second definition silently dropped
`Button2` (bring-to-front). `modules/keys.py` keeps a single consolidated
`mouse` list and registers the `Tab` group bindings once instead of once per
workspace (which produced "Key spec duplicated" warnings).

---

## Customising

- **Colours / fonts / layout theme** → `modules/theme.py`
- **Key bindings** → `modules/keys.py`
- **Bar widgets** → `modules/widgets.py`
- **Monitors / bars** → `modules/screens.py`
- **Startup apps** → `scripts/autostart.sh`
- **Workspaces** → `modules/groups.py`

## Requirements

- Arch Linux (installer), qtile 0.37.x.
- The installer pulls: `python`, `python-pip`, `python-cffi`,
  `python-cairocffi`, `python-pywayland`, `python-pywlroots`, `python-pyxdg`,
  `ttf-nerd-fonts-symbols`.
- Optional wallpapers: `/usr/share/wallpapers/garuda-wallpapers/`.

## Manual install (non-Arch)

1. Install qtile 0.37.x with `pywayland`, `pywlroots`, `cairocffi`, `dbus-fast`
   and **`xcffib == 1.6.2`**.
2. Copy this directory to `~/.config/qtile`.
3. Point your session at `~/.config/qtile/scripts/qtile-venv start -b x11` or
   `... -b wayland`.

## License

Released under the [MIT License](LICENSE). Copyright (c) 2026 YosefGemini.
