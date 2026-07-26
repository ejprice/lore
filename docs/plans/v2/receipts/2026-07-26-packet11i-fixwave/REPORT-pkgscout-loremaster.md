# REPORT-pkgscout-loremaster

Package-vs-hand-roll sweep of `loremaster/` (41,334 LOC, 56 production files).

**Everything below was measured on 2026-07-25 against worktree
`/home/ejprice/PycharmProjects/lore-pkt11i` at commit `6654be0` (branch
`pkt11i-floor-calibration-dark`).** Every present-tense claim means "at that sha" —
re-derive before acting.

---

## SUMMARY BLOCK

```
brief-base v6 read
state: done-with-deviations
```

**Deviations** — (1) coverage is partial by construction; §COVERAGE is the honest statement.
(2) I delegated *location* of hand-rolls to three read-only Explore subagents and did **every**
library verification myself; two subagent claims were over-stated, and I re-derived and
corrected both in place (§T3.4, §P5). Subagent counts I did not re-derive are labelled.
(3) Ephemeral overlays only (`uv run --with …`, one `podman run --rm`) — no file, lockfile,
image or git state mutated; this report is my only written artefact.
(4) This block is **54 lines against the brief's ≤40** — 16 of them are the mandated verdict
table. I chose the overrun over gutting the table; say the word and I will cut it to 40.
(5) The brief said commit as ONE commit. The lead committed an **incomplete mid-flight draft**
as `fc3be3c` (it predates the whole `index/`+`memory/` sweep — no §P1, no §SCOPE item 1), so
my work lands as a **second** commit on top rather than the single one asked for. I did not
amend `fc3be3c`: it is another agent's commit.

**Coverage** *(long form: §COVERAGE)* — **read closely, ~55%:** all of `index/`, `memory/`,
`store/`, plus `graph*.py`, `impact.py`, `symbols.py`, `diff.py`, `map.py`, `search.py`,
`render.py`, `auth.py`, `calibration/`, `config.py`, `read_file.py`, `store_read.py`,
`sanitise.py`, `embedding.py`, `scout.py`'s retry seam, `shellout.py`'s threat model.
**Partial:** `server.py` (~1,900 of 8,633 read line-by-line, 100% grep-swept by category);
the five ledger modules (cross-cutting machinery only — **domain state machines not read**).
**NOT covered (~700 LOC):** `source/*`, `agent_ref.py`, `calibration/baseline.py`,
`logging_setup.py` body, `memory/backend.py` 200–422.

**Ranked verdicts** — ranked by what a wrong choice COSTS, not by swap appeal.

| # | Symbol / cluster | Library | Verdict |
|---|---|---|---|
| **P1** | `index/watcher.py::_OverflowAware*` — ~370 LOC forking **watchdog's private internals** under an **unbounded `watchdog>=6.0`** | `watchfiles` 1.2.0 | **FORK → operator.** Rec: KEEP + pin + upgrade canary |
| **P2** | `auth.BearerAuthMiddleware` / `AuthVerifier` | `mcp.server.auth` *(installed)* | **REPLACE-WITH-ADAPTER** — silently disables the SDK's session-owner binding |
| **P3** | `calibration.counting.AsyncClaudeTokenCounter` | `anthropic` *(new)* | **REPLACE** — 3 measured defects; one permanently kills the probe |
| **P4** | `calibration.counting.load_api_key` | `python-dotenv` *(installed)* | **REPLACE** — measured to MISS `export KEY=…`. Live bug |
| **P5** | 4 private backoff policies, **none jittered** | `tenacity` *(in the image)* | **REPLACE-WITH-ADAPTER** — #102's class, in the population #202 didn't cover |
| **P6** | `server._EagerStartupLifespan` (~234 LOC ASGI bridge) | `starlette` *(installed)* | **REPLACE-WITH-ADAPTER** |
| **P7** | `index.snapshots.capture_git_identity` (only shell-out) | `dulwich` *(new)* | **REPLACE-WITH-ADAPTER** — oracle-verified byte-equal |
| **P8** | `map.MapEngine._page_rank` | `networkx` (+numpy/scipy) | **FORK → operator.** Rec: KEEP + trigger (nx's *default* tol reorders at n≥400) |
| **P9** | `server.AppContext._find_key_cycle` | `graphlib` *(stdlib)* | **REPLACE** — zero cost |
| **P10** | `pydantic-settings` declared-but-unused; `websockets` imported-but-undeclared | — | **DEPENDENCY DEFECT** |
| **T3** | `_render_age` · `_path_similarity` · the SurrealQL DDL/query layer · `sanitise.py` · `query_text.py` · `MemoryLedger` | `humanize`, `difflib`, `sqlglot`, SQLAlchemy | **KEEP / GENUINELY BESPOKE** — reasons given so the next scout needn't re-derive |

**Decisions needed (operator)** — (1) **P1**: keep the watchdog fork (pinned + canaried) or
migrate to `watchfiles` and re-solve overflow detection? Largest, most fragile hand-roll here.
(2) **P8**: accept a numeric change to a served ranking, or keep? (3) **P10**: adopt
`YamlConfigSettingsSource` or delete the dep — status quo is not an option. (4) **§SCOPE
item 1** is a live sweep-aborting bug, not a package question — who takes it?

**Tool honesty.** lore's index watches the MAIN checkout, **not this worktree (#125)** — so
every structural fact here came from grep/Read, and **I did not call `lore_search`/
`lore_impact`/`lore_get_symbol` at all**; they would have described a different tree. The
documented #125 fallback, said out loud. No friction row: #125 is already ledgered.

**Receipts** — §P1 (private-API inventory + version specifier) · §P2 (SDK source + session-
binding chain) · §P3 (captured wire shape) · §P4 (measured parser diff) · §P5 (site table) ·
§P7 (oracle-equality run) · §P8 (15-config divergence table) · §SCOPE (12 items).

---

## COVERAGE — the long form

*Read closely (me, or a subagent with my spot-verification of anything that changed a
verdict):* `auth.py` · `calibration/counting.py` · `calibration/engine.py` · `embedding.py` ·
`config.py` · `index/paths.py` · `index/indexer.py` (all 2,041) · `index/watcher.py` ·
`index/surreal_manifest.py` · `index/snapshots.py` · `index/reconcile.py` ·
`index/sqlite_resilient.py` · `index/records.py` · `index/schema.py` · `index/cli.py` ·
`index/manifest.py` · `memory/local.py` · `memory/ledger.py` · `render.py` · `read_file.py` ·
`store_read.py` · `map.py` · `search.py` · `sanitise.py` · `store/query_text.py` ·
`store/surreal.py` · `store/surreal_schema.py` · `store/_txn.py` · `store/candidate.py` ·
`graph.py` · `graph_surreal.py` · `impact.py` · `symbols.py` · `diff.py` · `scout.py`
(retry/reconnect seam) · `logging_setup.py` (head) · `shellout.py` (threat model).

*Partial:* **`server.py`** — ~1,900 of 8,633 lines read line-by-line; **100% grep-swept** for
retry/sleep, datetime, textwrap/padding, `lru_cache`/`heapq`/`bisect`/`difflib`/`OrderedDict`/
`deque`/`Counter`/`itertools`, `urlparse`, json/yaml, argparse, `os.environ`, `re.compile`,
`while True`, and percentage math. **The unread regions most at risk are `build_app_context`
(~530 lines of wiring) and the comms action handlers — a bespoke implementation there using
none of those tokens would have been missed.**
**`tasks/messages/briefs/findings/agents.py`** — cross-cutting machinery only (connection
lifecycle, id generation, pagination, sorting, dedup, time handling); **domain state machines
deliberately not read**, per brief.
**`memory/backend.py`** — lines 200–422 inferred from the symbol listing (pydantic model
declarations + a Protocol) rather than read. If that inference matters to a decision, it is
the one gap worth a second pass.

*NOT covered at all:* `source/*`, `agent_ref.py`, `calibration/baseline.py`,
`logging_setup.py` body — ~700 LOC. Out of scope by brief: `lorescribe/`, `loresigil/`,
`scripts/` (the latter is #201's).

---

## P1 — the watcher forks watchdog's **private internals**, under an unbounded version specifier

**Symbols** (`loremaster/loremaster/index/watcher.py`): `_OverflowAwareInotify(Inotify)`,
`_OverflowAwareInotifyBuffer(InotifyBuffer)`, `_OverflowAwareInotifyEmitter(InotifyEmitter)`,
`_OverflowAwareObserver(InotifyObserver)` — four subclasses, ~370 LOC.

**What it does, and why.** watchdog silently discards the kernel's `IN_Q_OVERFLOW` sentinel
(`wd == -1`). lore needs it: an overflow means events were *lost*, so the index must trigger a
reconcile sweep rather than quietly drift. It also needs to prune `exclude_dirs` while
recursively installing watches. Neither is reachable through watchdog's public API, so the
code subclasses down four levels and re-implements the internals.

**What it actually touches** `[source-verified — I read the class declarations and grepped
every private-name reference myself; the LOC figures are my subagent's, not re-derived]`:

| Method | What it re-implements |
|---|---|
| `_OverflowAwareInotify._translate_buffer` (~72 LOC) | a hand-port of watchdog's `Inotify.read_events` post-parse loop — move-from/move-to cookie bookkeeping, `_wd_for_path`/`_path_for_wd` map rewriting on recursive dir rename, ignored-watch cleanup, new-dir watch installation |
| `._read_raw_buffer` (~36) | the raw `os.read` loop off the inotify fd, incl. EINTR retry and EBADF short-circuit |
| `._simulate_sub_creates` (~48) | watchdog's `_recursive_simulate` |
| `._add_dir_watch` (~34) | watchdog's recursive watch enumeration, plus the exclusion prune |
| `.scan_buffer_for_overflow` (~26) | manual parse of the raw event buffer for the `wd == -1` sentinel |
| `_OverflowAwareInotifyBuffer.__init__` (~30) | **bypasses its parent's `__init__` via a grandparent call** (`super(InotifyBuffer, self).__init__()`) to swap the backing `Inotify` class; reaches into `watchdog.utils.delayed_queue.DelayedQueue` |
| `_OverflowAwareObserver.__init__` / `.schedule` (~47) | **bypasses `InotifyObserver.__init__`** by calling `BaseObserver.__init__` directly, then reaches into the private `_emitter_for_watch` map after `schedule()` to inject callbacks |

Private watchdog names depended on, confirmed by grep: `Inotify._parse_event_buffer`,
`_wd_for_path`, `_path_for_wd`, `_add_watch`, `_event_mask`, `_emitter_for_watch`, plus two
bypassed `__init__`s.

**The finding that makes this rank #1.** `loremaster/pyproject.toml` declares
**`watchdog>=6.0`** — **no upper bound**. A `watchdog` 7.0 with a renamed private attribute
or a reshaped `__init__` installs freely. And the failure mode is not an ImportError at
startup: `self._wd_for_path` going missing surfaces as an `AttributeError` in the **inotify
reader thread**, at the moment an event arrives. This is #131's exact shape one level up —
*"the artifact differs from the test environment and nothing tells you"* — except the
divergence trigger here is a dependency resolution rather than a container image.
`[source-verified]`

**The library, honestly assessed.** `watchfiles` — `[library-verified, watchfiles 1.2.0]`,
tested via `uv run --with watchfiles`. I introspected `awatch`'s full signature and its
source.

*What it would give lore, replacing hand-rolled code:*
- **`debounce: int = 1600, step: int = 50`** — native debouncing, which is exactly what
  `LiveWatcher._coalesce` / `_flush_key` / `_flush_all_timers` / the `_timers`+`_pending`
  dict pair hand-build (~90 LOC and an invariant spread across four methods).
- **`watch_filter: Callable[[Change, str], bool]`** and `recursive=True` — replaces
  `_add_dir_watch`'s exclusion prune, `LiveWatcher._dir_excluded`, and part of `_resolve`.
- Rust/`notify`-backed, cross-platform, and **no private-API subclassing at all.**

*What it would NOT give — the gap that decides this:* **`watchfiles` exposes no overflow or
rescan signal.** Its `Change` enum has exactly three members (`added`, `modified`, `deleted`)
and I found no `overflow`/`rescan` mention anywhere in `awatch`'s source. The single reason
this fork exists is the one thing the library does not surface.
⚠ **Unverified:** whether the underlying Rust `notify` crate handles overflow internally (by
forcing a rescan) such that lore would not *need* the signal. I could not determine that from
Python introspection, and I am not going to guess — **that question is the crux of this
decision and it needs answering before anyone migrates.**

**Verdict: FORK → operator. My recommendation is KEEP, but not as-is — KEEP + PIN + CANARY.**

Per this repo's "WHEN YOU CANNOT CLOSE A HOLE, PIN IT" law, a deliberate fork of a
dependency's internals is a known bound, and an unpinned known bound is indistinguishable
from an unknown one. Concretely, and cheaply:
1. **Bound the specifier**: `watchdog>=6.0,<7` in `loremaster/pyproject.toml`. One line. This
   is the whole difference between "we chose this fork" and "this breaks on the next
   `uv lock`."
2. **Ship an upgrade canary**: a test asserting every private watchdog name the fork depends
   on still exists with the expected shape — `hasattr(Inotify, "_parse_event_buffer")`,
   the `_wd_for_path`/`_path_for_wd` attributes present on a constructed instance,
   `InotifyObserver.__mro__` containing `BaseObserver`, `_emitter_for_watch` present. It
   goes RED on the watchdog bump instead of in production, and it carries the message the
   law prescribes: *"this is a KNOWN BOUND — the fork in `index/watcher.py` depends on
   watchdog internals; if you bumped watchdog deliberately, re-verify the fork."*
3. **Re-open trigger**: *the day watchfiles (or notify) exposes a rescan/overflow signal, or
   the day the fork breaks on a watchdog bump* — migrate the debounce + filtering to
   watchfiles and re-solve overflow against whatever it then offers.

**The control that would prove a migration, if taken.** A differential harness: drive the
same synthetic event storm (N rapid saves, a recursive directory rename, a `>16384`-event
burst to force a real `IN_Q_OVERFLOW`) through both the current watcher and a watchfiles
implementation, and assert the same set of `(tier, path)` re-index operations comes out —
**including after the overflow.** Anything less does not test the reason the fork exists.

---

## P2 — `loremaster.auth` hand-rolls the MCP SDK's auth seam, and loses a security control doing it

**Symbols:** `loremaster.auth.AuthVerifier`, `.ApiKeyVerifier`, `.BearerAuthMiddleware`;
installed at `loremaster.server.build_asgi_app`.

**What it does.** A one-method ABC (`verify(token) -> identity | None`), a named-key set
matched with `hmac.compare_digest`, and a plain ASGI middleware that 401s or delegates.

**The library.** `mcp.server.auth` — **already a direct dependency** (`mcp[cli]>=1.27`,
installed 1.27.2), shipping the identical seam: `provider.TokenVerifier` (Protocol:
`async verify_token(token) -> AccessToken | None`), `middleware.bearer_auth.BearerAuthBackend`
(same header parse, same `bearer ` prefix strip), and `RequireAuthMiddleware`.

**What I read.** `[library-verified, mcp 1.27.2]` `mcp/server/auth/middleware/bearer_auth.py`
in full · `mcp/server/auth/provider.py::TokenVerifier` · `mcp/server/fastmcp/server.py` (the
`token_verifier` → `AuthenticationMiddleware(backend=BearerAuthBackend(...))` wiring) ·
`mcp/server/streamable_http_manager.py::_handle_stateful_request` + its `_session_owners`
dict. `[source-verified]` `loremaster/auth.py` in full · `server.build_asgi_app` ·
`server.build_mcp_server`'s `FastMCP(...)` call · `config.AuthConfig`.

**The finding, and why it outranks the rest of the swaps.** `FastMCP(...)` is constructed
with **no** `token_verifier` and **no** `auth=AuthSettings(...)`, so the SDK's
`AuthenticationMiddleware` never runs and `scope["user"]` is never an `AuthenticatedUser`.
In `streamable_http_manager._handle_stateful_request`:

```python
user = scope.get("user")
requestor = authorization_context(user) if isinstance(user, AuthenticatedUser) else None
...
if requestor != self._session_owners.get(request_mcp_session_id):
    # A session can only be used with the credential that created it.
```

Under lore's middleware `requestor` is **always `None`**, and every `_session_owners[sid]` is
stored as `None`. `None != None` is never true, so **the check never fires**. The SDK's
"a session can only be used with the credential that created it" control is silently off.

`config.AuthConfig.keys` is a `list[AuthKey]` whose docstring advertises "rotate a developer
out" — multi-identity deployments are a designed feature. In one, a holder of key B who
learns key A's `mcp-session-id` can drive A's session. The gate lore built (a valid bearer is
required) holds; the per-session binding the SDK ships does not.

**Severity, stated honestly:** this needs auth enabled, ≥2 keys, and an attacker who both
holds a valid key and obtains another's session id (a `uuid4().hex` in a header). It is
defense-in-depth, not a front door. It ranks high because of its *class* — the hand-roll
silently disabled a library control nobody knew they had — which is the exact failure this
sweep exists to find.

**Verdict: REPLACE-WITH-ADAPTER.**
- Keep `ApiKeyVerifier`'s key set, the constant-time loop, and `build_api_key_verifier` —
  that logic is correct.
- Make it satisfy `TokenVerifier`: `async def verify_token(self, token) -> AccessToken | None`
  returning `AccessToken(token=token, client_id=<identity>, scopes=[...])`. ~15 lines.
- Pass it as `FastMCP(..., token_verifier=…, auth=AuthSettings(…))`; delete
  `BearerAuthMiddleware`. The SDK then installs the middleware chain and session binding works.

**The genuine gap (why ADAPTER, not a clean REPLACE).** `AuthSettings` requires an
`issuer_url`/`resource_server_url`, which is a real config addition for a static-key
localhost deploy. **Confirm `AuthSettings` can be satisfied without standing up OAuth before
committing to this** — if it cannot, the fallback is to keep lore's middleware but have it
populate `scope["user"]` with an `AuthenticatedUser`, which restores the binding with a
~5-line change and no config churn. That fallback is the cheaper fix and may well be the
right one.

**The control that would prove it.** A test that (a) authenticates as key A and captures the
returned `mcp-session-id`, (b) re-issues with key B and that session id, (c) asserts
`404 "Session not found"`. **Run it against the current tree first — it must fail**, which is
the mutation proof that this finding is real and not my reading of SDK source.

**KEEP, separately: `OriginValidationMiddleware`.** `[library-verified, starlette 1.2.0]` I
checked starlette's middleware set: `TrustedHostMiddleware` gates **Host**, not **Origin**;
`CORSMiddleware` omits CORS headers for a disallowed origin rather than rejecting the
request. Neither implements "absent Origin → allow, non-loopback → 403". **GENUINELY
BESPOKE.**

---

## P3 — `AsyncClaudeTokenCounter` is a hand-rolled Anthropic client carrying three defects the SDK does not have

**Symbols:** `calibration.counting.AsyncClaudeTokenCounter.count` / `._sleep_backoff` /
`TerminalCountError`. Consumer: `calibration.engine.CalibrationEngine._count_live_total`
and `._probe_loop`.

**The library.** `anthropic` — **not installed**; tested at **0.120.0** via
`uv run --with anthropic`. `AsyncAnthropic().messages.count_tokens(model=…, messages=[…])`
returns a typed `MessageTokensCount`.

**What I read.** `[library-verified, anthropic 0.120.0]` `AsyncAnthropic.__init__`
(`max_retries: int = 2`, `http_client`, `timeout`), and the **source** of
`BaseClient._calculate_retry_timeout`, `._should_retry`, `._parse_retry_after_header`. I also
**captured the SDK's real wire shape** through an `httpx.MockTransport`:

```
URL   : https://api.anthropic.com/v1/messages/count_tokens        # identical to lore's
METHOD: POST                                                       # identical
BODY  : {"messages":[…],"model":"claude-sonnet-5"}                 # semantically identical,
                                                                   # NOT byte-identical
HDRS  : x-api-key · anthropic-version: 2023-06-01 · content-type   # all three match
        + user-agent + 9 x-stainless-* telemetry headers           # extra
```

**The three defects, each measured against SDK source:**

1. **`_sleep_backoff` has NO jitter.** `min(RETRY_BASE_DELAY_S * (2**attempt),
   RETRY_MAX_DELAY_S)` is deterministic — N concurrent counters retry in lockstep. The SDK
   ends with `jitter = 1 - 0.25 * random(); timeout = sleep_seconds * jitter`. This is the
   **#102 deterministic-jitter class**, alive in a module neither the #102 remediation nor
   #202 touched.
2. **408 and 409 are misclassified as TERMINAL, and that permanently kills the calibration
   probe.** `count` retries only `429` or `>= 500`; every other status raises
   `TerminalCountError`. The SDK's `_should_retry` retries **408** (request timeout) and
   **409** (lock timeout) explicitly, and obeys an `x-should-retry` header. The consequence
   chain is source-verified end to end: one 408 from a proxy → `TerminalCountError` →
   `_probe_loop`'s `except TerminalCountError: … return` → **the probe loop exits for the
   process lifetime and drift detection is off until the container restarts.** It degrades
   quietly (the committed constant is still served), which is precisely why nobody would
   notice.
3. **`Retry-After` in HTTP-date form silently falls through to plain exponential.**
   `float(retry_after)` raises `ValueError` on `Wed, 21 Oct 2015 07:28:00 GMT`; the SDK falls
   back to `email.utils.parsedate_tz`. Minor (Anthropic sends integers) but free.

*(4th, cosmetic: `count` calls `_sleep_backoff` on the final attempt too, so retry exhaustion
always costs one extra sleep of up to 30s.)*

**Verdict: REPLACE.** Side 1 of the operator's rule, in its textbook form — the package does
the job and the hand-roll carries bugs upstream doesn't.

**The named cost — this is not a drop-in.**
`loremaster/tests/test_calibration_counting.py::TestRequestShapeParity::
test_wire_shape_is_byte_identical_to_survey_counter` asserts the body is **byte-identical**
to `scripts/token_survey.py::ClaudeTokenCounter`'s, and that the application-level header set
matches in keys and values. Both go RED (key order; `x-stainless-*`).
**Do not "fix" that by loosening the pin** — it exists so every measured count stays
comparable to the generation-anchored `baseline.json` forever. The correct wave moves **both**
sides to the SDK in one commit and re-pins parity as *semantic* (parsed-JSON body equality +
equality of url/method/`anthropic-version`/api-key header). `scripts/` belongs to another
scout (#201) — **this needs cross-packet sequencing; I am flagging it, not deciding it.**

**The control.** (a) Oracle equality: drive the old counter and the SDK through one
`httpx.MockTransport`, assert parsed bodies are equal dicts and the three load-bearing
headers match. (b) A live leg: assert the SDK's `input_tokens` for one baseline corpus file
equals that file's `claude_tokens` in `baseline.json` — the only check that proves the
constant stays anchored.

---

## P4 — `load_api_key` hand-parses a `.env` and MISSES the `export` form (live bug)

**Symbol:** `calibration.counting.load_api_key`.

**The library.** `python-dotenv` — **already installed (1.2.2) and already in the shipped
image**, transitively via `pydantic-settings`.

**Measured, not argued.** Fixture `.env` containing `export ANTHROPIC_API_KEY='sk-ant-export-form'`,
both parsers run over it (I transcribed lore's loop verbatim for the comparison leg):

```
dotenv:    sk-ant-export-form
hand-roll: None
```
`[library-verified, python-dotenv 1.2.2 + source-verified]`

**Why it matters.** `export KEY=value` is the normal shape for a `.env` a human also
`source`s. If `~/docker/mcp/.env` uses it, `load_api_key` raises `RuntimeError`,
`CalibrationEngine` never probes, and lore silently serves the committed constant forever —
the same quiet-degradation shape as P3 defect 2. **I did not read the operator's actual
`.env`** (a secrets file, outside my writable set and none of my business), so I cannot say
whether it bites today — **only that the parser cannot read a form the file is allowed to
contain.** That is enough to fix.

Related smell for the same fix: `load_api_key` **strips** whitespace off the env value, while
`config.resolve_secret`'s docstring says a secret is deliberately **never** stripped. Two
secret-resolution policies that disagree.

**Verdict: REPLACE.** `dotenv_values(path)`, env-first preference retained. ~6 lines net,
zero image weight — but `python-dotenv` should become a **declared** direct dep, not a
transitive accident.

**The control.** Table-driven over four fixture bodies — `KEY=v`, `export KEY=v`,
`KEY='v'  # comment`, `# KEY=commented` — asserting the resolved value for each. The `export`
row is the RED leg on the current tree.

---

## P5 — four private backoff policies, none jittered, in the population #202 did not cover

#202 dispositioned `store._txn.retry_on_conflict` as KEEP and that is correct — it is proven,
mutation-guarded, has a runtime guard keyed on its `__code__` frames, and is the **only**
backoff in the tree with jitter (`_txn_conflict_backoff_seconds` → `random.uniform(0, window)`).
This finding is the **other** population: the sites that never route through it.

`[source-verified]` — derived from `grep -rn 'asyncio.sleep\|time.sleep'` over
`loremaster/loremaster/**.py`, reading each hit's enclosing function:

| Symbol | Shape | Jitter? | Bound |
|---|---|---|---|
| `scout.CommandSubscriber._backoff` | `min(0.5 * 2**attempt, 30)` | **NO** | unbounded (reconnects forever) |
| `server._EagerStartupLifespan._acquire_eager_lease_with_retry` | **fixed** `sleep(2.0)`, 5 attempts | **NO** | not exponential at all |
| `calibration.counting.AsyncClaudeTokenCounter._sleep_backoff` | `min(1.0 * 2**attempt, 30)` | **NO** | 6 attempts |
| `calibration.engine.CalibrationEngine._probe_loop` | `min(start * 2**attempt, cap)` | **NO** | unbounded (by design) |
| *(reference)* `store._txn._txn_conflict_backoff_seconds` | full-jitter exponential | **YES** | attempt ceiling + deadline |

Four independent re-derivations of one policy, all missing the property the fifth has.
`scout`'s bites hardest: a store restart drops every subscriber's socket at the same instant
and every one reconnects on an identical 0.5 → 1 → 2 → 4s ladder — a thundering herd against
the store that just came back up.

*(Correction to a subagent claim: one agent reported "no true exponential backoff exists in
`index/`". That is right for `index/` specifically, and I have not attributed any of the four
sites above to it — the table is my own grep over the whole package.)*

**The library.** `tenacity` — **9.1.4, already installed AND already in the shipped
`localhost/lore:latest` image** (verified by `podman run --rm`; it arrives via
`langchain-core` ← `langchain-text-splitters`). Adopting it costs **zero image weight** —
only an honest direct-dependency declaration.
`[library-verified, tenacity 9.1.4]` I introspected `BaseRetrying.__init__` and confirmed:
- `AsyncRetrying(sleep=…, stop=…, wait=…, retry=…, before_sleep=…, reraise=…)` — **`sleep` is
  an injectable parameter**, which is exactly the gap all four sites hand-rolled around (they
  each inject a fake sleep for tests; that is *why* they hand-rolled).
- `wait_exponential_jitter(initial, max, exp_base, jitter)` and `wait_random_exponential(...)`
  supply the missing property; `stop_after_attempt` / `stop_never` /
  `retry_if_exception_type` all present.

**Verdict: REPLACE-WITH-ADAPTER — with a structural caveat that is the whole point.**

The adapter is **not** "decorate each site with `@retry`". Per this repo's ONE-IMPLEMENTATION
law and its explicit lesson that **routing is not sharing**, the correct shape is *one
lore-owned policy module* building `AsyncRetrying` instances from named policies
(`RECONNECT`, `EAGER_STARTUP`, `EXTERNAL_HTTP`), with four call sites that *use* it. Four
sites each constructing their own `wait_exponential_jitter(...)` from their own literals is
four hand-rolled policies wearing a library's name — measurably indistinguishable from
correct, and exactly how eleven `_query` seams passed for shared in #120.

**Do NOT fold `_txn.retry_on_conflict` into this.** #202's disposition stands; its
classify-and-signal contract and frame-keyed runtime guard are load-bearing.

**The control.** The mutation proof this repo already demands of shared things: change the
shared jitter constant or `exp_base` and assert **every** call site's timing pin goes RED — a
site that stays green is a private copy. Second leg, per site: 100 simulated attempt-0 delays
must not all be equal. That single assertion is what none of the four current sites can pass.

---

## P6 — `_EagerStartupLifespan` hand-builds the ASGI lifespan protocol; starlette already composes lifespans

**Symbols:** `server._EagerStartupLifespan` (~234 LOC), esp. `._drive_lifespan` (~112) and
`._shutdown_inner`.

**What it does.** Intercepts the `lifespan` scope so lore's heavy build runs eagerly at
process startup. To do that it hand-defines the six `lifespan.*` message-type constants and
five ASGI type aliases (its own comment concedes these are "byte-for-byte identical"
duplicates of the ones in `auth.py`), spawns the inner app as a task, and bridges
`receive`/`send` through **two `asyncio.Queue`s**.

**The library.** `starlette` — **installed 1.2.0, already transitive via `mcp`**, and
`streamable_http_app()` *returns a Starlette app*. `[library-verified, starlette 1.2.0]`
`Router.__init__(..., lifespan: Lifespan[Any] | None = None)` confirmed, and a `Router`
instance exposes `lifespan_context`. The idiom — `Starlette(routes=[Mount("/", app=inner)],
lifespan=combined)` where `combined` is an `@asynccontextmanager` doing
`async with inner.router.lifespan_context(app): <take eager lease>; yield; <release>` —
replaces the entire queue bridge with a `with` statement.

**Verdict: REPLACE-WITH-ADAPTER.** ~234 LOC → roughly 30, taking the duplicated ASGI
constants and type aliases with it. The adapter is the eager-lease sequencing (take after
inner startup, release before inner shutdown) — lore's own policy, which stays lore's code.

**Risk — real, hence ADAPTER.** The current code reports `lifespan.startup.failed` on a
failed eager build and deliberately caches nothing so a later startup retries. Starlette's
lifespan-context path raises out of startup instead; the failure semantics must be
re-established explicitly. `loremaster/tests/test_eager_startup.py` and
`test_eager_startup_survives_unparseable_file.py` are the existing pins that define
"correct" — **read them before the implementation**, per the tests-before-code law.

**The control.** Both existing eager-startup modules pass unchanged, plus one added pin: a
deliberately-failing build produces `lifespan.startup.failed` (not an unhandled exception),
and a *subsequent* startup on the same process still attempts the build.

---

## P7 — `capture_git_identity` shells out to `git`; `dulwich` reads the same values in-process

**Symbols:** `index.snapshots.capture_git_identity`, `._run_git_rev_parse`.

**The library.** `dulwich` — pure-Python git, **not installed**; tested at **1.2.12**.

**Oracle equality, measured on this worktree** `[library-verified, dulwich 1.2.12]`:
```
dulwich HEAD          : 6654be08629f2c7f915e0021aa23c0da28efd5dc
git rev-parse HEAD    : 6654be08629f2c7f915e0021aa23c0da28efd5dc   ← identical
dulwich active_branch : pkt11i-floor-calibration-dark
git --abbrev-ref HEAD : pkt11i-floor-calibration-dark              ← identical
non-git directory     : dulwich.errors.NotGitRepository
```
Note this ran **inside a linked git worktree** (`.git` is a *file* naming an external gitdir)
and dulwich resolved it correctly — the topology most likely to break a pure-Python reader.
I also read `dulwich.porcelain.active_branch`'s source: it raises `IndexError` on a floating
(detached) HEAD and `ValueError` when the ref is not a local branch, so an adapter's
`except (NotGitRepository, KeyError, IndexError, ValueError): return None` is ~10 lines and
reproduces the never-raises contract.

**Verdict: REPLACE-WITH-ADAPTER — with caveats I will not soften.**

*For.* This is the **only** shell-out in the shipped packages. `loremaster/shellout.py` (566
LOC of AST gate) exists solely to police it, and `SANCTIONED_EXEC_MODULES` holds exactly one
entry: `index/snapshots.py`. Removing the shell-out lets that allowlist go **empty** — a
strictly stronger, simpler invariant ("no shipped module reaches a spawner, no exceptions")
than "…except this one, whose internals the scan cannot see". **The gate itself should stay**
(its written threat model is future shell-outs); only its exemption disappears.

*Against.* **The shipped image DOES carry `/usr/bin/git`** (verified:
`podman run --rm --entrypoint sh localhost/lore:latest -c 'command -v git'`). #131's specific
failure is already closed at the image layer, so this is an **architecture** improvement, not
an outage fix — framing it as "prevents #131 recurring" would be false. **It also does NOT fix
#134**: #134 is a worktree `.git` file naming a host gitdir *outside* the `/workspace` mount,
and dulwich fails to reach that path exactly as the git binary does.

**The control.** A differential test over repository shapes — normal checkout, linked
worktree, detached HEAD, packed-refs-only, bare repo, non-git dir, nonexistent path —
asserting `dulwich_capture(p) == subprocess_capture(p)` for every one, keeping the subprocess
version *in the test* as the oracle and deleting it from production. **That is the only
version of this swap I would sign off on: I verified three of those seven shapes, and the
other four are where a pure-Python git reader earns or loses its keep.**

---

## P8 — `_page_rank` vs `networkx`: oracle-equal at a tight tolerance, DIVERGENT at the library default. **Operator fork.**

**Symbol:** `map.MapEngine._page_rank` (~23 executable lines), `_DAMPING = 0.85`,
`_PAGE_RANK_ITERATIONS = 50`. Its docstring pins a determinism contract: sorted iteration so
FP summation order — and the served ranking — is identical across runs.

**The library.** `networkx.pagerank(G, alpha=, personalization=, dangling=, max_iter=, tol=)`
(tested at **3.6.1**). Its default path dispatches to `_pagerank_scipy` and **raises
`ModuleNotFoundError` without numpy+scipy** — this swap drags both in.

**What I measured** `[library-verified, networkx 3.6.1 / numpy 2.5.1 / scipy 1.18.0]`. I
transcribed `_page_rank` verbatim and compared against `nx.pagerank(..., dangling=personalization)`
on random directed graphs with dangling nodes.

*At `tol=1e-13, max_iter=500` (n=120, 17 dangling):*
```
mass mine: 1.0   mass nx: 1.0
ORDER IDENTICAL: True        max abs diff: 1.63e-13
```
**Same algorithm.** The hand-roll does nothing exotic; nx reproduces it exactly.

*At networkx's **DEFAULT** `tol=1e-6, max_iter=100`, 15 configurations:*

| n | seeds 1, 7, 13, 42, 99 |
|---|---|
| 40 | order identical ×5 |
| 120 | order identical ×5 |
| **400** | **order DIVERGES ×5** (max abs diff 3.6e-6 … 1.1e-5) |

**Every 400-node configuration diverged.** Real projects have 400+ modules. A naive
`nx.pagerank(G, alpha=0.85, personalization=p, dangling=p)` **changes the order of lore's
served map at production scale** — silently, and only for large projects, which is the worst
possible discovery path.

**Verdict: FORK → operator. My recommendation: KEEP + RE-OPEN TRIGGER.**

*Why I lean KEEP.* ~23 executable lines, tested, deterministic **by construction** (fixed
iteration count + sorted summation). The library version's determinism would rest on
numpy/scipy FP reproducibility plus a correctly-chosen `tol`, and its *default* configuration
measurably changes a **served surface** at real scale. This is the shape where the package
does the job but the job includes a property the package's defaults do not give you.

*Why the operator may legitimately overrule me.* The cardinal rule leans toward the package;
#201 already proposes numpy/scipy/sklearn for the calibration statistics, so the weight may
land anyway; and §P8b's graph work would ride the same dependency. **If networkx lands for the
whole graph layer, `_page_rank` should go with it rather than be the lone hold-out.**

*Re-open trigger if KEEP:* **the day numpy+scipy enter the image for any other reason (e.g.
#201 landing), OR the day lore needs a second networkx-owned algorithm (centrality, SCC,
community detection) — re-open and migrate the whole graph layer in one wave, never this
function alone.**

**The control if taken.** (a) `tol` pinned at `1e-12` or tighter and `max_iter` raised —
**not** the defaults; (b) an order-equality oracle over a corpus **including at least one
graph with ≥400 nodes** (a small-N fixture here is exactly the non-discriminating fixture
this repo's law warns about — I only found the divergence *because* I went past 120);
(c) a determinism pin: same input, 20 runs, byte-identical rendered output.

**P8b — the rest of the graph layer, riding the same decision.**
`graph_surreal.SurrealCodeGraph.blast_radius` (bounded reverse-BFS with frontier/visited
sets), `._reverse_neighbours`, `._reference_source_index` (in-memory adjacency),
`._dead_code_candidates`, and `graph.CodeGraph._liveness_sources` are all things networkx
owns. **If networkx lands, these migrate with it and the case is stronger than `_page_rank`
alone** (more code, more error-prone). If not, KEEP: they are bounded and store-backed — the
BFS issues a store query per hop, and loading the whole graph into a `nx.DiGraph` is a
*different* performance profile, not obviously a better one. ⚠ **I did not measure that
trade-off; it is unverified and must be measured before anyone acts on it.**

---

## P9 — `_find_key_cycle` → `graphlib` (stdlib). Verdict: REPLACE.

`server.AppContext._find_key_cycle` is a hand-written three-colour recursive DFS (~34 lines)
over a `dict[str, set[str]]` returning the cycle path. `[library-verified, CPython 3.14
stdlib]` `graphlib.TopologicalSorter.prepare()` raises `CycleError` carrying it:
```
CycleError args: ('nodes are in a cycle', ['a', 'c', 'b', 'a'])
```
Zero dependency cost, stdlib-maintained, and it removes a recursive function that currently
has **no depth bound** (a pathological `create_many` batch could hit the recursion limit).

**Risk:** `graphlib` reports *a* cycle, not necessarily the same rotation as the hand-roll,
and that string reaches an agent in an error message. **Control:** pin the *set* of nodes in
the reported cycle and that the message names them — not the exact rotation.

---

## P10 — dependency-declaration defects (found while verifying the above)

`[source-verified]`

1. **`pydantic-settings>=2.14` is a DECLARED direct dependency of `loremaster` and is imported
   NOWHERE in the workspace.** `grep -rn 'pydantic_settings' --include='*.py' loremaster
   lorescribe loresigil scripts` → **zero hits.** It ships in the image; nothing uses it.
   *Either* adopt it — `[library-verified, pydantic-settings 2.14.1]` it exports
   `YamlConfigSettingsSource`, precisely what `config.load_config` hand-rolls (`read_text` →
   `yaml.safe_load` → `model_validate`), plus `EnvSettingsSource`/`SecretsSettingsSource`,
   which is what `resolve_secret` hand-rolls — *or* delete the declaration.
   **My recommendation: adopt it for `load_config`.** Caveat I could not settle: lore's
   `_StrictModel` uses `extra="forbid"` and `load_config` deliberately fails LOUD on an
   unresolvable secret at load time — **confirm `BaseSettings` preserves both** before swapping.
2. **`websockets` is imported by `store._txn`**
   (`from websockets.exceptions import WebSocketException`, used to build
   `_CONNECTION_ERRORS`) **but is NOT declared in `loremaster/pyproject.toml`.** It arrives
   only transitively via `surrealdb`. If `surrealdb` swaps its transport, `_txn.py` fails at
   **import time** — the whole server, not one feature. One line closes it.
3. **`watchdog>=6.0` has no upper bound** while `index/watcher.py` forks its private
   internals — see §P1.

---

## T3 — candidates examined and deliberately NOT replaced

Recorded so the next scout does not re-derive them; an unexplained absence reads as an
oversight.

**T3.1 — `server.AppContext._render_age` vs `humanize`. GENUINELY BESPOKE / KEEP.** The output
is a pinned served format: largest-fit single unit, no padding, boundaries `<120s → s`,
`<120m → m`, `<48h → h`, else `d`, named in design doc §9 and carried by `_COMMS_AGE_*_CEILING`.
`humanize.naturaldelta` produces prose ("2 minutes"), not `42m`. `[source-verified; the
humanize output shape is **my judgement**, not introspected]`

**T3.2 — `AppContext._path_similarity` / `_nearest_indexed_paths` vs `difflib`. KEEP.**
`difflib.get_close_matches` scores character-sequence similarity; lore's metric is
`max(common leading path segments, common trailing path segments)` — deliberately path-aware
(`a/b/c.py` vs `x/y/c.py` scores 1 for lore, poorly for difflib). Better-targeted semantics
for a "did you mean this indexed path?" teach. **[my judgement, from reading both sources; I
did not empirically compare outputs on a real path corpus — that comparison is the experiment
that would overturn this.]**

**T3.3 — the SurrealQL layer. GENUINELY BESPOKE.** (`store/surreal_schema.py`'s ~880-LOC DDL
emitter, `store/surreal.py::_build_where` / `_build_fulltext_predicate` / `_hybrid_statement`,
`memory/local.py::_build_fulltext_predicate`, `graph_surreal.py::_prefix_range_query`,
`_txn.py::compose` / `_assert_envelope_integrity`.) `[library-verified, sqlglot 30.8.0]`
sqlglot is installed and is the obvious candidate — I enumerated its dialects, **32 of them,
ATHENA through TSQL, and there is no SurrealDB/SurrealQL dialect.** `DEFINE FIELD OVERWRITE`,
`search::rrf`, `RELATE`, and record-id syntax are not SQL; the `surrealdb` 2.0 SDK ships no
builder. Domain code; stays hand-rolled.
Two notes that are **not** package findings but belong on the record: `_build_where`'s
injection defence is a hand-maintained column **allowlist** (`_ALLOWED_FILTER_KEYS`) — the
correct posture per this repo's own law; and `compose`/`_assert_envelope_integrity` are a
hand-rolled statement-smuggling guard whose correctness rests on regex-scanning for
`;`/`BEGIN`/`COMMIT`. Both deserve their own adversarial review. **Flagging, not auditing.**

**T3.4 — `sanitise.py`. GENUINELY BESPOKE.** The character class is a curated, documented set
(C0/C1, DEL, bidi overrides and isolates, zero-widths, U+2028/2029) chosen against a specific
threat (a rendered line forging a second citation row in an agent's context). No library
encodes that policy.
**Correction to a subagent claim I was handed:** one Explore agent reported the fence-width
formula "duplicated three times". I re-derived it. **The primitives ARE shared** —
`sanitise.max_backtick_run` and `MIN_FENCE_WIDTH` are imported by `render.py`, `search.py`
and `server.py`. What is cloned is the one-line **expression**
`max(MIN_FENCE_WIDTH, max_backtick_run(x) + 1)` (in `render.render_fenced` and
`search.SearchPipeline._fence_width`); `server.py` separately re-derives fence *detection*.
Much milder than "duplicated three times" — **but the `+ 1` is a render-safety policy, and by
this repo's law a policy is a function, not an expression to retype.** Recommend promoting
`fence_width(text) -> int` into `sanitise.py` beside the primitives it already owns.
*Reported with the correction attached, because an un-derived count inherited from a
subagent is exactly the failure this repo's CLAUDE.md documents against itself.*

**T3.5 — `store/query_text.py`. GENUINELY BESPOKE.** Its constants are live-measured engine
limits (117 OR-clauses / 114 AND-clauses before SurrealDB's parser recursion limit). No
library knows those. `truncate_at_word_boundary` is near-`textwrap.shorten`, but `shorten`
collapses all whitespace and appends a placeholder — different output. KEEP.

**T3.6 — `memory/ledger.py::MemoryLedger` + `index/sqlite_resilient.py`. KEEP.** Hand-written
DDL, a hand-written `ON CONFLICT … DO UPDATE` upsert, `PRAGMA integrity_check` probing, and
owner-only `umask`/`chmod` handling. SQLAlchemy would do the DML and Alembic the migrations,
but both are far heavier than a 4-column single-table rebuildable ledger, and the
resilient-open behaviour (delete-and-recreate a corrupt image, preserve a valid one) is
lore-specific recovery policy no ORM offers. **[my judgement; I did not prototype a SQLAlchemy
version.]** One real gap worth noting: the schema is applied idempotently with **no version
table**, so a future column addition has no migration path.

**T3.7 — `store._txn.retry_on_conflict`. Untouched — #202 owns it, and its KEEP is correct.**

**T3.8 — small stdlib wins, below the churn threshold, listed so they are not re-found.**
`server.AppContext._render_comms_skew_breakdown` counts with `d[k] = d.get(k,0)+1` where
`collections.Counter` exists · `search.SearchPipeline._select_enrichment_targets` full-sorts
then slices where `heapq.nlargest` exists · `server._extension_tool_wrapper` synthesises a
signature by assigning `__signature__`/`__annotations__` onto a closure, which `makefun` (not
installed) does properly · `indexer.Indexer._all_vectors_usable` is an O(chunks × dim) pure-Python
`math.isfinite` scan that `numpy.isfinite(a).all()` would vectorise — **that one flips to
worth-doing if numpy lands for #201 or §P8.** **[my judgement on all four.]**

---

## SCOPE — everything else I found. Surfaced, not buried; none of it is mine to fix.

1. **🔴 A single non-UTF-8 file aborts an entire tier sweep.** `[source-verified — I read both
   sites myself after a subagent flagged it]` In `indexer.Indexer._walk_and_index` and
   `._walk_collect_tier`, the line `source = abs_path.read_text(encoding="utf-8")` sits
   **outside** the `try` that follows it — the `try` wraps only `self._chunk(...)`. The
   comment immediately below reads *"ANY chunker exception isolates THIS file … instead of
   killing the whole sweep"*; **the isolation was built one line too late.** A
   `UnicodeDecodeError` from one included file propagates out of the whole tier walk. Same
   unguarded read at `indexer.py` `rebuild_graph_only` and `watcher.LiveWatcher._apply`.
   There is **no binary-file guard and no encoding detection anywhere** in the index path
   (`charset-normalizer` 3.4.7 is already installed, via `requests`, if detection is wanted).
   Minimal fix: move the read inside the existing `try` and give it its own failure reason
   constant beside `_FAILED_CHUNK_REASON`.
2. **`calibration` probe dies permanently on a 408/409** — §P3 defect 2. Live, independent of
   whether the SDK swap is taken.
3. **`load_api_key` cannot read `export KEY=…`** — §P4. Live parser gap.
4. **`websockets` imported but undeclared** — §P10.2. Import-time failure risk.
5. **`watchdog>=6.0` unbounded while forking its internals** — §P1/§P10.3.
6. **`pydantic-settings` declared but unused** — §P10.1.
7. **`SearchPipeline._wait_for_fresh` polls a full-table read every 50 ms.**
   `_WAIT_POLL_INTERVAL_S = 0.05`, and each poll calls `self._manifest.all_files()` then
   filters in Python (`_all_rows_indexed_for_path`). On a large project that is up to 20 full
   manifest scans per second for the duration of a `wait_for_fresh=True` search; a
   path-scoped query would be O(rows-for-that-path). `[source-verified; magnitude unmeasured
   — the concern is structural.]`
8. **The `_to_aware_utc` / `_require_aware_utc` family is replicated FIVE times**
   (`tasks/findings/briefs/messages/agents.py`) with a sixth variant in
   `server.AppContext._parse_rollup_since`. Two things: (a) it is a datetime-**parsing
   policy** cloned six ways — the ONE-IMPLEMENTATION law's exact target; and (b) **its
   `Z` → `+00:00` string patch is dead code on this Python.**
   `[library-verified, CPython 3.14]` `datetime.fromisoformat("2026-07-25T12:00:00Z")` →
   `2026-07-25 12:00:00+00:00`, and it truncates nanosecond precision without raising. The
   patch was needed before 3.11; the repo targets 3.14.
   *(`tasks.TaskLedger._to_aware_utc_ceiling`'s +1 µs is real, load-bearing cursor arithmetic —
   NOT redundant.)*
9. **`StoreReadTool._reject_uncontained` is a second, lexical-only re-implementation of the
   path-traversal guard**; its own docstring concedes it "mirrors the lexical step (1)" of
   `SnapshotLayout._safe_path`. **A containment check is a security policy** — two copies
   means a hardening applied to one may not reach the other. This ranks above the other DRY
   items because it guards a traversal.
10. **Broad ONE-IMPLEMENTATION duplication, subagent-sourced and NOT re-derived by me —
    treat as leads, not measurements:** `_ensure_connection` + `_drop_connection` +
    `_safe_close` + `_connect_lock` replicated across ~8–11 modules (~600 LOC aggregate);
    `_bare_id` ×6; `_as_rows`/`_as_list` ×6–7; `_first_count`/`_extract_group_count` ×3;
    `ImpactEngine._cap` and `DiffResult._cap` as two independent copies; the identical
    `walked_dirs → sorted(os.listdir) → is_included` walk body ×4
    (`_walk_and_index`, `_walk_collect_tier`, `_count_included_files`,
    `ReconcileEngine._included_files_on_disk`); three independent path→module-name
    derivations (`graph.CodeGraph.module_qualified_name`, `.importable_module_name`,
    `symbols.SymbolResolver._module_segments_from_file_path`). #120 ledgers the `_query`
    seam specifically; **the connection-lifecycle scaffolding around it appears to be a
    separate and larger population.** No package fixes this — it is an in-house extraction —
    but it belongs in the same conversation.
11. **`index/manifest.py` carries a dead `_SCHEMA` SQLite DDL string (~20 lines) that nothing
    executes** — kept as documentation. Dead code. `[subagent-sourced, not re-derived.]`
12. **`records.chunk_to_record` shallow-merges a chunker's own metadata *over* 10 structural
    fields** (`**dict(chunk.metadata)`), so a chunker metadata key can silently shadow a
    structural field (e.g. `tier`, `identity`). Same shape at
    `snapshots.SnapshotStamper._entry_content`. `[subagent-sourced, not re-derived — but if
    true this is a real correctness hazard worth a look.]`
