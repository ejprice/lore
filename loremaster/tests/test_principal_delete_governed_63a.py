"""Contract — packet 63a-ii, SF-63-5: ``PrincipalStore.delete`` REFUSES-LOUD while the principal
owns a GOVERNED row (design §10.7-Z / §2.1). The INTERIM until packet 64's admin ``set_owner``
orphans owned governed rows to NONE (audited) inside the delete transaction.

⚠⚠ #SF-63-5 PIN-THE-MISS: this pin asserts the REFUSAL with one owned memory row present. It goes
RED the day 64's orphan-to-NONE mechanism lands (a delete that orphans-then-succeeds will no longer
raise) — DELETE THIS PIN WITH THE MECHANISM (per WHEN YOU CANNOT CLOSE A HOLE, PIN IT). Re-open
trigger (design §10.7-Z): the first principal-delete against a store holding an owned governed row.

``memory.owner_principal`` is the FIRST ``record<principal>`` link on a governed row — a LIVE
dependency (never the retired-history dangle the agent / audit back-links tolerate, store-ref §2).

STORE LAW cited: §2 (record<> links — owner binds as a ``type::record`` link; no auto-clean on a
keeper/owner delete). Live TEST store ``ws://127.0.0.1:18000`` (NEVER :18500); per-test unique DB,
reaped.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from _governed_contract import _bare, build_memory_backend, seed_memory_governed
from _surreal_harness import (
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.principals import PrincipalStore, PrincipalStoreError
from loremaster.store.surreal_schema import MEMORY_TABLE

_DIM = 8
_OWNER_EMAIL = "owner@example.com"  # owns one governed memory row, keeps NOTHING
_LONER_EMAIL = "loner@example.com"  # owns no governed row, keeps nothing (the positive control)

# The typed-error NAME, looked up dynamically so this file COLLECTS even on a build where the class
# does not exist yet (the type pin then fails for the RIGHT reason, never an ImportError).
_OWNS_GOVERNED_ERROR_NAME = "PrincipalOwnsGovernedRowsError"


@pytest_asyncio.fixture()
async def governed_delete_env() -> AsyncIterator[tuple[PrincipalStore, SurrealEnv]]:
    """A ready principal + keep + GOVERNED-memory world on a fresh unique DB.

    The ``keep`` table exists (KeepStore.ensure_ready) because ``delete``'s refuse-while-keeping
    reads it FIRST on the store's OWN connection (§FR-4). The ``memory`` table (with the governed
    ``owner_principal`` column + index) is provisioned by the real backend's ensure_ready. Two
    principals are seeded — an OWNER of one memory row and a LONER of none, neither keeping a keep —
    and ONE memory row is seeded owned by the owner. Reaped on exit.
    """
    from loremaster.keeps import KeepStore
    from loremaster.principal_keys import PrincipalKeyStore

    env = make_env(database=unique_database(), dim=_DIM)
    principal_store = PrincipalStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    key_store = PrincipalKeyStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    keep_store = KeepStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await principal_store.ensure_ready()  # principal FIRST (link target + member_of endpoint)
    await key_store.ensure_ready()  # the principal_key table delete's cascade-count reads
    await keep_store.ensure_ready()  # the keep table delete's refuse-while-keeping reads
    # Provision the governed memory table (its ensure_ready wires owner_principal + the index).
    backend = await build_memory_backend(env)
    await backend.close()
    owner = await principal_store.create(email=_OWNER_EMAIL)
    await principal_store.create(email=_LONER_EMAIL)
    # ONE memory row owned by the owner (owner binds as a type::record<principal> link, store-ref §2).
    admin_conn = await connect_admin(env)
    try:
        await seed_memory_governed(
            admin_conn, row_id="owned1", dim=_DIM,
            owner_principal=_bare(owner), owner_agent=None, scope="server",
        )
    finally:
        await admin_conn.close()
    try:
        yield principal_store, env
    finally:
        await keep_store.close()
        await key_store.close()
        await principal_store.close()
        await drop_database(env)


async def _memory_row_count(env: SurrealEnv, *, owner_bare_id: str) -> int:
    """The count of memory rows owned by ``owner_bare_id`` (via a fresh admin connection)."""
    connection = await connect_admin(env)
    try:
        rows = await run(
            connection,
            f"SELECT count() FROM {MEMORY_TABLE} "
            f"WHERE owner_principal = type::record('principal', $pid) GROUP ALL",
            {"pid": owner_bare_id},
        )
    finally:
        await connection.close()
    return int(rows[0]["count"]) if isinstance(rows, list) and rows else 0


class TestPrincipalOwnsGovernedRowsErrorType:
    def test_the_error_class_exists_and_subclasses_principal_store_error(self) -> None:
        """The refuse raises a DEDICATED typed error subclassing ``PrincipalStoreError`` — so
        ``_dispatch``'s existing ``except PrincipalStoreError`` launders it to a ``lore-adm:`` stderr
        line + exit 1 with no new catch clause (symmetric with ``PrincipalHasKeepsError``)."""
        import loremaster.principals as principals_module

        error_cls = getattr(principals_module, _OWNS_GOVERNED_ERROR_NAME, None)
        assert isinstance(error_cls, type) and issubclass(error_cls, PrincipalStoreError), (
            f"{_OWNS_GOVERNED_ERROR_NAME} must exist and subclass PrincipalStoreError so the "
            f"existing CLI launder catches it: {error_cls!r}"
        )


class TestDeleteRefusesWhileOwningGovernedRows:
    async def test_deleting_an_owner_of_a_memory_row_refuses_naming_count_and_mechanism(
        self, governed_delete_env: tuple[PrincipalStore, SurrealEnv]
    ) -> None:
        """⚠ #SF-63-5 — RED the day 64's orphan-to-NONE lands; DELETE THIS PIN WITH THE MECHANISM.

        The owner keeps NOTHING (so refuse-while-keeping does NOT fire — the memory-owner refuse is
        what does the work), yet owns one governed memory row, so ``delete`` REFUSES loud with the
        typed error, naming the COUNT (1) and the packet-64 ``set_owner`` orphaning mechanism —
        never a silent dangle of ``memory.owner_principal``."""
        import loremaster.principals as principals_module

        principal_store, _env = governed_delete_env
        owns_governed_error = principals_module.PrincipalOwnsGovernedRowsError
        with pytest.raises(owns_governed_error) as exc_info:
            await principal_store.delete(email=_OWNER_EMAIL)
        message = str(exc_info.value)
        assert "1" in message, f"the refusal must name the owned-row COUNT (1): {message!r}"
        assert "set_owner" in message, (
            f"the refusal must name the packet-64 set_owner orphaning mechanism: {message!r}"
        )

    async def test_a_refused_delete_removes_nothing(
        self, governed_delete_env: tuple[PrincipalStore, SurrealEnv]
    ) -> None:
        """A refusal removes NOTHING (raised BEFORE any DELETE): the owner principal survives AND its
        owned memory row is untouched — never a half-delete."""
        principal_store, env = governed_delete_env
        owner_before = await principal_store.get_by_email(_OWNER_EMAIL)
        assert owner_before is not None
        with pytest.raises(PrincipalStoreError):
            await principal_store.delete(email=_OWNER_EMAIL)
        assert await principal_store.get_by_email(_OWNER_EMAIL) is not None, (
            "a refused delete must leave the principal in place"
        )
        assert await _memory_row_count(env, owner_bare_id=_bare(owner_before)) == 1, (
            "a refused delete must leave the owned governed memory row untouched"
        )

    async def test_a_principal_owning_no_governed_row_deletes_cleanly(
        self, governed_delete_env: tuple[PrincipalStore, SurrealEnv]
    ) -> None:
        """POSITIVE CONTROL (fixtures-must-discriminate): a principal owning NO governed row and
        keeping no keep deletes CLEANLY — so the refusal above is the OWNED ROW doing the work, not
        a delete that always refuses on a store that happens to have a memory table."""
        principal_store, _env = governed_delete_env
        cascaded = await principal_store.delete(email=_LONER_EMAIL)
        assert cascaded == 0, "a loner (no keys) cascades zero principal_key rows"
        assert await principal_store.get_by_email(_LONER_EMAIL) is None, (
            "a principal owning no governed row must delete cleanly"
        )
