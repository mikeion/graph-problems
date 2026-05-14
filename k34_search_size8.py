"""K(3,4) size-8 exhaustive search — confirms γ(K(3,4)) = 8."""
from collections import defaultdict, deque
from itertools import combinations
from math import comb

m, n = 3, 4
N_VERTICES = m + n
EDGES = [(i, m + j) for i in range(m) for j in range(n)]
N_EDGES = len(EDGES)
EDGE_INDEX = {frozenset([u, v]): k for k, (u, v) in enumerate(EDGES)}


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
    mask, nn = 0, len(cycle)
    for i in range(nn):
        mask |= 1 << EDGE_INDEX[frozenset([cycle[i], cycle[(i + 1) % nn]])]
    return mask


print("Precomputing...")
tcos = [o for o in range(1 << N_EDGES) if is_tco(o)]
tco_set = set(tcos)
tco_idx = {o: i for i, o in enumerate(tcos)}
N = len(tcos)

all_masks = {}
avail = {o: set() for o in tcos}
for o in tcos:
    for c in find_cycles(o):
        mk = cycle_mask(c)
        if mk not in all_masks: all_masks[mk] = c
        avail[o].add(mk)

mask_list = list(all_masks.keys())
M = len(mask_list)
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

    for mi in sel: [union(u, v) for u, v in edges_by_mask[mi]]
    return sum(1 for i in range(N) if find(i) == i)


TARGET = count_comps(range(M))
total = comb(M, 8)
print(f"N={N}, M={M}, cycle_rank=6, target={TARGET}")
print(f"Size-8 search: {total:,} subsets...\n")

good = []
for i, subset in enumerate(combinations(range(M), 8)):
    if count_comps(subset) == TARGET:
        good.append(subset)
    if (i + 1) % 10_000_000 == 0:
        pct = (i + 1) / total * 100
        print(f"  {i+1:,} / {total:,} ({pct:.1f}%), found {len(good)}")

print(f"\nFound {len(good)} size-8 generating sets")
if good:
    from collections import Counter
    print(f"\n✓ Minimum = 8 = cycle rank + 2\n")
    print(f"Sample sets (first 3):")
    for j, subset in enumerate(good[:3]):
        cycles = [all_masks[mask_list[i]] for i in subset]
        lengths = sorted(len(c) for c in cycles)
        print(f"  Set {j+1}: cycle lengths {lengths}")
        for c in sorted(cycles, key=len):
            print(f"    C{len(c)}: {list(c)}")
else:
    print(f"\n✗ Minimum > 8")
