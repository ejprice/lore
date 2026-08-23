"""lorerunes — shared stdlib-only primitives for the lore project.

A rune is the atomic mark a sigil is composed from, so the name states the dependency
direction: ``lorerunes`` is what the other members are built FROM, and it is built from
nothing but the stdlib.

``lorescribe``, ``loresigil`` and ``loremaster`` may all import this package. It imports
none of them — ever. That is the whole constraint (CLAUDE.md, `lorerunes` — THE HOME FOR
SHARED CODE): the moment it imports a sibling it stops being importable by that sibling,
and the shared home is back to being nowhere.

Policy lives here — anything whose *rules must agree everywhere*: validation predicates,
error classification, retry/backoff budgets, sanitisation, normalisation, formatting
rules. Names are re-exported at package level so callers can write
``from lorerunes import is_blank`` without binding to a module path.
"""

from __future__ import annotations

from lorerunes.blankness import is_blank
from lorerunes.email_normalisation import normalize_email
from lorerunes.engine_rejection import reclassify
from lorerunes.posture import (
    Posture,
    PostureError,
    derive_posture,
    host_is_loopback,
)
from lorerunes.scopes import (
    LORE_READ,
    LORE_WRITE,
    hosted_scopes_for_role,
    lan_scopes_for_role,
)

__all__ = [
    "LORE_READ",
    "LORE_WRITE",
    "Posture",
    "PostureError",
    "derive_posture",
    "hosted_scopes_for_role",
    "host_is_loopback",
    "is_blank",
    "lan_scopes_for_role",
    "normalize_email",
    "reclassify",
]
