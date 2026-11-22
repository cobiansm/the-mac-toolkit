import time

ALGORITHMS = ["Greedy", "Welsh-Powell", "MMI"]
MODES = ["Basic", "MRV", "LCV", "MRV+LCV"]


def greedy_order(graph):
    # degree of each vertex
    degree = {v: len(graph.adj[v]) for v in graph.vertices}
    # error degree = degree + neighbors with equal or greater degree
    error = {v: degree[v] + sum(1 for u in graph.adj[v] if degree[u] >= degree[v])
             for v in graph.vertices}
    # input order, used as the last tie-break
    position = {v: i for i, v in enumerate(graph.vertices)}
    # sort by degree, then error degree, then input order
    return sorted(graph.vertices, key=lambda v: (-degree[v], -error[v], position[v]))


def welsh_powell_order(graph):
    position = {v: i for i, v in enumerate(graph.vertices)}
    # sort by degree, then input order as the tie-break
    return sorted(graph.vertices, key=lambda v: (-len(graph.adj[v]), position[v]))


def mmi_order(graph):
    # input order, used as the tie-break
    position = {v: i for i, v in enumerate(graph.vertices)}
    degree = {v: len(graph.adj[v]) for v in graph.vertices}
    remaining = set(graph.vertices)
    removed = []
    # smallest-last: remove a vertex with the smallest current degree
    while remaining:
        vertex = min(remaining, key=lambda v: (degree[v], position[v]))
        remaining.remove(vertex)
        removed.append(vertex)
        # its neighbors lose one degree
        for neighbor in graph.adj[vertex]:
            if neighbor in remaining:
                degree[neighbor] -= 1
    # colour in reverse removal order 
    return removed[::-1]


def colour_vertices(graph, order, k):
    colour_graph = {}
    steps = []
    verifications = 0
    # traverse the vertices in the order given by the algorithm
    for vertex in order:
        unused_colours = k * [True]
        # discard the colours already used by colored neighbors
        for neighbor in graph.adj[vertex]:
            verifications += 1
            if neighbor in colour_graph:
                unused_colours[colour_graph[neighbor]] = False
        # assign the first free colour (first-fit)
        for colour, unused in enumerate(unused_colours):
            if unused:
                colour_graph[vertex] = colour
                steps.append((vertex, colour, ""))
                break
        # no free colour: stop and report the vertex
        else:
            steps.append((vertex, None, ""))
            return colour_graph, steps, verifications, vertex
    return colour_graph, steps, verifications, None


def colour_by_classes(graph, order, k):
    colour_graph = {}
    steps = []
    verifications = 0
    # Welsh-Powell: one pass per colour
    for colour in range(k):
        for vertex in order:
            # skip vertices colored in a previous pass
            if vertex in colour_graph:
                continue
            # the vertex fits if no neighbor already has this colour
            fits = True
            for neighbor in graph.adj[vertex]:
                verifications += 1
                if colour_graph.get(neighbor) == colour:
                    fits = False
                    break
            if fits:
                colour_graph[vertex] = colour
                steps.append((vertex, colour, ""))
    # the first vertex left without colour is the failure
    for vertex in order:
        if vertex not in colour_graph:
            steps.append((vertex, None, ""))
            return colour_graph, steps, verifications, vertex
    return colour_graph, steps, verifications, None


def color_graph(graph, algorithm, mode, color_names):
    if mode != "Basic":
        raise NotImplementedError

    # k = number of colours, index 0 has the highest priority
    k = len(color_names)
    start = time.perf_counter()
    if algorithm == "Greedy":
        colours, steps, verifications, fail = colour_vertices(graph, greedy_order(graph), k)
    elif algorithm == "Welsh-Powell":
        colours, steps, verifications, fail = colour_by_classes(graph, welsh_powell_order(graph), k)
    elif algorithm == "MMI":
        colours, steps, verifications, fail = colour_vertices(graph, mmi_order(graph), k)
    time_ms = (time.perf_counter() - start) * 1000

    # colored neighbors of the vertex that failed
    fail_neighbors = []
    if fail is not None:
        fail_neighbors = [(u, colours[u]) for u in graph.vertices
                          if u in graph.adj[fail] and u in colours]

    # result read by the coloring page
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
