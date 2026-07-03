"""Contract tests for ledger #14 (part 1): the loresigil BATCH embedding
capability — Voyage AI's asynchronous Batch API — for BOTH the flat
(``VoyageCloudEmbedder``) and contextualized (``VoyageContextEmbedder``) arms.

SCOPE: loresigil ONLY. The indexer bulk-sweep integration (loremaster) that
will actually DRIVE this capability against a 100K+-file cold-start sweep is
a later cycle; this file pins the embedder-level capability in isolation.

GROUND TRUTH (fetched 2026-07-03 directly from docs.voyageai.com/docs/batch-
inference — the "Batch Inference" guide page; the WebFetch/WebSearch tools
were unavailable in this environment, so the page was retrieved with
``curl`` and its server-rendered ``ssr-props`` JSON payload was parsed for
the authored markdown body, i.e. the SAME primary-source content a browser
renders, not a cache/recollection). Verbatim passages this contract relies
on:

* "You can create batch jobs for the following endpoints: `/v1/embeddings`
  ..., `/v1/contextualizedembeddings` ..., and `v1/rerank` ..." — CONFIRMS
  both endpoint arms are batch-capable (rerank is out of loresigil's scope
  entirely — it embeds, it does not rerank).
* "The input data for batch requests are bundled in a JSONL file... A batch
  request input object requires two keys: `custom_id` and `body`... `input`
  for `v1/embeddings`, `inputs` for `v1/contextualizedembeddings`."
* "**100K inputs per batch maximum**. Each batch can contain up to 100K
  inputs." + (Organization Limits) "each batch job may contain no more than
  **100K inputs**." — CONFIRMS the 100K-line cap; this is a LINE-COUNT cap,
  not a per-line example count (a single `/v1/embeddings` line may itself
  hold "up to 1,000 examples").
* "Our Batch API offers a **12-hour completion window**" and the create-batch
  example body: `{"endpoint": ..., "completion_window": "12h", ...}`.
* "In order for batch jobs to access the batch input file, it must be
  uploaded using our Files API" — `POST /v1/files` multipart, `-F
  purpose="batch" -F file="@foo.jsonl"` — response `{"object":"file",
  "id":"file_abc123", "purpose":"batch", "filename":..., "bytes":...,
  "created_at":...}`.
* "This is a user-provided ID used to match outputs to inputs SINCE THE
  ORDERING OF OUTPUT RESULTS WILL NOT NECESSARILY BE ALIGNED WITH THE
  ORDERING OF INPUT REQUESTS. The `custom_id` values must be unique..." —
  CONFIRMS order-independence must be pinned by content, never by position.
* "The `request_params` parameter specifies all endpoint parameters for
  requests... Essentially, the batch job combines the input data from the
  batch input JSONL file with the endpoint parameters in `request_params`...
  Any endpoint parameter not explicitly set will default to the endpoint's
  default value." — CONFIRMS `model`/`input_type`/`output_dimension`/
  `enable_auto_chunking` belong in the BATCH-LEVEL `request_params`, not
  per-line — a STRONGER guarantee than the realtime per-request pin, since
  one override covers every line in the job.
* Batch lifecycle table: `validating` -> `failed` | `in_progress` ->
  `finalizing` -> `completed` | `cancelling` -> `cancelled`.
* Batch output-file line: `{"batch_id":..., "custom_id":..., "response":
  {"status_code":200, "body": {"object":"list", "data":[{"object":
  "embedding","index":0,"embedding":[...]}], "model":..., "usage":
  {"total_tokens":33}}}, "error": null}` — CONFIRMS the wrapped body is
  BYTE-IDENTICAL in shape to the realtime response (`data[].embedding` for
  `/v1/embeddings`; the S8-verified `data[i].data[j].embedding` for
  `/v1/contextualizedembeddings`), just nested under `response.body`.
* Batch error-file lines (two documented shapes): `{"batch_id":...,
  "custom_id":..., "response": {"status_code":500,"message":"..."},
  "error": null}` and `{"batch_id":..., "custom_id":..., "response": null,
  "error": {"code":"batch_expired","message":"..."}}` — a parser must
  tolerate BOTH.
* "each batch job may contain no more than 100K inputs" (Organization
  Limits section) — corroborates the 100K cap a second time.

DOCS CROSS-CHECK FLAG (operator attention needed): the task brief's
previously-verified "1GB per batch file" cap was NOT found in the
anonymously-fetchable guide text this session (only the 100K-input COUNT
cap is stated there). The byte-size cap likely lives in the OAS reference
spec (`docs.voyageai.com/reference/files` / `/reference/batch`), which
renders client-side from a separately-fetched JSON definition not reachable
via a plain HTTP GET in this environment. ``MAX_BATCH_FILE_BYTES`` below is
carried over from the task brief's prior spike ground truth and pinned
DEFENSIVELY (a byte cap is a sane guard regardless), but is NOT
independently re-confirmed by this session's fetch — flagged for GREEN-phase
confirmation before treating it as verified.

THE PINNED PUBLIC API SURFACE (named here, blind to any implementation)
-------------------------------------------------------------------------
``loresigil.base``:

    class Embedder:
        @property
        def supports_batch(self) -> bool: ...  # non-abstract default False,
                                                 # mirrors supports_contextualized

``loresigil.testing``:

    class FakeEmbedder:
        def __init__(self, ..., supports_batch: bool = False, ...) -> None: ...

``loresigil.voyage_batch`` (NEW shared module — Files/Batches API plumbing
common to both Voyage backends; the /v1/embeddings vs
/v1/contextualizedembeddings request/response SHAPE differences stay in each
backend, exactly the same separation-of-concerns ``voyage_http.py`` already
uses for the realtime bearer-client builder):

    DEFAULT_FILES_API_URL: str = "https://api.voyageai.com/v1/files"
    DEFAULT_BATCHES_API_URL: str = "https://api.voyageai.com/v1/batches"
    DEFAULT_COMPLETION_WINDOW: str = "12h"
    DEFAULT_POLL_INTERVAL_S: float
    MAX_BATCH_INPUTS: int = 100_000
    MAX_BATCH_FILE_BYTES: int = 1_073_741_824  # see docs cross-check flag above

    STATUS_VALIDATING = "validating"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_FINALIZING = "finalizing"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELLING = "cancelling"
    STATUS_CANCELLED = "cancelled"
    TERMINAL_BATCH_STATUSES: frozenset[str]

    class BatchSizeExceededError(ValueError): ...   # names actual size/count AND the cap
    class BatchJobFailedError(RuntimeError): ...     # names the job id
    class DuplicateBatchIdError(ValueError): ...     # names the duplicate id

    def encode_batch_jsonl(
        ids: list[str], bodies: list[dict[str, Any]], *,
        max_inputs: int = MAX_BATCH_INPUTS, max_bytes: int = MAX_BATCH_FILE_BYTES,
    ) -> bytes: ...
        # PURE. One JSONL line per (id, body) pair, in input order:
        # {"custom_id": id, "body": body}. Raises ValueError on empty input,
        # a length mismatch, DuplicateBatchIdError on a repeated id, and
        # BatchSizeExceededError when line count or encoded byte size
        # exceeds the (injectable, for cheap testing) caps.

On ``VoyageCloudEmbedder`` (flat arm) AND ``VoyageContextEmbedder`` (grouped
arm) — new constructor keywords (sensible defaults, existing call sites
unaffected) plus five new methods each:

    def __init__(..., files_api_url: str = DEFAULT_FILES_API_URL,
                 batches_api_url: str = DEFAULT_BATCHES_API_URL) -> None: ...

    @property
    def supports_batch(self) -> bool: ...  # True

    # VoyageCloudEmbedder — mirrors embed_documents' flat shape:
    async def submit_batch_documents(self, texts: list[str], ids: list[str]) -> str: ...
    async def fetch_batch_results(self, job_id: str) -> dict[str, list[float] | None]: ...

    # VoyageContextEmbedder — mirrors embed_document_chunks' grouped shape,
    # ONE JSONL line per document group (P1 per-doc atomicity preserved at
    # the batch seam; enable_auto_chunking pinned once in request_params):
    async def submit_batch_document_chunks(self, docs: list[list[str]], ids: list[str]) -> str: ...
    async def fetch_batch_results(self, job_id: str) -> dict[str, EmbedResult | None]: ...

    # Shared shape on BOTH classes:
    async def get_batch_status(self, job_id: str) -> str: ...
    async def await_batch_completion(
        self, job_id: str, *, poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
        sleep_fn: SleepFn | None = None,
    ) -> str: ...
        # Polls until a TERMINAL status; sleeps only BETWEEN polls (never a
        # trailing sleep); raises BatchJobFailedError naming the job id if
        # the terminal status is "failed".

DESIGN DECISIONS (documented per the CONTRACT-phase discipline)
-------------------------------------------------------------------------
1. Results are retrieved BY CALLER-SUPPLIED STABLE ID, never by response
   line position (the guide explicitly disclaims output-line ordering) — a
   dict keyed by the caller's own ``ids``, not a positionally-reassembled
   list. This is also what makes resumability possible: a NEW process only
   needs ``job_id`` (persisted externally) to fetch results; it never needs
   the original in-memory submission list.
2. ONE JSONL line per input unit (one text for the cloud arm, one document
   group for the context arm) rather than packing multiple examples into
   one line for throughput. This keeps `custom_id` 1:1 with the caller's own
   id (no internal index-to-id re-attribution bookkeeping to get wrong) and
   makes the 100K-line cap directly equal to "100K docs/texts per job" for
   this cycle. Packing multiple examples per line is legal per the wire
   (the guide's OWN example groups 2 docs in 1 line) and is explicitly left
   as later-cycle implementation freedom for throughput tuning.
3. Batch-level parameters (`model`, `input_type`, `output_dimension`,
   `enable_auto_chunking`) are sent ONCE in `request_params` at batch
   creation — never per-line — because the guide states they apply to every
   request in the job. `input_type` is always `"document"` (a batch job's
   12h latency makes it useless for live queries).
4. A whole-line (whole-doc / whole-text) failure surfaces via the
   documented error file and maps its id to `None` — the SAME sentinel
   convention `EmbedResult.vectors` already uses for a permanently-failed
   slot, extended to whole-line grain here (a batch line IS one unit, unlike
   the realtime combined-batch fast path's finer per-chunk grain).
5. Per-doc `EmbedResult.usage` on the context arm's successful lines is an
   EXACT measurement (this line's own wire `usage.total_tokens`), not an
   attributed split — because design decision #2 means one line == one doc,
   so there is no cross-doc attribution problem to solve (unlike the
   realtime arm's combined-request fast path).
6. Cloud-arm usage stays entirely un-surfaced this cycle (batch results are
   raw `list[float] | None`, no `EmbedResult` envelope) — this MATCHES the
   realtime cloud arm's own pinned guarantee (`usage is None`,
   `test_embed_usage.py::TestNonReportingBackendsDefaultNone`), so "same
   guarantees the realtime arm pins" holds by construction rather than by a
   fresh promise this cycle would have to keep.
7. Factory/config (ledger item 8): NO new ``EmbeddingConfig`` fields this
   cycle. The Files/Batches endpoints are fixed, documented URLs (module
   constants, same precedent as ``DEFAULT_API_URL``) — there is nothing
   deployment-specific to configure yet, and no consumer (the indexer bulk
   sweep) exists within scope to read a YAML `embedding.batch.*` block. The
   one factory-level pin here is the SAME shape as
   ``test_factory_voyage_context.py``'s capability-survives-the-seam pin:
   ``supports_batch`` reads ``True`` off a factory-built embedder.

RED STRATEGY: ``loresigil.voyage_batch`` is a brand-new top-level module, so
importing its names is guarded (try/except ImportError, mirroring
``test_surreal_apply.py``'s precedent) with OBVIOUSLY-WRONG placeholder
values (never the real expected value) so a constant-only assertion cannot
accidentally pass pre-implementation. The new METHODS on
``VoyageCloudEmbedder``/``VoyageContextEmbedder`` hang off classes that
already import cleanly — calling one raises ``AttributeError`` at the point
under test, a behavioural RED needing no import guard.
"""

from __future__ import annotations

import asyncio
import email
import hashlib
import json
import math
import os
import time
import uuid
from typing import Any

import httpx
import pytest
from _contextualized_fixtures import DOC_POLICY, DOC_RUNBOOK, DOC_SINGLE
from loresigil.base import Embedder, EmbedResult, EmbedUsage
from loresigil.testing import FakeEmbedder
from loresigil.voyage_cloud import DEFAULT_API_URL as CLOUD_API_URL
from loresigil.voyage_cloud import DEFAULT_DIM as CLOUD_DIM
from loresigil.voyage_cloud import DEFAULT_MODEL as CLOUD_MODEL
from loresigil.voyage_cloud import VoyageCloudEmbedder
from loresigil.voyage_context import DEFAULT_API_URL as CONTEXT_API_URL
from loresigil.voyage_context import DEFAULT_DIM as CONTEXT_DIM
from loresigil.voyage_context import DEFAULT_MODEL as CONTEXT_MODEL
from loresigil.voyage_context import VoyageContextEmbedder

# --- The brand-new loresigil.voyage_batch module (RED-guarded so collection
# never explodes; see the module docstring's RED STRATEGY section). ----------
try:
    from loresigil.voyage_batch import (  # noqa: E402
        DEFAULT_BATCHES_API_URL,
        DEFAULT_COMPLETION_WINDOW,
        DEFAULT_FILES_API_URL,
        DEFAULT_POLL_INTERVAL_S,
        MAX_BATCH_FILE_BYTES,
        MAX_BATCH_INPUTS,
        STATUS_COMPLETED,
        STATUS_FAILED,
        STATUS_IN_PROGRESS,
        TERMINAL_BATCH_STATUSES,
        BatchJobFailedError,
        BatchSizeExceededError,
        DuplicateBatchIdError,
        encode_batch_jsonl,
    )

    _BATCH_API_AVAILABLE = True
except ImportError:  # pragma: no cover - pre-implementation RED: the module is absent
    _BATCH_API_AVAILABLE = False

    class _MissingVoyageBatchApiError(Exception):
        """Placeholder so ``pytest.raises(BatchSizeExceededError)`` etc. are
        valid type expressions before the real error classes exist. Every
        test that reads a fallback below ALSO calls ``encode_batch_jsonl``
        (``None`` here) or a not-yet-existing embedder method first, so RED
        always comes from the real API under test."""

    BatchSizeExceededError = _MissingVoyageBatchApiError  # type: ignore[misc,assignment]
    BatchJobFailedError = _MissingVoyageBatchApiError  # type: ignore[misc,assignment]
    DuplicateBatchIdError = _MissingVoyageBatchApiError  # type: ignore[misc,assignment]
    encode_batch_jsonl = None  # type: ignore[assignment]
    # Obviously-wrong placeholders (never the real expected value) so a
    # constant-only comparison cannot silently pass pre-implementation.
    DEFAULT_FILES_API_URL = ""
    DEFAULT_BATCHES_API_URL = ""
    DEFAULT_COMPLETION_WINDOW = ""
    DEFAULT_POLL_INTERVAL_S = -1.0
    MAX_BATCH_INPUTS = -1
    MAX_BATCH_FILE_BYTES = -1
    STATUS_IN_PROGRESS = "__missing_status_in_progress__"
    STATUS_COMPLETED = "__missing_status_completed__"
    STATUS_FAILED = "__missing_status_failed__"
    TERMINAL_BATCH_STATUSES = frozenset()


# ── Shared test parameters ───────────────────────────────────────────────────
API_KEY: str = "voyage-test-key-batch-b077e5"

# Realistic flat texts / grouped docs — the SAME shared fixtures already used
# project-wide (test_voyage_context.py, test_embed_usage.py), never invented
# ad hoc strings (clause 5: shared domain convention, not a hand-copied literal).
FLAT_TEXTS: list[str] = [DOC_POLICY[0], DOC_RUNBOOK[1], DOC_SINGLE[0]]

# Stable, realistic-SHAPED ids: uuid5 strings, mirroring loremaster's own
# content-addressed id convention (``loremaster.index.records.point_id`` is a
# uuid5 of a natural key) rather than an arbitrary "id-1"/"id-2" placeholder —
# this is the id SHAPE a real caller (the indexer, later cycle) will actually
# pass as ``custom_id``.
_ID_NAMESPACE = uuid.NAMESPACE_URL


def _stable_id(seed: str) -> str:
    """A realistic-shaped, deterministic uuid5 id for a given seed string."""
    return str(uuid.uuid5(_ID_NAMESPACE, seed))


FLAT_IDS: list[str] = [_stable_id(f"flat-chunk:{text}") for text in FLAT_TEXTS]
DOC_IDS_2: list[str] = [
    _stable_id(f"doc:{i}:{chunks[0]}") for i, chunks in enumerate([DOC_RUNBOOK, DOC_POLICY])
]
DOC_IDS_3: list[str] = [
    _stable_id(f"doc:{i}:{chunks[0]}") for i, chunks in enumerate([DOC_RUNBOOK, DOC_POLICY, DOC_SINGLE])
]

NORM_TOLERANCE: float = 1e-6
# Smallest REAL poll delay is DEFAULT_POLL_INTERVAL_S (>= several seconds in
# any sane deployment); a retried/polled call finishing well under this proves
# the injected fake sleep really replaced a real one (mirrors
# test_voyage_context.py's FAKE_SLEEP_WALL_BUDGET_S precedent).
FAKE_SLEEP_WALL_BUDGET_S: float = 0.5


async def _instant_sleep(_delay: float) -> None:
    """No-op sleep — the injectable seam, standing in for real backoff/poll waits."""
    return None


def _unit_vector_for_text(text: str, dim: int) -> list[float]:
    """Deterministic, text-distinguishing, L2-normalized vector — the SAME
    independent oracle style ``test_voyage_context.py`` uses, so the mock
    server and the assertions can each recompute it without consulting the
    implementation under test."""
    digest = hashlib.sha256(text.encode()).digest()
    seed = int.from_bytes(digest[:8], "big") / float(1 << 64)
    raw = [seed + 1.0 + index * 1e-6 for index in range(dim)]
    norm = math.sqrt(sum(component * component for component in raw))
    return [component / norm for component in raw]


def _heuristic_tokens(text: str) -> int:
    """~4 chars/token mock-provider billing meter (deliberately different from
    the client's exact tokenizer — see test_embed_usage.py's identical
    convention: an implementation that fabricates usage from its own token
    counter, instead of reading the wire, cannot conserve this)."""
    return max(1, len(text) // 4) if text else 0


def _parse_multipart_upload(request: httpx.Request) -> tuple[str, bytes]:
    """Decode a Files-API multipart upload into ``(purpose, file_bytes)``.

    Mirrors the guide's ``-F purpose="batch" -F file="@foo.jsonl"`` shape.
    Uses the stdlib ``email`` parser (multipart/form-data is MIME-structurally
    identical) rather than a hand-rolled boundary splitter.
    """
    header_bytes = f'Content-Type: {request.headers["content-type"]}\r\nMIME-Version: 1.0\r\n\r\n'.encode()
    message = email.message_from_bytes(header_bytes + request.content)
    parts: dict[str, bytes] = {}
    payload = message.get_payload()
    assert isinstance(payload, list)  # multipart: the parser yields sub-Messages
    for part in payload:
        assert isinstance(part, email.message.Message)
        name = part.get_param("name", header="Content-Disposition")
        body = part.get_payload(decode=True)
        assert isinstance(body, bytes)
        parts[str(name)] = body
    return parts["purpose"].decode(), parts["file"]


def _jsonl_lines(raw: bytes) -> list[dict[str, Any]]:
    """Parse JSONL bytes into an ordered list of line objects."""
    return [json.loads(line) for line in raw.decode().splitlines() if line]


class _CloudBatchServer:
    """Offline fake of the Voyage Files + Batches APIs for the flat
    ``/v1/embeddings`` arm — AND the realtime ``/v1/embeddings`` endpoint
    itself, so the SAME server backs both the lifecycle tests and the
    realtime/batch vector-parity tests.

    Models exactly the objects the Batch Inference guide documents (fetched
    2026-07-03; see module docstring): ``POST /v1/files`` (multipart) ->
    ``{"id": file_id}``; ``POST /v1/batches`` -> Batch object; ``GET
    /v1/batches/{id}`` -> Batch object (status advances to the configured
    terminal state after ``polls_before_terminal`` GETs); ``GET
    /v1/files/{id}/content`` -> raw JSONL output/error bytes. The output file
    is written in REVERSED line order relative to the input file — the
    guide's own documented behaviour ("the output line order may not match
    the input line order") — so EVERY lifecycle test here exercises the real
    id-keyed seam, not just a dedicated ordering test.
    """

    def __init__(
        self,
        dim: int = CLOUD_DIM,
        polls_before_terminal: int = 2,
        terminal_status: str = STATUS_COMPLETED,
        failed_ids: frozenset[str] = frozenset(),
    ) -> None:
        self.dim = dim
        self._polls_before_terminal = polls_before_terminal
        self._terminal_status = terminal_status
        self._failed_ids = failed_ids
        self.files: dict[str, bytes] = {}
        self.jobs: dict[str, dict[str, Any]] = {}
        self.batch_create_bodies: list[dict[str, Any]] = []
        self.status_poll_count: dict[str, int] = {}
        self.seen_auth_headers: list[str | None] = []
        self._file_seq = 0
        self._job_seq = 0

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            self.seen_auth_headers.append(request.headers.get("authorization"))
            path = request.url.path
            method = request.method
            if method == "POST" and path == "/v1/embeddings":
                return self._handle_realtime(request)
            if method == "POST" and path == "/v1/files":
                return self._handle_upload(request)
            if method == "POST" and path == "/v1/batches":
                return self._handle_create(request)
            if method == "GET" and path.startswith("/v1/batches/"):
                return self._handle_status(path.removeprefix("/v1/batches/"))
            if method == "GET" and path.startswith("/v1/files/") and path.endswith("/content"):
                file_id = path.removeprefix("/v1/files/").removesuffix("/content")
                return self._handle_download(file_id)
            raise AssertionError(f"unexpected cloud batch-server request: {method} {path}")

        return httpx.MockTransport(handler)

    def _handle_realtime(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        data = [{"embedding": _unit_vector_for_text(text, self.dim)} for text in body["input"]]
        return httpx.Response(200, json={"data": data})

    def _handle_upload(self, request: httpx.Request) -> httpx.Response:
        purpose, file_bytes = _parse_multipart_upload(request)
        assert purpose == "batch"
        self._file_seq += 1
        file_id = f"file-{self._file_seq}"
        self.files[file_id] = file_bytes
        return httpx.Response(
            200,
            json={
                "object": "file",
                "id": file_id,
                "purpose": "batch",
                "filename": "batch_input.jsonl",
                "bytes": len(file_bytes),
                "created_at": "2026-07-03T00:00:00Z",
            },
        )

    def _handle_create(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        self.batch_create_bodies.append(body)
        self._job_seq += 1
        job_id = f"batch-{self._job_seq}"
        self.jobs[job_id] = {
            "input_file_id": body["input_file_id"],
            "output_file_id": None,
            "error_file_id": None,
        }
        self.status_poll_count[job_id] = 0
        return httpx.Response(
            200,
            json={
                "id": job_id,
                "object": "batch",
                "status": STATUS_IN_PROGRESS,
                "output_file_id": None,
                "error_file_id": None,
            },
        )

    def _handle_status(self, job_id: str) -> httpx.Response:
        job = self.jobs[job_id]
        self.status_poll_count[job_id] += 1
        if self.status_poll_count[job_id] < self._polls_before_terminal:
            return httpx.Response(
                200,
                json={
                    "id": job_id,
                    "object": "batch",
                    "status": STATUS_IN_PROGRESS,
                    "output_file_id": None,
                    "error_file_id": None,
                },
            )
        if (
            job["output_file_id"] is None
            and job["error_file_id"] is None
            and self._terminal_status == STATUS_COMPLETED
        ):
            self._finalize(job_id, job)
        return httpx.Response(
            200,
            json={
                "id": job_id,
                "object": "batch",
                "status": self._terminal_status,
                "output_file_id": job["output_file_id"],
                "error_file_id": job["error_file_id"],
            },
        )

    def _finalize(self, job_id: str, job: dict[str, Any]) -> None:
        lines = _jsonl_lines(self.files[job["input_file_id"]])
        output_lines: list[dict[str, Any]] = []
        error_lines: list[dict[str, Any]] = []
        for line in lines:
            custom_id = line["custom_id"]
            texts: list[str] = line["body"]["input"]
            if custom_id in self._failed_ids:
                error_lines.append(
                    {
                        "batch_id": job_id,
                        "custom_id": custom_id,
                        "response": {"status_code": 500, "message": "Internal Server Error"},
                        "error": None,
                    }
                )
                continue
            data = [
                {"object": "embedding", "index": i, "embedding": _unit_vector_for_text(text, self.dim)}
                for i, text in enumerate(texts)
            ]
            total_tokens = sum(_heuristic_tokens(text) for text in texts)
            output_lines.append(
                {
                    "batch_id": job_id,
                    "custom_id": custom_id,
                    "response": {
                        "status_code": 200,
                        "body": {
                            "object": "list",
                            "data": data,
                            "model": CLOUD_MODEL,
                            "usage": {"total_tokens": total_tokens},
                        },
                    },
                    "error": None,
                }
            )
        # Documented behaviour: output line order need not match input order.
        output_lines.reverse()
        self._file_seq += 1
        output_file_id = f"file-{self._file_seq}"
        self.files[output_file_id] = self._encode_lines(output_lines)
        job["output_file_id"] = output_file_id
        if error_lines:
            self._file_seq += 1
            error_file_id = f"file-{self._file_seq}"
            self.files[error_file_id] = self._encode_lines(error_lines)
            job["error_file_id"] = error_file_id

    @staticmethod
    def _encode_lines(lines: list[dict[str, Any]]) -> bytes:
        return b"\n".join(json.dumps(line).encode() for line in lines) + b"\n"

    def _handle_download(self, file_id: str) -> httpx.Response:
        return httpx.Response(200, content=self.files[file_id], headers={"content-type": "application/jsonl"})


class _ContextBatchServer:
    """Offline fake of the Voyage Files + Batches APIs for the CONTEXTUALIZED
    (document-grouped) ``/v1/contextualizedembeddings`` arm, plus the
    realtime endpoint itself (see ``_CloudBatchServer`` docstring for why).

    ONE input line == ONE document group (design decision #2 in the module
    docstring): ``body["inputs"]`` is always a single-element outer list.
    """

    def __init__(
        self,
        dim: int = CONTEXT_DIM,
        polls_before_terminal: int = 2,
        terminal_status: str = STATUS_COMPLETED,
        failed_ids: frozenset[str] = frozenset(),
    ) -> None:
        self.dim = dim
        self._polls_before_terminal = polls_before_terminal
        self._terminal_status = terminal_status
        self._failed_ids = failed_ids
        self.files: dict[str, bytes] = {}
        self.jobs: dict[str, dict[str, Any]] = {}
        self.batch_create_bodies: list[dict[str, Any]] = []
        self.status_poll_count: dict[str, int] = {}
        self.seen_auth_headers: list[str | None] = []
        self._file_seq = 0
        self._job_seq = 0

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            self.seen_auth_headers.append(request.headers.get("authorization"))
            path = request.url.path
            method = request.method
            if method == "POST" and path == "/v1/contextualizedembeddings":
                return self._handle_realtime(request)
            if method == "POST" and path == "/v1/files":
                return self._handle_upload(request)
            if method == "POST" and path == "/v1/batches":
                return self._handle_create(request)
            if method == "GET" and path.startswith("/v1/batches/"):
                return self._handle_status(path.removeprefix("/v1/batches/"))
            if method == "GET" and path.startswith("/v1/files/") and path.endswith("/content"):
                file_id = path.removeprefix("/v1/files/").removesuffix("/content")
                return self._handle_download(file_id)
            raise AssertionError(f"unexpected context batch-server request: {method} {path}")

        return httpx.MockTransport(handler)

    def _handle_realtime(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        data = []
        for doc_index, chunks in enumerate(body["inputs"]):
            entries = [
                {"index": j, "embedding": _unit_vector_for_text(chunk, self.dim)}
                for j, chunk in enumerate(chunks)
            ]
            data.append({"index": doc_index, "data": entries})
        return httpx.Response(200, json={"data": data, "usage": {"total_tokens": 0}})

    def _handle_upload(self, request: httpx.Request) -> httpx.Response:
        purpose, file_bytes = _parse_multipart_upload(request)
        assert purpose == "batch"
        self._file_seq += 1
        file_id = f"file-{self._file_seq}"
        self.files[file_id] = file_bytes
        return httpx.Response(
            200,
            json={
                "object": "file",
                "id": file_id,
                "purpose": "batch",
                "filename": "batch_input.jsonl",
                "bytes": len(file_bytes),
                "created_at": "2026-07-03T00:00:00Z",
            },
        )

    def _handle_create(self, request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode())
        self.batch_create_bodies.append(body)
        self._job_seq += 1
        job_id = f"batch-{self._job_seq}"
        self.jobs[job_id] = {
            "input_file_id": body["input_file_id"],
            "output_file_id": None,
            "error_file_id": None,
        }
        self.status_poll_count[job_id] = 0
        return httpx.Response(
            200,
            json={
                "id": job_id,
                "object": "batch",
                "status": STATUS_IN_PROGRESS,
                "output_file_id": None,
                "error_file_id": None,
            },
        )

    def _handle_status(self, job_id: str) -> httpx.Response:
        job = self.jobs[job_id]
        self.status_poll_count[job_id] += 1
        if self.status_poll_count[job_id] < self._polls_before_terminal:
            return httpx.Response(
                200,
                json={
                    "id": job_id,
                    "object": "batch",
                    "status": STATUS_IN_PROGRESS,
                    "output_file_id": None,
                    "error_file_id": None,
                },
            )
        if (
            job["output_file_id"] is None
            and job["error_file_id"] is None
            and self._terminal_status == STATUS_COMPLETED
        ):
            self._finalize(job_id, job)
        return httpx.Response(
            200,
            json={
                "id": job_id,
                "object": "batch",
                "status": self._terminal_status,
                "output_file_id": job["output_file_id"],
                "error_file_id": job["error_file_id"],
            },
        )

    def _finalize(self, job_id: str, job: dict[str, Any]) -> None:
        lines = _jsonl_lines(self.files[job["input_file_id"]])
        output_lines: list[dict[str, Any]] = []
        error_lines: list[dict[str, Any]] = []
        for line in lines:
            custom_id = line["custom_id"]
            docs: list[list[str]] = line["body"]["inputs"]
            assert len(docs) == 1, "design decision #2: exactly one doc per line"
            chunks = docs[0]
            if custom_id in self._failed_ids:
                error_lines.append(
                    {
                        "batch_id": job_id,
                        "custom_id": custom_id,
                        "response": {"status_code": 500, "message": "Internal Server Error"},
                        "error": None,
                    }
                )
                continue
            entries = [
                {"index": j, "embedding": _unit_vector_for_text(chunk, self.dim)}
                for j, chunk in enumerate(chunks)
            ]
            total_tokens = sum(_heuristic_tokens(chunk) for chunk in chunks)
            output_lines.append(
                {
                    "batch_id": job_id,
                    "custom_id": custom_id,
                    "response": {
                        "status_code": 200,
                        "body": {
                            "object": "list",
                            "data": [{"index": 0, "data": entries}],
                            "model": CONTEXT_MODEL,
                            "usage": {"total_tokens": total_tokens},
                        },
                    },
                    "error": None,
                }
            )
        output_lines.reverse()
        self._file_seq += 1
        output_file_id = f"file-{self._file_seq}"
        self.files[output_file_id] = self._encode_lines(output_lines)
        job["output_file_id"] = output_file_id
        if error_lines:
            self._file_seq += 1
            error_file_id = f"file-{self._file_seq}"
            self.files[error_file_id] = self._encode_lines(error_lines)
            job["error_file_id"] = error_file_id

    @staticmethod
    def _encode_lines(lines: list[dict[str, Any]]) -> bytes:
        return b"\n".join(json.dumps(line).encode() for line in lines) + b"\n"

    def _handle_download(self, file_id: str) -> httpx.Response:
        return httpx.Response(200, content=self.files[file_id], headers={"content-type": "application/jsonl"})


def _make_cloud_batch_embedder(transport: httpx.MockTransport, **overrides: Any) -> VoyageCloudEmbedder:
    """Construct the cloud embedder under test — this call IS the constructor contract."""
    kwargs: dict[str, Any] = {
        "api_key": API_KEY,
        "api_url": CLOUD_API_URL,
        "model": CLOUD_MODEL,
        "dim": CLOUD_DIM,
        "output_dimension": CLOUD_DIM,
        "concurrency": 2,
        "transport": transport,
        "files_api_url": DEFAULT_FILES_API_URL,
        "batches_api_url": DEFAULT_BATCHES_API_URL,
    }
    kwargs.update(overrides)
    return VoyageCloudEmbedder(**kwargs)


def _make_context_batch_embedder(transport: httpx.MockTransport, **overrides: Any) -> VoyageContextEmbedder:
    """Construct the context embedder under test — this call IS the constructor contract."""
    kwargs: dict[str, Any] = {
        "api_key": API_KEY,
        "api_url": CONTEXT_API_URL,
        "model": CONTEXT_MODEL,
        "output_dimension": CONTEXT_DIM,
        "concurrency": 2,
        "transport": transport,
        "files_api_url": DEFAULT_FILES_API_URL,
        "batches_api_url": DEFAULT_BATCHES_API_URL,
    }
    kwargs.update(overrides)
    return VoyageContextEmbedder(**kwargs)


# ── 1. Capability seam ───────────────────────────────────────────────────────


class _LegacyCompleteEmbedder(Embedder):
    """Implements EXACTLY the pre-batch abstract/optional members — the
    back-compat probe proving ``supports_batch`` is a non-abstract default
    (mirrors ``test_contextualized_base.py``'s ``_LegacyCompleteEmbedder``)."""

    @property
    def name(self) -> str:
        return "legacy-complete"

    @property
    def dim(self) -> int:
        return 8

    @property
    def max_input_tokens(self) -> int:
        return 8192

    @property
    def normalized(self) -> bool:
        return True

    async def embed_documents(self, texts: list[str]) -> EmbedResult:
        return EmbedResult(vectors=[[0.0] * 8 for _ in texts], dim=8)

    async def embed_query(self, text: str) -> list[float]:
        return [0.0] * 8

    async def probe(self) -> int:
        return 8

    def count_tokens(self, texts: list[str]) -> list[int]:
        return [max(1, len(text) // 4) if text else 0 for text in texts]


class TestBatchCapabilityFlag:
    """``supports_batch`` — read-only, non-abstract, default False."""

    def test_defaults_to_false_on_a_legacy_embedder(self) -> None:
        embedder = _LegacyCompleteEmbedder()
        # ``is False`` (not falsy): a None/0 lookalike must not pass the
        # branch a caller/factory would gate batch-submission on.
        assert embedder.supports_batch is False

    def test_legacy_embedder_still_instantiates(self) -> None:
        # Back-compat pin: adding the property must not make Embedder (or a
        # subclass implementing only the pre-existing members) abstract.
        assert isinstance(_LegacyCompleteEmbedder(), Embedder)

    def test_is_read_only(self) -> None:
        embedder = _LegacyCompleteEmbedder()
        with pytest.raises(AttributeError):
            embedder.supports_batch = True  # type: ignore[misc]

    def test_fake_embedder_defaults_to_no_batch_support(self) -> None:
        assert FakeEmbedder().supports_batch is False

    def test_fake_embedder_batch_support_is_configurable(self) -> None:
        assert FakeEmbedder(supports_batch=True).supports_batch is True

    def test_voyage_cloud_embedder_advertises_batch_support(self) -> None:
        server = _CloudBatchServer()
        embedder = _make_cloud_batch_embedder(server.transport())
        assert embedder.supports_batch is True

    def test_voyage_context_embedder_advertises_batch_support(self) -> None:
        server = _ContextBatchServer()
        embedder = _make_context_batch_embedder(server.transport())
        assert embedder.supports_batch is True


# ── 2. Module constants (docs-grounded, see module docstring citations) ─────


class TestVoyageBatchModuleConstants:
    """Pins the shared module constants against the fetched Batch Inference guide."""

    def test_files_and_batches_endpoints_match_the_guide(self) -> None:
        assert DEFAULT_FILES_API_URL == "https://api.voyageai.com/v1/files"
        assert DEFAULT_BATCHES_API_URL == "https://api.voyageai.com/v1/batches"

    def test_completion_window_matches_the_guide(self) -> None:
        # Guide: "Our Batch API offers a 12-hour completion window"; the
        # create-batch example body literally sends "completion_window": "12h".
        assert DEFAULT_COMPLETION_WINDOW == "12h"

    def test_max_batch_inputs_matches_the_guide(self) -> None:
        # Guide, verbatim (stated twice): "100K inputs per batch maximum" and
        # "each batch job may contain no more than 100K inputs."
        assert MAX_BATCH_INPUTS == 100_000

    def test_max_batch_file_bytes_is_the_carried_over_cap(self) -> None:
        # See the module docstring's "DOCS CROSS-CHECK FLAG": this 1 GiB
        # value could NOT be independently re-confirmed against the
        # anonymously-fetchable guide text this session — pinned defensively
        # from the task brief's prior ground truth, flagged for the operator.
        assert MAX_BATCH_FILE_BYTES == 1_073_741_824

    def test_terminal_statuses_match_the_lifecycle_table(self) -> None:
        # Guide's lifecycle table: completed/failed/cancelled are the three
        # states with no further transition drawn in the diagram description.
        assert TERMINAL_BATCH_STATUSES == frozenset({"completed", "failed", "cancelled"})


# ── 3. JSONL shaping + build-time size refusal (pure, no network) ───────────


class TestEncodeBatchJsonlShaping:
    """``encode_batch_jsonl`` — pure JSONL builder + REFUSED-LOUD size caps."""

    def test_one_line_per_id_preserving_ids_and_bodies_in_order(self) -> None:
        ids = [_stable_id("a"), _stable_id("b")]
        bodies: list[dict[str, Any]] = [{"input": ["hello"]}, {"inputs": [["a", "b"]]}]
        encoded = encode_batch_jsonl(ids, bodies)
        lines = _jsonl_lines(encoded)
        assert len(lines) == 2
        assert [line["custom_id"] for line in lines] == ids
        assert [line["body"] for line in lines] == bodies

    def test_rejects_mismatched_ids_and_bodies_length(self) -> None:
        with pytest.raises(ValueError):
            encode_batch_jsonl([_stable_id("only-one")], [{"input": ["a"]}, {"input": ["b"]}])

    def test_rejects_empty_batch(self) -> None:
        with pytest.raises(ValueError):
            encode_batch_jsonl([], [])

    def test_rejects_duplicate_ids_naming_the_duplicate(self) -> None:
        duplicate = _stable_id("dup")
        with pytest.raises(DuplicateBatchIdError) as exc_info:
            encode_batch_jsonl([duplicate, duplicate], [{"input": ["a"]}, {"input": ["b"]}])
        assert duplicate in str(exc_info.value)

    def test_refuses_when_line_count_exceeds_an_injected_cap(self) -> None:
        # Injectable cap keeps this CHEAP — never allocates the real 100K
        # default, matching the "cheap sanity bound" discipline.
        ids = [_stable_id(f"line-{i}") for i in range(4)]
        bodies: list[dict[str, Any]] = [{"input": ["x"]}] * 4
        with pytest.raises(BatchSizeExceededError) as exc_info:
            encode_batch_jsonl(ids, bodies, max_inputs=3)
        message = str(exc_info.value)
        # Names BOTH the actual count and the cap — an operator must not have
        # to re-derive either number from the traceback alone.
        assert "4" in message
        assert "3" in message

    def test_refuses_when_encoded_bytes_exceed_an_injected_cap(self) -> None:
        ids = [_stable_id("big-line")]
        bodies: list[dict[str, Any]] = [
            {"input": ["Chargeback disputes must be filed within sixty days. " * 5]}
        ]
        # Derive the real encoded length from the function itself (never a
        # hand-guessed magic number) so the injected cap is realistic.
        encoded_len = len(encode_batch_jsonl(ids, bodies, max_bytes=10**9))
        with pytest.raises(BatchSizeExceededError) as exc_info:
            encode_batch_jsonl(ids, bodies, max_bytes=encoded_len - 1)
        assert str(encoded_len) in str(exc_info.value) or str(encoded_len - 1) in str(exc_info.value)


# ── 4/8. Request shape per arm + factory/config decision ────────────────────


class TestVoyageCloudBatchRequestShape:
    """Flat arm: JSONL upload + batch-create body + bearer auth on every leg."""

    async def test_uploads_one_jsonl_line_per_text_with_stable_ids(self) -> None:
        server = _CloudBatchServer()
        embedder = _make_cloud_batch_embedder(server.transport())
        await embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS)
        uploaded = next(iter(server.files.values()))
        lines = _jsonl_lines(uploaded)
        assert [line["custom_id"] for line in lines] == FLAT_IDS
        assert [line["body"] for line in lines] == [{"input": [text]} for text in FLAT_TEXTS]

    async def test_creates_batch_targeting_embeddings_endpoint(self) -> None:
        server = _CloudBatchServer()
        embedder = _make_cloud_batch_embedder(server.transport())
        await embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS)
        body = server.batch_create_bodies[0]
        assert body["endpoint"] == "/v1/embeddings"
        assert body["completion_window"] == DEFAULT_COMPLETION_WINDOW
        assert body["input_file_id"] in server.files
        # Batch-level parameters, sent ONCE (design decision #3) — not per-line.
        assert body["request_params"]["model"] == CLOUD_MODEL
        assert body["request_params"]["input_type"] == "document"
        assert body["request_params"]["output_dimension"] == CLOUD_DIM

    async def test_sends_bearer_authorization_on_every_leg(self) -> None:
        server = _CloudBatchServer(polls_before_terminal=1)
        embedder = _make_cloud_batch_embedder(server.transport())
        job_id = await embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS)
        await embedder.await_batch_completion(job_id, sleep_fn=_instant_sleep)
        await embedder.fetch_batch_results(job_id)
        # upload + create + >=1 status poll + download all happened.
        assert len(server.seen_auth_headers) >= 4
        assert all(header == f"Bearer {API_KEY}" for header in server.seen_auth_headers)

    async def test_returns_a_json_serializable_job_id_string(self) -> None:
        server = _CloudBatchServer()
        embedder = _make_cloud_batch_embedder(server.transport())
        job_id = await embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS)
        assert isinstance(job_id, str) and job_id
        assert json.loads(json.dumps(job_id)) == job_id  # "serializable job handle"

    async def test_rejects_mismatched_ids_length_before_any_network_call(self) -> None:
        server = _CloudBatchServer()
        embedder = _make_cloud_batch_embedder(server.transport())
        with pytest.raises(ValueError):
            await embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS[:-1])
        assert server.files == {}  # build-time refusal: nothing ever uploaded

    async def test_rejects_empty_batch_before_any_network_call(self) -> None:
        server = _CloudBatchServer()
        embedder = _make_cloud_batch_embedder(server.transport())
        with pytest.raises(ValueError):
            await embedder.submit_batch_documents([], [])
        assert server.files == {}

    async def test_rejects_duplicate_ids_before_any_network_call(self) -> None:
        server = _CloudBatchServer()
        embedder = _make_cloud_batch_embedder(server.transport())
        duplicate_ids = [FLAT_IDS[0], FLAT_IDS[0], FLAT_IDS[1]]
        with pytest.raises(DuplicateBatchIdError):
            await embedder.submit_batch_documents(FLAT_TEXTS, duplicate_ids)
        assert server.files == {}


class TestVoyageContextBatchRequestShape:
    """Grouped arm: one line PER DOCUMENT + enable_auto_chunking pinned once."""

    async def test_uploads_one_jsonl_line_per_document_group(self) -> None:
        server = _ContextBatchServer()
        embedder = _make_context_batch_embedder(server.transport())
        docs = [DOC_RUNBOOK, DOC_POLICY]
        await embedder.submit_batch_document_chunks(docs, DOC_IDS_2)
        uploaded = next(iter(server.files.values()))
        lines = _jsonl_lines(uploaded)
        assert [line["custom_id"] for line in lines] == DOC_IDS_2
        # P1 per-doc atomicity preserved at the batch seam: ONE doc per line.
        assert [line["body"] for line in lines] == [{"inputs": [DOC_RUNBOOK]}, {"inputs": [DOC_POLICY]}]

    async def test_creates_batch_targeting_contextualized_endpoint(self) -> None:
        server = _ContextBatchServer()
        embedder = _make_context_batch_embedder(server.transport())
        await embedder.submit_batch_document_chunks([DOC_SINGLE], [DOC_IDS_2[0]])
        body = server.batch_create_bodies[0]
        assert body["endpoint"] == "/v1/contextualizedembeddings"
        assert body["completion_window"] == DEFAULT_COMPLETION_WINDOW
        assert body["request_params"]["model"] == CONTEXT_MODEL
        assert body["request_params"]["input_type"] == "document"
        assert body["request_params"]["output_dimension"] == CONTEXT_DIM
        # Pinned ONCE at the batch level (design decision #3) -> the guide's
        # own claim ("used for all requests in the batch") makes this a
        # STRONGER guarantee than a per-line pin: a provider-side default
        # flip cannot affect any line in the job.
        assert body["request_params"]["enable_auto_chunking"] is False

    async def test_sends_bearer_authorization_on_every_leg(self) -> None:
        server = _ContextBatchServer(polls_before_terminal=1)
        embedder = _make_context_batch_embedder(server.transport())
        job_id = await embedder.submit_batch_document_chunks([DOC_SINGLE], [DOC_IDS_2[0]])
        await embedder.await_batch_completion(job_id, sleep_fn=_instant_sleep)
        await embedder.fetch_batch_results(job_id)
        assert len(server.seen_auth_headers) >= 4
        assert all(header == f"Bearer {API_KEY}" for header in server.seen_auth_headers)

    async def test_rejects_mismatched_ids_length_before_any_network_call(self) -> None:
        server = _ContextBatchServer()
        embedder = _make_context_batch_embedder(server.transport())
        with pytest.raises(ValueError):
            await embedder.submit_batch_document_chunks([DOC_RUNBOOK, DOC_POLICY], DOC_IDS_2[:-1])
        assert server.files == {}

    async def test_rejects_empty_batch_before_any_network_call(self) -> None:
        server = _ContextBatchServer()
        embedder = _make_context_batch_embedder(server.transport())
        with pytest.raises(ValueError):
            await embedder.submit_batch_document_chunks([], [])
        assert server.files == {}

    async def test_rejects_duplicate_ids_before_any_network_call(self) -> None:
        server = _ContextBatchServer()
        embedder = _make_context_batch_embedder(server.transport())
        duplicate_ids = [DOC_IDS_2[0], DOC_IDS_2[0]]
        with pytest.raises(DuplicateBatchIdError):
            await embedder.submit_batch_document_chunks([DOC_RUNBOOK, DOC_POLICY], duplicate_ids)
        assert server.files == {}


class TestFactoryBatchCapabilitySurvivesConfig:
    """Design decision 7: no new EmbeddingConfig fields; supports_batch alone
    is pinned to survive the config-only construction seam, mirroring
    ``test_factory_voyage_context.py``'s capability-survives-factory pattern.
    """

    def test_factory_built_voyage_cloud_embedder_advertises_batch_support(self) -> None:
        from loresigil.factory import EmbeddingConfig, make_embedder

        env_name = "LORE_VOYAGE_BATCH_CLOUD_KEY_TEST"
        os.environ[env_name] = API_KEY
        try:
            config = EmbeddingConfig(backend="voyage-cloud", api_key_env=env_name)
            embedder = make_embedder(config)
            assert embedder.supports_batch is True
        finally:
            del os.environ[env_name]

    def test_factory_built_voyage_context_embedder_advertises_batch_support(self) -> None:
        from loresigil.factory import EmbeddingConfig, make_embedder

        env_name = "LORE_VOYAGE_BATCH_CONTEXT_KEY_TEST"
        os.environ[env_name] = API_KEY
        try:
            config = EmbeddingConfig(backend="voyage-context", api_key_env=env_name)
            embedder = make_embedder(config)
            assert embedder.supports_batch is True
        finally:
            del os.environ[env_name]


# ── 5/6. Lifecycle, partial/whole failure, usage conservation ───────────────


class TestVoyageCloudBatchLifecycleAndResults:
    """Flat arm: submitted -> in_progress -> completed; results by stable id."""

    async def test_get_batch_status_reports_in_progress_before_terminal(self) -> None:
        server = _CloudBatchServer(polls_before_terminal=5)
        embedder = _make_cloud_batch_embedder(server.transport())
        job_id = await embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS)
        assert await embedder.get_batch_status(job_id) == STATUS_IN_PROGRESS

    async def test_await_batch_completion_sleeps_only_between_polls(self) -> None:
        server = _CloudBatchServer(polls_before_terminal=3)
        embedder = _make_cloud_batch_embedder(server.transport())
        job_id = await embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS)
        sleeps: list[float] = []

        async def recording_sleep(delay: float) -> None:
            sleeps.append(delay)

        started = time.monotonic()
        final_status = await embedder.await_batch_completion(job_id, sleep_fn=recording_sleep)
        elapsed = time.monotonic() - started
        assert final_status == STATUS_COMPLETED
        # 3 polls needed to reach terminal -> exactly 2 BRIDGING sleeps, never
        # a trailing one after the terminal poll.
        assert len(sleeps) == 2
        assert all(delay == DEFAULT_POLL_INTERVAL_S for delay in sleeps)
        # Proves the injected fake sleep really replaced a real poll wait.
        assert elapsed < FAKE_SLEEP_WALL_BUDGET_S

    async def test_results_are_content_correct_and_order_independent(self) -> None:
        server = _CloudBatchServer(polls_before_terminal=1)
        embedder = _make_cloud_batch_embedder(server.transport())
        job_id = await embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS)
        await embedder.await_batch_completion(job_id, sleep_fn=_instant_sleep)
        # Sanity: the fixture server really did reorder its own output file
        # relative to submission — proves this exercises the real seam, not
        # a coincidentally-correct positional pass-through.
        output_file_id = server.jobs[job_id]["output_file_id"]
        served_ids = [line["custom_id"] for line in _jsonl_lines(server.files[output_file_id])]
        assert served_ids != FLAT_IDS
        assert sorted(served_ids) == sorted(FLAT_IDS)

        results = await embedder.fetch_batch_results(job_id)
        assert set(results.keys()) == set(FLAT_IDS)
        for text, id_ in zip(FLAT_TEXTS, FLAT_IDS, strict=True):
            vector = results[id_]
            assert vector is not None
            assert vector == _unit_vector_for_text(text, CLOUD_DIM)
            assert math.hypot(*vector) == pytest.approx(1.0, abs=NORM_TOLERANCE)

    async def test_partial_per_item_failure_maps_failed_id_to_none(self) -> None:
        failed_id = FLAT_IDS[1]  # middle slot — catches an off-by-one remap
        server = _CloudBatchServer(polls_before_terminal=1, failed_ids=frozenset({failed_id}))
        embedder = _make_cloud_batch_embedder(server.transport())
        job_id = await embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS)
        await embedder.await_batch_completion(job_id, sleep_fn=_instant_sleep)
        results = await embedder.fetch_batch_results(job_id)
        # Existing None-vector convention, extended to whole-line grain.
        assert results[failed_id] is None
        # Successes still returned for the OTHER ids, unpoisoned.
        for text, id_ in zip(FLAT_TEXTS, FLAT_IDS, strict=True):
            if id_ == failed_id:
                continue
            assert results[id_] == _unit_vector_for_text(text, CLOUD_DIM)

    async def test_whole_job_failure_raises_naming_the_job_id(self) -> None:
        server = _CloudBatchServer(polls_before_terminal=1, terminal_status=STATUS_FAILED)
        embedder = _make_cloud_batch_embedder(server.transport())
        job_id = await embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS)
        with pytest.raises(BatchJobFailedError) as exc_info:
            await embedder.await_batch_completion(job_id, sleep_fn=_instant_sleep)
        assert job_id in str(exc_info.value)

    async def test_fetch_results_on_a_failed_job_also_raises(self) -> None:
        server = _CloudBatchServer(polls_before_terminal=1, terminal_status=STATUS_FAILED)
        embedder = _make_cloud_batch_embedder(server.transport())
        job_id = await embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS)
        await embedder.get_batch_status(job_id)  # advance the fake to terminal
        with pytest.raises(BatchJobFailedError):
            await embedder.fetch_batch_results(job_id)

    async def test_fetch_results_before_completion_raises(self) -> None:
        # Defense in depth: calling fetch before the job is terminal is
        # caller misuse, not a "job failed"/"size exceeded" case.
        server = _CloudBatchServer(polls_before_terminal=5)
        embedder = _make_cloud_batch_embedder(server.transport())
        job_id = await embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS)
        with pytest.raises(RuntimeError):
            await embedder.fetch_batch_results(job_id)


class TestVoyageContextBatchLifecycleAndResults:
    """Grouped arm: per-doc EmbedResult alignment + exact per-line usage."""

    async def test_results_are_per_doc_aligned_by_content(self) -> None:
        server = _ContextBatchServer(polls_before_terminal=1)
        embedder = _make_context_batch_embedder(server.transport())
        docs = [DOC_RUNBOOK, DOC_POLICY]
        job_id = await embedder.submit_batch_document_chunks(docs, DOC_IDS_2)
        await embedder.await_batch_completion(job_id, sleep_fn=_instant_sleep)

        results = await embedder.fetch_batch_results(job_id)
        assert set(results.keys()) == set(DOC_IDS_2)
        for doc_id, chunks in zip(DOC_IDS_2, docs, strict=True):
            result = results[doc_id]
            assert isinstance(result, EmbedResult)
            assert result.dim == CONTEXT_DIM
            assert len(result.vectors) == len(chunks)
            for vector, chunk in zip(result.vectors, chunks, strict=True):
                assert vector is not None
                assert vector == _unit_vector_for_text(chunk, CONTEXT_DIM)
                assert math.hypot(*vector) == pytest.approx(1.0, abs=NORM_TOLERANCE)
            # Design decision 5: EXACT per-line measurement (one line == one
            # doc), not an attributed split.
            expected_usage = EmbedUsage(total_tokens=sum(_heuristic_tokens(c) for c in chunks))
            assert result.usage == expected_usage

    async def test_usage_conserves_the_whole_job_served_total(self) -> None:
        server = _ContextBatchServer(polls_before_terminal=1)
        embedder = _make_context_batch_embedder(server.transport())
        docs = [DOC_RUNBOOK, DOC_POLICY, DOC_SINGLE]
        job_id = await embedder.submit_batch_document_chunks(docs, DOC_IDS_3)
        await embedder.await_batch_completion(job_id, sleep_fn=_instant_sleep)
        results = await embedder.fetch_batch_results(job_id)
        summed = sum(
            result.usage.total_tokens for result in results.values() if result is not None and result.usage
        )
        # Independent derivation: the SAME mock-provider billing meter used
        # by the fixture server, recomputed here rather than re-read from it.
        expected = sum(_heuristic_tokens(chunk) for doc in docs for chunk in doc)
        assert summed == expected
        assert summed > 0  # sanity: real text bills tokens

    async def test_whole_doc_failure_maps_to_none_without_poisoning_siblings(self) -> None:
        docs = [DOC_RUNBOOK, DOC_POLICY]
        failed_id = DOC_IDS_2[0]
        server = _ContextBatchServer(polls_before_terminal=1, failed_ids=frozenset({failed_id}))
        embedder = _make_context_batch_embedder(server.transport())
        job_id = await embedder.submit_batch_document_chunks(docs, DOC_IDS_2)
        await embedder.await_batch_completion(job_id, sleep_fn=_instant_sleep)
        results = await embedder.fetch_batch_results(job_id)
        assert results[failed_id] is None
        sibling = results[DOC_IDS_2[1]]
        assert isinstance(sibling, EmbedResult)
        assert all(vector is not None for vector in sibling.vectors)

    async def test_whole_job_failure_raises_naming_the_job_id(self) -> None:
        server = _ContextBatchServer(polls_before_terminal=1, terminal_status=STATUS_FAILED)
        embedder = _make_context_batch_embedder(server.transport())
        job_id = await embedder.submit_batch_document_chunks([DOC_SINGLE], [DOC_IDS_2[0]])
        with pytest.raises(BatchJobFailedError) as exc_info:
            await embedder.await_batch_completion(job_id, sleep_fn=_instant_sleep)
        assert job_id in str(exc_info.value)


# ── 5. Resumability (crash recovery) ─────────────────────────────────────────


class TestVoyageCloudBatchResumability:
    async def test_new_instance_reattaches_to_job_id_and_fetches_same_results(self) -> None:
        server = _CloudBatchServer(polls_before_terminal=1)
        submitting_embedder = _make_cloud_batch_embedder(server.transport())
        job_id = await submitting_embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS)
        await submitting_embedder.await_batch_completion(job_id, sleep_fn=_instant_sleep)
        original_results = await submitting_embedder.fetch_batch_results(job_id)
        del submitting_embedder  # simulate the submitting process exiting

        # A BRAND NEW instance, sharing only the transport's backing server
        # state (standing in for the real Voyage account/credentials) and the
        # externally-persisted job_id — never any in-memory submission state.
        resumed_embedder = _make_cloud_batch_embedder(server.transport())
        assert await resumed_embedder.get_batch_status(job_id) == STATUS_COMPLETED
        resumed_results = await resumed_embedder.fetch_batch_results(job_id)
        assert resumed_results == original_results


class TestVoyageContextBatchResumability:
    async def test_new_instance_reattaches_to_job_id_and_fetches_same_results(self) -> None:
        server = _ContextBatchServer(polls_before_terminal=1)
        docs = [DOC_RUNBOOK, DOC_POLICY]
        submitting_embedder = _make_context_batch_embedder(server.transport())
        job_id = await submitting_embedder.submit_batch_document_chunks(docs, DOC_IDS_2)
        await submitting_embedder.await_batch_completion(job_id, sleep_fn=_instant_sleep)
        original_results = await submitting_embedder.fetch_batch_results(job_id)
        del submitting_embedder

        resumed_embedder = _make_context_batch_embedder(server.transport())
        assert await resumed_embedder.get_batch_status(job_id) == STATUS_COMPLETED
        resumed_results = await resumed_embedder.fetch_batch_results(job_id)
        assert resumed_results == original_results


# ── 7. Vector-parity drift alarm ─────────────────────────────────────────────


class TestBatchRealtimeVectorParity:
    """Batch and realtime arms must embed IDENTICAL text into IDENTICAL vectors.

    Both paths, at the fake level, are driven through the SAME deterministic
    hash-of-text oracle (``_unit_vector_for_text``) but via ENTIRELY
    DIFFERENT request/response plumbing (one POST vs upload+create+poll+
    download). A batch-path bug that drops, reorders, truncates, or
    mis-maps an id would surface here as a VALUE mismatch against the
    realtime path — never as a shape/tautology check against the batch
    implementation's own formula.
    """

    async def test_cloud_arm_batch_and_realtime_vectors_match(self) -> None:
        server = _CloudBatchServer(polls_before_terminal=1)
        embedder = _make_cloud_batch_embedder(server.transport())

        realtime_result = await embedder.embed_documents(FLAT_TEXTS)
        job_id = await embedder.submit_batch_documents(FLAT_TEXTS, FLAT_IDS)
        await embedder.await_batch_completion(job_id, sleep_fn=_instant_sleep)
        batch_results = await embedder.fetch_batch_results(job_id)

        for id_, realtime_vector in zip(FLAT_IDS, realtime_result.vectors, strict=True):
            assert realtime_vector is not None
            assert batch_results[id_] == realtime_vector

    async def test_context_arm_batch_and_realtime_vectors_match(self) -> None:
        server = _ContextBatchServer(polls_before_terminal=1)
        embedder = _make_context_batch_embedder(server.transport())
        docs = [DOC_RUNBOOK, DOC_POLICY]

        realtime_results = await embedder.embed_document_chunks(docs)
        job_id = await embedder.submit_batch_document_chunks(docs, DOC_IDS_2)
        await embedder.await_batch_completion(job_id, sleep_fn=_instant_sleep)
        batch_results = await embedder.fetch_batch_results(job_id)

        for doc_id, realtime_result in zip(DOC_IDS_2, realtime_results, strict=True):
            batch_result = batch_results[doc_id]
            assert isinstance(batch_result, EmbedResult)
            assert batch_result.vectors == realtime_result.vectors


class TestBatchRealtimeLiveParitySmoke:
    """Best-effort LIVE smoke: real Voyage batch vs real Voyage realtime.

    Skipped entirely unless ``VOYAGE_API_KEY`` is set — the ONE test in this
    file allowed to touch the network. A real batch job may legally take up
    to the full 12h completion window, so this also self-skips (never
    fails/hangs a run) if the job has not completed within a short polling
    budget: it is a manual/opportunistic check, not a CI gate.
    """

    LIVE_POLL_BUDGET_S: float = 30.0
    LIVE_POLL_INTERVAL_S: float = 5.0

    @pytest.mark.skipif(
        not os.environ.get("VOYAGE_API_KEY"),
        reason="requires a real VOYAGE_API_KEY in the environment; never runs in CI",
    )
    async def test_live_batch_and_realtime_vectors_agree(self) -> None:
        api_key = os.environ["VOYAGE_API_KEY"]
        embedder = VoyageCloudEmbedder(api_key=api_key)
        text = DOC_POLICY[1]
        doc_id = _stable_id(f"live-parity-smoke:{text}")

        realtime_result = await embedder.embed_documents([text])
        job_id = await embedder.submit_batch_documents([text], [doc_id])

        deadline = time.monotonic() + self.LIVE_POLL_BUDGET_S
        status = await embedder.get_batch_status(job_id)
        while status not in TERMINAL_BATCH_STATUSES and time.monotonic() < deadline:
            await asyncio.sleep(self.LIVE_POLL_INTERVAL_S)
            status = await embedder.get_batch_status(job_id)
        if status != STATUS_COMPLETED:
            pytest.skip(
                f"live batch job {job_id} did not complete within the smoke "
                f"budget (status={status!r}); batch jobs may legally take up "
                f"to 12h, this is a best-effort check, not a CI gate"
            )

        batch_results = await embedder.fetch_batch_results(job_id)
        realtime_vector = realtime_result.vectors[0]
        batch_vector = batch_results[doc_id]
        assert realtime_vector is not None
        assert batch_vector is not None
        # Cosine similarity, not exact equality: the SAME model may carry
        # negligible cross-request floating-point drift on the live service.
        cosine = sum(a * b for a, b in zip(realtime_vector, batch_vector, strict=True))
        assert cosine == pytest.approx(1.0, abs=1e-3)
