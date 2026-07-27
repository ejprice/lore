"""Contract tests for ``loremaster.logging_setup`` — structured logging.

The structured-logging layer turns the project's stdlib ``logging`` records into
Mezmo-friendly structured output and guarantees a secret never reaches a log
sink. These tests pin that boundary:

* :class:`JsonFormatter` emits ONE JSON object per record carrying ``ts`` (ISO-8601
  UTC), ``level``, ``logger``, ``msg`` (the static event string), plus every key
  the caller passed via ``extra={...}`` — flattened to the top level so Mezmo can
  index each field — plus :data:`EXC_FIELD` when the caller passed an exception.
* :class:`KeyValueFormatter` emits a human ``ts level logger event k=v`` line,
  with any traceback appended below it.
* :class:`RedactingFilter` is the LABELLED-PATTERN backstop: a bearer token or
  an ``api_key``-style assignment is scrubbed to :data:`REDACTED` in the message,
  the ``extra`` values, AND the rendered exception/stack — proven by a known fake
  secret that must appear in NO emitted record.

  ⚠ PACKET 42 (2026-07-26) DELETED the bare high-entropy catch-all that used to
  sit behind those two patterns, and with it #227's path exemption, the
  bare-hex/SHA bound and the UUID bound. An UNLABELLED credential in free log
  text is no longer redacted — a deliberate, operator-ruled trade whose
  replacement control is the ``SecretStr`` TYPE. Every pin that certified the
  deleted mechanism was removed rather than left green; the surviving property
  pins and the accepted bounds both live in ``test_secret_leak_vectors.py``,
  which is where anything about the entropy sweep belongs now.
* Exception rendering is its own class below
  (:class:`TestExceptionRenderingIsEmittedAndScrubbed`, finding #211): the
  traceback must be EMITTED (it was silently dropped) and SCRUBBED (it was never
  seen by the filter), across every shape an exception arrives in — message,
  ``from``-cause, implicit context chain, ``__notes__``, the quoted source line,
  ``stack_info``, and a raw ``exc_text`` cached by a foreign handler.
* :func:`configure_logging` scopes handlers to the lore namespace with
  ``propagate=False`` (it must NOT reconfigure root — that fights uvicorn),
  silences ``httpx`` to WARNING, honours the level + format,
  lets ``LORE_LOG_LEVEL`` override the config default, and is IDEMPOTENT (a second
  call does not stack a second handler / double-emit).

The independent oracle for the JSON shape is the stdlib :mod:`json` parser; the
oracle for the timestamp is :func:`datetime.fromisoformat` — never the
formatter's own serialisation logic. The namespace list and the REDACTED
sentinel are imported from the module under test, never re-hardcoded here.
"""

from __future__ import annotations

import io
import json
import logging
import sys
import traceback
from collections.abc import Callable, Iterator
from datetime import datetime

import pytest
from loremaster.logging_setup import (
    EXC_FIELD,
    LORE_NAMESPACES,
    REDACTED,
    JsonFormatter,
    KeyValueFormatter,
    RedactingFilter,
    configure_logging,
)

# A known fake bearer token + api key the secret-scrubbing test embeds in a log
# call and then asserts appears in NO emitted record.
#
# ⚠ Both are only ever asserted BEHIND A LABEL (``Bearer …`` / ``api_key=…``).
# Before packet 42 several pins here carried them BARE and passed on the entropy
# catch-all; those pins certified a mechanism that no longer exists and were
# deleted, not weakened.
FAKE_BEARER_TOKEN = "sk-deadbeefcafef00d1234567890abcdef0123456789abcdef"
FAKE_API_KEY = "AbCdEf0123456789AbCdEf0123456789AbCdEf01"

# The third-party loggers configure_logging must pin to WARNING (their per-request
# INFO chatter would otherwise flood the structured stream).
SILENCED_THIRD_PARTY = ("httpx",)

# A credential written as a LITERAL in source. A traceback quotes each frame's
# source LINE, so this value reaches the log through a path that has nothing to do
# with the exception's message — the shape a message-only scrubber cannot see.
LITERAL_IN_SOURCE = "Zt7QnP4xW9kLm2Rb8VyH3sJd6FgA1cUe0oIT"

# The same idea for the ``stack_info`` surface, which renders the CALLING line.
# It is interpolated behind a ``token=`` key so the LABELLED pattern is what
# redacts it (see ``_log_with_stack_info_from_a_literal_credential``).
LITERAL_IN_SOURCE_LABEL_VALUE = "Kp9RmT2vX6bN4wQ8yH1jL5dF7gA3sZ0cUeIo"


def _refuse(**_credentials: str) -> None:
    """Raise, so the CALLER's line — which carries the literal — is rendered."""
    raise RuntimeError("connection refused")


def _leak_from_a_literal_credential() -> None:
    """Raise such that the rendered frame QUOTES a hardcoded credential.

    ⚠ The shape here is load-bearing and was wrong until cold-audit R3. It used to
    put the literal on an ``if`` guard above the ``raise`` — but Python's traceback
    quotes the line that RAISED, not the lines above it, so the credential never
    reached the rendered text and the pin below passed on every build, including
    one that never scrubbed source lines at all.

    The credential is therefore on the CALL line, which is exactly what this frame
    renders — and which is also the realistic shape: a hardcoded token passed at a
    call site.
    """
    _refuse(token="Zt7QnP4xW9kLm2Rb8VyH3sJd6FgA1cUe0oIT")


def _log_with_stack_info_from_a_literal_credential(logger: logging.Logger) -> None:
    """Emit with ``stack_info=True`` from a line that itself carries a credential.

    Same correction as above: ``stack_info`` renders the CALLING line, so the
    literal must be ON the logging call, not on a guard above it.

    ⚠ RE-AUTHORED BY PACKET 42. The literal used to sit BARE in a trailing
    ``# noqa`` comment, so the only thing scrubbing it was the deleted entropy
    catch-all — this pin certified a corpse and would have gone red on the
    deletion. It now rides behind a ``token=`` LABEL, which is both the realistic
    shape (a hardcoded credential passed at a call site) and the property that
    actually survives. The BARE case is pinned as an accepted bound in
    ``test_secret_leak_vectors.py``.
    """
    _emit_with_stack(logger, token="Kp9RmT2vX6bN4wQ8yH1jL5dF7gA3sZ0cUeIo")


def _emit_with_stack(logger: logging.Logger, **_credentials: str) -> None:
    """Emit with ``stack_info=True`` so the CALLER's labelled line is rendered."""
    logger.error("store.connect.failed", stack_info=True)


def _make_record(
    *, name: str = "loremaster.demo", level: int = logging.INFO, msg: str = "event.demo",
    extra: dict[str, object] | None = None,
) -> logging.LogRecord:
    """Build a real :class:`logging.LogRecord` with ``extra`` keys attached.

    Mirrors what ``logger.info(msg, extra={...})`` produces: each extra key is set
    as an attribute on the record (which is exactly how the stdlib threads
    ``extra`` through), so the formatter sees the same shape it would in
    production.
    """
    record = logging.LogRecord(
        name=name, level=level, pathname=__file__, lineno=1,
        msg=msg, args=(), exc_info=None,
    )
    for key, value in (extra or {}).items():
        setattr(record, key, value)
    return record


@pytest.fixture(autouse=True)
def _restore_lore_loggers() -> Iterator[None]:
    """Snapshot + restore the lore-namespace + third-party loggers around each test.

    ``configure_logging`` mutates global logging state (handlers, levels,
    ``propagate``) on the ``loremaster``/``loresigil``/``lorescribe`` namespace
    loggers and on ``httpx``. Without a restore, a configure in
    one test leaks its handler into the next (cross-contamination of shared
    global state — the exact state-leakage the lifecycle rule forbids). This
    fixture records each affected logger's handlers/level/propagate before the
    test and restores them after, so every test starts from the same baseline.
    """
    names = (*LORE_NAMESPACES, *SILENCED_THIRD_PARTY)
    saved: dict[str, tuple[list[logging.Handler], int, bool]] = {}
    for name in names:
        logger = logging.getLogger(name)
        saved[name] = (list(logger.handlers), logger.level, logger.propagate)
    try:
        yield
    finally:
        for name, (handlers, level, propagate) in saved.items():
            logger = logging.getLogger(name)
            logger.handlers = list(handlers)
            logger.setLevel(level)
            logger.propagate = propagate


class TestJsonFormatter:
    """One JSON object per record: ts/level/logger/msg + flattened extra."""

    def test_emits_parseable_json_with_core_fields(self) -> None:
        record = _make_record(level=logging.WARNING, msg="watcher.in_q_overflow")
        line = JsonFormatter().format(record)
        # Independent oracle: the stdlib JSON parser, not the formatter's logic.
        parsed = json.loads(line)
        assert parsed["level"] == "WARNING"
        assert parsed["logger"] == "loremaster.demo"
        assert parsed["msg"] == "watcher.in_q_overflow"

    def test_ts_is_iso8601_utc(self) -> None:
        line = JsonFormatter().format(_make_record())
        parsed = json.loads(line)
        # Independent oracle: fromisoformat parses it AND it must be UTC-aware.
        when = datetime.fromisoformat(parsed["ts"])
        assert when.utcoffset() is not None
        assert when.utcoffset().total_seconds() == 0  # type: ignore[union-attr]

    def test_extra_fields_are_flattened_to_top_level(self) -> None:
        record = _make_record(
            msg="index.file.done",
            extra={"tier": "custom", "file_path": "src/a.py", "n_chunks": 7, "duration_ms": 12},
        )
        parsed = json.loads(JsonFormatter().format(record))
        # Each extra key must be indexable at the JSON top level (Mezmo fields).
        assert parsed["tier"] == "custom"
        assert parsed["file_path"] == "src/a.py"
        assert parsed["n_chunks"] == 7
        assert parsed["duration_ms"] == 12

    def test_does_not_leak_stdlib_logrecord_internals(self) -> None:
        # The JSON must be a clean structured event, not a dump of every LogRecord
        # attribute (args/levelno/pathname/… would bloat Mezmo and confuse fields).
        parsed = json.loads(JsonFormatter().format(_make_record()))
        for noise in ("args", "levelno", "msecs", "relativeCreated", "pathname"):
            assert noise not in parsed


class TestKeyValueFormatter:
    """Human-readable ``ts level logger event k=v`` line."""

    def test_contains_level_logger_event_and_kv_pairs(self) -> None:
        record = _make_record(
            level=logging.INFO, msg="reconcile.summary",
            extra={"files_indexed": 3, "files_purged": 1},
        )
        line = KeyValueFormatter().format(record)
        assert "INFO" in line
        assert "loremaster.demo" in line
        assert "reconcile.summary" in line
        # The extra fields appear as k=v tokens (independent substring oracle).
        assert "files_indexed=3" in line
        assert "files_purged=1" in line


class TestRedactingFilter:
    """The secret backstop: bearer / api_key / high-entropy tokens are scrubbed."""

    def test_redacts_bearer_in_message(self) -> None:
        record = _make_record(msg=f"Authorization: Bearer {FAKE_BEARER_TOKEN}")
        assert RedactingFilter().filter(record) is True  # never drops the record
        rendered = record.getMessage()
        assert FAKE_BEARER_TOKEN not in rendered
        assert REDACTED in rendered

    def test_redacts_api_key_assignment_in_extra_value(self) -> None:
        record = _make_record(
            msg="embed.probe.ok",
            extra={"detail": f"api_key={FAKE_API_KEY}"},
        )
        RedactingFilter().filter(record)
        assert FAKE_API_KEY not in str(record.detail)  # type: ignore[attr-defined]
        assert REDACTED in str(record.detail)  # type: ignore[attr-defined]

    # DELETED BY PACKET 42 — ``test_redacts_long_high_entropy_token_in_extra``.
    # It asserted that a BARE, unlabelled token in an ``extra`` value is scrubbed,
    # which was true only of the deleted entropy catch-all (inventory A2/A18).
    # The behaviour is now the packet's accepted, operator-ruled trade, and it is
    # pinned AS A BOUND — with a "if you closed this deliberately, say so"
    # message and a re-open trigger — by
    # ``test_secret_leak_vectors.TestTheDeletionsResidualBoundsArePinned``.
    # Leaving it here would have been a green test certifying a corpse.

    def test_does_not_redact_ordinary_short_values(self) -> None:
        # False-positive guard: normal short structured fields survive untouched.
        record = _make_record(msg="index.file.done", extra={"tier": "custom", "n_chunks": 5})
        RedactingFilter().filter(record)
        assert record.tier == "custom"  # type: ignore[attr-defined]
        assert record.n_chunks == 5  # type: ignore[attr-defined]

    def test_does_not_redact_realistic_paths_and_identifiers(self) -> None:
        # Critical false-positive guard: the events log file paths, dotted module
        # names, version stamps, and event strings. These are NOT secrets and must
        # survive the entropy backstop verbatim — a redacted ``file_path`` would
        # gut the observability the catalog exists to provide. (The original
        # entropy heuristic wrongly nuked these because ``/`` and ``.`` inflated a
        # path's apparent entropy; the fix splits on those separators.)
        survivors = [
            "src/loremaster/index/watcher.py",
            "loremaster.loremaster.index.indexer",
            "a/very/deeply/nested/module/path/to/something.py",
            "embed.over_length.subsplit",
            "15.0.20260420",
            "voyageai/voyage-4-nano",
        ]
        for value in survivors:
            record = _make_record(msg="index.file.done", extra={"field": value})
            RedactingFilter().filter(record)
            assert record.field == value, f"{value!r} must not be redacted"  # type: ignore[attr-defined]

    def test_still_redacts_a_labelled_secret_even_alongside_paths(self) -> None:
        # RE-AUTHORED BY PACKET 42. The original carried the token BARE, so it
        # tested the deleted catch-all; the surviving property is that a LABELLED
        # credential is redacted in the same record whose path fields survive
        # untouched. A build that deleted the catch-all AND broke the labelled
        # patterns passes nothing here.
        record = _make_record(
            msg="event", extra={"path": "src/a.py", "detail": f"api_key={FAKE_BEARER_TOKEN}"}
        )
        RedactingFilter().filter(record)
        assert record.path == "src/a.py"  # type: ignore[attr-defined]
        assert FAKE_BEARER_TOKEN not in str(record.detail)  # type: ignore[attr-defined]
        assert REDACTED in str(record.detail)  # type: ignore[attr-defined]


class TestExceptionRenderingIsEmittedAndScrubbed:
    """Finding #211 Half B: the traceback is a log surface too — and it leaked.

    Two defects, one seam, and they must be fixed together or not at all:

    1. **The redactor never saw the exception.** ``RedactingFilter`` scrubbed
       ``msg``/``args``/``extra`` and nothing else; ``exc_info`` and ``exc_text``
       were untouched. A traceback is rendered by the FORMATTER from
       ``exc_info``, so a credential in an exception's own message — the single
       most likely place one surfaces — reached any stdlib formatter verbatim.
    2. **lore's own formatters DISCARDED the exception entirely.**
       :class:`JsonFormatter` and :class:`KeyValueFormatter` override
       ``format()`` without calling ``super()``, and read neither ``exc_info``
       nor ``exc_text``. Measured 2026-07-25 at ``c32800d``: ``logger.exception``
       emitted ``{"ts": …, "level": "ERROR", "logger": …, "msg": "…"}`` and
       nothing else — the type, the message, the cause chain, the notes and the
       traceback all silently dropped, at eight production ``exc_info=True``
       call sites (``indexer.py``, ``reconcile.py``, ``calibration/engine.py``,
       ``watcher.py``).

    Defect 2 is why fixing defect 1 alone would have been theatre: a scrubber
    over a surface nothing renders is a green gate over a dead mechanism. So
    these tests pin BOTH — the traceback is emitted, AND it is scrubbed — across
    the shapes an exception actually arrives in. A single-shape fixture is the
    documented way this class stays green.
    """

    @staticmethod
    def _emit(fmt: str, action: Callable[[logging.Logger], None]) -> str:
        """Run ``action`` against a real configured lore logger; return the stream."""
        buffer = io.StringIO()
        configure_logging(level="DEBUG", fmt=fmt)
        namespace_logger = logging.getLogger("loremaster")
        handler = namespace_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        handler.setStream(buffer)
        action(logging.getLogger("loremaster.exc"))
        return buffer.getvalue()

    def test_the_traceback_is_emitted_at_all(self) -> None:
        # The observability half. Without this the scrubbing half is untestable
        # in production: there is nothing to scrub because nothing is rendered.
        def action(logger: logging.Logger) -> None:
            try:
                raise RuntimeError("store.signin refused")
            except RuntimeError:
                logger.exception("store.connect.failed")

        output = self._emit("json", action)
        parsed = json.loads(output)
        assert EXC_FIELD in parsed, "logger.exception emitted no exception field at all"
        assert "RuntimeError" in parsed[EXC_FIELD]
        assert "store.signin refused" in parsed[EXC_FIELD]
        assert "Traceback" in parsed[EXC_FIELD]

    def test_secret_in_the_exception_message_is_scrubbed(self) -> None:
        def action(logger: logging.Logger) -> None:
            try:
                raise RuntimeError(f"signin refused for password={FAKE_BEARER_TOKEN}")
            except RuntimeError:
                logger.exception("store.connect.failed")

        for fmt in ("json", "keyvalue"):
            output = self._emit(fmt, action)
            assert FAKE_BEARER_TOKEN not in output, f"{fmt}: secret survived in the traceback"
            assert REDACTED in output, f"{fmt}: nothing was scrubbed — the pin proved nothing"

    def test_secret_in_a_chained_cause_is_scrubbed(self) -> None:
        # ``raise X from Y`` renders BOTH exceptions. A scrubber that only saw the
        # outermost one would pass every single-exception fixture.
        def action(logger: logging.Logger) -> None:
            try:
                try:
                    raise ValueError(f"Authorization: Bearer {FAKE_BEARER_TOKEN}")
                except ValueError as cause:
                    raise RuntimeError("embed.probe.failed") from cause
            except RuntimeError:
                logger.exception("embed.probe.failed")

        output = self._emit("json", action)
        assert "direct cause" in output, "the fixture did not actually chain"
        assert FAKE_BEARER_TOKEN not in output
        assert REDACTED in output

    def test_secret_in_an_implicit_context_chain_is_scrubbed(self) -> None:
        # The ``During handling of the above exception…`` leg — a DIFFERENT
        # traceback section from the ``from``-cause leg above.
        def action(logger: logging.Logger) -> None:
            try:
                try:
                    raise ValueError(f"api_key={FAKE_API_KEY}")
                except ValueError:
                    raise RuntimeError("secondary failure")  # noqa: B904
            except RuntimeError:
                logger.exception("store.connect.failed")

        output = self._emit("json", action)
        assert "During handling" in output, "the fixture did not produce a context chain"
        assert FAKE_API_KEY not in output
        assert REDACTED in output

    def test_secret_in_an_exception_note_is_scrubbed(self) -> None:
        # ``add_note`` text is rendered by the traceback machinery and is a place
        # a helpful error handler will happily paste a request header.
        def action(logger: logging.Logger) -> None:
            try:
                error = RuntimeError("upstream rejected the request")
                error.add_note(f"sent header Authorization: Bearer {FAKE_BEARER_TOKEN}")
                raise error
            except RuntimeError:
                logger.exception("embed.request.failed")

        output = self._emit("json", action)
        assert "sent header" in output, "the fixture's note did not reach the render"
        assert FAKE_BEARER_TOKEN not in output
        assert REDACTED in output

    def test_the_literal_actually_reaches_an_unscrubbed_render(self) -> None:
        """POSITIVE CONTROL for the two pins below (cold-audit R3).

        Both of them assert a credential is ABSENT from the output — which passes
        just as happily when the credential never arrived. It never did: the
        original fixture put the literal on an ``if`` guard, and Python quotes the
        RAISING line, so ``LITERAL_IN_SOURCE not in output`` was true on every
        build including one that scrubbed nothing. This control proves the fixture
        delivers the credential to the rendered text in the first place, so the
        absence asserted below means something.
        """
        try:
            _leak_from_a_literal_credential()
        except RuntimeError:
            rendered = traceback.format_exc()
        assert LITERAL_IN_SOURCE in rendered, (
            "the fixture no longer puts the credential on the rendered frame line — "
            "the two pins below are now vacuous (this is exactly how R3 happened)"
        )

    def test_secret_in_the_rendered_source_line_is_scrubbed(self) -> None:
        # A traceback quotes the SOURCE LINE of each frame. A hardcoded credential
        # at the raising CALL SITE therefore reaches the log even when the
        # exception's own message is clean — a shape no message-only scrubber
        # covers. Meaningful only because of the control above.
        def action(logger: logging.Logger) -> None:
            try:
                _leak_from_a_literal_credential()
            except RuntimeError:
                logger.exception("store.connect.failed")

        output = self._emit("json", action)
        assert LITERAL_IN_SOURCE not in output, "the credential in the source line survived"
        # Asserted at the POSITION the literal occupied, not merely "somewhere in
        # the output" — the old form was satisfied by the redactor eating an
        # unrelated function name (R2) at a 0.023-bit entropy margin. Read from the
        # PARSED field, since the raw line is JSON-escaped.
        rendered = json.loads(output)[EXC_FIELD]
        # ``token=`` is a LABELLED assignment, so ``_ASSIGNMENT_RE`` fires before the
        # entropy sweep and consumes the closing quote/paren with the value — hence
        # the open-ended form. Still positional: REDACTED must sit immediately where
        # the credential was.
        assert f"_refuse(token={REDACTED}" in rendered, (
            "REDACTED must appear where the credential was, not incidentally "
            f"elsewhere. Rendered:\n{rendered}"
        )

    def test_exc_info_true_on_a_plain_error_call_is_scrubbed(self) -> None:
        # The shape eight production call sites actually use — NOT
        # ``logger.exception``.
        def action(logger: logging.Logger) -> None:
            try:
                raise RuntimeError(f"signin refused for password={FAKE_BEARER_TOKEN}")
            except RuntimeError:
                logger.error("index.file.failed", exc_info=True)

        output = self._emit("json", action)
        assert FAKE_BEARER_TOKEN not in output
        assert REDACTED in output

    def test_exc_info_given_an_exception_object_is_scrubbed(self) -> None:
        # ``exc_info=exc`` (calibration/engine.py's shape) — a third spelling the
        # stdlib normalises differently from ``True``.
        def action(logger: logging.Logger) -> None:
            error = RuntimeError(f"api_key={FAKE_API_KEY}")
            logger.warning("calibration.probe.unreachable", exc_info=error)

        output = self._emit("json", action)
        assert FAKE_API_KEY not in output
        assert REDACTED in output

    def test_stack_info_is_scrubbed(self) -> None:
        # ``stack_info=True`` renders the CALLER's stack — another source-line
        # surface, cached on its own record attribute.
        def action(logger: logging.Logger) -> None:
            _log_with_stack_info_from_a_literal_credential(logger)

        parsed = json.loads(self._emit("json", action))
        # POSITIVE CONTROL: before #211 this assertion passed VACUOUSLY, because
        # the formatters emitted no stack at all — "the secret is absent" and
        # "everything is absent" are the same string. Prove the stack is there
        # before believing it is clean.
        assert "Stack (most recent call last)" in parsed[EXC_FIELD]
        # SECOND CONTROL, added by packet 42 after its reference build caught the
        # re-authored fixture delivering NOTHING: the credential must be ON a
        # rendered line. A multi-line call renders only its first line, so the
        # literal has to sit on the CALLER's single line — the same R3 lesson,
        # relearned the same way. Prove the render carries the labelled site.
        assert "_emit_with_stack(logger, token=" in parsed[EXC_FIELD], (
            "the fixture no longer puts the labelled credential on a rendered stack line — "
            "this pin is vacuous (cold-audit R3, repeated)"
        )
        assert LITERAL_IN_SOURCE_LABEL_VALUE not in parsed[EXC_FIELD]
        assert REDACTED in parsed[EXC_FIELD]

    def test_exc_info_true_with_no_live_exception_emits_nothing(self) -> None:
        # ``exc_info=True`` outside an ``except`` block hands the record the
        # TRUTHY-but-empty ``(None, None, None)`` triple. The stdlib renders that
        # as the useless line ``NoneType: None``; lore emits no field at all.
        def action(logger: logging.Logger) -> None:
            logger.error("index.file.failed", exc_info=True)

        parsed = json.loads(self._emit("json", action))
        assert EXC_FIELD not in parsed
        assert "NoneType" not in json.dumps(parsed)

    def test_a_foreign_handler_that_already_cached_raw_exc_text_is_repaired(self) -> None:
        # Cross-handler hazard, measured: ``Logger.callHandlers`` hands the SAME
        # record to every handler, and a plain handler formatting first CACHES the
        # RAW traceback into ``record.exc_text`` for everyone downstream. Our
        # filter must scrub what it finds there, not assume it rendered it.
        record = logging.LogRecord(
            name="loremaster.demo", level=logging.ERROR, pathname=__file__, lineno=1,
            msg="store.connect.failed", args=(), exc_info=None,
        )
        record.exc_text = (
            f"Traceback (most recent call last):\n"
            f"RuntimeError: signin refused for password={FAKE_BEARER_TOKEN}"
        )
        assert RedactingFilter().filter(record) is True
        assert record.exc_text is not None
        assert FAKE_BEARER_TOKEN not in record.exc_text
        assert REDACTED in record.exc_text

    def test_the_filter_protects_a_plain_stdlib_formatter(self) -> None:
        """THE FINDING'S OWN SCENARIO — the filter as last line of defence.

        ``RedactingFilter`` is a ``logging.Filter``: it can be attached to ANY
        handler, and its docstring sells it as the last line of defence. That
        promise is only true if a handler using the ordinary
        :class:`logging.Formatter` also emits scrubbed traceback text — which
        works because the filter pre-populates ``record.exc_text``, the attribute
        ``Formatter.format`` consults BEFORE re-rendering from ``exc_info``.

        Measured against the unfixed tree (2026-07-25, before ``47ee6ed``) this
        emitted, in full: ``RuntimeError: signin refused for
        password=sk-deadbeefcafef00d…``. Pinned separately from the lore-formatter
        tests because those cannot see this leg — mutation proof M2, same date,
        showed the filter's render leg could be DELETED with every other test in
        this file still green.
        """
        buffer = io.StringIO()
        handler = logging.StreamHandler(buffer)
        handler.setFormatter(logging.Formatter("%(message)s"))
        handler.addFilter(RedactingFilter())
        logger = logging.getLogger("loremaster.plainfmt")
        logger.handlers = [handler]
        logger.propagate = False
        logger.setLevel(logging.INFO)
        try:
            raise RuntimeError(f"signin refused for password={FAKE_BEARER_TOKEN}")
        except RuntimeError:
            logger.exception("store.connect.failed")
        output = buffer.getvalue()
        assert "Traceback" in output, "the stdlib formatter rendered no traceback"
        assert FAKE_BEARER_TOKEN not in output
        assert REDACTED in output

    def test_ordinary_traceback_text_is_not_mangled(self) -> None:
        # FALSE-POSITIVE GUARD: a traceback is mostly file paths, dotted module
        # names and identifiers. Redacting those would gut the observability this
        # whole change exists to restore — a scrubber that nukes the traceback is
        # not better than one that drops it.
        def action(logger: logging.Logger) -> None:
            try:
                raise RuntimeError("no secret here at all")
            except RuntimeError:
                logger.exception("store.connect.failed")

        parsed = json.loads(self._emit("json", action))
        assert REDACTED not in parsed[EXC_FIELD], "a clean traceback must not be redacted"
        assert "test_logging_setup.py" in parsed[EXC_FIELD]
        assert "RuntimeError: no secret here at all" in parsed[EXC_FIELD]

    @staticmethod
    def _record_with_a_secret_bearing_exception() -> logging.LogRecord:
        """A record carrying live ``exc_info``, with NO filter having touched it."""
        try:
            raise RuntimeError(f"signin refused for password={FAKE_BEARER_TOKEN}")
        except RuntimeError:
            record = logging.LogRecord(
                name="loremaster.demo", level=logging.ERROR, pathname=__file__,
                lineno=1, msg="store.connect.failed", args=(), exc_info=sys.exc_info(),
            )
        return record

    def test_the_json_formatter_scrubs_on_its_own_without_the_filter(self) -> None:
        # BELT-AND-BRACES LEG, and it needs its own pin: through
        # ``configure_logging`` the FILTER scrubs first, so every test above passes
        # whether or not the formatter scrubs at all. (Found by mutation proof M1,
        # 2026-07-25: deleting the formatter's scrub left all eight declared-RED
        # tests GREEN — the mutation had landed in code no test reached.) Both
        # formatters are public and usable WITHOUT the filter, so that path is
        # pinned here directly.
        parsed = json.loads(
            JsonFormatter().format(self._record_with_a_secret_bearing_exception())
        )
        assert "Traceback" in parsed[EXC_FIELD], "the fixture carried no traceback"
        assert FAKE_BEARER_TOKEN not in parsed[EXC_FIELD]
        assert REDACTED in parsed[EXC_FIELD]

    def test_the_keyvalue_formatter_scrubs_on_its_own_without_the_filter(self) -> None:
        line = KeyValueFormatter().format(self._record_with_a_secret_bearing_exception())
        assert "Traceback" in line, "the fixture carried no traceback"
        assert FAKE_BEARER_TOKEN not in line
        assert REDACTED in line

    def test_the_wire_field_name_is_exactly_exc_info(self) -> None:
        """Pin the SERVED NAME as a literal — every other test uses the constant.

        Because all the assertions above index ``parsed[EXC_FIELD]``, they follow
        the constant wherever it points: renaming its VALUE would change the
        served surface with the whole suite still green. lore's log consumers are
        agents and Mezmo queries that key on the literal string, so the literal is
        what needs pinning. ``exc_info`` is the lead's ruling (2026-07-25) and
        python-json-logger's convention.
        """
        assert EXC_FIELD == "exc_info"

        def action(logger: logging.Logger) -> None:
            try:
                raise RuntimeError("store.signin refused")
            except RuntimeError:
                logger.exception("store.connect.failed")

        parsed = json.loads(self._emit("json", action))
        # Asserted against the literal, NOT the constant — the whole point.
        assert "exc_info" in parsed
        assert "Traceback" in parsed["exc_info"]
        # And the old spelling must be gone, so a stale consumer fails loudly
        # rather than silently reading nothing.
        assert "exc" not in parsed

    def test_a_record_with_no_exception_is_untouched(self) -> None:
        parsed = json.loads(self._emit("json", lambda logger: logger.info("index.file.done")))
        assert EXC_FIELD not in parsed


class TestOrdinaryPathsSurviveRedaction:
    """Cold-audit DEFECT D / #227: the redactor mangled FILE PATHS in tracebacks.

    A path COMPONENT that is a UUID, a git SHA, a container overlay id or a nix
    store hash was one unbroken high-entropy run, so the entropy backstop redacted
    it — turning ``/tmp/ci/<uuid>/app.py`` into ``/tmp/ci/***REDACTED***/app.py``.
    #211 Half B had just made tracebacks visible for the first time; this made
    them unreadable in exactly the environments that need them most (CI runners,
    containers, ephemeral checkouts).

    ⚠ PACKET 42 DELETED THE CAUSE, so this property now holds because nothing
    examines the run at all rather than because a four-condition exemption
    (inventory A4-A9) tames a sweep. **The class stays as a REGRESSION pin.** The
    property is what mattered; the mechanism never was, and the next engineer who
    reaches for a shape-based detector reddens here first.

    ⚠ **EVERY PATH HERE IS CONSTRUCTED, NEVER TAKEN FROM THE RUNNING CHECKOUT.**
    The original defect was invisible because this repo happens to live at a path
    with no high-entropy component. A pin that rendered the real ``__file__``
    would pass here and fail on a CI runner — CLAUDE.md's "THE TEST ENVIRONMENT
    IS A FICTION" exactly: the fixture would guarantee the one condition under
    which the bug is invisible. These fixtures are hostile by construction and
    identical on every machine.

    The provenance note that matters for anyone reading this later: the defect
    PRE-DATES the #211 wave — ``_TOKEN_RE`` was byte-identical at ``d0ee2be``,
    and the false positive reproduced there through ``extra=``. Half B did not
    create it; it routed the path-dense traceback surface through it.
    """

    # (label, absolute path) — the four shapes measured to trip the deleted backstop.
    HOSTILE_PATHS = [
        ("uuid workspace", "/tmp/ci/090685cb-2064-498d-8479-e141e4fd4ea5/loremaster/store/surreal.py"),
        (
            "container overlay",
            "/var/lib/containers/storage/overlay/"
            "3f786850e387550fdab836ed7e6dc881de23001b2b4a3f7a4a5b6c7d8e9f0a1b/merged/app.py",
        ),
        ("nix store", "/nix/store/1a2b3c4d5e6f7g8h9i0jklmnopqrstuv-python3-3.14.6/lib/x.py"),
        ("hashed checkout", "/build/9f8e7d6c5b4a39281706f5e4d3c2b1a09f8e7d6c/src/indexer.py"),
    ]

    @staticmethod
    def _traceback_text(path: str, message: str) -> str:
        """A realistic rendered traceback naming ``path`` — built, not captured."""
        return (
            "Traceback (most recent call last):\n"
            f'  File "{path}", line 42, in _ensure_connection\n'
            "    await connection.signin(credentials)\n"
            f"RuntimeError: {message}"
        )

    @pytest.mark.parametrize("label,path", HOSTILE_PATHS, ids=[p[0] for p in HOSTILE_PATHS])
    def test_a_hostile_path_survives_verbatim_through_the_filter(
        self, label: str, path: str
    ) -> None:
        record = _make_record(msg="store.connect.failed")
        record.exc_text = self._traceback_text(path, "connection refused")
        RedactingFilter().filter(record)
        assert record.exc_text is not None
        assert path in record.exc_text, (
            f"the {label} path was mangled by the redactor — a traceback that "
            f"cannot name its own file is the observability this fix restored:\n"
            f"  {record.exc_text}"
        )
        assert REDACTED not in record.exc_text

    @pytest.mark.parametrize("label,path", HOSTILE_PATHS, ids=[p[0] for p in HOSTILE_PATHS])
    def test_a_secret_is_still_redacted_in_that_same_traceback(
        self, label: str, path: str
    ) -> None:
        # THE DISCRIMINATOR. Fixing a false positive by weakening the backstop
        # would pass the test above and silently undo the finding this module
        # exists for. The path must survive AND the secret must not, in one line.
        record = _make_record(msg="store.connect.failed")
        record.exc_text = self._traceback_text(
            path, f"signin refused for password={FAKE_BEARER_TOKEN}"
        )
        RedactingFilter().filter(record)
        assert record.exc_text is not None
        assert path in record.exc_text, f"{label}: path mangled"
        assert FAKE_BEARER_TOKEN not in record.exc_text, f"{label}: SECRET LEAKED"
        assert REDACTED in record.exc_text

    # DELETED BY PACKET 42 — ``test_the_exemption_is_contextual_not_a_blanket_stand_down``.
    # It took ONE token and asserted it survived inside a path and was REDACTED
    # outside one, to prove the #227 exemption was contextual rather than a
    # blanket stand-down. Both halves of that discriminator died with the
    # mechanism (inventory A4-A9): there is no exemption to be contextual, and
    # the bare token outside a path is now the packet's accepted trade. Pinning
    # either half would re-certify a deleted heuristic.

    def test_it_survives_end_to_end_through_a_configured_logger(self) -> None:
        # The pins above drive the filter directly; this proves the property holds
        # through the real handler + JsonFormatter that production actually uses.
        path = self.HOSTILE_PATHS[0][1]
        buffer = io.StringIO()
        configure_logging(level="DEBUG", fmt="json")
        handler = logging.getLogger("loremaster").handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        handler.setStream(buffer)
        logger = logging.getLogger("loremaster.pathcase")
        try:
            raise RuntimeError(f"signin refused for password={FAKE_BEARER_TOKEN}")
        except RuntimeError:
            record = logger.makeRecord(
                logger.name, logging.ERROR, path, 42, "store.connect.failed", (), None
            )
            record.exc_text = self._traceback_text(path, f"password={FAKE_BEARER_TOKEN}")
            logger.handle(record)
        parsed = json.loads(buffer.getvalue())
        assert path in parsed[EXC_FIELD]
        assert FAKE_BEARER_TOKEN not in parsed[EXC_FIELD]


# ---------------------------------------------------------------------------
# DELETED BY PACKET 42 — two whole classes, with the reason each one dies.
# ---------------------------------------------------------------------------
# ``TestThePathExemptionNeverWeakensTheBackstop`` (cold-audit R1). Its corpus was
# ten base64 credentials embedded as ``"api key is <secret>"`` — note the SPACE:
# ``_ASSIGNMENT_RE`` needs ``label<sep>value`` with ``=`` or ``:``, so it never
# fired, and every one of those ten was redacted PURELY by the entropy catch-all.
# The class existed to prove #227's path exemption had not widened far enough to
# admit an encoded credential. Inventory A4-A9: the exemption is deleted, so
# there is nothing left to widen; inventory A18: those ten values are now the
# accepted trade. Keeping the class would have made it the loudest corpse in the
# suite — ten parametrized pins asserting a mechanism that no longer exists.
#
# ``TestBareHexRunsStayRedactedKnownBound`` (inventory A16). It pinned a git SHA
# in prose and a ``unique_database()`` name as ACCEPTED FALSE POSITIVES, with the
# ruling that *"a redacted SHA costs provenance; an un-redacted 40-hex API key
# costs a credential"*. That asymmetry was an argument about the catch-all, and
# the catch-all is gone: the bound DISSOLVED rather than being closed. Per
# CLAUDE.md — *"a pin outlives its hole only as a lie"* — the class is deleted,
# and the same two values are re-pinned INVERTED, as diagnostic data that must
# now SURVIVE, in ``test_secret_leak_vectors.TestScrubbingNoLongerDestroys
# DiagnosticData``. That is the recovered data the packet's Exit clause asks to
# be reported as a receipt.
#
# ``test_the_four_false_positive_classes_are_still_preserved`` was the one pin in
# either class worth keeping; it is not lost — the identical property is pinned
# parametrically by ``TestOrdinaryPathsSurviveRedaction`` above and by
# ``test_a_hashy_absolute_path_survives_verbatim`` in the new module.


class TestConfigureLogging:
    """``configure_logging`` scopes to the lore namespace, idempotent, level-aware."""

    def test_scopes_to_lore_namespaces_without_touching_root(self) -> None:
        root_handlers_before = list(logging.getLogger().handlers)
        configure_logging(level="INFO", fmt="json")
        # Root is untouched (must not fight uvicorn's own root handler).
        assert logging.getLogger().handlers == root_handlers_before
        for name in LORE_NAMESPACES:
            logger = logging.getLogger(name)
            assert logger.handlers, f"{name} should own a handler"
            assert logger.propagate is False, f"{name} must not propagate to root"

    def test_silences_third_party_loggers_to_warning(self) -> None:
        configure_logging(level="DEBUG", fmt="json")
        for name in SILENCED_THIRD_PARTY:
            assert logging.getLogger(name).level == logging.WARNING

    def test_level_is_honoured(self) -> None:
        configure_logging(level="WARNING", fmt="json")
        logger = logging.getLogger("loremaster")
        # An INFO record is below the WARNING threshold → not enabled.
        assert logger.isEnabledFor(logging.WARNING)
        assert not logger.isEnabledFor(logging.INFO)

    def test_lore_log_level_env_overrides_config(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # The run-time override: LORE_LOG_LEVEL beats the config default. The
        # READER of that env is the entry path; here we prove configure_logging
        # honours whatever level string it is handed (DEBUG), distinct from the
        # config default (INFO) — the entry path resolves env-then-config.
        import os

        monkeypatch.setenv("LORE_LOG_LEVEL", "DEBUG")
        configure_logging(level=os.environ.get("LORE_LOG_LEVEL", "INFO"), fmt="json")
        assert logging.getLogger("loremaster").isEnabledFor(logging.DEBUG)

    def test_idempotent_reconfigure_does_not_stack_handlers(self) -> None:
        configure_logging(level="INFO", fmt="json")
        first_count = len(logging.getLogger("loremaster").handlers)
        configure_logging(level="INFO", fmt="json")
        second_count = len(logging.getLogger("loremaster").handlers)
        assert second_count == first_count == 1

    def test_idempotent_reconfigure_does_not_double_emit(self) -> None:
        # The lifecycle/state-leakage proof: after two configures, a single log
        # call must produce exactly ONE line (not two from two stacked handlers).
        buffer = io.StringIO()
        configure_logging(level="INFO", fmt="json")
        configure_logging(level="INFO", fmt="json")
        logger = logging.getLogger("loremaster.idem")
        # Point the single namespace handler at our buffer to capture emission.
        namespace_logger = logging.getLogger("loremaster")
        assert len(namespace_logger.handlers) == 1
        handler = namespace_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        handler.setStream(buffer)
        logger.info("event.once", extra={"k": "v"})
        emitted = [ln for ln in buffer.getvalue().splitlines() if ln.strip()]
        assert len(emitted) == 1

    def test_secret_in_a_log_call_never_reaches_any_record(self) -> None:
        # CRITICAL: a known fake bearer passed INTO a log call must be scrubbed by
        # the RedactingFilter before it reaches the handler's stream — it appears
        # in NO emitted output. This is the secret-never-logged backstop.
        buffer = io.StringIO()
        configure_logging(level="INFO", fmt="json")
        namespace_logger = logging.getLogger("loremaster")
        handler = namespace_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        handler.setStream(buffer)
        # RE-AUTHORED BY PACKET 42: the second value used to be BARE
        # (``"key": FAKE_API_KEY``) and was scrubbed only by the deleted entropy
        # catch-all. Both values now ride behind a label, which is what the
        # backstop still covers. The unlabelled case is an accepted bound pinned
        # in ``test_secret_leak_vectors.py``, not a silent gap.
        logging.getLogger("loremaster.secret").info(
            "embed.probe.ok",
            extra={
                "header": f"Authorization: Bearer {FAKE_BEARER_TOKEN}",
                "detail": f"api_key={FAKE_API_KEY}",
            },
        )
        output = buffer.getvalue()
        assert FAKE_BEARER_TOKEN not in output
        assert FAKE_API_KEY not in output
        assert REDACTED in output  # proof the scrubbing actually fired
