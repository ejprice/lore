"""Packet SDK3 contract, round 5 — R12 X18/X19: two behaviours the per-owner lifecycle code carried, pinned by
BEHAVIOUR because the shared connection factory (R5) replaces the code that carries them.

* **X18** — ``KeepStore.close`` and ``PrincipalKeyStore.close`` also close the ``PrincipalStore`` each one
  composes. Observed at the SDK's own connection class (never a lore factory name, so it holds whichever
  factory
  an owner calls — the per-module ``AsyncSurreal`` at HEAD, the shared factory after R5): every SDK connection
  object opened while the owner worked is closed once ``close()`` returns. A ``close()`` that forgets the
  nested
  store leaves that store's socket open.
* **X19** — ``LocalMemoryBackend.rebuild_embeddings`` is serialised against the read/write path: a ``recall``
  issued while the rebuild holds the memory table DROPPED must wait for the rebuild, then return the note.
  Name-blind (unlike ``test_schema_rebuild``'s race pins, which branch on the ``_rebuild_lock`` attribute's
  existence): the recall is given a bounded settle time; finishing inside it, while the table is dropped, is
  the
  unserialised build.

Packet doc §ROUND 5 / R4.8 X18–X19.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Callable
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
import test_schema_rebuild as rebuild_suite
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.keeps import KeepStore, KeepStoreError
from loremaster.principal_keys import PrincipalKeyStore, PrincipalKeyStoreError
from loremaster.principals import PrincipalNotFoundError, PrincipalStore
from surrealdb import AsyncWsSurrealConnection

# How long an UNserialised recall needs to finish against the dropped table (it is one local round trip,
# measured in milliseconds); a serialised recall stays pending for as long as the rebuild holds the table.
_RECALL_SETTLE_SECONDS = 1.5
# The window barrier's own bound: a recreate that never reaches the barrier fails loud, never hangs.
_WINDOW_TIMEOUT_SECONDS = 30.0


@pytest_asyncio.fixture()
async def store_env() -> AsyncIterator[SurrealEnv]:
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup = await connect_admin(env)
    await setup.close()
    # The nested store's table must exist, so the email lookup is REFUSED for an unknown principal (the
    # owner's own error) rather than for a missing table.
    principal_store = PrincipalStore(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await principal_store.ensure_ready()
    await principal_store.close()
    try:
        yield env
    finally:
        await drop_database(env)


class _SdkConnectionLedger:
    """Every SDK websocket connection object created from installation on, and which of them were closed."""

    def __init__(self) -> None:
        self.created: list[int] = []
        self.closed: set[int] = set()

    @property
    def open_ids(self) -> list[int]:
        return [identity for identity in self.created if identity not in self.closed]


def _watch_sdk_connections(monkeypatch: pytest.MonkeyPatch) -> _SdkConnectionLedger:
    ledger = _SdkConnectionLedger()
    real_init: Callable[..., None] = AsyncWsSurrealConnection.__init__
    real_close: Callable[..., Any] = AsyncWsSurrealConnection.close

    def _init(self: Any, *args: Any, **kwargs: Any) -> None:
        ledger.created.append(id(self))
        real_init(self, *args, **kwargs)

    async def _close(self: Any, *args: Any, **kwargs: Any) -> Any:
        ledger.closed.add(id(self))
        return await real_close(self, *args, **kwargs)

    monkeypatch.setattr(AsyncWsSurrealConnection, "__init__", _init)
    monkeypatch.setattr(AsyncWsSurrealConnection, "close", _close)
    return ledger


class TestAComposingStoreClosesItsNestedPrincipalStore:
    """X18: drive each composing owner far enough that its nested ``PrincipalStore`` connects (an email lookup
    for a principal that does not exist — refused, but only AFTER the lookup ran), then ``close()`` it.
    Premise:
    at least two SDK connections were opened (the owner's own and the nested store's); verdict: none is left
    open."""

    async def test_keep_store_close_closes_every_connection_it_opened(
        self, store_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = KeepStore(
            url=store_env.url,
            namespace=store_env.namespace,
            database=store_env.database,
            user=store_env.user,
            password=store_env.password,
        )
        ledger = _watch_sdk_connections(monkeypatch)
        await store.ensure_ready()
        with pytest.raises(KeepStoreError):
            await store.create_keep(keeper_email="x18-nobody@example.com", type="project")
        await store.close()
        assert len(ledger.created) >= 2, (
            f"premise: the owner and its nested store each connected ({ledger.created})"
        )
        assert not ledger.open_ids, (
            f"KeepStore.close() left {len(ledger.open_ids)} of {len(ledger.created)} SDK connections open "
            f"— the "
            f"composed PrincipalStore was not closed (X18)"
        )

    async def test_principal_key_store_close_closes_every_connection_it_opened(
        self, store_env: SurrealEnv, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        store = PrincipalKeyStore(
            url=store_env.url,
            namespace=store_env.namespace,
            database=store_env.database,
            user=store_env.user,
            password=store_env.password,
        )
        ledger = _watch_sdk_connections(monkeypatch)
        await store.ensure_ready()
        with pytest.raises((PrincipalKeyStoreError, PrincipalNotFoundError)):
            await store.mint(email="x18-nobody@example.com", name="x18", secret_hash="x18-hash")
        await store.close()
        assert len(ledger.created) >= 2, (
            f"premise: the owner and its nested store each connected ({ledger.created})"
        )
        assert not ledger.open_ids, (
            f"PrincipalKeyStore.close() left {len(ledger.open_ids)} of {len(ledger.created)} SDK "
            f"connections open "
            f"— the composed PrincipalStore was not closed (X18)"
        )


class TestARecallDuringARebuildWaitsForIt:
    """X19: the rebuild drops and re-creates the memory table; ``_WindowBarrierMemoryBackend``
    (``test_schema_rebuild``) holds that window open. A recall issued inside the window must NOT finish while
    the
    table is dropped; once the window closes it must return the note (block-then-succeed, never an empty read
    off
    the dropped table)."""

    async def test_a_recall_inside_the_recreate_window_blocks_then_returns_the_note(
        self, tmp_path: Path
    ) -> None:
        slug = rebuild_suite._slug()
        backend, ledger = rebuild_suite._make_memory_backend(
            rebuild_suite._WindowBarrierMemoryBackend, slug, tmp_path
        )
        window = backend
        assert isinstance(window, rebuild_suite._WindowBarrierMemoryBackend)
        note = "x19 serialisation: hostname -I is GNU inetutils here; use ip -4 -o addr show scope global."
        try:
            await backend.ensure_ready()
            await backend.remember(note, kind="fact", subject=rebuild_suite._GOV_SUBJECT, scope="server")
            rebuild = asyncio.create_task(backend.rebuild_embeddings())
            await asyncio.wait_for(window.window_open.wait(), timeout=_WINDOW_TIMEOUT_SECONDS)
            recall = asyncio.create_task(backend.recall(note, k=5, subject=rebuild_suite._GOV_SUBJECT))
            await asyncio.wait_for(window.recall_entered.wait(), timeout=_WINDOW_TIMEOUT_SECONDS)
            finished_early, _pending = await asyncio.wait({recall}, timeout=_RECALL_SETTLE_SECONDS)
            window.resume_rebuild.set()
            rebuild_result, recall_result = await asyncio.gather(rebuild, recall, return_exceptions=True)
        finally:
            await backend.close()
            ledger.close()
            await rebuild_suite._drop_slug_database(slug)
        assert not finished_early, (
            f"a recall FINISHED while the rebuild held the memory table dropped "
            f"(result {recall_result!r}) — the "
            f"rebuild is not serialised against the read path (X19)"
        )
        assert not isinstance(rebuild_result, BaseException), f"the rebuild failed: {rebuild_result!r}"
        assert not isinstance(recall_result, BaseException), f"the blocked recall raised: {recall_result!r}"
        assert any(note in text for text in rebuild_suite._recalled_texts(recall_result)), (
            f"the recall that waited out the rebuild did not return the note: {recall_result!r}"
        )
