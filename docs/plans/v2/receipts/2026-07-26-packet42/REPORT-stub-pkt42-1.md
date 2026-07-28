# REPORT-stub-pkt42-1 — STUB phase, packet 42

brief-base v7 read

- **state:** done-with-deviations
- **deviation 1:** `ruff` goes from clean → 2 × `F401` (the two `resolve_secret` imports are
  unused *because the brief forbade migrating the call sites*). Self-clearing at GREEN. I did
  **not** add `# noqa` — that would be a lie the implementer must remember to delete.
- **deviation 2:** I fixed one `I001` (import-sort) that my own edit introduced in
  `counting.py`, using `ruff check --select I001 --fix` so `--fix` could not delete the
  F401 imports I had deliberately added.
- **Packages considered:** pydantic (already this repo's validated-boundary library, CLAUDE.md
  "Quality gates") — **replace**: used `Field(min_length=1)` rather than hand-rolling a length
  check. Read: `pydantic.Field` constraint support on `SecretStr`, verified by live probe (§4),
  not assumed. ⚠ That read is also what produced decision-needed #1: the constraint provably
  **cannot** express the contract's actual requirement.
- **decisions-needed #1 (BLOCKING for GREEN):** the annotation the brief cites as the binding
  ruling — `Annotated[SecretStr, Field(min_length=1)]` — **satisfies only 1 of the 3 legs** of
  the frozen contract's blank-credential pin. Measured, §4.
- **decisions-needed #2:** `scripts/search_score_survey.py` constructs the loresigil
  `EmbeddingConfig` directly, bypassing `to_loresigil_config`. It is 1 of only 2 production
  construction sites and it is **not** in the scoped contract run. §6.
- **receipts:** §1 gate histogram · §2 before/after counts · §3 the three targets, now
  behavioural · §4 the `min_length` escalation · §5 ruff/mypy deltas · §6 blast radius.

All measurements in this report were taken **2026-07-27** in the worktree
`/home/ejprice/PycharmProjects/lore-pkt42`, branch `pkt42-prevent-the-leak`, against contract
commit `9ab5888` with only the three-file diff in §7 applied. They are **not** current claims
about any later tree.

**Tree-provenance receipt** (CLAUDE.md: "prove which tree you are testing"):

```
loremaster: /home/ejprice/PycharmProjects/lore-pkt42/loremaster/loremaster/__init__.py
loresigil:  /home/ejprice/PycharmProjects/lore-pkt42/loresigil/loresigil/__init__.py
```

Both resolve inside the packet-42 worktree. `/home/ejprice/PycharmProjects/lore` was never
touched. No test file was edited; no git state was mutated (the two `git stash`/`stash pop`
pairs in §5–§6 were for baseline measurement and are restored — `git diff --stat` after each
is in the transcript and matches §7).

---

## 1. THE GATE — failure-type histogram

The brief's exact command, `grep -oE "^E +[A-Za-z]*(Error|Exception)"`, sorted and counted:

| type | before | after |
|---|---|---|
| AssertionError | 66 | 66 |
| TypeError | 21 | 21 |
| **AttributeError** | **3** | **0** ✅ |
| RuntimeError | 2 | 2 |

**Structural sentinels — all zero after.** I did not rely on the brief's grep alone, because it
is anchored to a *bare* identifier and would miss a dotted/qualified name (CLAUDE.md: "sweep
greps use BARE, anchor-free patterns"; the instrument-lesson table: a gate keyed on a name is
defeated by a spelling of it). Second, word-boundary scan over the whole output:

```
AttributeError         0
ImportError            0
ModuleNotFoundError    0
NameError              0
SyntaxError            0
IndentationError       0
```

**That anchoring caution was justified.** The brief's grep classifies only 89 of the 118
failures — it silently drops every `pydantic_core._pydantic_core.ValidationError` (the `[A-Za-z]*`
cannot cross `_` or `.`). A full per-failure classification via `--tb=line`, which emits exactly
one line per failure, reconciles to 118/118:

| type | count | verdict |
|---|---|---|
| `AssertionError` | 66 + 5 bare-`assert` renderings = 71 | BEHAVIORAL |
| `pydantic_core...ValidationError` | 25 | BEHAVIORAL |
| `TypeError` | 21 | BEHAVIORAL — see below |
| `Failed: DID NOT RAISE` | 1 | BEHAVIORAL |
| **total** | **118** | |

**On the 21 `TypeError`s.** My standing instructions class "TypeError from wrong argument count"
as STRUCTURAL; the brief explicitly overrides ("`TypeError` … correct and expected"), and
brief-base v7 §precedence puts the spawn brief first. I am flagging it rather than silently
accepting it, because it *is* an arity mismatch. All 21 are one cause:

```
resolve_secret() takes 1 positional argument but 2 were given
```

The brief's override is right here: the contract (`test_secret_resolution_seam.py`, class
`TestResolveSecretIsTheUnifiedLookup`) requires `resolve_secret` to **grow** the ruled
`env_file: Path | None = None` parameter. The symbol exists, is importable and is callable — the
tests are red because the production signature has not yet changed, which is the GREEN phase's
work order, not an absent stub. That is a genuine behavioural red, not a broken test.

## 2. Counts — before and after

Quoted tails (real, with passed-counts — CLAUDE.md: a piped pytest with a bad path exits "no
tests ran" silently):

```
BEFORE:  113 failed, 261 passed in 5.87s
AFTER:   118 failed, 256 passed in 7.55s
```

I hit the "no tests ran" trap once during §3 (a guessed class name) and caught it on the
`no tests ran in 0.05s` line before reporting anything — noted because it is exactly the mode
the law warns about.

Node-id delta: **0 tests fixed, 5 newly failing.** All five were predicted by the brief
("if adding `api_key` while `api_key_env` still exists breaks other suites, that is EXPECTED"):

| newly failing | cause |
|---|---|
| `TestEveryOtherFieldStillCopiesThrough::test_every_shared_field_is_copied_through_byte_exact` | `to_loresigil_config` does not pass the now-required `api_key` |
| `TestEveryOtherFieldStillCopiesThrough::test_output_dimension_follows_dim_and_not_the_factory_default` | same |
| `TestEveryOtherFieldStillCopiesThrough::test_the_fixture_uses_no_default_values` | same |
| `test_a_blank_credential_is_rejected_AT_THE_API_KEY_FIELD[single-space]` | **§4 — was a FALSE PASS** |
| `test_a_blank_credential_is_rejected_AT_THE_API_KEY_FIELD[whitespace-only]` | **§4 — was a FALSE PASS** |

## 3. The three targets are now BEHAVIORAL

Run in isolation, `--tb=line`:

| test | before | after |
|---|---|---|
| `TestTheCompositionRootIsWhereTheEmbeddingSecretIsResolved::test_it_routes_through_the_shared_resolver` | `AttributeError: module 'loremaster.embedding' has no attribute 'resolve_secret'` | `ValidationError: … missing api_key` at `embedding.py::to_loresigil_config` |
| `TestTheCompositionRootIsWhereTheEmbeddingSecretIsResolved::test_the_resolved_key_is_the_environments_real_value` | `AttributeError: 'EmbeddingConfig' object has no attribute 'api_key'` | `ValidationError: … missing api_key` |
| `TestLoadApiKeyRoutesThroughTheSharedResolver::test_it_routes_through_the_shared_resolver` | `AttributeError: module 'loremaster.calibration.counting' has no attribute 'resolve_secret'` | `AssertionError: assert 'test-dummy-anthropic-key' == 'pa-RESOLVED-BY-THE-SHARED-SEAM'` |

The third is the clearest evidence the stub did its job: the `monkeypatch.setattr` now **lands**,
and the test reports that `load_api_key` returned the real environment value instead of the
sentinel — i.e. the mutation pin can now *discriminate* a routing build from a hand-rolled one,
which is precisely what it could not do while it died on attribute lookup.

⚠ Correction to the brief's framing: the third `AttributeError`
(`'EmbeddingConfig' object has no attribute 'api_key'`) was attributed to `loresigil.factory`.
It is raised from `loremaster/tests/test_secret_resolution_seam.py`, on the **loresigil**
`EmbeddingConfig` returned by `to_loresigil_config`. Same root cause, same fix — flagged only so
the address is accurate. `loresigil/tests/test_factory_secret_resolution.py` contributed no
`AttributeError` in the baseline.

## 4. ⚠ ESCALATION — the cited annotation does not satisfy the frozen contract

The brief states the binding ruling is `Annotated[SecretStr, Field(min_length=1)]`. I implemented
exactly that. **It cannot satisfy the contract as frozen.** Live probe against this tree's
pydantic 2.13 (a read, not an expectation — CLAUDE.md: read the docs, then verify them):

| `api_key` value | result under `Field(min_length=1)` |
|---|---|
| `''` | REJECTED — `too_short` at `('api_key',)` ✅ |
| `' '` | **ACCEPTED** ❌ |
| `' \t '` | **ACCEPTED** ❌ |
| missing | REJECTED — `missing` at `('api_key',)` |

The contract's `TestAnAbsentCredentialFailsLoudAndNeverBuildsAKeylessEmbedder::test_a_blank_credential_is_rejected_AT_THE_API_KEY_FIELD`
is parametrised over exactly `["empty", "single space", "whitespace-only"]` and requires an error
at `('api_key',)` for all three. `min_length` measures **length**, and `' '` has length 1. Two
legs cannot pass. The GREEN implementer needs a "blank all through" check (the semantics
`config.resolve_secret` already implements as `not value or not value.strip()`) — and per
CLAUDE.md ONE IMPLEMENTATION, that policy should be the *same function*, not a second copy;
but `loresigil` cannot import `loremaster`, so this is a design fork for the lead/operator, not
something I should settle. I did not implement it: the brief scoped me to the field only.

**The sharper half — this was a FALSE PASS, and my change unmasked it.** Those two legs were
**green before my edit**, for the wrong reason: `api_key` was an unknown field, so
`extra="forbid"` produced an `extra_forbidden` error whose `loc` is also `('api_key',)`, and the
assertion `any(error["loc"] == ("api_key",) …)` was satisfied by a rejection that had nothing to
do with blankness. The contract author warned about this exact class in the neighbouring test's
own comment ("*the lead measured exactly this class of false pass on this packet*"), and guarded
the *neighbouring* pin by inspecting `error["type"]` — but this pin checks only `loc`. So the
red is now **honest**, and the pin as written still cannot distinguish "rejected for blankness"
from "rejected for some other reason at `api_key`". Recommend the lead consider whether that pin
needs the `error["type"]` leg its sibling has. **I did not touch it** — the contract is frozen.

## 5. Other gates — deltas, not absolutes

**ruff:** baseline `All checks passed!` → **2 errors**, both `F401`:

```
loremaster/loremaster/calibration/counting.py:32:31: F401 `loremaster.config.resolve_secret` imported but unused
loremaster/loremaster/embedding.py:31:48:            F401 `loremaster.config.resolve_secret` imported but unused
```

Unavoidable given the brief's boundary: the tests require the name to be *bound in the module
namespace*, and the brief forbade the call-site migration that would consume it. Both clear the
moment GREEN calls `resolve_secret(...)` in `to_loresigil_config` and `load_api_key`. This is the
one place my diff makes a repo gate red that was green, so it is stated plainly rather than
suppressed.

**mypy (`scripts/typecheck.sh`):** baseline was **already RED at 24 errors** — the contract is
committed red, so this is not a regression I introduced. After: **30**.

⚠ **The +6 is a NET figure and I nearly shipped it as if it were the new-error count.** Derived
as a multiset diff over `(file, message)` pairs with line numbers normalised away (a `comm` over
sorted lines silently mis-handles duplicates, which is how the wrong number arose):

**17 new instances - 11 disappeared instances = +6 net.**

New (all one class — "required field, un-migrated call sites"):

| new error | count |
|---|---|
| `loremaster/loremaster/embedding.py: Missing named argument "api_key"` | 1 |
| `loresigil/tests/test_factory.py: Missing named argument "api_key"` | 2 |
| `loresigil/tests/test_factory_voyage_context.py: Missing named argument "api_key"` | 2 |
| `loresigil/tests/test_tei_prompt_name.py: Missing named argument "api_key"` | 4 |
| `loresigil/tests/test_voyage_batch.py: Missing named argument "api_key"` | 2 |
| `loresigil/tests/test_factory_secret_resolution.py: Missing named argument "api_key_env"` | 5 |
| `loresigil/tests/test_factory_secret_resolution.py: Unused "type: ignore"` | 1 |

The last two rows are the mirror image: the contract constructs *without* `api_key_env` because
it expects it deleted, and I was told not to delete it. They clear when GREEN retires the field.

**Disappeared — and this is an independent confirmation of the gate in §1:**

| disappeared error | count |
|---|---|
| `loremaster/tests/test_secret_resolution_seam.py: "EmbeddingConfig" has no attribute "api_key"` `[attr-defined]` | 3 |
| `loresigil/tests/test_factory_secret_resolution.py: "EmbeddingConfig" has no attribute "api_key"` `[attr-defined]` | 3 |
| `loresigil/tests/test_factory_secret_resolution.py: Unexpected keyword argument "api_key"` | 5 |

All eleven are mypy's *own* structural complaints about the missing attribute — the same defect
class the runtime `AttributeError`s were. A second, independent instrument therefore agrees the
structural hole is closed, which is worth more than the pytest histogram alone (CLAUDE.md: a
probe needs a control; the `[attr-defined]` disappearances are the positive control showing the
instrument could see the defect before the fix).

## 6. Blast radius outside the scoped run (reported, not chased)

**`loresigil/tests` (full tree):** baseline `20 failed, 361 passed, 1 skipped` → after
`46 failed, 335 passed, 1 skipped`. **+26 failures.** Full per-failure classification:

```
38 pydantic_core._pydantic_core.ValidationError
 7 AssertionError
 1 Failed
--
46  (reconciles exactly)

structural sentinels: AttributeError 0 · ImportError 0 · ModuleNotFoundError 0 · NameError 0 · SyntaxError 0
```

**Zero structural failures introduced anywhere I measured.** Every new red is a pre-existing
loresigil suite constructing `EmbeddingConfig` without the now-required `api_key`.

**Production construction sites of the loresigil `EmbeddingConfig` — there are exactly two**
(derived by grep over `loresigil/loresigil`, `loremaster/loremaster`, `scripts`; this is a
cross-cutting textual sweep, so grep is the honest instrument per CLAUDE.md's dogfood protocol
case (c) — I did not use the lore index here and am saying so):

1. `loremaster/loremaster/embedding.py::to_loresigil_config` — the composition root. In scope.
2. `scripts/search_score_survey.py` (`config = EmbeddingConfig(`) — **direct construction that
   bypasses `to_loresigil_config` entirely.** This is the same bypass the contract's own
   `TestAnAbsentCredentialFailsLoudAndNeverBuildsAKeylessEmbedder` docstring cites as its reason
   for validating at the config boundary, and which
   `docs/plans/v2/receipts/2026-07-26-packet42/REMOVED-BEHAVIOR-INVENTORY.md` flags at R28/#233.
   It is **not** covered by the scoped contract run, so GREEN can land all-green there and still
   leave this file broken. Recommend the lead put it explicitly in the implementer's writable
   set with a "must construct successfully" receipt.

## 7. What changed

`git diff --stat`:

```
 loremaster/loremaster/calibration/counting.py |  5 +++++
 loremaster/loremaster/embedding.py            |  6 +++++-
 loresigil/loresigil/factory.py                | 13 +++++++++++--
 3 files changed, 21 insertions(+), 3 deletions(-)
```

Three concerns, three files, no logic:

1. **`loremaster/loremaster/embedding.py`** — `from loremaster.config import EmbeddingConfig`
   → `… import EmbeddingConfig, resolve_secret`, plus a comment saying *why* the name is bound
   here rather than reached through `config.` (the tests substitute this attribute).
2. **`loremaster/loremaster/calibration/counting.py`** — added
   `from loremaster.config import resolve_secret`, same rationale comment. No import cycle:
   `config.py` imports only stdlib, `yaml`, `pydantic` and `loresigil.voyage_batch`.
3. **`loresigil/loresigil/factory.py`** — added `api_key: Annotated[SecretStr, Field(min_length=1)]`
   beside the (deliberately retained) `api_key_env`, plus `Annotated` / `Field` / `SecretStr`
   imports and a docstring-style comment on the field.

**Not done, per the brief:** `api_key_env` not deleted · `_resolve_api_key` and
`MissingApiKeyError` not deleted · `logging_setup.py` untouched · no `build_auth_headers`, no
mint gate, no seam · no call site migrated · `resolve_secret` signature unchanged · no behaviour
changed · no test file edited · nothing committed or staged.
