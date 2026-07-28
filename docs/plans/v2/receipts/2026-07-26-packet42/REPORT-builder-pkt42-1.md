# REPORT-builder-pkt42-1 — GREEN phase, packet 42

> ⚠ **SUPERSEDED SYMBOLS (dated record):** mentions `_BRIEF_PUBLISH_`, a retired prefix (the
> private mint-retry constants deleted by finding #108 — `_txn.retry_on_conflict` owns that
> policy now). It appears here only inside REPRODUCED TEST OUTPUT: this record quotes the
> packet-11i/03b doc-banner failure that packet 42 inherited and verified as unrelated to its
> own work. Preserved as-written per the archive law; read it as history, not instruction.

brief-base v7 read

> **REVISION 2 — the six contract defects are FIXED at `7889bcf` and the wave is GREEN.**
> The seventh defect the author's sweep found needed a PRODUCTION change and is now done:
> `lorerunes` is named in the in-image conformance guard, so the #139 instrument can see the
> member R29 minted. **Scoped gate 0 failed / 383 passed. Full suite 2 failed / 7368 passed**,
> and those two are the pre-existing failures — now with the receipt the lead asked for: both
> **reproduced at `76f1d9f`** in a provenance-verified pristine archive (§5.8, §7.8).
> Revision 1's §5 is kept verbatim below as the record of what was reported and why; every entry
> now reads as CLOSED.

- **state:** done — all gates green; two pre-existing failures outside this work, receipted
- **gate (revision 2, measured 2026-07-27):** scoped run **0 failed / 383 passed** ·
  `./scripts/typecheck.sh` **0 errors across five iterations**, exit 0 · `uv run ruff check .`
  **All checks passed!** · deploy-skill suite **117 passed** · R25 co-run **16 passed** ·
  **full suite 2 failed / 7368 passed / 17 skipped / 3 xfailed in 194s**.
  Inherited at the start of GREEN: **121 failed / 259 passed**.
- **deviations:**
  1. **I edited FIVE loresigil test files beyond §9's list** (`test_tei.py`, `test_tei_prompt_reserve.py`,
     `test_voyage_cloud.py`, `test_voyage_context.py`, `test_embed_usage.py`) — 8 sites, each
     `api_key=API_KEY` → `api_key=SecretStr(API_KEY)`. They construct the EMBEDDERS directly, which §9's
     `EmbeddingConfig(api_key_env=…)` sweep could not see. §4.9.
  2. **I edited FOUR `skills/` test files** to discharge R9's "fix 11 test-file errors" half. §4.10.
  3. Every §9 row that says *"whole class → the property now lives at the config boundary"* was
     executed as a DELETION with an in-file note naming where the property went. §4.9.
  4. **I edited `scripts/test_snapshot_gc.py` (2 lines) — a regression my own change caused.**
     `_wire_fakes` stubbed `gc.resolve_secret`; R17 made the username read go through the new
     `resolve_config_value`, which the fakes did not cover, so 4 `TestMainWiring` tests hit the real
     environment and exited 1. One `monkeypatch.setattr` mirroring the existing stub. §5.8.1.
  5. **(revision 2) I edited `skills/lore-deploy/scripts/test_conformance_provenance.py` beyond the
     literal grant.** The lead authorised the frozen tuple; I also (a) added the fourth member to the
     one test that hand-builds a per-member map, because `audit` now asks for a name that map lacked,
     and (b) **renamed two tests whose NAMES carried the member count** (`..._are_the_three_uv_workspace_members`)
     — they passed while their names had silently become false, which is the stale-natural-language
     class one layer harder to see than prose. Written count-free, so member five does not re-stale
     them. §4.11.
- **Packages considered:** `python-dotenv` **1.2.2** → **replace** (read the installed
  `dotenv/main.py` signature of `dotenv_values`, specifically `interpolate: bool = True`, before
  passing `interpolate=False`; ruling R12 names the argument and §4.2 carries the measured receipt.
  Also read `DotEnv._get_stream`: with `verbose=False` a MISSING file yields an empty stream
  silently, so replacing the old `if env_file.is_file()` guard adds no new output);
  `pydantic.SecretStr` **2.13.4** → **replace** (already adopted; read `SecretStr.__len__` and
  `get_secret_value` to confirm there is NO public accessor that yields the raw bytes without the
  method the unwrap gate is keyed on — that read is what proved C-DEF 2 was unsatisfiable rather than
  merely awkward, §5.2); `pydantic.Field(min_length=1)` → **rejected by measurement, already ruled**
  (R29); `httpx` **0.28.1** → **keep** (no change needed; shape B builds headers per request through
  the existing `headers=` kwarg). No mechanism here was hand-rolled where a package covers it.
- **decisions-needed: NONE.** Revision 1 reported six contract defects (8 failing tests); all six were
  adjudicated REAL and fixed by the contract author at `7889bcf` (inventory "Ninth ruling wave", R32).
  The seventh — the in-image guard's blindness to `lorerunes` — was a PRODUCTION gap and is fixed
  here (§4.11).
- **receipt pointers:** §1 tree provenance · §2 the gate, both revisions · §3 what each ruling became
  · §4 file-by-file (§4.11 = the revision-2 fix) · §5 the six defects as reported (now CLOSED) ·
  §5.7 the R29 riders, one now closed · §5.8 the two pre-existing failures · §6 judgement calls ·
  §7 gates · **§7.6 the shared-predicate mutation proof** · **§7.7 the R16 one-commit receipt** ·
  **§7.8 the pre-existing-at-`76f1d9f` receipt the lead asked for**.

---

## 1. Tree provenance (#140)

```
worktree : /home/ejprice/PycharmProjects/lore-pkt42   branch pkt42-prevent-the-leak
HEAD     : 76f1d9f  stub(pkt42): mint the `lorerunes` workspace member as a skeleton
loremaster.__file__ = /home/ejprice/PycharmProjects/lore-pkt42/loremaster/loremaster/__init__.py
lorerunes.__file__  = /home/ejprice/PycharmProjects/lore-pkt42/lorerunes/lorerunes/__init__.py
```

No scratch copy was made: every change is in this worktree and every measurement was taken here, on
**2026-07-27**. `/home/ejprice/PycharmProjects/lore` was never touched. Nothing staged, nothing
committed (`git diff --cached --stat` empty) — R16's one-commit rule means the lead owns the boundary.

**Tool honesty (repo law §4):** I used **direct Read/grep/AST, not lore**, throughout. Reason stated
rather than hidden: lore's index points at the PRIMARY checkout (#134/#125) and every file this packet
touches is edited here, so a graph answer would describe a different tree. Two of the three
grep-sanctioned cases applied continuously — rename exhaustiveness where one missed site
compiles-but-breaks (`api_key_env`, `MissingApiKeyError`, `self._headers`), and non-symbol textual
seams (the forbidden-prose scan, the ENV/UNWRAP allowlist keys). No friction row filed: this is the
documented worktree limitation, not a new gap.

---

## 2. THE GATE

**Scoped run, the brief's exact command, at revision 2:**

```
$ uv run pytest loremaster/tests/test_secret_typing.py loremaster/tests/test_secret_leak_vectors.py \
    loremaster/tests/test_secret_resolution_seam.py loremaster/tests/test_logging_setup.py \
    loresigil/tests/test_factory_secret_resolution.py lorerunes/tests -q -n auto
...
383 passed in 6.16s
```

**0 failed.** Inherited at the start of GREEN: `121 failed, 259 passed`. The path was
**121 → 8 → 0**: 113 pins turned green on production work, the 8 survivors were contract defects the
lead adjudicated and the author fixed at `7889bcf`, and the last one (`lorerunes` invisible to the
in-image guard) was the production fix in §4.11. **I did not bend the design to make a pin pass at
any point.**

Per-file, at revision 2 (each run individually, so no count is inferred from the aggregate):

| file | failed | passed |
|---|---|---|
| `test_secret_leak_vectors.py` | 0 | 181 |
| `test_secret_resolution_seam.py` | 0 | 64 |
| `test_secret_typing.py` | 0 | 66 |
| `test_logging_setup.py` | 0 | 44 |
| `test_factory_secret_resolution.py` | 0 | 27 |
| `lorerunes/tests` | 0 | 1 |

(The per-file sum is 383 and the parallel aggregate is 383 — they agree, which is the check that
neither number came from the other.)

⚠ **#221 compliance, stated rather than inferred:** every green above is a RUNTIME green from a live
`pytest` run. No pin in this work is demonstrated by a mypy result, and the mypy gate went from 3
errors to 0 only as a side effect. The two places mypy could have lied through `dict[str, Any]` —
`to_loresigil_config`'s field map and the counters' `headers=` mapping — are both pinned behaviourally
(`test_every_shared_field_is_copied_through_byte_exact`, the four wire pins), and both were RED before
this change for runtime reasons.

---

## 3. What each ruling became

| ruling | what I built |
|---|---|
| **R29** | `lorerunes.is_blank` = `not value or not value.strip()`. **Both** callers call it: `loremaster.config.resolve_secret` and `loresigil.factory.EmbeddingConfig._reject_a_blank_credential`. Proven shared by the contract's own mutation pin — inverting the predicate makes BOTH accept a blank, and the baseline leg proves both rejected first. |
| **R2 / R5 / R12** | `resolve_secret(env_var_name, env_file=None)`. Environment first; a blank exported value falls THROUGH to the file when one was supplied; `dotenv_values(env_file, interpolate=False)`; never `load_dotenv`; fatal at the END of resolution, naming the variable. |
| **R3** | Server-path call sites pass no `env_file`. The only site that does is `counting.py::load_api_key` — the allowlist's single entry, verified in both directions by the contract's pin. |
| **R1** | Never stripped. The value is classified by `is_blank`, never mutated; a padded credential survives byte-exact from both sources. |
| **#222 / B1–B10** | `loresigil` resolves nothing: `_resolve_api_key` and `MissingApiKeyError` deleted, `api_key_env` replaced by `api_key: SecretStr`, `to_loresigil_config` resolves. `loremaster.config.EmbeddingConfig.api_key_env` untouched. |
| **R26** | Two typed seams, one per package: `loremaster.calibration.counting.build_auth_headers` and `loresigil.voyage_http.build_auth_headers`, both `(credential: SecretStr) -> dict[str, str]`. Not one shared implementation — `loresigil` cannot import `loremaster`, and the enforcement is the SIGNATURE. |
| **R19 / R22** | **Shape B on all three classes**: `AsyncClaudeTokenCounter`, the sync `ClaudeTokenCounter`, and (inertly, by construction) `MultiModelClaudeCounter`. No auth headers at construction on either arm; the credential stays wrapped on the instance; headers are built per request. |
| **R10** | Falls out of shape B: no `self._headers`, so no bare-`str` credential object exists to render. |
| **R8 / R16** | The labelled `Authorization` pattern is FIXED **in the same change** as the catch-all deletion. `_ASSIGNMENT_RE` no longer carries `authorization`; a new `_AUTH_HEADER_RE` owns the header. §4.1 carries the measured output table. |
| **steps 5+6** | All eight symbols deleted, plus `math`/`Counter`. `_scrub_text` is three label-driven passes. |
| **R17 / R21 / R24** | The five username round-trips call a new non-secret sibling `resolve_config_value(env_var_name) -> str` in `loremaster/config.py` — which keeps the read inside the one module the gate permits AND keeps the NAMING `KeyError` that `snapshot_gc.py::main` renders. |
| **R7** | `comms_consumer_eval.py::_amain` routes through `resolve_secret`; exit code and operator message unchanged. |
| **R14** | `probe_embed.py` fixed IN PLACE, stdlib-only: `if not key` → `if not key or not key.strip()`. Exit contract untouched; the ledgered-duplicate rationale written into its docstring with the re-open trigger. |
| **R31 / #233** | `scripts/search_score_survey.py::_make_embedder` migrated to `api_key=resolve_secret(...)`. It is a composition root and says so. |
| **R9** | `scripts/typecheck.sh` `MEMBERS` gains `skills` as its own iteration; the 11 pre-existing errors are fixed. §4.10. |

---

## 4. File by file

### 4.1 `loremaster/loremaster/logging_setup.py` — the deletion + the R8 fix, ONE change (R16)

Deleted: `_TOKEN_RE`, `_ENTROPY_BITS_THRESHOLD`, `_shannon_entropy_bits`, `_is_safe_high_entropy_run`,
`_is_absolute_path_component`, `_UUID_RE`, `_PATH_BLOB_CHARS`, `_PATH_SEPARATOR`, and the now-unused
`math` / `collections.Counter` imports. Net −277/+~120 lines.

Added `_KNOWN_AUTH_SCHEMES` + `_AUTH_HEADER_RE` + `_redact_auth_header`, and removed `authorization`
from `_ASSIGNMENT_RE`'s alternation. **Why a separate pattern rather than a tweak:** while
`authorization` was an assignment label, that pattern's `(\S+)` consumed the SCHEME word as the value —
which is R8's defect and, for `Token`/`Mutual`, a live leak. The two cannot coexist in one pattern
because one of them has to know what a scheme is.

**The design decision inside the fix, stated because it is the load-bearing half.** A known scheme is
PRESERVED and only the credential token is redacted; an UNRECOGNISED leading word is redacted **along
with the rest of the line**. That asymmetry is forced, not chosen: `test_an_UNKNOWN_auth_scheme_does_not_leak_its_credential_either`
requires the credential to vanish for `Negotiate`/`HOBA`/`Mutual`/`X-Vendor-Scheme`, and when we cannot
tell whether the first token is a scheme or the credential, redacting only one token leaks whenever it
was a scheme. So: **failing to recognise a scheme costs a diagnostic word; failing to recognise a
credential costs a credential.** The redaction is bounded to the LINE (`[^\n]*`), never across a
newline, because `_scrub_text` is handed whole tracebacks.

Measured output, run against the built tree (regenerate with the snippet in §7.3):

```
'Authorization: Bearer <k>'                    -> 'Authorization: Bearer ***REDACTED***'
'Authorization: Basic dXNlcjpzdXBlcnNlY3JldHBhc3N3b3Jk'  -> 'Authorization: Basic ***REDACTED***'
'Authorization: Token 8f3ka92mfLQ0zXvbNqRt'    -> 'Authorization: Token ***REDACTED***'      # LEAKED at base
'Authorization: Mutual short123'               -> 'Authorization: ***REDACTED***'            # LEAKED at base
'Authorization: Negotiate YIIZ...'             -> 'Authorization: ***REDACTED***'
'Authorization: <k>'                           -> 'Authorization: ***REDACTED***'
'authorization=<pw> endpoint=ws://x/rpc'       -> 'authorization=***REDACTED***'
'x-api-key: <k>'                               -> 'x-api-key: ***REDACTED***'
'sent Bearer <k> up'                           -> 'sent Bearer ***REDACTED*** up'
"curl -H 'Authorization: Bearer <k>' https://api/x" -> "curl -H 'Authorization: Bearer ***REDACTED*** https://api/x"
'password=<pw> endpoint=ws://x/rpc'            -> 'password=***REDACTED*** endpoint=ws://x/rpc'
'/tmp/ci/090685cb-.../store/surreal.py'        -> unchanged   # recovered (#227)
'commit 8538303a1b2c... landed'                -> unchanged   # recovered (A16 inverted)
'_build_the_contextualized_request_body'       -> unchanged   # recovered (audit R2)
```

⚠ The `curl` line eats the closing quote. That is the pre-existing residual R12 the eighth ruling wave
recorded as **raised and NOT actioned** (`(\S+)` swallows adjacent punctuation) — unchanged by this
work, in both the Bearer and the assignment patterns.

The module docstring was rewritten: it no longer teaches a mechanism the code does not run, and it now
states the A18 trade once, in the module that made it.

### 4.2 `loremaster/loremaster/config.py` — the unified lookup + the non-secret sibling

`resolve_secret(env_var_name, env_file=None)` per R2/R5/R12. Two things worth naming:

* **`interpolate=False` is load-bearing and I read the signature before relying on it.** With the
  default, `dotenv_values` rewrites `${…}` inside a secret and an unset `${VAR}` SHORTENS it. The
  contract pins four `$` shapes; all four pass.
* **The blank test is `is_blank(value)` at BOTH decision points** — the fall-through condition and the
  final fatal check — so `" "` behaves exactly like `""` on the file-enabled path (the lead ruling the
  contract flagged as absent from the authority file, §0.2b).

`resolve_config_value(env_var_name) -> str` is new: the non-secret sibling R24 names. It raises a
NAMING `KeyError` rather than returning `None` — required by `snapshot_gc.py::main`, which is the only
one of the five sites that CATCHES it and renders it as a clean `_EXIT_ERROR`.

### 4.3 `lorerunes` — the predicate, and only the predicate

`is_blank` implemented; nothing else added. The package still imports nothing but its own submodule,
reads no environment, and both consumers' `pyproject.toml` now declare it
(`lorerunes = { workspace = true }`) rather than relying on `uv sync --all-packages` installing it
incidentally — the stub's §5d flagged exactly this and it is now closed.

### 4.4 `loresigil` — the reshape

`factory.py`: `MissingApiKeyError` and `_resolve_api_key` deleted; `api_key_env` gone;
`api_key: SecretStr` with a `field_validator` that calls the SHARED `is_blank`; `os` import gone.
`voyage_http.py`: `build_auth_headers(credential: SecretStr)` added, `build_bearer_client` retyped and
routed through it. `tei.py` keeps its own client (it needs `base_url` and a different timeout) but takes
its HEADERS from the seam, so there is exactly one `Bearer` f-string and one unwrap-for-the-wire in the
package. All three embedder constructors take `api_key: SecretStr`.

### 4.5 `loremaster/loremaster/embedding.py` — the composition root

`to_loresigil_config` calls `resolve_secret(config.api_key_env)` and passes `api_key=`. Failure moves
earlier (translation, not `make_embedder`) and changes type (`KeyError` naming the variable, not
`MissingApiKeyError`). Its docstring says it is the composition root.

### 4.6 The counters — SHAPE B, both twins

`counting.py` and `token_survey.py`: `self._headers` deleted, `self._api_key: SecretStr` retained,
`headers=build_auth_headers(self._api_key)` per request. `token_survey.py` now IMPORTS
`build_auth_headers` **and** `load_api_key` from `loremaster.calibration.counting` — so the twins are
literally one function, and the wire-shape parity `TestRequestShapeParity` guards is true by
construction rather than by two copies agreeing.

`MultiModelClaudeCounter` needed no change and that is the point: under shape B, N counters over one
shared client is inert, where under shape A it is N writers to one header map.

### 4.7 The five username round-trips (R17)

`index/cli.py::_run`, `server.py::build_app_context`, `scout.py::from_config`,
`search_score_survey.py::_make_store`, `snapshot_gc.py::run_gc` — all five now call
`resolve_config_value`. **Every one of the five password siblings verifiably still calls
`resolve_secret` and stays wrapped**; I re-derived that rather than inheriting it (`grep -n
resolve_secret` on all five files, §7.4). The stale comment in `search_score_survey.py` that said
*"exactly as at the other four `resolve_secret` user sites"* went with the change.

### 4.8 `comms_consumer_eval.py`, `probe_embed.py`, `search_score_survey.py`

As ruled (R7 / R14 / R31). `comms_consumer_eval` imports the resolver LOCALLY, matching that script's
standing idiom for every loremaster import; `probe_embed` imports nothing new at all.

### 4.9 Test-file migrations — §9's rows, plus five files §9 could not see

§9's eight rows executed. Two `KeyResolution` classes DELETED (not weakened) with in-file notes naming
where the property went; `test_embedding_prompt_name.py` got the env fixture R13 authorised.

⚠ **DEVIATION — five files beyond §9.** §9's list was derived from `EmbeddingConfig(api_key_env=…)`
call sites. It is complete for that population. But `api_key: str` → `SecretStr` on the three EMBEDDER
constructors breaks a SECOND population — files that construct an embedder directly — and those are not
in §9:

```
loresigil/tests/test_tei.py                 1 site
loresigil/tests/test_tei_prompt_reserve.py  1 site
loresigil/tests/test_voyage_cloud.py        1 site
loresigil/tests/test_voyage_context.py      2 sites
loresigil/tests/test_embed_usage.py         3 sites
```

Each edit is `api_key=API_KEY` → `api_key=SecretStr(API_KEY)`. **The raw `API_KEY` constant deliberately
stays a `str`**, because those same files assert `header == f"Bearer {API_KEY}"` — making the constant a
`SecretStr` would have asserted against the MASK, i.e. a pin that passes while proving nothing. This is
the two-populations shape this packet keeps finding, and it is why the count is 8 sites and not 0.

### 4.10 `skills/` under the typecheck (R9)

`MEMBERS=(lorerunes lorescribe loresigil loremaster skills)` — its own iteration, never merged. The 11
errors R9 measured are fixed, all in test files, all ordinary:

| file | fix |
|---|---|
| `test_conformance_provenance.py` | `_baked` and `_resolver` return `MemberProvenance` rather than `object` (which is what made the `dict[str, object]` mismatch); `_inject` takes a covariant `Mapping`; the now-unused `type: ignore[import-not-found]` removed |
| `test_lore_deploy.py` | patch `shutil.which` on the stdlib module rather than through `lore_deploy.shutil` (strict mypy forbids the implicit re-export; the patched object is the same one) |
| `test_port_probe.py` | narrow `getsockname()[1]` to `int` explicitly instead of returning `Any` |
| `test_workspace_probe.py` | replace two `(list.append(...), value)[1]` tuple tricks with a named closure — `append` returns `None`, so the tuple form only ever worked by index |

Receipt: `uv run mypy skills` → **11 errors → `Success: no issues found in 12 source files`**, and the
deploy-skill suite still **117 passed**.


### 4.11 (revision 2) The in-image guard now SEES `lorerunes` — the seventh defect

`skills/lore-deploy/scripts/conformance_provenance.py::WORKSPACE_MEMBERS` gains `"lorerunes"`, and
so does `EXPECTED_MEMBERS`, the frozen tuple its own test pins independently (the failure message
named both, and the pair is deliberate: the test constant is derived from the design doc, NOT read
back from the module, so a build that ships a shorter list is caught rather than mirrored).

**Why this was a real gap and not bookkeeping.** R29's consequence 5 says a workspace member missing
from the image is an `ImportError` at boot, **in production only, invisible to every test on this
host**, and names packet 01a's in-image conformance run as THE instrument that proves otherwise.
The Containerfile half was done (`COPY lorerunes/ /app/lorerunes/`). The PROVING half was not: the
guard enumerates the members it checks, and `lorerunes` was not among them — so a broken `COPY`, a
member that reached the image but would not import, or a member resolving to the `:ro` mount instead
of the baked artifact would all have passed the guard silently. **That is #131/#139's shape occurring
inside the instrument built to prevent #131/#139.**

Two knock-on edits, both disclosed as deviation 5:

* `TestAudit::test_audit_evaluates_every_member_and_accounts_for_each_one` hand-builds a
  `{member: provenance}` map and `audit` now asks for a name it did not contain (`KeyError`). The
  fourth member is added as a **second HONEST fate** — which strengthens the test rather than merely
  unbreaking it: with one honest member, `len(receipts)` and "the honest member" are
  indistinguishable, so a build returning only the FIRST receipt passed. It no longer does.
* **Two tests carried the member COUNT in their NAMES** —
  `test_workspace_members_are_the_three_uv_workspace_members` and
  `test_audit_default_members_cover_all_three_workspace_members`. Both **passed** with a four-member
  tuple while their names had become false. That is the stale-natural-language class this repo pays
  for most often, one layer harder to see than prose, and the STUB flagged it in its §5a. Renamed
  count-free (not to "four"), so member five does not re-stale them.

Receipts: deploy-skill suite **117 passed**; scoped gate **0 failed / 383 passed**; the pin that
found it (`TestTheInImageGuardCoversEveryWorkspaceMember`, ∀ derived from `pyproject.toml`, never a
hand-list) is green.

---

## 5. THE SIX CONTRACT DEFECTS (8 failing tests) — reported, not fixed

> **ALL SIX ARE CLOSED.** The lead adjudicated every one as real; the contract author fixed them at
> `7889bcf` (inventory "Ninth ruling wave" / R32, which records the shared root cause: each was a pin
> written against a design a LATER ruling changed, with a satisfiability receipt taken at revisions
> 3–4 and never re-run after 6 and 8 reshaped the design). **This section is preserved verbatim as
> the record of what was reported and on what evidence** — including §5.3, where the refusal is the
> point. Nothing below is a live instruction.

Each is a pin that contradicts a ruling the same contract implements. **None can be satisfied by any
production code I could write without violating a ruling.** I state for each what I tried, why it is
structural rather than awkward, and the exact patch I would apply if contract edits were mine.

### 5.1 🔴 `UNWRAP_ALLOWLIST` is at the PRE-R19/R26 addresses (3 tests)

**Failing:** `test_no_allowlist_entry_is_stale` · `test_every_unwrap_site_has_an_evidence_backed_entry`
· `test_the_scan_finds_the_population`

The allowlist was written in contract revision 3 (R17) and never re-derived after revision 4 (R19,
shape B) or revision 6 (R26, the typed seam) moved the unwraps. Measured now:

```
stale (named, no live site):   loremaster/calibration/counting.py::__init__
                               scripts/token_survey.py::__init__
                               loresigil/voyage_http.py::build_bearer_client
unlisted (live, no entry):     loremaster/calibration/counting.py::build_auth_headers
                               loresigil/voyage_http.py::build_auth_headers
                               loresigil/factory.py::_reject_a_blank_credential
```

* `counting.py::__init__` and `token_survey.py::__init__` cannot unwrap: **R19 forbids building auth
  headers at construction.** That is the whole mandate.
* `voyage_http.py::build_bearer_client` cannot unwrap either, because the header NAME literal must sit
  inside a function named `build_auth_headers` (the construction gate's only exemption), and the
  unwrap has to be where the header string is built.

**And the threshold in the same class contradicts the contract's own arithmetic:**
`test_the_scan_finds_the_population` asserts `len(sites) >= 8` while §0.9 states the post-R17 surface is
**6** ("5 pre-existing + 1 loresigil seam"). Measured: **6**. The sibling pin
`test_the_surviving_entries_are_all_real_credential_unwraps` asserts `4 <= len(UNWRAP_ALLOWLIST) <= 7`,
which agrees with 6 — so two pins in one class disagree about the same number.

**Proposed patch** (`loremaster/tests/test_secret_typing.py`):

```python
UNWRAP_ALLOWLIST: dict[str, str] = {
    "loremaster/auth.py::verify": CONSTANT_TIME_COMPARE,
    "loremaster/auth.py::add_key": EMPTINESS_GUARD,
    "loremaster/calibration/counting.py::build_auth_headers": AUTH_HEADER,   # was ::__init__
    "loremaster/store/_txn.py::signin_credentials": SDK_PAYLOAD,
    "loresigil/voyage_http.py::build_auth_headers": AUTH_HEADER,             # was ::build_bearer_client
    "loresigil/factory.py::_reject_a_blank_credential": EMPTINESS_GUARD,     # NEW — R29's validator
}
```
…and `assert len(sites) >= 6` in `test_the_scan_finds_the_population` (or `>= 5`, if the author wants
head-room; **not `>= 8`**, which no ruled design reaches). `scripts/token_survey.py::__init__` is simply
deleted — the sync counter now imports the seam instead of owning a copy, which is R22 working.

Note the resulting list is *better* than the one it replaces: six entries, four categories, every one a
leaf call site, and the two `AUTH_HEADER` entries are now the two typed seams rather than two instance
attributes.

### 5.2 🔴 `test_exactly_one_unwrap_site_exists_in_loresigil` — R26 and R29 each need one (1 test)

**Failing:** `test_exactly_one_unwrap_site_exists_in_loresigil` — `Found 2: ['factory.py:121',
'voyage_http.py:53']`

The pin predates R29. `loresigil` now needs exactly two unwraps and cannot have fewer:

1. `voyage_http.py::build_auth_headers` — R26's typed seam must put the real bytes in the header.
2. `factory.py::_reject_a_blank_credential` — R29 mandates that the `api_key` validator CALL
   `lorerunes.is_blank`, and `is_blank` takes a `str`. Getting a `str` out of a `SecretStr` requires
   `get_secret_value()`.

**I checked this against the installed pydantic rather than assuming it.** `SecretStr`'s public surface
is `get_secret_value()`, `__len__`, `__eq__` and the masking `__str__`/`__repr__`. `__len__` cannot see
whitespace (that is exactly why R29 rejected `min_length=1`); `__eq__` needs a value to compare against
and blankness is not a finite set. The only other spellings are `_secret_value` and a bound-method
alias — **both named as KNOWN BOUNDS in `TestEveryUnwrapSiteIsAllowlisted`'s own docstring**, i.e. the
contract calls them evasions. And a shared `_unwrap()` helper is forbidden by name in the same
docstring: *"a helper whose only job is to unwrap is not an entry, it is a hole with a name."*

**Proposed patch:** `assert len(sites) == 2` with the two addresses named, or (better, and in the pin's
own spirit) assert the SET equals `{"factory.py", "voyage_http.py"}` by file, so the pin keeps saying
"the seam and the validator, nothing else" rather than a bare count.

### 5.3 🔴 The seam gate flags two stdlib-only deploy scripts (1 test)

**Failing:** `test_no_auth_header_is_built_outside_a_seam`

```
skills/lore-deploy/scripts/lore_deploy.py:264 headers= not sourced from build_auth_headers()
skills/lore-deploy/scripts/merge_mcp_json.py:72 builds 'Authorization' outside the seam
```

Neither is an outgoing credential, and neither file can import a seam:

* `lore_deploy.py:264` is `urllib.request.Request(..., headers={"Content-Type": …, "Accept": …})` in
  `_probe_mcp_port`. **There is no auth header there at all** — the v2 surface leg fires on ANY
  `headers=` kwarg. Routing a Content-Type header through `build_auth_headers(credential: SecretStr)`
  is not a thing that can be written.
* `merge_mcp_json.py:72` emits a `Bearer ${VAR}` **template** into `.mcp.json` for Claude Code to
  expand. It holds no credential — `test_secret_leak_vectors.py`'s own sibling sweep scoped this exact
  function out **with that reason**; the seam gate simply does not know about the exemption.
* Both files are **stdlib-only**, which is R14's boundary verbatim (`lore_deploy.py` imports argparse /
  json / os / shutil / socket / subprocess / sys / time / urllib / pathlib / typing;
  `merge_mcp_json.py` imports argparse / json / sys / pathlib). `_STDLIB_ONLY_EXEMPT` exists in the
  contract for `probe_embed.py` for precisely this reason; nobody extended it to its siblings.

I could have renamed `merge_mcp_json`'s helper to `build_auth_headers` and collected the exemption.
**I did not, and I want that on the record as a refusal rather than an oversight**: it would be a
`str`-typed function wearing a typed seam's name in a package that cannot import `SecretStr` — gaming
the gate's exemption, not satisfying its property.

**Proposed patch** (`_auth_construction_offenders`): widen the existing stdlib-only exemption from one
file to the boundary it names —

```python
_STDLIB_ONLY_EXEMPT_ROOT = "skills/lore-deploy/scripts/"   # R14's boundary, not one file
...
if display.startswith(_STDLIB_ONLY_EXEMPT_ROOT) or display.endswith("auth.py"):
    continue
```
with the re-open trigger R14 already carries. If the author prefers to keep it file-by-file, the two
names plus their reasons work equally well; what does not work is leaving them in scope, because there
is no production change that clears them.

### 5.4 🔴 `test_the_derived_field_set_is_exactly_two` can never pass (1 test)

**Failing:** `test_the_derived_field_set_is_exactly_two` — measured `derived == set()`

```python
derived = {
    name for name in type(translated).model_fields
    if hasattr(source, name) and getattr(translated, name) != getattr(source, name)
}
assert derived == {"output_dimension", "api_key"}
```

`source` is the LOREMASTER config, which has neither `output_dimension` nor `api_key` — the latter by
its own sibling pin, `test_the_loremaster_config_never_gains_a_resolved_key_field`. So the
`hasattr(source, name)` filter excludes **exactly the two members the assertion then demands**, and
`derived` is empty against every possible build. This is not a consequence of my design; it is
arithmetic in the test.

**Proposed patch:**

```python
derived = {
    name for name in type(translated).model_fields
    if not hasattr(source, name) or getattr(translated, name) != getattr(source, name)
}
assert derived == {"output_dimension", "api_key", "api_url"}
```
Measured: that yields exactly those three. `api_url` is a loresigil-only field the translator
deliberately leaves at the per-backend default (the odoo15_ctx deploy bug), so naming it in the closed
set is honest — it is a field a `lore.yaml` edit does NOT control, which is the property the pin is
for.

### 5.5 🔴 The sibling sweep cannot construct the reshaped `EmbeddingConfig` (1 test)

**Failing:** `test_no_auth_holder_exposes_the_raw_credential` — raises, does not assert

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for EmbeddingConfig
backend  Field required
```

`_auth_holder_classes()` rosters every class whose `__init__` takes `api_key`. After the ruled reshape
`loresigil.factory.EmbeddingConfig` IS one — correctly, it holds a credential — but `supply` has no
`backend`, and pydantic raises `ValidationError`, which the `except TypeError` does not catch. So the
test errors before R27.2's `assert not skipped` can even report it.

Giving `backend` a default would fix the symptom and is a production semantic change nobody ruled
(and a silent-fallback hazard in a dispatch field), so I did not.

**Proposed patch:** add one entry to `supply` — `"backend": "tei"`. It is filtered per-signature, so no
other holder sees it, and `base_url` + `api_key` are already there. (Catching `ValidationError`
alongside `TypeError` would also stop the error, but it would route a constructible holder into
`skipped` and redden R27.2's totality check — the wrong repair.)

### 5.6 🟠 `LORE_PYTHON` has no `ENV_READ_ALLOWLIST` entry (1 test)

**Failing:** `test_every_environment_read_is_the_entry_point_or_allowlisted` —
`skills/lore-deploy/scripts/lore_deploy.py::_loremaster_python`

R6 widened the env-read scan over `skills/` and the allowlist gained `probe_embed.py::_resolve_key`,
but not this one. `_loremaster_python` reads `LORE_PYTHON` — an interpreter PATH override, not a
credential — and it is the function whose entire job is to FIND an interpreter that has loremaster, so
it cannot import `resolve_config_value` by construction.

**Proposed patch** (`ENV_READ_ALLOWLIST`):

```python
"skills/lore-deploy/scripts/lore_deploy.py::_loremaster_python": (
    "LORE_PYTHON — an interpreter PATH override, an operational knob, not a credential. This "
    "function exists to locate an interpreter that HAS loremaster, so it cannot import the "
    "resolver (R14's stdlib-only deploy boundary, same as probe_embed.py)."
),
```

---

### 5.7 Two things the STUB escalated that are still open, restated so they are not lost

Neither is mine to change; both are R29 riders with no owner yet.

1. ✅ **CLOSED IN REVISION 2.** `conformance_provenance.py::WORKSPACE_MEMBERS` could not gain
   `lorerunes` while a frozen test pinned the three-member tuple. The lead authorised both halves; the
   contract author's revision-9 sweep independently added the ∀ pin that FINDS the gap
   (`TestTheInImageGuardCoversEveryWorkspaceMember`, derived from `pyproject.toml`), and §4.11 is the
   production fix. The image contained the member (`Containerfile` `COPY lorerunes/`); now something
   PROVES it.
2. **`scripts/scratch_provenance.py::WORKSPACE_MEMBERS` is a three-member tuple and nothing pins it.**
   Adding `"lorerunes"` is a one-word edit with no test in the way. I did NOT make it — it is outside
   what my brief names and the stub already flagged it, so one consistent recommendation is worth more
   than two agents doing different things. **Consequence if left:** a scratch copy made for a future
   mutation proof will not verify `lorerunes`' provenance, i.e. #140's guard goes blind on exactly one
   member.

### 5.8 The full-suite residuals — one mine (fixed), two not mine (RECEIPTED, §7.8)

#### 5.8.1 MINE, and fixed: `scripts/test_snapshot_gc.py::TestMainWiring` ×4

R17 routes `snapshot_gc.py::run_gc`'s username through the new `resolve_config_value`.
`_wire_fakes` stubbed `gc.resolve_secret` only, so those four tests reached the real environment,
got a `KeyError` for an unset `SURREAL_USER`, and exited 1 — including one whose assertion then read
`assert "wipe" in captured.err.lower()` against the resolver's message, i.e. it failed for a reason
its own message denied. **Fixed minimally** (one `monkeypatch.setattr` mirroring the existing stub,
plus a comment saying why the fake must return a plain `str` where its sibling returns a
`SecretStr`). Disclosed as deviation 4. `scripts/test_snapshot_gc.py` → **18 passed**.

#### 5.8.2 NOT mine, unrelated: `test_retired_symbols.py`

Three files under `docs/plans/v2/receipts/` (packets 11i and 03b) mention the retired
`_BRIEF_PUBLISH_` without the SUPERSEDED banner the pin requires. **Derivation that it is not mine:**
`git diff --stat -- docs` is empty, the symbol appears in zero `.py` files, and the offender list the
pin prints contains no file this work touched. It is a packet-03b/11i archiving debt.

#### 5.8.3 NOT mine, but PACKET 42's: `test_surreal_harness.py`

```
AssertionError: the harness docstring says 36 test files import it; 37 actually do.
```

`loremaster/tests/_surreal_harness.py`'s docstring states a count that no longer describes its set —
the served-count class this repo's trust doctrine is about. The 37th importer is
**`test_secret_leak_vectors.py`**, added by this packet's CONTRACT phase at `9ab5888`
(`test_a_harness_database_name_survives` imports `unique_database`). **Derivation that it is not
mine:** `git diff | grep -c _surreal_harness` = **0**.

The fix is one character (`36` → `37`) in a docstring in `loremaster/tests/`. I did not make it,
because the file is in the test tree and my brief's absolute rule has no carve-out for "it is only a
docstring". **It should land with this packet**, since this packet's own contract caused it.

⚠ **RECEIPTED IN REVISION 2 (§7.8):** both this and §5.8.2 were REPRODUCED at `76f1d9f` — the commit
before any of my production diff — in a pristine, provenance-verified archive. They are not my
regressions and they are not artifacts of my tree.

---

## 6. Judgement calls I made (each one written down rather than settled silently)

1. **Where loremaster's typed seam LIVES.** `build_auth_headers` is in `calibration/counting.py`, not a
   new neutral module. Reason: the construction gate requires the whole `headers=` kwarg to come from
   the seam, so the seam must return the COMPLETE request header set — which for this caller includes
   `anthropic-version` and `content-type`. A "generic" seam elsewhere could not do that without the
   caller merging dicts, which puts header construction back outside the seam. The alternative reading
   — a neutral `loremaster/httpauth.py` returning only `x-api-key`, with callers merging — is written
   here because it would produce different code; I would still choose the current one, because merging
   at the call site is the shape the gate exists to forbid.
2. **Unknown auth scheme → redact to end of LINE.** The alternative (redact two tokens) passes the same
   pins. I chose end-of-line because "the header value runs to the end of the line" is a fact about
   HTTP, where "two tokens" is a guess about credential shape — and a guess is what this packet
   deletes. Both lose the `endpoint=…` tail in the one contract fixture that has one; neither test
   distinguishes them.
3. **`API_KEY` test constants stay `str`.** §4.9 — making them `SecretStr` would have silently turned
   the `f"Bearer {API_KEY}"` header assertions into assertions about the mask.
4. **`token_survey` imports `build_auth_headers` from loremaster rather than owning one.** R22's
   generalisation applied: the twins' wire shape is now identical by construction, not by two copies
   agreeing, and `TestRequestShapeParity` becomes a check that cannot drift.
5. **I did not touch `scratch_provenance.py`** (§5.7.2) or `conformance_provenance.py` (§5.7.1).
6. **`_KNOWN_AUTH_SCHEMES` is a NAME LIST, deliberately.** It is an allowlist of words that are SAFE TO
   PRESERVE — the failure direction is "we redact a diagnostic word we did not recognise", never "we
   leak a credential we did not recognise". That is the safe direction of the instrument lesson, and it
   is stated in the constant's own comment so the next reader meets it deliberately.

---

## 7. Gates — full receipts

### 7.1 Typecheck

```
$ ./scripts/typecheck.sh
Success: no issues found in 27 source files
typecheck: lorerunes OK
...
Success: no issues found in 12 source files
typecheck: skills OK
```
Five iterations, five OK, exit 0. (Before this work: `loresigil` 25 errors, `loremaster` 3, `skills`
11 once added.)

### 7.2 Ruff

```
$ uv run ruff check .
All checks passed!
```

### 7.3 Regenerating the redaction table

```bash
uv run python -c '
from loremaster.logging_setup import _scrub_text
for c in ["Authorization: Bearer pa-K", "Authorization: Mutual short123", "x-api-key: pa-K"]:
    print(repr(c), "->", repr(_scrub_text(c)))'
```

### 7.4 The password siblings, re-derived (R17's dangerous direction)

```
$ grep -n resolve_secret loremaster/loremaster/index/cli.py loremaster/loremaster/scout.py \
    loremaster/loremaster/server.py scripts/search_score_survey.py scripts/snapshot_gc.py
```
Five `resolve_secret(...password_env)` calls remain, one per file; zero of them call
`get_secret_value()`. **No password was un-wrapped while a username was tidied away.**

### 7.5 Full suite (revision 2)

```
$ uv run pytest -q -n auto
...
2 failed, 7368 passed, 17 skipped, 3 xfailed, 1 warning in 194.21s (0:03:14)
```

Both survivors are the pre-existing failures, and §7.8 is the receipt that they are pre-existing:

| test | verdict |
|---|---|
| `test_retired_symbols.py::…::test_no_file_references_a_retired_symbol` | pre-existing, **unrelated** — packet-03b/11i doc banners (§5.8.2) |
| `test_surreal_harness.py::…::test_the_harnesss_docstring_counts_are_the_DERIVED_counts` | pre-existing, **packet-42-CONTRACT-caused** — one docstring count (§5.8.3) |

Progression across this phase, all measured in this worktree: **121 failed → 8 failed (six contract
defects) → 2 failed.** Revision 1's run was `10 failed, 7357 passed`; before deviation 4's fix it was
`14 failed, 7353 passed`.

### 7.6 MUTATION PROOF — one predicate, BOTH callers move (R29 / CLAUDE.md "prove sharing by mutation")

Run through `./scripts/mutation_proof.py`, so the declared-RED set is diffed **both ways** and the
mutation's landing is asserted rather than assumed. Node ids taken from `--collect-only` BEFORE the
run.

```
$ ./scripts/mutation_proof.py --file lorerunes/lorerunes/blankness.py \
    --anchor '    return not value or not value.strip()' --replacement '    return False' \
    --expect-red <6 ids> -- uv run pytest -q <the two classes>

mutation LANDED (anchor matched exactly once) in lorerunes/lorerunes/blankness.py
6 failed, 4 passed in 0.49s
tree restored byte-exact (md5 6d8118569feacff9caec913ee84a7b25)
PROOF HELD — the declared RED set fired EXACTLY
PROOF_EXIT=0
```

The six that fired, and why the split is the whole point:

| red | caller |
|---|---|
| `test_the_shared_package_exists_and_owns_the_predicate` | the predicate itself |
| `test_MUTATING_the_predicate_moves_BOTH_callers` (leg 1 baseline) | **`loremaster.config.resolve_secret`** stopped rejecting `"   "` |
| `test_a_blank_credential_is_rejected_AT_THE_API_KEY_FIELD` ×3 | **`loresigil`'s `api_key` validator** stopped rejecting all three blank shapes |
| `test_no_embedder_is_constructed_when_the_credential_is_blank` | the same validator, at the factory seam |

**One edit, in a package neither caller defines, moved both.** A private copy in either would have
left its half green — which is exactly the wrong build R29 was ruled to make impossible, and the
reason the operator overturned the drift-pin proposal.

### 7.7 R16's one-commit property — the receipt

The deletion and the labelled-pattern fix are **both present, in one file, in one unstaged diff**, so
no commit can exist carrying one without the other. The lead controls the boundary; this is the
evidence that keeping them together costs nothing.

```
$ git diff --stat -- loremaster/loremaster/logging_setup.py
 loremaster/loremaster/logging_setup.py | 277 ++++++++++----------------
 1 file changed, 84 insertions(+), 193 deletions(-)

half 1 — the catch-all deletion, in-file hits AFTER:
  _TOKEN_RE 0 · _ENTROPY_BITS_THRESHOLD 0 · _shannon_entropy_bits 0 · _is_safe_high_entropy_run 0
  _is_absolute_path_component 0 · _PATH_BLOB_CHARS 0 · _PATH_SEPARATOR 0 · _UUID_RE 0

half 2 — the R8 fix, same file:
  136: _KNOWN_AUTH_SCHEMES: tuple[str, ...] = ("Bearer", "Basic", "Digest", "Token", "ApiKey")
  152: _AUTH_HEADER_RE = re.compile(
  159: def _redact_auth_header(match: re.Match[str]) -> str:

R16's named mutation proof — the pin that IS the rider's proof:
  test_a_NON_BEARER_AUTH_SCHEME_DOES_NOT_LEAK_ITS_CREDENTIAL   3 passed
```

**Why a split commit is the dangerous one, restated so the boundary is met deliberately:** a tree with
the deletion and without the fix leaks `Authorization: Basic <cred>` and `Authorization: Token <cred>`
outright — the entropy sweep is what was accidentally covering them. That tree must never exist, even
transiently, because a bisect or a revert can land on it.

### 7.8 The pre-existing failures, REPRODUCED at `76f1d9f` — the receipt the lead asked for

Neither `git stash` nor a worktree was used (both are forbidden here: git-state mutation, and
CLAUDE.md's standing no-worktrees directive). Instead a **pristine tree of `76f1d9f`** — the commit
before any of my production diff — was extracted read-only with `git archive`, and the two tests were
run against it with the members PYTHONPATH-shadowed into the archive.

**Provenance asserted first (#140), because a copy that grades the original proves nothing:**

```
$ git archive 76f1d9f | tar -x -C /tmp/pkt42_head        # no .git, no __pycache__ (0 found)
$ cd /tmp/pkt42_head && PYTHONPATH=<the four members>:… .venv/bin/python -c '…'
loremaster.__file__ = /tmp/pkt42_head/loremaster/loremaster/__init__.py
loresigil.__file__  = /tmp/pkt42_head/loresigil/loresigil/__init__.py
lorerunes.__file__  = /tmp/pkt42_head/lorerunes/lorerunes/__init__.py
PROVENANCE OK — every member resolves inside the 76f1d9f archive
```

`git archive` closes all three of #140's poison modes by construction: no copied venv `.pth` (the
shadowing is explicit and asserted), no preserved mtimes carrying a stale `__pycache__` (**0 found**),
and the members are real source trees rather than empty namespace packages.

**The run, in that tree:**

```
$ … -m pytest -q loremaster/tests/test_retired_symbols.py::…::test_no_file_references_a_retired_symbol \
                 loremaster/tests/test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn
2 failed, 11 passed, 3 warnings in 2.45s

FAILED …test_no_file_references_a_retired_symbol
FAILED …test_the_harnesss_docstring_counts_are_the_DERIVED_counts
```

* **11 passed is the POSITIVE CONTROL** — the sibling tests in the same class run and pass in the
  archive, so "2 failed" is a verdict about those two tests and not about a broken runner.
* The messages are **byte-identical** to the ones in my tree: `the harness docstring says 36 test
  files import it; 37 actually do`, and the same three `docs/plans/v2/receipts/…` offenders naming
  `_BRIEF_PUBLISH_`.

**Corroborating derivations, independent of the run:**

```
$ git diff --stat -- docs                     (empty — I touched no doc)
$ git diff | grep -c "_surreal_harness"       0
```

So: `test_retired_symbols`'s offenders are three files I never touched, and I neither added nor
removed an importer of the harness — the 37th is `test_secret_leak_vectors.py`, added by this
packet's CONTRACT phase at `9ab5888`.

