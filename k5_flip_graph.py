from collections import defaultdict, deque, Counter
from itertools import combinations
from math import comb

# K5: all pairs of {0,1,2,3,4}
N_VERTICES = 5
EDGES = [(i, j) for i in range(5) for j in range(i + 1, 5)]
N_EDGES = len(EDGES)  # 10
EDGE_INDEX = {frozenset([u, v]): k for k, (u, v) in enumerate(EDGES)}
CYCLE_RANK = N_EDGES - N_VERTICES + 1  # 6


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
        src, dst = (v, u) if (orientation >> k) & 1 else (u, v)
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
        if (orientation >> k) & 1:
            seq[v] += 1
        else:
            seq[u] += 1
    return tuple(seq)


def count_comps(adj_dict, nodes):
    visited = set()
    count = 0
    for o in nodes:
        if o not in visited:
            count += 1
            stack = [o]
            visited.add(o)
            while stack:
                cur = stack.pop()
                for nb in adj_dict[cur]:
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
    return count


if __name__ == "__main__":
    print(f"K5: {N_VERTICES} vertices, {N_EDGES} edges, cycle rank = {CYCLE_RANK}")
    print(f"Total orientations: {1 << N_EDGES}\n")

    # --- TCOs ---
    print("Computing TCOs...")
    tcos = [o for o in range(1 << N_EDGES) if is_totally_cyclic(o)]
    tco_set = set(tcos)
    print(f"Found {len(tcos)} TCOs\n")

    # --- Equivalence classes via out-degree sequence ---
    classes = defaultdict(list)
    for o in tcos:
        classes[out_degree_seq(o)].append(o)
    n_classes = len(classes)
    size_counts = Counter(len(v) for v in classes.values())
    print(f"Equivalence classes (out-degree invariant): {n_classes}")
    for sz in sorted(size_counts):
        print(f"  {size_counts[sz]}x size-{sz}")
    print()

    # --- All distinct cycle masks ---
    print("Collecting distinct cycle masks across all TCOs...")
    all_masks = {}
    avail = {o: set() for o in tcos}
    for o in tcos:
        for c in find_all_simple_cycles(o):
            m = cycle_to_edge_mask(c)
            if m not in all_masks:
                all_masks[m] = c
            avail[o].add(m)

    length_counts = Counter(len(c) for c in all_masks.values())
    print(f"Distinct cycle masks: {len(all_masks)}")
    for l in sorted(length_counts):
        print(f"  {length_counts[l]}x C{l}")
    print()

    # --- Full flip graph ---
    print("Building full flip graph...")
    flip_graph = {o: set() for o in tcos}
    for o in tcos:
        for m in avail[o]:
            nb = o ^ m
            if nb in tco_set and nb != o:
                flip_graph[o].add(nb)
                flip_graph[nb].add(o)

    n_full_comps = count_comps(flip_graph, tcos)
    total_edges = sum(len(v) for v in flip_graph.values()) // 2
    print(f"Full flip graph: {len(tcos)} nodes, {total_edges} edges, {n_full_comps} components")
    comp_sizes = Counter()
    visited = set()
    for o in tcos:
        if o not in visited:
            stack, comp = [o], []
            visited.add(o)
            while stack:
                cur = stack.pop()
                comp.append(cur)
                for nb in flip_graph[cur]:
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
            comp_sizes[len(comp)] += 1
    for sz in sorted(comp_sizes, reverse=True):
        print(f"  {comp_sizes[sz]}x size-{sz}")
    print()

    # --- Minimum generator search ---
    target = n_full_comps
    mask_list = list(all_masks.keys())
    n_masks = len(mask_list)
    print(f"Minimum generator search (target: {target} components, cycle rank = {CYCLE_RANK})")
    print(f"Pool of {n_masks} distinct cycle masks\n")

    def count_comps_subset(subset_set):
        adj = {o: set() for o in tcos}
        for o in tcos:
            for m in avail[o]:
                if m in subset_set:
                    nb = o ^ m
                    if nb in tco_set and nb != o:
                        adj[o].add(nb)
                        adj[nb].add(o)
        return count_comps(adj, tcos)

    found = False
    for size in range(1, CYCLE_RANK + 3):
        total_subsets = comb(n_masks, size)
        if total_subsets > 2_000_000:
            print(f"  Size {size}: {total_subsets:,} subsets — too large to check exhaustively, stopping.")
            break
        good = 0
        for subset in combinations(mask_list, size):
            if count_comps_subset(set(subset)) == target:
                good += 1
        print(f"  Size {size}: {total_subsets:5,} subsets → {good} generating sets")
        if good:
            print(f"  ✓ Minimum generating set size = {size}  (cycle rank = {CYCLE_RANK})")
            found = True
            break

    if not found:
        print(f"\n  Did not find minimum within search bounds.")
        print(f"  Cycle rank = {CYCLE_RANK}. If minimum > {CYCLE_RANK}, Alex's conjecture holds for K5.")
