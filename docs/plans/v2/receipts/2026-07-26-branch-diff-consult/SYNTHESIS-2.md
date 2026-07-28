# Branch/diff consult, second wave (rounds 2–5) — hosted multi-user, fleets, feeds, races

Date: 2026-07-26 (same day as `SYNTHESIS.md`; this file consolidates everything after it).
Method unchanged: three independent positions per round — the lead (Fable) committed each
position to a file BEFORE reading either consultant's reply (`POSITION-fable-lead-2-multibranch.md`,
`POSITION-fable-lead-3-hosted.md` §§7–9); consultants answered blind to the lead and to each
other (`FOLLOWUP-consultant-opus-1.md`, `FOLLOWUP-consultant-sonnet-1.md`, verbatim).

## The four operator escalations, and what each did

1. **"What about main/staging/dev? And: main checked out, new feature branch"** (round 2/3
   pre-hosted) → branch-in-place found to be ALREADY SERVED by existing machinery
   (branch-tagged snapshots + `lore_diff`; render/teaching gap only); standing multi-branch
   visibility held at "not now."
2. **"Cloud-hosted, multi-user: A on feature/nose-cheese, B on staging, C on fix/butt-widget"**
   → exposed the silently-WRONG-TREE serving class in the planned split topology; REVERSED
   the multi-branch "not now" (per-render tree identity is mandatory once two users exist —
   the ambiguity objection becomes mandatory infrastructure); minted the view abstraction.
3. **"Three agents in worktrees on components of my branch"** → packet 17's home case,
   sharpened: agent-granular sessions, fleet-scale concurrency, the same-file three-sibling
   discriminating fixture, stacked identity (parent pointer) with depth-1 serving.
4. **"Untrue with file watchers — a write is not a commit; ./worktrees/ gets watched too"**
   then **"two watchers, same branch, different machines"** → falsified the pushed-only
   bound all three participants had stated as absolute; minted feed-typed honesty + the
   positive-heartbeat requirement + the ingestion-routing leg; then dissolved the two-scout
   race by identity (feed-INSTANCE in the key, single-writer-per-view).

## The consolidated rider package — OPERATOR ADOPTED IN FULL, 2026-07-26

Recorded as the second ruled block in `docs/plans/v2/17-worktree-overlay-design.md`; the
authoritative wording lives THERE — this file is the receipt trail, not the law.

Summary of what was adopted: view identity `(parent, ref|path, feed-instance)` with
single-writer-per-view (a branch NAME is never a view key; lore never merges two machines'
trees — push/pull is git's reconciliation channel); declared agent-granular sessions with
no default view and no default disambiguation; feed-typed honesty renders (ref-fed: sha +
fetch age + unpushed-absent; scout-fed: last-ingest age + POSITIVE-heartbeat liveness, no
unpushed-absent line); both isolation legs with named discriminating fixtures (serving:
same file modified/modified-differently/deleted across three siblings → one path, four
view-dependent answers; ingestion: same relative path edited in base and worktree
simultaneously → each lands only in its owning view, with positive control);
ephemeral-vs-standing lifetimes (+ scout-disconnected reap trigger); merge-base re-derived
under a continuously advancing base; concurrency pins ≥8-way; stacked-vs-flattened
SERVING = measure-then-tune at wave O; the packet-39 seam list NAMED in 17 and designed in
39 (per-scout identity, view-scoped write grants, base read-only to user scouts, content
trust, poisoning/quota, revocation); embedding locality + wire format stay 36/38.

## Second ruling — Scenario A re-dispositioned

Standing multi-ref visibility: **ruled-in for the hosted DESIGN, build deferred** to the
hosted packets (supersedes the morning "never in this design + re-open trigger" — the
trigger turned out to be the already-planned hosted deployment). What STANDS of the
morning ruling: no ref-vs-ref compare VERB, no git-ref mode on `lore_diff` (#232).

## The meta-finding (worth more than any single rider)

Opus, after its third collapsed absolute in one consult: *"every absolute I offered was an
absolute about the topology I happened to be picturing."* Sonnet and the lead each shipped
the same class of error once (the pushed-only bound). The askable form, for any design
review: **"which topology am I picturing, and is this claim true of the others?"** The
identity tuple is the structural fix — it converts each silent topology premise (whose
parent? which source? which writer?) into an explicit, rendered component.

## Residual flags (surfaced, not resolved — for the packets that own them)

- Sonnet R2b: whether packet 01's watched-path/branch render generalises to the hosted
  deployment — unverified; packet 38's e2e should check it.
- Sonnet R5: MASTER-PLAN's singular "a git-synced repo" is an unverified assumption if
  multi-region git-sync ever exists.
- Sonnet R2 option (ii): auto-stamp-snapshot-on-branch-change — a new mechanism, flagged
  and NOT recommended; revisit only if the render-level teaching proves insufficient.
- Opus R4: refuse-vs-empty on scout-fed views works ONLY if the heartbeat exists — the
  design dependency that forces the heartbeat into packet 17 rather than a later bolt-on.
