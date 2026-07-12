"""Project configuration model for ``lore.yaml`` (amended tiered contract).

``LoreConfig`` is the typed parse of a project's ``lore.yaml``. The known
sections are strict (``extra="forbid"``): a typo'd or stale key fails loudly at
load time rather than being silently dropped — a dropped ``dim``, for instance,
would let a wrong-dimension index slip past the startup coherence gate and
silently corrupt retrieval.

Two amendment additions break the "everything forbids extras" rule in a
controlled way:

* **``roots:``** (D5) — a list of source roots/tiers, each with a per-tier
  freshness policy. ``watch: live`` roots are watched (inotify) and declare a
  ``path``; ``watch: static`` roots are batch-indexed, frozen, version-stamped,
  and declare a ``source`` + ``version`` + ``provider``. Each root is itself a
  strict section (a typo'd root key still fails).
* **``extensions:``** (seam 7 / §A1.3.7) — an OPAQUE pass-through mapping the
  base does *not* interpret or reject. A registered :class:`Extension` validates
  its own slice with its own pydantic model. This is the *only* sanctioned extra
  top-level key; a raw, unrecognised top-level field is still rejected.

An optional **``auth``** block (D9) models a rotatable set of named API keys,
each referenced by an environment-variable *name* (``*_env``) — never inlined.
Absent ⇒ no-auth localhost single-user mode. ``tls_terminated_upstream`` (D11)
records that loremaster serves plain HTTP behind a TLS-terminating ingress.

Secrets are *never* inlined. The config carries only the *name* of an
environment variable; :func:`resolve_secret` reads ``os.environ`` and raises a
clear, remediable error when the variable is unset, so a missing credential
fails at startup rather than as an opaque 401 later.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from loresigil.voyage_batch import DEFAULT_POLL_INTERVAL_S
from pydantic import (
    BaseModel,
    ConfigDict,
    PositiveFloat,
    PositiveInt,
    StringConstraints,
    model_validator,
)

# Sweep-level batch-embedding dispatch modes (ledger #14 Part 2). "realtime"
# forces the per-file embed path; "batch" forces the two-pass bulk-sweep path
# (falling back to realtime with a WARNING when the embedder lacks
# ``supports_batch``); "auto" picks batch only when a sweep's pending chunk
# count exceeds the threshold AND the embedder supports it.
BatchMode = Literal["realtime", "batch", "auto"]
DEFAULT_BATCH_MODE: BatchMode = "auto"

# The default pending-chunk count above which an "auto" sweep dispatches a batch
# job: small enough that a real multi-hundred-file project sweep trips it, large
# enough that a single-file watcher reconcile (which stays realtime regardless
# of mode) never accidentally qualifies.
DEFAULT_BATCH_CHUNK_COUNT_THRESHOLD: int = 1000

# Freshness policies a root may declare (D5). Typed as the exact string literals
# so they satisfy ``RootConfig.watch: Literal["live", "static"]`` when used to
# construct a root (e.g. the synthesised single-tree default root).
WATCH_LIVE: Literal["live"] = "live"
WATCH_STATIC: Literal["static"] = "static"

# The tier name given to the single LIVE root synthesised for a single-tree
# config (top-level ``include`` globs and NO explicit ``roots:``). Records,
# the manifest, the store, and the code-graph all partition by tier, so the
# synthesised root must carry a concrete, non-empty tier.
TIER_DEFAULT = "default"

# The safe charset a project ``slug`` must match: lowercase alphanumerics plus
# ``_``, starting with an alphanumeric, non-empty. The slug is f-string'd
# straight into the on-disk state-DB paths (``<slug>.memory.db``), the SurrealDB
# database name (``effective_surreal_database``), AND the ``lore_<slug>``
# container/naming convention, so a traversal (``../etc``),
# a separator (``a/b``), whitespace, an uppercase, or a leading separator is a
# path/database hazard, and a HYPHEN is rejected outright (operator directive
# 2026-07-03, task #32): an unescaped hyphenated identifier fails SurrealQL
# parsing (``REMOVE DATABASE my-proj`` → parse error), so it is blocked at
# config load rather than escaped at every interpolation site. Constraining it
# makes an operator typo or a malicious value FAIL FAST at load.
SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_]*$"

# An annotated ``str`` carrying the safe-charset constraint — mirrors the
# ``PositiveInt`` annotated-type idiom already used for ``dim`` etc., so an
# invalid slug raises a pydantic ``ValidationError`` at parse time exactly like
# every other strict field on the model (both on direct ``ProjectConfig(...)``
# construction and via ``LoreConfig.model_validate(...)``).
SlugStr = Annotated[str, StringConstraints(pattern=SLUG_PATTERN)]


class _StrictModel(BaseModel):
    """Base for every *known* config section: forbid unknown keys so typos fail."""

    model_config = ConfigDict(extra="forbid")


class ProjectConfig(_StrictModel):
    """Project identity.

    Attributes:
        slug: The project identifier; drives the SurrealDB database name
            AND the on-disk state-DB paths (``<slug>.db`` / ``<slug>.memory.db``).
            Constrained to the safe :data:`SLUG_PATTERN` charset because it is
            interpolated straight into filesystem paths and
            the SurrealDB database name: a traversal, separator, whitespace,
            uppercase, or leading-separator slug is a path/database hazard and
            must be rejected at load, not silently written to the wrong place.
        root: The project root the include/exclude globs are resolved against.
    """

    slug: SlugStr
    root: str


class BatchConfig(_StrictModel):
    """Sweep-level batch-embedding configuration (ledger #14 Part 2).

    OPTIONAL on :class:`EmbeddingConfig` with a default instance (mirroring
    :class:`LoggingConfig` / :class:`SurrealConfig` on :class:`LoreConfig`), so
    every existing ``lore.yaml`` (which carries no ``embedding.batch:`` block)
    keeps validating and transparently gets these defaults.

    Attributes:
        mode: The sweep dispatch mode. ``"auto"`` (the default) picks the
            two-pass batch flow only when a sweep's pending chunk count exceeds
            :attr:`chunk_count_threshold` AND the embedder advertises
            ``supports_batch``; ``"batch"`` forces it (falling back to realtime
            with a WARNING when unsupported); ``"realtime"`` forces the
            pre-existing per-file embed path.
        chunk_count_threshold: The pending-chunk count above which an ``"auto"``
            sweep dispatches a batch job. Positive.
        poll_interval_s: The delay between batch-job status polls. Defaults to
            loresigil's own
            :data:`~loresigil.voyage_batch.DEFAULT_POLL_INTERVAL_S` (the SAME
            source of truth the Voyage batch client uses), never a hand-copied
            literal.
    """

    mode: BatchMode = DEFAULT_BATCH_MODE
    chunk_count_threshold: PositiveInt = DEFAULT_BATCH_CHUNK_COUNT_THRESHOLD
    poll_interval_s: PositiveFloat = DEFAULT_POLL_INTERVAL_S


class EmbeddingConfig(_StrictModel):
    """Embedding-backend configuration.

    Attributes:
        backend: Which embedder implementation to construct.
        base_url: The embedding service base URL.
        endpoint: The embedding endpoint path (e.g. ``/embed``).
        model: The model identifier the backend serves.
        dim: The embedding dimensionality; must match the live probe and the
            existing collection's vector size or startup refuses. Positive.
        max_input_tokens: The hard per-input token cap; over-length inputs are
            rejected (HTTP 422), never truncated.
        max_batch_texts: The maximum number of texts per embedding request.
        concurrency: The number of in-flight embedding requests.
        connect_timeout_s: Connect timeout, in seconds, for the startup probe.
        api_key_env: The *name* of the environment variable holding the API key.
        tokenizer: The local tokenizer identifier used for exact token counts.
        truncate: Whether the backend truncates over-length inputs. With the
            self-hosted TEI backend this is ``False`` (over-limit → hard 422).
        query_prompt_name: Optional TEI prompt name sent as ``"prompt_name"`` in
            the POST body for ``embed_query`` calls. ``None`` (default) means no
            ``"prompt_name"`` key is sent — backward-compatible opt-in.
        document_prompt_name: Optional TEI prompt name sent as ``"prompt_name"``
            in the POST body for ``embed_documents`` calls. ``None`` (default)
            means no ``"prompt_name"`` key is sent — backward-compatible opt-in.
        batch: Sweep-level batch-embedding configuration (see
            :class:`BatchConfig`). OPTIONAL with a default instance, so an
            existing lore.yaml with no ``embedding.batch:`` block still parses.
    """

    backend: Literal["tei", "voyage-cloud", "voyage-context"]
    base_url: str
    endpoint: str
    model: str
    dim: PositiveInt
    max_input_tokens: PositiveInt
    max_batch_texts: PositiveInt
    concurrency: PositiveInt
    connect_timeout_s: float
    api_key_env: str
    tokenizer: str
    truncate: bool

    # Asymmetric prompt-name fields (TEI only). Both default to None so existing
    # lore.yaml files without these keys continue to parse without error (the
    # extra="forbid" guard on _StrictModel still rejects any unrecognised key
    # not listed here — this is an explicit addition, not a relaxation).
    query_prompt_name: str | None = None
    document_prompt_name: str | None = None

    # OPTIONAL with a default instance (like ``logging`` on ``LoreConfig``), so
    # an existing lore.yaml with no ``embedding.batch:`` block still validates
    # and transparently gets the documented sweep-batch defaults.
    batch: BatchConfig = BatchConfig()


# The production SurrealDB RPC default — the standard WebSocket ``/rpc`` port.
# The test harness retargets it via a per-test ``surreal:`` block (the dev
# server on :18000 with a unique per-test database).
SURREAL_DEFAULT_URL = "ws://127.0.0.1:8000/rpc"

# The shared namespace every project's database lives under. Follows the
# ``lore_<slug>`` naming convention: one namespace, one database per project
# slug, so the two-container topology maps cleanly onto Surreal.
SURREAL_DEFAULT_NAMESPACE = "lore"

# The env-var *names* the root credentials are referenced by — never the secret
# itself (mirrors :attr:`AuthKey.key_env`'s env-var-name discipline).
SURREAL_DEFAULT_USER_ENV = "SURREAL_USER"
SURREAL_DEFAULT_PASSWORD_ENV = "SURREAL_PASS"


class SurrealConfig(_StrictModel):
    """SurrealDB connection configuration (P5 store unification).

    Locates the project's SurrealDB namespace + database and references the root
    credentials by environment-variable *name* — never inlined (:func:`resolve_secret`
    reads them at startup and fails loudly if unset), the same env-var-name
    discipline :attr:`AuthKey.key_env` uses.

    OPTIONAL on :class:`LoreConfig` with a default instance, so every existing
    ``lore.yaml`` (which carries no ``surreal:`` section) keeps validating and
    transparently gets the localhost production defaults.

    Attributes:
        url: The SurrealDB RPC URL (a WebSocket ``/rpc`` endpoint). Defaults to
            the standard localhost port.
        namespace: The namespace the project's database lives under. Defaults to
            the shared ``lore`` namespace.
        database: The database name. ``None`` (default) derives it from the
            project slug — the same identity the on-disk state-DB paths and the
            ``lore_<slug>`` naming convention use — via
            :attr:`LoreConfig.effective_surreal_database`.
        user_env: The *name* of the environment variable holding the root
            username.
        password_env: The *name* of the environment variable holding the root
            password.
    """

    url: str = SURREAL_DEFAULT_URL
    namespace: SlugStr = SURREAL_DEFAULT_NAMESPACE
    database: SlugStr | None = None
    user_env: str = SURREAL_DEFAULT_USER_ENV
    password_env: str = SURREAL_DEFAULT_PASSWORD_ENV


class RootConfig(_StrictModel):
    """A single source root/tier with a per-tier freshness policy (D5).

    A ``live`` root (e.g. a host checkout) is watched via inotify and indexed
    incrementally — it declares a ``path``. A ``static`` root (vendored
    community/enterprise/pip trees) is batch-indexed, frozen and version-stamped
    — it declares a ``source`` (where the provider materialises the snapshot
    from), a ``version`` (the rebuild trigger), and a ``provider`` (which
    :class:`SourceProvider` acquires it). Per-root ``include``/``exclude`` globs
    scope what the walk picks up within the root.

    Attributes:
        tier: The tier name — a first-class key dimension downstream (records /
            manifest / store partition by it, so two tiers' copies of one path
            coexist).
        watch: The freshness policy (``"live"`` or ``"static"``).
        path: Where a ``live`` root lives on disk (required for ``live``).
        source: Where a ``static`` root's provider materialises from (required
            for ``static``).
        version: A ``static`` root's version stamp; a change triggers a rebuild
            (required for ``static``).
        provider: The :class:`SourceProvider` key that acquires a ``static``
            root (required for ``static``).
        include: Per-root glob patterns selecting files to index.
        exclude: Per-root glob patterns excluding files.
    """

    tier: str
    watch: Literal["live", "static"]
    path: str | None = None
    source: str | None = None
    version: str | None = None
    provider: str | None = None
    include: list[str] = []
    exclude: list[str] = []

    @model_validator(mode="after")
    def _check_policy_fields(self) -> RootConfig:
        """Enforce the per-policy required fields.

        A ``live`` root needs a ``path`` (the watcher must know what subtree to
        observe). A ``static`` root needs a ``source`` + ``version`` + a
        ``provider`` (the version stamp is the rebuild trigger; without it the
        trigger is undefined). Failing here keeps a malformed root from silently
        producing a watcher with nothing to watch or a static tier that never
        rebuilds.
        """
        if self.watch == WATCH_LIVE:
            if not self.path:
                raise ValueError(f"live root {self.tier!r} must declare a 'path'")
        else:  # WATCH_STATIC
            missing = [
                field
                for field in ("source", "version", "provider")
                if not getattr(self, field)
            ]
            if missing:
                raise ValueError(
                    f"static root {self.tier!r} must declare {', '.join(missing)}"
                )
        return self


class AuthKey(_StrictModel):
    """One named API key, referenced by environment-variable name only (D9).

    Attributes:
        name: A human label per developer/service (used to revoke one identity
            without disturbing others).
        key_env: The *name* of the environment variable holding this key's
            value — the secret itself is never inlined in the config.
    """

    name: str
    key_env: str


class AuthConfig(_StrictModel):
    """The optional rotatable-key auth layer (D9).

    Gates access to the *service* only — not per-content ACL (every
    authenticated developer sees the same indexed code). Hot-reloadable: rotate
    = add a new key / drop an old one with zero downtime.

    Attributes:
        enabled: Whether the auth layer gates requests. Off ⇒ no-auth localhost
            single-user mode.
        keys: The configured set of named keys (each an ``*_env`` ref).
        tls_terminated_upstream: D11 — loremaster serves plain HTTP behind a
            TLS-terminating ingress and assumes encrypted transport. Defaults to
            ``True`` to reflect that assumption.
    """

    enabled: bool = False
    keys: list[AuthKey] = []
    tls_terminated_upstream: bool = True


class WatcherConfig(_StrictModel):
    """Live-watch and reconcile configuration.

    Attributes:
        enabled: Whether the inotify watcher runs.
        observer: The watchdog observer backend (e.g. ``inotify``).
        debounce_ms: Debounce window, in milliseconds, before re-indexing a file.
        reconcile_interval_s: Periodic reconcile-sweep interval, in seconds.
    """

    enabled: bool
    observer: str
    debounce_ms: PositiveInt
    reconcile_interval_s: PositiveInt


class ServerConfig(_StrictModel):
    """MCP server bind configuration.

    Attributes:
        host: The bind host.
        path: The MCP mount path (e.g. ``/mcp``).
        port: The bind port.
    """

    host: str
    path: str
    port: int


class LoggingConfig(_StrictModel):
    """Structured-logging configuration (the cross-cutting observability layer).

    OPTIONAL on :class:`LoreConfig` with a default instance, so every existing
    ``lore.yaml`` (which carries no ``logging:`` section) keeps validating and
    transparently gets the JSON-to-stderr default. The run-time level is further
    overridable by the ``LORE_LOG_LEVEL`` environment variable at the entry path
    (env beats this config default), so an operator can crank verbosity without
    editing the config.

    Attributes:
        level: The minimum level emitted on the lore-namespace loggers
            (``"DEBUG"``/``"INFO"``/``"WARNING"``/…). Defaults to ``"INFO"``.
        format: ``"json"`` (one structured object per record, Mezmo-friendly) or
            ``"keyvalue"`` (a human ``ts level logger event k=v`` line for local
            dev). Defaults to ``"json"``.
        destination: Where records are written. Only ``"stderr"`` is supported
            (uvicorn owns stdout); modelled as a ``Literal`` so a typo fails loud.
    """

    level: str = "INFO"
    format: Literal["json", "keyvalue"] = "json"
    destination: Literal["stderr"] = "stderr"


class RerankerConfig(_StrictModel):
    """A cross-encoder reranker backend (P6 §6 item 9, the config-gated seam).

    Locates an external cross-encoder rerank service the search pipeline routes
    its RRF-fused candidates through, AFTER the store's hybrid fusion and BEFORE
    formatting. PRESENCE of this block is the sole gate: with no ``reranker:``
    the pipeline provably never calls the reranker seam (a merely-injected seam
    object stays inert), so the default deploy pays no rerank latency.

    Attributes:
        url: The rerank service endpoint (a cross-encoder scoring API).
        model: The reranker model identifier the service serves.
    """

    url: str
    model: str


class SearchConfig(_StrictModel):
    """Query-time search configuration (P6 §6 item 9).

    OPTIONAL on :class:`LoreConfig` with a default instance (mirroring
    :class:`LoggingConfig` / :class:`SurrealConfig`), so every existing
    ``lore.yaml`` (which carries no ``search:`` section) keeps validating and
    transparently gets the defaults — chiefly ``reranker: null`` (no reranker).

    Attributes:
        reranker: The optional config-gated cross-encoder reranker (see
            :class:`RerankerConfig`). ``None`` (the default) means the pipeline's
            reranker seam is provably NOT called — the config, not the mere
            presence of a seam object, is the gate.
    """

    reranker: RerankerConfig | None = None


# PKT-28 C1 (agent-comms) render-layer knobs (design doc
# docs/design/2026-07-12-pkt28-c1-semantics.md §4). Repo law: no hardcoded
# values — these three tune what the ``lore_comms`` dispatcher renders
# (staleness marker, fleet page size, brief-body warn line), so they live in
# config, not module constants, even though the store layer (agents.py/
# briefs.py) needed neither at build time.
DEFAULT_COMMS_STALE_HEARTBEAT_S: int = 600
DEFAULT_COMMS_FLEET_LIMIT: int = 20
DEFAULT_COMMS_BRIEF_WARN_CHARS: int = 4000


class CommsConfig(_StrictModel):
    """Agent-comms (``lore_comms``) render-layer configuration (PKT-28 C1).

    OPTIONAL on :class:`LoreConfig` with a default instance (mirroring
    :class:`LoggingConfig` / :class:`SurrealConfig` / :class:`SearchConfig`),
    so every existing ``lore.yaml`` (which carries no ``comms:`` section)
    keeps validating and transparently gets the documented defaults.

    Attributes:
        stale_heartbeat_s: The heartbeat age, in seconds, past which
            ``lore_comms`` renders a fleet row's status as ``⚠ STALE``
            (design doc §3/§6) — derived at render time, never stored.
        fleet_limit: The default number of fleet rows ``action=fleet``
            renders before a counted, clamped elision notice (design doc §6).
        brief_body_warn_chars: The body length, in characters, past which
            ``action=brief_publish`` appends a size-warning line (design doc
            §5.2) — a warning only, never a rejection.
    """

    stale_heartbeat_s: PositiveInt = DEFAULT_COMMS_STALE_HEARTBEAT_S
    fleet_limit: PositiveInt = DEFAULT_COMMS_FLEET_LIMIT
    brief_body_warn_chars: PositiveInt = DEFAULT_COMMS_BRIEF_WARN_CHARS


# The default model the token-calibration yardstick probes run against.
# Provenance: SURVEY-FINAL (2026-07-04) derived the calibration baseline against
# ``claude-sonnet-5``; YARDSTICK-FINAL (2026-07-04) then proved token counts are
# byte-identical across the current generation (sonnet-5 / opus-4-8 / fable-5),
# so the baseline is GENERATION-anchored, not model-anchored — swapping to any
# same-generation sibling leaves the calibration numbers unchanged.
DEFAULT_YARDSTICK_MODEL: str = "claude-sonnet-5"


class AnthropicConfig(_StrictModel):
    """Anthropic API configuration — REQUIRED (P8c token-calibration probes).

    Unlike the optional-with-default sub-sections (:class:`LoggingConfig`,
    :class:`SurrealConfig`, :class:`SearchConfig`), this block is REQUIRED on
    :class:`LoreConfig`: lore needs an Anthropic key to run its calibration
    yardstick, so a ``lore.yaml`` without an ``anthropic:`` section fails at load
    naming the missing field rather than deferring to an opaque 401 later.

    The API key is referenced by environment-variable *name* only (mirroring
    :attr:`EmbeddingConfig.api_key_env` and :attr:`AuthKey.key_env`) — the secret
    itself is never inlined. :func:`load_config` resolves it EAGERLY at load via
    :func:`resolve_secret`, so a missing or empty key fails boot immediately.

    Attributes:
        api_key_env: The *name* of the environment variable holding the Anthropic
            API key (e.g. ``ANTHROPIC_API_KEY``) — never the key itself.
        yardstick_model: The model the token-calibration probes run against.
            Defaults to :data:`DEFAULT_YARDSTICK_MODEL` (``claude-sonnet-5``); see
            that constant for the generation-anchored provenance.
    """

    api_key_env: str
    yardstick_model: str = DEFAULT_YARDSTICK_MODEL


class LoreConfig(_StrictModel):
    """The complete, validated parse of a project's tiered ``lore.yaml``.

    Known sections forbid unknown keys. The single sanctioned escape hatch is
    ``extensions``: an opaque pass-through mapping the base neither interprets
    nor rejects, for a registered :class:`Extension` to validate itself.

    Attributes:
        schema_version: The config schema version.
        project: Project identity.
        embedding: Embedding-backend configuration.
        anthropic: Anthropic API configuration (P8c). REQUIRED — a ``lore.yaml``
            without an ``anthropic:`` section fails at load, and its
            ``api_key_env`` is resolved eagerly by :func:`load_config`.
        roots: The source roots/tiers with per-tier freshness policies (D5).
            Defaults to an empty list (a bare single-tree generic deploy).
        include: Glob patterns (relative to the project root) selecting files to
            index in single-tree mode.
        exclude_dirs: Directory names pruned at walk time.
        exclude_globs: Glob patterns excluding individual files.
        chunkers: Map of file extension → chunker configuration mapping.
        watcher: Live-watch and reconcile configuration.
        server: MCP server bind configuration.
        logging: Structured-logging configuration. OPTIONAL with a default, so an
            existing ``lore.yaml`` with no ``logging:`` section still validates.
        search: Query-time search configuration (P6 §6 item 9). OPTIONAL with a
            default, so an existing ``lore.yaml`` with no ``search:`` section
            still validates; carries the config-gated reranker seam.
        comms: Agent-comms (``lore_comms``) render-layer configuration
            (PKT-28 C1). OPTIONAL with a default, so an existing ``lore.yaml``
            with no ``comms:`` section still validates and gets the
            documented defaults (stale-heartbeat threshold, fleet page size,
            brief-body warn size).
        auth: The optional rotatable-key auth layer (D9). ``None`` ⇒ no-auth
            localhost mode.
        extensions: The OPAQUE extension namespace — a mapping of extension name
            → arbitrary nested config the base passes through verbatim.
    """

    schema_version: int
    project: ProjectConfig
    embedding: EmbeddingConfig
    # REQUIRED (no default): lore needs an Anthropic key for its calibration
    # yardstick, so a missing ``anthropic:`` section fails at load naming the
    # field. Its ``api_key_env`` is resolved EAGERLY in ``load_config``.
    anthropic: AnthropicConfig
    # OPTIONAL with a default instance (like ``logging``), so an existing
    # ``lore.yaml`` with no ``surreal:`` section still validates and gets the
    # localhost production defaults; the dev-server harness sets it explicitly.
    surreal: SurrealConfig = SurrealConfig()
    roots: list[RootConfig] = []
    include: list[str]
    exclude_dirs: list[str]
    exclude_globs: list[str]
    chunkers: dict[str, dict[str, Any]]
    watcher: WatcherConfig
    server: ServerConfig
    logging: LoggingConfig = LoggingConfig()
    # OPTIONAL with a default instance (like ``logging``): an existing
    # ``lore.yaml`` with no ``search:`` section still validates and gets the
    # documented default (``reranker: null`` — the reranker seam stays off).
    search: SearchConfig = SearchConfig()
    # OPTIONAL with a default instance (like ``search``): an existing
    # ``lore.yaml`` with no ``comms:`` section still validates and gets the
    # documented defaults (PKT-28 C1).
    comms: CommsConfig = CommsConfig()
    auth: AuthConfig | None = None
    # The opaque extension namespace: a typo'd extension *key* is not catchable
    # by the base (it cannot know every extension's schema), so this is a
    # deliberate pass-through validated downstream by the registered extension.
    extensions: dict[str, dict[str, Any]] = {}

    @property
    def effective_roots(self) -> list[RootConfig]:
        """The roots every indexing consumer iterates — explicit or synthesised.

        When ``roots:`` is explicitly configured (demand_intelligence / lore,
        and any multi-tier deploy), it is returned VERBATIM — the explicit-roots
        path is untouched. When ``roots:`` is empty (the documented single-tree
        style: top-level ``include`` globs and NO ``roots:``), ONE LIVE root is
        synthesised so the project indexes as documented instead of silently
        indexing nothing.

        The synthesised root is rooted at :attr:`ProjectConfig.root`, watches
        live, and carries the top-level :attr:`include` globs. Project-level
        ``exclude_dirs`` and ``exclude_globs`` are applied by the shared walk
        predicates (``walked_dirs`` / ``is_included``) against ``config`` and so
        need not be duplicated onto the synthesised root's per-root ``exclude``.

        Returns:
            The explicit ``roots`` when non-empty, else a one-element list with
            the synthesised default live root.
        """
        if self.roots:
            return self.roots
        return [
            RootConfig(
                tier=TIER_DEFAULT,
                watch=WATCH_LIVE,
                path=self.project.root,
                include=list(self.include),
            )
        ]

    @property
    def effective_surreal_database(self) -> str:
        """The SurrealDB database name for this project.

        Returns the explicit :attr:`SurrealConfig.database` when set, else the
        project slug — the same identity the on-disk state-DB paths and the
        ``lore_<slug>`` naming convention use, so the Surreal database co-locates
        with the rest of a project's durable state under one name.
        """
        return self.surreal.database or self.project.slug


def load_config(path: str | Path) -> LoreConfig:
    """Read a ``lore.yaml`` file and return the validated :class:`LoreConfig`.

    Secrets required at boot are resolved EAGERLY here (fail-fast): the
    ``anthropic.api_key_env`` variable is read immediately so a missing or empty
    key aborts the load rather than surfacing as an opaque 401 at first probe.
    This is the boot seam — the schema-only :meth:`LoreConfig.model_validate`
    deliberately does NOT touch the environment (mirroring how the TEI/auth keys
    resolve lazily in their own consumers).

    Args:
        path: The filesystem path to the YAML config.

    Returns:
        The parsed, validated configuration.

    Raises:
        pydantic.ValidationError: If the YAML contents violate the schema.
        ValueError: If ``anthropic.api_key_env`` names an environment variable
            that is unset or empty — the message names BOTH the yaml field and
            the variable, chained from the underlying :class:`KeyError`.
        FileNotFoundError: If ``path`` does not exist.
    """
    text = Path(path).read_text(encoding="utf-8")
    raw: Any = yaml.safe_load(text)
    config = LoreConfig.model_validate(raw)
    # Fail-fast: resolve the REQUIRED Anthropic key at load. resolve_secret
    # raises KeyError (naming the variable) when it is unset or empty; re-raise
    # as a ValueError that ALSO names the yaml field so the operator can fix the
    # config and the environment in one step.
    try:
        resolve_secret(config.anthropic.api_key_env)
    except KeyError as error:
        raise ValueError(
            f"anthropic.api_key_env references environment variable "
            f"{config.anthropic.api_key_env!r}, which is unset or empty; "
            f"export it before starting lore."
        ) from error
    return config


def resolve_secret(env_var_name: str) -> str:
    """Resolve a secret value from the environment by variable name.

    The returned value is never stripped or otherwise mutated — a secret whose
    real content happens to include leading/trailing whitespace passes through
    byte-exact. Only the *emptiness check* looks past whitespace, to catch a
    variable that was set to nothing but spaces/tabs.

    Args:
        env_var_name: The name of the environment variable to read.

    Returns:
        The variable's value, unmodified.

    Raises:
        KeyError: If the variable is unset, set to an empty string, or set to
            a whitespace-only string — an empty or blank API key is effectively
            missing. The message names the variable so the operator can
            remediate immediately.
    """
    value = os.environ.get(env_var_name)
    if not value or not value.strip():
        raise KeyError(
            f"Required secret environment variable {env_var_name!r} is unset, empty, "
            f"or whitespace-only; export it before starting lore."
        )
    return value
