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
