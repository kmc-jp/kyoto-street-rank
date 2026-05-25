import networkx as nx

from .ranking import PAGERANK_ALPHA


PADDING = 90.0
NODE_RADIUS = 34.0
NODE_HEIGHT = 78.0
ARROW_LENGTH = 18.0
ARROW_HALF_WIDTH = 8.0
WHITE_TEXT_LUMINANCE_LIMIT = 135


def build_graph_view(intersections):
    graph = nx.DiGraph()
    edge_names = {}

    for intersection in intersections:
        source = intersection.loser.name
        target = intersection.winner.name
        graph.add_edge(source, target)
        edge_names[(source, target)] = intersection.name

    cycles = list(nx.simple_cycles(graph))
    cycle_nodes = {node for cycle in cycles for node in cycle}
    cycle_edges = collect_cycle_edges(cycles)
    colors = build_rank_colors(graph)

    positions, width, height = build_positions(graph)
    return {
        "width": width,
        "height": height,
        "nodes": build_nodes(graph, positions, colors, cycle_nodes),
        "edges": build_edges(graph, positions, colors, edge_names, cycle_edges),
        "cycles": cycles,
    }


def collect_cycle_edges(cycles):
    cycle_edges = set()
    for cycle in cycles:
        for index, source in enumerate(cycle):
            target = cycle[(index + 1) % len(cycle)]
            cycle_edges.add((source, target))
    return cycle_edges


def build_positions(graph):
    if not graph:
        return {}, 1000, 640

    node_count = graph.number_of_nodes()
    width = max(1000, int((node_count**0.5) * 360))
    height = max(640, int((node_count**0.5) * 260))

    if node_count == 1:
        node = next(iter(graph.nodes))
        return {node: {"x": width / 2, "y": height / 2}}, width, height

    raw_positions = nx.kamada_kawai_layout(graph)
    positions = normalize_positions(raw_positions, width, height)
    resolve_label_collisions(positions, width, height)
    return positions, width, height


def normalize_positions(raw_positions, width, height):
    xs = [position[0] for position in raw_positions.values()]
    ys = [position[1] for position in raw_positions.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    return {
        node: {
            "x": scale(position[0], min_x, max_x, PADDING, width - PADDING),
            "y": scale(position[1], min_y, max_y, PADDING, height - PADDING),
        }
        for node, position in raw_positions.items()
    }


def resolve_label_collisions(positions, width, height):
    node_names = list(positions)
    label_widths = {node: estimate_label_width(node) for node in node_names}

    for _ in range(120):
        moved = False
        for index, source in enumerate(node_names):
            for target in node_names[index + 1 :]:
                dx = positions[target]["x"] - positions[source]["x"]
                dy = positions[target]["y"] - positions[source]["y"]
                min_dx = (label_widths[source] + label_widths[target]) / 2
                min_dy = NODE_HEIGHT

                if abs(dx) >= min_dx or abs(dy) >= min_dy:
                    continue

                moved = True
                if dx == 0 and dy == 0:
                    dx = 1.0
                    dy = 1.0

                overlap_x = min_dx - abs(dx)
                overlap_y = min_dy - abs(dy)
                if overlap_x < overlap_y:
                    shift = (overlap_x / 2) + 1
                    direction = 1 if dx >= 0 else -1
                    positions[source]["x"] -= direction * shift
                    positions[target]["x"] += direction * shift
                else:
                    shift = (overlap_y / 2) + 1
                    direction = 1 if dy >= 0 else -1
                    positions[source]["y"] -= direction * shift
                    positions[target]["y"] += direction * shift

                clamp_position(positions[source], width, height)
                clamp_position(positions[target], width, height)

        if not moved:
            break


def estimate_label_width(name):
    return max(118.0, (len(name) * 18.0) + 48.0)


def clamp_position(position, width, height):
    position["x"] = min(max(position["x"], PADDING), width - PADDING)
    position["y"] = min(max(position["y"], PADDING), height - PADDING)


def build_rank_colors(graph):
    if not graph:
        return {}

    scores = nx.pagerank(graph, alpha=PAGERANK_ALPHA)
    ranked_nodes = sorted(scores, key=lambda node: (-scores[node], node))
    node_count = len(ranked_nodes)

    colors = {}
    for index, node in enumerate(ranked_nodes):
        position = 0 if node_count == 1 else index / (node_count - 1)
        color = darken_for_white_text(rank_color(position))
        colors[node] = {
            "fill": color,
            "text": "#ffffff",
        }
    return colors


def rank_color(position):
    if position <= 0.5:
        return interpolate_color("#d73027", "#fee08b", position / 0.5)
    return interpolate_color("#fee08b", "#4575b4", (position - 0.5) / 0.5)


def interpolate_color(start_hex, end_hex, ratio):
    start = hex_to_rgb(start_hex)
    end = hex_to_rgb(end_hex)
    mixed = tuple(round(start[index] + ((end[index] - start[index]) * ratio)) for index in range(3))
    return rgb_to_hex(mixed)


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#" + "".join(f"{channel:02x}" for channel in rgb)


def darken_for_white_text(color):
    red, green, blue = hex_to_rgb(color)
    while luminance((red, green, blue)) > WHITE_TEXT_LUMINANCE_LIMIT:
        red = round(red * 0.92)
        green = round(green * 0.92)
        blue = round(blue * 0.92)
    return rgb_to_hex((red, green, blue))


def luminance(rgb):
    red, green, blue = rgb
    return ((red * 299) + (green * 587) + (blue * 114)) / 1000


def build_nodes(graph, positions, colors, cycle_nodes):
    return [
        {
            "name": node,
            "x": positions[node]["x"],
            "y": positions[node]["y"],
            "color": colors[node]["fill"],
            "text_color": colors[node]["text"],
            "in_cycle": node in cycle_nodes,
        }
        for node in graph.nodes
    ]


def build_edges(graph, positions, colors, edge_names, cycle_edges):
    edges = []
    for source, target in graph.edges:
        source_node = positions[source]
        target_node = positions[target]
        x1, y1, x2, y2, unit_x, unit_y = edge_endpoints(source_node, target_node)
        edges.append(
            {
                "source": source,
                "target": target,
                "name": edge_names[(source, target)],
                "color": colors[source]["fill"],
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "arrow_points": arrow_points(x2, y2, unit_x, unit_y),
                "in_cycle": (source, target) in cycle_edges,
            }
        )
    return edges


def edge_endpoints(source_node, target_node):
    dx = target_node["x"] - source_node["x"]
    dy = target_node["y"] - source_node["y"]
    distance = (dx**2 + dy**2) ** 0.5
    if distance == 0:
        return source_node["x"], source_node["y"], target_node["x"], target_node["y"], 1.0, 0.0

    unit_x = dx / distance
    unit_y = dy / distance
    return (
        source_node["x"] + (unit_x * NODE_RADIUS),
        source_node["y"] + (unit_y * NODE_RADIUS),
        target_node["x"] - (unit_x * NODE_RADIUS),
        target_node["y"] - (unit_y * NODE_RADIUS),
        unit_x,
        unit_y,
    )


def arrow_points(tip_x, tip_y, unit_x, unit_y):
    base_x = tip_x - (unit_x * ARROW_LENGTH)
    base_y = tip_y - (unit_y * ARROW_LENGTH)
    perp_x = -unit_y
    perp_y = unit_x
    left_x = base_x + (perp_x * ARROW_HALF_WIDTH)
    left_y = base_y + (perp_y * ARROW_HALF_WIDTH)
    right_x = base_x - (perp_x * ARROW_HALF_WIDTH)
    right_y = base_y - (perp_y * ARROW_HALF_WIDTH)
    return f"{tip_x},{tip_y} {left_x},{left_y} {right_x},{right_y}"


def scale(value, source_min, source_max, target_min, target_max):
    source_span = source_max - source_min
    if source_span == 0:
        return (target_min + target_max) / 2

    target_span = target_max - target_min
    return target_min + ((value - source_min) / source_span) * target_span
