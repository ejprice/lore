# loremaster — MCP orchestration layer backed by SurrealDB end to end: the write
# path, and the read path (search/symbols through P6, memory through P7), now
# serve from SurrealDB. The Qdrant read path was retired at P8.

# packet 62 wave 2 (ESC-1 RULED): ``stamp_owner`` — the ONE server-derived
# owner-stamp seam — is exposed at the PACKAGE surface (``loremaster.stamp_owner``),
# its defining module being an implementation detail. It is store-reading
# I/O-orchestration (an ENTRY POINT), so it lives in ``loremaster``, never in the
# stdlib-only ``lorerunes`` (which holds only the pure ``parse_credential`` predicate).
from loremaster.owner_stamp import OwnerStampError, stamp_owner

__all__ = ["OwnerStampError", "stamp_owner"]
