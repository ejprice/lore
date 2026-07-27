"""The ONE shared ``AgentRefLike`` Protocol — the externally-resolved agent
identity both the brief ledger and the message ledger accept per roster item.

Promoted here from ``briefs.py`` (operator-ruled 2026-07-19, DRY law): a second
copy of a Protocol is still copy #2, and duplication is a DESIGN decision, not a
quiet clone. :class:`~loremaster.briefs.BriefLedger` (``coverage``/``ack``) and
:class:`~loremaster.messages.MessageLedger` (``send``) both import THIS object,
so ``loremaster.briefs.AgentRefLike is loremaster.messages.AgentRefLike`` — the
single home the contract pins structurally
(``test_message_ledger.py::TestAgentRefLikeHasONEHome``).

It lives in NEITHER ledger module on purpose: a ledger owning the shared
Protocol would force its sibling to import IT, reintroducing exactly the coupling
the "the ledger never imports its neighbours" decoupling law
(``briefs.py`` module docstring) exists to prevent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class AgentRefLike(Protocol):
    """The structural shape the ledgers accept per roster / send item.

    Matches an :class:`~loremaster.agents.Agent` STRUCTURALLY, never nominally —
    the ledgers never import :mod:`loremaster.agents`. Declared as READ-ONLY
    properties (rather than plain mutable attributes) so a frozen/immutable
    duck-typed caller-supplied stand-in (e.g. a contract test's
    ``@dataclass(frozen=True)`` roster item) structurally satisfies this
    Protocol — mypy treats a plain attribute Protocol member as requiring a
    SETTABLE variable, which a frozen dataclass field is not; the ledgers only
    ever READ ``.id``/``.name``, so the narrower read-only shape is the correct
    (and more permissive) contract.
    """

    @property
    def id(self) -> str: ...

    @property
    def name(self) -> str: ...


@dataclass(frozen=True)
class AgentRef:
    """The minimal concrete :class:`AgentRefLike` — a row id and the display label it was
    resolved under.

    Added by packet 04a for a specific reason, stated so it is not mistaken for a general
    invitation to build agent objects here: the shared unknown-agent policy
    (:func:`loremaster.agent_existence.reject_unknown_agents`) resolves a SEQUENCE of
    identities, which is the shape ``MessageLedger.send`` already holds — while
    ``BriefLedger.publish``/``ack`` hold a bare ``agent_id`` string plus the label their
    caller resolved it under. Without a concrete ref the brief ledger could only reach the
    shared policy through a SECOND, id-only entry point, and a policy with two doors is a
    policy with two futures.

    Frozen, so it structurally satisfies :class:`AgentRefLike`'s read-only properties
    (see that Protocol's own docstring for why they are properties and not attributes) and
    cannot be mutated between the check and the write it guards.
    """

    id: str
    name: str
