# REPORT — coldaudit-63b-ii-b (COLD AUDIT, packet 63b wave ii-b)

brief-base v14 read
brief project v7 read

## Summary block (brief-base §1)

- **VERDICT: GO.** I tried to break every load-bearing property (read the correct build seam-by-seam, mutation-proved the dirty-store pins BOTH ways in a provenance-asserted scratch, sampled the DUAL for neutering, traced the secret literal) and could not. No CONFIRMED defect; residuals are all previously-surfaced accepted bounds + two LOW notes (§R).
- **state:** done-with-deviations (deviation: text-search binaries hook-blocked in this checkout — every textual sweep is `awk index()` over an explicit file list or lore MCP; SAID OUT LOUD per occurrence. Second deviation: the idle-gate hook emitted one false nudge — it derived `REPORT-coldaudit-63b-iib.md` from my comms-registration spelling, but the brief-mandated report name is `REPORT-coldaudit-63b-ii-b.md` (present); the brief uses two name spellings. Wrote a defensive contract at the hook-expected path.).
- **Graded:** `5d61f9e` · HEAD-at-report: `5d61f9e` · SAME.
- **Packages considered:** none — this is an audit; no mechanism specified/built.
- **Reuse ledger:** none — 0 new symbols (audit only; all probes are scratch mutations, discarded).
- **Gates (re-run ALONE, bounded `-n 12`, sequentially — #466):**
  - full suite `uv run pytest -n 12 -q` → **11242 passed, 62 skipped, 3 xfailed, 0 failed** (exit 0, 499.53s, ALONE)
  - `pending_contract_gate.py --currency -- -n 12` → **PASS — every claimed gate is GREEN or OWNED; 0 RED_ORPHANED** (manifest = typecheck/ruff/pytest, all GREEN; exit 0)
  - `typecheck.sh` → **GREEN** (0 mypy incl. tests) · `ruff check .` → **All checks passed!**
- **decisions-needed:** none blocking. Residuals in §R (all previously-surfaced accepted bounds + one LOW invisible-remainder re-ask note + one minor F-DUP reach note).

---

## §0 What I did to try to break it (this is not a bare GO)

I re-read the shipped correct build for every load-bearing property the two adversaries
DEFERRED to me ("read-governance correct-build satisfiability … cold audit is the
satisfiability backstop", adversary2 §What-I-re-graded), traced each read seam to the ONE
shared splice, confirmed the ASSERT drops in the shipped schema, confirmed the MP-7 corpse
is deleted, sampled the DUAL translations for neutering, and re-confirmed the F-DUP + secret
allowlist. Where a claim needed execution (dirty-store pin discrimination), I mutation-proved
it in a provenance-asserted scratch copy (§P3).

---

## §Properties — refutation receipts

### P#3 — the ASSERT drops + #107 OVERWRITE mechanism — HELD (code read; mutation proof §P3-M)
`surreal_schema.py` at `5d61f9e`:
- `_MESSAGE_FIELD_SPECS` (`loremaster/loremaster/store/surreal_schema.py:769`): `grade` KEEPS
  `ASSERT $value IN [{_MESSAGE_GRADE_ALLOWED}]` (R19, §13); `body`/`thread`/`task_id` → `""`,
  `refs` → `"DEFAULT []"`, `refs[*]` → `""` (row KEPT because `array<T>` implicitly re-defines
  `refs.*` and only an emitted OVERWRITE with no clause DROPS the stored ASSERT — §12).
- `_TO_FIELD_SPECS` (`:823`): `ack_note` → `option<string>` `""` (ASSERT dropped, §3).
- The module docstring (`:17`) + `_define_field` emit `DEFINE FIELD OVERWRITE` (full-replace
  drops the stored ASSERT; NOT `IF NOT EXISTS` #107-noop, NOT `ALTER`). Comments rewritten to
  the §3.4/§13.1 invariants (D5, D-M9/D-M10) — no stale prose teaching the corpse.
- Grade KEPT is CORRECT per R19 (§13.1): grade's violation set ≡ the reader's decode
  rejection set (`InboxEntry.grade: MessageGrade` Literal), so the guard is reader-ALIGNED, a
  positive control at the write, not a loaded gun at the UPDATE.

### P#2 — read governance (the wave's core) — HELD (correct build genuinely correct)
The satisfiability the adversaries deferred to me. All FOUR read seams splice the ONE shared
filter `governed.read_filter(subject, MESSAGE_TABLE)` (`loremaster/loremaster/governed.py:242`
== `pdp.authorize_filter(subject, READ, table).to_surql()` — a thin wrapper, NOT a hand-rolled
copy → ROUTING IS sharing here):
- `MessageLedger.drain` (`messages.py:1078`): `window = await self._filter_visible_rows(window, subject)`
  BEFORE the decode and BEFORE the stamp; `entries = [_row_to_inbox_entry(row) for row in window]`
  built BEFORE the `UPDATE … WHERE … in IN $message_ids AND seen_at IS NONE RETURN AFTER`
  (message_ids derived from the FILTERED window). ⇒ an invisible message is neither served NOR
  stamped (§4.3); decode-first (F-1 §13.2) — decode failure raises with nothing stamped. The
  `since=` recovery path filters too.
- `_filter_visible_rows` (`messages.py:1281`) + `_resolve_message_ids` (`messages.py:1437`,
  ack's seq→message resolution) + `messages_for_task` (`messages.py:1679`, story) +
  `message_activity_since` (`messages.py:1718`, rollup) ALL splice the SAME `governed.read_filter`.
- `ack` (`messages.py:1319`): resolves seqs THROUGH the read filter, so an addressed-but-INVISIBLE
  seq does not resolve → `unknown_message` (never `already_acked(acked_at=None)`), CAS never reaches
  its edge, nothing stamped (§9.5 α). ✓
- `subject=None` is the legacy/internal unfiltered path (governance is the tool layer's, §4.D) —
  consistent across all seams.

### P#7 render_subject_bound placement (P4) — HELD (all 5 carriers)
`render_subject_bound` (`server.py:4216`) renders a scope FACT
(`scope: principal … · agent … · visible via N keep(s)`) via the `render_attributed` containment
seam; **no withheld count** (bound is a fact, not a disclaimer). Placed as the FIRST line, once
per response, in `_render_comms_drain` (`:8537`, incl. empty case), `_render_comms_await` (`:8761`),
`_render_comms_await_empty` (`:8814`, the empty path where Leg 1 matters most, names TIME bound),
`_render_comms_ack` (`:8922`), `_render_comms_story` (`:7109`). Each takes `subject` keyword-only,
**no default** (fixture-default law at the signature layer). Sub-renders (`_render_comms_drain_row`,
`_render_story_message`) NEVER carry it. G1 once-count pins landed for ALL five carriers +
await-empty in `test_comms_read_governance_63b_ii_b.py` (drain:401, await:437, await-empty:474,
story:521, ack:562).

### G2 — rollup message leg — HELD
`_render_rollup` (`server.py:4996`): tokenless (subject None) → the ONE line
`messages: identity required — pass capability=`, **no count, no rows** (existence-leak safe);
with a verified Subject → `render_subject_bound` HEADS the message leg (appended after task/finding
legs, before cursor — LEG-scoped, not response head, so the ungoverned task/finding legs are not
over-claimed). `_rollup_message_activity_lines` (`server.py:5141`) renders `total =
message_window.total`, which IS the FILTERED count (`message_activity_since` splices the read_filter
into BOTH the row SELECT and the `count() … GROUP ALL` — Leg 1: the count describes the set its
label claims). G2 pins landed (read-gov file :614 tokenless, :640 with-capability filtered count).

### P#1 — DUAL translated, not gutted — HELD (sampled)
- `test_comms_footer.py`: the 5 read_fragment splice sites are covered by 2 injection-allowlist
  entries (`messages.py::read_fragment`, `::filter_clause`) in `TestNoCommsIdentityReachesQueryTEXT`,
  adjudicated INDIVIDUALLY (the PDP fragment is fully parameterized — every value a bound param
  `$s_/$p_/$a_`; only structural text interpolated) with a named re-open trigger. NOT a gutting —
  an "allowlist the safe" addition.
- `test_comms_story.py`: the hostile-body containment test PRESERVES its assertion
  (`assert not _forged_row_escapes(rendered)`); only `subject=_STORY_RENDER_SUBJECT` (a benign member
  Subject producing a CONSTANT bound line) is added, chosen so it never perturbs the field-value diff.
  `_StoryCtx._resolve_subject` stubs an ADMIN subject (AllRows ⇒ unfiltered) so the composition tests
  certify arc COMPOSITION/containment exactly as pre-ii-b; the FILTER itself is certified in the
  read-governance file. `messages_for_task` (story's real seam) DOES splice the filter (verified).
- `test_comms_promise_registry.py`: every render driver gets `subject=_RENDER_SUBJECT` added; the
  bound line is CONSTANT across a proof's predicate-true/false renders, so the emit-iff-predicate
  diff is unaffected — assertions preserved.
- Builder claims ~226 reds, 0 deletions, nothing escalated (all reds = "needs capability now"). The
  samples corroborate: reds are the capability-flip mechanical consequence, credentials preserve
  behavior.

### P#4 — F-DUP mutation pin — HELD (with a minor reach note, §R)
`TestTheCredentialingSeamIsSharedByMutation` (`test_wire_isolation_63a.py:278`): control (alice≠bob
resolve distinctly) + mutate the shared `_governed_contract.access_token` seam → `wire_world`'s
resolved identity FLIPS to bob for a fixed ambient alice email. A per-file private copy would keep
resolving alice. All 4 converged files import + call `credentialed_app_context`/`register_owned`
(verified: capability:257, send_scope:268, message_enforcement:577, wire:78).

### P#5 — test_secret_typing allowlist add — CLEAN (evidence-backed, not masking a leak)
`probe_drain_read_63b_ii_b.py:679` mints `SecretStr(PASSWORD)` where `PASSWORD` is imported from
`probe_read_filter_63.py:140: PASSWORD = "spikeroot"` — the well-known spike-surreal **TEST store**
(`ws://127.0.0.1:18000`, never :18500) dev literal, NOT a real secret. The allowlist entry
(`test_secret_typing.py:1070`) is evidence-backed: names the throwaway literal + TEST-store URL, NOT
attack shape S6, with a re-open trigger ("if it ever sources a REAL secret … must move to config.py's
resolver seam"). ✓

### P#6 — trust doctrine on served surfaces — HELD (one accepted-bound observation, §R)
No served count lies under its label: drain counts are labelled "pending"/"unread" edge counts (the
recipient's whole-set edge counts, accepted bound iv), and the bound line names the visibility scope
diff. The rollup with-capability count is FILTERED (matches its label). Tokenless rollup withholds
the count entirely (no leak). One observation on the unfiltered `+N more unread` drain re-ask when the
remainder is invisible-only — §R.

---

## §R — RESIDUAL table (read forward)

| # | residual | severity | disposition |
|---|---|---|---|
| B2 | drain/ack serve read_filter-visible (not agent-ownership): an addressed-but-invisible message is neither served nor stamped | accepted (design) | Correct per §4.3; verified in code. |
| — | drain `+N more unread` re-ask counts invisible remainder (unfiltered count under "pending"); self-correcting (next drain returns empty), bound line names scope | LOW / accepted bound iv | Not a blocker; noted for the ruling's accepted-bound iv. See §R-note. |
| G2 | rollup capability= interface (DN2) | resolved | with-cap filtered count + leg-scoped bound both landed. |
| DN2 | `_rollup(capability=)` interface assumption | resolved in build | served via `serve_message_leg`/`subject`. |
| G1 | future row-bearing read verb needs its own once-count (hand-listed carrier set) | accepted bound | 5 carriers pinned; a NEW verb is surfaced by P5 non-vacuity floor. |
| F-DUP | the mutation pin directly flips only `wire_world`; the other 3 fixtures' routing is by construction (import+call-site) | LOW | Shared fn IS the one impl; call-sites verified. Not a blocker. |

## §R-note — the invisible-remainder re-ask (not a blocker)
`_render_comms_drain` renders `drained {shown} of {total} pending` + `+{remainder} more unread —
re-run with limit={N}` where `total`/`remainder` are the whole-set (unfiltered) edge counts and
`shown` is the visible-served count. When the remainder is entirely invisible messages, the re-ask
names rows the next drain will filter out — but the NEXT drain then returns "no unread messages"
(empty), so it is self-correcting, not an infinite loop, and the bound line names the scope. This is
within the ruling's accepted bound iv (counts are "pending deliveries", never "messages you can read").
Flagged for operator/lead visibility per scope law; NOT a trust violation on my read.

## §P3-M — independent dirty-store MUTATION PROOF (both ways, in a provenance-asserted scratch)

The adversaries built a reference on the frozen contract; I re-confirm discrimination on the
SHIPPED tree (`5d61f9e`). Scratch via `./scripts/scratch_copy.sh`; provenance ASSERTED every run —
`loremaster.__file__ = /tmp/…/scratchpad/refbuild/loremaster/loremaster/__init__.py` (INSIDE the
scratch — #140). Expected-RED sets DECLARED before each run (from the read test structure, not
transcribed from output). Runs `-n 0` (serial, few tests), spike-surreal TEST store `:18000`, run
AFTER the currency gate's pytest finished (ONE pytest at a time — #466).

- **Mutation A — re-add the `to.ack_note` ASSERT** (`_TO_FIELD_SPECS`: `""` → `ASSERT
  string::len($value) <= 4000`). Declared RED: P1 `TestALegacyOverCapNoteCannotDenyADrain`, P2
  `TestNoGovernedTableCarriesAConstraintALegacyRowCanViolate[to]`.
  → **3 failed, 2 passed** — RED: `TestALegacyOverCapNoteCannotDenyADrain::{test_a_dirty_over_cap_note_edge_is_SERVED_and_STAMPED_not_denied,
  test_CONTROL_an_already_seen_edge_is_outside_the_drain_window}` + `…CarriesAConstraint…[to]`; the
  P2 failure carried the EXACT ruled bound text (*"`to.ack_note` carries a store ASSERT — DD-3.c …
  total inbox denial … you owe (a) a heal … (b) the §6/§12.6 dirty-store pin inverted"*). `[message]`
  param stayed GREEN (only `to` mutated). Restore → **5 passed** GREEN.
- **Mutation B — the R19 wrong build: DROP the `grade` ASSERT** (`_MESSAGE_FIELD_SPECS`: grade `ASSERT
  $value IN […]` → `""`). Declared RED: P-G3 `TestAJunkGradeLegacyRowRefusesTheCutover::test_a_legacy_junk_grade_row_refuses_the_real_migrate`,
  P2-m exemption-non-vacuity `…CarriesAConstraint…[message]`.
  → **2 failed, 2 passed** — RED: P-G3 (junk grade now MIGRATES instead of refusing the cutover) +
  `…[message]` with the EXACT ruled text (*"`message.grade` is EXEMPT … but carries NO ASSERT — a
  stale exemption … R19 regression: `grade` must keep it"*). `[to]` param + `test_CONTROL_a_legal_grade_fixture_migrates_cleanly`
  stayed GREEN. Restore → **4 passed** GREEN.

Both mutations discriminate exactly as declared, both directions, with controls. R19's grade KEEP is
load-bearing and pinned two independent ways (P-G3 migrate-refusal + P2-m exemption non-vacuity). The
ASSERT-drop pins would go RED the day the hazard reopens — the "pin the miss" property demonstrated,
not asserted.

## §Housekeeping (non-blocking, flagged per scope law)
- **Stray test artifacts at repo root** (pre-existing at session start per git status; the memory
  backend tests write `test_<pid>_<uuid>.memory.db[-shm/-wal]` to CWD): several sit untracked at the
  repo root. Not this wave's doing and not a gate concern, but the repo root should be clear of stray
  files before the pkt-65 image build — the lead may want a `.gitignore` entry or a fixture-teardown
  fix. Surfaced, not fixed (outside my audit writable set).
- **Idle-gate false nudge** (deviation, above): the brief's two name spellings
  (`coldaudit-63b-iib` comms vs `coldaudit-63b-ii-b` report) made the hook look for the wrong report
  name. Minor; noted so a future brief uses one spelling.

## §Verdict rationale — why GO, not a bare pass
Every property the two adversaries DEFERRED to me (the read-governance correct-build satisfiability,
the dirty-store pin discrimination on the shipped tree) I established by execution, not by reading the
pins: the four read seams provably route through the ONE `governed.read_filter` (single-brain, not a
clone), decode-before-stamp and stamp-only-visible hold in `drain`, ack's invisible-seq → `unknown_message`
holds, the ASSERT-drop pins discriminate both ways with the ruled bound text, and the DUAL translations
preserve their assertions. The MP-7 corpse is deleted; the G1/G2 fidelity gaps are closed with real
pins. Full suite 11242/0 ALONE, currency 0 RED_ORPHANED, typecheck+ruff clean. I could not construct a
wrong build that survives. **GO.**
