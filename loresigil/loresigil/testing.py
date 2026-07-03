"""Shipped, deterministic test double for :class:`~loresigil.base.Embedder`.

:class:`FakeEmbedder` is **production code** — it ships in the loresigil wheel so
that downstream packages (``loremaster``, and loresigil's own tests) can exercise
embedding-dependent logic without network access, API keys, or non-determinism.

It satisfies the full :class:`~loresigil.base.Embedder` contract:

* Vectors are derived deterministically from a stable hash of the input text, so
  the same text always yields the same vector — within a process and across
  separately-constructed instances.
* When ``normalized`` is set (the default) every vector is L2-normalized to unit
  length, matching a real normalized embedder so cosine similarity equals the dot
  product downstream.
* Failure is injectable: any text in ``fail_inputs`` comes back as ``None`` at its
  position in :meth:`embed_documents`, simulating a permanently-failed input; and
  ``probe_fails`` makes :meth:`probe` raise, simulating an unreachable endpoint.
* Token counting uses a cheap, dependency-light ``len // 4`` heuristic by default
  (so the double stays fast and import-light); pass ``use_exact_tokenizer=True`` to
  delegate to the exact :class:`~loresigil.tokens.VoyageTokenCounter`.
* Usage is deterministic and ALWAYS reported (never ``None``): the offline fake
  can measure exactly what it "billed" via its own public :meth:`count_tokens`,
  so it always does — a fail_inputs text (or a would-be quarantined vector in a
  real backend) still counts toward the bill, matching "billed" != "succeeded".

The asynchronous Batch API seam (2026-07-03) is an OPTIONAL, offline double of
the real Voyage Files/Batches lifecycle (see :mod:`loresigil.voyage_batch`):
``supports_batch=True`` enables ``submit_batch_documents`` /
``submit_batch_document_chunks`` (validated identically to the real backends via
:func:`~loresigil.voyage_batch.encode_batch_jsonl`), plus ``get_batch_status`` /
``await_batch_completion`` / ``fetch_batch_results``. Batch vectors are computed
through the SAME realtime paths (:meth:`embed_documents` /
:meth:`embed_document_chunks`), so batch/realtime parity holds by construction.
Submitted jobs live in an injectable ``batch_jobs`` mapping (private per instance
by default) that stands in for the real Voyage account — a brand-new instance
sharing that mapping can resume a job it never submitted itself.
"""

from __future__ import annotations

import hashlib
import math
import struct
import uuid
from collections.abc import Set
from typing import Any

from loresigil.base import Embedder, EmbedResult, EmbedUsage
from loresigil.resilient import SleepFn
from loresigil.tokens import VoyageTokenCounter
from loresigil.voyage_batch import (
    DEFAULT_POLL_INTERVAL_S,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_IN_PROGRESS,
    TERMINAL_BATCH_STATUSES,
    BatchJobFailedError,
    encode_batch_jsonl,
    poll_until_terminal,
)

# Default model parameters mirror the small-model shape used across the project.
_DEFAULT_DIM: int = 8
_DEFAULT_MAX_INPUT_TOKENS: int = 8192
_DEFAULT_NAME: str = "fake-embedder"

# Approximate characters-per-token for the cheap heuristic token counter. A
# faithful behavioural stand-in for a BPE tokenizer on prose (~4 chars/token).
_CHARS_PER_TOKEN: int = 4

# Number of bytes consumed from the hash digest per vector component (float64).
_BYTES_PER_COMPONENT: int = 8

# Delimiter folded into the hash input for a contextualized chunk (doc chunks
# joined + chunk index + chunk text). A control character is vanishingly
# unlikely to appear in real prose, so it cannot collide with chunk content.
_DOC_CONTEXT_SEPARATOR: str = "\x00"

# Batch-double defaults. A job reaches a terminal status on its FIRST poll by
# default (so the common happy path never sleeps); a test raises this to hold a
# job ``in_progress`` for a configured number of polls.
_DEFAULT_BATCH_POLLS_BEFORE_TERMINAL: int = 1
# Prefix for the offline fake's job ids (json-serializable, unique per submit).
_FAKE_BATCH_JOB_PREFIX: str = "fake-batch-"
# The two batch-line shapes the fake records, mirroring the two real backends.
_BATCH_KIND_FLAT: str = "flat"
_BATCH_KIND_GROUPED: str = "grouped"


class FakeEmbedder(Embedder):
    """Deterministic, offline :class:`Embedder` for tests and downstream fixtures."""

    def __init__(
        self,
        dim: int = _DEFAULT_DIM,
        max_input_tokens: int = _DEFAULT_MAX_INPUT_TOKENS,
        normalized: bool = True,
        fail_inputs: Set[str] | None = None,
        probe_fails: bool = False,
        name: str = _DEFAULT_NAME,
        use_exact_tokenizer: bool = False,
        supports_batch: bool = False,
        batch_jobs: dict[str, Any] | None = None,
        batch_polls_before_terminal: int = _DEFAULT_BATCH_POLLS_BEFORE_TERMINAL,
        batch_should_fail: bool = False,
    ) -> None:
        """Configure the fake embedder.

        Args:
            dim: Dimensionality of the produced vectors.
            max_input_tokens: Reported hard per-input token cap.
            normalized: Whether produced vectors are L2-normalized to unit length.
            fail_inputs: Texts that should come back as ``None`` (permanent
                failure) from :meth:`embed_documents` and, per chunk, from
                :meth:`embed_document_chunks`; in the batch double a document
                containing any such chunk fails as a WHOLE line.
            probe_fails: When ``True``, :meth:`probe` raises to simulate an
                unreachable endpoint.
            name: Reported model name.
            use_exact_tokenizer: When ``True``, :meth:`count_tokens` delegates to
                the exact :class:`VoyageTokenCounter`; otherwise a ``len // 4``
                heuristic is used.
            supports_batch: Configurable :attr:`supports_batch` flag, so a test
                exercising batch-capability gating can flip it without a real
                batch-capable backend.
            batch_jobs: Injectable job store standing in for the real Voyage
                account — shared across instances to exercise resumability; a
                private (per-instance) ``{}`` by default so unrelated instances
                never see each other's jobs.
            batch_polls_before_terminal: Number of :meth:`get_batch_status`
                polls a submitted job stays ``in_progress`` before reaching a
                terminal status (``1`` = terminal on the first poll).
            batch_should_fail: When ``True``, a submitted job's terminal status
                is ``failed`` (a whole-job failure), not ``completed``.
        """
        self._dim = dim
        self._max_input_tokens = max_input_tokens
        self._normalized = normalized
        self._fail_inputs: frozenset[str] = frozenset(fail_inputs or ())
        self._probe_fails = probe_fails
        self._name = name
        self._token_counter: VoyageTokenCounter | None = (
            VoyageTokenCounter() if use_exact_tokenizer else None
        )
        self._supports_batch = supports_batch
        # Private per-instance store by default; a shared dict makes a job
        # resumable by a brand-new instance (the real Voyage account analogue).
        self._batch_jobs: dict[str, Any] = batch_jobs if batch_jobs is not None else {}
        self._batch_polls_before_terminal = batch_polls_before_terminal
        self._batch_should_fail = batch_should_fail

    @property
    def name(self) -> str:
        """Reported model name."""
        return self._name

    @property
    def dim(self) -> int:
        """Dimensionality of the produced vectors."""
        return self._dim

    @property
    def max_input_tokens(self) -> int:
        """Reported hard per-input token cap."""
        return self._max_input_tokens

    @property
    def normalized(self) -> bool:
        """Whether produced vectors are L2-normalized to unit length."""
        return self._normalized

    def _vector_for(self, text: str) -> list[float]:
        """Derive a deterministic vector from a stable hash of ``text``.

        A SHA-256-based digest is expanded to ``dim`` float components (so the
        result is identical across processes and instances), then L2-normalized
        to unit length when ``normalized`` is set.

        Args:
            text: The input to embed.

        Returns:
            The deterministic embedding vector for ``text``.
        """
        # Expand the digest deterministically until we have enough bytes for all
        # components (dim * 8 bytes), then unpack to signed float64-friendly ints.
        needed = self._dim * _BYTES_PER_COMPONENT
        digest = b""
        counter = 0
        while len(digest) < needed:
            block = f"{text}\x00{counter}".encode()
            digest += hashlib.sha256(block).digest()
            counter += 1

        components: list[float] = []
        for index in range(self._dim):
            start = index * _BYTES_PER_COMPONENT
            chunk = digest[start : start + _BYTES_PER_COMPONENT]
            # Map 8 bytes -> an unsigned int -> a float centered around zero so
            # vectors point in varied directions rather than all-positive.
            raw = struct.unpack(">Q", chunk)[0]
            components.append(float(raw) - float(1 << 63))

        if self._normalized:
            norm = math.hypot(*components)
            if norm == 0.0:
                # Degenerate (astronomically unlikely): emit a canonical unit axis.
                components = [1.0] + [0.0] * (self._dim - 1)
            else:
                components = [value / norm for value in components]
        return components

    def _usage_for(self, texts: list[str]) -> EmbedUsage:
        """Deterministic bill for ``texts``: the sum of :meth:`count_tokens`.

        Shared by the flat and grouped paths so both report against the SAME
        public, recomputable source of truth — a downstream cost test can
        recompute this exactly via ``embedder.count_tokens``. A
        ``fail_inputs`` text (flat path) still counts: "billed" != "succeeded".
        """
        return EmbedUsage(total_tokens=sum(self.count_tokens(texts)))

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        """Embed a batch, returning a result positionally aligned with ``texts``."""
        return self._embed_documents_core(texts)

    def _embed_documents_core(self, texts: list[str]) -> EmbedResult:
        """The flat-embed core, shared by the realtime path AND the fake batch
        synthesis (:meth:`_compute_batch_results`) — a PRIVATE seam so a
        recording subclass overriding the public method never counts internal
        batch synthesis as a realtime call, while batch/realtime vectors stay
        byte-identical by construction."""
        vectors: list[list[float] | None] = [
            None if text in self._fail_inputs else self._vector_for(text) for text in texts
        ]
        return EmbedResult(vectors=vectors, dim=self._dim, usage=self._usage_for(texts))

    @property
    def supports_contextualized(self) -> bool:
        """The fake advertises the contextualized (document-grouped) seam."""
        return True

    @property
    def supports_batch(self) -> bool:
        """Configurable batch-capability flag (see the constructor's ``supports_batch``)."""
        return self._supports_batch

    async def embed_document_chunks(self, docs: list[list[str]]) -> list[EmbedResult]:
        """Embed each doc's grouped chunks with deterministic context sensitivity.

        A chunk's vector depends on its SURROUNDING document (different doc ->
        different vector; in-doc differs from flat ``embed_documents``), while
        chunks stay individually distinguishable. ``fail_inputs`` applies per
        chunk: a failing chunk is ``None`` at its slot, siblings unaffected.

        Args:
            docs: One entry per document, each the ordered chunk texts.

        Returns:
            One input-aligned :class:`EmbedResult` per doc; each doc's ``usage``
            is the exact bill for just that doc's chunks (offline, the fake CAN
            measure per doc, so it always does).
        """
        return self._embed_document_chunks_core(docs)

    def _embed_document_chunks_core(self, docs: list[list[str]]) -> list[EmbedResult]:
        """The grouped-embed core, shared by the realtime path AND the fake
        batch synthesis — private for the same recording-subclass reason as
        :meth:`_embed_documents_core`."""
        results: list[EmbedResult] = []
        for chunks in docs:
            # The context key folds in every chunk of the surrounding
            # document, so the SAME chunk text embedded inside two different
            # documents (differing elsewhere) yields two different vectors —
            # the observable proof that grouping happened.
            context_key = _DOC_CONTEXT_SEPARATOR.join(chunks)
            vectors: list[list[float] | None] = [
                None
                if chunk in self._fail_inputs
                else self._vector_for(
                    f"{context_key}{_DOC_CONTEXT_SEPARATOR}{index}{_DOC_CONTEXT_SEPARATOR}{chunk}"
                )
                for index, chunk in enumerate(chunks)
            ]
            results.append(EmbedResult(vectors=vectors, dim=self._dim, usage=self._usage_for(chunks)))
        return results

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string into one deterministic vector."""
        return self._vector_for(text)

    async def probe(self) -> int:
        """Return ``dim`` normally, or raise when configured to fail.

        Raises:
            ConnectionError: When ``probe_fails`` was set, simulating an
                unreachable embedding endpoint.
        """
        if self._probe_fails:
            raise ConnectionError("FakeEmbedder configured with probe_fails=True")
        return self._dim

    def count_tokens(self, texts: list[str]) -> list[int]:
        """Return an input-aligned list of token counts.

        Uses the exact :class:`VoyageTokenCounter` when configured, otherwise a
        ``len // 4`` heuristic (non-empty inputs report at least one token).
        """
        if self._token_counter is not None:
            return self._token_counter.count_tokens(texts)
        return [self._heuristic_count(text) for text in texts]

    @staticmethod
    def _heuristic_count(text: str) -> int:
        """Cheap ``len // 4`` token estimate; non-empty text yields at least one."""
        if not text:
            return 0
        return max(1, len(text) // _CHARS_PER_TOKEN)

    # ── Offline Batch API double ─────────────────────────────────────────────
    async def submit_batch_documents(self, texts: list[str], ids: list[str]) -> str:
        """Record an offline batch job embedding ``texts`` (flat arm).

        Validated identically to the real backends (via the shared
        :func:`~loresigil.voyage_batch.encode_batch_jsonl` length/empty/
        duplicate checks) BEFORE any job is recorded.

        Raises:
            NotImplementedError: When ``supports_batch`` is ``False``.
            ValueError: Empty batch or an ``ids``/``texts`` length mismatch.
            DuplicateBatchIdError: A repeated id (named in the message).
        """
        if not self._supports_batch:
            raise self._batch_unsupported("submit_batch_documents")
        # Validate before recording; discards the encoded bytes (offline fake).
        encode_batch_jsonl(ids, [{"input": [text]} for text in texts])
        return self._record_batch_job(_BATCH_KIND_FLAT, list(texts), list(ids))

    async def submit_batch_document_chunks(self, docs: list[list[str]], ids: list[str]) -> str:
        """Record an offline batch job embedding ``docs`` (grouped arm).

        Raises:
            NotImplementedError: When ``supports_batch`` is ``False``.
            ValueError: Empty batch or an ``ids``/``docs`` length mismatch.
            DuplicateBatchIdError: A repeated id (named in the message).
        """
        if not self._supports_batch:
            raise self._batch_unsupported("submit_batch_document_chunks")
        encode_batch_jsonl(ids, [{"inputs": [chunks]} for chunks in docs])
        return self._record_batch_job(
            _BATCH_KIND_GROUPED, [list(chunks) for chunks in docs], list(ids)
        )

    def _record_batch_job(self, kind: str, payload: Any, ids: list[str]) -> str:
        """Store a job in the shared job store and return its unique id.

        The per-job poll/failure config is snapshotted HERE so a resumed
        instance (sharing only the job store) reproduces the submitter's
        behaviour, not its own — a job's outcome is fixed at submit time.
        """
        job_id = f"{_FAKE_BATCH_JOB_PREFIX}{uuid.uuid4().hex}"
        self._batch_jobs[job_id] = {
            "kind": kind,
            "payload": payload,
            "ids": ids,
            "polls": 0,
            "polls_before_terminal": self._batch_polls_before_terminal,
            "should_fail": self._batch_should_fail,
        }
        return job_id

    async def get_batch_status(self, job_id: str) -> str:
        """Return a recorded job's status, advancing its poll counter.

        Mirrors the real fake-provider server: each poll advances the job until
        it has been polled ``polls_before_terminal`` times, then it settles on
        its terminal status.

        Raises:
            KeyError: An unknown job id (e.g. a job an unrelated instance's
                private store never recorded).
        """
        job = self._batch_jobs[job_id]
        job["polls"] += 1
        if job["polls"] < job["polls_before_terminal"]:
            return STATUS_IN_PROGRESS
        return STATUS_FAILED if job["should_fail"] else STATUS_COMPLETED

    async def await_batch_completion(
        self,
        job_id: str,
        *,
        poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
        sleep_fn: SleepFn | None = None,
        deadline_s: float | None = None,
    ) -> str:
        """Poll a recorded job until terminal (see :func:`poll_until_terminal`).

        Honours the SAME terminal/deadline/failure contract as the real
        backends, driven by the shared helper.

        Raises:
            TimeoutError: The deadline elapsed before a terminal status.
            BatchJobFailedError: A ``failed`` terminal status, naming the job id.
        """
        return await poll_until_terminal(
            lambda: self.get_batch_status(job_id),
            job_id=job_id,
            poll_interval_s=poll_interval_s,
            sleep_fn=sleep_fn,
            deadline_s=deadline_s,
        )

    async def fetch_batch_results(
        self, job_id: str
    ) -> dict[str, list[float] | EmbedResult | None]:
        """Fetch a completed job's results, keyed by caller-supplied id.

        Vectors are computed through the SAME realtime code paths as
        :meth:`embed_documents` / :meth:`embed_document_chunks`, so batch and
        realtime results are byte-identical by construction. A flat id maps to
        a bare vector (or ``None`` for a failed text); a grouped id maps to its
        doc's :class:`EmbedResult` (or bare ``None`` when the WHOLE line failed,
        design decision #4).

        Raises:
            KeyError: An unknown job id.
            RuntimeError: The job has not yet reached a terminal status.
            BatchJobFailedError: A ``failed`` terminal status, naming the job id.
        """
        status = await self.get_batch_status(job_id)
        if status not in TERMINAL_BATCH_STATUSES:
            raise RuntimeError(
                f"batch job {job_id} has not reached a terminal status yet (status={status!r})"
            )
        if status != STATUS_COMPLETED:
            raise BatchJobFailedError(job_id, status=status)
        return await self._compute_batch_results(self._batch_jobs[job_id])

    async def _compute_batch_results(
        self, job: dict[str, Any]
    ) -> dict[str, list[float] | EmbedResult | None]:
        """Compute a completed job's id-keyed results via the realtime paths."""
        ids: list[str] = job["ids"]
        results: dict[str, list[float] | EmbedResult | None] = {}
        if job["kind"] == _BATCH_KIND_FLAT:
            # PRIVATE core, not the public method: a recording subclass's
            # override of embed_documents must never count this internal
            # synthesis as a realtime call (vectors stay byte-identical —
            # same core the realtime path delegates to).
            realtime = self._embed_documents_core(job["payload"])
            for custom_id, vector in zip(ids, realtime.vectors, strict=True):
                results[custom_id] = vector
            return results
        for chunks, custom_id in zip(job["payload"], ids, strict=True):
            if any(chunk in self._fail_inputs for chunk in chunks):
                # A batch line is one atomic unit: any failed chunk fails the
                # WHOLE line to a bare None (design decision #4).
                results[custom_id] = None
            else:
                [doc_result] = self._embed_document_chunks_core([chunks])
                results[custom_id] = doc_result
        return results
