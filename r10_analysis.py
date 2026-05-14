"""
R10 flip graph analysis.
Minimum circuit generating set for the circuit reversal system on
totally cyclic orientations of the R10 matroid.

R10 is the unique non-graphic, non-cographic regular matroid that
appears in Seymour's decomposition of regular matroids.
Represented by A = [I_5 | D] where D_ij = 1 if i==j, -1 if (i-j)%5 in {1,4}.
"""
import numpy as np
from itertools import combinations
from collections import Counter
from math import comb

N_ELEMENTS = 10
RANK = 5
CYCLE_RANK = N_ELEMENTS - RANK  # 5

# Build A = [I_5 | D]
D = np.zeros((RANK, RANK), dtype=int)
for i in range(RANK):
    for j in range(RANK):
        if i == j:
            D[i, j] = 1
        elif (i - j) % RANK in {1, 4}:
            D[i, j] = -1

A = np.hstack([np.eye(RANK, dtype=int), D])

print("R10 matrix A = [I_5 | D]:")
print(A)
print(f"\nCycle rank = {CYCLE_RANK}")


def mat_rank(cols):
    if not cols:
        return 0
    return int(np.linalg.matrix_rank(A[:, sorted(cols)].astype(float)))


# --- Circuit enumeration (check all 2^10 subsets) ---
print("\nEnumerating circuits...")
dependent_sets = []
for mask in range(1, 1 << N_ELEMENTS):
    cols = [k for k in range(N_ELEMENTS) if (mask >> k) & 1]
    if mat_rank(cols) < len(cols):
        dependent_sets.append(frozenset(cols))

circuits = []
for S in dependent_sets:
    if not any(C < S for C in dependent_sets if C != S):
        circuits.append(S)

size_dist = Counter(len(c) for c in circuits)
print(f"Found {len(circuits)} circuits: {dict(sorted(size_dist.items()))}")


# --- Signed circuits ---
def get_signed_circuit(C):
    """Return (plus_mask, minus_mask) bitmasks for canonical signing of circuit C.
    Canonical: smallest element of C is in plus."""
    C_list = sorted(C)
    submat = A[:, C_list].astype(float)
    _, _, Vt = np.linalg.svd(submat)
    null = Vt[-1]
    nonzero_abs = np.abs(null[np.abs(null) > 1e-6])
    null = null / np.min(nonzero_abs)
    null = np.round(null).astype(int)
    if null[0] < 0:
        null = -null
    plus_mask = sum(1 << C_list[k] for k, v in enumerate(null) if v > 0)
    minus_mask = sum(1 << C_list[k] for k, v in enumerate(null) if v < 0)
    return plus_mask, minus_mask


circuit_data = []  # (support_mask, plus_mask, minus_mask)
for C in circuits:
    pm, mm = get_signed_circuit(C)
    sm = pm | mm
    circuit_data.append((sm, pm, mm))

print(f"Computed {len(circuit_data)} signed circuits")


# --- Totally cyclic orientations ---
def is_tco(sigma):
    """Orientation sigma is TCO if every element is in some positive circuit."""
    covered = 0
    for sm, pm, mm in circuit_data:
        sigma_c = sigma & sm
        if sigma_c == pm or sigma_c == mm:
            covered |= sm
        if covered == (1 << N_ELEMENTS) - 1:
            return True
    return covered == (1 << N_ELEMENTS) - 1


print("\nEnumerating TCOs...")
tcos = [sigma for sigma in range(1 << N_ELEMENTS) if is_tco(sigma)]
tco_set = set(tcos)
N = len(tcos)
tco_idx = {o: i for i, o in enumerate(tcos)}
print(f"N = {N} totally cyclic orientations")


# --- Flip graph by circuit mask ---
circuit_masks = sorted(set(sm for sm, pm, mm in circuit_data))
M = len(circuit_masks)
mask_idx = {m: i for i, m in enumerate(circuit_masks)}
print(f"M = {M} distinct circuit support masks")

edges_by_mask = [[] for _ in range(M)]
for sigma in tcos:
    for sm, pm, mm in circuit_data:
        sigma_c = sigma & sm
        if sigma_c in (pm, mm):
            sigma_prime = sigma ^ sm
            if sigma_prime in tco_set:
                u, v = tco_idx[sigma], tco_idx[sigma_prime]
                if u < v:
                    mi = mask_idx[sm]
                    edges_by_mask[mi].append((u, v))

edges_by_mask = [list(set(e)) for e in edges_by_mask]
print(f"Flip graph edges per mask: min={min(len(e) for e in edges_by_mask)}, "
      f"max={max(len(e) for e in edges_by_mask)}, "
      f"total={sum(len(e) for e in edges_by_mask)}")


# --- Connectivity check ---
def count_comps(sel):
    parent = list(range(N))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        a, b = find(a), find(b)
        if a != b:
            parent[a] = b

    for mi in sel:
        for u, v in edges_by_mask[mi]:
            union(u, v)
    return sum(1 for i in range(N) if find(i) == i)


TARGET = count_comps(range(M))
print(f"\nFull flip graph components: {TARGET}")

# --- Minimum generating set search ---
print(f"\nSearching for minimum circuit generating set (cycle rank = {CYCLE_RANK})...")
min_found = None
for size in range(1, M + 1):
    total = comb(M, size)
    print(f"  size {size}: checking {total:,} subsets...", end=" ", flush=True)
    good = []
    for subset in combinations(range(M), size):
        if count_comps(subset) == TARGET:
            good.append(subset)
    print(f"found {len(good)}")
    if good:
        min_found = size
        print(f"\n{'='*50}")
        print(f"Minimum = {size}   |   Cycle rank = {CYCLE_RANK}")
        relation = "=" if size == CYCLE_RANK else (">" if size > CYCLE_RANK else "<")
        print(f"γ(R10) {relation} cycle_rank(R10)")
        print(f"Total generating sets of minimum size: {len(good)}")
        print(f"\nSample sets (first 3):")
        for j, subset in enumerate(good[:3]):
            masks = [circuit_masks[i] for i in subset]
            sizes = [bin(m).count('1') for m in masks]
            print(f"  Set {j+1}: circuit sizes {sorted(sizes)}")
            for i in subset:
                sm = circuit_masks[i]
                elems = [k for k in range(N_ELEMENTS) if (sm >> k) & 1]
                print(f"    Circuit: elements {elems} (size {len(elems)})")
        break

if min_found is None:
    print("No generating set found (unexpected)")
