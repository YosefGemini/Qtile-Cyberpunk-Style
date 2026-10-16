"""Colours, fonts and layout theme. Values kept identical to the original."""


def init_layout_theme():
    return {
        "margin": 5,
        "border_width": 2,
        "border_focus": "#6eead2",
        "border_normal": "#2E3440",
    }


def init_colors():
    return [
        ["#D8DEE9", "#D8DEE9"],  # color 0
        ["#0B1225", "#0B1225"],  # color 1 black
        ["#ec3246", "#ec3246"],  # color 2 red
        ["#68e932", "#68e932"],  # color 3
        ["#F7F80D", "#F7F80D"],  # color 4
        ["#bc434a", "#bc434a"],  # color 5 obscure red
        ["#fe8061", "#fe8061"],  # color 6
        ["#6eead2", "#6eead2"],  # color 7
        ["#246688", "#246688"],  # color 8
        ["#88C0D0", "#88C0D0"],  # color 9
        ["#fad32e", "#fad32e"],  # color 10 amarillo
        ["#f35645", "#f35645"],  # color 11 naranja
        ["#000000", "#000000"],  # color 12 negro
        ["#33B0B5", "#33B0B5"],  # color 13 verde
        ["#00BDA5", "#00BDA5"],  # color 14 verde
        ["#a2ff36", "#a2ff36"],  # color 15 verde
        ["#00BDA5", "#00BDA5"],  # color 16 verde
    ]


def init_widgets_defaults():
    return {
        "font": "Cyberform Super-Italic",
        "fontsize": 12,
    }


layout_theme = init_layout_theme()
colors = init_colors()
widget_defaults = init_widgets_defaults()
