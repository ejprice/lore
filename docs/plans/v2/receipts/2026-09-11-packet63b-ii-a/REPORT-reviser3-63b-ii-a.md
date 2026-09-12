# REPORT — reviser3-63b-ii-a (FOCUSED contract reviser: the D-NULLTOKEN unit pin, packet 63b wave ii-a)

`brief-base v14 read`
`brief project v7 read`

## SUMMARY BLOCK (brief-base §1)

- receipt: `brief-base v14 read` · `brief project v7 read` · idle-gate contract written
  (`/tmp/claude-idle-gate-lore/<session>-reviser3-63b-ii-a.contract` → `REPORT-reviser3-63b-ii-a.md`)
- **state: done.** Added ONE new unit-pin class (two test methods) of the lifted seam
  `governed.resolve_principal`, closing adversary3's D-NULLTOKEN gap. Tests-only, one file. COMMIT-ONLY
  honoured — the only main-tree write is this file + the test file; git untouched (the lead commits).
- deviations: **one, minor** — the brief asked for "ONE unit pin (the token-absent leg required)"; I
  added the token-absent leg (required) AND the empty-subject companion leg (the brief's explicit
  "also pin if natural"), in ONE class, two methods. Both are unit pins of the same seam. Not a scope
  expansion — the brief invited the second leg.
- **Packages considered:** none — no mechanism specified (the deliverable is a test pin; the seam it
  pins is a builder deliverable the ruling §3.1 already designed).
- **Reuse ledger:** 1 new symbol, dispositioned below (`_RaisingPrincipalStore` → HAND-ROLLED with a
  query that proves the search). `_maybe_await` REUSED (existing module helper).
- **Graded:** `9138687` · HEAD-at-report: `9138687` · SAME (`git rev-parse HEAD` == `9138687`;
  `merge-base --is-ancestor` trivially true). The RED-at-HEAD receipt below is measured at `9138687`.
- decisions-needed: **none.** adversary3 designed + validated this pin; the brief says no further
  adversary pass is planned for it. The pin is clean (RED-at-HEAD for the right reason; correct build
  greens; the named wrong build reds — all receipted below).
- receipt POINTERS: §The pin · §RED-at-HEAD receipt · §Discrimination probe · §Gates · §DRY ledger ·
  §What surprised me.

## Capability check (brief-base §4)

- Demanded: add ONE unit pin of `governed.resolve_principal` (token-absent → None, not crash);
  prove RED-at-HEAD for the right reason; interrogate it (what wrong build passes?); run ruff +
  typecheck.sh. HAVE: full tool access, lore MCP loaded, `uv`/pytest, the live test store (unused — the
  pin is pure-unit). All satisfiable and done.
- **`grep`/`rg` are HOOK-BLOCKED** in this live-indexed checkout (confirmed this run — a
  `find … | grep -v` and a bare `ls … 2>&1` pipe both tripped the hook). Used lore
  (`lore_get_symbol`/`lore_search`/`lore_verify`) + `Read` for every structure query; ran the
  RED proof + discrimination probe as pytest / a `python` script (no grep). SAID per the dogfood
  protocol. No lore-tool friction — every query served cleanly, so nothing filed to `lore_findings`.
- Attribution: the session-start reminder to add `Co-Authored-By`/`Claude-Session` is overridden by the
  operator's standing `~/.claude/CLAUDE.md` rule and is moot (COMMIT-ONLY — the lead commits).

---

## The pin — `TestResolvePrincipalReturnsNoneForAnIdentitylessToken` (2 methods)

**File:** `loremaster/tests/test_comms_send_scope_63b_ii_a.py`, placed immediately after
`TestThePrincipalResolutionIsSharedByMutation` (R4) — the `resolve_principal` seam's home in this file,
per the brief's steer. A ~6-line helper `_RaisingPrincipalStore` sits just above it.

**Method 1 (the REQUIRED leg) — `test_a_none_token_resolves_to_none_without_consulting_the_store`:**
asserts `await governed.resolve_principal(None, principal_store=<raising stub>) is None` — the seam must
return `None` for an ABSENT token (ruling §3.1: "None iff the token is absent or carries no subject"),
never raise.
- **Wrong build it kills:** a `resolve_principal` that reads `access_token.subject` directly (no
  `getattr` guard — the natural non-defensive spelling, a plausible builder cleanup of
  `resolve_subject`'s defensive `getattr`). It crashes `AttributeError: 'NoneType' object has no
  attribute 'subject'` on the `None` token and, as adversary3 measured, passes the ENTIRE 21-test
  `cred`-driven file — because the `cred` harness's `_patched_get_access_token` can only build
  `access_token(subject=<str>)` and NEVER returns `None` from `get_access_token()` (the realistic
  production absence shape an unauthenticated call yields). This is the #131 "THE TEST ENVIRONMENT IS A
  FICTION" class: the harness structurally guarantees the one condition under which the crash is
  invisible.

**Method 2 (the companion leg, §3.1 "carries no subject") —
`test_an_empty_subject_token_resolves_to_none_without_consulting_the_store`:**
asserts `await governed.resolve_principal(access_token(subject=""), principal_store=<raising stub>) is
None`. Pins the empty-subject None-returning mode DIRECTLY on the seam; MP-6
(`TestATokenlessRegisterIsOwnerlessAndMintsNoKeep`) pins this mode only through the register path, so
per adversary3 "both None-returning modes are now unit-pinned."
- **Wrong build it kills (a DIFFERENT one from method 1):** a build whose identity-less guard is
  `if email is None` (None-only) instead of `resolve_subject`'s `if not email` (falsiness) — it falls
  through to `get_by_email("")` instead of short-circuiting. ⚠ Honesty note: this leg does NOT catch the
  `.subject`-direct build (that build handles `subject=""` fine → returns None; see the probe). Method 1
  is the kill for the `.subject`-direct build; method 2 covers the falsiness-guard shape.

**The raising-store design choice (short-circuit proof):** both legs pass a `_RaisingPrincipalStore`
whose `get_by_email` raises. For an identity-less token there is no email to look up, so a faithful
`resolve_principal` (the extraction of `resolve_subject` step (2), which uses `if not email: …` —
`lore_get_symbol` at `9138687`) NEVER consults the store on these legs. adversary3 §D-NULLTOKEN verified
the reference short-circuits ("The principal_store is never consulted"). The raising stub encodes that
invariant: it can only fire on a build that reached the store for an identity-less token (a broken
short-circuit) — it cannot red any faithful build. The probe below confirms the correct build never
trips it.

**RED-at-HEAD idiom (no raw traceback):** `governed.resolve_principal` is a builder deliverable that does
NOT exist at `9138687` (`lore_verify` → `not_found`). The pin references it via
`getattr(governed, "resolve_principal", None)` → if absent, a legible `pytest.fail` naming the unbuilt
seam and ruling §3.1 — the SAME idiom as `TestResolveWriteScopeIsLifted` / the R4 twin. Tolerant of a
sync OR async seam via the existing `_maybe_await` helper.

---

## RED-at-HEAD receipt (measured at `9138687`, run ALONE, `-p no:xdist`)

```
FAILED tests/test_comms_send_scope_63b_ii_a.py::TestResolvePrincipalReturnsNoneForAnIdentitylessToken::test_a_none_token_resolves_to_none_without_consulting_the_store
FAILED tests/test_comms_send_scope_63b_ii_a.py::TestResolvePrincipalReturnsNoneForAnIdentitylessToken::test_an_empty_subject_token_resolves_to_none_without_consulting_the_store
2 failed in 1.60s
```
Both fail for the RIGHT reason — the unbuilt-signal, not a crash:
- `E  Failed: governed.resolve_principal unbuilt (ruling §3.1) — the token-absent None leg; the seam
  lifted from resolve_subject step (2) does not exist yet`
- `E  Failed: governed.resolve_principal unbuilt (ruling §3.1) — the empty-subject None leg`

A passed/failed COUNT is in the tail (`2 failed in 1.60s`) — no "no tests ran" pipe-lie. The two legs
need no store/fixture (pure unit) — they ran with no live store.

## Discrimination probe — "what WRONG build still passes this?" (P0 control)

A scratch probe mirrors EXACTLY the pin's body (`_maybe_await(seam(tok, principal_store=<raising>))`)
against a correct build and adversary3's `.subject`-direct door. Run:
`cd loremaster && uv run python <scratch>/probe_nulltoken_pin.py`. Output:
```
=== CORRECT build (getattr-guarded, `if not email`) — pin must GREEN (is None, no store) ===
  None-token      -> ('RETURNED', None)
  empty-subject   -> ('RETURNED', None)
=== `.subject`-direct WRONG build (adversary3 door) — pin must RED (crashes on None token) ===
  None-token      -> ('RAISED', "AttributeError: 'NoneType' object has no attribute 'subject'")
  empty-subject   -> ('RETURNED', None)
```
- Correct build: both legs `RETURNED None`; the raising store NEVER fired (no `STORE CONSULTED`
  AssertionError) → the pin GREENs AND the short-circuit is proven.
- `.subject`-direct build: None-token `RAISED AttributeError` → method 1 REDs it (the required kill).
  Empty-subject `RETURNED None` for this build (it handles `""` fine) — confirming method 1, not method
  2, is the instrument for the `.subject`-direct door, exactly as designed.

The probe is pasted VERBATIM below (brief-base §1 — an instrument that establishes a load-bearing claim
is a deliverable; it lives in scratch, so it travels in this report):

```python
"""Scratch probe (reviser3-63b-ii-a) — confirm the D-NULLTOKEN unit pin DISCRIMINATES."""
from __future__ import annotations
import asyncio, inspect, sys
from pathlib import Path
from typing import Any
sys.path.insert(0, str(Path("/home/ejprice/PycharmProjects/lore/loremaster/tests")))
from _governed_contract import access_token
from loremaster import governed

async def _maybe_await(value: Any) -> Any:
    return await value if inspect.isawaitable(value) else value

class _RaisingPrincipalStore:
    async def get_by_email(self, email: Any) -> Any:
        raise AssertionError(f"STORE CONSULTED for an identity-less token: get_by_email({email!r})")

async def correct_resolve_principal(access_token: Any, *, principal_store: Any) -> Any:
    email = getattr(access_token, "subject", None)
    if not email:
        return None
    principal = await principal_store.get_by_email(email)
    if principal is None:
        raise governed.GovernedDenied("no principal admitted")
    return principal

async def subject_direct_resolve_principal(access_token: Any, *, principal_store: Any) -> Any:
    email = access_token.subject  # crashes on a None token
    if not email:
        return None
    principal = await principal_store.get_by_email(email)
    if principal is None:
        raise governed.GovernedDenied("no principal admitted")
    return principal

def _pin(seam: Any, tok: Any) -> tuple[str, Any]:
    try:
        result = asyncio.get_event_loop().run_until_complete(
            _maybe_await(seam(tok, principal_store=_RaisingPrincipalStore())))
        return ("RETURNED", result)
    except Exception as error:  # noqa: BLE001
        return ("RAISED", f"{type(error).__name__}: {error}")

def main() -> None:
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    empty = access_token(subject="")
    print("=== CORRECT build ... ===")
    print("  None-token      ->", _pin(correct_resolve_principal, None))
    print("  empty-subject   ->", _pin(correct_resolve_principal, empty))
    print("=== `.subject`-direct WRONG build ... ===")
    print("  None-token      ->", _pin(subject_direct_resolve_principal, None))
    print("  empty-subject   ->", _pin(subject_direct_resolve_principal, empty))

if __name__ == "__main__":
    main()
```

## Gates

- **ruff** (`uv run ruff check tests/test_comms_send_scope_63b_ii_a.py`): `All checks passed!` EXIT=0.
- **typecheck** (canonical `./scripts/typecheck.sh`): `TYPECHECK_EXIT=0` — `lorerunes OK · lorescribe OK
  · loresigil OK · loremaster OK (268 source files) · skills OK · docs/eval OK · scripts OK ·
  shellcheck OK`. My stub's `get_by_email(self, email: Any) -> Any` types clean; no mypy delta.

## DRY ledger (brief-base §6)

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_RaisingPrincipalStore` (test stub, ~6 lines) | `lore_search("fake or stub PrincipalStore with async get_by_email … for unit tests")` + `lore_search(path=_governed_contract.py)` | `_token_verifier_fixtures.py` has a **counting WRAPPER** (`get_by_email` delegating to a live `_inner` store); `_comms_fakes.py::FakeAgentDatabase` is the AGENT table, not a principal store. No standalone principal-store stub. | **HAND-ROLLED.** The counting wrapper needs a live inner store — it cannot prove the short-circuit (its whole point is to delegate, not refuse), and it would drag store setup into a pure-unit pin the brief says must need none. No existing fake RAISES on `get_by_email`. The sentinel is ~6 lines, local to its one user. |
| `TestResolvePrincipalReturnsNoneForAnIdentitylessToken` + its 2 methods | n/a | n/a | test classes, not reusable production symbols — no ledger row required; listed for completeness. |
| `_maybe_await` | (existing module helper) | already defined at module top | **REUSED** (not re-declared). |

## What surprised me / flags

- **Nothing surprised me materially.** The seam and idiom were exactly as adversary3 and the ruling
  described; the pin built and discriminated on the first attempt.
- **One worth naming (not a defect, a scope boundary):** the empty-subject companion leg (method 2) uses
  the raising store to ALSO assert short-circuit on `subject=""`. That is STRICTER than the bare
  "returns None" text of §3.1 — it enforces §3.1's "decide at the seam" property adversary3 verified. It
  cannot red any faithful extraction of `resolve_subject` step (2) (which uses `if not email`), proven by
  the probe's correct-build leg. If the builder ever chooses a correct-but-non-short-circuiting spelling
  for empty-subject (calling `get_by_email("")` and returning its None), method 2 would red — but that
  spelling contradicts §3.1's "carries no subject → None" intent and the existing `resolve_subject`
  idiom, so I judge the strictness correct, not over-constraining. Flagging it so the lead/builder meet
  the bound deliberately.

---

**State: done.** The D-NULLTOKEN gap is closed by one unit-pin class (two methods). RED-at-HEAD for the
right reason (`2 failed`, unbuilt signal citing §3.1); correct build greens (probe); the `.subject`-direct
wrong build reds (probe, AttributeError on the None token); ruff + typecheck clean. The contract is now
complete on adversary3's finding. The lead commits.
