"""The email normaliser — ONE answer to *"are these the same person?"* (design §3.4/§5).

Packet 39 puts the email normaliser in ``lorerunes`` because two call sites must not be
able to disagree about identity:

* the ADMISSION side stores what the admin typed (``lore-adm add --email``), and
* the VERIFIER normalises the email Google reports at verification time.

If those two answers ever diverge, an operator who admitted ``JHarrington@Example.com``
silently stops matching the person Google reports as ``jharrington@example.com`` — a
fail-CLOSED divergence that looks like "the allowlist is broken" and gets debugged by
widening the allowlist, which is a fail-OPEN fix. So the predicate has ONE home and ONE
behaviour, and both sites call it (contract:
``lorerunes/tests/test_email_normalisation.py``; the loremaster admission side proves the
routing by mutation in ``test_token_verifier.py``).

RULED SEMANTICS (design §5): ``NFKC → casefold → strip``. It is a CLASSIFIER-NORMALISER,
never a rewriter of identity: NFKC folds paste/IME compatibility artefacts (fullwidth
``＠``, the ``ﬁ`` ligature) but NOT script homographs (a Cyrillic ``е`` is not a Latin
``e`` — a SECURITY property), ``casefold`` is the ruled fold (stronger than ``lower`` —
``ß`` → ``ss``), and only SURROUNDING whitespace is stripped (interior content, including
an interior newline a parser must later refuse, survives untouched). Gmail dot/plus
aliasing is deliberately NOT canonicalised (a documented bound — aliases are distinct
identities).
"""

from __future__ import annotations

import unicodedata


def normalize_email(value: str) -> str:
    """Normalise an email address for identity comparison — ``NFKC → casefold → strip``.

    The order is the ruled one (design §5): NFKC first folds compatibility forms into
    their canonical code points (so a pasted fullwidth ``＠`` or a ``ﬁ`` ligature match
    their ASCII equivalents, and Unicode spaces like NBSP/IDEOGRAPHIC SPACE collapse to
    ordinary spaces the strip then removes); ``casefold`` then case-folds (the ruled fold,
    which correctly maps ``ß`` → ``ss`` where ``lower`` would not); ``strip`` finally
    removes only SURROUNDING whitespace, leaving interior content byte-exact.

    This normaliser CLASSIFIES; it never refuses. A blank / whitespace-only value
    classifies to the empty string (the roster parser and the config validator are what
    REFUSE — a normaliser that raised would force every caller to guard, and the guard is
    where the two call sites would drift apart). NFKC does NOT fold script confusables, so
    two visually-identical addresses from different scripts stay distinct (the homograph
    security property).

    Args:
        value: The raw email address, as typed by an admin or reported by the provider.

    Returns:
        The normalised address (``NFKC``-folded, case-folded, surrounding-whitespace
        stripped) — the empty string for a blank input, never a raised exception.
    """
    return unicodedata.normalize("NFKC", value).casefold().strip()
