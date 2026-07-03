"""Shared Voyage AI Files + Batches API plumbing (asynchronous Batch Inference).

Common to both hosted Voyage backends (:class:`~loresigil.voyage_cloud.VoyageCloudEmbedder`
and :class:`~loresigil.voyage_context.VoyageContextEmbedder`): uploading a JSONL
batch input file via the Files API, creating/polling a batch job via the Batches
API, and downloading/parsing its result files. The ``/v1/embeddings`` vs
``/v1/contextualizedembeddings`` request/response SHAPE differences (what one
JSONL line's ``body`` looks like, how a successful line's ``response.body`` is
read back into a vector) stay in each backend — exactly the separation of
concerns :mod:`loresigil.voyage_http` already uses for the realtime bearer-client
builder.

Ground truth (fetched 2026-07-03 from docs.voyageai.com/docs/batch-inference,
the "Batch Inference" guide page — see ``test_voyage_batch.py``'s module
docstring for the verbatim citations this module's constants and shapes rely
on).

Design highlights (see the contract test's module docstring for the full
rationale):

* Results are always retrieved by caller-supplied ``custom_id``, never by
  output-line position — the guide explicitly disclaims output-line ordering.
* One JSONL line per input unit (one text, or one document's chunk group).
* Batch-level parameters (``model``/``input_type``/``output_dimension``/
  ``enable_auto_chunking``) travel once in ``request_params`` at batch
  creation, never per-line.
* A whole-line failure (from the batch's error file) maps its id to ``None``;
  a whole-job failure (terminal status other than ``"completed"``) raises
  :class:`BatchJobFailedError` naming the job id.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Iterator
from typing import Any

import httpx

from loresigil.resilient import SleepFn

# ── Files/Batches endpoints (fixed, documented URLs — no deployment-specific
# configuration exists yet; see the contract's design decision 7). ──────────
DEFAULT_FILES_API_URL: str = "https://api.voyageai.com/v1/files"
DEFAULT_BATCHES_API_URL: str = "https://api.voyageai.com/v1/batches"

# "Our Batch API offers a 12-hour completion window" — the only value the
# guide's create-batch example ever sends.
DEFAULT_COMPLETION_WINDOW: str = "12h"

# A real batch job may legally take up to 12h to complete; polling every few
# seconds would be needless load. 30s keeps a caller responsive to a job that
# finishes early without hammering the endpoint.
DEFAULT_POLL_INTERVAL_S: float = 30.0

# "100K inputs per batch maximum" (stated twice in the guide, once per section).
MAX_BATCH_INPUTS: int = 100_000

# See the contract test's "DOCS CROSS-CHECK FLAG": carried over from the task
# brief's prior spike ground truth as a defensive byte cap; not independently
# re-confirmed by the anonymously-fetchable guide text this session pulled.
MAX_BATCH_FILE_BYTES: int = 1_073_741_824

# Batch lifecycle table (guide): validating -> failed | in_progress ->
# finalizing -> completed | cancelling -> cancelled.
STATUS_VALIDATING: str = "validating"
STATUS_IN_PROGRESS: str = "in_progress"
STATUS_FINALIZING: str = "finalizing"
STATUS_COMPLETED: str = "completed"
STATUS_FAILED: str = "failed"
STATUS_CANCELLING: str = "cancelling"
STATUS_CANCELLED: str = "cancelled"
TERMINAL_BATCH_STATUSES: frozenset[str] = frozenset({STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED})

# The upload's multipart purpose/filename fields (the guide's own
# ``-F purpose="batch" -F file="@foo.jsonl"`` example).
_UPLOAD_PURPOSE: str = "batch"
_UPLOAD_FILENAME: str = "batch_input.jsonl"
_UPLOAD_CONTENT_TYPE: str = "application/jsonl"

# HTTP status a batch output line's nested ``response.status_code`` carries
# for a successfully-embedded input.
_HTTP_OK: int = 200


class BatchSizeExceededError(ValueError):
    """Raised when a batch JSONL would exceed the line-count or byte-size cap."""


class BatchJobFailedError(RuntimeError):
    """Raised when a batch job's terminal status is not ``"completed"``.

    Names the job id so an operator can look the job up directly (via the
    Voyage dashboard/API) without re-deriving it from the call site.
    """


class DuplicateBatchIdError(ValueError):
    """Raised when two inputs share the same ``custom_id`` in one batch."""


def encode_batch_jsonl(
    ids: list[str],
    bodies: list[dict[str, Any]],
    *,
    max_inputs: int = MAX_BATCH_INPUTS,
    max_bytes: int = MAX_BATCH_FILE_BYTES,
) -> bytes:
    """Build a batch input JSONL file: one ``{"custom_id": id, "body": body}`` line per pair.

    Pure and offline — no network access. ``ids``/``bodies`` are encoded in
    the given order (the guide disclaims OUTPUT order, never input order).

    Args:
        ids: Caller-supplied stable ids, 1:1 with ``bodies``. Become each
            line's ``custom_id`` — the key results are later returned under.
        bodies: Each line's endpoint-specific request body (``{"input": [...]}``
            for ``/v1/embeddings``, ``{"inputs": [[...]]}`` for
            ``/v1/contextualizedembeddings``), opaque to this function.
        max_inputs: Maximum number of lines allowed (injectable so a cheap
            test never has to allocate the real 100K-line default).
        max_bytes: Maximum encoded byte size allowed (injectable for the
            same reason).

    Returns:
        The encoded JSONL file content, newline-terminated.

    Raises:
        ValueError: ``ids``/``bodies`` length mismatch, or both are empty.
        DuplicateBatchIdError: A repeated id (named in the message).
        BatchSizeExceededError: The line count or encoded byte size exceeds
            its cap (both the actual value and the cap are named).
    """
    if len(ids) != len(bodies):
        raise ValueError(f"ids length {len(ids)} does not match bodies length {len(bodies)}")
    if not ids:
        raise ValueError("encode_batch_jsonl requires at least one (id, body) pair")

    seen_ids: set[str] = set()
    for custom_id in ids:
        if custom_id in seen_ids:
            raise DuplicateBatchIdError(f"duplicate batch custom_id: {custom_id!r}")
        seen_ids.add(custom_id)

    if len(ids) > max_inputs:
        raise BatchSizeExceededError(
            f"batch line count {len(ids)} exceeds the maximum of {max_inputs} inputs per batch"
        )

    encoded = (
        b"\n".join(
            json.dumps({"custom_id": custom_id, "body": body}).encode()
            for custom_id, body in zip(ids, bodies, strict=True)
        )
        + b"\n"
    )
    if len(encoded) > max_bytes:
        raise BatchSizeExceededError(
            f"encoded batch size {len(encoded)} bytes exceeds the maximum of {max_bytes} bytes"
        )
    return encoded


def _iter_jsonl(raw: bytes) -> Iterator[dict[str, Any]]:
    """Yield parsed JSON objects from JSONL bytes, skipping blank lines."""
    for line in raw.decode().splitlines():
        if line:
            yield json.loads(line)


def parse_batch_output_lines(raw: bytes) -> dict[str, dict[str, Any]]:
    """Parse a batch OUTPUT file into ``{custom_id: response body}``.

    Only successfully-embedded (``response.status_code == 200``) lines are
    included; a failed input's line lives in the batch's separate ERROR file
    instead (see :func:`parse_batch_failed_ids`) — a batch job never mixes
    the two shapes within one file.

    Args:
        raw: The downloaded output file's raw bytes.

    Returns:
        A mapping from each successful line's ``custom_id`` to its wire
        ``response.body`` — byte-identical in shape to the realtime response
        body for the same endpoint, per the guide.
    """
    bodies: dict[str, dict[str, Any]] = {}
    for line in _iter_jsonl(raw):
        response = line.get("response")
        if response is not None and response.get("status_code") == _HTTP_OK and "body" in response:
            bodies[line["custom_id"]] = response["body"]
    return bodies


def parse_batch_failed_ids(raw: bytes) -> frozenset[str]:
    """Parse a batch ERROR file into the set of ``custom_id``s that failed.

    Tolerates both documented error-line shapes (a non-2xx ``response`` with
    a ``message``, or a top-level ``error`` object with ``code``/``message``)
    — both carry the ``custom_id`` this parser needs; the failure detail
    itself is not surfaced further (the caller maps the id straight to
    ``None``, the same sentinel convention a permanently-failed realtime
    input already uses).

    Args:
        raw: The downloaded error file's raw bytes.

    Returns:
        The set of ids the batch job could not embed.
    """
    return frozenset(line["custom_id"] for line in _iter_jsonl(raw))


class VoyageBatchClient:
    """Thin async wrapper around the Voyage Files + Batches HTTP endpoints.

    Holds no submission state of its own — every method is keyed by a
    provider-assigned id (``file_id``/``job_id``) so a brand-new instance
    (sharing only the bearer-authenticated ``httpx.AsyncClient`` and the
    externally-persisted ``job_id``) can resume a job a prior process
    submitted, which is what makes batch submission crash-recoverable.
    """

    def __init__(
        self,
        client: httpx.AsyncClient,
        files_api_url: str = DEFAULT_FILES_API_URL,
        batches_api_url: str = DEFAULT_BATCHES_API_URL,
        completion_window: str = DEFAULT_COMPLETION_WINDOW,
    ) -> None:
        """Configure the batch client.

        Args:
            client: A bearer-authenticated ``httpx.AsyncClient`` (built by
                :func:`~loresigil.voyage_http.build_bearer_client`) shared
                with the owning embedder's realtime requests.
            files_api_url: Full Files API base URL.
            batches_api_url: Full Batches API base URL.
            completion_window: The batch's requested completion window —
                fixed at the guide's only documented value.
        """
        self._client = client
        self._files_api_url = files_api_url
        self._batches_api_url = batches_api_url
        self._completion_window = completion_window

    async def upload_input_file(self, jsonl_bytes: bytes) -> str:
        """Upload a batch input JSONL file via the Files API.

        Args:
            jsonl_bytes: The encoded JSONL content (see :func:`encode_batch_jsonl`).

        Returns:
            The provider-assigned file id.
        """
        response = await self._client.post(
            self._files_api_url,
            data={"purpose": _UPLOAD_PURPOSE},
            files={"file": (_UPLOAD_FILENAME, jsonl_bytes, _UPLOAD_CONTENT_TYPE)},
        )
        response.raise_for_status()
        file_id: str = response.json()["id"]
        return file_id

    async def create_batch(self, endpoint: str, input_file_id: str, request_params: dict[str, Any]) -> str:
        """Create a batch job targeting ``endpoint``.

        Args:
            endpoint: The endpoint path the batch job runs against (e.g.
                ``"/v1/embeddings"``).
            input_file_id: The uploaded input file's id.
            request_params: Endpoint parameters applied to every line in the
                job (``model``/``input_type``/``output_dimension``/etc.) —
                sent ONCE here, never per-line.

        Returns:
            The provider-assigned batch job id.
        """
        response = await self._client.post(
            self._batches_api_url,
            json={
                "endpoint": endpoint,
                "completion_window": self._completion_window,
                "input_file_id": input_file_id,
                "request_params": request_params,
            },
        )
        response.raise_for_status()
        job_id: str = response.json()["id"]
        return job_id

    async def get_batch(self, job_id: str) -> dict[str, Any]:
        """Fetch the raw batch job object.

        Args:
            job_id: The batch job id.

        Returns:
            The parsed JSON batch object (``id``/``status``/``output_file_id``/
            ``error_file_id``).
        """
        response = await self._client.get(f"{self._batches_api_url}/{job_id}")
        response.raise_for_status()
        batch: dict[str, Any] = response.json()
        return batch

    async def download_file(self, file_id: str) -> bytes:
        """Download a file's raw content via the Files API.

        Args:
            file_id: The file id (an input, output, or error file).

        Returns:
            The file's raw bytes.
        """
        response = await self._client.get(f"{self._files_api_url}/{file_id}/content")
        response.raise_for_status()
        return response.content

    async def get_status(self, job_id: str) -> str:
        """Return a batch job's current lifecycle status."""
        batch = await self.get_batch(job_id)
        status: str = batch["status"]
        return status

    async def await_completion(
        self,
        job_id: str,
        *,
        poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
        sleep_fn: SleepFn | None = None,
    ) -> str:
        """Poll a batch job until it reaches a terminal status.

        Sleeps only BETWEEN polls — a status already terminal on the first
        check returns immediately, and a status discovered terminal after a
        poll never pays a trailing sleep it would not use.

        Args:
            job_id: The batch job id.
            poll_interval_s: Delay between polls.
            sleep_fn: Awaitable sleep used between polls; defaults to
                ``asyncio.sleep`` (injected in tests so polling doesn't block
                the suite) — the same seam convention
                :class:`~loresigil.resilient.ResilientEmbedder` uses for
                backoff.

        Returns:
            The terminal status (always ``STATUS_COMPLETED`` — any other
            terminal status raises instead).

        Raises:
            BatchJobFailedError: If the terminal status is not ``"completed"``,
                naming the job id.
        """
        sleep = sleep_fn or asyncio.sleep
        status = await self.get_status(job_id)
        while status not in TERMINAL_BATCH_STATUSES:
            await sleep(poll_interval_s)
            status = await self.get_status(job_id)
        if status != STATUS_COMPLETED:
            raise BatchJobFailedError(f"batch job {job_id} ended in terminal status {status!r}")
        return status

    async def fetch_result_files(self, job_id: str) -> tuple[bytes | None, bytes | None]:
        """Validate a job is completed and return its ``(output, error)`` file bytes.

        Args:
            job_id: The batch job id.

        Returns:
            ``(output_bytes, error_bytes)`` — either may be ``None`` when the
            job produced no such file (e.g. a job with zero failures has no
            error file).

        Raises:
            RuntimeError: If the job has not yet reached a terminal status
                (caller misuse — poll or await completion first).
            BatchJobFailedError: If the job's terminal status is not
                ``"completed"``, naming the job id.
        """
        batch = await self.get_batch(job_id)
        status = batch["status"]
        if status not in TERMINAL_BATCH_STATUSES:
            raise RuntimeError(
                f"batch job {job_id} has not reached a terminal status yet (status={status!r})"
            )
        if status != STATUS_COMPLETED:
            raise BatchJobFailedError(f"batch job {job_id} ended in terminal status {status!r}")

        output_file_id = batch.get("output_file_id")
        error_file_id = batch.get("error_file_id")
        output_bytes = await self.download_file(output_file_id) if output_file_id else None
        error_bytes = await self.download_file(error_file_id) if error_file_id else None
        return output_bytes, error_bytes
