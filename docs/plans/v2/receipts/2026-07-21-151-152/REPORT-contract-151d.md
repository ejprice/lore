# REPORT-contract-151d — closing the cold audit's NO-GO by making the false clause TRUE

brief-base v5 read

## SUMMARY BLOCK
- **state:** done-with-deviations.
- **The contract extension is committed-ready and RED for the right reasons.** 2 exemption
  entries deleted, 8 new pins added, 0 committed pins touched. Real tree: **6 failed / 525
  passed** (531 = 523 baseline + 8 new). Reference build: **531 passed / 0 failed**.
- **deviations:** (1) I left a 8-line comment where the two exemption entries were, recording
  WHY they went — the brief said "deleted", not "deleted without trace"; repo law prefers a
  retired thing to be met deliberately. (2) `_bootstrap_labels()` (`:8819`) duplicates an
  inline expression inside the committed `_scout_query` pin (`:8180-8188`); consolidating it
  would mean editing a pin the brief forbids me to touch, so the duplication is FLAGGED, not
  fixed.
- **decisions-needed:**
  1. **`_txn.py:859-861` goes STALE the moment the builder lands the labels** and NO gate
     catches it — the driver's own docstring enumerates who passes a `label=` and the
     enumeration will omit the two new callers. This is the served-English class verbatim,
     created by this very fix. Production file, outside my writable set. Exact edit in §F1.
  2. **`test_retry_seam.py:6844`** (a committed #151 pin's failure MESSAGE) carries the same
     enumeration and goes stale the same way. It IS in my writable file but it IS a committed
     pin — brief item 4 forbids me. One-clause edit in §F2.
  3. Fork on how the two labels are pinned (property vs declared-constant) — §F3. I picked
     property, mirroring R4.
- **receipt POINTERS:** RED tails + failure reasons → §RED · wrong-build discrimination
  (6 builds) → §DISCRIMINATION · satisfiability + `loremaster.__file__` → §SATISFIABILITY ·
  gates → §GATES · flags/forks → §FLAGS · sweep → §SWEEP.

---

## §WHAT CHANGED (one file: `loremaster/tests/test_retry_seam.py`)

| # | change | anchor |
|---|---|---|
| 1 | **DELETED** `("scout.py", "_consume_live")` from `_ATTRIBUTED_BY_ANOTHER_MECHANISM` — the false clause dies with it | was `:7143` |
| 2 | **DELETED** `("scout.py", "_safe_kill")` from the same dict | was `:7152` |
| 3 | Note recording that both entries left deliberately and must not be re-added | `:7144-7152` |
| 4 | **NEW §10f** header — the audit's measurement, the ruling, the inherited url bound | `:8716-8749` |
| 5 | Two forever-conflicting fakes (`subscribe_live` / `kill`) | `:8752`, `:8771` |
| 6 | Three seam drivers + `_scout_seam_exhaustion_record` (clears caplog; IS the reach control) | `:8783-8817` |
| 7 | `_bootstrap_labels()` — the borrow-detector's set, read live from the seam module | `:8819` |
| 8 | `_UNCHAINED_CONTROL_LABEL` | `:8838` |
| 9 | **8 new pins** in `TestScoutsBestEffortSeamsAreAttributedByLabelOnly` | `:8841-9160` |

Only `execute_transaction` remains exempt. **Zero committed pins were weakened, rewritten or
restructured**; the diff is `+468 / -17` in one file, `git status` shows one modified file and
no git state touched.

### The eight new pins

| line | pin | verdict today |
|---|---|---|
| `:8850` | `_consume_live` exhaustion carries a label OF ITS OWN (+ not borrowed from bootstrap) | **RED** |
| `:8896` | `_consume_live` exhaustion carries the ENGINE'S OWN TEXT | **RED** |
| `:8931` | `_safe_kill` exhaustion carries a label OF ITS OWN (+ not borrowed) | **RED** |
| `:8968` | `_safe_kill` exhaustion carries the ENGINE'S OWN TEXT | **RED** |
| `:8990` | scout's THREE seams label their exhaustion THREE DIFFERENT WAYS (+ none borrowed) | **RED** |
| `:9060` | `_consume_live` carries NO url — **KNOWN BOUND**, RED the day someone threads one | green (disclosed non-discriminating today) |
| `:9100` | `_safe_kill` carries NO url — **KNOWN BOUND** | green (disclosed non-discriminating today) |
| `:9128` | **POSITIVE CONTROL**: a LABELLED call raising the signal BARE logs `engine_error == ""` | green |

The two url pins reproduce §10d's own disclosure verbatim: on the unfixed tree `url is None`
holds *for the wrong reason* (no label ⇒ no url either). They become real tripwires in the same
diff that turns the five RED pins green — which is exactly what §10d's pin did, and it is
recorded in each docstring rather than left for an auditor to discover.

---

## §RED — receipts, with counts and FAILURE REASONS

Committed baseline re-measured by me first (not relayed): **523 passed, 0 failed in 18.65s**.

```
cd /home/ejprice/PycharmProjects/lore/loremaster && uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q
...
FAILED tests/test_retry_seam.py::TestEveryCallIntoTheRetryDriverIsAttributable::test_every_call_into_the_driver_passes_a_label
FAILED ...TestScoutsBestEffortSeamsAreAttributedByLabelOnly::test_scouts_live_subscription_exhaustion_carries_a_label_OF_ITS_OWN
FAILED ...TestScoutsBestEffortSeamsAreAttributedByLabelOnly::test_scouts_live_subscription_exhaustion_carries_the_ENGINES_OWN_TEXT
FAILED ...TestScoutsBestEffortSeamsAreAttributedByLabelOnly::test_scouts_kill_exhaustion_carries_a_label_OF_ITS_OWN
FAILED ...TestScoutsBestEffortSeamsAreAttributedByLabelOnly::test_scouts_kill_exhaustion_carries_the_ENGINES_OWN_TEXT
FAILED ...TestScoutsBestEffortSeamsAreAttributedByLabelOnly::test_scouts_three_seams_label_their_exhaustion_THREE_DIFFERENT_WAYS
6 failed, 525 passed, 1 warning in 19.71s
```

531 collected = 523 committed + 8 new. **Each failure checked against its reason, not merely
its redness:**

**R1 — the deny-by-default gate, RED purely from the two deletions** (brief item 1, confirmed):
```
E  AssertionError: these calls into the retry driver pass no `label=`, so the driver
   suppresses `label`, `url` AND `engine_error` on their exhaustion record ...:
E      scout.py:571  in _consume_live()
E      scout.py:599  in _safe_kill()
E  assert not [('scout.py', 571, '_consume_live'), ('scout.py', 599, '_safe_kill')]
```
⚠ **The brief's line numbers were `:563`/`:591`; the real sites are `:571`/`:599`** (verified by
running the contract's own `_call_sites_in` scanner). Harmless — nothing keys on a lineno (the
allowlist keys on a COUNT, deliberately) — but the builder should use `:571`/`:599`.

**R2/R3 — the two label pins** (`label=None`, i.e. the driver suppressed all three extras):
```
E  AssertionError: scout's live-subscription seam exhausted and logged label=None. ...
   The traceback does not rescue it: the driver raises the exhaustion error BARE, so
   `__cause__` is `None` and the engine's text is nowhere ... Pass a canonical event name
   as `label=` at `scout.py:571`.
E  assert (False) +  where False = isinstance(None, str)
```
```
E  AssertionError: scout's kill seam exhausted and logged label=None. ... at `scout.py:599`.
E  assert (False) +  where False = isinstance(None, str)
```

**R4/R5 — the two engine-text pins** (`engine_error` present but EMPTY — the exact loss the
false clause denied):
```
E  AssertionError: scout's live-subscription seam exhausted and its record carries
   engine_error=''; the engine said 'Transaction conflict: Resource busy. This transaction
   can be retried'. ...
E  assert 'Transaction conflict: Resource busy. This transaction can be retried' in ''
```
(`_safe_kill`'s is identical in shape.)

**R6 — the distinctness pin**, which shows the whole defect in one line:
```
E  AssertionError: scout's three driver callers labelled their exhaustion
   {'_consume_live': None, '_safe_kill': None, '_scout_query': 'command_subscriber.query.rejected'}
   — the values must be PAIRWISE DISTINCT ...
E  assert 2 == 3
```

---

## §SATISFIABILITY — my own reference fix, in a provenance-asserted tree

I did **not** reuse a report's number. Scratch made with the blessed tool:

```
/home/ejprice/PycharmProjects/lore/scripts/scratch_copy.sh /tmp/lore-151d-ref   -> exit 0
scratch copy READY: /tmp/lore-151d-ref
  loremaster  -> /tmp/lore-151d-ref/loremaster/loremaster/__init__.py
```
**PROVENANCE RECEIPT, printed from inside the copy at run time:**
```
PROVENANCE loremaster.__file__ = /tmp/lore-151d-ref/loremaster/loremaster/__init__.py
```

Reference fix — two arguments, no other change:
```python
# scout.py:571 (_consume_live)
subscription = await retry_on_conflict(
    _attempt, label="command_subscriber.live_subscribe.rejected"
)
# scout.py:599 (_safe_kill)
await retry_on_conflict(_attempt, label="command_subscriber.kill.rejected")
```
(Those names are MY reference build's, not a requirement — the contract holds no opinion on
scout's naming vocabulary; see §F3.)

```
cd /tmp/lore-151d-ref/loremaster && uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q
531 passed, 1 warning in 19.36s
```
**531 passed / 0 failed. The full contract is satisfiable by the ruled fix.**

**The harder leg the C-DEF law demands — still satisfiable AFTER what the lint will ask for:**
```
cd /tmp/lore-151d-ref && uv run ruff check .      -> All checks passed!   (exit 0)
cd /tmp/lore-151d-ref && ./scripts/typecheck.sh   -> exit 1, 55 errors
   grep 'scout.py|test_retry_seam' -> NONE in scout.py / test_retry_seam.py
```
The 55 are the unrelated packet-03 comms baseline, unchanged in count and in files. No import
becomes orphaned, no signature changes, so the lint demands no cleanup at all.

**Collateral check (not asked for, done anyway):** scout's own suite against the reference fix
— `uv run pytest tests/test_scout.py -q` → **33 passed**. Adding the labels breaks nothing in
scout's own contract.

---

## §DISCRIMINATION — six wrong builds, all against the REFERENCE build in the scratch copy

Interrogating every fixture with *"what WRONG build still passes this?"*. Each mutation was
asserted non-no-op before running (a no-op mutation is a blind probe). Node set = the new
class + §10's gate class + §10d's `_scout_query` class (17 tests).

| build | what it is | result |
|---|---|---|
| **REF** | the ruled fix | **17 passed** (control: the probe can see a correct build) |
| **W1** | `_consume_live` labelled, `_safe_kill` NOT — the likeliest wrong build (16 lines apart) | **3 failed**: both `_safe_kill` pins + the §10 gate |
| **W2** | ONE shared scout label on both | **1 failed**: the distinctness pin |
| **W3** | both BORROW `_scout_query`'s label | **1 failed**: the distinctness pin |
| **W4** | two DIFFERENT *bootstrap* labels (pairwise-distinct, so only the borrow legs may fire) | **3 failed**: both label pins' borrow legs + the distinctness pin's borrow leg |
| **W5** | labelled, but the signal raised BARE (`from error` dropped) — engine text lost | **2 failed**: both engine-text pins; **label pins stay GREEN** |
| **W6** | a url threaded through both | **2 failed**: both KNOWN-BOUND url pins |

Restored byte-exact after the sweep: `md5sum scout.py` = `5246f7aca2cac92ceb0dae7613916c08`,
identical to the pre-mutation reference.

**What this proves, item by item against the brief's three demands:**
1. *"labels DISTINCT from each other, from `_scout_query`'s and from bootstrap's"* — W2, W3 and
   W4 are three different ways to violate that and each is caught. **The distinctness pin is
   load-bearing, not redundant:** W2 and W3 are invisible to every per-seam pin (a shared label
   is still a non-empty, non-bootstrap string) and ONLY the three-observations-compared-to-each-
   other pin sees them.
2. *"the engine-text pin must FAIL on an empty string"* — W5 is that build, driven live: labels
   land, `engine_error` is `""`, label pins green, engine-text pins RED. The `:9128` control
   independently demonstrates the driver's `""` fallback firing on a labelled call, so the
   containment assertions have been *shown able to fail* rather than merely asserted.
3. *"a build that labels one but not the other must go RED on the unlabelled one"* — W1, and it
   reds exactly the two `_safe_kill` pins plus §10's gate, leaving `_consume_live`'s green.

**Reach control (the vacuity door):** `_scout_seam_exhaustion_record` clears caplog and routes
through `_exhaustion_record`, which fails loudly on ZERO records. No pin in §10f can go
vacuously green by failing to drive its seam. The two label pins additionally assert
`connection.calls > 1`, so a fixture that "exhausted" without ever RETRYING is caught rather
than graded.

---

## §GATES (output captured, exit code checked, count asserted before interpreting)

⚠ **The CWD trap fired on me once** (a `cd <repo-root>` for ruff persisted into the next call;
`pytest tests/...` then exited *"no tests ran in 0.00s"* behind a tail). It was caught **because
I asserted a passed-COUNT** rather than reading the absence of "FAILED". Every run below uses an
absolute `cd` in the same command.

| gate | result |
|---|---|
| `cd .../loremaster && uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q` | **6 failed, 525 passed** (531 collected; 523 baseline + 8 new) — the intended RED |
| `cd .../lore && uv run ruff check .` | **All checks passed!**, exit 0 |
| `cd .../lore && ./scripts/typecheck.sh` | **exit 1, 55 errors in 5 files** — matches the brief's baseline exactly; **zero in `test_retry_seam.py`** (grep receipt) |

Pre-existing wart, unchanged and not mine: `RuntimeWarning: coroutine '_empty_subscription' was
never awaited` at `test_retry_seam.py:3156` (the cold audit flagged it as residual 4).

---

## §FLAGS — things I noticed and may not fix (operator owns these)

### F1 — ⚠ BLOCKING-ADJACENT: `_txn.py:859-861` goes STALE when the builder lands the labels, and no gate catches it
The driver's own `label:` docstring reads:
> *"Every other caller — the ten single-statement seams, the three session-bootstrap
> statements, and **scout's query seam** — passes its own `label`."*

After the fix that enumeration omits `_consume_live` and `_safe_kill`. **Measured: the reference
build scores 531/0 with the sentence untouched** — nothing in the repository can see it. This is
the served-English class *created by this fix*, in the same function #151 is about, which is
precisely the shape §10e exists for. It escapes §10e because `_prose_liars` audits claims that a
caller is label-LESS; this is an incomplete enumeration of label-PASSERS, the dual.

`_txn.py` is production and outside my writable set. **Exact edit for the builder, same diff:**
> `scout's query seam — passes its own ``label``.`
> → `scout's query seam, and scout's two best-effort seams — passes its own ``label``.`

(I verified the literal `bootstrap_session` is NOT a substring of the docstring, so
`_prose_liars` and `_DOCUMENTED_SELF_ATTRIBUTING` are unaffected by the fix either way.)

**Should this get an INSTRUMENT rather than an edit?** That is the honest question given *"a
diagnosis is not an instrument"*. A derived pin is available — assert
`{unlabelled driver callers} == {callers the driver's prose accounts for}` — but it is a NEW
invariant, not one of the four things my brief authorises, and it changes what §10e means.
**Recommendation: builder makes the edit now; lead decides separately whether the enumeration
deserves its own derived pin.** I did not build it.

### F2 — the same enumeration, inside a committed pin's failure message
`test_retry_seam.py:6844` reads *"it cannot be attributed to ANY of the possible emitters (the
ten `_query` seams, scout's query seam, the session bootstrap)"*. Post-fix there are two more
possible emitters. It is a diagnostic HINT, not a promise of a check — so it is **not** a false
gate — but it is the same class. It is in my writable FILE yet it is a committed #151 pin, which
brief item 4 forbids me to touch, so I flagged it. **Exact edit:** insert
`scout's two best-effort seams, ` before `the session bootstrap`.

### F3 — FORK (recorded per brief; I picked one and say which)
*"each … carries ITS OWN distinct label"* admits two readings that produce different tests:
- **(i) PROPERTY-based** — non-empty string, not borrowed, pairwise distinct. **This is what I
  built.** It mirrors `TestScoutsQuerySeamIsAttributedByLabelOnly` (which the brief told me to
  mirror) and inherits its stated reason: scout's own events are `command_subscriber.*`, not
  `scout.*`, so any vocabulary pin is a **C-DEF trap** for a builder doing the right thing.
- **(ii) DECLARED-CONSTANT** — a `{seam: exact label}` map in the contract, asserted for equality,
  as `_SEAM_REJECTION_EVENTS` does for the ten `_query` seams at `:6852`. Stronger (it pins the
  exact operator-greppable string) but it forces the builder to guess my two names or edit a
  contract it may not edit — the C-DEF class the repo just spent a wave on.
**I would pick (i)**, and did. If the operator wants the exact strings pinned, that is a
one-function change to §10f and I should make it rather than the builder.

### F4 — deviation: the deleted entries left a note, not a hole
I replaced the two allowlist entries with an 8-line comment naming what was there, why it went,
and that it must not be re-added. The brief said "the false clause is DELETED"; a silent deletion
is also a valid reading. I chose the note under repo law (*a bound the next engineer meets
deliberately*; the store reference keeps a retired ban struck rather than deleted for the same
reason). Trivial to strip if the lead disagrees.

### F5 — deviation: one duplicated expression I was not allowed to consolidate
`_bootstrap_labels()` (`:8819`) is the same set-building expression as the inline one inside the
committed `_scout_query` label pin (`:8180-8188`). By the ONE-IMPLEMENTATION law that second
copy should not exist — but consolidating means editing a committed pin, which brief item 4
forbids. **Flagged, not fixed.** The correct follow-up is one edit: point `:8188` at
`_bootstrap_labels()`. It is a derived-constant lookup rather than a POLICY, so the divergence
risk is low; I am raising it because the law says escalate rather than quietly write copy #2.

### F6 — the `_safe_kill` exemption's evidence was NOT false, and it still went
The cold audit found only `_consume_live`'s clause false; `_safe_kill`'s wording was correctly
framed. The operator ruling is explicit that **both** paths leave the allowlist, so I deleted
both. Recording it so nobody later reads the deletion as an accusation against `_safe_kill`'s
evidence: it left because the ruling made the exemption unnecessary, not because it lied.

### F7 — pre-existing, not mine
The `_empty_subscription` `RuntimeWarning` at `:3156` (cold audit residual 4). Untouched.

---

## §SWEEP — bare, anchor-free, per repo law (every hit gets an individual verdict)

`grep -rn "rides the traceback"` across `*.py` + `*.md`:

| hit | verdict |
|---|---|
| `REPORT-audit-151-cold.md:12,136,164,191` | the audit report quoting the defect — **correct, leave** |
| `test_retry_seam.py:8901` | **my new §10f pin**, quoting the retired clause to say it was false — **intended** |
| *(the live clause at the old `:7147`)* | **DELETED** — no surviving instance in any production or test file |

`grep -rn "568-569\|593-594"` across `*.py` → **NONE**. The audit's residual 2 (the stale line
cite inside the retired evidence) is closed by deletion rather than correction.

`grep -n "exc_info" scout.py` → `:485`, `:498`, `:577`. **None of the three claims anything about
what the traceback carries** — the false clause lived only in the contract, not in scout. Verdicts:
`:485` connect_failed (fine), `:498` socket_dropped (fine), `:577` live_unavailable (fine — it
logs a traceback, and after the fix the driver record carries the engine text separately).

`grep -rn "scout's query seam"` → the two prose sites in **§F1** and **§F2** (flagged above), plus
`test_retry_seam.py:8133/8140/8172/8189/8230/8231`, all inside §10d's own fixtures and messages
about `_scout_query` specifically — **correct, leave**; plus two hits in `REPORT-contract-151b.md`,
a historical report — **leave**.

**Tool honesty (§4):** I used lore for `lore_findings get 151` only. Every structural question
here — enumerating driver call sites, the retired-clause sweep, the prose enumerations — was
answered with the contract's own AST scanner or with bare grep, because all three are the
grep-honest cases: exhaustiveness where one missed site matters, and non-symbol textual seams
(prose inside string literals). Saying so out loud as the protocol requires; no lore weakness was
routed around, so nothing to file.

---

## §HOUSEKEEPING
- **Writable set respected exactly.** `git status --porcelain` → `M loremaster/tests/test_retry_seam.py`
  and this report. Nothing under `loremaster/loremaster/`, nothing in `test_surreal_harness.py`,
  `docs/`, `pyproject.toml` or `.claude/`. **No git state staged, committed or reverted.**
- **No worktree created** (standing directive). The scratch copy is a plain directory outside the
  repo: **`/tmp/lore-151d-ref`** — it holds my reference fix (labels applied) and is left in
  place so the lead or builder can re-run the satisfiability leg without rebuilding it. Delete
  with `rm -rf /tmp/lore-151d-ref` when done. Other scratch: `/tmp/151d_mutate.py`,
  `/tmp/151d_scout_ref.py`, `/tmp/151d_typecheck.txt`, `/tmp/151d_ref_typecheck.txt`.
- **Test store:** none of this needed a store. No connection to `:18000` or `:18500` was opened;
  every fixture is an in-process fake.
- I did **not** file a lore finding (no ledger row named as mine).

## VERDICT
The contract extension is **RED for the right reasons on the current tree and 0-failed against
the ruled fix**, with every discrimination axis the brief named proven by mutation rather than
argued. **The one thing the lead must act on before the builder starts is §F1** — the ruled fix
plants a fresh served-English staleness in `_txn.py`, in the exact function #151 is about, and no
gate in this repository can see it.
