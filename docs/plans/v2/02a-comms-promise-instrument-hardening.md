# 02a — Comms: promise-instrument hardening · split off from packet 02 (operator, 2026-07-19)
size ~0.20 wu · wave C · depends: 02 (the promise-guard CORE ships there) · NOT smoke-critical
law: read `comms-subsystem.md` + spec v8 `docs/design/2026-07-12-pkt28-c1-semantics.md` §9.7
(the 19-line mechanism-promise sweep this packet fully mechanizes) + DESIGN-LAW §1 · DEPLOY: yes (both)

## Why this exists
Packet 02 measured ~3–4× its 0.20 estimate. The operator split off the promise instrument's
ADVANCED hardening so packet 02 could ship its render architecture + the completeness-guard CORE
(every comms render literal classified — registered-with-predicate OR declared promise-free;
default-FAIL AST scan; coverage a checked variable) without carrying the heavier mechanization.

## Scope IN (the deferred hardening — the CORE already shipped in packet 02)
- **Full §9.7 per-entry EXECUTABLE-predicate emission proofs** — beyond packet 02's behavioural
  A2/B pins: for EACH registered promise-line, a test that drives the render with the predicate
  TRUE (line MUST emit) and FALSE (line MUST NOT emit), mechanizing §9.7's 19-row table so a
  future author cannot register a promise whose predicate never actually gates its emission.
- **The `safe_str(f"…")` literal-text coverage closure** (`_SAFE_STR_LITERAL_RESIDUAL`, the
  documented residual from packet 02): close the AST scanner's coverage over promise/imperative
  text assembled via `safe_str(f"…")` (or concatenation) OUTSIDE a `render_line` template — the
  gap where a promise-literal can currently escape classification. Per the repo instrument-lesson:
  a gate is an invariant only over code it RUNS — enumerate every comms render literal site and
  assert each is observed, or the scan's reach is the next name-list.

## Scope IN — OPERATOR-RULED ADDITIONS (2026-07-19, recorded per the protocol's scope rule)
Both found by the cold audit / lead probes AFTER kickoff; the operator ruled them into this
packet rather than deferring (the packet's original scope line rested on an untested premise —
see the INDEX protocol's coverage-premise rule, which this packet's experience minted).
- **f-string `render_line` templates** — the CORE scanner required `ast.Constant`, so
  `render_line(f"…")` was invisible to BOTH scanners while rendering and serving normally.
  The original scope line ("OUTSIDE a `render_line` template") formally excluded it on the
  belief the CORE covered it; it did not, and `mypy` does NOT enforce `LiteralString`/PEP 675
  here. Ruled IN: close it, do not merely pin it.
- **Deny-by-default canonicaliser + marker cross-satisfaction meta-test** — shape-patching the
  f-string case left `%`-format, `.format()` and `str.join` promises still invisible (lead-probed,
  measured). Unknown AST shape must FAIL LOUD, never silently placeholder; and every proof marker
  must be proven non-satisfiable by its sibling branches MECHANICALLY, not by a human reading.
  Ruled IN so the defect CLASSES die here rather than recurring shape-by-shape.

## Scope OUT
- Any render/mechanism change (those all land in packet 02). This packet only HARDENS the
  instrument that guards them. (The additions above are INSTRUMENT changes, not render changes —
  the served surface is untouched; production stayed byte-identical throughout.)

## Entry check
Packet 02 deployed; the promise-guard CORE (`test_comms_promise_registry.py`) is live and the
render architecture (STANDING_BRIEF role + typed applicability + subscribed-name skew) is shipped.
Read §9.7 + the packet-02 promise-registry file first; a genuine spec gap is a STOP-and-flag.

## Exit
Full gates + cold audit (test-instrument surface) + deploy BOTH (if the guard changes any served
surface — likely test-only, confirm) + findings resolved; INDEX row + Log.
