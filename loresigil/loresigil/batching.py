"""Token-aware request batching and a bounded windowed-concurrency runner.

Two collaborators every embedder shares:

* :func:`build_batches` packs input *indices* into per-request batches that respect
  **both** the TEI per-request text cap (``max_client_batch_size`` = 32) **and** a
  per-request token budget. A batch is closed as soon as adding the next input
  would breach *either* limit. A single input whose own token cost exceeds the
  budget is still emitted as its own lone batch — never dropped and never merged —
  because clamping over-length inputs is the embedder's 422 backstop, not
  batching's job. The function returns lists of *indices* (positions into the
  original ``token_counts``) so the caller can map them back to the source texts;
  every index appears exactly once, in input order.

* :func:`run_in_windows` runs an async ``worker`` over a list of items with a
  bounded in-flight pool (default 2 — the measured throughput optimum for the TEI
  box; a pool of 4 regressed, and approaching the server's 64-concurrency guard
  risks 429s). Results come back positionally aligned to the inputs.

Adapted from the odoo-code donor's ``build_batches`` / windowed gather, but
re-shaped to be free of any module-global tokenizer or client: token counts are
passed in, and the worker is injected.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

# TEI ``max_client_batch_size`` — over this, the server returns HTTP 413.
MAX_BATCH_TEXTS: int = 32

# Measured optimum in-flight pool size for the TEI endpoint (2 = 1.10x vs 1;
# 4 regressed to 0.98x; the server's DOS guard is 64, never to be approached).
DEFAULT_CONCURRENCY: int = 2


def build_batches(
    token_counts: list[int],
    max_tokens: int,
    max_texts: int = MAX_BATCH_TEXTS,
) -> list[list[int]]:
    """Pack input indices into batches bounded by both a text count and a token budget.

    Args:
        token_counts: Per-input token counts, in input order.
        max_tokens: Maximum summed token cost allowed in one batch.
        max_texts: Maximum number of inputs allowed in one batch.

    Returns:
        A list of batches, each a list of indices into ``token_counts``. Indices
        form an in-order partition of ``range(len(token_counts))`` — every input
        appears exactly once. An input whose own cost exceeds ``max_tokens`` is
        emitted as its own lone batch.
    """
    batches: list[list[int]] = []
    current_batch: list[int] = []
    current_tokens = 0
    for index, count in enumerate(token_counts):
        # Close the current batch if appending this input would breach EITHER cap.
        # The current_batch guard ensures a lone over-budget input is still placed
        # (it gets a batch of its own rather than being dropped).
        would_exceed_tokens = current_tokens + count > max_tokens
        would_exceed_texts = len(current_batch) >= max_texts
        if current_batch and (would_exceed_tokens or would_exceed_texts):
            batches.append(current_batch)
            current_batch = []
            current_tokens = 0
        current_batch.append(index)
        current_tokens += count
    if current_batch:
        batches.append(current_batch)
    return batches


async def run_in_windows[T, R](
    items: list[T],
    worker: Callable[[T], Awaitable[R]],
    concurrency: int = DEFAULT_CONCURRENCY,
) -> list[R]:
    """Run ``worker`` over ``items`` with at most ``concurrency`` in flight at once.

    Args:
        items: The work items, processed in order across windows.
        worker: An async callable applied to each item.
        concurrency: Maximum number of concurrent in-flight workers.

    Returns:
        The worker results, positionally aligned to ``items``.
    """
    results: list[R] = []
    # Process in fixed windows of ``concurrency`` so peak in-flight never exceeds
    # the bound (a plain gather over all items would peak at len(items)).
    for window_start in range(0, len(items), concurrency):
        window = items[window_start : window_start + concurrency]
        window_results = await asyncio.gather(*(worker(item) for item in window))
        results.extend(window_results)
    return results
