"""Fake-domain ingest fixtures for the packet-47a twelfth-seam contract.

These are the reference EXTENSION + its domain store that prove the generic
ingest seam (packet 47 ruled design, ``docs/design/2026-08-14-packet47-ingest-
entity-seam-design.md`` §Q6) — the analog of packet 46's fake registry, injected
via ``register_in_discovery(monkeypatch, {"fake": FakeIngestExtension})``. The
seam under test is FRAMEWORK code (indexer / server / store); everything in this
module is a faithful STAND-IN for a real domain extension (the dnd extension is
packet 51+). It carries NO edition logic — 52b owns the real cross-edition
resolver; :class:`FakeIngestExtension` resolves an edge intent by EXACT SLUG,
newest book wins, where "newest" is a fixture-supplied ``book_ranks`` total order
(the stand-in for the lore-side ``book_precedence`` map the edition-precedence
mechanism rules, ``docs/design/2026-08-14-edition-precedence-mechanism.md`` §5).

Store law (``docs/reference/surrealdb-31-capabilities.md``, CITED never
re-transcribed): the DDL uses LEADING clauses (§1.1/§4 — a trailing clause is a
parse error, F8); ``fake_node`` is a plain table (``IF NOT EXISTS``, §1.1), its
lookup index is SLUG-LEADING (``FIELDS slug, source_book`` — §2 leading-column
rule, F6); ``fake_link`` is a RELATION table defined with ``OVERWRITE`` (the ONLY
clause that lands ``ENFORCED`` on a live store — §1.1/§4/#107); every value is a
bound param namespaced under ``xt_<name>_``; DDL and per-file writes ride
``execute_transaction`` (§3 — checks EVERY statement, never the SDK's
statement[0]-only ``query()``). All four DDL/CREATE/RELATE/ENFORCED shapes were
probed live on spike-surreal 3.2.x before this module was authored.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from loremaster.extension import Extension, ExtensionContext, IngestBackend, ResolvedScope
from loremaster.store._txn import (
    TxnFragment,
    bootstrap_session,
    execute_transaction,
    signin_credentials,
)
from pydantic import BaseModel, ConfigDict, SecretStr
from surrealdb import AsyncSurreal, RecordID

# --- table + param-prefix identity ------------------------------------------
FAKE_NODE_TABLE = "fake_node"
FAKE_LINK_TABLE = "fake_link"

#: The suffix :meth:`FakeIngestExtension.claims` owns. A claimed file skips
#: chunking/embedding and is ingested via ``entity_fragment`` instead.
FAKE_SUFFIX = ".fake"


def entity_param_prefix(name: str) -> str:
    """The ``xt_<name>_`` param namespace an extension's ingest fragments bind under.

    ``ext.name`` is the extension's stable key, so two DIFFERENT extensions can
    never collide and ``xt_`` is distinct from the five producer prefixes
    (``st_``/``ft_``/``mf_``/``gr_``/``sn_``). Derived from the NAME, never a
    literal, so a name-monoculture build (namespaces only when ``name=="fake"``)
    is caught by a two-name fixture (§Q1.3 / CLAUDE.md parameter-monoculture).
    """
    return f"xt_{name}_"


# --- the fake-domain DDL (store law §1.1/§2/§4, probed live) ----------------
# Plain node table: IF NOT EXISTS (§1.1). Fields: OVERWRITE (§1.1 — a CHANGED
# definition must land, #107). Lookup index: SLUG-LEADING (§2, F6) so a slug-only
# predicate IndexScans and 52b's book-agnostic slug resolution is servable.
FAKE_NODE_DDL = (
    f"DEFINE TABLE IF NOT EXISTS {FAKE_NODE_TABLE} TYPE NORMAL SCHEMAFULL;\n"
    f"DEFINE FIELD OVERWRITE slug ON {FAKE_NODE_TABLE} TYPE string;\n"
    f"DEFINE FIELD OVERWRITE name ON {FAKE_NODE_TABLE} TYPE string;\n"
    f"DEFINE FIELD OVERWRITE kind ON {FAKE_NODE_TABLE} TYPE string;\n"
    f"DEFINE FIELD OVERWRITE tier ON {FAKE_NODE_TABLE} TYPE string;\n"
    f"DEFINE FIELD OVERWRITE file_path ON {FAKE_NODE_TABLE} TYPE string;\n"
    f"DEFINE FIELD OVERWRITE source_book ON {FAKE_NODE_TABLE} TYPE string;\n"
    # Outgoing edge intents carried ON the node (phase 1 is NODES-ONLY; phase 2
    # READS these to resolve endpoints — §Q3.1 "a LOOKUP, not a parse").
    f"DEFINE FIELD OVERWRITE edges ON {FAKE_NODE_TABLE} TYPE array<string>;\n"
    f"DEFINE INDEX IF NOT EXISTS fake_node_slug ON {FAKE_NODE_TABLE} "
    f"FIELDS slug, source_book UNIQUE;\n"
)

# The relation-table DDL body (fields + UNIQUE(in,out), §4), shared by the
# enforced and un-enforced variants so the ONLY difference the migration pin
# (§Q3.4) sees is the ENFORCED keyword.
_FAKE_LINK_BODY = (
    f"DEFINE FIELD OVERWRITE source_book ON {FAKE_LINK_TABLE} TYPE string;\n"
    f"DEFINE INDEX IF NOT EXISTS fake_link_uniq ON {FAKE_LINK_TABLE} "
    f"FIELDS in, out UNIQUE;\n"
)
# Relation table: OVERWRITE is the ONLY clause that lands ENFORCED on a live
# store (§1.1/§4/#107). ENFORCED guards BOTH endpoints.
FAKE_LINK_DDL_ENFORCED = (
    f"DEFINE TABLE OVERWRITE {FAKE_LINK_TABLE} TYPE RELATION "
    f"IN {FAKE_NODE_TABLE} OUT {FAKE_NODE_TABLE} ENFORCED SCHEMAFULL;\n"
    f"{_FAKE_LINK_BODY}"
)
# The #107-invisible OLD world (§Q3.4): the SAME relation table WITHOUT ENFORCED.
# The migration pin applies THIS, writes a dangling edge under it, then flips to
# the enforced DDL via OVERWRITE and proves the guard now bites.
FAKE_LINK_DDL_UNENFORCED = (
    f"DEFINE TABLE OVERWRITE {FAKE_LINK_TABLE} TYPE RELATION "
    f"IN {FAKE_NODE_TABLE} OUT {FAKE_NODE_TABLE} SCHEMAFULL;\n"
    f"{_FAKE_LINK_BODY}"
)

#: The full domain DDL an ingest backend applies at ``ensure_ready``.
FAKE_DDL = FAKE_NODE_DDL + FAKE_LINK_DDL_ENFORCED


# --- the trivial machine-tier line format -----------------------------------
@dataclass(frozen=True)
class _FakeNode:
    slug: str
    name: str
    kind: str
    edges: tuple[str, ...]  # outgoing dst-slug intents (resolved in phase 2)


@dataclass(frozen=True)
class ParsedFakeFile:
    """One ``.fake`` file parsed into its source_book + typed nodes (≥2 kinds)."""

    source_book: str
    nodes: tuple[_FakeNode, ...]


def parse_fake_source(text: str) -> ParsedFakeFile | None:
    """Parse a ``.fake`` file's trivial line format, or ``None`` if it declares nothing.

    Grammar (one file = one ``source_book``):

    * ``book <source_book>`` — the file's provenance scope (exactly one).
    * ``node <kind> <slug> <name...>`` — a typed node (multiple KINDS, §Q1.4 —
      a spell-only single-kind fixture is the small-N trap CLAUDE.md warns of).
    * ``edge <src_slug> <dst_slug>`` — an outgoing edge intent attached to
      ``src_slug``'s node (``dst_slug`` may live in ANOTHER book — a cross-book
      edge, F1). Resolved in phase 2, never phase 1.

    A PURE parser — never a socket touch (the ``build_file_graph_fragment``
    discipline).
    """
    source_book: str | None = None
    order: list[str] = []
    fields: dict[str, tuple[str, str]] = {}  # slug -> (kind, name)
    edges: dict[str, list[str]] = defaultdict(list)
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        head, _, rest = line.partition(" ")
        rest = rest.strip()
        if head == "book":
            source_book = rest
        elif head == "node":
            kind, _, tail = rest.partition(" ")
            slug, _, name = tail.strip().partition(" ")
            if slug not in fields:
                order.append(slug)
            fields[slug] = (kind, name.strip() or slug)
        elif head == "edge":
            src, _, dst = rest.partition(" ")
            edges[src.strip()].append(dst.strip())
    if source_book is None or not order:
        return None
    nodes = tuple(
        _FakeNode(slug=slug, name=fields[slug][1], kind=fields[slug][0], edges=tuple(edges[slug]))
        for slug in order
    )
    return ParsedFakeFile(source_book=source_book, nodes=nodes)


# --- the fake domain store (an IngestBackend; clones SurrealCodeGraph's shape) -
class FakeDomainStore:
    """A minimal fake-domain store — own connection, ``execute_transaction``, DDL.

    Structurally satisfies :class:`~loremaster.extension.IngestBackend`
    (``ensure_ready`` / ``close``), cloning :class:`~loremaster.graph_surreal.
    SurrealCodeGraph`'s lazily-opened, signed-in connection. It is BOTH the DDL
    collaborator (readied on ``build_app_context``'s write-stack rail, §Q4) AND
    the phase-2 READ connection ``resolve_edges`` uses to see committed nodes —
    the ingest WRITES ride the shared ``SurrealStore.apply`` (ONE
    IMPLEMENTATION), never this store's own connection.
    """

    def __init__(
        self,
        *,
        url: str,
        namespace: str,
        database: str,
        user: str,
        password: SecretStr,
    ) -> None:
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        self._connection: Any = None
        self._connect_lock = asyncio.Lock()

    async def _ensure_connection(self) -> Any:
        """Return the live connection, opening + signing in on first use (double-checked)."""
        if self._connection is not None:
            return self._connection
        async with self._connect_lock:
            # Re-check: another caller may have connected while this one waited for
            # the lock. mypy narrows _connection to None from the outer guard and
            # can't model the cross-coroutine mutation across the await in __aenter__
            # (the same unreachable-ignore SurrealCodeGraph._ensure_connection carries).
            if self._connection is not None:
                return self._connection  # type: ignore[unreachable]
            connection = AsyncSurreal(self._url)
            await connection.signin(signin_credentials(user=self._user, password=self._password))
            await bootstrap_session(connection, self._namespace, self._database, url=self._url)
            self._connection = connection
            return connection

    async def _drop_connection(self, connection: Any) -> None:
        """Compare-and-swap self-heal seam (execute_transaction's ``drop``)."""
        if self._connection is connection:
            self._connection = None

    async def ensure_ready(self) -> None:
        """Apply the fake-domain schema DDL — idempotent, ONE BEGIN…COMMIT (§3)."""
        await self._ensure_connection()
        await execute_transaction(
            f"BEGIN;\n{FAKE_DDL}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )

    async def close(self) -> None:
        """Close the live connection (if any); safe to call more than once."""
        if self._connection is not None:
            connection = self._connection
            self._connection = None
            await connection.close()

    def entity_tables(self) -> tuple[str, ...]:
        """The entity tables this backend owns (DG1 — the store's tier-purge channel).

        ``fake_node`` carries a ``tier`` field (Fable's rider), so the store's
        ``DELETE fake_node WHERE tier=$tier`` co-purge is not a silent no-op.
        """
        return (FAKE_NODE_TABLE,)

    async def fetch_nodes(self) -> list[dict[str, Any]]:
        """Every committed ``fake_node`` row (the phase-2 endpoint-resolution READ)."""
        connection = await self._ensure_connection()
        result = await connection.query(
            f"SELECT slug, source_book, edges FROM {FAKE_NODE_TABLE}"
        )
        return [row for row in result if isinstance(row, dict)] if isinstance(result, list) else []


# --- the reference ingest extension -----------------------------------------
class FakeIngestExtension(Extension):
    """The reference twelfth-seam extension: typed nodes + two-phase cross-file edges.

    Injected via ``register_in_discovery(monkeypatch, {"fake": <class>})`` OR
    constructed directly and handed to ``Indexer(extensions=[...])``. Overrides
    the five ingest seams and NOTHING else (a zero-other-seam extension). Carries
    NO edition logic: :meth:`resolve_edges` resolves an intent by exact slug,
    newest book winning per the fixture ``book_ranks`` total order (stand-in for
    the lore-side ``book_precedence`` map — 52b owns the real resolver).
    """

    def __init__(
        self,
        *,
        domain_store: FakeDomainStore,
        book_ranks: dict[str, int] | None = None,
        name: str = "fake",
    ) -> None:
        self._domain_store = domain_store
        self._book_ranks = dict(book_ranks or {})
        self._name = name
        #: Spy: every ``changed_scopes`` value the framework called this seam with,
        #: in order. The full-sweep trigger passes ``None`` and only ``None``
        #: (§Q3.2 pinned non-feature); a single-file watched change triggers NONE.
        self.resolve_calls: list[set[str] | None] = []

    @property
    def name(self) -> str:
        return self._name

    # seam 12 (phase 0) — the DDL/lifecycle collaborator.
    def ingest_backends(self, ctx: ExtensionContext) -> list[IngestBackend]:
        return [self._domain_store]

    # seam 12 (phase 1) — claims + NODE fragment.
    def claims(self, tier: str, path: str) -> bool:
        return path.endswith(FAKE_SUFFIX)

    def entity_fragment(
        self, tier: str, path: str, text: str, ctx: ExtensionContext
    ) -> TxnFragment | None:
        parsed = parse_fake_source(text)
        if parsed is None:
            return None
        prefix = entity_param_prefix(self._name)
        tier_key, path_key = f"{prefix}tier", f"{prefix}path"
        params: dict[str, Any] = {tier_key: tier, path_key: path}
        # Purge THIS file's prior nodes first (a node delete cascades its edges,
        # §2/§4 — probed live), then CREATE the current node set. NODES ONLY.
        statements = [
            f"DELETE {FAKE_NODE_TABLE} WHERE tier = ${tier_key} AND file_path = ${path_key};"
        ]
        for index, node in enumerate(parsed.nodes):
            id_key = f"{prefix}id_{index}"
            slug_key = f"{prefix}slug_{index}"
            name_key = f"{prefix}name_{index}"
            kind_key = f"{prefix}kind_{index}"
            book_key = f"{prefix}book_{index}"
            edges_key = f"{prefix}edges_{index}"
            params[id_key] = RecordID(FAKE_NODE_TABLE, [parsed.source_book, node.slug])
            params[slug_key] = node.slug
            params[name_key] = node.name
            params[kind_key] = node.kind
            params[book_key] = parsed.source_book
            params[edges_key] = list(node.edges)
            statements.append(
                f"CREATE ${id_key} CONTENT {{ "
                f"slug: ${slug_key}, name: ${name_key}, kind: ${kind_key}, "
                f"tier: ${tier_key}, file_path: ${path_key}, source_book: ${book_key}, "
                f"edges: ${edges_key} }};"
            )
        return TxnFragment(statements=statements, params=params)

    def entity_purge_fragment(self, tier: str, path: str) -> TxnFragment | None:
        prefix = entity_param_prefix(self._name)
        tier_key, path_key = f"{prefix}tier", f"{prefix}path"
        return TxnFragment(
            statements=[
                f"DELETE {FAKE_NODE_TABLE} WHERE tier = ${tier_key} AND file_path = ${path_key};"
            ],
            params={tier_key: tier, path_key: path},
        )

    # seam 12 (phase 2) — resolve cross-file edges per source_book scope.
    async def resolve_edges(
        self, ctx: ExtensionContext, changed_scopes: set[str] | None
    ) -> list[ResolvedScope]:
        self.resolve_calls.append(set(changed_scopes) if changed_scopes is not None else None)
        nodes = await self._domain_store.fetch_nodes()
        candidates_by_slug: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for node in nodes:
            candidates_by_slug[str(node["slug"])].append(node)

        def resolve(dst_slug: str) -> RecordID | None:
            """Newest book wins; an unresolvable slug is DROPPED before RELATE (F2)."""
            candidates = candidates_by_slug.get(dst_slug)
            if not candidates:
                return None
            best = max(
                candidates,
                key=lambda candidate: self._book_ranks.get(str(candidate["source_book"]), 0),
            )
            return RecordID(FAKE_NODE_TABLE, [best["source_book"], best["slug"]])

        prefix = entity_param_prefix(self._name)
        # Group the current nodes by their own source_book (the edge scope) — every
        # scope with nodes gets ONE purge-then-RELATE fragment so a re-crawl
        # re-resolves every scope against ALL current nodes (§Q3.2 full-sweep).
        scopes: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for node in nodes:
            scopes[str(node["source_book"])].append(node)

        resolved: list[ResolvedScope] = []
        for scope in sorted(scopes):
            scope_key = f"{prefix}scope"
            params: dict[str, Any] = {scope_key: scope}
            statements = [f"DELETE {FAKE_LINK_TABLE} WHERE source_book = ${scope_key};"]
            edge_index = 0
            seen: set[tuple[str, str]] = set()  # DEDUPE before RELATE (§Q5, UNIQUE(in,out))
            for node in scopes[scope]:
                src_id = RecordID(FAKE_NODE_TABLE, [node["source_book"], node["slug"]])
                for dst_slug in node.get("edges") or []:
                    dst_id = resolve(str(dst_slug))
                    if dst_id is None:
                        continue  # resolve-or-drop: never a RELATE to a missing endpoint
                    dedupe_key = (str(src_id), str(dst_id))
                    if dedupe_key in seen:
                        continue
                    seen.add(dedupe_key)
                    from_key = f"{prefix}from_{edge_index}"
                    to_key = f"{prefix}to_{edge_index}"
                    params[from_key] = src_id
                    params[to_key] = dst_id
                    statements.append(
                        f"RELATE ${from_key}->{FAKE_LINK_TABLE}->${to_key} "
                        f"SET source_book = ${scope_key};"
                    )
                    edge_index += 1
            # DG2: LABEL each fragment with its scope id so the indexer can name a
            # failed scope in IndexSummary.scopes_failed (a bare fragment carries
            # only position, never the source_book scope).
            resolved.append(
                ResolvedScope(scope=scope, fragment=TxnFragment(statements=statements, params=params))
            )
        return resolved


# --- the config slice the fake extension validates (seam 7, for discovery) ---
class FakeIngestConfigModel(BaseModel):
    """The pydantic model seam 7 validates the ``extensions.fake`` slice with."""

    model_config = ConfigDict(extra="forbid")

    flavour: str = "vanilla"


# --- lightweight lifecycle backends/extensions (build_app_context pins) ------
@dataclass
class RecordingBackend:
    """A lightweight :class:`IngestBackend` that RECORDS its lifecycle, no socket.

    For the ordering-rail + unwind pins (§Q4): they assert ``ensure_ready`` /
    ``close`` are CALLED (and in the right order, and on the failure paths), not
    that any DDL lands — so a real connection is unneeded and undesirable
    (fault-injection stays deterministic).
    """

    label: str
    events: list[str]
    fail_ready: bool = False
    ready_count: int = 0
    close_count: int = 0

    async def ensure_ready(self) -> None:
        self.ready_count += 1
        self.events.append(f"ready:{self.label}")
        if self.fail_ready:
            raise RuntimeError(f"ingest backend {self.label} refused to ready")

    async def close(self) -> None:
        self.close_count += 1
        self.events.append(f"close:{self.label}")

    def entity_tables(self) -> tuple[str, ...]:
        """No real tables — the lifecycle probe only records ready/close (DG1)."""
        return ()


class LifecycleProbeExtension(Extension):
    """A no-arg-constructible extension whose ingest backend records its lifecycle.

    Discoverable via ``EXTENSION_REGISTRY`` (``build_app_context`` instantiates it
    with no args), so the ordering-rail / unwind pins can inject an ingest backend
    through the REAL discovery + wiring path. Lifecycle events land in the SHARED
    CLASS-LEVEL :data:`LIFECYCLE_LOG` (the instance is created inside
    ``build_app_context`` where a test cannot reach it, so the log must be class
    scope); a test :meth:`reset` s it, flips the fault-injection class flags, then
    reads the log + the backend counts back. The backend is also reachable off the
    constructed instance (``server.extensions[i].backend``).
    """

    #: Shared across the (discovery-constructed) instance, its backend, and the
    #: test — reset per test via :meth:`reset`. Records ``ready:``/``close:`` from
    #: the backend and (via a test monkeypatch) ``indexer_built`` from the Indexer.
    LIFECYCLE_LOG: list[str] = []
    #: Flip to make the contributed backend's ``ensure_ready`` raise (block-1 unwind).
    fail_ready: bool = False
    #: Flip to make ``resolve_edges`` raise during the initial sweep (block-2 unwind).
    fail_resolve: bool = False

    @classmethod
    def reset(cls) -> None:
        """Clear the shared log and fault flags — call at the START of each test."""
        cls.LIFECYCLE_LOG = []
        cls.fail_ready = False
        cls.fail_resolve = False

    def __init__(self) -> None:
        self.events = type(self).LIFECYCLE_LOG
        self.backend = RecordingBackend(
            label="lifecycle_probe", events=self.events, fail_ready=type(self).fail_ready
        )

    @property
    def name(self) -> str:
        return "lifecycle_probe"

    def config_model(self) -> type[BaseModel]:
        return FakeIngestConfigModel

    def claims(self, tier: str, path: str) -> bool:
        return path.endswith(FAKE_SUFFIX)

    def ingest_backends(self, ctx: ExtensionContext) -> list[IngestBackend]:
        return [self.backend]

    async def resolve_edges(
        self, ctx: ExtensionContext, changed_scopes: set[str] | None
    ) -> list[ResolvedScope]:
        self.events.append("resolve")
        if type(self).fail_resolve:
            raise RuntimeError("phase-2 resolve refused during the initial sweep")
        return []
