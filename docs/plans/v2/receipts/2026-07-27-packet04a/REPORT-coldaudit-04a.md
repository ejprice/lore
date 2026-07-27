# REPORT-coldaudit-04a — the independent COLD REFUTE audit of packet 04a

brief-base v7 read

*Every measurement below was taken **2026-07-27** against `feat/surreal-unification` @ **`5a0be0f`**
(clean tree at start AND end — `git status --short` empty, verified twice, `git -C` semantics per
adversary R14). Live legs ran on **spike-surreal `ws://127.0.0.1:18000` (the TEST store) ONLY** —
`:18500` was never contacted, and no `podman`/systemd unit was touched. Present-tense claims describe
THAT commit; re-derive any number here before relying on it.*

**Scratch provenance (#140).** Every mutation ran in a `./scripts/scratch_copy.sh` tree whose own
guard printed, live:
`loremaster.__file__ = /tmp/…/scratchpad/scratch/loremaster/loremaster/__init__.py`
Each mutated file was `cp -a`-restored from the repo's own content and proven byte-exact with
`diff -q` (not an md5 list — an md5 list is a detector, not a backup). The repo tree was never
mutated. Store reference read as instructed (§0, §1.1–1.5, §3, §4, §6.4, §7); its facts are cited,
never re-transcribed, and the four MEASURED facts the brief supplied were **not** re-probed.

---

## SUMMARY BLOCK

- **VERDICT: GO.** No runtime correctness defect found in the five production files. The flip LANDS
  through the production entry point on a DIRTY store; the shared policy IS the sole decision point;
  the served surface TEACHES end-to-end on real components.
- **CONFIRMED DEFECTS: 3 medium + 2 low.** All five are natural-language / instrument defects — the
  repo's audited failure class — not behaviour. None blocks the commit; F1 and F3 should be fixed
  in this wave (both are one-file edits) rather than passed forward.
- **GATE 1 — `uv run pytest -q -n auto` (FULL): `7134 passed, 36 skipped, 3 xfailed, 1 warning in
  194.03s` · `EXIT=0`.** Reproduces the builder's count EXACTLY. Unpiped; exit captured separately.
- **GATE 2 — `./scripts/typecheck.sh`: `EXIT=0`** — `Success: no issues found in 27 source files` /
  `lorescribe OK`; `34 files` / `loresigil OK`; **`156 files` / `loremaster OK`**.
- **GATE 3 — `uv run ruff check .`: `All checks passed!` · `EXIT=0`.**
- **GATE 4 — contract: `50 passed in 5.43s`** (`test_enforced_relations.py` alone, `-rs` confirms
  **0 skipped**). With `test_derivation_source_unification.py` as instructed:
  **`57 passed, 19 skipped in 5.68s`** — all 19 skips are that file's deliberate packet-43 deferral
  (reason text verified; the exemption guard `test_the_deferred_set_names_EXACTLY_…` is among the
  **7 that RUN**, and the file is inside `testpaths`, so adversary R3 is closed by construction).
- Receipt pointers: §1 (dirty-store, W-A) · §2 (sole-decision mutation, W-E) · §3 (served surface,
  real registry + real ledger) · §4 (removed-behaviour diff) · §5 (NL sweep) · §6 (assertion-vs-
  message) · §RESIDUALS · §WHAT I COULD NOT DETERMINE.

**Packages considered:** none — no mechanism specified or built. This is a read-only audit; the one
thing I wrote was throwaway probe scripts under my scratchpad, which use only the repo's own
`_surreal_harness` helpers and the already-installed `surrealdb` SDK.

---

## §1 — Q1: does the flip LAND through the production entry point on a DIRTY store? **CONFIRMED**

Independent of the packet's own test file: the OLD world is derived **from the diff** (the sole
production change to `_briefed_statements` is the `enforced=True` kwarg), and the migration is driven
by **`BriefLedger.ensure_ready()`**, not by the scaffold's `apply_ddl`.

```
BEFORE: DEFINE TABLE briefed TYPE RELATION IN agent OUT brief SCHEMAFULL PERMISSIONS NONE
AFTER:  DEFINE TABLE briefed TYPE RELATION IN agent OUT brief ENFORCED SCHEMAFULL PERMISSIONS NONE
CONTROL (untouched neighbour): DEFINE TABLE brief TYPE NORMAL SCHEMAFULL PERMISSIONS NONE
enforced_before = False | enforced_after = True | enforced_after_revert = False
```

Twelve legs, each with its control:

| leg | result |
|---|---|
| L0 pre-state: dirty store's `briefed` is NOT enforced | PASS |
| L1 **CONTROL** — pre-flip the store ACCEPTS a fully-dangling edge | PASS (rows=1) |
| L2 `BriefLedger.ensure_ready()` on the DIRTY store | ran |
| L3 the clause LANDED on the EXISTING table | PASS |
| L4 the pre-existing dangling row SURVIVED the `OVERWRITE` | PASS (rows=1) |
| L5 fields + `briefed_in_out` UNIQUE index survived | PASS |
| L6 post-flip a ghost RELATE is REJECTED | PASS — `NotFoundError: The record 'agent:ghost_after' does not exist` |
| L7 **CONTROL** — a REAL pair is still ACCEPTED post-flip | PASS |
| L8 `publish(agent_id=<ghost>)` REFUSED and NAMES the id | PASS |
| L9 the refusal reached NO write path (0 counter rows, 0 brief rows) | PASS |
| L10 **CONTROL** — `publish` with a REGISTERED agent still works | PASS (v1) |

**⚠ MY OWN INSTRUMENT LIED FIRST, and the control is what caught it.** L3's first form read
`INFO FOR TABLE briefed`, which returns fields/indexes/events but **not the table's own definition**
— so it reported `FAIL` while L6 (behavioural) reported the guard live. The corrected instrument is
`INFO FOR DB → ["tables"]["briefed"]`, and it was validated in **both directions**: re-applying the
old-world DDL over the migrated table flips `enforced` back to `False`, so the probe demonstrably
sees change either way. A negative result from the first instrument would have been a false NO-GO.

**Mutation proof of the flip itself** (scratch, provenance printed): deleting `enforced=True` from
`_briefed_statements` reddens **8 pins** in `test_enforced_relations.py` (`8 failed, 42 passed`),
including `TestTheLEDGERsOwnMigrationPathLandsTheGuard::test_ensure_ready_on_a_DIRTY_store_makes_the_guard_LIVE`.
The flip is not deletable green. Matches the builder's 8/8 declared set.

**The order-dependence claim is ∀-true, derived not recalled.** `_briefed_statements`' docstring says
*"Every consumer already applies the agent slice first"*. Derived: the only non-test constructions of
`BriefLedger`/`MessageLedger` in the tree are `server.py:6900` and `server.py:6913`, and
`generate_brief_ddl`/`generate_agent_ddl`/`generate_message_ddl` have **no other non-test consumers**
(`agents.py`, `briefs.py`, `messages.py` only). `server.py` orders `agent_registry.ensure_ready()` →
`brief_ledger.ensure_ready()` → `message_ledger.ensure_ready()`. The cross-reference to
`_message_statements`' identical note is also TRUE (it records the same for `to`).

---

## §2 — Q2: is the shared policy the SOLE decision point, or ROUTING? **SOLE — proven by mutation**

Mutation: `reject_unknown_agents` neutralised to `return None` (accept everything), in the scratch
copy, provenance printed. A private copy underneath any caller would keep that caller green.

`14 failed, 377 passed, 14 skipped` across `test_enforced_relations.py` + `test_message_ledger.py` +
`test_brief_ledger.py`. **All three verbs reddened** — none holds a private decision:

- **`publish`** — `TestPublishRefusesAnUnregisteredAgent::test_an_UNREGISTERED_agent_id_is_REFUSED`
  ×2 and `::test_the_refusal_NAMES_the_bad_agent_id` ×2 → the engine's
  `statement 3 of 4 was rejected (unspecified rejection)` reaches the caller instead.
- **`ack`** — `TestTheIdempotentReAckSignalIsNotConfusedWithAnUnknownAgent::test_an_ack_by_an_UNREGISTERED_agent…`
  ×2 and `TestARefusedAgentIdReachesNoWritePathAtAll::test_a_refused_ack_never_ATTEMPTS_the_RELATE`.
  **This is the leg the contract's own `TestTheSharedPolicyIsTheSOLEDecisionPoint` does NOT cover**
  (it mutates only `publish` and `send`) — I add it as an independent receipt, and it holds.
- **`send`** — `TestSendRefusesBeforeTheWrite::test_a_MIXED_recipient_list_is_refused…` plus
  `test_message_ledger.py::TestSendValidatesEveryRecipientBeforeWritingAnyEdge` ×3.
- **`FakeBriefLedger`** — `test_brief_ledger.py::TestTheFakeLedgerSharesTheUnknownAgentPolicy` (the
  fake derives its error class from the shared module, so it moves too).
- **Controls held**: every `POSITIVE_CONTROL` stayed GREEN, and the contract's own monkeypatching
  mutation legs stayed GREEN (they overwrite my mutation, as predicted).

**Both-ways diff of my declared-RED set (written from `--collect-only` BEFORE the run):** 12 declared,
10 observed. **Two declared reds STAYED GREEN** — that is F1 below, and it is the only reason this
audit found anything at all. I did not "fix" the mismatch by editing my list.

**A second, harder mutation (W-SPLIT) — the hazard the module's own comment names.**
`agent_existence.py` matches the engine's echo against `str(RecordID)` renderings and justifies it by
saying a hand-rolled `str(row["id"]).split(":", 1)[-1]` is *"WRONG for every uuid-shaped id"*. I built
exactly that wrong code:

| suite | result under W-SPLIT |
|---|---|
| `test_enforced_relations.py` (04a's OWN contract) | **50 passed — WAVED IT THROUGH** |
| `test_comms_tool.py` | 879 passed — waved it through |
| `test_brief_ledger.py` | 36 failed |
| `test_message_ledger.py` | 94 failed |
| `test_retry_seam.py` | 5 failed |

The hazard IS caught — by the neighbours, whose fixtures use dash-bearing ids that `str(RecordID)`
brackets. It is **invisible to 04a's own contract**, because every id in that file is
`registered_agent_<hex>` / `unregistered_agent_<zeros>` — unbracketed, so a naive split works on all
of them. Residual R-2 below.

**And the symmetry claim itself is CORRECT — I tried to refute it and failed.** Production mints
agent ids as a bare 32-char `uuid5(...).hex` (`AgentRegistry._agent_id`), which no contract fixture
uses. I probed six shapes on a live 3.2.1 store, each paired with an absent id of the same shape as
its positive control:

```
production uuid5 hex   cdbf8550…  -> agent:cdbf8550…
digit-leading 32-hex   2e75591c…  -> agent:2e75591c…
all-numeric            1234…0012  -> agent:⟨1234…0012⟩
dashed uuid4           a18f37f1-… -> agent:⟨a18f37f1-…⟩
```
**12/12 legs PASS** — every registered id accepted (including both bracketed shapes), every absent id
of the same shape refused — plus `publish(agent_id=<production uuid5 hex>)` → v1 and
`publish(agent_id=<digit-leading 32-hex>)` → v1. The round-trip holds. **REFUTATION FAILED; the code
is right.**

---

## §3 — Q3: can a caller still lose a publish silently, and does the surface TEACH? **CONFIRMED — it teaches**

Real `AgentRegistry` + real `BriefLedger` + real `MessageLedger`, one live database, production wiring
order, **no fakes anywhere**. The reachable production scenario is the reap window: the seam resolves
identity through the registry first, so the policy fires when a row disappears between resolution and
the write. Reproduced by hard-deleting `peer`'s row after resolution.

```
CONTROL publish on a LIVE row succeeds            v1
CONTROL send to a LIVE row succeeds               recipients=['peer']
CONTROL ack on a LIVE row succeeds                v1
the reap landed (peer's row is gone)              rows=0
send  -> UnknownRecipientError:   unknown agent(s): peer (f1c229ce10c756739a0aa9f76fa3988a) — every id must name a registered agent row before a message or a brief can be written in its name
ack   -> UnknownBriefAgentError:  (same text)
publish -> UnknownBriefAgentError: (same text)
the refused publish burned NO version             next real publish got v2
a MIXED recipient list names ONLY the reaped one  (the live third recipient's id is absent from the text)
```
`0 FAIL`. The refusal names **both** the display name and the row id, in all three verbs, and no write
lands. I additionally READ the seam: `AppContext._comms_dispatch` wraps the handler in **no**
`try/except`, so the text above propagates verbatim into the MCP `ToolError` an agent sees (the
mechanism `SchemaRebuildingError`'s docstring documents). I did not construct a full `AppContext`
against a live store — that hop is read, not run; disclosed.

**Two honest scope notes the packet text does not make:**
1. At the tool seam the policy is a **second** teaching layer. The **first** is the registry's own
   name resolution (`agent_registry.touch` → enriched `UnknownAgentError` with a roster; for `send`,
   `_comms_resolve_recipients`). The new prose reaches an agent only on a TOCTOU/reap, or for a
   ledger-level (non-MCP) caller. That does not make it optional — it is the ONLY layer in those
   cases — but nobody should read "brief_publish now teaches" as describing the common path.
2. `ack`'s `_relate_briefed` catches `SurrealStoreError` as the idempotent-re-ack signal. I verified
   the ENFORCED rejection does **not** get swallowed there: `_select_briefed_edge` finds no edge and
   the original rejection re-raises. So even with the app check bypassed there is **no silent loss**
   — the outcome is a raw, uninformative error, not a lie.

---

## §4 — Q4: my independent removed-behaviour enumeration, DIFFED against the builder's 11

I enumerated the deleted/replaced behaviours from the diff **before** opening `REPORT-builder-04a.md`.
15 items; 13 map onto the builder's 11 (its RB-2 and the "Behaviour changed" note each absorb one of
mine). **Two items of mine are absent from the builder's inventory:**

- **D-1 — `BriefLedger.ack`'s ERROR PRECEDENCE changed** (not in RB-1…RB-11 nor the changed-behaviour
  note). The existence check now runs UPSTREAM of the brief/version lookups, so an ack naming both an
  unknown agent and an unknown brief raises a different class than it did. Measured, with controls
  that isolate each error:

  | case | HEAD `5a0be0f` |
  |---|---|
  | unknown agent + unknown brief | `UnknownBriefAgentError` (was `UnknownBriefError`) |
  | unknown agent + unknown VERSION | `UnknownBriefAgentError` (was `UnknownBriefVersionError`) |
  | CONTROL real agent + unknown brief | `UnknownBriefError` |
  | CONTROL real agent + unknown version | `UnknownBriefVersionError` |
  | CONTROL real agent + real brief | no raise |

  **Verdict: dropped-deliberately, and defensible** — the upstream placement IS the design, and the
  ack docstring states it. But the no-consumers ruling excuses not PRESERVING, not not NOTICING, and
  this was not noticed. Report-only; no fix needed beyond acknowledging it.

- **D-2 — a duplicate id carrying two different names now reports only the FIRST name.** Old code
  built `{ref.name for ref in recipients if …}` (a set of names); new code `setdefault`s first-wins
  per id. Builder's RB-6 covers the opposite direction (two ids sharing one name) but not this one.
  **Verdict: dropped-deliberately, trivial** — the id is the load-bearing half and it is always named.

Everything else I found, the builder had: the `dict.fromkeys` dedupe (RB-1), the one-query property
(RB-2), the `$recipient_ids`→`$agent_ids` rename (RB-3 — I confirmed independently that **no** file
in the tree keys on either name), the `_bare_id` derivation (RB-4), the retired error prose (RB-5),
the name-set (RB-6), the raised class (RB-7), `del agent_name` (RB-8), the retired ack docstring
sentence (RB-9), the dangling-endpoint acceptance (RB-10), the order dependence (RB-11), the
check-before-mint change, the TOCTOU window, and the added round trip.

I also verified two of the builder's claims rather than accepting them: `_bare_id`, `_as_rows`,
`_ID_KEY`, `AGENT_TABLE` and `RecordID` all remain used in `messages.py` (no orphaned import or dead
private method), and `send`'s `EmptyRecipientSetError` guard precedes `_reject_unknown_recipients`,
so the new empty short-circuit is unreachable from `send` and inert.

---

## §5 — Q5: natural-language surfaces. BARE, anchor-free sweep — every hit gets its own verdict

Patterns swept with no prefix/paren anchors: `unknown recipient`, `every recipient must`,
`never queries the agent`, `caller-resolved`, `validates NEITHER`, `neither RELATE endpoint`,
`unknown agent:`, `every agent must be a registered`, `REPORT-`.

| # | file:symbol | verdict |
|---|---|---|
| 1 | `messages.py` **module docstring** (`— because the engine validates NEITHER RELATE endpoint`) | **DEFECT (F2)** — FALSE at HEAD |
| 2 | `_message_fakes.py::FakeMessageLedger.send` (`unknown recipient(s): … every recipient must register`) | **DEFECT (F3)** — divergent clone of a retired production string |
| 3 | `_comms_fakes.py::FakeBriefLedger._reject_unknown_agent` (`unknown agent: {id} — every agent must be…`) | **DEFECT (F3)** — new divergent clone shipped by THIS wave |
| 4 | `_message_fakes.py` header comment #5 (`the engine validates NEITHER endpoint`) | stale-but-test-prose — fix alongside F2 |
| 5 | `test_message_ledger.py` module docstring (`the engine validates NEITHER endpoint`) | stale-but-test-prose — fix alongside F2 |
| 6 | `test_message_ledger.py::TestSendValidatesEveryRecipientBeforeWritingAnyEdge` (`An application-level existence check is the ONLY guard`) | stale-but-test-prose — false since `df59f76` |
| 7 | `docs/design/2026-07-12-pkt28-c1-semantics.md` §Roster plumbing (`the brief ledger never queries the agent table itself`) | stale design doc — the ack docstring now says this described the OLD world; the doc still asserts it as current. Operator's call whether a landed design doc gets a correction header. |
| 8 | `agent_existence.py::reject_unknown_agents` (`~50 sites`) | **imprecise served number.** DERIVED by AST over `loremaster/` + `scripts/`: **74** attribute calls named `publish` carry no `agent_id` (53 of them in `test_brief_ledger.py`). The tilde makes it soft, not false — but no gate derives it. |
| 9 | `agent_existence.py` (`REPORT-contract-04a-enforced-3.md §7 D-d`) | **DEFECT (F5)** — bare repo-root REPORT cite in PRODUCTION code |
| 10 | `test_enforced_relations.py:8, :64` (two bare REPORT cites) | F5 — same class; the same file cites `REPORT-probe-pkt04-store.md` correctly via its receipts path, so the rule was known |
| 11 | `test_derivation_source_unification.py:9, :43, :90, :639` | F5 — and `:90` is inside the **skip reason an agent reads at every run** |
| 12 | `briefs.py::coverage` (`caller-resolved roster`) | clean — about the roster param, unaffected |
| 13 | `scripts/comms_consumer_eval.py:188, :841` | clean — it explicitly documents the unknown-recipient reject as ABSENT rather than faked, so the consumer battery is **not** measuring a fiction |
| 14 | tool description for `comms` action `brief_publish` (`mint a new version`) | clean — no retired mechanism |
| 15 | `_briefed_statements` docstring's `server.py` ordering claim | clean — verified ∀ in §1 |
| 16 | `_briefed_statements` docstring's *"exactly as `_message_statements` records for `to`"* | clean — verified, that note exists |

---

## §6 — Q6: does any assertion promise a check it does not perform? **YES — one, and it is F1**

---

## CONFIRMED DEFECTS

### F1 — MEDIUM. The pin the contract names as "THE discriminator" cannot discriminate
`loremaster/tests/test_enforced_relations.py::TestPublishRefusesAnUnregisteredAgent::test_the_refusal_happens_BEFORE_the_version_is_minted`

**The claim.** Its docstring opens *"THE discriminator between 'refused early' and 'rolled back
late'."* Its sibling `test_the_refused_publish_writes_NO_brief_row` explicitly delegates to it:
*"'No row afterwards' cannot tell refused-early from rolled-back-late; the version pin below is what
does."*

**What breaks.** It does not. Under the neutralising mutation — which IS the "rolled back late" build
(the app check decides nothing, `ENFORCED` rejects the write, `_release_version` compensates) — the
pin **PASSES**. Its own docstring anticipates the escape hatch (*"…would still see v1 only if the
release succeeded"*) and on the live 3.2.1 store the release always succeeds, so the condition never
bites. The real discriminator is a pin in a different class.

**Proof, with its control** (scratch, provenance printed, three ids run in isolation):

| pin | under the mutation |
|---|---|
| `…::test_the_refusal_happens_BEFORE_the_version_is_minted` | **PASSED** ← claims to be THE discriminator |
| `…::test_the_refused_publish_writes_NO_brief_row` | PASSED ← honestly documented as non-discriminating |
| `TestARefusedAgentIdReachesNoWritePathAtAll::test_a_refused_publish_never_TOUCHES_the_version_counter_row` | **FAILED** ← the actual discriminator |

`1 failed, 2 passed`. The control that makes this sound: the third pin proves the mutation genuinely
landed and is observable, so the first two passing is a property of THEM, not of a dead mutation.

**Why it matters.** Nothing is broken today — the correct build shipped and the counter-row pin does
the work. The hazard is the prose: a future author reading *"the version pin below is what does [the
discrimination]"* can delete `test_a_refused_publish_never_TOUCHES_the_version_counter_row` as
redundant and take the ONLY discriminator with it, gates green. **Fix (one file):** correct both
docstrings to name the counter-row pin as the discriminator, or strengthen the version pin to assert
the counter row is absent.

### F2 — MEDIUM. Production module prose teaches a retired engine behaviour
`loremaster/loremaster/messages.py` — module docstring, the DELIBERATE DECOUPLING paragraph

**The claim.** *"What the ledger still owns — because the engine validates NEITHER RELATE endpoint
(store reference §4, finding #105) — is that EVERY supplied recipient id must EXIST…"*

**What breaks.** FALSE at HEAD. `to` has carried `ENFORCED` since **`df59f76`** (packet 03 STORE) and
`briefed` since `6f0e03a`. The engine validates **both** endpoints on both edges — I measured the
rejection live (§1 L6, and §2's W-E leg reaches a real `SurrealStoreError` from `to`'s guard). The
sentence states a **false rationale for a required check**, which is worse than a stale fact: an agent
reading it learns the app check is the only guard (and `test_message_ledger.py:676` says exactly that
in as many words) and could conclude the check is deletable once it looks redundant, or that
`ENFORCED` is unavailable.

**Provenance.** Written in `e6b9b81` (03a-1), invalidated by `df59f76` — so **pre-existing, not
introduced by 04a.** It is reported here because 04a is the wave that rewrote *this exact sentence*
out of `_reject_unknown_recipients`' method docstring, three docstrings away, and did not sweep the
module docstring above it — the rename/reshape failure class verbatim. The correct replacement text
already exists: `agent_existence.py`'s module docstring states the real rationale (ENFORCED reports
ONE endpoint, untyped, after the write, and the seam withholds it).

**Fix:** replace the causal clause in `messages.py`, and the three test-prose siblings (§5 rows 4–6)
in the same edit.

### F3 — MEDIUM. The refusal PROSE is cloned into two fakes; production's text has no pin at all
`loremaster/tests/_comms_fakes.py::FakeBriefLedger._reject_unknown_agent` (NEW, this wave) ·
`loremaster/tests/_message_fakes.py::FakeMessageLedger.send` (pre-existing)

**What breaks.** The new fake derives the exception **class** from the shared module — genuinely good,
and it fails closed. Then it hand-writes the message:

- fake: `unknown agent: {agent_id} — every agent must be a registered agent row before a brief can be published or acked in its name`
- prod: `unknown agent(s): {name} ({id}) — every id must name a registered agent row before a message or a brief can be written in its name`

Different prefix, no display name, different tail. `_message_fakes.py` carries the sibling divergence
for `send` and now diverges in the prefix too. **`_message_fakes.py`'s own comment names this exact
class** — *"the body/grade checks above are historical CLONES, and that pattern is exactly how this
oracle's `EmptyRecipientSetError` prose drifted away from production's (finding #190) — a divergence
no surface pin can see, because every surface pin rides the fake"* — and prescribes the cure it
applied one line later: *"CALLS the production validator rather than cloning its rules."* The wave
took the cure for the class and skipped it for the prose.

**And the half that makes it consequential:** `grep` over the whole tree for
`unknown agent(s)` / `every id must name a registered` returns **exactly one hit — the production
source line itself.** **No test anywhere asserts production's served refusal text.** Every pin is a
`id in str(exc)` / `name in str(exc)` substring check, which both strings satisfy. So (a) the fake/
production divergence is invisible, and (b) the served string an agent learns the contract from can be
edited to anything containing the id, with all 7134 tests green. Under the TRUST DOCTRINE the served
surface IS the contract; this one has no instrument.

**Fix (one file, then two call sites):** extract the message into a module-level formatter in
`agent_existence.py` and have both fakes call it — one implementation, per repo law — and add one pin
on the production text. `FakeBriefLedger`'s declared empty-table bound and its named re-open trigger
are well done and should stay.

### F4 — LOW. `ack`'s error precedence changed and was not enumerated
See §4 D-1 for the measured table and controls. Report-only.

### F5 — LOW. A bare repo-root `REPORT-*.md` citation in PRODUCTION code
`loremaster/loremaster/agent_existence.py` cites `REPORT-contract-04a-enforced-3.md §7 D-d`; six more
live in `test_enforced_relations.py` (×2) and `test_derivation_source_unification.py` (×4, one inside
the **skip reason an agent reads on every run**). Repo law bans bare `REPORT-*.md` addresses
precisely because the close-out `git mv` into `docs/plans/v2/receipts/<date>-<packet>/` makes them
**absent, not stale** (#152/#153: 54 of 57 such citations dangled when last derived). The same file
cites `REPORT-probe-pkt04-store.md` correctly via its receipts path, so the rule was known and
applied unevenly. **Fix: rewrite all seven to
`docs/plans/v2/receipts/2026-07-27-packet04a/REPORT-…md §…` as part of the close-out `git mv`,** in
the same commit — otherwise they break the moment the archive lands.

---

## RESIDUALS — every item with an individual verdict

| # | item | verdict |
|---|---|---|
| R-1 | `TestTheSharedPolicyIsTheSOLEDecisionPoint` mutates `publish` and `send` only — **`ack` has no accept-everything leg**. | **Real gap, not a defect.** I supplied the missing receipt myself (§2): `ack`'s three refusal pins DO redden under the mutation, so the property holds — it is simply un-pinned in the contract. One leg would close it. |
| R-2 | 04a's contract **waves through the W-SPLIT wrong build 50/50** — every id in `test_enforced_relations.py` is unbracketed, so the very hazard `agent_existence.py`'s comment names is invisible to the file that owns the policy. | **Real fixture monoculture on a NEW axis (id SHAPE).** Not urgent: `test_brief_ledger.py`/`test_message_ledger.py`/`test_retry_seam.py` catch it (135 reds). Fix = one parametrisation using a dash-bearing or all-numeric id. |
| R-3 | The refusal names the identity as `{created_by} ({agent_id})` in `publish` — `created_by` is the *author* label, not necessarily the agent's registry name. | **Low.** At the tool seam they are the same value (`agent_row.name`); at ledger-level call sites they can differ, making the label mildly misleading. Named, no action recommended. |
| R-4 | `publish`/`ack` each gain ONE round trip when `agent_id` is present — `ack` is on the `register` auto-ack hot path. | **Unmeasured by me, as by the builder (§8.2).** No query-count pin reddened. Named; a measurement, not a fix. |
| R-5 | `_comms_dispatch`'s `Raises:` block lists `ValueError`, `AgentRegistryError`, `BriefLedgerError` — **not `MessageLedgerError`**, which `send`/`drain`/`ack` raise. | **Pre-existing (packet 03), real docstring gap.** `UnknownRecipientError` now propagates through a seam whose docstring does not admit its class. One-line fix. |
| R-6 | `refers` and `answers_to` remain un-`ENFORCED`. | **Correct and deliberate** — the operator-ruled 04a/43 split. The exemption guard runs (not skipped) and is inside `testpaths`. Closes adversary R3. |
| R-7 | Packet deliverable `04-comms-blocks-footer.md:82` — *"Widen #105's own text from 'latent — we never hard-delete' when resolving it"* — is **NOT DONE**. | **Real, unmet.** Verified live: #105 is still `acknowledged` and its subject still reads *"(latent today; live the day anything hard-deletes an agent)"*. Adversary R12 flagged it; it survived the wave. Lead close-out item. |
| R-8 | The **SENDER door** is still open — a `send` whose sender names no `agent` row writes a message row with a ghost sender id. | **Escalated twice already** (adversary R8, builder E-2) and still unruled. I confirm it is untouched by this diff. **Operator's call: fix now (one line — pass the sender into the same shared call) vs. defer with a finding number and a named re-open trigger.** A third pass-forward with no ledger row would be a can-kick. |
| R-9 | Adversary residuals R1/R2 (two gates red at `dfb5cd0`). | **CLOSED** — `369db57`; my full suite is green with an identical count. |
| R-10 | Adversary residuals R4/R6/R7 (floor-vs-message, `_seed_agent_rows` count, stale summary block). | **CLOSED** — verified in-tree at HEAD (the D1 floor is now 6 with its own derivation note; `_seed_agent_rows`' docstring says "every function here"; the `-3` report's block is current). |
| R-11 | Adversary R5's named re-open trigger (an `env`-taking real-ledger helper defeats the D1 coverage sweep's reach). | **Still live, correctly pinned.** No new such helper in this diff. |
| R-12 | `MP-6` covers `brief_publish` at the tool seam; **`brief_ack` has no tool-seam teaching pin.** | **Real, disclosed by the builder (§8.6).** My §3 probe covers `ack` at the LEDGER seam on real components, so the behaviour is verified — only the seam pin is missing. |
| R-13 | 19 skips in `test_derivation_source_unification.py`. | **Deliberate and correctly reasoned** — every skip reason names packet 43 as its entry condition. Not a hidden failure. |
| R-14 | My scratch tree at `/tmp/…/scratchpad/scratch` holds a `scratch_copy.sh` clone; all mutated files restored and `diff -q`-verified byte-exact. | **No repo-state risk.** `git status --short` empty at start and end. The scratch is disposable; delete or leave, your call. |

---

## WHAT I COULD NOT DETERMINE

1. **The full `AppContext` → FastMCP `ToolError` hop.** I READ that `_comms_dispatch` wraps the
   handler in no `try/except` and relied on the repo's own documented SDK behaviour; I did not build a
   live `AppContext` against a real store and call `comms(action="brief_publish")` end-to-end. §3's
   text is measured at the ledger seam on real components; the last hop is read, not run.
2. **Concurrency.** No leg exercises the app check under contention. `publish`'s check-then-mint
   window is a genuine TOCTOU; I confirmed `ENFORCED` is the backstop that makes it safe rather than
   merely narrow, but I did not run an ≥8-way race, and repo law is explicit that a single green run
   never clears a concurrency claim.
3. **Whether pre-existing dangling `briefed` edges exist in production.** I never contacted `:18500`.
   Turning `ENFORCED` on is a FALSE ALL-CLEAR on rows already written (store reference §4). Any
   number here — including zero — is a rumour. #236 rules cleanup out; nobody has measured it.
4. **The deployed artifact.** I built no image and ran nothing in a container. THE TEST ENVIRONMENT IS
   A FICTION: the migration is proven against a dirty TEST store through the ledger's own
   `ensure_ready()`, which proves the recipe. Only the deploy smoke (packet 01a's in-image
   conformance run) proves the cake.
5. **The cost of `ENFORCED` on 3.2.1.** Unmeasured, as by the builder. The store reference's
   *"none measurable"* is a 3.1.5 figure and I did not re-derive it.
6. **Whether the `[fake]` half of `test_brief_ledger.py` SHOULD carry the policy (MP-7).** A
   fake/real parity design question, not an audit finding. The declared bound and its re-open trigger
   are honestly written; I am not entitled to rule on it.

---

## GO — and it survives the residual table

Three medium defects, all natural-language or instrument, none behavioural: **F1** (a pin whose
message promises discrimination it does not perform — the wave's own contract), **F2** (a
pre-existing false rationale in production prose that this wave was best placed to sweep), **F3** (a
cloned refusal string plus the absence of any pin on the served text). Plus two low. The production
change itself withstood every refutation I could construct: the flip lands on a dirty store through
`ensure_ready()`, all three verbs route their decision through the one shared function, the id
round-trip holds on six shapes including the two the fixtures never exercise, no write path is
reached by a refusal, no version is burned, and the served surface names both the identity and the id
on real components. **Commit the wave; fix F1 and F3 in it (each is a single file), and rewrite F5's
seven citations in the same commit as the receipts `git mv`.**
