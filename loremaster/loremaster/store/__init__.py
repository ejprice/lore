"""The store package. Public store operations live in :mod:`loremaster.store._txn`.

``_txn_coroutines`` is re-exported here so it is reachable at the PACKAGE level
(``loremaster.store._txn_coroutines``) — the operator-ruled home for the ONE store-seam
derivation (finding #279 / design INSTRUMENT F). It is the single walk both store-seam
callers (``scripts.forgery_door_sweep.store_seams`` and
``loremaster/tests/test_blocks_edge._degrade_every_STORE_seam``) derive from, so a new
``_txn`` coroutine is classified consistently by both rather than by "whichever walk sees
it" (the #279 defect).
"""

from ._txn import _txn_coroutines as _txn_coroutines
