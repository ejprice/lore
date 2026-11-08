"""Contract — packet 63b wave ii-a: §4.A (send stamps scope from the session keep, via the LIFTED
``governed.resolve_write_scope``) + SF-63-1 (``register`` MINTS the session keep). Design
``docs/design/2026-09-03-packet63b-design.md`` §4.A (RULED reading A: ``send`` resolves
``session:<session>`` by keep KEY → scope through the ONE lifted grant seam; a missing keep at send is
a DENY, never a fallback) + §5 SF-63-1 (register mints ``get_or_create_keyed("session:<s>",
type="session")``). Authored by ``contract-63b-ii-a`` (Opus 4.8 contract author — TESTS ONLY).

TWO layers, split so the RED reasons stay legible:
  · the LIFT (unit / structural) — ``governed.resolve_write_scope(subject, scope, *, default)`` is the
    ONE grant seam ``LocalMemoryBackend._resolve_write_scope`` (memory ``remember``) and the ``send``
    handler BOTH call. ONE IMPLEMENTATION (design §4.A / §6): the grant predicate lives once, so a fix
    to it reaches remember AND send. Pinned by a UNIT of the seam + a structural route pin on each
    caller (the L2a ``function_calls_named`` idiom; the value-mutation proof is available and named in
    the report's DRY ledger).
  · the BEHAVIOUR (harness, real store via ``build_app_context``) — register mints a resolvable
    ``session:<s>`` keep; a send with NO session keep DENIES with a "register first" teaching.

FLAG F-KEEPER RESOLVED by the ruling ``docs/design/2026-09-09-packet63b-ii-a-owner-resolution-ruling.md``
§3 (this module REVISED by ``reviser-63b-ii-a``): the keep's keeper is the REGISTRANT's admitted
principal, read from the transport token through the SAME lifted seam ``governed.resolve_principal``
that ``resolve_subject`` reads it from (§3.1). Reading A (``resolve_operator_principal``) is REJECTED as
copy #2 of owner derivation — it is a migrate-time fleet-wide guess with a REFUSE, not a served-path
resolver, and would make principal B's session A's the moment B is householded (§2.2 / §3.1). A tokenless
register succeeds OWNERLESS and mints NO keep (reading α, §3.2). The behavioural layer is now a
CREDENTIALED harness (the ``test_wire_isolation_63a.py::wire_world`` idiom): ≥2 member principals + one
ADMIN, so ``resolve_operator_principal`` gives a DIFFERENT answer (the admin) than the NON-admin
registrant — the WB-2 ownership-forgery detector Reading A fails. R3 pins the keeper EXACTLY (the
registrant, not the admin); R1 the send owner EXACTLY (the sender's pair, not the keeper); R2 the
tokenless-send DENY; R5 the send-half grant flip; R4 the ONE-derivation sharing by mutation.

STORE LAW cited: §1.8 (``keep.key`` UNIQUE over option<> — the deterministic natural key), §2 (CONTENT
writes). Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique DB, reaped. NO skip.
pytest runs ``-n auto``.
"""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import (
    access_token,
    build_memory_backend,
    credentialed_app_context,
    member,
    register_owned,
)
from _surreal_harness import drop_database as drop_surreal_database
from _surreal_harness import make_env, surreal_password, surreal_user, unique_database
from loremaster.memory import local as local_mod
from loremaster.server import _COMMS_ACTIONS, AppContext
from sdk3_shape_fakes import bare_record_key, same_record

import lorerunes as pdp
from loremaster import governed

_DIM = 8


async def _maybe_await(value: Any) -> Any:
    return await value if inspect.isawaitable(value) else value


def _ks(ctx: AppContext) -> Any:
    """The real KeepStore, narrowed (it is Optional on ``AppContext``; the test always has one)."""
    store = ctx._keep_store  # noqa: SLF001 - the test reads the real keep store
    assert store is not None
    return store


def _ps(ctx: AppContext) -> Any:
    """The real PrincipalStore, narrowed (Optional on ``AppContext``; the test always has one)."""
    store = ctx._principal_store  # noqa: SLF001 - the test reads the real principal store
    assert store is not None
    return store


# =========================================================================== #
# LAYER 1a — the LIFTED grant seam (unit). governed.resolve_write_scope(subject, scope, *, default).
# =========================================================================== #


class TestResolveWriteScopeIsLifted:
    """§4.A / §6 — the ``remember``-scope grant predicate (``LocalMemoryBackend._resolve_write_scope``:
    None → the default project scope; an explicit scope → PDP-``_grantable`` check, else GovernedDenied)
    is LIFTED to ONE ``governed.resolve_write_scope(subject, scope, *, default)`` that ``send`` shares.
    RED at HEAD (``governed.resolve_write_scope`` does not exist — the predicate lives only on the memory
    backend). Tolerant of a sync OR async lifted seam (``_maybe_await``)."""

    def test_resolve_write_scope_exists_on_governed(self) -> None:
        """⚠ RED at HEAD — ``governed.resolve_write_scope`` is unbuilt (the grant predicate is a private
        method on ``LocalMemoryBackend``). REDDENS the un-lifted HEAD."""
        assert hasattr(governed, "resolve_write_scope"), (
            "governed.resolve_write_scope is not lifted — the write-scope grant predicate lives only on "
            "LocalMemoryBackend._resolve_write_scope, so `send` cannot share it (design §4.A / §6)"
        )

    async def test_a_none_scope_returns_the_default(self) -> None:
        """⚠ RED at HEAD (AttributeError, caught as the unbuilt-signal). ``scope=None`` → the supplied
        ``default`` (the caller resolves the canonical project scope and passes it in)."""
        subject = member("alice", "ag_a1", frozenset({pdp.keep_scope("k1")}))
        seam = getattr(governed, "resolve_write_scope", None)
        if seam is None:
            pytest.fail("governed.resolve_write_scope unbuilt (design §4.A) — the None→default leg")
        result = await _maybe_await(seam(subject, None, default=pdp.keep_scope("proj")))
        assert result == pdp.keep_scope("proj"), f"None scope must return the default, got {result!r}"

    async def test_a_grantable_scope_is_returned(self) -> None:
        """⚠ RED at HEAD. An explicit scope the subject IS householded in (its own keep) is returned
        verbatim — the shared ``pdp._grantable`` predicate accepts it."""
        subject = member("alice", "ag_a1", frozenset({pdp.keep_scope("k1")}))
        seam = getattr(governed, "resolve_write_scope", None)
        if seam is None:
            pytest.fail("governed.resolve_write_scope unbuilt (design §4.A) — the grantable leg")
        result = await _maybe_await(seam(subject, pdp.keep_scope("k1"), default=pdp.keep_scope("proj")))
        assert result == pdp.keep_scope("k1"), f"a grantable scope must be returned, got {result!r}"

    async def test_a_non_grantable_scope_denies(self) -> None:
        """⚠ RED at HEAD. A scope the subject is NOT householded in → ``GovernedDenied`` (never a
        silent fallback to the default — §4.A: a non-grantable scope is a DENY). This is the shared
        predicate whose mutation the report's DRY ledger names (remove the ``_grantable`` call → this
        AND the send foreign-keep deny both flip)."""
        subject = member("alice", "ag_a1", frozenset({pdp.keep_scope("k1")}))
        seam = getattr(governed, "resolve_write_scope", None)
        if seam is None:
            pytest.fail("governed.resolve_write_scope unbuilt (design §4.A) — the deny leg")
        with pytest.raises(governed.GovernedDenied):
            await _maybe_await(seam(subject, pdp.keep_scope("k_foreign"), default=pdp.keep_scope("proj")))


class TestBothCallersRouteThroughTheLiftedSeam:
    """§4.A / §6 ONE IMPLEMENTATION (proven by ROUTING — the L2a AST idiom; ROUTING-IS-NOT-SHARING is
    guarded by the shared unit above + the value-mutation proof named in the report). Both the memory
    ``remember`` scope resolver AND the comms ``send`` handler call ``governed.resolve_write_scope``."""

    def test_memory_resolve_write_scope_routes_through_the_lifted_seam(self) -> None:
        """⚠ RED at HEAD — ``LocalMemoryBackend._resolve_write_scope`` calls the LIFTED
        ``governed.resolve_write_scope`` (it becomes a caller, design §4.A). At HEAD it calls
        ``pdp._grantable`` directly (a private copy), so it does NOT route through the lifted seam →
        reds. REDDENS a build that leaves the memory backend with its own copy of the predicate."""
        from _governed_contract import function_calls_named

        source = Path(local_mod.__file__).read_text(encoding="utf-8")
        assert function_calls_named(source, "_resolve_write_scope", "resolve_write_scope"), (
            "LocalMemoryBackend._resolve_write_scope does not call governed.resolve_write_scope — the "
            "grant predicate is not lifted/shared (§4.A / §6 ONE IMPLEMENTATION); remember keeps a copy"
        )

    def test_the_send_handler_routes_through_the_lifted_seam(self) -> None:
        """⚠ RED at HEAD — the comms ``send`` handler (``AppContext._comms_send``) resolves the write
        scope through ``governed.resolve_write_scope`` (design §4.A: send stamps scope through the
        LIFTED seam). At HEAD ``_comms_send`` resolves no scope at all → reds. ⚠ Committed reading
        (report §Decisions): the scope resolution lives in the SERVER-level send handler (it has the
        keep_store + the resolved Subject); a build that resolves it inside ``MessageLedger.send``
        instead would red this — a lead flag, not a silent narrowing."""
        from _governed_contract import function_calls_named

        from loremaster import server

        source = Path(server.__file__).read_text(encoding="utf-8")
        assert function_calls_named(source, "_comms_send", "resolve_write_scope"), (
            "AppContext._comms_send does not call governed.resolve_write_scope — send does not stamp "
            "its message scope through the LIFTED grant seam (§4.A)"
        )


# =========================================================================== #
# LAYER 1b — the mutation proof of the SHARED grant predicate (the remember half; the send half is the
# structural route pin above + 63b-iii's wire battery). Perturb the lifted seam → the live remember
# scope-deny FLIPS, proving remember routes through it (not a private copy). RED at HEAD (remember does
# not route through the lifted seam yet, so the perturbation does not reach it).
# =========================================================================== #


@pytest_asyncio.fixture()
async def memory_backend() -> AsyncIterator[Any]:
    """A ready ``LocalMemoryBackend`` on a fresh DB (the ``build_memory_backend`` idiom). Reaped."""
    env = make_env(database=unique_database(), dim=_DIM)
    backend = await build_memory_backend(env)
    try:
        yield backend
    finally:
        await backend.close()
        await drop_surreal_database(env)


class TestTheSharedGrantPredicateIsProvenByMutation:
    """§4.A / §6 — mutate the LIFTED seam and watch a CALLER change: with a PERMISSIVE
    ``governed.resolve_write_scope`` monkeypatched in (grant check removed), a ``remember`` with a
    NON-grantable scope no longer DENIES. This proves remember ROUTES THROUGH the lifted seam (not a
    private ``pdp._grantable`` copy). RED at HEAD: remember calls its own ``_resolve_write_scope`` →
    ``pdp._grantable`` directly, so the monkeypatched seam is never consulted → the write still DENIES
    → the 'no longer denies' assert reds (correct — the lift is unbuilt)."""

    async def test_perturbing_the_lifted_seam_changes_remember(
        self, memory_backend: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD. A permissive lifted seam (returns the requested scope, no grant check) makes
        a foreign-scope ``remember`` SUCCEED where it otherwise DENIES — ONLY if remember routes through
        the seam. At HEAD it does not, so the deny stands and this reds. POSITIVE CONTROL: the same
        foreign-scope remember WITHOUT the perturbation DENIES (so the flip is real, not a fixture that
        never denied)."""
        member_subject = member("alice", "ag_a1", frozenset({pdp.keep_scope("k1")}))
        foreign = pdp.keep_scope("k_foreign")
        # positive control — the foreign scope genuinely denies on the unperturbed path.
        with pytest.raises(governed.GovernedDenied):
            await memory_backend.remember("control note", kind="fact", subject=member_subject, scope=foreign)

        def _permissive(subject: Any, scope: Any, *, default: Any) -> Any:
            return default if scope is None else scope

        monkeypatch.setattr(governed, "resolve_write_scope", _permissive, raising=False)
        # With the seam permissive, a routed remember accepts the foreign scope. At HEAD remember does
        # NOT route through the seam (private _grantable), so it STILL denies → this reds.
        try:
            await memory_backend.remember("routed note", kind="fact", subject=member_subject, scope=foreign)
        except governed.GovernedDenied:
            pytest.fail(
                "a foreign-scope remember STILL denied under a permissive governed.resolve_write_scope — "
                "remember does not route through the lifted seam (it keeps a private _grantable copy; "
                "§4.A / §6 ONE IMPLEMENTATION unbuilt)"
            )


# =========================================================================== #
# LAYER 2 — BEHAVIOUR over the real store (build_app_context). SF-63-1 keep mint + §4.A send scope.
# =========================================================================== #

_SURREAL_USER_ENV = "SURREAL_USER"
_SURREAL_PASS_ENV = "SURREAL_PASS"


@pytest_asyncio.fixture(autouse=True)
async def _surreal_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the store credentials for the Layer-1b ``memory_backend`` fixture (which builds its backend
    directly). The credentialed ``cred`` harness sets its own env + reaps its own db via the shared
    ``credentialed_app_context`` home, so this fixture no longer tracks any slugs to reap."""
    monkeypatch.setenv(_SURREAL_USER_ENV, surreal_user())
    monkeypatch.setenv(_SURREAL_PASS_ENV, surreal_password().get_secret_value())


async def _message_count(ctx: AppContext, session: str) -> int:
    """The number of ``message`` rows in ``session`` — the zero-rows / anti-vacuity instrument (R2)."""
    rows = await ctx.agent_registry._query(  # noqa: SLF001 - test-only count of the message rows
        "SELECT count() FROM message WHERE session = $s GROUP ALL", {"s": session}
    )
    return rows[0]["count"] if isinstance(rows, list) and rows else 0


@pytest_asyncio.fixture()
async def cred(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> AsyncIterator[dict[str, Any]]:
    """A CREDENTIALED real ``AppContext`` — a CALLER of the shared ``credentialed_app_context``
    (§11.3 F-DUP: the private per-file credentialed harness CONVERGED onto the ONE lifted home). Provisions
    THREE principals — ``alice``/``bob`` (members) and ``carol`` (ADMIN). alice is the NON-admin
    registrant/keeper; carol exists so ``resolve_operator_principal`` (the single admin) gives a DIFFERENT
    answer than alice — the WB-2 ownership-forgery detector Reading A fails (§3 / ruling §5 preamble).
    Reaped by the shared home (NEVER :18500). SHARING is provable BY MUTATION (§11.3): change the shared
    harness's token shape and this file's credentialed identity flips with it — the F-DUP mutation pin."""
    async with credentialed_app_context(
        monkeypatch,
        tmp_path,
        principals={"alice": "member", "bob": "member", "carol": "admin"},
        dim=_DIM,
        digit_led_principals=True,  # R15 / MP-C 3c: a principal-id compare is deterministic on SDK 3
    ) as world:
        yield {
            "ctx": world["ctx"],
            "holder": world["holder"],
            "emails": world["emails"],
            "pids": world["pids"],
        }


class TestRegisterMintsTheSessionKeep:
    """SF-63-1 — ``register`` MINTS the session keep ``session:<session>`` (type ``session``), kept by
    the REGISTRANT's admitted principal (ruling §3), so a later ``send`` in that session can resolve it
    by key. Driven CREDENTIALED (the ambient token is the registrant's email). R3 adds the keeper
    EXACTNESS + the SF-63-1 foreign gate + the keeper's-own-second-agent positive control."""

    async def test_a_fresh_register_mints_a_resolvable_session_keep(self, cred: dict[str, Any]) -> None:
        """⚠ RED at HEAD — after a CREDENTIALED ``comms(action="register", session="s1", …)`` a keep
        bearing key ``session:s1`` and type ``session`` exists (resolvable by ``KeepStore.get_by_key``).
        At HEAD ``_comms_register`` reads no token and mints NO keep → ``get_by_key`` returns None →
        reds (SF-63-1 unbuilt)."""
        ctx = cred["ctx"]
        cred["holder"]["email"] = cred["emails"]["alice"]
        await ctx.comms(action="register", agent="ag_one", session="s1", role="builder")
        keep = await _ks(ctx).get_by_key("session:s1")
        assert keep is not None, (
            "register did not mint a session keep keyed 'session:s1' (SF-63-1 unbuilt) — a later send "
            "cannot resolve the session scope by key"
        )
        assert keep.type == "session", (
            f"the register-minted keep must be type 'session' (SF-63-1), got {keep.type!r}"
        )

    async def test_register_is_idempotent_on_the_session_keep(self, cred: dict[str, Any]) -> None:
        """⚠ RED at HEAD — a SECOND register in the same session (by the keeper's own second agent)
        resolves the SAME keep (the ``get_or_create_keyed`` CAS on the UNIQUE ``keep.key`` — store-ref
        §1.8), never a second row. RED at HEAD (no keep minted at all). Discriminates a build that mints
        a NEW keep per register."""
        ctx = cred["ctx"]
        cred["holder"]["email"] = cred["emails"]["alice"]
        await ctx.comms(action="register", agent="ag_one", session="s1", role="builder")
        first = await _ks(ctx).get_by_key("session:s1")
        assert first is not None, "SF-63-1 unbuilt: first register minted no session keep"
        await ctx.comms(action="register", agent="ag_two", session="s1", role="builder")
        second = await _ks(ctx).get_by_key("session:s1")
        assert second is not None and second.id == first.id, (
            f"a second register in session s1 must resolve the SAME session keep (idempotent CAS on the "
            f"UNIQUE key, store-ref §1.8), got {first.id if first else None!r} vs "
            f"{second.id if second else None!r}"
        )

    async def test_register_mints_the_session_keep_kept_by_the_registrants_principal(
        self, cred: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD — R3 keeper EXACTNESS (ruling §3). The session keep's keeper is the REGISTRANT's
        principal (alice, a NON-admin member), NOT ``resolve_operator_principal``'s answer (carol, the
        single ADMIN — Reading A / WB-2). At HEAD register mints no keep → ``get_by_key`` None → reds
        (SF-63-1 unbuilt). On a Reading-A build the keeper is carol → the ``== alice`` assert reds (the
        ownership-forgery WB-2 fails to catch: a keeper=admin would make principal B's session A's)."""
        ctx = cred["ctx"]
        cred["holder"]["email"] = cred["emails"]["alice"]  # alice is a NON-admin member; carol is the admin
        await ctx.comms(action="register", agent="alice_w1", session="s1", role="builder")
        keep = await _ks(ctx).get_by_key("session:s1")
        assert keep is not None, "SF-63-1 unbuilt: register minted no session keep"
        assert keep.keeper_id == cred["pids"]["alice"], (
            f"the session keep's keeper must be the REGISTRANT's principal (alice), NOT "
            f"resolve_operator_principal's answer (carol, the single admin — Reading A / WB-2). got "
            f"keeper_id={keep.keeper_id!r}, alice={cred['pids']['alice']!r}, carol={cred['pids']['carol']!r}"
        )
        assert keep.keeper_id != cred["pids"]["carol"], (
            "the keeper is the ADMIN (carol) — Reading A (keeper = resolve_operator_principal = the "
            "single admin) is the ownership-forgery WB-2 cannot see; the keeper is the REGISTRANT (§3)"
        )

    async def test_a_foreign_principals_register_into_a_kept_session_denies_naming_the_remedy_not_the_keeper(
        self, cred: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD — R3 the SF-63-1 foreign gate (ruling §3.1 step 4). alice keeps ``session:s1``;
        bob (a FOREIGN principal, not householded) registering into it is DENIED with a teaching that
        names the SESSION and the ``add-household`` remedy — and NOT the keeper's identity (63-rulings
        §6 existence-leak stance) — and writes NO agent row (#97: a rejected call has no side effect).
        At HEAD alice's register mints no keep → the ``keep is not None`` guard reds (SF-63-1 unbuilt);
        even reached, HEAD has no foreign gate → bob's register succeeds → the ``raises`` reds."""
        ctx = cred["ctx"]
        cred["holder"]["email"] = cred["emails"]["alice"]
        await ctx.comms(action="register", agent="alice_w1", session="s1", role="builder")
        keep = await _ks(ctx).get_by_key("session:s1")
        assert keep is not None, "SF-63-1 unbuilt: alice's register minted no session keep"
        cred["holder"]["email"] = cred["emails"]["bob"]  # a FOREIGN principal, not householded in s1
        with pytest.raises(governed.GovernedDenied) as excinfo:
            await ctx.comms(action="register", agent="bob_w1", session="s1", role="builder")
        message = str(excinfo.value)
        assert "s1" in message and "household" in message.lower(), (
            f"a foreign register deny must NAME the session + the add-household remedy (ruling §3.1 step "
            f"4), got: {message!r}"
        )
        assert cred["emails"]["alice"] not in message, (
            f"a foreign register deny must NOT leak the keeper's identity (63-rulings §6 existence-leak "
            f"stance — a foreign principal must not learn who keeps a session), got: {message!r}"
        )
        rows = await ctx.agent_registry._query(  # noqa: SLF001 - test-only side-effect check
            "SELECT count() FROM agent WHERE name = $n GROUP ALL", {"n": "bob_w1"}
        )
        assert (rows[0]["count"] if isinstance(rows, list) and rows else 0) == 0, (
            "a DENIED foreign register wrote an agent row for bob_w1 — a rejected call must have NO side "
            "effect (the dispatcher's #97 law)"
        )

    async def test_the_keepers_own_second_agent_registers_fine(self, cred: dict[str, Any]) -> None:
        """R3 POSITIVE CONTROL (63-rulings §9 item 7) — the keeper's OWN second agent joins the session
        it keeps WITHOUT a foreign-gate deny (a gate that denied its own keeper's agents would be a
        false positive that made the deny above meaningless). GREEN at HEAD (no gate) AND on the build
        (alice is auto-householded as the keeper). Proves the foreign deny is not a blanket refusal."""
        ctx = cred["ctx"]
        cred["holder"]["email"] = cred["emails"]["alice"]
        await ctx.comms(action="register", agent="alice_w1", session="s1", role="builder")
        # alice's SECOND agent in the SAME session must register fine (auto-householded keeper).
        await ctx.comms(action="register", agent="alice_w2", session="s1", role="builder")


async def _credentialed_send(ctx: AppContext, **kwargs: Any) -> Any:
    """Drive a CREDENTIALED ``comms(action='send', …)``; at HEAD ``comms`` rejects ``capability=`` (the
    §4.D seam is unbuilt) → a LEGIBLE ``pytest.fail`` RED rather than a raw ``TypeError`` traceback. Use
    only where the send is expected to SUCCEED or to raise ``GovernedDenied`` on the BUILT path."""
    try:
        return await ctx.comms(action="send", **kwargs)
    except TypeError as error:
        pytest.fail(
            f"AppContext.comms rejected capability= — the §4.D seam is unbuilt (RED-at-HEAD for the "
            f"right reason): {error}"
        )


class TestSendResolvesTheSessionKeepScope:
    """§4.A — a CREDENTIALED ``send`` resolves ``session:<session>`` by KEY and stamps the message scope
    through the lifted grant seam; a MISSING session keep at send is a teaching DENY, never a fallback.
    Adds R1 (owner EXACTNESS — the send owner is the SENDER's pair, not the keeper), R2 (a tokenless
    send DENIES and writes nothing), R5 (the §4.A send-half grant flip). All driven CREDENTIALED."""

    async def test_a_send_with_no_session_keep_denies_teaching_register_first(
        self, cred: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD — a CREDENTIALED ``send`` in a session with NO session keep DENIES with a
        teaching naming ``register`` (§4.A: missing keep → 'register first', never the project keep,
        never NONE). CREDENTIALED so ``_resolve_subject`` SUCCEEDS and the deny is the MISSING KEEP —
        NOT a missing IDENTITY (whose deny ALSO contains 'register', the fixture-doesn't-discriminate
        trap a tokenless drive fell into). The missing-keep state is manufactured by DELETING the keep
        register minted. At HEAD ``comms`` rejects ``capability=`` (§4.D unbuilt) → the wrapper reds."""
        ctx = cred["ctx"]
        cred["holder"]["email"] = cred["emails"]["alice"]
        sender_cap, _sender_agent = await register_owned(
            ctx, "sender_a", owner_principal_id=cred["pids"]["alice"], session="s1"
        )
        await ctx.comms(action="register", agent="recip_a", session="s1", role="builder")
        await _ks(ctx)._query(  # noqa: SLF001 - test-only teardown of the minted keep
            "DELETE keep WHERE key = $k", {"k": "session:s1"}
        )
        try:
            with pytest.raises(governed.GovernedDenied) as excinfo:
                await ctx.comms(
                    action="send", agent="sender_a", session="s1", to=["recip_a"],
                    body="a note with no session keep", grade="signal", capability=sender_cap,
                )
        except TypeError as error:  # HEAD: `comms` rejects capability= (§4.D unbuilt)
            pytest.fail(f"AppContext.comms rejected capability= — the §4.D seam is unbuilt: {error}")
        assert "register" in str(excinfo.value).lower(), (
            f"the missing-session-keep send DENIAL must teach 'register first' (§4.A), got: {excinfo.value}"
        )

    async def test_a_send_stamps_the_message_scope_to_the_session_keep(self, cred: dict[str, Any]) -> None:
        """⚠ RED at HEAD — a CREDENTIALED ``send`` in a session whose keep exists stamps the created
        message row's ``scope`` = the session keep's scope (``keep:<session-keep-id>``), resolved via the
        lifted ``resolve_write_scope``. RED at HEAD (SF-63-1 mints no keep → the ``keep is not None``
        guard reds); its GREEN is the ii-a integration (§4.F + SF-63-1 + the lift all landing)."""
        ctx = cred["ctx"]
        cred["holder"]["email"] = cred["emails"]["alice"]
        sender_cap, _sender_agent = await register_owned(
            ctx, "sender_b", owner_principal_id=cred["pids"]["alice"], session="s2"
        )
        await ctx.comms(action="register", agent="sender_b", session="s2", role="builder")
        await ctx.comms(action="register", agent="recip_b", session="s2", role="builder")
        keep = await _ks(ctx).get_by_key("session:s2")
        assert keep is not None, "SF-63-1 unbuilt: no session keep to stamp the send scope from"
        await _credentialed_send(
            ctx, agent="sender_b", session="s2", to=["recip_b"],
            body="a scoped note", grade="signal", capability=sender_cap,
        )
        rows = await ctx.agent_registry._query(  # noqa: SLF001 - test-only read of the message row
            "SELECT scope FROM message WHERE session = $s", {"s": "s2"}
        )
        assert rows and rows[0]["scope"] == pdp.keep_scope(bare_record_key(keep.id)), (
            f"the sent message's scope must be the session keep's scope (§4.A via resolve_write_scope), "
            f"got {rows[0]['scope'] if rows else '<no message row>'!r}"
        )

    async def test_a_credentialed_send_stamps_exactly_the_subjects_pair(self, cred: dict[str, Any]) -> None:
        """⚠ RED at HEAD — R1 owner EXACTNESS (ruling §2.3, the F4 effect leg the enforcement file's
        docstring PROMISED and nobody wrote). A (alice) keeps ``session:s1`` and HOUSEHOLDS B (bob); B's
        agent sends → the created message's owner is B's ``(principal, agent)`` pair, NOT the keeper A
        (Reading A / WB-2), NOT None (reading B), and its ``owner_agent`` IS the row's own ``sender``.
        This is the pin that makes the enforcement live-classify's non-None owner a REAL leg rather than
        a false clear (a build stamping the keeper/operator/any-non-None passes the non-None check but
        FAILS here). RED at HEAD: SF-63-1 mints no keep → the ``keep is not None`` guard reds."""
        ctx = cred["ctx"]
        ks = _ks(ctx)
        cred["holder"]["email"] = cred["emails"]["alice"]  # A = the keeper
        await ctx.comms(action="register", agent="alice_w1", session="s1", role="builder")
        keep = await ks.get_by_key("session:s1")
        assert keep is not None, "SF-63-1 unbuilt: alice's register minted no session keep"
        bob_cap, bob_agent = await register_owned(
            ctx, "bob_w1", owner_principal_id=cred["pids"]["bob"], session="s1"
        )
        await ks.add_household_member(keep_id=keep.id, member_email=cred["emails"]["bob"])  # A households B
        cred["holder"]["email"] = cred["emails"]["bob"]  # B sends with B's own token + capability
        await _credentialed_send(
            ctx, agent="bob_w1", session="s1", to=["alice_w1"],
            body="B's note into A's session", grade="signal", capability=bob_cap,
        )
        rows = await ctx.agent_registry._query(  # noqa: SLF001 - test-only read of the message row
            "SELECT owner_principal, owner_agent, sender FROM message WHERE session = $s", {"s": "s1"}
        )
        assert rows, "the credentialed send created no message row"
        row = rows[0]
        assert same_record(row["owner_principal"], f"principal:{cred['pids']['bob']}"), (
            f"the send owner_principal must be the SENDER B's principal (§2.3 subject.principal_id), NOT "
            f"the keeper A (Reading A / WB-2), NOT None. got {row['owner_principal']!r}; "
            f"bob=principal:{cred['pids']['bob']} alice(keeper)=principal:{cred['pids']['alice']}"
        )
        assert not same_record(row["owner_principal"], f"principal:{cred['pids']['alice']}"), (
            "the send owner_principal is the KEEPER A (Reading A) — the ownership forgery R1 exists to "
            "catch: B's send owned by A the moment A householded B (§2.2 / WB-2)"
        )
        assert same_record(row["owner_agent"], f"agent:{bob_agent}"), (
            f"the send owner_agent must be the SENDER B's agent, got {row['owner_agent']!r}"
        )
        assert str(row["owner_agent"]) == str(row["sender"]), (
            f"the send owner_agent must equal the row's own sender (R8 structural leg), got "
            f"owner_agent={row['owner_agent']!r} sender={row['sender']!r}"
        )

    async def test_a_tokenless_send_denies_and_creates_no_message_row(self, cred: dict[str, Any]) -> None:
        """⚠ RED at HEAD — R2 (anti-vacuity INVERTED). A TOKENLESS ``send`` (no ambient token, no
        capability) DENIES with ``GovernedDenied`` and creates ZERO message rows — the deny fires at
        the unconditional ``_resolve_subject`` (§2.3), BEFORE any write. At HEAD ``_comms_send`` resolves
        no subject → the send SUCCEEDS and WRITES a row → the ``raises`` reds (DID NOT RAISE) and the
        zero-rows assert would red. CONTROL: the SAME send CREDENTIALED writes exactly ONE row (so the
        tokenless deny is the MISSING IDENTITY, not a send that never works)."""
        ctx = cred["ctx"]
        holder = cred["holder"]
        holder["email"] = cred["emails"]["alice"]
        alice_cap, _alice_agent = await register_owned(
            ctx, "alice_w1", owner_principal_id=cred["pids"]["alice"], session="s1"
        )
        await ctx.comms(action="register", agent="alice_w1", session="s1", role="builder")
        await ctx.comms(action="register", agent="recip", session="s1", role="builder")
        before = await _message_count(ctx, "s1")
        # TOKENLESS: clear the ambient token and present NO capability → the write must DENY, writing nothing.
        holder["email"] = None
        with pytest.raises(governed.GovernedDenied):
            await ctx.comms(
                action="send", agent="alice_w1", session="s1", to=["recip"],
                body="a tokenless note", grade="signal",
            )
        after = await _message_count(ctx, "s1")
        assert after == before == 0, (
            f"a tokenless send must create ZERO message rows (the deny fires at _resolve_subject, before "
            f"any write) — before={before} after={after}. At HEAD the unenforced send writes a row → reds"
        )
        # CONTROL — the SAME send CREDENTIALED writes exactly one row.
        holder["email"] = cred["emails"]["alice"]
        await _credentialed_send(
            ctx, agent="alice_w1", session="s1", to=["recip"],
            body="a credentialed note", grade="signal", capability=alice_cap,
        )
        assert await _message_count(ctx, "s1") == 1, (
            "the credentialed control send must write exactly ONE message row — proving the tokenless "
            "deny above is the MISSING IDENTITY, not a send that never works"
        )

    async def test_a_sender_removed_from_the_session_household_is_denied_at_send(
        self, cred: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD — R5 the §4.A send-half grant flip (§6). B is householded then REMOVED; B's
        send then DENIES, because ``send`` resolves the session scope through
        ``resolve_write_scope(subject, session_scope, default=session_scope)`` with ``session_scope``
        EXPLICIT (never None), so ``_grantable(subject, session_scope)`` runs on EVERY send and a removed
        member is no longer householded → GovernedDenied. RED at HEAD: SF-63-1 mints no keep → the
        ``keep is not None`` guard reds (and at HEAD send checks no household → would succeed)."""
        ctx = cred["ctx"]
        ks = _ks(ctx)
        cred["holder"]["email"] = cred["emails"]["alice"]
        await ctx.comms(action="register", agent="alice_w1", session="s1", role="builder")
        keep = await ks.get_by_key("session:s1")
        assert keep is not None, "SF-63-1 unbuilt: register minted no session keep"
        bob_cap, _bob_agent = await register_owned(
            ctx, "bob_w1", owner_principal_id=cred["pids"]["bob"], session="s1"
        )
        await ks.add_household_member(keep_id=keep.id, member_email=cred["emails"]["bob"])
        await ks.remove_household_member(keep_id=keep.id, member_email=cred["emails"]["bob"])
        cred["holder"]["email"] = cred["emails"]["bob"]
        try:
            with pytest.raises(governed.GovernedDenied):
                await ctx.comms(
                    action="send", agent="bob_w1", session="s1", to=["alice_w1"],
                    body="a note from a removed member", grade="signal", capability=bob_cap,
                )
        except TypeError as error:  # HEAD: `comms` rejects capability= (§4.D unbuilt)
            pytest.fail(f"AppContext.comms rejected capability= — the §4.D seam is unbuilt: {error}")

    async def test_perturbing_the_lifted_seam_changes_send(
        self, cred: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD — R5 the send-half MUTATION proof (the twin of the remember-half in
        ``TestTheSharedGrantPredicateIsProvenByMutation``). POSITIVE CONTROL: a REMOVED member's send
        DENIES on the unperturbed path. Then a PERMISSIVE ``governed.resolve_write_scope`` (grant check
        removed) makes the SAME removed-member send SUCCEED — ONLY IF ``send`` routes through the lifted
        seam. So BOTH halves flip under the seam mutation, as §4.A's rider demands. RED at HEAD: SF-63-1
        mints no keep → the ``keep is not None`` guard reds."""
        ctx = cred["ctx"]
        ks = _ks(ctx)
        cred["holder"]["email"] = cred["emails"]["alice"]
        await ctx.comms(action="register", agent="alice_w1", session="s1", role="builder")
        keep = await ks.get_by_key("session:s1")
        assert keep is not None, "SF-63-1 unbuilt: register minted no session keep"
        bob_cap, _bob_agent = await register_owned(
            ctx, "bob_w1", owner_principal_id=cred["pids"]["bob"], session="s1"
        )
        await ks.add_household_member(keep_id=keep.id, member_email=cred["emails"]["bob"])
        await ks.remove_household_member(keep_id=keep.id, member_email=cred["emails"]["bob"])
        cred["holder"]["email"] = cred["emails"]["bob"]
        # POSITIVE CONTROL — the removed member's send DENIES on the unperturbed grant path.
        try:
            with pytest.raises(governed.GovernedDenied):
                await ctx.comms(
                    action="send", agent="bob_w1", session="s1", to=["alice_w1"],
                    body="control", grade="signal", capability=bob_cap,
                )
        except TypeError as error:
            pytest.fail(f"AppContext.comms rejected capability= — the §4.D seam is unbuilt: {error}")

        def _permissive(subject: Any, scope: Any, *, default: Any) -> Any:
            return default if scope is None else scope

        monkeypatch.setattr(governed, "resolve_write_scope", _permissive, raising=False)
        # With the seam permissive, a ROUTED send accepts the session scope even for the removed member.
        # If send does NOT route through the seam, it still denies → this reds.
        try:
            await ctx.comms(
                action="send", agent="bob_w1", session="s1", to=["alice_w1"],
                body="routed", grade="signal", capability=bob_cap,
            )
        except governed.GovernedDenied:
            pytest.fail(
                "a removed member's send STILL denied under a permissive governed.resolve_write_scope — "
                "send does NOT route through the lifted seam (§4.A / §6 send-half unbuilt; "
                "ROUTING-IS-NOT-SHARING)"
            )
        except TypeError as error:
            pytest.fail(f"AppContext.comms rejected capability= — the §4.D seam is unbuilt: {error}")


class TestThePrincipalResolutionIsSharedByMutation:
    """R4 VALUE-mutation (ruling §3.1 / §3.3 — ONE derivation). The send owner (Q1, via
    ``resolve_subject``) and the keep keeper (Q2, via ``_comms_register``) are BOTH the transport
    token's admitted principal, resolved through ONE lifted ``governed.resolve_principal``. Perturb that
    seam to return a FIXED admitted principal P* and watch BOTH move: a private copy on either path does
    NOT move. The STRUCTURAL twin (``function_calls_named``) lives in
    ``test_comms_capability_63b_ii_a.py``."""

    async def test_perturbing_resolve_principal_changes_both_send_owner_and_keep_keeper(
        self, cred: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD — perturb ``governed.resolve_principal`` → a DISTINCT admitted principal P*.
        (a) ``resolve_subject`` (send's identity) must then resolve P* as the Subject's principal; at
        HEAD ``resolve_subject`` INLINES ``principal_store.get_by_email`` (no ``resolve_principal`` call)
        → the Subject stays alice → the ``== P*`` assert reds. (b) a register's minted keep must then be
        kept by P*; at HEAD ``_comms_register`` mints no keep → the ``keep is not None`` guard reds.
        POSITIVE CONTROL: unpatched, ``resolve_subject`` resolves alice's REAL principal."""
        ctx = cred["ctx"]
        ks = _ks(ctx)
        # A DISTINCT admitted principal P* the SHARED seam will return for EVERY token.
        p_star = await _ps(ctx).create(email="pstar@example.com", role="member")
        p_star_pid = bare_record_key(p_star.id)
        cred["holder"]["email"] = cred["emails"]["alice"]
        alice_cap, _alice_agent = await register_owned(
            ctx, "alice_w1", owner_principal_id=cred["pids"]["alice"], session="s1"
        )
        # POSITIVE CONTROL — unpatched, resolve_subject resolves alice's real principal.
        control_subject = await ctx._resolve_subject(alice_cap)  # noqa: SLF001 - the composition root
        assert control_subject.principal_id == cred["pids"]["alice"], (
            f"positive control: unpatched _resolve_subject must resolve alice's real principal, got "
            f"{control_subject.principal_id!r}"
        )

        async def _fixed_principal(access_token: Any, *, principal_store: Any) -> Any:
            return p_star

        monkeypatch.setattr(governed, "resolve_principal", _fixed_principal, raising=False)
        # (a) SEND owner (Q1): resolve_subject now yields P* as the principal.
        mutated_subject = await ctx._resolve_subject(alice_cap)  # noqa: SLF001
        assert mutated_subject.principal_id == p_star_pid, (
            f"perturbing governed.resolve_principal did NOT change resolve_subject's principal (got "
            f"{mutated_subject.principal_id!r}, expected {p_star_pid!r}) — resolve_subject does not route "
            f"through the shared resolve_principal (ruling §3.1; a private get_by_email copy)"
        )
        # (b) KEEP keeper (Q2): a register now mints a keep kept by P*.
        await ctx.comms(action="register", agent="reg_after_patch", session="s9", role="builder")
        keep = await ks.get_by_key("session:s9")
        assert keep is not None and keep.keeper_id == p_star_pid, (
            f"perturbing governed.resolve_principal did NOT change the register-minted keep's keeper — "
            f"_comms_register does not route through the shared resolve_principal (ruling §3.1 / §3.3 "
            f"ONE derivation: Q1 and Q2 must be the SAME seam). keep={keep!r}, expected keeper {p_star_pid!r}"
        )


class _RaisingPrincipalStore:
    """A principal store whose ``get_by_email`` RAISES — the short-circuit proof for the unit pin below.
    §3.1's None-returning legs (token absent / carries no subject) decide at the SEAM, with no email to
    look up, so a correct ``resolve_principal`` NEVER consults the store on those legs (adversary3
    §D-NULLTOKEN verified the reference short-circuits). If it IS consulted, the seam reached the store
    for an identity-less token → the short-circuit is broken → this fails legibly rather than letting a
    real (or None-returning) store make a dropped-guard build look correct."""

    async def get_by_email(self, email: Any) -> Any:
        raise AssertionError(
            f"resolve_principal consulted the principal store (get_by_email({email!r})) for an "
            f"identity-less token — §3.1's None-returning legs must short-circuit BEFORE the store "
            f"(the absent/empty-subject decision is at the seam, not a downstream lookup)"
        )


class TestResolvePrincipalReturnsNoneForAnIdentitylessToken:
    """RULING §3.1 — the lifted ``governed.resolve_principal(access_token, *, principal_store)`` returns
    ``None`` iff the token is ABSENT **or** carries no subject, and decides so at the SEAM (no store
    lookup — adversary3 §D-NULLTOKEN). A pure UNIT pin that bypasses the ``cred`` harness: that harness's
    ``_patched_get_access_token`` can only ever build ``access_token(subject=<str>)`` and NEVER return
    ``None`` from ``get_access_token()`` — the realistic production absence shape an unauthenticated call
    yields — so the token-ABSENT leg is structurally unpinnable through it (#131 THE TEST ENVIRONMENT IS
    A FICTION: the harness guarantees the one condition under which the bug is invisible). MP-6
    (``TestATokenlessRegisterIsOwnerlessAndMintsNoKeep``) pins only the empty-subject mode, through the
    register path; this pins BOTH None-returning modes DIRECTLY on the seam. Added per adversary3's
    D-NULLTOKEN finding (``REPORT-adversary3-63b-ii-a.md`` §D-NULLTOKEN).

    RED at HEAD: ``governed.resolve_principal`` is a builder deliverable that does not exist at
    ``9138687`` (``lore_verify`` → not_found); the ``getattr`` unbuilt-signal is this file's established
    idiom (``TestResolveWriteScopeIsLifted``). Tolerant of a sync OR async seam (``_maybe_await``)."""

    async def test_a_none_token_resolves_to_none_without_consulting_the_store(self) -> None:
        """⚠ RED at HEAD — the REQUIRED leg (adversary3 D-NULLTOKEN). ``resolve_principal(None, …)``
        returns ``None`` and does NOT raise. The WRONG BUILD it kills: a ``resolve_principal`` that reads
        ``access_token.subject`` directly (no ``getattr`` guard — the natural non-defensive spelling, a
        plausible builder cleanup of ``resolve_subject``'s defensive ``getattr``) — it crashes
        ``AttributeError`` on the ``None`` token yet passes the ENTIRE ``cred``-driven file, because that
        harness cannot produce a ``None`` token (adversary3 confirmed empirically: the ``.subject``-direct
        door goes ``21 passed`` on this file). The raising store proves §3.1's decision is at the seam,
        before any lookup — but the ``.subject``-direct build crashes before ever reaching it."""
        seam = getattr(governed, "resolve_principal", None)
        if seam is None:
            pytest.fail(
                "governed.resolve_principal unbuilt (ruling §3.1) — the token-absent None leg; the seam "
                "lifted from resolve_subject step (2) does not exist yet"
            )
        result = await _maybe_await(seam(None, principal_store=_RaisingPrincipalStore()))
        assert result is None, (
            f"resolve_principal(None, …) must return None for an ABSENT token (§3.1: None iff the token "
            f"is absent or carries no subject) — never raise, never fabricate. got {result!r}. A build "
            f"doing `access_token.subject` (no getattr guard) crashes AttributeError here instead of "
            f"returning None (adversary3 D-NULLTOKEN: the #131 gap the cred harness cannot express)"
        )

    async def test_an_empty_subject_token_resolves_to_none_without_consulting_the_store(self) -> None:
        """⚠ RED at HEAD — the companion leg (§3.1 'carries no subject'), pinned DIRECTLY on the seam
        (MP-6 pins this mode only through the register path). ``access_token(subject="")`` → the subject
        is falsy → ``None``, store untouched (``resolve_subject`` step (2) uses ``if not email`` —
        falsiness, so the faithful extraction short-circuits on ``""`` too). Kills a build whose
        identity-less guard is ``if email is None`` (None-only) rather than ``if not email`` (falsiness):
        it would fall through to ``get_by_email("")`` → the raising store fires (or a real store's None →
        GovernedDenied), neither of which is the ruled ``None`` return."""
        seam = getattr(governed, "resolve_principal", None)
        if seam is None:
            pytest.fail("governed.resolve_principal unbuilt (ruling §3.1) — the empty-subject None leg")
        result = await _maybe_await(
            seam(access_token(subject=""), principal_store=_RaisingPrincipalStore())
        )
        assert result is None, (
            f"resolve_principal(access_token(subject=''), …) must return None for a token that carries "
            f"no subject (§3.1) — never raise, never consult the store. got {result!r}"
        )


class TestTheAgentArgumentMustMatchTheCapability:
    """RULING §2.3 / §9 B2 — the ONE agent≡capability MISMATCH case pinned in ii-a (the ≥2×≥2 battery is
    63b-iii's headline; the EQUALITY CHECK ``_bare(agent_row.id) == subject.agent_id`` is BUILT in ii-a).
    An ``agent=`` selecting an identity the presented capability did NOT prove is F4's kernel: 'no
    argument moves the stamp'. Added per the design authority's fidelity read (ruling §11.2 MP-5), which
    found no test drove a sibling's capability."""

    async def test_a_send_with_a_siblings_capability_denies_and_writes_nothing(
        self, cred: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD — a ``send`` whose ``agent=`` names ``alice_w1`` but whose ``capability=``
        proves a SIBLING owned by the SAME principal (``alice_w2``) must DENY at the §2.3 agent≡subject
        check and write ZERO message rows. Both agents are alice's, so ``stamp_owner``'s
        ``(principal, agent)`` binding for ``alice_w2`` HOLDS under alice's token — ONLY the
        agent≡subject check can deny. RED at HEAD on the ``keep is not None`` guard (SF-63-1 unbuilt); if
        the send is reached, ``comms`` rejects ``capability=`` (§4.D unbuilt) → the wrapper reds. The
        WRONG BUILD it kills (§2.3) is a ``_comms_send`` that OMITS ``_bare(agent_row.id) ==
        subject.agent_id``: stamp_owner verifies alice_w2, nothing denies, the send proceeds with
        ``sender=alice_w1`` and ``owner_agent=alice_w2`` — that build passes R1 (honest fixture), R2, R6
        and the live-classify (an honest send). POSITIVE CONTROL: the SAME send with ``alice_w1``'s OWN
        capability writes exactly one row."""
        ctx = cred["ctx"]
        cred["holder"]["email"] = cred["emails"]["alice"]
        # TWO agents, both OWNED BY ALICE; register_owned mints each one's one-time capability.
        w1_cap, _w1_agent = await register_owned(
            ctx, "alice_w1", owner_principal_id=cred["pids"]["alice"], session="s1"
        )
        w2_cap, _w2_agent = await register_owned(
            ctx, "alice_w2", owner_principal_id=cred["pids"]["alice"], session="s1"
        )
        # A session keep (tool register, under alice's token — re-register of alice_w1 mints/joins it).
        await ctx.comms(action="register", agent="alice_w1", session="s1", role="builder")
        keep = await _ks(ctx).get_by_key("session:s1")
        assert keep is not None, "SF-63-1 unbuilt: register minted no session keep"
        before = await _message_count(ctx, "s1")
        # MISMATCH — agent= names alice_w1, capability proves the sibling alice_w2.
        try:
            with pytest.raises(governed.GovernedDenied) as excinfo:
                await ctx.comms(
                    action="send", agent="alice_w1", session="s1", to=["alice_w2"],
                    body="a note whose agent= does not match the capability", grade="signal",
                    capability=w2_cap,
                )
        except TypeError as error:  # HEAD: `comms` rejects capability= (§4.D unbuilt)
            pytest.fail(f"AppContext.comms rejected capability= — the §4.D seam is unbuilt: {error}")
        assert "alice_w1" in str(excinfo.value), (
            f"the agent≡capability mismatch DENY must NAME the requested agent= (§2.3 teaching 'agent= "
            f"names X but the capability verifies as Y'), got: {excinfo.value}"
        )
        after = await _message_count(ctx, "s1")
        assert after == before == 0, (
            f"a mismatched-capability send must write ZERO message rows (the deny fires at the §2.3 "
            f"agent≡subject check, before any write) — before={before} after={after}. A build that omits "
            f"the check stamps owner_agent=alice_w2 with sender=alice_w1 and writes a row (F4's kernel: "
            f"'no argument moves the stamp')"
        )
        # POSITIVE CONTROL — the SAME send with alice_w1's OWN capability writes exactly one row.
        await _credentialed_send(
            ctx, agent="alice_w1", session="s1", to=["alice_w2"],
            body="a matching-capability note", grade="signal", capability=w1_cap,
        )
        assert await _message_count(ctx, "s1") == 1, (
            "the control send (agent= matches its own capability) must write exactly ONE row — proving "
            "the mismatch deny above is the agent≡capability check, not a send that never works"
        )


class TestATokenlessRegisterIsOwnerlessAndMintsNoKeep:
    """RULING §3.2 (reading α) / §9 B1 — a TOKENLESS register SUCCEEDS OWNERLESS, mints NO keep, and its
    render NAMES the bound. F2's letter (the pkt-62 registry pin) lifted from the registry to the TOOL
    layer: nothing is fabricated. Added per the design authority's fidelity read (ruling §11.2 MP-6),
    which found nothing drove a tokenless register on the credentialed harness. The empty-subject token
    is the harness's native tokenless mode (``holder['email'] = None`` → ``access_token(subject='')``);
    the ``get_access_token()``-returns-``None`` variant is NOT natively reachable via this harness (see
    the report flag)."""

    async def test_a_tokenless_register_succeeds_ownerless_mints_no_keep_and_names_the_bound(
        self, cred: dict[str, Any]
    ) -> None:
        """⚠ RED at HEAD — a tokenless (empty-subject) ``register`` SUCCEEDS (no raise — the 58 corpse
        sites pin that half), then: (1) the agent row's ``owner_principal`` IS NONE (F2 at the tool layer
        — never fabricated); (2) NO ``session:<s>`` keep is kept; (3) the render NAMES the α bound
        (ownerless · the DERIVED requires_capability=True deny-verbs · the two remedies). RED at HEAD on
        (3): at HEAD the register is already ownerless + keepless, but the render carries NO bound line
        (F10 — the α-ownerless render is unbuilt). The WRONG BUILD it kills (§3.2 α) is the Reading-A
        HYBRID ``principal = await resolve_principal(...) or await resolve_operator_principal(...)`` on
        the tokenless branch: it FABRICATES the fleet's admin as keeper AND owner — passing R3 (alice ≠
        carol), R4 (the patched seam returns P*, so the fallback never runs) and the corpse (registers
        succeed) — but (1) reds (owner=carol≠None), (2) reds (a keep is minted), and (3) reds (a keeper
        line, not the ownerless bound). POSITIVE CONTROL: a CREDENTIALED register in a fresh session
        DOES mint a keep."""
        ctx = cred["ctx"]
        cred["holder"]["email"] = None  # the empty-subject token (harness wraps None → subject="")
        try:
            result = await ctx.comms(
                action="register", agent="ownerless_w1", session="s_tok", role="builder"
            )
        except governed.GovernedDenied as error:  # a reading-β build (deny the register) — NOT ruled for ii-a
            pytest.fail(
                f"a tokenless register DENIED (reading β) — ii-a rules reading α: ownerless SUCCESS, no "
                f"keep, a named bound (RULING §3.2; β's re-open trigger is 63c). got: {error}"
            )
        rendered = str(result).lower()
        # (1) F2 at the tool layer — the agent is OWNERLESS, never fabricated.
        rows = await ctx.agent_registry._query(  # noqa: SLF001 - test-only read of the agent row's owner
            "SELECT owner_principal FROM agent WHERE name = $n", {"n": "ownerless_w1"}
        )
        assert rows, "the tokenless register wrote no agent row (reading α: it must SUCCEED ownerless)"
        assert rows[0].get("owner_principal") is None, (
            f"a tokenless register FABRICATED an owner (§3.2 α forbids it; F2 at the tool layer) — the "
            f"Reading-A hybrid stamps the fleet admin (carol). got owner_principal="
            f"{rows[0].get('owner_principal')!r}, carol={cred['pids']['carol']!r}"
        )
        # (2) no keep kept.
        assert await _ks(ctx).get_by_key("session:s_tok") is None, (
            "a tokenless register MINTED a session keep (§3.2 α: an ownerless registrant keeps nothing) "
            "— the Reading-A hybrid mints one kept by the fabricated admin"
        )
        # (3) the render NAMES the α bound — reds at HEAD (no bound line, F10).
        required = {
            verb for verb, spec in _COMMS_ACTIONS.items()
            if getattr(spec, "requires_capability", False)
        }
        missing_verbs = [verb for verb in required if verb not in rendered]
        ownerless_named = any(token in rendered for token in ("ownerless", "no owner", "no owning"))
        remedies_named = "credential" in rendered and "migrate-governed" in rendered
        bound_named = ownerless_named and not missing_verbs and remedies_named
        assert bound_named, (
            f"the tokenless register render must NAME the α bound (§3.2): the agent holds no owner, the "
            f"requires_capability=True verbs that deny for it (DERIVED; ii-a={{send}}), and the two "
            f"remedies (present the fleet credential + register a fresh name / `lore-adm migrate-governed "
            f"--table agent`). §9 B1 re-open trigger: 63c (when `agent` becomes a governed population, "
            f"reading β — deny the register — is the natural shape). derived_deny_verbs={sorted(required)} "
            f"missing_from_render={missing_verbs} render={rendered!r}"
        )
        # POSITIVE CONTROL — a CREDENTIALED register in a fresh session DOES mint a keep.
        cred["holder"]["email"] = cred["emails"]["alice"]
        await ctx.comms(action="register", agent="cred_w1", session="s_cred", role="builder")
        assert await _ks(ctx).get_by_key("session:s_cred") is not None, (
            "the credentialed control register minted NO session keep — the tokenless no-keep above must "
            "be the MISSING IDENTITY, not a build that never mints keeps (SF-63-1)"
        )
