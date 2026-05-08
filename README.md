# K(3,3) Cycle Reversal Explorer

An interactive tool for exploring **totally cyclic orientations** of K(3,3) and the structure of cycle reversals — motivated by the question of which orientations are reachable from which others.

**[Live demo →](https://mikeion.github.io/graph-problems/)**

---

## The Setup

**K(3,3)** is the complete bipartite graph: 3 "left" vertices each connected to 3 "right" vertices, giving 9 edges total. It's famously non-planar — you can't draw it on a flat page without edges crossing — but it embeds cleanly on a **torus** (Pac-Man style, where opposite edges of a rectangle are identified).

Give each edge an arrow (a *direction*). An orientation is **totally cyclic** if every edge is part of at least one directed cycle — no edge is stranded outside of any loop.

Of the 2⁹ = 512 ways to orient K(3,3)'s edges, exactly **102 are totally cyclic**.

---

## The Game

**Move**: pick any directed cycle in your current orientation and reverse all of its arrows.

**Question**: starting from one totally cyclic orientation, which others can you reach?

---

## What We Found

The 102 TCOs split into exactly **20 equivalence classes** under cycle reversal. You can move freely within a class but can never cross into another.

### The Invariant

Reversing a directed cycle never changes any vertex's **out-degree** (the number of arrows pointing away from it). In a TCO of K(3,3), every vertex sends out either 1 or 2 arrows. With 6 vertices summing to 9 edges, exactly 3 vertices have out-degree 2 ("heavy") and 3 have out-degree 1.

The number of ways to assign which 3 vertices are heavy: **C(6,3) = 20** — exactly the number of equivalence classes.

### Structure of the Classes

| Heavy vertices | # classes | Class size |
|---|---|---|
| All 3 on the Left | 1 | 6 |
| 2 Left, 1 Right | 9 | 5 |
| 1 Left, 2 Right | 9 | 5 |
| All 3 on the Right | 1 | 6 |

Each class forms a **complete graph** (any two TCOs in the class are one reversal apart, diameter = 1).

### Torus Face Cycles

K(3,3) on the torus has 3 hexagonal faces. Restricting to only reversing these face cycles gives a much more constrained picture: **80 equivalence classes**, and **60 of 102 TCOs have no available face cycle move at all** (they are stuck).

---

## Using the App

- **Graph panel**: K(3,3) with directed arrows. The number below each node (→1 or →2) is its out-degree.
- **Directed cycles**: list of directed cycles in the current orientation. Click to highlight edges; click ↺ to reverse.
- **Equivalence class**: which of the 20 classes you're in, and all other TCOs in that class (click to navigate).
- **Class map**: all 20 classes as colored squares. Green = all heavy on Left, Blue = all heavy on Right, Purple = mixed.
- **Mode toggle**: switch between "All directed cycles" and "Torus face cycles only" to compare the two games.

---

## Running the Analysis

```bash
python k33_flip_graph.py
```

Outputs:
- Count of TCOs and flip graph structure
- Verification that out-degree sequence is a complete invariant
- Face-cycle-only flip graph structure and isolated node count
