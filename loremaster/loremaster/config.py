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
from pydantic import (
    BaseModel,
    ConfigDict,
    PositiveInt,
    StringConstraints,
    model_validator,
)

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
# ``-`` / ``_``, starting with an alphanumeric, non-empty. The slug is f-string'd
# straight into BOTH the ``lore_<slug>`` Qdrant collection name AND the on-disk
# state-DB paths (``<slug>.db`` / ``<slug>.memory.db`` / ``<slug>.graph.kuzu``), so
# a traversal (``../etc``), a separator (``a/b``), whitespace, an uppercase, or a
# leading separator is a path/collection hazard. Constraining it makes an
# operator typo or a malicious value FAIL FAST at config load rather than
# silently relocating the durable state outside the state dir.
SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_-]*$"

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
        slug: The project identifier; drives the ``lore_<slug>`` collection name
            AND the on-disk state-DB paths (``<slug>.db`` / ``<slug>.memory.db``
            / ``<slug>.graph.kuzu``). Constrained to the safe :data:`SLUG_PATTERN`
            charset because it is interpolated straight into filesystem paths and
            a Qdrant collection name: a traversal, separator, whitespace,
            uppercase, or leading-separator slug is a path/collection hazard and
            must be rejected at load, not silently written to the wrong place.
        root: The project root the include/exclude globs are resolved against.
    """

    slug: SlugStr
    root: str


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
    """

    backend: Literal["tei", "voyage-cloud"]
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


class QdrantConfig(_StrictModel):
    """Qdrant connection configuration.

    Attributes:
        url: The Qdrant base URL.
        api_key_env: The *name* of the environment variable holding the API key.
    """

    url: str
    api_key_env: str


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


class LoreConfig(_StrictModel):
    """The complete, validated parse of a project's tiered ``lore.yaml``.

    Known sections forbid unknown keys. The single sanctioned escape hatch is
    ``extensions``: an opaque pass-through mapping the base neither interprets
    nor rejects, for a registered :class:`Extension` to validate itself.

    Attributes:
        schema_version: The config schema version.
        project: Project identity.
        embedding: Embedding-backend configuration.
        qdrant: Qdrant connection configuration.
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
        auth: The optional rotatable-key auth layer (D9). ``None`` ⇒ no-auth
            localhost mode.
        extensions: The OPAQUE extension namespace — a mapping of extension name
            → arbitrary nested config the base passes through verbatim.
    """

    schema_version: int
    project: ProjectConfig
    embedding: EmbeddingConfig
    qdrant: QdrantConfig
    roots: list[RootConfig] = []
    include: list[str]
    exclude_dirs: list[str]
    exclude_globs: list[str]
    chunkers: dict[str, dict[str, Any]]
    watcher: WatcherConfig
    server: ServerConfig
    logging: LoggingConfig = LoggingConfig()
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


def load_config(path: str | Path) -> LoreConfig:
    """Read a ``lore.yaml`` file and return the validated :class:`LoreConfig`.

    Args:
        path: The filesystem path to the YAML config.

    Returns:
        The parsed, validated configuration.

    Raises:
        pydantic.ValidationError: If the YAML contents violate the schema.
        FileNotFoundError: If ``path`` does not exist.
    """
    text = Path(path).read_text(encoding="utf-8")
    raw: Any = yaml.safe_load(text)
    return LoreConfig.model_validate(raw)


def resolve_secret(env_var_name: str) -> str:
    """Resolve a secret value from the environment by variable name.

    Args:
        env_var_name: The name of the environment variable to read.

    Returns:
        The variable's value.

    Raises:
        KeyError: If the variable is unset *or* set to an empty string — an
            empty API key is effectively missing. The message names the variable
            so the operator can remediate immediately.
    """
    value = os.environ.get(env_var_name)
    if not value:
        raise KeyError(
            f"Required secret environment variable {env_var_name!r} is unset or empty; "
            f"export it before starting lore."
        )
    return value
