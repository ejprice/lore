# REPORT-mem-migrator

brief-base v6 read

## SUMMARY BLOCK
- state: **done** — all 51 native-memory entries migrated into lore.
- counts: **written 51 / skipped 0 / failed 0.** Every entry WRITTEN+VERIFIED; none unaccounted.
- fidelity: **byte-exact on all 51.** `lore_remember` echoes the stored char-count; it equalled each
  source `body_chars` on every write (primary fidelity gate). To guarantee that, bodies were
  extracted to plain-text files with a roundtrip byte-assert (`scratchpad/extract.py`) before
  transcription — incl. the 18,715-char entry 32, which matched exactly.
- verify method: `lore_recall(labels=["origin=claude_native_memory","source_file=<file>"], k=1)` —
  a collision-proof filter returning exactly the migrated row. Entries 1–25 also passed unfiltered
  semantic recall (11/23/24/25 needed a sharper query first — a recall-ranking artifact, NOT a write
  defect; each write was already char-count-confirmed).
- dedup: 0 real duplicates. Per brief, biased hard to write; the pre-existing ~38 memories are the
  session-close/doctrine genre — related hits (multi-agent-comms doctrine, SurrealDB gotchas,
  P8d-closed, "attack the safe set") were confirmed to be DIFFERENT memories, never verbatim
  restatements of these distilled operator-lessons.
- kind/trust map applied: reference→fact/authoritative (41,46); feedback→decision/experiential (26 of them);
  project→fact/experiential (23). labels on every row: `origin=claude_native_memory`, `source_file=<file>`, `harness_type=<type>`.
- deviations: (1) scratch helper files written under the session scratchpad (`extract.py`, `bodies/*.txt`,
  `manifest.json`) — non-repo, in-scope. (2) NO edits to MEMORY.md / topic files / git (as instructed).
- FLAG (operator's call): entry 43 `spectron-verdict-partial-reuse` is SELF-DECLARED STALE by entry 45's
  body ("Spectron docs are now PUBLIC … the invite-gated memory is stale"). Migrated verbatim per no-loss;
  flagging so you know a superseded memory now lives in lore.
- receipt pointers: full id table below; extractor at
  `scratchpad/extract.py`; worklist `scratchpad/migrate_entries.json`.

## COMPLETE TABLE (51 rows)

| source_file | decision | verify | kind | trust |
|---|---|---|---|---|
| adversarial-test-doubles-lesson.md | written:8e2386a7-d1e5-5398-a7ef-5f9c20fcaa43 | OK | decision | experiential |
| agent-inbox-half-processing.md | written:6d815b67-2cfe-502b-bd76-2b1c17510cc6 | OK | decision | experiential |
| archive-dont-delete-and-chunk-headers.md | written:c0e3858b-0a56-5087-97a9-685ee0a3c947 | OK | fact | experiential |
| background-agents-permission-stalls.md | written:af587cfc-662e-51a6-a3a0-41ebf03dbd54 | OK | decision | experiential |
| brief-shape-determines-agent-stalls.md | written:52ccfd88-78d3-5350-9673-a48d3a159e8d | OK | decision | experiential |
| chunker-coverage-and-detection-plan.md | written:50be5e83-8543-5bac-88ec-72ca053b8756 | OK | fact | experiential |
| code-graph-astroid-kuzu-rearchitecture.md | written:d49f4e78-b5ef-528d-a766-c45c8901e41a | OK | fact | experiential |
| consults-yield-hypotheses-not-findings.md | written:a61b55b6-f16c-5034-840c-62c61a434e00 | OK | decision | experiential |
| contract-adversary-grades-the-tests.md | written:811cea1b-7677-5de8-9764-ee32f92b3116 | OK | decision | experiential |
| embedder-ab-voyage-large-beats-context.md | written:aa1ca471-94a4-57ec-8ce7-8830aeb9d45f | OK | fact | experiential |
| embedding-cost-is-negligible.md | written:60f96ff2-3bb7-5179-a3ef-a8ef5770e7ba | OK | fact | experiential |
| feedback-brief-before-asking-decisions.md | written:91e639b6-dffa-51e6-8ae1-8319054a2fba | OK | decision | experiential |
| feedback-checkpoint-cadence.md | written:2abd0aca-e035-5a2a-8a0c-1d1e281e5304 | OK | decision | experiential |
| feedback-commit-at-checkpoints.md | written:8055c041-d57b-5a93-88b3-6d072b7f4ea8 | OK | decision | experiential |
| feedback-deadreckoning-plus-scope.md | written:d545228b-99b5-5761-a7df-8d0ac84a3081 | OK | decision | experiential |
| feedback-delegate-before-inline.md | written:5ffc9b76-d787-5265-896b-51d604d59982 | OK | decision | experiential |
| feedback-directives-build-or-confirm-timing.md | written:6344c451-db27-5142-a38f-3285a1ad52bc | OK | decision | experiential |
| feedback-eat-the-dogfood.md | written:6937f31f-eaba-56a6-8320-1d0012158c5c | OK | decision | experiential |
| feedback-lore-first-choice.md | written:9e0027a4-a18f-5283-ab18-3bda3b6a7f1f | OK | decision | experiential |
| feedback-measure-dont-pilot.md | written:c8f26094-c0e2-58f8-b254-fe6d35b02327 | OK | decision | experiential |
| feedback-results-trump-costs.md | written:ed965945-4725-53b4-8c5b-a8808cbc7a5c | OK | decision | experiential |
| feedback-right-size-fable-vs-opus.md | written:a405fc89-55a3-5acf-a8b3-2cf022497a1f | OK | decision | experiential |
| feedback-sequencing-forks-are-operator-decisions.md | written:da110826-30fc-5e4a-9e1d-daf0f7db73b2 | OK | decision | experiential |
| fix-discovered-debt-on-sight.md | written:6b241f09-a0ef-56c5-8407-844b615ed90b | OK | decision | experiential |
| global-promotions-p8d-process-law.md | written:9e9f076c-1d36-5380-b01d-3d26571f8fff | OK | decision | experiential |
| idempotent-startup-v0.3.6.md | written:f5ebbcbb-ef78-5d19-aa15-166da2d52c1e | OK | fact | experiential |
| lore-container-runs-baked-image.md | written:63aad7bc-c24a-51ea-aab6-124cf17814c8 | OK | fact | experiential |
| lore-deploy-pre-existing-hostname-leak.md | written:9aca31aa-54b6-5a93-9792-eccca0d9a855 | OK | fact | experiential |
| lore-deploy-skill-home.md | written:cf7ca03c-4e82-5fb2-aa3c-3ebaa686b582 | OK | fact | experiential |
| lore-resolution-installed-vs-mounted.md | written:b96933a7-b498-5da2-97a0-aa82194f5784 | OK | fact | experiential |
| lore-two-container-topology.md | written:c78b7f10-7dfe-518e-bdc8-6deb659d6c6b | OK | fact | experiential |
| lore-v2-deadreckoning-plus-plan.md | written:cfb89a08-ad6c-59b3-b337-31a30e7b7446 | OK | fact | experiential |
| mandatory-gates-mypy-pylint-pydantic.md | written:6e5c12f1-36d6-5019-bc4f-6eb2f0f8b792 | OK | decision | experiential |
| no-autochunking-our-chunks-are-canonical.md | written:e9f0c237-d49b-5620-985e-e3ff2da69a56 | OK | fact | experiential |
| odoo-target-needs-xml-reference-extractor.md | written:8c9f2d90-efce-5c7a-b3f2-338b52b939de | OK | fact | experiential |
| orchestration-fork-and-path-hazards.md | written:0fbf7569-452e-546b-acb6-fa03301ef1cc | OK | decision | experiential |
| pr93-quantifier-and-frame-law.md | written:f932db46-192c-5d56-8867-6baab290f2ac | OK | decision | experiential |
| read-the-docs-then-verify-them.md | written:aa9175a4-281f-560b-8839-a09f2137237e | OK | decision | experiential |
| recreate-rebuild-is-intentional-not-a-bug.md | written:c2bb08b6-cf1b-5684-bc38-2f0081011183 | OK | fact | experiential |
| schema-rebuild-and-stale-image.md | written:3cf429f8-c3cd-576d-b2e0-d8b082ded2f9 | OK | fact | experiential |
| self-armed-watchers-deliver-midchain.md | written:d727cc4f-57b0-5855-9f31-fc27e2247fac | OK | fact | authoritative |
| sonnet-5-builder-grade.md | written:f666b6ce-9a79-5545-b637-f4cded4a777c | OK | decision | experiential |
| spectron-verdict-partial-reuse.md | written:5a321934-318f-5c6a-a571-d55945440be8 | OK | fact | experiential |
| surreal-31-docs-audit-adjustments.md | written:465d274c-ba0b-52e4-b365-e801c5fb0c76 | OK | fact | experiential |
| surreal-321-migration-and-docs-rag.md | written:591b5d26-0672-5e7b-a9cb-2adb9274644c | OK | fact | experiential |
| surreal-error-classifier-latent-edges.md | written:c5827948-f873-5d14-82bd-208b6a907d6e | OK | fact | authoritative |
| surreal-stores-systemd-managed.md | written:ef0042b3-4c3d-5fdb-9414-21b1a369b979 | OK | fact | experiential |
| tei-endpoint-prompts-and-asymmetry.md | written:c0032c9b-e016-5698-83cd-18c63e572006 | OK | fact | experiential |
| test-environment-is-a-fiction.md | written:8419dc7d-43c0-58ce-a42b-3785d96bf39d | OK | fact | experiential |
| test-references-not-true-references.md | written:9167a1ae-524d-5ca3-a12d-ceea3b36a992 | OK | decision | experiential |
| watcher-excludes-dirs-from-watch.md | written:1bd108af-dc3d-5d34-aa53-89aefe742778 | OK | fact | experiential |

## FAIL rows
None. All 51 WRITTEN + VERIFIED.

## Notes for the lead / operator
- **Byte-fidelity evidence**: for each write, `lore_remember` returned a note "this memory is N chars";
  N equalled the entry's `body_chars` (from the source JSON) on all 51 — the strongest available
  proof of a verbatim, un-paraphrased carry. This includes the 18,715-char plan (entry 32).
- **Verify semantics**: the `source_file` label filter guarantees the recall returns ONLY the migrated
  row, so an OK here means the exact stored text (verbatim) came back. Unfiltered semantic recall was
  additionally used on entries 1–25 and matched, with 4 needing a sharper query (they are outranked on
  shared vocabulary by high-importance session memories — retrieval ranking, not a fidelity problem).
- **Stale-memory flag (repeat for visibility)**: `spectron-verdict-partial-reuse.md` (row 43) is declared
  stale inside `surreal-321-migration-and-docs-rag.md` (row 45). Both migrated verbatim per no-loss.
  Operator may want to supersede/close row 43 in lore later.
