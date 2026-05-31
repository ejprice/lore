"""Structured logging for the lore monorepo (stdlib ``logging``, Mezmo-friendly).

This is the cross-cutting observability layer. Every module keeps the existing
``logger = logging.getLogger(__name__)`` precedent (e.g. ``lorescribe.sql``);
this module owns only the *sinks* and the *secret backstop*:

* :class:`JsonFormatter` renders ONE JSON object per record — ``ts`` (ISO-8601
  UTC), ``level``, ``logger``, ``msg`` (the static event string), plus every key
  the caller passed via ``extra={...}`` flattened to the top level so Mezmo
  indexes each field. Stdlib :class:`logging.LogRecord` internals (``args``,
  ``levelno``, ``pathname``, …) are deliberately NOT serialised.
* :class:`KeyValueFormatter` renders a human ``ts level logger event k=v`` line
  for local development.
* :class:`RedactingFilter` is the CRITICAL secret backstop: it scrubs an
  ``Authorization: Bearer …`` header, an ``api_key``-style assignment, and any
  long high-entropy token — in BOTH the rendered message and the ``extra``
  values — to :data:`REDACTED`. The discipline is that callers never log a
  secret in the first place (counts/statuses only); this filter is the last line
  of defence if one ever slips through.
* :func:`configure_logging` attaches exactly one stderr handler (with the chosen
  formatter + the redacting filter) to each lore-namespace logger
  (:data:`LORE_NAMESPACES`) with ``propagate=False`` — it does NOT reconfigure
  the root logger (that would fight uvicorn's own root handler) — and pins the
  chatty third-party loggers (``httpx``/``qdrant_client``) to ``WARNING``. It is
  idempotent: a second call resets handlers rather than stacking a duplicate.
"""

from __future__ import annotations

import json
import logging
import math
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from typing import Any

# The logger namespaces this layer owns. Each gets a scoped stderr handler with
# ``propagate=False`` so lore's structured stream is isolated from uvicorn's root
# logger. A module's ``getLogger(__name__)`` lands under one of these prefixes.
LORE_NAMESPACES: tuple[str, ...] = ("loremaster", "loresigil", "lorescribe")

# Third-party loggers whose per-request INFO chatter would flood the structured
# stream; pinned to WARNING so only their genuine problems surface.
_THIRD_PARTY_WARN_NAMESPACES: tuple[str, ...] = ("httpx", "qdrant_client")

# The sentinel a scrubbed secret is replaced with.
REDACTED = "***REDACTED***"

# The format selectors accepted by :func:`configure_logging`.
FORMAT_JSON = "json"
FORMAT_KEYVALUE = "keyvalue"

# The set of :class:`logging.LogRecord` attribute names that are stdlib
# machinery, not caller-supplied ``extra`` fields. Everything on a record that is
# NOT one of these (and is not a private dunder) is treated as an ``extra`` key.
_LOGRECORD_RESERVED: frozenset[str] = frozenset(
    {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "taskName", "message",
    }
)

# Explicit secret patterns (the common, named shapes). Each capturing group's
# secret span is replaced with REDACTED; surrounding label text is preserved.
_BEARER_RE = re.compile(r"(Bearer\s+)(\S+)", re.IGNORECASE)
_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(api[_-]?key|apikey|token|secret|password|authorization)\b(\s*[=:]\s*)(\S+)"
)

# A bare high-entropy token (no label) is the catch-all backstop: any UNBROKEN
# run of >= this many base64/JWT-style characters whose Shannon entropy clears
# the threshold is scrubbed. The charset deliberately EXCLUDES ``/`` and ``.``
# so a file path (``src/a/b.py``) or a dotted module name
# (``loremaster.index.indexer``) splits into short, sub-threshold segments and
# is NOT matched — only a contiguous secret-shaped blob (a bearer/JWT/key) is.
_TOKEN_RE = re.compile(r"[A-Za-z0-9+=_\-]{24,}")
_ENTROPY_BITS_THRESHOLD = 3.5


def _shannon_entropy_bits(text: str) -> float:
    """Return the Shannon entropy (bits/char) of ``text`` — a randomness proxy.

    A high-entropy run of characters (a random key/token) scores well above a
    repetitive English word or a structured path, so it discriminates a secret
    from ordinary log text without a label.
    """
    if not text:
        return 0.0
    counts = Counter(text)
    length = len(text)
    return -sum((n / length) * math.log2(n / length) for n in counts.values())


def _scrub_text(value: str) -> str:
    """Redact secrets from a single string: bearer, labelled assignment, entropy.

    Applied in order so the most specific (label-preserving) patterns run before
    the bare-token entropy sweep. The output keeps non-secret structure intact so
    a redacted log line is still readable (``Authorization: Bearer ***REDACTED***``).
    """
    scrubbed = _BEARER_RE.sub(rf"\1{REDACTED}", value)
    scrubbed = _ASSIGNMENT_RE.sub(rf"\1\2{REDACTED}", scrubbed)

    def _maybe_redact_token(match: re.Match[str]) -> str:
        token = match.group(0)
        if _shannon_entropy_bits(token) >= _ENTROPY_BITS_THRESHOLD:
            return REDACTED
        return token

    return _TOKEN_RE.sub(_maybe_redact_token, scrubbed)


def _scrub_value(value: Any) -> Any:
    """Scrub a single ``extra`` value, recursing through containers.

    Strings are scrubbed directly; lists/tuples/dicts are walked so a secret
    nested in a structured field is still caught; non-string scalars (ints,
    bools, floats, ``None``) are returned untouched (they cannot carry a token).
    """
    if isinstance(value, str):
        return _scrub_text(value)
    if isinstance(value, dict):
        return {key: _scrub_value(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple)):
        scrubbed = [_scrub_value(item) for item in value]
        return type(value)(scrubbed)
    return value


class RedactingFilter(logging.Filter):
    """Scrub secrets from a record's message + ``extra`` values (never drops it).

    Mutates the record in place: the ``msg`` (and any positional ``args``) and
    every caller-supplied ``extra`` attribute are passed through :func:`_scrub_text`
    / :func:`_scrub_value`. Always returns ``True`` — its job is sanitisation, not
    filtering — so it composes with any level-based filtering above it.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitise ``record`` in place and keep it (returns ``True`` always)."""
        if isinstance(record.msg, str):
            record.msg = _scrub_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: _scrub_value(v) for k, v in record.args.items()}
            else:
                record.args = tuple(_scrub_value(a) for a in record.args)
        for key, value in list(record.__dict__.items()):
            if key in _LOGRECORD_RESERVED or key.startswith("_"):
                continue
            record.__dict__[key] = _scrub_value(value)
        return True


def _extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    """Return the caller-supplied ``extra`` keys carried on ``record``.

    Everything on the record that is neither stdlib machinery
    (:data:`_LOGRECORD_RESERVED`) nor a private dunder is an ``extra`` field the
    caller attached via ``logger.<level>(msg, extra={...})``.
    """
    return {
        key: value
        for key, value in record.__dict__.items()
        if key not in _LOGRECORD_RESERVED and not key.startswith("_")
    }


def _iso_utc(record: logging.LogRecord) -> str:
    """Render a record's creation time as an ISO-8601 UTC timestamp."""
    return datetime.fromtimestamp(record.created, tz=UTC).isoformat()


class JsonFormatter(logging.Formatter):
    """Render a record as one JSON object: ts/level/logger/msg + flattened extra."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialise ``record`` to a single-line JSON object.

        ``ts`` is ISO-8601 UTC, ``msg`` is the rendered (and already-scrubbed)
        event string, and every ``extra`` key is flattened to the JSON top level
        so Mezmo indexes each as its own field. Non-JSON-native extra values fall
        back to ``str`` via ``default`` so the formatter never raises on a record.
        """
        payload: dict[str, Any] = {
            "ts": _iso_utc(record),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        payload.update(_extra_fields(record))
        return json.dumps(payload, default=str)


class KeyValueFormatter(logging.Formatter):
    """Render a record as a human ``ts level logger event k=v k=v`` line."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialise ``record`` to a single readable key=value line."""
        head = f"{_iso_utc(record)} {record.levelname} {record.name} {record.getMessage()}"
        pairs = " ".join(f"{key}={value}" for key, value in _extra_fields(record).items())
        return f"{head} {pairs}".rstrip()


def _resolve_formatter(fmt: str) -> logging.Formatter:
    """Map a format selector to its formatter (``json`` default, ``keyvalue``)."""
    if fmt == FORMAT_KEYVALUE:
        return KeyValueFormatter()
    return JsonFormatter()


def configure_logging(level: str, fmt: str) -> None:
    """Configure the lore-namespace loggers idempotently (scoped, secret-safe).

    For each namespace in :data:`LORE_NAMESPACES`: reset its handlers (so a second
    call does not stack a duplicate / double-emit), attach ONE stderr
    :class:`logging.StreamHandler` carrying the chosen formatter + a
    :class:`RedactingFilter`, set the level, and turn OFF propagation so lore's
    structured stream never leaks into — or doubles through — uvicorn's root
    handler. The chatty third-party loggers are pinned to ``WARNING``. The root
    logger is intentionally left untouched.

    Args:
        level: The minimum level name (e.g. ``"INFO"``). The entry path resolves
            this as ``os.environ.get("LORE_LOG_LEVEL", config.logging.level)`` so
            the environment overrides the config default at run time.
        fmt: ``"json"`` or ``"keyvalue"`` (anything else falls back to JSON).
    """
    resolved_level = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)
    for namespace in LORE_NAMESPACES:
        logger = logging.getLogger(namespace)
        # Reset handlers so a re-configure replaces rather than stacks (idempotent).
        for existing in list(logger.handlers):
            logger.removeHandler(existing)
        handler = logging.StreamHandler(stream=sys.stderr)
        handler.setFormatter(_resolve_formatter(fmt))
        handler.addFilter(RedactingFilter())
        logger.addHandler(handler)
        logger.setLevel(resolved_level)
        logger.propagate = False
    for namespace in _THIRD_PARTY_WARN_NAMESPACES:
        logging.getLogger(namespace).setLevel(logging.WARNING)
