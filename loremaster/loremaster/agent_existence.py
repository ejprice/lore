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

from collections.abc import Awaitable, Callable, Mapping, Sequence
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


def format_unknown_agent_refusal(unknown_name_by_id: Mapping[str, str]) -> str:
    """The ONE served refusal text for *"these ids name no ``agent`` row"*.

    A FUNCTION BOTH THE LEDGERS AND THEIR TEST DOUBLES CALL, never a sentence any of
    them re-types (repo law #102). It exists because the sentence had already been
    cloned twice and had already diverged twice: ``_message_fakes.FakeMessageLedger.send``
    served *"unknown recipient(s): … every recipient must register before it can be sent
    to"* (names only, no ids) and ``_comms_fakes.FakeBriefLedger._reject_unknown_agent``
    served *"unknown agent: {id} — every agent must be a registered agent row …"* (id
    only, no name, singular prefix). Every pin over those doubles was an ``id in
    str(exc)`` substring check that BOTH strings satisfy, so the divergence was
    invisible — and the divergence is the fake teaching an agent a contract production
    does not serve. That is finding #190's shape, which ``_message_fakes.py``'s own
    comment names and prescribes this cure for.

    ⚠ **THE CONSUMERS OF THIS STRING ARE AGENTS** (the TRUST DOCTRINE): it is the whole
    of what a refused caller learns, so it names BOTH halves of every unresolved
    identity — the display label the caller thought it was acting under AND the row id
    that resolved to nothing — because an id alone teaches less than the label beside
    it, and a label alone cannot be looked up.

    The served text is pinned by VALUE (never derived from this function, which would be
    a tautology) in
    ``test_enforced_relations.py::TestTheSERVEDRefusalTextHasONEImplementation``, whose
    three legs — production, both fakes — all compare against ONE literal, so changing
    the sentence here reddens all three and a double that stops CALLING this function
    reddens its own.

    Args:
        unknown_name_by_id: The unresolved identities, ``{agent_id: display_name}``.
            Rendered ``name (id)``, SORTED on the rendered form so one refusal naming
            several ids is stable rather than dict-ordered.

    Returns:
        The refusal sentence, with no trailing punctuation and no leading class name —
        the caller wraps it in its own domain error.
    """
    identities = sorted(
        f"{name} ({agent_id})" for agent_id, name in unknown_name_by_id.items()
    )
    return (
        f"unknown agent(s): {', '.join(identities)} — every id must name a registered "
        f"agent row before a message or a brief can be written in its name"
    )


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
    optimisation dressed as a rule: ``publish`` is routinely called with no ``agent_id``
    — *"a ledger-level caller with no agent row in play"*, a legal, edge-free publish —
    and those callers must not each pay a round trip to be told nothing.
    **74 such call sites** DERIVED 2026-07-27 (AST over ``loremaster/`` + ``scripts/``:
    attribute calls named ``publish`` carrying no ``agent_id`` keyword; 97 such calls
    total). ⚠ All 74 are TEST sites — no production caller publishes without an
    ``agent_id`` today, so the round-trip this branch saves is paid by the suite, not by
    the server. The figure is a dated MEASUREMENT, not a pinned invariant: it drifts with
    every test added, and no gate derives it. Re-derive before citing it. (It read
    *"~50 sites"* until 2026-07-27, when the packet-04a cold audit derived 74.)

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
    # two ledger suites
    # (``docs/plans/v2/receipts/2026-07-27-packet04a/REPORT-contract-04a-enforced-3.md`` §7 D-d).
    # Matching the
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

    unknown = {
        agent_id: name
        for agent_id, name in name_by_id.items()
        if agent_id not in existing_ids
    }
    if unknown:
        raise error(format_unknown_agent_refusal(unknown))
