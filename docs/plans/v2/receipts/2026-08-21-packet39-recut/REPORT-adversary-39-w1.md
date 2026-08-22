# REPORT — adversary-39-w1 (packet 39 RE-CUT, wave-1 contract adversary)

brief-base v14 read
brief project v7 read
model: claude-opus-4-8

## SUMMARY BLOCK
- state: **done — DELTA ROUND 2 COMPLETE.** Round-1 verdict was INSUFFICIENT (4 surviving wrong
  builds); the contract author's revision (r1) closed all 4. **DELTA VERDICT: SUFFICIENT** — see
  §Delta round 2 (2026-08-22). The round-1 sections below are preserved for provenance.
- **DELTA VERDICT (round 2, revised contract at `50fb230` working tree): SUFFICIENT** — all 4
  previously-surviving wrong builds now RED, reference build still 0-failed (44/44, ruff clean, no
  C-DEF), the 4 new pins discriminate (email_verified catches BOTH directions, agent_of unit catches
  a constant, exact-scope catches an extra scope, client_id catches sub), none vacuous or
  over-pinned (two legitimate alternative predicates still pass), and no new wrong build survives.
- **VERDICT (round 1, superseded): INSUFFICIENT** — the reference build was 0-failed (contract
  satisfiable), but **4 of 21 plausible wrong builds passed the WHOLE contract.** One was BLOCKER-class.
- deviations:
  - The reference build's email normaliser is inline (`unicodedata.normalize("NFKC",…).casefold().strip()`)
    rather than `lorerunes.normalize_email` — that primitive is CONTRACTED but NOT YET IMPLEMENTED
    (`lorerunes/__init__.py` exports only `is_blank`). Inline is behaviour-identical for the pins; a
    real builder REUSES the lorerunes symbol once it lands. Disclosed, not a contract defect.
  - The reference build + its 3 drivers live in the scratch copy (disposable). All are pasted
    VERBATIM in the appendices (brief-base §1 — an instrument that establishes a load-bearing
    claim is a deliverable).
- **Packages considered:** `fastmcp==3.4.7` `GoogleTokenVerifier` → **bespoke (hand-roll)** — I
  independently READ `.venv/.../fastmcp/server/auth/providers/google.py:57-201` and CONFIRM finding
  #393 (3 BLOCKER misfits). `httpx.MockTransport` → reuse (the injected transport spy, already a
  dep). `cachetools.TTLCache` → the builder's (design §4.2); my reference used a plain dict for the
  verdict cache (sufficient to grade the contract; NOT the shipped cache).
- **Reuse ledger:** none — I authored no shipped symbol (adversary builds only scratch instruments).
- **Graded:** `50fb230` · HEAD-at-report: `50fb230` · **SAME** (contract files untouched since author).
- **scratch-provenance receipt:** `loremaster.__file__ = /tmp/adv39w1/loremaster/loremaster/__init__.py`
  (resolves INSIDE the scratch root — `scripts/scratch_copy.sh` asserted it; a naive `cp` would have
  graded the ORIGINAL tree).
- decisions-needed:
  - **MISSING PIN #1 (BLOCKER-class, required):** `email_verified` string-vs-bool type monoculture
    — routes back to the contract author (contract → adversary → build).
  - **MISSING PIN #2 (low, recommended):** the Google-branch `client_id` is unpinned (fastmcp's
    `client_id=sub` survives).
  - **MISSING PIN #3 (very low, optional):** the exact hosted scope SET is unpinned.
- receipt pointers: VERDICT → §Verdict; satisfiability → §Satisfiability; wrong-build table →
  §Wrong-build sweep; missing pins → §Missing pins; ∀-table → §P1b; seam → §P1c; perturbation → §P2;
  #393 → §393; reference build → Appendix A; drivers → Appendix B/C.

---

## §Capability check (brief-base §4)
Everything the brief demanded was satisfiable with my toolset: `scratch_copy.sh` ran (provenance
asserted), the spike-surreal test store `ws://127.0.0.1:18000` was reachable (every admission pin ran
live), lore tools loaded via `ToolSearch "+lore"`, and `lore_comms` register/send/heartbeat worked.
No impossibility to report.

**Tool honesty (brief-base §4 / dogfood §3):** I read the contract/design/substrate by direct `Read`
(the brief named exact paths — no where-is question for lore to answer) and used `grep`/`find` only
for NON-symbol textual seams (locating `google.py`/`auth.py` in `.venv`, and DDL-string anchors in
`surreal_schema.py`) — the legitimate grep cases (dogfood §3b/c), said out loud here. lore was used
for comms + a finding file. No silent route-around.

---

## §Verdict — INSUFFICIENT

The contract is **satisfiable** (a correct build goes 0-failed) and its pins are **strong** — 17 of
21 plausible wrong builds are each caught, most fates are forced, and the PIN-THE-MISS seam is NOT
vacuous. But it is **INSUFFICIENT** because **4 wrong builds pass the entire contract (37/37)**, one
of which (`email_verified` handling) is a BLOCKER-class production defect. A builder who satisfies
this contract perfectly can still ship: (a) a verifier that admits UNVERIFIED emails, or (b) one that
denies EVERY real Google login. Route the missing pins back to the contract author before the build.

This is the **first** adversary pass (no three-times escalation). The findings are real but
easy-fix (2–4 fixtures) — per the §13 escalation rider they do NOT go to the operator; they go back
to the contract author.

---

## §Satisfiability receipt (C-DEF check — PASS)

I built a KNOWN-CORRECT `LoreTokenVerifier` (Appendix A) in the scratch copy: hand-rolled Google
authN per #393 (POST body, `aud == client_id`, email scope required, split 401/5xx caching,
absolute `expires_at`), api-key branch routing through `PrincipalKeyStore.verify`, per-principal
mint (#206), read-only hosted scopes regardless of role, role+agent claims.

| stage | result |
|---|---|
| RED baseline (stub, `verify_token` raises) | **34 failed / 3 passed** (matches author's report) |
| reference build | **37 passed / 0 failed** (10.08s, live store `ws://127.0.0.1:18000`) |
| after ruff cleanup (`# noqa: PLR0911` + `_HTTP_OK` constant — behaviour-preserving) | `ruff check` **All checks passed!** + **37 passed / 0 failed** |

No pin is RED on the correct build ⇒ **no C-DEF (unsatisfiable pin).** The 3 seam pins in
`test_oauth_identity_seam.py` are GREEN-now by design (they guard the shipped single-subject model).

---

## §Wrong-build sweep — the core (Appendix B is the driver)

21 plausible wrong builds, each a targeted mutation of the reference, each run against the full
contract. **17 caught; 4 pass the whole contract (MISSING PINS).**

| wrong build | defect modelled | result |
|---|---|---|
| WB1 skip aud comparison | accept a different-client token (fastmcp #393) | ✅ caught: `test_different_client_aud_is_denied` + Auth ∀ |
| WB3 token in URL | `client.get(params={access_token})` (fastmcp #393) | ✅ caught: `test_token_never_appears_in_the_request_url` |
| **WB4a `bool(email_verified)`** | admits string `"false"` (bool("false")==True) | ❌ **MISSING PIN — 37/37** |
| **WB4b `email_verified is True`** | denies Google's string `"true"` | ❌ **MISSING PIN — 37/37** |
| WB5 `email_verified is not False` | absent/None admitted | ✅ caught: `test_email_verified_absent_is_denied` + Auth ∀ |
| WB6 lookup before email_verified | ordering (F1) | ✅ caught: `test_email_verified_false_is_denied_before_principal_lookup` |
| WB7 hardcode `admin ⇒ +write` | premature RBAC | ✅ caught: `test_hosted_admin_is_ALSO_read_only_regardless_of_role` |
| WB8 per-credential identity | #206 (key-name as identity) | ✅ caught: 3 pins (`resolves_to_the_principal`, `two_keys_of_one_human`, `distinct_principals`) |
| WB9 cache 5xx like 401 | negative-cache a blip | ✅ caught: `test_5xx_is_not_cached` + `test_transient_5xx_then_success_admits` |
| WB10 no email normalisation | mixed-case denied | ✅ caught: `test_admission_normalisation_matches_a_lowercase_stored_principal` |
| WB11 email-as-sub | sub extraction (odoo-code port bug) | ✅ caught: `test_sub_is_extracted_and_used_as_the_runtime_subject` |
| WB12 relative `expires_in` in `expires_at` | 1970 trap (100% denial) | ✅ caught: `test_expires_at_is_absolute_not_relative` + `test_admission_is_never_cached` |
| WB13 drop role from claims | RBAC can't act | ✅ caught: 2 role pins + Auth ∀ |
| WB14 no agent seam | packet-62 rewrite | ✅ caught: `test_minted_identity_exposes_the_agent_binding_seam` |
| WB15 no status check | suspended admitted | ✅ caught: `test_suspended_principal_is_denied` + `test_admission_is_never_cached` |
| WB16 no principal-expiry check | expired admitted | ✅ caught: `test_expired_principal_is_denied` |
| WB17 serve stale positive cache | expired token served from cache | ✅ caught: `test_expired_token_is_not_served_from_cache` |
| WB18 cache the admission decision | suspend has a residual window | ✅ caught: `test_admission_is_never_cached_suspend_takes_effect_next_request` |
| WB19 hand-rolled hash check (bypass verify) | ROUTING-IS-NOT-SHARING | ✅ caught: `test_api_key_branch_routes_through_principal_key_store_verify` |
| **WB20 Google `client_id=sub`** | fastmcp `google.py:176` pattern | ❌ **MISSING PIN — 37/37** |
| **WB21 extra bogus scope** | `scopes=[read, "lore:bogus"]` | ❌ **MISSING PIN — 37/37** (very low sev) |

**A PROBE NEEDS A CONTROL:** every "caught" row is paired with the reference build's 37/37 (the
positive control that the same fixtures ADMIT a correct build), so a RED is a real discrimination,
not a probe that reddens on everything. WB5/WB6 additionally prove their pins fire for a DIFFERENT
reason than a plain no-principal deny (the ordering counter / the absent-vs-false distinction).

---

## §Missing pins (the deliverable — numbered, each with the exact surviving wrong build)

### MISSING PIN #1 — `email_verified` string-vs-bool TYPE MONOCULTURE (BLOCKER-class, required)

**Surviving wrong builds:** WB4a `return bool(value)` and WB4b `return value is True` — BOTH pass
37/37.

**Why it survives:** Google's `/tokeninfo` v3 returns `email_verified` as the **STRING** `"true"` /
`"false"`, not a JSON bool — this is stated verbatim in the contract's OWN fixture module
(`_auth_fixtures.py` docstring: *"Google's v3 /tokeninfo returns its numeric and boolean fields as
JSON strings ("3599", "true")"*), and the module deliberately emits `expires_in`/`exp` as strings to
expose exactly this coercion class. But **every `email_verified` fixture in the contract uses a Python
`bool`** — `admitted_payload` passes `email_verified=True`; the deny pins pass `False` or `OMIT`. The
string form Google actually sends is never exercised.

**Consequences (both are §1 mechanical verdicts / outage classes):**
- WB4a `bool("false")` == `True` ⇒ a token with `email_verified="false"` is **ADMITTED** — an
  UNVERIFIED email admitted. §1: *"a token whose email_verified is false/absent is admitted — BLOCKER."*
- WB4b `"true" is True` == `False` ⇒ a token with `email_verified="true"` is **DENIED** — **100% denial
  of every real Google login** (the #107 "widened check that never fires in prod" class; no
  verifier-level unit sees it because the suite uses bools).

**Fix (2 fixtures, mirrors the `expires_in` discipline already in the module):**
1. `email_verified="true"` (string) + active principal ⇒ **admits** (positive control that the string
   truth is accepted).
2. `email_verified="false"` (string) ⇒ **denies** (the one WB4a admits).
Add both to `TestAdmission` AND add the string-`"false"` fate to the `TestAuthQuantifier` deny set
(the ∀ currently forces only the bool-`False` and absent fates — see §P1b).

### MISSING PIN #2 — the Google-branch `client_id` is unpinned (low, recommended)

**Surviving wrong build:** WB20 `client_id=sub` — passes 37/37. This is the EXACT fastmcp pattern
(`google.py:176`, `client_id=sub`), so a builder reusing/mimicking `GoogleTokenVerifier` naturally
sets the minted token's `client_id` to the Google `sub`, not the configured OAuth client. No pin
asserts the Google-branch `AccessToken.client_id`. Design §3.3 explicitly wants
`client_id=<configured Google client_id>`. Not security-load-bearing in wave-1 (the SUBJECT is the
identity and SCOPES gate write), but it is precisely the fastmcp-reuse trap #393 exists to catch.
**Fix:** one assertion — an admitted Google token carries `result.client_id == GOOGLE_CLIENT_ID`.

### MISSING PIN #3 — the exact hosted scope SET is unpinned (very low, optional)

**Surviving wrong build:** WB21 `scopes=[LORE_READ, "lore:bogus"]` — passes 37/37. Pins check
`LORE_READ in scopes` and `LORE_WRITE not in scopes`, never the exact set. Not a security hole (the
write property IS pinned). **Optional fix:** assert `set(result.scopes) == {LORE_READ}` on the hosted
branch. I do NOT consider this required — flagging for completeness.

---

## §P1b — the Auth ∀ quantifier attack

`test_every_google_fate_is_none_or_a_wellformed_access_token` loops a `deny_payloads` dict (6 fates)
+ 1 admit fate. Per-fate FORCED-vs-∀-helper table:

| fate | fixture | FORCED? |
|---|---|---|
| aud-mismatch | `aud=OTHER_OAUTH_CLIENT_ID` | ✅ distinct fixture (WB1 reds it) |
| aud-absent | `aud=None` | ✅ distinct fixture |
| email_verified-false | `email_verified=False` (**bool**) | ⚠ forced, but bool-only (see below) |
| email_verified-absent | `email_verified=OMIT` | ✅ distinct fixture (WB5 reds it) |
| no-email-scope | `email=None, scope=SCOPE_STRING_WITHOUT_EMAIL` | ✅ distinct fixture |
| no-principal | `admitted_payload(email=UNLISTED_EMAIL)` | ✅ distinct fixture |
| ADMIT | `admitted_payload(...)` | ✅ subject+role+read-not-write all asserted |

**No fate is an unforced ∀-helper** — each is a concrete payload producing a concrete outcome
(confirmed: WB1/WB5/WB13 each redden the ∀ from a different fate). **The one gap is the SAME as
Missing Pin #1:** the `email_verified-false` fate uses bool `False`, so WB4a (`bool()`) denies it
correctly and the ∀ passes; the string-`"false"` fate that WB4a ADMITS is not in the set. Add it.

---

## §P1c — the child-table SEAM reach attack (Appendix C is the driver)

I CONSTRUCTED the "oauth_identity added at provider #2" state two faithful ways and checked which of
the 3 seam pins actually fire:

| constructed state | pins that RED |
|---|---|
| SHAPE_A — module `OAUTH_IDENTITY_TABLE` constant + `generate_oauth_identity_ddl` (the design §3.6 / pin-docstring "mirror principal_key" shape), standalone | 1: `test_schema_module_defines_no_oauth_identity_generator` |
| SHAPE_B — SHAPE_A **+** the child DDL folded into `generate_principal_key_ddl()`'s output | 2: `+ test_no_oauth_identity_table_exists_yet` |

**The seam is NOT vacuous** — on the faithful, design-prescribed shape (SHAPE_A) the module-symbol
pin fires and hands the adder the re-open-trigger message. **Reach observation (not a required fix):**
the seam's reach is a NAME-LIST — the two symbol names `OAUTH_IDENTITY_TABLE` /
`generate_oauth_identity_ddl` plus the literal substring `"oauth_identity"` in the principal/key DDL
strings. A differently-spelled constant, or a child table defined inline in `generate_ddl()` with no
module-level generator symbol, would evade all three seam pins. This is the classic "keyed on a name"
reach limit (CLAUDE.md instrument-lesson). Per the reach-attack STOP-rule + right-size-rigor (this is
a DEFERRED, low-importance provider-#2 seam that the design explicitly prescribes the mirror shape
for), I recommend **accepting the pinned bound as-is** — do NOT run a hardening round. Documented so
the next engineer meets the reach deliberately.

Note: `test_principal_ddl_defines_a_single_subject_column` is a different guard — it reddens if
`subject` is REMOVED, not when `oauth_identity` is added; it correctly stayed green in both shapes.

---

## §P2 — fixture perturbation / monoculture

The wrong-build sweep already exercised every value-branching build the fixtures must discriminate,
with the reference 37/37 as the correct-build control leg:

- **role monoculture** — WB7 (`admin ⇒ +write`) and WB13 (drop role) are caught by the member+admin
  fixtures. A build hard-coding one role value cannot pass.
- **key-name / #206 monoculture** — WB8 (per-credential identity) is caught by the two distinct
  key-names + two distinct principals. `len()≡sum()`-style collapse is impossible here.
- **client_id monoculture** — the `aud` pins use `OTHER_OAUTH_CLIENT_ID` (a real, different, well-formed
  client), so WB1 is a genuine negative, not a malformed-token pass.

**The ONE load-bearing monoculture that IS present and DOES mask a wrong build is the `email_verified`
TYPE monoculture (bool-only)** — which is Missing Pin #1. P2 and the wrong-build sweep converge on the
same defect.

---

## §393 — confirm/refute from my own READ of `google.py`

**CONFIRMED, all three, from `.venv/lib/python3.14/site-packages/fastmcp/server/auth/providers/google.py`:**
1. **Token in URL** — `verify_token` does `client.get("https://oauth2.googleapis.com/tokeninfo",
   params={"access_token": token})` (`:108-112`). The token is a URL query param. ✅ confirmed
   (violates "token never in a URL"; NOT wrappable — the HTTP call is inside the framework method).
2. **No aud-vs-client_id check** — `__init__` (`:67-90`) takes only `required_scopes`/`timeout`/
   `http_client`; there is NO `client_id` param. `verify_token` rejects only a MISSING `aud`
   (`:124-127 if not aud: return None`) and never compares it to a configured client. ✅ confirmed —
   a different-client token is ACCEPTED (confused-deputy hole).
3. **No 401-vs-5xx split** — `if response.status_code != 200: … return None` (`:114-119`) collapses
   every non-200 to `None`; malformed JSON falls into the broad `except Exception … return None`
   (`:199-201`). ✅ confirmed — the return cannot distinguish definitive-invalid from a transient blip,
   so lore's split negative-cache is impossible on reuse.

Also observed (relevant to Missing Pin #2): `google.py:176` sets `client_id=sub` — the exact pattern
WB20 models. The design's REUSE→bespoke flip (#393) is sound; the contract's group-2 pins correctly
discriminate against a naive `GoogleTokenVerifier` reuse on all three properties (WB1, WB3 caught).
One misfit fastmcp does NOT have that a reuse-mimic COULD import is the `email_verified` type — fastmcp
reads it raw into `claims` (`:183`), leaving the truthiness decision to the consumer — which is
exactly where Missing Pin #1 bites.

---

## Appendix A — the reference build (verbatim; the satisfiability instrument)

Built at `/tmp/adv39w1/loremaster/loremaster/token_verifier.py` (scratch); drives the contract 37/37,
ruff-clean. NOT the shipped build — a hand-rolled correct implementation to grade the contract.

```python
"""REFERENCE BUILD (contract-adversary adversary-39-w1) — a KNOWN-CORRECT LoreTokenVerifier."""
from __future__ import annotations

import hashlib
import time
import unicodedata
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Any

import httpx
from fastmcp.server.auth import AccessToken, TokenVerifier

from loremaster.principal_keys import PrincipalKeyStore
from loremaster.principals import PrincipalStore

_DEFAULT_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
_DEFAULT_GOOGLE_ISSUER = "https://accounts.google.com"
LORE_READ = "lore:read"
LORE_WRITE = "lore:write"
_PRINCIPAL_STATUS_ACTIVE = "active"
_HTTP_OK = 200


class _Sentinel:
    def __init__(self, name: str) -> None:
        self._name = name

    def __repr__(self) -> str:
        return self._name


_TRANSPORT_BLIP = _Sentinel("<transport-blip>")
_MALFORMED = _Sentinel("<malformed>")
_DEFINITIVE_INVALID = _Sentinel("<definitive-invalid>")


def _normalize_email(email: str) -> str:
    return unicodedata.normalize("NFKC", email).casefold().strip()


def _is_verified(value: Any) -> bool:
    # Google tokeninfo v3 returns email_verified as the STRING "true"/"false"; a bool may appear too.
    if value is True:
        return True
    return isinstance(value, str) and value.strip().lower() == "true"


class LoreTokenVerifier(TokenVerifier):
    def __init__(
        self,
        *,
        principal_store: PrincipalStore,
        principal_key_store: PrincipalKeyStore,
        google_client_id: str | None = None,
        google_required_scopes: Sequence[str] | None = None,
        google_issuer: str = _DEFAULT_GOOGLE_ISSUER,
        tokeninfo_url: str = _DEFAULT_TOKENINFO_URL,
        http_client: httpx.AsyncClient | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._principal_store = principal_store
        self._principal_key_store = principal_key_store
        self._google_client_id = google_client_id
        self._google_required_scopes = (
            list(google_required_scopes) if google_required_scopes is not None else None
        )
        self._google_issuer = google_issuer
        self._tokeninfo_url = tokeninfo_url
        self._http_client = http_client
        self._clock = clock if clock is not None else time.time
        self._verdict_cache: dict[str, tuple[Any, ...]] = {}  # token_sha -> ("ok",(email,sub,exp)) | ("bad",)

    async def verify_token(self, token: str) -> AccessToken | None:
        verification = await self._principal_key_store.verify(token)  # api-key branch, no network
        if verification is not None:
            principal = verification.principal
            return AccessToken(
                token=token,
                client_id=f"api_key:{principal.email}",
                scopes=[LORE_READ, LORE_WRITE],
                subject=principal.email,
                claims={"role": principal.role, "agent": None, "key_name": verification.key_name},
            )
        if self._google_client_id is None:
            return None
        identity = await self._verified_identity(token)
        if identity is None:
            return None
        email_norm, sub, exp = identity
        principal = await self._admit(email_norm, sub)
        if principal is None:
            return None
        return AccessToken(
            token=token,
            client_id=self._google_client_id,
            scopes=[LORE_READ],  # READ-ONLY hosted, regardless of role
            subject=principal.email,
            expires_at=exp,
            claims={
                "iss": self._google_issuer,
                "email": email_norm,
                "sub": sub,
                "role": principal.role,
                "agent": None,
            },
        )

    async def _verified_identity(  # noqa: PLR0911
        self, token: str
    ) -> tuple[str, str, int | None] | None:
        now = self._clock()
        key = hashlib.sha512(token.encode()).hexdigest()
        cached = self._verdict_cache.get(key)
        if cached is not None:
            if cached[0] == "bad":
                return None
            _, identity = cached
            _email, _sub, exp = identity
            if exp is None or exp > now:
                return identity
        data = await self._call_tokeninfo(token)
        if data is _TRANSPORT_BLIP or data is _MALFORMED:
            return None  # NOT cached
        if data is _DEFINITIVE_INVALID:
            self._verdict_cache[key] = ("bad",)
            return None
        assert isinstance(data, dict)
        aud = data.get("aud")
        if not aud or aud != self._google_client_id:
            return None
        if not _is_verified(data.get("email_verified")):
            return None  # BEFORE any principal lookup (F1)
        email = data.get("email")
        if not email:
            return None
        if self._google_required_scopes:
            granted = set((data.get("scope") or "").split())
            if not set(self._google_required_scopes).issubset(granted):
                return None
        sub = data.get("sub")
        if not sub:
            return None
        exp = self._absolute_expiry(data, now)
        identity = (_normalize_email(email), str(sub), exp)
        self._verdict_cache[key] = ("ok", identity)
        return identity

    async def _call_tokeninfo(self, token: str) -> Any:
        client = self._http_client if self._http_client is not None else httpx.AsyncClient()
        try:
            response = await client.post(self._tokeninfo_url, data={"access_token": token})
        except httpx.HTTPError:
            return _TRANSPORT_BLIP
        status = response.status_code
        if status in (400, 401):
            return _DEFINITIVE_INVALID
        if status != _HTTP_OK:
            return _TRANSPORT_BLIP  # 5xx: transient, not cached
        try:
            return response.json()
        except Exception:  # noqa: BLE001
            return _MALFORMED

    @staticmethod
    def _absolute_expiry(data: dict[str, Any], now: float) -> int | None:
        exp = data.get("exp")
        if exp is not None:
            try:
                return int(exp)
            except (TypeError, ValueError):
                pass
        expires_in = data.get("expires_in")
        if expires_in is not None:
            try:
                return int(now) + int(expires_in)
            except (TypeError, ValueError):
                pass
        return None

    async def _admit(self, email_norm: str, sub: str) -> Any:
        principal = await self._principal_store.get_by_subject(sub)
        if principal is None:
            principal = await self._principal_store.get_by_email(email_norm)
        if principal is None:
            return None
        if principal.status != _PRINCIPAL_STATUS_ACTIVE:
            return None
        if principal.expires_at is not None and principal.expires_at <= datetime.now(UTC):
            return None
        if principal.subject is None:
            await self._principal_store.set_subject(email=principal.email, subject=sub)
        return principal


__all__ = ["LoreTokenVerifier"]
```

## Appendix B — the wrong-build sweep driver (verbatim)

The driver applies each named mutation to the reference source, runs the full contract, records the
RED node ids, and restores. Full source lived at `/tmp/adv39w1/run_wrongbuilds.py`. Each mutation is a
single `str.replace` on the reference (a `SystemExit` fires if any `old` string is not found — so a
stale mutation can never silently no-op). The 21 mutations are exactly the WB1–WB21 rows in §Wrong-build
sweep; WB18 (admission cache) and WB19 (hand-rolled no-route) additionally inject a cache dict / a
`_handrolled_verify` method. Verbatim reproduction of the mutation set:

- WB1 `if not aud or aud != self._google_client_id:` → `if not aud:` (presence-only)
- WB3 `client.post(url, data={"access_token": token})` → `client.get(url, params={"access_token": token})`
- WB4a `_is_verified` body → `return bool(value)`
- WB4b `_is_verified` body → `return value is True`
- WB5 `_is_verified` body → `return value is not False`
- WB6 insert `await self._principal_store.get_by_email(...)` immediately after `assert isinstance(data, dict)`
- WB7 google `scopes=[LORE_READ]` → `[LORE_READ, LORE_WRITE] if principal.role == "admin" else [LORE_READ]`
- WB8 api-key `client_id`/`subject` → `verification.key_name`
- WB9 `if status != _HTTP_OK: return _TRANSPORT_BLIP` → `return _DEFINITIVE_INVALID`
- WB10 `_normalize_email` body → `return email`
- WB11 identity tuple sub → `_normalize_email(email)`
- WB12 `_absolute_expiry` → `return int(expires_in)` (relative)
- WB13 google claims `"role": principal.role` → `"role": None`
- WB14 remove `"agent": None` from google claims
- WB15 remove the `status != active` guard in `_admit`
- WB16 remove the `expires_at` guard in `_admit`
- WB17 `if exp is None or exp > now:` → `if True:`
- WB18 `_admit` caches its principal per-sub in an injected `self._admission_cache`
- WB19 api-key branch calls an injected `_handrolled_verify` (own hash lookup) instead of `verify`
- WB20 google `client_id=self._google_client_id` → `client_id=sub`
- WB21 google `scopes=[LORE_READ]` → `[LORE_READ, "lore:bogus"]`

## Appendix C — the seam-reach driver (verbatim intent)

`/tmp/adv39w1/run_seam_reach.py` mutated `loremaster/loremaster/store/surreal_schema.py` to add
`OAUTH_IDENTITY_TABLE = "oauth_identity"` + a `generate_oauth_identity_ddl()` mirroring
`generate_principal_key_ddl` (SHAPE_A), then additionally folded that DDL into
`generate_principal_key_ddl()`'s returned string (SHAPE_B), running only
`test_oauth_identity_seam.py` after each, and restored. Results in §P1c.

---

*Reference build + drivers are pasted above because the scratch copy `/tmp/adv39w1` is disposable
(brief-base §1). The operator/lead should discard `/tmp/adv39w1` after reading — nothing durable
lives only there.*

---

# §Delta round 2 (2026-08-22) — re-grade of the revised contract (r1)

**DELTA VERDICT: SUFFICIENT.** The contract author's revision (REPORT-contract-39-w1.md §Revision
round 1) closed all 4 round-1 missing pins. I re-graded against my scratch reference build (with the
new `agent_of` accessor added), reusing the scratch copy per the delta directive.

- **scratch-provenance receipt (unchanged):** `loremaster.__file__ = /tmp/adv39w1/loremaster/loremaster/__init__.py`
  (`scratch_copy.sh --verify-only` re-asserted). Graded: `50fb230` working tree · HEAD-at-report:
  `50fb230` · SAME (contract still untracked, revised in place).
- **The revision:** revised contract collects **44** (was 37); against the STUB it is 40 RED / 4 GREEN
  (the 3 seam pins + the new `agent_of` unit, which is a pure accessor the stub now implements).

## (b) Satisfiability preserved — no C-DEF
Reference build (Appendix A + the `agent_of` accessor copied from the revised stub) vs the revised
contract: **44 passed / 0 failed** (11.26s, live store), `ruff check` **All checks passed!** No pin
reds a correct build ⇒ the additions introduced no C-DEF.

## (a) The 4 previously-surviving wrong builds — ALL now caught
Re-ran each against the revised contract (driver: `/tmp/adv39w1/run_delta.py`, pasted intent below):

| round-1 survivor | now caught by |
|---|---|
| WB4a `bool(email_verified)` (admits string `"false"`) | `test_email_verified_string_and_bool_representations[false-False]` + Auth ∀ |
| WB4b `email_verified is True` (denies string `"true"`) | `test_email_verified_string_and_bool_representations[true-True]` |
| WB20 Google `client_id=sub` | `test_google_client_id_is_the_configured_oauth_client_not_the_sub` |
| WB21 extra bogus scope | `test_hosted_member_gets_read_only_scope` + `test_hosted_admin_is_ALSO_read_only_regardless_of_role` + Auth ∀ |

## (c) The 4 new pins DISCRIMINATE — not vacuous, not over-pinned
- **`test_email_verified_string_and_bool_representations`** is parametrized over the 5 representations
  `[("true",True),(True,True),("false",False),(False,False),(OMIT,False)]`. It catches BOTH failure
  directions from a SINGLE pin (WB4a reds `[false-False]`; WB4b reds `[true-True]`) — the exact
  monoculture round 1 exposed is gone. **Over-pinning probe (a probe needs a control):** I built TWO
  legitimate alternative correct predicates — `str(value).strip().lower()=="true"` and
  `value in (True,"true")` — and **both pass 44/44**, proving the pin is not over-pinned to one
  spelling of the truth test.
- **`test_agent_of_is_the_typed_fail_closed_accessor`** proves `agent_of` READS a bound value: a
  constant-`None` `agent_of` (WB22) reds it on the `agent_of(bound)=="agent:pkt62-x"` assertion. It
  is not vacuous. The seam pin `test_minted_identity_exposes_the_agent_binding_seam` additionally
  catches a mint that writes the binding under a DIFFERENT claim key (WB23 → `"agent" in claims` fails).
- **Exact-scope `{lore:read}` pins** (`test_hosted_member_gets_read_only_scope` /
  `..._admin_is_ALSO_read_only...`) are NOT over-pinning: the correct build (which mints exactly
  `[lore:read]`) passes; only an extra-scope build (WB21) reds. Design-ruled exact set.
- **`test_google_client_id_...not_the_sub`** is monoculture-safe: it asserts `== GOOGLE_CLIENT_ID`
  AND `!= OPERATOR_SUBJECT` (distinct constants), so `client_id=sub` reds and no single value
  satisfies both wrongly.

## (d) New wrong builds the additions opened — both caught
| new wrong build | caught by |
|---|---|
| WB22 `agent_of` returns a constant `None` (ignores the binding) | `test_agent_of_is_the_typed_fail_closed_accessor` |
| WB23 mint writes the agent under `claims["agent_binding"]` not `claims["agent"]` | `test_minted_identity_exposes_the_agent_binding_seam` |

## Residual observations (NON-blocking — SUFFICIENT stands)
- The Auth ∀'s ADMIT fate still uses bool `True` (not the string `"true"`); WB4b is therefore caught
  by the dedicated parametrized pin, not by the ∀. Coverage is complete via the parametrize — a
  string-`"true"` admit fate in the ∀ would be defense-in-depth, not a gap. **Not required.**
- The §P1c seam-reach observation (the deferred provider-#2 seam's reach is a name-list) is unchanged
  and remains an accepted pinned bound, not a fix — per the reach-attack STOP-rule + right-size-rigor.

**Delta driver** (`/tmp/adv39w1/run_delta.py`) — 8 builds, each a single `str.replace` on the
reference (a failed `old` match aborts, so no silent no-op), full contract run per build, RED node ids
parsed, reference restored in `finally`: WB4a/WB4b mutate `_is_verified`; WB20 sets google
`client_id=sub`; WB21 adds `"lore:bogus"`; WB22 makes `agent_of` `return None`; WB23 renames the mint
claim key; the two CONTROL rows swap in legitimate alternative `_is_verified` predicates and assert
44/44 (over-pinning check). Results verbatim above.
