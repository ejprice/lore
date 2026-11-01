# RULING: :18500 guard forks (lead-165 + operator, 2026-10-31)

Source: `REPORT-contract-165-guard.md` §Forks and §Chokepoint.

- **Chokepoint = the repo-root `conftest.py`** (operator, AskUserQuestion: "Repo root (Recommended)").
  - Every lore suite is guarded: loremaster, lorescribe, loresigil, lorerunes and skills.
  - Grounds: no member has its own `[tool.pytest]` table, so the root `pyproject.toml` is the rootdir and
    configfile for every suite, and the root conftest loads for all of them.
  - The contract's `_mirror_repo` symlinks the root `conftest.py`, so its pins hold at that chokepoint unchanged.
- **F1 (lead): if user namespaces are unavailable, SKIP with a named reason.** The contract must never run
  un-isolated. The guard itself still arms in-image; only the contract test skips.
- **F2 (lead): loopback only** (`127.0.0.0/8`, `::1`, `localhost`).
  - Measured: lore-surreal runs `Network=host` and `ss` shows the listener at `127.0.0.1:18500` only. So
    loopback is every route to production from this host.
  - Re-open trigger, written in the guard's docstring: production binds a non-loopback address.
- **Port literal:** 18500 has no named constant in production; it appears only inside `_scaffold_lore_yaml`'s
  template.
  - The guard owns ONE named constant.
  - Do not add a second scattered literal. Whether the scaffold should read the guard's constant is a
    dependency-direction question: production must not import a conftest. So the guard's constant cites the
    scaffold as its source of truth, and that pairing is ledgered as a residual, not a new shared module.
- **Subprocess / C-extension clients** (curl, `podman exec … surreal`) are invisible to a Python guard. KNOWN
  BOUND: the guard docstring names it.

## Addendum: builder decisions D1–D3 (lead, after REPORT-impl-165-guard.md)
- **KEEP D1, D2 and D3.** They are one ∀ property, and the operator rule ("fail any test attempting :18500")
  already covers it:
  > **every attempt fails the report of the node in whose phase it happened. That covers fixture setup and
  > teardown at EVERY scope (function, class, module, session) and module import (collection), and it holds
  > regardless of a later skip or xfail.**
- Grounds: the reference guard's `clear()`-at-function-setup DISCARDED attempts made in module- or
  session-scoped fixtures. That is a false clear of exactly the T8 shape (a shared fixture defaulting to the
  production URL).
- Rider: **pin it** (contract-165-guard-r2). The discrimination proof is that the reference guard
  (`/var/tmp/claude-1000/guard-ref/conftest.py`) goes RED on each new pin, while the build passes them all.
- typecheck.sh: the root `conftest.py` becomes a typecheck root (Phase 5 audit, with a red-leg proof).
