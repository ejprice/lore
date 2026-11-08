"""Packet SDK3 contract, round 8 — MP-1 (adversary round 3; R28/R29): a per-file fault's SERVED reason is the
same in BOTH sweep shapes.

R4 rider (3) + R17: a file the index refuses must be NAMED on a served surface WITH the bound that refused
it —
``index_status`` serves ``index.failed_reason:<tier>:<path>``. ``test_sdk3_index_batching::
TestARefusedFileIsNamedOnTheServedStatus`` (B3) drives only the REALTIME sweep, and adversary round 3 built
``b3_no_bound_batch``: the batch-sweep arm (``Indexer._commit_batch_file``) serving the reason with no bound
passed every pin. Under a batch-capable embedder (the shipped voyage backends; ``auto`` above the chunk
threshold) an agent told "failed" with no bound cannot tell "split the file" from "retry".

CLASS (the adversary's, a repeat of round 2's MP-A): *a per-file fault's served fate AND reason are decided
identically in both sweep shapes.* The two legs below reach the two distinct production arms — a PREMISE
assertion per leg proves which arm embedded the file — so a build that diverges in either arm reddens exactly
that leg. Same parametrisation, same breath: the embed-failure sibling (``_FAILED_EMBED_REASON``; RULING-7 §4
rider). Store-free (the fake Surreal trio): what is pinned is the indexer's served reason, not the engine.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import pytest
import test_indexer_bulk_sweep as bulk_suite
from loremaster.index.manifest import STATE_FAILED
from loremaster.store import _txn

#: A row cap no default produces, so its appearance in the served reason IS the bound being named.
_SHRUNK_ROW_CAP = 1009
_TIER = "custom"
#: The served embed-failure reason (``indexer._FAILED_EMBED_REASON``), spelled as the agent reads it.
_EMBED_FAILED_REASON = "embed_failed_or_non_finite"
_SWEEP_SHAPES = ["batch", "realtime"]


def _refuse_one_commit_at_the_row_cap(
    real_apply: Callable[..., Awaitable[Any]],
) -> Callable[..., Awaitable[Any]]:
    """``store.apply`` that refuses its FIRST per-file commit the way ``compose`` does over the row cap."""
    remaining = [1]

    async def _apply(*args: Any, **kwargs: Any) -> Any:
        if remaining[0] <= 0:
            return await real_apply(*args, **kwargs)
        remaining[0] -= 1
        raise _txn.TxnRowCapExceededError(
            f"composed transaction writes 4242 rows, over the {_SHRUNK_ROW_CAP}-row cap per transaction — "
            f"refused before anything was sent to the server"
        )

    return _apply


def _assert_the_leg_reached_its_arm(embedder: Any, mode: str) -> None:
    """The premise RULING-7 §4 keeps: each leg reaches a DIFFERENT production arm."""
    if mode == "batch":
        assert embedder.batch_submit_calls and not embedder.realtime_calls, (
            f"premise: the batch leg must embed through the batch job (submits "
            f"{len(embedder.batch_submit_calls)}, realtime calls {len(embedder.realtime_calls)}) — otherwise "
            f"it does not reach _commit_batch_file"
        )
    else:
        assert embedder.realtime_calls and not embedder.batch_submit_calls, (
            f"premise: the realtime leg must embed inline (realtime calls {len(embedder.realtime_calls)}, "
            f"submits {len(embedder.batch_submit_calls)}) — otherwise it does not reach _index_chunks"
        )


async def _served_reasons(trio: Any, paths: list[str]) -> dict[str, str]:
    reasons = {path: await trio.manifest.meta_get(f"index.failed_reason:{_TIER}:{path}") for path in paths}
    return {path: reason for path, reason in reasons.items() if reason}


class TestARefusedFileNamesItsBoundInEitherSweepShape:
    """MP-1: one per-file commit refused at the row cap ⇒ that file, and only it, is served FAILED with a
    reason naming the cap — whichever sweep shape indexed it."""

    @pytest.mark.parametrize("mode", _SWEEP_SHAPES)
    async def test_the_refused_files_served_reason_names_the_row_cap(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
    ) -> None:
        live = tmp_path / "live"
        paths = bulk_suite._build_corpus(live, count=3)
        config = bulk_suite._config(slug=bulk_suite._slug(), live_path=live, batch={"mode": mode})
        trio = bulk_suite._trio()
        embedder = bulk_suite.RecordingBatchFlatEmbedder(dim=bulk_suite._DIM, supports_batch=True)
        indexer = bulk_suite._make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )
        monkeypatch.setattr(trio.store, "apply", _refuse_one_commit_at_the_row_cap(trio.store.apply))

        summary = await indexer.index_all()

        _assert_the_leg_reached_its_arm(embedder, mode)
        assert summary.files_failed == 1 and summary.files_indexed == len(paths) - 1, (
            f"{mode}: premise — exactly one file refused, its siblings indexed ({summary!r})"
        )
        refused = await _served_reasons(trio, paths)
        assert len(refused) == 1, f"{mode}: exactly one file carries a served failure reason: {refused!r}"
        ((path, reason),) = refused.items()
        row = await trio.manifest.get(_TIER, path)
        assert row is not None and row.state == STATE_FAILED, f"{mode}: the refused file is not served failed"
        assert str(_SHRUNK_ROW_CAP) in reason, (
            f"{mode}: the refused file {path!r} is served as {reason!r}, which does not name the row cap "
            f"({_SHRUNK_ROW_CAP}) that refused it — the agent cannot tell 'split the file' from 'retry' "
            f"(R4 rider 3)"
        )


class TestAnEmbedFailureIsServedTheSameInEitherSweepShape:
    """RULING-7 §4 rider (the adversary's untried sibling): an embedder that cannot embed one file's chunks ⇒
    that file is served FAILED with the embed-failure reason, in both sweep shapes."""

    @pytest.mark.parametrize("mode", _SWEEP_SHAPES)
    async def test_the_unembeddable_files_served_reason_is_the_embed_failure(
        self, tmp_path: Path, mode: str
    ) -> None:
        live = tmp_path / "live"
        paths = bulk_suite._build_corpus(live, count=3)
        config = bulk_suite._config(slug=bulk_suite._slug(), live_path=live, batch={"mode": mode})
        trio = bulk_suite._trio()
        failing_source = (live / paths[1]).read_text(encoding="utf-8")
        failing_texts = set(bulk_suite._probe_texts(config, _TIER, paths[1], failing_source))
        embedder = bulk_suite.RecordingBatchFlatEmbedder(
            dim=bulk_suite._DIM, supports_batch=True, fail_inputs=failing_texts
        )
        indexer = bulk_suite._make_indexer(
            config=config, trio=trio, embedder=embedder, snapshot_root=tmp_path / "snap"
        )

        await indexer.index_all()

        _assert_the_leg_reached_its_arm(embedder, mode)
        refused = await _served_reasons(trio, paths)
        assert refused == {paths[1]: _EMBED_FAILED_REASON}, (
            f"{mode}: the unembeddable file must be the only one served failed, with reason "
            f"{_EMBED_FAILED_REASON!r}; served {refused!r}"
        )
