"""
K₅ flip graph analysis.
Finds all minimal generating sets for the cycle reversing system on K₅.
Result: minimum = 6 = cycle rank. The 5 minimal sets are exactly the
6 triangles through each vertex (one set per vertex of K₅).
"""
from collections import defaultdict, deque, Counter
from itertools import combinations
from math import comb

N_VERTICES = 5
EDGES = [(i, j) for i in range(5) for j in range(i + 1, 5)]
N_EDGES = len(EDGES)
EDGE_INDEX = {frozenset([u, v]): k for k, (u, v) in enumerate(EDGES)}
CYCLE_RANK = N_EDGES - N_VERTICES + 1  # 6

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
        n = q.popleft()
        for nb in adj[n]:
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
    m, n = 0, len(cycle)
    for i in range(n): m |= 1 << EDGE_INDEX[frozenset([cycle[i], cycle[(i+1)%n]])]
    return m

def out_seq(o):
    seq = [0] * N_VERTICES
    for k, (u, v) in enumerate(EDGES):
        if (o >> k) & 1: seq[v] += 1
        else: seq[u] += 1
    return tuple(seq)

print(f"K₅: {N_VERTICES} vertices, {N_EDGES} edges, cycle rank = {CYCLE_RANK}")
print(f"Total orientations: {1 << N_EDGES}\n")

print("Computing TCOs...")
tcos = [o for o in range(1 << N_EDGES) if is_tco(o)]
tco_set = set(tcos)
tco_idx = {o: i for i, o in enumerate(tcos)}
N = len(tcos)
print(f"Found {N} TCOs\n")

classes = defaultdict(list)
for o in tcos: classes[out_seq(o)].append(o)
size_counts = Counter(len(v) for v in classes.values())
print(f"Equivalence classes: {len(classes)}")
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
M = len(all_masks)
print(f"Distinct cycle masks: {M}")
for l in sorted(length_counts): print(f"  {length_counts[l]}x C{l}")
print()

mask_list = list(all_masks.keys())
mask_idx = {mk: i for i, mk in enumerate(mask_list)}

edges_by_mask = [[] for _ in range(M)]
for o in tcos:
    for mk in avail[o]:
        nb = o ^ mk
        if nb in tco_set and nb != o and tco_idx[o] < tco_idx[nb]:
            edges_by_mask[mask_idx[mk]].append((tco_idx[o], tco_idx[nb]))
edges_by_mask = [list(set(e)) for e in edges_by_mask]

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
print(f"Full flip graph: {N} nodes, {TARGET} components\n")

print(f"Minimum generator search (target: {TARGET} components, cycle rank = {CYCLE_RANK})")
print(f"Pool: {M} distinct masks\n")

for size in range(1, CYCLE_RANK + 1):
    total = comb(M, size)
    good = []
    for subset in combinations(range(M), size):
        if count_comps(subset) == TARGET:
            good.append(subset)
    print(f"  Size {size}: {total:,} subsets → {len(good)} generating sets")
    if good:
        print(f"\n  ✓ Minimum = {size} = cycle rank\n")
        print(f"Found {len(good)} minimal generating sets:")
        print("=" * 60)
        for i, subset in enumerate(good):
            cycles = [all_masks[mask_list[j]] for j in subset]
            lengths = sorted(len(c) for c in cycles)
            verts_used = sorted(set(v for c in cycles for v in c))
            print(f"\nSet {i+1}: cycle lengths {lengths}  vertices {verts_used}")
            for c in sorted(cycles, key=len):
                print(f"  C{len(c)}: {list(c)}")
        print("\n" + "=" * 60)
        print("Summary:")
        all_lengths = [tuple(sorted(len(c) for c in [all_masks[mask_list[j]] for j in s])) for s in good]
        for pattern, count in Counter(all_lengths).items():
            print(f"  {count}x sets with cycle lengths {list(pattern)}")
        break
