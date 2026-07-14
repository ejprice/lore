# PKT-08b — Containerfile roles + image rework (split from PKT-08, 2026-07-14)
size ~0.20 wu · wave S · depends: PKT-07 (roles exist)
law: DESIGN-LAW §12 · DEPLOY: yes

## Mission
The containerfile half of the original PKT-08, deferred with the client/server wave:
role-aware images/entrypoints for the scout|mcp|all split. (The astroid-shadow half —
finding #24 — stayed in PKT-08, wave L, because dead-code truth couldn't wait.)

## Scope IN
- Containerfile rework: role-aware entrypoints (PKT-07's roles), image slimming as found,
  boot-time notes (lore-lore ~150s eager boot — document, don't "fix" silently).
- Whatever image implications PKT-08's #24 fix left as notes (it fixes the path order on
  the CURRENT image shape; this packet must not regress it — the #24 probe re-runs here).

## Scope OUT
- Split-topology drills (PKT-10b). Recreate-rebuild behavior is WONTFIX by design
  (memory: recreate-rebuild-is-intentional) — don't re-raise.

## Entry check
PKT-07 landed; capture `podman inspect <name> --format '{{.Config.CreateCommand}}'` for
BOTH containers before any rm (repo law).

## Exit
Full gates + cold audit; rebuild + recreate BOTH; smoke: each role image serves only its
own surface + the #24 probe still shows live prod refs in-container; INDEX row + Log.
