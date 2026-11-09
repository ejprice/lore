"""Packet 58 contract r5 — amendment 15 fold items 3 and 6 (the SDK3 re-base).

*Every claim in this file is scoped to the tree at ``99044d0`` (branch ``feat/surreal-unification``),
2026-11-09, authored by ``contract-58-r5``.  "RED at HEAD" means RED at that commit.*

Spec: ``docs/design/2026-11-09-packet58-amendment-15.md`` §2 (58's fragments stay un-annotated) and §4.1 (58's
four classes on the TYPED, anchored-prefix classifier, built by the ONE mapping helper,
``proven_no_key`` TRUE).

* **Un-annotated fragments (§2 rider).** ``compose`` bounds ``_txn.fragment_rows``; a fragment that declares
  ``TxnFragment.rows`` lower than its statements slips the bound.  At the ``compose`` spy, every transaction a
  supersede and a boot heal send must satisfy ``fragment_rows == Σ len(statements)``.
* **The four classes (§4.1).** For each ruled class: it names its own label by construction (not the
  unspecified residue), ``_domain_rejection_error`` builds exactly that class for that label,
  ``proven_no_key`` is TRUE for it, and — through the ledger's REAL write door — an engine ``THROW`` whose
  text STARTS with the class's marker raises that class, while the same marker anywhere but the start does
  NOT (63c-i-a's anchored-prefix decision). The marker is DERIVED from ``_txn`` (the one string the
  classifier maps to the class's label), never spelled here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from _reanchor_58_support import (
    FIFTY_EIGHT_CLASS_NAMES,
    ComposeSpy,
    boot,
    bulk_seed_dependents,
    create,
    fifty_eight_thrown_markers,
    ledger58,
    raw_seed_row,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.store._txn import TxnDomainRejectionError, TxnFragment
from loremaster.tasks import TaskLedger

if TYPE_CHECKING:
    # ⚠ packet 58's RULED, not-yet-built symbols, named STATICALLY for the typecheck gate (the #461 shape):
    # mypy errors at HEAD owned by `scripts/pending_contracts.yaml` packet-58-contract.
    from loremaster.store._txn import TxnCasLostError  # noqa: F401

__all__ = ["ledger58"]

#: am-15 §4.1: packet 58's four ruled classes, resolved on ``_txn`` at run time.
FIFTY_EIGHT_CLASSES = FIFTY_EIGHT_CLASS_NAMES
#: The engine's typed kind for a THROW (SDK ``ErrorKind.THROWN``'s value, written as the engine's word — the
#: same convention as ``test_sdk3_txn_classification._THROWN_KIND``).
THROWN_KIND = "Thrown"
#: A payload placed BEFORE the marker for the echoed (not-at-start) control.
ECHO_LEAD = "a client note quoting "


def _ruled_class(name: str) -> type[TxnDomainRejectionError]:
    """The ruled class by name, from ``_txn`` (RED at HEAD by name — the class is unbuilt)."""
    cls = getattr(_txn, name, None)
    assert isinstance(cls, type) and issubclass(cls, TxnDomainRejectionError), (
        f"packet 58 rules `_txn.{name}` as a TxnDomainRejectionError subclass (am-15 §4.1); got {cls!r}"
    )
    return cls


async def _throw_through_the_ledger(ledger: TaskLedger, text: str) -> BaseException:
    """Send ``THROW $text`` through the ledger's REAL write door (``_apply`` → ``compose`` →
    ``execute_transaction``) and return what reached the caller."""
    fragment = TxnFragment(statements=["THROW $r5_payload"], params={"r5_payload": text})
    with pytest.raises(BaseException) as caught:  # noqa: PT011 - the TYPE is the assertion below
        await ledger._apply([fragment])  # noqa: SLF001 - the ledger's own write door IS the seam
    return caught.value


class TestFiftyEightsFragmentsAreUnannotated:
    """am-15 §2 rider (fold item 3): ∀ transactions a supersede and a boot heal send, ``fragment_rows`` equals
    the composed statement count — no ``rows=`` annotation on 58's path (a lower one slips the row bound)."""

    async def test_every_supersede_and_heal_transaction_counts_one_row_per_statement(
        self, ledger58: tuple[TaskLedger, SurrealEnv]
    ) -> None:
        ledger, env = ledger58
        blockers = [await create(ledger, f"successor blocker {i}") for i in range(2)]
        old = await create(ledger, "a hub")
        await bulk_seed_dependents(ledger, old, 3, tag="r5rows")
        head = await create(ledger, "a straggler head")
        legacy = "r5rowslegacyblocker0000000000000"
        await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
        await bulk_seed_dependents(ledger, legacy, 3, tag="r5strag")
        spy = ComposeSpy()
        with spy.installed():
            await supersede(ledger, old, blocked_by=blockers)
            await boot(env)
        assert spy.calls and spy.heal_calls(), (
            f"non-vacuity: the spy saw {len(spy.calls)} transactions and {len(spy.heal_calls())} "
            f"heal chunks — "
            "both a supersede and a heal must be measured"
        )
        assert spy.annotated_calls() == [], (
            f"(rows, statements) of 58-path transactions whose fragment_rows ≠ statement count: "
            f"{spy.annotated_calls()} — a `rows=` annotation on 58's fragments (am-15 §2)"
        )

    def test_CONTROL_the_check_sees_an_annotated_fragment(self) -> None:
        """The detector fires on a fragment that DOES declare rows (fails for a different reason than the
        pin above: no store, no 58 code — only the spy's own accounting)."""
        spy = ComposeSpy()
        spy(TxnFragment(statements=["RETURN 1", "RETURN 2"], params={}, rows=1))
        assert spy.annotated_calls() == [(1, 2)], spy.annotated_calls()


class TestTheFourClassesAreTypedAndAnchored:
    """am-15 §4.1 (fold item 6) — RED at HEAD (the four classes are unbuilt)."""

    @pytest.mark.parametrize("name", FIFTY_EIGHT_CLASSES)
    def test_the_class_is_recognised_by_construction_and_built_by_the_one_mapping_helper(
        self, name: str
    ) -> None:
        cls = _ruled_class(name)
        label = cls._constructed_error_class()  # noqa: SLF001 - am-37 §15.2's construction seam
        assert label != _txn._ERROR_CLASS_UNSPECIFIED, f"{name} carries the unspecified residue label"
        built = _txn._domain_rejection_error(label, f"{name} probe", kind=THROWN_KIND)
        assert type(built) is cls, (
            f"_domain_rejection_error({label!r}) built {type(built).__name__}, not {name}"
        )
        assert built.error_class == label and built.kind == THROWN_KIND
        assert _txn.proven_no_key(built), (
            f"a THROW rolled the transaction back: proven_no_key({name}) must be TRUE"
        )

    @pytest.mark.parametrize("name", FIFTY_EIGHT_CLASSES)
    async def test_a_THROW_LED_by_the_marker_raises_the_class_and_an_echoed_marker_does_not(
        self, ledger58: tuple[TaskLedger, SurrealEnv], name: str
    ) -> None:
        ledger, _env = ledger58
        cls = _ruled_class(name)
        marker = fifty_eight_thrown_markers()[name]
        led = await _throw_through_the_ledger(ledger, f"{marker} r5 probe")
        assert type(led) is cls, f"a THROW led by {marker!r} raised {type(led).__name__}: {led}"
        echoed = await _throw_through_the_ledger(ledger, f"{ECHO_LEAD}{marker} r5 probe")
        assert not isinstance(echoed, cls), (
            f"a THROW that merely QUOTES {marker!r} (not at the start) classified as {name} — the substring "
            f"classifier 63c-i-a's typed decision forbids (amendments 35 §2 / 36 §1.1)"
        )
        assert (
            isinstance(echoed, TxnDomainRejectionError)
            and echoed.error_class == _txn._ERROR_CLASS_UNSPECIFIED
        ), f"the echoed THROW must be the unspecified residue: {type(echoed).__name__} {echoed!r}"
