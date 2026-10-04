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
import inspect
import logging
import re
import shlex
import string
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

import loremaster.governed as governed_module
import pytest
import test_engine_rejection_seam as seam  # module-qualified: its Test* classes are not re-collected here
import test_preboot_schema_precondition_63c_13d as preboot
import test_principals_cli as cli
import yaml
from loremaster.principal_keys import PrincipalKeyStore, PrincipalKeyStoreError
from loremaster.store._txn import SurrealStoreError
from loremaster.store.surreal_schema import BRIEF_TABLE
from pydantic import SecretStr

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

_LANDED_TEMPLATE = (
    "the {noun} LANDED (committed) but answered a {type} instead of its rows — nothing was decided from the "
    "answer; {remedy}"
)

#: The rendered default for a site that passes no remedy — written OUT, not derived from the template, so a
#: changed template or default remedy that alters the served text goes RED here (#531 follow-up, fix531b).
_LANDED_DEFAULT_TEXT = (
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

    @pytest.mark.parametrize("answer", ["garbage", None, {"id": "x"}], ids=["str", "None", "dict"])
    def test_the_one_landed_template(self, answer: Any) -> None:
        """RED at bec29190 (``rows_of`` has no ``landed``). The template is ONE text, byte-exact."""
        with pytest.raises(Exception) as caught:  # noqa: PT011 - SurrealStoreError, the class rows_of raises
            governed_module.rows_of(answer, noun="probe write", landed=True)  # type: ignore[call-arg,unused-ignore]
        assert str(caught.value) == _LANDED_TEMPLATE.format(
            noun="probe write",
            type=type(answer).__name__,
            remedy="verify the stored state before re-running",
        )

    @pytest.mark.parametrize("answer", ["garbage", None, ["row"]], ids=["str", "None", "non-dict-member"])
    def test_a_site_passing_no_remedy_serves_the_default_text_byte_identical(self, answer: Any) -> None:
        """fix531b (a): slotting the remedy must not change one byte for the sites that pass none."""
        kind = type(answer[0] if isinstance(answer, list) else answer).__name__
        with pytest.raises(SurrealStoreError) as caught:
            governed_module.rows_of(answer, noun="probe write", landed=True)
        assert str(caught.value) == _LANDED_DEFAULT_TEXT.format(noun="probe write", type=kind)

    def test_the_template_has_exactly_one_remedy_slot(self) -> None:
        """fix531b (c): the ONE template carries the remedy as exactly one slot, beside noun and type."""
        template = governed_module._LANDED_SHAPE_FAULT  # noqa: SLF001
        fields = [
            field for _literal, field, _spec, _conv in string.Formatter().parse(template) if field is not None
        ]
        assert sorted(fields) == ["noun", "remedy", "type"], fields
        assert template == _LANDED_TEMPLATE

    def test_a_passed_remedy_replaces_the_default_clause(self) -> None:
        with pytest.raises(SurrealStoreError) as caught:
            governed_module.rows_of("garbage", noun="probe write", landed=True, remedy="do the special thing")
        assert str(caught.value) == _LANDED_TEMPLATE.format(
            noun="probe write", type="str", remedy="do the special thing"
        )

    def test_a_remedy_without_landed_is_refused(self) -> None:
        """A remedy belongs to a landed write only; on a plain read it would be silently dropped."""
        with pytest.raises(ValueError, match="remedy"):
            governed_module.rows_of([], noun="probe read", remedy="do the special thing")

    def test_CONTROL_the_unlanded_read_keeps_its_own_text(self) -> None:
        with pytest.raises(Exception) as caught:  # noqa: PT011
            governed_module.rows_of("garbage", noun="probe read")
        assert "LANDED" not in str(caught.value), str(caught.value)


class TestALandedThenFaultedMintNamesTheRevokeRemedy:
    """fix531b (b), #531 follow-up: a ``mint`` whose CREATE committed but answered a wrong shape aborts BEFORE
    the CLI prints the one-time secret, leaving a LIVE key whose secret nobody has. The generic "verify the
    stored state" advice leaves that key standing; the fault must name the revoke verb for THAT key."""

    @pytest.mark.parametrize("answer", ["garbage", None, {"id": "principal_key:x"}, ["row"]])
    @pytest.mark.parametrize(
        ("email", "name"),
        [("ops531@example.com", "laptop"), ("dev.531+keys@example.org", "work laptop")],
        ids=["plain", "needs-quoting"],
    )
    async def test_the_fault_names_lore_adm_revoke_key_for_the_landed_key(
        self, monkeypatch: pytest.MonkeyPatch, answer: Any, email: str, name: str
    ) -> None:
        store = PrincipalKeyStore(
            url="ws://127.0.0.1:1", namespace="ns531b", database="db531b", user="u", password=SecretStr("p")
        )
        landed = {"count": 0}

        async def require_principal_id(_email: str) -> str:
            return "abc531b"

        async def query(statement: str, _params: dict[str, Any] | None = None) -> Any:
            assert statement.startswith("CREATE "), statement
            landed["count"] += 1
            return answer

        monkeypatch.setattr(store, "_require_principal_id", require_principal_id)
        monkeypatch.setattr(store, "_query", query)
        with pytest.raises(SurrealStoreError) as caught:
            await store.mint(email=email, name=name, secret_hash="0" * 128)
        assert landed["count"] == 1, "the forged CREATE answer never landed (#194)"
        message = str(caught.value)
        revoke_argv = shlex.join(["lore-adm", "revoke-key", "--email", email, "--name", name])
        assert "principal-key mint LANDED" in message, message
        assert revoke_argv in message, f"the revoke remedy for {name!r} is missing: {message}"
        assert "never shown" in message and "mint a new" in message, message
        assert "verify the stored state before re-running" not in message, message
        self._assert_served_revoke_parses(message, email=email, name=name)

    @staticmethod
    def _assert_served_revoke_parses(message: str, *, email: str, name: str) -> None:
        """The FIRST backticked command must be one the REAL lore-adm parser runs as THIS key's revoke — a
        renamed verb or flag reddens here instead of shipping a remedy that no longer works."""
        parser = p_module.build_parser()
        served = shlex.split(message.split("`")[1])
        assert served[0] == parser.prog, served
        parsed = vars(parser.parse_args(served[1:]))
        assert (parsed["command"], parsed["email"], parsed["name"]) == ("revoke-key", email, name), parsed

    @staticmethod
    def _store_whose_create_answers(
        monkeypatch: pytest.MonkeyPatch, answer: Any
    ) -> tuple[PrincipalKeyStore, dict[str, int]]:
        """A store whose mint CREATE lands (counted, #194) and answers ``answer``."""
        store = PrincipalKeyStore(
            url="ws://127.0.0.1:1", namespace="ns531c", database="db531c", user="u", password=SecretStr("p")
        )
        landed = {"count": 0}

        async def require_principal_id(_email: str) -> str:
            return "abc531c"

        async def query(statement: str, _params: dict[str, Any] | None = None) -> Any:
            assert statement.startswith("CREATE "), statement
            landed["count"] += 1
            return answer

        monkeypatch.setattr(store, "_require_principal_id", require_principal_id)
        monkeypatch.setattr(store, "_query", query)
        return store, landed

    @pytest.mark.parametrize(
        ("email", "name"),
        [("ops531@example.com", "laptop"), ("dev.531+keys@example.org", "work laptop")],
        ids=["plain", "needs-quoting"],
    )
    async def test_a_create_answering_no_row_names_the_same_revoke_repair(
        self, monkeypatch: pytest.MonkeyPatch, email: str, name: str
    ) -> None:
        """fix531c, #531 (REPORT-fix531b §5.2): a CREATE ``RETURN AFTER`` answering ``[]`` may or may not have
        stored the key, and its secret was never shown. The fault must name the SAME revoke repair as the
        wrong-shape mint, conditioned on ``list-keys`` showing the key — never a bare "vanished"."""
        store, landed = self._store_whose_create_answers(monkeypatch, [])
        with pytest.raises(PrincipalKeyStoreError) as caught:
            await store.mint(email=email, name=name, secret_hash="0" * 128)
        assert landed["count"] == 1, "the forged CREATE answer never landed (#194)"
        message = str(caught.value)
        revoke_argv = shlex.join(["lore-adm", "revoke-key", "--email", email, "--name", name])
        assert repr(name) in message, message
        assert revoke_argv in message, f"the revoke remedy for {name!r} is missing: {message}"
        assert "never shown" in message and "list-keys" in message and "mint a new" in message, message
        self._assert_served_revoke_parses(message, email=email, name=name)

    @pytest.mark.parametrize(
        ("answer", "raised"),
        [("garbage", SurrealStoreError), ([], PrincipalKeyStoreError)],
        ids=["wrong-shape", "no-row"],
    )
    async def test_both_mint_faults_take_the_revoke_command_from_the_one_helper(
        self, monkeypatch: pytest.MonkeyPatch, answer: Any, raised: type[Exception]
    ) -> None:
        """ONE IMPLEMENTATION, proven by MUTATION: replace ``PrincipalKeyStore._revoke_command`` and BOTH
        fault sites must serve the replacement — a site that still serves the real argv built its own copy."""
        sentinel = "SENTINEL-531c revoke command"
        calls: list[tuple[str, str]] = []

        def fake_revoke_command(*, email: str, name: str) -> str:
            calls.append((email, name))
            return sentinel

        monkeypatch.setattr(PrincipalKeyStore, "_revoke_command", staticmethod(fake_revoke_command))
        store, _landed = self._store_whose_create_answers(monkeypatch, answer)
        with pytest.raises(raised) as caught:
            await store.mint(email="ops531@example.com", name="laptop", secret_hash="0" * 128)
        message = str(caught.value)
        assert f"`{sentinel}`" in message, message
        assert "revoke-key" not in message, f"a private copy of the revoke command: {message}"
        assert calls == [("ops531@example.com", "laptop")], calls


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
    for path in sorted(_PACKAGE.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
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
    for path in sorted(_PACKAGE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
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
                    sites.append((f"{path.relative_to(_PACKAGE)}::{function.name}::{call.lineno}", has_noun))
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
        for path in sorted(_PACKAGE.rglob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in _function_nodes(tree):
                if node.name in _row_reader_wrappers(tree):
                    kwonly = {
                        arg.arg: default
                        for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True)
                    }
                    if "noun" not in kwonly or kwonly["noun"] is not None:
                        problems.append(f"{path.relative_to(_PACKAGE)}::{node.name}")
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
