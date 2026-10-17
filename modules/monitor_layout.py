"""Monitor layout manager.

Persistence, output discovery and layout application for X11 and Wayland.

The layout is stored in ``~/.config/qtile/monitor_layout.txt`` (INI format)::

    [layout]
    version=1
    primary=eDP-1
    order=DP-1,eDP-1,HDMI-A-1

    [DP-1]
    mode=1440x900
    x=-1440
    y=0

Behaviour:

* Saved settings are applied for connected outputs. Outputs that are not in the
  file are appended to the order and auto-placed.
* Entries for disconnected outputs and the stored ``primary`` are never pruned.
* If the stored primary is disconnected, the effective primary falls back to
  the laptop panel, then to the first connected output.
"""

from __future__ import annotations

import configparser
import os
import re
import shutil
import subprocess
import threading
from dataclasses import dataclass, field

from libqtile.log_utils import logger

from modules.settings import (
    MONITOR_LAYOUT_FILE,
    backend_is_wayland,
    is_main_output,
)

XRANDR = "xrandr"
WLR_RANDR = "wlr-randr"


@dataclass
class OutputInfo:
    name: str
    connected: bool = True
    enabled: bool = True
    mode: str | None = None
    modes: list[str] = field(default_factory=list)
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    preferred: str | None = None
    primary: bool = False


@dataclass
class LayoutState:
    primary: str | None = None
    order: list[str] = field(default_factory=list)
    outputs: dict[str, dict] = field(default_factory=dict)


_last_connected: tuple[str, ...] | None = None


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load_layout(path: str | None = None) -> LayoutState:
    path = path or MONITOR_LAYOUT_FILE
    state = LayoutState()
    if not os.path.exists(path):
        return state

    parser = configparser.ConfigParser()
    parser.optionxform = str
    try:
        parser.read(path)
    except (configparser.Error, OSError):
        logger.exception("Could not parse monitor layout file %s", path)
        return state

    if parser.has_section("layout"):
        section = parser["layout"]
        state.primary = section.get("primary") or None
        order = section.get("order") or ""
        state.order = [name.strip() for name in order.split(",") if name.strip()]

    for name in parser.sections():
        if name == "layout":
            continue
        section = parser[name]
        entry: dict = {}
        if section.get("mode"):
            entry["mode"] = section.get("mode")
        for axis in ("x", "y"):
            value = section.get(axis)
            if value is not None:
                try:
                    entry[axis] = int(value)
                except ValueError:
                    pass
        if entry:
            state.outputs[name] = entry

    return state


def save_layout(state: LayoutState, path: str | None = None) -> None:
    path = path or MONITOR_LAYOUT_FILE
    parser = configparser.ConfigParser()
    parser.optionxform = str

    parser["layout"] = {
        "version": "1",
        "primary": state.primary or "",
        "order": ",".join(state.order),
    }

    for name, entry in state.outputs.items():
        if not entry:
            continue
        parser[name] = {}
        if entry.get("mode"):
            parser[name]["mode"] = entry["mode"]
        if "x" in entry:
            parser[name]["x"] = str(entry["x"])
        if "y" in entry:
            parser[name]["y"] = str(entry["y"])

    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as handle:
        parser.write(handle)
    os.replace(tmp_path, path)


# ---------------------------------------------------------------------------
# Output discovery
# ---------------------------------------------------------------------------

def _run(command: list[str]) -> str | None:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=8,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        logger.warning(
            "Command failed (%s): %s", " ".join(command), result.stderr.strip()
        )
        return None
    return result.stdout


def list_x11_outputs() -> list[OutputInfo]:
    if not shutil.which(XRANDR):
        return []
    output = _run([XRANDR, "--query"])
    if not output:
        return []

    outputs: list[OutputInfo] = []
    current: OutputInfo | None = None

    for line in output.splitlines():
        header = re.match(r"^(\S+)\s+(connected|disconnected)\b(.*)$", line)
        if header:
            if current is not None:
                outputs.append(current)
            name, status, rest = header.groups()
            connected = status == "connected"
            geometry = re.search(r"(\d+)x(\d+)\+(-?\d+)\+(-?\d+)", rest)
            info = OutputInfo(
                name=name,
                connected=connected,
                enabled=connected,
                primary=bool(re.search(r"\bprimary\b", rest)),
            )
            if geometry:
                info.width = int(geometry.group(1))
                info.height = int(geometry.group(2))
                info.x = int(geometry.group(3))
                info.y = int(geometry.group(4))
                info.mode = f"{info.width}x{info.height}"
            current = info
            continue

        if current is not None and current.connected:
            mode_line = re.match(r"^\s+(\d+x\d+)\s+(.*)$", line)
            if mode_line:
                mode = mode_line.group(1)
                flags = mode_line.group(2)
                if mode not in current.modes:
                    current.modes.append(mode)
                if "*" in flags or "*" in mode_line.group(0):
                    current.mode = mode
                if "+" in flags or "+" in mode_line.group(0):
                    current.preferred = mode

    if current is not None:
        outputs.append(current)

    return outputs


def _qtile_outputs() -> list[OutputInfo]:
    """Fallback discovery using qtile's backend (works without wlr-randr)."""
    try:
        from libqtile import qtile

        core = getattr(qtile, "core", None)
        if core is None:
            return []
        infos = core.get_output_info()
    except Exception:
        return []

    outputs = []
    for info in infos:
        rect = info.rect
        outputs.append(
            OutputInfo(
                name=info.port or "",
                connected=True,
                enabled=True,
                mode=f"{rect.width}x{rect.height}" if rect.width else None,
                x=rect.x,
                y=rect.y,
                width=rect.width,
                height=rect.height,
            )
        )
    return [info for info in outputs if info.name]


def _sysfs_modes() -> dict[str, list[str]]:
    """Read available modes from /sys/class/drm (safe from the event loop)."""
    root = "/sys/class/drm"
    result: dict[str, list[str]] = {}
    try:
        entries = os.listdir(root)
    except OSError:
        return result

    for entry in entries:
        base = os.path.join(root, entry)
        status_path = os.path.join(base, "status")
        modes_path = os.path.join(base, "modes")
        try:
            with open(status_path, encoding="ascii") as handle:
                if handle.read().strip() != "connected":
                    continue
            with open(modes_path, encoding="ascii") as handle:
                modes = [line.strip() for line in handle if line.strip()]
        except OSError:
            continue
        # Skip the legacy "card0-VGA-1"-style names without a connector suffix.
        if "-" not in entry:
            continue
        name = entry.split("-", 1)[1]
        if modes:
            result[name] = modes
    return result


def _qtile_outputs() -> list[OutputInfo]:
    """Fallback discovery using qtile's backend (works without wlr-randr)."""
    try:
        from libqtile import qtile

        core = getattr(qtile, "core", None)
        if core is None:
            return []
        infos = core.get_output_info()
    except Exception:
        return []

    sysfs = _sysfs_modes()
    outputs = []
    for info in infos:
        rect = info.rect
        modes: list[str] = []
        for mode in sysfs.get(info.port or "", []):
            if mode not in modes:
                modes.append(mode)
        outputs.append(
            OutputInfo(
                name=info.port or "",
                connected=True,
                enabled=True,
                mode=f"{rect.width}x{rect.height}" if rect.width else None,
                modes=modes,
                x=rect.x,
                y=rect.y,
                width=rect.width,
                height=rect.height,
                preferred=modes[0] if modes else None,
            )
        )
    return [info for info in outputs if info.name]


def list_wayland_outputs() -> list[OutputInfo]:
    # Do NOT call wlr-randr here: qtile is the compositor, so blocking the
    # event loop on a Wayland client would deadlock. qtile's own output info
    # plus sysfs gives us names, geometry and available modes.
    return _qtile_outputs()


def list_outputs() -> list[OutputInfo]:
    if backend_is_wayland():
        return list_wayland_outputs()
    return list_x11_outputs()


# ---------------------------------------------------------------------------
# Layout rules
# ---------------------------------------------------------------------------

def ordered_outputs(state: LayoutState, outputs: list[OutputInfo]) -> list[str]:
    names = [info.name for info in outputs if info.connected]
    order = [name for name in state.order if name in names]
    for name in names:
        if name not in order:
            order.append(name)
    return order


def effective_primary(state: LayoutState, outputs: list[OutputInfo]) -> str | None:
    names = [info.name for info in outputs if info.connected]
    if not names:
        return None
    if state.primary in names:
        return state.primary
    for name in names:
        if is_main_output(name):
            return name
    return names[0]


def _is_explicit(state: LayoutState, name: str) -> bool:
    entry = state.outputs.get(name, {})
    return "x" in entry and "y" in entry


def _mode_width(state: LayoutState, info: OutputInfo) -> int:
    entry = state.outputs.get(info.name, {})
    mode = entry.get("mode") or info.mode or info.preferred
    if mode and "x" in mode:
        try:
            return int(mode.split("x", 1)[0])
        except ValueError:
            pass
    return info.width or 0


def resolve_positions(
    state: LayoutState, outputs: list[OutputInfo]
) -> dict[str, tuple[int, int]]:
    order = ordered_outputs(state, outputs)
    by_name = {info.name: info for info in outputs}
    positions: dict[str, tuple[int, int]] = {}
    cursor = 0

    for name in order:
        info = by_name.get(name)
        if info is None:
            continue
        if _is_explicit(state, name):
            x = int(state.outputs[name]["x"])
            y = int(state.outputs[name]["y"])
        else:
            x, y = cursor, 0
        positions[name] = (x, y)
        cursor = max(cursor, x + _mode_width(state, info))

    primary = effective_primary(state, outputs)
    if primary and primary in positions and not _is_explicit(state, primary):
        offset = positions[primary][0]
        if offset:
            for name, (x, y) in list(positions.items()):
                if not _is_explicit(state, name):
                    positions[name] = (x - offset, y)

    return positions


def auto_layout(outputs: list[OutputInfo]) -> LayoutState:
    names = [info.name for info in outputs if info.connected]
    if not names:
        return LayoutState()

    main = next((name for name in names if is_main_output(name)), names[0])
    left = [name for name in names if name != main and name.startswith("DP")]
    right = [name for name in names if name != main and name not in left]

    return LayoutState(primary=main, order=left + [main] + right, outputs={})


def _choose_mode(state: LayoutState, info: OutputInfo) -> str | None:
    entry = state.outputs.get(info.name, {})
    mode = entry.get("mode")
    if mode and (not info.modes or mode in info.modes):
        return mode
    return info.preferred or info.mode or (info.modes[0] if info.modes else None)


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------

def apply_x11(state: LayoutState, outputs: list[OutputInfo]) -> bool:
    connected = [info for info in outputs if info.connected]
    if not connected:
        return False
    by_name = {info.name: info for info in connected}
    order = ordered_outputs(state, connected)
    positions = resolve_positions(state, connected)
    primary = effective_primary(state, connected)

    args = [XRANDR]
    for name in order:
        info = by_name[name]
        mode = _choose_mode(state, info)
        x, y = positions.get(name, (0, 0))
        args += ["--output", name]
        if mode:
            args += ["--mode", mode]
        args += ["--pos", f"{x}x{y}"]
        if name == primary:
            args += ["--primary"]

    return _run(args) is not None


def apply_wayland(state: LayoutState, outputs: list[OutputInfo]) -> bool:
    if not shutil.which(WLR_RANDR):
        logger.warning("wlr-randr not found; cannot arrange outputs on Wayland")
        return False

    connected = [info for info in outputs if info.connected]
    if not connected:
        return False

    by_name = {info.name: info for info in connected}
    order = ordered_outputs(state, connected)
    positions = resolve_positions(state, connected)

    success = True
    for name in order:
        info = by_name[name]
        mode = _choose_mode(state, info)
        x, y = positions.get(name, (0, 0))
        args = [WLR_RANDR, "--output", name, "--on"]
        if mode:
            args += ["--mode", mode]
        args += ["--pos", f"{x},{y}"]
        success = (_run(args) is not None) and success

    return success


def apply_layout(
    state: LayoutState | None = None,
    outputs: list[OutputInfo] | None = None,
) -> bool:
    outputs = outputs if outputs is not None else list_outputs()
    if not outputs:
        return False

    if state is None:
        state = load_layout()

    if not state.order and not state.outputs and state.primary is None:
        state = auto_layout(outputs)
    else:
        state.order = ordered_outputs(state, outputs)

    if backend_is_wayland():
        # wlr-randr is a Wayland client; running it synchronously from qtile
        # (the compositor) would deadlock. Apply from a background thread.
        thread = threading.Thread(
            target=apply_wayland, args=(state, outputs), daemon=True
        )
        thread.start()
        return True

    return apply_x11(state, outputs)


def _connected_names(outputs: list[OutputInfo]) -> tuple[str, ...]:
    return tuple(sorted(info.name for info in outputs if info.connected))


def startup_layout() -> bool:
    """Apply the saved layout (or the automatic one) at session start."""
    global _last_connected
    outputs = list_outputs()
    _last_connected = _connected_names(outputs)
    if not outputs:
        return False
    return apply_layout(load_layout(), outputs)


def on_outputs_changed() -> bool:
    """Re-apply the saved layout when the set of connected outputs changes."""
    global _last_connected
    outputs = list_outputs()
    names = _connected_names(outputs)
    if names == _last_connected:
        return False
    _last_connected = names
    if not outputs:
        return False
    return apply_layout(load_layout(), outputs)
