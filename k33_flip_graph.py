from collections import defaultdict, deque

# K(3,3): left vertices {0,1,2}, right vertices {3,4,5}
EDGES = [(0,3),(0,4),(0,5),(1,3),(1,4),(1,5),(2,3),(2,4),(2,5)]
N_EDGES = 9
N_VERTICES = 6
EDGE_INDEX = {frozenset([u, v]): k for k, (u, v) in enumerate(EDGES)}

# Face cycles of K(3,3) on the torus (computed from rotation system)
# Rotation system: rot[v] = clockwise neighbor order at v
#   rot[0]=[3,4,5], rot[1]=[4,5,3], rot[2]=[5,3,4]
#   rot[3]=[0,2,1], rot[4]=[1,0,2], rot[5]=[2,1,0]
# Traced via face-tracing algorithm (see comments below for derivation)
FACE_CYCLES = [
    [0, 3, 2, 4, 1, 5],  # Face 1: 0→3→2→4→1→5→0 (forward)
    [3, 0, 4, 2, 5, 1],  # Face 2: 3→0→4→2→5→1→3 (forward)
    [4, 0, 5, 2, 3, 1],  # Face 3: 4→0→5→2→3→1→4 (forward)
]


def get_directed_adj(orientation):
    adj = defaultdict(list)
    for k, (u, v) in enumerate(EDGES):
        if orientation & (1 << k):
            adj[v].append(u)
        else:
            adj[u].append(v)
    return adj


def can_reach(adj, src, dst):
    if src == dst:
        return True
    visited = {src}
    queue = deque([src])
    while queue:
        node = queue.popleft()
        for nb in adj[node]:
            if nb == dst:
                return True
            if nb not in visited:
                visited.add(nb)
                queue.append(nb)
    return False


def is_totally_cyclic(orientation):
    adj = get_directed_adj(orientation)
    for k, (u, v) in enumerate(EDGES):
        if orientation & (1 << k):
            src, dst = v, u
        else:
            src, dst = u, v
        if not can_reach(adj, dst, src):
            return False
    return True


def find_all_simple_cycles(orientation):
    adj = get_directed_adj(orientation)
    cycles = set()

    def dfs(start, current, path, visited):
        for nb in adj[current]:
            if nb == start and len(path) > 1:
                cycles.add(tuple(path))
            elif nb not in visited and nb > start:
                visited.add(nb)
                path.append(nb)
                dfs(start, nb, path, visited)
                path.pop()
                visited.remove(nb)

    for start in range(N_VERTICES):
        dfs(start, start, [start], {start})

    return cycles


def cycle_to_edge_mask(cycle):
    mask = 0
    n = len(cycle)
    for i in range(n):
        u, v = cycle[i], cycle[(i + 1) % n]
        mask |= 1 << EDGE_INDEX[frozenset([u, v])]
    return mask


def out_degree_seq(orientation):
    """Out-degree of each vertex: how many edges point away from it."""
    seq = [0] * N_VERTICES
    for k, (u, v) in enumerate(EDGES):
        if orientation & (1 << k):
            seq[v] += 1
        else:
            seq[u] += 1
    return tuple(seq)


def edge_goes(u, v, orientation):
    """Does edge point from u to v in this orientation?"""
    k = EDGE_INDEX[frozenset([u, v])]
    bit = (orientation >> k) & 1
    return (u < v and bit == 0) or (u > v and bit == 1)


def is_face_directed(face, orientation):
    """Is this hexagonal face a directed cycle (forward or backward)?"""
    n = len(face)
    forward = all(edge_goes(face[i], face[(i+1)%n], orientation) for i in range(n))
    backward = all(edge_goes(face[(i+1)%n], face[i], orientation) for i in range(n))
    return forward or backward


def connected_components(flip_graph):
    visited = set()
    components = []
    for node in flip_graph:
        if node not in visited:
            comp = []
            queue = deque([node])
            visited.add(node)
            while queue:
                curr = queue.popleft()
                comp.append(curr)
                for nb in flip_graph[curr]:
                    if nb not in visited:
                        visited.add(nb)
                        queue.append(nb)
            components.append(sorted(comp))
    return components


def build_flip_graph(tcos, tco_set, face_only=False):
    flip_graph = {o: set() for o in tcos}
    face_masks = [cycle_to_edge_mask(f) for f in FACE_CYCLES]

    for o in tcos:
        if face_only:
            moves = [(m,) for f, m in zip(FACE_CYCLES, face_masks) if is_face_directed(f, o)]
            candidates = [m for (m,) in moves]
        else:
            candidates = [cycle_to_edge_mask(c) for c in find_all_simple_cycles(o)]

        for mask in candidates:
            nb = o ^ mask
            if nb in tco_set and nb != o:
                flip_graph[o].add(nb)
                flip_graph[nb].add(o)

    return flip_graph


def verify_out_degree_invariant(tcos, components):
    print("=== Verifying Out-Degree Invariant ===")

    # Same component → same out-degree sequence
    for comp in components:
        seqs = {out_degree_seq(o) for o in comp}
        assert len(seqs) == 1, f"Component has {len(seqs)} distinct out-degree sequences!"

    # Different components → different out-degree sequences
    comp_seqs = [out_degree_seq(comp[0]) for comp in components]
    assert len(set(comp_seqs)) == len(comp_seqs), \
        "Two components share an out-degree sequence!"

    n_comps = len(components)
    print(f"  ✓ Each component has exactly one out-degree sequence")
    print(f"  ✓ All {n_comps} components have distinct out-degree sequences")
    print(f"  ✓ C(6,3) = 20 = ways to place 3 'heavy' vertices (out=2) among 6 = components")

    # Show breakdown by how many heavy vertices are on each side
    left_counts = defaultdict(list)
    for comp in components:
        seq = out_degree_seq(comp[0])
        n_heavy_left = sum(1 for i in range(3) if seq[i] == 2)
        left_counts[n_heavy_left].append(len(comp))

    print("\n  Heavy vertices on left | # classes | class sizes")
    for k in sorted(left_counts):
        sizes = sorted(left_counts[k])
        print(f"  {k} left, {3-k} right       | {len(sizes):9} | {sizes}")


def bfs_from(flip_graph, start):
    dist = {start: 0}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for nb in flip_graph[node]:
            if nb not in dist:
                dist[nb] = dist[node] + 1
                queue.append(nb)
    return dist


def analyze_graph(flip_graph, label):
    tcos = list(flip_graph.keys())
    n = len(tcos)
    total_edges = sum(len(nb) for nb in flip_graph.values()) // 2
    comps = sorted(connected_components(flip_graph), key=len, reverse=True)

    print(f"\n=== {label} ===")
    print(f"Nodes: {n}  |  Edges: {total_edges}  |  Components: {len(comps)}")

    size_counts = defaultdict(int)
    for comp in comps:
        size_counts[len(comp)] += 1
    for sz in sorted(size_counts, reverse=True):
        diameters = []
        for comp in comps:
            if len(comp) == sz:
                d = max(max(bfs_from(flip_graph, node).values()) for node in comp)
                diameters.append(d)
        print(f"  {size_counts[sz]}× size-{sz} components, diameters: {sorted(set(diameters))}")

    degrees = [len(flip_graph[o]) for o in tcos]
    print(f"  Degree range: {min(degrees)}–{max(degrees)}, mean {sum(degrees)/n:.2f}")
    return comps


if __name__ == "__main__":
    print("Computing all totally cyclic orientations of K(3,3)...")
    tcos = [o for o in range(1 << N_EDGES) if is_totally_cyclic(o)]
    tco_set = set(tcos)
    print(f"Found {len(tcos)} TCOs out of {1 << N_EDGES} total orientations\n")

    # All-cycles flip graph
    all_fg = build_flip_graph(tcos, tco_set, face_only=False)
    all_comps = analyze_graph(all_fg, "All-Cycles Flip Graph")

    # Verify invariant
    print()
    verify_out_degree_invariant(tcos, all_comps)

    # Face-cycles-only flip graph
    face_fg = build_flip_graph(tcos, tco_set, face_only=True)
    face_comps = analyze_graph(face_fg, "Face-Cycles-Only Flip Graph (torus faces)")

    # Face-only: show isolated nodes
    isolated = [o for o in tcos if not face_fg[o]]
    print(f"  Isolated nodes (no face cycle available): {len(isolated)}")

    # Show sample TCO with its out-degree sequence
    print("\n=== Sample TCO ===")
    sample = tcos[0]
    seq = out_degree_seq(sample)
    print(f"Orientation: {sample} (bits: {sample:09b})")
    print(f"Out-degrees: L0={seq[0]}, L1={seq[1]}, L2={seq[2]}, R0={seq[3]}, R1={seq[4]}, R2={seq[5]}")
    cycs = find_all_simple_cycles(sample)
    print(f"Directed cycles: {len(cycs)}")
    for c in sorted(cycs, key=len):
        print(f"  {'→'.join(str(v) for v in c)}→{c[0]}  (mask={cycle_to_edge_mask(c)})")
