"""The #398/#399 recurrence-prevention invariant — a STRUCTURAL fold-coverage guard.

Built for packet 61a-w3 (contract ``test_schema_fold_coverage.py``, ruling of record
``docs/design/2026-08-22-packet61-pdp-audit-rulings.md`` §Fork J, findings #398/#399).
It is the invariant that stops the *"a schema-slice fn LIES — in code structure or in
leading prose — about being empty / not-applied"* class from recurring (the PKT-28 C1 /
rename-sweep "green-at-gate natural-language surface" class, CLAUDE.md).

WHAT IT GUARDS
--------------
``loremaster/loremaster/store/surreal_schema.py`` follows a convention: each DDL slice is
a top-level ``def _*_statements(...) -> list[str]`` returning its table's statements;
:func:`~loremaster.store.surreal_schema.generate_ddl` FOLDS the shared slices by CALLING
them, and a dedicated store's ``ensure_ready`` applies the rest through a standalone
``generate_*_ddl`` entry point. A slice that EMITS statements yet is folded NOWHERE and
consumed by NO standalone generator is DEAD DDL wearing an implementation — the #398/#399
defect (a builder greened a RED-STUB slice but left a ``# … emit [] / NOT folded`` comment,
so committed code carried a present-tense claim contradicting the running code).

PURE SOURCE / AST — one code path grades the real module and every synthetic fixture
--------------------------------------------------------------------------------------
Every public entry point is a pure function of module SOURCE TEXT (``ast.parse`` +, for the
prose leg, raw-line inspection of leading comments the AST discards). No import of the
subject's functions, no live SurrealDB connection, no static/dynamic divergence: a fixture
is just a string, so the real schema and the mutation copies travel the identical path.

THE TWO LEGS
------------
* PRIMARY — :func:`scan_schema_fold_coverage` (STRUCTURAL, undefeatable by rewording): every
  emitting ``_*_statements`` slice must be FOLDED (called in ``generate_ddl``) or STANDALONE
  (called in some other ``generate_*_ddl``). No forbidden literal — the coverage is a set
  relation over AST-derived call sites.
* BACKSTOP — :func:`scan_stale_emptiness_prose` (allowlist-the-safe, a KNOWN BOUND): a
  folded/standalone emitting slice whose docstring or leading comment asserts emptiness in a
  phrasing from the CLOSED :data:`KNOWN_EMPTINESS_PHRASES` set is flagged. Best-effort — a
  novel phrasing evades it (the structural leg is the real defense).

INSTRUMENT-0 — the guard's OWN reach is a CHECKED VARIABLE
---------------------------------------------------------
The slice-fn set is derived by a NAME predicate (``^_[a-z0-9_]+_statements$``), itself a
reach surface. :func:`scan_schema_fold_coverage` therefore FAILS CLOSED
(:class:`SchemaGuardReachError`) when that set is EMPTY (a blind scan / mis-targeted source
must never return a falsely-clean ``[]``) OR when it DIVERGES from an INDEPENDENT by-SHAPE
oracle (:func:`derive_statement_emitters` — every top-level private ``-> list[str]`` def),
so a slice renamed off the convention REDS the guard instead of escaping it silently. The
residual bound (a rename that ALSO drops the ``-> list[str]`` annotation evades both) is
pinned as a KNOWN BOUND in the contract.

Conservative emptiness (the ONLY safe bias for a coverage guard): a slice is treated as
empty ONLY if it provably ``return []`` (the literal RED-STUB shape); EVERY other body is
treated as EMITTING. Over-flagging a slice that is dead-code-empty in some exotic way is
harmless (folding an empty slice is a no-op); false-clearing a real emitter is the only
dangerous direction, and this bias makes it impossible.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass

#: A schema DDL slice: a top-level ``def`` whose name matches this. The BY-NAME derivation.
_SLICE_NAME_RE = re.compile(r"^_[a-z0-9_]+_statements$")

#: The global folding generator; slices it CALLS are "folded". Standalone generators are the
#: OTHER ``generate_*_ddl`` functions (this one excluded).
_GLOBAL_GENERATOR = "generate_ddl"
_GENERATOR_PREFIX = "generate_"
_GENERATOR_SUFFIX = "_ddl"

_ModuleDef = ast.FunctionDef | ast.AsyncFunctionDef


class SchemaGuardReachError(Exception):
    """The fold-coverage scan's OWN reach is compromised, so it refuses to return a verdict.

    Raised by :func:`scan_schema_fold_coverage` when the by-NAME slice-fn set is EMPTY
    (fail-closed — a blind scan or a mis-targeted source must never masquerade as clean) or
    when the by-NAME and by-SHAPE derivations DIVERGE (a slice renamed off the convention —
    the INSTRUMENT-0 reach cross-check). A guard that certifies a set it cannot see is the
    seventh instrument-defeat; this makes its reach a checked variable.
    """


#: The CLOSED set of stale-emptiness phrasings the prose backstop matches (case-insensitive).
#: allowlist-the-safe's dual: enumerate-the-forbidden is the KNOWN BOUND here — a novel
#: phrasing evades it (the structural leg is the real defense). Must at least catch the
#: wordings #398/#399 actually shipped ("RED STUB", "NOT folded", an "emit []" claim).
KNOWN_EMPTINESS_PHRASES: frozenset[str] = frozenset(
    {
        "emit []",
        "emits nothing",
        "red stub",
        "not folded",
        "do not implement",
        "raises notimplementederror",
    }
)


@dataclass(frozen=True)
class FoldFinding:
    """An emitting slice fn folded NOWHERE and consumed by NO standalone generator."""

    slice_fn: str

    def __str__(self) -> str:
        return (
            f"{self.slice_fn}: emits >=1 DDL statement but is NEITHER folded into "
            f"{_GLOBAL_GENERATOR} NOR consumed by a standalone {_GENERATOR_PREFIX}*"
            f"{_GENERATOR_SUFFIX} — dead DDL wearing an implementation (#398/#399)."
        )


@dataclass(frozen=True)
class ProseFinding:
    """A folded/standalone emitting slice whose leading prose asserts emptiness (a stale lie)."""

    slice_fn: str
    phrase: str

    def __str__(self) -> str:
        return (
            f"{self.slice_fn}: a folded/standalone emitting slice whose docstring or leading "
            f"comment asserts emptiness ({self.phrase!r}) while its body emits statements — a "
            f"stale #398/#399 emptiness claim contradicting the running code."
        )


def _module_defs(source: str) -> list[_ModuleDef]:
    """Every TOP-LEVEL function definition in ``source`` (sync or async)."""
    tree = ast.parse(source)
    return [node for node in tree.body if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)]


def _called_names(fn_node: ast.AST) -> set[str]:
    """Every function-call NAME (``Name.id`` or ``Attribute.attr``) reachable within ``fn_node``.

    Hand-rolled (see the report's DRY ledger): the nearest twin,
    ``test_ast_reach_helpers._call_names_in``, lives inside a pytest module (uncollectable as a
    shared import) and serves a whole-workspace tree parser, a different input contract than this
    single-module source guard.
    """
    names: set[str] = set()
    for node in ast.walk(fn_node):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                names.add(func.id)
            elif isinstance(func, ast.Attribute):
                names.add(func.attr)
    return names


def _returns_list_str(fn_node: _ModuleDef) -> bool:
    """True iff ``fn_node`` is annotated ``-> list[str]`` (whitespace-insensitive)."""
    if fn_node.returns is None:
        return False
    return ast.unparse(fn_node.returns).replace(" ", "") == "list[str]"


def _is_provably_empty(fn_node: _ModuleDef) -> bool:
    """True iff ``fn_node``'s body — docstring stripped — is EXACTLY a single ``return []``.

    The conservative RED-STUB shape. Every other body (a literal-list return, the house
    ``statements = [...]; ...; return statements`` variable idiom, anything at all) is treated
    as EMITTING — the only safe bias for a coverage guard (see the module docstring).
    """
    body = fn_node.body
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        body = body[1:]  # drop the docstring
    if len(body) != 1:
        return False
    stmt = body[0]
    return (
        isinstance(stmt, ast.Return)
        and isinstance(stmt.value, ast.List)
        and len(stmt.value.elts) == 0
    )


def _emits(fn_node: _ModuleDef) -> bool:
    """True unless the slice provably ``return []`` — see :func:`_is_provably_empty`."""
    return not _is_provably_empty(fn_node)


def derive_slice_fns(source: str) -> set[str]:
    """The BY-NAME derivation: every top-level ``def`` matching ``^_[a-z0-9_]+_statements$``."""
    return {node.name for node in _module_defs(source) if _SLICE_NAME_RE.match(node.name)}


def derive_statement_emitters(source: str) -> set[str]:
    """The INDEPENDENT BY-SHAPE oracle for the INSTRUMENT-0 reach cross-check.

    Every top-level PRIVATE (``_``-prefixed) def annotated ``-> list[str]``. Deliberately does
    NOT reuse :func:`derive_slice_fns`' name predicate — on a module whose emitter is misnamed
    the two derivations MUST diverge (else the cross-check is ``derived == derived`` theatre).
    """
    return {
        node.name
        for node in _module_defs(source)
        if node.name.startswith("_") and _returns_list_str(node)
    }


def _is_standalone_generator(name: str) -> bool:
    return (
        name.startswith(_GENERATOR_PREFIX)
        and name.endswith(_GENERATOR_SUFFIX)
        and name != _GLOBAL_GENERATOR
    )


def derive_folded_slices(source: str) -> set[str]:
    """Slice-fn names appearing as a CALL in the body of top-level ``generate_ddl``.

    Intersected with the real slice-fn set, so a phantom call (a ``_*_statements`` name with no
    def) can never inflate the folded set past the actual slices.
    """
    slices = derive_slice_fns(source)
    for node in _module_defs(source):
        if node.name == _GLOBAL_GENERATOR:
            return _called_names(node) & slices
    return set()


def derive_standalone_slices(source: str) -> dict[str, set[str]]:
    """Each slice-fn name called in SOME top-level ``generate_*_ddl`` OTHER than ``generate_ddl``,
    mapped to the set of ``generate_*_ddl`` names that call it (the evidence)."""
    slices = derive_slice_fns(source)
    standalone: dict[str, set[str]] = {}
    for node in _module_defs(source):
        if not _is_standalone_generator(node.name):
            continue
        for called in _called_names(node) & slices:
            standalone.setdefault(called, set()).add(node.name)
    return standalone


def _assert_reach_or_raise(by_name: set[str], by_shape: set[str]) -> None:
    """INSTRUMENT-0: fail closed unless the guard can see its whole subject.

    Raises :class:`SchemaGuardReachError` when the by-NAME slice-fn set is EMPTY (a blind scan
    or a mis-targeted source must never return a falsely-clean ``[]``) or when the by-NAME and
    by-SHAPE derivations DIVERGE (a slice renamed off the convention), so the guard's own reach
    is a CHECKED VARIABLE rather than a hidden constant.
    """
    if not by_name:
        raise SchemaGuardReachError(
            "fold-coverage scan derived ZERO `_*_statements` slice fns — a blind scan or a "
            "mis-targeted source must never return a falsely-clean []. FAIL CLOSED: either the "
            "`_*_statements` convention was renamed wholesale (widen the derivation) or the wrong "
            f"source was scanned. by-shape emitters present: {sorted(by_shape)}"
        )
    if by_name != by_shape:
        raise SchemaGuardReachError(
            "the by-NAME (`_*_statements`) and by-SHAPE (private `-> list[str]`) slice-fn "
            "derivations DIVERGE — a slice was renamed off the convention (INSTRUMENT-0 reach "
            f"cross-check). name-only={sorted(by_name - by_shape)}, "
            f"shape-only={sorted(by_shape - by_name)}"
        )


def scan_schema_fold_coverage(source: str) -> list[FoldFinding]:
    """The PRIMARY structural leg: one :class:`FoldFinding` per emitting slice fn that is folded
    NOWHERE and consumed by NO standalone generator.

    FAILS CLOSED (:class:`SchemaGuardReachError`) on an empty by-NAME set or a name/shape reach
    divergence (INSTRUMENT-0), so the guard's own reach is a checked variable.
    """
    defs = _module_defs(source)
    by_name = {node.name for node in defs if _SLICE_NAME_RE.match(node.name)}
    by_shape = {node.name for node in defs if node.name.startswith("_") and _returns_list_str(node)}
    _assert_reach_or_raise(by_name, by_shape)

    covered = derive_folded_slices(source) | set(derive_standalone_slices(source))
    return [
        FoldFinding(slice_fn=node.name)
        for node in defs
        if node.name in by_name and _emits(node) and node.name not in covered
    ]


def _leading_comment_block(source_lines: list[str], def_lineno: int) -> str:
    """The contiguous ``#`` comment lines DIRECTLY above the def at 1-based ``def_lineno``.

    Walks UP from the line immediately above the def, collecting comment lines until the first
    non-comment (a blank line, code, a closing paren) breaks the run. Comments are stripped by
    the AST, so this is the only way to see a ``# … emit [] / NOT folded`` leading comment — the
    exact #398/#399 shape.
    """
    collected: list[str] = []
    index = def_lineno - 2  # 0-based index of the line directly above the def
    while index >= 0 and source_lines[index].lstrip().startswith("#"):
        collected.append(source_lines[index].strip())
        index -= 1
    return "\n".join(reversed(collected))


def scan_stale_emptiness_prose(source: str) -> list[ProseFinding]:
    """The BACKSTOP prose leg (KNOWN BOUND): flag any folded/standalone EMITTING slice whose
    docstring or leading comment contains a :data:`KNOWN_EMPTINESS_PHRASES` phrasing.

    Best-effort over a CLOSED phrase set — a novel phrasing evades it. It only adds cover for an
    emptiness claim on an ALREADY-folded slice (whose statements DO run, so the structural leg
    cannot see the lie). It targets a MISMATCH (emitting body + emptiness claim), never an honest
    emptiness claim on a genuinely-empty stub.
    """
    defs = _module_defs(source)
    by_name = {node.name for node in defs if _SLICE_NAME_RE.match(node.name)}
    covered = derive_folded_slices(source) | set(derive_standalone_slices(source))
    source_lines = source.splitlines()
    phrases = tuple(phrase.lower() for phrase in KNOWN_EMPTINESS_PHRASES)

    findings: list[ProseFinding] = []
    for node in defs:
        if node.name not in by_name or not _emits(node) or node.name not in covered:
            continue
        docstring = ast.get_docstring(node) or ""
        leading = _leading_comment_block(source_lines, node.lineno)
        blob = f"{docstring}\n{leading}".lower()
        matched = next((phrase for phrase in phrases if phrase in blob), None)
        if matched is not None:
            findings.append(ProseFinding(slice_fn=node.name, phrase=matched))
    return findings
