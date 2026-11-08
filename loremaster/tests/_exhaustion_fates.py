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
        # packet 58 amendment 11 §0 (d): the ONE raise shape that registers — an UNCHAINED raise (``from
        # None`` / no ``from``) — with evidence logs>=warning ∧ logs-exc_info and a REQUIRED ``reason``.
        "re-raise-unchained",
    }
)

#: am-10 §2's EXACT fault allowlist — a translation of exhausted contention into one of these, chained
#: ``from`` the caught error, is an honest fate (the caller retries or aborts; it cannot be misled).  am-10
#: names ``MemoryBackendError`` too; NO such class exists in the tree (measured 2026-09-26 —
#: ``loremaster.memory`` and ``loremaster.memory.local`` define none), so it is not listed (REPORT
#: §DEVIATIONS D-AM10-FAULTS).
#
#: ⚠ DUAL (packet 58 contract r4 — amendment 11 §2 "exact, both ways", REPORT-contract-58-r4.md FK-r4-1): SIX
#: admissions are REMOVED — ``SurrealStoreError``, ``FindingLedgerError``, ``BriefLedgerError``,
#: ``PrincipalStoreError``, ``AgentRegistryError``, ``KeepStoreError``.  MEASURED 2026-09-29 at ``a77dc00``
#: (``test_exhaustion_fates.translate_targets``): NO catch site in the production tree raises any of them
#: ``from`` a caught error, and am-11 §2 rules "an admitted class with no translating site → RED 'delete the
#: admission'".  Removing them changes no current verdict (none is a translation target); a future translate
# to
#: one of them is a NEW admission, adjudicated then (why it is a fault to its catchers), never inherited.
FAULT_CLASS_NAMES: tuple[str, ...] = (
    "loremaster.store._txn.SurrealConnectionError",
    "loremaster.tasks.TaskLedgerError",
    # ⚠ DUAL (packet 58 contract r4 — amendment 11 §0 (c), folded by amendment 12 §4 item 1): ADMITTED —
    # a retryable probe outage (catcher: the probe loop's backoff) and a refuse-to-start gate.  A translate to
    # an admitted class is DERIVED; a translate to anything else is RED by name (never a site row).
    "loremaster.calibration.engine._ProbeUnavailableError",
    "loremaster.server.ProbeGateError",
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
    #: packet 58 amendment 11 §0 (d): REQUIRED (non-empty) for ``re-raise-unchained``; empty otherwise.
    reason: str = ""
    #: packet 58 amendment 12 §3 R-7: the caught EXPRESSION of the site this row adjudicates, as written
    #: (``test_exhaustion_fates.site_signature``) — rows are matched per SITE, not by ordinal alone.
    catches: str = ""


_LIFECYCLE = "lifecycle-catch-all"
_LEASE_OWNER = "lease (store/lease.py; rider carried by 58's build)"
_LEASE_EVIDENCE = ("logs>=warning", "logs-error-class")
_RECORDED = "named-isolation-recorded"
_SERVED = "named-isolation-served"
_COMPENSATION = "best-effort-compensation"

REGISTERED_FATES: dict[str, tuple[Fate, ...]] = {
    "briefs.py::_release_version": (
        Fate(_COMPENSATION, "briefs", ("logs>=warning",), catches="SurrealStoreError"),
    ),
    # ⚠ DUAL (packet 58 contract r4 — amendment 11 §0 (a)): this key's FIRST row,
    # ``Fate(_LIFECYCLE, "calibration", ("raises-chained",))``, is DELETED — the site translates to the now
    # ADMITTED ``_ProbeUnavailableError`` ``from`` the cause, so the classifier DERIVES it (TRANSLATE).
    "calibration/engine.py::_count_live_total": (
        Fate(_LIFECYCLE, "calibration", (), catches="suppress(Exception)"),
    ),
    "calibration/engine.py::_file_drift_finding_deduped": (
        Fate(
            _SERVED,
            "calibration",
            ("logs>=warning", "logs-exc_info", "returns-named-outcome"),
            catches="Exception",
        ),
    ),
    "calibration/engine.py::_probe_loop": (
        Fate(_LIFECYCLE, "calibration", ("logs>=warning", "logs-exc_info"), catches="Exception"),
    ),
    "floor_calibration/store.py::_fence_verdict": (
        Fate(
            _RECORDED,
            "floor_calibration",
            ("logs>=warning", "returns-named-outcome"),
            catches="SurrealStoreError",
        ),
    ),
    # Packet 66 R36 (sidecar RULING-12 fork 2, option (c)): the ONE per-file store catch site — the batch
    # (``_commit_batch_file``) and realtime (``_index_chunks``) sweeps both commit through it, so their two
    # former rows are this one; its handler body still logs >= WARNING with exc_info and marks the file
    # failed.
    "index/indexer.py::_commit_or_isolate": (
        Fate(
            _RECORDED,
            "indexer",
            ("logs>=warning", "logs-exc_info", "marks-failed"),
            catches="SurrealStoreError",
        ),
    ),
    "index/indexer.py::_resolve_all_extension_edges": (
        Fate(
            _RECORDED,
            "indexer",
            ("logs>=warning", "logs-exc_info", "appends-failed"),
            catches="SurrealStoreError",
        ),
    ),
    "index/indexer.py::_walk_and_index": (
        Fate(_RECORDED, "indexer", ("marks-failed",), catches="Exception"),
    ),
    "index/indexer.py::_walk_collect_tier": (
        Fate(_RECORDED, "indexer", ("marks-failed",), catches="Exception"),
    ),
    "index/indexer.py::index_file": (Fate(_RECORDED, "indexer", ("marks-failed",), catches="Exception"),),
    "index/reconcile.py::_maybe_stamp_snapshot": (
        Fate(_RECORDED, "indexer", ("logs>=warning", "logs-exc_info"), catches="Exception"),
    ),
    "index/watcher.py::read_events": (Fate(_LIFECYCLE, "watcher", (), catches="Exception"),),
    # 63c am-37 §11 item 4 (R2-1, supersedes the §8.1 rows for ``_dispatch_migrate_governed`` and
    # ``_dispatch_report_unmigrated`` before they landed): ONE lore-adm fault handler at the ENTRY — the three
    # verb dispatchers lost their ``except`` blocks, so their rows are DELETED and this one row adjudicates
    # the one site. The row's owner is the SITE's owner (63c). Rider (58 am-14 §3): ``catches`` is
    # ``ast.unparse`` of the production except-tuple AS WRITTEN, member order included.
    "principals.py::_dispatch": (
        Fate(
            "cli-exit",
            "principals",
            ("stderr", "returns-named-outcome"),
            catches=(
                "(PrincipalStoreError, PrincipalKeyStoreError, KeepStoreError, SurrealStoreError, ValueError)"
            ),
        ),
    ),
    "scout.py::_dispatch": (
        Fate(_RECORDED, "scout", ("logs>=warning", "marks-failed"), catches="Exception"),
    ),
    "scout.py::_periodic_reconcile": (
        Fate(_LIFECYCLE, "scout", ("logs>=warning", "logs-exc_info"), catches="Exception"),
    ),
    "scout.py::aclose": (Fate(_LIFECYCLE, "scout", (), catches="suppress(Exception)"),),
    # ⚠ DUAL (packet 58 contract r4 — amendment 12 §2, F-A): the fail-closed resolver makes the two
    # ``_CONNECTION_ERRORS`` tuple-constant handlers in ``run`` (connect / socket-drop, DEBUG only) VISIBLE —
    # two
    # HOLE rows join the two signal-registration rows, in SOURCE ORDER.
    "scout.py::run": (
        Fate(_LIFECYCLE, "scout", (), catches="_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION"),
        Fate(_LIFECYCLE, "scout", (), catches="_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION"),
        Fate(_LIFECYCLE, "scout", (), catches="suppress(NotImplementedError, ValueError, RuntimeError)"),
        Fate(_LIFECYCLE, "scout", (), catches="suppress(NotImplementedError, ValueError, RuntimeError)"),
    ),
    "scout.py::_consume_live": (
        Fate(_LIFECYCLE, "scout", (), catches="_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION"),
    ),
    "scout.py::_safe_kill": (
        Fate(_LIFECYCLE, "scout", (), catches="_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION"),
    ),
    # packet 58 amendment 12 §2 (F-A): inbox_awaiter's four ``_CONNECTION_ERRORS`` sites — HOLES (unlogged or
    # DEBUG), interim-pinned in UNLOGGED_SITES until the owner's one-line WARNING lands (finding #521).
    "inbox_awaiter.py::await_inbox": (
        Fate(_LIFECYCLE, "inbox_awaiter", (), catches="_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION"),
    ),
    "inbox_awaiter.py::_establish_live": (
        Fate(_LIFECYCLE, "inbox_awaiter", (), catches="_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION"),
    ),
    "inbox_awaiter.py::_consume_live": (
        Fate(_LIFECYCLE, "inbox_awaiter", (), catches="_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION"),
    ),
    "inbox_awaiter.py::_safe_kill": (
        Fate(_LIFECYCLE, "inbox_awaiter", (), catches="_SDK_AWAIT_BOUNDARY_ERRORS_WITH_CONTENTION"),
    ),
    # packet 58 amendment 12 §2 (R-3), RULED ``named-isolation-served``: the election library's interface is a
    # bool (or ``(bool, record)``) per tick; each site logs ``lease.lock.<op>_failed`` at WARNING and serves
    # the
    # library's own fail-SAFE value (a candidate that cannot prove its write never claims leadership).
    # Evidence
    # by EFFECT: ``test_reanchor_58_r4_lease_fates.py`` (the WARNING names the class, the failure value is
    # served, the store receives no further call).  ``logs-error-class`` is the rider's static half: the
    # WARNING's
    # ``extra`` carries ``error_class`` (RED until 58's build adds the four lines — lead scope call, am-12
    # §6).
    "store/lease.py::get": (Fate(_SERVED, _LEASE_OWNER, _LEASE_EVIDENCE, catches="_LOCK_CALL_ERRORS"),),
    "store/lease.py::create": (Fate(_SERVED, _LEASE_OWNER, _LEASE_EVIDENCE, catches="_LOCK_CALL_ERRORS"),),
    "store/lease.py::update": (Fate(_SERVED, _LEASE_OWNER, _LEASE_EVIDENCE, catches="_LOCK_CALL_ERRORS"),),
    "store/lease.py::release_if_held": (
        Fate(_SERVED, _LEASE_OWNER, _LEASE_EVIDENCE, catches="_LOCK_CALL_ERRORS"),
    ),
    "scout.py::start": (Fate(_LIFECYCLE, "scout", (), catches="suppress(Exception)"),),
    "search.py::_enrichment_lines": (
        Fate(_SERVED, "search", ("returns-named-outcome",), catches="Exception"),
    ),
    # ⚠ DUAL (packet 63c-i-a a28c — REPORT-contract-63c-i-a-a28c.md §5 U-27): the row
    # ``"server.py::_comms_register": (Fate(_COMPENSATION, "comms (server)", ("logs>=warning",)),)`` is
    # DELETED. The ruled 63c build has NO register compensation (amendment 32 — a28b K5 "no refusal class
    # compensates", K6 "no register path removes or writes keep state"), so the site this row registered — the
    # ``except Exception`` around the compensating ``delete_keep`` — does not exist in any correct build, and
    # the both-ways pin reds a stale row by name. RED at ``169925f`` (the site is still there, now
    # unregistered) for exactly that reason, owned by ``packet-63c-i-a-a28-contract`` in
    # ``scripts/pending_contracts.yaml``.
    # ⚠ DUAL (packet 58 contract r4 — amendment 11 §0 (d)): re-classified from ``lifecycle-catch-all`` to
    # ``re-raise-unchained`` with its REQUIRED reason (the redaction boundary).
    "server.py::_eager_build_or_operator_safe_error": (
        Fate(
            "re-raise-unchained",
            "server startup",
            ("logs>=warning", "logs-exc_info"),
            reason="security-59 F4: credentialed cause must not ride the traceback",
            catches="Exception",
        ),
    ),
    "server.py::_eager_build_with_retry": (
        Fate(_LIFECYCLE, "server startup", ("logs>=warning",), catches="BaseException"),
    ),
    "server.py::_periodic_reconcile": (
        Fate(_LIFECYCLE, "server", ("logs>=warning", "logs-exc_info"), catches="Exception"),
    ),
    "server.py::_resolve_or_acknowledge_many": (
        Fate(
            _SERVED, "findings dispatcher (64b)", ("appends-failed",), catches="TxnContentionExhaustedError"
        ),
    ),
    "server.py::aclose": (
        Fate(_LIFECYCLE, "server shutdown", (), catches="(asyncio.CancelledError, Exception)"),
        Fate(_LIFECYCLE, "server shutdown", (), catches="suppress(Exception)"),
    ),
    "server.py::build_app_context": (
        Fate(_LIFECYCLE, "server startup", (), catches="suppress(Exception)"),
        Fate(_LIFECYCLE, "server startup", (), catches="suppress(Exception)"),
        Fate(_LIFECYCLE, "server startup", (), catches="suppress(Exception)"),
    ),
    "server.py::on_call_tool": (
        Fate(_LIFECYCLE, "server (trace emit)", ("logs>=warning", "logs-exc_info"), catches="Exception"),
    ),
    # ⚠ DUAL (packet 58 contract r4 — amendment 11 §0 (c) consequence, regenerated not hand-edited): the row
    # ``"server.py::run_probe_gate": (Fate(_LIFECYCLE, "server startup", ("logs>=warning",)),)`` is DELETED —
    # the site translates to the now-ADMITTED ``ProbeGateError`` ``from`` the cause, so it is DERIVED
    # (TRANSLATE).
    "server.py::run_startup_hooks": (Fate(_LIFECYCLE, "server startup", (), catches="BaseException"),),
    "testing/loopback.py::_loud_teardown": (
        Fate(_LIFECYCLE, "testing harness", ("adds-note",), catches="Exception"),
    ),
    "testing/loopback.py::_run": (
        Fate(_LIFECYCLE, "testing harness", ("records-on-self",), catches="BaseException"),
    ),
}

#: THE PINNED HOLE SET (am-10 §4: "a lifecycle site with NO log line is the one real hole this reading can
#: find — reported by name, and its fix is one line in its owner's module (not 58's)").  Every key here has
#: at least one evidence-less row; the pin reds when a NEW one appears and when a listed one gains evidence
#: (then remove it). ⚠ ``index/watcher.py::read_events`` is the sharpest: it RETURNS AN EMPTY ANSWER
#: (``[]``) at DEBUG — am-10 §1's forbidden shape, not merely an unlogged one (REPORT §FATES).
#
#: ⚠ DUAL (packet 58 contract r4 — amendment 12 §2): a frozenset of keys became a MAP ``key → "owner · re-open
#: trigger"`` so every pinned hole names who fixes it and when its entry dies (am-12 §2: "with owner +
# trigger").
_OWNER_WARNING_TRIGGER = "the owner's one-line WARNING lands → delete this entry and the row's empty evidence"
UNLOGGED_SITES: dict[str, str] = {
    "calibration/engine.py::_count_live_total": f"calibration · {_OWNER_WARNING_TRIGGER}",
    "index/watcher.py::read_events": f"watcher · {_OWNER_WARNING_TRIGGER} (am-11 §3: a DEFECT, not a bound)",
    "scout.py::aclose": f"scout · {_OWNER_WARNING_TRIGGER}",
    "scout.py::run": f"scout · {_OWNER_WARNING_TRIGGER} (#521 for the two connect/drop sites)",
    "scout.py::start": f"scout · {_OWNER_WARNING_TRIGGER}",
    "scout.py::_consume_live": f"scout · {_OWNER_WARNING_TRIGGER} (#521)",
    "scout.py::_safe_kill": f"scout · {_OWNER_WARNING_TRIGGER} (#521)",
    "inbox_awaiter.py::await_inbox": f"inbox_awaiter · {_OWNER_WARNING_TRIGGER} (#521)",
    "inbox_awaiter.py::_establish_live": f"inbox_awaiter · {_OWNER_WARNING_TRIGGER} (#521)",
    "inbox_awaiter.py::_consume_live": f"inbox_awaiter · {_OWNER_WARNING_TRIGGER} (#521)",
    "inbox_awaiter.py::_safe_kill": f"inbox_awaiter · {_OWNER_WARNING_TRIGGER} (#521)",
    "server.py::aclose": f"server shutdown · {_OWNER_WARNING_TRIGGER}",
    "server.py::build_app_context": f"server startup · {_OWNER_WARNING_TRIGGER}",
    "server.py::run_startup_hooks": f"server startup · {_OWNER_WARNING_TRIGGER}",
}
