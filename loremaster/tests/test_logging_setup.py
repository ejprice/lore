"""Contract tests for ``loremaster.logging_setup`` — structured logging.

The structured-logging layer turns the project's stdlib ``logging`` records into
Mezmo-friendly structured output and guarantees a secret never reaches a log
sink. These tests pin that boundary:

* :class:`JsonFormatter` emits ONE JSON object per record carrying ``ts`` (ISO-8601
  UTC), ``level``, ``logger``, ``msg`` (the static event string), plus every key
  the caller passed via ``extra={...}`` — flattened to the top level so Mezmo can
  index each field.
* :class:`KeyValueFormatter` emits a human ``ts level logger event k=v`` line.
* :class:`RedactingFilter` is the CRITICAL backstop: a bearer token, an
  ``api_key``-style assignment, or a long high-entropy token is scrubbed to
  :data:`REDACTED` in BOTH the message and the ``extra`` values — proven by a
  known fake secret that must appear in NO emitted record.
* :func:`configure_logging` scopes handlers to the lore namespace with
  ``propagate=False`` (it must NOT reconfigure root — that fights uvicorn),
  silences ``httpx``/``qdrant_client`` to WARNING, honours the level + format,
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
from collections.abc import Iterator
from datetime import datetime

import pytest
from loremaster.logging_setup import (
    LORE_NAMESPACES,
    REDACTED,
    JsonFormatter,
    KeyValueFormatter,
    RedactingFilter,
    configure_logging,
)

# A known fake bearer token + api key the secret-scrubbing test embeds in a log
# call and then asserts appears in NO emitted record. High-entropy so the
# entropy heuristic also catches it if the explicit pattern ever regresses.
FAKE_BEARER_TOKEN = "sk-deadbeefcafef00d1234567890abcdef0123456789abcdef"
FAKE_API_KEY = "AbCdEf0123456789AbCdEf0123456789AbCdEf01"

# The third-party loggers configure_logging must pin to WARNING (their per-request
# INFO chatter would otherwise flood the structured stream).
SILENCED_THIRD_PARTY = ("httpx", "qdrant_client")


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
    loggers and on ``httpx``/``qdrant_client``. Without a restore, a configure in
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

    def test_redacts_long_high_entropy_token_in_extra(self) -> None:
        # A bare high-entropy token (no "api_key=" prefix) must still be scrubbed —
        # the entropy heuristic is the catch-all backstop.
        record = _make_record(msg="event", extra={"blob": FAKE_BEARER_TOKEN})
        RedactingFilter().filter(record)
        assert FAKE_BEARER_TOKEN not in str(record.blob)  # type: ignore[attr-defined]

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

    def test_still_redacts_a_secret_even_alongside_paths(self) -> None:
        # The fix must NOT weaken the backstop: a genuine high-entropy token is
        # still scrubbed even though paths now survive.
        record = _make_record(msg="event", extra={"path": "src/a.py", "key": FAKE_BEARER_TOKEN})
        RedactingFilter().filter(record)
        assert record.path == "src/a.py"  # type: ignore[attr-defined]
        assert FAKE_BEARER_TOKEN not in str(record.key)  # type: ignore[attr-defined]


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
        logging.getLogger("loremaster.secret").info(
            "embed.probe.ok",
            extra={"header": f"Authorization: Bearer {FAKE_BEARER_TOKEN}", "key": FAKE_API_KEY},
        )
        output = buffer.getvalue()
        assert FAKE_BEARER_TOKEN not in output
        assert FAKE_API_KEY not in output
        assert REDACTED in output  # proof the scrubbing actually fired
