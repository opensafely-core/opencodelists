from django.urls import reverse

from .tree_utils import walk_tree_depth_first


def build_html_tree_highlighting_codes(coding_system, hierarchy, subtree, definition):
    codes = definition.codes(hierarchy)
    codes_in_definition = {r.code for r in definition.including_rules()}
    codes_in_tree = set(walk_tree_depth_first(subtree))
    code_to_name = coding_system.lookup_names(codes_in_tree)
    sort_key = code_to_name.__getitem__

    lines = []
    last_direction = 1
    for code, direction in walk_tree_depth_first(subtree, sort_key):
        if direction == last_direction == 1:
            lines.append("<ul>")
        elif direction == last_direction == -1:
            lines.append("</ul>")

        last_direction = direction

        if direction == -1:
            continue

        if code in codes:
            colour = "blue"
        else:
            colour = "black"

        style = f"color: {colour}"

        if code in codes_in_definition:
            style += "; text-decoration: underline"

        name = code_to_name[code]
        url = reverse(f"{coding_system.id}:concept", args=[code])

        lines.append(
            f'<li><a href="{url}" style="{style}">{name}</a> (<code>{code}</code>)</li>'
        )

    return "\n".join(lines)
