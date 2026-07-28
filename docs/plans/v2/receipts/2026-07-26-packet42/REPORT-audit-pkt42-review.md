# REPORT-audit-pkt42-review — Phase 7 fresh-context review, packet 42

> ⚠ **SUPERSEDED SYMBOLS (dated record):** mentions `_BRIEF_PUBLISH_`, a retired prefix (the
> private mint-retry constants deleted by finding #108 — `_txn.retry_on_conflict` owns that
> policy now). It appears here only inside REPRODUCED TEST OUTPUT: this record quotes the
> packet-11i/03b doc-banner failure that packet 42 inherited and verified as unrelated to its
> own work. Preserved as-written per the archive law; read it as history, not instruction.

brief-base v7 read

- **state:** done-with-deviations
- **deviations:** (1) I edited `CLAUDE.md` and `docs/plans/v2/DESIGN-LAW.md` — standing-law
  documents. Both carried a *measurably wrong count* introduced/left by this diff; I corrected
  the counts and the pointer only, changed no rule, and flag it here for an operator veto.
  (2) One wrong-build probe and one source mutation-proof ran while a full-suite run was in
  flight; I **discarded that run and re-ran clean** rather than reason about contamination.
  (3) **HEAD moved from `8dc1259` to `fbd6f36` mid-audit and a lead commit swept in my
  uncommitted `DESIGN-LAW.md` edit — see §6.2.** The two new commits are docs-only, so no
  finding or measurement here is invalidated.
- **Packages considered:** `python-dotenv` 1.2.2 — READ: `dotenv.dotenv_values` live against
  a fixture `.env` in this tree (interpolation + quoting behaviour), and installed version via
  `importlib.metadata` → **verdict: keep, ruling R2/R12 confirmed by measurement, not assumed**
  (see §5.3). `pydantic-settings` — READ: `loremaster/pyproject.toml` declares it; no module in
  the tree imports it → **verdict: still declared-but-unused; the packet pinned python-dotenv's
  declaration but left this one standing** (§4, D7). No mechanism was built by me; the seven
  fixes below are prose/derivation corrections and one docstring count.
- **decisions-needed:**
  1. **C1** — the typed-seam gate exempts a filename SUFFIX (`endswith("auth.py")`), demonstrated
     to let a byte-identical offender through under the name `oauth.py`. Frozen file → routes to
     `tdd-contract`. One-line patch supplied.
  2. **D1** — packet 42 deleted ten symbols and registered none in `_RETIRED_SYMBOLS`. Registering
     them reddens the gate against this packet's own LIVE spec prose, so it is a scope call.
  3. **D2** — two functions named `build_auth_headers` with different return contracts.
  4. Operator veto on the `CLAUDE.md` / `DESIGN-LAW.md` edits above.
- **receipt pointers:** §1 the tenth defect · §2 fixes applied · §3 routed to `tdd-contract` ·
  §4 reported-not-actioned · §5 what I attacked and could not break · §6 gates.

---

## 0. Scope and method

Reviewed `git diff 6a21fb6..8dc1259` in `/home/ejprice/PycharmProjects/lore-pkt42`
(branch `pkt42-prevent-the-leak`) for reuse, quality, efficiency, DRY, standards adherence,
and spec coverage. All measurements below were taken by me in this worktree on **2026-07-27**
at `8dc1259` (plus my own edits where stated); every inherited number was re-derived.

lore's index points at the primary checkout, so **I did not use it** — every structural
question here was answered by direct `Read` / `git grep` / AST derivation over this worktree,
and by `./scripts/registration_sites.py`. Saying so per tool-honesty law.

Two source mutations were run in the real tree with `cp -a` content backups and restored
**byte-exact, md5-verified**; one probe file was created and deleted. `git status` after all
probes showed exactly my eight intended edits and nothing else.

---

## 1. THE TENTH DEFECT — a test THIS PACKET broke, filed as pre-existing

**Both the audit brief and commit `8dc1259`'s own message classify the two baseline failures as
"pre-existing, verified unrelated". One of them is not.**

`loremaster/tests/test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts`

```
E  AssertionError: the harness docstring says 36 test files import it; 37 actually do.
```

Re-derived with the pin's own AST predicate over both trees:

| revision | `_surreal_harness` importers |
|---|---|
| `6a21fb6` (base) | **36** |
| `8dc1259` (HEAD) | **37** |
| added | `loremaster/tests/test_secret_leak_vectors.py` |

`test_secret_leak_vectors.py` is **created by this packet** and does
`from _surreal_harness import unique_database`. The pin was GREEN at base and went RED because
of this diff. `8dc1259`'s message attributes both failures to one cause — `_BRIEF_PUBLISH_`
mentions in packet 11i/03b receipts — which is the true cause of the *other* failure only
(`test_retired_symbols`, independently confirmed still failing for exactly that reason, and
genuinely pre-existing).

**Why this is worth more than one line:** `_surreal_harness.py`'s own docstring says the two
counts *"cannot rot"* because they are pinned against an AST derivation. The mechanism worked
perfectly. Its RED was then read as somebody else's mess and carried into a commit message, a
close-out and an audit brief. **A pin that fires and is misattributed is worse than no pin**,
because it converts a live signal into a documented non-issue.

**Fixed:** `loremaster/tests/_surreal_harness.py` docstring `36` → `37`. Verified:
`1 passed, 56 deselected`.

---

## 2. Fixed in place

All eight are prose-or-derivation corrections. **No production behaviour changed by any of them.**

### 2.1 🔴 `loremaster/tests/_surreal_harness.py` — importer count 36 → 37
§1 above.

### 2.2 🟠 `CLAUDE.md` + `docs/plans/v2/DESIGN-LAW.md` — three mutually inconsistent counts
The section this diff ADDED to `CLAUDE.md` is headed **"THE SEVEN PLACES A NEW WORKSPACE MEMBER
MUST BE REGISTERED"** and warns that *"THIS LIST HAS BEEN WRONG TWICE."* Commit `8dc1259`'s own
message — the commit that ships this text — says the list *"was wrong FOUR times (five entries,
then six, then seven, then nine)"* and adds **sites 8 and 9**. The heading was never updated.
Meanwhile `DESIGN-LAW.md` §0 says *"Adding any workspace member touches **six** registration
sites — see repo CLAUDE.md … for the enumerated list."*

So the law about stale enumerations shipped with **three different counts across two documents,
none of them the truth.** That is this repo's #1 defect class occurring inside the section
written to name it — the same shape the inventory records for its own archived-report count.

Worse, `CLAUDE.md` instructed the reader to hand-roll
`grep -rn 'lorescribe' --include='*.py' …` — while `scripts/registration_sites.py`, a committed
script that DERIVES the answer, landed in the same commit and **is referenced from nowhere in
the repo** (`git grep` finds hits only inside the script itself and one untracked builder
report). brief-base §1 ranks *"a committed script that regenerates a measurement"* as the top
citation tier; the law pointed at a recipe instead of at the function.

**Fixed:** both documents are now **count-free** and cite `./scripts/registration_sites.py`.
The `CLAUDE.md` list is reframed as *annotations on the script's output* — the entries whose
consequence is worth knowing in advance — not a substitute for running it. The corrected
history (four wrong counts, and why the heading itself was the fourth) is recorded in place.
`DESIGN-LAW.md` records that its own "six" was the fifth.

### 2.3 🟠 `scripts/registration_sites.py` — the constant contradicts its own comment
```python
#: … Two is the smallest number that distinguishes "enumerates" from "imports one thing".
_MIN_MEMBERS_FOR_A_SITE = 3
```
The module docstring correctly documents **three** and explains why (two produced 82 unreadable
hits). The constant's own `#:` comment argues for two while the value is three — so the served
justification does not describe the code, in the tool built to find exactly that.
**Fixed:** the comment now records the measured trade and cross-references the bound it buys
(*"cannot see a registry that has fallen TWO members behind"*).

### 2.4 🟠 `skills/lore-deploy/scripts/test_conformance_provenance.py:24` — the interface list
```
* ``WORKSPACE_MEMBERS`` — ``("loremaster", "loresigil", "lorescribe")``.
```
This packet correctly widened, **in this same file**, the `EXPECTED_MEMBERS` constant, two test
NAMES that carried the count, and two class docstrings — and left the module docstring's restated
value behind. The file's own new comment says *"a member count in prose — or in a test NAME — is
the stale-natural-language class this repo pays for most often, and this file carried it in both
places."* It carried it in three.
**Fixed:** the value is no longer restated; the line points at `EXPECTED_MEMBERS`.

### 2.5 🟠 `skills/lore-deploy/references/lifecycle.md:220` — the deploy operator's doc
> *"asserts every workspace member (`loremaster`/`loresigil`/`lorescribe`) imports the baked artifact"*

This is the reference an agent reads to run the deploy. It teaches a three-member workspace.
**Fixed:** count-free, pointing at `conformance_provenance.py::WORKSPACE_MEMBERS`.

### 2.6 🟡 `loremaster/loremaster/logging_setup.py::LORE_NAMESPACES` — a subset with nothing saying so
`registration_sites.py` reports this line as a stale member-enumerating site. It is in fact a
**deliberate** subset (`lorerunes` emits no logs) — but the justification lives only in
`registration_sites.py`'s docstring, and that script's own output says *"a deliberate subset
should say so where it is written, so the next run of this script is read rather than
re-derived."*
**Fixed:** the reason is now at the site, with a named re-open trigger — *the day any `lorerunes`
module calls `logging.getLogger`, its records propagate to the ROOT logger and bypass both the
structured formatter and `RedactingFilter`.* That consequence was nowhere stated.

### 2.7 🟠 `loresigil/tests/test_factory_voyage_context.py:188` — a coverage claim that is false
The comment replacing the deleted `TestFactoryVoyageContextKeyResolution` says the property is
*"pinned for **all three backends** in
`test_factory_secret_resolution.py::TestAnAbsentCredentialFailsLoudAndNeverBuildsAKeylessEmbedder`."*
Verified: **every construction in that class passes `backend="tei"`** (three sites, lines 31/63/71
of the class). No `voyage-cloud` or `voyage-context` leg exists.

The deletion is nonetheless **sound**, and for a better reason than the comment gave: the new
guard is a pydantic `field_validator` on `api_key`, so it runs during model validation before any
backend arm is selected and `backend` cannot reach it. The property holds **by construction**; it
is **pinned on one backend**.
**Fixed:** the comment now states the structural reason, states the one-backend pin as a residual
instead of claiming three, and names the change that would make backend-independence stop being
structural (moving the blankness check off the field into `make_embedder` or a per-arm
constructor) — which is exactly the coverage this file deleted.

*(The sibling note in `test_factory.py` makes no backend claim and is accurate — two copies of one
explanation, one of which had drifted into a false claim. Cause form of the same finding.)*

### 2.8 🟠 `loremaster/loremaster/config.py::resolve_secret` — a ∀ claim true of one of two sources
Docstring, at `8dc1259`:
> *"The value is never stripped or otherwise mutated — a secret whose real content happens to
> include leading/trailing whitespace passes through byte-exact."*

Measured by me, python-dotenv **1.2.2**, in this tree:

| source | file/env bytes | resolved | byte-exact |
|---|---|---|---|
| environment | `'  sec ret  '` | `'  sec ret  '` | ✅ |
| `env_file`, unquoted | `KEY=  sec ret  ` | `'sec ret'` | ❌ **stripped** |
| `env_file`, trailing tab | `KEY=secret\t` | `'secret'` | ❌ **stripped** |
| `env_file`, quoted | `KEY="  sec ret  "` | `'  sec ret  '` | ✅ |

The claim was written when `resolve_secret` had **one** source and was carried verbatim after
R2 added a **second** with different semantics. That is the quantifier shape the inventory
itself names — *"does this claim still hold on every branch this ruling TOUCHES, or only the one
I DERIVED it on?"*

**The behaviour is correct and ruled** (inventory C5: dotenv owns quote/escape handling), and
**the contract already knows**: `test_secret_resolution_seam.py::test_the_value_is_byte_exact_from_either_source`
forces both sources and its comment records the quoting nuance precisely. So the knowledge
existed in a test comment and never reached the served surface — the exact gap this repo calls
its most expensive.
**Fixed (docstring only):** the claim is now scoped to *this function*, the file FORMAT's
stripping is stated with the measured examples, the *"a padded credential MUST be quoted in the
file"* consequence is spelled out, and the pin is cited.

---

## 3. Routed to `tdd-contract` — frozen contract files, not patched

### 3.1 🔴 C1 — the typed-seam gate's exemption is an unbounded name SUFFIX
`loremaster/tests/test_secret_typing.py::_auth_construction_offenders`:
```python
if display.startswith(_STDLIB_ONLY_EXEMPT_ROOT) or display.endswith("auth.py"):
    continue
```
`_INCOMING_AUTH_MODULE = "loremaster/auth.py"` is declared 40 lines above with a full paragraph
of R26-constraint-2 justification — and **`git grep` finds exactly one occurrence: its own
definition. It is never used.** The gate uses an unanchored suffix instead, which exempts any
file in any member named `auth.py`, and anything merely ENDING in it: `oauth.py`, `basicauth.py`,
`noauth.py`.

**Proven with a positive control** (byte-identical file, only the name changed, at HEAD):

| probe | verdict |
|---|---|
| `loresigil/loresigil/oauth.py` returning `{"Authorization": f"Bearer {token}"}` from a `str` param | `1 passed` — **silently exempt** |
| the same file renamed `loresigil/loresigil/wire.py` | `FAILED … assert not ["loresigil/wire.py:7 builds 'Authorization' outside the seam"]` |

Both probe files were deleted; `git status` on `loresigil/` is clean.

**Exposure today is NIL** — `loremaster/loremaster/auth.py` is the only matching file in the
scanned tree, and it is the intended exemption. **The gap is in the gate's REACH, not in the
codebase.** But this is the class `CLAUDE.md` has six receipts against — an instrument keyed on
a NAME, defeated by a name its author did not enumerate — sitting inside the gate R26 built to
end that class, with the exact constant needed to close it already present and unused.

**Patch (one line):**
```python
if display.startswith(_STDLIB_ONLY_EXEMPT_ROOT) or display == _INCOMING_AUTH_MODULE:
```
`display` for that file is exactly `loremaster/auth.py` (label + path relative to the member
root), so the equality holds today and the exemption becomes the single file R26 authorised.

### 3.2 🟡 C2 — `_SCANNED_MEMBERS` is still a private hand-list under a class that says otherwise
`TestEveryScannerSharesOneRootList` states: *"The fix is not to widen four lists — it is that
they **call one**, and that one is **derived from `pyproject.toml`**."* Three scanners now call
`_logging_fixtures.workspace_roots`. `test_secret_typing.py`'s own `_python_sources()` still
walks the hand-written `_SCANNED_MEMBERS` tuple.

Not a hole: `test_every_scanner_reaches_every_declared_workspace_member` and
`test_all_the_scanners_agree_with_each_other` both redden if it falls behind — verified by
reading, and consistent with `registration_sites.py` reporting `test_secret_typing.py:122` as a
site. But the class docstring overstates its own mechanism, which is R27.1's defect
(*"DERIVED from the live tree, never a hand-list" — it was a hand-list of 6*) recurring one
file over. Either derive it or narrow the claim.

### 3.3 🟡 C3 — the ONE-ENTRY-POINT gate only sees attribute access
`test_secret_resolution_seam.py::_environment_reads` matches `ast.Attribute` with
`attr in {"environ", "getenv"}`. `from os import environ` (or `getenv`) followed by a bare
`environ.get("KEY")` is an `ast.Name` and is invisible. The stated threat model is the honest
developer who *"adds a fourth `os.environ.get(...)` because it was easier than importing the
resolver"* — and `from os import environ` is honest, if unusual. Widening: also match `ast.Name`
with `id in {"environ", "getenv"}`, or flag `ImportFrom(module="os")` naming either.

### 3.4 🟡 C4 — `test_factory_secret_resolution.py` blank-credential class is a backend monoculture
(Frozen.) All three constructions use `backend="tei"`; the parametrisation varies the blank
*shape*, never the backend. Correct today because the guard is a field validator — but nothing
pins that it stays one, and this class is the named replacement for coverage deleted from **two**
backend-specific files (§2.7). One `backend="voyage-context"` leg would close it.

### 3.5 🟡 C5 — `test_logging_setup.py` credential constant duplicated as a bare literal
(Frozen.) `LITERAL_IN_SOURCE_LABEL_VALUE = "Kp9RmT2vX6bN4wQ8yH1jL5dF7gA3sZ0cUeIo"` (line 89) is
re-typed as a literal inside `_log_with_stack_info_from_a_literal_credential` (line 127) — the
duplication is unavoidable for the stack-render mechanic, since the value must appear *in the
source line*. But nothing ties the two together, so if they drift the assertion
`LITERAL_IN_SOURCE_LABEL_VALUE not in parsed[EXC_FIELD]` (line 488) goes **vacuous** while the new
positive control still passes. An `assert LITERAL_IN_SOURCE_LABEL_VALUE in inspect.getsource(...)`
would bind them. Same latent shape pre-exists for `LITERAL_IN_SOURCE`; this diff adds a second
instance.

---

## 4. Reported, not actioned

**D1 🟠 — the retired-symbol registry was not extended by this packet.**
`test_retired_symbols.py::_RETIRED_SYMBOLS` carries the discipline in its own comment: *"Add a
name here the moment you delete it — that is the whole discipline, and it costs one line."*
Packet 42 deleted `_TOKEN_RE`, `_ENTROPY_BITS_THRESHOLD`, `_shannon_entropy_bits`,
`_is_safe_high_entropy_run`, `_is_absolute_path_component`, `_PATH_BLOB_CHARS`,
`_PATH_SEPARATOR`, `_UUID_RE`, `MissingApiKeyError`, `_resolve_api_key`. **None is registered.**

It is *not* a one-liner, which is why I am reporting rather than doing it:
`docs/plans/v2/42-prevent-the-leak-delete-the-sanitizer.md` is a LIVE document that says
*"THEN DELETE `_TOKEN_RE`…"*, so registering that name reddens the gate until the spec prose is
rewritten, and `docs/plans/v2/receipts/2026-07-26-packet42/` would need a SUPERSEDED banner.
That is a scope decision.

**Recommendation:** register at minimum `_TOKEN_RE`, `_shannon_entropy_bits` and
`MissingApiKeyError`. A packet whose thesis is *"there is no next mole, because there is no
detector"* is precisely the case this registry exists for — and the registry's whole value is
that a future doc cannot prescribe the corpse.

**D2 🟡 — two `build_auth_headers`, one name, two contracts.**
`loresigil.voyage_http.build_auth_headers` returns **only** `{"Authorization": …}`;
`loremaster.calibration.counting.build_auth_headers` returns the **full request header set**
(`x-api-key` + `anthropic-version` + `content-type`). Each docstring justifies its own shape, and
R26 rules the two-seam split (the shared thing is the TYPE) — but the global naming convention is
*"once a name is chosen for a concept, use that exact name everywhere"*, and here one name carries
two concepts. The gate's `SEAM_FUNCTION = "build_auth_headers"` **requires** the shared spelling,
so this is a real tension rather than an oversight. Operator's call; **do not collapse the seams.**

**D3 🟡 — `resolve_secret` / `resolve_config_value` clone the blank-and-raise block.**
Both call the shared `lorerunes.is_blank`, so the *rule* cannot drift; what is duplicated is the
`if value is None or is_blank(value): raise KeyError(f"Required … {env_var_name!r} is unset,
empty, or whitespace-only; export it before starting lore.")` block, message included. Low value
to collapse, the messages are asserted in the contract, and `resolve_config_value`'s existence is
ruled (R17). Reporting per ONE-IMPLEMENTATION's *"duplication is a DESIGN decision, escalate it"*
rather than acting.

**D4 🟡 — `probe_embed.py`'s ledgered duplicate has gained a second re-open trigger nobody wrote
down.** R14's stated trigger is *"the day `probe_embed.py` runs under `_loremaster_python()`"*.
R14 predates R29: `lorerunes` now exists and is **stdlib-only by construction**, so the
hand-rolled `if not key or not key.strip()` could become `from lorerunes import is_blank` the
day `lorerunes` is importable from `sys.executable` — which does not require the interpreter
boundary to move. Worth adding as a second trigger on the `ENV_READ_ALLOWLIST` entry.

**D5 🟢 — residual R12's attribution is now slightly wrong.** The ninth wave records
*"the BASE scrubber mangles adjacent structure (`Bearer <k>'}` eats the closing quote/brace,
because the pattern ends `(\S+)`)"*, operator-ruled out of scope. Measured at HEAD: the NEW
`_AUTH_HEADER_RE` inherits it, so it is not only the base pattern —
`curl -H 'Authorization: Bearer sk-abc' https://x` → `curl -H 'Authorization: Bearer ***REDACTED*** https://x`
(closing quote eaten by `_AUTH_HEADER_RE`'s `(\S+)`, before `_BEARER_RE` ever runs). Still
cosmetic; noting only so the residual is not re-scoped as "pre-existing, therefore untouched by us".

**D6 🟢 — the unrecognised-scheme branch drops the rest of the LINE, not "the rest of the header
value".** Module comment: *"An unrecognised leading word is therefore redacted ALONG WITH the rest
of the header value."* `_redact_auth_header` returns `label + REDACTED`, discarding
`rest_of_line`. Measured: `Authorization: Negotiate abc status=500 elapsed=3ms` →
`Authorization: ***REDACTED***`. The behaviour is correct and errs safe; the prose understates
what is lost. Bounded to one field, because `RedactingFilter` scrubs per-field and `[^\n]*` stops
at a newline — worth stating, since "we lose the rest of the line" sounds much worse than it is.

**D8 🟠 — `scripts/test_snapshot_gc.py::_wire_fakes` gained a seam fake nothing asserts on.**
The diff adds `monkeypatch.setattr(gc, "resolve_config_value", lambda name: f"dummy-{name}")`.
Nothing in the file asserts on `user`, `password`, `signin` or `connect`, so the `setattr` proves
only that the symbol is *imported*. **A build that passed `args.password_env` where
`args.user_env` belongs would pass this suite** — and `snapshot_gc.py` is the one site whose
`KeyError` is caught and rendered as a clean CLI error (R21), which is exactly why the seam was
given a naming failure. The same hole pre-exists for the `resolve_secret` fake; this diff widens
it to a second seam. Test-smell → routes rather than being patched here. One assertion on the
recorded `signin` arguments closes both.

**D9 🟡 — `test_embedding.py` / `test_embedding_context_backend.py` `test_missing_api_key_env_fails_loud`
traded a bespoke exception for a builtin.** `pytest.raises(MissingApiKeyError)` →
`pytest.raises(KeyError)` + `assert _KEY_ENV in str(excinfo.value)`. The migration is correct
(`MissingApiKeyError` is retired) and the added name assertion is new coverage — but `KeyError`
naming the variable is what a bare `os.environ[name]` raises from *anywhere* in the chain, so the
pin no longer localises the failure to the composition root. Structurally covered by
`test_factory_secret_resolution.py::TestLoresigilResolvesNothing`; noting the local weakening.

**D10 🟡 — `test_embedding_prompt_name.py` resolves one literal env-var name everywhere.**
The new autouse fixture exports `_TEI_KEY_ENV = "LORE_TEI_KEY"` and `_BASE_EMBEDDING_FIELDS`
hardcodes the same name, so **every** `to_loresigil_config` call in the module resolves one
literal — a build that hardcoded `"LORE_TEI_KEY"` instead of reading `config.api_key_env` passes
the whole file. Not a repo-wide hole (`test_embedding.py` uses `"LORE_EMBED_TEST_KEY"`,
`test_embedding_context_backend.py` uses `"LORE_VOYAGE_CONTEXT_KEY_TEST"`), so the parameter-value
monoculture is bounded to one file. Worth one differing value.

**D11 🟢 — two `test_logging_setup.py` path-survival tests now pass for a new reason,
self-disclosed.** `TestOrdinaryPathsSurviveRedaction` says so in its own prose (*"they survive
because nothing inspects an unlabelled run at all"*), and the class's discriminating leg
(`password={FAKE_BEARER_TOKEN}`, a label the packet KEEPS) still fires — so the class
discriminates even though the individual tests would pass against a gutted `_scrub_text`.
Honest as written; recorded so a later reader does not re-discover it as a defect.

**D7 🟢 — `pydantic-settings` is still declared-and-unused.** The spec's Scope IN #2 said
*"Investigate `pydantic-settings` first — it is already a declared-but-unused dependency."* It was
investigated (R2 chose `python-dotenv`, correctly and with reasons), and
`TestPythonDotenvIsDeclaredAndActuallyUsed` now pins that `python-dotenv` is *declared AND used* —
citing `pydantic-settings` in its own docstring as the cautionary example of declared-but-unused.
The cautionary example is still in `loremaster/pyproject.toml:19` and imported by nothing. Not
packet-42 scope; surfaced because the packet's own new pin names it.

---

## 5. What I attacked and could NOT break

Recorded because a review that only lists defects understates a diff this strong.

### 5.1 `lorerunes.is_blank` sharing — proven by SOURCE mutation, not only by the contract's monkeypatch
Backed up `lorerunes/lorerunes/blankness.py` (`cp -a`), replaced the body with `return False`,
ran both callers' suites:

```
FAILED loremaster/tests/test_secret_resolution_seam.py ... (6 tests)
FAILED loresigil/tests/test_factory_secret_resolution.py ... (4 tests)
FAILED lorerunes/tests/test_smoke.py ...
18 failed, 74 passed
```
Restored: `md5 6d8118569feacff9caec913ee84a7b25` identical before and after, `git status` clean,
`28 passed` on re-run. **DRY here is real, not routed** — an independent instrument agrees with
`test_MUTATING_the_predicate_moves_BOTH_callers`.

### 5.2 R22's sync twin — I expected a hole and there was none
I suspected the owned-arm wire pin covered only the ASYNC counter. Built the wrong build
**W-SYNCOWNED** (sync `ClaudeTokenCounter` authenticates only when a client was injected):

```
FAILED loremaster/tests/test_secret_leak_vectors.py::TestTheSyncCounterTwinIsAuthenticatedToo::test_the_OWNED_client_arm_is_authenticated
FAILED loremaster/tests/test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_no_auth_header_is_built_outside_a_seam
2 failed, 401 passed
```
Two independent instruments caught it. `scripts/token_survey.py` restored byte-exact
(`md5 e2dce155f89df82b358d356fa742ec5f`, `git status` clean). **R22 is satisfied.**

### 5.3 R12's `interpolate=False` — re-derived, not inherited
python-dotenv 1.2.2, live: `K=pw${NOPE}tail` → `interpolate=True` yields `'pwtail'` (credential
**shortened**), `interpolate=False` yields `'pw${NOPE}tail'`. Production passes
`interpolate=False`. Ruling confirmed by measurement.

### 5.4 Efficiency — the deletion made the hot path FASTER, and nothing was reintroduced
`RedactingFilter` runs on every record, so this was the brief's specific question. Timed the base
`_scrub_text` (loaded from `git show 6a21fb6:…`) against HEAD's over a realistic 21.7 KB corpus
(tracebacks, absolute paths, ULID chunk ids, a bearer header), 200 reps:

| implementation | time |
|---|---|
| base — entropy catch-all + per-candidate `Counter`/`log2` | **0.334 s** |
| HEAD — three labelled `re.sub` | **0.259 s** |

**1.29× faster.** Same number of passes (three before, three after); the entropy callback is gone
and nothing replaced it. `_AUTH_HEADER_RE`'s `(\S+)([^\n]*)` has no nested-quantifier
backtracking shape. **No hot-path cost was reintroduced.**

### 5.5 The spec's Exit receipt — the same traceback, before and after
The spec requires *"the same traceback rendered before and after"* as the recovered-data receipt.
Produced here (task #2 still lists it as pending):

```
=== BEFORE (base 6a21fb6) ===
  File "/tmp/ci/090685cb-2064-498d-8479-e141e4fd4ea5/loremaster/server.py", line 6752, in build_app_context
  File "/nix/store/9k2vq0m3d7abcdefghijklmnopqrstuv-python3/lib/config.py", line 812, in _enforce_search_budget
  chunk_id=lore_chunk:***REDACTED*** ***REDACTED***

=== AFTER (HEAD) ===
  ... identical frames ...
  chunk_id=lore_chunk:01JQ8Z5R7X9K2M4N6P8Q0S2T4V commit=3fd0fee9c1e2b3a4d5f60718293a4b5c6d7e8f90
```
Redactions on a credential-free traceback: **2 → 0**; the AFTER output is **byte-identical to the
input**. The ULID chunk id and the git SHA — a correlation key and a provenance stamp, both
load-bearing for debugging — were being destroyed and now survive.

### 5.6 Scrubber battery — 24 shapes
All 24 idempotent. `Authorization: Basic <cred>` **is** scrubbed with the catch-all gone (the
#235 rider, mutation-proof intact); `Basic`/`Digest`/`Token` keep their scheme word; an
unrecognised scheme redacts the whole value; `x-api-key` line form covered; `?key=` and
`?access_token=` leak **exactly as the pinned bound says** and `?api_key=`/`?token=` do not;
UUID paths, nix-store hashes, git SHAs, ULIDs and production function names all survive verbatim.
Nothing behaved outside what the contract pins or ledgers.

### 5.7 Spec coverage
All six Scope-IN items and all three riders are implemented and pinned: type coverage through
`loresigil` (§1), one entry point + `resolve_config_value` (§2, R17 shrink 10→5 verified in
`UNWRAP_ALLOWLIST` — 6 entries, matching R32.1's measured 6), the unwrap allowlist (§3), the M4
locals pin **with a positive control that proves it can see a leak** (§4), the deletion (§5), and
the retired bounds removed rather than left vestigial (§6, `TestBareHexRunsStayRedactedKnownBound`
deleted with a note at `test_logging_setup.py`). #235 landed in one commit with the deletion;
#221's runtime-red requirement is met (I found no pin demonstrated only by mypy).

---

## 6. Gates — after my edits

| gate | result |
|---|---|
| `./scripts/typecheck.sh` | **5 members, 0 errors** (`lorerunes`, `lorescribe`, `loresigil`, `loremaster`, `skills`) |
| `uv run ruff check .` | **All checks passed!** |
| `uv run pytest -q -n auto` (baseline, `8dc1259`) | 2 failed / 7373 passed / 17 skipped / 3 xfailed — reproduced exactly |
| `uv run pytest -q -n auto` (after my edits) | see §6.1 |

### 6.1 Post-fix full-suite tail
```
1 failed, 7374 passed, 17 skipped, 3 xfailed, 1 warning in 191.92s (0:03:11)
FAILED loremaster/tests/test_retired_symbols.py::TestNoFileReferencesARetiredSymbol::test_no_file_references_a_retired_symbol
```
**Baseline 2 failed / 7373 passed → after my edits 1 failed / 7374 passed.** The recovered test is
§1's `test_the_harnesss_docstring_counts_are_the_DERIVED_counts`. The remaining failure is the
genuinely pre-existing `test_retired_symbols` one (packet 11i/03b receipts missing `_BRIEF_PUBLISH_`
SUPERSEDED banners — reproduced and read in full, unrelated to this diff). **No fix of mine broke
anything.**

Re-verified after my last edit against the CURRENT tree (see §6.2): scoped run over
`test_retired_symbols`, `test_surreal_harness`, `test_secret_typing`, `test_secret_leak_vectors`,
`test_secret_resolution_seam`, `test_logging_setup`, all of `loresigil/tests` and `lorerunes/tests`
→ **1 failed, 811 passed, 1 skipped** — same single pre-existing failure.

### 6.2 ⚠ HEAD MOVED UNDER THIS AUDIT, AND MY UNCOMMITTED EDIT WAS SWEPT INTO A LEAD COMMIT
The brief pinned HEAD at `8dc1259`. While I was working, the lead advanced the branch:

```
fbd6f36 docs(pkt42): eleventh wave R37-R40 — DEPLOY BLOCKED, three widenings
5261933 docs(pkt42): tenth ruling wave R33-R36 — the blind reader found a regression WE caused
8dc1259 fix(pkt42): registration sites are DERIVED, not listed — plus sites 8 and 9   <- brief's HEAD
```

**`git diff --stat 8dc1259..fbd6f36` touches exactly two files, both documentation** —
`docs/plans/v2/DESIGN-LAW.md` and the packet-42 `REMOVED-BEHAVIOR-INVENTORY.md`. **No production
or test code changed**, so every measurement, mutation proof and gate run in this report remains
valid at `fbd6f36`.

**But `5261933` swept in my uncommitted `DESIGN-LAW.md` edit.** `git show 5261933 --
docs/plans/v2/DESIGN-LAW.md` contains my exact `-**six** … +derive them with
./scripts/registration_sites.py` hunk, committed under a message about the tenth ruling wave.
I did not stage or commit anything (brief-base §2); a `git commit -a` / `git add -A` in a worktree
with a live agent in it did.

**This is worth a process note beyond packet 42:** parallel agents in ONE shared worktree means any
`-a` commit captures whatever another agent has half-written, and attributes it to an unrelated
message. Two other agents also landed reports in this tree during my run
(`REPORT-audit-pkt42-security.md` 14:32, `REPORT-blindreader-pkt42.md` 14:30). The repo's law
already says *"commit at natural boundaries"* and *"an agent mutating an uncommitted tree `cp -a`s
first"* — the missing clause is the converse: **a lead committing a shared worktree must stage
paths explicitly, never `-a`, while agents are live in it.** Recommend the lead check `5261933`
and `fbd6f36` for any other agent's in-flight work that rode along.

My remaining eight edits are still uncommitted and are listed below.

**Files changed by me (9, all prose/derivation/counts — no production behaviour changed):**

| file | change |
|---|---|
| `loremaster/tests/_surreal_harness.py` | importer count 36 → 37 (§1 — turns a RED test green) |
| `CLAUDE.md` | registration sites: count-free, cites `./scripts/registration_sites.py` (§2.2) |
| `docs/plans/v2/DESIGN-LAW.md` | same (§2.2) — **already committed by the lead in `5261933`, see §6.2** |
| `scripts/registration_sites.py` | `_MIN_MEMBERS_FOR_A_SITE` comment vs value (§2.3) |
| `skills/lore-deploy/scripts/test_conformance_provenance.py` | module docstring member list (§2.4) |
| `skills/lore-deploy/references/lifecycle.md` | deploy doc member list (§2.5) |
| `loremaster/loremaster/logging_setup.py` | `LORE_NAMESPACES` subset rationale + re-open trigger (§2.6) |
| `loresigil/tests/test_factory_voyage_context.py` | false "all three backends" coverage claim (§2.7) |
| `loremaster/loremaster/config.py` | `resolve_secret` byte-exactness scoped to its two sources (§2.8) |

Nothing staged, nothing committed by me — the lead commits.
