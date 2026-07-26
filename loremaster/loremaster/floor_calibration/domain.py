"""STUB SURFACE (packet 11-i-a) — the pure domain of floor calibration.

WRITTEN BY THE CONTRACT AUTHOR (`contract-11ia-1`), NOT BY A BUILDER. Every
``NotImplementedError`` is a hole the 11-i-a builder fills; the names and
signatures are the FROZEN interface packet 11-i-b cites.

Everything in this module is a PURE FUNCTION or a pre-registered CONSTANT — no
store, no clock, no I/O. That is deliberate: the head identity and the corpus
digest are both *identity* decisions, and F6 records that deciding them after
the table ships is a record-identity migration, "the one non-``OVERWRITE``-able
freeze in 11-i-a".

Design of record: `docs/design/2026-07-25-floor-calibration-addendum-F.md` F4
(states + the 30–49 join) / F5 (cause enum) / F6 (``head_identity(axes)`` +
the reserved ``query_shape`` axis) ·
`docs/plans/v2/receipts/2026-07-24-packet11i/CONTRACT-FREEZE-DECISIONS.md` C10
(the corpus content digest).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

# --- F6: the head identity axis registry -------------------------------------
#
# The head is keyed on its AXIS MAPPING. ``statistic`` and ``scope`` ALWAYS
# serialize; any FUTURE axis serializes ONLY when its value differs from its
# registered default. The consequence F6 pins by mutation: registering a new
# axis AT ITS DEFAULT changes NO existing head id (byte-identical), while a
# non-default value mints a NEW head.
#
# ``query_shape`` is registered NOW at default ``"any"`` (F6, from the client
# consult) precisely so the axis costs zero migration when it is first used.

FLOOR_HEAD_ALWAYS_SERIALISED_AXES: tuple[str, ...] = ()
"""The axes that serialize unconditionally — CLOSED, exact-set-pinned."""

FLOOR_HEAD_DEFAULTED_AXES: Mapping[str, str] = {}
"""Axis name -> registered default. Serialized only when the value differs."""


# --- F4.2: the validity floors (``insufficient_corpus``'s predicate) ---------
#
# RESTORED predicates — F4.2 records these as restoring a gate D0's retirement
# sentence removed. They gate VALIDITY only; adopted N is chosen solely by F1.
# The values are pre-registered and adversary-attackable, which is why they are
# named constants and not literals at a call site.

MIN_ANSWERED_PROBES = 0
MIN_IDENTIFIER_PROBES = 0
MIN_ABSENT_SAMPLES = 0


def head_identity(axes: Mapping[str, str]) -> str:
    """STUB (packet 11-i-a). The ONE head-identity function (F6).

    ``records.sha512_hex`` over the sorted ``(axis_name, value)`` pairs.

    Args:
        axes: The axis mapping. Every axis in
            :data:`FLOOR_HEAD_ALWAYS_SERIALISED_AXES` is REQUIRED; every other
            key must be a registered axis (a member of
            :data:`FLOOR_HEAD_DEFAULTED_AXES`). The registry is CLOSED.

    Returns:
        The 128-character lowercase hex digest that is the head's record id.

    Raises:
        ValueError: A required axis is missing, an unregistered axis name was
            supplied, or a value contains the pre-image separator (which would
            let one axis's value forge another axis).
    """
    raise NotImplementedError("packet 11-i-a: head_identity")


def corpus_content_digest(rows: Iterable[Mapping[str, Any]]) -> str:
    """STUB (packet 11-i-a). The C10 exact-skip change-detection datum.

    A ``sha512_hex`` over the ASCENDING-ID walk of every chunk's
    ``(point_id, content_hash)``, computed from the run's own exhaustive scroll
    — no extra read. 11-ii's exact-skip compares this against the head row's:
    equal ⇔ zero chunks added, removed, or edited ⇔ skip.

    ⚠ The design says "concatenation". A BARE concatenation of two
    variable-length strings is FORGEABLE — ``("ab", "c")`` and ``("a", "bc")``
    collide — so the encoding MUST be unambiguous at the boundary. The contract
    pins the PROPERTY (a boundary shift changes the digest), not a spelling.

    Args:
        rows: The enumeration's rows, in ascending record-id order. Each must
            carry ``point_id`` and ``content_hash``.

    Returns:
        The 128-character lowercase hex digest. An empty corpus yields a
        DEFINED digest, never an error.

    Raises:
        KeyError: A row is missing ``point_id`` or ``content_hash``.
    """
    raise NotImplementedError("packet 11-i-a: corpus_content_digest")
