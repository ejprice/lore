"""CONTRACT — ``lorerunes`` posture derivation + scope constants (packet 39, design §5).

lore now has THREE legitimate deployment postures and an unbounded set of incoherent
configs. Design §5 rules that the classification is a PURE FUNCTION over primitives —
``derive_posture(host_is_loopback, enabled, mode, has_keys, has_google)`` — living in
``lorerunes`` so its three call sites (``build_asgi_app``, ``lore_deploy.py``'s
start/setup verbs, and ``load_config``) cannot answer differently. Anything that is
not one of the three postures is a REFUSAL naming the nearest posture and the exact
field to change.

WHY A CLOSED SET AND NOT A LIST OF FORBIDDEN SHAPES (CLAUDE.md, the instrument
lesson): *"when you catch yourself enumerating what is FORBIDDEN, you have already
lost — the forbidden set is unbounded; the SAFE set is small and enumerable, so
ALLOWLIST THE SAFE."* This contract therefore pins the three accepting shapes exactly
and asserts that EVERY other point of the input cross-product refuses. A build that
enumerates bad shapes instead passes each named-bad fixture and quietly admits the
combination nobody thought of.

THE WRONG BUILDS THIS DISCRIMINATES AGAINST
* A build that returns ``HOSTED_OAUTH`` for a NON-loopback bind — lore would be
  listening on the LAN/world itself instead of behind lore-caddy on loopback
  (investigation M-2: ``--network=host`` + a wide bind is instant whole-LAN exposure).
* A build that accepts a ``google`` block in ``api_key`` mode — the operator believes
  Google auth is on; it is not, and every request is gated by an API key they may not
  even have configured.
* A build that returns a posture for an UNKNOWN mode string instead of refusing.
* A build that hardcodes posture NAMES into its refusal prose rather than reading them
  off the enum — the prose then survives a rename and teaches a posture that is gone.

⚠ SPEC-SILENT, RESOLVED HERE AND ESCALATED IN THE CONTRACT REPORT: design §5 does not
say what ``mode`` means while ``enabled`` is False. This contract takes the
allowlist-the-safe reading — ``LOOPBACK`` requires the default ``api_key`` mode, and
``enabled: false`` alongside ``mode: google_oauth`` is a diagnosable refusal rather
than a silent LOOPBACK. The alternative reading (mode is inert while disabled) would
let an operator believe hosted auth is configured when nothing is gated at all.
"""

from __future__ import annotations

import inspect
import itertools
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:  # annotations only — resolved by mypy, never imported at runtime
    from lorerunes import Posture, PostureRefusal


# ⚠ ``lorerunes`` SYMBOLS ARE IMPORTED INSIDE EACH FUNCTION, NOT AT MODULE LEVEL.
# This contract is written before the implementation exists, so a module-level import
# would collapse every pin in this file into ONE collection error — and a collection
# error yields NO node ids, which is exactly what ``scripts/mutation_proof.py`` needs
# in order to declare its expected-RED set from ``--collect-only``. Function-local
# imports keep the module collectible and let each pin fail on its own terms.


# The two modes the config's ``Literal`` admits, plus one hostile string. ``mode`` is
# typed ``str`` at this seam (design §5), so a typo that slips past a config boundary
# must be REFUSED here rather than crash or fall through to a posture.
MODE_API_KEY = "api_key"
MODE_GOOGLE_OAUTH = "google_oauth"
MODE_TYPO = "google-oauth"
ALL_MODES = (MODE_API_KEY, MODE_GOOGLE_OAUTH, MODE_TYPO)

# The full input cross-product: 2 × 2 × 3 × 2 × 2 = 48 points. Enumerated rather than
# sampled, because the defects this packet exists to prevent live in the combination
# nobody wrote a fixture for.
CROSS_PRODUCT = tuple(
    itertools.product((False, True), (False, True), ALL_MODES, (False, True), (False, True))
)


def expected_posture(
    host_is_loopback: bool, enabled: bool, mode: str, has_keys: bool, has_google: bool
) -> Posture | None:
    """The SPEC's three accepting shapes (design §5 table); ``None`` means refusal.

    This is an INDEPENDENT restatement of the requirement — the three rows of design
    §5's posture table plus the ruled "everything else refuses" — not a mirror of any
    implementation. It is deliberately written as an allowlist so an input combination
    nobody anticipated lands in the refusal branch by construction.

    Args:
        host_is_loopback: Whether ``server.host`` is a loopback address.
        enabled: The ``auth.enabled`` flag.
        mode: The ``auth.mode`` string.
        has_keys: Whether at least one named API key is configured.
        has_google: Whether a complete ``auth.google`` block is present.

    Returns:
        The expected :class:`Posture`, or ``None`` when the spec requires a refusal.
    """
    from lorerunes import Posture
    if (
        host_is_loopback
        and not enabled
        and mode == MODE_API_KEY
        and not has_keys
        and not has_google
    ):
        return Posture.LOOPBACK
    if enabled and mode == MODE_API_KEY and has_keys and not has_google:
        return Posture.LAN_BEARER
    if enabled and mode == MODE_GOOGLE_OAUTH and has_google and host_is_loopback:
        return Posture.HOSTED_OAUTH
    return None


class TestPostureEnumIsAClosedSet:
    """The posture names are read OFF the enum; a fourth posture is a deliberate act."""

    def test_exactly_three_postures_exist(self) -> None:
        # Freezing the member set makes adding a posture a RED test rather than a
        # silent widening — and it is what lets refusal prose be generated from the
        # enum instead of hand-written (design §5: "a fourth posture is a type error,
        # not a prose edit").
        from lorerunes import Posture
        assert set(Posture) == {Posture.LOOPBACK, Posture.LAN_BEARER, Posture.HOSTED_OAUTH}, (
            "the posture set changed. If that was deliberate, update this pin AND "
            "every refusal-prose generator that enumerates from the enum."
        )

    def test_each_posture_has_a_distinct_name(self) -> None:
        from lorerunes import Posture
        names = [posture.name for posture in Posture]
        assert len(set(names)) == len(names)


class TestDerivePostureAcceptsExactlyTheThreeRuledShapes:
    """The whole 48-point cross-product, table-driven (design §5's rider)."""

    @pytest.mark.parametrize(
        ("host_is_loopback", "enabled", "mode", "has_keys", "has_google"), CROSS_PRODUCT
    )
    def test_every_input_combination_matches_the_spec_table(
        self,
        host_is_loopback: bool,
        enabled: bool,
        mode: str,
        has_keys: bool,
        has_google: bool,
    ) -> None:
        from lorerunes import PostureRefusal, derive_posture
        expected = expected_posture(host_is_loopback, enabled, mode, has_keys, has_google)
        result = derive_posture(
            host_is_loopback=host_is_loopback,
            enabled=enabled,
            mode=mode,
            has_keys=has_keys,
            has_google=has_google,
        )
        inputs = (
            f"host_is_loopback={host_is_loopback} enabled={enabled} mode={mode!r} "
            f"has_keys={has_keys} has_google={has_google}"
        )
        if expected is None:
            assert isinstance(result, PostureRefusal), (
                f"{inputs} is not one of the three ruled postures and must REFUSE; "
                f"got {result!r}. A posture returned for an unruled combination is "
                f"the operator believing a gate is on when it is not."
            )
        else:
            assert result is expected, f"{inputs} must derive {expected!r}; got {result!r}"

    def test_at_least_one_combination_reaches_each_posture(self) -> None:
        # ANTI-VACUITY for the ∀ above: if the expected-table itself never produced a
        # posture, the parametrised test would be a 48-way assertion that everything
        # refuses — and a build that refuses everything would pass it.
        from lorerunes import Posture
        reached = {
            expected_posture(*combination)
            for combination in CROSS_PRODUCT
        }
        assert Posture.LOOPBACK in reached
        assert Posture.LAN_BEARER in reached
        assert Posture.HOSTED_OAUTH in reached
        assert None in reached, "the table must also produce refusals, or the ∀ is one-sided"


class TestDerivePostureNamedShapes:
    """The three postures, named individually so a wrong flip reds by NAME."""

    def test_todays_default_config_with_no_auth_block_is_loopback(self) -> None:
        # The live ``lore.yaml`` at packet-39 time carries NO auth block and binds
        # 127.0.0.1. That deployment must keep working untouched.
        from lorerunes import Posture, derive_posture
        assert (
            derive_posture(
                host_is_loopback=True,
                enabled=False,
                mode=MODE_API_KEY,
                has_keys=False,
                has_google=False,
            )
            is Posture.LOOPBACK
        )

    def test_todays_enabled_api_key_config_is_lan_bearer(self) -> None:
        # The existing networked multi-dev deployment (``lore.yaml.sample``'s auth
        # block: enabled + one named ``*_env`` key) must map to LAN_BEARER, on a
        # NON-loopback bind as well as a loopback one — it is the LAN posture.
        from lorerunes import Posture, derive_posture
        for host_is_loopback in (True, False):
            assert (
                derive_posture(
                    host_is_loopback=host_is_loopback,
                    enabled=True,
                    mode=MODE_API_KEY,
                    has_keys=True,
                    has_google=False,
                )
                is Posture.LAN_BEARER
            )

    def test_hosted_oauth_requires_a_loopback_bind(self) -> None:
        # The proxy comes to us. lore must never be the thing listening off-loopback.
        from lorerunes import Posture, PostureRefusal, derive_posture
        assert (
            derive_posture(
                host_is_loopback=True,
                enabled=True,
                mode=MODE_GOOGLE_OAUTH,
                has_keys=True,
                has_google=True,
            )
            is Posture.HOSTED_OAUTH
        )
        refusal = derive_posture(
            host_is_loopback=False,
            enabled=True,
            mode=MODE_GOOGLE_OAUTH,
            has_keys=True,
            has_google=True,
        )
        assert isinstance(refusal, PostureRefusal)
        assert refusal.nearest is Posture.HOSTED_OAUTH, (
            "one field away from HOSTED_OAUTH must be diagnosed AS hosted — an "
            "operator staring at 'refused' with no nearest posture edits at random"
        )

    def test_hosted_oauth_does_not_require_api_keys(self) -> None:
        # Design §5: in google_oauth mode the ``keys`` list is OPTIONAL. A build that
        # demands keys here refuses a legitimate hosted-only deployment.
        from lorerunes import Posture, derive_posture
        assert (
            derive_posture(
                host_is_loopback=True,
                enabled=True,
                mode=MODE_GOOGLE_OAUTH,
                has_keys=False,
                has_google=True,
            )
            is Posture.HOSTED_OAUTH
        )

    def test_a_google_block_in_api_key_mode_refuses(self) -> None:
        # The operator believes Google auth is on. It is not. Silently ignoring the
        # block is the failure this refusal exists to prevent.
        from lorerunes import PostureRefusal, derive_posture
        result = derive_posture(
            host_is_loopback=True,
            enabled=True,
            mode=MODE_API_KEY,
            has_keys=True,
            has_google=True,
        )
        assert isinstance(result, PostureRefusal)

    def test_enabled_with_neither_keys_nor_google_refuses(self) -> None:
        from lorerunes import PostureRefusal, derive_posture
        result = derive_posture(
            host_is_loopback=True,
            enabled=True,
            mode=MODE_API_KEY,
            has_keys=False,
            has_google=False,
        )
        assert isinstance(result, PostureRefusal)

    def test_an_unknown_mode_string_refuses_rather_than_crashing(self) -> None:
        # Hostile input at a ``str``-typed seam: a typo that slips past a config
        # boundary (or a caller that passes a raw value) must be diagnosed, never
        # raise and never fall through to a posture.
        from lorerunes import PostureRefusal, derive_posture
        result = derive_posture(
            host_is_loopback=True,
            enabled=True,
            mode=MODE_TYPO,
            has_keys=True,
            has_google=True,
        )
        assert isinstance(result, PostureRefusal)

    @pytest.mark.parametrize("mode", ["", "   ", "API_KEY", "google_oauth ", "None"])
    def test_degenerate_mode_strings_refuse(self, mode: str) -> None:
        # Blank, whitespace, wrong case, trailing space, and the string "None" — the
        # shapes a hand-edited yaml or a stringified value actually produces.
        from lorerunes import PostureRefusal, derive_posture
        result = derive_posture(
            host_is_loopback=True,
            enabled=True,
            mode=mode,
            has_keys=True,
            has_google=True,
        )
        assert isinstance(result, PostureRefusal)


class TestPostureRefusalIsDiagnosable:
    """A gate that refuses honest configs gets switched off — so it must TEACH."""

    def _refusal(self) -> PostureRefusal:
        from lorerunes import PostureRefusal, derive_posture
        result = derive_posture(
            host_is_loopback=False,
            enabled=True,
            mode=MODE_GOOGLE_OAUTH,
            has_keys=False,
            has_google=True,
        )
        assert isinstance(result, PostureRefusal)
        return result

    def test_the_refusal_names_its_nearest_posture_in_the_message(self) -> None:
        # The name is read OFF the enum member the refusal carries, so a posture
        # rename cannot leave the prose teaching a posture that no longer exists.
        refusal = self._refusal()
        assert refusal.nearest.name in refusal.message, (
            "the refusal message must name its nearest posture, and must take that "
            "name from the enum rather than a hardcoded literal"
        )

    def test_the_refusal_lists_at_least_one_concrete_problem(self) -> None:
        refusal = self._refusal()
        assert refusal.problems, (
            "'refused' with no problems is undiagnosable; the operator needs the "
            "exact field to change"
        )

    def test_every_reported_problem_names_a_real_input_field(self) -> None:
        # DERIVED, not hand-listed: the legal field names come from the function's own
        # signature, so a renamed parameter cannot leave a problem string pointing at
        # a field that no longer exists.
        from lorerunes import derive_posture
        legal_fields = set(inspect.signature(derive_posture).parameters)
        assert legal_fields, "derive_posture must take named parameters"
        refusal = self._refusal()
        for problem in refusal.problems:
            assert any(field in problem for field in sorted(legal_fields)), (
                f"problem {problem!r} names no input field; legal fields are "
                f"{sorted(legal_fields)}. A problem the operator cannot act on is "
                f"prose, not a diagnosis."
            )

    def test_the_refusal_for_a_non_loopback_hosted_config_names_the_host_field(
        self,
    ) -> None:
        # The specific, unambiguous case: everything is hosted-shaped except the bind.
        refusal = self._refusal()
        assert any("host" in problem for problem in refusal.problems), (
            f"the one wrong field is the bind host; problems were {refusal.problems}"
        )

    def test_a_refusal_is_not_a_posture(self) -> None:
        # The CONTROL that keeps every ``isinstance(result, PostureRefusal)`` above
        # meaningful: a build whose refusal type also satisfied ``Posture`` would pass
        # them all. The two results must be disjoint types.
        from lorerunes import Posture
        refusal = self._refusal()
        assert not isinstance(refusal, Posture)


class TestScopeConstants:
    """The two minted/checked scopes have ONE home (design §6)."""

    def test_the_scope_values_are_the_ruled_strings(self) -> None:
        # Design §6 names them verbatim. They travel on the wire in
        # ``AccessToken.scopes`` and in ``AuthSettings.required_scopes``, so the
        # VALUES are contract, not an internal choice.
        from lorerunes import SCOPE_READ, SCOPE_WRITE
        assert SCOPE_READ == "lore:read"
        assert SCOPE_WRITE == "lore:write"

    def test_the_two_scopes_are_distinct(self) -> None:
        # If they ever collapsed to one string, every hosted principal would carry
        # write authority and the §7 guard would be inert while staying green.
        from lorerunes import SCOPE_READ, SCOPE_WRITE
        assert SCOPE_READ != SCOPE_WRITE
