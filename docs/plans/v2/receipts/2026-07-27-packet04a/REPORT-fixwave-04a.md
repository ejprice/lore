# REPORT-fixwave-04a — closing the three medium findings from packet 04a's cold audit

brief-base v7 read

*Every measurement below was taken **2026-07-27** against `feat/surreal-unification`, base
commit **`6549d53`** (clean tree at start). Live legs ran on **spike-surreal
`ws://127.0.0.1:18000` (the TEST store) ONLY** — `:18500` was never contacted, no `podman` or
systemd unit was touched. Present-tense claims describe the tree at that base plus this
wave's diff; re-derive any number here before relying on it. Store reference
`docs/reference/surrealdb-31-capabilities.md` read as instructed (§1.1, §3, §4 incl. the
`ENFORCED` adoption table, §6.3, §6.4) — its facts are CITED, never re-transcribed, and
nothing here re-probes the engine.*

---

## SUMMARY BLOCK

- **State: done-with-deviations.** F1, F2, F3 all closed; **runtime behaviour unchanged**
  (see the dedicated section below — the passed-count is necessary, not sufficient).
- **F1** — fixed by option **(b)**, the stronger one:
  `test_the_refusal_happens_BEFORE_the_version_is_minted` now ASSERTS the `brief_counter`
  hot row is absent, so its "THE discriminator" docstring is TRUE; both docstrings corrected;
  the two pins now deliberately overlap, so deleting either leaves the discrimination
  standing. Receipt: §F1.
- **F2** — the false rationale replaced in `messages.py` **plus** all three test-prose
  siblings (audit §5 rows 4–6), in one edit. Receipt: §F2.
- **F3** — `agent_existence.format_unknown_agent_refusal` extracted; **both** fakes now CALL
  it; **three** new exact-text pins (production + both fakes) in
  `TestTheSERVEDRefusalTextHasONEImplementation`. `FakeBriefLedger`'s declared bound and
  re-open trigger KEPT verbatim. Receipt: §F3.
- **GATE 1 — `uv run pytest -q -n auto` (FULL, unpiped, exit captured separately):
  `7137 passed, 36 skipped, 3 xfailed, 1 warning in 192.33s` · `EXIT=0`.**
  `7134 → 7137` = exactly the three pins added by F3.
- **GATE 2 — `./scripts/typecheck.sh`: `EXIT=0`** — `27 files`/lorescribe OK · `34
  files`/loresigil OK · **`156 files`/loremaster OK**.
- **GATE 3 — `uv run ruff check .`: `All checks passed!` · `EXIT=0`.**
- **MUTATION PROOFS, both-ways, 5 runs, every declared set taken from `--collect-only`
  BEFORE its run** — F1 BEFORE (`EXIT=4`, reproduces the audit) · F1 AFTER (`EXIT=0`, PROOF
  HELD) · F3 sharing (`EXIT=0`, 3/3 legs red across 1273 tests) · F3 private-copy ×2, one per
  fake (`EXIT=0` each, each reddening EXACTLY its own leg). Receipts: §F1, §F3.
- **DEVIATION (1):** also corrected the `~50 sites` served number in `agent_existence.py` +
  `test_enforced_relations.py` to the independently DERIVED **74** (audit §5 row 8). Inside
  the writable set, outside the three named fixes — revert is one edit. §DEVIATIONS.
- **DECISIONS NEEDED (2):** a live instance of F2's own class survives in
  `docs/reference/surrealdb-31-capabilities.md` §8, and the audit's §5 row 7 design doc is
  still stale. Both are OUTSIDE my writable set. §FLAGS carries the exact edits.
- **Packages considered:** the only mechanism built is an **in-repo extraction** (one
  f-string → one function), which IS the packages rule's in-house half (ONE IMPLEMENTATION).
  For message templating I read `string.Template`'s and `gettext`'s stdlib signatures
  (`Template.substitute`, `gettext.gettext`): both insert an indirection between the served
  sentence and the literal that pins it — the exact seam F3 exists to close — and this repo
  has no message catalogue. Verdict: **bespoke**, i.e. the repo's own function.
- Receipt pointers: §F1 · §F2 · §F3 · §RUNTIME-BEHAVIOUR-UNCHANGED · §DEVIATIONS · §FLAGS ·
  §WHAT I COULD NOT DETERMINE.

---

## §F1 — the pin that claimed to be THE discriminator and could not discriminate

**Chosen fix: (b) — STRENGTHEN the pin so its own claim is true.** Option (a) (concede in
prose) was rejected for the reason the brief gives: a pin that earns its docstring beats a
docstring that concedes, and (b) also removes the deletion hazard *by construction* rather
than by asking a future author to read a warning.

**What changed** (`loremaster/tests/test_enforced_relations.py`):

1. `TestPublishRefusesAnUnregisteredAgent::test_the_refusal_happens_BEFORE_the_version_is_minted`
   now asserts `await _version_counter_rows(ledger) == []` **immediately after the refused
   publish and before** the second, legal publish. The v1 leg is kept and re-labelled in the
   failure message as the *consequence*, not the proof.
2. Its docstring records the correction, dated, with the measurement — including that the
   pin PASSED under the neutralising mutation at `6549d53` — and says the overlap with the
   counter-row pin is deliberate.
3. `test_the_refused_publish_writes_NO_brief_row`'s delegating sentence (*"the version pin
   below is what does"*) is replaced: it now names the **`brief_counter` hot row's absence**
   as the discriminating observation and names BOTH pins that carry it.
4. `TestARefusedAgentIdReachesNoWritePathAtAll::test_a_refused_publish_never_TOUCHES_the_version_counter_row`
   gains a **NOT REDUNDANT WITH** paragraph naming its twin — so the deletion the audit
   feared is now *loud* (a deleter reads why the overlap exists) **and** *harmless* (the
   other pin still discriminates). Deleting BOTH is what re-opens F1, and the docstring says
   so.

**Mutation instrument (identical in both runs).** `reject_unknown_agents` neutralised to
accept everything by inserting `return None` at the top of its body — this IS the
"rolled-back-late" build (the app check decides nothing, `ENFORCED` rejects the write,
`_release_version` compensates). Driven by `scripts/mutation_proof.py` with the declared-RED
node ids taken from `pytest --collect-only -q` **before** either run and never edited
between them.

**Run 1 — BEFORE the fix, at `6549d53` (independent reproduction of the audit's F1):**

```
EXIT=4
PROOF FAILED — the observed RED set is not the declared one.
  DECLARED RED but STAYED GREEN (the pin never fired …):
    - …::TestPublishRefusesAnUnregisteredAgent::test_the_refusal_happens_BEFORE_the_version_is_minted
…
1 failed, 2 passed in 0.85s
tree restored byte-exact (loremaster/loremaster/agent_existence.py: md5 5b570b0e2246fea2eedd4e32cb81fbc6)
```

The one pin that DID fire was `test_a_refused_publish_never_TOUCHES_the_version_counter_row`
(`assert [{'id': RecordID(table_name=brief_counter, record_id='project')}] == []`) — the
control proving the mutation genuinely landed and is observable, so the version pin's pass
was a property of the PIN, not of a dead mutation. **F1 confirmed independently.**

> ⚠ **Disclosure — this run also reported one spurious "unexpected red":**
> `loremaster.store._txn:_txn.py:790 store.transaction.rolled_back`. That is a line of the
> failing test's own **captured log**, not a pytest summary line — `mutation_proof.py`'s
> documented parsing bound ("a line of a test's own captured output beginning with `FAILED `
> is indistinguishable from a summary line"), which applies to `ERROR ` too. It is loud and
> wrong, never silent and wrong. Adding `--show-capture=no` to the child pytest command
> removes it, and every later run here uses that flag.

**Run 2 — AFTER the fix, same mutation, same declared set:**

```
EXIT=0
F.F                                                                      [100%]
FAILED …::TestPublishRefusesAnUnregisteredAgent::test_the_refusal_happens_BEFORE_the_version_is_minted
FAILED …::TestARefusedAgentIdReachesNoWritePathAtAll::test_a_refused_publish_never_TOUCHES_the_version_counter_row
2 failed, 1 passed in 1.00s
tree restored byte-exact (… md5 5b570b0e2246fea2eedd4e32cb81fbc6)
PROOF HELD — the declared RED set fired EXACTLY
```

Re-run VERBATIM on the FINAL tree (after the §DEVIATIONS docstring edit, so this receipt
describes the code as handed over, not an intermediate state): `EXIT=0` ·
`2 failed, 1 passed in 0.71s` · `PROOF HELD` · restored byte-exact, md5
`935e67c9ee5f7e3c48ab254608dbd1f1`.

**Both directions, stated explicitly.** Unexpected reds: **none**. Declared reds that stayed
green: **none**. The third node in the run —
`test_the_refused_publish_writes_NO_brief_row` — was deliberately declared **GREEN** and
stayed green: it is honestly non-discriminating (an `ENFORCED`-only build also leaves no
brief row, by rolling it back), and any redness there would have surfaced as an unexpected
red and failed the proof. That is the control that makes "2 failed, 1 passed" a measurement
rather than a hope.

Reproduce (do not pipe — the pipe's exit status is not the tool's):

```bash
printf '    name_by_id: dict[str, str] = {}\n' > /tmp/anchor.txt
printf '    return None  # MUTATION\n    name_by_id: dict[str, str] = {}\n' > /tmp/replacement.txt
F=loremaster/tests/test_enforced_relations.py
./scripts/mutation_proof.py --file loremaster/loremaster/agent_existence.py \
  --anchor-file /tmp/anchor.txt --replacement-file /tmp/replacement.txt \
  --expect-red "$F::TestPublishRefusesAnUnregisteredAgent::test_the_refusal_happens_BEFORE_the_version_is_minted" \
  --expect-red "$F::TestARefusedAgentIdReachesNoWritePathAtAll::test_a_refused_publish_never_TOUCHES_the_version_counter_row" \
  -- uv run pytest -q --show-capture=no \
     "$F::TestPublishRefusesAnUnregisteredAgent::test_the_refusal_happens_BEFORE_the_version_is_minted" \
     "$F::TestPublishRefusesAnUnregisteredAgent::test_the_refused_publish_writes_NO_brief_row" \
     "$F::TestARefusedAgentIdReachesNoWritePathAtAll::test_a_refused_publish_never_TOUCHES_the_version_counter_row"
```

---

## §F2 — the false RATIONALE for a required check

`loremaster/loremaster/messages.py`, the DELIBERATE DECOUPLING paragraph, said the ledger
owns the existence check *"because the engine validates NEITHER RELATE endpoint"*. FALSE at
`6549d53`: `to` has carried `ENFORCED` since `df59f76`, `briefed` since `6f0e03a`.

**The replacement does three things, in this order:** (1) states what the ledger owns and
names the function that does it; (2) states outright that the engine is NOT blind, with both
commits; (3) gives the TRUE reason the check is required — `ENFORCED` reports ONE bad
endpoint, as untyped prose, only AFTER the write, and the store seam's error hygiene
withholds even that, so the app layer is the only one that can TEACH. Point (3) is **CITED,
not re-transcribed**: it points at `loremaster.agent_existence`'s module docstring (the one
canonical statement) and at store reference §4's `ENFORCED` adoption table, error-ergonomics
row. The paragraph closes with the sentence that makes the defect non-recurring: *"Neither
guard is redundant"* — the false rationale's danger was that it licensed deleting the check
once it looked redundant.

**The three test-prose siblings, fixed in the same edit** (audit §5 rows 4–6):

| # | site | what it now says |
|---|---|---|
| 4 | `loremaster/tests/_message_fakes.py`, adversarial-property comment **#5** | keeps the property, replaces the rationale; states the old claim was TRUE when probe 1 ran and FALSE since `df59f76`, and that this fake models production's TEACHING failure, not the engine's |
| 5 | `loremaster/tests/test_message_ledger.py`, module docstring, DELIBERATE DECOUPLING ¶ | same correction, plus the *"not the only GUARD; the only layer that can TEACH"* distinction |
| 6 | `loremaster/tests/test_message_ledger.py::TestSendValidatesEveryRecipientBeforeWritingAnyEdge` | the *"An application-level existence check is the ONLY guard"* sentence is now explicitly marked FALSE-since-`df59f76`, with the real reason and *"still not deletable as redundant"* |

Each correction quotes the retired claim as history, in the past tense, so the next
anchor-free sweep sees a labelled corpse rather than a live claim. **No assertion was
touched in any of the three** — these are docstrings and one comment.

**Anchor-free sweep, every residual hit with its own verdict** (patterns, no prefix/paren
anchors: `NEITHER`, `neither endpoint`, `neither RELATE`, `ONLY guard`, `only guard`,
`the only guard`, `unknown recipient(s)`, `every recipient must`,
`every agent must be a registered`, `unknown agent:`, `never queries the agent`). Excluding
`REPORT-*.md` at the repo root and `docs/plans/` (out of scope this wave):

| file:symbol | verdict |
|---|---|
| `agent_existence.py::format_unknown_agent_refusal` docstring (2 hits) | **clean — history.** Quotes both retired FAKE strings, past tense, as the reason the function exists |
| `messages.py` module docstring (`…would conclude the app check is the only guard`) | **clean — NEW text**, and the hit is inside the sentence naming that conclusion as the false one |
| `test_message_ledger.py` module docstring / class docstring (2 hits) | **clean — NEW corrected text**, quoting the retired claim as history |
| `_message_fakes.py` comment #5 (1 hit) | **clean — NEW corrected text** |
| `_comms_fakes.py::_shared_unknown_agent_message` docstring (1 hit) | **clean — history**, quotes the retired fake string |
| `loremaster/tests/test_watcher.py` (`the only guard against a` repeat-callback) | **clean — different subject** (watcher callbacks) |
| `loremaster/tests/test_render_seam_pins.py` (`the ONLY guard on the template slot`) | **clean — different subject** (template slot) |
| `loremaster/tests/test_comms_tool.py` (`its only guard` = `test_no_dead_registry_entries`) | **clean — different subject** (registry entries) |
| `loremaster/loremaster/server.py` ×2 (`floor_stub … only guards`, `except BaseException … only guards`) | **clean — different subject** (control flow) |
| `scripts/comms_consumer_eval.py` ×2 (`Neither is re-typed here`, `neither extends nor breaks`) | **clean — the word "neither", unrelated** |
| `docs/reference/surrealdb-31-capabilities.md:730` (§8 `#105` bullet) | ⚠ **LIVE STALE CLAIM — F2's own class, NOT in my writable set.** §FLAGS-1 |
| `docs/design/2026-07-12-pkt28-c1-semantics.md:520` | ⚠ **stale (audit §5 row 7), NOT in my writable set.** §FLAGS-2 |
| `docs/plans/v2/INDEX.md:680` · `docs/plans/v2/28a-report-thread-serving.md:23` | **clean** — the first records the claim AS FALSE; the second is a different subject (a protocol rule) |
| `docs/plans/v2/receipts/2026-07-19-packet03/*` (5 files) | **clean — ARCHIVED, DATED receipts.** Two of them are the reports that FOUND the claim false; archived artifacts keep their claims by law |

---

## §F3 — the served refusal text: one implementation, and its first pin

**The extraction.** `loremaster/loremaster/agent_existence.py` gains a module-level
`format_unknown_agent_refusal(unknown_name_by_id: Mapping[str, str]) -> str`. It owns BOTH
halves of the served surface — the `name (id)` identity rendering AND the sentence — because
handing the fakes only the joined string would have left them cloning the rendering.
`reject_unknown_agents` now builds `unknown` as a `{id: name}` dict and calls it.

**Both fakes CALL it. Neither clones it.**

- `loremaster/tests/_message_fakes.py::FakeMessageLedger.send` — imports the formatter at
  module scope (that file already imports `loremaster.messages`, which imports
  `agent_existence`, so the finding-#133 uncollectable hazard does not apply). Its unknown
  set is now collected **first-wins per ID**, matching production, instead of as a set of
  NAMES: two agents may share a display name, and a name-keyed set silently merged two bad
  recipients into one refusal line.
- `loremaster/tests/_comms_fakes.py::FakeBriefLedger._reject_unknown_agent` — gains a
  **required keyword-only `agent_name`**, threaded from `created_by` (publish) and
  `agent_name` (ack), exactly the values production passes into the shared policy. It is
  required, not defaulted: a default would let the fake serve a different sentence for a
  fixture reason (repo law — a fixture factory must not default a parameter the served text
  depends on). The text comes from a new `_shared_unknown_agent_message()` helper that
  **keeps that file's call-time-import idiom** (finding #133) and **fails closed** via
  `getattr` with no default, exactly like its sibling `_shared_unknown_agent_error()`.
- ✅ **`FakeBriefLedger`'s declared empty-table bound and its named re-open trigger are
  untouched**, as instructed — the paragraph and its trigger sentence are byte-identical.

**The pins** — `test_enforced_relations.py::TestTheSERVEDRefusalTextHasONEImplementation`,
three legs, all comparing against ONE literal produced by a local `_served_refusal(...)`
helper that is **deliberately NOT derived from the production formatter** (deriving it would
be the tautology in a new costume):

| leg | what it holds |
|---|---|
| `test_the_PRODUCTION_refusal_text_is_EXACTLY_the_served_sentence` | the REAL `BriefLedger.publish` on a REAL store — the text an agent actually receives |
| `test_the_BRIEF_fake_serves_the_SAME_sentence_as_production` | `FakeBriefLedger`, `agent` table MODELLED (an empty one is its declared bound) |
| `test_the_MESSAGE_fake_serves_the_SAME_sentence_as_production` | `FakeMessageLedger`, and the leg that pins the JOIN and the SORT: TWO unknown recipients handed in the order that is NOT the served order |

**PROVE SHARING BY MUTATION — the formatter's sentence changed, all three legs must move.**
Mutation: `f"unknown agent(s): …"` → `f"unknown agent identities: …"` in
`agent_existence.py`. Declared-RED set taken from `--collect-only` before the run. Command
run over **four** suites so a private copy anywhere in the fake fleet would surface as an
unexpected red:

```
EXIT=0
mutation LANDED (anchor matched exactly once) in loremaster/loremaster/agent_existence.py
3 failed, 1270 passed, 14 skipped in 16.15s
tree restored byte-exact (loremaster/loremaster/agent_existence.py: md5 89f3eccfb61cceaaa0d98b5ad9353546)
PROOF HELD — the declared RED set fired EXACTLY:
  …::TestTheSERVEDRefusalTextHasONEImplementation::test_the_BRIEF_fake_serves_the_SAME_sentence_as_production
  …::TestTheSERVEDRefusalTextHasONEImplementation::test_the_MESSAGE_fake_serves_the_SAME_sentence_as_production
  …::TestTheSERVEDRefusalTextHasONEImplementation::test_the_PRODUCTION_refusal_text_is_EXACTLY_the_served_sentence
```

(`uv run pytest -q -n auto --show-capture=no test_enforced_relations.py test_brief_ledger.py
test_message_ledger.py test_comms_tool.py`.) **Both directions:** unexpected reds **none**;
declared reds that stayed green **none**. Production and both doubles moved together across
1273 tests — no caller stayed green, so no caller holds a private copy.

**AND THE CONVERSE, which the sharing proof alone does not give: a fake that stops CALLING
the formatter reddens ITS OWN leg, and only its own.** Two further mutations, each turning
one double into a private copy that hand-writes a plausible sentence:

| mutated file | mutation | result |
|---|---|---|
| `_comms_fakes.py::_shared_unknown_agent_message` | `return formatter(...)` → a hand-written `"unknown agent: <ids>"` | `EXIT=0` · `1 failed, 1060 passed` · **PROOF HELD**, only `test_the_BRIEF_fake_serves_the_SAME_sentence_as_production` red |
| `_message_fakes.py::FakeMessageLedger.send` | the formatter call → a hand-written `"unknown recipient(s): <names>"` — the exact string this wave retired | `EXIT=0` · `1 failed, 1143 passed, 14 skipped` · **PROOF HELD**, only `test_the_MESSAGE_fake_serves_the_SAME_sentence_as_production` red |

Both restored byte-exact (`_comms_fakes.py` md5 `12b505a2a7ddb5f5a514ea7c3336064f`;
`_message_fakes.py` md5 `39d64919650747a74c115b030df6ec7a`), zero unexpected reds in either
run — so each leg is ATTRIBUTABLE to its own double, and the second mutation specifically
proves the pin catches the *historical* divergence (names-only, no ids) that shipped
undetected for a whole packet.

**What this closes, measured.** At `6549d53` a tree-wide grep for production's own words
returned **exactly one hit — the source line itself**; every pin over it was a substring
check. The served sentence could have been edited to anything containing the id with the
full suite green. It now cannot: three legs assert it exactly.

---

## RUNTIME BEHAVIOUR IS UNCHANGED — and here is how I know

The full-suite count is necessary and **not** sufficient, so it is the weakest of these four:

1. **The served string is BYTE-IDENTICAL, proven against the retired expression, not
   against my memory of it.** I transcribed the pre-change expression verbatim out of
   `git show 6549d53:loremaster/loremaster/agent_existence.py` and diffed its output against
   the new function over **15 cases**: 0/1/2/3+ identities, 25 identities, two agents sharing
   one display name, a dashed uuid id, an em-dash-and-parens name, and **all 6 permutations
   of a 3-identity input** (so insertion order cannot leak through the new dict). Result:
   `cases=15 mismatches=0`.
2. **The only production edits are one extraction and prose.** `git diff` on
   `loremaster/loremaster/` is 2 files: `messages.py` is **docstring-only** (zero executable
   lines changed), and `agent_existence.py` changes exactly one expression — a `sorted(...)`
   generator became a dict comprehension whose keys/values feed the extracted formatter. No
   call graph, no query, no control flow, no exception type, no DDL. Nothing in the diff
   touches the store, the schema, or a transaction.
3. **The neutralising mutation still produces the SAME behaviour it produced at
   `6549d53`.** §F1 run 2 shows `publish` still reaching the engine, still minting, still
   taking `_release_version` — the mutation observes the same machinery through the same
   path. If the refactor had moved a decision, that run's shape would have changed.
4. **Every consumer suite of both fakes is green at an unchanged count** —
   `test_brief_ledger.py` + `test_message_ledger.py` + `test_comms_tool.py` +
   `test_retry_seam.py` + `test_comms_render_architecture.py`: `1749 passed, 14 skipped`.
   These are the suites whose pins ride the fakes whose messages changed; a behavioural
   change in either double lands here first.

Full suite: `7137 passed, 36 skipped, 3 xfailed` · `EXIT=0`. The delta from the audit's
`7134` is **+3 and only +3** — the three F3 pins, named above and collectable by node id.

---

## DEVIATIONS

**D-1 — I also corrected the `~50 sites` served number (audit §5 row 8), which is outside
the three named fixes.** It is inside my writable set, and it is F2's class: a number in
production prose that no gate derives. I re-derived it MYSELF rather than inheriting the
audit's figure — an AST walk over `loremaster/` + `scripts/` counting attribute calls named
`publish` that carry no `agent_id` keyword:

```
attribute calls named .publish( ... ): 97
…of which carry NO agent_id kwarg:     74
    53  loremaster/tests/test_brief_ledger.py
    10  loremaster/tests/test_comms_tool.py
     5  loremaster/tests/test_comms_render_architecture.py
     4  loremaster/tests/test_retry_seam.py
     1  loremaster/tests/test_enforced_relations.py
     1  loremaster/tests/test_comms_wiring.py
```

**74, reproducing the audit's figure independently — and one fact the audit did not state:
all 74 are TEST sites.** No production caller publishes without an `agent_id`, so the round
trip the empty short-circuit saves is paid by the suite, not the server. The docstring in
`agent_existence.py::reject_unknown_agents` and the mirroring sentence in
`test_enforced_relations.py::test_agent_id_None_is_ACCEPTED_and_writes_no_edge` now carry
the derived number, its population, its date, its derivation, and an explicit *"this is a
dated MEASUREMENT, not a pinned invariant — it drifts with every test added and no gate
derives it; re-derive before citing"*. **I deliberately did NOT add an AST pin for it**: the
count changes on every test added, so a pin would be a maintenance tax that teaches nothing
— the honest instrument for a soft number is a dated derivation, and saying that out loud.
Revert is one edit in each file if the lead disagrees.

**No other deviation.** I touched no file outside the writable set, staged/committed nothing,
and did not touch F5's citations.

---

## FLAGS — outside my writable set, exact edits supplied

**FLAGS-1 (NEW — found by this wave's sweep, not in the audit). F2's own defect is alive in
the store reference itself.** `docs/reference/surrealdb-31-capabilities.md`, §8's open-hazards
list, the `#105` bullet:

> **[#105, OPEN — and NO LONGER LATENT] Dangling `RELATE` edges, on BOTH endpoints** (§4). …
> **An application-level existence check is the only guard**; a typed `TYPE RELATION IN a OUT b`
> catches only wrong-*table* endpoints.

That is the SAME sentence **§6.3 of that very file** records as FALSE (*"this one would have
made us hand-roll a guard the vendor already ships"*) and **§4** replaces with the `ENFORCED`
adoption table. It survived in the hazard list. This is the highest-value residual I found:
the store reference is the file every store/schema/DDL brief is told to read FIRST, and it
currently teaches, in its own summary of open hazards, the exact claim that produced the
§6.3 entry. **Proposed edit** (one bullet):

> …(§4). Goes live the moment any verb accepts a recipient/endpoint identity from a caller
> rather than resolving it from the store. **The engine's `ENFORCED` clause guards both
> endpoints (§4) and is now live on `to` (`df59f76`) and `briefed` (`6f0e03a`); it is a
> BACKSTOP, not a replacement — it reports ONE bad endpoint, as untyped prose, only AFTER
> the write, so an application-level check remains the only layer that can TEACH.** A typed
> `TYPE RELATION IN a OUT b` alone catches only wrong-*table* endpoints.

⚠ Also note the bullet's *"[#105, OPEN]"* label interacts with audit residual R-7 (the
packet deliverable to widen #105's own text), which was still unmet at `6549d53`.

**FLAGS-2 (audit §5 row 7, unchanged).** `docs/design/2026-07-12-pkt28-c1-semantics.md:520`
still asserts *"the brief ledger never queries the agent table itself (one roster
definition, one owner)"* as current. `BriefLedger.ack`'s docstring already records that this
described the OLD world. Operator's call whether a landed design doc gets a correction
header; I made none.

**FLAGS-3 (no action wanted, recorded).** `scripts/comms_consumer_eval.py` was checked and is
**unaffected** by F3: the reject texts it reproduces with throwaway wiring are the grade /
body / empty-recipient ones, and its §C5(a) note already documents the unknown-recipient
reject as **absent rather than faked**. Nothing there was measuring the string I changed.

---

## WHAT I COULD NOT DETERMINE

1. **The tool seam.** My production pin is at the LEDGER seam. `TestBriefPublishTeachesWhenTheAUTHORNamesNoAgentRow`
   (MP-6) covers the served text at the tool seam only as an `id in str(exc)` substring — I
   did not extend it to exact text, because `test_comms_tool.py` is outside my writable set.
   Audit residual R-12 (`brief_ack` has no tool-seam teaching pin at all) is likewise
   untouched.
2. **Concurrency.** Nothing here was exercised under contention, and repo law is explicit
   that a single green run never clears a concurrency claim. The refactor adds no await and
   no shared state, but that is an argument, not a measurement.
3. **The deployed artifact.** No image was built and nothing ran in a container. THE TEST
   ENVIRONMENT IS A FICTION applies unchanged: the served-text pins prove the recipe, and
   only packet 01a's in-image conformance run proves the cake. That said, every change in
   this wave is prose plus one pure-function extraction, so the deploy exposure is the
   lowest of any 04a wave.
4. **Whether `~50` was ever right.** I derived 74 today; I did not derive what the number was
   on the day the sentence was written, so I cannot say whether it was wrong-when-written or
   correct-then-drifted. The correction is dated for exactly that reason.
5. **The audit's residuals R-7 and R-8** (the unmet #105 text-widening deliverable; the open
   SENDER door). Both are lead/operator items; I confirm this wave touched neither.

---

## Files changed

| file | nature |
|---|---|
| `loremaster/loremaster/agent_existence.py` | **PRODUCTION** — one extraction (`format_unknown_agent_refusal`), byte-identical output; docstrings |
| `loremaster/loremaster/messages.py` | **PRODUCTION** — docstring only, zero executable lines |
| `loremaster/tests/test_enforced_relations.py` | F1 strengthening + 3 new F3 pins + docstrings |
| `loremaster/tests/_comms_fakes.py` | F3 — calls the shared formatter; `agent_name` threaded |
| `loremaster/tests/_message_fakes.py` | F3 — calls the shared formatter; first-wins-per-id; comment #5 corrected |
| `loremaster/tests/test_message_ledger.py` | F2 — two docstrings, no assertion touched |
| `REPORT-fixwave-04a.md` | this report |
