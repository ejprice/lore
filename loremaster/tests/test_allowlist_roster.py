"""CONTRACT — the R12 roster substrate: runtime state, fail-closed, no restart to revoke.

Design ``docs/design/2026-07-31-packet39-google-oauth.md`` §3-R12 (operator override,
verbatim: *"I don't want the user allow list baked in the image. That's so stupid it
hurts."*). The allowlist is an mtime-watched flat file OUTSIDE the repo and OUTSIDE the
image, bind-mounted read-only; ``lore.yaml`` carries only its PATH. **The acceptance
test IS the point: adding or revoking a principal requires NO container recreate and NO
image rebuild.**

------------------------------------------------------------------------------
THE FRESHNESS MODEL, STATED ONCE BECAUSE EVERY FIXTURE BELOW DEPENDS ON IT

**Operator ruling, 2026-07-31 (S5), overruling the earlier "one ``stat`` per cache-MISS"
wording: the roster is ``stat``-ed on EVERY verification, cache hits included. A
principal removed from the roster is denied on the FIRST verification after the edit.
THERE IS NO RESIDUAL WINDOW.** The earlier wording was a PERFORMANCE floor, never a
licence to cap revocation speed; design §3-R12 is being restored to the strong form,
which design §9 group 1 already carried (*"revoked-while-token-cached principal denied
on the next request (cache-hit fixture)"*).

Two consequences every fixture below depends on:

1. **No revocation pin needs an intervening cache MISS.** The cached principal is
   denied on their very next verification, full stop. Where a pin asserts that denial,
   it also asserts the outbound call-count did NOT move — otherwise the pin could pass
   because caching is broken rather than because admission was re-evaluated.
2. **The two caches stay separate.** The token cache caches GOOGLE's verdict
   (token → subject/email/expiry) and is NOT flushed by a roster edit; admission is a
   set lookup against the live in-memory roster on every verification. A build that
   "fixes" revocation by flushing the token cache passes the denial pin and fails
   :meth:`TestRevocationIsEffectiveOnTheVeryNextVerification.
   test_the_token_cache_is_not_flushed_by_a_roster_edit`.

The ONE performance property that survives the ruling: an UNCHANGED roster is
``stat``-ed but not re-READ (design R12's *"full re-read only when mtime changed"*).
Pinned behaviourally in :class:`TestRosterFreshnessOnEveryVerification`.

------------------------------------------------------------------------------
WHY THIS IS ITS OWN MODULE, AND WHY IT USES REAL FILES

Every other auth pin can run against an in-memory allowlist. These cannot: the
behaviour under contract is *"what happens on disk, between two verifications, in one
live process"*. A fixture that guarantees a fresh in-memory set is exactly the shape
CLAUDE.md warns about — **the fixture guarantees the one condition under which the bug
is invisible**. Every roster here is a real file, mutated mid-process.

------------------------------------------------------------------------------
THE INVARIANT, QUANTIFIED OVER PRINCIPALS AND NOT OVER CAUSES

    Whenever the roster is not a loadable file with at least one valid entry,
    EVERY principal is denied — whatever made it unloadable.

The quantifier law forbids phrasing this as *"when the file is missing → deny"*. The
next defect arrives through a door nobody enumerated (a bind mount that vanished, a
truncating write, an editor's swap file, a uid change). So the denial is pinned over
every principal and over six independently-broken roster states, each with its own
forcing fixture.

------------------------------------------------------------------------------
THE WRONG BUILDS THESE PINS DISCRIMINATE AGAINST

* **F4, the inherited fail-open** — ``if allowlist: check(...)``. An empty roster
  admits everyone. Pinned at the runtime leg, over every principal, over six states.
* **A silently-shorter list** — a parser that skips one malformed line and admits the
  rest. Pinned by proving a GOOD principal on the same file is denied too.
* **Admission cached with the token.** odoo-code evaluates its allowlist ONLY on the
  cache-miss path, so a revoked principal keeps working for the whole cache TTL. The
  cached-principal fixture drives a cache HIT and demands denial anyway.
* **Reload only at boot.** A build that reads the roster once at startup passes every
  in-memory pin except the mid-process edit — the one the operator actually asked for.
* **Freshness on the MISS path only.** The pre-S5 shape: correct for an uncached
  principal, and it leaves a revoked-but-cached principal admitted until something
  unrelated happens to miss. Killed by
  ``test_a_revoked_principal_with_a_cached_token_is_denied_immediately``, whose fixture
  performs NO intervening miss.
* **Re-reading the whole file on every verification.** Satisfies freshness and puts a
  file read on lore's hottest path. Killed by ``test_an_unchanged_roster_is_not_re_read``.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from _auth_fixtures import (
    OPERATOR_EMAIL,
    OPERATOR_SUBJECT,
    SECOND_PRINCIPAL_EMAIL,
    SECOND_PRINCIPAL_SUBJECT,
    TokeninfoSpy,
    admitted_payload,
    base_config_payload,
    google_access_token,
    hosted_auth_block,
    make_verifier,
    rewrite_roster,
    slug,
    write_roster,
)

# The roster shapes that must ALL deny every principal (design R12: missing,
# unreadable, empty, zero-valid, parse-refused — plus a directory, which is what a
# podman bind mount of a non-existent host path actually leaves behind).
BROKEN_ROSTER_SHAPES = (
    "missing",
    "empty",
    "whitespace-only",
    "comments-only",
    "parse-refused",
    "directory",
)

# A roster line that forges lore's own structured output. Operator-supplied stored
# text, rendered into an ERROR log record a machine may parse.
FORGED_ROSTER_LINE = "``` admin@evil.example event=roster.reloaded entries=99 ok ```"

# A domain-shaped line: always an operator error, never a rule (R7).
DOMAIN_SHAPED_LINE = "firehawktransam.org"

# A third principal, used where a refusal must be shown NOT to dump the whole roster.
THIRD_PRINCIPAL_EMAIL = "marcus.olabode@firehawktransam.org"

# A replacement address with the SAME BYTE LENGTH as SECOND_PRINCIPAL_EMAIL, so a build
# that detects roster change by ``st_size`` alone sees nothing move (M6 / WB41).
SAME_LENGTH_REPLACEMENT = "dana.whitfield@pricepaper.net"

# A COMPATIBILITY spelling of the operator's address: U+FF45 FULLWIDTH LATIN SMALL LETTER
# E. NFKC folds it onto plain ``e``; ``casefold()`` alone does not. It is the only shape
# of input on which the ruled normaliser and a hand-rolled ``casefold().strip()``
# DISAGREE — which is exactly why it is the fixture that proves the two sides share one
# implementation (N7 / WB61c).
FULLWIDTH_OPERATOR_EMAIL = "ejpric\uff45@firehawktransam.org"
assert FULLWIDTH_OPERATOR_EMAIL != OPERATOR_EMAIL, (
    "the compatibility fixture must NOT already equal the ASCII address, or N7 is vacuous"
)
assert len(SAME_LENGTH_REPLACEMENT) == len(SECOND_PRINCIPAL_EMAIL), (
    "the same-length fixture must actually be the same length, or M6 tests nothing"
)

_SUBJECTS = {
    OPERATOR_EMAIL: OPERATOR_SUBJECT,
    SECOND_PRINCIPAL_EMAIL: SECOND_PRINCIPAL_SUBJECT,
    THIRD_PRINCIPAL_EMAIL: "113355779911335577991",
}


class _RosterProbe:
    """A verifier over a real roster file, plus the helpers every pin here needs."""

    def __init__(self, roster: Path, emails_by_token: dict[str, str]) -> None:
        self.roster = roster
        self._emails_by_token = emails_by_token
        self.spy = TokeninfoSpy(responder=self._respond)
        self.verifier = make_verifier(
            roster_path=roster, api_keys=None, http_client=self.spy.client()
        )

    def _respond(self, request: httpx.Request) -> httpx.Response:
        for token, email in self._emails_by_token.items():
            if token.encode() in request.content:
                return httpx.Response(
                    200,
                    json=admitted_payload(
                        email=email, sub=_SUBJECTS.get(email, "119900112233445566778")
                    ),
                )
        return httpx.Response(401)

    def token_for(self, email: str, label: str) -> str:
        """Mint a FRESH, never-verified token for ``email`` (forces a cache MISS)."""
        token = google_access_token(label)
        self._emails_by_token[token] = email
        return token

    async def verify(self, token: str) -> Any:
        """Verify ``token`` through the production verifier."""
        return await self.verifier.verify_token(token)

    async def verify_expecting_a_cache_hit(self, token: str) -> Any:
        """Verify ``token`` and PROVE the verification was served from the cache.

        The S5 ruling makes "denied on the very next verification" the contract, and a
        denial is only interesting if the token was genuinely warm — otherwise the pin
        passes because caching is broken. So the outbound call-count is asserted
        unchanged across the call, which is the only observable that distinguishes a
        cache HIT from a re-validation.
        """
        before = self.spy.call_count
        result = await self.verify(token)
        assert self.spy.call_count == before, (
            f"the verification of this token was NOT a cache hit ("
            f"{self.spy.call_count - before} outbound call(s)); the pin using it would "
            f"pass for the wrong reason"
        )
        return result


@pytest.fixture
def roster_stat_counter(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[Path], int]]:
    """Count ``stat`` calls per path, so the ruled freshness floor is measurable.

    ``pathlib.Path.stat`` resolves ``os.stat`` at call time (verified on this
    interpreter), so patching the module attribute observes both spellings. The spy
    delegates to the real implementation — it measures, it does not simulate.
    """
    real_stat = os.stat
    counts: dict[str, int] = {}

    def _spy(path: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            key = os.fspath(path)
        except TypeError:  # a file descriptor, not a path
            return real_stat(path, *args, **kwargs)
        counts[str(key)] = counts.get(str(key), 0) + 1
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(os, "stat", _spy)
    yield lambda path: counts.get(str(path), 0)


def break_roster(roster: Path, shape: str) -> None:
    """Force one named broken state. Each is a real production accident."""
    if shape == "missing":
        roster.unlink()
    elif shape == "empty":
        roster.write_text("", encoding="utf-8")
    elif shape == "whitespace-only":
        roster.write_text("   \n\t\n\n", encoding="utf-8")
    elif shape == "comments-only":
        roster.write_text("# every principal revoked 2026-07-31\n", encoding="utf-8")
    elif shape == "parse-refused":
        roster.write_text(
            f"{OPERATOR_EMAIL}\n{DOMAIN_SHAPED_LINE}\n{SECOND_PRINCIPAL_EMAIL}\n",
            encoding="utf-8",
        )
    elif shape == "directory":
        roster.unlink()
        roster.mkdir()
    else:  # pragma: no cover - guards the parametrisation itself
        raise AssertionError(f"unknown broken-roster shape {shape!r}")
    if roster.exists() and roster.is_file():
        # Force the mtime forward so the reload is driven by BEHAVIOUR, not by a
        # coarse clock happening to tick between two writes.
        forced = os.stat(roster).st_mtime + 1.0
        os.utime(roster, (forced, forced))


class TestRosterIsLiveRuntimeStateNotBootConfig:
    """THE ACCEPTANCE TEST (design R12, rider a): add and revoke without a restart."""

    async def test_an_uncached_principal_added_mid_process_is_admitted(
        self, tmp_path: Path
    ) -> None:
        # R12's rider (a) verbatim: "an uncached-principal fixture proves the next
        # verification after a roster edit sees the new roster". The newcomer's
        # post-edit token has NEVER been seen, so its verification is a genuine cache
        # MISS — the path that stats and reloads.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        probe = _RosterProbe(roster, {})

        before = probe.token_for(SECOND_PRINCIPAL_EMAIL, "newcomer-before")
        assert await probe.verify(before) is None, (
            "the newcomer must be denied BEFORE the edit, or the pin proves nothing"
        )

        rewrite_roster(roster, OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)

        after = probe.token_for(SECOND_PRINCIPAL_EMAIL, "newcomer-after")
        assert await probe.verify(after) is not None, (
            "a principal added to the roster file mid-process must be admitted on the "
            "next (uncached) verification — no recreate, no rebuild, no restart. This "
            "is the operator requirement the whole substrate exists for."
        )

    async def test_an_uncached_principal_revoked_mid_process_is_denied(
        self, tmp_path: Path
    ) -> None:
        # The direction that matters for security — kill switch #3 in design §10.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        probe = _RosterProbe(roster, {})

        before = probe.token_for(SECOND_PRINCIPAL_EMAIL, "revoked-before")
        assert await probe.verify(before) is not None

        rewrite_roster(roster, OPERATOR_EMAIL)

        after = probe.token_for(SECOND_PRINCIPAL_EMAIL, "revoked-after")
        assert await probe.verify(after) is None, (
            "deleting a principal's line must take effect on the next verification"
        )

    async def test_re_adding_a_principal_re_admits_them(self, tmp_path: Path) -> None:
        # Stated positively so the revocation pins cannot be satisfied by a build that
        # simply latches denial after any roster change.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        probe = _RosterProbe(roster, {})
        warm = probe.token_for(SECOND_PRINCIPAL_EMAIL, "toggled")

        assert await probe.verify(warm) is not None
        rewrite_roster(roster, OPERATOR_EMAIL)
        assert await probe.verify(warm) is None

        rewrite_roster(roster, OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        assert await probe.verify(warm) is not None, (
            "re-adding a principal must re-admit them — a build that latched denial "
            "after the first roster change would pass every revocation pin above"
        )


class TestRevocationIsEffectiveOnTheVeryNextVerification:
    """S5 (operator ruling, 2026-07-31) — there is NO residual window.

    ⚠ THIS CLASS REPLACES A PIN THAT ASSERTED THE OPPOSITE. An earlier revision of this
    contract carried ``TestTheResidualWindowIsAKnownBound``, which pinned the hole OPEN
    on the strength of design §3-R12's *"one ``stat`` per cache-MISS"* wording. The
    operator has overruled that wording — it was a performance floor, never a licence to
    cap revocation speed — and design §9 group 1 had carried the strong form all along
    (*"revoked-while-token-cached principal denied on the next request (cache-hit
    fixture)"*). The design contradicted itself; the strong form wins. The old pin is
    DELETED rather than left in place, because a pin asserting a hole that is now closed
    is a false statement about the system, and its "if you closed this deliberately"
    message would be actively misleading: the closure IS deliberate.

    MUTATION RIDER (the builder owes the receipt, per design R12 rider c and
    ``scripts/mutation_proof.py`` — expected-RED ids declared from ``--collect-only``
    BEFORE the run, diffed BOTH ways):

        mutation: move the roster ``stat`` to the token-cache MISS path only
        expected RED:
          …::TestRevocationIsEffectiveOnTheVeryNextVerification::
              test_a_revoked_principal_with_a_cached_token_is_denied_immediately
          …::TestRosterFreshnessOnEveryVerification::
              test_every_verification_stats_the_roster_including_cache_hits
        expected GREEN (they must NOT move — a mutation that reds everything proves
        nothing about WHICH property is guarded):
          …::TestRosterIsLiveRuntimeStateNotBootConfig::
              test_an_uncached_principal_revoked_mid_process_is_denied
          …::TestRosterFreshnessOnEveryVerification::test_an_unchanged_roster_is_not_re_read
    """

    async def test_a_revoked_principal_with_a_cached_token_is_denied_immediately(
        self, tmp_path: Path
    ) -> None:
        # THE PIN THE S5 RULING EXISTS FOR, and the one that discriminates hardest.
        # odoo-code evaluates its allowlist ONLY on the cache-miss path, so a cached
        # token outlives revocation by the whole cache TTL. Here the revoked
        # principal's token is DELIBERATELY warm and NOTHING ELSE HAPPENS between the
        # operator's edit and the denial — no other principal, no unrelated miss, no
        # restart. The next verification is the first verification, and it must deny.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        probe = _RosterProbe(roster, {})
        warm = probe.token_for(SECOND_PRINCIPAL_EMAIL, "warm")

        assert await probe.verify(warm) is not None
        rewrite_roster(roster, OPERATOR_EMAIL)

        # ``verify_expecting_a_cache_hit`` asserts ZERO outbound calls across this
        # verification. That is the control: without it the pin would also pass on a
        # build that simply re-validates every token with Google, where the denial says
        # nothing at all about the roster.
        assert await probe.verify_expecting_a_cache_hit(warm) is None, (
            "a principal whose token is CACHED must be denied on the VERY NEXT "
            "verification after their line is removed. Admission is re-evaluated on "
            "every verification against the live in-memory roster; the token cache "
            "caches GOOGLE's verdict, never admission."
        )

    async def test_the_token_cache_is_not_flushed_by_a_roster_edit(
        self, tmp_path: Path
    ) -> None:
        # THE SEPARATION, pinned as its own property. A build can pass the pin above by
        # flushing the token cache whenever the roster changes — which is a DIFFERENT
        # (and much weaker) mechanism: it re-validates every live token with Google on
        # every roster edit, i.e. a self-inflicted thundering herd triggered by an
        # operator's text editor. The two caches must stay separate: a still-listed
        # principal's warm token must survive an unrelated roster edit with ZERO
        # outbound calls.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        probe = _RosterProbe(roster, {})
        survivor = probe.token_for(OPERATOR_EMAIL, "survivor")

        assert await probe.verify(survivor) is not None

        # Somebody ELSE is revoked. The survivor's Google verdict is untouched by that.
        rewrite_roster(roster, OPERATOR_EMAIL)

        assert await probe.verify_expecting_a_cache_hit(survivor) is not None, (
            "a still-listed principal must stay admitted across an unrelated roster "
            "edit, and from CACHE — the roster governs admission, not Google's verdict"
        )

    async def test_a_re_added_principal_is_re_admitted_from_cache_immediately(
        self, tmp_path: Path
    ) -> None:
        # The other direction, also with no intervening miss and no outbound call: the
        # operator fixes a mistaken revocation and the principal works again at once.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        probe = _RosterProbe(roster, {})
        warm = probe.token_for(SECOND_PRINCIPAL_EMAIL, "restored")

        assert await probe.verify(warm) is not None
        rewrite_roster(roster, OPERATOR_EMAIL)
        assert await probe.verify_expecting_a_cache_hit(warm) is None

        rewrite_roster(roster, OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        assert await probe.verify_expecting_a_cache_hit(warm) is not None, (
            "re-adding the line must re-admit on the very next verification, still "
            "from cache — the roster edit is the only state that changed"
        )

    async def test_a_roster_that_goes_empty_denies_a_cached_principal_immediately(
        self, tmp_path: Path
    ) -> None:
        # F4 meets S5: the fastest per-principal kill switch in design §10 is emptying
        # the file, and it must reach a warm token on the next call with no help.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        probe = _RosterProbe(roster, {})
        warm = probe.token_for(OPERATOR_EMAIL, "kill-switch")

        assert await probe.verify(warm) is not None
        break_roster(roster, "empty")
        assert await probe.verify_expecting_a_cache_hit(warm) is None


class TestRosterChangeDetectionSurvivesASameLengthEdit:
    """M6 / WB41 — every shipped revocation fixture changes the file's LENGTH."""

    async def test_swapping_one_address_for_another_of_equal_length_revokes(
        self, tmp_path: Path
    ) -> None:
        # An operator replacing one principal with another — the ordinary membership
        # edit, not an exotic one — can leave the byte count unchanged. A build whose
        # change detection is keyed on ``st_size`` then never reloads, and the departed
        # principal keeps read access to the whole corpus indefinitely.
        #
        # ⚠ THE FIXTURE IS THE PIN. Every other revocation fixture in this module
        # DELETES a line, so the size always moves and a size-keyed build passes them
        # all. This one asserts the size did NOT move before asserting the revocation.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        probe = _RosterProbe(roster, {})
        warm = probe.token_for(SECOND_PRINCIPAL_EMAIL, "same-length")
        assert await probe.verify(warm) is not None

        before = roster.stat()
        roster.write_text(
            "# lore hosted-read allowlist — one Google identity per line.\n"
            "# Revoke by deleting a line; effective on the next verification.\n\n"
            f"{OPERATOR_EMAIL}\n{SAME_LENGTH_REPLACEMENT}\n",
            encoding="utf-8",
        )
        forced = max(time.time(), before.st_mtime + 1.0)
        os.utime(roster, (forced, forced))
        assert roster.stat().st_size == before.st_size, (
            "the fixture must leave the file SIZE unchanged, or it is exercising the "
            "size-changed path that every other revocation pin already covers"
        )

        assert await probe.verify_expecting_a_cache_hit(warm) is None, (
            "a principal replaced by a DIFFERENT address of the same byte length must "
            "still be revoked. Change detection keyed on st_size alone never reloads, "
            "and the departed principal keeps access indefinitely."
        )

    async def test_the_replacement_principal_is_admitted(self, tmp_path: Path) -> None:
        # The CONTROL: the same-length edit must be seen in BOTH directions. A build
        # that reloaded but then admitted nobody would pass the pin above.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        probe = _RosterProbe(roster, {})
        assert await probe.verify(probe.token_for(OPERATOR_EMAIL, "pre-swap")) is not None

        before = roster.stat()
        roster.write_text(
            "# lore hosted-read allowlist — one Google identity per line.\n"
            "# Revoke by deleting a line; effective on the next verification.\n\n"
            f"{OPERATOR_EMAIL}\n{SAME_LENGTH_REPLACEMENT}\n",
            encoding="utf-8",
        )
        forced = max(time.time(), before.st_mtime + 1.0)
        os.utime(roster, (forced, forced))

        newcomer = probe.token_for(SAME_LENGTH_REPLACEMENT, "post-swap")
        assert await probe.verify(newcomer) is not None


class TestRosterFreshnessOnEveryVerification:
    """S5's ruled mechanism: ``stat`` on EVERY verification; re-READ only on change."""

    async def test_every_verification_stats_the_roster_including_cache_hits(
        self, tmp_path: Path, roster_stat_counter: Callable[[Path], int]
    ) -> None:
        # The S5 ruling as a mechanism pin. Under the pre-S5 shape (stat on the MISS
        # path only) the count stops growing after the first verification, which is
        # exactly the build that leaves a revoked-but-cached principal admitted.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        probe = _RosterProbe(roster, {})
        token = probe.token_for(OPERATOR_EMAIL, "hot")

        assert await probe.verify(token) is not None
        after_first = roster_stat_counter(roster)
        assert after_first >= 1, "the first verification must stat the roster"

        repeats = 5
        for _ in range(repeats):
            assert await probe.verify_expecting_a_cache_hit(token) is not None
        grew_by = roster_stat_counter(roster) - after_first
        assert grew_by >= repeats, (
            f"{repeats} cache HITs grew the roster stat count by only {grew_by}. "
            f"S5 rules the roster stat'd on EVERY verification — a build that stats on "
            f"the MISS path only leaves a revoked principal admitted until something "
            f"unrelated happens to miss."
        )

    async def test_an_unchanged_roster_is_not_re_read(self, tmp_path: Path) -> None:
        # The ONE performance property that survives S5 (design R12: "full re-read only
        # when mtime changed"). The instrument is implementation-agnostic on purpose —
        # it does not spy on ``open``/``read_text``/``read_bytes``, because which one the
        # build uses is not the contract. Instead the file is made UNREADABLE while its
        # mtime is left UNTOUCHED (``chmod`` moves ctime, never mtime). A build that
        # only stats and compares mtime keeps serving from the in-memory roster; a build
        # that re-reads on every verification fails the open and denies.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        probe = _RosterProbe(roster, {})
        token = probe.token_for(OPERATOR_EMAIL, "unchanged")
        assert await probe.verify(token) is not None

        mtime_before = os.stat(roster).st_mtime
        roster.chmod(0o000)
        try:
            if os.access(roster, os.R_OK):  # running as root — the state is unreachable
                pytest.skip("cannot make a file unreadable as this user")
            assert os.stat(roster).st_mtime == mtime_before, (
                "the fixture must leave mtime untouched, or it is testing the "
                "change-detected path instead"
            )
            assert await probe.verify_expecting_a_cache_hit(token) is not None, (
                "an UNCHANGED roster must not be re-read — a file read on every "
                "verification is a syscall on lore's hottest path, and design R12 "
                "rules the re-read conditional on the mtime moving"
            )
        finally:
            roster.chmod(0o600)

    async def test_a_changed_roster_IS_re_read(self, tmp_path: Path) -> None:
        # The CONTROL for the pin above, and it is essential: a build that NEVER
        # re-reads after the first load would pass ``test_an_unchanged_roster_is_not_
        # re_read`` perfectly and ignore every operator edit forever.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        probe = _RosterProbe(roster, {})
        token = probe.token_for(SECOND_PRINCIPAL_EMAIL, "changed")
        assert await probe.verify(token) is not None

        rewrite_roster(roster, OPERATOR_EMAIL)
        assert await probe.verify_expecting_a_cache_hit(token) is None


class TestRosterFailsClosedAtRuntime:
    """∀ principal, ∀ broken roster state: DENIED, and LOUDLY (design R11/R12, F4)."""

    @pytest.mark.parametrize("shape", BROKEN_ROSTER_SHAPES)
    async def test_every_principal_is_denied_when_the_roster_is_broken(
        self, tmp_path: Path, shape: str
    ) -> None:
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        probe = _RosterProbe(roster, {})
        first = probe.token_for(OPERATOR_EMAIL, "first")
        second = probe.token_for(SECOND_PRINCIPAL_EMAIL, "second")

        # POSITIVE CONTROL first: both principals are admitted while the roster is
        # healthy, so a denial below is caused by the break, not by the fixture.
        assert await probe.verify(first) is not None
        assert await probe.verify(second) is not None

        # S5: no driver, no intervening miss. Both tokens are WARM, and the denial must
        # reach them on their very next verification — asserted as a cache HIT, which
        # also pins that a broken roster does not send every live token back to Google
        # (an operator's bad edit must not become an outbound stampede).
        break_roster(roster, shape)

        for label, token in (("first", first), ("second", second)):
            assert await probe.verify_expecting_a_cache_hit(token) is None, (
                f"the {label} principal was still admitted with a {shape} roster. An "
                f"unloadable allowlist that skips the check is the inherited fail-open "
                f"(F4); on lore's public endpoint it admits every verified Google "
                f"account on earth."
            )

    @pytest.mark.parametrize("shape", BROKEN_ROSTER_SHAPES)
    async def test_a_never_seen_principal_is_denied_when_the_roster_is_broken(
        self, tmp_path: Path, shape: str
    ) -> None:
        # The same ∀, on the MISS path rather than the cache path — a build could get
        # one right and the other wrong, and only one of them faces the internet first.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        probe = _RosterProbe(roster, {})
        assert await probe.verify(probe.token_for(OPERATOR_EMAIL, "control")) is not None

        break_roster(roster, shape)

        fresh = probe.token_for(OPERATOR_EMAIL, f"fresh-{shape}")
        assert await probe.verify(fresh) is None

    async def test_a_parse_refusal_denies_the_VALID_lines_on_the_same_file(
        self, tmp_path: Path
    ) -> None:
        # The silently-shorter-list build denies only the malformed line's principal
        # and keeps serving the others. This is the pin that kills it, stated as its
        # own case so the failure message says exactly what happened.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL, SECOND_PRINCIPAL_EMAIL)
        probe = _RosterProbe(roster, {})
        assert await probe.verify(probe.token_for(OPERATOR_EMAIL, "pre")) is not None

        break_roster(roster, "parse-refused")

        fresh = probe.token_for(OPERATOR_EMAIL, "post")
        assert await probe.verify(fresh) is None, (
            "a malformed line must refuse the WHOLE roster (R7/R12). Skipping it and "
            "admitting the good lines is a silently-shorter allowlist, and the "
            "operator is never told which principals are actually admitted."
        )

    async def test_an_unreadable_roster_denies_everyone(self, tmp_path: Path) -> None:
        # The mount is `:ro` and the uid mismatched (#132/#134's neighbourhood): the
        # process can see the file and cannot open it.
        #
        # ⚠ READ THIS BESIDE ``TestRosterFreshnessOnEveryVerification::
        # test_an_unchanged_roster_is_not_re_read``, which asserts an unreadable roster
        # KEEPS SERVING. They are not in conflict — they pin the two sides of design
        # R12's mtime rule. Here the mtime MOVED (``rewrite_roster``), so a re-read is
        # owed and its failure must deny. There the mtime did NOT move, so no re-read is
        # owed and the in-memory roster stands. The distinguishing input is the mtime,
        # and both cases are pinned so neither can be "simplified" into the other.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        probe = _RosterProbe(roster, {})
        assert await probe.verify(probe.token_for(OPERATOR_EMAIL, "readable")) is not None

        rewrite_roster(roster, OPERATOR_EMAIL)
        roster.chmod(0o000)
        try:
            if os.access(roster, os.R_OK):  # running as root — the state is unreachable
                pytest.skip("cannot make a file unreadable as this user")
            fresh = probe.token_for(OPERATOR_EMAIL, "unreadable")
            assert await probe.verify(fresh) is None
        finally:
            roster.chmod(0o600)

    @pytest.mark.parametrize("shape", ["missing", "empty", "parse-refused"])
    async def test_a_broken_roster_is_reported_at_ERROR_naming_the_path(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture, shape: str
    ) -> None:
        # LOUD, not silent. A total denial with nothing in the log is indistinguishable
        # from "Google is down" and costs an operator an evening.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        probe = _RosterProbe(roster, {})
        assert await probe.verify(probe.token_for(OPERATOR_EMAIL, "quiet")) is not None

        break_roster(roster, shape)
        with caplog.at_level(logging.ERROR):
            fresh = probe.token_for(OPERATOR_EMAIL, f"loud-{shape}")
            assert await probe.verify(fresh) is None

        errors = [record for record in caplog.records if record.levelno >= logging.ERROR]
        assert errors, f"a {shape} roster produced no ERROR record — the denial is silent"
        rendered = "\n".join(record.getMessage() for record in errors)
        assert str(roster) in rendered or roster.name in rendered, (
            f"the ERROR must name the roster PATH so the operator knows which file to "
            f"fix; message was {rendered!r}"
        )

    async def test_a_healthy_roster_logs_no_ERROR(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # The CONTROL for the loudness pins: a build that logged an ERROR on every
        # verification would satisfy all of them.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        probe = _RosterProbe(roster, {})
        with caplog.at_level(logging.ERROR):
            assert await probe.verify(probe.token_for(OPERATOR_EMAIL, "silent")) is not None
        assert not [record for record in caplog.records if record.levelno >= logging.ERROR]


class TestRosterErrorRendersHostileTextUnambiguously:
    """Operator-supplied roster text reaches a log record — it may not forge one."""

    async def test_a_forged_roster_line_cannot_be_read_as_a_log_event(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # The roster is stored free text. A refusal renders the offending line into an
        # ERROR record a log pipeline parses. A line carrying a backtick FENCE RUN and
        # a key=value payload shaped like lore's own "roster reloaded" event must be
        # rendered unambiguously (repr-quoted, one record) so it cannot inject a fake
        # success event into the very stream reporting the failure.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        probe = _RosterProbe(roster, {})
        assert await probe.verify(probe.token_for(OPERATOR_EMAIL, "pre-forgery")) is not None

        rewrite_roster(roster, OPERATOR_EMAIL, FORGED_ROSTER_LINE)
        with caplog.at_level(logging.ERROR):
            fresh = probe.token_for(OPERATOR_EMAIL, "forgery")
            assert await probe.verify(fresh) is None

        rendered = [record.getMessage() for record in caplog.records]
        forging = [message for message in rendered if "evil.example" in message]
        assert forging, (
            "the refusal must name the offending line — a bare 'roster invalid' leaves "
            "the operator grepping a file they cannot see from inside the container"
        )
        for message in forging:
            assert repr(FORGED_ROSTER_LINE) in message, (
                f"the hostile line must be repr-quoted so its backtick run and "
                f"key=value payload cannot be parsed as message structure; got "
                f"{message!r}"
            )
            assert "\n" not in message, (
                "the record must stay ONE line: a multi-line message lets "
                "operator-supplied text occupy a line of its own and be read as a "
                "separate event"
            )

    async def test_the_error_does_not_dump_the_whole_roster(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        # The roster is a list of everyone with access to the corpus. A refusal needs
        # the OFFENDING line to be diagnosable; it does not need — and must not emit —
        # the other principals' addresses into a log aggregator.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        probe = _RosterProbe(roster, {})
        assert await probe.verify(probe.token_for(OPERATOR_EMAIL, "pre-dump")) is not None

        rewrite_roster(
            roster,
            OPERATOR_EMAIL,
            SECOND_PRINCIPAL_EMAIL,
            THIRD_PRINCIPAL_EMAIL,
            DOMAIN_SHAPED_LINE,
        )
        with caplog.at_level(logging.ERROR):
            fresh = probe.token_for(OPERATOR_EMAIL, "dump")
            assert await probe.verify(fresh) is None

        rendered = "\n".join(record.getMessage() for record in caplog.records)
        assert DOMAIN_SHAPED_LINE in rendered, "the OFFENDING line must be named"
        assert THIRD_PRINCIPAL_EMAIL not in rendered, (
            "a roster refusal must not dump the other principals' addresses into the "
            "log stream — the file is a membership list, not a diagnostic payload"
        )


class TestRosterNormalisationAtTheLoremasterSeam:
    """One normaliser, both sides of the seam — proved where the two actually meet."""

    async def test_a_capitalised_roster_line_admits_the_lowercase_google_email(
        self, tmp_path: Path
    ) -> None:
        # The producer↔consumer seam: the operator types capitals, Google reports
        # lowercase. Mocks on each side individually would not catch a build that
        # normalises only one.
        roster = write_roster(tmp_path / "lore-secrets", "EJPrice@FireHawkTransAm.ORG")
        probe = _RosterProbe(roster, {})
        assert await probe.verify(probe.token_for(OPERATOR_EMAIL, "casefold")) is not None

    async def test_a_roster_line_with_stray_whitespace_still_admits(
        self, tmp_path: Path
    ) -> None:
        directory = tmp_path / "lore-secrets"
        directory.mkdir(parents=True)
        roster = directory / "lore-allowed-emails.txt"
        roster.write_text(f"   {OPERATOR_EMAIL}\t\n", encoding="utf-8")
        probe = _RosterProbe(roster, {})
        assert await probe.verify(probe.token_for(OPERATOR_EMAIL, "whitespace")) is not None

    async def test_a_COMPATIBILITY_form_google_email_matches_an_ascii_roster_line(
        self, tmp_path: Path
    ) -> None:
        # N7 / WB61c — ⚑ THE MUTATION PROOF THIS SEAM WAS OWED, as behaviour.
        # ``test_a_capitalised_roster_line_admits_the_lowercase_google_email`` differs
        # from a hand-rolled ``.casefold().strip()`` on NO input: ASCII capitals fold
        # identically either way. So every seam fixture in this module was blind to a
        # private copy, and a build that hand-rolled BOTH loremaster-side normalisation
        # sites passed all 448 pins. (Breaking either site ALONE is invisible because the
        # other re-normalises — which is why only the both-sites build is the honest
        # wrong build, and why single-site mutation proofs would have said "equivalent".)
        #
        # The ONLY inputs that distinguish the ruled normaliser (NFKC → casefold → strip)
        # from a private copy are COMPATIBILITY forms. U+FF45 FULLWIDTH LATIN SMALL
        # LETTER E folds onto plain ``e`` under NFKC and not under casefold alone.
        #
        # ⚠ BOUNDED HONESTLY: Google does not normally emit compatibility spellings, so
        # this is a ONE-IMPLEMENTATION violation with a bounded live consequence, not an
        # authentication bypass. It is pinned because it is #102's exact shape — routing
        # is not sharing, and the only instrument that tells them apart is a mutation the
        # contract must actually perform.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        probe = _RosterProbe(roster, {})
        token = probe.token_for(FULLWIDTH_OPERATOR_EMAIL, "nfkc-seam")
        assert await probe.verify(token) is not None, (
            "Google reported a compatibility (NFKC-foldable) spelling of a LISTED "
            "address and the principal was denied. A side of the seam that only "
            "casefolds is a private copy wearing the shared name."
        )

    async def test_a_plus_alias_of_a_listed_principal_is_NOT_admitted(
        self, tmp_path: Path
    ) -> None:
        # The DOCUMENTED BOUND (design §5) as behaviour at the seam: dot/plus aliasing
        # is not stripped, so ``ejprice+lore@…`` is a different identity that must be
        # listed separately if it is wanted.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        probe = _RosterProbe(roster, {})
        alias = probe.token_for("ejprice+lore@firehawktransam.org", "plus-alias")
        assert await probe.verify(alias) is None

    async def test_an_unlisted_principal_at_a_listed_domain_is_NOT_admitted(
        self, tmp_path: Path
    ) -> None:
        # R7 at the seam: lore has NO domain rule. Being a colleague of an allowlisted
        # principal is not admission.
        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        probe = _RosterProbe(roster, {})
        colleague = probe.token_for("someone.new@firehawktransam.org", "colleague")
        assert await probe.verify(colleague) is None


class TestBootRefusesAnUnloadableRoster:
    """The BOOT leg, pinned SEPARATELY from the runtime leg (R11: every leg, each pinned)."""

    def _hosted_config(self, tmp_path: Path, roster: Path) -> Any:
        from loremaster.config import LoreConfig

        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = hosted_auth_block(roster)
        return LoreConfig.model_validate(payload)

    def test_a_hosted_config_with_a_healthy_roster_resolves_to_hosted_oauth(
        self, tmp_path: Path
    ) -> None:
        # POSITIVE CONTROL for every boot refusal below.
        from loremaster.config import resolve_posture

        from lorerunes import Posture

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        assert resolve_posture(self._hosted_config(tmp_path, roster)) is Posture.HOSTED_OAUTH

    @pytest.mark.parametrize(
        "shape", ["missing", "empty", "whitespace-only", "comments-only", "parse-refused"]
    )
    def test_boot_refuses_when_the_roster_does_not_load_with_at_least_one_entry(
        self, tmp_path: Path, shape: str
    ) -> None:
        # Design R12: "HOSTED_OAUTH refuses to boot unless the roster file loads with
        # ≥1 valid entry (refusal names the path and the reason)". A container that
        # boots with an empty allowlist and 403s everyone is a silent outage; one that
        # boots and admits everyone is a breach. Refusing is the only honest option.
        from loremaster.config import PostureConfigError, resolve_posture

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        config = self._hosted_config(tmp_path, roster)
        break_roster(roster, shape)

        with pytest.raises(PostureConfigError) as excinfo:
            resolve_posture(config)
        assert str(roster) in str(excinfo.value), (
            f"the boot refusal must name the roster PATH; got {str(excinfo.value)!r}"
        )

    def test_the_boot_refusal_carries_no_credential_material(self, tmp_path: Path) -> None:
        # Laundered: uvicorn prints this at startup, UNREDACTED, into whatever collects
        # container logs. The path and the reason are the whole payload.
        from loremaster.config import PostureConfigError, resolve_posture

        roster = write_roster(tmp_path / "lore-secrets", OPERATOR_EMAIL)
        config = self._hosted_config(tmp_path, roster)
        break_roster(roster, "missing")
        with pytest.raises(PostureConfigError) as excinfo:
            resolve_posture(config)
        message = str(excinfo.value)
        assert "ya29." not in message
        assert "LORE_KEY_" not in message, (
            "an env-var NAME for an api key has no business in a roster diagnostic"
        )

    def test_a_loopback_config_with_no_auth_block_needs_no_roster(
        self, tmp_path: Path
    ) -> None:
        # The CONTROL that keeps the boot gate from being a blanket refusal: today's
        # default deployment carries no auth block at all and must resolve cleanly.
        from loremaster.config import LoreConfig, resolve_posture

        from lorerunes import Posture

        config = LoreConfig.model_validate(base_config_payload(slug(), tmp_path / "live"))
        assert resolve_posture(config) is Posture.LOOPBACK

    def test_a_lan_bearer_config_needs_no_roster(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Second control, on the OTHER non-hosted posture: the roster gate must be
        # scoped to HOSTED_OAUTH and must not start demanding a file from the existing
        # LAN deployment.
        from _auth_fixtures import (
            API_KEY_ENV_LAN_CLIENT,
            API_KEY_ENV_LOCAL_AGENT,
            API_KEY_VALUE_LAN_CLIENT,
            API_KEY_VALUE_LOCAL_AGENT,
            lan_bearer_auth_block,
        )
        from loremaster.config import LoreConfig, resolve_posture

        from lorerunes import Posture

        monkeypatch.setenv(API_KEY_ENV_LOCAL_AGENT, API_KEY_VALUE_LOCAL_AGENT)
        monkeypatch.setenv(API_KEY_ENV_LAN_CLIENT, API_KEY_VALUE_LAN_CLIENT)
        payload = base_config_payload(slug(), tmp_path / "live")
        payload["auth"] = lan_bearer_auth_block()
        assert resolve_posture(LoreConfig.model_validate(payload)) is Posture.LAN_BEARER
