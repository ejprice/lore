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
from test_memory_replay_fidelity_63b_ib import dirty_world  # noqa: F401 - the replay fixture


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


class TestANonWordKeyServesTheEnginesText:
    """Round 4 — RS4 (operator ruling R8 F15): the ENGINE form (``<string> id``) is the text form for
    anything persisted or compared with persisted text; ``.table_name + ":" + .id`` is allowed only where
    no persisted comparison exists. The two forms AGREE for every word key (``[A-Za-z0-9_]``) — which is
    every key lore mints today — and DIFFER for a non-word key: the engine brackets it
    (``keep:⟨sdk3-non-word⟩``), the parts-join does not. A served keep id is compared with persisted text
    (every ``keep:<id>`` scope on a governed row), so it must be the engine's form for EVERY key the
    engine holds. A non-word keep key is constructed directly (a restored or legacy row; lore's own mint
    cannot produce one) — the case the word-key pins above cannot tell apart."""

    _NON_WORD_KEY = "sdk3-non-word.key"

    async def test_a_non_word_keep_key_is_served_as_the_engines_text_and_found_again(
        self, stores: tuple[PrincipalStore, KeepStore, Any]
    ) -> None:
        principal_store, keep_store, admin = stores
        await principal_store.create(email=_KEEPER_EMAIL)
        minted = await keep_store.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="sdk3")
        rows = await run(admin, "SELECT * FROM keep")
        assert len(rows) == 1, f"premise: one minted keep ({rows!r})"
        content = {field: value for field, value in rows[0].items() if field != "id"}
        for unique_field in ("name", "key"):  # never collide with the minted keep on a UNIQUE index
            if isinstance(content.get(unique_field), str):
                content[unique_field] = f"{content[unique_field]}-clone"
        await run(
            admin,
            "CREATE $id CONTENT $content",
            {"id": RecordID("keep", self._NON_WORD_KEY), "content": content},
        )
        engine_text = (
            await run(
                admin, "SELECT VALUE <string> id FROM $id", {"id": RecordID("keep", self._NON_WORD_KEY)}
            )
        )[0]
        assert engine_text != f"keep:{self._NON_WORD_KEY}", (
            f"premise: the engine brackets a non-word key (it rendered {engine_text!r}) — otherwise the two "
            f"R7 (d) forms agree and this pin cannot discriminate"
        )
        served = await keep_store.get_keep(engine_text)
        assert served is not None, (
            f"get_keep({engine_text!r}) found nothing: the engine's own text must name it"
        )
        assert served.id == engine_text, (
            f"the served id {served.id!r} of a non-word keep is not the engine's text {engine_text!r}; "
            f"F15: a "
            f"served id compared with persisted text (keep scopes) is the ENGINE form, never a parts-join"
        )
        assert minted.id != served.id, "premise: two distinct keeps"


class TestTheOwnerClassifierRecognisesTheOperatorWhateverItsKey:
    """Round 5 — C9 (ruling R12: "an SDK3 REGRESSION, not noise"). The governed-migrate precondition
    classifies the owners of owned-but-unscoped agents against THE operator principal
    (``principals._measured_counts`` → ``owner_classification``; the owner sentence in
    ``principals._owned_unscoped_part``). On both SDK3 references ``test_fixwave_a28_63c_i_a::
    TestTheMeasuredCountsAreTypedFields63cIAa28`` failed NONDETERMINISTICALLY as ``owner_classification
    'foreign'``: the operator's id was rendered one way (``Principal.id``, the parts-join) and each agent's
    ``owner_principal`` RecordID another (``str(RecordID)``, which SDK 3.0.0 brackets for a digit-led or
    non-word key — ~28 % of engine-minted principal ids are digit-led, hence the flake).

    DETERMINISTIC by construction: the operator principal is re-keyed to a FIXED key of each shape that
    renders differently across forms (digit-led; non-word), and each case also runs under the SDK
    renderings R7 names (``angle`` = 3.0.0, ``backtick`` = 3.0.1, applied to EVERY string key). The
    property is rendering-blind: the operator's own agents are classified ``operator`` and the owner
    sentence says so; with one foreign owner beside the operator the classification is ``mixed`` and the
    sample of OTHERS never names the operator. A build comparing two different text forms of one record
    fails at least one case on every run."""

    _OPERATOR_KEYS: dict[str, str] = {
        "digit_led": "9c9operator0000000000",
        "non_word": "c9-op.erator",
    }

    @staticmethod
    async def _rekey_the_operator(world: Any, key: str) -> None:
        """Replace the world's ONE (engine-minted) operator principal with the same row under ``key``."""
        rows = await run(world.connection, "SELECT * FROM principal")
        assert len(rows) == 1, f"premise: the governed world holds exactly its operator ({rows!r})"
        content = {field: value for field, value in rows[0].items() if field != "id"}
        await run(world.connection, "DELETE principal")
        await run(
            world.connection,
            "CREATE $id CONTENT $content",
            {"id": RecordID("principal", key), "content": content},
        )
        world.operator_bare = key

    @pytest.mark.parametrize("rendering", sorted(_RENDERINGS))
    @pytest.mark.parametrize("key_shape", sorted(_OPERATOR_KEYS))
    async def test_the_operators_own_agents_are_classified_operator(
        self, monkeypatch: pytest.MonkeyPatch, key_shape: str, rendering: str
    ) -> None:
        import test_fixwave_a19_63c_i_a as a19  # noqa: PLC0415 - module-qualified: never re-collect its tests
        from _governed_contract import AGENT_TABLE, seed_agent_governed, seed_agent_legacy  # noqa: PLC0415

        key = self._OPERATOR_KEYS[key_shape]
        async with a19._governed_world() as world:
            await self._rekey_the_operator(world, key)
            for index in range(3):
                await seed_agent_governed(
                    world.connection,
                    row_id=f"c9owned{index}",
                    name=f"c9owned{index}",
                    session="c9",
                    owner_principal=key,
                    owner_agent=None,
                    scope=None,
                )
            await seed_agent_legacy(world.connection, row_id="c9legacy", name="c9legacy", session="c9")
            with _rendered(monkeypatch, rendering):
                result = await world.migrate(AGENT_TABLE)
        counts = result.preconditions
        assert result.refused is True and counts is not None, f"premise: a verb-level refusal ({result!r})"
        assert counts.owned_but_unscoped_agents == 3 and counts.distinct_owner_principals == 1, counts
        assert counts.owner_classification == "operator", (
            f"[{key_shape} key {key!r}, rendering {rendering}] the operator's own 3 agents were classified "
            f"{counts.owner_classification!r}: the classifier compared two different TEXT forms of the same "
            f"record (C9 — str(RecordID) vs the served Principal.id). Compare one form, or the values."
        )
        assert "owned by the operator" in str(result.reason), (
            f"[{key_shape}, {rendering}] the owner sentence does not name the operator: {result.reason!r}"
        )

    @pytest.mark.parametrize("rendering", sorted(_RENDERINGS))
    @pytest.mark.parametrize("key_shape", sorted(_OPERATOR_KEYS))
    async def test_a_mixed_owner_sample_never_names_the_operator(
        self, monkeypatch: pytest.MonkeyPatch, key_shape: str, rendering: str
    ) -> None:
        import test_fixwave_a19_63c_i_a as a19  # noqa: PLC0415
        from _governed_contract import AGENT_TABLE, seed_agent_governed  # noqa: PLC0415

        key = self._OPERATOR_KEYS[key_shape]
        async with a19._governed_world() as world:
            await self._rekey_the_operator(world, key)
            await world.principal_store.create(email="c9-foreign@example.com", role="member")
            foreign_key = (
                await run(
                    world.connection,
                    "SELECT VALUE record::id(id) FROM principal WHERE email = $e",
                    {"e": "c9-foreign@example.com"},
                )
            )[0]
            for index, owner in enumerate((key, key, foreign_key)):
                await seed_agent_governed(
                    world.connection,
                    row_id=f"c9mixed{index}",
                    name=f"c9mixed{index}",
                    session="c9m",
                    owner_principal=owner,
                    owner_agent=None,
                    scope=None,
                )
            with _rendered(monkeypatch, rendering):
                result = await world.migrate(AGENT_TABLE)
        counts = result.preconditions
        assert result.refused is True and counts is not None, f"premise: a verb-level refusal ({result!r})"
        assert counts.distinct_owner_principals == 2, counts
        assert counts.owner_classification == "mixed", (
            f"[{key_shape} key {key!r}, rendering {rendering}] operator + one foreign owner classified "
            f"{counts.owner_classification!r} (C9: two text forms of the operator's record compared)"
        )
        sample = str(result.reason).split("a sample of the others:", 1)[-1]
        assert key not in sample, (
            f"[{key_shape}, {rendering}] the sample of OTHER owners names the operator ({key!r}): "
            f"{result.reason!r}"
        )
        assert foreign_key in sample, f"premise: the foreign owner is sampled: {result.reason!r}"


# ----------------------------------------------------------------------------------------------------
# Round 5 — R12 "C9's class is PINNED": one record compared (or served) through two text forms, at the
# siblings
# the round-5 sweep found. Each pin forces the SDK renderings (``_rendered``) so it is deterministic, and uses
# keys of the two shapes that render differently across forms: digit-led (SDK 3.0.0 brackets it in
# ``str(RecordID)``; the engine does not) and non-word (SDK 2.0 AND 3.0 bracket it with ⟨⟩; the engine renders
# backticks — measured 2026-11-07 on 3.3.5, packet doc §ROUND 5).
# ----------------------------------------------------------------------------------------------------

_C9_SIBLING_KEYS: dict[str, tuple[str, str]] = {
    # (principal key, agent key)
    "digit_led": ("9c9owner00000000", "7c9agent0000"),
    "non_word": ("c9-own.er", "c9-ag.ent"),
}


@pytest_asyncio.fixture()
async def governed_row_world(store_env: SurrealEnv) -> AsyncIterator[tuple[Any, Any]]:
    """An admin connection and a driver ``StoreHandle`` over the fresh database (no governed DDL needed: the
    gate's pre-read is a plain ``SELECT owner_principal, owner_agent, scope``)."""
    from _governed_contract import store_handle  # noqa: PLC0415

    admin = await connect_admin(store_env)
    try:
        await run(admin, "DEFINE TABLE c9gov SCHEMALESS")
        handle, _calls = store_handle(admin, url=store_env.url)
        yield admin, handle
    finally:
        await admin.close()


class TestTheGovernedGateRecognisesTheOwnerWhateverItsKey:
    """R12 C9 sibling 1 (first priority — an ACCESS decision): ``governed.authorize_guarded`` builds
    ``pdp.Resource.owner_principal`` / ``owner_agent`` from the row's ``record<…>`` links and compares them
    with
    the Subject's BARE ids. The round-5 reference took the bare id by splitting ``str(RecordID)`` — under SDK
    3.0
    a digit-led key is bracketed (``⟨9c9…⟩``), so the row's own owner is DENIED its own row (and under SDK 2.0
    a
    non-word key already was). The owner must be recognised whatever the key shape and the SDK's rendering; a
    foreign principal must still be denied (the control: the gate is live, not waving everything through)."""

    @pytest.mark.parametrize("rendering", sorted(_RENDERINGS))
    @pytest.mark.parametrize("key_shape", sorted(_C9_SIBLING_KEYS))
    async def test_the_rows_owner_may_delete_it_and_a_stranger_may_not(
        self,
        governed_row_world: tuple[Any, Any],
        monkeypatch: pytest.MonkeyPatch,
        key_shape: str,
        rendering: str,
    ) -> None:
        from _governed_contract import member  # noqa: PLC0415

        from loremaster import governed  # noqa: PLC0415
        from lorerunes import pdp  # noqa: PLC0415

        admin, handle = governed_row_world
        principal_key, agent_key = _C9_SIBLING_KEYS[key_shape]
        await run(
            admin,
            "CREATE c9gov:r1 SET owner_principal = $p, owner_agent = $a",
            {"p": RecordID("principal", principal_key), "a": RecordID("agent", agent_key)},
        )
        with _rendered(monkeypatch, rendering):
            try:
                await governed.authorize_guarded(
                    member(principal_key, agent_key), pdp.Action.DELETE,
                    table="c9gov", row_id="r1", audit=None, store=handle,
                )
            except governed.GovernedDenied as denied:
                pytest.fail(
                    f"[{key_shape} keys {principal_key!r}/{agent_key!r}, rendering {rendering}] the row's "
                    f"OWN owner "
                    f"was denied: {denied} — the gate compared two text forms of the owner record (C9 class)"
                )
            with pytest.raises(governed.GovernedDenied):
                await governed.authorize_guarded(
                    member("c9stranger", agent_key), pdp.Action.DELETE,
                    table="c9gov", row_id="r1", audit=None, store=handle,
                )


class TestTheDanglingSenderRefusalServesTheEnginesText:
    """R12 C9 sibling 2: the migrate refusal for legacy messages with a dangling sender names each message
    id and
    sender. Message ids are ULIDs (always digit-led), so ``str(RecordID)`` under SDK 3.0 serves
    ``message:⟨01…⟩`` —
    text that names no record when an agent pastes it back. The served ids must be the ENGINE's text (R7 (d) /
    F15), read here from the engine itself (``<string> id`` / ``<string> sender``)."""

    @pytest.mark.parametrize("rendering", sorted(_RENDERINGS))
    async def test_each_dangling_message_and_sender_is_named_by_its_engine_text(
        self, monkeypatch: pytest.MonkeyPatch, rendering: str
    ) -> None:
        import test_fixwave_a19_63c_i_a as a19  # noqa: PLC0415
        from _governed_contract import seed_message_legacy  # noqa: PLC0415
        from loremaster.store.surreal_schema import MESSAGE_TABLE  # noqa: PLC0415

        async with a19._governed_world() as world:
            for seq, (message_key, sender_key) in enumerate(
                (
                    ("01JC9R5B7XK0000000000000AA", "7c9ghost000a"),
                    ("01JC9R5B7XK0000000000000BB", "8c9ghost000b"),
                ),
                start=1,
            ):
                await seed_message_legacy(
                    world.connection, sender_id=sender_key, session="c9d", seq=seq, row_id=message_key
                )
            engine_ids = await run(world.connection, f"SELECT VALUE <string> id FROM {MESSAGE_TABLE}")
            engine_senders = await run(world.connection, f"SELECT VALUE <string> sender FROM {MESSAGE_TABLE}")
            with _rendered(monkeypatch, rendering):
                result = await world.migrate(MESSAGE_TABLE)
        reason = str(result.reason or "")
        assert result.refused is True and "dangling" in reason.lower(), (
            f"premise: the dangling refusal ({reason!r})"
        )
        missing = [text for text in (*engine_ids, *engine_senders) if text not in reason]
        assert not missing, (
            f"[rendering {rendering}] the refusal does not name {missing} as the engine writes them; it "
            f"serves "
            f"{reason!r} (C9 class: str(RecordID) served instead of the engine's text)"
        )
        assert "⟨" not in reason, (
            f"[rendering {rendering}] an SDK-only bracket rendering was served: {reason!r}"
        )


class TestTheMemoryReplayClosesThePredecessorWhateverTheOwnerKey:
    """R12 C9 sibling 3: ``memory/local.py``'s replay close compares the predecessor's STORED owner pair (two
    ``record<…>`` links) with the record's stamped BARE pair. It guards with ``getattr(link, "record_id",
    None)``
    — measured 2026-11-07: ``RecordID`` has NO ``record_id`` attribute on SDK 2.0.0 or 3.0.0 (attributes:
    ``id``, ``table_name``, ``parse``), so the guard NEVER applies and every compare falls to
    ``str(link).split(":")[-1]``. Under SDK 3.0 a digit-led owner key is bracketed, the SAME-owner pair
    compares
    unequal, the close is skipped and the superseded predecessor is REVIVED by the boot restore (and under SDK
    2.0
    a non-word key already was). The same-owner close must apply whatever the key shape and rendering."""

    @pytest.mark.parametrize("rendering", sorted(_RENDERINGS))
    @pytest.mark.parametrize("key_shape", sorted(_C9_SIBLING_KEYS))
    async def test_a_same_owner_orphan_is_closed_by_the_restore(
        self,
        dirty_world: Any,  # noqa: F811 - the replay fixture imported above
        monkeypatch: pytest.MonkeyPatch,
        key_shape: str,
        rendering: str,
    ) -> None:
        import test_memory_replay_fidelity_63b_ib as replay  # noqa: PLC0415
        from _governed_contract import admin  # noqa: PLC0415

        backend, _ledger, connection, _env = dirty_world
        principal_key, agent_key = _C9_SIBLING_KEYS[key_shape]
        owner = admin(principal_key, agent_key)
        predecessor = await backend.remember(
            "c9 pred", kind="fact", subject=owner, scope=replay._SERVER_SCOPE
        )
        successor = await backend.remember(
            "c9 succ", kind="fact", subject=owner, scope=replay._SERVER_SCOPE, supersedes=predecessor
        )
        await replay._orphan_the_successor_in_the_store(
            connection, successor=successor, predecessor=predecessor
        )
        with _rendered(monkeypatch, rendering):
            await backend.restore_from_ledger()
        post = await replay._governed_row(connection, predecessor)
        assert post is not None and post.get("valid_until") is not None, (
            f"[{key_shape} keys {principal_key!r}/{agent_key!r}, rendering {rendering}] the restore did NOT "
            f"close a "
            f"SAME-owner predecessor (it is revived): the owner pair was compared through two text forms. "
            f"{post!r}"
        )
        assert str(post.get("superseded_by")) == successor, f"the close must point at the successor: {post!r}"


class TestTheAuditAppendServesTheEnginesText:
    """C4 (round 4 §R4.7; R7 (d) / F15): ``AuditStore.append`` returns the created row's id as a handle.
    Audit ids
    are ULIDs (digit-led), so ``str(RecordID)`` under SDK 3.0 hands back ``audit:⟨01…⟩``. The returned handle
    must
    be the engine's ``<string> id`` of the row that landed. (The pre-existing routing spy
    ``test_governed_substrate_64b.py::TestAuditAppendConsumesItsFragment`` reddens on that build only
    incidentally — its ``endswith`` trips on the trailing bracket — and lives in a dormant 64b file.)"""

    @pytest.mark.parametrize("rendering", sorted(_RENDERINGS))
    async def test_the_returned_id_is_the_engines_text(
        self, store_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch, rendering: str
    ) -> None:
        from loremaster.audit import AuditStore  # noqa: PLC0415

        audit = AuditStore(
            url=store_env.url, namespace=store_env.namespace, database=store_env.database,
            user=store_env.user, password=store_env.password,
        )
        admin = await connect_admin(store_env)
        try:
            await audit.ensure_ready()
            with _rendered(monkeypatch, rendering):
                created = await audit.append(
                    actor_principal="c4alice", actor_agent="c4agent", actor_email="c4alice@example.com",
                    actor_agent_name="c4-agent", action="WRITE",
                    target_table="finding", target_row="finding:c4",
                )
            engine_ids = await run(admin, "SELECT VALUE <string> id FROM audit")
        finally:
            await admin.close()
            await audit.close()
        assert engine_ids == [created], (
            f"[rendering {rendering}] append returned {created!r}; the engine names the row {engine_ids!r} "
            f"(C4: str(RecordID) served instead of the engine's text)"
        )
