"""Contract — packet 63b wave ii-a: §4.D — the ``capability=`` identity seam for the ``lore_comms``
tool. Design ``docs/design/2026-09-03-packet63b-design.md`` §4.D + the owner-resolution RULING
``docs/design/2026-09-09-packet63b-ii-a-owner-resolution-ruling.md`` (§4 the per-verb flip; §3.1/§3.3
the ONE ``governed.resolve_principal`` derivation; §3.4 the register-response credential). Authored by
``contract-63b-ii-a``; REVISED by ``reviser-63b-ii-a`` per the adversary INSUFFICIENT verdict + the
ruling (Opus 4.8 contract authors — CONTRACT TESTS ONLY, no production).

WHY (design §4.D / §9): at HEAD comms derives identity from ``agent=`` + the registration row, so
ANYONE WHO KNOWS AN AGENT'S NAME acts as it (reading B, REJECTED). ii-a closes that write-side hole by
requiring a verified capability for ``send`` (the message-family WRITE verb), resolved through the SAME
``_resolve_subject`` seam 63a-ii built.

THE PER-VERB FLIP (RULING §4 — WHAT CHANGED FROM THE ORIGINAL CONTRACT): ``requires_capability`` flips
TRUE per verb WITH the wave that ENFORCES it. In ii-a that is EXACTLY ``send`` — its handler gains an
UNCONDITIONAL ``_resolve_subject``. The four READS (drain/ack/await/story) flip in ii-b WITH their
read-shape enforcement; a ``True`` whose handler does NOT enforce is the typed-applicability lie
(PKT-28 C1, ten receipts). ``register`` MINTS identity (False); heartbeat/brief_*/fleet flip in 63c
(RED_ADJUDICATED→63c). So ii-a asserts the True-set is EXACTLY ``{send}`` (the exact-set pin's literal
grows to the five in ii-b).

SCOPE DIVISION (design §5 wave table — stated, not silently narrowed): ii-a pins the SPEC (typed
``requires_capability``), the routing STRUCTURE (the AST coverage floor + the R4 shared-derivation
twin), the ``capability=`` param, the R6 BEHAVIOURAL deny-without-a-capability (closes F-D's
guarded-call door), and R7 (register serves the credential once — ruling §3.4, D2=ii-a). The full
≥2-principal × ≥2-agent agent≡capability MISMATCH battery is 63b-iii's headline (design §5). R4's
VALUE-mutation lives in ``test_comms_send_scope_63b_ii_a.py`` (the credentialed harness is there); this
file carries R4's STRUCTURAL twin.

RED-AT-HEAD: ``CommsActionSpec`` has no ``requires_capability`` field; ``comms`` has no ``capability``
param; ``_comms_send`` calls no ``_resolve_subject``; ``resolve_subject`` inlines the principal read
(no ``resolve_principal`` call); ``_comms_register`` reads no token and renders no credential (F10). A
credentialed harness (the ``test_wire_isolation_63a.py::wire_world`` idiom) drives the behavioural R6/R7.

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique DB, reaped. NO skip marker.
pytest runs ``-n auto``.
"""

from __future__ import annotations

import dataclasses
import inspect
import re
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any

import loremaster.server as server_mod
import pytest
import pytest_asyncio
from _governed_contract import access_token, function_calls_named
from _surreal_harness import drop_database as drop_surreal_database
from _surreal_harness import make_env, surreal_password, surreal_url, surreal_user
from loremaster.config import LoreConfig
from loremaster.server import _COMMS_ACTIONS, AppContext, CommsActionSpec, LoreServer, build_app_context
from loresigil.testing import FakeEmbedder

from loremaster import governed, server

# The message-family verb whose ``requires_capability`` flips TRUE in ii-a (RULING §4): EXACTLY
# ``send`` — the one message-family WRITE verb ii-a ENFORCES (an unconditional ``_resolve_subject``).
_CAPABILITY_REQUIRED_IN_II_A = frozenset({"send"})
# The four READS that flip TRUE in ii-b WITH their read-shape enforcement (they were FALSE in ii-a — a
# True they did not yet enforce would have been the typed-applicability lie, PKT-28 C1). In ii-b they
# ARE required, so the name no longer says "NOT_YET".
_READS_REQUIRED_IN_II_B = frozenset({"drain", "ack", "await", "story"})
# ⚠ 63b-ii-b (RULING §4 / ii-a §11.5): the READS flip TRUE in ii-b WITH their read-shape enforcement.
# The requires_capability=True set GROWS from {send} to the FIVE message-family verbs. ii-b "updates
# the literal" (ii-a §4's own instruction). This is what the exact-set pin now asserts (RED at HEAD:
# at HEAD only send is True).
_CAPABILITY_REQUIRED_IN_II_B = _CAPABILITY_REQUIRED_IN_II_A | _READS_REQUIRED_IN_II_B
# register MINTS identity (False by construction); heartbeat/brief_*/fleet flip in 63c (RED_ADJUDICATED).
_NON_CAPABILITY_IN_63B = frozenset(
    {"register", "heartbeat", "brief_get", "brief_publish", "brief_ack", "fleet"}
)
# The verbs that STAY requires_capability=False through ii-b (register + the 63c-deferred set). In ii-b
# the reads LEAVE the false-set (they flip True), so the "still False" pin checks ONLY these.
_FALSE_IN_II_B = _NON_CAPABILITY_IN_63B

_DIM = 8


def _server_source() -> str:
    return Path(server.__file__).read_text(encoding="utf-8")


def _spec_fields() -> set[str]:
    return {field.name for field in dataclasses.fields(CommsActionSpec)}


class TestCommsActionSpecCarriesRequiresCapability:
    """§4.D / RULING §4 — the applicability is TYPED on the spec (``requires_capability: bool``), per
    the packet-28 'renders take typed applicability, never a name they compare' law — NOT a hardcoded
    verb list in the dispatch. RED at HEAD (the field is absent)."""

    def test_the_spec_has_a_requires_capability_field(self) -> None:
        """⚠ RED at HEAD — ``CommsActionSpec`` gains ``requires_capability: bool``. REDDENS the HEAD
        whose fields are exactly {handler, params, required, requires_registration, limit_cap}."""
        assert "requires_capability" in _spec_fields(), (
            "CommsActionSpec has no `requires_capability` field — the §4.D capability applicability is "
            "unbuilt (it must be TYPED on the spec, not a hardcoded verb list in the dispatch)"
        )

    def test_send_requires_capability_in_ii_a(self) -> None:
        """⚠ RED at HEAD (field absent → getattr None → the assert fires). ii-a flips EXACTLY the
        message-family WRITE verb ``send`` to ``requires_capability=True`` (RULING §4): send acts as an
        agent and must present a VERIFIED capability, resolved through ``_resolve_subject`` — not merely
        a name (reading B, the §9 name-only hole). The four reads (drain/ack/await/story) flip in ii-b
        WITH their read-shape enforcement, so ii-a asserts only ``{send} ⊆ True-set``."""
        for verb in sorted(_CAPABILITY_REQUIRED_IN_II_A):
            spec = _COMMS_ACTIONS[verb]
            assert getattr(spec, "requires_capability", None) is True, (
                f"comms verb {verb!r} must set requires_capability=True in ii-a (RULING §4) — it is the "
                f"message-family WRITE verb ii-a ENFORCES (an unconditional _resolve_subject)"
            )

    def test_the_deferred_verbs_do_not_require_capability_in_ii_b(self) -> None:
        """The verbs that STAY False through ii-b: ``register`` MINTS identity (False by construction),
        and heartbeat/brief_*/fleet flip in 63c (RED_ADJUDICATED→63c). ⚠ UPDATED for ii-b (was
        ``test_the_non_send_verbs_do_not_require_capability_in_ii_a``, which also asserted the READS
        False — they flip TRUE in ii-b, so they LEAVE the false-set; the rename-sweep DUAL). GREEN at
        HEAD AND after the ii-b build (these six never flip in 63b). REDDENS a build that over-reaches
        (flips a 63c verb early)."""
        for verb in sorted(_FALSE_IN_II_B):
            spec = _COMMS_ACTIONS[verb]
            assert getattr(spec, "requires_capability", None) is False, (
                f"comms verb {verb!r} must be requires_capability=False through ii-b (RULING §4 — "
                f"register MINTS identity; heartbeat/brief_*/fleet flip in 63c). got "
                f"{getattr(spec, 'requires_capability', '<no field>')!r}"
            )

    def test_the_reads_require_capability_in_ii_b(self) -> None:
        """⚠ RED at HEAD (63b-ii-b RULING §4) — the four READ verbs (drain/ack/await/story) flip
        ``requires_capability=True`` in ii-b, WITH their read-shape enforcement (each handler resolves
        the Subject UNCONDITIONALLY and filters, §4.B/§4.E). At HEAD they are False (ii-a deferred them)
        → this reds. On the ii-b build each is True AND its handler calls ``_resolve_subject`` (the
        effect-keyed coverage floor above then governs them)."""
        for verb in sorted(_READS_REQUIRED_IN_II_B):
            spec = _COMMS_ACTIONS[verb]
            assert getattr(spec, "requires_capability", None) is True, (
                f"comms READ verb {verb!r} must flip requires_capability=True in ii-b (RULING §4) — its "
                f"read shape resolves the Subject and filters (§4.B/§4.E); a name is not enough (§9). got "
                f"{getattr(spec, 'requires_capability', '<no field>')!r}"
            )

    def test_the_capability_set_is_EXACTLY_the_five_in_ii_b_surfaced_not_narrowed(self) -> None:
        """⚠ RED at HEAD — the SET of verbs with ``requires_capability=True`` is DERIVED from
        ``_COMMS_ACTIONS`` and must EQUAL EXACTLY ``{send, drain, ack, await, story}`` in ii-b (the
        §10.5 'surfaced, not narrowed' trigger: a NEW/moved comms verb forces a requires_capability
        decision, it does not default into the unguarded set). ⚠ UPDATED for ii-b (was
        ``..._is_EXACTLY_send_in_ii_a...`` asserting ``{send}`` — the rename-sweep DUAL: the ii-a
        literal certified the OLD world and ii-b updates it). At HEAD only ``send`` is True → reds."""
        required = {
            verb for verb, spec in _COMMS_ACTIONS.items()
            if getattr(spec, "requires_capability", False)
        }
        assert required == set(_CAPABILITY_REQUIRED_IN_II_B), (
            f"the requires_capability=True set is {sorted(required)}, not the ii-b set "
            f"{sorted(_CAPABILITY_REQUIRED_IN_II_B)} — a new/moved comms verb must DECIDE its capability "
            f"applicability (surfaced, not narrowed; RULING §4 / §10.5). 63c grows it further "
            f"(heartbeat/brief_*/fleet)."
        )


class TestTheCapabilityRoutingCoverageIsEffectKeyed:
    """§4.D routing-coverage pin — derived from ``_COMMS_ACTIONS`` itself, keyed on each verb's EFFECT:
    a verb with ``requires_capability=True`` whose HANDLER does not call ``_resolve_subject`` reds. This
    is the instrument that makes 'every capability verb resolves identity through the ONE composition
    root' a CHECKED VARIABLE, not a hope (INSTRUMENT 0 — reach as a checked variable over the verb SET).
    ⚠ This is the STRUCTURAL FLOOR only: an AST call-presence check passes a DEAD/guarded call
    (adversary F-D). R6 (below) closes that door BEHAVIOURALLY."""

    def test_every_capability_verb_handler_resolves_the_subject(self) -> None:
        """⚠ RED at HEAD — first the field must exist (else the coverage is unrepresentable), then ∀
        requires_capability verb, its handler (``spec.handler.__name__``, derived from _COMMS_ACTIONS)
        must call ``_resolve_subject`` (AST, the L2a ``function_calls_named`` idiom). At HEAD the field
        is absent AND ``_comms_send`` calls no _resolve_subject — both reasons red. On the build every
        capability handler routes identity through the ONE composition root (in ii-a that is ``send``)."""
        assert "requires_capability" in _spec_fields(), (
            "CommsActionSpec has no requires_capability field — the effect-keyed routing coverage is "
            "unrepresentable until the typed applicability exists (§4.D)"
        )
        source = _server_source()
        for verb, spec in _COMMS_ACTIONS.items():
            if not getattr(spec, "requires_capability", False):
                continue
            handler_name = spec.handler.__name__
            assert function_calls_named(source, handler_name, "_resolve_subject"), (
                f"comms verb {verb!r} requires a capability but its handler {handler_name!r} never calls "
                f"_resolve_subject — identity is not resolved through the ONE composition root (§4.D); a "
                f"requires_capability verb with no _resolve_subject call is the §9 name-only hole reopened"
            )


class TestThePrincipalResolutionIsSharedStructurally:
    """R4 STRUCTURAL twin (RULING §3.1 / §3.3 — ONE derivation). ``governed.resolve_subject`` (send's
    identity, via ``_resolve_subject``) and ``AppContext._comms_register`` (the keep's keeper) BOTH call
    the LIFTED ``governed.resolve_principal(access_token, *, principal_store)``: Q1 (send owner) and Q2
    (keep keeper) are the SAME admitted principal iff the same token — one seam, no second path. The
    VALUE-mutation proof lives in ``test_comms_send_scope_63b_ii_a.py``
    (``TestThePrincipalResolutionIsSharedByMutation``, which perturbs ``resolve_principal`` and watches
    BOTH move); this is the structural half (ROUTING-IS-NOT-SHARING is guarded by the value-mutation +
    the shared seam, the L2a idiom)."""

    def test_resolve_subject_calls_the_lifted_resolve_principal(self) -> None:
        """⚠ RED at HEAD — ``governed.resolve_subject`` step (2) becomes ``principal = await
        resolve_principal(...)`` (RULING §3.1: the token→admitted-principal derivation is EXTRACTED to
        ONE ``governed.resolve_principal``). At HEAD ``resolve_subject`` INLINES the
        ``principal_store.get_by_email`` block (no call) → reds."""
        source = Path(governed.__file__).read_text(encoding="utf-8")
        assert function_calls_named(source, "resolve_subject", "resolve_principal"), (
            "governed.resolve_subject does not call governed.resolve_principal — the token→principal "
            "derivation is not lifted/shared (RULING §3.1 / §6 ONE IMPLEMENTATION); it keeps a private copy"
        )

    def test_comms_register_calls_the_lifted_resolve_principal(self) -> None:
        """⚠ RED at HEAD — ``AppContext._comms_register`` resolves the keeper principal via
        ``governed.resolve_principal(get_access_token(), ...)`` (RULING §3.1 step 1). At HEAD
        ``_comms_register`` reads no token and calls no resolver → reds. A register that hand-rolls its
        own keeper resolution (Reading A's ``resolve_operator_principal``, copy #2 of owner derivation
        §3.1) does NOT call ``resolve_principal`` and reds — ROUTING-IS-NOT-SHARING (the send_scope
        value-mutation proves the sharing by mutation)."""
        source = _server_source()
        assert function_calls_named(source, "_comms_register", "resolve_principal"), (
            "AppContext._comms_register does not call governed.resolve_principal — the keeper is not "
            "resolved through the SAME seam resolve_subject uses (RULING §3.1 / §3.3 ONE derivation); a "
            "register hand-rolling its own keeper resolution is copy #2 of owner derivation"
        )


class TestTheCommsToolAcceptsACapabilityParameter:
    """§4.D — ``lore_comms`` gains ONE optional ``capability=`` parameter (the wire surface the tool
    presents). RED at HEAD (the dispatch signature carries no ``capability``)."""

    def test_the_comms_dispatch_accepts_capability(self) -> None:
        """⚠ RED at HEAD — ``AppContext.comms`` gains a ``capability: str | None`` keyword. REDDENS the
        HEAD signature (which ends at ...seqs, peek). The FastMCP ``lore_comms`` wrapper threads it to
        this dispatch; pinning the dispatch signature is the seam-level contract."""
        params = inspect.signature(AppContext.comms).parameters
        assert "capability" in params, (
            "AppContext.comms has no `capability` parameter — the §4.D optional capability= seam is "
            f"unbuilt. present params end: {list(params)[-4:]}"
        )


# =========================================================================== #
# BEHAVIOURAL — a CREDENTIALED harness (the ``test_wire_isolation_63a.py::wire_world`` idiom: patch
# ``loremaster.server.get_access_token`` to a switchable holder; provision an ``alice`` member
# principal). R6 (the ∀ deny-without-a-capability) + R7 (register serves the credential once) drive the
# REAL tool over the real store. ⚠ FIXTURE DUPLICATION (flag, report §Flags): the ``_config`` /
# ``_surreal_env`` / credentialed harness mirrors send_scope + enforcement — the established per-file
# 'fixture DATA, local, deliberately not imported' convention (a shared home would be _governed_contract,
# do-not-touch, or a new shared file outside the writable set).
# =========================================================================== #

_SURREAL_TEST_NAMESPACE = "lore_test"
_SURREAL_USER_ENV = "SURREAL_USER"
_SURREAL_PASS_ENV = "SURREAL_PASS"
_E_ALICE = "alice@example.com"
_pending_slugs: list[str] = []


@pytest_asyncio.fixture(autouse=True)
async def _surreal_env(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[None]:
    monkeypatch.setenv(_SURREAL_USER_ENV, surreal_user())
    monkeypatch.setenv(_SURREAL_PASS_ENV, surreal_password().get_secret_value())
    try:
        yield
    finally:
        for slug in _pending_slugs:
            await drop_surreal_database(make_env(database=slug, dim=_DIM))
        _pending_slugs.clear()


def _config(slug: str) -> LoreConfig:
    """A minimal valid LoreConfig pointed at the spike test store (the test_comms_wiring idiom —
    local fixture DATA, deliberately not imported)."""
    return LoreConfig.model_validate(
        {
            "schema_version": 1,
            "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
            "project": {"slug": slug, "root": "."},
            "embedding": {
                "backend": "tei", "base_url": "http://localhost:8080", "endpoint": "/embed",
                "model": "voyageai/voyage-4-nano", "dim": _DIM, "truncate": False,
                "max_input_tokens": 8192, "max_batch_texts": 32, "concurrency": 2,
                "connect_timeout_s": 5, "api_key_env": "LORE_TEI_KEY", "tokenizer": "voyage-4-nano",
            },
            "surreal": {
                "url": surreal_url(), "namespace": _SURREAL_TEST_NAMESPACE,
                "user_env": _SURREAL_USER_ENV, "password_env": _SURREAL_PASS_ENV,
            },
            "roots": [], "include": [], "exclude_dirs": [".git"], "exclude_globs": [],
            "chunkers": {".py": {"chunker": "python_ast"}},
            "watcher": {"enabled": False, "observer": "inotify", "debounce_ms": 1500,
                        "reconcile_interval_s": 600},
            "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9234},
        }
    )


@pytest_asyncio.fixture()
async def cred(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> AsyncIterator[dict[str, Any]]:
    """A REAL AppContext with a SWITCHABLE ambient transport token (patch
    ``loremaster.server.get_access_token`` to read ``holder['email']``, the wire_world idiom) + ONE
    ``alice`` member principal. ``ANTHROPIC_API_KEY``/``LORE_TEI_KEY`` set so config key-envs resolve
    (FakeEmbedder never calls out). Reaped (NEVER :18500)."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-capability-dummy")
    monkeypatch.setenv("LORE_TEI_KEY", "capability-dummy")
    holder: dict[str, str | None] = {"email": None}

    def _patched_get_access_token() -> Any:
        email = holder["email"]
        return access_token(subject=email if email is not None else "")

    monkeypatch.setattr(server_mod, "get_access_token", _patched_get_access_token)

    slug = f"test_{uuid.uuid4().hex}"
    _pending_slugs.append(slug)
    context = await build_app_context(
        server=LoreServer(_config(slug)),
        embedder=FakeEmbedder(dim=_DIM),
        manifest_path=tmp_path / f"{slug}-m.db",
        snapshot_root=tmp_path / f"{slug}-snap",
        start_tasks=False,
    )
    principal_store = context._principal_store  # noqa: SLF001 - provision the credentialed principal
    assert principal_store is not None
    await principal_store.create(email=_E_ALICE, role="member")
    try:
        yield {"ctx": context, "holder": holder, "alice_email": _E_ALICE}
    finally:
        await context.aclose()


class TestEveryCapabilityRequiredVerbDeniesWithoutOne:
    """R6 (RULING §4 — closes F-D's guarded-call door BEHAVIOURALLY). The AST floor pin above passes a
    DEAD/guarded ``_resolve_subject`` call (``if capability is not None: await self._resolve_subject``);
    only a BEHAVIOURAL leg proves identity is ACTUALLY enforced. ∀ requires_capability verb (DERIVED from
    ``_COMMS_ACTIONS``; in ii-a EXACTLY ``send``), a well-formed call with NO capability → GovernedDenied.
    ⚠ ii-b extends the per-verb driver to the four reads as they flip True (the ∀ is the checked
    variable — a True verb the driver cannot exercise is a blind spot)."""

    async def test_send_without_a_capability_denies(self, cred: dict[str, Any]) -> None:
        """⚠ RED at HEAD — anti-vacuity FIRST (the True-set is non-empty; at HEAD the field is absent →
        the set is empty → this reds, so R6 is never vacuously green). Then a well-formed ``send`` with
        a VALID ambient token but NO capability must DENY (``_resolve_subject(None)`` →
        ``stamp_owner`` OwnerStampError → GovernedDenied): the capability is REQUIRED, a name is not
        enough. On the built path this reaches ``_resolve_subject`` (the send handler's FIRST act).
        REDDENS a build whose send handler contains a DEAD/guarded ``_resolve_subject`` (F-D)."""
        required = {
            verb for verb, spec in _COMMS_ACTIONS.items()
            if getattr(spec, "requires_capability", False)
        }
        assert _CAPABILITY_REQUIRED_IN_II_A <= required, (
            f"the requires_capability=True set {sorted(required)} does not contain the ii-a verb "
            f"{sorted(_CAPABILITY_REQUIRED_IN_II_A)} — §4 unbuilt; R6's ∀ would be vacuous"
        )
        ctx = cred["ctx"]
        cred["holder"]["email"] = cred["alice_email"]  # a VALID token, so the deny is the missing CAPABILITY
        await ctx.comms(action="register", agent="r6_sender", session="s1", role="builder")
        await ctx.comms(action="register", agent="r6_recip", session="s1", role="builder")
        # ii-a's True-set is {send}; drive the send with NO capability (omitted) → the capability
        # requirement denies. (ii-b widens this to a per-verb driver over the four reads.)
        with pytest.raises(governed.GovernedDenied):
            await ctx.comms(
                action="send", agent="r6_sender", session="s1", to=["r6_recip"],
                body="a send with no capability", grade="signal",
            )

    async def test_every_capability_required_verb_denies_without_one(
        self, cred: dict[str, Any]
    ) -> None:
        """R6 (ii-a §11.5 obligation for ii-b) — the per-verb no-cap-deny DRIVER TABLE keyed on the
        True-set DERIVED from ``_COMMS_ACTIONS``, WITH a COVERAGE ASSERTION: every True verb has a
        driver row; a True verb WITHOUT one reds (INSTRUMENT-0 — reach as a checked variable, so
        growing the True-set cannot silently outrun the behavioural leg).

        For each True verb, a well-formed call with NO capability under a VALID token must DENY
        (``GovernedDenied``). At HEAD the True-set is ``{send}`` (driven → denies → GREEN); once ii-b
        flips the reads True they JOIN the True-set and are driven with NO edit — the exact-set /
        reads-require-capability pins above carry the RED-at-HEAD "flip these", and THIS pin guarantees
        each flipped verb is behaviourally enforced (F-D's dead/guarded ``_resolve_subject`` reddens
        here), not merely typed. A GREEN-at-HEAD INSTRUMENT that grows with the flip."""
        ctx = cred["ctx"]
        cred["holder"]["email"] = cred["alice_email"]  # a VALID token — the deny is the missing CAPABILITY
        # actors every driver reuses (register MINTS identity — no capability on register).
        await ctx.comms(action="register", agent="r6t_a", session="s1", role="builder")
        await ctx.comms(action="register", agent="r6t_b", session="s1", role="builder")
        # The per-verb DRIVER TABLE: verb → a well-formed NO-capability call. Keyed by verb so the
        # coverage assertion diffs it against the DERIVED True-set (a hand map whose COVERAGE is the
        # checked variable — the SAFE set is small + enumerable; the True-set is derived from truth).
        drivers: dict[str, Callable[[], Awaitable[Any]]] = {
            "send": lambda: ctx.comms(
                action="send", agent="r6t_a", session="s1", to=["r6t_b"], body="x", grade="signal"
            ),
            "drain": lambda: ctx.comms(action="drain", agent="r6t_a", session="s1"),
            "ack": lambda: ctx.comms(action="ack", agent="r6t_a", session="s1", seqs=[0]),
            "await": lambda: ctx.comms(action="await", agent="r6t_a", session="s1"),
            "story": lambda: ctx.comms(action="story", agent="r6t_a", session="s1", task_id="t-r6"),
        }
        required = {
            verb for verb, spec in _COMMS_ACTIONS.items()
            if getattr(spec, "requires_capability", False)
        }
        assert required, "the requires_capability=True set is EMPTY — R6's ∀ would be vacuous (§4 unbuilt)"
        # COVERAGE ASSERTION (INSTRUMENT-0): every True verb has a driver row. A True verb this table
        # cannot exercise is a blind spot — growing the True-set MUST grow the driver map, or this reds.
        uncovered = required - drivers.keys()
        assert not uncovered, (
            f"requires_capability verbs {sorted(uncovered)} have NO driver row in the R6 table — the "
            f"behavioural ∀ cannot exercise them, so a flipped-True verb could be name-only-enforced "
            f"undetected (ii-a §11.5: reach as a checked variable). Add a driver row for each."
        )
        for verb in sorted(required):
            with pytest.raises(governed.GovernedDenied):
                await drivers[verb]()


class TestTheRegisterResponseServesTheCapabilityOnce:
    """R7 (RULING §3.4, D2=ii-a) — the register RESPONSE serves the minted ``<name>:<secret>`` credential
    ONCE (the §4.D 'register MINTS it' letter over the wire). At HEAD ``_render_comms_register`` serves
    NO credential (F10), so a wire client can NEVER obtain the thing ``send`` (§4.D / R6) requires — a
    bound that is not a fact. The FIRST-register render carries the credential in one line; a re-register
    does NOT re-serve it; ``fleet``/``heartbeat`` renders NEVER carry it (pairs with the pkt-62 §F3a
    no-leak pin)."""

    async def test_a_first_register_serves_the_capability_once_and_a_reregister_does_not(
        self, cred: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD — the FIRST register's render contains a ``<name>:<secret>`` credential that
        VERIFIES (the EXACT minted secret, not a decoy — proven by presenting it to
        ``verify_capability`` under the owner's token); a RE-register's render does NOT carry it (the
        secret is served exactly once — mint-once-on-create returns no capability on re-register). At
        HEAD the render serves no credential (F10) → the 'contains' assert reds."""
        ctx = cred["ctx"]
        alice_email = cred["alice_email"]
        cred["holder"]["email"] = alice_email
        name = "r7_fresh_agent"
        rendered_first = await ctx.comms(action="register", agent=name, session="s1", role="builder")
        pattern = rf"{re.escape(name)}:[A-Za-z0-9_\-]{{16,}}"
        match = re.search(pattern, str(rendered_first))
        assert match is not None, (
            "the FIRST-register render carries no `<name>:<secret>` credential (F10 / R7 unbuilt) — a "
            "wire client cannot obtain the capability `send` requires; register MINTS it (§4.D), so the "
            f"render MUST serve it once. render={str(rendered_first)!r}"
        )
        extracted = match.group(0)
        verified = await ctx.agent_registry.verify_capability(
            extracted, access_token(subject=alice_email)
        )
        assert verified is not None, (
            "the credential in the register render does NOT verify under the owner's token — it is not "
            "the EXACT minted secret (a decoy/placeholder render, not the real capability)"
        )
        rendered_again = await ctx.comms(action="register", agent=name, session="s1", role="builder")
        assert re.search(pattern, str(rendered_again)) is None, (
            "a RE-register render RE-SERVED the credential — the secret must be served exactly ONCE "
            f"(mint-once-on-create; a re-register returns no capability). render={str(rendered_again)!r}"
        )

    async def test_no_other_comms_render_carries_a_credential(self, cred: dict[str, Any]) -> None:
        """After a first register mints a credential, NEITHER ``fleet`` NOR ``heartbeat`` renders may
        carry a ``<name>:<secret>`` — the §F3a no-leak invariant (a credential lives in the first
        register response and NOWHERE else). GREEN at HEAD (those renders never carried a credential) —
        a standing no-leak GUARD that REDDENS a build leaking the secret into any other surface."""
        ctx = cred["ctx"]
        cred["holder"]["email"] = cred["alice_email"]
        name = "r7_leak_probe"
        await ctx.comms(action="register", agent=name, session="s1", role="builder")
        pattern = rf"{re.escape(name)}:[A-Za-z0-9_\-]{{16,}}"
        rendered_fleet = await ctx.comms(action="fleet", agent=name, session="s1")
        assert re.search(pattern, str(rendered_fleet)) is None, (
            f"the `fleet` render carried a `<name>:<secret>` credential — §F3a no-leak broken. "
            f"render={str(rendered_fleet)!r}"
        )
        rendered_heartbeat = await ctx.comms(action="heartbeat", agent=name, session="s1")
        assert re.search(pattern, str(rendered_heartbeat)) is None, (
            f"the `heartbeat` render carried a `<name>:<secret>` credential — §F3a no-leak broken. "
            f"render={str(rendered_heartbeat)!r}"
        )
