# REPORT-builder-pkt42-1-pass4 — packet 42, builder pass 4 (R33–R40, the deploy blockers)

brief-base v7 read

Base: **`640b31b`**. Measured **2026-07-27** in `/home/ejprice/PycharmProjects/lore-pkt42`, branch
`pkt42-prevent-the-leak`. Nothing staged, nothing committed. Prior: `REPORT-builder-pkt42-1.md`,
`-pass2.md`, `-pass3.md` — cited, not superseded.

- **state:** done — **all four leaks closed, both 🟠 items fixed, R40 closed as a side effect.**
- **gate:** **your probe: 7/7 redact, 0 leaks** (§1, quoted verbatim) · scoped **0 failed / 417
  passed** · `./scripts/typecheck.sh` five iterations **all OK** · `uv run ruff check .` **All checks
  passed!** · **full suite 1 failed / 7403 passed** — **better than the 2-failed target**; the one
  survivor is the packet-03b/11i doc-banner debt reproduced at `76f1d9f` in pass-1 §7.8.
- **deviations:**
  1. **R33's fix needed more than removing `Digest`.** The contract author's new pin iterates
     **every** allowlisted scheme against a multi-token value — so `Bearer` had the same hole.
     Fixed receiver-blind, by RFC 7235's own grammar rather than by a scheme list (§2.1).
  2. **R37's fix needed more than the `\b` boundary.** `SURREAL_PASS` is not an instance of the
     mechanism R37 names — `PASS` is not `password`, so **no boundary change could ever have matched
     it** (§3.1). Two populations in one ruling; I fixed both.
  3. **I renamed `_KNOWN_AUTH_SCHEMES` → `_KNOWN_SCHEMES` and changed its type** to satisfy a new
     contract pin that binds both (§2.2). Production-shape change made to fit a test, disclosed.
  4. **I did not touch any test file.** Three files under `loremaster/tests/` show as modified —
     the contract author's parallel edits, which landed *during* my run (§6).
- **Packages considered: none — no mechanism specified.** Every change is inside patterns and a
  filter this repo already owns; the one thing that looked like a mechanism (parsing an
  `Authorization` auth-param list) is four lines of RFC 7235 grammar, and pulling a header-parsing
  library into the logging backstop would add a dependency to the code that runs when everything
  else has already failed.
- **decisions-needed (2, neither blocking):** ① §3.2 — the compound pattern redacts `cache_key=`
  and `sort_key=` as the price of catching `private_key=`; that trade is stated in the code and is
  yours to narrow. ② §5 — R40 is **closed**, but httpx's underlying asymmetry is still real and
  wants a bound pinned with R20's trigger; that pin is the contract author's.
- **receipt pointers:** §1 your probe · §2 R33+R34 · §3 R37 · §4 R38/R39 · §5 R40 · §6 the parallel
  edits · §7 gates.

---

## 1. Your probe, re-run — **7/7 redact, 0 leaks**

```
redacted   SURREAL_PASS=hunter2-the-password-nobody-should-see      -> SURREAL_PASS=***REDACTED***
redacted   client_secret=hunter2-the-password-nobody-should-see     -> client_secret=***REDACTED***
redacted   client-secret=hunter2-the-password-nobody-should-see     -> client-secret=***REDACTED***
redacted   {'api_key': 'hunter2-the-password-nobody-should-see'}    -> {'api_key': ***REDACTED***
redacted   {'Authorization': 'Basic hunter2-the-password-…'}        -> {'Authorization': 'Basic ***REDACTED***
redacted   Authorization: Basic hunter2-the-password-nobody-…       -> Authorization: Basic ***REDACTED***
redacted   Authorization: Digest username="u", realm="r", …         -> Authorization: ***REDACTED***

LEAKS REMAINING: 0
```

And through `_scrub_value`, which is the seam the `extra=` path actually takes:

```
{'api_key': '<v>'}              -> {'api_key': '***REDACTED***'}
{'Authorization': 'Basic <v>'}  -> {'Authorization': '***REDACTED***'}
```

**The catch-all was not reinstated.** Every fix is inside the labelled patterns and the container
walk. `_scrub_text` still runs four structural passes and copies every unmatched byte through.

---

## 2. R33 + R34 — the regression we caused, and it was wider than `Digest`

### 2.1 ⚠ Removing `Digest` was NOT sufficient, and the pin that proved it is the contract author's

I removed `Digest` as ruled. Then the new pin
`test_every_allowlisted_scheme_takes_a_SINGLE_TOKEN_value` went RED **on `Bearer`**:

```
scheme 'Bearer' is allowlisted for scheme-preservation, but its credential is not a single
token — the tail survives redaction:
  'Authorization: Bearer ***REDACTED*** realm="lore", response="deadbeefcafef00d1234"'
```

**The ruling diagnosed the instance; the pin has the property.** `Digest` was the scheme that
*happens* to send an auth-param list, but nothing stops one arriving after `Bearer` — and the leak
is identical. Removing one name from a list would have left the mechanism intact, which is this
repo's most-receipted failure shape.

So the fix is **receiver-blind, from RFC 7235's own grammar** rather than from a scheme list:

```python
def _auth_value_length(text: str) -> int:
    """…a token ending in a comma means the parameter list continues."""
    end = 0
    for token in _AUTH_VALUE_TOKEN_RE.finditer(text):
        end = token.end()
        if not token.group(1).endswith(","):
            break
    return end
```

**Why this rule and not a longer allowlist:** it cannot go stale. A scheme allowlist is wrong the
day someone adds `Negotiate`; "the auth-param list continues after a comma" is true of the syntax
itself. And it is exactly what keeps the rest of a log LINE outside the redaction — the pre-existing
`curl -H 'Authorization: Bearer <k>' https://api/x` pin still passes, because that first token does
**not** end in a comma, so consumption stops there and `https://api/x` survives.

`Digest` is still removed (its value is not one token, so preserving its scheme buys nothing), and
the single-token property is now enforced for whatever is left.

### 2.2 ⚠ Deviation — I renamed a production symbol to satisfy a pin

The new pin reads `re.split(r"\|", logging_setup._KNOWN_SCHEMES)`: it binds both the **name**
`_KNOWN_SCHEMES` and the **type** (a `|`-joined string, not the tuple I shipped in pass 1). I
renamed and reshaped rather than route it back, because nothing else referenced the old name and the
string form removes a `join` at the point of use — one representation instead of a tuple plus its
rendering. **It is still a production shape changed to fit a test, so it is on the record as one.**

### 2.3 R34 — the `%`-interpolation defect was real, and it MADE LOGGING RAISE

Measured before the fix:

```python
logger.warning("authorization: denied for %s after %s attempts", "bob", 3)
  msg after filter: 'authorization: ***REDACTED***'   args: ('bob', 3)
  getMessage() RAISED: TypeError not all arguments converted during string formatting
```

`RedactingFilter.filter` scrubbed `record.msg` while `args` still waited, and the unknown-scheme
branch discarded the placeholders with the rest of the line. **A logging backstop that can raise
inside logging is worse than the leak it guards.** Fixed by rendering first:

```python
if record.args:
    record.msg = _scrub_text(record.getMessage())
    record.args = ()
```

which also scrubs the arguments by construction — they are in the text. Verified:

```
OK   'authorization: ***REDACTED***'
OK   'embed.probe.unreachable presented=pa-KEY'      # %-style, unlabelled: bound preserved
OK   'count 4 for alice'                             # %(name)s dict-args form
```

The pre-render is observable to a second handler, so it is documented in `RedactingFilter`'s
docstring beside the existing `exc_text` pre-render, for the same reason.

**On R34's other half — the dropped tail — I adjudicated KEEP.** The redaction is right and it is
now load-bearing: it is the branch `Digest` falls into. What was missing is that nothing said so, so
`_redact_auth_header`'s docstring now states the collateral in terms (`authorization: denied
user=bob reason=policy` → `authorization: ***REDACTED***`), and the discarded groups are named with
`del first_token, rest_of_line` — you were right that a bound-and-unused name is part of why the
drop was invisible.

---

## 3. R37 — the underscore compounds, and a second defect inside the same ruling

### 3.1 ⚠ `SURREAL_PASS` is not an instance of the mechanism R37 names

R37 lists `SURREAL_PASS` under the `\b` defect. **Measured: it is not.** The label alternation is
`api[_-]?key|apikey|token|secret|password` — **`PASS` is not `password`**, so no boundary change
could ever have matched it. Two populations in one ruling, which is this packet's signature defect
appearing inside a ruling written to fix it.

So the compound pattern carries its own label set — `key` and `pass` added — which are far too broad
as bare words and precise after a `_` or `-`:

```python
_COMPOUND_ASSIGNMENT_RE = re.compile(
    r"(?i)(?<=[_-])(api[_-]?key|apikey|key|token|secret|password|pass)"
    r"(['\"]?\s*[=:]\s*)['\"]?(\S+)"
)
```

`key` earns its place independently: `secret_key=` and `private_key=` are **not** reachable by
fixing the boundary either — in `secret_key` the label `secret` is at the *start*, and the separator
check fails on `_key=`. The tail label is the only thing that matches them.

**It is a second pattern, not a widened one**, for the same reason R8 split the auth header out: the
frozen `test_the_core_label_set_is_derived_from_the_pattern` reads the alternation out of
`_ASSIGNMENT_RE.pattern` with `\b\(([^)]+)\)\b`, and a lookbehind or an inner group would break that
parse. Two patterns, one `_scrub_text`, no behavioural overlap.

### 3.2 The trade, stated in the code rather than discovered later

`cache_key=abc` and `sort_key=name` now redact. That is a real diagnostic cost, accepted
deliberately: **a leaked `private_key` is not recoverable and a lost `cache_key` is.** It is written
into the constant's comment as a design decision so narrowing it is a decision too. **Yours to
narrow if you disagree** — I would not, but I am not the one who reads these logs.

---

## 4. R38 + R39 — one edit, as the audit said

**The root is one sentence: the label and the value never adjoined.** Two shapes, one cause.

**R38 — the mapping key IS the label.** `_scrub_value` walked a dict by scrubbing each key and each
value *independently*, so `{"api_key": "sk-…"}` handed the value to `_scrub_text` as a bare string
with no label anywhere near it. The key is now passed down as context:

```python
def _names_a_secret(key: str) -> bool:
    return _LABEL_PROBE not in _scrub_text(f"{key}={_LABEL_PROBE}")
```

**That asks the patterns rather than re-stating them**, which is the part I care about: the label
set keeps exactly one definition, so a label added or removed changes mapping behaviour in the same
edit. A second list here would be a second answer to one question — which is precisely how
`client_secret` and `Authorization` came to disagree with themselves.

**R39 — the quoted form.** `_ASSIGNMENT_RE` and `_AUTH_HEADER_RE` now tolerate a quote between label
and separator and between separator and value. The **leading** quote is captured (so
`{'api_key': …}` keeps its punctuation); the **trailing** one is consumed but not re-emitted,
because the pre-existing `test_secret_in_the_rendered_source_line_is_scrubbed` pins
`_refuse(token=***REDACTED***` exactly — a rendered source line has no quote there. That pin caught
my first attempt, which is the pin working.

**Plus a third the contract author's fixture-reach interrogation found while I worked:** a
credential in the **key** position (`{"api_key=sk-…": 3}` — a reverse lookup, or per-token
telemetry). Dict keys are now scrubbed as text as well as used as labels; both halves are needed and
they are different defects.

---

## 5. R40 — your call, and the answer changed: **it is CLOSED, not pinned**

You leaned pin-with-trigger. **Measure first:** the R39 fix closes it, because the leak was always
*through our sink*, and our sink now reads the quoted form.

Differential control, httpx 0.28.1 — the asymmetry you measured is **still real**:

```
x-api-key        repr(headers) -> Headers({…, 'x-api-key': 'sk-ant-api03-MEASUREDVALUE…'})   leaks: True
Authorization    repr(headers) -> Headers({…, 'authorization': '[secure]'})                  leaks: False
```

But end-to-end through `configure_logging` + the real JSON formatter, with the real
`httpx.Request` as an `extra=` value in both its repr and its dict form:

```json
{"…", "request_headers": "Headers({… 'x-api-key': ***REDACTED***", "hdrs": {… "x-api-key": "**…"}}

LEAKS through the production sink: False
```

**So: fix, not pin — and it cost nothing extra**, because R38/R39 was the fix. What remains true and
worth pinning is the *upstream* fact — httpx obfuscates `authorization` and not `x-api-key` — as a
bound carrying R20's trigger, so nobody concludes from our green sink that httpx is safe. **That pin
is the contract author's**, and I have not written it.

---

## 6. ⚠ Three `loremaster/tests/` files are modified — none by me

At the start of this pass `git status` showed **no tracked file modified**. It now shows
`test_secret_leak_vectors.py` and `test_secret_typing.py` changed: the contract author's parallel
fixture work, landing during my run. I hit their file mid-edit twice —
`NameError: _auth_holder_classes is not defined` and a ruff `F821` on `workspace_roots` — both
transient, both gone by the final run.

**My edits this pass are three files:** `loremaster/loremaster/logging_setup.py`,
`loresigil/loresigil/factory.py` (⑥, §below). No test file was touched.

**⑥ R36 — the prose.** `loresigil/factory.py` said *"a consumer (lore, odoo-code)"*. Corrected,
with the reason recorded where it will be read: odoo-code is a **donor** (`batching.py` and
`voyage_cloud.py` say "ported from the odoo-code donor"), nothing imports this package — and the
distinction is not pedantry, because prose naming an external consumer reads as a compatibility
constraint, and this packet reshaped `EmbeddingConfig` on the strength of there being none.

---

## 7. Gates

```
$ uv run pytest <the six scoped paths> -q -n auto
417 passed in 5.76s

$ ./scripts/typecheck.sh
typecheck: lorerunes OK · lorescribe OK · loresigil OK · loremaster OK · skills OK

$ uv run ruff check .
All checks passed!

$ uv run pytest -q -n auto
1 failed, 7403 passed, 17 skipped, 3 xfailed, 1 warning in 192.99s (0:03:12)
```

**Target was 2 failed / 7373. Result: 1 failed / 7403.** The single survivor:

| test | verdict |
|---|---|
| `test_retired_symbols.py::…::test_no_file_references_a_retired_symbol` | pre-existing, unrelated — three packet-03b/11i receipt docs mention `_BRIEF_PUBLISH_` without the SUPERSEDED banner. Reproduced at `76f1d9f` in a provenance-verified archive (pass-1 §7.8). |

`test_surreal_harness.py`'s docstring-count failure — the other pre-existing one — is **gone**: the
contract author fixed the 36→37 count during this pass.

---

## 8. The pattern, since it is now eleven instances

Every one of R33/R34/R37/R38/R39 is the same shape, and the audits named it before I did: **a pin
whose property is right and whose fixtures cannot reach the case its prose claims.** Seven bare-word
labels that structurally cannot contain a compound. Text carriers that are unlabelled by
construction, guarding a scenario whose prose says "a labelled bearer token out of an `extra=` map".
A receiver-blind auth pin defeated not by a scheme but by a quote.

Two of this pass's own fixes were themselves too narrow on the first attempt — removing `Digest`
where the property was about every scheme, and fixing `\b` where `SURREAL_PASS` needed a label that
did not exist. **Both were caught by a pin or a measurement, not by review**, which is the only part
of this worth generalising: I would not have found either by reading my own diff.
