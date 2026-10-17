"""Bar widget and popup editor for the monitor layout manager."""

from __future__ import annotations

from libqtile import hook
from libqtile.command.base import expose_command
from libqtile.widget import TextBox
from qtile_extras.popup.toolkit import PopupGridLayout, PopupText

from modules import monitor_layout as ml


class MonitorLayout(TextBox):
    """Show the monitor order and open an editor on click.

    The editor lets the user set the primary output, reorder outputs, choose a
    resolution (where the backend supports it) and nudge exact x/y positions.
    Changes are stored in ``monitor_layout.txt`` when *Apply* is pressed.
    """

    def __init__(self, **config):
        config.setdefault("mouse_callbacks", {})
        super().__init__(**config)
        self.mouse_callbacks.setdefault("Button1", self.show_editor)
        self._popup = None
        self._positions_popup = None
        self._draft = None
        self._position_target = None
        self._hooked = False

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        if not self._hooked:
            hook.subscribe.screens_reconfigured(self._on_screens_reconfigured)
            self._hooked = True
        self.update_text()

    def finalize(self):
        if self._hooked:
            hook.unsubscribe.screens_reconfigured(self._on_screens_reconfigured)
            self._hooked = False
        self._kill_popups()
        super().finalize()

    # -- status ---------------------------------------------------------

    def _connected(self):
        return [info for info in ml.list_outputs() if info.connected]

    def _status_text(self) -> str:
        outputs = self._connected()
        if not outputs:
            return "󱋆 N/A"
        # state = ml.load_layout()
        # primary = ml.effective_primary(state, outputs)
        # parts = []
        # for name in ml.ordered_outputs(state, outputs):
        #     parts.append(name + ("★" if name == primary else ""))
        return " 󱋆 "
        # return "󱋆  " + " | ".join(parts)

    def update_text(self):
        try:
            self.update(self._status_text())
        except Exception:
            pass

    def _on_screens_reconfigured(self):
        self.update_text()

    # -- popup management ----------------------------------------------

    def _kill_popups(self):
        for popup in (self._positions_popup, self._popup):
            if popup is not None:
                try:
                    popup.kill()
                except Exception:
                    pass
        self._positions_popup = None
        self._popup = None

    def _schedule(self, func):
        """Run a rebuild after the current click event has finished."""
        try:
            self.qtile.call_later(0.01, func)
        except Exception:
            func()

    @expose_command()
    def show_editor(self):
        """Open the monitor layout editor."""
        self._kill_popups()
        outputs = self._connected()
        if not outputs:
            return

        self._draft = ml.load_layout()
        self._draft.order = ml.ordered_outputs(self._draft, outputs)
        if self._draft.primary is None:
            self._draft.primary = ml.effective_primary(self._draft, outputs)
        self._render_editor()

    def _render_editor(self):
        if not self.configured:
            return
        outputs = self._connected()
        if not outputs:
            self._kill_popups()
            return

        by_name = {info.name: info for info in outputs}
        order = [name for name in self._draft.order if name in by_name]
        for name in by_name:
            if name not in order:
                order.append(name)
        # Keep entries for disconnected outputs in the saved order.
        for name in order:
            if name not in self._draft.order:
                self._draft.order.append(name)

        primary = ml.effective_primary(self._draft, outputs)
        rows = len(order) + 2
        cols = 7
        controls = [
            PopupText(
                text="Monitor layout",
                row=0,
                col=0,
                col_span=cols,
                fontsize=14,
                foreground="#6eead2",
                h_align="left",
            )
        ]

        for index, name in enumerate(order):
            row = index + 1
            info = by_name[name]
            entry = self._draft.outputs.setdefault(name, {})
            mode = entry.get("mode") or info.mode or info.preferred or "-"
            controls += [
                PopupText(
                    text="★" if name == primary else "☆",
                    row=row,
                    col=0,
                    fontsize=15,
                    foreground="#fad32e",
                    h_align="center",
                    mouse_callbacks={"Button1": self._primary_callback(name)},
                ),
                PopupText(
                    text=name,
                    row=row,
                    col=1,
                    col_span=2,
                    fontsize=12,
                    foreground="#ffffff",
                    h_align="left",
                ),
                PopupText(
                    text=mode,
                    row=row,
                    col=3,
                    fontsize=12,
                    foreground="#a2ff36",
                    h_align="center",
                    mouse_callbacks={"Button1": self._mode_callback(name)},
                ),
                PopupText(
                    text="◀",
                    row=row,
                    col=4,
                    fontsize=14,
                    foreground="#88C0D0",
                    h_align="center",
                    mouse_callbacks={"Button1": self._move_callback(name, -1)},
                ),
                PopupText(
                    text="▶",
                    row=row,
                    col=5,
                    fontsize=14,
                    foreground="#88C0D0",
                    h_align="center",
                    mouse_callbacks={"Button1": self._move_callback(name, 1)},
                ),
                PopupText(
                    text="Pos…",
                    row=row,
                    col=6,
                    fontsize=11,
                    foreground="#fe8061",
                    h_align="center",
                    mouse_callbacks={"Button1": self._positions_callback(name)},
                ),
            ]

        footer = len(order) + 1
        controls += [
            PopupText(
                text="Apply",
                row=footer,
                col=0,
                col_span=2,
                fontsize=13,
                foreground="#68e932",
                h_align="center",
                mouse_callbacks={"Button1": self._apply},
            ),
            PopupText(
                text="Auto",
                row=footer,
                col=2,
                col_span=2,
                fontsize=13,
                foreground="#fad32e",
                h_align="center",
                mouse_callbacks={"Button1": self._auto},
            ),
            PopupText(
                text="Close",
                row=footer,
                col=4,
                col_span=3,
                fontsize=13,
                foreground="#ec3246",
                h_align="center",
                mouse_callbacks={"Button1": self._close},
            ),
        ]

        if self._popup is not None:
            try:
                self._popup.kill()
            except Exception:
                pass

        self._popup = PopupGridLayout(
            self.qtile,
            rows=rows,
            cols=cols,
            width=820,
            height=36 * rows + 16,
            controls=controls,
            background="#0B1225",
            border="#6eead2",
            border_width=1,
            close_on_click=False,
            keyboard_navigation=True,
        )
        self._popup.show(centered=True)

    # -- editor callbacks ----------------------------------------------

    def _primary_callback(self, name):
        def callback():
            self._draft.primary = name
            self._schedule(self._render_editor)

        return callback

    def _mode_callback(self, name):
        def callback():
            outputs = self._connected()
            info = next((item for item in outputs if item.name == name), None)
            if info is None or not info.modes:
                return
            entry = self._draft.outputs.setdefault(name, {})
            current = entry.get("mode") or info.mode or info.preferred
            modes = info.modes
            index = modes.index(current) if current in modes else -1
            entry["mode"] = modes[(index + 1) % len(modes)]
            self._schedule(self._render_editor)

        return callback

    def _move_callback(self, name, delta):
        def callback():
            outputs = self._connected()
            connected = [info.name for info in outputs]
            order = [item for item in self._draft.order if item in connected]
            for item in connected:
                if item not in order:
                    order.append(item)
            if name not in order:
                order.append(name)
            index = order.index(name)
            target = index + delta
            if 0 <= target < len(order):
                order[index], order[target] = order[target], order[index]
                disconnected = [
                    item for item in self._draft.order if item not in connected
                ]
                self._draft.order = order + disconnected
                self._schedule(self._render_editor)

        return callback

    def _positions_callback(self, name):
        def callback():
            outputs = self._connected()
            positions = ml.resolve_positions(self._draft, outputs)
            x, y = positions.get(name, (0, 0))
            entry = self._draft.outputs.setdefault(name, {})
            entry["x"] = int(x)
            entry["y"] = int(y)
            self._position_target = name
            self._schedule(self._render_positions)

        return callback

    def _apply(self):
        self._schedule(self._do_apply)

    def _do_apply(self):
        if not self.configured or self._draft is None:
            return
        ml.save_layout(self._draft)
        ml.apply_layout(self._draft)
        self._focus_primary()
        self._kill_popups()
        self.update_text()

    def _auto(self):
        self._schedule(self._do_auto)

    def _do_auto(self):
        if not self.configured:
            return
        outputs = self._connected()
        if not outputs:
            return
        state = ml.auto_layout(outputs)
        ml.save_layout(state)
        ml.apply_layout(state, outputs)
        self._focus_primary()
        self._kill_popups()
        self.update_text()

    def _focus_primary(self):
        try:
            from modules.hooks import focus_primary

            focus_primary()
        except Exception:
            pass

    def _close(self):
        self._kill_popups()

    # -- exact position popup ------------------------------------------

    def _render_positions(self):
        if not self.configured:
            return
        name = self._position_target
        if name is None:
            return
        entry = self._draft.outputs.setdefault(name, {})
        if "x" in entry and "y" in entry:
            x = int(entry["x"])
            y = int(entry["y"])
        else:
            positions = ml.resolve_positions(self._draft, self._connected())
            x, y = positions.get(name, (0, 0))

        rows, cols = 4, 5
        controls = [
            PopupText(
                text=f"Position: {name}   x={x}  y={y}",
                row=0,
                col=0,
                col_span=cols,
                fontsize=13,
                foreground="#6eead2",
                h_align="left",
            )
        ]

        for row, axis in ((1, "x"), (2, "y")):
            for col, delta in enumerate((-100, -10, 10, 100)):
                controls.append(
                    PopupText(
                        text=f"{axis} {delta:+d}",
                        row=row,
                        col=col,
                        fontsize=11,
                        foreground="#88C0D0",
                        h_align="center",
                        mouse_callbacks={
                            "Button1": self._nudge_callback(axis, delta)
                        },
                    )
                )

        controls += [
            PopupText(
                text="Auto flow",
                row=3,
                col=0,
                col_span=2,
                fontsize=12,
                foreground="#fad32e",
                h_align="center",
                mouse_callbacks={"Button1": self._auto_flow},
            ),
            PopupText(
                text="Back",
                row=3,
                col=2,
                col_span=3,
                fontsize=12,
                foreground="#ec3246",
                h_align="center",
                mouse_callbacks={"Button1": self._close_positions},
            ),
        ]

        if self._positions_popup is not None:
            try:
                self._positions_popup.kill()
            except Exception:
                pass

        self._positions_popup = PopupGridLayout(
            self.qtile,
            rows=rows,
            cols=cols,
            width=560,
            height=36 * rows + 16,
            controls=controls,
            background="#0B1225",
            border="#fe8061",
            border_width=1,
            close_on_click=False,
            keyboard_navigation=True,
        )
        self._positions_popup.show(centered=True)

    def _nudge_callback(self, axis, delta):
        def callback():
            name = self._position_target
            if name is None:
                return
            entry = self._draft.outputs.setdefault(name, {})
            entry[axis] = int(entry.get(axis, 0)) + delta
            self._schedule(self._render_positions)

        return callback

    def _auto_flow(self):
        name = self._position_target
        if name is None:
            return
        entry = self._draft.outputs.setdefault(name, {})
        entry.pop("x", None)
        entry.pop("y", None)
        self._schedule(self._render_positions)

    def _close_positions(self):
        if self._positions_popup is not None:
            try:
                self._positions_popup.kill()
            except Exception:
                pass
        self._positions_popup = None
        self._schedule(self._render_editor)
