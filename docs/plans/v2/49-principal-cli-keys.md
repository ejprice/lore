# 49 — Principal management CLI (1B) + per-user API keys (1C) (wave-D mint, 2026-08-02)
size ~0.25 wu · wave D · depends: 48 · DEPLOY: yes (the CLI must be in the image; 54 re-verifies)
spec: docs/design/2026-08-01-multi-user-lore-proposal.md §Part 1B + §Part 1C (this file only points)

## Mission
Mint and manage principals + their API keys from inside the image
(`podman exec lore-<slug> python -m loremaster.principals …`).

## Scope IN (headlines; the spec carries the mechanics)
- CLI per the house idiom and the `snapshot_gc.py` template (argparse, env-var NAMES not
  values, **strict dry-run unless `--execute`** for delete/suspend); verbs add/list/
  delete/suspend/unsuspend/--expires; `__main__`-guard-last law.
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
key never stored raw (constructed leak probe with positive control); CLI dry-run mutates
nothing (state-unchanged probe + a `--execute` control that DOES mutate).
