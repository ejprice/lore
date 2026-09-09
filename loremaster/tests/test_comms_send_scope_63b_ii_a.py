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

⚠ FLAG F-KEEPER (report §Decisions — a genuine §5/SF-63-1 ambiguity I do NOT resolve silently):
SF-63-1 says the keep's keeper is "the first registrant", and §4.D says register's identity comes from
the transport token. But the PRE-CUTOVER local fleet registers with NO capability/token, so HOW register
resolves the keeper principal to mint the keep is underspecified. Reading A: register resolves THE
operator principal (the lifted ``resolve_operator_principal`` single-principal resolution, consistent
with migrate). Reading B: the keep is keyed at register but its keeper is filled from the agent's
``owner_principal`` when one exists, ownerless otherwise. These produce different keeper assertions, so
the SF-63-1 pins below assert only the UNAMBIGUOUS core (key + type + resolvability) and I flag the
keeper mechanism to the lead. The harness creates ONE operator principal so the mint has a keeper under
EITHER reading.

STORE LAW cited: §1.8 (``keep.key`` UNIQUE over option<> — the deterministic natural key), §2 (CONTENT
writes). Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500). Per-test unique DB, reaped. NO skip.
pytest runs ``-n auto``.
"""

from __future__ import annotations

import inspect
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import build_memory_backend, member
from _surreal_harness import drop_database as drop_surreal_database
from _surreal_harness import make_env, surreal_password, surreal_url, surreal_user
from loremaster.config import LoreConfig
from loremaster.memory import local as local_mod
from loremaster.server import AppContext, LoreServer, build_app_context
from loresigil.testing import FakeEmbedder

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
    env = make_env(database=f"test_{uuid.uuid4().hex}", dim=_DIM)
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

_SURREAL_TEST_NAMESPACE = "lore_test"
_SURREAL_USER_ENV = "SURREAL_USER"
_SURREAL_PASS_ENV = "SURREAL_PASS"
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
    local, deliberately not imported; fixture DATA, no shared logic)."""
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
            "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9233},
        }
    )


@pytest_asyncio.fixture()
async def ctx(tmp_path: Path) -> AsyncIterator[AppContext]:
    """A real AppContext over an empty corpus (build_app_context, start_tasks=False) with ONE operator
    principal provisioned (so a register-time keep mint has a keeper under either FLAG F-KEEPER reading)."""
    slug = f"test_{uuid.uuid4().hex}"
    _pending_slugs.append(slug)
    context = await build_app_context(
        server=LoreServer(_config(slug)),
        embedder=FakeEmbedder(dim=_DIM),
        manifest_path=tmp_path / f"{slug}-m.db",
        snapshot_root=tmp_path / f"{slug}-snap",
        start_tasks=False,
    )
    await _ps(context).create(email="operator@example.com", role="member")
    try:
        yield context
    finally:
        await context.aclose()


class TestRegisterMintsTheSessionKeep:
    """SF-63-1 — ``register`` MINTS the session keep ``session:<session>`` (type ``session``), so a
    later ``send`` in that session can resolve it by key. Asserts the UNAMBIGUOUS core (key + type +
    resolvability); the KEEPER mechanism is FLAG F-KEEPER."""

    async def test_a_fresh_register_mints_a_resolvable_session_keep(self, ctx: AppContext) -> None:
        """⚠ RED at HEAD — after ``comms(action="register", session="s1", …)`` a keep bearing key
        ``session:s1`` and type ``session`` exists (resolvable by ``KeepStore.get_by_key``). At HEAD
        ``_comms_register`` mints NO keep → ``get_by_key`` returns None → reds (SF-63-1 unbuilt)."""
        await ctx.comms(action="register", agent="ag_one", session="s1", role="builder")
        keep = await _ks(ctx).get_by_key("session:s1")
        assert keep is not None, (
            "register did not mint a session keep keyed 'session:s1' (SF-63-1 unbuilt) — a later send "
            "cannot resolve the session scope by key"
        )
        assert keep.type == "session", (
            f"the register-minted keep must be type 'session' (SF-63-1), got {keep.type!r}"
        )

    async def test_register_is_idempotent_on_the_session_keep(self, ctx: AppContext) -> None:
        """⚠ RED at HEAD — a SECOND register in the same session resolves the SAME keep (the
        ``get_or_create_keyed`` CAS on the UNIQUE ``keep.key`` — store-ref §1.8), never a second row.
        RED at HEAD (no keep minted at all). Discriminates a build that mints a NEW keep per register."""
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


class TestSendResolvesTheSessionKeepScope:
    """§4.A — ``send`` resolves ``session:<session>`` by KEY and stamps the message scope through the
    lifted grant seam; a MISSING session keep at send is a teaching DENY, never a fallback."""

    async def test_a_send_with_no_session_keep_denies_teaching_register_first(
        self, ctx: AppContext
    ) -> None:
        """⚠ RED at HEAD — a ``send`` in a session with NO session keep DENIES with a teaching message
        naming ``register`` (§4.A: missing keep → GovernedDenied 'register first', never the project
        keep, never NONE). To reach ``send`` the sender+recipient must be registered; on the correct
        build register MINTS the keep, so the missing-keep state is manufactured by DELETING it before
        the send. At HEAD register mints no keep (so the delete is a no-op) AND send performs no keep
        resolution → the send SUCCEEDS instead of denying → reds (§4.A unbuilt)."""
        sender = await ctx.comms(action="register", agent="sender_a", session="s1", role="builder")
        await ctx.comms(action="register", agent="recip_a", session="s1", role="builder")
        # Manufacture the missing-keep state: delete any session keep register may have minted.
        await _ks(ctx)._query(  # noqa: SLF001 - test-only teardown of the minted keep
            "DELETE keep WHERE key = $k", {"k": "session:s1"}
        )
        assert sender is not None  # register returned (the send below is the pinned behaviour)
        with pytest.raises(governed.GovernedDenied) as excinfo:
            await ctx.comms(
                action="send", agent="sender_a", session="s1", to=["recip_a"],
                body="a note with no session keep", grade="signal",
            )
        assert "register" in str(excinfo.value).lower(), (
            f"the missing-session-keep send DENIAL must teach 'register first' (§4.A), got: {excinfo.value}"
        )

    async def test_a_send_stamps_the_message_scope_to_the_session_keep(self, ctx: AppContext) -> None:
        """⚠ RED at HEAD — a ``send`` in a session whose keep exists stamps the created message row's
        ``scope`` = the session keep's scope (``keep:<session-keep-id>``), resolved via the lifted
        ``resolve_write_scope``. RED at HEAD for a compound reason (message has no scope column until
        §4.F; send resolves no keep; SF-63-1 mints no keep) — this is the WRITE-side outcome §4.A owns;
        it depends on §4.F (piece 1) + SF-63-1 + the lift all landing, so its GREEN is the ii-a
        integration. (Report §Decisions: the finest-grained RED reasons are carried by the piece-1/
        resolve_write_scope/SF-63-1 pins; this pin is the composed behavioural outcome.)"""
        await ctx.comms(action="register", agent="sender_b", session="s2", role="builder")
        await ctx.comms(action="register", agent="recip_b", session="s2", role="builder")
        keep = await _ks(ctx).get_by_key("session:s2")
        assert keep is not None, "SF-63-1 unbuilt: no session keep to stamp the send scope from"
        await ctx.comms(
            action="send", agent="sender_b", session="s2", to=["recip_b"],
            body="a scoped note", grade="signal",
        )
        rows = await ctx.agent_registry._query(  # noqa: SLF001 - test-only read of the message row
            "SELECT scope FROM message WHERE session = $s", {"s": "s2"}
        )
        assert rows and rows[0]["scope"] == pdp.keep_scope(str(keep.id).split(":", 1)[-1]), (
            f"the sent message's scope must be the session keep's scope (§4.A via resolve_write_scope), "
            f"got {rows[0]['scope'] if rows else '<no message row>'!r}"
        )
