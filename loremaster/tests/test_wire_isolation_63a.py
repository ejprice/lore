"""Contract — packet 63a-iii: the WIRE-ISOLATION REGRESSION GATE.

Adapted from the packet-63a SECURITY AUDIT's per-call-token wire-level instruments
(``REPORT-secaudit-63a.md`` §APPENDIX — ``/tmp/secaudit-63a/audit.py`` CHECK1/CHECK6), committed
here as a PERMANENT cross-principal READ-isolation gate. This tests what the shipped
``governed_ctx`` fixture (``test_mcp_server.py``) STRUCTURALLY CANNOT: it patches
``get_access_token`` to a static lambda returning ONE email, so it can never switch principals per
call and thus cannot exercise a cross-principal boundary. The retrofit shipped WITHOUT a committed
wire-level isolation gate; this is it.

⚠ REGRESSION GATE — GREEN at HEAD (``dd5c9b2``). The §9 headline — cross-principal isolation OVER
THE WIRE — already HOLDS for the READ paths (security-auditor verdict GO; the F1/RES-2 defects are
WRITE-path). This pins the read isolation so a future change to the composition root
(``AppContext._resolve_subject`` → ``get_access_token()`` → ``governed.resolve_subject``) cannot
SILENTLY re-open a cross-principal leak. It is NOT a RED-until-built pin.

Boots a REAL ``AppContext`` (``build_app_context``) and patches ``loremaster.server.get_access_token``
to a SWITCHABLE transport token whose subject flips per call — every check runs through the identical
seam a hosted foreign principal would (``_resolve_subject`` reads the ambient transport token for the
principal, the ``capability=`` arg for the agent, the 62 binding cross-checks the two). ≥2 principals
× ≥2 agents each. Every negative carries a POSITIVE CONTROL (admin AllRows SEES the rows a member
cannot → the read FILTER is the blocker, not a recall/validity artifact).

STORE LAW cited: §2 (record<> owner links; explicit projection reads a NONE option<> column as None).
Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500); per-test unique DB, reaped; NO skip marker.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import loremaster.server as server_mod
import pytest
import pytest_asyncio
from _governed_contract import (
    MEMORY_TABLE,
    access_token,
    apply_ddl,
    governed_overlay_ddl,
    seed_memory_governed,
)
from _surreal_harness import (
    connect_admin,
    drop_database,
    make_env,
    run,
    surreal_password,
    surreal_url,
    surreal_user,
    unique_database,
)
from loremaster.config import LoreConfig
from loremaster.server import LoreServer, build_app_context
from loresigil.testing import FakeEmbedder

import lorerunes as pdp
from loremaster import governed

_DIM = 8
_E_ALICE = "alice@example.com"
_E_BOB = "bob@example.com"
_E_CAROL = "carol@example.com"
_SURREAL_TEST_NAMESPACE = "lore_test"
_SURREAL_USER_ENV = "SURREAL_USER"
_SURREAL_PASS_ENV = "SURREAL_PASS"
_QUERY_TOKEN = "zebracorn"  # a rare token so ONLY the seeded rows match


def _bare(value: Any) -> str:
    text = str(getattr(value, "id", value))
    return text.split(":", 1)[-1] if ":" in text else text


def _count(rows: Any) -> int:
    return rows[0]["count"] if isinstance(rows, list) and rows else 0


def _boot_config(slug: str, root: Path) -> LoreConfig:
    """A validated config on the dev harness with ``surreal.database`` UNSET (derives from the
    uuid-unique ``slug``) — the ``test_memory_retrofit_63a._boot_config`` idiom, distinct port."""
    payload: dict[str, Any] = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "surreal": {
            "url": surreal_url(),
            "namespace": _SURREAL_TEST_NAMESPACE,
            "user_env": _SURREAL_USER_ENV,
            "password_env": _SURREAL_PASS_ENV,
        },
        "roots": [{"tier": "custom", "watch": "live", "path": str(root), "include": ["**/*.py"]}],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9252},
    }
    return LoreConfig.model_validate(payload)


@pytest_asyncio.fixture()
async def wire_world(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Any:
    """A REAL booted :class:`AppContext` with a SWITCHABLE transport token + a ≥2-principal × ≥2-agent
    hostile seed matrix over the real memory table. ``ANTHROPIC_API_KEY`` / ``LORE_TEI_KEY`` are set so
    the config's key-env references resolve (FakeEmbedder never calls out). Reaped on exit (NEVER
    :18500)."""
    monkeypatch.setenv(_SURREAL_USER_ENV, surreal_user())
    monkeypatch.setenv(_SURREAL_PASS_ENV, surreal_password().get_secret_value())
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-wire-isolation-dummy")
    monkeypatch.setenv("LORE_TEI_KEY", "wire-isolation-dummy")

    # The switchable WIRE authentication: `_resolve_subject` reads `get_access_token()`; flipping
    # `holder["email"]` per call is the seam a hosted foreign principal would present. `email=None`
    # → an empty-subject token → resolve_subject sees no principal → GovernedDenied (identity-less).
    holder: dict[str, str | None] = {"email": None}

    def _patched_get_access_token() -> Any:
        email = holder["email"]
        return access_token(subject=email if email is not None else "")

    monkeypatch.setattr(server_mod, "get_access_token", _patched_get_access_token)

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
        principal_store = context._principal_store
        keep_store = context._keep_store
        registry = context.agent_registry
        assert principal_store is not None and keep_store is not None, (
            "the composition root did not wire the identity stores — the wire-isolation gate needs a "
            "real AppContext with principal + keep stores"
        )

        p_alice = await principal_store.create(email=_E_ALICE, role="member")
        p_bob = await principal_store.create(email=_E_BOB, role="member")
        p_carol = await principal_store.create(email=_E_CAROL, role="admin")
        id_alice, id_bob = _bare(p_alice.id), _bare(p_bob.id)

        async def mint(name: str, principal_id: str) -> tuple[str, str]:
            result = await registry.register(
                name, session="s1", role="worker", owner_principal_id=principal_id
            )
            return str(result.capability), _bare(result.agent.id)

        cap_a1, ag_a1 = await mint("alice_w1", id_alice)
        cap_a2, ag_a2 = await mint("alice_w2", id_alice)  # 2nd alice agent (≥2 per principal)
        cap_b1, ag_b1 = await mint("bob_w1", id_bob)
        cap_b2, _ag_b2 = await mint("bob_w2", id_bob)  # 2nd bob agent (≥2 per principal)
        cap_c1, _ag_c1 = await mint("carol_admin", _bare(p_carol.id))

        # keeps: project P (keeper alice), kA (keeper alice), kB (keeper bob) — disjoint households.
        await keep_store.get_or_create_keyed(
            key=governed.PROJECT_KEEP_KEY, type="project", keeper_email=_E_ALICE, name="lore"
        )
        keep_a = await keep_store.create_keep(keeper_email=_E_ALICE, type="project", name="alicespace")
        keep_b = await keep_store.create_keep(keeper_email=_E_BOB, type="project", name="bobspace")
        id_ka, id_kb = _bare(keep_a.id), _bare(keep_b.id)

        # Idempotent double-apply of the §4.1 overlay (the emitter also emits these post-retrofit).
        await apply_ddl(admin_conn, governed_overlay_ddl(MEMORY_TABLE), url=env.url)

        # The 9-row hostile matrix: every scope, both principals, keeps IN and OUT, a NONE-owner
        # server row, and a NONE-scope dirty legacy row (member-invisible, admin-visible).
        seeds: list[tuple[str, str | None, str | None, str | None, str]] = [
            ("s_alice_pp", id_alice, ag_a1, "principal-private", f"{_QUERY_TOKEN} alice principalprivate"),
            ("s_alice_ap1", id_alice, ag_a1, "agent-private", f"{_QUERY_TOKEN} alice agentprivate a1"),
            ("s_alice_ap2", id_alice, ag_a2, "agent-private", f"{_QUERY_TOKEN} alice agentprivate a2"),
            ("s_bob_pp", id_bob, ag_b1, "principal-private", f"{_QUERY_TOKEN} bob principalprivate"),
            ("s_bob_ap1", id_bob, ag_b1, "agent-private", f"{_QUERY_TOKEN} bob agentprivate b1"),
            ("s_server", None, None, "server", f"{_QUERY_TOKEN} shared server row"),
            ("s_keepA", id_alice, ag_a1, pdp.keep_scope(id_ka), f"{_QUERY_TOKEN} keepA alice household"),
            ("s_keepB", id_bob, ag_b1, pdp.keep_scope(id_kb), f"{_QUERY_TOKEN} keepB bob household"),
            ("s_none", None, None, None, f"{_QUERY_TOKEN} legacy none-scope dirty"),
        ]
        for row_id, owner_principal, owner_agent, scope, note_text in seeds:
            await seed_memory_governed(
                admin_conn, row_id=row_id, dim=_DIM, owner_principal=owner_principal,
                owner_agent=owner_agent, scope=scope, note_text=note_text,
            )

        yield {
            "ctx": context,
            "holder": holder,
            "admin_conn": admin_conn,
            "seeds": seeds,
            "caps": {
                "a1": (_E_ALICE, cap_a1),
                "a2": (_E_ALICE, cap_a2),
                "b1": (_E_BOB, cap_b1),
                "b2": (_E_BOB, cap_b2),
                "carol": (_E_CAROL, cap_c1),
            },
            # The member READ predicate: own agent-private + own principal-private + server (incl.
            # NONE-owner) + the HOUSEHOLD's keeps. NOT a sibling agent's agent-private, NOT a foreign
            # principal's rows, NOT a keep the household is not in, NOT the NONE-scope legacy row.
            "exp": {
                "a1": {"s_alice_pp", "s_alice_ap1", "s_server", "s_keepA"},
                "a2": {"s_alice_pp", "s_alice_ap2", "s_server", "s_keepA"},
                "b1": {"s_bob_pp", "s_bob_ap1", "s_server", "s_keepB"},
                "b2": {"s_bob_pp", "s_server", "s_keepB"},
            },
            "all_ids": {row[0] for row in seeds},
        }
    finally:
        await admin_conn.close()
        await context.aclose()
        await drop_database(env)


async def _wire_recall(world: dict[str, Any], agent_key: str) -> set[str]:
    """Recall through the TRUE composition root: set the ambient transport token to the agent's
    principal email, present its capability, and return the set of SEEDED row ids whose text appears
    in the rendered digest."""
    email, capability = world["caps"][agent_key]
    world["holder"]["email"] = email
    rendered = await world["ctx"].recall(_QUERY_TOKEN, k=50, capability=capability)
    return {row_id for (row_id, _op, _oa, _sc, text) in world["seeds"] if text in rendered}


class TestCrossPrincipalReadIsolationOverTheWire:
    """§9 headline — cross-principal READ isolation over the wire. REGRESSION GATE (GREEN at HEAD
    ``dd5c9b2``): every ``(principal, agent)`` recall serves EXACTLY its visible set through the true
    served composition root, and admin (AllRows) is the positive control proving the read FILTER —
    not a recall accident — is the blocker."""

    async def test_each_member_recall_serves_exactly_its_visible_set(self, wire_world: Any) -> None:
        """Each of ≥2 agents × ≥2 principals serves EXACTLY its visible set — no leak, no miss. The
        intra-principal rule is exercised for BOTH principals (a2 sees a2's agent-private not a1's;
        b2 sees neither b1's agent-private). Headline negatives are called out explicitly, and the
        NONE-scope legacy row is member-invisible (fail-closed §2.3). REDDENS any composition-root
        change that leaks a foreign principal's private row into a member's answer."""
        for agent_key, want in wire_world["exp"].items():
            got = await _wire_recall(wire_world, agent_key)
            leaked, missing = got - want, want - got
            assert not leaked and not missing, (
                f"[{agent_key}] wire recall served the wrong set: served={sorted(got)} "
                f"want={sorted(want)} leaked={sorted(leaked)} missing={sorted(missing)}"
            )
        got_a1 = await _wire_recall(wire_world, "a1")
        got_b1 = await _wire_recall(wire_world, "b1")
        assert "s_alice_pp" not in got_b1, (
            f"bob surfaced alice's principal-private note over the wire — cross-principal leak; "
            f"bob served={sorted(got_b1)}"
        )
        assert "s_bob_pp" not in got_a1, (
            f"alice surfaced bob's principal-private note over the wire — cross-principal leak; "
            f"alice served={sorted(got_a1)}"
        )
        assert "s_none" not in got_a1, (
            "a member surfaced the NONE-scope legacy row over the wire — §2.3 fail-closed broken "
            "(a legacy row must be invisible to every member)"
        )

    async def test_admin_sees_all_rows_and_members_see_strictly_fewer(self, wire_world: Any) -> None:
        """POSITIVE CONTROL — admin (carol, AllRows) recall serves EVERY seeded row, including bob's
        private rows AND the NONE-scope legacy row, so the read FILTER is what blocks a member, not a
        recallability artifact. And each member's served count is STRICTLY BELOW the unfiltered total
        (never the whole table — trust Leg 1), while admin's equals it. REDDENS a build where recall
        ignores identity (member served == unfiltered) or admin under-sees."""
        got_admin = await _wire_recall(wire_world, "carol")
        all_ids = wire_world["all_ids"]
        assert got_admin == all_ids, (
            f"admin (AllRows) must see EVERY seeded row incl bob's private + the NONE-scope row: "
            f"served={sorted(got_admin)} of {sorted(all_ids)} — the positive control that the FILTER "
            f"is the member's blocker"
        )
        # The unfiltered matching total — MEASURED from the store (only the 9 seeds exist on this
        # fresh DB, and all share the token), never a literal.
        unfiltered = _count(
            await run(wire_world["admin_conn"], f"SELECT count() FROM {MEMORY_TABLE} GROUP ALL")
        )
        assert unfiltered == len(all_ids), (
            f"fixture setup — expected {len(all_ids)} seeded rows, store holds {unfiltered}"
        )
        got_a1 = await _wire_recall(wire_world, "a1")
        got_b1 = await _wire_recall(wire_world, "b1")
        assert len(got_a1) < unfiltered and len(got_b1) < unfiltered, (
            f"a member's served count must be STRICTLY BELOW the unfiltered total (never the whole "
            f"table): a1={len(got_a1)} b1={len(got_b1)} unfiltered={unfiltered}"
        )
        assert len(got_admin) == unfiltered, (
            f"admin's served set-size must equal the unfiltered total: admin={len(got_admin)} "
            f"unfiltered={unfiltered}"
        )


class TestTheWireBindingIsEnforced:
    """§3.2.2 / 62 binding — a capability is useless without the matching authenticated principal
    (a stolen capability under a foreign transport token DENIES), and an identity-less call DENIES
    with a teaching error (never a ``TypeError``, never the pre-retrofit unfiltered answer). This is
    the confused-deputy door the shipped ``governed_ctx`` (one static email) cannot test."""

    async def test_a_capability_under_a_foreign_or_absent_token_is_denied(self, wire_world: Any) -> None:
        """alice's cap under BOB's token → DENY; bob's cap under ALICE's token → DENY; an
        identity-less call (no cap, no ambient token) → DENY. POSITIVE CONTROL: the MATCHED alice
        cap+token SUCCEEDS — so the deny is the BINDING, not a broken capability. REDDENS a build
        where a stolen capability authorizes under any principal, or an identity-less call answers."""
        ctx = wire_world["ctx"]
        holder = wire_world["holder"]
        _email_a, cap_a1 = wire_world["caps"]["a1"]
        _email_b, cap_b1 = wire_world["caps"]["b1"]

        holder["email"] = _E_BOB
        with pytest.raises(governed.GovernedDenied):
            await ctx.recall(_QUERY_TOKEN, capability=cap_a1)

        holder["email"] = _E_ALICE
        with pytest.raises(governed.GovernedDenied):
            await ctx.recall(_QUERY_TOKEN, capability=cap_b1)

        holder["email"] = None
        with pytest.raises(governed.GovernedDenied):
            await ctx.recall(_QUERY_TOKEN, capability=None)

        holder["email"] = _E_ALICE
        rendered = await ctx.recall(_QUERY_TOKEN, capability=cap_a1)
        assert isinstance(rendered, str) and rendered, (
            "the MATCHED alice cap + token must SUCCEED — the binding denies only on a mismatch, so a "
            "failing positive control would mean the deny is a broken cap, not the binding"
        )
