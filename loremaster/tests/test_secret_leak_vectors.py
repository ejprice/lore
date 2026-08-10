"""Contract — packet 42: PREVENT THE LEAK, DELETE THE SANITIZER.

Packet 42 deletes the redactor's Shannon-entropy catch-all (``_TOKEN_RE`` +
``_shannon_entropy_bits`` + the ``_is_safe_high_entropy_run`` exemption machinery
that only existed to tame it) and keeps the two LABELLED patterns
(``_BEARER_RE``, ``_ASSIGNMENT_RE``). The packet's own Exit clause names the
control this module must provide:

    "prove that with the catch-all gone, a credential in each of the four M1-M4
    vectors still cannot reach a rendered log line"

That is inventory item **A18** — *"an UNLABELLED secret in free log text was
caught by A2 … exposure genuinely widens — the deliberate trade"* — and it is the
load-bearing risk of the whole packet. The replacement control is not a better
detector. It is that **the value cannot be in the text**: every secret is a
:class:`pydantic.SecretStr` from resolution to an allowlisted unwrap (#211 Half A
+ packet 42 scope items 1-3), and a ``SecretStr`` renders ``**********`` through
every path an accidental log call actually takes.

So this module pins three things that must hold TOGETHER, and are worthless apart:

1. **The replacement control works.** A ``SecretStr`` credential carried through
   every shape a log call can carry one, out through both production formatters,
   never appears in the emitted bytes.
2. **What survived, survived — and one of them is FIXED (ruling R8).** The
   labelled patterns still redact, still preserve their labels, still run in
   order, are still idempotent, and are still reached from all three consumers of
   ``_scrub_text``. **R8 additionally corrects a real defect on that surface:**
   ``_ASSIGNMENT_RE`` was consuming an auth SCHEME word (``Bearer``, ``Basic``,
   ``Token``) as though it were the credential. For Bearer that cost a diagnostic;
   for the others it is a **credential leak**, live today for a short token and
   live for ALL of them once the catch-all is deleted. See
   :class:`TestTheLabelledPatternsSurviveTheDeletion`.
3. **What the deletion COSTS is pinned, not assumed away.** An unlabelled
   credential in free text is no longer redacted. That is the accepted trade;
   these pins go RED the day someone quietly re-adds a detector, so the bound is
   met deliberately rather than rediscovered (CLAUDE.md, "WHEN YOU CANNOT CLOSE A
   HOLE, PIN IT").

THE THREAT MODEL, stated IN the instrument (CLAUDE.md: a gate needs one)
-----------------------------------------------------------------------
These pins protect against the **HONEST developer or dependency** that lets a
credential reach a log line — a config repr, an ``Authorization`` header echoed
back by a client, a connection string in an exception message, a credential in
flight through an ``extra=`` field. They are **NOT** a boundary against an author
deliberately smuggling a secret out: anyone who can write log statements here can
log anything in any encoding, and no type and no regex changes that. Verdicts
follow mechanically: *"a clever attacker gets through"* is not a defect here;
*"an honest engineer's credential reaches the sink"* is.

MEASUREMENTS behind the fixtures (re-derived 2026-07-26 at ``9c08cac``)
-----------------------------------------------------------------------
Every number below was measured against the base implementation, not recalled.
They are what makes the fixtures discriminating rather than decorative.

* The deleted catch-all mangled **89 of 1004 (8.9%)** distinct function names in
  the production packages, **227 of 494 (46.0%)** in ``scripts/`` and **3722 of
  5435 (68.5%)** in the test trees — this repo's long descriptive names are
  exactly the shape a bits/char threshold reads as random. (The audit's R2 figure
  of "201 of 1,616 / 12.4%" matches none of these four scopings; it was a
  different population. Regenerate with the corpus helper below.)
* It did **not** protect realistic operator passwords. ``correct-horse-battery-
  staple`` scores **3.495** bits/char against a **3.5** threshold — it survived
  the catch-all by 0.005 bits. ``lore-root-pw-not-a-real-one`` scores 3.102.
  The heuristic destroyed diagnostics it was not asked about and missed the
  credential class it was.

How to run:
    uv run pytest loremaster/tests/test_secret_leak_vectors.py -n auto -q
"""

from __future__ import annotations

import ast
import contextlib
import inspect
import io
import json
import logging
import re
import sys
import traceback
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from _logging_fixtures import (
    emit_through_configured_logger,
    make_record,
    parse_production_trees,
    production_sources,
    restored_lore_logger_state,
    workspace_roots,
)
from loremaster.logging_setup import (
    _ASSIGNMENT_RE,
    _BEARER_RE,
    EXC_FIELD,
    REDACTED,
    JsonFormatter,
    KeyValueFormatter,
    RedactingFilter,
    _scrub_text,
    _scrub_value,
    scrubbed_exception_text,
)
from pydantic import SecretStr

import loremaster

# --------------------------------------------------------------------------- #
# Credential fixtures — PRODUCTION SHAPES, obviously-fake bodies
# --------------------------------------------------------------------------- #
# Each is the shape of a credential family lore actually holds, because the pins
# below must not pass for a fixture reason. The character class and the ">= 24
# unbroken chars" length are load-bearing: both are precisely the window the
# DELETED ``_TOKEN_RE`` selected, so a build that keeps any catch-all is visible
# in the bound pins at the bottom of this module.

# ``embedding.api_key_env`` (LORE_TEI_KEY) holds a Voyage bearer key: ``pa-``
# followed by base64url. Measured entropy of the run: 5.393 bits/char.
VOYAGE_STYLE_KEY = "pa-Q4nT8vX2mK9wL5bR7yH3jD6sF1gA0cUeZpOiN2tVxYw"

# ``anthropic.api_key_env`` (ANTHROPIC_API_KEY) holds an ``sk-ant-api03-``
# prefixed key. Measured entropy of the run: 5.667 bits/char.
ANTHROPIC_STYLE_KEY = "sk-ant-api03-7hQ2xR9mB4kW1nT6vY8pL3cJ5dF0gS-aZeUiOoXtMrKyPqNwHbVjGl"

# ``surreal.password_env`` holds an OPERATOR-CHOSEN root password. Deliberately
# LOW entropy (3.102 bits/char, measured): the deleted catch-all never redacted
# this class of credential at all, so a pin that passes on it proves the TYPE is
# doing the work and not a leftover heuristic. This is the fixture that stops
# this module certifying the corpse.
SURREAL_ROOT_PASSWORD = "lore-root-pw-not-a-real-one"

# The three, as one parametrisable population. A pin exercised on only the
# high-entropy members would pass on a build that quietly kept the entropy sweep.
CREDENTIALS: list[tuple[str, str]] = [
    ("voyage-bearer", VOYAGE_STYLE_KEY),
    ("anthropic-key", ANTHROPIC_STYLE_KEY),
    ("surreal-root-password", SURREAL_ROOT_PASSWORD),
]

# Both production formatters. ``KeyValueFormatter`` appends the traceback BELOW
# the line while ``JsonFormatter`` folds it into one field — different code, so
# each is forced rather than one standing in for both (the quantifier law).
FORMATS: tuple[str, ...] = ("json", "keyvalue")

# What ``SecretStr`` renders instead of the value. Pinned as a literal here (and
# only here) because it is pydantic's contract, not lore's: if pydantic ever
# changed it, every "the secret is absent" pin below would still pass while the
# masking marker assertions would fail loudly rather than silently.
SECRET_MASK = "**********"

# The labels ``_ASSIGNMENT_RE`` recognises, with a representative literal for
# each. Cross-checked against the compiled pattern by
# ``test_the_label_set_is_derived_from_the_pattern`` so this list cannot drift
# into describing a pattern that no longer exists (CLAUDE.md: prose that
# describes behaviour is DERIVED from it, never restated beside it).
# The labels that live ONLY in ``_ASSIGNMENT_RE`` — dropping one is a silent
# narrowing with nothing else to catch it. ``authorization`` is deliberately NOT
# here: ruling R8's fix may legitimately move auth-header handling into its own
# scheme-aware pattern, and the behavioural pins below hold either way.
CORE_ASSIGNMENT_LABELS: frozenset[str] = frozenset(
    {"api[_-]?key", "apikey", "token", "secret", "password"}
)
ASSIGNMENT_LABEL_SAMPLES: list[tuple[str, str]] = [
    ("api_key", "api_key"),
    ("api-key", "api-key"),
    ("apikey", "apikey"),
    ("token", "token"),
    ("secret", "secret"),
    ("password", "password"),
    ("authorization", "authorization"),
    # ⚠ **RULING R37 — THE SEVEN ABOVE ARE ALL BARE WORDS, AND THAT WAS THE DEFECT.**
    # The "∀ label" pin ranged over a set that **structurally could not contain an
    # underscore compound**, so it could never reach the case its own name claims.
    # ``_ASSIGNMENT_RE`` anchors on ``\b``, and ``_`` is a WORD character — so
    # ``\bpassword\b`` never matches inside ``db_password``. Measured at 640b31b:
    # ``client_secret``, ``session_token``, ``db_password`` and **``SURREAL_PASS``**
    # all leaked; ``client-secret`` scrubbed.
    #
    # ``SURREAL_PASS`` is deliberately in this list: it is **our own env var name**,
    # so the pin is anchored to a real leak in this repo's own logs rather than to
    # an invented shape.
    ("client_secret compound", "client_secret"),
    ("session_token compound", "session_token"),
    ("db_password compound", "db_password"),
    ("SURREAL_PASS (ours)", "SURREAL_PASS"),
]

# The separators ``_ASSIGNMENT_RE`` accepts between label and value.
ASSIGNMENT_SEPARATORS: tuple[str, ...] = ("=", ": ", " = ", ":")


@pytest.fixture(autouse=True)
def _isolate_global_logging_state() -> Iterator[None]:
    """Restore every logger ``configure_logging`` mutates, around each test."""
    with restored_lore_logger_state():
        yield


# --------------------------------------------------------------------------- #
# Carriers — every shape a log call can carry a credential in
# --------------------------------------------------------------------------- #
# A CARRIER is written ONCE and driven with both a ``SecretStr`` and a bare
# ``str``. That is the whole discriminator: identical call-site code, identical
# sink, only the TYPE differs — so a green SecretStr leg next to a leaking
# bare-str leg proves the TYPE is the mechanism, not the fixture.
Carrier = Callable[[object], Callable[[logging.Logger], None]]


def _carrier_message(credential: object) -> Callable[[logging.Logger], None]:
    """The credential interpolated into the event string itself."""

    def action(logger: logging.Logger) -> None:
        logger.error(f"embed.probe.failed upstream rejected {credential}")

    return action


def _carrier_extra_scalar(credential: object) -> Callable[[logging.Logger], None]:
    """The credential as a flat ``extra=`` field (the Mezmo-indexed shape)."""

    def action(logger: logging.Logger) -> None:
        logger.error("embed.probe.failed", extra={"presented": credential})

    return action


def _carrier_extra_nested(credential: object) -> Callable[[logging.Logger], None]:
    """The credential nested in a container — ``_scrub_value``'s recursion path."""

    def action(logger: logging.Logger) -> None:
        logger.error(
            "store.connect.failed",
            extra={"attempts": [{"endpoint": "ws://127.0.0.1:18000/rpc", "cred": credential}]},
        )

    return action


def _carrier_positional_arg(credential: object) -> Callable[[logging.Logger], None]:
    """``logger.info("%s", credential)`` — the ``record.args`` path."""

    def action(logger: logging.Logger) -> None:
        logger.warning("embed.probe.unreachable presented=%s", credential)

    return action


def _carrier_exception_message(credential: object) -> Callable[[logging.Logger], None]:
    """The credential inside an exception message, logged with ``exc_info=True``."""

    def action(logger: logging.Logger) -> None:
        try:
            raise RuntimeError(f"upstream rejected the presented credential {credential}")
        except RuntimeError:
            logger.error("embed.probe.failed", exc_info=True)

    return action


def _carrier_exception_cause(credential: object) -> Callable[[logging.Logger], None]:
    """The credential in a ``raise … from …`` CAUSE — a second traceback section."""

    def action(logger: logging.Logger) -> None:
        try:
            try:
                raise ValueError(f"signin refused for {credential}")
            except ValueError as inner:
                raise RuntimeError("store.connect.failed") from inner
        except RuntimeError:
            logger.exception("store.connect.failed")

    return action


def _carrier_exception_note(credential: object) -> Callable[[logging.Logger], None]:
    """The credential in an ``__notes__`` entry — rendered after the message."""

    def action(logger: logging.Logger) -> None:
        try:
            error = RuntimeError("embed.probe.failed")
            error.add_note(f"sent credential {credential}")
            raise error
        except RuntimeError:
            logger.exception("embed.probe.failed")

    return action


TEXT_CARRIERS: list[tuple[str, Carrier]] = [
    ("message", _carrier_message),
    ("extra-scalar", _carrier_extra_scalar),
    ("extra-nested", _carrier_extra_nested),
    ("positional-arg", _carrier_positional_arg),
    ("exception-message", _carrier_exception_message),
    ("exception-cause", _carrier_exception_cause),
    ("exception-note", _carrier_exception_note),
]

# Every carrier deliberately carries the credential WITHOUT an adjacent label
# (no ``api_key=``, no ``Bearer ``), so the labelled patterns cannot be what
# saves it. The labelled shapes are pinned separately, below.
_CARRIER_IDS = [name for name, _ in TEXT_CARRIERS]
_CREDENTIAL_IDS = [name for name, _ in CREDENTIALS]


def _matrix() -> list[tuple[str, Carrier, str, str, str]]:
    """The full carrier x credential x format matrix, one tuple per case."""
    return [
        (carrier_name, carrier, credential_name, credential, fmt)
        for carrier_name, carrier in TEXT_CARRIERS
        for credential_name, credential in CREDENTIALS
        for fmt in FORMATS
    ]


_MATRIX = _matrix()
_MATRIX_IDS = [f"{c}-{k}-{f}" for c, _, k, _, f in _MATRIX]


class TestASecretStrCredentialNeverReachesARenderedLogLine:
    """The A18 REPLACEMENT CONTROL: the value cannot be in the text.

    The packet removes a detector and keeps no equivalent. What replaces it is
    the TYPE: a credential resolved through ``resolve_secret`` is a
    :class:`SecretStr` all the way to an allowlisted unwrap, and a ``SecretStr``
    renders ``**********`` through every path in the matrix below.

    ⚠ Every case here has a paired BARE-``str`` case in
    :class:`TestTheDeletionsResidualBoundsArePinned`, driving the SAME carrier
    through the SAME sink. Without that pairing, "the secret is absent" is
    satisfied just as happily by "nothing was emitted" — which is exactly how the
    #211 stack_info pin passed vacuously before its control was added.
    """

    @pytest.mark.parametrize("carrier_name,carrier,cred_name,credential,fmt", _MATRIX, ids=_MATRIX_IDS)
    def test_the_wrapped_credential_is_absent_from_the_emitted_bytes(
        self, carrier_name: str, carrier: Carrier, cred_name: str, credential: str, fmt: str
    ) -> None:
        output = emit_through_configured_logger(
            fmt, carrier(SecretStr(credential)), child=f"vec.{carrier_name}"
        )
        # ANTI-VACUITY: the record actually reached the sink. Asserted before the
        # absence claim, because an empty stream satisfies the absence claim.
        assert output.strip(), f"{carrier_name}/{fmt}: nothing was emitted — this pin is vacuous"
        assert credential not in output, (
            f"{cred_name} leaked through the {carrier_name} carrier into the {fmt} sink. "
            f"With the entropy catch-all deleted (packet 42 step 5), the SecretStr TYPE is "
            f"the only thing standing between this value and Mezmo.\n{output}"
        )

    @pytest.mark.parametrize("carrier_name,carrier", TEXT_CARRIERS, ids=_CARRIER_IDS)
    @pytest.mark.parametrize("fmt", FORMATS)
    def test_the_mask_appears_where_the_credential_was(
        self, carrier_name: str, carrier: Carrier, fmt: str
    ) -> None:
        # POSITIONAL, not merely "absent somewhere". The absence assertion above
        # is satisfied by a build that drops the field entirely; this one is not.
        # (The #211 wave shipped exactly that shape: a formatter that discarded
        # the exception passed every "the secret is not in the output" pin.)
        output = emit_through_configured_logger(
            fmt, carrier(SecretStr(VOYAGE_STYLE_KEY)), child=f"mask.{carrier_name}"
        )
        assert SECRET_MASK in output, (
            f"{carrier_name}/{fmt}: the credential is absent but so is the mask — the "
            f"carrier's payload was DROPPED rather than masked, which is a different "
            f"(and also wrong) build.\n{output}"
        )

    def test_a_secretstr_inside_a_config_repr_is_masked(self) -> None:
        # The realistic accidental shape: a whole config object logged for
        # diagnostics. This is what #211 was filed about.
        payload = {
            "surreal": {"user": "root", "password": SecretStr(SURREAL_ROOT_PASSWORD)},
            "embedding": {"api_key": SecretStr(VOYAGE_STYLE_KEY)},
        }
        output = emit_through_configured_logger(
            "json", lambda logger: logger.info("server.start", extra={"config": repr(payload)}), child="cfg"
        )
        assert SURREAL_ROOT_PASSWORD not in output
        assert VOYAGE_STYLE_KEY not in output
        # ⚠ The PROPERTY is "both credentials were neutralised, not dropped". This
        # asserted the SecretStr mask specifically, which encoded a mechanism that
        # then changed: once R38/R39 made the structured form redact, the masked
        # ``**********`` is itself replaced by ``***REDACTED***``, so counting the
        # mask went to zero while the property held perfectly. Assert the property
        # — either sentinel, twice — not the spelling of one mechanism.
        neutralised = output.count(SECRET_MASK) + output.count(REDACTED)
        assert neutralised >= 2, (
            f"both credentials must be masked or redacted, not dropped: {output}"
        )

    def test_the_low_entropy_password_proves_the_type_not_a_leftover_heuristic(self) -> None:
        # DISCRIMINATOR, stated as its own pin because it is the one this module
        # would be worthless without. ``SURREAL_ROOT_PASSWORD`` scores 3.102
        # bits/char against the DELETED threshold of 3.5 — the catch-all never
        # redacted it, at any point in this repo's history. So a green result
        # here cannot be attributed to a surviving detector: it is the type.
        record = make_record(msg="store.connect.failed", extra={"pw": SecretStr(SURREAL_ROOT_PASSWORD)})
        RedactingFilter().filter(record)
        rendered = JsonFormatter().format(record)
        assert SURREAL_ROOT_PASSWORD not in rendered
        assert SECRET_MASK in rendered


class TestTheLabelledPatternsSurviveTheDeletion:
    """A12/A13/A14/A15/A19: what the packet KEEPS must still work.

    Packet 42 Scope OUT is explicit — *"The labelled patterns stay. This packet
    does not remove defence-in-depth; it removes a guess."* A build that deletes
    the catch-all AND breaks a labelled pattern passes every pin in the class
    above (nothing there is labelled) and is a strict regression.
    """

    def test_bearer_is_redacted_and_the_scheme_word_is_preserved(self) -> None:
        # LABEL-PRESERVING, not just "redacted": a redacted line whose structure
        # is destroyed is the observability loss this packet exists to reverse.
        # The fixture is a bare ``Bearer <token>`` in running prose — the shape a
        # client echoes back — so ``_BEARER_RE`` is the only pattern in play and
        # the equality is a real statement about IT.
        scrubbed = _scrub_text(f"embed.probe.failed sent Bearer {VOYAGE_STYLE_KEY} upstream")
        assert VOYAGE_STYLE_KEY not in scrubbed
        assert scrubbed == f"embed.probe.failed sent Bearer {REDACTED} upstream"

    def test_the_bearer_scheme_word_survives_a_full_authorization_header(self) -> None:
        # ⚠ RULING R8 (2026-07-26) — a PRODUCTION BEHAVIOUR CHANGE, not a pin on
        # today's output. Measured at 9c08cac the real output was
        # ``Authorization: ***REDACTED*** ***REDACTED***``: ``_BEARER_RE`` fires,
        # then ``_ASSIGNMENT_RE`` matches its own ``authorization`` label and eats
        # the scheme word ``Bearer`` as if it were the value. The module docstring
        # promised ``Authorization: Bearer ***REDACTED***``, and the operator ruled
        # THE DOCSTRING IS RIGHT: the scheme is non-secret and tells an operator
        # WHICH auth mechanism failed — the same diagnostic-data argument that
        # justifies this entire packet.
        scrubbed = _scrub_text(f"Authorization: Bearer {VOYAGE_STYLE_KEY}")
        assert scrubbed == f"Authorization: Bearer {REDACTED}"

    def test_the_scheme_survives_case_insensitively_and_mid_line(self) -> None:
        # Two shapes the header actually arrives in: lowercased by an HTTP/2 client,
        # and quoted inside a rendered ``curl`` command in an exception message. A
        # fix keyed on the exact literal ``"Authorization: Bearer "`` passes the pin
        # above and fails both of these.
        lowered = _scrub_text(f"authorization: bearer {VOYAGE_STYLE_KEY}")
        assert lowered == f"authorization: bearer {REDACTED}"
        rendered = _scrub_text(f"curl -H 'Authorization: Bearer {VOYAGE_STYLE_KEY}' https://api/x")
        assert VOYAGE_STYLE_KEY not in rendered
        assert f"Authorization: Bearer {REDACTED}" in rendered
        assert "https://api/x" in rendered, "the rest of the line must survive"

    @pytest.mark.parametrize(
        "scheme,credential",
        [
            ("Basic", "dXNlcjpzdXBlcnNlY3JldHBhc3N3b3Jk"),
            ("Token", "8f3ka92mfLQ0zXvbNqRt"),
            ("ApiKey", "pa-Q4nT8vX2mK9wL5bR7yH3jD6sF1gA0cUeZpOiN2tVxYw"),
        ],
        ids=["basic", "token", "apikey"],
    )
    def test_a_NON_BEARER_AUTH_SCHEME_DOES_NOT_LEAK_ITS_CREDENTIAL(
        self, scheme: str, credential: str
    ) -> None:
        # ⚠ THE MOST IMPORTANT PIN THIS CLASS GAINED, and it is a LEAK, not a
        # cosmetic. R8 names Bearer; the SAME defect is live for every other
        # scheme, and for two of them it is already a credential leak TODAY.
        #
        # Measured 2026-07-26 at 9c08cac:
        #   'Authorization: Token 8f3ka92mfLQ0zXvbNqRt'
        #     -> 'Authorization: ***REDACTED*** 8f3ka92mfLQ0zXvbNqRt'
        # The scheme is redacted and THE CREDENTIAL SURVIVES — it is only 20 chars,
        # under the deleted catch-all's 24-char window, so nothing ever caught it.
        # 'Authorization: Basic <base64>' looks safe today ONLY because the entropy
        # catch-all redacted the base64 as a second pass; **delete the catch-all
        # and it leaks too.** That would make packet 42 a strict regression on the
        # one surface its own Scope OUT promises to keep protecting ("the labelled
        # patterns stay — this packet does not remove defence-in-depth").
        #
        # This asserts the SAFETY property (the credential is gone) for every
        # scheme, and R8's scheme preservation on top. A fix that simply deletes
        # ``authorization`` from _ASSIGNMENT_RE's label list satisfies R8's Bearer
        # pin above and makes every line here leak outright.
        scrubbed = _scrub_text(f"Authorization: {scheme} {credential}")
        assert credential not in scrubbed, (
            f"the {scheme} credential LEAKED. _ASSIGNMENT_RE consumes the scheme word as if it "
            f"were the value, leaving the real credential untouched: {scrubbed!r}"
        )
        # ⚠ **RULING R39 — THE QUOTED FORM, and the pin above could not reach it.**
        # This pin is receiver-blind about the SCHEME and was still defeated — not
        # by a scheme it did not know, but by a **QUOTE**. ``{'Authorization':
        # 'Basic <v>'}`` leaked while the bare header form scrubbed, because the
        # header pattern anchors on ``authorization\s*[=:]`` and a mapping repr puts
        # a quote between them. Same surface as #235/R8/R16; a form none of their
        # fixtures rendered.
        quoted = _scrub_text(f"{{'Authorization': '{scheme} {credential}'}}")
        assert credential not in quoted, (
            f"the {scheme} credential LEAKED from the QUOTED header form. A mapping repr is how "
            f"an httpx error actually renders headers: {quoted!r}"
        )
        assert scrubbed == f"Authorization: {scheme} {REDACTED}", (
            f"R8's rule is that the SCHEME survives and the credential does not: {scrubbed!r}"
        )

    @pytest.mark.parametrize(
        "scheme,credential",
        [
            ("Negotiate", "YIIZg2FhYmJjY2RkZWVmZmdnaGhpaWpq"),
            ("HOBA", "cGtqOTg3NjU0MzIxYWJjZGVm"),
            ("Mutual", "short123"),
            ("X-Vendor-Scheme", "kd82MfQ0zXvbNqRt"),
        ],
        ids=["negotiate", "hoba", "mutual-short", "vendor"],
    )
    def test_an_UNKNOWN_auth_scheme_does_not_leak_its_credential_either(
        self, scheme: str, credential: str
    ) -> None:
        # ⚠ THE RECEIVER-BLIND FORM, and it exists because the pin above is a NAME
        # LIST — "enumerate the forbidden and lose", the shape this repo has six
        # receipts on. The set of HTTP auth schemes is open: RFC 7235 registers
        # Negotiate, HOBA, Mutual, SCRAM…, and vendors invent their own.
        #
        # Measured 2026-07-26 at 9c08cac: 'Authorization: Mutual short123' ->
        # 'Authorization: ***REDACTED*** short123'. It LEAKS TODAY. Negotiate and
        # HOBA survive only because the entropy catch-all redacts their long
        # base64 on a second pass — **delete the catch-all and every unknown
        # scheme leaks.**
        #
        # This pin does not care what the scheme is CALLED. It forces the fix to be
        # general — treat whatever leading word precedes the credential as a
        # scheme — rather than a list that is wrong the day someone adds SCRAM.
        scrubbed = _scrub_text(f"Authorization: {scheme} {credential}")
        assert credential not in scrubbed, (
            f"the {scheme} credential LEAKED: {scrubbed!r}. A scheme ALLOWLIST cannot close "
            "this — the set of auth schemes is open. Redact whatever follows the leading "
            "scheme word, whatever that word is."
        )

    def test_every_allowlisted_scheme_takes_a_SINGLE_TOKEN_value(self) -> None:
        # ⚠ **RULING R33 — the pin that stops the next engineer inheriting a leak
        # we CAUSED.** ``Digest`` was allowlisted as a preservable scheme, but its
        # value is a **comma-separated auth-param list**
        # (``username="u", realm="r", response="<hash>"``), so preserving the
        # scheme and redacting one whitespace-delimited token destroys the username
        # and LOGS THE RESPONSE HASH. It is being removed from the production list.
        #
        # This pin is the general form: a scheme may only be allowlisted for
        # scheme-preservation if its credential is ONE token. ``Negotiate`` and
        # ``HOBA`` are the next candidates and each would have to pass this.
        from loremaster import logging_setup

        multi_token = 'username="alice", realm="lore", response="deadbeefcafef00d1234"'
        for scheme in re.split(r"\|", logging_setup._KNOWN_SCHEMES):
            scrubbed = _scrub_text(f"Authorization: {scheme} {multi_token}")
            assert "deadbeefcafef00d1234" not in scrubbed, (
                f"scheme {scheme!r} is allowlisted for scheme-preservation, but its credential "
                f"is not a single token — the tail survives redaction: {scrubbed!r}. Only "
                "single-token schemes may be preserved; the rest must redact the whole value."
            )

    def test_an_authorization_header_with_no_scheme_is_still_redacted(self) -> None:
        # The other direction, so the R8 fix cannot be "never redact after
        # ``Authorization:``". A bare credential with no scheme word must still go.
        scrubbed = _scrub_text(f"Authorization: {VOYAGE_STYLE_KEY}")
        assert VOYAGE_STYLE_KEY not in scrubbed
        assert scrubbed == f"Authorization: {REDACTED}"

    def test_the_assignment_form_of_authorization_is_still_redacted(self) -> None:
        # And the third door: ``authorization=<token>`` carries no scheme and no
        # colon. Removing ``authorization`` from the label alternation — the naive
        # way to satisfy R8 — un-redacts this. Pinned so that fix reddens.
        scrubbed = _scrub_text(f"authorization={ANTHROPIC_STYLE_KEY}")
        assert ANTHROPIC_STYLE_KEY not in scrubbed
        assert scrubbed == f"authorization={REDACTED}"

    def test_the_two_patterns_INTERACT_in_the_right_order(self) -> None:
        # ⚠ R8's ORDER RIDER, pinned as an OUTCOME rather than as a mechanism.
        #
        # The wrong build R8 names is one where the assignment pass treats the
        # scheme word as the value. Its fingerprint is DOUBLE REDACTION —
        # ``Authorization: ***REDACTED*** ***REDACTED***`` — which is exactly what
        # base produced (measured 2026-07-26 at 9c08cac). So the discriminator is
        # not "which regex ran first" but "how many things got redacted": ONE
        # credential in, exactly ONE sentinel out.
        #
        # Asserted this way ON PURPOSE. A pin that inspected pattern ORDER, or
        # required ``authorization`` to live in a particular regex, would forbid a
        # CORRECT fix — see this contract's report §0.5 Trap 3, where the only
        # design that satisfies every property here moves auth-header handling into
        # its own scheme-aware pattern. The outcome pin holds under every mechanism
        # and still fails every wrong one.
        scrubbed = _scrub_text(f"Authorization: Bearer {VOYAGE_STYLE_KEY}")
        assert scrubbed.count(REDACTED) == 1, (
            "one credential went in and more than one sentinel came out — the scheme word was "
            f"redacted as if it were a second secret: {scrubbed!r}"
        )
        assert scrubbed == f"Authorization: Bearer {REDACTED}"

    def test_disabling_the_authorization_label_does_not_satisfy_R8(self) -> None:
        # R8's rider names a specific wrong build: "fix" the render by dropping
        # ``authorization`` handling altogether. These are the three doors that
        # build opens, pinned by BEHAVIOUR so they hold however the label is
        # implemented — in ``_ASSIGNMENT_RE``, in a dedicated auth pattern, or
        # anywhere else. A build that drops the label WITHOUT replacing it fails
        # all three; a build that relocates it passes all three.
        for text, must_go in (
            (f"authorization={ANTHROPIC_STYLE_KEY}", ANTHROPIC_STYLE_KEY),
            (f"Authorization: {VOYAGE_STYLE_KEY}", VOYAGE_STYLE_KEY),
            ("Authorization: Basic dXNlcjpzdXBlcnNlY3JldA==", "dXNlcjpzdXBlcnNlY3JldA=="),
        ):
            scrubbed = _scrub_text(text)
            assert must_go not in scrubbed, (
                f"dropping the authorization label un-redacted {text!r} -> {scrubbed!r}. R8 asks "
                "for the SCHEME to be preserved, not for the label to be abandoned."
            )

    def test_the_anthropic_api_key_header_is_redacted(self) -> None:
        # The REAL production header shape for the calibration counter
        # (``x-api-key: <key>``), which reaches ``httpx`` and can be echoed back in
        # an error. ``\bapi[_-]?key\b`` matches inside ``x-api-key`` because ``-``
        # is a non-word character — verified rather than assumed.
        scrubbed = _scrub_text(f"x-api-key: {ANTHROPIC_STYLE_KEY}")
        assert ANTHROPIC_STYLE_KEY not in scrubbed
        assert scrubbed == f"x-api-key: {REDACTED}"

    @pytest.mark.parametrize(
        "label,literal", ASSIGNMENT_LABEL_SAMPLES, ids=[s[0] for s in ASSIGNMENT_LABEL_SAMPLES]
    )
    @pytest.mark.parametrize("separator", ASSIGNMENT_SEPARATORS)
    def test_every_labelled_assignment_is_redacted(self, label: str, literal: str, separator: str) -> None:
        # ∀ label x ∀ separator, forced individually. A build that keeps only the
        # ``api_key=`` spelling passes a single-sample pin and silently stops
        # redacting ``password:`` — which is the shape a SurrealDB signin error
        # actually carries.
        text = f"store.connect.failed {literal}{separator}{SURREAL_ROOT_PASSWORD} endpoint=ws://x/rpc"
        scrubbed = _scrub_text(text)
        assert SURREAL_ROOT_PASSWORD not in scrubbed, f"{literal}{separator}… was not redacted"
        assert f"{literal}{separator}{REDACTED}" in scrubbed, (
            "the label AND separator must survive so the line stays diagnosable"
        )

    def test_the_core_label_set_is_derived_from_the_pattern(self) -> None:
        # The samples above are a HAND LIST; this stops it describing a pattern
        # that no longer exists (CLAUDE.md: prose describing behaviour is DERIVED
        # from it, never restated beside it).
        #
        # ⚠ DELIBERATELY A SUPERSET CHECK, NOT AN EQUALITY. An earlier draft pinned
        # the alternation EXACTLY, including ``authorization`` — which would have
        # forbidden a correct R8 fix that moves auth-header handling into its own
        # scheme-aware pattern and drops ``authorization`` from this one. A
        # contract pins BEHAVIOUR; the behavioural guards are the 28-case matrix
        # above and the auth-header pins below, and they hold under either
        # mechanism. What this pins is only the five labels that have no other
        # home, so a silent narrowing of THOSE still reddens.
        match = re.search(r"\\b\(([^)]+)\)\\b", _ASSIGNMENT_RE.pattern)
        assert match is not None, "_ASSIGNMENT_RE no longer has a \\b(...)\\b label group"
        alternatives = frozenset(match.group(1).split("|"))
        assert CORE_ASSIGNMENT_LABELS <= alternatives, (
            "a label with no other pattern to catch it was dropped from _ASSIGNMENT_RE: "
            f"missing {sorted(CORE_ASSIGNMENT_LABELS - alternatives)}"
        )

    def test_the_bearer_pattern_still_exists_and_is_case_insensitive(self) -> None:
        # ``bearer``/``BEARER`` are both wire-legal; the pattern carries
        # ``re.IGNORECASE`` and a build that drops the flag looks identical in
        # every canonical-case fixture.
        assert _BEARER_RE.flags & re.IGNORECASE
        assert VOYAGE_STYLE_KEY not in _scrub_text(f"authorization: bearer {VOYAGE_STYLE_KEY}")

    def test_the_two_patterns_compose_in_one_line(self) -> None:
        # A12: ORDER. Both patterns fire on one string, each preserving its own
        # label. A build where one pattern consumes the other's match loses a
        # credential or a label.
        # Deliberately WITHOUT the ``Authorization:`` field name, whose own label
        # overlap is the separate (and unruled) case pinned above — this case is
        # about the two patterns coexisting, not about that interaction.
        text = f"upstream sent Bearer {VOYAGE_STYLE_KEY} and rejected api_key={ANTHROPIC_STYLE_KEY}"
        scrubbed = _scrub_text(text)
        assert VOYAGE_STYLE_KEY not in scrubbed
        assert ANTHROPIC_STYLE_KEY not in scrubbed
        assert f"Bearer {REDACTED}" in scrubbed
        assert f"api_key={REDACTED}" in scrubbed

    def test_scrubbing_is_idempotent(self) -> None:
        # A13. Two handlers, or a filter plus a formatter, may scrub the same
        # text twice; the second pass must be a no-op or REDACTED itself becomes
        # a moving target for consumers.
        text = f"Authorization: Bearer {VOYAGE_STYLE_KEY} api_key={ANTHROPIC_STYLE_KEY}"
        once = _scrub_text(text)
        # Guard against the degenerate reading: idempotence is trivially true of
        # the identity function, so prove redaction happened before proving it is
        # stable (CLAUDE.md: interrogate the assertion against its own message).
        assert REDACTED in once
        assert _scrub_text(once) == once
        assert _scrub_text(REDACTED) == REDACTED

    def test_all_three_consumers_route_through_the_one_scrub_implementation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A19 proven by MUTATION, not inspection (CLAUDE.md: routing is not
        # sharing). Replace the shared implementation with a sentinel; every
        # consumer must move with it. A consumer that inlined the regexes stays
        # unchanged and is a private copy wearing the shared name.
        sentinel = "SCRUBBED-BY-THE-SHARED-SEAM"
        from loremaster import logging_setup

        monkeypatch.setattr(logging_setup, "_scrub_text", lambda _value: sentinel)

        # 1. RedactingFilter.filter
        record = make_record(msg="store.connect.failed", extra={"detail": "anything"})
        logging_setup.RedactingFilter().filter(record)
        assert record.msg == sentinel, "RedactingFilter.filter does not route through _scrub_text"
        # 2. _scrub_value (the extra/container path)
        assert record.detail == sentinel, "_scrub_value does not route through _scrub_text"  # type: ignore[attr-defined]
        # 3. scrubbed_exception_text
        exc_record = make_record(msg="store.connect.failed")
        exc_record.exc_text = 'Traceback (most recent call last):\n  File "x.py", line 1\nRuntimeError: no'
        assert logging_setup.scrubbed_exception_text(exc_record) == sentinel, (
            "scrubbed_exception_text does not route through _scrub_text"
        )

    def test_scrub_value_leaves_non_string_scalars_untouched(self) -> None:
        # A19's other half: the recursion must not stringify structured fields.
        # A build that coerced everything to str would pass every leak pin above
        # and destroy Mezmo's numeric indexing.
        assert _scrub_value(5) == 5
        assert _scrub_value(None) is None
        assert _scrub_value(True) is True
        assert _scrub_value(["a", 1, {"b": 2}]) == ["a", 1, {"b": 2}]

    def test_a_labelled_credential_is_still_scrubbed_out_of_a_real_traceback(self) -> None:
        # End to end on the surface that matters: the labelled patterns must
        # still reach the RENDERED EXCEPTION, which is a different code path from
        # msg/extra (it goes through _render_exception + exc_text).
        def action(logger: logging.Logger) -> None:
            try:
                raise RuntimeError(f"signin refused for password={SURREAL_ROOT_PASSWORD}")
            except RuntimeError:
                logger.exception("store.connect.failed")

        parsed = json.loads(emit_through_configured_logger("json", action, child="labelled-tb"))
        assert "Traceback" in parsed[EXC_FIELD], "no traceback rendered — the pin would be vacuous"
        assert SURREAL_ROOT_PASSWORD not in parsed[EXC_FIELD]
        assert f"password={REDACTED}" in parsed[EXC_FIELD]


def _scripts_module(name: str) -> Any:
    """Import a module out of the non-package ``scripts/`` directory.

    Mirrors ``scripts/test_snapshot_gc.py``'s idiom — ``scripts/`` is not a
    package, so the directory has to be on ``sys.path`` first.
    """
    package_file = loremaster.__file__
    assert package_file is not None, "loremaster imported as an empty namespace package"
    scripts_root = Path(package_file).resolve().parent.parent.parent / "scripts"
    if str(scripts_root) not in sys.path:
        sys.path.insert(0, str(scripts_root))
    import importlib

    return importlib.import_module(name)


def _production_function_names() -> list[str]:
    """Every distinct function name defined in the production packages.

    DERIVED from the live tree, never a hand-list — this is the corpus audit R2
    measured against, and regenerating it is how the "recovered data" receipt the
    packet's Exit clause asks for stays honest as the tree changes.
    """
    # ⚠ REWIRED to the ONE shared parser (F4 / #279): routes its whole-workspace parse
    # through ``parse_production_trees`` so no private ast.parse loop escapes L1's runtime
    # chokepoint. ``include_scripts=False, include_skills=False`` preserves the members-prod
    # corpus this pin measured (production packages have no test files nested in them).
    names: set[str] = set()
    for _relative, tree in parse_production_trees(include_scripts=False, include_skills=False).items():
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
    return sorted(names)


class TestScrubbingNoLongerDestroysDiagnosticData:
    """The RECOVERED DATA — audit R2 and #227, both dissolved by the deletion.

    This is the packet's payoff, and it is pinned as a REGRESSION guard rather
    than left to hold trivially: every assertion here goes RED the day anyone
    re-introduces a shape-based detector, whatever they call it. That is the
    point — the property must be guarded by a mechanism, not by the memory of
    why the mechanism was removed (CLAUDE.md: a diagnosis is not an instrument).
    """

    # The four false-positive classes #227 was filed for. Every path is
    # CONSTRUCTED, never taken from the running checkout: this repo happens to
    # live at a path with no high-entropy component, so a pin rendering the real
    # ``__file__`` would pass here and fail on a CI runner — the fixture would
    # guarantee the one condition under which the bug is invisible.
    HOSTILE_PATHS: list[tuple[str, str]] = [
        ("uuid workspace", "/tmp/ci/090685cb-2064-498d-8479-e141e4fd4ea5/loremaster/store/surreal.py"),
        (
            "container overlay",
            "/var/lib/containers/storage/overlay/"
            "3f786850e387550fdab836ed7e6dc881de23001b2b4a3f7a4a5b6c7d8e9f0a1b/merged/app.py",
        ),
        ("nix store", "/nix/store/1a2b3c4d5e6f7g8h9i0jklmnopqrstuv-python3-3.14.6/lib/x.py"),
        ("hashed checkout", "/build/9f8e7d6c5b4a39281706f5e4d3c2b1a09f8e7d6c/src/indexer.py"),
    ]

    def test_the_function_name_corpus_actually_exercises_the_deleted_window(self) -> None:
        # POSITIVE CONTROL for the ∀ pin below. The deleted ``_TOKEN_RE`` only
        # examined unbroken runs of >= 24 chars, so a corpus of short names would
        # pass the pin without touching the mechanism at all.
        corpus = _production_function_names()
        long_enough = [name for name in corpus if len(name) >= 24]
        assert len(corpus) >= 800, f"the corpus collapsed to {len(corpus)} names — the scan is broken"
        assert len(long_enough) >= 50, (
            f"only {len(long_enough)} production function names are >= 24 chars — this corpus no "
            "longer reaches the window the deleted catch-all selected, so the pin below is vacuous"
        )

    def test_no_production_function_name_is_mangled(self) -> None:
        # AUDIT R2, reversed. Measured 2026-07-26 at 9c08cac: 89 of 1004 (8.9%)
        # distinct production function names were erased from every traceback
        # frame by the catch-all. Zero is the contract.
        corpus = _production_function_names()
        mangled = [name for name in corpus if _scrub_text(name) != name]
        assert not mangled, (
            f"{len(mangled)} of {len(corpus)} production function names are still being erased "
            f"from tracebacks. Packet 42 deleted the mechanism that did this; if something "
            f"re-introduced a shape-based detector, that is the whole finding chain "
            f"(#211 -> #227 -> R1 -> R2) starting over. First few: {mangled[:8]}"
        )

    @pytest.mark.parametrize("label,path", HOSTILE_PATHS, ids=[p[0] for p in HOSTILE_PATHS])
    def test_a_hashy_absolute_path_survives_verbatim(self, label: str, path: str) -> None:
        # #227. This used to require a four-condition exemption (inventory
        # A4-A9); it now holds because nothing examines the run at all. The pin
        # stays because the PROPERTY is what mattered, never the mechanism.
        assert _scrub_text(path) == path, f"the {label} path was mangled"

    def test_a_git_sha_in_prose_survives(self) -> None:
        # A16, INVERTED. ``TestBareHexRunsStayRedactedKnownBound`` pinned this
        # value as an ACCEPTED FALSE POSITIVE; the bound dissolved with the
        # mechanism, so the same value is now pinned as data that must survive.
        # It rhymes with #131, where git provenance was silently empty in
        # production for months — this is the sink-side half of that loss,
        # closed.
        sha = "8538303a1b2c3d4e5f60718293a4b5c6d7e8f9a0"
        assert _scrub_text(f"commit {sha} landed") == f"commit {sha} landed"

    def test_a_correlation_uuid_in_prose_survives(self) -> None:
        # A9/A17. Previously exempted by ``_UUID_RE``; now no exemption is
        # needed because there is no sweep. A trace/run id must reach Mezmo.
        trace_id = "090685cb-2064-498d-8479-e141e4fd4ea5"
        text = f"trace.emit ok correlation {trace_id} span=search"
        assert _scrub_text(text) == text

    def test_a_harness_database_name_survives(self) -> None:
        # Built by the PRODUCTION builder rather than a hand-copied literal, so
        # this pin follows the convention if ``unique_database`` ever changes its
        # shape (CLAUDE.md clause: shared domain conventions, never literals).
        from _surreal_harness import unique_database

        database_name = unique_database()
        assert _scrub_text(f"store.bootstrap database={database_name}") == (
            f"store.bootstrap database={database_name}"
        )

    def test_a_clean_traceback_is_returned_byte_exact(self) -> None:
        # R2's other half: the RENDERED SOURCE LINES. A traceback is mostly
        # paths, dotted module names and identifiers; a scrubber that eats them
        # is not better than one that drops the traceback entirely.
        def action(logger: logging.Logger) -> None:
            try:
                _raise_with_a_long_identifier_on_the_line()
            except RuntimeError:
                logger.exception("index.file.failed")

        parsed = json.loads(emit_through_configured_logger("json", action, child="clean-tb"))
        rendered = parsed[EXC_FIELD]
        assert REDACTED not in rendered, f"a clean traceback was redacted:\n{rendered}"
        assert "_raise_with_a_long_identifier_on_the_line" in rendered
        assert "test_secret_leak_vectors.py" in rendered


def _raise_with_a_long_identifier_on_the_line() -> None:
    """Raise from a line whose identifiers exceed the deleted 24-char window.

    The function NAME is itself 41 characters of ``[a-z_]`` — an unbroken run the
    deleted ``_TOKEN_RE`` selected and (measured at base) redacted. The rendered
    frame therefore carries a value the old mechanism destroyed, which is what
    makes the "clean traceback" pin above discriminating rather than decorative.
    """
    raise RuntimeError("upstream_embedding_endpoint_did_not_respond")


class TestNoTracebackFormatterRendersFrameLocals:
    """Packet 42 step 4 — PIN M4, do not assume it.

    M4 measured that nothing in this codebase renders frame LOCALS, so a secret
    held in a variable never reaches a traceback. The packet is explicit that
    this *"is a property of the code TODAY and is exactly the kind of thing a
    future dependency change silently breaks"* — ``rich`` 15.0.0 IS in the
    dependency closure (verified 2026-07-26), so ``rich.traceback.install(
    show_locals=True)`` is one line away from reopening the vector.

    The pins are ordered strongest-first:

    * **Leg A/B are PROPERTY pins and name nothing.** They render a real
      secret-bearing frame through the production logging path and through
      ``sys.excepthook`` AS CURRENTLY BOUND, and assert the value is absent.
      Whatever installed the hook, and whatever it is called, is exercised. A
      harmless ``rich.traceback.install()`` (``show_locals`` defaults to False)
      stays green — which is correct, because the property still holds, and a
      gate that refuses honest code is a gate that gets switched off.
    * **Leg C is a NAME-keyed structural pin and says so.** It is the cheap
      mechanical half; its bound is pinned in
      ``test_the_structural_leg_is_keyed_on_api_names_and_says_so``.
    """

    @staticmethod
    def _raise_holding_a_credential_in_a_local(credential: object) -> None:
        """Raise from a frame whose LOCAL holds the credential.

        The value arrives as a PARAMETER and is never written as a literal, so
        the rendered source line names ``held_credential``, not the value. That
        distinction is the whole M1-vs-M4 boundary and it is easy to get wrong: a
        first draft of this probe put the credential in a module-level literal
        and "leaked" through ``rich``'s +/-3-line source WINDOW, not through
        locals at all.
        """
        held_credential = credential
        assert held_credential is not None
        raise RuntimeError("store.connect.failed")

    def test_a_frame_local_is_not_rendered_through_the_production_log_path(self) -> None:
        def action(logger: logging.Logger) -> None:
            try:
                self._raise_holding_a_credential_in_a_local(ANTHROPIC_STYLE_KEY)
            except RuntimeError:
                logger.exception("store.connect.failed")

        parsed = json.loads(emit_through_configured_logger("json", action, child="m4-log"))
        rendered = parsed[EXC_FIELD]
        # ANTI-VACUITY first: the frame IS in the traceback.
        assert "_raise_holding_a_credential_in_a_local" in rendered
        assert ANTHROPIC_STYLE_KEY not in rendered, (
            "the logging path rendered a frame LOCAL — M4 no longer holds and the packet's "
            "central safety argument is void"
        )

    def test_a_frame_local_is_not_rendered_through_the_bound_excepthook(self) -> None:
        # RECEIVER-BLIND: whatever ``sys.excepthook`` is at this moment gets
        # driven with a secret-bearing frame. No dependency is named, so a hook
        # installed by a package nobody thought of is still exercised.
        rendered = _render_through_bound_excepthook(ANTHROPIC_STYLE_KEY)
        assert "_raise_holding_a_credential_in_a_local" in rendered or "RuntimeError" in rendered, (
            "the excepthook produced nothing recognisable — this pin is vacuous"
        )
        assert ANTHROPIC_STYLE_KEY not in rendered, (
            "the process-level exception hook renders frame LOCALS. Container stderr is a "
            "served surface; this reopens the vector packet 42 measured shut (M4)."
        )

    def test_the_probe_can_actually_see_a_locals_leak(self) -> None:
        # POSITIVE CONTROL for the two pins above (CLAUDE.md: a probe needs a
        # control — the auditor's instrument can lie the same way the author's
        # did). Install a locals-rendering hook on purpose and prove the probe
        # catches it. Measured 2026-07-26: rich 15.0.0 with show_locals=True
        # leaks; with show_locals=False it does not.
        rich_traceback = pytest.importorskip("rich.traceback")
        from rich.console import Console

        buffer = io.StringIO()
        saved_hook = sys.excepthook
        try:
            rich_traceback.install(
                console=Console(file=buffer, width=200), show_locals=True, extra_lines=0
            )
            try:
                self._raise_holding_a_credential_in_a_local(ANTHROPIC_STYLE_KEY)
            except RuntimeError:
                sys.excepthook(*sys.exc_info())
            leaked = buffer.getvalue()
        finally:
            sys.excepthook = saved_hook
        assert ANTHROPIC_STYLE_KEY in leaked, (
            "the control did NOT reproduce a locals leak — the two pins above may be "
            "passing for a reason unrelated to what they claim to check"
        )

    def test_a_secretstr_local_masks_even_under_a_locals_rendering_hook(self) -> None:
        # DEFENCE IN DEPTH, and the reason the type migration matters more than
        # the M4 pin: even if a future dependency DOES render locals, a credential
        # that is a SecretStr masks anyway. This is the composition of M2 and M4
        # and it is the property that survives a dependency change.
        rich_traceback = pytest.importorskip("rich.traceback")
        from rich.console import Console

        buffer = io.StringIO()
        saved_hook = sys.excepthook
        try:
            rich_traceback.install(
                console=Console(file=buffer, width=200), show_locals=True, extra_lines=0
            )
            try:
                self._raise_holding_a_credential_in_a_local(SecretStr(ANTHROPIC_STYLE_KEY))
            except RuntimeError:
                sys.excepthook(*sys.exc_info())
            rendered = buffer.getvalue()
        finally:
            sys.excepthook = saved_hook
        assert "held_credential" in rendered, "the hook did not render locals — pin is vacuous"
        assert ANTHROPIC_STYLE_KEY not in rendered

    def test_no_production_source_enables_locals_capture_or_installs_a_hook(self) -> None:
        # LEG C, the structural half. Three doors exist in the closure:
        #   traceback.TracebackException(capture_locals=True)  [stdlib — verified
        #     2026-07-26 to render local VALUES; plain format_exception does not]
        #   rich.traceback.Traceback/install(show_locals=True)
        #   any assignment to sys.excepthook
        offenders: list[str] = []
        # Routed through the SHARED ONE parser (F4 / #279) — the split-leg
        # ``_workspace_python_sources()`` + ``ast.parse`` loop is gone, so L1 sees this scan
        # SANCTIONED. ``include_skills=True`` matches the old ``production_sources()`` reach;
        # the parser also covers scripts/skills test files (measured to add no new offenders).
        for display, tree in parse_production_trees(include_scripts=True, include_skills=True).items():
            for node in ast.walk(tree):
                if isinstance(node, ast.keyword) and node.arg in {"capture_locals", "show_locals"}:
                    if isinstance(node.value, ast.Constant) and node.value.value is True:
                        offenders.append(f"{display}:{node.value.lineno} {node.arg}=True")
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Attribute) and target.attr == "excepthook":
                            offenders.append(f"{display}:{node.lineno} assigns sys.excepthook")
        assert not offenders, (
            "production code now renders frame locals or hijacks the exception hook. M4 was "
            "the packet-42 measurement that made deleting the entropy catch-all safe; if this "
            "is deliberate, the trade has to be re-made explicitly:\n  " + "\n  ".join(offenders)
        )

    def test_the_structural_leg_is_keyed_on_api_names_and_says_so(self) -> None:
        # AN HONEST BOUND, stated as a test so it cannot be mistaken for total
        # coverage (the same shape as #211's own name-keyed honesty pin). Leg C
        # is keyed on THREE API names; the set of ways a dependency could render
        # locals is not closed, and a THIRD-PARTY package that installs a hook at
        # import is invisible to any AST scan of OUR source (#137's bound, same
        # class). Legs A and B are the property instruments that do not depend on
        # names — they exercise whatever hook is actually bound.
        #
        # RE-OPEN TRIGGER: the day a dependency is added that installs an
        # excepthook or a logging handler of its own, Legs A/B must be extended
        # to run in a subprocess that imports the production entry point, because
        # an in-process pytest run can mask an import-time hook installation.
        assert True

    def test_the_stdlib_renderer_used_by_logging_does_not_capture_locals(self) -> None:
        # The measurement M1 rests on, re-derived here rather than trusted: the
        # stdlib's plain rendering shows the source LINE and never local VALUES.
        try:
            self._raise_holding_a_credential_in_a_local(ANTHROPIC_STYLE_KEY)
            raise AssertionError("the fixture did not raise — this pin would be vacuous")
        except RuntimeError:
            exception = sys.exception()
        assert exception is not None
        plain = "".join(traceback.format_exception(exception))
        with_locals = "".join(
            traceback.TracebackException.from_exception(exception, capture_locals=True).format()
        )
        assert ANTHROPIC_STYLE_KEY not in plain
        # And the CONTROL that proves the fixture delivers a local at all — if
        # this ever stopped being true, the pin above would be vacuous.
        assert ANTHROPIC_STYLE_KEY in with_locals


def _render_through_bound_excepthook(credential: str) -> str:
    """Drive ``sys.excepthook`` as currently bound; return what it wrote."""
    buffer = io.StringIO()
    try:
        TestNoTracebackFormatterRendersFrameLocals._raise_holding_a_credential_in_a_local(credential)
    except RuntimeError:
        with contextlib.redirect_stderr(buffer):
            sys.excepthook(*sys.exc_info())
    return buffer.getvalue()


def _workspace_python_sources() -> list[tuple[str, Path]]:
    """Every production ``.py`` file this packet governs.

    ⚠ REWIRED to the ONE shared root list. This carried a private copy missing
    BOTH ``lorerunes`` and ``skills`` — so the M4 locals gate, whose property is
    "no production code renders frame locals", was not looking at two trees of
    production code.
    """
    return production_sources()


class TestTheDeletionsResidualBoundsArePinned:
    """A16/A17/A18 + M1 — what the deletion COSTS, pinned so it is not rediscovered.

    Deleting the catch-all genuinely WIDENS exposure: an unlabelled credential in
    free log text is no longer redacted. The operator ruling that authored packet
    42 accepted that trade, on the grounds that the detector *"paid for a guess
    with real diagnostic data"* four rounds running and that the replacement
    control (the ``SecretStr`` type + the allowlisted unwrap surface) prevents the
    value being in the text at all.

    **An unpinned known limitation is indistinguishable from an unknown one.**
    These pins ASSERT THE HOLE. Each goes RED the day someone closes it, carrying
    the message that says so — so a future engineer meets the bound deliberately,
    with its rationale attached, and cannot silently re-open a settled trade.

    **RE-OPEN TRIGGER (a bound without one is a can-kick):** if a credential is
    ever confirmed in a production log line despite the type migration — i.e. if
    the replacement control is measured to have failed rather than assumed to
    work. At that point the fix is NOT another detector: it is to find the unwrap
    site that let a bare value escape, and to close it in
    ``test_secret_typing.UNWRAP_ALLOWLIST``.
    """

    _CLOSED_DELIBERATELY = (
        "If you closed this hole DELIBERATELY, delete this pin and say so in your report, "
        "naming the ruling that authorised it. If it closed by accident, something "
        "re-introduced a shape-based detector and the #211 -> #227 -> R1 -> R2 chain is "
        "starting over."
    )

    @pytest.mark.parametrize("name,credential", CREDENTIALS, ids=_CREDENTIAL_IDS)
    def test_an_unlabelled_credential_in_free_text_is_not_redacted(
        self, name: str, credential: str
    ) -> None:
        # A18, the deliberate trade, stated at the unit seam.
        text = f"upstream rejected the request: {credential}"
        assert _scrub_text(text) == text, f"{name}: {self._CLOSED_DELIBERATELY}"

    @pytest.mark.parametrize("carrier_name,carrier", TEXT_CARRIERS, ids=_CARRIER_IDS)
    @pytest.mark.parametrize("fmt", FORMATS)
    def test_a_bare_str_credential_does_reach_the_sink(
        self, carrier_name: str, carrier: Carrier, fmt: str
    ) -> None:
        # THE PAIRED CONTROL for TestASecretStrCredentialNeverReachesARenderedLogLine.
        # Same carrier, same sink, only the TYPE differs. Two jobs in one pin:
        #   (a) it proves the oracle can SEE a leak, so the SecretStr legs are not
        #       passing because nothing was emitted, and
        #   (b) it is the A18 bound itself, per carrier and per format.
        output = emit_through_configured_logger(
            fmt, carrier(VOYAGE_STYLE_KEY), child=f"bound.{carrier_name}"
        )
        assert VOYAGE_STYLE_KEY in output, (
            f"{carrier_name}/{fmt}: a BARE credential no longer reaches the sink. "
            f"{self._CLOSED_DELIBERATELY}"
        )

    def test_a_hardcoded_unlabelled_credential_reaches_the_rendered_source_line(self) -> None:
        # M1's residual. A traceback quotes each frame's SOURCE LINE, so a
        # credential written as a LITERAL at a call site reaches the log even
        # though nothing about it is "in flight". SecretStr cannot help here — a
        # literal in source is a source-level defect, not a typing one.
        try:
            _call_with_a_hardcoded_unlabelled_credential()
            raise AssertionError("the fixture did not raise — this pin would be vacuous")
        except RuntimeError:
            rendered = traceback.format_exc()
        # POSITIVE CONTROL first (the R3 lesson): prove the fixture delivers the
        # literal to the rendered text, or "it survived scrubbing" is vacuous.
        assert HARDCODED_UNLABELLED_LITERAL in rendered, (
            "the fixture no longer puts the literal on the rendered frame line"
        )
        assert HARDCODED_UNLABELLED_LITERAL in _scrub_text(rendered), self._CLOSED_DELIBERATELY

    def test_a_hardcoded_LABELLED_credential_is_still_scrubbed_from_the_source_line(self) -> None:
        # THE OTHER HALF, and the reason the bound above is narrow rather than
        # total: the realistic hardcoded shape carries a keyword, and the
        # labelled patterns still catch it. A build that deleted _ASSIGNMENT_RE
        # along with the catch-all passes the bound pin above and fails here.
        try:
            _call_with_a_hardcoded_labelled_credential()
            raise AssertionError("the fixture did not raise — this pin would be vacuous")
        except RuntimeError:
            rendered = traceback.format_exc()
        assert HARDCODED_LABELLED_LITERAL in rendered, "the fixture no longer delivers the literal"
        assert HARDCODED_LABELLED_LITERAL not in _scrub_text(rendered)
        assert REDACTED in _scrub_text(rendered)

    def test_a_credential_in_a_url_path_segment_is_not_redacted(self) -> None:
        # A17. Previously a bound BOUGHT by the path exemption; now simply a
        # consequence of having no detector. Recorded so the two are not confused
        # by a later reader: nothing was traded away here, the mechanism went.
        url = f"https://api.voyageai.com/{VOYAGE_STYLE_KEY}/v1/embeddings"
        assert _scrub_text(url) == url, self._CLOSED_DELIBERATELY

    def test_the_replacement_control_is_what_covers_this_bound(self) -> None:
        # The bound above is only acceptable BECAUSE of this. Stated as a pin so
        # the two travel together: if the type migration were ever reverted, this
        # goes RED and the accepted trade is void.
        from loremaster.config import resolve_secret

        with pytest.MonkeyPatch.context() as patcher:
            patcher.setenv("LORE_PKT42_PROBE_KEY", VOYAGE_STYLE_KEY)
            resolved = resolve_secret("LORE_PKT42_PROBE_KEY")
        assert isinstance(resolved, SecretStr)
        record = make_record(msg="embed.probe.failed", extra={"api_key": resolved})
        RedactingFilter().filter(record)
        assert VOYAGE_STYLE_KEY not in KeyValueFormatter().format(record)


# A credential written as a LITERAL at a call site, with NO adjacent label. Kept
# at module scope so the two fixture functions below are the only lines that
# carry it — a traceback quotes the RAISING line, so the literal must be on the
# call, not on a guard above it (cold-audit R3).
HARDCODED_UNLABELLED_LITERAL = "Zt7QnP4xW9kLm2Rb8VyH3sJd6FgA1cUe0oIT"
HARDCODED_LABELLED_LITERAL = "Yq2WmR8vT5nK1bX7cJ4hL9dF6gA3sZ0pUeIo"


def _refuse(**_credentials: str) -> None:
    """Raise, so the CALLER's line — which carries the literal — is rendered."""
    raise RuntimeError("connection refused")


def _call_with_a_hardcoded_unlabelled_credential() -> None:
    """Raise from a line carrying a bare credential literal with no label."""
    _refuse(presented="Zt7QnP4xW9kLm2Rb8VyH3sJd6FgA1cUe0oIT")


def _call_with_a_hardcoded_labelled_credential() -> None:
    """Raise from a line carrying a credential literal behind a ``token=`` label."""
    _refuse(token="Yq2WmR8vT5nK1bX7cJ4hL9dF6gA3sZ0pUeIo")


class TestTheEntropyMachineryIsGone:
    """Packet 42 steps 5 + 6: the mechanism and everything it forced are DELETED.

    Retired-symbol pins (the repo idiom). A build that keeps the code but stops
    calling it passes every behavioural pin above while leaving the next engineer
    a loaded gun and the exemption machinery it needed.
    """

    RETIRED_NAMES = [
        "_TOKEN_RE",
        "_ENTROPY_BITS_THRESHOLD",
        "_shannon_entropy_bits",
        "_is_safe_high_entropy_run",
        "_is_absolute_path_component",
        "_PATH_BLOB_CHARS",
        "_PATH_SEPARATOR",
        "_UUID_RE",
    ]

    @pytest.mark.parametrize("name", RETIRED_NAMES)
    def test_the_symbol_is_gone(self, name: str) -> None:
        from loremaster import logging_setup

        assert not hasattr(logging_setup, name), (
            f"{name} still exists. Packet 42 step 6 is explicit that #227's exemption and "
            "its four conditions, the bare-hex bound and the UUID bound are retired WITH the "
            "catch-all — 'do not leave them as vestigial guards'."
        )

    def test_the_kept_symbols_are_still_there(self) -> None:
        # POSITIVE CONTROL for the retired-symbol scan: prove the module is the
        # one under test and that ``hasattr`` discriminates at all. Without this
        # a typo'd import name would make every pin above pass vacuously.
        from loremaster import logging_setup

        for kept in ("_BEARER_RE", "_ASSIGNMENT_RE", "_scrub_text", "REDACTED", "RedactingFilter"):
            assert hasattr(logging_setup, kept), f"{kept} is missing — packet 42 keeps it"

    # The phrases that name the DELETED mechanism. Kept as one list so both legs
    # below read from the same source of truth.
    CORPSE_PROSE = ["Shannon entropy", "high-entropy token", "entropy threshold", "catch-all backstop"]

    # Words that make a mention HISTORICAL rather than a live claim. A test module
    # explaining what was removed is doing its job; one asserting the mechanism
    # still runs is teaching a corpse.
    DELETION_MARKERS = [
        "delet", "retir", "no longer", "used to", "was ", "were ", "packet 42",
        "dissolv", "former", "pre-r", "at base", "before ",
    ]

    def test_no_PRODUCTION_prose_teaches_a_mechanism_it_does_not_run(self) -> None:
        # ⚠ **REACH WIDENED (REFACTOR §4.D).** This read ONE file —
        # ``logging_setup.__file__`` — and that narrow reach is *why three corpse-prose
        # sites survived the deletion*, one of them a class docstring stating outright
        # that high-entropy tokens are scrubbed. The refactorer fixed those three by
        # hand; nothing stopped the fourth. Per CLAUDE.md — *"every audit-caught defect
        # class becomes a repo-local invariant test"* — the property is now quantified
        # over every production source this packet governs, via the ONE shared root list.
        offenders = [
            f"{display}: {phrase}"
            for display, source_path in _workspace_python_sources()
            for phrase in self.CORPSE_PROSE
            if phrase.lower() in source_path.read_text(encoding="utf-8").lower()
        ]
        assert not offenders, (
            "production prose still teaches the deleted entropy heuristic. A doc that describes "
            "a mechanism the code does not run is how this repo ships green-at-gate defects "
            "(CLAUDE.md, rename/reshape sweeps):\n  " + "\n  ".join(offenders)
        )

    def test_no_PACKET_TEST_prose_claims_the_mechanism_still_RUNS(self) -> None:
        # The second half of the reach, and it needs a different predicate. These
        # test modules legitimately NARRATE the deleted mechanism — explaining what
        # was removed and why is most of their value — so a flat blocklist here
        # would be a false gate that gets switched off.
        #
        # The distinction that matters is TENSE: "the catch-all used to redact this"
        # is documentation; "high-entropy tokens are scrubbed" is a corpse. So a
        # mention is allowed only in the presence of a deletion marker within its
        # own comment/docstring neighbourhood. Measured 2026-07-27: every existing
        # mention in these five modules passes, so this costs nothing today and
        # catches the fourth site tomorrow.
        packet_modules = [
            Path(__file__).with_name(name)
            for name in (
                "test_secret_leak_vectors.py",
                "test_logging_setup.py",
                "test_secret_typing.py",
                "test_secret_resolution_seam.py",
            )
        ]
        offenders: list[str] = []
        for module_path in packet_modules:
            lines = module_path.read_text(encoding="utf-8").splitlines()
            for index, line in enumerate(lines):
                if not any(phrase.lower() in line.lower() for phrase in self.CORPSE_PROSE):
                    continue
                neighbourhood = " ".join(lines[max(0, index - 6) : index + 7]).lower()
                if not any(marker in neighbourhood for marker in self.DELETION_MARKERS):
                    offenders.append(f"{module_path.name}:{index + 1} {line.strip()[:70]}")
        assert not offenders, (
            "these test-module mentions of the deleted entropy heuristic read as LIVE claims "
            "rather than history. Say what was removed, in the past tense, or the next reader "
            "learns a mechanism that does not exist:\n  " + "\n  ".join(offenders)
        )

    def test_the_prose_gate_can_actually_fire(self) -> None:
        # POSITIVE CONTROL for both legs, which assert absences. Hand each
        # predicate a string it must reject, so a broken scan is not mistaken for
        # a clean tree.
        live_claim = "any long high-entropy token is scrubbed to REDACTED"
        assert any(phrase.lower() in live_claim.lower() for phrase in self.CORPSE_PROSE)
        assert not any(marker in live_claim.lower() for marker in self.DELETION_MARKERS)
        historical = "the high-entropy token sweep was deleted by packet 42"
        assert any(marker in historical.lower() for marker in self.DELETION_MARKERS)


class TestTheScrubbedSurfacesAreUnchanged:
    """A19: only ``_scrub_text``'s BODY shrinks — its call sites are untouched.

    The inventory's per-field provenance note for ``_scrub_text`` is that the
    output is the input with three transforms applied and becomes the input with
    two; every byte not matched by a labelled pattern is COPIED THROUGH. These
    pins hold the SURFACES constant while that body changes, so a reshape that
    quietly stops scrubbing one of them is visible.
    """

    def test_the_filter_still_scrubs_message_args_extra_exception_and_stack(self) -> None:
        # ∀ surface, in ONE record, each with its own labelled credential so a
        # surface that stopped being scrubbed is named rather than hidden behind
        # a single boolean.
        record = make_record(
            msg=f"store.connect.failed password={SURREAL_ROOT_PASSWORD}",
            extra={"detail": f"api_key={VOYAGE_STYLE_KEY}"},
        )
        try:
            raise RuntimeError(f"signin refused token={ANTHROPIC_STYLE_KEY}")
        except RuntimeError:
            record.exc_info = sys.exc_info()
        record.stack_info = f"Stack (most recent call last):\n  secret={HARDCODED_LABELLED_LITERAL}"
        assert RedactingFilter().filter(record) is True  # never drops a record
        rendered = JsonFormatter().format(record)
        for surface, value in (
            ("msg", SURREAL_ROOT_PASSWORD),
            ("extra", VOYAGE_STYLE_KEY),
            ("exc_info", ANTHROPIC_STYLE_KEY),
            ("stack_info", HARDCODED_LABELLED_LITERAL),
        ):
            assert value not in rendered, f"the {surface} surface is no longer scrubbed"

    def test_both_formatters_still_scrub_without_the_filter(self) -> None:
        # BELT-AND-BRACES LEG (#211 mutation proof M1, 2026-07-25): through
        # ``configure_logging`` the FILTER scrubs first, so every end-to-end pin
        # passes whether or not the formatters scrub at all. Both are public and
        # usable without the filter, so that path is pinned directly.
        def _record_with_a_secret_bearing_exception() -> logging.LogRecord:
            try:
                raise RuntimeError(f"signin refused for password={SURREAL_ROOT_PASSWORD}")
            except RuntimeError:
                return logging.LogRecord(
                    name="loremaster.demo",
                    level=logging.ERROR,
                    pathname=__file__,
                    lineno=1,
                    msg="store.connect.failed",
                    args=(),
                    exc_info=sys.exc_info(),
                )

        parsed = json.loads(JsonFormatter().format(_record_with_a_secret_bearing_exception()))
        assert "Traceback" in parsed[EXC_FIELD], "the fixture carried no traceback"
        assert SURREAL_ROOT_PASSWORD not in parsed[EXC_FIELD]
        line = KeyValueFormatter().format(_record_with_a_secret_bearing_exception())
        assert "Traceback" in line, "the fixture carried no traceback"
        assert SURREAL_ROOT_PASSWORD not in line

    def test_scrubbed_exception_text_still_prefers_a_foreign_handlers_cached_text(self) -> None:
        # A19 third consumer, on the shape it exists for: another handler already
        # rendered ``exc_text`` with no scrubber, and this seam repairs it.
        record = make_record(msg="store.connect.failed")
        record.exc_text = f'  File "/srv/app.py", line 3\nRuntimeError: password={SURREAL_ROOT_PASSWORD}'
        text = scrubbed_exception_text(record)
        assert text is not None
        assert SURREAL_ROOT_PASSWORD not in text
        assert "/srv/app.py" in text, "repairing exc_text must not destroy the frame it names"

    def test_a_record_with_neither_exception_nor_stack_yields_none(self) -> None:
        assert scrubbed_exception_text(make_record(msg="index.file.done")) is None


class TestNoProductionObjectRetainsAnUnwrappedCredential:
    """**RULING R10 (MP1 🔴) — the source fix, and the frame correction behind it.**

    The adversary broke this contract with a build that scored **204 passed / 0
    failed** and leaked a production credential through **six paths**. Root cause,
    accepted verbatim: **A18's frame was too narrow.** The bound was written as *"an
    UNLABELLED secret in free log text"*, so every carrier here was built around
    unlabelled text — while the credential that actually exists as a bare ``str``
    in this codebase is **labelled** (``x-api-key``), sitting in a **header map**,
    at the very site the ``UNWRAP_ALLOWLIST`` blesses.

    Neither defence could reach it. ``_ASSIGNMENT_RE`` needs the label
    *immediately* followed by a separator regex; in a mapping repr there is a QUOTE
    between them, and in ``_scrub_value`` keys and values are scrubbed
    independently so the label never adjoins the value at all. And the
    ``SecretStr`` control cannot apply, because at that site the value is a bare
    ``str`` **by design** — the allowlist entry is precisely the licence to make
    one.

    **The operator declined the redactor fix and ruled the SOURCE fix (R10):**
    ``calibration/counting.py::__init__`` and ``scripts/token_survey.py::__init__``
    stop retaining the unwrapped header dict on the instance, baking it into the
    ``httpx`` client exactly as ``loresigil/tei.py`` already does. *"Then the bare
    ``str`` credential object does not exist and there is nothing for a repr to
    leak."* Widening the pattern was declined because it treats the symptom and
    returns us to matching arbitrary text — the practice this packet exists to end.

    ⚠ **The comment directly above that code already named the hazard** — *"A bare
    ``str`` here would render verbatim in any repr of ``self._headers``"* — and
    shipped it anyway. It was true the whole time; only the entropy catch-all was
    hiding it, and this packet deletes the catch-all. Prose that names a hazard is
    not a guard.
    """

    @staticmethod
    def _rendered_state(instance: object) -> str:
        """Everything a traceback frame or a debug log could render off an object."""
        return f"{instance!r} {instance!s} {vars(instance)!r}"

    def test_the_async_counter_does_not_retain_the_raw_key(self) -> None:
        from loremaster.calibration.counting import AsyncClaudeTokenCounter

        counter = AsyncClaudeTokenCounter(api_key=SecretStr(ANTHROPIC_STYLE_KEY))
        assert ANTHROPIC_STYLE_KEY not in self._rendered_state(counter), (
            "the counter still holds the unwrapped credential in its own state. R10: bake it "
            "into the httpx client at construction; do not retain the header dict."
        )

    def test_the_sync_survey_counter_does_not_retain_the_raw_key(self) -> None:
        # The twin in ``scripts/``, which mypy never sees (``scripts/`` is not a
        # typecheck member) and which the loremaster package scan below cannot
        # reach. Forced explicitly for exactly that reason.
        token_survey = _scripts_module("token_survey")
        counter = token_survey.ClaudeTokenCounter(api_key=SecretStr(ANTHROPIC_STYLE_KEY))
        assert ANTHROPIC_STYLE_KEY not in self._rendered_state(counter)

    def test_the_leak_detector_can_see_a_retained_key(self) -> None:
        # POSITIVE CONTROL. Both pins above assert an ABSENCE, which passes just as
        # happily when the rendering oracle is broken. A deliberately-wrong owner
        # of the SAME shape must be caught by the SAME oracle.
        class RetainingCounter:
            def __init__(self, *, api_key: SecretStr) -> None:
                self._headers = {"x-api-key": api_key.get_secret_value()}

        leaky = RetainingCounter(api_key=SecretStr(ANTHROPIC_STYLE_KEY))
        assert ANTHROPIC_STYLE_KEY in self._rendered_state(leaky)

    @pytest.mark.parametrize("fmt", FORMATS)
    def test_the_counters_state_does_not_leak_through_the_production_log_path(
        self, fmt: str
    ) -> None:
        # THE ADVERSARY'S ACTUAL PROBE, kept as a pin: the real production object,
        # through the real production sink, in both formats. It measured 6/6 paths
        # leaking on a 204/204 build.
        from loremaster.calibration.counting import AsyncClaudeTokenCounter

        counter = AsyncClaudeTokenCounter(api_key=SecretStr(ANTHROPIC_STYLE_KEY))

        def action(logger: logging.Logger) -> None:
            try:
                raise RuntimeError(f"count_tokens failed for {vars(counter)!r}")
            except RuntimeError:
                logger.exception("calibration.count.failed", extra={"state": vars(counter)})

        output = emit_through_configured_logger(fmt, action, child=f"mp1.{fmt}")
        assert output.strip(), "nothing was emitted — this pin is vacuous"
        assert ANTHROPIC_STYLE_KEY not in output

    @staticmethod
    def _mock_transport(seen: list[str | None]) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers.get("x-api-key"))
            return httpx.Response(200, json={"input_tokens": 7})

        return httpx.MockTransport(handler)

    async def test_the_OWNED_client_arm_is_authenticated(self) -> None:
        # 🔴 **RULING R19 / MP5 — THE #107 SHAPE, and the pin that closes it.**
        #
        # The wrong build applies R10's fix to the INJECTED arm only and leaves the
        # OWNED ``httpx.AsyncClient`` completely unauthenticated. It produced a
        # **byte-identical failure set to the correct build** — the adversary's
        # ``diff`` was empty — because the previous version of this class only ever
        # INJECTED a client.
        #
        # ⚠ **Every production construction uses the OWNED arm**:
        # ``calibration/engine.py::_default_counter_factory`` and
        # ``scripts/calibration_baseline.py`` both call
        # ``AsyncClaudeTokenCounter(api_key, model=…)`` with no client. So the arm
        # the contract tested was the arm production never uses. Green everywhere,
        # 100% broken in production — #107 exactly.
        from loremaster.calibration import counting

        seen: list[str | None] = []
        real_client_cls = httpx.AsyncClient

        def _patched(*args: object, **kwargs: object) -> httpx.AsyncClient:
            kwargs["transport"] = self._mock_transport(seen)
            return real_client_cls(*args, **kwargs)  # type: ignore[arg-type]

        with pytest.MonkeyPatch.context() as patcher:
            patcher.setattr(httpx, "AsyncClient", _patched)
            counter = counting.AsyncClaudeTokenCounter(api_key=SecretStr(ANTHROPIC_STYLE_KEY))
            await counter.count("The quarterly safety report summarizes incident rates.")
        assert seen == [ANTHROPIC_STYLE_KEY], (
            "the OWNED client arm did not authenticate. This is the arm every production "
            f"caller uses; observed x-api-key: {seen}"
        )

    async def test_the_INJECTED_client_arm_is_authenticated(self) -> None:
        # The other arm, forced separately — ∀ arm, never one standing in for both.
        from loremaster.calibration.counting import AsyncClaudeTokenCounter

        seen: list[str | None] = []
        injected = httpx.AsyncClient(transport=self._mock_transport(seen))
        counter = AsyncClaudeTokenCounter(api_key=SecretStr(ANTHROPIC_STYLE_KEY), client=injected)
        await counter.count("The quarterly safety report summarizes incident rates.")
        assert seen == [ANTHROPIC_STYLE_KEY], f"the INJECTED client arm did not authenticate: {seen}"

    def test_no_credential_is_baked_into_either_CLIENT(self) -> None:
        # **R19's STRUCTURAL MANDATE — SHAPE B, per-request headers.** The ruling is
        # explicit that this is settled structurally rather than by pin: *"build no
        # auth headers at construction at all; attach them per request. One code
        # path, so there is no owned-vs-injected arm to fix-one-and-forget."* The
        # adversary measured shape B **immune** to the W-R10a wrong build.
        #
        # This is the pin that makes the mandate checkable: the credential must not
        # live on EITHER client's header map. The two wire pins above then prove it
        # still arrives — mandate and function, pinned separately, so satisfying one
        # by breaking the other is impossible.
        from loremaster.calibration import counting

        owned_holder: list[httpx.AsyncClient] = []
        real_client_cls = httpx.AsyncClient

        def _patched(*args: object, **kwargs: object) -> httpx.AsyncClient:
            client = real_client_cls(*args, **kwargs)  # type: ignore[arg-type]
            owned_holder.append(client)
            return client

        with pytest.MonkeyPatch.context() as patcher:
            patcher.setattr(httpx, "AsyncClient", _patched)
            counting.AsyncClaudeTokenCounter(api_key=SecretStr(ANTHROPIC_STYLE_KEY))
        assert owned_holder, "no owned client was constructed — this pin is vacuous"
        assert ANTHROPIC_STYLE_KEY not in repr(dict(owned_holder[0].headers)), (
            "the credential is baked into the OWNED client's headers. R19 mandates shape B: "
            "no auth headers at construction, attached per request instead."
        )

    def test_an_injected_client_is_not_mutated(self) -> None:
        # Shape B's other observable consequence, and a correctness property in its
        # own right: the caller OWNS the injected client, and a counter that
        # rewrites its headers has reached into somebody else's object. Under shape
        # A this pin fails; under shape B it passes — which is why the ruling chose
        # B rather than leaving the fork open.
        from loremaster.calibration.counting import AsyncClaudeTokenCounter

        injected = httpx.AsyncClient(transport=httpx.MockTransport(lambda _r: httpx.Response(200)))
        before = dict(injected.headers)
        AsyncClaudeTokenCounter(api_key=SecretStr(ANTHROPIC_STYLE_KEY), client=injected)
        assert dict(injected.headers) == before, (
            "the counter mutated a client it does not own. R19 mandates per-request headers."
        )

    def test_the_x_api_key_HEADER_LINE_form_is_covered_by_a_kept_pattern(self) -> None:
        # **RULING R20, part 2.** ``x-api-key`` is the header our production
        # credential actually travels in. ``_ASSIGNMENT_RE``'s ``\bapi[_-]?key\b``
        # fires INSIDE ``x-api-key`` because ``-`` is a non-word character, so the
        # header-LINE form is covered by a pattern packet 42 KEEPS. That is
        # **incidental today** — nothing states it — and *"it happens to match"* is
        # not a guarantee. Pinned so a future narrowing of the label alternation
        # goes RED instead of silently un-covering the one header that matters.
        scrubbed = _scrub_text(f"x-api-key: {ANTHROPIC_STYLE_KEY}")
        assert ANTHROPIC_STYLE_KEY not in scrubbed
        assert scrubbed == f"x-api-key: {REDACTED}"

    # ---------------------------------------------------------------- #
    # RETIRED — ``test_the_STRUCTURED_x_api_key_form_remains_a_KNOWN_BOUND``
    # ---------------------------------------------------------------- #
    # It pinned three shapes as LEAKING: ``Headers({'x-api-key': …})``, a plain
    # dict repr, and a JSON body. **Rulings R38/R39 closed all three**, and the
    # production fix is landed — measured 2026-07-27, all three now redact.
    #
    # So the BOUND DISSOLVED, and per CLAUDE.md a pin outlives its hole only as a
    # lie (A16's lesson, the second time this packet has applied it). The pin is
    # DELETED WITH THIS NOTE rather than left green or weakened.
    #
    # ⚠ What was accepted with it is also gone: the old rationale said the
    # structured form was tolerable because *"no lore code path produces it"*.
    # R40 measured that false — httpx retains the unwrapped ``x-api-key`` on every
    # Request and ``Headers.__repr__`` renders it — which is precisely why the
    # bound had to close rather than be re-argued. The surviving coverage is
    # pinned positively by ``test_the_x_api_key_HEADER_LINE_form_is_covered_by_a_kept_pattern``
    # above and by the container pins in ``TestScrubValueRecursesIntoContainers``.


def _auth_holder_classes() -> list[tuple[str, type]]:
    """Every class in the workspace whose ``__init__`` accepts an ``api_key``.

    **RULING R27.1 — the module list is now GENUINELY DERIVED.** The previous
    version's docstring claimed *"DERIVED from the live tree, never a hand-list"*
    while being a hand-list of six. That is the served-English class this repo
    keeps paying for, in the docstring of an instrument whose whole job is to stop
    hand-lists. It now walks the installed packages with ``pkgutil`` and the
    non-package ``scripts/`` directory by filename, so a module added next year is
    swept without anyone remembering to add it.
    """
    import importlib
    import pkgutil

    found: list[tuple[str, type]] = []
    seen: set[type] = set()
    # ⚠ REWIRED to the ONE shared root list — this hand-listed two packages and
    # missed ``lorerunes`` and ``lorescribe``, so an auth holder landing in either
    # would never be swept. The sweep's whole point is that a sibling nobody
    # thought of is covered; a hand-list of packages re-created the defect one
    # level up.
    modules: list[str] = []
    for label, _root in workspace_roots(include_scripts=False, include_skills=False):
        try:
            package = importlib.import_module(label)
        except Exception:  # pragma: no cover - a member with no importable package
            continue
        modules += [
            info.name
            for info in pkgutil.walk_packages(package.__path__, prefix=f"{package.__name__}.")
        ]
    package_file = loremaster.__file__
    assert package_file is not None
    scripts_root = Path(package_file).resolve().parent.parent.parent / "scripts"
    if scripts_root.is_dir():
        if str(scripts_root) not in sys.path:
            sys.path.insert(0, str(scripts_root))
        modules += [
            path.stem
            for path in sorted(scripts_root.glob("*.py"))
            if not path.name.startswith("test_")
        ]
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
        except Exception:  # pragma: no cover - an unimportable optional module
            continue
        for _name, candidate in vars(module).items():
            if not inspect.isclass(candidate) or candidate.__module__ != module.__name__:
                continue
            if candidate in seen:
                continue
            try:
                parameters = inspect.signature(candidate).parameters
            except (TypeError, ValueError):  # pragma: no cover - C types
                continue
            if "api_key" in parameters:
                seen.add(candidate)
                found.append((f"{module_name}.{candidate.__name__}", candidate))
    return sorted(found)


class TestEveryAuthHolderSiblingIsSwept:
    """**RULING R22 — the GENERALISATION, which matters more than the pin it came from.**

    This packet has now been bitten **three times by one shape**: the
    ``load_api_key`` twins, the owned-vs-injected client arms, and the async/sync
    counter twins. Each time a pin covered one member of a pair and the adversary
    walked through the other. *A pin over one member of a twin pair is half a pin.*

    So the answer is not a fourth bespoke pin — it is a **∀ sweep derived from the
    tree**, which covers the sibling nobody has thought of yet.

    **THE SWEEP FOUND TWO SIBLINGS BEYOND THE SYNC TWIN** (measured 2026-07-27 at
    ``c05fde4``), neither previously pinned by anything:

    * ``loremaster.calibration.engine.CalibrationEngine`` — takes ``api_key`` and
      retains it as ``self._api_key``, then hands it to
      ``AsyncClaudeTokenCounter``. Safe **by type** today (it keeps the
      ``SecretStr``), and nothing was checking that.
    * ``token_survey.MultiModelClaudeCounter`` — builds **N** sync counters over
      **one shared** ``httpx.Client``. Under shape A that is a third arm with N
      writers to one header map; under R19's shape B it is inert. Nothing pinned it.

    A third hit was inspected and **scoped out with a reason**:
    ``merge_mcp_json._desired_entry`` emits a literal ``Bearer ${VAR}`` **template**
    into a config file for Claude Code to expand — it never holds a credential.
    """

    def test_the_sweep_finds_the_population(self) -> None:
        # POSITIVE CONTROL. A derived scan that silently found nothing would make
        # the ∀ pin below pass vacuously — the exact shape this class exists to end.
        holders = _auth_holder_classes()
        assert len(holders) >= 6, f"the auth-holder sweep found only {len(holders)}: {holders}"

    def test_the_known_siblings_are_all_present(self) -> None:
        # The sweep must SEE the two it found and the twins it was built for. If a
        # rename or a move drops one out of ``modules``, the ∀ pin stays green
        # while governing less — so the roster is asserted, not assumed.
        names = {name for name, _ in _auth_holder_classes()}
        for required in (
            "loremaster.calibration.counting.AsyncClaudeTokenCounter",
            "loremaster.calibration.engine.CalibrationEngine",
            "token_survey.ClaudeTokenCounter",
            "token_survey.MultiModelClaudeCounter",
            "loresigil.tei.TEIEmbedder",
        ):
            assert required in names, f"the sibling sweep no longer reaches {required}"

    def test_no_auth_holder_exposes_the_raw_credential(self) -> None:
        # ∀ SIBLING, and **RULING R27.2: every rostered holder must actually be
        # CONSTRUCTED**, not merely counted. The previous version skipped
        # ``CalibrationEngine`` (it needs three more required kwargs) and the
        # ``constructed >= 4`` floor was still cleared by the other six — so the
        # skip was INVISIBLE. A count that passes while a member is silently
        # dropped is precisely the vacuity this instrument exists to prevent.
        from pathlib import Path as _Path

        class _NullFindingsPort:
            """Minimal stand-in so ``CalibrationEngine`` is constructible here."""

            async def report(self, *args: object, **kwargs: object) -> None:  # pragma: no cover
                return None

        supply: dict[str, object] = {
            "api_key": SecretStr(ANTHROPIC_STYLE_KEY),
            # ⚠ R32 defect 5: ``loresigil.factory.EmbeddingConfig`` is now correctly
            # rostered as an auth holder, and it needs a ``backend``. Without this
            # the sweep raised ``ValidationError`` — which ``except TypeError``
            # does not catch — so the test ERRORED before R27.2's totality check
            # could report anything. Supplying the field is the right repair;
            # catching ``ValidationError`` would route a CONSTRUCTIBLE holder into
            # ``skipped`` and redden R27.2 for the wrong reason, and defaulting
            # ``backend`` in production is a silent-fallback hazard in a dispatch
            # field that nobody ruled.
            "backend": "tei",
            "base_url": "http://embedder.test:8080",
            "models": ("claude-sonnet-5",),
            "model": "claude-sonnet-5",
            "committed_constant": 1.0,
            "state_dir": _Path("/tmp/pkt42-sweep"),
            "findings_port": _NullFindingsPort(),
        }
        leakers: list[str] = []
        constructed: list[str] = []
        skipped: list[str] = []
        for name, holder in _auth_holder_classes():
            parameters = inspect.signature(holder).parameters
            kwargs = {key: value for key, value in supply.items() if key in parameters}
            try:
                instance = holder(**kwargs)
            except TypeError as error:
                skipped.append(f"{name}: {error}")
                continue
            constructed.append(name)
            if ANTHROPIC_STYLE_KEY in f"{instance!r} {instance!s} {vars(instance)!r}":
                leakers.append(name)
        # R27.2 — the floor is REPLACED by a totality check. Every holder the sweep
        # rosters is interrogated, or the sweep says which one it could not build
        # and why. No silent skips behind a satisfied count.
        assert not skipped, (
            "these auth holders were ROSTERED but never CONSTRUCTED, so the ∀ pin below never "
            "interrogated them. Add what they need to ``supply``:\n  " + "\n  ".join(skipped)
        )
        assert constructed, "the sweep constructed nothing — vacuous"
        assert not leakers, f"these auth holders expose the raw credential: {leakers}"


class TestTheSyncCounterTwinIsAuthenticatedToo:
    """**RULING R22 (MP10 🔴) — every wire pin gets a sync leg.**

    ``W-SYNCWIRE`` — the sync ``ClaudeTokenCounter`` posting with **no auth header
    at all** — scored **ZERO failures** against this contract, because both wire
    pins targeted the async class only. Measured `[None]` on the wire against
    `['sk-ant-…']` on a correct build.

    R19's shape-B mandate and its owned-arm wire pin extend to this class
    **verbatim**, so these are deliberate mirrors of the async legs rather than a
    reduced set: owned arm, injected arm, no client-level credential, injected
    client unmutated.
    """

    @staticmethod
    def _sync_transport(seen: list[str | None]) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers.get("x-api-key"))
            return httpx.Response(200, json={"input_tokens": 7})

        return httpx.MockTransport(handler)

    def test_the_OWNED_client_arm_is_authenticated(self) -> None:
        # The blocker leg. ``MultiModelClaudeCounter`` and every bare
        # ``ClaudeTokenCounter(api_key, model=…)` call reach production through
        # this arm.
        token_survey = _scripts_module("token_survey")
        seen: list[str | None] = []
        real_client_cls = httpx.Client

        def _patched(*args: object, **kwargs: object) -> httpx.Client:
            kwargs["transport"] = self._sync_transport(seen)
            return real_client_cls(*args, **kwargs)  # type: ignore[arg-type]

        with pytest.MonkeyPatch.context() as patcher:
            patcher.setattr(httpx, "Client", _patched)
            counter = token_survey.ClaudeTokenCounter(api_key=SecretStr(ANTHROPIC_STYLE_KEY))
            counter.count("The quarterly safety report summarizes incident rates.")
        assert seen == [ANTHROPIC_STYLE_KEY], (
            f"the SYNC counter's OWNED client arm did not authenticate: {seen}"
        )

    def test_the_INJECTED_client_arm_is_authenticated(self) -> None:
        token_survey = _scripts_module("token_survey")
        seen: list[str | None] = []
        injected = httpx.Client(transport=self._sync_transport(seen))
        counter = token_survey.ClaudeTokenCounter(
            api_key=SecretStr(ANTHROPIC_STYLE_KEY), client=injected
        )
        counter.count("The quarterly safety report summarizes incident rates.")
        assert seen == [ANTHROPIC_STYLE_KEY], (
            f"the SYNC counter's INJECTED client arm did not authenticate: {seen}"
        )

    def test_no_credential_is_baked_into_the_owned_CLIENT(self) -> None:
        # R19 shape B, sync leg.
        token_survey = _scripts_module("token_survey")
        owned: list[httpx.Client] = []
        real_client_cls = httpx.Client

        def _patched(*args: object, **kwargs: object) -> httpx.Client:
            client = real_client_cls(*args, **kwargs)  # type: ignore[arg-type]
            owned.append(client)
            return client

        with pytest.MonkeyPatch.context() as patcher:
            patcher.setattr(httpx, "Client", _patched)
            token_survey.ClaudeTokenCounter(api_key=SecretStr(ANTHROPIC_STYLE_KEY))
        assert owned, "no owned client was constructed — this pin is vacuous"
        assert ANTHROPIC_STYLE_KEY not in repr(dict(owned[0].headers))

    def test_an_injected_client_is_not_mutated(self) -> None:
        token_survey = _scripts_module("token_survey")
        injected = httpx.Client(transport=httpx.MockTransport(lambda _r: httpx.Response(200)))
        before = dict(injected.headers)
        token_survey.ClaudeTokenCounter(api_key=SecretStr(ANTHROPIC_STYLE_KEY), client=injected)
        assert dict(injected.headers) == before, (
            "the sync counter mutated a client it does not own (R19 shape B)"
        )

    def test_the_multi_model_counter_authenticates_every_model(self) -> None:
        # The sibling the sweep found: N counters over ONE shared client. Under
        # shape A this is N writers to one header map; under shape B it is inert.
        # Forced with TWO models, because one model cannot distinguish "each
        # counter authenticates" from "the last one to write wins".
        token_survey = _scripts_module("token_survey")
        seen: list[str | None] = []
        real_client_cls = httpx.Client

        def _patched(*args: object, **kwargs: object) -> httpx.Client:
            kwargs["transport"] = self._sync_transport(seen)
            return real_client_cls(*args, **kwargs)  # type: ignore[arg-type]

        with pytest.MonkeyPatch.context() as patcher:
            patcher.setattr(httpx, "Client", _patched)
            multi = token_survey.MultiModelClaudeCounter(
                SecretStr(ANTHROPIC_STYLE_KEY), ("claude-sonnet-5", "claude-opus-4")
            )
            for model in multi.models:
                multi.count("warehouse incident rates", model)
        assert len(seen) == 2, f"expected one request per model, saw {seen}"
        assert all(header == ANTHROPIC_STYLE_KEY for header in seen), (
            f"a per-model counter did not authenticate: {seen}"
        )


class TestScrubValueRecursesIntoContainers:
    """**RULING R11 (MP2) — RESTORED, and its absence is the finding.**

    ⚠ **THIS CLASS WAS MUTATION-PROVEN IN CONTRACT REVISION 3 AND NEVER REACHED A
    COMMIT.** It caught the adversary's ``W-COSMETIC`` build — ``_scrub_value``
    replaced by ``return value``, which had scored **204 passed / 0 failed** — and
    took it to 8 failed. It is absent from `9ab5888`, the first commit of this
    contract, and from every commit since. Most likely a slice-based edit in a
    later revision swallowed it; whatever the cause, **R11's blocker has been
    unprotected ever since, and no gate could tell, because a test that does not
    exist does not fail.**

    Found by the fixture-reach interrogation, not by a grep for regressions —
    which is its own lesson: I went looking for cases my fixtures could not
    construct and found a whole class that no longer existed.

    **Why the existing carriers cannot substitute** (the adversary's analysis,
    which is what makes this class necessary rather than nice): the
    ``extra-nested`` carrier runs two legs, and **both are non-discriminating
    here**. Its ``SecretStr`` leg is masked by the TYPE whatever ``_scrub_value``
    does; its bare-``str`` leg is an ACCEPTED BOUND asserted to leak, so breaking
    the recursion makes that assertion *more* true. The discriminating leg is a
    **LABELLED bare ``str``** — not masked by a type, not an accepted bound.
    """

    LABELLED = f"Authorization: Bearer {VOYAGE_STYLE_KEY}"

    @pytest.mark.parametrize(
        "container", ["dict", "list", "tuple", "dict-in-list", "list-in-dict"]
    )
    def test_every_container_shape_recurses(self, container: str) -> None:
        # ∀ container kind, forced individually — a build that kept the dict arm
        # and dropped the list arm passes a dict-only pin.
        payload: object = {
            "dict": {"h": self.LABELLED},
            "list": [self.LABELLED],
            "tuple": (self.LABELLED,),
            "dict-in-list": [{"h": self.LABELLED}],
            "list-in-dict": {"hs": [self.LABELLED]},
        }[container]
        assert VOYAGE_STYLE_KEY not in repr(_scrub_value(payload)), (
            "_scrub_value stopped recursing into containers. A19 is 'preserved — call sites "
            "unchanged'; the recursion IS the call site."
        )

    def test_a_tuple_stays_a_tuple(self) -> None:
        # The recursion must preserve the container TYPE, or a downstream consumer
        # that indexes or serialises it changes shape.
        assert isinstance(_scrub_value(("a", self.LABELLED)), tuple)

    @pytest.mark.parametrize("fmt", FORMATS)
    def test_it_holds_end_to_end_through_the_production_sink(self, fmt: str) -> None:
        output = emit_through_configured_logger(
            fmt,
            lambda logger: logger.error(
                "store.connect.failed", extra={"attempts": [{"hdr": self.LABELLED}]}
            ),
            child=f"mp2.{fmt}",
        )
        assert output.strip(), "nothing was emitted — this pin is vacuous"
        assert VOYAGE_STYLE_KEY not in output
        assert REDACTED in output, "the value was dropped rather than scrubbed"

    @pytest.mark.parametrize(
        "label", ["api_key", "password", "token", "secret", "authorization"]
    )
    def test_a_labelled_credential_AS_A_DICT_VALUE_is_scrubbed(self, label: str) -> None:
        # ⚠ **RULING R38 — THE SHARPEST FIXTURE GAP IN THIS PACKET.** This class's
        # prose claims it catches *"a labelled bearer token out of an ``extra=``
        # map"*. It could not: the 7 ``TEXT_CARRIERS`` are unlabelled BY
        # CONSTRUCTION, and every labelled pin drove a FLAT STRING — so no fixture
        # anywhere put a labelled credential inside a CONTAINER. The class proved
        # ROUTING (that recursion happens), never REDACTION of the shape it names.
        #
        # ``{'api_key': '<v>'}`` leaked while 388 tests passed. The discriminating
        # fixture is the label as the KEY and the credential as the VALUE, because
        # ``_scrub_value`` scrubs keys and values INDEPENDENTLY — so the label never
        # adjoins the value and ``_ASSIGNMENT_RE`` structurally cannot fire.
        scrubbed = _scrub_value({label: VOYAGE_STYLE_KEY})
        assert VOYAGE_STYLE_KEY not in repr(scrubbed), (
            f"a credential under the key {label!r} survived. The KEY is the label; scrubbing "
            f"the value in isolation can never see it: {scrubbed!r}"
        )

    def test_a_credential_used_as_a_dict_KEY_is_scrubbed(self) -> None:
        # ⚠ **THE TWELFTH, found by the fixture-reach interrogation rather than by
        # an audit.** ``_scrub_value``'s dict arm is
        # ``{key: _scrub_value(inner) for key, inner in value.items()}`` — it
        # recurses into VALUES and passes every KEY through untouched. No pin in
        # this packet could construct that shape: every container fixture put the
        # credential in the value position.
        #
        # A real shape, not an invented one: a reverse lookup ``{token: identity}``
        # or per-token telemetry ``{token: count}`` renders the credential as a key
        # in any ``extra=`` map or repr.
        scrubbed = _scrub_value({f"api_key={VOYAGE_STYLE_KEY}": 3})
        assert VOYAGE_STYLE_KEY not in repr(scrubbed), (
            "a credential in the KEY position survived — _scrub_value recurses into values "
            f"and copies keys through: {scrubbed!r}"
        )

    def test_a_labelled_credential_in_a_MULTI_LINE_render_is_scrubbed(self) -> None:
        # The other reach gap the interrogation surfaced: every labelled fixture in
        # this packet is a SINGLE LINE. A pretty-printed JSON body — what an httpx
        # error actually carries — separates label from value with a QUOTE and
        # spreads the object over several lines. Neither half was ever rendered.
        body = f'{{\n  "model": "voyage-4",\n  "api_key": "{VOYAGE_STYLE_KEY}"\n}}'
        assert VOYAGE_STYLE_KEY not in _scrub_text(body), (
            f"a credential in a pretty-printed JSON body survived: {_scrub_text(body)!r}"
        )
