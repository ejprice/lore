"""The ``<name>:<secret>`` credential parse — ONE answer to *"how is a presented
credential split into its name and secret halves?"*.

Extracted (packet 62 wave 2, W2.6) from the sequence that was INLINE in
``loremaster.principal_keys.PrincipalKeyStore.verify`` so that BOTH credential
verifiers — the packet-49 ``PrincipalKeyStore`` (api keys) and the packet-62
``AgentRegistry.verify_capability`` (agent capabilities) — call ONE implementation.
The two wire formats are identical by construction (``<name>:<secret>``, hashed as
``sha512_hex`` of the WHOLE string), so a credential minted one way parses the other
and the two can never drift on the parse rule (ONE IMPLEMENTATION — proven by the
mutation pins that patch this module attribute on each consumer).

⚠ **THIS MODULE HOLDS A PURE PREDICATE, NOT AN ENTRY POINT.** It classifies a string;
it never reads a store, an environment, or a clock. It depends only on ``is_blank``
(the sibling predicate), keeping ``lorerunes`` importable by every other member.
"""

from __future__ import annotations

from lorerunes.blankness import is_blank


def parse_credential(presented: str) -> tuple[str, str] | None:
    """Split a presented ``<name>:<secret>`` credential into its two halves.

    The rule, byte-exact with the packet-49 inline parse it replaces: reject a blank
    credential outright; split on the FIRST colon (so a secret may itself contain
    colons and keeps its tail); reject a blank name OR a blank secret half. The value
    is classified, never mutated — a half whose real bytes are surrounded by
    whitespace is NOT blank (the ``is_blank`` contract), and both halves are returned
    verbatim.

    Args:
        presented: The raw wire credential (e.g. ``"alice_worker:s3cr3t"``).

    Returns:
        ``(name, secret)`` on a well-formed credential, else ``None`` — the uniform
        malformed reject both verifies share (no raise, no per-shape oracle).
    """
    if is_blank(presented):
        return None
    name, separator, secret = presented.partition(":")
    if not separator:
        return None
    if is_blank(name) or is_blank(secret):
        return None
    return name, secret
