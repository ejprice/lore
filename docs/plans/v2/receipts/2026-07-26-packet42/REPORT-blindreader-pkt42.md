# REPORT-blindreader-pkt42 — contract-blind diff read of packet 42

brief-base v7 read

- **state:** done-with-deviations
- **deviations:**
  - *Contamination (disclosed, unavoidable):* four `git grep` sweeps returned MATCHED LINES from
    withheld files — `docs/plans/v2/receipts/2026-07-26-packet42/REMOVED-BEHAVIOR-INVENTORY.md`
    (≈6 lines: the `B2`/`B6` rows and fragments of three others) and single matched lines from
    ~10 test modules. I opened none of those files. Full accounting + which findings could
    conceivably be tainted: §7.
  - Contract, spec, adversary reports and `REPORT-*.md` were never opened; no test file was read;
    no test suite was run.
- **Packages considered:** none — review-only, no mechanism specified. (I did READ an installed
  dependency's source to adjudicate a claim: `python_dotenv 1.2.2`,
  `.venv/lib/python3.14/site-packages/dotenv/{parser.py,main.py}` — `parse_unquoted_value`,
  `parse_value`, `_equal_sign`, `DotEnv._get_stream`, `dotenv_values`. That read is the whole
  basis of F3 and part of §1.)
- **decisions-needed:**
  1. F1 — is `Digest` staying in `_KNOWN_AUTH_SCHEMES`? As written it preserves the credential.
  2. F5/F6 — `CLAUDE.md` at `8dc1259` still says SEVEN sites, still teaches the hand-grep, and
     cites a symbol that does not exist. Was the doc half of the HEAD commit dropped?
  3. F14 — `loresigil.factory.EmbeddingConfig` is a breaking change and `loresigil` names
     `odoo-code` as a consumer. Is odoo-code pinned/vendored, or does it break?
  4. F4 — the deleted `.strip()` on the env-sourced Anthropic key: keep the byte-exact policy
     and accept an unrecognisable failure, or restore stripping for that path?
- **receipt pointers:** findings §3 (ranked) · removed-behaviour inventory §2 · input-fate tables
  §1 · prose-vs-logic §4 · six-month misreads §5 · files opened §6 · contamination §7.

*All claims dated: read at `8dc1259` (2026-07-27), base `6a21fb6`, tree
`/home/ejprice/PycharmProjects/lore-pkt42`, branch `pkt42-prevent-the-leak`.*

---

## 1. Fate of every input

### 1.1 `loremaster.config.resolve_secret(env_var_name, env_file=None)`

| input | fate at `6a21fb6` | fate at `8dc1259` |
|---|---|---|
| env set, real content | `SecretStr(value)`, byte-exact | same |
| env set, `""` | `KeyError` | `env_file=None` → `KeyError`; else consult file |
| env set, whitespace-only | `KeyError` | falls THROUGH to the file (R5), then `KeyError` |
| env unset | `KeyError` | consult file, then `KeyError` |
| `env_file` given, key absent from file | n/a | `.get()` → `None` → `KeyError` |
| `env_file` given, file missing | n/a | `dotenv` yields `StringIO("")` silently → `KeyError` ✅ |
| `env_file` given, file is a FIFO | n/a | `_is_file_or_fifo` accepts it → **blocks on read** (new hang; base's `Path.is_file()` was False for a FIFO) |
| `env_file` given, unreadable | n/a | `PermissionError` propagates (same as base's `read_text`) |
| `env_file` line `KEY` (no `=`) | n/a | dotenv yields `None` → `KeyError` ✅ |

Blank-value handling is now decided **once, at the end**, which is a real improvement: the old
`counting.load_api_key` returned `SecretStr("")` for a whitespace-only env var and shipped an
empty `x-api-key`.

### 1.2 `counting.load_api_key(env_file=DEFAULT_ENV_FILE)` — the consolidation's sharpest edges

| input | `6a21fb6` | `8dc1259` |
|---|---|---|
| env set, surrounded by whitespace/`\r`/`\n` | **`.strip()`ped** → clean key | **passed through raw** → invalid header (F4) |
| env whitespace-only | `SecretStr("")` — empty key on the wire | falls to file, else `RuntimeError` ✅ |
| file `export KEY=v` | **not matched** (`startswith("KEY=")`) → `RuntimeError` | matched (`_export` regex) ✅ widened |
| file has `KEY` twice | **first** match wins | dict → **last** wins |
| file `KEY=real` then `KEY=` | `real` | `""` → **`RuntimeError`** ⚠ |
| file `KEY="a\nb"` | literal `a\nb` (6 chars) | **real newline** (`decode_escapes`) ⚠ |
| file `KEY=v # note` | `v # note` | `v` (`re.sub(r"\s+#.*", …)`) ⚠ |
| file `KEY=  v  ` | `v` (`.strip()`) | `v` (`_equal_sign` + `.rstrip()`) — same |
| file `KEY='v'` / `KEY="v"` | `v` (`.strip("'\"")`) | `v` — same |

### 1.3 `_scrub_text` — every string reaching the redactor

| shape | `6a21fb6` | `8dc1259` |
|---|---|---|
| `Authorization: Bearer <tok>` | scheme word redacted, credential **left** (the R8 leak) | scheme kept, credential redacted ✅ **fixed** |
| `Authorization: Token <tok>` | same leak | fixed ✅ |
| `Authorization: Negotiate <tok> …tail` | `(\S+)` redacted, tail kept | whole tail **deleted** (F2) |
| `Authorization: Digest username="u", …, response="<hash>"` | `username="u",` redacted; `response` hash **caught by the entropy sweep** | `username="u",` redacted; **`response` hash survives** (F1) |
| `x-api-key: sk-ant-…` | redacted (`_ASSIGNMENT_RE`) | redacted ✅ unchanged |
| `{"authorization": "Token abc…"}` (JSON/dict repr) | entropy sweep redacted the token | **not redacted** — neither pattern matches a quoted key |
| `extra={"api_key": "<secret>"}` (label in the KEY, value alone in the string) | entropy sweep redacted it | **not redacted** — `_scrub_value` walks values, never keys |
| credential in a URL (`https://u:pw@host`, `?token=…` path segment) | entropy sweep redacted it | not redacted |
| UUID / git SHA / overlay-id path component | mangled (#227) | copied through ✅ **fixed** |
| function name, rendered source line | mangled | copied through ✅ **fixed** |
| `msg` with `%s` placeholders + `authorization=` | one `%s` eaten → `TypeError` in `getMessage()` | **every** `%s` after the label eaten → same `TypeError`, wider (F2c) |

Idempotency holds in every branch (`***REDACTED***` re-matches produce the same string) — the
`scrubbed_exception_text` claim checks out.

---

## 2. Behaviour present at `6a21fb6`, absent at `8dc1259`

Built by reading pre-images, not minus-lines. Verdicts are mine, contract-blind.

| # | removed behaviour | replacement | verdict |
|---|---|---|---|
| R1 | `_TOKEN_RE` + `_shannon_entropy_bits` unlabelled-token sweep | nothing | **gone**, declared in the module docstring. But the declaration says "an UNLABELLED credential in **free text**" — the loss also covers *labelled* structured shapes where the label and the value are in different strings (`extra={"api_key": …}`, JSON/dict header reprs) and credentials inside URLs. Under-stated. |
| R2 | `_is_safe_high_entropy_run` / `_is_absolute_path_component` / `_UUID_RE` / `_PATH_BLOB_CHARS` | nothing | correctly gone with R1 |
| R3 | `authorization` as an `_ASSIGNMENT_RE` label | `_AUTH_HEADER_RE` | **stronger** — same prefix, wider replacement |
| R4 | `_ASSIGNMENT_RE` preserving the rest of the line after an `authorization=` value | tail deleted when the scheme is unknown | **weaker on diagnosability**, undocumented at module level (F2) |
| R5 | `counting.load_api_key`'s `.strip()` on the env value | none | **gone**, deliberate per docstring, operationally sharp (F4) |
| R6 | `counting.load_api_key`'s hand parser (`startswith`, first-match, `.strip("'\"")`) | `dotenv_values(..., interpolate=False)` | mostly stronger; four fate changes, §1.2 |
| R7 | `loresigil.factory._resolve_api_key` (env read inside the library) | composition-root resolution | **preserved-with-strengthening** — the "never build a keyless embedder" property now fires earlier and on every construction path |
| R8 | `MissingApiKeyError` (a `RuntimeError` subclass) | `KeyError` from `resolve_secret` | **type + message both changed** (F12); breaking for out-of-tree consumers (F14) |
| R9 | `EmbeddingConfig.api_key_env` field | `api_key: SecretStr` | breaking, `version` unchanged (F14) |
| R10 | `_resolve_api_key` accepting a whitespace-only key | rejected by the validator | **old bug, deliberately not re-pinned** ✅ |
| R11 | `AsyncClaudeTokenCounter._headers` / `ClaudeTokenCounter._headers` instance attribute | per-request `build_auth_headers` | private; strictly better (no header surface on a shared client) |
| R12 | `token_survey.ANTHROPIC_VERSION` / `ANTHROPIC_API_KEY_ENV` | imported from `counting` | verified: `git grep` finds no remaining consumer outside tests/docs |
| R13 | `probe_embed._resolve_key`'s `if not key` | `if not key or not key.strip()` | strengthened; a whitespace-only value now `exit 4` instead of probing with `" "` — a deploy-path behaviour change |
| R14 | `to_loresigil_config` being PURE (no IO, cannot raise) | now reads `os.environ` | **gone** (F13); no production caller is harmed today |

---

## 3. Findings, most severe first

Each carries my confidence and, where relevant, the likelihood of the triggering shape actually
occurring in this deployment.

### F1 — `Digest` is allowlisted, and for `Digest` the redactor deletes the username and keeps the credential
`logging_setup._KNOWN_AUTH_SCHEMES` includes `Digest`. `_AUTH_HEADER_RE` redacts group 4 — **the
first whitespace-delimited token** after the scheme — and copies group 5 (`[^\n]*`, the rest of the
line) through verbatim. An RFC 7616 `Digest` header value is by definition a comma-separated
auth-param list:

```
Authorization: Digest username="u", realm="r", nonce="...", uri="/x", response="<32-hex hash>"
→ Authorization: Digest ***REDACTED*** realm="r", nonce="...", uri="/x", response="<32-hex hash>"
```

`username="u",` is destroyed; `response=` — the value that actually authenticates — is logged in
the clear. Nothing downstream catches it: `_ASSIGNMENT_RE`'s labels are
`api_key|apikey|token|secret|password`, and `response`/`nonce`/`cnonce` are none of them. At
`6a21fb6` the entropy sweep redacted it (32 hex chars ≥ the 24 minimum, entropy ≈ 3.9 ≥ 3.5, not
slash-adjacent).

This is the R8 leak — *"the non-secret word redacted and the credential left in the log"*, quoted
verbatim in the comment above `_AUTH_HEADER_RE` as the reason the two patterns were split —
reintroduced for the one allowlisted scheme whose value is not a single token. It is the quantifier
failure CLAUDE.md names: the "one token after the scheme" property was derived on `Bearer` and
stated over the whole allowlist. Any future multi-token scheme added to the tuple inherits it.

*Confidence: high (mechanical). Likelihood in this deployment: low — lore's clients are Bearer /
`x-api-key`. But the allowlist entry was chosen by this change, and nothing in code or comment
records the constraint it assumes.*

### F2 — the unknown-scheme branch silently deletes the rest of the line, and the served prose says the opposite
`_redact_auth_header` returns `f"{label}{REDACTED}"` when the scheme is unrecognised — dropping
group 5 entirely. Group 4 (`first_token`) is bound and **never used in either branch**, which is
part of why the drop is easy to miss.

Three consequences, none stated where a reader will look:

a. **Ordinary prose is destroyed.** `authorization: denied user=bob reason=policy` →
   `authorization: ***REDACTED***`. Everything after the separator is gone.
b. **One line of a scrubbed traceback can be truncated** (`[^\n]*` correctly confines the blast
   radius to a line, which is the saving grace).
c. **`%`-style logging can now lose every placeholder on the line.** `RedactingFilter.filter`
   mutates `record.msg` *before* `getMessage()` interpolates. A msg such as
   `"authorization=%s status=%s"` becomes `"authorization=***REDACTED***"` — zero placeholders,
   two args — and `getMessage()` raises `TypeError: not all arguments converted during string
   formatting`, which `logging` swallows via `handleError` and the record is **dropped**. The
   hazard pre-existed (any pattern eating a `%s` did it) but base ate ONE token; HEAD eats every
   placeholder to end of line. Exposure is low today because lore's own call sites use
   `logger.x("event", extra={...})` and third-party loggers are outside `LORE_NAMESPACES`.

The prose gap is the reportable part. `_scrub_text`'s docstring: *"Every byte the three patterns do
not match is COPIED THROUGH … paths, identifiers, git SHAs, UUIDs and rendered source lines reach
the log exactly as they were written."* The module docstring describes the filter only as replacing
secrets *"to `REDACTED`"*. Only `_redact_auth_header`'s own docstring — the one a reader reaches
last — says *"everything after the separator goes when it is not [recognised]"*.

*Suggested fix, non-binding: terminate the unknown-scheme match at the first whitespace run rather
than at the newline, or say the destruction out loud in the module docstring's filter bullet.*

*Confidence: high (mechanical).*

### F3 — "byte-exact" is false on the branch this change added
`resolve_secret`'s docstring: *"The value is never stripped or otherwise mutated — a secret whose
real content happens to include leading/trailing whitespace passes through byte-exact."* That
sentence sits after both the env paragraph and the `env_file` paragraph, so it reads as covering
both. Ruling R12 correctly found **one** `dotenv_values` mutation (interpolation) and disabled it.
Reading the installed parser (`python_dotenv 1.2.2`) there are three more on that branch:

| mutation | source | effect |
|---|---|---|
| `_equal_sign = (=[^\S\r\n]*)` | `parser.py::parse_binding` | leading horizontal whitespace eaten |
| `re.sub(r"\s+#.*", "", part).rstrip()` | `parser.py::parse_unquoted_value` | trailing whitespace stripped **and** the value truncated at the first whitespace-preceded `#` |
| `decode_escapes(...)` on quoted values | `parser.py::parse_value` | `\\ \' \" \a \b \f \n \r \t \v` are **decoded** — `KEY="a\nb"` yields a real newline where the deleted parser yielded a literal backslash-n |

So byte-exactness holds on the ENV branch only. Anthropic keys (`sk-ant-api03-<base64url>`) contain
none of these characters, so today's exposure is nil — but the sentence is a served claim about a
security property, and the packet's own R12 shows the mutation audit was attempted and stopped one
step short.

*Confidence: high — read from the installed dependency's source, not inferred.*

### F4 — the ENV branch lost the `.strip()`, and the resulting failure names nothing
`6a21fb6`'s `counting.load_api_key` did `SecretStr(from_env.strip())`. `resolve_secret` does not
strip. An `ANTHROPIC_API_KEY` exported with a trailing newline, space or `\r` — `$(cat key.txt)`, a
CRLF-sourced env file, a paste — used to work. It now goes verbatim into `x-api-key`; httpx/h11
reject a header value containing `\r`/`\n`, so `AsyncClaudeTokenCounter.count` sees an
`httpx.HTTPError`, burns the whole retry ladder, and ends in
`RuntimeError: count_tokens exhausted retries (transport:LocalProtocolError)` — a message that
mentions neither the key nor whitespace. `resolve_secret`'s docstring shows the choice was
conscious ("three resolvers disagreed … about stripping"), so this is a fate change to rule on
rather than an obvious defect; the operator-facing consequence is what I am surfacing.

*Confidence: high on the fate change; medium on the exact httpx failure mode (not executed).*

### F5 — `scripts/registration_sites.py` is referenced by nothing, and the law still teaches the tool it replaces
`git grep -l registration_sites 8dc1259` returns exactly one path: the script itself. No test, no
gate, no `typecheck.sh` entry, no `CLAUDE.md` pointer. `scripts` **is** in `testpaths`, so a
`scripts/test_registration_sites.py` would have run — `ls scripts/` shows none exists.

Meanwhile `CLAUDE.md` at `8dc1259`:

- still reads **"THE SEVEN PLACES A NEW WORKSPACE MEMBER MUST BE REGISTERED"** with seven entries;
- still says the list *"has been wrong TWICE"* — the script's own docstring says **three** times and
  names two more ∀ scanners that were narrower than the workspace;
- still instructs *"Do not trust this list. **DERIVE it:** `grep -rn 'lorescribe' --include='*.py'
  …`"* — a **single-member** grep, strictly weaker than the tool committed in the same commit, and
  structurally blind to any site that names `loremaster`+`loresigil` but not `lorescribe`.

The HEAD commit message is *"registration sites are DERIVED, not listed — plus sites 8 and 9"*. The
law carries neither the derivation nor sites 8 and 9. This is the repo's own line — *a guard nobody
runs is a hope with a filename, and worse than no guard, because its presence is read as coverage* —
landing on the instrument built to stop the list from being wrong a fourth time.

*Confidence: high (verified against the commit object, not the working tree).*

### F6 — `CLAUDE.md` entry 6 cites a symbol that does not exist in the file it names
> *"`conformance_provenance.py::EXPECTED_MEMBERS` proves it arrived."*

The production symbol in `skills/lore-deploy/scripts/conformance_provenance.py` is
**`WORKSPACE_MEMBERS`**. `EXPECTED_MEMBERS` exists only in the sibling *test* module (surfaced by
grep; file not opened). Packet 42 edited that exact constant — adding `lorerunes` and a nine-line
warning above it — and left the law pointing at a name that is not there.

*Confidence: high.*

### F7 — `_MIN_MEMBERS_FOR_A_SITE = 3`, and its own comment justifies 2
```python
#: A site must name at least this many DISTINCT members … Two is the smallest number that
#: distinguishes "enumerates" from "imports one thing".
_MIN_MEMBERS_FOR_A_SITE = 3
```
The module docstring separately (and correctly) explains 3: *"two co-occurring names is ordinary
prose and flagging it produced 82 hits nobody would read."* The constant's own comment contradicts
its value. A reader tuning this will trust whichever they read first.

*Confidence: high.*

### F8 — `_is_a_module_reference` drops the prose enumerations the module docstring promises to keep
The docstring: *"Prose hits are NOT filtered out, deliberately: a docstring or a comment listing
three of four members is a served-English defect this packet was bitten by twice."*

But the predicate drops a mention when **every** occurrence of the name on that line is followed by
`.`. Two consequences:

- A sentence that **ends on a member name** loses that member:
  *"…imported by lorescribe, loresigil and loremaster."* → `loremaster` dropped → 2 members named →
  below the threshold of 3 → **the site is invisible**.
- Any **dotted** enumeration is invisible wholesale: a docstring listing `lorerunes.blankness`,
  `loresigil.factory`, `loremaster.config` reports zero members.

The instrument is keyed on a shape and defeated by the next shape — in the file whose own docstring
lectures about exactly that (*"an enumeration of places to look is the artifact this repo has the
most receipts against"*).

Related, smaller: `find_sites` clusters **transitively** (the window is measured from the previous
mention, not from `cluster_start`), so the documented false positive — *"a construct wider than the
window splits into two clusters"* — is imprecise. It is the GAP that splits, not the width.

*Confidence: high on the end-of-sentence case (mechanical); high on the dotted case.*

### F9 — `lorerunes` is the one member outside `LORE_NAMESPACES`, unannotated, and it is the member everything imports
`logging_setup.LORE_NAMESPACES` is still `("loremaster", "loresigil", "lorescribe")`. The subset is
correct today — `lorerunes` logs nothing — and `registration_sites.py`'s own output text says
exactly what should have happened: *"A deliberate subset should say so **where it is written**, so
the next run of this script is read rather than re-derived."* Nothing is written at
`LORE_NAMESPACES`.

The consequence is worth writing down regardless of the annotation: the day anyone adds
`logger = logging.getLogger(__name__)` to the package **every other member imports**, those records
propagate to the root logger with **no `RedactingFilter`** and no lore formatter. The shared home
is the one place the secret backstop does not reach. That is the same hazard `CLAUDE.md` already
states for secret *resolution* ("a shared home makes the wrong thing newly possible"), one layer up.

*Confidence: high on the mechanism; the trigger is a future edit.*

### F10 — the R14 exemption argues against the wrong candidate, and the file holds two un-ledgered copies of the very policy this packet centralised
`probe_embed._resolve_key` justifies staying a duplicate with: *"Importing `loremaster.config` here
would trade a clean `exit 4` for a `KeyError` traceback read as `exit 1`."* But the thing duplicated
at HEAD is the **blankness predicate** (`if not key or not key.strip()`), whose shared home
`lorerunes.is_blank` is stdlib-only, raises nothing, and returns a bool — so neither stated reason
covers it. The actual reason (`lorerunes` is a *workspace member*, and this script deliberately runs
under an interpreter with no workspace installed) is nowhere written, and it is precisely the reason
a reader who knows `lorerunes` exists will come looking for. The stated RE-OPEN TRIGGER — *"the day
this script runs under `_loremaster_python()`"* — is the right trigger for the unwritten reason.

Two consequences:
- **The "prove sharing by mutation" claim has a known, unstated hole:** changing `is_blank` will not
  redden `probe_embed`.
- Same file hand-rolls `{"Authorization": f"Bearer {key}"}` **twice** (`_poll_health`,
  `_observe_dim`) — two more copies of the exact policy `build_auth_headers` was created to
  centralise, neither ledgered, both holding the credential as a bare `str`. Ruling R9 brought
  `skills` under `scripts/typecheck.sh`, but there is no `SecretStr` in this file for the type gate
  to bite on, so the new coverage does not reach the shape the packet is about.

*Confidence: high.*

### F11 — two different functions named `build_auth_headers`, type-identical, semantically different
| symbol | returns |
|---|---|
| `loremaster.calibration.counting.build_auth_headers` | `{x-api-key, anthropic-version, content-type}` |
| `loresigil.voyage_http.build_auth_headers` | `{Authorization: Bearer …}` |

Both take `SecretStr`, both return `dict[str, str]`. mypy cannot distinguish them at a call site.
`scripts/token_survey.py` imports the loremaster one; `loresigil/tei.py` imports the loresigil one.
An engineer who autocompletes the wrong import gets a **type-correct, silently unauthenticated**
request against the other service — a 401 with no type error and no lint. The `voyage_http`
docstring defends the duplication (*"the shared thing is the TYPE, not an implementation — two typed
seams are not a DRY violation when what must agree is a signature"*), which is a fair argument; but
identical signatures are exactly what makes the identical **name** dangerous, and the name was not
made distinct.

*Confidence: high on the mechanism; it is a foot-gun, not a live defect.*

### F12 — the embedding-credential failure lost its field name, inconsistently with its two siblings in this same packet
Deleted: `MissingApiKeyError("embedding api_key_env {name!r} is unset or empty in the
environment")` — names the **config field**. HEAD raises `KeyError("Required secret environment
variable {name!r} is unset, empty, or whitespace-only; export it before starting lore.")` — names
the variable, not that it is the *embedding* key.

In the same packet the identical `KeyError` is translated twice, precisely to add that context:
`load_config` → `ValueError` naming `anthropic.api_key_env`; `counting.load_api_key` → `RuntimeError`
naming the env file. `to_loresigil_config` got no translation, and its docstring's *"The message
names the variable"* is technically true and diagnostically weaker than what it replaced. The
exception base class also moved from `RuntimeError` to `KeyError`, and `str(KeyError(msg))` renders
the message wrapped in quotes.

*Confidence: high.*

### F13 — `to_loresigil_config` stopped being pure, and its module still advertises purity
At `6a21fb6` it was a total function on config. At HEAD it reads `os.environ` and can raise. Every
production caller is a composition root (`index/cli.py::_run`, `scout.py::_run_scout`,
`server.py::build_app_context`) — verified — so nothing breaks today. But `embedding.py`'s module
docstring still says *"This module only carries the config fields across faithfully"* and *"THIN:
config → loresigil.make_embedder()"*, and the function's name still reads as a translation. Anything
wanting to inspect/validate/render the translation without an environment (a config dump, a dry-run,
a doc generator, a future `lore_index()` render of the embedding block) now cannot.

*Confidence: high.*

### F14 — a breaking API change to a package whose own docstring names an out-of-tree consumer
`loresigil.factory.EmbeddingConfig`: `api_key_env: str` → `api_key: SecretStr` (required, model is
`extra="forbid"`), and `MissingApiKeyError` deleted. `loresigil/pyproject.toml` still says
`version = "0.1.0"`. The module's first paragraph: *"The single seam through which a consumer (lore,
**odoo-code**) picks an embedding backend by config only."*

Any out-of-tree checkout constructing `EmbeddingConfig(api_key_env=…)` now takes a `ValidationError`
on **both** counts (extra key forbidden, required field missing), and any `except
MissingApiKeyError` becomes an `ImportError`. In-repo this is clean — I verified every production
construction site goes through `factory.make_embedder` and both direct construction sites
(`loremaster.embedding.to_loresigil_config`, `scripts/search_score_survey._make_embedder`) were
updated. This finding is entirely about the named external consumer, and it is a question, not an
accusation: **is `odoo-code` pinned, vendored, or on this workspace?**

*Confidence: high on the mechanics; the impact depends on a fact I cannot see from this tree.*

---

## 4. Residuals — smaller, still worth a line each

1. **`scripts/` stayed outside `typecheck.sh` while `skills` was added.** `search_score_survey.py`'s
   own comment calls `_make_embedder` *"one of only two production construction sites of that model
   — and the one no type gate can see, because `scripts/` is not a typecheck member."* So the
   packet's central instrument (*"a bare `str` is a mypy error at every call site"*) does not hold at
   a site the packet itself labels a composition root. Compounding: pydantic **coerces** `str →
   SecretStr`, so `EmbeddingConfig(api_key="raw-string")` is accepted silently there — the model
   boundary is not a type gate, only the `build_auth_headers` signature is.
2. **`comms_consumer_eval`'s precheck is now stricter than the resolver it gates.** It calls
   `resolve_secret(ANTHROPIC_API_KEY_ENV)` with **no** `env_file`, while the counter it guards uses
   `load_api_key`, which **does** consult `~/docker/mcp/.env`. The script can therefore refuse a run
   the counter could have completed. This follows directly from R3 (one `env_file` call site) and is
   unremarked at the call site. Net-positive in the other direction: a whitespace-only
   `ANTHROPIC_API_KEY` used to pass the old truthiness check and then send an **empty** `x-api-key`;
   it now exits cleanly with `EXIT_NO_KEY`.
3. **`counting.py`'s module docstring contradicts itself about which file is the reference.**
   Paragraph 1 still calls `scripts/token_survey.py` *"the READ-ONLY shape reference"*; paragraph 2
   says token_survey now imports **from** counting. A reader asking *"where do I change the wire
   shape?"* gets both answers.
4. **`token_survey.py` now imports `loremaster` at module scope**, while its sibling
   `comms_consumer_eval.py` states the opposite as *"this script's standing idiom for every
   loremaster import"* (lazy, so a half-built workspace is one loud failure at point of use). The
   survey now needs the full workspace — including `dotenv` and `yaml` via `loremaster.config` — to
   `import`, not to run.
5. **`_redact_auth_header` binds `first_token` and never uses it** in either branch. Cosmetic, but
   it is the group the function is nominally about, and its unusedness is what makes F2's tail-drop
   easy to read past.
6. **`snapshot_gc.main` catches `KeyError` around the entire `asyncio.run(run_gc(args))`** and prints
   it as a credential error. Pre-existing (not in this diff), but the surface widened: at HEAD both
   `resolve_secret` and `resolve_config_value` raise `KeyError` there, and so does any unrelated dict
   lookup anywhere under `run_gc`.
7. **Working tree at review time is not clean:** `loremaster/tests/_surreal_harness.py` is modified
   and nine untracked `REPORT-*.md` sit at the repo root. Repo law requires the root clear of
   `REPORT-*.md` (archived under `docs/plans/v2/receipts/<date>-<packet>/`, never deleted) before an
   image build. Noted from `git status` only; none were opened.

---

## 5. What a careful engineer would misread in six months

1. **"The redactor never destroys non-secret data."** Two of the three places that describe it say
   so; the third contradicts them (F2).
2. **"`resolve_secret` is byte-exact."** True of the env branch, false of the file branch (F3).
3. **"The registration list is derived now."** `CLAUDE.md` says SEVEN, says "wrong twice", and hands
   you a single-member `grep`. The derived tool exists, is unreferenced, and is not run (F5).
4. **"`conformance_provenance.py::EXPECTED_MEMBERS`."** They will grep that file, find nothing, and
   have to reconstruct which of two similarly-named constants the law meant (F6).
5. **"`build_auth_headers` is the shared auth seam."** There are two, type-identical, for different
   services (F11).
6. **"`to_loresigil_config` is a pure translation."** Its module says THIN and faithful; it now
   performs IO and raises (F13).
7. **"`lorerunes` is covered by everything, it's a workspace member."** It is outside
   `LORE_NAMESPACES`, so it is outside the secret backstop and outside the structured sinks (F9).
8. **"`probe_embed` duplicates the resolver because it can't import loremaster."** That reasoning
   does not explain why it doesn't import `lorerunes`, which is stdlib-only (F10).

---

## 6. Receipt — every file I opened

**Read in full (Read tool):**
- `~/.claude/orchestration/brief-base.md`
- `/home/ejprice/PycharmProjects/lore-pkt42/CLAUDE.md`
- `loremaster/loremaster/logging_setup.py` (HEAD)
- `loremaster/loremaster/calibration/counting.py` (HEAD)
- `loresigil/loresigil/factory.py` (HEAD)
- `/tmp/pkt42_prod.diff` — the production-only diff produced by the brief's own command, with
  `uv.lock` additionally excluded

**Read in part (Bash: `sed`/`grep`/`cat`/`git show`):**
- `skills/lore-deploy/scripts/probe_embed.py` (HEAD, lines 1–200)
- `loremaster/loremaster/embedding.py` (HEAD, full via `cat`)
- `loremaster/loremaster/config.py` (HEAD, lines 700–825)
- `loremaster/loremaster/server.py` (HEAD, lines 1590–1615, 7025–7045)
- `loremaster/loremaster/scout.py` (HEAD, lines 1008–1024)
- `loremaster/loremaster/index/cli.py` (HEAD, grep only)
- `loremaster/loremaster/auth.py` (HEAD, grep only)
- `scripts/token_survey.py` (HEAD, lines 1–60 + greps)
- `scripts/snapshot_gc.py` (HEAD, lines 425–450)
- `scripts/typecheck.sh` (HEAD, full)
- `pyproject.toml` (HEAD, full) · `loresigil/pyproject.toml`, `lorescribe/pyproject.toml`,
  `loremaster/pyproject.toml` (version lines only)
- `git show 6a21fb6:loremaster/loremaster/logging_setup.py` (lines 100–125, 300–330)
- `git show 8dc1259:CLAUDE.md` (lines 355–425 + greps)
- `.venv/lib/python3.14/site-packages/dotenv/parser.py` (lines 1–200)
- `.venv/lib/python3.14/site-packages/dotenv/main.py` (lines 30–140 + `dotenv_values`)

**Directory listings only:** `lorerunes/` (`find`), `scripts/` (`ls`).

**Not opened, per the brief:** any test file · `docs/plans/v2/42-*.md` · anything under
`docs/plans/v2/receipts/2026-07-26-packet42/` · any `REPORT-*.md`. **No test suite was run.**

---

## 7. Contamination disclosure

Four repo-wide `git grep` calls returned **matched lines** from withheld files before I tightened
the pathspecs. I did not open any of them. Precisely what I saw:

1. **`docs/plans/v2/receipts/2026-07-26-packet42/REMOVED-BEHAVIOR-INVENTORY.md`** — six matched
   lines: the `B2` and `B6` table rows (about `_resolve_api_key`'s `if not key` and
   `MissingApiKeyError`'s public importability), and fragments of three others mentioning
   `to_loresigil_config`. This told me the inventory uses `B*`/`C*` item ids and that
   `MissingApiKeyError` is *"caught nowhere in production; 4 test files import it"*.
2. **~10 test modules** — one matched line each (`test_embedding.py`, `test_factory.py`,
   `test_factory_secret_resolution.py`, `test_config.py`, `test_conformance_provenance.py`, and
   others), plus their file names in an `ls`.

Where this could have shaped a finding, I say so explicitly:

- **F14 is NOT derived from the inventory fragment.** The fragment I saw asserts
  `MissingApiKeyError` is caught nowhere *in production* — an in-repo claim I independently
  confirmed. F14 is about an **out-of-tree** consumer, and its sole basis is
  `loresigil/loresigil/factory.py`'s own module docstring naming `odoo-code`.
- **R8/R10 in §2** (the exception type change; the whitespace-only key being an old bug not
  re-pinned) overlap with what those fragments say. I reached both from the pre-images
  (`git show 6a21fb6:loresigil/loresigil/factory.py` via the diff) — but I cannot claim the overlap
  was uninfluenced, so treat those two rows as corroboration, not independent enumeration.
- Everything in §3 (F1–F14) was derived from production code, pre-images, `CLAUDE.md`, commit
  objects and the installed `python-dotenv` source. None of it appeared in the fragments I saw.

Some test file *names* also reach me legitimately through the production diff itself
(`test_secret_leak_vectors.py` in `logging_setup.py`'s docstring;
`test_secret_typing.py::TestTheInImageGuardCoversEveryWorkspaceMember` in
`conformance_provenance.py`; `test_calibration_counting.py::TestRequestShapeParity` in
`counting.py` and `token_survey.py`). I read none of them, and I deliberately did not use them as
a map of what the contract covers.
