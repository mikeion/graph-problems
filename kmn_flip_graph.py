"""
General flip graph analysis for complete bipartite graphs K(m,n).
Usage: python kmn_flip_graph.py m n
"""
import sys
from collections import defaultdict, deque, Counter
from itertools import combinations
from math import comb

def run(m, n):
    N_VERTICES = m + n
    EDGES = [(i, m + j) for i in range(m) for j in range(n)]
    N_EDGES = len(EDGES)
    EDGE_INDEX = {frozenset([u, v]): k for k, (u, v) in enumerate(EDGES)}
    CYCLE_RANK = N_EDGES - N_VERTICES + 1

    def get_adj(o):
        adj = defaultdict(list)
        for k, (u, v) in enumerate(EDGES):
            if (o >> k) & 1: adj[v].append(u)
            else: adj[u].append(v)
        return adj

    def can_reach(adj, src, dst):
        if src == dst: return True
        vis, q = {src}, deque([src])
        while q:
            node = q.popleft()
            for nb in adj[node]:
                if nb == dst: return True
                if nb not in vis: vis.add(nb); q.append(nb)
        return False

    def is_tco(o):
        adj = get_adj(o)
        for k, (u, v) in enumerate(EDGES):
            s, d = (v, u) if (o >> k) & 1 else (u, v)
            if not can_reach(adj, d, s): return False
        return True

    def find_cycles(o):
        adj = get_adj(o)
        found = set()
        def dfs(st, cur, path, vis):
            for nb in adj[cur]:
                if nb == st and len(path) > 1: found.add(tuple(path))
                elif nb not in vis and nb > st:
                    vis.add(nb); path.append(nb)
                    dfs(st, nb, path, vis)
                    path.pop(); vis.remove(nb)
        for s in range(N_VERTICES): dfs(s, s, [s], {s})
        return found

    def cycle_mask(cycle):
        mask, n = 0, len(cycle)
        for i in range(n): mask |= 1 << EDGE_INDEX[frozenset([cycle[i], cycle[(i+1)%n]])]
        return mask

    def out_seq(o):
        seq = [0] * N_VERTICES
        for k, (u, v) in enumerate(EDGES):
            if (o >> k) & 1: seq[v] += 1
            else: seq[u] += 1
        return tuple(seq)

    print(f"K({m},{n}): {N_VERTICES} vertices, {N_EDGES} edges, cycle rank = {CYCLE_RANK}")
    print(f"Total orientations: {1 << N_EDGES}\n")

    print("Computing TCOs...")
    tcos = [o for o in range(1 << N_EDGES) if is_tco(o)]
    tco_set = set(tcos)
    tco_idx = {o: i for i, o in enumerate(tcos)}
    N = len(tcos)
    print(f"Found {N} TCOs\n")

    classes = defaultdict(list)
    for o in tcos: classes[out_seq(o)].append(o)
    n_classes = len(classes)
    size_counts = Counter(len(v) for v in classes.values())
    print(f"Equivalence classes: {n_classes}")
    for sz in sorted(size_counts): print(f"  {size_counts[sz]}x size-{sz}")
    print()

    print("Collecting cycle masks...")
    all_masks = {}
    avail = {o: set() for o in tcos}
    for o in tcos:
        for c in find_cycles(o):
            mk = cycle_mask(c)
            if mk not in all_masks: all_masks[mk] = c
            avail[o].add(mk)

    length_counts = Counter(len(c) for c in all_masks.values())
    print(f"Distinct cycle masks: {len(all_masks)}")
    for l in sorted(length_counts): print(f"  {length_counts[l]}x C{l}")
    print()

    mask_list = list(all_masks.keys())
    M = len(mask_list)
    mask_idx = {mk: i for i, mk in enumerate(mask_list)}

    # Precompute edges per mask (for union-find)
    edges_by_mask = [[] for _ in range(M)]
    for o in tcos:
        for mk in avail[o]:
            nb = o ^ mk
            if nb in tco_set and nb != o and tco_idx[o] < tco_idx[nb]:
                edges_by_mask[mask_idx[mk]].append((tco_idx[o], tco_idx[nb]))
    edges_by_mask = [list(set(e)) for e in edges_by_mask]

    # Full flip graph component count
    def count_comps(sel):
        parent = list(range(N))
        def find(x):
            while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
            return x
        def union(a, b):
            a, b = find(a), find(b)
            if a != b: parent[a] = b
        for mi in sel:
            for u, v in edges_by_mask[mi]: union(u, v)
        return sum(1 for i in range(N) if find(i) == i)

    TARGET = count_comps(range(M))
    print(f"Full flip graph: {N} nodes, {TARGET} components (= equivalence classes)\n")

    # Minimum generator search
    print(f"Minimum generator search (target: {TARGET} components, cycle rank = {CYCLE_RANK})")
    print(f"Pool: {M} distinct masks\n")

    found = False
    for size in range(1, CYCLE_RANK + 3):
        total = comb(M, size)
        if total > 3_000_000:
            print(f"  Size {size}: {total:,} subsets — too large, stopping.")
            break
        good = 0
        for subset in combinations(range(M), size):
            if count_comps(subset) == TARGET: good += 1
        print(f"  Size {size}: {total:6,} subsets → {good} generating sets")
        if good:
            print(f"\n  ✓ Minimum = {size}  (cycle rank = {CYCLE_RANK})")
            if size > CYCLE_RANK:
                print(f"  → Exceeds cycle rank by {size - CYCLE_RANK}")
            elif size == CYCLE_RANK:
                print(f"  → Equals cycle rank")
            else:
                print(f"  → Below cycle rank")
            found = True
            break

    if not found:
        print(f"\n  Search exhausted up to feasible size. Cycle rank = {CYCLE_RANK}.")

if __name__ == "__main__":
    m, n = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) == 3 else (3, 4)
    run(m, n)
