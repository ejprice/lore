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
    "qdrant": {
        "url": "http://127.0.0.1:16333",
        "api_key_env": "QDRANT__SERVICE__API_KEY",
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
        assert config.qdrant.url == "http://127.0.0.1:16333"
        assert config.qdrant.api_key_env == "QDRANT__SERVICE__API_KEY"
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

    def test_rejects_extra_qdrant_field(self) -> None:
        payload = _deep_copy_config()
        payload["qdrant"]["timeout"] = 5
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


# ---------------------------------------------------------------------------
# FIX 1 — ProjectConfig.slug must be constrained to a safe charset
# ---------------------------------------------------------------------------
#
# ``ProjectConfig.slug`` is the single value that drives BOTH the ``lore_<slug>``
# Qdrant collection name AND the on-disk state paths the server constructs:
# ``_DEFAULT_MANIFEST_DIR / f"{slug}.db"`` / ``f"{slug}.memory.db"`` /
# ``f"{slug}.graph.db"`` (server.py ~2022-2023, _DEFAULT_MANIFEST_DIR ~2954).
#
# Today the field is a bare ``str`` — unconstrained. An operator typo or a
# malicious config could put path-traversal (``../etc``), a separator (``a/b``),
# whitespace (``Has Space``), uppercase (``UPPER``), an empty string, or a
# leading separator (``-leading``) into the slug. Because the slug is f-string'd
# straight into a filesystem path, ``../etc`` would relocate the state DBs OUTSIDE
# the state dir, and a separator could collide / escape the collection namespace.
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
# test verifies — NOT copied from the implementation (which does not yet exist).
# Lowercase alnum + ``-``/``_``, must start with an alnum, non-empty.
_SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_-]*$"

# VALID slugs that MUST be accepted. Grounded in real lore deployments: ``lore``
# (this repo's own slug), ``demand_intelligence`` (the canonical config above),
# and a hyphen+underscore+digit mix proving the full permitted charset parses.
_VALID_SLUGS: tuple[str, ...] = (
    "lore",
    "demand_intelligence",
    "my-proj_2",
)

# INVALID slugs that MUST raise at load. Each is a realistic operator-typo or
# attack input, annotated with the failure mode it exercises (the adversarial
# pre-flight, encoded as data so every entry is a case, not a comment).
_INVALID_SLUGS: dict[str, str] = {
    "../etc": "path traversal — escapes the state dir, relocates the DBs",
    "a/b": "embedded separator — escapes the slug into a subpath / collection",
    "Has Space": "whitespace + a space — not a safe filename / collection token",
    "UPPER": "uppercase — Qdrant collection names and the convention are lowercase",
    "": "empty — yields a bare '.db' path and an 'lore_' collection",
    "-leading": "leading separator — must start with an alphanumeric",
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
    """FIX 1: ``ProjectConfig.slug`` is constrained to a safe ``[a-z0-9_-]`` charset.

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
