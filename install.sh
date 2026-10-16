#!/usr/bin/env bash
#
# Installer for the modular qtile configuration.
#
# Arch Linux focused. It:
#   1. backs up any existing ~/.config/qtile
#   2. installs the configuration into ~/.config/qtile
#   3. creates an isolated virtualenv with a *working* pinned xcffib
#      (Arch's python-xcffib 1.7.0 is broken with cairocffi - see README.md)
#   4. creates X11 and Wayland session entries that launch the venv
#   5. validates the configuration with `qtile check`
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG_DIR="$CONFIG_HOME/qtile"
VENV_DIR="$DATA_HOME/qtile/venv"
XSESSION_DIR="$DATA_HOME/xsessions"
WAYLAND_SESSION_DIR="$DATA_HOME/wayland-sessions"

# Pinned versions (see README.md - "Problem 1").
XCFFIB_VERSION="1.6.2"
QTILE_VERSION="0.37.1"
QTILE_EXTRAS_VERSION="0.37.1"

# System packages the config expects. Installed with the detected AUR helper
# or pacman if missing.
SYSTEM_PKGS=(
  python
  python-pip
  python-cffi
  python-cairocffi
  python-pywayland
  python-pywlroots
  python-pyxdg
  ttf-nerd-fonts-symbols
)

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

require_arch() {
  command -v pacman >/dev/null 2>&1 || \
    die "This installer targets Arch Linux (pacman not found). Install manually - see README.md."
}

install_system_pkgs() {
  local missing=()
  for pkg in "${SYSTEM_PKGS[@]}"; do
    pacman -Qq "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
  done
  [ ${#missing[@]} -eq 0 ] && return 0

  warn "Missing system packages: ${missing[*]}"
  if command -v paru >/dev/null 2>&1; then
    paru -S --needed --noconfirm "${missing[@]}"
  elif command -v yay >/dev/null 2>&1; then
    yay -S --needed --noconfirm "${missing[@]}"
  else
    sudo pacman -S --needed --noconfirm "${missing[@]}"
  fi
}

backup_config() {
  [ -e "$CONFIG_DIR" ] || return 0
  local backup="${CONFIG_DIR}-backup-$(date +%Y%m%d-%H%M%S)"
  info "Backing up existing config to $backup"
  cp -a "$CONFIG_DIR" "$backup"
}

install_config() {
  if [ "$REPO_DIR" = "$CONFIG_DIR" ]; then
    info "Repository already lives in $CONFIG_DIR, skipping copy"
  else
    info "Installing configuration into $CONFIG_DIR"
    mkdir -p "$CONFIG_DIR"
    cp -a "$REPO_DIR/config.py" "$CONFIG_DIR/"
    for d in modules scripts icons; do
      rm -rf "${CONFIG_DIR:?}/$d"
      cp -a "$REPO_DIR/$d" "$CONFIG_DIR/"
    done
    for f in README.md CHANGELOG.md LICENSE install.sh; do
      [ -e "$REPO_DIR/$f" ] && cp -a "$REPO_DIR/$f" "$CONFIG_DIR/"
    done
  fi
  chmod +x "$CONFIG_DIR/scripts/"*.sh "$CONFIG_DIR/scripts/qtile-venv" 2>/dev/null || true
}

create_venv() {
  info "Creating isolated virtualenv at $VENV_DIR"
  mkdir -p "$DATA_HOME/qtile"
  [ -d "$VENV_DIR" ] || python -m venv --system-site-packages "$VENV_DIR"

  "$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip
  info "Pinning xcffib==$XCFFIB_VERSION (workaround for the 1.7.0 regression)"
  "$VENV_DIR/bin/python" -m pip install --quiet --force-reinstall --no-deps "xcffib==$XCFFIB_VERSION"
  info "Installing qtile==$QTILE_VERSION and qtile-extras==$QTILE_EXTRAS_VERSION"
  "$VENV_DIR/bin/python" -m pip install --quiet --force-reinstall --no-deps \
    "qtile==$QTILE_VERSION" "qtile-extras==$QTILE_EXTRAS_VERSION"
  "$VENV_DIR/bin/python" -m pip install --quiet "dbus-fast"
}

create_sessions() {
  info "Creating user session entries"
  mkdir -p "$XSESSION_DIR" "$WAYLAND_SESSION_DIR"

  cat > "$XSESSION_DIR/qtile-custom.desktop" <<EOF
[Desktop Entry]
Name=Qtile (custom)
Comment=Qtile X11 session (isolated venv)
Exec=$CONFIG_DIR/scripts/qtile-venv start -b x11
Type=Application
DesktopNames=qtile
Keywords=wm;tiling
EOF

  cat > "$WAYLAND_SESSION_DIR/qtile-custom.desktop" <<EOF
[Desktop Entry]
Name=Qtile (custom, Wayland)
Comment=Qtile Wayland session (isolated venv)
Exec=$CONFIG_DIR/scripts/qtile-venv start -b wayland
Type=Application
DesktopNames=qtile
Keywords=wm;tiling
EOF
}

validate() {
  info "Validating configuration"
  ( cd "$CONFIG_DIR" && "$VENV_DIR/bin/qtile" check ) || \
    warn "qtile check reported issues (see above)"
}

main() {
  require_arch
  install_system_pkgs
  backup_config
  install_config
  create_venv
  create_sessions
  validate
  info "Done. Log out and choose 'Qtile (custom)' at your display manager."
  info "Storage used: about 28 MB for $VENV_DIR + ~1 MB for the config"
}

main "$@"
