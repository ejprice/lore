"""Packet SDK3 contract, round 3 — operator ruling R7 (F8/F7): record ids are SDK-native VALUES; the
text lore serves or persists comes from the ENGINE, never from ``str(RecordID)``.

``docs/plans/v2/sdk3-rulings.md`` R7 (replaces R6's F8/F7): SDK ``str(RecordID)`` changed between 3.0.0
(``keep:⟨01J…⟩``) and 3.0.1 (``keep:`01J…```), and ``RecordID.parse`` is ``split(":", 1)``. The engine
renders BARE (``keep:01J…``) — the form lore already persists. Ruled, all SDK-native:
(a) ids travel as ``RecordID`` values end to end; (b) built with ``RecordID(table, key)`` from
``.table_name`` / ``.id``; (c) text → id via ``StringRecordId(text)`` (server-parsed; reads both bracket
styles); (d) served/persisted text from the engine (``<string> id``) or ``.table_name + ":" + .id``, never
``str(RecordID)``. The four-plus ``partition(":")`` / ``split(":")`` re-parsers are deleted.

THE FIXTURE DISCRIMINATES BY RENDERING (the brief's "pins must hold under BOTH SDK renderings"): the
``rendering`` parameter patches ``RecordID.__str__`` for the duration of the action under test to each
rendering an SDK release has shipped for a string key — ``angle`` (3.0.0: ``t:⟨k⟩``) and ``backtick``
(3.0.1: ``t:`k```) — applied to EVERY string key, not only digit-led ones, so the pins need not hunt for
an id of a particular shape (``installed`` leaves the installed SDK alone). A build that still derives
served or persisted text from ``str(RecordID)`` fails under at least one rendering; a build that follows
R7 is indifferent to all three. The patch never reaches the wire: the SDK encodes a ``RecordID`` from
``table_name`` / ``id`` (CBOR tag 8), read in both SDKs' ``data/cbor.py``.

Moved here from ``test_sdk3_result_shapes`` (round 1/2 R7–R9), re-cut for R7: the round-trip pin no longer
asserts the SDK 2.0 RENDERING (R7 forbids depending on it); it asserts value identity instead.
"""

from __future__ import annotations

import contextlib
import importlib
import uuid
from collections.abc import AsyncIterator, Callable, Iterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _governed_contract import credentialed_app_context
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.keeps import KeepStore
from loremaster.principals import PrincipalHasKeepsError, PrincipalStore
from surrealdb import RecordID


# The renderings an SDK release has shipped for a string record key (R7 grounds), applied to EVERY
# string key so the pin does not depend on drawing a digit-led id.
def _angle(record_id: Any) -> str:
    """SDK 3.0.0's rendering of a string key."""
    return f"{record_id.table_name}:⟨{record_id.id}⟩"


def _backtick(record_id: Any) -> str:
    """SDK 3.0.1's rendering of a string key."""
    return f"{record_id.table_name}:`{record_id.id}`"


_RENDERINGS: dict[str, Callable[[Any], str] | None] = {
    "installed": None,
    "angle": _angle,
    "backtick": _backtick,
}

# Every key SHAPE lore mints or admits (round 1/2 R7, kept): a keep ULID (digit-led), an engine-style
# principal id digit-led and letter-led, a uuid5 hex string (agents/briefs/memories), a path-like
# chunk identity, an integer key.
_KEY_SHAPES: dict[str, str | int] = {
    "ulid": "01JCXZ3Q9V8M2T5K7R4N6P1W0Y",
    "engine_style_digit_led": "0ysb7r5es9z0ysb7r5es",
    "engine_style_letter_led": "z0ysb7r5es9z0ysb7r5e",
    "uuid5_hex": uuid.uuid5(uuid.NAMESPACE_URL, "sdk3").hex,
    "path": "loremaster/store/_txn.py",
    "integer": 42,
}

# The keeper of the keep the served-id pins create, and how many engine-minted principals the
# refuse-while-keeping pin will mint looking for a digit-led one (~28% are; P(miss in 40) < 1e-5).
_KEEPER_EMAIL = "sdk3-keeper@example.com"
_DIGIT_LED_PRINCIPAL_ATTEMPTS = 40


@contextlib.contextmanager
def _rendered(monkeypatch: pytest.MonkeyPatch, rendering: str) -> Iterator[None]:
    """Render every string ``RecordID`` key as ``rendering`` for the duration of the block."""
    render = _RENDERINGS[rendering]
    if render is None:
        yield
        return
    original = RecordID.__str__

    def _patched(self: RecordID) -> str:
        if isinstance(self.id, str):
            return render(self)
        return original(self)

    with monkeypatch.context() as patch:
        patch.setattr(RecordID, "__str__", _patched)
        yield


@pytest_asyncio.fixture()
async def store_env() -> AsyncIterator[SurrealEnv]:
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    try:
        yield env
    finally:
        await drop_database(env)


@pytest_asyncio.fixture()
async def stores(store_env: SurrealEnv) -> AsyncIterator[tuple[PrincipalStore, KeepStore, Any]]:
    """Ready principal + keep stores on the fresh database, and an admin connection for oracle reads."""
    wiring: dict[str, Any] = {
        "url": store_env.url,
        "namespace": store_env.namespace,
        "database": store_env.database,
        "user": store_env.user,
        "password": store_env.password,
    }
    principal_store = PrincipalStore(**wiring)
    keep_store = KeepStore(**wiring)
    admin = await connect_admin(store_env)
    try:
        await principal_store.ensure_ready()
        await keep_store.ensure_ready()
        yield principal_store, keep_store, admin
    finally:
        await admin.close()
        await keep_store.close()
        await principal_store.close()


class TestARecordIdRoundTripsAsAValue:
    """R7 (a)/(b): an id built from its parts and the id the engine hands back are the SAME value —
    equal, hashable alike (a set or dict key), same table, same key — for every key shape lore mints.
    SDK 2.0's ``RecordID`` was unhashable, which is why lore keys sets and dicts by ``str(...)``
    (graph_surreal's de-dupe idiom — DROP LIST); that workaround is retired by this pin."""

    async def test_every_minted_key_shape_comes_back_as_the_value_that_was_written(
        self, store_env: SurrealEnv
    ) -> None:
        admin = await connect_admin(store_env)
        try:
            for name, key in _KEY_SHAPES.items():
                built = RecordID("shape", key)
                await run(admin, "CREATE $id SET kind = $kind", {"id": built, "kind": name})
                read = await run(admin, "SELECT VALUE id FROM shape WHERE kind = $kind", {"kind": name})
                assert len(read) == 1, f"{name}: expected one row, got {read!r}"
                returned = read[0]
                assert isinstance(returned, RecordID), f"{name}: came back as {type(returned).__name__}"
                assert (returned.table_name, returned.id) == ("shape", key), f"{name}: {returned!r}"
                assert returned == built, f"{name}: the returned id is not equal to the one built"
                assert {returned} == {built} and {built: name}[returned] == name, (
                    f"{name}: equal ids do not hash alike — they cannot key a set or a dict"
                )
        finally:
            await admin.close()

    async def test_server_parsed_text_in_either_bracket_style_names_the_same_record(
        self, store_env: SurrealEnv
    ) -> None:
        """R7 (c): text becomes an id through ``StringRecordId`` — parsed by the SERVER, so the bare form
        lore persists and BOTH bracket styles an SDK has rendered name the same record. (Imported inside
        the test, and looked up dynamically: SDK 2.0 has no ``StringRecordId`` — this pin is RED at HEAD by
        design — and the rest of the file must still collect and type-check against either SDK.)"""
        string_record_id: Any = getattr(importlib.import_module("surrealdb"), "StringRecordId", None)
        assert string_record_id is not None, "the installed SDK has no StringRecordId (R7 (c) needs it)"

        admin = await connect_admin(store_env)
        try:
            for name in ("ulid", "engine_style_digit_led", "engine_style_letter_led", "uuid5_hex"):
                key = _KEY_SHAPES[name]
                await run(admin, "CREATE $id SET kind = $kind", {"id": RecordID("shape", key), "kind": name})
                for text in (f"shape:{key}", f"shape:⟨{key}⟩", f"shape:`{key}`"):
                    found = await run(admin, "SELECT VALUE kind FROM $id", {"id": string_record_id(text)})
                    assert found == [name], f"{name}: {text!r} did not name the record (read {found!r})"
        finally:
            await admin.close()


class TestTheIdLoreServesNamesTheEnginesKey:
    """R7 (d): ``Keep.id`` is served text, so it is the ENGINE's ``keep:<key>`` — whatever the SDK's
    ``str(RecordID)`` says — and a keep is found again by it."""

    @pytest.mark.parametrize("rendering", sorted(_RENDERINGS))
    async def test_a_keep_round_trips_by_its_served_id(
        self, stores: tuple[PrincipalStore, KeepStore, Any], rendering: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        principal_store, keep_store, admin = stores
        await principal_store.create(email=_KEEPER_EMAIL)
        with _rendered(monkeypatch, rendering):
            keep = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="sdk3")
            again = await keep_store.get_keep(keep.id)
        engine_ids = await run(admin, "SELECT VALUE <string> id FROM keep")
        assert engine_ids == [keep.id], (
            f"[{rendering}] the served keep id {keep.id!r} is not the engine's text {engine_ids!r} — every "
            f"scope lore derives from it, and every row persisted before, stops matching"
        )
        assert again is not None and again.id == keep.id, (
            f"[{rendering}] a keep cannot be found again by its own served id"
        )

    async def test_a_keep_is_found_by_its_id_written_in_any_form(
        self, stores: tuple[PrincipalStore, KeepStore, Any]
    ) -> None:
        """R7 (c): a caller may hand lore an id in the bare form or either bracket style (an agent
        echoing what some SDK printed); each names the same keep."""
        principal_store, keep_store, admin = stores
        await principal_store.create(email=_KEEPER_EMAIL)
        await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="sdk3")
        key = (await run(admin, "SELECT VALUE record::id(id) FROM keep"))[0]
        for text in (f"keep:{key}", f"keep:⟨{key}⟩", f"keep:`{key}`"):
            found = await keep_store.get_keep(text)
            assert found is not None, (
                f"get_keep({text!r}) found nothing — the id was parsed by lore, not the server"
            )
            assert found.id == f"keep:{key}", f"get_keep({text!r}) served {found.id!r}"


class TestAKeeperCannotBeDeletedWhileKeeping:
    """``PrincipalStore.delete`` refuses while the principal keeps a keep: a ``keep.keeper`` link does not
    auto-clean, so the delete would dangle it. The refusal binds the id of the served ``Principal.id``;
    a build that re-parses rendered text binds the wrong key, finds no kept keep and DELETES THE KEEPER."""

    @pytest.mark.parametrize("rendering", sorted(_RENDERINGS))
    async def test_a_digit_led_keeper_is_refused_deletion(
        self, stores: tuple[PrincipalStore, KeepStore, Any], rendering: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        principal_store, keep_store, admin = stores
        keeper_email: str | None = None
        for attempt in range(_DIGIT_LED_PRINCIPAL_ATTEMPTS):
            email = f"sdk3-principal-{attempt}@example.com"
            await principal_store.create(email=email)
            key = (
                await run(admin, "SELECT VALUE record::id(id) FROM principal WHERE email = $e", {"e": email})
            )[0]
            if str(key)[:1].isdigit():
                keeper_email = email
                break
        assert keeper_email is not None, (
            f"premise: no digit-led principal id in {_DIGIT_LED_PRINCIPAL_ATTEMPTS} mints"
        )
        await keep_store.create_keep(keeper_email=keeper_email, type="project", name="sdk3")
        with _rendered(monkeypatch, rendering):
            served = await principal_store.get_by_email(keeper_email)
            assert served is not None and served.id == f"principal:{key}", (
                f"[{rendering}] the served principal id {getattr(served, 'id', None)!r} is not the engine's "
                f"principal:{key}"
            )
            try:
                await principal_store.delete(email=keeper_email)
            except PrincipalHasKeepsError:
                return
        remaining = await run(admin, "SELECT VALUE id FROM principal WHERE email = $e", {"e": keeper_email})
        raise AssertionError(
            f"[{rendering}] a principal who KEEPS a keep was deleted (rows left: {remaining!r}) — its keep's "
            f"keeper link now dangles; the refuse-while-keeping read bound a re-parsed rendering"
        )


class TestARegisteredAgentIsOwnedAndScopedByEngineIds:
    """R7 (a)/(d) through the served ``register`` path (``AppContext._comms_register``), which re-parses
    the served principal and session-keep ids at HEAD (``str(...).split(":", 1)``). Two PERSISTED values
    must name the engine's records: ``agent.owner_principal`` (a record link to the registrant) and
    ``agent.scope`` (the TEXT ``keep:<key>`` of the session keep — the inventory's agent.scope row, packet
    doc §F8). A build that re-parses a bracketed rendering links the agent to a principal that does not
    exist, and scopes it to a keep no governed read will ever match."""

    @pytest.mark.parametrize("rendering", ["angle", "backtick"])
    async def test_the_agent_links_its_principal_and_its_session_keeps_engine_text(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, rendering: str
    ) -> None:
        session = f"sdk3-{rendering}"
        async with credentialed_app_context(monkeypatch, tmp_path, principals={"alice": "member"}) as world:
            ctx, admin = world["ctx"], world["admin_conn"]
            world["holder"]["email"] = world["emails"]["alice"]
            with _rendered(monkeypatch, rendering):
                await ctx._comms_register(
                    agent="sdk3-agent",
                    session=session,
                    role="builder",
                    model=None,
                    spawned_by=None,
                    task_id=None,
                )
            principal_key = (
                await run(
                    admin,
                    "SELECT VALUE record::id(id) FROM principal WHERE email = $e",
                    {"e": world["emails"]["alice"]},
                )
            )[0]
            keep_text = await run(
                admin, "SELECT VALUE <string> id FROM keep WHERE key = $k", {"k": f"session:{session}"}
            )
            rows = await run(admin, "SELECT owner_principal, scope FROM agent WHERE name = 'sdk3-agent'")
            assert len(rows) == 1 and len(keep_text) == 1, (
                f"premise: one agent, one session keep ({rows!r}, {keep_text!r})"
            )
            assert rows[0]["owner_principal"] == RecordID("principal", principal_key), (
                f"[{rendering}] the agent's owner_principal {rows[0]['owner_principal']!r} is not the "
                f"registrant principal:{principal_key} — a re-parsed rendering minted a link to a "
                f"principal that does not exist"
            )
            assert rows[0]["scope"] == keep_text[0], (
                f"[{rendering}] the agent's persisted scope {rows[0]['scope']!r} is not its session "
                f"keep's engine text {keep_text[0]!r} — rows scoped before and after the bump would not match"
            )
