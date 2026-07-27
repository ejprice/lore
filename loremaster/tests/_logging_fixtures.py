"""Shared logging-test plumbing — ONE implementation, two contracts.

``test_logging_setup.py`` (the sink/formatter contract, #211) and
``test_secret_leak_vectors.py`` (packet 42's leak-vector contract) both need to
build a real :class:`logging.LogRecord`, snapshot/restore the *global* lore
namespace logger state, and drive an emission through the REAL
``configure_logging`` handler.

Cloning that plumbing into the second file would be copy #2 of a POLICY, not of
trivia (CLAUDE.md, ONE IMPLEMENTATION — "if two call sites need the same policy,
it is a function they call"). The policy is load-bearing twice over:

* the snapshot/restore is what stops one test's handler leaking into the next
  (``configure_logging`` mutates process-global state), and
* :func:`emit_through_configured_logger` is the only honest way to assert what
  actually leaves the process — the pins that drive ``_scrub_text`` directly
  prove a string transform, not a served surface.

Nothing here asserts anything. It is fixture plumbing; the contracts live in the
two test modules that import it.
"""

from __future__ import annotations

import io
import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from loremaster.logging_setup import LORE_NAMESPACES, configure_logging

# The third-party loggers ``configure_logging`` pins to WARNING. Their state is
# mutated by the same call, so it is restored with the lore namespaces or a
# level change leaks across tests.
SILENCED_THIRD_PARTY: tuple[str, ...] = ("httpx",)

# The namespace whose single handler the emit helper re-points at a buffer, and
# the child logger emissions are made through. Read from the production tuple
# rather than hardcoded, so a namespace rename moves this with it.
EMITTING_NAMESPACE: str = LORE_NAMESPACES[0]


@contextmanager
def restored_lore_logger_state() -> Iterator[None]:
    """Snapshot + restore every logger ``configure_logging`` touches.

    ``configure_logging`` mutates handlers, levels and ``propagate`` on the
    lore-namespace loggers and on the silenced third-party ones. Without a
    restore, a configure in one test leaks its handler into the next — the
    cross-contamination of shared global state the lifecycle rule forbids.
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


def make_record(
    *,
    name: str = "loremaster.demo",
    level: int = logging.INFO,
    msg: str = "event.demo",
    extra: dict[str, object] | None = None,
) -> logging.LogRecord:
    """Build a real :class:`logging.LogRecord` with ``extra`` keys attached.

    Mirrors what ``logger.info(msg, extra={...})`` produces: each extra key is
    set as an attribute on the record (exactly how the stdlib threads ``extra``
    through), so a formatter sees the same shape it would in production.

    Args:
        name: The logger name recorded on the record.
        level: The numeric level.
        msg: The event string.
        extra: Caller-supplied fields, attached as record attributes.

    Returns:
        The populated record.
    """
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )
    for key, value in (extra or {}).items():
        setattr(record, key, value)
    return record


def emit_through_configured_logger(
    fmt: str,
    action: Callable[[logging.Logger], None],
    *,
    child: str = "exc",
    level: str = "DEBUG",
) -> str:
    """Run ``action`` against a REAL configured lore logger; return the stream.

    This is the production path end to end — ``configure_logging`` builds the
    handler, attaches the real formatter and the real
    :class:`~loremaster.logging_setup.RedactingFilter`, and the only substitution
    is the handler's stream. A pin that calls ``_scrub_text`` directly proves a
    string transform; this proves what leaves the process.

    Args:
        fmt: ``"json"`` or ``"keyvalue"``.
        action: Receives the child logger and performs the emission.
        child: Suffix of the child logger name (distinct per test so records
            cannot be attributed to the wrong case).
        level: Minimum level to configure.

    Returns:
        Everything the handler wrote.
    """
    buffer = io.StringIO()
    configure_logging(level=level, fmt=fmt)
    namespace_logger = logging.getLogger(EMITTING_NAMESPACE)
    handler = namespace_logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler), (
        "configure_logging no longer attaches a StreamHandler — this helper "
        "re-points its stream and cannot capture anything else"
    )
    handler.setStream(buffer)
    action(logging.getLogger(f"{EMITTING_NAMESPACE}.{child}"))
    return buffer.getvalue()
