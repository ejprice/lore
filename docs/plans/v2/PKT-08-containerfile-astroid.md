# PKT-08 — Containerfile rework + the astroid shadow (finding #24)
size ~0.25 wu · wave D (parallel-safe) · depends: none
law: DESIGN-LAW §4 (graph invariants), §12 · DEPLOY: yes

## Mission
Rework the Containerfile for the role era and VERIFY-then-fix the installed-vs-mounted
astroid shadow gap on the v2 image (finding #24): in-container astroid can resolve
project imports to the pip-installed site-packages copy instead of /workspace, dropping
in-project refs → dead-code FALSE POSITIVES. Liveness verdicts depend on this.

## Scope IN
- Reproduce #24 on the current image (a known-referenced symbol reading 0 prod refs in
  container but not on host is the signature). Fix = make the source shadow the install
  on astroid's path. If it does NOT reproduce, close #24 with the receipt.
- Containerfile rework: role-aware entrypoints (PKT-07's roles), image slimming as
  found, boot-time notes (lore-lore ~150s eager boot — document, don't "fix" silently).
- Escalation valve (pre-agreed): if the shadow fix reproduces DEEPLY (needs packaging
  changes beyond path order), STOP and surface — it may need its own packet
  (decomposition-rationale flag, 2026-07-04:118-120).

## Scope OUT
- Split-topology compose/drills (PKT-10). Recreate-rebuild behavior is WONTFIX by
  design (memory: recreate-rebuild-is-intentional) — don't re-raise.

## Entry check
`lore_findings` → #24 open; capture `podman inspect <name> --format
'{{.Config.CreateCommand}}'` for BOTH containers before any rm (repo law).

## Exit
Full gates + cold audit; rebuild + recreate BOTH; smoke: in-container lore_impact on a
known-referenced symbol shows live prod refs (the #24 probe); #24 resolved either way
with receipts; INDEX row + Log.
