import time 

def chromatic_polynomial(graph, log=None):
    # deletion-contraction: P(G) = P(G - e) - P(G / e)
    # returns {"coeffs": [a_n, ..., a_0], "subproblems": int, "time_ms": float}
    # if log is a list, every call is added to it (used to document the recursion tree)
    
    # Record the starting time
    start_time = time.perf_counter()

    # Convert vertices into numerical indices
    vertices = graph.vertices
    index = {v: i for i, v in enumerate(vertices)}
    n = len(vertices)

    # Create a set of edges without duplicates
    edges = set()

    for u, neighbors in graph.adj.items():
        for v in neighbors:
            if v not in index:
                raise ValueError("Neighbor not found in graph")

            if u == v:
                raise ValueError("Self-loops are not supported")

            a, b = sorted((index[u], index[v]))
            edges.add((a, b))

    # Initialize the recursive call counter
    subproblems = 0

    def subtract(p1, p2):
        # Align polynomial coefficients by degree
        size = max(len(p1), len(p2))

        p1 = [0] * (size - len(p1)) + p1
        p2 = [0] * (size - len(p2)) + p2

        # Subtract the corresponding coefficients
        return [a - b for a, b in zip(p1, p2)]

    def solve(n, edges, names, depth, label):
        nonlocal subproblems

        # Count every recursive call
        subproblems += 1

        # Record the call with the vertex names (merged vertices are joined, e.g. AB)
        entry = None
        if log is not None:
            entry = {"depth": depth, "label": label, "vertices": list(names),
                     "edges": sorted(names[a] + "-" + names[b] for a, b in edges),
                     "edge": None, "coeffs": None}
            log.append(entry)

        # Base case: a graph with no edges has P(G,q) = q^n
        if not edges:
            if entry:
                entry["coeffs"] = [1] + [0] * n
            return [1] + [0] * n

        # Select an edge for deletion-contraction
        u, v = min(edges)
        if entry:
            entry["edge"] = names[u] + "-" + names[v]

        # Deletion: remove the selected edge
        deleted = edges - {(u, v)}

        # Contraction: merge vertices u and v
        contracted = set()

        for a, b in deleted:
            # Replace vertex v with vertex u
            if a == v:
                a = u
            if b == v:
                b = u

            # Remove self-loops and duplicate edges
            if a != b:
                contracted.add(tuple(sorted((a, b))))

        # Reindex vertices after removing vertex v
        remaining = [i for i in range(n) if i != v]

        mapping = {
            old: new for new, old in enumerate(remaining)
        }

        contracted = frozenset(
            tuple(sorted((mapping[a], mapping[b])))
            for a, b in contracted
        )

        # The merged vertex keeps the position of u
        merged = [names[i] for i in remaining]
        merged[mapping[u]] = names[u] + names[v]

        # Recursively calculate both polynomials
        p_deleted = solve(n, frozenset(deleted), names, depth + 1, "G - e")
        p_contracted = solve(n - 1, contracted, merged, depth + 1, "G / e")

        # Apply the deletion-contraction formula
        result = subtract(p_deleted, p_contracted)
        if entry:
            entry["coeffs"] = result
        return result

    # Calculate the chromatic polynomial
    coeffs = solve(n, frozenset(edges), list(vertices), 0, "G")

    # Calculate execution time in milliseconds
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    # Return coefficients, recursive calls, and execution time
    return {
        "coeffs": coeffs,
        "subproblems": subproblems,
        "time_ms": elapsed_ms
    }

def evaluate(coeffs, q):
    # value of P(q)
    
    # Validate the number of available colors
    if not isinstance(q, int) or isinstance(q, bool) or q < 0:
        raise ValueError("q must be a non-negative integer")

    # Evaluate the polynomial using Horner's method
    result = 0

    for coefficient in coeffs:
        result = result * q + coefficient

    # Return the number of valid colorings
    return result

def chromatic_number(coeffs):
    # min q >= 1 with P(q) > 0 (0 for the empty graph)
    # Validate the coefficient list
    if not coeffs:
        raise ValueError("Coefficient list cannot be empty")

    # Special case: graph with zero vertices
    if coeffs == [1]:
        return 0

    # Get the degree of the polynomial
    degree = len(coeffs) - 1

    # Find the minimum number of colors
    for q in range(1, degree + 1):
        if evaluate(coeffs, q) > 0:
            return q

    # Handle invalid polynomial inputs
    raise ValueError("No valid coloring found")
