# REPORT-adversary-pkt42-1-rerun — CONTRACT ADVERSARY, packet 42, SECOND PASS

brief-base v7 read

Grades revision 3 of the contract at **`720e26a`**. Supersedes nothing in
`REPORT-adversary-pkt42-1.md` (round 1), which stands as the record of the first pass and is
cited here.

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT** — one new BLOCKER, one new C-DEF trap, two honesty defects. **Round 1's four findings are all genuinely closed.**
- **P1 headline — the two round-1 survivors are DEAD, but a NEW wrong build survives.** MP1's build now scores **5 RED**, MP2's **13 RED** (8 recursion-specific), W3 **76 RED**, W-DEL **16 RED**. The new survivor: **W-R10a — R10's fix applied to the INJECTED client arm only, leaving the OWNED `httpx.AsyncClient` completely unauthenticated.** It produces a **byte-identical failure set to the correct build** (`diff` empty). Every production construction of the Anthropic counter uses the **owned** arm (`calibration/engine.py:686`, `scripts/calibration_baseline.py:149`); the contract's only wire pin injects a client. **This is the #107 shape: green everywhere, 100% broken in production.**
- **Frontier 1 answered — R10's fix is REAL, not cosmetic.** `vars(counter)`, `repr(counter)`, `repr(client)`, `repr(request)`, httpx exception strings and tracebacks are all clean. **But it is not the whole story:** the bytes relocate into `httpx.Headers`, and httpx obfuscates **only** `authorization`/`proxy-authorization` — **not `x-api-key`**. R10's own rationale ("bake it in exactly as `tei.py` does") cites a precedent whose residual protection **does not transfer**.
- **Frontier 2 — the KNOWN BOUND's TRIGGER is real and specific; its JUSTIFICATION is now false.** *"the source fix removes the only object in the tree that held a labelled credential as a bare `str`"* — after R10, `httpx.Headers` holds exactly that and renders it.
- **Frontier 3 — the injected-client pin is sound.** Measured: shape A (mutate `.headers`) passes, shape B (per-request) passes, bare-dict retention fails. It admits both right answers and rejects the wrong one. Shape B is additionally immune to W-R10a.
- **R17's re-derivation VERIFIED independently** — "1 of 5 sites wrong" genuinely does **not** reproduce; all 5 are username round-trips, all 5 password siblings stay wrapped. The author's `snapshot_gc.py` caveat is a real independent find. **But R17 creates a new C-DEF trap** (below).
- **R18 verified structurally:** 337 collected, **0 collection errors**, 103 runtime reds. Base RED **103 failed / 234 passed** — **exact** match to §10.1.
- **R16:** the `Basic` pin *is* named as the mutation proof (§0.8). Nothing mechanically enforces the commit boundary — but W-DEL = 16 RED means a split commit has a red suite, which is adequate enforcement. Reported, not a defect.
- **MISSING PINS:** MP5 (owned-arm wire pin, BLOCKER) · MP6 (§9 rows for 3 of 5 R17 sites, C-DEF) · MP7 (the bound's rationale) · MP8 (the `x-api-key`-vs-`authorization` asymmetry, note or pin).
- **Packages considered:** `httpx` 0.28.1 → **keep_with_trigger** (read `inspect.getsource(httpx.Headers.__repr__)` → `_obfuscate_sensitive_headers`; measured 5 header names; trigger: **the day a lore client authenticates with a header httpx does not obfuscate**, which is TODAY for `x-api-key`). No mechanism built by me beyond scratch probes.
- **Receipt pointers:** §P1 (5 wrong builds) · §P1b (quantifier table) · §F1–F4 (frontier answers) · §P4 (reproduced claims) · §Residuals.

All measurements **2026-07-26**, worktree `lore-pkt42` at **`720e26a`**, in a `scratch_copy.sh` tree.
`loremaster.__file__ = /tmp/…/scratchpad/adversary-pkt42/ref/loremaster/loremaster/__init__.py`
(printed live). **The repo was never edited** — `git diff` over all production trees is empty.

---

## P0 — CONTROLS

Scratch survives from round 1; `logging_setup.BASE.py` md5 `831ca42e782e9ee9b4533dc750166ccc`
still matches `720e26a`'s pristine file, so the four round-1 wrong builds are re-usable **and
still differ from base only where I intended**. All four production files I had mutated in round 1
were restored from the worktree before this pass, verified by `git status` in the scratch tree
(empty over production trees).

**Every mutation asserts its own landing** — `assert old in t, "…TARGET ABSENT"` — after round 1's
`\x01\x02` heredoc incident. Two mutations this pass printed `TARGET ABSENT` guards that held.
Each wrong build also carries a **sanity line** proving the intended behaviour changed:

```
W-R10a LANDED: owned client is UNAUTHENTICATED
SANITY owned-arm    x-api-key present: False   <- production would 401
SANITY injected-arm x-api-key present: True
```

**The scratch-path artifact from round 1 recurs and is again excluded**: my scratch path contains
a 30-char high-entropy run, so `test_ordinary_traceback_text_is_not_mangled` reddens in scratch
only. Scratch base = 104 RED; **real worktree base = 103 RED**, matching §10.1 exactly. Every count
below that I attribute to the contract was taken in the tree where it is not confounded.

---

## P1 — WRONG BUILDS

### ✅ Round 1's two survivors are dead

| build (unchanged since round 1) | at `506e595` | at `720e26a` | killed by |
|---|---|---|---|
| **MP1 leak build** (deletion + R8, no source fix) | **204 passed / 0 failed** | **5 failed** | `TestNoProductionObjectRetainsAnUnwrappedCredential` ×5 |
| **MP2 recursion build** (`_scrub_value` returns containers) | **204 passed / 0 failed** | **13 failed** | 5 source pins + `TestScrubValueRecursesIntoContainers` ×8 |
| W3 (inlined catch-all, no names) | 72 failed | **76 failed** | behavioural pins |
| W-DEL (deletion, no R8) | 11 failed | **16 failed** | R8 pins |

**On the author's claimed numbers (4 and 8):** both are *attributions*, and both are correct. MP2's
8 is exactly the recursion-specific set; the other 5 are the shared source pins that fail on any
build lacking R10. MP1's claimed 4 vs my 5 differs only by
`test_an_injected_client_is_still_authenticated`, which is red on every pre-R10 build. **Neither
is an over-claim** — the direction is under-claiming, which is the safe one.

**Satisfiability, independently rebuilt:** my own R10 source fix + R8 shape scores
**221 passed / 0 failed** on `test_secret_leak_vectors.py` + `test_logging_setup.py`.

### 🔴 BLOCKER F3 (NEW) — W-R10a: the owned client left unauthenticated, indistinguishable from correct

R10 says *"bake the headers into the `httpx` client at construction"*. `AsyncClaudeTokenCounter`
has **two arms** — owned (`client is None`) and injected. A builder who honours the header on the
**injected** arm only produces this:

```
SANITY owned-arm    x-api-key present: False   <- production would 401
SANITY injected-arm x-api-key present: True
```

Against the full contract:

```
### W-R10a vs the FULL contract ###
3 failed, 243 passed in 5.25s
```

…and all 3 are pre-existing base reds in `test_secret_typing.py` (the unbuilt loresigil seam). The
decisive measurement is the **failure-set diff against the correct build**:

```
=== DIFF: R10-GOOD vs W-R10a — is the wrong build DISTINGUISHABLE at all? ===
>>> IDENTICAL FAILURE SETS — the unauthenticated build is INDISTINGUISHABLE from correct <<<
```

**Why nothing sees it.** The only wire pin is
`test_the_credential_still_reaches_the_wire`, which *must* inject a client to use
`MockTransport` — so it exercises the injected arm exclusively. There is no `client=None` wire
assertion anywhere in the contract (`grep -n "client=None\|_owns_client\|owned"` on
`test_secret_leak_vectors.py` returns nothing).

**Why it matters — the production path is exclusively the unpinned arm:**

```
loremaster/loremaster/calibration/engine.py:686:  AsyncClaudeTokenCounter(self._api_key, model=self._model)
scripts/calibration_baseline.py:149:              AsyncClaudeTokenCounter(api_key, model=model)
scripts/token_survey.py:865:                      ClaudeTokenCounter(api_key, model=model, client=self._client, …)
```

`engine.py:686` is reached from `server.py`'s `CalibrationEngine` construction. Neither production
site passes a client. **Every calibration call in production would 401, with a full green suite.**

This is precisely the class this repo's CLAUDE.md names first: *"the fixture guarantees the one
condition under which the bug is invisible"* — here the fixture guarantees an injected client,
and production guarantees the opposite.

**MP5 — the test that should exist:** `test_the_owned_client_is_also_authenticated` — construct
with `client=None`, swap the transport (`counter._client._transport = httpx.MockTransport(...)` —
the technique the contract already uses in loresigil's `_config_for`), fire a real `count()`, and
assert the `x-api-key` header arrives with equality. **The defect it catches:** a source fix that
authenticates only the arm the tests inject.
*(Note: R10's shape B — per-request headers — is structurally immune, because it has no
owned/injected branch. That is an argument for shape B, and the contract could say so.)*

---

## P1b — QUANTIFIER TABLE (mandatory)

| # | invariant | ∀-over-inputs / GUARDED | receipt |
|---|---|---|---|
| I1 | A `SecretStr` credential never reaches a rendered log line | ∀ over 7×3×2, **now + the real production object** (R10 pins) | ✅ round-1 door (header map) CLOSED — MP1 build 5 RED |
| I2 | No production object retains an unwrapped credential (R10) | **GUARDED — ∀ over the two counter classes, but the wire leg is ∀ over the INJECTED arm only** | 🔴 door-build **W-R10a** survives: owned arm unauthenticated, **identical failure set to correct** → **MP5** |
| I3 | `_scrub_value` recurses through containers (R11/A19) | ∀ over dict/list/tuple/dict-in-list/list-in-dict + end-to-end ×2 formats | ✅ MP2 build 8 RED on this class alone |
| I4 | An unlabelled credential in free text is NOT redacted (A18 bound) | ∀ over the matrix | ✅ killed W3 (76 RED) |
| I5 | The **structured** form remains un-redacted (new KNOWN BOUND) | ∀ (single shape), trigger stated | ⚠ trigger real and specific; **justification false** → **MP7** |
| I6 | Labelled patterns still redact, label+separator preserved | ∀ label × separator (28 forced) | ✅ caught my own Trap-2 draft in round 1 |
| I7 | R8: known scheme preserved, credential always gone | ∀ over known + unknown schemes | ✅ killed W-DEL (16 RED) |
| I8 | Scrubbing is idempotent | ∀, with a "redaction happened" guard | ✅ green on REF |
| I9 | All three consumers route through one `_scrub_text` | ∀ over 3, mutation-proven | ✅ reproduced |
| I10 | The entropy machinery is gone (retired symbols) | **GUARDED** — keyed on NAMES | ✅ door-build W3 (behaviour, no names) killed by *behavioural* pins, 76 RED |
| I11 | No traceback formatter renders frame locals (M4) | ∀ legs + `rich show_locals=True` positive control | ✅ not broken |
| I12 | Every unwrap site is allowlisted | **GUARDED** — keyed on the CALL spelling | ⚠ round-1 residuals R1/R2 now named in the docstring (verified); bound-method alias + laundering helper closed as prose. Accepted under the stated threat model. |
| I13 | No username round-trip survives (R17) | **GUARDED** — a **prefix NAME LIST** of 5 files | ⚠ the strong leg is the **retirement of the `NOT_A_SECRET` category** (structural, ∀); the prefix list is the weak leg. A 6th-site round-trip would need to be mis-categorised, which nothing detects. Residual, not a blocker. |
| I14 | Only `loremaster/config.py` reads env for a secret | ∀ over AST env reads, both ways | ✅ fires — and **traps the R17 migration** → **MP6** |
| I15 | No server-path call site passes an `env_file` (R3) | ∀, both spellings, both directions | ✅ reproduced in round 1 |
| I16 | A resolved secret is byte-exact from either source (R1/R12) | ∀ over source **and** over quoting form incl. unset-var | ✅ round-1 MP3 closed by `interpolate=False` |
| I17 | Every backend puts the real credential bytes on the wire | ∀ 3 arms, real requests, equality | RED at base as designed; not attacked |
| I18 | Every pin has a runtime red, never a type-gate red (R18) | ∀ over the suite | ✅ 337 collected, **0 collection errors**, 103 runtime reds |
| I19 | Deletion + labelled-pattern fix ship in ONE commit (R16) | **GUARDED** — no mechanical commit check | ✅ acceptable: a split commit is a **red tree** (W-DEL = 16 RED), so bisect/revert land on visible red. Named in §0.8. |

---

## FRONTIER ANSWERS

### F1 — Does R10's source fix close MP1, or relocate it? **It closes it. But the analogy in its rationale is weaker than it reads.**

Measured on the R10 build:

```
=== FRONTIER 1: where did the bytes GO? ===
  vars(counter)                  LEAK=False  {'_model': …, '_client': <httpx.AsyncC…
  repr(counter)                  LEAK=False  <loremaster.calibration.counting.AsyncClaudeTokenCounter object at …>
  repr(counter._client)          LEAK=False  <httpx.AsyncClient object at …>
  repr(client.headers)           LEAK=True   Headers({'accept': …, 'x-api-key': 'sk-ant-…
  vars(client) [deep]            LEAK=True   {'_base_url': …, '_headers': Headers({…
  client.headers['x-api-key']    LEAK=True   'sk-ant-api03-…'
```

The **six paths round 1 measured are all closed**, and so are the httpx paths that matter most:

```
  repr(request)            LEAK= False
  ConnectError str         LEAK= False
  ConnectError traceback   LEAK= False
```

So the fix is **real**, not cosmetic. **But** — reading `httpx.Headers.__repr__` source rather than
assuming:

```
  authorization          repr LEAK=False  -> Headers({'authorization': '[secure]'})
  proxy-authorization    repr LEAK=False  -> Headers({'proxy-authorization': '[secure]'})
  x-api-key              repr LEAK=True   -> Headers({'x-api-key': 'sk-ant-api03-…'})
  api-key                repr LEAK=True
  cookie                 repr LEAK=True
```

httpx's `_obfuscate_sensitive_headers` protects exactly `authorization` and
`proxy-authorization`. **R10's instruction is "bake it into the client exactly as `loresigil/tei.py`
already does" — but `tei.py` uses `Authorization`, which httpx protects, and `counting.py` uses
`x-api-key`, which it does not.** The precedent's residual safety does not transfer. The remaining
exposure needs a developer to reach explicitly into `client.headers` (e.g. a retry log
`extra={"headers": dict(self._client.headers)}`), which is a narrower door than `vars(counter)` —
so I do **not** call this a blocker. **MP8:** say it in the bound's docstring, or pin
`repr(client.headers)` too.

### F2 — Is the KNOWN BOUND honestly stated, and is the trigger real?

**Trigger: real, specific, and actionable** — *"the day a new `UNWRAP_ALLOWLIST` entry is added
with category `AUTH_HEADER` that stores rather than sends"*. That is checkable and names the fix
direction ("fix the SOURCE again; do not widen the pattern"). Good.

**Justification: now false.** The pin says:

> *"WHY IT IS ACCEPTABLE: the source fix removes the only object in the tree that held a labelled
> credential as a bare `str`. What remains is a shape no production code now produces."*

After R10, `httpx.Headers` inside the client holds `{'x-api-key': '<raw>'}` and renders it (F1).
A labelled credential as a bare `str` inside a container **still exists in the tree** — it moved
into a dependency. This is the *"a failure message that promises a check the assertion does not
perform"* class, one level up: **a bound whose rationale is stronger than the facts.** The bound
itself is correct and worth keeping. **MP7:** correct the sentence.

### F3 — Does the injected-client property pin admit both shapes and reject the wrong one? **Yes, all three.**

| shape | `vars(counter)` | R10 pins |
|---|---|---|
| A — mutate injected `.headers` (my R10 build) | no credential | **8 passed** |
| B — per-request headers, `SecretStr` retained (`_api_key: SecretStr('**********')`) | masked by type | **7 passed / 1 failed**, and the 1 is `token_survey` (left at base in that run), not shape B |
| WRONG — retain the bare dict (round-1 build) | credential present | **fails** `test_an_injected_client_is_still_authenticated` + 4 more |

The pin is not "loose enough for a wrong one". Confirmed.

### F4 — What wrong build does the smaller allowlist admit?

**The shrink TIGHTENS, it does not loosen** — retiring `NOT_A_SECRET` means a re-introduced
username round-trip has *no category to claim*, and `test_every_entry_uses_a_category_from_the_closed_set`
plus `test_the_category_set_is_closed` make inventing one a visible act. That is the strong,
structural leg.

`test_no_username_round_trip_survives` itself is a **prefix name list** of five files — the shape
this repo has six receipts against. A round-trip re-introduced at a *sixth* site, mis-labelled
`AUTH_HEADER`, passes it. But it would have to lie about the category, and the category set is
closed, so I rate this a **residual, not a blocker**. `test_the_surviving_entries_are_all_real_credential_unwraps`
sensibly uses a bound (`4 <= len <= 7`) rather than an exact count, and says why.

### 🟠 MP6 (NEW, C-DEF) — R17 mandates a de-wrap that a sibling gate forbids, and 3 of 5 sites have no §9 row

R17 retires the five username round-trips: *"a non-secret config read is a plain read and never
reaches this list."* I built the plain read:

```
R17 de-wrap LANDED at scout.py::from_config (plain env read)
FAILED …TestSecretResolutionHasExactlyOneEntryPoint::test_every_environment_read_is_the_entry_point_or_allowlisted
E   assert not ['…', 'loremaster/scout.py::from_config', …]
```

`ENV_READ_ALLOWLIST` permits env reads only inside `loremaster/config.py` and at named
operational-knob sites. So the obvious implementation of R17 reddens, `ENV_READ_ALLOWLIST` lives in
a **contract file the builder may not edit**, and **§9 has rows for `snapshot_gc.py` and
`search_score_survey.py` but none for `index/cli.py`, `scout.py`, or `server.py`** — three of the
five sites R17 governs.

The resolution is presumably a non-secret reader **in `config.py`** (exempt by prefix), but the
contract neither names nor pins one. R13's own words are that §9 exists *"so the builder is
authorised rather than trapped (C-DEF)"*. **MP6:** add the three rows and name the replacement
read's home.

---

## P4 — CLAIMS REPRODUCED

| claim | verdict |
|---|---|
| Base RED **103 failed / 234 passed**, 337 tests | ✅ **EXACT** in the real worktree. (Scratch shows 104 — the known hashy-path artifact, excluded.) |
| MP1 build now 4 failed / MP2 build now 8 failed | ✅ **CONFIRMED as attributions.** Totals 5 and 13; the deltas are shared source pins. Under-claims, not over-claims. |
| R17: *"1 of 5 sites wrong"* does **not** reproduce | ✅ **INDEPENDENTLY CONFIRMED.** My own derivation found 4 via `config.surreal.user_env` and the 5th (`search_score_survey.py:696`) via `DEFAULT_SURREAL_USER_ENV`. All five are username round-trips; **all five password siblings stay wrapped** (`:113 :6753 :729 :697 :333`, none calls `get_secret_value`). A rider claim falsified, correctly. |
| R17's `snapshot_gc.py` caveat (its `KeyError` is the only one CAUGHT) | ✅ real, and a genuinely sharp independent find — it is the grain of truth in the rider. |
| R18 — every pin has a runtime red | ✅ **337 collected, 0 collection errors, 103 runtime reds.** No pin is demonstrated by mypy. |
| R16 — the `Basic` pin named as the same-commit mutation proof | ✅ named at §0.8. Nothing *mechanically* checks the commit boundary, but a split commit is a red tree (W-DEL = 16 RED), so the rider is enforced in effect. |
| R14 — `probe_embed` migration reversed, stdlib-only pin + ledgered duplicate | ✅ `ENV_READ_ALLOWLIST` carries the ledgered entry with the re-open trigger, exactly as ruled. |
| Round-1 residuals R1/R2/R6/R9 closed as one-liners | ✅ verified present. |
| Round-1 residual R11 (prose blocklist) kept over my objection | ✅ **correct call, and I was wrong to leave it open** — it fired on my own REF build in round 1 (`['high-entropy token']`) and again this pass. |

---

## RESIDUALS — individual verdicts

| # | item | verdict |
|---|---|---|
| S1 | `httpx` protects `authorization` but not `x-api-key` in `Headers.__repr__` | **ESCALATE as MP8** — a note in the bound, or a pin on `repr(client.headers)`. Not a blocker; the door needs deliberate reaching. |
| S2 | `test_no_username_round_trip_survives` is a 5-file prefix list | **RESIDUAL.** The category retirement is the real guard; the list is belt-and-braces. Acceptable. |
| S3 | R16 has no mechanical commit-boundary check | **ACCEPTABLE, say so plainly.** Enforcement is that a split commit is red. Recommend one sentence in §0.8 stating that, so the rider is not read as unmeasured. |
| S4 | Shape B (per-request headers) is immune to W-R10a; shape A is not | **FLAG.** The contract presents the fork as symmetric. It is not, on this axis. Worth one line once MP5 exists. |
| S5 | `test_the_surviving_entries_are_all_real_credential_unwraps` bound is `4 <= len <= 7` while R17 ruled exactly 6 | **ACCEPTABLE** — the author states the reasoning (a justified addition should be possible, doubling should not). |
| S6 | Round-1 residual R12 (`Bearer <k>'}` eats the closing quote) | **STILL OPEN, still out of scope** — the operator explicitly declined to action it. Re-raised so it is not lost. |
| S7 | Worktree is deliberately not merged forward from `6a21fb6` (primary at `48537c3` carries 26 RED) | **NOTED, agree.** Merging would make every gate reading ambiguous. Merge at close-out. |
| S8 | I ran `pytest` in the graded worktree twice (read-only) | **DISCLOSED.** `git diff` over all production trees empty; only the author's own files appear in `git status`. |

---

## VERDICT

# CONTRACT INSUFFICIENT

**The revision is a big, genuine improvement.** Every round-1 finding is closed, and closed
properly: MP1 and MP2's builds are dead, MP3's `interpolate=False` is pinned over every quoting
form, MP4's §9 row is corrected, and R14 reversed a ruling on evidence rather than defending it.
The new `TestNoProductionObjectRetainsAnUnwrappedCredential` includes the leg that matters most —
*"the leg without which R10 is satisfied by breaking authentication"* — which is exactly the right
instinct. R17's re-derivation falsified an inherited claim and found a real caveat nobody had.
I could not break R8, R11, R12, the retired-symbol surface, or the injected-client property pin.

It is INSUFFICIENT because that right instinct stopped one step short. The contract asked *"is the
credential still on the wire?"* and answered it **for the arm the test injects** — while every
production caller uses the other arm. A build that leaves production 100% unauthenticated is
**byte-identically indistinguishable** from the correct one. That is the same shape as round 1's
finding in a new place: an invariant quantified over the inputs someone enumerated rather than over
the inputs production supplies.

MP5 is the blocker and is a small pin to write. MP6 is a C-DEF trap that costs a builder a
red-test detour. MP7 and MP8 are honesty corrections — the bound and its rationale are load-bearing
documents, and one sentence in each is now false.
