"""The comms identity charset — ONE pattern, ONE decision (packet 63c-i-a, amendment-2 A4).

Every agent ``name``, agent ``session`` and brief ``name`` is an IDENTITY: the registry mints
row ids from it and every reader compares it. WHY the charset, CORRECTED (finding #219; packet
63c-i-a amendment 19 F-8 — an earlier version of this paragraph taught a refuted threat model):
identities reach the store as BOUND PARAMETERS, never inlined literals, so this is NOT an
injection guard. It buys three things: (1) ``fullmatch`` makes two distinct identities impossible
to render identically (finding #210: ``.match`` accepted ``"scout\\n"``, a second identity
indistinguishable from ``"scout"`` wherever a trailing newline is invisible); (2) with no space,
backtick, ``=`` or newline admissible, every RENDER of a resolved identity is safe by construction
(a forged instruction is inexpressible as a name); (3) it is the cheap gate in front of the
registry read — a value that cannot BE a name is never looked up. Before 63c-i-a the pattern lived in
``loremaster.agents`` and the decision in ``loremaster.server``, and the store carried a third
spelling as a schema ``ASSERT``. Q3 of the 63c ruling DROPS the store ``ASSERT`` and MOVES the
check into the one writer, which is what makes the decision cross-member POLICY — so it lives
here, where every workspace member may import it (CLAUDE.md, `lorerunes` — THE HOME FOR SHARED
CODE).

Consumers (each proven by mutation to move with this module, never by inspection):
``loremaster.agents.AgentRegistry.register`` (the writer's refusal), and
``loremaster.server.AppContext._is_comms_charset_legal`` — the server's decision home, read by
both the REFUSE policy (``_validate_comms_charset``) and the SKIP policy
(``_comms_traffic_line``). ``loremaster.store.surreal_schema._IDENTIFIER_CHARSET_PATTERN`` is a
READ of :data:`AGENT_NAME_PATTERN`'s text (the ``brief.name`` store ``ASSERT`` until 63c-ii), not a
second spelling.

⚠ This module holds the PATTERN and the PREDICATE, never a policy about what to do with a value
that fails it — refusing and skipping are the callers' decisions.
"""

from __future__ import annotations

import re

#: The ONE comms identity charset: a lowercase letter or digit, then up to 63 lowercase letters,
#: digits, ``_`` or ``-`` (1-64 characters in all). A module constant, never a config knob —
#: configurability would make the identity-integrity and render-safety guarantees above
#: operator-breakable.
AGENT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def is_legal_identifier(value: str) -> bool:
    """Report whether ``value`` is a legal comms identity (an agent name/session, a brief name).

    Args:
        value: The candidate identity string, classified byte-exact (never stripped or
            normalised).

    Returns:
        ``True`` when ``value`` matches :data:`AGENT_NAME_PATTERN` IN FULL. ``fullmatch``, never
        ``match`` (finding #210): Python's ``$`` also matches immediately before a TRAILING
        NEWLINE, so ``.match`` accepted ``"scout\\n"`` — a second identity rendering identically to
        ``"scout"`` wherever a trailing newline is invisible.
    """
    return AGENT_NAME_PATTERN.fullmatch(value) is not None
