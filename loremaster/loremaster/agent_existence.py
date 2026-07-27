"""The ONE unknown-agent policy: *does this row id name a live ``agent`` ROW?*

:meth:`~loremaster.messages.MessageLedger.send` and
:meth:`~loremaster.briefs.BriefLedger.publish`/:meth:`~loremaster.briefs.BriefLedger.ack`
need the SAME decision — *resolve these agent ids against the ``agent`` table and
refuse, naming EVERY missing one, BEFORE any write* — so it is a FUNCTION THEY CALL,
never a pattern one ledger clones from the other (repo law #102: a pattern to clone is a
defect to clone; a doc naming one method as "the reference pattern" got its jitter bug
faithfully cloned into a sibling).

It lives in NEITHER ledger module, cloning the :mod:`loremaster.agent_ref` precedent
verbatim: a ledger owning the shared object would force its sibling to import IT,
reintroducing exactly the coupling ``briefs.py``'s *"the ledger never imports its
neighbours"* decoupling law exists to prevent. For the same reason this module imports
neither ledger, and its :class:`UnknownAgentRowError` is a BASE each ledger subclasses
into its own domain error rather than an error either ledger owns.

**Why an app-level check exists at all, when the engine ships ``ENFORCED``.** Both are
wanted and neither is redundant (store reference §4, the ``ENFORCED`` adoption table's
error-ergonomics row):

* ``ENFORCED`` guards the TABLE — including the ``INSERT RELATION`` door no check on one
  verb can ever reach — but it reports ONE bad endpoint, as untyped prose, only AFTER the
  write is attempted, aborting the whole transaction. And the store seam's error hygiene
  (ledger #31) withholds even that: a caller receives ``statement N of M was rejected
  (unspecified rejection); see the server log``.
* So the app-level check is the ONLY layer that can TEACH — it names every bad id, before
  anything is minted or written. That is packet 04a's Exit criterion, and the reason this
  module is REQUIRED rather than ergonomic garnish.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any

from surrealdb import RecordID

from loremaster.agent_ref import AgentRefLike
from loremaster.store.surreal_schema import AGENT_TABLE

#: The bound parameter the existence read binds its ``agent`` RecordIDs into.
_AGENT_IDS_PARAM = "agent_ids"

#: The projected column the existence read asks for.
_ID_KEY = "id"

#: A ledger's single-statement query seam (``BriefLedger._query`` /
#: ``MessageLedger._query`` — both ride ``loremaster.store._txn.run_query``, so this
#: policy inherits the shared classify/self-heal/retry behaviour rather than owning any
#: of it).
AgentQuery = Callable[[str, dict[str, Any]], Awaitable[Any]]


class UnknownAgentRowError(RuntimeError):
    """Raised when an id names no ``agent`` ROW at the ledger.

    ⚠ Deliberately NOT :class:`loremaster.agents.UnknownAgentError`, which already exists
    and means something DIFFERENT: *this display NAME resolves to no agent at the
    REGISTRY*. This one is about a row ID that resolves to no ``agent`` row at the
    LEDGER — two same-named exceptions in one package is precisely the confusion a
    teaching error exists to remove.

    The BASE, not the raised class. Each ledger raises its own subclass so its callers
    keep one ``except`` for that ledger's whole vocabulary, while a caller who wants
    *"this id names no agent"* across BOTH verbs catches this one thing. The base must
    belong to THIS module: a base owned by either ledger is the coupling this module
    exists to prevent.
    """


async def reject_unknown_agents(
    query: AgentQuery,
    agents: Sequence[AgentRefLike],
    *,
    error: type[UnknownAgentRowError] = UnknownAgentRowError,
) -> None:
    """Raise ``error`` naming EVERY id in ``agents`` that is not a registered ``agent``
    row. Return silently when they all resolve — and when there are none to resolve.

    ONE query regardless of how many ids are asked about: a direct-record-access
    ``SELECT id FROM $agent_ids`` returns only the ids that EXIST (a non-existent
    ``RecordID`` is silently DROPPED, [PROBED 2026-07-23 and re-probed 2026-07-27 on
    spike-surreal 3.2.1]), so the missing set is exactly ``requested − returned``. That
    is what lets one refusal name every bad id at once, which ``ENFORCED`` structurally
    cannot do (store reference §4).

    An EMPTY ``agents`` short-circuits without touching the wire. That is not an
    optimisation dressed as a rule: ``publish`` is called with no ``agent_id`` at ~50
    sites — *"a ledger-level caller with no agent row in play"*, a legal, edge-free
    publish — and those callers must not each pay a round trip to be told nothing.

    Args:
        query: The calling ledger's single-statement query seam.
        agents: The identities to resolve. Duplicate ids collapse first-wins, keyed on
            ``id`` and never on ``name``: two different agents may legitimately share a
            display name across sessions.
        error: The :class:`UnknownAgentRowError` subclass to raise. The DECISION —
            which ids are unknown — is made HERE and only here; a caller chooses only
            the vocabulary its own callers catch. (A caller that re-decides underneath
            this is a private copy wearing the shared name, which
            ``test_enforced_relations.py::TestTheSharedPolicyIsTheSOLEDecisionPoint``
            neutralises this function to detect.)

    Raises:
        UnknownAgentRowError: A subclass of it, as chosen by ``error`` — naming every
            unresolved identity as ``name (id)``.
        SurrealConnectionError: A transport fault, from the caller's own seam.
        SurrealStoreError: The engine rejected the read, from the caller's own seam.
    """
    name_by_id: dict[str, str] = {}
    for ref in agents:
        name_by_id.setdefault(ref.id, ref.name)
    if not name_by_id:
        return

    # The id a returned row denotes, keyed by the SDK's own rendering of the RecordID we
    # ASKED about — never by re-parsing the rendering ourselves. ``str(RecordID)`` wraps
    # a uuid-shaped component in angle brackets (``agent:⟨0199c4f1-…⟩``), so a
    # hand-rolled ``str(row["id"]).split(":", 1)[-1]`` is right for ``agent:abc`` and
    # WRONG for every uuid-shaped id — measured, and it costs ~130 red pins across the
    # two ledger suites (``REPORT-contract-04a-enforced-3.md`` §7 D-d). Matching the
    # engine's echo against our own renderings is symmetric BY CONSTRUCTION: both sides
    # are produced by the same SDK function, so there is no derivation to get wrong.
    asked_by_render: dict[str, str] = {}
    records: list[RecordID] = []
    for agent_id in name_by_id:
        record = RecordID(AGENT_TABLE, agent_id)
        records.append(record)
        asked_by_render[str(record)] = agent_id

    result = await query(
        f"SELECT {_ID_KEY} FROM ${_AGENT_IDS_PARAM}", {_AGENT_IDS_PARAM: records}
    )
    rows = result if isinstance(result, list) else []
    existing_ids = {
        asked_by_render[rendered]
        for row in rows
        if isinstance(row, dict) and _ID_KEY in row
        for rendered in (str(row[_ID_KEY]),)
        if rendered in asked_by_render
    }

    unknown = sorted(
        f"{name} ({agent_id})"
        for agent_id, name in name_by_id.items()
        if agent_id not in existing_ids
    )
    if unknown:
        raise error(
            f"unknown agent(s): {', '.join(unknown)} — every id must name a registered "
            f"agent row before a message or a brief can be written in its name"
        )
