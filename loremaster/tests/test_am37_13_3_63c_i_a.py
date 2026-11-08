"""Packet 63c-i-a, amendment 37 §13.3 (commit ``07549f7``) — the FINAL capped round's test side.

Written by ``fixup-tests-63c-i-a-2`` (round 6, 2026-10-01), over the fix6 final build (patch md5
``bec29190``).
Every claim "RED at bec29190" below is scoped to that build. One file, one class per ruled item:

* F-1  — ``_set_columns`` is COMPLETE or RAISES, never a subset (the corpus pin; item 1).
* F-2  — the lore-adm stderr sink routes through ``RedactingFilter``; ``_fault_line`` scrubs every message
through the
         PUBLIC ``logging_setup.scrub_text``; ``scrub_text`` redacts a 128-hex credential-hash run (item 2).
* #527 — ``_fault_line``'s ``__cause__`` walk terminates on a cycle (item 3).
* #528 — ``report_unmigrated_governed_rows`` validates ITS OWN table, zero I/O on a typo (item 4).
* F-3  — every post-write shape read passes ``landed=True``; the ONE landed template (item 5).
* F-5  — the report remedy is DERIVED from membership (item 6).
* F-6  — no shape-reader call without ``noun=`` (item 7).
* F-7  — ``GovernedStatementError`` is OUTSIDE the lore-adm handler tuple; a leg literal the gate cannot read
         TRACEBACKS; a ``ValueError`` still launders (item 8).
* #31  — ``_not_supported``'s table prose is derived (item 9).

No pin here evaluates code from the tree (the am-37 §9 one-resolver law, ``test_retry_seam.py::…am34_5…``):
the
AST helpers read nodes, never ``eval``.
"""

from __future__ import annotations

import ast
import functools
import inspect
import logging
import re
import shlex
import string
import subprocess
import sys
import textwrap
import traceback
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import loremaster.governed as governed_module
import pytest
import test_engine_rejection_seam as seam  # module-qualified: its Test* classes are not re-collected here
import test_preboot_schema_precondition_63c_13d as preboot
import test_principals_cli as cli
import yaml
from _surreal_harness import PRODUCTION_DIM, connect_admin, drop_database, make_env, unique_database
from loremaster.principal_keys import PrincipalKeyStore, PrincipalKeyStoreError
from loremaster.store import _txn as _txn_module
from loremaster.store._txn import (
    SurrealConnectionError,
    SurrealStoreError,
    TxnContentionExhaustedError,
    TxnDomainRejectionError,
    wrap_store_rejection,
)
from loremaster.store.surreal_schema import BRIEF_TABLE
from pydantic import SecretStr
from surrealdb.errors import parse_query_error

from loremaster import logging_setup
from loremaster import principals as p_module

_PACKAGE = Path(p_module.__file__).resolve().parent
_HEX128 = re.compile(r"[0-9a-fA-F]{128}")
_A_HASH = "ab" * 64  # a sha512-hex-shaped credential hash (128 hex characters)
_SHAPE_READERS = frozenset({"rows_of", "_as_rows", "map_of", "group_all_count"})


def _function_nodes(tree: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)]


def _call_name(call: ast.Call) -> str:
    func = call.func
    return func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""


# =========================================================================== #
# F-1 — the corpus pin: COMPLETE or RAISE, never a subset (§13.3 item 1)
# =========================================================================== #

#: ``statement -> the EXACT column set``. The blind-reader-5 cases (``REPORT-blindreader-63c-i-a-5.md``
#: §probe)
#: + the ruled siblings (RETURN inside a call, SET inside a string before the real SET, an unbalanced ``)``
#: in a
#: string, the other end keywords, a double-quoted comma). A corpus is a hand-list — enough here ONLY
#: because the
#: §13.1 one-derivation pin + mutation E exist (§13.3 item 1 (c)).
_COMPLETE_OR_RAISE: dict[str, tuple[str, frozenset[str]]] = {
    "shipped-memory": ("UPDATE memory SET scope = $scope WHERE scope IS NONE", frozenset({"scope"})),
    "shipped-agent": (
        "UPDATE agent SET owner_principal = type::record('principal', $owner), owner_agent = id, "
        "scope = $scope "
        "WHERE scope IS NONE AND owner_principal IS NONE",
        frozenset({"owner_principal", "owner_agent", "scope"}),
    ),
    "shipped-message": (
        "UPDATE message SET owner_agent = sender, owner_principal = sender.owner_principal, scope = $scope "
        "WHERE scope IS NONE AND owner_principal IS NONE AND sender.owner_principal IS NOT NONE",
        frozenset({"owner_agent", "owner_principal", "scope"}),
    ),
    "subquery-WHERE-in-value": (
        "UPDATE brief SET a = 1, owner_principal = (SELECT VALUE x FROM y WHERE z = 1)[0] WHERE "
        "scope IS NONE",
        frozenset({"a", "owner_principal"}),
    ),
    "RETURN-inside-a-call": (
        "UPDATE t SET a = fn::pick( RETURN 1 ), b = 3 WHERE x = 1",
        frozenset({"a", "b"}),
    ),
    "SET-inside-a-string-before-the-real-SET": (
        "UPDATE type::record('t', 'x SET y = 2 ') SET a = 1 WHERE x = 1",
        frozenset({"a"}),
    ),
    "unbalanced-paren-in-a-string": ("UPDATE t SET a = ')', b = 2 WHERE x = 1", frozenset({"a", "b"})),
    "plus-equals": ("UPDATE t SET n += 1 WHERE x = 1", frozenset({"n"})),
    "quoted-comma": ("UPDATE t SET note = 'a, b' WHERE x = 1", frozenset({"note"})),
    "double-quoted-WHERE-and-comma": (
        'UPDATE t SET a = "x, WHERE y", b = 1 WHERE z = 1',
        frozenset({"a", "b"}),
    ),
    "newline-before-WHERE": ("UPDATE t SET a = 1\nWHERE x = 1", frozenset({"a"})),
    "lowercase-where": ("UPDATE t SET a = 1, b = 2 where c = 3", frozenset({"a", "b"})),
    "RETURN-end": ("UPDATE t SET a = 1, b = 2 RETURN AFTER", frozenset({"a", "b"})),
    "TIMEOUT-end": ("UPDATE t SET a = 1 TIMEOUT 5s", frozenset({"a"})),
    "PARALLEL-end": ("UPDATE t SET a = 1, b = 2 PARALLEL", frozenset({"a", "b"})),
}

#: Statements the gate CANNOT read completely — they must RAISE (an open paren, an open quote, a trailing item
#: without ``<col> =``), never return whatever prefix parsed.
_MUST_RAISE: dict[str, str] = {
    "open-paren-at-end": "UPDATE t SET a = (1, b = 2 WHERE x = 1",
    "open-quote-at-end": "UPDATE t SET a = 'x, b = 2 WHERE x = 1",
    "trailing-item-without-equals": "UPDATE t SET a = 1, b WHERE x = 1",
    "no-SET-clause": "UPDATE t CONTENT { a: 1 }",
}


class TestTheSetParserIsCompleteOrRaises:
    """§13.3 item 1. RED at bec29190 on the cases the regex end-split narrows (the subquery's inner
    ``WHERE``, the
    ``RETURN`` inside a call, the ``SET`` inside a string, ``+=``, the double-quoted ``WHERE``) and on the
    must-raise cases it returns a prefix for."""

    @pytest.mark.parametrize("case", sorted(_COMPLETE_OR_RAISE))
    def test_the_parse_is_exact_or_raises_never_a_subset(self, case: str) -> None:
        statement, expected = _COMPLETE_OR_RAISE[case]
        try:
            parsed = p_module._set_columns(statement)  # noqa: SLF001
        except Exception:  # noqa: BLE001 - a RAISE is an allowed fate; a narrowed set is not
            return
        assert frozenset(parsed) == expected, (
            f"{case}: `_set_columns` returned {sorted(parsed)} for {statement!r} — the exact set is "
            f"{sorted(expected)}; a parse that is not COMPLETE must RAISE, never narrow (§13.3 F-1)"
        )
        assert len(parsed) == len(expected), f"{case}: duplicate columns {parsed!r}"

    @pytest.mark.parametrize("case", sorted(_MUST_RAISE))
    def test_an_unreadable_statement_raises(self, case: str) -> None:
        with pytest.raises(Exception) as caught:  # noqa: PT011 - the class is pinned in TestGovernedStatementError
            p_module._set_columns(_MUST_RAISE[case])  # noqa: SLF001
        assert caught.value is not None

    @pytest.mark.parametrize("case", ["shipped-memory", "shipped-agent", "shipped-message"])
    def test_the_shipped_statements_parse_to_their_exact_sets(self, case: str) -> None:
        statement, expected = _COMPLETE_OR_RAISE[case]
        assert frozenset(p_module._set_columns(statement)) == expected  # noqa: SLF001


# =========================================================================== #
# F-2 — the stderr sink is redacted; the scrub learns the credential-hash shape (§13.3 item 2)
# =========================================================================== #


def _public_scrub_text() -> Any:
    scrub = getattr(logging_setup, "scrub_text", None)
    if scrub is None:
        pytest.fail("am-37 §13.3 item 2: `logging_setup.scrub_text` (public) does not exist")
    return scrub


class TestTheCliSinkIsRedacted:
    def test_the_cli_stderr_handler_carries_a_RedactingFilter(self) -> None:
        """RED at bec29190: ``_cli_logging`` installs a bare handler — the ONE redaction seam is bypassed."""
        package_logger = logging.getLogger(p_module._CLI_LOGGER_NAME)  # noqa: SLF001
        with p_module._cli_logging():  # noqa: SLF001
            installed = [h for h in package_logger.handlers if isinstance(h, p_module._CliStderrHandler)]  # noqa: SLF001
            assert len(installed) == 1, installed
            filters = installed[0].filters
        assert any(isinstance(item, logging_setup.RedactingFilter) for item in filters), (
            f"the lore-adm stderr sink must route through RedactingFilter (§13.3 item 2 i): {filters!r}"
        )

    def test_scrub_text_is_public_and_is_the_filters_own_scrub(self) -> None:
        """RED at bec29190 (private ``_scrub_text``). ONE name: the filter calls the public function —
        proven by
        the module source, never a second regex."""
        _public_scrub_text()
        filter_source = inspect.getsource(logging_setup.RedactingFilter)
        assert re.search(r"(?<![\w_])scrub_text\(", filter_source), (
            "RedactingFilter must call the PUBLIC scrub_text (one name, §13.3 item 2 ii)"
        )

    def test_scrub_text_redacts_a_128_hex_run(self) -> None:
        """RED at bec29190. The credential-hash SHAPE (sha512 hex) is redacted wherever it appears."""
        scrubbed = _public_scrub_text()(f"Database index `pk_hash` already contains '{_A_HASH}' (engine)")
        assert not _HEX128.search(scrubbed), f"a 128-hex run survived the scrub: {scrubbed!r}"

    @pytest.mark.parametrize(
        "value",
        ["c" * 64, "d" * 127, "0123456789abcdef", "ulid 01J9ZQ3W7XK4V8N2B5C6D7E8F9"],
        ids=["sha256-hex-64", "hex-127", "hex-16", "ulid"],
    )
    def test_CONTROL_a_non_128_hex_value_is_untouched(self, value: str) -> None:
        text = f"keep {value} as is"
        assert _public_scrub_text()(text) == text, f"the scrub must not touch a non-128-hex value: {value!r}"

    def test_fault_line_scrubs_the_error_and_every_cause(self) -> None:
        """RED at bec29190: ``_fault_line`` renders raw messages."""
        error = PrincipalKeyStoreError(f"could not mint key 'laptop' ({_A_HASH})")
        middle = RuntimeError(f"unique violation on {_A_HASH}")
        middle.__cause__ = RuntimeError(f"engine: index already contains '{_A_HASH}'")
        error.__cause__ = middle
        rendered = p_module._fault_line(error)  # noqa: SLF001
        assert not _HEX128.search(rendered), f"a 128-hex run reached the fault text: {rendered!r}"
        assert rendered.count("\n") == 2, f"every cause line is still printed: {rendered!r}"

    def test_the_stderr_log_record_is_scrubbed_end_to_end(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """RED at bec29190: the seam's ``engine_error`` extra reaches stderr through the bare handler."""
        from loremaster.store import _txn  # noqa: PLC0415

        def fault(_text: str) -> Exception:
            logging.getLogger("loremaster.principal_keys").error(
                "principal_key.query.rejected",
                extra={
                    "url": "ws://unit",
                    "error_class": "unique violation",
                    "engine_error": f"dup {_A_HASH}",
                },
            )
            error = _txn._domain_rejection_error(  # noqa: SLF001
                "unique violation",
                f"SurrealDB principal-key query rejected; {_txn._SERVER_LOG_HINT}",  # noqa: SLF001
            )
            error.__cause__ = RuntimeError(f"dup {_A_HASH}")
            return error

        outcome, _out, err, _calls = cli._run_verb_against("list", fault, tmp_path, monkeypatch, capsys)
        assert outcome == "rc=1", (outcome, err)
        assert "principal_key.query.rejected" in err, f"the record must still reach stderr: {err!r}"
        assert not _HEX128.search(err), f"a 128-hex run reached the operator's stderr: {err!r}"


# =========================================================================== #
# #527 — the cause walk terminates on a cycle (§13.3 item 3)
# =========================================================================== #

_CYCLE_CHILD = textwrap.dedent(
    """
    import resource, sys
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    from loremaster import principals as p
    a, b = RuntimeError("alpha-cause"), RuntimeError("beta-cause")
    a.__cause__, b.__cause__ = b, a
    sys.stdout.write(p._fault_line(a))
    """
)


class TestTheCauseWalkTerminates:
    def test_a_two_cycle_terminates_with_each_message_once(self) -> None:
        """RED at bec29190 (an unbounded walk). Run in a CHILD with a 512 MiB address-space cap and a timeout,
        so the unbounded base build cannot grow inside the pytest worker."""
        try:
            done = subprocess.run(  # noqa: S603 - our own interpreter, a fixed script
                [sys.executable, "-c", _CYCLE_CHILD], capture_output=True, text=True, timeout=20, check=False
            )
        except subprocess.TimeoutExpired:
            pytest.fail("_fault_line did not terminate on a 2-cycle of __cause__ (#527)")
        assert done.returncode == 0, (
            f"the walk did not terminate cleanly: rc={done.returncode} {done.stderr[-500:]}"
        )
        assert done.stdout.count("alpha-cause") == 1 and done.stdout.count("beta-cause") == 1, done.stdout

    def test_CONTROL_a_plain_chain_is_unchanged(self) -> None:
        top = p_module.PrincipalStoreError("top")
        middle = RuntimeError("middle")
        middle.__cause__ = RuntimeError("bottom")
        top.__cause__ = middle
        assert p_module._fault_line(top).splitlines() == [  # noqa: SLF001
            f"{p_module._CLI_PROG}: top",  # noqa: SLF001
            f"{p_module._CAUSE_LINE_PREFIX}middle",  # noqa: SLF001
            f"{p_module._CAUSE_LINE_PREFIX}bottom",  # noqa: SLF001
        ]

    def test_CONTROL_context_is_not_walked(self) -> None:
        """``__cause__`` ONLY (§13.3 item 3): an implicit ``__context__`` link is never rendered."""
        error = p_module.PrincipalStoreError("explicit")
        error.__context__ = RuntimeError("implicit-context-link")
        assert "implicit-context-link" not in p_module._fault_line(error)  # noqa: SLF001


class TestTheFaultLineRendersNotes:
    """am-37 §13.5 item 1 / item 6 (d): after the error's message and BEFORE the cause lines, one `` ↳ `` line
    per ``__notes__`` entry, through the same ``scrub_text`` as every message."""

    def test_each_note_renders_between_the_message_and_the_causes(self) -> None:
        error = p_module.PrincipalStoreError("top")
        error.__cause__ = RuntimeError("bottom")
        error.add_note("first note")
        error.add_note(f"second note {_A_HASH}")
        lines = p_module._fault_line(error).splitlines()  # noqa: SLF001
        assert lines[:3] == [
            f"{p_module._CLI_PROG}: top",  # noqa: SLF001
            " ↳ first note",
            f" ↳ {_public_scrub_text()(f'second note {_A_HASH}')}",
        ], lines
        assert lines[3:] == [f"{p_module._CAUSE_LINE_PREFIX}bottom"], lines  # noqa: SLF001
        assert not _HEX128.search("\n".join(lines)), "a note bypassed the shared scrub"

    def test_CONTROL_an_error_without_notes_renders_no_note_line(self) -> None:
        error = p_module.PrincipalStoreError("top")
        error.__cause__ = RuntimeError("bottom")
        assert p_module._fault_line(error).splitlines() == [  # noqa: SLF001
            f"{p_module._CLI_PROG}: top",  # noqa: SLF001
            f"{p_module._CAUSE_LINE_PREFIX}bottom",  # noqa: SLF001
        ]


# =========================================================================== #
# #528 — the report count validates its own table (§13.3 item 4)
# =========================================================================== #


class TestTheReportCountValidatesItsOwnTable:
    async def test_an_invalid_table_is_refused_by_the_function_itself_with_zero_io(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """RED at bec29190: only the VERB validates; a direct caller interpolates any name."""
        from loremaster.store._txn import StoreHandle  # noqa: PLC0415

        calls: list[str] = []

        async def spy_run_query(**kwargs: Any) -> Any:
            calls.append(str(kwargs.get("statement")))
            return [{"count": 0}]

        async def never_acquire() -> Any:
            calls.append("acquire")
            raise AssertionError("no connection may be opened for an invalid table")

        async def never_drop(_connection: Any) -> None:
            return None

        monkeypatch.setattr(governed_module, "run_query", spy_run_query)
        handle = StoreHandle(acquire=never_acquire, drop=never_drop, url="ws://unit")
        with pytest.raises(Exception) as refused:  # noqa: PT011 - the refusal class is the builder's
            await governed_module.report_unmigrated_governed_rows(handle, "memory; REMOVE TABLE memory")
        assert calls == [], f"an invalid table reached the store: {calls}"
        assert "REMOVE TABLE" in str(refused.value) or "not" in str(refused.value), str(refused.value)


# =========================================================================== #
# F-3 — every post-write shape read passes landed=True; the ONE template (§13.3 item 5)
# =========================================================================== #

#: THE landed text, written OUT (not derived from the template): am-37 §13.5 item 5 deleted the ``{remedy}``
#: slot (fix531d), so the served text must be byte-identical to the pre-#531 default — the remedy moved to
#: ``mint``'s ONE ``add_note`` handler.
_LANDED_TEMPLATE = (
    "the {noun} LANDED (committed) but answered a {type} instead of its rows — nothing was decided from the "
    "answer; verify the stored state before re-running"
)

def _post_write_reads(case: Any, method_name: str) -> list[tuple[int, bool]]:
    """``(lineno, passes_landed_True)`` for every shape-reader call in the boundary whose first argument is
    a name
    bound from a WRITE sink's result (the write sinks are §12's derivation,
    ``test_engine_rejection_seam``)."""
    method = next(
        node
        for node in seam._store_class_node(case).body  # noqa: SLF001
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name == method_name
    )
    write_lines = {line for line, _wrapped in seam._write_sinks(method, case.domain_error.__name__)}  # noqa: SLF001
    bound: set[str] = set()
    for assign in ast.walk(method):
        if isinstance(assign, ast.Assign) and any(
            isinstance(inner, ast.Call) and inner.lineno in write_lines for inner in ast.walk(assign.value)
        ):
            bound |= {target.id for target in assign.targets if isinstance(target, ast.Name)}
    reads: list[tuple[int, bool]] = []
    for call in ast.walk(method):
        if not (isinstance(call, ast.Call) and _call_name(call) in _SHAPE_READERS and call.args):
            continue
        argument = call.args[0]
        reads_a_write = (isinstance(argument, ast.Name) and argument.id in bound) or any(
            isinstance(inner, ast.Call) and inner.lineno in write_lines for inner in ast.walk(argument)
        )
        if reads_a_write:
            landed = any(
                kw.arg == "landed" and isinstance(kw.value, ast.Constant) and kw.value.value is True
                for kw in call.keywords
            )
            reads.append((call.lineno, landed))
    return reads


def _landed_population() -> list[str]:
    """``<label>::<method>`` ∀ store reached by ``_dispatch`` ∀ derived write boundary that shape-reads its
    own
    write result, + ``principals::_rows_stamped`` (the three legs' post-write reader) — DERIVED at
    collection."""
    try:
        stores = seam._dispatch_store_classes()  # noqa: SLF001
        population = [
            f"{case.label}::{method}"
            for case in seam._CASES  # noqa: SLF001
            if case.class_name in stores
            for method in sorted(seam.derived_write_boundaries(case))
            if _post_write_reads(case, method)
        ]
    except Exception as error:  # noqa: BLE001 - a broken derivation must RED, never shrink the population
        population = [f"<the post-write derivation failed: {error!r}>"]
    return [*population, "principals::_rows_stamped"]


def _rows_stamped_passes_landed() -> bool:
    tree = ast.parse(Path(p_module.__file__).read_text(encoding="utf-8"))
    function = next(node for node in _function_nodes(tree) if node.name == "_rows_stamped")
    return any(
        isinstance(call, ast.Call)
        and _call_name(call) in _SHAPE_READERS
        and any(
            kw.arg == "landed" and isinstance(kw.value, ast.Constant) and kw.value.value is True
            for kw in call.keywords
        )
        for call in ast.walk(function)
    )


class TestEveryPostWriteShapeReadSaysItLanded:
    @pytest.mark.parametrize("boundary", _landed_population())
    def test_the_post_write_read_passes_landed_true(self, boundary: str) -> None:
        """RED at bec29190 BY NAME for every boundary (no ``landed`` exists): a fault after a COMMITTED
        write must
        say the write landed, through the ONE template (§13.3 item 5)."""
        if boundary == "principals::_rows_stamped":
            assert _rows_stamped_passes_landed(), "_rows_stamped's rows_of read must pass landed=True"
            return
        label, separator, method = boundary.partition("::")
        assert separator and label in seam._CASES_BY_LABEL, f"population defect: {boundary}"  # noqa: SLF001
        reads = _post_write_reads(seam._CASES_BY_LABEL[label], method)  # noqa: SLF001
        missing = [line for line, landed in reads if not landed]
        assert not missing, f"{boundary}: post-write shape read(s) at line(s) {missing} lack landed=True"

    def test_the_population_is_not_vacuous(self) -> None:
        population = _landed_population()
        assert len(population) >= 4 and all(not item.startswith("<") for item in population), population

    @pytest.mark.parametrize(
        "answer", ["garbage", None, {"id": "x"}, ["row"]], ids=["str", "None", "dict", "non-dict-member"]
    )
    def test_the_one_landed_template(self, answer: Any) -> None:
        """RED at bec29190 (``rows_of`` has no ``landed``). The template is ONE text, byte-exact — and, since
        am-37 §13.5 item 5 (fix531d), byte-identical to the pre-#531 default for EVERY site."""
        kind = type(answer[0] if isinstance(answer, list) else answer).__name__
        with pytest.raises(SurrealStoreError) as caught:
            governed_module.rows_of(answer, noun="probe write", landed=True)
        assert str(caught.value) == _LANDED_TEMPLATE.format(noun="probe write", type=kind)

    def test_the_template_has_no_remedy_slot(self) -> None:
        """am-37 §13.5 item 5 (fix531d; DUAL of fix531b (c)): the remedy lives ONLY in ``mint``'s note, so the
        ONE template carries exactly ``noun`` and ``type`` and its fixed last clause."""
        template = governed_module._LANDED_SHAPE_FAULT  # noqa: SLF001
        fields = [
            field for _literal, field, _spec, _conv in string.Formatter().parse(template) if field is not None
        ]
        assert sorted(fields) == ["noun", "type"], fields
        assert template == _LANDED_TEMPLATE

    @pytest.mark.parametrize(
        ("owner", "attribute"),
        [
            (governed_module, "rows_of"),
            (governed_module, "_shape_fault"),
            (PrincipalKeyStore, "_as_rows"),
        ],
        ids=["rows_of", "_shape_fault", "_as_rows"],
    )
    def test_no_reader_takes_a_remedy_any_more(self, owner: Any, attribute: str) -> None:
        """am-37 §13.5 item 5 (fix531d; DUAL of fix531b's passed-remedy and remedy-without-landed pins): the
        ``remedy=`` machinery is deleted end to end — its only non-default user (``mint``) moved to the note,
        so a surviving parameter would be dead."""
        assert "remedy" not in inspect.signature(getattr(owner, attribute)).parameters
        assert not hasattr(governed_module, "_LANDED_DEFAULT_REMEDY")

    def test_CONTROL_the_unlanded_read_keeps_its_own_text(self) -> None:
        with pytest.raises(Exception) as caught:  # noqa: PT011
            governed_module.rows_of("garbage", noun="probe read")
        assert "LANDED" not in str(caught.value), str(caught.value)


# --------------------------------------------------------------------------- #
# am-37 §13.5 (fix531d, #531) — ONE add_note handler over mint's post-CREATE window
# --------------------------------------------------------------------------- #

_PLAIN = ("ops531@example.com", "laptop")
_NEEDS_QUOTING = ("dev.531+keys@example.org", "work laptop")


def _certain_note(email: str, name: str) -> str:
    """§13.5 item 5's CERTAIN wording, written OUT (the revoke command shell-quoted as the CLI parses it)."""
    command = shlex.join(["lore-adm", "revoke-key", "--email", email, "--name", name])
    return (
        f"the CREATE committed but the secret was never shown — key {name!r} is LIVE with no holder; "
        f"revoke it (`{command}`) and mint a new key"
    )


def _conditional_note(email: str, name: str) -> str:
    """§13.5 item 5's CONDITIONAL wording, written OUT."""
    command = shlex.join(["lore-adm", "revoke-key", "--email", email, "--name", name])
    listing = shlex.join(["lore-adm", "list-keys", "--email", email])
    return (
        "the mint's outcome is unknown (the connection failed during the CREATE) — if "
        f"`{listing}` shows {name!r}, revoke it (`{command}`) and mint a new key"
    )


def _rendered(error: BaseException) -> str:
    """Everything lore-adm can print for ``error``: its ``_fault_line`` AND the full traceback (notes and
    every chained link included)."""
    return p_module._fault_line(error) + "\n" + "".join(traceback.format_exception(error))  # noqa: SLF001


def _store_taxonomy() -> list[type[BaseException]]:
    """GENERATED: every PROPER subclass of ``SurrealStoreError`` that the store taxonomy
    (``loremaster.store._txn``) defines, walked transitively from the base — never a hand-list.

    am-37 §14 Q1 re-key (DUAL, operator-ruled 2026-10-04): the bare BASE is no longer in this domain. A bare
    ``SurrealStoreError`` proves nothing about the CREATE's outcome, and it cannot sit in an ``isinstance``
    proven-set: ``SurrealConnectionError`` subclasses it. It moved to the unknown-outcome cells
    (``test_mint_unknown_outcome_note_q1.py``). The filter is the DEFINING module, so the walk does not
    depend on which other ``loremaster`` modules this worker happened to import. Foreign subclasses
    (``store.lease``, ``store.surreal``, ``floor_calibration``) appear only when their module is loaded."""
    found: set[type[BaseException]] = set()
    pending = list(SurrealStoreError.__subclasses__())
    while pending:
        cls = pending.pop()
        pending.extend(cls.__subclasses__())
        if cls.__module__ == _txn_module.__name__:
            found.add(cls)
    return sorted(found, key=lambda cls: cls.__qualname__)


#: am-37 §14 Q1 (operator-ruled "Yes, separate cycle", 2026-10-04): the store faults that PROVE no key landed.
#: They are the driver's own refusals and pre-send faults, WRITTEN OUT from the ruling. This is the contract's
#: independent adjudication, never production's set used AS the expected value. §14:
#: "TxnDomainRejectionError (+ subclasses, UNIQUE included), TxnContentionExhaustedError (rolled back),
#: TxnParamCollisionError, TxnEnvelopeViolationError". am-37 §15 re-key (contract-mint-q1b, 2026-10-05): the
#: ``TxnDomainRejectionError`` family is proven only when TYPED with a proven engine kind (kind-less, or an
#: outcome-unknown kind, is UNKNOWN), so its cells inject ``_typed_proven_instance``; the per-kind and
#: kind-less fates are pinned in ``test_mint_kind_carveout_q1b.py``.
_RULED_PROVEN_NO_KEY: frozenset[str] = frozenset(
    {
        "TxnDomainRejectionError",
        "TxnGovernedConflictError",
        "TxnUniqueViolationError",
        "TxnContentionExhaustedError",
        "TxnParamCollisionError",
        "TxnEnvelopeViolationError",
        # SDK3 round 6 (R15, MP-C 3e): R3/R4/F12's row cap — ``compose`` refuses an over-cap transaction at
        # BUILD time, "before anything was sent to the server": a driver refusal, the §14 proven-no-key kind.
        "TxnRowCapExceededError",
    }
)
#: §14 Q1: the store layer's unknown-outcome classes (the engine may have committed and the answer been
#: lost). SDK3 round 6 (R15, MP-C 3e) adds ``SurrealOutcomeUnknownError`` — F14 / R5 rider 2 / R9 D1: a
#: request was SENT and no reply came back, so the commit may have landed (it subclasses
#: ``SurrealConnectionError``, the original §14 unknown-outcome class).
_RULED_UNKNOWN_OUTCOME_STORE: frozenset[str] = frozenset(
    {"SurrealConnectionError", "SurrealOutcomeUnknownError"}
)


def _instance(cls: type[BaseException]) -> BaseException:
    if issubclass(cls, TxnContentionExhaustedError):
        return cls("injected 531d", attempts=3, elapsed_seconds=0.1)
    return cls("injected 531d")


async def _through_the_seam(sdk_error: BaseException) -> BaseException:
    """What the driver's ONE failure ladder (``_txn._raise_attempt_failure``, the single-statement path
    ``PrincipalKeyStore._query`` rides) raises for a REAL SDK error (am-37 §15, contract-mint-q1b)."""
    dropped: list[object] = []

    async def drop(connection: object) -> None:
        dropped.append(connection)

    try:
        await _txn_module._raise_attempt_failure(  # noqa: SLF001
            sdk_error,
            object(),
            drop=drop,
            url="ws://127.0.0.1:1/rpc",
            noun="principal key query",
            label="principal.key.query.rejected",
            logger=logging.getLogger("test.531d.seam"),
        )
    except BaseException as raised:  # noqa: BLE001 - the ladder's raise IS the observation
        return raised
    raise AssertionError("unreachable: the failure ladder returned")  # pragma: no cover


#: am-37 §15: per kind-decided class, the REAL SDK error the seam classifies into that class with a PROVEN
#: kind: ``Validation`` (refused at evaluation), ``Thrown`` carrying OUR governed prefix (the guard aborts
#: the txn), ``AlreadyExists`` naming the record (UNIQUE, typed). Parsed by the SDK's own parser.
_GOVERNED_THROW = f"An error occurred: {_txn_module._GOVERNED_CONFLICT_MARKER} principal_key:k531d"  # noqa: SLF001
_TYPED_PROVEN_SDK_ERROR: dict[str, dict[str, Any]] = {
    "TxnDomainRejectionError": {"kind": "Validation", "result": "Parse error: injected 531d"},
    "TxnGovernedConflictError": {"kind": "Thrown", "result": _GOVERNED_THROW},
    "TxnUniqueViolationError": {
        "kind": "AlreadyExists",
        "result": "Database record `principal_key:k531d` already exists",
        "details": {"kind": "Record", "details": {"id": "principal_key:k531d"}},
    },
}


async def _typed_proven_instance(cls: type[BaseException]) -> BaseException:
    """A PROVEN instance of ``cls``: through the real seam for the kind-decided ``TxnDomainRejectionError``
    family (asserted to land on ``cls`` exactly), the plain constructor for every other class."""
    if not issubclass(cls, TxnDomainRejectionError):
        return _instance(cls)
    raised = await _through_the_seam(parse_query_error(_TYPED_PROVEN_SDK_ERROR[cls.__name__]))
    assert type(raised) is cls, (cls, type(raised))
    return raised


def _through_the_wrap(error: BaseException) -> BaseException:
    """The ORACLE for "class unchanged": what ``wrap_store_rejection`` alone serves for ``error`` today."""
    try:
        with wrap_store_rejection(PrincipalKeyStoreError, "oracle"):
            raise error
    except BaseException as served:  # noqa: BLE001 - the oracle observes whatever the wrap serves
        return served
    raise AssertionError("unreachable: the wrap swallowed")  # pragma: no cover


#: The pre-commit STORE domain: the generated ``_txn`` taxonomy. am-37 §14 Q1 DUAL re-key: fix531d listed
#: ``RuntimeError`` and ``asyncio.CancelledError`` here as "no note" controls, and the bare base too. Under
#: §14 all three are UNKNOWN-outcome faults, so they get the CONDITIONAL note. They moved to
#: ``test_mint_unknown_outcome_note_q1.py`` (its own file so its pending-build reds are owned narrowly).
_PRE_COMMIT_CLASSES: list[type[BaseException]] = _store_taxonomy()


def _note_free_chain(error: BaseException) -> None:
    """No link of ``error``'s ``__cause__`` chain carries a note — a proven fault must carry no revoke
    advice anywhere lore-adm renders it (``_fault_line`` walks causes; the traceback prints every link)."""
    link: BaseException | None = error
    seen: set[int] = set()
    while link is not None and id(link) not in seen:
        seen.add(id(link))
        assert not getattr(link, "__notes__", None), (type(link).__name__, link.__notes__)
        link = link.__cause__


def _full_row(name: str) -> dict[str, Any]:
    return {
        "id": "principal_key:k531d",
        "principal": "principal:abc531d",
        "name": name,
        "created_at": datetime.now(UTC),
    }


class TestTheMintWindowNotesTheRevokeRepair:
    """am-37 §13.5 items 1-5, pinned by item 6 (a): ∀ raise point × zone. A fault raised once the CREATE
    MAY have committed carries the revoke repair as a PEP 678 note on the SAME object — CERTAIN after the
    engine answered, CONDITIONAL for a transport fault during the CREATE; every other pre-commit fault
    carries none."""

    @staticmethod
    def _store(
        monkeypatch: pytest.MonkeyPatch, *, answer: Any = None, raises: BaseException | None = None
    ) -> tuple[PrincipalKeyStore, dict[str, int]]:
        """A store whose mint CREATE is reached (counted, #194) and answers ``answer`` / raises ``raises``."""
        store = PrincipalKeyStore(
            url="ws://127.0.0.1:1", namespace="ns531d", database="db531d", user="u", password=SecretStr("p")
        )
        reached = {"count": 0}

        async def require_principal_id(_email: str) -> str:
            return "abc531d"

        async def query(statement: str, _params: dict[str, Any] | None = None) -> Any:
            assert statement.startswith("CREATE "), statement
            reached["count"] += 1
            if raises is not None:
                raise raises
            return answer

        monkeypatch.setattr(store, "_require_principal_id", require_principal_id)
        monkeypatch.setattr(store, "_query", query)
        return store, reached

    def test_the_generated_pre_commit_domain_is_not_vacuous(self) -> None:
        names = {cls.__name__ for cls in _PRE_COMMIT_CLASSES}
        assert {
            "SurrealConnectionError",
            "TxnDomainRejectionError",
            "TxnUniqueViolationError",
            "TxnContentionExhaustedError",
            "TxnParamCollisionError",
            "TxnEnvelopeViolationError",
        } <= names, names
        assert "SurrealStoreError" not in names, "the bare base proves nothing; it is an unknown-outcome cell"

    def test_every_generated_store_class_is_adjudicated_by_the_ruling(self) -> None:
        """am-37 §14 Q1 completeness, CONTRACT side: every class the derived walk finds is ruled exactly once,
        proven-no-key or unknown-outcome. A new ``_txn`` subclass nobody ruled reds HERE, BY NAME. The fix is
        a ruling plus one line in ``_RULED_PROVEN_NO_KEY`` / ``_RULED_UNKNOWN_OUTCOME_STORE``, never a
        default."""
        derived = {cls.__name__ for cls in _PRE_COMMIT_CLASSES}
        assert not (_RULED_PROVEN_NO_KEY & _RULED_UNKNOWN_OUTCOME_STORE)
        unruled = derived - _RULED_PROVEN_NO_KEY - _RULED_UNKNOWN_OUTCOME_STORE
        assert not unruled, f"store fault class(es) nobody adjudicated (am-37 §14 Q1): {sorted(unruled)}"
        retired = (_RULED_PROVEN_NO_KEY | _RULED_UNKNOWN_OUTCOME_STORE) - derived
        assert not retired, f"ruled class(es) the taxonomy no longer defines: {sorted(retired)}"

    @pytest.mark.parametrize("cls", _PRE_COMMIT_CLASSES, ids=lambda cls: cls.__name__)
    @pytest.mark.parametrize(("email", "name"), [_PLAIN, _NEEDS_QUOTING], ids=["plain", "needs-quoting"])
    async def test_a_fault_during_the_CREATE_call(
        self, monkeypatch: pytest.MonkeyPatch, cls: type[BaseException], email: str, name: str
    ) -> None:
        """GENERATED ∀ ``_txn`` store class (am-37 §14 Q1, which inverts §13.5 item 1's domain).

        A class the ruling marks PROVEN-no-key carries NO note anywhere on its chain. That holds even though
        the wrap TRANSLATES most of them into ``PrincipalKeyStoreError`` before the handler sees them: the
        UNIQUE rejection is exactly that shape. The unknown-outcome store class carries the CONDITIONAL note,
        on the SAME object. Either way the served class is exactly what the wrap alone serves today."""
        if cls.__name__ not in _RULED_PROVEN_NO_KEY | _RULED_UNKNOWN_OUTCOME_STORE:
            pytest.fail(f"{cls.__name__} is not adjudicated (am-37 §14 Q1) — rule it before pinning its fate")
        injected = await _typed_proven_instance(cls)  # am-37 §15: the family is proven only when TYPED
        expected_type = type(_through_the_wrap(await _typed_proven_instance(cls)))
        store, reached = self._store(monkeypatch, raises=injected)
        with pytest.raises(BaseException) as caught:  # noqa: PT011 - the class IS the assertion below
            await store.mint(email=email, name=name, secret_hash="0" * 128)
        assert reached["count"] == 1, "the CREATE was never reached (#194)"
        served = caught.value
        assert type(served) is expected_type, (type(served), expected_type)
        if cls.__name__ in _RULED_UNKNOWN_OUTCOME_STORE:
            assert served is injected, "a transport fault must re-raise as the SAME object"
            assert served.__notes__ == [_conditional_note(email, name)]
            self._assert_commands_parse(served.__notes__[0], email=email, name=name)
        else:
            _note_free_chain(served)
            assert "revoke-key" not in _rendered(served), _rendered(served)
            assert "list-keys" not in _rendered(served), _rendered(served)

    @pytest.mark.parametrize(
        ("answer", "raised"),
        [
            ("garbage", SurrealStoreError),
            (None, SurrealStoreError),
            ({"id": "principal_key:x"}, SurrealStoreError),
            (["row"], SurrealStoreError),
            ([], PrincipalKeyStoreError),
        ],
        ids=["str", "None", "dict", "non-dict-member", "no-row"],
    )
    @pytest.mark.parametrize(("email", "name"), [_PLAIN, _NEEDS_QUOTING], ids=["plain", "needs-quoting"])
    async def test_a_fault_after_the_engine_answered_shape(
        self, monkeypatch: pytest.MonkeyPatch, answer: Any, raised: type[Exception], email: str, name: str
    ) -> None:
        """Post-commit: every shape fault keeps its class and message and carries the CERTAIN note."""
        store, reached = self._store(monkeypatch, answer=answer)
        with pytest.raises(raised) as caught:
            await store.mint(email=email, name=name, secret_hash="0" * 128)
        assert reached["count"] == 1, "the forged CREATE answer never landed (#194)"
        served = caught.value
        assert type(served) is raised
        assert served.__notes__ == [_certain_note(email, name)]
        if answer == []:
            assert str(served) == f"key {name!r} for principal {email!r}: the mint answered no row"
        else:
            assert "principal-key mint LANDED" in str(served)
            assert "revoke-key" not in str(served), "the remedy lives in the note, never the message"
        self._assert_commands_parse(served.__notes__[0], email=email, name=name)

    @pytest.mark.parametrize("column", sorted(_full_row("x")), ids=str)
    async def test_a_row_missing_a_required_column(
        self, monkeypatch: pytest.MonkeyPatch, column: str
    ) -> None:
        """GENERATED over the row ``_row_to_key`` reads: each missing column keeps its class (``KeyError``
        for a subscripted one — §13.3 F-7: our bug stays a bug; a missing STAMP is the shared stamp
        validator's ``SurrealStoreError`` naming the row — packet 66 R34 / RULING-11 rider 3, F1) and carries
        the CERTAIN note, which the traceback renderer prints."""
        email, name = _PLAIN
        row = _full_row(name)
        del row[column]
        store, _reached = self._store(monkeypatch, answer=[row])
        with pytest.raises(Exception) as caught:  # noqa: PT011 - the class IS the assertion below
            await store.mint(email=email, name=name, secret_hash="0" * 128)
        served = caught.value
        expected = SurrealStoreError if column == "created_at" else KeyError
        assert type(served) is expected, type(served)
        assert served.__notes__ == [_certain_note(email, name)]
        assert _certain_note(email, name) in "".join(traceback.format_exception(served))

    async def test_a_programming_defect_after_the_answer(self, monkeypatch: pytest.MonkeyPatch) -> None:
        email, name = _PLAIN
        store, _reached = self._store(monkeypatch, answer=[_full_row(name)])

        def broken(_row: dict[str, Any]) -> Any:
            raise TypeError("injected 531d defect")

        monkeypatch.setattr(store, "_row_to_key", broken)
        with pytest.raises(TypeError) as caught:
            await store.mint(email=email, name=name, secret_hash="0" * 128)
        assert caught.value.__notes__ == [_certain_note(email, name)]

    async def test_CONTROL_a_clean_mint_carries_no_note(self, monkeypatch: pytest.MonkeyPatch) -> None:
        email, name = _PLAIN
        store, _reached = self._store(monkeypatch, answer=[_full_row(name)])
        key = await store.mint(email=email, name=name, secret_hash="0" * 128)
        assert key.name == name

    async def test_the_note_takes_its_revoke_command_from_the_one_helper(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ONE IMPLEMENTATION, proven by MUTATION: replace ``_revoke_command`` and BOTH wordings serve it."""
        sentinel = "SENTINEL-531d revoke command"
        monkeypatch.setattr(PrincipalKeyStore, "_revoke_command", staticmethod(lambda **_kw: sentinel))
        for kwargs in ({"answer": "garbage"}, {"raises": SurrealConnectionError("injected 531d")}):
            store, _reached = self._store(monkeypatch, **kwargs)
            with pytest.raises(SurrealStoreError) as caught:
                await store.mint(email="ops531@example.com", name="laptop", secret_hash="0" * 128)
            (note,) = caught.value.__notes__
            assert f"`{sentinel}`" in note and "revoke-key" not in note, note

    @staticmethod
    def _assert_commands_parse(note: str, *, email: str, name: str) -> None:
        """Every backticked command in the note is one the REAL lore-adm parser runs for THIS key."""
        parser = p_module.build_parser()
        commands = [shlex.split(text) for text in note.split("`")[1::2]]
        assert commands, note
        for argv in commands:
            assert argv[0] == parser.prog, argv
            parsed = vars(parser.parse_args(argv[1:]))
            assert parsed["email"] == email, parsed
            assert parsed["command"] in {"revoke-key", "list-keys"}, parsed
            if parsed["command"] == "revoke-key":
                assert parsed["name"] == name, parsed


class TestALiveUniqueCollisionCarriesNoRevokeAdvice:
    """am-37 §13.5 item 2 / item 6 (b): a UNIQUE rejection proves no key landed, so — live, on a minted
    ``:18000`` database — the served fault is ``PrincipalKeyStoreError`` with NO note and no ``revoke-key``
    anywhere lore-adm could print it (its ``_fault_line`` and the full traceback)."""

    async def test_a_duplicate_name_mint(self) -> None:
        env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
        setup = await connect_admin(env)
        await setup.close()
        principal_store = p_module.PrincipalStore(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        key_store = PrincipalKeyStore(
            url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
        )
        try:
            await principal_store.ensure_ready()
            await key_store.ensure_ready()
            await principal_store.create(email="live531d@example.com")
            first = await key_store.mint(email="live531d@example.com", name="laptop", secret_hash="1" * 128)
            assert first.name == "laptop"  # the positive control: the first mint landed
            with pytest.raises(PrincipalKeyStoreError) as caught:
                await key_store.mint(email="live531d@example.com", name="laptop", secret_hash="2" * 128)
        finally:
            await key_store.close()
            await principal_store.close()
            await drop_database(env)
        served = caught.value
        assert type(served) is PrincipalKeyStoreError
        assert isinstance(served.__cause__, TxnDomainRejectionError), repr(served.__cause__)
        link: BaseException | None = served
        while link is not None:
            assert not getattr(link, "__notes__", None), (link, link.__notes__)
            link = link.__cause__
        assert "revoke-key" not in _rendered(served), _rendered(served)


class TestTheMintHasOneNoteHandlerOverTheWholeWindow:
    """am-37 §13.5 item 6 (c): exactly ONE handler in ``mint`` calls ``add_note``; it is a bare passthrough
    of ``BaseException``; its ``try`` opens AT the CREATE ``_query`` call and ends at the ``return`` — no
    statement of ``mint`` lies after the ``try`` (the window-completeness leg)."""

    @staticmethod
    def _mint_node() -> ast.AsyncFunctionDef:
        tree = ast.parse(textwrap.dedent(inspect.getsource(PrincipalKeyStore.mint)))
        node = tree.body[0]
        assert isinstance(node, ast.AsyncFunctionDef), node
        return node

    @staticmethod
    def _queries(node: ast.AST) -> list[ast.Call]:
        return [
            call
            for call in ast.walk(node)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "_query"
        ]

    def test_one_add_note_handler(self) -> None:
        mint = self._mint_node()
        noting = [
            handler
            for handler in ast.walk(mint)
            if isinstance(handler, ast.ExceptHandler)
            and any(
                isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                and call.func.attr == "add_note"
                for call in ast.walk(handler)
            )
        ]
        assert len(noting) == 1, [ast.unparse(handler)[:80] for handler in noting]
        (handler,) = noting
        assert isinstance(handler.type, ast.Name) and handler.type.id == "BaseException", ast.unparse(handler)
        last = handler.body[-1]
        assert isinstance(last, ast.Raise) and last.exc is None and last.cause is None, ast.unparse(last)
        exits = [node for node in ast.walk(handler) if isinstance(node, ast.Raise | ast.Return)]
        assert exits == [last], "the handler's ONLY exit is the bare re-raise (a passthrough)"

    def test_the_window_spans_the_CREATE_call_to_the_return(self) -> None:
        mint = self._mint_node()
        assert isinstance(mint.body[-1], ast.Try), "no statement of mint may lie after the window's try"
        window = mint.body[-1]
        assert len(window.handlers) == 1, ast.unparse(window)[:200]
        assert not window.orelse and not window.finalbody, ast.unparse(window)[:200]
        before = ast.Module(body=mint.body[:-1], type_ignores=[])
        assert not self._queries(before), "the CREATE _query call lies OUTSIDE (before) the window"
        assert len(self._queries(ast.Module(body=window.body[:1], type_ignores=[]))) == 1, (
            "the window must OPEN at the CREATE _query call"
        )
        assert isinstance(window.body[-1], ast.Return), "the window must END at the return"


# =========================================================================== #
# F-5 — the report remedy is derived from membership (§13.3 item 6)
# =========================================================================== #


def _migrated_tables() -> frozenset[str]:
    """The tables ``migrate-governed`` actually MIGRATES — the derived legs "
    "(``test_preboot…::_leg_statements``)."""
    return frozenset(preboot._LEGS)  # noqa: SLF001


def _report_domain() -> list[str]:
    """The tables the REPORT validator accepts — ``governed.governed_tables()`` (am-37 §13.4 / §13.4.1: the
    REPORT domain is the governed set, wider than the MIGRATE leg set), derived at COLLECTION. A missing
    accessor reds BY NAME (round 7 re-key: this pin was parametrized over the MIGRATE set, so it could not see
    the wider domain it is written over)."""
    accessor = getattr(governed_module, "governed_tables", None)
    if accessor is None:
        return ["<governed.governed_tables() does not exist>"]
    return sorted(accessor())


class TestTheReportRemedyIsDerived:
    @pytest.mark.parametrize("table", _report_domain())
    async def test_the_remedy_names_a_migrating_verb_or_none(
        self, table: str, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """RED at bec29190 on ``brief``: the remedy says "run `lore-adm migrate-governed --table brief`",
        which the
        verb REFUSES as not-yet-migrated. Reading (recorded in the report): "a table the MIGRATE verb
        accepts" =
        a table with a derived migrate LEG, not mere membership of the validator set (``brief`` is in it)."""
        assert not table.startswith("<"), table
        from loremaster.store._txn import StoreHandle  # noqa: PLC0415

        async def three_rows(**_kwargs: Any) -> Any:
            return [{"count": 3}]

        async def no_connection() -> Any:
            return None

        async def no_drop(_connection: Any) -> None:
            return None

        monkeypatch.setattr(governed_module, "run_query", three_rows)
        handle = StoreHandle(acquire=no_connection, drop=no_drop, url="ws://unit")
        with caplog.at_level(logging.WARNING, logger=governed_module.__name__):
            assert await governed_module.report_unmigrated_governed_rows(handle, table) == 3
        rendered = " ".join(record.getMessage() for record in caplog.records)
        named = set(re.findall(r"migrate-governed --table (\w+)", rendered))
        assert named <= _migrated_tables(), (
            f"{table}: the remedy names `migrate-governed --table {sorted(named)}`, which does not "
            f"migrate it "
            f"(migrating legs: {sorted(_migrated_tables())}); rendered={rendered!r}"
        )
        pending = getattr(governed_module, "PENDING_GOVERNED_TABLES", {})
        if table in pending:
            # §13.4.2 rider: a PENDING member names its owning PACKET (derived from its entry), never a verb
            assert not named, f"{table}: a pending table was pointed at `migrate-governed`: {rendered!r}"
            assert "no governed columns yet" in rendered, f"{table}: pending remedy missing: {rendered!r}"
            packet = f"packet {pending[table].owning_packet}"
            assert packet in rendered, f"{table}: the remedy does not name `{packet}`: {rendered!r}"
        else:
            assert named or "no migrate verb accepts" in rendered, (
                f"{table}: no remedy was rendered: {rendered!r}"
            )


# =========================================================================== #
# F-6 — every shape-reader call names its read (§13.3 item 7)
# =========================================================================== #


@functools.cache
def _package_trees() -> dict[str, ast.Module]:
    """``{path relative to the loremaster package: ast.Module}`` for every ``*.py`` under
    ``_PACKAGE`` — the F-6 scan domain, parsed through the ONE shared tree parser
    (``_logging_fixtures.parse_production_trees``; lore #536, CLAUDE.md ONE IMPLEMENTATION)
    rather than a private ``rglob`` + ``ast.parse`` clone.

    The domain is unchanged from the hand-rolled scan it replaces: the shared parser's keys are
    repo-relative, so they are narrowed to the ``_PACKAGE`` prefix and re-keyed relative to it.
    REACH IS CHECKED, not assumed: the narrowed key set must equal the ``*.py`` files actually
    on disk under ``_PACKAGE`` (a path listing, no parse), so a shared parser that stopped
    reaching this package reds here instead of shrinking every F-6 pin to a vacuous pass.
    Cached: the trees are read-only to every consumer, and ``_SITES`` is built at import."""
    from _logging_fixtures import parse_production_trees  # noqa: PLC0415 - house lazy-import idiom

    repo_root = _PACKAGE.parent.parent
    prefix = f"{_PACKAGE.relative_to(repo_root).as_posix()}/"
    trees = {
        key.removeprefix(prefix): tree
        for key, tree in sorted(parse_production_trees(include_scripts=False).items())
        if key.startswith(prefix)
    }
    on_disk = {path.relative_to(_PACKAGE).as_posix() for path in _PACKAGE.rglob("*.py")}
    assert on_disk and set(trees) == on_disk, (
        "the shared parser's reach diverged from the loremaster package on disk "
        f"(missing: {sorted(on_disk - set(trees))}, extra: {sorted(set(trees) - on_disk)})"
    )
    return trees


def _row_reader_wrappers(tree: ast.Module) -> set[str]:
    """``_as_rows`` defs that delegate to ``rows_of`` — the wrappers in the ruled domain (derived)."""
    return {
        node.name
        for node in _function_nodes(tree)
        if node.name == "_as_rows"
        and any(isinstance(call, ast.Call) and _call_name(call) == "rows_of" for call in ast.walk(node))
    }


def _row_reader_owner_classes() -> set[str]:
    """Classes whose ``_as_rows`` delegates to ``rows_of`` (package-wide, derived): a call
    ``<Owner>._as_rows(...)`` in ANY module is in the ruled domain (``keeps.py`` calls
    ``PrincipalStore._as_rows``)."""
    owners: set[str] = set()
    for tree in _package_trees().values():
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and any(
                isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
                and item.name == "_as_rows"
                and any(isinstance(c, ast.Call) and _call_name(c) == "rows_of" for c in ast.walk(item))
                for item in node.body
            ):
                owners.add(node.name)
    return owners


def _shape_reader_call_sites() -> list[tuple[str, bool]]:
    """``(<file>::<function>::<line>, has noun=)`` ∀ call to ``rows_of`` / ``map_of`` / ``group_all_count``
    in the
    package, + ∀ call to a ``_as_rows`` in a module whose ``_as_rows`` delegates to ``rows_of``."""
    sites: list[tuple[str, bool]] = []
    owners = _row_reader_owner_classes()
    for relative, tree in _package_trees().items():
        readers = {"rows_of", "map_of", "group_all_count"} | _row_reader_wrappers(tree)
        for function in _function_nodes(tree):
            for call in ast.walk(function):
                if not isinstance(call, ast.Call) or function.name == _call_name(call):
                    continue
                owner_call = (
                    _call_name(call) == "_as_rows"
                    and isinstance(call.func, ast.Attribute)
                    and isinstance(call.func.value, ast.Name)
                    and call.func.value.id in owners
                )
                if _call_name(call) in readers or owner_call:
                    has_noun = any(kw.arg == "noun" for kw in call.keywords)
                    sites.append((f"{relative}::{function.name}::{call.lineno}", has_noun))
    return sites


_SITES = dict(_shape_reader_call_sites())


class TestEveryShapeReadNamesItsRead:
    @pytest.mark.parametrize("site", sorted(_SITES))
    def test_the_call_passes_noun(self, site: str) -> None:
        """RED at bec29190 by site for every ``_as_rows`` call relying on a default noun / having none."""
        assert _SITES[site], f"{site}: a shape read without `noun=` (§13.3 item 7)"

    def test_the_row_reader_wrappers_require_noun(self) -> None:
        """RED at bec29190: ``PrincipalStore._as_rows`` defaults ``noun``; "
        "``PrincipalKeyStore._as_rows`` has none."""
        problems: list[str] = []
        for relative, tree in _package_trees().items():
            for node in _function_nodes(tree):
                if node.name in _row_reader_wrappers(tree):
                    kwonly = {
                        arg.arg: default
                        for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True)
                    }
                    if "noun" not in kwonly or kwonly["noun"] is not None:
                        problems.append(f"{relative}::{node.name}")
        assert not problems, f"`noun` must be keyword-only and REQUIRED on: {problems}"

    def test_the_site_population_is_not_vacuous(self) -> None:
        assert len(_SITES) >= 10, sorted(_SITES)


# =========================================================================== #
# F-7 — the defect class is OUTSIDE the lore-adm handler tuple (§13.3 item 8)
# =========================================================================== #


def _governed_statement_error() -> type[Exception]:
    error_class = getattr(p_module, "GovernedStatementError", None)
    if error_class is None:
        pytest.fail("am-37 §13.3 item 8: principals.GovernedStatementError does not exist")
    assert issubclass(error_class, RuntimeError) and not issubclass(error_class, ValueError), (
        error_class.__mro__
    )
    return error_class  # type: ignore[no-any-return]


def _main_with_a_migrate_body(body: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    calls: list[str] = []
    monkeypatch.setattr(
        p_module, "build_principal_store", lambda _c: cli._HandleStore("principal", None, calls)
    )
    monkeypatch.setattr(p_module, "build_keep_store", lambda _c: cli._HandleStore("keep", None, calls))
    monkeypatch.setattr(p_module, "migrate_governed", body)
    config_path = tmp_path / "lore.yaml"
    config_path.write_text(
        yaml.safe_dump(cli._config_payload(database=cli._SWEEP_DATABASE)), encoding="utf-8"
    )
    return p_module.main(["--config", str(config_path), "migrate-governed", "--table", "memory"])


class TestGovernedStatementErrorTracebacks:
    def test_the_class_exists_and_is_not_in_the_handler_tuple(self) -> None:
        """RED at bec29190 (no class). The §11 tuple is derived by AST (``test_principals_cli``)."""
        error_class = _governed_statement_error()
        assert error_class.__name__ not in cli._handler_fault_names(), cli._handler_fault_names()

    def test_an_unreadable_leg_literal_reaches_main_as_a_traceback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """RED at bec29190: the REAL parser raises ``ValueError``, which the handler launders to exit 1."""
        error_class = _governed_statement_error()

        async def body(**_kwargs: Any) -> Any:
            p_module._set_columns(_MUST_RAISE["open-paren-at-end"])  # noqa: SLF001 - the REAL parser raises
            raise AssertionError("the parser must have raised")

        with pytest.raises(error_class):
            _main_with_a_migrate_body(body, tmp_path, monkeypatch)

    def test_CONTROL_a_ValueError_still_launders(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        async def body(**_kwargs: Any) -> Any:
            raise ValueError("--name is required for --type project")

        assert _main_with_a_migrate_body(body, tmp_path, monkeypatch) == 1
        assert "--name is required" in capsys.readouterr().err


# =========================================================================== #
# #31 — the not-supported prose is derived (§13.3 item 9)
# =========================================================================== #


class TestTheNotSupportedProseIsDerived:
    def test_the_invalid_name_refusal_lists_exactly_the_valid_tables(self) -> None:
        reason = p_module._not_supported("nope", table_defined=None).reason or ""  # noqa: SLF001
        named = set(re.findall(r"`(\w+)`", reason)) - {"nope"}
        assert named == set(p_module._MIGRATE_VALID_TABLES), (reason, p_module._MIGRATE_VALID_TABLES)  # noqa: SLF001

    def test_the_brief_refusal_names_exactly_the_migrating_legs(self) -> None:
        """§13.3 item 9 / #31: the "today: …" list is DERIVED — it must equal the derived migrate legs."""
        reason = p_module._not_supported(BRIEF_TABLE, table_defined=True).reason or ""  # noqa: SLF001
        today = reason.split("today:", 1)[1].split(")", 1)[0] if "today:" in reason else ""
        assert set(re.findall(r"`(\w+)`", today)) == set(_migrated_tables()), reason
