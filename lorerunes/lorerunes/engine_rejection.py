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


@contextlib.contextmanager
def reclassify(
    *,
    passthrough: tuple[type[BaseException], ...],
    catch: tuple[type[BaseException], ...],
    make_error: Callable[[], BaseException],
) -> Iterator[None]:
    """Reclassify exceptions raised inside the ``with`` body.

    Applies, in order:

    * an exception that is an instance of any class in ``passthrough`` is re-raised
      UNTOUCHED (the same instance, no re-chaining) — checked FIRST, because the pass-through
      classes may subclass the caught ones (see the module docstring);
    * otherwise an exception that is an instance of any class in ``catch`` is translated into
      ``make_error()``'s result, raised ``from`` the original (its ``__cause__`` is preserved
      so the raw engine detail is never lost);
    * every other exception propagates unchanged — this manager never uses a bare
      ``except Exception`` and never swallows anything outside ``catch``.

    ``make_error`` is a lazy, zero-argument factory: it is invoked EXACTLY once, and ONLY on a
    ``catch``, to build the single error raised. A clean body (or a pass-through) never calls
    it.

    Args:
        passthrough: The exception classes to re-raise untouched. Checked before ``catch`` so
            a pass-through that subclasses a caught class is never translated. An empty tuple
            means "no pass-throughs" — every ``catch`` instance is then translated.
        catch: The exception classes to translate into ``make_error()``'s result. Membership
            follows the normal ``isinstance`` hierarchy, so a subclass of a ``catch`` member
            (that is not itself a ``passthrough``) is translated too.
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
    except catch as error:
        raise make_error() from error
