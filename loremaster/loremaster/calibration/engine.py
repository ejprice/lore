"""The boot token-calibration ENGINE — HYBRID *detect + auto-adopt-scaled*.

lore budgets are denominated in **voyage** tokens; the consumers that read those budgets
pay **Claude** tokens. The bridge is a single multiplicative constant
(``TOKEN_BUDGET_CALIBRATION``, committed at ``server.py`` and handed to this engine's
constructor). Because the Anthropic ``count_tokens`` endpoint is deterministic and
byte-identical across the current model generation, that constant can be *generation-
anchored*: measured once, committed, and trusted — UNLESS a future model generation shifts
the counts, which this engine detects at boot and adapts to without a redeploy.

The engine serves :attr:`served_constant`, the float the server multiplies budgets by:

* **Fresh boot, no cache** → serve the committed constant (state ``cached``).
* **Per-model cache from a prior run** → serve the cache's constant (state ``cached``)
  while a background probe re-measures.
* **Probe lands, |shift| < :data:`DRIFT_THRESHOLD`** → serve the committed constant
  (state ``measured``): the live generation still matches the baseline.
* **Probe lands, |shift| ≥ :data:`DRIFT_THRESHOLD`** → serve ``committed × (live/baseline)``
  (state ``drift_adopted``) AND attempt-and-await ONE deduped drift finding. Filing is
  *best-effort*: a findings-store failure (dedupe query or report) is logged at ERROR and
  surfaced in the status ``note``, never raised — serving must not depend on the store.
* **Endpoint unreachable** → keep serving the current value (state ``cached_retrying``),
  retrying forever with bounded exponential backoff (:data:`BACKOFF_START_S` →
  :data:`BACKOFF_CAP_S`). Boot NEVER blocks on the probe; the probe NEVER crashes the box.

Drift is judged on the AGGREGATE token-weighted totals (``live_total`` vs the baseline's
``claude_total``), never per-file ratios — those legitimately vary ~1.6–2.2 by content
shape. An *integrity* mismatch (the shipped corpus no longer hashes to the baseline) is a
packaging/content bug, NOT token drift: the engine logs it, serves the committed constant,
adopts NOTHING, files no finding, and flips to its OWN state (:data:`STATE_INTEGRITY_FAILED`,
P8d Wave 3) — distinguishable from fresh-boot ``cached`` by ``state`` alone.

The drift finding is filed with ``kind="drift"`` — the finding ``kind`` field is FREE-FORM
(a ``TYPE string`` + trim-aware non-empty ``ASSERT``, not a closed-domain enum; only
``status`` is closed-domain), so a purpose-named ``"drift"`` kind is valid and clearer than
the generic ``"friction"`` default (receipt:
``loremaster/tests/test_surreal_schema.py::test_kind_is_a_required_non_empty_string``).

Thread-safety: the served-state bundle (constant, state, ratio, timestamp, note) is guarded
by a :class:`threading.Lock`, so a synchronous server thread reading :attr:`served_constant`
or :meth:`status` always sees a consistent snapshot even as the async probe updates it.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import math
import threading
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import httpx

from loremaster.calibration.baseline import (
    IntegrityResult,
    load_baseline,
    load_corpus,
    verify_corpus_integrity,
)
from loremaster.calibration.counting import (
    AsyncClaudeTokenCounter,
    AsyncSleep,
    TerminalCountError,
)
from loresigil import backoff

logger = logging.getLogger(__name__)

# --- serving states (the closed set the index_status render consumes) ---------
STATE_CACHED: str = "cached"
STATE_MEASURED: str = "measured"
STATE_DRIFT_ADOPTED: str = "drift_adopted"
STATE_CACHED_RETRYING: str = "cached_retrying"
#: P8d Wave 3 (finding #4): an integrity mismatch (the shipped corpus no longer
#: hashes to the baseline) is its OWN terminal state — distinct from fresh-boot
#: ``cached``. Before this, ``_handle_integrity_failure`` served ``cached`` with
#: only a distinguishing ``note``, making an integrity mismatch indistinguishable
#: from "never probed yet" by ``state`` alone.
STATE_INTEGRITY_FAILED: str = "integrity_failed"

#: Aggregate token-weighted shift, ``|live_total / baseline_total − 1|``, at or above which
#: the live generation is treated as DRIFTED and the scaled constant is adopted. The
#: boundary is inclusive (``>=``): an exact 0.01 shift is drift.
DRIFT_THRESHOLD: float = 0.01

#: Bounded exponential backoff for the endpoint-unreachable retry: start at 30s, double
#: each failure, cap at 900s (15 min). Retries forever — a transient outage must never
#: permanently pin the served value to a stale cache, and a never-ending outage must never
#: spin hot or crash the container.
BACKOFF_START_S: float = 30.0
BACKOFF_CAP_S: float = 900.0

# --- drift-finding coordinates (see the module docstring for the kind rationale) ---
CALIBRATION_AREA: str = "token_calibration"
DRIFT_CATEGORY: str = "api_drift"
DRIFT_KIND: str = "drift"
DRIFT_CREATED_BY: str = "calibration-engine"

_UTF8: str = "utf-8"


class _ProbeUnavailableError(RuntimeError):
    """The probe could not reach / complete the token count — a retryable condition.

    Raised by the count phase when the endpoint is unreachable or keeps failing (the
    underlying :class:`AsyncClaudeTokenCounter` has already exhausted its own short retry
    budget). The probe loop catches THIS type to drive its bounded-backoff retry, and only
    this type — an unexpected programming error is never mistaken for an outage.
    """


@runtime_checkable
class FindingsPort(Protocol):
    """The narrow findings seam the engine files drift through (impl by a wiring agent).

    Two async methods: a dedupe query and a report. ``has_open_drift_finding`` must count a
    finding in status *open* OR *acknowledged* as still-live (an acknowledged-but-unresolved
    drift must not be re-filed on the next boot).
    """

    async def has_open_drift_finding(self, area: str) -> bool: ...

    async def report_drift_finding(
        self,
        *,
        subject: str,
        body: str,
        area: str,
        category: str,
        kind: str,
        created_by: str,
    ) -> None: ...


class _TokenCounter(Protocol):
    """The counter surface the engine uses — satisfied by :class:`AsyncClaudeTokenCounter`."""

    async def count(self, text: str) -> int: ...

    async def aclose(self) -> None: ...


CounterFactory = Callable[[], _TokenCounter]
Clock = Callable[[], datetime]


class CalibrationEngine:
    """Serve a boot-calibrated budget-scaling constant; adapt to token-generation drift.

    See the module docstring for the serving contract. Construct it, :meth:`start` it (the
    probe runs in the background — boot does not block), read :attr:`served_constant` /
    :meth:`status`, and :meth:`stop` it on shutdown (cancels the probe cleanly).
    """

    def __init__(
        self,
        *,
        committed_constant: float,
        model: str,
        api_key: str,
        state_dir: Path,
        findings_port: FindingsPort,
        baseline: Mapping[str, Any] | None = None,
        corpus: Mapping[str, bytes] | None = None,
        counter_factory: CounterFactory | None = None,
        clock: Clock | None = None,
        sleep: AsyncSleep | None = None,
        drift_threshold: float = DRIFT_THRESHOLD,
        backoff_start_s: float = BACKOFF_START_S,
        backoff_cap_s: float = BACKOFF_CAP_S,
    ) -> None:
        self._committed = float(committed_constant)
        self._model = model
        self._api_key = api_key
        self._state_dir = Path(state_dir)
        self._findings_port = findings_port
        self._baseline: dict[str, Any] = dict(baseline) if baseline is not None else load_baseline()
        self._corpus: dict[str, bytes] = dict(corpus) if corpus is not None else load_corpus()
        self._counter_factory: CounterFactory = counter_factory or self._default_counter_factory
        self._clock: Clock = clock or (lambda: datetime.now(UTC))
        self._sleep: AsyncSleep = sleep or asyncio.sleep
        self._drift_threshold = drift_threshold
        self._backoff_start_s = backoff_start_s
        self._backoff_cap_s = backoff_cap_s

        self._baseline_generated_at: str | None = self._baseline.get("generated_at")
        self._cache_path = self._state_dir / "calibration" / f"{self._model}.json"

        # The served-state bundle, guarded for cross-thread reads. Fresh-boot default:
        # serve the committed constant, state ``cached``, nothing measured yet.
        self._lock = threading.Lock()
        self._served_constant: float = self._committed
        self._state: str = STATE_CACHED
        self._ratio_shift: float | None = None
        self._last_probe_at: str | None = None
        self._note: str | None = None

        self._probe_task: asyncio.Task[None] | None = None

    # --- public surface -------------------------------------------------------

    @property
    def served_constant(self) -> float:
        """The float the server multiplies budgets by, as a consistent snapshot."""
        with self._lock:
            return self._served_constant

    def cached_ratio_for_model(self, model: str) -> float | None:
        """Read-only per-model ratio lookup (P8d Wave 4a caller-model seam).

        NEVER starts a probe, NEVER touches the network, NEVER blocks the read
        path, and NEVER mutates shared engine state — a pure best-effort read,
        safe to call from a concurrent request handler.

        ``model`` equal to THIS engine's own yardstick model returns the live,
        lock-guarded :attr:`served_constant` (the authoritative in-process
        value — it may be fresher than whatever last landed on disk). Any
        OTHER model name is looked up in a prior probe's on-disk cache file at
        ``state_dir/calibration/<model>.json`` (the SAME shape
        :meth:`_write_cache` writes for this engine's own model — a fleet of
        per-model boots each drop their own file there over time). A missing
        file, unreadable/corrupt JSON, or a served value that is not a finite
        positive float is treated as "no cached ratio" rather than an error.

        Args:
            model: The caller-supplied model name to look up a ratio for.

        Returns:
            The cached (or live) multiplicative ratio, or ``None`` when no
            valid cached ratio exists for ``model`` — the caller falls back to
            the generation constant and renders an honest note.
        """
        if model == self._model:
            return self.served_constant
        path = self._state_dir / "calibration" / f"{model}.json"
        if not path.is_file():
            return None
        try:
            blob = json.loads(path.read_text(encoding=_UTF8))
            served = float(blob["served_constant"])
        except (OSError, ValueError, TypeError, KeyError):
            return None
        if not math.isfinite(served) or served <= 0:
            return None
        return served

    def status(self) -> dict[str, Any]:
        """A snapshot dict for the ``index_status`` render (consumed by a later agent)."""
        with self._lock:
            return {
                "state": self._state,
                "served_constant": self._served_constant,
                "committed_constant": self._committed,
                "model": self._model,
                "ratio_shift": self._ratio_shift,
                "last_probe_at": self._last_probe_at,
                "baseline_generated_at": self._baseline_generated_at,
                "note": self._note,
            }

    async def start(self) -> None:
        """Adopt any prior-run cache, then schedule the probe as a background task.

        Idempotent: a second call while a probe is live is a no-op. Boot NEVER blocks on
        the probe — the heavy token counting runs entirely in the scheduled task.
        """
        if self._probe_task is not None:
            return
        self._adopt_cache_if_present()
        self._probe_task = asyncio.create_task(
            self._probe_loop(), name=f"calibration-probe-{self._model}"
        )

    async def stop(self) -> None:
        """Cancel the probe task cleanly (no pending-task warning). Idempotent."""
        task = self._probe_task
        self._probe_task = None
        if task is None:
            return
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

    async def wait_until_settled(self) -> None:
        """Await the probe task's completion (returns at once if it already terminated).

        For a probe that terminates (measured / drift / integrity mismatch). A probe stuck
        retrying an unreachable endpoint never settles — do not await it without a timeout.
        """
        task = self._probe_task
        if task is not None:
            with contextlib.suppress(asyncio.CancelledError):
                await task

    # --- probe orchestration --------------------------------------------------

    def _backoff_delay(self, attempt: int) -> float:
        """Draw this probe's reconnect delay from the SHARED full-jitter policy.

        A named seam rather than an expression inline in :meth:`_probe_loop`, mirroring
        :meth:`loremaster.scout.CommandSubscriber._backoff`: it is what lets the
        one-implementation invariant DRIVE this call site directly and prove it shares the
        policy (``loremaster/tests/test_backoff_seam.py``). A backoff buried inside a loop
        body can only be reached through the loop's whole harness, and a site a pin cannot
        drive is a site nothing certifies.

        Finding #207: this used to be ``min(start * 2**attempt, cap)`` — a pure function of
        ``attempt``. Every lore container calibrating against the same endpoint enters this
        loop on the same outage, so a deterministic ladder marched all of them back in step,
        forever. The delay is now DRAWN, so they decorrelate.

        Args:
            attempt: The zero-based index of the probe attempt that just failed.

        Returns:
            A delay in seconds from ``[0, min(backoff_cap_s, backoff_start_s * 2**attempt))``.
        """
        return backoff.jittered_backoff_delay(
            attempt, base_s=self._backoff_start_s, cap_s=self._backoff_cap_s
        )

    async def _probe_loop(self) -> None:
        """Run the probe, retrying an unreachable endpoint with bounded backoff, forever.

        A single successful landing (measured / drift), an integrity mismatch, OR a permanent
        endpoint error (:class:`TerminalCountError`) is terminal — the loop returns. Only a
        :class:`_ProbeUnavailableError` drives a retry. Any other exception is logged and
        swallowed so the background task never crashes the container.
        """
        attempt = 0
        try:
            while True:
                try:
                    await self._run_probe_once()
                except TerminalCountError as exc:
                    # Permanent, non-retryable (bad key / 4xx): stop probing — retrying cannot
                    # heal it without a process restart. Keep serving; name the cause.
                    self._handle_terminal_endpoint_error(exc)
                    return
                except _ProbeUnavailableError as exc:
                    self._enter_retrying(attempt, exc)
                    await self._sleep(self._backoff_delay(attempt))
                    attempt += 1
                    continue
                return  # terminal: measured / drift_adopted / integrity mismatch
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 — the probe must never crash the container
            logger.error("calibration probe loop crashed unexpectedly", exc_info=True)

    async def _run_probe_once(self) -> None:
        """One probe attempt: integrity FIRST, then count + compare.

        Raises:
            TerminalCountError: A permanent, non-retryable endpoint error (bad key / 4xx).
            _ProbeUnavailableError: The endpoint could not be reached / completed (retryable).
        """
        integrity = verify_corpus_integrity(self._baseline, self._corpus)
        if not integrity.ok:
            self._handle_integrity_failure(integrity)
            return
        live_total = await self._count_live_total()
        await self._apply_measurement(live_total)

    async def _count_live_total(self) -> int:
        """Count every corpus file (mirroring the baseline generator) and sum.

        Uses a FRESH counter per attempt so a dead client from a prior outage is replaced —
        a per-file decode+count+sum in sorted order, IDENTICAL to
        ``scripts/calibration_baseline.py``, so the live total is comparable to the
        baseline's ``claude_total``.

        Raises:
            TerminalCountError: A permanent, non-retryable endpoint error (bad key / 4xx) —
                propagated UNWRAPPED so the loop can stop instead of retrying it forever.
            _ProbeUnavailableError: The endpoint was unreachable / kept failing (retryable).
        """
        counter = self._counter_factory()
        try:
            total = 0
            for name in sorted(self._corpus):
                text = self._corpus[name].decode(_UTF8)
                total += await counter.count(text)
            return total
        except TerminalCountError:
            # A permanent 4xx (bad key / 400): do NOT collapse it into the retryable path —
            # let it propagate so the loop disables the probe instead of spinning forever.
            raise
        except (RuntimeError, httpx.HTTPError, OSError) as exc:
            raise _ProbeUnavailableError(str(exc)) from exc
        finally:
            with contextlib.suppress(Exception):
                await counter.aclose()

    # --- outcomes -------------------------------------------------------------

    async def _apply_measurement(self, live_total: int) -> None:
        """Compare the live total to the baseline and adopt measured / drifted serving.

        The drift path orders its side effects so that OBSERVING ``drift_adopted`` implies
        the filing step has *run*: write the cache, ATTEMPT-and-AWAIT the (deduped) drift
        finding as best-effort, THEN flip the served value + state atomically as the LAST
        step — there is no window where a reader sees ``drift_adopted`` before the scaled
        constant is served or before filing was attempted. Filing is best-effort: a
        findings-store failure is logged at ERROR and named in the ``note`` (observable in
        :meth:`status`), never raised — serving must not depend on the store being healthy.

        A corrupt COMMITTED baseline (``claude_total`` missing / non-numeric / non-positive)
        cannot be calibrated against: the engine degrades LOUDLY — serves the committed
        constant, logs at ERROR, and names the fault in the note — never silently.
        """
        now_iso = self._clock().isoformat()
        raw_total = self._baseline.get("claude_total")
        try:
            baseline_total = int(raw_total)  # type: ignore[arg-type]  # None/str -> caught below
        except (TypeError, ValueError):
            # A missing / non-numeric committed claude_total is a corrupt baseline, not token
            # drift: name it loudly rather than let int(None) crash the probe silently.
            logger.error(
                "calibration baseline claude_total is malformed (%r); serving committed", raw_total
            )
            self._set_state(
                served=self._committed,
                state=STATE_CACHED,
                ratio_shift=None,
                last_probe_at=now_iso,
                note=f"baseline claude_total malformed ({raw_total!r}); serving committed (cannot calibrate)",
            )
            return
        if baseline_total <= 0:
            # A non-positive baseline total is a corrupt baseline, not token drift: cannot
            # form a ratio, so serve committed and say so rather than divide by zero.
            logger.error("calibration baseline claude_total is non-positive; serving committed")
            self._set_state(
                served=self._committed,
                state=STATE_CACHED,
                ratio_shift=None,
                last_probe_at=now_iso,
                note="baseline claude_total non-positive; serving committed (cannot calibrate)",
            )
            return

        ratio = live_total / baseline_total
        ratio_shift = ratio - 1.0
        if abs(ratio_shift) >= self._drift_threshold:
            served = self._committed * ratio
            note = f"adopted scaled constant: live/baseline shift {ratio_shift * 100:+.2f}%"
            self._write_cache(live_total, baseline_total, ratio_shift, served, STATE_DRIFT_ADOPTED, now_iso)
            filing_error = await self._file_drift_finding_deduped(
                live_total, baseline_total, ratio_shift, served
            )
            if filing_error is not None:
                note = f"{note}; {filing_error}"
            self._set_state(
                served=served,
                state=STATE_DRIFT_ADOPTED,
                ratio_shift=ratio_shift,
                last_probe_at=now_iso,
                note=note,
            )
        else:
            self._write_cache(
                live_total, baseline_total, ratio_shift, self._committed, STATE_MEASURED, now_iso
            )
            self._set_state(
                served=self._committed,
                state=STATE_MEASURED,
                ratio_shift=ratio_shift,
                last_probe_at=now_iso,
                note=None,
            )

    def _handle_integrity_failure(self, integrity: IntegrityResult) -> None:
        """Serve the committed constant, adopt nothing, and name the offending files.

        An integrity mismatch means the shipped corpus no longer matches the baseline's
        hashes — a packaging/content bug, not token drift. It is TERMINAL (retrying cannot
        heal a content mismatch) and files no drift finding. State flips to
        :data:`STATE_INTEGRITY_FAILED` (P8d Wave 3, finding #4) — NOT :data:`STATE_CACHED` —
        so this branch is distinguishable from "never probed yet" by ``state`` alone; the
        ``note`` remains the human-readable detail, the state carries the machine-readable fact.
        """
        offenders = sorted({*integrity.mismatched, *integrity.missing, *integrity.unexpected})
        names = ", ".join(offenders)
        logger.error(
            "calibration corpus integrity mismatch; serving committed and NOT adopting",
            extra={
                "mismatched": list(integrity.mismatched),
                "missing": list(integrity.missing),
                "unexpected": list(integrity.unexpected),
            },
        )
        self._set_state(
            served=self._committed,
            state=STATE_INTEGRITY_FAILED,
            ratio_shift=None,
            last_probe_at=self._clock().isoformat(),
            note=f"corpus integrity mismatch ({names}); serving committed constant, NOT adopting",
        )

    def _enter_retrying(self, attempt: int, exc: BaseException) -> None:
        """Flip to ``cached_retrying`` (keeping the served value) and log without spam."""
        self._set_retrying(
            "probe endpoint unreachable; retrying with backoff (serving last-known constant)"
        )
        if attempt == 0:
            logger.warning("calibration probe endpoint unreachable; retrying", exc_info=exc)
        else:
            logger.debug("calibration probe still unreachable; retrying", exc_info=exc)

    def _handle_terminal_endpoint_error(self, exc: BaseException) -> None:
        """A permanent, non-retryable endpoint error (bad key / 4xx): stop, keep serving.

        The API key is resolved once at boot, so a 401/400 cannot self-heal without a process
        restart — retrying would spin on backoff forever, indistinguishable from a transient
        outage. Keep serving the current value (safe), flip to ``cached`` (terminal), and NAME
        the cause so the operator sees an actionable message in :meth:`status` / ``index_status``.
        """
        logger.error(
            "calibration probe hit a terminal endpoint error; probe disabled until restart",
            exc_info=exc,
        )
        self._set_terminal(
            f"terminal endpoint error ({exc}): probe disabled until restart — check the API key"
        )

    # --- drift finding --------------------------------------------------------

    async def _file_drift_finding_deduped(
        self, live_total: int, baseline_total: int, ratio_shift: float, served: float
    ) -> str | None:
        """File ONE drift finding unless an open/acknowledged one already exists (dedupe).

        Attempted-and-awaited best-effort: a findings-store failure (the dedupe query OR the
        report) is logged at ERROR and returned as a human-readable note so the dropped
        finding is OBSERVABLE in :meth:`status`, never raised — a missed finding must not
        crash the boot probe or block serving the scaled constant.

        Returns:
            ``None`` when filing succeeded (or was correctly deduped); otherwise a short note
            naming the failure, for the caller to fold into the status ``note``.
        """
        try:
            await self._report_drift(live_total, baseline_total, ratio_shift, served)
            return None
        except Exception as exc:  # noqa: BLE001 — filing is best-effort; never crash the probe
            logger.error("calibration drift finding could not be filed", exc_info=True)
            return f"drift finding filing failed: {exc}"

    async def _report_drift(
        self, live_total: int, baseline_total: int, ratio_shift: float, served: float
    ) -> None:
        """File ONE drift finding unless an open/acknowledged one already exists (dedupe)."""
        if await self._findings_port.has_open_drift_finding(CALIBRATION_AREA):
            return
        pct = ratio_shift * 100
        subject = (
            f"token calibration drift: {self._model} live count shifted {pct:+.2f}% from baseline"
        )
        body = (
            f"model={self._model}\n"
            f"baseline claude_total={baseline_total}\n"
            f"live total={live_total}\n"
            f"shift={pct:+.2f}%\n"
            f"served (scaled) constant={served}\n"
            "remediation: re-run scripts/token_survey.py + scripts/calibration_baseline.py, "
            "commit the new baseline + constant"
        )
        await self._findings_port.report_drift_finding(
            subject=subject,
            body=body,
            area=CALIBRATION_AREA,
            category=DRIFT_CATEGORY,
            kind=DRIFT_KIND,
            created_by=DRIFT_CREATED_BY,
        )

    # --- cache ----------------------------------------------------------------

    def _adopt_cache_if_present(self) -> None:
        """Serve a prior-run cache's constant while the fresh probe re-measures."""
        cached = self._load_cache()
        if cached is None:
            return
        served, ratio_shift, probed_at = cached
        self._set_state(
            served=served,
            state=STATE_CACHED,
            ratio_shift=ratio_shift,
            last_probe_at=probed_at,
            note="serving cached constant from a prior run pending re-probe",
        )

    def _load_cache(self) -> tuple[float, float | None, str | None] | None:
        """Read the per-model cache, or ``None`` (missing, or corrupt with a WARNING).

        The cached ``served_constant`` is the multiplier the server applies to every budget,
        so a value that is not a finite float > 0 (negative / zero / NaN / inf) is nonsense —
        it is rejected exactly like corrupt JSON (WARNING + ignore), rather than served as a
        budget multiplier indefinitely while the endpoint is unreachable.
        """
        if not self._cache_path.is_file():
            return None
        try:
            blob = json.loads(self._cache_path.read_text(encoding=_UTF8))
            served = float(blob["served_constant"])
            if not math.isfinite(served) or served <= 0:
                raise ValueError(f"served_constant not a finite positive float: {served!r}")
            ratio_shift = blob.get("ratio_shift")
            ratio_shift = None if ratio_shift is None else float(ratio_shift)
            probed_at = blob.get("probed_at")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            logger.warning("calibration cache unreadable; ignoring", exc_info=exc)
            return None
        return served, ratio_shift, probed_at

    def _write_cache(
        self,
        live_total: int,
        baseline_total: int,
        ratio_shift: float,
        served: float,
        state: str,
        probed_at_iso: str,
    ) -> None:
        """Persist the probe result to ``state_dir/calibration/<model>.json`` (best-effort).

        Plain JSON with an ISO datetime STRING (the SurrealDB datetime-object idiom does not
        apply to a JSON file). A write failure is logged, never raised — a durable cache is
        an optimisation, not a correctness requirement.
        """
        payload = {
            "model": self._model,
            "probed_at": probed_at_iso,
            "live_total": live_total,
            "baseline_total": baseline_total,
            "ratio_shift": ratio_shift,
            "served_constant": served,
            "state": state,
        }
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._cache_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding=_UTF8
            )
        except OSError as exc:
            logger.warning("calibration cache could not be written; continuing", exc_info=exc)

    # --- guarded state mutation ----------------------------------------------

    def _set_state(
        self,
        *,
        served: float,
        state: str,
        ratio_shift: float | None,
        last_probe_at: str | None,
        note: str | None,
    ) -> None:
        with self._lock:
            self._served_constant = served
            self._state = state
            self._ratio_shift = ratio_shift
            self._last_probe_at = last_probe_at
            self._note = note

    def _set_retrying(self, note: str) -> None:
        """Flip to ``cached_retrying`` WITHOUT disturbing the served value / last probe."""
        with self._lock:
            self._state = STATE_CACHED_RETRYING
            self._note = note

    def _set_terminal(self, note: str) -> None:
        """Flip to ``cached`` (terminal, probe disabled) WITHOUT disturbing the served value."""
        with self._lock:
            self._state = STATE_CACHED
            self._note = note

    def _default_counter_factory(self) -> _TokenCounter:
        return AsyncClaudeTokenCounter(self._api_key, model=self._model)
