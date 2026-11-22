class Graph:
    def __init__(self, vertices, edges):
        # vertices in input order and edges as (u, v) tuples
        self.vertices = list(vertices)
        self.edges = list(edges)
        # adjacency list in edge order (a list, not a set, so every run checks
        # neighbors in the same order); isolated vertices keep an empty list
        self.adj = {v: [] for v in self.vertices}
        for a, b in self.edges:
            self.adj[a].append(b)
            self.adj[b].append(a)


def parse_graph(text):
    # split non-empty lines into tokens and drop the BOM
    lines = [line.split() for line in text.replace("﻿", "").splitlines() if line.strip()]
    if not lines:
        raise ValueError("The graph is empty. Line 1 must be: n m.")

    # line 1: n m
    header = lines[0]
    if len(header) != 2 or not all(x.isdigit() for x in header):
        raise ValueError("Line 1 must have two non-negative integers: n m.")
    n, m = int(header[0]), int(header[1])

    # line 2: the n vertex ids (n = 0 is the empty graph)
    if n == 0:
        vertices, edge_lines = [], lines[1:]
    else:
        if len(lines) < 2:
            raise ValueError("Line 2 must list the {} vertex ids.".format(n))
        vertices, edge_lines = lines[1], lines[2:]
        if len(vertices) != n:
            raise ValueError("Expected {} vertex ids, found {}.".format(n, len(vertices)))
        seen = set()
        for v in vertices:
            if v in seen:
                raise ValueError("Vertex '{}' is repeated.".format(v))
            seen.add(v)

    # the remaining lines are the m edges
    if len(edge_lines) != m:
        raise ValueError("Expected {} edges, found {}.".format(m, len(edge_lines)))

    names = set(vertices)
    edges, seen_edges = [], set()
    for i, parts in enumerate(edge_lines, 1):
        if len(parts) != 2:
            raise ValueError("Edge {} must have two vertices: u v.".format(i))
        a, b = parts
        # endpoints must exist, no loops and no duplicates (A B equals B A)
        for v in (a, b):
            if v not in names:
                raise ValueError("Edge {}: '{}' is not a vertex.".format(i, v))
        if a == b:
            raise ValueError("Edge {} is a loop ({} {}).".format(i, a, b))
        key = frozenset((a, b))
        if key in seen_edges:
            raise ValueError("Edge {}-{} is duplicated.".format(a, b))
        seen_edges.add(key)
        edges.append((a, b))

    return Graph(vertices, edges)


def load_graph(path):
    # read a .txt file with the same format
    with open(path, encoding="utf-8") as f:
        return parse_graph(f.read())
