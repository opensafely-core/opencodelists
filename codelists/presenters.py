from django.urls import reverse


def build_html_tree_highlighting_codes(coding_system, hierarchy, definition):
    codes = definition.codes(hierarchy)
    codes_in_definition = {r.code for r in definition.including_rules()}
    codes_in_hierarchy = hierarchy.nodes
    code_to_name = coding_system.lookup_names(codes_in_hierarchy)
    sort_key = code_to_name.__getitem__

    lines = []
    last_direction = 1
    for node in hierarchy.walk_depth_first_as_tree(sort_key=sort_key):
        direction = node.direction
        code = node.label

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
