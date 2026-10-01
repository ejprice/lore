"""Packet 63c-i-a, amendment 37 §13 class B — "Fail-closed shapes — ONE policy" (F-1, F-6, F-7, F-5).

PROPERTY (am-37 §13 B, verbatim intent): *a driver answer in the wrong shape never decides a served value or a
write; it raises the ONE class the CLI launders (``SurrealStoreError``), never a ``TypeError``, never ``0``,
never ``[]``.*

DOMAIN (derived, never listed): every function in ``loremaster/principals.py`` / ``loremaster/governed.py``
whose body tests ``isinstance(<x>, list|dict)`` (tuple forms included). The ALLOWLIST is exactly THREE helpers
in ``governed`` (am-37 §13.1 item 1, commit ``d6cdd0b``): ``group_all_count``, ``rows_of`` and ``map_of``.
Any other shape-tester reds BY NAME (parametrized at
collection over the AST-derived set — the completeness assertion of the class).

Operational reading of "on a store result" (written into REPORT-sub-63c13-b-1 §Readings): EVERY
``isinstance(…, list|dict)`` test in those two modules counts: a static walker cannot tell a store answer from
a non-store value, and the modules' only list/dict shape tests at fix5 ``5f2d7c43`` ARE store answers. The two
``INFO FOR DB`` map-readers (``PrincipalStore._table_exists`` — fail-OPEN — and
``_agent_migration_preconditions``) were held as strict xfails until §13.1 ruled (a): they route through the
new ``governed.map_of`` and are now PLAIN pins, RED at fix5 by name.

Behaviour pins drive the seams with FAKES (monkeypatched run_query / _query / execute_transaction);
only the F-5 pin uses the live TEST store (``ws://127.0.0.1:18000``) via the a19 ``_governed_world`` harness
(``unique_database()``), because the leftover read must follow a REALLY committed backfill.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import loremaster.governed as governed_module
import pytest
import test_fixwave_a19_63c_i_a as a19  # module-qualified: its Test* classes must not be re-collected here
from _surreal_harness import run
from loremaster.principals import PrincipalNotFoundError, PrincipalStore, PrincipalStoreError
from loremaster.store._txn import SurrealStoreError
from pydantic import SecretStr

from loremaster import principals
from lorerunes import pdp

#: The module namespace, for constants principals re-uses but does not re-export (mypy attr-defined).
_PRINCIPALS_NS: dict[str, Any] = vars(principals)
MESSAGE_TABLE: str = _PRINCIPALS_NS["MESSAGE_TABLE"]


# =========================================================================== #
# The AST-derived domain + the allowlist pin (the completeness assertion)
# =========================================================================== #

#: The ONLY functions in the two modules allowed to test a store answer's shape (am-37 §13 B + §13.1 item 1).
_ALLOWLIST: frozenset[str] = frozenset({"governed.group_all_count", "governed.rows_of", "governed.map_of"})

_SHAPE_NAMES: frozenset[str] = frozenset({"list", "dict"})
_MODULES: dict[str, Path] = {
    "principals": Path(inspect.getfile(principals)),
    "governed": Path(inspect.getfile(governed_module)),
}


def _tests_list_or_dict(call: ast.Call) -> bool:
    """Whether ``call`` is ``isinstance(<x>, list|dict)`` or ``isinstance(<x>, (… list|dict …))``."""
    if not (isinstance(call.func, ast.Name) and call.func.id == "isinstance" and len(call.args) == 2):
        return False
    target = call.args[1]
    names = target.elts if isinstance(target, ast.Tuple) else [target]
    return any(isinstance(name, ast.Name) and name.id in _SHAPE_NAMES for name in names)


class _ShapeTesterWalker(ast.NodeVisitor):
    """Collect ``<module>.<Class>.<function>`` for every function whose OWN body (innermost def) holds a
    list/dict ``isinstance`` test."""

    def __init__(self, module: str) -> None:
        self._scope: list[str] = [module]
        self._function_depth = 0
        self.found: set[str] = set()

    def _enter(self, node: ast.AST, name: str, *, is_function: bool) -> None:
        self._scope.append(name)
        self._function_depth += int(is_function)
        self.generic_visit(node)
        self._function_depth -= int(is_function)
        self._scope.pop()

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._enter(node, node.name, is_function=False)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._enter(node, node.name, is_function=True)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._enter(node, node.name, is_function=True)

    def visit_Call(self, node: ast.Call) -> None:
        if self._function_depth and _tests_list_or_dict(node):
            self.found.add(".".join(self._scope))
        self.generic_visit(node)


def _shape_testers_in_source(module: str, source: str) -> set[str]:
    walker = _ShapeTesterWalker(module)
    walker.visit(ast.parse(source))
    return walker.found


def _derived_shape_testers() -> list[str]:
    found: set[str] = set()
    for module, path in _MODULES.items():
        found |= _shape_testers_in_source(module, path.read_text(encoding="utf-8"))
    return sorted(found)


_DERIVED = _derived_shape_testers()


class TestOneShapePolicyAllowlist63c13b:
    @pytest.mark.parametrize("qualname", _DERIVED)
    def test_only_the_three_allowlisted_helpers_test_a_store_answer_shape(self, qualname: str) -> None:
        """⚠ RED at fix5 ``5f2d7c43`` by name for every non-allowlisted shape-tester (``_as_rows``,
        ``_governed_select``, ``_rows_stamped``, ``authorize_guarded``, ``_table_exists``,
        ``_agent_migration_preconditions``). am-37 §13 B + §13.1: the ONE fail-closed policy lives in
        ``group_all_count`` / ``rows_of`` / ``map_of``; any other shape-tester is a private copy of it."""
        assert qualname in _ALLOWLIST, (
            f"{qualname} tests an answer's list/dict shape itself — am-37 §13 B/§13.1 allow exactly "
            f"{sorted(_ALLOWLIST)}; route the read through governed.rows_of / map_of / group_all_count"
        )

    def test_positive_control_the_walker_finds_group_all_count(self) -> None:
        """CONTROL: the walker sees the one helper known to test shape at every sha since am-37 §8.3."""
        assert "governed.group_all_count" in _DERIVED, _DERIVED

    def test_non_vacuity_the_walker_discriminates(self) -> None:
        """The walker catches the bare, tuple and nested/method forms and ignores non-list/dict tests."""
        source = (
            "def bare(x):\n    return isinstance(x, list)\n"
            "def tupled(x):\n    return isinstance(x, (tuple, dict))\n"
            "def other(x):\n    return isinstance(x, (str, int))\n"
            "class K:\n    async def method(self, x):\n        return isinstance(x, dict)\n"
            "def outer(x):\n    def inner(y):\n        return isinstance(y, list)\n    return inner\n"
            "MODULE_LEVEL = isinstance([], list)\n"
        )
        assert _shape_testers_in_source("m", source) == {"m.bare", "m.tupled", "m.K.method", "m.outer.inner"}
        assert len(_DERIVED) >= 2, f"the derived domain is implausibly small: {_DERIVED}"

    def test_the_allowlisted_helpers_are_all_derived_shape_testers(self) -> None:
        """⚠ RED at fix5 (``rows_of`` / ``map_of`` do not exist). The allowlist is not decoration: every
        allowlisted helper must itself be a derived shape-tester (a helper that stopped testing shape is a
        stale entry — delete it)."""
        missing = sorted(_ALLOWLIST - set(_DERIVED))
        assert not missing, f"allowlisted helpers the walker does not derive: {missing}"


# =========================================================================== #
# rows_of — the ruled contract: rows_of(result, noun) -> list[dict]
# =========================================================================== #


def _rows_of() -> Any:
    rows_of = getattr(governed_module, "rows_of", None)
    if rows_of is None:
        pytest.fail("am-37 §13 B: governed.rows_of(result, noun) -> list[dict] does not exist")
    return rows_of


_NON_LIST_ANSWERS: dict[str, Any] = {
    "None": None,
    "str": "garbage",
    "dict": {"id": "principal:x"},
    "tuple": ({"id": "principal:x"},),
    "int": 3,
}
_NON_DICT_MEMBERS: dict[str, Any] = {
    "str-member": [{"id": "a"}, "garbage"],
    "None-member": [None, {"id": "a"}],
    "list-member": [{"id": "a"}, [{"id": "b"}]],
    "int-member": [7],
}


class TestRowsOfContract63c13b:
    def test_rows_of_exists_with_the_ruled_signature(self) -> None:
        """⚠ RED at fix5 ``5f2d7c43`` (no ``rows_of``). Parameters ``result`` then ``noun``."""
        parameters = list(inspect.signature(_rows_of()).parameters)
        assert parameters[:2] == ["result", "noun"], parameters

    @pytest.mark.parametrize("shape", sorted(_NON_LIST_ANSWERS))
    def test_a_non_list_answer_raises_the_store_class(self, shape: str) -> None:
        """⚠ RED at fix5 (no ``rows_of``). A non-list never reads as ``[]``: ``SurrealStoreError`` naming the
        noun and the type received."""
        with pytest.raises(SurrealStoreError) as caught:
            _rows_of()(_NON_LIST_ANSWERS[shape], noun="probe-noun-13b")
        text = str(caught.value)
        assert "probe-noun-13b" in text and type(_NON_LIST_ANSWERS[shape]).__name__ in text, text

    @pytest.mark.parametrize("shape", sorted(_NON_DICT_MEMBERS))
    def test_a_non_dict_member_raises_never_a_silent_drop(self, shape: str) -> None:
        """⚠ RED at fix5 (no ``rows_of``). F-7: a non-dict MEMBER raises — the old filter dropped it."""
        with pytest.raises(SurrealStoreError) as caught:
            _rows_of()(_NON_DICT_MEMBERS[shape], noun="probe-noun-13b")
        assert "probe-noun-13b" in str(caught.value), str(caught.value)

    @pytest.mark.parametrize("rows", [[], [{"id": "a"}], [{"id": "a"}, {"id": "b", "count": 2}]])
    def test_a_list_of_dicts_is_returned_whole_and_in_order(self, rows: list[dict[str, Any]]) -> None:
        """CONTROL: a well-shaped answer is returned unchanged (every member, same order)."""
        assert _rows_of()(list(rows), noun="probe-noun-13b") == rows


# =========================================================================== #
# F-6 — _rows_stamped on a malformed UPDATE answer raises the store class, not TypeError
# =========================================================================== #


def _call_rows_stamped(update_result: Any) -> Any:
    """``_rows_stamped`` may gain a ``noun`` (am-37 §13 B: ``len(rows_of(update_result, noun))``) — bind it
    if present, so the pin is about the raised CLASS, not the arity (reading recorded in the report).

    Called through an ``Any`` binding ON PURPOSE (round 5, lead ~17:25Z): the probe must type-check against
    EVERY arity it tolerates, so it never forces production to grow a default just to quiet mypy (the F-16
    smell — a production default justified only by a test)."""
    function: Any = principals._rows_stamped
    if "noun" in inspect.signature(function).parameters:
        return function(update_result, noun="governed backfill probe")
    return function(update_result)


class TestRowsStampedFailsClosed63c13b:
    @pytest.mark.parametrize("shape", sorted(_NON_LIST_ANSWERS))
    def test_F6_a_non_list_update_answer_raises_SurrealStoreError(self, shape: str) -> None:
        """⚠ RED at fix5 (raises ``TypeError`` — the class the CLI does not launder)."""
        with pytest.raises(SurrealStoreError):
            _call_rows_stamped(_NON_LIST_ANSWERS[shape])

    @pytest.mark.parametrize("shape", sorted(_NON_DICT_MEMBERS))
    def test_F6_a_non_dict_member_is_not_counted_as_stamped(self, shape: str) -> None:
        """⚠ RED at fix5 (``len()`` counts the garbage member as a stamped row)."""
        with pytest.raises(SurrealStoreError):
            _call_rows_stamped(_NON_DICT_MEMBERS[shape])

    def test_F6_control_a_row_list_counts_its_rows(self) -> None:
        assert _call_rows_stamped([{"id": "a"}, {"id": "b"}]) == 2
        assert _call_rows_stamped([]) == 0


# =========================================================================== #
# F-7 — _governed_select with a non-dict member raises (no silent drop)
# =========================================================================== #


def _forge_run_query(monkeypatch: pytest.MonkeyPatch, answer: Any) -> dict[str, int]:
    landed = {"count": 0}

    async def forged(**_kwargs: Any) -> Any:
        landed["count"] += 1
        return answer

    monkeypatch.setattr(principals, "run_query", forged)
    return landed


_FAKE_HANDLE: Any = SimpleNamespace(acquire=None, drop=None, url="ws://fake-13b")


class TestGovernedSelectFailsClosed63c13b:
    @pytest.mark.parametrize("shape", sorted(_NON_DICT_MEMBERS))
    async def test_F7_a_non_dict_member_raises(self, monkeypatch: pytest.MonkeyPatch, shape: str) -> None:
        """⚠ RED at fix5 (the filter silently drops the member — a precondition row vanishes)."""
        landed = _forge_run_query(monkeypatch, _NON_DICT_MEMBERS[shape])
        with pytest.raises(SurrealStoreError):
            await principals._governed_select(
                _FAKE_HANDLE,
                noun="governed probe 13b",
                label="probe.rejected",
                statement="SELECT id FROM agent",
            )
        assert landed["count"] == 1, "the forgery never landed (#194)"

    @pytest.mark.parametrize("shape", sorted(_NON_LIST_ANSWERS))
    async def test_F7_a_non_list_answer_raises(self, monkeypatch: pytest.MonkeyPatch, shape: str) -> None:
        """Already GREEN at fix5 (am-28 A2) — kept as the sibling so a rows_of routing cannot regress it."""
        _forge_run_query(monkeypatch, _NON_LIST_ANSWERS[shape])
        with pytest.raises(SurrealStoreError):
            await principals._governed_select(
                _FAKE_HANDLE,
                noun="governed probe 13b",
                label="probe.rejected",
                statement="SELECT id FROM agent",
            )

    async def test_F7_control_a_row_list_is_returned(self, monkeypatch: pytest.MonkeyPatch) -> None:
        rows = [{"id": "a"}, {"id": "b"}]
        _forge_run_query(monkeypatch, rows)
        assert (
            await principals._governed_select(
                _FAKE_HANDLE,
                noun="governed probe 13b",
                label="probe.rejected",
                statement="SELECT id FROM agent",
            )
            == rows
        )


# =========================================================================== #
# PrincipalStore — F-1 (delete's cascaded count) and _as_rows behind revoke / set_* / delete
# =========================================================================== #


def _principal_store() -> PrincipalStore:
    """A store that never connects — every read/write seam below is faked."""
    return PrincipalStore(
        url="ws://127.0.0.1:1", namespace="ns13b", database="db13b", user="u", password=SecretStr("p")
    )


_MALFORMED_COUNTS: dict[str, Any] = {
    "str-count": [{"count": "3"}],
    "missing-count": [{"total": 3}],
    "None-count": [{"count": None}],
    "bool-count": [{"count": True}],
    "non-list": "garbage",
    "dict-answer": {"count": 3},
    "non-dict-row": ["3"],
}


def _wire_delete(monkeypatch: pytest.MonkeyPatch, store: PrincipalStore, count_answer: Any) -> dict[str, int]:
    """Fake every seam ``delete`` touches: the principal exists, keeps nothing, owns no governed row; the
    principal_key count answers ``count_answer``; ``execute_transaction`` is a spy that must stay at 0."""
    calls = {"count_read": 0, "transaction": 0}

    async def get_by_email(_email: str) -> Any:
        return SimpleNamespace(id="principal:abc13b")

    async def table_exists(_table: str) -> bool:
        return False

    async def query(statement: str, _params: dict[str, Any] | None = None) -> Any:
        if "count()" in statement and _PRINCIPALS_NS["PRINCIPAL_KEY_TABLE"] in statement:
            calls["count_read"] += 1
            return count_answer
        return []

    async def transaction(*_args: Any, **_kwargs: Any) -> None:
        calls["transaction"] += 1

    monkeypatch.setattr(store, "get_by_email", get_by_email)
    monkeypatch.setattr(store, "_table_exists", table_exists)
    monkeypatch.setattr(store, "_query", query)
    monkeypatch.setattr(principals, "execute_transaction", transaction)
    return calls


class TestPrincipalDeleteCascadedCount63c13b:
    @pytest.mark.parametrize("shape", sorted(_MALFORMED_COUNTS))
    async def test_F1_a_malformed_count_answer_raises_and_deletes_nothing(
        self, monkeypatch: pytest.MonkeyPatch, shape: str
    ) -> None:
        """⚠ RED at fix5 (``int(count_rows[0].get("count", 0)) if count_rows else 0``: a missing / non-list
        answer serves ``0``, a ``"3"`` serves ``3``, a ``None`` raises ``TypeError``). The count goes through
        ``group_all_count`` → ``SurrealStoreError`` → the delete's wrap → ``PrincipalStoreError``; the
        cascade transaction never runs."""
        store = _principal_store()
        calls = _wire_delete(monkeypatch, store, _MALFORMED_COUNTS[shape])
        with pytest.raises((PrincipalStoreError, SurrealStoreError)) as caught:
            await store.delete(email="x13b@example.com")
        assert calls["count_read"] == 1, "the forgery never landed (#194)"
        assert not isinstance(caught.value, PrincipalNotFoundError), caught.value
        assert calls["transaction"] == 0, "a malformed count answer let the cascade run"

    @pytest.mark.parametrize(("answer", "expected"), [([], 0), ([{"count": 2}], 2)])
    async def test_F1_control_a_well_shaped_count_is_served(
        self, monkeypatch: pytest.MonkeyPatch, answer: Any, expected: int
    ) -> None:
        store = _principal_store()
        calls = _wire_delete(monkeypatch, store, answer)
        assert await store.delete(email="x13b@example.com") == expected
        assert calls["transaction"] == 1


_SETTERS: dict[str, dict[str, Any]] = {
    "set_status(revoke)": {
        "method": "set_status",
        "kwargs": {"status": _PRINCIPALS_NS["_PRINCIPAL_STATUS_SUSPENDED"]},
    },
    "set_subject": {"method": "set_subject", "kwargs": {"subject": "sub-13b"}},
    "set_expires": {"method": "set_expires", "kwargs": {"expires_at": None}},
}
_SETTER_WRONG_SHAPES: dict[str, Any] = {"None": None, "str": "garbage", "dict": {"id": "principal:x"}}


class TestAsRowsNonListIsAStoreFaultNotNotFound63c13b:
    @pytest.mark.parametrize("shape", sorted(_SETTER_WRONG_SHAPES))
    @pytest.mark.parametrize("setter", sorted(_SETTERS))
    async def test_a_non_list_update_answer_is_a_store_fault(
        self, monkeypatch: pytest.MonkeyPatch, setter: str, shape: str
    ) -> None:
        """⚠ RED at fix5 (``_as_rows`` reads a non-list as ``[]`` → ``PrincipalNotFoundError``: a wrong-shaped
        answer AFTER an UPDATE is served as "no such principal"). am-37 §13 B: ``_as_rows`` = ``rows_of``."""
        store = _principal_store()
        landed = {"count": 0}

        async def query(_statement: str, _params: dict[str, Any] | None = None) -> Any:
            landed["count"] += 1
            return _SETTER_WRONG_SHAPES[shape]

        monkeypatch.setattr(store, "_query", query)
        spec = _SETTERS[setter]
        with pytest.raises((PrincipalStoreError, SurrealStoreError)) as caught:
            await getattr(store, spec["method"])(email="x13b@example.com", **spec["kwargs"])
        assert landed["count"] >= 1, "the forgery never landed (#194)"
        assert not isinstance(caught.value, PrincipalNotFoundError), (
            f"{setter}: a {shape} UPDATE answer was served as NotFound — a store fault, am-37 §13 B"
        )

    @pytest.mark.parametrize("setter", sorted(_SETTERS))
    async def test_control_an_empty_list_is_still_not_found(
        self, monkeypatch: pytest.MonkeyPatch, setter: str
    ) -> None:
        """CONTROL: an UPDATE matching nothing (``[]``) is still ``PrincipalNotFoundError``."""
        store = _principal_store()

        async def query(_statement: str, _params: dict[str, Any] | None = None) -> Any:
            return []

        monkeypatch.setattr(store, "_query", query)
        spec = _SETTERS[setter]
        with pytest.raises(PrincipalNotFoundError):
            await getattr(store, spec["method"])(email="x13b@example.com", **spec["kwargs"])

    async def test_delete_a_non_list_keep_read_is_a_store_fault(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at fix5 — the refuse-while-keeping read: a non-list keep answer read as "keeps nothing"
        lets the delete proceed (fail-OPEN on a safety guard)."""
        store = _principal_store()
        calls = _wire_delete(monkeypatch, store, [{"count": 0}])

        async def query(statement: str, _params: dict[str, Any] | None = None) -> Any:
            if _PRINCIPALS_NS["KEEP_TABLE"] in statement and "count()" not in statement:
                return "garbage"
            return [{"count": 0}]

        monkeypatch.setattr(store, "_query", query)
        with pytest.raises((PrincipalStoreError, SurrealStoreError)) as caught:
            await store.delete(email="x13b@example.com")
        assert not isinstance(caught.value, PrincipalNotFoundError), caught.value
        assert calls["transaction"] == 0, "a wrong-shaped keep read let the cascade run"


# =========================================================================== #
# F-5 — a post-commit leftover-read failure names the landed backfill (live TEST store)
# =========================================================================== #

_LEFTOVER_LABEL = "governed.message_leftover.rejected"
_F5_TEXT = "the backfill landed (1 message row(s) stamped) but the leftover count read failed"


class TestMessageLeftoverReadNamesTheLandedWrite63c13b:
    async def test_F5_a_failed_leftover_read_names_the_committed_backfill(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at fix5 (the raw ``SurrealStoreError`` escapes: the operator is told the read failed, never
        that a write LANDED). The leftover read is forged to be REJECTED after it really runs; the verb raises
        ``PrincipalStoreError`` naming the stamped count, chained from the rejection, and the backfill is
        committed."""
        real = vars(principals)["run_query"]
        landed = {"count": 0}

        async def forging(*args: Any, **kwargs: Any) -> Any:
            answer = await real(*args, **kwargs)
            if kwargs.get("label") == _LEFTOVER_LABEL:
                landed["count"] += 1
                raise SurrealStoreError("forged rejection 13b")
            return answer

        async with a19._governed_world() as world:
            await a19._seed_clean_single_principal_store(world)
            monkeypatch.setattr(principals, "run_query", forging)
            with pytest.raises(PrincipalStoreError) as caught:
                await world.migrate(MESSAGE_TABLE)
            assert landed["count"] == 1, "the forgery never landed (#194)"
            assert _F5_TEXT in str(caught.value), str(caught.value)
            assert isinstance(caught.value.__cause__, SurrealStoreError), repr(caught.value.__cause__)
            stamped = await run(
                world.connection, f"SELECT id FROM {MESSAGE_TABLE} WHERE owner_principal != NONE"
            )
            assert len(stamped) == 1, f"the backfill must have committed before the read failed: {stamped!r}"


# =========================================================================== #
# am-37 §13.1 (commit ``d6cdd0b``) — item 1: ``map_of`` (the INFO-map helper), ``_table_exists``'s fail-OPEN
# guard closed; item 2: ``authorize_guarded``'s pre-read routed through ``rows_of``.
# =========================================================================== #


def _map_of() -> Any:
    map_of = getattr(governed_module, "map_of", None)
    if map_of is None:
        pytest.fail("am-37 §13.1: governed.map_of(result, noun) -> dict does not exist")
    return map_of


_NON_DICT_INFO: dict[str, Any] = {"None": None, "list": [{"tables": {}}], "str": "garbage", "int": 3}
_BAD_SUB_MAPS: dict[str, Any] = {
    "tables-list": {"tables": ["memory"]},
    "tables-str": {"tables": "memory"},
    "fields-list": {"fields": ["scope"]},
    "fields-None": {"fields": None},
}


class TestMapOfContract63c13_1:
    def test_map_of_exists_with_the_ruled_signature(self) -> None:
        """⚠ RED at fix5 (no ``map_of``). Parameters ``result`` then ``noun``."""
        parameters = list(inspect.signature(_map_of()).parameters)
        assert parameters[:2] == ["result", "noun"], parameters

    @pytest.mark.parametrize("shape", sorted(_NON_DICT_INFO))
    def test_a_non_dict_info_answer_raises_the_store_class(self, shape: str) -> None:
        """⚠ RED at fix5 (no ``map_of``). A non-dict ``INFO FOR …`` answer never reads as an empty map."""
        with pytest.raises(SurrealStoreError) as caught:
            _map_of()(_NON_DICT_INFO[shape], noun="probe-info-13_1")
        assert "probe-info-13_1" in str(caught.value), str(caught.value)

    @pytest.mark.parametrize("shape", sorted(_BAD_SUB_MAPS))
    def test_a_non_dict_tables_or_fields_sub_map_raises(self, shape: str) -> None:
        """⚠ RED at fix5 (no ``map_of``). §13.1 item 1: a ``tables`` / ``fields`` sub-map non-dict → raise."""
        with pytest.raises(SurrealStoreError):
            _map_of()(_BAD_SUB_MAPS[shape], noun="probe-info-13_1")

    def test_a_well_shaped_info_map_is_returned_whole(self) -> None:
        answer = {"tables": {"memory": "DEFINE TABLE memory"}, "fields": {}, "analyzers": {}}
        assert _map_of()(dict(answer), noun="probe-info-13_1") == answer


def _wire_delete_with_info(
    monkeypatch: pytest.MonkeyPatch, store: PrincipalStore, info: Any
) -> dict[str, int]:
    """Fake ``delete``'s seams so ONLY the ``INFO FOR DB`` answer is malformed: the principal exists, keeps
    nothing, the key count is well-shaped; ``execute_transaction`` is the write spy (must stay 0)."""
    calls = {"info_read": 0, "transaction": 0}

    async def get_by_email(_email: str) -> Any:
        return SimpleNamespace(id="principal:abc13b")

    async def query(statement: str, _params: dict[str, Any] | None = None) -> Any:
        if statement.strip().upper().startswith("INFO FOR DB"):
            calls["info_read"] += 1
            return info
        if "count()" in statement:
            return [{"count": 0}]
        return []

    async def transaction(*_args: Any, **_kwargs: Any) -> None:
        calls["transaction"] += 1

    monkeypatch.setattr(store, "get_by_email", get_by_email)
    monkeypatch.setattr(store, "_query", query)
    monkeypatch.setattr(principals, "execute_transaction", transaction)
    return calls


class TestDeleteNeverSkipsTheOwnedRowGuardOnAGarbageInfoAnswer63c13_1:
    @pytest.mark.parametrize("shape", sorted({**_NON_DICT_INFO, "tables-list": {"tables": ["memory"]}}))
    async def test_a_malformed_info_for_db_answer_raises_and_deletes_nothing(
        self, shape: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at fix5: ``_table_exists`` reads a non-dict ``INFO FOR DB`` as "no tables", so ``delete``
        SKIPS the SF-63-5 owned-row guard and runs the cascade (fail-OPEN). §13.1 item 1: it raises the store
        class and the cascade never runs."""
        answer = {**_NON_DICT_INFO, "tables-list": {"tables": ["memory"]}}[shape]
        store = _principal_store()
        calls = _wire_delete_with_info(monkeypatch, store, answer)
        with pytest.raises((SurrealStoreError, PrincipalStoreError)):
            await store.delete(email="owner@example.com")
        assert calls["info_read"] >= 1, (
            f"the INFO FOR DB read was never reached (the pin proves nothing): {calls}"
        )
        assert calls["transaction"] == 0, f"the cascade ran on a garbage INFO answer (fail-OPEN): {calls}"

    async def test_control_a_well_shaped_info_answer_without_the_table_deletes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """CONTROL: a well-shaped answer with no governed table → the guard legitimately passes, the cascade
        runs once (so the RED above is about the SHAPE, never the harness)."""
        store = _principal_store()
        calls = _wire_delete_with_info(monkeypatch, store, {"tables": {}})
        await store.delete(email="owner@example.com")
        assert calls["transaction"] == 1, calls


class TestAuthorizeGuardedPreReadFailsClosed63c13_1:
    @pytest.mark.parametrize(
        "shape", sorted({**_NON_LIST_ANSWERS, "non-dict-row": ["garbage"], "None-row": [None]})
    )
    async def test_a_wrong_shaped_pre_read_raises_never_absent(
        self, shape: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⚠ RED at fix5: ``authorize_guarded`` coerces a non-list pre-read to ``[]`` and a non-dict row to
        ``{}`` — a wrong-shaped answer DECIDES a governed write as "row absent". §13.1 item 2: it raises."""
        from _governed_contract import admin  # noqa: PLC0415 - scaffold-local
        from loremaster.store._txn import StoreHandle  # noqa: PLC0415

        answer = {**_NON_LIST_ANSWERS, "non-dict-row": ["garbage"], "None-row": [None]}[shape]

        async def _forged_pre_read(**_kwargs: Any) -> Any:
            return answer

        async def _never_acquire() -> Any:
            raise AssertionError("the forged pre-read must be the only store touch")

        async def _never_drop(_connection: Any) -> None:
            return None

        monkeypatch.setattr(governed_module, "run_query", _forged_pre_read)
        handle = StoreHandle(acquire=_never_acquire, drop=_never_drop, url="ws://127.0.0.1:18000/rpc")
        with pytest.raises(SurrealStoreError):
            await governed_module.authorize_guarded(
                admin("alice", "ag_a1"),
                pdp.Action.WRITE,
                table="finding",
                row_id="x",
                audit=object(),
                store=handle,
            )
