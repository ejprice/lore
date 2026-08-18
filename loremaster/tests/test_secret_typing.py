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
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

import pytest
from _logging_fixtures import (
    assert_scan_reached_every_member,
    parse_production_trees,
    production_sources,
)
from loremaster.config import resolve_secret
from loremaster.store._txn import signin_credentials
from pydantic import SecretStr, ValidationError

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


# The trees these pins govern, as ``(display_label, path_relative_to_workspace)``.
#
# ⚠ WIDENED BY PACKET 42 (2026-07-26) from ``loremaster`` + ``scripts`` to the
# WHOLE WORKSPACE. Packet 42 scope item 1 is *"loresigil's embedder keys are
# still bare ``str``"* — a gap that existed precisely because the #211 ∀ pin
# stopped at the package boundary. A structural pin that does not cover a
# package is a pin that package is exempt from, silently.
# ⚠ THE SHARED-PREDICATE PACKAGE'S NAME LIVES HERE, ONCE — and the single-constant
# shape earned its keep within the hour: the operator ruled a different name from
# the one first proposed WHILE this contract was being written, and adopting it
# cost exactly one line instead of a sweep across four files.
#
# **``lorerunes``, PLURAL, and the plural IS the ruling** (operator, 2026-07-27).
# Per the global naming convention — *"once a name is chosen for a concept, use
# that exact name everywhere"* — a stray singular is a bug, not a typo. Ruling R29
# mints it to hold the blankness predicate that BOTH
# ``loremaster.config.resolve_secret`` and ``loresigil``'s ``api_key`` validator
# call.
SHARED_PREDICATE_PACKAGE = "lorerunes"

# The predicate itself: ONE implementation of "what counts as blank", so the two
# callers cannot disagree. Pinned by name because the mutation proof below has to
# be able to find and patch it.
BLANKNESS_PREDICATE = "is_blank"

# ⚠ ``_SCANNED_MEMBERS`` (the per-file ``(label, relative_dir)`` hand-list) is RETIRED
# (F4 / #279 / A-SUB-4): it was a #291-shaped private copy of "which members exist" that
# went STALE on #251. The member set now comes from the SHARED derivation — the trees are
# parsed by ``parse_production_trees`` and coverage is asserted by
# ``assert_scan_reached_every_member`` (both read ``[tool.uv.workspace] members`` from
# pyproject), so a new member is covered by running the suite, never by editing a tuple here.

# ``scripts/`` is scanned even though it is NOT one of ``scripts/typecheck.sh``'s
# ``MEMBERS``, so mypy never sees it — and its files construct the very stores
# this module types. (The MEMBERS list is deliberately not quoted here: packet 42
# changed it, and a comment quoting a list it does not own goes stale the next
# time somebody does.) That gap shipped a real defect during #211's own
# migration: ``survey_txn_contention_102.py`` kept a bare-``str`` ``PASSWORD``
# and would have died at the SDK seam, and ``snapshot_gc.py``'s helper
# annotations still claimed ``str`` while ``main`` handed them a ``SecretStr``.
# Neither was visible to the type gate OR to the main pytest run.
#
# ⚠ ``skills/`` IS SCANNED (ruling R6), and it was ungated ground when that
# ruling was written — outside ``testpaths`` AND outside ``scripts/typecheck.sh``.
# Ruling R9 closed the second half in packet 42 (``skills`` is its own ``MEMBERS``
# iteration). ⚠ CORRECTED 2026-07-29: this comment used to end "so today the
# residual is ``testpaths`` alone" — packet 44 closed that half too, so there is
# no residual; ``skills/lore-deploy/{scripts,tests}`` are ``testpaths`` entries
# and their 117 tests run in the standard gate. Extending
# a gate over ground nothing else checks is only worth anything if the gate RUNS
# there, so that is asserted rather than assumed: these scanners live in
# ``loremaster/tests/``, which IS collected, and they READ the tree rather than
# importing it. ``test_the_scan_reaches_every_workspace_member`` is the receipt.


def _python_source_trees() -> list[tuple[str, ast.Module]]:
    """Every PRODUCTION ``.py`` file these pins govern, as ``(display_path, ast.Module)``.

    Parsed by the SHARED ONE parser (F4 / #279): ``parse_production_trees`` does the compile
    (SANCTIONED at L1's runtime chokepoint), so no private ``ast.parse`` loop escapes it, and
    the retired ``_SCANNED_MEMBERS`` hand-list is gone. Display paths + the production-only set
    (test files excluded — a fixture may legitimately hold a plain-``str`` password) come from
    the shared ``production_sources``, which uses the same member-labelled format the pins'
    allowlists key on (``loresigil/factory.py``). A member directory absent on disk (the
    deployed image carries ``loremaster`` alone) is simply covered less; the positive control
    :meth:`TestEverySecretParameterIsTyped.test_the_scan_reaches_every_workspace_member` is
    what stops that degrading silently in a CHECKOUT.
    """
    workspace_root = _package_root().parent.parent
    trees = parse_production_trees(include_scripts=True, include_skills=True)
    return [
        (display, trees[path.relative_to(workspace_root).as_posix()])
        for display, path in production_sources(include_scripts=True, include_skills=True)
    ]


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
    for relative, tree in _python_source_trees():
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

    def test_the_scan_reaches_every_workspace_member(self) -> None:
        # POSITIVE CONTROL for the WIDENING (packet 42), now routed through the SHARED ONE
        # coverage assertion (F4 / #279): a member directory absent on disk would restore
        # exactly the blind spot that let loresigil keep bare-``str`` keys through the whole of
        # #211. ``assert_scan_reached_every_member`` reads the declared members INDEPENDENTLY
        # from pyproject (never ``derived == derived``), fails closed on an empty scan, and
        # names any member silently exempted. ``extra_roots`` = the non-member trees this pin
        # governs (``scripts`` per R6/R14, ``skills`` per R9).
        scanned = {display: tree for display, tree in _python_source_trees()}
        assert_scan_reached_every_member(scanned, extra_roots=("scripts", "skills"))

    def test_the_pin_is_keyed_on_names_and_says_so(self) -> None:
        # A HONEST BOUND on this instrument, stated as a test so it cannot be
        # mistaken for total coverage: the AST pin is keyed on PARAMETER NAMES,
        # and the set of names a future secret could wear is unbounded (a
        # parameter called ``value``, ``credential``, ``bearer`` would sail past).
        # It is the cheap, mechanical half.
        assert SECRET_PARAM_NAMES == frozenset({"password", "api_key"})

    def test_the_name_keyed_bound_is_covered_by_the_unwrap_allowlist(self) -> None:
        # THE RECONCILIATION packet 42 owes this file, with a RECEIPT rather than
        # a promise. CLAUDE.md's instrument lesson is that enumerating the
        # FORBIDDEN loses — and the pin above is exactly that shape, keyed on two
        # parameter names. The correction is
        # :class:`TestEveryUnwrapSiteIsAllowlisted`, which allowlists the SAFE:
        # it is keyed on the ``.get_secret_value()`` CALL, so it sees credential
        # handling regardless of what the parameter is called.
        #
        # ``ApiKeyVerifier``'s credential parameter is named ``value`` — invisible
        # to SECRET_PARAM_NAMES — yet BOTH of its unwrap sites are governed by the
        # allowlist. That is the proof the two instruments are complementary and
        # not two copies of one blind spot.
        assert "value" not in SECRET_PARAM_NAMES
        auth_entries = [key for key in UNWRAP_ALLOWLIST if key.startswith("loremaster/auth.py::")]
        assert len(auth_entries) == 2, (
            "the unwrap allowlist no longer covers the credential handling the NAME-keyed "
            f"pin above cannot see: {auth_entries}"
        )


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
        for relative, tree in _python_source_trees():
            if relative == f"loremaster/{Path('store') / '_txn.py'}":
                continue
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


# --------------------------------------------------------------------------- #
# PACKET 42 STEP 3 — GATE THE UNWRAP SURFACE (allowlist the safe)
# --------------------------------------------------------------------------- #
# Packet 42 step 3: *"An AST pin over the ``.get_secret_value()`` call sites.
# Each entry is evidence-backed: the unwrapped value goes directly to a client
# call and is not logged, stored, interpolated, or bound to a name that outlives
# the expression. A new unwrap site with no entry is RED. This is CLAUDE.md's own
# instrument law — the forbidden set is unbounded; the safe set is small and
# enumerable."*
#
# ⚠ THE PACKET'S CRITERION AS WRITTEN IS FALSE OF SEVEN OF THE TEN SITES, and
# saying so is the point of this block rather than a quibble. Measured
# 2026-07-26 at 9c08cac:
#   * five sites bind the unwrapped value to a local (``surreal_user = ...``)
#     that outlives the expression — but the value is a root USERNAME, which
#     ``store/_txn.py::signin_credentials`` documents as *deliberately NOT a
#     secret*;
#   * two sites bake the unwrapped bytes into a long-lived ``self._headers``
#     mapping — which is the minimum surface an authenticated HTTP client can
#     have, since the client must hold the credential to send it.
# So "not stored, not bound" cannot be the literal test. What IS testable, and
# what each entry asserts, is a CLOSED SET of evidence CATEGORIES, each of which
# is a reason the unwrap is safe. A site that fits none of them is a design
# decision, not a lint fix. The category set itself is pinned closed below, so
# inventing a seventh category to launder a new unwrap reddens.
# ⚠ ``NOT_A_SECRET`` IS RETIRED BY RULING R17 (#226 rider, 2026-07-26). Five of the
# original ten entries were the SAME pointless round-trip — ``resolve_secret`` wrapping
# the SurrealDB USERNAME, a non-secret, at a site that immediately unwrapped it again.
# The consolidated seam wraps ONLY secrets; a non-secret config read gets a plain read,
# so those five sites stop unwrapping and stop needing an entry. **The allowlist goes
# 10 -> 5 pre-existing entries** (+1 for loresigil's new seam = 6 total).
#
# RE-DERIVED, NOT INHERITED (the rider claims "its author got 1 of 5 sites wrong";
# this contract's standing law is to re-derive every inherited count). Measured
# 2026-07-26 at 720e26a — all five ARE genuine username round-trips and the claim
# does NOT reproduce as a mis-identification:
#     index/cli.py:112 · server.py:6752 · scout.py:728        -> config.surreal.user_env
#     search_score_survey.py:696 -> DEFAULT_SURREAL_USER_ENV  · snapshot_gc.py:332 -> args.user_env
# and all five PASSWORD siblings (cli:113, server:6753, scout:729, survey:697, gc:333)
# verifiably STAY wrapped — the dangerous direction is un-wrapping a real secret while
# tidying away a fake one, and it does not occur.
# ⚠ ONE site IS materially different, which is the grain of truth: ``snapshot_gc.py:332``
# is the only one of the five whose ``KeyError`` is CAUGHT — ``main`` renders it as a
# clean ``_EXIT_ERROR`` message. Dropping ``resolve_secret`` there must keep raising a
# NAMING ``KeyError`` or the CLI's error message silently degrades.
SDK_PAYLOAD = "sdk-payload: handed straight into the SDK call that needs the bytes on the wire"
AUTH_HEADER = "auth-header: baked into an HTTP client's header map and held nowhere else"
CONSTANT_TIME_COMPARE = "constant-time-compare: encoded for hmac.compare_digest, never bound"
EMPTINESS_GUARD = "emptiness-guard: tested for truthiness only; the value is never bound"

UNWRAP_EVIDENCE_CATEGORIES: frozenset[str] = frozenset(
    {SDK_PAYLOAD, AUTH_HEADER, CONSTANT_TIME_COMPARE, EMPTINESS_GUARD}
)

# Keyed ``<display path>::<enclosing function>``. Every entry needs a category; a
# new entry is a DESIGN decision, not a lint fix.
UNWRAP_ALLOWLIST: dict[str, str] = {
    "loremaster/auth.py::verify": CONSTANT_TIME_COMPARE,
    "loremaster/auth.py::add_key": EMPTINESS_GUARD,
    # ⚠ RE-DERIVED under R32 against the CURRENT design. This entry was
    # ``counting.py::__init__`` — an address R19 then made IMPOSSIBLE, because
    # shape B forbids building auth headers at construction. The property was
    # right; the address was two rulings stale.
    "loremaster/calibration/counting.py::build_auth_headers": AUTH_HEADER,
    "loremaster/store/_txn.py::signin_credentials": SDK_PAYLOAD,
    # Was ``voyage_http.py::build_bearer_client``; R26 moved the unwrap into the
    # typed seam, because the header literal must sit inside ``build_auth_headers``
    # (the construction gate's only exemption) and the unwrap goes where the header
    # string is built.
    "loresigil/voyage_http.py::build_auth_headers": AUTH_HEADER,
    # NEW under R29: the validator must hand a ``str`` to ``lorerunes.is_blank``.
    # This is a real second loresigil unwrap, not a leak — see
    # ``test_loresigil_has_exactly_the_two_unwraps_its_rulings_require``.
    "loresigil/factory.py::_reject_a_blank_credential": EMPTINESS_GUARD,
    # ``scripts/token_survey.py::__init__`` is GONE, not moved: the sync counter
    # imports the shared seam instead of owning a copy. That is R22 working.
}


def _unwrap_sites() -> list[str]:
    """Every ``.get_secret_value()`` CALL, keyed ``<display path>::<function>``.

    AST, never grep — and that difference is load-bearing. Measured 2026-07-26 at
    9c08cac, a grep for ``get_secret_value`` returns **13** hits of which only
    **10** are call sites: ``config.py``'s ``resolve_secret`` docstring and two
    lines of ``store/_txn.py``'s ``signin_credentials`` docstring are PROSE. The
    packet's own measurement table says "13 call sites"; the Phase 0 inventory
    corrected it to 10. An AST scan cannot make that mistake, because it never
    sees a docstring as a call.
    """
    found: list[str] = []
    for display, tree in _python_source_trees():
        enclosing: dict[int, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for inner in ast.walk(node):
                    enclosing.setdefault(id(inner), node.name)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get_secret_value"
            ):
                found.append(f"{display}::{enclosing.get(id(node), '<module>')}")
    return sorted(set(found))


class TestEveryUnwrapSiteIsAllowlisted:
    """Packet 42 step 3 — the unwrap surface is a CLOSED, evidence-backed set.

    THE THREAT MODEL, stated IN the instrument (CLAUDE.md: a gate needs one).
    This gate catches the **HONEST developer** who unwraps a ``SecretStr`` for
    convenience — to log it while debugging, to stash it on an attribute, to
    build a connection string — and leaves the bare value somewhere a traceback
    or a ``repr`` can render it. It is **NOT** a boundary against a hostile
    author: anyone who can commit here can read ``secret._secret_value``,
    ``vars(secret)``, or ``secret.__dict__`` and never touch the method this scan
    is keyed on. Verdicts follow mechanically: *"a determined author reads the
    private attribute"* is not a defect for this gate; *"a new unwrap ships
    unnoticed"* is.

    **KNOWN BOUNDS (pinned, not hidden) — THREE honest spellings this gate does not
    see**, two of them named by the adversary's residuals:

    1. **Attribute access.** ``pydantic.SecretStr`` stores its payload on
       ``_secret_value`` (verified 2026-07-26: ``vars(SecretStr('abc')) ==
       {'_secret_value': 'abc'}``), so ``s._secret_value`` bypasses the scan.
    2. **The bound-method alias.** ``g = s.get_secret_value; g()`` — the CALL node's
       ``func`` is a bare ``Name``, not an ``Attribute``, so the AST predicate never
       matches. This is an *honest* spelling (it appears in comprehensions and
       partials), which is why it is named rather than denied.
    3. **The laundering helper.** An allowlisted wrapper launders every caller:
       ``def _key(s): return s.get_secret_value()`` gets ONE entry and then any
       number of sites call ``_key``. **Entries must therefore be LEAF call sites** —
       a helper whose only job is to unwrap is not an entry, it is a hole with a
       name. Judged at review; not mechanically enforced.

    The scan is keyed on the
    ``.get_secret_value()`` CALL. ``pydantic.SecretStr`` stores its payload on
    ``_secret_value``, so attribute access bypasses this instrument entirely.
    None of the three is closed, because closing them receiver-blind would refuse
    legitimate code across the tree, and a gate that refuses honest code is a gate
    that gets switched off. **RE-OPEN TRIGGER:** if a credential is ever found to
    have escaped through any of the three, close that one and accept the false
    positives.
    """

    def test_the_scan_finds_the_population(self) -> None:
        # POSITIVE CONTROL. A scan that silently matched nothing would make the
        # ∀ pin below pass vacuously — the exact non-discriminating shape this
        # repo's fixture law forbids.
        sites = _unwrap_sites()
        # ⚠ R32 defect 1: this said ``>= 8``, a threshold NO ruled design reaches,
        # while its sibling asserted ``<= 7`` and §0.9 said 6. Two pins in one
        # class disagreeing about one number is the two-populations defect wearing
        # a floor. Measured against the current design: **6**.
        assert len(sites) >= 5, f"the unwrap scan found only {len(sites)} sites: {sites}"

    def test_the_scan_counts_calls_not_grep_hits(self) -> None:
        # The 13-vs-10 correction, asserted rather than described. Three of the
        # thirteen grep hits are prose inside docstrings; none may appear here.
        sites = _unwrap_sites()
        assert "loremaster/config.py::resolve_secret" not in sites, (
            "the scan is matching DOCSTRING PROSE — resolve_secret's docstring mentions "
            "get_secret_value() and does not call it"
        )
        assert sites.count("loremaster/store/_txn.py::signin_credentials") == 1, (
            "signin_credentials' docstring mentions get_secret_value() twice and calls it "
            "once; the scan must see exactly the call"
        )

    def test_every_unwrap_site_has_an_evidence_backed_entry(self) -> None:
        unlisted = [site for site in _unwrap_sites() if site not in UNWRAP_ALLOWLIST]
        assert not unlisted, (
            "these sites unwrap a SecretStr with no entry in UNWRAP_ALLOWLIST. Adding one is "
            "a DESIGN decision: state which evidence category makes the unwrap safe, and "
            "check that the bare value cannot outlive the expression in a form a repr or a "
            "traceback would render (packet 42 step 3):\n  " + "\n  ".join(unlisted)
        )

    def test_no_allowlist_entry_is_stale(self) -> None:
        # BOTH DIRECTIONS, because a stale entry silently pre-authorises a future
        # unwrap at that address. This is the same both-ways diff
        # ``scripts/mutation_proof.py`` performs on declared-RED node ids, and the
        # direction that catches a "fix" landing in dead code.
        sites = set(_unwrap_sites())
        stale = [key for key in UNWRAP_ALLOWLIST if key not in sites]
        assert not stale, (
            "these UNWRAP_ALLOWLIST entries name no live unwrap site. Delete them — an "
            f"entry that guards nothing is a licence nobody asked for: {stale}"
        )

    def test_every_entry_uses_a_category_from_the_closed_set(self) -> None:
        # The categories are the EVIDENCE. A free-text reason would let a future
        # unwrap be laundered by writing a sentence; a closed set makes inventing
        # a new justification a visible, deliberate act.
        invented = {
            key: evidence
            for key, evidence in UNWRAP_ALLOWLIST.items()
            if evidence not in UNWRAP_EVIDENCE_CATEGORIES
        }
        assert not invented, (
            "these entries use an evidence category that is not in the closed set. A new "
            f"category is a design decision the operator rules on, not a lint fix: {invented}"
        )

    def test_the_category_set_is_closed(self) -> None:
        # And the set itself is pinned, so widening it reddens here first.
        # ``NOT_A_SECRET`` was RETIRED by R17: the five username round-trips it
        # justified are gone, and a category with no members is a door left open.
        assert UNWRAP_EVIDENCE_CATEGORIES == frozenset(
            {SDK_PAYLOAD, AUTH_HEADER, CONSTANT_TIME_COMPARE, EMPTINESS_GUARD}
        )

    def test_only_one_site_unwraps_for_the_surrealdb_sdk(self) -> None:
        # ONE IMPLEMENTATION, restated as a property of the allowlist rather than
        # left to the reader: twelve owners each calling ``get_secret_value()``
        # inline would be twelve copies of the unwrap policy (#102). Exactly one
        # entry may carry the SDK_PAYLOAD category.
        sdk_sites = [key for key, evidence in UNWRAP_ALLOWLIST.items() if evidence == SDK_PAYLOAD]
        assert sdk_sites == ["loremaster/store/_txn.py::signin_credentials"], (
            f"the SDK unwrap policy has more than one implementation: {sdk_sites}"
        )

    def test_no_username_round_trip_survives(self) -> None:
        # RULING R17 (#226), stated as the property rather than as a count: no
        # entry may exist whose justification is "the value is not actually a
        # secret". ``resolve_secret`` now wraps ONLY secrets, so a non-secret
        # config read is a plain read and never reaches this list.
        #
        # The five retired sites, re-derived 2026-07-26 (see the comment on the
        # category constants above): index/cli.py, server.py, scout.py,
        # search_score_survey.py, snapshot_gc.py — all reading a ``*_user_env``.
        retired = [
            key
            for key in UNWRAP_ALLOWLIST
            if any(
                key.startswith(prefix)
                for prefix in (
                    "loremaster/index/cli.py::",
                    "loremaster/scout.py::",
                    "loremaster/server.py::",
                    "scripts/search_score_survey.py::",
                    "scripts/snapshot_gc.py::",
                )
            )
        ]
        assert not retired, (
            "these entries are the USERNAME round-trip R17 retired — resolve_secret should "
            f"not be wrapping a non-secret at all: {retired}"
        )

    def test_the_surviving_entries_are_all_real_credential_unwraps(self) -> None:
        # The positive half: after R17 every remaining entry unwraps a genuine
        # credential at a leaf call site. Five pre-existing + one new loresigil
        # seam = six. Asserted as a BOUND rather than an exact count so adding a
        # justified entry is possible, but doubling the surface is not.
        assert 5 <= len(UNWRAP_ALLOWLIST) <= 7, (
            f"the unwrap surface is {len(UNWRAP_ALLOWLIST)} entries; the ruled design is SIX "
            "— 2 auth.py + 1 SDK payload + 2 typed seams + 1 blankness validator. A jump means "
            "a new category of unwrap that needs an operator decision, not a lint fix."
        )


# --------------------------------------------------------------------------- #
# RULING R26 — ONE TYPED AUTH-HEADER SEAM (the name-list, at its seventh address)
# --------------------------------------------------------------------------- #
# ``W-PARAMNAME-BARE`` — a class holding a bare-``str`` credential under the
# parameter name ``bearer_token`` — leaked into a rendered log line in BOTH
# formats and added ZERO failures, because THREE independent instruments all key
# on NAMES: the sibling sweep on ``"api_key" in parameters``, ``SECRET_PARAM_NAMES``
# on ``{"password", "api_key"}``, and this file's ``UNWRAP_ALLOWLIST`` on a
# ``.get_secret_value()`` call a bare ``str`` never makes.
#
# ⚠ **THE GAP IS REAL; THE LEAK IS NOT.** Verified by the lead and not restated as
# worse than it is: ``bearer_token`` exists in this tree ONLY as
# ``auth.py::_bearer_token``, an INCOMING client token; ``auth.py`` contains ZERO
# logger calls; and per M1 that local renders as ``self._verifier.verify(token)``
# with no value. The wrong build is CONSTRUCTED. Nothing here describes a live leak.
#
# THE RULED SHAPE, which is this packet's own thesis turned on its own instrument:
# stop DETECTING a credential by what it is called, and make a bare ``str`` a TYPE
# ERROR at the last mile.
#
#     def build_auth_headers(credential: SecretStr) -> dict[str, str]: ...
#
# The parameter-name set is unbounded; the type is not. What remains for an AST
# gate is small and STRUCTURAL, and that is the point.
SEAM_FUNCTION = "build_auth_headers"

# The packages that send outgoing credentials. TWO seams, not one shared helper —
# ruling R26 constraint 1: ``loresigil`` cannot import ``loremaster`` (#222), and
# **the enforcement is the TYPE SIGNATURE, not a shared implementation.** Two
# typed seams are not a DRY violation when the shared thing is a type, not a policy.
SEAM_PACKAGES: tuple[str, ...] = ("loremaster", "loresigil")

# R26 constraint 2 — SCOPE IS OUTGOING CREDENTIALS ONLY. The incoming bearer token
# in ``loremaster/auth.py`` is the other direction: we verify it, never send it,
# and it is not in this seam. Over-building here was explicitly ruled against.
_INCOMING_AUTH_MODULE = "loremaster/auth.py"

# The one production file exempt from the seam: stdlib-only by ruling R14, so it
# cannot import a typed seam from either package without breaking the deploy path.
# ⚠ R32 defect 3 — WIDENED FROM ONE FILE TO THE BOUNDARY IT NAMES. R14's exemption
# is *stdlib-only deploy scripts*, and the whole directory is that: none of them can
# import ``SecretStr``, so none can call a typed seam. Keeping it at one filename
# meant two siblings were flagged for things that are not credentials at all — a
# ``Content-Type`` header, and a ``Bearer ${VAR}`` TEMPLATE that
# ``test_secret_leak_vectors``'s sibling sweep had already scoped out with that
# reason.
#
# ⚠ AND THE REASON THIS IS THE RIGHT REPAIR, on the record: the builder could have
# renamed a helper to ``build_auth_headers`` and collected the exemption. It
# refused and said so — that would be a ``str``-typed function wearing a typed
# seam's name, gaming the gate instead of satisfying its property. A gate that can
# be satisfied by a rename is not a gate.
#
# RE-OPEN TRIGGER (inherited from R14): the day any of these scripts runs under
# ``_loremaster_python()``, the stdlib-only boundary is gone and they join the seam.
_STDLIB_ONLY_EXEMPT_ROOT = "skills/lore-deploy/scripts/"

# ⚠ **RULING C1 — THIS WAS A FILENAME SUFFIX, AND THE INSTRUMENT LESSON AT ITS Nth
# ADDRESS.** The exemption for R26 constraint 2 (incoming auth is out of scope) was
# ``display.endswith("auth.py")``. Measured: ``oauth.py``, ``xauth.py``,
# ``jwt_auth.py`` and ``reauth.py`` are ALL exempt under that test, and the Phase-7
# reviewer walked a byte-identical offender through as ``oauth.py``.
#
# An EXACT PATH, because the safe set here is exactly one file — the one module
# that verifies an INCOMING client token. A suffix is a pattern; a path is a fact.
_INCOMING_AUTH_EXEMPT = "loremaster/auth.py"

# ⚠ EXEMPT (regr-fixer, packet 59) — the fastmcp migration SPIKE exercises raw
# fastmcp/MCP auth plumbing the typed seam does NOT cover, so no site can route
# through it. EVIDENCE (every one of its six flagged sites read):
#   * ``build_auth_headers(credential: SecretStr)`` produces a FIXED Anthropic
#     token-counting header set — ``{"x-api-key", "anthropic-version",
#     "content-type"}`` — from a wrapped credential (calibration/counting.py).
#   * The spike builds ``Authorization: Bearer <token>`` (a DIFFERENT header name
#     and scheme), a FastMCP SERVER-side ``auth=<verifier>`` object (incoming, not
#     an outgoing header at all), a fastmcp ``Client(auth=BearerAuth(...))`` SDK
#     object, and bare httpx ``headers=`` merges carrying ``Host``/``Accept`` and
#     DELIBERATELY-WRONG test tokens (``"Bearer WRONG"``) as negative controls.
#   * None carries a real loremaster/Anthropic credential — they are hardcoded MCP
#     test literals. Routing a "WRONG"-token negative control through a
#     ``SecretStr`` seam that unwraps to ``x-api-key`` is not expressible.
# A path, not a suffix, per the C1 discipline above. RE-OPEN TRIGGER: the day this
# spike sends a REAL credential (an Anthropic ``x-api-key`` from a ``SecretStr``),
# OR ``build_auth_headers`` gains a ``Bearer``-emitting overload — either makes a
# site expressible through the seam, and the exemption must go.
_FASTMCP_SPIKE_EXEMPT = "scripts/fastmcp_migration_spike.py"


def _auth_construction_offenders() -> list[str]:
    """Auth-header construction outside a seam — the v3 gate, both halves.

    ⚠ **THIS SHAPE IS v3. v1 AND v2 BOTH FAILED AND THE FAILURES ARE THE DESIGN.**
    Repo law requires the author of an invented property to attack it before
    shipping; :class:`TestTheSeamGateWasAttackedByItsOwnAuthor` carries the corpus
    and the measured results. In short:

    * **v1** keyed on auth-header NAMES. **6 of 10 invented shapes walked past it.**
    * **v2** keyed on the httpx CONSTRUCTION SURFACE (``headers=``/``auth=``) plus
      ``SecretStr()`` minting. It closed the type bypasses v1 could not see — and
      LOST the ones v1 caught, because a helper that merely *returns* a header dict
      touches no httpx call.
    * **v3 is the union**, and neither half is redundant: each closes exactly what
      the other misses.
    """
    offenders: list[str] = []
    for display, tree in _python_source_trees():
        if (
            display.startswith(_STDLIB_ONLY_EXEMPT_ROOT)
            or display == _INCOMING_AUTH_EXEMPT
            or display == _FASTMCP_SPIKE_EXEMPT
        ):
            # R14 stdlib-only boundary; R26 constraint 2 excludes incoming auth;
            # the fastmcp spike exercises MCP auth plumbing the seam cannot express.
            continue
        enclosing: dict[int, str] = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for inner in ast.walk(node):
                    enclosing.setdefault(id(inner), node.name)
        for node in ast.walk(tree):
            if enclosing.get(id(node)) == SEAM_FUNCTION:
                continue
            if not isinstance(node, (ast.expr, ast.stmt)):
                continue
            offenders += [f"{display}:{node.lineno} {why}" for why in _node_verdicts(node)]
    return offenders


def _node_verdicts(node: ast.expr | ast.stmt) -> list[str]:
    """The v3 gate's per-node verdicts — v1's name leg and v2's surface leg."""
    verdicts: list[str] = []
    # v1's half — an auth-header NAME as a literal.
    if (
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.lower() in AUTH_HEADER_NAMES
    ):
        verdicts.append(f"builds {node.value!r} outside the seam")
    # v2's half — an httpx construction whose headers=/auth= is not from the seam.
    # Never inspects a header NAME, so a computed one cannot slip past this leg.
    if isinstance(node, ast.Call):
        for keyword in node.keywords:
            if keyword.arg in {"headers", "auth"} and not _is_seam_call(keyword.value):
                verdicts.append(f"{keyword.arg}= not sourced from {SEAM_FUNCTION}()")
    # v2's half — direct header mutation.
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "headers"
    ):
        verdicts.append("mutates .headers[...] directly")
    return verdicts


def _is_seam_call(value: ast.expr) -> bool:
    """Is ``value`` a call to the typed seam?"""
    return isinstance(value, ast.Call) and (
        getattr(value.func, "id", None) == SEAM_FUNCTION
        or getattr(value.func, "attr", None) == SEAM_FUNCTION
    )


AUTH_HEADER_NAMES: frozenset[str] = frozenset({"authorization", "x-api-key", "proxy-authorization"})


def _is_secretstr_mint(node: ast.AST) -> bool:
    """Is ``node`` a ``SecretStr(...)`` construction? THE mint predicate.

    ONE implementation, called by both the file scan below and the attack corpus —
    see :class:`TestTheSeamGateWasAttackedByItsOwnAuthor` for why that matters.
    """
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (getattr(func, "id", None) or getattr(func, "attr", None)) == "SecretStr"


def _secretstr_mint_sites() -> list[str]:
    """Every ``SecretStr(...)`` construction — the S6 bypass's gate."""
    sites: list[str] = []
    for display, tree in _python_source_trees():
        sites += [
            f"{display}:{node.lineno}"
            for node in ast.walk(tree)
            if _is_secretstr_mint(node) and isinstance(node, ast.expr)
        ]
    return sites


class TestOutgoingAuthHeadersGoThroughATypedSeam:
    """R26: a bare ``str`` credential is a TYPE ERROR at the last mile.

    THE THREAT MODEL, stated in the instrument: this catches the **HONEST
    developer** who adds an outgoing auth header and, having a plain ``str`` in
    hand, just uses it. It is NOT a boundary against an author who computes a
    header name to evade a scan — that door is LEDGERED below rather than paid
    for in false positives.
    """

    @pytest.mark.parametrize("package", SEAM_PACKAGES)
    def test_the_package_has_a_typed_seam(self, package: str) -> None:
        import importlib

        module = importlib.import_module(package)
        seam = _find_seam(package)
        assert seam is not None, (
            f"{package} has no {SEAM_FUNCTION}(). R26 requires ONE typed seam PER PACKAGE — "
            "two seams, because loresigil cannot import loremaster (#222) and the enforcement "
            "is the TYPE SIGNATURE, not a shared implementation."
        )
        del module
        annotation = inspect.signature(seam).parameters["credential"].annotation
        assert "SecretStr" in str(annotation), (
            f"{package}'s seam takes {annotation!r}; it must take SecretStr — that annotation "
            "IS the instrument, and it works regardless of what any caller names its variable."
        )

    @pytest.mark.parametrize("package", SEAM_PACKAGES)
    def test_the_seam_rejects_a_bare_str_at_RUNTIME(self, package: str) -> None:
        # ⚠ R26 CONSTRAINT 3 / #221: **mypy is the PREVENTION; a type-gate red is
        # not a demonstrated pin.** The mypy gate is blind through
        # ``dict[str, Any]`` — the SecretStr migration once passed it at zero delta
        # with 119 tests runtime-broken. So the seam must refuse a bare ``str``
        # when actually called, and that refusal is pinned here at runtime.
        seam = _find_seam(package)
        assert seam is not None
        with pytest.raises((TypeError, AttributeError)):
            seam("sk-ant-a-bare-string-not-a-secret")

    @pytest.mark.parametrize("package", SEAM_PACKAGES)
    def test_the_seam_still_produces_the_real_bytes(self, package: str) -> None:
        # Without this, "reject a bare str" is satisfiable by returning nothing —
        # the same trap as the wire pins in test_secret_leak_vectors.py.
        seam = _find_seam(package)
        assert seam is not None
        headers = seam(SecretStr(FAKE_SECRET))
        assert isinstance(headers, dict) and headers, "the seam produced no headers"
        assert any(FAKE_SECRET in value for value in headers.values()), (
            f"{package}'s seam does not put the real credential bytes in any header: {headers}"
        )
        assert any(key.lower() in AUTH_HEADER_NAMES for key in headers), (
            f"{package}'s seam emits no recognised auth header: {list(headers)}"
        )

    def test_no_auth_header_is_built_outside_a_seam(self) -> None:
        offenders = _auth_construction_offenders()
        assert not offenders, (
            "these sites build an outgoing auth header outside the typed seam. R26: route them "
            f"through {SEAM_FUNCTION}(credential: SecretStr), so a bare str is a type error "
            "whatever the variable is called:\n  " + "\n  ".join(offenders)
        )

    def test_secretstr_is_minted_only_where_a_credential_ORIGINATES(self) -> None:
        # Closes attack shape S6: ``build_auth_headers(SecretStr(raw))`` satisfies
        # the type while the value was bare the whole way. The type proves the
        # value is wrapped AT the call, never that it was never bare — so the
        # MINT is gated too. Cheap: 6 production sites today, and 2 of them retire
        # with the resolver consolidation.
        # ADJUDICATED (contract-fix-05aiii, packet 05a-iii): comms_cli.py mints
        # ``SecretStr(args.password)`` from the ``--password`` argv value — a genuine
        # credential ORIGIN. A CLI ``main()`` reading a credential from argv IS a
        # composition root (packet 42 law: only composition roots mint SecretStr),
        # and argv is where that bare value first enters the process, exactly like an
        # env var at ``config.py::resolve_secret``. It is the ONLY mint in the module
        # (the sibling ``resolve_secret`` branch wraps inside config.py, an existing
        # origin). ONE origin added, never a wildcard.
        # ADJUDICATED (regr-fixer, packets 07/07a): the three spike-store probes each mint
        # ``SecretStr("spikeroot")`` — the well-known spike-surreal (TEST store, :18000) root
        # credential literal, NOT a production secret. The store-connect API they call GENUINELY
        # requires a SecretStr and a plain str is not an option: ``signin_credentials(*, user: str,
        # password: SecretStr)`` and ``SurrealStore.__init__(..., password: SecretStr)`` both take
        # SecretStr (#211 — every connection owner holds one), so a bare str is a type error AND a
        # runtime AttributeError at ``password.get_secret_value()``. Same shape as the already-allowed
        # ``survey_txn_contention_102.py`` scripts/ probe. Re-open trigger: if any of these probes ever
        # sources a REAL / production credential (env, argv, secret file) instead of the "spikeroot"
        # literal, it is a genuine credential ORIGIN and must move to config.py's resolver seam.
        allowed = (
            "loremaster/config.py",
            "scripts/survey_txn_contention_102.py",
            "loremaster/comms_cli.py",
            "scripts/probe_query_complexity_07.py",
            "scripts/probe_store_error_classes_07.py",
            "scripts/probe_store_recovery_07a.py",
        )
        offenders = [
            site for site in _secretstr_mint_sites() if not site.startswith(allowed)
        ]
        assert not offenders, (
            "a SecretStr is minted outside a credential ORIGIN. Re-wrapping a bare str at a "
            "call site defeats the typed seam (attack shape S6):\n  " + "\n  ".join(offenders)
        )


def _find_seam(package: str) -> Callable[..., dict[str, str]] | None:
    """Locate ``build_auth_headers`` anywhere in ``package``, by name not address.

    Deliberately address-independent: the contract pins that the seam EXISTS and
    what its signature is, not which module the builder puts it in.
    """
    import importlib
    import pkgutil

    root = importlib.import_module(package)
    for info in pkgutil.walk_packages(root.__path__, prefix=f"{package}."):
        try:
            module = importlib.import_module(info.name)
        except Exception:  # pragma: no cover - optional module
            continue
        candidate = getattr(module, SEAM_FUNCTION, None)
        if callable(candidate):
            return cast("Callable[..., dict[str, str]]", candidate)
    return None


# The shapes I invented against my OWN seam design, with the measured verdict of
# the shipped v3 gate. Repo law (packet 01's three-scanner chain): the author of an
# invented property must build AND break its own shape before shipping it. v1 and
# v2 of that chain failed because nobody required their authors to attack them.
#
# The value is the **attributing instrument**, re-derived against the REAL gate
# under ruling R28.1 — never a boolean, because a boolean let a wrong attribution
# (S6) sit undetected behind a correct outcome.
#   ``_CONSTRUCTION`` = the auth-construction gate flags it.
#   ``_MINT``         = the SecretStr-mint gate flags it.
#   ``_UNCAUGHT``     = a LEDGERED BOUND with a reason, never a silent miss.
_CONSTRUCTION = frozenset({"construction"})
_MINT = frozenset({"mint"})
_UNCAUGHT: frozenset[str] = frozenset()

SEAM_ATTACK_CORPUS: dict[str, tuple[str, frozenset[str]]] = {
    "S1 inline dict literal": ('def go(k):\n    return {"x-api-key": k}\n', _CONSTRUCTION),
    "S2 computed header name": ('H = "x-api" + "-key"\ndef go(k):\n    return {H: k}\n', _UNCAUGHT),
    "S3 module-constant name": (
        'HDR = "authorization"\ndef go(k):\n    return {HDR: f"Bearer {k}"}\n',
        _CONSTRUCTION,
    ),
    "S4 subscript mutation": (
        'def go(req, k):\n    req.headers["authorization"] = f"Bearer {k}"\n',
        _CONSTRUCTION,
    ),
    "S5 httpx auth= kwarg": (
        "import httpx\ndef go(u, p):\n    return httpx.Client(auth=httpx.BasicAuth(u, p))\n",
        _CONSTRUCTION,
    ),
    "S6 re-wrap a bare str": (
        # ⚠ RE-DERIVED under R28.1: this row USED TO SAY "construction". The real
        # gate says otherwise — S6 is caught by the MINT gate, a DIFFERENT function.
        # Outcome always safe; the ATTRIBUTION was wrong, and only a copy of the
        # gate could hide that.
        "def go(raw):\n    return build_auth_headers(SecretStr(raw))\n",
        _MINT,
    ),
    "S7 join-built name": ('def go(k):\n    return {"-".join(["x","api","key"]): k}\n', _UNCAUGHT),
    "S8 credential in URL query": ('def go(b, k):\n    return f"{b}?api_key={k}"\n', _UNCAUGHT),
    "S9 log the seam output": (
        'def go(log, k):\n    h = build_auth_headers(k)\n    log.info("h", extra={"h": h})\n',
        _UNCAUGHT,
    ),
    "S10 CORRECT seam (control)": (
        "def build_auth_headers(credential):\n"
        '    return {"x-api-key": credential.get_secret_value()}\n',
        _UNCAUGHT,
    ),
}


def _instruments_catching(source: str) -> frozenset[str]:
    """Which REAL instrument(s) catch ``source`` — never a re-implementation.

    ⚠ **RULING R28.1 — THIS FUNCTION USED TO BE A COPY OF THE GATE, AND THAT WAS
    THE DEFECT.** The previous ``_gate_flags()`` re-implemented
    :func:`_node_verdicts` inline. The adversary proved it by mutation: it deleted
    v1's name leg from the REAL gate, ``_node_verdicts`` stopped flagging S1,
    ``_gate_flags`` still returned ``True``, and this corpus passed **13/13** while
    adding **zero** failures. **The instrument built to measure the gate's reach
    every run was measuring a duplicate's reach** — #102 (ONE IMPLEMENTATION)
    inside the instrument built to prevent that class, and exactly what *"prove
    sharing by MUTATION"* exists to catch.

    Fixed by **DELETION**, not by keeping a copy in sync — a synchronised copy is
    the same defect with a maintenance ritual attached. This now calls
    :func:`_node_verdicts` and :func:`_is_secretstr_mint` directly, so mutating
    either moves the corpus with it.

    It also returns the **attributing instrument**, not a boolean, because the
    copy had falsified a ledger row: S6 was recorded as caught by the construction
    gate when the real gate says otherwise — outcome safe, attribution wrong, and
    drift undetectable. Attribution is now derived, so it cannot drift again.
    """
    tree = ast.parse(source)
    enclosing: dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for inner in ast.walk(node):
                enclosing.setdefault(id(inner), node.name)
    caught: set[str] = set()
    for node in ast.walk(tree):
        if _is_secretstr_mint(node):
            caught.add("mint")
        if enclosing.get(id(node)) == SEAM_FUNCTION:
            continue
        if isinstance(node, (ast.expr, ast.stmt)) and _node_verdicts(node):
            caught.add("construction")
    return frozenset(caught)


class TestTheSeamGateWasAttackedByItsOwnAuthor:
    """R26's build-AND-break requirement, kept as a running instrument.

    The corpus is not a report artifact — it is a TEST, so the gate's reach is
    **measured on every run** rather than claimed once. If a later change silently
    narrows the gate, the shape it stops catching reddens here.
    """

    @pytest.mark.parametrize(
        "shape", list(SEAM_ATTACK_CORPUS), ids=[k.split()[0] for k in SEAM_ATTACK_CORPUS]
    )
    def test_the_real_gates_verdict_on_each_invented_shape_is_unchanged(self, shape: str) -> None:
        source, expected = SEAM_ATTACK_CORPUS[shape]
        assert _instruments_catching(source) == expected, (
            f"the REAL gate's verdict on {shape!r} changed. If you widened or narrowed an "
            "instrument deliberately, update this row AND the ledger below; if not, a shape "
            "has changed hands or slipped through."
        )

    def test_the_correct_seam_is_not_flagged(self) -> None:
        # POSITIVE CONTROL in the other direction: a gate that flagged everything
        # would "catch" every attack and be worthless.
        source, _ = SEAM_ATTACK_CORPUS["S10 CORRECT seam (control)"]
        assert _instruments_catching(source) == _UNCAUGHT

    def test_the_corpus_calls_the_REAL_gate_and_not_a_copy(self) -> None:
        # ⚠ RULING R28.1, pinned so the defect cannot return. The corpus must be
        # WIRED to the production predicates, not a re-implementation of them.
        # Asserted structurally: ``_instruments_catching`` must actually call
        # ``_node_verdicts`` and ``_is_secretstr_mint``. A future author who
        # "optimises" it back into an inline copy reddens here.
        source = inspect.getsource(_instruments_catching)
        for shared in ("_node_verdicts", "_is_secretstr_mint"):
            assert f"{shared}(" in source, (
                f"the attack corpus no longer calls {shared}() — it is measuring a COPY of the "
                "gate again (R28.1). Fix by DELETION, never by keeping a copy in sync."
            )

    def test_each_instrument_catches_at_least_one_shape(self) -> None:
        # ANTI-VACUITY over the corpus itself, now per-instrument rather than a
        # bare count: if a refactor silently disabled one gate, its shapes would
        # all move to UNCAUGHT and the parametrised rows would still pass.
        attributed = {name for _src, names in SEAM_ATTACK_CORPUS.values() for name in names}
        assert attributed == {"construction", "mint"}, (
            f"an instrument stopped catching anything in the corpus: {sorted(attributed)}"
        )

    def test_the_uncaught_shapes_are_LEDGERED_with_reasons(self) -> None:
        # ⚠ THE HONEST HALF. Four shapes are NOT caught, each recorded with why it
        # is acceptable and what would re-open it.
        #
        # S2 / S7 — a COMPUTED header name (``"x-api" + "-key"``, ``"-".join(...)``).
        #   No name-keyed leg can see these, and the surface leg only fires if the
        #   dict reaches an httpx call in the same function. ACCEPTED under the
        #   threat model: an honest developer writes the header name literally.
        #   RE-OPEN TRIGGER: the day any production module computes a header name.
        #
        # S8 — a credential in a URL QUERY. ⚠ **RULING R28.2: this SHRANK, it did
        #   not dissolve, and the earlier claim was over-stated from a sample of
        #   two.** Measured against the surviving labelled pattern:
        #       COVERED: ?api_key= ?api-key= ?apikey= ?apiKey= ?token= ?secret= ?password=
        #       LEAKS:   ?key=  ?access_token=  ?auth=  ?x_api_key=
        #   So a credential in a query string is covered only when the parameter
        #   happens to be spelled like one of ``_ASSIGNMENT_RE``'s labels. It is not
        #   a header, so it is outside this seam by construction — and the residual
        #   is the four spellings above, not zero.
        #   RE-OPEN TRIGGER: the day lore sends a credential as a query parameter
        #   at all. Today it does not — every outgoing credential is a header.
        #
        # S9 — LOGGING the seam's own output. The seam returns ``dict[str, str]``,
        #   a bare-str container by necessity (httpx needs the bytes). Covered for
        #   every production holder by the retention and shape-B pins in
        #   ``test_secret_leak_vectors.py``; the general case is a bound.
        #   RE-OPEN TRIGGER: a caller binding the seam's result to anything that
        #   outlives the request.
        uncaught = {
            shape for shape, (_src, names) in SEAM_ATTACK_CORPUS.items() if not names
        }
        assert uncaught == {
            "S2 computed header name",
            "S7 join-built name",
            "S8 credential in URL query",
            "S9 log the seam output",
            "S10 CORRECT seam (control)",
        }, (
            "the set of shapes no instrument catches has changed. Every member needs a written "
            f"reason and a re-open trigger in this test's body: {sorted(uncaught)}"
        )

    @pytest.mark.parametrize(
        "spelling,covered",
        [
            ("api_key", True), ("api-key", True), ("apikey", True), ("apiKey", True),
            ("token", True), ("secret", True), ("password", True),
            ("key", False), ("access_token", False), ("auth", False), ("x_api_key", False),
        ],
    )
    def test_the_query_parameter_residual_is_pinned_spelling_by_spelling(
        self, spelling: str, covered: bool
    ) -> None:
        # RULING R28.2 made mechanical. The earlier text claimed S8 "dissolved" on
        # the strength of ONE spelling; four spellings leak. Pinned individually so
        # the boundary is a measured fact rather than a sample, and so widening the
        # label set moves this table with it.
        from loremaster.logging_setup import _ASSIGNMENT_RE, _BEARER_RE, REDACTED

        rendered = f"GET https://api.example/v1/e?{spelling}={FAKE_SECRET}&n=3"
        scrubbed = _BEARER_RE.sub(rf"\1{REDACTED}", rendered)
        scrubbed = _ASSIGNMENT_RE.sub(rf"\1\2{REDACTED}", scrubbed)
        assert (FAKE_SECRET not in scrubbed) is covered, (
            f"?{spelling}= coverage changed. This table is the measured residual for S8; if a "
            "label was added or removed, update it and say so."
        )


class TestTheBlanknessPredicateIsGENUINELYSHARED:
    """**RULING R29 — one implementation of "blank", provable by MUTATION.**

    The operator overturned a local-validator-plus-drift-pin proposal and minted a
    shared workspace member instead, and the reasoning is the part worth keeping:
    **a drift pin is a mechanism for detecting that two copies disagree; one
    implementation cannot disagree with itself.**

    So the pin that matters is not "both callers reject a blank value" — two
    private copies pass that. It is **change the shared predicate and watch BOTH
    callers move**. A caller that stays green is a private copy wearing the shared
    name (#102, and this repo's "prove sharing by mutation" law).

    ⚠ **THE RESOLVER DOES NOT MOVE.** A shared package makes it *possible* for
    ``loresigil`` to resolve secrets again and it must not: R3, the
    composition-root ruling and
    ``test_no_loresigil_module_reads_an_environment_variable`` all stand. **The
    package holds the PREDICATE, not the ENTRY POINT** — pinned below.
    """

    @staticmethod
    def _patch_everywhere(patcher: pytest.MonkeyPatch, replacement: object) -> int:
        """Patch the predicate in EVERY module exposing it; return how many.

        Import-style agnostic ON PURPOSE. ``from lorerunes import is_blank``
        binds at import time, so patching only the defining module would prove
        nothing about a caller that imported the name. Patching every module that
        exposes it covers both styles — and a caller with a genuinely PRIVATE
        implementation (an inline copy, or its own differently-named helper) is
        not patched, does not change, and is therefore caught.
        """
        import sys as _sys

        patched = 0
        for module in list(_sys.modules.values()):
            if module is None or not hasattr(module, BLANKNESS_PREDICATE):
                continue
            patcher.setattr(module, BLANKNESS_PREDICATE, replacement, raising=False)
            patched += 1
        return patched

    def test_the_shared_package_exists_and_owns_the_predicate(self) -> None:
        import importlib

        package = importlib.import_module(SHARED_PREDICATE_PACKAGE)
        predicate = getattr(package, BLANKNESS_PREDICATE, None)
        assert callable(predicate), (
            f"{SHARED_PREDICATE_PACKAGE} does not export {BLANKNESS_PREDICATE}(). R29 mints this "
            "member to hold ONE implementation of 'what counts as blank'."
        )
        # It must actually answer the question both callers ask, over all three
        # blank shapes — this is the semantics ``Field(min_length=1)`` could not
        # provide (it measures LENGTH, so ' ' has length 1 and is accepted).
        for blank in ("", " ", " \t ", "\n"):
            assert predicate(blank) is True, f"{blank!r} must count as blank"
        assert predicate(FAKE_SECRET) is False
        assert predicate(f"  {FAKE_SECRET}  ") is False, (
            "a credential with real leading/trailing whitespace is NOT blank — R1's "
            "byte-exactness rule depends on this distinction"
        )

    def test_the_shared_package_depends_on_nothing_but_the_stdlib(self) -> None:
        # R29: "It depends on nothing but the stdlib." A shared leaf that imports
        # a sibling re-creates the dependency tangle the split exists to avoid —
        # and would make it importable from ``loresigil`` only by dragging
        # ``loremaster`` behind it, re-opening #222.
        package_file = loremaster.__file__
        assert package_file is not None
        workspace_root = Path(package_file).resolve().parent.parent.parent
        root = workspace_root / SHARED_PREDICATE_PACKAGE / SHARED_PREDICATE_PACKAGE
        assert root.is_dir(), f"{SHARED_PREDICATE_PACKAGE} is not a workspace member yet"
        offenders: list[str] = []
        for source_path in sorted(root.rglob("*.py")):
            tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
            for node in ast.walk(tree):
                roots: set[str] = set()
                if isinstance(node, ast.Import):
                    roots = {alias.name.split(".")[0] for alias in node.names}
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    roots = {node.module.split(".")[0]}
                else:
                    continue
                line = node.lineno
                for name in roots - set(sys.stdlib_module_names) - {SHARED_PREDICATE_PACKAGE}:
                    offenders.append(f"{source_path.name}:{line} imports {name}")
        assert not offenders, (
            f"{SHARED_PREDICATE_PACKAGE} must depend on the stdlib only: {offenders}"
        )

    def test_the_shared_package_does_NOT_resolve_secrets(self) -> None:
        # ⚠ The guard on the ruling's own risk. R29 is explicit that a shared
        # package makes it POSSIBLE for loresigil to resolve again. It holds the
        # PREDICATE, not the ENTRY POINT.
        package_file = loremaster.__file__
        assert package_file is not None
        workspace_root = Path(package_file).resolve().parent.parent.parent
        root = workspace_root / SHARED_PREDICATE_PACKAGE / SHARED_PREDICATE_PACKAGE
        assert root.is_dir(), f"{SHARED_PREDICATE_PACKAGE} is not a workspace member yet"
        offenders = [
            f"{path.name}:{node.lineno}"
            for path in sorted(root.rglob("*.py"))
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
            if isinstance(node, ast.Attribute)
            and node.attr in {"environ", "getenv"}
            and isinstance(node, ast.expr)
        ]
        assert not offenders, (
            f"{SHARED_PREDICATE_PACKAGE} reads the environment. It holds the PREDICATE, never "
            f"the ENTRY POINT — R3 and the composition-root ruling stand: {offenders}"
        )

    def test_MUTATING_the_predicate_moves_BOTH_callers(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # **THE PIN THE OPERATOR'S RULING IS WORTH MORE THAN A DRIFT PIN FOR.**
        #
        # ⚠ TWO LEGS, AND THE FIRST ONE IS NOT DECORATION. An earlier draft asserted
        # only the second — that both callers STOP rejecting once the shared
        # predicate is inverted — and building the reference implementation proved
        # that non-discriminating: a caller that **never rejected in the first
        # place** also "stops rejecting", so ``loresigil`` passed this pin while
        # using no shared predicate at all. (That is R29's own defect wearing my
        # pin as camouflage: ``Field(min_length=1)`` accepts ``'   '``.)
        #
        # So the baseline is established HERE, in the same test, before the
        # mutation. A caller that never rejects fails leg 1; a caller with a
        # private copy fails leg 2. Neither leg alone is enough.
        from loresigil.factory import EmbeddingConfig

        blank = "   "

        # LEG 1 — BASELINE, unpatched: both callers reject a blank credential.
        monkeypatch.setenv("LORE_PKT42_SHARED_PREDICATE", blank)
        with pytest.raises(KeyError):
            resolve_secret("LORE_PKT42_SHARED_PREDICATE")
        with pytest.raises(ValidationError):
            EmbeddingConfig(backend="tei", base_url="http://x", api_key=SecretStr(blank))

        # LEG 2 — MUTATION: invert the SHARED predicate so nothing is blank. Both
        # callers must now accept. A caller that still rejects has its own copy.
        patched = self._patch_everywhere(monkeypatch, lambda _value: False)
        assert patched >= 1, "the predicate was not found in any imported module"

        resolved = resolve_secret("LORE_PKT42_SHARED_PREDICATE")
        assert resolved.get_secret_value() == blank, (
            "resolve_secret still rejected a blank value after the SHARED predicate was "
            "inverted — it is using a private copy of the blankness rule (#102)"
        )
        config = EmbeddingConfig(backend="tei", base_url="http://x", api_key=SecretStr(blank))
        assert config.api_key.get_secret_value() == blank, (
            "loresigil's api_key validator still rejected a blank value after the SHARED "
            "predicate was inverted — it is using a private copy (#102)"
        )

    def test_the_mutation_probe_can_actually_SEE_a_change(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # POSITIVE CONTROL for the mutation pin above, which asserts that things
        # STOP failing — a state a broken probe reaches by never having patched
        # anything. Invert the other way: everything is blank, and both callers
        # must now reject a perfectly good credential.
        from loresigil.factory import EmbeddingConfig

        self._patch_everywhere(monkeypatch, lambda _value: True)
        monkeypatch.setenv("LORE_PKT42_SHARED_PREDICATE", FAKE_SECRET)
        with pytest.raises(KeyError):
            resolve_secret("LORE_PKT42_SHARED_PREDICATE")
        with pytest.raises(ValidationError):
            EmbeddingConfig(backend="tei", base_url="http://x", api_key=SecretStr(FAKE_SECRET))


class TestTheInImageGuardCoversEveryWorkspaceMember:
    """**THE SEVENTH — found by sweeping, not by a builder hitting it.**

    R29 mints ``lorerunes`` and names **packet 01a's in-image conformance run
    (#139)** as the instrument that proves the new member reached the deployed
    artifact — consequence 5 of five, and the ruling's own words are that
    forgetting it *"is #131/#139 verbatim"*.

    Measured 2026-07-27 at ``147cf2e``: the ``Containerfile`` **does** carry the
    member (``COPY lorerunes/ /app/lorerunes/``), but
    ``conformance_provenance.WORKSPACE_MEMBERS`` is frozen at the OLD three, so
    **the guard the ruling names cannot see the member the ruling mints.** If
    ``lorerunes`` failed to reach the image, or reached it and would not import,
    the conformance run would pass anyway. That is the artifact-differs-from-the-
    test-environment shape with no instrument looking at it.

    ⚠ **Pinned as a ∀ DERIVED FROM ``pyproject.toml``, never a hand-list** — which
    is the whole lesson of R32. A fifth member added next year is covered by this
    pin rather than by anyone remembering; a pin naming ``lorerunes`` would be
    stale the same way the six R32 defects were.
    """

    @staticmethod
    def _declared_members() -> list[str]:
        import tomllib

        package_file = loremaster.__file__
        assert package_file is not None
        workspace_root = Path(package_file).resolve().parent.parent.parent
        manifest = tomllib.loads((workspace_root / "pyproject.toml").read_text(encoding="utf-8"))
        members: list[str] = manifest["tool"]["uv"]["workspace"]["members"]
        return members

    def test_the_declared_workspace_is_not_empty(self) -> None:
        # POSITIVE CONTROL: a mis-keyed lookup returning [] would make the ∀ pin
        # below pass over nothing.
        members = self._declared_members()
        assert len(members) >= 3, f"the workspace member list looks wrong: {members}"

    def test_the_conformance_run_checks_every_declared_member(self) -> None:
        package_file = loremaster.__file__
        assert package_file is not None
        workspace_root = Path(package_file).resolve().parent.parent.parent
        scripts_root = workspace_root / "skills" / "lore-deploy" / "scripts"
        if str(scripts_root) not in sys.path:
            sys.path.insert(0, str(scripts_root))
        import conformance_provenance  # type: ignore[import-not-found]

        checked = set(conformance_provenance.WORKSPACE_MEMBERS)
        unseen = sorted(set(self._declared_members()) - checked)
        assert not unseen, (
            "the in-image conformance run does not check these workspace members: "
            f"{unseen}. R29 names that run as THE instrument proving a new member reached the "
            "deployed artifact (consequence 5 of five, '#131/#139 verbatim'). A member the "
            "guard cannot see is a member whose absence from the image is invisible until "
            "production. Add it to WORKSPACE_MEMBERS and to the frozen tuple its own test pins."
        )

    def test_the_image_actually_copies_every_declared_member(self) -> None:
        # The other half, and the one that makes the pin above meaningful: the
        # conformance run can only verify what the image contains. Checked against
        # the Containerfile, because a member declared in the workspace and absent
        # from the image is an ImportError at boot, in production only.
        package_file = loremaster.__file__
        assert package_file is not None
        workspace_root = Path(package_file).resolve().parent.parent.parent
        containerfile = (workspace_root / "Containerfile").read_text(encoding="utf-8")
        missing = [
            member
            for member in self._declared_members()
            if f"COPY {member}/" not in containerfile
        ]
        assert not missing, (
            f"the Containerfile does not copy these workspace members: {missing}. They would be "
            "an ImportError at boot, in production only, invisible to every test on this host."
        )


class TestEveryScannerSharesOneRootList:
    """**THE EIGHTH — and it is a CLASS, not an instance.**

    Asked *"what is each instrument's REACH, and is the reach as wide as its
    property?"*, I found four scanners across three contract modules each carrying
    a **private copy** of "which roots does this packet govern":

    | scanner | property | reach before |
    |---|---|---|
    | ONE-ENTRY-POINT env gate | *one secret resolver in the workspace* | missing ``lorerunes`` |
    | M4 locals gate | *no production code renders frame locals* | missing ``lorerunes`` **and** ``skills`` |
    | R2 function-name corpus | *no production name is mangled* | missing ``lorerunes`` |
    | auth-holder sibling sweep | *every auth holder is swept* | missing ``lorerunes``, ``lorescribe`` |

    When ``lorerunes`` was minted, ``_SCANNED_MEMBERS`` was widened and **the other
    four were not** — so three gates and a corpus silently stopped covering a
    workspace member, exactly the way R32's six defects went stale. **That is #102
    in my own instruments**: four call sites needing one POLICY, each cloning it.

    The fix is not to widen four lists — it is that they **call one**, and that one
    is **derived from ``pyproject.toml``** so a fifth member is covered without
    anyone remembering. `_logging_fixtures.workspace_roots` is that function.

    This class is the guard that keeps it true.
    """

    @staticmethod
    def _scanner_labels() -> dict[str, set[str]]:
        """The root labels each scanner actually reaches, measured not declared."""
        import importlib.util

        package_file = loremaster.__file__
        assert package_file is not None
        tests_dir = Path(package_file).resolve().parent.parent / "tests"
        labels: dict[str, set[str]] = {
            "secret_typing": {display.split("/")[0] for display, _ in _python_source_trees()}
        }
        for module_name, function_name in (
            ("test_secret_resolution_seam", "_scanned_python_sources"),
            ("test_secret_leak_vectors", "_workspace_python_sources"),
        ):
            spec = importlib.util.spec_from_file_location(
                module_name, tests_dir / f"{module_name}.py"
            )
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            labels[module_name] = {
                display.split("/")[0] for display, _ in getattr(module, function_name)()
            }
        return labels

    def test_every_scanner_reaches_every_declared_workspace_member(self) -> None:
        import tomllib

        package_file = loremaster.__file__
        assert package_file is not None
        workspace_root = Path(package_file).resolve().parent.parent.parent
        manifest = tomllib.loads((workspace_root / "pyproject.toml").read_text(encoding="utf-8"))
        declared = set(manifest["tool"]["uv"]["workspace"]["members"])

        shortfalls = {
            scanner: sorted(declared - reached)
            for scanner, reached in self._scanner_labels().items()
            if declared - reached
        }
        assert not shortfalls, (
            "these scanners do not reach every declared workspace member, so their ∀ pins are "
            "silently exempting a package — the eighth instance of property-right/reach-short "
            f"in this packet: {shortfalls}"
        )

    def test_all_the_scanners_agree_with_each_other(self) -> None:
        # The DRY property stated directly: they share one list, so they cannot
        # disagree. Two scanners reaching different root sets means one has grown
        # a private copy again, which is how this defect class starts.
        labels = self._scanner_labels()
        distinct = {frozenset(reached) for reached in labels.values()}
        assert len(distinct) == 1, (
            f"the scanners no longer agree on what this packet governs: "
            f"{ {name: sorted(reached) for name, reached in labels.items()} }"
        )

    def test_the_shared_list_is_DERIVED_and_not_a_hand_list(self) -> None:
        # The claim in ``workspace_roots``' own docstring, checked. A future author
        # who "simplifies" it back into a literal tuple reddens here — which is the
        # only thing that stops the class recurring a ninth time.
        from _logging_fixtures import workspace_roots

        source = inspect.getsource(workspace_roots)
        assert "tomllib" in source and "pyproject.toml" in source, (
            "workspace_roots no longer derives the member list from pyproject.toml. A hand-list "
            "is how lorerunes was missed by four scanners at once."
        )
        labels = [label for label, _ in workspace_roots()]
        assert "lorerunes" in labels, "the derived list does not include the newest member"
