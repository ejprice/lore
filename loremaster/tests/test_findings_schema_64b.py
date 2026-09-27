"""Contract — packet 64b-i: the ``finding`` SCHEMA under the retrofit (kickoff rulings ``e5fa7f9`` §12 DD-3.c
row; P64 §Scope IN 1 + 8). Authored by ``contract-64b`` (Opus 5.5 — contract tests ONLY).

THE P2 ``[finding]`` ROW as a NEW PARAMETRISATION FILE (kickoff §13: ``test_comms_schema.py`` is a
63c-shared file, so the row lands here and is FOLDED into that file's parametrised pin by the HELD patch).
``_ConstraintSpec`` / ``_assert_no_violable_constraint`` / ``_synthetic_violating_ddl`` ARE importable
from ``test_comms_schema`` (the class is module-scope) — so this file is a CALLER of the ONE checker,
never a second copy (the kickoff §13 fallback "write it against a twin" was not needed; said so in the
REPORT).

DD-3.c (the ii-b discriminator, kickoff §12): each ASSERT a whole-table migration UPDATE re-validates is
KEPT iff its violation set ≡ the reader's own decode-rejection set, else DROPPED. ``Finding`` decodes
``kind``/``subject``/``area``/``category``/``created_by`` as ``str`` (ANY value) → their non-empty
ASSERTs are WIDER than the reader → DROP (a legacy blank would abort the cutover — the ``to.ack_note``
total-denial class). ``status`` decodes as the ``FindingStatus`` Literal → its domain ASSERT ≡ the reader
→ KEEP (P-F2 pins the alignment). The dropped rules' VIRTUE is PRESERVED-WITH-PIN in the ONE writer: the
MOVE pins below (``FindingLedger.report`` refuses a blank ``kind``/``subject``/``created_by`` through
``lorerunes.is_blank`` BEFORE any store I/O — F-4: at HEAD the ledger guards only area/category).

Birth set GIT-DERIVED (INSTRUMENT-0 — never the ruling's candidate list): ``git log -S
_FINDING_FIELD_SPECS`` → ``d5cbeaf`` (2026-07-04), whose spec carries all eleven columns; so every
current column is a birth column and only the governed trio is post-birth (⇒ ``option<>``). ⚠ And a
HISTORY FACT that makes Leg A/B load-bearing on the real store: at ``d5cbeaf`` ``area``/``category`` had
NO ASSERT (added later), so production rows filed before that commit may legally carry a BLANK
``area``/``category`` — exactly the legacy violators Leg B migrates.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, get_args

import pytest
from _governed_contract import member
from _governed_contract_64 import (
    FINDING_DROPPED_ASSERT_COLUMNS,
    FINDING_KEPT_ASSERT_COLUMN,
    LEDGER_IDENTITY_KWARG,
    LEDGER_TITLE_KWARG,
    frozen_asserted_finding_ddl,
)
from loremaster.findings import FINDING_STATUSES, FindingLedger, FindingStatus
from loremaster.store.surreal_schema import generate_finding_ddl
from pydantic import SecretStr
from test_comms_schema import (
    _assert_no_violable_constraint,
    _ConstraintSpec,
    _schema,
    _synthetic_violating_ddl,
)

import lorerunes

if TYPE_CHECKING:
    # 64b-i's RULED, not-yet-built signature this file pins — a TYPED CALL (amendment 8 §5, MP-9: mypy's
    # ``[call-arg]`` sees a renamed or missing kwarg, so the bound discharges only on the ruled SHAPE; a
    # permanent
    # signature pin — mypy checks TYPE_CHECKING bodies after the build too). Until the build lands it, a
    # mypy error
    # OWNED by `scripts/pending_contracts.yaml` bound `packet-64b-i-contract` (lead #17055, #461).
    # Runtime-inert.
    # DUAL (r2): r1's ``_ruled_64b_i_report_takes_the_caller`` (``caller=``) is RE-KEYED by amendment 7 §2
    # (FK-1):
    # the identity kwarg is ``subject=`` and the title is ``title``.
    async def _ruled_64b_i_report_takes_the_subject(
        ledger: FindingLedger, subject: lorerunes.Subject
    ) -> None:
        """FK-1: the ONE writer (where DD-3.c's blank rule MOVES) takes the verified identity as "
        "``subject=``."""
        await ledger.report(
            title="t", body="b", area="a", category="c", created_by="c", subject=subject, scope=None
        )


#: The ``[finding]`` P2 row (kickoff §12 DD-3.c row). ``hazard`` names THIS table's writer, its
#: UPDATE-able mechanism and its dirty-store pins (the r2 sidecar-F1 rule: never another table's prose).
FINDING_CONSTRAINT_SPEC = _ConstraintSpec(
    "FINDING_TABLE",
    make_ddl=generate_finding_ddl,
    hazard=(
        "`finding` is UPDATE-able whole-window: the `migrate-governed --table finding` cutover backfill "
        "re-validates every legacy finding in ONE statement, and every status verb (`acknowledge`/"
        "`resolve`/`wontfix`/`annotate`) re-validates the WHOLE row it touches, so a legacy blank would "
        "refuse the cutover and freeze that finding. The rule lives in `FindingLedger.report` (the ONE "
        "implementation — `lorerunes.is_blank`); the dirty-store pins are test_findings_migrate_64b.py "
        "(Leg A / Leg B / P-F3, kickoff §12 DD-3.c)"
    ),
    # birth = GIT-DERIVED: `git log -S _FINDING_FIELD_SPECS` → d5cbeaf, all eleven columns present.
    birth=frozenset(
        {
            "number",
            "kind",
            "status",
            "subject",
            "body",
            "area",
            "category",
            "created_by",
            "created_at",
            "supersedes",
            "provenance",
        }
    ),
    birth_defaults=frozenset({"status", "created_at"}),  # both present at d5cbeaf.
    exemptions=frozenset({FINDING_KEPT_ASSERT_COLUMN}),  # status: reader-aligned (FindingStatus) — KEPT.
    # (DUAL r2 → am-9: the r2 draft exempted `scope` for amendment 8 §2's store ASSERT; amendment 9 §2
    # WITHDREW that ASSERT (63a §4.1 stands), so `scope` carries NO constraint and needs no exemption —
    # r1's spec, restored.)
    floor=frozenset({"number", "status", "created_by", "owner_principal", "scope"}),  # a derivation that
    # loses a birth identity column, the KEPT status, or the governed overlay must RED (non-vacuity).
)


class TestTheFindingTableCarriesNoConstraintALegacyRowCanViolate:
    """P2 ``[finding]`` — the SAME ∀-no-constraint check the ``to``/``message``/``agent`` rows run (the
    quantifier law: ∀ EMITTED field, not the one field a ruling was derived on). FOLDS into
    ``test_comms_schema.py::TestNoGovernedTableCarriesAConstraintALegacyRowCanViolate`` at integration."""

    def test_no_finding_field_carries_a_constraint_a_legacy_row_can_violate(self) -> None:
        """⚠ RED at HEAD: the emitter carries the five non-empty ASSERTs AND lacks the governed overlay
        (``owner_principal``/``scope`` are in the floor → the non-vacuity leg reds first). After the
        build GREEN, and RED the day a finding constraint returns or the overlay regresses."""
        _assert_no_violable_constraint(FINDING_CONSTRAINT_SPEC, FINDING_CONSTRAINT_SPEC.make_ddl())

    def test_the_served_red_names_the_finding_writer_and_its_pins(self) -> None:
        """GREEN at HEAD (prose-only; the synthetic DDL's ONLY defect is one ASSERT on ``kind``). The r2
        rider: the RED a builder reads when re-adding a finding constraint names ``FindingLedger.report``,
        the finding cutover, and THIS wave's dirty-store file — never the message/agent writer."""
        with pytest.raises(AssertionError) as exc_info:
            _assert_no_violable_constraint(
                FINDING_CONSTRAINT_SPEC, _synthetic_violating_ddl(FINDING_CONSTRAINT_SPEC, "kind")
            )
        served = str(exc_info.value)
        assert "`finding.kind` carries a store ASSERT" in served, served
        for token in (
            "FindingLedger.report",
            "migrate-governed --table finding",
            "test_findings_migrate_64b.py",
        ):
            assert token in served, (token, served)
        for token in ("MessageLedger", "AgentRegistry"):
            assert token not in served, (token, served)


class TestTheFrozenOldWorldIsAFaithfulCapture:
    """CONTROL — the frozen ``6a09954`` capture carries all six ASSERT literals; the Leg A BASELINE and the
    Leg B C-CONTROL rest on it. Verified against WHAT IT FROZE, never the live emitter (which this wave is
    designed to change). GREEN at HEAD AND after the build (the constant is immutable)."""

    def test_the_capture_carries_every_asserted_column(self) -> None:
        frozen = frozen_asserted_finding_ddl()
        for column in FINDING_DROPPED_ASSERT_COLUMNS:
            assert re.search(
                rf"DEFINE FIELD OVERWRITE {column} ON finding TYPE string "
                r"ASSERT string::len\(string::trim\(\$value\)\) > 0;",
                frozen,
            ), column
        assert "ASSERT $value IN ['open', 'acknowledged', 'resolved', 'wontfix']" in frozen


class TestTheKeptStatusAssertIsReaderAligned:
    """P-F2 (kickoff §12): the KEPT ``status`` ASSERT's literal set == ``FINDING_STATUSES`` ==
    ``get_args(FindingStatus)`` — the alignment that justifies KEEPING it (a drift in any of the three is
    a reader/store disagreement: a status the store accepts and the reader refuses, or vice versa)."""

    def test_the_three_status_sets_agree(self) -> None:
        """GREEN at HEAD AND after the build — an INVARIANT the retrofit must not break. Mutation-proven in
        the report (add a status to ``_FINDING_STATUSES`` only → RED)."""
        statement = next(
            line
            for line in generate_finding_ddl().splitlines()
            if line.startswith("DEFINE FIELD OVERWRITE status ON finding")
        )
        emitted = set(re.findall(r"'([a-z_]+)'", statement.split("ASSERT", 1)[1]))
        assert emitted == set(FINDING_STATUSES) == set(get_args(FindingStatus)), (
            emitted,
            sorted(FINDING_STATUSES),
            get_args(FindingStatus),
        )


# =========================================================================== #
# The MOVE pins — the dropped ASSERTs' virtue lives in the ONE writer.
# =========================================================================== #

_BLANKS = ("", "   ", "\t\n")


class _NoStoreIo(Exception):
    """Raised by the patched connection opener — proves a refusal happened BEFORE any store I/O."""


def _offline_ledger(monkeypatch: pytest.MonkeyPatch) -> FindingLedger:
    ledger = FindingLedger(
        url="ws://127.0.0.1:18000/rpc",
        namespace="lore_test",
        database="move_pin_offline",
        user="root",
        password=SecretStr("unused"),
    )

    async def _refuse_io(*_args: Any, **_kwargs: Any) -> Any:
        raise _NoStoreIo("the report touched the store before validating its arguments")

    monkeypatch.setattr(ledger, "_ensure_connection", _refuse_io)
    return ledger


def _report_kwargs(**overrides: Any) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "kind": "friction",
        "area": "lore_search",
        "category": "capability_gap",
        "created_by": "ag-a1",
        LEDGER_IDENTITY_KWARG: member("alice", "ag_a1", frozenset({lorerunes.keep_scope("keepalpha")})),
    }
    kwargs.update(overrides)
    return kwargs


class TestTheDroppedAssertsMoveIntoTheWriter:
    """The MOVE pins (kickoff §12 DD-3.c row; §14 item 16 — PRESERVED-WITH-PIN). ∀ the five dropped
    columns × three blank shapes: ``FindingLedger.report`` raises ``ValueError`` naming the column, BEFORE
    any store I/O (the patched opener raises ``_NoStoreIo`` if touched). ``subject`` is the finding TITLE
    (the report's first positional)."""

    @pytest.mark.parametrize("blank", _BLANKS)
    @pytest.mark.parametrize("column", FINDING_DROPPED_ASSERT_COLUMNS)
    async def test_report_refuses_a_blank_before_any_store_io(
        self, monkeypatch: pytest.MonkeyPatch, column: str, blank: str
    ) -> None:
        """⚠ RED at HEAD for ``kind``/``subject``/``created_by`` (F-4: no ledger-side blankness check —
        the blank reaches the store) and for every column via the identity keyword (``report`` takes no
        ``subject=`` Subject at HEAD — FK-1). Kills: a guard on area/category only; a guard AFTER the
        counter bump; a
        hand-rolled ``strip`` that misses ``\\t\\n``… (the shared predicate is pinned below)."""
        from inspect import Parameter, signature  # noqa: PLC0415

        # DUAL (r2, amendment 7 §2): r1 checked the kwarg's NAME only — with FK-1's ``subject`` that name is
        # ALSO
        # HEAD's positional TITLE, so the name check passes at HEAD and the call dies on a TypeError (the
        # wrong
        # reason). The guard now checks the ruled SHAPE: a keyword-only ``subject`` and a ``title`` parameter.
        parameters = signature(FindingLedger.report).parameters
        identity = parameters.get(LEDGER_IDENTITY_KWARG)
        assert (
            identity is not None
            and identity.kind is Parameter.KEYWORD_ONLY
            and LEDGER_TITLE_KWARG in parameters
        ), (
            "UNBUILT (amendment 7 §2 FK-1): FindingLedger.report takes no keyword-only "
            f"`{LEDGER_IDENTITY_KWARG}=` "
            f"Subject and no `{LEDGER_TITLE_KWARG}` title: {signature(FindingLedger.report)}"
        )
        ledger = _offline_ledger(monkeypatch)
        title = blank if column == "subject" else "a real title"
        overrides = {} if column == "subject" else {column: blank}
        # FK-1 renames only the Python parameter (``title``); the column/served name stays ``subject``. Either
        # name teaches a caller which argument was blank, so the title leg admits both (never a third).
        with pytest.raises(ValueError, match=column if column != "subject" else "subject|title"):
            await ledger.report(title, "body", **_report_kwargs(**overrides))

    def test_report_uses_the_shared_blankness_predicate(self) -> None:
        """⚠ RED at HEAD (``report`` hand-rolls ``.strip()`` for area/category, via
        ``_require_non_empty_area_category``). ONE answer to "what counts as blank?" (lorerunes #222):
        ``report`` (or the one helper it calls) references ``is_blank``."""
        import ast  # noqa: PLC0415
        import inspect  # noqa: PLC0415

        source = inspect.getsource(FindingLedger)
        tree = ast.parse(source)
        class_node = next(node for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
        methods = {
            node.name: node
            for node in class_node.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        report_calls = {
            (node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", ""))
            for node in ast.walk(methods["report"])
            if isinstance(node, ast.Call)
        }
        candidates = {"report"} | (report_calls & set(methods))
        uses = any(
            isinstance(node, ast.Name) and node.id == "is_blank"
            for name in candidates
            for node in ast.walk(methods[name])
        )
        assert uses, (
            "FindingLedger.report does not route its blankness rule through lorerunes.is_blank (#222)"
        )
        assert _schema().FINDING_TABLE == "finding"
