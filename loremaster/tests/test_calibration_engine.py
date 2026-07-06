"""Tests for :mod:`loremaster.calibration.engine` — the boot token-calibration engine.

The engine is the HYBRID *detect + auto-adopt-scaled* boot primitive: it serves a
budget-scaling constant that is the committed constant on a fresh boot, the prior-run
cache while a background probe is in flight, and — once the probe lands — either the
committed constant (live counts match the generation-anchored baseline) or a scaled
constant (the count generation drifted). A drifted probe also files ONE deduped finding.

Test doubles, split by what each exercises:

* **Programmed fake counter** (:class:`_ProgrammedCounter`) — deterministic per-file live
  totals and an optional asyncio gate, for the state-machine / arithmetic / cache / dedupe
  paths where endpoint *behaviour* is irrelevant and total *control* is what matters.
* **Real :class:`~loremaster.calibration.counting.AsyncClaudeTokenCounter` over
  :class:`httpx.MockTransport`** — for the endpoint-failure lifecycle, where the counter's
  own retry-then-raise semantics ARE the thing under test. Adversarial by default:
  fail-then-succeed sequences, never always-succeed.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from loremaster.calibration import baseline as bl
from loremaster.calibration import counting
from loremaster.calibration import engine as ce

# --- a tiny synthetic corpus + baseline (control the totals precisely) --------

_FILE_A = b"alpha alpha alpha\n"
_FILE_B = b"beta beta beta beta\n"
_TEXT_A = _FILE_A.decode("utf-8")
_TEXT_B = _FILE_B.decode("utf-8")

# baseline per-file counts → total 1000 (400 + 600), so ratios land on round numbers.
_BASELINE_A = 400
_BASELINE_B = 600
_BASELINE_TOTAL = _BASELINE_A + _BASELINE_B  # 1000

_FIXED_NOW = datetime(2026, 7, 4, 12, 0, 0, tzinfo=UTC)
_GENERATED_AT = "2026-07-04T00:00:00+00:00"
_MODEL = "claude-sonnet-5"
_COMMITTED = 1.78


def _synthetic_corpus() -> dict[str, bytes]:
    return {"a.py.txt": _FILE_A, "b.py.txt": _FILE_B}


def _synthetic_baseline(corpus: Mapping[str, bytes]) -> dict[str, Any]:
    """A complete baseline whose sha256s match ``corpus`` (integrity passes)."""
    files = {
        "a.py.txt": {"claude_tokens": _BASELINE_A, "voyage_tokens": None, "sha256": bl.sha256_hex(_FILE_A)},
        "b.py.txt": {"claude_tokens": _BASELINE_B, "voyage_tokens": None, "sha256": bl.sha256_hex(_FILE_B)},
    }
    return {
        "schema_version": bl.SCHEMA_VERSION,
        "generated_at": _GENERATED_AT,
        "generator": bl.GENERATOR_REL_PATH,
        "model": _MODEL,
        "generation_note": bl.GENERATION_NOTE,
        "endpoint": counting.ANTHROPIC_COUNT_TOKENS_URL,
        "files": files,
        "claude_total": _BASELINE_TOTAL,
        "voyage_total": None,
    }


# --- doubles ------------------------------------------------------------------


class _ProgrammedCounter:
    """A fake token counter returning a programmed count per (decoded) text.

    Optional ``gate``: when set, every :meth:`count` awaits it first, so a test can
    freeze the probe mid-flight and observe the served-cached state before releasing it.
    """

    def __init__(
        self,
        counts: Mapping[str, int],
        *,
        gate: asyncio.Event | None = None,
        closed: list[bool] | None = None,
    ) -> None:
        self._counts = counts
        self._gate = gate
        self.closed = closed if closed is not None else []

    async def count(self, text: str) -> int:
        if self._gate is not None:
            await self._gate.wait()
        return self._counts[text]

    async def aclose(self) -> None:
        self.closed.append(True)


def _programmed_factory(
    counts: Mapping[str, int], *, gate: asyncio.Event | None = None, closed: list[bool] | None = None
) -> Callable[[], _ProgrammedCounter]:
    def factory() -> _ProgrammedCounter:
        return _ProgrammedCounter(counts, gate=gate, closed=closed)

    return factory


class _FakeFindingsPort:
    """Records dedupe queries and drift filings; ``has_open`` may be preset or toggled.

    ``report_raises`` / ``has_open_raises`` make the respective method raise, so a test can
    reproduce a misbehaving findings store (the F1 filing-failure-observability probe).
    """

    def __init__(
        self,
        *,
        has_open: bool = False,
        file_flips_open: bool = False,
        report_raises: bool = False,
        has_open_raises: bool = False,
    ) -> None:
        self._has_open = has_open
        self._file_flips_open = file_flips_open
        self._report_raises = report_raises
        self._has_open_raises = has_open_raises
        self.queried_areas: list[str] = []
        self.reported: list[dict[str, str]] = []

    async def has_open_drift_finding(self, area: str) -> bool:
        self.queried_areas.append(area)
        if self._has_open_raises:
            raise RuntimeError("findings store unreachable (dedupe query)")
        return self._has_open

    async def report_drift_finding(
        self, *, subject: str, body: str, area: str, category: str, kind: str, created_by: str
    ) -> None:
        if self._report_raises:
            raise RuntimeError("findings store write failed")
        self.reported.append(
            {
                "subject": subject,
                "body": body,
                "area": area,
                "category": category,
                "kind": kind,
                "created_by": created_by,
            }
        )
        if self._file_flips_open:
            self._has_open = True


def _mock_counts_transport(counts: Mapping[str, int]) -> httpx.MockTransport:
    """A MockTransport returning ``input_tokens`` looked up by the request's text."""

    def handler(request: httpx.Request) -> httpx.Response:
        text = json.loads(request.content)["messages"][0]["content"]
        return httpx.Response(200, json={"input_tokens": counts[text]})

    return httpx.MockTransport(handler)


def _real_counter_factory(
    transport: httpx.MockTransport, *, counter_sleep: Callable[[float], Awaitable[None]]
) -> Callable[[], counting.AsyncClaudeTokenCounter]:
    """Build a FRESH real counter (own client) per probe attempt over ``transport``."""

    def factory() -> counting.AsyncClaudeTokenCounter:
        client = httpx.AsyncClient(transport=transport)
        return counting.AsyncClaudeTokenCounter(
            "k", model=_MODEL, client=client, sleep=counter_sleep, max_retries=2
        )

    return factory


async def _noop_sleep(_delay: float) -> None:
    return None


def _build_engine(
    tmp_path: Path,
    *,
    counter_factory: Callable[[], Any],
    port: _FakeFindingsPort | None = None,
    baseline: Mapping[str, Any] | None = None,
    corpus: Mapping[str, bytes] | None = None,
    committed: float = _COMMITTED,
    sleep: Callable[[float], Awaitable[None]] = _noop_sleep,
    clock: Callable[[], datetime] | None = None,
    drift_threshold: float = ce.DRIFT_THRESHOLD,
) -> ce.CalibrationEngine:
    the_corpus = _synthetic_corpus() if corpus is None else corpus
    the_baseline = _synthetic_baseline(the_corpus) if baseline is None else baseline
    return ce.CalibrationEngine(
        committed_constant=committed,
        model=_MODEL,
        api_key="k",
        state_dir=tmp_path,
        findings_port=port if port is not None else _FakeFindingsPort(),
        baseline=the_baseline,
        corpus=the_corpus,
        counter_factory=counter_factory,
        clock=clock if clock is not None else (lambda: _FIXED_NOW),
        sleep=sleep,
        drift_threshold=drift_threshold,
    )


async def _wait_state(engine: ce.CalibrationEngine, state: str, tries: int = 400) -> None:
    for _ in range(tries):
        if engine.status()["state"] == state:
            return
        await asyncio.sleep(0)
    raise AssertionError(f"engine never reached state {state!r}; stuck at {engine.status()['state']!r}")


def _cache_path(tmp_path: Path) -> Path:
    return tmp_path / "calibration" / f"{_MODEL}.json"


# --- module constants ---------------------------------------------------------


class TestModuleContract:
    def test_documented_constants(self) -> None:
        assert ce.DRIFT_THRESHOLD == 0.01
        assert ce.BACKOFF_START_S == 30.0
        assert ce.BACKOFF_CAP_S == 900.0
        assert ce.CALIBRATION_AREA == "token_calibration"
        assert ce.DRIFT_CATEGORY == "api_drift"
        assert ce.DRIFT_KIND == "drift"  # free-form kind (receipt: findings kind is not enum)
        assert ce.DRIFT_CREATED_BY == "calibration-engine"

    def test_state_string_constants(self) -> None:
        assert ce.STATE_CACHED == "cached"
        assert ce.STATE_MEASURED == "measured"
        assert ce.STATE_DRIFT_ADOPTED == "drift_adopted"
        assert ce.STATE_CACHED_RETRYING == "cached_retrying"


# --- fresh boot ---------------------------------------------------------------


class TestFreshBoot:
    async def test_serves_committed_before_start(self, tmp_path: Path) -> None:
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory({}))
        assert engine.served_constant == pytest.approx(_COMMITTED)
        status = engine.status()
        assert status["state"] == "cached"
        assert status["served_constant"] == pytest.approx(_COMMITTED)
        assert status["committed_constant"] == pytest.approx(_COMMITTED)
        assert status["model"] == _MODEL
        assert status["ratio_shift"] is None
        assert status["last_probe_at"] is None
        assert status["baseline_generated_at"] == _GENERATED_AT

    async def test_fresh_boot_no_cache_serves_committed_while_probing(self, tmp_path: Path) -> None:
        gate = asyncio.Event()
        engine = _build_engine(
            tmp_path,
            counter_factory=_programmed_factory({_TEXT_A: _BASELINE_A, _TEXT_B: _BASELINE_B}, gate=gate),
        )
        await engine.start()
        # Probe is gated (frozen mid-flight): still serving the committed constant.
        assert engine.served_constant == pytest.approx(_COMMITTED)
        assert engine.status()["state"] == "cached"
        gate.set()
        await engine.stop()


# --- measured (no drift) ------------------------------------------------------


class TestMeasured:
    async def test_identical_counts_measured_serves_committed(self, tmp_path: Path) -> None:
        transport = _mock_counts_transport({_TEXT_A: _BASELINE_A, _TEXT_B: _BASELINE_B})
        engine = _build_engine(
            tmp_path, counter_factory=_real_counter_factory(transport, counter_sleep=_noop_sleep)
        )
        await engine.start()
        await _wait_state(engine, "measured")
        status = engine.status()
        assert status["served_constant"] == pytest.approx(_COMMITTED)
        assert status["ratio_shift"] == pytest.approx(0.0)
        assert status["last_probe_at"] == _FIXED_NOW.isoformat()
        await engine.stop()

    async def test_shift_just_below_threshold_is_measured(self, tmp_path: Path) -> None:
        # live 1005 / baseline 1000 = 1.005 -> |shift| 0.005 < 0.01 -> measured.
        counts = {_TEXT_A: 402, _TEXT_B: 603}
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory(counts))
        await engine.start()
        await _wait_state(engine, "measured")
        assert engine.served_constant == pytest.approx(_COMMITTED)
        assert engine.status()["ratio_shift"] == pytest.approx(0.005)
        await engine.stop()


# --- drift (auto-adopt scaled) ------------------------------------------------


class TestDrift:
    async def test_shift_exactly_at_threshold_adopts_inclusive(self, tmp_path: Path) -> None:
        # Inject an EXACTLY-representable threshold so the boundary is unambiguous in float:
        # 750/1000 - 1 == -0.25 exactly (0.75 = 3/4 is representable), so |shift| == threshold
        # to the bit. Under >= this ADOPTS; a regression to strict > would NOT — this pins the
        # inclusive boundary the docstring promises (and keeps a scale-DOWN drift case).
        counts = {_TEXT_A: 300, _TEXT_B: 450}  # live 750
        port = _FakeFindingsPort()
        engine = _build_engine(
            tmp_path, counter_factory=_programmed_factory(counts), port=port, drift_threshold=0.25
        )
        await engine.start()
        await _wait_state(engine, "drift_adopted")
        status = engine.status()
        assert status["served_constant"] == pytest.approx(_COMMITTED * 0.75)
        assert status["ratio_shift"] == pytest.approx(-0.25)
        assert len(port.reported) == 1
        await engine.stop()

    async def test_shift_one_token_below_threshold_is_measured(self, tmp_path: Path) -> None:
        # 751/1000 - 1 ≈ -0.249 < 0.25 -> measured (NOT drift). Together with the exact-boundary
        # test this pins >= (not >): the threshold shift adopts, one token short does not.
        counts = {_TEXT_A: 300, _TEXT_B: 451}  # live 751
        engine = _build_engine(
            tmp_path, counter_factory=_programmed_factory(counts), drift_threshold=0.25
        )
        await engine.start()
        await _wait_state(engine, "measured")
        assert engine.served_constant == pytest.approx(_COMMITTED)
        await engine.stop()

    async def test_shift_above_threshold_is_drift(self, tmp_path: Path) -> None:
        # live 1011 / baseline 1000 = 1.011 -> |shift| 0.011 > 0.01 -> DRIFT.
        counts = {_TEXT_A: 405, _TEXT_B: 606}
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory(counts))
        await engine.start()
        await _wait_state(engine, "drift_adopted")
        assert engine.served_constant == pytest.approx(_COMMITTED * 1.011)
        assert engine.status()["ratio_shift"] == pytest.approx(0.011)
        await engine.stop()

    async def test_auto_adopt_arithmetic(self, tmp_path: Path) -> None:
        # live 1050 / baseline 1000 = 1.05 -> served = committed * 1.05.
        counts = {_TEXT_A: 420, _TEXT_B: 630}
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory(counts))
        await engine.start()
        await _wait_state(engine, "drift_adopted")
        assert engine.served_constant == pytest.approx(1.78 * 1.05)
        await engine.stop()


# --- drift finding: filed once, deduped ---------------------------------------


class TestDriftFinding:
    async def test_finding_filed_once_with_expected_content(self, tmp_path: Path) -> None:
        counts = {_TEXT_A: 420, _TEXT_B: 630}  # 1050 -> +5% drift
        port = _FakeFindingsPort(has_open=False)
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory(counts), port=port)
        await engine.start()
        await _wait_state(engine, "drift_adopted")
        assert port.queried_areas == ["token_calibration"]  # dedupe checked first
        assert len(port.reported) == 1
        finding = port.reported[0]
        assert finding["area"] == "token_calibration"
        assert finding["category"] == "api_drift"
        assert finding["kind"] == "drift"
        assert finding["created_by"] == "calibration-engine"
        assert _MODEL in finding["body"]
        assert str(_BASELINE_TOTAL) in finding["body"]  # baseline claude_total
        assert "1050" in finding["body"]  # live total
        assert "re-run scripts/token_survey.py" in finding["body"]
        assert finding["subject"]
        await engine.stop()

    async def test_dedupe_skips_filing_when_open_finding_exists(self, tmp_path: Path) -> None:
        counts = {_TEXT_A: 420, _TEXT_B: 630}
        port = _FakeFindingsPort(has_open=True)  # an open drift finding already exists
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory(counts), port=port)
        await engine.start()
        await _wait_state(engine, "drift_adopted")
        assert port.queried_areas == ["token_calibration"]
        assert port.reported == []  # deduped: NOT re-filed
        await engine.stop()

    async def test_second_engine_run_does_not_refile(self, tmp_path: Path) -> None:
        counts = {_TEXT_A: 420, _TEXT_B: 630}
        port = _FakeFindingsPort(has_open=False, file_flips_open=True)
        first = _build_engine(tmp_path, counter_factory=_programmed_factory(counts), port=port)
        await first.start()
        await _wait_state(first, "drift_adopted")
        await first.stop()
        assert len(port.reported) == 1  # filed on the first run

        second = _build_engine(tmp_path, counter_factory=_programmed_factory(counts), port=port)
        await second.start()
        await _wait_state(second, "drift_adopted")
        await second.stop()
        assert len(port.reported) == 1  # dedupe: still exactly one


# --- filing-failure observability (F1) ----------------------------------------


class TestFilingFailureObservability:
    """A misbehaving findings store must NOT corrupt serving, but the dropped finding must
    be OBSERVABLE: state still flips to ``drift_adopted`` and the scaled constant is served
    (serving does not depend on the store), while the failure is logged at ERROR and named
    in the ``note`` so it surfaces in :meth:`status` / ``index_status``.
    """

    async def test_report_failure_serves_scaled_and_notes_the_drop(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        counts = {_TEXT_A: 420, _TEXT_B: 630}  # 1050 -> +5% drift
        port = _FakeFindingsPort(report_raises=True)  # the store write blows up
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory(counts), port=port)
        with caplog.at_level(logging.ERROR):
            await engine.start()
            await _wait_state(engine, "drift_adopted")
        status = engine.status()
        assert status["served_constant"] == pytest.approx(_COMMITTED * 1.05)  # serving unharmed
        assert status["ratio_shift"] == pytest.approx(0.05)
        assert port.queried_areas == ["token_calibration"]  # dedupe was checked
        assert port.reported == []  # the write raised: nothing recorded
        assert "filing failed" in (status["note"] or "")  # observable in status()
        assert any(record.levelno == logging.ERROR for record in caplog.records)  # loud
        await engine.stop()

    async def test_dedupe_query_failure_serves_scaled_and_notes_the_drop(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        counts = {_TEXT_A: 420, _TEXT_B: 630}
        port = _FakeFindingsPort(has_open_raises=True)  # the dedupe query blows up
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory(counts), port=port)
        with caplog.at_level(logging.ERROR):
            await engine.start()
            await _wait_state(engine, "drift_adopted")
        status = engine.status()
        assert status["served_constant"] == pytest.approx(_COMMITTED * 1.05)  # serving unharmed
        assert port.queried_areas == ["token_calibration"]  # query was attempted
        assert port.reported == []  # filing skipped: the query never returned
        assert "filing failed" in (status["note"] or "")
        assert any(record.levelno == logging.ERROR for record in caplog.records)
        await engine.stop()


# --- integrity mismatch -------------------------------------------------------


class TestIntegrityMismatch:
    async def test_mismatch_does_not_adopt_and_names_files(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        corpus = _synthetic_corpus()
        baseline = _synthetic_baseline(corpus)
        baseline["files"]["a.py.txt"]["sha256"] = "0" * 64  # a.py.txt now MISMATCHES
        port = _FakeFindingsPort()
        # If the count path were reached it would raise (empty map) — proving it is NOT reached.
        engine = _build_engine(
            tmp_path,
            counter_factory=_programmed_factory({}),
            port=port,
            baseline=baseline,
            corpus=corpus,
        )
        with caplog.at_level(logging.ERROR):
            await engine.start()
            await _wait_state(engine, "cached")
            # Let the probe run to completion (it should stay 'cached', not adopt).
            await engine.wait_until_settled()
        status = engine.status()
        # P8d Wave 3 (finding #4): an integrity mismatch is now its OWN state —
        # indistinguishable-from-never-probed was the bug; ``cached`` no longer
        # covers this branch (fresh-boot-cached is a DIFFERENT, genuine state).
        assert status["state"] == ce.STATE_INTEGRITY_FAILED
        assert status["served_constant"] == pytest.approx(_COMMITTED)  # committed, NOT adopted
        assert port.reported == []  # a content bug is not a drift finding
        assert "a.py.txt" in (status["note"] or "")  # the mismatched file is named
        assert any(record.levelno == logging.ERROR for record in caplog.records)
        await engine.stop()


# --- endpoint-down lifecycle (real counter over MockTransport) ----------------


class TestEndpointLifecycle:
    async def test_recovers_after_transient_outage(self, tmp_path: Path) -> None:
        available = {"v": False}
        engine_delays: list[float] = []

        async def engine_sleep(delay: float) -> None:
            engine_delays.append(delay)
            available["v"] = True  # the endpoint recovers during the first backoff

        counts = {_TEXT_A: _BASELINE_A, _TEXT_B: _BASELINE_B}

        def handler(request: httpx.Request) -> httpx.Response:
            if not available["v"]:
                return httpx.Response(503, json={})
            text = json.loads(request.content)["messages"][0]["content"]
            return httpx.Response(200, json={"input_tokens": counts[text]})

        transport = httpx.MockTransport(handler)
        engine = _build_engine(
            tmp_path,
            counter_factory=_real_counter_factory(transport, counter_sleep=_noop_sleep),
            sleep=engine_sleep,
        )
        await engine.start()
        # First attempt fails -> cached_retrying; recovery flips to measured.
        await _wait_state(engine, "measured")
        assert engine_delays == [30.0]  # exactly one backoff before recovery
        assert engine.served_constant == pytest.approx(_COMMITTED)
        await engine.stop()

    async def test_first_failure_flips_to_cached_retrying(self, tmp_path: Path) -> None:
        async def engine_sleep(delay: float) -> None:
            # Park so the engine stays in cached_retrying for observation.
            await asyncio.sleep(3600)

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503, json={})

        transport = httpx.MockTransport(handler)
        engine = _build_engine(
            tmp_path,
            counter_factory=_real_counter_factory(transport, counter_sleep=_noop_sleep),
            sleep=engine_sleep,
        )
        await engine.start()
        await _wait_state(engine, "cached_retrying")
        status = engine.status()
        assert status["served_constant"] == pytest.approx(_COMMITTED)  # keeps serving current
        await engine.stop()  # cancels the task parked in backoff — clean

    async def test_backoff_doubles_and_caps(self, tmp_path: Path) -> None:
        available = {"v": False}
        engine_delays: list[float] = []

        async def engine_sleep(delay: float) -> None:
            engine_delays.append(delay)
            if len(engine_delays) >= 6:  # recover after 6 failures — enough to hit the cap
                available["v"] = True

        counts = {_TEXT_A: _BASELINE_A, _TEXT_B: _BASELINE_B}

        def handler(request: httpx.Request) -> httpx.Response:
            if not available["v"]:
                return httpx.Response(503, json={})
            text = json.loads(request.content)["messages"][0]["content"]
            return httpx.Response(200, json={"input_tokens": counts[text]})

        transport = httpx.MockTransport(handler)
        engine = _build_engine(
            tmp_path,
            counter_factory=_real_counter_factory(transport, counter_sleep=_noop_sleep),
            sleep=engine_sleep,
        )
        await engine.start()
        await _wait_state(engine, "measured")
        # 30, 60, 120, 240, 480, then capped at 900 (not 960).
        assert engine_delays == [30.0, 60.0, 120.0, 240.0, 480.0, 900.0]
        await engine.stop()

    async def test_terminal_4xx_stops_retrying_and_names_the_cause(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # A permanent 401 (bad key) cannot self-heal without a restart — the engine must NOT
        # retry it forever as a transient outage. It stops probing, keeps serving, and names
        # the cause so the operator sees it instead of an indistinguishable 'cached_retrying'.
        engine_delays: list[float] = []

        async def engine_sleep(delay: float) -> None:
            engine_delays.append(delay)

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(401, json={"error": "invalid x-api-key"})

        transport = httpx.MockTransport(handler)
        engine = _build_engine(
            tmp_path,
            counter_factory=_real_counter_factory(transport, counter_sleep=_noop_sleep),
            sleep=engine_sleep,
        )
        with caplog.at_level(logging.ERROR):
            await engine.start()
            # Bounded poll: the terminal path sets a distinctive note. Under the bug it would
            # retry forever (note = the retrying note) and this exhausts without hanging.
            note = None
            for _ in range(200):
                note = engine.status()["note"]
                if note is not None and "terminal endpoint error" in note:
                    break
                await asyncio.sleep(0)
        status = engine.status()
        assert status["state"] == "cached"
        assert status["served_constant"] == pytest.approx(_COMMITTED)  # serving intact
        assert engine_delays == []  # NOT retried as a transient outage: no backoff at all
        assert note is not None and "terminal endpoint error" in note
        assert "check the API key" in note  # actionable cause named
        assert any(record.levelno == logging.ERROR for record in caplog.records)
        await engine.stop()

    async def test_429_is_retried_not_treated_as_terminal(self, tmp_path: Path) -> None:
        # Regression pin: 429 is a 4xx but MUST stay on the retry/backoff path (it is not a
        # terminal error). The counter exhausts its own retries -> engine backs off once ->
        # the endpoint recovers -> measured.
        available = {"v": False}
        engine_delays: list[float] = []

        async def engine_sleep(delay: float) -> None:
            engine_delays.append(delay)
            available["v"] = True  # recovers during the first engine backoff

        counts = {_TEXT_A: _BASELINE_A, _TEXT_B: _BASELINE_B}

        def handler(request: httpx.Request) -> httpx.Response:
            if not available["v"]:
                return httpx.Response(429, json={})
            text = json.loads(request.content)["messages"][0]["content"]
            return httpx.Response(200, json={"input_tokens": counts[text]})

        transport = httpx.MockTransport(handler)
        engine = _build_engine(
            tmp_path,
            counter_factory=_real_counter_factory(transport, counter_sleep=_noop_sleep),
            sleep=engine_sleep,
        )
        await engine.start()
        await _wait_state(engine, "measured")
        assert engine_delays == [30.0]  # exactly one backoff (retryable), then recovery
        assert engine.served_constant == pytest.approx(_COMMITTED)
        await engine.stop()


# --- per-model cache ----------------------------------------------------------


class TestCache:
    async def test_probe_writes_cache_file(self, tmp_path: Path) -> None:
        counts = {_TEXT_A: 420, _TEXT_B: 630}  # drift +5%
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory(counts))
        await engine.start()
        await _wait_state(engine, "drift_adopted")
        await engine.stop()
        cache = _cache_path(tmp_path)
        assert cache.is_file()
        blob = json.loads(cache.read_text(encoding="utf-8"))
        assert blob["model"] == _MODEL
        assert blob["live_total"] == 1050
        assert blob["baseline_total"] == _BASELINE_TOTAL
        assert blob["ratio_shift"] == pytest.approx(0.05)
        assert blob["served_constant"] == pytest.approx(_COMMITTED * 1.05)
        assert blob["state"] == "drift_adopted"
        assert blob["probed_at"] == _FIXED_NOW.isoformat()

    async def test_serves_cache_then_reprobes(self, tmp_path: Path) -> None:
        # A prior run left a drift-adopted cache.
        cache = _cache_path(tmp_path)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cached_served = _COMMITTED * 1.20
        cache.write_text(
            json.dumps(
                {
                    "model": _MODEL,
                    "probed_at": "2026-07-01T00:00:00+00:00",
                    "live_total": 1200,
                    "baseline_total": _BASELINE_TOTAL,
                    "ratio_shift": 0.2,
                    "served_constant": cached_served,
                    "state": "drift_adopted",
                }
            ),
            encoding="utf-8",
        )
        gate = asyncio.Event()
        engine = _build_engine(
            tmp_path,
            counter_factory=_programmed_factory({_TEXT_A: _BASELINE_A, _TEXT_B: _BASELINE_B}, gate=gate),
        )
        await engine.start()
        # While the probe is frozen, the engine serves the CACHE value, state cached.
        assert engine.served_constant == pytest.approx(cached_served)
        assert engine.status()["state"] == "cached"
        gate.set()
        await _wait_state(engine, "measured")
        assert engine.served_constant == pytest.approx(_COMMITTED)  # re-probe found no drift
        await engine.stop()

    async def test_corrupt_cache_is_ignored_with_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        cache = _cache_path(tmp_path)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text("{ this is not valid json", encoding="utf-8")
        with caplog.at_level(logging.WARNING):
            engine = _build_engine(
                tmp_path,
                counter_factory=_programmed_factory({_TEXT_A: _BASELINE_A, _TEXT_B: _BASELINE_B}),
            )
            await engine.start()
            # A corrupt cache must not crash: served falls back to committed, probe proceeds.
            assert engine.served_constant == pytest.approx(_COMMITTED)
            await _wait_state(engine, "measured")
        assert any(record.levelno == logging.WARNING for record in caplog.records)
        await engine.stop()

    @pytest.mark.parametrize("bad_served", [-999.0, 0, float("nan"), float("inf")])
    async def test_cache_with_invalid_served_constant_is_ignored_with_warning(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture, bad_served: float
    ) -> None:
        # A well-formed cache JSON whose served_constant is not a finite positive float (a
        # budget multiplier that is negative/zero/NaN/inf is nonsense) must be ignored the
        # same as corrupt JSON — otherwise, with the endpoint down, the engine would serve
        # the bad multiplier indefinitely. Serve the committed constant instead.
        cache = _cache_path(tmp_path)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(
            json.dumps(
                {
                    "model": _MODEL,
                    "probed_at": "2026-07-01T00:00:00+00:00",
                    "live_total": 1200,
                    "baseline_total": _BASELINE_TOTAL,
                    "ratio_shift": 0.2,
                    "served_constant": bad_served,
                    "state": "drift_adopted",
                }
            ),
            encoding="utf-8",
        )
        gate = asyncio.Event()  # freeze the probe so the (ignored) cache posture is observable
        with caplog.at_level(logging.WARNING):
            engine = _build_engine(
                tmp_path,
                counter_factory=_programmed_factory(
                    {_TEXT_A: _BASELINE_A, _TEXT_B: _BASELINE_B}, gate=gate
                ),
            )
            await engine.start()
            # Cache ignored: the bad value is NOT adopted; the committed constant is served.
            assert engine.served_constant == pytest.approx(_COMMITTED)
            assert engine.status()["state"] == "cached"
        assert any(record.levelno == logging.WARNING for record in caplog.records)
        gate.set()
        await engine.stop()


# --- degraded / corrupt committed baseline (F6) -------------------------------


class TestDegradedBaseline:
    """A corrupt COMMITTED baseline cannot be calibrated against. The engine must degrade
    LOUDLY — serve the committed constant, log at ERROR, and name the reason in the note
    with ``last_probe_at`` set — never silently look identical to a never-probed boot.
    """

    async def test_non_positive_baseline_total_serves_committed_with_note(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        corpus = _synthetic_corpus()
        baseline = _synthetic_baseline(corpus)
        baseline["claude_total"] = 0  # corrupt: no ratio can be formed (would divide by zero)
        engine = _build_engine(
            tmp_path,
            counter_factory=_programmed_factory({_TEXT_A: _BASELINE_A, _TEXT_B: _BASELINE_B}),
            baseline=baseline,
            corpus=corpus,
        )
        with caplog.at_level(logging.ERROR):
            await engine.start()
            await engine.wait_until_settled()
        status = engine.status()
        assert status["state"] == "cached"
        assert status["served_constant"] == pytest.approx(_COMMITTED)  # no div-by-zero, safe
        assert status["ratio_shift"] is None
        assert status["last_probe_at"] == _FIXED_NOW.isoformat()  # loud: the probe RAN
        assert "non-positive" in (status["note"] or "")
        assert any(record.levelno == logging.ERROR for record in caplog.records)
        await engine.stop()

    async def test_malformed_baseline_total_none_degrades_loudly_not_silently(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        corpus = _synthetic_corpus()
        baseline = _synthetic_baseline(corpus)
        baseline["claude_total"] = None  # malformed: int(None) would raise mid-probe
        engine = _build_engine(
            tmp_path,
            counter_factory=_programmed_factory({_TEXT_A: _BASELINE_A, _TEXT_B: _BASELINE_B}),
            baseline=baseline,
            corpus=corpus,
        )
        with caplog.at_level(logging.ERROR):
            await engine.start()
            await engine.wait_until_settled()
        status = engine.status()
        assert status["state"] == "cached"
        assert status["served_constant"] == pytest.approx(_COMMITTED)  # serving intact
        # Loud, not silent: note names the fault and last_probe_at is set (vs never-probed None).
        assert status["last_probe_at"] == _FIXED_NOW.isoformat()
        assert "malformed" in (status["note"] or "")
        assert any(record.levelno == logging.ERROR for record in caplog.records)
        await engine.stop()


# --- lifecycle: stop() cancels cleanly ----------------------------------------


class TestLifecycle:
    async def test_stop_without_start_is_noop(self, tmp_path: Path) -> None:
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory({}))
        await engine.stop()  # must not raise

    async def test_stop_cancels_in_flight_probe_cleanly(self, tmp_path: Path) -> None:
        gate = asyncio.Event()  # never set -> probe parks forever in count()
        engine = _build_engine(
            tmp_path,
            counter_factory=_programmed_factory({_TEXT_A: _BASELINE_A, _TEXT_B: _BASELINE_B}, gate=gate),
        )
        await engine.start()
        await asyncio.sleep(0)  # let the probe task start and park on the gate
        await engine.stop()  # cancels the parked probe — no pending-task warning, no raise
        # Idempotent: a second stop is a no-op too.
        await engine.stop()

    async def test_stop_after_settled_is_noop(self, tmp_path: Path) -> None:
        engine = _build_engine(
            tmp_path,
            counter_factory=_programmed_factory({_TEXT_A: _BASELINE_A, _TEXT_B: _BASELINE_B}),
        )
        await engine.start()
        await _wait_state(engine, "measured")
        await engine.stop()
        await engine.stop()  # second stop after the task already finished — no-op


# --- P8d Wave 4a: caller_model read-side ratio lookup -------------------------
#
# ``cached_ratio_for_model`` is the MINIMAL read-side accessor the caller-model
# budget re-denomination plugs into (server.py's ``_count_tokens_single``). It
# must NEVER start a probe, NEVER block on the network, and NEVER mutate shared
# engine state — a pure best-effort read of a per-model cache file (the same
# ``state_dir/calibration/<model>.json`` shape ``_write_cache``/``_load_cache``
# already use for the engine's OWN yardstick model).


class TestCachedRatioForModel:
    def test_own_model_returns_the_live_served_constant(self, tmp_path: Path) -> None:
        # The engine's own yardstick model never touches disk for this lookup —
        # it is the authoritative in-process value (may differ from a stale
        # on-disk cache if a write ever failed).
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory({}))
        assert engine.cached_ratio_for_model(_MODEL) == pytest.approx(engine.served_constant)

    def test_unknown_model_with_no_cache_file_returns_none(self, tmp_path: Path) -> None:
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory({}))
        assert engine.cached_ratio_for_model("claude-haiku-4-5") is None

    def test_reads_a_valid_prior_cache_file_for_a_different_model(self, tmp_path: Path) -> None:
        other_model = "claude-opus-4-8"
        cache_dir = tmp_path / "calibration"
        cache_dir.mkdir(parents=True)
        (cache_dir / f"{other_model}.json").write_text(
            json.dumps({"served_constant": 1.4, "model": other_model}), encoding="utf-8"
        )
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory({}))
        assert engine.cached_ratio_for_model(other_model) == pytest.approx(1.4)

    def test_corrupt_cache_file_for_a_different_model_returns_none(self, tmp_path: Path) -> None:
        other_model = "claude-haiku-4-5"
        cache_dir = tmp_path / "calibration"
        cache_dir.mkdir(parents=True)
        (cache_dir / f"{other_model}.json").write_text("not json at all", encoding="utf-8")
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory({}))
        assert engine.cached_ratio_for_model(other_model) is None

    def test_non_positive_served_constant_for_a_different_model_returns_none(
        self, tmp_path: Path
    ) -> None:
        other_model = "claude-haiku-4-5"
        cache_dir = tmp_path / "calibration"
        cache_dir.mkdir(parents=True)
        (cache_dir / f"{other_model}.json").write_text(
            json.dumps({"served_constant": 0.0, "model": other_model}), encoding="utf-8"
        )
        engine = _build_engine(tmp_path, counter_factory=_programmed_factory({}))
        assert engine.cached_ratio_for_model(other_model) is None

    def test_never_starts_a_probe_or_touches_the_network(self, tmp_path: Path) -> None:
        # A counter_factory that raises if ever called proves the lookup is a
        # pure disk read — never a live measurement.
        def _forbidden_factory() -> Any:
            raise AssertionError("cached_ratio_for_model must never start a probe")

        engine = _build_engine(tmp_path, counter_factory=_forbidden_factory)
        assert engine.cached_ratio_for_model("claude-haiku-4-5") is None
