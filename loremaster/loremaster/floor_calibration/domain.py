"""The pure domain of floor calibration (packet 11-i-a).

The names and signatures were FROZEN by the contract author (`contract-11ia-1`)
and are the interface packet 11-i-b cites; the bodies were built by
`builder-11ia-1` against that contract.

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
from types import MappingProxyType
from typing import Any

import orjson

from loremaster.index.records import sha512_hex

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

FLOOR_HEAD_ALWAYS_SERIALISED_AXES: tuple[str, ...] = ("scope", "statistic")
"""The axes that serialize unconditionally — CLOSED, exact-set-pinned."""

FLOOR_HEAD_DEFAULTED_AXES: Mapping[str, str] = MappingProxyType({"query_shape": "any"})
"""Axis name -> registered default. Serialized only when the value differs.

A :class:`~types.MappingProxyType`, not a bare ``dict``, for the same reason the
always-serialised axes are a tuple: a closed registry a caller can mutate at run
time is not closed, and this one keys a RECORD IDENTITY.
"""

# The pre-image encoding, in ONE place (operator ruling O1). ``OPT_SORT_KEYS``
# makes the pre-image independent of the caller's mapping order, and JSON escapes
# every separator a value could otherwise splice into — so the forgery the
# retired ``\x00``-join needed a REFUSAL guard for is impossible by construction.
_PREIMAGE_OPTIONS = orjson.OPT_SORT_KEYS


# --- F4.2: the validity floors (``insufficient_corpus``'s predicate) ---------
#
# RESTORED predicates — F4.2 records these as restoring a gate D0's retirement
# sentence removed. They gate VALIDITY only; adopted N is chosen solely by F1.
# The values are pre-registered and adversary-attackable, which is why they are
# named constants and not literals at a call site.

MIN_ANSWERED_PROBES = 30
MIN_IDENTIFIER_PROBES = 15
MIN_ABSENT_SAMPLES = 30


def corpus_meets_validity_floors(
    *, answered_probes: int, identifier_probes: int, absent_samples: int
) -> bool:
    """F4.2's ``insufficient_corpus`` predicate.

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
    # The three floors are READ off the module here, at CALL time — never
    # re-typed as literals. That is what makes them ONE implementation: raise
    # ``MIN_ANSWERED_PROBES`` and this predicate's verdict moves with it.
    return (
        answered_probes >= MIN_ANSWERED_PROBES
        and identifier_probes >= MIN_IDENTIFIER_PROBES
        and absent_samples >= MIN_ABSENT_SAMPLES
    )


def head_identity(axes: Mapping[str, str]) -> str:
    """The ONE head-identity function (F6).

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
    return sha512_hex(orjson.dumps(_serialised_axes(axes), option=_PREIMAGE_OPTIONS))


def _serialised_axes(axes: Mapping[str, str]) -> dict[str, str]:
    """The CLOSED, validated axis mapping :func:`head_identity` hashes.

    Every always-serialised axis is REQUIRED and every other key must be a
    registered defaulted axis; a registered axis sitting AT its default is
    ELIDED, which is what makes registering ``query_shape`` today cost zero
    migration (F6) — and what makes a non-default value mint a new head.

    Args:
        axes: The caller's axis mapping.

    Returns:
        The mapping that becomes the pre-image, with defaults elided.

    Raises:
        ValueError: A required axis is missing, an unregistered axis name was
            supplied, or a value is not a ``str``.
    """
    registered = set(FLOOR_HEAD_ALWAYS_SERIALISED_AXES) | set(FLOOR_HEAD_DEFAULTED_AXES)
    unregistered = sorted(set(axes) - registered)
    if unregistered:
        raise ValueError(
            f"unregistered head axis name(s) {unregistered}: the F6 registry is CLOSED "
            f"(always-serialised {list(FLOOR_HEAD_ALWAYS_SERIALISED_AXES)}, defaulted "
            f"{sorted(FLOOR_HEAD_DEFAULTED_AXES)}) — an unknown axis would mint a head "
            f"nothing can ever resolve again"
        )
    missing = [axis for axis in FLOOR_HEAD_ALWAYS_SERIALISED_AXES if axis not in axes]
    if missing:
        raise ValueError(
            f"head axis mapping is missing required axis/axes {missing} — a head is "
            f"identified by ALL of {list(FLOOR_HEAD_ALWAYS_SERIALISED_AXES)}"
        )
    for name, value in axes.items():
        if not isinstance(value, str):
            raise ValueError(
                f"head axis {name!r} has a non-string value {value!r} ({type(value).__name__}): "
                f"coercing it would make 1 and '1' the same head"
            )
    serialised = {axis: axes[axis] for axis in FLOOR_HEAD_ALWAYS_SERIALISED_AXES}
    serialised.update(
        {
            axis: axes[axis]
            for axis, default in FLOOR_HEAD_DEFAULTED_AXES.items()
            if axis in axes and axes[axis] != default
        }
    )
    return serialised


def corpus_content_digest(rows: Iterable[Mapping[str, Any]]) -> str:
    """The C10 exact-skip change-detection datum.

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
    # A LIST OF PAIRS, not a concatenation: JSON delimits both fields and both
    # ends of every row, so no character can move across a boundary unnoticed and
    # no row can be spliced into its neighbour. Subscripting (never ``.get``) is
    # what makes a row missing either field a loud ``KeyError`` instead of an
    # empty-string substitution that would digest-equal a corpus without the row.
    pairs = [[row["point_id"], row["content_hash"]] for row in rows]
    return sha512_hex(orjson.dumps(pairs))
