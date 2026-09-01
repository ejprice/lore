"""Independent recomputation of the frozen golden memory-id literals for the #439 owner fold
(design §10.9-B), packet 63a-iv. Instrument-as-deliverable (brief-base §1): the corpse test files
``test_memory_backend.py`` / ``test_memory_ledger.py`` pin HAND-COMPUTED ``uuid5`` id literals as a
belt-and-braces cross-check on the derivation convention. The owner fold changes the ``uuid5`` NAME
from ``memory:{text}:{refs_stamp}`` to ``memory:{owner_principal}:{owner_agent}:{text}:{refs_stamp}``,
so those literals must be recomputed for the new scheme.

This reimplements the convention DIRECTLY over ``uuid.uuid5`` — it does NOT call
``derive_memory_id`` — so the literals stay an INDEPENDENT oracle: the parity tests
``derive_memory_id(...) == <LITERAL>`` still catch a production derivation that diverges from the
convention. The field order matches production (``owner_principal``, ``owner_agent``, ``text``,
``refs_stamp``) and the owner pair is the shared ADMIN subject the corpse suite folds
(``corpse_a_admin`` / ``corpse_a_agent``). Run: ``uv run python
scripts/compute_ownerfold_golden_ids_63a_iv.py`` from the repo root.
"""

from __future__ import annotations

import uuid

_ID_PREFIX = "memory"
_ID_SEPARATOR = ":"
_OWNER_PRINCIPAL = "corpse_a_admin"
_OWNER_AGENT = "corpse_a_agent"

# The exact notes/keys the corpse tests pin (copied byte-for-byte from test_memory_backend.py).
PG_NOTE = (
    "PG 18 mounts the data volume at /var/lib/postgresql, not "
    "/var/lib/postgresql/data, or pg_ctlcluster errors at startup."
)
PINNED_CHUNK_KEY = "loremaster:loremaster/memory/store.py:symbol:MemoryStore:0"
UNICODE_NOTE = "SurrealDB RecordID → str(id) everywhere; café ☕ naïve — 日本語"
ASCII_SHORT = "PG 18 mounts the data volume at /var/lib/postgresql"


def convention_id(text: str, refs_stamp: str) -> str:
    """The owner-folded uuid5 id per the #439 convention — INDEPENDENT of derive_memory_id."""
    name = _ID_SEPARATOR.join(
        (_ID_PREFIX, _OWNER_PRINCIPAL, _OWNER_AGENT, text, refs_stamp)
    )
    return str(uuid.uuid5(uuid.NAMESPACE_URL, name))


def main() -> None:
    stamp_v1 = f"{PINNED_CHUNK_KEY}@1"
    stamp_v3 = f"{PINNED_CHUNK_KEY}@3"
    print("# test_memory_backend.py pinned LITERAL ids (owner corpse_a_admin/corpse_a_agent):")
    print(f'_LITERAL_ID_NO_REFS = "{convention_id(PG_NOTE, "")}"')
    print(f'_LITERAL_ID_REF_V1  = "{convention_id(PG_NOTE, stamp_v1)}"')
    print(f'_LITERAL_ID_REF_V3  = "{convention_id(PG_NOTE, stamp_v3)}"')
    print()
    print("# TestMovedMemoryIdHelpersParity inline golden literals:")
    print(f'ascii_no_stamp   = "{convention_id(ASCII_SHORT, "")}"')
    print(f'ascii_with_stamp = "{convention_id(ASCII_SHORT, "a_chunk@1,b_chunk@2")}"')
    print(f'unicode_no_stamp = "{convention_id(UNICODE_NOTE, "")}"')
    print(f'unicode_w_stamp  = "{convention_id(UNICODE_NOTE, "a_chunk@1,b_chunk@2")}"')
    print(f'empty_no_stamp   = "{convention_id("", "")}"')
    print(f'empty_with_stamp = "{convention_id("", "a_chunk@1,b_chunk@2")}"')


if __name__ == "__main__":
    main()
