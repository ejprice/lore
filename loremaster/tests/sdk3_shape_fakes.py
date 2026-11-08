"""Test-side SDK-shape helpers for packet SDK3 (surrealdb 2.0.0 → 3.0.0), shared by the hand-written
SDK doubles.

R12 F-a (lead, 2026-11-07): during the interim the doubles answer PER SDK VERSION, so HEAD (SDK 2.0.0) stays
green
until the build lands and the SDK-3.0 reference grades the same tests in SDK 3.0's shape.

⚠ DROP LIST (packet doc §ROUND 5, row F-a): in the commit that pins ``surrealdb==3.0.0`` the builder deletes
the
SDK-2.0 branch of :func:`one_statement_answer` (the ``SDK_MAJOR`` test with it); the helpers below stay.

Three helpers, each the ONE home for its rule (C1, C2, C8 in packet doc §R4.7):

* :func:`one_statement_answer` — what ``connection.query(<one statement>)`` returns: SDK 3.0 answers the
  per-statement list (R2: the seam selects its ONE statement's result); SDK 2.0 answered that result bare.
* :func:`route_connections` — make every owner's next SDK connection the double a test supplies, by rebinding
  EVERY name in a loaded ``loremaster`` module that is bound to the SDK's ``AsyncSurreal`` or to the shared
  connection factory (``store._txn.open_surreal_connection``, R5). Derived from the live module objects, so it
  holds whichever name an owner imports — the per-module ``AsyncSurreal`` at HEAD, the shared factory after R5
  —
  instead of patching one per-module name the build deletes.
* :func:`bare_record_key` — a record's bare KEY from its parts (``.id``), never by splitting ``str(RecordID)``
  (SDK 3.0 brackets a digit-led key; SDK 2.0 and 3.0 bracket a non-word one).
"""

from __future__ import annotations

import importlib.metadata
import sys
from collections.abc import Callable
from typing import Any

import pytest
import surrealdb

#: The installed SDK's major version — the ONE switch of the F-a interim.
SDK_MAJOR = int(importlib.metadata.version("surrealdb").split(".")[0])


def one_statement_answer(statement_result: Any) -> Any:
    """What the installed SDK's ``query()`` returns for ONE statement whose result is ``statement_result``."""
    return [statement_result] if SDK_MAJOR >= 3 else statement_result


def route_connections(
    monkeypatch: pytest.MonkeyPatch, factory: Callable[..., Any], *, modules: tuple[str, ...] | None = None
) -> list[str]:
    """Rebind every loaded ``loremaster`` module's connection-constructor name to ``factory`` — or, with
    ``modules``, only those modules' (the per-owner scope the retired per-module patch had).

    ``factory`` must accept ``(url, **kwargs)``: the shared factory passes reconnect/timeout options (R5); the
    per-module ``AsyncSurreal(url)`` at HEAD passes none. Returns the ``module.name`` bindings it replaced, so
    a
    caller can assert the route reached the owner it drives (an empty list is a route that reached nothing).
    """
    targets: list[object] = [surrealdb.AsyncSurreal]
    txn = sys.modules.get("loremaster.store._txn")
    shared = getattr(txn, "open_surreal_connection", None) if txn is not None else None
    if shared is not None:
        targets.append(shared)
    replaced: list[str] = []
    for module_name, module in list(sys.modules.items()):
        if module is None or not (module_name == "loremaster" or module_name.startswith("loremaster.")):
            continue
        if modules is not None and module_name not in modules:
            continue
        for attribute, value in list(vars(module).items()):
            if any(value is target for target in targets):
                monkeypatch.setattr(module, attribute, factory)
                replaced.append(f"{module_name}.{attribute}")
    return replaced


def bare_record_key(value: Any) -> str:
    """The bare key of a ``RecordID`` (from its parts) or of ``table:key`` text."""
    key = getattr(value, "id", None)
    if getattr(value, "table_name", None) is not None and key is not None:
        return str(key)
    text = str(value)
    return text.partition(":")[2] or text
