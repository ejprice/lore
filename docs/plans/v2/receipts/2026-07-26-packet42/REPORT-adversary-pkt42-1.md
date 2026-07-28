# REPORT-adversary-pkt42-1 — CONTRACT ADVERSARY, packet 42

brief-base v7 read

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT** — 4 missing pins, 2 of them BLOCKER (a wrong build survives, or a green build ships a leak).
- **P1 headline — YES, wrong builds survive.** (1) A build scoring **204 passed / 0 failed** on the full logging contract **leaks a real production Anthropic key through 6 paths**, from the object the `UNWRAP_ALLOWLIST` itself blesses (`counting.py::__init__`, category `AUTH_HEADER`). Base leaks **0/6**: this is a *strict regression*, not an accepted bound. (2) A build where `_scrub_value` stops recursing into containers also scores **204 passed / 0 failed** and leaks a labelled `Authorization: Bearer …` out of an `extra=` header map end-to-end.
- **Wrong builds that were correctly KILLED:** inlined-catch-all-without-the-names (72 RED, by *behavioural* pins), deletion-without-R8 (11 RED, all R8 pins, right reason). The R8 surface is genuinely strong.
- **P-PKG diff:** the ruled `dotenv_values` mechanism **violates ruling R1's byte-exactness** — `interpolate=True` is the default and rewrites `${VAR}` in a secret (all quoting forms; an unset var silently becomes `""`). Not in the inventory, not in the author's 11 measured cases, not pinned.
- **P6b diff:** inventory has **no D section for `probe_embed.py`** (R6 pulled a 4th resolver in scope with zero enumerated behaviors — its distinct `sys.exit(_EXIT_BAD_USAGE)` and `--env-file` remediation message are unrecorded). I would re-adjudicate **C5** from `dropped-deliberately (mechanism)` to **spec-silent → ruling**.
- **Verified-and-true author claims:** RED counts exact (92R/219G; logging-setup 0R/44G) · R3 mutation proof reproduced (2 RED, both directions, site named) · **R6 rider is real** — the gate provably reaches `skills/` (93 files scanned, `probe_embed.py` present, inline tests excluded) · `_secret_value` KNOWN BOUND is genuinely pinned with a re-open trigger.
- **MISSING PINS:** MP1 structured/quoted-label redaction · MP2 `_scrub_value` container recursion · MP3 byte-exactness under `${VAR}` · MP4 §9 under-scopes `test_embedding_prompt_name.py` (C-DEF, 5 RED proven).
- **Receipt pointers:** §P1 (wrong builds + both-legs missing pin) · §P1b (quantifier table) · §P-PKG · §P6b (two-stage diff) · §P4 (reproduced claims) · §Residuals (each with an individual verdict).
- **Packages considered:** `python-dotenv` 1.2.2 → **finding, not a verdict** (read installed `inspect.signature(dotenv_values)` → `interpolate: bool = True`; measured 13 parse cases incl. 5 interpolation shapes — divergence proven, see §P-PKG). `pydantic.SecretStr` → **replace, agreed** (measured 8 unwrap spellings against the gate's AST predicate). No mechanism was specified or built by me beyond scratch probes.
- **Tree provenance (#140):** all probes in `scripts/scratch_copy.sh`-built scratch; `loremaster.__file__ = /tmp/…/scratchpad/adversary-pkt42/ref/loremaster/loremaster/__init__.py` (printed live, §P0). **The repo was never edited** — `git status` on `lore-pkt42` shows only the contract author's own 6 files.

All measurements below taken **2026-07-26**, against worktree `lore-pkt42` at **`506e595`**, in a scratch copy. Statements are dated to that SHA, not to "today".

---

## P0 — MY OWN PROBES' CONTROLS (this section applies first)

**Provenance receipt.** Scratch built with the blessed tool, not `cp -a`:

```
scratch copy READY: /tmp/…/scratchpad/adversary-pkt42/ref
  loremaster  -> /tmp/…/scratchpad/adversary-pkt42/ref/loremaster/loremaster/__init__.py
  loresigil   -> /tmp/…/scratchpad/adversary-pkt42/ref/loresigil/loresigil/__init__.py
```
Printed again live inside the P1 probe run. Every wrong build was graded in that tree.

**A probe of mine failed for the wrong reason, and I caught it.** My first W-DEL build was
assembled through a nested shell heredoc, which turned `rf"\1\2{REDACTED}"` into the control
characters `\x01\x02`. It scored *47 failed* and I nearly reported that as "the contract catches
the partial fix". It was catching **my broken build**:

```
SANITY: 'store.connect.failed \x01\x02***REDACTED*** endpoint=ws://x/rpc'
```
Rebuilt from a file instead of a heredoc; the sanity line then read
`'store.connect.failed api_key:***REDACTED*** endpoint=ws://x/rpc'`, and the honest result was
**11 failed** — all of them R8 pins. **Every wrong build in this report carries a sanity line
proving the mutation landed as intended.**

**A second self-caught artifact.** My scratch path contains
`-home-ejprice-PycharmProjects-lore`, a 30-char high-entropy run, so the base catch-all redacted
it inside tracebacks and `test_ordinary_traceback_text_is_not_mangled` went RED *in scratch only*.
In the real worktree that file is **44 passed / 0 failed**. I verified in both trees before
reporting a count. (It is also an unusually pure demonstration of the packet's own thesis.)

**Positive control on the leak oracle.** Every leak measurement below is paired with shapes the
same probe reports as *not* leaking (`x-api-key: <k>` and `api_key=<k>` are redacted on the same
build in the same run), so "LEAK=True" is a discrimination, not a probe that always fires.

---

## P1 — WRONG BUILDS. Two survive.

### Reference build first (the control that makes the rest mean anything)

I built the deletion + the author's recommended R8 shape (known-scheme preserved, everything
else redacted to end of line) independently, from the spec and the pins, without copying the
author's build:

```
loremaster/tests/test_secret_leak_vectors.py loremaster/tests/test_logging_setup.py
204 passed in 1.48s
```

**The author's §10.2 satisfiability receipt is independently reproduced.** Every "survives"
claim below is measured against *this* green build, so a survivor is a hole in the contract and
not a hole in my implementation.

### 🔴 BLOCKER F1 — a 204/204 build leaks a production credential through 6 paths

The `UNWRAP_ALLOWLIST` blesses `loremaster/calibration/counting.py::__init__` under category
`AUTH_HEADER` — *"baked into an HTTP client's header map and held nowhere else"*. That is the
one place in the tree where a real credential provably exists as a **bare `str`**, by design.
I drove the **real production object** through the **real production log path** on the
contract-green build:

```
PROVENANCE: /tmp/…/scratchpad/adversary-pkt42/ref/loremaster/loremaster/__init__.py
repr(self._headers) = {'x-api-key': 'sk-ant-api03-7hQ2xR9mB4kW1nT6vY8pL3cJ5dF0gS-…', 'anthropic-version': …

extra= header map        [json    ] CREDENTIAL LEAKED = True
extra= header map        [keyvalue] CREDENTIAL LEAKED = True
message interpolation    [json    ] CREDENTIAL LEAKED = True
message interpolation    [keyvalue] CREDENTIAL LEAKED = True
exception message        [json    ] CREDENTIAL LEAKED = True
exception message        [keyvalue] CREDENTIAL LEAKED = True
_scrub_value({'x-api-key': KEY}) -> {'x-api-key': 'sk-ant-api03-7hQ2xR9mB4kW1nT…'}
```

**The paired control — the same six cases on BASE, catch-all alive:**

```
=== BASE (catch-all ALIVE) — same six cases ===
extra= header map        [json    ] CREDENTIAL LEAKED = False
extra= header map        [keyvalue] CREDENTIAL LEAKED = False
message interpolation    [json    ] CREDENTIAL LEAKED = False
message interpolation    [keyvalue] CREDENTIAL LEAKED = False
exception message        [json    ] CREDENTIAL LEAKED = False
exception message        [keyvalue] CREDENTIAL LEAKED = False
_scrub_value({'x-api-key': KEY}) -> {'x-api-key': '***REDACTED***'}
```

**0/6 → 6/6. A strict regression, invisible to all 204 tests.**

**Why both of the packet's defences structurally miss it — this is the important part:**

1. **It is not the accepted A18 bound.** A18 is *"an **UNLABELLED** secret in free log text"*.
   Here the credential **is labelled** — `x-api-key` — and packet Scope OUT explicitly promises
   *"The labelled patterns stay. This packet does not remove defence-in-depth."* That promise is
   **false for the structured form**. `_ASSIGNMENT_RE` requires the label to be *immediately*
   followed by `\s*[=:]\s*`; in a mapping repr or JSON there is a **quote** between them. And in
   `_scrub_value`, keys and values are scrubbed **independently**, so the label never adjoins the
   value at all — the pattern is structurally incapable of firing.
2. **The SecretStr replacement control cannot apply.** At that site the value is a bare `str`
   *by design*; the allowlist entry is precisely the licence to make it one.

The full surface, measured on the green build (controls last, and they discriminate):

```
python dict repr (x-api-key)            LEAK=True   -> {'x-api-key': 'sk-ant-api03-…'}
python dict repr (Authorization Token)  LEAK=True   -> {'Authorization': 'Token pa-Q4nT…'}
json body                               LEAK=True   -> {"api_key": "sk-ant-api03-…"}
json body (authorization)               LEAK=True   -> {"authorization": "sk-ant-api03-…"}
httpx-style kwargs                      LEAK=True   -> post(headers={'x-api-key': 'sk-ant-…'})
_scrub_value nested dict                LEAK=True   -> {'headers': {'x-api-key': 'sk-ant-…'}}
python dict repr (Authorization Bearer) LEAK=False  -> {'Authorization': 'Bearer ***REDACTED***
CONTROL bare colon form                 LEAK=False  -> x-api-key: ***REDACTED***
CONTROL assignment form                 LEAK=False  -> api_key=***REDACTED***
```

(`Bearer` survives only because `_BEARER_RE` needs no separator. `Token`, `Basic` and every
non-Bearer scheme leak in the structured form even *with* the R8 fix.)

**The contract's only pin on this surface is `test_the_anthropic_api_key_header_is_redacted`,
and it uses `x-api-key: <k>` — a form that does not exist in the codebase.** The form that does
exist is `{"x-api-key": <k>}`, built two lines away in `counting.py::__init__`.

**THE MISSING PIN, WRITTEN AND PROVEN BOTH WAYS** (scratch copy, never the repo):

```
LEG 1: on the CONTRACT-GREEN reference build   ->  5 failed in 0.23s     (the defect)
LEG 2: on BASE, catch-all alive                 ->  5 passed in 0.16s     (not a botched expectation)
```

### 🔴 BLOCKER F2 — `_scrub_value` can stop recursing entirely and score 204/204

Wrong build: replace the dict/list/tuple recursion with `return value`.

```
### W-COSMETIC: _scrub_value stops recursing into containers ###
204 passed in 1.58s
```

Three-way control proving it is a real regression and not a cosmetic quibble:

```
=== build: REF (correct) ===
  _scrub_value nested LABELLED bearer : {'headers': {'Authorization': 'Bearer ***REDACTED***'}}
  END-TO-END through configured logger — LEAKED = False
=== build: WCOS_no_recursion ===
  _scrub_value nested LABELLED bearer : {'headers': {'Authorization': 'Bearer pa-Q4nT8vX2mK9…'}}
  END-TO-END through configured logger — LEAKED = True
=== BASE ===
  BASE nested LABELLED bearer         : {'headers': {'Authorization': 'Bearer ***REDACTED***'}}
```

**Why the `extra-nested` carrier cannot see it, and this generalises:** the carrier is driven
with two legs. The `SecretStr` leg is masked **by the type**, whatever `_scrub_value` does; the
bare-`str` leg is the **accepted bound** (`test_a_bare_str_credential_does_reach_the_sink`
asserts the credential *does* reach the sink), so breaking the recursion makes that assertion
*more* true. **For any property where the SecretStr leg is saved by the TYPE and the bare-str
leg is an accepted bound, the pair is non-discriminating.** The paired-control design is
excellent — this is its one blind spot, and it is exactly where inventory item A19
("preserved — call sites unchanged") lives.

### ✅ Wrong builds the contract correctly KILLED

| build | result | killed by |
|---|---|---|
| **W3 — delete the NAMES, keep the BEHAVIOUR** (entropy sweep inlined in `_scrub_text`, zero module symbols) | **72 failed / 132 passed** | **behavioural** pins — the A18 bound pins, `TestScrubbingNoLongerDestroysDiagnosticData`, the four `HOSTILE_PATHS`. Not the retired-symbol pins. This is the frontier-5 attack and the contract wins it cleanly. |
| **W-DEL — deletion, no R8 fix** (the partial fix) | **11 failed / 193 passed** | every one an R8 pin: `…scheme_word_survives_a_full_authorization_header`, `…case_insensitively_and_mid_line`, `NON_BEARER…[basic/token/apikey]`, `UNKNOWN…[negotiate/hoba/mutual-short/vendor]`, `…INTERACT_in_the_right_order`, `…disabling_the_authorization_label`. Sanity line confirmed the build was well-formed. |

**Verdict on the R8 surface: I could not break it.** The scheme-allowlist shape the lead asked
me to attack hard is closed by `test_an_UNKNOWN_auth_scheme_does_not_leak_its_credential_either`
(4 schemes in no list the code may hold). While building REF I independently hit the author's
§0.5 **Trap 2** — my first `[A-Za-z][A-Za-z0-9_-]*\s+` scheme matcher treated
`authorization: lore-root-pw-not-a-real-one endpoint=…` as scheme+credential and leaked the
password; the **28-case ∀ label × ∀ separator matrix** caught it. That matrix is load-bearing and
is doing exactly the job claimed for it.

---

## P1b — QUANTIFIER TABLE (mandatory)

Every invariant classified. Every **guarded** row carries a receipt: a surviving door-build, or
the pin that killed my door-build.

| # | invariant | ∀-over-inputs / GUARDED | receipt |
|---|---|---|---|
| I1 | A `SecretStr` credential never reaches a rendered log line | **GUARDED** — ∀ over *7 carriers someone enumerated*, not ∀ over "shapes a log call can carry a credential" | 🔴 door-build: the **header-map carrier** (the one the allowlist blesses) is not in the population → **F1**, 6/6 leak on a 204/204 build |
| I2 | An unlabelled credential in free text is NOT redacted (accepted bound) | ∀ over 7×3×2 matrix | ✅ killed W3 (72 RED) |
| I3 | Labelled patterns still redact, label+separator preserved | **GUARDED** — ∀ over label × separator **in the inline `label<sep>value` FORM only** | 🔴 door-build: the **structured/quoted form** (`{'x-api-key': …}`, JSON) → **F1**; base redacts it, green build does not |
| I4 | R8: known scheme preserved, credential always gone | ∀ over known **and** unknown schemes (7 total, 4 in no list) | ✅ killed W-DEL (11 RED); killed my own Trap-2 REF draft |
| I5 | Scrubbing is idempotent | ∀, with a "redaction actually happened" guard | ✅ green on REF; guard prevents the identity-function pass |
| I6 | All three consumers route through one `_scrub_text` | ∀ over 3 consumers, mutation-proven | ✅ reproduced; W3 caught |
| I7 | `_scrub_value` recurses through containers (inventory A19) | **GUARDED — in fact UNPINNED** | 🔴 door-build **W-COSMETIC survives 204/204** → **F2** |
| I8 | The entropy machinery is gone (8 retired symbols) | **GUARDED** — keyed on 8 NAMES | ✅ door-build W3 (behaviour without names) killed by *behavioural* pins, 72 RED. Name-keying is backstopped. |
| I9 | No traceback formatter renders frame locals (M4) | ∀ property legs + `rich show_locals=True` positive control + name-keyed leg with honesty pin | ✅ not broken; the positive control proves the probe fires |
| I10 | Every unwrap site is allowlisted | **GUARDED** — keyed on the `.get_secret_value()` **CALL spelling** | ⚠ 5 of 8 spellings invisible (§Residual R1). `_secret_value` **is** pinned as a KNOWN BOUND with a re-open trigger — *claim verified*. `getattr`/bound-alias/laundering-helper are not. |
| I11 | Only `loremaster/config.py` reads env for a secret | ∀ over `os.environ`/`os.getenv` AST reads, both ways | ✅ fires at base (2 RED); not separately attacked |
| I12 | No server-path call site passes an `env_file` (R3) | ∀ over `resolve_secret` calls, **both spellings**, **both directions** | ✅ mutation reproduced: 2 RED, offending site named |
| I13 | A resolved secret is byte-exact from either source (R1) | **GUARDED** — ∀ over *source*, not over *value content* | 🔴 door: `${VAR}` in the value → `dotenv_values` rewrites it (**MP3**, §P-PKG) |
| I14 | Every backend puts the real credential bytes on the wire | ∀ 3 arms, real requests, equality | RED at base as designed; not attacked (needs the full loresigil build) |
| I15 | 10 fields still copy through `to_loresigil_config` | ∀ fields, every fixture non-default + a no-default control | not attacked; design is sound |
| I16 | Every scan finds a real population | positive control on **every** scan | ✅ verified live: 93 files, `skills/` reached, `probe_embed.py` present |

---

## P-PKG — MY PACKAGE TABLE, BUILT FIRST, THEN DIFFED

I enumerated the mechanisms before opening §2.

| mechanism | my read | my verdict | author's verdict | diff |
|---|---|---|---|---|
| parse `KEY=value` from a `.env` | `inspect.signature(dotenv_values)` → **`interpolate: bool = True`**; measured 13 parse cases | **replace_with_adapter** — dotenv, **called with `interpolate=False`** | `replace`, `dotenv_values` | 🔴 **DIVERGENT — see below** |
| resolve env var named by runtime data | agree with author's read of `EnvSettingsSource._extract_field_info` | `bespoke` (keep `resolve_secret`) | `bespoke` | ✅ agree |
| hide a credential from `repr`/`str` | `vars(SecretStr('x'))`; measured 8 unwrap spellings vs the gate predicate | `replace` | `replace` | ✅ agree |
| render traceback with locals | agree | `keep_with_trigger` (rich) | `keep_with_trigger` | ✅ agree |
| detect a secret in arbitrary text | — | **delete** (the packet's thesis) | `bespoke → DELETED` | ✅ agree |
| entropy / candidate window | — | **delete** | deleted | ✅ agree |

### 🔴 MP3 — the ruled mechanism violates ruling R1's byte-exactness

R1 is explicit: *"the value is **never stripped** (a key whose real bytes include leading/trailing
whitespace survives **byte-exact**)"*. `dotenv_values` defaults to `interpolate=True`. Measured:

```
python-dotenv 1.2.2   SIGNATURE: (dotenv_path=None, stream=None, verbose=False, interpolate: bool = True, encoding='utf-8')

braced ${HOME}         interpolate=True -> p/home/ejpricex          interpolate=False -> p${HOME}x
bare $HOME             interpolate=True -> p$HOME-x                 interpolate=False -> p$HOME-x
braced UNSET var       interpolate=True -> px                       interpolate=False -> p${NOT_SET_ANYWHERE}x
double-quoted braced   interpolate=True -> p/home/ejpricex          interpolate=False -> p${HOME}x
single-quoted braced   interpolate=True -> p/home/ejpricex          interpolate=False -> p${HOME}x
```

Three things make this worse than a curiosity: it fires **inside single quotes** (where POSIX
shell semantics say literal, so an operator's intuition is wrong); an **unset** braced var
silently collapses to `""`, *shortening* a credential rather than failing; and `resolve_secret`
is now the **shared** resolver for **every** secret including operator-chosen SurrealDB root
passwords, where `${` is entirely plausible. The failure mode is a *wrong* credential and a
confusing auth error, not a loud one.

Against the author's own 11 measured cases (§2): `export`, quotes, `KEY=a=b=c`, comments,
padding, duplicates — **no interpolation case**. The inventory's C5 asserts dotenv *"does it more
correctly"*, which is a superiority claim about the half that was read. This is the exact
read-column failure the P-PKG probe exists for, in its inverted form.

**The fix is one keyword**, and it belongs in the pin: `dotenv_values(env_file, interpolate=False)`.

**Also confirmed (3rd divergence, author already found it honestly):** the real-then-blank dual —
old parser returns `"sk-ant-REALKEY-000"`, dotenv returns `""` → fatal. The author flagged this
in §8-note-C as unpinned and unasked. **I agree it is a live open question, and I would take
last-wins too** — but note it is a *behaviour change on a fail-open→fail-closed axis*, so it
deserves a ruling rather than a preference. The `export ` divergence is the intended C11 fix and
is correctly pinned forward.

---

## P6b — TWO-STAGE ENUMERATION DIFF

Stage 1 was written to disk from the base sources **before** the inventory's A/B/C tables were
opened (only the two operator-ruling sections were read first, as the brief permits). 47 items
enumerated across A/B/C/D/E.

### Behaviors I found that the inventory MISSED

| mine | behavior | why it matters |
|---|---|---|
| **mD1–mD6** | **There is no D section at all.** R6 pulled `probe_embed.py::_resolve_key` — a **fourth** resolver — into scope in the second ruling wave, and **no inventory rows were added**. Unrecorded: it exits with a **distinct code** `sys.exit(_EXIT_BAD_USAGE)` rather than raising (and `lore_deploy.py` shells out and branches on that exit code); its message names the **`--env-file` remediation**; it imports **only stdlib today**, so migrating adds a hard `loremaster.config` dependency to a skill script. | R6 is the packet's size-overrun item. Its behaviors are adjudicated nowhere. |
| **mA16** | `_ASSIGNMENT_RE` cannot match a **quote-separated** label (mapping repr / JSON). A18 is framed as "unlabelled", which **understates the widening**. | This is **BLOCKER F1**. |
| **mA17** | `_ASSIGNMENT_RE`'s value group is `(\S+)` — a single whitespace-delimited token. | R8 covers the consequence, but no A-row records the cause. |
| **mB10** | `EmbeddingConfig` gaining a `SecretStr` field changes `model_dump()` / `model_dump_json()` output shape for every serialiser of that model. | Silent wire/debug shape change. |
| **mB11/mB12** | Three backends, **two** bearer seams: `tei.py` inlines `f"Bearer {api_key}"`; the two voyage arms route through `build_bearer_client`. No inventory row for `build_bearer_client`. | The ONE-IMPLEMENTATION target is unnamed in the inventory. |
| **mC6** | Duplicate non-blank keys: old = **FIRST** wins, dotenv = **LAST** wins. C6 covers only blank-then-real. | Author independently found the dual (§8-note-C). |
| **mC9** | `DEFAULT_ENV_FILE` is a **default argument** — "the server gets no file" is a call-site property that a default silently re-grants. | R3's trap; the contract pins the call sites, so it is covered — but the inventory has no row. |
| **mC10/mC11** | dotenv **interpolation** and inline-comment handling. | **MP3**, above. |
| **mE3** | `to_loresigil_config` becomes an **IO-performing** function; its `Raises:` contract and its callers' blast radius change. | **MP4**, below. |
| **mA21** | `math` / `collections.Counter` become orphaned imports; ruff will demand deletion. | Trivial, but it is a builder-visible consequence. |

### Inventory items I MISSED

- **A13 — idempotence.** I did not enumerate it. Real, and correctly pinned with an
  "a redaction actually happened" guard.
- **C10 — the twins are "byte-divergent".** I recorded them as logically identical; the
  inventory is more precise about the source formatting. (Note: the *message strings* are
  identical — the divergence is line-wrapping only, so "byte-divergent" slightly over-claims.)
- **B10 / A19** — I had these, less crisply stated.

### Verdicts I would ADJUDICATE DIFFERENTLY

1. **C5** — inventory says `dropped-deliberately (mechanism)`, *"dotenv owns quote/escape handling
   and does it more correctly"*. I would rule **spec-silent → operator ruling**, because the
   replacement mechanism changes the value's **bytes** (§P-PKG) and R1 governs exactly that.
2. **C4 vs C11 are in tension.** C4 is `preserved-with-pin` for *"matches lines starting with
   `ANTHROPIC_API_KEY=`"*; C11 says the `export ` miss is an old bug not to be re-pinned. A pin
   written literally to C4 would **re-pin C11's bug**. The contract resolves this correctly
   (`test_an_export_prefixed_line_is_honoured`), but the inventory rows contradict each other.
3. **C11's count is wrong** — it says "one twin"; **both** twins fail. The author already
   re-derived this and reported it (§5). Confirmed independently: both use
   `stripped.startswith(f"{ANTHROPIC_API_KEY_ENV}=")`.
4. **A18's framing** — "an **unlabelled** secret" should read "**any** secret the two labelled
   patterns do not match, **including labelled ones in structured renders**". The narrower wording
   is what let F1 through.

---

## P4 — AUTHOR CLAIMS, REPRODUCED (never relayed)

| claim | verdict |
|---|---|
| RED at base: **92 failed, 219 passed**; logging-setup **0R/44G** | ✅ **EXACT.** `44 passed in 0.18s` in the real worktree. My scratch showed 93R/218G — traced to my own hashy scratch path, not a defect (§P0). |
| §10.2 satisfiability: **204 passed, 0 failed** | ✅ **REPRODUCED** on my own independently-built reference. |
| §10.4 R3 mutation proof: 2 RED, both directions, site named | ✅ **REPRODUCED** verbatim: `assert not ['loremaster/scout.py::from_config']` and `{…from_config} == {…load_api_key}`. Declared-RED set taken from `--collect-only` first; mutation landing asserted, not hoped. Restored byte-exact (md5 match). |
| §0.3 R6 rider — *"the gate RUNS over `skills/`"* | ✅ **TRUE, and it is a real receipt.** Live: `total scanned files: 93` · `Counter({'loremaster': 56, 'loresigil': 13, 'lorescribe': 12, 'scripts': 8, 'skills': 4})` · `probe_embed present: True` · `skills test files excluded: []`. Given packet 03b's two dead instruments, this one deserves the credit. |
| §2 — `_secret_value` is a pinned KNOWN BOUND with a re-open trigger | ✅ **VERIFIED** in `TestEveryUnwrapSiteIsAllowlisted`'s docstring, with the trigger stated. |
| §5 — "the catch-all does not protect realistic passwords" (3.102 / 3.495 vs 3.5) | ✅ consistent with my W3/REF measurements. |
| §9 — the migration enumeration is complete | ⚠ **file list complete; characterisation not.** See MP4. |

---

## MISSING PINS — each as *the test that should exist* + *the defect it catches*

### MP1 🔴 BLOCKER — structured/quoted-label redaction
**Test:** in `test_secret_leak_vectors.py::TestTheLabelledPatternsSurviveTheDeletion`, a
parametrised pin over the **structured** renders of a labelled credential —
`repr({"x-api-key": K})`, `'{"api_key": "K"}'`, `'{"authorization": "K"}'`,
`"post(headers={'x-api-key': 'K'})"` — plus a `_scrub_value` leg on a nested header **map**.
Best driven from the real object: `AsyncClaudeTokenCounter(api_key=SecretStr(K))._headers`.
**Defect it catches:** deleting the catch-all silently un-guards the *only* production site where
a credential is a bare `str` by design (the `AUTH_HEADER` allowlist entries in
`counting.py::__init__` and `token_survey.py::__init__`). 0/6 → 6/6 leak, with all 204 tests green.
**Receipt:** both legs proven — 5 failed on the green build, 5 passed on base.
**Note for the author:** this pin is currently *unsatisfiable* by the labelled patterns as
designed — closing it needs either a delimiter-tolerant label pattern
(`label` `["']?` `\s*[=:]\s*` `["']?`) or a `_scrub_value` change that passes the mapping KEY as
context when scrubbing its value. **That is a design fork and belongs to the operator, not to a
builder** — flagging rather than prescribing.

### MP2 🔴 BLOCKER — `_scrub_value` container recursion (inventory A19)
**Test:** `test_scrub_value_recurses_through_containers` — assert a labelled credential nested in
`{"headers": {"Authorization": f"Bearer {K}"}}` and in `["api_key=K"]` is redacted, driven
end-to-end through `configure_logging` as well as directly.
**Defect it catches:** a build that replaces the dict/list/tuple recursion with `return value`
scores **204 passed / 0 failed** and leaks a labelled bearer token out of an `extra=` field.
**Receipt:** three-way control (BASE redacts / REF redacts / W-COSMETIC leaks end-to-end).
**Why the existing carrier can't:** the `SecretStr` leg is masked by the *type*, and the
bare-`str` leg is an *accepted bound asserted to leak* — so both legs pass either way.

### MP3 🟠 — byte-exactness under `${VAR}` (ruling R1)
**Test:** `test_a_credential_containing_a_dollar_expansion_survives_byte_exact` — a `.env` value
`p${HOME}x` (and `p${NOT_SET_ANYWHERE}x`) must resolve **unchanged**, ∀ quoting form.
**Defect it catches:** a builder copying R2's snippet verbatim gets `interpolate=True` and
silently rewrites secrets; an unset braced var *shortens* the credential to `px`.
**Receipt:** §P-PKG measurement table. One-keyword fix: `interpolate=False`.

### MP4 🟠 — §9 under-scopes `test_embedding_prompt_name.py` (C-DEF class)
**Not a test to write — a scope line to correct.** §9 says of that file only
*`assert loresigil_config.api_key_env == "LORE_TEI_KEY"`*, and heads the table
*"None is an adjudication — they are field renames."* It is not a rename. The file has **no
`monkeypatch.setenv` anywhere**, `LORE_TEI_KEY` is in no conftest and not in the ambient env, and
once `to_loresigil_config` resolves, **5 tests raise `KeyError`**:

```
minimal reshape applied
FAILED …TestToLoresigilConfigCarriesPromptNames::test_query_prompt_name_carried_to_loresigil_config
FAILED …test_document_prompt_name_carried_to_loresigil_config
FAILED …test_both_prompt_names_carried_together
FAILED …test_none_prompt_names_translated_as_none
FAILED …test_existing_fields_are_still_translated_faithfully
5 failed, 5 passed in 0.22s
E   KeyError: "Required secret environment variable 'LORE_TEI_KEY' is unset, empty, or whitespace-only…"
```
**Defect it catches:** the builder meets 5 RED tests whose fix (an autouse env fixture) is not in
its authorised set. §9 should say *"add an env fixture; `to_loresigil_config` now performs IO."*
**§9's FILE list is otherwise complete** — I independently enumerated every consumer and ran the
reshape across `test_embedding*`, `test_eager_startup`, `test_cli`, `test_impact`,
`test_workspace_status` and all of `loresigil/tests/`: **39 failed across exactly 8 files, and
every one of the 8 is named in §9.** No unlisted file went RED.

---

## RESIDUALS — every item, an individual verdict

| # | item | verdict |
|---|---|---|
| R1 | **Unwrap-gate spellings.** Measured 8: canonical → seen; `getattr(s,'get_secret_value')()`, `s._secret_value`, `vars(s)['_secret_value']`, bound-method alias `g = s.get_secret_value; g()`, `operator.attrgetter`, serializer, `model_dump` → **all invisible**. | **ACCEPTED for `_secret_value`/`vars`/`getattr`/`attrgetter`** — the gate states its threat model (honest developer, not hostile author) and pins the bound with a re-open trigger, so those verdicts follow mechanically. **FLAG the bound-method alias**: it is the public API in an honest spelling and is *not* named by the bound. One sentence in the docstring closes it. |
| R2 | **The laundering helper.** A single `def unwrap_for_client(s): return s.get_secret_value()` called from N sites needs **exactly ONE** allowlist entry. Measured: 4 uses (one of which *logs* the value, one *caches* it) → gate sees `['unwrap_for_client']`, 1 entry. | **REAL GATE HOLE, low likelihood, worth one line.** It looks like DRY, so an honest developer will write it. Recommend the docstring's known-bound paragraph name it: *an allowlisted wrapper launders every caller; entries must be leaf call sites.* |
| R3 | **`probe_embed.py` migration changes the deploy contract.** `_resolve_key` exits `_EXIT_BAD_USAGE`; `resolve_secret` raises `KeyError` → traceback, exit 1. `lore_deploy.py:1030` shells out and branches on exit codes. The `--env-file` remediation message is also lost. | **ESCALATE — unpinned and un-inventoried.** Recommend a pin that the migrated `main` still returns `_EXIT_BAD_USAGE` on an unset key. Nothing in the contract asserts this. |
| R4 | **`probe_embed.py` gains a `loremaster.config` import**, where it imports only stdlib today. `skills/` is outside `testpaths` *and* outside `scripts/typecheck.sh`. | **ESCALATE.** The gate reads `skills/` as text — it never *imports* it, so nothing proves `probe_embed.py` still runs after the migration. The author flagged the mypy half (§0.3); the *importability* half is unflagged. |
| R5 | **`skills/` outside `scripts/typecheck.sh`** — author's own residual. | **CONFIRMED, agree it is not a blocker.** Restating so it is not lost. |
| R6 | **`EmbeddingConfig.model_dump()` shape change** once `api_key: SecretStr` lands (`SecretStr('**********')` / `"**********"`). | **FLAG.** Not in the inventory, not pinned. Low risk; a one-line note in the adjudication table would close it. |
| R7 | **Real-then-blank duplicate-key dual** (`KEY=real` then `KEY=`): old → `"real"`, dotenv → `""` → fatal. | **AGREE WITH THE AUTHOR that it is open; DISAGREE that it is a preference.** It is a fail-open→fail-closed behaviour change on a credential path. Deserves a ruling line, not a pin chosen by taste. |
| R8 | **Inventory C10 over-claims** "byte-divergent" — the twins' *message strings* are identical; only source line-wrapping differs. | **COSMETIC.** Note it; no action. |
| R9 | **Inventory C4/C11 mutually contradictory** (see P6b verdict 2). | **FIX THE INVENTORY**, not the contract — the contract already resolves it correctly. |
| R10 | **Audit R2's "201 of 1,616 / 12.4%"** matches no scoping the author could construct (nor could I). | **AGREE with the author's handling** — reported as a discrepancy, pin regenerated live from the tree. Correct call. |
| R11 | **`test_the_module_prose_no_longer_teaches_a_mechanism_it_does_not_run`** is a phrase blocklist (author's own §12.5 objection). | **KEEP IT.** It fired on my REF build (`['high-entropy token']`) and forced me to fix the docstring — measured value, twice. A blocklist that catches the *actual* corpse is worth more than the nothing it replaces. Not a defect. |
| R12 | **Unrelated:** the base scrubber mangles adjacent structure — `Bearer <k>'}` redacts the closing quote/brace too (`(\S+)`). | **PRE-EXISTING, cosmetic**, out of packet scope. Raising per scope law; operator's call. |
| R13 | I ran `pytest` inside the `lore-pkt42` worktree twice (read-only ops; `.pytest_cache`/`__pycache__` only). | **DISCLOSED.** `git status` confirms **no tracked file changed** — only the contract author's own 6 files appear. |

---

## VERDICT

# CONTRACT INSUFFICIENT

This is a genuinely strong contract — among the strongest I have graded. Its ∀-matrices are real,
its positive controls are everywhere, its R8 pins killed my partial fix on the first attempt and
its label×separator matrix caught a trap in my *own* reference build. The R6 rider is discharged
with a receipt that is actually true, and the R3 mutation proof reproduces verbatim. I could not
break the R8 surface, the retired-symbol surface, or the recovered-data surface.

It is INSUFFICIENT for one reason, and it is the one the packet's own risk register names:
**A18's frame is too narrow.** The bound was written as *"an **unlabelled** secret in free text"*,
so every pin and every carrier was built around unlabelled text — and the credential that
actually exists as a bare `str` in this codebase is **labelled**, sitting in a **header map** at
the very sites the `UNWRAP_ALLOWLIST` blesses. A build satisfying this contract perfectly ships a
strict regression on the surface packet 42's own Scope OUT promises to keep protecting.

MP1 and MP2 route back to the contract author. MP1 additionally contains a **design fork** —
delimiter-tolerant labels vs. key-aware `_scrub_value` — that is the operator's to rule, not a
builder's to invent.
