# REPORT-contract-pkt42-1 — TEST CONTRACT for packet 42

brief-base v7 read

> **REVISION 11 — Phase-7's four fixture-reach defects + C1, and the TWELFTH found by asking.**
> All four leaks reproduced by me before fixing. **The twelfth: a credential in the dict KEY
> position** — `_scrub_value` recurses into values and copies keys through; no fixture in this
> packet could construct it.
> ⚠ **AND A FINDING ABOUT MY OWN CONTRACT: R11's blocker class was absent from EVERY COMMIT.**
> Mutation-proven in revision 3 (caught the adversary's 204/0 build), never landed — so it has been
> unprotected since `9ab5888` and no gate could tell, *because a test that does not exist does not
> fail*. Restored (§0.18.1).
> **One bound RETIRED, not kept green:** R38/R39 closed the structured `x-api-key` forms, so the
> KNOWN BOUND pinning them as leaking is deleted with a note — a pin outliving its hole is a lie.
> **Receipt: `417 passed, 0 failed`**, mypy `Success`, ruff clean.
>
> **REVISION 10 — REFACTOR's two gaps closed, and the EIGHTH is a CLASS, not an instance.**
> Both named gaps were *property right, reach short*. Asking that question of every instrument I
> own found **four scanners each carrying a PRIVATE copy of "which roots this packet governs"** —
> three gates and a corpus had silently stopped covering `lorerunes`. **#102 in my own
> instruments.** Fixed by ONE derived root list they all call, mutation-proven **both ways**
> (§0.17). **Receipt: `388 passed, 0 failed`**; mypy `Success` on both members; co-run `16 passed`.
>
> **REVISION 9 — R32's six defects fixed, a SEVENTH found by sweeping, and a FRESH
> satisfiability receipt at head `147cf2e`.**
> **The six are all address-drift, not property errors** — I fixed the addresses and kept the
> properties, per instruction. **`8 failed → 0 failed`** on the R32 set.
> **THE SEVENTH (§0.16.7): R29's own guard cannot see the member R29 mints.** The Containerfile
> copies `lorerunes`; `conformance_provenance.WORKSPACE_MEMBERS` is frozen at the old three, so
> the in-image run the ruling names as its instrument is blind to it — #131/#139 shape. Pinned
> ∀-derived from `pyproject.toml`, and it is **the one intentional RED I am leaving**: real
> remaining work with an authorised §9 row, not a contract defect.
> **Receipt: `1 failed, 381 passed`** — the 1 is that seventh. Co-run `16 passed`. mypy
> `Success: no issues found` on **both** members (the first time this packet has had zero).
>
> **REVISION 8 — R29/R30 applied; head moved to `672b813` mid-revision and the NAME IS RULED.**
> ⚠ **The package is `lorerunes` — PLURAL — not the `lorecommon` in my brief.** The operator ruled
> it at `672b813` while I was working; the authority file governs, so I adopted it. **It cost one
> line**, because the name lives in a single constant. My name opinion is therefore moot and I am
> not offering one (§0.15).
> **R30 fixed and SWEPT** — the sibling control had the same shape and got the same leg.
> **R29's shared-predicate pin is MUTATION-PROVEN against a behaviourally identical private copy**
> (§0.15), and building the reference **found a real weakness in my own pin**, which now has two
> legs instead of one.
>
> **REVISION 7 — adversary SUFFICIENT; R28's three closure corrections applied at head `1324140`.**
> **R28.1 was a real defect and the sharpest one in the packet: my attack corpus was measuring a
> COPY of the gate.** Fixed by DELETION — it now calls the real `_node_verdicts()` and
> `_is_secretstr_mint()` — and **mutation-proven the way it was found**: deleting v1's name leg
> from the real gate now reddens S1 and S3, where the corpus previously passed 13/13 with zero
> failures (§0.14). The copy had also **falsified a ledger row** — S6 is caught by the *mint* gate,
> not construction — so attribution is now DERIVED, not recorded. R28.2: S8 **shrank, did not
> dissolve** — 4 of 11 spellings leak, now pinned individually. R28.3: "2 retire" was **4** — I
> counted functions, not sites.
>
> **REVISION 6 — adversary FOURTH pass answered; rulings R26–R27 applied at head `77d70f7`.**
> **Naming both: R26 and R27 — §0.13.** R26 was a DESIGN ruling, so per repo law I built my own
> seam gate and **attacked it: 10 invented shapes, and my first design failed 6 of them.**
> v1 (header NAMES) → 6 breaks. v2 (construction SURFACE + type bypasses) → closed those, LOST
> four v1 caught. **v3 = the union**, and neither half is redundant. Four shapes remain uncaught
> and are LEDGERED with reasons and re-open triggers — one of them turned out to be covered by a
> different instrument entirely (measured, not assumed).
> **The attack corpus ships AS A TEST**, so the gate's reach is measured every run, not claimed once.
>
> **REVISION 5 — adversary THIRD pass answered; rulings R22–R25 applied at head `c05fde4`.**
> **Naming the two required: R22 and R23 — §0.12.**
> **R22's sibling sweep FOUND TWO SIBLINGS BEYOND THE SYNC TWIN** — `CalibrationEngine` and
> `MultiModelClaudeCounter`, neither previously pinned by anything (§0.12). The answer is a
> **∀ sweep derived from the tree**, not three more bespoke pins.
> **MP10 closed and mutation-proven:** `W-SYNCWIRE` scored **0 failures** before; it now scores
> **3**. Shape-B reference build on BOTH counters: **225 passed / 0 failed**.
> **R23:** the stale §9 row is rewritten — **and re-reading the whole report as R23 demands found
> the SAME stale-text class one section earlier, in my own §0.7**, now superseded in place.
>
> **REVISION 4 — adversary RE-RUN answered; rulings R19–R21 applied at head `abd86c3`.**
> Read: the fourth ruling wave and `REPORT-adversary-pkt42-1-rerun.md`.
> **Naming the two required: R19 and R20 — §0.10.** **MP5, the new BLOCKER, is closed and
> MUTATION-PROVEN:** `W-R10a` (owned arm left unauthenticated) produced a *byte-identical*
> failure set before; it now scores **2 failed**, with a sanity line confirming the mutation
> landed. Shape B reference build: **217 passed / 0 failed**.
> ⚠ **R20's own part-2 rationale is FALSE and I measured it** — §0.11. That is the third
> rationale in this chain falsified by measurement, and the second one I was handed.
>
> **REVISION 3 — adversary INSUFFICIENT answered; rulings R10–R18 applied at head `720e26a`.**
> Read: the third ruling wave, the packet spec's three slotted riders, and
> `REPORT-adversary-pkt42-1.md` in full. **Naming the three required: R10, R14, R17 — §0.7.**
> **Both BLOCKERs closed and MUTATION-PROVEN against the adversary's own wrong builds:**
> MP1's 204/0 leak build now scores **4 failed**; MP2's 204/0 build now scores **8 failed**.
> The frame correction is accepted — A18 was written around *unlabelled* text while the real
> bare-`str` credential is *labelled, in a header map, at an allowlisted site*.
>
> **CORRECTION RECEIPT (revision 2) — rulings R1–R8 applied; re-verified at head `506e595`.** Both sections re-read
> ("## Open rulings — RESOLVED" R1–R4, and "## Second ruling wave" R5–R8). Naming the three the
> lead asked for:
>
> * **R3** — `TestTheEnvFileFallbackIsNotAvailableToTheServer` (`test_secret_resolution_seam.py`):
>   no server-path `resolve_secret(...)` call site may pass an `env_file`; allowlist of exactly
>   one; checked **both ways**; detector control; **mutation-proven** (§10.4).
> * **R6** — `skills/` is now scanned by **both** AST gates, and the ruling's rider is discharged
>   with a receipt: `test_the_scan_reaches_the_skills_tree` proves the gate RUNS over that
>   ungated ground (§0.3).
> * **R8** — the scheme-preservation fix is pinned as a **production behaviour change**, and
>   pinning it uncovered that the defect is **a live credential LEAK for non-Bearer schemes**,
>   not a lost diagnostic (§0.4). The reference build then showed the naive fix **collides** with
>   the assignment labels (§0.5).
>
> R1/R5 folded out of decisions-needed. R7 applied (allowlist entry deleted). R4 unchanged.
> `search_score_survey.py` added to §9 as mandatory scope, citing lore finding **#233**.
> `506e595` (R6 size pre-approval) read: **not re-raising the size question, not trimming R6.**
>
> ⚠ **TWO ITEMS IN THE LEAD'S MESSAGE ARE NOT IN THE AUTHORITY FILE, and both were real work
> I had not done** — §0.6. (1) R5's whitespace-only symmetry, which **changes R2's ruled code
> snippet**. (2) R8's interaction-ORDER rider. Both now pinned.

- **state:** done-with-deviations
- **deviations:** (1) I EDITED two pre-existing test files (`test_logging_setup.py`,
  `test_secret_typing.py`) — required, because leaving corpse pins in place traps the builder
  between the spec and a test it may not edit (the C-DEF class); every edit is adjudicated below.
  (2) I created a shared fixture module `loremaster/tests/_logging_fixtures.py` rather than clone
  `_emit`/`_make_record`/the restore fixture into the new suite (ONE IMPLEMENTATION).
  (3) I did **not** migrate the ~8 pre-existing test files that construct
  `loresigil EmbeddingConfig(api_key_env=…)`; that is mechanical builder work and is enumerated
  in §9 so it is authorised rather than discovered.
- **Packages considered:** `python-dotenv` 1.2.2 → **replace**, specifically `dotenv_values`
  (read installed `dotenv/__init__.py` `__all__` + `dotenv.main.get_key` source + 11 measured
  parse cases; ruling R2 names the function, and the no-mutation pin is what enforces it);
  `python-decouple` → **declined by the operator** (probed and works; 3.8, uploaded 2023-03-01,
  no declared `requires_python`, vs Python 3.14 — maintenance, not capability);
  `pydantic-settings` 2.14.1 → **bespoke** (read installed
  `EnvSettingsSource._extract_field_info` source — env name derived from field name/alias at
  class-definition time; our sites pass the name as runtime data); `pydantic.SecretStr` 2.13.4 →
  **replace** (read `vars(SecretStr('abc'))`); `rich` 15.0.0 → **keep_with_trigger**;
  `detect-secrets` → **bespoke** (already rejected under #227 with receipts — not re-proposed).
  Full table in §2.
- **decisions-needed: ZERO open rulings.** All five §7 findings are ruled (R1, R5, R6, R7, R8);
  I hold no unresolved fork. **Two things the operator should still SEE, both discovered while
  implementing R8 and neither a question:** (a) the `Authorization:` defect is a **live credential
  leak today** for a short non-Bearer credential, and becomes one for *all* non-Bearer schemes the
  moment the catch-all is deleted — pinned, §0.4; (b) the obvious R8 fix **collides** with the
  `_ASSIGNMENT_RE` label list and silently redacts the `=` sign instead of the value — §0.5.
- **receipt pointers:** §0.1 (R3 instrument) · §10 (RED/GREEN, two satisfiability receipts, two
  mutation proofs) · §8 (adjudication table, 40 items) · §6 (adversarial pre-flight) · §3 (files).

---

## 0. What rulings R1–R8 changed in this contract

**Base `9c08cac` → `9600d84` → `251d112`.** Re-read both ruling sections; re-derived; four classes rewritten, two added, both AST gates widened.

| ruling | what I changed |
|---|---|
| **R1** — C2/C9 semantics ruled | My pins already encoded exactly this reading (never strip; unset/empty/whitespace-only fatal, variable named), so no assertion changed — but the `RULING-DEPENDENT (C2)` / `(C9)` markers are **gone**, replaced by `RULED BY R1`, and **§7.1 and §7.2 are struck from the open-rulings list**. Three open rulings remain, not five. |
| **R2** — unified `resolve_secret(name, env_file=None)` | `TestLoadApiKeyIsOneImplementationAdoptingDotenv` **deleted** and replaced by two classes: `TestResolveSecretIsTheUnifiedLookup` (13 pins on the shared lookup itself) and `TestLoadApiKeyRoutesThroughTheSharedResolver` (8 pins, incl. a **mutation proof** that `load_api_key` calls the shared resolver *and passes the env_file through*). The dotenv-import pin now targets **`loremaster/config.py`**, not `calibration/counting.py` — the earlier ruling would have put it in the wrong module. |
| **R2** — `dotenv_values`, never `load_dotenv` | **`test_reading_the_file_does_NOT_mutate_the_process_environment`.** This is the pin the ruling's "not `load_dotenv`" clause exists for, and it is the **receiver-blind** form: it asserts the OUTCOME (`os.environ` unchanged, including unrelated keys in the file) rather than banning a function name. The wrong build is nasty and passes everything else — `load_dotenv` exports every key in the file, so one calibration run that opts into a file silently arms `os.environ` for every later `resolve_secret(NAME)` **in the same process, including the server-path ones R3 exists to protect.** Plus `test_no_file_is_discovered_implicitly` (a `.env` in CWD must stay invisible — `load_dotenv()` with no args finds it by default). |
| **R3** — `.env` is NOT available to the server | **NEW: `TestTheEnvFileFallbackIsNotAvailableToTheServer`** (4 pins). See §0.1. |
| **R4** — A18 accepted, not waived | No change: A18 was already treated as *accepted-and-therefore-pinned-as-a-bound*, with the SecretStr matrix as the "strongest available control". R4's "not waived by being accepted" is exactly the paired-control design. |
| **R5** — blank var falls through (**against my recommendation**) | `test_an_empty_exported_variable_never_yields_an_empty_credential` (which accepted either branch) **replaced** by two pins that assert the ruled branch: `test_a_blank_exported_variable_falls_through_to_the_file` and `test_a_blank_exported_variable_is_still_fatal_when_the_file_also_misses`. Plus the rider — see §0.2. |
| **R6** — `skills/` IN SCOPE | Both AST gates widened (`_SCANNED_MEMBERS` in `test_secret_typing.py`; `_scanned_python_sources` in `test_secret_resolution_seam.py`), test files excluded on the new roots, the old "KNOWN BOUND: skills/ is unscanned" notes **deleted**, `probe_embed.py::_resolve_key` added to the retired-resolver pin, and an `UNWRAP_ALLOWLIST` entry seeded for its migrated unwrap. Rider discharged: §0.3. |
| **R7** — `comms_consumer_eval` migrates | Its `ENV_READ_ALLOWLIST` entry **deleted**, with the operator's reason kept in a comment where the entry was; added to the retired-resolver pin so its disappearance is asserted, not inferred from silence. |
| **R8** — fix the code, preserve the scheme | Six new pins in `TestTheLabelledPatternsSurviveTheDeletion`, including the leak pin. §0.4, §0.5. |

### 0.1 R3, the instrument (this is the confirmation the lead asked for)

`RESOLVE_SECRET_ENV_FILE_ALLOWLIST = {"loremaster/calibration/counting.py::load_api_key"}` — the
safe set is **one entry**, which is as small as an allowlist gets. Four pins:

1. `test_no_server_path_call_site_passes_an_env_file` — ∀ `resolve_secret(...)` call site in the
   scanned tree, a second positional argument **or** an `env_file=` keyword is an offender unless
   allowlisted. **Both spellings**, because a pin that knew one would be defeated by the other —
   this repo's most-repeated instrument failure.
2. `test_the_allowlisted_site_actually_passes_one` — **the control that makes pin 1 mean
   anything.** If the AST detection were wrong, `passes_file` would be `False` everywhere and pin 1
   would pass on a tree where every call site threaded a file. Asserts set equality against the
   allowlist, in both directions.
3. `test_the_server_entry_points_are_actually_in_the_scanned_population` — R3 names `server.py`,
   `scout.py`, `index/cli.py` by name; if a move took one out of the scan, pin 1 would be green
   while governing nothing.
4. `test_the_scan_finds_the_population` — positive control on the scan itself.

**Why a pin and not a convention, in the ruling's own terms:** every *behavioural* pin in the
module passes on a build where `server.py` helpfully threads a `--env-file` through to
`build_app_context`. The resolver still works, the value is still a `SecretStr`, the suite is
still green — and the container has quietly gained a credential source that is not its
environment. Nothing except this pin sees that.

**Mutation-proven** (§10.3): declared-RED set taken from `--collect-only` *before* the run; adding
`env_file=Path('.env')` to `scout.py::from_config` reddened pins 1 and 2 and named the offending
site. Restored byte-exact.

### 0.2 R5 — my FIRST recommendation was declined, my SECOND was adopted

⚠ **I made two different recommendations at two different times, and an earlier draft of this
section conflated them into one sentence — the same two-populations defect this report keeps
finding elsewhere.** Precisely:

- **§7.2, before R2 existed:** *"blank is always fatal, the file is never consulted."*
  **DECLINED by R5**, and the inventory records that decline.
- **§0.2, after R2's snippet landed:** *"follow the CODE — blank falls through"*, with the
  argument that R3 makes it harmless. **ADOPTED by R5**, which the lead confirms in terms.

So R5 both declined me and agreed with me, about different proposals. The operator's stated
reason — *an operator blanking a variable to force the file is a real calibration workflow* — is
better than my first attempt, and my second attempt's key point (R3 makes the fall-through
unreachable from any production path) is the one that carried.

**The rider matters more than the ruling**, and it is the half a builder drops: *"emptiness is
fatal at the END of resolution, not at each source; a pin whose message claims 'empty is always
fatal' would be a false gate."* That is the P2 2026-07-14 class — a message promising a check the
assertion does not perform, which let a wrong build pass 399/399. So:

- The `test_a_blank_variable_is_fatal_on_the_serverpath` comment now says *scoped: no `env_file`
  supplied, so resolution ends at the environment* — it does **not** claim unconditional fatality.
- `test_a_blank_value_is_fatal_wherever_it_came_from` is reworded to the end-of-resolution form.
- **`test_the_emptiness_rule_is_stated_honestly_and_not_overclaimed`** mechanises the rider: it
  scans this module's own source for any message making the unqualified claim. A test about the
  TESTS, deliberately — the rider is about what the pins *say*, and nothing else checks that.
  (CLAUDE.md: "if you implemented the clause BEFORE the 'and pin it like this' phrase and not
  after, you are not done.")

### 0.2b TWO ITEMS THE AUTHORITY FILE DOES NOT CARRY — and one changes the ruled code

I diffed the lead's message against `REMOVED-BEHAVIOR-INVENTORY.md` at head rather than assuming
they matched. Two instructions exist only in the message, and both were genuinely undone work.

**(1) R5's whitespace-only symmetry — and it makes R2's ruled SNIPPET wrong.** The message says
*"whitespace-only should behave the SAME as empty on the file-enabled path."* The inventory's R5
says only "a blank exported variable falls through" and never settles it. **R2's snippet, which is
the thing a builder will copy, does not implement it:**

```python
if not value and env_file is not None:      # " " is TRUTHY -> does NOT fall through
```

Under the snippet as written, `ANTHROPIC_API_KEY="   "` skips the file and dies at the emptiness
check — the opposite of the ruling. Implementing R5 as ruled needs:

```python
if (not value or not value.strip()) and env_file is not None:
```

`test_a_blank_exported_variable_falls_through_to_the_file` is now parametrised over **empty /
single space / tabs+spaces**, and its fatal-when-the-file-also-misses twin over two of them, so
the symmetry holds in both directions. **Flagged rather than silently fixed: the snippet in the
inventory should be corrected, because it is what gets copied and it currently contradicts R5.**

**(2) R8's interaction-ORDER rider.** The message adds *"including the interaction ORDER between
the two patterns"*. Pinned as `test_the_two_patterns_INTERACT_in_the_right_order` — as an
**outcome**, not a mechanism: the wrong build's fingerprint is DOUBLE redaction
(`Authorization: ***REDACTED*** ***REDACTED***`, which is exactly what base produces), so the pin
asserts `scrubbed.count(REDACTED) == 1`. One credential in, exactly one sentinel out.

**On the rider's other half, I did something different from what was asked, and here is why.** The
message says *"a build that fixes the render by disabling `_ASSIGNMENT_RE`'s `authorization` label
entirely is a wrong build — pin against it."* I pinned the **behaviour** that protects, not the
label's location — because §0.5 Trap 3 measured that the only design satisfying every property
here **does** move `authorization` out of `_ASSIGNMENT_RE` into a dedicated scheme-aware pattern,
and the reference build doing exactly that goes **204 passed / 0 failed**. Two different builds
hide behind one phrase:

| build | verdict | caught by |
|---|---|---|
| drop the label, replace it with nothing | **WRONG** — `authorization=<tok>`, `Authorization: <tok>` and `Authorization: Basic <creds>` all un-redact | `test_disabling_the_authorization_label_does_not_satisfy_R8` (3 doors) + the leak pins |
| move the label into a dedicated auth-header pattern | **CORRECT** — every property holds and the unknown-scheme leak closes | passes all of the above |

A pin on the label's *location* would have failed the correct build. So the rider is honoured by
`test_disabling_the_authorization_label_does_not_satisfy_R8`, which fails every build that drops
the protection and passes every build that relocates it. **Flagging the deviation rather than
quietly doing it my way.**

### 0.7 REVISION 3 — R10–R18, and the frame correction that caused them

**The adversary was right and the diagnosis is accepted verbatim.** I wrote A18's bound as *"an
UNLABELLED secret in free text"*, so every carrier and every pin was built around unlabelled
text — while the credential that actually exists as a bare `str` in this tree is **labelled**
(`x-api-key`), inside a **header map**, at the very site my own `UNWRAP_ALLOWLIST` blessed. Both
defences missed it structurally: `_ASSIGNMENT_RE` needs the label *immediately* adjacent to the
separator and a mapping repr puts a quote between them, while `_scrub_value` scrubs keys and
values independently so they never adjoin at all; and the `SecretStr` control cannot apply
because that value is a bare `str` **by design** — my allowlist entry was the licence to make one.

| ruling | what changed here |
|---|---|
| **R10** 🔴 | **`TestNoProductionObjectRetainsAnUnwrappedCredential`** — 8 pins. The SOURCE fix, not the redactor: the counters must stop retaining the unwrapped header dict. Drives the **real production object** through the **real production sink** in both formats, plus a wire pin (`x-api-key` must still arrive — "don't retain it" is otherwise satisfiable by breaking auth), plus a leak-detector control, plus the structured form pinned as a **KNOWN BOUND with a re-open trigger** since R10 deliberately declined the redactor fix. |
| **R11** 🔴 | **`TestScrubValueRecursesIntoContainers`** — 9 pins, ∀ container shape, tuple-type preservation, end-to-end in both formats. The discriminating leg is a **LABELLED bare `str`**: not masked by a type, not an accepted bound. |
| **R12** | `interpolate=False` pinned byte-exact over four `$` shapes including the unset-`${VAR}` case that **shortens** a credential. |
| **R13** | §9 corrected — see below. |
| **R14** | R6's migration half **reversed**; the gate half untouched. |
| **R15** | real-then-blank duplicate key → fatal, pinned as the dual of C6. |
| **R16** | the `Authorization: Basic` pin named as the same-commit rider's mutation proof (§0.8). |
| **R17** | allowlist **10 → 5** (+1 loresigil = 6); `NOT_A_SECRET` category **retired**. |
| **R18** | runtime-red compliance stated per pin (§0.9). |

**The generalisation I am taking from this, beyond the two pins:** for any property where the
`SecretStr` leg is saved by the TYPE and the bare-`str` leg is an accepted bound *asserted to
leak*, **the paired control is non-discriminating** — it passes either way. That is the one blind
spot in a design the adversary otherwise praised, and it is exactly where A19 lived. Wherever that
shape recurs, the discriminating leg is a **labelled bare `str`**.

**R10's design fork, surfaced not guessed** (the ruling handed it back to me): `AsyncClaudeTokenCounter`
accepts an **injected** client it does not own, so "bake the headers into the client" is ambiguous
there. Two shapes work — mutate the injected client's `.headers`, or send headers per-request.
I refused to pick and flagged it for the operator.

> ⚠ **SUPERSEDED — READ §0.10.** Ruling **R19 CLOSED this fork: shape B (per-request) is
> MANDATED and shape A is forbidden** (`W-SHAPEA`, 2 RED). The sentence above describes the
> state before that ruling and is kept only because §0.10 refers back to it. **Nothing in this
> paragraph is a live instruction.** — Found by re-reading my own report against R19–R21 as
> R23 requires, not just the §9 rows it named: the same stale-text class, one section earlier.

### 0.8 R14 and R16 — a reversed instruction and a commit-boundary rider

**R14 reverses R6's migration half, and the reversal is right.** `probe_embed.py` is deliberately
stdlib-only, runs under `sys.executable` while loremaster code in the same skill runs under
`_loremaster_python()`, and `lore_deploy.py` **branches on its exit codes** — importing
`loremaster.config` would turn a clean exit 4 into a `KeyError` traceback read as exit 1. So:
- the `UNWRAP_ALLOWLIST` entry I seeded for its migration is **deleted**;
- it is **removed** from the retired-resolvers pin (its `_resolve_key` stays);
- `ENV_READ_ALLOWLIST` gains it as a **LEDGERED DESIGN DECISION** with the deploy boundary as its
  reason and a **named re-open trigger** — *the day it runs under `_loremaster_python()`*;
- **`test_probe_embed_keeps_its_own_resolver_as_a_LEDGERED_duplicate`** goes RED if a future agent
  "helpfully" consolidates it, and the message explains why not;
- **`test_probe_embed_imports_nothing_outside_the_stdlib`** pins the boundary itself, derived from
  `sys.stdlib_module_names` rather than a hand list.
- B3's bug is fixed **in place**: `if not key` → `if not key or not key.strip()`, §9.

**R6's gate half is unchanged and stands** — the adversary reproduced its receipt (93 files
scanned, `probe_embed.py` present).

**R16 (#235) — the same-commit rider.** The deletion of `_TOKEN_RE` and the labelled-pattern fix
are **ONE commit**; a tree with the deletion but not the fix must never exist even transiently,
because that is the tree a bisect or a revert lands on. **`test_a_NON_BEARER_AUTH_SCHEME_DOES_NOT_LEAK_ITS_CREDENTIAL`
IS the mutation proof for this rider** — named as such here, and already measured: the adversary's
W-DEL build (deletion, no fix) scored **11 failed**, every one an R8 pin.

### 0.9 R17 re-derived, and R18 stated rather than inferred

**R17 — the rider's "its author got 1 of 5 sites wrong" does NOT reproduce.** Re-derived at
`720e26a`: all five are genuine username round-trips (`index/cli.py:112`, `server.py:6752`,
`scout.py:728`, `search_score_survey.py:696`, `snapshot_gc.py:332` — each reading a `*user_env`),
and **all five password siblings verifiably STAY wrapped** (`:113`, `:6753`, `:729`, `:697`,
`:333` — none calls `get_secret_value`). The dangerous direction the rider warns about does not
occur. **What IS materially different, and is probably the grain of truth: `snapshot_gc.py:332` is
the only one of the five whose `KeyError` is CAUGHT** — `main` renders it into a clean
`_EXIT_ERROR` message (`server.py`'s single handler is at line 464, nowhere near 6752). De-wrapping
there must keep raising a *naming* `KeyError` or the CLI's error message silently degrades. Noted
in §9.

Counts, stated as two populations because conflating them is this packet's recurring defect:
**5 of the 10 pre-existing entries retire; 1 new loresigil seam arrives; final = 6.** The
`NOT_A_SECRET` category is **retired entirely** — a category with no members is a door left open —
and `test_no_username_round_trip_survives` pins the property rather than the count.

**R18 — every pin in this contract has a RUNTIME red, never a type-gate red.** Stated explicitly
rather than left inferred: every satisfiability receipt (§10.2, §10.3) and both blocker mutation
proofs (§10.5) are **live `pytest` runs with pasted pass/fail counts**. No pin anywhere in these
five files is demonstrated by a mypy error. The mypy deltas reported in §10.6 are *side effects*
of the unbuilt API, never the evidence for a pin. Where a pin's only possible red would have been
a type error, it is paired with a runtime assertion — e.g. `api_key` field absence is pinned by a
`ValidationError` with an inspected `loc`, not by mypy's `call-arg`.

### 0.10 REVISION 4 — R19 (the #107 shape) and R20

**R19 — MP5 was the #107 shape, and my pin was on the wrong arm.** The wrong build applies R10's
fix to the **injected** client and leaves the **owned** `httpx.AsyncClient` unauthenticated. It
produced a *byte-identical failure set to the correct build* — the adversary's `diff` was empty —
because my only wire pin **injected** a client. Re-derived: **both production constructions use
the OWNED arm** (`calibration/engine.py::_default_counter_factory` and
`scripts/calibration_baseline.py` both call `AsyncClaudeTokenCounter(api_key, model=…)` with no
client). *The arm I tested was the arm production never uses.*

R19 rules the fix **structurally — shape B, per-request headers** — so there is no owned-vs-injected
arm to fix one of and forget the other. Four pins now carry it, and they are deliberately split so
that satisfying one by breaking another is impossible:

| pin | what it forbids |
|---|---|
| `test_the_OWNED_client_arm_is_authenticated` | **the MP5 blocker** — the arm production actually uses, patched at `counting.httpx.AsyncClient` so the owned client's transport is observable |
| `test_the_INJECTED_client_arm_is_authenticated` | the other arm, forced separately — ∀ arm, never one standing in for both |
| `test_no_credential_is_baked_into_either_CLIENT` | the shape-B mandate itself: the credential may not live on either client's header map |
| `test_an_injected_client_is_not_mutated` | shape B's other consequence — the caller owns that client; shape A fails this, which is why the ruling chose B |

**The fork I surfaced in revision 3 is now CLOSED by ruling, not by me** — and note the sequence
worked as intended: I refused to pick, the adversary measured both shapes, the operator ruled the
one that is immune. My old fork-straddling pin is narrowed to a retention check.

**R20 part 1 — R10's rationale was false and is corrected.** I had written, from the ruling, that
the source fix *"removes the only object in the tree that held a labelled credential as a bare
`str`"*. It does not: after R10 the credential lives in an `httpx.Headers` map. Re-derived here
rather than inherited — httpx **0.28.1**, reading `Headers.__repr__` → `_obfuscate_sensitive_headers`
→ `SENSITIVE_HEADERS`, then measured:

```
Headers({'x-api-key': 'sk-ant-SECRETVALUE', 'authorization': '[secure]', 'proxy-authorization': '[secure]'})
```

**httpx obfuscates `authorization` and `proxy-authorization` only.** R10 cited `tei.py` as
precedent and **that precedent does not transfer**, because `tei.py` authenticates with
`Authorization: Bearer` and this counter with `x-api-key`. The docstring now says so, with the
measurement in it.

### 0.11 ⚠ R20's OWN part-2 rationale is also false — measured, and it changes the pin

R20 part 2 states that `_ASSIGNMENT_RE` fires inside `x-api-key` *"so a rendered `Headers` repr
**would** be scrubbed by a pattern this packet keeps"*. **It would not.** Measured with the
labelled patterns alone (catch-all removed, which is the world after this packet):

```
x-api-key: <k>                    -> x-api-key: ***REDACTED***      COVERED
Headers({'x-api-key': '<k>'})     -> LEAKS
{'x-api-key': '<k>'}              -> LEAKS
{"x-api-key": "<k>"}              -> LEAKS
```

The reason is the one the adversary itself established in MP1: **there is a QUOTE between the
label and the colon**, and `_ASSIGNMENT_RE` requires `\s*[=:]\s*` *immediately* after the label.
The ruling contradicts its own earlier finding. Had I pinned the repr form as covered, it would
have been RED forever against every correct build.

So I honoured R20's **intent** — make the coverage explicit so a future narrowing reddens — while
pinning what is true:

- **`test_the_x_api_key_HEADER_LINE_form_is_covered_by_a_kept_pattern`** — the form that IS
  covered, pinned exactly, so narrowing `\bapi[_-]?key\b` goes RED.
- **`test_the_STRUCTURED_x_api_key_form_remains_a_KNOWN_BOUND`** (3 shapes) — the forms that are
  NOT, pinned as a bound with the corrected rationale and the adversary's **measured trigger**
  kept and sharpened: *the day a lore client authenticates with a header httpx does not
  obfuscate* is **TODAY** for `x-api-key`, so the live condition is **"if an httpx error carrying
  request headers is ever logged on the Anthropic path, this bound becomes a leak"** — and the
  fix then is at the SOURCE, never by widening the pattern.

**Tally worth stating once:** across four revisions, **three rationales handed to me have been
falsified by measurement** — R2's snippet (interpolation), R10's "only object" claim, and now
R20's "would be scrubbed". Each was found by measuring rather than by reading. That is the habit
this packet keeps rewarding, and it is the same habit that surfaced #233.

### 0.12 REVISION 5 — R22 (siblings) and R23 (my own stale text)

**R22 — the sync twin, and the generalisation I was asked to take instead of a fourth patch.**
`W-SYNCWIRE` — the sync `ClaudeTokenCounter` posting with no auth header — scored **0 failures**,
because both wire pins targeted the async class. Three times now one shape has bitten this packet:
the `load_api_key` twins, the owned-vs-injected arms, the async/sync twins.

So I ran the sweep **before** writing the pin, derived from the tree — every class whose `__init__`
takes an `api_key`, and every function that builds an auth header. **It found two siblings beyond
the sync twin, neither pinned by anything:**

| sibling | why it was invisible |
|---|---|
| `loremaster.calibration.engine.CalibrationEngine` | takes `api_key`, retains it as `self._api_key`, hands it to the async counter. Safe **by type** today — and nothing was checking that, so an early unwrap would have been silent. |
| `token_survey.MultiModelClaudeCounter` | builds **N** sync counters over **one shared** `httpx.Client`. Under shape A that is a third arm with N writers to one header map; under shape B it is inert. |

A third hit was inspected and **scoped out with a reason**: `merge_mcp_json._desired_entry` emits a
literal `Bearer ${VAR}` **template** into a config file for Claude Code to expand — it never holds
a credential.

The instrument is therefore `TestEveryAuthHolderSiblingIsSwept`: a **∀ sweep derived from the live
tree** (with an anti-vacuity control and an asserted roster), so the sibling nobody has thought of
yet is covered. Plus `TestTheSyncCounterTwinIsAuthenticatedToo` — deliberate mirrors of all four
async legs, not a reduced set, and a two-model `MultiModelClaudeCounter` leg (one model cannot
distinguish *"each counter authenticates"* from *"the last writer wins"*).

**Mutation proof:** `W-SYNCWIRE` **0 → 3 failed** (both arms plus the MultiModel sibling), sanity
line `SANITY sync wire x-api-key: [None]` confirming it landed.

**R23 — the stale §9 row, and the same defect one section earlier in my own report.** §9's R10 row
still said *"bake it into the httpx client … either shape passes"* — measured false under R19
(`W-SHAPEA`, 2 RED); a builder following it verbatim writes the forbidden shape. Rewritten to
mandate shape B on **both** counters and `MultiModelClaudeCounter`.

⚠ **R23 said re-read EVERY row, not just the amended ones — so I re-read the whole report, and
found the same class in §0.7**, which still described R10's fork as *"either passes"*. R19 closed
that fork two waves ago. It is now marked **SUPERSEDED in place** rather than deleted, because
§0.10 refers back to it. I audited all 16 §9 rows; the other 14 are current. **The lesson I am
taking: a superseding ruling obsoletes text wherever it lives, and "the rows I touched" is not the
search space — the whole document is.**

**R24** — the three rows saying *"→ a plain env read"* were **explicitly wrong** (2 RED, measured:
a new unlisted `os.environ` site reddens the entry-point gate). All five now name the mechanism: a
**non-secret sibling in `loremaster/config.py`** (`resolve_config_value(env_var_name) -> str`),
which keeps the read inside the one module the gate permits **and** preserves the naming `KeyError`
that `snapshot_gc.py::main` renders — the caveat I found in revision 4 is exactly why the shared
sibling is right and five inline reads are not.

**R25** — `test_calibration_counting.py` named as a **required co-run**: R19's shape change is
invisible to this packet's own five suites, and only that file exercises the counters' request path.

### 0.13 REVISION 6 — R26 (the typed seam, and the attack on my own design) and R27

**R26 — the name-list at its seventh address, and the operator ruled the DESIGN.** Three of my
instruments all keyed on NAMES: the sibling sweep on `"api_key" in parameters`, `SECRET_PARAM_NAMES`
on `{"password","api_key"}`, and `UNWRAP_ALLOWLIST` on a `.get_secret_value()` call a bare `str`
never makes. `W-PARAMNAME-BARE` walked through all three.

⚠ **Stated the way the ruling requires: the GAP is real, the LEAK is not.** `bearer_token` exists
in this tree only as `auth.py::_bearer_token`, an INCOMING token; `auth.py` has zero logger calls;
per M1 that local renders as `self._verifier.verify(token)` with no value. **No pin I wrote implies
a live leak** — the wrong build is constructed.

The seam is pinned per package (`loremaster`, `loresigil`) — **two seams, because #222 stands and
the enforcement is the TYPE SIGNATURE, not a shared implementation**; and the runtime-rejection pin
exists because **#221 says a type-gate red is not a demonstrated pin** (mypy is blind through
`dict[str, Any]`; the SecretStr migration once passed it at zero delta with 119 tests broken). Scope
is outgoing only — `auth.py` is excluded by name in the gate, per constraint 2.

#### The attack — what I invented, and what broke

Repo law: a property to INVENT must be attacked by its author before shipping. Packet 01's v1 and v2
failed because nobody required that. So I wrote 10 shapes and ran them against my own gate:

| # | shape | v1 (names) | v2 (surface) | **v3 = union** |
|---|---|---|---|---|
| S1 | inline `{"x-api-key": k}` | ✅ | ✗ | ✅ |
| S2 | **computed name** `"x-api" + "-key"` | ✗ | ✗ | **✗ ledgered** |
| S3 | module constant `HDR = "authorization"` | ✅ | ✗ | ✅ |
| S4 | `req.headers["authorization"] = …` | ✅ | ✅ | ✅ |
| S5 | **`httpx.Client(auth=BasicAuth(...))`** | ✗ | ✅ | ✅ |
| S6 | **`build_auth_headers(SecretStr(raw))`** | ✗ | ✅ | ✅ |
| S7 | `{"-".join(["x","api","key"]): k}` | ✗ | ✗ | **✗ ledgered** |
| S8 | credential in URL query `?api_key=` | ✗ | ✗ | **✗ — covered elsewhere** |
| S9 | logging the seam's own output | ✗ | ✗ | **✗ ledgered** |
| S10 | the correct seam (control) | — | — | correctly silent |

**My first design failed 6 of 10.** The two that mattered most were ones I would not have guessed
without building the attack:

* **S5 — `httpx.Client(auth=…)`.** Verified against the installed httpx: `auth` is a real
  constructor parameter and `BasicAuth.auth_flow` builds an `Authorization` header **with no header
  name anywhere in our source**. An honest, documented API that no name-keyed gate can ever see.
* **S6 — `SecretStr(raw)` at the call site.** The type only proves the value is wrapped *at the
  call*, never that it was never bare. **The typed seam alone does not close its own bypass** — so
  the MINT is gated too. Cost measured before adopting it: **6 production sites, of which 4 retire**
  with the resolver consolidation (`counting.py:77,84` + `token_survey.py:731,738`).
  ⚠ **RULING R28.3 — I first wrote "2 of them retire". That counted FUNCTIONS, not
  SITES**: two functions, four call sites. Two populations in one number — M3's
  13-vs-10 shape, and the **fourth instance in this packet alone**.

**The four survivors are LEDGERED, not hidden**, each with a reason and a re-open trigger. S2/S7
are computed header names: no honest developer writes them, closing them costs false positives on
every dict built near a client, and the trigger is *the day any production module computes a header
name*. S9 is covered for every production holder by the retention and shape-B pins.

⚠ **RULING R28.2 — I over-claimed S8 and the correction matters.** I wrote that it "dissolved",
on the strength of **one** spelling. Measured across eleven:

```
COVERED: ?api_key= ?api-key= ?apikey= ?apiKey= ?token= ?secret= ?password=
LEAKS:   ?key=  ?access_token=  ?auth=  ?x_api_key=
```

**The residual SHRANK; it did not dissolve.** A credential in a query string is covered only when
the parameter happens to be spelled like one of `_ASSIGNMENT_RE`'s labels. It is now pinned
**spelling by spelling** (`test_the_query_parameter_residual_is_pinned_spelling_by_spelling`, 11
parametrised rows) so the boundary is a measured fact rather than a sample, and widening the label
set moves the table with it. *A residual claimed closed on a sample of two is the same error class
as a count derived from one population — which is R28.3, one paragraph up.*

**The corpus ships as `TestTheSeamGateWasAttackedByItsOwnAuthor`** — a parametrised test asserting
the gate's verdict on each shape, plus an anti-vacuity check (a refactor flipping every expectation
to "uncaught" would otherwise pass) and a control that the correct seam is *not* flagged. The
gate's reach is therefore **measured on every run**, and a later narrowing reddens.

**R27 — both honesty halves fixed, and they were fair hits.**

1. The sweep's docstring claimed *"DERIVED from the live tree, never a hand-list"* while being a
   hand-list of six — the served-English class, in the docstring of an instrument built to stop
   hand-lists. **I derived it** (`pkgutil.walk_packages` over both packages + `scripts/` by
   filename) rather than deleting the claim, so a module added next year is swept without anyone
   remembering.
2. `CalibrationEngine` was **rostered but skipped** at construction, and `constructed >= 4` was
   cleared by the other six, so the skip was invisible. **The floor is replaced by a totality
   check**: every rostered holder must be constructed, or the pin names which one it could not
   build and why. A count that passes while a member is silently dropped is exactly the vacuity
   this instrument exists to prevent — the same shape I had been catching in others.

### 0.14 REVISION 7 — R28.1, the defect I am most glad was caught

**My attack corpus tested a copy of the gate.** `_gate_flags()` re-implemented `_node_verdicts()`
inline instead of calling it. The adversary proved it by mutation: delete v1's name leg from the
**real** gate, and `_node_verdicts` stops flagging S1 — while `_gate_flags` still returned `True`,
the corpus passed **13/13**, and the file added **zero** failures.

**The instrument I built to measure the gate's reach every run was measuring a duplicate's reach.**
That is #102 — ONE IMPLEMENTATION — *inside the instrument built to prevent that class*, and it is
exactly what "prove sharing by mutation" exists to catch: change the shared thing, and a caller
that keeps working is a private copy wearing the shared name. **I wrote a mutation proof for the
seam and did not write one for the corpus**, because I was treating the corpus as documentation
that happened to run. It was an instrument, and instruments get proved.

**Fixed by DELETION, not by re-syncing** — a synchronised copy is the same defect with a
maintenance ritual attached. `_instruments_catching()` now calls the production predicates
directly, and `test_the_corpus_calls_the_REAL_gate_and_not_a_copy` asserts structurally that it
still does, so the copy cannot come back quietly.

**Mutation proof, run the way the defect was found** (declared-RED ids from `--collect-only`
before mutating; target-absent assertion on the edit):
```
MUTATION LANDED: _node_verdicts no longer has the name leg
2 failed  — test_the_real_gates_verdict_on_each_invented_shape_is_unchanged[S1]
            test_the_real_gates_verdict_on_each_invented_shape_is_unchanged[S3]
```
**13/13-and-zero-failures → 2 failed.** Restored byte-exact (md5 `1885138f…`).

**The second-order damage was worth more than the fix, exactly as ruled.** The copy had falsified a
ledger row: I recorded S6 as caught by the construction gate; the real gate says it is caught by the
**mint** gate — a different function. Outcome safe, **attribution wrong, and undetectable while a
copy stood in for the gate**. So the corpus no longer stores a boolean: it stores the
**attributing instrument**, re-derived against the real gates, and
`test_each_instrument_catches_at_least_one_shape` fails if either gate silently stops contributing.
Every row was re-derived; S6 was the only wrong one.

**On R28.3, and I want to name the pattern rather than just fix the number.** "6 sites, 2 retire"
counted **functions** where the sentence said **sites** — 6 sites, **4** retire. That is the
fourth two-populations error in this packet: M3's 13-vs-10, the `resolve_secret` 13-raw-vs-7-distinct
threshold, the "1 of 5 wrong" that did not reproduce, and now this. **Every one of them appeared in
a sentence I wrote while being careful about exactly that class.** The instrument that has actually
caught them is never vigilance — it is *deriving the number in the test instead of asserting it in
prose*, which is what the corpus now does for attribution and what the spelling-by-spelling table
now does for S8.

### 0.15 REVISION 8 — R30's false pass, and R29's shared package

**R30 — my pin was green for the wrong reason, and its own sibling already had the guard.**
`test_a_blank_credential_is_rejected_AT_THE_API_KEY_FIELD` asserted only `error["loc"] ==
("api_key",)`. Before the field existed, `api_key` was an *unknown* field, so `extra="forbid"`
raised `extra_forbidden` — **whose `loc` is also `('api_key',)`**. It passed on a rejection with
nothing to do with blankness.

Fixed with the `type` leg, and **swept rather than patched**: `test_a_differently_broken_payload_is_
rejected_for_a_DIFFERENT_reason` asserted `loc` only in exactly the same shape, and now carries the
same guard. With the stub in the tree the fixed pin RED-s on `single-space` and `whitespace-only`
and passes on `empty` — **which is precisely R29's defect made visible**: `min_length` measures
length, so `' '` is accepted. The pin now discriminates in the direction that matters.

⚠ **The method bound is worth more than the fix, and the lead named it correctly.** Five adversary
passes could not catch this because *the contract was never graded against a tree where the field
existed*. **A contract graded against the OLD world can hold a pin that only the NEW world
falsifies.** That is a structural limit of contract-first, not a lapse — and the swept sibling is
the only mitigation I can offer from inside the contract phase.

**R29 — the shared package, and the name that changed under me.**

The name in my brief was `lorecommon`; the operator ruled **`lorerunes`, plural**, at `672b813`
mid-revision. I took the authority file over the brief and adopted it. **It cost one line**, because
I had put the name in a single constant — the one decision in this revision that paid for itself
within the hour. I then swept for strays: a blanket replace mangled the one legitimate *historical*
mention into nonsense (`"from the lead's proposed lorerunes to the operator's ruled lorerunes"`),
so that comment is reworded to describe the rename without leaving a retired name usable. Per the
global convention a stray name is a bug, not a typo; `grep -c lorecommon` is **0** across all four
contract files.

**What changed:** `_SCANNED_MEMBERS` gains it — consequence 3 of five, and the load-bearing one,
because *a package outside that scan is exempt from every ∀ pin in this packet, silently*, which is
why I widened the scan in the first place. `test_the_scan_reaches_every_workspace_member` covers it
automatically (it iterates the constant). Four new pins: the predicate exists and answers all four
blank shapes *and* leaves a padded credential non-blank (the distinction R1's byte-exactness
depends on); the package is stdlib-only; **the package does NOT read the environment** — the guard
on the ruling's own stated risk, since a shared package makes it *possible* for `loresigil` to
resolve again and R3 stands; and the mutation proof.

**The mutation proof, and the weakness building it exposed in my own pin.** I built the reference
(`lorerunes` + both callers wired) and the pin passed — *while `loresigil` was not using the shared
predicate at all*. My first version asserted only that both callers **stop** rejecting once the
predicate is inverted, and a caller that **never rejected** also stops. R29's own defect was wearing
my pin as camouflage. The pin now has **two legs**: a baseline (unpatched, both callers reject) and
the inversion (both accept). A caller that never rejects fails leg 1; a private copy fails leg 2.

Then the definitive proof — `W-PRIVATECOPY`: `loresigil` inlines `not raw or not raw.strip()`
instead of calling the shared predicate. **Behaviourally identical** — the sanity check confirms a
blank key is still rejected, and every other pin in the packet stays green:

```
W-PRIVATECOPY LANDED: loresigil inlines the blankness rule
SANITY: blank still rejected -> behaviourally identical to the correct build
2 failed  — test_MUTATING_the_predicate_moves_BOTH_callers
            test_the_mutation_probe_can_actually_SEE_a_change
```

**That is the pin the operator's ruling is worth more than a drift pin for**, made concrete: a drift
pin detects that two copies *disagree*; this detects that a second copy *exists at all*, while it
still agrees. Reference build and all mutations restored — `config.py` md5 `5de21de8…`, `git status`
over every production tree empty.

### 0.16 REVISION 9 — six address-drift defects, and the root cause I accept

**The lead's diagnosis is right and I am not going to soften it.** All six are pins written against
a design a later ruling changed: R19 moved the unwraps, R26 moved them again, R29 added a second
loresigil unwrap, R27 rostered a new holder. **The pins were correct when written and I never
re-derived them.** My satisfiability receipts were real — repo law requires them and I took them —
but at revisions 3–4, and revisions 6 and 8 reshaped the design underneath them. *A satisfiability
receipt is valid only for the design it was taken against.* That is R30 generalised from one pin to
the whole instrument, and it is the sharpest lesson in this packet.

Every fix keeps the property and moves the address, as instructed. Not one pin was weakened.

| # | defect | fix |
|---|---|---|
| 1 | `UNWRAP_ALLOWLIST` at pre-R19/R26 addresses (3 tests) | Re-derived against the live tree: `counting.py::__init__` → `::build_auth_headers` (R19 made the old address *impossible*), `voyage_http.py::build_bearer_client` → `::build_auth_headers` (R26), **new** `factory.py::_reject_a_blank_credential` (R29), and `token_survey.py::__init__` **deleted** — the sync counter imports the shared seam now, which is R22 working. |
| 1b | **two pins in one class disagreeing about one number** | `>= 8` was a threshold *no ruled design reaches*, while its sibling said `<= 7` and §0.9 said 6. Measured: **6**. Both now agree, and the sibling's message names the composition (2 auth + 1 SDK + 2 seams + 1 validator) so the number is derivable, not remembered. |
| 2 | `exactly_one_unwrap_site_exists_in_loresigil` predates R29 | R26 and R29 each require one and neither can be removed. **Re-pinned as a SET OF FILES, not a count** — so it keeps saying *"the seam and the validator, and nothing else"* instead of a bare number the next ruling silently falsifies. That is R32's root cause fixed in the pin's shape, not just its value. |
| 3 | seam gate flags two stdlib-only deploy scripts | `_STDLIB_ONLY_EXEMPT` was **one filename**; R14's boundary is *stdlib-only deploy scripts*, and the whole directory is that. Widened to the boundary it names, with R14's re-open trigger. |
| 4 | `derived_field_set_is_exactly_two` **cannot pass** | The `hasattr(source, name)` filter excluded exactly the two fields the assertion demanded. `not hasattr(...)` is the correct predicate — a loresigil field with no loremaster counterpart *is* derived. Closed set is now `{output_dimension, api_key, api_url}`; `api_url` belongs there honestly (the translator leaves it at each backend's default — the odoo15_ctx bug). |
| 5 | sibling sweep cannot construct the reshaped config | Added `"backend": "tei"` to `supply`. **Not** catching `ValidationError` — that routes a *constructible* holder into `skipped` and reddens R27.2 for the wrong reason; and defaulting `backend` in production is a silent-fallback hazard in a dispatch field nobody ruled. |
| 6 | `LORE_PYTHON` unallowlisted | Entry added. It **cannot** route through the shared resolver by construction: it is the function whose job is to find an interpreter that *has* loremaster, so it runs before loremaster is importable. |

**On defect 3 I want the builder's refusal preserved, because it is the standard.** It could have
renamed a helper to `build_auth_headers` and collected the exemption; it refused and put the refusal
on the record as a refusal. A `str`-typed function wearing a typed seam's name would have gamed the
gate's exemption rather than satisfied its property — **and a gate that can be satisfied by a rename
is not a gate.** My fix widens the exemption to the boundary R14 actually draws, so the honest
scripts are out of scope and the dishonest rename still would not help.

### 0.16.7 THE SEVENTH — found by sweeping, and it is R29's own guard

The lead asked me to find the seventh rather than wait for a builder to hit it. I swept every
hardcoded `path::function` address in the contract against the live tree (two hits, both legitimate
retired-symbol guards), then checked the R29 riders. This one is real:

```
workspace members (pyproject):      ['loremaster', 'lorerunes', 'lorescribe', 'loresigil']
conformance WORKSPACE_MEMBERS:      ['loremaster', 'lorescribe', 'loresigil']
MEMBERS THE IN-IMAGE GUARD IGNORES: ['lorerunes']
```

**R29 names packet 01a's in-image conformance run as THE instrument proving the new member reached
the artifact** — consequence 5 of five, and the ruling's own words are that forgetting it *"is
#131/#139 verbatim"*. The `Containerfile` **does** copy `lorerunes/`; the guard is frozen at the old
three. So **the ruling's own instrument cannot see the member the ruling mints** — if `lorerunes`
failed to reach the image, or reached it and would not import, the conformance run passes anyway.

Pinned **∀-derived from `pyproject.toml`, never a hand-list** — which is the entire lesson of R32; a
pin naming `lorerunes` would go stale exactly as the six did. Plus a second leg asserting the
Containerfile copies every declared member, because the conformance run can only verify what the
image contains.

⚠ **This is the one intentional RED I am leaving, and I want it labelled as such:** it is real
remaining work (update `WORKSPACE_MEMBERS` and the frozen tuple its own test pins), authorised in
§9 — not a contract defect and not something to weaken.

### 0.17 REVISION 10 — the two REFACTOR gaps, and the eighth as a class

**① The smoke test could not discriminate a namespace shell.** `def test_import(): import lorerunes`
passes against `lorerunes` installed as an empty namespace package — `__file__ is None`, no
production code loaded, **#140 poison mode 3**, and exactly what a plain `uv sync` without
`--all-packages` produces. Now three legs: `__file__ is not None` (a shell has no file), the
predicate is importable (a shell exports nothing), and **the predicate works** — because an
importable stub returning `None` would satisfy the first two and nothing that matters.

**② The prose gate's reach stopped at one file, which is why three corpse sites survived.** Widened
to **every production source this packet governs** via the shared root list. The second half needed
a different predicate, and this is the interesting part: my own test modules *legitimately narrate*
the deleted mechanism, so a flat blocklist there would be a false gate that gets switched off. The
distinction that matters is **tense** — *"the catch-all used to redact this"* is documentation;
*"high-entropy tokens are scrubbed"* is a corpse. So a mention in a packet test module is allowed
only near a deletion marker. Measured before adopting it: every existing mention passes, so it costs
nothing today and catches the fourth site tomorrow. Both legs carry a positive control, because both
assert absences.

### 0.17.1 THE EIGHTH — and the lead was right that it is one shape

Asked *"what is each instrument's REACH, and is the reach as wide as its property?"*, the answer was
worse than one gap:

| scanner | property | reach before |
|---|---|---|
| ONE-ENTRY-POINT env gate | *one secret resolver in the workspace* | missing `lorerunes` |
| M4 locals gate | *no production code renders frame locals* | missing `lorerunes` **and** `skills` |
| R2 function-name corpus | *no production name is mangled* | missing `lorerunes` |
| auth-holder sibling sweep | *every auth holder is swept* | missing `lorerunes`, `lorescribe` |

**Four scanners, four private copies of "which roots do we govern".** When `lorerunes` was minted I
widened `_SCANNED_MEMBERS` and left the other four behind — so three gates and a corpus silently
stopped covering a workspace member, exactly the way R32's six defects went stale.

**That is #102 in my own instruments**, and it is the honest diagnosis of why this packet has hit
*property-right/reach-short* eight times: the reach was never one thing that could be widened once.
So the fix is not four wider lists. It is `_logging_fixtures.workspace_roots()` — **one function,
derived from `pyproject.toml`** — that all four call, so a fifth member is covered without anyone
remembering.

**Mutation-proven in both directions**, which is the only thing that distinguishes sharing from
looks-like-sharing:

```
# forward — add a fifth member `loreghost`, change no scanner:
shared list              : ['loreghost', 'loremaster', 'lorerunes', 'lorescribe', 'loresigil', 'scripts', 'skills']
_scanned_python_sources  : ['loreghost', ...]          # picked it up, zero edits
_workspace_python_sources: ['loreghost', ...]          # picked it up, zero edits

# reverse — one scanner regrows a private list:
W-PRIVATECOPY LANDED: one scanner now excludes a declared member
2 failed — test_every_scanner_reaches_every_declared_workspace_member
           test_all_the_scanners_agree_with_each_other
```

`TestEveryScannerSharesOneRootList` keeps it true, including a leg asserting `workspace_roots` is
still *derived* — a future author who "simplifies" it back into a literal tuple reddens, which is
the only thing that stops a ninth instance.

### 0.18 REVISION 11 — fixtures that could not reach what their names claimed

Every one of the four leaks reproduced before I touched a fixture. The shape is identical in all
four: **the property was right and the fixture set structurally could not construct the case.**

| ruling | the gap | the fixture that closes it |
|---|---|---|
| **R37** | `ASSIGNMENT_LABEL_SAMPLES` was **seven bare words**, so a "∀ label" pin ranged over a set that *could not contain an underscore compound* — and `\b` never matches after `_`. `client_secret`, `session_token`, `db_password` and **`SURREAL_PASS`** all leaked. | Four compounds added, including **`SURREAL_PASS` — our own env var**, so the pin is anchored to a real leak in this repo's logs rather than an invented shape. |
| **R38** | The class's prose claimed *"a labelled bearer token out of an `extra=` map"*. The 7 `TEXT_CARRIERS` are unlabelled **by construction**; every labelled pin drove a **flat string**. So nothing ever put a labelled credential in a container: the class proved **ROUTING, not REDACTION**. | The label as the dict **KEY**, credential as the **VALUE** — because `_scrub_value` scrubs keys and values independently, so the label never adjoins the value. |
| **R39** | The receiver-blind scheme pin was defeated **not by a scheme but by a QUOTE**. `{'Authorization': 'Basic <v>'}` leaked while the bare form scrubbed. | The quoted form added to the same parametrised pin, so both renders are forced together. |
| **R33** | `Digest`'s value is a comma-separated auth-param list, so preserving the scheme and redacting one token **logs the response hash**. | A general pin: a scheme may only be allowlisted for preservation if its credential is **one token**. `Negotiate`/`HOBA` would each have to pass it. |
| **C1** | `display.endswith("auth.py")` — measured: `oauth.py`, `xauth.py`, `jwt_auth.py`, `reauth.py` all exempt. | **Exact path.** The safe set is exactly one file; a suffix is a pattern, a path is a fact. |

### 0.18.1 ⚠ R11's BLOCKER CLASS WAS ABSENT FROM EVERY COMMIT

Looking for cases my fixtures could not construct, I found something worse: a **whole class that no
longer existed**. `TestScrubValueRecursesIntoContainers` — R11's blocker, mutation-proven in
revision 3, which took the adversary's `W-COSMETIC` build from **204 passed / 0 failed** to 8
failed — is absent from `9ab5888`, the first commit of this contract, and from every commit since.
Most likely a slice-based edit in a later revision swallowed it.

**So R11 has been unprotected since the contract was first committed, and nothing could tell — a
test that does not exist does not fail.** Restored, with the R38/twelfth/multi-line fixtures folded
in rather than bolted beside it.

⚠ **This bit me twice more in this same session and the receipt is worth keeping.** Two of my
`s[:index] + new + s[index:]` edits silently ate code — first the three new pins (written into
nothing; `ruff` said *All checks passed*, the suite ran, and it read as success), then
`_auth_holder_classes`. **Both were caught only because I verified by COLLECTION COUNT rather than
by the absence of an error.** That is CLAUDE.md's own question — *"if step N silently no-opped,
would step N+1 still print something that reads as success?"* — and for a slice edit the answer is
always yes.

### 0.18.2 THE TWELFTH — a credential in the dict KEY position

The interrogation the lead asked for (*"can my fixtures REACH the case this pin's NAME claims?"*)
produced one gap no ruling had named:

```
_scrub_value: {key: _scrub_value(inner) for key, inner in value.items()}
                ^^^ every KEY is copied through, unscrubbed
```

Every container fixture in this packet put the credential in the **value** position. A reverse
lookup `{token: identity}` or per-token telemetry `{token: count}` renders it as a **key** — and
nothing scrubbed it. Pinned, plus a second gap the same sweep found: every labelled fixture here is
**single-line**, while a pretty-printed JSON body (what an httpx error carries) separates label from
value with a quote *and* spans several lines.

### 0.18.3 A BOUND RETIRED, and why that is the correct outcome

R38/R39's production fix landed while I worked, and it **closed the three structured `x-api-key`
forms** my KNOWN BOUND pinned as leaking. Measured: all three now redact. So the bound **dissolved**,
and per A16 — *a pin outlives its hole only as a lie* — `test_the_STRUCTURED_x_api_key_form_remains_a_KNOWN_BOUND`
is **deleted with a note**, not weakened and not left green. R40 also falsified its old rationale
(*"no lore code path produces it"* — httpx retains the unwrapped `x-api-key` on every Request), which
is why it had to close rather than be re-argued.

One more pin was **de-coupled from a mechanism**: `test_a_secretstr_inside_a_config_repr_is_masked`
counted the `SecretStr` mask specifically, and once the structured form began redacting, the mask is
itself replaced by `***REDACTED***` — so the count went to zero while the property held perfectly.
It now asserts the property (neutralised twice, by either sentinel), not the spelling of one
mechanism.

### 0.18.4 D1 and D2 — my reading, no action taken

**D1 — the ten retired symbols.** My reading: registering them in `_RETIRED_SYMBOLS` would redden
the gate against this packet's own live spec prose, because the inventory and this report *name*
those symbols in order to explain their deletion. That is the same tense problem I solved for the
prose gate in revision 10, and the same answer applies — a retired-name gate needs a
historical-mention exemption, or a scope that excludes spec/receipt documents. **I did not act:
`_RETIRED_SYMBOLS` is a repo-wide instrument, not this packet's, and changing its semantics is an
operator call.**

**D2 — two `build_auth_headers` with different return contracts.** My reading: this is a genuine
ONE-IMPLEMENTATION smell, and it is also **exactly what R26 constraint 1 ordered** — two typed seams,
because `loresigil` cannot import `loremaster` and *"the enforcement is the TYPE SIGNATURE, not a
shared implementation"*. If the return contracts have diverged (one returning the full header map,
the other only the auth pair), that is a real inconsistency worth closing — but the fix is to make
the contracts agree, **not** to merge the functions, which R26 forbids. **Operator call; I did not
act.**

### 0.3 R6 — `skills/` scanned, and the rider DISCHARGED WITH A RECEIPT

The ruling's warning is that `skills/` is outside `testpaths` **and** outside
`scripts/typecheck.sh`, so extending a gate over it means proving the gate runs — *"a guard nobody
runs is a hope with a filename"*, and both of packet 03b's instruments were victims of that class.

**It does run, and here is why rather than a promise:** both scanners live in
`loremaster/tests/`, which IS in `testpaths`, and they **read** `skills/` as text rather than
importing it — so no `testpaths` or `sys.path` question arises. The receipt is a pin, not this
paragraph: **`test_the_scan_reaches_the_skills_tree`** asserts (a) at least one `skills/` file is
in the scanned population, (b) `probe_embed.py` specifically is — it is the whole reason the
root was added — and (c) the test-file exclusion still holds on the new root, so its inline
`test_*.py` files are not governed as production sources.

Live receipt at base `251d112`: the pin **passes**, and `test_the_scan_reaches_every_workspace_member`
in `test_secret_typing.py` passes for all five members including `skills`.

⚠ **What this does NOT fix, said plainly:** `skills/` is still outside `scripts/typecheck.sh`, so
mypy will not see `probe_embed.py` after its migration. My gates cover the resolver shape and the
unwrap surface; they do not cover types there. That is a residual for the lead, not a blocker.

### 0.4 R8 — pinning it uncovered that this is a LEAK, not a lost diagnostic

R8 rules that `Authorization: Bearer <tok>` must render `Authorization: Bearer ***REDACTED***`.
Writing the pin, I measured the sibling shapes, and the defect is worse than "a scheme word gets
eaten":

```
'Authorization: Token 8f3ka92mfLQ0zXvbNqRt'
   -> 'Authorization: ***REDACTED*** 8f3ka92mfLQ0zXvbNqRt'      # measured 2026-07-26, 9c08cac
```

`_ASSIGNMENT_RE` consumes the **scheme** as the value and leaves **the credential untouched**. For
that 20-character token it leaks *today* — it is under the deleted catch-all's 24-char window, so
nothing ever caught it. `Authorization: Basic <base64>` only *looks* safe because the entropy
catch-all redacted the base64 on a second pass; **delete the catch-all and it leaks too.** That
would make packet 42 a strict regression on the one surface its own Scope OUT promises to keep
protecting.

Pinned as `test_a_NON_BEARER_AUTH_SCHEME_DOES_NOT_LEAK_ITS_CREDENTIAL` (Basic / Token / ApiKey),
asserting the safety property first (*the credential is gone*) and R8's scheme preservation on
top. Around it, three pins that make the naive fix fail: a fix that simply deletes `authorization`
from the label list satisfies R8's Bearer pin and un-redacts
`test_an_authorization_header_with_no_scheme_is_still_redacted`,
`test_the_assignment_form_of_authorization_is_still_redacted` and every line of the leak pin. Plus
`test_the_anthropic_api_key_header_is_redacted` (`x-api-key:` — the real production header for the
calibration counter, and `\bapi[_-]?key\b` matching inside `x-api-key` is verified, not assumed)
and `test_the_scheme_survives_case_insensitively_and_mid_line` (lowercased by an HTTP/2 client;
quoted inside a rendered `curl` in an exception message).

### 0.5 R8's fix took SIX reference builds — three real traps, all found by fixtures

The clearest thing this contract's fixture design bought, and a warning the builder needs before
starting. Each trap was found by a test going red, never by inspection.

**Trap 1 — the scheme list collides with the label list.** The natural fix is to widen the scheme
pattern to `Bearer|Basic|Token|ApiKey|Digest`. Two tests went red:
```
FAILED …test_every_labelled_assignment_is_redacted[ = -apikey]
FAILED …test_every_labelled_assignment_is_redacted[ = -token]
'store.connect.failed token ***REDACTED*** lore-root-pw-not-a-real-one endpoint=ws://x/rpc'
```
**`Token` and `ApiKey` are auth schemes AND `_ASSIGNMENT_RE` labels.** A scheme pattern firing on
a bare `token ` matches `token ` + `\S+` = the **equals sign** — so `token = <secret>` redacts the
`=` and leaks the value. Found by the **∀ label × ∀ separator** matrix (7 × 4); a
single-label fixture could not have seen it.

**Trap 2 — "any leading word is the scheme" eats the wrong token.** Generalising to
`[A-Za-z][\w-]*\s+` made `authorization=lore-root-pw-not-a-real-one endpoint=ws://x/rpc` treat the
**password** as the scheme and redact `endpoint=…` instead. Four more matrix cases red.

**Trap 3 — my own pin over-constrained the mechanism.** `test_the_label_set_is_derived_from_the_pattern`
asserted the alternation EXACTLY, including `authorization` — which forbids a correct fix that
moves auth-header handling into its own pattern and drops the label. **I relaxed my own pin** to a
superset check over the five labels that have no other home (`CORE_ASSIGNMENT_LABELS`), and said
so in its docstring. A contract pins behaviour; that one was pinning a mechanism.

**The shape that works — offered as a RECOMMENDATION, not a prescription** (the contract pins
behaviours; this is evidence they are jointly satisfiable). It is *allowlist the safe*, in the one
direction that is safe to get wrong:

> A scheme word is **PRESERVED only when it is one we know**. Anything else after
> `authorization:` is redacted to the end of the value. **A scheme we fail to recognise costs a
> diagnostic word; a credential we fail to recognise costs a credential.**

That inverts the failure direction of every earlier attempt, and it is the only shape found that
satisfies all three pinned properties at once — known scheme preserved, unknown scheme's
credential gone, assignment forms intact. Eleven shapes verified (§10.2); **202 passed, 0 failed**.

---

## 1. Tree provenance (#140 — prove which tree you are testing)

```
worktree : /home/ejprice/PycharmProjects/lore-pkt42   branch pkt42-prevent-the-leak
HEAD     : 9c08cac  docs(pkt42): Phase 0 removed-behavior inventory + the M3 correction
loremaster.__file__ = /home/ejprice/PycharmProjects/lore-pkt42/loremaster/loremaster/__init__.py
```
Every measurement in this report was taken in that tree, on 2026-07-26, at `9c08cac`.
**No production file was modified.** The one production file I temporarily mutated for the
satisfiability receipt (`logging_setup.py`) was `cp -a`-backed up first and restored byte-exact —
md5 `831ca42e782e9ee9b4533dc750166ccc` before and after, `git diff` empty (§10).

**Tool honesty (repo law §4):** I used **direct Read/grep/AST, not lore**, for essentially all of
this work. Reason stated up front: lore's index points at the PRIMARY checkout, and every file
this packet touches is either edited in this worktree or being *counted* — and exhaustive counts
over renamed/retired symbols are one of the three cases the dogfood protocol reserves for grep
anyway. I did not file a friction row, because this is the documented `#134`/`#125` worktree
limitation rather than a new gap.

---

## 2. PACKAGE SURVEY

| mechanism | libraries evaluated (name + version) | what I READ | verdict |
|---|---|---|---|
| Parse `KEY=value` out of an operator `.env` file (inventory C3–C6) | `python-dotenv` **1.2.2** (installed, transitively via pydantic-settings) | Installed `dotenv/__init__.py` `__all__`; signatures of `dotenv_values`/`get_key`/`load_dotenv`/`find_dotenv`; source of `dotenv.main.get_key`. Then **measured 11 parse cases**: `export ` prefix ✅, single/double quotes ✅, `KEY=a=b=c` ✅, comment lines ✅, unquoted padding stripped, quoted padding **preserved**, duplicate keys **LAST-WINS**. | **replace**, and specifically **`dotenv_values`** — ruling R2 names the function, not just the package, because `load_dotenv` mutates `os.environ`. Enforced by `test_reading_the_file_does_NOT_mutate_the_process_environment` (an OUTCOME pin, not a banned name) + `test_no_file_is_discovered_implicitly`. |
| *(same mechanism, alternative)* | `python-decouple` **3.8** | Operator probed it: it delivers env-beats-file precedence, file fallback and byte-exact values once our two-line policy sits on top. Metadata read: latest release **3.8, uploaded 2023-03-01, no declared `requires_python`**, against this repo's Python **3.14**. | **declined (operator, R2) — on MAINTENANCE, not capability.** Recorded because "we didn't consider it" and "we considered it and said no, here's why" are different artifacts, and only the second survives the next person's review. |
| Resolve a secret from an env var whose NAME is runtime data | `pydantic-settings` **2.14.1** (declared in `loremaster/pyproject.toml`, unused) | Installed source of `EnvSettingsSource._extract_field_info(field, field_name)` — it derives the env var name from the **field name / static `validation_alias`**, at class-definition time. Every lore site passes the name as a *value* (`resolve_secret(config.surreal.user_env)`). | **bespoke** (packages-rule side 2). Wrong shape, not a missing feature. Keep the existing `resolve_secret`; hand-roll nothing new. Lead's Phase 0 verdict re-derived, not inherited. |
| Hide a credential from `repr`/`str`/f-string/exception rendering | `pydantic.SecretStr` **2.13.4** | `vars(SecretStr('abc')) == {'_secret_value': 'abc'}`; masks as `**********` through all four paths (measured). | **replace** — already adopted (#211). The `_secret_value` attribute is the AST gate's KNOWN BOUND, pinned in `TestEveryUnwrapSiteIsAllowlisted`'s docstring with a re-open trigger. |
| Render a traceback with frame locals (the M4 threat) | `rich` **15.0.0** (in closure), `better_exceptions` (**absent**), stdlib `traceback` | `inspect.signature(rich.traceback.install)` — `show_locals: bool = False`, `extra_lines: int = 3`. Measured: `show_locals=True` leaks a frame local; `show_locals=False` does not; `traceback.format_exception` never renders locals; `TracebackException(capture_locals=True)` does. | **keep_with_trigger** — nothing to replace; the risk is a future `install(show_locals=True)`. Trigger: adding any dependency that installs an excepthook → extend the M4 legs to a subprocess run. |
| Detect a secret in arbitrary text | `detect-secrets` 1.5.0 | Not re-evaluated. Rejected under #227 with receipts (a detector not a redactor; 4.80 ms/traceback; flags `Traceback`/`File`/`line`). | **bespoke → then DELETED.** Packet 42's whole thesis is that no library and no heuristic should do this. |
| Shannon entropy / candidate-window selection | — | — | **deleted, not replaced.** This is the mechanism packet 42 removes. |
| The labelled-pattern redaction (`_BEARER_RE`, `_ASSIGNMENT_RE`) | — | — | **domain logic** — a project-specific predicate over lore's own log surface. Kept as-is (packet Scope OUT). |

---

## 3. Test files

| file | status | what it carries |
|---|---|---|
| `loremaster/tests/test_secret_leak_vectors.py` | **NEW**, 146 tests | The packet's Exit-clause instrument: M1–M4 vector battery, labelled-pattern survival, recovered-data pins, the M4 locals pin, and the accepted bounds. |
| `loresigil/tests/test_factory_secret_resolution.py` | **NEW**, 26 tests | Steps 1+2 loresigil half: `api_key: SecretStr`, ∀-3-backend wire bytes, loresigil reads no env, one bearer-header implementation. |
| `loremaster/tests/test_secret_resolution_seam.py` | **NEW**, **50 tests** | Step 2 loremaster half: composition root, copied-through provenance, **R2's unified lookup + the no-mutation pin**, **R3's `TestTheEnvFileFallbackIsNotAvailableToTheServer`**, `load_api_key` routing (mutation-proven), the ONE-entry-point env allowlist. |
| `loremaster/tests/test_secret_typing.py` | **EDITED** | Widened `_python_sources()` to the whole workspace; **added step 3's `UNWRAP_ALLOWLIST` gate**; reconciled the name-keyed honesty pin with a receipt. |
| `loremaster/tests/test_logging_setup.py` | **EDITED** | Corpse removal (2 classes + 2 tests deleted, 3 re-authored), each with an in-file note naming the inventory item and where the property moved. 52 → 44 tests. |
| `loremaster/tests/_logging_fixtures.py` | **NEW**, 0 tests | Shared plumbing so the new suite does not clone `_emit`/`_make_record`/the restore fixture. |

---

## 4. The contract, in plain English

**Step 1 — complete the type coverage.** `_python_sources()` in the #211 ∀ pin now covers
`loremaster` + `loresigil` + `lorescribe` + `scripts`, so `api_key: str` in loresigil's four
embedder constructors reddens automatically. A positive control asserts the scan reaches *each*
member (a silently-skipped member is an exempt package).

**Step 2 — one entry point.** `to_loresigil_config` calls `resolve_secret`, proven by MUTATION
(sentinel-patch the resolver; the translated config must carry the sentinel — a hand-rolled
`os.environ.get` calls it zero times and stays green on any type-only pin). Failure moves EARLIER,
to translation, and names the env var. `loremaster.config.EmbeddingConfig.api_key_env` STAYS; the
loremaster model must never gain an `api_key`. Per **R2**, `resolve_secret` grows an opt-in
`env_file` and becomes the single lookup for all three former resolvers — env first, then
`dotenv_values(env_file)`, never `load_dotenv` (pinned by OUTCOME: `os.environ` must be unchanged
afterwards, unrelated keys included). Per **R3**, the file fallback is **not reachable from the
server**: an AST pin allowlists exactly one call site, both spellings of the argument, both
directions. The two `load_api_key` twins must be *the same function object* and must *route through*
the shared resolver (mutation-proven — identity alone would pass on one shared copy of the old
parser), with `python-dotenv` **declared** in `loremaster/pyproject.toml` **and** imported by
`loremaster/config.py` (not by `calibration/counting.py` — the earlier ruling's module). An AST gate over `os.environ`/`os.getenv` allows
exactly one module — `loremaster/config.py` — to resolve a secret from the environment; every
other read needs an evidence-backed allowlist entry, checked **both ways** (unlisted site → RED;
stale entry → RED).

**Step 3 — gate the unwrap surface.** `UNWRAP_ALLOWLIST` in `test_secret_typing.py`, keyed on the
AST **call** (not grep — that is the 13-vs-10 correction made mechanical). Each entry carries an
evidence CATEGORY from a **closed set**; inventing a sixth category to launder a new unwrap
reddens. Both directions checked. The gate states its threat model and its known bound
(`SecretStr._secret_value` bypasses it) with a re-open trigger.

**Step 4 — pin M4.** Two property legs that name no library — render a secret-bearing frame
through the production log path and through `sys.excepthook` **as currently bound** — plus a
positive control that installs `rich.traceback(show_locals=True)` and proves the probe SEES the
leak, plus the composition pin (a `SecretStr` local masks *even under* a locals-rendering hook).
A third, name-keyed structural leg scans for `capture_locals=True`/`show_locals=True`/`sys.excepthook`
assignment, with an explicit honesty pin saying it is name-keyed.

**Steps 5+6 — delete the catch-all and everything it forced.** Retired-symbol pins for all eight
symbols; a prose pin (`logging_setup`'s docstring may not teach a mechanism it no longer runs);
∀-labelled-pattern survival across every label × every separator; idempotence; and A19 proven by
mutation (patch `_scrub_text` to a sentinel — all three consumers must move).

**The A18 control (the load-bearing one).** A 7-carrier × 3-credential × 2-format matrix: a
`SecretStr` credential never reaches the emitted bytes, and the mask appears where it was. Every
case has a **paired bare-`str` case** driving the same carrier through the same sink, which does
two jobs at once — it proves the oracle can see a leak (so the green legs are not "nothing was
emitted"), and it IS the accepted bound, per carrier and per format, carrying a "if you closed
this deliberately, say so" message and a re-open trigger.

**The recovered data.** A ∀ pin over **every distinct function name in the production packages**,
derived live from the tree: none may be mangled. Plus the four #227 path classes, a git SHA in
prose, a canonical UUID, and a `unique_database()` name built by the *production builder* — the
last two being `TestBareHexRunsStayRedactedKnownBound`'s accepted false positives, now inverted
into data that must survive.

---

## 5. Measurements I re-derived (repo law: a number you did not measure is a rumour)

| claim | source | re-derived at `9c08cac`, 2026-07-26 |
|---|---|---|
| M3 "13 `.get_secret_value()` call sites" | packet | **13 grep hits, 10 AST call sites.** Confirms the Phase 0 correction independently. The allowlist is sized off 10 (+1 new loresigil seam). |
| env reads | new | **14 grep hits, 11 AST reads.** Same two-population trap; the gate is AST for that reason. |
| Audit R2 "201 of 1,616 function names (12.4%)" | audit R2 | **Matches no scoping I can construct.** Mine: production packages **89/1004 = 8.9%**; `scripts/` **227/494 = 46.0%**; test trees **3722/5435 = 68.5%**. Reported as a discrepancy, not as "the audit was wrong" — it plainly used a different population. The pin uses the production corpus, regenerated live. |
| C11 "**one twin** failed to honour `export KEY=…`" | inventory C11 | **BOTH twins fail.** Both use `stripped.startswith(f"{ANTHROPIC_API_KEY_ENV}=")`, which cannot match `export ANTHROPIC_API_KEY=…`. Inventory says re-derive before claiming fixed — done; the count was low by one. |
| "the catch-all protects credentials" | implicit | **It does not protect the realistic ones.** `correct-horse-battery-staple` scores **3.495** bits/char against a 3.5 threshold — it survived by 0.005 bits. `lore-root-pw-not-a-real-one` scores 3.102. Meanwhile it erased 8.9% of production function names. That asymmetry is the packet's thesis, measured. |
| `loresigil.factory.EmbeddingConfig` "2 prod refs" (lore_impact) | Phase 0 | **Three.** `scripts/search_score_survey.py::_make_embedder` constructs it directly with `api_key_env=`. `scripts/` is outside lore's prod scoping *and* outside `scripts/typecheck.sh`, so neither instrument sees it. **Escalated, §7.2.** |

---

## 6. Adversarial pre-flight — every entry, and where it is covered

| # | hazard | covered by |
|---|---|---|
| 1 | **Wrong unit** — bits/char vs a threshold; a fixture whose entropy sits either side of 3.5 by accident | Three credentials spanning 3.102 / 5.393 / 5.667 bits/char, each measured and stated in the module docstring. The low-entropy one is the discriminator that proves the TYPE, not a leftover heuristic, is doing the work. |
| 2 | **Wrong scale** — a credential shorter than the deleted 24-char window, so no pin touches the mechanism | `test_the_function_name_corpus_actually_exercises_the_deleted_window` asserts ≥50 corpus names are ≥24 chars; every credential fixture exceeds 24 unbroken in-charset chars. |
| 3 | **Sign flip / null / zero** — empty, whitespace-only, and interior-whitespace credentials | `TestAnAbsentCredentialFailsLoudAndNeverBuildsAKeylessEmbedder` (3 blank shapes + the accepted interior-whitespace case); `test_a_blank_variable_fails_at_translation`; `test_a_blank_value_in_the_file_also_fails_loud`. |
| 4 | **Boundary** — cap/cap±1 analogue here is *the label alternation*: a build keeping only `api_key=` | ∀ label (7 literals) × ∀ separator (4) = 28 forced cases, **plus** `test_the_label_set_is_derived_from_the_pattern`, which reads the alternation out of the compiled regex so the hand list cannot drift. |
| 5 | **Empty / degenerate driver table** — a scan that matches nothing and passes vacuously | Positive controls on **every** scan: unwrap sites (≥8), env reads (≥6), function-name corpus (≥800), secret params (≥10), loresigil files (≥8), per-member reach, shared-field count (≥10). |
| 6 | **Real-distribution tails** — hashy CI paths, container overlays, nix store hashes, UUID temp dirs | The four `HOSTILE_PATHS`, constructed (never taken from the running checkout — this repo's own path has no high-entropy component, which is how the defect stayed invisible). |
| 7 | **Producer↔consumer seam, unit change** — `SecretStr` crossing into an HTTP header | `TestEveryBackendPutsTheRealCredentialBytesOnTheWire`: a **real request** through a MockTransport on all three arms, asserting `header == f"Bearer {key}"` by **equality**. This is the packet's deadliest wrong build and nothing in the tree caught it before (§7.5). |
| 8 | **Producer↔consumer seam, field drop** — `to_loresigil_config` silently dropping a field | ∀-field provenance pin with **every field at a non-default value**, plus a control asserting no fixture value equals the loresigil default (a defaulted fixture cannot see a dropped field). |
| 9 | **Byte-exactness** — a resolver that "helpfully" strips a padded key | `test_a_key_with_real_whitespace_survives_byte_exact` (∀ 3 arms), `test_the_exported_value_is_NOT_stripped`, `test_a_credential_that_is_only_whitespace_INSIDE_is_still_accepted`. |
| 10 | **Rejected for the WRONG reason** (the lead's measured hazard) | `test_api_key_env_is_rejected_AS_AN_UNKNOWN_FIELD` inspects `error["type"] == "extra_forbidden"` and `error["loc"]`; blank-key pins assert `loc == ("api_key",)`; both are paired with a success control **and** a differently-broken input rejected for a different reason (`backend`). |
| 11 | **Parameter-value monoculture** | Three arms, three different keys; three credentials in the leak matrix; a `voyage-context` (not `tei`) fixture in the copied-through pin. |
| 12 | **Deleting a pin whose bound dissolved** | `TestBareHexRunsStayRedactedKnownBound` and `TestThePathExemptionNeverWeakensTheBackstop` DELETED with in-file notes; their two values re-pinned INVERTED as recovered data. |
| 13 | **Over-deleting** — losing the paths/function-names property with the mechanism | `TestOrdinaryPathsSurviveRedaction` kept as a regression pin (docstring rewritten); the production function-name ∀ pin is new and stronger than anything that existed. |
| 14 | **The suite is green because it asserts the corpse** | BARE anchor-free grep of the whole tree for `entropy` / `_TOKEN_RE` / `_shannon` / `_UUID_RE` / `_PATH_BLOB_CHARS` / `_is_*`; every hit adjudicated individually in §8; 5 sites in `test_logging_setup.py` found carrying an UNLABELLED credential and each re-authored or deleted. |
| 15 | **Hostile rendered text** | The M1 literal-in-source fixtures (labelled and unlabelled), the `stack_info` caller-line fixture, and the `_scrub_value` container recursion. |
| 16 | **A fixture that delivers nothing** (cold-audit R3) | Hit for real during this contract: my re-authored `stack_info` fixture split the call across lines and delivered no credential; the reference build caught it and a **second positive control** (`"_emit_with_stack(logger, token=" in rendered`) was added. |
| 17 | **A dependency reopening M4** | Property legs A/B (receiver-blind) + the `rich show_locals=True` positive control + the name-keyed leg with its honesty pin. |
| 17b | **Environment mutation as a side effect** (R2) — `load_dotenv` exports every key in the file into `os.environ`, silently arming the server path for the rest of the process | `test_reading_the_file_does_NOT_mutate_the_process_environment` — asserts the OUTCOME (the target key **and** an unrelated key in the same file are both absent from `os.environ` afterwards), so it is receiver-blind rather than a banned name. Plus `test_no_file_is_discovered_implicitly` for `load_dotenv()`'s no-argument CWD discovery. |
| 17c | **A credential source the container never configured** (R3) — a server call site gains an `env_file` and a stray `.env` becomes production credentials | `TestTheEnvFileFallbackIsNotAvailableToTheServer`, 4 pins, both spellings of the argument, both directions of the allowlist, with a detector control and a mutation proof (§0.1, §10.3). |
| 18 | **Concurrency degree** | **Scoped out** — nothing in packet 42 is concurrent. `_scrub_text` is pure; `resolve_secret` reads `os.environ`; config translation is synchronous. No shared mutable state beyond the global logging config, which the autouse restore fixture isolates. |
| 19 | **Wrong anchor (week/epoch/timezone)** | **Scoped out** — no dates, no calendars, no time arithmetic anywhere in this packet. |
| 20 | **Input accounting over a collection** | **Scoped out** — no unit here consumes a caller-supplied collection and emits per-item results. The nearest analogue (`_scrub_value` walking a container) is covered by `test_scrub_value_leaves_non_string_scalars_untouched` and the `extra-nested` carrier. |

---

## 7. OPEN RULINGS — NONE. All five §7 findings are ruled.

| my finding | ruling | outcome |
|---|---|---|
| C2 strip semantics | **R1** | My recommendation A adopted verbatim. Pins unchanged; markers now read `RULED BY R1`. |
| C9 empty-vs-unset | **R1 + R5** | **My recommendation DECLINED.** The R2 shape stands — blank falls through to the file. Re-pinned to the ruled branch (§0.2), with the message rider mechanised. |
| `comms_consumer_eval.py` 4th env-read | **R7 — MIGRATE** | Allowlist entry deleted; added to the retired-resolver pin. |
| `probe_embed.py::_resolve_key` 4th resolver | **R6 — IN SCOPE** | Both AST gates widened to `skills/`; rider discharged with a receipt (§0.3). |
| `Authorization: Bearer` double-redaction | **R8 — FIX THE CODE** | Six pins; and pinning it revealed a **live credential leak** (§0.4) and a fix collision (§0.5). |

**I hold no unresolved fork.** Two things the operator should SEE rather than decide: §0.4 (this is
a leak, not a diagnostic loss) and §0.5 (the obvious fix collides). Both are pinned; neither is a
question.

**One residual, flagged not blocking:** `skills/` remains outside `scripts/typecheck.sh`, so mypy
will not see `probe_embed.py` after its migration. My gates cover its resolver shape and unwrap
surface; they do not cover its types.

## 8. FOUR-VERDICT ADJUDICATION TABLE — all 40 inventory items

Verdicts: **P** preserved-with-pin (spec clause cited; *"the old code did it"* is banned) ·
**D** dropped-deliberately · **B** old-bug/known-limitation, NOT re-pinned ·
**S** spec-silent → operator ruling.

### A. `loremaster/logging_setup.py`

| # | verdict | pin / reason |
|---|---|---|
| A1 `_TOKEN_RE` candidate window | **D** | Exists only to feed A2. `TestTheEntropyMachineryIsGone::test_the_symbol_is_gone[_TOKEN_RE]`. |
| A2 entropy ≥3.5 → REDACTED | **D** | *Spec:* packet Mission + step 5. This IS the deletion. Retired-symbol pins for `_shannon_entropy_bits`, `_ENTROPY_BITS_THRESHOLD`. |
| A3 sub-threshold candidate survives | **D** | Falls out with A2. |
| A4 `_is_safe_high_entropy_run` | **D** | *Spec:* step 6, "do not leave them as vestigial guards". Retired-symbol pin. |
| A5–A8 the four path conditions | **D** | Support for A4. `_is_absolute_path_component` retired-symbol pin covers all four. |
| A9 `_UUID_RE` exemption | **D** | Support for A4. Retired-symbol pin. **The PROPERTY is inverted and kept:** `test_a_correlation_uuid_in_prose_survives`. |
| A10 `_shannon_entropy_bits("") == 0.0` | **D** | Function deleted. |
| A11 `_PATH_BLOB_CHARS` includes `+`/`=` | **D** | Support for A6; the coupling dies with both. Retired-symbol pin. |
| A12 order bearer→assignment→entropy | **P** | *Spec:* Scope OUT keeps the labelled patterns. `test_the_two_patterns_compose_in_one_line`. |
| A13 idempotence | **P** | *Spec:* Scope OUT. `test_scrubbing_is_idempotent` — with a "redaction actually happened" guard, because idempotence is trivially true of the identity function. |
| A14 `_BEARER_RE` label-preserving | **P — and CORRECTED by R8** | *Spec:* Scope OUT names `Authorization: Bearer …` explicitly; **R8** rules the current output wrong. `test_bearer_is_redacted_and_the_scheme_word_is_preserved` + `test_the_bearer_scheme_word_survives_a_full_authorization_header` (exact equality) + `test_the_scheme_survives_case_insensitively_and_mid_line`. This is the packet's one **production behaviour change** outside the deletion. |
| A15 `_ASSIGNMENT_RE` label+separator | **P — and NARROWED by R8** | *Spec:* Scope OUT names `api_key=…`; **R8** additionally forbids it consuming an auth scheme word. ∀ label × ∀ separator = 28 cases (the matrix that caught the §0.5 collision) + the derived-alternation pin, whose message now names the hazard + `test_a_NON_BEARER_AUTH_SCHEME_DOES_NOT_LEAK_ITS_CREDENTIAL` + `test_an_authorization_header_with_no_scheme_is_still_redacted` + `test_the_assignment_form_of_authorization_is_still_redacted` + `test_the_anthropic_api_key_header_is_redacted`. |
| A16 KNOWN BOUND: bare hex/SHA redacted | **B → dissolved** | `TestBareHexRunsStayRedactedKnownBound` **DELETED** with an in-file note. A pin outliving its hole is a lie. **Inverted:** `test_a_git_sha_in_prose_survives`, `test_a_harness_database_name_survives`. |
| A17 KNOWN BOUND: URL-path-segment secret | **D as a bound** | It was a bound *bought by* an exemption; there is now no exemption. Re-pinned as a plain consequence: `test_a_credential_in_a_url_path_segment_is_not_redacted`, with the re-open message. |
| A18 unlabelled secret in free text | **D — THE deliberate trade** | *Spec:* packet Mission + operator ruling. Pinned **as a bound** ∀ credential × ∀ carrier × ∀ format (`test_an_unlabelled_credential_in_free_text_is_not_redacted`, `test_a_bare_str_credential_does_reach_the_sink`), each with the re-open trigger. The **replacement control** is the whole of `TestASecretStrCredentialNeverReachesARenderedLogLine`. |
| A19 three consumers call `_scrub_text` | **P** | *Spec:* step 5 shrinks the body, not the surface. `test_all_three_consumers_route_through_the_one_scrub_implementation` — **proven by mutation** (sentinel-patch; a consumer that inlined the regexes stays unchanged and is caught). Plus `TestTheScrubbedSurfacesAreUnchanged` over msg/args/extra/exc_info/stack_info. |

### B. `loresigil/factory.py`

| # | verdict | pin / reason |
|---|---|---|
| B1 `_resolve_api_key` reads `os.environ` | **D** | *Spec:* operator ruling 2026-07-26. `test_no_loresigil_module_reads_an_environment_variable` (keyed on `os.environ`, **not** on the name) + `test_the_retired_symbol_is_gone[_resolve_api_key]`. |
| B2 `if not key` → loud failure | **P** | *Spec:* B2's own property statement. Re-established at the config boundary: `TestAnAbsentCredentialFailsLoudAndNeverBuildsAKeylessEmbedder` (3 blank shapes, each asserted at `loc == ("api_key",)`) + `test_no_embedder_is_constructed_when_the_credential_is_blank`. **⚠ Reading noted in §8-note.** |
| B3 whitespace-only key accepted | **B** | Old bug. **NOT re-pinned.** The new pins reject it; the in-class docstring says so explicitly so nobody "restores" it. |
| B4 value passed byte-exact | **P** | *Spec:* `resolve_secret`'s docstring ("never stripped or otherwise mutated"). `test_a_key_with_real_whitespace_survives_byte_exact` ∀ 3 arms + `test_a_credential_that_is_only_whitespace_INSIDE_is_still_accepted`. |
| B5 error names the env var | **P** | *Spec:* B5. `test_an_unset_variable_fails_at_TRANSLATION…` asserts the var name is in the message. |
| B6 `MissingApiKeyError` public | **D** | Raised only by B1; caught in **zero** production sites (re-derived). `test_the_retired_symbol_is_gone[MissingApiKeyError]`. 4 test files migrate (§9). |
| B7 resolution at `make_embedder()` time | **D → moves earlier** | *Spec:* the ruling. `test_an_unset_variable_fails_at_TRANSLATION_before_any_embedder_exists` + `test_make_embedder_from_config_surfaces_the_same_failure`. |
| B8 `api_key_env: str` on loresigil | **D** | *Spec:* the ruling. `test_api_key_env_is_rejected_AS_AN_UNKNOWN_FIELD` — inspecting `extra_forbidden` + `loc`, with two controls, because the lead measured this exact pin passing for the wrong reason. |
| B9 one key into all three arms | **P** | *Spec:* B9, "forced per backend". `TestEveryBackendPutsTheRealCredentialBytesOnTheWire` — real requests, three different keys, **equality** on the header. |
| B10 `loremaster.config…api_key_env` | **P (not touched)** | *Spec:* the ruling. `test_loremaster_config_still_carries_the_env_var_NAME` + the inverse guard `test_the_loremaster_config_never_gains_a_resolved_key_field`. |
| *(provenance)* 10 copied-through fields | **P** | *Spec:* the inventory's per-field provenance note. `TestEveryOtherFieldStillCopiesThrough` — derived field set pinned **closed** at `{output_dimension, api_key}`, every fixture value non-default, with a control proving no fixture value equals a loresigil default. |

**§8-note (B2):** the ruling puts *resolution* at the composition root, which would put the emptiness
check there too. I pinned it at the **config boundary** as well, because
`scripts/search_score_survey.py` constructs the loresigil config **directly**, so a
composition-root-only check leaves B2's property untrue over that path. This is a reading, it is
written into the class docstring, and it is the reason §7.4 is an escalation and not a footnote.

### C. `load_api_key` twins

| # | verdict | pin / reason |
|---|---|---|
| C1 exported var beats the file | **P** | *Spec:* C1, "precedence is policy". `test_an_exported_variable_wins_over_the_file` — with the file carrying a *different* value, so precedence is observable. |
| C2 exported value `.strip()`ped | **D — RULED by R1** | *Spec:* R1, *"the value is never stripped"*. C2's `.strip()` is retired as drift. `test_the_value_is_byte_exact_from_either_source` ∀ source (env **and** file — different code paths, dotenv has its own quoting rules). |
| C3 falls back to the file | **P** | *Spec:* C3. `test_it_falls_back_to_the_env_file`. |
| C4 matches `ANTHROPIC_API_KEY=` lines | **P** | *Spec:* C4. Same test, with two decoy keys around it. |
| C5 split-on-first-`=`, strip quotes | **D (mechanism)** | *Spec:* R2 — `dotenv_values` owns it, inside `resolve_secret`. The OUTCOME is kept: `test_a_quoted_file_value_is_unquoted` (single **and** double). |
| C6 empty value keeps scanning | **P** | *Spec:* C6. `test_a_blank_declaration_does_not_shadow_a_later_real_one`. **Measured:** dotenv is LAST-WINS, which produces the same outcome by a different route. ⚠ The **dual** (`KEY=real` then `KEY=`) diverges — see §8-note-C. |
| C7 `RuntimeError` names var + file | **P** | *Spec:* C7. ⚠ R2's shared resolver raises `KeyError` naming only the VARIABLE, so `load_api_key` must translate and add the FILE — the `load_config` precedent. A build that let the bare `KeyError` escape loses half the message **and changes the exception type its two CLI callers catch**. `test_a_missing_key_names_both_the_variable_and_the_file`, plus two more doors (file exists without the key; key present but blank) so the guard is not conditioned on "the file is missing". |
| C8 returns `SecretStr` | **P** | *Spec:* C8. `test_it_returns_a_secret_type`. |
| C9 empty exported var falls through | **P — PRESERVED by R5** (I expected D; the operator ruled otherwise) | *Spec:* R5, *"a blank exported variable falls through to the `env_file` when one is supplied"*. `test_a_blank_exported_variable_falls_through_to_the_file` + `test_a_blank_exported_variable_is_still_fatal_when_the_file_also_misses`. Server path (no `env_file`) is fatal per R1: `test_a_blank_variable_is_fatal_on_the_serverpath` ×3. R5's rider mechanised by `test_the_emptiness_rule_is_stated_honestly_and_not_overclaimed` — emptiness is fatal at the END of resolution, and no pin message may claim otherwise. |
| C10 the twins are byte-divergent | **D** | *Spec:* Scope IN #2 + R2's *"ONE lookup shape across all three former resolvers"*. `test_the_twins_are_literally_one_function` (identity, not equivalence) **plus** `test_it_routes_through_the_shared_resolver` — a mutation proof that `load_api_key` calls `resolve_secret` **and passes the env_file through**. Identity alone would pass on one shared *copy* of the old parser. |
| C11 one twin ignores `export ` | **B, and the count was wrong** | Old bug, NOT re-pinned as a bug; **BOTH** twins fail (re-derived). The FIX is pinned forward: `test_an_export_prefixed_line_is_honoured`. |

**§8-note-C (an inventory GAP I found):** C6 covers *blank-then-real*. Its **dual** —
`ANTHROPIC_API_KEY=real` followed by `ANTHROPIC_API_KEY=` — is in no inventory row, and the two
mechanisms **disagree**: the hand-rolled loop returns `"real"` (first non-empty wins), dotenv
returns `""` (last wins) → `RuntimeError`. I did **not** pin either behaviour. R2 partly settles it — the ruled snippet consults the file only when the ENVIRONMENT read came
back empty, so a duplicate key inside the file resolves by `dotenv_values`' last-wins, which I
pinned (`test_a_blank_declaration_does_not_shadow_a_later_real_one`). The *dual* (real-then-blank
inside one file) is still unpinned and still unasked; dotenv's last-wins matches shell semantics
and I would take it. Flagged, not decided.

---

## 9. Mechanical migrations the builder must make (authorised, not discovered)

These pre-existing tests construct the retired shape. None is an adjudication — they are field
renames — so I left them for the builder rather than churn 8 files:

| file | sites |
|---|---|
| `loresigil/tests/test_factory.py` | docstring ×3, `MissingApiKeyError` import, `api_key_env` ×4, `TestFactoryKeyResolution` (whole class → the property now lives at the config boundary) |
| `loresigil/tests/test_factory_voyage_context.py` | docstring ×2, import, `api_key_env` ×4, two `MissingApiKeyError` raises |
| `loresigil/tests/test_voyage_batch.py` | `EmbeddingConfig(..., api_key_env=env_name)` ×2 |
| `loresigil/tests/test_tei_prompt_name.py` | `api_key_env=_TEI_KEY_ENV` ×4 |
| `loremaster/tests/test_embedding.py` | `MissingApiKeyError` import, `_embedding_config(api_key_env=…)`, `test_missing_api_key_env_fails_loud` |
| `loremaster/tests/test_embedding_context_backend.py` | import, `api_key_env` ×2, `test_missing_api_key_env_fails_loud` |
| `loremaster/tests/test_embedding_prompt_name.py` | **NOT a field rename (ruling R13).** It has no `monkeypatch.setenv`, `LORE_TEI_KEY` is in no conftest, and **5 tests raise `KeyError`** once `to_loresigil_config` performs IO. **Add an env fixture; `to_loresigil_config` now performs IO.** Authorised here so the builder is not trapped (C-DEF). |
| **`scripts/search_score_survey.py`** (**PRODUCTION — MANDATORY, not optional**) | `_make_embedder` constructs `loresigil.factory.EmbeddingConfig` directly with `api_key_env=`. It is a **THIRD** production consumer; `lore_impact` reported 2 and missed it (lore finding **#233**). After the reshape it raises `ValidationError` **at runtime**, and **mypy cannot catch it because `scripts/` is not a typecheck member.** Migrate to `api_key=resolve_secret(...)`. |
| **`skills/lore-deploy/scripts/probe_embed.py`** (**ruling R14 — R6's migration is REVERSED**) | **DO NOT migrate it to the shared resolver.** Stdlib-only by design; `lore_deploy.py` branches on its exit codes. Fix **B3 in place, stdlib-only**: `if not key` → `if not key or not key.strip()`. Two pins guard it: the ledgered-duplicate pin and the stdlib-only import pin. ⚠ **R22 sibling note:** it has TWO wire sites (`_poll_health`, `_observe_dim`), both already building the header **per request** — i.e. shape B by construction. Fix the shared `_resolve_key`, and do not consolidate them into a client-level header while "tidying". |
| **`loremaster/loremaster/calibration/counting.py`** + **`scripts/token_survey.py`** (**rulings R10 + R19 + R22** 🔴) | ⚠ **THIS ROW WAS STALE AND IS REWRITTEN (R23).** It previously said *"bake it into the httpx client as `loresigil/tei.py` does … either shape passes"* — **measured false**: that build is `W-SHAPEA`, **2 RED** under R19. A builder following it verbatim wrote the shape R19 forbids. **The ruled shape is B, and only B: build NO auth headers at construction on either arm; render them per request.** `self._headers` is deleted; the credential is held as a `SecretStr` and unwrapped inside a per-request header builder. **R22: this applies to BOTH counters — `AsyncClaudeTokenCounter` AND the sync `ClaudeTokenCounter`** — and to `MultiModelClaudeCounter`, which shares one client across N sync counters. Every `self._headers` reader moves with it. |
| **`loremaster/loremaster/index/cli.py`** (**R17/R21/R24**) | `:112` — retire the username round-trip. ⚠ **NOT "a plain env read" (R24): that is a NEW unlisted `os.environ` site and reddens `test_every_environment_read_is_the_entry_point_or_allowlisted`** (2 RED, measured). **Mechanism: add a NON-SECRET sibling in `loremaster/config.py` — e.g. `resolve_config_value(env_var_name) -> str` — and call it.** That keeps the read inside the ONE module the gate permits, and keeps the fail-loud naming. `:113`'s password **stays wrapped**. |
| **`loremaster/loremaster/server.py`** (**R17/R21/R24**) | `:6752` — retire the username round-trip. ⚠ **NOT "a plain env read" (R24): that is a NEW unlisted `os.environ` site and reddens `test_every_environment_read_is_the_entry_point_or_allowlisted`** (2 RED, measured). **Mechanism: add a NON-SECRET sibling in `loremaster/config.py` — e.g. `resolve_config_value(env_var_name) -> str` — and call it.** That keeps the read inside the ONE module the gate permits, and keeps the fail-loud naming. `:6753`'s password **stays wrapped**. Its `except KeyError` at `:464` is unrelated and does not cover this site (re-derived). |
| **`loremaster/loremaster/scout.py`** (**R17/R21/R24**) | `:728` — retire the username round-trip. ⚠ **NOT "a plain env read" (R24): that is a NEW unlisted `os.environ` site and reddens `test_every_environment_read_is_the_entry_point_or_allowlisted`** (2 RED, measured). **Mechanism: add a NON-SECRET sibling in `loremaster/config.py` — e.g. `resolve_config_value(env_var_name) -> str` — and call it.** That keeps the read inside the ONE module the gate permits, and keeps the fail-loud naming. `:729`'s password **stays wrapped**. |
| **`scripts/search_score_survey.py`** (**R17/R21/R24**, second change to this file) | `:696` — same mechanism (`resolve_config_value`, imported like `resolve_secret` already is). `:697`'s password **stays wrapped**. Its comment *"exactly as at the other four `resolve_secret` user sites"* becomes false and must go with it. |
| **`skills/lore-deploy/scripts/conformance_provenance.py`** + its test (**the SEVENTH, §0.16.7**) | `WORKSPACE_MEMBERS` gains `lorerunes`, **and** `test_conformance_provenance.py`'s frozen `EXPECTED_MEMBERS` tuple gains it too (the stub mutation-proved that tuple is pinned: 7 tests redden). Without both, R29's own in-image guard is blind to the member R29 mints. |
| **`scripts/snapshot_gc.py`** (**R17/R21/R24 — with the caveat**) | `:332` retires like the other four, same `resolve_config_value` mechanism — **and it is the ONLY one of the five whose `KeyError` is CAUGHT**: `main` renders it into a clean `_EXIT_ERROR`. So `resolve_config_value` **must raise a naming `KeyError`**, not return `None` or raise a bare one, or this CLI's diagnostics degrade silently. That requirement is why the shared sibling is the right mechanism rather than five inline reads. `:333`'s password **stays wrapped**. |
| **`scripts/comms_consumer_eval.py`** (**PRODUCTION — ruling R7**) | `_amain`'s `os.environ.get("ANTHROPIC_API_KEY")` presence check → the shared resolver. Its `ENV_READ_ALLOWLIST` entry is already deleted, so leaving it reddens `test_every_environment_read_is_the_entry_point_or_allowlisted`. |

⚠ **REQUIRED CO-RUN (ruling R25): `loremaster/tests/test_calibration_counting.py`.** R19's shape
change is **invisible to this packet's own five suites** — only that file exercises the counters'
request path, so it must be run alongside them or the shape change ships unverified against its
own existing contract. `TestApiKeyAcquisition`'s three tests survive the resolver consolidation
unchanged (checked); the rest of the file is what covers R19.
`loremaster/tests/test_config.py` — every `api_key_env` there is **loremaster's** config (B10),
unchanged. Not a corpse.

---

## 10. Receipts

### 10.1 At base `251d112` — the RED the builder inherits
```
loremaster/tests/test_secret_leak_vectors.py  test_secret_resolution_seam.py
test_secret_typing.py  test_logging_setup.py  loresigil/.../test_factory_secret_resolution.py
124 failed, 255 passed in 13.98s
```
**379 tests collected, 0 collection errors** (204 → 222 → 305 → 311 → 337 → **348** after R19–R21). Per file: leak-vectors 47R/130G ·
resolution-seam 39R/50G · secret-typing 2R/22G · logging-setup **0R/44G** (every survivor is
green at base *and* after — that is the point) · loresigil 17R/9G.

### 10.2 SATISFIABILITY RECEIPT A — the deletion half **+ R8** (steps 5+6, rebuilt)
Rebuilt after R8, because R8 changes production behaviour and a receipt that predates the change
is worthless. Final reference build: all eight retired symbols cut; `_scrub_text` reduced to the
labelled passes; **R8 implemented as known-scheme-preserved / everything-else-redacted**.
Eleven shapes verified:
```
Authorization: Bearer <k>            -> 'Authorization: Bearer ***REDACTED***'
Authorization: Basic <k>             -> 'Authorization: Basic ***REDACTED***'
Authorization: Token <k>             -> 'Authorization: Token ***REDACTED***'    # was LEAKING
Authorization: Mutual short123       -> 'Authorization: ***REDACTED***'          # was LEAKING
Authorization: Negotiate <k>         -> 'Authorization: ***REDACTED***'
Authorization: <k>                   -> 'Authorization: ***REDACTED***'
authorization=<k> endpoint=ws://x    -> 'authorization=***REDACTED***'
x-api-key: <k>                       -> 'x-api-key: ***REDACTED***'
sent Bearer <k> up                   -> 'sent Bearer ***REDACTED*** up'
curl -H 'Authorization: Bearer <k>'  -> "curl -H 'Authorization: Bearer ***REDACTED*** https://api/x"
password=<pw> endpoint=ws://x/rpc    -> 'password=***REDACTED*** endpoint=ws://x/rpc'
```
```
loremaster/tests/test_secret_leak_vectors.py loremaster/tests/test_logging_setup.py
204 passed in 1.48s
```
**0 failed** — including the new R8 interaction-ORDER pin and the three-door
anti-regression pin. And the whole resolver half in the same build:
```
loremaster/tests/test_secret_resolution_seam.py
9 failed, 48 passed        # every one of the 9 is the loresigil half I did not build
``` Restored: md5 `831ca42e782e9ee9b4533dc750166ccc` before and after; `git status` on
every production tree empty.

⚠ **This receipt took SEVEN builds and every failure was real** (§0.5): the scheme/label
collision, the leading-word mis-parse, one of my own pins over-constraining the mechanism, and —
on the final pass — **my own R5 rider pin failing self-referentially**, because it grepped raw
lines and matched its own explanatory comment and its own predicate. Rewritten as an AST walk over
`ast.Assert.msg`, which structurally can only see what a failing pin would actually PRINT, plus a
positive control (`test_the_scan_for_overclaiming_messages_can_actually_fire`) that hands it a
synthetic overclaiming message and proves it fires. **Across the whole contract: five reference
builds, seven real defects, every one in work I had already convinced myself was correct.** The
recurring instrument was never review — it was a ∀ fixture matrix and a build that had to actually
go green.

⚠ **Its FIRST run was `1 failed`, and the failure was a real defect in my own contract:** the
re-authored `stack_info` fixture split the logging call across lines, and Python renders only the
line that raised — so the credential never reached the render and the pin was vacuous.
Cold-audit R3, repeated by me, in the file that documents R3. Fixed, plus a **second positive
control** asserting the labelled call site is actually present in the rendered stack.

### 10.3 SATISFIABILITY RECEIPT B — the R2/R3 resolver half *(new, this correction)*
Built the ruled shape verbatim — `resolve_secret(env_var_name, env_file=None)` with
`dotenv_values`; `load_api_key` as a thin caller translating `KeyError`→`RuntimeError`;
`token_survey` aliasing it; `python-dotenv` declared — and ran the resolution-seam suite:
```
loremaster/tests/test_secret_resolution_seam.py
9 failed, 41 passed in 5.50s     (from 27 failed, 23 passed)
```
**All four R1/R2/R3 classes went fully GREEN** — `TestResolveSecretIsTheUnifiedLookup` (13),
`TestTheEnvFileFallbackIsNotAvailableToTheServer` (4), `TestLoadApiKeyRoutesThroughTheSharedResolver`
(8), `TestPythonDotenvIsDeclaredAndActuallyUsed` (3). **Every one of the 9 residual failures is the
loresigil half, which I deliberately did not build** (composition root + `_resolve_api_key`
deletion). So: the correction's pins are proven satisfiable against the ruled shape, and I have
receipts rather than an opinion that I encoded the ruling correctly.

⚠ **This run also caught two real bugs in my own contract**, both before shipping:
1. `NameError: resolve_secret is not defined` — `ruff --fix` had removed the import earlier, when
   it was genuinely unused; the R2 class then called it. 13 pins were RED for the wrong reason.
2. `test_the_scan_finds_the_population` asserted `>= 8` against a helper that returns **7** —
   because it de-duplicates `(key, passes_file)`, so **13 raw `resolve_secret` calls collapse to 7
   distinct site keys**. I had written the threshold off the RAW count. **That is the
   two-populations conflation this report warns about in three separate places, committed by me,
   in the contract that warns about it.** Fixed, with both numbers now stated in the pin's comment.

### 10.4 MUTATION PROOF — R3's pin can actually fail
Declared-RED node ids taken from `--collect-only` **before** the run (never transcribed from the
output — that is the tautology in a new costume). Mutation: add `env_file=Path('.env')` to
`scout.py::from_config`, a server-path caller R3 names by name.
```
2 failed, 2 passed, 46 deselected
FAILED …TestTheEnvFileFallbackIsNotAvailableToTheServer::test_no_server_path_call_site_passes_an_env_file
FAILED …TestTheEnvFileFallbackIsNotAvailableToTheServer::test_the_allowlisted_site_actually_passes_one
E   AssertionError: the env_file detector sees ['loremaster/calibration/counting.py::load_api_key',
    'loremaster/scout.py::from_config'] where the ruling permits [...::load_api_key]
```
Both directions fired and the offending site is named in the message. Restored byte-exact.

### 10.5b MP5 — mutation-proven against the build that was BYTE-IDENTICAL

Reference build v9 = deletion + R8 + R2/R5/R12 + **R19 shape B**:
```
test_secret_leak_vectors.py  test_logging_setup.py     217 passed, 0 failed
```
**MUTATION W-R10a** — shape A applied to the injected arm only, owned client unauthenticated.
Mutation landing asserted (`assert old in s, "TARGET ABSENT"`) and behaviour confirmed:
```
W-R10a LANDED: owned client is UNAUTHENTICATED
SANITY owned-arm x-api-key present: False        <- production would 401
2 failed  — test_the_OWNED_client_arm_is_authenticated
            test_an_injected_client_is_not_mutated
```
**Byte-identical-to-correct → 2 failed.** Restored byte-exact.

### 10.5 THE TWO ROUND-1 BLOCKERS — mutation-proven against the adversary's own wrong builds

Declared-RED node ids taken from `--collect-only` **before** any mutation (17 collected across
the two new classes). Reference build v8 = deletion + R8 + R2/R5/R12 + **R10's source fix**.

**Baseline — the contract's own suites on v8:**
```
test_secret_leak_vectors.py  test_logging_setup.py  test_secret_resolution_seam.py
9 failed, 276 passed        # all 9 are the loresigil half, deliberately not built
                            # leak-vectors + logging-setup: 0 failed
```

**MUTATION A — revert R10's source fix (retain the header dict).** This is the build the
adversary scored **204 passed / 0 failed** on:
```
4 failed  — test_the_async_counter_does_not_retain_the_raw_key
            test_the_counters_state_does_not_leak_through_the_production_log_path[json]
            test_the_counters_state_does_not_leak_through_the_production_log_path[keyvalue]
            test_an_injected_client_is_still_authenticated
```
Both end-to-end formats fire — the exact six-path leak, now visible.

**MUTATION B — `_scrub_value` stops recursing** (the adversary's `W-COSMETIC`, also **204/0**):
```
8 failed, 213 passed   (full leak-vectors + logging-setup run)
   test_every_container_shape_recurses[tuple | dict-in-list | list-in-dict]
   test_it_holds_end_to_end_through_the_production_sink[json | keyvalue]  … and 3 more
```

**204/0 → 4 failed and 204/0 → 8 failed.** Both restored byte-exact afterwards.

### 10.6 Tree hygiene
All mutated production files restored from `cp -a` content backups (never from `git checkout`):
`logging_setup.py` (×3 reference builds), `config.py`, `counting.py`, `token_survey.py`,
`scout.py`, plus `loremaster/pyproject.toml` and `uv.lock` (which `uv run` had re-resolved).
```
git status --short -- loremaster/loremaster loresigil/loresigil lorescribe scripts skills docs uv.lock loremaster/pyproject.toml
(empty)
```
**Zero production files modified.** The working tree carries only the 4 test files + this report.

### 10.7 Gates
`uv run ruff check loremaster/tests/ loresigil/tests/` → **All checks passed!**

`mypy`: every error in the tree is one of exactly two shapes, both of which resolve the moment the
builder lands the ruled API — `"EmbeddingConfig" has no attribute "api_key"` and
`Too many arguments for "resolve_secret"`. Verified:
```
mypy loremaster/loremaster loremaster/tests | grep error: | grep -vE 'api_key|Too many arguments for "resolve_secret"'
mypy loresigil/loresigil loresigil/tests   | grep error: | grep -v api_key
(both empty)
```
There is no unrelated type delta.

## 11. Realism-&-independence checklist

- ☑ **Production-realistic inputs.** Credential fixtures use the real families (`pa-` +
  base64url for Voyage/TEI, `sk-ant-api03-` for Anthropic, an operator-chosen low-entropy root
  password), with their entropies **measured** against the threshold being deleted and stated in
  the module docstring. Paths are the four hashy shapes #227 was filed for. Prose fixtures use
  warehouse-ops text matching the sibling suites' register.
- ☑ **Independent expected values.** The oracle for "the credential did not appear" is a substring
  search for a known fake value over the rendered bytes — never the implementation's notion of
  redaction. The wire assertion is `header == f"Bearer {key}"`, derived from the HTTP spec.
  Function names come from the live AST, not from the redactor. Dotenv semantics were **measured**
  before being asserted. *Tautology check:* the header pin would fail on `Bearer **********`, on
  `Bearer Bearer KEY`, and on one-arm-hardcoded — three plausible wrong builds.
- ☑ **Seam / boundary coverage.** Three seams exercised with real handoffs, not mocks-on-both-sides:
  `lore.yaml`→loresigil config (all fields, non-default), loresigil config→HTTP header (real request
  ×3 arms), and `LogRecord`→emitted bytes (both formatters, end to end through `configure_logging`).
- ☑ **Magnitude / sanity bounds on derived outputs.** Corpus size ≥800, ≥50 names ≥24 chars,
  ≥8 unwrap sites, ≥6 env reads, ≥10 shared fields, ≥8 loresigil files, ≥2 masks in the config
  repr, and `len(...) == 1` on both one-implementation pins. Every scan has one — these are the
  assertions that stop a broken instrument reading as a clean tree.
- ☑ **Shared domain conventions, never hardcoded literals.** `ANTHROPIC_API_KEY_ENV` imported from
  production; the harness database name built by the production `unique_database()`; the label
  alternation read out of the compiled `_ASSIGNMENT_RE`; `EMBEDDING_DIM` from `loresigil.tei`;
  the emitting namespace from `LORE_NAMESPACES[0]`; `SECRET_MASK` pinned once, as pydantic's
  contract, and explained.
- ☑ **Hostile fixtures for rendered stored text.** The M1 literal-in-source fixtures (labelled and
  unlabelled) are forgery-shaped by construction: a credential written into source that a traceback
  quotes verbatim. Multi-line hostility is covered by the exception-cause and `__notes__` carriers
  and by `stack_info`. *Narrower than the usual clause because this unit renders TRACEBACKS, not
  stored user free text — the sanitiser seam clause does not apply here.*
- ☐ **Input accounting (totality) for collection transforms** — **not applicable: no collection
  transform.** No unit in packet 42 consumes a caller-supplied collection of items and emits
  per-item results. `_scrub_value`'s container recursion is the nearest thing and is pinned
  (`extra-nested` carrier + `test_scrub_value_leaves_non_string_scalars_untouched`).

---

## 12. What I would tell the adversary to attack first

1. **The A18 paired-control design.** If a carrier's bare-`str` leg leaks for a reason unrelated to
   the catch-all, the pairing is decoration. Perturb the carriers.
2. **`_config_for`'s transport injection** (`embedder._client._transport = …`). Validated against
   the live httpx API on all three arms *before* writing it, but it is a private attribute.
3. **`test_the_bearer_header_string_is_built_in_exactly_one_module`** — it forces a consolidation
   the packet implies but never states. Is `== 1` the right number, or am I legislating design?
4. **The `UNWRAP_ALLOWLIST` category set.** Five categories, closed. Is `NOT_A_SECRET` (5 of 11
   entries — the username unwraps) a legitimate category or a laundering device?
5. **`test_the_module_prose_no_longer_teaches_a_mechanism_it_does_not_run`** — a phrase blocklist,
   which is exactly the "enumerate the forbidden and lose" shape. It is the only pin here I cannot
   defend on principle; I kept it because served English has no other guard and the alternative
   was nothing.
6. **`test_the_emptiness_rule_is_stated_honestly_and_not_overclaimed`** (R5's rider) — it greps
   this module's own source for an overclaiming phrase. Same objection as 5: it is a phrase
   blocklist. I could not think of a mechanical form of "does this message describe this
   assertion", and said so rather than dressing it up.
7. ~~**The R8 scheme list is a name list.**~~ **FOUND AND CLOSED while writing this line** — and
   the closing changed a fact I had already written down wrongly. I first wrote that the
   reference build "degrades safely for an unknown scheme". **It does not.** Measured:
   `Authorization: Mutual short123` → `Authorization: ***REDACTED*** short123` — **it leaks
   today**, and `Negotiate`/`HOBA` leak the moment the catch-all goes. The set of HTTP auth
   schemes is open (RFC 7235 + vendor schemes), so a scheme allowlist is the exact
   "enumerate the forbidden and lose" shape, *in my own pin*. Closed by
   `test_an_UNKNOWN_auth_scheme_does_not_leak_its_credential_either` (4 schemes, none of them in
   any list the code may hold), which forces the fix to be general: redact whatever follows the
   leading scheme WORD, whatever that word is. **The lesson worth keeping: I caught this only
   because I made myself write down what an adversary should attack. The list is the instrument.**
