# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-10-16

First modular, cross-backend release. Fixes the issues that prevented the
X11 and Wayland sessions from starting and adds automatic multi-monitor
handling and an installer.

### Added

- **Isolated virtualenv** (`~/.local/share/qtile/venv`) created by
  `install.sh`, pinning `xcffib==1.6.2`, `qtile==0.37.1`,
  `qtile-extras==0.37.1` and `dbus-fast`. Works around the broken
  `python-xcffib 1.7.0-1` package that made `import libqtile` fail.
- `modules/` package: `settings`, `theme`, `functions`, `keys`, `groups`,
  `layouts`, `widgets`, `screens`, `hooks`.
- `modules/screens.py` with `generate_screens()`: one bar per real output,
  laptop panel (`eDP-*`) as main screen, single monitor becomes main
  automatically, and per-output screen caching to avoid duplicate trays.
- `arrange_monitors()`: X11 monitor layout with `xrandr` at startup
  (laptop primary, `DP-*` left, HDMI right, best mode per output).
- Backend-aware system tray: `Systray` on X11, `StatusNotifier` on Wayland.
- `install.sh` (Arch-focused) and user session entries for X11 and Wayland.
- `README.md` and this `CHANGELOG.md` documenting every solved problem.
- `scripts/qtile-venv` launcher wrapper.

### Changed

- `config.py` reduced from ~1100 lines to a thin entry point that imports the
  modules. No visual/graphical settings changed.
- `scripts/autostart.sh` is now session-aware (X11 vs Wayland) and fixes the
  picom invocation.
- `scripts/picom-toggle.sh` refuses to run on Wayland.
- Resize key bindings now use valid `MonadTall` commands
  (`grow`/`shrink`/`shuffle_up`/`shuffle_down`).

### Fixed

- qtile not starting on X11 **and** Wayland because
  `cairocffi`/`xcffib` `ffi.include()` raised `TypeError` (xcffib 1.7.0
  regression).
- Bar attached to the wrong monitor and the Wayland "false screen" that
  produced a blank session.
- `ConfigError: Only one Systray can be used.` when screens were reconfigured.
- Monitor order being forgotten on every login.
- `AttributeError: 'NoneType' object has no attribute 'split'` in the
  `WindowName` widget.
- Repeated `KB command error ... No such command` for layout actions.
- picom failing due to the removed `--experimental-backends` flag and a
  relative config path; picom no longer starting on Wayland.
- Duplicate `mouse` definition (lost `Button2` bring-to-front) and duplicated
  `Tab` key bindings.

[Unreleased]: https://example.com/compare/v0.1.0...HEAD
[0.1.0]: https://example.com/releases/tag/v0.1.0
