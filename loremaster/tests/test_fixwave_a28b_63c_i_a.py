"""Contract — packet 63c wave i-a, the a28b FOLD (amendments 32 + 33). Authored by ``contract-63c-i-a-a28b``
(Opus 5.5 contract author — CONTRACT TESTS ONLY, no production code). The build under repair is the checkpoint
``169925f`` (cold audit NO-GO); the contract folded is a28 (``d334042``) as graded INSUFFICIENT by
``REPORT-adversary-63c-i-a-a28.md`` (``4441b9d``).

THE SPEC IS THE RULINGS (later wins):
* ``docs/design/2026-09-26-packet63c-amendment-32.md`` (``51fd508``) §W — §1 FK-ADV-1 Reading B: the ONE
  driver (``loremaster.store._txn``) types an identity-taken engine rejection at BOTH raise sites
  (``run_query``:
  typed, from the SDK's ``AlreadyExistsError.record_id``; ``execute_transaction``: live-verified markers
  inside the ONE classifier); RS-5 (``AgentRegistry.register``) and keeps' CAS
  (``KeepStore.get_or_create_keyed``)
  decide from THAT class (R-6, one predicate). §4 C1–C3: the adversary's kill probes K1–K9
  (``REPORT-adversary-63c-i-a-a28.md`` §A.2) land AST-equal where they already encode the ruling; K9 with
  ``_CONFLICT_CLASS`` = the ruled class; K3 re-keyed to the class (deviation, report §DEVIATIONS); C1's
  refusal-cause legs completeness-checked against a28's derived ``_REGISTRY_CLASSES``. §5 R-2:
  ``keeps.minted_by_this_call`` / ``_MINTED_BY_THIS_CALL`` are DELETED (a retired-name pin).
* ``docs/design/2026-09-26-packet63c-amendment-33.md`` (``f66a190``) — FK-a28b-1 Reading 1: the class covers
  BOTH identity shapes (a record-id collision AND a UNIQUE-index collision, two noun-bearing marker pairs) and
  is RENAMED ``TxnUniqueViolationError(TxnDomainRejectionError)``; pin (c) generated over shape × path; the
  U-sdk
  pin-the-miss (the SDK does not type an index collision).
* ``docs/design/2026-09-26-packet58-amendment-7.md`` (``01565f9``) — the guarded-CAS scanner (in
  ``test_retry_seam.py``): 63c lands the DOMAIN half with ONE set first.
(§2 FK-ADV-2, §3 the am-31 fold, R-1 and R-3 land in ``test_fixwave_a28_63c_i_a.py``; §1.3 (f) the scanner in
``test_retry_seam.py``.)

STORE LAW (``docs/reference/surrealdb-31-capabilities.md`` — cited, never re-transcribed): §3 (a
multi-statement ``query()`` validates statement[0] only — every setup here is one statement per call), §5 (a
concurrency pin
holds at ≥8-way and is cleared only by 20 consecutive greens). Live TEST store ``ws://127.0.0.1:18000`` (NEVER
:18500), one unique database per world, reaped. No skip marker.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
import pathlib
import re
from typing import TYPE_CHECKING, Any

import loremaster.keeps as keeps_module
import loremaster.store._txn as _txn_module
import pytest
import surrealdb.errors as sdk_errors
import test_fixwave_a28_63c_i_a as a28
from _governed_contract import credentialed_app_context
from _surreal_harness import (
    SurrealConnection,
    SurrealEnv,
    admin_db,  # noqa: F401 - re-exported pytest fixture (live per-test store)
    run,
)
from loremaster.agents import (
    AgentIdentityConflictError,
    AgentRegistryError,
    RetiredAgentError,
)
from loremaster.governed import GovernedDenied
from loremaster.keeps import KeepStoreError
from loremaster.store._txn import (
    SurrealConnectionError,
    TxnDomainRejectionError,
    execute_transaction,
    run_query,
)
from lorerunes.pdp import keep_scope
from surrealdb import RecordID
from test_fixwave_a28_63c_i_a import _spy_registry_queries

if TYPE_CHECKING:
    # The STATIC reference that owns this file's pending pins in scripts/pending_contracts.yaml (#461's
    # shape):
    # amendments 32/33's ruled, not-yet-built class. Runtime-inert; the pins read it dynamically
    # (``_CONFLICT_CLASS``).
    from loremaster.store._txn import TxnUniqueViolationError

    def _typed_unique_violation() -> object:
        return TxnUniqueViolationError


_DIM = a28._DIM


class _UnbuiltUniqueViolationError(Exception):
    """Stand-in while ``loremaster.store._txn.TxnUniqueViolationError`` is unbuilt (at ``169925f``): it is NO
    ``SurrealStoreError``, so the derived-domain non-vacuity pins red by the ruled class's NAME, and nothing
    else silently passes for it."""


#: amendment 32 §1.1 item 5: THE conflict class every CAS door decides from — read DYNAMICALLY (the static
#: reference is the ``TYPE_CHECKING`` block above).
_CONFLICT_CLASS: type[Exception] = vars(_txn_module).get(
    "TxnUniqueViolationError", _UnbuiltUniqueViolationError
)
_CONFLICT_CLASS_NAME = "TxnUniqueViolationError"


# ======================================================================================================== #
# §1.3 (a)(b)(c) — the ONE driver types an IDENTITY-TAKEN rejection as ``TxnUniqueViolationError`` at BOTH
# raise
# sites, and nothing else as it. GENERATED over live engine situations × both raise sites (a record-id
# collision and a UNIQUE-index collision ARE identity-taken — FK-a28b-1; a table-level already-exists and an
# ASSERT rejection are NOT), plus the SDK's already-exists detail kinds DERIVED from its own source (the typed
# discriminator, ``run_query`` path).
# ======================================================================================================== #

#: The live situations: (setup statements — one per call, store-ref §3; the colliding statement; identity
#: taken?). Values are the texts probed live on 3.2.4 (report §A.1, ``probe_exists_texts.py``).
_SITUATIONS: dict[str, tuple[tuple[str, ...], str, bool]] = {
    "record-id-collision": (
        ("DEFINE TABLE rx SCHEMALESS", "CREATE rx:taken CONTENT { v: 1 }"),
        "CREATE rx:taken CONTENT { v: 2 }",
        True,
    ),
    "unique-index-collision": (
        (
            "DEFINE TABLE kx SCHEMAFULL",
            "DEFINE FIELD key ON kx TYPE string",
            "DEFINE INDEX kx_key ON kx FIELDS key UNIQUE",
            "CREATE kx:one CONTENT { key: 'dup' }",
        ),
        "CREATE kx:two CONTENT { key: 'dup' }",
        True,
    ),
    "table-already-exists": (("DEFINE TABLE tx SCHEMALESS",), "DEFINE TABLE tx", False),
    "assert-violation": (
        ("DEFINE TABLE ax SCHEMAFULL", "DEFINE FIELD n ON ax TYPE int ASSERT $value > 0"),
        "CREATE ax:one CONTENT { n: -1 }",
        False,
    ),
}
#: Values the raised message must NEVER echo (ledger #31: the hygiene boundary is unchanged by the new class).
_RAW_VALUES = ("rx:taken", "'dup'", "kx:one", "-1")


def _driver_handles(connection: SurrealConnection, env: SurrealEnv) -> dict[str, Any]:
    async def acquire() -> Any:
        return connection

    async def drop(_connection: Any) -> None:
        return None

    return {"acquire": acquire, "drop": drop, "url": env.url}


async def _raise_through(
    path: str,
    statement: str,
    connection: SurrealConnection,
    env: SurrealEnv,
    params: dict[str, Any] | None = None,
) -> BaseException:
    """Run ``statement`` (with bound ``params``, default none — EXTENDED by a28c for its KB-widened class pin)
    through ONE driver raise site and return what it raised (fails if nothing did)."""
    handles = _driver_handles(connection, env)
    try:
        if path == "run_query":
            await run_query(
                **handles,
                noun="a28b probe",
                label="a28b.probe.rejected",
                statement=statement,
                params=params or {},
                logger=logging.getLogger(__name__),
            )
        else:
            await execute_transaction(f"BEGIN;\n{statement};\nCOMMIT;", params or {}, **handles)
    except BaseException as error:  # noqa: BLE001 - the pin classifies whatever the driver raised
        return error
    pytest.fail(
        f"{path}: the colliding statement {statement!r} raised NOTHING — the situation is not constructed"
    )


class TestTheDriverTypesAnIdentityTakenRejection63cIAa28b:
    @pytest.mark.parametrize("path", ["run_query", "execute_transaction"])
    @pytest.mark.parametrize("situation", sorted(_SITUATIONS))
    async def test_am32_1_3_ab_every_raise_site_types_exactly_the_identity_taken_rejection(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
        situation: str,
        path: str,
    ) -> None:
        """⚠ RED at ``169925f`` for the two identity-taken situations (the class does not exist; both raise
        the base ``TxnDomainRejectionError`` as ``unspecified rejection``). amendment 32 §1.3 (a)/(b) + (c)'s
        live leg, GENERATED: ∀ live situation × ∀ raise site, the driver raises ``TxnUniqueViolationError``
        IFF
        the
        write's identity is taken (a record-id collision, a UNIQUE-index collision — FK-a28b-1), and otherwise
        EXACTLY the base ``TxnDomainRejectionError`` (never the subclass — a table-level already-exists is not
        a
        taken row id; the probe shows its text differs, so am-32 §1.1 item 3's bound need not be carried). The
        message never echoes the raw value (ledger #31). Mutation (the report): reword the transactional
        marker
        → the ``execute_transaction`` legs red and the ``run_query`` legs stay green (the paths are
        independent)."""
        connection, env = admin_db
        setup, statement, identity_taken = _SITUATIONS[situation]
        for setup_statement in setup:
            await run(connection, setup_statement)
        raised = await _raise_through(path, statement, connection, env)
        if identity_taken:
            assert type(raised).__name__ == _CONFLICT_CLASS_NAME and isinstance(
                raised, TxnDomainRejectionError
            ), (
                f"{situation} via {path}: amendment 32 §1 — an identity-taken rejection must raise "
                f"{_CONFLICT_CLASS_NAME} (a TxnDomainRejectionError subclass); got {type(raised).__name__}: "
                f"{raised}"
            )
        else:
            assert type(raised) is TxnDomainRejectionError, (
                f"{situation} via {path}: NOT identity-taken — must raise exactly the base "
                f"TxnDomainRejectionError, never the unique-violation class; got {type(raised).__name__}: "
                f"{raised}"
            )
        leaked = [value for value in _RAW_VALUES if value in str(raised)]
        assert not leaked, (
            f"{situation} via {path}: the raised message echoes raw engine values {leaked}: {raised}"
        )


def _sdk_already_exists_kinds() -> dict[str, str]:
    """``{detail kind: the AlreadyExistsError property that reads it}`` — DERIVED from the SDK's OWN source:
    every ``AlreadyExistsError`` property is ``_detail_field(self.details, "<Kind>", "<field>")``."""
    kinds: dict[str, str] = {}
    for name, member in inspect.getmembers(sdk_errors.AlreadyExistsError):
        if isinstance(member, property) and member.fget is not None:
            match = re.search(
                r'_detail_field\(\s*self\.details\s*,\s*"(\w+)"', inspect.getsource(member.fget)
            )
            if match:
                kinds[match.group(1)] = name
    return kinds


class _RaisingConnection:
    """A connection whose single-statement ``query`` raises ``error`` — the SDK exception in hand."""

    def __init__(self, error: BaseException) -> None:
        self.error = error

    async def query(self, _statement: str, _params: Any = None) -> Any:
        raise self.error


def _already_exists(kind: str, message: str) -> sdk_errors.AlreadyExistsError:
    inner = {"id": "rx:taken"} if kind == "Record" else {"id": "x", "name": "x"}
    return sdk_errors.AlreadyExistsError(
        kind="AlreadyExists", message=message, details={"kind": kind, "details": inner}
    )


async def _run_query_raises(error: BaseException) -> BaseException:
    connection = _RaisingConnection(error)

    async def acquire() -> Any:
        return connection

    async def drop(_connection: Any) -> None:
        return None

    try:
        await run_query(
            acquire=acquire,
            drop=drop,
            url="ws://unit",
            noun="a28b unit",
            label="a28b.unit.rejected",
            statement="CREATE rx:taken",
            params={},
            logger=logging.getLogger(__name__),
        )
    except BaseException as raised:  # noqa: BLE001 - classified below
        return raised
    pytest.fail("run_query raised nothing for a raising connection")


class TestTheTypedDiscriminatorDecidesOnTheRunQueryPath63cIAa28b:
    def test_am32_1_3_c_the_sdk_kind_domain_is_derived_and_non_vacuous(self) -> None:
        """GREEN at ``169925f`` (a property of the installed SDK) — the generated sweep below is non-vacuous:
        the derived kinds include ``Record`` (the class) and ≥1 other kind (the discriminator's controls). A
        new SDK kind joins the sweep unedited."""
        kinds = _sdk_already_exists_kinds()
        assert "Record" in kinds and len(kinds) >= 2 and kinds["Record"] == "record_id", kinds

    @pytest.mark.parametrize("wording", ["engine-wording", "reworded"])
    @pytest.mark.parametrize("kind", sorted(_sdk_already_exists_kinds()))
    async def test_am32_1_3_c_the_unique_violation_class_iff_the_sdk_says_the_record_id_is_taken(
        self, kind: str, wording: str
    ) -> None:
        """⚠ RED at ``169925f`` for ``Record`` (no class). amendment 32 §1.1 item 3 / §1.3 (c), GENERATED over
        the SDK's already-exists detail kinds (derived): on the ``run_query`` path the SDK exception in hand
        is
        classified BY TYPE — ``AlreadyExistsError`` with a record id (kind ``Record``) →
        ``TxnUniqueViolationError``;
        any other kind (Table / Namespace / Database / Session — a DDL door) → exactly the base
        ``TxnDomainRejectionError``. Both wordings: the engine's own shape of text for the kind, and a
        REWORDED
        text carrying the OTHER kind's words (a ``Record`` error worded like a table, a table worded like a
        record) — so "typed beats text" is load-bearing: a text-keyed build reds one wording or the other."""
        record_text, other_text = (
            "Database record `rx:taken` already exists",
            f"The {kind.lower()} 'x' already exists",
        )
        if kind == "Record":
            message = record_text if wording == "engine-wording" else "The table 'x' already exists"
        else:
            message = (
                other_text if wording == "engine-wording" else "Database record `rx:taken` already exists"
            )
        raised = await _run_query_raises(_already_exists(kind, message))
        if kind == "Record":
            assert type(raised).__name__ == _CONFLICT_CLASS_NAME, (
                f"AlreadyExistsError(kind=Record, record_id set) worded {message!r} must raise "
                f"{_CONFLICT_CLASS_NAME} "
                f"— the typed discriminator decides, never the text; got {type(raised).__name__}: {raised}"
            )
        else:
            assert type(raised) is TxnDomainRejectionError, (
                f"AlreadyExistsError(kind={kind}, record_id None) worded {message!r} is NOT a taken row id — "
                f"exactly the base TxnDomainRejectionError; got {type(raised).__name__}: {raised}"
            )


class TestTheSdkDoesNotTypeAUniqueIndexCollision63cIAa28b:
    async def test_am33_KNOWN_BOUND_a_unique_index_collision_is_an_untyped_InternalError(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
    ) -> None:
        """GREEN at ``169925f`` and on a correct build — a property of the installed SDK. amendment 33 §(a)
        PIN
        THE MISS: on the ``run_query`` path the engine's UNIQUE-index collision reaches the driver as
        ``surrealdb.errors.InternalError`` with ``kind == 'Internal'`` and ``details is None`` — NOTHING typed
        to
        key on, which is why the index shape is text-classified on BOTH paths (am-33). Also: the SDK's
        already-exists detail kinds (derived, ``_sdk_already_exists_kinds``) carry no index kind.

        KNOWN BOUND (amendment 33 §(a)) — the SDK does not type a unique-index collision; the day it does
        (``KIND_TO_CLASS`` gains an index kind, or ``InternalError`` carries details), add the typed branch
        ahead
        of the marker and delete this pin."""
        connection, env = admin_db
        setup, statement, _identity_taken = _SITUATIONS["unique-index-collision"]
        for setup_statement in setup:
            await run(connection, setup_statement)
        raised = await _raise_through("run_query", statement, connection, env)
        cause = raised.__cause__
        bound = (
            "KNOWN BOUND (amendment 33 §(a)) — the SDK does not type a unique-index collision; the day it "
            "does "
            "(KIND_TO_CLASS gains an index kind, or InternalError carries details), add the typed branch "
            "ahead "
            "of the marker and delete this pin"
        )
        assert type(cause) is sdk_errors.InternalError, (
            f"{bound}: the cause is {type(cause).__name__}: {cause!r}"
        )
        assert cause.kind == "Internal" and cause.details is None, (
            f"{bound}: {cause.kind!r} {cause.details!r}"
        )
        assert not any("index" in kind.lower() for kind in _sdk_already_exists_kinds()), (
            f"{bound}: {_sdk_already_exists_kinds()}"
        )


# ======================================================================================================== #
# §1.1 item 4 / §4 C3 — RS-5 decides from THE class. K9 GENERATED over the derived store-error domain (the one
# declared deviation: ``_CONFLICT_CLASS`` = ``TxnUniqueViolationError``), K7 AST-equal, K2 / K4 AST-equal, K3
# re-keyed to the class (report §DEVIATIONS).
# ======================================================================================================== #


class TestK2AGenuineCreateRejectionIsRaisedOnce:
    async def test_K2_a_non_conflict_CREATE_rejection_is_re_raised_after_one_attempt(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            registry = ctx.agent_registry
            real = registry._query
            creates = {"n": 0}

            async def forging(statement: str, params: Any = None) -> Any:
                if statement.startswith("CREATE"):
                    creates["n"] += 1
                    if creates["n"] > 3:  # stop a recursing build quickly; the count is the verdict
                        raise RuntimeError(
                            "K2: CREATE re-attempted >3x — the registry re-entered on a genuine rejection"
                        )
                    raise TxnDomainRejectionError(
                        "K2 forged: a genuine NON-conflict domain rejection of the CREATE"
                    )
                return await real(statement, params)

            monkeypatch.setattr(registry, "_query", forging)
            with pytest.raises(Exception) as caught:
                await registry.register("k2agent", session="s-k2", role="builder")
            assert type(caught.value) is TxnDomainRejectionError and creates["n"] == 1, (
                f"a genuine CREATE rejection must surface as the store's typed rejection after ONE attempt: "
                f"{type(caught.value).__name__}: {caught.value} (CREATE attempts: {creates['n']})"
            )
            assert await run(admin_conn, "SELECT VALUE name FROM agent WHERE session = 's-k2'") == []
            # CONTROL: unforged, the same register succeeds.
            monkeypatch.setattr(registry, "_query", real)
            result = await registry.register("k2agent", session="s-k2", role="builder")
            assert result.re_registered is False


class TestK3TheConflictIsClassifiedByClassNotText:
    async def test_K3_a_reworded_conflict_still_takes_the_re_register_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """DEVIATION from §A.2 (report §DEVIATIONS, K3): under amendment 32 Reading B the conflict IS the
        class,
        so the forged conflict is ``_CONFLICT_CLASS`` (was the base ``TxnDomainRejectionError``) — with a
        REWORDED message and a non-SDK cause, so a build keyed on the engine's text still reds."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            ctx = world["ctx"]
            registry = ctx.agent_registry
            real = registry._query
            fired = {"n": 0}

            async def winner_then_reworded_conflict(statement: str, params: Any = None) -> Any:
                if statement.startswith("CREATE") and fired["n"] == 0:
                    fired["n"] += 1
                    await real(statement, params)  # an IDENTICAL concurrent winner's CREATE lands first
                    try:
                        raise RuntimeError("K3: the engine reworded its unique-id conflict")
                    except RuntimeError as cause:
                        raise _CONFLICT_CLASS("SurrealDB agent query rejected (reworded)") from cause
                return await real(statement, params)

            monkeypatch.setattr(registry, "_query", winner_then_reworded_conflict)
            result = await registry.register("k3agent", session="s-k3", role="builder")
            assert fired["n"] == 1 and result.re_registered is True, (fired, result)


class TestK4ATransportFailureIsNeverAReRegister:
    async def test_K4_a_connection_error_on_CREATE_propagates(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            ctx = world["ctx"]
            registry = ctx.agent_registry
            real = registry._query
            fired = {"n": 0}

            async def commit_then_lose_the_response(statement: str, params: Any = None) -> Any:
                if statement.startswith("CREATE") and fired["n"] == 0:
                    fired["n"] += 1
                    await real(statement, params)  # the CREATE LANDED; the response is lost
                    raise SurrealConnectionError("K4 forged: socket dropped after the CREATE committed")
                return await real(statement, params)

            monkeypatch.setattr(registry, "_query", commit_then_lose_the_response)
            with pytest.raises(Exception) as caught:
                outcome = await registry.register("k4agent", session="s-k4", role="builder")
                pytest.fail(
                    f"a transport failure was swallowed into {outcome!r} (capability={outcome.capability!r})"
                )
            assert type(caught.value) is SurrealConnectionError, repr(caught.value)


# --------------------------------------------------------------------------------------------------------
# K7 — the LIFTED RS-5 property: the loser of a concurrent identical first register is served EXACTLY what the
# SEQUENTIAL second call is served (amendment 29) — including its own mutable-on-provided writes (model,
# task_id,
# cadence). A deterministic race: the winner's complete register runs inside the loser's CREATE seam, then the
# loser's CREATE meets the REAL engine conflict. Control: the sequential second call, same arguments.
# --------------------------------------------------------------------------------------------------------
class TestK7TheRaceLoserIsServedTheSequentialSecondCall:
    async def test_K7_the_loser_writes_its_own_mutable_fields(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            registry = ctx.agent_registry
            real_query = registry._query
            fired = {"n": 0}
            loser_args = dict(role="builder", model="m-loser", task_id="t-loser", cadence="≤5m")

            async def winner_first(statement: str, params: Any = None) -> Any:
                if statement.startswith("CREATE") and fired["n"] == 0:
                    fired["n"] += 1
                    await registry.register(
                        "k7agent",
                        session="s-k7",
                        role="builder",
                        model="m-winner",
                        task_id="t-winner",
                        cadence="≤1m",
                    )
                return await real_query(statement, params)

            monkeypatch.setattr(registry, "_query", winner_first)
            raced = await registry.register("k7agent", session="s-k7", **loser_args)
            row = await run(
                admin_conn, "SELECT model, task_id, declared_cadence FROM agent WHERE session = 's-k7'"
            )
            assert fired["n"] == 1 and raced.re_registered is True, (fired, raced)
            assert (raced.agent.model, raced.agent.task_id, raced.agent.declared_cadence) == (
                "m-loser",
                "t-loser",
                "≤5m",
            ), raced.agent
            assert row == [{"model": "m-loser", "task_id": "t-loser", "declared_cadence": "≤5m"}], row
            # CONTROL: the sequential second call with the same arguments serves the same thing.
            monkeypatch.setattr(registry, "_query", real_query)
            await registry.register(
                "k7seq", session="s-k7s", role="builder", model="m-winner", task_id="t-winner", cadence="≤1m"
            )
            sequential = await registry.register("k7seq", session="s-k7s", **loser_args)
            assert (
                sequential.re_registered,
                sequential.agent.model,
                sequential.agent.task_id,
                sequential.agent.declared_cadence,
            ) == (True, "m-loser", "t-loser", "≤5m"), sequential


# --------------------------------------------------------------------------------------------------------
# K9 — the LIFTED RS-5 pin, GENERATED over its domain: ∀ store-error class the agent CREATE can raise
# (DERIVED:
# every ``SurrealStoreError`` subclass in ``loremaster.store._txn``) × {the row LANDED before the raise, it
# did
# not}: the registry serves the re-register outcome (with THIS call's own writes) iff the error is the
# unique-id
# CONFLICT class AND the row exists; otherwise the SAME error class propagates unchanged after exactly ONE
# CREATE
# attempt. ``_CONFLICT_CLASS`` is the fold's choice (FK-ADV-1): Reading B = ``TxnUniqueViolationError``
# (amendment
# 32 §1.1 item 5 — the one declared deviation from §A.2, bound above). Completeness: a NEW store-error class
# joins
# the sweep without editing this pin (the derivation), and the non-vacuity leg asserts the derived set
# contains
# the conflict class AND a non-conflict ``TxnDomainRejectionError`` sibling.
# --------------------------------------------------------------------------------------------------------
_STORE_ERROR_CLASSES = sorted(
    (
        member
        for member in vars(_txn_module).values()
        if inspect.isclass(member) and issubclass(member, _txn_module.SurrealStoreError)
    ),
    key=lambda member: member.__name__,
)


def _forge(error_class: type[Exception]) -> Exception:
    if error_class is _txn_module.TxnContentionExhaustedError:
        return error_class("K9 forged", attempts=1, elapsed_seconds=0.0)
    return error_class("K9 forged")


def test_K9_the_derived_error_domain_is_non_vacuous() -> None:
    """⚠ RED at ``169925f`` (the conflict class is not in the domain). amendment 32 §1.1 item 5: the derived
    set
    contains ``TxnUniqueViolationError`` AND ≥1 non-conflict ``TxnDomainRejectionError`` sibling
    (``TxnGovernedConflictError`` — which lands in the "propagates unchanged" half), plus the transport
    class."""
    names = {member.__name__ for member in _STORE_ERROR_CLASSES}
    assert _CONFLICT_CLASS in _STORE_ERROR_CLASSES and _CONFLICT_CLASS.__name__ == _CONFLICT_CLASS_NAME, (
        f"amendment 32 §1: {_CONFLICT_CLASS_NAME} must be a SurrealStoreError subclass in "
        f"loremaster.store._txn: "
        f"{sorted(names)}"
    )
    siblings = [
        member
        for member in _STORE_ERROR_CLASSES
        if issubclass(member, TxnDomainRejectionError) and not issubclass(member, _CONFLICT_CLASS)
    ]
    assert "TxnGovernedConflictError" in {member.__name__ for member in siblings}, siblings
    assert "SurrealConnectionError" in names and len(names) >= 5, names


class TestK9EveryCreateOutcomeIsServedAsTheSequentialCallWould:
    @pytest.mark.parametrize("landed", [True, False], ids=["row-landed", "no-row"])
    @pytest.mark.parametrize("error_class", _STORE_ERROR_CLASSES, ids=lambda member: member.__name__)
    async def test_K9_create_outcome(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any, error_class: type[Exception], landed: bool
    ) -> None:
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            registry = world["ctx"].agent_registry
            real_query = registry._query
            creates = {"n": 0}

            async def forging(statement: str, params: Any = None) -> Any:
                if statement.startswith("CREATE"):
                    creates["n"] += 1
                    if creates["n"] > 2:
                        raise RuntimeError(
                            "K9: CREATE re-attempted — the registry re-entered on a forged error"
                        )
                    if creates["n"] == 1:
                        if (
                            landed
                        ):  # an identical winner's row lands first (a DIFFERENT model, so the write shows)
                            await real_query(
                                statement,
                                {
                                    **(params or {}),
                                    "content": {**(params or {})["content"], "model": "m-winner"},
                                },
                            )
                        raise _forge(error_class)
                return await real_query(statement, params)

            monkeypatch.setattr(registry, "_query", forging)
            outcome: Any
            try:
                outcome = await registry.register("k9agent", session="s-k9", role="builder", model="m-self")
            except Exception as error:  # noqa: BLE001 - the pin classifies what is served
                outcome = error
            conflict = issubclass(error_class, _CONFLICT_CLASS) and landed
            if conflict:
                assert not isinstance(outcome, Exception) and outcome.re_registered is True, repr(outcome)
                assert outcome.agent.model == "m-self", (
                    f"the re-register must carry THIS call's writes: {outcome.agent!r}"
                )
            else:
                assert type(outcome) is error_class and creates["n"] == 1, (
                    f"{error_class.__name__} (landed={landed}) must propagate unchanged after ONE CREATE: "
                    f"{type(outcome).__name__}: {outcome!r} (CREATE attempts {creates['n']})"
                )


# ======================================================================================================== #
# §1.2 (R-6) — keeps' CAS decides from THE SAME class: ONE predicate for both CAS doors. The keeps twin of K9,
# GENERATED over the same derived domain × {a winner keyed the same landed first, none}: the call returns the
# WINNER iff the error is ``TxnUniqueViolationError`` AND the winner exists; otherwise the wrap's answer
# unchanged
# (transport / exhausted contention pass through; every other store error → ``KeepStoreError``), after exactly
# ONE create transaction. DUAL (amendment 32 §1.2): a NON-conflict rejection whose key coincidentally resolves
# used to return the winner — dropped deliberately; this pin reds a build that keeps it.
# ======================================================================================================== #

_KEEPS_PASSTHROUGH = (SurrealConnectionError, _txn_module.TxnContentionExhaustedError)


class TestKeepsCasDecidesFromTheOneClass63cIAa28b:
    @pytest.mark.parametrize("winner", [True, False], ids=["winner-landed", "no-winner"])
    @pytest.mark.parametrize("error_class", _STORE_ERROR_CLASSES, ids=lambda member: member.__name__)
    async def test_am32_1_2_keeps_returns_the_winner_iff_the_unique_violation_class_and_a_winner(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any, error_class: type[Exception], winner: bool
    ) -> None:
        """⚠ RED at ``169925f`` on every non-conflict DOMAIN class × ``winner-landed`` (keeps catches the
        broad
        ``SurrealStoreError`` and returns the coincidental winner). The same derived domain as K9 — mutation-
        provable ONE predicate: change the class keeps catches and this pin reds; change the class RS-5
        catches
        and K9 reds."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            keep_store = world["ctx"]._keep_store
            key, email = "session:s-keeps-cas", world["emails"]["alice"]
            real_execute = vars(keeps_module)["execute_transaction"]
            attempts = {"n": 0}

            async def forging(statement: str, params: dict[str, Any], **kwargs: Any) -> Any:
                attempts["n"] += 1
                if attempts["n"] > 1:
                    raise RuntimeError("keeps CAS: the create transaction was re-attempted")
                if winner:  # a concurrent mint of the SAME key lands first (its own id)
                    await real_execute(
                        statement,
                        {**params, "keep_id": "winnerkeep", "keep_edge": RecordID("keep", "winnerkeep")},
                        **kwargs,
                    )
                raise _forge(error_class)

            monkeypatch.setattr(keeps_module, "execute_transaction", forging)
            outcome: Any
            try:
                outcome = await keep_store.get_or_create_keyed(key, type="session", keeper_email=email)
            except Exception as error:  # noqa: BLE001 - the pin classifies what is served
                outcome = error
            if issubclass(error_class, _CONFLICT_CLASS) and winner:
                assert not isinstance(outcome, Exception) and str(outcome.id).endswith("winnerkeep"), (
                    f"{error_class.__name__} with a landed winner: keeps must return THE WINNER: {outcome!r}"
                )
            else:
                expected = error_class if issubclass(error_class, _KEEPS_PASSTHROUGH) else KeepStoreError
                assert type(outcome) is expected and attempts["n"] == 1, (
                    f"{error_class.__name__} (winner={winner}): keeps must serve {expected.__name__} after "
                    f"ONE "
                    f"create — never the winner for a non-conflict cause (amendment 32 §1.2 DUAL): "
                    f"{type(outcome).__name__}: {outcome!r} (attempts {attempts['n']})"
                )

    async def test_am32_1_2_the_REAL_unique_key_conflict_converges_eight_way(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        """GREEN at ``169925f`` (keeps catches broadly); RED on a build whose unique-violation class misses
        the engine's
        UNIQUE-INDEX text (FK-a28b-1: a literal am-32 marker ``already exists`` only). The REAL engine
        conflict,
        no forgery: ``a28._ROUNDS`` rounds × ``a28._CONCURRENCY`` concurrent ``get_or_create_keyed`` of ONE
        fresh
        key — every call returns a keep, all the SAME id, and the key holds ONE row (store-ref §5: ≥8-way; the
        report clears it 20 consecutive)."""
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            keep_store, admin_conn = world["ctx"]._keep_store, world["admin_conn"]
            email = world["emails"]["alice"]
            failures: list[str] = []
            for round_index in range(a28._ROUNDS):
                key = f"session:s-keeps-8way-{round_index}"
                outcomes = await asyncio.gather(
                    *[
                        keep_store.get_or_create_keyed(key, type="session", keeper_email=email)
                        for _ in range(a28._CONCURRENCY)
                    ],
                    return_exceptions=True,
                )
                raised = [
                    f"{type(outcome).__name__}: {outcome}"
                    for outcome in outcomes
                    if isinstance(outcome, BaseException)
                ]
                ids = {str(outcome.id) for outcome in outcomes if not isinstance(outcome, BaseException)}
                rows = await run(admin_conn, f"SELECT VALUE id FROM keep WHERE key = '{key}'")
                if raised or len(ids) != 1 or len(rows) != 1:
                    failures.append(
                        f"round {round_index}: raised={raised[:2]!r} ids={sorted(ids)} rows={rows!r}"
                    )
            assert not failures, (
                "amendment 32 §1.2: keeps' CAS must converge on the REAL unique-key conflict (the winner is "
                "returned to every loser, one row):\n" + "\n".join(failures)
            )


# ======================================================================================================== #
# §4 C2 — a foreign principal's register issues ZERO agent-registry queries and is served ONE denial, ∀ probe
# kinds × ∀ foreign shapes. K1 and K8 AST-equal (the seam spy replaces RS-3's 3-method hand-list — a28 DUAL);
# the foreign shapes as parametrisation, enumerated from the gate's inputs (the principal's relation to THIS
# keep).
# ======================================================================================================== #


class TestK1TheGateReadsNoRegistryRowThroughANYDoor:
    async def test_K1_foreign_probes_issue_zero_registry_queries(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        async with credentialed_app_context(
            monkeypatch,
            tmp_path,
            principals={"alice": "member", "carol": "member", "bob": "member"},
            dim=_DIM,
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            session = "s-alice"
            await a28._alice_keeps_a_session(ctx, world, session)
            keep_bare = a28._bare((await a28._session_keep_ids(admin_conn, session))[0])
            await ctx._keep_store.add_household_member(keep_id=keep_bare, member_email=world["emails"]["bob"])
            seen = _spy_registry_queries(monkeypatch, ctx.agent_registry)
            world["holder"]["email"] = world["emails"]["carol"]
            for probe in a28._FOREIGN_PROBES.values():
                with pytest.raises(GovernedDenied):
                    await ctx.comms(action="register", session=session, **probe)
            assert seen == [], f"a foreign register read the registry before the gate denied it: {seen!r}"
            # POSITIVE CONTROL: the spy SEES registry reads on a householded register.
            world["holder"]["email"] = world["emails"]["bob"]
            await ctx.comms(action="register", agent="bobagent", session=session, role="builder")
            assert seen, "CONTROL: the _query spy saw nothing on a householded register — the probe is blind"


# --------------------------------------------------------------------------------------------------------
# K8 — P2 perturbation of RS-3's fixture: the foreign principal KEEPS ANOTHER SESSION of her own (so her
# visible
# keep set is NON-EMPTY). The four probes must still be the same GovernedDenied with zero registry queries.
# --------------------------------------------------------------------------------------------------------
class TestK8AForeignPrincipalWithHerOwnKeepIsStillDenied:
    async def test_K8_foreign_probes_by_a_principal_who_keeps_another_session(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member", "carol": "member"}, dim=_DIM
        ) as world:
            ctx = world["ctx"]
            await a28._alice_keeps_a_session(ctx, world, "s-alice")
            world["holder"]["email"] = world["emails"]["carol"]
            await ctx.comms(
                action="register", agent="carols", session="s-carol", role="builder"
            )  # carol keeps s-carol
            seen = _spy_registry_queries(monkeypatch, ctx.agent_registry)
            served = {
                label: await a28._outcome(ctx.comms(action="register", session="s-alice", **probe))
                for label, probe in a28._FOREIGN_PROBES.items()
            }
            assert {kind for kind, _t in served.values()} == {GovernedDenied.__name__}, served
            assert len({text for _k, text in served.values()}) == 1, served
            assert seen == [], seen


#: The principal's relation to THIS session's keep (amendment 32 §4 C2 — the gate's inputs), each shape →
#: whether it is FOREIGN to alice's keep. ``householded-in-this-keep`` is the NOT-foreign control.
_C2_SHAPES: dict[str, bool] = {
    "holds-no-keep": True,
    "keeper-of-another-keep": True,
    "householded-in-another-keep": True,
    "householded-in-this-keep": False,
}


async def _shape_carol(ctx: Any, world: dict[str, Any], shape: str) -> None:
    """Give carol ``shape``'s relation to alice's ``s-alice`` keep (dan keeps ``s-dan`` for the householded-
    elsewhere shape). Leaves the holder as carol."""
    admin_conn = world["admin_conn"]
    if shape == "keeper-of-another-keep":
        world["holder"]["email"] = world["emails"]["carol"]
        await ctx.comms(action="register", agent="carols", session="s-carol", role="builder")
    elif shape == "householded-in-another-keep":
        world["holder"]["email"] = world["emails"]["dan"]
        await ctx.comms(action="register", agent="dans", session="s-dan", role="builder")
        dan_keep = a28._bare((await a28._session_keep_ids(admin_conn, "s-dan"))[0])
        await ctx._keep_store.add_household_member(keep_id=dan_keep, member_email=world["emails"]["carol"])
    elif shape == "householded-in-this-keep":
        alice_keep = a28._bare((await a28._session_keep_ids(admin_conn, "s-alice"))[0])
        await ctx._keep_store.add_household_member(keep_id=alice_keep, member_email=world["emails"]["carol"])
    world["holder"]["email"] = world["emails"]["carol"]


class TestC2EveryForeignShapeIsDeniedWithZeroRegistryQueries63cIAa28b:
    @pytest.mark.parametrize("shape", sorted(_C2_SHAPES))
    async def test_am32_C2_foreign_shapes_x_probe_kinds(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any, shape: str
    ) -> None:
        """⚠ RED at ``169925f`` on every FOREIGN shape (preflight reads the registry before the gate, and
        serves
        alice's agent facts). amendment 32 §4 C2, ∀ foreign shapes × ∀ probe kinds (``a28._FOREIGN_PROBES``):
        ONE
        byte-identical ``GovernedDenied``, ZERO queries through the registry's ONE seam
        (``AgentRegistry._query``
        — K1's spy; bound: a read on another connection is outside it). CONTROL
        (``householded-in-this-keep``):
        the same probes PROCEED past the gate — the spy SEES registry queries and no probe is
        ``GovernedDenied``
        (the role/retired probes meet the registry's own teaching; the absent name registers)."""
        async with credentialed_app_context(
            monkeypatch,
            tmp_path,
            principals={"alice": "member", "carol": "member", "dan": "member"},
            dim=_DIM,
        ) as world:
            ctx = world["ctx"]
            await a28._alice_keeps_a_session(ctx, world, "s-alice")
            await _shape_carol(ctx, world, shape)
            seen = _spy_registry_queries(monkeypatch, ctx.agent_registry)
            served = {
                label: await a28._outcome(ctx.comms(action="register", session="s-alice", **probe))
                for label, probe in a28._FOREIGN_PROBES.items()
            }
            if _C2_SHAPES[shape]:
                assert {kind for kind, _text in served.values()} == {GovernedDenied.__name__}, (shape, served)
                assert len({text for _kind, text in served.values()}) == 1, (shape, served)
                assert seen == [], (
                    f"{shape}: a foreign register queried the registry before the gate: {seen!r}"
                )
            else:
                assert GovernedDenied.__name__ not in {kind for kind, _text in served.values()}, (
                    shape,
                    served,
                )
                assert seen, f"CONTROL {shape}: the seam spy saw no registry query — the probe is blind"


# ======================================================================================================== #
# §4 C1 — ∀ register calls (success, ∀ refusal classes, ∀ denial): the keep store's ONLY write is the
# session-keep mint; no pre-existing keep / member_of row changes. K6 is the class pin; K5 folded as its
# per-cause legs (both AST-equal); the refusal-cause completeness is DERIVED from a28's ``_REGISTRY_CLASSES``.
# ======================================================================================================== #


class TestK5NoRefusalClassCompensates:
    @pytest.mark.parametrize("refusal", ["role", "spawned_by", "retired"])
    async def test_K5_every_post_mint_refusal_class_leaves_the_keep(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any, refusal: str
    ) -> None:
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            world["holder"]["email"] = world["emails"]["alice"]
            session = f"s-k5-{refusal}"
            keep_store = ctx._keep_store
            real_mint = keep_store.get_or_create_keyed
            calls = {"mint": 0}
            x_role, x_spawned = "builder", "leadx"
            winner_kwargs = {
                "role": dict(role="auditor", spawned_by=x_spawned),
                "spawned_by": dict(role=x_role, spawned_by="leadother"),
                "retired": dict(role=x_role, spawned_by=x_spawned),
            }[refusal]

            async def racing_mint(*args: Any, **kwargs: Any) -> Any:
                calls["mint"] += 1
                keep = await real_mint(*args, **kwargs)
                if calls["mint"] == 1:
                    await ctx.comms(action="register", agent="a", session=session, **winner_kwargs)
                    if refusal == "retired":
                        await ctx.agent_registry.touch("a", session=session, status="retired")
                return keep

            monkeypatch.setattr(keep_store, "get_or_create_keyed", racing_mint)
            deletes = a28._spy_delete_keep(monkeypatch, ctx)
            with pytest.raises(AgentRegistryError) as caught:
                await ctx.comms(
                    action="register", agent="a", session=session, role=x_role, spawned_by=x_spawned
                )
            expected = RetiredAgentError if refusal == "retired" else AgentIdentityConflictError
            assert type(caught.value) is expected, repr(caught.value)
            keeps = await a28._session_keep_ids(admin_conn, session)
            scopes = await run(
                admin_conn, f"SELECT VALUE scope FROM agent WHERE session = '{session}' AND name = 'a'"
            )
            assert len(keeps) == 1 and scopes == [keep_scope(a28._bare(keeps[0]))], (keeps, scopes)
            assert deletes["count"] == 0, deletes


# --------------------------------------------------------------------------------------------------------
# K6 — the LIFTED property for (a)+(b): during ANY register call — foreign denial or post-mint race refusal, ∀
# refusal classes — the keep store performs NO write but the session-keep mint, and no keep / member_of row
# that
# existed before the call is absent or changed after it. Domain: KeepStore's public async verbs, DERIVED by
# inspection; the SAFE set is allowlisted (reads + the mint); ``_query`` is watched for any non-SELECT
# statement.
# --------------------------------------------------------------------------------------------------------
_KEEP_SAFE_VERBS = frozenset(
    {
        "get_by_key",
        "get_keep",
        "list_keeps_for_member",
        "list_household",
        "list_keeps_for_keeper",
        "get_or_create_keyed",
    }
)


def _arm_keep_write_spy(monkeypatch: pytest.MonkeyPatch, keep_store: Any) -> list[str]:
    seen: list[str] = []
    verbs = [
        name
        for name, member in inspect.getmembers(type(keep_store), inspect.iscoroutinefunction)
        if not name.startswith("_")
    ]
    assert "delete_keep" in verbs and "get_by_key" in verbs, f"derivation broken: {verbs}"
    for name in verbs:
        real = getattr(keep_store, name)

        async def wrapped(*args: Any, __name: str = name, __real: Any = real, **kwargs: Any) -> Any:
            seen.append(__name)
            return await __real(*args, **kwargs)

        monkeypatch.setattr(keep_store, name, wrapped)
    real_query = keep_store._query

    async def watched(statement: str, params: Any = None) -> Any:
        if not statement.lstrip().upper().startswith("SELECT"):
            seen.append(f"_query:{statement.split()[0]}")  # noqa: PLC0207 - K6 lands AST-equal (§A.2)
        return await real_query(statement, params)

    monkeypatch.setattr(keep_store, "_query", watched)
    return seen


async def _keep_rows(admin_conn: Any) -> list[Any]:
    return [
        await run(admin_conn, "SELECT * FROM keep ORDER BY id"),
        await run(admin_conn, "SELECT * FROM member_of ORDER BY id"),
    ]


class TestK6NoRegisterPathRemovesOrWritesKeepState:
    async def test_K6_foreign_denials_write_nothing_to_the_keep_store(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any
    ) -> None:
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member", "carol": "member"}, dim=_DIM
        ) as world:
            ctx = world["ctx"]
            await a28._alice_keeps_a_session(ctx, world, "s-alice")
            seen = _arm_keep_write_spy(monkeypatch, ctx._keep_store)
            world["holder"]["email"] = world["emails"]["carol"]
            for probe in a28._FOREIGN_PROBES.values():
                with pytest.raises(GovernedDenied):
                    await ctx.comms(action="register", session="s-alice", **probe)
            unsafe = [name for name in seen if name not in _KEEP_SAFE_VERBS or name == "get_or_create_keyed"]
            assert not unsafe, f"a foreign denial touched the keep store beyond reads: {unsafe}"
            # CONTROL: the spy SEES a write verb.
            world["holder"]["email"] = world["emails"]["carol"]
            await ctx.comms(action="register", agent="carols", session="s-carol", role="builder")
            assert "get_or_create_keyed" in seen, "CONTROL: the spy is blind to the mint"

    @pytest.mark.parametrize("refusal", ["role", "spawned_by", "retired"])
    async def test_K6_a_race_refusal_removes_no_keep_state(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any, refusal: str
    ) -> None:
        async with credentialed_app_context(
            monkeypatch, tmp_path, principals={"alice": "member", "bob": "member"}, dim=_DIM
        ) as world:
            ctx, admin_conn = world["ctx"], world["admin_conn"]
            world["holder"]["email"] = world["emails"]["alice"]
            session = f"s-k6-{refusal}"
            await ctx.comms(
                action="register", agent="first", session=session, role="builder"
            )  # K pre-exists (FOUND)
            keep_bare = a28._bare((await a28._session_keep_ids(admin_conn, session))[0])
            await ctx._keep_store.add_household_member(keep_id=keep_bare, member_email=world["emails"]["bob"])
            winner_kwargs = {
                "role": dict(role="auditor", spawned_by="leadx"),
                "spawned_by": dict(role="builder", spawned_by="leadother"),
                "retired": dict(role="builder", spawned_by="leadx"),
            }[refusal]
            real_mint = ctx._keep_store.get_or_create_keyed
            fired = {"n": 0}
            snapshot: dict[str, Any] = {}

            async def racing_mint(*args: Any, **kwargs: Any) -> Any:
                keep = await real_mint(*args, **kwargs)
                fired["n"] += 1
                if fired["n"] == 1:
                    await ctx.comms(action="register", agent="a", session=session, **winner_kwargs)
                    if refusal == "retired":
                        await ctx.agent_registry.touch("a", session=session, status="retired")
                    snapshot["before"] = await _keep_rows(admin_conn)
                return keep

            monkeypatch.setattr(ctx._keep_store, "get_or_create_keyed", racing_mint)
            seen = _arm_keep_write_spy(monkeypatch, ctx._keep_store)
            with pytest.raises(AgentRegistryError):
                await ctx.comms(
                    action="register", agent="a", session=session, role="builder", spawned_by="leadx"
                )
            after = await _keep_rows(admin_conn)
            assert after == snapshot["before"], "a refused register changed keep / household state"
            unsafe = [name for name in seen if name not in _KEEP_SAFE_VERBS]
            assert not unsafe, f"a refused register wrote to the keep store beyond the mint: {unsafe}"


#: C1's refusal CAUSES (the K5 / K6 per-cause legs) → the registry class each provokes post-mint.
_CAUSE_CLASS: dict[str, type[AgentRegistryError]] = {
    "role": AgentIdentityConflictError,
    "spawned_by": AgentIdentityConflictError,
    "retired": RetiredAgentError,
}
#: Every OTHER registry class, with the evidence it is not reachable POST-MINT on the register path (amendment
#: 32
#: §4 C1: "provoked post-mint by a fixture, or named in an evidence-backed exemption list"). A new
#: ``AgentRegistryError`` class in ``agents.py`` joins ``a28._REGISTRY_CLASSES`` unedited and reds the pin
#: below.
_NOT_REACHABLE_POST_MINT: dict[str, str] = {
    "AgentRegistryError": "the base: register raises it bare only for a just-CREATEd row that does not read "
    "back (a `pragma: no cover` engine-contract break), never as a refusal",
    "UnknownAgentError": "a lookup miss (get_agent / touch / _resolve_row); register CREATES on a miss",
    "AmbiguousAgentError": "a session-less name resolution; register always carries its session",
    "InvalidAgentIdentityError": "an identity check preflight runs BEFORE the mint on the same arguments "
    "(evidenced live by the pre-mint leg below)",
    "IllegalAgentStatusError": "a status-edge refusal of touch; register never edits status by an edge",
}


def test_am32_C1_every_registry_class_is_provoked_post_mint_or_exempt_with_evidence() -> None:
    """GREEN at ``169925f`` unless the class family moved. amendment 32 §4 C1 COMPLETENESS: the K5 / K6
    per-cause
    legs + the exemption list cover EXACTLY a28's derived ``_REGISTRY_CLASSES``; the legs' parametrisation IS
    ``_CAUSE_CLASS`` (read from the collected marks, a checked variable — never a second hand-list)."""
    provoked = {cls.__name__ for cls in _CAUSE_CLASS.values()}
    assert provoked.isdisjoint(_NOT_REACHABLE_POST_MINT), sorted(provoked & set(_NOT_REACHABLE_POST_MINT))
    assert provoked | set(_NOT_REACHABLE_POST_MINT) == set(a28._REGISTRY_CLASSES), (
        f"C1 completeness: registry classes {sorted(set(a28._REGISTRY_CLASSES))} vs provoked "
        f"{sorted(provoked)} + exempt {sorted(_NOT_REACHABLE_POST_MINT)} — a class is neither provoked "
        "post-mint nor exempted with evidence"
    )
    for test in (
        TestK5NoRefusalClassCompensates.test_K5_every_post_mint_refusal_class_leaves_the_keep,
        TestK6NoRegisterPathRemovesOrWritesKeepState.test_K6_a_race_refusal_removes_no_keep_state,
    ):
        causes = next(mark.args[1] for mark in test.pytestmark if mark.name == "parametrize")
        assert list(causes) == list(_CAUSE_CLASS), (
            f"{test.__qualname__} legs {causes} != causes {list(_CAUSE_CLASS)}"
        )


async def test_am32_C1_evidence_an_invalid_identity_is_refused_before_any_mint(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Any
) -> None:
    """GREEN at ``169925f`` (the #485 order). The executable evidence behind the ``InvalidAgentIdentityError``
    exemption: an invalid identity is refused with ZERO keep mints — it can never be a POST-mint refusal."""
    async with credentialed_app_context(
        monkeypatch, tmp_path, principals={"alice": "member"}, dim=_DIM
    ) as world:
        ctx = world["ctx"]
        world["holder"]["email"] = world["emails"]["alice"]
        mints: dict[str, int] = {}
        a28._count_calls(monkeypatch, ctx._keep_store, "get_or_create_keyed", mints)
        served = await a28._outcome(
            ctx.comms(action="register", agent="blankrole", session="s-invalid", role="   ")
        )
        assert served[0] == "InvalidAgentIdentityError" and mints == {}, (served, mints)


# ======================================================================================================== #
# §5 R-2 — ``keeps.minted_by_this_call`` / ``_MINTED_BY_THIS_CALL`` are DELETED (amendment 28 §F-1 "dead and
# go"):
# no binding and no prose mention anywhere in the production package (a BARE, anchor-free pattern — CLAUDE.md
# rename-sweep law: prose carries no structural anchor).
# ======================================================================================================== #

_RETIRED_NAME = "minted_by_this_call"
_PACKAGE_ROOT = pathlib.Path(keeps_module.__file__).resolve().parent


def test_am32_R2_the_created_only_flag_is_gone_from_the_package() -> None:
    """⚠ RED at ``169925f`` (``keeps.py`` defines ``minted_by_this_call`` + ``_MINTED_BY_THIS_CALL`` and its
    docstrings teach the retired compensation). Positive control: the scan reads a non-empty ``.py`` set that
    includes ``keeps.py`` (a scan over nothing would pass)."""
    scanned = [path for path in sorted(_PACKAGE_ROOT.rglob("*.py")) if "__pycache__" not in path.parts]
    assert any(path.name == "keeps.py" for path in scanned) and len(scanned) > 10, scanned[:5]
    hits = [
        f"{path.relative_to(_PACKAGE_ROOT)}:{number}"
        for path in scanned
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1)
        if _RETIRED_NAME in line.lower()
    ]
    assert not hits, (
        f"amendment 32 §5 R-2: the retired created-only flag `{_RETIRED_NAME}` survives at {hits} — delete "
        f"the "
        "function, its constant and every prose mention (amendment 28 §F-1: dead and go)"
    )
