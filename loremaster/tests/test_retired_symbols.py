"""THE DELETED-SYMBOL HYGIENE INVARIANT — a repo-wide gate on prose that names code
which no longer exists.

WHY THIS MODULE EXISTS. This repo's own CLAUDE.md names its #1 defect class:
*"natural-language surfaces whose consistency with code no gate checks."* It then
says, in standing law: *"When a defect CLASS is identified, ship the INSTRUMENT in
the same breath as the law"* and *"a fix without an invariant is half a fix."*

The law was written. The instrument never was. So the class shipped again — in the
very commit that fixes finding #102. That commit deletes ``_apply_mint``, the four
``_REPORT_MINT_*`` constants and ``_TXN_CONFLICT_BACKOFF_SECONDS``, and leaves live
references to them scattered across the tree. The worst is not a stale comment; it is
**standing law**::

    docs/plans/v2/DESIGN-LAW.md:75
      "`findings.py::_apply_mint` (bounded app-retry, deterministic jitter) is the
       reference pattern for ANY new hot-row mint"

That sentence names a **deleted** method and prescribes **the exact defect #102
exists to remove** (a deterministic, id-derived jitter — the lockstep that makes N
racers re-collide). A future agent obeying standing law would faithfully rebuild the
bug. Four of these sites were flagged by a cold audit and shipped anyway, because a
flag is not a gate.

This module is the gate.

------------------------------------------------------------------------------
DESIGN — and why it is a REGISTRY, not a derived scan.

The obvious instrument is: "extract every symbol-shaped token from prose, and flag any
that is not defined in the codebase." **I built that and measured it: 83 candidate
offenders, of which about four are real.** It flags ``ValueError``, ``RecordID``,
``FakeEmbedder``, ``Observer`` (a watchdog class), ``_surreal_harness`` (a module, not
a symbol)... A pin that cries wolf 79 times gets deleted by the first engineer it
annoys — which is strictly worse than no pin. (I learned this the expensive way: three
earlier revisions of the #102 contract shipped ever-more-elaborate AST scanners, and a
cold adversary walked through every one of them.)

So the instrument is a **small, enumerable, self-cleaning registry**: the names this
repo has deliberately RETIRED. Precision is 100% by construction — we only search for
names we KNOW are gone. Recall is bounded by the registry, and
:meth:`TestRetiredSymbolRegistryIsHonest.test_every_retired_symbol_is_really_gone`
keeps the registry from becoming fiction (the same disease as the dead ``"assert"``
marker: a claim about the code that no gate ever checked).

**Matching is BARE and ANCHOR-FREE** — CLAUDE.md is explicit that prose mentions carry
no structural anchors, and anchored patterns "systematically miss exactly the sites
gates can't see". The live sites prove it: the same symbol appears as ``_apply_mint``,
```findings.py::_apply_mint```, ```findings.py _apply_mint``` (a space!),
``_REPORT_MINT_*`` (a glob) and ``_txn._TXN_CONFLICT_BACKOFF_SECONDS`` (dotted). Only a
bare substring sees all five.

------------------------------------------------------------------------------
WHAT THIS GATE DOES **NOT** CATCH — stated here on purpose (operator ruling,
2026-07-13), because a gate that overstates its reach is the very thing it polices.

**It catches a retired NAME. It cannot catch a stale NUMERIC CLAIM about one.**

    briefs.py:157   "Budget 4 (not findings' 12)"

That sentence is wrong — findings' 12 was ``_REPORT_MINT_MAX_ATTEMPTS``, and it no
longer exists — but it **names no symbol**, so no name-based instrument can see it, and
a value-based one would fire on every number in the repo. Such sites must be found and
fixed BY HAND, and this gate will not enforce them.

**This class is therefore NOT fully closed, and this module does not pretend it is.**
Saying so is the whole lesson of the dead ``"assert"`` marker, which claimed a coverage
it had never once had.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PACKAGE_ROOT = _REPO_ROOT / "loremaster" / "loremaster"
_TESTS_ROOT = _REPO_ROOT / "loremaster" / "tests"
_DOCS_ROOT = _REPO_ROOT / "docs"

# ---------------------------------------------------------------------------
# THE REGISTRY. Add a name here the moment you delete it — that is the whole
# discipline, and it costs one line. Each entry is a BARE substring, matched
# anchor-free, with the reason it was retired (so the next reader knows why the
# name must not come back, not merely that it left).
# ---------------------------------------------------------------------------
_RETIRED_SYMBOLS: dict[str, str] = {
    "_apply_mint": (
        "findings.py's hand-rolled mint backstop. Its retry was gated on a substring of "
        "a classification LABEL, so finding #93's relabelling silently killed it — it "
        "never executed a single retry. DELETED by finding #102; the shared seam owns "
        "the retry now. Anything citing it as a pattern is prescribing the bug."
    ),
    "_REPORT_MINT": (
        "the four _REPORT_MINT_* constants that tuned that dead loop (max attempts, "
        "backoff, and a 16-SLOT deterministic jitter derived from the finding id — the "
        "lockstep #102 exists to remove). DELETED with it. Prefix, so the glob form "
        "`_REPORT_MINT_*` is caught too."
    ),
    "_TXN_CONFLICT_BACKOFF_SECONDS": (
        "the seam's deterministic linear backoff. Every racer slept the identical "
        "duration and re-collided in lockstep. REPLACED by per-attempt full jitter "
        "(finding #102)."
    ),
    "_BRIEF_PUBLISH_": (
        "the four private mint-retry constants briefs.py hand-rolled because the "
        "substrate offered nothing to call: _BRIEF_PUBLISH_MAX_ATTEMPTS (4), "
        "_BRIEF_PUBLISH_BACKOFF_SECONDS, and a FOUR-SLOT deterministic jitter table "
        "(_BRIEF_PUBLISH_JITTER_SLOTS / _BRIEF_PUBLISH_JITTER_SECONDS) — at the "
        "contract's own 8-way contention the pigeonhole guarantees two racers share a "
        "slot and then stay lockstepped for the entire ladder. DELETED by finding #108; "
        "the shared _txn.retry_on_conflict driver owns the policy now. A PREFIX, so all "
        "four are caught by one entry (the _REPORT_MINT precedent). Anything citing "
        "these as a budget is quoting a number nobody chose any more."
    ),
    "_BRIEF_MINT_MAX_ATTEMPTS": (
        "the product (_BRIEF_PUBLISH_MAX_ATTEMPTS * _MAX_TXN_CONFLICT_ATTEMPTS = 20) "
        "that drove briefs' hand-rolled mint loop. It inherited the SEAM's attempt "
        "floor for an unrelated purpose — finding #102's own trap, a constant tuned for "
        "one thing and silently borrowed by another. DELETED by finding #108. The floor "
        "(_MAX_TXN_CONFLICT_ATTEMPTS) SURVIVES and keeps its value of 5; what is gone is "
        "every consumer of it outside the seam that owns it."
    ),
}

# ---------------------------------------------------------------------------
# The ONLY files allowed to name a retired symbol: those whose JOB is to prove it
# is gone. A pin that asserts `not hasattr(FindingLedger, "_apply_mint")` must, of
# necessity, spell the name.
#
# This list is the invariant's only blind spot, so it is kept as short as it can
# be and every entry is justified — and
# `test_every_allowlisted_file_still_enforces_a_retirement` makes it SELF-CLEANING:
# an entry that stops enforcing anything must be deleted, so a stale exemption can
# never quietly grandfather a real dangling reference.
# ---------------------------------------------------------------------------
_RETIREMENT_ENFORCERS: dict[str, str] = {
    "loremaster/tests/test_retired_symbols.py": "this module — it IS the registry",
    "loremaster/tests/test_findings.py": (
        "the deletion pins (TestMintBackstopIsDeleted) assert the symbols are gone; "
        "they must name them to do so"
    ),
}

# Files we scan: all package + test Python, and all docs markdown. Docs are IN scope
# deliberately — DESIGN-LAW.md is exactly where the most dangerous instance lives, and
# a gate that only looked at code would have missed it completely.
_SCANNED_SUFFIXES = frozenset({".py", ".md"})


# ---------------------------------------------------------------------------
# LIVE documents vs DATED RECORDS — a MECHANICAL rule, deliberately not a
# hand-maintained list of exceptions (operator ruling, 2026-07-13).
#
# The two kinds of prose fail differently, so they are held to different standards:
#
#   LIVE / STANDING (DESIGN-LAW.md, INDEX.md, all code) — these INSTRUCT a future
#     agent. A retired name here is an order to rebuild the corpse. They are scoped
#     IN, strictly: REWRITE the prose. No banner will save them (see
#     `test_a_LIVE_document_cannot_be_saved_by_a_banner`).
#
#   DATED RECORD (a receipts/ file, or any file named YYYY-MM-DD-*) — this RECORDS
#     what was true on a date. **Rewriting it falsifies the record.** But leaving it
#     un-annotated teaches the bug to anyone who greps for the pattern. So the prose
#     is PRESERVED and the reader is WARNED: the file earns its exemption ONLY while
#     it carries a SUPERSEDED banner naming every retired symbol it mentions.
#
# The exemption is therefore self-cleaning by construction: delete the banner and the
# pin fires again; add a NEW retired symbol to the file without extending the banner
# and the pin fires again. Nothing here is a promise anyone has to remember.
#
# The LIVE-vs-DATED test is PATH-BASED because a list of blessed files is exactly the
# kind of hand-maintained claim that rots into fiction — which is the disease this
# whole module exists to treat.
# ---------------------------------------------------------------------------
_DATED_FILENAME = re.compile(r"^\d{4}-\d{2}-\d{2}[-_.]")
_DATED_DIRECTORIES = frozenset({"receipts"})

# The banner's sentinel, and how far into the file we will look for it. It must be at
# the TOP: a warning below the stale prose is a warning nobody reads in time.
_SUPERSEDED_MARKER = "SUPERSEDED"
_BANNER_SEARCH_LINES = 20


def _is_dated_record(path: Path) -> bool:
    """Is this file a RECORD OF a date, rather than an INSTRUCTION for the future?"""
    return bool(_DATED_FILENAME.match(path.name)) or bool(
        _DATED_DIRECTORIES & set(path.parts)
    )


def _superseded_banner(path: Path) -> str | None:
    """The file's SUPERSEDED banner — the CONTIGUOUS block of lines starting at the
    marker and ending at the first blank line — or ``None`` if it carries none.

    It is the BLOCK, not the file's head. Returning the head would let a symbol
    mentioned in the BODY (but absent from the banner) count as "warned about", simply
    because it happened to sit within the first few lines — and the banner would become
    a rubber stamp that exempts everything and warns about nothing. My own control
    (`test_a_DATED_record_is_spared_only_while_its_banner_names_the_symbol`) caught that
    on the first run.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()[:_BANNER_SEARCH_LINES]
    except (OSError, UnicodeDecodeError):
        return None
    for index, line in enumerate(lines):
        if _SUPERSEDED_MARKER in line:
            block: list[str] = []
            for candidate in lines[index:]:
                if not candidate.strip():
                    break
                block.append(candidate)
            return "\n".join(block)
    return None


def _scanned_files() -> list[Path]:
    roots = [_PACKAGE_ROOT, _TESTS_ROOT, _DOCS_ROOT]
    return sorted(
        path
        for root in roots
        if root.exists()
        for path in root.rglob("*")
        if path.is_file() and path.suffix in _SCANNED_SUFFIXES and "__pycache__" not in path.parts
    )


def _repo_key(path: Path) -> str:
    return path.relative_to(_REPO_ROOT).as_posix()


def _references(path: Path) -> list[tuple[int, str, str]]:
    """Every BARE, anchor-free mention of a retired symbol in ``path``.

    Returns ``(lineno, symbol, line)``. No prefix anchor, no call-paren anchor — a
    prose mention carries neither, and that is the whole point.
    """
    hits: list[tuple[int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return hits
    for lineno, line in enumerate(text.splitlines(), 1):
        for symbol in _RETIRED_SYMBOLS:
            if symbol in line:
                hits.append((lineno, symbol, line.strip()))
    return hits


def _defined_names() -> set[str]:
    """Every name DEFINED anywhere in the package or its tests."""
    defined: set[str] = set()
    for root in (_PACKAGE_ROOT, _TESTS_ROOT):
        for path in root.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, OSError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    defined.add(node.name)
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    defined.add(node.id)
    return defined


class TestRetiredSymbolRegistryIsHonest:
    """The registry must describe the codebase that EXISTS — or it is fiction, which
    is the very disease it is here to cure.
    """

    @pytest.mark.parametrize("symbol", sorted(_RETIRED_SYMBOLS))
    def test_every_retired_symbol_is_really_gone(self, symbol: str) -> None:
        """A registry entry claims "this name no longer exists". Check it.

        Without this, the registry could drift into a list of names that ARE defined —
        and then the hygiene pin below would be demanding the deletion of live code, or
        (worse) silently passing because nothing references a name that never left.
        That is exactly how the ``"assert"`` marker stayed fiction for the repo's whole
        life: a claim about the code that no gate ever checked.
        """
        resurrected = sorted(name for name in _defined_names() if name.startswith(symbol))
        assert not resurrected, (
            f"{symbol!r} is in the retired registry but these names are DEFINED in the "
            f"codebase: {resurrected}. Either the symbol came back (in which case the "
            f"deletion was undone and #102's defect may be back with it), or the "
            f"registry entry is stale and must be removed."
        )

    def test_every_allowlisted_file_still_enforces_a_retirement(self) -> None:
        """SELF-CLEANING allowlist. An enforcer that no longer names a retired symbol
        has stopped enforcing anything, and its exemption is now a hole through which a
        real dangling reference could walk. Delete it.
        """
        stale = [
            key
            for key in _RETIREMENT_ENFORCERS
            if not _references(_REPO_ROOT / key)
        ]
        assert not stale, (
            f"these files are allowlisted as retirement ENFORCERS but no longer mention "
            f"any retired symbol: {stale}. Remove them from _RETIREMENT_ENFORCERS — a "
            f"stale exemption is a blind spot nobody chose."
        )


class TestNoFileReferencesARetiredSymbol:
    """**THE INSTRUMENT.** No file — code, comment, docstring, or standing law — may
    name a symbol this repo has deleted.

    RED against the current tree. The sites are listed by the failure itself, which is
    the point: a flag in an audit report is not a gate, and four of these were flagged
    by an audit and shipped anyway.
    """

    def test_the_scanner_sees_every_reference_form(self) -> None:
        """POSITIVE CONTROL — the probe must be shown FIRING, on every shape the live
        tree actually contains, before a clean result from it means anything.

        These five forms are not hypothetical: each is copied from a real site found by
        the bare scan. An ANCHORED pattern (requiring a ``_txn.`` prefix, or a call
        paren) would miss most of them — which is precisely CLAUDE.md's warning that
        anchored sweeps "systematically miss exactly the sites gates can't see".
        """
        forms = {
            "bare": "the _apply_mint pattern is the reference for hot-row minting",
            "backticked": "hot-row `_apply_mint` pattern + two-step recreate",
            "module::symbol": "`findings.py::_apply_mint` (bounded app-retry)",
            "module space symbol": "`findings.py _apply_mint` (bounded app-retry)",
            "glob": "module constants (``_REPORT_MINT_*``); operators tune behaviour",
            "dotted": "mirrors ``_txn._TXN_CONFLICT_BACKOFF_SECONDS``.",
        }
        for name, line in forms.items():
            assert any(symbol in line for symbol in _RETIRED_SYMBOLS), (
                f"the bare scan does not see the {name!r} reference form"
            )

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            pytest.param("docs/plans/v2/receipts/2026-07-10-resume-chain.md", True, id="receipts-dir"),
            pytest.param("docs/design/2026-07-12-pkt28-c1-semantics.md", True, id="dated-filename"),
            pytest.param("docs/plans/v2/DESIGN-LAW.md", False, id="standing-law"),
            pytest.param("docs/plans/v2/INDEX.md", False, id="plan-of-record"),
            pytest.param("loremaster/loremaster/briefs.py", False, id="code"),
        ],
    )
    def test_the_LIVE_versus_DATED_rule_is_mechanical(self, name: str, expected: bool) -> None:
        """The distinction is decided BY PATH, never by a blessed-file list — a list of
        exceptions is exactly the hand-maintained claim that rots into fiction, which is
        the disease this module treats.

        A file is a DATED RECORD iff it lives under ``receipts/`` or its name begins
        ``YYYY-MM-DD-``. Everything else INSTRUCTS the future and is held to the strict
        standard.
        """
        assert _is_dated_record(_REPO_ROOT / name) is expected

    def test_a_DATED_record_is_spared_only_while_its_banner_names_the_symbol(
        self, tmp_path: Path
    ) -> None:
        """THE BANNER MECHANISM, controlled in all three states.

        History is preserved; the reader is warned; and the exemption evaporates the
        moment the warning does. Nothing here relies on anyone remembering anything.
        """
        record = tmp_path / "receipts" / "2026-07-10-a-record.md"
        record.parent.mkdir(parents=True)
        body = "the `_apply_mint` posture was adopted for hot-row minting\n"

        # 1. No banner -> the reader would meet the stale prose unwarned.
        record.write_text(body)
        assert _superseded_banner(record) is None

        # 2. Banner naming the symbol -> spared. The record is intact AND honest.
        record.write_text(
            "> ⚠ SUPERSEDED: `_apply_mint` was deleted by finding #102; its\n"
            "> deterministic id-derived jitter IS the defect. Do not use as a pattern.\n\n"
            + body
        )
        banner = _superseded_banner(record)
        assert banner is not None
        assert "_apply_mint" in banner

        # 3. Banner that does NOT name the symbol the file mentions -> NOT spared.
        record.write_text(
            "> ⚠ SUPERSEDED: some other thing changed.\n\n" + body
        )
        incomplete = _superseded_banner(record)
        assert incomplete is not None
        assert "_apply_mint" not in incomplete, (
            "a banner that does not name the symbol must not exempt it — otherwise the "
            "banner becomes a rubber stamp"
        )

    def test_a_LIVE_document_cannot_be_saved_by_a_banner(self, tmp_path: Path) -> None:
        """A banner is an exemption for HISTORY, never for STANDING LAW.

        ``DESIGN-LAW.md`` instructs future agents. Annotating it "this used to be true"
        is not enough: an agent obeying standing law would still find the pattern and
        clone the defect. It must be REWRITTEN — so the LIVE path must never qualify as
        a dated record, banner or no banner.
        """
        law = tmp_path / "DESIGN-LAW.md"
        law.write_text(
            "> ⚠ SUPERSEDED: `_apply_mint` was deleted by #102.\n\n"
            "`findings.py::_apply_mint` is the reference pattern for hot-row minting\n"
        )
        assert not _is_dated_record(law), (
            "a LIVE standing-law document must never be treated as a dated record — a "
            "banner would let it keep prescribing the defect"
        )
        assert _references(law), "the scan must still see the reference in a LIVE document"

    def test_innocent_prose_is_not_flagged(self) -> None:
        """NEGATIVE CONTROL. The scan must not fire on prose that merely discusses
        minting, jitter or backoff WITHOUT naming a retired symbol — otherwise every
        docstring in the retry seam would trip it and the pin would be deleted.
        """
        innocent = [
            "the mint's retry is owned by the shared seam, with per-attempt full jitter",
            "a deterministic backoff makes N racers re-collide in lockstep",
            "_txn_conflict_backoff_seconds draws a fresh window every attempt",
            "the four constants that tuned the old loop are gone",
        ]
        for line in innocent:
            assert not any(symbol in line for symbol in _RETIRED_SYMBOLS), (
                f"innocent prose was flagged: {line!r}"
            )

    def test_no_file_references_a_retired_symbol(self) -> None:
        """RED before 00f4301 at every site below.

        A LIVE document goes GREEN when its prose is rewritten to describe the
        BEHAVIOUR instead of naming the corpse. A DATED RECORD goes GREEN when it gains
        a SUPERSEDED banner naming the symbols it mentions — its prose is preserved,
        because rewriting a record of a date falsifies it.
        """
        offenders: list[str] = []
        for path in _scanned_files():
            key = _repo_key(path)
            if key in _RETIREMENT_ENFORCERS:
                continue

            referenced = {symbol for _, symbol, _ in _references(path)}
            if not referenced:
                continue

            if _is_dated_record(path):
                banner = _superseded_banner(path)
                if banner is None:
                    offenders.append(
                        f"{key} [DATED RECORD, no banner] mentions {sorted(referenced)} — "
                        f"do NOT rewrite the record; add a {_SUPERSEDED_MARKER} banner at "
                        f"the top naming them"
                    )
                    continue
                unwarned = sorted(symbol for symbol in referenced if symbol not in banner)
                if unwarned:
                    offenders.append(
                        f"{key} [DATED RECORD, banner incomplete] mentions {unwarned} but "
                        f"the {_SUPERSEDED_MARKER} banner does not name them"
                    )
                continue  # banner present and complete: history preserved, reader warned

            for lineno, symbol, line in _references(path):
                offenders.append(f"{key}:{lineno} [{symbol}] {line[:78]}")

        assert not offenders, (
            "these files name a symbol that NO LONGER EXISTS — the repo's own #1 defect "
            "class ('natural-language surfaces whose consistency with code no gate "
            "checks'), and the most dangerous of them is STANDING LAW prescribing the "
            "very defect finding #102 removes.\n\n"
            "LIVE documents and code: describe the BEHAVIOUR, do not name the corpse.\n"
            "DATED RECORDS: keep the prose, add a SUPERSEDED banner.\n\n"
            + "\n".join(f"  {offender}" for offender in offenders)
        )
