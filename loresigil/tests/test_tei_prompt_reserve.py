"""Contract tests for the TEI prompt-reserve fix — TDD Phase 1 (RED).

The bug: TEI applies ``prompt_name`` server-side and counts prompt+content against
the 8192-token cap, but ``TEIEmbedder`` sizes chunks to ``max_input_tokens`` (8192)
without reserving for the prompt.  A near-cap chunk plus the server-side prompt
pushes the combined token count over the cap, triggering a 422 that silently drops
the file.

Confirmed live overheads:
    ``prompt_name="document"`` → 6 extra tokens (8193 given for 8187-token content)
    ``prompt_name="query"``    → 8 extra tokens (8195 given for 8187-token content)

STRICT CAP (off-by-one): the server error says inputs must have **LESS THAN** 8192
tokens, so the limit is strict — a total of exactly 8192 is REJECTED (max accepted
total is 8191).  Confirmed by the live error ("Given: 8193" rejected for 8187 + 6).

Consequence for the reserve: the chunker sizes content with
``count(embedding_text) <= effective_cap``.  Worst case content == effective_cap,
plus the prompt (max_overhead).  For the server to ACCEPT it we need
``effective_cap + max_overhead < 8192`` (i.e. <= 8191).  With
``effective_cap = 8192 − reserve`` that requires ``reserve >= max_overhead + 1``.
So the reserve is ``max(overhead_per_prompt) + 1`` — the +1 absorbs the strict-"<"
boundary.  With document=6, query=8 → reserve = 8 + 1 = 9, and
``max_input_tokens = 8192 − 9 = 8183``.

The fix contract: ``TEIEmbedder.probe()`` MEASURES each configured prompt's overhead
by sending a near-cap sentinel with ``prompt_name`` and parsing the server's 422
``"... Given: N"`` response.  The reserve (``max(overhead_per_prompt) + 1``) is then
deducted from ``max_input_tokens`` so ``content + server-side_prompt < cap`` always
holds (strictly less than, never equal).

Module under test: ``loresigil.tei.TEIEmbedder`` (not yet implemented for this fix).
Mock pattern: offline ``httpx.MockTransport`` — same as the sibling ``test_tei.py``
suite.  The 422 error format used in the mocks is the REAL server wire format,
taken verbatim from the live production incident.
"""

from __future__ import annotations

import json

import httpx
import pytest
from loresigil.tei import TEIEmbedder
from loresigil.tokens import VoyageTokenCounter

# ── Shared constants ──────────────────────────────────────────────────────────

BASE_URL: str = "http://embedder.test:8080"
EMBED_ENDPOINT: str = "/embed"
API_KEY: str = "test-bearer-key-deadbeef"

# Verified model parameters — source of truth for the effective-budget arithmetic.
TEI_DIM: int = 2048
TEI_MAX_INPUT_TOKENS: int = 8192  # the hard server cap (configured value)

# Real server-observed prompt overheads (tokens the server counts beyond the
# client content) — values taken from the live production incident report.
# These are the EXPECTED values the tests pin; they are independent of the
# implementation formula.
DOCUMENT_PROMPT_NAME: str = "document"
QUERY_PROMPT_NAME: str = "query"
DOCUMENT_OVERHEAD_TOKENS: int = 6   # server-confirmed: document prompt = 6 tokens
QUERY_OVERHEAD_TOKENS: int = 8      # server-confirmed: query prompt = 8 tokens

# The strict-"<" boundary fudge.  The server rejects a total of EXACTLY 8192
# ("must have LESS THAN 8192 tokens"), so the reserve must be one token larger
# than the prompt overhead it covers: reserve = max_overhead + STRICT_CAP_GUARD.
# Without this +1, a chunk sized to the effective cap plus the max prompt would
# total exactly 8192 and be REJECTED — the off-by-one this fix guards against.
STRICT_CAP_GUARD: int = 1

# Reserve when only the document prompt is configured: 6 + 1 = 7.
EXPECTED_RESERVE_DOCUMENT_ONLY: int = DOCUMENT_OVERHEAD_TOKENS + STRICT_CAP_GUARD  # 7
# Reserve when only the query prompt is configured: 8 + 1 = 9.
EXPECTED_RESERVE_QUERY_ONLY: int = QUERY_OVERHEAD_TOKENS + STRICT_CAP_GUARD  # 9
# Reserve when both prompts are configured: max(6, 8) + 1 = 9.
EXPECTED_RESERVE_BOTH_PROMPTS: int = (
    max(DOCUMENT_OVERHEAD_TOKENS, QUERY_OVERHEAD_TOKENS) + STRICT_CAP_GUARD
)  # 9

# Shared tokenizer instance — same pinned voyage-4 tokenizer the production code
# uses; all token-count expectations in this file are derived from it.
_TOKEN_COUNTER = VoyageTokenCounter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_embedder(
    transport: httpx.MockTransport,
    *,
    document_prompt_name: str | None = None,
    query_prompt_name: str | None = None,
    max_input_tokens: int = TEI_MAX_INPUT_TOKENS,
) -> TEIEmbedder:
    """Construct a ``TEIEmbedder`` backed by an offline mock transport.

    Mirrors ``_make_embedder`` in ``test_tei.py`` but exposes prompt-name
    parameters for the reserve-measurement tests.
    """
    return TEIEmbedder(
        base_url=BASE_URL,
        endpoint=EMBED_ENDPOINT,
        api_key=API_KEY,
        dim=TEI_DIM,
        max_input_tokens=max_input_tokens,
        concurrency=2,
        transport=transport,
        document_prompt_name=document_prompt_name,
        query_prompt_name=query_prompt_name,
    )


def _build_probe_transport(
    *,
    document_overhead: int | None = None,
    query_overhead: int | None = None,
    dim: int = TEI_DIM,
) -> httpx.MockTransport:
    """Build a mock transport that simulates the TEI server's 422 behavior.

    For any request carrying ``prompt_name``:
      - Counts the tokens in ``inputs[0]`` using the SAME pinned tokenizer.
      - Looks up the simulated overhead for that prompt name.
      - Returns HTTP 422 with the REAL server error format:
        ``{"error":"Input validation error: `inputs` must have less than 8192
        tokens. Given: <C + overhead>","error_type":"Validation"}``

    For requests WITHOUT ``prompt_name`` (the dim-observation probe):
      - Returns a 200 with one ``dim``-dimensional zero vector.

    This design mirrors real server behavior: the server counts content tokens
    (which the client also counts, and they agree) then adds the prompt tokens.

    Args:
        document_overhead: Tokens to add when ``prompt_name="document"``.
        query_overhead:    Tokens to add when ``prompt_name="query"``.
        dim:               Vector dimension to return on successful no-prompt calls.
    """
    overhead_map: dict[str, int] = {}
    if document_overhead is not None:
        overhead_map[DOCUMENT_PROMPT_NAME] = document_overhead
    if query_overhead is not None:
        overhead_map[QUERY_PROMPT_NAME] = query_overhead

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        prompt_name: str | None = body.get("prompt_name")
        inputs: list[str] = body["inputs"]
        content_text = inputs[0] if inputs else ""

        if prompt_name is not None and prompt_name in overhead_map:
            # Server counts the content tokens, adds the prompt's token cost, then
            # reports the total in the 422 error.  Client and server use the same
            # tokenizer, so content_token_count is reliable as the base.
            content_token_count = _TOKEN_COUNTER.count(content_text)
            given_n = content_token_count + overhead_map[prompt_name]
            error_body = {
                "error": (
                    f"Input validation error: `inputs` must have less than 8192 tokens. "
                    f"Given: {given_n}"
                ),
                "error_type": "Validation",
            }
            return httpx.Response(422, json=error_body)

        # No prompt_name (or a prompt not in our map): successful embedding.
        vector = [0.0] * dim
        return httpx.Response(200, json=[vector])

    return httpx.MockTransport(handler)


# ── A1: Overhead measurement — document prompt → reserve 7 (overhead 6 + 1) ──

class TestProbeDocumentOverheadMeasurement:
    """A1: probe() sends the sentinel with prompt_name='document', parses the 422
    ``Given: N``, and records a reserve of 7 (overhead 6 + the strict-"<" guard of 1).

    Contract: after ``probe()`` completes, the document-prompt reserve accessible via
    the embedder is exactly ``EXPECTED_RESERVE_DOCUMENT_ONLY`` (6 + 1 = 7).
    The 422 format is the real server wire format; the mock derives ``N`` from the
    actual request content count so the test is not a tautology against a canned
    token count.
    """

    async def test_probe_measures_document_prompt_reserve(self) -> None:
        """After probe(), the document-prompt reserve is overhead 6 + guard 1 == 7."""
        transport = _build_probe_transport(document_overhead=DOCUMENT_OVERHEAD_TOKENS)
        embedder = _make_embedder(transport, document_prompt_name=DOCUMENT_PROMPT_NAME)

        await embedder.probe()

        # Reserve = measured overhead (6) + strict-cap guard (1) = 7.
        # The property name ``prompt_reserve`` is the new attribute the fix must add.
        assert embedder.prompt_reserve == EXPECTED_RESERVE_DOCUMENT_ONLY

    async def test_probe_document_only_reduces_budget_by_seven(self) -> None:
        """max_input_tokens drops to 8192 − 7 == 8185 with the document prompt only."""
        transport = _build_probe_transport(document_overhead=DOCUMENT_OVERHEAD_TOKENS)
        embedder = _make_embedder(transport, document_prompt_name=DOCUMENT_PROMPT_NAME)

        await embedder.probe()

        assert embedder.max_input_tokens == TEI_MAX_INPUT_TOKENS - EXPECTED_RESERVE_DOCUMENT_ONLY

    async def test_probe_parses_given_n_from_real_422_format(self) -> None:
        """The overhead is extracted from the exact real server error format.

        The real server produces:
          'Input validation error: `inputs` must have less than 8192 tokens. Given: N'
        Any other parse path (e.g. truncating at wrong position) yields a wrong
        overhead and a wrong effective budget.
        """
        # Use a deliberately different overhead to confirm parsing is not a
        # constant/hardcoded path.  Reserve must track it: 7 + strict guard 1 = 8.
        custom_overhead = 7
        expected_reserve = custom_overhead + STRICT_CAP_GUARD  # 8
        transport = _build_probe_transport(document_overhead=custom_overhead)
        embedder = _make_embedder(transport, document_prompt_name=DOCUMENT_PROMPT_NAME)

        await embedder.probe()

        assert embedder.prompt_reserve == expected_reserve


# ── A2: Reserve = max over configured prompts + strict-cap guard ─────────────

class TestProbeReserveMaxAcrossPrompts:
    """A2: With both document (overhead 6) and query (overhead 8) prompts configured,
    the reserve is 9 (max(6, 8) + 1), and ``max_input_tokens`` equals the configured
    cap minus the reserve.

    Contract:
        reserve = max(6, 8) + 1 = 9
        embedder.max_input_tokens == TEI_MAX_INPUT_TOKENS - 9 (== 8183)
    """

    async def test_reserve_is_max_overhead_plus_strict_guard(self) -> None:
        """probe() sets reserve to max overhead across prompts plus the +1 guard."""
        transport = _build_probe_transport(
            document_overhead=DOCUMENT_OVERHEAD_TOKENS,
            query_overhead=QUERY_OVERHEAD_TOKENS,
        )
        embedder = _make_embedder(
            transport,
            document_prompt_name=DOCUMENT_PROMPT_NAME,
            query_prompt_name=QUERY_PROMPT_NAME,
        )

        await embedder.probe()

        # Reserve is the larger overhead (8) plus the strict-cap guard (1) = 9.
        assert embedder.prompt_reserve == EXPECTED_RESERVE_BOTH_PROMPTS

    async def test_max_input_tokens_reduced_by_reserve_after_probe(self) -> None:
        """max_input_tokens reflects the effective per-chunk budget (8192 − 9 == 8183)."""
        transport = _build_probe_transport(
            document_overhead=DOCUMENT_OVERHEAD_TOKENS,
            query_overhead=QUERY_OVERHEAD_TOKENS,
        )
        embedder = _make_embedder(
            transport,
            document_prompt_name=DOCUMENT_PROMPT_NAME,
            query_prompt_name=QUERY_PROMPT_NAME,
        )

        # Before probe: max_input_tokens is the raw configured cap.
        assert embedder.max_input_tokens == TEI_MAX_INPUT_TOKENS

        await embedder.probe()

        # After probe: max_input_tokens is reduced by the reserve (== 8183).
        expected_effective_budget = TEI_MAX_INPUT_TOKENS - EXPECTED_RESERVE_BOTH_PROMPTS
        assert embedder.max_input_tokens == expected_effective_budget

    async def test_document_overhead_only_sets_reserve_of_seven(self) -> None:
        """When only the document prompt is configured, reserve is 6 + 1 == 7."""
        transport = _build_probe_transport(document_overhead=DOCUMENT_OVERHEAD_TOKENS)
        embedder = _make_embedder(transport, document_prompt_name=DOCUMENT_PROMPT_NAME)

        await embedder.probe()

        assert embedder.prompt_reserve == EXPECTED_RESERVE_DOCUMENT_ONLY  # 7
        assert embedder.max_input_tokens == TEI_MAX_INPUT_TOKENS - EXPECTED_RESERVE_DOCUMENT_ONLY

    async def test_query_overhead_only_sets_reserve_of_nine(self) -> None:
        """When only the query prompt is configured, reserve is 8 + 1 == 9."""
        transport = _build_probe_transport(query_overhead=QUERY_OVERHEAD_TOKENS)
        embedder = _make_embedder(transport, query_prompt_name=QUERY_PROMPT_NAME)

        await embedder.probe()

        assert embedder.prompt_reserve == EXPECTED_RESERVE_QUERY_ONLY  # 9
        assert embedder.max_input_tokens == TEI_MAX_INPUT_TOKENS - EXPECTED_RESERVE_QUERY_ONLY


# ── A3: No prompt configured → no reserve ────────────────────────────────────

class TestProbeNoPomptNoReserve:
    """A3: When neither prompt is configured, probe() sets no reserve and
    ``max_input_tokens`` is unchanged.

    Contract: reserve == 0, max_input_tokens == configured value (8192).
    No prompt is sent server-side, so there is nothing to reserve for — the
    strict-cap guard does NOT apply when there is no prompt overhead at all.
    """

    async def test_no_prompt_means_zero_reserve(self) -> None:
        """With no prompt names, probe() leaves the reserve at zero (no +1 guard)."""
        # No prompt overheads needed: the transport returns a successful 200 for
        # the plain (no-prompt) probe call.
        transport = _build_probe_transport()
        embedder = _make_embedder(transport)  # no document/query prompts

        assert embedder.prompt_reserve == 0

        await embedder.probe()

        assert embedder.prompt_reserve == 0

    async def test_no_prompt_max_input_tokens_unchanged_after_probe(self) -> None:
        """max_input_tokens stays at the configured cap when there are no prompts."""
        transport = _build_probe_transport()
        embedder = _make_embedder(transport)

        await embedder.probe()

        assert embedder.max_input_tokens == TEI_MAX_INPUT_TOKENS


# ── A4: Effective budget drives sizing — STRICT inequality ───────────────────

class TestEffectiveBudgetInvariant:
    """A4: The reduced ``max_input_tokens`` enforces that content + prompt < cap.

    This is a PURE ARITHMETIC invariant — no HTTP required.  After probe() has set
    the reserve, a chunk sized to the effective budget plus the full server-side
    prompt overhead must be STRICTLY LESS THAN the server cap (the server rejects a
    total of exactly 8192 — "must have LESS THAN 8192 tokens").

    Contract: effective_cap + max_overhead < TEI_MAX_INPUT_TOKENS
    (i.e. effective_cap + max_overhead <= 8191).  The boundary case
    effective_cap + max_overhead == 8192 is a FAILURE — the server rejects it.
    """

    async def test_reduced_plus_overhead_is_strictly_below_server_cap(self) -> None:
        """A chunk at the effective cap + the max prompt overhead is STRICTLY < 8192.

        This is the whole point of the +1 guard: with a plain
        reserve = max_overhead the total would equal 8192 and be REJECTED.
        """
        transport = _build_probe_transport(
            document_overhead=DOCUMENT_OVERHEAD_TOKENS,
            query_overhead=QUERY_OVERHEAD_TOKENS,
        )
        embedder = _make_embedder(
            transport,
            document_prompt_name=DOCUMENT_PROMPT_NAME,
            query_prompt_name=QUERY_PROMPT_NAME,
        )

        await embedder.probe()

        effective_cap = embedder.max_input_tokens
        max_overhead = max(DOCUMENT_OVERHEAD_TOKENS, QUERY_OVERHEAD_TOKENS)  # 8

        # STRICT inequality: a total of exactly 8192 is rejected by the server.
        assert effective_cap + max_overhead < TEI_MAX_INPUT_TOKENS

    async def test_plain_max_overhead_reserve_would_hit_the_rejected_boundary(self) -> None:
        """Guard the off-by-one: reserve = max_overhead (no +1) lands on the rejected 8192.

        This pins WHY the +1 is required.  With a naive reserve equal to just the
        max overhead, the worst-case chunk (effective_cap = 8192 − max_overhead)
        plus the prompt totals EXACTLY 8192 — which the server REJECTS ("less than
        8192").  The contract therefore demands reserve = max_overhead + 1 so the
        real ``embedder.max_input_tokens`` clears the boundary strictly.
        """
        max_overhead = max(DOCUMENT_OVERHEAD_TOKENS, QUERY_OVERHEAD_TOKENS)  # 8

        # The naive (buggy) effective cap if the reserve were just the overhead.
        naive_effective_cap = TEI_MAX_INPUT_TOKENS - max_overhead  # 8184
        # That naive sizing lands exactly on the rejected boundary.
        assert naive_effective_cap + max_overhead == TEI_MAX_INPUT_TOKENS  # 8192 == REJECTED

        # The corrected effective cap (with the +1 guard) clears it strictly.
        transport = _build_probe_transport(
            document_overhead=DOCUMENT_OVERHEAD_TOKENS,
            query_overhead=QUERY_OVERHEAD_TOKENS,
        )
        embedder = _make_embedder(
            transport,
            document_prompt_name=DOCUMENT_PROMPT_NAME,
            query_prompt_name=QUERY_PROMPT_NAME,
        )
        await embedder.probe()

        corrected_effective_cap = embedder.max_input_tokens  # expected 8183
        assert corrected_effective_cap < naive_effective_cap  # strictly tighter than naive
        assert corrected_effective_cap + max_overhead < TEI_MAX_INPUT_TOKENS  # accepted

    async def test_effective_budget_is_strictly_below_cap_when_prompts_present(self) -> None:
        """When prompts are configured, the effective budget is strictly below the cap.

        A budget equal to the cap (i.e. no reduction) would allow near-cap chunks
        to exceed the cap after the server adds the prompt — the exact bug.
        """
        transport = _build_probe_transport(document_overhead=DOCUMENT_OVERHEAD_TOKENS)
        embedder = _make_embedder(transport, document_prompt_name=DOCUMENT_PROMPT_NAME)

        await embedder.probe()

        # Must be strictly less than the server cap — equal means no reserve was applied.
        assert embedder.max_input_tokens < TEI_MAX_INPUT_TOKENS

    async def test_max_input_tokens_is_positive_after_probe(self) -> None:
        """The reduced budget is a sane positive integer (not zero or negative).

        Sanity-bound: the reserve (7–9 tokens) is tiny relative to the 8192-token
        cap; the effective budget should remain in the range [8000, 8191].
        """
        transport = _build_probe_transport(
            document_overhead=DOCUMENT_OVERHEAD_TOKENS,
            query_overhead=QUERY_OVERHEAD_TOKENS,
        )
        embedder = _make_embedder(
            transport,
            document_prompt_name=DOCUMENT_PROMPT_NAME,
            query_prompt_name=QUERY_PROMPT_NAME,
        )

        await embedder.probe()

        effective_budget = embedder.max_input_tokens
        # Lower bound: reserve is at most a few dozen tokens; budget stays large.
        assert effective_budget >= 8000
        # Upper bound: strictly below cap (reserve was actually applied).
        assert effective_budget < TEI_MAX_INPUT_TOKENS


# ── A5: probe() still returns the embedding dimension ────────────────────────

class TestProbeStillReturnsDim:
    """A5: Adding reserve measurement does NOT break the existing probe() contract —
    it still returns the observed embedding dimension.

    Contract: probe() returns an int equal to the model's ``dim`` (2048).
    """

    async def test_probe_returns_dim_with_document_prompt(self) -> None:
        """probe() returns the correct dim when a document prompt is configured."""
        transport = _build_probe_transport(document_overhead=DOCUMENT_OVERHEAD_TOKENS)
        embedder = _make_embedder(transport, document_prompt_name=DOCUMENT_PROMPT_NAME)

        observed_dim = await embedder.probe()

        assert observed_dim == TEI_DIM

    async def test_probe_returns_dim_with_both_prompts(self) -> None:
        """probe() returns the correct dim when both prompts are configured."""
        transport = _build_probe_transport(
            document_overhead=DOCUMENT_OVERHEAD_TOKENS,
            query_overhead=QUERY_OVERHEAD_TOKENS,
        )
        embedder = _make_embedder(
            transport,
            document_prompt_name=DOCUMENT_PROMPT_NAME,
            query_prompt_name=QUERY_PROMPT_NAME,
        )

        observed_dim = await embedder.probe()

        assert observed_dim == TEI_DIM

    async def test_probe_returns_dim_with_no_prompts(self) -> None:
        """probe() returns the correct dim when no prompts are configured."""
        transport = _build_probe_transport()
        embedder = _make_embedder(transport)

        observed_dim = await embedder.probe()

        assert observed_dim == TEI_DIM

    async def test_probe_dim_is_an_int(self) -> None:
        """probe() returns a plain int, not a list or float."""
        transport = _build_probe_transport(document_overhead=DOCUMENT_OVERHEAD_TOKENS)
        embedder = _make_embedder(transport, document_prompt_name=DOCUMENT_PROMPT_NAME)

        observed_dim = await embedder.probe()

        assert isinstance(observed_dim, int)


# ── A5 edge: probe() raises when the overhead 422 is malformed ───────────────

class TestProbeRaisesOnBadOverhead422:
    """probe() must raise (not silently set reserve=0) when it receives a 422 that
    does not carry the expected 'Given: N' format — a misconfigured or unexpected
    server error should surface as a startup failure, not a silent no-reserve.
    """

    async def test_probe_raises_on_422_without_given_n(self) -> None:
        """A 422 with an unexpected body format is a hard startup error."""
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content.decode())
            if body.get("prompt_name") is not None:
                # A 422 with a body that does NOT contain 'Given: N'
                return httpx.Response(422, json={"error": "some other server error"})
            return httpx.Response(200, json=[[0.0] * TEI_DIM])

        embedder = _make_embedder(
            httpx.MockTransport(handler),
            document_prompt_name=DOCUMENT_PROMPT_NAME,
        )

        with pytest.raises(Exception):
            await embedder.probe()

    async def test_probe_raises_on_unexpected_2xx_for_prompt_probe(self) -> None:
        """A 200 for a near-cap prompt probe is ambiguous — the reserve was not measured.

        The probe sends a near-cap sentinel precisely to force a 422 with the token
        count.  A 200 means the sentinel was within cap and the overhead is unknown.
        The embedder must treat this as an error and refuse to start without a
        measured reserve, rather than silently assuming reserve=0.
        """
        def handler(request: httpx.Request) -> httpx.Response:
            # Always return 200, even for prompt-name requests.
            return httpx.Response(200, json=[[0.0] * TEI_DIM])

        embedder = _make_embedder(
            httpx.MockTransport(handler),
            document_prompt_name=DOCUMENT_PROMPT_NAME,
        )

        # We pin: if the embedder cannot confirm the overhead, probe() must raise.
        with pytest.raises(Exception):
            await embedder.probe()


# ── A5 edge: prompt_reserve is zero before probe() runs ──────────────────────

class TestPromptReserveBeforeProbe:
    """Before ``probe()`` is called, ``prompt_reserve`` is 0 (no measurement yet).

    This is the contract for the pre-probe state — the reserve is explicitly zero,
    not undefined/unset.  The chunker must not be called before probe() runs.
    """

    def test_prompt_reserve_is_zero_before_probe(self) -> None:
        """prompt_reserve starts at 0 (no measurement yet)."""
        transport = _build_probe_transport(document_overhead=DOCUMENT_OVERHEAD_TOKENS)
        embedder = _make_embedder(transport, document_prompt_name=DOCUMENT_PROMPT_NAME)

        # No probe() called yet.
        assert embedder.prompt_reserve == 0

    def test_max_input_tokens_is_configured_cap_before_probe(self) -> None:
        """max_input_tokens returns the configured cap before probe() runs."""
        transport = _build_probe_transport(document_overhead=DOCUMENT_OVERHEAD_TOKENS)
        embedder = _make_embedder(transport, document_prompt_name=DOCUMENT_PROMPT_NAME)

        assert embedder.max_input_tokens == TEI_MAX_INPUT_TOKENS
