"""Per-corpus cosine-floor calibration — the DARK machinery (packet 11-i).

⚠ **NOTHING HERE IS SERVED.** Packet 11-i is ``DEPLOY: no``: the existing
constants keep serving exactly as they do today, and every surface in this
package runs only when explicitly invoked. The serving cutover is 11-ii.

11-i-a (this package's store half) owns: the schema, the append-only
measurement rows, the head pointer and its hot-row mint, the head identity
function, the corpus digest, and the exhaustive pool enumeration's contract.
11-i-b owns the probe runner, the statistics, and the R2 lab-validation verb.
"""

from __future__ import annotations
