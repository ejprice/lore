"""THE INVARIANT for finding #207 — one backoff policy, provably shared, with a perimeter.

This class of defect has now been audit-caught THREE times — #102 (a 16-slot jitter derived
from the contended row's id), #108 (a 4-slot table cloned into a sibling), #207 (five
implementations, none jittered) — and until this file existed it had **no invariant to show
for it**. Fixing N call sites without a pin guarantees an N+1th; that is the whole lesson.

Two instruments, because one is not enough and this repo has the receipts to prove it:

**1. SHARING, proven by MUTATION with CHECKED COVERAGE.**
   ``TestEveryBackoffSharesTheOnePolicy`` mutates the shared policy to a sentinel and drives
   every known call site, asserting each one slept the sentinel. A site that kept a private
   copy still backs off, still retries, still passes every "does it work?" test — and sleeps
   its own value here. That is the only test that distinguishes DRY from looks-DRY
   (``CLAUDE.md``: *"ROUTING IS NOT SHARING"*).

   Coverage is a CHECKED VARIABLE, not a hope: the observed site set must EQUAL the declared
   site set. A guard is an invariant only over code it actually RUNS, so a site nobody drives
   is a site this file certifies NOTHING about — that is exactly how this repo's fifth
   instrument was defeated (``test_retry_seam.py``, finding #120).

**2. THE PERIMETER, allowlisting the SAFE.**
   ``TestNoNewHandRolledBackoff`` AST-scans production source for exponentiation by a variable
   and denies it everywhere except one evidence-backed file. This is deliberately NOT a scan
   for forbidden shapes: ``CLAUDE.md``'s six-defeat table records that every instrument keyed
   on what is FORBIDDEN was defeated by the next name (a label's literal, a symbol's name,
   ``async def _query``, 3 SDK method names, 2 receiver names, 4 arming tests). The forbidden
   set is unbounded; the safe set here is **one file**, enumerable and small.

   Measured 2026-07-25 at the #207 fix: pre-fix the scan returned **6** hits — the five
   defects plus the fenced ``_txn`` seam — with **zero false positives** across every
   workspace member plus ``scripts/`` and ``skills/``. No legitimate arithmetic anywhere in
   production raises anything to a variable power. That is what makes deny-by-default
   affordable here rather than an insult that gets switched off.

   ⚠ That sentence used to NAME three members, and the scan used to hold its own list of
   them. Both went stale when ``lorerunes`` was minted (lore **#251**). The trees are now
   parsed by the SHARED ``_logging_fixtures.parse_production_trees`` (F4 / #279) — and this
   prose is count-free and member-free on purpose, so it cannot go stale again.

**THE THREAT MODEL, stated IN the instrument** (``CLAUDE.md``: *a gate needs one written down,
or every auditor is entitled to call a clever evasion a defect*): these pins catch the HONEST
ENGINEER who adds a retry loop and hand-writes its delay — the #207 defect verbatim, five
times over. They are NOT a boundary against someone determined to evade them. Therefore
*"a contributor could write ``delay *= 2`` in a loop and slip past"* is **not** a defect in
this file; *"an engineer added a backoff and nothing noticed"* **is**. See the KNOWN BOUND
pinned at the bottom.
"""

from __future__ import annotations

import ast
import asyncio
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest
from _logging_fixtures import parse_production_trees
from loremaster.calibration import counting
from loremaster.calibration import engine as ce
from loremaster.scout import CommandSubscriber
from loresigil.resilient import ResilientEmbedder
from loresigil.tokens import VoyageTokenCounter
from pydantic import SecretStr

from loremaster import server
from loresigil import backoff as backoff_module
from loresigil import resilient as resilient_module

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import token_survey as ts  # type: ignore[import-not-found]  # noqa: E402

#: The sentinel the mutated EXPONENTIAL policy returns. Deliberately absurd — no window in
#: the tree could produce it by chance, so "the site slept this" cannot be a coincidence.
_SENTINEL_DELAY = 1234.5

#: A DISTINCT sentinel for the mutated ADDITIVE policy. Two values rather than one so a
#: site cannot pass by calling the wrong policy: an exponential draw where an additive one
#: belongs would still decorrelate, still look jittered, and still be WRONG — on a
#: ``Retry-After`` it would return values BELOW the server's floor. Only distinct sentinels
#: can tell "jittered" from "jittered the right way".
_SENTINEL_ADDITIVE = 4321.5

#: Every production call site of the shared backoff module — BOTH policies: the full-jitter
#: exponential draw (#207) and the additive jitter (#207 D2/D3). Declared here so coverage is
#: a CHECKED variable: :func:`test_EVERY_declared_site_draws_from_the_mutated_policy` fails if
#: a site is declared but never driven, and the perimeter scan below fails if a new
#: hand-rolled backoff appears. Adding another backoff means adding it to BOTH.
#:
#: ⚠⚠ **DO NOT NARROW THIS SET TO "loremaster ONLY".** It reaches across package and gate
#: boundaries deliberately, and for one entry that is not tidiness — it is the only thing
#: standing between a production backoff and zero coverage of any kind.
#:
#: ``token_survey.ClaudeTokenCounter._sleep_backoff`` lives in ``scripts/``, where THREE
#: independently-reasonable decisions intersect:
#:   1. ``scripts/`` **used to be** excluded from ``testpaths``, so its collectable test
#:      nodes had never run in any gate (finding **#199**; measured 2026-07-25 —
#:      ``uv run pytest scripts/ --collect-only -q`` → 150, versus ``0`` collected by a bare
#:      gated run). ⚠ **DISCHARGED 2026-07-25 by #199** — ``scripts`` is in ``testpaths``,
#:      and re-measured 2026-07-29 in packet 44 BOTH figures have moved: 352 collectable
#:      nodes, and a bare gated run now collects all 352, not 0. **This premise no longer
#:      holds, and the conclusion below does not depend on it** — reason 2 alone is
#:      sufficient, which is why the ⚠⚠ warning above still stands;
#:   2. ``scripts/test_token_survey.py`` does not cover ``ClaudeTokenCounter`` **at all** —
#:      by design, not oversight: that module's own docstring declares the live counting
#:      client *"intentionally test-exempt"* as its only network surface;
#:   3. therefore the driver in THIS file is not merely the only *gated* coverage of that
#:      backoff site — it is the only coverage **that exists anywhere, of any kind**.
#:
#: No one of those three decisions is wrong. The hole is what they produce jointly, and
#: nobody owns an intersection. Measured consequence in this same wave: a ``scripts/`` defect
#: with no equivalent pin reached the branch tip **100% broken with every gate green** (the
#: cold audit's defect A). If you are here to tidy a cross-package test away, this comment is
#: the reason not to.
_DECLARED_SITES = frozenset(
    {
        # --- full-jitter exponential sites (#207) ---
        "loresigil.resilient.compute_backoff_delay",
        "loremaster.calibration.counting.AsyncClaudeTokenCounter._sleep_backoff",
        "loremaster.calibration.engine.CalibrationEngine._probe_loop",
        "loremaster.scout.CommandSubscriber._backoff",
        "token_survey.ClaudeTokenCounter._sleep_backoff",
        # --- additive-jitter sites (#207 D2/D3), declared at birth, not retrofitted ---
        "loremaster.calibration.counting.AsyncClaudeTokenCounter._sleep_backoff.retry_after",
        "token_survey.ClaudeTokenCounter._sleep_backoff.retry_after",
        "loremaster.server._eager_build_with_retry",
    }
)

# --- the perimeter's evidence-backed allowlist -------------------------------------------
#: The ONE production file permitted to raise a value to a VARIABLE power.
#:
#: ``_txn.py::_txn_conflict_backoff_seconds`` is the transaction-conflict seam's own
#: full-jitter policy. It is exempt on EVIDENCE, not opinion: it already draws
#: ``random.uniform(0, window)`` (the same Full Jitter this module's policy uses), it is
#: mutation-proven across eleven consumers by ``test_retry_seam.py``, its distribution is
#: pinned by ``test_surreal_store.py::TestTxnConflictBackoffIsJittered``, and finding #202
#: deliberately fenced it from being churned.
#:
#: RE-OPEN TRIGGER: the day either jitter formula changes, these two implementations of one
#: policy get consolidated (raised as R4 in ``REPORT-fix-207-jitter.md``, archived under
#: ``docs/plans/v2/receipts/``). Until then this is a KNOWN, DELIBERATE second copy.
_POW_ALLOWLIST = frozenset({"loremaster/loremaster/store/_txn.py"})

#: The subscriber window the drivers construct with. Deliberately NOT scout's production
#: defaults: a fixture reusing the module constant cannot tell "the site forwards MY
#: parameters" from "the site ignores them and happens to agree with the default".
_SCOUT_BASE_S = 0.25
_SCOUT_CAP_S = 12.0

#: Likewise for the eager-lease driver — NOT ``_DEFAULT_EAGER_BACKOFF_BASE_S``.
_EAGER_BASE_S = 3.5

class _PolicyMutation:
    """Replaces the shared policy with a sentinel and records which sites drew from it.

    The instrument for pin 1. Returning a SENTINEL rather than delegating is the point: a
    site that shares the policy sleeps 1234.5; a site with a private copy sleeps whatever
    its own arithmetic produced. Nothing else can tell those apart.
    """

    def __init__(self) -> None:
        self.draws: list[tuple[int, float, float]] = []
        self.additive_draws: list[tuple[float, float]] = []

    def __call__(self, attempt: int, *, base_s: float, cap_s: float) -> float:
        self.draws.append((attempt, base_s, cap_s))
        return _SENTINEL_DELAY

    def additive(self, base_s: float, *, width_s: float = backoff_module.ADDITIVE_JITTER_WIDTH_S) -> float:
        self.additive_draws.append((base_s, width_s))
        return _SENTINEL_ADDITIVE


def _apply_mutation(monkeypatch: pytest.MonkeyPatch) -> _PolicyMutation:
    """Replace BOTH shared policies with recording sentinels."""
    for name in ("jittered_backoff_delay", "additive_jitter"):
        assert hasattr(backoff_module, name), (
            f"the shared policy's named function {name!r} is gone. It must survive under "
            f"this exact name: identity is the only way a pin can tell 'shares the policy' "
            f"from 'hand-rolled one that looks like it'."
        )
    mutation = _PolicyMutation()
    monkeypatch.setattr(backoff_module, "jittered_backoff_delay", mutation)
    monkeypatch.setattr(backoff_module, "additive_jitter", mutation.additive)
    return mutation


@pytest.fixture
def mutated_policy(monkeypatch: pytest.MonkeyPatch) -> _PolicyMutation:
    """Mutate BOTH shared policies. Every genuine caller must change with them."""
    return _apply_mutation(monkeypatch)


def _status_error(status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "http://embedder.test/embed")
    response = httpx.Response(status_code, request=request, text="error body")
    return httpx.HTTPStatusError("err", request=request, response=response)


# --------------------------------------------------------------------------------------
# ONE driver per call site, shared by the per-site pins AND the set-coverage pin below.
#
# Written once rather than twice on purpose: duplicating a driver is how the two pins
# drift until they are testing different things while appearing to agree — the same
# defect class (#207/#102) this whole file exists to instrument, reproduced in the
# instrument. Each driver returns the delays the site actually slept.
# --------------------------------------------------------------------------------------


async def _drive_resilient_embedder() -> list[float]:
    """Site 1: one 429 then success -> exactly one backoff through the shared policy."""
    delays: list[float] = []
    calls = 0

    async def request_fn(texts: list[str]) -> list[list[float]]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise _status_error(429)
        return [[0.1] * 8 for _ in texts]

    async def sleep_fn(delay: float) -> None:
        delays.append(delay)

    await ResilientEmbedder(
        request_fn=request_fn,
        token_counter=VoyageTokenCounter(),
        max_input_tokens=8192,
        sleep_fn=sleep_fn,
    ).embed_texts(["a sentence to embed"])
    return delays


async def _drive_token_counter() -> list[float]:
    """Site 2: one 503 then success -> exactly one backoff through the shared policy."""
    slept: list[float] = []
    attempts: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) < 2:
            return httpx.Response(503, json={})
        return httpx.Response(200, json={"input_tokens": 7})

    async def sleep_fn(delay: float) -> None:
        slept.append(delay)

    counter = counting.AsyncClaudeTokenCounter(SecretStr("k"),
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        sleep=sleep_fn,
    )
    await counter.count("hi")
    await counter.aclose()
    return slept


def _drive_calibration_engine(attempt: int) -> float:
    """Site 3: the engine's named backoff seam, without the probe loop's whole harness.

    The loop needs a corpus, a baseline, an integrity check and a findings port to reach
    its backoff; a second copy of that harness would be a second thing to keep correct.
    The window LADDER through the real loop is pinned in
    ``test_calibration_engine.py::TestEndpointLifecycle::test_backoff_doubles_and_caps``.
    """
    engine = ce.CalibrationEngine.__new__(ce.CalibrationEngine)
    engine._backoff_start_s = ce.BACKOFF_START_S
    engine._backoff_cap_s = ce.BACKOFF_CAP_S
    return engine._backoff_delay(attempt)


async def _drive_command_subscriber(attempt: int) -> list[float]:
    """Site 4: the subscriber's reconnect backoff, driven through its named seam.

    Direct rather than through a reconnect storm: the run loop interleaves poll-interval
    sleeps with reconnect backoffs on the SAME seam (``test_scout.py`` documents that
    mixing), so an end-to-end drive cannot attribute a recorded delay to the backoff.
    """
    slept: list[float] = []

    async def sleep_fn(delay: float) -> None:
        slept.append(delay)

    async def never_connect() -> Any:  # pragma: no cover - _backoff never connects
        raise ConnectionResetError("unused")

    async def handler(_row: dict[str, Any]) -> None:  # pragma: no cover - unused
        return None

    await CommandSubscriber(
        connect=never_connect,
        handler=handler,
        poll_interval_s=0.01,
        sleep=sleep_fn,
        backoff_base_s=_SCOUT_BASE_S,
        max_backoff_s=_SCOUT_CAP_S,
    )._backoff(attempt)
    return slept


def _drive_token_survey(monkeypatch: pytest.MonkeyPatch, attempt: int) -> list[float]:
    """Site 5: the survey counter's sync backoff (``time.sleep``, not asyncio)."""
    slept: list[float] = []

    def fake_sleep(delay: float) -> None:
        slept.append(delay)

    monkeypatch.setattr(ts.time, "sleep", fake_sleep)
    ts.ClaudeTokenCounter._sleep_backoff(attempt, None)
    return slept


# --- additive-jitter drivers (#207 D2/D3) ------------------------------------------------
#
# These pass a ``retry_after`` where the exponential drivers above pass ``None``, so they
# reach the OTHER branch of the same method. That is why the two counters appear twice in
# _DECLARED_SITES: one method, two policies, and a build could route one branch correctly
# while hand-rolling the other.


async def _drive_token_counter_retry_after(retry_after: str = "7") -> list[float]:
    """Site 6: ``counting`` on the ``Retry-After`` branch — ADDITIVE jitter."""
    slept: list[float] = []

    async def sleep_fn(delay: float) -> None:
        slept.append(delay)

    counter = counting.AsyncClaudeTokenCounter(
        SecretStr("k"), client=httpx.AsyncClient(), sleep=sleep_fn
    )
    await counter._sleep_backoff(0, retry_after)
    await counter.aclose()
    return slept


def _drive_token_survey_retry_after(
    monkeypatch: pytest.MonkeyPatch, retry_after: str = "7"
) -> list[float]:
    """Site 7: ``token_survey`` on the ``Retry-After`` branch — ADDITIVE jitter."""
    slept: list[float] = []

    def fake_sleep(delay: float) -> None:
        slept.append(delay)

    monkeypatch.setattr(ts.time, "sleep", fake_sleep)
    ts.ClaudeTokenCounter._sleep_backoff(0, retry_after)
    return slept


async def _drive_eager_lease(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Site 8: the eager-startup retry — ADDITIVE jitter, constant ladder.

    Driven through the real module-level ``server._eager_build_with_retry`` with a heavy
    build that always fails, so the retry path is genuinely exercised rather than simulated
    (packet 59: the per-session ``_EagerStartupLifespan`` was deleted; the retry re-homed to
    this helper). ``asyncio.sleep`` is patched at the ``server`` module's own reference, so
    nothing else in the suite is affected.
    """
    slept: list[float] = []

    async def fake_sleep(delay: float) -> None:
        slept.append(delay)

    async def _always_failing_build() -> None:
        raise RuntimeError("dependency down at boot")

    # Patch the shared ``asyncio`` module object, which is the same one ``server.py``
    # resolves its ``asyncio.sleep`` through. Patching ``server.asyncio`` directly is the
    # obvious spelling but mypy rejects it — ``asyncio`` is an import in that module, not
    # an explicit re-export. monkeypatch reverts it at teardown.
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    # max_attempts=2 -> one retry -> exactly one backoff sleep; fail-closed re-raises.
    with pytest.raises(RuntimeError):
        await server._eager_build_with_retry(
            _always_failing_build, max_attempts=2, backoff_base_s=_EAGER_BASE_S
        )
    return slept


class TestEveryBackoffSharesTheOnePolicy:
    """Mutate the shared policy; every declared site must sleep the sentinel.

    These prove each site INDIVIDUALLY, so a failure names the offender. The SET is
    proven separately, in one process, by
    :func:`test_EVERY_declared_site_draws_from_the_mutated_policy` below.
    """

    def test_the_mutation_is_visible_at_all(self, mutated_policy: _PolicyMutation) -> None:
        """POSITIVE CONTROL — the mutation instrument can actually be seen.

        Without this, every "the site slept the sentinel" assertion below could be passing
        for the wrong reason (a broken fixture that silently no-ops looks identical to a
        perfectly shared policy). This repo has shipped exactly that mistake: a "closed set
        is enforced" probe that rejected on a PARSE ERROR rather than the ASSERT.
        """
        assert (
            backoff_module.jittered_backoff_delay(0, base_s=1.0, cap_s=2.0) == _SENTINEL_DELAY
        )
        assert mutated_policy.draws == [(0, 1.0, 2.0)]

    async def test_resilient_embedder_shares_the_policy(
        self, mutated_policy: _PolicyMutation
    ) -> None:
        """Site 1: ``loresigil.resilient.compute_backoff_delay`` (both embedder backends)."""
        assert await _drive_resilient_embedder() == [_SENTINEL_DELAY], (
            "ResilientEmbedder backed off WITHOUT the shared policy — it is hand-rolling "
            "its own. Five seams each owning a private backoff is finding #207."
        )
        assert mutated_policy.draws

    async def test_token_counter_shares_the_policy(
        self, mutated_policy: _PolicyMutation
    ) -> None:
        """Site 2: ``calibration.counting.AsyncClaudeTokenCounter._sleep_backoff``."""
        assert await _drive_token_counter() == [_SENTINEL_DELAY], (
            "AsyncClaudeTokenCounter backed off WITHOUT the shared policy"
        )
        assert mutated_policy.draws[-1] == (0, counting.RETRY_BASE_DELAY_S, counting.RETRY_MAX_DELAY_S)

    def test_calibration_engine_shares_the_policy(
        self, mutated_policy: _PolicyMutation
    ) -> None:
        """Site 3: ``calibration.engine.CalibrationEngine._backoff_delay``."""
        assert _drive_calibration_engine(4) == _SENTINEL_DELAY, (
            "CalibrationEngine._backoff_delay computed its own delay instead of drawing "
            "from the shared policy"
        )
        assert mutated_policy.draws[-1] == (4, ce.BACKOFF_START_S, ce.BACKOFF_CAP_S)

    async def test_command_subscriber_shares_the_policy(
        self, mutated_policy: _PolicyMutation
    ) -> None:
        """Site 4: ``scout.CommandSubscriber._backoff``."""
        assert await _drive_command_subscriber(2) == [_SENTINEL_DELAY], (
            "CommandSubscriber._backoff backed off WITHOUT the shared policy"
        )
        assert mutated_policy.draws[-1] == (2, _SCOUT_BASE_S, _SCOUT_CAP_S), (
            "the subscriber passed the wrong window parameters to the shared policy"
        )

    def test_token_survey_shares_the_policy(
        self, mutated_policy: _PolicyMutation, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Site 5: ``scripts/token_survey.py::ClaudeTokenCounter._sleep_backoff`` (sync)."""
        assert _drive_token_survey(monkeypatch, 3) == [_SENTINEL_DELAY], (
            "token_survey's counter backed off WITHOUT the shared policy"
        )
        assert mutated_policy.draws[-1] == (3, ts.RETRY_BASE_DELAY_S, ts.RETRY_MAX_DELAY_S)

    async def test_counting_retry_after_uses_the_ADDITIVE_policy(
        self, mutated_policy: _PolicyMutation
    ) -> None:
        """Site 6 (#207 D2): the ``Retry-After`` branch jitters ADDITIVELY, not exponentially.

        The distinct sentinel is the point. A build that routed this branch to
        ``jittered_backoff_delay`` would still be "jittered" and would still pass any pin
        asking merely whether a shared policy was called — while returning values BELOW the
        server's stated floor, which is the one thing this path must never do.
        """
        assert await _drive_token_counter_retry_after("7") == [_SENTINEL_ADDITIVE], (
            "the Retry-After branch did not draw from the ADDITIVE policy"
        )
        assert mutated_policy.additive_draws[-1][0] == 7.0, (
            "the additive jitter was not centred on the server's Retry-After value"
        )
        assert not mutated_policy.draws, (
            "the Retry-After branch called the EXPONENTIAL policy — that draws from "
            "[0, window) and can return LESS than the server instructed (#207 D2)"
        )

    async def test_counting_retry_after_is_capped_before_jittering(
        self, mutated_policy: _PolicyMutation
    ) -> None:
        """The pre-existing cap still applies, and the jitter is added AFTER it (#223).

        A `Retry-After: 120` is capped to RETRY_MAX_DELAY_S before the jitter is added, so
        the additive base is the CAPPED value. Pinned because the cap-vs-Retry-After
        conflict is a KNOWN, unsettled bound (#223) and a silent change to which side of
        the cap the jitter lands on would quietly alter it.
        """
        await _drive_token_counter_retry_after("120")
        assert mutated_policy.additive_draws[-1][0] == counting.RETRY_MAX_DELAY_S

    def test_token_survey_retry_after_uses_the_ADDITIVE_policy(
        self, mutated_policy: _PolicyMutation, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Site 7 (#207 D2): the survey counter's ``Retry-After`` branch."""
        assert _drive_token_survey_retry_after(monkeypatch, "7") == [_SENTINEL_ADDITIVE]
        assert mutated_policy.additive_draws[-1][0] == 7.0
        assert not mutated_policy.draws

    async def test_eager_lease_uses_the_ADDITIVE_policy(
        self, mutated_policy: _PolicyMutation, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Site 8 (#207 D3): boot-retry decorrelates WITHOUT growing.

        Asserts both halves of the ruling: the sleep comes from the additive policy, and
        its base is the UNCHANGED constant — not an exponential ladder. A build that
        "fixed" this by switching to ``jittered_backoff_delay`` would move total
        boot-retry time from ~8 s to ~30 s and could cross an unmeasured container
        health-check budget; ``mutated_policy.draws`` staying empty is what forbids it.
        """
        assert await _drive_eager_lease(monkeypatch) == [_SENTINEL_ADDITIVE]
        assert mutated_policy.additive_draws[-1][0] == _EAGER_BASE_S, (
            "the eager-lease jitter is not centred on its own constant"
        )
        assert not mutated_policy.draws, (
            "the eager-lease retry grew into an exponential ladder — #207 D3 ruled the "
            "ladder shape must NOT move (boot-timing budget is unmeasured)"
        )


async def test_EVERY_declared_site_draws_from_the_mutated_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """COVERAGE AS A CHECKED VARIABLE — the half that makes the rest an invariant.

    The per-site tests above prove each site individually. This one proves the SET: it
    mutates the shared policy ONCE and drives EVERY declared site inside a single test,
    asserting the observed set equals :data:`_DECLARED_SITES` exactly.

    Why a single test rather than an accumulation across the class: class-level state does
    not survive ``pytest -n auto``, where xdist distributes tests across worker processes.
    An accumulator would silently see a PARTIAL set on every parallel run — and this repo
    runs ``-n auto`` by standing rule. A coverage check that quietly degrades to "some
    sites" under the project's own default runner is exactly the false-confidence failure
    this pin exists to prevent, so the drives live together in one process.

    Both directions are asserted. A declared site nothing drives is an unguarded site
    wearing a guarantee; an observed site nobody declared means the declaration drifted
    from reality.
    """
    # BOTH policies, via the same helper the per-site fixture uses — a second hand-rolled
    # patch here would be this file's own version of the duplication it exists to forbid,
    # and its first casualty was this very test (it patched only the exponential policy and
    # reported the three additive sites as unshared).
    mutation = _apply_mutation(monkeypatch)
    observed: set[str] = set()

    if await _drive_resilient_embedder() == [_SENTINEL_DELAY]:
        observed.add("loresigil.resilient.compute_backoff_delay")
    if await _drive_token_counter() == [_SENTINEL_DELAY]:
        observed.add("loremaster.calibration.counting.AsyncClaudeTokenCounter._sleep_backoff")
    if _drive_calibration_engine(1) == _SENTINEL_DELAY:
        observed.add("loremaster.calibration.engine.CalibrationEngine._probe_loop")
    if await _drive_command_subscriber(1) == [_SENTINEL_DELAY]:
        observed.add("loremaster.scout.CommandSubscriber._backoff")
    if _drive_token_survey(monkeypatch, 1) == [_SENTINEL_DELAY]:
        observed.add("token_survey.ClaudeTokenCounter._sleep_backoff")

    # --- sites 6-8: the ADDITIVE policy (#207 D2/D3) --------------------------------
    if await _drive_token_counter_retry_after() == [_SENTINEL_ADDITIVE]:
        observed.add(
            "loremaster.calibration.counting.AsyncClaudeTokenCounter._sleep_backoff.retry_after"
        )
    if _drive_token_survey_retry_after(monkeypatch) == [_SENTINEL_ADDITIVE]:
        observed.add("token_survey.ClaudeTokenCounter._sleep_backoff.retry_after")
    if await _drive_eager_lease(monkeypatch) == [_SENTINEL_ADDITIVE]:
        observed.add("loremaster.server._eager_build_with_retry")

    missing = _DECLARED_SITES - observed
    assert not missing, (
        f"these declared backoff sites did NOT draw from the mutated shared policy: "
        f"{sorted(missing)}.\n"
        f"Each one still backs off, still retries, and still passes every 'does it work?' "
        f"test — while keeping a PRIVATE copy of the delay policy. That is finding #207 "
        f"(and #102, #108) reproducing: a fix reaches one copy and not the others.\n"
        f"Route the site through:\n"
        f"    from loresigil import backoff\n"
        f"    delay = backoff.jittered_backoff_delay(attempt, base_s=..., cap_s=...)\n"
        f"NOTE: import the MODULE, not the function — a `from ... import "
        f"jittered_backoff_delay` binds at import time, so this mutation could not reach it "
        f"and a private copy would be indistinguishable from the real thing."
    )
    undeclared = observed - _DECLARED_SITES
    assert not undeclared, f"observed sites missing from _DECLARED_SITES: {sorted(undeclared)}"
    # Both ledgers, because the two policies record separately. Summing only the
    # exponential one under-counts by exactly the additive sites — which is what this
    # assertion did on its first draft, reporting 5 draws for 8 sites while every site
    # had in fact been observed. An instrument that miscounts its own coverage is the
    # failure mode this whole file exists to prevent, so it is pinned honestly here.
    total_draws = len(mutation.draws) + len(mutation.additive_draws)
    assert total_draws >= len(_DECLARED_SITES), (
        f"the mutated policies recorded only {total_draws} draws "
        f"({len(mutation.draws)} exponential + {len(mutation.additive_draws)} additive) "
        f"for {len(_DECLARED_SITES)} declared sites — the instrument is under-counting"
    )


_JITTER_DRAWS = 64
_JITTER_MIN_DISTINCT = 60


async def _real_policy_draws_per_site(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[float]]:
    """Drive every declared site ``_JITTER_DRAWS`` times against the REAL policy.

    No mutation, no sentinel: each site's own binding of the real shared policy is
    exercised and the delays it actually sleeps are collected. Entry points are the
    cheapest real ones per site (the policy binding itself, not the whole HTTP/probe
    flow) so 64 draws x 8 sites stays fast.
    """
    draws: dict[str, list[float]] = {}

    # 1. loresigil.resilient.compute_backoff_delay
    draws["loresigil.resilient.compute_backoff_delay"] = [
        resilient_module.compute_backoff_delay(0) for _ in range(_JITTER_DRAWS)
    ]

    # 2 + 6. counting — exponential branch (retry_after=None) and additive branch.
    exponential: list[float] = []
    additive: list[float] = []

    async def rec_exp(delay: float) -> None:
        exponential.append(delay)

    async def rec_add(delay: float) -> None:
        additive.append(delay)

    client = httpx.AsyncClient()
    for sink, retry_after in ((rec_exp, None), (rec_add, "7")):
        counter = counting.AsyncClaudeTokenCounter(SecretStr("k"), client=client, sleep=sink)
        for _ in range(_JITTER_DRAWS):
            await counter._sleep_backoff(0, retry_after)
    await client.aclose()
    draws["loremaster.calibration.counting.AsyncClaudeTokenCounter._sleep_backoff"] = exponential
    draws[
        "loremaster.calibration.counting.AsyncClaudeTokenCounter._sleep_backoff.retry_after"
    ] = additive

    # 3. calibration engine
    draws["loremaster.calibration.engine.CalibrationEngine._probe_loop"] = [
        _drive_calibration_engine(0) for _ in range(_JITTER_DRAWS)
    ]

    # 4. scout — its own named seam, so no poll-interval sleeps are mixed in.
    scout_draws: list[float] = []

    async def rec_scout(delay: float) -> None:
        scout_draws.append(delay)

    async def never_connect() -> Any:  # pragma: no cover - _backoff never connects
        raise ConnectionResetError("unused")

    async def scout_handler(_row: dict[str, Any]) -> None:  # pragma: no cover - unused
        return None

    subscriber = CommandSubscriber(
        connect=never_connect,
        handler=scout_handler,
        poll_interval_s=0.01,
        sleep=rec_scout,
        backoff_base_s=_SCOUT_BASE_S,
        max_backoff_s=_SCOUT_CAP_S,
    )
    for _ in range(_JITTER_DRAWS):
        await subscriber._backoff(0)
    draws["loremaster.scout.CommandSubscriber._backoff"] = scout_draws

    # 5 + 7. token_survey — exponential and additive branches.
    survey_exp: list[float] = []
    survey_add: list[float] = []
    monkeypatch.setattr(ts.time, "sleep", survey_exp.append)
    for _ in range(_JITTER_DRAWS):
        ts.ClaudeTokenCounter._sleep_backoff(0, None)
    monkeypatch.setattr(ts.time, "sleep", survey_add.append)
    for _ in range(_JITTER_DRAWS):
        ts.ClaudeTokenCounter._sleep_backoff(0, "7")
    draws["token_survey.ClaudeTokenCounter._sleep_backoff"] = survey_exp
    draws["token_survey.ClaudeTokenCounter._sleep_backoff.retry_after"] = survey_add

    # 8. the eager-startup lease.
    eager: list[float] = []
    for _ in range(_JITTER_DRAWS):
        eager.extend(await _drive_eager_lease(monkeypatch))
    draws["loremaster.server._eager_build_with_retry"] = eager

    return draws


async def test_reverting_the_shared_policy_reddens_EVERY_site(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """THE ACCEPTANCE CRITERION from cold-audit R4: undoing #207 must fail HERE, per site.

    The sentinel-mutation instrument above proves each site ROUTES to the shared policy.
    It does not prove the policy still JITTERS — under the sentinel, every site returns a
    constant by construction. So an auditor reverted ``loresigil/backoff.py`` to the exact
    pre-#207 build and measured: **only 4 tests reddened, all inside the policy's own unit
    file.** Every site-level pin stayed green, several while their failure messages promised
    otherwise. A false gate, five times over, by this repo's own definition.

    This test closes that flank centrally rather than by patching each pin's bound: it
    drives every declared site against the REAL policy and requires the delays each one
    actually sleeps to be DRAWN. A deterministic revert yields 1 distinct value per site
    and fails here immediately.

    Thresholds are borrowed from the policy's own derived pin (64 draws, >= 60 distinct)
    rather than re-invented, and they close two wrong builds at once: a deterministic
    ladder scores 1, and a QUANTISED slot table — this repo's #102/#108 shape — cannot
    exceed its slot count (16 at worst). A weaker 8/>=6 bar, which is what the D2 pin
    first shipped with, admits a 16-slot table ~70% of the time.

    Coverage is checked, not assumed: the observed site set must EQUAL
    :data:`_DECLARED_SITES`, so a new site cannot be added without being jitter-proven.
    """
    draws = await _real_policy_draws_per_site(monkeypatch)

    assert set(draws) == set(_DECLARED_SITES), (
        f"this instrument does not cover every declared site — "
        f"missing={sorted(set(_DECLARED_SITES) - set(draws))}, "
        f"undeclared={sorted(set(draws) - set(_DECLARED_SITES))}"
    )

    undiscriminating: list[str] = []
    for site, values in sorted(draws.items()):
        assert len(values) == _JITTER_DRAWS, (
            f"{site}: expected {_JITTER_DRAWS} draws, got {len(values)} — the driver is "
            f"not exercising the site once per iteration"
        )
        if len(set(values)) < _JITTER_MIN_DISTINCT:
            undiscriminating.append(f"{site}: {len(set(values))} distinct of {len(values)}")

    assert not undiscriminating, (
        "these sites did NOT produce drawn delays against the real shared policy:\n  "
        + "\n  ".join(undiscriminating)
        + "\n\n1 distinct = a DETERMINISTIC ladder (#207 undone). <= 16 distinct = a "
        "QUANTISED slot table (#102/#108). Either way the site's clients wake in "
        "lockstep. This is the acceptance criterion for cold-audit R4: a revert of "
        "loresigil/backoff.py to its pre-#207 behaviour must fail THIS test, not only "
        "the policy's own unit file."
    )


class TestNoNewHandRolledBackoff:
    """THE PERIMETER: no production module may hand-roll an exponential window.

    Deny-by-default over a rare construct with a one-file allowlist — not a scan for
    forbidden shapes. See this module's docstring for why that direction is the only one
    with a track record.
    """

    def test_no_production_module_outside_the_allowlist_exponentiates_by_a_variable(
        self,
    ) -> None:
        offenders: list[str] = []
        # Routed through the SHARED ONE parser (F4 / #279): the split-leg private-parse loop
        # (``_production_python_files()`` → ``production_sources`` + ``ast.parse``) the
        # delta-adversary-asub-5 survivor hid behind is GONE, so L1's runtime chokepoint sees
        # this scan route SANCTIONED. ``include_skills=True`` matches the old
        # ``production_sources()`` reach; the parser also covers scripts/skills test files
        # (a benign, arguably-more-correct widening — measured to add no new offenders).
        for relative, tree in parse_production_trees(include_scripts=True, include_skills=True).items():
            if relative in _POW_ALLOWLIST:
                continue
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.BinOp)
                    and isinstance(node.op, ast.Pow)
                    and not isinstance(node.right, ast.Constant)
                ):
                    offenders.append(f"{relative}:{node.lineno}: {ast.unparse(node)}")

        assert not offenders, (
            "a production module raised a value to a VARIABLE power outside the allowlist:\n  "
            + "\n  ".join(offenders)
            + "\n\nIn this tree that shape has only ever been one thing: a hand-rolled "
            "exponential backoff window. Finding #207 found FIVE of them and none was "
            "jittered; #102 and #108 were the same class before it. Draw the delay from the "
            "shared policy instead:\n"
            "    from loresigil import backoff\n"
            "    delay = backoff.jittered_backoff_delay(attempt, base_s=..., cap_s=...)\n"
            "and add the new site to _DECLARED_SITES in this file with a driver.\n"
            "If this really is unrelated arithmetic, add the file to _POW_ALLOWLIST WITH "
            "evidence (this scan had ZERO false positives across the whole tree on "
            "2026-07-25)."
        )

    def test_the_allowlisted_file_still_contains_what_it_was_exempted_for(self) -> None:
        """POSITIVE CONTROL for the allowlist — an exemption must still be earning itself.

        Without this, ``_POW_ALLOWLIST`` silently becomes a permanent hole: if
        ``_txn_conflict_backoff_seconds`` were deleted or rewritten, the exemption would
        keep waving through any FUTURE hand-rolled backoff added to that file. Pairing the
        deny with proof that the exempted construct is still present and still jittered is
        the difference between an allowlist and an unexamined blind spot.
        """
        for relative in _POW_ALLOWLIST:
            source = (_REPO_ROOT / relative).read_text(encoding="utf-8")
            assert "_txn_conflict_backoff_seconds" in source, (
                f"{relative} is allowlisted from the exponentiation perimeter because it owns "
                f"the transaction-conflict full-jitter policy — but that function is gone. "
                f"Re-derive the exemption or drop it; a stale allowlist entry is a hole."
            )
            assert "random.uniform(0, window)" in source, (
                f"{relative}'s exemption rests on it ALREADY drawing full jitter. That draw is "
                f"no longer there, so the exemption no longer holds (finding #102)."
            )

    def test_the_scan_can_actually_see_an_offender(self, tmp_path: Path) -> None:
        """POSITIVE CONTROL for the scan itself — prove it fires on a known-bad input.

        A perimeter that returns "no offenders" is worthless until it has been shown
        returning "offender" on something broken. ``CLAUDE.md``: *a probe needs a control —
        the auditor's instrument can lie the same way the author's did.*
        """
        offending = "delay = min(base * (2**attempt), cap)\n"
        tree = ast.parse(offending)
        found = [
            ast.unparse(node)
            for node in ast.walk(tree)
            if isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Pow)
            and not isinstance(node.right, ast.Constant)
        ]
        assert found == ["2 ** attempt"], (
            "the perimeter's detection logic did not fire on a verbatim copy of the #207 "
            "defect — every negative result it produces is meaningless"
        )

        benign = "area = radius**2\nscaled = value**2.0\n"
        benign_tree = ast.parse(benign)
        benign_hits = [
            node
            for node in ast.walk(benign_tree)
            if isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Pow)
            and not isinstance(node.right, ast.Constant)
        ]
        assert not benign_hits, (
            "the perimeter fires on constant-exponent arithmetic — it would produce false "
            "positives on ordinary maths, and a gate that insults honest code gets switched off"
        )


class TestKnownBoundsOfThisInstrument:
    """PIN THE MISS (``CLAUDE.md``: *when you cannot close a hole, pin it*).

    An unpinned known limitation is indistinguishable from an unknown one — the next
    engineer either rediscovers it from an outage or "helpfully" closes it and re-opens a
    settled trade. These tests assert the holes EXIST and go RED the day someone closes one.
    """

    def test_KNOWN_BOUND_a_multiplicative_backoff_evades_the_perimeter(self) -> None:
        """KNOWN BOUND (#207): the perimeter sees ``2**attempt``, not ``delay *= 2``.

        A backoff accumulated by repeated multiplication, or read from a lookup table, has no
        ``Pow`` node and is invisible to this scan. That is DELIBERATE and not worth closing:
        catching it would mean enumerating forbidden shapes, and ``CLAUDE.md``'s six-defeat
        table records that every instrument keyed on the forbidden set was beaten by the next
        name. The perimeter is aimed at the honest engineer writing the obvious thing, which
        is what all five #207 sites and both prior instances actually did.

        IF YOU CLOSED THIS DELIBERATELY, delete this pin and say so in the commit.
        RE-OPEN TRIGGER: the first backoff found in this tree written multiplicatively.
        """
        multiplicative = "delay = 1.0\nfor _ in range(n):\n    delay *= 2\n"
        tree = ast.parse(multiplicative)
        pow_nodes = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow)
        ]
        assert not pow_nodes, (
            "a multiplicative backoff now produces a Pow node — the perimeter's known bound "
            "has changed shape. Re-derive the bound (finding #207)."
        )

    def test_KNOWN_BOUND_the_retry_after_jitter_WIDTH_is_chosen_not_measured(self) -> None:
        """KNOWN BOUND (#207 D2): the ``Retry-After`` path IS now jittered — the residual
        bound is the WIDTH, not the existence.

        The previous bound ("this path is not jittered at all") was CLOSED by D2 and this
        pin was retargeted rather than deleted, per the ruling. What remains unsettled:

        1. ``ADDITIVE_JITTER_WIDTH_S = 1.0`` is a **chosen** constant, not a measured one.
           Nobody has observed how many clients share a rate limiter here or how wide a
           window actually disperses them; 1 s is a reasoned default, not evidence.
        2. The pre-existing ``min(…, RETRY_MAX_DELAY_S)`` cap can still sleep LESS than a
           large ``Retry-After`` asks (`Retry-After: 120` → ~30 s). That conflict predates
           #207 entirely and is finding **#223**. The additive jitter did NOT settle it,
           and must not be read as having done so.

        IF YOU CLOSED EITHER DELIBERATELY, delete the corresponding half and say so.
        RE-OPEN TRIGGERS: (1) a measurement of real concurrent-client counts on this
        endpoint; (2) an operator ruling on #223.
        """
        source = (
            _REPO_ROOT / "loremaster/loremaster/calibration/counting.py"
        ).read_text(encoding="utf-8")
        assert "min(float(retry_after), RETRY_MAX_DELAY_S)" in source, (
            "the Retry-After CAP is gone. If #223 was ruled and the cap deliberately "
            "removed, delete this half of the pin and say so; if not, a large Retry-After "
            "is now honoured in full and a hostile server can park a counter indefinitely."
        )
        assert backoff_module.ADDITIVE_JITTER_WIDTH_S == 1.0, (
            f"the additive jitter width changed to "
            f"{backoff_module.ADDITIVE_JITTER_WIDTH_S}. That is fine IF it was measured — "
            f"but this pin exists because 1.0 never was. Update the pin WITH the "
            f"measurement, so the next reader inherits evidence rather than a second guess."
        )


def test_the_shared_policy_is_backed_by_tenacity_not_a_hand_roll() -> None:
    """The policy is the PACKAGE's, not ours (operator: packages over hand-rolling).

    Pinned structurally because the alternative — re-deriving Full Jitter by hand — is
    exactly what the rule forbids, and because a future edit could quietly replace the
    import with three lines of ``random.uniform`` that pass every behavioural pin in
    ``loresigil/tests/test_backoff.py`` while re-taking on the maintenance burden.

    It also pins WHICH tenacity strategy: ``wait_exponential_jitter`` (equal jitter around a
    floor) would satisfy the word "jitter" and silently re-ship the policy #102 rejected.
    """
    source = (_REPO_ROOT / "loresigil/loresigil/backoff.py").read_text(encoding="utf-8")

    # Inspect the CALL inside the policy function, not the file's text. A substring
    # check over the whole module cannot tell "uses tenacity" from "still imports
    # tenacity while hand-rolling the maths underneath" — measured 2026-07-25: a
    # mutation that replaced this function's entire body with
    # ``min(base_s * 2**attempt, cap_s)`` left the import and the docstring intact and
    # this pin STAYED GREEN. The both-ways mutation diff caught it; the pin now reads
    # the AST so it cannot be fooled the same way.
    tree = ast.parse(source)
    policy_fn = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "jittered_backoff_delay"
        ),
        None,
    )
    assert policy_fn is not None, "the shared policy function jittered_backoff_delay is gone"
    called_names = {
        node.func.id
        for node in ast.walk(policy_fn)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "wait_random_exponential" in called_names, (
        f"jittered_backoff_delay does not CALL tenacity's wait_random_exponential — the AWS "
        f"Full Jitter implementation (it calls: {sorted(called_names)}). If the maths was "
        f"hand-rolled back into this body, that re-takes a maintenance burden the package "
        f"already carries (operator: packages over hand-rolling, verified by reading the "
        f"installed API)."
    )
    assert "wait_exponential_jitter" not in source, (
        "the shared policy switched to tenacity's wait_exponential_jitter. That class is "
        "EQUAL jitter — 'initial * 2**n + uniform(0, jitter)' with a FIXED 1s jitter width — "
        "so it never draws below its exponential floor. This repo ruled that insufficient in "
        "#102; test_surreal_store.py fails such builds as 'wb13-equal-jitter'."
    )
