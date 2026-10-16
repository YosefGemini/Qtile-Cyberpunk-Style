"""Workspace (group) definitions. Names, labels and layouts unchanged."""

from libqtile.config import Group

group_names = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]

group_labels = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

group_layouts = ["monadtall"] * len(group_names)

groups = [
    Group(
        name=group_names[i],
        layout=group_layouts[i].lower(),
        label=group_labels[i],
    )
    for i in range(len(group_names))
]
