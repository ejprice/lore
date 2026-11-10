# ruff: noqa: E501 - the pasted fence body is kept verbatim
# Committed copy of packet 58 amendment 17 §INSTRUMENT-3 (docs/design/2026-11-09-packet58-amendment-17.md), by
# contract-58-r53 (lead #20087, am-17 §13.5 item 4). Changes vs the fence, and nothing else: type annotations (the
# gate types `scripts/`), and the cold-audit seam — every rule-U call goes through `RULE_U`; `--built` points it at
# `rule_u_built`, whose body the cold audit replaces with a call to the built predicate.
"""am-17 §13: candidate skip rules for the boot heal, brute-forced in memory (no store).

World: random small `blocked_by` graphs with a random acyclic `superseded_by` map. A straggler is a
row naming a superseded id; its proposed column replaces each superseded id by its chain head.

Rules (which pending rows are SKIPPED):
  U    one pass: skip row r iff some proposed blocker b of r shares r's strongly connected component
       in (stored columns UNION every pending row's proposed column).
  OV1  one pass: skip r iff r is in a non-trivial SCC of the overlay (every pending row applied).
  OVF  OV1 repeated to a fixpoint (skipped rows return to their stored column).

Property G (what "the heal never puts a row it wrote on a cycle" needs once chunks can fail alone):
for EVERY subset A of the kept rows applied (the rest left as stored), no row in A lies on a cycle.
`full` counts violations with A = all kept rows; `partial` with any proper subset.

Control: rule NONE (skip nothing) must show violations, or the checker sees nothing.

Part S: live supersede. exact = "the successor lies on a cycle of the overlay"; union = rule U asked
of the successor only. Counts worlds where they differ.

Run: uv run python <this file> [worlds] [seed]
"""
import itertools
import random
import sys
from collections.abc import Callable
from typing import Any

import networkx

#: ``{task: its blocked_by}``.
Columns = dict[str, list[str]]
#: A skip rule: ``(stored, proposed) -> the pending rows it skips``.
Rule = Callable[[Columns, Columns], set[str]]


def digraph(columns: Columns) -> Any:
    g = networkx.DiGraph()
    for node, blockers in columns.items():
        g.add_node(node)
        for b in blockers:
            g.add_edge(node, b)
    return g


def on_cycle(g: Any, node: str) -> bool:
    if g.has_edge(node, node):
        return True
    return any(node in comp and len(comp) > 1 for comp in networkx.strongly_connected_components(g))


def component_of(g: Any) -> dict[str, int]:
    out = {}
    for index, comp in enumerate(networkx.strongly_connected_components(g)):
        for node in comp:
            out[node] = index
    return out


def world(rng: random.Random, n: int) -> Any:
    ids = [f"t{i}" for i in range(n)]
    order = ids[:]
    rng.shuffle(order)
    successor = {}
    for i, old in enumerate(order[:-1]):          # successor always later in `order` => acyclic chains
        if rng.random() < 0.35:
            successor[old] = rng.choice(order[i + 1:])
    stored = {t: [b for b in ids if b != t and rng.random() < 0.28] for t in ids}

    def head(t: str) -> str:
        while t in successor:
            t = successor[t]
        return t

    proposed = {}
    for t, col in stored.items():
        if any(b in successor for b in col):
            proposed[t] = list(dict.fromkeys(head(b) if b in successor else b for b in col))
    return stored, proposed


def rule_none(stored: Columns, proposed: Columns) -> set[str]:
    return set()


def rule_u(stored: Columns, proposed: Columns) -> set[str]:
    union = digraph(stored)
    for r, col in proposed.items():
        for b in col:
            union.add_edge(r, b)
    comp = component_of(union)
    return {r for r, col in proposed.items() if any(b == r or comp[b] == comp[r] for b in col)}


def rule_u_built(stored: Columns, proposed: Columns) -> set[str]:
    """⚠ COLD-AUDIT SEAM (am-17 §13.5 item 4): replace this body with a call to the BUILT persisted-row cycle
    predicate (am-17 §13.2: ``all_or_nothing=False``, every proposed row asked) returning the hit rows as a set,
    then run with ``--built``: rule ``U`` must read 0 / 0 and ``NONE`` non-zero. Until then it refuses to run."""
    raise NotImplementedError(
        "cold audit: call the built predicate here (stored, proposed, asked=set(proposed), all_or_nothing=False) "
        "and return set(result)"
    )


#: Which implementation rule ``U`` runs: the in-memory reference (``rule_u``, default) or the built function
#: (``rule_u_built``, selected by ``--built``). Every rule-U call in parts heal and supersede goes through this.
RULE_U: Rule = rule_u


def rule_ov1(stored: Columns, proposed: Columns) -> set[str]:
    g = digraph({**stored, **proposed})
    return {r for r in proposed if on_cycle(g, r)}


def rule_ovf(stored: Columns, proposed: Columns) -> set[str]:
    pending, skipped = dict(proposed), set[str]()
    while True:
        g = digraph({**stored, **pending})
        hit = {r for r in pending if on_cycle(g, r)}
        if not hit:
            return skipped
        skipped |= hit
        for r in hit:
            del pending[r]


def violations(stored: Columns, proposed: Columns, skipped: set[str]) -> Any:
    kept = [r for r in proposed if r not in skipped]
    full = partial = 0
    for size in range(1, len(kept) + 1):
        for applied in itertools.combinations(kept, size):
            g = digraph({**stored, **{r: proposed[r] for r in applied}})
            if any(on_cycle(g, r) for r in applied):
                if size == len(kept):
                    full += 1
                else:
                    partial += 1
    return full, partial


def boots_until_stable(stored: Columns, proposed: Columns, rule: Rule) -> Any:
    """Re-run the heal (rule + apply all kept) until nothing changes; return rows still skipped."""
    stored, proposed = dict(stored), dict(proposed)
    while True:
        skipped = rule(stored, proposed)
        kept = [r for r in proposed if r not in skipped]
        if not kept:
            return stored, skipped
        for r in kept:
            stored[r] = proposed.pop(r)


def part_heal(rng: random.Random, worlds: int) -> None:
    rules = {"NONE": rule_none, "U": RULE_U, "OV1": rule_ov1, "OVF": rule_ovf}
    bad = {name: [0, 0] for name in rules}
    with_pending = extra_u = extra_u_after_boots = stuck_checked = stuck_ok = 0
    for _ in range(worlds):
        stored, proposed = world(rng, rng.randint(4, 7))
        if not proposed:
            continue
        with_pending += 1
        for name, rule in rules.items():
            full, partial = violations(stored, proposed, rule(stored, proposed))
            bad[name][0] += bool(full)
            bad[name][1] += bool(partial)
        over = RULE_U(stored, proposed) - rule_ovf(stored, proposed)
        extra_u += bool(over)
        final, still = boots_until_stable(stored, proposed, RULE_U)
        left = over & still
        extra_u_after_boots += bool(left)
        g = digraph(final)
        for r in left:      # claim: a row U never heals is unclaimable anyway under its proposed column
            stuck_checked += 1
            reach = set().union(*(networkx.descendants(g, b) | {b} for b in proposed[r]))
            stuck_ok += bool(reach & still)
    print(f"heal worlds with stragglers: {with_pending}")
    for name, (full, partial) in bad.items():
        print(f"  rule {name:4s} worlds violating G: all-applied={full} partial={partial}")
    print(f"  worlds where U skips a row OVF heals: {extra_u}; still so after repeated boots: {extra_u_after_boots}")
    print(f"  of those rows, proposed blockers reach a permanently skipped row: {stuck_ok}/{stuck_checked}")


def part_supersede(rng: random.Random, worlds: int) -> None:
    differ = refused = tried = 0
    for _ in range(worlds):
        n = rng.randint(4, 7)
        ids = [f"t{i}" for i in range(n)]
        stored = {t: [b for b in ids if b != t and rng.random() < 0.3] for t in ids}
        old = rng.choice(ids)
        deps = [b for b in ids if b != old and rng.random() < 0.3]
        rewired = {t: ["new" if b == old else b for b in col] for t, col in stored.items() if old in col}
        tried += 1
        exact = on_cycle(digraph({**stored, **rewired, "new": deps}), "new")
        asked_u = "new" in RULE_U(stored, {**rewired, "new": deps}) if deps else False
        # rule U asked of the successor only: recompute directly
        union = digraph(stored)
        for r, col in {**rewired, "new": deps}.items():
            for b in col:
                union.add_edge(r, b)
        comp = component_of(union)
        union_says = any(comp[b] == comp["new"] for b in deps)
        assert union_says == asked_u
        refused += exact
        differ += exact != union_says
    print(f"supersede worlds: {tried}; exact refuses {refused}; union differs from exact in {differ}")


if __name__ == "__main__":
    if "--built" in sys.argv:
        sys.argv.remove("--built")
        RULE_U = rule_u_built
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 4000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 58
    part_heal(random.Random(seed), count)
    part_supersede(random.Random(seed + 1), count)
