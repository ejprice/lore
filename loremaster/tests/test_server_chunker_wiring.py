"""Contract tests for the boot-time ``config.chunkers`` → ``ChunkerRegistry`` wiring.

Operator-ruled 2026-07-05 ("wire it for real"), resolving the #13 config-dynamism
table's "fingerprint-vs-selection lie": ``config.chunkers`` (the ``lore.yaml`` map
of *file extension → inner mapping carrying a ``chunker:`` key naming a registered
chunker*) already folds into the embedding-schema fingerprint (``index/schema.py``)
— so editing it triggers a rebuild — but it did NOT actually route extensions to
chunkers. Editing the block changed the fingerprint yet changed no behaviour: a
lie. This contract pins the fix: at :class:`~loremaster.server.LoreServer`
construction, right after ``_build_default_registry()``, the config block is
projected onto the registry's existing ``apply_overrides`` seam so the yaml block
genuinely routes extensions to chunkers.

This is the SERVER-BOOT WIRING layer. The registry's own routing/override/atomicity
guarantees are pinned by ``lorescribe/tests/test_registry.py`` and are NOT
duplicated here — this file exercises only what the *wiring* adds: the projection
from the inner mappings, the loud failure translation, boot ordering, degenerate
inputs, and fingerprint-fold neutrality.

Ruled decisions (each written so an operator can approve or strike it):

* **R3 — extra inner keys are TOLERATED and IGNORED (permissive-ignore).**
  OPERATOR-RULED 2026-07-05 (permissive-ignore, not strict-reject). The wiring
  reads ONLY ``inner["chunker"]``; any additional inner keys (e.g. DI's live
  ``dialect: postgres`` on its ``.sql`` entry) are silently ignored, so
  construction succeeds and DI's live yaml stays UNTOUCHED (no coordinated edit).
  ``chunker`` itself remains REQUIRED (R2): its absence still fails loudly.
  **Accepted residual:** a decorative extra key is inert for routing yet still
  folds into the embedding-schema fingerprint (``index/schema.py:133`` folds the
  whole ``chunkers`` mapping), so editing one still triggers the existing
  automatic full rebuild — an accepted cost of leaving the block permissive, not
  a lie the wiring must police. Pinned by
  :class:`TestChunkerConfigWiringExtraKeysIgnored`.

* **R5 — walk-gating seam SCOPED OUT (boundary pinned).** The re-route is a
  *dispatch-routing* change only. Whether a re-routed extension's files are ever
  presented to ``dispatch_file`` is the Indexer's walk responsibility
  (``index/indexer.py:443`` applies ``config.include``/``exclude`` BEFORE dispatch)
  and is tested in the indexer suite — OUT of this contract's scope. What IS pinned
  here is the boundary: the wiring must not silently widen ``config.include`` (a
  re-routed ``.yaml`` NOT in ``include`` stays gated out by the walk).

* **R7 — extension-chunker keys DEFERRED.** The wiring runs in ``__init__``, BEFORE
  any ``register_extension`` (which has no production caller). Only the default
  base + profile chunker keys exist at that point, so an override naming an
  extension-namespaced key (e.g. ``odoo:OdooXmlChunker``) is rejected via the same
  R1 unregistered-key path. Extension-contributed chunkers at boot are out of scope.

* **R6 — fingerprint reconciliation (noted for operator review).** An *edited*
  ``chunkers`` block already flips the fingerprint (pinned by
  ``test_schema_rebuild.py::TestFingerprintSensitivity`` —
  ``test_chunkers_change_flips_fingerprint`` / ``..._within_extension_...``), which
  triggers the EXISTING automatic full rebuild (reason ``fingerprint_mismatch``).
  Per the prior operator ruling that this auto-rebuild is intentional, this contract
  does NOT invent new opt-in machinery; it deviates knowingly from the #13 hazard
  row's "gate behind explicit operator opt-in" language and reconciles by reusing
  the existing announce surface (schema_rebuild status + rebuilding_notice). This
  file therefore pins only the OTHER direction: the wiring itself is fold-neutral
  (an unedited config yields an unchanged fingerprint, and the wiring never mutates
  ``config.chunkers`` in place).
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml
from _extension_helpers import minimal_config
from loremaster.config import LoreConfig
from loremaster.index.schema import embedding_schema_fingerprint

# ``_BASE_CHUNKER_SUFFIXES`` is the SAME source of truth production registers its
# default chunkers from (server.py). Importing it — rather than hand-copying the
# key names — means a production rename of a default chunker key cannot leave these
# fixtures silently pointing at a stale key (clause 5). ``LoreServer`` is the unit
# under test; the wiring being contracted lives in its ``__init__``.
from loremaster.server import _BASE_CHUNKER_SUFFIXES, LoreServer
from lorescribe.markdown import MarkdownChunker
from lorescribe.models import ChunkContext
from lorescribe.python_ast import PythonAstChunker
from lorescribe.sql import SqlChunker
from lorescribe.text import TextChunker

# --------------------------------------------------------------------------- #
# Shared domain conventions — the override-target keys are the ACTUAL keys the
# production registry registers (server._BASE_CHUNKER_SUFFIXES), never invented
# strings. ``TestFixtureIntegrity`` pins these against that source of truth so a
# rename trips a test, not a silently-inert fixture.
# --------------------------------------------------------------------------- #
PYTHON_AST_CHUNKER_KEY = "python_ast"
MARKDOWN_CHUNKER_KEY = "markdown"
TEXT_CHUNKER_KEY = "text"
SQL_CHUNKER_KEY = "sql"

# The yaml field name the loud failure must cite (the operator's fix target).
CHUNKERS_YAML_FIELD = "chunkers"
# The required inner key the wiring projects the override VALUE from.
CHUNKER_INNER_KEY = "chunker"

# Real live-yaml shapes used as fixture material (owner directive: real yaml
# shapes, not invented toys). The lore repo's own ``lore.yaml`` block is a pair of
# behaviour-neutral IDENTITY mappings; DI's live intent is a genuine re-route of
# ``.yaml`` to the plain-text chunker plus a ``.sql`` entry.
LIVE_LORE_IDENTITY_CHUNKERS: dict[str, dict[str, object]] = {
    ".py": {CHUNKER_INNER_KEY: PYTHON_AST_CHUNKER_KEY},
    ".md": {CHUNKER_INNER_KEY: MARKDOWN_CHUNKER_KEY},
}
# DI's live ``chunkers`` block VERBATIM (demand_intelligence/lore.yaml): the ``.sql``
# entry carries the decorative ``dialect: postgres`` key, which R3 (permissive-ignore)
# tolerates — DI's yaml is used unedited. Exercising the true live shape means the
# reroute / no-mutation / fold-neutral tests test exactly what the operator ships.
LIVE_DI_CHUNKERS: dict[str, dict[str, object]] = {
    ".py": {CHUNKER_INNER_KEY: PYTHON_AST_CHUNKER_KEY},
    ".md": {CHUNKER_INNER_KEY: MARKDOWN_CHUNKER_KEY},
    ".sql": {CHUNKER_INNER_KEY: SQL_CHUNKER_KEY, "dialect": "postgres"},
    ".yaml": {CHUNKER_INNER_KEY: TEXT_CHUNKER_KEY},
}
# DI's live ``.sql`` entry verbatim — carries the decorative ``dialect: postgres``
# key R3 (permissive-ignore) tolerates (verbatim from demand_intelligence/lore.yaml).
LIVE_DI_SQL_WITH_DIALECT: dict[str, dict[str, object]] = {
    ".sql": {CHUNKER_INNER_KEY: SQL_CHUNKER_KEY, "dialect": "postgres"},
}

# Realistic source material for the routing oracles. Real-ish code/docs/SQL/yaml,
# never ``x = 1`` toys; the ``.yaml`` source (below) is representative multi-key
# fleet-config yaml so the re-route test dispatches genuine yaml content.
PYTHON_SOURCE = (
    "import logging\n"
    "\n"
    "logger = logging.getLogger(__name__)\n"
    "\n"
    "\n"
    "def post_payroll(run_id: int) -> bool:\n"
    '    logger.info("posting payroll run %s", run_id)\n'
    "    return run_id > 0\n"
)
MARKDOWN_SOURCE = (
    "# Payroll\n"
    "\n"
    "Direct deposit posts on the second business day.\n"
    "\n"
    "## Cutoff\n"
    "\n"
    "Submit before 17:00 CST.\n"
)
SQL_SOURCE = (
    "CREATE TABLE payroll_run (\n"
    "    id           bigint PRIMARY KEY,\n"
    "    posted_at    timestamptz NOT NULL,\n"
    "    total_cents  bigint NOT NULL\n"
    ");\n"
)

# A representative ``.yaml`` source the re-route routes through the text chunker.
# Inlined (NOT read from the gitignored ``lore.yaml``) so the module collects on a
# fresh clone / CI runner where that file is absent. Shaped like DI's fleet-config
# YAML: nested mappings, a list, and a comment — genuine multi-key yaml, not a toy.
YAML_SOURCE = (
    "# fleet configuration for the demand-intelligence forecaster\n"
    "fleet:\n"
    "  region: us-central\n"
    "  vehicles:\n"
    "    - id: TRK-4417\n"
    "      axles: 5\n"
    "      max_gross_kg: 36287\n"
    "    - id: TRK-4418\n"
    "      axles: 6\n"
    "      max_gross_kg: 41730\n"
    "horizon:\n"
    "  weeks: 26\n"
    "  anchor: monday\n"
)

# Realistic on-disk paths for dispatch (the extension is what selects the chunker).
PY_DISPATCH_PATH = "loremaster/loremaster/payroll.py"
MD_DISPATCH_PATH = "docs/payroll.md"
SQL_DISPATCH_PATH = "migrations/0007_payroll_run.sql"
YAML_DISPATCH_PATH = "demand/config/fleet.yaml"  # DI's real re-route locus


def _count_tokens(text: str) -> int:
    """A cheap per-string token estimate for the dispatch :class:`ChunkContext`."""
    return max(1, len(text) // 4)


def _chunk_context(file_path: str) -> ChunkContext:
    """Build a :class:`ChunkContext` for driving dispatch over a source string.

    Mirrors ``test_server._chunk_context`` so the injected token counter and cap
    match the rest of the loremaster suite's dispatch idiom.
    """
    return ChunkContext(
        slug="lore_ext_test",
        file_path=file_path,
        count_tokens=_count_tokens,
        max_input_tokens=8192,
    )


def _config_with_chunkers(chunkers: dict[str, dict[str, object]]) -> LoreConfig:
    """Derive a valid :class:`LoreConfig` from the production test builder, swapping ``chunkers``.

    Built by re-using ``_extension_helpers.minimal_config`` — the shared, production
    test builder — and overriding ONLY the ``chunkers`` block, so every other field
    stays production-realistic and there is a single source of truth for the config
    shape (clause 1 + clause 5). The result is re-validated through ``LoreConfig`` so
    it is genuinely schema-valid, exactly as a parsed ``lore.yaml`` would be.
    """
    payload = minimal_config().model_dump(mode="json")
    payload[CHUNKERS_YAML_FIELD] = chunkers
    return LoreConfig.model_validate(payload)


def _boot_from_yaml(chunkers: dict[str, dict[str, object]], tmp_path: Path) -> LoreServer:
    """Write a ``lore.yaml`` carrying ``chunkers`` and boot through the FULL seam.

    Exercises the real producer→consumer handoff: yaml text → ``yaml.safe_load`` →
    ``LoreConfig`` → ``LoreServer.from_config`` → ``__init__`` → the wiring →
    ``ChunkerRegistry.apply_overrides``. This is how an operator actually triggers
    the wiring, so the loud-failure tests boot through it too.
    """
    config = _config_with_chunkers(chunkers)
    path = tmp_path / "lore.yaml"
    path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    return LoreServer.from_config(path)


class TestFixtureIntegrity:
    """The fixtures' override-target keys ARE the keys production registers.

    A drift guard: if a default chunker key is renamed in production
    (``server._BASE_CHUNKER_SUFFIXES``) but not here, these routing tests would
    silently start exercising a stale key. This test fails loudly instead.
    """

    def test_override_target_keys_are_registered_default_chunkers(self) -> None:
        # Every key these fixtures re-route TO must be a real default chunker key.
        fixture_keys = {
            PYTHON_AST_CHUNKER_KEY,
            MARKDOWN_CHUNKER_KEY,
            TEXT_CHUNKER_KEY,
            SQL_CHUNKER_KEY,
        }
        assert fixture_keys <= set(_BASE_CHUNKER_SUFFIXES), (
            "fixture chunker keys drifted from the production default registry keys"
        )


class TestChunkerConfigWiringIdentity:
    """R4 — identity mappings (``.py→python_ast`` / ``.md→markdown``) are behaviour-neutral.

    The live ``lore.yaml`` block re-states the defaults. Applying it must leave
    dispatch for those extensions IDENTICAL to the default registration. These are
    green both before and after the wiring exists (identity is neutral by
    definition); their contract value is a regression / MIS-route guard — a wiring
    that read the wrong inner key or re-routed ``.py`` elsewhere breaks them. The
    override targets (``python_ast``/``markdown``) also only exist AFTER
    ``_build_default_registry()``, so a clean boot here doubles as proof the wiring
    runs after the defaults are registered.
    """

    def test_identity_py_mapping_dispatches_python_ast_output(self, tmp_path: Path) -> None:
        # Arrange: boot with the live lore.yaml identity block.
        server = _boot_from_yaml(LIVE_LORE_IDENTITY_CHUNKERS, tmp_path)
        ctx = _chunk_context(PY_DISPATCH_PATH)
        # Independent oracle: the python_ast chunker's OWN output for this source —
        # NOT a re-run of dispatch. Identity routing must reproduce it exactly.
        expected = PythonAstChunker().chunk(PYTHON_SOURCE, ctx)
        # Act
        chunks = server.registry.dispatch_file(PY_DISPATCH_PATH, PYTHON_SOURCE, ctx)
        # Assert: behaviour-neutral — the .py→python_ast identity dispatches exactly
        # as the python_ast chunker would; a mis-route yields different chunks.
        assert chunks == expected
        assert chunks, "identity .py mapping must still produce python_ast chunks"

    def test_identity_md_mapping_dispatches_markdown_output(self, tmp_path: Path) -> None:
        server = _boot_from_yaml(LIVE_LORE_IDENTITY_CHUNKERS, tmp_path)
        ctx = _chunk_context(MD_DISPATCH_PATH)
        expected = MarkdownChunker().chunk(MARKDOWN_SOURCE, ctx)
        chunks = server.registry.dispatch_file(MD_DISPATCH_PATH, MARKDOWN_SOURCE, ctx)
        assert chunks == expected
        assert chunks, "identity .md mapping must still produce markdown chunks"


class TestChunkerConfigWiringReroute:
    """R5 — a genuine re-route (``.yaml→text``) routes yaml content through the text chunker.

    DI's live intent: index fleet-config YAML through the plain-text chunker. The
    wiring must make ``dispatch_file`` on a ``.yaml`` path select the ``text``
    chunker — the extension the bare registry does not otherwise claim (it would
    return ``[]``). The walk-gating seam (whether a ``.yaml`` file is ever presented
    to dispatch) is SCOPED OUT to the indexer suite; the boundary is pinned here:
    the wiring must not widen ``config.include``.
    """

    def test_yaml_reroutes_to_text_chunker(self, tmp_path: Path) -> None:
        # Arrange: DI's live re-route intent.
        server = _boot_from_yaml(LIVE_DI_CHUNKERS, tmp_path)
        ctx = _chunk_context(YAML_DISPATCH_PATH)
        # Independent oracle: the text chunker's own output for genuine yaml source.
        expected = TextChunker().chunk(YAML_SOURCE, ctx)
        # Act: a .yaml path the bare registry would return [] for.
        chunks = server.registry.dispatch_file(YAML_DISPATCH_PATH, YAML_SOURCE, ctx)
        # Assert: non-empty (sanity bound — a mis-wire yields the silent [] class) and
        # exactly the text chunker's output; if the projection read the wrong inner
        # key, .yaml would not route to text and this fails.
        assert chunks, "re-routed .yaml must produce chunks, not the silent empty list"
        assert chunks == expected
        assert all(chunk.chunk_type == "text" for chunk in chunks)

    def test_reroute_targets_the_key_named_in_the_chunker_inner_field(self, tmp_path: Path) -> None:
        # A re-route to the SQL chunker proves the projection reads ``inner["chunker"]``
        # (the value, "sql"), not some other inner field. A .sql path is claimed by
        # the default sql chunker anyway, so instead assert an UNAMBIGUOUS re-route:
        # send .yaml to sql and confirm it produces sql_statement chunks for SQL text.
        server = _boot_from_yaml({".yaml": {CHUNKER_INNER_KEY: SQL_CHUNKER_KEY}}, tmp_path)
        ctx = _chunk_context(YAML_DISPATCH_PATH)
        expected = SqlChunker().chunk(SQL_SOURCE, ctx)
        chunks = server.registry.dispatch_file(YAML_DISPATCH_PATH, SQL_SOURCE, ctx)
        assert chunks, "re-route to the named chunker key must produce chunks"
        assert chunks == expected

    def test_reroute_does_not_widen_config_include(self, tmp_path: Path) -> None:
        # R5 boundary (walk-gating scoped out): the wiring is dispatch-routing ONLY.
        # Re-routing .yaml must NOT silently add a yaml glob to config.include — a
        # .yaml file not matched by include stays gated out by the indexer walk.
        include_before = list(minimal_config().include)  # the production builder's include
        server = _boot_from_yaml(LIVE_DI_CHUNKERS, tmp_path)
        # The wiring re-routed .yaml but must leave the walk's include untouched.
        assert server.config.include == include_before
        assert not any("yaml" in pattern for pattern in server.config.include), (
            "the chunker re-route must not widen include patterns to pull in .yaml files"
        )


class TestChunkerConfigWiringUnregisteredKey:
    """R1 — an override targeting an unregistered chunker key fails construction LOUDLY.

    The registry raises ``KeyError`` on an unknown target; the wiring must WRAP it as
    a ``ValueError`` naming the yaml field and the offending extension→key (precedent:
    ``load_config``'s eager-key check, ``config.py:620-624``; the nit-1 guard in
    ``LoreServer._register_extension_chunker``). The registry's all-or-nothing atomicity ("nothing applied on
    any invalid key") is already pinned at the registry level and is inherited so long
    as the wiring passes the whole projected batch to ``apply_overrides`` in ONE call.
    """

    def test_unregistered_chunker_key_raises_value_error_naming_field_and_offender(
        self, tmp_path: Path
    ) -> None:
        # Arrange / Act / Assert: a typo'd chunker name is a config error surfaced
        # eagerly at boot, not a silent file-drop later. ``pytest.raises(ValueError)``
        # ALSO pins the wrap itself: it fails both if the registry's raw KeyError
        # propagates unwrapped (KeyError is not a ValueError) and if the wiring
        # swallows it (construction would then raise nothing, and the `with` block
        # would fail with "DID NOT RAISE") — REFACTOR de-bloat 2026-07-05 folded a
        # narrower ``..._is_a_value_error_not_a_bare_keyerror`` test into this one
        # after confirming (by transiently breaking each failure mode) that this
        # assertion alone already catches both.
        with pytest.raises(ValueError) as exc_info:
            _boot_from_yaml({".foo": {CHUNKER_INNER_KEY: "no_such_chunker"}}, tmp_path)
        message = str(exc_info.value)
        # The message must name the yaml field the operator edits, the offending
        # extension, and the offending key — so the fix is a one-step edit.
        assert CHUNKERS_YAML_FIELD in message
        assert ".foo" in message
        assert "no_such_chunker" in message

    def test_mixed_valid_and_invalid_batch_raises_naming_the_invalid_entry(
        self, tmp_path: Path
    ) -> None:
        # A realistic multi-entry block (configs ship many overrides at once) where a
        # VALID entry precedes the invalid one. The wiring must not stop at the valid
        # entry and skip validation of the rest; the loud failure must name the
        # INVALID entry. Registry atomicity (none-applied) is inherited from the
        # registry's own tested guarantee and not re-asserted here.
        batch: dict[str, dict[str, object]] = {
            ".yaml": {CHUNKER_INNER_KEY: TEXT_CHUNKER_KEY},  # valid, comes first
            ".foo": {CHUNKER_INNER_KEY: "no_such_chunker"},  # invalid, must be caught
        }
        with pytest.raises(ValueError) as exc_info:
            _boot_from_yaml(batch, tmp_path)
        message = str(exc_info.value)
        assert ".foo" in message
        assert "no_such_chunker" in message

    def test_extension_namespaced_key_is_rejected_at_boot(self, tmp_path: Path) -> None:
        # R7 deferral: the wiring runs in __init__, BEFORE any register_extension, so
        # only the default base/profile chunker keys exist. An override naming an
        # extension-namespaced key (the "ext:ClassName" convention) is therefore
        # unregistered at boot and rejected via the same loud path — extension
        # chunkers at boot are explicitly out of scope.
        with pytest.raises(ValueError) as exc_info:
            _boot_from_yaml({".xml": {CHUNKER_INNER_KEY: "odoo:OdooXmlChunker"}}, tmp_path)
        assert "odoo:OdooXmlChunker" in str(exc_info.value)

    def test_non_string_chunker_value_is_rejected_loudly(self, tmp_path: Path) -> None:
        # AUDIT FINDING 3 (2026-07-05): a NON-STRING ``chunker:`` value (a yaml typo
        # -- a bare number where a quoted chunker name belongs) is UNPINNED today: it
        # happens to fail loudly only because ``123`` is never a registered chunker
        # key, so it falls through this SAME unregistered-key path as a typo'd
        # string (the projection performs no type check of its own). This freezes
        # the LOUD-FAILURE BEHAVIOUR, not the specific path: construction must keep
        # raising a ValueError naming the yaml field and the offending extension,
        # whatever path a future implementation routes it through.
        with pytest.raises(ValueError) as exc_info:
            _boot_from_yaml({".yaml": {CHUNKER_INNER_KEY: 123}}, tmp_path)
        message = str(exc_info.value)
        assert CHUNKERS_YAML_FIELD in message
        assert ".yaml" in message


class TestChunkerConfigWiringMissingChunkerKey:
    """R2 — an inner mapping MISSING the ``chunker`` key fails LOUDLY, naming the extension.

    The wiring projects ``{ext: inner["chunker"]}``. An inner mapping with no
    ``chunker`` key (e.g. an operator who wrote the options but forgot the chunker
    name) must raise a ``ValueError`` that names the extension AND the required key —
    NOT a confusing downstream "None is unregistered" error, and NOT a silent skip.
    """

    def test_inner_mapping_without_chunker_key_raises_naming_extension_and_key(
        self, tmp_path: Path
    ) -> None:
        # Arrange: an inner mapping with options but no ``chunker`` name.
        with pytest.raises(ValueError) as exc_info:
            _boot_from_yaml({".yaml": {"dialect": "postgres"}}, tmp_path)
        message = str(exc_info.value)
        # The message names the offending extension and the required key the operator
        # must add — distinct from R1's "unregistered key" wording. Assert the
        # repr-quoted form (``f"{CHUNKER_INNER_KEY!r}"`` -> ``'chunker'``, exactly
        # what the implementation emits) rather than a bare substring check: a bare
        # ``CHUNKER_INNER_KEY in message`` is ALSO satisfied by the yaml field name
        # ``"chunkers"`` (which contains "chunker" as a substring) even if the
        # required-key name were dropped from the message entirely. The quoted
        # field name ``'chunkers'`` does NOT contain the quoted key ``'chunker'`` as
        # a substring (the trailing "s" sits before the closing quote), so this
        # form can only be satisfied by the actual required-key mention.
        assert ".yaml" in message
        assert f"{CHUNKER_INNER_KEY!r}" in message


class TestChunkerConfigWiringExtraKeysIgnored:
    """R3 — PERMISSIVE-IGNORE: inner keys beyond ``chunker`` are tolerated and ignored.

    OPERATOR-RULED 2026-07-05 (permissive-ignore, not strict-reject). The wiring reads
    ONLY ``inner["chunker"]``; decorative extras (DI's live ``dialect: postgres``) are
    ignored, construction succeeds, and DI's live yaml stays untouched. ``chunker``
    stays REQUIRED — its absence still fails loudly (pinned by
    :class:`TestChunkerConfigWiringMissingChunkerKey`, R2). Accepted residual: a
    decorative key still folds into the fingerprint (``index/schema.py:133``), so
    editing one triggers the existing auto-rebuild — an accepted cost, not policed.
    """

    def test_live_di_sql_entry_with_extra_key_boots_and_routes(self, tmp_path: Path) -> None:
        # DI's live ``.sql`` entry VERBATIM (``dialect: postgres`` and all) must boot
        # cleanly and route .sql to the sql chunker — the extra key is ignored, not
        # rejected. Green-by-design: stays green under a correct permissive impl and
        # guards against a FUTURE over-rejecting implementation that would fail here.
        server = _boot_from_yaml(LIVE_DI_SQL_WITH_DIALECT, tmp_path)
        ctx = _chunk_context(SQL_DISPATCH_PATH)
        expected = SqlChunker().chunk(SQL_SOURCE, ctx)
        chunks = server.registry.dispatch_file(SQL_DISPATCH_PATH, SQL_SOURCE, ctx)
        assert chunks, "the .sql entry with an extra key must still produce sql chunks"
        assert chunks == expected

    def test_extra_key_is_ignored_on_a_genuine_reroute(self, tmp_path: Path) -> None:
        # The decisive permissive-ignore proof: a GENUINE re-route (``.yaml`` -> text)
        # carrying a decorative extra key must boot AND route .yaml through the text
        # chunker — the extra ``note`` key is ignored, only ``chunker`` is read. Red
        # pre-impl (dispatch returns [] for .yaml today); goes green once the wiring
        # applies the override while ignoring the extra key.
        server = _boot_from_yaml(
            {".yaml": {CHUNKER_INNER_KEY: TEXT_CHUNKER_KEY, "note": "fleet configs"}},
            tmp_path,
        )
        ctx = _chunk_context(YAML_DISPATCH_PATH)
        expected = TextChunker().chunk(YAML_SOURCE, ctx)
        chunks = server.registry.dispatch_file(YAML_DISPATCH_PATH, YAML_SOURCE, ctx)
        assert chunks, "re-route with an extra inner key must still produce text chunks"
        assert chunks == expected

    def test_sole_chunker_key_sql_entry_boots_and_routes(self, tmp_path: Path) -> None:
        # The plain sole-``chunker``-key form must construct cleanly and route .sql to
        # the sql chunker — the permissive path handles the no-extras case too.
        server = _boot_from_yaml({".sql": {CHUNKER_INNER_KEY: SQL_CHUNKER_KEY}}, tmp_path)
        ctx = _chunk_context(SQL_DISPATCH_PATH)
        expected = SqlChunker().chunk(SQL_SOURCE, ctx)
        chunks = server.registry.dispatch_file(SQL_DISPATCH_PATH, SQL_SOURCE, ctx)
        assert chunks, "the sole-chunker-key .sql entry must produce sql chunks"
        assert chunks == expected


class TestChunkerConfigWiringDegenerateAndOrdering:
    """Empty/boundary inputs, boot ordering, default preservation, and case-folding."""

    def test_empty_chunkers_block_is_a_noop_leaving_defaults_intact(self, tmp_path: Path) -> None:
        # ``chunkers`` is a REQUIRED field with no default (config.py), so ``{}`` is a
        # valid degenerate the wiring must treat as a no-op (apply_overrides({})): no
        # crash, defaults untouched. A .py file still routes to python_ast.
        server = _boot_from_yaml({}, tmp_path)
        ctx = _chunk_context(PY_DISPATCH_PATH)
        expected = PythonAstChunker().chunk(PYTHON_SOURCE, ctx)
        chunks = server.registry.dispatch_file(PY_DISPATCH_PATH, PYTHON_SOURCE, ctx)
        assert chunks == expected

    def test_wiring_runs_after_default_registry_is_built(self, tmp_path: Path) -> None:
        # Ordering guard against the "applied before defaults registered" bug: the
        # target ``python_ast`` exists ONLY after ``_build_default_registry()``. A
        # wiring that applied overrides first would reject this identity mapping as an
        # unknown key (false positive). A clean boot + correct dispatch proves order.
        server = _boot_from_yaml({".py": {CHUNKER_INNER_KEY: PYTHON_AST_CHUNKER_KEY}}, tmp_path)
        ctx = _chunk_context(PY_DISPATCH_PATH)
        chunks = server.registry.dispatch_file(PY_DISPATCH_PATH, PYTHON_SOURCE, ctx)
        assert chunks == PythonAstChunker().chunk(PYTHON_SOURCE, ctx)

    def test_override_leaves_unmentioned_default_extensions_untouched(self, tmp_path: Path) -> None:
        # An override for one extension must not wipe the defaults for others (the
        # registry keeps overrides in a SEPARATE map). Re-route only .yaml; assert
        # .py and .md still route to their defaults, and .yaml to the override.
        server = _boot_from_yaml({".yaml": {CHUNKER_INNER_KEY: TEXT_CHUNKER_KEY}}, tmp_path)
        py_ctx = _chunk_context(PY_DISPATCH_PATH)
        md_ctx = _chunk_context(MD_DISPATCH_PATH)
        yaml_ctx = _chunk_context(YAML_DISPATCH_PATH)
        assert server.registry.dispatch_file(
            PY_DISPATCH_PATH, PYTHON_SOURCE, py_ctx
        ) == PythonAstChunker().chunk(PYTHON_SOURCE, py_ctx)
        assert server.registry.dispatch_file(
            MD_DISPATCH_PATH, MARKDOWN_SOURCE, md_ctx
        ) == MarkdownChunker().chunk(MARKDOWN_SOURCE, md_ctx)
        assert server.registry.dispatch_file(
            YAML_DISPATCH_PATH, YAML_SOURCE, yaml_ctx
        ) == TextChunker().chunk(YAML_SOURCE, yaml_ctx)

    def test_uppercase_extension_in_config_still_routes_case_insensitively(
        self, tmp_path: Path
    ) -> None:
        # Defense-in-depth (lower real-world likelihood: live yamls use lowercase
        # extension keys). The registry lowercases extensions on apply_overrides;
        # the wiring must not break that seam. An UPPERCASE ``.YAML`` config key must
        # still claim a lowercase ``notes.yaml`` file for the text chunker.
        server = _boot_from_yaml({".YAML": {CHUNKER_INNER_KEY: TEXT_CHUNKER_KEY}}, tmp_path)
        ctx = _chunk_context("notes.yaml")
        chunks = server.registry.dispatch_file("notes.yaml", YAML_SOURCE, ctx)
        assert chunks == TextChunker().chunk(YAML_SOURCE, ctx)

    def test_direct_construction_also_applies_overrides(self) -> None:
        # The wiring lives in ``__init__``, not ``from_config``. Constructing directly
        # (bypassing the yaml round-trip) must apply the overrides too.
        server = LoreServer(_config_with_chunkers({".yaml": {CHUNKER_INNER_KEY: TEXT_CHUNKER_KEY}}))
        ctx = _chunk_context(YAML_DISPATCH_PATH)
        chunks = server.registry.dispatch_file(YAML_DISPATCH_PATH, YAML_SOURCE, ctx)
        assert chunks, "direct construction must apply config.chunkers overrides"
        assert chunks == TextChunker().chunk(YAML_SOURCE, ctx)


class TestChunkerConfigWiringFingerprintNeutral:
    """R6 — the wiring itself is fingerprint-fold neutral (it must not mutate config.chunkers).

    ``embedding_schema_fingerprint`` folds ``config.chunkers`` (``index/schema.py``).
    The EDITED-block direction (an edit flips the fingerprint → triggers the existing
    auto-rebuild) is already pinned by ``test_schema_rebuild.py::TestFingerprintSensitivity``
    and is NOT duplicated. This pins the neutrality direction: applying overrides must
    not alter the fold — an unedited config's fingerprint is unchanged by construction,
    and the wiring never mutates ``config.chunkers`` in place (e.g. by popping the
    ``chunker`` key while projecting), which would silently change the fold.
    """

    def test_construction_does_not_mutate_config_chunkers(self) -> None:
        # Arrange: snapshot the block BEFORE construction (deepcopy so an in-place
        # mutation of the live dict is detectable).
        config = _config_with_chunkers(LIVE_DI_CHUNKERS)
        chunkers_before = copy.deepcopy(config.chunkers)
        # Act
        server = LoreServer(config)
        # Assert: the projection must not pop/mutate the inner mappings; the fold's
        # input is preserved verbatim.
        assert server.config.chunkers == chunkers_before

    def test_wiring_is_fingerprint_fold_neutral(self) -> None:
        # The fingerprint computed from an identical config must be unchanged by the
        # act of constructing the server (which applies the overrides).
        config = _config_with_chunkers(LIVE_DI_CHUNKERS)
        fingerprint_before = embedding_schema_fingerprint(config)
        server = LoreServer(config)
        fingerprint_after = embedding_schema_fingerprint(server.config)
        assert fingerprint_after == fingerprint_before
