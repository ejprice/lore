# REPORT-adversary-39-auth-2 — packet 39 Google-OAuth contract, DELTA adversary pass

brief-base v9 read

- **VERDICT: CONTRACT INSUFFICIENT.** Measured 2026-07-31 against repo HEAD **`71bdd37`**
  (448 pins). The revision is a **real** fix, not a narrow patch: **10 of the predecessor's
  12 survivors are now KILLED**, and every one of the nine named pins discriminates.
  It is insufficient because **9 NEW wrong builds pass all 448 pins**, three of them
  aimed squarely at the pins added in the fix wave.
- **P1 headline (the BLOCKER): `WB48` — the dispatch guard placed AFTER `super().call_tool`.**
  448/448 green, the new WIRE pin green (its body carries the `HOSTED_OAUTH` marker exactly
  as the correct build's does) — **and the mutating tool's body EXECUTED**. Paired receipt
  (§4.1): correct build `invocations=0`, WB48 `invocations=1`, same refusal raised on both.
  Every refusal pin observes the exception; **none observes the effect**.
- **Two more that the fix wave's own new pins invite:** `WB50` — the served refused-set
  section names **all fifteen** tools (the annotation filter dropped); the new M7
  derivation pin checks MEMBERSHIP only, so it passes, and a hosted agent is told
  `lore_search` is refused (§4.2 has the rendered text). `WB51` — `host_is_loopback`
  computed by `ipaddress.ip_address(...).is_loopback` with `except ValueError: return True`:
  passes all six new host pins and boots `HOSTED_OAUTH` on a **hostname** bind (§4.3).
- **A ∀ pin that is FALSE on the correct build:** `TestEveryRegisteredToolIsClassified`
  holds only because its fixture registers no extensions. `_register_extension_tools`
  calls `mcp.add_tool(...)` with **no annotations**, and `ToolSpec` has no field for one
  (`extra="forbid"`). One extension ⇒ the pin's own assertion fails on the **reference
  build**, no mutation (§4.5). That is a **DESIGN gap**, not a pin gap.
- **SATISFIABILITY RE-DISCHARGED on the REVISED contract:** reference build → **448 passed
  / 0 failed**, `uv run ruff check .` → **All checks passed!** (§3).
  `loremaster.__file__ = /home/ejprice/scratch/adv39d/loremaster/loremaster/__init__.py`.
- **§8 handoff list: NOW COMPLETE** for the instrument that found it incomplete — the same
  4 collateral reds, all 4 listed (§8.1). Every retired-name grep hit gets an individual
  verdict; two riders remain undischarged (a CHANGELOG that does not exist; row 6's spy).
- **P4:** 415 RED / 33 GREEN / 448 collected **reproduces exactly** (§7). **P5:** the
  `TokeninfoSpy` fake CAN fail — mutating `call_count` reddens 16 pins (§9).
- **P-PKG diff:** `asgi-lifespan` 2.1.0 was installed **for this packet** (`93bd193`) and
  the contract **still hand-rolls** `running_asgi_app`. The `keep_with_trigger` trigger
  FIRED and nobody re-ran the decision (§2).
- ⚠ **Tool honesty:** the lore MCP tools are **absent from my toolset** — finding #294's
  **third** reproduction in this packet. All structure work is bare anchor-free grep (§1).
- Receipts: §2 P-PKG · §3 satisfiability · §4 wrong builds · §5 P1b quantifier table ·
  §6 the proposed pins, paired · §7 P4 · §8 P6/P6b · §9 P5 · §10 residuals · §11 instruments.

---

## 1. Capability check (brief-base §4 — first thing in the report)

| Demanded | What I have | What I did instead | What a lead must change |
|---|---|---|---|
| `ToolSearch "select:mcp__lore_lore__lore_search,…"` | **Not in my toolset.** The brief's exact select-list returned `No matching deferred tools found`, twice (once before and once after the MCP servers finished connecting). | **Bare, anchor-free `grep` + `Read`** for every structural question — the retired-name sweep, the extension registration path, the SDK source, the boot sites. Said out loud per the dogfood protocol. | The `contract-adversary` agent definition still lacks the lore tools it is required by project law to prefer. **Third independent reproduction of #294 in this packet** (contract author §1, `adversary-39-auth-1` §1, me). Its `tools:` block lists `ToolSearch`, so the gap is in what ToolSearch can REACH from this agent, not in the brief. |
| `lore_findings action=report` for friction | Not reachable (same cause). | Recorded here for the lead to file. | — |
| **Drive ledger task `9`** (`claimed → in_progress → done`), assigned to me mid-run at 2026-07-31T05:51:51Z | `lore_claim_task` / `lore_tasks` are **not in my toolset** — re-checked after the assignment arrived; `ToolSearch` returned `No matching deferred tools found` for both the select-list and a keyword query. **`SendMessage` is also absent**, so my final chat message and this file are my only channels. | **This report IS the proof of receipt** for task 9's second half — the lead ground-truths artifacts, not messages. Task 9's FIRST half (closing the nine pins) is not mine: it landed at `71bdd37` and is graded in §4.0. | **The lead must transition row 9 itself, or the `contract-adversary` definition must gain the lore tools.** Brief-base §5 says an agent drives its own row; that instruction is unmeetable for this agent, silently, and has been for every `contract-adversary` run in this packet. |
| Everything else (Read/Write/Bash/Grep, `scratch_copy.sh`, the venv, the predecessor's surviving scratch tree) | Available. | — | — |

**P6b ordering — honoured this time.** I enumerated the to-be-deleted code's behaviours from
`loremaster/loremaster/auth.py` **before** opening design §8 (§8.2). My predecessor could not
(the inventory is a section of the design doc it was briefed to read first); I read §8 only
after writing my enumeration down, and the diff in §8.2 is therefore independent.

---

## 2. P-PKG — my own survey, built first, then diffed

Every read-column entry names a file I opened or a value I executed **this run**, or says
plainly that I am relaying.

| # | Mechanism | Library | What I **READ / RAN** (2026-07-31) | My verdict |
|---|---|---|---|---|
| 1 | Token-verifier protocol · 401 challenge · session identity · RFC 9728 | `mcp` 1.27.2 | Relayed from `adversary-39-auth-1` §2 row 1 (it read `provider.py`, `bearer_auth.py`, `settings.py`, `routes.py`, `fastmcp/server.py` in full). **I did not re-read these.** | **replace** (agree) |
| 2 | Host/Origin DNS-rebinding validation | `mcp.server.transport_security` | **Read `_validate_host` and `_validate_origin` in full, this run** (pasted §2.1). Confirmed: exact match, then `allowed.endswith(":*")` ⇒ `host.startswith(base + ":")`. **No `*` catch-all exists**, so a policy cannot accidentally disable the check with a wildcard entry. Both methods are `# pragma: no cover` upstream. | **replace_with_adapter** (agree) |
| 3 | TTL positive/negative caches | `cachetools` 7.1.6 | Exercised in the reference build (both caches); 448/448 green. | **replace** (agree) |
| 4 | Outbound HTTP + hermetic double | `httpx` 0.28.1 | `MockTransport` async handler + `call_count` spy exercised in every wrong-build run. | **keep** (agree) |
| 5 | Google opaque-**access**-token introspection | `google-auth` **2.56.2** | **RAN IT MYSELF** (§2.2), not relayed: public surface of `google.oauth2.id_token` is `verify_oauth2_token`/`verify_token`/`verify_firebase_token`/`fetch_id_token`/`fetch_id_token_credentials`; first docstring line is *"Verifies an **ID Token**…"*; `[n for n in dir(id_token) if 'token_info' in n or 'introspect' in n]` → **`[]`**. | **bespoke — EARNED, and independently re-derived.** Agree with the author's §16 finding. |
| 6 | Email normalisation (NFKC → casefold → strip) | stdlib `unicodedata` | `lorerunes/pyproject.toml` `dependencies = []` (stdlib-only by workspace law); executed the fold on `ｅ` (U+FF45) to build the §6 fixture. | **bespoke** (agree) |
| 7 | Email syntax validation for the roster | stdlib / `email-validator` | Relayed from predecessor §2 row 7 (it executed `parseaddr` on all five R7 shapes). | **bespoke** (agree) |
| 8 | Roster change detection | `os.stat` signature / `watchdog` | Read the reference build's `_current_roster`: `(st_mtime_ns, st_size, st_ino)`. `watchdog` is a thread+queue per watched TREE — wrong shape for one file consulted per request. | **bespoke, minimal** (agree) |
| 9 | ⚑ **Running an ASGI lifespan in a test** | **`asgi-lifespan` 2.1.0 — NOW INSTALLED** (`pyproject.toml:52`, dev group, landed `93bd193` **for this packet**) | **Read `asgi_lifespan._manager` in full, this run** (§2.3): `LifespanManager(app, startup_timeout=5, shutdown_timeout=5)`, an async context manager; `state_middleware` injects `scope["state"]` — the same key the hand-roll passes by hand; `startup()` raises the app's own exception; `run_and_fail_after` bounds both phases. | ⚑ **replace — and this is a live DIFF.** The contract at HEAD still hand-rolls `_auth_fixtures::running_asgi_app` (35 lines: queues, a hand-rolled 30 s `wait_for`, a `suppress(CancelledError)`). |
| 10 | `TrustedHostMiddleware` / `CORSMiddleware` as alternatives | `starlette` | Relayed from predecessor §2 rows 10–11 (source read there). | **correctly NOT used** (agree) |
| 11 | ⚑ **Loopback classification of the bind host** — a row NEITHER table carries | stdlib `ipaddress` | Executed `ipaddress.ip_address(h).is_loopback` against the six pinned host values and three hostnames. It agrees with the contract on all six pinned values and **disagrees on every unparseable one**, where the implementer must choose a default. | **the contract does not decide, and the default is fail-open by accident** → **WB51**, §4.3 |

### The DIFF against `REPORT-contract-39-auth-1.md` §2 / §16

| Row | Author | Me | Disposition |
|---|---|---|---|
| `mcp` SDK | replace | replace (relayed) | **agree** |
| `transport_security` | replace_with_adapter | replace_with_adapter (read this run) | **agree** |
| `cachetools` | replace | replace | **agree** |
| `httpx` | keep | keep | **agree** |
| `google-auth` | bespoke, **settled by execution** in §16 | bespoke, **re-executed independently** | **agree — and now verified twice, not relayed** |
| `email-validator` | bespoke | bespoke (relayed) | **agree** |
| `watchdog` | bespoke, minimal | bespoke, minimal | **agree** |
| **`asgi-lifespan`** | *"escalate for install"* (§2, pre-revision) — the predecessor countered `keep_with_trigger` | **replace: the package is INSTALLED and the contract does not use it** | ⚑ **DISAGREE — a live finding.** §2.3 |
| **`ipaddress` / loopback classification** | absent | own row | ⚑ **gap in both tables**, and it is where WB51 lives |

**No mechanism the contract specifies is one a library already provides — except #9, whose
package the lead installed for this packet and the contract does not call.**

### 2.1 `_validate_host` / `_validate_origin`, read this run

```
$ sed -n "$(grep -n 'def _validate_host' .venv/.../mcp/server/transport_security.py | cut -d: -f1),+30p" …
    def _validate_host(self, host: str | None) -> bool:  # pragma: no cover
        if not host: … return False
        if host in self.settings.allowed_hosts: return True
        for allowed in self.settings.allowed_hosts:
            if allowed.endswith(":*"):
                base_host = allowed[:-2]
                if host.startswith(base_host + ":"): return True
        return False
```

Two facts worth carrying: **(a)** the `:*` form needs a colon in the presented Host — the
fact the author's M4 fix correctly pins BOTH forms on; **(b)** there is **no `*` catch-all**,
so I could not construct a "policy silently allows everything" wrong build. That is the
SDK, not the contract, doing the work — recorded so nobody re-derives it.

### 2.2 `google-auth`, re-executed rather than relayed

```
$ uv run --with google-auth python -c "…"
google-auth 2.56.2
public: [… 'fetch_id_token', 'fetch_id_token_credentials', 'verify_firebase_token',
         'verify_oauth2_token', 'verify_token']
verify_oauth2_token doc line 1: Verifies an ID Token issued by Google's OAuth 2.0 authorization server.
has tokeninfo/introspect helper: []
```

### 2.3 ⚑ `asgi-lifespan` is installed and unused — the trigger fired and nobody re-ran the decision

```
$ uv run python -c "import asgi_lifespan, importlib.metadata as md; print(md.version('asgi-lifespan'))"
2.1.0
$ grep -n "asgi-lifespan" pyproject.toml
52:    "asgi-lifespan>=2",
$ grep -rn "asgi_lifespan" loremaster/tests/
(no hits)
```

`LifespanManager.__init__(app, startup_timeout=5, shutdown_timeout=5)`; `state_middleware`
sets `scope["state"]`; `startup()` re-raises the app's own exception rather than a generic
`RuntimeError`. The hand-rolled `running_asgi_app` does the same job with private queues, a
hand-rolled 30 s timeout, and `contextlib.suppress(asyncio.CancelledError)` on teardown.

**Verdict: not a blocker, and not nothing.** The predecessor's `keep_with_trigger` verdict
named the trigger as *"the first pin needing lifespan STATE the stand-in does not model"*;
the LEAD then resolved the row by **installing the package**, which is a stronger event than
the named trigger. Under the packages-over-hand-rolling rule the row now reads `replace`.
**Concrete ask:** either swap `running_asgi_app`'s body for `LifespanManager` (its API is a
drop-in async context manager) **or** record in the survey why an installed dependency is
being carried unused — because a dev dependency nobody imports is a maintenance cost with
no consumer, and the next reader cannot tell which of the two happened.

---

## 3. THE SATISFIABILITY RECEIPT, re-discharged on the REVISED contract

The predecessor's receipt is void (26 pins are new). Re-run from scratch.

**Provenance (standing law — a verdict that cannot name its tree is not a verdict):**

```
$ ./scripts/scratch_copy.sh /home/ejprice/scratch/adv39d
scratch copy READY: /home/ejprice/scratch/adv39d
  loremaster  -> /home/ejprice/scratch/adv39d/loremaster/loremaster/__init__.py
  loresigil   -> /home/ejprice/scratch/adv39d/loresigil/loresigil/__init__.py
  lorescribe  -> /home/ejprice/scratch/adv39d/lorescribe/lorescribe/__init__.py
  lorerunes   -> /home/ejprice/scratch/adv39d/lorerunes/lorerunes/__init__.py

$ ./scripts/scratch_copy.sh --verify-only /home/ejprice/scratch/adv39d    # re-run at close-out
scratch copy VERIFIED: /home/ejprice/scratch/adv39d
```

The 6 reference-build production files (`auth.py`, `config.py`, `server.py`,
`lorerunes/{emails,posture,__init__}.py`) were copied byte-exact from
`/home/ejprice/scratch/refbuild` — the predecessor's **post-ruff-cleanup** build, so the
harder leg is included by construction, not re-argued. The 8 contract files were copied
from repo HEAD `71bdd37`.

```
$ cd /home/ejprice/scratch/adv39d && uv run pytest <the 7 loremaster contract modules> lorerunes/tests -q -p no:randomly
448 passed in 11.27s

$ uv run python -c "import loremaster, lorerunes; print(loremaster.__file__); print(lorerunes.__file__)"
/home/ejprice/scratch/adv39d/loremaster/loremaster/__init__.py
/home/ejprice/scratch/adv39d/lorerunes/lorerunes/__init__.py

$ uv run ruff check .
All checks passed!
```

**448 → 0 failed, ruff clean, post-cleanup leg included. The revised contract is satisfiable.**
The two pins the author flagged as possibly unsatisfiable (`test_an_unchanged_roster_is_not_re_read`,
`test_an_expired_token_is_not_served_from_the_positive_cache`) are inside those 448 and green;
that finding stands unchanged.

⚠ **One friction the builder still hits, unchanged from pass 1:** the demanded surface drives
`verify_token` to 7 returns, one over the live `PLR0911` ceiling. Satisfiable by factoring
(`_api_key_principal` + `_google_verdict`), but a builder who writes the straight-line version
gets a lint failure that reads like a contract problem and is not.

---

## 4. P1 — wrong builds

### 4.0 THE 12-SURVIVOR RE-RUN — 10 killed, 2 still standing

Harness: the predecessor's registry, retargeted at my tree with `BASELINE_COLLECTED = 448`
(`/home/ejprice/scratch/adv39d_wrong_builds.py`). Its two guards are intact — an anchor
matching ≠ 1 time is a hard error, and every run's COLLECTED total is compared to the
baseline. `not_comparable = 0`.

```
BASELINE (reference build): 448 passed, 0 failed, 448 collected
```

| # | Prior survivor | NOW | The pin that killed it |
|---|---|---|---|
| **WB30** ⚑ | guard as an instance attribute — dead on the wire | ✅ **KILLED** (1 pin) | `test_auth_identity_seam::TestTheReadOnlyGuardFiresOnTheSERVEDPath::test_a_hosted_principal_is_refused_a_mutating_tool_over_the_WIRE` |
| **WB34** ⚑ | `build_mcp_server` swallows `PostureConfigError` | ✅ **KILLED** (4 pins) | `…TestTheBootRefusalReachesTheThingThatActuallyBoots::test_build_mcp_server_refuses_a_hosted_config_whose_roster_will_not_load` |
| **WB33** ⚑ | `host_is_loopback` hardcoded `True` | ✅ **KILLED** (6 pins) | `…::test_a_hosted_config_on_a_NON_loopback_bind_refuses_to_boot[0.0.0.0]` |
| **WB28** | `EdgePolicy.allowed_hosts` ignores the bind host | ✅ **KILLED** (4 pins) | `…TestEdgePolicyIsOneDerivationFeedingBothLayers::test_a_lan_bearer_deployment_on_a_real_lan_address_is_not_421ed` |
| **WB35** | `LOOPBACK` policy trusts claude.ai | ✅ **KILLED** (1 pin) | `…::test_the_loopback_posture_does_not_allow_the_claude_origins` |
| **WB40** | refused-set section is a HAND-LIST | ✅ **KILLED** (1 pin) | `…TestInstructionsAreHonestAboutThePosture::test_the_refused_set_section_is_DERIVED_from_the_annotations` |
| **WB41** | roster change keyed on `st_size` | ✅ **KILLED** (2 pins) | `…TestRosterChangeDetectionSurvivesASameLengthEdit::test_swapping_one_address_for_another_of_equal_length_revokes` |
| **WB42** | raw token logged on the ADMITTED path | ✅ **KILLED** (1 pin) | `…TestTokenSecrecy::test_the_raw_token_never_appears_in_a_log_record_ON_SUCCESS` |
| **WB42b** | same, UNLABELLED (scrubber-invisible) | ✅ **KILLED** (1 pin) | same |
| **WB45** | `required_scopes=[]` | ✅ **KILLED** (1 pin) | `…::test_the_hosted_auth_settings_require_the_read_scope` |
| **WB29** | last-known-good roster kept on `OSError` | ⚠ **STILL SURVIVES** | **Not a finding — behaviourally equivalent.** The `OSError` arm still returns `None`, so every principal is still denied; a restored file gets a new inode/mtime, so the stale set can never be served. Unchanged verdict from pass 1. |
| **WB31** | cache key is a **truncated** SHA-512 (`[:8]`) | ⚠ **STILL SURVIVES** | ⚑ **Unadjudicated across TWO adversary passes.** §10-R1. |

**Every one of the nine named missing pins discriminates, and none of the 26 new pins is
decoration.** No sign of a letter-of-the-finding patch on any of the nine: three of them
(M3's enforcement leg, M4's both-Host-forms, M7's mutation instrument) are STRICTLY WIDER
than what the predecessor proposed, and I confirmed each widening does work the narrow
version would not have done.

### 4.0b THE NEW WRONG BUILDS — 9 of 11 SURVIVE 448/448

Harness: `/home/ejprice/scratch/adv39d_new_builds.py` (pasted §11.1), importing the
predecessor's mechanism so both guards apply unchanged.

| # | Wrong build | Verdict |
|---|---|---|
| **WB48** ⚑ | guard runs AFTER `super().call_tool` — the tool EXECUTES, then is refused | **SURVIVED** → **MISSING PIN N1, BLOCKER** |
| **WB50** ⚑ | refused-set section names EVERY tool (annotation filter dropped) | **SURVIVED** → **N2, HIGH (trust doctrine)** |
| **WB50b** ⚑ | the section's read-ladder list is EMPTY | **SURVIVED** → **N3, HIGH (trust doctrine)** |
| **WB51** ⚑ | `host_is_loopback` fails OPEN on any host `ipaddress` cannot parse | **SURVIVED** → **N4, HIGH (fail-open posture)** |
| **WB54** | `LoreServer.run()` swallows the refusal and serves a no-auth app | **SURVIVED** → **N8, MODERATE (third boot site = the Containerfile CMD)** |
| **WB55** | `required_scopes=[]` for LAN_BEARER only | **SURVIVED** → **N6, LOW** |
| **WB61c** | BOTH loremaster-side normalisation sites hand-rolled | **SURVIVED** → **N7, MODERATE (ONE-IMPLEMENTATION law)** |
| WB61 | only the `is_admitted` call site hand-rolled | **SURVIVED — but behaviourally EQUIVALENT** (§4.4); not a finding on its own |
| WB61b | only `_verdict_from` hand-rolled | **SURVIVED — but behaviourally EQUIVALENT** (§4.4); not a finding on its own |
| WB52 | raw token logged on the ROSTER-DENIED path | ✅ killed by `TestTokenSecrecy::test_the_raw_token_never_appears_in_a_log_record` |
| WB53 | raw token logged on the blank-credential path | ✅ killed (3 pins), same class |

**WB52/WB53 killing cleanly is the good news in this section:** invariant J (*the credential
is never logged*) is now genuinely ∀ over verification outcomes, not just over the two the
M5 fix named. I went looking for a third door and could not find one.

### 4.1 ⚑ `WB48` — THE BLOCKER, with its paired control

**The mutation** (one hunk, `TracingFastMCP.call_tool`):

```python
-        await _enforce_dispatch_policy(self, name)
         started = time.perf_counter()
         ok = False
         try:
-            result = await super().call_tool(name, arguments)
+            try:
+                result = await super().call_tool(name, arguments)
+            except Exception:
+                result = []
+            await _enforce_dispatch_policy(self, name)
             ok = True
             return result
```

**Contract verdict: 448 passed, 0 failed** — including all three of the new
`TestTheReadOnlyGuardFiresOnTheSERVEDPath` pins. The wire body carries the `HOSTED_OAUTH`
marker; the read-tool control and the api-key control both behave.

**Why the contract cannot see it:** every refusal pin in the packet — the 55 in
`test_hosted_readonly_posture` and the 3 new wire pins — observes **the raised exception or
the response body**. None observes **the effect**. And every one of them calls with
`arguments={}`, so on `lore_remember` the tool errors on argument validation anyway and no
side effect is visible even in principle.

**The paired probe** (`adv39d_survivor_receipts.py`, §11.2) registers a MUTATING tool with
**no required arguments** — so argument validation can never be the reason it did not run —
installs a real Google principal, and counts invocations:

```
=== WB48 — did the refused tool's BODY actually run? ===
  LEG 0 — the CORRECT reference build (the control):
    loremaster.__file__ = /home/ejprice/scratch/adv39d/loremaster/loremaster/__init__.py
    refusal raised: HostedToolRefusedError
    the MUTATING tool body executed: False  (invocations=0)
  LEG WB48 — guard runs AFTER super().call_tool
    loremaster.__file__ = /home/ejprice/scratch/adv39d/loremaster/loremaster/__init__.py
    refusal raised: HostedToolRefusedError
    the MUTATING tool body executed: True  (invocations=1)
```

**Same exception, same marker, opposite reality.** This is CLAUDE.md's cosmetic-fix category
verbatim: *the output looks right and the underlying state is wrong.* A hosted Google
principal calling `lore_remember` with well-formed arguments writes the memory row and is
then told, politely, that it may not.

**It is the M1 lesson one turn further on.** M1 asked *"does the guard run on the SERVED
path?"* and answered it. The question it did not ask is *"does the guard run BEFORE the
thing it is guarding?"* — and ORDER is not observable from a message.

### 4.2 ⚑ `WB50` / `WB50b` — the served refused-set section, in the direction nobody pinned

One hunk each. **448 passed, 0 failed** on both.

```
WB50 :  refused = _mutating_tool_names(mcp)
     -> refused = sorted(tool.name for tool in mcp._tool_manager.list_tools())
WB50b:  readable = sorted(… readOnlyHint is True)   ->   readable: list[str] = []
```

The rendered surface, all three legs (probe `section`, §11.2):

```
LEG 0 — CORRECT:
  … refused at call time: lore_claim_task, lore_comms, lore_findings, lore_index,
  lore_remember, lore_tasks. The read ladder remains fully available: lore_dead_code,
  lore_diff, lore_get_symbol, lore_impact, lore_map, lore_read, lore_recall, lore_search,
  lore_verify.

LEG WB50:
  … refused at call time: lore_claim_task, lore_comms, lore_dead_code, lore_diff,
  lore_findings, lore_get_symbol, lore_impact, lore_index, lore_map, lore_read,
  lore_recall, lore_remember, lore_search, lore_tasks, lore_verify. The read ladder
  remains fully available: lore_dead_code, lore_diff, … lore_verify.

LEG WB50b:
  … refused at call time: lore_claim_task, … lore_tasks. The read ladder remains fully
  available: .
```

**Both are served to an AGENT.** WB50's section is internally self-contradictory — it names
`lore_search` as refused **and** as available in the same paragraph — and under the Consumer
Law the reader is a model that learns the contract from what is served. WB50b tells a hosted
principal it has no surface at all.

**Why the fix wave's own new pin cannot see it:** M7's
`test_the_refused_set_section_is_DERIVED_from_the_annotations` computes
`missing = [name for name in derived if name not in section]` and asserts `not missing`. That
is a **membership** check in one direction. A section that names MORE than the derived set has
`missing == []`. `test_every_refused_tool_is_named_inside_that_section` is the same shape.
Neither checks the complement, and no pin checks the read-ladder clause's contents at all.

This is the exact class the M7 pin was added for — a served natural-language surface no gate
checks — reached through the opposite door.

### 4.3 ⚑ `WB51` — the loopback claim, through the branch the six new host pins do not reach

The revised contract pins six values: `{0.0.0.0, 192.168.64.100, ::}` must refuse,
`{127.0.0.1, localhost, ::1}` must resolve. **Every one is a value any classifier is certain
to recognise.** Nothing pins the UNKNOWN branch — and the natural implementation has one,
because `localhost` is not an IP literal and `ipaddress.ip_address` raises on it:

```python
def _host_is_loopback(host: str) -> bool:
    try:
        return bool(ipaddress.ip_address(host).is_loopback)
    except ValueError:
        return True          # 'localhost' is not an IP literal -- treat unparseable as local
```

**448 passed, 0 failed.** The paired probe:

```
  LEG 0 — the CORRECT reference build (the control):
    server.host='lore.firehawktransam.org'       -> REFUSED (PostureConfigError)
    server.host='0.0.0.0'                        -> REFUSED (PostureConfigError)
    server.host='127.0.0.1'                      -> HOSTED_OAUTH
  LEG WB51:
    server.host='lore.firehawktransam.org'       -> HOSTED_OAUTH        <-- FAIL OPEN
    server.host='0.0.0.0'                        -> REFUSED (PostureConfigError)
    server.host='127.0.0.1'                      -> HOSTED_OAUTH
```

**Consequence:** `HOSTED_OAUTH` boots with lore itself bound to a name that resolves to a LAN
or public address — design R4 / investigation M-2's *"instant whole-LAN exposure"*, reached
one spelling over from the value WB33 was fixed for. `""` (uvicorn's all-interfaces spelling)
takes the same branch.

**The generalisable shape, which is worth more than the pin:** *when a contract pins only
values a classifier is certain to recognise, the UNKNOWN branch is unpinned — and the unknown
branch is where the fail-open/fail-closed default lives.* The fix wave widened this pin from
one host to six and every one of the six is canonical.

### 4.4 `WB61` / `WB61b` / `WB61c` — one normaliser, or two?

The predecessor's residual R9 (*the "prove sharing by mutation" leg is owed and
undischarged*) is still owed. I made it concrete.

There are **two** loremaster-side normalisation sites: `_verdict_from` (`normalize_email(email)`)
and the `is_admitted(verdict.email, roster)` call, which normalises again inside. Breaking
**either one alone is invisible because the other rescues it** — I measured both:

| build | broken sites | contract | observable? |
|---|---|---|---|
| WB61 | `is_admitted` call only | **448/0 SURVIVED** | **No** — `_verdict_from` already normalised. Behaviourally equivalent; **not a finding.** |
| WB61b | `_verdict_from` only | **448/0 SURVIVED** | **No** — `is_admitted` re-normalises. Behaviourally equivalent; **not a finding.** |
| **WB61c** | **both** | **448/0 SURVIVED** | ⚑ **YES** — a Google-reported compatibility form is DENIED against a listed ASCII address |

The reference build's double normalisation is defensive redundancy, and it is why single-site
mutations look equivalent. **WB61c is the honest wrong build**, and my proposed pin N7 kills
it (`9 passed, 2 failed` — the second failure is N5, which fails everywhere; §6).

**Bounded honestly:** the divergence is only reachable when Google reports an NFKC-foldable
spelling, which Google does not normally emit. So WB61c is a **ONE-IMPLEMENTATION law
violation with a bounded live consequence**, not an authentication bypass. It matters because
it is precisely the shape #102 documents: routing is not sharing, and the only instrument that
tells them apart is a mutation the contract does not perform.

### 4.5 ⚑ A ∀ PIN THAT IS FALSE ON THE CORRECT BUILD — the extension registration path

`TestEveryRegisteredToolIsClassified::test_every_registered_tool_carries_an_explicit_read_only_hint`
iterates `hosted_server(tmp_path).list_tools()`. That fixture registers **no extensions**.
Production registers extension tools through `_register_extension_tools`:

```python
wrapper = _extension_tool_wrapper(spec)
mcp.add_tool(wrapper, name=spec.name, description=spec.description)   # <-- no annotations=
```

and `ToolSpec` (`loremaster/loremaster/extension.py`) has **no annotations field** and is
`model_config = ConfigDict(..., extra="forbid")` — so an extension author **cannot** declare
a tool read-only even if they want to.

Probe `adv39d_extension_probe.py` (§11.3), on the **known-correct reference build**, no
mutation of any kind:

```
loremaster.__file__ = /home/ejprice/scratch/adv39d/loremaster/loremaster/__init__.py

LEG A (no extension): 15 tools registered
  unclassified: []
  the pin's assertion HOLDS for this configuration

LEG B (one extension): 16 tools registered
  unclassified: ['bump_counter']
  the pin's assertion *** FAILS *** for this configuration
```

**Two consequences, and the second is a DESIGN question the builder cannot answer alone:**

1. The ∀ pin does not quantify over the **registration paths**. It is the quantifier law's
   own shape: *a ∀ helper evaluated only where the branch cannot fire.*
2. Under R8's deny-by-default, **every extension tool is refused on the hosted surface,
   permanently, with no way to say otherwise.** That is fail-CLOSED and therefore not
   dangerous — but it is undesigned. Design §7 never mentions extensions, and the day
   somebody ships a read-only extension tool for the hosted deployment, the answer is
   "you cannot".

⚠ **This one cannot be closed by writing a pin alone.** My N5 (§6) is written and it fails on
the correct build — adding it as-is would ship an unsatisfiable pin (the C-DEF class the
satisfiability receipt exists to catch). **It needs an operator/lead ruling first:** add a
read-only declaration to `ToolSpec`, or have `_register_extension_tools` pass an explicit
`ToolAnnotations(readOnlyHint=False, …)` and record "extension tools are hosted-refused by
construction" as a KNOWN BOUND with a re-open trigger. Either way the pin then becomes
satisfiable and belongs in the contract.

---

## 5. P1b — THE QUANTIFIER TABLE (every invariant; every guarded row with a receipt)

| # | Invariant | ∀-over-inputs or GUARDED? | Receipt |
|---|---|---|---|
| A | **Auth ∀** — every `(token, tokeninfo-response, allowlist)` → `None` or a complete, allowlist-consistent `AccessToken` | **∀-over-outcomes** via `assert_verification_outcome_is_total` | 8 hostile-field door builds killed (WB08/11/12/18/19/44 + malformed/degenerate). ⚠ Bound unchanged: the helper rides `_VerifierProbe`, so `test_allowlist_roster`'s 43 direct-call pins sit outside it. Not exploited by any build I constructed. |
| B | **Posture ∀** — every registered tool classified | ⚑ **GUARDED — by the REGISTRATION PATH.** The fixture registers no extensions | **Receipt: §4.5 — the pin's own assertion is FALSE on the correct build with one extension.** → **N5 + a design ruling** |
| C | **Roster fail-closed ∀** — any unloadable roster denies everyone, whatever the cause | **∀ over 6 broken states × both cache paths** | WB04a/04b/05/46 killed. WB29 survives, behaviourally equivalent (§4.0). |
| D | **Revocation immediacy (S5)** | **∀ over principals × cache states × change SIGNAL** — the M6 fix closed the signal axis | WB13/14/15 killed; **WB41 now killed (2 pins)**. I found no third signal a build could key on that the `(mtime_ns, size, ino)` fixture does not move. |
| E | **Identity distinctness (F3)** | **∀ over 4 ordered principal pairs, through the assembled app** | WB01/02/03 killed at two layers each. Strongest property in the contract, unchanged. |
| F | **Hosted principals cannot write** | ⚑ **GUARDED — by the OBSERVATION POINT.** The wire door is now closed (M1); the pins observe the *message*, never the *effect*, and never the *order* | **Receipt: WB48 survives 448/448 with `invocations=1` (§4.1).** → **N1, BLOCKER** |
| G | **One EdgePolicy derivation feeds both layers (R9)** | **∀ over 3 bind hosts × HOSTED / LAN_BEARER / LOOPBACK** after M4+M8 | WB16/17/28/35 all killed. I attacked the remaining axis (a policy that allows too MUCH) and the SDK's lack of a `*` catch-all (§2.1) closes it. |
| H | **Boot refuses an unloadable roster / an incoherent posture (R11/R12)** | ⚑ **GUARDED — by the SEAM LIST.** `resolve_posture` + `build_mcp_server` + `build_asgi_app` are pinned; `LoreServer.run()` and `main()` — what the Containerfile actually runs — are not | **Receipt: WB54 survives 448/448 (§4.0b).** → **N8** |
| I | **The loopback claim** — `HOSTED_OAUTH` requires a loopback bind | ⚑ **GUARDED — by RECOGNISED VALUES.** Six canonical hosts; the unknown branch is free | **Receipt: WB51 survives 448/448 and boots on a hostname (§4.3).** → **N4** |
| J | **The presented credential is never logged** | ✅ **∀ over verification OUTCOMES** — the M5 fix generalised it | WB42/42b killed; **my WB52 (roster-denied) and WB53 (blank credential) BOTH killed** by the same pins. I could not find an unguarded door. **This row moved from guarded to universal.** |
| K | **The token travels in the BODY, never the URL** | **∀ over the recorded request** | WB21 killed by 45 pins. |
| L | **Every roster INPUT LINE has exactly one fate** | **∀-over-lines**, all three fates fixture-FORCED | WB05 killed; merge fate forced by a 2-in-1-out fixture. Exemplary. |
| M | **ONE normaliser, both sides of the seam** | ⚑ **GUARDED — by ASCII FIXTURES.** The seam pin's inputs differ on no input from a private `.casefold()` | **Receipt: WB61c survives 448/448 (§4.4).** → **N7** |
| N | **The refusal is a structured `ToolError`** | **∀ over both refusal types** | WB23/24/25 killed. |
| O | **`required_scopes` is the ruled value** | ⚑ **GUARDED — by the POSTURE.** Asserted for HOSTED_OAUTH only | **Receipt: WB55 survives 448/448 (§4.0b).** → **N6** |
| P | **The served instructions match the served behaviour** | ⚑ **GUARDED — by MEMBERSHIP, in ONE direction.** Both section pins ask "is every refused tool named?", neither asks "is anything else named?" | **Receipt: WB50 and WB50b both survive 448/448, with the rendered text (§4.2).** → **N2, N3** |
| Q | **The cache key is the whole token's SHA-512** | **GUARDED — a token-PREFIX pin, not a digest-LENGTH pin** | **Receipt: WB31 survives, unchanged across two passes.** → §10-R1, needs a ruling |
| R | **The wire pins exercise the SERVED path** | ⚑ **GUARDED — by the fixture's TRANSPORT.** All three wire pins set `mcp.settings.json_response = True`; production never does, so production serves **SSE** | **Receipt: I could NOT construct a wrong build that differs between the two transports** — dispatch sits above the encoder. Declared as an honest residual (§10-R7), not a finding. |

**Six invariants remain guarded rather than universal, and every one of the six carries a
surviving wrong build.** Two rows moved the right way in the fix wave (D and J); one moved
the wrong way in the sense that M1 closed the *path* axis of F and exposed the *order* axis.

---

## 6. The MISSING PINS, written and PAIRED

All eleven proposed pins live in a scratch copy at
`/home/ejprice/scratch/adv39d/loremaster/tests/test_adv39d_missing_pins.py` (pasted verbatim
in §11.4), never in the repo.

**The P0 control leg** — on the known-correct reference build:

```
$ uv run pytest loremaster/tests/test_adv39d_missing_pins.py -q -p no:randomly
1 failed, 10 passed in 2.07s
FAILED …::TestEveryREGISTRATION_PATHProducesAClassifiedTool::test_an_extension_contributed_tool_is_classified_too
```

**10 of 11 are green on a correct build. The eleventh (N5) fails ON THE CORRECT BUILD — that
is the finding of §4.5, not a botched pin, and it is why N5 needs a ruling before it is
adopted.**

**The RED leg** — each wrong build applied, the same module re-run
(`adv39d_pin_pairs.py`, §11.5). N5's constant failure is listed everywhere and is expected:

```
CONTROL (reference build): 10 passed, 1 failed :: ['test_an_extension_contributed_tool_is_classified_too']
WB48    -> 9 passed, 2 failed :: ['test_the_refused_tools_body_is_never_invoked', <N5>]
WB50    -> 9 passed, 2 failed :: ['test_the_refused_set_section_does_not_name_a_READ_ONLY_tool', <N5>]
WB50b   -> 9 passed, 2 failed :: ['test_the_section_names_every_read_only_tool_as_still_available', <N5>]
WB51    -> 7 passed, 4 failed :: ['…refuses_to_boot[lore.firehawktransam.org]',
                                  '…refuses_to_boot[lore-internal]',
                                  '…refuses_to_boot[example.com]', <N5>]
WB55    -> 9 passed, 2 failed :: [<N5>, 'test_the_lan_bearer_auth_settings_require_the_read_scope_too']
WB54    -> 9 passed, 2 failed :: [<N5>, 'test_run_propagates_the_posture_refusal_rather_than_serving']
WB61c   -> 9 passed, 2 failed :: [<N5>, 'test_a_compatibility_form_google_email_matches_an_ascii_roster_line']
```

**Every proposed pin reds on its own build and ONLY on its own build.** That is the
discrimination leg the role spec demands, and it is why these are pins rather than opinions.

| # | The test that should exist | The defect it catches | Severity |
|---|---|---|---|
| **N1** | `TestARefusedToolNeverRUNS::test_the_refused_tools_body_is_never_invoked` (+ its control `…_a_permitted_read_tool_body_IS_invoked`) — register a mutating tool with **no required arguments**, refuse it, assert the invocation counter is 0 | **WB48**: a guard placed after dispatch. The refusal message and the wire body are byte-identical to the correct build's; the write has already happened. | ⚑ **BLOCKER** |
| **N2** | `TestTheRefusedSetSectionIsHONESTInBOTHDirections::test_the_refused_set_section_does_not_name_a_READ_ONLY_tool` | **WB50**: the section names all fifteen tools. An agent reads *"lore_search … refused"* and routes around the MCP — a failed acceptance under the trust doctrine. | **HIGH** |
| **N3** | `…::test_the_section_names_every_read_only_tool_as_still_available` | **WB50b**: *"The read ladder remains fully available: ."* — a hosted principal is told it has nothing. | **HIGH** |
| **N4** | `TestTheLoopbackClaimIsDENY_BY_DEFAULT::test_a_bind_host_the_mapping_does_not_RECOGNISE_refuses_to_boot`, parametrised over 3 **hostnames** | **WB51**: fail-open on the unrecognised branch ⇒ `HOSTED_OAUTH` on a non-loopback bind. | **HIGH (fail-open)** |
| **N5** | `TestEveryREGISTRATION_PATHProducesAClassifiedTool::test_an_extension_contributed_tool_is_classified_too` | The ∀ classification pin's blind registration path — **and the design gap under it.** ⚠ **Needs a ruling before adoption** (§4.5): it is RED on a correct build today. | **DESIGN ESCALATION** |
| **N6** | `TestTheRequiredScopeIsRuledInEveryGATEDPosture::test_the_lan_bearer_auth_settings_require_the_read_scope_too` | **WB55**: M9's property, one posture over. Behaviourally inert today; a silently deleted defence-in-depth layer. | **LOW** |
| **N7** | `TestOneNormaliserBOTHSidesOfTheSeam::test_a_compatibility_form_google_email_matches_an_ascii_roster_line` | **WB61c**: two private normalisers at the loremaster seam. Discharges the predecessor's residual R9 as behaviour rather than as an import assertion. | **MODERATE** |
| **N8** | `TestTheBootRefusalReachesTheCONTAINERSEntryPoint::test_run_propagates_the_posture_refusal_rather_than_serving` (uvicorn stubbed; asserts it is never reached) | **WB54**: the third boot site. `Containerfile` `CMD ["…","-m","loremaster.server"]` → `main()` → `LoreServer.run()`, neither of which any pin touches. Low plausibility, zero cost. | **MODERATE** |
| **N9** | a pin on the cache key itself — see §10-R1; **needs a ruling**, not a unilateral pin | **WB31**: a 32-bit cache key. The **positive** cache is the dangerous half: a token colliding with a previously-ADMITTED one is served that principal's verdict. | **ESCALATION** |

---

## 7. P4 — the author's claims, reproduced rather than relayed

```
$ cd /home/ejprice/PycharmProjects/lore && uv run pytest <the 7 loremaster contract modules> lorerunes/tests \
      -q -p no:randomly --tb=no
415 failed, 33 passed in 1.73s
```

**415 RED / 33 GREEN / 448 collected — reproduces EXACTLY** at HEAD `71bdd37`. The author's
and the lead's independently-derived counts hold, and the 33 GREEN are unchanged from the
pre-revision baseline, which is the property that says nothing was loosened to make room.

The `+26` arithmetic in §16 also reconciles: 3+3+9+4+2+2+1+1+1 = 26; 422+26 = 448. ✔

Its three widenings (§16 *"Three places I did NOT take the adversary's code verbatim"*) were
each checked against the narrow version:
- **M7's mutation instrument** — monkeypatching `_READ_ONLY_ANNOTATIONS` rather than calling
  `_install_hosted_instructions`. Verified: `_READ_ONLY_ANNOTATIONS` is a real production
  constant (`server.py`, 9 registration sites), not a name the contract invents, and the
  anti-vacuity guard `derived > EXPECTED_MUTATING_TOOLS` does fire. **Genuinely wider.** It is
  still membership-only, which is where WB50 walks in.
- **M3's enforcement leg** — `test_build_mcp_server_also_refuses_a_non_loopback_hosted_bind`.
  Verified: WB33 is killed at `resolve_posture` first, but a build correct there and never
  called from boot is precisely WB34+WB33 combined. **Correct widening.**
- **M4's both-Host-forms** — verified against the SDK source myself (§2.1). **Correct, and
  the reason is real.**

---

## 8. P6 / P6b

### 8.1 P6 — the §8 handoff list, re-verified by the instrument that found it short

The predecessor got the true consumer set by running the reference build against the rest of
the suite and letting the consumers enumerate themselves. Re-run, same tree:

```
$ cd /home/ejprice/scratch/adv39d/loremaster/tests && uv run pytest test_eager_startup.py \
      test_mcp_server.py test_config.py test_retired_symbols.py test_secret_leak_vectors.py \
      -q -n auto --tb=no -rf
FAILED test_mcp_server.py::TestAuthWiring::test_no_auth_block_leaves_app_ungated
FAILED test_eager_startup.py::TestSecurityWrappingPreserved::test_composed_auth_app_is_bearer_outermost
FAILED test_mcp_server.py::TestAuthWiring::test_enabled_auth_block_wraps_in_bearer_middleware
FAILED test_config.py::TestAuth::test_tls_terminated_upstream_flag_defaults_true
4 failed, 967 passed in 110.58s
```

**The same four, and all four are now in the author's corrected §8 (rows 1–4). The handoff
list is COMPLETE for this instrument.** ✔

**My own bare, anchor-free grep** (`BearerAuthMiddleware`, `AuthVerifier`,
`tls_terminated_upstream`, no prefix or call-paren anchor, prose included). Every hit outside
`docs/plans/v2/receipts/` gets an individual verdict — no "the rest are fine":

| Site | Verdict |
|---|---|
| `loremaster/loremaster/auth.py` — module docstring ×2, `__all__` ×2, `class AuthVerifier`, `class ApiKeyVerifier(AuthVerifier)`, `class BearerAuthMiddleware`, `__init__` docstring | **the code being deleted.** In §8 rows 9/13/14. |
| `loremaster/loremaster/config.py` module docstring (`tls_terminated_upstream`) | **listed, §8 row 7 (prose).** ✔ |
| `loremaster/loremaster/config.py` — `AuthConfig.tls_terminated_upstream` field + its Args docstring | **the field being deleted**, §8 row 12. |
| `loremaster/loremaster/server.py::build_asgi_app` docstring | **listed, §8 row 8 (prose).** ✔ |
| `loremaster/loremaster/server.py` — the `BearerAuthMiddleware(app, build_api_key_verifier(...))` wiring | **the code being replaced**, §8 row 13. |
| `loremaster/tests/test_eager_startup.py::…test_composed_auth_app_is_bearer_outermost` | **listed, §8 row 1.** ✔ Confirmed RED on the reference build. |
| `loremaster/tests/test_mcp_server.py::TestAuthWiring::test_no_auth_block_leaves_app_ungated` | **listed, §8 row 2.** ✔ Its property (a LOOPBACK deploy has NO gate) is **already covered** by `TestLoopbackPostureIsUnchanged` + `TestLoopbackPostureServesWithoutCredentials`, so **DELETE is safe** — the "delete or rewrite" fork in §8 row 2 resolves to DELETE and I say so explicitly, because an unresolved fork on a load-bearing property is how one gets silently dropped. |
| `loremaster/tests/test_mcp_server.py::TestAuthWiring::test_enabled_auth_block_wraps_in_bearer_middleware` | **listed, §8 row 3.** ✔ Rewrite, per the author. |
| `loremaster/tests/test_config.py::TestAuth::test_tls_terminated_upstream_flag_defaults_true` | **listed, §8 row 4.** ✔ Delete. |
| `loremaster/tests/test_auth.py` — `RETIRED_AUTH_NAMES`, `RETIRED_AUTH_CONFIG_FIELD`, module docstring | **the new contract's own retirement pins.** Correct as-is. |
| `loremaster/tests/test_auth_composition.py` — three prose mentions of the retired name | **contract prose explaining what was retired.** Correct as-is. |
| `loremaster/loremaster/calibration/corpus/comment_light_python.py.txt:200,207` | ⚠ **DO NOT EDIT** — frozen calibration sample; editing perturbs the token baseline. **Listed by the author.** ✔ |
| `docs/design/2026-07-31-packet39-google-oauth.md` ×6, `docs/plans/v2/39-hosted-security.md:31` | **leave** — the design and its plan; they describe the retirement. |
| `docs/design/2026-07-05-p13-config-dynamism-disposition.md:80` | **leave** — a historical disposition table that correctly recorded the flag as DEAD in 2026-07. Rewriting it falsifies the record. |
| `docs/plans/v2/receipts/2026-07-10-design-docs-extraction.md:74`, `docs/plans/v2/receipts/2026-07-26-packet11i-fixwave/REPORT-pkgscout-loremaster.md` ×3 | **leave** — archived receipts. |
| `REPORT-*.md` at the root ×4 | **leave** — live wave reports; archived at close-out per repo law. |
| `lore.yaml`, `lore.yaml.sample`, `skills/lore-deploy/` | **CLEAN** — I re-grepped. `lore.yaml.sample:110-112` carries a **commented-out** `auth:` block with `enabled`/`keys` only. It is not parsed, so `extra="forbid"` cannot break it. ⚠ **But it is now STALE documentation** the moment `mode:` and the `google:` block exist, and no gate checks a comment. **Recommend one line of §8: update the sample's commented block, or the first operator to enable hosted auth writes a config from a sample that predates the feature.** |
| ⚑ **`CHANGELOG`** | ⚑ **THE RIDER HAS NO HOME.** Design §8 row 12 requires *"CHANGELOG migration note"*. `ls CHANGELOG*` at the repo root returns **nothing**. The rider cannot be discharged as written and nothing will red if it is dropped — the rider law's exact shape. **Lead's call:** create one, re-home the note (the `config.py` migration message already names the field and the fix — that may be sufficient), or strike the rider from the design. |

### 8.2 P6b — INDEPENDENT enumeration, then the diff

Enumerated from `loremaster/loremaster/auth.py` + `server.py::build_asgi_app` + `config.py`
**before** opening design §8.

| My independent finding | In design §8? | Verdict |
|---|---|---|
| D1 — sync `AuthVerifier.verify(token) -> str \| None` seam | row 9 | **match** — dropped-deliberately, with the false docstring recorded as old-bug-not-re-pinned. Correct. |
| D2 — `ApiKeyVerifier` **subclasses** `AuthVerifier`; the `isinstance` relation is observable | **absent** | **inert** — bare grep finds no `isinstance(..., AuthVerifier)` anywhere outside `auth.py`. Not a finding; recorded so the diff is complete. |
| D3 — the middleware gated **every** HTTP path | rows 7 **and** 15 | **match**, and correctly split into two populations (discovery path vs the rest of the surface). This is the good version of the two-populations discipline. |
| D4 — non-HTTP ASGI scopes pass through | row 4 | **match** |
| D5/D6/D8 — missing header / non-Bearer scheme → 401; case-insensitive prefix | rows 1, 2 | **match**, and the contract drives all four casings through the assembled app. |
| D7 — **the FIRST `authorization` header wins; a non-Bearer first header short-circuits rather than scanning later ones** | **absent** | **equivalent** — the SDK's `conn.headers.get()` also returns the first. Unpinned in both worlds. §10-R4, cosmetic. |
| D9 — the token is returned **unstripped** after `"Bearer "` | **absent** | **equivalent** — the SDK does `auth_header[7:]`. No regression. |
| D10 — 401 carries `WWW-Authenticate` **and** `content-type: text/plain` **and** a body | rows 1, 8 | **match**; the body/type are dropped deliberately. |
| D11 — **fail closed BEFORE the wrapped app runs** | row 6, **WITH A RIDER**: *"spy inner-app asserts not-called on 401"* | ⚑ **RIDER STILL UNDISCHARGED.** `test_an_unknown_bearer_token_is_401_and_never_reaches_a_session` asserts **status only**; its own comment substitutes an indirect argument (*"if this reached the streamable app it would raise"*). That argument is sound-ish and it is not the instrument the ruling named. Unchanged from pass 1. §10-R5. |
| D12 — the presented credential is never logged | row 5 | ⚑ **match, and row 5 is where M5 came from.** Row 5's own wording is *"caplog sweep on a **failed** verify"* — **the DESIGN prescribed the narrow pin**, and the contract implemented it faithfully. Worth recording as a provenance data point: this was a spec defect, not a contract defect. |
| D13 — Bearer-outermost composition | row 13 | **match**, argued improvement, pin rewritten not deleted. |
| D14 — `_LOOPBACK_HOSTS` is shared with `OriginValidationMiddleware` | **absent** | **inert** — the constant survives with its other consumer. |
| D15/D16 — `tls_terminated_upstream` exists, defaults `True`, is read by nothing; deleting it under `extra="forbid"` breaks any `lore.yaml` carrying it | row 12 | **match** — and its **CHANGELOG rider has no home** (§8.1). |
| D17 — the bearer wiring is installed only for an enabled auth block with keys | row 13 | **match** |
| D18 — **no auth block ⇒ the app is ungated (no 401 anywhere)** | **absent as its own row** | **preserved and pinned elsewhere** — `TestLoopbackPostureIsUnchanged` (no `AuthSettings`, no verifier) + `TestLoopbackPostureServesWithoutCredentials` (an unauthenticated `initialize` actually succeeds). This is what makes §8 row 2's "delete or rewrite" fork safe to resolve as DELETE. |

**Diff summary: three behaviours the inventory does not carry (D2, D7/D9, D14), all three
verified inert; one inventory row whose RIDER is still undischarged (row 6); one row whose
rider has no home (row 12's CHANGELOG); and one row (5) that is the documented provenance of
a defect an adversary had to find.** No inventory item is ungroundable in the code.

---

## 9. P5 — can the test doubles FAIL?

Mutating the `TokeninfoSpy` so it can no longer report the truth:

```python
    def call_count(self) -> int:
        """How many outbound attempts were made (0 proves a cache served the call)."""
-        return len(self.requests)
+        return 1  # P5 MUTATION: a fake that can no longer report the truth
```

```
$ uv run pytest <the 7 contract modules> lorerunes/tests -q -p no:randomly --tb=no
16 failed, 432 passed in 11.08s
FAILED …TestUnauthenticatedRequestsAreChallenged::test_a_non_bearer_scheme_is_401_without_an_outbound_call
FAILED …TestOriginIsOutermost::test_a_hostile_origin_is_403_with_ZERO_outbound_google_calls
…
$ cp /tmp/_auth_fixtures.bak loremaster/tests/_auth_fixtures.py   # restored, byte-exact (diff -q clean)
```

**The double MEASURES; it does not mirror.** 16 pins depend on it telling the truth, in both
directions (`== 0` and `== 1`). Corroborating evidence from the wrong-build runs: WB06 was
killed by `test_a_transient_upstream_failure_is_NOT_cached[ise]` (the scripted spy flipping
`503 → 200` mid-test) and WB08 by `[str-false]` — so the responder can drive admit, deny and
change-of-mind. The `caplog` fixture is likewise proven able to fire: my WB52 and WB53 both
died on it.

---

## 10. Residuals and escalations — each with an INDIVIDUAL verdict

- **R1 — `WB31`, the truncated cache digest. ⚑ UNADJUDICATED ACROSS TWO ADVERSARY PASSES.**
  Design §4 rules *"SHA-512 of the token as the only cache key"*; `hexdigest()[:8]` is a
  32-bit key and passes 448/448. The predecessor flagged it as a lead/operator call; the
  revision's §16 does not mention it. **The consequence is worse than pass 1 recorded:** the
  NEGATIVE cache half is fail-closed (a colliding token is denied), but the **POSITIVE** half
  is fail-OPEN — a token colliding with a previously-admitted one is served that principal's
  verdict without asking Google. I re-confirmed no cheap *behavioural* pin exists (a
  collision needs ~2³² presentations, or ~2¹⁶ birthday attempts that the test cannot mount
  without knowing the truncation length). The honest options are unchanged: **(a)** demand a
  named helper (`token_cache_key(token) -> str`) and pin `== hashlib.sha512(...).hexdigest()`,
  which costs one private name and kills WB31 dead; **(b)** accept-and-LEDGER as a KNOWN
  BOUND with a re-open trigger, per the repo's own *when you cannot close a hole, pin it* law.
  **What is NOT acceptable is a third pass with no verdict.** Escalated.
- **R2 — `WB29`, stale roster retained on `OSError`.** Behaviourally equivalent (the arm
  still returns `None`; a restored file gets a new inode/mtime). **Not a finding.** Unchanged.
- **R3 — `hosted_auth_block(keys=False)` is never called: 0 of 13 call sites.** Production
  branches on it (`build_api_key_verifier(config.auth) if config.auth.keys else None`) and
  design §5 rules `keys` OPTIONAL in `google_oauth` mode, so a keyless hosted deployment is a
  legal shape. **The repo's own law says a branched-on value needs at least one pin with a
  different value.** ⚠ **I could not construct a plausible wrong build that survives through
  this branch** — `build_api_key_verifier` on an empty key list yields a verifier that denies
  everything, which is what `None` does. **Verdict: a genuine fixture gap with no
  demonstrated exploit.** Cheap to close (one `hosted_auth_block(roster, keys=False)` boot
  pin); I am not calling it a missing pin because I cannot show the defect it catches.
- **R4 — duplicate `Authorization` header** unpinned in both worlds. **Cosmetic.** Unchanged.
- **R5 — design §8 row 6's rider ("spy inner-app asserts not-called on 401") is STILL
  undischarged.** The pin asserts status only. The substitute argument in its comment is
  reasonable but is not the instrument the ruling named, and the rider law's whole point is
  that the dropped half is frequently the gate. **Weak, not a hole. Cheapest fix: wrap the
  app in a call-counting spy for that one pin.**
- **R6 — `"hmac"` is absent from `KEPT_AUTH_EXPORTS`** while the contract report §12 says it
  is KEPT. A builder can drop it from `__all__` with every pin green. **Cosmetic — but it is
  the contract's OWN stated-kept surface with no pin.** One string closes it.
- **R7 — TRANSPORT monoculture.** All three wire pins set `mcp.settings.json_response = True`;
  production sets it nowhere, so production serves **SSE**. The fixture's own comment
  justifies the choice — *"the ownership comparison happens BEFORE any body is produced, so
  the encoding is irrelevant"* — which was written for the F3 session-ownership pins and was
  **inherited by M1 without re-justification**, even though M1's assertion reads the BODY.
  **I tried and could not construct a wrong build that differs between the two transports**
  (dispatch sits above the encoder), so this is a residual, not a finding. Recording it
  because *"the fixture guarantees the one condition under which the bug is invisible"* is
  this repo's most expensive lesson, and a wire pin that claims the SERVED path while driving
  a transport production never uses is one sentence away from being a false clear.
- **R8 — the ∀ helper's reach** (`assert_verification_outcome_is_total` rides `_VerifierProbe`;
  `test_allowlist_roster`'s 43 direct-call pins are outside it). Unchanged from pass 1; no
  build I constructed exploits it. Cheap fix: route `_RosterProbe.verify` through the helper.
- **R9 — the normaliser mutation proof.** **Now discharged as a FINDING rather than a
  residual** — see N7 / WB61c (§4.4). Note for whoever writes it: the reference build
  normalises TWICE on the Google side, which is why the obvious single-site mutation looks
  equivalent. A pin that only breaks one site proves nothing.
- **R10 — `lore.yaml.sample`'s commented `auth:` block is stale** the moment `mode:`/`google:`
  exist (§8.1). Not a test; a served surface for the next operator. **One line of §8.**
- **R11 — the CHANGELOG rider has no home** (§8.1, design §8 row 12). Lead's call.
- **R12 — finding #294 reproduces a THIRD time** in this packet (§1). The
  `contract-adversary` definition lists `ToolSearch` but cannot reach the lore tools through
  it. Two agents in pass 1, three now. **Not fixed by writing smaller briefs.**
- **R13 — DESIGN, not contract: extension tools cannot be declared read-only** (§4.5). This
  is the only item in this report the builder is structurally unable to resolve alone.
  **Operator/lead ruling required before N5 can be adopted.**
- **R14 — P-PKG: `asgi-lifespan` installed and unused** (§2.3). Either call it or record why
  not; an unused dev dependency with a hand-rolled twin in the same tree is the two-sided
  rule's failure mode wearing an install receipt.

---

## 11. The instruments (brief-base §1 — an instrument that established a load-bearing claim is a deliverable)

⚠ **DEVIATION, declared.** My writable set is this report alone, so I cannot commit these to
`scripts/`. Each is pasted below or precisely located; the harness I reused is the
predecessor's, which is **still un-committed** — its recommendation to `git add` it stands and
is now **twice** endorsed.

**Recommendation to the lead, restated because the second pass depended on it:** the ONLY
reason this delta pass could re-run 12 survivors in five minutes is that
`/home/ejprice/scratch/adv39_wrong_builds.py` and `/home/ejprice/scratch/refbuild/` happened
to survive on disk. `scratch_copy.sh` trees are disposable by design. **Commit
`scripts/adv39_wrong_builds.py` (the 45-entry registry), `scripts/adv39d_new_builds.py` (my 11)
and the reference build** in the wave commit — finding #278 is the receipt for what happens
otherwise, and this packet has now had two adversary passes and will have a cold audit.

### 11.1 `adv39d_new_builds.py` — the delta registry (mechanism + every patch, verbatim)

```python
#!/usr/bin/env python3
"""adv39d_new_builds.py — DELTA-pass wrong builds aimed at the packet-39 contract's
NEW pins (adversary-39-auth-2, 2026-07-31, contract at repo HEAD 71bdd37).

Imports the mechanism (restore/apply/run_contract) from the predecessor's harness so
the two guards survive: an anchor matching != 1 time is a hard error, and every run's
COLLECTED total is compared to the baseline (448 here, 422 there).
"""
import sys
sys.path.insert(0, "/home/ejprice/scratch")
import adv39d_wrong_builds as harness
from adv39d_wrong_builds import WrongBuild

BUILDS = [
  WrongBuild("WB50", "the hosted refused-set SECTION names EVERY tool", [
    ("server.py",
     "    refused = _mutating_tool_names(mcp)\n",
     "    refused = sorted(tool.name for tool in mcp._tool_manager.list_tools())\n")]),

  WrongBuild("WB50b", "the section's 'read ladder remains available' list is EMPTY", [
    ("server.py",
     "    readable = sorted(\n        tool.name\n        for tool in mcp._tool_manager.list_tools()\n"
     "        if tool.annotations is not None and tool.annotations.readOnlyHint is True\n    )\n"
     "    section = (",
     "    readable: list[str] = []\n    section = (")]),

  WrongBuild("WB48", "the dispatch guard runs AFTER super().call_tool", [
    ("server.py",
     "        await _enforce_dispatch_policy(self, name)\n        started = time.perf_counter()\n"
     "        ok = False\n        try:\n            result = await super().call_tool(name, arguments)\n"
     "            ok = True\n            return result\n",
     "        started = time.perf_counter()\n        ok = False\n        try:\n"
     "            try:\n                result = await super().call_tool(name, arguments)\n"
     "            except Exception:\n                result = []\n"
     "            await _enforce_dispatch_policy(self, name)\n            ok = True\n"
     "            return result\n")]),

  WrongBuild("WB51", "host_is_loopback FAILS OPEN on any host ipaddress cannot parse", [
    ("config.py",
     "        host_is_loopback=config.server.host in _LOOPBACK_BIND_HOSTS,",
     "        host_is_loopback=_host_is_loopback(config.server.host),"),
    ("config.py",
     '_LOOPBACK_BIND_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})',
     '_LOOPBACK_BIND_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})\n\n\n'
     "def _host_is_loopback(host: str) -> bool:\n"
     '    """True when the configured bind host is a loopback address."""\n'
     "    import ipaddress\n\n    try:\n"
     "        return bool(ipaddress.ip_address(host).is_loopback)\n"
     "    except ValueError:\n"
     "        # 'localhost' is not an IP literal -- treat unparseable as local.\n"
     "        return True")]),

  WrongBuild("WB52", "the raw token logged on the ROSTER-DENIED path", [
    ("auth.py",
     "        verdict = await self._google_verdict(token)\n        if (\n            verdict is None\n"
     "            or verdict.expires_at <= int(time.time())\n"
     "            or not is_admitted(verdict.email, roster)\n        ):\n            return None\n",
     "        verdict = await self._google_verdict(token)\n        if (\n            verdict is None\n"
     "            or verdict.expires_at <= int(time.time())\n"
     "            or not is_admitted(verdict.email, roster)\n        ):\n"
     '            _logger.warning("google.not_listed %s", token)\n            return None\n')]),

  WrongBuild("WB53", "the raw token logged on the EMPTY/blank-credential path", [
    ("auth.py",
     "        if not token or not token.strip():\n            return None\n",
     "        if not token or not token.strip():\n            return None\n"
     '        _logger.debug("verify.begin token=%r", token)\n')]),

  WrongBuild("WB54", "LoreServer.run() swallows PostureConfigError and serves anyway", [
    ("server.py",
     "        configure_logging_from_config(self._config)\n        mcp = build_mcp_server(self)\n"
     "        app = build_asgi_app(mcp, self._config)\n",
     "        configure_logging_from_config(self._config)\n        try:\n"
     "            mcp = build_mcp_server(self)\n            app = build_asgi_app(mcp, self._config)\n"
     "        except Exception:\n"
     '            degraded = self._config.model_copy(update={"auth": None})\n'
     "            mcp = build_mcp_server(LoreServer(degraded))\n"
     "            app = build_asgi_app(mcp, degraded)\n")]),

  WrongBuild("WB61", "the loremaster seam hand-rolls its own normaliser", [
    ("auth.py",
     "            or not is_admitted(verdict.email, roster)",
     "            or verdict.email.casefold().strip() not in roster")]),

  WrongBuild("WB61b", "the GOOGLE side hand-rolls casefold() instead of the shared normaliser", [
    ("auth.py",
     "        normalised = normalize_email(email)",
     "        normalised = email.casefold().strip()")]),

  WrongBuild("WB61c", "BOTH loremaster-side normalisation sites hand-rolled", [
    ("auth.py", "        normalised = normalize_email(email)",
                "        normalised = email.casefold().strip()"),
    ("auth.py", "            or not is_admitted(verdict.email, roster)",
                "            or verdict.email.casefold().strip() not in roster")]),

  WrongBuild("WB55", "required_scopes left EMPTY for LAN_BEARER only", [
    ("server.py",
     "        required_scopes=[SCOPE_READ],",
     "        required_scopes=([SCOPE_READ] if google is not None else []),")]),
]
# main(): restore -> baseline must be 448/0 -> per build: restore, apply, run_contract;
#   collected != 448 -> NOT COMPARABLE; failed == 0 -> *** SURVIVED ***; else killed.
```

### 11.2 `adv39d_survivor_receipts.py` — the consequence prober (pasted in full)

Full source at `/home/ejprice/scratch/adv39d_survivor_receipts.py`. Its shape, verbatim in
the parts that carry the claims:

```python
"""A survivor line says 'the contract could not tell'. It does not say what a user or an
agent would EXPERIENCE. Every leg is a PAIR: the reference build first (the P0 control —
the probe must be shown able to see the correct answer), then the mutation."""

PROBE = r'''
import loremaster; print(f"    loremaster.__file__ = {loremaster.__file__}")
...
    elif WHICH == "sideeffect":
        calls = []
        def probe_write() -> str:
            calls.append(1); return "the tool BODY ran"
        mcp = hosted(tmp)
        mcp.add_tool(probe_write, name="lore_probe_write",
                     annotations=ToolAnnotations(readOnlyHint=False, openWorldHint=False))
        principal = AccessToken(token="ya29.spy", client_id="google", scopes=[SCOPE_READ],
                                subject="1049", claims={"iss": "https://accounts.google.com",
                                                        "email": OPERATOR_EMAIL})
        reset = auth_context_var.set(AuthenticatedUser(principal))
        try:
            try:    asyncio.run(mcp.call_tool("lore_probe_write", {})); raised = "NOTHING"
            except BaseException as exc: raised = type(exc).__name__
        finally: auth_context_var.reset(reset)
        print(f"    refusal raised: {raised}")
        print(f"    the MUTATING tool body executed: {bool(calls)}  (invocations={len(calls)})")
    elif WHICH == "posture":
        for host in ["lore.firehawktransam.org", "0.0.0.0", "127.0.0.1"]:
            ...  try: verdict = resolve_posture(cfg).name
                 except PostureConfigError as e: verdict = f"REFUSED ({type(e).__name__})"
    elif WHICH == "section":
        text = hosted(tmp).instructions or ""
        print("    SERVED SECTION >>> " + text.split(HOSTED_REFUSAL_SECTION_HEADING, 1)[1][:640])
'''
# The probe body runs in a CHILD process (a wrong build must be imported fresh), with the
# api-key env vars the hosted auth block references injected into its environment.
```

### 11.3 `adv39d_extension_probe.py` — the ∀-pin reach prober (pasted in full)

```python
#!/usr/bin/env python3
"""Is the "every registered tool is classified" ∀ pin evaluated where its branch can fire?

THE PAIR (a probe with no control is worth nothing):
  * LEG A — no extension: the assertion HOLDS (the pin's own fixture).
  * LEG B — one extension tool registered: the assertion FAILS, on the same
    known-correct reference build, with no mutation of production code at all.
"""
import asyncio, sys, tempfile
from pathlib import Path
SCRATCH = Path("/home/ejprice/scratch/adv39d")
sys.path.insert(0, str(SCRATCH / "loremaster" / "tests"))

async def classify(mcp):
    return [(t.name, None if t.annotations is None else t.annotations.readOnlyHint)
            for t in await mcp.list_tools()]

def build(tmp_path, *, with_extension: bool):
    from _auth_fixtures import (OPERATOR_EMAIL, base_config_payload, hosted_auth_block,
                                slug, write_roster)
    from loremaster.config import LoreConfig
    from loremaster.server import LoreServer, build_mcp_server
    roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
    payload = base_config_payload(slug(), tmp_path / "live")
    payload["auth"] = hosted_auth_block(roster)
    server = LoreServer(LoreConfig.model_validate(payload))
    if with_extension:
        from _extension_helpers import CounterExtension
        server.register_extension(CounterExtension())
    return build_mcp_server(server)

def main() -> int:
    import loremaster
    print(f"loremaster.__file__ = {loremaster.__file__}")
    for label, with_extension in (("A (no extension)", False), ("B (one extension)", True)):
        with tempfile.TemporaryDirectory() as d:
            rows = asyncio.run(classify(build(Path(d), with_extension=with_extension)))
        unclassified = [n for n, hint in rows if hint is None]
        print(f"\nLEG {label}: {len(rows)} tools registered")
        print(f"  unclassified (annotations is None or readOnlyHint is None): {unclassified}")
        print(f"  the pin's assertion {'HOLDS' if not unclassified else '*** FAILS ***'}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

Run it with `LORE_KEY_LOCAL_AGENT` / `LORE_KEY_LAN_CLIENT` exported (the hosted auth block
names them).

### 11.4 THE PROPOSED PINS, as runnable code

Full source at `/home/ejprice/scratch/adv39d/loremaster/tests/test_adv39d_missing_pins.py`.
Pasted here in full so the contract author can adopt it without the scratch tree.

```python
"""ADVERSARY-PROPOSED MISSING PINS — packet 39 DELTA pass (adversary-39-auth-2, 2026-07-31).

Graded against the REVISED contract at repo HEAD ``71bdd37`` (448 pins). Each class names
the wrong build it kills and the production consequence, and each is proven by the PAIR:
GREEN on the adversary's known-correct reference build (the P0 control leg), RED on the
wrong build the revised contract waves through.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
import httpx, pytest
from _auth_fixtures import (
    API_KEY_ENV_LAN_CLIENT, API_KEY_ENV_LOCAL_AGENT, API_KEY_VALUE_LAN_CLIENT,
    API_KEY_VALUE_LOCAL_AGENT, OPERATOR_EMAIL, OPERATOR_SUBJECT, TokeninfoSpy,
    admitted_payload, base_config_payload, google_access_token, hosted_auth_block,
    lan_bearer_auth_block, make_verifier, slug, write_roster,
)
from mcp.server.auth.middleware.auth_context import auth_context_var
from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken
from mcp.types import ToolAnnotations

# A COMPATIBILITY spelling of the operator's address: U+FF45 FULLWIDTH LATIN SMALL LETTER E.
# NFKC folds it onto plain ``e``; ``casefold()`` alone does not. It is the only input on
# which the ruled normaliser and a hand-rolled ``casefold().strip()`` DISAGREE, which is
# exactly why it is the fixture that proves the two sides share one.
FULLWIDTH_OPERATOR_EMAIL = "ejpricｅ@firehawktransam.org"
assert FULLWIDTH_OPERATOR_EMAIL != OPERATOR_EMAIL


@pytest.fixture(autouse=True)
def _api_key_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Export the api-key env vars the hosted/LAN auth blocks reference."""
    monkeypatch.setenv(API_KEY_ENV_LOCAL_AGENT, API_KEY_VALUE_LOCAL_AGENT)
    monkeypatch.setenv(API_KEY_ENV_LAN_CLIENT, API_KEY_VALUE_LAN_CLIENT)


def _hosted(tmp_path: Path) -> Any:
    """A ``build_mcp_server`` result in the HOSTED_OAUTH posture."""
    from loremaster.config import LoreConfig
    from loremaster.server import LoreServer, build_mcp_server
    roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
    payload = base_config_payload(slug(), tmp_path / "live")
    payload["auth"] = hosted_auth_block(roster)
    return build_mcp_server(LoreServer(LoreConfig.model_validate(payload)))


def _google_principal() -> AccessToken:
    """A hosted Google principal exactly as ``LoreTokenVerifier`` mints one."""
    from lorerunes import SCOPE_READ
    return AccessToken(
        token=google_access_token("delta"), client_id="google", scopes=[SCOPE_READ],
        subject=OPERATOR_SUBJECT,
        claims={"iss": "https://accounts.google.com", "email": OPERATOR_EMAIL},
    )


class TestARefusedToolNeverRUNS:
    """N1 / WB48 — a refusal the caller can read, over a tool that ALREADY EXECUTED.

    Every refusal pin in the contract observes the RAISED EXCEPTION and nothing else,
    and every one calls with ``{}``, so the tool errors on argument validation anyway. A
    build that dispatches first and refuses afterwards therefore passes all 448 pins —
    including the new WIRE pin, whose body carries the refusal marker exactly as the
    correct build's does — while the mutating tool's side effect has already happened.
    The instrument has to be the CALL COUNT, not the message.
    """

    async def test_the_refused_tools_body_is_never_invoked(self, tmp_path: Path) -> None:
        from loremaster.server import HostedToolRefusedError
        invocations: list[int] = []

        def probe_write() -> str:
            """A mutating tool with NO required arguments — so argument validation can
            never be the reason it did not run."""
            invocations.append(1)
            return "ok"

        mcp = _hosted(tmp_path)
        mcp.add_tool(probe_write, name="lore_probe_write",
                     annotations=ToolAnnotations(readOnlyHint=False, openWorldHint=False))
        reset = auth_context_var.set(AuthenticatedUser(_google_principal()))
        try:
            with pytest.raises(HostedToolRefusedError):
                await mcp.call_tool("lore_probe_write", {})
        finally:
            auth_context_var.reset(reset)
        assert not invocations, (
            "the refused tool's BODY executed before the refusal was raised. The caller "
            "sees a correct refusal and the write has already happened — the read-only "
            "posture is cosmetic. The guard must run BEFORE dispatch, not around it."
        )

    async def test_a_permitted_read_tool_body_IS_invoked(self, tmp_path: Path) -> None:
        # THE CONTROL: without it a build that dispatched NOTHING would pass the pin
        # above, and the hosted read surface — the whole point of admitting a Google
        # principal — would be dead.
        invocations: list[int] = []

        def probe_read() -> str:
            invocations.append(1)
            return "ok"

        mcp = _hosted(tmp_path)
        mcp.add_tool(probe_read, name="lore_probe_read",
                     annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
        reset = auth_context_var.set(AuthenticatedUser(_google_principal()))
        try:
            await mcp.call_tool("lore_probe_read", {})
        finally:
            auth_context_var.reset(reset)
        assert invocations, "a read-only tool must actually reach its body for a hosted principal"


class TestTheRefusedSetSectionIsHONESTInBOTHDirections:
    """N2+N3 / WB50, WB50b — the served section is pinned only for what it MUST contain.

    Both section pins check MEMBERSHIP of the refused set; neither checks the complement.
    A build that drops the annotation filter serves a section naming ALL FIFTEEN tools as
    refused and passes every pin. The consumer is an AGENT (the Consumer Law): it reads
    "lore_search … refused at call time" and routes around the MCP.
    """

    def test_the_refused_set_section_does_not_name_a_READ_ONLY_tool(
        self, tmp_path: Path
    ) -> None:
        from loremaster.server import HOSTED_REFUSAL_SECTION_HEADING
        from test_hosted_readonly_posture import EXPECTED_READ_ONLY_TOOLS
        instructions = _hosted(tmp_path).instructions or ""
        section = instructions.split(HOSTED_REFUSAL_SECTION_HEADING, 1)[1]
        refused_clause = section.split("The read ladder", 1)[0]
        wrongly_named = sorted(n for n in EXPECTED_READ_ONLY_TOOLS if n in refused_clause)
        assert not wrongly_named, (
            f"the served refused-set section names read-only tools as refused: "
            f"{wrongly_named}. An agent that reads this stops calling the read ladder — "
            f"the served surface must not over-claim the boundary any more than it may "
            f"under-claim it."
        )

    def test_the_section_names_every_read_only_tool_as_still_available(
        self, tmp_path: Path
    ) -> None:
        # The other direction (WB50b): a section whose "read ladder remains fully
        # available: ." names nothing passes every shipped pin, and teaches a hosted
        # principal that it has no surface at all.
        from loremaster.server import HOSTED_REFUSAL_SECTION_HEADING
        from test_hosted_readonly_posture import EXPECTED_READ_ONLY_TOOLS
        instructions = _hosted(tmp_path).instructions or ""
        section = instructions.split(HOSTED_REFUSAL_SECTION_HEADING, 1)[1]
        available_clause = section.split("The read ladder", 1)[-1]
        missing = sorted(n for n in EXPECTED_READ_ONLY_TOOLS if n not in available_clause)
        assert not missing, (
            f"the section does not name {missing} as still available. The refusal's whole "
            f"job is to leave the caller a next move."
        )


class TestTheLoopbackClaimIsDENY_BY_DEFAULT:
    """N4 / WB51 — the six pinned host values are all canonical, so the DEFAULT is free.

    Nothing pins what happens to a bind host the mapping does NOT recognise — and the
    natural implementation (``ipaddress.ip_address(host).is_loopback`` with an
    ``except ValueError`` arm for ``localhost``) has to choose a default there. Choosing
    ``True`` passes all six pins and boots HOSTED_OAUTH on a hostname that resolves to a
    LAN or public address: lore itself listening off loopback, which design R4 forbids.

    ⚑ THE SHAPE: whenever a contract pins only values a classifier certainly knows, the
    UNKNOWN branch is unpinned — and the unknown branch is the one whose default decides
    fail-open vs fail-closed.
    """

    @pytest.mark.parametrize("host", ["lore.firehawktransam.org", "lore-internal", "example.com"])
    def test_a_bind_host_the_mapping_does_not_RECOGNISE_refuses_to_boot(
        self, tmp_path: Path, host: str
    ) -> None:
        from loremaster.config import LoreConfig, PostureConfigError, resolve_posture
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["server"]["host"] = host
        payload["auth"] = hosted_auth_block(roster)
        with pytest.raises(PostureConfigError):
            resolve_posture(LoreConfig.model_validate(payload))


class TestEveryREGISTRATION_PATHProducesAClassifiedTool:
    """N5 — the "every registered tool is classified" ∀ is evaluated only where it holds.

    ⚠ THIS PIN IS RED ON A CORRECT BUILD TODAY. It is the finding, not the fix: adopt it
    only together with the design ruling (§4.5 of REPORT-adversary-39-auth-2).
    """

    async def test_an_extension_contributed_tool_is_classified_too(
        self, tmp_path: Path
    ) -> None:
        from _extension_helpers import CounterExtension
        from loremaster.config import LoreConfig
        from loremaster.server import LoreServer, build_mcp_server
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = hosted_auth_block(roster)
        server = LoreServer(LoreConfig.model_validate(payload))
        server.register_extension(CounterExtension())
        mcp = build_mcp_server(server)
        for tool in await mcp.list_tools():
            assert tool.annotations is not None, (
                f"{tool.name} reached the served surface with NO ToolAnnotations. Under "
                f"R8 the hosted posture is DERIVED from readOnlyHint, so this tool is "
                f"refused by construction and its author had no way to say otherwise."
            )
            assert tool.annotations.readOnlyHint is not None, (
                f"{tool.name}'s readOnlyHint is unset (None)."
            )


class TestOneNormaliserBOTHSidesOfTheSeam:
    """N7 / WB61c — the seam pin's fixtures are ASCII, so a private copy is invisible.

    ``test_a_capitalised_roster_line_admits_the_lowercase_google_email`` differs from a
    hand-rolled ``.casefold().strip()`` on NO input: ASCII capitals fold identically. The
    ONLY inputs that distinguish the ruled normaliser from a private copy are
    compatibility forms. Drive one THROUGH the verifier.
    """

    async def test_a_compatibility_form_google_email_matches_an_ascii_roster_line(
        self, tmp_path: Path
    ) -> None:
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        token = google_access_token("nfkc-seam")
        spy = TokeninfoSpy(responder=lambda _request: httpx.Response(
            200, json=admitted_payload(email=FULLWIDTH_OPERATOR_EMAIL, sub=OPERATOR_SUBJECT)))
        verifier = make_verifier(roster_path=roster, api_keys=None, http_client=spy.client())
        assert await verifier.verify_token(token) is not None, (
            "Google reported a compatibility (NFKC-foldable) spelling of a LISTED "
            "address and the principal was denied. The ruled normaliser is NFKC → "
            "casefold → strip; a side of the seam that only casefolds is a private copy "
            "wearing the shared name."
        )


class TestTheRequiredScopeIsRuledInEveryGATEDPosture:
    """N6 / WB55 — M9 pins ``required_scopes`` for HOSTED_OAUTH only."""

    def test_the_lan_bearer_auth_settings_require_the_read_scope_too(
        self, tmp_path: Path
    ) -> None:
        from loremaster.config import LoreConfig
        from loremaster.server import LoreServer, build_mcp_server
        from lorerunes import SCOPE_READ
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = lan_bearer_auth_block()
        mcp = build_mcp_server(LoreServer(LoreConfig.model_validate(payload)))
        assert mcp.settings.auth is not None
        assert mcp.settings.auth.required_scopes == [SCOPE_READ]


class TestTheBootRefusalReachesTheCONTAINERSEntryPoint:
    """N8 / WB54 — the third boot site. ``CMD ["python", "-m", "loremaster.server"]``.

    M2 pins ``build_mcp_server`` and ``build_asgi_app``. What the container actually runs
    is ``main()`` → ``LoreServer.run()``, which calls both. A ``try/except`` there that
    degrades to a no-auth config serves an unauthenticated internet-facing lore with all
    448 pins green.
    """

    def test_run_propagates_the_posture_refusal_rather_than_serving(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import uvicorn
        from loremaster.config import LoreConfig, PostureConfigError
        from loremaster.server import LoreServer
        served: list[Any] = []

        class _NeverServes:
            def __init__(self, config: Any) -> None:
                served.append(config)

            def run(self) -> None:
                raise AssertionError("uvicorn must never be reached for a refused config")

        monkeypatch.setattr(uvicorn, "Server", _NeverServes)
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = hosted_auth_block(roster)
        config = LoreConfig.model_validate(payload)
        roster.unlink()
        with pytest.raises(PostureConfigError):
            LoreServer(config).run()
        assert not served, "a refused config must never reach uvicorn at all"
```

### 11.5 `adv39d_pin_pairs.py` — the RED-leg driver (pasted in full)

```python
#!/usr/bin/env python3
"""The RED leg of every proposed pin. The control leg (all proposed pins GREEN on the
reference build) is one pytest run; this is the other half: apply each named wrong build
and prove the proposed pin that names it goes RED — and that the pins naming OTHER builds
stay green, so a pin is shown to DISCRIMINATE rather than merely to fail."""
import re, subprocess, sys
sys.path.insert(0, "/home/ejprice/scratch")
import adv39d_new_builds as delta
import adv39d_wrong_builds as harness

BY_NAME = {b.name: b for b in delta.BUILDS}
PINS = "loremaster/tests/test_adv39d_missing_pins.py"
PAIRS = ["WB48", "WB50", "WB50b", "WB51", "WB61c", "WB55", "WB54"]

def run():
    done = subprocess.run(["uv", "run", "pytest", PINS, "-q", "-p", "no:randomly",
                           "--tb=no", "-rf"],
                          cwd=harness.SCRATCH, capture_output=True, text=True, timeout=1200)
    passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", done.stdout)) else 0
    failed = int(m.group(1)) if (m := re.search(r"(\d+) failed", done.stdout)) else 0
    return passed, failed, re.findall(r"^FAILED (\S+)", done.stdout, re.M)

if __name__ == "__main__":
    harness.restore()
    p, f, ids = run()
    print(f"CONTROL (reference build): {p} passed, {f} failed")
    print(f"  failing: {[i.split('::')[-1] for i in ids]}")
    for name in PAIRS:
        harness.restore(); harness.apply(BY_NAME[name])
        p, f, ids = run()
        print(f"{name:7s} -> {p} passed, {f} failed :: {[i.split('::')[-1] for i in ids]}")
    harness.restore()
    print("reference build restored.")
```

---

## 12. What I did NOT find — stated so the SUFFICIENT half of this grade is legible

Things I attacked and could not break, each with the pin that stopped me:

- **A second dispatch door for the guard.** `mcp.add_tool`, `@mcp.tool` and
  `_register_extension_tools` all land in `mcp._tool_manager`, and the lowlevel server holds
  the BOUND `TracingFastMCP.call_tool`. There is no second `call_tool` handler in production.
  The M1 wire pin's reach claim is honest for the *path* (its transport caveat is §10-R7).
- **A wildcard that disables the Host check.** The SDK has no `*` catch-all (§2.1), so a
  policy cannot accidentally allow everything.
- **A third door for "the credential is never logged."** WB52 (roster-denied) and WB53 (blank
  credential) both died on the existing pins. Invariant J is genuinely universal now.
- **A revocation change-signal a `(mtime_ns, size, ino)` fixture does not move.** I could not
  construct one after M6.
- **A build that admits an unlisted principal.** Every attack through the roster (empty,
  malformed, missing, unreadable, parse-refused, same-length swap) is killed at two layers.
- **A build differing between the SSE and JSON transports.** Tried; dispatch sits above the
  encoder. Reported as a residual rather than dressed up as a finding.

---

# VERDICT

# CONTRACT INSUFFICIENT

The revision is good work and it did the thing a delta pass exists to check: **it is a
widening, not a narrow patch.** Ten of twelve survivors are dead, two of the nine fixes are
strictly stronger than what was asked for, and one invariant (the credential never being
logged) moved from guarded to genuinely universal — I attacked it through two new doors and
both closed.

It is insufficient because **nine wrong builds pass all 448 pins**, and because the three
that matter are each one turn past a pin the fix wave just wrote:

- M1 asked *does the guard run on the SERVED path* and answered it. **WB48** runs the guard on
  the served path — **after** the tool. Order is not observable from a message.
- M7 asked *is the refused set DERIVED* and answered it. **WB50/WB50b** derive it and serve a
  section that names every tool as refused, or names nothing as available. Membership is not
  honesty.
- M3 widened the loopback claim from one host to six. **WB51** passes all six and boots on a
  hostname, because six canonical values never reach the unknown branch.

And one thing no pin can fix alone: **the ∀ "every registered tool is classified" pin is FALSE
on a correct build the moment an extension is registered** (§4.5), because `ToolSpec` cannot
express `readOnlyHint`. That is a design question, and by the routing rule it belongs to the
operator or to an author who will attack its own design — not to a builder with "figure it out".

**Eight pins to write (all eight written and paired in §11.4), one design ruling, and two
escalations (`WB31`'s cache key; `asgi-lifespan`'s unused install).** The pins are an
afternoon. The ruling is one sentence. Route it back to CONTRACT.
