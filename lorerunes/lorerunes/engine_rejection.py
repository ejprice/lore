"""``reclassify`` — the shared exception-reclassification control flow.

Layer 1 of the two-layer engine-rejection seam (finding #400 / packet-61 Fork I addendum
D2). This is the *control-flow POLICY* — "re-raise the pass-through classes untouched,
translate the caught classes into a fresh domain error chained ``from`` the original" —
extracted ONCE so the many store write-paths that shared the idiom stop cloning it (the
ONE-IMPLEMENTATION rule: a policy two call sites must agree on is a function they call,
never a pattern they clone).

It is parameterised over the exception CLASSES it receives — it never names a concrete
taxonomy — so it can live in stdlib-only ``lorerunes`` (its ``__init__`` charters *"error
classification"* here explicitly) with no dependency on any sibling. The surreal taxonomy
is bound ONE level up, by ``loremaster.store._txn.wrap_store_rejection`` (Layer 2), which
supplies the real ``passthrough`` / ``catch`` / ``make_error``.

⚠ THE ``passthrough``-FIRST ORDERING IS LOAD-BEARING, not stylistic. The intended callers'
pass-through classes SUBCLASS their caught class (``SurrealConnectionError`` and
``TxnContentionExhaustedError`` both subclass ``SurrealStoreError`` — ``_txn.py:120/156``),
so a naive ``except catch: translate`` with no earlier ``except passthrough: raise`` would
TRANSLATE a transport fault into the domain error — a real regression (a connection drop
masquerading as a domain rejection, lost to the retry/lifecycle layer). The pass-through
clause is therefore re-raised FIRST, before the catch-and-translate is ever reached.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable, Iterator

#: What ``reclassify`` may be told to translate: the exception CLASSES (membership by ``isinstance``), or a
#: PREDICATE over the raised exception itself (am-37 §15.1: *catch-by-property* — "the faults I can explain",
#: the allowlist-the-safe form of a catch tuple, for a set no class tree can express).
CatchSpec = tuple[type[BaseException], ...] | Callable[[BaseException], bool]


def _is_caught(catch: CatchSpec, error: BaseException) -> bool:
    """Whether ``error`` is one ``catch`` explains: a tuple is an ``isinstance`` test, anything else is called
    as the predicate (am-37 §15.1). The ONE place the two forms are told apart."""
    if isinstance(catch, tuple):
        return isinstance(error, catch)
    return catch(error)


@contextlib.contextmanager
def reclassify(
    *,
    passthrough: tuple[type[BaseException], ...],
    catch: CatchSpec,
    make_error: Callable[[], BaseException],
) -> Iterator[None]:
    """Reclassify exceptions raised inside the ``with`` body.

    Applies, in order:

    * an exception that is an instance of any class in ``passthrough`` is re-raised
      UNTOUCHED (the same instance, no re-chaining) — checked FIRST, because the pass-through
      classes may subclass the caught ones (see the module docstring);
    * otherwise an exception that ``catch`` explains — an instance of any class in a ``catch``
      tuple, or one a ``catch`` predicate answers TRUE for — is translated into
      ``make_error()``'s result, raised ``from`` the original (its ``__cause__`` is preserved
      so the raw engine detail is never lost);
    * every other exception propagates unchanged, as the SAME object (a bare ``raise``) —
      this manager never translates anything ``catch`` does not explain and never swallows
      anything at all; the predicate is never consulted for a pass-through.

    ``make_error`` is a lazy, zero-argument factory: it is invoked EXACTLY once, and ONLY on a
    ``catch``, to build the single error raised. A clean body (or a pass-through) never calls
    it.

    Args:
        passthrough: The exception classes to re-raise untouched. Checked before ``catch`` so
            a pass-through that subclasses a caught class is never translated. An empty tuple
            means "no pass-throughs" — every ``catch`` instance is then translated.
        catch: What to translate into ``make_error()``'s result (:data:`CatchSpec`). A TUPLE of
            exception classes: membership follows the normal ``isinstance`` hierarchy, so a
            subclass of a ``catch`` member (that is not itself a ``passthrough``) is translated
            too — unchanged. A PREDICATE ``(error) -> bool`` (am-37 §15.1): called with the
            raised exception, at most once, only for a non-pass-through; TRUE translates,
            FALSE re-raises the exception untouched.
        make_error: A zero-argument callable that builds the domain error to raise on a
            ``catch``. Called at most once, lazily.

    Yields:
        ``None`` — the manager wraps the body only for its exception handling; it produces no
        value.
    """
    try:
        yield
    except passthrough:
        raise
    except BaseException as error:
        # Every non-pass-through reaches ONE decision, whatever the catch's form; what it does not
        # explain is re-raised untouched (bare ``raise``: same object, traceback, cancellation semantics).
        if not _is_caught(catch, error):
            raise
        raise make_error() from error
