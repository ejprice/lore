"""Contract — finding #210: a ``$``-anchored regex is never VALIDATED with ``.match``.

THE DEFECT (measured 2026-07-25, fixed in this same commit)
-----------------------------------------------------------
``AppContext._validate_comms_charset`` guarded every comms identity with
``AGENT_NAME_PATTERN.match(value)`` against ``r"^[a-z0-9][a-z0-9_-]{0,63}$"``.
Python's ``$`` matches at end-of-string **OR immediately before a trailing
newline**, so ``"scout\\n"`` PASSED a guard whose entire job is a closed
charset — and ``"scout" != "scout\\n"``, so the store minted it a DIFFERENT
``uuid5`` row id while the two render identically in any surface where a
trailing newline is invisible (a fleet table cell, a log line, a report).
That is the consumer law's failure mode: the agent reading the surface cannot
tell the two identities apart.

Behavioural pin for the instance:
``test_comms_tool.py::TestCommsDispatchCharsetValidation::
test_a_trailing_newline_agent_name_is_rejected`` (+ its session/brief-name
siblings). THIS file is the CLASS instrument — *"a fix without an invariant is
half a fix"* (CLAUDE.md), and this class is mechanical, greppable, and rarely
alone.

THE THREAT MODEL — who this gate is for
---------------------------------------
It catches the **HONEST DEVELOPER** who writes a ``^...$`` charset validator and
reaches for ``.match`` — the more familiar name, and the one every tutorial
uses — thereby shipping a validator with a trailing-newline hole. That is
finding #210 verbatim.

It is **NOT** a security boundary against a hostile author: anyone who can
commit here can write ``re.compile(build_pattern()).match(x)`` and be invisible
to any AST scan. *"A clever author evades it"* is therefore **not a defect for
this gate**; *"an honest engineer's charset validator silently accepts a
trailing newline"* **is**.

DENY BY DEFAULT, ALLOWLIST THE SAFE
-----------------------------------
Per CLAUDE.md's most expensive lesson (*"when you catch yourself enumerating
what is FORBIDDEN, you have already lost — the forbidden set is unbounded; the
SAFE set is small and enumerable"*), every ``$``-anchored-pattern + ``.match``
pair is a FAILURE unless it appears in :data:`_ALLOWED_ANCHORED_MATCH` with a
written, evidence-backed reason. A new one fails until someone adjudicates it.

KNOWN BOUNDS — what this scan CANNOT see (stated, not implied)
--------------------------------------------------------------
* A pattern literal built at runtime (f-string, concatenation, ``.format``) —
  the AST holds no string to inspect.
* A compiled pattern stored somewhere other than a module-level NAME (a dict
  value, a list element, an instance attribute) — the ``.match`` receiver is
  not a ``Name`` this scan can resolve.
* The map is keyed on the bare NAME, repo-wide, so two modules defining the
  same name with different patterns would collapse into one entry. Today every
  such name is a distinctive ``UPPER_SNAKE`` constant; the coverage assertion
  in :class:`TestScanCoverage` is what would notice a silent loss.
* ``.search()`` is deliberately out of scope — it is never a validation idiom
  in this repo (it is used for deliberately-unanchored scanning, e.g.
  ``CONTROL_CHAR_PATTERN.search``).

How to run:
    uv run pytest loremaster/tests/test_anchored_pattern_seam.py -n auto -q
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]

# Every production tree the gate covers. Test trees are excluded deliberately:
# a test may legitimately assert ``.match`` behaviour ABOUT a pattern (e.g.
# ``test_agent_registry.py``'s hazard pin, which exists precisely to document
# that ``.match`` is insufficient here).
_SCANNED_ROOTS: tuple[Path, ...] = (
    _REPO_ROOT / "loremaster" / "loremaster",
    _REPO_ROOT / "lorescribe" / "lorescribe",
    _REPO_ROOT / "loresigil" / "loresigil",
    _REPO_ROOT / "scripts",
)

# The SAFE set. Keyed by the compiled pattern's NAME; the value is the
# evidence-backed reason ``.match`` is correct there — never "it looked fine".
_ALLOWED_ANCHORED_MATCH: dict[str, str] = {
    "_TASK_ID_SHAPE_PATTERN": (
        "INVERTED guard: server.py's create_many REJECTS a batch key that matches "
        "(i.e. one shaped like a minted 32-hex task id), so ``$``'s trailing-newline "
        "leniency errs toward rejecting MORE, never toward accepting a hazard. "
        "``fullmatch`` here would be a REGRESSION: TaskSpecItem.key is an unconstrained "
        "``str``, so '<32hex>\\n' can arrive, and accepting it as a batch-local key "
        "re-creates exactly the id/key ambiguity the guard exists to prevent — a "
        "blocked_by of '<32hex>' would pass through as a pre-existing task id while "
        "'<32hex>\\n' resolved to a sibling's minted id, invisibly. "
        "PROBED 2026-07-26, not merely argued (with a positive control): "
        "TaskSpecItem.model_fields['key'] carries annotation `str | None` and metadata `[]` "
        "— genuinely unconstrained — and TaskSpecItem(key=<32hex>+NL) constructs. Against "
        "that value the shipped `.match` REJECTS it as id-shaped; `.fullmatch` ACCEPTS it as "
        "a key. Control: a bare uuid4().hex is REJECTED by BOTH, so the probe discriminates "
        "and the difference is scoped to exactly the trailing-newline value."
    ),
    "_HEADING_LINE": (
        "NOT A VALIDATOR: lorescribe/markdown.py's _parse_sections EXTRACTS a heading's "
        "depth and text from a line, and its input is `source.splitlines()` output, which "
        "cannot contain a line terminator by construction — so ``$`` has no trailing "
        "newline to be lenient about, and nothing downstream treats the matched INPUT as "
        "an identity (only group(1)/group(2) are read). MEASURED 2026-07-25 over this "
        "repo's own markdown corpus — 215 files, 65,786 lines: ``.match`` and "
        "``.fullmatch`` agreed on every line, both on match/no-match and on the extracted "
        "groups (0 disagreements). Left as ``.match`` deliberately: churning a working "
        "parser in another package to satisfy this gate is the false-positive tax that "
        "gets gates switched off."
    ),
}


@dataclass(frozen=True)
class _AnchoredMatchUse:
    """One ``.match`` call against an end-anchored pattern."""

    path: str
    lineno: int
    pattern_name: str
    pattern: str

    def __str__(self) -> str:
        return f"{self.path}:{self.lineno} — {self.pattern_name} = {self.pattern!r}"


def _ends_with_end_anchor(pattern: str) -> bool:
    """True when ``pattern`` ends in an UNESCAPED ``$`` (the end-of-line anchor).

    A trailing ``\\$`` is a literal dollar sign, not an anchor, so the count of
    backslashes immediately preceding the final ``$`` decides it: an even count
    (including zero) leaves the ``$`` unescaped.
    """
    if not pattern.endswith("$"):
        return False
    body = pattern[:-1]
    preceding_backslashes = len(body) - len(body.rstrip("\\"))
    return preceding_backslashes % 2 == 0


def _is_re_call(node: ast.AST | None, function_name: str) -> bool:
    """True when ``node`` is a call to ``re.<function_name>(...)``.

    ``None`` is accepted because a bare ``AnnAssign`` (``NAME: re.Pattern[str]``
    with no value) carries ``node.value is None``.
    """
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == function_name
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "re"
    )


def _first_string_argument(call: ast.Call) -> str | None:
    """The call's first positional argument when it is a plain string literal."""
    if not call.args:
        return None
    first = call.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _anchored_pattern_names(trees: dict[str, ast.Module]) -> dict[str, str]:
    """Map ``NAME -> pattern`` for every ``NAME = re.compile("...$")`` found.

    Built across ALL scanned trees at once, because the defect's own shape is
    CROSS-MODULE: ``AGENT_NAME_PATTERN`` is defined in ``agents.py`` and called
    in ``server.py``. A per-file scan could not have seen finding #210.
    """
    anchored: dict[str, str] = {}
    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AnnAssign):
                targets = [node.target]
            else:
                continue
            if not _is_re_call(node.value, "compile"):
                continue
            assert isinstance(node.value, ast.Call)  # narrowed by _is_re_call
            pattern = _first_string_argument(node.value)
            if pattern is None or not _ends_with_end_anchor(pattern):
                continue
            for target in targets:
                if isinstance(target, ast.Name):
                    anchored[target.id] = pattern
    return anchored


def _anchored_match_uses(trees: dict[str, ast.Module]) -> list[_AnchoredMatchUse]:
    """Every ``.match`` call in ``trees`` whose pattern is end-anchored.

    Three shapes are recognised — the ones an honest author actually writes:
    a module-level compiled constant (``NAME.match(x)``), an inline compile
    (``re.compile("...$").match(x)``), and the module-level function
    (``re.match("...$", x)``).
    """
    anchored = _anchored_pattern_names(trees)
    uses: list[_AnchoredMatchUse] = []
    for path, tree in trees.items():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            # Shape 3: re.match("...$", value)
            if _is_re_call(node, "match"):
                pattern = _first_string_argument(node)
                if pattern is not None and _ends_with_end_anchor(pattern):
                    uses.append(_AnchoredMatchUse(path, node.lineno, "re.match", pattern))
                continue
            if not isinstance(node.func, ast.Attribute) or node.func.attr != "match":
                continue
            receiver = node.func.value
            # Shape 1: NAME.match(value), NAME bound to an anchored re.compile.
            if isinstance(receiver, ast.Name) and receiver.id in anchored:
                uses.append(
                    _AnchoredMatchUse(path, node.lineno, receiver.id, anchored[receiver.id])
                )
            # Shape 2: re.compile("...$").match(value)
            elif _is_re_call(receiver, "compile"):
                assert isinstance(receiver, ast.Call)  # narrowed by _is_re_call
                pattern = _first_string_argument(receiver)
                if pattern is not None and _ends_with_end_anchor(pattern):
                    uses.append(
                        _AnchoredMatchUse(path, node.lineno, "re.compile(...)", pattern)
                    )
    return uses


def _parse_production_trees() -> dict[str, ast.Module]:
    """Parse every production ``*.py`` under :data:`_SCANNED_ROOTS`."""
    trees: dict[str, ast.Module] = {}
    for root in _SCANNED_ROOTS:
        if not root.is_dir():
            continue
        for source_path in sorted(root.rglob("*.py")):
            relative = source_path.relative_to(_REPO_ROOT).as_posix()
            trees[relative] = ast.parse(source_path.read_text(encoding="utf-8"))
    return trees


@pytest.fixture(scope="module")
def production_trees() -> dict[str, ast.Module]:
    return _parse_production_trees()


class TestNoAnchoredPatternValidatedWithMatch:
    """The invariant: ``$``-anchored + ``.match`` is a failure unless allowlisted."""

    def test_every_anchored_match_use_is_allowlisted(
        self, production_trees: dict[str, ast.Module]
    ) -> None:
        unexplained = [
            use
            for use in _anchored_match_uses(production_trees)
            if use.pattern_name not in _ALLOWED_ANCHORED_MATCH
        ]
        assert not unexplained, (
            "A ``$``-anchored pattern is validated with ``.match`` (finding #210). "
            "Python's ``$`` also matches immediately before a TRAILING NEWLINE, so "
            "``.match`` accepts 'value\\n' against a pattern that reads as a closed "
            "charset — two identities that render identically. Use ``.fullmatch`` "
            "(intent-revealing, and immune to a later edit of the pattern's anchors). "
            "If ``.match`` is genuinely correct here — e.g. an INVERTED guard where "
            "matching means REJECT, so the leniency errs safe — add the pattern name "
            "to _ALLOWED_ANCHORED_MATCH with the evidence. Offenders:\n  "
            + "\n  ".join(str(use) for use in unexplained)
        )

    def test_the_allowlist_carries_no_dead_entries(
        self, production_trees: dict[str, ast.Module]
    ) -> None:
        """An exemption for a pattern that no longer does this is a stale licence.

        Deleting it costs nothing and keeps the SAFE set honest — an allowlist
        nobody prunes is how a future ``.match`` inherits an exemption written
        for code that has since been rewritten.
        """
        live = {use.pattern_name for use in _anchored_match_uses(production_trees)}
        stale = sorted(set(_ALLOWED_ANCHORED_MATCH) - live)
        assert not stale, (
            f"_ALLOWED_ANCHORED_MATCH exempts {stale}, which no longer validate an "
            "end-anchored pattern with ``.match`` — delete the entries."
        )


class TestScanCoverage:
    """A gate is an invariant only over code it actually SEES.

    These assertions make the scan's REACH a checked variable rather than an
    assumption: a scanner that silently parsed nothing, or silently stopped
    resolving compiled constants, would otherwise pass vacuously forever.
    """

    def test_the_scan_reaches_every_production_tree(
        self, production_trees: dict[str, ast.Module]
    ) -> None:
        scanned_packages = {path.split("/", 1)[0] for path in production_trees}
        assert scanned_packages == {"loremaster", "lorescribe", "loresigil", "scripts"}

    def test_the_scan_resolves_the_known_anchored_constants(
        self, production_trees: dict[str, ast.Module]
    ) -> None:
        """Positive control on the RESOLVER: the two end-anchored compiled
        constants this repo actually ships must both be found by name.

        ``AGENT_NAME_PATTERN`` is the #210 pattern (now called with
        ``fullmatch``); ``_TASK_ID_SHAPE_PATTERN`` is the allowlisted inverted
        guard. If either name stops resolving, the gate has gone blind and the
        deny test above would pass for the wrong reason.
        """
        anchored = _anchored_pattern_names(production_trees)
        assert anchored.get("AGENT_NAME_PATTERN") == r"^[a-z0-9][a-z0-9_-]{0,63}$"
        assert anchored.get("_TASK_ID_SHAPE_PATTERN") == r"^[0-9a-f]{32}$"

    def test_the_fixed_call_site_is_not_reported(
        self, production_trees: dict[str, ast.Module]
    ) -> None:
        """#210's own call site must be invisible to the scan now it uses
        ``fullmatch`` — the gate must not keep flagging the fixed code."""
        flagged = {use.pattern_name for use in _anchored_match_uses(production_trees)}
        assert "AGENT_NAME_PATTERN" not in flagged


class TestScannerFiresOnAKnownViolation:
    """POSITIVE CONTROLS — proof the scanner can SEE a violation.

    CLAUDE.md: *"pair every negative result with a POSITIVE CONTROL showing the
    probe firing on a case you know is broken"*. Without these, a green
    :class:`TestNoAnchoredPatternValidatedWithMatch` is indistinguishable from a
    scanner that never matches anything.
    """

    @staticmethod
    def _uses(source: str) -> list[_AnchoredMatchUse]:
        return _anchored_match_uses({"synthetic.py": ast.parse(source)})

    def test_a_module_level_constant_reproducing_finding_210_is_caught(self) -> None:
        uses = self._uses(
            'import re\nNAME_RE = re.compile(r"^[a-z]+$")\n'
            "def check(v):\n    return NAME_RE.match(v)\n"
        )
        assert [use.pattern_name for use in uses] == ["NAME_RE"]

    def test_a_cross_module_constant_is_caught(self) -> None:
        """The defect's actual shape: compiled in one file, called in another."""
        uses = _anchored_match_uses(
            {
                "defines.py": ast.parse('import re\nOTHER_RE = re.compile(r"^[a-z]+$")\n'),
                "uses.py": ast.parse("def check(v):\n    return OTHER_RE.match(v)\n"),
            }
        )
        assert [(use.path, use.pattern_name) for use in uses] == [("uses.py", "OTHER_RE")]

    def test_an_inline_compile_is_caught(self) -> None:
        uses = self._uses('import re\ndef check(v):\n    return re.compile(r"^[a-z]+$").match(v)\n')
        assert [use.pattern_name for use in uses] == ["re.compile(...)"]

    def test_the_module_level_function_is_caught(self) -> None:
        uses = self._uses('import re\ndef check(v):\n    return re.match(r"^[a-z]+$", v)\n')
        assert [use.pattern_name for use in uses] == ["re.match"]

    def test_an_annotated_assignment_is_caught(self) -> None:
        """``AGENT_NAME_PATTERN`` is an ``AnnAssign`` — a scan that only walked
        plain ``Assign`` nodes would have missed finding #210 entirely."""
        uses = self._uses(
            "import re\n"
            'NAME_RE: re.Pattern[str] = re.compile(r"^[a-z]+$")\n'
            "def check(v):\n    return NAME_RE.match(v)\n"
        )
        assert [use.pattern_name for use in uses] == ["NAME_RE"]


class TestScannerDoesNotRefuseHonestCode:
    """NEGATIVE CONTROLS — a gate that refuses honest code gets SWITCHED OFF.

    Each case below is legitimate code that must NOT be reported, so the
    positive controls above cannot be satisfied by a scanner that simply flags
    every ``.match``.
    """

    @staticmethod
    def _uses(source: str) -> list[_AnchoredMatchUse]:
        return _anchored_match_uses({"synthetic.py": ast.parse(source)})

    def test_fullmatch_on_an_anchored_pattern_is_clean(self) -> None:
        assert not self._uses(
            'import re\nNAME_RE = re.compile(r"^[a-z]+$")\n'
            "def check(v):\n    return NAME_RE.fullmatch(v)\n"
        )

    def test_match_on_a_prefix_only_pattern_is_clean(self) -> None:
        """``lorescribe``'s JS/markdown chunkers match ``^``-anchored prefixes
        deliberately — ``.match`` is the CORRECT idiom there."""
        assert not self._uses(
            'import re\nHEAD_RE = re.compile(r"^\\s*(#{1,6})")\n'
            "def check(v):\n    return HEAD_RE.match(v)\n"
        )

    def test_search_on_an_anchored_pattern_is_clean(self) -> None:
        assert not self._uses(
            'import re\nNAME_RE = re.compile(r"^[a-z]+$")\n'
            "def check(v):\n    return NAME_RE.search(v)\n"
        )

    def test_a_literal_dollar_is_not_an_anchor(self) -> None:
        """``r"...\\$"`` ends in an ESCAPED dollar — a currency sign, not an
        end-of-line anchor — so ``.match`` on it is not this defect."""
        assert not self._uses(
            'import re\nPRICE_RE = re.compile(r"^[0-9]+\\$")\n'
            "def check(v):\n    return PRICE_RE.match(v)\n"
        )

    def test_an_unrelated_match_receiver_is_clean(self) -> None:
        """``.match`` is a common method name; only receivers bound to an
        anchored compiled pattern count."""
        assert not self._uses("def check(matcher, v):\n    return matcher.match(v)\n")


class TestEndAnchorDetection:
    """Unit-level pins on :func:`_ends_with_end_anchor`, the one place a
    mis-read decides whether the whole gate looks at a pattern at all."""

    @pytest.mark.parametrize(
        "pattern", [r"^[a-z]+$", r"$", r"^a\\$", r"^[0-9a-f]{32}$", r"^(#{1,6})\s+(.*\S)\s*$"]
    )
    def test_unescaped_trailing_dollar_is_an_anchor(self, pattern: str) -> None:
        assert _ends_with_end_anchor(pattern)

    @pytest.mark.parametrize("pattern", [r"^[a-z]+", r"^a\$", r"", r"$x", r"^a\\\$"])
    def test_no_unescaped_trailing_dollar(self, pattern: str) -> None:
        assert not _ends_with_end_anchor(pattern)
