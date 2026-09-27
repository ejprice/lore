"""Contract r2 — packet 64b-i: the calibration-drift SYSTEM writer (packet-64 amendment 7 ``6e42ed1`` §1,
FK-7 RULED). Authored by ``contract-64b-r2`` (Opus 5.5 — contract tests ONLY).

THE RULING (cited, never re-transcribed): a system writer is the finding-side twin of the migrate — a
governed-table write that is NOT member-reachable, evidenced by a NAMED exempt entry, writing the UNOWNED
shape (owner ``NONE/NONE``, scope = the project keep via the SAME ``get_or_create_keyed(PROJECT_KEEP_KEY,
…)``-minted keep every legacy leg uses). ``FindingLedger.report_system(title, body, *, kind, area, category,
created_by)``; ONE fragment builder (``_report_fragment`` takes the governed triple as PARAMETERS — a member
``report`` and ``report_system`` execute the SAME two statements); the write runs inside ``with
governed_exempt("calibration-drift", statement=<the COMPOSED transaction text>)`` (amendment 9 §4 — the text
``store._txn.compose`` builds, which is what ``execute_transaction`` receives) entered in ``report_system``'s
own frame;
ONE production caller (``_CalibrationFindingsAdapter.report_drift_finding``), no served verb; a missing
project keep is a LOUD, NON-FATAL boot fault (the adapter catches the ONE typed refusal, logs
``calibration.drift.unfiled`` at ERROR, the boot continues). Never a fabricated owner; never a
``None``-Subject path through ``report``.

The r1 reference (``REPORT-adversary-64b.md`` §RESIDUALS 16) used a LABEL (``finding_report_system``) and
wrote scope NONE silently when the keep was absent — both contradict the ruling; every pin below reds on it.

Live TEST store ``:18000`` (NEVER :18500); per-test databases, reaped.
"""

from __future__ import annotations

import ast
import contextlib
import inspect
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from _governed_contract import (
    ObservedEffect,
    RowDelta,
    SchemaDelta,
    _normalise_statement,
    apply_ddl,
    build_principal_and_keep_stores,
    classify_tree_observed_write,
    observe_governed_table_writes,
    patch_shared_object_everywhere,
)
from _governed_contract_64 import (
    CALIBRATION_DRIFT_EXEMPT,
    FINDING_TABLE,
    FINDING_TREE_ALLOWLIST,
    REPORT_SYSTEM_TXN_GOLDEN,
    bare,
    current_finding_ddl,
    effect_finding_report_system,
    finding_world,
)
from _surreal_harness import connect_admin, drop_database, make_env, run, unique_database
from loremaster.calibration.engine import CALIBRATION_AREA, DRIFT_CATEGORY, DRIFT_CREATED_BY, DRIFT_KIND
from loremaster.findings import FindingLedger
from loremaster.governed import PROJECT_KEEP_KEY
from lorerunes.pdp import keep_scope

from loremaster import governed, server

if TYPE_CHECKING:
    # 64b-i's RULED, not-yet-built signature (amendment 8 §5 — a TYPED CALL, so mypy's ``[call-arg]`` checks
    # the SHAPE, not just the name). A permanent signature pin: mypy checks TYPE_CHECKING bodies after the
    # build too. Until the build lands it, a mypy error OWNED by bound ``packet-64b-i-contract``.
    async def _ruled_64b_i_report_system_shape(ledger: FindingLedger) -> None:
        """FK-7: the system writer takes the title + body positionally and NO identity/scope/supersedes."""
        await ledger.report_system(
            "title", "body", kind="drift", area="a", category="c", created_by="calibration-engine"
        )


_SERVER_PY = Path(server.__file__)
_DRIFT_TITLE = "token calibration drift: probe"


@dataclass
class SystemLedgerWorld:
    """A throwaway store carrying the CURRENT finding DDL + the principal/keep stores, ONE keeper principal,
    a real ``FindingLedger`` and THE production calibration adapter wrapping it."""

    env: Any
    connection: Any
    ledger: FindingLedger
    adapter: Any
    keep_store: Any
    keeper_bare: str

    async def file_drift(self) -> Any:
        """The WRITER itself (``report_system``), with the engine's own constants."""
        return await self.ledger.report_system(
            _DRIFT_TITLE,
            "drift body",
            kind=DRIFT_KIND,
            area=CALIBRATION_AREA,
            category=DRIFT_CATEGORY,
            created_by=DRIFT_CREATED_BY,
        )

    async def file_drift_via_adapter(self) -> None:
        """The ONE production caller, exactly as the calibration engine drives it."""
        await self.adapter.report_drift_finding(
            subject=_DRIFT_TITLE,
            body="drift body",
            area=CALIBRATION_AREA,
            category=DRIFT_CATEGORY,
            kind=DRIFT_KIND,
            created_by=DRIFT_CREATED_BY,
        )

    async def project_scope(self) -> str:
        ids = await run(self.connection, "SELECT VALUE id FROM keep WHERE key = $k", {"k": PROJECT_KEEP_KEY})
        assert ids, "fixture: no project keep"
        return keep_scope(bare(ids[0]))

    async def findings(self) -> list[dict[str, Any]]:
        return list(await run(self.connection, f"SELECT * FROM {FINDING_TABLE} ORDER BY id"))


@contextlib.asynccontextmanager
async def system_ledger_world(*, provision_project_keep: bool) -> AsyncIterator[SystemLedgerWorld]:
    """Build a :class:`SystemLedgerWorld`; ``provision_project_keep`` mints THE canonical project keep
    through the production ``KeepStore.get_or_create_keyed`` (the keep every legacy leg uses). Reaped."""
    env = make_env(database=unique_database(), dim=8)
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    connection = await connect_admin(env)
    ledger = FindingLedger(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    try:
        await apply_ddl(connection, current_finding_ddl(), url=env.url)
        keeper = await principal_store.create(email="keeper@example.com", role="admin")
        if provision_project_keep:
            await keep_store.get_or_create_keyed(
                key=PROJECT_KEEP_KEY, type="project", keeper_email="keeper@example.com", name="lore"
            )
        yield SystemLedgerWorld(
            env=env,
            connection=connection,
            ledger=ledger,
            adapter=server._CalibrationFindingsAdapter(ledger),  # noqa: SLF001 - THE production adapter
            keep_store=keep_store,
            keeper_bare=bare(keeper.id),
        )
    finally:
        await ledger.close()
        await connection.close()
        await keep_store.close()
        await principal_store.close()
        await drop_database(env)


def _require_report_system() -> None:
    assert callable(getattr(FindingLedger, "report_system", None)), (
        "UNBUILT (amendment 7 §1): FindingLedger.report_system does not exist"
    )


# =========================================================================== #
# The written row — UNOWNED, in the project keep, never a fabricated owner.
# =========================================================================== #


class TestTheSystemWriterWritesTheUnownedShape:
    """amendment 7 §1 "Answer" + the F1 reasoning: owner NONE/NONE (the engine proved nothing — an owner is a
    principal who PROVED it wrote the row), scope = the project keep, ``open``, the engine's area/author;
    ``report_system`` takes NO identity, scope or supersedes parameter (no ``None``-Subject door beside the
    PDP)."""

    async def test_one_unowned_row_in_the_project_keep(self) -> None:
        """⚠ RED at HEAD (``report_system`` absent)."""
        _require_report_system()
        async with system_ledger_world(provision_project_keep=True) as world:
            await world.file_drift()
            rows = await world.findings()
            assert len(rows) == 1, rows
            row = rows[0]
            assert row.get("owner_principal") is None and row.get("owner_agent") is None, (
                f"the system writer FABRICATED an owner (amendment 7 §1 forbids it): {row!r}"
            )
            assert row.get("scope") == await world.project_scope(), row
            assert (row.get("status"), row.get("area"), row.get("created_by")) == (
                "open",
                CALIBRATION_AREA,
                DRIFT_CREATED_BY,
            ), row

    def test_the_signature_carries_no_identity_scope_or_supersedes(self) -> None:
        """⚠ RED at HEAD. ``report_system(title, body, *, kind, area, category, created_by)`` — FK-1's
        ``title`` spelling; a ``subject``/``scope``/``supersedes`` parameter would be a second door beside
        ``report``."""
        _require_report_system()
        params = inspect.signature(FindingLedger.report_system).parameters
        assert list(params)[:3] == ["self", "title", "body"], list(params)
        assert {"kind", "area", "category", "created_by"} <= set(params), list(params)
        assert not {"subject", "caller", "scope", "supersedes"} & set(params), list(params)


# =========================================================================== #
# ONE fragment builder — the golden is report's composed transaction too.
# =========================================================================== #


def _recorded_transactions(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Every transaction text ``execute_transaction`` receives (the bytes the F5 observer records too)."""
    from loremaster.store import _txn  # noqa: PLC0415

    seen: list[str] = []
    real = _txn.execute_transaction

    async def _spy(statement_text: str, *args: Any, **kwargs: Any) -> Any:
        seen.append(statement_text)
        return await real(statement_text, *args, **kwargs)

    patch_shared_object_everywhere(
        monkeypatch, "execute_transaction", real, _spy, expect_in=("loremaster.store._txn",)
    )
    return seen


class TestTheSystemWriterSharesTheOneReportFragment:
    """amendment 7 §1 "ONE fragment builder, two entry points" (+ amendment 9 §4): a member ``report`` and
    ``report_system`` execute the SAME composed transaction —
    ``_governed_contract_64.REPORT_SYSTEM_TXN_GOLDEN`` (the governed triple BOUND) — so a padded CREATE
    moves BOTH (the sharing pin; mutation-proven in REPORT §MUTATION). Compared whitespace-normalised, the
    classifier's own leg-2 rule."""

    async def test_both_writers_execute_the_golden_transaction(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD (no capability= / no report_system; HEAD's CREATE carries no triple)."""
        _require_report_system()
        golden = _normalise_statement(REPORT_SYSTEM_TXN_GOLDEN)
        async with system_ledger_world(provision_project_keep=True) as world:
            with monkeypatch.context() as scoped:
                seen = _recorded_transactions(scoped)
                await world.file_drift()
            assert seen and _normalise_statement(seen[-1]) == golden, (
                f"report_system's executed transaction is not the golden: {seen!r}"
            )
        async with finding_world(monkeypatch, tmp_path) as world:
            with monkeypatch.context() as scoped:
                seen = _recorded_transactions(scoped)
                await world.findings(
                    "ag-a1", action="report", subject="member", body="", area="a", category="c"
                )
            assert seen and _normalise_statement(seen[-1]) == golden, (
                f"a member report's executed transaction is not the SAME golden (two fragment builders): "
                f"{seen!r}"
            )


# =========================================================================== #
# F5 — the write classifies under ITS OWN exempt, and only it.
# =========================================================================== #


class TestTheSystemWriterClassifiesUnderItsOwnExempt:
    """amendment 7 §1 "Attribution": the F5 battery DRIVES the production adapter under observation; the
    system write CLASSIFIES via the ``calibration-drift`` exempt entry (name · golden · effect · origin
    ``report_system``); CONTROL: with the token removed the same write is UNCLASSIFIED (deny-by-default
    works); a member ``report`` stays on the LABEL leg."""

    async def test_the_adapter_driven_write_classifies_via_the_exempt(self) -> None:
        """⚠ RED at HEAD (no system path — the adapter calls ``report`` without an identity)."""
        _require_report_system()
        async with system_ledger_world(provision_project_keep=True) as world:
            with observe_governed_table_writes(FINDING_TABLE) as writes:
                await world.file_drift_via_adapter()
            assert writes, "no finding write was OBSERVED — F5 cannot certify an unobserved writer"
            for write in writes:
                assert getattr(write.exempt, "name", None) == CALIBRATION_DRIFT_EXEMPT, write
                assert getattr(write.exempt, "origin", None) == (
                    "loremaster/loremaster/findings.py",
                    "report_system",
                ), write
                assert write.label is None, (
                    f"the system write rides a LABEL too (a second channel): {write!r}"
                )
                assert classify_tree_observed_write(write, FINDING_TREE_ALLOWLIST), write

    async def test_the_token_statement_IS_the_observed_statement(self) -> None:
        """⚠ RED at HEAD. amendment 9 §4: ``report_system`` derives its token text from the ONE composer and
        ``_apply`` composes the identical bytes — so the token's statement EQUALS the observed statement
        EXACTLY (not merely whitespace-normalised): leg 2 is then a fact about the same bytes, never a claim
        about two producers. A token built from a hand-written text, a statement slice, or a second composer
        reds here."""
        _require_report_system()
        async with system_ledger_world(provision_project_keep=True) as world:
            with observe_governed_table_writes(FINDING_TABLE) as writes:
                await world.file_drift()
            assert writes, "no finding write was OBSERVED"
            for write in writes:
                token_statement = getattr(write.exempt, "statement", None)
                assert token_statement == write.statement, (
                    "the exempt token's statement is not the observed bytes:"
                    f"\n  token:    {token_statement!r}"
                    f"\n  observed: {write.statement!r}"
                )

    async def test_CONTROL_without_the_token_the_write_is_unclassified(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at HEAD. Rebinding THE ``governed_exempt`` (by identity) to a token-less context: the same
        write is observed with no exempt and must NOT classify — the entry is what attributes it."""
        _require_report_system()

        @contextlib.contextmanager
        def _no_token(*_args: Any, **_kwargs: Any) -> Any:
            yield None

        async with system_ledger_world(provision_project_keep=True) as world:
            patch_shared_object_everywhere(
                monkeypatch,
                "governed_exempt",
                governed.governed_exempt,
                _no_token,
                expect_in=("loremaster.governed",),
            )
            with observe_governed_table_writes(FINDING_TABLE) as writes:
                await world.file_drift()
            assert writes, "CONTROL: the write was not observed"
            assert not any(classify_tree_observed_write(write, FINDING_TREE_ALLOWLIST) for write in writes), (
                "a token-less system write CLASSIFIED — the allowlist blesses it by something other than "
                "its exempt"
            )

    @staticmethod
    def _unit_write(
        statement: str, *, token_statement: str | None = None, extra: RowDelta | None = None
    ) -> Any:
        """A pure-unit observed system write: the created drift row (+ optionally a second mutation), under
        the calibration-drift token whose text is ``token_statement`` (default: ``statement``)."""
        from _governed_contract import ExemptToken, ObservedWrite  # noqa: PLC0415

        empty = SchemaDelta(added=frozenset(), removed=frozenset(), changed=frozenset())
        after = {
            "owner_principal": None,
            "owner_agent": None,
            "scope": "keep:01JB6Q8V0Z6X3K9M2N4P5R7S8T",
            "status": "open",
            "area": CALIBRATION_AREA,
            "created_by": DRIFT_CREATED_BY,
        }
        created = RowDelta(
            id="f1", kind="created", changed_columns=frozenset(after), before=None, after=after
        )
        deltas = (created,) if extra is None else (created, extra)
        origin = ("loremaster/loremaster/findings.py", "report_system")
        token = ExemptToken(
            CALIBRATION_DRIFT_EXEMPT, statement if token_statement is None else token_statement, origin
        )
        return ObservedWrite(
            label=None,
            effect=ObservedEffect(row_deltas=deltas, schema_delta=empty),
            exempt=token,
            statement=statement,
        )

    def test_the_golden_transaction_classifies_and_every_discriminator_refuses(self) -> None:
        """amendment 9 §4's three discrimination pins, each beside the CONTROL that the SAME write classifies
        with the discriminating edit undone (so every refusal is the leg's, never a broken fixture):
        (1) token ≠ observed → UNCLASSIFIED (leg 2); (2) the entry's golden EDITED → UNCLASSIFIED (coverage —
        leg 2 against the adjudicated text); (3) a second governed mutation inside the block → UNCLASSIFIED
        (leg 3 — the effect sees two row deltas). ⚠ RED at HEAD only through the entry's effect/scope legs'
        build dependencies; the discriminators themselves hold at HEAD."""
        import dataclasses  # noqa: PLC0415

        golden = REPORT_SYSTEM_TXN_GOLDEN
        assert classify_tree_observed_write(self._unit_write(golden), FINDING_TREE_ALLOWLIST), (
            "CONTROL: the golden composed transaction under its own token does not classify"
        )
        drifted = golden.replace("supersedes: NONE", "supersedes: $smuggled")
        assert drifted != golden, "fixture: the drift edit did not land"
        assert not classify_tree_observed_write(
            self._unit_write(drifted, token_statement=golden), FINDING_TREE_ALLOWLIST
        ), "(1) the observed transaction differs from the token's text and still classified"
        edited_allowlist = tuple(
            dataclasses.replace(entry, statement=drifted)
            if entry.exempt_name == CALIBRATION_DRIFT_EXEMPT
            else entry
            for entry in FINDING_TREE_ALLOWLIST
        )
        assert edited_allowlist != tuple(FINDING_TREE_ALLOWLIST), (
            "fixture: no calibration-drift entry to edit"
        )
        assert not classify_tree_observed_write(self._unit_write(golden), edited_allowlist), (
            "(2) the adjudicated golden was edited and the unchanged write still classified"
        )
        second = RowDelta(
            id="f2",
            kind="updated",
            changed_columns=frozenset({"status"}),
            before={"status": "open"},
            after={"status": "resolved"},
        )
        assert not classify_tree_observed_write(
            self._unit_write(golden, extra=second), FINDING_TREE_ALLOWLIST
        ), "(3) a second governed mutation inside the exempt block classified"

    def test_the_effect_predicate_discriminates(self) -> None:
        """GREEN at HEAD (a pure predicate): the leg that stops laundering — an owned row, a non-keep scope,
        a foreign area or author, a non-create each fail it."""
        empty = SchemaDelta(added=frozenset(), removed=frozenset(), changed=frozenset())
        good = {
            "owner_principal": None,
            "owner_agent": None,
            "scope": "keep:01JB6Q8V0Z6X3K9M2N4P5R7S8T",
            "status": "open",
            "area": CALIBRATION_AREA,
            "created_by": DRIFT_CREATED_BY,
        }

        def _effect(after: dict[str, Any], kind: str = "created") -> ObservedEffect:
            delta = RowDelta(id="f1", kind=kind, changed_columns=frozenset(after), before=None, after=after)
            return ObservedEffect(row_deltas=(delta,), schema_delta=empty)

        assert effect_finding_report_system(_effect(good))
        for column, bad in (
            ("owner_principal", "principal:alice"),
            ("owner_agent", "agent:ag_a1"),
            ("scope", "server"),
            ("scope", None),
            ("area", "lore_search"),
            ("created_by", "ag-a1"),
            ("status", "resolved"),
        ):
            assert not effect_finding_report_system(_effect({**good, column: bad})), (column, bad)
        assert not effect_finding_report_system(_effect(good, kind="updated"))


# =========================================================================== #
# Reach — ONE production caller, no served verb.
# =========================================================================== #


class TestTheSystemWriterHasOneProducer:
    """amendment 7 §1 "Reach": ``report_system`` is in NO served dispatch table and has EXACTLY ONE
    production caller — ``_CalibrationFindingsAdapter.report_drift_finding`` — derived over the WHOLE
    production tree (THE shared parse), never a file hand-list."""

    def test_exactly_one_production_caller(self) -> None:
        """⚠ RED at HEAD (no caller at all — the adapter calls ``report``)."""
        from _logging_fixtures import parse_production_trees  # noqa: PLC0415

        callers: list[tuple[str, str]] = []
        for relative, tree in parse_production_trees(include_scripts=True).items():
            owners: dict[int, str] = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    for child in ast.walk(node):
                        owners.setdefault(id(child), node.name)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "report_system":
                    callers.append((relative, owners.get(id(node), "<module>")))
        assert callers == [("loremaster/loremaster/server.py", "report_drift_finding")], (
            f"report_system's production callers must be EXACTLY the calibration adapter: {callers}"
        )
        actions = vars(server)["_FINDING_ACTIONS"]
        assert "report_system" not in actions, (
            "report_system is a SERVED verb — a member-reachable system door"
        )


# =========================================================================== #
# The project keep is a PRECONDITION — loud, non-fatal.
# =========================================================================== #


class TestAnUnprovisionedProjectKeepIsLoudAndNonFatal:
    """amendment 7 §1 "The project keep is a PRECONDITION": no project keep ⇒ ``report_system`` raises the
    substrate's typed refusal; the ADAPTER catches that ONE typed class, logs ``calibration.drift.unfiled``
    at ERROR with the reason, and does not raise (an alarm that cannot be filed must not take the server
    down; it must be SEEN). CONTROL: provisioned ⇒ one row, no ERROR."""

    async def test_unprovisioned(self, caplog: pytest.LogCaptureFixture) -> None:
        """⚠ RED at HEAD (the adapter's identity-less ``report`` path)."""
        _require_report_system()
        async with system_ledger_world(provision_project_keep=False) as world:
            with pytest.raises(governed.GovernedDenied):
                await world.file_drift()  # the writer itself refuses, typed
            caplog.clear()
            with caplog.at_level(logging.ERROR):
                await world.file_drift_via_adapter()  # the boot path: caught, loud, non-fatal
            unfiled = [
                record for record in caplog.records if "calibration.drift.unfiled" in record.getMessage()
            ]
            assert len(unfiled) == 1 and unfiled[0].levelno == logging.ERROR, [
                (record.levelname, record.getMessage()) for record in caplog.records
            ]
            assert await world.findings() == [], "a refused system write left a row"

    async def test_CONTROL_provisioned(self, caplog: pytest.LogCaptureFixture) -> None:
        """⚠ RED at HEAD. The same adapter call with the keep provisioned: exactly one row, no ERROR."""
        _require_report_system()
        async with system_ledger_world(provision_project_keep=True) as world:
            caplog.clear()
            with caplog.at_level(logging.ERROR):
                await world.file_drift_via_adapter()
            assert not [record for record in caplog.records if record.levelno >= logging.ERROR], [
                record.getMessage() for record in caplog.records
            ]
            assert len(await world.findings()) == 1
