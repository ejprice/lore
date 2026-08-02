"""Contract for the GATE-CURRENCY mode of ``scripts/pending_contract_gate.py``
(sidecar Ruling 7, operator-granted: *"Close the gap"*; grounds #306 + #312).

**THE GAP, in the words of #312's resolve note.** *"Nothing systematically checks
whether a gate named in CLAUDE.md is actually green at HEAD — #306 and #312 were
both found by agents tripping over them mid-task, not by any instrument. The
question 'is every gate we CLAIM to run actually passing, and if not who owns it'
has no derived answer."*

Two measured instances, and they are different failure modes:

* **#306** — a gate RUN and RED, with no owner, no trigger, no ledger row. It sat
  red for an unmeasured length of time and every session inherited it.
* **#312** — a gate CLAIMED and NEVER RUN. The wrapper built to pin #306 shipped
  without its own ruff leg, so its receipt read as full-gate while one third of
  the gate set was never executed. Reproduced inside #306's own instrument.

**THE THREE RULINGS THIS PINS** (sidecar §7.1–7.3):

1. **The binding is INVERTED.** You cannot derive a gate set from English law —
   *a regex over prose is the enumeration antipattern one level up*, with six
   receipts against its class. So ``scripts/gates.yaml`` is CANONICAL and
   ``CLAUDE.md``'s gate section is demoted to commentary that CITES it. Pinned by
   ``test_claude_md_cites_the_manifest`` (a citation-PRESENCE anchor — the safe
   set — never prose parsing).
2. **ONE IMPLEMENTATION.** The leg set DERIVES from the manifest; there is no
   hand-tuple to forget. #312's *"any future gate must be added to ALL_LEGS in the
   same diff"* stops being a thing to remember and becomes a thing that cannot be
   written. Proved by MUTATION, not inspection
   (``test_adding_a_gate_to_the_manifest_reaches_the_runner_with_no_code_edit``).
3. **The invariant is ADJUDICATION, not GREENNESS.** ``GREEN`` ·
   ``RED_ADJUDICATED(owner, trigger)`` · ``RED_ORPHANED``, and **only
   RED_ORPHANED fails.** Packet 39's red typecheck is a ruled, owned bound doing
   its job; red-and-orphaned is the disease.

⚠ **WHAT WRONG BUILD WOULD STILL PASS THIS?** Each answer is a test:

* one that calls every red "adjudicated" → killed by the orphan cases;
* one that calls every red "orphaned" → killed by the packet-39 case, which must
  PASS currency while the tree is red;
* one that reads greenness instead of ownership → killed by
  ``test_a_zero_tolerance_gate_is_ORPHANED_even_when_the_registry_names_the_file``;
* one that grandfathers a stale adjudication → killed by
  ``test_an_EXPIRED_adjudication_is_ORPHANED_not_grandfathered``;
* one whose manifest can be empty → killed by ``test_an_EMPTY_manifest_is_refused``
  (an empty gate set makes currency vacuously true, which is the whole disease);
* one that lets currency impersonate the deploy receipt → killed by
  ``test_currency_and_the_deploy_receipt_are_NAMED_APART``.

⚠ **ONE DELIBERATE DEPARTURE from the sibling contract's fixture law.**
``test_pending_contract_gate.py`` keeps every fixture canned under ``tmp_path``.
``test_claude_md_cites_the_manifest`` reads the REAL ``CLAUDE.md``, because the
drift it pins IS drift of that file — a canned copy would pin nothing. It is a
substring check on a path literal, so it costs one file read and cannot go flaky.
"""

from __future__ import annotations

import os
import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pending_contract_gate import (  # noqa: E402
    DEFAULT_MANIFEST_PATH,
    READERS,
    GateManifest,
    GateSpec,
    ManifestError,
    PendingContractGate,
    PendingContractRegistry,
    gate_currency,
)

REPO_ROOT = Path(__file__).resolve().parent.parent

_REGISTERED_FILE = "lorerunes/tests/test_posture.py"
_UNREGISTERED_FILE = "loremaster/tests/test_search.py"

_MANIFEST_YAML = textwrap.dedent(
    """\
    version: 1
    gates:
      - id: typecheck
        description: "the canonical static-analysis runner"
        command: ["./scripts/typecheck.sh"]
        reader: typecheck_transcript
        adjudicated_by: pending-contracts
      - id: ruff
        description: "the lint gate"
        command: ["uv", "run", "ruff", "check", "."]
        reader: ruff
        adjudicated_by: none
      - id: pytest
        description: "the suite"
        command: ["uv", "run", "pytest", "-q", "--junit-xml={junit_xml}"]
        reader: pytest_junit
        adjudicated_by: pending-contracts
    """
)

_REGISTRY_YAML = textwrap.dedent(
    f"""\
    version: 1
    bounds:
      - id: packet-39-pending-build
        owner: "packet 39 — hosted-security contract"
        reopen_trigger: "operator decision #296, or packet 39's build start"
        ruling: "finding #306"
        rationale: "contract committed ahead of a build blocked on #296"
        files:
          - path: {_REGISTERED_FILE}
            missing_symbols:
              - lorerunes.Posture
    """
)


@pytest.fixture()
def manifest(tmp_path: Path) -> GateManifest:
    path = tmp_path / "gates.yaml"
    path.write_text(_MANIFEST_YAML)
    return GateManifest.load(path)


@pytest.fixture()
def gate(tmp_path: Path) -> PendingContractGate:
    registry_path = tmp_path / "pending_contracts.yaml"
    registry_path.write_text(_REGISTRY_YAML)
    tree = tmp_path / "tree"
    (tree / _REGISTERED_FILE).parent.mkdir(parents=True, exist_ok=True)
    (tree / _REGISTERED_FILE).write_text("# pending contract\n")
    return PendingContractGate(
        registry=PendingContractRegistry.load(registry_path), repo_root=tree
    )


# --------------------------------------------------------------------------
# 1. The manifest is canonical — and it is a validated boundary
# --------------------------------------------------------------------------


def test_the_manifest_names_the_gates_and_their_readers(manifest: GateManifest) -> None:
    assert manifest.ids == ("typecheck", "ruff", "pytest")
    assert manifest.gate("ruff").adjudicated_by == "none"


def test_an_EMPTY_manifest_is_refused(tmp_path: Path) -> None:
    """THE VACUITY CASE, and it is the disease itself: a currency check over an
    empty gate set answers "every claimed gate is green" while claiming nothing.
    A manifest with no gates is a BROKEN INSTRUMENT, never a clean repo."""
    path = tmp_path / "empty.yaml"
    path.write_text("version: 1\ngates: []\n")
    with pytest.raises(ManifestError):
        GateManifest.load(path)


def test_an_UNKNOWN_reader_is_refused_naming_the_safe_set(tmp_path: Path) -> None:
    """ALLOWLIST THE SAFE. A gate whose reader the runner does not implement must
    fail to PARSE — that is Ruling 7.2's mechanism: *"a gate added to the manifest
    reaches the runner in the same edit, or the runner fails to parse."*"""
    path = tmp_path / "bad.yaml"
    path.write_text(_MANIFEST_YAML.replace("reader: ruff", "reader: telepathy"))
    with pytest.raises(ManifestError, match="telepathy"):
        GateManifest.load(path)


def test_an_UNKNOWN_adjudicator_is_refused(tmp_path: Path) -> None:
    """Falsifier 7.3: a red class with no registry able to own it is a NEW
    adjudication citizen and a DESIGN question — so it must stop the parse, never
    be improvised into existence by a builder."""
    path = tmp_path / "bad.yaml"
    path.write_text(
        _MANIFEST_YAML.replace("adjudicated_by: none", "adjudicated_by: vibes")
    )
    with pytest.raises(ManifestError, match="vibes"):
        GateManifest.load(path)


def test_duplicate_gate_ids_are_refused(tmp_path: Path) -> None:
    path = tmp_path / "dupe.yaml"
    path.write_text(_MANIFEST_YAML.replace("id: ruff", "id: typecheck"))
    with pytest.raises(ManifestError, match="typecheck"):
        GateManifest.load(path)


def test_a_junit_reader_whose_command_lacks_the_placeholder_is_refused(
    tmp_path: Path,
) -> None:
    """The junit reader cannot read a document the command never writes. A
    manifest that promises one without asking for it is a gate that would fail
    LOUD at run time — caught at parse time instead."""
    path = tmp_path / "nojunit.yaml"
    path.write_text(_MANIFEST_YAML.replace(' "--junit-xml={junit_xml}"', ""))
    with pytest.raises(ManifestError, match="junit_xml"):
        GateManifest.load(path)


def test_an_empty_command_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "nocmd.yaml"
    path.write_text(
        _MANIFEST_YAML.replace('command: ["uv", "run", "ruff", "check", "."]', "command: []")
    )
    with pytest.raises(ManifestError):
        GateManifest.load(path)


# --------------------------------------------------------------------------
# 2. ONE IMPLEMENTATION — the leg set DERIVES; there is no hand-tuple
# --------------------------------------------------------------------------


def test_adding_a_gate_to_the_manifest_reaches_the_runner_with_no_code_edit(
    tmp_path: Path,
) -> None:
    """PROVE SHARING BY MUTATION, NOT BY INSPECTION (CLAUDE.md).

    #312's own generalisation was *"any future gate added to CLAUDE.md must be
    added to ALL_LEGS in the same diff"* — a thing to REMEMBER, i.e. a hope. This
    test is the mechanism that replaces it: mutate the manifest, and the runner's
    leg set must move with it. A runner keeping a private hand-tuple passes every
    other test in this file and fails this one.
    """
    path = tmp_path / "grown.yaml"
    fourth_gate = (
        '  - id: shellcheck_standalone\n'
        '    description: "a fourth gate nobody has written yet"\n'
        '    command: ["uv", "run", "shellcheck", "scripts/typecheck.sh"]\n'
        "    reader: ruff\n"
        "    adjudicated_by: none\n"
    )
    path.write_text(_MANIFEST_YAML + fourth_gate)
    grown = GateManifest.load(path)
    assert "shellcheck_standalone" in grown.ids
    assert len(grown.ids) == 4


def test_every_reader_named_by_the_SHIPPED_manifest_exists(self_check: None = None) -> None:
    """The always-on manifest-validity leg (Ruling 7.3): the SHIPPED manifest
    parses and every reader it names resolves — checked without executing a single
    gate, so it costs milliseconds and runs in the ordinary suite."""
    shipped = GateManifest.load(DEFAULT_MANIFEST_PATH)
    assert shipped.ids, "the shipped manifest must name at least one gate"
    for spec in shipped.gates:
        assert spec.reader in READERS


def test_every_command_in_the_SHIPPED_manifest_resolves(self_check: None = None) -> None:
    """A manifest naming a command that does not exist is a gate that cannot run —
    the #312 failure mode (claimed, never executed) in its purest form."""
    import shutil

    for spec in GateManifest.load(DEFAULT_MANIFEST_PATH).gates:
        head = spec.command[0]
        resolved = (
            (REPO_ROOT / head).exists() if head.startswith("./") else shutil.which(head)
        )
        assert resolved, f"gate {spec.id!r} names an unresolvable command {head!r}"


# --------------------------------------------------------------------------
# 3. ADJUDICATION, not greenness
# --------------------------------------------------------------------------


def test_a_gate_with_no_residuals_is_GREEN(gate: PendingContractGate) -> None:
    currency = gate_currency(
        gate=gate, gate_id="ruff", adjudicated_by="none", residuals=[], expired=[]
    )
    assert currency.verdict == "GREEN"
    assert currency.ok


def test_a_red_gate_whose_residuals_are_ALL_REGISTERED_is_RED_ADJUDICATED(
    gate: PendingContractGate,
) -> None:
    """PACKET 39's WORKED EXAMPLE. The typecheck gate is red, and that is a ruled,
    owned bound doing its job — currency must PASS, and must NAME the owner and
    the trigger rather than merely tolerating the red."""
    currency = gate_currency(
        gate=gate,
        gate_id="typecheck",
        adjudicated_by="pending-contracts",
        residuals=[],
        expired=[],
        registered_count=191,
    )
    assert currency.verdict == "RED_ADJUDICATED"
    assert currency.ok, "a ruled, owned red must NOT fail the currency check"
    assert any("packet-39-pending-build" in owner for owner in currency.owners)
    assert any("#296" in owner for owner in currency.owners)


def test_a_red_gate_with_an_UNOWNED_residual_is_RED_ORPHANED(
    gate: PendingContractGate,
) -> None:
    """#306 and #312's shared disease: red, with nobody's name on it."""
    currency = gate_currency(
        gate=gate,
        gate_id="typecheck",
        adjudicated_by="pending-contracts",
        residuals=[f"{_UNREGISTERED_FILE}:12: error: something new"],
        expired=[],
        registered_count=191,
    )
    assert currency.verdict == "RED_ORPHANED"
    assert not currency.ok
    assert any(_UNREGISTERED_FILE in orphan for orphan in currency.orphans)


def test_a_zero_tolerance_gate_is_ORPHANED_even_when_the_registry_names_the_file(
    gate: PendingContractGate,
) -> None:
    """``adjudicated_by: none`` means NO registry may own this gate's reds. A
    build reading greenness-plus-registry rather than the gate's own policy would
    call this adjudicated — #312's ruff violations were in a file the registry
    could plausibly have named."""
    currency = gate_currency(
        gate=gate,
        gate_id="ruff",
        adjudicated_by="none",
        residuals=[f"{_REGISTERED_FILE}:1:8 — F401 unused import"],
        expired=[],
    )
    assert currency.verdict == "RED_ORPHANED"
    assert not currency.ok


def test_an_EXPIRED_adjudication_is_ORPHANED_not_grandfathered(
    gate: PendingContractGate,
) -> None:
    """Ruling 7.3 rider 2. The self-destruct legs already force a registry entry
    to die when its premise does; currency must not quietly outlive them. A build
    that counted only UNREGISTERED residuals would pass this while carrying a
    stale exemption — which is the exact artifact the whole instrument exists to
    make impossible."""
    currency = gate_currency(
        gate=gate,
        gate_id="typecheck",
        adjudicated_by="pending-contracts",
        residuals=[],
        expired=["SELF-DESTRUCT: registered file X produced NO mypy errors"],
        registered_count=191,
    )
    assert currency.verdict == "RED_ORPHANED"
    assert not currency.ok
    assert any("SELF-DESTRUCT" in orphan for orphan in currency.orphans)


def test_ONLY_orphaned_fails_across_the_whole_verdict_set(
    gate: PendingContractGate,
) -> None:
    """The rule stated once, over the whole set, rather than three times over
    three instances — the quantifier form."""
    green = gate_currency(gate=gate, gate_id="ruff", adjudicated_by="none", residuals=[], expired=[])
    adjudicated = gate_currency(
        gate=gate,
        gate_id="typecheck",
        adjudicated_by="pending-contracts",
        residuals=[],
        expired=[],
        registered_count=1,
    )
    orphaned = gate_currency(
        gate=gate,
        gate_id="ruff",
        adjudicated_by="none",
        residuals=["something"],
        expired=[],
    )
    assert [c.ok for c in (green, adjudicated, orphaned)] == [True, True, False]
    assert [c.verdict for c in (green, adjudicated, orphaned)] == [
        "GREEN",
        "RED_ADJUDICATED",
        "RED_ORPHANED",
    ]


def test_a_CLAIMED_but_UNRUN_gate_is_NOT_RUN_and_fails_without_claiming_it_is_RED(
    tmp_path: Path,
) -> None:
    """⚠ A FOURTH STATE THE RULING DID NOT NAME — added because a live control
    caught this render OVER-CLAIMING, and reported to the lead as a deviation.

    Ruling 7.3's set is GREEN / RED_ADJUDICATED / RED_ORPHANED, and the first
    build mapped "claimed but never executed" onto RED_ORPHANED. It **failed
    correctly** — a gate nobody ran cannot be shown green-or-owned, and that is
    #312's half of the disease — but it **asserted the gate was RED**, which is a
    fact not in evidence. The trust doctrine forbids a served surface
    over-claiming outright, so the state is named for what it is.

    Both halves are pinned, because either alone admits a wrong build: one that
    passes over unrun gates (#312 restored), and one that keeps telling the reader
    an unmeasured gate is red.
    """
    from pending_contract_gate import VERDICT_NOT_RUN, GateCurrency

    unrun = GateCurrency(
        gate_id="pytest",
        verdict=VERDICT_NOT_RUN,
        owners=(),
        orphans=("gate 'pytest' is CLAIMED by the manifest and was NOT RUN",),
        registered_count=0,
    )
    assert not unrun.ok, "an unmeasured gate cannot satisfy 'every gate is owned'"
    rendered = unrun.render()
    assert "NOT_RUN" in rendered
    assert "RED" not in rendered, (
        "the render must not assert a gate is RED when it was never executed — "
        "that is a served claim with no measurement behind it"
    )


# --------------------------------------------------------------------------
# 4. The two verdicts are NAMED APART
# --------------------------------------------------------------------------


def test_currency_and_the_deploy_receipt_are_NAMED_APART(
    gate: PendingContractGate,
) -> None:
    """Ruling 7.3 rider 3: *"Currency answers 'is every claimed gate green-or-owned
    at HEAD'; the deploy receipt answers 'may this ship'. Two verdicts, one runner,
    named apart so neither impersonates the other."*

    Concretely: at HEAD today, currency PASSES (packet 39's red is owned) while
    the deploy receipt does NOT (the tree is red). A build that collapsed them
    would either block the deploy forever or ship over an unowned red.
    """
    adjudicated = gate_currency(
        gate=gate,
        gate_id="typecheck",
        adjudicated_by="pending-contracts",
        residuals=[],
        expired=[],
        registered_count=191,
    )
    assert adjudicated.ok
    assert adjudicated.verdict == "RED_ADJUDICATED"
    assert not hasattr(adjudicated, "is_deploy_receipt"), (
        "currency must not carry a deploy-receipt field — the two verdicts answer "
        "different questions and a shared field is how one impersonates the other"
    )


# --------------------------------------------------------------------------
# 5. The INVERTED BINDING — CLAUDE.md cites the manifest
# --------------------------------------------------------------------------


def test_claude_md_cites_the_manifest() -> None:
    """Ruling 7.1's cheap pin on the binding itself.

    A citation-PRESENCE anchor: the gate section must name the manifest path. It
    does NOT parse the prose — *a regex over English law is the enumeration
    antipattern one level up*, and this repo has six receipts against that class.
    It asserts one safe-set literal is present, and nothing else.

    ⚠ Reads the REAL CLAUDE.md on purpose. The drift being pinned IS drift of
    that file; a canned copy under tmp_path would pin nothing at all.
    """
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text()
    manifest_citation = str(DEFAULT_MANIFEST_PATH.relative_to(REPO_ROOT))
    assert manifest_citation in claude_md, (
        f"CLAUDE.md must CITE {manifest_citation} — under Ruling 7.1 the manifest "
        "is canonical and this section is commentary. If you moved the manifest, "
        "update the citation in the same diff."
    )


def test_the_shipped_manifest_names_every_gate_claude_md_still_spells_out() -> None:
    """The honest bound of 7.1, made visible rather than merely stated.

    Prose-only drift (a sentence naming a gate with no manifest entry) is NOT
    machine-catchable in general — the ruling accepts that, because the close-out
    enumeration is GENERATED from the manifest, so an unmanifested "gate" is
    absent from every receipt the first time anyone reads one. What IS cheaply
    checkable is the reverse direction for the commands we know: each shipped
    gate's command string should appear somewhere in CLAUDE.md, so a manifest
    entry nobody documented is visible too.
    """
    claude_md = (REPO_ROOT / "CLAUDE.md").read_text()
    for spec in GateManifest.load(DEFAULT_MANIFEST_PATH).gates:
        assert spec.id in claude_md, (
            f"gate {spec.id!r} is in the manifest but CLAUDE.md never mentions it — "
            "the manifest is canonical, but a gate no human doc names is one nobody "
            "knows to read the receipt for"
        )


def test_a_gate_spec_is_frozen_and_forbids_unknown_keys() -> None:
    """A typo'd manifest key must not be a silently-ignored gate setting."""
    with pytest.raises(Exception):
        GateSpec(
            id="x",
            description="d",
            command=("true",),
            reader="ruff",
            adjudicated_by="none",
            adjudicatedby="none",  # type: ignore[call-arg]
        )
