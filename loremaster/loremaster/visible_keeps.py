"""The visible-Keeps RESOLVER — the ``loremaster`` shell over the pure PDP (packet 61b-w2).

:func:`resolve_visible_keeps` is the thin, store-touching shell (design
``docs/design/2026-08-22-packet61-pdp-audit-rulings.md`` Fork B/F) that turns a member's
household membership into the pure ``lorerunes`` PDP's ``Subject.visible_keep_ids`` — the
``keep:<id>`` scope set ``authorize_filter`` / ``ScopeInKeeps`` consume.

The store READ lives HERE in ``loremaster`` (Fork B: the pure ``lorerunes`` core stays
store-free); the mapping is pure string work over the SHIPPED ``lorerunes.pdp.keep_scope``
helper — the ONE spelling. The resolver NEVER hand-rolls ``f"keep:{k}"``: the PDP and the
resolver MUST agree on the scope value, and cloning the format string is the
ROUTING-IS-NOT-SHARING trap (#102). ``keep_scope`` reads ``KEEP_SCOPE_PREFIX`` at call
time, so the single shared constant governs both sides.

Packet 62 imports this shell to build the full :class:`~lorerunes.pdp.Subject`.
"""

from __future__ import annotations

from lorerunes.pdp import keep_scope

from loremaster.keeps import KeepStore


async def resolve_visible_keeps(
    keep_store: KeepStore, *, member_email: str
) -> frozenset[str]:
    """Resolve the ``keep:<id>`` scope set the member can see, for the PDP's ``Subject``.

    Reads the bare ids of the keeps whose household ``member_email`` is in
    (:meth:`~loremaster.keeps.KeepStore.list_keeps_for_member` — Fork F, born-wrapped, so a
    store rejection surfaces as :class:`~loremaster.keeps.KeepStoreError` rather than a raw
    engine error into the authz path) and maps each bare id → its ``keep:<id>`` scope via
    the shared ``lorerunes.pdp.keep_scope`` helper. Returns a FROZENSET (immutable — it
    feeds the frozen :class:`~lorerunes.pdp.Subject`); a member of no keep resolves to
    ``frozenset()`` (the empty ``$my_keep_scopes`` the PDP's ``ScopeInKeeps`` handles as
    ``false``).

    Args:
        keep_store: The :class:`~loremaster.keeps.KeepStore` to read household membership
            from.
        member_email: The email of the principal whose visible keeps to resolve.

    Returns:
        The ``frozenset`` of ``keep:<id>`` scope strings for the keeps the member's
        household is in — the PDP's ``visible_keep_ids``.

    Raises:
        KeepStoreError: ``member_email`` resolves to no principal, or the store rejected
            the read (propagated unchanged from ``list_keeps_for_member`` — never a raw
            engine error, and never an empty set for a typo'd identity, which would
            silently under-authorize the confused deputy).
    """
    keep_ids = await keep_store.list_keeps_for_member(member_email=member_email)
    return frozenset(keep_scope(keep_id) for keep_id in keep_ids)
