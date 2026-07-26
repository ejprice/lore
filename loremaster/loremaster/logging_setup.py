"""Structured logging for the lore monorepo (stdlib ``logging``, Mezmo-friendly).

This is the cross-cutting observability layer. Every module keeps the existing
``logger = logging.getLogger(__name__)`` precedent (e.g. ``lorescribe.sql``);
this module owns only the *sinks* and the *secret backstop*:

* :class:`JsonFormatter` renders ONE JSON object per record — ``ts`` (ISO-8601
  UTC), ``level``, ``logger``, ``msg`` (the static event string), plus every key
  the caller passed via ``extra={...}`` flattened to the top level so Mezmo
  indexes each field, plus :data:`EXC_FIELD` carrying the rendered traceback
  when the caller passed one. Stdlib :class:`logging.LogRecord` internals
  (``args``, ``levelno``, ``pathname``, …) are deliberately NOT serialised.
* :class:`KeyValueFormatter` renders a human ``ts level logger event k=v`` line
  for local development, with any traceback appended below it.
* :class:`RedactingFilter` is the CRITICAL secret backstop: it scrubs an
  ``Authorization: Bearer …`` header, an ``api_key``-style assignment, and any
  long high-entropy token — in the rendered message, the ``extra`` values, AND
  the rendered exception/stack — to :data:`REDACTED`. The discipline is that
  callers never log a secret in the first place (counts/statuses only); this
  filter is the last line of defence if one ever slips through.

  ⚠ Until #211 (2026-07-25) the last two of those were FALSE in both
  directions: the filter never touched ``exc_info``/``exc_text``, and the two
  formatters above discarded the exception outright — so eight production
  ``exc_info=True`` call sites logged no traceback at all, and any handler that
  DID render one rendered it unscrubbed. Both halves were fixed together,
  because scrubbing a surface nothing renders is a gate over a dead mechanism,
  and rendering a surface nothing scrubs is the leak the finding named.
* :func:`configure_logging` attaches exactly one stderr handler (with the chosen
  formatter + the redacting filter) to each lore-namespace logger
  (:data:`LORE_NAMESPACES`) with ``propagate=False`` — it does NOT reconfigure
  the root logger (that would fight uvicorn's own root handler) — and pins the
  chatty third-party logger ``httpx`` to ``WARNING``. It is
  idempotent: a second call resets handlers rather than stacking a duplicate.
"""

from __future__ import annotations

import json
import logging
import math
import re
import sys
import traceback
from collections import Counter
from datetime import UTC, datetime
from types import TracebackType
from typing import Any

# The logger namespaces this layer owns. Each gets a scoped stderr handler with
# ``propagate=False`` so lore's structured stream is isolated from uvicorn's root
# logger. A module's ``getLogger(__name__)`` lands under one of these prefixes.
LORE_NAMESPACES: tuple[str, ...] = ("loremaster", "loresigil", "lorescribe")

# Third-party loggers whose per-request INFO chatter would flood the structured
# stream; pinned to WARNING so only their genuine problems surface.
_THIRD_PARTY_WARN_NAMESPACES: tuple[str, ...] = ("httpx",)

# The sentinel a scrubbed secret is replaced with.
REDACTED = "***REDACTED***"

# The JSON key the rendered (and scrubbed) exception is emitted under (#211).
# One field rather than several, so a Mezmo query retrieves a whole traceback as
# a unit; named here rather than inlined so a consumer can import it.
#
# The VALUE is ``exc_info`` by lead ruling (2026-07-25), matching
# python-json-logger's convention rather than a lore-specific spelling: a served
# field name is a consumer surface, and lore's consumers are agents that learn
# the contract from what is served. It deliberately coincides with the
# ``LogRecord`` attribute of the same name — which ``_LOGRECORD_RESERVED``
# excludes from the flattened ``extra`` keys, so the two can never collide in one
# payload.
EXC_FIELD = "exc_info"

# The stdlib ``sys.exc_info()`` triple, as ``LogRecord.exc_info`` carries it.
# The all-``None`` arm is REACHABLE, not defensive padding: ``exc_info=True``
# outside an ``except`` block makes ``Logger._log`` store ``sys.exc_info()``,
# which is ``(None, None, None)`` — a TRUTHY tuple that names no exception.
_ExcInfo = (
    tuple[type[BaseException], BaseException, TracebackType | None]
    | tuple[None, None, None]
)

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
# the threshold is scrubbed. The charset excludes ``/`` and ``.`` so a dotted
# module name (``loremaster.index.indexer``) splits into short, sub-threshold
# segments and is NOT matched.
#
# ⚠ THAT IS NOT SUFFICIENT FOR FILE PATHS, and the comment here used to claim it
# was (#211 cold-audit Defect D). The charset INCLUDES ``-`` and ``_``, so a
# single path COMPONENT that is a UUID, a git SHA, a container overlay id or a
# nix store hash is one unbroken high-entropy run and was redacted — turning
# ``/tmp/ci/090685cb-2064-498d-8479-e141e4fd4ea5/app.py`` into
# ``/tmp/ci/***REDACTED***/app.py``. Measured false positives: UUID temp dirs,
# 64-hex container overlay paths, nix store paths. Tracebacks are DENSE in
# absolute paths, so the surface that most needs to stay readable was the one
# most affected — and the environments with hashy paths (CI runners, containers,
# ephemeral checkouts) are exactly the ones where a traceback matters most.
# :func:`_is_safe_high_entropy_run` is the guard; see its docstring for the
# threat model that makes its exemptions sound.
_TOKEN_RE = re.compile(r"[A-Za-z0-9+=_\-]{24,}")
_ENTROPY_BITS_THRESHOLD = 3.5

# The filesystem path separator. A high-entropy run ADJACENT to one is a path
# COMPONENT, not a credential (see :func:`_is_safe_high_entropy_run`).
_PATH_SEPARATOR = "/"

# The canonical RFC-4122 UUID form. Verified against an independent
# implementation rather than invented here: ``detect_secrets.filters.heuristic.
# _get_uuid_regex`` (detect-secrets 1.5.0) uses the identical pattern to decide
# that a high-entropy string is an id and not a secret. The FORMAT is a spec, so
# expressing it here is not a duplicated policy — the policy (what lore exempts)
# lives in the function below, once.
_UUID_RE = re.compile(
    r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", re.IGNORECASE
)


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


def _is_safe_high_entropy_run(text: str, start: int, end: int) -> bool:
    """Is the high-entropy run at ``text[start:end]`` a known-safe non-secret?

    An ALLOWLIST of the safe, never a denylist of the forbidden — the forbidden
    set (what a credential can look like) is unbounded; the safe set is small,
    enumerable and stated here in full:

    1. **A filesystem path component** — the run is adjacent to a ``/``. This is
       what fixes Defect D: UUID workspace dirs, 64-hex container overlay ids and
       nix store hashes are all single path components that clear the entropy bar.
    2. **A canonical RFC-4122 UUID**, anywhere — a correlation/trace/run id, not a
       credential.

    **THE THREAT MODEL, stated here because the exemptions are only sound under
    it** (CLAUDE.md: a gate needs a threat model, written IN the instrument). This
    filter catches the HONEST developer or dependency that lets a credential reach
    a log line — an ``Authorization`` header echoed back by a client, a connection
    string, a config repr. It is **NOT** a boundary against an author deliberately
    smuggling a secret out: anyone who can write log statements here can log
    anything in any encoding, and no regex changes that.

    Under that model these exemptions cost little: an honest credential leak does
    not arrive as ``/…/<secret>/…`` or wearing exact UUID punctuation, while the
    false positives they remove are constant, and land on tracebacks — the surface
    whose whole value is being readable.

    **The known bound they buy, met deliberately rather than discovered:** a
    secret embedded in a URL *path segment* (``https://host/<secret>/x``), or one
    that is itself a canonical UUID (some services do issue UUID API keys), is not
    caught by this backstop. The labelled patterns (:data:`_BEARER_RE`,
    :data:`_ASSIGNMENT_RE`) still catch either when it carries a label, and the
    real defence is the ``SecretStr`` TYPE at the boundary (#211 Half A), which
    prevents the value from reaching a log line at all.

    Args:
        text: The full string being scrubbed.
        start: Start offset of the candidate run within ``text``.
        end: End offset (exclusive) of the candidate run within ``text``.

    Returns:
        ``True`` when the run must be left intact.
    """
    before = text[start - 1] if start > 0 else ""
    after = text[end] if end < len(text) else ""
    if _PATH_SEPARATOR in (before, after):
        return True
    return _UUID_RE.fullmatch(text[start:end]) is not None


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
        if _is_safe_high_entropy_run(match.string, match.start(), match.end()):
            return token
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


def _render_exception(exc_info: _ExcInfo) -> str | None:
    """Render ``exc_info`` to traceback text exactly as the stdlib formatter would.

    Mirrors :meth:`logging.Formatter.formatException` (including its trailing
    newline strip) so a record this module pre-renders is byte-identical to one
    the stdlib would have produced — a foreign handler must not be able to tell
    the difference, or the pre-render becomes an observable behaviour change.

    Returns ``None`` for the all-``None`` triple. That case is reachable from
    ordinary code (``exc_info=True`` with no live exception — see
    :data:`_ExcInfo`), and the stdlib renders it as the useless line
    ``NoneType: None``; emitting nothing is both truer and quieter.
    """
    exception_type, exception, exception_traceback = exc_info
    if exception_type is None or exception is None:
        return None
    rendered = "".join(
        traceback.format_exception(exception_type, exception, exception_traceback)
    )
    if rendered.endswith("\n"):
        rendered = rendered[:-1]
    return rendered


def scrubbed_exception_text(record: logging.LogRecord) -> str | None:
    """Return this record's exception + stack text, SCRUBBED — or ``None``.

    THE ONE PLACE exception rendering is turned into log-safe text (#211). Both
    formatters in this module call it, and :class:`RedactingFilter` calls it to
    pre-populate ``record.exc_text``, so the scrubbing policy has exactly one
    implementation rather than one per sink.

    Prefers an already-rendered ``exc_text`` when present — which is what a
    stdlib formatter on ANOTHER handler will have cached onto this same record —
    and scrubs it regardless of who produced it, because that other handler had
    no scrubber. Scrubbing is idempotent (:data:`REDACTED` matches none of the
    patterns), so a value this filter already cleaned survives a second pass
    unchanged.

    Args:
        record: The record being emitted.

    Returns:
        The scrubbed traceback (plus ``stack_info``, when the caller asked for
        it), or ``None`` when the record carries no exception and no stack.
    """
    sections: list[str] = []
    if record.exc_text:
        sections.append(_scrub_text(record.exc_text))
    elif record.exc_info:
        rendered = _render_exception(record.exc_info)
        if rendered is not None:
            sections.append(_scrub_text(rendered))
    if record.stack_info:
        sections.append(_scrub_text(record.stack_info))
    if not sections:
        return None
    return "\n".join(sections)


class RedactingFilter(logging.Filter):
    """Scrub secrets from a record's message, ``extra`` values, AND its traceback.

    Mutates the record in place: the ``msg`` (and any positional ``args``), every
    caller-supplied ``extra`` attribute, and the rendered EXCEPTION + ``stack_info``
    are passed through :func:`_scrub_text` / :func:`_scrub_value`. Always returns
    ``True`` — its job is sanitisation, not filtering — so it composes with any
    level-based filtering above it.

    It writes ``exc_text`` and ``stack_info`` as SEPARATE attributes (which is why
    it cannot simply call :func:`scrubbed_exception_text`, whose job is to hand a
    formatter one joined string) — but both paths render through
    :func:`_render_exception` and scrub through :func:`_scrub_text`, so the
    rendering and redaction policies still have exactly one implementation each.

    **Why the exception leg exists (#211).** A traceback is rendered by the
    FORMATTER from ``exc_info``, never from ``msg`` — so this filter used to see
    none of it, and a credential in an exception's own message (a connection
    string, an ``Authorization`` header echoed back by a client, a config repr)
    reached the sink verbatim. The filter now renders the exception itself,
    scrubs it, and caches the result in ``record.exc_text``: the attribute
    :meth:`logging.Formatter.format` checks BEFORE re-rendering
    (``if not record.exc_text``), so any stdlib-compatible formatter downstream
    emits the scrubbed text without knowing this filter exists.

    **Two bounds worth meeting deliberately, not discovering (#211):**

    * ``record.exc_info`` is deliberately NOT cleared. It is shared state — the
      same record object reaches every handler — and other handlers may want the
      live exception for structured reporting. A formatter that ignores
      ``exc_text`` and re-renders from ``exc_info`` (``python-json-logger``
      inverts the stdlib's precedence and does exactly this) therefore still
      sees raw text. lore's own formatters route through
      :func:`scrubbed_exception_text` and so are safe regardless.
    * Handler filters run per handler, in handler order. If a handler WITHOUT
      this filter formats the record first, it emits raw text and caches it —
      this filter then repairs ``exc_text`` for everyone after it, but cannot
      un-emit what already went out. ``configure_logging`` attaches exactly one
      handler per lore namespace with ``propagate=False``, so that ordering does
      not arise in lore's own configuration today.
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
        # Render-and-scrub the exception into the attribute the stdlib formatter
        # honours ahead of ``exc_info``, so a handler that never heard of this
        # filter still emits scrubbed traceback text.
        if record.exc_text:
            record.exc_text = _scrub_text(record.exc_text)
        elif record.exc_info:
            rendered = _render_exception(record.exc_info)
            if rendered is not None:
                record.exc_text = _scrub_text(rendered)
        if record.stack_info:
            record.stack_info = _scrub_text(record.stack_info)
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
        # The exception is CALLER INTENT, not stdlib machinery: eight production
        # sites pass ``exc_info=True``/``exc_info=exc`` and every one of them was
        # emitting nothing at all before #211. One field, so Mezmo indexes the
        # whole traceback as a unit rather than smearing it across the line.
        exception_text = scrubbed_exception_text(record)
        if exception_text is not None:
            payload[EXC_FIELD] = exception_text
        return json.dumps(payload, default=str)


class KeyValueFormatter(logging.Formatter):
    """Render a record as a human ``ts level logger event k=v k=v`` line."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialise ``record`` to a single readable key=value line.

        An exception is appended BELOW the line, as the stdlib does — a traceback
        is inherently multi-line and folding it into a ``k=v`` token would make it
        unreadable in exactly the local-dev case this formatter exists for.
        """
        head = f"{_iso_utc(record)} {record.levelname} {record.name} {record.getMessage()}"
        pairs = " ".join(f"{key}={value}" for key, value in _extra_fields(record).items())
        line = f"{head} {pairs}".rstrip()
        exception_text = scrubbed_exception_text(record)
        if exception_text is not None:
            return f"{line}\n{exception_text}"
        return line


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
