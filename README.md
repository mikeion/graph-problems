# K(3,3) Circuit Generators

An interactive tool for exploring a question about totally cyclic orientations of K(3,3):
**if you can only reverse specific circuits, how many do you need?**

**[Live demo →](https://mikeion.github.io/graph-problems/)**

---

## Background

**K(3,3)** is the complete bipartite graph: 3 "left" vertices each connected to 3 "right" vertices, 9 edges total. It's non-planar but embeds cleanly on the torus.

An orientation of K(3,3) is **totally cyclic (TCO)** if every edge lies in at least one directed cycle — no edge is stranded outside any loop. Of the 2⁹ = 512 orientations, exactly **102 are totally cyclic**.

The **move**: pick any directed cycle and reverse all of its arrows. This produces another TCO.

---

## The Question

For planar graphs, the minimum number of specific circuits that generate all reachable moves equals the **cycle rank** (E − V + 1). For K(3,3) that would be 9 − 6 + 1 = **4**.

Does K(3,3) also need just 4? Or more?

---

## What We Found

The 102 TCOs split into **20 equivalence classes** under cycle reversal, determined entirely by the out-degree sequence of each vertex (which vertices have out-degree 2 vs 1). No reversal can move between classes.

**The minimum generating set size is 5** — one more than the cycle rank. Using only 4 specific circuits, the 102 TCOs fragment into more than 20 groups regardless of which 4 you choose.

Additional findings:
- All 9 minimal generating sets use **only C₄ cycles** (4-cycles) — the hexagonal torus face cycles never appear in a minimal set
- There are exactly **9 minimal generating sets**, one for each column of the C₄ grid (indexed by which pair of right vertices the cycle uses)

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

## Running the Analysis

```bash
python k33_flip_graph.py
```

Outputs the flip graph structure, out-degree invariant verification, and face-cycle-only analysis.
