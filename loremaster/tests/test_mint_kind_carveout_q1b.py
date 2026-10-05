"""am-37 §15 + §15.1 (contract-mint-q1b, 2026-10-05): ``TxnDomainRejectionError`` is NOT uniformly
"proven no key". The engine's TYPED kind decides, through ONE predicate ``_txn.proven_no_key``, and that ONE
predicate decides the mint's catch, its message AND its note.

Its own file so its pending-build reds are owned NARROWLY by ONE self-destructing bound
(``scripts/pending_contracts.yaml`` id ``am37-15-q1b-mint-contract``): the currency gate owns pytest reds at
FILE
granularity. Every "RED" claim in REPORT-contract-mint-q1b.md is scoped to ``4ac88fb``.

The INDEPENDENT expected values are §15's table, WRITTEN OUT below (``_RULED_KIND_FATE``); the domain is the
SDK's own enumerations (``ErrorKind`` ∪ ``KIND_TO_CLASS`` ∪ ``QueryDetailKind``), GENERATED, so a kind the SDK
gains reds here by name. Every typed rejection is built through the REAL seam
(``_txn._raise_attempt_failure`` over a real SDK error), so the producer↔consumer handoff is the one
exercised.

⚠ FORK (REPORT-contract-mint-q1b.md §FORK-1): a live UNIQUE-index collision arrives as SDK kind ``Internal``
(probed on ``:18000``, 2026-10-05). §15's table rules "UNIQUE → proven" AND "Internal → unknown"; this
contract pins the reading that keeps §15's own "the live UNIQUE pin stands" (the UNIQUE-classified Internal is
PROVEN) in ONE class, ``TestAUniqueIndexCollisionUnderInternalIsProven``, so a contrary ruling deletes one
class.
"""

from __future__ import annotations

import asyncio
import logging
import re
import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
import surrealdb.errors as sdk_errors
import test_am37_13_3_63c_i_a as fix531d  # module-qualified: its Test* classes are not re-collected here
import test_mint_unknown_outcome_note_q1 as q1  # module-qualified, same reason
from loremaster.principal_keys import PrincipalKeyStoreError
from loremaster.store import _txn as _txn_module
from loremaster.store._txn import (
    SurrealConnectionError,
    SurrealStoreError,
    TxnDomainRejectionError,
    wrap_store_rejection,
)

import loremaster
from lorerunes import reclassify

# --------------------------------------------------------------------------- #
# The independent adjudication — §15's table, written out (never computed from production).
# --------------------------------------------------------------------------- #

_PROVEN = "proven"
_UNKNOWN = "unknown"
_TRANSPORT = "transport"

#: §15 "Adjudication over the SDK's own enumerations". Query detail kinds are keyed by their DETAIL value
#: (``QueryDetailKind``), top-level kinds by their ``ErrorKind`` value.
#: ⚠ ``"Query"`` itself (a Query error carrying NO detail kind) is NOT in §15's table: SPEC-SILENT. It is
#: ruled UNKNOWN here on §15's own asymmetry ("a conditional note on a fault that was in truth pre-commit
#: costs
#: one list-keys; the reverse costs a live credential") — REPORT §FORK-2 asks for the ruling.
_RULED_KIND_FATE: dict[str, str] = {
    "Validation": _PROVEN,
    "Thrown": _PROVEN,
    "AlreadyExists": _PROVEN,
    "NotFound": _PROVEN,
    "Configuration": _PROVEN,
    "NotExecuted": _PROVEN,
    "NotAllowed": _TRANSPORT,
    "Connection": _TRANSPORT,
    "Internal": _UNKNOWN,
    "Serialization": _UNKNOWN,
    "TimedOut": _UNKNOWN,
    "Cancelled": _UNKNOWN,
    "Query": _UNKNOWN,  # FORK-2: spec-silent, safe side
}

#: §15.2 (RULED, 9813259): the ``TxnDomainRejectionError`` subclasses CLASSIFIED BY CONSTRUCTION — proven
#: whatever their kind, because recognition means the engine evaluated the statement and refused it.
_RULED_CLASSIFIED_BY_CONSTRUCTION: frozenset[str] = frozenset(
    {"TxnUniqueViolationError", "TxnGovernedConflictError"}
)

#: §15.2: the classifier's labels, written out. Every label but ``unspecified rejection`` is a RECOGNISED
#: refusal
#: (proven ∀ kind); the §15 kind table applies ONLY to the unspecified residue.
_RULED_UNSPECIFIED_LABEL = "unspecified rejection"
_RULED_CLASSIFIED_LABEL_NAMES: frozenset[str] = frozenset(
    {
        "_ERROR_CLASS_ASSERT_VIOLATION",
        "_ERROR_CLASS_FIELD_COERCION",
        "_ERROR_CLASS_GOVERNED_CONFLICT",
        "_ERROR_CLASS_QUERY_TOO_COMPLEX",
        "_ERROR_CLASS_RETRYABLE_CONFLICT",
        "_ERROR_CLASS_UNIQUE_VIOLATION",
    }
)
#: §15.3 (RULED, dde69a6): the unspecified × kind axis is ALLOWLIST-driven — moved, re-keyed, to
#: ``test_mint_kind_allowlist_q1c.py`` (``_RULED_PROVEN_KINDS``).

#: §15 row 2 + §15.1: the classes proven by CLASS, whatever their kind (rolled back / never sent).
_RULED_PROVEN_BY_CLASS: frozenset[str] = frozenset(
    {"TxnContentionExhaustedError", "TxnParamCollisionError", "TxnEnvelopeViolationError"}
)


def _sdk_kind_domain() -> set[str]:
    """GENERATED from the installed SDK: every top-level kind (``ErrorKind`` values ∪ ``KIND_TO_CLASS`` keys)
    plus every ``QueryDetailKind`` value. Never a hand-list."""

    def values_of(enum_like: type) -> set[str]:
        return {value for name, value in vars(enum_like).items() if name.isupper() and isinstance(value, str)}

    return (
        values_of(sdk_errors.ErrorKind)
        | set(sdk_errors.KIND_TO_CLASS)
        | values_of(sdk_errors.QueryDetailKind)
    )


_QUERY_DETAIL_KINDS: frozenset[str] = frozenset(
    value
    for name, value in vars(sdk_errors.QueryDetailKind).items()
    if name.isupper() and isinstance(value, str)
)


def _sdk_error(kind: str, *, message: str | None = None) -> sdk_errors.ServerError:
    """A REAL SDK error of ``kind``, built by the SDK's own query-error parser (the shape the transactional
    and single-statement paths both receive). A Query detail kind rides ``details`` under top-level ``Query``;
    ``"Query"`` alone carries no detail kind. Messages are realistic and never start with a marker the
    classifier keys a label on (except where a cell says so)."""
    text = message if message is not None else f"injected q1b: the engine reported a {kind} error"
    if kind in _QUERY_DETAIL_KINDS:
        details: dict[str, Any] = {"kind": kind}
        if kind == sdk_errors.QueryDetailKind.TIMED_OUT:
            details["details"] = {"duration": {"secs": 5, "nanos": 0}}  # the engine's {secs, nanos} shape
        return sdk_errors.parse_query_error({"kind": "Query", "result": text, "details": details})
    return sdk_errors.parse_query_error({"kind": kind, "result": text})


async def _through_the_seam(sdk_error: BaseException) -> BaseException:
    """What the driver's ONE failure ladder raises for ``sdk_error`` (``_raise_attempt_failure``, the
    single-statement path ``PrincipalKeyStore._query`` rides)."""
    dropped: list[object] = []

    async def drop(connection: object) -> None:
        dropped.append(connection)

    try:
        await _txn_module._raise_attempt_failure(  # noqa: SLF001
            sdk_error,
            object(),
            drop=drop,
            url="ws://127.0.0.1:1/rpc",
            noun="principal key query",
            label="principal.key.query.rejected",
            logger=logging.getLogger("test.q1b"),
        )
    except BaseException as raised:  # noqa: BLE001 - the ladder's raise IS the observation
        return raised
    raise AssertionError("unreachable: the failure ladder returned")  # pragma: no cover


def _typed_rejection(kind: str, *, message: str | None = None) -> BaseException:
    return asyncio.run(_through_the_seam(_sdk_error(kind, message=message)))


def _proven_no_key() -> Callable[[BaseException], bool]:
    """STUB EXPECTATION: ``_txn.proven_no_key`` does not exist before the build, so every cell reading it is
    RED by AttributeError, by name, until then."""
    predicate = _txn_module.proven_no_key
    assert callable(predicate), type(predicate)
    return predicate


_DOMAIN: list[str] = sorted(_sdk_kind_domain())
_NON_TRANSPORT_KINDS: list[str] = [kind for kind in _DOMAIN if _RULED_KIND_FATE.get(kind) != _TRANSPORT]
_EMAIL, _NAME = fix531d._PLAIN  # noqa: SLF001
_NOT_LANDED = f"could not mint key {_NAME!r} for principal {_EMAIL!r}"
#: The ``TxnDomainRejectionError`` family in the GENERATED ``_txn`` taxonomy: decided by KIND (§15).
_KIND_DECIDED_CLASSES: list[type[BaseException]] = [
    cls
    for cls in fix531d._store_taxonomy()  # noqa: SLF001
    if issubclass(cls, TxnDomainRejectionError)
]


# --------------------------------------------------------------------------- #
# (i) completeness over the SDK's own enumerations
# --------------------------------------------------------------------------- #


class TestEveryEngineKindIsAdjudicated:
    """am-37 §15 pin (i): every kind the installed SDK enumerates is ruled proven / unknown / transport by the
    table above. A kind the SDK gains reds BY NAME; a ruled kind the SDK dropped reds BY NAME."""

    def test_the_generated_domain_is_not_vacuous(self) -> None:
        assert {"Internal", "Serialization", "TimedOut", "Cancelled", "Validation", "NotExecuted"} <= set(
            _DOMAIN
        )

    def test_every_kind_is_ruled(self) -> None:
        unruled = set(_DOMAIN) - set(_RULED_KIND_FATE)
        retired = set(_RULED_KIND_FATE) - set(_DOMAIN)
        # am-37 §15.4 rider: the failure text names the table and BOTH dispositions, so an SDK-bump author
        # adjudicates the new kind in place instead of deleting this pin.
        assert not unruled, (
            f"SDK kind(s) nobody adjudicated: {sorted(unruled)}. Rule each against the am-37 §15 table "
            f"(§15.3: docs/design/2026-09-29-packet63c-amendment-37.md) — EITHER (a) it is proven no-key: "
            f"add it to _txn._PROVEN_KINDS WITH evidence, a §15 proven row, and a 'proven' entry in "
            f"_RULED_KIND_FATE here; OR (b) leave it off _PROVEN_KINDS (it is then unknown by rule) and add "
            f"it to _RULED_KIND_FATE here as 'unknown'. Do not delete this pin."
        )
        assert not retired, (
            f"ruled kind(s) the SDK no longer enumerates: {sorted(retired)}. Retire each from the am-37 §15 "
            f"table (§15.3) and from _RULED_KIND_FATE here (and from _txn._PROVEN_KINDS if it is a proven "
            f"row) — do not delete this pin."
        )

    @pytest.mark.parametrize("kind", _DOMAIN)
    async def test_the_seam_and_the_predicate_agree_with_the_ruling(self, kind: str) -> None:
        """GENERATED ∀ kind, through the REAL seam: a transport kind becomes ``SurrealConnectionError`` (and
        is
        never proven); every other kind becomes a ``TxnDomainRejectionError`` carrying a typed, non-None
        ``kind``, and ``proven_no_key`` answers exactly the ruled fate."""
        predicate = _proven_no_key()
        raised = await _through_the_seam(_sdk_error(kind))
        fate = _RULED_KIND_FATE[kind]
        if fate == _TRANSPORT:
            assert type(raised) is SurrealConnectionError, type(raised)
            assert predicate(raised) is False
            return
        assert isinstance(raised, TxnDomainRejectionError), type(raised)
        typed_kind = getattr(raised, "kind")  # noqa: B009 - a stub expectation: red by name
        assert isinstance(typed_kind, str) and typed_kind, (
            f"a typed input must carry its kind, got {typed_kind!r}"
        )
        assert typed_kind == kind, "the typed kind is the SDK's own (the Query DETAIL kind for a Query error)"
        assert predicate(raised) is (fate == _PROVEN), (kind, fate)


# --------------------------------------------------------------------------- #
# the class half, the kind-less rule, and the non-store faults
# --------------------------------------------------------------------------- #


class TestThePredicateOverTheTaxonomy:
    """§15.1: ∀ ``_txn`` store class: the class-proven half is proven whatever its kind; the
    ``TxnDomainRejectionError`` family is decided by kind, and KIND-LESS (a bare-text input) is UNKNOWN; the
    connection class and the bare base are never proven; nor is any non-store fault."""

    def test_every_generated_store_class_is_adjudicated(self) -> None:
        derived = {cls.__name__ for cls in fix531d._store_taxonomy()}  # noqa: SLF001
        kind_decided = {
            cls.__name__ for cls in fix531d._store_taxonomy() if issubclass(cls, TxnDomainRejectionError)
        }  # noqa: SLF001
        ruled = _RULED_PROVEN_BY_CLASS | kind_decided | {SurrealConnectionError.__name__}
        assert derived == ruled, (
            f"unadjudicated: {sorted(derived - ruled)} · retired: {sorted(ruled - derived)}"
        )
        assert not (_RULED_PROVEN_BY_CLASS & kind_decided)

    @pytest.mark.parametrize("cls", fix531d._store_taxonomy(), ids=lambda cls: cls.__name__)  # noqa: SLF001
    def test_a_kind_less_instance(self, cls: type[BaseException]) -> None:
        predicate = _proven_no_key()
        instance = fix531d._instance(cls)  # noqa: SLF001 - constructed WITHOUT a kind (the bare-text shape)
        if issubclass(cls, TxnDomainRejectionError):
            assert getattr(instance, "kind") is None, "a kind-less rejection's kind is None"  # noqa: B009
            # §15.2: UNIQUE / governed are CLASSIFIED BY CONSTRUCTION (proven whatever the kind); a bare base
            # rejection is the unclassified residue, and kind-less ⇒ UNKNOWN (§15 safe side).
            assert predicate(instance) is (cls.__name__ in _RULED_CLASSIFIED_BY_CONSTRUCTION), cls.__name__
        else:
            assert predicate(instance) is (cls.__name__ in _RULED_PROVEN_BY_CLASS), cls.__name__

    @pytest.mark.parametrize(
        "fault",
        [
            SurrealStoreError("injected q1b: bare base"),
            asyncio.CancelledError(),
            KeyboardInterrupt(),
            TimeoutError("injected q1b"),
            RuntimeError("injected q1b: a future unknown"),
            *(q1._construct(cls) for cls in q1._FOREIGN),  # noqa: SLF001
        ],
        ids=lambda fault: type(fault).__name__,
    )
    def test_a_non_taxonomy_fault_is_never_proven(self, fault: BaseException) -> None:
        assert _proven_no_key()(fault) is False


def _error_class_labels() -> dict[str, str]:
    """GENERATED: every ``_ERROR_CLASS_*`` label the classifier can produce (name → label)."""
    return {
        name: value
        for name, value in vars(_txn_module).items()
        if name.startswith("_ERROR_CLASS_") and isinstance(value, str)
    }


#: §15.2's classification-axis pin (``TestTheClassificationAxis``) MOVED to
#: ``test_mint_kind_allowlist_q1c.py::TestTheClassificationAxisIsAllowlistDriven`` (am-37 §15.3 re-keys its
#: ``unspecified`` × ``NotAllowed`` cell TRUE → FALSE and adds the unenumerated kinds).


def _classified_internal_messages() -> dict[str, str]:
    """REAL-shaped ``Internal`` engine texts the classifier RECOGNISES (built from its own markers), the shape
    a live UNIQUE / ASSERT / coercion refusal arrives in on 3.2.4 (probed :18000, 2026-10-05, for UNIQUE)."""
    return {
        "unique": (
            "Database index `principal_key_principal_name` already contains "
            "[principal:abc531d, 'laptop'], with record `principal_key:k531d`"
        ),
        "assert": (
            f"Found 'x' for field `name`, with record `principal_key:k531d`, but field must conform to: "
            f"string::len($value) > 0 — {_txn_module._ASSERT_VIOLATION_MARKER}"  # noqa: SLF001
        ),
        "coercion": (
            f"{_txn_module._FIELD_COERCION_MARKER} field `created_at`: expected a datetime"  # noqa: SLF001
        ),
    }


class TestAClassifiedInternalRefusalIsProvenAtTheMint:
    """§15.2 live/seam cells: a UNIQUE / ASSERT / coercion refusal arrives as kind ``Internal`` and is
    RECOGNISED by the classifier → the mint says "could not mint", with NO note. (The LIVE UNIQUE pin
    stands unchanged:
    ``test_am37_13_3_63c_i_a.py::TestALiveUniqueCollisionCarriesNoRevokeAdvice``.) The CONTROL: an
    unrecognised ``Internal`` is the unknown fate (``TestTheMintFollowsTheKind[Internal]``)."""

    @pytest.mark.parametrize("refusal", sorted(_classified_internal_messages()))
    async def test_a_classified_internal_refusal(self, monkeypatch: pytest.MonkeyPatch, refusal: str) -> None:
        injected = await _through_the_seam(
            _sdk_error("Internal", message=_classified_internal_messages()[refusal])
        )
        assert isinstance(injected, TxnDomainRejectionError), type(injected)
        assert getattr(injected, "error_class") != _RULED_UNSPECIFIED_LABEL, (
            "fixture: the classifier must recognise it"
        )  # noqa: B009
        assert getattr(injected, "kind") == "Internal"  # noqa: B009
        _assert_proven_fate(await _mint_with(monkeypatch, injected), injected)


class _FakeTransactionConnection:
    """The transactional path's connection, answering ONE rolled-back ERR entry (the engine's per-statement
    shape: status / result / kind / details) and no RPC-level error."""

    def __init__(self, entry: dict[str, Any]) -> None:
        self.entry = entry

    async def query_raw(self, _statement: str, _params: dict[str, Any] | None = None) -> dict[str, Any]:
        return {"result": [self.entry]}

    def check_response_for_error(self, _response: Any, *_args: Any, **_kwargs: Any) -> None:
        return None


async def _through_the_transaction(kind: str) -> BaseException:
    entry: dict[str, Any] = {"status": "ERR", "result": f"injected q1b: the engine reported a {kind} error"}
    if kind in _QUERY_DETAIL_KINDS:
        entry |= {"kind": "Query", "details": {"kind": kind}}
    else:
        entry["kind"] = kind

    async def acquire() -> Any:  # the fake stands in for the SDK connection (duck-typed, two methods)
        return _FakeTransactionConnection(entry)

    async def drop(_connection: object) -> None:
        return None

    try:
        await _txn_module._run_verified_transaction(  # noqa: SLF001
            "BEGIN; CREATE principal_key CONTENT {}; COMMIT;",
            {},
            acquire=acquire,
            drop=drop,
            url="ws://127.0.0.1:1/rpc",
            deadline_seconds=1.0,
        )
    except BaseException as raised:  # noqa: BLE001 - the raise IS the observation
        return raised
    raise AssertionError("unreachable: a rolled-back transaction returned")  # pragma: no cover


class TestTheTransactionalRaiseSitePassesTheKind:
    """§15.2 mechanics: BOTH raise sites pass a kind derived from the typed error. The single-statement site
    is pinned by ``TestEveryEngineKindIsAdjudicated``; this pins ``_run_verified_transaction``'s (via
    ``failed.typed``), generated ∀ non-transport kind."""

    @pytest.mark.parametrize("kind", [kind for kind in _NON_TRANSPORT_KINDS if kind != "Query"])
    async def test_the_transactional_rejection_carries_its_kind(self, kind: str) -> None:
        raised = await _through_the_transaction(kind)
        assert isinstance(raised, TxnDomainRejectionError), type(raised)
        assert getattr(raised, "kind") == kind  # noqa: B009
        assert _proven_no_key()(raised) is (_RULED_KIND_FATE[kind] == _PROVEN), kind


# --------------------------------------------------------------------------- #
# (ii) / §15.1 (b) — the mint, ∀ kind
# --------------------------------------------------------------------------- #


async def _mint_with(monkeypatch: pytest.MonkeyPatch, injected: BaseException) -> BaseException:
    return await q1._served(monkeypatch, injected)  # noqa: SLF001 - CREATE reached (#194) is asserted there


def _assert_proven_fate(served: BaseException, injected: BaseException) -> None:
    assert type(served) is PrincipalKeyStoreError, type(served)
    assert str(served) == _NOT_LANDED, str(served)
    assert served.__cause__ is injected
    fix531d._note_free_chain(served)  # noqa: SLF001
    rendered = fix531d._rendered(served)  # noqa: SLF001 - _fault_line + the full traceback
    assert "revoke-key" not in rendered and "list-keys" not in rendered, rendered


def _assert_unknown_fate(served: BaseException, injected: BaseException) -> None:
    """Mechanism (d) (lead's binding constraint): the OUTER wrap keeps the class ``PrincipalKeyStoreError``
    (#400) with the cause-neutral outcome-unknown message; the note is the conditional one; and "could not
    mint" appears NOWHERE lore-adm can print (``str``, ``_fault_line``, ``traceback.format_exception``)."""
    assert type(served) is PrincipalKeyStoreError, type(served)
    assert served.__cause__ is injected
    notes = getattr(served, "__notes__", None) or []
    assert len(notes) == 1, notes
    q1._assert_conditional_shape(notes[0], email=_EMAIL, name=_NAME)  # noqa: SLF001
    q1._assert_cause_neutral_message(str(served))  # noqa: SLF001
    rendered = fix531d._rendered(served) + "\n" + str(served)  # noqa: SLF001
    assert "could not mint" not in rendered.lower(), rendered
    assert notes[0] in "".join(traceback.format_exception(served)), "the traceback prints the note"


class TestTheMintFollowsTheKind:
    """§15 pin (ii) + §15.1 pin (b), GENERATED ∀ non-transport kind: a typed rejection during the CREATE. The
    expected fate is the RULED table (never the predicate), so a predicate that is wrong AND consulted
    reds."""

    @pytest.mark.parametrize("kind", _NON_TRANSPORT_KINDS)
    async def test_a_typed_rejection_during_the_CREATE(
        self, monkeypatch: pytest.MonkeyPatch, kind: str
    ) -> None:
        injected = await _through_the_seam(_sdk_error(kind))
        assert isinstance(injected, TxnDomainRejectionError), type(injected)
        served = await _mint_with(monkeypatch, injected)
        if _RULED_KIND_FATE[kind] == _PROVEN:
            _assert_proven_fate(served, injected)
        else:
            _assert_unknown_fate(served, injected)

    @pytest.mark.parametrize(
        "cls",
        _KIND_DECIDED_CLASSES,
        ids=lambda cls: cls.__name__,
    )
    async def test_a_kind_less_rejection_during_the_CREATE(
        self, monkeypatch: pytest.MonkeyPatch, cls: type[BaseException]
    ) -> None:
        """§15: a kind-less UNCLASSIFIED rejection is UNKNOWN (safe side); §15.2: a class that is classified
        by        construction (UNIQUE, governed) is PROVEN even kind-less."""
        injected = fix531d._instance(cls)  # noqa: SLF001
        served = await _mint_with(monkeypatch, injected)
        if cls.__name__ in _RULED_CLASSIFIED_BY_CONSTRUCTION:
            _assert_proven_fate(served, injected)
        else:
            _assert_unknown_fate(served, injected)


# --------------------------------------------------------------------------- #
# §15.1 (a) — lorerunes: a predicate catch, with the tuple form unchanged (DUAL)
# --------------------------------------------------------------------------- #


class _Passed(Exception):
    """A pass-through class (checked first)."""


class _Explained(Exception):
    """A fault the predicate explains."""


class _Unexplained(Exception):
    """A fault the predicate does not explain."""


class _Domain(Exception):
    """The translation target."""


class TestReclassifyHonoursAPredicateCatch:
    """§15.1 pin (a): ``reclassify(catch=<predicate>)`` translates iff the predicate is TRUE (``from`` the
    original, ``make_error`` called once), re-raises UNTOUCHED iff FALSE (same object, no new cause, no
    factory call), and still checks ``passthrough`` FIRST. The predicate receives the exception itself."""

    @staticmethod
    def _run(raised: BaseException, *, catch: Any) -> tuple[BaseException, list[BaseException], int]:
        seen: list[BaseException] = []
        built = {"count": 0}

        def make_error() -> BaseException:
            built["count"] += 1
            return _Domain("translated")

        def predicate(error: BaseException) -> bool:
            seen.append(error)
            return isinstance(error, _Explained)

        try:
            with reclassify(
                passthrough=(_Passed,),
                catch=predicate if catch == "predicate" else catch,
                make_error=make_error,
            ):
                raise raised
        except BaseException as served:  # noqa: BLE001 - the served fault IS the observation
            return served, seen, built["count"]
        raise AssertionError("unreachable: reclassify swallowed")  # pragma: no cover

    def test_a_true_predicate_translates(self) -> None:
        raised = _Explained("x")
        served, seen, built = self._run(raised, catch="predicate")
        assert type(served) is _Domain and served.__cause__ is raised
        assert seen == [raised] and built == 1

    def test_a_false_predicate_passes_the_SAME_object_untouched(self) -> None:
        raised = _Unexplained("y")
        served, seen, built = self._run(raised, catch="predicate")
        assert served is raised and served.__cause__ is None
        assert seen == [raised] and built == 0

    def test_passthrough_is_checked_before_the_predicate(self) -> None:
        raised = _Passed("z")
        served, seen, built = self._run(raised, catch="predicate")
        assert served is raised and built == 0
        assert seen == [], "a pass-through must never reach the predicate"

    def test_a_base_exception_the_predicate_rejects_propagates(self) -> None:
        raised = KeyboardInterrupt()
        served, _seen, built = self._run(raised, catch="predicate")
        assert served is raised and built == 0

    def test_DUAL_the_tuple_form_is_unchanged(self) -> None:
        explained, unexplained = _Explained("t"), _Unexplained("u")
        served, _seen, built = self._run(explained, catch=(_Explained,))
        assert type(served) is _Domain and served.__cause__ is explained and built == 1
        served, _seen, built = self._run(unexplained, catch=(_Explained,))
        assert served is unexplained and built == 0


class TestTheWrapAcceptsTheStorePredicate:
    """§15.1: ``wrap_store_rejection(..., catch=proven_no_key)`` translates a proven fault and passes an
    unproven store fault UNTOUCHED (its own class); the default (tuple) catch is unchanged for the 20 other
    callers (``test_mint_unknown_outcome_note_q1.py::TestTheOtherWrapCallersAreUnchanged``)."""

    @pytest.mark.parametrize("kind", ["Validation", "TimedOut"])
    def test_the_predicate_catch(self, kind: str) -> None:
        injected = _typed_rejection(kind)
        try:
            with wrap_store_rejection(PrincipalKeyStoreError, "inner", catch=_proven_no_key()):
                raise injected
        except BaseException as served:  # noqa: BLE001 - the served fault IS the observation
            if _RULED_KIND_FATE[kind] == _PROVEN:
                assert type(served) is PrincipalKeyStoreError and served.__cause__ is injected
            else:
                assert served is injected, "an unproven fault passes the predicate wrap UNTOUCHED"


# --------------------------------------------------------------------------- #
# (iii) ONE predicate decides catch, message AND note — by MUTATION
# --------------------------------------------------------------------------- #


def _rebind_all(monkeypatch: pytest.MonkeyPatch, value: object, replacement: object) -> int:
    bindings = q1._loremaster_bindings_of(value)  # noqa: SLF001 - identity-found, any import spelling
    for namespace, attribute in bindings:
        monkeypatch.setattr(namespace, attribute, replacement)
    return len(bindings)


class TestOnePredicateDecidesCatchMessageAndNote:
    """§15 pin (iii) + §15.1: flipping one member of EITHER half moves BOTH the message and the note of its
    mint cell. A second decider (a class tuple for the catch, a private kind list, an ``isinstance`` ladder in
    the note) keeps one of the two and reds here. The KIND-half legs (§15.3: the allowlist ``_PROVEN_KINDS``
    replaces the deny-list) live in ``test_mint_kind_allowlist_q1c.py::TestTheAllowlistIsTheOneDecider``."""

    async def test_moving_a_class_OUT_of_the_class_half_flips_the_note(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The class half (§15.1 ``_PROVEN_NO_KEY_CLASSES``). ``TxnParamCollisionError`` is translated by the
        inner wrap when proven; moved out, it must reach the outer wrap with the conditional note."""
        classes = getattr(_txn_module, "_PROVEN_NO_KEY_CLASSES")  # noqa: B009 - §15.1 names it: red by name
        cls = next(c for c in fix531d._store_taxonomy() if c.__name__ == "TxnParamCollisionError")
        injected = fix531d._instance(cls)  # noqa: SLF001
        _assert_proven_fate(await _mint_with(monkeypatch, injected), injected)  # the CONTROL
        assert _rebind_all(monkeypatch, classes, tuple(c for c in classes if c is not cls)) >= 1
        injected = fix531d._instance(cls)  # noqa: SLF001
        _assert_unknown_fate(await _mint_with(monkeypatch, injected), injected)

    async def test_replacing_the_predicate_moves_catch_and_note_together(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Every binding of ``proven_no_key`` replaced by "never proven": a Validation rejection must then
        lose its not-landed message (the CATCH asked the predicate) AND gain the note (the NOTE asked it)."""
        predicate = _proven_no_key()
        assert _rebind_all(monkeypatch, predicate, lambda _error: False) >= 1
        injected = await _through_the_seam(_sdk_error("Validation"))
        _assert_unknown_fate(await _mint_with(monkeypatch, injected), injected)


# --------------------------------------------------------------------------- #
# §15.1: ``_PROVEN_NO_KEY_FAULTS`` is REPLACED — retired-name hygiene (bare, anchor-free)
# --------------------------------------------------------------------------- #

_RETIRED = "_PROVEN_NO_KEY_FAULTS"


class TestTheRetiredTupleIsGone:
    """§15.1: the predicate REPLACES the tuple as the target. A bare, anchor-free scan of the production
    package (code AND prose: docstrings, comments) finds no surviving mention, and ``_txn`` binds no such
    name. Positive control: the scan finds the name in a synthetic text."""

    @staticmethod
    def _hits(text: str) -> list[int]:
        return [number for number, line in enumerate(text.splitlines(), 1) if re.search(_RETIRED, line)]

    def test_CONTROL_the_scan_sees_the_name(self) -> None:
        assert self._hits(f"x = 1\n# see {_RETIRED} here\n") == [2]

    def test_no_production_module_mentions_it(self) -> None:
        package = Path(loremaster.__file__).resolve().parent
        sources = sorted(path for path in package.rglob("*.py") if "tests" not in path.parts)
        assert len(sources) > 20, "the scan's population is vacuous"
        found = {str(path.relative_to(package)): self._hits(path.read_text()) for path in sources}
        assert not {path: lines for path, lines in found.items() if lines}, found

    def test_the_store_layer_binds_no_such_name(self) -> None:
        assert not hasattr(_txn_module, _RETIRED)
