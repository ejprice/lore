# REPORT-builder-gatewrapper-1 — the pending-contract gate wrapper + registry (finding #306)

brief-base v9 read
brief project v7 read

## SUMMARY BLOCK

- **state:** done-with-deviations
- **deviation 1:** the ruling names 11 files; a **12th** red file exists at HEAD
  (`loremaster/tests/test_comms_footer.py`, wave C's own C3 contract). Deliberately **NOT
  registered** — adjudicating a bound is not a builder's authority, and its build discharges
  it this wave. **The gate therefore FAILS at HEAD naming those 7 errors.** §6.1.
- **deviation 2:** the ruling's *"every mypy error must name a registered SYMBOL"* is
  **unsatisfiable for 4 of 198 errors** (`no-any-unimported` names no symbol). Ruling
  **falsifier (b) invoked**, residual stated per-file/per-code/per-COUNT. §6.2.
- **deviation 3:** two numbers inherited from #306/§L-4 do not reproduce — filed as **#307**
  (supersedes #306). "102 errors" is ONE LEG's summary line; merged = 191 then, **198 now**.
  "Every error is attr-defined" = 190/198. §2.
- **deviation 4:** module carries **no shebang / not executable** (house convention for
  dep-importing scripts). Invoke with `uv run python scripts/...`. §3.
- **deviation 5:** the **first full run exposed a real defect in this instrument** —
  pytest's default `junit_family=xunit2` drops the `file` attribute, so 444 registered
  pins rendered as UNREGISTERED with nothing looking wrong. Fixed two ways (flag + a
  refusal guard) and pinned. **§8.2 — read this one.**
- **deviation 6:** this repo's `#210` pin caught **my own** `^…$`-with-`.match` regex, in
  the instrument built to stop unaccounted gate output. Fixed (`.fullmatch`); pin green
  (25 passed). §4.
- **deviation 7 — the biggest one:** the ruling's §4 specifies mypy + pytest partitions;
  `CLAUDE.md` names **THREE** commit gates. The wrapper was missing **ruff** — #306's own
  defect inside #306's pin. Found because **`uv run ruff check .` was ALSO red at HEAD** (2
  violations, committed file, no ledger row). **Both fixed**; a zero-tolerance ruff leg
  added; `is_deploy_receipt` now requires all three. Filed as **#312**. **§8.1b.**
- `Packages considered:` PyYAML 6.0.3 (`safe_load`/`safe_dump`, read live) → **replace** ·
  pydantic 2.13.4 (`ConfigDict(extra="forbid")`, `field_validator`) → **replace** · pytest
  9.0.3 `--junitxml` + stdlib `xml.etree.ElementTree` (read `pytest --help`) → **replace**
  (`pytest-json-report` NOT installed; no install needed, built-in suffices) · mypy
  `-O/--output json` → **bespoke text parse, gated by an exact count cross-check** — using
  it would require re-invoking mypy directly, cloning `typecheck.sh`'s `MEMBERS`/`MYPYPATH`
  policy, a registration site `CLAUDE.md` names. §7 carries the trigger.
- **decisions-needed (4):** register the 12th file or leave the gate red? (§6.1) · accept
  falsifier (b)'s stated residual? (§6.2) · teach `typecheck.sh` an opt-in machine-readable
  mode, retiring the bespoke parse? (§7) · who fixes `_surreal_harness`'s `45`→`46`
  docstring count — it is another agent's file (§10b, finding #308)?
- **findings filed:** **#307** (two of #306's headline numbers do not reproduce) ·
  **#308** (the non-contract RED pins) · **#312** (a SECOND canonical gate red at HEAD, and
  the wrapper's own missing leg) · one `lore_remember` gotcha (the junit family).
- **receipts:** §4 unit contract **41/41** · §5 nine live controls, all fired · §5.7 leg-4
  in isolation · §8.1 full run · §8.1b the missing gate · §8.2 the defect the full run
  found · §9 gates (ruff now clean repo-wide) · §10b the unrelated-failure flag.
- **files:** `scripts/pending_contract_gate.py` · `scripts/pending_contracts.yaml` ·
  `scripts/test_pending_contract_gate.py` · a 2-line lint fix in
  `scripts/lore_tool_name_currency.py` (§8.1b). **No `pyproject.toml` edit was needed** —
  `scripts` is already a `testpaths` entry, so the instrument is gated on arrival (§9).
- **⚠ EVERY COUNT HERE IS A MEASUREMENT AT A MOMENT, 2026-08-01, on `533d917` PLUS a LIVE
  shared tree** — two other agents were writing `loremaster/tests/**` throughout, and the
  mypy total moved 198 → 209 mid-run. **`191 registered` held identical across that move**
  (§5.7b), which is the receipt that matters. Re-derive; never inherit. `--derive` exists as
  a command precisely so nobody has to trust this paragraph.

---

## §1 · CAPABILITY CHECK (brief-base §4 — first thing, before the work)

Nothing in the brief was unmeetable. `lore_comms register`/`drain` worked; the lore tool
surface loaded from the `+lore` keyword line; `scratch_copy.sh` was not needed (see §10).
One honest note: **§4 of the design sidecar's report is at a repo-root `REPORT-*.md`
address, which `CLAUDE.md` forbids citing durably.** I therefore cite **finding #306**,
whose body carries the ruling verbatim, everywhere the instrument needs a citation — and
the registry file cites #306, not the report path.

**Tool honesty (brief-base §4):** the file/symbol derivation is a **grep-and-parse over
`typecheck.sh`'s transcript**, not a lore query. Said out loud as required. This is fallback
case (b) — *non-symbol textual seams*: mypy error prose is not a symbol the graph indexes,
and the question is *"what does the gate PRINT"*, which no code index can answer. `lore_read`
/`lore_get_symbol` would have been the wrong instrument, not a skipped one. No friction filed
for this: it is not a lore weakness.

---

## §2 · GROUND TRUTH RE-DERIVED (and two inherited numbers that did not reproduce)

The brief and #306 hand me *"102 errors in 8 files; merged, 11 files"*. Re-measured with the
canonical runner at `533d917`:

| leg | mypy's own summary line |
|---|---|
| `lorerunes` | `Found 89 errors in 3 files (checked 6 source files)` |
| `loremaster` | `Found 109 errors in 9 files (checked 180 source files)` |
| `lorescribe`, `loresigil`, `skills`, `docs/eval`, `scripts` | `Success: no issues found` |

**Merged: 198 errors, 12 files.** Codes: **190 `attr-defined` · 4 `call-arg` ·
4 `no-any-unimported`**.

Two inherited claims are narrower than they read, and both are the class #306 itself warns
about. **Filed as finding #307 (supersedes #306).** Provenance, not blame:

1. **`102` is the LOREMASTER LEG'S OWN summary line**, quoted beside an 11-file table that
   sums to **191**. The `lorerunes` leg's second summary was never quoted. 102 and the
   11-file list cannot both describe the same set. (191 → 198 today is the 12th file, §6.1.)
2. **"Every error is `attr-defined`" is false** — 8 of 198 are not, and 4 of those 8 name no
   symbol at all, which makes the ruling's central matching rule literally unsatisfiable for
   them (§6.2).

Why this is not pedantry: the wrapper's tail serves the **merged** total. A reader comparing
`198` to #306's `102` would conclude the tree regressed by 96 errors when nothing regressed.

---

## §3 · WHAT WAS BUILT

Three files, all under `scripts/`. Zero packet-39 files touched; zero `type: ignore`; zero
mypy-config or `testpaths` changes; the gate definition is untouched. **This is a SECOND,
STRICTER gate on top of the canonical ones, not a narrowing of them:** `typecheck.sh` still
runs unchanged, every error it prints is still printed, and the registry only decides which
of them were already adjudicated.

| file | what it is |
|---|---|
| `scripts/pending_contract_gate.py` | the wrapper: runs the gates, partitions their output deny-by-default, self-destructs, serves the counts |
| `scripts/pending_contracts.yaml` | the registry: the accepted bounds as FACTS (files · symbols · code counts · owner · re-open trigger) |
| `scripts/test_pending_contract_gate.py` | its contract, 41 pins, inside `testpaths` |

**Invocation** (deviation 4): the module imports project dependencies, so — exactly like
`snapshot_gc.py` and `token_survey.py` — it carries **no shebang and no exec bit**. A
barefoot `./scripts/pending_contract_gate.py` dies on `ModuleNotFoundError: pydantic`;
**measured, not assumed** — that was my first run's actual failure. Use:

```
uv run python scripts/pending_contract_gate.py                    # all 3 legs — the deploy receipt
uv run python scripts/pending_contract_gate.py --legs mypy,ruff   # static legs (NOT a deploy receipt)
uv run python scripts/pending_contract_gate.py --verify-registry  # interpreter only, no gate run
uv run python scripts/pending_contract_gate.py --derive           # re-derive the registry body
uv run python scripts/pending_contract_gate.py --registry <path>  # controls / what-if runs
```

Exit **0** = accounted for · **1** = partition failure · **2** = BROKEN INSTRUMENT or bad
registry. The last two are distinct because they demand different actions.

### 3.1 · The registry's derivation — and what is honestly a hand-list

The brief said *derive what you can, and allowlist the SAFE set*. Both were done, and the
split is stated in the registry's own header rather than implied:

- **DERIVED** by `--derive` from a live `typecheck.sh` run: the file set, each file's
  `missing_symbols`, each file's `unsymboled_codes` counts. I did not type any of them.
- **HAND-AUTHORED, because no script can derive an adjudication:** `owner`,
  `reopen_trigger`, `ruling`, `rationale`, and each allowance's `reason`. These are facts
  about a DECISION, not about the tree. `--derive` emits them as `TODO` and refuses to
  invent them — a script that filled them in would be manufacturing authority.
- **CHECKED EVERY RUN, so membership is not merely asserted:** file exists · file still
  errors · every symbol still matches an error line · every symbol still fails to import ·
  every code count still exact. See §3.3.

**The safe set is the allowlist, and it is enumerable** (11 files, 45 symbol claims, 2 code
allowances); the forbidden set is never enumerated at all. A brand-new defect is caught by
**not being on the short list**, which is why it needs no entry anywhere to be caught.

**Grouping:** `owner` and `reopen_trigger` live on the BOUND, not repeated on 11 files —
eleven copies of one fact are eleven places for it to drift (ONE IMPLEMENTATION, applied to
data).

### 3.2 · The matching rule, and the wrong builds it excludes

Deny-by-default. A mypy error is EXPECTED only if its **file** is registered **AND** the
message **names a registered symbol** (or its code carries a declared per-file allowance).
A pytest failure is EXPECTED only if its **file** is registered.

Symbol matching is on **quoted tokens, never substrings**, via one shared function
(`error_names_symbol`) that every caller routes through:

- `Posture` is a proper substring of `PostureRefusal`; a `symbol in message` test admits an
  unregistered symbol and cannot tell. Pinned.
- a dotted `owner.attribute` requires **both** quoted tokens, so the same attribute name on
  a different owner stays unexpected. Pinned.
- the matcher deliberately does **not** parse mypy's message *shapes* (`--derive` does).
  Matching on a quoted-token pair is phrasing-independent, so a new mypy message wording
  costs a re-derivation, never a false clear.

### 3.2b · The THREE canonical gates, not two

`typecheck.sh` (mypy + shellcheck) · `uv run ruff check .` · pytest. All three, because
`CLAUDE.md` names all three and a wrapper that runs a subset is a close-out that reports a
subset — **executed on every future run instead of once**. `is_deploy_receipt` is False
unless all three ran, enforced rather than remembered. See §8.1b for why this sentence
exists, and finding **#312**.

### 3.3 · Self-destruction — five legs, two independent instruments

The registry cannot outlive its premise:

| leg | fires when | instrument |
|---|---|---|
| 1 | a registered file no longer exists | filesystem |
| 2 | a registered file produced **no** mypy errors | transcript |
| 3 | a registered **symbol** matched **no** error line | transcript |
| 4 | a registered symbol now **imports successfully** | **interpreter** |
| 5 | an unsymboled-code count moved, in **either** direction | transcript |

Legs 2/3 read the gate output; leg 4 asks the interpreter. **Two instruments because each is
blind exactly where the other is strong** — leg 4 still fires when the mypy leg was not run
at all (`--verify-registry`, demonstrated in isolation at §5.7).

Leg 3 is per-SYMBOL on purpose: **half a build discharges half a claim, and the surviving
half must shrink to match.** A per-file-only self-destruct would let a registry keep 6 stale
symbol claims alive because a 7th still errors.

### 3.4 · Anti-vacuity — *"if step N silently no-opped, would step N+1 read as success?"*

Yes, in **five** places, so all five are checked and all five raise `BrokenInstrumentError`
(exit 2), never a partition:

1. **The parsed error count must equal mypy's own `Found N errors` total.** If the regex
   stops matching production output, the partition sees nothing unexpected and the tail
   reads green **over an unread error set**. This is the single most important guard here:
   it is the one that stops the whole instrument from silently becoming a rubber stamp.
2. **Every mypy leg must account for itself** with a `Found`/`Success` line.
   `mypy: can't read file` emits neither, and counting only what parsed reads as a pass.
   An empty transcript and a missing shellcheck verdict are likewise refusals.
3. **pytest collecting ZERO tests is a broken instrument** — this repo's documented
   `no tests ran in 0.00s` silent green. So is a pytest exit code above 1 (interrupted /
   internal error / usage / nothing collected), and so is a missing junit-xml document.
4. **A junit document whose failing testcases carry no `file` attribute is refused
   outright** rather than partitioned — see §8.2, which is the guard that exists because
   the defect it names actually happened, on a real 8779-test run, to this instrument.
5. **`ruff check` finding no Python files is refused.** Measured: it prints
   `warning: No Python files found under the given path(s)`, **then `All checks passed!`,
   and exits 0** — byte-identical to a clean repo, so a wrong cwd would read as green.
   (Plus a violation-count cross-check against ruff's own `Found N errors.`, mirroring
   guard 1.)

A **shellcheck** failure is never partitionable — the registry speaks about mypy symbols and
pytest files; a shell defect is neither, so it can only be a loud failure.

---

## §4 · RED → GREEN (TDD receipt)

Contract written first, confirmed RED before the module existed:

```
scripts/test_pending_contract_gate.py:63: in <module>
    from pending_contract_gate import (  # noqa: E402
E   ModuleNotFoundError: No module named 'pending_contract_gate'
1 error in 0.13s
```

After the implementation:

```
................................                                         [100%]
32 passed in 0.14s
```

**⚠ One of my own fixtures was vacuous and the run caught it.** `test_registry_rejects_an_
unknown_key` did `.replace("        rationale:", ...)` against YAML indented **four** spaces
— the edit never landed, the YAML stayed valid, and the test asserted nothing. It now
asserts its own mutation landed (`assert typoed != _REGISTRY_YAML`) before asserting the
rejection. Disclosed because it is precisely the class this repo has the most receipts
against: *a mutation proof needs evidence the mutation LANDED.*

**⚠ And `--derive`'s first live run found three real mypy errors in my own test file**
(`arg-type`, from a `-> object` return annotation). **They were FIXED, not registered.** The
instrument's first act was to catch its own author.

**⚠ So did this repo's #210 pin, and that one is worth reading twice.** The first draft of
`_ERROR_LINE` was `re.compile(r"^…$")` validated with `.match` — the exact violation
`test_anchored_pattern_seam.py::test_every_anchored_match_use_is_allowlisted` exists to
catch, since Python's `$` also matches immediately before a trailing newline, so `.match`
accepts `"…[attr-defined]\n"` against a pattern that reads as closed. **In the instrument
whose entire purpose is refusing to let unaccounted gate output pass.** Fixed — anchors
dropped, `.fullmatch` used, with the reason written at the regex — and the pin is green
again (`25 passed`). Recorded because it is the strongest available argument for keeping ∀
scanners: it caught a real defect in a brand-new file within hours of it being written.

---

## §5 · POSITIVE CONTROLS — nine live runs against the real tree

All owed controls, plus five self-destruct demonstrations. **Every run below is a REAL
end-to-end `typecheck.sh` invocation at `533d917`**, not a canned fixture. The runner is
pasted verbatim at §11 (brief-base §1: an instrument that establishes a load-bearing claim
survives, and mine is not in a scratch dir).

### 5.1 · CONTROL C — the healthy path must PASS *(the control that makes the rest mean something)*

```
registry     : packet-39-pending-build (11 files, 45 symbols) · wave-c-c3-contract-in-flight (1 files, 6 symbols)
mypy         : 198 errors · 198 registered · 0 UNREGISTERED
pytest       : NOT RUN
self-destruct: 43 symbol(s) import-checked absent · 8 UNCHECKED (owner not importable)
               unchecked: build_mcp_server.http_client ×3, build_mcp_server.permission_resolver, ...
VERDICT      : PARTIAL-PASS — NOT a deploy receipt; a leg was not run, so this cannot discharge "full gates green".
EXIT=0
```

Note the verdict wording: a leg that did not run can never be served as the deploy receipt,
even when it passes. Pinned (`test_a_skipped_leg_is_never_served_as_a_deploy_receipt`).

### 5.2 · CONTROL A0 — the REAL registry at HEAD *(an unplanned control, and the best one)*

The 12th file is deliberately unregistered (§6.1), so the instrument fails **on the live
tree, with no injection at all**, naming every residual individually:

```
UNREGISTERED mypy error: loremaster/tests/test_comms_footer.py:1234: Module "loremaster.server" has no attribute "COMMS_FOOTER_PREFIX"  [attr-defined]
UNREGISTERED mypy error: loremaster/tests/test_comms_footer.py:1244: Module "loremaster.messages" has no attribute "PendingTraffic"  [attr-defined]
UNREGISTERED mypy error: loremaster/tests/test_comms_footer.py:1254: "type[AppContext]" has no attribute "_comms_footer"  [attr-defined]
UNREGISTERED mypy error: loremaster/tests/test_comms_footer.py:1268: "type[AppContext]" has no attribute "_comms_footer"  [attr-defined]
UNREGISTERED mypy error: loremaster/tests/test_comms_footer.py:1326: "FakeMessageLedger" has no attribute "pending_traffic"  [attr-defined]
UNREGISTERED mypy error: loremaster/tests/test_comms_footer.py:1352: Module "test_comms_tool" does not explicitly export attribute "FakeAgentDatabase"  [attr-defined]
UNREGISTERED mypy error: loremaster/tests/test_comms_footer.py:1352: Module "test_comms_tool" does not explicitly export attribute "FakeAgentRegistry"  [attr-defined]
========================================================================
registry     : packet-39-pending-build (11 files, 45 symbols)
mypy         : 198 errors · 191 registered · 7 UNREGISTERED
VERDICT      : FAIL — 7 unaccounted item(s)
EXIT=1
```

*"All remaining hits are X" is banned output* — every residual carries its own `file:line`.

### 5.3 · CONTROL A — an injected error OUTSIDE the registry must FAIL

A throwaway `scripts/_control_injected_defect.py` with three real type errors, run against
the **healthy** registry (so the only difference from a PASS is the injection), then deleted:

```
UNREGISTERED mypy error: scripts/_control_injected_defect.py:8: Incompatible types in assignment (expression has type "int", variable has type "str")  [assignment]
UNREGISTERED mypy error: scripts/_control_injected_defect.py:8: Argument 1 to "add" has incompatible type "str"; expected "int"  [arg-type]
UNREGISTERED mypy error: scripts/_control_injected_defect.py:8: Argument 2 to "add" has incompatible type "str"; expected "int"  [arg-type]
mypy         : 201 errors · 198 registered · 3 UNREGISTERED
VERDICT      : FAIL — 3 unaccounted item(s)
EXIT=1
injected file removed: gone
```

`201 = 198 + 3` — the count cross-check (§3.4 guard 1) held across the injection.

### 5.4 · CONTROL B — an UNREGISTERED SYMBOL inside a REGISTERED file must FAIL

`lorerunes.Posture` dropped from `lorerunes/tests/test_posture.py`'s entry; the file stays
registered and keeps erroring for its other four symbols. **This is the case a file-only
matcher waves through**:

```
UNREGISTERED mypy error: lorerunes/tests/test_posture.py:47: Module "lorerunes" has no attribute "Posture"  [attr-defined]
  ... (10 lines, each with its own file:line) ...
mypy         : 198 errors · 188 registered · 10 UNREGISTERED
VERDICT      : FAIL — 10 unaccounted item(s)
EXIT=1
```

### 5.5 · SELF-DESTRUCT, demonstrated — not asserted

| leg | injected condition | observed output | exit |
|---|---|---|---|
| 2 | registered `scripts/mutation_proof.py`, which is green | `SELF-DESTRUCT: registered file 'scripts/mutation_proof.py' (bound 'packet-39-pending-build') produced NO mypy errors — the bound is discharged. DELETE its registry entry with the fix.` | 1 |
| 3 | added `lorerunes.NeverMentionedAnywhere` | `SELF-DESTRUCT: registered symbol 'lorerunes.NeverMentionedAnywhere' (lorerunes/tests/test_posture.py) matched NO error line — the claim is discharged. DELETE the symbol from the registry.` | 1 |
| 4 | added `loremaster.config.LoreConfig` (which exists) | `SELF-DESTRUCT: registered symbol 'loremaster.config.LoreConfig' … now RESOLVES — the bound is discharged. DELETE the entry with the fix.` | 1 |
| 1 | registered a non-existent path | `SELF-DESTRUCT: registered file 'loremaster/tests/test_deleted_by_someone.py' … does not exist — DELETE its registry entry.` | 1 |
| 5 | `count: 2` → `count: 1` | `SELF-DESTRUCT: lorerunes/tests/test_posture.py declares 1 unsymboled 'no-any-unimported' error(s); 2 observed. An allowance is a PIN, not a category… (all codes seen in this file: {'attr-defined': 33, 'no-any-unimported': 2})` | 1 |

**Every one of the five fired, and in each case the partition itself said
`0 UNREGISTERED`** — i.e. the self-destruct legs are what produced the failure, so they are
demonstrably not riding on the partition's coattails.

### 5.6 · What the leg-4 control accidentally proved about leg 3

Injecting `loremaster.config.LoreConfig` fired **legs 3 AND 4 together** (it matches no error
line *and* it imports). That is the design working — but it means leg 4 was not
**independently** demonstrated by that run. So:

### 5.7 · LEG 4 IN ISOLATION — no gate run at all

```
### real registry
registry     : /home/ejprice/PycharmProjects/lore/scripts/pending_contracts.yaml
self-destruct: 41 import-checked absent · 4 UNCHECKED (owner not importable)
               unchecked: build_mcp_server.http_client ×3, build_mcp_server.permission_resolver
EXIT=0

### fixture with a symbol that NOW RESOLVES
SELF-DESTRUCT: registered symbol 'loremaster.config.LoreConfig' (lorerunes/tests/test_posture.py, bound 'packet-39-pending-build') now RESOLVES — the bound is discharged. DELETE the entry with the fix.
EXIT=1
```

Both runs execute **no gate whatsoever** — leg 4 is genuinely independent, and
`--verify-registry` is a sub-second *"does the bound still hold?"* check the lead can run
any time.

### 5.7b · ⚠ THE CONTROLS IN §5.1–5.6 PREDATE THE §8.2 AND #210 FIXES — so they were re-run

Honest bookkeeping: §5.1–5.6 were produced before the `.fullmatch` change (§4) and the junit
fix (§8.2). Both touch parsing, so those receipts belong to an earlier build. The two
load-bearing negative controls were re-run on the **post-fix** build, and — because two other
agents were writing `loremaster/tests/**` throughout — **the tree had moved by 11 errors**:

```
### A0, real registry, POST-FIX
mypy         : 209 errors · 191 registered · 18 UNREGISTERED     (EXIT=1)
### CONTROL B, narrowed registry, POST-FIX
mypy         : 209 errors · 188 registered · 21 UNREGISTERED     (EXIT=1)
```

The 18 = 7 `test_comms_footer.py` + **11 `test_task_read_surface.py`**, an UNTRACKED file
another agent was mid-write in. Which yields the single most reassuring number in this
report:

> **`191 registered` is IDENTICAL across both runs and across an 11-error move in the tree.**

The registry covers exactly what it claims and nothing else; all churn landed outside it, and
the instrument said so, by name, both times. Control B's delta is likewise exactly the 10
`Posture` lines it dropped (`191 − 3` symbols → `188`).

⚠ **Every count in this report is therefore a MEASUREMENT AT A MOMENT on a live shared tree,
not a property of `533d917`.** Re-derive; do not inherit. (That is the whole reason
`--derive` exists as a command rather than as a paragraph.)

### 5.8 · Coverage is a CHECKED VARIABLE, not an assumption

`41 import-checked absent · 4 UNCHECKED` is served on every run, and
`checked + unchecked == symbol_count` is pinned. The 4 unchecked are the `call-arg` claims
(`build_mcp_server.http_client` ×3, `build_mcp_server.permission_resolver`): mypy names the
callable but not its module, so there is nothing to import. **They are not silently assumed
absent — they are counted, named, and still fully covered by legs 2/3/5.** A runtime guard
is an invariant only over what it actually reaches, so the reach is served rather than
rounded away.

---

## §6 · WHERE §4's RULING WAS UNDER-DETERMINED — escalations, not silent choices

### 6.1 · DECISION 1 — the TWELFTH file. **The gate is RED at HEAD until you rule.**

The ruling names 11 files. At `533d917` there are **12**:
`loremaster/tests/test_comms_footer.py`, 7 errors — **wave C's own C3 contract**, committed
RED by `contract-04b2-wavec-1` after the sidecar wrote §4. It is **not packet 39** and **not
blocked on #296**; its build is in flight *this wave*.

**Two readings, both defensible, and they produce different code:**

- **(a) leave it unregistered — what I did.** Registering it would create an accepted bound
  for work that is actively proceeding; the entry would be stale from the hour it was
  written, and if C3's build never lands the registry would silently bless a permanently red
  file (leg 2 fires on *green*, never on *never-built*). **Adjudicating a bound is the
  lead's/sidecar's authority, not a builder's** — the ruling enumerated 11, and 12 ≠ 11.
  **Consequence: the gate FAILS at HEAD** (§5.2) until C3's build lands, at which point the
  registry is already correct with no edit at all.
- **(b) register it as a second bound.** Makes the wrapper pass at HEAD; self-destructs the
  moment C3 lands. The registry is multi-bound by construction precisely because the ruling
  says *"04b-3 deploys after this and inherits the same red HEAD"* — a second bound is a
  supported shape, not a hack.

**My recommendation: (a), unchanged.** The end state is identical and (a) never mints an
exemption that must then be un-minted. But **if C3's build is not landing before the
deploy**, (b) is required and here is the exact block to paste under `bounds:` — no other
edit needed:

```yaml
  - id: wave-c-c3-contract-in-flight
    owner: packet 04b-2 wave C — C3 (loremaster/tests/test_comms_footer.py)
    reopen_trigger: C3's build landing, this wave
    ruling: <lead's ruling id>
    rationale: contract committed RED ahead of a build in flight this wave
    files:
      - path: loremaster/tests/test_comms_footer.py
        missing_symbols:
          - FakeMessageLedger.pending_traffic
          - loremaster.messages.PendingTraffic
          - loremaster.server.COMMS_FOOTER_PREFIX
          - test_comms_tool.FakeAgentDatabase
          - test_comms_tool.FakeAgentRegistry
          - type[AppContext]._comms_footer
```

(That block is exactly the control-C fixture, so §5.1 is already its receipt: with it,
`198 errors · 198 registered · 0 UNREGISTERED`.)

### 6.2 · DECISION 2 — falsifier (b) invoked. Please accept or narrow the residual.

The ruling: *"every mypy error line must name a registered file AND a registered symbol."*
**Four of 198 errors name no symbol at all:**

```
lorerunes/tests/test_posture.py:74:  Return type becomes "Any | None" due to an unfollowed import  [no-any-unimported]
lorerunes/tests/test_posture.py:313: Return type becomes "Any" due to an unfollowed import        [no-any-unimported]
lorerunes/tests/test_roster_parser.py:133: Argument 2 to "assert_every_roster_line_is_accounted_for" becomes "Any" …  [no-any-unimported]
lorerunes/tests/test_roster_parser.py:190: Argument 1 to "assert_roster_refusal_names_the_line" becomes "ExceptionInfo[Any]" …  [no-any-unimported]
```

They name a **decayed signature** (a local assert-helper), never the missing symbol that
caused the decay. Per-symbol discrimination is therefore **unbuildable** for them — the
ruling's falsifier (b) exactly. I applied its prescribed fallback and **tightened it**:
file-exact + code-exact **+ an exact declared COUNT**, because a bare per-file code
allowance is a *category*, and categories drift.

**RESIDUAL, stated plainly rather than disclaimed** (it is written into the registry beside
the entries): while these stand, a genuinely NEW `no-any-unimported` error in one of these
two files would be admitted **if and only if it replaced one of the existing two** — the
count cannot tell one from another. **Bounded at 2 lines × 2 files; discharges at packet
39's build.** The four `call-arg` errors need no residual: they DO name symbols
(`Unexpected keyword argument "http_client" for "build_mcp_server"`) and are registered as
`build_mcp_server.http_client` / `build_mcp_server.permission_resolver`.

### 6.3 · DECISION 3 — §B6's amended line, and what "green" now prints

§4 amends §B6 line 1 to *"full gates green under the pending-contract wrapper, with the
partition counts in the pasted tail"*. The tail's exact wording is mine, not the ruling's;
the ruling's illustrative form was *"7705+wave passed · 444 pending-build(packet-39/#296) ·
mypy 0 outside the registered set"*. I served a five-line block instead (registry / mypy /
pytest / self-destruct / VERDICT) because the illustrative one-liner cannot carry the
self-destruct coverage or the unchecked count, and a receipt that hides its own reach is the
shape this repo keeps getting burned by. **If the lead wants the one-line form for the
deploy record, it is a rendering change, not a logic one.**

---

## §7 · ONE IMPLEMENTATION — where I deliberately did NOT reuse, and the trigger

The wrapper **invokes `./scripts/typecheck.sh`; it never reimplements it.** `MEMBERS` and
the per-root `MYPYPATH` map are a registration site `CLAUDE.md` names explicitly, and a
second copy here would be the exact ONE IMPLEMENTATION defect this repo has the most
receipts against. Consequence: I parse mypy's **text**, because `typecheck.sh` has no
machine-readable mode.

**mypy DOES have one** — `-O/--output json` (read in `mypy --help`). Using it would mean
re-invoking mypy directly and cloning the runner's policy. So the parse is **bespoke by
design**, and it is gated by the count cross-check (§3.4 guard 1) rather than trusted.

**`keep_with_trigger` — the named trigger:** *the day `typecheck.sh` grows an opt-in
`--output json` mode (a one-line `leg=(... -O json ...)` branch), delete the text parser and
read the structured output.* That edit is in a shared canonical file and is a lead/operator
call, which is why I did not make it. **Escalated as decision 3.**

`stderr` is merged into `stdout` (`stderr=subprocess.STDOUT`) because the runner writes its
`typecheck: <leg> FAILED` lines to fd 2 while mypy writes to fd 1 — capturing them
separately destroys the ordering the leg accounting depends on. Ordering is safe because
each mypy process exits (flushing) before bash echoes its verdict.

---

## §8 · THE FULL TWO-LEG RUN

### 8.1 · Result — both legs, the whole suite, the post-fix build

`uv run python scripts/pending_contract_gate.py --registry /tmp/gw_reg_healthy.yaml`
(the healthy fixture — the real registry **plus** the 12th file of §6.1, so the run
exercises the multi-bound shape). **ALL THREE LEGS**, on the final build:

```
========================================================================
registry     : packet-39-pending-build (11 files, 45 symbols) · wave-c-c3-contract-in-flight (1 files, 6 symbols)
mypy         : 207 errors · 196 registered · 11 UNREGISTERED
ruff         : 0 violation(s) (zero-tolerance — the registry has no say over lint)
pytest       : 8786 passed · 478 failed registered · 36 failed UNREGISTERED
self-destruct: 43 symbol(s) import-checked absent · 8 UNCHECKED (owner not importable)
               unchecked: FakeMessageLedger.pending_traffic, build_mcp_server.http_client ×3, …
VERDICT      : FAIL — 49 unaccounted item(s)
EXIT=1
```

(The immediately preceding two-leg run, before the ruff leg existed, read
`514 failed, 8779 passed, 36 skipped, 3 xfailed in 506.25s` with
`mypy 209 · 198 registered · 11 UNREGISTERED` — the same partition, two errors of tree
drift apart. The `ruff : 0 violation(s)` line is the only structural difference, and it is
`0` only because §8.1b fixed it.)

**FAIL is the correct verdict, and every one of the 47 is named individually.** The
residuals decompose exactly, with no remainder:

| | count | where | why unregistered |
|---|---|---|---|
| mypy | 11 | `loremaster/tests/test_task_read_surface.py` | an **UNTRACKED** file another agent was mid-write in |
| pytest | 35 | same file | same |
| pytest | 1 | `loremaster/tests/test_surreal_harness.py` | a real RED, not mine — §10b / #308 |
| ruff | 0 | — | clean, as of §8.1b |

`11 + 35 + 1 + 0 = 47`, **and the tail says 49.** I do not get to hand-wave that; derived
from the run's own output (`grep -c '^SELF-DESTRUCT'` = **2**), the other two are:

```
SELF-DESTRUCT: registered symbol 'test_comms_tool.FakeAgentDatabase' (loremaster/tests/test_comms_footer.py) matched NO error line — the claim is discharged. DELETE the symbol from the registry.
SELF-DESTRUCT: registered symbol 'test_comms_tool.FakeAgentRegistry' (loremaster/tests/test_comms_footer.py) matched NO error line — the claim is discharged. DELETE the symbol from the registry.
```

**This is the self-destruct firing FOR REAL, unplanned, on live drift** — and it is a better
receipt than any of my injected controls. Between my `--derive` run and this one, another
agent's edit to `test_comms_footer.py` made two of its six missing symbols resolve. The
control-C fixture registry, written an hour earlier, still claimed them. **The instrument
noticed within one run, named both symbols, and refused to pass until they are deleted** —
which is exactly the property §3.3 leg 3 exists for, demonstrated by the world rather than
by me. (It fired on the *fixture* registry, not the committed one, because the committed
registry deliberately does not carry that file — §6.1.)

`11 + 36 + 2 = 49`. ✓

And the registered side is the number the ruling wanted served:
**`478 failed registered` = packet 39's 444 designed-RED pins + C3's 34.** The 444 is an
**independent reproduction of packet 39's INDEX row**, arrived at by a completely different
route (a file-attributed junit partition rather than that packet's own count).

**This is the §B6-line-1 receipt in its explicit form** — a green claim that says WHICH
failures were expected, WHOSE bound they belong to, and what remains unaccounted. Compare
the old form, *"full gates green"*, which at this tree state is simply unsayable.

⚠ **Not a deploy receipt for 04b-2 as it stands** — it is a demonstration that the
instrument works end to end. A deploy receipt requires the tree to settle (the in-flight
contract landing or being registered) and the §6.1 decision.

### 8.1b · ⚠ AND THEN THE WRAPPER TURNED OUT TO BE MISSING A GATE — #306, INSIDE #306's PIN

**`CLAUDE.md` names THREE commit gates: `scripts/typecheck.sh`, `uv run ruff check .`, and
pytest. My wrapper ran two of them** and would have served a verdict that reads exactly like
a full-gate receipt. **That is finding #306's own transferable lesson —** *"a close-out that
reports SOME gates green reads as ALL gates green"* **— reproduced inside the instrument
built to pin #306.** The ruling's §4 spells out only the mypy and pytest partitions, so
implementing it literally produced the omission; nobody would have noticed, because the
missing gate was believed clean.

**It was not clean.** `uv run ruff check .` was **RED AT HEAD**, 2 violations, in a
*committed, unmodified* file:

```
F401 [*] `subprocess` imported but unused
  --> scripts/lore_tool_name_currency.py:33:8
PLW2901 `for` loop variable `line` overwritten by assignment target
  --> scripts/lore_tool_name_currency.py:148:9
```

**A SECOND canonical gate red at HEAD with no ledger row, no owner and no re-open trigger —
#306's class exactly, in a different gate, found only because I went looking for the gate I
had skipped.**

**Both fixed** (the file is in my writable set, `scripts/**`; the fix is an unused-import
deletion and a loop-variable rename — no behaviour touched). `uv run ruff check .` is now
**clean repo-wide**, and `uv run pytest scripts/ -q` is `705 passed`.

**And the wrapper grew the leg**, so this cannot recur silently:

- `RuffOutputReader`, **zero-tolerance** — the registry has no say over lint. A pending
  *contract* is a real category (symbols a build will create); a pending *lint violation* is
  not, so ruff must simply be clean. Stated as a design decision so it can be overturned
  deliberately.
- `is_deploy_receipt` now requires **all three legs**, enforced not remembered
  (`test_a_deploy_receipt_requires_ALL_THREE_legs`, asserting both directions).
- with its own anti-vacuity guard, **measured**: `ruff check` over a path with no Python
  files prints `warning: No Python files found under the given path(s)` **then
  `All checks passed!` and exits 0** — byte-identical to a clean repo. Refused as a broken
  instrument, and a violation count cross-check against ruff's own `Found N errors.`
  mirrors the mypy leg's.
- **one stale test was deleted, deliberately**: `test_full_run_is_a_deploy_receipt` asserted
  that two legs sufficed. It was true of the old design and false of the new one — *a test
  written before a semantic change certifying the OLD world*, which this repo's law says to
  hunt for rather than leave green. Its successor asserts both directions, so nothing was
  lost. The deletion is recorded in-file at the site.

### 8.2 · ⚠ THE DEFECT THE FULL RUN FOUND, WHICH NO SMALLER RUN COULD HAVE

**The first full run reported `0 failed registered · 515 failed UNREGISTERED`.** The correct
answer was `444 registered`. Nothing about the run looked wrong — no crash, no warning, no
parse error, no anomaly in any other line of the tail. **Only the number was different, and
in the direction that reads as "the tree is in worse shape than you thought", which is
exactly the direction a reader believes.**

**Root cause, read in the installed source rather than guessed** (`_pytest/junitxml.py`):

```python
families = {
    "_base":        {"testcase": ["classname", "name"]},
    "_base_legacy": {"testcase": ["file", "line", "url"]},
}
```

`_NodeReporter.record_testreport` **does** set `attrs["file"] = testreport.location[0]` — and
then the **family filter drops it**, because pytest's default `junit_family` is `xunit2`,
which inherits only `_base`. `file` and `line` are *legacy* (`xunit1`) attributes. Verified
empirically both ways, and **`-n auto` is NOT the cause** (the attribute is missing in a
serial run too):

```
# default family
<testcase classname="scripts.test_mutation_proof.TestTheTwoWayDiff…" name="test_a_mutation…" time="0.697" />
# -o junit_family=xunit1  (+ -n 2)
<testcase classname="scripts.test_mutation_proof.TestTheTwoWayDiff…" name="test_a_mutation…" file="scripts/test_mutation_proof.py" line="139" time="0.684" />
```

**Two fixes, because the flag alone is a hope with a filename:**

1. the runner passes `-o junit_family=xunit1`, with the reason written at the call site;
2. **`JUnitReportReader` REFUSES any document whose failing testcases carry no `file`**, with
   a message naming the flag. Losing the flag is now a loud `BROKEN INSTRUMENT` (exit 2), not
   a silently wrong count. Pinned by
   `test_a_failure_with_no_file_attribute_is_a_broken_instrument`, and its sibling pins that
   the guard is scoped to FAILURES so a passing row needs no `file`.

**Why this belongs in the report rather than being quietly fixed:** it is a textbook
instance of this repo's own law — *"if step N silently no-opped, would step N+1 still print
something that reads as success?"* The junit document parsed. The XML was valid. The counts
were internally consistent. Every guard I had written passed. **The only thing that caught it
was knowing what the answer should be** (packet 39's INDEX row says 444) **and noticing the
observed set differed** — the same checked-expectation mechanism that is the only thing that
has ever caught a mutation proof landing in dead code. A wrapper built and tested only
against canned fixtures would have shipped this, green, forever.

**And it is an argument for the full run being non-optional:** every scoped run I did was
green, and the unit contract was green, *with this defect fully intact*.

---

## §9 · GATES ON MY OWN WORK

```
$ uv run ruff check .            # REPO-WIDE, and it was RED at HEAD until §8.1b
All checks passed!

$ uv run pytest scripts/ -q      # the whole scripts tree, incl. the file I lint-fixed
705 passed in 94.19s (0:01:34)

$ MYPYPATH=scripts uv run mypy scripts
Success: no issues found in 26 source files

$ uv run pytest scripts/test_pending_contract_gate.py -q
...................................                                      [100%]
35 passed in 0.15s

$ uv run pytest loremaster/tests/test_anchored_pattern_seam.py -q   # the pin I tripped (§4)
.........................                                                [100%]
25 passed in 1.92s
```

**The instrument is gated on arrival, with no `pyproject.toml` edit**: `scripts` is already
a `testpaths` entry (added by packet 44 / #188) and already a `MEMBERS` root of
`typecheck.sh`. So `test_pending_contract_gate.py` runs in the standard gate from its first
commit — it is not *"a guard nobody runs, a hope with a filename"*, which is the class both
of this repo's last two instruments shipped as. **My writable set included `pyproject.toml`
for exactly this; it was not needed and was not touched.**

---

## §10 · TREE PROVENANCE, and the git discipline

**No scratch copy was made and none was needed** (#140): every control mutated only `/tmp`
registry fixtures or one throwaway `scripts/_control_injected_defect.py` that the same block
deleted. Nothing in the repo was mutated and restored, so there is no restore to prove.
Receipt that the tree is as I found it plus my three new files:

```
$ git status --porcelain   # after all nine controls
?? scripts/pending_contract_gate.py
?? scripts/pending_contracts.yaml
?? scripts/test_pending_contract_gate.py
```

**No git write commands were run** — no add, commit, stash, or checkout (#189/#191; three
agents share this tree). The lead commits.

---

## §10b · FAILING TESTS OUTSIDE THIS TASK'S SCOPE — flagged, not buried

Filed as **finding #308**. On the final run (§8.1) the suite is `8779 passed / 514 failed /
36 skipped / 3 xfailed`, and the 514 decompose **exactly**, partitioned by the wrapper
itself rather than by hand:

| count | where | what it is |
|---|---|---|
| **444** | packet 39's 11 contract files | the designed-RED pins — **an independent reproduction of the INDEX row's 444** |
| 35 | `loremaster/tests/test_task_read_surface.py` | a wave-C contract, UNTRACKED and mid-write |
| 34 | `loremaster/tests/test_comms_footer.py` | wave C's C3 contract, pending its build |
| 1 | `test_surreal_harness.py` | **a real RED, not mine — see below** |

`444 + 35 + 34 + 1 = 514`. (The earlier, pre-fix run showed 515 — the 515th was
`test_anchored_pattern_seam.py`, **which was mine, and is FIXED**; see §4.) So exactly
**one** of 514 failures is neither a contract awaiting its build nor already closed.

**The one that is still red and that I may not touch:**

```
loremaster/tests/test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn
  ::test_the_harnesss_docstring_counts_are_the_DERIVED_counts
AssertionError: the harness docstring says 45 test files import it; 46 actually do.
```

**Not caused by this wave's wrapper** — confirmed, not assumed: that scanner walks
`loremaster/tests/*.py` only, and everything I wrote is under `scripts/`. Re-derived with an
independent AST walk: **46**, and the 46th is `loremaster/tests/test_task_read_surface.py`
(another agent's contract). **The fix is one character of prose** — `45` → `46` in
`_surreal_harness`'s docstring — but it is inside another agent's writable set, so it is a
FLAG with the exact edit attached, not an edit.

**There is 1 failing test unrelated to our present scope (514 total, of which 513 are
contracts committed RED ahead of their builds — 444 packet-39 + 69 wave-C). Do you want to
examine it more closely?**

---

## §11 · THE CONTROL RUNNER, VERBATIM

Pasted rather than committed (brief-base §1 option b) — it is a one-off harness whose
permanent form is the 32-pin contract in `scripts/test_pending_contract_gate.py`. It writes
its fixture registries by **deriving them from the real one**, never by hand-retyping.

### §11.1

```bash
#!/usr/bin/env bash
# Positive controls for scripts/pending_contract_gate.py — REAL end-to-end runs
# against the live tree at HEAD. Every control mutates only /tmp registries or a
# throwaway scripts/_control_*.py that is deleted in the same block.
#
# A probe never shown to fire is worthless: each NEGATIVE control below is paired
# with the HEALTHY control (C) proving the same instrument can say yes.
set -u
cd /home/ejprice/PycharmProjects/lore || exit 1

REAL=scripts/pending_contracts.yaml
run() {  # run <label> <registry> [extra args...]
  local label="$1"; shift
  local registry="$1"; shift
  echo "################ ${label}"
  uv run python scripts/pending_contract_gate.py --legs mypy --registry "${registry}" "$@" 2>&1 \
    | tail -25
  echo "EXIT=${PIPESTATUS[0]}"
  echo
}

# --- fixture registries, DERIVED from the real one (never hand-retyped) ------
uv run python - <<'PY'
import copy, yaml
from pathlib import Path
real = yaml.safe_load(Path("scripts/pending_contracts.yaml").read_text())

def dump(name, data):
    Path(f"/tmp/gw_reg_{name}.yaml").write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))

# C: healthy — additionally register wave C's own C3 contract (the 12th red file
#    this registry deliberately omits), so the whole observed set is accounted for.
healthy = copy.deepcopy(real)
healthy["bounds"].append({
    "id": "wave-c-c3-contract-in-flight",
    "owner": "packet 04b-2 wave C — C3",
    "reopen_trigger": "C3's build, this wave",
    "ruling": "CONTROL FIXTURE ONLY — not a real adjudication",
    "rationale": "control fixture for the healthy-path receipt",
    "files": [{
        "path": "loremaster/tests/test_comms_footer.py",
        "missing_symbols": [
            "FakeMessageLedger.pending_traffic",
            "loremaster.messages.PendingTraffic",
            "loremaster.server.COMMS_FOOTER_PREFIX",
            "test_comms_tool.FakeAgentDatabase",
            "test_comms_tool.FakeAgentRegistry",
            "type[AppContext]._comms_footer",
        ],
    }],
})
dump("healthy", healthy)

# B: an UNREGISTERED SYMBOL inside a REGISTERED file — drop lorerunes.Posture
#    from lorerunes/tests/test_posture.py. Its real errors must go unexpected.
narrowed = copy.deepcopy(healthy)
for bound in narrowed["bounds"]:
    for entry in bound["files"]:
        if entry["path"] == "lorerunes/tests/test_posture.py":
            entry["missing_symbols"] = [s for s in entry["missing_symbols"] if s != "lorerunes.Posture"]
dump("narrowed", narrowed)

# D1: a registered file that produces NO errors -> forced deletion.
green = copy.deepcopy(healthy)
green["bounds"][0]["files"].append(
    {"path": "scripts/mutation_proof.py", "missing_symbols": ["mutation_proof.NeverExisted"]}
)
dump("greenfile", green)

# D2: a registered SYMBOL that matches no error line -> forced deletion.
ghost = copy.deepcopy(healthy)
for entry in ghost["bounds"][0]["files"]:
    if entry["path"] == "lorerunes/tests/test_posture.py":
        entry["missing_symbols"].append("lorerunes.NeverMentionedAnywhere")
dump("ghostsymbol", ghost)

# D3: a registered symbol that NOW RESOLVES -> the bound is discharged.
alive = copy.deepcopy(healthy)
for entry in alive["bounds"][0]["files"]:
    if entry["path"] == "lorerunes/tests/test_posture.py":
        entry["missing_symbols"].append("loremaster.config.LoreConfig")
dump("liveimport", alive)

# D4: a registered file that no longer exists.
missing = copy.deepcopy(healthy)
missing["bounds"][0]["files"].append(
    {"path": "loremaster/tests/test_deleted_by_someone.py", "missing_symbols": ["a.b"]}
)
dump("missingfile", missing)

# D5: an unsymboled-code allowance whose declared count is wrong.
miscount = copy.deepcopy(healthy)
for entry in miscount["bounds"][0]["files"]:
    for allowance in entry.get("unsymboled_codes", []):
        allowance["count"] = 1
dump("miscount", miscount)
print("fixture registries written")
PY

run "CONTROL C (healthy path must PASS)" /tmp/gw_reg_healthy.yaml

run "CONTROL A0 (real registry at HEAD: the 12th file is deliberately unregistered)" "${REAL}"

echo "################ CONTROL A (injected error OUTSIDE the registry must FAIL)"
cat > scripts/_control_injected_defect.py <<'PY'
"""Throwaway control input for pending_contract_gate.py. Deleted immediately."""


def add(left: int, right: int) -> int:
    return left + right


VALUE: str = add("not", "ints")
PY
uv run python scripts/pending_contract_gate.py --legs mypy --registry /tmp/gw_reg_healthy.yaml 2>&1 | tail -20
echo "EXIT=${PIPESTATUS[0]}"
rm -f scripts/_control_injected_defect.py
echo "injected file removed: $(test -e scripts/_control_injected_defect.py && echo STILL-THERE || echo gone)"
echo

run "CONTROL B (unregistered SYMBOL inside a registered file must FAIL)" /tmp/gw_reg_narrowed.yaml
run "SELF-DESTRUCT D1 (registered file produces no errors)" /tmp/gw_reg_greenfile.yaml
run "SELF-DESTRUCT D2 (registered symbol matches no error line)" /tmp/gw_reg_ghostsymbol.yaml
run "SELF-DESTRUCT D3 (registered symbol now imports)" /tmp/gw_reg_liveimport.yaml
run "SELF-DESTRUCT D4 (registered file no longer exists)" /tmp/gw_reg_missingfile.yaml
run "SELF-DESTRUCT D5 (unsymboled-code count moved)" /tmp/gw_reg_miscount.yaml

echo "################ ALL CONTROLS DONE"
git status --porcelain
```

