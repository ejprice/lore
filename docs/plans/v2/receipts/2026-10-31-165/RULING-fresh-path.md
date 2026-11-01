# RULING: fresh-path start parity (lead-165, 2026-10-31)

Sources: impl-165 F3, impl-165-a1 decision 1, prose-165-r2 D3. This is a lead-decided fork (low blast radius),
listed for the operator at close-out.

## Property (one rule for BOTH `start` paths)
**A `start` that refuses or fails touches nothing it did not have to, and always exits loudly.**

1. **Fresh path (no running container): a refusal leaves any existing EXITED `lore-<slug>` container in place.**
   - Today `verb_start` runs `podman rm -f` on an existing exited container BEFORE its preconditions: image, env
     file, snapshot, embed probe, store probe.
   - Required: that `rm` happens only after EVERY precondition has passed, immediately before the launch.
   - ∀ form: pin it over each precondition's failure (drive each one to fail), not just the snapshot.
2. **Fresh path: any failure `_launch_container` documents (`RuntimeError`, `CalledProcessError`) returns
   `_EXIT_ERROR`, with the error's own text on stderr, never a raw raise.** This is the same rule A1 set for the
   recreate path. Pin both types.

## Also in this round (behaviour-preserving refactors, unblocked by T8 `1b8887d`)
- **A4:** `_STATIC_ROOT_COUNT_EXPR` uses `loremaster.config.WATCH_STATIC`, not the `'static'` literal. Rewrite the
  stale comment that blames the substring stubs.
- **A2:** `_require_launchable_snapshot` makes ONE `_read_config_field` read, returning the static count and the
  failing tiers together.
No new pins for these. The existing contract, plus a mutation proof that the predicate is still shared, is the
check.
