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

⚠ **BOTH PRE-IMAGES ARE `orjson.dumps(..., option=orjson.OPT_SORT_KEYS)`**
(operator ruling O1, `receipts/2026-07-26-packet11i-build/RULINGS-2026-07-26-adversary.md`).
Not a style choice, and worth the sentence: the earlier bespoke ``\x00``-joined
pre-image needed a NUL-refusal guard, a 12-mapping distinctness matrix written
to defeat separator-naive encodings, AND an escalation to rule which of two
readings mints the record identity. JSON admits ONE reading, escapes NUL, and
sorts keys — so the ambiguity was manufactured by the hand-roll, and ruling it
was the wrong repair. ``orjson`` is a DECLARED dependency, never a transitive
one: an identity frozen in the store must not rest on a version somebody else's
dependency happens to resolve.
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


def corpus_meets_validity_floors(
    *, answered_probes: int, identifier_probes: int, absent_samples: int
) -> bool:
    """STUB (packet 11-i-a). F4.2's ``insufficient_corpus`` predicate.

    ⚠ THE CONSTANTS MUST BE READ, NOT RE-TYPED. Before this function existed the
    three floors were pinned as VALUES that nothing consumed — a build could
    hard-code 30/15/30 at a call site, or read the wrong one of the three, and
    every pin stayed green (adversary M13; the lead's E4 "already pinned" clause
    was withdrawn on exactly this).

    Args:
        answered_probes: derivable answered probes in the pool.
        identifier_probes: distinct identifier probes.
        absent_samples: hold-out absent samples remaining AFTER the C9-rule drops.

    Returns:
        ``True`` iff all three counts meet their pre-registered floors. A
        ``False`` is what puts the engine in ``insufficient_corpus``; it gates
        VALIDITY only — adopted N is chosen solely by F1.
    """
    raise NotImplementedError("packet 11-i-a: corpus_meets_validity_floors")


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
        ValueError: A required axis is missing, or an unregistered axis name was
            supplied. There is deliberately NO separator-refusal clause: the
            JSON pre-image escapes NUL, so the forgery the old guard existed to
            stop is impossible by construction rather than by a check (O1).
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
    collide — so the encoding MUST be unambiguous at the boundary. Under O1 the
    pre-image is ``orjson.dumps`` over the ordered ``(point_id, content_hash)``
    pairs, which gives that for free. The contract pins the PROPERTY, not a
    spelling: unlike the head id, a re-encoded corpus digest costs one extra
    measurement, where a re-encoded head id is a record-identity migration.

    ⚠ **``point_id`` IS PART OF THE DIGEST, not a lookup key.** A digest over
    content hashes alone is RELOCATION-BLIND: a renamed symbol or a moved file
    changes membership with every content hash unchanged, and 11-ii's exact-skip
    then skips a re-measure on a corpus that moved (adversary W5, measured).

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
