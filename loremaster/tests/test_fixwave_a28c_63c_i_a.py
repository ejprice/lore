"""Contract — packet 63c wave i-a, the a28c FOLD (amendments 35 + 34, the a28b adversary's MP-1…MP-5, packet
58's FK-r3-4 drivers). Authored by ``contract-63c-i-a-a28c`` (Opus 5.5 contract author — CONTRACT TESTS ONLY,
no production code), 2026-09-27. *Every claim in this file is scoped to the tree at ``90d908f`` (production
byte-identical to the checkpoint ``169925f``) unless a docstring dates it otherwise.* The build under repair
is ``169925f``; the contract folded is a28b (``e039c64``) as graded INSUFFICIENT by
``REPORT-adversary-63c-i-a-a28b.md`` (``52c7522`` + ``4160f88``).

⚠ THE STOP-RULE (amendment 35 §0, binding): this is the LAST contract round for two properties — C2's gate
(strike 3: F-2 → W19 → B13) and the RS-5 classifier (strike 3: FK-ADV-1 → R-txn / B1 / MP-3). A FOURTH strike
on either is answered by a pinned bound with a named re-open trigger, never another contract round. Each class
pin below repeats its strike count in its docstring so the next grader reads it where it lands.

THE SPEC IS THE RULINGS (later wins):
* ``docs/design/2026-09-27-packet63c-amendment-35.md`` (``d463dba``) §W — §1 C2 re-ruled as the VISIBILITY
SEAM
  (a relation-set product × mint orders, both verdicts; a seam mutation pin; KE); §2 the classifier's
  MECHANISM (R typed on BOTH paths via ``surrealdb.errors.parse_query_error``; the record text pair DELETED; U
  a prefix-anchored engine-text test checked first; every other marker anchored or checked last; KA + the
  ``_domain_rejection_error`` mutation; pin-the-miss); §3 the scanner (in ``test_retry_seam.py``); §4 R-4.
* ``docs/design/2026-09-26-packet63c-amendment-34.md`` (``178d236``) — ``"empty"``, the invariant validator,
the
  unresolved-operator counts as fields (the a28 file carries the expectation changes), F-5 (an undefined
  target table is a typed answer).
* ``REPORT-adversary-63c-i-a-a28b.md`` §A.5 — the kill probes KA, KB, KC, KE land AST-equal (KD lands in
  ``test_retry_seam.py``, adapted — ``REPORT-contract-63c-i-a-a28c.md`` §DEVIATIONS).
* packet 58 amendment 8 §3 / FK-r3-4 — this module's ``CAS_SEAM_DRIVERS`` drives the three 63c-owned listed
  handlers for 58's population pin (``test_reanchor_58_r3_cas_seam.py``).

STORE LAW (``docs/reference/surrealdb-31-capabilities.md`` — cited, never re-transcribed): §3 (a
multi-statement ``query()`` validates statement[0] only — every setup here is one statement per call), §5 (a
concurrency pin holds at ≥8-way and is cleared only by 20 consecutive greens). Live TEST store
``ws://127.0.0.1:18000`` (NEVER :18500), one unique database per world, reaped. No skip marker."""

from __future__ import annotations

import ast
import dataclasses
import inspect
import itertools
import pathlib
import re
import time
from typing import TYPE_CHECKING, Any, cast

import loremaster.agents as agents_module
import loremaster.keeps as keeps_module
import loremaster.visible_keeps as visible_keeps_module
import pytest
import surrealdb.errors as sdk_errors
import test_fixwave_a19a_63c_i_a as a19a  # module-qualified: its Test* classes must not be re-collected
import test_fixwave_a28_63c_i_a as a28
import test_fixwave_a28b_63c_i_a as a28b
from _engine_shapes import CASCADE_OPENINGS, CONFLICT_WORDS
from _governed_contract import (
    AGENT_TABLE,
    MESSAGE_TABLE,
    build_principal_and_keep_stores,
    credentialed_app_context,
    patch_shared_object_everywhere,
)
from _reanchor_58_support import DRIVER_SEAM_NAMES, ledger58  # noqa: F401 - the fixture is re-exported
from _surreal_harness import SurrealConnection, SurrealEnv, admin_db, run  # noqa: F401
from loremaster.floor_calibration.store import FenceLostError, LeaseFence
from loremaster.governed import GovernedDenied, MigrateGovernedResult
from loremaster.store import _txn
from loremaster.store._txn import (
    TxnDomainRejectionError,
    TxnGovernedConflictError,
    execute_transaction,
)
from lorerunes.pdp import keep_scope
from sdk3_shape_fakes import bare_record_key, same_record

from loremaster import principals

if TYPE_CHECKING:
    # The STATIC references owning this file's pending pins (scripts/pending_contracts.yaml, #461's shape):
    # amendments 32/33/35's ruled class and amendment 34's ruled result field. Runtime-inert. And 58's
    # instrument, for annotations only: a MODULE-level import would be circular — its collection-time scan
    # (``discovered_drivers``) imports THIS module to read ``CAS_SEAM_DRIVERS``.
    from loremaster.store._txn import TxnUniqueViolationError
    from test_reanchor_58_r3_cas_seam import DriverSeamInjection

    def _ruled_a28c(result: MigrateGovernedResult) -> tuple[object, ...]:
        return (TxnUniqueViolationError, result.table_defined)


def _class_name(raised: BaseException) -> str:
    return type(raised).__name__


# ======================================================================================================== #
# amendment 35 §2 — THE CLASSIFIER'S MECHANISM (the RS-5 classifier property, STRIKE 3 of 3 — FK-ADV-1 → R-txn
# / B1 / MP-3; a fourth strike is a pinned bound, never a round). The ONE classifier's verdict is a function
# of the engine's rejection KIND: read from the SDK's TYPED signal wherever the engine types it (the record-id
# collision, on BOTH raise sites), from a prefix-anchored engine-authored text ONLY for the one untyped
# identity shape (the UNIQUE-index collision); never of a caller value the text echoes; the class built in ONE
# place.
# ======================================================================================================== #


# ------------------------------------------------------------------------------------------------------------
# KA — ONE classifier, proven by MUTATION (am-33 §(a): "the text is read ONCE, in
# `_txn._classify_engine_error`"). The U shape is text-classified on BOTH paths (no typed leg exists), so if
# the ONE classifier stops recognising it, BOTH raise sites must lose the class. A build that reads the marker
# text anywhere else (a helper both raise sites call first — B1) keeps the class under the mutation and reds
# here. Reverse leg: the classifier's LABEL is what builds the class at both sites (an ASSERT the patched
# classifier labels unique raises the class).
# ------------------------------------------------------------------------------------------------------------
class TestKATheOneClassifierDecidesTheTextShape:
    @pytest.mark.parametrize("path", ["run_query", "execute_transaction"])
    async def test_KA_mutating_the_one_classifier_moves_both_raise_sites(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
        monkeypatch: pytest.MonkeyPatch,
        path: str,  # noqa: F811
    ) -> None:
        connection, env = admin_db
        for situation in ("unique-index-collision", "assert-violation"):
            for statement in a28b._SITUATIONS[situation][0]:
                await run(connection, statement)
        u_statement = a28b._SITUATIONS["unique-index-collision"][1]
        a_statement = a28b._SITUATIONS["assert-violation"][1]
        control = await a28b._raise_through(path, u_statement, connection, env)
        assert _class_name(control) == a28b._CONFLICT_CLASS_NAME, f"CONTROL: {control!r}"
        real = _txn._classify_engine_error
        monkeypatch.setattr(_txn, "_classify_engine_error", lambda raw: _txn._ERROR_CLASS_UNSPECIFIED)
        muted = await a28b._raise_through(path, u_statement, connection, env)
        assert type(muted) is TxnDomainRejectionError, (
            f"{path}: the ONE classifier no longer recognises the index text, yet the raise site still typed "
            f"it {type(muted).__name__} — the text is read OUTSIDE _classify_engine_error (am-33 §(a))"
        )
        unique_label = real("Database index `k` already contains 'v', with record `k:1`")
        monkeypatch.setattr(_txn, "_classify_engine_error", lambda raw: unique_label)
        relabelled = await a28b._raise_through(path, a_statement, connection, env)
        assert _class_name(relabelled) == a28b._CONFLICT_CLASS_NAME, (
            f"{path}: the classifier labelled an ASSERT unique, yet the raise site built "
            f"{type(relabelled).__name__} — the class is not built from the ONE classifier's label"
        )


# ------------------------------------------------------------------------------------------------------------
# KB — the class is a function of the engine's rejection KIND, never of a caller VALUE the engine text ECHOES
# (ledger #31: the raw text "can carry an interpolated bound VALUE"). Hostile values carry the OTHER class's
# marker words. ⚠ The RULED mechanism (substring membership in a fixed order, am-33) CANNOT pass all four
# legs: order unique-before-ASSERT fails `assert-echoes-index-words`; ASSERT-before-unique fails
# `unique-echoes-assert-words`; governed-first fails `unique-echoes-governed-marker`. An ANCHORED match (the
# engine message PREFIX `Database index` / `Database record`, which precedes every echoed value) passes all
# four (§SAT-3). A RULING question, surfaced as MP-3.
# ------------------------------------------------------------------------------------------------------------
_HOSTILE_SETUP = (
    "DEFINE TABLE hx SCHEMAFULL",
    "DEFINE FIELD s ON hx TYPE string ASSERT string::len($value) < 8",
    "DEFINE FIELD k ON hx TYPE option<string>",
    "DEFINE FIELD n ON hx TYPE option<int>",
    "DEFINE INDEX hx_k ON hx FIELDS k UNIQUE",
    "CREATE hx:seed1 SET s = 'ok', k = 'x must conform to y'",
    "CREATE hx:seed2 SET s = 'ok', k = 'session:governed_conflict:x'",
)
_HOSTILE: dict[str, tuple[str, bool]] = {
    "assert-echoes-index-words": ("CREATE hx SET s = 'Database index `z` already contains 1'", False),
    "coerce-echoes-record-words": (
        "CREATE hx SET s = 'ok', n = 'Database record `hx:q` already exists'",
        False,
    ),
    "unique-echoes-assert-words": ("CREATE hx SET s = 'ok', k = 'x must conform to y'", True),
    "unique-echoes-governed-marker": ("CREATE hx SET s = 'ok', k = 'session:governed_conflict:x'", True),
}


class TestKBTheClassIgnoresEchoedValues:
    @pytest.mark.parametrize("path", ["run_query", "execute_transaction"])
    @pytest.mark.parametrize("case", sorted(_HOSTILE))
    async def test_KB_a_hostile_echoed_value_never_moves_the_class(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
        case: str,
        path: str,  # noqa: F811
    ) -> None:
        connection, env = admin_db
        for statement in _HOSTILE_SETUP:
            await run(connection, statement)
        statement, identity_taken = _HOSTILE[case]
        raised = await a28b._raise_through(path, statement, connection, env)
        if identity_taken:
            assert _class_name(raised) == a28b._CONFLICT_CLASS_NAME, f"{case}/{path}: {raised!r}"
        else:
            assert type(raised) is TxnDomainRejectionError, f"{case}/{path}: {raised!r}"


# ------------------------------------------------------------------------------------------------------------
# KB WIDENED OVER THE WHOLE READER SET — the CLASS pin (amendment 35 §2 item 3 + amendment 36 §1.2 pin 1): ∀
# phrases × ∀ live host shapes × both raise sites, the phrase injected as the ECHOED VALUE moves NOTHING — not
# the served class, not the retry count, not the elapsed time, not the selected root cause. GENERATED on both
# axes:
# * HOSTS — every live rejection shape that echoes a caller value (the identity shapes, the ASSERT / coercion
#   shapes, the governed THROW whose suffix carries a row id — ``governed.py``'s ``THROW
#   "governed_conflict:<t>:<id>"``);
# * PHRASES — (a) every host's OWN engine text, captured LIVE in the test (the engine is the source of truth
# for what each class's text looks like — a builder's marker spelling is irrelevant); (b) the engine's retry
# and cascade texts (``_engine_shapes`` — what the two UPSTREAM readers used to key on, amendment 36 §1); (c)
# every text marker the driver module carries (``vars(_txn)``: every ``*_MARKER`` string and every element of
# a ``*_MARKERS`` / ``*_MARKER_PAIRS`` tuple, derived at collection — a marker the builder adds joins
# unedited). The expected class is the HOST's, derived from the host table, never from the phrase.
# ------------------------------------------------------------------------------------------------------------
# #

#: The KB-widened hosts' schema — one statement per call (store-ref §3). ``s`` rejects every value but
#: ``'ok'`` (an ASSERT that echoes ANY phrase), ``n`` is an int column (a string value is a coercion failure
#: that echoes it), ``k`` carries a UNIQUE index (a taken value is echoed by the index text).
_ECHO_SETUP = (
    "DEFINE TABLE hx SCHEMAFULL",
    "DEFINE FIELD s ON hx TYPE string ASSERT $value = 'ok'",
    "DEFINE FIELD k ON hx TYPE option<string>",
    "DEFINE FIELD n ON hx TYPE option<int>",
    "DEFINE INDEX hx_k ON hx FIELDS k UNIQUE",
)
#: host → (seed statement or ``None``, the colliding / rejected statement, the class the HOST must raise).
#: Every statement takes the echoed value as ``$v`` (a bound parameter — the value reaches the engine unquoted
#: by us).
_ECHO_HOSTS: dict[str, tuple[str | None, str, str]] = {
    "unique-index-collision": (
        "CREATE hx SET s = 'ok', k = $v",
        "CREATE hx SET s = 'ok', k = $v",
        a28b._CONFLICT_CLASS_NAME,
    ),
    "record-id-collision": (
        "CREATE type::record('hx', $v) SET s = 'ok'",
        "CREATE type::record('hx', $v) SET s = 'ok'",
        a28b._CONFLICT_CLASS_NAME,
    ),
    "assert-violation": (None, "CREATE hx SET s = $v", TxnDomainRejectionError.__name__),
    "coercion-failure": (None, "CREATE hx SET s = 'ok', n = $v", TxnDomainRejectionError.__name__),
    "governed-throw": (None, "THROW 'governed_conflict:hx:' + $v", TxnGovernedConflictError.__name__),
}
#: The value each host is driven with to CAPTURE its own engine text (a phrase source).
_PLAIN_VALUE = "plain-echo-value"
#: amendment 36 §1.2 pin 1 — the engine texts the two UPSTREAM readers (the retry decision, the root-cause
#: selector) used to key on, as the engine authors them (``_engine_shapes``, measured 3.2.4). They are phrases
#: in their own right: once the build deletes the text markers, ``vars(_txn)`` no longer names them, so the
#: domain carries the ENGINE's words directly — the class, the attempt count and the root cause must not move
#: for them.
_ENGINE_DECISION_TEXTS: dict[str, str] = {
    "engine-conflict-commit": (
        f"Cannot COMMIT: Transaction conflict: Resource busy. This transaction {CONFLICT_WORDS}"
    ),
    **{f"engine-cascade-{index}": opening for index, opening in enumerate(CASCADE_OPENINGS)},
}
#: The served root-cause position on ``execute_transaction`` ("statement N of M was rejected").
_ROOT_CAUSE_POSITION = re.compile(r"statement (\d+) of (\d+) was rejected")


def _driver_marker_phrases() -> dict[str, str]:
    """Every text marker ``loremaster.store._txn`` carries, DERIVED at collection (``vars(_txn)``): a
    ``*_MARKER`` string is one phrase; a ``*_MARKERS`` / ``*_MARKER_PAIRS`` tuple contributes each element (a
    pair's words joined around a backtick token, the way an engine text carries them)."""
    phrases: dict[str, str] = {}
    for name, value in sorted(vars(_txn).items()):
        if name.endswith("_MARKER") and isinstance(value, str):
            phrases[f"marker{name}"] = value
        elif name.endswith(("_MARKERS", "_MARKER_PAIRS")) and isinstance(value, tuple):
            for index, element in enumerate(value):
                if isinstance(element, str):
                    phrases[f"marker{name}{index}"] = element
                elif isinstance(element, tuple) and all(isinstance(word, str) for word in element):
                    phrases[f"marker{name}{index}"] = " `z` ".join(element)
    return phrases


#: phrase label → the literal phrase, or ``None`` for a host phrase (captured live from that host).
_ECHO_PHRASES: dict[str, str | None] = {
    **{f"host-{host}": None for host in _ECHO_HOSTS},
    **_ENGINE_DECISION_TEXTS,
    **_driver_marker_phrases(),
}


async def _engine_text(connection: SurrealConnection, host: str, value: str) -> str:
    """The engine's OWN rejection text for ``host`` driven with ``value`` — through the SDK directly (no
    driver), so the phrase is exactly what the engine authors."""
    seed, statement, _expected = _ECHO_HOSTS[host]
    if seed is not None:
        await run(connection, seed, {"v": value})
    try:
        await run(connection, statement, {"v": value})
    except Exception as error:  # noqa: BLE001 - the text is the measurement
        return str(error)
    pytest.fail(f"{host}: {statement!r} raised nothing — the host is not constructed")


def _count_attempts(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """Count every ATTEMPT the ONE retry driver makes (``_txn.retry_on_conflict``, rebound at the module
    global both raise sites call) — a domain rejection is exactly ONE attempt."""
    real = _txn.retry_on_conflict
    attempts = {"n": 0}

    async def counting(attempt: Any, *args: Any, **kwargs: Any) -> Any:
        async def counted() -> Any:
            attempts["n"] += 1
            return await attempt()

        return await real(counted, *args, **kwargs)

    monkeypatch.setattr(_txn, "retry_on_conflict", counting)
    return attempts


class TestTheClassIgnoresEveryEchoedPhrase63cIAa28c:
    def test_am36_1_2_the_phrase_domain_is_derived_and_non_vacuous(self) -> None:
        """GREEN at ``169925f`` — the widened KB is non-vacuous: every host's own text, the engine's retry and
        cascade texts (the two UPSTREAM readers, amendment 36 §1), and every driver marker (≥4 at the
        checkpoint: governed, ASSERT, coercion, recursion-depth — plus the retry / cascade markers until the
        build deletes them)."""
        assert len(_driver_marker_phrases()) >= 4, _driver_marker_phrases()
        assert all(f"host-{host}" in _ECHO_PHRASES for host in _ECHO_HOSTS), _ECHO_PHRASES
        assert set(_ENGINE_DECISION_TEXTS) <= set(_ECHO_PHRASES), _ECHO_PHRASES
        assert any(CONFLICT_WORDS in text for text in _ENGINE_DECISION_TEXTS.values())

    def test_am35_2_3_every_classifier_label_is_hosted_or_exempt_with_a_reason(self) -> None:
        """⚠ RED at ``169925f`` (the unique-violation label is unbuilt). COMPLETENESS of the host domain
        against the classifier's OWN label set (``vars(_txn)``: every ``_ERROR_CLASS_*`` string): each label
        is produced by a live host above, or exempt with a stated reason. A NEW label reds here by name until
        it is hosted (a new rejection kind whose echo nobody has driven) or exempted with evidence."""
        labels = {
            name
            for name, value in vars(_txn).items()
            if name.startswith("_ERROR_CLASS_") and isinstance(value, str)
        }
        hosted = {
            "_ERROR_CLASS_UNIQUE_VIOLATION",  # the unique-index + record-id hosts
            "_ERROR_CLASS_ASSERT_VIOLATION",
            "_ERROR_CLASS_FIELD_COERCION",
            "_ERROR_CLASS_GOVERNED_CONFLICT",
        }
        exempt = {
            "_ERROR_CLASS_RETRYABLE_CONFLICT": "decided by the TYPED conflict kind (amendment 36) — no text",
            "_ERROR_CLASS_QUERY_TOO_COMPLEX": "a PARSE-time Validation rejection (#66) — no value echoed",
            "_ERROR_CLASS_UNSPECIFIED": "the fall-through — no marker, nothing an echo can spoof INTO",
        }
        assert labels == hosted | set(exempt), (
            f"the classifier's labels {sorted(labels)} are not exactly the hosted {sorted(hosted)} ∪ exempt "
            f"{sorted(exempt)} — missing {sorted(hosted | set(exempt) - labels)}, unhosted "
            f"{sorted(labels - hosted - set(exempt))} (amendment 35 §2 item 3: ∀ marker phrases × ∀ live "
            "host "
            "shapes — a new label needs a host or a reasoned exemption)"
        )

    @pytest.mark.parametrize("path", ["run_query", "execute_transaction"])
    @pytest.mark.parametrize("phrase", sorted(_ECHO_PHRASES))
    @pytest.mark.parametrize("host", sorted(_ECHO_HOSTS))
    async def test_am36_1_2_an_echoed_phrase_moves_nothing(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
        monkeypatch: pytest.MonkeyPatch,
        host: str,
        phrase: str,
        path: str,
    ) -> None:
        """⚠ RED at ``169925f`` on every identity host (no class), wherever an unanchored marker is spoofed
        (an ASSERT / coercion text echoing the governed marker is served ``TxnGovernedConflictError`` — R-9),
        and wherever an echoed retry / cascade phrase reaches an UPSTREAM reader (~2 s of retries → contention
        exhausted; a skipped root cause). amendment 35 §2 + amendment 36 §1.2 pin 1 — the RS-5 classifier
        property, STRIKE 3 of 3 (after a28c any further instance is a pinned bound, amendment 36 §1): ∀ phrase
        × ∀ live host × both raise sites, the echoed caller value moves NOTHING — the served CLASS is the
        host's; the ONE driver makes exactly ONE attempt (a domain rejection is never retried); the call
        returns within half the retry deadline; and on ``execute_transaction`` the served root cause is the
        one a PLAIN value yields. ASSERT ↔ coercion ↔ recursion may trade LABELS (one class — amendment 36
        §1.2 pin 4's bound)."""
        connection, env = admin_db
        for statement in _ECHO_SETUP:
            await run(connection, statement)
        literal = _ECHO_PHRASES[phrase]
        echoed = (
            literal
            if literal is not None
            else await _engine_text(connection, phrase.removeprefix("host-"), _PLAIN_VALUE)
        )
        seed, statement, expected = _ECHO_HOSTS[host]
        plain_position: re.Match[str] | None = None
        if path == "execute_transaction":
            plain = f"plain-root-cause ·{host}"
            if seed is not None:
                await run(connection, seed, {"v": plain})
            plain_raised = await a28b._raise_through(path, statement, connection, env, {"v": plain})
            plain_position = _ROOT_CAUSE_POSITION.search(str(plain_raised))
        # Each host is driven with a FRESH value: the echoed phrase, tagged so no two cases share a row.
        value = f"{echoed} ·{host}·{path}"
        if seed is not None:
            await run(connection, seed, {"v": value})
        attempts = _count_attempts(monkeypatch)
        started = time.monotonic()
        raised = await a28b._raise_through(path, statement, connection, env, {"v": value})
        elapsed = time.monotonic() - started
        assert _class_name(raised) == expected, (
            f"{host} via {path}, echoing {phrase} ({echoed!r}): the host's class is {expected}, the driver "
            f"raised {type(raised).__name__}: {raised} — a caller VALUE the engine echoed moved the class "
            "(amendment 35 §2 / 36 §1: typed wherever the engine types; text only for the untyped kinds)"
        )
        if expected == TxnDomainRejectionError.__name__:
            assert type(raised) is TxnDomainRejectionError, f"{host}: exactly the base class, got {raised!r}"
        assert attempts["n"] == 1, (
            f"{host} via {path}, echoing {phrase}: the ONE driver made {attempts['n']} attempts for a DOMAIN "
            "rejection — an echoed value reached the RETRY DECISION (amendment 36: typed "
            "TransactionConflict only)"
        )
        assert elapsed < _txn._TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS / 2, (
            f"{host} via {path}, echoing {phrase}: {elapsed:.2f}s — the echoed value bought engine retries"
        )
        if plain_position is not None:
            served = _ROOT_CAUSE_POSITION.search(str(raised))
            assert served is not None and served.groups() == plain_position.groups(), (
                f"{host} via execute_transaction, echoing {phrase}: the root cause served is "
                f"{served and served[0]!r}, "
                f"a plain value's is {plain_position[0]!r} — an echoed value moved the ROOT-CAUSE SELECTOR "
                "(amendment 36: typed NotExecuted only)"
            )


# ------------------------------------------------------------------------------------------------------------
# # amendment 35 §2 item 1 (FK-ADV-3) — R is TYPED on the TRANSACTIONAL path too: ``_failed_statements`` keeps
# the whole per-statement dict and the raise site reads the SDK's ``parse_query_error`` (measured by the a28b
# adversary §A.3: the R-txn dict carries ``kind: AlreadyExists`` / ``details.kind: Record``). GENERATED over
# the SDK's derived already-exists detail kinds × {engine wording, the other kind's wording} — the twin of
# a28b's pin (c) on the run_query path. And the record TEXT pair is DELETED (one fewer spoofable marker): an
# UNTYPED rejection worded like a record collision is NOT the class, on either site.
# ------------------------------------------------------------------------------------------------------------
# #

#: The engine's cascade entry for a rolled-back transaction's COMMIT (measured, both probes: ``kind: Query``,
#: ``details.kind: NotExecuted``) — the forged responses carry it after the root cause, as the engine does.
_COMMIT_CASCADE = {
    "status": "ERR",
    "kind": "Query",
    "details": {"kind": "NotExecuted"},
    "result": "Cannot COMMIT: the transaction was aborted due to a prior error",
    "time": "1µs",
}


async def _execute_transaction_raises(statement_result: dict[str, Any]) -> BaseException:
    import test_surreal_store as surreal_store_tests  # noqa: PLC0415 - its fake (REUSED), imported at use

    connection = surreal_store_tests._TxnRollbackFakeConnection(
        responses=[
            {"result": [{"status": "OK", "result": None, "time": "1µs"}, statement_result, _COMMIT_CASCADE]}
        ]
    )

    async def acquire() -> Any:
        return connection

    async def drop(_connection: Any) -> None:
        return None

    try:
        await execute_transaction(
            "BEGIN;\nCREATE rx:taken;\nCOMMIT;", {}, acquire=acquire, drop=drop, url="ws://unit"
        )
    except BaseException as raised:  # noqa: BLE001 - classified below
        return raised
    pytest.fail("execute_transaction raised nothing for a forged ERR response")


def _already_exists_statement(kind: str, text: str) -> dict[str, Any]:
    """A forged per-statement ERR in the engine's own shape (a28b §A.1b / adversary §A.3)."""
    inner = {"id": "rx:taken"} if kind == "Record" else {"name": "x"}
    return {
        "status": "ERR",
        "kind": "AlreadyExists",
        "details": {"kind": kind, "details": inner},
        "result": text,
        "time": "1µs",
    }


_RECORD_WORDING = "Database record `rx:taken` already exists"


class TestTheRecordShapeIsTypedOnTheTransactionalPath63cIAa28c:
    @pytest.mark.parametrize("wording", ["engine-wording", "reworded"])
    @pytest.mark.parametrize("kind", sorted(a28b._sdk_already_exists_kinds()))
    async def test_am35_2_1_the_class_iff_the_sdk_says_the_record_id_is_taken_on_execute_transaction(
        self, kind: str, wording: str
    ) -> None:
        """⚠ RED at ``169925f`` for ``Record`` (no class) and on a text-classified build for the reworded
        legs. amendment 35 §2 item 1 (FK-ADV-3, ``replace_with_adapter``): on ``execute_transaction`` the
        per-statement dict is TYPED by ``surrealdb.errors.parse_query_error`` — ``AlreadyExistsError`` with a
        record id (kind ``Record``) → ``TxnUniqueViolationError``; any other kind → exactly the base, WHATEVER
        the text says. Both wordings, so a build that still reads the record text on this path reds one leg or
        the other."""
        other_text = f"The {kind.lower()} 'x' already exists"
        if kind == "Record":
            text = _RECORD_WORDING if wording == "engine-wording" else "The table 'x' already exists"
        else:
            text = other_text if wording == "engine-wording" else _RECORD_WORDING
        raised = await _execute_transaction_raises(_already_exists_statement(kind, text))
        if kind == "Record":
            assert _class_name(raised) == a28b._CONFLICT_CLASS_NAME, (
                f"a per-statement AlreadyExists(Record) worded {text!r} must raise "
                f"{a28b._CONFLICT_CLASS_NAME} on "
                "execute_transaction — typed via parse_query_error, never the text; got "
                f"{type(raised).__name__}: "
                f"{raised}"
            )
        else:
            assert type(raised) is TxnDomainRejectionError, (
                f"a per-statement AlreadyExists({kind}) worded {text!r} is NOT a taken row id — exactly the "
                "base "
                f"TxnDomainRejectionError; got {type(raised).__name__}: {raised}"
            )

    @pytest.mark.parametrize("path", ["run_query", "execute_transaction"])
    async def test_am35_2_1_the_record_TEXT_pair_is_deleted_an_untyped_record_wording_is_not_the_class(
        self, path: str
    ) -> None:
        """⚠ RED on a28b's reference (it still carries ``("database record", "already exists")``); GREEN at
        ``169925f`` (no class at all). amendment 35 §2 item 1: "the record text pair is DELETED" — an UNTYPED
        rejection (``kind: Internal``, no details — the shape an ASSERT or a U collision arrives in) whose
        text is worded exactly like a record collision is NOT the unique-violation class on either raise site:
        the record shape is decided by the type, and only by the type."""
        if path == "run_query":
            raised = await a28b._run_query_raises(
                sdk_errors.InternalError(kind="Internal", message=_RECORD_WORDING, details=None)
            )
        else:
            raised = await _execute_transaction_raises(
                {"status": "ERR", "kind": "Internal", "result": _RECORD_WORDING, "time": "1µs"}
            )
        assert type(raised) is TxnDomainRejectionError, (
            f"{path}: an UNTYPED rejection worded {_RECORD_WORDING!r} was served {type(raised).__name__} — "
            "the "
            "record text pair survives (amendment 35 §2 item 1: deleted; one fewer spoofable marker)"
        )


# ------------------------------------------------------------------------------------------------------------
# # amendment 35 §2 item 4 (R-8, MP-1's untried sibling) — the SECOND shared thing, mutated once: the ONE
# mapping helper ``_domain_rejection_error`` builds the class for BOTH identity shapes on BOTH raise sites. A
# raise site that builds ``TxnUniqueViolationError`` directly (a typed branch's private ``raise``) keeps the
# class under this mutation and reds.
# ------------------------------------------------------------------------------------------------------------
# #
class TestTheOneMappingHelperBuildsTheClassEverywhere63cIAa28c:
    @pytest.mark.parametrize("path", ["run_query", "execute_transaction"])
    @pytest.mark.parametrize(
        "situation", sorted(name for name, (_s, _st, taken) in a28b._SITUATIONS.items() if taken)
    )
    async def test_am35_2_4_mutating_the_mapping_helper_moves_every_identity_leg(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
        monkeypatch: pytest.MonkeyPatch,
        situation: str,
        path: str,
    ) -> None:
        """⚠ RED at ``169925f`` (the CONTROL: no class to lose). amendment 35 §2 item 4, GENERATED over the
        identity situations (derived from ``a28b._SITUATIONS``: every situation whose identity is taken) ×
        both raise sites: CONTROL — unpatched, the class; MUTATION — ``_domain_rejection_error`` patched to
        build the BASE class for every label → the raise site serves exactly the base. The record-id legs are
        the typed ones: a typed branch that constructs the class itself survives here."""
        connection, env = admin_db
        setup, statement, _taken = a28b._SITUATIONS[situation]
        for setup_statement in setup:
            await run(connection, setup_statement)
        control = await a28b._raise_through(path, statement, connection, env)
        assert _class_name(control) == a28b._CONFLICT_CLASS_NAME, f"CONTROL {situation}/{path}: {control!r}"
        calls: list[str] = []

        def _base_only(error_class: str, message: str, *, kind: str | None = None) -> Any:
            calls.append(error_class)
            return TxnDomainRejectionError(message)

        monkeypatch.setattr(_txn, "_domain_rejection_error", _base_only)
        muted = await a28b._raise_through(path, statement, connection, env)
        assert calls, f"{situation}/{path}: the patched mapping helper was never called (#194: did it LAND?)"
        assert type(muted) is TxnDomainRejectionError, (
            f"{situation} via {path}: `_domain_rejection_error` builds only the base class, yet the raise "
            "site "
            f"served {type(muted).__name__} — a raise site constructs the class OUTSIDE the ONE mapping "
            "helper "
            "(amendment 35 §2 item 4 / R-8: routing is not sharing)"
        )


# ------------------------------------------------------------------------------------------------------------
# # amendment 35 §2 item 5 — PIN THE MISS (the residual bound). The anchored U test and the typed R test rest
# on two measured engine facts; the day either changes, these RED with the re-open instruction.
# ------------------------------------------------------------------------------------------------------------
# #
#: live shape → (setup, colliding statement, the engine noun its text OPENS with on the pinned engine
#: version).
_ENGINE_NOUNS: dict[str, tuple[tuple[str, ...], str, str]] = {
    "record-id-collision": (
        ("DEFINE TABLE rx SCHEMALESS", "CREATE rx:taken CONTENT { v: 1 }"),
        "CREATE rx:taken CONTENT { v: 2 }",
        "Database record",
    ),
    "unique-index-collision": (
        a28b._SITUATIONS["unique-index-collision"][0],
        a28b._SITUATIONS["unique-index-collision"][1],
        "Database index",
    ),
    "table-already-exists": (("DEFINE TABLE tx SCHEMALESS",), "DEFINE TABLE tx", "The table"),
    "assert-violation": (
        a28b._SITUATIONS["assert-violation"][0],
        a28b._SITUATIONS["assert-violation"][1],
        "Found",
    ),
    "coercion-failure": (
        ("DEFINE TABLE cx SCHEMAFULL", "DEFINE FIELD n ON cx TYPE int"),
        "CREATE cx:one CONTENT { n: 'not-an-int' }",
        "Couldn't coerce",
    ),
    "governed-throw": ((), "THROW 'governed_conflict:gx:one'", "An error occurred:"),
}
_STRIKE_BOUND = (
    "KNOWN BOUND (amendment 35 §2 item 5; RS-5 classifier property, strike 3 of 3 — a fourth strike is a "
    "pinned "
    "bound, never a round): the anchored U test and the typed R test rest on measured engine facts; the day "
    "either changes, re-anchor the marker / add the typed branch and delete this pin"
)


class TestTheEngineFactsTheClassifierRestsOn63cIAa28c:
    @pytest.mark.parametrize("path", ["sdk", "txn"])
    @pytest.mark.parametrize("shape", sorted(_ENGINE_NOUNS))
    async def test_am35_2_5_KNOWN_BOUND_every_live_shape_opens_with_its_engine_noun(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
        shape: str,
        path: str,
    ) -> None:
        """GREEN at ``169925f`` and on a correct build — a property of the pinned engine (3.2.4, measured
        2026-09-27, ``REPORT-contract-63c-i-a-a28c.md`` §A.1). Each live rejection's engine-authored text
        OPENS with its noun on BOTH paths (the SDK exception on ``query()``; the per-statement ``result``
        inside ``BEGIN … COMMIT``) — the fact a position-0 prefix test is anchored to: a caller value is
        always echoed AFTER the noun."""
        connection, _env = admin_db
        setup, statement, noun = _ENGINE_NOUNS[shape]
        for setup_statement in setup:
            await run(connection, setup_statement)
        if path == "sdk":
            try:
                await connection.query(statement)
            except Exception as error:  # noqa: BLE001 - the text is the measurement
                text = str(error)
            else:
                pytest.fail(f"{shape}: {statement!r} raised nothing")
        else:
            raw = await connection.query_raw(f"BEGIN;\n{statement};\nCOMMIT;", {})
            substantive = [
                entry
                for entry in raw.get("result") or []
                if entry.get("status") == "ERR" and (entry.get("details") or {}).get("kind") != "NotExecuted"
            ]
            assert substantive, f"{shape}: no substantive ERR in {raw!r}"
            text = str(substantive[0].get("result"))
        assert text.startswith(noun), (
            f"{_STRIKE_BOUND}: {shape} via {path} now opens {text[:60]!r}, not {noun!r}"
        )

    async def test_am36_1_1_KNOWN_BOUND_every_cascade_notice_is_typed_NotExecuted(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
    ) -> None:
        """GREEN at ``169925f`` and on a correct build — the engine fact amendment 36's typed root-cause
        selector rests on: every cascade entry of a rolled-back transaction (the refused COMMIT after a
        rejection) carries ``kind: Query`` and ``details.kind: NotExecuted``. Re-open trigger: the engine
        stops typing it."""
        connection, _env = admin_db
        setup, statement, _taken = a28b._SITUATIONS["assert-violation"]
        for setup_statement in setup:
            await run(connection, setup_statement)
        raw = await connection.query_raw(f"BEGIN;\n{statement};\nCOMMIT;", {})
        cascades = [
            entry
            for entry in raw.get("result") or []
            if entry.get("status") == "ERR" and str(entry.get("result")).startswith(CASCADE_OPENINGS)
        ]
        assert cascades, f"no cascade entry in {raw!r}"
        assert all(
            entry.get("kind") == "Query" and (entry.get("details") or {}).get("kind") == "NotExecuted"
            for entry in cascades
        ), f"{_STRIKE_BOUND}: {cascades!r}"

    async def test_am35_2_5_KNOWN_BOUND_a_unique_index_collision_is_untyped_on_the_transactional_path(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
    ) -> None:
        """GREEN at ``169925f`` and on a correct build. amendment 35 §2 item 5: the U-txn per-statement dict
        carries ``kind: Internal`` and NO typed details (the U-sdk twin is a28b's
        ``test_am33_KNOWN_BOUND_a_unique_index_collision_is_an_untyped_InternalError``) — nothing typed to key
        on, which is why U alone stays text."""
        connection, _env = admin_db
        setup, statement, _taken = a28b._SITUATIONS["unique-index-collision"]
        for setup_statement in setup:
            await run(connection, setup_statement)
        raw = await connection.query_raw(f"BEGIN;\n{statement};\nCOMMIT;", {})
        entry = next(
            item
            for item in raw.get("result") or []
            if item.get("status") == "ERR" and (item.get("details") or {}).get("kind") != "NotExecuted"
        )
        assert entry.get("kind") == "Internal" and not entry.get("details"), f"{_STRIKE_BOUND}: {entry!r}"


# ------------------------------------------------------------------------------------------------------------
# amendment 36 §1.2 pin 3 — THE EXACT SET OF ENGINE-TEXT READERS in ``_txn`` (completeness: what makes a fifth
# arrival of the echoed-value class unrepresentable). ALLOWLIST THE SAFE: the derivation reports EVERY
# function in ``_txn`` that performs ANY membership (``in`` / ``not in``), prefix / suffix (``startswith`` /
# ``endswith``), search (``find`` / ``index`` / ``count`` / ``partition``) or ``re`` test — whatever it tests,
# and wherever the ``str()`` happened. (Its first version required a ``str(...)`` call AND the test in ONE
# function, and was blind to exactly the shape ``169925f`` ships: ``_is_retryable_conflict_text(text: str)`` /
# ``_is_domain_cascade_notice(text: str)`` test a PARAMETER whose ``str()`` is in the caller. The forbidden
# spellings are unbounded; the testers ``_txn`` legitimately holds are four, each named below with the reason
# it is not an engine-text decision.) Of those, exactly ONE may read ENGINE text — ``_classify_engine_error``
# — and inside it the text branch is reachable only where the engine's kind does not decide the label
# (``Internal``; ``Validation`` for recursion depth — FK-a28c-9) or where the input carries no kind at all (a
# bare text): the positive control over EVERY other SDK kind below. STATED BOUND (who this is for — the honest
# builder): a text test hidden inside one of the three non-engine allowlisted functions, or at module level
# (which runs once, at import, and cannot decide per error), is not seen here; the KB whole-reader pin sees
# its EFFECT.
# ------------------------------------------------------------------------------------------------------------
_ENGINE_TEXT_READER = "_classify_engine_error"
#: The functions in ``_txn`` allowed to perform a membership / prefix / search / regex test, each with the
#: reason it is safe. Only ``_ENGINE_TEXT_READER`` reads engine text.
_TEXT_TEST_ALLOWLIST: dict[str, str] = {
    _ENGINE_TEXT_READER: "THE one engine-text reader (amendment 36 §1.2 pin 3), text only for untyped kinds",
    "_assert_envelope_integrity": (
        "tests the CALLER's own statement text (the envelope terminator), never the engine's"
    ),
    "compose": "a params-dict KEY membership test",
    "is_connection_error": "a TYPED kind membership (``error.kind in _CONNECTION_ERROR_KINDS``)",
}
#: The SDK kinds whose TEXT may still decide a label (measured 3.2.4: the U prefix / ASSERT / coercion arrive
#: as ``Internal``; recursion depth as ``Validation`` — FK-a28c-9) plus ``Thrown``, whose OUR-authored
#: ``governed_conflict:`` prefix is our protocol, not engine-text classification (amendment 36 §1.1).
_TEXT_DECIDED_KINDS = frozenset({"Internal", "Validation", "Thrown"})
_SEARCH_METHODS = frozenset({"startswith", "endswith", "find", "index", "count", "partition"})


def _text_testers_in(tree: ast.Module) -> set[str]:
    """Every function (or method) in ``tree`` that performs a membership / prefix / search / ``re`` test."""
    testers: set[str] = set()
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(function):
            if isinstance(node, ast.Compare) and any(
                isinstance(operator, (ast.In, ast.NotIn)) for operator in node.ops
            ):
                testers.add(function.name)
                break
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                receiver = node.func.value
                regex = isinstance(receiver, ast.Name) and receiver.id == "re"
                if node.func.attr in _SEARCH_METHODS or regex:
                    testers.add(function.name)
                    break
    return testers


def _engine_text_readers() -> set[str]:
    """The derived testers of ``loremaster/store/_txn.py``."""
    return _text_testers_in(ast.parse(pathlib.Path(_txn.__file__).read_text(encoding="utf-8")))


#: Hostile TEXT for the positive control: each untyped-kind label's own engine words (the U prefix, ASSERT,
#: coercion, recursion depth) and our governed prefix — carried by a typed error of a kind that must IGNORE
#: them.
_HOSTILE_TEXTS = {
    "unique-prefix": "Database index `k` already contains 'v', with record `k:1`",
    "assert": "Found 'v' for field `s`, with record `t:1`, but field must conform to: $value = 'ok'",
    "coercion": "Couldn't coerce value for field `n` of `t:1`: Expected `int` but found `'v'`",
    "recursion": "Parse error: Exceeded expression recursion depth limit",
    "governed": "An error occurred: governed_conflict:t:1",
}


def _sdk_kinds() -> list[str]:
    """Every kind the installed SDK maps to an error class (``surrealdb.errors.KIND_TO_CLASS``) — DERIVED."""
    return sorted(str(kind) for kind in getattr(sdk_errors, "KIND_TO_CLASS", {}))


class TestTheEngineTextReadersAreExactlyTheClassifier63cIAa28c:
    def test_am36_1_2_3_the_only_engine_text_reader_is_the_classifier(self) -> None:
        """⚠ RED at ``169925f`` (``_is_retryable_conflict_text`` — the retry decision — and
        ``_is_domain_cascade_notice`` — the root-cause selector — test engine text). amendment 36 §1.2 pin 3 —
        EXACT SET, allowlist-the-safe: every tester the derivation finds in ``_txn`` is allowlisted with a
        reason, and the classifier is among them. A new tester reds BY NAME. (A builder who needs a new
        membership / prefix test in ``_txn`` compares a typed kind with ``==`` or asks for an allowlist row —
        BUILDER CONSTRAINTS item 1.)"""
        testers = _engine_text_readers()
        assert _ENGINE_TEXT_READER in testers, (
            f"the derivation does not see `{_ENGINE_TEXT_READER}` — broken, not clean (it IS a text reader)"
        )
        unlisted = sorted(testers - set(_TEXT_TEST_ALLOWLIST))
        assert not unlisted, (
            f"functions in _txn that test text / membership but are not allowlisted: {unlisted} — exactly "
            f"`{_ENGINE_TEXT_READER}` may read ENGINE text (amendment 36 §1.2 pin 3); every other decision "
            "reads the SDK's typed kind (compare it with `==`)"
        )

    def test_am36_1_2_3_the_derivation_SEES_a_text_reader(self) -> None:
        """POSITIVE CONTROL, run THROUGH the derivation: it reports a reader that tests ``str(error)``, a
        reader that tests a ``text: str`` PARAMETER whose ``str()`` is in its caller (``169925f``'s own
        shape), a prefix reader, a ``re`` reader and a method; it does not report a typed ``==`` decision or a
        caller that only stringifies."""
        synthetic = ast.parse(
            "import re\n"
            "def texty(error):\n    return 'can be retried' in str(error)\n"
            "def param_text(text: str) -> bool:\n    return any(marker in text for marker in MARKERS)\n"
            "def caller(failed):\n    return param_text(str(failed.raw_result))\n"
            "def prefixed(failed):\n    return failed.raw_result.startswith('The query was not')\n"
            "def regexed(text):\n    return re.search('retried', text) is not None\n"
            "class Holder:\n    def method(self, text):\n        return 'x' not in text\n"
            "def typed(error):\n    return error.details.get('kind') == 'TransactionConflict'\n"
        )
        assert _text_testers_in(synthetic) == {"texty", "param_text", "prefixed", "regexed", "method"}, (
            _text_testers_in(synthetic)
        )

    def test_am36_1_2_3_the_sdk_kind_domain_is_derived_and_non_vacuous(self) -> None:
        """GREEN at ``169925f``: the positive control below iterates the SDK's own kinds, and there are kinds
        outside the text-decided set (so the control is not vacuous)."""
        kinds = _sdk_kinds()
        assert set(kinds) - _TEXT_DECIDED_KINDS, kinds
        assert _TEXT_DECIDED_KINDS - {"Thrown"} <= set(kinds), kinds

    @pytest.mark.parametrize("text", sorted(_HOSTILE_TEXTS))
    @pytest.mark.parametrize("kind", [kind for kind in _sdk_kinds() if kind not in _TEXT_DECIDED_KINDS])
    def test_am36_1_2_3_a_typed_kind_never_reaches_the_text_branch(self, kind: str, text: str) -> None:
        """⚠ RED at ``169925f`` (text decides for every kind). amendment 36 §1.2 pin 3's positive control,
        GENERATED over every SDK kind the engine TYPES (``KIND_TO_CLASS`` minus the text-decided kinds) ×
        every untyped label's own words: a typed error of such a kind carrying that hostile text is NEVER
        classified by the text — it is served ``unspecified`` (or its typed verdict), never the unique /
        ASSERT / coercion / recursion / governed label."""
        error = sdk_errors.parse_query_error({"status": "ERR", "kind": kind, "result": _HOSTILE_TEXTS[text]})
        label = _txn._classify_engine_error(error)
        text_labels = {
            getattr(_txn, name, None)
            for name in (
                "_ERROR_CLASS_UNIQUE_VIOLATION",
                "_ERROR_CLASS_ASSERT_VIOLATION",
                "_ERROR_CLASS_FIELD_COERCION",
                "_ERROR_CLASS_QUERY_TOO_COMPLEX",
                "_ERROR_CLASS_GOVERNED_CONFLICT",
            )
        } - {None}
        assert label not in text_labels, (
            f"a typed `{kind}` error carrying {text!r} words was labelled {label!r} BY ITS TEXT — the text "
            "branch is "
            f"reachable only for {sorted(_TEXT_DECIDED_KINDS)} (amendment 36 §1.1 / FK-a28c-9)"
        )


# ------------------------------------------------------------------------------------------------------------
# amendment 36 §1.2 pin 4 — PIN THE MISS (the stated bound): among the untyped kinds, an echoed value can move
# the teaching LABEL between ASSERT / coercion (never the class, never the retry — pin 1). Re-open trigger:
# the engine types any of these kinds. Order-agnostic: the bound is OPEN iff at least one direction moves the
# label.
# ------------------------------------------------------------------------------------------------------------
_LABEL_BOUND = (
    "KNOWN BOUND (amendment 36 §1.2 pin 4): an echoed value may move the LABEL between ASSERT and coercion "
    "(one "
    "class); RE-OPEN TRIGGER: the engine types either kind — then key the label on the kind and delete this "
    "pin"
)


class TestTheInternalLabelBound63cIAa28c:
    async def test_am36_1_2_4_KNOWN_BOUND_an_echo_can_trade_the_assert_and_coercion_labels(
        self,
        admin_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
    ) -> None:
        """GREEN at ``169925f`` and on a correct build (the bound is open — the class never moves, pin 1). The
        ASSERT host echoing the coercion words and the coercion host echoing the ASSERT words, through the
        classifier: at least one is labelled as the OTHER. Also the premise: both arrive untyped
        (``Internal``)."""
        connection, _env = admin_db
        for statement in _ECHO_SETUP:
            await run(connection, statement)
        assert_text = await _engine_text(connection, "assert-violation", "x coerce y")
        coercion_text = await _engine_text(connection, "coercion-failure", "x must conform to y")
        assert_label = _txn._classify_engine_error(assert_text)
        coercion_label = _txn._classify_engine_error(coercion_text)
        moved = (
            assert_label != _txn._ERROR_CLASS_ASSERT_VIOLATION
            or coercion_label != _txn._ERROR_CLASS_FIELD_COERCION
        )
        assert moved, f"{_LABEL_BOUND}: neither label moved ({assert_label!r}, {coercion_label!r})"
        try:
            await connection.query("CREATE hx SET s = 'not-ok'")
        except Exception as error:  # noqa: BLE001 - the premise is the SDK kind
            assert getattr(error, "kind", None) == "Internal" and not getattr(error, "details", None), (
                f"{_LABEL_BOUND}: the ASSERT rejection is now typed: {error!r}"
            )
        else:
            pytest.fail("the ASSERT host raised nothing")


# ======================================================================================================== #
# amendment 35 §1 — C2 RE-RULED: THE GATE IS THE VISIBILITY SEAM (C2's gate property, STRIKE 3 of 3 — F-2 →
# W19 → B13; a fourth strike is a pinned bound, never a round). Property: ∀ caller relation sets S ⊆
# {member-of-THIS, keeper-of-OTHER, member-of-OTHER} × ∀ mint orders — the register PROCEEDS iff
# member-of-THIS ∈ S, else ONE denial with ZERO agent-registry queries. The predicate is
# ``keep_scope(session_keep) ∈ resolve_visible_keeps(keep_store, member_email=principal.email)`` — THE
# function the PDP's ``Subject.visible_keep_ids`` is built from — and nothing else.
# ======================================================================================================== #

#: The relation DOMAIN, generated (amendment 35 §1): a principal relates to a keep as its KEEPER or as a
#: household MEMBER, and to THIS session's keep or to ANOTHER keep. KEEPER-of-THIS is the minting principal
#: (alice — Fork D auto-households her), the not-foreign control every cell carries; it is never carol's
#: relation.
_KEEP_SIDES = ("this", "other")
_HOUSEHOLD_ROLES = ("member", "keeper")
_MINTING_RELATION = "keeper-of-this"
_RELATIONS: tuple[str, ...] = tuple(
    relation
    for relation in (f"{role}-of-{side}" for side, role in itertools.product(_KEEP_SIDES, _HOUSEHOLD_ROLES))
    if relation != _MINTING_RELATION
)
#: The ONE relation that makes THIS keep visible to carol — the verdict is DERIVED from it, never listed per
#: cell.
_VISIBLE_RELATION = "member-of-this"
#: Every relation set (the powerset — 8 sets), × both mint orders (keep ids are time-ordered ULIDs, so a gate
#: that picks ONE of the caller's keeps by ordering — first / min / max — differs from membership in one order
#: or the other; KC's own first version was a mint-order monoculture, adversary P0).
_RELATION_SETS: tuple[frozenset[str], ...] = tuple(
    frozenset(combination)
    for size in range(len(_RELATIONS) + 1)
    for combination in itertools.combinations(_RELATIONS, size)
)
_MINT_ORDERS = ("other-keep-first", "this-keep-first")
#: The keep-store verb that constructs each household ROLE through the REAL store (amendment 35 §1 item 3: a
#: keeper is a member by construction — ``create_keep`` auto-households its keeper, Fork D).
_RELATION_VERBS: dict[str, tuple[str, str]] = {
    "keeper": ("create_keep", "keeper_email"),
    "member": ("add_household_member", "member_email"),
}


def _relation_set_id(relations: frozenset[str]) -> str:
    return "+".join(sorted(relations)) or "no-relation"


async def _give_carol(
    ctx: Any, world: dict[str, Any], relations: frozenset[str], order: str
) -> dict[str, str]:
    """Build ``relations`` for carol through the REAL keep store, in ``order`` relative to alice's session
    keep (alice keeps ``s-alice`` — the minting principal). Returns ``{side: bare keep id}`` for every keep
    carol can reach, so the caller can derive the visible set it expects. Leaves the holder as carol."""
    keep_store = ctx._keep_store
    emails = world["emails"]
    reached: dict[str, str] = {}

    async def _other_relations() -> None:
        if "keeper-of-other" in relations:
            carol_keep = await keep_store.create_keep(
                keeper_email=emails["carol"], type="team", name="carol-own"
            )
            reached["carol-own"] = bare_record_key(carol_keep.id)
        if "member-of-other" in relations:
            dan_keep = await keep_store.create_keep(keeper_email=emails["dan"], type="team", name="dan-own")
            await keep_store.add_household_member(
                keep_id=bare_record_key(dan_keep.id), member_email=emails["carol"]
            )
            reached["dan-own"] = bare_record_key(dan_keep.id)

    if order == "other-keep-first":
        await _other_relations()
    await a28._alice_keeps_a_session(ctx, world, "s-alice")
    this_bare = bare_record_key((await a28._session_keep_ids(world["admin_conn"], "s-alice"))[0])
    if order == "this-keep-first":
        await _other_relations()
    if _VISIBLE_RELATION in relations:
        await keep_store.add_household_member(keep_id=this_bare, member_email=emails["carol"])
        reached["this"] = this_bare
    world["holder"]["email"] = emails["carol"]
    return {"this-keep": this_bare, **reached}


class TestTheGateIsTheVisibilitySeam63cIAa28c:
    def test_am35_1_3_every_relation_is_constructible_through_the_stores_public_verbs(self) -> None:
        """GREEN at ``169925f`` — the domain's constructibility (amendment 35 §1 item 3): every household ROLE
        the relation domain is generated from has ONE public async ``KeepStore`` verb that builds it (a verb
        that vanishes or renames its principal argument reds here, loud — never a silently smaller fixture),
        and the generated domain is exactly the three ruled relations."""
        assert set(_RELATION_VERBS) == set(_HOUSEHOLD_ROLES), (_RELATION_VERBS, _HOUSEHOLD_ROLES)
        for role, (verb, principal_argument) in _RELATION_VERBS.items():
            method = getattr(keeps_module.KeepStore, verb, None)
            assert method is not None and inspect.iscoroutinefunction(method), (
                f"{role}: KeepStore.{verb} is gone"
            )
            assert principal_argument in inspect.signature(method).parameters, (role, verb)
        assert set(_RELATIONS) == {"member-of-this", "member-of-other", "keeper-of-other"}, _RELATIONS
        assert len(_RELATION_SETS) == 2 ** len(_RELATIONS), _RELATION_SETS

    @pytest.mark.parametrize("order", _MINT_ORDERS)
    @pytest.mark.parametrize("relations", _RELATION_SETS, ids=_relation_set_id)
    async def test_am35_1_1_the_register_proceeds_iff_THIS_keep_is_visible(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any, relations: frozenset[str], order: str
    ) -> None:
        """⚠ RED at ``169925f`` on every cell WITHOUT member-of-THIS (the registry's preflight reads before
        the gate — the probes leak alice's agent facts and the seam spy sees queries). amendment 35 §1 pin 1 —
        C2's gate property, STRIKE 3 of 3 (F-2 → W19 → B13; a fourth strike is a pinned bound): GENERATED over
        the relation powerset × both mint orders × every foreign probe kind (``a28._FOREIGN_PROBES``); the
        verdict is DERIVED from the cell (``member-of-this ∈ S``). PROCEED cells: no probe is
        ``GovernedDenied`` and the registry seam sees queries (the control that the spy is not blind). DENY
        cells: every probe is ONE byte-identical ``GovernedDenied``, with ZERO queries through
        ``AgentRegistry._query``. The fixture checks itself: the seam's own answer for carol is exactly the
        keeps her relations reach (a keeper IS a member)."""
        async with credentialed_app_context(
            monkeypatch,
            tmp_path,
            principals={"alice": "member", "carol": "member", "dan": "member"},
            dim=a28._DIM,
        ) as world:
            ctx = world["ctx"]
            reached = await _give_carol(ctx, world, relations, order)
            this_bare = reached.pop("this-keep")
            visible = await visible_keeps_module.resolve_visible_keeps(
                ctx._keep_store, member_email=world["emails"]["carol"]
            )
            assert visible == {keep_scope(bare) for bare in reached.values()}, (
                f"FIXTURE: carol's relations {sorted(relations)} should make exactly {sorted(reached)} "
                "visible; the "
                f"seam answers {sorted(visible)}"
            )
            proceeds = _VISIBLE_RELATION in relations
            assert (keep_scope(this_bare) in visible) is proceeds, (relations, visible)
            seen = a28._spy_registry_queries(monkeypatch, ctx.agent_registry)
            served = {
                label: await a28._outcome(ctx.comms(action="register", session="s-alice", **probe))
                for label, probe in a28._FOREIGN_PROBES.items()
            }
            kinds = {kind for kind, _text in served.values()}
            if proceeds:
                assert GovernedDenied.__name__ not in kinds, (
                    f"{_relation_set_id(relations)} / {order}: carol is householded in THIS keep — the "
                    "register "
                    "must PROCEED past the gate whatever else she keeps or belongs to (B13 denied her): "
                    f"{served}"
                )
                assert seen, (
                    f"CONTROL {_relation_set_id(relations)}: the seam spy saw no registry query — blind"
                )
            else:
                assert kinds == {GovernedDenied.__name__}, (_relation_set_id(relations), order, served)
                assert len({text for _kind, text in served.values()}) == 1, served
                assert seen == [], (
                    f"{_relation_set_id(relations)} / {order}: a foreign register queried the registry "
                    "before the "
                    f"gate denied it: {seen!r}"
                )

    @pytest.mark.parametrize("leg", ["hide-this-keep-from-a-member", "show-this-keep-to-a-stranger"])
    async def test_am35_1_2_the_gate_READS_the_seam(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any, leg: str
    ) -> None:
        """GREEN at ``169925f`` (its gate already reads the seam — amendment 35 §1: "HEAD's `_comms_register`
        already spells it this way; the ruling makes it the pinned INVARIANT"); RED on any build whose gate
        re-derives visibility privately. amendment 35 §1 pin 2 — ROUTING IS NOT SHARING, proven by MUTATION of
        THE seam (every binding of ``visible_keeps.resolve_visible_keeps``, by identity): HIDE this keep from
        a householded member → she is DENIED; SHOW this keep to a stranger → she PROCEEDS past the gate. A
        gate with a private copy of the read passes neither leg. The mutation's landing is asserted (#194)."""
        async with credentialed_app_context(
            monkeypatch,
            tmp_path,
            principals={"alice": "member", "carol": "member", "dan": "member"},
            dim=a28._DIM,
        ) as world:
            ctx = world["ctx"]
            hide = leg == "hide-this-keep-from-a-member"
            relations = frozenset({_VISIBLE_RELATION}) if hide else frozenset()
            reached = await _give_carol(ctx, world, relations, "this-keep-first")
            this_scope = keep_scope(reached["this-keep"])
            carol_email = world["emails"]["carol"]
            control = await a28._outcome(
                ctx.comms(action="register", agent="carolctl", session="s-alice", role="builder")
            )
            assert (control[0] == GovernedDenied.__name__) is not hide, (
                f"CONTROL (unmutated) {leg}: {control}"
            )
            real = visible_keeps_module.resolve_visible_keeps
            landed: list[str] = []

            async def _mutated(keep_store: Any, *, member_email: str) -> frozenset[str]:
                visible = await real(keep_store, member_email=member_email)
                if member_email != carol_email:
                    return visible
                landed.append(member_email)
                return visible - {this_scope} if hide else visible | {this_scope}

            patched = patch_shared_object_everywhere(
                monkeypatch, "resolve_visible_keeps", real, _mutated, expect_in=("loremaster.visible_keeps",)
            )
            seen = a28._spy_registry_queries(monkeypatch, ctx.agent_registry)
            outcome = await a28._outcome(
                ctx.comms(action="register", agent="carolbot", session="s-alice", role="builder")
            )
            assert landed, f"{leg}: the mutated seam was never consulted (patched {patched}) — did it LAND?"
            if hide:
                assert seen == [], (
                    f"the seam hides THIS keep from carol, yet her register queried the registry {seen!r} — "
                    "the "
                    "GATE let her through (a later check denying her is not the gate reading the seam)"
                )
                assert outcome[0] == GovernedDenied.__name__, (
                    f"the seam hides THIS keep from carol, yet her register was served {outcome} — the gate "
                    "does not "
                    "READ `resolve_visible_keeps` (a private visibility derivation: routing is not sharing)"
                )
            else:
                assert outcome[0] != GovernedDenied.__name__, (
                    f"the seam shows THIS keep to a stranger, yet her register was DENIED: {outcome} — the "
                    "gate "
                    "decides on something other than THE visibility seam"
                )


# ------------------------------------------------------------------------------------------------------------
# KC — C2's DUAL: a NOT-foreign principal (householded in THIS keep) PROCEEDS past the gate whatever ELSE she
# keeps or belongs to. The contract's only not-foreign shape holds ONE keep, so a gate that compares this keep
# with the caller's one "primary" keep (B13) passes. Several-keeps shapes, derived as the product of the
# foreign relations with the one not-foreign relation.
# ------------------------------------------------------------------------------------------------------------
_NOT_FOREIGN_PLUS = ["keeper-of-another-keep", "householded-in-another-keep"]


class TestKCAMultiKeepMemberIsNotForeign:
    @pytest.mark.parametrize("minted", ["other-keep-first", "this-keep-first"])
    @pytest.mark.parametrize("extra", _NOT_FOREIGN_PLUS)
    async def test_KC_householded_here_plus_another_relation_proceeds(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Any, extra: str, minted: str
    ) -> None:
        """Both MINT ORDERS: keep ids are ULIDs (time-ordered), so a gate that picks ONE of the caller's keeps
        by ordering (first / min / max) is caught in one order or the other — a single order is itself a
        monoculture (this probe's own first version minted the other keep second and did not see B13: P0,
        self-caught)."""
        async with credentialed_app_context(
            monkeypatch,
            tmp_path,
            principals={"alice": "member", "carol": "member", "dan": "member"},
            dim=a28._DIM,
        ) as world:
            ctx = world["ctx"]
            if minted == "other-keep-first":
                await a28b._shape_carol(ctx, world, extra)
            await a28._alice_keeps_a_session(ctx, world, "s-alice")
            if minted == "this-keep-first":
                await a28b._shape_carol(ctx, world, extra)
            await a28b._shape_carol(ctx, world, "householded-in-this-keep")
            served = {
                label: await a28._outcome(ctx.comms(action="register", session="s-alice", **probe))
                for label, probe in a28._FOREIGN_PROBES.items()
            }
            assert GovernedDenied.__name__ not in {kind for kind, _t in served.values()}, (extra, served)


# ------------------------------------------------------------------------------------------------------------
# KE — K1 / C2's seam spy covers every registry READ only while every store call in agents.py rides
# `AgentRegistry._query` (or the DDL `ensure_ready`). A completeness assertion over the AST, allowlisting the
# two.
# ------------------------------------------------------------------------------------------------------------
_SEAM_CALLEES = {"run_query", "execute_transaction", "execute_read_transaction", "query", "query_raw"}
_SEAM_OWNERS = {"_query", "ensure_ready"}


def test_KE_every_registry_store_call_rides_the_one_seam() -> None:
    tree = ast.parse(pathlib.Path(agents_module.__file__).read_text(encoding="utf-8"))
    escapes: list[str] = []
    seen = 0
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for call in ast.walk(function):
            if isinstance(call, ast.Call):
                name = (
                    call.func.attr if isinstance(call.func, ast.Attribute) else getattr(call.func, "id", "")
                )
                if name in _SEAM_CALLEES:
                    seen += 1
                    if function.name not in _SEAM_OWNERS:
                        escapes.append(f"{function.name}:{call.lineno}:{name}")
    assert seen >= 2, "the scan saw no store call — broken, not clean"
    assert not escapes, f"registry store calls outside the spied seam: {escapes}"


# ======================================================================================================== #
# amendment 34 §2 — ``"empty"`` and THE INVARIANT, enforced at the STATE (a pydantic model validator), so no
# door can serve a contradictory triple. ``owner_classification is None`` ⇔ ``owned_but_unscoped_agents is
# None`` ⇔ ``distinct_owner_principals is None`` (one read, gated together); ``== "empty"`` ⇔ both counts ``==
# 0``; any other member ⇔ both counts ``> 0``. GENERATED over the enum (derived from the RULED spec) × the two
# counts' representative values {None, 0, > 0}.
# ======================================================================================================== #
_OWNED_VALUES: tuple[int | None, ...] = (None, 0, 3)
_DISTINCT_VALUES: tuple[int | None, ...] = (None, 0, 2)


def _ruled_classification_members() -> tuple[Any, ...]:
    return a28._literal_members(a28._RULED_FIELD_SPEC["owner_classification"][0])


def _the_triple_is_legal(owned: int | None, distinct: int | None, classification: Any) -> bool:
    """amendment 34 §2's invariant, as a predicate over the three agent-read values."""
    if classification is None or owned is None or distinct is None:
        return classification is None and owned is None and distinct is None
    if classification == "empty":
        return owned == 0 and distinct == 0
    return owned > 0 and distinct > 0


_TRIPLES = [
    pytest.param(owned, distinct, classification, id=f"owned{owned}-distinct{distinct}-{classification}")
    for owned, distinct, classification in itertools.product(
        _OWNED_VALUES, _DISTINCT_VALUES, (None, *_ruled_classification_members())
    )
]


class TestTheOwnerTripleIsConsistentByConstruction63cIAa28c:
    def test_am34_2_the_generated_domain_carries_both_verdicts(self) -> None:
        """GREEN at ``169925f`` — non-vacuity: the generated triples include legal AND illegal ones for EVERY
        member (so the validator pin below discriminates per member), and ``"empty"`` is a ruled member."""
        members = _ruled_classification_members()
        assert "empty" in members, members
        for member in members:
            verdicts = {
                _the_triple_is_legal(owned, distinct, member)
                for owned, distinct in itertools.product(_OWNED_VALUES, _DISTINCT_VALUES)
            }
            assert verdicts == {True, False}, (member, verdicts)

    @pytest.mark.parametrize(("owned", "distinct", "classification"), _TRIPLES)
    def test_am34_2_the_model_refuses_every_contradictory_triple(
        self, owned: int | None, distinct: int | None, classification: Any
    ) -> None:
        """⚠ RED at ``169925f`` (no model). amendment 34 §2: the invariant is a MODEL VALIDATOR — a legal
        triple constructs; a contradictory one raises ``pydantic.ValidationError`` (served through NO door,
        because no door can build it)."""
        from pydantic import ValidationError  # noqa: PLC0415 - scaffold-local

        model = a28._counts_model()
        values = {
            "owned_but_unscoped_agents": owned,
            "distinct_owner_principals": distinct,
            "owner_classification": classification,
        }
        if _the_triple_is_legal(owned, distinct, classification):
            built = model(**values)
            assert {name: getattr(built, name) for name in values} == values, built
        else:
            with pytest.raises(ValidationError):
                model(**values)


#: amendment 31's ruled owner-sentence STEMS ("owned by the operator …" / "owned by N other principal(s) …")
#: and the unclassified sentence's stem (amendment 31 "owners not classified …", amendment 34 §3's
#: UNCLASSIFIED sentence). The stem table is proven NON-VACUOUS against every non-empty population's served
#: reason below.
_OWNER_SENTENCE_STEMS = ("owned by", "classif")


def _populations_classified_as(predicate: Any) -> list[str]:
    return sorted(
        name
        for name, (_seed, _table, expected) in a28._POPULATIONS.items()
        if predicate(expected.get("owner_classification"))
    )


class TestEmptyContributesNoOwnerSentence63cIAa28c:
    @pytest.mark.parametrize(
        "population", _populations_classified_as(lambda member: member not in (None, "empty"))
    )
    async def test_am34_2_every_classified_population_carries_an_owner_stem(self, population: str) -> None:
        """⚠ RED at ``169925f`` (no preconditions). The CONTROL for the "empty" leg: every population served a
        non-empty classification carries at least one ruled owner-sentence stem — so the stem table sees owner
        sentences (a stem list that matched nothing would make the "empty" pin vacuous)."""
        seed, table, _expected = a28._POPULATIONS[population]
        async with a19a._governed_world() as world:
            await seed(world)
            reason = str((await world.migrate(table)).reason or "").lower()
        assert any(stem in reason for stem in _OWNER_SENTENCE_STEMS), (population, reason)

    @pytest.mark.parametrize(
        "population", [*_populations_classified_as(lambda member: member == "empty"), "RS-1"]
    )
    async def test_am34_2_an_empty_classification_adds_no_owner_sentence(self, population: str) -> None:
        """⚠ RED at ``169925f`` (no preconditions → no ``"empty"`` served). amendment 34 §2: ``"empty"`` = the
        agent read RAN and found nothing to classify — it contributes NO sentence. The served classification
        IS ``"empty"`` and the reason carries no owner-sentence stem."""
        async with a19a._governed_world() as world:
            if population == "RS-1":
                await a28._seed_rs1(world)
                table = MESSAGE_TABLE
            else:
                seed, table, _expected = a28._POPULATIONS[population]
                await seed(world)
            result = await world.migrate(table)
        served = a28._counts(result)
        assert served is not None and served["owner_classification"] == "empty", served
        leaked = [stem for stem in _OWNER_SENTENCE_STEMS if stem in str(result.reason or "").lower()]
        assert not leaked, (
            f"{population}: an `empty` classification rendered owner prose {leaked}: {result.reason!r}"
        )


# ======================================================================================================== #
# amendment 34 §4 (F-5, operator-ruled 2026-09-26) — an UNDEFINED target table is a TYPED, MEASURED answer,
# never a driver error: ``MigrateGovernedResult.table_defined`` is ``False``, ``scanned == backfilled == 0``,
# not refused; the precondition's ONE ``INFO FOR DB`` is the only probe of the table set, and the leg checks
# ``defined_tables`` BEFORE any store read of its own. GENERATED over the leg tables × two store shapes
# (FK-a28c-3): ``minimal`` (the target AND ``agent`` undefined — exactly ONE driver call, ``INFO FOR DB``) and
# ``realistic`` (only the target undefined — ``INFO FOR DB`` once, and no statement names the target table).
# ======================================================================================================== #
_DRIVER_SEAMS = ("run_query", "execute_transaction", "execute_read_transaction")


def _spy_driver_statements(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record the statement of EVERY driver call (every binding of the three driver seams, by identity)."""
    statements: list[str] = []
    for seam_name in _DRIVER_SEAMS:
        original = getattr(_txn, seam_name)

        def _recording(*args: Any, _original: Any = original, **kwargs: Any) -> Any:
            statements.append(str(kwargs.get("statement", args[0] if args else "")))
            return _original(*args, **kwargs)

        patch_shared_object_everywhere(
            monkeypatch, seam_name, original, _recording, expect_in=("loremaster.store._txn",)
        )
    return statements


_F5_SHAPES = {"minimal": True, "realistic": False}


class TestAnUndefinedTargetTableIsATypedAnswer63cIAa28c:
    def test_am34_4_the_preconditions_carry_the_defined_table_set(self) -> None:
        """⚠ RED at ``169925f``. amendment 34 §4: ``AgentMigrationPreconditions`` carries ``defined_tables``
        from the ONE ``INFO FOR DB`` read (the leg's check reads it, never a second probe)."""
        fields = {item.name for item in dataclasses.fields(principals.AgentMigrationPreconditions)}
        assert "defined_tables" in fields, fields

    @pytest.mark.parametrize("shape", sorted(_F5_SHAPES))
    @pytest.mark.parametrize("table", a28._LEG_TABLES)
    async def test_am34_4_an_undefined_target_answers_table_defined_False_after_ONE_probe(
        self, monkeypatch: pytest.MonkeyPatch, table: str, shape: str
    ) -> None:
        """⚠ RED at ``169925f`` (the leg raises ``TxnDomainRejectionError … governed scope count rejected`` on
        a legal ``--table`` — a raw driver teaching for a call that is not wrong). amendment 34 §4 (F-5),
        GENERATED over ``{agent, memory, message} × {minimal, realistic}``: the answer is TYPED
        (``table_defined is False``; ``scanned == 0``; ``backfilled == 0``; ``refused is False``), ``INFO FOR
        DB`` runs exactly ONCE, NO statement names the undefined table, and on the minimal store that one
        probe is the ONLY driver call (no operator resolution, no keep mint, no count)."""
        async with a19a._governed_world() as world:
            await a19a._seed_clean_single_principal_store(world)
            removed = {table} | ({AGENT_TABLE} if _F5_SHAPES[shape] else set())
            for gone in sorted(removed):
                await run(world.connection, f"REMOVE TABLE {gone}")
            statements = _spy_driver_statements(monkeypatch)
            result = await world.migrate(table)
        assert getattr(result, "table_defined", None) is False, (
            f"--table {table} on a {shape} store without `{table}`: amendment 34 §4 serves the typed "
            f"`table_defined=False` answer: {result!r}"
        )
        assert (result.scanned, result.backfilled, result.refused) == (0, 0, False), result
        probes = [
            statement for statement in statements if statement.strip().upper().startswith("INFO FOR DB")
        ]
        assert len(probes) == 1, f"INFO FOR DB must run exactly once: {statements}"
        naming = [
            statement
            for statement in statements
            if statement not in probes and re.search(rf"\b{table}\b", statement)
        ]
        assert not naming, f"statements named the undefined table `{table}`: {naming}"
        if _F5_SHAPES[shape]:
            assert statements == probes, (
                f"--table {table} on a store with neither `{table}` nor `agent`: the ONE INFO FOR DB is the "
                "only "
                f"store read (amendment 34 §4) — the run issued {statements}"
            )

    @pytest.mark.parametrize("name", a19a._invalid_table_names())
    async def test_am36_FK4_table_defined_is_None_when_INFO_FOR_DB_never_ran(self, name: str) -> None:
        """⚠ RED at ``169925f`` (no field). amendment 36 FK-4 (am-34's ``bool`` corrected to ``bool | None``):
        the invalid-``--table`` refusal reads NOTHING (a19a: zero store I/O), so its ``table_defined`` is
        ``None`` — an unread fact is never served as ``True`` / ``False``. GENERATED over a19a's derived
        invalid names (every emitted table outside the governed set, plus a typo)."""
        async with a19a._governed_world() as world:
            result = await world.migrate(name)
        assert result.refused is True, result
        assert hasattr(result, "table_defined") and result.table_defined is None, (
            f"--table {name!r} read nothing, yet served "
            f"table_defined={getattr(result, 'table_defined', '<absent>')!r}"
        )

    @pytest.mark.parametrize("defined", [False, True])
    async def test_am34_4_the_cli_render_derives_the_sentence_from_the_typed_field(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], defined: bool
    ) -> None:
        """⚠ RED at ``169925f`` (``MigrateGovernedResult`` has no ``table_defined``). amendment 34 §4: the
        render derives *"the `<table>` table is not defined in this store — nothing to migrate"* from the
        TYPED field, never from a count compare — driven through the CLI's own dispatcher with a forged result
        whose counts are IDENTICAL on both legs (``scanned == backfilled == 0``): only ``table_defined``
        differs, so a render keyed
        on the counts cannot tell them apart. Exit 0 on both (not a refusal)."""
        import argparse  # noqa: PLC0415 - scaffold-local

        # The ruled field is constructed through an ``Any`` alias: the STATIC reference that owns this file's
        # pending typecheck line is the ``TYPE_CHECKING`` block (one line per ruled symbol, #461's shape).
        result_class: Any = MigrateGovernedResult
        forged = result_class(
            table="memory",
            scanned=0,
            backfilled=0,
            already_migrated=0,
            refused=False,
            table_defined=defined,
        )

        class _Store:
            _url = "ws://unit"

            async def ensure_ready(self) -> None:
                return None

            async def close(self) -> None:
                return None

            async def _ensure_connection(self) -> None:
                return None

            async def _drop_connection(self, _connection: Any) -> None:
                return None

        async def _forged_migrate(**_kwargs: Any) -> Any:
            return forged

        monkeypatch.setattr(principals, "build_principal_store", lambda _config: _Store())
        monkeypatch.setattr(principals, "build_keep_store", lambda _config: _Store())
        monkeypatch.setattr(principals, "migrate_governed", _forged_migrate)
        code = await principals._dispatch_migrate_governed(
            argparse.Namespace(table="memory"), cast("Any", None)
        )
        out = capsys.readouterr()
        rendered = out.out + out.err
        stated = (
            "`memory` table is not defined in this store" in rendered and "nothing to migrate" in rendered
        )
        assert code == 0, (code, rendered)
        assert stated is (not defined), (
            f"table_defined={defined}: the render must state the undefined-table sentence iff the typed "
            "field is "
            f"False (amendment 34 §4 — derived from the field, never from the counts): {rendered!r}"
        )


# ======================================================================================================== #
# packet 58 amendment 8 §3 / FK-r3-4 (lead routing, 58 am-8 §3) — THIS module's slice of the discovered
# ``CAS_SEAM_DRIVERS`` registry (``test_reanchor_58_r3_cas_seam.discovered_drivers`` finds it by AST): one
# driver per 63c-owned LISTED handler (``test_retry_seam._GUARDED_CAS_DOORS`` / ``_TYPED_CAS_CATCHES``). Each
# driver has the 58 shape — the IDENTITY leg (exhausted contention injected at the driver seam while the verb
# is on the stack must reach the caller as the SAME instance) + a CONTROL leg (a REAL lost race served the
# ruled verdict, so the seam demonstrably can change the outcome). Keys are ``"<file>::<function>"`` (the
# frame key the injection understands).
# ======================================================================================================== #


async def _drive_agent_register(env: SurrealEnv, _ledger: Any, seam: DriverSeamInjection) -> None:
    registry = agents_module.AgentRegistry(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await registry.ensure_ready()
    try:
        seam.arm(
            "agents.py::register",
            seam="run_query",
            matches=lambda call: str(call.get("statement", "")).lstrip().startswith("CREATE"),
        )
        await seam.expect_the_SAME_instance(
            "agents.py::register", lambda: registry.register("casdrv63c", session="s-casdrv", role="builder")
        )
        # CONTROL: a REAL lost first-register race (K7's recipe) — the loser is served the re-register
        # verdict.
        real_query = registry._query
        fired = {"n": 0}

        async def winner_first(statement: str, params: Any = None) -> Any:
            if statement.lstrip().startswith("CREATE") and fired["n"] == 0:
                fired["n"] += 1
                await registry.register("casrace63c", session="s-casrace", role="builder")
            return await real_query(statement, params)

        registry._query = winner_first  # type: ignore[method-assign]
        try:
            raced = await registry.register("casrace63c", session="s-casrace", role="builder")
        finally:
            registry._query = real_query  # type: ignore[method-assign]
        assert fired["n"] == 1 and raced.re_registered is True, (fired, raced)
    finally:
        await registry.close()


async def _drive_keeps_get_or_create(env: SurrealEnv, _ledger: Any, seam: DriverSeamInjection) -> None:
    principal_store, keep_store = await build_principal_and_keep_stores(env)
    try:
        await principal_store.create(email="casdrv63c@example.com", role="admin")
        keeper = "casdrv63c@example.com"
        seam.arm("keeps.py::get_or_create_keyed", seam="execute_transaction")
        await seam.expect_the_SAME_instance(
            "keeps.py::get_or_create_keyed",
            lambda: keep_store.get_or_create_keyed(
                key="session:casdrv", type="session", keeper_email=keeper, name="d"
            ),
        )
        # CONTROL: a REAL lost CAS — the winner already holds the key, the loser's read saw it absent, its
        # CREATE collides on the UNIQUE key, and the loser is served the WINNER's keep.
        winner = await keep_store.get_or_create_keyed(
            key="session:casrace", type="session", keeper_email=keeper, name="w"
        )
        real_get = keep_store.get_by_key
        reads = {"n": 0}

        async def absent_once(key: str) -> Any:
            reads["n"] += 1
            return None if reads["n"] == 1 else await real_get(key)

        keep_store.get_by_key = absent_once
        try:
            loser = await keep_store.get_or_create_keyed(
                key="session:casrace", type="session", keeper_email=keeper, name="l"
            )
        finally:
            keep_store.get_by_key = real_get
        assert reads["n"] >= 2 and same_record(loser.id, winner.id), (reads, loser, winner)
    finally:
        await keep_store.close()
        await principal_store.close()


async def _drive_record_measurement(env: SurrealEnv, _ledger: Any, seam: DriverSeamInjection) -> None:
    import test_floor_calibration_store as floor_tests  # noqa: PLC0415 - scaffold-local (its fixtures, reused)

    floor = await floor_tests._new_floor_store(env)
    lease = await floor_tests._lease_store(env)
    try:
        observation = await lease.create_if_absent(
            holder_identity="pod-a", lease_duration="15", acquire_time="t", renew_time="t"
        )
        assert observation is not None
        fence = LeaseFence(holder_identity="pod-a", fence_epoch=observation.fence_epoch)
        seam.arm("floor_calibration/store.py::record_measurement", seam="execute_transaction")
        await seam.expect_the_SAME_instance(
            "floor_calibration/store.py::record_measurement",
            lambda: floor.record_measurement(
                axes=floor_tests.POOLED,
                measurement=floor_tests._measurement(state="measured"),
                adopt=True,
                fence=fence,
            ),
        )
        # CONTROL: a REAL lost fence (another pod seized) — the ruled verdict is FenceLostError.
        seized = await lease.compare_and_set(
            observed_revision=observation.revision,
            holder_identity="pod-b",
            lease_duration="15",
            acquire_time="t2",
            renew_time="t2",
        )
        assert seized is not None
        with pytest.raises(FenceLostError):
            await floor.record_measurement(
                axes=floor_tests.POOLED,
                measurement=floor_tests._measurement(state="measured"),
                adopt=True,
                fence=fence,
            )
    finally:
        await lease.close()
        await floor.close()


#: THIS module's slice of the discovered registry (58 FK-r3-4). Keys are ``"<file>::<function>"``.
CAS_SEAM_DRIVERS: dict[str, Any] = {
    "agents.py::register": _drive_agent_register,
    "keeps.py::get_or_create_keyed": _drive_keeps_get_or_create,
    "floor_calibration/store.py::record_measurement": _drive_record_measurement,
}


def _arm_the_driver_seams(monkeypatch: pytest.MonkeyPatch, seam: DriverSeamInjection) -> list[str]:
    """Wrap every binding of each driver seam (by identity, THE shared sweep) with 58's OWN injecting wrapper
    — the identity half of ``DriverSeamInjection.install`` WITHOUT its shell observer (the shell is packet
    58's unbuilt ``_guarded_append_fragment``; these three handlers never ride it)."""
    patched: list[str] = []
    for seam_name in DRIVER_SEAM_NAMES:
        original = getattr(_txn, seam_name)
        patched += patch_shared_object_everywhere(
            monkeypatch,
            seam_name,
            original,
            seam._seam_wrapper(seam_name, original),  # noqa: SLF001 - 58's own wrapper, reused (never copied)
            expect_in=("loremaster.store._txn",),
        )
    return patched


class TestThe63cCasHandlersPropagateExhaustionAsTheSameInstance63cIAa28c:
    def test_FK_r3_4_every_63c_listed_handler_has_a_driver_here(self) -> None:
        """⚠ RED until ``test_retry_seam``'s exact sets name these handlers (they do on a correct build).
        COMPLETENESS, both ways: this module drives exactly the listed handlers of the 63c-owned modules
        (agents, keeps, floor calibration) — a new 63c listed handler without a driver reds here by name."""
        import test_retry_seam as retry_seam  # noqa: PLC0415 - scaffold-local

        owned = ("agents.py", "keeps.py", "floor_calibration/")
        listed = {
            retry_seam._handler_function(key)  # noqa: SLF001
            for key in (*retry_seam._GUARDED_CAS_DOORS, *retry_seam._TYPED_CAS_CATCHES)  # noqa: SLF001
            if key.startswith(owned)
        }
        assert listed == set(CAS_SEAM_DRIVERS), (sorted(listed), sorted(CAS_SEAM_DRIVERS))

    @pytest.mark.parametrize("verb", sorted(CAS_SEAM_DRIVERS))
    async def test_FK_r3_4_the_injected_instance_reaches_the_caller_and_a_real_loss_is_the_ruled_verdict(
        self,
        ledger58: tuple[Any, SurrealEnv],  # noqa: F811
        monkeypatch: pytest.MonkeyPatch,
        verb: str,  # noqa: F811
    ) -> None:
        """GREEN on a correct build. At ``169925f`` the three IDENTITY legs are green (none of the three
        reinterprets exhausted contention) and ``agents.py::register``'s CONTROL leg is RED — the real race
        loser is served the raw engine rejection (RS-5 unbuilt: K7's reason). packet 58 amendment 8 §3 items
        1, 2, 4 for the three 63c-owned handlers: the injection fires under the armed verb, the SAME instance
        reaches the caller, and a REAL loss is the ruled verdict."""
        from test_reanchor_58_r3_cas_seam import DriverSeamInjection  # noqa: PLC0415 - see TYPE_CHECKING

        ledger, env = ledger58
        seam = DriverSeamInjection()
        patched = _arm_the_driver_seams(monkeypatch, seam)
        assert patched, "the driver seams were not wrapped"
        await CAS_SEAM_DRIVERS[verb](env, ledger, seam)
        assert verb in seam.flagged_stack, (
            f"{verb}: the injection fired under {seam.flagged_stack}, not under the verb it was armed for"
        )
