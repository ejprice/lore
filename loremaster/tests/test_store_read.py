"""Contract tests for ``loremaster.store_read.StoreReadTool`` — the store-backed,
hash-verified, freshness-aware span reader (P8b).

``StoreReadTool.read(tier, path, line_start, line_end)`` is the store-side half of
the Deliverable-3 read surface: it serves a file's verbatim body from the unified
SurrealDB ``file_text`` row (writer:
:meth:`~loremaster.store.surreal.SurrealStore.file_text_fragment`) instead of the
live filesystem, so it quotes the exact bytes lore INDEXED — and, unlike the
filesystem tool, verifies their integrity against the stored digest and flags
staleness against the manifest.

PARITY-PINNED, BOTH BACKENDS
----------------------------
Every behavioural test here runs against BOTH the real SurrealDB-backed
``SurrealStore`` + ``SurrealManifest`` (``_surreal_harness``, a live 3.1.x engine)
AND the adversarial in-memory fakes (``_surreal_fakes``), through the ONE
parametrized ``read_bench`` fixture — the fake-vs-real PARITY PIN: a behaviour the
fake gets wrong, or too friendly, shows up as a real-vs-fake divergence rather
than a fake-only green. Both backends are SEEDED identically through the shared
write API (``file_text_fragment`` + ``replace_fragment`` + ``apply``), so the
seeding code path is itself parity-checked.

The ``read_file`` span/containment CONTRACT is byte-identical on purpose (the P8d
flip must change no caller-visible behaviour); ``TestStoreReadFileParity`` pins
that directly by comparing the two tools' spans over the same source where disk
and store agree.

RED before GREEN: ``StoreReadTool.read`` and ``SurrealStore.file_text`` /
``FakeSurrealStore.file_text`` are stubs raising ``NotImplementedError`` until the
GREEN phase, so every behavioural test here fails at CALL time (not collection).
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, cast

import pytest
import pytest_asyncio
from _surreal_fakes import FakeSurrealStore, fake_surreal_trio
from _surreal_harness import (
    PRODUCTION_DIM,
    TIER_A,
    TIER_B,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.index.records import sha512_hex
from loremaster.index.surreal_manifest import (
    STATE_DIRTY,
    STATE_INDEXED,
    SurrealManifest,
)
from loremaster.read_file import ReadFileTool
from loremaster.source.snapshot import SnapshotLayout
from loremaster.store.surreal import SurrealConnectionError, SurrealStore
from loremaster.store_read import (
    StoreFileSpan,
    StoreReadContainmentError,
    StoreReadError,
    StoreReadIntegrityError,
    StoreReadNotFoundError,
    StoreReadTool,
)

# A multi-line source whose every line names its own number, so an off-by-one or
# a wrong-span read is detectable (mirrors ``test_read_file._LIVE_SOURCE``).
_SOURCE = "".join(f"line {n}\n" for n in range(1, 11))

# A realistic tier-relative path (Odoo-style domain code, not ``a.py``).
_PATH = "models/purchase_order.py"

# A guaranteed-dead RPC URL for the real "store down" arm: nothing listens on
# 127.0.0.1:1, so the connect is refused immediately (ECONNREFUSED → the store's
# typed ``SurrealConnectionError``), never a hang.
_DEAD_URL = "ws://127.0.0.1:1/rpc"


@dataclass
class ReadBench:
    """A per-test store+manifest pair (real or fake) with identical seeding.

    Holds one store and one manifest sharing a single backing database, plus the
    helpers every test uses so no test builds a tool or seeds a row inline. The
    SAME seeding code path (the shared ``file_text_fragment`` + ``replace_fragment``
    + ``apply`` write API) runs on both backends, so seeding is itself parity-
    checked.

    Attributes:
        backend: ``"real"`` or ``"fake"`` — a test can special-case the down-
            connection construction (the fakes have no socket to kill).
        store: The store whose ``file_text`` bodies the tool serves.
        manifest: The manifest consulted for per-file freshness/tracking state.
    """

    backend: str
    store: Any
    manifest: Any

    def tool(self) -> StoreReadTool:
        """The :class:`StoreReadTool` under test, wired to this bench's ports."""
        return StoreReadTool(store=self.store, manifest=self.manifest)

    async def seed(
        self,
        tier: str,
        path: str,
        source: str,
        *,
        state: str = STATE_INDEXED,
        manifest_sha: str | None = None,
        file_text_sha: str | None = None,
        with_manifest: bool = True,
    ) -> None:
        """Seed a ``file_text`` body (+ optionally a manifest row) via the shared API.

        The ``file_text`` row stores ``source`` under ``file_text_sha`` (defaults to
        the true digest of ``source``); the manifest row records ``manifest_sha``
        (defaults to the true digest too) and ``state``. Overriding
        ``file_text_sha`` seeds an INTEGRITY-corrupt row (body ≠ its own digest);
        overriding ``manifest_sha`` or ``state`` seeds a STALE row (manifest
        disagrees with the body / not ``indexed``). ``with_manifest=False`` writes
        the body with NO manifest row (an untracked file — a not-found).
        """
        body_sha = file_text_sha if file_text_sha is not None else sha512_hex(source)
        fragments: list[Any] = [self.store.file_text_fragment(tier, path, source, body_sha)]
        if with_manifest:
            row_sha = manifest_sha if manifest_sha is not None else sha512_hex(source)
            fragments.append(
                self.manifest.replace_fragment(
                    tier=tier,
                    file_path=path,
                    sha512=row_sha,
                    mtime_ns=time.time_ns(),
                    size=len(source.encode("utf-8")),
                    n_chunks=0,
                    chunk_ids=[],
                    state=state,
                )
            )
        await self.store.apply(fragments)

    def down_tool(self) -> StoreReadTool:
        """A :class:`StoreReadTool` whose STORE read raises ``SurrealConnectionError``.

        Uniform across backends: the fake arm arms a fresh fake store to trip; the
        real arm points a store at a dead RPC URL so its first read is refused.
        The manifest is never reached (the store read fails first), so the bench's
        own manifest is reused unchanged.
        """
        if self.backend == "fake":
            fake_downed = FakeSurrealStore(dim=PRODUCTION_DIM)
            fake_downed.arm_connection_failure()
            # A FakeSurrealStore satisfies the store-read contract behaviourally
            # (that IS this parity pin); it shares no base class with the real
            # store, so the cast tells mypy what the suite proves (mirrors
            # ``test_task_ledger``'s cast of ``FakeTaskLedger``).
            return StoreReadTool(store=cast(SurrealStore, fake_downed), manifest=self.manifest)
        real_downed = SurrealStore(
            url=_DEAD_URL,
            namespace="lore_test",
            database="never_reached",
            dim=PRODUCTION_DIM,
            user="root",
            password="spikeroot",
        )
        return StoreReadTool(store=real_downed, manifest=self.manifest)


@pytest_asyncio.fixture(params=["real", "fake"])
async def read_bench(request: pytest.FixtureRequest) -> AsyncIterator[ReadBench]:
    """A store+manifest pair on ONE per-test backing store, over BOTH backends.

    THE single construction seam — every test routes through here so the SAME
    contract suite exercises the real ports and the fakes. The ``"real"`` branch
    deliberately does NOT depend on the ``surreal_env`` pytest fixture (the
    pytest-asyncio 1.4 shared-``Runner`` re-entrancy limitation
    ``test_task_ledger`` documents): it calls the SAME harness helpers
    (``make_env`` / ``connect_admin`` / ``drop_database``) directly, getting the
    isolated-throwaway-database guarantee while keeping every port on the test's
    own event loop. The ``"fake"`` branch builds ONE shared ``FakeSurrealDatabase``
    (via ``fake_surreal_trio``) so the store and manifest see each other's writes.
    """
    if request.param == "real":
        env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup_connection = await connect_admin(env)
        await setup_connection.close()
        store = SurrealStore(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            dim=env.dim,
            user=env.user,
            password=env.password,
        )
        manifest = SurrealManifest(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            user=env.user,
            password=env.password,
        )
        await store.ensure_ready()
        await manifest.ensure_ready()
        try:
            yield ReadBench(backend="real", store=store, manifest=manifest)
        finally:
            await store.close()
            await manifest.close()
            await drop_database(env)
    else:
        trio = fake_surreal_trio(dim=PRODUCTION_DIM)
        yield ReadBench(backend="fake", store=trio.store, manifest=trio.manifest)


class TestStoreReadFullBody:
    """A found, fresh file: the whole verbatim body round-trips, hash-verified,
    with a [SOURCE:...] provenance header and no stale flag."""

    async def test_reads_full_body_when_no_span_given(self, read_bench: ReadBench) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE)
        span = await read_bench.tool().read(TIER_A, _PATH)
        assert isinstance(span, StoreFileSpan)
        # No span ⇒ the whole body, byte-for-byte.
        assert span.text == _SOURCE
        assert span.line_start == 1
        assert span.line_end == 10
        assert span.tier == TIER_A
        assert span.path == _PATH

    async def test_fresh_serve_is_hash_verified_and_not_stale(
        self, read_bench: ReadBench
    ) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE)
        span = await read_bench.tool().read(TIER_A, _PATH)
        assert span.stale is False
        assert span.integrity_verified is True

    async def test_header_names_tier_path_and_span_without_stale_notice(
        self, read_bench: ReadBench
    ) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE)
        span = await read_bench.tool().read(TIER_A, _PATH, line_start=2, line_end=4)
        header = span.header
        assert header.startswith("[SOURCE:")
        assert TIER_A in header
        assert _PATH in header
        assert "2" in header and "4" in header
        assert "STALE" not in header.upper()  # fresh: no degraded notice

    async def test_render_prepends_header_to_span_text(self, read_bench: ReadBench) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE)
        span = await read_bench.tool().read(TIER_A, _PATH, line_start=1, line_end=2)
        rendered = span.render()
        assert rendered.startswith(span.header)
        assert rendered.endswith(span.text)
        assert span.text in rendered

    async def test_two_tiers_of_one_path_are_distinct_bodies(
        self, read_bench: ReadBench
    ) -> None:
        # The composite-id discipline mirrored onto the read: a custom override and
        # the community original of one path COEXIST, each read back on its own.
        source_a = "".join(f"custom {n}\n" for n in range(1, 4))
        source_b = "".join(f"community {n}\n" for n in range(1, 6))
        await read_bench.seed(TIER_A, _PATH, source_a)
        await read_bench.seed(TIER_B, _PATH, source_b)
        span_a = await read_bench.tool().read(TIER_A, _PATH)
        span_b = await read_bench.tool().read(TIER_B, _PATH)
        assert span_a.text == source_a
        assert span_b.text == source_b


class TestStoreReadSpans:
    """Span addressing is 1-based inclusive, byte-identical to ``read_file``:
    omitted start ⇒ 1, omitted end ⇒ EOF, an end past EOF is clamped."""

    async def test_exact_inclusive_line_span(self, read_bench: ReadBench) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE)
        span = await read_bench.tool().read(TIER_A, _PATH, line_start=3, line_end=5)
        assert span.text == "line 3\nline 4\nline 5\n"
        assert span.line_start == 3
        assert span.line_end == 5

    async def test_single_line_span_start_equals_end(self, read_bench: ReadBench) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE)
        span = await read_bench.tool().read(TIER_A, _PATH, line_start=7, line_end=7)
        assert span.text == "line 7\n"

    async def test_start_only_reads_to_end_of_file(self, read_bench: ReadBench) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE)
        span = await read_bench.tool().read(TIER_A, _PATH, line_start=9)
        assert span.text == "line 9\nline 10\n"
        assert span.line_start == 9
        assert span.line_end == 10

    async def test_end_past_eof_is_clamped_not_errored(self, read_bench: ReadBench) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE)
        span = await read_bench.tool().read(TIER_A, _PATH, line_start=8, line_end=999)
        assert span.text == "line 8\nline 9\nline 10\n"
        assert span.line_end == 10


class TestStoreReadSpanErrors:
    """An out-of-range / inverted / non-positive span is a hard ``StoreReadError``
    (byte-identical to ``read_file``'s ``_resolve_span`` rejections)."""

    async def test_line_start_past_eof_raises(self, read_bench: ReadBench) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE)
        with pytest.raises(StoreReadError):
            await read_bench.tool().read(TIER_A, _PATH, line_start=50)

    async def test_inverted_span_raises(self, read_bench: ReadBench) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE)
        with pytest.raises(StoreReadError):
            await read_bench.tool().read(TIER_A, _PATH, line_start=5, line_end=2)

    async def test_non_positive_start_raises(self, read_bench: ReadBench) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE)
        with pytest.raises(StoreReadError):
            await read_bench.tool().read(TIER_A, _PATH, line_start=0)


class TestStoreReadNotFound:
    """An unknown ``(tier, path)`` — no ``file_text`` body OR no manifest row — is a
    clean, teaching ``StoreReadNotFoundError`` naming the tier/path and pointing at
    ``search_code``, never a bare/partial read."""

    async def test_missing_file_text_raises_not_found(self, read_bench: ReadBench) -> None:
        with pytest.raises(StoreReadNotFoundError) as exc_info:
            await read_bench.tool().read(TIER_A, "models/nope.py")
        message = str(exc_info.value)
        assert "models/nope.py" in message
        assert TIER_A in message
        assert "search_code" in message

    async def test_missing_manifest_row_is_treated_as_not_found(
        self, read_bench: ReadBench
    ) -> None:
        # The body exists but the file is UNTRACKED (no manifest row) — a
        # not-found, not a stale serve.
        await read_bench.seed(TIER_A, _PATH, _SOURCE, with_manifest=False)
        with pytest.raises(StoreReadNotFoundError):
            await read_bench.tool().read(TIER_A, _PATH)

    async def test_unknown_tier_raises_not_found(self, read_bench: ReadBench) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE)
        with pytest.raises(StoreReadNotFoundError):
            await read_bench.tool().read("no_such_tier", _PATH)


class TestStoreReadIntegrity:
    """A body whose recomputed SHA-512 disagrees with its stored digest is CORRUPT
    and must NEVER serve silently — a hard ``StoreReadIntegrityError``."""

    async def test_corrupt_body_raises_integrity_error(self, read_bench: ReadBench) -> None:
        # Seed a file_text row whose recorded digest does NOT match its body.
        await read_bench.seed(TIER_A, _PATH, _SOURCE, file_text_sha="0" * 128)
        with pytest.raises(StoreReadIntegrityError):
            await read_bench.tool().read(TIER_A, _PATH)

    async def test_integrity_error_does_not_leak_the_body(
        self, read_bench: ReadBench
    ) -> None:
        secret_source = "SECRET_TOKEN = 'do-not-leak'\n"
        await read_bench.seed(TIER_A, _PATH, secret_source, file_text_sha="f" * 128)
        with pytest.raises(StoreReadIntegrityError) as exc_info:
            await read_bench.tool().read(TIER_A, _PATH)
        message = str(exc_info.value)
        assert "SECRET_TOKEN" not in message  # the corrupt body never rides the error
        assert TIER_A in message and _PATH in message

    async def test_a_corrupt_body_is_a_hard_fail_even_for_a_valid_span(
        self, read_bench: ReadBench
    ) -> None:
        # Integrity is checked BEFORE the span is sliced: even a request for a
        # single, in-range line refuses a corrupt body outright.
        await read_bench.seed(TIER_A, _PATH, _SOURCE, file_text_sha="0" * 128)
        with pytest.raises(StoreReadIntegrityError):
            await read_bench.tool().read(TIER_A, _PATH, line_start=1, line_end=1)


class TestStoreReadFreshness:
    """A body the manifest reports behind disk still serves (degraded honesty), but
    carries an explicit ``stale`` flag and a visible header notice."""

    async def test_non_indexed_state_marks_stale(self, read_bench: ReadBench) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE, state=STATE_DIRTY)
        span = await read_bench.tool().read(TIER_A, _PATH)
        assert span.stale is True
        assert span.text == _SOURCE  # served anyway — degraded, not withheld
        assert span.integrity_verified is True  # the body still verified

    async def test_manifest_digest_mismatch_marks_stale(
        self, read_bench: ReadBench
    ) -> None:
        # The manifest records a DIFFERENT sha512 than the body's own — the file
        # on disk moved past the indexed body. Served, but flagged.
        await read_bench.seed(TIER_A, _PATH, _SOURCE, manifest_sha="a" * 128)
        span = await read_bench.tool().read(TIER_A, _PATH)
        assert span.stale is True

    async def test_stale_serve_has_a_visible_header_notice(
        self, read_bench: ReadBench
    ) -> None:
        await read_bench.seed(TIER_A, _PATH, _SOURCE, state=STATE_DIRTY)
        span = await read_bench.tool().read(TIER_A, _PATH, line_start=1, line_end=2)
        header = span.header
        assert "STALE" in header.upper()  # impossible to miss in the rendered output
        assert header.startswith("[SOURCE:")  # still in the [SOURCE:...] family
        # The stale notice is present in the rendered output too.
        assert "STALE" in span.render().upper()

    async def test_indexed_and_matching_digest_is_fresh(
        self, read_bench: ReadBench
    ) -> None:
        # The negative: an indexed row whose manifest digest MATCHES the body is
        # NOT stale (else the flag is noise and gets ignored when it matters).
        await read_bench.seed(TIER_A, _PATH, _SOURCE, state=STATE_INDEXED)
        span = await read_bench.tool().read(TIER_A, _PATH)
        assert span.stale is False
        assert "STALE" not in span.header.upper()


class TestStoreReadContainment:
    """The input contract rejects an absolute path or a ``../`` traversal up front —
    the same clean rejection ``read_file`` gives (the store lookup cannot traverse,
    but the contract must match so the P8d flip is seamless)."""

    async def test_absolute_path_is_rejected(self, read_bench: ReadBench) -> None:
        with pytest.raises(StoreReadContainmentError) as exc_info:
            await read_bench.tool().read(TIER_A, "/etc/passwd")
        message = str(exc_info.value)
        assert "containment" in message.lower() or "traversal" in message.lower()

    async def test_dotdot_traversal_is_rejected(self, read_bench: ReadBench) -> None:
        with pytest.raises(StoreReadContainmentError) as exc_info:
            await read_bench.tool().read(TIER_A, "../secret.py")
        message = str(exc_info.value)
        assert "containment" in message.lower() or "traversal" in message.lower()

    async def test_nested_dotdot_traversal_is_rejected(self, read_bench: ReadBench) -> None:
        with pytest.raises(StoreReadContainmentError):
            await read_bench.tool().read(TIER_A, "models/../../secret.py")


class TestStoreReadConnectionDown:
    """A downed store connection propagates loudly as ``SurrealConnectionError`` —
    NEVER masqueraded as a not-found (a silent empty would be misread as "the file
    isn't indexed")."""

    async def test_store_down_raises_connection_error_not_not_found(
        self, read_bench: ReadBench
    ) -> None:
        with pytest.raises(SurrealConnectionError):
            await read_bench.down_tool().read(TIER_A, _PATH)

    async def test_connection_error_is_not_a_store_read_error(
        self, read_bench: ReadBench
    ) -> None:
        # A transport failure is distinct from every StoreReadError mode — a
        # caller catching StoreReadNotFoundError must NOT swallow a down server.
        with pytest.raises(SurrealConnectionError) as exc_info:
            await read_bench.down_tool().read(TIER_A, _PATH)
        assert not isinstance(exc_info.value, StoreReadError)


class TestStoreReadFileParity:
    """The store-read span is byte-identical to ``read_file``'s span over the SAME
    source where disk and store agree — the guarantee that makes the P8d flip
    seamless (span semantics reuse ``ReadFileTool._resolve_span`` verbatim)."""

    @staticmethod
    def _disk_tool(live_root: Any, snapshot_root: Any) -> ReadFileTool:
        return ReadFileTool(
            live_roots={TIER_A: live_root},
            snapshot_layout=SnapshotLayout(snapshot_root),
            known_tiers={TIER_A},
        )

    @pytest.mark.parametrize(
        ("line_start", "line_end"),
        [(None, None), (1, 1), (3, 5), (9, None), (8, 999), (1, 10)],
    )
    async def test_store_span_matches_disk_span(
        self, read_bench: ReadBench, tmp_path: Any, line_start: int | None, line_end: int | None
    ) -> None:
        # Disk side: the same source materialised under a live root.
        live_root = tmp_path / "checkout"
        target = live_root / _PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(_SOURCE, encoding="utf-8")
        disk_span = self._disk_tool(live_root, tmp_path / "snap").read_file(
            TIER_A, _PATH, line_start, line_end
        )
        # Store side: the SAME source seeded into the store.
        await read_bench.seed(TIER_A, _PATH, _SOURCE)
        store_span = await read_bench.tool().read(TIER_A, _PATH, line_start, line_end)

        # The resolved span — start, end, and the exact bytes — is identical.
        assert store_span.line_start == disk_span.line_start
        assert store_span.line_end == disk_span.line_end
        assert store_span.text == disk_span.text
