"""The ONE row-existence policy: *does this id name a live ROW in this table?*

:meth:`~loremaster.messages.MessageLedger.send` (recipients AND — since #247 — the
SENDER), :meth:`~loremaster.briefs.BriefLedger.publish`/:meth:`~loremaster.briefs.BriefLedger.ack`
and :meth:`~loremaster.tasks.TaskLedger.create_task`/:meth:`~loremaster.tasks.TaskLedger.create_many`
need the SAME decision — *resolve these ids against a table and refuse, naming EVERY
unresolved one, BEFORE any write* — so it is a FUNCTION THEY CALL, never a pattern one
ledger clones from the other (repo law #102: a pattern to clone is a defect to clone; a
doc naming one method as "the reference pattern" got its jitter bug faithfully cloned into
a sibling module).

**Packet 04b-1 GENERALISED it rather than adding a sibling (lead ruling L3).** A
``reject_unknown_tasks`` twin would have been copy #2 of this policy — the #102 shape — so
the decision, the probe and the refusal SENTENCE SKELETON are parameterised by TABLE and
VOCABULARY (:func:`resolve_existing_rows`, :func:`reject_unknown_rows`,
:func:`format_unknown_row_refusal`), and packet 04a's agent entry points
(:func:`reject_unknown_agents`, :func:`format_unknown_agent_refusal`) are thin typed
ADAPTERS over them, so 04a's callers and pins are untouched. Sharing is proved by
MUTATION, never by inspection: replace the shared formatter and BOTH families' served text
must change (``test_blocks_edge.py::TestTheRowExistencePolicyHasONEImplementation``).

It lives in NEITHER ledger module, cloning the :mod:`loremaster.agent_ref` precedent
verbatim: a ledger owning the shared object would force its siblings to import IT,
reintroducing exactly the coupling ``briefs.py``'s *"the ledger never imports its
neighbours"* decoupling law exists to prevent. For the same reason this module imports no
ledger, and its :class:`UnknownRowError` is a BASE each ledger subclasses into its own
domain error rather than an error any ledger owns.

**Why an app-level check exists at all, when the engine ships ``ENFORCED``.** Both are
wanted and neither is redundant (store reference §4, the ``ENFORCED`` adoption table's
error-ergonomics row):

* ``ENFORCED`` guards the TABLE — including the ``INSERT RELATION`` door no check on one
  verb can ever reach — but it reports ONE bad endpoint, as untyped prose, only AFTER the
  write is attempted, aborting the whole transaction. And the store seam's error hygiene
  (ledger #31) withholds even that: a caller receives ``statement N of M was rejected
  (unspecified rejection); see the server log``.
* So the app-level check is the ONLY layer that can TEACH — it names every bad id, before
  anything is minted or written. That is packet 04a's Exit criterion and operator ruling
  R3's, and the reason this module is REQUIRED rather than ergonomic garnish.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any

from surrealdb import RecordID

from loremaster.agent_ref import AgentRefLike
from loremaster.store.surreal_schema import AGENT_TABLE

#: The bound parameter the existence read binds its RecordIDs into.
_ROW_IDS_PARAM = "row_ids"

#: The projected column the existence read always asks for.
_ID_KEY = "id"

#: A ledger's single-statement query seam (``BriefLedger._query`` /
#: ``MessageLedger._query`` / ``TaskLedger._query`` — all of which ride
#: ``loremaster.store._txn.run_query``, so this policy inherits the shared
#: classify/self-heal/retry behaviour rather than owning any of it).
RowQuery = Callable[[str, dict[str, Any]], Awaitable[Any]]

#: 04a's name for the same seam, kept so its callers and docs do not churn.
AgentQuery = RowQuery

#: The AGENT vocabulary, as data rather than as a sentence typed at each site. It lives
#: HERE so a caller that needs the agent policy under a DIFFERENT error class (``send``'s
#: SENDER door, #247) can reach the shared decision point directly without re-typing the
#: noun or the remedy — which would be copy #2 of the served surface.
AGENT_ROW_NOUN = "agent"
AGENT_ROW_REMEDY = (
    "every id must name a registered agent row before a message or a brief can be "
    "written in its name"
)


class UnknownRowError(RuntimeError):
    """Raised when an id names no ROW in the table it was resolved against.

    The GENERALISED base (lead ruling L3), and the base each family's own error
    subclasses: :class:`UnknownAgentRowError` for the agent families,
    :class:`~loremaster.tasks.UnknownBlockerError` for the task ledger. A caller who
    wants *"this id names no row"* across BOTH families catches this one thing, while
    each ledger's callers keep ONE ``except`` for that ledger's whole vocabulary.

    The base must belong to THIS module: a base owned by any ledger is the coupling this
    module exists to prevent.
    """


class UnknownAgentRowError(UnknownRowError):
    """Raised when an id names no ``agent`` ROW at the ledger.

    ⚠ Deliberately NOT :class:`loremaster.agents.UnknownAgentError`, which already exists
    and means something DIFFERENT: *this display NAME resolves to no agent at the
    REGISTRY*. This one is about a row ID that resolves to no ``agent`` row at the
    LEDGER — two same-named exceptions in one package is precisely the confusion a
    teaching error exists to remove.

    The AGENT-family base, not the raised class: each ledger raises its own subclass.
    """


def format_unknown_row_refusal(
    *,
    noun: str,
    identities: Sequence[str],
    remedy: str,
    clauses: Sequence[str] = (),
) -> str:
    """The ONE served refusal text for *"these ids name no usable ``<noun>`` row"*.

    A FUNCTION EVERY FAMILY (AND EVERY TEST DOUBLE) CALLS, never a sentence any of them
    re-types (repo law #102). It exists because the sentence had already been cloned twice
    and had already diverged twice: ``_message_fakes.FakeMessageLedger.send`` served
    *"unknown recipient(s): … every recipient must register before it can be sent to"*
    (names only, no ids) and ``_comms_fakes.FakeBriefLedger._reject_unknown_agent`` served
    *"unknown agent: {id} — every agent must be a registered agent row …"* (id only, no
    name, singular prefix). Every pin over those doubles was an ``id in str(exc)``
    substring check that BOTH strings satisfy, so the divergence was invisible — and the
    divergence is the fake teaching an agent a contract production does not serve. That is
    finding #190's shape, which ``_message_fakes.py``'s own comment names and prescribes
    this cure for.

    ⚠ **THE CONSUMERS OF THIS STRING ARE AGENTS** (the TRUST DOCTRINE): it is the whole of
    what a refused caller learns, so it names EVERY unresolved identity, in full, verbatim
    and never elided — which is precisely what ``ENFORCED`` structurally cannot do (store
    reference §4: ONE bad endpoint, as untyped prose, only AFTER the write, and the seam's
    error hygiene withholds even that).

    The served text is pinned by VALUE (never derived from this function, which would be a
    tautology) in ``test_enforced_relations.py::TestTheSERVEDRefusalTextHasONEImplementation``
    for the agent family and ``test_blocks_edge.py::TestAPhantomBlockerIsRefusedAndNamed``
    for the task family; ONE mutation of this body must redden both.

    Args:
        noun: What the unresolved ids were supposed to name (``agent`` / ``task``).
        identities: The unresolved identities AS RENDERED by the calling family — ``name
            (id)`` for an agent, a bare id (optionally ``id (item n)``) for a blocker.
            SORTED here on the rendered form, so one refusal naming several is stable
            rather than dict-ordered.
        remedy: The family's own clause saying what a caller must do instead.
        clauses: Extra per-identity clauses appended after the remedy — the shape ruling
            **R10(ii)** needs for a SUPERSEDED blocker (*"task X is superseded by Y —
            block on Y instead"*), which is a recovery rather than a rejection. Composed
            HERE rather than by the caller so the whole served sentence is this function's
            and the mutation proof observes all of it.

    Returns:
        The refusal sentence, with no trailing punctuation and no leading class name —
        the caller wraps it in its own domain error.
    """
    sentence = f"unknown {noun}(s): {', '.join(sorted(identities))} — {remedy}"
    if clauses:
        sentence = f"{sentence}; {'; '.join(sorted(clauses))}"
    return sentence


def format_unknown_agent_refusal(unknown_name_by_id: Mapping[str, str]) -> str:
    """The AGENT family's refusal text — a thin ADAPTER over
    :func:`format_unknown_row_refusal` (lead ruling L3).

    It renders BOTH halves of every unresolved identity — the display label the caller
    thought it was acting under AND the row id that resolved to nothing — because an id
    alone teaches less than the label beside it, and a label alone cannot be looked up.

    Args:
        unknown_name_by_id: The unresolved identities, ``{agent_id: display_name}``.

    Returns:
        The refusal sentence (byte-identical to packet 04a's).
    """
    return format_unknown_row_refusal(
        noun=AGENT_ROW_NOUN,
        identities=[f"{name} ({agent_id})" for agent_id, name in unknown_name_by_id.items()],
        remedy=AGENT_ROW_REMEDY,
    )


def agent_identities(agents: Sequence[AgentRefLike]) -> list[tuple[str, str]]:
    """``(row id, rendered identity)`` pairs for ``agents`` — first-wins on ID.

    Keyed on ``id`` and never on ``name``: two different agents may legitimately share a
    display name across sessions. Exposed so a caller needing the AGENT vocabulary under
    its OWN error class (``send``'s sender door) reaches the shared decision point without
    re-typing the identity rendering.
    """
    name_by_id: dict[str, str] = {}
    for ref in agents:
        name_by_id.setdefault(ref.id, ref.name)
    return [(agent_id, f"{name} ({agent_id})") for agent_id, name in name_by_id.items()]


async def resolve_existing_rows(
    query: RowQuery,
    table: str,
    row_ids: Sequence[str],
    *,
    projection: Sequence[str] = (),
) -> dict[str, dict[str, Any]]:
    """The NON-RAISING probe: the rows of ``table`` that EXIST, keyed by the id asked about.

    Ruling **ESC-2** (lead, 2026-07-28) rules this the shape the module grows, with
    :func:`reject_unknown_rows` becoming a thin caller of it: a MIGRATION needs the set of
    ids that resolved, and the raising entry point cannot give it one. The rejected
    alternative — call the raising entry per row and catch — is N round trips and makes an
    exception the control flow of a migration.

    ONE query regardless of how many ids are asked about: a direct-record-access
    ``SELECT id FROM $row_ids`` returns only the ids that EXIST (a non-existent
    ``RecordID`` is silently DROPPED, [PROBED 2026-07-23 and re-probed 2026-07-27 on
    spike-surreal 3.2.1]), so the missing set is exactly ``requested − returned``. That is
    what lets one refusal name every bad id at once.

    ⚠ **STATED BOUND (``test_blocks_edge.py::TestTheSTORESeamRAISESRatherThanReturningEMPTY``):**
    direct record access over a table that does NOT EXIST returns ``OK []`` rather than
    raising, so an empty answer cannot distinguish *"no such rows"* from *"no such table"*.
    Every caller here runs after ``ensure_ready`` has applied the DDL, so the table exists;
    a store with no such table has no rows to resolve either. An ENGINE REJECTION of the
    read (malformed statement, unresolvable function, a ``TIMEOUT`` cut-off) RAISES through
    the caller's own seam and is never laundered into an empty answer.

    An EMPTY ``row_ids`` short-circuits without touching the wire. That is not an
    optimisation dressed as a rule: ``publish`` is routinely called with no ``agent_id``
    — *"a ledger-level caller with no agent row in play"*, a legal, edge-free publish —
    and those callers must not each pay a round trip to be told nothing. (**74 such call
    sites** DERIVED 2026-07-27 by AST over ``loremaster/`` + ``scripts/``; all 74 are TEST
    sites, so the round trip this branch saves is paid by the suite, not by the server.
    The figure is a dated MEASUREMENT, not a pinned invariant — re-derive before citing it.)

    Args:
        query: The calling ledger's single-statement query seam.
        table: The table the ids are resolved against.
        row_ids: The ids to resolve. Duplicates are collapsed.
        projection: Extra columns to read beside ``id`` — how a caller learns something
            about a row it found (``superseded_by``, ruling R10(ii)) without a second
            round trip.

    Returns:
        ``{row id: the projected row}`` for exactly the ids that EXIST.

    Raises:
        SurrealConnectionError: A transport fault, from the caller's own seam.
        SurrealStoreError: The engine rejected the read, from the caller's own seam.
    """
    wanted = list(dict.fromkeys(row_ids))
    if not wanted:
        return {}

    # The id a returned row denotes, keyed by the SDK's own rendering of the RecordID we
    # ASKED about — never by re-parsing the rendering ourselves. ``str(RecordID)`` wraps
    # a uuid-shaped component in angle brackets (``agent:⟨0199c4f1-…⟩``), so a
    # hand-rolled ``str(row["id"]).split(":", 1)[-1]`` is right for ``agent:abc`` and
    # WRONG for every uuid-shaped id — measured, and it costs ~130 red pins across the
    # two ledger suites (store reference §7; finding #248). Matching the engine's echo
    # against our own renderings is symmetric BY CONSTRUCTION: both sides are produced by
    # the same SDK function, so there is no derivation to get wrong.
    asked_by_render: dict[str, str] = {}
    records: list[RecordID] = []
    for row_id in wanted:
        record = RecordID(table, row_id)
        records.append(record)
        asked_by_render[str(record)] = row_id

    columns = ", ".join([_ID_KEY, *projection])
    result = await query(
        f"SELECT {columns} FROM ${_ROW_IDS_PARAM}", {_ROW_IDS_PARAM: records}
    )
    rows = result if isinstance(result, list) else []
    resolved: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or _ID_KEY not in row:
            continue
        resolved_id = asked_by_render.get(str(row[_ID_KEY]))
        if resolved_id is not None:
            resolved[resolved_id] = row
    return resolved


async def reject_unknown_rows(
    query: RowQuery,
    table: str,
    identities: Sequence[tuple[str, str]],
    *,
    noun: str,
    remedy: str,
    error: type[UnknownRowError],
    projection: Sequence[str] = (),
    disqualified: Callable[[str, Mapping[str, Any]], str | None] | None = None,
) -> None:
    """Raise ``error`` naming EVERY identity that does not resolve to a USABLE row.

    THE SOLE DECISION POINT (lead ruling L3): a caller that re-decides underneath this is
    a private copy wearing the shared name, which the sharing proofs neutralise this
    function to detect. A thin caller of :func:`resolve_existing_rows` (ESC-2) — the probe
    holds the round trip, this holds the POLICY.

    Args:
        query: The calling ledger's single-statement query seam.
        table: The table the ids are resolved against.
        identities: ``(row id, rendered identity)`` pairs, in the caller's own vocabulary.
            The rendering is the caller's because only it knows what a reader can act on:
            ``name (id)`` for an agent, ``id`` or ``id (item n)`` for a blocker.
        noun / remedy: the family's vocabulary, handed to
            :func:`format_unknown_row_refusal`.
        error: The :class:`UnknownRowError` subclass to raise. The DECISION — which ids
            are unusable — is made HERE and only here; a caller chooses only the
            vocabulary its own callers catch.
        projection: Extra columns :func:`resolve_existing_rows` must read for
            ``disqualified`` to judge on.
        disqualified: An optional predicate over a row that EXISTS, returning a teaching
            CLAUSE when the row is nonetheless unusable (ruling **R10(ii)**: a SUPERSEDED
            blocker exists but is never a legitimate dependency) or ``None`` when it is
            fine. The clause rides the same refusal, so a caller learns what to do INSTEAD
            in the same breath rather than paying a reconnaissance read.

    Raises:
        UnknownRowError: A subclass of it, as chosen by ``error``.
        SurrealConnectionError: A transport fault, from the caller's own seam.
        SurrealStoreError: The engine rejected the read, from the caller's own seam.
    """
    if not identities:
        return
    existing = await resolve_existing_rows(
        query, table, [row_id for row_id, _label in identities], projection=projection
    )
    unresolved: list[str] = []
    clauses: list[str] = []
    for row_id, label in identities:
        row = existing.get(row_id)
        if row is None:
            unresolved.append(label)
            continue
        if disqualified is None:
            continue
        clause = disqualified(row_id, row)
        if clause is not None:
            unresolved.append(label)
            clauses.append(clause)
    if unresolved:
        raise error(
            format_unknown_row_refusal(
                noun=noun, identities=unresolved, remedy=remedy, clauses=clauses
            )
        )


async def reject_unknown_agents(
    query: RowQuery,
    agents: Sequence[AgentRefLike],
    *,
    error: type[UnknownAgentRowError] = UnknownAgentRowError,
) -> None:
    """Raise ``error`` naming EVERY id in ``agents`` that is not a registered ``agent``
    row. Return silently when they all resolve — and when there are none to resolve.

    Packet 04a's entry point, now a thin typed ADAPTER over :func:`reject_unknown_rows`
    (lead ruling L3) — it supplies the agent TABLE and VOCABULARY and nothing else. It
    keeps no probe and no decision of its own: neutralising the generalised policy must
    stop THIS verb deciding too, which is what proves the generalisation landed rather
    than being a compatibility shim over a retained second implementation
    (``test_blocks_edge.py::TestTheRowExistencePolicyHasONEImplementation``).

    Args:
        query: The calling ledger's single-statement query seam.
        agents: The identities to resolve. Duplicate ids collapse first-wins, keyed on
            ``id`` and never on ``name`` (see :func:`agent_identities`).
        error: The :class:`UnknownAgentRowError` subclass to raise.

    Raises:
        UnknownAgentRowError: A subclass of it, as chosen by ``error`` — naming every
            unresolved identity as ``name (id)``.
        SurrealConnectionError: A transport fault, from the caller's own seam.
        SurrealStoreError: The engine rejected the read, from the caller's own seam.
    """
    await reject_unknown_rows(
        query,
        AGENT_TABLE,
        agent_identities(agents),
        noun=AGENT_ROW_NOUN,
        remedy=AGENT_ROW_REMEDY,
        error=error,
    )
