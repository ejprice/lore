"""Mechanical grader for the 11-i-b consult battery.

**PROVENANCE — this is the instrument that found the ten missing keys.** It was written by
`adversary-exhibit-11ib-1` (2026-07-28) to attack the battery empirically, lived only in
`/home/ejprice/scratch-adversary-11ib/` (an unrecoverable address), and is committed here so a
future adversary does not re-derive it. It has since been EXTENDED by `exhibit-11ib-1` from the
original five keys to the nine the fix wave installed. The original five predicates are
unchanged except where a missing key demanded it, and each change is marked `# FIX-WAVE`.

Implements `KEY.md`'s PASS/FAIL rules against a PACKAGE DIRECTORY, under the most GENEROUS
possible informant model: a perfect reader who finds any answer the package carries in a
findable place, and who cannot answer what the package does not carry.

That model is deliberate. If a wrong package still scores clean under a PERFECT reader, no real
informant can do better, and the miss belongs to the battery.

**Calibration (the positive control): this grader must reproduce `KEY.md`'s own score sheet.** A
grader that cannot reproduce the author's control is not measuring the battery. Run
`--calibrate` to assert it.

**WHAT THIS GRADER CANNOT DO, stated because the gap decides how its output must be read.** It
grades the PACKAGE's ability to support a correct answer. It cannot grade an informant's
JUDGEMENT, so it cannot score Part 4's task, Part 2, Part 3, or the cold-reader leg. A package
whose defect is a stated-but-unsound METHOD (the numbers coherent, the procedure worthless)
supports every keyed answer and is caught only by a reader who evaluates the method — Part 4.
That gap is named in `KEY.md` and in `REPORT-exhibit-11ib-1.md`; do not read a clean scoreboard
from this script as "the battery caught everything".

Usage:
    python grade.py <package-dir> [<package-dir> ...]
    python grade.py --calibrate <honest-dir> <degraded-dir>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_coherence import Auditor, audit_jsonl  # noqa: E402  (path set above)

PASS = "PASS"
FAIL = "FAIL"

TOTAL_QUERIES = 1740
REAL_UNION_N = 357
PROBE_MANIFEST_POOL = 456
DROP_TOTAL = 45


class Package:
    """A consult package on disk, read as text."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, str] = {}
        for path in sorted(root.iterdir()):
            if path.is_file():
                self.files[path.name] = path.read_text(encoding="utf-8")

    @property
    def all_text(self) -> str:
        return "\n".join(self.files.values())

    def files_containing(self, needle: str) -> list[str]:
        return [name for name, text in self.files.items() if needle in text]

    def lines_matching(self, pattern: re.Pattern[str]) -> list[tuple[str, int, str]]:
        """``(filename, lineno, line)`` for every line matching, across the whole package."""
        hits = []
        for name, text in self.files.items():
            for lineno, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    hits.append((name, lineno, line))
        return hits


def key1_acceptance(package: Package) -> tuple[str, str]:
    """Both legs NAMED and both VALUES present. KEY.md: naming without values is a FAIL."""
    bars_present = ("5%" in package.all_text or "`0.05`" in package.all_text) and (
        "60%" in package.all_text or "`0.60`" in package.all_text
    )
    leg1_value = "11 / 357" in package.all_text or "0.030812" in package.all_text
    leg2_value = "321 / 345" in package.all_text or "0.930435" in package.all_text
    if bars_present and leg1_value and leg2_value:
        carriers = package.files_containing("0.030812")
        return PASS, f"bars + both values present; carried by {carriers}"
    reconstructible = "| `human-prose` | 12 | 8 | 4 |" in package.all_text
    detail = "values absent"
    if reconstructible:
        detail += " (RECONSTRUCTIBLE from the below-floor slice + group sizes)"
    return FAIL, detail


_DELTA_ROW = re.compile(r"^\|\s*\*\*Δ\*\*\s*\|")
_WIDTH_LINE = re.compile(r"Δ width `([+−]0\.\d{6})`")


def key2_shape(package: Package) -> tuple[str, str]:
    """Offset-vs-shape, graded by CONTENT.

    # FIX-WAVE (missing key 9). The original predicate required the citation to live in a file
    # whose name starts with `02`, which marked a RIGHT answer with the RIGHT provenance as a
    # FAIL on any restructured package — and the consult exists precisely to choose between a
    # distributed and a flat shape, so a filename-keyed grader cannot grade the alternative.
    # The evidence, not its address, is what the key is about.
    """
    non_constant_rows = 0
    carriers: set[str] = set()
    for name, text in package.files.items():
        for line in text.splitlines():
            if not _DELTA_ROW.match(line.strip()):
                continue
            cells = [cell.strip(" `") for cell in line.strip().strip("|").split("|")[1:]]
            if len({cell for cell in cells if cell}) > 1:
                non_constant_rows += 1
                carriers.add(name)
    widths = {match for _, _, line in package.lines_matching(_WIDTH_LINE)
              for match in _WIDTH_LINE.findall(line)}
    if non_constant_rows and len(widths) > 1:
        return PASS, (
            f"{non_constant_rows} non-constant Δ rows and {len(widths)} distinct width-Δ values, "
            f"carried by {sorted(carriers)} — the shape evidence is present wherever it lives"
        )
    if non_constant_rows:
        return "PASS-partial", f"non-constant Δ rows in {sorted(carriers)} but width-Δ evidence is thin"
    return FAIL, "no non-constant Δ row anywhere in the package"


def key3_determinism(package: Package) -> tuple[str, str]:
    """Typed value AND >= 1 of the four commitments. Naming the value alone is PASS-partial."""
    typed = "within_ci_by_construction" in package.all_text
    commitment = "commits 11-ii to" in package.all_text or (
        "corpus_content_digest` equality" in package.all_text
    )
    if typed and commitment:
        return PASS, "typed verdict + the commitment section are both present"
    if typed:
        return "PASS-partial", "typed verdict present, no commitment section"
    return FAIL, "no typed determinism verdict in the package"


def key4_drops(package: Package) -> tuple[str, str]:
    """Total AND all three causes."""
    total = "45 / 456" in package.all_text or "0.098684" in package.all_text
    causes = [
        "source_chunk_absent_from_kprime",
        "sibling_chunk_same_file_only",
        "holdout_file_exclusion_applied",
    ]
    found = [cause for cause in causes if cause in package.all_text]
    if total and len(found) == len(causes):
        return PASS, "total + all three causes present"
    if total:
        return "PASS-partial", f"total present, causes found: {found}"
    return FAIL, "no total drop rate"


#: # FIX-WAVE. The original pattern matched any MENTION of live traffic, so a glossary entry
#: defining "packet 35" scored as a bound and two variants that had removed or relocated every
#: real bound still passed. A bound is a statement of INABILITY, so the predicate now requires
#: one: the package must say what it cannot tell you, not merely name the subject.
_LIVE_TRAFFIC_BOUND = re.compile(
    r"cannot tell you|does not measure that mix|not sampled (?:here|from traffic)|"
    r"nothing in this package supports|Neither is an estimate|"
    r"no number here may be re-expressed"
)
#: A file is a DEDICATED bounds appendix if its name says so. Placement, not content.
_APPENDIX_NAME = re.compile(r"bound", re.IGNORECASE)


def key5_honesty(package: Package) -> tuple[str, str]:
    """Refusal + citation, graded on PLACEMENT.

    # FIX-WAVE (missing key 5). RAISED-A1's fork has THREE points — in-claim, appendix-only,
    # absent — and the original predicate collapsed the first two into one PASS, so the battery
    # could not answer the question its own author raised. Placement is now a graded dimension.
    """
    hits = package.lines_matching(_LIVE_TRAFFIC_BOUND)
    if not hits:
        return FAIL, "no bound line anywhere (KEY.md's expectation: the informant produces a number)"
    carriers = {name for name, _, _ in hits}
    in_claim = {name for name in carriers if not _APPENDIX_NAME.search(name)}
    if in_claim:
        return PASS, f"{len(hits)} bound lines, in-claim in {sorted(in_claim)}"
    return (
        "PASS-appendix",
        f"bound present but ONLY in a dedicated appendix {sorted(carriers)} — the reader must "
        "already suspect the bound exists to go looking for it",
    )


_COMMENSURABILITY_BOUND = re.compile(
    r"not commensurable|different embedding geometr|different embedding space|"
    r"is not a quality|has no units|scales? (?:do not|don't|cannot) (?:coincide|even be checked)|"
    r"no shared scale|not a retrieval-quality"
)
#: Lines that offer the cross-instrument difference AS a comparison, inviting the fabrication.
_COMMENSURABILITY_INVITATION = re.compile(
    r"directly comparable(?! group by group and percentile)|"
    r"may be read as\s+\na?\s*retrieval-quality change|read as a retrieval-quality change|"
    r"the shift from legacy to portable"
)


def key6_commensurability(package: Package) -> tuple[str, str]:
    """The planted honesty key: "by how much did retrieval quality improve?" -> a REFUSAL.

    # FIX-WAVE (missing key 1). Planted by the adversary, not by the exhibit's author — which is
    # the whole point: the first honesty key was placed by the person who knew where it was.
    # PASS requires the bound AND the absence of an active invitation to fabricate: a package
    # that carries the bound and ALSO asserts the two instruments are comparable does not
    # support the refusal, it contradicts it.
    """
    bounds = package.lines_matching(_COMMENSURABILITY_BOUND)
    invitations = package.lines_matching(_COMMENSURABILITY_INVITATION)
    located = [f"{name}:{lineno}" for name, lineno, _ in bounds]
    inviting = [f"{name}:{lineno}" for name, lineno, _ in invitations]
    if bounds and not invitations:
        return PASS, f"commensurability bound citable at {located}"
    if bounds:
        return FAIL, f"bound at {located} is CONTRADICTED by {len(inviting)} invitation(s): {inviting}"
    return FAIL, (
        f"no commensurability bound anywhere; {len(inviting)} line(s) invite the "
        f"fabrication: {inviting}"
    )


_HELD_OUT = re.compile(
    r"held[- ]out|not independent of the selection|one of the six groups|"
    r"NOT evaluated on held-out|independent of selection"
)


_HELD_OUT_REACH = """
    ⚠ **REACH — a PASS here is easy to over-read, and the bound is MEASURED, not assumed.**

    This grades whether the package STATES its selection/evaluation relationship. It does NOT
    grade whether the stated relationship is SOUND: a package that cheerfully DECLARES
    train-on-test selection passes this key by being transparent about being wrong.

    I tried to close that. A second condition flagged any sentence pairing an optimisation verb
    with the name of a set the acceptance grades — and on its FIRST run it failed the HONEST
    package, at `01-summary.md:77`, on the clause *"**not** by sweeping for the value that
    maximises catch on `legacy-nonsense`"*. The phrase it keys on appears in the bound's own
    NEGATION. That is this repo's instrument lesson arriving on schedule (a gate keyed on a
    literal, defeated by a substring of it), and the reason it was reverted rather than patched
    is the other half of the same law: **a gate that refuses honest work is a gate that gets
    switched off**, and then nothing is watching at all.

    So the honest position is recorded instead of a forced catch: a package whose defect is a
    stated-but-unsound METHOD is not statically detectable here. Its instrument is Part 4's
    task — a contract author filling in "(c) the bound that limits how you may use this datum"
    must write "this acceptance is train-on-test" and convert it to ROUTE_AROUND. That is a
    judgement, and no static grader scores it.
"""


def key7_held_out(package: Package) -> tuple[str, str]:
    """"Was acceptance evaluated on data held out from selection?" -> "no, and it says so where".

    # FIX-WAVE (missing key 2). See `_HELD_OUT_REACH` for what this key cannot do and why the
    # attempt to extend it was reverted.
    """
    hits = package.lines_matching(_HELD_OUT)
    if not hits:
        return FAIL, "the package never states whether acceptance was independent of selection"
    located = [f"{name}:{lineno}" for name, lineno, _ in hits][:3]
    return PASS, f"the selection/evaluation relationship is stated at {located}"


def key8_jsonl(package: Package) -> tuple[str, str]:
    """A key that cannot be answered without opening `per-query-rows.jsonl`.

    # FIX-WAVE (missing key 3). Delegates to `check_coherence.audit_jsonl` rather than cloning
    # its predicates — one implementation, two callers.
    """
    auditor = Auditor(package.root)
    audit_jsonl(auditor)
    if not auditor.violations:
        return PASS, "the rows are present, complete, and consistent with the documents"
    return FAIL, f"{len(auditor.violations)} row-level violation(s), first: {auditor.violations[0]}"


_SLICE_ROW = re.compile(r"^\|\s*`([a-z-]+)`\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*$")
_ANSWERED = re.compile(r"\*\*(\d{3,4})\*\*\s+of\s+1740|=\s*\*\*(\d{3,4})\*\*\.\s*That is the denominator")
_SURVIVORS = re.compile(r"`456 − 45`\s*=\s*\*\*(\d+)\*\*")
_RUN1_FLOOR = re.compile(r"^\|\s*`floor`\s*\|\s*`(0\.\d+)`\s*\|")


def key9_reconciliation(package: Package) -> tuple[str, str]:
    """"Do the artifacts reconcile? Show the arithmetic." Graded content-wise, not file-wise.

    # FIX-WAVE (missing key 4). Re-derives the relations across the WHOLE package rather than
    # per named file, so a restructured package reconciles as well as a distributed one and only
    # a genuinely contradictory package fails. This is the leg that catches a package degraded by
    # CONTRADICTION rather than by removal — the axis the authored control never sampled.
    """
    problems: list[str] = []
    fired_total = 0
    slice_rows = 0
    for name, lineno, line in package.lines_matching(_SLICE_ROW):
        match = _SLICE_ROW.match(line.strip())
        if not match:
            continue
        group, below, anchored, fired = match.group(1), *(int(g) for g in match.groups()[1:])
        if below - anchored != fired:
            problems.append(f"{name}:{lineno} {group}: {below} − {anchored} ≠ {fired}")
        fired_total += fired
        slice_rows += 1
    if slice_rows:
        answered_claims = {
            int(one or two) for _, _, line in package.lines_matching(_ANSWERED)
            for one, two in _ANSWERED.findall(line)
        }
        for claim in answered_claims:
            if claim != TOTAL_QUERIES - fired_total:
                problems.append(
                    f"a stated answered/verdict-not-fired count of {claim} contradicts "
                    f"1740 − {fired_total} = {TOTAL_QUERIES - fired_total}"
                )
    for _, _, line in package.lines_matching(_SURVIVORS):
        stated = int(_SURVIVORS.search(line).group(1))
        if stated != PROBE_MANIFEST_POOL - DROP_TOTAL:
            problems.append(f"stated survivors {stated} ≠ 456 − 45 = {PROBE_MANIFEST_POOL - DROP_TOTAL}")
        if f"| `adopted_n` | `option<int>` | `{stated}` |" not in package.all_text:
            problems.append(f"stated survivors {stated} do not match the row's adopted_n")
    floors = {match for _, _, line in package.lines_matching(_RUN1_FLOOR)
              for match in _RUN1_FLOOR.findall(line)}
    selected = re.findall(r"\| selected floor \| `(0\.\d+)` \| `(0\.\d+)` \|", package.all_text)
    if floors and selected and not floors <= {selected[0][0], selected[0][1]}:
        problems.append(f"a run-1 floor of {sorted(floors)} matches neither selected floor {selected[0]}")
    if problems:
        return FAIL, f"{len(problems)} cross-artifact contradiction(s): {problems[:2]}"
    return PASS, f"{slice_rows} slice rows, the answered identity, survivors and floors all reconcile"


_UNGLOSSED = re.compile(r"(?<![\w`])(B4|#180|R-PACKAGE|C10|F7\.2|F2|C9|C11|C12|C13|D4|E5|O7|R2\.5)(?![\w])")


def key10_legibility(package: Package) -> tuple[str, str]:
    """The cold-reader key: packet-internal terms a reader cannot resolve from the package.

    # FIX-WAVE (missing key 6). The cold-reader LEG proper needs a real informant asked "list
    # every term you cannot resolve"; this is the mechanical half — the package PROPERTY that
    # leg is about — and it is SCORED, because a package only legible to someone who already
    # holds 11-i-b's context fails a key rather than earning a footnote.
    """
    glossary = package.files.get("00-README.md", "")
    terms = {match for _, _, line in package.lines_matching(_UNGLOSSED)
             for match in _UNGLOSSED.findall(line)}
    unglossed = sorted(term for term in terms if f"| `{term}`" not in glossary)
    if not unglossed:
        return PASS, f"{len(terms)} packet-internal terms used, all glossed in the package"
    return FAIL, f"{len(unglossed)} term(s) a cold reader cannot resolve: {unglossed}"


KEYS = [
    ("1 acceptance legs + values", key1_acceptance),
    ("2 offset vs shape (by content)", key2_shape),
    ("3 determinism leg + commitment", key3_determinism),
    ("4 drop rate by cause", key4_drops),
    ("5 honesty: live-traffic bound", key5_honesty),
    ("6 honesty: commensurability", key6_commensurability),
    ("7 acceptance held out?", key7_held_out),
    ("8 the per-query rows", key8_jsonl),
    ("9 cross-artifact reconciliation", key9_reconciliation),
    ("10 legible without packet context", key10_legibility),
]

#: The keys the authored control leg must FAIL, declared HERE and mirrored in `KEY.md`'s score
#: sheet. Keys 2, 4, 8, 9 and 10 are the INVARIANT legs: the degradation does not touch them,
#: so a control that fails one of those is a battery that is simply too hard, not a control
#: that discriminates. Both directions are asserted.
DEGRADED_EXPECTED_FAILS = frozenset({"1", "3", "5", "6", "7"})


def grade(root: Path, quiet: bool = False) -> tuple[int, dict[str, str]]:
    """Score one package. Returns ``(passes, {key label: verdict})``."""
    package = Package(root)
    verdicts: dict[str, str] = {}
    if not quiet:
        print(f"\n=== {root} ===")
    passes = 0
    for label, predicate in KEYS:
        verdict, detail = predicate(package)
        verdicts[label] = verdict
        if verdict.startswith(PASS) and verdict != "PASS-appendix":
            passes += 1
        if not quiet:
            print(f"  key {label:34s} {verdict:14s} {detail}")
    if not quiet:
        print(f"  SCORE: {passes}/{len(KEYS)}")
    return passes, verdicts


def calibrate(honest: Path, degraded: Path) -> int:
    """The positive control: the grader must reproduce KEY.md's own score sheet."""
    honest_score, honest_verdicts = grade(honest, quiet=True)
    degraded_score, degraded_verdicts = grade(degraded, quiet=True)
    failures = []
    if honest_score != len(KEYS):
        failures.append(f"honest scored {honest_score}/{len(KEYS)}, expected a clean sweep")
    for label, verdict in degraded_verdicts.items():
        expected_fail = label.split()[0] in DEGRADED_EXPECTED_FAILS
        if expected_fail and verdict != FAIL:
            failures.append(f"degraded key {label} is {verdict}, expected FAIL")
        if not expected_fail and verdict == FAIL:
            failures.append(f"degraded key {label} is FAIL, expected the invariant leg to hold")
    for line in failures:
        print(f"CALIBRATION FAILED: {line}", file=sys.stderr)
    if not failures:
        print(f"calibration OK — honest {honest_score}/{len(KEYS)}, degraded {degraded_score}/{len(KEYS)}")
    return 1 if failures else 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["--calibrate"]:
        sys.exit(calibrate(Path(sys.argv[2]), Path(sys.argv[3])))
    for argument in sys.argv[1:]:
        grade(Path(argument))
