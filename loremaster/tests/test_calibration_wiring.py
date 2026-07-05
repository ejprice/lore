"""Wiring tests for the boot token-calibration engine into the server (P8c).

Pure, hermetic unit tests over the server-side SEAMS the wiring adds — no SurrealDB
and no network, every collaborator is a fake:

* the budget multiply site (:meth:`AppContext._count_tokens_single`) reads the
  engine's ``served_constant`` when an engine is present, falling back to the
  committed :data:`~loremaster.server.TOKEN_BUDGET_CALIBRATION` when absent;
* the findings-ledger adapter (``_CalibrationFindingsAdapter``) maps the engine's
  narrow ``FindingsPort`` onto the real ``FindingLedger.query`` / ``.report``;
* the ``index_status`` calibration section models (``CalibrationStatus`` /
  ``IndexStatusSummary``) round-trip ``CalibrationEngine.status()``;
* the boot probe-start hook (:meth:`AppContext.start_calibration_probe`) starts the
  engine (non-blocking) and emits the structured boot log line.

The end-to-end BUILD wiring — the real ``build_app_context`` construction from
``config.anthropic``, the ``index_status`` render over a live engine, and the
``aclose`` teardown — is pinned in ``test_mcp_server.py`` alongside the SurrealDB
harness fixtures (those need a live store; these do not).
"""

from __future__ import annotations

import logging
import math
from types import SimpleNamespace
from typing import Any, cast

import pytest
from loremaster.calibration.engine import (
    CALIBRATION_AREA,
    DRIFT_CATEGORY,
    DRIFT_CREATED_BY,
    DRIFT_KIND,
    STATE_CACHED,
    STATE_CACHED_RETRYING,
    STATE_DRIFT_ADOPTED,
    STATE_MEASURED,
)
from loremaster.findings import (
    STATUS_ACKNOWLEDGED,
    STATUS_OPEN,
    STATUS_RESOLVED,
    FindingLedger,
)
from loremaster.server import (
    TOKEN_BUDGET_CALIBRATION,
    AppContext,
    CalibrationStatus,
    IndexStatusSummary,
    _CalibrationFindingsAdapter,
)

_ALL_STATES = [STATE_CACHED, STATE_MEASURED, STATE_DRIFT_ADOPTED, STATE_CACHED_RETRYING]
_BOOT_LOG_EVENT = "startup.calibration.committed"


# --------------------------------------------------------------------------- #
# Fakes — each collaborator the seams touch, replaced by a recording double.
# --------------------------------------------------------------------------- #
class _FakeEmbedder:
    """A batch token counter that returns a fixed voyage count per input text."""

    def __init__(self, voyage_count: int) -> None:
        self._voyage_count = voyage_count

    def count_tokens(self, texts: list[str]) -> list[int]:
        return [self._voyage_count for _ in texts]


class _FakeServedEngine:
    """The budget seam reads only ``served_constant`` — serve a fixed float."""

    def __init__(self, served: float) -> None:
        self._served = served

    @property
    def served_constant(self) -> float:
        return self._served


class _RecordingFindingLedger:
    """Records ``query`` / ``report`` calls; returns configured rows by status.

    Mirrors the ``FindingLedger`` surface the adapter consumes: ``query`` takes an
    exact ``status`` filter (a single status), and ``report`` takes the two
    positional ``subject`` / ``body`` plus the keyword-only finding coordinates.
    """

    def __init__(self, *, by_status: dict[str, list[Any]] | None = None) -> None:
        self._by_status = by_status or {}
        self.query_calls: list[dict[str, Any]] = []
        self.report_calls: list[dict[str, Any]] = []

    async def query(
        self,
        *,
        status: str | None = None,
        kind: str | None = None,
        area: str | None = None,
        limit: int = 100,
    ) -> list[Any]:
        self.query_calls.append({"status": status, "kind": kind, "area": area, "limit": limit})
        if status is None:
            return []
        return list(self._by_status.get(status, []))

    async def report(
        self,
        subject: str,
        body: str,
        *,
        kind: str,
        area: str,
        category: str,
        created_by: str,
        supersedes: int | str | None = None,
    ) -> Any:
        self.report_calls.append(
            {
                "subject": subject,
                "body": body,
                "kind": kind,
                "area": area,
                "category": category,
                "created_by": created_by,
                "supersedes": supersedes,
            }
        )
        return SimpleNamespace(id="finding:test", number=1)


class _SpyProbeEngine:
    """A calibration-engine spy: records start()/stop(); status() is a fixed dict."""

    def __init__(self, status_dict: dict[str, Any]) -> None:
        self._status = status_dict
        self.started = False
        self.stopped = False

    @property
    def served_constant(self) -> float:
        return float(self._status["served_constant"])

    def status(self) -> dict[str, Any]:
        return dict(self._status)

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True


def _status_dict(state: str, *, served: float = 1.78, committed: float = 1.78) -> dict[str, Any]:
    """The exact snapshot dict ``CalibrationEngine.status()`` returns, for ``state``."""
    return {
        "state": state,
        "served_constant": served,
        "committed_constant": committed,
        "model": "claude-sonnet-5",
        "ratio_shift": None if state in (STATE_CACHED,) else 0.05,
        "last_probe_at": None if state == STATE_CACHED else "2026-07-04T00:00:00+00:00",
        "baseline_generated_at": "2026-07-04T00:00:00+00:00",
        "note": None,
    }


# --------------------------------------------------------------------------- #
# Budget seam — AppContext._count_tokens_single
# --------------------------------------------------------------------------- #
class TestBudgetUsesServedConstant:
    """The budget multiply reads the engine's served constant, falling back to
    the committed constant when no engine is wired (the ``TestTokenBudgetCalibration``
    ``SimpleNamespace(embedder=...)`` guard shape must stay green)."""

    def test_scales_by_engine_served_constant(self) -> None:
        # A DISTINCT served value (3.0, not the committed 1.78): the count must
        # scale by the ENGINE's constant, proving the wire-through — not the module
        # literal. ``cast`` is the SAME structural stand-in the test_map guard uses:
        # _count_tokens_single reads only ``self.embedder`` + ``self._calibration_engine``.
        namespace = cast(
            AppContext,
            SimpleNamespace(embedder=_FakeEmbedder(7), _calibration_engine=_FakeServedEngine(3.0)),
        )
        counted = AppContext._count_tokens_single(namespace, "irrelevant")
        assert counted == math.ceil(7 * 3.0) == 21

    def test_falls_back_to_committed_when_engine_attribute_absent(self) -> None:
        # No ``_calibration_engine`` attribute at all — the exact shape the
        # test_map calibration guard builds (SimpleNamespace(embedder=...)). Must
        # use the committed constant, never AttributeError.
        namespace = cast(AppContext, SimpleNamespace(embedder=_FakeEmbedder(7)))
        counted = AppContext._count_tokens_single(namespace, "irrelevant")
        assert counted == math.ceil(7 * TOKEN_BUDGET_CALIBRATION)

    def test_falls_back_to_committed_when_engine_is_none(self) -> None:
        namespace = cast(
            AppContext, SimpleNamespace(embedder=_FakeEmbedder(7), _calibration_engine=None)
        )
        counted = AppContext._count_tokens_single(namespace, "irrelevant")
        assert counted == math.ceil(7 * TOKEN_BUDGET_CALIBRATION)


# --------------------------------------------------------------------------- #
# Findings adapter — _CalibrationFindingsAdapter over FindingLedger
# --------------------------------------------------------------------------- #
class TestFindingsAdapter:
    """The narrow ``FindingsPort`` the engine files drift through, mapped onto the
    durable ``FindingLedger``: dedupe counts open OR acknowledged as live; report
    forwards a well-formed finding."""

    async def test_has_open_true_when_an_open_finding_exists(self) -> None:
        ledger = _RecordingFindingLedger(by_status={STATUS_OPEN: [SimpleNamespace(number=1)]})
        adapter = _CalibrationFindingsAdapter(cast(FindingLedger, ledger))
        assert await adapter.has_open_drift_finding(CALIBRATION_AREA) is True
        assert {call["area"] for call in ledger.query_calls} == {CALIBRATION_AREA}
        assert STATUS_OPEN in {call["status"] for call in ledger.query_calls}

    async def test_has_open_true_when_only_acknowledged_exists(self) -> None:
        # An acknowledged-but-unresolved drift is still LIVE — must not be re-filed.
        ledger = _RecordingFindingLedger(
            by_status={STATUS_ACKNOWLEDGED: [SimpleNamespace(number=2)]}
        )
        adapter = _CalibrationFindingsAdapter(cast(FindingLedger, ledger))
        assert await adapter.has_open_drift_finding(CALIBRATION_AREA) is True
        assert STATUS_ACKNOWLEDGED in {call["status"] for call in ledger.query_calls}

    async def test_has_open_false_checks_both_open_and_acknowledged(self) -> None:
        # Only a RESOLVED finding exists → not live. Both open AND acknowledged
        # must have been checked before concluding False.
        ledger = _RecordingFindingLedger(by_status={STATUS_RESOLVED: [SimpleNamespace(number=3)]})
        adapter = _CalibrationFindingsAdapter(cast(FindingLedger, ledger))
        assert await adapter.has_open_drift_finding(CALIBRATION_AREA) is False
        checked = {call["status"] for call in ledger.query_calls}
        assert {STATUS_OPEN, STATUS_ACKNOWLEDGED} <= checked

    async def test_report_forwards_a_wellformed_finding(self) -> None:
        ledger = _RecordingFindingLedger()
        adapter = _CalibrationFindingsAdapter(cast(FindingLedger, ledger))
        await adapter.report_drift_finding(
            subject="token calibration drift: shifted +5%",
            body="model=claude-sonnet-5\nshift=+5.00%",
            area=CALIBRATION_AREA,
            category=DRIFT_CATEGORY,
            kind=DRIFT_KIND,
            created_by=DRIFT_CREATED_BY,
        )
        assert len(ledger.report_calls) == 1
        call = ledger.report_calls[0]
        assert call["subject"] == "token calibration drift: shifted +5%"
        assert call["body"] == "model=claude-sonnet-5\nshift=+5.00%"
        assert call["area"] == CALIBRATION_AREA
        assert call["category"] == DRIFT_CATEGORY
        assert call["kind"] == DRIFT_KIND
        assert call["created_by"] == DRIFT_CREATED_BY


# --------------------------------------------------------------------------- #
# index_status section models — CalibrationStatus / IndexStatusSummary
# --------------------------------------------------------------------------- #
class TestCalibrationStatusModel:
    """The pydantic sections that carry the engine's status into ``index_status``."""

    @pytest.mark.parametrize("state", _ALL_STATES)
    def test_round_trips_every_engine_status_state(self, state: str) -> None:
        # The state string must survive verbatim (the deployed exit criterion:
        # index_status visibly shows cached / measured / drift_adopted / cached_retrying).
        cal = CalibrationStatus(**_status_dict(state, served=1.87, committed=1.78))
        assert cal.state == state
        assert cal.served_constant == 1.87
        assert cal.committed_constant == 1.78
        assert cal.model == "claude-sonnet-5"

    def test_index_status_summary_carries_optional_calibration(self) -> None:
        summary = IndexStatusSummary(
            files_indexed=1,
            files_failed=0,
            files_skipped=0,
            tiers_rebuilt=[],
            tiers_skipped=[],
            outcomes=[],
            calibration=CalibrationStatus(
                state=STATE_MEASURED,
                served_constant=1.78,
                committed_constant=1.78,
                model="claude-sonnet-5",
            ),
        )
        assert summary.calibration is not None
        assert summary.calibration.state == STATE_MEASURED
        # A subclass of IndexSummary — the base fields still read straight through.
        assert summary.files_indexed == 1

    def test_index_status_summary_calibration_defaults_none(self) -> None:
        # Backward-compatible: a summary built without calibration renders None,
        # not a crash (the no-engine / not-yet-wired branch).
        bare = IndexStatusSummary(
            files_indexed=0,
            files_failed=0,
            files_skipped=0,
            tiers_rebuilt=[],
            tiers_skipped=[],
            outcomes=[],
        )
        assert bare.calibration is None


# --------------------------------------------------------------------------- #
# Boot probe-start hook — AppContext.start_calibration_probe
# --------------------------------------------------------------------------- #
class TestStartCalibrationProbe:
    """The lifespan-called hook: start the engine (non-blocking) + log the wiring."""

    async def test_starts_the_engine_and_logs_the_committed_line(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        spy = _SpyProbeEngine(_status_dict(STATE_CACHED, served=1.78, committed=TOKEN_BUDGET_CALIBRATION))
        namespace = cast(AppContext, SimpleNamespace(_calibration_engine=spy))
        with caplog.at_level(logging.INFO, logger="loremaster.server"):
            await AppContext.start_calibration_probe(namespace)
        assert spy.started is True
        boot_records = [r for r in caplog.records if r.getMessage() == _BOOT_LOG_EVENT]
        assert len(boot_records) == 1, "exactly one calibration boot log line"
        # The structured extras ride the record's ``__dict__`` (dict access, not
        # attribute access — LogRecord declares no such attributes statically).
        extras = boot_records[0].__dict__
        assert extras["committed"] == TOKEN_BUDGET_CALIBRATION
        assert extras["state"] == STATE_CACHED
        assert extras["served"] == 1.78
        assert extras["model"] == "claude-sonnet-5"

    async def test_is_a_silent_noop_without_an_engine(self) -> None:
        # A context built with no calibration engine (a test seam injecting None)
        # must not raise — the hook degrades silently.
        namespace = cast(AppContext, SimpleNamespace(_calibration_engine=None))
        await AppContext.start_calibration_probe(namespace)
