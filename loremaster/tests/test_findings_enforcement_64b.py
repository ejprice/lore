"""Contract — packet 64b-i: the F5 WRITE-ENFORCEMENT case for the ``finding`` population (design §10.9-A
+ 63b-i-a §1.4; kickoff rulings ``e5fa7f9`` §12 "F5 enforcement [finding]" row). Authored by
``contract-64b`` (Opus 5.5 — contract tests ONLY).

The substrate is the SHIPPED one (``_governed_contract``: the whole-tree L1 scan, the effect observer, the
four-leg classifier) — this file only supplies the ``finding`` PARAMETRISATION
(``_governed_contract_64.FINDING_TREE_ALLOWLIST``), never a cloned module (design §3.2 RIDER).

THREE LAYERS, each a checked variable:
- the POPULATION: ``finding`` joins ``governed_populations()`` — DERIVED from the emitted DDL the moment
  ``_finding_statements`` appends the governed trio (RED at HEAD);
- L1 (static, whole tree): every raw SurrealQL mutation of ``finding`` in ANY workspace member is in the
  allowlist, and every site-backed allowlist entry is actually derived (no ghost) — BOTH directions;
- L2 (runtime): every OBSERVED ``finding`` state change under the real write verbs classifies (label +
  effect predicate, or the four-leg exempt), and COVERAGE is checked: every driven verb's label was seen.

The effect predicates are pure, so their discrimination is pinned offline with synthetic deltas (each
with the wrong build it kills); the live leg proves the real writes satisfy them.

Live TEST store ``:18000`` (NEVER :18500) for the runtime leg; reaped.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from _governed_contract import (
    ObservedEffect,
    ObservedWrite,
    RowDelta,
    SchemaDelta,
    classify_tree_observed_write,
    exempt_entry_is_self_contained,
    governed_populations,
    governed_table_raw_mutation_sites_in_tree,
    observe_governed_table_writes,
)
from _governed_contract_64 import (
    FINDING_TABLE,
    FINDING_TREE_ALLOWLIST,
    FINDING_WRITE_GUARD_LABELS,
    effect_finding_annotate,
    effect_finding_migrate,
    effect_finding_report,
    effect_finding_set_scope,
    effect_finding_status_edge,
    finding_world,
    new_row_id,
)

from loremaster import principals

if TYPE_CHECKING:
    from loremaster.findings import FindingLedger

    import lorerunes

    # 64b-i's RULED, not-yet-built signature this file pins — a TYPED CALL (amendment 8 §5, MP-9; a permanent
    # signature pin). Until the build lands it, a mypy error OWNED by bound `packet-64b-i-contract` (#461).
    # DUAL (r2): r1's name-only ``(FindingLedger.set_scope,)`` tuple is replaced.
    async def _ruled_64b_i_set_scope_shape(ledger: FindingLedger, subject: lorerunes.Subject) -> None:
        """kickoff §4.4 — the verb the F5 case observes, with am-7 §2's ``subject=``."""
        await ledger.set_scope(7, "server", subject=subject)


_EMPTY_SCHEMA = SchemaDelta(added=frozenset(), removed=frozenset(), changed=frozenset())
_OWNED = {"owner_principal": "principal:alice", "owner_agent": "agent:ag_a1", "scope": "keep:keepalphabravo"}


def _created(**after: Any) -> RowDelta:
    return RowDelta(id="f1", kind="created", changed_columns=frozenset(after), before=None, after=after)


def _updated(changed: set[str], before: dict[str, Any], after: dict[str, Any]) -> RowDelta:
    return RowDelta(id="f1", kind="updated", changed_columns=frozenset(changed), before=before, after=after)


def _effect(*deltas: RowDelta) -> ObservedEffect:
    return ObservedEffect(row_deltas=tuple(deltas), schema_delta=_EMPTY_SCHEMA)


class TestTheFindingTableJoinsTheGovernedPopulation:
    """The population is an OUTPUT (design §1.5c-iii): derived from the emitted DDL."""

    def test_finding_is_a_governed_population(self) -> None:
        """⚠ RED at HEAD (the finding emitter carries no governed trio)."""
        assert FINDING_TABLE in governed_populations(), (
            "finding is not in the DERIVED governed population set — _finding_statements does not append "
            "_governed_field_specs() (kickoff §Scope IN 1)"
        )


class TestEveryDerivedFindingSiteIsAllowlisted:
    """L1 both directions (design §10.9-A CORRECTION): derived ⊆ allowlisted (deny-by-default — a new
    unclassified raw write reds by name) AND every site-backed entry is derived (a ghost entry — adjudicating
    a site that does not exist — reds). The reach is the WHOLE workspace tree (derived member roots)."""

    def _derived(self) -> set[tuple[str, str, str]]:
        return {
            (site.file, site.function, site.verb)
            for site in governed_table_raw_mutation_sites_in_tree(
                FINDING_TABLE, table_const_hint="FINDING_TABLE"
            )
        }

    def test_every_derived_finding_mutation_site_is_allowlisted(self) -> None:
        """GREEN at HEAD (the two ledger sites are already listed) — the deny-by-default instrument: a build
        that adds an unclassified raw finding write anywhere reds here by name."""
        allowlisted = {
            (entry.site.file, entry.site.function, entry.site.verb) for entry in FINDING_TREE_ALLOWLIST
        }
        derived = self._derived()
        assert derived, "the whole-tree finding scan derived NOTHING — a vacuous scan"
        stray = sorted(derived - allowlisted)
        assert not stray, f"unclassified raw finding mutation sites (deny-by-default): {stray}"

    def test_no_site_backed_entry_is_a_ghost(self) -> None:
        """⚠ RED at HEAD (``principals._migrate_finding_scope`` does not exist, so its entry adjudicates a
        site the tree does not have)."""
        derived = self._derived()
        ghosts = sorted(
            (entry.site.file, entry.site.function, entry.site.verb)
            for entry in FINDING_TREE_ALLOWLIST
            if entry.l1_site and (entry.site.file, entry.site.function, entry.site.verb) not in derived
        )
        assert not ghosts, f"allowlist entries naming sites the tree does not derive: {ghosts}"

    def test_the_migrate_exempt_entry_is_self_contained(self) -> None:
        """⚠ RED at HEAD. R1 (§1.9 item 1): the exempt golden's literal, the ``governed_exempt`` block and the
        seam call live in the SAME function (``_migrate_finding_scope``) — never a module constant, never a
        helper borrowing the token."""
        entry = next(entry for entry in FINDING_TREE_ALLOWLIST if entry.exempt_name is not None)
        source = Path(principals.__file__).read_text(encoding="utf-8")
        assert exempt_entry_is_self_contained(entry, source=source), (
            "principals._migrate_finding_scope is absent or not self-contained (the golden literal, the "
            "governed_exempt block and the seam call must share ONE function — §1.9 item 1)"
        )


class TestTheFindingEffectPredicatesDiscriminate:
    """GREEN at HEAD (pure predicates over synthetic deltas) — each leg names the WRONG build it kills; the
    mutation proofs in the report flip one predicate clause and watch exactly its leg red."""

    def test_report_accepts_a_fully_governed_create_only(self) -> None:
        assert effect_finding_report(_effect(_created(number=1, **_OWNED)))
        assert not effect_finding_report(
            _effect(_created(number=1, owner_agent="agent:ag_a1", scope="server"))
        )  # no principal
        assert not effect_finding_report(
            _effect(_created(number=1, owner_principal="principal:alice", owner_agent="agent:ag_a1"))
        )  # no scope
        assert not effect_finding_report(
            _effect(_updated({"status"}, {"status": "open"}, {"status": "resolved"}))
        )  # not a create

    def test_a_status_edge_moves_only_status_and_provenance(self) -> None:
        base = {**_OWNED, "status": "open"}
        assert effect_finding_status_edge(
            _effect(_updated({"status", "provenance"}, base, {**base, "status": "resolved"}))
        )
        assert not effect_finding_status_edge(
            _effect(_updated({"status", "scope"}, base, {**base, "status": "resolved", "scope": "server"}))
        )
        assert not effect_finding_status_edge(
            _effect(_updated({"provenance"}, base, base))
        )  # no status move: annotate's shape

    def test_annotate_moves_only_provenance(self) -> None:
        base = {**_OWNED, "status": "resolved"}
        assert effect_finding_annotate(_effect(_updated({"provenance"}, base, base)))
        assert not effect_finding_annotate(
            _effect(_updated({"provenance", "status"}, base, {**base, "status": "open"}))
        )

    def test_set_scope_moves_only_the_scope(self) -> None:
        assert effect_finding_set_scope(_effect(_updated({"scope"}, _OWNED, {**_OWNED, "scope": "server"})))
        assert not effect_finding_set_scope(
            _effect(
                _updated(
                    {"scope", "owner_agent"},
                    _OWNED,
                    {**_OWNED, "scope": "server", "owner_agent": "agent:ag_b1"},
                )
            )
        )
        assert not effect_finding_set_scope(
            _effect(_updated({"scope"}, _OWNED, {**_OWNED, "scope": None}))
        )  # unscoping

    def test_migrate_stamps_only_the_scope_of_an_ownerless_unscoped_row(self) -> None:
        legacy = {"number": 1, "created_by": "ag-lead"}
        assert effect_finding_migrate(
            _effect(_updated({"scope"}, legacy, {**legacy, "scope": "keep:project"}))
        )
        stamped_owner = {**legacy, "scope": "keep:project", "owner_principal": "principal:operator"}
        assert not effect_finding_migrate(
            _effect(_updated({"scope", "owner_principal"}, legacy, stamped_owner))
        )  # F1's guess
        seized = {**legacy, "scope": "keep:elsewhere"}
        assert not effect_finding_migrate(
            _effect(_updated({"scope"}, seized, {**legacy, "scope": "keep:project"}))
        )  # re-scope


class TestClassificationOfFindingWrites:
    """The classifier over the finding allowlist: a label alone never classifies — its entry's effect must
    hold (adversary MISSING PIN #1, 63b-i-a §1.4)."""

    def test_an_unlabelled_create_is_unclassified(self) -> None:
        write = ObservedWrite(label=None, effect=_effect(_created(number=1, **_OWNED)))
        assert not classify_tree_observed_write(write, FINDING_TREE_ALLOWLIST)

    def test_a_labelled_report_with_a_governed_effect_classifies(self) -> None:
        write = ObservedWrite(
            label=FINDING_WRITE_GUARD_LABELS["report"], effect=_effect(_created(number=1, **_OWNED))
        )
        assert classify_tree_observed_write(write, FINDING_TREE_ALLOWLIST)

    def test_a_labelled_report_with_an_unstamped_effect_is_unclassified(self) -> None:
        write = ObservedWrite(label=FINDING_WRITE_GUARD_LABELS["report"], effect=_effect(_created(number=1)))
        assert not classify_tree_observed_write(write, FINDING_TREE_ALLOWLIST)

    def test_a_resolve_label_cannot_launder_a_scope_seizure(self) -> None:
        base = {**_OWNED, "status": "open"}
        seizure = _effect(
            _updated({"status", "scope"}, base, {**base, "status": "resolved", "scope": "server"})
        )
        write = ObservedWrite(label=FINDING_WRITE_GUARD_LABELS["resolve"], effect=seizure)
        assert not classify_tree_observed_write(write, FINDING_TREE_ALLOWLIST)


class TestTheLiveFindingWritesClassifyUnderF5:
    """L2 runtime, over the REAL dispatcher: every observed ``finding`` change classifies, and COVERAGE is a
    checked variable — the set of driven verbs' labels must ALL have been observed (a verb whose writes the
    observer never saw is a verb F5 cannot certify)."""

    async def test_every_driven_write_verb_is_observed_and_classifies(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """⚠ RED at HEAD (no ``capability=`` — the verbs cannot run governed).

        DUAL (r2, REPORT-adversary-64b §P1c R2): r1 drove a HAND-LIST of 7 calls (``acknowledge_many`` never
        driven) and checked coverage against its own list. The drive is now ∀ verb in the spec dict's DERIVED
        ``requires_capability`` True set (``test_findings_classes_64b.VERB_DRIVERS``, completeness-checked by
        ``_required_drivers``), and the expected labels are DERIVED from that set — a verb flipped True with
        no
        driver, or a driven verb whose writes F5 never saw, reds by name."""
        from test_findings_classes_64b import _required_drivers  # noqa: PLC0415 - ONE driver table

        drivers = _required_drivers()
        async with finding_world(monkeypatch, tmp_path) as world:
            numbers: dict[str, int] = {}
            for index, verb in enumerate(sorted(drivers)):
                owner, scope_key = ("ag-a1", "principal-private") if verb == "set_scope" else ("ag-a1", "AB")
                numbers[verb] = 9001 + index
                await world.seed(
                    row_id=new_row_id("f5"),
                    number=numbers[verb],
                    owner=owner,
                    scope_key=scope_key,
                    status="open",
                )
            with observe_governed_table_writes(FINDING_TABLE) as writes:
                for verb, driver in sorted(drivers.items()):
                    kwargs = driver.kwargs(world, numbers[verb])
                    if verb == "report":
                        kwargs = {key: value for key, value in kwargs.items() if key != "supersedes"}
                    if verb == "set_scope":
                        kwargs["scope"] = world.scopes["A"]
                    await world.findings("ag-a1" if verb == "set_scope" else "ag-b1", **kwargs)
            unclassified = [
                write for write in writes if not classify_tree_observed_write(write, FINDING_TREE_ALLOWLIST)
            ]
            assert not unclassified, f"UNCLASSIFIED finding writes (deny-by-default): {unclassified}"
            observed_labels = {write.label for write in writes}
            missing = sorted(
                verb
                for verb in drivers
                if verb != "set_scope" and FINDING_WRITE_GUARD_LABELS[verb] not in observed_labels
            )
            assert not missing, (
                f"driven verbs whose writes F5 never observed: {missing}; "
                f"saw {sorted(map(str, observed_labels))}"
            )
            assert observed_labels & {FINDING_WRITE_GUARD_LABELS["set_scope"], "guarded_write"}, (
                "the set_scope write was never observed under either admitted label: "
                f"{sorted(map(str, observed_labels))}"
            )
