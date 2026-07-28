# REPORT-adversary-pkt42-1-rerun3 — CONTRACT ADVERSARY, packet 42, FOURTH PASS

brief-base v7 read

Grades revision 5 at **`c05fde4`**. Prior passes cited, none superseded:
`REPORT-adversary-pkt42-1.md` · `REPORT-adversary-pkt42-1-rerun.md` · `REPORT-adversary-pkt42-1-rerun2.md`.

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT** — one BLOCKER (a wrong build leaks a credential into a rendered log line with **zero** added failures), one instrument-honesty defect. **Every round-3 finding is closed and independently verified.**
- **P1 headline — the round-3 blocker is dead; a new one survives, and it is the name-list shape.** `W-SYNCWIRE` → **3 RED** (claim exact) · `W-R10a` → **2 RED** · `W-SHAPEA` → **2 RED** · `W-LASTWRITER` → **2 RED** · shape-B reference on both counters → **225 passed / 0 failed** (claim exact). **But `W-PARAMNAME-BARE` — a production class in a module the sweep already scans, holding a bare-`str` credential under the parameter name `bearer_token` — leaks into a rendered log line in BOTH formats and adds ZERO failures.** Base leaks 0/2; post-deletion 2/2. **Strict regression.**
- **Why nothing sees it: THREE independent name-lists, and the credential is named in none of them.** The sibling sweep keys on `"api_key" in parameters`; `SECRET_PARAM_NAMES` is `{"password", "api_key"}`; `UNWRAP_ALLOWLIST` keys on a `.get_secret_value()` call that a bare `str` never makes. This is the repo's own six-receipt instrument lesson, at its seventh address.
- **The sibling sweep is genuinely good work and I want to be precise about its limits.** Its class-level derivation is real, it follows inheritance, its anti-vacuity control **provably fires** (`constructed=[]` → `AssertionError: vacuous: []`), and it caught `W-LASTWRITER`. Two honest gaps: its **module list is a hand-list of 6** (docstring says *"DERIVED from the live tree, never a hand-list"*), and **`CalibrationEngine` is in its asserted roster but SKIPPED at construction** (`missing 3 required keyword-only`), so the ∀ pin never interrogates it — `constructed=6` clears the floor of 4, making the skip invisible.
- **Both of those gaps are covered by a SIBLING instrument, verified deterministically:** a new-module sibling and an early `CalibrationEngine` unwrap both appear in `_unwrap_sites()` and are absent from `UNWRAP_ALLOWLIST` → **would redden a green tree**. So they are honesty defects, not holes. `W-PARAMNAME-BARE` is the one that is a hole.
- **Frontiers answered:** 1 — roster derived, module list hand-listed · 2 — anti-vacuity control **fires** · 3 — `CalibrationEngine` leg checks neither type nor behaviour; it is skipped · 4 — the two-model/sync legs **do** catch last-writer-wins (2 RED) · 5 — R24/R25 are now **executable** (`resolve_config_value` named, co-run named) · 6 — the §9 self-audit **holds**: no stale instruction survives, and the R10 row is superseded in place rather than silently edited.
- **MISSING PINS:** MP14 (BLOCKER — credential-name coverage) · MP13 (sweep must assert every rostered holder was constructed; fix the docstring's hand-list claim).
- **Packages considered:** none — no mechanism specified or built by me beyond scratch probes.
- **Receipts:** §P1 · §P1b · §Frontiers · §P4. Baseline at `c05fde4`: **105 failed / 236 passed** (341 tests), real worktree. `loremaster.__file__` inside scratch printed live. **Repo never edited** — `git diff` over production trees empty.

Measurements **2026-07-27**, worktree `lore-pkt42` at **`c05fde4`**, `scratch_copy.sh` tree.

---

## P0 — CONTROLS

Scratch survives from earlier passes; `logging_setup.BASE.py` md5 `831ca42e782e9ee9b4533dc750166ccc`
still matches. Every mutation asserts its landing (`assert … , "TARGET ABSENT"`) and carries a
behavioural sanity line. **Two of my own probes failed this pass and neither result is reported as
a finding:** a holder-enumeration probe that died on `ModuleNotFoundError: _logging_fixtures`
(missing `loremaster/tests` on `sys.path`), and a `comm`-diff that could not discriminate because
the pin in question was *already* red at base — I replaced it with a deterministic check against
the gate's own helper (`_unwrap_sites()` + `UNWRAP_ALLOWLIST` membership), which answers the
green-tree question without needing a green tree.

**Discrimination check on my headline probe:** the same rendering path reports
`LEAKED = False` on the base build and `LEAKED = True` after the deletion, so it is measuring the
packet's change and not a constant.

---

## P1 — WRONG BUILDS

### ✅ Round 3's blocker is dead, and the whole battery is caught

| build | sanity | contract verdict | note |
|---|---|---|---|
| **W-SYNCWIRE** (sync twin posts no auth header) | `sync wire x-api-key: [None]` | **3 failed** | round-3 BLOCKER, was 0. Claim exact. |
| **W-R10a** (owned arm unauthenticated) | `owned: None \| injected: sk-K` | **2 failed** | |
| **W-SHAPEA** (client-level headers) | headers on client | **2 failed** | |
| **W-LASTWRITER** (shared client, per-construction header writes) | `shared client carries x-api-key: sk-ant-MULTI` | **2 failed** | frontier 4 — the sync legs catch it |
| **shape-B reference, both counters** | — | **225 passed / 0 failed** | claim exact |

### 🔴 BLOCKER MP14 — `W-PARAMNAME-BARE`: a credential named anything else

Appended to `loremaster/loremaster/calibration/counting.py` — a module the sibling sweep **already
imports**:

```python
class StreamingCountClient:
    def __init__(self, bearer_token: str, *, model: str = DEFAULT_MODEL) -> None:
        self._model = model
        self._token = bearer_token
        self._client = httpx.AsyncClient(headers={"x-api-key": bearer_token})
```

Measured on the contract-green shape-B + R8 build:

```
  SANITY vars() holds the bare credential: True
  RENDERED LOG LINE [json    ] CREDENTIAL LEAKED = True
  RENDERED LOG LINE [keyvalue] CREDENTIAL LEAKED = True

--- failures ADDED by W-PARAMNAME-BARE (leak_vectors + secret_typing + logging_setup) ---
(blank = NOT CAUGHT by any pin in the contract)
```

**Paired control — the same class on the BASE build, catch-all alive:**

```
  BASE [json    ] CREDENTIAL LEAKED = False
  BASE [keyvalue] CREDENTIAL LEAKED = False
```

**0/2 → 2/2. A strict regression the packet introduces, and nothing in the contract sees it.**

**Why all three instruments miss it — and they miss it for three *different* reasons, which is
what makes this a class rather than a gap:**

| instrument | keyed on | why it misses |
|---|---|---|
| `_auth_holder_classes()` (the new sweep) | `"api_key" in parameters` | the parameter is `bearer_token` |
| `test_every_secret_parameter_is_annotated_secretstr` | `SECRET_PARAM_NAMES = {"password", "api_key"}` | same |
| `TestEveryUnwrapSiteIsAllowlisted` | a `.get_secret_value()` **call** | a bare `str` never makes one |

This is verbatim the lesson in this repo's own CLAUDE.md — *"when you catch yourself enumerating
what is FORBIDDEN, you have already lost… the forbidden set is unbounded; the SAFE set is small
and enumerable"* — and the table there already records six defeats of exactly this shape. The
credential-NAME set is unbounded: `token`, `bearer_token`, `access_token`, `secret_key`, `key`,
`credential`, `pat`, `dsn` are all ordinary, honest spellings.

**MP14 — the test that should exist.** Two shapes are available and I would take the second:

1. *Cheap:* widen `SECRET_PARAM_NAMES` to a documented credential-name set and pin that widening is
   a deliberate act. **This is another denylist and will lose again**, so I raise it only to reject it.
2. *Safe-set:* pin that **every `__init__` parameter annotated `str` in the auth-holder modules is
   on an explicit NON-credential allowlist** — i.e. invert the question from *"is this name a
   credential?"* to *"is this bare-`str` parameter one of the few we have cleared?"*. The contract
   already owns both halves of the machinery: `_python_sources()` walks the workspace and
   `UNWRAP_ALLOWLIST` demonstrates the closed-evidence-category pattern.

**The defect it catches:** a new credential-holding constructor, named anything, retaining a bare
`str` that reaches a rendered log line — which is precisely the A18 widening this packet owns and
the class R22's sweep was created to end.

⚠ **Scope note for the operator:** shape 2 is a *design* decision (it changes what the ∀ pin
quantifies over), not a lint fix. Per this repo's routing rule I am naming the fork rather than
prescribing it.

---

## P1b — QUANTIFIER TABLE (mandatory)

| # | invariant | ∀-over-inputs / GUARDED | receipt |
|---|---|---|---|
| I1 | No auth-holder sibling exposes the raw credential (R22) | **GUARDED — ∀ over classes with a parameter *named* `api_key*, in 6 *named* modules, that are *constructible* from a 4-key supply dict** | 🔴 **W-PARAMNAME-BARE** survives → **MP14**. ⚠ `CalibrationEngine` is rostered but **SKIPPED** (`missing 3 required keyword-only`) → **MP13** |
| I2 | The sweep finds a real population | positive control, `>= 6` | ✅ derives 7 classes live |
| I3 | The sweep's anti-vacuity control can fire | — | ✅ **proven**: empty supply → `constructed=[]` → `AssertionError: vacuous: []` |
| I4 | Every wire arm authenticates (async + sync, owned + injected) | ∀ over 2 classes × 2 arms + a 2-model leg | ✅ W-SYNCWIRE 3 RED · W-R10a 2 RED · W-LASTWRITER 2 RED |
| I5 | No credential is baked into either client (R19 shape B) | ∀ over both classes, mandate + function pinned separately | ✅ W-SHAPEA 2 RED |
| I6 | No production object retains an unwrapped credential | ∀ over both counters + production log path ×2 | ✅ closed since round 2 |
| I7 | `x-api-key` header-LINE covered / STRUCTURED bounded | ∀, clean partition | ✅ verified both ways in round 3; bound re-verified not-live |
| I8 | `_scrub_value` recurses through containers | ∀ over 5 shapes + end-to-end | ✅ closed since round 2 |
| I9 | R8 scheme handling | ∀ known + unknown schemes | ✅ closed since round 1 |
| I10 | Entropy machinery gone | **GUARDED** (names) | ✅ behavioural pins backstop it |
| I11 | Every unwrap site is allowlisted | ∀ over `.get_secret_value()` calls, whole workspace, both ways | ✅ **covers what the sweep misses**: new-module sibling and early `CalibrationEngine` unwrap both `-> NO -> WOULD redden a green tree`. Blind to bare-`str` credentials (I1) |
| I12 | Every secret-named parameter is `SecretStr` | **GUARDED** — `{"password", "api_key"}` | 🔴 same door as I1 → **MP14** |
| I13 | Only `config.py` reads env for a secret | ∀ both ways | ✅ and §9 now names the executable mechanism |
| I14 | Byte-exactness (R1/R12) | ∀ source × quoting form | ✅ closed since round 1 |
| I15 | Every pin has a runtime red (R18) | ∀ | ✅ 0 collection errors |

---

## FRONTIER ANSWERS

**1 — Is the roster derived or hardcoded?** *Both, at different levels.* The **class** roster is
genuinely derived (`vars(module)` + `inspect.signature`, `__module__` dedup), and **inheritance is
followed** — I checked, `Derived(Base)` with `api_key` on the base is seen. But the **module list
is a hand-list of six**, while the docstring claims *"DERIVED from the live tree, never a hand-list
— that is the whole point… A sibling added next year is covered by this scan."* Measured: a new
module `calibration/batch_counter.py` holding an unwrapped key → `sibling SWEEP sees it: NO`.
It **is** caught, by `_unwrap_sites()` (`-> NO -> WOULD redden a green tree`). So the outcome is
safe and the sentence is false. Fix the sentence.

**2 — Does the anti-vacuity control fire?** **Yes, proven**, not merely present.

**3 — Is the `CalibrationEngine` leg checking type or behaviour?** **Neither — it is skipped.**
The sweep's constructor loop supplies `{api_key, base_url, models, model}`; `CalibrationEngine`
also requires `committed_constant`, `state_dir`, `findings_port`, so it raises `TypeError` and hits
`continue`. Enumerated:

```
  CONSTRUCTED  loremaster.calibration.counting.AsyncClaudeTokenCounter
  SKIPPED      loremaster.calibration.engine.CalibrationEngine  <- missing 3 required keyword-only
  CONSTRUCTED  loresigil.tei.TEIEmbedder / voyage_cloud / voyage_context
  CONSTRUCTED  token_survey.ClaudeTokenCounter / MultiModelClaudeCounter
  constructed=6 (anti-vacuity floor is 4)
```

`test_the_known_siblings_are_all_present` asserts it is in the roster; nothing asserts it was
*exercised*. W-ENGINE (early unwrap) → `3 passed` on the green base: **the sweep does not catch it.**
It would redden a green tree via the unwrap gate. **MP13:** assert every rostered holder was
constructed, or carry an explicit named skip-list — `constructed >= 4` cannot tell coverage from
silence.

**4 — Does the two-model leg distinguish last-writer-wins?** **Yes.** `W-LASTWRITER` (shared client,
headers written per construction, no per-request headers) → **2 failed**. The sync legs are real
mirrors of the async four, not a reduced set.

**5 — Are R24/R25 executable?** **Yes.** The three rows now name the mechanism —
*"add a NON-SECRET sibling in `loremaster/config.py` — e.g. `resolve_config_value(env_var_name) -> str`"* —
explain **why** (keeps the read inside the one module the gate permits), and carry the
`snapshot_gc.py` naming-`KeyError` constraint as the *reason* a shared sibling beats five inline
reads. That is directional → executable. R25's required co-run is named. **MP11 and MP12 closed.**

**6 — Does the §9 self-audit hold?** **Yes, on my checks.** The R10 row is rewritten and, better,
**superseded in place** — it states what it used to say and why that was false, rather than quietly
editing. No surviving row carries *"either shape passes"*, *"bake it into the `httpx` client"* or
*"→ a plain env read"* as an instruction (the remaining hits are narrative describing the
correction). The `probe_embed.py` row correctly holds R14's reversal **and** gains an R22 sibling
note that its two wire sites are already shape B — a sibling check the sweep itself cannot make,
done by hand and correctly. **MP9 closed.**

---

## P4 — CLAIMS REPRODUCED

| claim | verdict |
|---|---|
| `W-SYNCWIRE` 0 → **3 failed** | ✅ exact, with sanity line |
| shape-B reference **225 passed / 0 failed** | ✅ exact |
| sweep found `CalibrationEngine` + `MultiModelClaudeCounter` | ✅ both in the derived roster |
| `merge_mcp_json._desired_entry` scoped out with a reason | ✅ accepted — a literal `Bearer ${VAR}` template is not a credential |
| §9's other 14 rows current | ✅ no stale instruction found |
| R22 generalisation ("a pin over one member of a twin pair is half a pin") | ✅ and it is the right lesson — it is *why* MP14 exists one level up |

---

## RESIDUALS — individual verdicts

| # | item | verdict |
|---|---|---|
| S1 | **MP13** — rostered-but-skipped holders; docstring's "never a hand-list" claim | **ESCALATE.** Two-line fix. Honesty defect, not a hole. |
| S2 | The sweep imports `token_survey` by mutating `sys.path`; a name collision with any other `token_survey` on the path would silently scan the wrong module | **FLAG**, low risk. |
| S3 | `counting.py:110` comment referencing `self._headers` (round-3 S2) | **STILL OPEN** — shape B deletes that attribute; the comment R10/R19 both quote becomes stale prose. |
| S4 | Round-1 residual R12 (`Bearer <k>'}` eats the closing quote) | **STILL OPEN, out of scope** — operator declined three times. Re-raised so it is not lost by attrition. |
| S5 | Baseline moved 333 → 341 tests between `abd86c3` and `c05fde4` | **CONSISTENT** with the two new classes; I did not derive it line-by-line. |
| S6 | I ran `pytest` in the graded worktree (read-only) | **DISCLOSED.** `git diff` over production trees empty; only the author's two test files show. |

---

## VERDICT

# CONTRACT INSUFFICIENT

**I want to be plain that this was close, and that the sweep was the right move.** R22's
generalisation — *"before any pin is called complete, enumerate the SIBLINGS of the object it
targets"* — is correct, and taking MP10 as a class rather than a patch found two siblings I had not
enumerated either. The sweep has a working anti-vacuity control, it follows inheritance, it caught
`W-LASTWRITER`, and the whole round-3 battery is now dead. §9 is executable rather than directional
for the first time, and the R10 row's supersede-in-place is the correct way to retire a false
instruction. Four of my five wrong builds failed to survive.

It is INSUFFICIENT for one reason: **the sweep answered "which siblings?" and left "keyed on what?"
untouched.** It is a third name-list stacked on two existing ones, and all three enumerate the same
unbounded set — what a credential is *called*. A class in a module the sweep already scans, with a
parameter named `bearer_token`, leaks a credential into a rendered log line in both formats and
reddens nothing; the base build does not leak it. That is the packet's own A18 widening walking
through a door none of the three instruments can see, and it is the seventh instance of the shape
this repo's CLAUDE.md already has six receipts on.

MP14 is a design fork (invert to a safe-set), so it routes to the operator, not to a builder.
MP13 is two lines.

**Severity trend, stated because it matters for the decision:** 2 blockers → 1 → 1 → 1, and this
one is narrower than its predecessors — it requires *new* code to be written rather than existing
code to be got wrong. If the operator judges "a future author adds a differently-named credential
holder" to be outside packet 42's blast radius, MP14 becomes a ledgered known bound with a re-open
trigger rather than a blocker, and I would not argue. **That is an operator call, not mine** — but
it should be made deliberately, because right now it is neither closed nor pinned.
