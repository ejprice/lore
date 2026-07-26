# 19 — Deploy architecture · DESIGN (#166 ⊃ #165; mints 19b+ builds) (formerly PKT-11's rework, REDESIGNATED 2026-07-22)
size ~0.15 wu (design only) · wave M · depends: none (the design; the minted BUILD packets inherit 14/15 where the scaffold needs them)
law: DESIGN-LAW §7 (Qdrant-pod law), §12 · roster law: **this is a DESIGN problem — an Opus
author who adversarially ATTACKS ITS OWN DESIGN, never a builder with "work out the general
form"; operator rules on the doc** · skill tests idiom: `cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests`

## REDESIGNATED (operator slotting, 2026-07-22)
**#166** landed: deploying lore requires TWO loremaster toolchains — the baked container
AND a host install, resolved through a path HARDCODED to the author's personal clone
(`lore_deploy.py:369-388`), because four load-bearing shell-outs (config-parse ×2, the
cold index, a snippet check — L442/L466/L736/L1137) run loremaster ON THE HOST while the
image already bakes everything needed (verified live: the skill itself is stdlib-only;
the image imports `loremaster.index.cli` + `loremaster.config` today). The clean shape —
run every loremaster operation IN the container, host needs only podman + the stdlib
script + the image — also **DISSOLVES #165** (the /source-vs-snapshot three-paths-must-
agree mount bug: indexer and server sharing one filesystem view removes the class).
That is an ARCHITECTURE decision plus a build well past this packet's old 0.30 → so 19
becomes the DESIGN pass and **mints 19b+ build packets, each ≤0.25 with its own
entry/exit** (the packet-25→26a+ pattern).

**#186 (2026-07-25, slotted 2026-07-26): #165 RECURRED** — lore-lore crash-looped on the
/source snapshot-mount mismatch AGAIN, now with THREE static tiers affected. Every new
static tier widens the blast radius until this design lands; the recurrence is the urgency
receipt, and #186 resolves with #165's dissolution (cite both in the build destination).

## Scope IN (the design doc answers each; operator rules)
- **The one-toolchain ruling (#166):** in-container execution for all four shell-outs
  (`podman run --rm <image> … -m loremaster.index --config …`, corpora `:ro`, snapshot
  `rw`); kill the hardcoded `~/PycharmProjects/lore/.venv` path (the #24/#140 provenance
  class); define what a PUBLIC user needs (podman + script + image, nothing else).
- **#165 dissolution stated as a design consequence** with the verification receipt the
  build must produce (a static-tier deploy where indexer and server read the same mounts).
- **Incremental-add verb** (#166 adjacent gap 1): add/refresh a static tier on an existing
  deployment — the 3.2.1 vendor tiers needed a manual `loremaster.index --tier` by hand.
- **Snapshot/boot-check keying** (#166 adjacent gap 2): for DB-served tiers, key the boot
  `_snapshot_materialized` skip on the STORE (file_text presence), not a disk snapshot —
  decide, or record why disk stays.
- **Partition the inherited rework scope into the minted builds**: finding #13 (status
  verb reads the legacy SQLite manifest), the scaffold fix (`_scaffold_lore_yaml` emits
  qdrant:/no surreal: — onboarding is broken today; verify b8e41a8's actual coverage),
  all-mode verbs (role arg defaulting `all`; packet 36 regains roles), git_sync pattern,
  Qdrant-verb drop (DESIGN-LAW §7). NOTE: **finding #13** here (status verb) is not
  **ledger #13** (packets 14/15's table).

## Scope OUT
- Building ANY of it (the minted 19b+ packets). The `migrate` verb machinery (packet 20
  builds it; the design leaves the seam).

## Entry check
**FIRST READ (repo store law): `docs/reference/surrealdb-31-capabilities.md`** (incl. §0 —
the engine is 3.2.1). Read finding **#166 in full** (it carries live verification receipts
for every mechanism claim — cite them, do not re-derive) and **#165**. `lore_findings` →
#166 #165 #186 #13 states; skill test suite green at HEAD before the design prescribes
changes to it.

## Exit
Design doc at docs/design/2026-07-XX-deploy-architecture.md; the author's adversarial
attack on its own design recorded in the doc; operator rulings recorded; **19b+ build
packet files minted (each ≤0.25 with entry/exit)** + INDEX table rows added; #166/#165
annotated with their build destinations; INDEX row + Log.
