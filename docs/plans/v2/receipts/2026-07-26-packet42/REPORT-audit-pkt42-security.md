# REPORT-audit-pkt42-security — Phase 7 security audit, packet 42

brief-base v7 read

- **state:** done
- **deviations:** (1) probes were written to `/tmp` (I am read-only apart from this report), so every
  one is **inlined verbatim below** and regenerable from this file alone — no `/tmp` path is cited
  as evidence. (2) **The working tree carries uncommitted edits to two files I audited**
  (`logging_setup.py`, `config.py`), so my probes did NOT run against `8dc1259` verbatim — see §0.1,
  where I prove the deltas are comment/docstring-only and the measurements therefore hold.
- **Packages considered:** log-secret scrubbing → I checked the resolved environment for
  `structlog`, `scrubadub`, `detect_secrets`, `python_json_logger`, `logredactor`
  (`uv run python -c "import importlib.util as u; ..."` — **all absent**) and read
  `loremaster/pyproject.toml`'s dependency block. Verdict **`bespoke`**, and the read is the reason:
  every remediation I propose is a 2–5 line change inside this repo's own three-function scrubber
  (`_scrub_text` / `_scrub_value` / `_redact_auth_header`); the only packages that would *replace*
  it are secret **detectors**, which is precisely the practice packet 42 exists to end — adopting
  one would be a design reversal, not a package adoption. · `python-dotenv` (already adopted under
  R2/R12) verified in use with the correct call — see §5.
- **decisions-needed:** F1, F2 and F3 are widenings on the surface the packet's Scope OUT promises
  to keep protecting. **Operator ruling wanted on all three before deploy** — fix now, or accept
  and pin. My recommendation: fix F1 and F2 (both small, both inside the kept patterns), accept-
  and-pin F3's residue.
- **receipt pointers:** §1 verdict · §2 F1 (container key/value split) · §3 F2 (`\b` compound
  labels) · §4 F3 (quoted `Authorization`) · §5 R3/R12 resolver verification (CLEAN) · §6 F4
  credential lifetime through httpx · §7 F5–F8 residuals · §8 the seam gate's real reach (largely
  CLEAN) · §9 `lorerunes` (CLEAN) · §10 what I could NOT falsify · §11 probe sources.

---

## 0. Threat model I applied, stated before the verdicts

CLAUDE.md's standing model for this surface, adopted verbatim: **these gates catch the honest
developer or dependency that lets a credential reach a log line. They are not a boundary against an
author deliberately smuggling one out — anyone who can commit here can ship anything.**

Therefore, in this report:

- *"a clever attacker gets through"* is **not** a defect. Bound-method aliasing
  (`g = s.get_secret_value; g()`), `getattr` indirection, `SecretStr._secret_value`, and computed
  header names are **not reported as findings** — they are deliberate evasion, and two of them are
  already ledgered.
- *"an honest engineer's mistake goes unnoticed"* **is** a defect. Every finding below is reachable
  by code a competent engineer would write without any intent to evade — logging a headers dict,
  naming an env var `SURREAL_PASS` (we did), or attaching an SDK response to `extra=` (we do).

**Every claim below is a command and its real output.** Every negative result is paired with a
positive control. Where a control was itself defective I say so (§3 note).

Tree: `/home/ejprice/PycharmProjects/lore-pkt42`, branch `pkt42-prevent-the-leak`, **HEAD `8dc1259`**,
base `6a21fb6`. Provenance asserted before any probe ran:

```
$ uv run python -c "import loremaster, loresigil, lorerunes; print(loremaster.__file__); ..."
loremaster /home/ejprice/PycharmProjects/lore-pkt42/loremaster/loremaster/__init__.py
loresigil  /home/ejprice/PycharmProjects/lore-pkt42/loresigil/loresigil/__init__.py
lorerunes  /home/ejprice/PycharmProjects/lore-pkt42/lorerunes/lorerunes/__init__.py
httpx 0.28.1 · pydantic 2.13.4
```

### 0.1 ⚠ The tree I actually measured is NOT `8dc1259` verbatim — and why the results still hold

The brief named HEAD `8dc1259`. `git status` at audit time (2026-07-27) showed **uncommitted
modifications to two of the files under audit**:

```
$ git diff --stat HEAD -- loremaster/loremaster/logging_setup.py loremaster/loremaster/config.py
 loremaster/loremaster/config.py        | 22 +++++++++++++++++-----
 loremaster/loremaster/logging_setup.py |  8 ++++++++
```

Python imports the **working tree**, so every probe below ran against that, not against the commit.
Rather than eyeball the diff, I proved executable equivalence: parse both versions, strip every
docstring, re-parse and hash the AST.

```
loremaster/loremaster/logging_setup.py  HEAD=9c80109783c4fbe25eb28e3f59b079a2  WORKTREE=9c80…  IDENTICAL executable AST
loremaster/loremaster/config.py         HEAD=ea4b70de4fd5608c2823967149dfa2f1  WORKTREE=ea4b…  IDENTICAL executable AST
--- control: base(6a21fb6) logging_setup must DIFFER ---
base=bc549a5f615c6e23c0c6ac0bca7dfa89   (differs from HEAD — the instrument can see a real change)
```

**The control is the point**: the same hash under the same treatment separates `6a21fb6` from
`8dc1259`, so "identical" is a measurement and not a tautology. Both working-tree deltas are prose —
a `LORE_NAMESPACES` scope comment and a `resolve_secret` docstring expansion. **Every behavioural
result in this report is valid for `8dc1259`.**

Recorded because an audit that cannot name the tree it tested has not tested anything, and because
the next reader of this report will otherwise reproduce against the commit and get a byte-different
source file.

Baseline is green — every finding below is against a **passing** tree, measured 2026-07-27 at
`8dc1259`:

```
$ uv run pytest -q -n auto loremaster/tests/test_secret_leak_vectors.py \
    loremaster/tests/test_secret_typing.py loremaster/tests/test_secret_resolution_seam.py \
    loremaster/tests/test_logging_setup.py loresigil/tests/test_factory_secret_resolution.py \
    lorerunes/tests
388 passed in 5.70s
```

---

## 1. VERDICT on the packet's central argument

The argument under audit: *a credential can no longer BE in the text — `SecretStr` end to end, one
resolver, a gated unwrap surface, typed auth-header seams.*

**For credentials this codebase RESOLVES and SENDS, the argument holds and I could not break it.**
I attacked the resolver, the unwrap allowlist, the mint gate, the seam gate and the shape-B
retention property, and each survived (§5, §6, §8). That work is genuinely strong; the R19 shape-B
property in particular I confirmed by measurement rather than inspection.

**The argument does not cover the credential-shaped data that arrives from OUTSIDE that typing
discipline**, and that is where the deleted catch-all was doing most of its work:

| class | typed? | scrubbed at base | scrubbed at HEAD |
|---|---|---|---|
| our own resolved secret, in flight | ✅ `SecretStr` | n/a (masked) | n/a (masked) |
| a credential map (`dict`/`Headers`) reaching `extra=` or a repr | ❌ | ✅ entropy | ❌ **F1** |
| a label our alternation's `\b` excludes (`client_secret`, `SURREAL_PASS`) | ❌ | ✅ entropy | ❌ **F2** |
| a quoted `Authorization:` with a non-Bearer scheme | ❌ | ✅ entropy | ❌ **F3** |
| an unlabelled credential in free text | ❌ | ✅ entropy | ❌ **A18, accepted** |

A18 was accepted knowingly. **F1–F3 were not** — they are not in the accepted-bounds list, they are
not pinned, and each was scrubbed at base. The deletion is defensible for the class it was argued
about (`M1`–`M4`, secrets in flight) and **under-defended for the class beside it** (secrets in
structure).

Three new findings at HIGH, one at MEDIUM-HIGH, four residuals. Nothing I found is a **live** leak
in a production call path today — I verified the production `extra=` key census (§2.4) — so every
one is a *gap*, which under the stated threat model is exactly the reportable category.

---

## 2. F1 [HIGH] — `_scrub_value` scrubs dict VALUES in isolation, so the KEY never participates

**Location:** `loremaster/loremaster/logging_setup.py::_scrub_value`
**CWE:** CWE-532 (insertion of sensitive information into log file)
**Status at HEAD `8dc1259`:** measured, unpinned, **widened by this packet**

### 2.1 The mechanism

The whole surviving mechanism is *labelled* patterns — a label, a separator, a value. But
`_scrub_value` walks a mapping and calls `_scrub_text` **on each value alone**:

```python
if isinstance(value, dict):
    return {key: _scrub_value(inner) for key, inner in value.items()}
```

The key — which *is* the label — is never joined to the value it labels. So the moment a credential
sits in a mapping rather than in a sentence, **every labelled pattern is structurally blind to it**,
for every label, including the ones the contract pins hardest.

The same blindness applies to any *rendered* mapping, because a Python dict repr and a JSON object
both put a quote between the label and the separator (`{'password': 'x'}`), which
`_ASSIGNMENT_RE`'s `\b(label)\b\s*[=:]` cannot match either.

### 2.2 Measured, end to end through the real production sink

Driven through `configure_logging` → real handler → real `RedactingFilter` → real formatter (the
`_logging_fixtures.emit_through_configured_logger` path), BASE vs HEAD, probe source in §11.2:

```
case                                         BASE      HEAD      delta
-----------------------------------------------------------------------------
CTRL msg carries api_key= label              scrubbed  scrubbed
CTRL nested dict, Bearer value               scrubbed  scrubbed
extra dict {'Authorization': 'Basic <b64>'}  scrubbed  LEAK      <<< WIDENED
extra dict {'x-api-key': <key>}              scrubbed  LEAK      <<< WIDENED
extra dict {'password': <key>}               scrubbed  LEAK      <<< WIDENED
extra httpx.Headers object (x-api-key)       LEAK      LEAK      leaks at both
extra httpx.Headers object (authorization)   scrubbed  scrubbed
extra set of strings                         LEAK      LEAK      leaks at both
extra frozenset of strings                   LEAK      LEAK      leaks at both
exception __notes__ (PEP 678)                scrubbed  LEAK      <<< WIDENED
exception __notes__ labelled                 scrubbed  LEAK      <<< WIDENED
%-args dict value                            scrubbed  LEAK      <<< WIDENED
extra dataclass-ish object repr              LEAK      LEAK      leaks at both
```

**Controls, both directions.** Two CTRL rows scrub at both ends (the oracle is not stuck open);
four rows leak at *both* ends (the oracle is not stuck closed, and the diff can see BASE leaking).
The `httpx.Headers(authorization)` row scrubbing at both ends while `httpx.Headers(x-api-key)` leaks
at both is a clean differential — same object type, same sink, opposite verdict, decided entirely by
httpx's `SENSITIVE_HEADERS` (§6).

**The JSON formatter is not better** — it is the Mezmo-indexed surface, so it is worse:

```
$ ... extra={"headers": {"x-api-key": K, "authorization": "Basic ZGVhZGJlZWZjYWZlYmFiZQ=="}}
{"ts": "...", "level": "ERROR", "logger": "loremaster.jsonleak", "msg": "embed.probe.failed",
 "headers": {"x-api-key": "sk-ant-api03-QQ9vZ1xLm4TnB7wKpYc2Rd6HsJfA0eGu",
             "authorization": "Basic ZGVhZGJlZWZjYWZlYmFiZQ=="}}
x-api-key credential present: True
Basic credential present: True
```

And at the `_scrub_text` seam, the rendered-mapping form (probe §11.3):

```
py dict repr {'password': ...}  base=scrubbed  head=LEAK      <<< WIDENED
py dict repr {'api_key': ...}   base=scrubbed  head=LEAK      <<< WIDENED
py dict repr {'token': ...}     base=scrubbed  head=LEAK      <<< WIDENED
py dict repr surreal signin     base=scrubbed  head=LEAK      <<< WIDENED
json {"password": ...}          base=scrubbed  head=LEAK      <<< WIDENED
json {"api_key": ...}           base=scrubbed  head=LEAK      <<< WIDENED
dict repr inside exception msg  base=scrubbed  head=LEAK      <<< WIDENED
CTRL unquoted password=         base=scrubbed  head=scrubbed
CTRL unquoted api_key:          base=scrubbed  head=scrubbed
```

Note `py dict repr surreal signin` — that is `repr({"username": "root", "password": <cred>})`, the
**exact shape `store/_txn.py::signin_credentials` returns**, bound to a local named `credentials` and
live across two `await`s at eleven connection owners.

### 2.3 Why no pin caught it, and it is a fixture-reason pass

This is not an oversight the contract could have noticed, because of how its two halves are split:

- The seven `TEXT_CARRIERS` in `test_secret_leak_vectors.py` **are unlabelled by construction** —
  the file says so: *"Every carrier deliberately carries the credential WITHOUT an adjacent label …
  so the labelled patterns cannot be what saves it."* `_carrier_extra_nested` uses
  `{"cred": credential}` — key `cred`, value bare. Both its legs pass whatever `_scrub_value` does:
  the `SecretStr` leg is masked by the TYPE, and the bare-`str` leg is the A18 bound *asserted to
  leak*.
- Every LABELLED pin — `test_every_labelled_assignment_is_redacted`,
  `test_the_anthropic_api_key_header_is_redacted`,
  `test_a_NON_BEARER_AUTH_SCHEME_DOES_NOT_LEAK_ITS_CREDENTIAL` — calls `_scrub_text` **on a flat
  string**.

So **no pin in the packet ever drives a LABELLED credential through the container path.** R11
ruled *"a build replacing the dict/list/tuple recursion with `return value` … leaks a labelled
bearer token out of an `extra=` map"* — and the instrument built for it
(`test_all_three_consumers_route_through_the_one_scrub_implementation`) proves **routing**, not that
a labelled map is scrubbed. R11's own wrong build is caught; R11's own stated scenario is not
covered. *The recursion runs. It just runs with the label thrown away.*

Its closest neighbour, `test_the_counters_state_does_not_leak_through_the_production_log_path`, uses
`extra={"state": vars(counter)}` and passes **because `vars(counter)` holds a `SecretStr`** — the
type does the work; the scrubber contributes nothing on that path. Swap the value for a bare `str`
under the same key and it leaks.

### 2.4 Reachability today — a gap, not a live leak

I censused every production `extra=` key:

```
$ grep -rhoP 'extra=\{[^}]*' --include='*.py' loremaster/loremaster loresigil/loresigil lorescribe \
  | grep -oP '"[a-z_]+"' | sort -u
"attempt" "brief_name" "command_id" "database" "delay_s" "dim" "embedder" "engine_error" "error"
"error_class" "extras" "file_path" "job_id" "limit" "mode" "namespace" "n_docs" "n_texts"
"observed_dim" "op" "queue_depth" "raw" "reason" "response" "source" "status" "tier" "tool" "url"
"version" "watch"
```

None carries a credential today. **The nearest approach is real and worth naming:**
`store/_txn.py` logs `store.transaction.malformed_response` with `extra={"response": response}` — an
arbitrary object handed back by the SurrealDB SDK, going straight into the sink, where it is either
recursed key-blind (if a dict) or not scrubbed at all (if an object, §7 F5).

### 2.5 Remediation

Two lines, inside the existing scrubber, no new mechanism:

```python
if isinstance(value, dict):
    return {
        key: _scrub_text(f"{key}={inner}").removeprefix(f"{key}=")
        if isinstance(inner, str) else _scrub_value(inner)
        for key, inner in value.items()
    }
```

— i.e. **let the key participate as the label** when scrubbing a mapping's string values. And in
`_ASSIGNMENT_RE`, allow an optional quote between label and separator so rendered dicts/JSON match:
`\b(labels)\b["']?(\s*[=:]\s*)["']?(...)`. Pin both with a fixture whose **key is the label and whose
value is bare** — the one shape no existing fixture uses.

---

## 3. F2 [HIGH] — the label alternation's `\b` excludes every underscore-compound spelling

**Location:** `loremaster/loremaster/logging_setup.py::_ASSIGNMENT_RE`
**CWE:** CWE-532
**Status:** measured, **widened**, and it misses **our own credential's env-var name**

### 3.1 The mechanism, proven by differential

`_ASSIGNMENT_RE` is `\b(api[_-]?key|apikey|token|secret|password)\b(\s*[=:]\s*)(\S+)`. `_` is a
**word** character, so `\b` fails on both sides of an underscore compound — while `-` is a non-word
character, so the hyphen twin matches. Measured at the `_scrub_text` seam (probe §11.1):

```
LEAK      client_secret (OAuth2 RFC6749 std param)   ->  client_secret=sk-ant-api03-QQ9v…
LEAK      secret_key (Django/Flask std name)         ->  secret_key=sk-ant-api03-QQ9v…
LEAK      session_token                              ->  session_token=sk-ant-api03-QQ9v…
LEAK      refresh_token                              ->  refresh_token=sk-ant-api03-QQ9v…
LEAK      auth_token                                 ->  auth_token=sk-ant-api03-QQ9v…
LEAK      bearer_token (R26's own wrong-build name)  ->  bearer_token=sk-ant-api03-QQ9v…
LEAK      db_password                                ->  db_password=sk-ant-api03-QQ9v…
LEAK      private_key                                ->  private_key=sk-ant-api03-QQ9v…
LEAK      access_key (AWS)                           ->  access_key=sk-ant-api03-QQ9v…
LEAK      secret_access_key (AWS std)                ->  aws_secret_access_key=sk-ant-api03-QQ9v…
scrubbed  client-secret (hyphen twin)                ->  client-secret=***REDACTED***
scrubbed  session-token (hyphen twin)                ->  session-token=***REDACTED***
```

**The hyphen twins are the control that names the mechanism**: same label word, same separator, same
credential — only the joiner differs, and the verdict flips. This is not a spelling list; it is one
regex property with an unbounded consequence set.

Also leaking, because the label family is absent entirely rather than boundary-excluded:
`credentials=`, `passwd=`, `pwd=`, `pass=`, `signature=`, `sig=`, `Cookie: session=`,
`Set-Cookie: sessionid=`, and **URL userinfo** (`postgresql://lore:<cred>@db:5432/lore`,
`ws://root:<cred>@127.0.0.1:18500/rpc`). URL *userinfo* is a different component from the accepted
"secret in a URL **path segment**" bound, and it is the shape our own DSNs take.

### 3.2 The sharpest instance: it misses `SURREAL_PASS`

```
$ uv run python -c "from loremaster.logging_setup import _scrub_text as s; ..."
our own env spelling SURREAL_PASS=   -> SURREAL_PASS=sk-ant-api03-QQ9vZ1xLm4TnB7wKpYc2Rd6HsJfA0eGu
our own env spelling SURREAL_USER=   -> SURREAL_USER=root
CONTROL bare password=               -> password=***REDACTED***
```

`SURREAL_DEFAULT_PASSWORD_ENV = "SURREAL_PASS"` (`loremaster/loremaster/config.py`). The env-var
name of this project's own SurrealDB root password is not covered by this project's own labelled
pattern, while the bare word one line away is. Under the stated threat model this is the defect in
its purest form: **no attacker, no evasion — we named the variable ourselves.**

### 3.3 Every one of these was scrubbed at base

From the BASE-vs-HEAD differential (probe §11.4), **25 of 29 shapes moved from `scrubbed` to
`LEAK`**, including every row above. The two rows that leak at *both* ends are the working
both-leak control (`weak operator password, unlabelled` — the A18 bound).

⚠ **One of my own controls was defective and I am disclosing it rather than quietly dropping it.**
I wrote a `CTRL both-leak: short cred` row as `pw=hunter2` while the probe searched for the *long*
credential string, so it reported `scrubbed/scrubbed` **tautologically** — the searched-for value was
never in the input. It proves nothing. The honest both-leak control is the
`weak operator password, unlabelled` row (`LEAK/LEAK`), and that one does the job. Cited so the
table is read correctly.

### 3.4 Why no pin caught it

`ASSIGNMENT_LABEL_SAMPLES` is a **hand list of seven bare labels**
(`api_key`, `api-key`, `apikey`, `token`, `secret`, `password`, `authorization`).
`test_every_labelled_assignment_is_redacted` iterates ∀ label × ∀ separator over that list, and its
comment claims exactly that quantifier — but **every member is a standalone word**, so the ∀ ranges
over a set that *structurally cannot contain a compound*. This is CLAUDE.md's
"parameter-value MONOCULTURE" verbatim: a fixture family that cannot distinguish the correct build
from the one that misses every compound spelling in the world.

`test_the_core_label_set_is_derived_from_the_pattern` derives the alternation from the regex —
good — but asserts only that five labels are *present*. It says nothing about their boundaries.

### 3.5 Remediation

Replace the two `\b` anchors with underscore-tolerant boundaries, so a compound label still fires:

```python
_ASSIGNMENT_RE = re.compile(
    r"(?i)(?:^|[^A-Za-z0-9])"
    r"([A-Za-z0-9_-]*(?:api[_-]?key|apikey|token|secret|password|passwd|pwd|credentials?)"
    r"[A-Za-z0-9_-]*)"
    r"(\s*[=:]\s*)(\S+)"
)
```

Then pin with a **compound** fixture — `client_secret`, `SURREAL_PASS`, `secret_key` — and keep the
hyphen twin beside it as the discriminator. Add URL userinfo (`scheme://user:<cred>@host`) as either
a pattern or an explicitly accepted bound; today it is neither.

---

## 4. F3 [MEDIUM-HIGH] — the quoted `Authorization` form leaks every non-Bearer scheme

**Location:** `loremaster/loremaster/logging_setup.py::_AUTH_HEADER_RE`
**CWE:** CWE-532 · **Ruling touched:** R8, R16 (#235 rider)

`_AUTH_HEADER_RE` requires `\bauthorization\b\s*[=:]`. In every *rendered* form the label is
followed by a **quote** before the separator, so the pattern cannot match — and then only `Bearer`
survives, because `_BEARER_RE` matches inside the value:

```
scrubbed  dict repr Authorization Bearer     ->  {'Authorization': 'Bearer ***REDACTED***
LEAK      dict repr Authorization Basic      ->  {'Authorization': 'Basic sk-ant-api03-QQ9v…'}
LEAK      dict repr Authorization Token      ->  {'Authorization': 'Token sk-ant-api03-QQ9v…'}
LEAK      JSON authorization Basic           ->  {"authorization": "Basic sk-ant-api03-QQ9v…"}
LEAK      dict repr proxy-authorization      ->  {'proxy-authorization': 'Basic sk-ant-api03-QQ9v…'}
scrubbed  CONTROL unquoted Authorization Basic -> Authorization: Basic ***REDACTED***
scrubbed  CONTROL kwargs Authorization Basic   -> Authorization = ***REDACTED***
```

All four LEAK rows were **scrubbed at base** (§11.4). This is the surface R16/#235 exists to
protect. The rider's own words: *"deleting the catch-all without the fix WIDENS the leak"* for
`Basic`. The fix landed — for the **unquoted header-line form only**. The contract's two strongest
auth pins,
`test_a_NON_BEARER_AUTH_SCHEME_DOES_NOT_LEAK_ITS_CREDENTIAL` and
`test_an_UNKNOWN_auth_scheme_does_not_leak_its_credential_either`, both build their fixture as
`f"Authorization: {scheme} {credential}"` — one shape, unquoted. The receiver-blind pin was written
precisely to avoid enumerating schemes, and it is defeated not by a scheme but by a **quote**.

This is **distinct from the accepted structured-`x-api-key` KNOWN BOUND**: that bound is pinned with
a trigger and was argued; this is the `Authorization` header, has a named ruling behind it, and is
unpinned.

Note in the Bearer row that the trailing `'}` was eaten — residual R12, already ruled
out of packet scope in the ninth wave. I confirm it is still present and note only that it makes a
leak-vs-scrub reading ambiguous at a glance; I am **not** re-raising it.

**Remediation:** allow an optional quote in `_AUTH_HEADER_RE`
(`\bauthorization\b["']?\s*[=:]\s*["']?`), and add one quoted fixture to each of the two auth pins.
Composes with F1's `_ASSIGNMENT_RE` quote fix — one change covers both.

---

## 5. `resolve_secret` — R3 and R12 VERIFIED CLEAN

I could not break this. Derived, not inherited:

```
$ grep -rn "resolve_secret(\|resolve_config_value(" --include='*.py' \
    loremaster/loremaster loresigil/loresigil scripts skills | grep -v test_
loremaster/loremaster/embedding.py:79        api_key=resolve_secret(config.api_key_env),
loremaster/loremaster/auth.py:204            resolved[key.name] = resolve_secret(key.key_env)
loremaster/loremaster/config.py:710          resolve_secret(config.anthropic.api_key_env)
loremaster/loremaster/index/cli.py:121       surreal_password = resolve_secret(config.surreal.password_env)
loremaster/loremaster/scout.py:729           surreal_password = resolve_secret(config.surreal.password_env)
loremaster/loremaster/server.py:6755         surreal_password = resolve_secret(config.surreal.password_env)
loremaster/loremaster/server.py:7034         api_key=resolve_secret(config.anthropic.api_key_env),
scripts/search_score_survey.py:697,710       resolve_secret(...)
scripts/snapshot_gc.py:340                   password = resolve_secret(args.password_env)
scripts/comms_consumer_eval.py:2377          resolve_secret(ANTHROPIC_API_KEY_ENV)
loremaster/loremaster/calibration/counting.py:144   return resolve_secret(ANTHROPIC_API_KEY_ENV, env_file)
```

- **R3 holds at every server-path site.** Exactly **one** call site in the entire tree passes an
  `env_file`: `counting.py::load_api_key`. `server.py`, `scout.py`, `index/cli.py`, `embedding.py`,
  `auth.py` and `config.py` pass none. A stray `.env` in a container working directory cannot become
  a production credential source.
- **`load_dotenv` appears nowhere in the repo** — only `dotenv_values`. Verified by bare grep
  (a non-symbol textual seam; saying so per the dogfood protocol §4). So nothing exports a `.env`
  into `os.environ` and silently arms the server path for the rest of the process.
- **R12's `interpolate=False` is present at the one call**: `config.py`
  `value = dotenv_values(env_file, interpolate=False).get(env_var_name)`. Correct — the default
  would rewrite `${…}` inside a credential and *shorten* it on an unset var.
- **R17's username/password split is correct in the failure direction that matters**: all five
  `password_env` reads use `resolve_secret` (stay wrapped); all five `user_env` reads use
  `resolve_config_value` (plain). No real secret was un-wrapped while tidying away a fake one.
- The **`ENV_READ_ALLOWLIST`** (`test_secret_resolution_seam.py`) is small, every entry carries a
  ≥40-char evidence string, and the gate also fails on **stale** entries naming no live site — a
  property most allowlists lack.

**One low-severity note (§7 F8):** `SurrealConfig.url` is an unvalidated `str`.

---

## 6. F4 [MEDIUM] — R19's shape B holds for lore objects; httpx retains the credential instead

**Location:** `loremaster/loremaster/calibration/counting.py::build_auth_headers` / httpx 0.28.1
**Status:** gap, not a live leak

The lead's Q6 asked whether any object retains an unwrapped header dict, including via httpx
internals. Measured after a real (mock-transported) request, with a positive control:

```
count ok: 7
A. counter.__dict__ leaks:            False   <- R19 shape B holds
B. client.headers leaks:              False   <- the injected client is not mutated
C. request.headers RAW leaks:         True    <- httpx RETAINS it
D. repr(request.headers) leaks:       True    -> Headers({'host': ..., 'x-api-key': 'sk-ant-…'})
E. repr(request) leaks:               False   -> <Request('POST', 'https://api.anthropic.com/...')>
F. bearer client repr(headers) leaks: False   -> Headers({..., 'authorization': '[secure]'})
G. bearer client dict(headers) leaks: True
CONTROL plain dict with the key leaks: True
```

- **A and B are the good news, and they are real.** R19's structural mandate — build no auth
  headers at construction — is confirmed by measurement, not by reading the docstring. The
  #107-shaped owned-vs-injected hazard is genuinely closed.
- **C/D: the retention moved into httpx.** Every `httpx.Request` keeps the built header map, and the
  `Request` is reachable from `response.request` and from `httpx.HTTPStatusError.request`. For
  `x-api-key`, `Headers.__repr__` renders it **in full**.
- **D vs F is the differential that proves the lead's warning**, read from the installed source, not
  assumed: `httpx/_models.py` → `SENSITIVE_HEADERS = {"authorization", "proxy-authorization"}` and
  `_obfuscate_sensitive_headers` substitutes `[secure]`. `x-api-key` — the header our Anthropic path
  uses — is not in that set. Same object type, opposite verdict.
- **E is good news**: `Request.__repr__` and `Response.__repr__` render method/url/status only, and
  `httpx.Client`/`AsyncClient` define **no** `__repr__` (checked: `'__repr__' in httpx.Client.__dict__`
  → `False`). So httpx does not spill headers on its own.
- **G**: `dict(client.headers)` bypasses the obfuscation even for `authorization`.

**Why the pins cannot see it.** `test_the_async_counter_does_not_retain_the_raw_key` and its sync
twin construct a counter and inspect `f"{instance!r} {instance!s} {vars(instance)!r}"` — **the
counter instance only, and never after a request**. The object that actually holds the credential
(`response.request.headers`) is outside their reach. The class's positive control
(`test_the_leak_detector_can_see_a_retained_key`) is sound, but it validates the oracle, not the
reach.

**This composes with F1 into a one-line honest mistake:**
`logger.error("count.failed", extra={"headers": response.request.headers})` emits the Anthropic key
in full — the `Headers` object is not a `str`/`dict`/`list`/`tuple`, so `_scrub_value` returns it
untouched (§7 F5) and the formatter `str()`s it afterwards.

**Remediation:** either (a) extend the retention pin to inspect the **`Request` produced by a real
request**, not just the counter, or (b) accept it and **pin it as a KNOWN BOUND** with R20's already-
measured trigger (*"the day a lore client authenticates with a header httpx does not obfuscate"* —
which is today). R20 corrected the rationale one step short of this: it fixed the claim about *our*
objects and did not follow the credential into httpx's.

---

## 7. Residuals F5–F8

### F5 [MEDIUM · pre-existing, NOT widened] — non-container `extra=` values are never scrubbed
`_scrub_value` handles `str`, `dict`, `list`, `tuple`. **`set`, `frozenset`, and every object are
returned untouched**, and are then rendered *after* the filter has run — `json.dumps(..., default=str)`
in `JsonFormatter`, `f"{key}={value}"` in `KeyValueFormatter`. Measured leaking at **both** base and
HEAD (§2.2 rows `extra set of strings`, `extra frozenset of strings`,
`extra dataclass-ish object repr`, `extra httpx.Headers object (x-api-key)`) — so this packet did not
cause it. It is unpinned, and it is the delivery mechanism that makes F4 reachable. Cheapest fix:
add `set`/`frozenset` to the recursion and scrub `str(value)` for anything else the formatter will
stringify anyway.

### F6 [MEDIUM · pre-existing] — third-party loggers carry no `RedactingFilter`
`configure_logging` attaches the filter only to `LORE_NAMESPACES`. Measured, with control:

```
httpx        level=WARNING  handlers=0 propagate=True filters=[]
httpcore     level=NOTSET   handlers=0 propagate=True filters=[]
surrealdb    level=NOTSET   handlers=0 propagate=True filters=[]
websockets   level=NOTSET   handlers=0 propagate=True filters=[]

--- what reached a root handler (uvicorn's shape) ---
httpx HTTP Request: GET https://api/x?api_key=sk-ant-api03-QQ9v…
surrealdb signin payload {'password': 'sk-ant-api03-QQ9v…'}
CREDENTIAL PRESENT IN THIRD-PARTY OUTPUT: True
CONTROL lore-namespace scrubbed: True | … GET https://api/x?api_key=***REDACTED***
```

The identical text is scrubbed through a lore logger and emitted verbatim through a third-party one.
Only `httpx` is level-pinned; `httpcore`, `surrealdb` and `websockets` are not (the surrealdb SDK
does log — `connections/async_ws.py` emits `f"Unexpected error in _recv_task: {e}"` at DEBUG). Not
widened by this packet, but **unpinned and undocumented**, and `logging_setup`'s module docstring
("this module owns … the *secret backstop*") reads broader than the mechanism is. Recommend a
docstring scope sentence plus a pin.

### F7 [LOW] — an unrecognised auth scheme destroys the rest of the line
`_redact_auth_header`'s no-scheme branch returns `f"{label}{REDACTED}"`, discarding
`rest_of_line`:

```
unknown scheme eats rest of line -> Authorization: ***REDACTED***
CONTROL known scheme keeps rest  -> Authorization: Bearer ***REDACTED*** host=api.example.com trace_id=abc123
```

Input was `Authorization: Negotiate <cred> host=api.example.com trace_id=abc123`. The safety choice
(redact everything when the leading word may be the credential) is correct and I am not disputing
it — but `trace_id` and `host` are exactly the diagnostic data this packet exists to protect, and
`test_the_bearer_scheme_word_survives_a_full_authorization_header`'s *"the rest of the line must
survive"* assertion covers only the known-scheme branch. Redacting just the first token and keeping
the remainder would preserve both properties.

### F8 [LOW] — `SurrealConfig.url` is an unvalidated `str`, logged verbatim
`url: str = SURREAL_DEFAULT_URL` accepts `ws://root:<password>@host/rpc`. That value is logged at
`store/_txn.py` via `extra={"url": url}` and interpolated into `SurrealConnectionError` at eleven
connection owners (`f"could not connect to SurrealDB at {self._url!r}"`). Base scrubbed a
high-entropy userinfo password there; HEAD does not (§3.1). Operator misconfiguration, but the
*caller* is logging a config value it has no reason to treat as secret. Recommend a validator
rejecting userinfo in `SurrealConfig.url`.

---

## 8. The unwrap + seam gates — largely CLEAN, with one scope bound

I attacked the R26 seam gate by feeding honest spellings through the **real** `_node_verdicts`
(never a copy — R28.1's lesson), with four positive controls (probe §11.5):

```
CAUGHT    CTRL headers= from a variable       client.post(url, headers=h)
CAUGHT    CTRL literal x-api-key              h = {"x-api-key": key}
CAUGHT    CTRL auth= tuple                    httpx.AsyncClient(auth=("root", pw))
CAUGHT    CTRL direct .headers[...] mutation  client.headers["X-Foo"] = v
CAUGHT    aiohttp-style session               aiohttp.ClientSession(headers=h)
CAUGHT    urllib Request add_header           req.add_header("X-Api-Key", key)
CAUGHT    stdlib urllib Request headers dict  urllib.request.Request(url, headers=h)
unseen    query-param auth: params=           client.get(url, params={"api_key": key})
unseen    OAuth2 body: data= client_secret    client.post(url, data={"client_secret": secret})
unseen    JSON body credential                client.post(url, json={"token": key})
unseen    URL userinfo in the endpoint        client.get(f"https://root:{pw}@api/v1")
unseen    cookie auth                         client.get(url, cookies={"session": key})
unseen    websockets extra_headers=           websockets.connect(url, extra_headers=h)
```

**The gate is genuinely strong and library-agnostic** — the `headers=`/`auth=` leg catches aiohttp
and stdlib urllib without knowing they exist, and the name leg catches any auth-header literal
anywhere. v3's union is doing real work; I could not defeat it with a header-shaped spelling.

**Its bound is stated honestly in its own name — *auth **headers*** — and I report it as a scope
observation rather than a defect:** a credential that reaches the wire as a **query parameter,
request body, URL userinfo, or cookie** is unseen. That matters because it **composes with F2**: an
OAuth2 client-credentials grant is `data={"client_secret": secret}` — invisible to the gate *and*
unscrubbed by the surviving patterns. No such call exists in the tree today; `websockets`'
`extra_headers=` is worth adding to the kwarg set now, since the SurrealDB transport is a WebSocket.

**`UNWRAP_ALLOWLIST`** is 6 entries, AST-derived (`_unwrap_sites`, immune to the docstring-vs-call
confusion that produced the packet's own 13-vs-10 error), each carrying an evidence category from a
closed set. I found no unallowlisted unwrap and no honest spelling that escapes it. The
bound-method-alias and `SecretStr._secret_value` spellings are outside the threat model, and both are
**double-covered anyway** — `{"x-api-key": s._secret_value}` still trips the seam gate's name leg.

---

## 9. `lorerunes` — CLEAN

Derived rather than trusted (`grep -rn 'lorerunes' --include='*.toml' --include='*.sh'
--include='Containerfile' --include='*.py'`):

- **Dependency surface is genuinely empty** — `dependencies = []`, stdlib only, and it imports no
  sibling. Nothing in it reads `os.environ`, opens a file, spawns, or logs. As a new module on every
  other package's import path, its attack surface is one pure function.
- **Registered everywhere it must be**, including the two that matter for this packet's own laws:
  `Containerfile` (`COPY lorerunes/ /app/lorerunes/`) **and** the in-image conformance guard
  (`EXPECTED_MEMBERS` in `skills/lore-deploy/scripts/test_conformance_provenance.py`) — so #131/#139's
  "in the image but nobody checks" hole is closed for it. Also present in workspace `members`,
  `mypy_path`, `testpaths`, `scripts/typecheck.sh` `MEMBERS`, `_SCANNED_MEMBERS`, and both
  `loremaster`/`loresigil` dependency lists.
- **`lorerunes` is absent from `LORE_NAMESPACES`, and at `8dc1259` nothing says why.** If any
  `lorerunes` module ever calls `logging.getLogger`, its records propagate to the ROOT logger and
  bypass both the structured formatter **and** `RedactingFilter` — the same hole as F6, opened inside
  a workspace member. Today it emits no logs, so the absence is correct. ✅ **Already being closed in
  the working tree**: the uncommitted `logging_setup.py` delta (§0.1) adds exactly this — a
  "deliberate subset, not a stale mirror" comment with the re-open trigger *"the day any `lorerunes`
  module calls `logging.getLogger`"*. I flag it only so the commit that lands it is not dropped, since
  at the audited commit the property is unexplained and untriggered.
- **One property worth stating rather than a finding:** `is_blank` is now the **single** predicate
  deciding whether a credential is acceptable, in both packages. That is the ruling working as
  intended, and it is also a single point of failure — a regression making `is_blank("")` return
  `False` would accept a blank credential at the composition root *and* at the `loresigil` validator
  simultaneously. `TestTheBlanknessPredicateIsGENUINELYSHARED` exists for exactly this; I did not
  independently mutation-prove it (out of my measured scope) and flag that as an unverified
  inheritance rather than claiming it verified.

---

## 10. What I attacked and could NOT break

Recorded so a later wave does not re-spend the effort:

1. **R19 shape B** — measured clean on both the counter instance and the injected client, after a
   real request (§6 A/B). The owned-vs-injected #107 hazard is genuinely closed.
2. **R3** — every server-path call site passes no `env_file`; exactly one site in the tree passes
   one; `load_dotenv` is absent from the repo (§5).
3. **R12** — `interpolate=False` present at the one `dotenv_values` call (§5).
4. **R17** — all five password reads stay wrapped; all five username reads are plain (§5).
5. **The seam gate v3** — no header-shaped honest spelling defeated it, across three HTTP libraries
   (§8).
6. **The unwrap allowlist and the mint gate** — no escaping honest spelling found; AST-based, so
   immune to the prose/call confusion (§8).
7. **`Bearer` in every form I tried**, including quoted, multi-line, and mid-line — `_BEARER_RE` is
   the pattern that holds up (§4). The asymmetry is that *only* Bearer does.
8. **`httpx`'s own reprs** — `Client`/`AsyncClient` have no `__repr__`; `Request`/`Response` render
   method/url/status only (§6 E).

---

## 11. Probe sources (inlined — regenerable from this file alone)

All run as `uv run python <file>` from the repo root. `CRED` throughout is
`sk-ant-api03-QQ9vZ1xLm4TnB7wKpYc2Rd6HsJfA0eGu` (40 chars, high entropy, in the charset the deleted
`_TOKEN_RE` selected). The BASE module is obtained with
`git show 6a21fb6:loremaster/loremaster/logging_setup.py > base_logging_setup.py` and loaded via
`importlib.util.spec_from_file_location`.

**11.1 Labelled-pattern gap sweep** — a list of `(name, text)` cases run through
`loremaster.logging_setup._scrub_text`, printing `LEAK` when `CRED in output`. Six cases prefixed
`CONTROL` (unquoted `Authorization: Bearer/Basic`, bare `Bearer`, `api_key=`, `x-api-key:`,
`password=`) must scrub or the run exits 2. Case set: the underscore compounds and their hyphen
twins, the quoted/structured `Authorization` forms, the absent label families, and the URL/DSN
userinfo forms.

**11.2 End-to-end BASE-vs-HEAD** — imports `emit_through_configured_logger` and
`restored_lore_logger_state` from `loremaster/tests/_logging_fixtures.py`, runs each case through the
real configured logger, then repeats it with `loremaster.logging_setup._scrub_text` monkeypatched to
the BASE module's, so **the only variable is the scrub policy**. Carriers: `extra=` dicts keyed by
`Authorization`/`x-api-key`/`password`; `httpx.Headers` objects; `set`/`frozenset`; PEP-678
`__notes__`; `%`-args dicts; an object with a credential-bearing `__repr__`.

**11.3 Quoted-key class** — the same diff at the `_scrub_text` seam over `repr(dict)`,
`json.dumps(dict)`, a kwargs repr, and a dict repr embedded in an exception message, with unquoted
controls.

**11.4 Full BASE-vs-HEAD shape differential** — 29 shapes, printing `<<< WIDENED` for
`base=scrubbed → head=LEAK`. ⚠ Its `CTRL both-leak: short cred` row is defective (see §3.3); the
working both-leak control is `weak operator password, unlabelled`.

**11.5 Seam-gate spelling probe** — parses each snippet with `ast.parse`, walks it, and calls the
**real** `test_secret_typing._node_verdicts` on every `expr`/`stmt`; four `CTRL` snippets must be
CAUGHT or the run exits 2.

**11.6 Credential-lifetime probe** — drives `AsyncClaudeTokenCounter` through an
`httpx.MockTransport` that captures the outgoing `Request`, then reports whether `CRED` appears in
the counter's `__dict__`, the client's headers, the request's raw headers, `repr(request.headers)`,
`repr(request)`, and — as the differential — the loresigil bearer client's `repr(headers)` and
`dict(headers)`. Positive control: `repr({"x-api-key": CRED})`.

---

## 12. Recommended disposition

| # | sev | finding | recommendation |
|---|---|---|---|
| F1 | HIGH | `_scrub_value` throws the label away on mappings | **fix before deploy** — let the key participate; pin with a key-is-the-label fixture |
| F2 | HIGH | `\b` excludes every underscore compound, incl. `SURREAL_PASS` | **fix before deploy** — underscore-tolerant boundary; keep the hyphen twin as discriminator |
| F3 | MED-HIGH | quoted `Authorization` leaks every non-Bearer scheme | **fix before deploy** — optional quote in `_AUTH_HEADER_RE` (same edit as F1's second half) |
| F4 | MED | httpx retains `x-api-key` on every `Request`; pin's reach is the instance only | fix **or** pin as a KNOWN BOUND with R20's measured trigger — operator's call |
| F5 | MED | non-container `extra=` values never scrubbed (pre-existing) | add `set`/`frozenset`; pin the object case as a bound |
| F6 | MED | third-party loggers unfiltered (pre-existing) | scope sentence in the docstring + a pin; consider filtering them |
| F7 | LOW | unknown scheme destroys the rest of the line | redact the first token only |
| F8 | LOW | `SurrealConfig.url` accepts and logs userinfo | validator rejecting userinfo |

**On the deletion itself:** I do not recommend reinstating the entropy catch-all. The packet's
diagnosis is right — it was an unbounded classifier that lost four rounds and cost real diagnostic
data. But F1–F3 mean the *labelled* half it was left standing beside is narrower than the packet
believes, on three axes the rulings themselves name (R8/R11/R16). Closing them costs roughly ten
lines and three fixtures, and it is the difference between "we removed a guess" and "we removed a
guess and a third of the coverage we meant to keep".

**Escalation, outside packet 42:** F5, F6 and F8 are pre-existing and untouched by this packet. I am
surfacing rather than dropping them per scope law — the operator decides whether they belong here, in
a follow-on, or on the ledger.
