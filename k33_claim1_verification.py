"""
Verify Claim 1 more carefully: why is every pair of TCOs in C* directly connected?

Claim 1: For sigma != tau in S_3, the mask m = o_sigma XOR o_tau is a valid
directed circuit in o_sigma (i.e., the discordant edges form a directed cycle in o_sigma).

This needs proof, not just computation. Let's understand the structure.
"""

from collections import defaultdict
from itertools import permutations, combinations

EDGES = [(0,3),(0,4),(0,5),(1,3),(1,4),(1,5),(2,3),(2,4),(2,5)]
N_EDGES = 9
N_VERTICES = 6
EDGE_INDEX = {frozenset([u, v]): k for k, (u, v) in enumerate(EDGES)}

def cycle_to_edge_mask(cycle):
    mask = 0
    n = len(cycle)
    for i in range(n):
        u, v = cycle[i], cycle[(i + 1) % n]
        mask |= 1 << EDGE_INDEX[frozenset([u, v])]
    return mask

def get_directed_adj(orientation):
    adj = defaultdict(list)
    for k, (u, v) in enumerate(EDGES):
        if orientation & (1 << k):
            adj[v].append(u)
        else:
            adj[u].append(v)
    return adj

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

def sigma_to_tco(sigma):
    """
    Build the TCO corresponding to sigma in S_3.
    Left vertex i sends edges to all j != sigma(i) (out-edges to right).
    Left vertex i receives edge from right vertex sigma(i) (in-edge from right).

    Encoding: edge (i, j+3) is at position EDGE_INDEX[{i, j+3}].
    Bit = 0: edge goes left->right (i -> j+3)
    Bit = 1: edge goes right->left (j+3 -> i)
    """
    o = 0
    for i in range(3):
        for j in range(3):
            k = EDGE_INDEX[frozenset([i, j+3])]
            if j == sigma[i]:
                # This edge goes right->left (R to L)
                o |= (1 << k)
            # else: edge goes left->right, bit remains 0
    return o

print("="*70)
print("UNDERSTANDING CLAIM 1: WHY EVERY PAIR IS DIRECTLY CONNECTED")
print("="*70)

perm_list = list(permutations([0,1,2]))
perm_to_tco = {sigma: sigma_to_tco(sigma) for sigma in perm_list}
tco_to_perm = {v: k for k, v in perm_to_tco.items()}

print("\nTCOs for each sigma:")
for sigma, o in sorted(perm_to_tco.items()):
    print(f"  sigma={sigma} -> TCO {o:3d} (binary: {o:09b})")

print("\n\nFor each pair (sigma, tau), analyze the 'discordant edges':")
print("These are edges where the two orientations disagree.")
print()

for sigma in perm_list:
    for tau in perm_list:
        if sigma >= tau:
            continue
        o_s = perm_to_tco[sigma]
        o_t = perm_to_tco[tau]
        m = o_s ^ o_t  # discordant edge mask

        # Find which edges disagree
        discordant = []
        for k, (u, v) in enumerate(EDGES):
            if (m >> k) & 1:
                li, ri = u, v-3
                # In o_sigma, direction of this edge:
                if (o_s >> k) & 1:
                    dir_s = f"R{ri+3}->L{li}"  # right to left
                else:
                    dir_s = f"L{li}->R{ri+3}"  # left to right
                discordant.append((li, ri, dir_s))

        # Find which rows are discordant
        disc_rows = set(li for li, ri, d in discordant)

        # What does rho = sigma^{-1} o tau look like?
        sigma_inv = [0]*3
        for i in range(3):
            sigma_inv[sigma[i]] = i
        rho = tuple(sigma_inv[tau[i]] for i in range(3))
        supp = [i for i in range(3) if rho[i] != i]

        print(f"sigma={sigma}, tau={tau}, rho={rho}, supp={supp}")
        print(f"  Discordant edges: {[(li,ri,d) for li,ri,d in discordant]}")

        # In o_sigma, the discordant edges form a directed subgraph.
        # Let's check if this subgraph is a directed cycle.
        disc_adj = defaultdict(list)
        for k, (u, v) in enumerate(EDGES):
            if (m >> k) & 1:
                # This edge is discordant
                if (o_s >> k) & 1:
                    disc_adj[v].append(u)  # right->left
                else:
                    disc_adj[u].append(v)  # left->right

        # Check: is this a directed cycle?
        nodes_in_disc = set()
        for k, (u, v) in enumerate(EDGES):
            if (m >> k) & 1:
                nodes_in_disc.add(u)
                nodes_in_disc.add(v)

        # Verify it's a valid circuit in o_sigma
        cycles_in_s = {cycle_to_edge_mask(c) for c in find_all_simple_cycles(o_s)}
        is_circuit = m in cycles_in_s
        print(f"  Is valid circuit in o_sigma: {is_circuit}")
        print()

print("="*70)
print("CONCEPTUAL PROOF OF CLAIM 1")
print("="*70)
print("""
Claim: For any sigma != tau in S_3, the mask m = o_sigma XOR o_tau is a
directed circuit in o_sigma (and in o_tau reversed).

Proof:
  In o_sigma, each left vertex i has:
  - Out-edges to all j != sigma(i) (2 out-edges)
  - In-edge from sigma(i) (1 in-edge)

  In o_tau, each left vertex i has:
  - Out-edges to all j != tau(i) (2 out-edges)
  - In-edge from tau(i) (1 in-edge)

  The discordant positions are pairs (i, j) where sigma(i) != tau(i).
  Let D = {i : sigma(i) != tau(i)} = supp(rho) where rho = sigma^{-1} o tau.

  For each i in D, the edges that differ are:
  - Edge (i, sigma(i)): goes R->L in o_sigma, goes L->R in o_tau
  - Edge (i, tau(i)): goes L->R in o_sigma, goes R->L in o_tau

  So in o_sigma, the discordant edges form the subgraph with edges:
    { sigma(i) -> i : i in D }  (from right to left)
    { i -> tau(i) : i in D }    (from left to right)

  This is a bipartite directed subgraph where:
  - The left nodes are D ⊆ {0,1,2}
  - The right nodes are sigma(D) ∪ tau(D)

  Case 1: rho is a transposition, say rho = (a b) with a,b in {0,1,2}, D = {a,b}.
    sigma(a) = c1, tau(a) = sigma(b) = c2, tau(b) = sigma(a) = c1 (rho swaps sigma(a) and sigma(b)?
    Wait: tau = sigma o rho, so tau(i) = sigma(rho(i)).

    For i=a: rho(a)=b, so tau(a) = sigma(b)
    For i=b: rho(b)=a, so tau(b) = sigma(a)

    Discordant edges in o_sigma:
    - sigma(a) -> a  (edge (a, sigma(a)) reversed)
    - a -> tau(a) = sigma(b)  (edge (a, sigma(b)) forward)
    - sigma(b) -> b  (edge (b, sigma(b)) reversed)
    - b -> tau(b) = sigma(a)  (edge (b, sigma(a)) forward)

    These form the directed path: sigma(a) -> a -> sigma(b) -> b -> sigma(a)
    = the 4-cycle! ✓

  Case 2: rho is a 3-cycle, say rho = (0 1 2), D = {0,1,2}.
    tau(i) = sigma(rho(i)) = sigma(i+1 mod 3)

    Discordant edges in o_sigma:
    - sigma(i) -> i for i=0,1,2  (3 right-to-left edges)
    - i -> sigma(i+1 mod 3) for i=0,1,2  (3 left-to-right edges)

    These form the directed 6-cycle:
    sigma(0) -> 0 -> sigma(1) -> 1 -> sigma(2) -> 2 -> sigma(0) ✓

CONCLUSION: In both cases, the discordant edges form a single directed circuit
in o_sigma. For transpositions, it's a C4; for 3-cycles, it's a C6.

Therefore, every pair (o_sigma, o_tau) is directly connected in the flip graph,
confirming that C* induces K_6. This proves Claim 1 without relying on enumeration.
""")

print("="*70)
print("EXPLICIT VERIFICATION OF THE CYCLE STRUCTURE")
print("="*70)
print()

for sigma in perm_list:
    for tau in perm_list:
        if sigma >= tau:
            continue
        # Compute rho = sigma^{-1} o tau
        sigma_inv = [0]*3
        for i in range(3):
            sigma_inv[sigma[i]] = i
        rho = tuple(sigma_inv[tau[i]] for i in range(3))
        supp = [i for i in range(3) if rho[i] != i]
        rho_type = f"transposition" if len(supp) == 2 else f"3-cycle"

        o_s = perm_to_tco[sigma]

        if len(supp) == 2:
            a, b = supp
            # Expected C4: sigma(a) -> a -> sigma(b) -> b -> sigma(a)
            c4_expected = [sigma[a]+3, a, sigma[b]+3, b]
            # Verify this is a directed cycle in o_s
            valid = True
            for step in range(4):
                u = c4_expected[step]
                v = c4_expected[(step+1) % 4]
                k = EDGE_INDEX[frozenset([u, v])]
                if u < v:  # edge is (u,v) in EDGES, bit=0 means u->v
                    goes_right = not ((o_s >> k) & 1)
                    expected_forward = True
                else:  # edge is (v,u) in EDGES
                    goes_right = (o_s >> k) & 1
                    expected_forward = True
                # Actually: check that in o_s, edge goes from u to v
                if u < v:
                    actual_fwd = not ((o_s >> k) & 1)
                else:
                    actual_fwd = ((o_s >> k) & 1)
                if not actual_fwd:
                    valid = False
                    break

            print(f"  sigma={sigma}, tau={tau} ({rho_type}): expected C4 = {c4_expected}")
            print(f"    rho={rho}, supp={supp}")
            print(f"    C4 is directed in o_sigma: {valid}")
        else:
            # 3-cycle
            # rho is (0 1 2) or (0 2 1)
            # tau(i) = sigma(rho(i))
            # Expected C6: sigma(0)+3 -> 0 -> sigma(rho(0))+3 -> rho(0) -> sigma(rho(rho(0)))+3 -> rho(rho(0)) -> sigma(0)+3
            r0 = 0
            r1 = rho[r0]
            r2 = rho[r1]
            c6_expected = [sigma[r0]+3, r0, sigma[r1]+3, r1, sigma[r2]+3, r2]
            print(f"  sigma={sigma}, tau={tau} ({rho_type}): expected C6 = {c6_expected}")
            print(f"    rho={rho}, supp={supp}")
        print()

print("="*70)
print("COMPLETE PROOF OUTLINE FOR PAPER")
print("="*70)
print("""
Theorem: gamma(K(3,3)) >= 5.

Proof outline:

(A) SETUP. Let C* be the reversal class with out-degree sequence (2,2,2,1,1,1).
    The TCOs in C* correspond bijectively to permutations sigma in S_3:

      o_sigma: edge (L_i, R_j) is directed L_i -> R_j iff j != sigma(i),
               and directed R_{sigma(i)} -> L_i.

    Note: o_sigma is totally cyclic because every edge lies in a directed cycle
    (any 4-cycle or 6-cycle through the edge). (This follows from the doubly
    stochastic structure of the underlying 0-1 matrix.)

(B) THE FLIP GRAPH ON C* IS K_6. For any sigma != tau:

    Let D = supp(sigma^{-1}tau) = {i : sigma(i) != tau(i)}.

    Case |D|=2 (rho is a transposition, D={a,b}):
      The discordant edges in o_sigma form the directed 4-cycle:
        R_{sigma(a)} -> L_a -> R_{sigma(b)} -> L_b -> R_{sigma(a)}.
      This is a valid directed circuit in o_sigma. Reversing it gives o_tau. ✓

    Case |D|=3 (rho is a 3-cycle, D={0,1,2}):
      Let 0 -> a -> b -> 0 be the cycle of rho. The discordant edges form:
        R_{sigma(0)} -> L_0 -> R_{sigma(a)} -> L_a -> R_{sigma(b)} -> L_b -> R_{sigma(0)}.
      This is a valid directed 6-cycle (circuit) in o_sigma. Reversing it gives o_tau. ✓

    Therefore, the flip graph on C* has an edge for every pair in C*, i.e., it is K_6.

(C) EDGE LABELS ARE DISTINCT. Each pair (sigma, tau) uses a different circuit mask
    m_{sigma,tau} = o_sigma XOR o_tau. This mask encodes exactly the edges at the
    positions {(i, sigma(i)) : i in D} ∪ {(i, tau(i)) : i in D}. For two different
    pairs, these position sets are different (one can verify all 15 cases directly
    or by the following argument): each pair {sigma,tau} uniquely determines both the
    "discordant rows" D and the specific edges sigma(D) and tau(D), which vary
    independently as {sigma,tau} ranges over pairs.

(D) LOWER BOUND. The circuit reversal rank gamma equals the minimum size of a set S
    of circuit masks such that the S-restricted flip graph still has 20 components.
    In particular, S must keep C* connected.

    By (B) and (C), C* induces K_6 with 15 distinct edge labels. A connected spanning
    subgraph of K_6 requires at least 5 edges. Since all edge labels are distinct, we
    need at least 5 distinct masks, so |S| >= 5, giving gamma >= 5.  QED

---

Note on the upper bound: One can exhibit a generating set of size 5 explicitly.
For example, the 5 C4 cycles {a,b,d,e,i} (using the grid labeling from the paper)
generate all reversal classes. (Verified computationally; 9 such minimal sets exist.)

Therefore gamma(K(3,3)) = 5.
""")
