"""Contract for the shared full-jitter backoff policy (:mod:`loresigil.backoff`).

Finding #207. The property under test is DECORRELATION, not growth: exponential
growth was present in all five backoff implementations this module replaced, and
jitter was absent from all five. So every pin here is written to fail a build that
grows correctly and decorrelates wrongly — that is the only failure mode with a
track record in this repo (#102, #108, #120, #207).

**Every bound below is distributional and stated with its own impossibility
margin.** A jitter test is a randomness test, and a pin that fails once in a
hundred runs gets deleted by the next engineer rather than investigated. None of
these thresholds is a coin-flip: each is quantified in its own docstring, and the
loosest margin in the file is ~1e-23.

Reference table for the discrimination thresholds — what each wrong build scores on
:meth:`TestSimultaneousClientsDecorrelate::test_simultaneous_clients_draw_distinct_delays`,
which draws 64 delays at a single attempt index:

    deterministic ladder (the #207 defect)      1  distinct   <- must die
    4-slot jitter table (the #108 defect)      <=4 distinct   <- must die
    16-slot jitter table (the #102 defect)    <=16 distinct   <- must die
    full continuous jitter (the design)         64 distinct   <- must live

The pin asserts >= 60, which no discrete-slot build can reach and no deterministic
build can approach.
"""

from __future__ import annotations

from loresigil import backoff

# Policy parameters used by the pins. Deliberately NOT the defaults of any call
# site: a fixture that reuses a production constant cannot tell "the policy honours
# my arguments" from "the policy ignores them and happens to agree".
_BASE_S = 1.0
_CAP_S = 30.0

#: Attempt index whose window (``1.0 * 2**3 == 8.0``) is comfortably below the cap,
#: so pins about the WINDOW are not silently testing the cap instead.
_UNCAPPED_ATTEMPT = 3
_UNCAPPED_WINDOW_S = 8.0


def _draws(count: int, attempt: int, *, base_s: float = _BASE_S, cap_s: float = _CAP_S) -> list[float]:
    """Draw ``count`` delays for the SAME attempt index — the simultaneous-failure case."""
    return [
        backoff.jittered_backoff_delay(attempt, base_s=base_s, cap_s=cap_s) for _ in range(count)
    ]


class TestSimultaneousClientsDecorrelate:
    """THE property of finding #207: clients that fail together must not wake together."""

    def test_simultaneous_clients_draw_distinct_delays(self) -> None:
        """64 clients failing at the same instant, on the same attempt, must draw 64
        different delays.

        This is the pin the whole finding exists for. Every one of the five
        implementations replaced here would score exactly 1 — they compute
        ``min(base * 2**attempt, cap)``, which is a pure function of the attempt
        index, so N racers sleep one shared value and re-collide on wake.

        Threshold rationale (see the module docstring's table): a continuous draw
        collides only on exact float64 equality, p ~ 64**2 / 2**53 ~ 5e-13 for the
        whole sample. Asserting >= 60 leaves that margin intact while sitting far
        above the 16 that this repo's own historical slot-table idiom could reach.
        """
        draws = _draws(64, _UNCAPPED_ATTEMPT)
        distinct = len(set(draws))
        assert distinct >= 60, (
            f"only {distinct} distinct delays across 64 simultaneous clients at one "
            f"attempt index — this backoff is quantised or deterministic, so racers "
            f"wake in lockstep and re-collide. A deterministic ladder scores 1; a "
            f"16-slot table scores <=16; full continuous jitter scores 64. Finding "
            f"#207 (and #102, #108 before it)."
        )

    def test_two_calls_with_identical_arguments_differ(self) -> None:
        """The delay is DRAWN, not computed.

        The minimal statement of the same property, and the one that reads as a
        contract rather than a statistic: same attempt, same base, same cap, two
        calls, two answers. A deterministic implementation is a pure function of its
        arguments and cannot pass this at all.

        Run over 100 pairs so the verdict does not hinge on one draw: a build that
        redraws correctly fails this only if all 100 pairs collide exactly, p ~ 1e-13
        per pair.
        """
        pairs = [
            (
                backoff.jittered_backoff_delay(_UNCAPPED_ATTEMPT, base_s=_BASE_S, cap_s=_CAP_S),
                backoff.jittered_backoff_delay(_UNCAPPED_ATTEMPT, base_s=_BASE_S, cap_s=_CAP_S),
            )
            for _ in range(100)
        ]
        differing = sum(1 for first, second in pairs if first != second)
        assert differing >= 95, (
            f"only {differing}/100 call pairs with IDENTICAL arguments returned "
            f"different delays — the delay is being computed from its arguments "
            f"rather than drawn, or drawn once and cached."
        )


class TestJitterIsFullNotAroundAFloor:
    """The jitter must reach DOWN TO ZERO, not sit above the exponential floor.

    This is the pin that distinguishes the policy this repo ruled (#102) from the
    superficially similar "equal jitter" family — including
    :class:`tenacity.wait.wait_exponential_jitter`, which computes
    ``initial * 2**n + uniform(0, jitter)`` and therefore never returns anything
    below its exponential floor. Adopting that class would have re-shipped the
    behaviour #102 already rejected, and no growth-shaped pin would have noticed.

    It is deliberately BEHAVIOURAL rather than a check on which tenacity symbol is
    imported: a name-list pin is defeated by the next name, whereas "did any draw
    land in the bottom half of the window" is true of full jitter and false of every
    floor-jittered build regardless of what it is called.
    """

    def test_draws_reach_the_bottom_half_of_the_window(self) -> None:
        """Across 200 draws, at least one must land below half the window.

        Full jitter over ``[0, 8.0)`` puts ~50% of draws under 4.0, so all 200
        missing the bottom half has p = 0.5**200 ~ 6e-61. An equal-jitter build
        scores ZERO such draws by construction — its minimum IS the floor.
        """
        draws = _draws(200, _UNCAPPED_ATTEMPT)
        half_window = _UNCAPPED_WINDOW_S / 2
        assert min(draws) < half_window, (
            f"no draw out of 200 landed below half the window "
            f"(min={min(draws)}, window={_UNCAPPED_WINDOW_S}) — this is jitter around "
            f"a FLOOR, not the full jitter the design ruled. Racers stay bunched just "
            f"above the floor and the tie never breaks."
        )

    def test_draws_span_both_halves_of_the_window(self) -> None:
        """The draws must populate the whole window, not cluster in one end.

        The positive control for the pin above: showing draws below the midpoint is
        only meaningful if draws ABOVE it also occur — a build that returned a
        constant 0.0 would pass a bottom-half check while decorrelating nothing.
        p(all 200 in one half) = 2 * 0.5**200.
        """
        draws = _draws(200, _UNCAPPED_ATTEMPT)
        half_window = _UNCAPPED_WINDOW_S / 2
        assert min(draws) < half_window < max(draws), (
            f"draws did not span both halves of the window "
            f"(min={min(draws)}, max={max(draws)}, window={_UNCAPPED_WINDOW_S})"
        )


class TestWindowGrowsAndIsBounded:
    """Growth and the cap — the half that was never broken, pinned so it stays unbroken.

    Jitter is worthless if it is drawn from a window that ignores the attempt index
    (a flat random delay does not back off) or one that ignores the cap (a long
    outage produces an absurd sleep). These pins keep the fix from trading one
    defect for another.
    """

    def test_the_window_grows_with_the_attempt_index(self) -> None:
        """Later attempts must be able to produce longer delays than earlier ones.

        Stated as a reachability claim rather than a per-draw comparison, because
        under full jitter a LATER attempt can legitimately draw a SHORTER delay than
        an earlier one — that asymmetry is the point. Pinning ``d[0] < d[1] < d[2]``
        would be pinning the absence of jitter, and would be flaky by construction.

        Attempt 0's window is ``[0, 1.0)`` so no draw can exceed 1.0; attempt 3's is
        ``[0, 8.0)`` and 500 draws all landing under 1.0 has p = 0.125**500.
        """
        early = _draws(500, 0)
        late = _draws(500, _UNCAPPED_ATTEMPT)
        assert max(early) <= _BASE_S, (
            f"a draw at attempt 0 exceeded its window (max={max(early)}, "
            f"window={_BASE_S}) — the window is not honouring base_s"
        )
        assert max(late) > _BASE_S, (
            f"500 draws at attempt {_UNCAPPED_ATTEMPT} all fell inside attempt 0's "
            f"window (max={max(late)}) — the window is not growing with the attempt "
            f"index, so this is a flat random delay, not a backoff"
        )

    def test_the_cap_bounds_an_arbitrarily_late_attempt(self) -> None:
        """At attempt 20 the uncapped window would be ~1e6 s; every draw must fit the cap."""
        draws = _draws(200, 20)
        assert max(draws) <= _CAP_S, (
            f"a draw exceeded the cap (max={max(draws)}, cap={_CAP_S}) — a long "
            f"outage would produce an absurd sleep"
        )
        assert min(draws) >= 0.0, f"a negative delay was drawn (min={min(draws)})"

    def test_the_cap_is_reached_not_merely_respected(self) -> None:
        """The positive control for the cap pin: capped draws must still span the cap.

        A build that returned 0.0 whenever the window exceeded the cap would satisfy
        "every draw <= cap" while destroying the backoff entirely. Under full jitter
        over ``[0, 30.0)``, 200 draws all landing below 15.0 has p = 0.5**200.
        """
        draws = _draws(200, 20)
        assert max(draws) > _CAP_S / 2, (
            f"200 capped draws all landed in the bottom half of the cap "
            f"(max={max(draws)}, cap={_CAP_S}) — the cap is collapsing the window "
            f"rather than bounding it"
        )

    def test_the_policy_honours_caller_supplied_parameters(self) -> None:
        """base_s and cap_s must actually drive the window.

        Guards the monoculture failure mode: every call site passes its own base and
        cap, so a policy that ignored them in favour of module constants would still
        pass every pin above (they all use one parameter pair) while silently giving
        five call sites the same schedule.
        """
        narrow = _draws(200, 0, base_s=0.01, cap_s=30.0)
        assert max(narrow) <= 0.01, (
            f"a draw exceeded a caller-supplied base_s of 0.01 (max={max(narrow)}) — "
            f"the policy is ignoring its arguments"
        )
        capped_low = _draws(200, 10, base_s=1.0, cap_s=0.05)
        assert max(capped_low) <= 0.05, (
            f"a draw exceeded a caller-supplied cap_s of 0.05 "
            f"(max={max(capped_low)}) — the policy is ignoring its arguments"
        )
