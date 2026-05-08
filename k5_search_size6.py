"""
Fast check: does any subset of 6 cycle masks generate 51 components for K5?
Uses union-find + precomputed edge lists per mask for speed.
Also tries random sampling first as a quick test.
"""
from collections import defaultdict, deque
from itertools import combinations
import random

# ── graph definition ──────────────────────────────────────────────────────────
N_VERTICES = 5
EDGES = [(i, j) for i in range(5) for j in range(i + 1, 5)]
N_EDGES = len(EDGES)
EDGE_INDEX = {frozenset([u, v]): k for k, (u, v) in enumerate(EDGES)}
CYCLE_RANK = N_EDGES - N_VERTICES + 1  # 6

# ── core functions ─────────────────────────────────────────────────────────────
def get_directed_adj(orientation):
    adj = defaultdict(list)
    for k, (u, v) in enumerate(EDGES):
        if orientation & (1 << k):
            adj[v].append(u)
        else:
            adj[u].append(v)
    return adj

def can_reach(adj, src, dst):
    if src == dst: return True
    visited, queue = {src}, deque([src])
    while queue:
        node = queue.popleft()
        for nb in adj[node]:
            if nb == dst: return True
            if nb not in visited:
                visited.add(nb); queue.append(nb)
    return False

def is_totally_cyclic(o):
    adj = get_directed_adj(o)
    for k, (u, v) in enumerate(EDGES):
        src, dst = (v, u) if (o >> k) & 1 else (u, v)
        if not can_reach(adj, dst, src): return False
    return True

def find_all_simple_cycles(o):
    adj = get_directed_adj(o)
    cycles = set()
    def dfs(start, cur, path, vis):
        for nb in adj[cur]:
            if nb == start and len(path) > 1:
                cycles.add(tuple(path))
            elif nb not in vis and nb > start:
                vis.add(nb); path.append(nb)
                dfs(start, nb, path, vis)
                path.pop(); vis.remove(nb)
    for s in range(N_VERTICES):
        dfs(s, s, [s], {s})
    return cycles

def cycle_to_edge_mask(cycle):
    mask, n = 0, len(cycle)
    for i in range(n):
        mask |= 1 << EDGE_INDEX[frozenset([cycle[i], cycle[(i+1)%n]])]
    return mask

# ── precompute ────────────────────────────────────────────────────────────────
print("Precomputing...")
tcos = [o for o in range(1 << N_EDGES) if is_totally_cyclic(o)]
tco_set = set(tcos)
tco_idx = {o: i for i, o in enumerate(tcos)}
N = len(tcos)  # 544

avail = {o: set() for o in tcos}
all_masks = {}
for o in tcos:
    for c in find_all_simple_cycles(o):
        m = cycle_to_edge_mask(c)
        if m not in all_masks:
            all_masks[m] = c
        avail[o].add(m)

mask_list = list(all_masks.keys())
M = len(mask_list)  # 37
mask_idx = {m: i for i, m in enumerate(mask_list)}

# Precompute: for each mask, list of (tco_index_src, tco_index_dst) undirected edges
edges_by_mask = [[] for _ in range(M)]
for o in tcos:
    for m in avail[o]:
        nb = o ^ m
        if nb in tco_set and nb != o and tco_idx[o] < tco_idx[nb]:
            edges_by_mask[mask_idx[m]].append((tco_idx[o], tco_idx[nb]))

# Remove duplicate edges per mask
edges_by_mask = [list(set(e)) for e in edges_by_mask]

print(f"TCOs: {N}, distinct masks: {M}, cycle rank: {CYCLE_RANK}\n")

# ── union-find ────────────────────────────────────────────────────────────────
def count_components_uf(selected_mask_indices):
    parent = list(range(N))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        a, b = find(a), find(b)
        if a != b: parent[a] = b

    for mi in selected_mask_indices:
        for u, v in edges_by_mask[mi]:
            union(u, v)
    return sum(1 for i in range(N) if find(i) == i)

TARGET = 51

# ── random sampling: quick test ───────────────────────────────────────────────
print("Random sampling 200,000 subsets of size 6...")
indices = list(range(M))
found_random = None
for trial in range(200_000):
    sel = random.sample(indices, 6)
    if count_components_uf(sel) == TARGET:
        found_random = sel
        break

if found_random is not None:
    circuits = [mask_list[i] for i in found_random]
    print(f"  Found a size-6 generating set after {trial+1} trials!")
    print(f"  → minimum ≤ 6 = cycle rank")
    print(f"  Masks: {[all_masks[m] for m in circuits]}")
else:
    print(f"  No size-6 generating set found in 200k random trials.")
    print(f"  Strong evidence: minimum > 6 > cycle rank\n")

# ── exhaustive check of size 6 (only if random failed and feasible) ───────────
if found_random is None:
    from math import comb
    total = comb(M, 6)
    print(f"Exhaustive check: {total:,} subsets of size 6...")
    print("(This may take several minutes — checking every subset)\n")
    good = 0
    for i, subset in enumerate(combinations(range(M), 6)):
        if count_components_uf(subset) == TARGET:
            good += 1
        if (i + 1) % 500_000 == 0:
            print(f"  {i+1:,} / {total:,} checked, {good} found so far...")
    print(f"\nSize 6: {total:,} subsets → {good} generating sets")
    if good == 0:
        print(f"✓ Minimum > 6 = cycle rank  (Alex's conjecture holds for K5)")
    else:
        print(f"✓ Minimum = 6 = cycle rank  (Alex's conjecture fails for K5)")
