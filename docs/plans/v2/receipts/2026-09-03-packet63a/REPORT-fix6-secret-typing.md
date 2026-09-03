brief-base v14 read
brief project v7 read

# REPORT-fix6-secret-typing — Packet 63a fix wave, FIX 6 (finding #452, item 9)

## SUMMARY BLOCK
- state: done
- deviations:
  - Brief triage said "a `capability` SecretStr is minted outside a credential origin" and named ONE mint. The actual RED at HEAD (278f524) flags TWO probe-script mints (`scripts/probe_dnd_defense_objects.py:696`, `scripts/probe_read_filter_63.py:799`), neither a "capability" mint. Fixed both. (See §Discrepancy.)
- Packages considered: none — no mechanism specified (allowlist-data + adjudication comment only; no library involved)
- Reuse ledger: none — no new reusable symbol introduced (added two data entries to an existing frozenset-style `allowed` tuple; see §DRY note for a flagged pre-existing duplication I did NOT act on)
- Graded: n/a — this is a builder fix, not a verdict on someone else's artifact
- decisions-needed: none (a pre-existing DRY smell across the probe scripts is FLAGGED for the operator, not a blocker — §DRY note)
- receipt POINTERS:
  - RED-before: §RED-before (node id + tail)
  - GREEN-after: §GREEN-after (passed COUNT)
  - flagged mint sites: `scripts/probe_dnd_defense_objects.py:696`, `scripts/probe_read_filter_63.py:799`
  - option chosen + evidence: §Decision (Option B)
  - fix diff: `loremaster/tests/test_secret_typing.py` — `allowed` tuple in `TestOutgoingAuthHeadersGoThroughATypedSeam::test_secretstr_is_minted_only_where_a_credential_ORIGINATES`

---

## MISSION
Finding #452, item 9: the standing derived-invariant pin
`loremaster/tests/test_secret_typing.py::TestOutgoingAuthHeadersGoThroughATypedSeam::test_secretstr_is_minted_only_where_a_credential_ORIGINATES`
went RED because packet-63 work added `SecretStr(...)` mint sites the pin's `allowed` origin-list was
never reconciled with. This is the standing invariant WORKING (it caught a new mint the wave didn't
register), not a bug in the pin. The fix is a real reconciliation, not a hack-to-green.

## RED-before (at HEAD 278f524)
Node: `...::test_secretstr_is_minted_only_where_a_credential_ORIGINATES`
```
E   AssertionError: a SecretStr is minted outside a credential ORIGIN. Re-wrapping a bare str at a
    call site defeats the typed seam (attack shape S6):
E       scripts/probe_dnd_defense_objects.py:696
E       scripts/probe_read_filter_63.py:799
E   assert not ['scripts/probe_dnd_defense_objects.py:696', 'scripts/probe_read_filter_63.py:799']
loremaster/tests/test_secret_typing.py:1058: AssertionError
1 failed in 5.24s
```

## The flagged mint sites (both identical shape)
- `scripts/probe_dnd_defense_objects.py:696` — `await connection.signin(signin_credentials(user=USER, password=SecretStr(PASSWORD)))`
- `scripts/probe_read_filter_63.py:799`      — `await connection.signin(signin_credentials(user=USER, password=SecretStr(PASSWORD)))`

Evidence read at the production sites (not guessed):
| file | URL | USER | PASSWORD | SecretStr import | # SecretStr mints |
|---|---|---|---|---|---|
| `probe_dnd_defense_objects.py` | `ws://127.0.0.1:18000/rpc` | `"root"` | `"spikeroot"` | `from pydantic import SecretStr` (L70) | 1 (L696) |
| `probe_read_filter_63.py` | `ws://127.0.0.1:18000/rpc` | `"root"` | `"spikeroot"` | `from pydantic import SecretStr` (L126) | 1 (L799) |

`ws://127.0.0.1:18000` is the **spike-surreal TEST store** (CLAUDE.md / `lore_recall("surreal stores systemd")`);
`:18500` would be production. `PASSWORD = "spikeroot"` is the well-known hardcoded dev literal — no real
secret. `probe_read_filter_63.py` was introduced by `4c9a54a` ("test(63): read-filter store-law probe").

## Decision — Option B (add to the allowed-origins list, with justification)
Chose **(B) legitimate credential origin → allowlist**, not (A) route-through-an-origin, because:

1. **The credential ORIGINATES at the literal.** Each probe is a self-contained throwaway script with
   NO config resolver. `PASSWORD = "spikeroot"` is a module-level literal that is where the credential
   first exists in the process — a composition root, exactly analogous to an env var at
   `config.py::resolve_secret` or argv at `comms_cli.py` (both already in `allowed`). It is **not**
   attack shape S6 (`build_auth_headers(SecretStr(raw))` re-wrapping a bare str that flowed in from
   upstream): there is no upstream typed seam being defeated; the value is born wrapped here.
2. **The store-connect API GENUINELY requires a `SecretStr`.** `signin_credentials(*, user: str,
   password: SecretStr)` and every connection owner hold a `SecretStr` (#211). A bare `str` is a type
   error AND a runtime `AttributeError` at `password.get_secret_value()`. So a plain `str` is not an
   option — this is the packages/DRY "the API genuinely needs it" case.
3. **Option A is unavailable in-scope.** There is NO shared spike-store connect helper anywhere
   (`grep` for a shared connect/signin helper returned nothing; the already-allowed sibling
   `probe_read_filter_61b.py:692` connects the *identical* inline way). Routing through an origin would
   require **creating a new shared symbol** — a DESIGN decision, outside my writable set, and it would
   itself need one allowlist entry as the origin. The established repo convention is exactly Option B:
   6 sibling probes (07, 07a, 48, 61a, 61b) are each individually allowlisted with this same
   "spikeroot TEST-store, no real secret" adjudication (see the ADJUDICATED comment stack above the
   `allowed` tuple). This fix is a faithful continuation of that convention.

**This is the invariant WORKING, not weakened.** The pin still fails on ANY new mint outside the
enumerated origins; I added two evidence-backed origins and left the assertion body untouched. Each
new entry carries the required re-open trigger (matches sibling style): *if either probe ever sources a
REAL secret instead of the `"spikeroot"` literal, it must move to `config.py`'s resolver seam.*

## Fix (writable set: `loremaster/tests/test_secret_typing.py` only — NO production edit)
Added an `ADJUDICATED (fix6-secret-typing, packet 63a, #452)` comment block (matching the existing
sibling adjudications) and two entries to the `allowed` tuple:
```
+            "scripts/probe_read_filter_63.py",
+            "scripts/probe_dnd_defense_objects.py",
```
No assertion, no scan (`_secretstr_mint_sites`), no threshold was changed. Option A (production edit)
was NOT taken, so no production module was touched.

## GREEN-after
```
uv run python -m pytest -q -n auto loremaster/tests/test_secret_typing.py
.....................................................................    [100%]
69 passed in 6.21s
```
The full scoped suite (which contains the target node) is green: **69 passed**.

## Discrepancy flagged (brief triage vs. ground truth)
Finding #452's one-line triage for item 9 read *"a capability SecretStr mint outside a credential
origin"* and my brief expected ONE `capability`-related mint. The **actual RED at HEAD 278f524** is
TWO **spike-store probe** mints (`probe_dnd_defense_objects.py`, `probe_read_filter_63.py`) — neither a
"capability" mint. The lead's summary also said *"none dnd"*, yet one offender is literally
`probe_dnd_defense_objects.py`. I fixed the ground-truth RED (both probes); the "capability" framing did
not reproduce. Raising per scope law — the lead may want to reconcile the finding's wording, and fix 4
(the sibling handling the `<name>:<secret>` capability param in `test_link5_render_containment.py`) is
the more likely home of the actual "capability" language.

## DRY note (FLAGGED, not acted on — operator's call)
The 3-line connect boilerplate `await connection.signin(signin_credentials(user=USER,
password=SecretStr(PASSWORD)))` + `await bootstrap_session(...)` is duplicated verbatim across ALL the
spike-store probe scripts (8+ files), each minting its own `SecretStr("spikeroot")` inline. A shared
`connect_spike_test_store()` helper (one origin, one allowlist entry) would be the ONE-IMPLEMENTATION
answer and would shrink this pin's `allowed` list back toward a single probe origin. I did NOT do this:
it is a cross-file refactor of 8+ scripts outside my writable set and a design decision (WHERE the
shared helper lives) that belongs to the operator, not a fix-wave builder. Surfacing it here per
scope law.

## Tooling honesty
lore MCP tools loaded (`ToolSearch "+lore"`). Used `lore_findings action=get` (finding #452) and
`lore_comms register`. For the mint-site enumeration and constant confirmation I read the two files
directly + used `grep` — a **declared fallback**: these are non-symbol textual seams (module-level
literals, exact `SecretStr(` call lines, git introduction history) and exhaustiveness where the test's
own AST scan is authoritative, which is CLAUDE.md's sanctioned grep case (b)/(a). The pin's
`_secretstr_mint_sites()` AST scan (run via pytest) is the authoritative enumerator — I confirmed my
grep matched its two flagged sites exactly.

