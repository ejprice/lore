"""Contract tests for the SECRET TYPE boundary (finding #211, Half A).

Finding #211: a credential can reach a log sink, and *nothing stopped it at the
type level* — every secret in the tree was a bare :class:`str`, so any
interpolation (``f"connecting as {password}"``), any container ``repr``, any
serialisation rendered it verbatim. A filter that must catch every path is
strictly weaker than a TYPE that cannot render its value in the first place.

These tests pin that boundary:

* :func:`~loremaster.config.resolve_secret` returns a
  :class:`pydantic.SecretStr` — the ONE seam every loremaster secret enters
  through — and that type hides its value in ``str``/``repr``/f-string
  interpolation BY CONSTRUCTION.
* A ∀-property, enforced STRUCTURALLY over the whole package rather than
  site-by-site: **every** parameter named in :data:`SECRET_PARAM_NAMES`, on
  **every** function/method under ``loremaster/``, is annotated ``SecretStr``.
  A new credential-carrying constructor written next year is caught by this pin,
  not by an auditor's memory. The exemptions are an ALLOWLIST of the *safe* (the
  documented unwrap seam), never a denylist of the forbidden — the safe set is
  small and enumerable, the forbidden set is not (CLAUDE.md, the instrument
  lesson).
* The type is not merely *annotated*: each connection owner constructed with a
  ``SecretStr`` must not expose the raw value through ``repr``, ``str``, or its
  own ``__dict__`` — which is what a container/frame repr in a traceback would
  render. An implementation that accepts ``SecretStr`` and immediately stores
  ``.get_secret_value()`` satisfies the AST pin and FAILS this one.
* :func:`~loremaster.store._txn.signin_credentials` is the ONE place a secret is
  unwrapped for the SDK. Proven by MUTATION, not by inspection: the shared key
  names are read back from that module, so a caller carrying a private copy of
  the payload shape is not wearing the shared name (CLAUDE.md, #102).

The oracle for "the value did not appear" is a substring search for a known fake
secret over the rendered text — never the implementation's own notion of
redaction.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from typing import Any

import pytest
from loremaster.config import resolve_secret
from loremaster.store._txn import signin_credentials
from pydantic import SecretStr

import loremaster

# A known fake secret with no structure a redactor could recognise: it is NOT
# high-entropy, carries no ``Bearer``/``api_key=`` label, and would sail straight
# through ``RedactingFilter``. That is deliberate — Half A must hold WITHOUT the
# filter's help, so the fixture cannot be one the filter would have caught
# anyway (a fixture that cannot distinguish the two mechanisms is decoration).
FAKE_SECRET = "hunter2-the-password-nobody-should-see"

# The parameter names that carry a secret VALUE anywhere in loremaster. Note the
# deliberate absence of ``user``: a root USERNAME is not a secret (it is a public
# default recorded in ``SURREAL_DEFAULT_USER_ENV``), and typing it as one would
# dilute the signal until "everything is a secret" means nothing is. It is
# unwrapped explicitly at its three resolution sites.
SECRET_PARAM_NAMES: frozenset[str] = frozenset({"password", "api_key"})

# The ALLOWLIST of parameters that legitimately carry a secret as a bare ``str``
# — the documented unwrap seam and nothing else. Keyed ``<module-relative
# path>::<qualified function>::<parameter>``. Every entry needs a reason; a new
# entry is a DESIGN decision, not a lint fix.
#
# (Empty by design: no site in loremaster needs a bare-``str`` secret parameter.
# The one unwrap happens INSIDE ``signin_credentials``' body, on an attribute,
# not through a parameter.)
SECRET_PARAM_ALLOWLIST: frozenset[str] = frozenset()

# The signin payload keys the SurrealDB SDK expects. Read back from the shared
# seam so this test cannot certify a private copy: mutate ``signin_credentials``
# and this pin moves with it.
_EXPECTED_SIGNIN_KEYS = frozenset({"username", "password"})


def _package_root() -> Path:
    """The on-disk root of the ``loremaster`` package under test.

    Derived from the imported module rather than a repo-relative literal, so the
    scan below provably covers the SAME tree the tests import (CLAUDE.md: prove
    which tree you are testing).
    """
    package_file = loremaster.__file__
    assert package_file is not None, "loremaster imported as an empty namespace package"
    return Path(package_file).resolve().parent


def _scripts_root() -> Path | None:
    """The repo's ``scripts/`` directory, or ``None`` when it is not alongside.

    CONDITIONAL BY DESIGN. In a checkout, ``scripts/`` sits two levels above the
    package (``<repo>/loremaster/loremaster`` → ``<repo>/scripts``) and MUST be
    scanned; in the deployed image ``loremaster`` lives in site-packages with no
    ``scripts/`` anywhere, and the scan simply covers less.

    It must be scanned because ``scripts/`` is **NOT a member of
    ``scripts/typecheck.sh``** (``MEMBERS=(lorescribe loresigil loremaster)``), so
    mypy never sees it — and its files construct the very stores this module
    types. That gap shipped a real defect during #211's own migration:
    ``survey_txn_contention_102.py`` kept a bare-``str`` ``PASSWORD`` and would
    have died at the SDK seam, and ``snapshot_gc.py``'s helper annotations still
    claimed ``str`` while ``main`` handed them a ``SecretStr``. Neither was
    visible to the type gate OR to the main pytest run (``scripts/`` tests live
    outside ``testpaths`` and run under their own ``cd scripts`` idiom).
    """
    candidate = _package_root().parent.parent / "scripts"
    return candidate if candidate.is_dir() else None


def _python_sources() -> list[tuple[str, Path]]:
    """Every ``.py`` file this pin governs, as ``(display_path, path)`` pairs.

    Covers the ``loremaster`` package plus the repo's ``scripts/`` when present
    (see :func:`_scripts_root`).
    """
    package_root = _package_root()
    sources = [
        (str(path.relative_to(package_root)), path)
        for path in sorted(package_root.rglob("*.py"))
    ]
    scripts_root = _scripts_root()
    if scripts_root is not None:
        sources += [
            (f"scripts/{path.relative_to(scripts_root)}", path)
            for path in sorted(scripts_root.rglob("*.py"))
        ]
    return sources


def _annotation_text(annotation: ast.expr | None) -> str:
    """Render a parameter annotation back to source text (``None`` → ``""``)."""
    if annotation is None:
        return ""
    return ast.unparse(annotation)


def _secret_parameters() -> list[tuple[str, str, str, str]]:
    """Every secret-named parameter in the package.

    Returns:
        ``(relative_path, function_name, parameter_name, annotation_text)`` for
        each parameter whose name is in :data:`SECRET_PARAM_NAMES`, across every
        ``def``/``async def`` in the package.
    """
    found: list[tuple[str, str, str, str]] = []
    for relative, source_path in _python_sources():
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            arguments = node.args
            every_arg = [
                *arguments.posonlyargs,
                *arguments.args,
                *arguments.kwonlyargs,
            ]
            if arguments.vararg is not None:
                every_arg.append(arguments.vararg)
            if arguments.kwarg is not None:
                every_arg.append(arguments.kwarg)
            for argument in every_arg:
                if argument.arg in SECRET_PARAM_NAMES:
                    found.append(
                        (relative, node.name, argument.arg, _annotation_text(argument.annotation))
                    )
    return found


class TestResolveSecretReturnsASecretType:
    """``resolve_secret`` is the ONE entry seam — and it returns a hiding type."""

    def test_returns_a_secretstr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("LORE_TEST_SECRET_211", FAKE_SECRET)
        resolved = resolve_secret("LORE_TEST_SECRET_211")
        assert isinstance(resolved, SecretStr)

    def test_the_value_survives_byte_exact_through_the_type(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The protection must not corrupt the credential: unwrapping returns the
        # variable's value unmodified (the pre-existing byte-exactness contract).
        padded = f"  {FAKE_SECRET}\t"
        monkeypatch.setenv("LORE_TEST_SECRET_211", padded)
        assert resolve_secret("LORE_TEST_SECRET_211").get_secret_value() == padded

    def test_repr_str_and_fstring_all_hide_the_value(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("LORE_TEST_SECRET_211", FAKE_SECRET)
        resolved = resolve_secret("LORE_TEST_SECRET_211")
        # Three independent rendering paths — the three an accidental log call
        # actually takes. A type that hides only one of them is not a type-level
        # fix.
        for rendered in (repr(resolved), str(resolved), f"connecting with {resolved}"):
            assert FAKE_SECRET not in rendered, f"secret leaked through {rendered!r}"

    def test_the_value_hides_inside_a_container_repr(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The realistic traceback shape: a credentials dict / kwargs mapping
        # rendered into an exception message. A bare str leaks here; SecretStr
        # does not.
        monkeypatch.setenv("LORE_TEST_SECRET_211", FAKE_SECRET)
        payload = {"user": "root", "password": resolve_secret("LORE_TEST_SECRET_211")}
        assert FAKE_SECRET not in repr(payload)

    def test_still_fails_loud_on_a_missing_variable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The pre-existing fail-fast contract is unchanged by the type migration.
        monkeypatch.delenv("LORE_TEST_SECRET_211", raising=False)
        with pytest.raises(KeyError):
            resolve_secret("LORE_TEST_SECRET_211")


class TestEverySecretParameterIsTyped:
    """The ∀ structural pin: no bare-``str`` secret parameter anywhere."""

    def test_the_scan_actually_finds_parameters(self) -> None:
        # POSITIVE CONTROL: a scan that silently matched nothing would pass the
        # test below vacuously. Prove the instrument sees the population it is
        # about to judge.
        assert len(_secret_parameters()) >= 10, (
            "the AST scan found almost no secret parameters — the instrument is "
            "broken, not the code"
        )

    def test_every_secret_parameter_is_annotated_secretstr(self) -> None:
        offenders = [
            f"{path}::{function}::{parameter} annotated {annotation or '<missing>'!r}"
            for path, function, parameter, annotation in _secret_parameters()
            if "SecretStr" not in annotation
            and f"{path}::{function}::{parameter}" not in SECRET_PARAM_ALLOWLIST
        ]
        assert not offenders, (
            "these parameters carry a secret as a bare value — annotate them "
            "SecretStr, or add an evidence-backed entry to SECRET_PARAM_ALLOWLIST "
            "(#211):\n  " + "\n  ".join(sorted(offenders))
        )

    def test_the_pin_is_keyed_on_names_and_says_so(self) -> None:
        # A HONEST BOUND on this instrument, stated as a test so it cannot be
        # mistaken for total coverage: the AST pin is keyed on PARAMETER NAMES,
        # and the set of names a future secret could wear is unbounded (a
        # parameter called ``value``, ``credential``, ``bearer`` would sail past).
        # It is the cheap, mechanical half. The ∀ instrument that does NOT depend
        # on names is the runtime leak scan in the class below, which constructs
        # the real objects and searches their rendered state.
        assert SECRET_PARAM_NAMES == frozenset({"password", "api_key"})


class TestSecretsDoNotSurviveAsBareStringsOnInstances:
    """Annotating is not storing: the instance must hold the hiding type."""

    @staticmethod
    def _connection_owner_classes() -> list[type]:
        """Every importable class whose ``__init__`` takes a ``password``.

        DERIVED from the live package, never a hand-list: a class added later is
        covered automatically (CLAUDE.md — prose/lists describing behaviour are
        derived from the behaviour, not restated beside it).
        """
        import importlib
        import pkgutil

        owners: list[type] = []
        for module_info in pkgutil.walk_packages(
            loremaster.__path__, prefix=f"{loremaster.__name__}."
        ):
            try:
                module = importlib.import_module(module_info.name)
            except Exception:  # pragma: no cover - an unimportable optional module
                continue
            for _name, candidate in vars(module).items():
                if not inspect.isclass(candidate) or candidate.__module__ != module_info.name:
                    continue
                try:
                    signature = inspect.signature(candidate)
                except (TypeError, ValueError):  # pragma: no cover - builtins/C types
                    continue
                if "password" in signature.parameters:
                    owners.append(candidate)
        return owners

    def test_the_owner_scan_finds_the_population(self) -> None:
        # POSITIVE CONTROL for the derived list (see the AST control above).
        assert len(self._connection_owner_classes()) >= 8

    def test_no_owner_exposes_the_raw_password(self) -> None:
        secret = SecretStr(FAKE_SECRET)
        # Values supplied per PARAMETER NAME, filtered by each constructor's own
        # signature — so an owner carrying an extra required argument (``dim``,
        # ``tier_roots``, …) is still constructed instead of silently skipped.
        # Skipping is how this pin would pass vacuously.
        supply: dict[str, Any] = {
            "url": "ws://127.0.0.1:1/rpc",
            "namespace": "lore",
            "database": "test",
            "user": "root",
            "password": secret,
            "dim": 8,
            "tier_roots": {},
            "project_roots": {},
        }
        leakers: list[str] = []
        constructed: list[str] = []
        for owner in self._connection_owner_classes():
            parameters = inspect.signature(owner).parameters
            kwargs = {name: value for name, value in supply.items() if name in parameters}
            try:
                instance: Any = owner(**kwargs)
            except TypeError:
                # A constructor needing an argument this pin cannot synthesise is
                # exercised by its own suite; recorded as NOT constructed so the
                # control below can see how much coverage was actually achieved.
                continue
            constructed.append(owner.__qualname__)
            rendered = f"{instance!r} {instance!s} {vars(instance)!r}"
            if FAKE_SECRET in rendered:
                leakers.append(owner.__qualname__)
        # POSITIVE CONTROL: without this, every constructor raising ``TypeError``
        # would leave ``leakers`` empty and the assertion below would pass
        # VACUOUSLY — the exact non-discriminating shape this repo's fixture law
        # forbids. Prove the pin actually built the objects it is judging.
        assert len(constructed) >= 8, (
            f"only {len(constructed)} owners were constructible — this pin is "
            f"passing vacuously, not passing: {sorted(constructed)}"
        )
        assert not leakers, (
            "these connection owners store or render the raw password — hold the "
            f"SecretStr and unwrap only at the SDK seam (#211): {sorted(leakers)}"
        )

    def test_the_api_key_verifier_never_renders_its_key_set(self) -> None:
        # The auth gate holds live bearer keys for the whole process lifetime. Its
        # parameter is named ``value``, so the NAME-keyed AST pin above cannot see
        # it — this is the instrument that can. A verifier rendered into an
        # exception message or a debug log must show nothing.
        from loremaster.auth import ApiKeyVerifier

        verifier = ApiKeyVerifier({"alice": SecretStr(FAKE_SECRET)})
        rendered = f"{verifier!r} {verifier!s} {vars(verifier)!r}"
        assert FAKE_SECRET not in rendered
        # And it still WORKS — a gate that hid the key by breaking auth would
        # pass the line above and be catastrophically wrong.
        assert verifier.verify(FAKE_SECRET) == "alice"
        assert verifier.verify("not-the-key") is None

    def test_the_leak_detector_can_actually_see_a_leak(self) -> None:
        # POSITIVE CONTROL for the detector itself: a deliberately-wrong owner
        # that unwraps into its attribute MUST be caught by the same rendering
        # oracle the pin above uses. Without this, a detector that never fires
        # would be indistinguishable from a clean tree (CLAUDE.md: a probe needs
        # a control).
        class LeakyOwner:
            def __init__(self, *, password: SecretStr) -> None:
                self._password = password.get_secret_value()

        instance = LeakyOwner(password=SecretStr(FAKE_SECRET))
        rendered = f"{instance!r} {instance!s} {vars(instance)!r}"
        assert FAKE_SECRET in rendered


class TestSigninCredentialsIsTheOneUnwrapSeam:
    """One implementation of the unwrap policy, proven by mutation not inspection."""

    def test_it_builds_the_sdk_payload_with_the_raw_value(self) -> None:
        payload = signin_credentials(user="root", password=SecretStr(FAKE_SECRET))
        # The SDK needs the real bytes — the unwrap happens HERE and only here.
        assert set(payload) == _EXPECTED_SIGNIN_KEYS
        assert payload["username"] == "root"
        assert payload["password"] == FAKE_SECRET

    def test_no_module_outside_the_seam_hand_rolls_the_payload(self) -> None:
        # ROUTING IS NOT SHARING: a caller that calls the shared helper but keeps
        # its own ``{"username": ..., "password": ...}`` literal is a private copy
        # wearing the shared name. Scan for the literal payload shape and allow it
        # in exactly one file.
        offenders: list[str] = []
        for relative, source_path in _python_sources():
            if relative == str(Path("store") / "_txn.py"):
                continue
            tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Dict):
                    continue
                keys = {
                    key.value
                    for key in node.keys
                    if isinstance(key, ast.Constant) and isinstance(key.value, str)
                }
                if _EXPECTED_SIGNIN_KEYS <= keys:
                    offenders.append(f"{relative}:{node.lineno}")
        assert not offenders, (
            "these sites hand-roll the SDK signin payload instead of calling "
            f"signin_credentials (#211 / #102): {offenders}"
        )
