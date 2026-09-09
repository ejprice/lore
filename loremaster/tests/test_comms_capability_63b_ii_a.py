"""Contract — packet 63b wave ii-a: §4.D — the ``capability=`` identity seam for the ``lore_comms``
tool. Design ``docs/design/2026-09-03-packet63b-design.md`` §4.D (RULED reading A: ONE optional
``capability=`` param; the message family REQUIRES it; resolved via the ONE composition root
``AppContext._resolve_subject``; ``agent=`` must equal the resolved Subject's agent name). Authored by
``contract-63b-ii-a`` (Opus 4.8 contract author — CONTRACT TESTS ONLY, no production).

WHY (design §4.D / §9): at HEAD comms derives identity from ``agent=`` + the registration row, so
ANYONE WHO KNOWS AN AGENT'S NAME acts as it (reading B, REJECTED). ii-a closes that write-side hole by
requiring a verified capability for every message-family verb, resolved through the SAME
``_resolve_subject`` seam 63a-ii built.

SCOPE DIVISION (design §5 wave table — stated, not silently narrowed): ii-a pins the SPEC + the
wiring STRUCTURE (the typed ``requires_capability`` applicability, the effect-keyed routing coverage,
the ``capability=`` param). The BEHAVIOURAL over-the-wire enforcement — a mismatched
``agent=``/capability → teaching ``GovernedDenied``, across ≥2 principals × ≥2 agents — is
**63b-iii's headline** (the security-auditor wave, over the REAL tables). This file does NOT stand up
the full resolve-chain harness; it pins that the resolution ROUTES through ``_resolve_subject`` so
63b-iii's wire test has a seam to exercise. (Report §Decisions carries this as a committed reading.)

The ROUTING-COVERAGE pin follows §4.D VERBATIM: it derives the verb set from ``_COMMS_ACTIONS`` itself
(the §10.5 'surfaced, not narrowed' trigger) and keys on each verb's EFFECT — *a verb with
``requires_capability=True`` and no ``_resolve_subject`` call in its handler reds.* (Committed reading:
resolution is HANDLER-level, per §4.D's exact wording; a central-dispatch-only build would red this and
is a lead flag — report §Decisions.)

RED-AT-HEAD: ``CommsActionSpec`` has no ``requires_capability`` field (fields: handler / params /
required / requires_registration / limit_cap); ``comms`` has no ``capability`` param; no message-family
handler calls ``_resolve_subject``. Every pin below reds for one of those reasons.
"""

from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path

from _governed_contract import function_calls_named
from loremaster.server import _COMMS_ACTIONS, AppContext, CommsActionSpec

from loremaster import server

# The message-family verbs that REQUIRE a capability in 63b (design §4.D). ``register`` MINTS identity
# (False by construction); heartbeat/brief_get/brief_publish/brief_ack/fleet are False in 63b and
# flipped by 63c (RED_ADJUDICATED rows naming 63c — NOT this contract's to require).
_MESSAGE_FAMILY = frozenset({"send", "drain", "ack", "await", "story"})
_NON_CAPABILITY_IN_63B = frozenset(
    {"register", "heartbeat", "brief_get", "brief_publish", "brief_ack", "fleet"}
)


def _server_source() -> str:
    return Path(server.__file__).read_text(encoding="utf-8")


def _spec_fields() -> set[str]:
    return {field.name for field in dataclasses.fields(CommsActionSpec)}


class TestCommsActionSpecCarriesRequiresCapability:
    """§4.D — the applicability is TYPED on the spec (``requires_capability: bool``), per the packet-28
    'renders take typed applicability, never a name they compare' law — NOT a hardcoded verb list in
    the dispatch. RED at HEAD (the field is absent)."""

    def test_the_spec_has_a_requires_capability_field(self) -> None:
        """⚠ RED at HEAD — ``CommsActionSpec`` gains ``requires_capability: bool``. REDDENS the HEAD
        whose fields are exactly {handler, params, required, requires_registration, limit_cap}."""
        assert "requires_capability" in _spec_fields(), (
            "CommsActionSpec has no `requires_capability` field — the §4.D capability applicability is "
            "unbuilt (it must be TYPED on the spec, not a hardcoded verb list in the dispatch)"
        )

    def test_the_message_family_verbs_require_capability(self) -> None:
        """⚠ RED at HEAD (field absent → getattr None → the assert fires). ∀ message-family verb
        (send/drain/ack/await/story): ``requires_capability is True``. This is the §4.D core: the
        write-side identity hole is closed for exactly the verbs that act as an agent."""
        for verb in sorted(_MESSAGE_FAMILY):
            spec = _COMMS_ACTIONS[verb]
            assert getattr(spec, "requires_capability", None) is True, (
                f"comms verb {verb!r} must set requires_capability=True (§4.D) — it acts as an agent "
                f"and must present a verified capability, not merely a name"
            )

    def test_the_non_capability_verbs_do_not_require_it_in_63b(self) -> None:
        """⚠ RED at HEAD (field absent → getattr None ≠ False). ``register`` MINTS identity (False by
        construction); heartbeat/brief_*/fleet are False in 63b (RED_ADJUDICATED→63c). A build that
        flipped one of these to True in 63b would over-reach (63c's job); a HEAD with no field reds."""
        for verb in sorted(_NON_CAPABILITY_IN_63B):
            spec = _COMMS_ACTIONS[verb]
            assert getattr(spec, "requires_capability", None) is False, (
                f"comms verb {verb!r} must be requires_capability=False in 63b (§4.D — register mints; "
                f"heartbeat/brief_*/fleet flip in 63c, RED_ADJUDICATED). got "
                f"{getattr(spec, 'requires_capability', '<no field>')!r}"
            )

    def test_the_capability_set_is_EXACTLY_the_message_family_surfaced_not_narrowed(self) -> None:
        """⚠ RED at HEAD — the SET of verbs with ``requires_capability=True`` is derived from
        ``_COMMS_ACTIONS`` and must EQUAL {send, drain, ack, await, story} (the §10.5 'surfaced, not
        narrowed' trigger: a NEW comms verb forces a requires_capability decision, it does not default
        into the unguarded set). At HEAD no verb has the field → the True-set is empty → reds."""
        required = {
            verb for verb, spec in _COMMS_ACTIONS.items()
            if getattr(spec, "requires_capability", False)
        }
        assert required == set(_MESSAGE_FAMILY), (
            f"the requires_capability=True set is {sorted(required)}, not the message family "
            f"{sorted(_MESSAGE_FAMILY)} — a new/moved comms verb must DECIDE its capability applicability "
            f"(surfaced, not narrowed; §4.D / §10.5)"
        )


class TestTheCapabilityRoutingCoverageIsEffectKeyed:
    """§4.D routing-coverage pin — derived from ``_COMMS_ACTIONS`` itself, keyed on each verb's EFFECT:
    a verb with ``requires_capability=True`` whose HANDLER does not call ``_resolve_subject`` reds. This
    is the instrument that makes 'every capability verb resolves identity through the ONE composition
    root' a CHECKED VARIABLE, not a hope (INSTRUMENT 0 — reach as a checked variable over the verb SET)."""

    def test_every_capability_verb_handler_resolves_the_subject(self) -> None:
        """⚠ RED at HEAD — first the field must exist (else the coverage is unrepresentable), then ∀
        requires_capability verb, its handler (``spec.handler.__name__``, derived from _COMMS_ACTIONS)
        must call ``_resolve_subject`` (AST, the L2a ``function_calls_named`` idiom). At HEAD the field
        is absent AND no message handler calls _resolve_subject — both reasons red. On the build every
        capability handler routes identity through the ONE composition root."""
        assert "requires_capability" in _spec_fields(), (
            "CommsActionSpec has no requires_capability field — the effect-keyed routing coverage is "
            "unrepresentable until the typed applicability exists (§4.D)"
        )
        source = _server_source()
        for verb, spec in _COMMS_ACTIONS.items():
            if not getattr(spec, "requires_capability", False):
                continue
            handler_name = spec.handler.__name__
            assert function_calls_named(source, handler_name, "_resolve_subject"), (
                f"comms verb {verb!r} requires a capability but its handler {handler_name!r} never calls "
                f"_resolve_subject — identity is not resolved through the ONE composition root (§4.D); a "
                f"requires_capability verb with no _resolve_subject call is the §9 name-only hole reopened"
            )


class TestTheCommsToolAcceptsACapabilityParameter:
    """§4.D — ``lore_comms`` gains ONE optional ``capability=`` parameter (the wire surface the tool
    presents). RED at HEAD (the dispatch signature carries no ``capability``)."""

    def test_the_comms_dispatch_accepts_capability(self) -> None:
        """⚠ RED at HEAD — ``AppContext.comms`` gains a ``capability: str | None`` keyword. REDDENS the
        HEAD signature (which ends at ...seqs, peek). The FastMCP ``lore_comms`` wrapper threads it to
        this dispatch; pinning the dispatch signature is the seam-level contract."""
        params = inspect.signature(AppContext.comms).parameters
        assert "capability" in params, (
            "AppContext.comms has no `capability` parameter — the §4.D optional capability= seam is "
            f"unbuilt. present params end: {list(params)[-4:]}"
        )
