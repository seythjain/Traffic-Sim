def printGraph(graph, root=None):
    """
    Prints a general graph as ASCII art.

    graph: dict of node -> list of neighbors, e.g.
           {"A": ["B", "C"], "B": ["D", "E"], "C": [], "D": [], "E": []}
           Works for trees, DAGs, cyclic graphs, and disconnected graphs.
    root:  optional starting node for the first component drawn.
    """
    if not graph:
        print("(empty graph)")
        return

    visited = set()
    extra_edges = []
    all_nodes = list(graph.keys())
    order = ([root] if root is not None else []) + \
            [n for n in all_nodes if n != root]

    first = True
    for start in order:
        if start in visited:
            continue
        lines, *_ = _build_tree(start, graph, visited, extra_edges)
        if not first:
            print()
        print("\n".join(lines))
        first = False

    if extra_edges:
        print("\nAdditional edges (not shown in tree layout above):")
        for a, b in extra_edges:
            print(f"  {a} -> {b}")


def _build_tree(node, graph, visited, extra_edges, directed=True, seen_edges=None):
    """Recursively builds ASCII block for `node` and its unvisited descendants.

    directed:   if True (default), every neighbor reference is treated as its
                own directed edge, matching the original behavior.
                if False, edges are treated as undirected: a neighbor pair
                is only ever counted once, so a reciprocal entry like
                graph["B"] containing "A" right after graph["A"] contained
                "B" is recognized as the *same* edge instead of being logged
                a second time as a spurious "extra" back-edge.
    seen_edges: set of frozenset({a, b}) pairs already accounted for.
                Only used/populated when directed=False.

    Returns (lines, width, height, mid) where `mid` is the column of node's
    label center.
    """
    if seen_edges is None:
        seen_edges = set()

    visited.add(node)

    children = []
    for neighbor in graph.get(node, []):
        if not directed:
            edge_key = frozenset((node, neighbor))
            if edge_key in seen_edges:
                # same undirected edge already accounted for from the
                # other side - not a new connection, skip it entirely
                continue
            seen_edges.add(edge_key)

        if neighbor not in visited:
            visited.add(neighbor)
            children.append(neighbor)
        elif neighbor != node:
            extra_edges.append((node, neighbor))

    s = str(node)
    u = len(s)

    if not children:
        return [s], u, 1, u // 2

    # Recurse into children (each already reserved in `visited`)
    child_blocks = [_build_tree(c, graph, visited, extra_edges, directed, seen_edges) for c in children]

    # Pad all child blocks to equal height
    max_height = max(h for _, _, h, _ in child_blocks)
    padded = []
    for lines, w, h, mid in child_blocks:
        lines = lines + [' ' * w] * (max_height - h)
        padded.append((lines, w, mid))

    # Concatenate children horizontally with a 1-space gap
    gap = 1
    total_width = sum(w for _, w, _ in padded) + gap * (len(padded) - 1)
    combined_rows = []
    for row in range(max_height):
        combined_rows.append((' ' * gap).join(lines[row] for lines, _, _ in padded))

    # Column of each child's label-center within the combined width
    centers = []
    offset = 0
    for lines, w, mid in padded:
        centers.append(offset + mid)
        offset += w + gap

    # Decide where to place the parent label: centered over the span of children
    span_left, span_right = centers[0], centers[-1]
    label_center = (span_left + span_right) // 2
    label_start = max(0, label_center - u // 2)
    label_start = min(label_start, total_width - u) if total_width >= u else 0
    total_width = max(total_width, label_start + u)
    label_center = label_start + u // 2

    # Branch line: '/' left of label, '|' under it, '\' right of it
    branch = [' '] * total_width
    for c in centers:
        if c < label_center:
            branch[c] = '/'
        elif c > label_center:
            branch[c] = '\\'
        else:
            branch[c] = '|'
    branch_line = ''.join(branch)

    # Top line: underscores spanning from leftmost to rightmost child center,
    # with the parent label written into the middle of that span
    top = [' '] * total_width
    lo, hi = min(span_left, label_start), max(span_right, label_start + u - 1)
    for i in range(lo, hi + 1):
        top[i] = '_'
    for i, ch in enumerate(s):
        top[label_start + i] = ch
    top_line = ''.join(top)

    # Pad combined rows to total_width if it grew to fit a wide label
    combined_rows = [row.ljust(total_width) for row in combined_rows]

    lines = [top_line, branch_line] + combined_rows
    return lines, total_width, max_height + 2, label_center


def returnGraph(graph, root=None):
    """
    Returns a general graph as ASCII art.

    graph: dict of node -> list of neighbors, e.g.
           {"A": ["B", "C"], "B": ["D", "E"], "C": [], "D": [], "E": []}
           Works for trees, DAGs, cyclic graphs, and disconnected graphs.
    root:  optional starting node for the first component drawn.

    Unlike printGraph, this treats the graph as UNDIRECTED: if "B" appears in
    graph["A"] and "A" appears in graph["B"], that's recognized as one single
    connection rather than two, so it won't show up as a spurious "additional
    edge" going back the way it came.
    """
    if not graph:
        return "(empty graph)"

    output = ""
    visited = set()
    extra_edges = []
    seen_edges = set()
    all_nodes = list(graph.keys())
    order = ([root] if root is not None else []) + \
            [n for n in all_nodes if n != root]

    first = True
    for start in order:
        if start in visited:
            continue
        lines, *_ = _build_tree(start, graph, visited, extra_edges, directed=False, seen_edges=seen_edges)
        if not first:
            output += "\n"
        output += "\n".join(lines)
        first = False

    if extra_edges:
        output += "\nAdditional edges (not shown in tree layout above):\n"
        for a, b in extra_edges:
            output += f"  {a} - {b}\n"
    return output


if __name__ == "__main__":
    print("== Simple binary example ==")
    printGraph({"A": ["B", "C"], "B": [], "C": []})

    print("\n== N-ary tree (3+ children) ==")
    printGraph({
        "A": ["B", "C", "D"],
        "B": ["E", "F"],
        "C": [],
        "D": ["G"],
        "E": [], "F": [], "G": [],
    })

    print("\n== Graph with a cycle / shared node ==")
    printGraph({
        "A": ["B", "C"],
        "B": ["D"],
        "C": ["D"],   # D has two parents -> shown as extra edge
        "D": ["A"],   # back edge to A -> cycle, shown as extra edge
    })

    print("\n== Disconnected graph (two components) ==")
    printGraph({
        "A": ["B"],
        "B": [],
        "X": ["Y", "Z"],
        "Y": [], "Z": [],
    })

    print("\n== returnGraph: undirected adjacency list (each edge stored both ways) ==")
    undirected = {
        "A": ["B", "C"],
        "B": ["A", "C"],
        "C": ["A", "B"],
    }
    print(returnGraph(undirected))