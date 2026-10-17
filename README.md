# YosefGemini Qtile Configuration

A modular [qtile](http://qtile.org) configuration with automatic multi-monitor
handling that works on **both X11 and Wayland**, plus an installer that works
around a broken Arch package so it keeps starting on Arch Linux.

```
config.py           # thin entry point
modules/            # settings, theme, functions, keys, groups,
                    # layouts, widgets, screens, hooks,
                    # monitor_layout, monitor_widget
scripts/            # autostart.sh, picom-toggle.sh, dmenu.sh
icons/              # bar icons
monitor_layout.txt  # generated: saved monitor order/modes/primary
install.sh          # installer (Arch Linux)
LICENSE             # MIT License
.gitignore          # keeps caches, venvs and backups out of the repo
```

The visual appearance (colours, fonts, bar layout, decorations) is unchanged
from the original single-file configuration.

---


## Screenshots 🖥️

![Qtile Screenshots](/docs/images/qtileconfig1.png)

![Qtile Screenshots](/docs/images/qtileconfig2.png)

![Qtile Screenshots](/docs/images/qtileconfig3.png)


## Quick start (Arch Linux)

```bash
git clone https://github.com/YosefGemini/Qtile-Cyberpunk-Style.git ~/.config/qtile
cd ~/.config/qtile
./install.sh
```

Then log out and pick **Qtile** (X11) or **Qtile (Wayland)** in your display
manager. The installer fixes the system Qtile so the standard session entries
work - no custom session file is needed.

After the first install, apply changes by editing the files under
`~/.config/qtile/modules/` and pressing `Super+Ctrl+R` (qtile reload) or
`Super+Shift+R` (full restart). Modules are reloaded automatically.

### Storage required

The installer only installs two small wheels into your **per-user**
site-packages (`~/.local/lib/python3.14/site-packages`):

| Item | Size |
|------|------|
| `xcffib` 1.6.2 override | ~2 MB |
| `dbus-fast` (Wayland tray) | ~2 MB |
| `~/.config/qtile` (config + icons) | <1 MB |

No virtualenv and no system packages are modified, so nothing is added to
`~/.local/share/qtile`. (An earlier design used an isolated venv of ~28 MB, but
it was dropped because display managers such as SDDM only read system session
directories and would never see it - see Problem 1.)

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

**Solution:** `install.sh` installs `xcffib==1.6.2` (the last known-good
release) into your **per-user** site-packages
(`~/.local/lib/python3.14/site-packages`). Python's user site-packages come
*before* the system site-packages on `sys.path`, so the working 1.6.2 shadows
the broken system 1.7.0 for every Qtile process - the system `qtile` command
and all built-in session entries now start, and the system packages stay
untouched (no sudo, nothing to upgrade).

```bash
python -m pip install --user --break-system-packages --no-deps --force-reinstall xcffib==1.6.2
python -m pip install --user --break-system-packages dbus-fast
```

> Why not a virtualenv? A venv is more isolated, but display managers such as
> SDDM only scan `/usr/local/share/{xsessions,wayland-sessions}` and
> `/usr/share/{xsessions,wayland-sessions}` - **not** `~/.local/share` - so the
> session would be invisible and you would keep landing on the broken built-in
> session. The per-user override fixes the built-in sessions directly.

**When Arch ships a fixed xcffib (>= 1.7.1):** remove the override:

```bash
rm -rf ~/.local/lib/python3.14/site-packages/xcffib \
       ~/.local/lib/python3.14/site-packages/xcffib-*.dist-info
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

On **X11** the outputs are arranged at startup by
`modules/monitor_layout.py` (falling back to the automatic layout when no
saved configuration exists), which reads `xrandr --query` and applies
`--mode ... --pos XxY` per output plus `--primary`:

```bash
xrandr --output DP-1     --mode 1440x900  --pos -1440x0 \
       --output eDP-1    --mode 1920x1080 --pos 0x0     --primary \
       --output HDMI-A-1 --mode 1280x1024 --pos 1920x0
```

Every output uses its preferred mode by default, and the exact ports are
detected at runtime, so it also works on other machines: the laptop panel is
primary, `DP-*` panels go on the left and the rest on the right.

On **Wayland** qtile (wlroots) owns the output layout; the bar mapping is
correct regardless, which is what caused the blank screen before. Position and
resolution changes use `wlr-randr` (Qtile implements
`wlr-output-management`); without it, only the primary/persistence logic is
available.

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
  per-user site-packages by `install.sh`).

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

## Monitor layout manager

A custom bar widget (`MonitorLayout`, a `TextBox`) lets you manage monitors
without editing files by hand.

- The widget shows the current order and marks the primary output, e.g.
  `🖥 eDP-1★ | DP-1 | HDMI-A-1`.
- **Click the widget** or press **`Super+Ctrl+M`** to open the editor popup.
- In the editor you can:
  - set the **primary** output (`★`),
  - **reorder** outputs (`◀` / `▶`),
  - **cycle resolutions** by clicking the mode (only modes reported by the
    backend are offered, preferred first),
  - **nudge exact x/y positions** via the `Pos…` menu (`±10`/`±100`), or return
    to automatic flow with `Auto flow`,
  - **Apply** (saves and applies) or **Auto** (reset to automatic layout).

The layout is saved to `~/.config/qtile/monitor_layout.txt`:

```ini
[layout]
version=1
primary=eDP-1
order=DP-1,eDP-1,HDMI-A-1

[DP-1]
mode=1440x900
x=-1440
y=0

[eDP-1]
mode=1920x1080
x=0
y=0

[HDMI-A-1]
mode=1280x1024
x=1920
y=0
```

Behaviour:

- With multiple screens, the saved configuration is used for the connected
  outputs; monitors not in the file are appended and auto-placed.
- Entries for **disconnected** outputs and the stored `primary` are kept.
- If the stored primary is disconnected, the effective primary falls back to
  the laptop panel, then to the first connected output.
- A single connected monitor always becomes the main screen.
- On X11, positions/modes are applied with `xrandr`; on Wayland with
  `wlr-randr` (Qtile implements `wlr-output-management`). Without
  `wlr-randr`, Wayland keeps the primary/persistence logic but cannot change
  position or resolution.
- The system tray stays on the built-in panel (or the first output when no
  laptop panel is present).

---

## Keyboard shortcuts

`Super` is the Windows/Command key (`mod4`), `Alt` is `mod1`, `Ctrl` is `mod2`.
Bindings live in `modules/keys.py`.

### Windows and focus

| Shortcut | Action |
|---|---|
| `Super+Return` | Open `alacritty` |
| `Super+Shift+Return` | Open `dolphin` |
| `Super+t` | Open `xterm` |
| `Super+q` / `Alt+F4` | Close focused window |
| `Super+m` | Toggle fullscreen |
| `Super+Shift+space` | Toggle floating |
| `Super+Up/Down/Left/Right` | Move focus between windows |
| `Super+Ctrl+Right` / `Super+Ctrl+Left` | Grow / shrink the main pane |
| `Super+Ctrl+Up/Down` | Move window up / down in the stack |
| `Super+Shift+Up/Down` | Shuffle window up / down |
| `Super+Shift+Left/Right` | Swap window left / right |
| `Super+Shift+f` | Flip the master pane side |

### Workspaces and layouts

| Shortcut | Action |
|---|---|
| `Super+1…0` | Switch to workspace 1–10 |
| `Super+Shift+1…0` | Move window to workspace and follow |
| `Super+Ctrl+1…0` | Move window to workspace (stay here) |
| `Super+Tab` / `Super+Shift+Tab` | Next / previous workspace |
| `Ctrl+Alt+Right` / `Ctrl+Alt+Left` | Next / previous workspace |
| `Super+space` | Cycle layout |

### Monitors

| Shortcut | Action |
|---|---|
| `Super+Ctrl+M` | Open the monitor layout editor |
| Click the `MonitorLayout` widget | Open the monitor layout editor |

### Launch and system

| Shortcut | Action |
|---|---|
| `Super+Shift+d` | `dmenu_run` |
| `Alt+F1` | `nwggrid` application grid |
| `Alt+F2` | `gmrun` run dialog |
| `Alt+p` | `pamac-manager` |
| `Alt+f` | `firedragon` |
| `Alt+m` | `pcmanfm` |
| `Alt+w` | `garuda-welcome` |
| `Alt+space` | Next keyboard layout |
| `Super+v` | `pavucontrol` |
| `Ctrl+Alt+t` | `xterm` |
| `Ctrl+Alt+o` | Toggle `picom` (X11 only) |
| `Ctrl+Shift+Escape` | `lxtask` |
| `Super+Escape` | `xkill` |
| `Super+Shift+r` | Restart qtile |
| `Super+Ctrl+q` | Shutdown qtile |

### Screenshots and media

| Shortcut | Action |
|---|---|
| `Print` / `Ctrl+Print` | Full screenshot to `~/Pictures` (`flameshot`) |
| `Super+Shift+s` | Region screenshot (`flameshot gui`) |
| `XF86MonBrightnessUp/Down` | Brightness ±5% |
| `XF86AudioRaiseVolume/LowerVolume/Mute` | Volume control |
| `XF86AudioPlay/Next/Prev/Stop` | Media control (`playerctl`) |

### Mouse

| Shortcut | Action |
|---|---|
| `Super+Button1` drag | Move a floating window |
| `Super+Button3` drag | Resize a floating window |
| `Super+Button2` | Bring window to front |

> The launcher/tool bindings require the optional packages listed under
> [Dependencies](#dependencies).

---

## Customising

- **Colours / fonts / layout theme** → `modules/theme.py`
- **Key bindings** → `modules/keys.py`
- **Bar widgets** → `modules/widgets.py`
- **Monitors / bars** → `modules/screens.py`
- **Monitor order / resolution / primary** → `monitor_layout.txt` or the
  `MonitorLayout` widget (`modules/monitor_layout.py`)
- **Startup apps** → `scripts/autostart.sh`
- **Workspaces** → `modules/groups.py`

## Dependencies

### Required

| Purpose | Package |
|---|---|
| Window manager | `qtile` |
| Qtile widgets, popups, tray | `qtile-extras-git` (AUR) |
| Python bindings | `python`, `python-pip`, `python-cffi`, `python-cairocffi`, `python-pywayland`, `python-pywlroots`, `python-pyxdg` |
| Fixed xcffib (per-user pip) | `xcffib==1.6.2` |
| Wayland tray / DBus | `dbus-fast` (per-user pip) |
| Monitor layout (X11) | `xorg-xrandr` |
| Monitor layout (Wayland) | `wlr-randr` |
| **Wayland wallpaper** | **`swaybg`** |
| X11 compositor / wallpaper / helpers | `picom`, `feh`, `numlockx`, `lxsession` |
| Notifications / tray applets | `dunst`, `network-manager-applet`, `blueman`, `volumeicon` |
| Bar icons/fonts | `ttf-nerd-fonts-symbols` |

`scripts/autostart.sh` uses **`swaybg`** on Wayland (and `feh`/`picom` on X11)
to set the wallpaper. Wallpapers under
`/usr/share/wallpapers/garuda-wallpapers/` are Garuda-specific and optional.

### Optional (apps used by the default key bindings)

`alacritty`, `xterm`, `dmenu`, `jgmenu`, `flameshot`, `brightnessctl`,
`playerctl`, `pavucontrol`, `lxtask`, `pcmanfm`, `xorg-xkill`.
Install them with `./install.sh --with-optional`.

Also referenced by some bindings (AUR/Garuda-specific, install manually if you
use them): `gmrun`, `nwg-grid`, `pamac-manager`/`pamac-tray`, `firedragon`,
`garuda-welcome`, `dolphin`.

## Manual install (non-Arch)

1. Install qtile 0.37.x with `pywayland`, `pywlroots`, `cairocffi` and
   `qtile-extras`.
2. Add a working **`xcffib == 1.6.2`** and `dbus-fast` to your Python user
   site-packages (`pip install --user xcffib==1.6.2 dbus-fast`) if your
   distribution ships a broken xcffib.
3. Install `xrandr` (X11), `wlr-randr` (Wayland layout) and `swaybg`
   (Wayland wallpaper).
4. Copy this directory to `~/.config/qtile`.
5. Log in with the standard **Qtile** / **Qtile (Wayland)** session.

## License

Released under the [MIT License](LICENSE). Copyright (c) 2026 YosefGemini.
