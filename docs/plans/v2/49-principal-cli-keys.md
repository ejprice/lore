# 49 — Principal management CLI (1B) + per-user API keys (1C) (wave-D mint, 2026-08-02)
size ~0.25 wu · wave D · depends: 48 · DEPLOY: yes (the CLI must be in the image; 54 re-verifies)
spec: docs/design/2026-08-01-multi-user-lore-proposal.md §Part 1B + §Part 1C (this file only points)

## Mission
Mint and manage principals + their API keys from inside the image via the
`lore-adm` console script (operator-ruled 2026-08-20 — a `[project.scripts]`
entry point `lore-adm = "loremaster.principals:main"`, NOT the unwieldy
`python -m loremaster.principals`): `podman exec lore-<slug> lore-adm …`.

## Scope IN (headlines; the spec carries the mechanics)
- CLI per the house idiom and the `snapshot_gc.py` template (argparse, env-var NAMES not
  values); verbs add/list/delete/suspend/unsuspend/set-expiry + mint-key/list-keys/
  revoke-key; `__main__`-guard-last law.
  ⚠ **OPERATOR RULING 2026-08-20 — NO dry-run / `--execute` paradigm** (verbatim: *"Gate
  none. I hate that paradigm."*). This OVERRIDES the former "strict dry-run unless
  `--execute` for delete/suspend" scope line **and** spec §1B's "only list is safe by
  default": every verb executes its effect directly when run (loud-on-failure,
  silent-on-success, Unix idiom); only `list`/`list-keys` are reads; there is no
  `--execute` flag. The CLI keeps `snapshot_gc.py`'s argparse/async/env-var-NAMES/
  loud-on-failure idiom but NOT its dry-run gating.
- Key wire format `<name>:<secret>` (odoo-code's split-on-first-colon shape) — **operator-
  confirmed 2026-08-20**.
- Keys: **adopt odoo-code's VALIDATION shape, REJECT its identity mint** (constant
  client_id collapses every keyholder — spec §1C receipts). Mint per packet 39 §4:
  `client_id=f"api_key:{name}"`, `subject=name`.
- Storage: hashed keys only (`principal_key` table: hash, label, created_at, expires_at,
  revoked_at); the CLI shows the key ONCE at mint.
- **Revocation beats the cache** — re-check on every verification, no residual TTL window
  (packet 39 R12's ruled property, applied here).

## Scope OUT
- The wire-level auth middleware (packet 39 wires verification into serving).
- Scoped memory (struck).

## Entry check
48 landed (`principal` table + `build_store`). Spec §1B/§1C read in full.

## Exit
Full gates + adversary + cold audit. Pins: revoked key denied on the NEXT verification;
key never stored raw (constructed leak probe with positive control); each verb executes
its effect directly (no dry-run/`--execute` paradigm — operator ruling 2026-08-20);
mint-key shows the key ONCE. Design doc: `docs/design/2026-08-20-packet49-cli-keys.md`.
