"""Full-jitter exponential backoff — the ONE retry-delay policy in this workspace.

Finding #207: five independent backoff implementations, none of them jittered.
Exponential growth was present every time; **decorrelation was absent every time**.
That is not coincidence — it is what hand-writing a policy whose subtle half is
invisible produces. Findings #102 and #120 are the same class, twice before.

**The defect jitter fixes.** Exponential backoff without jitter spreads retries in
TIME but not across CLIENTS. Clients that fail *simultaneously* — precisely what a
shared rate-limit guard, a store contention spike, or a cold start produces — all
compute the IDENTICAL delay, sleep it, and wake together to collide again. The herd
does not thin; it just arrives later. Only a random draw breaks the tie.

**Why FULL jitter, not "exponential plus a jitter term".** This policy draws
uniformly from ``[0, window)`` — the draw reaches all the way DOWN TO ZERO — so one
racer can retry almost immediately while another waits out most of the window. That
asymmetry is what actually breaks a tie. Jitter *around a floor* (the "equal jitter"
family: ``window + uniform(0, k)``) leaves every racer bunched just above the same
floor, which is the behaviour finding #102 already ruled insufficient for this repo
(see :func:`loremaster.store._txn._txn_conflict_backoff_seconds`, whose contract
pins the same property for the transaction-conflict seam).

**The implementation is tenacity's, not ours.** :class:`tenacity.wait.wait_random_exponential`
is the Full Jitter algorithm from AWS's "Exponential Backoff and Jitter" — its own
docstring names it as such — and it ships tested. We supply only the adapter that
turns tenacity's retry-loop-shaped interface into the delay-for-attempt-N function
these call sites need, because their retry LOOPS are proven, guarded, and deliberately
not being churned (#202). The package does the job; we do not re-implement it.

**Import this module, not the function** (``from loresigil import backoff``, then
``backoff.jittered_backoff_delay(...)``). The late binding is load-bearing, not
style: it is what lets one ``monkeypatch`` of this module's attribute reach EVERY
genuine caller, so a test can tell "shares the policy" from "hand-rolled one that
looks like it". A ``from ... import jittered_backoff_delay`` binds at import time and
would make a private copy indistinguishable from the real thing — which is exactly
the failure mode (#102) this module exists to end.
"""

from __future__ import annotations

from tenacity import AsyncRetrying, RetryCallState
from tenacity.wait import wait_random_exponential

#: The growth factor of the backoff window. Doubling is the universal convention and
#: the value every site this module replaced already used.
BACKOFF_EXP_BASE: float = 2.0

#: tenacity's wait strategies read their attempt index off a :class:`RetryCallState`,
#: which wants the owning retry object. We drive the strategy directly rather than
#: through a tenacity retry loop (the call sites keep their own proven loops, #202),
#: so this instance exists purely to satisfy that constructor. It holds no state that
#: a wait strategy reads.
_RETRY_OBJECT = AsyncRetrying()


def jittered_backoff_delay(attempt: int, *, base_s: float, cap_s: float) -> float:
    """Draw a full-jitter exponential backoff delay for a zero-based ``attempt``.

    The delay is drawn uniformly from ``[0, min(cap_s, base_s * 2**attempt))``: the
    window grows exponentially with the attempt index and is capped, but the delay
    itself is a FRESH random draw from that window on every call. Two callers that
    fail at the same instant therefore sleep INDEPENDENT durations and stop colliding,
    which a deterministic ladder cannot do no matter how steeply it grows.

    Redrawn per call — never cached, never derived from the identity of whatever was
    being retried, never quantised into slots. Each of those has been a real defect in
    this repo (#102 derived jitter from the contended row's id, making it identical
    across racers; #108 used a 4-slot table, so at 8-way contention the pigeonhole
    guarantees collisions).

    Args:
        attempt: Zero-based index of the attempt that just failed — ``0`` for the
            sleep taken after the first failure. This is the convention every call
            site already used; passing a 1-based count silently doubles the window.
        base_s: The width of the attempt-0 window, in seconds.
        cap_s: Ceiling on the window, in seconds, so a long outage cannot produce an
            absurd sleep. The drawn delay never exceeds it.

    Returns:
        A delay in seconds, uniformly distributed over ``[0, min(cap_s,
        base_s * 2**attempt))``.
    """
    state = RetryCallState(retry_object=_RETRY_OBJECT, fn=None, args=(), kwargs={})
    # tenacity's strategies are 1-based; our call sites are 0-based.
    state.attempt_number = attempt + 1
    strategy = wait_random_exponential(multiplier=base_s, max=cap_s, exp_base=BACKOFF_EXP_BASE)
    return strategy(state)
