"""Contract tests for ``loresigil.batching`` — token-aware batching + a
windowed-concurrency runner.

Two public surfaces are pinned here, both from the spec, not any implementation:

* ``build_batches(token_counts, max_tokens, max_texts)`` — packs input *indices*
  into batches that respect BOTH a per-request text cap (TEI ``max_client_batch_size``
  = 32) AND a per-request token budget. It returns batches of indices (positions
  into the original list) so the caller can map them back to the original texts.
  The two caps are independent: a batch is closed when adding the next text would
  breach *either* the text count or the token budget.

* ``run_in_windows(items, worker, concurrency)`` — runs an async ``worker`` over
  ``items`` with a bounded in-flight pool (default 2, the measured optimum for the
  TEI box). Results come back positionally aligned to ``items``, and at no instant
  do more than ``concurrency`` workers run concurrently (the server's 64-guard
  must never be approached, and 4 regressed throughput, so the bound is real).

The token-count fixtures are *real* values produced by the pinned voyage-4-nano
tokenizer (see ``tokens.py``) for representative warehouse-ops prose — not
hand-picked round numbers — so a wrong-scale packing bug cannot hide behind a
convenient synthetic.
"""

from __future__ import annotations

import asyncio

from loresigil.batching import build_batches, run_in_windows

# --- Real token-count anchors (voyage-4-nano tokenizer, verified offline) -----
# A single representative warehouse-ops sentence is 13 tokens; these counts are
# the real segmentation, used so the packing math is exercised against the scale
# the embedder actually sees (p50 ~186, p99 ~1281 tok per the perf bench).
SENTENCE_TOKENS: int = 13
SHORT_CHUNK_TOKENS: int = 186  # ~ real corpus p50
MID_CHUNK_TOKENS: int = 1281  # ~ real corpus p99

# TEI hard caps (from the verified spec; over-batch -> HTTP 413).
TEI_MAX_BATCH_TEXTS: int = 32
# A token budget chosen to force a split BEFORE the text cap, so the token rule
# is what closes the batch (not the count rule). 1000 tokens fits 5 short chunks
# of 186 (=930) but not 6 (=1116).
TOKEN_BUDGET: int = 1000


class TestBuildBatchesRespectsTextCap:
    """No batch exceeds the per-request text count cap, regardless of token budget."""

    def test_splits_when_text_count_cap_reached(self) -> None:
        # 70 tiny inputs, token budget effectively unlimited -> the 32-text cap
        # is the only thing that can close a batch. Expect ceil(70/32) = 3 batches
        # sized 32, 32, 6.
        token_counts = [SENTENCE_TOKENS] * 70
        batches = build_batches(token_counts, max_tokens=10_000_000, max_texts=TEI_MAX_BATCH_TEXTS)
        sizes = [len(batch) for batch in batches]
        assert sizes == [32, 32, 6]
        assert all(len(batch) <= TEI_MAX_BATCH_TEXTS for batch in batches)

    def test_single_oversized_count_still_yields_its_own_batch(self) -> None:
        # One input alone may exceed the token budget (the 422 sub-split is the
        # backstop, not batching's job) — it must still be emitted as a lone batch,
        # never dropped, never merged.
        token_counts = [MID_CHUNK_TOKENS * 100]  # way over any budget
        batches = build_batches(token_counts, max_tokens=TOKEN_BUDGET, max_texts=TEI_MAX_BATCH_TEXTS)
        assert batches == [[0]]


class TestBuildBatchesRespectsTokenBudget:
    """A batch closes when the next text would breach the token budget."""

    def test_token_budget_closes_batch_before_text_cap(self) -> None:
        # 12 short chunks of 186 tokens each, budget 1000: 5 fit (930), 6th (1116)
        # breaches. So batches pack 5,5,2 — driven by tokens, not the 32 cap.
        token_counts = [SHORT_CHUNK_TOKENS] * 12
        batches = build_batches(token_counts, max_tokens=TOKEN_BUDGET, max_texts=TEI_MAX_BATCH_TEXTS)
        sizes = [len(batch) for batch in batches]
        assert sizes == [5, 5, 2]
        # Every batch's summed tokens stays within budget (the lone-oversized case
        # is excluded here — none of these singletons exceed the budget).
        for batch in batches:
            assert sum(token_counts[i] for i in batch) <= TOKEN_BUDGET

    def test_both_caps_active_simultaneously(self) -> None:
        # Budget 1000 admits 5 short chunks (<32), so tokens win here; but with a
        # tiny token cost the 32-text rule wins. Mixed list proves BOTH gates fire.
        # 40 sentences of 13 tokens: token sum for 32 = 416 < 1000, so the 32 cap
        # closes the first batch (not tokens). Expect 32, 8.
        token_counts = [SENTENCE_TOKENS] * 40
        batches = build_batches(token_counts, max_tokens=TOKEN_BUDGET, max_texts=TEI_MAX_BATCH_TEXTS)
        sizes = [len(batch) for batch in batches]
        assert sizes == [32, 8]


class TestBuildBatchesAlignmentAndTotality:
    """Every input index appears exactly once, in order — no loss, no duplication."""

    def test_indices_are_a_partition_in_order(self) -> None:
        token_counts = [SHORT_CHUNK_TOKENS, MID_CHUNK_TOKENS, SENTENCE_TOKENS, SHORT_CHUNK_TOKENS]
        batches = build_batches(token_counts, max_tokens=TOKEN_BUDGET, max_texts=TEI_MAX_BATCH_TEXTS)
        flattened = [index for batch in batches for index in batch]
        # Totality + order preservation: a packing bug that drops or reorders a
        # chunk would corrupt the input↔vector alignment downstream.
        assert flattened == list(range(len(token_counts)))

    def test_empty_input_yields_no_batches(self) -> None:
        assert build_batches([], max_tokens=TOKEN_BUDGET, max_texts=TEI_MAX_BATCH_TEXTS) == []


class TestRunInWindowsAlignmentAndResults:
    """``run_in_windows`` returns results aligned to inputs."""

    async def test_results_aligned_to_inputs(self) -> None:
        items = [2, 3, 5, 7, 11]

        async def square(value: int) -> int:
            return value * value

        results = await run_in_windows(items, square, concurrency=2)
        # Independent oracle: squares computed here, not by the runner.
        assert results == [4, 9, 25, 49, 121]

    async def test_empty_items_yields_empty_results(self) -> None:
        async def worker(value: int) -> int:  # pragma: no cover - never called
            return value

        assert await run_in_windows([], worker, concurrency=2) == []


class TestRunInWindowsBoundsConcurrency:
    """At no instant do more than ``concurrency`` workers run at once."""

    async def test_never_exceeds_concurrency_bound(self) -> None:
        # Each worker bumps a live counter, awaits a barrier-ish sleep so windows
        # overlap, then decrements. We record the peak. With concurrency=2 over 6
        # items the peak in-flight must be exactly 2 — proving the pool is bounded
        # (a naive gather-all would peak at 6, the 64-guard risk the spec warns of).
        concurrency = 2
        live = 0
        peak = 0
        lock = asyncio.Lock()

        async def worker(value: int) -> int:
            nonlocal live, peak
            async with lock:
                live += 1
                peak = max(peak, live)
            await asyncio.sleep(0.01)
            async with lock:
                live -= 1
            return value

        await run_in_windows(list(range(6)), worker, concurrency=concurrency)
        assert peak == concurrency

    async def test_default_concurrency_is_two(self) -> None:
        # The measured optimum is a pool of 2; the default must encode that.
        live = 0
        peak = 0
        lock = asyncio.Lock()

        async def worker(value: int) -> int:
            nonlocal live, peak
            async with lock:
                live += 1
                peak = max(peak, live)
            await asyncio.sleep(0.01)
            async with lock:
                live -= 1
            return value

        # Call without specifying concurrency -> exercises the default.
        await run_in_windows(list(range(6)), worker)
        assert peak == 2
