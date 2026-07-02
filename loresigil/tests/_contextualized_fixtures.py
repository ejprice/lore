"""Shared document fixtures for the contextualized (document-grouped) contract tests.

Realistic chunked documents — the grouped chunks of ONE source document each,
exactly the shape a RAG indexer sends to a contextualized embedder. The same
three documents exercise the seam from three angles (the wire-level backend in
``test_voyage_context.py``, the offline stand-in in
``test_testing_contextualized.py``, and the optional-seam contract in
``test_contextualized_base.py``), so they are defined once here rather than
copy-pasted per file.
"""

from __future__ import annotations

DOC_RUNBOOK: list[str] = [
    "Incident response runbook: a SEV-1 alert pages the on-call engineer within five minutes.",
    "If the primary database is unreachable, fail over to the replica before restarting the app tier.",
    "After mitigation, the incident commander files a post-mortem within two business days.",
]
DOC_POLICY: list[str] = [
    "Direct deposit posts on the second business day after the pay-period closes.",
    "Chargeback disputes must be filed within sixty days of the statement closing date.",
]
DOC_SINGLE: list[str] = [
    "Quarterly safety training is mandatory for all warehouse staff.",
]
