def chromatic_polynomial(graph):
    # deletion-contraction: P(G) = P(G - e) - P(G / e)
    # returns {"coeffs": [a_n, ..., a_0], "subproblems": int, "time_ms": float}
    raise NotImplementedError


def evaluate(coeffs, q):
    # value of P(q)
    raise NotImplementedError


def chromatic_number(coeffs):
    # min q >= 1 with P(q) > 0 (0 for the empty graph)
    raise NotImplementedError
