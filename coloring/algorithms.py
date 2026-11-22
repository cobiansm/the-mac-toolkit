import time

ALGORITHMS = ["Greedy", "Welsh-Powell", "MMI"]
MODES = ["Basic", "MRV", "LCV", "MRV+LCV"]


def greedy_order(graph):
    """ Degree desc, then error degree desc, then input order """
    degree = {v: len(graph.adj[v]) for v in graph.vertices}
    error = {v: degree[v] + sum(1 for u in graph.adj[v] if degree[u] >= degree[v])
             for v in graph.vertices}
    position = {v: i for i, v in enumerate(graph.vertices)}
    return sorted(graph.vertices, key=lambda v: (-degree[v], -error[v], position[v]))


def colour_vertices(graph, order, k):
    colour_graph = {}
    steps = []
    verifications = 0
    for vertex in order:
        unused_colours = k * [True]
        for neighbor in graph.adj[vertex]:
            verifications += 1
            if neighbor in colour_graph:
                unused_colours[colour_graph[neighbor]] = False
        for colour, unused in enumerate(unused_colours):
            if unused:
                colour_graph[vertex] = colour
                steps.append((vertex, colour, ""))
                break
        else:
            steps.append((vertex, None, ""))
            return colour_graph, steps, verifications, vertex
    return colour_graph, steps, verifications, None


def color_graph(graph, algorithm, mode, color_names):
    """
    k = len(color_names), in priority order.
    Returns {
        "colors": {vertex: color index or None},
        "success": bool,
        "steps": [(vertex, color index or None, note), ...],
        "ties": [(vertex, [tied color indexes], chosen index), ...],
        "verifications": int,
        "time_ms": float,
        "fail_vertex": vertex or None,
        "fail_neighbors": [(vertex, color index), ...],
    }
    """
    if algorithm != "Greedy" or mode != "Basic":
        raise NotImplementedError

    k = len(color_names)
    start = time.perf_counter()
    colours, steps, verifications, fail = colour_vertices(graph, greedy_order(graph), k)
    time_ms = (time.perf_counter() - start) * 1000

    fail_neighbors = []
    if fail is not None:
        fail_neighbors = [(u, colours[u]) for u in graph.vertices
                          if u in graph.adj[fail] and u in colours]

    return {
        "colors": {v: colours.get(v) for v in graph.vertices},
        "success": fail is None,
        "steps": steps,
        "ties": [],
        "verifications": verifications,
        "time_ms": time_ms,
        "fail_vertex": fail,
        "fail_neighbors": fail_neighbors,
    }
