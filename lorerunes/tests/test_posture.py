"""CONTRACT (contract-39-w23) — deployment-posture derivation (design §6 / §13 g5).

Pins ``lorerunes.host_is_loopback`` (the R15 fail-closed predicate, over a 127/8 GRID, not
spellings) and ``lorerunes.derive_posture`` (the LOOPBACK / LAN_BEARER / HOSTED_OAUTH
cross-product + the typed refusal on an incoherent posture). Pure functions over primitives —
no config object, no store, no wire (``lorerunes`` is stdlib-only). The COMPOSITION that hands
the derived posture to ``FastMCP(auth=…)`` is ``test_auth_composition_recut.py``; this file pins
the LOGIC only (design "test the LOGIC — the in-image conformance run is packet-65's deploy").

CONTRACT-FIRST: ``host_is_loopback`` / ``derive_posture`` are stubs raising ``NotImplementedError``
(``lorerunes/lorerunes/posture.py``), so every pin here fails BEHAVIOURALLY, never on an
ImportError. The ``Posture`` enum + ``PostureError`` type are the real interface surface.
"""

from __future__ import annotations

import pytest

from lorerunes import Posture, PostureError, derive_posture, host_is_loopback

# --------------------------------------------------------------------------- #
# host_is_loopback — a PREDICATE over the 127/8 block, NOT a set of spellings (R15).
# --------------------------------------------------------------------------- #

# Genuine loopback binds: the literal hostname, both ends of 127.0.0.0/8, a mid-range 127.x, ::1.
# 127.0.0.2 / 127.255.255.254 are the DISCRIMINATOR against a build that special-cases only the
# literal "127.0.0.1" (a spellings set) instead of the whole /8 block.
_LOOPBACK_HOSTS = ["localhost", "127.0.0.1", "127.0.0.2", "127.255.255.254", "::1"]

# Non-loopback binds — LAN, public, the any-address, real hostnames. 0.0.0.0 is NOT loopback
# (binding it exposes every interface); a build treating "unspecified" as loopback fails here.
_NON_LOOPBACK_HOSTS = [
    "0.0.0.0",
    "10.0.0.1",
    "192.168.1.10",
    "8.8.8.8",
    "example.com",
    "lore.firehawktransam.org",
]

# Malformed / spoofed values ``ipaddress`` cannot parse: they MUST return False via a fail-CLOSED
# exception path (never True, never a leaked exception). The ``127.0.0.1.evil.com`` /
# ``127.0.0.1extra`` entries are the DISCRIMINATOR against a ``host.startswith("127.")`` build
# (which returns True → a public host wrongly admitted as loopback); ``localhost.evil.com`` is the
# discriminator against a ``"localhost" in host`` substring build.
_MALFORMED_HOSTS = [
    "",
    "   ",
    "not-an-ip",
    "999.999.999.999",
    "127.0.0.1.evil.com",
    "127.0.0.1extra",
    "localhost.evil.com",
]


class TestHostIsLoopback:
    @pytest.mark.parametrize("host", _LOOPBACK_HOSTS)
    def test_loopback_binds_are_true(self, host: str) -> None:
        # The whole 127/8 block + localhost + ::1 → True. WRONG BUILD: a spellings set that only
        # matches "127.0.0.1"/"localhost" (fails 127.0.0.2 / 127.255.255.254).
        assert host_is_loopback(host) is True, f"{host!r} is a genuine loopback bind"

    @pytest.mark.parametrize("host", _NON_LOOPBACK_HOSTS)
    def test_non_loopback_binds_are_false(self, host: str) -> None:
        # LAN/public/any-address/hostname → False. WRONG BUILD: treating 0.0.0.0 (the
        # any-address — exposes every interface) or a hostname as loopback.
        assert host_is_loopback(host) is False, f"{host!r} is NOT a loopback bind"

    @pytest.mark.parametrize("host", _MALFORMED_HOSTS)
    def test_malformed_hosts_fail_closed_to_false(self, host: str) -> None:
        # FAIL-CLOSED: an unparseable value returns False and NEVER raises. WRONG BUILDS:
        # (1) ``startswith("127.")`` → admits 127.0.0.1.evil.com / 127.0.0.1extra as loopback;
        # (2) ``"localhost" in host`` → admits localhost.evil.com;
        # (3) letting ``ipaddress.ip_address`` raise → the exception escapes as a 500/boot crash.
        result = host_is_loopback(host)  # must not raise
        assert result is False, (
            f"{host!r} is not parseable as a loopback bind — the predicate MUST fail closed to "
            f"False (a fail-OPEN True here would admit a public bind as loopback)"
        )


# --------------------------------------------------------------------------- #
# derive_posture — the three coherent postures + the typed refusal on an incoherent one.
# --------------------------------------------------------------------------- #


class TestDerivePostureCoherent:
    """Each coherent shape resolves to its posture — FORCED with a distinct fixture (the
    quantifier law: a build collapsing two postures into one reddens on the fixture the collapse
    can't serve)."""

    def test_loopback_bind_with_auth_disabled_is_loopback(self) -> None:
        posture = derive_posture(
            host="127.0.0.1", auth_enabled=False, mode=None, has_oauth_block=False
        )
        assert posture is Posture.LOOPBACK

    def test_enabled_api_key_is_lan_bearer_on_any_host(self) -> None:
        # LAN_BEARER is the networked deploy — it may bind a non-loopback LAN interface (no host
        # constraint, unlike HOSTED_OAUTH). A non-loopback host here proves LAN_BEARER is not
        # gated on loopback.
        posture = derive_posture(
            host="10.0.0.1", auth_enabled=True, mode="api_key", has_oauth_block=False
        )
        assert posture is Posture.LAN_BEARER

    def test_enabled_hosted_oauth_on_loopback_with_oauth_block_is_hosted_oauth(self) -> None:
        posture = derive_posture(
            host="127.0.0.1", auth_enabled=True, mode="hosted_oauth", has_oauth_block=True
        )
        assert posture is Posture.HOSTED_OAUTH


class TestDerivePostureRefusesIncoherent:
    """An incoherent configuration is a fail-LOUD ``PostureError`` naming the nearest posture +
    the exact missing/conflicting field — never a silently-degraded default.

    The recurring WRONG BUILD every reject pin catches: a build that DEFAULTS to some posture
    (e.g. returns ``LOOPBACK``/``LAN_BEARER``) instead of raising — which would silently run a
    misconfigured hosted deploy. ``pytest.raises(PostureError)`` reddens on that.
    """

    def test_hosted_mode_without_an_oauth_block_is_refused(self) -> None:
        with pytest.raises(PostureError) as excinfo:
            derive_posture(
                host="127.0.0.1", auth_enabled=True, mode="hosted_oauth", has_oauth_block=False
            )
        message = str(excinfo.value)
        # Names the nearest posture (enumerated FROM the enum, so a rename moves the message) AND
        # the missing field (``oauth``). WRONG BUILD: a bare "incoherent posture" with no field.
        assert Posture.HOSTED_OAUTH.name in message, (
            "the refusal must name the nearest posture, enumerated from the Posture enum"
        )
        assert "oauth" in message.lower(), "the refusal must name the missing field (the oauth block)"

    def test_hosted_mode_on_a_non_loopback_host_is_refused(self) -> None:
        # HOSTED_OAUTH requires a loopback bind — lore-caddy terminates TLS and proxies to
        # loopback lore ("the proxy comes to us", design §6). A hosted deploy binding a public
        # interface is a conflict. WRONG BUILD: skipping the host coherence check (would expose
        # lore directly, bypassing lore-caddy).
        with pytest.raises(PostureError) as excinfo:
            derive_posture(
                host="0.0.0.0", auth_enabled=True, mode="hosted_oauth", has_oauth_block=True
            )
        message = str(excinfo.value)
        assert Posture.HOSTED_OAUTH.name in message
        assert "host" in message.lower() or "loopback" in message.lower(), (
            "the refusal must name the conflicting field (the non-loopback host)"
        )

    def test_auth_disabled_on_a_non_loopback_host_is_refused(self) -> None:
        # LOOPBACK requires a loopback bind — auth-disabled on a public/LAN interface is an open
        # door (no gate, reachable off-box). WRONG BUILD: returning LOOPBACK regardless of host.
        with pytest.raises(PostureError) as excinfo:
            derive_posture(
                host="192.168.1.10", auth_enabled=False, mode=None, has_oauth_block=False
            )
        message = str(excinfo.value)
        assert Posture.LOOPBACK.name in message
        assert "host" in message.lower() or "loopback" in message.lower()


class TestPostureEnumIsAClosedDomain:
    def test_the_three_postures_are_the_closed_set(self) -> None:
        # GREEN-now guard: the posture domain is exactly these three. A build adding a fourth
        # posture (or dropping one) reddens — the composition's per-posture wiring and the
        # refusal-message enumeration both key on this closed set.
        assert {member.name for member in Posture} == {"LOOPBACK", "LAN_BEARER", "HOSTED_OAUTH"}
