"""Helper functions used by widgets and keys."""

import os
from libqtile.lazy import lazy


def no_text(text):
    return ""


def only_app_name(text):
    """Shorten ``app - title`` strings for the WindowName widget.

    Returns an empty string (instead of crashing) when the window has no
    name yet. The original implementation raised ``AttributeError`` because
    ``parse_text`` is called with ``None`` while a window is still mapping.
    """
    if not text:
        return ""
    array = text.split(" - ")
    if len(array) > 1:
        return "".join("-" + word for word in array[1:])
    return text


@lazy.function
def window_to_prev_group(qtile):
    if qtile.current_window is not None:
        i = qtile.groups.index(qtile.current_group)
        qtile.current_window.togroup(qtile.groups[i - 1].name)


@lazy.function
def window_to_next_group(qtile):
    if qtile.current_window is not None:
        i = qtile.groups.index(qtile.current_group)
        qtile.current_window.togroup(qtile.groups[i + 1].name)


def window_to_previous_screen(qtile, switch_group=False, switch_screen=False):
    i = qtile.screens.index(qtile.current_screen)
    if i != 0:
        group = qtile.screens[i - 1].group.name
        qtile.current_window.togroup(group, switch_group=switch_group)
        if switch_screen:
            qtile.cmd_to_screen(i - 1)


def window_to_next_screen(qtile, switch_group=False, switch_screen=False):
    i = qtile.screens.index(qtile.current_screen)
    if i + 1 != len(qtile.screens):
        group = qtile.screens[i + 1].group.name
        qtile.current_window.togroup(group, switch_group=switch_group)
        if switch_screen:
            qtile.cmd_to_screen(i + 1)


def window_to_screen(qtile, screen_index, switch_group=False, switch_screen=False):
    if 0 <= screen_index < len(qtile.screens):
        group = qtile.screens[screen_index].group.name
        qtile.current_window.togroup(group, switch_group=switch_group)
        if switch_screen:
            qtile.cmd_to_screen(screen_index)
