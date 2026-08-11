"""ADVERSARIAL in-memory ``FakeFindingLedger`` — the P8b finding-ledger
fake-vs-real parity pin (mirrors the house style of ``_task_fakes.py``).

``test_findings.py``'s own ``finding_ledger_factory`` fixture is parametrized
over BOTH the real SurrealDB-backed ``FindingLedger`` and this fake, so the exact
same contract suite runs against both. That parity pin is only as good as this
fake is UNFRIENDLY: a fake that quietly promises more than production (a lucky
non-atomic number mint, a shared mutable ``Finding`` reference, ids a consumer
could sort by) would let a consumer bug pass green here and then break for real.
Each adversarial property below exists to catch one such bug:

1. Finding ids are opaque ``uuid4().hex`` strings, never ``finding-1``/``#1``
   shapes a consumer could accidentally sort or index by — the STABLE
   human-addressable handle is the ``number``, addressed explicitly, never the id.
2. Every public ``async`` method opens with ``await asyncio.sleep(0)`` — a real
   event-loop yield point, so concurrent callers (``TestConcurrentNumbering`` /
   ``TestConcurrentTransitions``) actually interleave the way two live
   socket-backed calls would, rather than running start-to-finish back-to-back
   because nothing ever awaited.
3. :meth:`FakeFindingLedger.report` yields (``sleep(0)``) BEFORE it mints the
   next number, then runs the mint-and-store with NO ``await`` between the
   counter read and the write. The race window is honestly open (two racers can
   both reach the mint before either writes); the mint itself is honestly atomic
   (asyncio's cooperative single-thread scheduling means nothing preempts a
   stretch with no ``await`` in it) — the same shape production's single
   ``BEGIN … COMMIT`` counter bump gets from the server, not a fake-only accident.
   The same discipline guards :meth:`_transition`'s compare-and-set.
4. Every returned :class:`~loremaster.findings.Finding` /
   :class:`~loremaster.findings.ReportResult` is a FRESH ``model_copy(deep=True)``
   — production deserializes a fresh row on every call; a consumer that mutates a
   returned ``Finding`` (e.g. appends to ``provenance['events']``) must never
   corrupt this fake's store.
5. :meth:`query` returns rows ordered by ``number`` ASC by EXPLICITLY sorting on
   ``number`` — never by relying on the backing ``dict``'s insertion order — so a
   consumer whose "enumerate-in-order" assumption secretly rode insertion order is
   tested against the real contract (ordered by the stable number) here too.

Fidelity: :class:`~loremaster.findings.Finding`,
:class:`~loremaster.findings.ReportResult`,
:class:`~loremaster.findings.FindingStatus` and every exception are IMPORTED from
``loremaster.findings`` — never redefined here, so this fake can never drift from
the real value objects it stands in for. The four-status vocabulary and the
legal-transition matrix are the contract ``test_findings.py`` itself pins; this
file keeps its OWN copy of both (exactly as ``test_findings.py`` does), because a
fake importing its state machine FROM the test it is graded against would be
circular, not independent, verification.

Two :class:`FakeFindingLedger` instances built over the SAME
:class:`FakeFindingDatabase` are two independent "connections" to one store —
mirroring the single SurrealDB database every real ``FindingLedger`` handle
shares — which is what makes ``TestConcurrentNumbering`` (racing reporters),
``TestConcurrentTransitions`` (racing resolvers) and ``TestFleetVisibility`` (a
second handle reading the first's writes) meaningful against this fake at all.

PKT-06 addendum (rollup): :meth:`filed_since` reuses the ALREADY-DECLARED
``created_at`` field — unlike the task ledger's ``updated_at`` addendum, no
new field needs to be injected onto ``Finding`` for this leg, since findings
have always carried a creation timestamp.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from loremaster.findings import (
    ChainHead,
    Finding,
    FindingChainCycleError,
    FindingNotFoundError,
    FindingStatus,
    IllegalTransitionError,
    ReportResult,
)

# --- the domain's status vocabulary + legal-transition matrix ---------------
# A DELIBERATE local copy of the same vocabulary/matrix ``test_findings.py`` pins
# — an independent implementation of the contract, not a shortcut that imports
# the test's own fixtures. Typed against ``FindingStatus`` (imported, never
# redefined) so every constant here is statically a legal ``Finding.status`` value.
STATUS_OPEN: FindingStatus = "open"
STATUS_ACKNOWLEDGED: FindingStatus = "acknowledged"
STATUS_RESOLVED: FindingStatus = "resolved"
STATUS_WONTFIX: FindingStatus = "wontfix"

ALL_STATUSES: frozenset[FindingStatus] = frozenset(
    {STATUS_OPEN, STATUS_ACKNOWLEDGED, STATUS_RESOLVED, STATUS_WONTFIX}
)

# The full legal transition matrix (verbatim shape of the contract's own
# ``LEGAL_TRANSITIONS``): everything NOT listed here is illegal, including every
# edge out of a terminal status (``resolved``/``wontfix``) and every no-op
# self-edge.
LEGAL_TRANSITIONS: frozenset[tuple[FindingStatus, FindingStatus]] = frozenset(
    {
        (STATUS_OPEN, STATUS_ACKNOWLEDGED),
        (STATUS_OPEN, STATUS_RESOLVED),
        (STATUS_OPEN, STATUS_WONTFIX),
        (STATUS_ACKNOWLEDGED, STATUS_RESOLVED),
        (STATUS_ACKNOWLEDGED, STATUS_WONTFIX),
    }
)

DEFAULT_KIND = "friction"
DEFAULT_QUERY_LIMIT = 100


@dataclass
class _FakeFindingActivityWindow:
    """Duck-typed stand-in for the not-yet-built ``loremaster.findings.
    FindingActivityWindow`` — ``rows``/``total``, nothing more (mirrors
    ``_task_fakes._FakeTaskActivityWindow``; never imports the production
    class, which does not exist yet).
    """

    rows: list[Finding]
    total: int


@dataclass
class FakeFindingDatabase:
    """The shared in-memory finding table two or more ``FakeFindingLedger``
    handles read/write, plus the monotonic number counter they share.

    Mirrors the single SurrealDB database (and its ``finding_counter`` row) every
    real ``FindingLedger`` connection shares: build several
    :class:`FakeFindingLedger` instances over the SAME
    :class:`FakeFindingDatabase` and they behave like several independent sessions
    against one fleet-visible store (the exact topology
    ``TestConcurrentNumbering`` / ``TestFleetVisibility`` require).
    """

    findings: dict[str, Finding] = field(default_factory=dict)
    # The monotonic counter the server-side ``finding_counter`` row stands in for;
    # bumped atomically inside :meth:`FakeFindingLedger.report`'s no-await mint.
    next_number: int = 0


def _utc_now() -> datetime:
    """A tz-aware UTC timestamp — every stamped time in this fake uses this."""
    return datetime.now(UTC)


class FakeFindingLedger:
    """ADVERSARIAL in-memory stand-in for :class:`~loremaster.findings.FindingLedger`.

    See the module docstring for the deliberate adversarial behaviours. Every
    method's PUBLIC surface (name, parameters, return type, raised exceptions)
    matches :class:`~loremaster.findings.FindingLedger` exactly; only the storage
    is a plain in-memory dict rather than a SurrealDB connection.
    """

    def __init__(self, *, db: FakeFindingDatabase | None = None) -> None:
        self.db = db if db is not None else FakeFindingDatabase()

    # -- lifecycle ----------------------------------------------------------

    async def ensure_ready(self) -> None:
        """No-op (the fake holds no connection to establish)."""
        await asyncio.sleep(0)

    async def close(self) -> None:
        """No-op (the fake holds no connection to close)."""
        await asyncio.sleep(0)

    # -- internal helpers ---------------------------------------------------

    def _resolve(self, id_or_number: int | str) -> Finding:
        """The LIVE (mutable, store-owned) finding addressed by an id OR a number.

        An ``int`` addresses by the stable number; anything else by the opaque id.
        Never returned directly — every public method hands back a
        ``model_copy(deep=True)`` of whatever this returns, so the store's own
        reference is never exposed for a caller to accidentally corrupt.
        """
        if isinstance(id_or_number, int) and not isinstance(id_or_number, bool):
            for finding in self.db.findings.values():
                if finding.number == id_or_number:
                    return finding
            raise FindingNotFoundError(f"no finding addressed by number {id_or_number!r}")
        by_id = self.db.findings.get(str(id_or_number))
        if by_id is None:
            raise FindingNotFoundError(f"no finding addressed by id {id_or_number!r}")
        return by_id

    def _successors(self, finding_id: str) -> list[Finding]:
        """EVERY finding that supersedes ``finding_id`` (its chain successors).

        A finding X's successor is a finding whose ``supersedes`` names X. Ordered
        by ``number`` ASC so ``[0]`` is the deterministic lowest-numbered branch the
        walk follows and ``[1:]`` are the sibling arms of a FORK it surfaces —
        mirroring the real ledger's ``ORDER BY number ASC`` (never a ``LIMIT 1``, so
        the higher-numbered arm stays visible).
        """
        successors = [
            finding for finding in self.db.findings.values() if finding.supersedes == finding_id
        ]
        return sorted(successors, key=lambda finding: finding.number)

    # -- report / read ------------------------------------------------------

    async def report(
        self,
        subject: str,
        body: str,
        *,
        kind: str = DEFAULT_KIND,
        area: str,
        category: str,
        created_by: str,
        supersedes: int | str | None = None,
    ) -> ReportResult:
        # Refuse an empty/whitespace area or category BEFORE any yield or mint —
        # the ledger-side guard mirrored to parity (audit-findings #2): the real
        # ledger raises ValueError here before the store round-trip, so the fake
        # must too, else the parity pin would let a caller bug pass green on the
        # fake and break for real.
        for field_name, field_value in (("area", area), ("category", category)):
            if not field_value.strip():
                raise ValueError(
                    f"finding {field_name} must be a non-empty, non-whitespace "
                    f"string, got {field_value!r}"
                )
        # The race window is honestly OPEN before the mint (adversarial property
        # 3): two concurrent reporters can both reach this point before either
        # bumps the counter.
        await asyncio.sleep(0)
        supersedes_id: str | None = None
        if supersedes is not None:
            # Resolve (and validate existence of) the superseded target BEFORE the
            # mint, with NO ``await`` between here and the store write.
            supersedes_id = self._resolve(supersedes).id
        # --- the atomic mint: NO ``await`` between counter read and write ---
        self.db.next_number += 1
        number = self.db.next_number
        finding_id = uuid4().hex  # opaque, non-sequential (adversarial property 1)
        now = _utc_now()
        finding = Finding(
            id=finding_id,
            number=number,
            kind=kind,
            status=STATUS_OPEN,
            subject=subject,
            body=body,
            area=area,
            category=category,
            created_by=created_by,
            created_at=now,
            supersedes=supersedes_id,
            provenance={"created_by": created_by, "created_at": now.isoformat(), "events": []},
        )
        self.db.findings[finding_id] = finding
        # --- end atomic mint ---
        return ReportResult(id=finding_id, number=number)

    async def get(self, id_or_number: int | str) -> Finding:
        await asyncio.sleep(0)
        return self._resolve(id_or_number).model_copy(deep=True)

    async def query(
        self,
        *,
        status: str | None = None,
        kind: str | None = None,
        area: str | None = None,
        limit: int = DEFAULT_QUERY_LIMIT,
    ) -> list[Finding]:
        await asyncio.sleep(0)
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"limit must be a positive integer, got {limit!r}")
        rows = list(self.db.findings.values())
        if status is not None:
            rows = [finding for finding in rows if finding.status == status]
        if kind is not None:
            rows = [finding for finding in rows if finding.kind == kind]
        if area is not None:
            rows = [finding for finding in rows if finding.area == area]
        # Enumerate-in-order: sort by the STABLE number ASC (adversarial property
        # 5), never the dict's insertion order.
        rows.sort(key=lambda finding: finding.number)
        return [finding.model_copy(deep=True) for finding in rows[:limit]]

    async def chain_head(self, id_or_number: int | str) -> ChainHead:
        await asyncio.sleep(0)
        current = self._resolve(id_or_number)
        visited: set[str] = {current.id}
        # The numbers of every sibling successor the deterministic walk skipped —
        # surfaced sorted on the returned ChainHead (mirrors the real ledger).
        fork_successor_numbers: set[int] = set()
        while True:
            successors = self._successors(current.id)
            if not successors:
                # A finding nobody supersedes is its own head.
                return ChainHead(
                    finding=current.model_copy(deep=True),
                    forked=bool(fork_successor_numbers),
                    fork_successor_numbers=sorted(fork_successor_numbers),
                )
            # number-ASC: [0] is the lowest-numbered branch we walk; the rest are
            # the fork siblings we surface but do not follow.
            walked = successors[0]
            for sibling in successors[1:]:
                fork_successor_numbers.add(sibling.number)
            if walked.id in visited:
                raise FindingChainCycleError(
                    f"supersedes chain from finding {current.id!r} contains a cycle "
                    f"(revisited {walked.id!r}) — the finding data is corrupt"
                )
            visited.add(walked.id)
            current = walked

    # -- state machine ------------------------------------------------------

    async def acknowledge(
        self, id_or_number: int | str, actor: str, note: str | None = None
    ) -> Finding:
        # PKT-06 §3: acknowledge gains an optional note, matching resolve/wontfix
        # (the single ``acknowledge`` verb's existing ``_transition`` plumbing
        # already threads ``note`` through — only this call site hardcoded
        # ``None``, dropping a note the dispatcher's batch actions must forward).
        return await self._transition(id_or_number, STATUS_ACKNOWLEDGED, actor, note)

    async def resolve(
        self, id_or_number: int | str, actor: str, note: str | None = None
    ) -> Finding:
        return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)

    async def wontfix(
        self, id_or_number: int | str, actor: str, note: str | None = None
    ) -> Finding:
        return await self._transition(id_or_number, STATUS_WONTFIX, actor, note)

    async def _transition(
        self, id_or_number: int | str, status: str, actor: str, note: str | None
    ) -> Finding:
        # Yield BEFORE the compare-and-set (the race window is honestly open), then
        # run check-and-mutate with NO ``await`` between them.
        await asyncio.sleep(0)
        finding = self._resolve(id_or_number)
        current_status = finding.status
        # --- the compare-and-set: NO ``await`` between check and mutation ---
        legal = status in ALL_STATUSES and (current_status, status) in LEGAL_TRANSITIONS
        if not legal:
            raise IllegalTransitionError(
                f"illegal transition for finding {finding.id!r} from "
                f"{current_status!r} to {status!r}"
            )
        target_status = cast(FindingStatus, status)
        finding.status = target_status
        now = _utc_now()
        event: dict[str, Any] = {
            "actor": actor,
            "action": "transition",
            "to": target_status,
            "at": now.isoformat(),
        }
        if note is not None:
            event["note"] = note
        finding.provenance.setdefault("events", []).append(event)
        # --- end compare-and-set ---
        return finding.model_copy(deep=True)

    # -- annotate (#256) ----------------------------------------------------

    async def annotate(
        self, id_or_number: int | str, actor: str, note: str | None
    ) -> Finding:
        """Append an ``{actor, action:'annotate', at, note}`` event to a finding's
        ``provenance.events`` — changing NOTHING else.

        Independent parity reimplementation of the #256 contract (this fake never
        imports the real ledger's logic): status-PRESERVING (NO legal-transition
        gate — annotate is legal in EVERY status, the property that makes it
        status-orthogonal), ``note`` REQUIRED and non-blank (rejected BEFORE any
        yield/mutate, mirroring :meth:`report`'s area/category guard so the parity
        pin holds), and — like :meth:`_transition` — an atomic append with NO
        ``await`` between the resolve and the mutation, so concurrent annotates
        never clobber one another's events (the server-side ``+= [$event]`` a real
        ``FindingLedger`` gets from the engine, modelled here by asyncio's
        cooperative single-thread scheduling).

        The event carries NO ``to``/status field: an annotate changes no status, so
        a render must have nothing to fabricate a ``-> status`` arrow from (#104).
        """
        if note is None or not note.strip():
            raise ValueError(
                f"finding annotate note must be a non-empty, non-whitespace string, "
                f"got {note!r}"
            )
        # The race window is honestly OPEN before the append, then resolve-and-mutate
        # with NO ``await`` between them (mirrors :meth:`_transition`).
        await asyncio.sleep(0)
        finding = self._resolve(id_or_number)
        # --- the atomic append: NO ``await`` between resolve and mutation ---
        now = _utc_now()
        event: dict[str, Any] = {
            "actor": actor,
            "action": "annotate",
            "at": now.isoformat(),
            "note": note,
        }
        finding.provenance.setdefault("events", []).append(event)
        # --- end atomic append ---
        return finding.model_copy(deep=True)

    # -- rollup (PKT-06) ------------------------------------------------------

    async def filed_since(self, since: datetime, *, limit: int) -> _FakeFindingActivityWindow:
        """The rollup's leg-2 read: findings filed (``created_at``) after ``since``.

        Adversarial (mirrors :meth:`query`'s number-ASC sort discipline and
        ``FakeTaskLedger.updated_since``'s scrambled-storage property): the
        candidate set is built in REVERSE insertion order BEFORE the real
        ``created_at`` ASC sort is applied, so a consumer secretly riding dict
        insertion order breaks here exactly as it would against a real
        ``SELECT`` with no ``ORDER BY`` guarantee.
        """
        await asyncio.sleep(0)
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"limit must be a positive integer, got {limit!r}")
        scrambled = list(reversed(list(self.db.findings.values())))
        matching = [finding for finding in scrambled if finding.created_at > since]
        total = len(matching)
        matching.sort(key=lambda finding: finding.created_at)
        rows = [finding.model_copy(deep=True) for finding in matching[:limit]]
        return _FakeFindingActivityWindow(rows=rows, total=total)
