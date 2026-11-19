class Graph:
    def __init__(self, vertices, edges):
        self.vertices = list(vertices)                 # input order
        self.edges = list(edges)                       # [("A", "B"), ...]
        self.adj = {v: set() for v in self.vertices}
        for a, b in self.edges:
            self.adj[a].add(b)
            self.adj[b].add(a)


def parse_graph(text):
    """
    Parse "n m", the n vertex ids and m lines "u v".
    Returns a Graph or raises ValueError with a readable message.
    """
    raise NotImplementedError


def load_graph(path):
    with open(path, encoding="utf-8") as f:
        return parse_graph(f.read())
