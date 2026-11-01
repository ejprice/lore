# RULING F1: pin 4's exception type and placement (lead-165, 2026-10-31)

Fork: REPORT-contract-165.md §FORK F1 (contract-165). Ruled: **option (c), both levels**, plus two riders.

## Ruling
1. **(c)(i)** `_launch_container` refuses with `RuntimeError` when static roots are configured and the host
   `SNAPSHOT_ROOT` is absent. This is the type `_read_config_field` already raises from the same function. The
   message names the missing host path and the cold-index remedy (`python -m loremaster.index --config …`).
   `_run` is never called.
2. **(c)(ii)** `verb_start` checks the same precondition in its PRE-TEARDOWN precondition block, on BOTH paths:
   - fresh launch: no `podman run`;
   - stale-image recreate: no `podman stop`, no `podman rm`, no launch.

   Both paths return `_EXIT_ERROR` with the teaching message on stderr, matching the B1/B2 shape.

## Riders (part of the ruling: build them and pin them)
- **R1, one predicate.** (c)(i) and (c)(ii) call ONE function that decides "static roots configured and host
  snapshot absent". Neither site may clone the condition.
  Pin it with behaviour: drive both levels from the same fixture. The contract states the chokepoint by role
  ("the shared launch-precondition check"); the implementer names it.
- **R2, the config-read sibling.** A `_read_config_field` failure (malformed `lore.yaml`) on the recreate path
  must also abort BEFORE teardown: no stop, no rm, `_EXIT_ERROR`, and the error text on stderr. The (c)(ii)
  pre-teardown block reads the static-root count anyway, so this is the same chokepoint. Pin it ONCE, on the
  recreate path.

## Why it is in scope
The operator granted pin 4 ("refuse to launch when the host snapshot is missing"). A refusal that fires after
teardown turns a refused launch into an outage, which defeats pin 4's own purpose and violates the outage guard
B1/B2 already pin. So placing the check before teardown is how pin 4 is built correctly, not new scope. R2 is
a known defect inside the same chokepoint (global rule: known defects in granted scope are fixed in the session
that finds them).
