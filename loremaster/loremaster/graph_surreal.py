"""Async SurrealDB code-graph — the P4 port of the KùzuDB :class:`~loremaster.
graph.CodeGraph` onto the unified SurrealDB store (S13 "Model A").

P4 ports ONLY the STORAGE + QUERY layer (the Kùzu ``CREATE``/``MATCH`` →
SurrealQL). The astroid DERIVATION (``_derive_nodes`` / ``_derive_edges`` /
``_resolve`` / the keep-drop rule / the module-qualified-name helpers) is REUSED
UNCHANGED from :class:`~loremaster.graph.CodeGraph` — those methods touch no Kùzu
connection, so :class:`_AstroidDerivation` subclasses ``CodeGraph`` and skips the
Kùzu open to borrow them VERBATIM (a true reuse, never a re-implementation). The
value objects (:class:`~loremaster.graph.GraphNode` /
:class:`~loremaster.graph.ReferenceSummary` /
:class:`~loremaster.graph.DeadCodeNode`) and the edge-kind / reason constants are
imported from :mod:`loremaster.graph` and re-exported here so the server + CLI
can import either module interchangeably; ``GraphNode.id`` is the stringified
composite record id (the SurrealDB port has no int surrogate — S13 clause 3).

The S13 "Model A" storage schema (see
:func:`~loremaster.store.surreal_schema.generate_graph_ddl`):

* ``code_node`` — DETERMINISTIC composite record id
  ``code_node:[tier, file_path, qualified_name]`` (an array-keyed ``RecordID``,
  exactly like the manifest's ``file:[tier, file_path]``), so a rebuild targets
  the SAME row (idempotent) and the same qname under two tiers stays two distinct
  rows (collision-correct). Fields: ``kind`` / ``qualified_name`` / ``bare_name``
  (the last dotted segment) / ``file_path`` / ``tier`` / ``chunk_id``
  (``option<string>`` — ``NONE`` for the synthesised module node).
* ``name`` — id ``name:<dst-string>``, UPSERTed idempotently and carrying a
  queryable ``value`` (a copy of that id-string, indexed) so a MODULE-name query
  can ``string::starts_with`` on the resolved symbol fqns defined under it — the
  Kùzu ``dst STARTS WITH "<module>."`` module-prefix reach that ``what_imports``
  / ``blast_radius`` depend on (3.1.5 cannot prefix-match a RecordID id directly).
  An edge to a not-yet-defined name simply UPSERTs the name first
  (order-independence).
* ``refers`` RELATION (``code_node`` → ``name``): ``kind`` / ``resolved`` /
  ``src_tier`` / ``src_file_path`` (the per-file purge keys). One directed
  reference per row.
* ``answers_to`` RELATION (``code_node`` → ``name``): ``tier`` / ``file_path``.
  Each node ``answers_to`` its FQN-name AND its bare-name — the FQN-collision
  fan-out that bridges a bare query to a resolved FQN dst.

Connection lifecycle + self-heal mirror
:class:`~loremaster.index.surreal_manifest.SurrealManifest` exactly: one lazily
opened, cached, signed-in connection; a transport failure drops the cached handle
so the next call transparently reconnects (LOUD, typed
:class:`~loremaster.store.surreal.SurrealConnectionError` — never a silently empty
graph). Every per-file build/purge runs through the shared
:func:`~loremaster.store._txn.execute_transaction`, and every value is bound as a
parameter (no interpolation — SurrealQL-injection defense).

Deliberate divergence from the sibling ports' ``execute_transaction`` usage:
:class:`~loremaster.store.surreal.SurrealStore` and :class:`~loremaster.index.
surreal_manifest.SurrealManifest` each have exactly ONE transaction call site
(``replace_file`` / ``replace``), so they call ``execute_transaction`` inline.
This class has TWO (:meth:`SurrealCodeGraph.build_file_graph` and
:meth:`SurrealCodeGraph.delete_file_graph`), so the call is centralised once in
the private :meth:`SurrealCodeGraph._run_transaction` rather than duplicated —
a structural difference forced by having a second real caller, not a change in
the transaction/self-heal contract itself.

Async surface (S13 clause 1 — the ``surrealdb`` SDK is async-only, so the whole
query/mutation surface becomes ``async def``; P5 adds ``await`` at the indexer /
reconcile / server call sites). :meth:`reset_resolution_cache` stays SYNC — it
only touches astroid's process-global cache, never the DB.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, NoReturn

from lorescribe.models import Chunk
from surrealdb import AsyncSurreal, RecordID

from loremaster.graph import (
    _QUALIFIER_SEPARATOR,
    _REFERENCE_KINDS,
    _TEST_NAME_PREFIX,
    DEFAULT_DEAD_CODE_MAX_RESULTS,
    EDGE_CALLS,
    EDGE_DEFINES,
    EDGE_IMPORTS,
    EDGE_INHERITS,
    KIND_CLASS,
    KIND_FUNCTION,
    KIND_METHOD,
    KIND_MODULE,
    MAX_DEAD_CODE_MAX_RESULTS,
    REASON_NO_REFERENCES,
    REASON_ONLY_REFERENCED_BY_TESTS,
    CodeGraph,
    DeadCodeNode,
    GraphNode,
    ReferenceSummary,
    _EdgeSpec,
    _NodeSpec,
)
from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    SurrealConnectionError,
    SurrealStoreError,
    TxnFragment,
    _SurrealConnection,
    compose,
    execute_transaction,
    is_connection_error,
)
from loremaster.store.surreal import _SIGNIN_PASS_KEY, _SIGNIN_USER_KEY
from loremaster.store.surreal_schema import (
    ANSWERS_TO_RELATION,
    CODE_NODE_TABLE,
    NAME_TABLE,
    REFERS_RELATION,
    generate_graph_ddl,
)

# The edge-kind / node-kind / reason / bound constants and value objects are
# re-exported so callers can import the graph vocabulary from either module. Under
# mypy-strict ``no_implicit_reexport`` an explicit ``__all__`` marks the re-export.
__all__ = [
    "DEFAULT_DEAD_CODE_MAX_RESULTS",
    "EDGE_CALLS",
    "EDGE_DEFINES",
    "EDGE_IMPORTS",
    "EDGE_INHERITS",
    "KIND_CLASS",
    "KIND_FUNCTION",
    "KIND_METHOD",
    "KIND_MODULE",
    "MAX_DEAD_CODE_MAX_RESULTS",
    "REASON_NO_REFERENCES",
    "REASON_ONLY_REFERENCED_BY_TESTS",
    "DeadCodeNode",
    "GraphNode",
    "ReferenceSummary",
    "SurrealCodeGraph",
]

logger = logging.getLogger(__name__)

# Row-column / edge-endpoint names — the SINGLE source of truth reused by BOTH
# the SurrealQL text and the row-dict decode, so a rename can never silently
# desynchronise the query from the reader (the store's discipline).
_COL_ID = "id"
_COL_KIND = "kind"
_COL_QUALIFIED_NAME = "qualified_name"
_COL_BARE_NAME = "bare_name"
_COL_FILE_PATH = "file_path"
_COL_TIER = "tier"
_COL_CHUNK_ID = "chunk_id"
_COL_RESOLVED = "resolved"
_COL_SRC_TIER = "src_tier"
_COL_SRC_FILE_PATH = "src_file_path"
# The ``name`` table's queryable string column — a copy of the record-id string
# component that the module-prefix reach ``string::starts_with``es on (3.1.5
# cannot prefix-match a RecordID's id directly).
_COL_VALUE = "value"
# A native relation edge's auto-defined endpoint columns.
_EDGE_IN = "in"
_EDGE_OUT = "out"

# The composite ``code_node`` record-id key layout is ``[tier, file_path, qname]``;
# only the qname slot is ever decoded back out (tier/file_path already arrive as
# their own SELECTed columns on every row), so only that index is named.
_ID_QNAME_INDEX = 2

# The producer-namespacing prefix every bound param of the code-graph's per-file
# build/purge fragment carries, so its params never clobber a sibling producer's
# (chunk / file_text / manifest) params in a composed per-file transaction (see
# :func:`~loremaster.store._txn.compose`). ``gr_`` = the code GRaph.
GRAPH_FRAGMENT_PARAM_PREFIX = "gr_"

# Fixed bound-parameter names shared across QUERY statements (independent reads,
# never composed with another producer, so they need no namespacing prefix).
_P_NAMES = "names"
_P_IDS = "ids"
_P_KIND = "kind"
_P_KINDS = "kinds"
_P_MODULE_KIND = "module_kind"
_P_TIERS = "tiers"
_P_BARE = "bare"
_P_PAIR_TIER = "pair_tier"
_P_PAIR_FILE = "pair_file"

# The build/purge fragment's fixed tier/file params — namespaced under
# :data:`GRAPH_FRAGMENT_PARAM_PREFIX` because these DO compose into the shared
# per-file transaction alongside the other three producers' fragments.
_P_TIER = f"{GRAPH_FRAGMENT_PARAM_PREFIX}tier"
_P_FILE = f"{GRAPH_FRAGMENT_PARAM_PREFIX}file"

# Generated (per-node / per-edge / per-name) bound-parameter prefixes for the
# per-file build transaction — each anchored under
# :data:`GRAPH_FRAGMENT_PARAM_PREFIX` and kept distinct so a node/edge/name index
# can never collide on a param name (nor with a sibling producer's).
_NAME_PARAM_PREFIX = f"{GRAPH_FRAGMENT_PARAM_PREFIX}nm"
_NODE_PARAM_PREFIX = f"{GRAPH_FRAGMENT_PARAM_PREFIX}nd"
_EDGE_PARAM_PREFIX = f"{GRAPH_FRAGMENT_PARAM_PREFIX}ed"
# Generated bound-param prefix for the module-prefix ``string::starts_with`` arm
# of ``what_imports`` / ``_reverse_neighbours`` — one per frontier prefix, kept
# distinct so a prefix index can never collide with a node/edge/name param.
_PREFIX_PARAM_PREFIX = "pfx"


class _AstroidDerivation(CodeGraph):
    """Reuse :class:`~loremaster.graph.CodeGraph`'s astroid derivation WITHOUT a
    Kùzu database.

    ``CodeGraph.__init__`` opens a Kùzu file; the SurrealDB port needs only the
    PURE astroid derivation, which touches none of the Kùzu connection.
    Subclassing and setting just the three resolution attributes below
    (deliberately NOT calling ``super().__init__``, which would open the
    database) yields those methods VERBATIM — the mandated reuse, never a
    re-implementation.

    THE EXPLICIT CONTRACT (the entire surface :class:`SurrealCodeGraph` may
    touch on this delegate):

    * **Attributes this ``__init__`` MUST set** (the full state the reused
      methods read): ``_tier_roots``, ``_project_roots``, ``_resolution_enabled``.
    * **Methods :class:`SurrealCodeGraph` calls on it** (every one is PURE —
      python/astroid logic only, no I/O beyond reading the on-disk source
      ``_resolve`` needs for resolution): ``reset_resolution_cache``,
      ``_derive_nodes``, ``_derive_edges``, ``_is_excluded_candidate``,
      ``_liveness_sources``, ``_dead_code_node``.
    * **Never call a method that touches ``self._connection``/``self._database``**
      (``_execute`` and anything routed through it — every OTHER Kùzu-facing
      ``CodeGraph`` method funnels through ``_execute``, verified against
      ``graph.py``). Both attributes are deliberately never set on this
      delegate, so this is not merely a style rule: :meth:`_execute` is
      overridden below to FAIL LOUDLY with a targeted diagnostic the moment it
      is reached, rather than relying on an incidental
      ``AttributeError: no attribute '_connection'`` to catch a future
      ``CodeGraph`` change that adds a query to one of the reused methods.
    """

    def __init__(
        self,
        *,
        tier_roots: Mapping[str, str | Path] | None,
        project_roots: Sequence[str | Path] | None,
    ) -> None:
        """Set up only the resolution state the derivation reads (no Kùzu open)."""
        # These three attributes are the ENTIRE contract the reused derivation
        # methods depend on (``_resolve`` reads them; nothing else touches the
        # missing Kùzu connection) — see the class docstring's explicit list.
        self._tier_roots = (
            {tier: str(root) for tier, root in tier_roots.items()}
            if tier_roots is not None
            else {}
        )
        self._project_roots = (
            [str(root) for root in project_roots] if project_roots is not None else []
        )
        self._resolution_enabled = bool(self._project_roots)

    def _execute(
        self, cypher: str, params: dict[str, object] | None = None
    ) -> NoReturn:
        """Refuse a Kùzu query — this delegate never opens a connection.

        The guardrail for the class docstring's contract: every Kùzu-facing
        ``CodeGraph`` method funnels through ``_execute``, so overriding it here
        means a FUTURE change to one of the reused pure-derivation methods that
        accidentally starts querying Kùzu fails immediately with a clear,
        targeted diagnostic — never a silently wrong graph and never a bare,
        unexplained ``AttributeError``.

        Raises:
            RuntimeError: Always — this delegate holds no Kùzu connection.
        """
        raise RuntimeError(
            "_AstroidDerivation._execute was called, but this delegate never "
            "opens a Kùzu connection (see the class docstring's contract) — a "
            "reused derivation method must stay pure, python/astroid logic only"
        )


class SurrealCodeGraph:
    """Async code-graph over a single per-project SurrealDB database (S13 Model A).

    Owns its OWN lazily-opened, signed-in connection (mirroring
    :class:`~loremaster.index.surreal_manifest.SurrealManifest`) and reuses
    :class:`~loremaster.graph.CodeGraph`'s astroid derivation via a
    :class:`_AstroidDerivation` delegate. Every per-file build/purge is one
    transaction; every value is a bound parameter.

    Args:
        url: The SurrealDB RPC URL (e.g. ``ws://127.0.0.1:18000/rpc``).
        namespace: The namespace the database lives under.
        database: The per-project database name.
        user: The root/username to sign in with.
        password: The password to sign in with.
        tier_roots: Mapping ``tier -> on-disk root`` the tier-relative file paths
            are relative to — used to locate a file on disk for astroid
            resolution.
        project_roots: The project root directories astroid adds to its search
            path and uses to classify a reference in-project vs external.
    """

    def __init__(
        self,
        *,
        url: str,
        namespace: str,
        database: str,
        user: str,
        password: str,
        tier_roots: Mapping[str, str | Path],
        project_roots: Sequence[str | Path],
    ) -> None:
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        # Opened on first use; ``None`` means "not yet connected / closed".
        self._connection: _SurrealConnection | None = None
        # Guards the connect-time check-then-set below (mirrors
        # ``SurrealStore._connect_lock`` / ``SurrealManifest._connect_lock``):
        # without it, N concurrent first-callers on a fresh instance all pass
        # the ``self._connection is not None`` check before any of them
        # finishes connecting, each opening its OWN underlying SDK connection.
        # Safe to construct here (unbound to any running loop) on Python
        # >= 3.10.
        self._connect_lock = asyncio.Lock()
        # The reused astroid derivation (no Kùzu backend — see the delegate).
        self._derivation = _AstroidDerivation(
            tier_roots=tier_roots, project_roots=project_roots
        )

    # -- naming helpers (reused static surface the indexer still calls) -------

    @staticmethod
    def module_qualified_name(file_path: str) -> str:
        """Derive the dotted module name from a tier-relative POSIX path.

        Delegates to :meth:`CodeGraph.module_qualified_name` (moves UNCHANGED with
        the derivation).
        """
        return CodeGraph.module_qualified_name(file_path)

    @staticmethod
    def importable_module_name(base: Path, file_path: str) -> str:
        """Derive the TRUE importable dotted module name from an on-disk layout.

        Delegates to :meth:`CodeGraph.importable_module_name` (moves UNCHANGED
        with the derivation) — the pure static helper the indexer calls
        (``indexer._importable_module_name``) with the doubled-member-dir fix.
        """
        return CodeGraph.importable_module_name(base, file_path)

    def reset_resolution_cache(self) -> None:
        """Drop astroid's process-global resolution cache at a SWEEP boundary.

        SYNCHRONOUS + side-effect-only (no DB round-trip): the indexer calls it at
        a full-sweep boundary WITHOUT ``await`` — a coroutine here would be a
        contract break. Delegates to the reused astroid derivation.
        """
        self._derivation.reset_resolution_cache()

    # -- connection lifecycle (mirrors SurrealManifest exactly) --------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking (mirrors
        :meth:`~loremaster.store.surreal.SurrealStore._ensure_connection`):
        the fast path (already connected) never touches the lock; a first
        caller acquires :attr:`_connect_lock` and re-checks — a concurrent
        racer that lost the race to acquire the lock finds the connection
        already assigned by the winner and returns it without opening a
        second one. A down server or bad password is a LOUD, typed failure,
        never a hang or a silently empty graph.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        if self._connection is not None:
            return self._connection
        async with self._connect_lock:
            # Re-check: another caller may have already connected while this
            # one was waiting for the lock. mypy narrows ``self._connection``
            # to ``None`` from the outer guard and can't model the
            # cross-coroutine mutation across the ``await`` inside
            # ``__aenter__`` above, hence the unreachable ignore (mirrors
            # ``watcher.py``'s identical double-checked-lock pattern).
            if self._connection is not None:
                return self._connection  # type: ignore[unreachable]
            connection = AsyncSurreal(self._url)
            credentials: dict[str, Any] = {
                _SIGNIN_USER_KEY: self._user,
                _SIGNIN_PASS_KEY: self._password,
            }
            try:
                await connection.signin(credentials)
                await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {self._namespace}")
                await connection.use(self._namespace, self._database)
                await connection.query(f"DEFINE DATABASE IF NOT EXISTS {self._database}")
            except _CONNECTION_ERRORS as error:
                # Close the half-open socket (if any) so a failed connect never
                # leaks a dangling connection, then surface a typed connection
                # error.
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): {error}"
                ) from error
            self._connection = connection
            logger.debug(
                "graph.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect and apply the code-graph schema slice — idempotent.

        Applies :func:`~loremaster.store.surreal_schema.generate_graph_ddl` (the
        Model-A tables/indexes). The graph owns no embedder ``dim``/analyzer, so
        it never needs the full store DDL. Idempotent: a second call is a safe
        no-op. Applied inside ONE ``BEGIN … COMMIT`` transaction via
        :func:`~loremaster.store._txn.execute_transaction`, which inspects EVERY
        statement's status — the SDK's plain ``query()`` inspects only the
        FIRST statement, so a LATER statement's rejection would otherwise roll
        the whole schema back server-side while ``query()`` raised nothing at
        all (verified live).

        Raises:
            SurrealConnectionError: The server is unreachable, rejected auth, or
                the socket died mid-apply.
            SurrealStoreError: Any DDL statement was rejected by the engine (a
                real schema bug); the connection stays healthy.
        """
        await self._ensure_connection()
        ddl = generate_graph_ddl()
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("graph.schema.ready", extra={"database": self._database})

    async def close(self) -> None:
        """Close the live connection (if any); safe to call more than once."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal).

        A COMPARE-AND-SWAP, not an unconditional null: ``self._connection`` is
        cleared only when ``connection`` IS STILL the currently cached handle.
        A late caller can be holding a STALE connection reference captured
        BEFORE an earlier self-heal already replaced ``self._connection`` with
        a fresh one; nulling unconditionally would let that late caller wipe
        out a perfectly healthy, freshly-reconnected handle out from under
        every other in-flight caller. The connection HANDED to this call is
        always closed regardless, since it is the dead/stale one either way.
        """
        if self._connection is connection:
            self._connection = None
        await self._safe_close(connection)

    @staticmethod
    async def _safe_close(connection: _SurrealConnection) -> None:
        """Close ``connection``, swallowing an already-dead-socket failure."""
        try:
            await connection.close()
        except _CONNECTION_ERRORS:
            logger.debug("graph.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single read/statement on the (lazily opened) connection.

        Classifies a failure (see
        :func:`~loremaster.store._txn.is_connection_error`): a transport/auth
        fault drops the cached handle so the next call reconnects, surfaced as a
        typed, LOUD :class:`SurrealConnectionError`; a domain/schema rejection
        keeps the healthy connection and surfaces as :class:`SurrealStoreError`.

        The ``except`` also catches a raw ``KeyError``: probe-verified live (a
        socket drop with a query in flight), the installed SDK's OWN response
        routing raises ``builtins.KeyError(<request-uuid>)`` straight out of
        ``connection.query(...)`` — never a domain rejection — so it is ALWAYS
        classified as a connection fault. The ``except`` wraps ONLY the bare
        SDK call above — never our own dict-indexing code — so this can never
        misclassify a ``KeyError`` raised by application logic.
        """
        connection = await self._ensure_connection()
        try:
            return await connection.query(statement, params or {})
        except (*_CONNECTION_ERRORS, KeyError) as error:
            if isinstance(error, KeyError) or is_connection_error(error):
                await self._drop_connection(connection)
                raise SurrealConnectionError(
                    f"SurrealDB query failed against {self._url!r}: {error}"
                ) from error
            raise SurrealStoreError(
                f"SurrealDB query rejected against {self._url!r}: {error}"
            ) from error

    async def _run_transaction(self, statement: str, params: dict[str, Any]) -> None:
        """Run a multi-statement ``BEGIN … COMMIT`` and verify EVERY statement.

        Routes through the shared
        :func:`~loremaster.store._txn.execute_transaction`, which — unlike a bare
        ``query()`` — surfaces a rolled-back transaction as a raised error and
        self-heals a transport failure via :meth:`_drop_connection`.
        """
        await execute_transaction(
            statement,
            params,
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )

    # -- row / id helpers ----------------------------------------------------

    @staticmethod
    def _rows(result: Any) -> list[dict[str, Any]]:
        """Narrow a ``SELECT``-shaped result to its list of dict rows."""
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]

    @staticmethod
    def _values(result: Any) -> list[Any]:
        """Narrow a ``SELECT VALUE``-shaped result to its flat list of values."""
        return list(result) if isinstance(result, list) else []

    @staticmethod
    def _code_node_id(tier: str, file_path: str, qualified_name: str) -> RecordID:
        """The deterministic ``code_node`` record id ``[tier, file_path, qname]``."""
        return RecordID(CODE_NODE_TABLE, [tier, file_path, qualified_name])

    @staticmethod
    def _name_id(name: str) -> RecordID:
        """The ``name`` record id (``name:<name>``) every reference lands on."""
        return RecordID(NAME_TABLE, name)

    @staticmethod
    def _composite_qname(record_id: RecordID) -> str:
        """The ``qualified_name`` segment of a composite ``code_node`` record id.

        A ``code_node`` id is the array ``[tier, file_path, qualified_name]``; the
        SDK types ``RecordID.id`` as the broad ``Value`` union, so the array shape
        is narrowed here before the segment is read.
        """
        key = record_id.id
        if isinstance(key, (list, tuple)):
            return str(key[_ID_QNAME_INDEX])
        return str(key)

    @staticmethod
    def _row_to_node(row: dict[str, Any]) -> GraphNode:
        """Decode a raw ``code_node`` row into a :class:`GraphNode`.

        ``id`` is the stringified composite record id (S13 clause 3); the module
        node's ``NONE`` ``chunk_id`` decodes back to ``None``.
        """
        chunk_id = row.get(_COL_CHUNK_ID)
        return GraphNode(
            id=str(row[_COL_ID]),
            kind=str(row[_COL_KIND]),
            qualified_name=str(row[_COL_QUALIFIED_NAME]),
            file_path=str(row[_COL_FILE_PATH]),
            chunk_id=None if chunk_id is None else str(chunk_id),
            tier=str(row[_COL_TIER]),
        )

    def _decode_nodes(self, result: Any) -> list[GraphNode]:
        """Decode every dict row of a ``SELECT * FROM code_node`` into GraphNodes."""
        return [self._row_to_node(row) for row in self._rows(result)]

    @staticmethod
    def _dedupe_by_id(nodes: Sequence[GraphNode]) -> list[GraphNode]:
        """Keep one node per stringified record id (dedup preserving first-seen)."""
        seen: dict[str, GraphNode] = {}
        for node in nodes:
            seen.setdefault(node.id, node)
        return list(seen.values())

    @staticmethod
    def _bare(name: str) -> str:
        """The last dotted segment of ``name`` (reuses the derivation helper)."""
        return CodeGraph._bare_name(name)

    @staticmethod
    def _is_test_path(file_path: str) -> bool:
        """Whether ``file_path`` is a test file (reuses the derivation helper)."""
        return CodeGraph._is_test_path(file_path)

    async def _nodes_by_ids(self, ids: Sequence[RecordID]) -> list[GraphNode]:
        """Fetch and decode the ``code_node`` rows for ``ids`` (empty ⇒ no query)."""
        if not ids:
            return []
        result = await self._query(
            f"SELECT * FROM {CODE_NODE_TABLE} WHERE {_COL_ID} IN ${_P_IDS}",
            {_P_IDS: list(ids)},
        )
        return self._decode_nodes(result)

    async def _names_with_value_prefix(self, prefixes: Sequence[str]) -> list[RecordID]:
        """The ``name`` record ids whose ``value`` starts with ANY of ``prefixes``.

        Backs the module-target reach ported from Kùzu (``r.dst STARTS WITH
        "<module>."``): a trailing-dot-anchored ``<module>.`` prefix matches every
        ``name`` for a SYMBOL resolved UNDER that module (``demo.reflib.`` →
        ``demo.reflib.widget``) while the anchor keeps a sibling module out
        (``pkg.a.`` never matches ``pkg.ab.ab_symbol``). Each prefix is a BOUND
        parameter fed to ``string::starts_with`` (no interpolation); an empty
        ``prefixes`` short-circuits to no query.
        """
        if not prefixes:
            return []
        conditions: list[str] = []
        params: dict[str, Any] = {}
        for index, prefix in enumerate(prefixes):
            key = f"{_PREFIX_PARAM_PREFIX}{index}"
            conditions.append(f"string::starts_with({_COL_VALUE}, ${key})")
            params[key] = prefix
        clause = " OR ".join(conditions)
        result = await self._query(
            f"SELECT VALUE {_COL_ID} FROM {NAME_TABLE} WHERE {clause}", params
        )
        return [
            record_id for record_id in self._values(result) if isinstance(record_id, RecordID)
        ]

    # -- per-file build / delete ---------------------------------------------

    async def build_file_graph(
        self,
        tier: str,
        file_path: str,
        chunks: Sequence[Chunk],
        *,
        module_name: str | None = None,
    ) -> None:
        """Derive and store one file's nodes/references in a single transaction.

        A per-file rebuild: the file's prior code_node + refers + answers_to rows
        are purged and the freshly-derived set inserted, tier- and file-scoped so
        a sibling file or another tier's copy of the same path (C1) is untouched.
        The derivation is REUSED from :class:`~loremaster.graph.CodeGraph`.

        Expressed over the ONE statement-producing path: it builds its
        :meth:`build_file_graph_fragment` and composes it into a single
        transaction, so there is no second, drifting copy of the purge + upsert +
        relate statement text.

        Args:
            tier: The source tier the file belongs to.
            file_path: The tier-relative POSIX file path (the tier-scoping key).
            chunks: The file's lorescribe AST chunks.
            module_name: The importable module prefix every node/reference is
                qualified under; ``None`` ⇒ the pure path-join
                :meth:`module_qualified_name`.
        """
        fragment = self.build_file_graph_fragment(
            tier, file_path, chunks, module_name=module_name
        )
        statement, params = compose(fragment)
        await self._run_transaction(statement, params)

    async def delete_file_graph(self, tier: str, file_path: str) -> None:
        """Remove every code_node + refers + answers_to row owned by the file.

        Tier-scoped: the same path's rows under other tiers survive (C1). Orphan
        ``name`` rows a purge may strand are harmless — they carry no fields and
        every query walks the edge tables, not the name rows. Expressed over the
        ONE statement-producing path: it composes its :meth:`purge_file_fragment`.

        Args:
            tier: The source tier the file belongs to.
            file_path: The tier-relative POSIX file path to purge.
        """
        statement, params = compose(self.purge_file_fragment(tier, file_path))
        await self._run_transaction(statement, params)

    def build_file_graph_fragment(
        self,
        tier: str,
        file_path: str,
        chunks: Sequence[Chunk],
        *,
        module_name: str | None = None,
    ) -> TxnFragment:
        """Build the per-file code-graph fragment (purge + upsert + relate).

        A PURE builder: the astroid derivation (``_derive_nodes`` /
        ``_derive_edges``, REUSED from :class:`~loremaster.graph.CodeGraph`) runs
        here at BUILD time — it is sync CPU + on-disk source reads, never a socket
        touch. Every value — record ids, kinds, names — is a BOUND parameter (no
        interpolation), each namespaced under :data:`GRAPH_FRAGMENT_PARAM_PREFIX`
        so it never collides with a sibling producer's params in the merged
        transaction. The file's prior graph rows are purged first; the name records
        are UPSERTed next (each carrying its own string as ``value`` so the
        module-prefix reach can prefix-match it), so an edge to a not-yet-defined
        name never dangles (order-independence); each node then ``answers_to`` its
        FQN-name AND bare-name (the collision fan-out) and each reference ``refers``
        to its dst-name.

        Args:
            tier: The source tier the file belongs to.
            file_path: The tier-relative POSIX file path (the tier-scoping key).
            chunks: The file's lorescribe AST chunks.
            module_name: The importable module prefix every node/reference is
                qualified under; ``None`` ⇒ the pure path-join
                :meth:`module_qualified_name`.

        Returns:
            The code-graph :class:`TxnFragment`, carrying no ``BEGIN``/``COMMIT``.
        """
        module = (
            module_name if module_name is not None else CodeGraph.module_qualified_name(file_path)
        )
        nodes = self._derivation._derive_nodes(module, chunks)
        edges = self._derivation._derive_edges(module, chunks, tier=tier, file_path=file_path)

        params: dict[str, Any] = {_P_TIER: tier, _P_FILE: file_path}
        statements: list[str] = [*self._purge_statements()]

        # Every distinct name touched by this file (node FQNs/bares + edge dsts),
        # UPSERTed once so the relate targets always exist.
        names: set[str] = set()
        for node in nodes:
            names.add(node.qualified_name)
            names.add(self._bare(node.qualified_name))
        for edge in edges:
            names.add(edge.dst)
        for index, name in enumerate(sorted(names)):
            id_key = f"{_NAME_PARAM_PREFIX}{index}"
            value_key = f"{id_key}_value"
            params[id_key] = self._name_id(name)
            # ``value`` mirrors the record-id string so the module-prefix reach
            # can ``string::starts_with`` on an indexed column (a RecordID id is
            # not itself prefix-matchable on 3.1.5).
            params[value_key] = name
            statements.append(f"UPSERT ${id_key} SET {_COL_VALUE} = ${value_key};")

        for index, node in enumerate(nodes):
            statements.extend(self._node_statements(index, tier, file_path, node, params))
        for index, edge in enumerate(edges):
            statements.append(self._edge_statement(index, tier, file_path, edge, params))

        return TxnFragment(statements=statements, params=params)

    def purge_file_fragment(self, tier: str, file_path: str) -> TxnFragment:
        """Build the fragment that purges one file's whole code-graph slice.

        The composable counterpart to :meth:`delete_file_graph` — the three
        tier+file-scoped DELETEs a full-file purge composes alongside the chunk /
        file_text / manifest deletes. Params are namespaced under
        :data:`GRAPH_FRAGMENT_PARAM_PREFIX`.
        """
        return TxnFragment(
            statements=list(self._purge_statements()),
            params={_P_TIER: tier, _P_FILE: file_path},
        )

    @staticmethod
    def _purge_statements() -> tuple[str, ...]:
        """The three tier+file-scoped DELETEs that purge one file's graph slice."""
        return (
            f"DELETE {CODE_NODE_TABLE} "
            f"WHERE {_COL_TIER} = ${_P_TIER} AND {_COL_FILE_PATH} = ${_P_FILE};",
            f"DELETE {REFERS_RELATION} "
            f"WHERE {_COL_SRC_TIER} = ${_P_TIER} AND {_COL_SRC_FILE_PATH} = ${_P_FILE};",
            f"DELETE {ANSWERS_TO_RELATION} "
            f"WHERE {_COL_TIER} = ${_P_TIER} AND {_COL_FILE_PATH} = ${_P_FILE};",
        )

    def _node_statements(
        self,
        index: int,
        tier: str,
        file_path: str,
        node: _NodeSpec,
        params: dict[str, Any],
    ) -> list[str]:
        """The CREATE + two ``answers_to`` RELATEs for one derived node.

        Mutates ``params`` with this node's bound values and returns the
        statements. The node ``answers_to`` its FQN-name AND its bare-name — the
        mechanism that lets a bare query bridge to a resolved FQN dst.
        """
        bare = self._bare(node.qualified_name)
        prefix = f"{_NODE_PARAM_PREFIX}{index}"
        id_key, kind_key = f"{prefix}_id", f"{prefix}_kind"
        qname_key, bare_key, chunk_key = f"{prefix}_qname", f"{prefix}_bare", f"{prefix}_chunk"
        fqn_name_key, bare_name_key = f"{prefix}_fqn_name", f"{prefix}_bare_name"

        params[id_key] = self._code_node_id(tier, file_path, node.qualified_name)
        params[kind_key] = node.kind
        params[qname_key] = node.qualified_name
        params[bare_key] = bare
        # ``chunk_id`` is ``option<string>``: ``None`` binds as ``NONE`` for the
        # synthesised module node and decodes back to ``None`` on read.
        params[chunk_key] = node.chunk_id
        params[fqn_name_key] = self._name_id(node.qualified_name)
        params[bare_name_key] = self._name_id(bare)

        create = (
            f"CREATE ${id_key} CONTENT {{ "
            f"{_COL_KIND}: ${kind_key}, {_COL_QUALIFIED_NAME}: ${qname_key}, "
            f"{_COL_BARE_NAME}: ${bare_key}, {_COL_FILE_PATH}: ${_P_FILE}, "
            f"{_COL_TIER}: ${_P_TIER}, {_COL_CHUNK_ID}: ${chunk_key} }};"
        )
        answers_fqn = (
            f"RELATE ${id_key}->{ANSWERS_TO_RELATION}->${fqn_name_key} "
            f"SET {_COL_TIER} = ${_P_TIER}, {_COL_FILE_PATH} = ${_P_FILE};"
        )
        answers_bare = (
            f"RELATE ${id_key}->{ANSWERS_TO_RELATION}->${bare_name_key} "
            f"SET {_COL_TIER} = ${_P_TIER}, {_COL_FILE_PATH} = ${_P_FILE};"
        )
        return [create, answers_fqn, answers_bare]

    def _edge_statement(
        self,
        index: int,
        tier: str,
        file_path: str,
        edge: _EdgeSpec,
        params: dict[str, Any],
    ) -> str:
        """The ``refers`` RELATE for one derived reference (mutates ``params``)."""
        prefix = f"{_EDGE_PARAM_PREFIX}{index}"
        src_key, dst_key = f"{prefix}_src", f"{prefix}_dst"
        kind_key, resolved_key = f"{prefix}_kind", f"{prefix}_resolved"
        params[src_key] = self._code_node_id(tier, file_path, edge.src)
        params[dst_key] = self._name_id(edge.dst)
        params[kind_key] = edge.kind
        params[resolved_key] = edge.resolved
        return (
            f"RELATE ${src_key}->{REFERS_RELATION}->${dst_key} SET "
            f"{_COL_KIND} = ${kind_key}, {_COL_RESOLVED} = ${resolved_key}, "
            f"{_COL_SRC_TIER} = ${_P_TIER}, {_COL_SRC_FILE_PATH} = ${_P_FILE};"
        )

    # -- reconcile surface ---------------------------------------------------

    async def indexed_file_count(self) -> int:
        """Return the number of distinct ``(tier, file_path)`` files with nodes.

        3.1.5 has no ``SELECT DISTINCT <field>``, so the ``(tier, file_path)``
        pairs are deduped CLIENT-side. A wiped graph yields ``0`` (the reconcile's
        FP-04 trigger).

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        rows = self._rows(
            await self._query(
                f"SELECT {_COL_TIER}, {_COL_FILE_PATH} FROM {CODE_NODE_TABLE}"
            )
        )
        pairs = {(str(row[_COL_TIER]), str(row[_COL_FILE_PATH])) for row in rows}
        return len(pairs)

    # -- queries -------------------------------------------------------------

    async def what_imports(self, target: str) -> list[GraphNode]:
        """Return the module nodes that import ``target`` (by FQN or bare name).

        The reverse of the ``imports`` reference, read off the name node's
        INCOMING ``refers`` — file-independent, so it holds whether or not the
        target's defining file is graphed. A bare query bridges to a resolved FQN
        dst through the TARGET node's ``answers_to`` fan-out (which needs the
        target's file graphed — production always indexes the whole project).

        A MODULE-NAME target ALSO reaches every ``from <module> import <symbol>``
        importer (Kùzu parity): such an import records its dst as the resolved
        SYMBOL fqn (``demo.reflib.widget``), not the bare module, so the
        trailing-dot-anchored ``<module>.`` value-prefix arm pulls those names in.
        It is strictly ADDITIVE and harmless for a symbol target (nothing is
        resolved under ``demo.reflib.widget.``), and IMPORTS-only (the ``refers``
        query below already filters ``kind = imports``).

        Args:
            target: The imported module / dotted name to find importers of.

        Returns:
            The importing module nodes (empty if nobody imports the target).
        """
        bare = self._bare(target)
        name_keys: set[str] = {target, bare}
        # Bridge: any node ANSWERING TO the query name(s) contributes its FQN, so
        # a bare "LoadError" reaches the resolved import dst "pkg.errors.LoadError".
        bridge_names = [self._name_id(target), self._name_id(bare)]
        answerers = self._values(
            await self._query(
                f"SELECT VALUE {_EDGE_IN} FROM {ANSWERS_TO_RELATION} "
                f"WHERE {_EDGE_OUT} IN ${_P_NAMES}",
                {_P_NAMES: bridge_names},
            )
        )
        for record_id in answerers:
            if isinstance(record_id, RecordID):
                name_keys.add(self._composite_qname(record_id))

        # Module-prefix arm (Kùzu parity): the ``name`` ids for every SYMBOL
        # resolved UNDER a ``<target>.`` module prefix (trailing-dot-anchored so
        # ``pkg.a`` never matches a sibling ``pkg.ab.X``). Unioned into the same
        # ``imports``-only ``refers`` query below, so the arm stays imports-only.
        prefix_name_ids = await self._names_with_value_prefix(
            [f"{target}{_QUALIFIER_SEPARATOR}"]
        )
        import_names_by_key: dict[str, RecordID] = {
            str(name_id): name_id
            for name_id in [self._name_id(name) for name in name_keys] + prefix_name_ids
        }
        import_names = list(import_names_by_key.values())
        src_ids = [
            record_id
            for record_id in self._values(
                await self._query(
                    f"SELECT VALUE {_EDGE_IN} FROM {REFERS_RELATION} "
                    f"WHERE {_COL_KIND} = ${_P_KIND} AND {_EDGE_OUT} IN ${_P_NAMES}",
                    {_P_KIND: EDGE_IMPORTS, _P_NAMES: import_names},
                )
            )
            if isinstance(record_id, RecordID)
        ]
        if not src_ids:
            return []
        # Importers of an ``imports`` edge are always module nodes; filter to be
        # exact (matching the Kùzu ``n.kind = module`` semantics).
        result = await self._query(
            f"SELECT * FROM {CODE_NODE_TABLE} "
            f"WHERE {_COL_ID} IN ${_P_IDS} AND {_COL_KIND} = ${_P_MODULE_KIND}",
            {_P_IDS: src_ids, _P_MODULE_KIND: KIND_MODULE},
        )
        return self._dedupe_by_id(self._decode_nodes(result))

    async def blast_radius(self, target: str, depth: int, max_results: int) -> list[GraphNode]:
        """Return the BOUNDED reverse-reference transitive closure from ``target``.

        Everything that (transitively) depends on ``target``: walk references
        backwards (a node's dependents are the sources of references whose dst is
        that node's name, across ALL reference kinds) breadth-first, bounded by
        ``depth`` reverse hops and a hard ``max_results`` ceiling.

        Args:
            target: The qualified name to compute the blast radius of.
            depth: The maximum number of reverse hops (>= 0).
            max_results: The maximum number of nodes to return (the hard cap).

        Returns:
            Up to ``max_results`` dependent nodes, never the target itself.
        """
        if depth < 0 or max_results <= 0:
            return []

        frontier: set[str] = {target}
        found: dict[str, GraphNode] = {}
        visited_frontier: set[str] = {target}

        for _hop in range(depth):
            if not frontier or len(found) >= max_results:
                break
            next_frontier: set[str] = set()
            for node in await self._reverse_neighbours(frontier):
                if node.qualified_name == target or node.qualified_name in found:
                    continue
                found[node.qualified_name] = node
                if node.qualified_name not in visited_frontier:
                    visited_frontier.add(node.qualified_name)
                    next_frontier.add(node.qualified_name)
                if len(found) >= max_results:
                    break
            frontier = next_frontier

        return list(found.values())[:max_results]

    async def _reverse_neighbours(self, frontier: set[str]) -> list[GraphNode]:
        """The dependent NODES one reverse hop back from any name in ``frontier``.

        A frontier name is matched against a ``refers`` edge's dst by its full
        value AND its bare last segment (the resolution seam), across ALL
        reference kinds; the edge's source ``code_node`` is the dependent.

        A DOTTED frontier name ALSO reaches importers of a SYMBOL resolved UNDER
        it — ``from <module> import <sym>`` records the import dst as the resolved
        ``<module>.<sym>`` fqn, so once a bare MODULE qualified_name enters the
        BFS frontier mid-walk its importers are reachable only via the
        trailing-dot-anchored ``<module>.`` value-prefix arm (Kùzu parity). That
        arm is IMPORTS-only: ``defines`` already links a module to ALL its
        symbols, so a wider prefix would re-pull the whole symbol set in one hop
        and overshoot the depth bound. A bare (separator-less) frontier name is
        excluded from the prefix arm so a single segment can never swallow
        unrelated symbols.
        """
        unique: dict[str, RecordID] = {}
        # Base arm: any reference kind whose dst is a frontier name (full or bare).
        name_ids: list[RecordID] = []
        for name in frontier:
            name_ids.append(self._name_id(name))
            name_ids.append(self._name_id(self._bare(name)))
        base_src_ids = self._values(
            await self._query(
                f"SELECT VALUE {_EDGE_IN} FROM {REFERS_RELATION} WHERE {_EDGE_OUT} IN ${_P_NAMES}",
                {_P_NAMES: name_ids},
            )
        )
        for record_id in base_src_ids:
            if isinstance(record_id, RecordID):
                unique[str(record_id)] = record_id
        # Module-prefix arm (imports-only): importers of a symbol resolved under a
        # dotted frontier module name (``pkg.a`` never pulls a sibling ``pkg.ab.X``).
        prefixes = [
            f"{name}{_QUALIFIER_SEPARATOR}"
            for name in frontier
            if _QUALIFIER_SEPARATOR in name
        ]
        prefix_name_ids = await self._names_with_value_prefix(prefixes)
        if prefix_name_ids:
            prefixed_src_ids = self._values(
                await self._query(
                    f"SELECT VALUE {_EDGE_IN} FROM {REFERS_RELATION} "
                    f"WHERE {_COL_KIND} = ${_P_KIND} AND {_EDGE_OUT} IN ${_P_NAMES}",
                    {_P_KIND: EDGE_IMPORTS, _P_NAMES: prefix_name_ids},
                )
            )
            for record_id in prefixed_src_ids:
                if isinstance(record_id, RecordID):
                    unique[str(record_id)] = record_id
        return await self._nodes_by_ids(list(unique.values()))

    async def tests_for(self, symbol_or_file: str) -> list[GraphNode]:
        """Return the test nodes related to ``symbol_or_file``.

        A node is a TEST node when its ``file_path`` is a test path. It relates to
        the target when EITHER a test file carries a reference (any kind) to the
        target (by FQN or bare name), OR the ``test_x`` ↔ ``x`` name heuristic
        links it (a ``test_boot`` node tests any symbol whose bare name is
        ``boot``).

        Args:
            symbol_or_file: A qualified symbol name or a module name.

        Returns:
            The related test nodes (de-duplicated by record id).
        """
        target_bare = self._bare(symbol_or_file)
        related: dict[str, GraphNode] = {}

        # 1) Test files carrying a reference (any kind) to the target.
        name_ids = [self._name_id(symbol_or_file), self._name_id(target_bare)]
        ref_rows = self._rows(
            await self._query(
                f"SELECT {_COL_SRC_TIER}, {_COL_SRC_FILE_PATH} FROM {REFERS_RELATION} "
                f"WHERE {_EDGE_OUT} IN ${_P_NAMES}",
                {_P_NAMES: name_ids},
            )
        )
        test_pairs = {
            (str(row[_COL_SRC_TIER]), str(row[_COL_SRC_FILE_PATH]))
            for row in ref_rows
            if self._is_test_path(str(row[_COL_SRC_FILE_PATH]))
        }
        for pair_tier, pair_file in test_pairs:
            nodes = self._decode_nodes(
                await self._query(
                    f"SELECT * FROM {CODE_NODE_TABLE} "
                    f"WHERE {_COL_TIER} = ${_P_PAIR_TIER} AND {_COL_FILE_PATH} = ${_P_PAIR_FILE}",
                    {_P_PAIR_TIER: pair_tier, _P_PAIR_FILE: pair_file},
                )
            )
            for node in nodes:
                related[node.id] = node

        # 2) The ``test_x`` ↔ ``x`` name heuristic.
        heuristic_bare = f"{_TEST_NAME_PREFIX}{target_bare}"
        heuristic_nodes = self._decode_nodes(
            await self._query(
                f"SELECT * FROM {CODE_NODE_TABLE} WHERE {_COL_BARE_NAME} = ${_P_BARE}",
                {_P_BARE: heuristic_bare},
            )
        )
        for node in heuristic_nodes:
            if self._is_test_path(node.file_path):
                related[node.id] = node

        return list(related.values())

    async def references(self, name: str) -> ReferenceSummary:
        """Return the reference profile of the symbol ``name``, split by origin.

        A reference TO ``name`` is a ``refers`` edge of a TRUE reference kind
        (``imports`` / ``calls`` / ``inherits`` — NOT the structural ``defines``
        parent edge) whose dst matches ``name`` by exact qualified name OR bare
        last segment, and whose source is not ``name`` itself (self-reference —
        e.g. recursion — is not external use). Distinct sources are split into
        production vs test by the referencing file's path.

        Args:
            name: The qualified name of the symbol to profile.

        Returns:
            The :class:`ReferenceSummary` for ``name``.
        """
        rows = self._rows(
            await self._query(
                f"SELECT {_EDGE_IN}, {_COL_SRC_FILE_PATH} FROM {REFERS_RELATION} "
                f"WHERE {_COL_KIND} IN ${_P_KINDS} AND {_EDGE_OUT} IN ${_P_NAMES}",
                {
                    _P_KINDS: list(_REFERENCE_KINDS),
                    _P_NAMES: [self._name_id(name), self._name_id(self._bare(name))],
                },
            )
        )
        production: set[str] = set()
        test: set[str] = set()
        referencing_ids: dict[str, RecordID] = {}
        for row in rows:
            source_id = row[_EDGE_IN]
            if not isinstance(source_id, RecordID):
                continue
            source_qname = self._composite_qname(source_id)
            if source_qname == name:
                continue  # self-reference excluded
            if self._is_test_path(str(row[_COL_SRC_FILE_PATH])):
                test.add(source_qname)
            else:
                production.add(source_qname)
            referencing_ids[str(source_id)] = source_id

        referencing = self._dedupe_by_id(await self._nodes_by_ids(list(referencing_ids.values())))
        return ReferenceSummary(
            qualified_name=name,
            production_references=len(production),
            test_references=len(test),
            referencing=referencing,
        )

    async def dead_code(
        self,
        tiers: Sequence[str],
        *,
        include_tests: bool = False,
        include_dunders: bool = False,
        include_entrypoints: bool = False,
        max_results: int = DEFAULT_DEAD_CODE_MAX_RESULTS,
    ) -> list[DeadCodeNode]:
        """Return the dead/orphaned nodes in ``tiers`` — zero PRODUCTION references.

        A SYMBOL node is dead ⇔ it has zero production references (a symbol whose
        only consumers are its tests is dead); a MODULE node is dead ⇔ neither it
        NOR any symbol it defines has a production reference (the roll-up, since
        references are symbol-level). The liveness/exclusion/reason logic is
        REUSED from :class:`~loremaster.graph.CodeGraph` (via the derivation
        delegate) — this method only sources the reference index + candidate nodes
        from the Model-A tables. Test nodes, dunder methods and package/entry
        modules are excluded by default, each re-includable via its flag.

        Args:
            tiers: The tiers whose nodes are swept (empty ⇒ empty result).
            include_tests: Keep test-path nodes when ``True``.
            include_dunders: Keep dunder methods when ``True``.
            include_entrypoints: Keep package / entry modules when ``True``.
            max_results: The hard cap on dead nodes returned (clamped to
                :data:`MAX_DEAD_CODE_MAX_RESULTS`).

        Returns:
            Up to ``max_results`` :class:`DeadCodeNode` entries.
        """
        if not tiers or max_results <= 0:
            return []
        cap = min(max_results, MAX_DEAD_CODE_MAX_RESULTS)

        reference_index = await self._reference_source_index()
        candidates = self._decode_nodes(
            await self._query(
                f"SELECT * FROM {CODE_NODE_TABLE} WHERE {_COL_TIER} IN ${_P_TIERS}",
                {_P_TIERS: list(tiers)},
            )
        )
        symbol_qualified_names = [node.qualified_name for node in candidates]

        dead: list[DeadCodeNode] = []
        for node in candidates:
            # REUSED pure logic: exclusion rules, module liveness roll-up, and the
            # DeadCodeNode construction all come from the Kùzu CodeGraph unchanged.
            if self._derivation._is_excluded_candidate(
                node,
                include_tests=include_tests,
                include_dunders=include_dunders,
                include_entrypoints=include_entrypoints,
            ):
                continue
            production_sources, test_sources = self._derivation._liveness_sources(
                node, reference_index, symbol_qualified_names
            )
            if production_sources:
                continue  # has a production reference → alive
            reason = (
                REASON_ONLY_REFERENCED_BY_TESTS if test_sources else REASON_NO_REFERENCES
            )
            dead.append(self._derivation._dead_code_node(node, len(test_sources), reason))
            if len(dead) >= cap:
                break
        return dead

    async def _reference_source_index(self) -> dict[str, tuple[set[str], set[str]]]:
        """Index every true-reference dst → its (production, test) source sets.

        One pass over the ``refers`` rows of the true reference kinds, keyed by the
        dst NAME (the resolved FQN or bare fallback the edge points at) — the exact
        shape the reused :meth:`CodeGraph._sources_for` / ``_liveness_sources``
        consume, so the dead-code decision logic is served unchanged from Model A.
        """
        rows = self._rows(
            await self._query(
                f"SELECT {_EDGE_OUT}, {_EDGE_IN}, {_COL_SRC_FILE_PATH} FROM {REFERS_RELATION} "
                f"WHERE {_COL_KIND} IN ${_P_KINDS}",
                {_P_KINDS: list(_REFERENCE_KINDS)},
            )
        )
        index: dict[str, tuple[set[str], set[str]]] = {}
        for row in rows:
            dst_id, src_id = row[_EDGE_OUT], row[_EDGE_IN]
            if not isinstance(dst_id, RecordID) or not isinstance(src_id, RecordID):
                continue
            dst_name = str(dst_id.id)
            source_qname = self._composite_qname(src_id)
            production_sources, test_sources = index.setdefault(dst_name, (set(), set()))
            target = (
                test_sources
                if self._is_test_path(str(row[_COL_SRC_FILE_PATH]))
                else production_sources
            )
            target.add(source_qname)
        return index
