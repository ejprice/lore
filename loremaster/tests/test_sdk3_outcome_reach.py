"""Packet SDK3 contract, round 5 — R12 F18 (D1 reaches the ``SurrealStoreError`` family) and R12 F-b (a
server-ANSWERED error is a definite failure, never outcome-unknown).

``docs/plans/v2/sdk3-rulings.md`` R5 rider 2, R8 F14 (every SDK transport failure on a request is
``SurrealOutcomeUnknownError``), R9 D1 (no SERVED surface renders an unknown outcome as a definite failure),
R12 F18 (D1 reaches the 14 ``SurrealStoreError``-family catch sites; a pin wherever a site renders a definite
failure) and R12 F-b. Packet doc §ROUND 5 carries the per-site verdicts (14 family + 39 broad) these pins
come from.

Every behaviour pin here injects the ONE fault F14 defines — the write was SENT, no reply came — as a
commit-then-lose-the-reply wrapper: the real write runs to completion, and only then the call raises
``SurrealOutcomeUnknownError``. That is the exact state in which a "nothing committed" handler lies. Where a
pin also has a lost-before-commit leg, it is the control: it proves the pin can see the opposite outcome, so
the committed leg's verdict is not a build that always claims success.

* ``TestAnUnknownPublishNeverReleasesItsVersion`` — ``BriefLedger.publish``'s ``except SurrealStoreError``
  released the minted version on ANY store error ("nothing committed"); after a commit-then-unknown that
  re-mints the same version, whose CREATE then collides with the row that landed.
* ``TestAnUnknownIndexCommitIsNotServedAsFailed`` — the realtime (``index_file``) and batch (``index_all``
  two-pass) commits caught the same family and marked the file ``failed`` with the PRIOR chunk ids, which the
  landed commit had just purged.
* ``TestAnUnknownDriftFilingIsServedAsUnknown`` — the calibration probe served "drift finding filing failed"
  in ``status()`` / ``index_status`` for a filing whose write may have landed.
* ``TestAServerAnsweredErrorIsADefiniteFailure`` — F-b at the two seams (``run_query``,
  ``execute_transaction``): the server ANSWERED (an anonymous connection's write is refused with
  ``NotAllowedError``), so the outcome is KNOWN; an "unknown" here would teach agents to ignore the label.

The REACH half (every family catch site adjudicated, derived by THE ONE walker) lives beside D1's in
``test_sdk3_served_outcome.py``.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
import test_calibration_engine as calibration_suite
import test_indexer as indexer_suite
import test_indexer_bulk_sweep as bulk_suite
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.briefs import BriefLedger
from loremaster.index.surreal_manifest import STATE_FAILED, STATE_INDEXED
from loremaster.store import _txn
from loremaster.store._txn import SurrealConnectionError, SurrealStoreError, execute_transaction, run_query
from loresigil.testing import FakeEmbedder
from surrealdb import AsyncSurreal

logger = logging.getLogger(__name__)

# The reply-lost message the wrappers raise. Deliberately WITHOUT the words "unknown" / "failed", so a render
# that merely echoes the exception text cannot satisfy (or fail) a wording assertion by accident.
_REPLY_LOST = "SurrealDB transaction against 'ws://sdk3-r5' got no reply"

# A brief name that is NOT the ``project`` / ``base`` names every older brief fixture uses (monoculture law).
_BRIEF_NAME = "f18-handoff"
_BRIEF_BODY = "standing instruction for the F18 outcome-unknown publish pin, with real words"


def _unknown_type() -> type[SurrealConnectionError]:
    unknown = getattr(_txn, "SurrealOutcomeUnknownError", None)
    assert isinstance(unknown, type) and issubclass(unknown, SurrealConnectionError), (
        "store._txn.SurrealOutcomeUnknownError does not exist as a SurrealConnectionError subclass (R5 "
        "rider 2)"
    )
    return unknown


def _lose_the_reply(
    real: Callable[..., Awaitable[Any]], *, commit: bool, times: int = 1
) -> Callable[..., Awaitable[Any]]:
    """Wrap ``real`` so its next ``times`` calls raise ``SurrealOutcomeUnknownError`` — AFTER running ``real``
    to completion when ``commit`` (the write landed, the reply was lost), or without running it at all when
    not
    (the write never reached the store). Later calls pass straight through."""
    unknown = _unknown_type()
    remaining = [times]

    async def _wrapped(*args: Any, **kwargs: Any) -> Any:
        if remaining[0] <= 0:
            return await real(*args, **kwargs)
        remaining[0] -= 1
        if commit:
            await real(*args, **kwargs)
        raise unknown(_REPLY_LOST)

    return _wrapped


# ----------------------------------------------------------------------------------------------------
# briefs.BriefLedger.publish
# ----------------------------------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def brief_world() -> AsyncIterator[tuple[BriefLedger, Any]]:
    """A ready brief ledger on a fresh TEST-store database, plus an admin connection for oracle reads."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    admin = await connect_admin(env)
    ledger = BriefLedger(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    try:
        await ledger.ensure_ready()
        yield ledger, admin
    finally:
        await ledger.close()
        await admin.close()
        await drop_database(env)


async def _counter(admin: Any) -> Any:
    rows = await run(
        admin, "SELECT VALUE next FROM type::record('brief_counter', $name)", {"name": _BRIEF_NAME}
    )
    return rows[0] if rows else None


async def _versions(admin: Any) -> list[int]:
    return sorted(
        await run(admin, "SELECT VALUE version FROM brief WHERE name = $name", {"name": _BRIEF_NAME})
    )


class TestAnUnknownPublishNeverReleasesItsVersion:
    """F18 (R12, named in the ruling): a publish whose CREATE committed and whose reply was lost must not hand
    its version back. The error propagates as outcome-unknown (it is not re-labelled a definite failure), the
    counter still stands at the version that landed, and the NEXT publish of the name mints the next version
    and succeeds. A build that releases on an unknown outcome leaves the counter one behind the rows, so the
    next publish re-mints the landed version and its deterministic ``uuid5(name, version)`` CREATE collides.

    Control leg: a CREATE refused WITHOUT committing (a definite domain rejection) still releases — the next
    publish reuses version 1 — so the pin can see a release and is not passing on a build that never
    releases."""

    async def test_a_committed_publish_whose_reply_was_lost_keeps_its_version(
        self, brief_world: tuple[BriefLedger, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ledger, admin = brief_world
        unknown = _unknown_type()
        monkeypatch.setattr(ledger, "_apply", _lose_the_reply(ledger._apply, commit=True))
        with pytest.raises(SurrealStoreError) as caught:
            await ledger.publish(_BRIEF_NAME, _BRIEF_BODY, created_by="r5b")
        assert isinstance(caught.value, unknown), (
            f"a publish whose outcome is UNKNOWN surfaced as {type(caught.value).__name__}: D1 — it must "
            f"stay "
            f"outcome-unknown, never be re-labelled a definite failure"
        )
        assert await _versions(admin) == [1], "premise: the wrapped CREATE committed version 1"
        assert await _counter(admin) == 1, (
            f"the version counter reads {await _counter(admin)!r} after a publish that COMMITTED version 1: "
            f"the "
            f"handler released a version whose row landed (F18 — 'nothing committed' is false for an unknown "
            f"outcome)"
        )
        second = await ledger.publish(_BRIEF_NAME, _BRIEF_BODY, created_by="r5b")
        assert second.brief.version == 2 and await _versions(admin) == [1, 2], (
            f"the publish after an unknown-but-landed v1 got version {second.brief.version} "
            f"(rows {await _versions(admin)}): the counter was rolled back under a row that exists"
        )

    async def test_control_a_refused_create_still_releases_its_version(
        self, brief_world: tuple[BriefLedger, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ledger, admin = brief_world
        real = ledger._apply
        calls = [0]

        async def _refused_once(fragments: Any) -> None:
            calls[0] += 1
            if calls[0] == 1:
                raise _txn.TxnDomainRejectionError("refused (control)", kind="Thrown")
            await real(fragments)

        monkeypatch.setattr(ledger, "_apply", _refused_once)
        with pytest.raises(SurrealStoreError):
            await ledger.publish(_BRIEF_NAME, _BRIEF_BODY, created_by="r5b")
        assert await _versions(admin) == [] and await _counter(admin) == 0, (
            "control: a definitely-refused CREATE must hand its version back (the release this pin's other "
            "leg "
            "forbids for an UNKNOWN outcome)"
        )
        assert (await ledger.publish(_BRIEF_NAME, _BRIEF_BODY, created_by="r5b")).brief.version == 1


# ----------------------------------------------------------------------------------------------------
# index/indexer.py — _index_chunks (index_file) and _commit_batch_file (the two-pass batch sweep)
# ----------------------------------------------------------------------------------------------------

_EDITED_SUFFIX = "\n\ndef added_after_the_first_index(value: int) -> int:\n    return value * 3\n"


class TestAnUnknownIndexCommitIsNotServedAsFailed:
    """F18: a per-file commit whose reply was lost. Committed leg: the manifest must be the COMMITTED row
    (state
    ``indexed``, the new content hash, the NEW chunk ids) and the file must not be served ``failed``. A build
    that
    marks it failed with the PRIOR chunk ids points the manifest at chunks the landed commit just purged.

    Control leg (lost before the commit): the file must NOT be served ``indexed`` and the manifest must not
    claim the new chunks — a build that answers every unknown with "indexed" fails here."""

    @staticmethod
    async def _first_then_edited(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, commit: bool
    ) -> tuple[Any, Any, Any, list[str]]:
        root = tmp_path / "live"
        indexer_suite._build_live_corpus(root)
        config = indexer_suite._config(slug=unique_database(), live_path=root)
        trio = indexer_suite._trio()
        indexer = indexer_suite._make_indexer(
            config=config,
            trio=trio,
            embedder=FakeEmbedder(dim=indexer_suite._DIM),
            snapshot_root=tmp_path / "snap",
        )
        source = (root / "src" / "widget.py").read_text(encoding="utf-8")
        first = await indexer.index_file("custom", "src/widget.py", source)
        prior = await trio.manifest.get("custom", "src/widget.py")
        assert first.state == STATE_INDEXED and prior is not None and prior.chunk_ids, "premise: v1 indexed"
        monkeypatch.setattr(trio.store, "apply", _lose_the_reply(trio.store.apply, commit=commit))
        try:
            outcome: Any = await indexer.index_file("custom", "src/widget.py", source + _EDITED_SUFFIX)
        except SurrealConnectionError as error:
            outcome = error
        row = await trio.manifest.get("custom", "src/widget.py")
        return outcome, row, prior, list(prior.chunk_ids)

    async def test_a_committed_file_whose_reply_was_lost_keeps_the_committed_manifest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        outcome, row, prior, prior_ids = await self._first_then_edited(tmp_path, monkeypatch, commit=True)
        assert row is not None and row.state == STATE_INDEXED, (
            f"the manifest reads state {getattr(row, 'state', None)!r} after a commit that LANDED: an "
            f"unknown "
            f"outcome was recorded as a definite failure (F18/D1)"
        )
        assert row.sha512 != prior.sha512 and set(row.chunk_ids) - set(prior_ids), (
            f"the manifest points at the PRIOR content/chunk ids {prior_ids} after the edited file's commit "
            f"landed "
            f"(the edit's new chunk is missing from it; chunk ids are content-addressed, so the unchanged "
            f"chunks "
            f"legitimately keep theirs)"
        )
        assert not (getattr(outcome, "state", None) == STATE_FAILED), (
            f"index_file served {outcome!r} for a commit that landed — a definite failure for an unknown "
            f"outcome"
        )

    async def test_control_a_reply_lost_before_the_commit_is_not_served_indexed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        outcome, row, prior, prior_ids = await self._first_then_edited(tmp_path, monkeypatch, commit=False)
        assert getattr(outcome, "state", None) != STATE_INDEXED, (
            f"index_file served {outcome!r} for a write that never reached the store"
        )
        assert row is not None and not (row.state == STATE_INDEXED and row.sha512 != prior.sha512), (
            f"the manifest claims the EDITED content indexed ({row!r}) though its commit never happened"
        )

    async def test_the_batch_sweep_keeps_the_committed_manifest_too(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        live = tmp_path / "live"
        paths = bulk_suite._build_corpus(live, count=3)
        config = bulk_suite._config(slug=unique_database(), live_path=live, batch={"mode": "batch"})
        trio = bulk_suite._trio()
        embedder = bulk_suite.RecordingBatchFlatEmbedder(dim=bulk_suite._DIM, supports_batch=True)
        indexer = bulk_suite._make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )
        first = await indexer.index_all()
        assert first.files_indexed == len(paths) and embedder.batch_submit_calls, "premise: a batch sweep ran"
        edited = paths[0]
        prior = await trio.manifest.get("custom", edited)
        assert prior is not None and prior.chunk_ids
        (live / edited).write_text(
            (live / edited).read_text(encoding="utf-8") + _EDITED_SUFFIX, encoding="utf-8"
        )
        submits_before = len(embedder.batch_submit_calls)
        monkeypatch.setattr(trio.store, "apply", _lose_the_reply(trio.store.apply, commit=True))
        try:
            summary: Any = await indexer.index_all()
        except SurrealConnectionError as error:
            summary = error
        assert len(embedder.batch_submit_calls) > submits_before, (
            "premise: the edited file rode the batch commit"
        )
        row = await trio.manifest.get("custom", edited)
        assert row is not None and row.state == STATE_INDEXED and row.sha512 != prior.sha512, (
            f"the batch commit landed but the manifest reads {row!r}: an unknown outcome recorded as failed "
            f"(F18)"
        )
        assert set(row.chunk_ids) - set(prior.chunk_ids), (
            "the manifest kept the prior chunk ids (the edit's chunk is missing)"
        )
        assert getattr(summary, "files_failed", 0) == 0, (
            f"the sweep served {getattr(summary, 'files_failed', None)} failed file(s) for a commit that "
            f"landed"
        )


# ----------------------------------------------------------------------------------------------------
# calibration/engine.py::_file_drift_finding_deduped (a BROAD site whose served note is a definite failure)
# ----------------------------------------------------------------------------------------------------


class _UnknownFilingPort(calibration_suite._FakeFindingsPort):
    """A findings port whose drift filing raises outcome-unknown (the write was sent; no reply came)."""

    async def report_drift_finding(self, **kwargs: Any) -> None:
        raise _unknown_type()(_REPLY_LOST)


class TestAnUnknownDriftFilingIsServedAsUnknown:
    """F18, broad site: ``status()`` / ``index_status`` serve the calibration note. For a filing whose
    outcome is
    UNKNOWN the note must say so and tell the reader to verify — never "filing failed", which invites a manual
    re-file of a finding that may already exist. The plain-failure wording stays pinned by
    ``test_calibration_engine.py::TestFilingFailureObservability`` (the control: a definite failure still says
    "filing failed")."""

    async def test_the_note_names_the_outcome_unknown_not_failed(self, tmp_path: Path) -> None:
        counts = {calibration_suite._TEXT_A: 420, calibration_suite._TEXT_B: 630}  # +5% drift → a filing
        engine = calibration_suite._build_engine(
            tmp_path,
            counter_factory=calibration_suite._programmed_factory(counts),
            port=_UnknownFilingPort(),
        )
        await engine.start()
        try:
            await calibration_suite._wait_state(engine, "drift_adopted")
            note = str(engine.status()["note"] or "")
        finally:
            await engine.stop()
        lowered = note.lower()
        assert note, "the dropped-or-unknown filing must stay OBSERVABLE in status() (F1)"
        assert "failed" not in lowered, (
            f"the status note serves {note!r} for a filing whose write may have LANDED (D1/F18)"
        )
        assert "unknown" in lowered and "verify" in lowered, (
            f"the status note {note!r} must name the outcome as unknown and tell the reader to verify"
        )


# ----------------------------------------------------------------------------------------------------
# F-b — a server-ANSWERED error at the two seams
# ----------------------------------------------------------------------------------------------------


@pytest_asyncio.fixture()
async def anonymous_connection() -> AsyncIterator[tuple[SurrealEnv, Any]]:
    """A connection on a fresh TEST-store database that never signed in: every write is ANSWERED by the server
    with ``NotAllowedError`` (measured on SDK 2.0.0 and 3.0.0, 2026-11-07: "Anonymous access not allowed")."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    admin = await connect_admin(env)
    await admin.close()
    connection = AsyncSurreal(env.url)
    await connection.connect(env.url)
    await connection.use(env.namespace, env.database)
    try:
        yield env, connection
    finally:
        await connection.close()
        await drop_database(env)


class TestAServerAnsweredErrorIsADefiniteFailure:
    """R12 F-b: F14 covers TRANSPORT only. When the server answers — here a permission refusal of an anonymous
    write — the outcome is KNOWN (nothing was written), so the seam raises a store error that is NOT
    ``SurrealOutcomeUnknownError``. A build mapping every connection-classified error to "unknown" fails both
    legs."""

    @staticmethod
    def _assert_definite(error: BaseException, seam: str) -> None:
        unknown = _unknown_type()
        assert isinstance(error, SurrealStoreError), (
            f"{seam}: {type(error).__name__} escaped the store vocabulary"
        )
        assert not isinstance(error, unknown), (
            f"{seam}: a write the SERVER refused ({error}) was raised as outcome-unknown — F-b: an answered "
            f"error is "
            f"a definite failure"
        )

    async def test_the_single_statement_seam(self, anonymous_connection: tuple[SurrealEnv, Any]) -> None:
        env, connection = anonymous_connection

        async def _acquire() -> Any:
            return connection

        async def _drop(_connection: Any) -> None:
            return None

        with pytest.raises(SurrealStoreError) as caught:
            await run_query(
                acquire=_acquire,
                drop=_drop,
                url=env.url,
                noun="sdk3 F-b probe",
                label="sdk3.fb.rejected",
                statement="CREATE fb_probe:one SET n = 1",
                params={},
                logger=logger,
            )
        self._assert_definite(caught.value, "run_query")

    async def test_the_transaction_seam(self, anonymous_connection: tuple[SurrealEnv, Any]) -> None:
        env, connection = anonymous_connection

        async def _acquire() -> Any:
            return connection

        async def _drop(_connection: Any) -> None:
            return None

        with pytest.raises(SurrealStoreError) as caught:
            await execute_transaction(
                "BEGIN;\nCREATE fb_probe:two SET n = 2;\nCOMMIT;",
                {},
                acquire=_acquire,
                drop=_drop,
                url=env.url,
            )
        self._assert_definite(caught.value, "execute_transaction")
