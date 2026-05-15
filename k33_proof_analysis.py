"""
Deep analysis for proving gamma(K(3,3)) >= 5.

Approach 1: "Blocking pair" / uniquely required circuits.
For each pair of TCOs in the same reversal class, find ALL circuit masks
that can directly connect them. If a pair is connected by exactly one mask,
that mask is "required" for any generating set.

Approach 2: Analyze the structure of what 4-circuit sets fail and why.

Approach 3: Look at the complement pattern of the 9 minimal sets.
"""

from collections import defaultdict, deque
from itertools import combinations
import sys

# ---- Copy the core machinery from k33_flip_graph.py ----

EDGES = [(0,3),(0,4),(0,5),(1,3),(1,4),(1,5),(2,3),(2,4),(2,5)]
N_EDGES = 9
N_VERTICES = 6
EDGE_INDEX = {frozenset([u, v]): k for k, (u, v) in enumerate(EDGES)}

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
    seq = [0] * N_VERTICES
    for k, (u, v) in enumerate(EDGES):
        if orientation & (1 << k):
            seq[v] += 1
        else:
            seq[u] += 1
    return tuple(seq)


# ---- Setup ----

print("Setting up K(3,3) TCOs...")
tcos = [o for o in range(1 << N_EDGES) if is_totally_cyclic(o)]
tco_set = set(tcos)
print(f"Found {len(tcos)} TCOs\n")

# Group TCOs by out-degree sequence (= reversal class)
classes = defaultdict(list)
for o in tcos:
    classes[out_degree_seq(o)].append(o)

print(f"Found {len(classes)} reversal classes")
for seq, members in sorted(classes.items()):
    print(f"  out-deg {seq}: {len(members)} TCOs")

# ---- Collect all cycle masks ----

print("\nCollecting all cycle masks...")
all_masks_dict = {}  # mask -> representative cycle (vertex list)
for o in tcos:
    for c in find_all_simple_cycles(o):
        m = cycle_to_edge_mask(c)
        if m not in all_masks_dict:
            all_masks_dict[m] = c

# Separate C4 and C6 masks
c4_masks = {m: c for m, c in all_masks_dict.items() if len(c) == 4}
c6_masks = {m: c for m, c in all_masks_dict.items() if len(c) == 6}
all_masks = list(all_masks_dict.keys())

print(f"Total distinct cycle masks: {len(all_masks)} ({len(c4_masks)} C4, {len(c6_masks)} C6)")

# ---- Label the 9 C4 cycles using the grid notation ----

LEFT_PAIRS = [(0,1), (0,2), (1,2)]
RIGHT_PAIRS = [(3,4), (3,5), (4,5)]

# Labels: a=L01/R01, b=L01/R02, c=L01/R12, d=L02/R01, e=L02/R02, f=L02/R12,
#         g=L12/R01, h=L12/R02, i=L12/R12
label_names = 'abcdefghi'
mask_to_label = {}
label_to_mask = {}
label_grid = {}  # (lp_idx, rp_idx) -> label

for li, lp in enumerate(LEFT_PAIRS):
    for ri, rp in enumerate(RIGHT_PAIRS):
        label = label_names[li * 3 + ri]
        for m, c in c4_masks.items():
            verts = set(c)
            if set(lp) <= verts and set(rp) <= verts:
                mask_to_label[m] = label
                label_to_mask[label] = m
                label_grid[(li, ri)] = m
                break

print("\nC4 cycle labels:")
print("     R01  R02  R12")
for li, lp in enumerate(LEFT_PAIRS):
    row = f"L{''.join(str(v) for v in lp)}: "
    for ri in range(3):
        row += f"  {label_names[li*3+ri]}  "
    print(row)

# Also label C6 masks
c6_labels = {}
for i, m in enumerate(sorted(c6_masks.keys())):
    lbl = f"C6_{i+1}"
    c6_labels[m] = lbl
    mask_to_label[m] = lbl

def mask_label(m):
    return mask_to_label.get(m, f"mask_{m}")


# ============================================================
# APPROACH 1: Uniquely Required Circuits (Blocking Pairs)
# ============================================================

print("\n" + "="*60)
print("APPROACH 1: UNIQUELY REQUIRED CIRCUITS")
print("="*60)

# For each pair of TCOs in the same reversal class,
# find all masks that directly connect them.

# First, precompute for each TCO which masks are available
tco_avail_masks = {}
for o in tcos:
    masks = set()
    for c in find_all_simple_cycles(o):
        masks.add(cycle_to_edge_mask(c))
    tco_avail_masks[o] = masks

# For each pair (u, v) in the same class:
# masks that connect u->v = { m : m in avail(u), u^m = v }
# equivalently = avail(u) ∩ avail(v) where m=u^v... wait, m = u XOR v,
# and we need m to be a directed cycle in BOTH u and v.
# Actually: reversing m in u gives u^m = v.
# m must be a cycle in u (directed). After reversal, m is reversed in v=u^m.
# So m is also a cycle in v (reversed direction).
# The mask m that connects u and v is unique: m = u XOR v.
# But we need to check that m is actually a valid cycle in u.

pair_data = []  # (class_seq, u, v, list_of_valid_masks)
# Actually, for a given pair (u,v), the only possible connecting mask is m = u^v.
# We just need to check if m is a directed cycle in u (and equivalently in v reversed).

print("\nFor each same-class pair, the connecting mask is unique: m = u XOR v")
print("We just need to check if it's a valid directed cycle in u.\n")

# Collect all same-class pairs and their connecting masks
same_class_pairs = []
for seq, members in classes.items():
    for u, v in combinations(members, 2):
        m = u ^ v
        # Check: is m a valid directed cycle in u?
        if m in tco_avail_masks[u]:
            same_class_pairs.append((seq, u, v, m))

print(f"Total same-class pairs connected by some cycle: {len(same_class_pairs)}")
print(f"Total same-class pairs: {sum(len(v)*(len(v)-1)//2 for v in classes.values())}")

# Build the full flip graph edge set
flip_edges = set()
for seq, u, v, m in same_class_pairs:
    flip_edges.add((min(u,v), max(u,v)))

print(f"\nFlip graph has {len(flip_edges)} edges total")

# Now analyze: for each edge (u,v), what is the UNIQUE connecting mask?
# (It's always u^v if it's a cycle; there's exactly one mask per edge.)
# But within a generating set context, the question is:
# which masks are "required" because no other mask connects that pair?
# Since each pair has exactly ONE possible mask (u^v), every edge requires its unique mask.

print("\nKey insight: Each pair (u,v) in the same class is connected by EXACTLY ONE mask: u XOR v.")
print("So the flip graph is just: nodes=TCOs, edges={(u,v) : u^v is a directed cycle in u}.")
print("Each edge corresponds to a unique mask. To generate the flip graph using a subset S of masks,")
print("S must include all masks needed to CONNECT each reversal class.")
print()

# Which masks appear as edges?
mask_edges = defaultdict(list)  # mask -> list of (u,v) pairs it connects
for seq, u, v, m in same_class_pairs:
    mask_edges[m].append((u, v))

print("Masks and how many same-class pairs they connect:")
c4_edge_counts = []
c6_edge_counts = []
for m in sorted(c4_masks.keys(), key=lambda m: mask_to_label[m]):
    lbl = mask_to_label[m]
    cnt = len(mask_edges[m])
    c4_edge_counts.append((lbl, cnt))
    print(f"  C4 mask {lbl}: connects {cnt} pairs")

print()
for m in sorted(c6_masks.keys()):
    lbl = mask_to_label[m]
    cnt = len(mask_edges[m])
    c6_edge_counts.append((lbl, cnt))
    print(f"  C6 mask {lbl}: connects {cnt} pairs")


# ============================================================
# APPROACH 2: Minimum vertex cut in the flip graph
# ============================================================

print("\n" + "="*60)
print("APPROACH 2: STRUCTURE OF FLIP GRAPH COMPONENTS")
print("="*60)

print("\nFor each reversal class, list TCOs and their connections (mask labels):")
for seq, members in sorted(classes.items(), key=lambda x: (sum(x[0][:3]==2 for _ in [1]), x[0])):
    n_heavy_left = sum(1 for i in range(3) if seq[i] == 2)
    print(f"\n  Class {seq} (heavy: {n_heavy_left}L/{3-n_heavy_left}R), size {len(members)}:")
    for u in sorted(members):
        connections = []
        for v in sorted(members):
            if u != v:
                m = u ^ v
                if m in tco_avail_masks[u]:
                    connections.append(f"{v}[{mask_label(m)}]")
        print(f"    TCO {u:3d}: connects to {', '.join(connections)}")


# ============================================================
# APPROACH 3: Analyze which masks are "critical edges"
# (bridges in the flip graph components)
# ============================================================

print("\n" + "="*60)
print("APPROACH 3: BRIDGE / CRITICAL EDGE ANALYSIS")
print("="*60)

# Build per-class flip graphs
def build_class_graph(members):
    """Adjacency list for one reversal class."""
    adj = defaultdict(list)
    for u, v in combinations(members, 2):
        m = u ^ v
        if m in tco_avail_masks[u]:
            adj[u].append((v, m))
            adj[v].append((u, m))
    return adj

def find_bridges(members, adj):
    """Find all bridge edges in the class graph (using DFS)."""
    # An edge is a bridge if removing it disconnects the graph.
    # For small graphs, brute force: remove each edge and check connectivity.
    bridges = []
    edges_in_class = []
    for u in members:
        for v, m in adj[u]:
            if u < v:
                edges_in_class.append((u, v, m))

    for eu, ev, em in edges_in_class:
        # Remove this edge and check connectivity
        visited = set()
        start = members[0]
        stack = [start]
        visited.add(start)
        while stack:
            cur = stack.pop()
            for nb, nm in adj[cur]:
                if nb not in visited:
                    if not (cur == eu and nb == ev) and not (cur == ev and nb == eu):
                        visited.add(nb)
                        stack.append(nb)
        if len(visited) < len(members):
            bridges.append((eu, ev, em))
    return bridges

print("\nBridges (critical edges) in each reversal class:")
all_bridges = []
for seq, members in sorted(classes.items()):
    adj = build_class_graph(members)
    bridges = find_bridges(members, adj)
    n_heavy_left = sum(1 for i in range(3) if seq[i] == 2)
    if bridges:
        bridge_masks = [mask_label(em) for _,_,em in bridges]
        print(f"  Class {seq} ({n_heavy_left}L/{3-n_heavy_left}R): {len(bridges)} bridge(s): {bridge_masks}")
        all_bridges.extend([(seq, u, v, m) for u,v,m in bridges])
    else:
        print(f"  Class {seq} ({n_heavy_left}L/{3-n_heavy_left}R): no bridges (2-edge-connected)")

# Count which masks appear as bridges
bridge_mask_counts = defaultdict(int)
for _, u, v, m in all_bridges:
    bridge_mask_counts[m] += 1

print(f"\nTotal bridge edges: {len(all_bridges)}")
print("Bridge mask frequency:")
for m, cnt in sorted(bridge_mask_counts.items(), key=lambda x: mask_label(x[0])):
    print(f"  {mask_label(m)}: appears as bridge in {cnt} classes")


# ============================================================
# APPROACH 4: Required masks per reversal class
# ============================================================

print("\n" + "="*60)
print("APPROACH 4: MINIMUM SPANNING MASKS PER CLASS")
print("="*60)

# For each reversal class, what is the minimum set of masks needed
# to keep that class connected?
# This is related to the edge connectivity / spanning trees.

print("\nFor each class, find all edges and which masks they use:")
mask_class_usage = defaultdict(set)  # mask -> set of classes that need it

for seq, members in sorted(classes.items()):
    adj = build_class_graph(members)
    edges_in_class = []
    for u in members:
        for v, m in adj[u]:
            if u < v:
                edges_in_class.append((u, v, m))

    n_heavy_left = sum(1 for i in range(3) if seq[i] == 2)
    masks_in_class = {m for _,_,m in edges_in_class}
    mask_labels = sorted([mask_label(m) for m in masks_in_class])
    print(f"  {seq} ({n_heavy_left}L/{3-n_heavy_left}R): uses masks {mask_labels}")
    for m in masks_in_class:
        mask_class_usage[m].add(seq)

print("\nWhich masks appear in which classes:")
for m in sorted(c4_masks.keys(), key=lambda m: mask_to_label[m]):
    lbl = mask_to_label[m]
    classes_using = sorted(mask_class_usage[m])
    print(f"  {lbl}: used in {len(classes_using)} classes")


# ============================================================
# APPROACH 5: The "required mask" set — which masks must ANY generating set include?
# ============================================================

print("\n" + "="*60)
print("APPROACH 5: REQUIRED MASKS (necessary conditions)")
print("="*60)

# A mask m is "required" if there exists a same-class pair (u,v) such that:
# m = u^v is the ONLY mask that could possibly connect u and v.
# Since each pair has exactly one connecting mask (u^v), every edge in the flip graph
# corresponds to a unique mask. The question is: can some other path of reversals
# connect u and v without using mask m?
#
# m is required iff removing mask m disconnects some reversal class (i.e., m is a bridge in some class).

print("\nA mask is 'required' iff it is a bridge in some reversal class.")
print("Required masks:")
required_masks = set(bridge_mask_counts.keys())
for m in sorted(required_masks, key=lambda m: mask_label(m)):
    print(f"  {mask_label(m)}: bridge in {bridge_mask_counts[m]} classes")

print(f"\nTotal required masks: {len(required_masks)}")
print("Are all required masks C4?", all(m in c4_masks for m in required_masks))
print("Are all C4 masks required?", all(m in required_masks for m in c4_masks))


# ============================================================
# APPROACH 6: Why 4 masks always fail
# ============================================================

print("\n" + "="*60)
print("APPROACH 6: WHY 4 MASKS ALWAYS FAIL")
print("="*60)

# Strategy: show that for any set of 4 masks, there's some reversal class
# that becomes disconnected.

# First, understand the structure: which 4-element subsets of C4 masks fail?
# All C(9,4) = 126 subsets of 4 C4 masks fail (from the exhaustive search).
# Also all sets including C6 masks fail (since C6 never appears in a minimal set).

# Let's find, for each 4-element subset S of C4 masks, which class it fails on.
print("\nFor each 4-element subset of C4 masks, find which classes it fails to connect...")

c4_mask_list = sorted(c4_masks.keys(), key=lambda m: mask_to_label[m])

fail_reason = {}  # subset -> list of (seq, reason)
for subset in combinations(c4_mask_list, 4):
    subset_set = set(subset)
    # Check each class
    failed_classes = []
    for seq, members in classes.items():
        # Build restricted flip graph for this class
        reachable = set()
        start = members[0]
        stack = [start]
        reachable.add(start)
        while stack:
            cur = stack.pop()
            for other in members:
                if other not in reachable:
                    m = cur ^ other
                    if m in subset_set and m in tco_avail_masks[cur]:
                        reachable.add(other)
                        stack.append(other)
        if len(reachable) < len(members):
            failed_classes.append(seq)
    fail_reason[subset] = failed_classes

# Show statistics
all_4_subsets = list(combinations(c4_mask_list, 4))
print(f"\nAll {len(all_4_subsets)} 4-element C4 subsets fail (as expected).")

# For each 4-subset, how many classes does it fail on?
n_failed = [len(fail_reason[s]) for s in all_4_subsets]
from collections import Counter
fail_dist = Counter(n_failed)
print("Distribution of #failed classes per 4-subset:")
for k in sorted(fail_dist):
    print(f"  Fails {k} class(es): {fail_dist[k]} subsets")

# Which mask, when ABSENT, causes the most failures?
print("\nFor each C4 mask, how many 4-subsets (excluding it) fail on each class?")
# Equivalently: for each mask m not in subset, how does absence of m hurt?
# Let's look at it differently: for each mask m, all 4-subsets NOT containing m.
print("\nFor each C4 mask m, what fraction of 4-subsets NOT containing m fail?")
for m in c4_mask_list:
    subsets_without_m = [s for s in all_4_subsets if m not in s]
    # All of these fail since no 4-subset generates!
    # Instead: look at the SPECIFIC class that fails
    class_failures = defaultdict(int)
    for s in subsets_without_m:
        for seq in fail_reason[s]:
            class_failures[seq] += 1
    # Top failing class
    if class_failures:
        top = max(class_failures, key=class_failures.get)
        print(f"  Without {mask_to_label[m]}: {len(subsets_without_m)} subsets, "
              f"most common failure class {top} ({class_failures[top]}x)")


# ============================================================
# APPROACH 7: The "certificate" — find 5 disjoint blocking pairs
# ============================================================

print("\n" + "="*60)
print("APPROACH 7: CERTIFICATE OF LOWER BOUND")
print("="*60)

# Goal: find 5 pairs (u1,v1), ..., (u5,v5), each in the same reversal class,
# such that each pair requires a DIFFERENT mask, AND the 5 masks are all distinct.
#
# Better: find 5 same-class pairs requiring 5 DIFFERENT masks such that
# no mask appears as an edge in any OTHER pair's path-alternatives.
#
# Since each same-class pair (u,v) is connected by EXACTLY ONE mask (u^v),
# and since the flip graph within each class is small (5 or 6 nodes),
# a generating set S must include enough masks to keep each class connected.
#
# The minimum spanning "mask set" for a class is the minimum set of masks
# whose edges form a spanning tree of that class.
# The union of minimum spanning sets across all classes gives a lower bound.

# Let's find the minimum mask set needed for each class (minimum spanning "mask forest")
print("\nMinimum mask set to span each class (minimum spanning tree by mask set):")

def min_masks_for_class(members, all_avail):
    """Find minimum set of masks that keeps this class connected."""
    # Build the class graph
    edges = []
    for u, v in combinations(members, 2):
        m = u ^ v
        if m in tco_avail_masks[u]:
            edges.append((u, v, m))

    # Find minimum number of distinct masks needed to span
    # (spanning tree on the class graph where we can use any edge with those masks)
    n = len(members)
    masks_used = {m for _,_,m in edges}

    # Try all subsets of masks (smallest first)
    for size in range(1, len(masks_used) + 1):
        for subset in combinations(sorted(masks_used, key=lambda m: mask_label(m)), size):
            subset_set = set(subset)
            # Check connectivity
            visited = {members[0]}
            changed = True
            while changed:
                changed = False
                for u, v, m in edges:
                    if m in subset_set:
                        if u in visited and v not in visited:
                            visited.add(v)
                            changed = True
                        elif v in visited and u not in visited:
                            visited.add(u)
                            changed = True
            if len(visited) == n:
                return size, list(subset), masks_used
    return len(masks_used), list(masks_used), masks_used

print("\nDetailed analysis per class:")
class_min_masks = {}
for seq, members in sorted(classes.items()):
    n_heavy_left = sum(1 for i in range(3) if seq[i] == 2)
    size, min_set, all_used = min_masks_for_class(members, tco_avail_masks)
    class_min_masks[seq] = (size, min_set, all_used)
    min_labels = sorted([mask_label(m) for m in min_set])
    all_labels = sorted([mask_label(m) for m in all_used])
    print(f"  {seq} ({n_heavy_left}L/{3-n_heavy_left}R, size {len(members)}): "
          f"min masks = {size} ({min_labels}), all used = {all_labels}")


# ============================================================
# APPROACH 8: The "sunflower" / intersection structure
# ============================================================

print("\n" + "="*60)
print("APPROACH 8: COMPLEMENT PATTERN OF MINIMAL SETS")
print("="*60)

# The 9 minimal sets each use 5 of 9 C4 masks. The COMPLEMENT (missing 4 cycles)
# might have a pattern.

# From the problem statement, the minimal sets are:
# Set 1: {a,b,d,e,i}    complement: {c,f,g,h}
# Set 2: {c,d,e,g,h}    complement: {a,b,f,i}
# Set 3: {a,c,d,f,h}    complement: {b,e,g,i}
# Set 4: {b,d,f,g,i}    complement: {a,c,e,h}
# Set 5: {b,c,d,h,i}    complement: {a,e,f,g}  -- wait, let me recalculate from mask data

# Get the actual minimal sets from exhaustive check
print("\nFinding minimal generating sets...")

def count_comps_subset(subset_set):
    adj = {o: set() for o in tcos}
    for o in tcos:
        for m in tco_avail_masks[o]:
            if m in subset_set:
                nb = o ^ m
                if nb in tco_set and nb != o:
                    adj[o].add(nb)
                    adj[nb].add(o)
    visited = set()
    count = 0
    for o in tcos:
        if o not in visited:
            count += 1
            stack = [o]
            visited.add(o)
            while stack:
                cur = stack.pop()
                for nb in adj[cur]:
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
    return count

min_sets_found = []
for subset in combinations(c4_mask_list, 5):
    if count_comps_subset(set(subset)) == 20:
        min_sets_found.append(subset)

print(f"Found {len(min_sets_found)} minimal generating sets (all C4, size 5)")

print("\nAnalysis of complement patterns (4 missing cycles per set):")
print("     " + "  ".join(mask_to_label[m] for m in c4_mask_list))
for i, s in enumerate(min_sets_found):
    s_set = set(s)
    complement = [mask_to_label[m] for m in c4_mask_list if m not in s_set]
    present = [mask_to_label[m] for m in c4_mask_list if m in s_set]

    # Check if complement forms a "row cover" or "column cover" in the 3x3 grid
    # Rows = left pairs L01, L02, L12
    # Cols = right pairs R01, R02, R12
    c_set = set(complement)

    row_covered = []
    for li, lp in enumerate(LEFT_PAIRS):
        row_masks = {mask_to_label[label_grid[(li, ri)]] for ri in range(3)}
        if row_masks <= c_set:
            row_covered.append(f"L{''.join(str(v) for v in lp)}")

    col_covered = []
    for ri, rp in enumerate(RIGHT_PAIRS):
        col_masks = {mask_to_label[label_grid[(li, ri)]] for li in range(3)}
        if col_masks <= c_set:
            col_covered.append(f"R{''.join(str(v-3) for v in rp)}")

    complement_str = "{" + ",".join(sorted(complement)) + "}"
    print(f"  Set {i+1:2d}: complement {complement_str:20s} | "
          f"row cover: {row_covered or 'none'}, col cover: {col_covered or 'none'}")

# Grid visualization of each minimal set
print("\nGrid visualization (X=present, .=absent):")
print("       R01 R02 R12")
for i, s in enumerate(min_sets_found):
    s_set = set(s)
    row_str = f"  Set {i+1:2d}: "
    for li in range(3):
        for ri in range(3):
            row_str += "X" if label_grid[(li,ri)] in s_set else "."
        row_str += " "
    print(row_str)

# Check the complement structure more carefully
print("\nComplement grids (X=missing):")
for i, s in enumerate(min_sets_found):
    s_set = set(s)
    row_str = f"  Set {i+1:2d}: "
    for li in range(3):
        for ri in range(3):
            row_str += "X" if label_grid[(li,ri)] not in s_set else "."
        row_str += " "
    print(row_str)


# ============================================================
# APPROACH 9: Detailed look at the size-6 classes (special cases)
# ============================================================

print("\n" + "="*60)
print("APPROACH 9: SIZE-6 CLASSES — DETAILED STRUCTURE")
print("="*60)

# There are 2 size-6 classes: (0,0,0,2,2,2) and (2,2,2,0,0,0)
size6_classes = [(seq, members) for seq, members in classes.items() if len(members) == 6]
for seq, members in size6_classes:
    n_heavy_left = sum(1 for i in range(3) if seq[i] == 2)
    print(f"\nClass {seq} (heavy: {n_heavy_left}L/{3-n_heavy_left}R), size 6:")

    # All edges in this class
    edges_in_class = []
    for u, v in combinations(members, 2):
        m = u ^ v
        if m in tco_avail_masks[u]:
            edges_in_class.append((u, v, m))

    # Show the graph
    for u, v, m in sorted(edges_in_class):
        print(f"  {u:3d} <-[{mask_label(m):4s}]-> {v:3d}")

    # Degree of each node
    print("\n  Degree sequence:")
    for u in sorted(members):
        nbrs = [(v, mask_label(m)) for uu,v,m in edges_in_class if uu==u] + \
               [(u2, mask_label(m)) for u2,v,m in edges_in_class if v==u]
        # deduplicate
        seen = {}
        for nbr, lbl in nbrs:
            if nbr not in seen:
                seen[nbr] = lbl
        print(f"    {u}: degree {len(seen)}, neighbors: {seen}")

    # Which masks appear?
    masks_here = {m for _,_,m in edges_in_class}
    mask_labels_here = sorted([mask_label(m) for m in masks_here])
    print(f"\n  Masks used: {mask_labels_here}")

    # Edge connectivity (min cut)
    print("\n  Checking edge connectivity...")
    # For the 6-node complete-ish graph, find min edge cut

    # Count edges per mask
    mask_degree = defaultdict(int)
    for _,_,m in edges_in_class:
        mask_degree[m] += 1
    for m in sorted(mask_degree, key=lambda m: mask_label(m)):
        print(f"    Mask {mask_label(m)}: {mask_degree[m]} edges in this class")


# ============================================================
# APPROACH 10: Hypergraph / linear algebra view
# ============================================================

print("\n" + "="*60)
print("APPROACH 10: KEY STRUCTURAL THEOREM")
print("="*60)

# Let's think about this more carefully.
#
# We have 20 reversal classes. The flip graph on all 102 TCOs has 20 components.
# A generating set S of masks is valid iff the S-restricted flip graph also has 20 components
# (i.e., S doesn't merge any two same-class TCOs into separate components).
#
# Actually: a generating set is valid iff for every class, the S-restricted flip graph
# restricted to that class is still connected.
#
# So the question is: what is the minimum S such that for EVERY class,
# the edges of that class using masks in S form a connected subgraph?
#
# This is a set cover / covering design problem.

# Let's analyze: for each mask m, which classes does it "help connect"?
# And for each class, what's the minimum number of masks needed?

print("\nFor each reversal class, what is the minimum number of DISTINCT masks needed to span it?")
print("(This is a lower bound on the generating set size.)")

# We already computed this above. Let's summarize.
print("\nSummary of min mask sizes per class:")
min_size_dist = Counter()
max_needed = 0
for seq, (size, min_set, all_used) in class_min_masks.items():
    min_size_dist[size] += 1
    max_needed = max(max_needed, size)

for k in sorted(min_size_dist):
    print(f"  Min {k} mask(s): {min_size_dist[k]} class(es)")

print(f"\nLargest min mask requirement: {max_needed}")

# Now: the key insight for gamma >= 5
# We need S such that S spans ALL classes simultaneously.
# By inclusion-exclusion / covering arguments, we need |S| >= ?

# Let's find the MAXIMUM over all classes of the minimum masks needed,
# AND also look at "disjoint requirements."

# Find classes where required masks are disjoint
print("\nLooking for classes with pairwise DISJOINT minimum spanning mask sets...")
# For classes where the minimum spanning set is unique, those masks are "fixed"

classes_with_unique_span = []
for seq, members in classes.items():
    n_heavy_left = sum(1 for i in range(3) if seq[i] == 2)
    # Find ALL minimum-size spanning sets for this class
    edges_in_class = [(u,v,m) for u,v in combinations(members,2)
                      for m in [u^v] if m in tco_avail_masks[u]]
    masks_in_class = list({m for _,_,m in edges_in_class})
    min_size = class_min_masks[seq][0]

    all_min_sets = []
    for subset in combinations(masks_in_class, min_size):
        subset_set = set(subset)
        visited = {members[0]}
        changed = True
        while changed:
            changed = False
            for u, v, m in edges_in_class:
                if m in subset_set:
                    if u in visited and v not in visited:
                        visited.add(v); changed = True
                    elif v in visited and u not in visited:
                        visited.add(u); changed = True
        if len(visited) == len(members):
            all_min_sets.append(subset)

    print(f"\n  {seq} ({n_heavy_left}L/{3-n_heavy_left}R), size {len(members)}:")
    print(f"    Min spanning set size: {min_size}")
    print(f"    Number of min spanning sets: {len(all_min_sets)}")
    if len(all_min_sets) <= 10:
        for ms in all_min_sets:
            print(f"      {sorted([mask_label(m) for m in ms])}")

    # Intersection of all min sets = absolutely required masks for this class
    if all_min_sets:
        required = set(all_min_sets[0])
        for ms in all_min_sets[1:]:
            required &= set(ms)
        print(f"    Absolutely required for this class: {sorted([mask_label(m) for m in required])}")


# ============================================================
# FINAL SUMMARY: The combinatorial structure
# ============================================================

print("\n" + "="*60)
print("FINAL SUMMARY: KEY OBSERVATIONS FOR THE PROOF")
print("="*60)

# Re-examine the structure of the complete flip graph
# Edges are indexed by their unique mask
# A generating set S must cover/span each class

# For the lower bound, we use a fractional/cover argument:
# Count how many distinct masks are "essential" across all classes.

# Key question: is there a set of k "independent" constraints each requiring a different mask?

# Observation: the flip graph within each class is a small graph (5 or 6 nodes).
# For size-5 classes with min spanning mask = 1 (a single mask connects all):
#   No -- min spanning mask size >= 1 always, but what's the structure?

print("\nAll flip graph edges, organized by mask:")
for m in sorted(c4_masks.keys(), key=lambda m: mask_to_label[m]):
    lbl = mask_to_label[m]
    edges = mask_edges[m]
    classes_for_mask = defaultdict(list)
    for u,v in edges:
        seq = out_degree_seq(u)
        classes_for_mask[seq].append((u,v))
    print(f"\n  Mask {lbl}: {len(edges)} edges total, in {len(classes_for_mask)} classes")
    for seq, pairs in sorted(classes_for_mask.items()):
        n_heavy_left = sum(1 for i in range(3) if seq[i] == 2)
        print(f"    Class {seq} ({n_heavy_left}L/{3-n_heavy_left}R): {len(pairs)} edges")

print("\n" + "="*60)
print("COMPLETE EDGE LIST OF FULL FLIP GRAPH")
print("="*60)
print("\nAll 210 edges (sorted by mask label):")
for m in sorted(c4_masks.keys(), key=lambda m: mask_to_label[m]):
    lbl = mask_to_label[m]
    for u, v in sorted(mask_edges[m]):
        seq = out_degree_seq(u)
        n_heavy_left = sum(1 for i in range(3) if seq[i] == 2)
        print(f"  {lbl}: {u:3d} <-> {v:3d}  (class {n_heavy_left}L/{3-n_heavy_left}R)")
for m in sorted(c6_masks.keys()):
    lbl = mask_to_label[m]
    for u, v in sorted(mask_edges[m]):
        seq = out_degree_seq(u)
        n_heavy_left = sum(1 for i in range(3) if seq[i] == 2)
        print(f"  {lbl}: {u:3d} <-> {v:3d}  (class {n_heavy_left}L/{3-n_heavy_left}R)")
