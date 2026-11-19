ALGORITHMS = ["Greedy", "Welsh-Powell", "MMI"]
MODES = ["Basic", "MRV", "LCV", "MRV+LCV"]


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
    raise NotImplementedError
