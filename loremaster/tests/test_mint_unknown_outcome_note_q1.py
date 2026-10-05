"""am-37 §14 Q1 (contract-mint-q1, operator-ruled "Yes, separate cycle", 2026-10-04): the mint note's
domain is INVERTED. Before the engine answers, the revoke note is withheld IFF the fault PROVES no key landed,
meaning the store layer's own refusal / pre-send taxonomy, ONE exported tuple ``_txn._PROVEN_NO_KEY_FAULTS``.
EVERY other fault gets the CONDITIONAL note: cancellation (asyncio, anyio), an interrupt, a timeout, a raw
transport fault, a future unknown, and the bare store base.

Its own file so that its pending-build reds are owned NARROWLY: the currency gate owns pytest reds at FILE
granularity (``pending_contract_gate.partition_pytest``). Registering fix531d's whole file would blind its
other pins until the build lands (am-37 §2 F-15's masking class).

The generated taxonomy leg and its contract-side completeness stay in ``test_am37_13_3_63c_i_a.py`` (green
at ``c633fbf``, re-keyed there by DUAL), and this file reuses that module's fixtures. Every "RED" claim in
REPORT-contract-mint-q1.md is scoped to ``c633fbf``.
"""

from __future__ import annotations

import asyncio
import copy
import errno
import importlib
import pkgutil
import shlex
import sys
import traceback
from typing import Any

import anyio
import pytest
import test_am37_13_3_63c_i_a as fix531d  # module-qualified: its Test* classes are not re-collected here
from loremaster.principal_keys import PrincipalKeyStore, PrincipalKeyStoreError
from loremaster.store import _txn as _txn_module
from loremaster.store._txn import (
    SurrealConnectionError,
    SurrealStoreError,
    TxnDomainRejectionError,
    wrap_store_rejection,
)
from pydantic import SecretStr

import loremaster


def _unknown_outcome_faults() -> list[BaseException]:
    """am-37 §14 Q1: faults that interrupt or escape the CREATE without PROVING no key landed. The set is
    unbounded by construction (§14: "must never be enumerated"), so these are REPRESENTATIVES, one per family
    the ruling names. The rule under test is "not proven ⇒ conditional"; it is not a list of the forbidden."""
    return [
        asyncio.CancelledError(),  # cancellation (asyncio)
        KeyboardInterrupt(),  # an interrupt (BaseException, not Exception)
        TimeoutError("injected q1: the CREATE timed out"),  # a timeout (stdlib / SDK socket timeout)
        # a raw transport fault
        ConnectionResetError(errno.ECONNRESET, "injected q1: Connection reset by peer"),
        RuntimeError("injected q1: a future unknown"),  # the "future unknown" representative
        # the bare base: proves nothing (see fix531d._store_taxonomy)
        SurrealStoreError("injected q1: bare store base"),
    ]


#: Collected once so the parametrize ids are stable.
_UNKNOWN_OUTCOME_FAULTS: list[BaseException] = _unknown_outcome_faults()


#: am-37 §14 Q1 F-3 (OPERATOR, 2026-10-05: GENERALISE) + the lead's 2026-10-05 correction (REPORT-lead-63c.md
#: v13 addendum 2: CAUSE-NEUTRAL). Every word here names a cause that is FALSE for some member of the
#: conditional population:
#: - "connection" / "cancel" / "timeout" / "timed out" / "keyboard" name one family;
#: - "interrupt" / "answered" are false for a malformed-response bare base, which the store DID answer.
#: The operator's own example ("interrupted before the store answered") is therefore excluded by the
#: correction; the PROPERTY ("true for all of them") is what is pinned, never one string.
_FAMILY_CAUSE_WORDS: tuple[str, ...] = (
    "connection",
    "cancel",
    "timed out",
    "timeout",
    "keyboard",
    "interrupt",
    "answered",
)


def _assert_conditional_shape(note: str, *, email: str, name: str) -> None:
    """The CONDITIONAL wording for every NON-connection unknown-outcome fault (§13.5 item 5, §14 Q1, F-3).

    Unchanged parts: it says the outcome is UNKNOWN, never that the key is LIVE, and it names BOTH repair
    commands (``list-keys`` then ``revoke-key``) for THIS key, parsed by the real lore-adm parser.

    F-3 (operator, 2026-10-05) is pinned as a PROPERTY, not one string: the note names NO cause a fault in
    this population contradicts (``_FAMILY_CAUSE_WORDS``: cause-neutral), and it is not the connection
    class's text. That
    exact text stays pinned, for ``SurrealConnectionError`` only, in ``test_am37_13_3_63c_i_a.py``. A build
    that keeps "(the connection failed during the CREATE)" for every fault reds here."""
    assert note.startswith("the mint's outcome is unknown"), note
    assert "LIVE with no holder" not in note, "the CERTAIN wording claims the key landed; this is unknown"
    assert note != fix531d._conditional_note(email, name), "the connection text is FALSE for this fault (F-3)"  # noqa: SLF001
    named = [word for word in _FAMILY_CAUSE_WORDS if word in note.lower()]
    assert not named, f"F-3: the note names a cause ({named}) false for some unknown-outcome fault: {note!r}"
    commands = [shlex.split(text) for text in note.split("`")[1::2]]
    verbs = sorted(argv[1] for argv in commands if len(argv) > 1)
    assert verbs == ["list-keys", "revoke-key"], (verbs, note)
    fix531d.TestTheMintWindowNotesTheRevokeRepair._assert_commands_parse(note, email=email, name=name)  # noqa: SLF001


# --------------------------------------------------------------------------- #
# am-37 §14 Q1 (contract-mint-q1, operator-ruled 2026-10-04) — the note's domain is inverted: pre-answer,
# the note is WITHHELD iff the fault PROVES no key landed; EVERY other fault gets the CONDITIONAL note.
# --------------------------------------------------------------------------- #

#: Wall-clock bounds for the real-cancellation cells (seconds). The CREATE fake never answers, so any
#: positive budget cancels it; the cap only bounds a WRONG build that swallows cancellation and hangs.
_CANCEL_AFTER_SECONDS = 0.05
_HANG_CAP_SECONDS = 5.0


def _hanging_store(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[PrincipalKeyStore, asyncio.Event, dict[str, int]]:
    """A store whose mint CREATE is REACHED (signalled, #194) and then never answers: the shape of a CREATE
    in flight when a cancel or timeout arrives."""
    store = PrincipalKeyStore(
        url="ws://127.0.0.1:1", namespace="nsq1", database="dbq1", user="u", password=SecretStr("p")
    )
    reached_event = asyncio.Event()
    reached = {"count": 0}
    never = asyncio.Event()

    async def require_principal_id(_email: str) -> str:
        return "abcq1"

    async def query(statement: str, _params: dict[str, Any] | None = None) -> Any:
        assert statement.startswith("CREATE "), statement
        reached["count"] += 1
        reached_event.set()
        await never.wait()  # in flight: the engine may or may not have committed
        raise AssertionError("unreachable: the never-answering CREATE answered")  # pragma: no cover

    monkeypatch.setattr(store, "_require_principal_id", require_principal_id)
    monkeypatch.setattr(store, "_query", query)
    return store, reached_event, reached


class TestAnUnknownOutcomeDuringTheCREATECarriesTheConditionalNote:
    """am-37 §14 Q1: a fault that does NOT prove no key landed, arriving while the CREATE is in flight,
    carries the CONDITIONAL note. Cancellation, an interrupt, a timeout, a raw transport fault, a future
    unknown and the bare store base are all such faults. The object is re-raised UNCHANGED (same object,
    same class, cancellation still propagates), and the note is attached EXACTLY once.

    Wrong builds these cells kill: one keyed on ``SurrealConnectionError`` alone (fix531d as built: every
    cell here is note-less), one that swallows or converts cancellation (the real-cancel cells), and one that
    checks cancellation BEFORE ``answered`` (the post-answer cells in
    ``TestAPostAnswerInterruptStaysCertain``)."""

    @pytest.mark.parametrize("injected", _UNKNOWN_OUTCOME_FAULTS, ids=lambda error: type(error).__name__)
    @pytest.mark.parametrize(
        ("email", "name"), [fix531d._PLAIN, fix531d._NEEDS_QUOTING], ids=["plain", "needs-quoting"]
    )
    async def test_an_unproven_fault_raised_by_the_CREATE(
        self, monkeypatch: pytest.MonkeyPatch, injected: BaseException, email: str, name: str
    ) -> None:
        injected = copy.copy(injected)  # a fresh object per cell: notes must not leak across cells
        expected_type = type(fix531d._through_the_wrap(copy.copy(injected)))
        store, reached = fix531d.TestTheMintWindowNotesTheRevokeRepair._store(monkeypatch, raises=injected)  # noqa: SLF001
        with pytest.raises(BaseException) as caught:  # noqa: PT011 - the class IS the assertion below
            await store.mint(email=email, name=name, secret_hash="0" * 128)
        assert reached["count"] == 1, "the CREATE was never reached (#194)"
        served = caught.value
        assert type(served) is expected_type, (type(served), expected_type)
        if not isinstance(injected, SurrealStoreError):
            # The wrap passes non-store faults through, so the handler must re-raise THE SAME object.
            assert served is injected, "an unknown-outcome fault must re-raise as the SAME object"
        notes = getattr(served, "__notes__", None)
        assert notes is not None and len(notes) == 1, f"exactly ONE conditional note expected, got {notes!r}"
        _assert_conditional_shape(notes[0], email=email, name=name)
        rendered = "".join(traceback.format_exception(served))
        assert notes[0] in rendered, "the traceback renderer prints the note (PEP 678)"

    @pytest.mark.parametrize(
        ("email", "name"), [fix531d._PLAIN, fix531d._NEEDS_QUOTING], ids=["plain", "needs-quoting"]
    )
    async def test_every_non_connection_fault_gets_ONE_parenthetical(
        self, monkeypatch: pytest.MonkeyPatch, email: str, name: str
    ) -> None:
        """F-3 (operator): ONE parenthetical that is TRUE for every non-connection unknown-outcome fault, so
        the note text is IDENTICAL across them all (for a given key). A per-family build, e.g. "(the CREATE
        was cancelled)" for a cancel, reds here, because that text is false for a timeout."""
        notes: dict[str, str] = {}
        for injected in _unknown_outcome_faults():
            store, _reached = fix531d.TestTheMintWindowNotesTheRevokeRepair._store(  # noqa: SLF001
                monkeypatch, raises=injected
            )
            with pytest.raises(BaseException) as caught:  # noqa: PT011 - the note IS the assertion
                await store.mint(email=email, name=name, secret_hash="0" * 128)
            served_notes = getattr(caught.value, "__notes__", None) or []
            assert len(served_notes) == 1, (type(injected).__name__, served_notes)
            notes[type(injected).__name__] = served_notes[0]
        assert len(set(notes.values())) == 1, notes
        _assert_conditional_shape(next(iter(notes.values())), email=email, name=name)

    async def test_a_real_asyncio_timeout_cancels_the_CREATE_in_flight(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A real ``asyncio.timeout`` around the mint. Inside, the CREATE sees ``CancelledError``; outside,
        the caller sees ``TimeoutError`` chained from it. That chaining happens ONLY if the cancellation
        propagated out of ``mint`` unchanged, so a build that swallows or converts it reds here."""
        email, name = fix531d._PLAIN
        store, _reached_event, reached = _hanging_store(monkeypatch)
        async with asyncio.timeout(_HANG_CAP_SECONDS):  # the outer cap: only a WRONG build reaches it
            with pytest.raises(TimeoutError) as caught:
                async with asyncio.timeout(_CANCEL_AFTER_SECONDS):
                    await store.mint(email=email, name=name, secret_hash="0" * 128)
        assert reached["count"] == 1, "the CREATE was never reached (#194)"
        cancelled = caught.value.__cause__
        assert isinstance(cancelled, asyncio.CancelledError), repr(cancelled)
        notes = getattr(cancelled, "__notes__", None)
        assert notes is not None and len(notes) == 1, notes
        _assert_conditional_shape(notes[0], email=email, name=name)

    async def test_an_anyio_cancel_scope_cancels_the_CREATE_in_flight(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An anyio cancel (``move_on_after``, the shape ``anyio.fail_after`` / a task group uses). The scope
        must still CATCH its own cancellation, which proves it propagated, and the cancelled exception carries
        the conditional note."""
        email, name = fix531d._PLAIN
        store, _reached_event, reached = _hanging_store(monkeypatch)
        captured: list[BaseException] = []
        returned = False
        with anyio.fail_after(_HANG_CAP_SECONDS), anyio.move_on_after(_CANCEL_AFTER_SECONDS) as scope:
            try:
                await store.mint(email=email, name=name, secret_hash="0" * 128)
                returned = True
            except BaseException as error:
                captured.append(error)
                raise
        assert reached["count"] == 1, "the CREATE was never reached (#194)"
        assert not returned, "a cancelled mint must not return"
        assert scope.cancelled_caught, "the cancellation did not propagate to its own scope"
        (cancelled_error,) = captured
        assert isinstance(cancelled_error, anyio.get_cancelled_exc_class()), repr(cancelled_error)
        notes = getattr(cancelled_error, "__notes__", None)
        assert notes is not None and len(notes) == 1, notes
        _assert_conditional_shape(notes[0], email=email, name=name)

    async def test_a_cancelled_task_stays_cancelled(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """``Task.cancel()`` while the CREATE is in flight: the task ends CANCELLED, not failed and not
        succeeded, and the CancelledError that crossed ``mint`` carries the conditional note."""
        email, name = fix531d._NEEDS_QUOTING
        store, reached_event, reached = _hanging_store(monkeypatch)
        captured: list[BaseException] = []

        async def run() -> Any:
            try:
                return await store.mint(email=email, name=name, secret_hash="0" * 128)
            except BaseException as error:
                captured.append(error)
                raise

        async with asyncio.timeout(_HANG_CAP_SECONDS):
            task = asyncio.create_task(run())
            await reached_event.wait()
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        assert reached["count"] == 1
        assert task.cancelled(), f"the task must end CANCELLED; captured={captured!r}"
        (error,) = captured
        assert isinstance(error, asyncio.CancelledError), repr(error)
        notes = getattr(error, "__notes__", None)
        assert notes is not None and len(notes) == 1, notes
        _assert_conditional_shape(notes[0], email=email, name=name)


class TestAPostAnswerInterruptStaysCertain:
    """am-37 §13.5 item 1, unchanged by §14 Q1: after the engine ANSWERED, EVERY fault carries the CERTAIN
    note, interrupts and cancellations included. The key is LIVE whatever interrupts the read-back. This kills
    a build that tests for cancellation before it tests ``answered``."""

    @pytest.mark.parametrize(
        "injected",
        [asyncio.CancelledError(), KeyboardInterrupt(), TimeoutError("injected q1: post-answer")],
        ids=lambda error: type(error).__name__,
    )
    async def test_an_interrupt_after_the_answer(
        self, monkeypatch: pytest.MonkeyPatch, injected: BaseException
    ) -> None:
        email, name = fix531d._PLAIN
        injected = copy.copy(injected)
        store, reached = fix531d.TestTheMintWindowNotesTheRevokeRepair._store(  # noqa: SLF001
            monkeypatch, answer=[fix531d._full_row(name)]
        )

        def interrupted(_row: dict[str, Any]) -> Any:
            raise injected

        monkeypatch.setattr(store, "_row_to_key", interrupted)
        with pytest.raises(type(injected)) as caught:
            await store.mint(email=email, name=name, secret_hash="0" * 128)
        assert reached["count"] == 1
        assert caught.value is injected
        assert caught.value.__notes__ == [fix531d._certain_note(email, name)]


def _loremaster_bindings_of(value: object) -> list[tuple[object, str]]:
    """Every (namespace, attribute) in a loaded ``loremaster`` module, or a class it defines, that binds
    exactly ``value``, by IDENTITY. It finds the ONE tuple wherever the build imported it, under any name, so
    the sharing mutation below needs no knowledge of how production spells the import."""
    bindings: list[tuple[object, str]] = []
    for module_name, module in list(sys.modules.items()):
        if module is None or not (module_name == "loremaster" or module_name.startswith("loremaster.")):
            continue
        for attribute, bound in list(vars(module).items()):
            if bound is value:
                bindings.append((module, attribute))
            if isinstance(bound, type) and bound.__module__ == module_name:
                bindings.extend((bound, inner) for inner, member in vars(bound).items() if member is value)
    return bindings


class TestTheProvenNoKeySetIsOneExportedTuple:
    """am-37 §14 Q1: the proven-no-key set is ONE tuple, ``_txn._PROVEN_NO_KEY_FAULTS``, exported by the
    store layer that owns the taxonomy, so a new ``_txn`` subclass is adjudicated at birth. STUB EXPECTATION:
    the name does not exist before the build, so every cell here is RED by AttributeError until then."""

    @staticmethod
    def _proven() -> tuple[type[BaseException], ...]:
        proven = getattr(_txn_module, "_PROVEN_NO_KEY_FAULTS")  # noqa: B009 - a stub expectation: red by name
        assert isinstance(proven, tuple), type(proven)
        return proven

    def test_the_tuple_is_exported_by_the_store_layer(self) -> None:
        proven = self._proven()
        assert proven, "an EMPTY proven set would note every UNIQUE rejection"
        for cls in proven:
            assert isinstance(cls, type) and issubclass(cls, SurrealStoreError), cls
            assert cls is not SurrealStoreError, "the bare base would make SurrealConnectionError 'proven'"
            assert cls.__module__ == _txn_module.__name__, (cls, cls.__module__)
        assert len(set(proven)) == len(proven), "a duplicated member hides a missing one"

    def test_the_tuple_never_covers_the_connection_class(self) -> None:
        """Membership is tested by ``isinstance``, so it must be disjoint in BOTH directions: no member
        subclasses the connection class, and the connection class subclasses no member."""
        proven = self._proven()
        assert not isinstance(SurrealConnectionError("probe"), proven)
        assert not any(issubclass(cls, SurrealConnectionError) for cls in proven)

    def test_the_tuple_plus_the_connection_class_is_the_derived_taxonomy(self) -> None:
        """Completeness, PRODUCTION side: (the proven tuple) ∪ {SurrealConnectionError} == the GENERATED
        ``_txn`` taxonomy. A new, unadjudicated subclass reds BY NAME."""
        derived = {cls.__name__ for cls in fix531d._store_taxonomy()}
        produced = {cls.__name__ for cls in self._proven()} | {SurrealConnectionError.__name__}
        assert produced == derived, (
            f"unadjudicated: {sorted(derived - produced)} · not in the taxonomy: {sorted(produced - derived)}"
        )

    def test_the_tuple_is_the_rulings_adjudication(self) -> None:
        """Independent expected value: the tuple equals the set the OPERATOR ruled (§14 Q1), written out in
        this file. If it were computed from the live subclass tree, a new ``_txn`` class would be adjudicated
        'proven' silently, which is the false-clear direction. This cell turns that into a red by name."""
        assert {cls.__name__ for cls in self._proven()} == fix531d._RULED_PROVEN_NO_KEY

    @pytest.mark.parametrize("removed", sorted(fix531d._RULED_PROVEN_NO_KEY))
    async def test_the_mint_reads_the_one_tuple(self, monkeypatch: pytest.MonkeyPatch, removed: str) -> None:
        """ONE IMPLEMENTATION, proven by MUTATION. Every binding of the tuple is rebound WITHOUT ``removed``,
        and a ``removed`` fault during the CREATE must then carry the conditional note. A private copy of the
        set, or a hard-coded ``isinstance`` ladder, keeps the old verdict and reds here."""
        proven = self._proven()
        bindings = _loremaster_bindings_of(proven)
        assert (_txn_module, "_PROVEN_NO_KEY_FAULTS") in bindings, bindings
        cls = next(cls for cls in fix531d._store_taxonomy() if cls.__name__ == removed)
        # Membership is ``isinstance``: drop ``removed`` AND every member that COVERS it (its ancestors in the
        # tuple). Otherwise a subclass (UNIQUE, under TxnDomainRejectionError) stays covered.
        mutated = tuple(member for member in proven if not issubclass(cls, member))
        assert len(mutated) < len(proven), (removed, proven)
        for namespace, attribute in bindings:
            monkeypatch.setattr(namespace, attribute, mutated)
        email, name = fix531d._PLAIN
        store, _reached = fix531d.TestTheMintWindowNotesTheRevokeRepair._store(  # noqa: SLF001
            monkeypatch, raises=fix531d._instance(cls)
        )
        with pytest.raises(BaseException) as caught:  # noqa: PT011 - the note IS the assertion below
            await store.mint(email=email, name=name, secret_hash="0" * 128)
        notes = getattr(caught.value, "__notes__", None)
        assert notes is not None and len(notes) == 1, f"{removed} left the tuple but the mint still withholds"
        _assert_conditional_shape(notes[0], email=email, name=name)

    async def test_CONTROL_the_unmutated_tuple_withholds(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The positive control for the mutation cells: the same injection, tuple untouched → no note."""
        self._proven()
        email, name = fix531d._PLAIN
        store, _reached = fix531d.TestTheMintWindowNotesTheRevokeRepair._store(  # noqa: SLF001
            monkeypatch, raises=TxnDomainRejectionError("injected q1 control")
        )
        with pytest.raises(PrincipalKeyStoreError) as caught:
            await store.mint(email=email, name=name, secret_hash="0" * 128)
        fix531d._note_free_chain(caught.value)


# --------------------------------------------------------------------------- #
# am-37 §14 Q1 N-3 (operator "fix N-3 in Q1", 2026-10-05; mechanism (d) per REPORT-lead-63c.md v13 addendum
# 2): whenever the CONDITIONAL note applies, NO rendered message claims the key was not minted. Proven faults
# keep their not-landed message, which is TRUE for them. ONE tuple decides both the note and the message.
# (d) nests two wraps on the ONE seam, so the CLASS stays ``PrincipalKeyStoreError`` (finding #400 holds)
# and only the MESSAGE and the NOTE move.
# --------------------------------------------------------------------------- #


def _foreign_store_classes() -> list[type[BaseException]]:
    """GENERATED: every ``SurrealStoreError`` subclass defined OUTSIDE ``_txn``, after importing EVERY
    non-test ``loremaster`` module, so the walk does not depend on what this worker happened to import."""
    for module in pkgutil.walk_packages(loremaster.__path__, "loremaster."):
        if ".tests" not in module.name:
            importlib.import_module(module.name)
    found: set[type[BaseException]] = set()
    pending = list(SurrealStoreError.__subclasses__())
    while pending:
        cls = pending.pop()
        pending.extend(cls.__subclasses__())
        if cls.__module__ != _txn_module.__name__:
            found.add(cls)
    return sorted(found, key=lambda cls: f"{cls.__module__}.{cls.__qualname__}")


def _construct(cls: type[BaseException]) -> BaseException:
    """An instance without knowing the class's constructor (foreign classes take bespoke kwargs)."""
    instance = cls.__new__(cls)
    BaseException.__init__(instance, f"injected n3: {cls.__name__}")
    return instance


_FOREIGN: list[type[BaseException]] = _foreign_store_classes()
_N3_EMAIL, _N3_NAME = fix531d._PLAIN  # noqa: SLF001


def _unproven_population() -> list[BaseException]:
    """The r1 unknown-outcome faults plus every FOREIGN store class, each a fresh object."""
    return [*_unknown_outcome_faults(), *(_construct(cls) for cls in _FOREIGN)]


async def _served(monkeypatch: pytest.MonkeyPatch, injected: BaseException) -> BaseException:
    window = fix531d.TestTheMintWindowNotesTheRevokeRepair
    store, reached = window._store(monkeypatch, raises=injected)  # noqa: SLF001
    with pytest.raises(BaseException) as caught:  # noqa: PT011 - the fate IS the assertion
        await store.mint(email=_N3_EMAIL, name=_N3_NAME, secret_hash="0" * 128)
    assert reached["count"] == 1, "the CREATE was never reached (#194)"
    return caught.value


async def _not_landed_message(monkeypatch: pytest.MonkeyPatch) -> str:
    """DERIVED, never hard-coded: what mint serves for a PROVEN rejection (the true not-landed claim)."""
    served = await _served(monkeypatch, TxnDomainRejectionError("injected n3 proven"))
    assert isinstance(served, PrincipalKeyStoreError), type(served)
    return str(served)


def _rendered(error: BaseException) -> str:
    return str(error) + "\n" + "".join(traceback.format_exception(error))


def _assert_cause_neutral_message(message: str) -> None:
    """The lead's correction (v13 addendum 2): the message for an unproven store fault names no cause, by the
    same vocabulary as the F-3 note property."""
    named = [word for word in _FAMILY_CAUSE_WORDS if word in message.lower()]
    assert not named, f"the outcome-unknown message names a cause ({named}): {message!r}"


class TestAnUnprovenFaultNeverClaimsNonLanding:
    """N-3 property, ∀ the GENERATED unproven population: r1 unknown faults + every foreign store class."""

    def test_the_foreign_population_is_not_vacuous(self) -> None:
        names = {cls.__name__ for cls in _FOREIGN}
        assert {"LeaseError", "FenceLostError"} <= names, names

    @pytest.mark.parametrize("injected", _unproven_population(), ids=lambda error: type(error).__name__)
    async def test_the_message_does_not_claim_the_key_was_not_minted(
        self, monkeypatch: pytest.MonkeyPatch, injected: BaseException
    ) -> None:
        not_landed = await _not_landed_message(monkeypatch)
        served = await _served(monkeypatch, injected)
        notes = getattr(served, "__notes__", None) or []
        assert len(notes) == 1, (type(injected).__name__, notes)
        _assert_conditional_shape(notes[0], email=_N3_EMAIL, name=_N3_NAME)
        assert not_landed not in _rendered(served), _rendered(served)
        assert "could not mint" not in _rendered(served).lower(), _rendered(served)
        if isinstance(injected, SurrealStoreError):
            # (d): the class stays the domain error (#400: no raw engine error reaches the caller), and its
            # message is the cause-neutral outcome-unknown one.
            assert type(served) is PrincipalKeyStoreError, type(served)
            assert served.__cause__ is injected
            _assert_cause_neutral_message(str(served))
        else:
            assert served is injected, "a non-store fault re-raises as the SAME object"

    @pytest.mark.parametrize("cls", fix531d._PRE_COMMIT_CLASSES, ids=lambda cls: cls.__name__)  # noqa: SLF001
    async def test_a_proven_fault_keeps_the_not_landed_message(
        self, monkeypatch: pytest.MonkeyPatch, cls: type[BaseException]
    ) -> None:
        passes_through = cls.__name__ == "TxnContentionExhaustedError"
        if cls.__name__ not in fix531d._RULED_PROVEN_NO_KEY or passes_through:  # noqa: SLF001
            pytest.skip("not translated by the wrap today (connection / exhausted contention pass through)")
        served = await _served(monkeypatch, fix531d._instance(cls))  # noqa: SLF001
        assert str(served) == f"could not mint key {_N3_NAME!r} for principal {_N3_EMAIL!r}"
        fix531d._note_free_chain(served)  # noqa: SLF001


class TestOneTupleDecidesNoteAndMessage:
    """ONE IMPLEMENTATION, by MUTATION: moving a class across ``_PROVEN_NO_KEY_FAULTS`` (every identity-found
    binding) flips BOTH its note and its message. Under (d) the class stays ``PrincipalKeyStoreError`` either
    way, so WHICH wrap translated it shows as the message."""

    async def test_moving_a_proven_class_OUT_flips_both(self, monkeypatch: pytest.MonkeyPatch) -> None:
        proven = TestTheProvenNoKeySetIsOneExportedTuple._proven()  # noqa: SLF001
        not_landed = await _not_landed_message(monkeypatch)
        mutated = tuple(member for member in proven if not issubclass(TxnDomainRejectionError, member))
        for namespace, attribute in _loremaster_bindings_of(proven):
            monkeypatch.setattr(namespace, attribute, mutated)
        injected = TxnDomainRejectionError("injected n3 moved out")
        served = await _served(monkeypatch, injected)
        assert len(getattr(served, "__notes__", None) or []) == 1, "the NOTE did not flip"
        assert not_landed not in _rendered(served), "the MESSAGE did not flip"
        assert type(served) is PrincipalKeyStoreError and served.__cause__ is injected
        _assert_cause_neutral_message(str(served))  # the OUTER wrap translated it: cause-neutral

    async def test_moving_a_foreign_class_IN_flips_both(self, monkeypatch: pytest.MonkeyPatch) -> None:
        foreign = next(cls for cls in _FOREIGN if cls.__name__ == "LeaseError")
        proven = TestTheProvenNoKeySetIsOneExportedTuple._proven()  # noqa: SLF001
        not_landed = await _not_landed_message(monkeypatch)
        for namespace, attribute in _loremaster_bindings_of(proven):
            monkeypatch.setattr(namespace, attribute, (*proven, foreign))
        served = await _served(monkeypatch, _construct(foreign))
        assert not getattr(served, "__notes__", None), "the NOTE did not flip"
        assert str(served) == not_landed, "the MESSAGE did not flip"


class TestTheOtherWrapCallersAreUnchanged:
    """(d) widens the ONE seam with an optional ``catch=``. Its DEFAULT must stay the old catch set, so the 20
    non-mint callers (audit / keeps / principals / revoke) keep translating every non-passthrough store fault.
    The generated cross-store counterpart is ``test_engine_rejection_seam.py``'s #400 pins. Making the default
    the proven tuple reddens the cells below."""

    @pytest.mark.parametrize(
        "injected",
        [SurrealStoreError("bare"), *(_construct(cls) for cls in _FOREIGN)],
        ids=lambda error: type(error).__name__,
    )
    def test_the_default_wrap_translates(self, injected: BaseException) -> None:
        with (
            pytest.raises(PrincipalKeyStoreError) as caught,
            wrap_store_rejection(PrincipalKeyStoreError, "control"),
        ):
            raise injected
        assert str(caught.value) == "control"
        assert caught.value.__cause__ is injected

    @pytest.mark.parametrize(
        "injected",
        [SurrealStoreError("bare"), *(_construct(cls) for cls in _FOREIGN)],
        ids=lambda error: type(error).__name__,
    )
    async def test_revoke_still_translates(
        self, monkeypatch: pytest.MonkeyPatch, injected: BaseException
    ) -> None:
        """A real non-mint caller: ``revoke`` keeps its not-revoked translation and carries no mint note."""
        window = fix531d.TestTheMintWindowNotesTheRevokeRepair
        store, _reached = window._store(monkeypatch, raises=injected)  # noqa: SLF001

        async def query(statement: str, _params: dict[str, Any] | None = None) -> Any:
            assert statement.startswith("UPDATE "), statement
            raise injected

        monkeypatch.setattr(store, "_query", query)
        with pytest.raises(PrincipalKeyStoreError) as caught:
            await store.revoke(email=_N3_EMAIL, name=_N3_NAME)
        assert str(caught.value) == f"could not revoke key {_N3_NAME!r} for principal {_N3_EMAIL!r}"
        assert caught.value.__cause__ is injected
        assert not getattr(caught.value, "__notes__", None)

