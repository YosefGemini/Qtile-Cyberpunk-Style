#!/usr/bin/env bash
#
# Installer for the modular qtile configuration.
#
# Arch Linux focused. It:
#   1. installs the required system packages
#   2. backs up any existing ~/.config/qtile and installs this configuration
#   3. fixes the broken Arch python-xcffib 1.7.0 by placing a working
#      xcffib==1.6.2 (plus dbus-fast) in the per-user site-packages.
#      This needs no sudo and leaves the system packages untouched. See
#      README.md - "Problem 1".
#   4. validates the configuration with `qtile check`
#
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
CONFIG_DIR="$CONFIG_HOME/qtile"

# Last known-good xcffib before Arch's broken 1.7.0 (see README).
XCFFIB_VERSION="1.6.2"

SYSTEM_PKGS=(
  python
  python-pip
  python-cffi
  python-cairocffi
  python-pywayland
  python-pywlroots
  python-pyxdg
  qtile
  ttf-nerd-fonts-symbols
)

# qtile_extras is not in the official repositories.
AUR_PKGS=(
  qtile-extras-git
)

info() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[!]\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31m[x]\033[0m %s\n' "$*" >&2; exit 1; }

require_arch() {
  command -v pacman >/dev/null 2>&1 || \
    die "This installer targets Arch Linux (pacman not found). See README.md for manual steps."
}

aur_helper() {
  if command -v paru >/dev/null 2>&1; then echo paru
  elif command -v yay >/dev/null 2>&1; then echo yay
  else echo ""; fi
}

install_system_pkgs() {
  local missing=()
  for pkg in "${SYSTEM_PKGS[@]}"; do
    pacman -Qq "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
  done
  [ ${#missing[@]} -eq 0 ] && return 0
  info "Installing system packages: ${missing[*]}"
  sudo pacman -S --needed --noconfirm "${missing[@]}"
}

install_aur_pkgs() {
  local helper missing=()
  helper="$(aur_helper)"
  for pkg in "${AUR_PKGS[@]}"; do
    pacman -Qq "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
  done
  [ ${#missing[@]} -eq 0 ] && return 0

  if [ -z "$helper" ]; then
    warn "Missing AUR packages: ${missing[*]}"
    warn "Install an AUR helper (paru/yay) or build ${missing[*]} manually."
    return 0
  fi
  info "Installing AUR packages with $helper: ${missing[*]}"
  "$helper" -S --needed --noconfirm "${missing[@]}"
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
  chmod +x "$CONFIG_DIR/scripts/"*.sh 2>/dev/null || true
}

fix_xcffib() {
  local user_site
  user_site="$(python -c 'import site; print(site.USER_SITE)')"
  info "Installing xcffib==$XCFFIB_VERSION into $user_site (workaround for the 1.7.0 regression)"
  mkdir -p "$user_site"
  python -m pip install --user --break-system-packages --no-deps --force-reinstall \
    "xcffib==$XCFFIB_VERSION"
  info "Installing dbus-fast (required by the Wayland system tray)"
  python -m pip install --user --break-system-packages "dbus-fast"
}

validate() {
  info "Validating configuration"
  python -c "import cairocffi" >/dev/null 2>&1 || \
    die "cairocffi still broken - xcffib override did not take effect."
  ( cd "$CONFIG_DIR" && qtile check ) || warn "qtile check reported issues (see above)"
}

main() {
  require_arch
  install_system_pkgs
  install_aur_pkgs
  backup_config
  install_config
  fix_xcffib
  validate
  info "Done. Log out and pick 'Qtile' (X11) or 'Qtile (Wayland)' in your display manager."
}

main "$@"
