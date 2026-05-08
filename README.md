# K(3,3) Circuit Generators

**The question (Alex McDonough):** For K(3,3), if you can only reverse specific circuits, how many do you need to reach anything reachable by arbitrary reversals?

**The answer:** 5 — one more than the cycle rank of K(3,3) predicts. For planar graphs the cycle rank always suffices; K(3,3) is the simplest case where it doesn't.

**[Live demo →](https://mikeion.github.io/graph-problems/)**

---

## Background

**K(3,3)** is the complete bipartite graph: 3 "left" vertices each connected to 3 "right" vertices, 9 edges total. It's non-planar but embeds cleanly on the torus.

An orientation of K(3,3) is **totally cyclic (TCO)** if every edge lies in at least one directed cycle — no edge is stranded outside any loop. Of the 2⁹ = 512 orientations, exactly **102 are totally cyclic**.

The **move**: pick any directed cycle and reverse all of its arrows. This produces another TCO.

---

## The Question

For any connected graph, the **cycle rank** E − V + 1 measures the dimension of the cycle space. For K(3,3): 9 − 6 + 1 = **4**.

For planar graphs, a cycle basis of E−V+1 circuits always suffices to generate all reachable moves — any circuit is a XOR-combination of basis circuits, so any flip decomposes into basis flips. Fewer than E−V+1 circuits leave some directions unreachable. So for planar graphs, the minimum generating set size equals the cycle rank.

Does the same bound hold for K(3,3)?

---

## What We Found

The 102 TCOs split into **20 equivalence classes** under cycle reversal, determined entirely by the out-degree sequence of each vertex (which vertices have out-degree 2 vs 1). No reversal can move between classes.

**The minimum generating set size is 5** — one more than the cycle rank. Using only 4 specific circuits, the 102 TCOs fragment into more than 20 groups regardless of which 4 you choose.

Additional findings:
- All 9 minimal generating sets use **only C₄ cycles** (4-cycles) — the hexagonal torus face cycles never appear in a minimal set
- There are exactly **9 minimal generating sets**

### The 9 Minimal Sets

Label the 9 four-cycles by which left pair and right pair of vertices they use:

```
         R₀R₁   R₀R₂   R₁R₂
L₀L₁  [  a  ] [  b  ] [  c  ]
L₀L₂  [  d  ] [  e  ] [  f  ]
L₁L₂  [  g  ] [  h  ] [  i  ]
```

The 9 minimal generating sets (each is 5 of the 9 four-cycles):

| Set | Circuits |
|-----|----------|
| 1 | a b d e i |
| 2 | c d e g h |
| 3 | a c d f h |
| 4 | b d f g i |
| 5 | b c d h i |
| 6 | a c e g i |
| 7 | a e f h i |
| 8 | b c e f g |
| 9 | a b f g h |

Every possible set of 4 circuits fails; these 9 sets of 5 are the only ones that work. Verified by checking all C(15, k) subsets for k = 1 to 5 in [`k33_flip_graph.py`](k33_flip_graph.py).

### Why the Classes Exist

Reversing a directed cycle never changes any vertex's out-degree. In a K(3,3) TCO, every vertex has out-degree 1 or 2, and exactly 3 are "heavy" (out-degree 2). The number of ways to choose which 3 of 6 vertices are heavy: C(6,3) = **20**.

| Heavy vertices | Classes | Size |
|---|---|---|
| All 3 on the Left | 1 | 6 |
| 2 Left, 1 Right | 9 | 5 |
| 1 Left, 2 Right | 9 | 5 |
| All 3 on the Right | 1 | 6 |

---

## Using the App

1. The graph shows K(3,3) drawn on the torus (3×2 checkerboard layout — the two crossing diagonals are valid edges on the torus, not graph crossings)
2. The metric starts at **102 groups** with no circuits selected
3. Click cycles in the grid to add them as allowed reversal moves — watch the groups merge
4. **Try 4 cycles** to see that the cycle rank isn't enough
5. **Minimal set (5)** shows one of the 9 minimal generating sets

Hovering over any cycle cell highlights its edges on the graph.

---

## Connection to Prior Work

The reversal operation studied here is an instance of what Gioan (2007) calls a **cycle reversing system** on the set of strongly connected orientations (which coincides with totally cyclic orientations for K(3,3)). Two key results from that paper apply directly:

- **Equivalence classes = indegree sequences** (Proposition 4.10): two orientations land in the same class if and only if they assign the same indegree to every vertex. This is why the 20 classes are permanent — no reversal can change a vertex's out-degree.
- **Class count = t(G; 0, 1)** (Corollary 4.11): the number of classes equals the Tutte polynomial evaluated at (0, 1). For K(3,3) this evaluates to 20, matching our count.

**What Gioan doesn't address** — and what this project answers — is the **minimum generator question**: given the full circuit set generates the correct partition, what is the smallest subset that also generates it? For planar graphs the cycle rank E−V+1 always works; the exhaustive search here shows K(3,3) requires one more.

---

## Open Questions

**Is bipartiteness the condition?** K(3,3) (non-planar, bipartite) exceeds cycle rank; K₅ (non-planar, not bipartite) meets it. The refined conjecture: minimum > cycle rank iff G is non-planar and bipartite — equivalently, iff G contains K(3,3) as a minor but not K₅. The next test cases are non-planar non-bipartite graphs like the Petersen graph.

**K₅ needs exactly the cycle rank.** K₅ has cycle rank 6, and exhaustive search (all C(37,6) = 2,324,784 subsets checked) finds exactly **5 minimal generating sets, each of size 6 = cycle rank**. The 5 sets have a clean structure: each consists of the 6 triangles (C₃ cycles) passing through a single vertex — one set per vertex of K₅. Since K₅ has 5 vertices, there are 5 such sets. The triangles through any vertex span the full cycle space (there are exactly cycle rank = 6 of them), so the cycle rank bound is tight.

**Refined conjecture:** Minimum > cycle rank iff G is **non-planar and bipartite**. K(3,3) is bipartite (girth 4, no triangles) — no triangle-based cycle basis exists, so the bound fails. K₅ is non-planar but not bipartite — triangles through any vertex give a natural basis, so the bound holds. Planar graphs always satisfy the bound regardless of bipartiteness.

**Why only C₄ cycles in minimal sets?** The 9 minimal generating sets use only 4-cycles — the hexagonal torus face cycles never appear. The exhaustive search confirms this but doesn't explain it. There's likely a structural reason tied to the bipartite geometry or the torus embedding.

**What is the right general invariant?** The minimum generator count is computable but not obviously a matroid invariant. Is there a closed-form characterization, or does it require case-by-case computation for each graph?

---

## References

- E. Gioan, "Enumerating degree sequences in digraphs and a cycle–cocycle reversing system," *European Journal of Combinatorics* 28 (2007), 1351–1366.
- P. D. Seymour, "Decomposition of regular matroids," *Journal of Combinatorial Theory, Series B* 28 (1980), 305–359.
- W. T. Tutte, "A contribution to the theory of chromatic polynomials," *Canadian Journal of Mathematics* 6 (1954), 80–91.

---

## Running the Analysis

```bash
python k33_flip_graph.py
```

Outputs the flip graph structure, out-degree invariant verification, and face-cycle-only analysis. An **[annotated walkthrough of the full output](https://mikeion.github.io/graph-problems/proof.html)** is available without running the code.
