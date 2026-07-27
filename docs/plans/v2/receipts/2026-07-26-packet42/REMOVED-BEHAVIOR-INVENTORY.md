# Packet 42 — REMOVED-BEHAVIOR INVENTORY (tdd Phase 0)

Mechanical enumeration of every observable behavior of the code packet 42 deletes or
replaces, at sub-path grain. One old code path can hold both a virtue to preserve and a
sin to drop, so branches, guards, side effects and per-field output provenance are listed
individually. This file feeds Phase 1 adjudication, the Phase 2 adversary's **stage 2**
(never stage 1 — the adversary enumerates independently first and the DIFF is the
instrument), and the Phase 7 deletion reconciliation.

Base: `6a21fb6` on `feat/surreal-unification`. Worktree `pkt42-prevent-the-leak`.

**Provenance note.** The packet's own measurement table says *"M3 — **13**
`.get_secret_value()` call sites"*. Re-derived at base: **13 grep hits, 10 real call
sites**. `config.py:725` and `_txn.py:964,967` are prose inside docstrings. The count in
the packet conflates two populations; the allowlist in step 3 is sized off the **10**.

---

## A. `loremaster/logging_setup.py` — the entropy catch-all (packet steps 5 + 6)

| # | behavior at base | adjudication |
|---|---|---|
| A1 | `_TOKEN_RE` = `[A-Za-z0-9+=_\-]{24,}` selects the candidate window; charset excludes `/` and `.` | **dropped-deliberately** — the candidate window exists only to feed A2 |
| A2 | a candidate whose Shannon entropy ≥ `_ENTROPY_BITS_THRESHOLD` (3.5) → `***REDACTED***` | **dropped-deliberately** — packet Mission; this IS the heuristic being removed |
| A3 | a candidate with entropy < 3.5 survives intact (e.g. a long repetitive run) | **dropped-deliberately** — falls out with A2 |
| A4 | `_is_safe_high_entropy_run`: path-component OR canonical UUID → exempt | **dropped-deliberately** — vestigial once A2 is gone (packet step 6, explicit) |
| A5 | `_is_absolute_path_component` cond. 1: maximal blob starts with `/` | **dropped-deliberately** — support for A4 |
| A6 | cond. 2: blob contains no `+` and no `=` | **dropped-deliberately** — support for A4 |
| A7 | cond. 3: run is not the FIRST component of the blob | **dropped-deliberately** — support for A4 |
| A8 | cond. 4: run is not MIXED CASE | **dropped-deliberately** — support for A4 |
| A9 | `_UUID_RE.fullmatch` exempts a canonical RFC-4122 UUID anywhere | **dropped-deliberately** — support for A4 |
| A10 | `_shannon_entropy_bits("")` returns `0.0` (empty-string guard) | **dropped-deliberately** — function deleted |
| A11 | `_PATH_BLOB_CHARS` deliberately INCLUDES `+`/`=` so A6 can observe them | **dropped-deliberately** — support for A6. ⚠ This constant's comment records that an earlier version made A6 **dead code**; the coupling dies with both |
| A12 | ORDER in `_scrub_text`: bearer → assignment → entropy, so labelled patterns win | **preserved-with-pin** — bearer→assignment order survives; pin that a labelled secret is still label-preservingly redacted |
| A13 | scrubbing is idempotent (`***REDACTED***` re-scrubs to itself) | **preserved-with-pin** — must still hold with only the labelled patterns |
| A14 | `_BEARER_RE` redacts `Bearer <token>`, preserving the label | **preserved-with-pin** — packet Scope OUT keeps labelled patterns |
| A15 | `_ASSIGNMENT_RE` redacts `api_key=…`/`token:…`/`password=…` etc., preserving label+separator | **preserved-with-pin** — same |
| A16 | KNOWN BOUND: a bare hex/git-SHA run outside a path is redacted (#227 residual) | **bound DISSOLVED** — no longer redacted. `TestBareHexRunsStayRedactedKnownBound` must be **deleted with a note**, not left green. Per "WHEN YOU CANNOT CLOSE A HOLE, PIN IT", a pin outlives its hole only as a lie |
| A17 | KNOWN BOUND: a secret in a URL path segment, or a UUID-shaped key, is NOT caught | **bound dissolved as a bound** — but see A18 |
| A18 | an UNLABELLED secret in free log text was caught by A2 | ⚠ **exposure genuinely widens — the deliberate trade.** This is the load-bearing risk of the packet and the reason its Exit clause demands the strongest control available. Replacement control: `SecretStr` typing (M2) + the allowlisted unwrap surface, so the value cannot be in the text |
| A19 | `RedactingFilter.filter`, `_scrub_value`, `scrubbed_exception_text` call `_scrub_text` | **preserved** — call sites unchanged; only `_scrub_text`'s body shrinks |

**Per-field output provenance for `_scrub_text`:** input string → output string. At base the
output is the input with three transforms applied in order (A14, A15, A2). After: the same
string with two (A14, A15). Every byte not matched by a labelled pattern is **copied through**
— that is the copied-through set, and it WIDENS by exactly the A2 population.

---

## B. `loresigil/factory.py` — resolver copy #2 (packet steps 1 + 2, operator-ruled)

Ruling 2026-07-26: push resolution UP to the composition root. `loresigil` stops resolving.

| # | behavior at base | adjudication |
|---|---|---|
| B1 | `_resolve_api_key` reads `os.environ.get(api_key_env)` | **dropped-deliberately** — the ruled shape; loresigil resolves nothing |
| B2 | `if not key` → `MissingApiKeyError` (covers BOTH unset and empty-string) | **preserved-with-pin as a PROPERTY** — "a missing/empty key fails loud and never builds a keyless embedder". The exception TYPE moves packages with the ruling |
| B3 | a WHITESPACE-ONLY env var is **accepted** and returned as the key | **old-bug — documented, NOT re-pinned.** `resolve_secret` rejects it (`.strip()` emptiness check). Adopting the canonical resolver fixes this incidentally; the new contract must not re-pin the old permissiveness |
| B4 | the value is passed byte-exact (no stripping) | **preserved-with-pin** — `resolve_secret` also never strips; a key with real leading/trailing whitespace must survive |
| B5 | the error message names the offending env var | **preserved-with-pin** — `resolve_secret`'s `KeyError` also names it |
| B6 | `MissingApiKeyError` is a `RuntimeError` subclass, publicly importable | **dropped-deliberately** — raised only by B1. Caught nowhere in production; 4 test files import it |
| B7 | resolution happens at `make_embedder()` time, i.e. embedder CONSTRUCTION | **dropped-deliberately** — moves EARLIER, to config translation. Failure is strictly sooner, never later |
| B8 | `EmbeddingConfig.api_key_env: str` — required; any string accepted, unvalidated | **dropped-deliberately** — replaced by `api_key: SecretStr` |
| B9 | `make_embedder` passes one resolved `api_key` into all three backend arms | **preserved-with-pin** — must still reach the wire byte-exact on EVERY arm, forced per backend |
| B10 | `loremaster.config.EmbeddingConfig.api_key_env` (the `lore.yaml` schema) | **preserved — NOT TOUCHED.** The env-var NAME belongs in config. `server.py`'s probe-gate message reads this field and stays valid |

**Per-field output provenance for `to_loresigil_config`:** every loresigil field is
**copied-through** from the loremaster config except `output_dimension` (forced from
`config.dim`) and, after this change, `api_key` (**derived** via `resolve_secret`, replacing
the copied-through `api_key_env`). The remaining ten copied-through fields must stay
copied-through — a reshape that drops one is a silent config regression no gate sees.

---

## C. `calibration/counting.py::load_api_key` ≡ `scripts/token_survey.py::load_api_key`

Operator-ruled 2026-07-26: declare `python-dotenv` and adopt it.

| # | behavior at base | adjudication |
|---|---|---|
| C1 | prefers an already-exported `ANTHROPIC_API_KEY` over the file | **preserved-with-pin** — precedence is policy |
| C2 | the exported value is `.strip()`ped | **spec-silent → operator ruling.** Conflicts with B4/`resolve_secret`, which never strips. Two of our three resolvers disagree on this TODAY; consolidation must pick one and say why |
| C3 | falls back to parsing `env_file` line-by-line | **preserved-with-pin** — behavior kept, mechanism replaced by `dotenv` |
| C4 | matches lines starting with `ANTHROPIC_API_KEY=` | **preserved-with-pin** |
| C5 | splits on the first `=`, strips whitespace, then strips `'` and `"` | **dropped-deliberately (mechanism)** — `dotenv` owns quote/escape handling and does it more correctly (it also handles `export ` prefixes and multiline values, which C5 does not) |
| C6 | an empty value after parsing → keeps scanning subsequent lines | **preserved-with-pin** — a later non-empty line still wins |
| C7 | raises `RuntimeError` naming both the env var and the file | **preserved-with-pin** |
| C8 | returns `SecretStr` | **preserved-with-pin** |
| C9 | an EMPTY exported env var falls THROUGH to the file | **old-bug candidate → operator ruling.** `resolve_secret` treats empty as fatal; this treats it as absent. #222 names exactly this ("is an empty env var the same as an unset one") as the security-relevant drift |
| C10 | the two twins are byte-divergent (different `RuntimeError` line wrapping) | **dropped-deliberately** — they collapse to one implementation |
| C11 | pkgscout measured one twin failing to honour `export KEY=…` | **old-bug — documented, NOT re-pinned.** Re-derive before claiming fixed |

---

## Open rulings — RESOLVED by the operator 2026-07-26 (binding)

**R1 — C2 / C9, strip-and-emptiness semantics. RULED.** `resolve_secret`'s semantics win and
are the ONE implementation: the value is **never stripped** (a key whose real bytes include
leading/trailing whitespace survives byte-exact), and unset / empty / whitespace-only are all
**fatal**, with the error naming the variable. C2's `.strip()` and C9's fall-through-on-empty
are both retired as drift.

**R2 — the resolver mechanism. RULED (supersedes the earlier "adopt python-dotenv" ruling,
which is narrowed, not reversed).** `python-decouple` was probed and *works* — it delivers
env-beats-file precedence, file fallback and byte-exact values once our two-line policy sits
on top. It was **declined on maintenance grounds, not capability**: latest release 3.8,
uploaded **2023-03-01**, with **no declared `requires_python`**, against this repo's Python
3.14. `python-dotenv` is 1.2.2, uploaded 2026-03-01, `requires_python >=3.10`.

The ruled shape takes decouple's *unified lookup* without decouple:

```python
def resolve_secret(env_var_name: str, env_file: Path | None = None) -> SecretStr:
    value = os.environ.get(env_var_name)
    if not value and env_file is not None:
        value = dotenv_values(env_file).get(env_var_name)
    if not value or not value.strip():
        raise KeyError(f"{env_var_name!r} is unset, empty, or whitespace-only")
    return SecretStr(value)
```

`dotenv_values()` parses a `.env` into a dict **without mutating `os.environ`**. This gives ONE
lookup shape across all three former resolvers (the DRY property the split proposal lacked),
uses the maintained package for the file parsing, and keeps the file consultation **opt-in**.

**R3 — is the `.env` fallback available to the server? RULED: NO.** `server.py`, `scout.py` and
`index/cli.py` call `resolve_secret(NAME)` with **no** `env_file`, so an unset variable stays
fatal there exactly as today. Only `calibration/counting.py` and `scripts/token_survey.py` pass
an `env_file`, which is where a `.env` file is the intended operator workflow. Rationale: the
container is configured by environment, and a stray `.env` in the working directory must never
become a production credential source. **This is a pinnable property, not a convention** — a
test must assert the server-path call sites pass no `env_file`.

**R4 — A18, the widened exposure. ACCEPTED** by the operator ruling that authored this packet.
It remains the packet's central risk and must be met with the strongest available control
rather than assumed away — it is not waived by being accepted.

---

## Second ruling wave — 2026-07-26, on findings raised by `REPORT-contract-pkt42-1.md` §7

The contract author surfaced five open rulings. Two were already answered by R1/R2 above (its
§7.1 recommendation matches R1 exactly). The other three were genuinely new — the packet did
not know about them — plus one measured defect. All four are now ruled.

**R5 — C9, the blank-exported-variable case. RULED: the R2 shape as written stands.** A blank
exported variable **falls through to the `env_file`** when one is supplied, and is fatal only if
the file also misses. The author's alternative (blank is always fatal, file never consulted) was
declined: an operator blanking a variable to force the file fallback is a real calibration
workflow, and breaking it buys uniformity we do not need. **State the resulting rule honestly in
the pin's own message** — emptiness is fatal *at the end of resolution*, not at each source; a
pin whose message claims "empty is always fatal" would be a false gate (the P2 2026-07-14 class).

**R6 — `skills/lore-deploy/scripts/probe_embed.py::_resolve_key`. RULED: IN SCOPE.** Migrate it
to the shared resolver **and extend both AST gates to cover `skills/`**. Rationale: it is the
FOURTH hand-rolled resolver (the packet says three — re-derive every inherited count), and it
carries inventory bug **B3 alive in a second home** (`if not key` accepts a whitespace-only
value). Ledgering it would leave "ONE entry point" true of the workspace but false of the repo.
⚠ `skills/` is currently outside `testpaths` and outside `scripts/typecheck.sh` — extending a
gate over ungated ground means **verifying the gate actually RUNS there**, per the 2026-07-26 law
that a guard nobody runs is a hope with a filename. Both of that packet's instruments sat
outside `testpaths` and were victims of the class they instrument; do not repeat it.

**R9 — EXTEND `scripts/typecheck.sh` TO `skills/`. RULED IN SCOPE (operator, 2026-07-26).** The
contract author flagged as a non-blocking residual that `skills/` sits outside the canonical
typecheck, so mypy would not see `probe_embed.py` after R6 migrates it — the AST gates cover its
resolver SHAPE and unwrap SURFACE, not its TYPES. Closed in this wave rather than passed forward.

**The cost was MEASURED before the ruling, not estimated** (lead, at `506e595`):

```
$ uv run mypy skills/ --ignore-missing-imports
Found 11 errors in 4 files (checked 12 source files)
```

**All 11 are in TEST files** — `test_port_probe.py` (1), `test_workspace_probe.py` (2),
`test_lore_deploy.py` (4), `test_conformance_provenance.py` (4). **The production scripts are
CLEAN, including `probe_embed.py` itself (0 errors).** So the addition is: add the member to
`MEMBERS=(…)` in `scripts/typecheck.sh`, and fix 11 test-file errors of four ordinary kinds
(`no-any-return`, `func-returns-value` on `list.append`, `attr-defined` on a non-re-exported
`shutil`, `unused-ignore` + a `Callable` variance mismatch).

⚠ **Two things the builder must not assume.** (1) `scripts/typecheck.sh`'s header documents WHY it
runs one `mypy` per member rather than one combined invocation — a combined run false-errors on
`tests.conftest` under `explicit_package_bases`, and was measured 2026-07-20 to report **3 errors
where the true count was 55**, producing a false all-clear for two readers. Add `skills/lore-deploy`
as its own iteration; do NOT merge invocations. (2) `skills/` is ALSO outside `testpaths` — R6
already requires proving the AST gate RUNS there; R9 requires the same proof for typecheck (run it,
show the error count going 11 → 0). A gate nobody runs is a hope with a filename.

**SIZE OVERRUN PRE-APPROVED (operator, 2026-07-26).** R6 takes packet 42 past its stated 0.20 wu,
because gating `skills/` means bringing ungated ground under a gate for the first time. The
operator approved this explicitly — *"Include skills/ — consider that approved"*. **No agent
should re-raise the size question, and no agent should trim R6's scope to fit the original
estimate.** The INDEX row's size figure is stale, not a budget: correct it at close-out rather
than sizing the work to it.

**R7 — `scripts/comms_consumer_eval.py::_amain`. RULED: MIGRATE** to the shared resolver, and
delete its allowlist entry. The author's argument is accepted: migrating costs ~3 lines, less
than maintaining the note explaining the exemption — and it keeps every allowlist entry a real
client-call unwrap rather than mixing in a presence check, so the list has ONE justification
shape instead of two.

**R8 — the `Authorization: Bearer` double-redaction. RULED: FIX THE CODE, not the docstring.**
Measured real output is `Authorization: ***REDACTED*** ***REDACTED***`; the docstring promises
`Authorization: Bearer ***REDACTED***`. The docstring is right and the code is wrong: `_BEARER_RE`
fires, then `_ASSIGNMENT_RE` matches its own `authorization` label and eats the scheme word
`Bearer` as if it were the value. **Preserve the scheme word.** It is non-secret and tells an
operator WHICH auth mechanism failed — exactly the diagnostic-data-is-worth-protecting argument
that justifies this entire packet. This is a labelled-pattern behavior and packet 42 already owns
that surface, so it is in scope rather than a follow-on.

---

## Third ruling wave — 2026-07-26, on `REPORT-adversary-pkt42-1.md` (verdict: CONTRACT INSUFFICIENT)

The adversary broke the contract: **two wrong builds scored 204 passed / 0 failed and shipped a
leak.** Its diagnosis of the root cause is accepted verbatim and is the most important sentence in
this file: **A18's frame was too narrow.** The bound was written as *"an **unlabelled** secret in
free text"*, so every pin and carrier was built around unlabelled text — while the credential that
actually exists as a bare `str` in this codebase is **labelled**, sitting in a **header map**, at
the very sites the `UNWRAP_ALLOWLIST` blesses.

**R10 — MP1, the 6-path leak. RULED: FIX IT AT THE SOURCE, not in the redactor.**
`calibration/counting.py::__init__` and `scripts/token_survey.py::__init__` must **stop retaining
the unwrapped header dict on the instance**. Bake the headers into the `httpx` client at
construction, exactly as `loresigil/tei.py` already does (*"the bearer token is baked into the
client headers below; it is not retained on the instance (needless secret surface)"*). Then the
bare-`str` credential object does not exist and there is nothing for a `repr` to leak.

⚠ **The code comment above the defect already named the hazard and shipped it anyway:** *"A bare
`str` here would render verbatim in any repr of `self._headers` — which is precisely what an httpx
error or a debug log would carry."* It was true; only the entropy catch-all was hiding it, and this
packet deletes the catch-all. **Design detail the contract author must resolve:** `counting.py`
accepts an INJECTED client, so headers may need to move to per-request rather than client-level.
That is a design decision — surface it rather than guessing.

The widened-pattern option was declined: it treats the symptom, leaves the bare-`str` object alive,
and returns us to pattern-matching arbitrary text, which is the practice this packet exists to end.

**R11 — MP2, `_scrub_value` container recursion (inventory A19). PIN IT.** Not a fork — a missing
pin. A build replacing the dict/list/tuple recursion with `return value` scores 204/0 and leaks a
labelled bearer token out of an `extra=` map. The existing carriers cannot catch it: the
`SecretStr` leg is masked by the TYPE and the bare-`str` leg is an accepted bound *asserted to
leak*, so both pass either way.

**R12 — MP3. CORRECTS R2's SNIPPET, which was WRONG as written.** `dotenv_values` defaults to
`interpolate=True`, so a secret containing `${…}` is silently rewritten and an unset `${VAR}`
**shortens** the credential (`pw${NOPE}tail` → `pwtail`). Measured by the lead. **The ruled call is
`dotenv_values(env_file, interpolate=False)`**, pinned byte-exact over every quoting form including
the unset-var case. Any agent that copied R2's earlier snippet must re-read it here.

**R13 — MP4. §9 SCOPE CORRECTION.** `test_embedding_prompt_name.py` is not a field rename: it has
no `monkeypatch.setenv`, `LORE_TEI_KEY` is in no conftest, and 5 tests raise `KeyError` once
`to_loresigil_config` performs IO. §9 must say *"add an env fixture; `to_loresigil_config` now
performs IO"* so the builder is authorised rather than trapped (the C-DEF class). The adversary
independently verified §9's FILE list is otherwise complete: 39 failures across exactly 8 files,
all 8 named.

**R14 — R6 IS AMENDED. The MIGRATION half is REVERSED; the GATE half stands.**
The adversary found `probe_embed.py` is **deliberately stdlib-only** (`argparse/json/os/sys/time/
urllib`) with a structured exit-code contract (`_EXIT_BAD_USAGE = 4`) that `lore_deploy.py` shells
out to and **branches on** — and it runs under `sys.executable`, whereas loremaster code in the same
file runs under a separate `_loremaster_python()`. R6 as originally ruled would have imported
`loremaster.config` into a script whose interpreter may not have loremaster, and replaced a clean
exit 4 with a `KeyError` traceback read as exit 1. **That was my error, not the contract's.**

So: **fix B3's bug IN PLACE and stdlib-only** — `if not key` → `if not key or not key.strip()` —
leaving the exit contract untouched. **Ledger the duplicate resolver as a DESIGN decision** with
the stdlib-only deploy boundary as its documented reason, a pin that `probe_embed.py` imports
nothing outside the stdlib, and a **named re-open trigger: the day `probe_embed.py` runs under
`_loremaster_python()`.** This is what ONE IMPLEMENTATION actually prescribes — *"duplication is a
DESIGN decision, not a coding one; escalate it"*. We escalated; the boundary is real.
**R6's gate half is UNCHANGED and already proven** (the adversary reproduced the receipt: 93 files
scanned, `probe_embed.py` present). R9's typecheck extension also stands.

**R15 — residual R7, the real-then-blank duplicate key. FOLLOWS FROM R1, recorded not re-asked.**
`KEY=real` then `KEY=` in one file: the hand-rolled parser yields `"real"`, dotenv is LAST-WINS and
yields `""` → fatal. That is fail-open → fail-closed on a credential path, and **fail-closed is the
direction R1 already chose** (blank is operator error, and a duplicate key in a `.env` is operator
error twice over). Accepted as a deliberate behaviour change, pinned, not left to taste.
⚠ Operator: this one I ruled by extension rather than asking — say so if you want it the other way.

**Routed to the contract author as small closures (each one line, none a fork):** residual R1 —
name the **bound-method alias** (`g = s.get_secret_value; g()`) in the gate's known-bound paragraph;
residual R2 — name the **laundering helper** (an allowlisted wrapper launders every caller; entries
must be LEAF call sites); residual R6 — note `EmbeddingConfig.model_dump()`'s shape change under
`SecretStr`; residual R9 — **fix the inventory's own C4/C11 contradiction** (the contract already
resolves it correctly); residual R3/R4 — both dissolved by R14.

### Riders slotted onto the packet AFTER kickoff (operator sweep, INDEX Log 2026-07-26)

The packet spec gained three riders at `61c8964`/`e4cfc6e`, landed after this packet's Phase 0.
**The worktree copy of the spec is now current with them.** ⚠ The worktree is otherwise still
based on `6a21fb6` and is DELIBERATELY not merged forward: primary `feat/surreal-unification` has
advanced to `48537c3`, which lands packet 04a's contract with **26 deliberately-RED tests**.
Merging that would give this packet a red baseline it does not own and make every gate reading
ambiguous. Merge forward at close-out, not before.

**R16 — the #235 rider. SAME-COMMIT REQUIREMENT, and it binds.** *"Fix the labelled pattern in the
same commit that deletes the catch-all."* Our R8 already ruled the fix and the contract already
pins the non-Bearer leak, so the SUBSTANCE is covered — but the rider's other half is the commit
boundary, and **a rider dropped is the failure mode this repo names most often**. The deletion of
`_TOKEN_RE` and the labelled-pattern fix are **ONE commit**. A commit that deletes the catch-all
without the fix is a strictly-worse tree that must never exist, even transiently, because that is
the tree a bisect or a revert can land on. The `Authorization: Basic <cred>` pin **is** the
mutation proof for this rider — name it as such.
*(Provenance: #235 is this packet's own finding, filed by the lead at 2026-07-26 and picked up by
the sweep. The rider and our R8 are the same conclusion reached twice, independently.)*

**R17 — the #226 rider FOLDS INTO STEP 2, and it SHRINKS the allowlist.** Re-derived by the lead:
`resolve_secret` wraps the SurrealDB **username** — not a secret — at five sites, each of which
immediately unwraps it again:

```
index/cli.py:112  · server.py:6752 · scout.py:728
scripts/search_score_survey.py:696 · scripts/snapshot_gc.py:332
    surreal_user = resolve_secret(config.surreal.user_env).get_secret_value()
    surreal_password = resolve_secret(config.surreal.password_env)   # <- correct: stays wrapped
```

**Five of the ten step-3 allowlist entries are that pointless round-trip.** The consolidated seam
wraps ONLY secrets; a non-secret config read gets a plain read. **The allowlist therefore goes
10 → 5, not 10 → 12.** ⚠ The rider notes *"its own author got 1 of 5 sites wrong"* — the contract
must **re-derive which site that is** rather than inherit the claim (this file's own standing law),
and the password sites must be verified to STAY wrapped: the failure direction that matters is
un-wrapping a real secret while tidying away a fake one.

**R18 — the #221 rider is a VALIDATION RULE on every pin in this packet.** *"The mypy gate is
BLIND through `dict[str, Any]` — the SecretStr migration passed the type gate at ZERO DELTA while
119 tests were runtime-broken."* Therefore: **every contract pin needs a RUNTIME red, never a
type-gate red.** A pin demonstrated only by a mypy error is not demonstrated. This applies
retroactively to the satisfiability receipts already taken — they used live pytest runs, so they
appear to comply, but the contract must **state the compliance explicitly per pin** rather than
leave it inferred. Where a `dict[str, Any]` config seam can be narrowed to a typed model in
passing, do it; #221 stays open for the general instrument if not fully closed here.

---

## Fourth ruling wave — 2026-07-27, on the adversary RE-RUN (verdict: still INSUFFICIENT)

Round 1's four findings are **genuinely closed** — independently verified, not taken on the
author's word. The re-run found a new BLOCKER and, answering the lead's frontier question,
**falsified the rationale the lead had written into R10 itself.**

**R19 — MP5, the new BLOCKER. RULED: MANDATE SHAPE B (per-request headers).**
The wrong build `W-R10a` applies R10's fix to the **injected** client arm only, leaving the
**owned** `httpx.AsyncClient` completely unauthenticated — and produces a **byte-identical failure
set to the correct build** (`diff` empty). Every production construction of the Anthropic counter
uses the **owned** arm (`calibration/engine.py:686`, `scripts/calibration_baseline.py:149`) while
the contract's only wire pin **injects** one. **That is the #107 shape exactly: green everywhere,
100% broken in production.**

The ruled fix is structural, not a pin: **build no auth headers at construction at all; attach them
per request.** One code path, so there is no owned-vs-injected arm to fix-one-and-forget-the-other.
The adversary measured shape B **immune** to W-R10a. **The owned-arm wire pin (MP5) is ALSO
required** — it outlives the shape decision and catches a future refactor back to client-level
headers dropping auth on one arm.

**R20 — MP7 + MP8, the `x-api-key` asymmetry. RULED: correct the rationale AND pin the pattern.**
Two parts, both required:
1. **R10's stated rationale is now FALSE and must be corrected.** It claims the source fix *"removes
   the only object in the tree that held a labelled credential as a bare `str`"*. After R10,
   `httpx.Headers` holds exactly that — and httpx obfuscates **only** `authorization` /
   `proxy-authorization`, **not** `x-api-key` (read from `httpx.Headers.__repr__` →
   `_obfuscate_sensitive_headers`, httpx 0.28.1). **R10 cited `tei.py` as precedent; that
   precedent's residual protection does not transfer**, because `tei.py` authenticates with
   `Authorization: Bearer` and the counter with `x-api-key`. A false rationale in a docstring is
   the served-English-contradicting-code class this repo calls its most expensive — fix it.
2. **Pin `x-api-key` against the surviving labelled patterns.** `_ASSIGNMENT_RE` matches
   `\bapi[_-]?key\b`, which fires inside `x-api-key` — so a rendered `Headers` repr **would** be
   scrubbed by a pattern this packet keeps. That is currently **incidental**, and *"it happens to
   match"* is not a guarantee: pin it explicitly, so a future narrowing of the pattern goes RED
   instead of silently un-covering the one header our production credential travels in.
   ⚠ Keep the bound's **measured trigger** from the adversary: *the day a lore client authenticates
   with a header httpx does not obfuscate* — which is **TODAY**, for `x-api-key`.

**R21 — MP6, the C-DEF trap R17 created. FIX THE SCOPE LIST.** The allowlist shrink 10 → 5 changes
three call sites whose §9 rows do not exist, so the builder would meet red tests whose fix is not in
its authorised set. Add them. ⚠ And carry the author's own independent find: `snapshot_gc.py:332` is
the ONLY one of the five whose `KeyError` is **caught** and rendered into a clean `_EXIT_ERROR`
message — de-wrapping there must keep raising a **naming** error or the CLI's diagnostics silently
degrade.

**Verified and closed, recorded so they are not re-litigated:** R17's re-derivation is confirmed
independently (*"1 of 5 sites wrong"* does **not** reproduce; all five are username round-trips, all
five password siblings stay wrapped). R18 verified structurally (337 collected, **0 collection
errors**, 103 runtime reds; base RED 103/234 matches §10.1 exactly). R16's commit boundary has no
mechanical enforcement, but `W-DEL` = 16 RED means a split commit has a red suite — **adequate**,
reported not a defect. The injected-client pin is **sound**: shape A passes, shape B passes,
bare-dict retention fails.

**Raised and NOT actioned (operator's call, out of packet scope):** residual R12 — the base scrubber
mangles adjacent structure (`Bearer <k>'}` eats the closing quote/brace, because the pattern ends
`(\S+)`). Pre-existing, cosmetic, unrelated to the deletion.

---

**NOT A RULING — MANDATORY BUILDER SCOPE, no choice involved:**
`scripts/search_score_survey.py::_make_embedder` is a THIRD production-tree consumer of
`loresigil.factory.EmbeddingConfig` that `lore_impact` did not report (filed as lore finding
**#233**). It constructs the model directly, so after the `api_key_env` → `api_key` reshape it
raises `ValidationError` **at runtime**, and **mypy cannot catch it because `scripts/` is not a
typecheck member**. It migrates. Any count of that model's consumers inherited from Phase 0 is
wrong by one — re-derive it.
