"""RED contract for packet 47a — the twelfth seam: extension ingest entity-fragment.

The ONE seam the framework's eleven do not include: a per-file, extension-
contributed **ingest fragment** (typed entity NODES + two-phase cross-file
``ENFORCED`` edges) composed into the SAME ``SurrealStore.apply`` transaction as
the file's other producers, so entities and the manifest row commit-or-roll-back
together; a **claimed** file skips chunking (``n_chunks=0``); cross-file edges
resolve in a SECOND phase at full-sweep completion (purge-by-scope + ``RELATE``).

RULED design (execute VERBATIM, cite by §, never re-litigate):
``docs/design/2026-08-14-packet47-ingest-entity-seam-design.md`` — Q1-Q6, §7
(sink purge), §8 (surfaces), §9 (9 self-attack pins), §10 (store-law).
Companion: ``docs/design/2026-08-14-edition-precedence-mechanism.md`` (47a exposes
ONLY the phase-2 resolver HOOK + the F6 slug-leading index — NO edition logic).
Store law CITED: ``docs/reference/surrealdb-31-capabilities.md``.

Every test class is labelled ``# PHASE 1`` or ``# PHASE 2`` so ONE adversary owns
the cross-phase pins (F1, the §Q2.3 atomicity window, the chunk-skip∧entity
conjunction) as a unit. Each test names its design § and the pin id (P1..P26).

RED STRATEGY (why the file COLLECTS but the behaviour pins FAIL BEHAVIOURALLY).
The five ingest seam methods + ``IngestBackend`` + the ``Indexer(extensions=...)``
param are INERT STUBS (packet 47a contract) so the file imports and the inert
pins (P1) pass; every BEHAVIOUR pin exercises a wiring the BUILDER has not written
(the claimed-file compose branch, the phase-2 trigger, the in-``delete_by_tier``
purge, the watcher/reconcile entity purge, the ``build_app_context`` ingest-backend
rail) and so REDs on missing rows / a missing method / an un-raised error at the
seam — never on a collection ImportError. Runs against spike-surreal
``ws://127.0.0.1:18000`` ONLY (NEVER ``:18500``) with per-test DB isolation.
"""

from __future__ import annotations

import ast
import asyncio
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pytest
import pytest_asyncio
from _enforced_relations_scaffold import (
    apply_ddl,
    ghost_id,
    migration_db,  # noqa: F401 - re-exported pytest fixture
)
from _extension_helpers import register_in_discovery
from _ingest_entity_fixtures import (
    FAKE_LINK_DDL_ENFORCED,
    FAKE_LINK_DDL_UNENFORCED,
    FAKE_LINK_TABLE,
    FAKE_NODE_DDL,
    FAKE_NODE_TABLE,
    FAKE_SUFFIX,
    FakeDomainStore,
    FakeIngestConfigModel,
    FakeIngestExtension,
    LifecycleProbeExtension,
    entity_param_prefix,
)
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    surreal_env,  # noqa: F401 - re-exported pytest fixture
    surreal_password,
    surreal_url,
    surreal_user,
)
from loremaster.config import LoreConfig
from loremaster.extension import Extension, ExtensionContext, IngestBackend, ResolvedScope
from loremaster.graph_surreal import SurrealCodeGraph
from loremaster.index.indexer import Indexer, graph_roots
from loremaster.index.manifest import STATE_INDEXED
from loremaster.index.reconcile import ReconcileEngine
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.index.watcher import LiveWatcher
from loremaster.server import LoreServer
from loremaster.store._txn import TxnFragment
from loremaster.store.surreal import SurrealStore
from loresigil.testing import FakeEmbedder
from pydantic import SecretStr
from surrealdb import AsyncSurreal, RecordID

# The tier the machine-tier ``.fake`` files live under.
_TIER = "custom"
_DIM = PRODUCTION_DIM

# The repository root + the production package dir (for the derived-scan pin P8).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_PACKAGE_DIR = _REPO_ROOT / "loremaster" / "loremaster"
_EXTENSION_SOURCE_PATH = _PACKAGE_DIR / "extension.py"


def _entity_config(
    *, slug: str, live_path: Path, extensions: dict[str, dict[str, Any]] | None = None
) -> LoreConfig:
    """A single-live-root config that CLAIMS ``.fake`` and chunks it as markdown.

    ``.fake`` maps to the registered ``markdown`` chunker so a NON-claimed
    ``.fake`` file yields ``n_chunks>=1`` — which is what makes the chunk-skip
    leg of the conjunction pin (§Q2.3) DISCRIMINATE a build that composes entities
    but forgets the skip. A correct claimed build yields ``n_chunks=0`` instead.
    """
    payload: dict[str, Any] = {
        "schema_version": 1,
        "anthropic": {"api_key_env": "ANTHROPIC_API_KEY"},
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://tei.example:8080",
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
        # No explicit ``database`` — it defaults to the (unique) project slug, so
        # build_app_context writes to its own throwaway DB. Only build_app_context
        # (P11/P12) reads this block; entity_bench passes explicit connection params.
        "surreal": {
            "url": surreal_url(),
            "namespace": "lore_test",
            "user_env": "SURREAL_USER",
            "password_env": "SURREAL_PASS",
        },
        "roots": [
            {
                "tier": _TIER,
                "watch": "live",
                "path": str(live_path),
                "include": ["**/*.py", "**/*.fake"],
                "exclude": [],
            }
        ],
        "include": [],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}, ".fake": {"chunker": "markdown"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9201},
        "extensions": extensions or {},
    }
    return LoreConfig.model_validate(payload)


@dataclass(frozen=True)
class _EntityBench:
    """A fully-wired Indexer + fake domain store on ONE fresh spike-surreal DB."""

    indexer: Indexer
    engine: ReconcileEngine
    store: SurrealStore
    manifest: SurrealManifest
    graph: SurrealCodeGraph
    domain: FakeDomainStore
    ext: FakeIngestExtension
    env: SurrealEnv
    config: LoreConfig
    live_root: Path


@pytest_asyncio.fixture()
async def entity_bench(
    surreal_env: SurrealEnv,  # noqa: F811 - re-exported harness fixture
    tmp_path: Path,
) -> AsyncIterator[_EntityBench]:
    """Store + manifest + graph + FakeDomainStore + FakeIngestExtension + Indexer on one DB.

    Mirrors ``test_indexer_surreal_integration.bench`` and adds the fake domain
    store (readied like ``code_graph``) + the fake ingest extension threaded into
    ``Indexer(extensions=[...])``. The book_ranks encode the fixture stand-in
    total order (edition supersession — Bp newest).
    """
    live_root = tmp_path / "live"
    (live_root / "books").mkdir(parents=True)
    config = _entity_config(slug=surreal_env.database, live_path=live_root)
    snapshot_root = tmp_path / "snap"

    # Domain FIRST so its entity_tables() feeds the store (DG1 — the tier-purge
    # channel a bare store needs to identify fake_node).
    domain = FakeDomainStore(
        url=surreal_env.url, namespace=surreal_env.namespace, database=surreal_env.database,
        user=surreal_env.user, password=surreal_env.password,
    )
    store = SurrealStore(
        url=surreal_env.url, namespace=surreal_env.namespace, database=surreal_env.database,
        dim=_DIM, user=surreal_env.user, password=surreal_env.password,
        entity_tables=domain.entity_tables(),
    )
    manifest = SurrealManifest(
        url=surreal_env.url, namespace=surreal_env.namespace, database=surreal_env.database,
        user=surreal_env.user, password=surreal_env.password,
    )
    tier_roots, project_roots = graph_roots(config, snapshot_root)
    graph = SurrealCodeGraph(
        url=surreal_env.url, namespace=surreal_env.namespace, database=surreal_env.database,
        user=surreal_env.user, password=surreal_env.password,
        tier_roots=tier_roots, project_roots=project_roots,
    )
    await store.ensure_ready()
    await manifest.ensure_ready()
    await graph.ensure_ready()
    await domain.ensure_ready()

    ext = FakeIngestExtension(domain_store=domain, book_ranks={"A": 1, "B": 2, "Bp": 3})
    server = LoreServer(config)
    indexer = Indexer(
        store=store, embedder=FakeEmbedder(dim=_DIM), manifest=manifest,
        registry=server.registry, source_providers=[], config=config,
        snapshot_root=snapshot_root, code_graph=graph, extensions=[ext],
    )
    # CF7: reconcile reaches the claiming extension via its OWN extensions= param
    # (the code_graph precedent), NOT reach-through-indexer.
    engine = ReconcileEngine(
        indexer=indexer, manifest=manifest, store=store, config=config, code_graph=graph,
        extensions=[ext],
    )
    try:
        yield _EntityBench(
            indexer=indexer, engine=engine, store=store, manifest=manifest, graph=graph,
            domain=domain, ext=ext, env=surreal_env, config=config, live_root=live_root,
        )
    finally:
        await store.close()
        await manifest.close()
        await graph.close()
        await domain.close()


# --- read-back helpers (fresh admin connection; the cross-connection witness) --
async def _fetch_nodes(env: SurrealEnv) -> list[dict[str, Any]]:
    connection = await connect_admin(env)
    try:
        result = await run(
            connection, f"SELECT slug, source_book, kind, tier, file_path FROM {FAKE_NODE_TABLE}"
        )
    finally:
        await connection.close()
    return [row for row in result if isinstance(row, dict)] if isinstance(result, list) else []


async def _fetch_links(env: SurrealEnv) -> list[tuple[list[Any], list[Any], str]]:
    """Every ``fake_link`` edge as ``(in_id, out_id, source_book)`` tuples."""
    connection = await connect_admin(env)
    try:
        result = await run(connection, f"SELECT in, out, source_book FROM {FAKE_LINK_TABLE}")
    finally:
        await connection.close()
    rows = [row for row in result if isinstance(row, dict)] if isinstance(result, list) else []
    return sorted(
        (list(row["in"].id), list(row["out"].id), str(row["source_book"])) for row in rows
    )


async def _store_chunk_count(store: SurrealStore, tier: str, path: str) -> int:
    """How many chunk rows the store holds for ``(tier, path)`` (0 for a claimed file)."""
    rows = await store.scroll({"tier": tier, "file_path": path}, limit=1000)
    return len(rows)


def _white_box_indexer(tmp_path: Path, *, extensions: list[Extension]) -> Indexer:
    """An Indexer whose stores are UNCONNECTED — for pure fragment-builder pins.

    ``_compose_file_fragments`` / the ``_entity_fragment`` helper build fragments
    PURELY (no socket), so a white-box pin needs no live DB — only real store /
    manifest instances (their fragment builders are pure) and the extension list.
    """
    env_slug = tmp_path.name
    store = SurrealStore(
        url="ws://127.0.0.1:18000/rpc", namespace="lore_test", database=env_slug,
        dim=8, user="root", password=SecretStr("spikeroot"),
    )
    manifest = SurrealManifest(
        url="ws://127.0.0.1:18000/rpc", namespace="lore_test", database=env_slug,
        user="root", password=SecretStr("spikeroot"),
    )
    config = _entity_config(slug=env_slug, live_path=tmp_path)
    return Indexer(
        store=store, embedder=FakeEmbedder(dim=8), manifest=manifest,
        registry=LoreServer(config).registry, source_providers=[], config=config,
        snapshot_root=tmp_path / "snap", code_graph=None, extensions=extensions,
    )


def _ctx(bench: _EntityBench) -> ExtensionContext:
    """A real ExtensionContext over the bench's live resources (for seam calls)."""
    return ExtensionContext(
        store=bench.store, embedder=FakeEmbedder(dim=_DIM), config=bench.config,
        count_tokens=lambda texts: [len(text) for text in texts], manifest=bench.manifest,
    )


# A two-node, one-edge ``.fake`` file: node kinds ``monster`` + ``feature`` (≥2
# kinds, §Q1.4 — never a single-kind fixture). ``edge a f`` is intra-file here.
_FILE_A = "book A\nnode monster a Aye the Ancient\nnode feature f Frightful Presence\nedge a f\n"


# ===========================================================================
# PHASE 1 — fragment shape, composition, namespacing, gating, transactionality
# ===========================================================================


class TestInertDefaults:
    """P1 (§Q1.1) — a zero-ingest extension and a zero-extension compose are inert."""

    def test_base_extension_ingest_seams_are_inert(self) -> None:
        """P1a: a bare (name-only) Extension returns every seam's safe inert default."""

        class _Bare(Extension):
            @property
            def name(self) -> str:
                return "bare"

        bare = _Bare()
        ctx = _fake_ctx()
        assert bare.claims(_TIER, "x.fake") is False
        assert bare.entity_fragment(_TIER, "x.fake", "text", ctx) is None
        assert bare.entity_purge_fragment(_TIER, "x.fake") is None
        assert bare.ingest_backends(ctx) == []

    async def test_base_extension_resolve_edges_is_empty(self) -> None:
        """P1b: the async resolve-edges seam defaults to no edges."""

        class _Bare(Extension):
            @property
            def name(self) -> str:
                return "bare"

        assert await _Bare().resolve_edges(_fake_ctx(), None) == []

    def test_zero_extension_compose_has_no_entity_params(self, tmp_path: Path) -> None:
        """P1c: with NO extensions, composing a file emits ZERO ``xt_``-prefixed params.

        The inert-default regression guard — a zero-extension server has no entity
        behaviour, byte-for-byte. GREEN now AND after the build.
        """
        indexer = _white_box_indexer(tmp_path, extensions=[])
        fragments = indexer._compose_file_fragments(  # noqa: SLF001 - white-box compose pin
            tier=_TIER, path="mod.py", source="print('hi')\n", content_hash="0" * 128,
            records=[], vectors=[], new_ids=[], mtime_ns=0, size=0, chunks=[],
        )
        keys = [key for fragment in fragments for key in dict(fragment.params)]
        offenders = [key for key in keys if key.startswith("xt_")]
        assert offenders == [], f"a zero-extension compose leaked entity params: {offenders}"


class TestSeamCountIsTwelve:
    """P2 (§Q1.1 naming note) — the natural-language seam count is TWELVE, not eleven."""

    def test_extension_module_teaches_twelve_seams(self) -> None:
        """P2: the docstring/comment surface says ``twelve``; ``eleven seams`` is gone.

        The rename-sweep natural-language-surface pin (CLAUDE.md): a stale
        ``eleven`` teaches a wrong contract to the LLM that reads the module. RED
        until the builder updates the count AND adds seam 12 to the numbered list.
        """
        source = _EXTENSION_SOURCE_PATH.read_text(encoding="utf-8")
        assert "eleven seams" not in source, (
            "the Extension surface still says 'the eleven seams' — the ingest seam "
            "is the TWELFTH; update every seam-count surface (§Q1.1 naming note)"
        )
        assert "twelve seams" in source, (
            "no surface teaches 'twelve seams' — the seam-count naming note (§Q1.1) "
            "requires the eleven→twelve update"
        )
        assert "12." in source or "seam 12" in source, (
            "the numbered seam list never reaches item 12 — the ingest seam must be "
            "enumerated, not just default-defined"
        )


class TestClaimedFileComposition:
    """P3/P4 (§Q1.2/§Q2.3) — a claimed file composes entities + skips chunking."""

    async def test_claimed_file_composes_entity_nodes(self, entity_bench: _EntityBench) -> None:
        """P3 (§Q1.2): indexing a claimed ``.fake`` file lands its entity NODES.

        The entity fragment is composed into the SAME per-file ``apply`` as the
        manifest — so the rows only exist if the claimed-file branch fired. RED
        until the branch is built (0 rows today).
        """
        await entity_bench.indexer.index_file(_TIER, "books/a.fake", _FILE_A)
        nodes = [row for row in await _fetch_nodes(entity_bench.env) if row["file_path"] == "books/a.fake"]
        slugs = {row["slug"] for row in nodes}
        kinds = {row["kind"] for row in nodes}
        assert slugs == {"a", "f"}, f"expected both nodes composed, got {slugs}"
        assert kinds == {"monster", "feature"}, f"expected ≥2 node KINDS, got {kinds}"

    async def test_claimed_file_conjunction_nchunks_zero_and_entities_present(
        self, entity_bench: _EntityBench
    ) -> None:
        """P4 (§Q2.3 frontier-1): n_chunks==0 AND entity rows PRESENT, in ONE apply.

        The CONJUNCTION rejects BOTH one-legged wrong builds: skip-chunk-but-no-
        entities (fails the entity leg), and entities-but-no-chunk-skip (fails the
        n_chunks==0 leg — a non-claimed ``.fake`` chunks as markdown, n_chunks>=1).
        """
        await entity_bench.indexer.index_file(_TIER, "books/a.fake", _FILE_A)
        row = await entity_bench.manifest.get(_TIER, "books/a.fake")
        assert row is not None and row.state == STATE_INDEXED
        chunk_rows = await _store_chunk_count(entity_bench.store, _TIER, "books/a.fake")
        node_rows = [r for r in await _fetch_nodes(entity_bench.env) if r["file_path"] == "books/a.fake"]
        assert row.n_chunks == 0, f"chunk-skip did not take: n_chunks={row.n_chunks}"
        assert chunk_rows == 0, f"a claimed file left {chunk_rows} chunk rows (bare DELETE missing)"
        assert len(node_rows) > 0, "the conjunction requires entity rows PRESENT, found none"


class TestTransactionality:
    """P5 (§Q2.3) — a rejected entity statement rolls the WHOLE file back."""

    async def test_forced_entity_failure_leaves_no_indexed_row_and_no_nodes(
        self, entity_bench: _EntityBench
    ) -> None:
        """P5 (§Q2.3, R2 frontier-2): entity failure ⇒ NO node rows AND not INDEXED.

        Assert 'not INDEXED' (NOT 'no manifest row' — the fault-isolation path may
        write a FAILED row). Positive control below proves the clean build commits
        BOTH. RED until phase-1 composes the entity fragment (today: no entity
        statement runs, so the file indexes clean — the 'not INDEXED' leg fails).
        """

        class _PoisonEntity(FakeIngestExtension):
            def entity_fragment(self, tier: str, path: str, text: str, ctx: ExtensionContext) -> TxnFragment | None:  # noqa: E501
                fragment = super().entity_fragment(tier, path, text, ctx)
                if fragment is None:
                    return None
                # Append a statement the engine ALWAYS rejects, in the SAME fragment.
                return TxnFragment(
                    statements=[*fragment.statements, "THROW 'forced entity failure';"],
                    params=dict(fragment.params),
                )

        entity_bench.indexer._extensions = (  # noqa: SLF001 - swap in the poisoned reference build
            _PoisonEntity(domain_store=entity_bench.domain),
        )
        # index_file may RAISE the SurrealStoreError OR catch it into a FAILED row
        # (the fault-isolation path); atomicity is proven by the STORE state either way.
        try:
            await entity_bench.indexer.index_file(_TIER, "books/a.fake", _FILE_A)
        except Exception:  # noqa: BLE001 - a raised rollback is one legal outcome
            pass
        row = await entity_bench.manifest.get(_TIER, "books/a.fake")
        assert row is None or row.state != STATE_INDEXED, (
            "atomicity lost: a rejected entity statement left an INDEXED manifest row"
        )
        nodes = [r for r in await _fetch_nodes(entity_bench.env) if r["file_path"] == "books/a.fake"]
        assert nodes == [], f"atomicity lost: {len(nodes)} entity rows survived a rolled-back apply"

    async def test_positive_control_clean_build_commits_both(
        self, entity_bench: _EntityBench
    ) -> None:
        """P5 positive control: an un-poisoned claimed ingest commits nodes AND INDEXED."""
        await entity_bench.indexer.index_file(_TIER, "books/a.fake", _FILE_A)
        row = await entity_bench.manifest.get(_TIER, "books/a.fake")
        nodes = [r for r in await _fetch_nodes(entity_bench.env) if r["file_path"] == "books/a.fake"]
        assert row is not None and row.state == STATE_INDEXED
        assert len(nodes) == 2

    async def test_framework_failure_leaves_no_orphan_entity_rows(
        self, entity_bench: _EntityBench, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CF2 (THE QUANTIFIER LAW — the ∀-direction P5 was missing).

        P5 pins only "entity fails ⇒ nothing INDEXED". The REVERSE ("the FRAMEWORK
        apply fails ⇒ no ORPHAN entity rows") was unpinned, so a non-atomic
        separate-apply build (entity written in its OWN apply before the file's
        main apply) passes P3/P4/P5 while orphaning entities whenever the main apply
        fails (adversary Probe-6). Here the entity fragment is VALID but the
        FRAMEWORK chunk-replace fragment is poisoned: an ATOMIC build rolls the
        whole file back (no entity rows, not INDEXED); a separate-apply build
        leaves the entity rows behind. Positive control below commits both.
        """
        real_replace = entity_bench.store.replace_file_fragment

        def _poisoned_replace(tier: str, file_path: str, records_with_vectors: Any) -> TxnFragment:
            fragment = real_replace(tier, file_path, records_with_vectors)
            return TxnFragment(
                statements=[*fragment.statements, "THROW 'framework fragment forced failure';"],
                params=dict(fragment.params),
            )

        monkeypatch.setattr(entity_bench.store, "replace_file_fragment", _poisoned_replace)
        try:
            await entity_bench.indexer.index_file(_TIER, "books/a.fake", _FILE_A)
        except Exception:  # noqa: BLE001 - a raised rollback is one legal outcome
            pass
        row = await entity_bench.manifest.get(_TIER, "books/a.fake")
        nodes = [r for r in await _fetch_nodes(entity_bench.env) if r["file_path"] == "books/a.fake"]
        assert nodes == [], (
            f"framework apply failed but {len(nodes)} ORPHAN entity rows survived — the "
            "entity write is NOT atomic with the file's apply (separate-apply build)"
        )
        assert row is None or row.state != STATE_INDEXED, (
            "a framework failure left an INDEXED manifest row (atomicity lost)"
        )

    async def test_framework_failure_positive_control_clean_commits_both(
        self, entity_bench: _EntityBench
    ) -> None:
        """CF2 positive control: without the framework poison, the claimed ingest commits both."""
        await entity_bench.indexer.index_file(_TIER, "books/a.fake", _FILE_A)
        row = await entity_bench.manifest.get(_TIER, "books/a.fake")
        nodes = [r for r in await _fetch_nodes(entity_bench.env) if r["file_path"] == "books/a.fake"]
        assert row is not None and row.state == STATE_INDEXED
        assert len(nodes) == 2


class TestOneImplementation:
    """P6 (§Q5/R6) — the entity write rides ``compose``, not a private path."""

    async def test_entity_write_reddens_with_the_shared_compose_cap(
        self, entity_bench: _EntityBench, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """P6: shrinking the SHARED ``TXN_STATEMENT_HARD_CAP`` blocks the ENTITY rows.

        Prove-by-mutation (CLAUDE.md #102/#120 — routing ≠ sharing): with the cap
        at 1, ANY ``compose`` refuses the file's multi-statement apply, so a
        correct build (entity fragment composed INTO that apply) lands NO entity
        rows. A build that hand-rolls a private writer (bypassing ``compose``)
        would leave the rows behind — this pin catches it. Positive control: with
        the cap restored, the same index DOES land entity rows.
        """
        import loremaster.store._txn as txn_module

        # Positive control leg — the entity path lands rows when compose is healthy.
        await entity_bench.indexer.index_file(_TIER, "books/ctrl.fake", "book A\nnode monster c Ctrl\n")
        control = [r for r in await _fetch_nodes(entity_bench.env) if r["file_path"] == "books/ctrl.fake"]
        assert len(control) == 1, "positive control: a healthy compose must land the entity node"

        # Mutation leg — a shared-cap of 1 must reach the entity path. index_file
        # CATCHES SurrealStoreError and returns a FAILED outcome (§Q2.3 fault-
        # isolation — it NEVER raises), so `capped == []` is the SOLE discriminator
        # (CF1): a correct build's entity rows vanish with the refused apply; a
        # private-writer (routing≠sharing) build leaves them behind.
        monkeypatch.setattr(txn_module, "TXN_STATEMENT_HARD_CAP", 1)
        await entity_bench.indexer.index_file(_TIER, "books/a.fake", _FILE_A)
        capped = [r for r in await _fetch_nodes(entity_bench.env) if r["file_path"] == "books/a.fake"]
        assert capped == [], (
            "the entity write did NOT flow through the shared compose (its rows "
            "survived a cap that refused the file's apply) — a private writer path"
        )


class TestNamespacing:
    """P7 (§Q1.3) — entity fragment params are ``xt_<name>_``, proven over ≥2 names."""

    def test_entity_fragment_params_are_name_namespaced(self, tmp_path: Path) -> None:
        """P7: ``_entity_fragment`` returns the claimant's ``xt_<name>_`` params.

        Uses TWO extension names (``fake`` / ``fake2``) on two suffixes so a build
        that hardcodes ``fake`` in the prefix (parameter-monoculture) fails the
        ``fake2`` leg. RED until the ``_entity_fragment`` dispatch helper exists.
        """
        for name, suffix, source in (
            ("fake", ".fake", _FILE_A),
            ("fake2", ".fake2", "book B\nnode monster b Bee\n"),
        ):
            domain = FakeDomainStore(
                url="ws://127.0.0.1:18000/rpc", namespace="lore_test", database=tmp_path.name,
                user="root", password=SecretStr("spikeroot"),
            )

            class _Alt(FakeIngestExtension):
                def claims(self, tier: str, path: str) -> bool:
                    return path.endswith(suffix)  # noqa: B023 - bound per loop iteration by design

            ext = _Alt(domain_store=domain, name=name)
            indexer = _white_box_indexer(tmp_path, extensions=[ext])
            # ``_entity_fragment`` is BUILDER code (absent today) — cast so mypy does
            # not flag the intentional not-yet-existing seam, and no unused-ignore
            # survives once the builder adds it.
            fragment = cast(Any, indexer)._entity_fragment(  # noqa: SLF001 - white-box dispatch pin
                _TIER, f"books/x{suffix}", source, _fake_ctx()
            )
            assert fragment is not None
            prefix = entity_param_prefix(name)
            bad = [key for key in dict(fragment.params) if not key.startswith(prefix)]
            assert bad == [], f"params not under {prefix!r}: {bad}"


class TestIndexerConstructionSitesDerivedScan:
    """P8 (F3/§Q1.2) — EVERY ``Indexer(...)`` production site threads ``extensions=``."""

    def test_all_production_indexer_constructions_pass_extensions(self) -> None:
        """P8: a DERIVED AST scan (registration_sites idiom) — never a hand-list of 4.

        A 5th construction site that omits ``extensions=`` is caught because the
        SET is derived from the source, not enumerated. BANNED: ``len(sites)==4``.
        """
        sites = _find_indexer_construction_sites(_production_python_roots())
        assert sites, "the derived scan found ZERO Indexer(...) sites — the scan is blind"
        offenders = [
            f"{path}:{lineno}"
            for path, lineno, has_extensions in sites
            if not has_extensions
        ]
        assert offenders == [], (
            "these production Indexer(...) sites do NOT pass extensions= (F3 — each "
            f"must thread the extension list): {offenders}"
        )


def _claiming_extension_helper() -> Any:
    """The shared ``claiming_extension`` helper, or None (absent pre-build).

    Read LIVE off the module (never import-bound) so a test can monkeypatch it —
    the EXTENSION_REGISTRY idiom — which is exactly what makes CF8's mutation proof
    of ONE IMPLEMENTATION binding: all 3 sites must reference it the same live way.
    """
    import loremaster.extension as extension_module

    return getattr(extension_module, "claiming_extension", None)


class TestClaimExclusivity:
    """P9 + CF8 (§Q1.2/R5 · D1 rider) — ONE shared exclusivity helper across 3 sites."""

    def test_shared_helper_raises_naming_both(self, tmp_path: Path) -> None:
        """P9: the shared ``claiming_extension(extensions, tier, path)`` raises naming BOTH.

        RED until the shared helper exists (getattr is None today). At most one
        ``claims()`` True per ``(tier, path)``; two is a LOUD error naming both.
        """
        helper = _claiming_extension_helper()
        assert helper is not None, (
            "no shared loremaster.extension.claiming_extension helper — the "
            "exclusivity rule must be ONE function 3 sites call, not a per-site clone (CF8)"
        )
        domain = FakeDomainStore(
            url="ws://127.0.0.1:18000/rpc", namespace="lore_test", database=tmp_path.name,
            user="root", password=SecretStr("spikeroot"),
        )
        one = FakeIngestExtension(domain_store=domain, name="fake_one")
        two = FakeIngestExtension(domain_store=domain, name="fake_two")
        with pytest.raises(Exception) as exc_info:
            helper([one, two], _TIER, "books/a.fake")
        message = str(exc_info.value)
        assert "fake_one" in message and "fake_two" in message, (
            f"a two-claimant collision must raise LOUDLY naming BOTH extensions; got: {message!r}"
        )

    async def test_all_three_sites_route_through_the_shared_helper(
        self, entity_bench: _EntityBench, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CF8 (ONE IMPLEMENTATION, prove-by-mutation): the 3 claim sites SHARE the rule.

        Mutate the shared helper (make it raise on ANY call); then EACH of the 3
        claim sites — ``Indexer._entity_fragment``, ``watcher._purge``,
        ``reconcile._purge_file`` — must propagate the mutation. A site that
        hand-rolls a private exclusivity check stays green = routing≠sharing. RED
        until the shared helper exists AND all 3 route through it (via the live
        module reference — the EXTENSION_REGISTRY idiom).
        """
        import loremaster.extension as extension_module

        assert _claiming_extension_helper() is not None, (
            "no shared claiming_extension helper — CF8 cannot prove sharing (RED)"
        )
        sentinel = RuntimeError("claiming_extension MUTATED (raise-on-any)")

        def _mutated(extensions: Any, tier: str, path: str) -> Any:
            raise sentinel

        monkeypatch.setattr(extension_module, "claiming_extension", _mutated)
        watcher = LiveWatcher(
            indexer=entity_bench.indexer, manifest=entity_bench.manifest, store=entity_bench.store,
            config=entity_bench.config, loop=asyncio.get_running_loop(),
            reconcile_engine=entity_bench.engine, code_graph=entity_bench.graph,
            extensions=[entity_bench.ext],
        )
        entity_bench.live_root.joinpath("books", "x.fake").write_text(_FILE_A, encoding="utf-8")

        with pytest.raises(RuntimeError, match="MUTATED"):
            cast(Any, entity_bench.indexer)._entity_fragment(  # noqa: SLF001
                _TIER, "books/x.fake", _FILE_A, _ctx(entity_bench)
            )
        with pytest.raises(RuntimeError, match="MUTATED"):
            await cast(Any, watcher)._purge(_TIER, "books/x.fake")  # noqa: SLF001
        with pytest.raises(RuntimeError, match="MUTATED"):
            await cast(Any, entity_bench.engine)._purge_file(_TIER, "books/x.fake")  # noqa: SLF001


class TestBatchPathClaimedBranch:
    """P10 (§Q1.2) — the batch per-file compose shares the identical claimed branch."""

    def test_compose_for_a_claimed_file_emits_an_entity_fragment(self, tmp_path: Path) -> None:
        """P10a: ``_compose_file_fragments`` (records=[]) for a claimed file composes entities.

        Both the realtime commit AND ``_commit_batch_file`` call
        ``_compose_file_fragments`` — so the claimed branch living HERE covers both
        paths (ONE IMPLEMENTATION). RED until the branch is built.
        """
        domain = FakeDomainStore(
            url="ws://127.0.0.1:18000/rpc", namespace="lore_test", database=tmp_path.name,
            user="root", password=SecretStr("spikeroot"),
        )
        indexer = _white_box_indexer(
            tmp_path, extensions=[FakeIngestExtension(domain_store=domain)]
        )
        fragments = indexer._compose_file_fragments(  # noqa: SLF001 - white-box compose pin
            tier=_TIER, path="books/a.fake", source=_FILE_A, content_hash="0" * 128,
            records=[], vectors=[], new_ids=[], mtime_ns=0, size=0, chunks=[],
        )
        entity_keys = [
            key for fragment in fragments for key in dict(fragment.params)
            if key.startswith(entity_param_prefix("fake"))
        ]
        assert entity_keys, (
            "a claimed-file compose emitted NO xt_fake_ entity params — the claimed "
            "branch is unwired in _compose_file_fragments (both paths inherit it)"
        )

    def test_commit_batch_file_delegates_to_compose(self) -> None:
        """P10b (ONE IMPLEMENTATION): ``_commit_batch_file`` calls ``_compose_file_fragments``.

        Guards that the builder does NOT hand-roll a SEPARATE batch compose — both
        paths must share the one branch. GREEN now and after (a regression guard).
        """
        source = (_PACKAGE_DIR / "index" / "indexer.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        batch = next(
            node for node in ast.walk(tree)
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "_commit_batch_file"
        )
        calls = {
            child.func.attr
            for child in ast.walk(batch)
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute)
        }
        assert "_compose_file_fragments" in calls, (
            "_commit_batch_file must delegate to _compose_file_fragments so the "
            "claimed-file branch is shared, not cloned (ONE IMPLEMENTATION)"
        )


class TestOrderingRail:
    """P11 (§Q4) — the ingest backend readies BEFORE the Indexer is constructed."""

    async def test_ingest_backend_readies_before_indexer(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """P11: the domain store's ``ensure_ready`` precedes ``Indexer.__init__``.

        A fragment references tables the DDL defined, so the backend must ride the
        ``write_stack_readied`` rail before the Indexer. Observed via a shared
        lifecycle log: ``ready:lifecycle_probe`` must precede ``indexer_built``. RED
        until the ingest-backend rail is wired (today the backend never readies).
        """
        LifecycleProbeExtension.reset()
        original_init = Indexer.__init__

        def _spy_init(self: Indexer, **kwargs: Any) -> None:
            LifecycleProbeExtension.LIFECYCLE_LOG.append("indexer_built")
            original_init(self, **kwargs)

        monkeypatch.setattr(Indexer, "__init__", _spy_init)
        ctx = await _build_probe_app_context(tmp_path, monkeypatch, start_tasks=False)
        try:
            log = LifecycleProbeExtension.LIFECYCLE_LOG
            assert "ready:lifecycle_probe" in log, (
                "the ingest backend never readied on the write-stack rail (§Q4)"
            )
            assert "indexer_built" in log
            assert log.index("ready:lifecycle_probe") < log.index("indexer_built"), (
                f"the ingest backend must ready BEFORE the Indexer; log order: {log}"
            )
        finally:
            await ctx.aclose()


class TestUnwind:
    """P12 (F4) — the ingest backend is closed on BOTH teardown blocks + normal shutdown."""

    async def test_block1_ready_failure_closes_earlier_backends(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """P12a: a backend ``ensure_ready`` failure closes earlier write-stack collaborators."""
        import loremaster.index.surreal_manifest as manifest_module
        import loremaster.store.surreal as store_module

        LifecycleProbeExtension.reset()
        LifecycleProbeExtension.fail_ready = True
        opened: list[Any] = []
        _track(monkeypatch, store_module, "SurrealStore", opened)
        _track(monkeypatch, manifest_module, "SurrealManifest", opened)
        with pytest.raises(RuntimeError, match="refused to ready"):
            await _build_probe_app_context(tmp_path, monkeypatch, start_tasks=False)
        assert len(opened) >= 2, "the write store + manifest should have been opened"
        for handle in opened:
            assert handle._connection is None, (  # noqa: SLF001 - the closure signal
                f"{type(handle).__name__} leaked after the ingest backend's ready failed"
            )

    async def test_block2_sweep_failure_closes_the_ingest_backend(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """P12b (the rider the first draft missed): a failing initial-sweep phase-2 closes it.

        Phase-2 runs INSIDE the initial sweep = inside ``build_app_context``'s
        block 2, which closes a HARDCODED handle list omitting the ingest backend.
        RED until the backend is added to block 2 (today block 2 never runs phase-2,
        so the build succeeds and ``pytest.raises`` fails).
        """
        LifecycleProbeExtension.reset()
        LifecycleProbeExtension.fail_resolve = True
        with pytest.raises(RuntimeError, match="phase-2 resolve refused"):
            await _build_probe_app_context(tmp_path, monkeypatch, start_tasks=True)
        assert any(event == "close:lifecycle_probe" for event in LifecycleProbeExtension.LIFECYCLE_LOG), (
            "the ingest backend LEAKED on the block-2 (initial-sweep) failure path (F4)"
        )

    async def test_normal_shutdown_closes_the_ingest_backend(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """P12c: ``AppContext.aclose`` closes the ingest backend on a clean shutdown."""
        LifecycleProbeExtension.reset()
        ctx = await _build_probe_app_context(tmp_path, monkeypatch, start_tasks=False)
        await ctx.aclose()
        assert any(event == "close:lifecycle_probe" for event in LifecycleProbeExtension.LIFECYCLE_LOG), (
            "AppContext.aclose did not close the ingest backend (F4 normal shutdown)"
        )


class TestSinkPurge:
    """P13 (F5/§7) — the tier entity purge lives INSIDE ``delete_by_tier`` (the sink)."""

    async def test_delete_by_tier_removes_that_tiers_entity_rows(
        self, entity_bench: _EntityBench
    ) -> None:
        """P13 (DG1): after a tier purge, that tier's entity rows (and cascaded edges) are GONE.

        The store is told its entity tables via the DG1 channel (``entity_tables``
        fed from the backend's ``entity_tables()`` — adversary Probe-4: purges ONLY
        when told). Derived from the DATA op ("removes a claimed tier's rows"), NOT a
        purge-site hand-list. Entity rows are SEEDED directly (decoupled from the
        claimed-branch build) WITH a tier so ``DELETE fake_node WHERE tier`` is no
        silent no-op (#107). RED today: ``delete_by_tier`` purges chunks only.
        """
        # Seed entity rows for this tier via the store's shared apply (no claimed branch needed).
        fragment = entity_bench.ext.entity_fragment(_TIER, "books/a.fake", _FILE_A, _ctx(entity_bench))
        assert fragment is not None
        await entity_bench.store.apply([fragment])
        before = [r for r in await _fetch_nodes(entity_bench.env) if r["tier"] == _TIER]
        assert len(before) == 2, "fixture: two entity rows must be seeded before the purge"

        await entity_bench.store.delete_by_tier(_TIER)
        after = [r for r in await _fetch_nodes(entity_bench.env) if r["tier"] == _TIER]
        assert after == [], (
            f"delete_by_tier left {len(after)} entity rows — the tier entity purge is "
            "not co-located in the sink (F5); a chunk-only purge orphans entities"
        )


class TestPerFilePurge:
    """P14 (§7/CF7) — the per-file DELETE sites purge the file's entity slice too.

    CF7: watcher/reconcile reach the claiming extension via their OWN ``extensions=``
    ctor param (the code_graph precedent), NOT reach-through-indexer. The fixture
    clones ``test_watcher_delete_purges_graph_slice`` (test_graph_wiring.py).
    """

    async def _seed_entity_rows(self, bench: _EntityBench, rel_path: str) -> None:
        """Seed a claimed file's entity nodes + an INDEXED manifest row (WITH a tier)."""
        fragment = bench.ext.entity_fragment(_TIER, rel_path, _FILE_A, _ctx(bench))
        assert fragment is not None
        await bench.store.apply([fragment])
        await bench.manifest.replace(
            tier=_TIER, file_path=rel_path, sha512="0" * 128, mtime_ns=0, size=0,
            n_chunks=0, chunk_ids=[], state=STATE_INDEXED,
        )

    async def test_reconcile_deletion_purges_the_files_entity_rows(
        self, entity_bench: _EntityBench
    ) -> None:
        """P14a: ``reconcile._purge_file`` purges a deleted file's entity nodes (edges cascade).

        RED today: the reconcile purge composes chunk+graph deletes but not
        ``entity_purge_fragment`` (the engine now HOLDS the extensions via CF7).
        """
        await self._seed_entity_rows(entity_bench, "books/gone.fake")
        await entity_bench.engine.reconcile()  # the file is absent from disk ⇒ purged
        after = [r for r in await _fetch_nodes(entity_bench.env) if r["file_path"] == "books/gone.fake"]
        assert after == [], (
            f"reconcile left {len(after)} entity rows for a deleted file — the per-file "
            "purge does not call entity_purge_fragment (§7/CF7)"
        )

    async def test_watcher_delete_purges_the_files_entity_rows(
        self, entity_bench: _EntityBench, tmp_path: Path
    ) -> None:
        """P14b: ``watcher._purge`` composes ``entity_purge_fragment`` on a delete event.

        Clones ``test_watcher_delete_purges_graph_slice``: a LiveWatcher built WITH
        ``extensions=[ext]`` (CF7) whose ``_purge`` appends the entity purge into the
        SAME ``store.apply``. RED today (the watcher purge omits the entity slice).
        """
        gone = entity_bench.live_root / "books" / "watched.fake"
        gone.write_text(_FILE_A, encoding="utf-8")
        await self._seed_entity_rows(entity_bench, "books/watched.fake")
        watcher = LiveWatcher(
            indexer=entity_bench.indexer, manifest=entity_bench.manifest, store=entity_bench.store,
            config=entity_bench.config, loop=asyncio.get_running_loop(),
            reconcile_engine=entity_bench.engine, code_graph=entity_bench.graph,
            extensions=[entity_bench.ext],
        )
        gone.unlink()
        watcher.on_deleted_path(str(gone))
        await watcher.drain()
        after = [r for r in await _fetch_nodes(entity_bench.env) if r["file_path"] == "books/watched.fake"]
        assert after == [], (
            f"the watcher delete left {len(after)} entity rows — _purge does not compose "
            "entity_purge_fragment (§7/CF7)"
        )


class TestFileTextForClaimedFiles:
    """P15 (§Q1.4/R4) — NON-BLOCKING: a claimed file writes file_text provenance."""

    async def test_claimed_file_writes_file_text(self, entity_bench: _EntityBench) -> None:
        """P15 (CF6 — discriminates the CLAIMED branch; recommend WRITE, NON-BLOCKING).

        The adversary showed the first draft passed via the NON-claimed markdown
        path (a `.fake` is markdown-chunkable). This REQUIRES the file to be
        CLAIMED (``n_chunks==0``, chunking skipped) AND still carry file_text — so
        a build whose CLAIMED branch forgets file_text fails. Non-blocking: the
        operator/adversary may drop it. RED today (the `.fake` is not yet claimed,
        n_chunks≥1).
        """
        await entity_bench.indexer.index_file(_TIER, "books/a.fake", _FILE_A)
        row = await entity_bench.manifest.get(_TIER, "books/a.fake")
        assert row is not None and row.n_chunks == 0, (
            "P15 tests the CLAIMED branch — the file must be claimed (n_chunks==0) "
            f"before file_text provenance is meaningful; got n_chunks={None if row is None else row.n_chunks}"
        )
        connection = await connect_admin(entity_bench.env)
        try:
            result = await run(connection, "SELECT id FROM file_text")
        finally:
            await connection.close()
        rows = [r for r in result if isinstance(r, dict)] if isinstance(result, list) else []
        # file_text's id is the composite ``[tier, file_path]`` (no scalar fields).
        matches = [r for r in rows if tuple(r["id"].id) == (_TIER, "books/a.fake")]
        assert matches, "a CLAIMED file wrote no file_text row (§Q1.4/R4 recommends WRITE)"


# --- shared white-box + build_app_context helpers ---------------------------
def _fake_ctx() -> ExtensionContext:
    """A minimal ExtensionContext for pure white-box seam calls (no live store touched)."""
    return ExtensionContext(
        store=None, embedder=None, config=None,
        count_tokens=lambda texts: [len(text) for text in texts], manifest=None,
    )


def _production_python_roots() -> list[Path]:
    """The production Python trees an ``Indexer(...)`` could be constructed in.

    DERIVE the reach so it is NOT a hidden `loremaster/loremaster/`-only constant
    (CF3 / adversary Probe-2 leg B: a `scripts/` construction site was silently
    exempt). Covers the package AND every ``scripts/`` tree (repo + member) that
    exists — a future `scripts/` construction site is included the day it lands.
    Test trees are excluded (they legitimately construct Indexers with fakes).
    """
    candidates = [
        _PACKAGE_DIR,
        _REPO_ROOT / "scripts",
        _REPO_ROOT / "loremaster" / "scripts",
    ]
    return [root for root in candidates if root.is_dir()]


def _find_indexer_construction_sites(roots: list[Path]) -> list[tuple[str, int, bool]]:
    """DERIVE every ``Indexer(...)`` call site across ``roots`` (the registration_sites idiom).

    Returns ``(rel_path, lineno, passes_extensions)`` per site. A site is any call
    whose callee name is ``Indexer`` (a bare ``Name`` or an ``Attribute`` ending in
    ``Indexer``); a site 'passes extensions' iff it has an ``extensions`` keyword.
    Derived from source over ALL production roots, so a NEW site — even in a tree
    the first draft's reach excluded — is included the day it lands (CLAUDE.md
    reach law / F5).
    """
    sites: list[tuple[str, int, bool]] = []
    seen: set[Path] = set()
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = (
                    func.id if isinstance(func, ast.Name)
                    else func.attr if isinstance(func, ast.Attribute)
                    else None
                )
                if name != "Indexer":
                    continue
                has_extensions = any(keyword.arg == "extensions" for keyword in node.keywords)
                sites.append((str(path.relative_to(_REPO_ROOT)), node.lineno, has_extensions))
    return sites


def _track(
    monkeypatch: pytest.MonkeyPatch, module: Any, attribute: str, opened: list[Any]
) -> None:
    """Monkeypatch ``module.attribute`` to a subclass that records every instance opened."""
    base = getattr(module, attribute)

    class _Tracked(base):  # type: ignore[valid-type, misc]
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            opened.append(self)

    monkeypatch.setattr(module, attribute, _Tracked)


# Probe DBs (build_app_context defaults its DB to the unique slug) reaped on exit.
_pending_probe_slugs: list[str] = []


@pytest.fixture(autouse=True)
def _probe_surreal_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Export the harness root credentials build_app_context resolves + reap probe DBs.

    Mirrors ``test_mcp_server``'s autouse env fixture: build_app_context reads the
    Surreal user/pass from ``SURREAL_USER`` / ``SURREAL_PASS`` (named by the config
    ``surreal`` block) and defaults its database to the project slug.
    """
    monkeypatch.setenv("SURREAL_USER", surreal_user())
    monkeypatch.setenv("SURREAL_PASS", surreal_password().get_secret_value())
    yield


@pytest_asyncio.fixture(autouse=True)
async def _reap_probe_dbs() -> AsyncIterator[None]:
    """Drop every build_app_context probe database this test provisioned."""
    yield
    while _pending_probe_slugs:
        await drop_database(make_env(database=_pending_probe_slugs.pop(), dim=_DIM))


async def _build_probe_app_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, start_tasks: bool
) -> Any:
    """Build a real ``AppContext`` whose sole extension is the lifecycle probe.

    Discovers ``LifecycleProbeExtension`` through the REAL ``EXTENSION_REGISTRY``
    path so the ingest-backend rail / teardown wiring is exercised end-to-end.
    """
    from loremaster.server import build_app_context

    register_in_discovery(monkeypatch, {"lifecycle_probe": LifecycleProbeExtension})
    live = tmp_path / "live"
    (live / "books").mkdir(parents=True)
    (live / "books" / "a.fake").write_text(_FILE_A, encoding="utf-8")
    slug = f"probe_{tmp_path.name.replace('-', '_')}"
    _pending_probe_slugs.append(slug)
    config = _entity_config(
        slug=slug, live_path=live,
        extensions={"lifecycle_probe": {"flavour": "vanilla"}},
    )
    return await build_app_context(
        server=LoreServer(config),
        embedder=FakeEmbedder(dim=_DIM),
        manifest_path=tmp_path / "m.db",
        snapshot_root=tmp_path / "snap",
        start_tasks=start_tasks,
    )


# ===========================================================================
# PHASE 2 — cross-file edge resolution (two-phase, purge-then-RELATE, timing)
# ===========================================================================

# A cross-book pair: node ``a`` in book A carries an edge to slug ``b``, whose
# node lives in book B (a GENUINE cross-book edge — the edge's own source_book
# (A) differs from its ``out`` node's book (B), F1). All-intra-book fixtures are
# the small-N blindness CLAUDE.md warns of.
_BOOK_A_XREF = "book A\nnode monster a Aye\nedge a b\n"
_BOOK_B = "book B\nnode monster b Bee\n"


def _write_fake(bench: _EntityBench, rel_path: str, content: str) -> None:
    """Materialise a ``.fake`` file under the bench live root (for full-sweep walks)."""
    target = bench.live_root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _links_from(links: list[tuple[list[Any], list[Any], str]], in_id: list[Any]) -> list[list[Any]]:
    """The ``out`` ids of every edge whose ``in`` is ``in_id`` (order-independent)."""
    return sorted((out for got_in, out, _book in links if got_in == in_id), key=repr)


class TestTwoPhaseNodesOnly:
    """P16 (§Q3.0) — phase 1 writes NODES only; NO cross-file edge lands in phase 1."""

    async def test_single_file_index_lands_nodes_but_no_edges(
        self, entity_bench: _EntityBench
    ) -> None:
        """P16: index (phase-1 only) two files with a cross-file edge intent.

        ``index_file`` runs phase-1 (no sweep completion ⇒ no phase-2), so the
        nodes must land while the ``ENFORCED`` cross-file edge must NOT (its
        endpoint may not exist yet — the two-phase forcing function, §Q3.0). RED
        until phase-1 composes nodes (today: 0 nodes).
        """
        await entity_bench.indexer.index_file(_TIER, "books/a.fake", _BOOK_A_XREF)
        await entity_bench.indexer.index_file(_TIER, "books/b.fake", _BOOK_B)
        nodes = {row["slug"] for row in await _fetch_nodes(entity_bench.env)}
        links = await _fetch_links(entity_bench.env)
        assert nodes == {"a", "b"}, f"phase-1 must land both nodes, got {nodes}"
        assert links == [], f"a cross-file edge leaked into phase 1: {links}"


class TestPhaseTwoTrigger:
    """P17/P18 (§Q3.1/§Q3.2) — a full sweep resolves edges via resolve_edges(None)."""

    async def test_full_sweep_resolves_the_cross_file_edge(
        self, entity_bench: _EntityBench
    ) -> None:
        """P17: at ``_sweep_two_pass`` completion the indexer applies resolve_edges' fragments.

        RED until the phase-2 trigger exists (today no edge is ever resolved and
        ``resolve_edges`` is never called).
        """
        _write_fake(entity_bench, "books/a.fake", _BOOK_A_XREF)
        _write_fake(entity_bench, "books/b.fake", _BOOK_B)
        await entity_bench.indexer.index_all()
        links = await _fetch_links(entity_bench.env)
        assert _links_from(links, ["A", "a"]) == [["B", "b"]], (
            f"the full sweep did not resolve the cross-file edge a→b; links={links}"
        )
        assert entity_bench.ext.resolve_calls, "resolve_edges was never called at sweep completion"

    async def test_only_call_site_passes_changed_scopes_none(
        self, entity_bench: _EntityBench
    ) -> None:
        """P18 (§Q3.2): the indexer's ONLY resolve_edges call passes ``None`` — never a set.

        The ``set`` form is the pinned non-feature; the framework never passes it.
        RED until the (None-only) trigger exists.
        """
        _write_fake(entity_bench, "books/a.fake", _BOOK_A_XREF)
        _write_fake(entity_bench, "books/b.fake", _BOOK_B)
        await entity_bench.indexer.index_all()
        assert entity_bench.ext.resolve_calls, "resolve_edges was never called (trigger missing)"
        assert all(call is None for call in entity_bench.ext.resolve_calls), (
            f"the set form was passed — only None is legal today: {entity_bench.ext.resolve_calls}"
        )


class TestPhaseTwoOrchestratorUnion:
    """CF5 (DG3) — phase-2 fires from ALL 3 orchestrator entries via ONE shared resolver."""

    _FP = "f" * 64  # a rebuild fingerprint (64 hex, matching the existing idiom)

    async def test_rebuild_all_resolves_the_cross_file_edge(
        self, entity_bench: _EntityBench
    ) -> None:
        """CF5a: a schema rebuild (``rebuild_all``) ALSO resolves cross-file edges.

        `_sweep_two_pass` is the BATCH-only completion point; the correct union is
        index_all + rebuild_all + reconcile. RED until rebuild_all hooks the
        resolver — else a build hooking only index_all+reconcile passes while a
        schema rebuild resolves nothing.
        """
        _write_fake(entity_bench, "books/a.fake", _BOOK_A_XREF)
        _write_fake(entity_bench, "books/b.fake", _BOOK_B)
        await entity_bench.indexer.rebuild_all(self._FP)
        assert _links_from(await _fetch_links(entity_bench.env), ["A", "a"]) == [["B", "b"]], (
            "rebuild_all did not resolve the cross-file edge (phase-2 not hooked here)"
        )

    async def test_all_three_entries_share_one_resolver(
        self, entity_bench: _EntityBench, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CF5b (ONE IMPLEMENTATION, prove-by-mutation): index_all/rebuild_all/reconcile
        all route through ONE ``Indexer._resolve_all_extension_edges``.

        Wrap the shared method with a spy; each entry point must increment it. A
        build that hand-rolls resolution in ONE entry (a private clone) fails to
        increment for that entry (routing≠sharing). RED until the shared method
        exists (getattr is None today).
        """
        shared = getattr(Indexer, "_resolve_all_extension_edges", None)
        assert shared is not None, (
            "no shared Indexer._resolve_all_extension_edges — the 3 orchestrator "
            "entries must route through ONE extracted resolver (CF5/ONE IMPLEMENTATION)"
        )
        calls: list[str] = []

        async def _spy(self: Indexer, *args: Any, **kwargs: Any) -> Any:
            calls.append("call")
            return await shared(self, *args, **kwargs)

        monkeypatch.setattr(Indexer, "_resolve_all_extension_edges", _spy)
        _write_fake(entity_bench, "books/a.fake", _BOOK_A_XREF)
        _write_fake(entity_bench, "books/b.fake", _BOOK_B)

        before = len(calls)
        await entity_bench.indexer.index_all()
        assert len(calls) > before, "index_all must route through the shared resolver"
        before = len(calls)
        await entity_bench.indexer.rebuild_all(self._FP)
        assert len(calls) > before, "rebuild_all must route through the shared resolver"
        before = len(calls)
        await entity_bench.engine.reconcile()
        assert len(calls) > before, "reconcile must route through the shared resolver"

    async def test_noop_reconcile_tick_does_not_reresolve(
        self, entity_bench: _EntityBench
    ) -> None:
        """CF5c (DG3 rider, bound guard): a no-op reconcile tick with NO owned tier
        rebuilt does NOT call the resolver (cost, not correctness — avoids
        re-resolving all edges on every frequent tick).

        GREEN now AND after; a build that resolves on EVERY tick reddens it.
        """
        _write_fake(entity_bench, "books/a.fake", _BOOK_A_XREF)
        _write_fake(entity_bench, "books/b.fake", _BOOK_B)
        await entity_bench.indexer.index_all()
        calls_after_index = len(entity_bench.ext.resolve_calls)
        # A reconcile with NO file changes rebuilds no owned tier ⇒ no re-resolution.
        await entity_bench.engine.reconcile()
        assert len(entity_bench.ext.resolve_calls) == calls_after_index, (
            "a no-op reconcile tick re-resolved all edges — the driver must gate the "
            "resolver on an owned scope-bearing tier being rebuilt (DG3 rider)"
        )


class TestResolveOrDrop:
    """P19 (F2/§Q3.1) — one unresolvable intent is DROPPED, never a whole-scope abort."""

    async def test_unresolvable_intent_dropped_resolvable_committed(
        self, entity_bench: _EntityBench
    ) -> None:
        """P19: a scope with one resolvable + one unresolvable edge commits the resolvable.

        Store §3/§4: a single RELATE to a missing endpoint would abort the whole
        scope's purge+RELATE txn (the DD-3.c denial). resolve_edges MUST drop the
        unresolvable BEFORE the RELATE. RED until phase-2 exists (no edges today).
        """
        _write_fake(entity_bench, "books/a.fake", "book A\nnode monster a Aye\nedge a b\nedge a zzz\n")
        _write_fake(entity_bench, "books/b.fake", _BOOK_B)
        await entity_bench.indexer.index_all()
        links = await _fetch_links(entity_bench.env)
        assert _links_from(links, ["A", "a"]) == [["B", "b"]], (
            f"the resolvable edge a→b must commit and a→zzz drop (no whole-scope abort); links={links}"
        )

    async def test_positive_control_two_resolvable_intents_both_commit(
        self, entity_bench: _EntityBench
    ) -> None:
        """P19 positive control: two resolvable intents both commit (the drop is selective)."""
        _write_fake(entity_bench, "books/a.fake", "book A\nnode monster a Aye\nedge a b\nedge a c\n")
        _write_fake(entity_bench, "books/b.fake", "book B\nnode monster b Bee\nnode monster c Cee\n")
        await entity_bench.indexer.index_all()
        links = await _fetch_links(entity_bench.env)
        assert _links_from(links, ["A", "a"]) == [["B", "b"], ["B", "c"]], (
            f"both resolvable intents must commit; links={links}"
        )


class TestPhaseTwoPartialFailure:
    """P20 (F7/§Q6) — a failing scope isolates LOUDLY; siblings unaffected, never swallowed."""

    async def test_one_scope_failure_isolates_and_surfaces(
        self, entity_bench: _EntityBench, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """P20 (per Probe-5): scope B's apply fails → A committed, C attempted, B in scopes_failed.

        DG2 makes this satisfiable: ``resolve_edges`` returns scope-LABELLED
        ``ResolvedScope``s, so the indexer names WHICH scope failed. RED until the
        per-scope isolation loop populates ``IndexSummary.scopes_failed``.
        """

        class _FailScopeB(FakeIngestExtension):
            async def resolve_edges(self, ctx: ExtensionContext, changed_scopes: set[str] | None) -> list[ResolvedScope]:  # noqa: E501
                resolved = await super().resolve_edges(ctx, changed_scopes)
                out: list[ResolvedScope] = []
                for item in resolved:
                    if item.scope == "B":
                        poisoned = TxnFragment(
                            statements=[*item.fragment.statements, "THROW 'scope B forced failure';"],
                            params=dict(item.fragment.params),
                        )
                        out.append(ResolvedScope(scope=item.scope, fragment=poisoned))
                    else:
                        out.append(item)
                return out

        entity_bench.indexer._extensions = (  # noqa: SLF001 - swap in the failing-scope reference build
            _FailScopeB(domain_store=entity_bench.domain, book_ranks=dict(entity_bench.ext._book_ranks)),
        )
        for book in ("A", "B", "C"):
            lower = book.lower()
            _write_fake(
                entity_bench, f"books/{lower}.fake",
                f"book {book}\nnode monster {lower}1 {book}1\nnode monster {lower}2 {book}2\n"
                f"edge {lower}1 {lower}2\n",
            )
        summary = await entity_bench.indexer.index_all()
        links = await _fetch_links(entity_bench.env)
        assert _links_from(links, ["A", "a1"]) == [["A", "a2"]], "scope A must stay committed"
        assert _links_from(links, ["C", "c1"]) == [["C", "c2"]], "scope C must still be attempted (isolation)"
        assert _links_from(links, ["B", "b1"]) == [], "scope B failed — its edge must be absent"
        assert "B" in set(summary.scopes_failed), (
            f"the scope-B failure was SWALLOWED — not surfaced in IndexSummary: {summary.scopes_failed}"
        )


class TestCorruptionDirection:
    """P21 (§Q3.3) — purge-then-RELATE: a changed edge target converges, no stale/lost."""

    async def test_reingest_changed_edge_leaves_only_the_new_target(
        self, entity_bench: _EntityBench
    ) -> None:
        """P21: ingest a→b, re-ingest a→c ⇒ ONLY a→c (catches UPDATE-keeps-stale AND DELETE-loses).

        RED until phase-2 purge-by-scope exists (no edges today).
        """
        _write_fake(entity_bench, "books/a.fake", "book A\nnode monster a Aye\nedge a b\n")
        _write_fake(entity_bench, "books/b.fake", "book A\nnode monster b Bee\n")
        _write_fake(entity_bench, "books/c.fake", "book A\nnode monster c Cee\n")
        await entity_bench.indexer.index_all()
        assert _links_from(await _fetch_links(entity_bench.env), ["A", "a"]) == [["A", "b"]]

        _write_fake(entity_bench, "books/a.fake", "book A\nnode monster a Aye\nedge a c\n")
        await entity_bench.indexer.index_all()
        after = _links_from(await _fetch_links(entity_bench.env), ["A", "a"])
        assert after == [["A", "c"]], f"expected ONLY a→c after re-ingest, got {after}"


class TestCrossBookNewerWins:
    """P22 (F1/§Q6) — full-sweep re-resolution re-points a cross-book edge at the newer node."""

    async def test_full_sweep_repoints_cross_book_edge_to_newer_book(
        self, entity_bench: _EntityBench
    ) -> None:
        """P22: a genuine cross-book edge re-points to a NEWER book's node on a re-crawl.

        Edge a(A)→b: first resolves to node[B,b]; after adding newer book Bp
        (higher rank) carrying slug b, a full sweep re-points it to node[Bp,b] —
        AND keeps it (never silently dropped). RED until phase-2 exists.
        """
        _write_fake(entity_bench, "books/a.fake", _BOOK_A_XREF)
        _write_fake(entity_bench, "books/b.fake", _BOOK_B)
        await entity_bench.indexer.index_all()
        assert _links_from(await _fetch_links(entity_bench.env), ["A", "a"]) == [["B", "b"]]

        _write_fake(entity_bench, "books/bp.fake", "book Bp\nnode monster b BeePrime\n")
        await entity_bench.indexer.index_all()
        after = _links_from(await _fetch_links(entity_bench.env), ["A", "a"])
        assert after == [["Bp", "b"]], (
            f"the cross-book edge must re-point to the NEWER book's node (newer wins); got {after}"
        )


class TestCrossBookNonFeature:
    """P23 (§Q3.2/§Q6) — a single-file watched change does NOT re-resolve cross-book edges."""

    async def test_single_file_change_does_not_trigger_reresolution(
        self, entity_bench: _EntityBench
    ) -> None:
        """P23 (the pinned NON-FEATURE): incremental cross-book re-resolution is NOT built.

        Only a full sweep calls resolve_edges. A single-file ``index_file`` must NOT.
        GREEN now AND after; a build that silently adds incremental cross-book
        re-resolution reddens this and must DELETE the pin, saying so (pin-the-miss).
        """
        _write_fake(entity_bench, "books/a.fake", _BOOK_A_XREF)
        _write_fake(entity_bench, "books/b.fake", _BOOK_B)
        await entity_bench.indexer.index_all()
        calls_after_sweep = len(entity_bench.ext.resolve_calls)

        # A single-file watched re-ingest of book B must not re-resolve edges.
        await entity_bench.indexer.index_file(_TIER, "books/b.fake", _BOOK_B)
        assert len(entity_bench.ext.resolve_calls) == calls_after_sweep, (
            "a single-file change triggered cross-file edge re-resolution — the pinned "
            "non-feature (§Q3.2) is now built; delete this pin and record the re-open trigger"
        )


class TestRelateFormAndDedupe:
    """P24 (§Q5/§Q6) — bound-RecordID RELATE + ENFORCED endpoints + dedupe-before-RELATE."""

    async def test_duplicate_edge_intent_is_deduped_to_one_edge(
        self, entity_bench: _EntityBench
    ) -> None:
        """P24: a fan-out repeating an endpoint DEDUPES (else UNIQUE(in,out) rejects it).

        A node whose intents repeat ``b`` must yield exactly ONE a→b edge — the
        dedupe-before-RELATE the UNIQUE(in,out) backstop relies on (§Q5). RED until
        phase-2 exists.
        """
        _write_fake(entity_bench, "books/a.fake", "book A\nnode monster a Aye\nedge a b\nedge a b\n")
        _write_fake(entity_bench, "books/b.fake", _BOOK_B)
        await entity_bench.indexer.index_all()
        edges = [link for link in await _fetch_links(entity_bench.env) if link[0] == ["A", "a"]]
        assert len(edges) == 1, f"a repeated edge intent was not deduped: {edges}"
        # The bound-RecordID form lands a real fake_node → fake_node edge (§4).
        assert edges[0][1] == ["B", "b"]


class TestDirtyStoreEnforcedMigration:
    """P25 (§Q3.4/§Q6) — the #107-invisible pin: ENFORCED lands on a DIRTY store via OVERWRITE."""

    async def test_enforced_flip_bites_new_danglers_and_spares_the_old_row(
        self, migration_db: tuple[Any, SurrealEnv]  # noqa: F811 - imported fixture
    ) -> None:
        """P25: apply OLD (un-enforced) fake_link, RELATE a dangling edge, flip to ENFORCED.

        Asserts (a) a FRESH dangling RELATE is now REJECTED (the guard took via
        OVERWRITE — ``IF NOT EXISTS`` would be a silent no-op, #107) AND (b) the
        pre-existing dangling row SURVIVES (ENFORCED is a write-path guard, not a
        retro-validation). The ONE pin no virgin-DB fixture can produce (§1.6).
        The legacy row is written UNDER the old DDL (store ref §1.4 trap).
        """
        connection, env = migration_db
        await apply_ddl(connection, FAKE_NODE_DDL, url=env.url)
        await apply_ddl(connection, FAKE_LINK_DDL_UNENFORCED, url=env.url)

        live_slug = ghost_id("live")
        live_in = RecordID(FAKE_NODE_TABLE, ["A", live_slug])
        await run(
            connection,
            "CREATE $id CONTENT { slug: $s, name: $s, kind: $k, tier: $t, "
            "file_path: $f, source_book: $b, edges: [] }",
            {"id": live_in, "s": live_slug, "k": "monster", "t": _TIER, "f": "a.fake", "b": "A"},
        )
        ghost_slug = ghost_id("ghost")
        ghost_out = RecordID(FAKE_NODE_TABLE, ["A", ghost_slug])
        ghost_rows = await run(
            connection, f"SELECT id FROM {FAKE_NODE_TABLE} WHERE slug = $s", {"s": ghost_slug}
        )
        assert not ghost_rows, "fixture: the dangling edge's OUT endpoint must genuinely NOT exist"
        # Under the OLD (un-enforced) DDL a dangling RELATE is ACCEPTED.
        await run(
            connection, f"RELATE $f->{FAKE_LINK_TABLE}->$t SET source_book = $b",
            {"f": live_in, "t": ghost_out, "b": "A"},
        )
        before = await run(connection, f"SELECT id FROM {FAKE_LINK_TABLE}")
        assert before, "fixture: the OLD un-enforced DDL must ACCEPT the dangling edge"

        # Flip to today's ENFORCED DDL via OVERWRITE on the DIRTY store.
        await apply_ddl(connection, FAKE_NODE_DDL, url=env.url)
        await apply_ddl(connection, FAKE_LINK_DDL_ENFORCED, url=env.url)

        fresh_ghost = RecordID(FAKE_NODE_TABLE, ["A", ghost_id("still_absent")])
        with pytest.raises(Exception):  # noqa: B017 - the engine's ENFORCED rejection surface
            await run(
                connection, f"RELATE $f->{FAKE_LINK_TABLE}->$t SET source_book = $b",
                {"f": live_in, "t": fresh_ghost, "b": "A"},
            )
        after = await run(
            connection, f"SELECT id, out FROM {FAKE_LINK_TABLE} WHERE out = $out", {"out": ghost_out}
        )
        assert after, "the pre-existing dangling edge must SURVIVE the ENFORCED flip (§4)"


class TestSlugLeadingIndex:
    """P26 (F6/§Q6) — the fake_node lookup index is SLUG-LEADING (store §2 leading-column)."""

    def test_emitted_node_index_ddl_is_slug_leading(self) -> None:
        """P26: the emitted ``fake_node`` UNIQUE index leads with ``slug`` (not source_book).

        Store §2: composite indexes are leading-column-only; a slug-only lookup
        (52b's book-agnostic resolution) IndexScans ONLY when slug LEADS. A
        source_book-leading index would TableScan the slug lookup (F6).
        """
        from _ingest_entity_fixtures import FAKE_NODE_DDL as ddl

        assert "FIELDS slug, source_book UNIQUE" in ddl, (
            "the fake_node lookup index is not slug-leading (F6 — store §2)"
        )
        assert "FIELDS source_book, slug" not in ddl, (
            "the fake_node index leads with source_book — a slug-only lookup TableScans (F6)"
        )


# Names imported for the Phase-2 pins; referenced above to keep the linter honest.
_PHASE2_USED = (AsyncSurreal, IngestBackend, FakeIngestConfigModel, FAKE_SUFFIX)
