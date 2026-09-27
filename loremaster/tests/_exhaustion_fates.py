"""The exhaustion FATE registry (non-collected data for ``test_exhaustion_fates.py``) — packet 58 am-10.

*Scoped to the tree at ``4beb79e`` (branch ``feat/surreal-unification``), 2026-09-26, authored by
``contract-58-r3``.*

``docs/design/2026-09-26-packet58-amendment-10.md`` @ ``5b72471`` §2/§3/§4.  A CROSS-PACKET, repo-level
registry: landed by packet 58 (it built the instrument), each row OWNED by its site's component.  A row is
the ADJUDICATION of one catch site whose fate the classifier cannot derive (neither a PASSTHROUGH nor a
TRANSLATE to a fault class): its classification, its owner, and the AST EVIDENCE that proves the caller (or
the record) can tell the outcome from a healthy one.  Per-row verdicts, each with its reasoning:
``REPORT-contract-58-r3.md`` §FATES.  Rows are keyed ``"<package-relative path>::<function>"``; a function
with several non-derived sites carries one :class:`Fate` per site, in SOURCE ORDER."""

from __future__ import annotations

from dataclasses import dataclass

#: am-10 §2's ruled classifications (a closed set).
CLASSIFICATIONS = frozenset(
    {
        "named-isolation-served",
        "named-isolation-recorded",
        "best-effort-compensation",
        "cli-exit",
        "lifecycle-catch-all",
    }
)

#: am-10 §2's EXACT fault allowlist — a translation of exhausted contention into one of these, chained
#: ``from`` the caught error, is an honest fate (the caller retries or aborts; it cannot be misled).  am-10
#: names ``MemoryBackendError`` too; NO such class exists in the tree (measured 2026-09-26 —
#: ``loremaster.memory`` and ``loremaster.memory.local`` define none), so it is not listed (REPORT
#: §DEVIATIONS D-AM10-FAULTS).
FAULT_CLASS_NAMES: tuple[str, ...] = (
    "loremaster.store._txn.SurrealConnectionError",
    "loremaster.store._txn.SurrealStoreError",
    "loremaster.tasks.TaskLedgerError",
    "loremaster.findings.FindingLedgerError",
    "loremaster.briefs.BriefLedgerError",
    "loremaster.principals.PrincipalStoreError",
    "loremaster.agents.AgentRegistryError",
    "loremaster.keeps.KeepStoreError",
)


@dataclass(frozen=True)
class Fate:
    """One registered site: ``classification`` ∈ :data:`CLASSIFICATIONS`, the ``owner`` component, and the
    named
    ``evidence`` predicates (``test_exhaustion_fates.EVIDENCE``) that must HOLD on it.  Empty evidence is
    allowed
    ONLY for a key in :data:`UNLOGGED_SITES` — the pinned hole set."""

    classification: str
    owner: str
    evidence: tuple[str, ...]


_LIFECYCLE = "lifecycle-catch-all"
_RECORDED = "named-isolation-recorded"
_SERVED = "named-isolation-served"
_COMPENSATION = "best-effort-compensation"

REGISTERED_FATES: dict[str, tuple[Fate, ...]] = {
    "briefs.py::_release_version": (Fate(_COMPENSATION, "briefs", ("logs>=warning",)),),
    "calibration/engine.py::_count_live_total": (
        Fate(_LIFECYCLE, "calibration", ("raises-chained",)),
        Fate(_LIFECYCLE, "calibration", ()),
    ),
    "calibration/engine.py::_file_drift_finding_deduped": (
        Fate(_SERVED, "calibration", ("logs>=warning", "logs-exc_info", "returns-named-outcome")),
    ),
    "calibration/engine.py::_probe_loop": (
        Fate(_LIFECYCLE, "calibration", ("logs>=warning", "logs-exc_info")),
    ),
    "floor_calibration/store.py::_fence_verdict": (
        Fate(_RECORDED, "floor_calibration", ("logs>=warning", "returns-named-outcome")),
    ),
    "index/indexer.py::_commit_batch_file": (
        Fate(_RECORDED, "indexer", ("logs>=warning", "logs-exc_info", "marks-failed")),
    ),
    "index/indexer.py::_index_chunks": (
        Fate(_RECORDED, "indexer", ("logs>=warning", "logs-exc_info", "marks-failed")),
    ),
    "index/indexer.py::_resolve_all_extension_edges": (
        Fate(_RECORDED, "indexer", ("logs>=warning", "logs-exc_info", "appends-failed")),
    ),
    "index/indexer.py::_walk_and_index": (Fate(_RECORDED, "indexer", ("marks-failed",)),),
    "index/indexer.py::_walk_collect_tier": (Fate(_RECORDED, "indexer", ("marks-failed",)),),
    "index/indexer.py::index_file": (Fate(_RECORDED, "indexer", ("marks-failed",)),),
    "index/reconcile.py::_maybe_stamp_snapshot": (
        Fate(_RECORDED, "indexer", ("logs>=warning", "logs-exc_info")),
    ),
    "index/watcher.py::read_events": (Fate(_LIFECYCLE, "watcher", ()),),
    "principals.py::_dispatch_report_unmigrated": (
        Fate("cli-exit", "principals", ("stderr", "returns-named-outcome")),
    ),
    "scout.py::_dispatch": (Fate(_RECORDED, "scout", ("logs>=warning", "marks-failed")),),
    "scout.py::_periodic_reconcile": (Fate(_LIFECYCLE, "scout", ("logs>=warning", "logs-exc_info")),),
    "scout.py::aclose": (Fate(_LIFECYCLE, "scout", ()),),
    "scout.py::run": (Fate(_LIFECYCLE, "scout", ()), Fate(_LIFECYCLE, "scout", ())),
    "scout.py::start": (Fate(_LIFECYCLE, "scout", ()),),
    "search.py::_enrichment_lines": (Fate(_SERVED, "search", ("returns-named-outcome",)),),
    # ⚠ DUAL (packet 63c-i-a a28c — REPORT-contract-63c-i-a-a28c.md §5 U-27): the row
    # ``"server.py::_comms_register": (Fate(_COMPENSATION, "comms (server)", ("logs>=warning",)),)`` is
    # DELETED. The ruled 63c build has NO register compensation (amendment 32 — a28b K5 "no refusal class
    # compensates", K6 "no register path removes or writes keep state"), so the site this row registered — the
    # ``except Exception`` around the compensating ``delete_keep`` — does not exist in any correct build, and
    # the both-ways pin reds a stale row by name. RED at ``169925f`` (the site is still there, now
    # unregistered) for exactly that reason, owned by ``packet-63c-i-a-a28-contract`` in
    # ``scripts/pending_contracts.yaml``.
    "server.py::_eager_build_or_operator_safe_error": (
        Fate(_LIFECYCLE, "server startup", ("logs>=warning", "logs-exc_info")),
    ),
    "server.py::_eager_build_with_retry": (Fate(_LIFECYCLE, "server startup", ("logs>=warning",)),),
    "server.py::_periodic_reconcile": (Fate(_LIFECYCLE, "server", ("logs>=warning", "logs-exc_info")),),
    "server.py::_resolve_or_acknowledge_many": (
        Fate(_SERVED, "findings dispatcher (64b)", ("appends-failed",)),
    ),
    "server.py::aclose": (Fate(_LIFECYCLE, "server shutdown", ()), Fate(_LIFECYCLE, "server shutdown", ())),
    "server.py::build_app_context": (
        Fate(_LIFECYCLE, "server startup", ()),
        Fate(_LIFECYCLE, "server startup", ()),
        Fate(_LIFECYCLE, "server startup", ()),
    ),
    "server.py::on_call_tool": (Fate(_LIFECYCLE, "server (trace emit)", ("logs>=warning", "logs-exc_info")),),
    "server.py::run_probe_gate": (Fate(_LIFECYCLE, "server startup", ("logs>=warning",)),),
    "server.py::run_startup_hooks": (Fate(_LIFECYCLE, "server startup", ()),),
    "testing/loopback.py::_loud_teardown": (Fate(_LIFECYCLE, "testing harness", ("adds-note",)),),
    "testing/loopback.py::_run": (Fate(_LIFECYCLE, "testing harness", ("records-on-self",)),),
}

#: THE PINNED HOLE SET (am-10 §4: "a lifecycle site with NO log line is the one real hole this reading can
#: find — reported by name, and its fix is one line in its owner's module (not 58's)").  Every key here has
#: at least one evidence-less row; the pin reds when a NEW one appears and when a listed one gains evidence
#: (then remove it). ⚠ ``index/watcher.py::read_events`` is the sharpest: it RETURNS AN EMPTY ANSWER
#: (``[]``) at DEBUG — am-10 §1's forbidden shape, not merely an unlogged one (REPORT §FATES).
UNLOGGED_SITES: frozenset[str] = frozenset(
    {
        "calibration/engine.py::_count_live_total",
        "index/watcher.py::read_events",
        "scout.py::aclose",
        "scout.py::run",
        "scout.py::start",
        "server.py::aclose",
        "server.py::build_app_context",
        "server.py::run_startup_hooks",
    }
)
