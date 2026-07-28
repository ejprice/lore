"""AST-level runtime-string hygiene invariant (P8d dead-name defect class, take 2).

``test_mcp_server.py::TestNoDeadToolNamesInAgentFacingText`` closed the defect
class for text FastMCP actually SERVES to a connecting agent (the server
``instructions``, tool descriptions, per-parameter field descriptions). That
pin cannot see RUNTIME strings the server never registers as tool metadata —
error messages an exception carries, log lines, module/class/function
docstrings, inline comments. Two of the P8d flip-wave audits' confirmed
defects lived exactly there: an error message that told a caller to "run
reindex" after ``reindex`` had been folded (bare, un-prefixed) into
``lore_index``, and a stale docstring claiming a ``reindex(tier=…)`` escape
hatch that no longer exists as a callable (the real call is
``Indexer.index_tier``). Both were fixed as part of landing this test (see
REPORT-builder-hygiene-ast.md for the fix inventory) — this module is the
invariant that stops the class from recurring, not just a record of the fix.

This walks EVERY ``.py`` file under the shipped ``loremaster/loremaster``
package (never ``tests/`` — a test file legitimately says "reindex" while
naming what it tests) with :mod:`ast`, and inspects every string-literal
constant — plain strings, docstrings, AND the literal text segments of
f-strings (``JoinedStr``'s ``Constant`` children, which a plain ``ast.walk``
already visits without any special-casing) — for two defect tiers:

Tier 1 — ``lore_``-shaped tokens naming a tool that is not on the CURRENT
14-tool surface. The live set is IMPORTED from ``test_mcp_server`` (the exact
same ``_ALL_BUILTIN_TOOL_NAMES`` the registration-equality pin freezes), not a
hand-copied duplicate — a future surface change updates one place and both
pins move together automatically.

Tier 2 — bare (non-``lore_``-prefixed) retired verbs: the pre-prefix tool
names a P8d wave renamed or folded away. Naively banning all ten candidate
stems as bare words is untenable: seven of them ALSO name a live Python
identifier that legitimately survives internally (``SearchPipeline.search_code``,
``ReadFileTool.read_file``, and the four ``SurrealCodeGraph`` graph-engine
methods ``what_imports``/``blast_radius``/``tests_for``/``references``, plus
``Indexer.index_status``) — banning those outright would force dozens of
per-file whitelist entries for ordinary, honest engine-method documentation
(``references`` alone is common-English-word-shaped and appears in a dozen+
files as a plain noun). Rather than hand-maintain that exclusion list (which
would silently drift the moment one of those methods is itself renamed), this
module derives it MECHANICALLY from the SAME ast walk: it also collects every
currently-defined function/method/class name across the package, and only
enforces a candidate stem when NO living identifier of that exact name exists
today. That currently leaves exactly three enforced stems — ``save_memory``,
``recall_memory``, ``reindex`` — each verified to have zero surviving ``def``
anywhere in the tree; ``test_the_seven_survivor_stems_are_the_expected_set``
below pins the derived exclusion set so a future rename that deletes one of
the seven survivors is NOT silently absorbed — it starts failing loudly on
its very next appearance as a bare word, and a reviewer sees exactly why the
enforced set grew.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

import pytest
import test_mcp_server  # the exact-set pin's own derivation of the live tool surface

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent / "loremaster"

_LORE_TOKEN = re.compile(r"\blore_[a-z_]+\b")

# The ten pre-prefix / pre-fold bare verbs a P8d wave renamed or folded away.
# See the module docstring: seven of these also name a currently-living Python
# identifier and are excluded from enforcement mechanically, not by hand.
_RETIRED_BARE_STEMS: frozenset[str] = frozenset(
    {
        "search_code",
        "save_memory",
        "recall_memory",
        "read_file",
        "what_imports",
        "blast_radius",
        "tests_for",
        "references",
        "reindex",
        "index_status",
    }
)

# Tier 1: a ``lore_``-shaped token that is legitimately NOT a tool name, keyed
# globally (not per-file) because the collision is structural to the token
# itself, not to where it happens to appear.
_TIER1_GLOBAL_TOKEN_WHITELIST: frozenset[str] = frozenset(
    {
        # The memory backend's flat-label prefix constant
        # (``_LORE_REF_LABEL_PREFIX = "lore_ref="`` in memory/local.py) — a
        # stored-label convention, never a tool name, referenced throughout
        # memory/backend.py, memory/local.py, server.py, store/surreal_schema.py.
        "lore_ref",
    }
)

# Tier 1: dead lore_-prefixed tool names that appear ONLY inside honest,
# explicitly-historical fold/removal comments (each says "REMOVED"/"folded
# into"/"no longer exists" in the surrounding text) — never agent-facing
# instructions to invoke them.
_TIER1_FILE_TOKEN_WHITELIST: frozenset[tuple[str, str]] = frozenset(
    {
        # server.py:852 / 5105-5106 -- P8d Wave 2 impact-fold history comments.
        ("server.py", "lore_blast_radius"),
        ("server.py", "lore_what_imports"),
        ("server.py", "lore_tests_for"),
        ("server.py", "lore_references"),
        # server.py:4244 -- "lore_reindex no longer exists as a separate tool."
        ("server.py", "lore_reindex"),
    }
)

# Tier 2: whitelist for the three mechanically-enforced stems (save_memory,
# recall_memory, reindex — see module docstring). Every entry is a bare
# mention verified NOT to instruct a reader to invoke a dead capability.
_TIER2_WHITELIST: frozenset[tuple[str, str]] = frozenset(
    {
        # server.py:1074 -- "The v0.3 ``save_memory`` carried a free-form
        # ``metadata`` dict; the v2 backend ..." -- an explicit v0.3-vs-v2
        # historical contrast, not current guidance.
        ("server.py", "save_memory"),
        # search.py:536 -- "(the retired ``MemoryStore.recall_memory`` shape
        # is gone)." -- explicitly marked retired/gone.
        ("search.py", "recall_memory"),
        # index/watcher.py -- "Enqueue a reindex for ...", "reindex the
        # destination" -- the watcher describing its OWN background action in
        # plain English, not a caller-facing tool reference.
        ("index/watcher.py", "reindex"),
        # diff.py -- "mid-reindex" as an adjective naming a transient manifest
        # lifecycle state (dirty/embedding/failed), not an invocable verb.
        ("diff.py", "reindex"),
        # index/sqlite_resilient.py:305 -- a recovery WARNING log line
        # ("rebuildable by reindex") using the generic English verb, not
        # naming a tool.
        ("index/sqlite_resilient.py", "reindex"),
        # server.py -- every mention is explicitly historical ("the former
        # reindex", "the old reindex ran", "old reindex(tier=...) was") in the
        # lore_index tool's own docstring/description explaining what it
        # subsumed -- never an instruction to invoke a bare ``reindex``.
        ("server.py", "reindex"),
    }
)

_DEFINITION_NODE_TYPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


@dataclass(frozen=True)
class _StringLiteral:
    """One string-literal constant found in the production tree."""

    relative_path: str
    lineno: int
    text: str


def _scan_package() -> tuple[list[_StringLiteral], frozenset[str]]:
    """Walk every ``.py`` file under ``loremaster/loremaster`` once.

    Returns every string-literal constant (docstrings, plain strings, and the
    literal text segments of f-strings) alongside the set of every
    function/method/class name currently DEFINED anywhere in the package —
    the ground truth tier 2 uses to derive which retired stems still have a
    living identifier behind them.
    """
    literals: list[_StringLiteral] = []
    identifiers: set[str] = set()
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        relative_path = str(path.relative_to(_PACKAGE_ROOT))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                literals.append(_StringLiteral(relative_path, node.lineno, node.value))
            elif isinstance(node, _DEFINITION_NODE_TYPES):
                identifiers.add(node.name)
    return literals, frozenset(identifiers)


def _snippet(text: str, start: int, end: int, *, radius: int = 40) -> str:
    """A single-line, whitespace-collapsed excerpt around ``text[start:end]``.

    Failure messages must be actionable from the assertion alone: this keeps
    a huge docstring from dumping wholesale while still showing the offending
    token in its immediate sentence.
    """
    lo = max(0, start - radius)
    hi = min(len(text), end + radius)
    excerpt = " ".join(text[lo:hi].split())
    prefix = "…" if lo > 0 else ""
    suffix = "…" if hi < len(text) else ""
    return f"{prefix}{excerpt}{suffix}"


@pytest.fixture(scope="module")
def _scan() -> tuple[list[_StringLiteral], frozenset[str]]:
    return _scan_package()


class TestNoDeadToolTokensInRuntimeStrings:
    """Tier 1: every ``lore_``-shaped token in any production string literal is live."""

    def test_every_lore_prefixed_token_is_a_live_tool_or_whitelisted(
        self, _scan: tuple[list[_StringLiteral], frozenset[str]]
    ) -> None:
        literals, _identifiers = _scan
        live_tools = test_mcp_server._ALL_BUILTIN_TOOL_NAMES
        offenders: list[str] = []
        for literal in literals:
            for match in _LORE_TOKEN.finditer(literal.text):
                token = match.group(0)
                if token in live_tools:
                    continue
                if token in _TIER1_GLOBAL_TOKEN_WHITELIST:
                    continue
                if (literal.relative_path, token) in _TIER1_FILE_TOKEN_WHITELIST:
                    continue
                snippet = _snippet(literal.text, match.start(), match.end())
                offenders.append(
                    f"{literal.relative_path}:{literal.lineno}: dead/unknown tool "
                    f"token {token!r} -- \"{snippet}\""
                )
        assert not offenders, "runtime string names a dead or unknown lore_ tool:\n" + "\n".join(
            offenders
        )


class TestNoRetiredBareVerbsInRuntimeStrings:
    """Tier 2: retired bare verbs with no surviving Python identifier behind them."""

    def test_the_seven_survivor_stems_are_the_expected_set(
        self, _scan: tuple[list[_StringLiteral], frozenset[str]]
    ) -> None:
        # Pins WHY seven of the ten candidates are excluded from enforcement:
        # each is mechanically derived (a currently-defined identifier), not a
        # hand-maintained guess. If a future rename deletes one of these seven
        # (e.g. the graph engine's ``blast_radius`` method), it drops out of
        # this set and the OTHER test below starts enforcing it on its very
        # next bare-word appearance -- this pin fails first, pointing here.
        _literals, identifiers = _scan
        survivors = _RETIRED_BARE_STEMS & identifiers
        assert survivors == {
            "search_code",
            "read_file",
            "what_imports",
            "blast_radius",
            "tests_for",
            "references",
            "index_status",
        }

    def test_retired_stems_with_no_surviving_identifier_are_whitelisted_or_absent(
        self, _scan: tuple[list[_StringLiteral], frozenset[str]]
    ) -> None:
        literals, identifiers = _scan
        enforced_stems = _RETIRED_BARE_STEMS - identifiers
        assert enforced_stems, (
            "sanity check: at least one retired stem must currently have zero "
            "living identifier -- if this ever empties, tier 2 goes silently "
            "inert; revisit _RETIRED_BARE_STEMS"
        )
        offenders: list[str] = []
        for literal in literals:
            for stem in enforced_stems:
                pattern = re.compile(rf"\b{re.escape(stem)}\b")
                for match in pattern.finditer(literal.text):
                    if (literal.relative_path, stem) in _TIER2_WHITELIST:
                        continue
                    snippet = _snippet(literal.text, match.start(), match.end())
                    offenders.append(
                        f"{literal.relative_path}:{literal.lineno}: retired bare "
                        f"verb {stem!r} -- \"{snippet}\""
                    )
        assert not offenders, (
            "runtime string names a retired bare verb with no living code behind "
            "it:\n" + "\n".join(offenders)
        )


# ---------------------------------------------------------------------------
# Repo-wide BYTE hygiene: no tracked text file may carry a NUL.
#
# Provenance (2026-07-28, packet 11-i-b kickoff, scout-11ib-1 found it BY
# ACCIDENT): `REPORT-contract-11ia-1-fixwave.md` carried a single stray NUL —
# in a sentence *about* NUL escaping, where the author meant to type the
# literal text ``\x00``. One byte, and `file(1)` reclassifies the whole
# archived receipt as ``data``: **plain `grep` then SKIPS it, silently.**
#
# Why that is a defect and not a curiosity. This repo's #1 audited failure
# class is the rename/reshape sweep, and its ruled instrument is a BARE,
# anchor-free grep over the tree — with archived receipts explicitly in scope,
# because a receipt is a durable, citable address (the #152 archiving law).
# A file grep cannot see is a file the sweep cannot see, and the sweep's whole
# job is exhaustiveness. Measured bound, stated honestly rather than inflated:
# lore's index DID ingest this file (10 chunks), so the RAG was never blind —
# the damage is confined to the grep fallback, which is precisely the path
# CLAUDE.md reserves for "rename-exhaustiveness where one missed site
# compiles-but-breaks".
#
# THE INSTRUMENT LESSON, paid for in this very session: the lead's first
# repo-wide scan used ``grep -qP '\x00'`` and reported ZERO hits — a FALSE
# NEGATIVE, because grep classifies such a file as binary and the -q probe
# came back empty-handed. A negative result from an uncontrolled probe is
# worth nothing (CLAUDE.md: "a probe needs a control"). Hence
# ``test_the_detector_can_actually_see_a_NUL`` below: this pin refuses to
# report a clean tree until it has demonstrated, in the same run, that it can
# see a NUL it planted itself.
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]

# Directories that legitimately hold non-source bytes. Kept SHORT and boring on
# purpose: this is the fallback path only. The authoritative enumeration is
# ``git ls-files`` (a DERIVED list, per the repo's registration-sites law —
# never a hand-maintained one); the walk exists so the pin still RUNS where the
# git BINARY is absent, which in this project is not hypothetical (#131: the
# deployed image had no git, and the OSError was swallowed for months).
_WALK_SKIP_DIRS: frozenset[str] = frozenset(
    {".git", ".venv", "__pycache__", "node_modules", ".pytest_cache", ".ruff_cache", ".mypy_cache"}
)

# Suffixes whose files are legitimately binary. A NUL in these is not a defect.
_BINARY_SUFFIXES: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".gz", ".whl", ".so", ".pyc", ".onnx", ".bin"}
)


def _tracked_text_files() -> tuple[list[Path], str]:
    """Every repo file that is meant to be plain text, plus the instrument used.

    Returns ``(paths, instrument)`` so the failure message can say HOW the set
    was derived — a count with no named instrument is the kind of claim this
    repo re-derives rather than trusts.
    """
    import shutil
    import subprocess

    if shutil.which("git") is not None:
        completed = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "ls-files", "-z"],
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode == 0:
            paths = [
                _REPO_ROOT / name
                for name in completed.stdout.split("\0")
                if name and (_REPO_ROOT / name).is_file()
            ]
            return (
                [p for p in paths if p.suffix.lower() not in _BINARY_SUFFIXES],
                "git ls-files",
            )

    walked: list[Path] = []
    for path in _REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _WALK_SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in _BINARY_SUFFIXES:
            continue
        walked.append(path)
    return walked, "filesystem walk (git unavailable)"


class TestNoNulBytesInTrackedTextFiles:
    """A tracked text file with a NUL is invisible to the sweep instrument."""

    def test_the_detector_can_actually_see_a_NUL(self, tmp_path: Path) -> None:
        """POSITIVE CONTROL — the clean-tree verdict below means nothing without it.

        The lead's first attempt at this scan (``grep -qP '\\x00'``) returned a
        confident, wrong "no NUL anywhere" while a NUL sat in a tracked file.
        This test plants one and demands the detector find it, so a clean result
        from the sibling test is a MEASUREMENT rather than a hope.
        """
        planted = tmp_path / "planted.md"
        planted.write_bytes(b"ordinary prose\x00more prose\n")
        assert b"\x00" in planted.read_bytes(), (
            "the control file does not contain the NUL it was built to contain -- "
            "the instrument cannot be trusted in either direction"
        )

        clean = tmp_path / "clean.md"
        clean.write_bytes(b"ordinary prose, no NUL\n")
        assert b"\x00" not in clean.read_bytes(), (
            "the detector reports a NUL in a file that has none -- it would flag "
            "the whole tree and teach everyone to switch it off"
        )

    def test_no_tracked_text_file_contains_a_NUL(self) -> None:
        paths, instrument = _tracked_text_files()

        # Coverage is a CHECKED variable, not an assumption: a guard is an
        # invariant only over the files it actually READS. A broken enumeration
        # would otherwise pass vacuously and read as "the tree is clean".
        assert len(paths) > 200, (
            f"the file enumeration ({instrument}) found only {len(paths)} text "
            f"files under {_REPO_ROOT}; this repo has far more, so the scan is "
            f"broken and its clean verdict would be vacuous"
        )

        offenders: list[str] = []
        for path in paths:
            try:
                blob = path.read_bytes()
            except OSError:  # pragma: no cover - unreadable file is not this pin's business
                continue
            count = blob.count(b"\x00")
            if count:
                index = blob.index(b"\x00")
                line = blob[:index].count(b"\n") + 1
                offenders.append(
                    f"{path.relative_to(_REPO_ROOT).as_posix()}: {count} NUL byte(s), "
                    f"first at line {line}"
                )

        assert not offenders, (
            f"a tracked text file carries a NUL byte, which makes `file(1)` call it "
            f"`data` and makes plain `grep` SKIP IT SILENTLY -- so this repo's ruled "
            f"rename-sweep instrument (a bare, anchor-free grep over the tree, archived "
            f"receipts included) goes blind on it without saying so. Enumerated by "
            f"{instrument}; {len(paths)} files scanned.\n"
            + "\n".join(offenders)
            + "\n\nFix: replace the raw NUL with the text that was meant (usually the "
            "literal escape `\\x00`). If a file must genuinely hold NULs, give it a "
            "binary suffix or add that suffix to _BINARY_SUFFIXES -- deliberately, in a "
            "diff a reviewer can see."
        )
