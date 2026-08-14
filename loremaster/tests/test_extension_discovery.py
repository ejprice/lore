"""Contract — packet 46: config-driven extension DISCOVERY wiring.

Packet 46 makes ``extensions:`` in ``lore.yaml`` actually instantiate registered
:class:`~loremaster.extension.Extension`\\ s at boot and route them through the
existing :meth:`~loremaster.server.LoreServer.register_extension` composition.
Ruled design of record: ``docs/design/2026-08-03-wave-d-architecture.md`` §3
(binds the build) · spec ``docs/design/2026-08-01-dnd-rules-rag-proposal.md`` §4
Option C item 2 + §7 (trust posture). The framework itself
(``loremaster/loremaster/extension.py``, the eleven inert-default seams) is
COMPLETE and unwired; this contract wires the discovery gap.

THE MECHANISM (settled design, not invented here):
* A STATIC registry :data:`loremaster.extension.EXTENSION_REGISTRY`
  (``dict[str, type[Extension]]``) — ships EMPTY in production (no real extension
  until packet 51); TEST-INJECTABLE via ``monkeypatch.setattr`` and read LIVE at
  construction time.
* A discovery helper (:meth:`LoreServer._discover_extensions`) called at the END
  of ``LoreServer.__init__`` (after the registry + chunker overrides are built).
  For each key in ``config.extensions``: registry lookup → instantiate → verify
  ``instance.name == key`` → :meth:`register_extension`.
* Unknown key ⇒ FAIL BOOT LOUDLY (``ValueError``) with a teaching error whose
  known-set is DERIVED from ``EXTENSION_REGISTRY`` keys — never a hand-list (the
  served surface is read by an LLM; Trust Leg-1 / #291 natural-language class).
* Registry-key vs ``ext.name`` mismatch ⇒ FAIL BOOT LOUDLY: the framework
  declares ``name`` IS "its key in the ``extensions:`` config"
  (:attr:`Extension.name`), and a mismatch would make ``register_extension``
  validate ``config.extensions[ext.name]`` — the WRONG (usually absent) slice —
  silently (see :class:`TestRegistryKeyMustMatchExtensionName`).
* R14 rider (packet 39, unpaid at git 7908887): extension tools register carrying
  ``ToolAnnotations(readOnlyHint=False)`` — all 15 built-ins pass annotations; the
  extension ``mcp.add_tool`` call passes none (see :class:`TestR14ExtensionToolAnnotations`).

RED STATE (this contract, against the packet-46 INERT STUB):
``LoreServer._discover_extensions`` is a NO-OP and ``_register_extension_tools``
passes no annotations, so every NEW-behaviour pin below is RED while the
no-extensions regression pin (:class:`TestNoExtensionsIsByteIdenticalServing`)
and every pre-existing suite stay GREEN. Each load-bearing pin's docstring names
its expected-RED node id and the one-line mutation that reddens a finished build.

TEST ENVIRONMENT: these pins are SELF-CONTAINED — every one injects its own
``EXTENSION_REGISTRY`` and passes an explicit ``extensions=`` config, so NONE
depends on ``minimal_config``'s default slice. (That default's collision with
live discovery is a separate reconciliation escalated to lead-46; it does not
touch this file.) Construction + ``build_mcp_server`` + ``list_tools`` need no
live store — the store is built only inside the lifespan, never entered here —
so these run without the SurrealDB harness (``asyncio_mode = auto``).

NO STORE TOUCH: discovery composes in-process (registry lookup + ``cls()`` +
``register_extension`` — the last reads config, never the store); the injected
test extensions are inert. Packet 46 touches no store, schema, or DDL.
"""

from __future__ import annotations

from typing import Any

import loremaster.extension as extension_module
import pytest
from _extension_helpers import (
    BUILTIN_COLLISION_NAME,
    CollidingExtension,
    CounterExtension,
    FakeExtension,
    minimal_config,
)
from loremaster.config import LoreConfig, ToolsConfig
from loremaster.extension import Extension
from loremaster.server import (
    _ALL_BUILTIN_TOOL_NAMES,
    LoreServer,
    build_instructions,
    build_mcp_server,
)

# --------------------------------------------------------------------------- #
# Local, discovery-specific test extensions (the shared doubles live in
# ``_extension_helpers``; these are private to this contract, matching the
# inline-``_DuplicateBumpExtension`` idiom in ``test_extension.py``). None
# declares a ``config_model``, so ``register_extension`` needs no config slice —
# keeping each pin's discriminator on discovery, not on slice validation.
# --------------------------------------------------------------------------- #

# Two probe extensions whose names are NOT built-ins and are NOT hardcodable (a
# builder could not have guessed them): the monoculture guard for the unknown-name
# teaching error. A build that hand-lists the known set — or names only one — fails.
_ALPHA_PROBE_NAME = "alpha_probe_ext_46"
_BETA_PROBE_NAME = "beta_probe_ext_46"


class _AlphaProbeExtension(Extension):
    """A registry probe whose ``name`` == :data:`_ALPHA_PROBE_NAME`."""

    @property
    def name(self) -> str:
        return _ALPHA_PROBE_NAME


class _BetaProbeExtension(Extension):
    """A second registry probe whose ``name`` == :data:`_BETA_PROBE_NAME`."""

    @property
    def name(self) -> str:
        return _BETA_PROBE_NAME


# An extension whose ``name`` deliberately DIFFERS from any registry key it is
# filed under — the key-vs-name mismatch fixture.
_MISNAMED_ACTUAL_NAME = "misnamed_actual_46"


class _MisnamedExtension(Extension):
    """An extension whose ``name`` never equals the registry key it is filed under."""

    @property
    def name(self) -> str:
        return _MISNAMED_ACTUAL_NAME


def _inject_registry(
    monkeypatch: pytest.MonkeyPatch, registry: dict[str, type[Extension]]
) -> None:
    """Replace the LIVE :data:`EXTENSION_REGISTRY` for the duration of one test.

    ``setattr`` (not dict mutation) so pytest auto-reverts it, and because the
    discovery contract is that the helper reads the module ATTRIBUTE at
    construction time — a build that binds the name at import (not test-injectable)
    fails every pin that injects a registry.
    """
    monkeypatch.setattr(extension_module, "EXTENSION_REGISTRY", registry)


def _config(extensions: dict[str, dict[str, Any]]) -> LoreConfig:
    """A lightweight valid config (dim 8, no live store) with the given ``extensions``."""
    return minimal_config(extensions=extensions)


def _extension_names(server: LoreServer) -> list[str]:
    """The names of the extensions the server actually composed."""
    return [ext.name for ext in server.extensions]


# =========================================================================== #
# PIN 1 — unknown-name boot failure (Trust Leg 1) + monoculture guard.
# =========================================================================== #
class TestUnknownExtensionNameFailsBootLoudly:
    """A ``config.extensions`` key absent from the registry FAILS BOOT LOUDLY, and
    the teaching error names the REAL known set DERIVED from the registry keys."""

    def test_unknown_key_raises_naming_the_registry_derived_known_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Inject a two-entry registry whose keys are NON-hardcodable probe names;
        a config naming a DIFFERENT (unknown) key ⇒ construction raises ``ValueError``
        naming BOTH the unknown key AND every known name (derived from
        ``EXTENSION_REGISTRY.keys()``).

        expected-RED node (stub): this test — ``_discover_extensions`` is inert, so
        construction does NOT raise and ``pytest.raises`` fails.
        MUTATION that reddens a finished build: drop the registry-membership check
        (no raise), OR build the known-set from a hand-list (the probe names, being
        un-hardcodable, are then absent → the message assertions fail).
        WRONG BUILD THIS STILL PASSES — none: a blind ``raise`` with a generic
        message fails the ``in message`` checks; a message naming only ONE known
        extension fails (both required); a hardcoded known-set omits the probes.
        """
        _inject_registry(
            monkeypatch,
            {
                _ALPHA_PROBE_NAME: _AlphaProbeExtension,
                _BETA_PROBE_NAME: _BetaProbeExtension,
            },
        )
        config = _config({"totally_unknown_ext_46": {}})
        with pytest.raises(ValueError) as exc_info:
            LoreServer(config)
        message = str(exc_info.value)
        assert "totally_unknown_ext_46" in message, (
            "the loud-fail must NAME the unknown extension key"
        )
        # The known set is DERIVED from the registry keys — a hand-list cannot know
        # these probe names, so both must appear (naming only one, or a hardcoded
        # set, fails here).
        assert _ALPHA_PROBE_NAME in message, "the teaching error must name the known set"
        assert _BETA_PROBE_NAME in message, (
            "the teaching error must name the WHOLE known set, derived from the "
            "registry — not a sample of one"
        )
        # Anti-leak leg (Trust Leg-1): the offending key must appear ONLY as the
        # REJECTED key, never inside the "Known extensions:" clause the error
        # teaches — else a reading LLM concludes its typo IS a registered
        # extension (a false clear). Catches a known-set polluted with the
        # caller's own keys, e.g. ``sorted(registry ∪ config.extensions)``, which
        # otherwise passes every other assertion here (the unknown key IS "in
        # message", just in the wrong clause).
        # MUTATION that reddens this leg on a finished build: build the known-set
        # as ``", ".join(sorted(set(registry) | set(self._config.extensions)))``.
        known_clause = message.split("Known extensions:", 1)[1]
        assert "totally_unknown_ext_46" not in known_clause, (
            "the unknown key must be taught as REJECTED, never listed among the "
            "known extensions the error names"
        )

    def test_control_a_known_registry_key_boots_without_raising(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """POSITIVE CONTROL for the loud-fail: with the SAME registry, a config
        naming a KNOWN key boots cleanly and composes that extension — so the
        loud-fail above is specific to the unknown key, not "any ``extensions:``
        section raises".

        Green in a finished build; RED in the stub (discovery is inert, so the
        known extension is NOT composed and the ``in`` assertion fails) — which is
        correct: the control also proves discovery actually REGISTERS.
        """
        _inject_registry(
            monkeypatch,
            {
                _ALPHA_PROBE_NAME: _AlphaProbeExtension,
                _BETA_PROBE_NAME: _BetaProbeExtension,
            },
        )
        server = LoreServer(_config({_ALPHA_PROBE_NAME: {}}))  # must not raise
        assert _ALPHA_PROBE_NAME in _extension_names(server)


# =========================================================================== #
# PIN 2 — positive control: a registered extension BOOTS and is COMPOSED.
# =========================================================================== #
class TestRegisteredExtensionIsDiscoveredAndComposed:
    """A config naming a KNOWN extension ⇒ construction SUCCEEDS and the extension
    is REGISTERED (present in ``server.extensions``, its seams composed)."""

    @pytest.mark.parametrize(
        ("cls", "name", "slice_"),
        [
            # FakeExtension carries a config_model (FakeConfigModel(flavour)); its
            # slice is validated at register — proving the seam-7 path flows through
            # discovery too.
            (FakeExtension, "fake", {"flavour": "vanilla"}),
            # CounterExtension has NO config_model — a DIFFERENT, non-"fake" name so a
            # build that special-cases the single name "fake" fails this param.
            (CounterExtension, "counter", {}),
        ],
    )
    def test_named_extension_is_instantiated_and_registered(
        self,
        monkeypatch: pytest.MonkeyPatch,
        cls: type[Extension],
        name: str,
        slice_: dict[str, Any],
    ) -> None:
        """expected-RED node (stub): both params — ``_discover_extensions`` is inert,
        so the extension is never composed and ``server.extensions`` is empty.
        MUTATION that reddens a finished build: discovery that instantiates but never
        calls ``register_extension`` (the extension is absent from ``server.extensions``).
        WRONG BUILD THIS STILL PASSES — none: a one-name special-case (only "fake")
        fails the ``counter`` param; discover-without-register fails both.
        """
        _inject_registry(monkeypatch, {name: cls})
        server = LoreServer(_config({name: slice_}))
        assert name in _extension_names(server), (
            "a config-named extension must be instantiated AND registered by discovery"
        )
        # The composition is real: the extension instance carried is of the class the
        # registry mapped (not a placeholder).
        composed = next(ext for ext in server.extensions if ext.name == name)
        assert isinstance(composed, cls)


# =========================================================================== #
# PIN 3 — no ``extensions:`` block ⇒ byte-identical serving (regression leg).
# =========================================================================== #
class TestNoExtensionsIsByteIdenticalServing:
    """A config with an EMPTY ``extensions`` block ⇒ discovery is a no-op ⇒ the
    served surface is byte-identical to today (the GREEN-under-stub leg)."""

    async def test_empty_extensions_serves_only_the_builtins_byte_identical(
        self,
    ) -> None:
        """No extension ⇒ ``server.extensions == []`` ⇒ the registered surface is
        EXACTLY the built-ins and the instructions are byte-exact today's.

        expected-RED node (stub): none — GREEN under the inert stub AND a finished
        build (discovery no-ops on empty extensions either way).
        MUTATION that reddens it: a discovery that mis-fires on empty extensions —
        registering a phantom tool (surface grows) or reshaping the instructions.
        WRONG BUILD THIS STILL PASSES — a discovery that only breaks on NON-empty
        configs; that is what PINS 1/2/4/6 cover. This pin is the regression floor.
        """
        server = LoreServer(_config({}))
        assert _extension_names(server) == [], "empty extensions ⇒ a bare server"

        mcp = build_mcp_server(server)
        registered = {tool.name for tool in await mcp.list_tools()}
        # No extension tools leaked in: the registered set is EXACTLY the built-ins.
        assert registered == set(_ALL_BUILTIN_TOOL_NAMES)
        # Byte-identical instructions: default config (tools=None, identity=None) ⇒
        # the full-universe instructions, unchanged by discovery.
        assert (mcp.instructions or "") == build_instructions(
            _ALL_BUILTIN_TOOL_NAMES, identity=None
        )


# =========================================================================== #
# PIN 4 — a discovered colliding tool COMPOSES with 45's universe guard.
# =========================================================================== #
class TestDiscoveredCollisionComposesWithAllowlistUniverseGuard:
    """An extension DISCOVERED from config whose tool name collides with a built-in
    reserved by the DECLARED UNIVERSE fails ``build_mcp_server`` LOUDLY — even when
    that built-in is DISABLED by a ``tools:`` allowlist (packet 45 L2-4)."""

    def test_discovered_colliding_tool_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``CollidingExtension`` (tool name = ``lore_search``) discovered via config
        ⇒ ``build_mcp_server`` raises ``ValueError`` naming the collided name. The
        DISCOVERY is what puts the extension on the server (not a manual register).

        expected-RED node (stub): this test — discovery is inert, so
        ``CollidingExtension`` is never composed, ``build_mcp_server`` sees no
        extension tool, and no collision raises.
        MUTATION that reddens a finished build: discovery that fails to compose the
        extension (no collision path reached).
        """
        _inject_registry(monkeypatch, {"collider": CollidingExtension})
        server = LoreServer(_config({"collider": {}}))
        # Registration order: the built-ins register, THEN the discovered extension
        # tool — so the collision path is reached inside build_mcp_server.
        with pytest.raises(ValueError, match=BUILTIN_COLLISION_NAME):
            build_mcp_server(server)

    def test_discovered_collision_raises_even_when_the_builtin_is_disabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """HARDER LEG (packet 45 fix): DISABLE the built-in ``lore_search`` via a
        ``tools:`` allowlist AND discover an extension claiming that exact name ⇒
        ``build_mcp_server`` STILL raises, because the name is RESERVED by the
        declared universe even though the built-in is not registered on this deploy.

        expected-RED node (stub): this test — discovery inert ⇒ the extension is
        never composed ⇒ no raise (the built-in is simply disabled, silently).
        MUTATION that reddens a finished build: a collision guard that checks only
        the REGISTERED set (``get_tool(...)``) instead of ``_ALL_BUILTIN_TOOL_NAMES``
        — with ``lore_search`` disabled it is unregistered, the guard misses, and the
        discovered extension silently shadows the reserved name.
        WRONG BUILD THIS STILL PASSES — none: a registered-set-only guard passes the
        first leg (lore_search IS registered there) but fails THIS one.
        """
        assert BUILTIN_COLLISION_NAME == "lore_search"  # fixture guard
        _inject_registry(monkeypatch, {"collider": CollidingExtension})
        enabled = sorted(set(_ALL_BUILTIN_TOOL_NAMES) - {BUILTIN_COLLISION_NAME})
        config = _config({"collider": {}}).model_copy(
            update={"tools": ToolsConfig(enabled=enabled)}
        )
        server = LoreServer(config)
        with pytest.raises(ValueError, match=BUILTIN_COLLISION_NAME):
            build_mcp_server(server)


# =========================================================================== #
# PIN 5 — R14 rider: discovered/registered extension tools carry annotations.
# =========================================================================== #
class TestR14ExtensionToolAnnotations:
    """Extension tools register carrying ``ToolAnnotations(readOnlyHint=False)`` —
    all 15 built-ins pass annotations; today the extension ``mcp.add_tool`` call
    passes none (packet 39 R14, unpaid at git 7908887, paid here)."""

    async def test_extension_tool_publishes_readonly_hint_false(self) -> None:
        """A registered extension tool's published annotations carry
        ``readOnlyHint is False`` (an explicit, mutating-by-default hint that matches
        the built-ins' posture), not ``None``.

        A MANUAL ``register_extension`` (not discovery) isolates R14 from the
        discovery mechanism — R14 lives in ``_register_extension_tools``, which every
        registration path (manual or discovered) funnels through.

        expected-RED node (stub): this test — ``_register_extension_tools`` calls
        ``mcp.add_tool(...)`` with NO ``annotations``, so the published tool's
        ``annotations`` is ``None`` and ``is not None`` fails.
        MUTATION that reddens a finished build: pass no annotations (``None``) → the
        ``is not None`` leg reddens; pass ``readOnlyHint=True`` → the ``is False``
        leg reddens. Mutation-provable BOTH directions.
        """
        server = LoreServer(_config({})).register_extension(CounterExtension())
        mcp = build_mcp_server(server)
        tools = {tool.name: tool for tool in await mcp.list_tools()}
        bump = tools["bump_counter"]
        assert bump.annotations is not None, (
            "an extension tool must publish ToolAnnotations, like every built-in "
            "(R14); today the add_tool call passes none"
        )
        assert bump.annotations.readOnlyHint is False, (
            "extension tools declare readOnlyHint=False (mutating by default) — "
            "flipping this to None/True must redden this pin"
        )


# =========================================================================== #
# PIN 6 — BOUNDARY: registry KEY must match the instantiated ``ext.name``.
# =========================================================================== #
class TestRegistryKeyMustMatchExtensionName:
    """A registry KEY that maps to a class whose instance ``name`` differs FAILS
    BOOT LOUDLY, rather than silently validating ``config.extensions[ext.name]``
    (the wrong, usually-absent slice).

    DECISION (contract author, stated in the report): GUARD it. Rationale — the
    framework's own :attr:`Extension.name` docstring declares ``name`` IS "its key
    in the ``extensions:`` config", so a key ≠ name violates a DOCUMENTED invariant.
    Without the guard, ``register_extension`` validates ``config.extensions[ext.name]``
    — for a mismatched name that is ``{}`` — so the operator's real slice at
    ``config.extensions[key]`` is IGNORED and NOBODY is told (a Trust "false clear").
    THREAT MODEL: the honest extension author who files their class under the wrong
    registry key; caught at boot, not by a silent misconfiguration downstream.
    """

    def test_key_name_mismatch_raises_naming_both(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Register a class under a key that is NOT its ``name`` ⇒ construction raises
        ``ValueError`` naming BOTH the registry key and the instance's actual name.

        expected-RED node (stub): this test — discovery is inert, so no guard fires
        and construction returns normally.
        MUTATION that reddens a finished build: drop the ``instance.name == key``
        check. Then discovery instantiates ``_MisnamedExtension`` (name
        ``misnamed_actual_46``), ``register_extension`` validates
        ``config.extensions["misnamed_actual_46"]`` ⇒ ``{}`` (absent; no config_model
        ⇒ no error), and the wrong-slice bug ships silently with no raise.
        WRONG BUILD THIS STILL PASSES — a guard that raises but names only one side:
        the ``in`` assertions require BOTH the key and the name.
        """
        _inject_registry(monkeypatch, {"registry_key_46": _MisnamedExtension})
        config = _config({"registry_key_46": {}})
        with pytest.raises(ValueError) as exc_info:
            LoreServer(config)
        message = str(exc_info.value)
        assert "registry_key_46" in message, "the mismatch error must name the registry KEY"
        assert _MISNAMED_ACTUAL_NAME in message, (
            "the mismatch error must name the instance's ACTUAL name, so a reader "
            "sees exactly which side is wrong"
        )


# =========================================================================== #
# PIN 7 — ∀ OVER CONFIG KEYS: every configured extension is composed, and an
# unknown key that is NOT FIRST still fails boot. Closes the QUANTIFIER LAW /
# small-N door every |config|=1 fixture above leaves open.
# =========================================================================== #
class TestAllConfiguredExtensionsAreComposed:
    """Discovery processes EVERY key in ``config.extensions`` — not just the first.

    Every pre-existing pin uses a SINGLE-key ``extensions`` config, so the
    ∀-over-config-keys invariant is exercised only at ``|config| == 1``. A build
    whose loop stops after the first key — ``list(config.extensions)[:1]``, an
    early ``return``/``break``, ``next(iter(config.extensions))``, or a de-dup
    that collapses — composes the first extension, SILENTLY drops the rest, AND
    silently ignores an unknown key that is not first, defeating the packet's
    whole reason to exist (full composition + loud-fail on unknown keys). Both
    legs below use TWO DISTINCT keys so a first-key-only loop is caught.
    """

    def test_every_configured_key_is_composed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A ≥2-key config with BOTH keys registered ⇒ BOTH extensions composed.

        Two DISTINCT probe keys (``alpha`` then ``beta``, both registered): a
        first-key-only loop composes just one, so ``set(...) == {both}`` reddens.
        The comparison is order-independent — whichever single key such a loop
        keeps, a proper subset can never equal the full pair.

        expected-RED node (stub): this test — ``_discover_extensions`` is inert,
        so ``server.extensions`` is empty and the set comparison fails.
        MUTATION that reddens a finished build: iterate only the first key
        (``for key in list(self._config.extensions)[:1]:``) — ``beta`` is dropped.
        WRONG BUILD THIS STILL PASSES — none: any loop that fails to process
        every key composes a proper subset of ``{alpha, beta}``.
        """
        _inject_registry(
            monkeypatch,
            {
                _ALPHA_PROBE_NAME: _AlphaProbeExtension,
                _BETA_PROBE_NAME: _BetaProbeExtension,
            },
        )
        server = LoreServer(_config({_ALPHA_PROBE_NAME: {}, _BETA_PROBE_NAME: {}}))
        assert set(_extension_names(server)) == {_ALPHA_PROBE_NAME, _BETA_PROBE_NAME}, (
            "discovery must compose EVERY configured extension, not just the first "
            "key — a first-key-only loop drops the second and reddens here"
        )

    def test_an_unknown_key_after_a_valid_one_still_fails_boot(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A config whose SECOND key is unknown ⇒ boot fails LOUDLY naming that
        (non-first) key, even though the first key is valid.

        The unknown key sits AFTER a valid one — by insertion order AND
        alphabetically (``alpha_...`` < ``totally_...``), so it is second under
        any plausible iteration order a first-key-only loop would keep — so such a
        loop never reaches it and the loud-fail the packet guarantees never fires.

        expected-RED node (stub): this test — discovery is inert, so nothing
        raises and ``pytest.raises`` fails.
        MUTATION that reddens a finished build: iterate only the first key — the
        valid ``alpha`` is processed, the unknown key is never seen, no raise.
        WRONG BUILD THIS STILL PASSES — none: any loop reaching the unknown key
        raises; any loop that stops before it composes ``alpha`` silently and
        fails to raise.
        """
        _inject_registry(monkeypatch, {_ALPHA_PROBE_NAME: _AlphaProbeExtension})
        with pytest.raises(ValueError, match="totally_unknown_ext_46"):
            LoreServer(
                _config({_ALPHA_PROBE_NAME: {}, "totally_unknown_ext_46": {}})
            )
