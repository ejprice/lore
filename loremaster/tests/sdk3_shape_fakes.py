"""Test-side SDK-shape helpers for packet SDK3 (surrealdb 2.0.0 → 3.0.0), shared by the hand-written
SDK doubles.

R21 (operator, 2026-11-08) simplifies R12 F-a: the doubles answer in SDK 3.0's shape ONLY — no version-aware
interim branch (contract round 7 deleted it; R26-2: a version-branched fake asserts two worlds under one
name). Nodes that go RED at HEAD (SDK 2.0.0) because of it are DECLARED and registered (R22 rider 3) until
the build commit pins ``surrealdb==3.0.0``.

Three helpers, each the ONE home for its rule (C1, C2, C8 in packet doc §R4.7):

* :func:`one_statement_answer` — what ``connection.query(<one statement>)`` returns: SDK 3.0 answers the
  per-statement list (R2: the seam selects its ONE statement's result).
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
* :func:`digit_led_record_key` / :func:`letter_led_record_key` — FIXED record keys of each shape (R26-3: pure,
  I/O-free key-shape helpers live here; ``_governed_contract.rekey_principal`` applies them to a store).
"""

from __future__ import annotations

import asyncio
import contextlib
import sys
import uuid
from collections.abc import Callable, Iterator
from typing import Any, NoReturn

import pytest
import surrealdb


class SdkRequestTimeoutMixin:
    """SDK 3.0's ``connection.timeout(seconds)`` for a test double — ONE home (sidecar RULING-13 FORK T, R41).

    The teardown cap is ``with connection.timeout(TEARDOWN_KILL_TIMEOUT_SECONDS): await connection.kill(id)``;
    every double a ``_safe_kill`` can reach inherits this instead of growing its own ``timeout()``. It is a
    ``nullcontext`` that RECORDS the budget for the block's duration (``request_budget_s``), so a double
    whose request parks (:meth:`park_like_the_sdk`) can do what the SDK does: wait out the budget and raise
    its typed ``TransportTimeoutError`` — or, with no budget set, park forever (SDK: until the 30 s
    default)."""

    request_budget_s: float | None = None

    @contextlib.contextmanager
    def timeout(self, seconds: float | None) -> Iterator[None]:
        previous = self.request_budget_s
        self.request_budget_s = seconds
        try:
            yield
        finally:
            self.request_budget_s = previous

    async def park_like_the_sdk(self) -> NoReturn:
        """A request on a dropped socket under SDK 3.0: no reply inside the budget raises the SDK's
        ``TransportTimeoutError``."""
        budget = self.request_budget_s
        if budget is None:
            await asyncio.Event().wait()
        await asyncio.sleep(budget or 0)
        raise surrealdb.errors.TransportTimeoutError(f"no reply within {budget} s (SDK-shape test double)")


def one_statement_answer(statement_result: Any) -> Any:
    """What SDK 3.0's ``query()`` returns for ONE statement whose result is ``statement_result``."""
    return [statement_result]


def digit_led_record_key(seed: str) -> str:
    """A FIXED, DIGIT-LED, word-character record key derived from ``seed`` (R15 / MP-C 3c, R12: "pins it
    deterministically with a digit-led principal key"). SDK 3.0's ``str(RecordID)`` brackets a digit-led key
    (``principal:⟨0…⟩``) while SDK 2.0 does not, so a test comparing two text forms of such an id fails on
    SDK 3 EVERY run instead of on the ~28% of runs an engine-minted id happens to start with a digit. Word
    characters only, so SDK 2.0 renders it bare (a hyphenated uuid would be bracketed by BOTH SDKs)."""
    return f"0{uuid.uuid5(uuid.NAMESPACE_URL, f'lore://test/digit-led/{seed}').hex[1:]}"


def letter_led_record_key(seed: str) -> str:
    """A FIXED, LETTER-LED, word-character record key derived from ``seed`` — the discrimination leg R26-3
    requires beside a digit-led default (a digit-led-only fixture is a monoculture in the other direction)."""
    return f"z{uuid.uuid5(uuid.NAMESPACE_URL, f'lore://test/letter-led/{seed}').hex[1:]}"


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
