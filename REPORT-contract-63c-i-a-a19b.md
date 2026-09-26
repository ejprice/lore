brief-base v16 read · brief project v7 read

# REPORT-contract-63c-i-a-a19b — contract addendum a19b for 63c-i-a (amendment 24 §W 1–6 + amendment 25; the LAST contract round)

## SUMMARY BLOCK
- **state:** done-with-deviations (D-1…D-7, §4; none changes a graded probe's assertion)
- **What landed:** `test_fixwave_a19a_63c_i_a.py` revised (MP-A goes RUNTIME: `_ClosureWalk` + its derived pin DELETED with DUAL; `_RegisterPropertySpy` armed around every driven `comms(register)`, covered-driver set CHECKED; CD-1's scoped-but-ownerless pin RE-KEYED per amendment 25, DUAL) + NEW `test_fixwave_a19b_63c_i_a.py` (the adversary's 14 graded definitions — KP1–KP8, KP13, KP14, `_admitting`, `_DIM` — **AST-EQUAL, 7/7 positive controls DIFFERENT**; authored door-#2 both-halves refusal, the D2/WHERE/scope-keyed-count redirect leg, the door-#4b remedy-line pin).
- **deviations:** (D-1) KP12 not landed (keyed on a hypothetical class; N3b-as-built is the ruled #137 bound — demonstrated, §7). (D-2) KP5/KP6 RED at `84af63f` via `monkeypatch.setattr`'s AttributeError on the missing `preflight` — verbatim wins over the "not attribute" RED rule (a changed probe re-triggers an adversary); the absence is taught by `_require_preflight` pins. (D-3) a19a re-exports four helpers BY ASSIGNMENT so the probes' `a19a.<name>` reads type-check (mypy no-implicit-reexport; ruff PLC0414 forbids `X as X`). (D-4) the runtime pin is a NEW authored pin realising am-24 §1's spy (KP13 itself lands verbatim beside it). (D-5) CD-1's scope-keyed-count virtue re-pinned on the redirect leg (amendment 25 dropped only "counts as migrated"). (D-6) D2 has no graded probe — authored. (D-7) reference = the adversary's §A.1 + my door-#2/#4b extension (§A.2). ⚠ Process-table: my FIRST RED run started while a peer project's small pytest was live (brief breach, disclosed; re-run under a clear-table gate, identical count); both the re-run and SAT then saw 1 unidentified pytest at start (§5/§8).
- **Packages considered:** none — no mechanism specified for production (pins reuse `sanitise`'s `CONTROL_CHAR_PATTERN`, `_redirect_the_shared_preconditions`, `_snapshot`, `credentialed_app_context`, the a19a helpers; the reference build is scratch-only; the one CLI remedy named is the existing `lore-adm delete-keep`).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 11 new test-local symbols, all dispositioned (§11).
- **Graded:** n/a — I authored a contract; I graded no one's artifact (base `317b16c`, HEAD-at-report `f97d0d9`; production byte-identical to `84af63f`).
- **decisions-needed:** none open (FK-a19b-1 RULED by amendment 25 `027a3a3`, directive #17020 acked).
- **RED at `84af63f`:** 80 failed / 16 passed (a19a 53 + a19b 27; on-defect; 12 AttributeError = KP5/KP6, D-2) · **SAT:** `11625 passed, 62 skipped, 3 xfailed` EXIT=0, 0 failed, lint/type-clean (§8) · **Mutation:** **33/33 HELD** (32 wrong builds + REF, declare-then-diff both ways; §7)
- **receipt pointers:** §F fork + ruling · §1 required-green · §2 per-item table · §3 VERBATIM/AST receipts · §4 DEVIATIONS · §5 RED@`84af63f` · §6 DUAL · §7 mutation proofs · §8 SAT · §9 gates · §10 BUILDER CONSTRAINTS · §11 DRY ledger · §12 residuals · §A instruments verbatim.

## §0 Capability check (brief-base §4)
- Idle-gate contract written, NOT denied: `/tmp/claude-idle-gate-lore/297217bd-cb03-409c-ac95-0eb7ca9bf74b-contract-63c-i-a-a19b.contract`
  = `{"artifact": "REPORT-contract-63c-i-a-a19b.md"}` (the lead's session id, as the other 63c agents' files carry).
- lore reachable: `lore_comms register` OK (session `63c-20260924`, role `contract`, cadence `≤20m`); `lore_search` used for the
  DRY ledger (§11). ⚠ My first `send` addressed `team-lead` and was REFUSED (not registered in the session — the lead's comms
  name is `lead-63c-2`); re-sent to `lead-63c-2` as #17019. The ruling came back on thread `63c` (#17020), so the
  `q:a19b-door2-halves` question thread still renders "no reply" — the question IS answered.
- grep/rg are hook-blocked (#473): every textual sweep in this report uses `awk` (said so).
- Store reference `docs/reference/surrealdb-31-capabilities.md` read FIRST, in full (§1.4 legacy rows seeded under the
  DDL; §2 `SELECT *` omits NONE; §4/§6.4 record links not existence-checked; §7).
- Base: HEAD `317b16c` at spawn (2026-09-26); HEAD moved during the run by docs-only commits (`5dfa757`, `170a189`,
  `027a3a3`, `bca1ad7`, `ae54f20`, `e5fa7f9`, `f97d0d9` — `git diff --stat 317b16c HEAD -- loremaster lorerunes loresigil lorescribe scripts`
  → empty). Production byte-identical to the checkpoint `84af63f`.

## §F FORKS (brief-base §2 / brief ESCALATION) — written BEFORE the pins that depend on them

### FK-a19b-1 — "message half-pairs — BOTH halves" contradicted a standing CD-1 pin → **RULED: Reading A (amendment 25, `027a3a3`)**
- **Ruling text** (amendment 24 §2 #2): *"the shared preconditions function's message leg … REFUSES on message half-pairs —
  BOTH halves, symmetric with agents"*; the brief glossed it *"(owned-but-unscoped message rows) REFUSED — both halves"*.
- Reading A: refuse (i) owned-but-unscoped AND (ii) scoped-but-ownerless messages. Reading B: (i) only. Reading A
  contradicted `test_fixwave_a19a_63c_i_a.py::TestTheMessageBackfillIsScopeKeyed63cIAa19a::test_a_scoped_but_ownerless_message_is_never_restamped_and_counts_as_migrated`
  (amendment 21 CD-1), which REQUIRED population (ii) to proceed (`refused=False, 1/1/2`).
- Reachability of (ii), measured by reading the writer (`server.py::AppContext._comms_send`, 2026-09-26): a tokenless
  send is a `GovernedDenied` before any write; the governed send stamps `owner_principal=subject.principal_id` beside
  `scope`; the ledger's legacy path writes all three NONE (`messages.py` send-fragment docstring). No writer produces (ii).
- Escalated (report first, then #17019 + one native wake). **Ruled Reading A** by amendment 25 (`027a3a3`, relayed as
  directive #17020, acked): both halves refused in ONE refusal, each with its own count + bounded ids; the CD-1 pin
  RE-KEYED by DUAL (byte-inert survives, "counts as migrated" dropped); CD-1's self-guarding WHERE STAYS, proven by the
  redirect leg; D2 authored + cold-audit graded. Landed as ruled (§2 rows 4a–4d, §6 DUAL rows).

## §1 Required-green enumeration (written BEFORE the pins; re-checked by the reference build and SAT)
A correct a19b build must keep GREEN:
1. Every build prior rulings require green: the whole 63c-i-a contract as amended through a19a (`test_fixwave_a19a_63c_i_a.py`,
   `test_fixwave_a19_63c_i_a.py`, `test_agent_governance_63c_i_a.py`, `test_agent_registry.py`, the 63b-ii-a message
   migrate/enforcement suites, `test_comms_tool.py`) — both helper shapes, the exempt-token/F5 legs, R-Q5-1 integer truth
   + `perturbed-bound`, the fake-preflight mirror.
2. Single-principal stores unchanged on EVERY governed table: legacy agent/memory/message backfills proceed and stamp;
   governed rows byte-identical; idempotent re-runs; memory-only stores migrate memory (the `INFO FOR DB` gate). The door-#2
   refusal must not fire on a store with no half-pair message (pinned: every door-#2 pin's TWIN CONTROL proceeds and
   stamps `m_legacy`; KP7c[message]'s clean store reaches the operator refusal, not a half-pair one).
3. Tokenless register mints no keep; SF-63-1 foreign denial before any agent row; the credentialed register's
   successful path (1 mint) — the runtime pin's CONTROL driver.
4. The race's created-only compensation still deletes a keep this call created (a19a race pin) — door #4b changes only
   the FAILED-delete path.
5. The adversary's graded probes GREEN on a correct build (landed AST-equal; their reference = green, §3/§8).
Every item's pins are inside the SAT full-suite run (§8).

## §2 Per-item table (amendment 24 §W + amendment 25 §W)
Files: **a19a** = `loremaster/tests/test_fixwave_a19a_63c_i_a.py`, **a19b** = `loremaster/tests/test_fixwave_a19b_63c_i_a.py`.
| # | item | pin(s) | wrong build(s) killed (§7) | grading |
|---|---|---|---|---|
| 1 | MP-A → RUNTIME | a19a `TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_EVERY_driven_register_meets_the_runtime_property` over `_RegisterPropertySpy` + `_RUNTIME_DRIVERS` (every `_REFUSAL_FIXTURES` variant + KP13's cadence input + CONTROL + RACE); covered-driver labels CHECKED (== driver list); `_ClosureWalk` & derived pin DELETED (DUAL) | N17, N3b_driven, WB3, NOCOMP, T_RT (test-side bypass); N3b-as-built = the stated bound (declared GREEN) | authored realisation of am-24 §1 (cold audit) |
| 1 | MP-A — KP13 | a19b `test_KP13_a_register_refused_on_a_cadence_conflict_mints_nothing` | N17, N3b_driven | graded probe, AST-equal |
| 2 | MP-B | a19b `test_KP1_…` | N4, N5 | graded, AST-equal |
| 2 | MP-C | a19b `test_KP4_…` | N7 | graded, AST-equal |
| 2 | MP-D | a19b `test_KP5_…` ×6, `test_KP6_…` ×6 (∀ `a19a._REFUSAL_CASES`), `_admitting` | N13, N14 | graded, AST-equal |
| 2 | MP-E | a19b `test_KP2_…`, `test_KP3_…` | N11, N12 | graded, AST-equal |
| 2 | MP-F (FK-a A) | a19b `test_KP7a_…`, `test_KP7b_…`, `test_KP7c_…` ×3 | L3 | graded, AST-equal |
| 2 | MP-G | a19b `test_KP14_…` | N6 | graded, AST-equal |
| 3 | door #1 | a19b `test_KP8_both_half_pairs_are_both_named` | D1a, D1b | graded, AST-equal |
| 4a | door #2 refusal, both halves (am-24 §2 + am-25) | a19b `TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_a_message_half_pair_refuses_the_message_leg_byte_inert[owned-unscoped\|scoped-ownerless\|both-halves]` (TWIN CONTROL, byte-inert, "half-applied", per-half TRUE count + exactly `min(bound, n)` ids, hostile ids sanitised, `None` receipts) | H0, H1, H4, H5, H6, L3 | authored (cold audit) |
| 4b | door #2 bound per half | a19b `…::test_each_halfs_sample_is_bounded_by_THE_constant` (bound 2 over 3+3 ⇒ 2 per half) | H0, H1, H3, H5, H6 | authored |
| 4c | door #2 placement + sharing | a19b `…::test_a_message_half_pair_refuses_the_MESSAGE_leg_only[agent\|memory]`; `…::test_the_message_half_pair_decision_is_THE_shared_functions` (forward) | H1; H0, H2, H4 | authored |
| 4d | D2 + WHERE + scope-keyed counts (am-24 §2 "independently", am-25 "the redirect leg proves the WHERE") | a19b `TestBackfilledIsTheRowsStamped63cIAa19b::test_backfilled_is_the_rows_the_UPDATE_stamped_never_the_pre_count` (shared fn redirected at a clean store; BOTH halves present; `backfilled` == rows actually stamped, both runs; half-pair rows byte-identical; `already_migrated` == rows carrying a scope) | D2, H2, W1s, W1o, C1b | authored (no graded probe exists for D2 — §4 D-6) |
| 4e | CD-1 pin re-key (am-25) | a19a `TestTheMessageBackfillIsScopeKeyed63cIAa19a::test_a_scoped_but_ownerless_message_is_never_restamped` (refused "half-applied", byte-inert, both runs) | H0, H4, H5 | re-keyed by DUAL |
| 5 | door #4b | a19b `TestAFailedCompensationIsNamedToTheCaller63cIAa19b::test_a_FAILED_compensation_serves_the_teaching_plus_ONE_remedy_line` (same class; text STARTS WITH the teaching; exactly ONE appended `\n` line naming the keep's id + `lore-adm delete-keep`; keep left; delete attempted) | N8, R4, R5, R6, NOCOMP | authored (cold audit) |
| 6 | FK-a / FK-b reading A; FK-c moot | FK-a = KP7a/b/c + door-#2 `None` leg; FK-b = KP1; FK-c: the closure walker is deleted | (above) | — |

## §3 §VERBATIM — the graded probes landed AST-EQUAL (amendment 17's definition)
Instrument: `probe_ast_receipt.py` (§A.3) — PASTED = the ```python fence under "### §A.3" in
`git show 58f73b4:REPORT-adversary-63c-i-a-a19a.md`; LANDED = the COMMITTED `test_fixwave_a19b_63c_i_a.py`; compared per
top-level definition by name under the r4b-fix2 `ast_equiv.py` normaliser (docstring whitespace collapsed, import runs
sorted; comments invisible; implicit string concatenation folded by the parser).
Run on the STAGED INDEX blob (`probe_ast_receipt.py :` — exactly the bytes this commit records; the committed blob id
`git rev-parse HEAD:loremaster/tests/test_fixwave_a19b_63c_i_a.py` must equal the `LANDED blob` line), 2026-09-26:
```
LANDED blob 9a93e8d5ee2b5392b32f22b581fc448c8c1a47c5 (rev ':')
EQUIVALENT _DIM
EQUIVALENT test_KP1_a_keep_won_by_a_concurrent_mint_is_never_compensated
EQUIVALENT test_KP2_the_dangling_sender_sample_reads_THE_constant
EQUIVALENT test_KP3_the_half_applied_id_sample_is_bounded_by_THE_constant
EQUIVALENT test_KP4_the_race_refusal_is_the_registrys_own_teaching
EQUIVALENT _admitting
EQUIVALENT test_KP5_register_follows_an_admitting_preflight_for_EVERY_derived_class
EQUIVALENT test_KP6_the_handler_follows_an_admitting_preflight_for_EVERY_derived_class
EQUIVALENT test_KP7a_the_order_refusal_serves_no_unmeasured_count
EQUIVALENT test_KP7b_the_dangling_refusal_serves_no_unmeasured_count
EQUIVALENT test_KP7c_the_operator_only_refusal_serves_no_unmeasured_count
EQUIVALENT test_KP8_both_half_pairs_are_both_named
EQUIVALENT test_KP13_a_register_refused_on_a_cadence_conflict_mints_nothing
EQUIVALENT test_KP14_a_failed_session_keep_mint_is_never_an_ownerless_register
pasted imports missing from landed (less KP12's `agents`): none
ALL 14 graded definitions AST-EQUAL: True
BYTE CONTROL: 9 of 14 graded definitions are NOT byte-verbatim (rewrapped): ['test_KP1_a_keep_won_by_a_concurrent_mint_is_never_compensated', 'test_KP3_the_half_applied_id_sample_is_bounded_by_THE_constant', 'test_KP4_the_race_refusal_is_the_registrys_own_teaching', '_admitting', 'test_KP5_register_follows_an_admitting_preflight_for_EVERY_derived_class', 'test_KP6_the_handler_follows_an_admitting_preflight_for_EVERY_derived_class', 'test_KP8_both_half_pairs_are_both_named', 'test_KP13_a_register_refused_on_a_cadence_conflict_mints_nothing', 'test_KP14_a_failed_session_keep_mint_is_never_an_ownerless_register']
CONTROL test_KP1_a_keep_won_by_a_concurrent_mint_is_never_compensated: 'merely FOUND' -> 'merely SEEN': DIFFERENT
CONTROL test_KP2_the_dangling_sender_sample_reads_THE_constant: '"_REFUSAL_ID_SAMPLE_SIZE", 3' -> '"_REFUSAL_ID_SAMPLE_SIZE", 4': DIFFERENT
CONTROL test_KP4_the_race_refusal_is_the_registrys_own_teaching: 'role="builder")\n        with' -> 'role="scout")\n        with p': DIFFERENT
CONTROL test_KP8_both_half_pairs_are_both_named: 'and 2 in stated' -> 'and 3 in stated': DIFFERENT
CONTROL test_KP13_a_register_refused_on_a_cadence_conflict_mints_nothing: 'cadence="≤9m"' -> 'cadence="≤5m"': DIFFERENT
CONTROL test_KP14_a_failed_session_keep_mint_is_never_an_ownerless_register: 'assert rows == []' -> 'assert rows != []': DIFFERENT
CONTROL _admitting: 'Admits every refusal' -> 'Admits each refusal': DIFFERENT
```
- **14 / 14 graded definitions AST-EQUAL** (KP1–KP8 incl. KP7a/b/c, KP13, KP14, `_admitting`, `_DIM`); every pasted import
  present except `from loremaster import agents`, which only the un-landed KP12 used (D-1).
- **The equivalence is doing work:** 9 of the 14 are NOT byte-verbatim (lint rewraps: docstrings, f-string splits at
  literal boundaries, `ruff format` line breaks), and **7 / 7 positive controls** — one-token edits of a docstring WORD,
  an assertion constant, a call argument, a comparison — each print DIFFERENT for the definition they hit.
- The adversary's behavioural grading was re-measured ON THE LANDED BYTES: §7's builds N4/N5/N6/N7/N11/N12/N13/N14/L3/
  D1a/D1b/N17/WB3 are the adversary's own (re-anchored only where my reference moved their text — N7 and N8, whose
  compensation moved into `_release_the_minted_session_keep`); N3b_driven, NOCOMP, the H/W/R/T builds and C1b are mine.
  Each probe reddens exactly on its named build.

## §4 DEVIATIONS (each with why; none changes a probe's assertion)
- **D-1 · KP12 NOT landed.** The brief's map names KP1–KP8/KP13/KP14 (amendment 24 §4 lists no KP12). KP12 is keyed on a
  class that exists only in the adversary's wrong build (`getattr(agents, "SessionClosedError", None)`) and on a
  hypothetical input (`closed-wave`): landing it pins an imagined refusal by NAME — the static-shape keying amendment 24 §1
  retired. N3b-as-built (that refusal on an undriven input) is exactly the runtime form's ruled bound (#137's shape);
  §7 demonstrates it (declared GREEN, observed GREEN) and demonstrates the factory idiom is NOT a blind spot once its
  input is driven (N3b_driven: RED on KP13 and the runtime pin). The `from loremaster import agents` import only KP12
  used is dropped (F401) — the receipt excludes exactly that one import.
- **D-2 · KP5/KP6 RED at `84af63f` for an ATTRIBUTE reason.** `monkeypatch.setattr(AgentRegistry, "preflight", _admitting)`
  raises `AttributeError` where `preflight` does not exist. The brief's RED rule prefers the `vars().get` pattern or a
  `pending_contracts.yaml` entry; the former changes a graded probe's AST (re-triggers an adversary — amendment 24 §5),
  and the latter registers TYPECHECK errors, not pytest reds (`scripts/pending_contracts.yaml` header). Verbatim wins; the
  red is honest in substance (the ruled method is missing) and the absence is independently TAUGHT at `84af63f` by
  a19a's `_require_preflight` pins (`test_register_itself_decides_with_preflight_in_BOTH_directions`,
  `test_the_handler_decides_with_preflight_BEFORE_the_mint`, the mirror pins — "AgentRegistry.preflight does not
  exist — amendment 22 §1 …").
- **D-3 · a19a re-exports `_DIM`, `_governed_world`, `_seed_clean_single_principal_store`, `_seed_foreign_principals` BY
  ASSIGNMENT** (`_DIM = a19._DIM`, …) instead of importing them. Why: the probes read them as `a19a.<name>`; mypy
  (`./scripts/typecheck.sh`) rejected an imported name read through another module ("does not explicitly export"), and
  ruff PLC0414 rejects the `X as X` re-export. An adaptation OUTSIDE the probes (probe AST unchanged), so no kill needs
  re-proving; the a19a file's own uses are unchanged in behaviour.
- **D-4 · The ∀ runtime pin is authored, KP13 lands beside it.** amendment 24 §1 describes the ∀ as KP13's property
  "asserted by a spy ARMED AROUND EVERY driven register call, with the covered-call count a CHECKED VARIABLE"; KP13 as
  pasted arms a spy around ONE call on ONE input. Two readings (KP13 alone = MP-A; KP13 + a ∀-driver spy pin); the
  brief's item 1 text is the second, so both land. The spy's property is KP13's (`refused ⇒ zero mints`) plus the ruled
  race disjunction; its drivers are `_REFUSAL_FIXTURES` (kept as drivers, per the ruling) + KP13's input + CONTROL +
  RACE. It is NOT a graded probe — the cold audit grades it (flagged, not escalated: no probe's assertion changed).
- **D-5 · CD-1's scope-keyed COUNT virtue re-pinned** on the redirect leg (`already_migrated` == rows carrying a scope;
  `scanned` == all rows). Amendment 25 dropped "counts as migrated"; the re-keyed pin no longer reaches the counts (the
  leg refuses), and without a re-pin the owner-keyed-count build C1b would have survived every pin — killed (§7).
- **D-6 · D2 has no graded probe.** The adversary's D2 row is `0 | 0` and SP2 is print-only; the D2 pin is authored
  (SP2's fixture + the shared-function redirect so the door-#2 refusal cannot fire), as amendment 25 confirms.
- **D-7 · Reference build extension.** The adversary's §A.1 reference (reproduced; md5s match its report for principals /
  agents / server / governed; `keeps.py` differs only in the hand-shortened docstring the adversary names but does not
  paste — mine `f0f2fb66…`, theirs `31b2574b…`) + my door-#2 / door-#4b extension (unified diff pasted, §A.2).

## §5 RED at `84af63f` (main tree; production = `84af63f`; tests = the committed bytes)
Run 2026-09-26 02:36 (chain §A.6, after its clear-table gate; `spike-surreal` active; provenance
`/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` = the main tree, whose production is `84af63f`
bytes), both changed files, `-n 8`:
```
80 failed, 16 passed in 34.68s
```
(An identical `80 failed, 16 passed` run preceded it at ~02:10 — ⚠ started while a peer project's small pytest
(`mobile-pricepaper-smoke`, `tests/test_inventory.py` + dart compiles) was live, which the brief forbids; I noticed
from my own pre-run `ps` count AFTER launching, disclosed it, and re-ran under the clear-table gate. ⚠ That gate saw 0
other pytest twice 15 s apart, yet the re-run's own start line printed `others=1` — an unidentified process appeared in
that second; not a lore suite by the evidence available, and the result is byte-for-byte the same count.)

| file | collected | RED | GREEN at `84af63f` (by design) |
|---|---|---|---|
| a19a | 63 (a19a's 63 − the deleted derived pin + the runtime pin; CD-1 re-keyed in place) | 53 = a19a's 52 − 0 (the deleted pin was GREEN there) + 1 (runtime pin) | 10: the a19a author's 11 minus the deleted derived pin |
| a19b | 33 | 27 | 6: KP1, KP4, KP13, KP14 (they guard behaviours `84af63f` has — no compensation to over-delete or to mask, cadence accepted, mint error propagates; their kills are §7's builds) + `test_a_message_half_pair_refuses_the_MESSAGE_leg_only[agent\|memory]` (placement guards; H1 reddens them) |

RED reasons (the `--tb=line` heads): **51+1 AssertionError** on-defect (e.g. the runtime pin: *"RUNTIME PROPERTY (amendment
24 §1) — driver 'InvalidAgentIdentityError-blank-empty': a REFUSED register (InvalidAgentIdentityError) reached
get_or_create_keyed 1x …"*; the door-#2 pins: *"owned-unscoped: the message leg PROCEEDED over a half-pair:
MigrateGovernedResult(table='message', scanned=3, backfilled=1, already_migrated=2, refused=False …)"*; the re-keyed CD-1
pin: *"first: a scoped-but-ownerless message is a message HALF-PAIR — refuse … scanned=2, backfilled=2 …"*; door #4b:
*"the compensation never ATTEMPTED the delete"*) · **16 `Failed:`** — the a19/a19a teachings *"AgentRegistry.preflight
does not exist — amendment 22 §1 …"* (11) and *"principals._agent_migration_preconditions does not exist …"* (5, incl.
the a19b D2 and forward-sharing pins, via `_redirect_the_shared_preconditions`) · **12 AttributeError** — KP5 ×6 / KP6
×6, `monkeypatch.setattr(AgentRegistry, "preflight", _admitting)` on a missing method (D-2: verbatim wins). Zero
TypeError / ImportError / collection errors.

## §6 DUAL — every pin deleted, re-keyed or re-worded (each carries an in-place DUAL comment)
| # | site | old | new | virtue | verdict |
|---|---|---|---|---|---|
| U1 | a19a `_RaiseSite` / `_ClosureWalk` / `_register_raise_sites` / `_comms_required_classes` / `_WRITE_VERB` / `_PAIR_PARAMETERS` | AST raise-closure derivation of `register`'s pre-write refusal classes | DELETED (module-level DUAL comment in place) | "a new pre-write refusal class arrives with a driven fixture, by NAME" | DROPPED deliberately (am-24 §1): fails OPEN on the factory idiom (N3b) and counts classes not sites (N17); replaced by the runtime property whose bound (undriven refusal) is stated + triggered |
| U2 | a19a `test_every_derived_refusal_class_has_a_driven_fixture` | both-ways class coverage vs `_REFUSAL_FIXTURES`; A3-exclusion staleness check | DELETED; `test_EVERY_driven_register_meets_the_runtime_property` in its place (in-class DUAL comment) | (a) coverage both ways; (b) exclusion (2) checked stale | (a) re-keyed: the driver set is now the checked variable (observed == drivers); a stale-fixture check is moot (a driver is a driver whether or not a static walk sees its class); (b) exclusion (2)'s registry-level coverage (`test_agent_governance_63c_i_a.py::TestTheRegistryProvenanceSeam63cIA::test_an_inconsistent_provenance_pair_is_refused_before_any_store_io`) stands unchanged; its staleness check is DROPPED with the walker (it was a fact about code shape) |
| U3 | a19a `_REFUSAL_FIXTURES` comment | "checked against the DERIVED set both ways" | "the DRIVERS of the runtime property … BOUND … RE-OPEN TRIGGER" | — | prose follows the mechanism |
| U4 | a19a `test_a_scoped_but_ownerless_message_is_never_restamped_and_counts_as_migrated` | proceeds; `m_scoped` byte-identical; counts 1/1/2; second run backfills 0 | `test_a_scoped_but_ownerless_message_is_never_restamped`: refused "half-applied"; whole store byte-identical on both runs | (a) never re-stamped; (b) counts as migrated; (c) scope-keyed counts | (a) PRESERVED (byte-inert under the refusal; the WHERE's own skip pinned on the a19b redirect leg); (b) DROPPED deliberately — population forbidden (am-22 §3 / 24 §2 / 25); (c) PRESERVED-with-pin on the a19b redirect leg (D-5; C1b killed) |
| U5 | a19a race pin docstring BOUND | "a FAILED compensation … is not constructible here" | points at the a19b door-#4b pin | — | bound retired by a pin |
| U6 | a19a imports | `_DIM`, `_governed_world`, `_seed_clean_single_principal_store`, `_seed_foreign_principals` imported; `agents` imported | assigned from `a19` (D-3); `agents` import removed (only the walker used it) | — | no behaviour |

## §7 Mutation proofs — declare-then-diff, both ways (driver §A.4; declared sets IN the driver, written before the run)
Run 2026-09-26 on the reference tree (`./scripts/scratch_copy.sh` copy; provenance printed at the head of the log:
`PROVENANCE …/scratchpad/ref/loremaster/loremaster/__init__.py`), over the 35 collected nodes (the whole a19b file + the
runtime pin + the re-keyed CD-1 pin — `pytest --collect-only -q` → `collect_ids.txt`, md5 `1efe9161…`), `-n 8`, no
other lore pytest live, production restored byte-exact after every build (md5-checked; the a19a test file too).
Driver md5 `8bed8fe0…` (declared sets as written before the run) → `8ed807de…` after ONE fix: build H5's anchor matched
TWICE (the agent precondition query carries the same WHERE text) and the exactly-once guard (#194) STOPPED the run before
any test executed on an unmutated tree; the anchor was widened to include the message `SELECT` line, the declared sets
were NOT touched, and the 9 unrun builds (H5 … T_RT) were run from there (log section "resume after H5 anchor fix").
**33 / 33 HELD (32 wrong builds + REF): declared RED set == observed RED set, both ways, on every build.**

| build | defect | declared RED (before the run) | observed RED | verdict | tail |
|---|---|---|---|---|---|
| REF | — (control: the reference itself) | `[]` | `[]` | HELD | 35 passed in 40.48s |
| N17 | new raise SITE of a covered class (`AgentIdentityConflictError` on a cadence change) in `register` after `preflight` — post-mint | `['KP13', 'RT']` | `['KP13', 'RT']` | HELD | 2 failed, 33 passed in 37.53s |
| N3b_driven | a NEW class raised through the FACTORY idiom (`raise self._cadence_locked_refusal(name)`) on a DRIVEN input | `['KP13', 'RT']` | `['KP13', 'RT']` | HELD | 2 failed, 33 passed in 33.02s |
| N3b | the adversary's N3b as built: factory-idiom `SessionClosedError` on an UNDRIVEN input (`closed-*`) — the ruled BOUND | `[]` | `[]` | HELD | 35 passed in 39.54s |
| WB3 | handler drops `preflight` (mint first; created-only undo) | `['RT']` | `['RT']` | HELD | 1 failed, 34 passed in 21.11s |
| NOCOMP | no compensation at all (the race's keep left; `84af63f`'s shape) | `['C4B', 'RT']` | `['C4B', 'RT']` | HELD | 2 failed, 33 passed in 43.51s |
| N4 | compensation deletes FOUND keeps too | `['KP1']` | `['KP1']` | HELD | 1 failed, 34 passed in 38.22s |
| N5 | "created" from a PRE-READ `get_by_key` (TOCTOU) | `['KP1']` | `['KP1']` | HELD | 1 failed, 34 passed in 39.80s |
| N6 | mint `KeepStoreError` swallowed ⇒ OWNERLESS register | `['KP14']` | `['KP14']` | HELD | 1 failed, 34 passed in 41.78s |
| N7 | compensation masks the teaching with its own refusal | `['KP4']` | `['KP4']` | HELD | 1 failed, 34 passed in 44.73s |
| N8 | a failed compensation's delete error PROPAGATES (replaces the teaching) | `['C4B']` | `['C4B']` | HELD | 1 failed, 34 passed in 49.13s |
| N13 | `register` calls `preflight` AND keeps a private retired check | `['KP5r', 'KP6r']` | `['KP5r', 'KP6r']` | HELD | 2 failed, 33 passed in 48.58s |
| N14 | handler calls `preflight` AND keeps a private retired check | `['KP6r']` | `['KP6r']` | HELD | 1 failed, 34 passed in 40.96s |
| N11 | dangling sample = private literal `10` | `['KP2']` | `['KP2']` | HELD | 1 failed, 34 passed in 48.44s |
| N12 | half-applied id list UNBOUNDED | `['KP3']` | `['KP3']` | HELD | 1 failed, 34 passed in 40.68s |
| L3 | message leg's order / dangling / half-pair / operator refusals serve `0` | `['H_REF_B', 'H_REF_O', 'H_REF_S', 'KP7a', 'KP7b', 'KP7cM']` | `['H_REF_B', 'H_REF_O', 'H_REF_S', 'KP7a', 'KP7b', 'KP7cM']` | HELD | 6 failed, 29 passed in 41.43s |
| D1a | both agent half-pairs: only the half-applied part | `['KP8']` | `['KP8']` | HELD | 1 failed, 34 passed in 41.59s |
| D1b | both agent half-pairs: only the owned-unscoped part | `['KP8']` | `['KP8']` | HELD | 1 failed, 34 passed in 42.28s |
| D2 | message `backfilled` = the scope-keyed pre-count | `['D2P']` | `['D2P']` | HELD | 1 failed, 34 passed in 45.81s |
| H0 | no message half-pair check (= the adversary's reference) | `['CD1', 'H_BOUND', 'H_FWD', 'H_REF_B', 'H_REF_O', 'H_REF_S']` | `['CD1', 'H_BOUND', 'H_FWD', 'H_REF_B', 'H_REF_O', 'H_REF_S']` | HELD | 6 failed, 29 passed in 48.91s |
| H1 | message half-pair check at the VERB (generic text; refuses every table) | `['H_BOUND', 'H_ONLY_A', 'H_ONLY_M', 'H_REF_B', 'H_REF_O', 'H_REF_S']` | `['H_BOUND', 'H_ONLY_A', 'H_ONLY_M', 'H_REF_B', 'H_REF_O', 'H_REF_S']` | HELD | 6 failed, 29 passed in 43.07s |
| H2 | a PRIVATE message half-pair query (both halves) in the leg; the shared function reads none | `['D2P', 'H_FWD']` | `['D2P', 'H_FWD']` | HELD | 2 failed, 33 passed in 41.63s |
| H3 | per-half sample = private literal `10` | `['H_BOUND']` | `['H_BOUND']` | HELD | 1 failed, 34 passed in 40.38s |
| H4 | the sound rows stamped BEFORE the half-pair refusal | `['CD1', 'H_FWD', 'H_REF_B', 'H_REF_O', 'H_REF_S']` | `['CD1', 'H_FWD', 'H_REF_B', 'H_REF_O', 'H_REF_S']` | HELD | 5 failed, 30 passed in 46.76s |
| H5 | Reading B: half (i) only (amendment 25 rejects it) | `['CD1', 'H_BOUND', 'H_REF_B', 'H_REF_S']` | `['CD1', 'H_BOUND', 'H_REF_B', 'H_REF_S']` | HELD | 4 failed, 31 passed in 38.77s |
| H6 | both halves present: only half (i) named | `['H_BOUND', 'H_REF_B']` | `['H_BOUND', 'H_REF_B']` | HELD | 2 failed, 33 passed in 38.53s |
| W1s | backfill WHERE `scope IS NONE` only | `['D2P']` | `['D2P']` | HELD | 1 failed, 34 passed in 42.36s |
| W1o | backfill WHERE `owner_principal IS NONE` only (pre-CD-1) | `['D2P']` | `['D2P']` | HELD | 1 failed, 34 passed in 39.02s |
| C1b | message counts OWNER-keyed | `['D2P']` | `['D2P']` | HELD | 1 failed, 34 passed in 41.61s |
| R4 | failed compensation only LOGGED (the adversary's reference) | `['C4B']` | `['C4B']` | HELD | 1 failed, 34 passed in 40.05s |
| R5 | appended line without the remedy verb | `['C4B']` | `['C4B']` | HELD | 1 failed, 34 passed in 40.52s |
| R6 | remedy line PREPENDED (teaching not at the head) | `['C4B']` | `['C4B']` | HELD | 1 failed, 34 passed in 41.59s |
| T_RT | TEST-side: one driver's register bypasses the armed comms (`spy.arm` skipped for `control-valid`) | `['RT']` | `['RT']` | HELD | 1 failed, 34 passed in 40.47s |

Reading the table:
- **MP-A runtime pin (RT):** kills N17 and N3b_driven (a new refusal on a DRIVEN input, in either raise idiom — the
  static walker's two defeats), WB3 (mint-then-undo), NOCOMP (the race's keep left) and T_RT (a driver bypassing the
  armed comms ⇒ the covered-driver check reds). **N3b as built stays GREEN everywhere, as DECLARED** — the ruled bound
  (#137's shape: a refusal no driver reaches is unobserved), demonstrated rather than asserted.
- Every graded probe kills its named build on MY reference, exactly as on the adversary's (KP1: N4, N5; KP4: N7;
  KP5/KP6[retired]: N13, N14; KP2: N11; KP3: N12; KP7a/b/c[message]: L3; KP8: D1a, D1b; KP13: N17, N3b_driven; KP14: N6).
- Door #2 / D2 / WHERE / counts / #4b: each authored pin reddens on its named builds and on nothing else.

## §8 SAT — the contract is satisfiable by a known-correct build
Reference = the adversary's §A.1 reference + my extension (§A.2), in `./scripts/scratch_copy.sh` tree `…/scratchpad/ref`,
tests = the final a19a + a19b bytes (cmp-identical to the committed files), production md5s in §A. Lint-clean BEFORE
the run and re-verified after it (`uv run ruff check .` → `All checks passed!`; `./scripts/typecheck.sh` → exit 0), so
the post-cleanup run IS this run. Full suite ALONE, `-n 12`, 15 GB PID watchdog (never fired), `spike-surreal` active
(runner §A.5, launched by §A.6 after its clear-table gate):
```
START 2026-09-26T02:37:09-04:00 avail=60G
PROVENANCE /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/664e25f1-c022-4e05-addb-11550f2246d8/scratchpad/ref/loremaster/loremaster/__init__.py
active
other pytest: 1
11625 passed, 62 skipped, 3 xfailed, 7 warnings in 513.87s (0:08:33)
EXIT=0
END 2026-09-26T02:45:50-04:00
```
**0 failed.** 11625 = a19a's SAT 11592 + the 33 a19b nodes (a19a: −1 derived pin +1 runtime pin). **#486 did not
appear.** ⚠ `other pytest: 1` at start — the same unidentified process as §5's re-run (the gate had seen 0 twice);
disclosed, not explained. Additionally: the 35 new/changed nodes alone on the reference → `35 passed in 41.64s`, and
the 7 contract files + the adversary's own probe file on the adversary's reference reproduced its `1500 passed`
before I extended it.

## §9 Gate receipts (main tree, committed bytes)
Main tree, working-tree bytes = the committed test bytes (2026-09-26):
```
$ uv run ruff check .                 → All checks passed!
$ ./scripts/typecheck.sh              → exit 0 (… typecheck: loremaster OK … scripts OK … shellcheck OK)
```
Not run: `pending_contract_gate.py --currency` (the brief forbids a bare run, #466); no `pending_contracts.yaml`
entry is added (it registers typecheck errors, and the tests type-check clean). The full suite at `84af63f` is not a
gate here (RED by design); the SAT run (§8) is the green gate on a correct build.

## §10 BUILDER CONSTRAINTS (every name / keyword / placement the pins require of the production fix)
Carried from a19a (still binding): `AgentRegistry.preflight(name, *, session, role, spawned_by, owner_principal_id,
session_keep_id?)`; `register` calls it first; the handler calls it BY NAME on the wired registry BEFORE
`get_or_create_keyed` (called BY NAME — the spies wrap it); `principals._agent_migration_preconditions` is THE shared
function (the redirect pins rebind it by that name and swap its `StoreHandle` argument); `principals._REFUSAL_ID_SAMPLE_SIZE`
is THE one bound (monkeypatched by name). New in a19b:
1. **`AppContext.comms` is an instance-patchable method** — the runtime spy does `monkeypatch.setattr(ctx, "comms", …)`
   and `monkeypatch.setattr(ctx._keep_store, "get_or_create_keyed", …)`; the handler must reach the keep store through
   `self._keep_store` (as at `84af63f`) and must mint through `get_or_create_keyed`.
2. **Every refusal a driven register can meet precedes the mint** (∀ drivers), except a CONCURRENT register landing
   after the real mint (the race), which must leave keep + `member_of` byte-identical (created-only compensation).
3. **"created" comes from the mint's OWN return** (FK-b A; KP1): no pre-read `get_by_key` may decide it.
4. **The race path serves the registry's refusal unaltered** (KP4) — same class, same text; **a failed mint propagates
   `KeepStoreError` and writes no agent row** (KP14).
5. **Door #2 lives IN `_agent_migration_preconditions`'s message leg** (read when `table == "message"`, beside the
   dangling-sender read): both halves — `scope IS NONE AND owner_principal IS NOT NONE` and `scope IS NOT NONE AND
   owner_principal IS NONE` — each counted and sampled with `_REFUSAL_ID_SAMPLE_SIZE` PER HALF, ONE refusal naming every
   present half, containing `half-applied`, never `multi-principal` / `dangling`, rendering ids through `sanitise_line`,
   refusing the MESSAGE table only (agent/memory proceed), byte-inert, `scanned=None` / `already_migrated=None` /
   `backfilled=0`. The message leg must decide from the SHARED result (a redirected clean store ⇒ proceed).
6. **The message backfill WHERE stays `scope IS NONE AND owner_principal IS NONE`** (CD-1; the redirect leg asserts both
   halves byte-identical); **`backfilled` = the rows the UPDATE stamped** (e.g. `len(<UPDATE result>)`), never a pre-count;
   **counts SCOPE-keyed**: `already_migrated` = rows with a scope, `scanned` = all message rows (on a proceeding run).
7. **Door #4b:** when the compensation's `delete_keep` RAISES, the served exception is the registry refusal's own CLASS,
   its `str()` STARTS WITH the registry's teaching byte-for-byte, followed by exactly ONE `"\n"`-separated line that
   contains the left-behind keep's BARE id and the literal `lore-adm delete-keep` (e.g. `` `lore-adm delete-keep --keep
   <bare id>` ``). Keep the caller's `session` out of that line (the link-5 containment scan flags caller params
   interpolated outside the seam; the keep id is store-minted). The delete error itself must NOT replace the teaching (N8).
8. **FK-a everywhere**: every refusal (verb, order, dangling, half-pair, the legs' operator refusals) serves `None` for
   `scanned` / `already_migrated`.
9. Builder trap carried from the adversary (R-9 there): the fakes' `FakeKeepStore.get_or_create_keyed` signature must
   accept whatever the real one is called with on the tokened path.

## §11 DRY ledger (new reusable symbols — all test-local)
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `_RegisterPropertySpy`, `_RegisterObservation` (a19a) | `lore_search("test spy that wraps AppContext.comms register calls and counts get_or_create_keyed keep mints")` | only itself (live-indexed working tree); the nearest existing is a19a `_spy_the_mint` | HAND-ROLLED — `_spy_the_mint` counts mints for ONE call and cannot observe per-call refusal / keep identity / driver labels; the spy wraps comms around it (it reuses `_keep_snapshot`) |
| `_a_conflicting_register` (a19a) | same query | the a19a race pin's inline `conflicting_register` | EXTENDED in spirit: the same construction, factored so the runtime loop can bind it per world (the race pin itself left untouched) |
| `_kp13_cadence_change`, `_valid_register`, `_race_register`, `_RUNTIME_DRIVERS` (a19a) | — (fixture data) | — | driver data, not policy |
| `_seed_message_half_pair_store`, `_message_identifiers`, `_named`, `_HALVES` (a19b) | `lore_search("seed legacy message rows with owner_principal but no scope half-pair fixture")` | `test_fixwave_a19_63c_i_a.py::_seed_clean_single_principal_store` (a different population) | HAND-ROLLED on REUSED parts: `a19a._seed_migrated_senders`, `seed_message_legacy`, `a19a._names`, `a19a._stated_integers` (SP2's population, extended with half ii) |

## §12 Residuals (every one with an individual verdict)
| # | residual | verdict |
|---|---|---|
| R-1 | The runtime property reaches only what `_RUNTIME_DRIVERS` drives (N3b-as-built stays GREEN — §7). | RULED BOUND (am-24 §1, #137's shape); stated in the spy's docstring with its re-open trigger. |
| R-2 | The runtime spy treats ANY exception from a driven register as "refused" (conservative: a non-registry denial after a mint would also trip it). No current driver reaches such a path. | LOW — by design (a refusal of any class after a mint is #485's harm); re-open if a driver legitimately meets a post-mint non-registry denial. |
| R-3 | Door #2's combination with a dangling sender in the same store is unruled (my reference names both in one refusal; no pin). | LOW — no ruling covers it; not pinned (surfaced for the operator). |
| R-4 | KP1/KP4/KP13/KP14 are GREEN at `84af63f` (§5) — they guard behaviours `84af63f` already has or does not reach; their kills are on the §7 builds. | by design (graded probes). |
| R-5 | The adversary's R-2 (fake-preflight mirror compares outcome CLASS only) and R-3 (`_owner_count` possibly orphaned) are unchanged by a19b. | carried; LOW. |

## §A Instruments (verbatim — the scratch trees are disposable by design)
The reference fix build = the adversary's §A.1 patcher (`git show 58f73b4:REPORT-adversary-63c-i-a-a19a.md` §A.1 —
cited, not re-pasted; extracted by §A.1 below and applied to a `./scripts/scratch_copy.sh` tree of `84af63f` production,
then `ruff check --fix` + the two re-wraps it names) + MY extension (§A.2, the unified diff against the adversary's
reference bytes, which IS the reference extension — produced by `a19b_ref_patch.py` + a lint pass, both scratch-only;
the diff is the authoritative record). Production md5s of the final reference (`ref-prod-a19b/`): principals
`6f3d7044…`, agents `173dca1e…`, server `7b229335…`, keeps `f0f2fb66…`, governed `1a186212…`.

### §A.1 `extract.py` (pulls the adversary's §A fences from the COMMITTED report) — md5 `5613f2d3f03d7896fffbe2b0dc1a054f`
```python
"""Extract the adversary's §A fences from the COMMITTED report (git show 58f73b4)."""
import subprocess, sys
report = subprocess.run(["git", "-C", "/home/ejprice/PycharmProjects/lore", "show",
                         "58f73b4:REPORT-adversary-63c-i-a-a19a.md"], capture_output=True, text=True, check=True).stdout.splitlines(keepends=True)
def fence_after(marker):
    start = next(i for i, line in enumerate(report) if line.startswith(marker))
    open_ = next(i for i in range(start, len(report)) if report[i].startswith("```"))
    close = next(i for i in range(open_ + 1, len(report)) if report[i].strip() == "```")
    return "".join(report[open_ + 1:close])
for marker, out in (("### §A.1", "adv_ref_patch_a19a.py"), ("### §A.2", "adv_wrong_builds_a19a.py"),
                    ("### §A.3", "adv_probes.py"), ("### §A.4", "adv_runners.sh")):
    open(out, "w").write(fence_after(marker))
    print(out, len(fence_after(marker).splitlines()))
```

### §A.2 Reference EXTENSION — `diff -u` adversary-reference → a19b-reference (principals.py, server.py; agents/keeps/governed identical) — md5 `35702963f76d5216836c800af1671f16`
```diff
--- /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/664e25f1-c022-4e05-addb-11550f2246d8/scratchpad/ref-prod-adv/principals.py	2026-09-26 01:45:58.071513585 -0400
+++ /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/664e25f1-c022-4e05-addb-11550f2246d8/scratchpad/ref-prod-a19b/principals.py	2026-09-26 01:58:51.205610664 -0400
@@ -1302,6 +1302,7 @@
     owned_unscoped: list[tuple[Any, Any]]
     ownerless_scoped: list[Any]
     dangling_senders: list[tuple[Any, Any]]
+    message_half_pairs: list[tuple[Any, str]]
 
 
 async def _agent_migration_preconditions(
@@ -1346,6 +1347,7 @@
             else:
                 ownerless_scoped.append(row.get("id"))
     dangling: list[tuple[Any, Any]] = []
+    message_half_pairs: list[tuple[Any, str]] = []
     if table == MESSAGE_TABLE and MESSAGE_TABLE in tables:
         ghost_rows = await run_query(
             acquire=store.acquire,
@@ -1360,11 +1362,31 @@
         dangling = [
             (row.get("id"), row.get("sender")) for row in (ghost_rows or []) if isinstance(row, dict)
         ]
+        half_rows = await run_query(
+            acquire=store.acquire,
+            drop=store.drop,
+            url=store.url,
+            noun="governed message half-pair precondition",
+            label="governed.message_half_pair.rejected",
+            statement=(
+                f"SELECT id, owner_principal, scope FROM {MESSAGE_TABLE} "
+                "WHERE (scope IS NONE AND owner_principal IS NOT NONE) "
+                "OR (scope IS NOT NONE AND owner_principal IS NONE)"
+            ),
+            params={},
+            logger=logger,
+        )
+        message_half_pairs = [
+            (row.get("id"), "owned-unscoped" if row.get("scope") is None else "scoped-ownerless")
+            for row in (half_rows or [])
+            if isinstance(row, dict)
+        ]
     return AgentMigrationPreconditions(
         unscoped_count=unscoped_count,
         owned_unscoped=sorted(owned, key=lambda pair: str(pair[0])),
         ownerless_scoped=sorted(ownerless_scoped, key=str),
         dangling_senders=sorted(dangling, key=lambda pair: str(pair[0])),
+        message_half_pairs=sorted(message_half_pairs, key=lambda pair: str(pair[0])),
     )
 
 
@@ -1571,6 +1593,28 @@
                 "migrate-governed for `agent` first"
             ),
         )
+    if preconditions.message_half_pairs:
+        parts: list[str] = []
+        for kind, noun in (("owned-unscoped", "carry an owner but no scope"),
+                           ("scoped-ownerless", "carry a scope but no owner")):
+            ids = [row_id for row_id, row_kind in preconditions.message_half_pairs if row_kind == kind]
+            if ids:
+                shown_count, shown_ids = _shown(ids)
+                parts.append(
+                    f"{len(ids)} message row(s) {noun} — a half-applied store (one column of the governed "
+                    f"pair was stamped without the other). First {shown_count} of {len(ids)} ids "
+                    f"shown: {shown_ids}."
+                )
+        return MigrateGovernedResult(
+            table=MESSAGE_TABLE,
+            scanned=None,
+            backfilled=0,
+            already_migrated=None,
+            refused=True,
+            reason=" ".join(
+                [*parts, "Adjudicate these messages by hand before migrating `message`; no row was stamped"]
+            ),
+        )
     if preconditions.dangling_senders:
         dangling = preconditions.dangling_senders
         shown = [
--- /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/664e25f1-c022-4e05-addb-11550f2246d8/scratchpad/ref-prod-adv/server.py	2026-09-26 01:45:58.075513689 -0400
+++ /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/664e25f1-c022-4e05-addb-11550f2246d8/scratchpad/ref-prod-a19b/server.py	2026-09-26 01:58:51.211610820 -0400
@@ -2691,6 +2691,21 @@
     def status(self) -> str: ...
 
 
+async def _release_the_minted_session_keep(keep_store: Any, keep_id: str, refusal: Exception) -> None:
+    """Delete the session keep a refused register minted (amendment 22 §1.2). amendment 24 #4b: if the delete
+    FAILS, re-raise the registry's teaching (same class) + ONE appended line: the keep and its remedy."""
+    try:
+        await keep_store.delete_keep(keep_id=keep_id)
+    except Exception:  # noqa: BLE001 - the refusal below is the served outcome
+        logger.warning("register compensation failed to delete keep %s", keep_id)
+        left_behind = str(keep_id).split(":", 1)[-1]
+        raise type(refusal)(
+            f"{refusal}\nALSO: this refused register minted session keep {left_behind} and could not delete "
+            "it — it is LEFT BEHIND and denies the next principal's register into this session; remedy: "
+            f"`lore-adm delete-keep --keep {left_behind}`"
+        ) from refusal
+
+
 class AppContext:
     """The live runtime services bundle the MCP tools dispatch through.
 
@@ -6768,15 +6783,12 @@
                 owner_principal_id=principal_bare,
                 session_keep_id=session_keep_bare,
             )
-        except _AgentRegistryError:
+        except _AgentRegistryError as refusal:
             # The race residual (amendment 22 §1.2): a conflicting register landed between preflight and
-            # register. Delete the session keep ONLY if THIS call created it. BOUND: a failed
-            # compensation leaves the keep; re-open trigger: a keep observed left behind.
+            # register. Delete the session keep ONLY if THIS call created it. amendment 24 #4b: a FAILED
+            # compensation serves the registry's teaching + ONE appended line naming the keep + its remedy.
             if minted_session_keep and keep_store is not None and session_keep is not None:
-                try:
-                    await keep_store.delete_keep(keep_id=session_keep.id)
-                except Exception:  # noqa: BLE001 - the refusal below is the served outcome
-                    logger.warning("register compensation failed to delete keep %s", session_keep.id)
+                await _release_the_minted_session_keep(keep_store, session_keep.id, refusal)
             raise
         now = datetime.now(UTC)
         registered_age_s = int((now - result.agent.registered_at).total_seconds())
```

### §A.3 `probe_ast_receipt.py` (the §VERBATIM instrument; amendment 17's normaliser) — md5 `b471475c147505287ed62e7928342c67`
```python
"""contract-63c-i-a-a19b §VERBATIM — prove each graded probe landed AST-EQUAL (amendment 17's definition: ``ast.dump``
with docstring whitespace collapsed and runs of consecutive imports sorted; comments are not in the AST; implicit
string concatenation is folded by the parser) to the adversary's pasted form.

PASTED  = the ```python fence under "### §A.3" in ``git show 58f73b4:REPORT-adversary-63c-i-a-a19a.md`` (COMMITTED).
LANDED  = ``git show <rev>:loremaster/tests/test_fixwave_a19b_63c_i_a.py`` (COMMITTED; rev ``:`` = the staged INDEX blob,
          i.e. exactly the bytes the commit records), or the working tree if rev=WT.
Compared per top-level definition by NAME: every ``test_KP*`` (KP12 deliberately not landed — §DEVIATIONS), the
``_admitting`` helper and the ``_DIM`` binding. Plus: the pasted module's imports ⊆ the landed module's (less the
one pasted import only KP12 used).

POSITIVE CONTROLS (--controls): one-token mutations of the LANDED source, each of which MUST print DIFFERENT for the
definition it hits (a docstring WORD, an assertion constant, a call argument, a string literal, a comparison).
Usage: python probe_ast_receipt.py <rev|WT> [--controls]"""

import ast
import re
import subprocess
import sys

REPO = "/home/ejprice/PycharmProjects/lore"
LANDED_PATH = "loremaster/tests/test_fixwave_a19b_63c_i_a.py"
NOT_LANDED = {"test_KP12_a_session_closed_register_mints_nothing"}


def git_show(spec: str) -> str:
    return subprocess.run(["git", "-C", REPO, "show", spec], capture_output=True, text=True, check=True).stdout


def pasted_source() -> str:
    report = git_show("58f73b4:REPORT-adversary-63c-i-a-a19a.md").splitlines(keepends=True)
    start = next(i for i, line in enumerate(report) if line.startswith("### §A.3"))
    open_ = next(i for i in range(start, len(report)) if report[i].startswith("```python"))
    close = next(i for i in range(open_ + 1, len(report)) if report[i].strip() == "```")
    return "".join(report[open_ + 1 : close])


class _Normalise(ast.NodeTransformer):
    """Amendment 17's rule (the r4b-fix2 ``ast_equiv.py`` normaliser, reused verbatim in behaviour)."""

    def _body(self, body: list[ast.stmt]) -> list[ast.stmt]:
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            body[0].value.value = re.sub(r"\s+", " ", body[0].value.value).strip()
        out: list[ast.stmt] = []
        run: list[ast.stmt] = []
        for stmt in body + [None]:  # type: ignore[list-item]
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                run.append(stmt)
                continue
            out.extend(sorted(run, key=ast.dump))
            run = []
            if stmt is not None:
                out.append(stmt)
        return out

    def generic_visit(self, node: ast.AST) -> ast.AST:
        super().generic_visit(node)
        for field in ("body", "orelse", "finalbody"):
            value = getattr(node, field, None)
            if isinstance(value, list) and value and isinstance(value[0], ast.stmt):
                setattr(node, field, self._body(value))
        return node


def definitions(source: str) -> dict[str, str]:
    tree = _Normalise().visit(ast.parse(source))
    found: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found[node.name] = ast.dump(node, include_attributes=False)
        elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            found[node.targets[0].id] = ast.dump(node, include_attributes=False)
    return found


def imports(source: str) -> set[str]:
    names = set()
    for node in ast.parse(source).body:
        if isinstance(node, ast.ImportFrom):
            names |= {f"from {node.module} import {alias.name}" for alias in node.names}
        elif isinstance(node, ast.Import):
            names |= {f"import {alias.name} as {alias.asname}" for alias in node.names}
    return names


def compare(landed: str) -> dict[str, bool]:
    pasted = definitions(pasted_source())
    ours = definitions(landed)
    wanted = [name for name in pasted if (name.startswith("test_KP") and name not in NOT_LANDED)
              or name in ("_admitting", "_DIM")]
    return {name: pasted[name] == ours.get(name) for name in wanted}


rev = sys.argv[1]
landed_source = open(f"{REPO}/{LANDED_PATH}").read() if rev == "WT" else git_show(f":{LANDED_PATH}" if rev == ":" else f"{rev}:{LANDED_PATH}")
blob = subprocess.run(["git", "-C", REPO, "hash-object", "--stdin"], input=landed_source, capture_output=True,
                      text=True, check=True).stdout.strip()
print(f"LANDED blob {blob} (rev {rev!r})")
verdicts = compare(landed_source)
for name, equal in verdicts.items():
    print(f"{'EQUIVALENT' if equal else 'DIFFERENT '} {name}")
missing_imports = imports(pasted_source()) - imports(landed_source) - {"from loremaster import agents"}
print(f"pasted imports missing from landed (less KP12's `agents`): {sorted(missing_imports) or 'none'}")
print(f"ALL {len(verdicts)} graded definitions AST-EQUAL: {all(verdicts.values())}")
# BYTE CONTROL: which graded definitions are NOT byte-substrings of the landed file (so the AST equivalence is doing work)
pasted_src = pasted_source()
pasted_tree = ast.parse(pasted_src)
not_bytes = [node.name for node in pasted_tree.body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in verdicts
             and ast.get_source_segment(pasted_src, node) not in landed_source]
print(f"BYTE CONTROL: {len(not_bytes)} of {len(verdicts)} graded definitions are NOT byte-verbatim (rewrapped): {not_bytes}")

if "--controls" in sys.argv:
    controls = [
        ("test_KP1_a_keep_won_by_a_concurrent_mint_is_never_compensated", "merely FOUND", "merely SEEN"),
        ("test_KP2_the_dangling_sender_sample_reads_THE_constant", '"_REFUSAL_ID_SAMPLE_SIZE", 3)\n    async with a19a._governed_world() as world:\n        pairs', '"_REFUSAL_ID_SAMPLE_SIZE", 4)\n    async with a19a._governed_world() as world:\n        pairs'),
        ("test_KP4_the_race_refusal_is_the_registrys_own_teaching", 'role="builder")\n        with pytest.raises(AgentRegistryError) as direct', 'role="scout")\n        with pytest.raises(AgentRegistryError) as direct'),
        ("test_KP8_both_half_pairs_are_both_named", "and 2 in stated", "and 3 in stated"),
        ("test_KP13_a_register_refused_on_a_cadence_conflict_mints_nothing", 'cadence="≤9m"', 'cadence="≤5m"'),
        ("test_KP14_a_failed_session_keep_mint_is_never_an_ownerless_register", "assert rows == []", "assert rows != []"),
        ("_admitting", "Admits every refusal", "Admits each refusal"),
    ]
    for name, old, new in controls:
        assert landed_source.count(old) == 1, f"control anchor occurs {landed_source.count(old)}x: {old[:60]!r}"
        mutated = compare(landed_source.replace(old, new))
        print(f"CONTROL {name}: {old[:28]!r} -> {new[:28]!r}: {'DIFFERENT' if not mutated[name] else 'EQUIVALENT (CONTROL FAILED)'}")
```

### §A.4 `a19b_mut_driver.py` (mutation proofs; the DECLARED sets are in the file — final form, after the H5 anchor fix) — md5 `8ed807def98239f32c02d367882fd72b`
```python
"""contract-63c-i-a-a19b — mutation proofs, DECLARE-THEN-DIFF (both ways), over the a19b pins.

Each build = the a19b reference production bytes (ref-prod-a19b/, md5s in the report) + ONE named defect (the
adversary's N/L/D builds re-anchored where my reference moved their text; my own H/R builds for the authored pins;
one TEST-side mutation for the runtime pin's reach check). The DECLARED red set of every build is written in THIS
FILE, before any run, as short keys mapped to node ids taken from ``pytest --collect-only -q`` (collect_ids.txt).
Every patch asserts it landed exactly once (#194). The run covers the 32 collected nodes (the a19b file + the
runtime pin); observed reds are diffed against the declared set BOTH ways. Production + the a19a test file are
restored byte-exact after every build (md5-checked).
Usage: python a19b_mut_driver.py <scratch-root> <BUILD[,BUILD...]|ALL>
"""

import hashlib
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(sys.argv[1])
HERE = pathlib.Path(__file__).parent
REF = HERE / "ref-prod-a19b"
PROD = {name: f"loremaster/loremaster/{name}.py" for name in ("principals", "agents", "server", "keeps", "governed")}
A19A_TEST = "loremaster/tests/test_fixwave_a19a_63c_i_a.py"
B = "loremaster/tests/test_fixwave_a19b_63c_i_a.py::"
RT_ID = f"{A19A_TEST}::TestEveryRegisterRefusalPrecedesTheKeepMint63cIAa19a::test_EVERY_driven_register_meets_the_runtime_property"
NODES = [line.strip() for line in (HERE / "collect_ids.txt").read_text().splitlines() if "::" in line]
A19A_BACKUP = (ROOT / A19A_TEST).read_bytes()

KEYS = {
    "RT": RT_ID,
    "KP1": B + "test_KP1_a_keep_won_by_a_concurrent_mint_is_never_compensated",
    "KP2": B + "test_KP2_the_dangling_sender_sample_reads_THE_constant",
    "KP3": B + "test_KP3_the_half_applied_id_sample_is_bounded_by_THE_constant",
    "KP4": B + "test_KP4_the_race_refusal_is_the_registrys_own_teaching",
    "KP5r": B + "test_KP5_register_follows_an_admitting_preflight_for_EVERY_derived_class[RetiredAgentError-retired]",
    "KP6r": B + "test_KP6_the_handler_follows_an_admitting_preflight_for_EVERY_derived_class[RetiredAgentError-retired]",
    "KP7a": B + "test_KP7a_the_order_refusal_serves_no_unmeasured_count",
    "KP7b": B + "test_KP7b_the_dangling_refusal_serves_no_unmeasured_count",
    "KP7cM": B + "test_KP7c_the_operator_only_refusal_serves_no_unmeasured_count[message]",
    "KP8": B + "test_KP8_both_half_pairs_are_both_named",
    "KP13": B + "test_KP13_a_register_refused_on_a_cadence_conflict_mints_nothing",
    "KP14": B + "test_KP14_a_failed_session_keep_mint_is_never_an_ownerless_register",
    "D2P": B + "TestBackfilledIsTheRowsStamped63cIAa19b::test_backfilled_is_the_rows_the_UPDATE_stamped_never_the_pre_count",
    "H_REF_O": B + "TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_a_message_half_pair_refuses_the_message_leg_byte_inert[owned-unscoped]",
    "H_REF_S": B + "TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_a_message_half_pair_refuses_the_message_leg_byte_inert[scoped-ownerless]",
    "H_REF_B": B + "TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_a_message_half_pair_refuses_the_message_leg_byte_inert[both-halves]",
    "H_BOUND": B + "TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_each_halfs_sample_is_bounded_by_THE_constant",
    "CD1": f"{A19A_TEST}::TestTheMessageBackfillIsScopeKeyed63cIAa19a::test_a_scoped_but_ownerless_message_is_never_restamped",
    "H_ONLY_A": B + "TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_a_message_half_pair_refuses_the_MESSAGE_leg_only[agent]",
    "H_ONLY_M": B + "TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_a_message_half_pair_refuses_the_MESSAGE_leg_only[memory]",
    "H_FWD": B + "TestAMessageHalfPairRefusesTheMessageLeg63cIAa19b::test_the_message_half_pair_decision_is_THE_shared_functions",
    "C4B": B + "TestAFailedCompensationIsNamedToTheCaller63cIAa19b::test_a_FAILED_compensation_serves_the_teaching_plus_ONE_remedy_line",
}
assert set(KEYS.values()) <= set(NODES), sorted(set(KEYS.values()) - set(NODES))

# ------------------------------------------------------------------ DECLARED before any run
DECLARED: dict[str, set[str]] = {
    "REF": set(),
    "N17": {"KP13", "RT"},        # new raise SITE of a covered class (cadence), register after preflight
    "N3b_driven": {"KP13", "RT"},  # a NEW class via the FACTORY idiom, on a DRIVEN input (the cadence change)
    "N3b": set(),                 # adversary's N3b as built: undriven input ("closed-" session) — the STATED BOUND
    "WB3": {"RT"},                # handler drops preflight: mint, then (created-only) undo
    "NOCOMP": {"RT", "C4B"},      # no compensation at all (84af63f's handler shape on the race)
    "N4": {"KP1"},
    "N5": {"KP1"},
    "N6": {"KP14"},
    "N7": {"KP4"},
    "N8": {"C4B"},
    "N13": {"KP5r", "KP6r"},
    "N14": {"KP6r"},
    "N11": {"KP2"},
    "N12": {"KP3"},
    "L3": {"KP7a", "KP7b", "KP7cM", "H_REF_O", "H_REF_S", "H_REF_B"},
    "D1a": {"KP8"},
    "D1b": {"KP8"},
    "D2": {"D2P"},
    "H0": {"H_REF_O", "H_REF_S", "H_REF_B", "H_BOUND", "H_FWD", "CD1"},  # no message half-pair check (the adversary's reference)
    "H1": {"H_ONLY_A", "H_ONLY_M", "H_REF_O", "H_REF_S", "H_REF_B", "H_BOUND"},  # the check at the VERB (generic text; refuses agent/memory)
    "H2": {"D2P", "H_FWD"},                # a PRIVATE copy (both halves) in the leg, not in THE shared function
    "H3": {"H_BOUND"},                     # the sample a private literal 10
    "H4": {"H_REF_O", "H_REF_S", "H_REF_B", "H_FWD", "CD1"},        # the sound rows stamped before the refusal
    "H5": {"H_REF_S", "H_REF_B", "H_BOUND", "CD1"},  # Reading B: half (i) only (amendment 25 rejects it)
    "H6": {"H_REF_B", "H_BOUND"},          # both halves present: only half (i) named (door #1's shape, messages)
    "W1s": {"D2P"},                        # backfill WHERE `scope IS NONE` only — re-stamps half (i)
    "W1o": {"D2P"},                        # backfill WHERE `owner_principal IS NONE` only (pre-CD-1) — half (ii)
    "C1b": {"D2P"},                        # the message counts OWNER-keyed (CD-1's count virtue, DUAL re-pin)
    "R4": {"C4B"},                         # a failed compensation only LOGGED (the adversary's reference)
    "R5": {"C4B"},                         # appended line without the remedy verb
    "R6": {"C4B"},                         # remedy line PREPENDED (teaching not at the head)
    "T_RT": {"RT"},                        # TEST-side: one driver's register bypasses the armed comms
}

H_PREFLIGHT = """        await self.agent_registry.preflight(
            agent,
            session=session,
            role=role,
            spawned_by=spawned_by,
            owner_principal_id=str(principal.id).split(":", 1)[-1] if principal is not None else None,
        )
"""
REG_CALL = """        existing = await self.preflight(
            name,
            session=session,
            role=role,
            spawned_by=spawned_by,
            owner_principal_id=owner_principal_id,
            session_keep_id=session_keep_id,
        )
"""
CADENCE_REFUSAL_DIRECT = (
    "        if (existing is not None and cadence is not None and existing.declared_cadence is not None\n"
    "                and existing.declared_cadence != cadence):\n"
    "            raise AgentIdentityConflictError(\n"
    "                f\"agent {name!r} is already registered with cadence \"\n"
    "                f\"{render_attributed(existing.declared_cadence)} (you sent {render_attributed(cadence)}) \"\n"
    "                f\"— register a fresh name\"\n"
    "            )\n"
)
HELPER_BODY = """    try:
        await keep_store.delete_keep(keep_id=keep_id)
    except Exception:  # noqa: BLE001 - the refusal below is the served outcome
        logger.warning("register compensation failed to delete keep %s", keep_id)
        left_behind = str(keep_id).split(":", 1)[-1]
        raise type(refusal)(
            f"{refusal}\\nALSO: this refused register minted session keep {left_behind} and could not delete "
            "it — it is LEFT BEHIND and denies the next principal's register into this session; remedy: "
            f"`lore-adm delete-keep --keep {left_behind}`"
        ) from refusal
"""


def patch(key: str, old: str, new: str) -> None:
    path = ROOT / (PROD[key] if key in PROD else key)
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{key}: expected exactly one match, found {count}: {old[:90]!r}"
    path.write_text(text.replace(old, new))


def build(wb: str) -> None:  # noqa: C901, PLR0912, PLR0915 - a flat catalogue
    if wb == "REF":
        return
    if wb == "N17":
        patch("agents", REG_CALL, REG_CALL + CADENCE_REFUSAL_DIRECT)
    elif wb == "N3b_driven":
        patch("agents", "class RetiredAgentError(", "class CadenceLockedError(AgentRegistryError):\n"
              "    \"\"\"WB: a new refusal.\"\"\"\n\n\nclass RetiredAgentError(")
        patch("agents", "    async def preflight(",
              "    @staticmethod\n    def _cadence_locked_refusal(name: str) -> CadenceLockedError:\n"
              "        return CadenceLockedError(f\"agent {name!r} has a locked cadence\")\n\n    async def preflight(")
        patch("agents", REG_CALL, REG_CALL +
              "        if existing is not None and cadence is not None and existing.declared_cadence not in (None, cadence):\n"
              "            raise self._cadence_locked_refusal(name)\n")
    elif wb == "N3b":
        patch("agents", "class RetiredAgentError(", "class SessionClosedError(AgentRegistryError):\n"
              "    \"\"\"WB: a new refusal.\"\"\"\n\n\nclass RetiredAgentError(")
        patch("agents", "    async def preflight(",
              "    @staticmethod\n    def _session_closed_refusal(session: str) -> SessionClosedError:\n"
              "        return SessionClosedError(f\"session {session!r} is closed\")\n\n    async def preflight(")
        patch("agents", REG_CALL, REG_CALL + "        if session.startswith(\"closed-\"):\n"
              "            raise self._session_closed_refusal(session)\n")
    elif wb == "WB3":
        patch("server", H_PREFLIGHT, "")
    elif wb == "NOCOMP":
        patch("server", "                await _release_the_minted_session_keep(keep_store, session_keep.id, refusal)\n",
              "                pass\n")
    elif wb == "N4":
        patch("server", "            if minted_session_keep and keep_store is not None and session_keep is not None:\n",
              "            if keep_store is not None and session_keep is not None:\n")
    elif wb == "N5":
        patch("server", "            session_keep = await keep_store.get_or_create_keyed(\n",
              "            pre_existing = await keep_store.get_by_key(f\"session:{session}\")\n"
              "            session_keep = await keep_store.get_or_create_keyed(\n")
        patch("server", "            minted_session_keep = minted_by_this_call(session_keep)\n",
              "            minted_session_keep = pre_existing is None and callable(minted_by_this_call)\n")
    elif wb == "N6":
        patch("server", "            session_keep = await keep_store.get_or_create_keyed(\n"
              "                key=f\"session:{session}\", type=\"session\", keeper_email=principal.email, name=session\n"
              "            )\n",
              "            from loremaster.keeps import KeepStoreError as _WbKeepError  # noqa: PLC0415\n\n"
              "            try:\n"
              "                session_keep = await keep_store.get_or_create_keyed(\n"
              "                    key=f\"session:{session}\", type=\"session\", keeper_email=principal.email, name=session\n"
              "                )\n"
              "            except _WbKeepError:\n"
              "                session_keep = None\n")
        patch("server", "            minted_session_keep = minted_by_this_call(session_keep)\n"
              "            session_keep_bare = str(session_keep.id).split(\":\", 1)[-1]\n"
              "            visible = await resolve_visible_keeps(keep_store, member_email=principal.email)\n"
              "            if keep_scope(session_keep_bare) not in visible:\n",
              "            minted_session_keep = minted_by_this_call(session_keep)\n"
              "            session_keep_bare = str(session_keep.id).split(\":\", 1)[-1] if session_keep else None\n"
              "            if session_keep is None:\n"
              "                principal_bare = None\n"
              "            visible = await resolve_visible_keeps(keep_store, member_email=principal.email)\n"
              "            if session_keep is not None and keep_scope(session_keep_bare) not in visible:\n")
        patch("server", "            kept_by_me = session_keep.keeper_id == principal_bare\n",
              "            kept_by_me = session_keep is not None and session_keep.keeper_id == principal_bare\n")
    elif wb == "N7":
        patch("server", "                await _release_the_minted_session_keep(keep_store, session_keep.id, refusal)\n            raise\n",
              "                await _release_the_minted_session_keep(keep_store, session_keep.id, refusal)\n"
              "                raise _AgentRegistryError(\"register was refused after the session keep was minted; \"\n"
              "                                          \"the keep was released — retry the register\") from None\n"
              "            raise\n")
    elif wb == "N8":
        patch("server", HELPER_BODY, "    await keep_store.delete_keep(keep_id=keep_id)\n")
    elif wb == "N13":
        patch("agents", REG_CALL, REG_CALL +
              "        if existing is not None and existing.status == STATUS_RETIRED:\n"
              "            raise RetiredAgentError(f\"agent {name!r} is retired (terminal) — respawns register a fresh name\")\n")
    elif wb == "N14":
        patch("server", H_PREFLIGHT, H_PREFLIGHT +
              "        from loremaster.agents import RetiredAgentError as _WbRetired  # noqa: PLC0415\n"
              "        from loremaster.agents import UnknownAgentError as _WbUnknown  # noqa: PLC0415\n\n"
              "        try:\n"
              "            _wb_prior = await self.agent_registry.get_agent(agent, session=session)\n"
              "        except _WbUnknown:\n"
              "            _wb_prior = None\n"
              "        if _wb_prior is not None and _wb_prior.status == \"retired\":\n"
              "            raise _WbRetired(f\"agent {agent!r} is retired (terminal) — respawns register a fresh name\")\n")
    elif wb == "N11":
        patch("principals", "            for message_id, sender in dangling[:_REFUSAL_ID_SAMPLE_SIZE]\n",
              "            for message_id, sender in dangling[:10]\n")
    elif wb == "N12":
        patch("principals", "    shown_count, shown = _shown(ownerless_scoped)\n",
              "    shown_count, shown = len(ownerless_scoped), ', '.join(sanitise_line(str(v)) for v in ownerless_scoped)\n")
    elif wb == "L3":
        text = (ROOT / PROD["principals"]).read_text()
        start = text.index("async def _migrate_message_owner(")
        body = text[start:].replace("            scanned=None,\n", "            scanned=0,\n").replace(
            "            already_migrated=None,\n", "            already_migrated=0,\n")
        (ROOT / PROD["principals"]).write_text(text[:start] + body)
    elif wb == "D1a":
        patch("principals", "    if preconditions.owned_unscoped:\n        operator = await resolve_operator_principal(principal_store)\n",
              "    if preconditions.owned_unscoped and not preconditions.ownerless_scoped:\n"
              "        operator = await resolve_operator_principal(principal_store)\n")
    elif wb == "D1b":
        patch("principals", "    if preconditions.ownerless_scoped:\n        parts.append(_half_applied_part(",
              "    if preconditions.ownerless_scoped and not preconditions.owned_unscoped:\n"
              "        parts.append(_half_applied_part(")
    elif wb == "D2":
        patch("principals", "        backfilled=len(stamped) if isinstance(stamped, list) else unmigrated,\n",
              "        backfilled=unmigrated,\n")
    elif wb == "H0":
        patch("principals", "    if preconditions.message_half_pairs:\n        parts: list[str] = []\n",
              "    if False:  # noqa: SIM108 - WB H0: no message half-pair check\n        parts: list[str] = []\n")
    elif wb == "H1":
        patch("principals", "    preconditions = await _agent_migration_preconditions(store, table=table)\n",
              "    preconditions = await _agent_migration_preconditions(store, table=table)\n"
              "    _wb_message = await _agent_migration_preconditions(store, table=MESSAGE_TABLE)\n"
              "    if _wb_message.message_half_pairs:\n"
              "        return MigrateGovernedResult(table=table, scanned=None, backfilled=0, already_migrated=None,\n"
              "            refused=True, reason='message rows are half-applied; adjudicate by hand')\n")
    elif wb == "H2":  # shared function no longer reads half-pairs; the leg reads them privately
        patch("principals", "        message_half_pairs=sorted(message_half_pairs, key=lambda pair: str(pair[0])),\n",
              "        message_half_pairs=[],\n")
        patch("principals", "    if preconditions.message_half_pairs:\n        parts: list[str] = []\n",
              "    _wb_rows = await run_query(acquire=store.acquire, drop=store.drop, url=store.url, noun='wb', label='wb.r',\n"
              "        statement=f'SELECT id, scope FROM {MESSAGE_TABLE} WHERE (scope IS NONE AND owner_principal IS NOT NONE) '\n"
              "        'OR (scope IS NOT NONE AND owner_principal IS NONE)', params={}, logger=logger)\n"
              "    _wb_pairs = [(row['id'], 'owned-unscoped' if row.get('scope') is None else 'scoped-ownerless')\n"
              "                 for row in (_wb_rows or [])]\n"
              "    if _wb_pairs:\n        preconditions = preconditions.model_copy(update={'message_half_pairs': _wb_pairs})\n"
              "    if preconditions.message_half_pairs:\n        parts: list[str] = []\n")
    elif wb == "H3":
        patch("principals", "                shown_count, shown_ids = _shown(ids)\n",
              "                shown_count, shown_ids = min(10, len(ids)), ', '.join(sanitise_line(str(v)) for v in ids[:10])\n")
    elif wb == "H4":
        patch("principals", "    if preconditions.message_half_pairs:\n        parts: list[str] = []\n",
              "    if preconditions.message_half_pairs:\n"
              "        await run_query(acquire=store.acquire, drop=store.drop, url=store.url, noun='wb', label='wb.r',\n"
              "            statement=f'UPDATE {MESSAGE_TABLE} SET scope = \"keep:wbsound\" WHERE scope IS NONE AND owner_principal IS NONE',\n"
              "            params={}, logger=logger)\n"
              "        parts: list[str] = []\n")
    elif wb == "H5":
        patch("principals", '                f"SELECT id, owner_principal, scope FROM {MESSAGE_TABLE} "\n'
              '                "WHERE (scope IS NONE AND owner_principal IS NOT NONE) "\n'
              '                "OR (scope IS NOT NONE AND owner_principal IS NONE)"\n',
              '                f"SELECT id, owner_principal, scope FROM {MESSAGE_TABLE} "\n'
              '                "WHERE scope IS NONE AND owner_principal IS NOT NONE"\n')
    elif wb == "H6":
        patch("principals", "            if ids:\n                shown_count, shown_ids = _shown(ids)\n",
              "            if ids and not (kind == 'scoped-ownerless' and parts):\n"
              "                shown_count, shown_ids = _shown(ids)\n")
    elif wb == "W1s":
        patch("principals", '        "WHERE scope IS NONE AND owner_principal IS NONE"\n    )\n    with governed_exempt(',
              '        "WHERE scope IS NONE"\n    )\n    with governed_exempt(')
    elif wb == "W1o":
        patch("principals", '        "WHERE scope IS NONE AND owner_principal IS NONE"\n    )\n    with governed_exempt(',
              '        "WHERE owner_principal IS NONE"\n    )\n    with governed_exempt(')
    elif wb == "C1b":
        patch("principals", "    unmigrated = await _scope_count(store, MESSAGE_TABLE, none=True)\n"
              "    already = await _scope_count(store, MESSAGE_TABLE, none=False)\n",
              "    unmigrated = await _owner_count(store, MESSAGE_TABLE, none=True)\n"
              "    already = await _owner_count(store, MESSAGE_TABLE, none=False)\n")
    elif wb == "R4":
        patch("server", HELPER_BODY, """    try:
        await keep_store.delete_keep(keep_id=keep_id)
    except Exception:  # noqa: BLE001 - the refusal below is the served outcome
        logger.warning("register compensation failed to delete keep %s", keep_id)
""")
    elif wb == "R5":
        patch("server", "            \"it — it is LEFT BEHIND and denies the next principal's register into this session; remedy: \"\n"
              "            f\"`lore-adm delete-keep --keep {left_behind}`\"\n",
              "            \"it — it is LEFT BEHIND and denies the next principal's register into this session\"\n")
    elif wb == "R6":
        patch("server", "            f\"{refusal}\\nALSO: this refused register minted session keep {left_behind} and could not delete \"\n",
              "            f\"ALSO: this refused register minted session keep {left_behind} and could not delete \"\n")
        patch("server", "            f\"`lore-adm delete-keep --keep {left_behind}`\"\n        ) from refusal\n",
              "            f\"`lore-adm delete-keep --keep {left_behind}`\\n{refusal}\"\n        ) from refusal\n")
    elif wb == "T_RT":
        patch(A19A_TEST, "                    spy.arm(patch, ctx)\n",
              "                    if label != \"control-valid\":  # WB T_RT: this driver bypasses the armed comms\n"
              "                        spy.arm(patch, ctx)\n")
    else:
        raise SystemExit(f"unknown build {wb}")


def md5(path: pathlib.Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def restore() -> None:
    for name, rel in PROD.items():
        shutil.copyfile(REF / f"{name}.py", ROOT / rel)
        assert md5(ROOT / rel) == md5(REF / f"{name}.py")
    (ROOT / A19A_TEST).write_bytes(A19A_BACKUP)


builds = list(DECLARED) if sys.argv[2] == "ALL" else sys.argv[2].split(",")
failures = 0
for wb in builds:
    restore()
    build(wb)
    run = subprocess.run(["uv", "run", "pytest", "-n", "8", "-q", "-p", "no:cacheprovider", "--tb=no", "-rf", *NODES],
                         cwd=ROOT, capture_output=True, text=True)
    out = run.stdout + run.stderr
    tail = out.strip().splitlines()[-1] if out.strip() else "<no output>"
    red = {line.split()[1] for line in out.splitlines() if line.startswith("FAILED ")}
    red = {re.sub(r" - .*$", "", node) for node in red}
    declared = {KEYS[key] for key in DECLARED[wb]}
    unexpected, still_green = sorted(red - declared), sorted(declared - red)
    inverse = {value: key for key, value in KEYS.items()}
    verdict = "HELD" if not unexpected and not still_green and "passed" in tail or (not red and not declared and "passed" in tail) else "FAILED"
    if verdict == "FAILED":
        failures += 1
    print(f"{wb:11s} {verdict:6s} declared={sorted(DECLARED[wb])} observed={sorted(inverse.get(n, n) for n in red)} | {tail}")
    if unexpected:
        print(f"    UNEXPECTED red: {unexpected}")
    if still_green:
        print(f"    DECLARED but GREEN: {still_green}")
restore()
print(f"restored byte-exact; {len(builds) - failures}/{len(builds)} HELD")
sys.exit(1 if failures else 0)
```

### §A.5 `run_suite.sh` (SAT full suite ALONE -n 12 + 15 GB PID watchdog — the adversary's runner, re-used) — md5 `30a660acd5319c3343419874b37f6577`
```bash
#!/usr/bin/env bash
# contract-63c-i-a-a19b — full suite ALONE, -n 12, PID watchdog kills pytest below 15 GB avail (polls 10 s).
# (the adversary a19a §A.4 runner, re-used.) usage: run_suite.sh <tree> <logfile>
T=$1; LOG=$2
cd "$T" || exit 2
{ echo "START $(date -Is) avail=$(free -g | awk 'NR==2{print $7}')G"; uv run python -c "import loremaster; print('PROVENANCE', loremaster.__file__)"; systemctl --user is-active spike-surreal.service; echo "other pytest: $(ps -eo cmd | awk '/[p]ytest/' | wc -l)"; } > "$LOG" 2>&1
uv run pytest -n 12 -q -p no:cacheprovider --tb=line >> "$LOG" 2>&1 &
PID=$!
while kill -0 $PID 2>/dev/null; do
  if [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ]; then echo "WATCHDOG: killing $PID (avail < 15G)" >> "$LOG"; kill $PID; fi
  sleep 10
done
wait $PID; echo "EXIT=$?" >> "$LOG"; echo "END $(date -Is)" >> "$LOG"
```

### §A.6 `chain.sh` (waits ≤30 min for a clear process table, then RED re-run + SAT) — md5 `9d11edbbfde91d6f1effecf73947ebef`
```bash
#!/usr/bin/env bash
# wait (<=30 min) for NO other pytest on the process table (2 consecutive clear checks 15 s apart), then:
# (1) RED re-run at 84af63f on the main tree, (2) SAT full suite ALONE -n 12 on the reference.
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/664e25f1-c022-4e05-addb-11550f2246d8/scratchpad
L=/home/ejprice/PycharmProjects/lore
deadline=$(( $(date +%s) + 1800 )); clear=0
while [ $clear -lt 2 ]; do
  if [ "$(date +%s)" -gt $deadline ]; then echo "BLOCKED: other pytest live for 30 min $(date -Is)" > $S/chain.status; exit 3; fi
  if [ "$(pgrep -fc '[p]ytest')" -eq 0 ]; then clear=$((clear+1)); else clear=0; fi
  sleep 15
done
echo "CLEAR $(date -Is)" > $S/chain.status
( cd $L && systemctl --user is-active spike-surreal.service && uv run python -c "import loremaster; print('PROVENANCE', loremaster.__file__)" && echo "free=$(free -g | awk 'NR==2{print $7}')G others=$(pgrep -fc '[p]ytest')" && timeout 1500 uv run pytest -n 8 -q -p no:cacheprovider --tb=line -rf loremaster/tests/test_fixwave_a19a_63c_i_a.py loremaster/tests/test_fixwave_a19b_63c_i_a.py ) > $S/red_84af63f_rerun.log 2>&1
echo "RED_DONE $(date -Is)" >> $S/chain.status
while [ "$(free -g | awk 'NR==2{print $7}')" -lt 23 ]; do sleep 10; done
$S/run_suite.sh $S/ref $S/sat_run1.log
echo "SAT_DONE $(date -Is)" >> $S/chain.status
```

Scratch aids NOT pasted (no measured claim rests on them; their output is certified by §A.3's AST receipt and the
ruff gate): two rewrap helpers used for the 110-column lint on docstrings/comments — one of which merged my own `# ===`
section separators into prose in the authored section, caught on read-back and fixed by rewriting that section by hand.

