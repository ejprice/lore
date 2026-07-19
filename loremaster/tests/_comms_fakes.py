"""ADVERSARIAL in-memory fakes for the C1 comms ledgers — ``AgentRegistry`` /
``BriefLedger`` (PKT-28 C1, seam S2).

Mirrors ``_task_fakes.py``'s house style and its documented adversarial
properties, applied to the two NEW comms ledgers rather than re-deriving the
pattern from scratch:

1. :meth:`FakeAgentRegistry.fleet` and :meth:`FakeBriefLedger.coverage` return
   rows in a DETERMINISTIC order that is NOT insertion order (fleet sorts by
   the §6 status/heartbeat rule; coverage's ``behind`` list sorts by agent
   name) — a consumer assuming "the order I built things in" breaks here
   exactly as it would against a real ``SELECT`` with no incidental ordering
   guarantee.
2. Every public ``async`` method opens with ``await asyncio.sleep(0)`` — a
   real event-loop yield point, so concurrent callers (the publish-mint race
   test) actually interleave the way two live socket-backed calls would.
3. :meth:`FakeAgentRegistry.register` yields (``sleep(0)``) BEFORE its
   compare-and-set, then runs the check-and-mutate with NO ``await`` between
   them — the race window is honestly open (two racers can both reach the
   read before either mutates); the mutation itself is honestly atomic
   (asyncio's cooperative single-thread scheduling means nothing can preempt
   a stretch of code with no ``await`` in it) — the same shape production's
   single-transaction ``BEGIN … COMMIT`` gets from the server, not a
   fake-only accident.
3a. :meth:`FakeBriefLedger.publish` is TWO-PHASE, mirroring production's TWO
   separate awaited statements (:meth:`~loremaster.briefs.BriefLedger._mint_version`
   then its CREATE) rather than property 3's single compare-and-set shape: the
   per-name counter bump (the mint) is its OWN no-``await``-between-read-and-write
   span — exactly property 3's idiom, applied to ``FakeBriefDatabase.counters``
   instead of a row — and ONLY AFTER that version is atomically secured does an
   HONEST ``await asyncio.sleep(0)`` open a race window before the brief row is
   written. This is deliberately NOT atomic-by-construction the way an
   unconditional single compare-and-set would be: a fake whose mint reads the
   max of existing rows and only THEN yields before writing (the shape
   production's retired ``_apply_publish`` TOCTOU used) loses updates under
   this same window — see ``REPORT-c1-hardener.md`` for the reintroduced-TOCTOU
   proof. Because the counter bump itself is genuinely atomic, THIS
   implementation's race window is safe: two racers can never observe or mint
   the same ``next_version``.
3b. :meth:`FakeBriefLedger.publish` writes the AUTHOR's self-ack edge
   (``via='publish'``, design doc §5.1 step 2 — v7/finding #98) in the SAME
   no-``await`` span as the brief row, because production writes both
   statements inside ONE ``execute_transaction`` fragment. A fake that
   yielded between the two writes — or wrote the edge in a second, separately
   failable step — would model the build the spec explicitly forbids, and
   would hide exactly the defect the atomicity pins exist to catch.
4. Every returned value object is a FRESH ``model_copy(deep=True))`` —
   production deserializes a fresh row on every call; a consumer that mutates
   a returned object must never corrupt this fake's store.
5. Ids are minted via the SAME deterministic ``uuid5`` recipes the C1 spec
   pins for ``agent``/``brief`` records (never a fake-only opaque
   ``uuid4``), so an id-determinism test is meaningful against BOTH backends.

Adversarial-fake caveat (repo memory, "adversarial test doubles must
reorder/append-failures by default"): this fake implements (1)-(3) above
(reordering + an honestly-open race window) but does NOT implement deliberate
failure injection (no capacity to simulate a dropped connection mid-call) —
matching ``_task_fakes.py``'s own precedent (verified by reading it in full
for this build: it reorders ``query_tasks``/``updated_since`` and opens an
honest race window in ``claim_task``, but carries no fault-injection hook
either). Failure-path coverage for both ledgers rides the REAL-backend
connection-lifecycle tests instead (mirrors ``TestQueryClassifiedErrorPosture``
in ``test_task_ledger.py``), exactly as findings/task failure paths do today.

Fidelity: every value object, ``Literal`` alias, and exception class is
IMPORTED from ``loremaster.agents``/``loremaster.briefs`` — never redefined
here, so this fake can never drift from the real value objects it stands in
for. The status vocabulary and legal-transition matrix ARE re-derived locally
(not imported), exactly as ``_task_fakes.py`` keeps its own copy of
``LEGAL_TRANSITIONS`` — an independent implementation of the contract, not a
shortcut that imports the test's own fixtures.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import cast
from uuid import NAMESPACE_URL, uuid5

from loremaster.agents import (
    Agent,
    AgentFleetWindow,
    AgentIdentityConflictError,
    AgentRegisterResult,
    AgentRosterMember,
    AgentStatus,
    AmbiguousAgentError,
    FleetRoster,
    IllegalAgentStatusError,
    RetiredAgentError,
    UnknownAgentError,
)
from loremaster.briefs import (
    _KNOWN_BRIEFS_CAP,
    AgentRefLike,
    Brief,
    BriefAckResult,
    BriefAckVia,
    BriefBehindEntry,
    BriefCoverage,
    BriefPublishResult,
    UnknownBriefError,
    UnknownBriefVersionError,
)

# --- the domain's status vocabulary + legal-transition matrix ---------------
# A DELIBERATE local copy of the same vocabulary/matrix the test modules pin
# (see ``test_agent_registry.py``'s own ``STATUS_*`` / ``LEGAL_AGENT_TRANSITIONS``
# constants) — an independent implementation of the contract, not a shortcut
# that imports the test's own fixtures.
STATUS_ACTIVE: AgentStatus = "active"
STATUS_IDLE: AgentStatus = "idle"
STATUS_INPUT_REQUIRED: AgentStatus = "input_required"
STATUS_RETIRED: AgentStatus = "retired"

ALL_AGENT_STATUSES: frozenset[AgentStatus] = frozenset(
    {STATUS_ACTIVE, STATUS_IDLE, STATUS_INPUT_REQUIRED, STATUS_RETIRED}
)

LEGAL_AGENT_TRANSITIONS: frozenset[tuple[AgentStatus, AgentStatus]] = frozenset(
    {
        (STATUS_ACTIVE, STATUS_IDLE),
        (STATUS_ACTIVE, STATUS_INPUT_REQUIRED),
        (STATUS_ACTIVE, STATUS_RETIRED),
        (STATUS_IDLE, STATUS_ACTIVE),
        (STATUS_IDLE, STATUS_INPUT_REQUIRED),
        (STATUS_IDLE, STATUS_RETIRED),
        (STATUS_INPUT_REQUIRED, STATUS_ACTIVE),
        (STATUS_INPUT_REQUIRED, STATUS_RETIRED),
    }
)

# Fleet row ordering (spec §6): parked questions first, then active, then idle.
_STATUS_SORT_ORDER: dict[AgentStatus, int] = {
    STATUS_INPUT_REQUIRED: 0,
    STATUS_ACTIVE: 1,
    STATUS_IDLE: 2,
}

# --- the ``briefed.via`` vocabulary (spec §0, v7 — finding #98) -------------
# A DELIBERATE local copy of the closed THREE-value set the schema ASSERTs
# (``surreal_schema._BRIEFED_VIA_VALUES``) — an independent implementation of
# the contract, never an import of production's own tuple (an imported tuple
# makes every "the vocabulary is X" assertion a tautology that can never fail).
VIA_REGISTER = "register"
VIA_EXPLICIT = "explicit"
VIA_PUBLISH = "publish"  # v7: the author's self-ack, written BY ``publish``
BRIEFED_VIA_VALUES: frozenset[str] = frozenset({VIA_REGISTER, VIA_EXPLICIT, VIA_PUBLISH})


def _utc_now() -> datetime:
    """A tz-aware UTC timestamp — every stamped time in these fakes uses this."""
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# AgentRegistry fake
# ---------------------------------------------------------------------------


@dataclass
class FakeAgentDatabase:
    """The shared in-memory ``agent`` table two or more ``FakeAgentRegistry``
    handles read/write — mirrors ``FakeTaskDatabase``.
    """

    agents: dict[str, Agent] = field(default_factory=dict)


class FakeAgentRegistry:
    """ADVERSARIAL in-memory stand-in for :class:`~loremaster.agents.AgentRegistry`.

    See the module docstring for the adversarial properties. Every method's
    PUBLIC surface (name, parameters, return type, raised exceptions) matches
    :class:`~loremaster.agents.AgentRegistry` exactly; only the storage is a
    plain in-memory dict rather than a SurrealDB connection.
    """

    def __init__(self, *, db: FakeAgentDatabase | None = None) -> None:
        self.db = db if db is not None else FakeAgentDatabase()

    # -- lifecycle ------------------------------------------------------------

    async def ensure_ready(self) -> None:
        """No-op (the fake holds no connection to establish)."""
        await asyncio.sleep(0)

    async def close(self) -> None:
        """No-op (the fake holds no connection to close)."""
        await asyncio.sleep(0)

    # -- id + resolution --------------------------------------------------------

    @staticmethod
    def _agent_id(session: str, name: str) -> str:
        """The C1 spec's pinned recipe: ``uuid5(NAMESPACE_URL, f"lore://agent/{session}/{name}")``."""
        return uuid5(NAMESPACE_URL, f"lore://agent/{session}/{name}").hex

    async def _resolve(self, name: str, session: str | None) -> Agent:
        """§0.3 name -> row resolution: direct id lookup with ``session``, else a
        bare-name search over non-retired rows (0 -> unknown, >1 -> ambiguous).
        """
        await asyncio.sleep(0)
        if session is not None:
            agent_id = self._agent_id(session, name)
            agent = self.db.agents.get(agent_id)
            if agent is None:
                raise UnknownAgentError(
                    f"agent {name!r} is not registered — every comms call requires a prior 'register'"
                )
            return agent
        # Bare-name search excludes retired rows (a retired agent never shadows
        # a live same-named agent in another session).
        candidates = [
            agent
            for agent in self.db.agents.values()
            if agent.name == name and agent.status != STATUS_RETIRED
        ]
        if not candidates:
            raise UnknownAgentError(
                f"agent {name!r} is not registered — every comms call requires a prior 'register'"
            )
        if len(candidates) > 1:
            sessions = sorted(candidate.session for candidate in candidates)
            raise AmbiguousAgentError(
                f"agent name {name!r} is registered in sessions "
                f"{', '.join(sessions)} — pass session= to disambiguate"
            )
        return candidates[0]

    # -- register ---------------------------------------------------------------

    async def register(
        self,
        name: str,
        *,
        session: str,
        role: str,
        model: str | None = None,
        spawned_by: str | None = None,
        task_id: str | None = None,
    ) -> AgentRegisterResult:
        # The race window is honestly OPEN before the check (mirrors
        # ``FakeTaskLedger.claim_task``): two concurrent callers can both reach
        # this point before either one mutates.
        await asyncio.sleep(0)
        agent_id = self._agent_id(session, name)
        now = _utc_now()
        # --- the compare-and-set: NO ``await`` between check and mutation ----
        existing = self.db.agents.get(agent_id)
        if existing is None:
            agent = Agent(
                id=agent_id,
                name=name,
                session=session,
                role=role,
                model=model,
                status=STATUS_ACTIVE,
                spawned_by=spawned_by,
                task_id=task_id,
                checkpoint=None,
                last_note=None,
                registered_at=now,
                heartbeat_at=now,
            )
            self.db.agents[agent_id] = agent
            return AgentRegisterResult(agent=agent.model_copy(deep=True), re_registered=False)
        if existing.status == STATUS_RETIRED:
            raise RetiredAgentError(f"agent {name!r} is retired (terminal) — respawns register a fresh name")
        if existing.role != role:
            raise AgentIdentityConflictError(
                f"agent {name!r} is already registered with role {existing.role!r} "
                f"(you sent {role!r}) — names are never reused; register a fresh name "
                f"(e.g. {name + '2'!r})"
            )
        if spawned_by is not None and existing.spawned_by is not None and existing.spawned_by != spawned_by:
            raise AgentIdentityConflictError(
                f"agent {name!r} is already registered with spawned_by "
                f"{existing.spawned_by!r} (you sent {spawned_by!r}) — names are never "
                f"reused; register a fresh name (e.g. {name + '2'!r})"
            )
        # write-once fields, resolved: compared only when BOTH sides carry a
        # concrete value (a first-time incoming value fills a previously-unset
        # field without conflict — see the contract-decision note in the report).
        if spawned_by is not None and existing.spawned_by is None:
            existing.spawned_by = spawned_by
        # mutable fields: overwritten when provided, kept when omitted.
        if model is not None:
            existing.model = model
        if task_id is not None:
            existing.task_id = task_id
        # status resets to active unconditionally (retired already excluded above).
        existing.status = STATUS_ACTIVE
        existing.heartbeat_at = now
        # --- end compare-and-set ---
        return AgentRegisterResult(agent=existing.model_copy(deep=True), re_registered=True)

    # -- read ---------------------------------------------------------------

    async def get_agent(self, name: str, *, session: str | None = None) -> Agent:
        agent = await self._resolve(name, session)
        return agent.model_copy(deep=True)

    # -- heartbeat / status machine ------------------------------------------

    async def touch(
        self,
        name: str,
        *,
        session: str | None = None,
        status: str | None = None,
        note: str | None = None,
    ) -> Agent:
        agent = await self._resolve(name, session)
        if agent.status == STATUS_RETIRED:
            raise RetiredAgentError(f"agent {name!r} is retired (terminal) — respawns register a fresh name")
        if status is not None:
            if status not in ALL_AGENT_STATUSES:
                if status == "orphaned":
                    raise IllegalAgentStatusError(
                        "'orphaned' is derived from heartbeat age at render time, never "
                        f"set; legal statuses: {', '.join(sorted(ALL_AGENT_STATUSES))}"
                    )
                raise IllegalAgentStatusError(
                    f"{status!r} is not a legal agent status; legal statuses: "
                    f"{', '.join(sorted(ALL_AGENT_STATUSES))}"
                )
            target_status: AgentStatus = status  # narrowed by the membership check above
            if target_status != agent.status and (agent.status, target_status) not in LEGAL_AGENT_TRANSITIONS:
                legal_from = sorted(
                    to_status
                    for from_status, to_status in LEGAL_AGENT_TRANSITIONS
                    if from_status == agent.status
                )
                raise IllegalAgentStatusError(
                    f"illegal status transition {agent.status} -> {target_status} for "
                    f"{name!r}; legal from {agent.status}: {', '.join(legal_from)}"
                )
            new_status = target_status
        elif agent.status == STATUS_IDLE:
            # Auto-flip: any comms action by an idle agent flips it active,
            # UNLESS this call carried an explicit status (handled above).
            new_status = STATUS_ACTIVE
        else:
            # input_required NEVER auto-flips; active stays active.
            new_status = agent.status
        agent.status = new_status
        agent.heartbeat_at = _utc_now()
        if note is not None:
            agent.last_note = note
        return agent.model_copy(deep=True)

    # -- fleet ----------------------------------------------------------------

    async def fleet(self, *, session: str | None = None, limit: int) -> AgentFleetWindow:
        await asyncio.sleep(0)
        rows = list(self.db.agents.values())
        if session is not None:
            rows = [agent for agent in rows if agent.session == session]
        retired = [agent for agent in rows if agent.status == STATUS_RETIRED]
        non_retired = [agent for agent in rows if agent.status != STATUS_RETIRED]
        # Deterministic NON-insertion order (adversarial property 1): status
        # group per §6, most-recent heartbeat first within a group.
        non_retired.sort(
            key=lambda agent: (_STATUS_SORT_ORDER[agent.status], -agent.heartbeat_at.timestamp())
        )
        total = len(non_retired)
        limited = non_retired[:limit]
        return AgentFleetWindow(
            rows=[agent.model_copy(deep=True) for agent in limited],
            retired_count=len(retired),
            total_non_retired=total,
        )

    async def roster(self, *, session: str | None = None) -> FleetRoster:
        """Mirrors :meth:`~loremaster.agents.AgentRegistry.roster` exactly:
        a row-UNLIMITED true per-status count (all four statuses present,
        zero-filled when absent) plus the complete non-retired membership.
        """
        await asyncio.sleep(0)
        rows = list(self.db.agents.values())
        if session is not None:
            rows = [agent for agent in rows if agent.session == session]
        status_counts: dict[str, int] = dict.fromkeys(ALL_AGENT_STATUSES, 0)
        for agent in rows:
            status_counts[agent.status] = status_counts.get(agent.status, 0) + 1
        members = [
            AgentRosterMember(
                id=agent.id, name=agent.name, status=agent.status, heartbeat_at=agent.heartbeat_at
            )
            for agent in rows
            if agent.status != STATUS_RETIRED
        ]
        return FleetRoster(members=members, status_counts=status_counts)


# ---------------------------------------------------------------------------
# BriefLedger fake
# ---------------------------------------------------------------------------


@dataclass
class FakeBriefDatabase:
    """The shared in-memory ``brief`` + ``briefed`` store two or more
    ``FakeBriefLedger`` handles read/write — mirrors ``FakeTaskDatabase``.

    ``edges`` is keyed by ``(agent_id, brief_id)`` — a UNIQUE(in, out) idiom —
    so re-acking the SAME (agent, name@version) pair is a no-op, while acking
    two DIFFERENT versions of the same name legitimately coexists as two edges
    (exactly the real ``briefed`` relation's shape, §5.4).

    ``counters`` is the per-name version-mint hot row, keyed by brief NAME —
    mirrors the real store's ``brief_counter`` table
    (:data:`~loremaster.store.surreal_schema.BRIEF_COUNTER_TABLE`): ONE next-int
    entry per name, so publishers of different names never contend (see
    :meth:`FakeBriefLedger.publish`).
    """

    briefs: dict[str, Brief] = field(default_factory=dict)
    edges: dict[tuple[str, str], BriefAckVia] = field(default_factory=dict)
    counters: dict[str, int] = field(default_factory=dict)


class FakeBriefLedger:
    """ADVERSARIAL in-memory stand-in for :class:`~loremaster.briefs.BriefLedger`.

    See the module docstring for the adversarial properties. Every method's
    PUBLIC surface matches :class:`~loremaster.briefs.BriefLedger` exactly;
    only the storage is a plain in-memory dict rather than a SurrealDB
    connection.
    """

    def __init__(self, *, db: FakeBriefDatabase | None = None) -> None:
        self.db = db if db is not None else FakeBriefDatabase()

    # -- lifecycle ------------------------------------------------------------

    async def ensure_ready(self) -> None:
        await asyncio.sleep(0)

    async def close(self) -> None:
        await asyncio.sleep(0)

    # -- id ---------------------------------------------------------------------

    @staticmethod
    def _brief_id(name: str, version: int) -> str:
        """The C1 spec's pinned recipe: ``uuid5(NAMESPACE_URL, f"lore://brief/{name}/{version}")``."""
        return uuid5(NAMESPACE_URL, f"lore://brief/{name}/{version}").hex

    def _known_names(self) -> list[str]:
        return sorted({brief.name for brief in self.db.briefs.values()})

    def _versions_of(self, name: str) -> list[Brief]:
        return [brief for brief in self.db.briefs.values() if brief.name == name]

    def _unknown_name_error(self, name: str) -> UnknownBriefError:
        # Mirrors ``BriefLedger._unknown_brief_error``'s capped/counted
        # known-names clause (v4 audit D2 fix) exactly — an independent
        # implementation of the same contract, not a shortcut import.
        known = self._known_names()
        if not known:
            return UnknownBriefError(
                f"no briefs published yet — lore_comms action=brief_publish creates {name!r} v1"
            )
        shown = known[:_KNOWN_BRIEFS_CAP]
        remainder = len(known) - len(shown)
        names_text = ", ".join(shown)
        if remainder > 0:
            names_text = f"{names_text} (+{remainder} more)"
        return UnknownBriefError(f"unknown brief {name!r}; known briefs: {names_text}")

    # -- publish ----------------------------------------------------------------

    async def publish(
        self,
        name: str,
        body: str,
        *,
        created_by: str,
        note: str | None = None,
        agent_id: str | None = None,
    ) -> BriefPublishResult:
        """Mint + write one version — and, when ``agent_id`` is given, the
        author's SELF-ACK ``briefed`` edge (``via='publish'``) in the SAME
        atomic span (design doc §5.1 step 2, v7 — finding #98).

        ``agent_id`` is the PUBLISHING AGENT's opaque row id (never its
        ``created_by`` display name): the edge is ``agent->briefed->brief``,
        so only a real agent row id can carry it. Omitted (a ledger-level
        caller with no agent row in play) ⇒ no edge, exactly as production's
        RELATE fragment is only composed when an id is supplied.
        """
        # Blank-body rejection is a SCHEMA-level (``_NON_EMPTY_STRING_ASSERT``)
        # concern owned by the S1 DDL slice, not app-validated here — see the
        # report's contract-decisions section. This fake therefore does NOT
        # reject a blank body either, matching production's split.
        await asyncio.sleep(0)
        # --- the mint: an atomic per-name counter bump, NO ``await`` between
        # its read and its write (property 3's idiom, applied to the counter
        # row rather than a whole record) — mirrors production's ONE-statement
        # ``UPSERT brief_counter:⟨name⟩ SET next = (next ?? 0) + 1`` mint
        # (:meth:`~loremaster.briefs.BriefLedger._mint_version`): the engine
        # handles that statement's read-modify-write atomically server-side,
        # so a single no-``await`` span is the FAITHFUL model, not a shortcut.
        # Every racer publishing the SAME name contends here; racers on
        # DIFFERENT names touch different dict keys and never contend.
        next_version = self.db.counters.get(name, 0) + 1
        self.db.counters[name] = next_version
        # --- end mint ---
        brief_id = self._brief_id(name, next_version)
        # An HONEST race window BETWEEN the mint and the row write: production
        # runs the mint and the CREATE as TWO SEPARATE awaited statements, so a
        # concurrent racer's own mint can genuinely interleave right here. This
        # is safe ONLY because ``next_version`` was already secured, uniquely,
        # by the atomic mint above — see the module docstring's property 3a.
        await asyncio.sleep(0)
        brief = Brief(
            id=brief_id,
            name=name,
            version=next_version,
            body=body,
            created_by=created_by,
            note=note,
            created_at=_utc_now(),
        )
        # --- the row + the author's self-ack edge: ONE no-``await`` span -----
        # Production writes both statements inside ONE ``execute_transaction``
        # fragment (§5.1 step 2: "never a second, separately-failable call"),
        # so no reader can ever observe a brief whose author is not acked to
        # it. Modelled faithfully here: nothing may interleave between the two
        # dict writes below. A fake that yielded between them would be
        # simulating the two-write build the spec FORBIDS.
        self.db.briefs[brief_id] = brief
        if agent_id is not None:
            self.db.edges[(agent_id, brief_id)] = cast(BriefAckVia, VIA_PUBLISH)
        # --- end atomic span ---
        return BriefPublishResult(brief=brief.model_copy(deep=True), first_version=next_version == 1)

    # -- read ---------------------------------------------------------------

    async def get_head(self, name: str) -> Brief:
        await asyncio.sleep(0)
        versions = self._versions_of(name)
        if not versions:
            raise self._unknown_name_error(name)
        head = max(versions, key=lambda brief: brief.version)
        return head.model_copy(deep=True)

    async def get_version(self, name: str, version: int) -> Brief:
        await asyncio.sleep(0)
        versions = self._versions_of(name)
        if not versions:
            raise self._unknown_name_error(name)
        for brief in versions:
            if brief.version == version:
                return brief.model_copy(deep=True)
        head_version = max(brief.version for brief in versions)
        raise UnknownBriefVersionError(f"brief {name!r} has no v{version} — head is v{head_version}")

    async def known_names(self) -> list[str]:
        await asyncio.sleep(0)
        return self._known_names()

    # -- ack ---------------------------------------------------------------

    async def ack(
        self,
        *,
        agent_id: str,
        agent_name: str,
        name: str,
        version: int,
        via: str,
    ) -> BriefAckResult:
        await asyncio.sleep(0)
        versions = self._versions_of(name)
        if not versions:
            raise self._unknown_name_error(name)
        target = next((brief for brief in versions if brief.version == version), None)
        head_version = max(brief.version for brief in versions)
        if target is None:
            raise UnknownBriefVersionError(f"brief {name!r} has no v{version} — head is v{head_version}")
        edge_key = (agent_id, target.id)
        already = edge_key in self.db.edges
        if not already:
            # Idempotent RELATE: only ever set on first ack (UNIQUE(in, out)).
            # The value is stored VERBATIM — never normalised into a
            # two-value guess. The retired ``"register" if via == "register"
            # else "explicit"`` coercion silently rewrote any THIRD vocabulary
            # word (v7's ``publish``) into ``explicit``, which would have made
            # this fake structurally incapable of failing a build that recorded
            # the wrong ``via``. Out-of-domain values RAISE here — the fake's
            # stand-in for the schema's own ``ASSERT $value IN [...]``, which
            # is what rejects them against the real store.
            if via not in BRIEFED_VIA_VALUES:
                raise ValueError(
                    f"via {via!r} is not in the briefed vocabulary "
                    f"{sorted(BRIEFED_VIA_VALUES)} (the schema ASSERT rejects it)"
                )
            self.db.edges[edge_key] = cast(BriefAckVia, via)
        stored_via = self.db.edges[edge_key]
        return BriefAckResult(
            name=name,
            version=version,
            head_version=head_version,
            already_acked=already,
            via=stored_via,
        )

    async def acked_version(self, *, agent_id: str, name: str) -> int | None:
        await asyncio.sleep(0)
        versions = [
            self.db.briefs[brief_id].version
            for (edge_agent_id, brief_id) in self.db.edges
            if edge_agent_id == agent_id and self.db.briefs[brief_id].name == name
        ]
        return max(versions) if versions else None

    async def coverage(self, name: str, *, active_agents: Sequence[AgentRefLike]) -> BriefCoverage:
        await asyncio.sleep(0)
        versions = self._versions_of(name)
        if not versions:
            raise self._unknown_name_error(name)
        head_version = max(brief.version for brief in versions)
        roster = list(active_agents)
        behind: list[BriefBehindEntry] = []
        current = 0
        for ref in roster:
            acked = await self.acked_version(agent_id=ref.id, name=name)
            if acked == head_version:
                current += 1
            else:
                behind.append(BriefBehindEntry(agent_name=ref.name, acked_version=acked))
        # Deterministic non-arbitrary order: sort by agent name (adversarial
        # property 1's analogue — never rely on roster/insertion order).
        behind.sort(key=lambda entry: entry.agent_name)
        return BriefCoverage(
            name=name,
            head_version=head_version,
            total_agents=len(roster),
            current_count=current,
            behind=behind,
        )

    async def subscribed_name_skew(
        self, *, agent_id: str, exclude: str
    ) -> list[tuple[str, int, int]]:
        # [pkt02 ref] per-name (name, head, acked) for names this agent is
        # SUBSCRIBED to (has >=1 briefed edge to) with acked < head, excluding
        # ``exclude`` (the standing name, handled separately). Independent
        # implementation over self.db.edges, same idiom as acked_version.
        await asyncio.sleep(0)
        acked_by_name: dict[str, int] = {}
        for (edge_agent_id, brief_id) in self.db.edges:
            if edge_agent_id != agent_id:
                continue
            brief = self.db.briefs[brief_id]
            if brief.name == exclude:
                continue
            current = acked_by_name.get(brief.name)
            if current is None or brief.version > current:
                acked_by_name[brief.name] = brief.version
        result: list[tuple[str, int, int]] = []
        for subscribed_name, acked in acked_by_name.items():
            head = max(brief.version for brief in self._versions_of(subscribed_name))
            if acked < head:
                result.append((subscribed_name, head, acked))
        return result

    async def acked_versions_for_ids(self, agent_ids: Sequence[str], *, name: str) -> dict[str, int]:
        """The bulk, self-contained sibling of :meth:`acked_version` (finding
        #94, REPORT-c1b-contract-9495.md): the ``fleet`` action's fix for a
        per-row ``acked_version()`` loop -- measured 407 store round-trips at
        limit=200. An INDEPENDENT implementation (iterates ``self.db.edges``
        directly, exactly like :meth:`acked_version`/:meth:`coverage` above),
        never a shortcut delegating to production's private
        ``_acked_versions_for_roster`` -- the fake stays able to fail.

        Returns a mapping keyed by acked agent ids ONLY: an id ABSENT is
        unbriefed for ``name`` (mirrors production's
        ``_acked_versions_for_roster`` convention exactly); an id acked at
        multiple versions maps to the MAX. An unknown ``name`` or an empty
        ``agent_ids`` returns ``{}`` -- not an error for a bulk status read.
        """
        await asyncio.sleep(0)
        if not agent_ids:
            return {}
        versions = self._versions_of(name)
        if not versions:
            return {}
        version_by_brief_id = {brief.id: brief.version for brief in versions}
        wanted_ids = set(agent_ids)
        result: dict[str, int] = {}
        for edge_agent_id, brief_id in self.db.edges:
            if edge_agent_id not in wanted_ids:
                continue
            brief_version = version_by_brief_id.get(brief_id)
            if brief_version is None:
                continue  # a briefed edge to a DIFFERENT brief name -- irrelevant here
            current_max = result.get(edge_agent_id)
            if current_max is None or brief_version > current_max:
                result[edge_agent_id] = brief_version
        return result
