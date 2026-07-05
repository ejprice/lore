"""Contract tests for ``loremaster.config`` under the AMENDED tiered contract.

These pin the project-configuration boundary, including the amendment deltas:

* ``LoreConfig`` parses the canonical ``lore.yaml`` shape from the approved plan.
* Known sections stay strict (``extra="forbid"``): a typo'd key fails loudly
  rather than being silently dropped — a dropped ``dim`` would let a
  wrong-dimension index slip past the startup coherence gate.
* ``dim`` must be a positive integer; secrets are referenced by env-var *name*
  only, and ``resolve_secret`` raises a clear error when the var is unset.

AMENDMENT deltas (the load-bearing new behaviour):

* A **``roots:``** list — each root declares ``{tier, watch}`` plus per-policy
  fields: a ``live`` root needs a ``path``; a ``static`` root needs a
  ``source`` + ``version`` + ``provider`` and carries per-root include/exclude.
* An **``extensions:`` OPAQUE namespace** — modelled as a pass-through mapping
  the base does NOT reject (an extension validates it with its own model),
  WHILE the known top-level sections still reject unknown keys. This is the
  exact tension the parked ``extra="forbid"`` test enforced: a *raw extra
  top-level field* must still be rejected, but ``extensions:`` must pass.
* An optional **``auth``** block (D9): a set of named API keys via ``*_env``
  secret refs; absent ⇒ no-auth localhost mode. TLS is terminated upstream
  (D11) — modelled as a flag only, no server here.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml
from loremaster.config import LoreConfig, ProjectConfig, load_config, resolve_secret
from pydantic import ValidationError

# The canonical tiered lore.yaml as a Python mapping. Kept inline (not a fixture
# file) so the expected shape is reviewable here and the test is self-contained.
_CANONICAL_CONFIG: dict[str, Any] = {
    "schema_version": 1,
    "project": {"slug": "demand_intelligence", "root": "."},
    # The REQUIRED P8c Anthropic block (api_key_env is an env-var NAME only). The
    # suite conftest sets a dummy ``ANTHROPIC_API_KEY`` so ``load_config``'s eager
    # resolution passes for every fixture that boots through it.
    "anthropic": {"api_key_env": "ANTHROPIC_API_KEY", "yardstick_model": "claude-sonnet-5"},
    "embedding": {
        "backend": "tei",
        "base_url": "http://tei.example:8080",
        "endpoint": "/embed",
        "model": "voyageai/voyage-4-nano",
        "dim": 2048,
        "truncate": False,
        "max_input_tokens": 8192,
        "max_batch_texts": 32,
        "concurrency": 2,
        "connect_timeout_s": 5,
        "api_key_env": "LORE_TEI_KEY",
        "tokenizer": "voyage-4-nano",
    },
    "roots": [
        {
            "tier": "custom",
            "watch": "live",
            "path": "/workspace/custom",
            "include": ["**/*.py"],
            "exclude": ["**/__pycache__/**"],
        },
        {
            "tier": "community",
            "watch": "static",
            "source": "/roots/community",
            "version": "15.0.20260420",
            "provider": "local_directory",
            "include": ["**/*.py", "**/*.xml"],
            "exclude": ["**/tests/**"],
        },
    ],
    "include": ["src/**/*.py", "*.md"],
    "exclude_dirs": [".git", ".venv", ".claude"],
    "exclude_globs": ["**/*.parquet", "uv.lock"],
    "chunkers": {
        ".py": {"chunker": "python_ast"},
        ".sql": {"chunker": "sql", "dialect": "postgres"},
    },
    "watcher": {
        "enabled": True,
        "observer": "inotify",
        "debounce_ms": 1500,
        "reconcile_interval_s": 600,
    },
    "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9201},
    "extensions": {
        "odoo": {
            "snapshot_dir": "/home/ejprice/docker/mcp/lore-snapshot",
            "installed_modules_file": "/source/installed.txt",
        }
    },
}


def _deep_copy_config() -> dict[str, Any]:
    """Return an independent deep copy of the canonical config mapping."""
    return copy.deepcopy(_CANONICAL_CONFIG)


class TestLoreConfigParsing:
    """The model accepts and faithfully reflects the canonical tiered config."""

    def test_parses_canonical_config(self) -> None:
        config = LoreConfig.model_validate(_CANONICAL_CONFIG)
        assert config.project.slug == "demand_intelligence"
        assert config.embedding.backend == "tei"
        assert config.embedding.dim == 2048
        assert config.embedding.max_input_tokens == 8192
        assert config.embedding.max_batch_texts == 32
        assert config.embedding.concurrency == 2
        assert config.embedding.connect_timeout_s == 5
        assert config.embedding.api_key_env == "LORE_TEI_KEY"
        assert config.embedding.truncate is False
        assert config.include == ["src/**/*.py", "*.md"]
        assert config.exclude_dirs == [".git", ".venv", ".claude"]
        assert config.exclude_globs == ["**/*.parquet", "uv.lock"]
        assert config.chunkers[".sql"] == {"chunker": "sql", "dialect": "postgres"}
        assert config.watcher.enabled is True
        assert config.watcher.debounce_ms == 1500
        assert config.watcher.reconcile_interval_s == 600
        assert config.server.host == "127.0.0.1"
        assert config.server.path == "/mcp"
        assert config.server.port == 9201

    def test_backend_accepts_voyage_cloud(self) -> None:
        payload = _deep_copy_config()
        payload["embedding"]["backend"] = "voyage-cloud"
        config = LoreConfig.model_validate(payload)
        assert config.embedding.backend == "voyage-cloud"

    def test_backend_rejects_unknown_literal(self) -> None:
        payload = _deep_copy_config()
        payload["embedding"]["backend"] = "openai"
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)


class TestRoots:
    """The amendment's multi-root / per-tier freshness model (D5)."""

    def test_parses_both_roots(self) -> None:
        config = LoreConfig.model_validate(_CANONICAL_CONFIG)
        assert len(config.roots) == 2
        tiers = [root.tier for root in config.roots]
        assert tiers == ["custom", "community"]

    def test_live_root_exposes_path_and_watch(self) -> None:
        config = LoreConfig.model_validate(_CANONICAL_CONFIG)
        live = config.roots[0]
        assert live.tier == "custom"
        assert live.watch == "live"
        assert live.path == "/workspace/custom"
        assert live.include == ["**/*.py"]
        assert live.exclude == ["**/__pycache__/**"]

    def test_static_root_exposes_source_version_provider(self) -> None:
        config = LoreConfig.model_validate(_CANONICAL_CONFIG)
        static = config.roots[1]
        assert static.tier == "community"
        assert static.watch == "static"
        assert static.source == "/roots/community"
        assert static.version == "15.0.20260420"
        assert static.provider == "local_directory"

    def test_watch_rejects_unknown_policy(self) -> None:
        payload = _deep_copy_config()
        payload["roots"][0]["watch"] = "sometimes"
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_live_root_requires_a_path(self) -> None:
        # A live (watched) root has no source/version; it must declare where it
        # lives on disk so the watcher knows what subtree to observe.
        payload = _deep_copy_config()
        del payload["roots"][0]["path"]
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_static_root_requires_a_version_stamp(self) -> None:
        # A static tier is rebuilt when its version stamp changes; without one
        # the rebuild trigger is undefined, so it must fail loudly at load.
        payload = _deep_copy_config()
        del payload["roots"][1]["version"]
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_root_rejects_extra_field(self) -> None:
        # A root is a *known* section — a typo'd key (e.g. ``waatch``) must fail.
        payload = _deep_copy_config()
        payload["roots"][0]["waatch"] = "live"
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_roots_default_to_empty_list(self) -> None:
        # A bare generic deploy may omit ``roots`` entirely (single-tree mode).
        payload = _deep_copy_config()
        del payload["roots"]
        config = LoreConfig.model_validate(payload)
        assert config.roots == []


class TestEffectiveRoots:
    """``effective_roots`` synthesises a default live root for single-tree configs.

    A ``lore.yaml`` in the documented Deliverable-3 single-tree style declares
    top-level ``include`` globs and NO ``roots:`` — the config parses fine but
    ``roots`` is empty, so every consumer that iterates ``roots`` would index
    nothing. ``effective_roots`` closes that footgun: an empty ``roots`` yields
    ONE synthesised LIVE root rooted at ``project.root`` with the top-level
    ``include`` globs; an explicit ``roots`` list is returned verbatim.
    """

    def test_explicit_roots_are_returned_unchanged(self) -> None:
        # When roots are explicitly configured, effective_roots is a pass-through:
        # the demand_intelligence / lore explicit-roots path is untouched.
        config = LoreConfig.model_validate(_CANONICAL_CONFIG)
        assert config.roots  # the canonical config has explicit roots
        assert config.effective_roots == config.roots

    def test_empty_roots_synthesises_one_default_live_root(self) -> None:
        # The single-tree footgun: no roots + top-level include globs must yield
        # ONE live root rooted at project.root carrying those include globs.
        payload = _deep_copy_config()
        del payload["roots"]
        payload["project"]["root"] = "/srv/project"
        payload["include"] = ["src/**/*.py", "*.md"]
        config = LoreConfig.model_validate(payload)

        effective = config.effective_roots
        assert len(effective) == 1
        root = effective[0]
        assert root.watch == "live"
        assert root.path == "/srv/project"
        assert root.include == ["src/**/*.py", "*.md"]
        # A non-empty tier name so manifest/store/graph partitioning works.
        assert root.tier


class TestExtensionsNamespace:
    """The opaque ``extensions:`` pass-through (seam 7 / §A1.3.7)."""

    def test_extensions_block_is_accepted_and_preserved(self) -> None:
        config = LoreConfig.model_validate(_CANONICAL_CONFIG)
        # The base does not interpret the block — it carries it through verbatim
        # for the registered extension to validate with its own pydantic model.
        assert config.extensions["odoo"]["snapshot_dir"] == (
            "/home/ejprice/docker/mcp/lore-snapshot"
        )
        assert config.extensions["odoo"]["installed_modules_file"] == "/source/installed.txt"

    def test_extensions_accepts_arbitrary_extension_keys(self) -> None:
        # An unknown extension name + arbitrary nested keys must pass — the base
        # is deliberately opaque here (it cannot know every extension's schema).
        payload = _deep_copy_config()
        payload["extensions"] = {"some_future_ext": {"a": 1, "nested": {"b": [1, 2]}}}
        config = LoreConfig.model_validate(payload)
        assert config.extensions["some_future_ext"]["nested"]["b"] == [1, 2]

    def test_extensions_defaults_to_empty_mapping(self) -> None:
        payload = _deep_copy_config()
        del payload["extensions"]
        config = LoreConfig.model_validate(payload)
        assert config.extensions == {}


class TestLoreConfigStrictness:
    """Known sections forbid unknown fields; only ``extensions:`` is opaque."""

    def test_rejects_extra_top_level_field(self) -> None:
        # The parked-foundation invariant: a *raw* extra top-level field is
        # rejected. ``extensions:`` is the ONLY sanctioned escape hatch.
        payload = _deep_copy_config()
        payload["unexpected_top_level"] = True
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_rejects_extra_embedding_field(self) -> None:
        payload = _deep_copy_config()
        payload["embedding"]["retry_backoff"] = True  # plausible typo'd extra
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_rejects_extra_project_field(self) -> None:
        payload = _deep_copy_config()
        payload["project"]["nmae"] = "oops"
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_rejects_a_qdrant_block(self) -> None:
        # P8a retired the ``qdrant:`` config section entirely. The strict model
        # (extra="forbid") now REJECTS any lingering ``qdrant:`` block outright —
        # the intended fail-loud posture so a stale, pre-P8a lore.yaml fails at
        # load rather than silently ignoring a section the server no longer reads
        # (P8f ships the config upgrader that strips it).
        payload = _deep_copy_config()
        payload["qdrant"] = {
            "url": "http://127.0.0.1:16333",
            "api_key_env": "QDRANT__SERVICE__API_KEY",
        }
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)


class TestAuth:
    """The optional D9 rotatable-key auth block."""

    def test_auth_is_optional_off_by_default(self) -> None:
        # Absent ``auth`` ⇒ no-auth localhost single-user mode (unchanged for the
        # local demand_intelligence deploy).
        payload = _deep_copy_config()
        payload.pop("auth", None)
        config = LoreConfig.model_validate(payload)
        assert config.auth is None

    def test_auth_models_named_keys_via_env_refs(self) -> None:
        payload = _deep_copy_config()
        payload["auth"] = {
            "enabled": True,
            "keys": [
                {"name": "alice", "key_env": "LORE_KEY_ALICE"},
                {"name": "ci", "key_env": "LORE_KEY_CI"},
            ],
        }
        config = LoreConfig.model_validate(payload)
        assert config.auth is not None
        assert config.auth.enabled is True
        names = [k.name for k in config.auth.keys]
        assert names == ["alice", "ci"]
        # Secrets are referenced by env-var NAME only — never inlined.
        assert config.auth.keys[0].key_env == "LORE_KEY_ALICE"

    def test_auth_secret_is_an_env_ref_not_inlined(self) -> None:
        # An auth key entry must NOT accept an inline raw secret value; only the
        # ``*_env`` name field exists, so a typo'd inline ``key`` is rejected.
        payload = _deep_copy_config()
        payload["auth"] = {
            "enabled": True,
            "keys": [{"name": "alice", "key": "raw-secret-should-be-rejected"}],
        }
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_tls_terminated_upstream_flag_defaults_true(self) -> None:
        # D11: loremaster serves plain HTTP behind a TLS-terminating ingress and
        # assumes encrypted transport. The default reflects that assumption.
        payload = _deep_copy_config()
        payload["auth"] = {
            "enabled": True,
            "keys": [{"name": "alice", "key_env": "LORE_KEY_ALICE"}],
        }
        config = LoreConfig.model_validate(payload)
        assert config.auth is not None
        assert config.auth.tls_terminated_upstream is True


class TestLoggingConfig:
    """The optional structured-logging block (defaults, strictness preserved)."""

    def test_logging_defaults_when_block_absent(self) -> None:
        # The block is OPTIONAL with a default, so every existing lore.yaml (which
        # has NO ``logging:`` section) still validates and gets the JSON default.
        payload = _deep_copy_config()
        payload.pop("logging", None)
        config = LoreConfig.model_validate(payload)
        assert config.logging.level == "INFO"
        assert config.logging.format == "json"
        assert config.logging.destination == "stderr"

    def test_logging_block_is_parsed_when_present(self) -> None:
        payload = _deep_copy_config()
        payload["logging"] = {"level": "DEBUG", "format": "keyvalue", "destination": "stderr"}
        config = LoreConfig.model_validate(payload)
        assert config.logging.level == "DEBUG"
        assert config.logging.format == "keyvalue"

    def test_logging_format_rejects_unknown_literal(self) -> None:
        payload = _deep_copy_config()
        payload["logging"] = {"format": "xml"}
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_logging_block_rejects_extra_field(self) -> None:
        # A known section stays strict: a typo'd key inside ``logging`` fails loud.
        payload = _deep_copy_config()
        payload["logging"] = {"level": "INFO", "levle": "oops"}
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_adding_logging_block_does_not_weaken_top_level_strictness(self) -> None:
        # Regression guard: making ``logging`` an optional defaulted field must NOT
        # turn ``extra="forbid"`` off — an UNKNOWN top-level key is still rejected.
        payload = _deep_copy_config()
        payload["logging"] = {"level": "INFO"}
        payload["loggin"] = {"level": "INFO"}  # the realistic typo of the new key
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)


class TestDimValidation:
    """``dim`` must be a positive integer."""

    def test_rejects_zero_dim(self) -> None:
        payload = _deep_copy_config()
        payload["embedding"]["dim"] = 0
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_rejects_negative_dim(self) -> None:
        payload = _deep_copy_config()
        payload["embedding"]["dim"] = -1
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)


class TestLoadConfig:
    """``load_config`` reads YAML from disk and validates it (real fixture file)."""

    def test_loads_and_validates_yaml_file(self, tmp_path: Path) -> None:
        config_path = tmp_path / "lore.yaml"
        config_path.write_text(yaml.safe_dump(_CANONICAL_CONFIG), encoding="utf-8")
        config = load_config(config_path)
        assert isinstance(config, LoreConfig)
        assert config.project.slug == "demand_intelligence"
        assert config.embedding.dim == 2048
        assert len(config.roots) == 2

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        config_path = tmp_path / "lore.yaml"
        config_path.write_text(yaml.safe_dump(_CANONICAL_CONFIG), encoding="utf-8")
        config = load_config(str(config_path))
        assert config.project.slug == "demand_intelligence"

    def test_invalid_yaml_contents_raise_validation_error(self, tmp_path: Path) -> None:
        payload = _deep_copy_config()
        payload["embedding"]["dim"] = 0
        config_path = tmp_path / "lore.yaml"
        config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
        with pytest.raises(ValidationError):
            load_config(config_path)


class TestResolveSecret:
    """Secret resolution from the environment by variable name."""

    def test_returns_value_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LORE_TEI_KEY", "s3cr3t-token")
        assert resolve_secret("LORE_TEI_KEY") == "s3cr3t-token"

    def test_raises_clear_error_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LORE_TEI_KEY", raising=False)
        with pytest.raises(KeyError) as excinfo:
            resolve_secret("LORE_TEI_KEY")
        assert "LORE_TEI_KEY" in str(excinfo.value)

    def test_raises_when_set_but_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LORE_TEI_KEY", "")
        with pytest.raises(KeyError):
            resolve_secret("LORE_TEI_KEY")

    def test_raises_when_set_but_whitespace_only(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Whitespace-only ("   ") is truthy in Python, so a naive `if not value`
        # check lets it slip past — it must be rejected the same as unset/empty.
        monkeypatch.setenv("LORE_TEI_KEY", "   ")
        with pytest.raises(KeyError) as excinfo:
            resolve_secret("LORE_TEI_KEY")
        assert "LORE_TEI_KEY" in str(excinfo.value)

    def test_value_with_surrounding_whitespace_and_real_content_is_unmodified(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A secret may legitimately contain leading/trailing whitespace as part
        # of its actual bytes (e.g. copy-paste padding) — resolve_secret must
        # never strip or otherwise mutate the returned value.
        monkeypatch.setenv("LORE_TEI_KEY", "  s3cr3t-token  ")
        assert resolve_secret("LORE_TEI_KEY") == "  s3cr3t-token  "


# ---------------------------------------------------------------------------
# FIX 1 — ProjectConfig.slug must be constrained to a safe charset
# ---------------------------------------------------------------------------
#
# ``ProjectConfig.slug`` is the single value that drives BOTH the SurrealDB
# database name AND the on-disk state paths the server constructs:
# ``_DEFAULT_MANIFEST_DIR / f"{slug}.db"`` / ``f"{slug}.memory.db"`` /
# ``f"{slug}.graph.db"`` (server.py ~2022-2023, _DEFAULT_MANIFEST_DIR ~2954).
#
# Today the field is a bare ``str`` — unconstrained. An operator typo or a
# malicious config could put path-traversal (``../etc``), a separator (``a/b``),
# whitespace (``Has Space``), uppercase (``UPPER``), an empty string, or a
# leading separator (``-leading``) into the slug. Because the slug is f-string'd
# straight into a filesystem path, ``../etc`` would relocate the state DBs OUTSIDE
# the state dir, and a separator could collide / escape the database namespace.
# This is defense-in-depth: the config is operator-controlled, but a typo must
# FAIL FAST at load time rather than silently writing the durable memory ledger
# to the wrong place.
#
# The contract (from the requirement, NOT from any implementation): the slug must
# match ``^[a-z0-9][a-z0-9_-]*$`` — lowercase alphanumerics plus ``-`` / ``_``,
# not starting with a separator, non-empty. A valid slug is accepted; an invalid
# one raises a pydantic ``ValidationError`` at config load (parsing time), exactly
# like every other strict field on the model.
#
# These tests are BEHAVIOURALLY RED today: the unconstrained ``str`` accepts every
# malicious value below without error. The assertions are accept-vs-reject
# (independent of HOW the constraint is implemented — a regex, an annotated type,
# a validator); they do not re-state any implementation formula (clause 2).
# ---------------------------------------------------------------------------

# The documented safe-charset contract for a slug. Stated here as the spec the
# test verifies — NOT copied from the implementation.
# Lowercase alnum + ``_``, must start with an alnum, non-empty. HYPHENS ARE
# REJECTED (operator directive 2026-07-03): the slug becomes the SurrealDB
# database name (``effective_surreal_database``), and an unescaped hyphenated
# identifier fails SurrealQL parsing — blocked at config load rather than
# escaped at every interpolation site.
_SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_]*$"

# VALID slugs that MUST be accepted. Grounded in real lore deployments: ``lore``
# (this repo's own slug), ``demand_intelligence`` (the canonical config above),
# and an underscore+digit mix proving the full permitted charset parses.
_VALID_SLUGS: tuple[str, ...] = (
    "lore",
    "demand_intelligence",
    "my_proj_2",
)

# INVALID slugs that MUST raise at load. Each is a realistic operator-typo or
# attack input, annotated with the failure mode it exercises (the adversarial
# pre-flight, encoded as data so every entry is a case, not a comment).
_INVALID_SLUGS: dict[str, str] = {
    "../etc": "path traversal — escapes the state dir, relocates the DBs",
    "a/b": "embedded separator — escapes the slug into a subpath / collection",
    "Has Space": "whitespace + a space — not a safe filename / collection token",
    "UPPER": "uppercase — the SurrealDB database name and the convention are lowercase",
    "": "empty — yields a bare '.db' path and a nameless database",
    "-leading": "leading separator — must start with an alphanumeric",
    "my-proj": "hyphen — the slug is the SurrealDB database name; an unescaped "
    "hyphenated identifier fails SurrealQL parsing (blocked at load, task #32)",
}


def _project_payload(slug: str) -> dict[str, Any]:
    """A ``project`` section carrying ``slug`` over the canonical valid ``root``.

    Built by mutating the canonical config's ``project`` block so the test drives
    the SAME construction path production uses (clause 5: one source of truth),
    varying ONLY the slug under test.
    """
    payload = _deep_copy_config()
    payload["project"]["slug"] = slug
    return payload


class TestProjectSlugCharset:
    """FIX 1: ``ProjectConfig.slug`` is constrained to a safe ``[a-z0-9_]`` charset.

    The slug drives the ``lore_<slug>`` collection name and the on-disk
    ``<slug>.db`` / ``<slug>.memory.db`` / ``<slug>.graph.db`` paths. An
    unconstrained slug containing ``/``, ``..``, whitespace, uppercase, or a
    leading separator could relocate the durable state outside the state dir or
    collide collection names. A valid slug parses; an invalid slug fails loudly
    at config load (a pydantic ``ValidationError``), never silently.
    """

    @pytest.mark.parametrize("slug", _VALID_SLUGS)
    def test_valid_slug_is_accepted(self, slug: str) -> None:
        """A safe-charset slug constructs and round-trips unchanged.

        Arrange: a ProjectConfig payload with a valid slug.
        Act: construct the model directly.
        Assert: it validates and preserves the slug verbatim.
        """
        config = ProjectConfig(slug=slug, root=".")
        assert config.slug == slug

    @pytest.mark.parametrize("slug", _VALID_SLUGS)
    def test_valid_slug_matches_the_documented_pattern(self, slug: str) -> None:
        """Sanity-check the fixture: every 'valid' slug truly satisfies the spec.

        Independent of the implementation — this asserts the TEST DATA against the
        published pattern so a future edit cannot smuggle an invalid value into
        the accepted set (clause 2: guards the oracle, not the impl).
        """
        import re

        assert re.match(_SLUG_PATTERN, slug), (
            f"fixture error: {slug!r} is in _VALID_SLUGS but violates {_SLUG_PATTERN}"
        )

    @pytest.mark.parametrize(
        "slug", list(_INVALID_SLUGS), ids=[s or "<empty>" for s in _INVALID_SLUGS]
    )
    def test_invalid_slug_raises_validation_error_directly(self, slug: str) -> None:
        """An unsafe slug must fail loudly when ProjectConfig is constructed.

        Arrange: a slug from the adversarial set (path traversal, separator,
        whitespace, uppercase, empty, leading separator).
        Act + Assert: constructing ProjectConfig raises a pydantic ValidationError.
        """
        with pytest.raises(ValidationError):
            ProjectConfig(slug=slug, root=".")

    @pytest.mark.parametrize(
        "slug", list(_INVALID_SLUGS), ids=[s or "<empty>" for s in _INVALID_SLUGS]
    )
    def test_invalid_slug_fails_at_full_config_load(self, slug: str) -> None:
        """The constraint fires through the WHOLE LoreConfig parse, not just the leaf.

        The server validates the full config via ``LoreConfig.model_validate`` /
        ``load_config`` at startup (the real entry seam, clause 3). An invalid slug
        must abort that parse so a bad deploy never reaches the path-construction.
        """
        payload = _project_payload(slug)
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_path_traversal_slug_is_rejected_before_path_construction(self) -> None:
        """The headline attack: ``../../etc/cron.d`` must never reach an f-string path.

        A traversal slug is exactly what relocates ``<slug>.db`` outside the state
        dir. This pins that the rejection happens at validation — the slug never
        becomes a Path component (a direct security-boundary assertion, not a
        generic 'is it valid' check).
        """
        traversal_slug = "../../etc/cron.d/lore"
        with pytest.raises(ValidationError):
            ProjectConfig(slug=traversal_slug, root=".")

    def test_canonical_demand_intelligence_slug_still_parses_unchanged(self) -> None:
        """Anti-regression: the existing canonical deploy slug must keep validating.

        The whole canonical config (which uses ``demand_intelligence``) must still
        parse after the constraint lands — the fix must not break a real deploy.
        """
        config = LoreConfig.model_validate(_CANONICAL_CONFIG)
        assert config.project.slug == "demand_intelligence"


# ---------------------------------------------------------------------------
# Ledger #14 Part 2 — the sweep-level batch-embedding config seam
# ---------------------------------------------------------------------------
#
# ``EmbeddingConfig`` gains one new OPTIONAL, defaulted sub-section — ``batch``
# — mirroring the EXACT "OPTIONAL with a default instance" precedent already
# established by ``LoggingConfig`` / ``SurrealConfig`` on ``LoreConfig``: every
# existing ``lore.yaml`` (which carries no ``embedding.batch:`` block) keeps
# validating unchanged and transparently gets the documented defaults.
#
# THE PINNED SHAPE (this contract's own design decision, named here, blind to
# any implementation):
#
#   class BatchConfig(_StrictModel):
#       mode: Literal["realtime", "batch", "auto"] = "auto"
#       chunk_count_threshold: PositiveInt = 1000
#       poll_interval_s: float = <loresigil.voyage_batch.DEFAULT_POLL_INTERVAL_S>
#
#   class EmbeddingConfig(_StrictModel):
#       ...
#       batch: BatchConfig = BatchConfig()
#
# Design notes:
# * ``mode`` — "realtime" forces the pre-batch per-file embed path regardless
#   of embedder capability; "batch" forces the two-pass bulk-sweep path
#   (falling back to realtime with a WARNING if the embedder doesn't
#   advertise ``supports_batch``); "auto" (the default) picks batch only when
#   a sweep's pending chunk count exceeds ``chunk_count_threshold`` AND the
#   embedder supports it.
# * ``chunk_count_threshold`` (default 1000) is THIS CONTRACT's own pinned
#   default — small enough that a real multi-hundred-file project sweep
#   trips it, large enough that a single-file watcher-triggered reconcile
#   (which stays realtime regardless of mode — see
#   ``test_indexer_bulk_sweep.py``) never accidentally qualifies.
# * ``poll_interval_s`` defaults to loresigil's OWN
#   ``DEFAULT_POLL_INTERVAL_S`` (never a hand-copied ``30.0`` literal here —
#   clause 5: the SAME source of truth the Voyage batch client itself uses).


class TestEmbeddingBatchConfig:
    """The ``embedding.batch`` sweep-level batch-embedding config seam."""

    def test_batch_defaults_when_block_is_absent(self) -> None:
        # Every existing lore.yaml (no ``batch:`` sub-block) must keep
        # validating and transparently get the documented defaults.
        from loresigil.voyage_batch import DEFAULT_POLL_INTERVAL_S

        payload = _deep_copy_config()
        assert "batch" not in payload["embedding"]
        config = LoreConfig.model_validate(payload)
        assert config.embedding.batch.mode == "auto"
        assert config.embedding.batch.chunk_count_threshold == 1000
        assert config.embedding.batch.poll_interval_s == DEFAULT_POLL_INTERVAL_S

    def test_batch_poll_interval_default_is_read_from_the_shared_voyage_constant(
        self,
    ) -> None:
        # Independent-of-any-hand-copied-literal pin: if loresigil's own
        # default ever changes, this contract's default must track it rather
        # than silently drifting to a stale hardcoded number.
        from loresigil.voyage_batch import DEFAULT_POLL_INTERVAL_S

        assert DEFAULT_POLL_INTERVAL_S == pytest.approx(30.0)  # sanity: the real value
        payload = _deep_copy_config()
        config = LoreConfig.model_validate(payload)
        assert config.embedding.batch.poll_interval_s == DEFAULT_POLL_INTERVAL_S

    def test_batch_block_is_parsed_when_explicitly_present(self) -> None:
        payload = _deep_copy_config()
        payload["embedding"]["batch"] = {
            "mode": "batch",
            "chunk_count_threshold": 500,
            "poll_interval_s": 45.0,
        }
        config = LoreConfig.model_validate(payload)
        assert config.embedding.batch.mode == "batch"
        assert config.embedding.batch.chunk_count_threshold == 500
        assert config.embedding.batch.poll_interval_s == 45.0

    @pytest.mark.parametrize("mode", ["realtime", "batch", "auto"])
    def test_batch_mode_accepts_every_documented_literal(self, mode: str) -> None:
        payload = _deep_copy_config()
        payload["embedding"]["batch"] = {"mode": mode}
        config = LoreConfig.model_validate(payload)
        assert config.embedding.batch.mode == mode

    def test_batch_mode_rejects_unknown_literal(self) -> None:
        payload = _deep_copy_config()
        payload["embedding"]["batch"] = {"mode": "sometimes"}
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_batch_chunk_count_threshold_rejects_zero(self) -> None:
        payload = _deep_copy_config()
        payload["embedding"]["batch"] = {"chunk_count_threshold": 0}
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_batch_chunk_count_threshold_rejects_negative(self) -> None:
        payload = _deep_copy_config()
        payload["embedding"]["batch"] = {"chunk_count_threshold": -50}
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_batch_block_rejects_extra_field(self) -> None:
        # A known section stays strict: a typo'd key inside ``batch`` fails loud
        # (mirrors TestLoggingConfig's identical pin on its own sub-section).
        payload = _deep_copy_config()
        payload["embedding"]["batch"] = {"mode": "auto", "chunck_count_threshold": 10}
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_adding_batch_block_does_not_weaken_embedding_strictness(self) -> None:
        # Regression guard (mirrors TestLoggingConfig's identical top-level
        # pin): making ``batch`` an optional defaulted field must NOT loosen
        # ``extra="forbid"`` on the surrounding ``embedding`` section itself —
        # an unrelated typo'd embedding key is still rejected.
        payload = _deep_copy_config()
        payload["embedding"]["batch"] = {"mode": "auto"}
        payload["embedding"]["bacth"] = {"mode": "auto"}  # the realistic typo
        with pytest.raises(ValidationError):
            LoreConfig.model_validate(payload)

    def test_batch_config_class_is_named_and_importable(self) -> None:
        # Mirrors the sibling-section naming convention already established
        # for every OPTIONAL-with-default sub-section on LoreConfig
        # (LoggingConfig, SurrealConfig, WatcherConfig, AuthConfig) —
        # imported inside the test body (not at module scope)
        # so a not-yet-existing symbol fails ONLY this one test, not the
        # whole file's collection.
        from loremaster.config import BatchConfig

        payload = _deep_copy_config()
        config = LoreConfig.model_validate(payload)
        assert isinstance(config.embedding.batch, BatchConfig)


# ---------------------------------------------------------------------------
# P8c — the REQUIRED Anthropic block + fail-fast key resolution
# ---------------------------------------------------------------------------
#
# ``LoreConfig`` gains a REQUIRED ``anthropic`` section (NO default — unlike the
# optional-with-default ``logging`` / ``surreal`` / ``search`` blocks). It
# carries the token-calibration probe configuration:
#
#   class AnthropicConfig(_StrictModel):
#       api_key_env: str                        # REQUIRED — env-var NAME only
#       yardstick_model: str = "claude-sonnet-5"
#
#   class LoreConfig(_StrictModel):
#       ...
#       anthropic: AnthropicConfig              # REQUIRED — no default
#
# Two behaviours are pinned, blind to any implementation:
#
# 1. SCHEMA (via ``model_validate``): the block is REQUIRED (a config without it
#    fails, naming ``anthropic``); ``yardstick_model`` defaults to the pinned
#    ``claude-sonnet-5`` when omitted; a typo'd sub-key is rejected (strict).
# 2. FAIL-FAST (via ``load_config`` — the file-load boot seam): the key is
#    resolved EAGERLY at load. A missing OR empty env var aborts the load with a
#    ``ValueError`` naming BOTH the yaml field ``anthropic.api_key_env`` AND the
#    env-var name — never a lazy 401 at first probe. (``model_validate`` stays a
#    pure schema check: it does NOT touch the environment, mirroring how the TEI
#    / auth keys resolve lazily in their consumers today.)
#
# Secrets are referenced by env-var NAME only and set/unset by the tests
# themselves via monkeypatch — never a real key. A DEDICATED env-var name that
# the suite-wide conftest fixture does NOT set is used for the missing/empty
# cases so they stay independent of that fixture.
# ---------------------------------------------------------------------------

# The env-var NAME the happy-path Anthropic tests reference. A test-only name so
# a monkeypatch never clobbers a developer's real ``ANTHROPIC_API_KEY``.
_ANTHROPIC_KEY_ENV: str = "LORE_ANTHROPIC_KEY_TEST"

# A dedicated env-var NAME the tests keep UNSET/empty to exercise the fail-fast
# path. Distinct from the suite conftest's dummy ``ANTHROPIC_API_KEY`` so these
# cases never accidentally resolve against it.
_ANTHROPIC_ABSENT_ENV: str = "LORE_ANTHROPIC_KEY_ABSENT"

# The contract's pinned default yardstick model (SURVEY-FINAL / YARDSTICK-FINAL,
# 2026-07-04). Stated here as the SPEC the test verifies — NOT copied from the
# implementation (clause 2).
_EXPECTED_DEFAULT_YARDSTICK_MODEL: str = "claude-sonnet-5"


def _config_with_anthropic(
    api_key_env: str = _ANTHROPIC_KEY_ENV, **block_overrides: Any
) -> dict[str, Any]:
    """A canonical config payload carrying an ``anthropic`` block.

    Built by overwriting the canonical config's ``anthropic`` key so the test is
    order-independent: it works whether or not ``_CANONICAL_CONFIG`` itself
    already carries the block. ``block_overrides`` inject extra/typo'd keys.
    """
    payload = _deep_copy_config()
    block: dict[str, Any] = {"api_key_env": api_key_env}
    block.update(block_overrides)
    payload["anthropic"] = block
    return payload


class TestAnthropicConfigSchema:
    """The REQUIRED ``anthropic`` block's schema behaviour (via ``model_validate``)."""

    def test_valid_block_is_parsed(self) -> None:
        config = LoreConfig.model_validate(_config_with_anthropic())
        assert config.anthropic.api_key_env == _ANTHROPIC_KEY_ENV

    def test_yardstick_model_defaults_to_the_pinned_baseline(self) -> None:
        # Omitting ``yardstick_model`` yields the generation-anchored default.
        config = LoreConfig.model_validate(_config_with_anthropic())
        assert config.anthropic.yardstick_model == _EXPECTED_DEFAULT_YARDSTICK_MODEL

    def test_yardstick_model_is_preserved_when_set(self) -> None:
        payload = _config_with_anthropic(yardstick_model="claude-opus-4-8")
        config = LoreConfig.model_validate(payload)
        assert config.anthropic.yardstick_model == "claude-opus-4-8"

    def test_missing_block_fails_naming_the_field(self) -> None:
        # The block is REQUIRED (no default): a config without it must fail load,
        # and the error must name ``anthropic`` so the operator knows what to add.
        payload = _deep_copy_config()
        payload.pop("anthropic", None)
        with pytest.raises(ValidationError) as excinfo:
            LoreConfig.model_validate(payload)
        assert "anthropic" in str(excinfo.value)

    def test_block_rejects_unknown_sub_key(self) -> None:
        # A known section stays strict (``extra="forbid"``): a typo'd key INSIDE
        # the block fails loud and NAMES the offending key. Asserting the key
        # name makes this red-for-the-right-reason before the field exists (a
        # bare ``pytest.raises`` would spuriously catch the "extra top-level
        # ``anthropic``" error the strict base raises pre-implementation).
        payload = _config_with_anthropic(bogus_sub_key=True)
        with pytest.raises(ValidationError) as excinfo:
            LoreConfig.model_validate(payload)
        assert "bogus_sub_key" in str(excinfo.value)

    def test_missing_api_key_env_within_block_is_rejected(self) -> None:
        # ``api_key_env`` itself is REQUIRED inside the block — an ``anthropic``
        # block that omits it must fail (a keyless block is un-resolvable). The
        # error must NAME ``api_key_env``: at RED the strict base rejects the
        # whole block (echoing only the keys present, which do NOT include
        # ``api_key_env``), so this assertion is red-for-the-right-reason.
        payload = _deep_copy_config()
        payload["anthropic"] = {"yardstick_model": "claude-sonnet-5"}
        with pytest.raises(ValidationError) as excinfo:
            LoreConfig.model_validate(payload)
        assert "api_key_env" in str(excinfo.value)

    def test_anthropic_config_class_is_named_and_importable(self) -> None:
        # Mirrors the sibling-section naming convention (LoggingConfig,
        # SurrealConfig, BatchConfig): imported inside the test body so a
        # not-yet-existing symbol fails ONLY this test, not the file's collection.
        from loremaster.config import AnthropicConfig

        config = LoreConfig.model_validate(_config_with_anthropic())
        assert isinstance(config.anthropic, AnthropicConfig)

    def test_model_validate_does_not_touch_the_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Pure schema construction must NOT resolve the secret — only the
        # ``load_config`` boot seam does (mirroring the lazy TEI/auth idiom). An
        # UNSET key must still let ``model_validate`` succeed.
        monkeypatch.delenv(_ANTHROPIC_ABSENT_ENV, raising=False)
        config = LoreConfig.model_validate(
            _config_with_anthropic(api_key_env=_ANTHROPIC_ABSENT_ENV)
        )
        assert config.anthropic.api_key_env == _ANTHROPIC_ABSENT_ENV


class TestAnthropicFailFast:
    """``load_config`` resolves the Anthropic key EAGERLY and fails loud at boot."""

    def _write_config(self, tmp_path: Path, payload: dict[str, Any]) -> Path:
        config_path = tmp_path / "lore.yaml"
        config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
        return config_path

    def test_loads_when_env_var_is_set(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(_ANTHROPIC_KEY_ENV, "sk-ant-dummy-value")
        config_path = self._write_config(tmp_path, _config_with_anthropic())
        config = load_config(config_path)
        assert config.anthropic.api_key_env == _ANTHROPIC_KEY_ENV

    def test_unset_env_var_fails_load_naming_field_and_var(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv(_ANTHROPIC_ABSENT_ENV, raising=False)
        payload = _config_with_anthropic(api_key_env=_ANTHROPIC_ABSENT_ENV)
        config_path = self._write_config(tmp_path, payload)
        with pytest.raises(ValueError) as excinfo:
            load_config(config_path)
        message = str(excinfo.value)
        # The error must name BOTH the yaml field (contiguously — the strict
        # base's pre-implementation "extra key" error cannot produce this exact
        # substring, so the assertion is red-for-the-right-reason) AND the env var.
        assert "anthropic.api_key_env" in message
        assert _ANTHROPIC_ABSENT_ENV in message

    def test_empty_env_var_fails_load_naming_field_and_var(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # An empty string is effectively a missing key (resolve_secret's own
        # contract) — it must fail the SAME way as unset.
        monkeypatch.setenv(_ANTHROPIC_ABSENT_ENV, "")
        payload = _config_with_anthropic(api_key_env=_ANTHROPIC_ABSENT_ENV)
        config_path = self._write_config(tmp_path, payload)
        with pytest.raises(ValueError) as excinfo:
            load_config(config_path)
        message = str(excinfo.value)
        assert "anthropic.api_key_env" in message
        assert _ANTHROPIC_ABSENT_ENV in message

    def test_whitespace_only_env_var_fails_load_naming_field_and_var(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A whitespace-only value is effectively a missing key too — it must
        # fail the SAME way as unset/empty, not slip through to a later,
        # confusing failure at the API call.
        monkeypatch.setenv(_ANTHROPIC_ABSENT_ENV, "   ")
        payload = _config_with_anthropic(api_key_env=_ANTHROPIC_ABSENT_ENV)
        config_path = self._write_config(tmp_path, payload)
        with pytest.raises(ValueError) as excinfo:
            load_config(config_path)
        message = str(excinfo.value)
        assert "anthropic.api_key_env" in message
        assert _ANTHROPIC_ABSENT_ENV in message

    def test_fail_fast_error_chains_from_the_original_keyerror(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The ValueError is raised ``from`` resolve_secret's KeyError so the
        # operator sees the underlying cause in the traceback.
        monkeypatch.delenv(_ANTHROPIC_ABSENT_ENV, raising=False)
        payload = _config_with_anthropic(api_key_env=_ANTHROPIC_ABSENT_ENV)
        config_path = self._write_config(tmp_path, payload)
        with pytest.raises(ValueError) as excinfo:
            load_config(config_path)
        assert isinstance(excinfo.value.__cause__, KeyError)
