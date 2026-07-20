"""PKT-28 Phase 0 render-safety seam pins.

Spec: phase0-render-safety-ruling.md — §ENFORCEMENT failure-matrix row 6
(the AST mint-pin) and §REGISTRY-MIGRATION (the dispatch-table completeness
helper for a future comms battery's own action registry, e.g. C1's
``_COMMS_ACTIONS``). NOTE: that ruling is UNRECOVERABLE — a per-session
``/tmp`` scratch file, never in the repo and now gone from disk (see
``test_render.py``'s module docstring). Its §-references resolve to nothing
and are unverified provenance.

Two independent, zero-semantics invariants live here:

1. ``TestSafeLineRenderedMintPin`` -- ``SafeLine``/``Rendered`` may only be
   MINTED (constructed, or ``cast`` to) inside their own seam modules
   (``loremaster/sanitise.py`` / ``loremaster/render.py``). A construction or
   cast anywhere else in the production package is a silent bypass of the
   type-level guarantee the render-safety seam exists to provide -- the type
   checker cannot catch this (constructing a subclass of ``str`` from a
   ``str`` is always legal), so an AST scan is the enforcement instrument.
   Mirrors ``test_text_hygiene.py``'s AST-walk idiom in this same test tree.

2. ``assert_actions_covered`` -- a reusable completeness helper any future
   dispatch-table-shaped battery (e.g. a C1 comms test module) can call
   against its own ``{action_name: handler}`` registry: every action must
   have a registered ``RenderCase`` (by family -- ``label.split(".")[0]``)
   or an explicit, non-blank exemption-with-reason. Default is FAIL --
   coverage is proven by a positive record, never assumed by omission.
"""

from __future__ import annotations

import ast
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

import pytest
from render_injection_scaffold import RenderCase

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent / "loremaster"

# The only two modules permitted to mint (construct, or ``cast`` to) either
# seam type -- everywhere else in the production package, a SafeLine/Rendered
# must arrive already-minted through the assembly vocabulary.
_ALLOWED_MINT_MODULES: frozenset[str] = frozenset({"sanitise.py", "render.py"})

_MINTED_TYPE_NAMES: frozenset[str] = frozenset({"SafeLine", "Rendered"})

# R1 residual (REPORT-phase0-audit-1.md §RESIDUALS): the two verb names whose
# CALLEE NAME the template-literal pin matches on (see
# ``_scan_for_nonliteral_render_templates`` below). Aliasing either import
# evades that callee-name match exactly the way aliasing SafeLine/Rendered
# evaded the mint-pin's own callee-name match -- closed the SAME way, by
# banning the ALIAS (not the call: ``render_line(...)``/``render_join(...)``
# calls themselves are the sanctioned idiom everywhere in production code,
# and are never flagged by this set -- it is used ONLY in the ImportFrom
# branch below, never the Call branch).
_ALIAS_BANNED_VERB_NAMES: frozenset[str] = frozenset({"render_line", "render_join"})


@dataclass(frozen=True)
class _MintSite:
    """One construction, ``cast``, import-alias, or subclass-definition of a
    seam type found by the AST scan (v2 hardening, audit §PROBE-C)."""

    relative_path: str
    lineno: int
    kind: str  # "construct" | "cast" | "import-alias" | "subclass"
    type_name: str


def _string_constant_type_names(node: ast.expr) -> set[str]:
    """Every minted-type identifier appearing as a plain identifier token
    inside a STRING-FORM type expression, e.g. ``cast("SafeLine", x)`` or
    ``cast("SafeLine | Rendered", x)`` (v2 hardening, audit §PROBE-C bypass
    2). ``from __future__ import annotations`` makes the quoted-string form
    of ``cast``'s first argument a routine, unremarkable idiom -- and
    ``cast()`` never actually evaluates that argument at runtime, so a
    string here is exactly as effective a bypass as the bare-name form and
    must be caught the same way, not just the ``ast.Name``/``ast.Attribute``
    shapes :func:`_type_names_in_expr` already handles.
    """
    if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
        return set()
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", node.value)) & _MINTED_TYPE_NAMES


def _type_names_in_expr(node: ast.AST) -> set[str]:
    """Every bare/attribute identifier inside a type-expression AST subtree.

    Handles the plain form (``SafeLine``), the module-qualified form
    (``sanitise.SafeLine``), and the union form ``cast`` accepts
    (``SafeLine | Rendered``, an ``ast.BinOp``/``ast.BitOr``) uniformly by
    just collecting every ``Name``/``Attribute`` identifier under the node,
    since none of those shapes needs different handling to answer "does this
    type expression mention SafeLine or Rendered".
    """
    names: set[str] = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name):
            names.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            names.add(sub.attr)
    return names


def _called_name(func: ast.expr) -> str | None:
    """The bare callee name of a ``Call`` node's ``func``, for both
    ``SafeLine(...)`` (``ast.Name``) and ``sanitise.SafeLine(...)``
    (``ast.Attribute``) call shapes."""
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _scan_for_mint_sites(root: Path) -> list[_MintSite]:
    """Walk every ``.py`` file under ``root`` for SafeLine/Rendered mint sites.

    A generic scanner over an arbitrary root (not just ``_PACKAGE_ROOT``) so
    the detector itself is testable against synthetic fixture trees --
    see ``TestSafeLineRenderedMintPin``'s scanner self-tests below.

    v2 hardening (fix-wave, audit §PROBE-C -- three bypass shapes the
    original scanner missed, all zero-false-positive syntactic checks):
    (i) a string-form ``cast("SafeLine", x)`` -- the cast's first arg is
    inspected for a Constant string naming a seam type, not just a
    Name/Attribute; (ii) ``from ... import SafeLine as SL`` -- an
    ``ImportFrom`` alias of a seam name has no legitimate use outside the
    seam, so any ``asname`` on one is itself an offender, no call needed;
    (iii) ``class MyRendered(Rendered): ...`` -- a ``ClassDef`` whose bases
    mention a seam type is banned at the DEFINITION, closing subclass-mint
    at its root (the follow-on construction call becomes moot).

    R1 residual hardening (REPORT-phase0-audit-1.md §RESIDUALS, re-verify
    follow-up): the SAME ``ImportFrom``-``asname`` check ALSO bans aliasing
    ``render_line``/``render_join`` (``_ALIAS_BANNED_VERB_NAMES``) -- an
    alias-imported verb evades the template-literal pin's callee-name match
    exactly as an aliased ``SafeLine``/``Rendered`` evaded this pin's own
    callee-name match, so the fix is the same instrument, widened. A
    RE-ASSIGNED name (``_r = render_line``) is a DIFFERENT, narrower shape
    this does NOT catch -- no reassignment detector is built here (that
    would be a real dataflow-analysis project, the same class of overreach
    §RULING's option (c) analysis rejected); it is deliberately left to the
    runtime no-newline/control-char guard inside ``render_line``/
    ``render_join`` themselves, which fires regardless of what name reached
    the call (R2 kills the residual chain unconditionally, not just this
    one alias shape).
    """
    sites: list[_MintSite] = []
    for path in sorted(root.rglob("*.py")):
        relative_path = str(path.relative_to(root))
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                called_name = _called_name(node.func)
                if called_name in _MINTED_TYPE_NAMES and called_name is not None:
                    sites.append(_MintSite(relative_path, node.lineno, "construct", called_name))
                elif called_name == "cast" and node.args:
                    type_names = _type_names_in_expr(node.args[0]) | _string_constant_type_names(
                        node.args[0]
                    )
                    for type_name in sorted(type_names & _MINTED_TYPE_NAMES):
                        sites.append(_MintSite(relative_path, node.lineno, "cast", type_name))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if (
                        alias.name in _MINTED_TYPE_NAMES | _ALIAS_BANNED_VERB_NAMES
                        and alias.asname is not None
                    ):
                        sites.append(
                            _MintSite(relative_path, node.lineno, "import-alias", alias.name)
                        )
            elif isinstance(node, ast.ClassDef):
                base_names: set[str] = set()
                for base in node.bases:
                    base_names |= _type_names_in_expr(base)
                for type_name in sorted(base_names & _MINTED_TYPE_NAMES):
                    sites.append(_MintSite(relative_path, node.lineno, "subclass", type_name))
    return sites


def _scan_production_package_for_mint_sites() -> list[_MintSite]:
    return _scan_for_mint_sites(_PACKAGE_ROOT)


# The two calls whose first slot (render_line's ``template``, render_join's
# ``separator``) mypy cannot guard: ``LiteralString`` is parsed but never
# enforced by mypy 2.1.0 (v2 ruling amendment, audit §PROBE-A). This AST scan
# is the ONLY instrument on that slot -- see TestRenderLineTemplateLiteralPin.
# Same two names as ``_ALIAS_BANNED_VERB_NAMES`` above (R1 residual) -- one
# constant, two complementary uses: there, banning the ALIAS; here, matching
# the CALLEE name.
_TEMPLATE_CALL_NAMES: frozenset[str] = _ALIAS_BANNED_VERB_NAMES


@dataclass(frozen=True)
class _TemplateSite:
    """One ``render_line``/``render_join`` call whose template/separator
    slot is NOT a literal string constant, found by the AST scan."""

    relative_path: str
    lineno: int
    call_name: str
    node_kind: str  # e.g. "JoinedStr", "Name", "BinOp", "Call", "Attribute"


def _template_arg_node(node: ast.Call, called_name: str) -> ast.expr | None:
    """The AST node occupying the template/separator slot, whether passed
    POSITIONALLY (``args[0]`` -- both ``render_line``'s ``template`` and
    ``render_join``'s ``separator`` accept this) or, for ``render_join``
    only, by KEYWORD (``separator=...`` -- unlike ``render_line``'s
    ``template``, ``render_join``'s ``separator`` is not positional-only in
    the current signature, so ``args[0]`` alone would miss
    ``render_join(separator=hostile, parts=parts)``). Returns ``None`` if
    the call supplies neither -- a malformed/non-functional call, out of
    this scanner's scope (it would fail with a ``TypeError`` at runtime
    regardless of anything this pin checks).
    """
    if node.args:
        return node.args[0]
    if called_name == "render_join":
        for kw in node.keywords:
            if kw.arg == "separator":
                return kw.value
    return None


def _scan_for_nonliteral_render_templates(root: Path) -> list[_TemplateSite]:
    """Walk every ``.py`` file under ``root`` for a ``render_line``/
    ``render_join`` call whose template/separator slot is not a literal
    string constant -- the row-3 instrument (ruling v2, audit §PROBE-A /
    §REMEDIATION item 1): mypy does not enforce ``LiteralString`` (it parses
    the annotation and then erases it to plain ``str``), so this AST check
    is the ONLY guard on the template slot. There is no legitimate reason to
    pass a non-literal template/separator to either verb, so this has zero
    false-positive cost. Generic over an arbitrary root so the detector is
    self-testable against synthetic fixture trees, same as
    :func:`_scan_for_mint_sites`.
    """
    sites: list[_TemplateSite] = []
    for path in sorted(root.rglob("*.py")):
        relative_path = str(path.relative_to(root))
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            called_name = _called_name(node.func)
            if called_name not in _TEMPLATE_CALL_NAMES or called_name is None:
                continue
            template_arg = _template_arg_node(node, called_name)
            if template_arg is None:
                continue
            if isinstance(template_arg, ast.Constant) and isinstance(template_arg.value, str):
                continue
            sites.append(
                _TemplateSite(relative_path, node.lineno, called_name, type(template_arg).__name__)
            )
    return sites


class TestSafeLineRenderedMintPin:
    """Failure-matrix row 6: SafeLine/Rendered minted only inside the seam."""

    def test_no_mint_site_outside_the_seam_modules(self) -> None:
        offenders = [
            site
            for site in _scan_production_package_for_mint_sites()
            if site.relative_path not in _ALLOWED_MINT_MODULES
        ]
        assert not offenders, (
            "SafeLine/Rendered minted outside sanitise.py/render.py:\n"
            + "\n".join(
                f"{site.relative_path}:{site.lineno}: {site.kind} of {site.type_name}"
                for site in offenders
            )
        )

    # -- Scanner self-tests: prove the detector is a REAL detector, not
    # vacuously passing because nothing constructs these types yet (render.py
    # doesn't exist at contract-authoring time). Each writes a synthetic
    # source file to tmp_path and scans THAT root, independent of the real
    # production tree. --

    def test_scanner_detects_a_bare_construction(self, tmp_path: Path) -> None:
        (tmp_path / "hostile.py").write_text(
            "from loremaster.sanitise import SafeLine\nx = SafeLine('a')\n"
        )
        sites = _scan_for_mint_sites(tmp_path)
        assert any(s.type_name == "SafeLine" and s.kind == "construct" for s in sites)

    def test_scanner_detects_a_module_qualified_construction(self, tmp_path: Path) -> None:
        (tmp_path / "hostile.py").write_text(
            "from loremaster import render\nx = render.Rendered('a')\n"
        )
        sites = _scan_for_mint_sites(tmp_path)
        assert any(s.type_name == "Rendered" and s.kind == "construct" for s in sites)

    def test_scanner_detects_a_bare_cast(self, tmp_path: Path) -> None:
        (tmp_path / "hostile.py").write_text(
            "from typing import cast\n"
            "from loremaster.render import Rendered\n"
            "x = cast(Rendered, 'a')\n"
        )
        sites = _scan_for_mint_sites(tmp_path)
        assert any(s.type_name == "Rendered" and s.kind == "cast" for s in sites)

    def test_scanner_detects_both_names_in_a_union_cast(self, tmp_path: Path) -> None:
        (tmp_path / "hostile.py").write_text(
            "from typing import cast\n"
            "from loremaster.sanitise import SafeLine\n"
            "from loremaster.render import Rendered\n"
            "x = cast(SafeLine | Rendered, 'a')\n"
        )
        sites = _scan_for_mint_sites(tmp_path)
        type_names = {s.type_name for s in sites if s.kind == "cast"}
        assert type_names == {"SafeLine", "Rendered"}

    def test_scanner_ignores_an_unrelated_call(self, tmp_path: Path) -> None:
        (tmp_path / "benign.py").write_text("x = str('a')\ny = dict(a=1)\n")
        assert _scan_for_mint_sites(tmp_path) == []

    def test_allowed_modules_are_not_flagged_as_offenders(self, tmp_path: Path) -> None:
        (tmp_path / "sanitise.py").write_text("class SafeLine(str):\n    pass\nx = SafeLine('a')\n")
        sites = _scan_for_mint_sites(tmp_path)
        offenders = [s for s in sites if s.relative_path not in _ALLOWED_MINT_MODULES]
        assert not offenders
        # sanity: the scanner DID see the site, it just isn't an offender --
        # a scanner returning [] here would silently pass for the WRONG
        # reason (finding nothing) rather than the right one (exempting it).
        assert sites

    # -- v2 hardening self-tests (fix-wave, cold audit §PROBE-C): three bypass
    # shapes the audit found the ORIGINAL scanner blind to. Each mirrors one
    # of the audit's own hostile_tree/ fixtures byte-for-byte in spirit.
    # EXPECTED RED against the pre-hardening scanner -- recorded before the
    # hardening below made them pass. --

    def test_scanner_catches_an_import_as_alias_of_a_seam_name(self, tmp_path: Path) -> None:
        """Audit §PROBE-C bypass 1 (hostile_tree/bypass_alias.py): ``from
        loremaster.sanitise import SafeLine as SL`` then ``SL("raw")`` --
        rebinding the identifier evaded the old callee-name match entirely
        (it only ever compared against the literal names "SafeLine"/
        "Rendered")."""
        (tmp_path / "hostile.py").write_text(
            "from loremaster.sanitise import SafeLine as SL\nx = SL('raw agent text\\nforged')\n"
        )
        sites = _scan_for_mint_sites(tmp_path)
        assert any(s.kind == "import-alias" and s.type_name == "SafeLine" for s in sites)

    def test_scanner_catches_a_string_form_cast(self, tmp_path: Path) -> None:
        """Audit §PROBE-C bypass 2 (hostile_tree/bypass_cast_string.py):
        ``cast("SafeLine", x)`` -- a normal idiom under ``from __future__
        import annotations`` -- was invisible because the old scan only
        walked Name/Attribute nodes in the cast's type argument, never a
        Constant string."""
        (tmp_path / "hostile.py").write_text(
            "from typing import cast\nx = cast('SafeLine', 'raw agent text')\ny = cast('Rendered', 'raw')\n"
        )
        sites = _scan_for_mint_sites(tmp_path)
        type_names = {s.type_name for s in sites if s.kind == "cast"}
        assert type_names == {"SafeLine", "Rendered"}

    def test_scanner_catches_a_subclass_of_a_seam_type(self, tmp_path: Path) -> None:
        """Audit §PROBE-C bypass 3 (hostile_tree/bypass_subclass.py):
        ``class MyRendered(Rendered): pass`` then ``MyRendered("raw")`` --
        the CALL was to "MyRendered", never a recognized minted-type name, so
        the old scan never saw it. Banning the subclass DEFINITION itself
        closes the bypass at its root -- the follow-on construction call
        becomes moot once the class can't legally exist outside the seam."""
        (tmp_path / "hostile.py").write_text(
            "from loremaster.render import Rendered\n"
            "class MyRendered(Rendered):\n"
            "    pass\n"
            "x = MyRendered('raw\\nforged')\n"
        )
        sites = _scan_for_mint_sites(tmp_path)
        assert any(s.kind == "subclass" and s.type_name == "Rendered" for s in sites)

    # -- R1 residual self-test (REPORT-phase0-audit-1.md §RESIDUALS, re-verify
    # follow-up): the template-literal pin matches render_line/render_join by
    # CALLEE NAME, so aliasing either import evades it -- the same bypass
    # class the mint-pin above already closes for SafeLine/Rendered.
    # EXPECTED RED against the pre-R1 scanner -- recorded before widening the
    # ImportFrom-asname check below made it pass. --

    def test_scanner_catches_an_aliased_import_of_a_template_verb_name(self, tmp_path: Path) -> None:
        """Reproduces the auditor's ``tpl_tree/BYPASS_aliased_import.py``
        exactly: ``from loremaster.render import render_line as rl`` then
        ``rl(f"row {raw}")`` -- rebinding the import evades the template
        pin's callee-name match precisely as aliasing SafeLine/Rendered
        evaded the mint-pin's, closed the SAME way here: banning the
        ALIAS, not the call (a normal, unaliased ``render_line(...)`` call
        is never flagged)."""
        (tmp_path / "hostile.py").write_text(
            "from loremaster.render import render_line as rl\ndef f(raw): return rl(f'row {raw}')\n"
        )
        sites = _scan_for_mint_sites(tmp_path)
        assert any(s.kind == "import-alias" and s.type_name == "render_line" for s in sites)

    def test_unaliased_verb_import_is_not_flagged(self, tmp_path: Path) -> None:
        """Negative control: a plain, unaliased ``from loremaster.render
        import render_line`` -- the sanctioned idiom everywhere in
        production code -- must never be an offender."""
        (tmp_path / "clean.py").write_text(
            "from loremaster.render import render_line\ndef f(raw): return render_line('static')\n"
        )
        assert _scan_for_mint_sites(tmp_path) == []


class TestRenderLineTemplateLiteralPin:
    """Failure-matrix row 3 (v2, ruling amendment post cold-audit NO-GO):
    mypy does NOT enforce ``LiteralString`` (audit §PROBE-A -- mypy 2.1.0
    parses but never checks it, erasing it to plain ``str``), so
    render_line's/render_join's template/separator slot (the first
    positional argument, or render_join's ``separator`` keyword -- see
    below) needs its own AST instrument: it must be a literal
    ``ast.Constant`` string everywhere in the production package. There is
    no legitimate reason to pass a non-literal template/separator, so this
    has zero false-positive cost -- and unlike ``LiteralString`` it cannot be
    defeated by aliasing, because it inspects the argument NODE, not a type
    (ruling §REMEDIATION item 1).

    EXPECTED RED at contract-authoring time: ``_scan_for_nonliteral_render_
    templates`` does not exist yet -- these self-tests are written first,
    confirmed to fail (NameError), THEN the scanner is implemented below.

    **R1 residual, and its accepted narrower gap (REPORT-phase0-audit-1.md
    §RESIDUALS — NOTE: that report was deleted per repo law and never archived,
    and its parent ruling is the unrecoverable ``/tmp`` spec above, so the
    AUTHORITY for accepting this bound is unverified. The mechanism below is
    self-contained; the ACCEPTANCE is not. Repo law wants a known bound carried
    as a ledgered finding with a named re-open trigger — this one has never been
    filed):** this scanner matches ``render_line``/``render_join`` by
    CALLEE NAME (``_called_name`` in ``_scan_for_nonliteral_render_
    templates``), so `from loremaster.render import render_line as rl`
    followed by `rl(f"...")` evades it -- the alias is a DIFFERENT name, so
    the callee-name match never fires. This is closed as a SEPARATE,
    complementary instrument rather than inside this scanner: the mint-pin's
    ``ImportFrom``-``asname`` check (``TestSafeLineRenderedMintPin`` above,
    ``_ALIAS_BANNED_VERB_NAMES``) now ALSO bans aliasing either verb name, so
    the alias itself is flagged before any call is ever inspected. A
    RE-ASSIGNED name (`_r = render_line`) is narrower still and is NOT
    caught by either AST instrument -- deliberately: an AST reassignment
    detector is real dataflow analysis, the same class of overreach the
    ruling's option (c) already rejected as unviable (aliasing false
    negatives degrade a scanner to a heuristic, and a silent-pass heuristic
    is worse than none). It is accepted as a known, narrow residual and
    closed instead by the RUNTIME control-char guard inside ``render_line``/
    ``render_join`` (R2), which fires regardless of what name reached the
    call -- the payload is what R2 kills, not the source-level indirection.
    """

    def test_no_nonliteral_template_in_the_production_package(self) -> None:
        offenders = _scan_for_nonliteral_render_templates(_PACKAGE_ROOT)
        assert not offenders, (
            "render_line/render_join called with a non-literal template/separator:\n"
            + "\n".join(
                f"{site.relative_path}:{site.lineno}: {site.call_name}(...) "
                f"template/separator arg is {site.node_kind}, not a literal str"
                for site in offenders
            )
        )

    # -- scanner self-tests: reproduce every offender shape the audit's
    # row3_exploit.py / row3_nonliteral_template.py fixtures probed at the
    # mypy layer, now at the AST layer -- plus the sanctioned control. --

    def test_scanner_catches_an_fstring_template(self, tmp_path: Path) -> None:
        (tmp_path / "hostile.py").write_text(
            "from loremaster.render import render_line\n"
            "def f(raw, owner):\n"
            "    return render_line(f'row {raw}: {{owner}}', owner=owner)\n"
        )
        sites = _scan_for_nonliteral_render_templates(tmp_path)
        assert any(s.call_name == "render_line" and s.node_kind == "JoinedStr" for s in sites)

    def test_scanner_catches_a_plain_str_variable_template(self, tmp_path: Path) -> None:
        (tmp_path / "hostile.py").write_text(
            "from loremaster.render import render_line\n"
            "def f(owner):\n"
            "    tpl = 'owner: {owner}'\n"
            "    return render_line(tpl, owner=owner)\n"
        )
        sites = _scan_for_nonliteral_render_templates(tmp_path)
        assert any(s.call_name == "render_line" and s.node_kind == "Name" for s in sites)

    def test_scanner_catches_a_string_concatenation_template(self, tmp_path: Path) -> None:
        (tmp_path / "hostile.py").write_text(
            "from loremaster.render import render_line\n"
            "def f(raw):\n"
            "    return render_line('row ' + raw, x=raw)\n"
        )
        sites = _scan_for_nonliteral_render_templates(tmp_path)
        assert any(s.call_name == "render_line" and s.node_kind == "BinOp" for s in sites)

    def test_scanner_catches_a_nonliteral_join_separator_passed_positionally(
        self, tmp_path: Path
    ) -> None:
        (tmp_path / "hostile.py").write_text(
            "from loremaster.render import render_join\n"
            "def f(sep, parts):\n"
            "    return render_join(sep, parts)\n"
        )
        sites = _scan_for_nonliteral_render_templates(tmp_path)
        assert any(s.call_name == "render_join" and s.node_kind == "Name" for s in sites)

    def test_scanner_catches_a_nonliteral_join_separator_passed_by_keyword(
        self, tmp_path: Path
    ) -> None:
        # render_join's ``separator`` parameter is NOT positional-only in the
        # current signature (unlike render_line's ``template``), so
        # args[0]-only inspection would miss this call shape -- a real gap
        # found while implementing this pin, closed here as defense-in-depth
        # beyond the brief's literal args[0] wording.
        (tmp_path / "hostile.py").write_text(
            "from loremaster.render import render_join\n"
            "def f(sep, parts):\n"
            "    return render_join(separator=sep, parts=parts)\n"
        )
        sites = _scan_for_nonliteral_render_templates(tmp_path)
        assert any(s.call_name == "render_join" and s.node_kind == "Name" for s in sites)

    def test_scanner_accepts_the_sanctioned_literal_idiom(self, tmp_path: Path) -> None:
        (tmp_path / "clean.py").write_text(
            "from loremaster.render import render_line, render_join\n"
            "def f(owner, parts):\n"
            "    render_line('owner: {owner}', owner=owner)\n"
            "    render_join(', ', parts)\n"
        )
        assert _scan_for_nonliteral_render_templates(tmp_path) == []

    def test_scanner_ignores_an_unrelated_call(self, tmp_path: Path) -> None:
        (tmp_path / "benign.py").write_text("x = str('a')\n")
        assert _scan_for_nonliteral_render_templates(tmp_path) == []


def assert_actions_covered(
    actions: Iterable[str],
    cases: Iterable[RenderCase],
    exemptions: Mapping[str, str],
) -> None:
    """Fail loudly unless every entry in ``actions`` is COVERED.

    Covered means either: a registered :class:`RenderCase` whose
    ``label``'s family (``label.split(".", 1)[0]``) equals the action name,
    OR an entry in ``exemptions`` naming a non-blank reason. Default is FAIL
    -- an action absent from both is never silently treated as fine; a
    dispatch table's completeness is proven by a positive record, not
    assumed by omission (mirrors ``TestRenderInjectionRegistry``'s
    completeness pin one level up: a dispatch table, not a hand-maintained
    expected-set).
    """
    covered_families = {case.label.split(".", 1)[0] for case in cases}
    missing = [
        action for action in actions if action not in covered_families and action not in exemptions
    ]
    assert not missing, (
        "action(s) with no RenderCase and no exemption-with-reason: "
        f"{missing!r} (register a RenderCase or add an exemption entry naming why)"
    )
    blank_reasons = [action for action, reason in exemptions.items() if not reason.strip()]
    assert not blank_reasons, f"exemption(s) with a blank/whitespace-only reason: {blank_reasons!r}"


async def _stub_render(value: str, _ctx: object) -> str:
    return value


def _case(label: str) -> RenderCase:
    return RenderCase(label, _stub_render)


class TestAssertActionsCovered:
    """Unit tests for the reusable completeness helper itself -- covered,
    missing, and exempted paths (brief item: "Unit-test the helper itself")."""

    def test_action_with_a_registered_case_passes(self) -> None:
        assert_actions_covered(["drain"], [_case("drain.body")], {})

    def test_action_matched_by_family_not_the_full_label(self) -> None:
        # Multiple fields under one action's family all satisfy coverage --
        # the pin is per-ACTION, not per-field.
        assert_actions_covered(
            ["drain"], [_case("drain.body"), _case("drain.sender")], {}
        )

    def test_action_missing_both_case_and_exemption_fails_naming_it(self) -> None:
        with pytest.raises(AssertionError, match="drain"):
            assert_actions_covered(["drain"], [], {})

    def test_action_with_an_exemption_and_a_reason_passes(self) -> None:
        assert_actions_covered(["fleet"], [], {"fleet": "counts/ints only, no free text"})

    def test_exemption_with_a_blank_reason_fails(self) -> None:
        with pytest.raises(AssertionError, match="fleet"):
            assert_actions_covered(["fleet"], [], {"fleet": "   "})

    def test_unrelated_case_does_not_accidentally_cover_a_different_action(self) -> None:
        with pytest.raises(AssertionError, match="fleet"):
            assert_actions_covered(["fleet"], [_case("drain.body")], {})

    def test_multiple_actions_partially_covered_names_only_the_gap(self) -> None:
        with pytest.raises(AssertionError) as exc_info:
            assert_actions_covered(
                ["drain", "fleet"], [_case("drain.body")], {}
            )
        message = str(exc_info.value)
        assert "fleet" in message
        assert "drain" not in message
