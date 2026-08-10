"""INSTRUMENT E (finding #289) — the reusable trailing-newline malformed-input matrix.

Contract: ``scripts/test_trailing_newline_matrix.py`` (PART 2). Design doc
``docs/plans/v2/design/2026-08-09-defect-class-prevention.md`` §INSTRUMENT E.

WHY THIS EXISTS. ``gated_ground.Exemption`` bare-interpolates ``finding`` into a served failure
message, and its validator once used ``.match`` — which accepts a value carrying a TRAILING
NEWLINE because Python's ``$`` matches immediately before one. A row with ``finding == "#188\\n"``
was constructible and injected a line into every message rendering it. The instance is fixed
(``.fullmatch``), but a fix without a discriminating pin is half a fix, and the class recurs the
next time a validator's malformed-input matrix omits the ``\\n`` case for a field it interpolates.

This turns *"a contract's malformed-input matrix must carry a trailing-newline case for EVERY field
it interpolates into served text"* from a REMEMBERED PROPERTY into a reusable ENUMERATION a contract
author CALLS, so the ``\\n`` case for a declared field cannot be silently omitted.

THE HONEST BOUND (design §INSTRUMENT E — MEASURED, not argued). WHICH fields are FORGEABLE bare
doors versus ``!r``-escaped safe slots is a JUDGEMENT this helper does NOT make: it enumerates the
``\\n`` case for WHATEVER fields the author declares. The field-classification stays where the
judgement actually is; the helper only makes a forgotten case impossible (INSTRUMENT B's stance one
surface over — derive the inventory so a wrong judgement surfaces as a missing/undriven case).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def newline_forgery_variants(
    base: Mapping[str, object],
    interpolated_fields: Sequence[str],
) -> list[tuple[str, dict[str, object]]]:
    """One ``(field, kwargs)`` variant per declared field, differing from ``base`` only by a
    trailing newline appended to that ONE field.

    Args:
        base: the well-formed field values every variant perturbs by exactly one field.
        interpolated_fields: the fields a validator interpolates into served text — the ``\\n``
            case is produced for each, in order.

    Returns:
        A list of ``(field, kwargs)`` pairs; ``kwargs`` is a fresh dict copied from ``base`` with
        ``field`` carrying a trailing ``"\\n"``. Order follows ``interpolated_fields``.

    Raises:
        ValueError: if ``interpolated_fields`` is empty (a matrix over zero fields enumerates
            nothing and certifies nothing — the #290 anti-vacuity lesson applied to this matrix),
            or if a named field is absent from ``base`` (a field with no base value is a SILENT
            MISS — refuse loudly rather than skip it, because skipping leaves that field with no
            ``\\n`` case anyway).
    """
    if not interpolated_fields:
        raise ValueError(
            "newline_forgery_variants was asked for a matrix over ZERO fields — it would "
            "enumerate nothing and every `for … in variants` loop would pass vacuously. A "
            "trailing-newline matrix that covers no field is a broken instrument, not a clean pass."
        )
    variants: list[tuple[str, dict[str, object]]] = []
    for field in interpolated_fields:
        if field not in base:
            raise ValueError(
                f"newline_forgery_variants cannot build a case for {field!r}: it is absent from "
                f"the base mapping ({sorted(base)}). Skipping it silently is how a declared field "
                "ends up with no trailing-newline case — refusing loudly instead."
            )
        variant = dict(base)
        variant[field] = f"{base[field]}\n"
        variants.append((field, variant))
    return variants
