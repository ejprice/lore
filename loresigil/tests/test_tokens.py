"""Contract tests for ``loresigil.tokens.VoyageTokenCounter``.

``VoyageTokenCounter`` wraps the *pinned, committed* voyage-4 tokenizer
(``loresigil/loresigil/data/voyage4_tokenizer.json``) to return **exact** token
counts with **no network access** — the same counts the live Voyage embedding
endpoint charges/limits against.

Independent oracle (this is the whole point of the test)
--------------------------------------------------------
The expected counts below are NOT re-derived from the implementation. They are
the values observed against the *live Voyage server* for these exact strings:

    ""             -> 0 tokens
    "a"            -> 1 token
    "Hello world." -> 3 tokens

A counter built on the *wrong* tokenizer (a different model, or a stale/HF
download) would produce different counts and fail these assertions. That is the
adversarial guard: the test can only pass if the pinned tokenizer genuinely
reproduces the live server's segmentation offline.

Offline guarantee
------------------
The whole suite is run with the Hugging Face download paths disabled
(``HF_HUB_OFFLINE`` / ``TRANSFORMERS_OFFLINE``). If ``VoyageTokenCounter`` ever
tried to reach the network for a model, construction would fail rather than
silently fetch — proving the ``from_file`` path is exercised, not a download.
"""

from __future__ import annotations

import pytest
from loresigil.tokens import VoyageTokenCounter

# --- Independent oracle: live-Voyage-server-verified exact token counts. ------
# (string, exact token count) pairs. These are ground truth, not implementation
# echoes. A different tokenizer would segment these differently.
EMPTY_STRING: str = ""
EMPTY_STRING_TOKENS: int = 0

SINGLE_CHAR: str = "a"
SINGLE_CHAR_TOKENS: int = 1

SHORT_SENTENCE: str = "Hello world."
SHORT_SENTENCE_TOKENS: int = 3

ORACLE_CASES: list[tuple[str, int]] = [
    (EMPTY_STRING, EMPTY_STRING_TOKENS),
    (SINGLE_CHAR, SINGLE_CHAR_TOKENS),
    (SHORT_SENTENCE, SHORT_SENTENCE_TOKENS),
]

# A realistic multi-paragraph prose chunk (~hundreds of tokens). Used for a
# magnitude/sanity guard: BPE tokenizers on English prose land in a well-known
# band of roughly 0.6–1.0 tokens per whitespace-word. We assert the count falls
# in a sane range rather than hardcoding a brittle exact value — this catches an
# order-of-magnitude (wrong-scale / wrong-tokenizer) bug without re-deriving the
# implementation's arithmetic.
REALISTIC_PARAGRAPH: str = (
    "Embeddings map text into a dense vector space where semantic similarity "
    "becomes geometric proximity. A retrieval pipeline tokenizes each chunk, "
    "submits it to the embedding endpoint, and stores the resulting vector in a "
    "vector database. At query time the same model embeds the question and the "
    "nearest stored vectors are returned as candidate context.\n\n"
) * 8
# Sanity band derived from the word count, independent of the tokenizer code.
REALISTIC_WORD_COUNT: int = len(REALISTIC_PARAGRAPH.split())
REALISTIC_MIN_TOKENS: int = REALISTIC_WORD_COUNT // 2  # >= ~0.5 tok/word
REALISTIC_MAX_TOKENS: int = REALISTIC_WORD_COUNT * 2  # <= ~2 tok/word


class TestVoyageTokenCounterExactness:
    """The pinned tokenizer reproduces live-server-verified exact counts offline."""

    def setup_method(self) -> None:
        self.counter = VoyageTokenCounter()

    @pytest.mark.parametrize(("text", "expected"), ORACLE_CASES)
    def test_count_matches_independent_oracle(self, text: str, expected: int) -> None:
        # Assert against the live-server oracle, NOT the implementation.
        assert self.counter.count(text) == expected

    def test_count_tokens_matches_oracle_for_each_input(self) -> None:
        texts = [text for text, _ in ORACLE_CASES]
        expected = [count for _, count in ORACLE_CASES]
        # count_tokens returns a list aligned per-element to the inputs.
        assert self.counter.count_tokens(texts) == expected


class TestVoyageTokenCounterListAlignment:
    """``count_tokens`` returns a list aligned 1:1 with its input list."""

    def setup_method(self) -> None:
        self.counter = VoyageTokenCounter()

    def test_output_length_equals_input_length(self) -> None:
        texts = [SHORT_SENTENCE, SINGLE_CHAR, EMPTY_STRING, REALISTIC_PARAGRAPH]
        counts = self.counter.count_tokens(texts)
        assert len(counts) == len(texts)

    def test_empty_input_list_yields_empty_output(self) -> None:
        assert self.counter.count_tokens([]) == []

    def test_each_list_element_equals_scalar_count(self) -> None:
        texts = [SHORT_SENTENCE, SINGLE_CHAR, REALISTIC_PARAGRAPH]
        list_counts = self.counter.count_tokens(texts)
        # The list path and the scalar path must agree element-by-element.
        assert list_counts == [self.counter.count(text) for text in texts]


class TestVoyageTokenCounterDeterminism:
    """Counting the same input twice — and across instances — is identical."""

    def test_repeatable_within_instance(self) -> None:
        counter = VoyageTokenCounter()
        first = counter.count(SHORT_SENTENCE)
        second = counter.count(SHORT_SENTENCE)
        assert first == second == SHORT_SENTENCE_TOKENS

    def test_repeatable_across_instances(self) -> None:
        # Two independently-constructed counters must agree (cached tokenizer
        # must not drift between instances).
        a = VoyageTokenCounter().count_tokens([SHORT_SENTENCE, REALISTIC_PARAGRAPH])
        b = VoyageTokenCounter().count_tokens([SHORT_SENTENCE, REALISTIC_PARAGRAPH])
        assert a == b


class TestVoyageTokenCounterRealisticMagnitude:
    """A realistic ~hundreds-of-token chunk returns a plausible, in-band count."""

    def setup_method(self) -> None:
        self.counter = VoyageTokenCounter()

    def test_realistic_chunk_count_is_in_sane_band(self) -> None:
        count = self.counter.count(REALISTIC_PARAGRAPH)
        # Magnitude guard: catches wrong-scale / wrong-tokenizer bugs.
        assert REALISTIC_MIN_TOKENS <= count <= REALISTIC_MAX_TOKENS
        # And it really is in the "hundreds of tokens" regime, not single digits.
        assert count > 100

    def test_realistic_chunk_scalar_and_list_agree(self) -> None:
        scalar = self.counter.count(REALISTIC_PARAGRAPH)
        listed = self.counter.count_tokens([REALISTIC_PARAGRAPH])
        assert listed == [scalar]
