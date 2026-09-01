"""Contract — packet 63a-iv: §10.8 the production audit-DDL, pinned at the COMPOSITION ROOT.
Authored by ``contract-63a-iv`` (tests ONLY).

⚠ ESCALATED FORK (finding #440, REPORT-contract-63a-iv.md §AUDIT-DDL-FORK): design §10.8 +
cold-audit §FORK-1 assert the production ``audit`` table is UNDEFINED (so a memory guarded_write
admin-bypass audit CREATE auto-creates it SCHEMALESS, #107 shape) and RULE "wire an explicit
AuditStore.ensure_ready NOW". PROBED FALSE at HEAD ``f77ac24``: ``SurrealStore.ensure_ready()``
applies ``generate_ddl()`` which folds in ``_audit_statements()`` → ``DEFINE TABLE audit SCHEMAFULL``
+ the call-time ``action`` ASSERT, and ``build_app_context`` calls ``write_store.ensure_ready()``
FIRST (before the memory backend) on the SAME database. So the gap is ALREADY CLOSED and the explicit
wiring is REDUNDANT. These pins therefore ship as GREEN-at-HEAD **REGRESSION GUARDS** (design §10.8
riders i + ii): they red if anyone removes ``_audit_statements()`` from ``generate_ddl``, reorders so
a write precedes the ready, or otherwise leaves the composed audit trail non-schemaful — the #131
class closed BY CONSTRUCTION at the real composition root, with NO test-side audit ``ensure_ready``.

Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500). Each boot writes a throwaway DB.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _surreal_harness import (
    connect_admin,
    drop_database,
    make_env,
    run,
    surreal_password,
    surreal_user,
    unique_database,
)
from loremaster.server import LoreServer, build_app_context
from loresigil.testing import FakeEmbedder

# Reuse the SHIPPED boot recipe + constants (ONE implementation — never a second _boot_config copy).
from test_memory_retrofit_63a import _DIM, _SURREAL_PASS_ENV, _SURREAL_USER_ENV, _boot_config

_AUDITED_ACTIONS = ("WRITE", "DELETE", "SET_SCOPE", "SET_OWNER")


@pytest_asyncio.fixture()
async def composition_root_db(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Any:
    """Boot a REAL :class:`AppContext` via the PRODUCTION ``build_app_context`` on a throwaway DB —
    NO test-side ``AuditStore.ensure_ready`` anywhere (the #131 fixture-fiction the §10.8 rider (i)
    forbids). Yields ``(context, admin_conn, env)`` so a pin can INFO/CREATE against the SAME database
    the composition root readied. Reaped on exit (NEVER :18500)."""
    monkeypatch.setenv(_SURREAL_USER_ENV, surreal_user())
    monkeypatch.setenv(_SURREAL_PASS_ENV, surreal_password().get_secret_value())
    slug = unique_database()
    context = await build_app_context(
        server=LoreServer(_boot_config(slug, tmp_path)),
        embedder=FakeEmbedder(dim=_DIM),
        manifest_path=tmp_path / "m.db",
        snapshot_root=tmp_path / "snap",
        start_tasks=False,
        calibration_engine=None,
    )
    env = make_env(database=slug, dim=_DIM)
    admin_conn = await connect_admin(env)
    try:
        yield context, admin_conn, env
    finally:
        await admin_conn.close()
        await context.aclose()
        await drop_database(env)


class TestTheCompositionRootReadiesTheAuditTrail:
    """§10.8 rider (i) — the audit trail is SCHEMAFULL with the call-time ``action`` ASSERT after the
    REAL composition root, with NO test-side audit ensure. The #131 class closed by construction."""

    async def test_the_audit_table_is_schemafull_with_the_action_assert(
        self, composition_root_db: Any
    ) -> None:
        """⚠ GREEN at HEAD (audit readied via write_store.ensure_ready → generate_ddl). REDDENS a
        build that removes ``_audit_statements()`` from ``generate_ddl``, or leaves the audit table
        undefined at the composition root (so a bypass would auto-create it SCHEMALESS, §10.8 pt 2)."""
        _context, admin_conn, _env = composition_root_db
        db_info = await run(admin_conn, "INFO FOR DB", {})
        audit_def = str(db_info.get("tables", {}).get("audit"))
        assert "SCHEMAFULL" in audit_def, (
            f"the production ``audit`` table is not SCHEMAFULL at the composition root: {audit_def!r} "
            "(a bypass would auto-create it SCHEMALESS — §10.8 pt 2, unrepairable by IF NOT EXISTS)"
        )
        table_info = await run(admin_conn, "INFO FOR TABLE audit", {})
        action_field = str(table_info.get("fields", {}).get("action"))
        assert "ASSERT" in action_field and all(a in action_field for a in _AUDITED_ACTIONS), (
            f"the audit ``action`` field lacks the call-time domain ASSERT at the composition root: "
            f"{action_field!r}"
        )


class TestTheAuditTrailIsGenuinelySchemafulAndEnforcing:
    """§10.8 rider (ii) — the DISCRIMINATING pair: a valid audit row LANDS (+1) and an out-of-domain
    ``action`` is REJECTED by the ASSERT. A schemaless auto-created table would ACCEPT BOTH, so the
    rejection is what distinguishes the real SCHEMAFULL trail from the #131 fiction."""

    async def test_a_valid_action_lands_and_an_out_of_domain_action_is_rejected(
        self, composition_root_db: Any
    ) -> None:
        """⚠ GREEN at HEAD. REDDENS a build whose audit table is schemaless (out-of-domain accepted)
        or non-writable (valid rejected)."""
        from surrealdb import RecordID

        _context, admin_conn, _env = composition_root_db
        before = _count(await run(admin_conn, "SELECT count() FROM audit GROUP ALL", {}))
        valid = {
            "actor_principal": RecordID("principal", "p1"),
            "actor_agent": RecordID("agent", "a1"),
            "actor_email": "actor@example.com",
            "actor_agent_name": "actor_agent",
            "action": "WRITE",
            "target_table": "memory",
            "target_row": "memory:1",
        }
        await run(admin_conn, "CREATE audit CONTENT $content", {"content": valid})
        after = _count(await run(admin_conn, "SELECT count() FROM audit GROUP ALL", {}))
        assert after == before + 1, f"a valid audit row did not land (+1): {before} -> {after}"

        out_of_domain = dict(valid, action="EXFILTRATE")
        with pytest.raises(Exception):  # noqa: B017,PT011 - the engine rejects the ASSERT (typed by the SDK)
            await run(admin_conn, "CREATE audit CONTENT $content", {"content": out_of_domain})
        settled = _count(await run(admin_conn, "SELECT count() FROM audit GROUP ALL", {}))
        assert settled == after, (
            f"an out-of-domain audit action was ACCEPTED (schemaless-like — the action ASSERT is not "
            f"enforcing): count {after} -> {settled}"
        )


def _count(rows: Any) -> int:
    return rows[0]["count"] if rows else 0
