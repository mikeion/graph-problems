"""Print the 5 minimal generating sets for K5 with cycle details."""
from collections import defaultdict, deque
from itertools import combinations

N_VERTICES = 5
EDGES = [(i, j) for i in range(5) for j in range(i + 1, 5)]
N_EDGES = len(EDGES)
EDGE_INDEX = {frozenset([u, v]): k for k, (u, v) in enumerate(EDGES)}
CYCLE_RANK = N_EDGES - N_VERTICES + 1  # 6

def get_directed_adj(o):
    adj = defaultdict(list)
    for k, (u, v) in enumerate(EDGES):
        (adj[v] if (o >> k) & 1 else adj[u]).append(v if not (o >> k) & 1 else u)
    return adj

def get_directed_adj2(o):
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
    adj = get_directed_adj2(o)
    for k, (u, v) in enumerate(EDGES):
        s, d = (v, u) if (o >> k) & 1 else (u, v)
        if not can_reach(adj, d, s): return False
    return True

def find_cycles(o):
    adj = get_directed_adj2(o)
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

def mask(cycle):
    m, n = 0, len(cycle)
    for i in range(n): m |= 1 << EDGE_INDEX[frozenset([cycle[i], cycle[(i+1)%n]])]
    return m

print("Precomputing...")
tcos = [o for o in range(1 << N_EDGES) if is_tco(o)]
tco_set = set(tcos)
tco_idx = {o: i for i, o in enumerate(tcos)}
N = len(tcos)

avail = {o: set() for o in tcos}
all_masks = {}
for o in tcos:
    for c in find_cycles(o):
        m = mask(c)
        if m not in all_masks: all_masks[m] = c
        avail[o].add(m)

mask_list = list(all_masks.keys())
M = len(mask_list)
mask_idx = {m: i for i, m in enumerate(mask_list)}

edges_by_mask = [[] for _ in range(M)]
for o in tcos:
    for m in avail[o]:
        nb = o ^ m
        if nb in tco_set and nb != o and tco_idx[o] < tco_idx[nb]:
            edges_by_mask[mask_idx[m]].append((tco_idx[o], tco_idx[nb]))
edges_by_mask = [list(set(e)) for e in edges_by_mask]

TARGET = 51

def count_comps(sel_indices):
    parent = list(range(N))
    def find(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        if a != b: parent[a] = b
    for mi in sel_indices:
        for u, v in edges_by_mask[mi]:
            union(u, v)
    return sum(1 for i in range(N) if find(i) == i)

print(f"Finding all size-6 generating sets...\n")
good = []
for subset in combinations(range(M), 6):
    if count_comps(subset) == TARGET:
        good.append(subset)

print(f"Found {len(good)} minimal generating sets (minimum = {CYCLE_RANK} = cycle rank)\n")
print("=" * 60)

# Describe each set
from collections import Counter
for i, subset in enumerate(good):
    masks = [mask_list[j] for j in subset]
    cycles = [all_masks[m] for m in masks]
    lengths = sorted(len(c) for c in cycles)
    print(f"\nSet {i+1}: {lengths} (cycle lengths)")
    for c in sorted(cycles, key=len):
        print(f"  C{len(c)}: {list(c)}")

# Summary: what cycle lengths appear?
print("\n" + "=" * 60)
print("Summary:")
all_lengths = []
for subset in good:
    cycles = [all_masks[mask_list[j]] for j in subset]
    all_lengths.append(tuple(sorted(len(c) for c in cycles)))

from collections import Counter
for pattern, count in Counter(all_lengths).items():
    print(f"  {count}x sets with cycle lengths {list(pattern)}")

# Also show what cycles are available overall
print(f"\nAll {M} distinct cycle masks by length:")
length_counts = Counter(len(c) for c in all_masks.values())
for l in sorted(length_counts):
    print(f"  C{l}: {length_counts[l]} distinct cycles")
