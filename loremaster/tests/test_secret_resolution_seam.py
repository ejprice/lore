"""Contract — packet 42 step 2: ONE secret-resolution entry point.

Packet 42 Scope IN #2: *"Three hand-rolled secret resolvers exist —
``config.resolve_secret``, ``loresigil/factory._resolve_api_key``, and
``calibration/counting.load_api_key`` ≡ ``scripts/token_survey.load_api_key``.
Consolidate."* Two operator rulings settle the shape:

1. **#222 — push resolution UP to the composition root.** ``loresigil`` resolves
   nothing; ``loremaster.embedding.to_loresigil_config`` — the ONLY production
   translator — calls ``resolve_secret``. ``loremaster.config.EmbeddingConfig.
   api_key_env`` STAYS: the env-var NAME belongs in ``lore.yaml``.
2. **Declare ``python-dotenv`` and adopt it** in the ``load_api_key`` twins,
   replacing the hand-rolled ``KEY=value`` parser and collapsing them to ONE
   implementation.

This module pins the loremaster half. The loresigil half is
``loresigil/tests/test_factory_secret_resolution.py``.

**OPERATOR RULINGS R1-R3, 2026-07-26 (`9600d84`) — BINDING, and they settle what the
Phase 0 inventory left spec-silent. They are not re-litigated here.**

* **R1 — C2/C9 semantics.** ``resolve_secret``'s semantics are the ONE implementation:
  the value is **never stripped** (a key whose real bytes include leading/trailing
  whitespace survives byte-exact) and unset / empty / whitespace-only are all
  **fatal**, with the error naming the variable.
* **R2 — the mechanism (this NARROWS the earlier "adopt python-dotenv in the twins"
  ruling).** ``resolve_secret`` grows an OPT-IN ``env_file: Path | None = None`` and
  becomes the single lookup for all three former resolvers: environment first, then —
  only when a file was passed — ``dotenv.dotenv_values(env_file)``. ``dotenv_values``,
  never ``load_dotenv``: it must NOT mutate ``os.environ``. (``python-decouple`` was
  probed and WORKS; declined on maintenance — 3.8, uploaded 2023-03-01, no declared
  ``requires_python``, against this repo's Python 3.14.)
* **R3 — the ``.env`` fallback is NOT available to the server.** ``server.py``,
  ``scout.py`` and ``index/cli.py`` call ``resolve_secret(NAME)`` with **no**
  ``env_file``; only ``calibration/counting.py`` (and, through it,
  ``scripts/token_survey.py``) passes one. *"A stray ``.env`` in the working directory
  must never become a production credential source."* The ruling is explicit that this
  **is a pinnable property, not a convention** — see
  :class:`TestTheEnvFileFallbackIsNotAvailableToTheServer`, which is the instrument.

⚠ ONE NEW TENSION, surfaced rather than decided (it is NOT a re-opening of C9): R1's
prose says an empty exported variable is fatal, while R2's ruled code snippet reads
``if not value and env_file is not None`` — so on the **file-enabled** path an empty
exported variable falls THROUGH to the file, which is C9's old behaviour. The two
disagree in exactly one cell. Nothing here pins that cell; the pins below assert only
what BOTH readings demand. The report carries the fork and a recommendation.

How to run:
    uv run pytest loremaster/tests/test_secret_resolution_seam.py -n auto -q
"""

from __future__ import annotations

import ast
import inspect
import os
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest
from _logging_fixtures import production_sources
from loremaster.config import EmbeddingConfig, resolve_secret
from pydantic import SecretStr

import loremaster

# The env var names the fixtures below resolve against. Distinct per concern so a
# leaked monkeypatch cannot make one test pass because another set it.
TEI_KEY_ENV = "LORE_PKT42_TEI_KEY"
ABSENT_KEY_ENV = "LORE_PKT42_DEFINITELY_UNSET_KEY"

# A Voyage-shaped bearer key (``pa-`` + base64url), obviously fake.
TEI_KEY_VALUE = "pa-S3aM9wQ2mV7bX4nR8yL5jH1dF6sA0cUeZpOiN2tVxYw"

# The Anthropic key env var ``load_api_key`` reads. Imported from the production
# module rather than re-typed, so a rename moves these fixtures with it
# (CLAUDE.md clause: shared conventions, never hand-copied literals).
from loremaster.calibration.counting import (  # noqa: E402  (after the constants it annotates)
    ANTHROPIC_API_KEY_ENV,
    load_api_key,
)

ANTHROPIC_KEY_VALUE = "sk-ant-api03-7hQ2xR9mB4kW1nT6vY8pL3cJ5dF0gS-aZeUiOoXtMrKyPqNwHbVjGl"


def _repo_root() -> Path:
    """The workspace root, derived from the imported package under test."""
    package_file = loremaster.__file__
    assert package_file is not None, "loremaster imported as an empty namespace package"
    return Path(package_file).resolve().parent.parent.parent


def _scripts_module(name: str) -> Any:
    """Import a module out of the non-package ``scripts/`` directory.

    Mirrors ``scripts/test_snapshot_gc.py``'s idiom exactly rather than inventing
    a second one — ``scripts/`` is not a package, so the directory has to be on
    ``sys.path`` before the import.
    """
    scripts_root = _repo_root() / "scripts"
    if str(scripts_root) not in sys.path:
        sys.path.insert(0, str(scripts_root))
    import importlib

    return importlib.import_module(name)


# --------------------------------------------------------------------------- #
# The loremaster embedding config, with EVERY field set to a NON-DEFAULT value
# --------------------------------------------------------------------------- #
# A fixture that leaves optional fields at their defaults cannot see a
# translation that DROPS them: ``None`` in, ``None`` out, byte-identical, wrong.
# This repo has shipped that exact class three times (CLAUDE.md, FIXTURES MUST
# DISCRIMINATE). Every value below therefore differs from both models' defaults.
NON_DEFAULT_EMBEDDING_FIELDS: dict[str, Any] = {
    "backend": "voyage-context",
    "base_url": "http://embedder.internal:9090",
    "endpoint": "/v1/embed-custom",
    "model": "voyageai/voyage-4-large",
    "dim": 1024,
    "max_input_tokens": 4096,
    "max_batch_texts": 17,
    "concurrency": 5,
    "connect_timeout_s": 12.5,
    "api_key_env": TEI_KEY_ENV,
    "tokenizer": "voyageai/voyage-4-nano",
    "truncate": True,
    "query_prompt_name": "query-prompt-not-the-default",
    "document_prompt_name": "document-prompt-not-the-default",
}


def _loremaster_embedding_config(**overrides: Any) -> EmbeddingConfig:
    """Build a loremaster embedding config from the non-default fixture."""
    return EmbeddingConfig(**{**NON_DEFAULT_EMBEDDING_FIELDS, **overrides})


class TestTheCompositionRootIsWhereTheEmbeddingSecretIsResolved:
    """#222's ruled shape: ``to_loresigil_config`` resolves; nothing below it does."""

    def test_it_routes_through_the_shared_resolver(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # PROVEN BY MUTATION, NOT INSPECTION (CLAUDE.md: routing is not sharing).
        # Replace the shared resolver with a sentinel; the translated config must
        # carry the sentinel. A build that hand-rolls ``os.environ.get`` here
        # calls the right thing zero times and stays green on any pin that only
        # checks the resulting type.
        from loremaster import embedding

        sentinel = "RESOLVED-BY-THE-SHARED-SEAM"
        observed_names: list[str] = []

        def _fake_resolve(env_var_name: str) -> SecretStr:
            observed_names.append(env_var_name)
            return SecretStr(sentinel)

        monkeypatch.setattr(embedding, "resolve_secret", _fake_resolve)
        translated = embedding.to_loresigil_config(_loremaster_embedding_config())
        assert observed_names == [TEI_KEY_ENV], (
            "to_loresigil_config did not call the shared resolver with the configured "
            f"api_key_env; observed {observed_names}"
        )
        assert translated.api_key.get_secret_value() == sentinel

    def test_the_resolved_key_is_the_environments_real_value(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The unmocked leg — the mutation pin above proves ROUTING, this proves
        # the routing produces the right bytes end to end.
        from loremaster import embedding

        monkeypatch.setenv(TEI_KEY_ENV, TEI_KEY_VALUE)
        translated = embedding.to_loresigil_config(_loremaster_embedding_config())
        assert isinstance(translated.api_key, SecretStr)
        assert translated.api_key.get_secret_value() == TEI_KEY_VALUE

    def test_an_unset_variable_fails_at_TRANSLATION_before_any_embedder_exists(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Inventory B7: resolution moves EARLIER — from embedder CONSTRUCTION to
        # config translation. "Strictly sooner, never later" is the property.
        from loremaster import embedding

        monkeypatch.delenv(ABSENT_KEY_ENV, raising=False)
        config = _loremaster_embedding_config(api_key_env=ABSENT_KEY_ENV)
        # Pinned to ``KeyError`` — ``resolve_secret``'s documented contract, which
        # the ruling adopts by naming it. "Any exception" would pass on a stub's
        # NotImplementedError (the trap ``test_factory.py`` already warns about).
        with pytest.raises(KeyError) as excinfo:
            embedding.to_loresigil_config(config)
        # Inventory B5: the message names the offending variable.
        assert ABSENT_KEY_ENV in str(excinfo.value)

    def test_make_embedder_from_config_surfaces_the_same_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The caller-facing half of B2/B7: no keyless embedder is ever built.
        from loremaster import embedding

        monkeypatch.delenv(ABSENT_KEY_ENV, raising=False)
        with pytest.raises(KeyError):
            embedding.make_embedder_from_config(_loremaster_embedding_config(api_key_env=ABSENT_KEY_ENV))

    @pytest.mark.parametrize(
        "label,value", [("empty", ""), ("whitespace only", "  \t ")], ids=["empty", "whitespace-only"]
    )
    def test_a_blank_variable_fails_at_translation(
        self, monkeypatch: pytest.MonkeyPatch, label: str, value: str
    ) -> None:
        # RULED BY R1 (2026-07-26): unset / empty / whitespace-only are ALL fatal.
        # Inventory B2's old ``if not key`` covered unset AND empty, while B3
        # records that it ACCEPTED a whitespace-only value — an old bug this
        # consolidation fixes incidentally. B3 is deliberately NOT re-pinned; the
        # ruled semantics are. This is the SERVER path (no ``env_file``), where
        # R3 guarantees no file fallback exists to soften any of the three.
        from loremaster import embedding

        monkeypatch.setenv(ABSENT_KEY_ENV, value)
        with pytest.raises(KeyError):
            embedding.to_loresigil_config(_loremaster_embedding_config(api_key_env=ABSENT_KEY_ENV))

    def test_loremaster_config_still_carries_the_env_var_NAME(self) -> None:
        # Inventory B10, pinned because it is the half a reshape most easily
        # over-applies: the loresigil model loses ``api_key_env``, the LOREMASTER
        # model keeps it. ``server.py``'s embed probe-gate message reads this
        # field, and ``lore.yaml`` is where an env-var NAME belongs.
        assert "api_key_env" in EmbeddingConfig.model_fields
        assert _loremaster_embedding_config().api_key_env == TEI_KEY_ENV

    def test_the_loremaster_config_never_gains_a_resolved_key_field(self) -> None:
        # The inverse guard: a build that "helpfully" mirrors ``api_key`` onto the
        # loremaster model would put a secret in the ``lore.yaml`` schema — the
        # exact thing the env-ref indirection exists to prevent.
        assert "api_key" not in EmbeddingConfig.model_fields


class TestEveryOtherFieldStillCopiesThrough:
    """Inventory's per-field provenance note for ``to_loresigil_config``.

    Ten loresigil fields are COPIED THROUGH from the loremaster config;
    ``output_dimension`` is FORCED from ``config.dim``; ``api_key`` becomes
    DERIVED. *"The remaining ten copied-through fields must stay copied-through —
    a reshape that drops one is a silent config regression no gate sees."*

    The field list is derived from the loresigil model, never hand-written, so a
    field added there next year is covered by this pin rather than by an auditor's
    memory.
    """

    @staticmethod
    def _translate(monkeypatch: pytest.MonkeyPatch) -> Any:
        from loremaster import embedding

        monkeypatch.setenv(TEI_KEY_ENV, TEI_KEY_VALUE)
        return embedding.to_loresigil_config(_loremaster_embedding_config())

    def test_the_derived_field_set_is_exactly_two(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # A CLOSED set. Adding a third derived field silently changes what a
        # ``lore.yaml`` edit controls; making it reddens here so it is a decision.
        translated = self._translate(monkeypatch)
        source = _loremaster_embedding_config()
        # ⚠ **R32 defect 4 — THIS COULD NEVER PASS, AND IT WAS ARITHMETIC IN THE
        # TEST, NOT A BUILD OUTCOME.** The filter was ``hasattr(source, name)``,
        # and ``source`` is the LOREMASTER config, which has neither
        # ``output_dimension`` nor ``api_key`` — the latter guaranteed by this
        # file's own sibling pin
        # ``test_the_loremaster_config_never_gains_a_resolved_key_field``. So the
        # filter excluded exactly the two members the assertion then demanded and
        # ``derived`` was empty against EVERY possible build. The C-DEF class.
        #
        # ``not hasattr(...)`` is the correct predicate: a loresigil field with no
        # loremaster counterpart IS derived — it is a value a ``lore.yaml`` edit
        # does not control, which is the property this pin exists for.
        derived = {
            name
            for name in type(translated).model_fields
            if not hasattr(source, name) or getattr(translated, name) != getattr(source, name)
        }
        # ``api_url`` joins the closed set honestly: the translator deliberately
        # leaves it at each backend's own default rather than forcing one (the
        # odoo15_ctx deploy bug), so it is genuinely not config-controlled.
        assert derived == {"output_dimension", "api_key", "api_url"}, (
            f"the derived/forced field set changed: {derived}. Every other loresigil field "
            "must be copied through from lore.yaml, or a configured value silently reverts "
            "to a loresigil factory default."
        )

    def test_every_shared_field_is_copied_through_byte_exact(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        translated = self._translate(monkeypatch)
        source = _loremaster_embedding_config()
        shared = [
            name
            for name in type(translated).model_fields
            if name not in {"output_dimension", "api_key", "api_url"} and hasattr(source, name)
        ]
        # ANTI-VACUITY: the inventory says TEN fields are copied through. A build
        # that renamed them all would leave ``shared`` empty and this pin silent.
        assert len(shared) >= 10, f"only {len(shared)} shared fields found: {shared}"
        mismatches = [
            f"{name}: loresigil={getattr(translated, name)!r} lore.yaml={getattr(source, name)!r}"
            for name in shared
            if getattr(translated, name) != getattr(source, name)
        ]
        assert not mismatches, "these fields no longer carry the project config's value:\n  " + "\n  ".join(
            mismatches
        )

    def test_the_fixture_uses_no_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # POSITIVE CONTROL FOR THE FIXTURE ITSELF. If any fixture value happened
        # to equal the loresigil model's default, a translation that DROPPED that
        # field would be invisible. Assert each shared field's fixture value
        # differs from the loresigil default it would fall back to.
        translated = self._translate(monkeypatch)
        source = _loremaster_embedding_config()
        indistinguishable = [
            name
            for name, field in type(translated).model_fields.items()
            if name not in {"output_dimension", "api_key", "api_url"}
            and hasattr(source, name)
            and field.default is not None
            and getattr(source, name) == field.default
        ]
        assert not indistinguishable, (
            "these fixture values equal the loresigil model's DEFAULT, so a translation that "
            f"dropped the field would pass unnoticed: {indistinguishable}"
        )

    def test_output_dimension_follows_dim_and_not_the_factory_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The one FORCED field, pinned on a non-default dim so the assertion is
        # about the routing rather than about a coincidence.
        translated = self._translate(monkeypatch)
        assert translated.output_dimension == NON_DEFAULT_EMBEDDING_FIELDS["dim"]
        assert translated.dim == NON_DEFAULT_EMBEDDING_FIELDS["dim"]


class TestResolveSecretIsTheUnifiedLookup:
    """RULING R2: ONE lookup shape serves all three former resolvers.

    ``resolve_secret(env_var_name, env_file=None)`` reads the environment first and,
    only when a file was passed, falls back to ``dotenv.dotenv_values(env_file)``.
    The DRY property the earlier "adopt dotenv in the twins" shape lacked: there is
    now one place that decides precedence, one place that decides emptiness, and one
    place that decides whether a file is consulted at all.
    """

    def test_the_signature_makes_the_file_OPT_IN(self) -> None:
        # The default is what makes R3 enforceable at all: a call that says nothing
        # about files gets no file. A required parameter, or a default pointing at
        # a discovered ``.env``, would make every server call site a decision.
        parameters = inspect.signature(resolve_secret).parameters
        assert "env_file" in parameters, "resolve_secret did not grow the ruled second parameter"
        assert parameters["env_file"].default is None, (
            "env_file must default to None — opt-in is the property R3 depends on"
        )

    def test_the_environment_beats_the_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Inventory C1: precedence is POLICY. The file carries a DIFFERENT value, so
        # precedence is observable rather than assumed.
        env_file = tmp_path / "mcp.env"
        env_file.write_text(f"{ANTHROPIC_API_KEY_ENV}=pa-from-the-file-not-the-env\n", encoding="utf-8")
        monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, ANTHROPIC_KEY_VALUE)
        assert resolve_secret(ANTHROPIC_API_KEY_ENV, env_file).get_secret_value() == ANTHROPIC_KEY_VALUE

    def test_the_file_is_consulted_when_the_variable_is_unset(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Inventory C3/C4, now a property of the shared resolver rather than of a
        # private parser. Two decoy keys around it so a parser that returns the
        # first or last line regardless of name is caught.
        monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
        env_file = tmp_path / "mcp.env"
        env_file.write_text(
            f"OTHER_TOOL_TOKEN=irrelevant\n{ANTHROPIC_API_KEY_ENV}={ANTHROPIC_KEY_VALUE}\nMORE=2\n",
            encoding="utf-8",
        )
        assert resolve_secret(ANTHROPIC_API_KEY_ENV, env_file).get_secret_value() == ANTHROPIC_KEY_VALUE

    def test_reading_the_file_does_NOT_mutate_the_process_environment(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # ⚠ THE PIN THAT DISCRIMINATES ``dotenv_values`` FROM ``load_dotenv``, and the
        # reason R2 names the function rather than the package. ``load_dotenv``
        # EXPORTS every key in the file into ``os.environ`` — so one calibration run
        # that opts into a file would silently populate the environment for every
        # subsequent ``resolve_secret(NAME)`` in the same process, including the
        # server-path ones R3 exists to protect. That build satisfies every other pin
        # in this class.
        #
        # It is also the RECEIVER-BLIND form of the check: it asserts the OUTCOME
        # (the environment is unchanged) rather than banning a function name, so a
        # third-party helper that mutates the environment is caught too.
        monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
        env_file = tmp_path / "mcp.env"
        env_file.write_text(
            f"{ANTHROPIC_API_KEY_ENV}={ANTHROPIC_KEY_VALUE}\nSOME_OTHER_TOOL_TOKEN=leaked\n",
            encoding="utf-8",
        )
        resolved = resolve_secret(ANTHROPIC_API_KEY_ENV, env_file)
        assert resolved.get_secret_value() == ANTHROPIC_KEY_VALUE  # the lookup worked
        assert ANTHROPIC_API_KEY_ENV not in os.environ, (
            "resolving from a file EXPORTED the key into os.environ — that is load_dotenv, "
            "not dotenv_values (ruling R2), and it silently arms the server path R3 protects"
        )
        assert "SOME_OTHER_TOOL_TOKEN" not in os.environ, (
            "reading the file exported UNRELATED keys into the process environment"
        )

    def test_no_file_is_discovered_implicitly(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # R3's unit-level half: with no ``env_file`` argument, a ``.env`` sitting in
        # the working directory must be invisible. ``dotenv.find_dotenv()`` would
        # find it — that is the wrong build, and it is a plausible one, because
        # ``load_dotenv()`` with no arguments does exactly that by default.
        monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
        (tmp_path / ".env").write_text(f"{ANTHROPIC_API_KEY_ENV}={ANTHROPIC_KEY_VALUE}\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        with pytest.raises(KeyError):
            resolve_secret(ANTHROPIC_API_KEY_ENV)

    @pytest.mark.parametrize(
        "label,value",
        [("empty", ""), ("single space", " "), ("tabs and spaces", " \t ")],
        ids=["empty", "single-space", "whitespace-only"],
    )
    def test_a_blank_variable_is_fatal_on_the_serverpath(
        self, monkeypatch: pytest.MonkeyPatch, label: str, value: str
    ) -> None:
        # RULING R1, scoped honestly per R5's rider: this is the path where NO
        # ``env_file`` is supplied, so resolution ends at the environment and a blank
        # value is fatal there. It is NOT the claim that a blank variable is always
        # fatal — with a file supplied it falls THROUGH (R5), pinned above.
        # Inventory B3's old permissiveness — a whitespace-only value ACCEPTED — is
        # retired and deliberately NOT re-pinned.
        monkeypatch.setenv(ABSENT_KEY_ENV, value)
        with pytest.raises(KeyError) as excinfo:
            resolve_secret(ABSENT_KEY_ENV)
        assert ABSENT_KEY_ENV in str(excinfo.value), f"the {label} case did not name the variable"

    def test_a_blank_value_is_fatal_wherever_it_came_from(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # THE QUANTIFIER FORM of the pin above, and the one R5 leaves intact: the
        # outcome property is "a blank credential is never RETURNED", ∀ source —
        # which is a statement about the END of resolution, not about each source.
        # A build that validated the environment read and forwarded the FILE
        # value unchecked passes the parametrised pin above and hands the calibration
        # counter an empty ``x-api-key`` header, 401-ing on every request instead of
        # failing at load.
        monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
        env_file = tmp_path / "mcp.env"
        env_file.write_text(f'{ANTHROPIC_API_KEY_ENV}="   "\n', encoding="utf-8")
        with pytest.raises(KeyError):
            resolve_secret(ANTHROPIC_API_KEY_ENV, env_file)

    @pytest.mark.parametrize("source", ["environment", "file"], ids=["from-env", "from-file"])
    def test_the_value_is_byte_exact_from_either_source(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, source: str
    ) -> None:
        # RULING R1: never stripped. Forced from BOTH sources, because they are
        # different code paths and dotenv has its own quoting rules — measured
        # 2026-07-26, ``KEY="  padded  "`` preserves the padding while an unquoted
        # ``KEY=  padded  `` does not, so the quoted form is what a byte-exact
        # credential requires and what this fixture uses.
        padded = f"  {ANTHROPIC_KEY_VALUE}\t"
        env_file = tmp_path / "mcp.env"
        if source == "environment":
            monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, padded)
            env_file.write_text("", encoding="utf-8")
        else:
            monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
            env_file.write_text(f'{ANTHROPIC_API_KEY_ENV}="{padded}"\n', encoding="utf-8")
        assert resolve_secret(ANTHROPIC_API_KEY_ENV, env_file).get_secret_value() == padded

    def test_an_absent_file_is_not_an_error_by_itself(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # The environment still wins when the named file does not exist — a missing
        # operator ``.env`` must not break a correctly-exported environment.
        monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, ANTHROPIC_KEY_VALUE)
        resolved = resolve_secret(ANTHROPIC_API_KEY_ENV, tmp_path / "does-not-exist.env")
        assert resolved.get_secret_value() == ANTHROPIC_KEY_VALUE

    @pytest.mark.parametrize(
        "label,literal",
        [
            ("dollar-brace", "pa-Q4nT${NOT_A_REAL_VAR}8vX2mK9wL5bR7yH3jD6sF1gA0c"),
            ("unset-var-tail", "pw${DEFINITELY_UNSET_PKT42}tail"),
            ("bare-dollar", "pa-Q4nT$HOME8vX2mK9wL5bR7yH3jD6sF1gA0c"),
            ("double-dollar", "pa-Q4nT$$8vX2mK9wL5bR7yH3jD6sF1gA0c"),
        ],
        ids=["dollar-brace", "unset-var-tail", "bare-dollar", "double-dollar"],
    )
    def test_a_dollar_sign_in_the_credential_survives_byte_exact(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, label: str, literal: str
    ) -> None:
        # ⚠ RULING R12 — this CORRECTS R2's ruled snippet, which was wrong as
        # written. ``dotenv_values`` defaults to ``interpolate=True``, so a secret
        # containing ``${…}`` is silently REWRITTEN, and an unset ``${VAR}``
        # SHORTENS the credential (measured: ``pw${NOPE}tail`` -> ``pwtail``).
        # The ruled call is ``dotenv_values(env_file, interpolate=False)``.
        #
        # This is a byte-exactness violation of R1 hiding inside the mechanism R2
        # chose — the package did the job for the file FORMAT and quietly did
        # something else to the VALUE. ``$`` is legal in a generated API key, so
        # this is not exotic: it silently authenticates as a different string.
        monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
        env_file = tmp_path / "mcp.env"
        env_file.write_text(f"{ANTHROPIC_API_KEY_ENV}='{literal}'\n", encoding="utf-8")
        assert resolve_secret(ANTHROPIC_API_KEY_ENV, env_file).get_secret_value() == literal, (
            f"the {label} credential was rewritten in transit — pass interpolate=False (R12)"
        )

    def test_a_real_then_blank_duplicate_key_is_fatal(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # RULING R15, ruled by extension from R1 and recorded rather than re-asked.
        # ``KEY=real`` then ``KEY=`` in one file: the hand-rolled parser yielded
        # ``"real"`` (first non-empty wins); ``dotenv_values`` is LAST-WINS and
        # yields ``""`` -> fatal. That is fail-OPEN to fail-CLOSED on a credential
        # path, and fail-closed is the direction R1 already chose. A duplicate key
        # in a ``.env`` is operator error twice over.
        #
        # This is the DUAL of the blank-then-real case pinned above; the inventory
        # (C6) only covered one direction.
        monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
        env_file = tmp_path / "mcp.env"
        env_file.write_text(
            f"{ANTHROPIC_API_KEY_ENV}={ANTHROPIC_KEY_VALUE}\n{ANTHROPIC_API_KEY_ENV}=\n",
            encoding="utf-8",
        )
        with pytest.raises(KeyError):
            resolve_secret(ANTHROPIC_API_KEY_ENV, env_file)

    @pytest.mark.parametrize("quote", ["'", '"'], ids=["single", "double"])
    def test_a_quoted_file_value_is_unquoted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, quote: str
    ) -> None:
        # Inventory C5: the MECHANISM is dropped, the OUTCOME kept. dotenv owns
        # quote handling and does it more correctly than ``.strip("'\"")``.
        monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
        env_file = tmp_path / "mcp.env"
        env_file.write_text(
            f"{ANTHROPIC_API_KEY_ENV}={quote}{ANTHROPIC_KEY_VALUE}{quote}\n", encoding="utf-8"
        )
        assert resolve_secret(ANTHROPIC_API_KEY_ENV, env_file).get_secret_value() == ANTHROPIC_KEY_VALUE

    def test_an_export_prefixed_line_is_honoured(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Inventory C11, RE-DERIVED 2026-07-26 at 9c08cac: the finding says "one
        # twin" failed to honour ``export KEY=…`` — in fact BOTH did, because both
        # matched with ``stripped.startswith(f"{ANTHROPIC_API_KEY_ENV}=")``. An
        # operator ``.env`` written for a shell routinely carries ``export``.
        monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
        env_file = tmp_path / "mcp.env"
        env_file.write_text(f"export {ANTHROPIC_API_KEY_ENV}={ANTHROPIC_KEY_VALUE}\n", encoding="utf-8")
        assert resolve_secret(ANTHROPIC_API_KEY_ENV, env_file).get_secret_value() == ANTHROPIC_KEY_VALUE

    def test_a_blank_declaration_does_not_shadow_a_later_real_one(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Inventory C6: an empty value must not end the search. Measured 2026-07-26:
        # ``dotenv_values`` is LAST-WINS on a duplicate key, so blank-then-real
        # yields the real one — the same outcome the hand-rolled "keep scanning"
        # loop produced, by a different route.
        monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
        env_file = tmp_path / "mcp.env"
        env_file.write_text(
            f"{ANTHROPIC_API_KEY_ENV}=\n{ANTHROPIC_API_KEY_ENV}={ANTHROPIC_KEY_VALUE}\n",
            encoding="utf-8",
        )
        assert resolve_secret(ANTHROPIC_API_KEY_ENV, env_file).get_secret_value() == ANTHROPIC_KEY_VALUE

    @pytest.mark.parametrize(
        "label,blank",
        [("empty", ""), ("single space", " "), ("tabs and spaces", " \t ")],
        ids=["empty", "single-space", "whitespace-only"],
    )
    def test_a_blank_exported_variable_falls_through_to_the_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, label: str, blank: str
    ) -> None:
        # RULING R5 (2026-07-26) — it went against this contract's FIRST
        # recommendation and adopted its SECOND. The R2 shape stands: a blank
        # exported variable falls through to the ``env_file`` when one is supplied,
        # because an operator blanking a variable to force the file fallback is a
        # real calibration workflow.
        #
        # ⚠ PARAMETRISED OVER ALL THREE BLANK SHAPES BY A LEAD RULING THAT THE
        # AUTHORITY FILE DOES NOT COVER (2026-07-26): *"whitespace-only should
        # behave the SAME as empty on the file-enabled path."* This is a REAL
        # CHANGE to R2's ruled snippet, which reads ``if not value and env_file is
        # not None`` — ``" "`` is TRUTHY, so under the snippet as written a
        # whitespace-only variable does NOT fall through and dies at the
        # emptiness check instead. Implementing the ruling needs
        # ``if (not value or not value.strip()) and env_file is not None``.
        # Flagged in the report: the snippet and the ruling now disagree, and the
        # snippet is the thing that will get copied.
        monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, blank)
        env_file = tmp_path / "mcp.env"
        env_file.write_text(f"{ANTHROPIC_API_KEY_ENV}={ANTHROPIC_KEY_VALUE}\n", encoding="utf-8")
        assert resolve_secret(ANTHROPIC_API_KEY_ENV, env_file).get_secret_value() == (
            ANTHROPIC_KEY_VALUE
        ), f"a {label} exported variable did not fall through to the file (R5)"

    @pytest.mark.parametrize(
        "label,blank",
        [("empty", ""), ("whitespace only", "  \t ")],
        ids=["empty", "whitespace-only"],
    )
    def test_a_blank_exported_variable_is_still_fatal_when_the_file_also_misses(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, label: str, blank: str
    ) -> None:
        # The other half of R5, and the half that keeps the fall-through honest:
        # falling through is not forgiving, it is DEFERRING. If the file misses
        # too, the end of resolution is still fatal — for BOTH blank shapes, so
        # the symmetry the lead ruled holds in both directions.
        monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, blank)
        env_file = tmp_path / "mcp.env"
        env_file.write_text("SOME_OTHER_TOKEN=abc\n", encoding="utf-8")
        with pytest.raises(KeyError) as excinfo:
            resolve_secret(ANTHROPIC_API_KEY_ENV, env_file)
        assert ANTHROPIC_API_KEY_ENV in str(excinfo.value), f"the {label} case did not name it"

    def test_no_pins_failure_message_overclaims_the_emptiness_rule(self) -> None:
        # ⚠ R5's RIDER, mechanised — the half a builder drops (CLAUDE.md: "THE
        # RIDER IS PART OF THE RULING"). Emptiness is fatal **at the end of
        # resolution**, not at each source. A pin whose failure MESSAGE says
        # otherwise is a FALSE GATE: the message is the spec its author believed,
        # the assertion is the check the suite performs, and the gap between them
        # is a wrong build's door (P2 2026-07-14, where that gap let a wrong build
        # pass 399/399).
        #
        # SCANS ASSERTION MESSAGES VIA AST, not raw lines. The first version of
        # this pin grepped the file and matched its OWN explanatory comment and
        # its OWN predicate — it failed for a self-referential reason while every
        # real message was fine. An AST walk over ``ast.Assert.msg`` can only see
        # what a failing pin would actually PRINT, which is the thing the rider is
        # about.
        module = ast.parse(Path(__file__).read_text(encoding="utf-8"), filename=__file__)
        offenders: list[str] = []
        for node in ast.walk(module):
            if not isinstance(node, ast.Assert) or node.msg is None:
                continue
            text = " ".join(
                part.value
                for part in ast.walk(node.msg)
                if isinstance(part, ast.Constant) and isinstance(part.value, str)
            ).lower()
            if not text:
                continue
            overclaims = "always fatal" in text or "empty is fatal" in text
            if overclaims and "end of resolution" not in text:
                offenders.append(f"line {node.lineno}: {text[:90]}")
        assert not offenders, (
            "a pin's failure message states the emptiness rule unconditionally. Ruling R5: a "
            "blank exported variable falls through to the file, so the rule holds only at the "
            "end of resolution:\n  " + "\n  ".join(offenders)
        )

    def test_the_scan_for_overclaiming_messages_can_actually_fire(self) -> None:
        # POSITIVE CONTROL for the pin above, which asserts an ABSENCE — and an
        # absence assertion passes just as happily when the scanner is broken.
        # Feed it a synthetic module carrying exactly the message it hunts.
        synthetic = ast.parse('assert value, "an empty variable is always fatal"\n')
        found = [
            node
            for node in ast.walk(synthetic)
            if isinstance(node, ast.Assert)
            and node.msg is not None
            and any(
                isinstance(part, ast.Constant)
                and isinstance(part.value, str)
                and "always fatal" in part.value
                for part in ast.walk(node.msg)
            )
        ]
        assert found, "the message scanner cannot see an overclaiming message it is handed"


# The ONE call site permitted to hand ``resolve_secret`` an ``env_file`` (ruling R3).
# Keyed ``<display path>::<enclosing function>``, exactly like the unwrap allowlist —
# the safe set here is ONE entry, which is as small as an allowlist gets.
#
# ``scripts/token_survey.py`` does NOT appear: inventory C10 collapses the twins, so
# it reaches the file path through this one function rather than owning a call site.
RESOLVE_SECRET_ENV_FILE_ALLOWLIST: frozenset[str] = frozenset(
    {"loremaster/calibration/counting.py::load_api_key"}
)


def _resolve_secret_call_sites() -> list[tuple[str, bool]]:
    """Every ``resolve_secret(...)`` call, as ``(key, passes_an_env_file)``.

    ``passes_an_env_file`` is true for a second POSITIONAL argument or an
    ``env_file=`` keyword — both spellings, because a pin that only knew one of
    them would be defeated by the other, which is this repo's most-repeated
    instrument failure.
    """
    found: list[tuple[str, bool]] = []
    for display, source_path in _scanned_python_sources():
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        enclosing: dict[int, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for inner in ast.walk(node):
                    enclosing.setdefault(id(inner), node.name)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            name = (
                node.func.id
                if isinstance(node.func, ast.Name)
                else node.func.attr
                if isinstance(node.func, ast.Attribute)
                else None
            )
            if name != "resolve_secret":
                continue
            passes_file = len(node.args) > 1 or any(kw.arg == "env_file" for kw in node.keywords)
            found.append((f"{display}::{enclosing.get(id(node), '<module>')}", passes_file))
    return sorted(set(found))


class TestTheEnvFileFallbackIsNotAvailableToTheServer:
    """**RULING R3**, and the ruling says in terms that it is a PIN, not a convention.

    *"``server.py``, ``scout.py`` and ``index/cli.py`` call ``resolve_secret(NAME)``
    with no ``env_file``, so an unset variable stays fatal there exactly as today.
    Only ``calibration/counting.py`` and ``scripts/token_survey.py`` pass an
    ``env_file`` … a stray ``.env`` in the working directory must never become a
    production credential source."*

    Nothing else catches a future edit that adds one. Every behavioural pin in this
    module passes on a build where ``server.py`` helpfully threads a ``--env-file``
    through to ``build_app_context``: the resolver still works, the value is still a
    ``SecretStr``, the tests are still green — and the container has quietly gained a
    credential source that is not its environment.

    THE THREAT MODEL: this catches the **HONEST developer** who adds an ``env_file``
    argument because it made local development easier. It is NOT a boundary against a
    hostile author, who can read a file directly. Verdicts follow: *"someone could
    call ``dotenv_values`` themselves"* is not a defect for this gate — the
    ONE-ENTRY-POINT gate below is what covers that — whereas *"a server call site
    silently gained a file fallback"* is exactly what it exists to see.

    ALLOWLIST THE SAFE: the permitted set is ONE entry, and both directions are
    checked, so a stale entry cannot pre-authorise a future call site either.
    """

    def test_the_scan_finds_the_population(self) -> None:
        # POSITIVE CONTROL, and mind the TWO POPULATIONS — the trap this whole
        # packet keeps re-finding. Re-derived 2026-07-26 at 9c08cac: **13 raw
        # ``resolve_secret(...)`` calls** collapsing to **7 distinct
        # ``function::passes_file`` keys**, because several functions call it twice
        # (user + password). This helper returns the DISTINCT keys, so the
        # threshold is 7-based, not 13-based. De-duplicating on the PAIR is
        # deliberate: a function with one plain call and one file-passing call
        # yields two entries, so the offender is still visible.
        sites = _resolve_secret_call_sites()
        assert len(sites) >= 6, (
            f"the resolve_secret call-site scan found only {len(sites)} distinct sites: {sites}"
        )

    def test_no_server_path_call_site_passes_an_env_file(self) -> None:
        offenders = [
            key
            for key, passes_file in _resolve_secret_call_sites()
            if passes_file and key not in RESOLVE_SECRET_ENV_FILE_ALLOWLIST
        ]
        assert not offenders, (
            "these call sites hand resolve_secret an env_file. Ruling R3 (2026-07-26): the "
            "server path — server.py, scout.py, index/cli.py and everything reached from a "
            "container boot — must NOT have a file fallback, because a stray .env in the "
            "working directory would become a production credential source. If a NEW site "
            "genuinely needs the operator-.env workflow, that is an operator decision, not a "
            "lint fix:\n  " + "\n  ".join(offenders)
        )

    def test_the_allowlisted_site_actually_passes_one(self) -> None:
        # ⚠ THE CONTROL THAT MAKES THE PIN ABOVE MEAN ANYTHING. If
        # ``_resolve_secret_call_sites`` mis-detected the second argument — wrong AST
        # node, wrong keyword name — ``passes_file`` would be False everywhere and
        # ``test_no_server_path_call_site_passes_an_env_file`` would pass on a tree
        # where every call site threaded a file. Prove the detector can see one, on
        # the one site that is supposed to have it.
        passing = {key for key, passes_file in _resolve_secret_call_sites() if passes_file}
        assert passing == set(RESOLVE_SECRET_ENV_FILE_ALLOWLIST), (
            "the env_file detector sees "
            f"{sorted(passing)} where the ruling permits {sorted(RESOLVE_SECRET_ENV_FILE_ALLOWLIST)}. "
            "If the permitted site does not appear, the detector is broken and the pin above "
            "is passing vacuously — not passing."
        )

    def test_the_server_entry_points_are_actually_in_the_scanned_population(self) -> None:
        # R3 names three modules explicitly. If a rename or a move took one out of
        # the scan, this pin would still be green while governing nothing — so the
        # ruling's own three are asserted present by NAME.
        scanned = {key.split("::")[0] for key, _ in _resolve_secret_call_sites()}
        for named_by_the_ruling in ("loremaster/server.py", "loremaster/scout.py", "loremaster/index/cli.py"):
            assert named_by_the_ruling in scanned, (
                f"ruling R3 names {named_by_the_ruling} as a server-path caller, but the scan "
                "sees no resolve_secret call there — the gate is not governing what it claims"
            )


class TestLoadApiKeyRoutesThroughTheSharedResolver:
    """Inventory C1-C11 after R2: ``load_api_key`` is a thin, file-enabled caller.

    It is no longer an implementation of a lookup — it is the one place that opts
    into the operator ``.env`` workflow and translates the shared resolver's
    ``KeyError`` into the ``RuntimeError`` naming BOTH the variable and the file
    (inventory C7), exactly as ``load_config`` translates it into a ``ValueError``
    naming the yaml field.
    """

    def test_the_twins_are_literally_one_function(self) -> None:
        # Inventory C10. The strongest available collapse proof: two functions that
        # merely agree today are two functions that diverge tomorrow; identity
        # cannot (CLAUDE.md, #102).
        token_survey = _scripts_module("token_survey")
        assert token_survey.load_api_key is load_api_key, (
            "scripts/token_survey still owns a private copy of load_api_key"
        )

    def test_it_routes_through_the_shared_resolver(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # PROVEN BY MUTATION, NOT INSPECTION. Patch the shared resolver to a
        # sentinel; ``load_api_key`` must move with it AND must have passed the
        # env_file through. A build that kept its own dotenv call calls this zero
        # times and stays green on every behavioural pin in this class.
        from loremaster.calibration import counting

        sentinel = "pa-RESOLVED-BY-THE-SHARED-SEAM"
        observed: list[tuple[str, object]] = []

        def _fake_resolve(env_var_name: str, env_file: Path | None = None) -> SecretStr:
            observed.append((env_var_name, env_file))
            return SecretStr(sentinel)

        monkeypatch.setattr(counting, "resolve_secret", _fake_resolve)
        env_file = tmp_path / "mcp.env"
        assert counting.load_api_key(env_file).get_secret_value() == sentinel
        assert observed == [(ANTHROPIC_API_KEY_ENV, env_file)], (
            "load_api_key did not call the shared resolver with both the variable name and "
            f"the operator env file; observed {observed}"
        )

    def test_it_returns_a_secret_type(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # Inventory C8.
        monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, ANTHROPIC_KEY_VALUE)
        assert isinstance(load_api_key(tmp_path / "absent.env"), SecretStr)

    def test_an_exported_variable_wins_over_the_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Inventory C1, at the caller — the precedence a calibration operator sees.
        env_file = tmp_path / "mcp.env"
        env_file.write_text(f"{ANTHROPIC_API_KEY_ENV}=pa-from-the-file\n", encoding="utf-8")
        monkeypatch.setenv(ANTHROPIC_API_KEY_ENV, ANTHROPIC_KEY_VALUE)
        assert load_api_key(env_file).get_secret_value() == ANTHROPIC_KEY_VALUE

    def test_it_falls_back_to_the_env_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Inventory C3/C4 — the workflow R3 deliberately keeps available HERE and
        # nowhere else.
        monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
        env_file = tmp_path / "mcp.env"
        env_file.write_text(f"{ANTHROPIC_API_KEY_ENV}={ANTHROPIC_KEY_VALUE}\n", encoding="utf-8")
        assert load_api_key(env_file).get_secret_value() == ANTHROPIC_KEY_VALUE

    def test_a_missing_key_names_both_the_variable_and_the_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Inventory C7. The shared resolver's KeyError names only the VARIABLE (R2's
        # ruled snippet), so this caller must add the FILE — the operator has to be
        # able to fix the environment and the file in one step. A build that let the
        # bare KeyError escape loses half the message and changes the exception type
        # its two CLI callers catch.
        monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
        env_file = tmp_path / "does-not-exist.env"
        with pytest.raises(RuntimeError) as excinfo:
            load_api_key(env_file)
        message = str(excinfo.value)
        assert ANTHROPIC_API_KEY_ENV in message
        assert str(env_file) in message

    def test_a_file_that_exists_without_the_key_also_fails_loud(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # DIFFERENT DOOR, SAME OUTCOME (the quantifier law): the guard must not be
        # conditioned on "the file is missing". A file that exists and simply does
        # not carry the key is the more common operator mistake.
        monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
        env_file = tmp_path / "mcp.env"
        env_file.write_text("SOME_OTHER_TOKEN=abc\n", encoding="utf-8")
        with pytest.raises(RuntimeError):
            load_api_key(env_file)

    def test_a_blank_value_in_the_file_also_fails_loud(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # A third door, and the one that reaches the wire: dotenv returns ``""`` for
        # ``KEY=``; a build that forwarded it would hand the counter an empty
        # ``x-api-key`` header and 401 on every request instead of failing at load.
        monkeypatch.delenv(ANTHROPIC_API_KEY_ENV, raising=False)
        env_file = tmp_path / "mcp.env"
        env_file.write_text(f"{ANTHROPIC_API_KEY_ENV}=\n", encoding="utf-8")
        with pytest.raises(RuntimeError):
            load_api_key(env_file)


class TestPythonDotenvIsDeclaredAndActuallyUsed:
    """R2's two halves — declared AND adopted, in the RULED module — pinned apart.

    Declared-but-unused is how ``pydantic-settings`` sat in this tree; used-but-
    undeclared is how ``python-dotenv`` sits in it today (it arrives transitively
    through ``pydantic-settings``). *"A transitive pin is somebody else's promise to
    keep"* — ``loremaster/pyproject.toml``'s own words about ``anyio``.
    """

    def test_python_dotenv_is_a_declared_dependency(self) -> None:
        manifest = tomllib.loads(
            (_repo_root() / "loremaster" / "pyproject.toml").read_text(encoding="utf-8")
        )
        declared = {
            requirement.split(">")[0].split("=")[0].split("[")[0].strip().lower()
            for requirement in manifest["project"]["dependencies"]
        }
        assert "python-dotenv" in declared, (
            "python-dotenv is used but not declared — it currently resolves only as a "
            "transitive dependency of pydantic-settings, and breaks the day that chain "
            "drops it, with nothing in our own metadata to prevent it."
        )

    def test_the_ONE_resolver_module_is_what_imports_dotenv(self) -> None:
        # R2 puts the file parsing inside ``resolve_secret``, so
        # ``loremaster/config.py`` is where the import belongs — NOT
        # ``calibration/counting.py``, which is where the earlier (narrowed) ruling
        # would have put it. An import anywhere else is a second lookup wearing the
        # shared package's name.
        from loremaster import config as config_module

        source_path = Path(config_module.__file__)
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "dotenv"
            for alias in node.names
        }
        assert "dotenv_values" in imported, (
            "loremaster/config.py does not import dotenv_values. Ruling R2 names the FUNCTION, "
            f"not just the package — imported from dotenv: {sorted(imported) or 'nothing'}"
        )

    def test_no_other_module_parses_env_files(self) -> None:
        # ONE IMPLEMENTATION, structurally. The behavioural no-mutation pin catches a
        # ``load_dotenv`` in the resolver; this catches a SECOND parser somewhere
        # else, which no behavioural pin would see because nothing calls it yet.
        offenders = [
            display
            for display, source_path in _scanned_python_sources()
            if display != SECRET_RESOLUTION_MODULE
            and any(
                isinstance(node, ast.ImportFrom) and node.module == "dotenv"
                for node in ast.walk(ast.parse(source_path.read_text(encoding="utf-8")))
            )
        ]
        assert not offenders, (
            f"these modules parse .env files outside the one resolver: {offenders}"
        )


# --------------------------------------------------------------------------- #
# The ONE-ENTRY-POINT gate — ALLOWLIST THE SAFE
# --------------------------------------------------------------------------- #
# CLAUDE.md's instrument law: the forbidden set is unbounded, the safe set is
# small and enumerable. Every ``os.environ`` / ``os.getenv`` read in the scanned
# tree needs an entry here. Keyed on the ACCESS, not on any function's name, so a
# resolver that survives under a new name is still caught (six receipts on
# name-keyed gates losing).
#
# Re-derived 2026-07-26 at 9c08cac: 14 grep hits, 11 REAL reads — ``config.py``'s
# module docstring, ``logging_setup.py``'s and ``shellout.py``'s comments are
# prose. The AST excludes prose by construction, which is why the scan is AST and
# not grep (the same 13-vs-10 correction the Phase 0 inventory made for
# ``.get_secret_value()``).
#
# THE RULE, in two parts:
#   1. Exactly ONE module may resolve a SECRET from the environment —
#      :data:`SECRET_RESOLUTION_MODULE`. That is packet 42 Scope IN #2 stated as a
#      property rather than as a function name, so an optional-resolution sibling
#      (needed because ``load_api_key`` must distinguish UNSET from BLANK — see
#      the report's C9 ruling request) does not require a contract edit.
#   2. Every environment read ANYWHERE ELSE is a non-secret operational knob and
#      needs an evidence-backed entry below. A new entry is a DESIGN decision.
SECRET_RESOLUTION_MODULE = "loremaster/config.py"

ENV_READ_ALLOWLIST: dict[str, str] = {
    "loremaster/server.py::_resolve_version": (
        "reads the build-stamped version env var — a public build identifier, rendered in "
        "the server's own honesty line."
    ),
    "loremaster/server.py::configure_logging_from_config": (
        "LORE_LOG_LEVEL override — an operational knob, not a credential."
    ),
    "loremaster/server.py::main": (
        "LORE_CONFIG default for the --config argument — a filesystem path."
    ),
    "scripts/gated_ground.py::_collector_input_fingerprint": (
        "an operational knob read as a CACHE KEY, never as configuration — the inherited value "
        "still decides what is measured. The gated-ground guard memoises its collector subprocess "
        "behind a fingerprint of that subprocess's inputs, and PYTEST_ADDOPTS is one of those "
        "inputs: the child inherits it, so a value that CHANGES inside one process alters what the "
        "collector answers while the key stands still, and the memo then serves a stale healthy "
        "verdict. Reading it here neither resolves nor neutralises anything — the inherited value "
        "is passed through untouched and still governs the child. Granted 2026-07-30 as a NARROW "
        "one-entry scope extension under packet 44 ruling R10, whose rider is that a memo's "
        "invalidation pin is the price of its speed; pinned by "
        "TestTheCollectorIsMemoisedAndTheMemoInvalidates."
    ),
    "scripts/mutation_proof.py::main": (
        "forwards the PARENT environment into a pytest subprocess (``{**os.environ, ...}``); "
        "reads no named variable and resolves nothing."
    ),
    "scripts/search_score_survey.py::_default_output_dir": (
        "SEARCH_SCORE_SURVEY_OUT — an output directory override for a survey script."
    ),
    "scripts/token_survey.py::_default_output_dir": (
        "TOKEN_SURVEY_OUT — an output directory override for a survey script."
    ),
    "skills/lore-deploy/scripts/lore_deploy.py::_loremaster_python": (
        "LORE_PYTHON — an interpreter PATH override, an operational knob, not a credential. ⚠ It "
        "cannot route through the shared resolver BY CONSTRUCTION: this is the function whose "
        "whole job is to FIND an interpreter that HAS loremaster, so it runs before loremaster is "
        "importable. Same stdlib-only deploy boundary as probe_embed.py (R14). Added under R32 "
        "defect 6 — R6 widened the scan over skills/ and this read was never adjudicated."
    ),
    "skills/lore-deploy/scripts/probe_embed.py::_resolve_key": (
        "LEDGERED DESIGN DECISION (ruling R14, 2026-07-26) — NOT an oversight. This script is "
        "deliberately stdlib-only: it runs under sys.executable while loremaster code in the "
        "same skill runs under a separate _loremaster_python(), and lore_deploy.py shells out "
        "to it and BRANCHES ON ITS EXIT CODES. Importing loremaster.config would replace a "
        "clean exit 4 with a KeyError traceback read as exit 1. The duplicate is the price of "
        "that boundary. RE-OPEN TRIGGER: the day probe_embed.py runs under _loremaster_python()."
    ),
    # ``scripts/comms_consumer_eval.py::_amain`` DELETED from this allowlist by
    # ruling R7 (2026-07-26): it read ANTHROPIC_API_KEY directly for a presence
    # check and now migrates to the shared resolver. The operator's reason is worth
    # keeping — migrating costs ~3 lines, less than maintaining the note explaining
    # the exemption, and it keeps every remaining entry ONE justification shape (an
    # operational knob) instead of mixing in a credential read.
}


def _scanned_python_sources() -> list[tuple[str, Path]]:
    """Production packages + ``scripts/``, excluding test trees.

    ⚠ **``skills/lore-deploy/scripts/`` IS SCANNED — ruling R6 (2026-07-26).** It
    holds the FOURTH hand-rolled resolver, ``probe_embed.py::_resolve_key``, which
    returns a bare ``str`` and accepts a whitespace-only value (inventory bug B3,
    alive in a second home). The operator ruled it IN SCOPE: *"ledgering it would
    leave 'ONE entry point' true of the workspace but false of the repo."*

    ⚠ **AND THE RIDER, which is the half that gets dropped:** when R6 was written
    ``skills/`` was outside ``testpaths`` AND outside ``scripts/typecheck.sh``, so
    extending a gate over it means proving the gate RUNS there. It does — this
    scanner lives in ``loremaster/tests/``, which IS collected, and it READS
    ``skills/`` rather than importing it. (Ruling R9 closed the typecheck half
    within that same packet — ``skills`` is its own ``MEMBERS`` iteration — and
    **packet 44 closed the last half on 2026-07-29**: this docstring used to end
    *"so the standing residual is ``testpaths`` alone"*, and there is now no
    residual — ``skills/lore-deploy/{scripts,tests}`` are ``testpaths`` entries and
    their 117 tests run in the standard gate. The rider below is unaffected: it
    proves THIS scanner reaches the tree, which is a different claim from the tree
    having its own gate, and both are now true.)
    :meth:`TestSecretResolutionHasExactlyOneEntryPoint.
    test_the_scan_reaches_the_skills_tree` is the receipt, and it fails loudly if
    the directory ever stops being reached. A guard nobody runs is a hope with a
    filename, and both of packet 03b's instruments were victims of exactly that.
    """
    # ⚠ REWIRED to the ONE shared root list (see ``_logging_fixtures``). This
    # carried a private copy that did NOT include ``lorerunes`` — so the gate whose
    # property is "ONE secret-resolution entry point in the workspace" was not
    # looking at a workspace member. Property right, reach short.
    return production_sources()


def _environment_reads() -> list[str]:
    """Every ``os.environ`` / ``os.getenv`` access, keyed ``path::function``."""
    found: list[str] = []
    for display, source_path in _scanned_python_sources():
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        enclosing: dict[int, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for inner in ast.walk(node):
                    enclosing.setdefault(id(inner), node.name)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in {"environ", "getenv"}:
                found.append(f"{display}::{enclosing.get(id(node), '<module>')}")
    return sorted(set(found))


class TestSecretResolutionHasExactlyOneEntryPoint:
    """Packet 42 Scope IN #2, enforced as an ALLOWLIST OF THE SAFE.

    THE THREAT MODEL: this gate catches the HONEST developer who adds a fourth
    ``os.environ.get("SOME_KEY")`` because it was easier than importing the
    resolver — which is precisely how the existing three were born. It is NOT a
    boundary against a hostile author, who can read the environment a dozen other
    ways. Verdicts follow: *"a clever author could use ``os.popen('env')``"* is
    not a defect here; *"a new hand-rolled resolver ships unnoticed"* is.
    """

    def test_the_scan_finds_the_population(self) -> None:
        # POSITIVE CONTROL: an AST walk that silently matched nothing would make
        # every assertion below pass vacuously.
        reads = _environment_reads()
        assert len(reads) >= 6, f"the env-read scan found only {len(reads)} sites: {reads}"
        assert any(read.startswith(f"{SECRET_RESOLUTION_MODULE}::") for read in reads), (
            "the scan cannot even see the known entry point — the instrument is broken, "
            "not the code"
        )

    def test_the_scan_reaches_the_skills_tree(self) -> None:
        # ⚠ R6's RIDER, and the reason it is a test rather than a claim in a report.
        # When R6 was written ``skills/`` was outside ``testpaths`` (ruling R9
        # brought it INSIDE ``scripts/typecheck.sh`` in that same packet, but not
        # inside pytest; packet 44 added the ``testpaths`` entries on 2026-07-29).
        # Extending a gate over ungated ground is worthless unless the gate RUNS
        # there — a guard nobody runs is a hope with a filename (2026-07-26 law;
        # both of packet 03b's instruments were victims of the class they
        # instrument). This scanner runs because it lives in ``loremaster/tests/``
        # and READS ``skills/`` rather than importing it; this pin is the receipt,
        # and it goes RED the day the directory stops being reached.
        scanned = {display for display, _ in _scanned_python_sources()}
        assert any(display.startswith("skills/") for display in scanned), (
            "the scan reaches no file under skills/ — ruling R6 put that tree in scope, and "
            "a gate that cannot see it is exempting it silently"
        )
        assert "skills/lore-deploy/scripts/probe_embed.py" in scanned, (
            "probe_embed.py is not in the scanned population — it is the FOURTH resolver R6 "
            "ruled in scope, and the whole point of extending the scan"
        )
        # And the exclusions still hold on the new root: its inline test files and
        # its tests/ directory must not be governed as production sources.
        assert not any(
            display.startswith("skills/") and "test_" in Path(display).name for display in scanned
        ), "the skills/ scan is picking up test files as production sources"

    def test_probe_embed_keeps_its_own_resolver_as_a_LEDGERED_duplicate(self) -> None:
        # ⚠ RULING R14 REVERSES R6's MIGRATION HALF. R6 originally ruled
        # ``probe_embed.py::_resolve_key`` should adopt the shared resolver; the
        # adversary found that would BREAK THE DEPLOY PATH. The script is
        # deliberately stdlib-only, runs under ``sys.executable`` (loremaster code
        # in the same skill runs under a separate ``_loremaster_python()``), and
        # ``lore_deploy.py`` shells out to it and BRANCHES ON ITS EXIT CODES —
        # importing ``loremaster.config`` would replace a clean exit 4 with a
        # ``KeyError`` traceback read as exit 1.
        #
        # So the duplicate is a **LEDGERED DESIGN DECISION**, which is what ONE
        # IMPLEMENTATION actually prescribes — *"duplication is a DESIGN decision,
        # not a coding one; escalate it"*. We escalated; the boundary is real.
        # **RE-OPEN TRIGGER: the day ``probe_embed.py`` runs under
        # ``_loremaster_python()``, the boundary is gone and it migrates.**
        #
        # This pin asserts the duplicate is STILL THERE, so a future agent cannot
        # "helpfully" consolidate it and silently break the deploy without this
        # going RED and telling them why.
        reads = set(_environment_reads())
        assert "skills/lore-deploy/scripts/probe_embed.py::_resolve_key" in reads, (
            "probe_embed no longer reads the environment itself. If you migrated it to the "
            "shared resolver, STOP — R14: it is stdlib-only by design and lore_deploy branches "
            "on its exit codes. If the re-open trigger fired (it now runs under "
            "_loremaster_python()), delete this pin and say so."
        )

    def test_probe_embed_imports_nothing_outside_the_stdlib(self) -> None:
        # R14's other half, and the property the ledgered duplicate BUYS. A pin on
        # the imports, because that is the boundary — not on the resolver's shape.
        package_file = loremaster.__file__
        assert package_file is not None
        workspace_root = Path(package_file).resolve().parent.parent.parent
        source_path = workspace_root / "skills" / "lore-deploy" / "scripts" / "probe_embed.py"
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                roots.add(node.module.split(".")[0])
        non_stdlib = sorted(roots - set(sys.stdlib_module_names))
        assert not non_stdlib, (
            "probe_embed.py imports outside the stdlib. It runs under sys.executable, which "
            "is NOT guaranteed to have loremaster installed, and lore_deploy branches on its "
            f"exit codes (R14): {non_stdlib}"
        )

    def test_the_scan_excludes_prose(self) -> None:
        # The 13-vs-10 correction, generalised: ``config.py``'s module docstring,
        # ``logging_setup.py``'s docstring and ``shellout.py``'s comment all
        # mention ``os.environ`` (14 grep hits vs 11 real reads, measured
        # 2026-07-26 at 9c08cac). An AST scan cannot see prose; a grep-based gate
        # would have inflated the population and forced meaningless entries.
        reads = _environment_reads()
        assert "loremaster/shellout.py::<module>" not in reads
        assert "loremaster/logging_setup.py::configure_logging" not in reads

    def test_every_environment_read_is_the_entry_point_or_allowlisted(self) -> None:
        unlisted = [
            read
            for read in _environment_reads()
            if not read.startswith(f"{SECRET_RESOLUTION_MODULE}::") and read not in ENV_READ_ALLOWLIST
        ]
        assert not unlisted, (
            "these sites read the environment outside the ONE secret-resolution module and "
            "have no allowlist entry. If a site resolves a CREDENTIAL it must go through "
            f"{SECRET_RESOLUTION_MODULE} (packet 42 Scope IN #2: ONE entry point). If it is "
            "an operational knob, add an evidence-backed entry — a new entry is a DESIGN "
            "decision, not a lint fix:\n  " + "\n  ".join(unlisted)
        )

    def test_no_allowlist_entry_is_stale(self) -> None:
        # BOTH DIRECTIONS. An entry naming no live site is a lie that quietly
        # pre-licenses a future read at that address — the same both-ways diff
        # ``scripts/mutation_proof.py`` performs on declared-RED node ids.
        reads = set(_environment_reads())
        stale = [key for key in ENV_READ_ALLOWLIST if key not in reads]
        assert not stale, (
            f"these ENV_READ_ALLOWLIST entries name no live site — delete them: {stale}"
        )

    def test_the_retired_resolvers_read_nothing(self) -> None:
        # The three sites packet 42 consolidates, named so their disappearance is
        # asserted rather than inferred from the allowlist's silence.
        reads = set(_environment_reads())
        survivors = {
            "loresigil/factory.py::_resolve_api_key",
            "scripts/token_survey.py::load_api_key",
            "loremaster/calibration/counting.py::load_api_key",
            # Ruled MIGRATE by R7.
            "scripts/comms_consumer_eval.py::_amain",
        } & reads
        assert not survivors, (
            "these hand-rolled resolvers still read the environment directly. Packet 42 "
            f"Scope IN #2 consolidates them onto {SECRET_RESOLUTION_MODULE}: {sorted(survivors)}"
        )

    def test_every_allowlist_entry_carries_a_reason(self) -> None:
        # Evidence-backed, never a bare name (CLAUDE.md: every exemption in a
        # deny-by-default safe set is evidence-backed, never "it looks fine").
        reasonless = [key for key, reason in ENV_READ_ALLOWLIST.items() if len(reason) < 40]
        assert not reasonless, f"these allowlist entries have no real justification: {reasonless}"
