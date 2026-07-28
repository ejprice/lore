# REPORT-adversary-pkt42-1-rerun2 — CONTRACT ADVERSARY, packet 42, THIRD PASS

brief-base v7 read

Grades revision 4 of the contract at **`abd86c3`**. Prior passes:
`REPORT-adversary-pkt42-1.md` (round 1) and `REPORT-adversary-pkt42-1-rerun.md` (round 2), both
cited and neither superseded.

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT** — 1 missing wire pin, 2 live C-DEF traps in §9, 2 residuals. **Every round-2 finding's PIN half is closed and verified; two of the SCOPE-LIST halves are not.**
- **P1 headline — the round-2 blocker is dead, a narrower sibling survives.** W-R10a (owned arm unauthenticated) → **2 RED**, killed by `test_the_OWNED_client_arm_is_authenticated`. W-SHAPEA (client-level headers, both arms) → **2 RED**, killed by `test_no_credential_is_baked_into_either_CLIENT`. The mandate is enforced in **both** directions. **But `W-SYNCWIRE` — the SYNC twin `ClaudeTokenCounter` posting with no auth header — scores 0 failures against the contract** (measured `[None]` on the wire vs `['sk-ant-SYNCKEY']` on the correct build). Both wire pins are on the **async** class only.
- **🔴 MP9 — §9's R10 row is STALE and contradicts R19.** It still reads *"bake it into the `httpx` client as `loresigil/tei.py` does … **either shape passes**"*. Measured **false**: that build is W-SHAPEA, **2 RED**. A builder following §9 verbatim writes the shape R19 forbids. This is the served-English-contradicting-code class, inside the scope list whose whole job is to stop it.
- **🟠 MP11 — MP6 is only half-fixed.** R21 added the three §9 rows (good), but their instruction — *"→ a plain env read"* — still reddens `test_every_environment_read_is_the_entry_point_or_allowlisted` (**2 RED**, measured). Round 2's §9 was silent; revision 4 is now explicitly wrong.
- **Frontier 2 answered: the new KNOWN BOUND is a real bound, not a live leak.** `engine.py` *does* log `httpx.HTTPError` with `exc_info` — but the rendered record carries **no credential** in either format, with a positive control proving the same sink leaks when one is present.
- **Frontier 3 answered: the two `x-api-key` pins are jointly honest.** Narrowing the label reddens the **line** pins only; widening to cover the structured form reddens the **bound** pins only. Clean partition, verified both ways with working sanity lines.
- **The author's handling of R20 part 2 is the best work in this packet.** Handed a false rationale, it measured it, said so in the pin's own docstring, and pinned what is true. **Independently confirmed.**
- **Frontier 4 clean:** the reshape sweep reddens the same 8 files, **all named in §9**. R13/MP4 stays closed.
- **MISSING PINS:** MP10 (sync-twin wire pin) · MP9 (fix the stale §9 R10 row) · MP11 (name the username read's mechanism) · MP12 (§9 must name `test_calibration_counting.py` as a required co-run for R19).
- **Packages considered:** `httpx` 0.28.1 → **keep_with_trigger**, unchanged from round 2 (re-read `Headers.__repr__`; the author independently re-derived the same `SENSITIVE_HEADERS` fact). No mechanism built by me beyond scratch probes.
- **Receipt pointers:** §P1 (5 wrong builds) · §P1b (quantifier table) · §F1–F4 · §P4 · §Residuals.

All measurements **2026-07-27**, worktree `lore-pkt42` at **`abd86c3`**, in a `scratch_copy.sh` tree.
`loremaster.__file__ = /tmp/…/scratchpad/adversary-pkt42/ref/loremaster/loremaster/__init__.py`.
**The repo was never edited** — `git diff` over all production trees empty.

---

## P0 — CONTROLS, INCLUDING TWO OF MY OWN PROBES THAT FAILED

The lead's meta-note ("treat any rationale in the ruling file as an unverified claim") applies to
me too. **Three of my own probes failed this pass and none of their results are reported as
findings:**

1. **A malformed shape-B build.** My first reference build spliced `_request_headers` *inside*
   `__init__`, truncating it and destroying `self._sleep`. It scored **217 passed** on the
   contract; the breakage only surfaced when a probe hit `_sleep_backoff`
   (`AttributeError: 'AsyncClaudeTokenCounter' object has no attribute '_sleep'`). Rebuilt with the
   method placed after `__init__`; shape B v2 scores **233 passed** including
   `test_calibration_counting.py`. *(This produced a real residual — see MP12.)*
2. **A malformed sanity probe.** My first sync-twin loader omitted `sys.modules[name] = m`, so
   `token_survey.py` failed to import at all (`dataclasses … 'NoneType' object has no attribute
   '__dict__'`). The `217 passed` from that run was real but the behavioural claim was unproven
   until I fixed the loader and produced the paired control.
3. **A malformed widening regex** (frontier 3b, twice). The first attempt left the structured form
   **unchanged** — its sanity line said so — so its "5 passed" proved nothing. Redone via a file
   rather than nested shell quoting, with a sanity line showing the structured form now redacted.

**Every wrong build below carries a sanity line proving the mutation changed behaviour**, and every
absence-assertion is paired with a positive control. The round-1/round-2 scratch-path artifact
recurs and is again excluded by taking baselines in the real worktree.

**Baseline at `abd86c3`, real worktree:** `104 failed, 229 passed` (333 tests).

---

## P1 — WRONG BUILDS

### ✅ Round 2's blocker is dead, and the mandate is enforced both ways

| build | sanity | contract verdict | killed by |
|---|---|---|---|
| **W-R10a** — owned arm unauthenticated (round 2's BLOCKER, byte-identical to correct at `720e26a`) | `owned x-api-key: None \| injected: sk-K` | **2 failed** | `test_the_OWNED_client_arm_is_authenticated`, `test_an_injected_client_is_not_mutated` |
| **W-SHAPEA** — client-level headers on **both** arms (round 2's "correct" build) | headers on both clients | **2 failed** | `test_no_credential_is_baked_into_either_CLIENT`, `test_an_injected_client_is_not_mutated` |
| **W-BOTHWIRE** — both twins drop per-request headers | `sync [None]`, `async [None]` | **3 failed** | both wire pins + `TestRequestShapeParity` |
| **shape B reference (correct)** | `_sleep` present, header built per request | **217 passed / 0 failed** (233 with the counter's own suite) | — |

The author's claimed numbers (W-R10a = 2 failed, shape B = 217/0) are **exact**. R19's structural
mandate is genuinely checkable: mandate and function are pinned separately, so satisfying one by
breaking the other is impossible — I tried both directions and neither worked.

### 🔴 MP10 — W-SYNCWIRE: the SYNC twin has no wire pin

`scripts/token_survey.py::ClaudeTokenCounter` is the sync twin. The contract forces it for
**retention** (`test_the_sync_survey_counter_does_not_retain_the_raw_key`, whose comment
explicitly reasons *"the twin in `scripts/`, which mypy never sees … forced explicitly for exactly
that reason"*) — but **both wire pins are on the async class**. A shape-B build that forgets the
per-request headers on the sync twin only:

```
W-SYNCWIRE LANDED
CONTROL (correct build): sync-twin x-api-key on the wire: ['sk-ant-SYNCKEY']
W-SYNCWIRE             : sync-twin x-api-key on the wire: [None]

loremaster/tests/test_secret_leak_vectors.py loremaster/tests/test_logging_setup.py
217 passed in 1.65s
```

**Zero contract failures.** The same reasoning the author applied to retention — force the twin,
because nothing else sees `scripts/` — was not extended to the wire.

**Honest severity qualifier, because it changes the verdict's weight.** Running the counter's own
pre-existing suite as well, W-SYNCWIRE *is* caught:

```
… test_secret_leak_vectors + test_logging_setup + test_calibration_counting
1 failed, 232 passed
FAILED …test_calibration_counting.py::TestRequestShapeParity::test_wire_shape_is_byte_identical_to_survey_counter
```

So the repo has a net — but it is **contingent and unnamed**: it fires only because the *async*
twin is still correct (parity), and the contract never names `test_calibration_counting.py` as
required for this change. **MP10 — the test that should exist:**
`test_the_sync_survey_counter_authenticates_on_the_wire`, mirroring
`test_the_INJECTED_client_arm_is_authenticated` through `_scripts_module("token_survey")`.
**The defect it catches:** `token_survey.py` 401-ing on every count, with the contract green.

### 🔴 MP9 — §9's R10 row tells the builder to write the forbidden shape

`REPORT-contract-pkt42-1.md` §9, the `counting.py` + `token_survey.py` row, verbatim at `abd86c3`:

> *"`__init__` must stop retaining the unwrapped header dict; **bake it into the `httpx` client as
> `loresigil/tei.py` does**. ⚠ Both accept an **injected** client — see §0.7's fork; **either shape
> passes**."*

R19 **overrode** that: *"build no auth headers at construction at all; attach them per request."*
And "either shape passes" is **measurably false** — that build is W-SHAPEA, **2 RED**. The row was
written under R10 and never updated when R19 mandated shape B.

§9's stated purpose (R13) is *"so the builder is authorised rather than trapped (C-DEF)"*. This row
does the opposite: it instructs the trap. **MP9 — replace the row with R19's mandate**, and delete
"either shape passes".

### 🟠 MP11 — R21 added the rows; their instruction still reddens a sibling gate

The three new rows say: *"drop the username round-trip … **→ a plain env read**"*. Measured, on the
exact instruction:

```
  plain env read LANDED at scout.py::from_config (exactly what the §9 row says)
FAILED …TestSecretResolutionHasExactlyOneEntryPoint::test_every_environment_read_is_the_entry_point_or_allowlisted
FAILED …TestSecretResolutionHasExactlyOneEntryPoint::test_the_retired_resolvers_read_nothing
2 failed, 7 passed
```

`ENV_READ_ALLOWLIST` permits env reads only inside `loremaster/config.py` and at named
operational-knob sites — and it lives in a contract file the builder **may not edit**. Round 2's §9
was silent here; revision 4 gives an instruction that provably fails. **MP11 — name the mechanism**
(a non-secret reader **in `config.py`**, which is exempt by prefix), or pre-add the allowlist
entries.

---

## P1b — QUANTIFIER TABLE (mandatory)

| # | invariant | ∀-over-inputs / GUARDED | receipt |
|---|---|---|---|
| I1 | The credential reaches the wire | **GUARDED — ∀ over the two ASYNC arms; the SYNC twin is unpinned** | 🔴 door-build **W-SYNCWIRE**: `[None]` on the wire, **0 contract failures** → **MP10** |
| I2 | No credential is baked into either client (R19 shape B) | ∀ over owned + injected, mandate and function pinned separately | ✅ W-SHAPEA → 2 RED; W-R10a → 2 RED; both directions |
| I3 | An injected client is not mutated | ∀ (single property, both wrong shapes fail it) | ✅ fires on W-R10a **and** W-SHAPEA |
| I4 | No production object retains an unwrapped credential (R10) | ∀ over both counter classes + the production log path ×2 formats, with a leak-detector positive control | ✅ round-1 MP1 door stays closed |
| I5 | The `x-api-key` **header-LINE** form is covered | ∀ (one form), derived from the kept pattern | ✅ narrowing `api[_-]?key`→`api_key` reddens exactly this + its sibling; bound unaffected |
| I6 | The `x-api-key` **STRUCTURED** forms remain a KNOWN BOUND | ∀ over 3 render shapes, trigger stated | ✅ widening to cover them reddens exactly these 3; line pins unaffected. **Trigger verified NOT already live** (F2) |
| I7 | `_scrub_value` recurses through containers (R11) | ∀ over 5 container shapes + end-to-end ×2 | ✅ closed since round 2 |
| I8 | Unlabelled credential in free text is NOT redacted (A18) | ∀ over the matrix | ✅ killed W3 |
| I9 | R8: known scheme preserved, credential always gone | ∀ known + unknown schemes | ✅ killed W-DEL |
| I10 | Entropy machinery gone | **GUARDED** — keyed on NAMES | ✅ behavioural pins kill the inlined-behaviour build |
| I11 | No username round-trip survives (R17) | **GUARDED** — prefix name list + category retirement | ⚠ category retirement is the real guard (round-2 residual, unchanged) |
| I12 | Only `config.py` reads env for a secret | ∀ over AST env reads, both ways | ✅ fires — and **still traps §9's own instruction** → **MP11** |
| I13 | Every unwrap site is allowlisted | **GUARDED** — CALL spelling | ⚠ round-1 residuals closed as prose; accepted under the stated threat model |
| I14 | Byte-exactness from either source (R1/R12) | ∀ source × quoting form incl. unset-var | ✅ closed since round 1 |
| I15 | Every pin has a runtime red (R18) | ∀ | ✅ 0 collection errors at base |
| I16 | The counter still *functions* after R19's structural change | **NOT AN INVARIANT OF THIS CONTRACT** | ⚠ my truncated-`__init__` build scored **217/0** here and **12 failed** in `test_calibration_counting.py` → **MP12** |

---

## FRONTIER ANSWERS

### F1 — Is MP5 closed for the right reason? Is there a third arm? **Right reason, yes. Third arm, YES.**

Both directions verified (table above). The mandate pin rejects shape A and the wire pins reject a
missing arm — they cannot be satisfied by breaking each other.

**The third arm is the sync twin** (MP10). I enumerated every construction and request site:

```
loremaster/loremaster/calibration/counting.py:118   httpx.AsyncClient(...)     — owned  ✅ pinned
scripts/token_survey.py:771                          httpx.Client(...)          — owned  ❌ no wire pin
scripts/token_survey.py:863                          httpx.Client(...)          — MultiModelClaudeCounter's shared client, injected into each per-model counter  ❌ no wire pin
loresigil/{voyage_http,tei}.py                       — loresigil, pinned by its own ∀-3-backend wire pin
```

`scripts/token_survey.py:863` is a **fourth** client construction — `MultiModelClaudeCounter`
builds one `httpx.Client` and injects it into N per-model counters. Under shape B that is harmless
(headers are per-request), which is a further argument for R19's choice; under shape A it would
have been a fifth place to forget. No pin covers it either way.

### F2 — Is the new bound's trigger already true? **No. The bound is honest.**

The trigger is *"if an httpx error carrying request headers is ever logged on the Anthropic path"*.
Its **precondition is met** — `engine.py` catches `(RuntimeError, httpx.HTTPError, OSError)` at
`:395` and logs with `exc_info=exc` at `:513/:515/:527`. So I replicated that exact path on the
shape-B build with a real `httpx.ConnectError` from a mock transport:

```
  engine-shaped httpx-error log [json    ] emitted=True  CREDENTIAL LEAKED=False
  engine-shaped httpx-error log [keyvalue] emitted=True  CREDENTIAL LEAKED=False
  POSITIVE CONTROL (structured header in extra=)      CREDENTIAL LEAKED= True
```

The operative clause is **"carrying request headers"**, and httpx errors do not — their `str()`,
their `repr()` and their rendered traceback are all clean (measured in round 2 and again here).
The positive control proves the probe can see a leak through the same sink.

**One wording note, not a defect:** the trigger as written invites a reader to check "does anything
log an httpx error?" (yes) rather than "does anything render `client.headers` / `request.headers`
into a record?" (no). The second is the actual condition. Sharpening the wording would make the
trigger self-checking.

### F3 — Are the two `x-api-key` pins jointly honest? **Yes — a clean partition.**

| mutation | sanity | reddens |
|---|---|---|
| narrow `api[_-]?key\|apikey` → `api_key` | — | `test_the_x_api_key_HEADER_LINE_form_is_covered_by_a_kept_pattern` + `test_the_anthropic_api_key_header_is_redacted`. **Bound untouched.** |
| widen so labels are seen through quotes | `{'x-api-key: ***REDACTED***` (was leaking) | all 3 `test_the_STRUCTURED_x_api_key_form_remains_a_KNOWN_BOUND` params. **Line pins untouched.** |

Neither pin can be satisfied by sacrificing the other, and together they state exactly which forms
are covered and which are bounded. **The author's correction of R20's own rationale — writing the
measured truth into the pin's docstring rather than the ruling's claim — is verified accurate.**

### F4 — Does any unlisted file still go RED? **No.**

The reshape sweep reddens the same 8 files as round 2 — `test_factory_voyage_context` (11),
`test_factory_secret_resolution` (8), `test_factory` (7), `test_embedding_prompt_name` (5),
`test_tei_prompt_name` (4), `test_voyage_batch` (2), `test_embedding` (1),
`test_embedding_context_backend` (1) — **all named in §9**, with `test_embedding_prompt_name` now
carrying R13's corrected characterisation. MP4 stays closed.

---

## P4 — CLAIMS REPRODUCED

| claim | verdict |
|---|---|
| W-R10a now scores **2 failed** | ✅ exact, with sanity line |
| shape B reference **217 passed / 0 failed** | ✅ exact (233 with `test_calibration_counting.py`) |
| R20 part 2's rationale is false; structured forms LEAK, line form is covered | ✅ **independently confirmed both ways** (F3) |
| R21 §9 rows added for the three R17 sites | ✅ present — but see MP11 |
| httpx obfuscates only `authorization`/`proxy-authorization` | ✅ author's re-derivation matches mine |
| Round-1 and round-2 pin closures | ✅ all still closed |

---

## RESIDUALS — individual verdicts

| # | item | verdict |
|---|---|---|
| S1 | **MP12** — the contract cannot tell a working counter from a structurally broken one. My truncated-`__init__` build scored **217/0** here while `self._sleep` was gone; `test_calibration_counting.py` caught it (12 failed). | **ESCALATE.** R19 mandates a structural change to `__init__`, and the suite governing that change does not exercise the object. §9 should name `test_calibration_counting.py` as a required co-run. One line. |
| S2 | `counting.py:110` comment still reads *"…would render verbatim in any repr of `self._headers`"* — an attribute shape B deletes. | **FLAG.** The very comment R10/R19 quote as "prose that names a hazard is not a guard" becomes stale prose about a non-existent attribute. Update it with the change. |
| S3 | `scripts/token_survey.py:863` — `MultiModelClaudeCounter`'s shared client, a 4th construction site, unpinned. | **NOTED, harmless under shape B.** Worth one sentence in the R19 docstring as *why* shape B was chosen. |
| S4 | The bound's trigger names a precondition (httpx errors logged) rather than the operative condition (headers rendered into a record). | **COSMETIC but worth fixing** — a self-checking trigger is the point of writing one. |
| S5 | `test_no_username_round_trip_survives` is still a 5-file prefix list | **RESIDUAL, unchanged from round 2.** The category retirement is the real guard. Acceptable. |
| S6 | R16 has no mechanical commit-boundary check | **ACCEPTABLE, unchanged** — a split commit is a red tree. |
| S7 | Round-1 residual R12 (`Bearer <k>'}` eats the closing quote) | **STILL OPEN, still out of scope** — operator declined twice. Re-raised so it is not lost by attrition. |
| S8 | Baseline test count moved 337 → 333 between `720e26a` and `abd86c3` | **NOTED, not investigated** — consistent with consolidation, but I did not derive it. Flagging rather than assuming. |
| S9 | I ran `pytest` in the graded worktree (read-only) | **DISCLOSED.** `git diff` over all production trees empty. |

---

## VERDICT

# CONTRACT INSUFFICIENT

**The pin work in this revision is excellent and I could not break it.** R19's structural mandate is
enforced from both sides — I built the two obvious wrong shapes and each died on a different pin,
which is what "mandate and function pinned separately" is supposed to buy. The R20 handling is the
strongest single act of this packet: handed a false rationale by the ruling, the author measured it,
contradicted it in the pin's own docstring, and pinned the truth — and my independent both-ways
mutation confirms the resulting pair is a clean partition. Frontier 2's bound is real, not a live
leak, with a positive control behind that claim.

It is INSUFFICIENT for two reasons, and they are different in kind.

**One is a pin (MP10):** the wire invariant is quantified over the *async* arms, and the sync twin
in `scripts/` — the file the contract itself says mypy never sees — has retention forced but not
wire. That is the same quantifier shape as rounds 1 and 2, at its third address. The repo's
pre-existing parity test happens to catch it, but only because the async twin is still right, and
the contract never names that test.

**The other is the scope list (MP9, MP11), and it is the more troubling of the two**, because §9
exists specifically to stop C-DEF traps and now contains two. Its R10 row still instructs the shape
R19 forbids and asserts "either shape passes", which I measured red. Its R21 rows instruct a plain
env read, which I measured red. **Rulings updated the pins; nobody re-ran the scope list against
them.** A builder who follows §9 literally writes two wrong things and meets four red tests it was
told it would not.

All four missing items are small. None requires a new design decision.
