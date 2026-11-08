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
* :func:`bare_record_key` / :func:`record_parts` / :func:`same_record` — a record's identity from its parts
  (``.id``) or from ANY of its text forms, never by comparing ``str(RecordID)`` with engine/bare text (SDK 3.0
  brackets a digit-led key; SDK 2.0 and 3.0 bracket a non-word one). Round 6 widened it from one helper to
  the one home every test-side id comparison uses (the ~30 cloned ``_bare`` helpers were folded into it).
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


def record_parts(value: Any) -> tuple[str | None, str]:
    """``(table, bare key)`` of a record id, from a ``RecordID``'s parts or from any of its TEXT forms.

    Round 6 (R15, MP-C 3c — C9's class in the TEST tree: one record compared through two text forms). The ONE
    test-side home for "which record is this": every test that compares a record id compares PARTS through
    this function, never ``str(RecordID)`` against engine or bare text. It accepts every rendering a record id
    reaches a test in — a ``RecordID`` (SDK 2.0 or 3.0), the SDK's ``str()`` (``keep:01M6…`` on 2.0,
    ``keep:⟨01M6…⟩`` on 3.0 for a digit-led key, ``principal:⟨mallory-x⟩`` on both for a non-word key), the
    engine's ``<string>`` cast (which may escape with backticks), and a bare key — so a comparison is
    independent of WHICH side rendered the id. Text with no ``:`` is a bare key (``table`` is ``None``).
    """
    key = getattr(value, "id", None)
    table = getattr(value, "table_name", None)
    if table is not None and key is not None:
        return str(table), str(key)
    if key is not None and not isinstance(value, str):
        # A DOMAIN object carrying its record id (``Principal.id``, ``Keep.id``, …): the id is the record.
        return record_parts(key)
    text = str(value)
    table_text, separator, key_text = text.partition(":")
    if not separator:
        return None, _unescape_key(text)
    return table_text, _unescape_key(key_text)


def _unescape_key(text: str) -> str:
    """Strip ONE layer of record-key escaping — ``⟨…⟩`` (the SDK and engine angle form) or ``` `…` ```."""
    for opening, closing in (("⟨", "⟩"), ("`", "`")):
        if len(text) >= 2 and text.startswith(opening) and text.endswith(closing):  # noqa: PLR2004 - two delimiters
            return text[1:-1]
    return text


def bare_record_key(value: Any) -> str:
    """The bare key of a ``RecordID`` (from its parts) or of ANY text form of one (:func:`record_parts`)."""
    return record_parts(value)[1]


def same_record(left: Any, right: Any) -> bool:
    """Whether two renderings (``RecordID`` or any text form) name the SAME record — table AND key; a bare key
    (no table) matches on the key alone."""
    left_table, left_key = record_parts(left)
    right_table, right_key = record_parts(right)
    tables_agree = left_table is None or right_table is None or left_table == right_table
    return tables_agree and left_key == right_key
