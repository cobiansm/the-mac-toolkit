def chromatic_polynomial(graph):
    """
    Deletion-contraction.
    Returns {"coeffs": [a_n, ..., a_0], "subproblems": int, "time_ms": float}
    """
    raise NotImplementedError


def evaluate(coeffs, q):
    raise NotImplementedError


def chromatic_number(coeffs):
    """ min q >= 1 with P(q) > 0 (0 for the empty graph) """
    raise NotImplementedError
