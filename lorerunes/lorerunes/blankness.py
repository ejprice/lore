"""The blankness predicate — ONE answer to *"what counts as blank?"*.

Ruling R29 (``docs/plans/v2/receipts/2026-07-26-packet42/REMOVED-BEHAVIOR-INVENTORY.md``,
"Eighth ruling wave") mints this module because two callers were about to answer that
question separately:

* ``loremaster.config.resolve_secret`` — rejects an env var that is unset, empty, or
  whitespace-only, so a blank credential fails at the composition root.
* ``loresigil.factory.EmbeddingConfig``'s ``api_key`` validator — rejects a blank
  credential at the config boundary, so no keyless embedder is ever half-built.

They must not be able to disagree. A ``pydantic`` ``Field(min_length=1)`` was ruled out
by measurement: it constrains LENGTH, and a single space has length 1, so it accepts
``" "`` — two of the three blank shapes the contract requires be rejected.

⚠ **THIS MODULE HOLDS THE PREDICATE, NOT THE ENTRY POINT.** A shared package makes it
newly *possible* for ``loresigil`` to resolve secrets again, and it must not: only a
composition root may read the environment. Nothing here reads ``os.environ``.
"""

from __future__ import annotations


def is_blank(value: str) -> bool:
    """Report whether ``value`` carries no real content.

    "Blank" means *empty or nothing but whitespace all the way through*. The
    distinction that matters, and the reason this is not a ``strip()`` call at each
    call site: a credential whose REAL bytes happen to be padded with whitespace is
    **not** blank. Callers pass the value through byte-exact, so this predicate may
    only classify it — never mutate, strip, or normalise it.

    Args:
        value: The candidate string. Whitespace is interpreted by ``str.isspace``,
            so every Unicode space character counts, not just ASCII blanks.

    Returns:
        ``True`` when the value is empty or consists solely of whitespace;
        ``False`` otherwise, including for a value with real content surrounded by
        whitespace.
    """
    # ``str.strip()`` with no argument removes every character ``str.isspace``
    # recognises, so the Unicode claim above is the stdlib's rather than an
    # assumption of ours. The empty arm is kept explicit even though ``"".strip()``
    # is falsy too: "empty counts as blank" is a stated rule, not a derivation.
    return not value or not value.strip()
