"""Shared fixtures for loremaster tests, including the REAL-Qdrant harness.

The store tests run against the **real local Qdrant server** (not ``:memory:``)
because the C1 fix is about server-side behaviour: payload indexes and
filter-based deletes are *no-ops* in the in-memory backend but take real effect
on the server. Proving "two tiers' copies of one path both survive, and
``delete_by_tier`` purges only one" is only meaningful against the real engine.

Connection details:

* URL ``http://127.0.0.1:16333`` (verified up: ``readyz`` 200, ``/collections``
  401 without a key).
* The API key is the ``QDRANT__SERVICE__API_KEY`` entry of
  ``/home/ejprice/docker/mcp/.env``. It is read from that file (never inlined,
  never echoed) by :func:`_qdrant_api_key`.

Each test that needs the store gets a UNIQUE throwaway collection named
``lore_test_<session>_<uuid4>`` (the session token namespaces this pytest
PROCESS) and the teardown deletes only collections under this process's
``lore_test_<session>_*`` prefix — NOT a bare ``lore_test_*`` sweep, which would
delete a concurrent process's in-flight collections on the shared server.
Nothing leaks; nothing nukes a sibling run.
"""

from __future__ import annotations

import os
import sys
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest_asyncio
from qdrant_client import AsyncQdrantClient

# Make sibling test helper modules (e.g. ``_extension_helpers``) importable as
# plain top-level modules under ``--import-mode=importlib``: that mode does NOT
# add each test file's directory to ``sys.path``, and ``loremaster`` is the
# *installed* package (with no ``tests`` subpackage), so neither a bare
# ``_extension_helpers`` nor a ``loremaster.tests._extension_helpers`` import
# would otherwise resolve. Inserting this directory keeps the shared fake
# extension in one reviewable module without polluting the shipped package.
_TESTS_DIR = str(Path(__file__).parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)

# The local Qdrant server the real-corpus tests hit.
QDRANT_URL = "http://127.0.0.1:16333"

# Where the server's API key lives (read, never echoed).
_ENV_FILE = Path("/home/ejprice/docker/mcp/.env")
_QDRANT_KEY_NAME = "QDRANT__SERVICE__API_KEY"

# The prefix every throwaway test collection shares.
TEST_COLLECTION_PREFIX = "lore_test_"

# A token unique to THIS pytest PROCESS, mixed into every collection name this
# process creates. A concurrent pytest process (another worktree's suite on the
# same shared server) gets a different token, so the teardown below — which
# sweeps only THIS process's prefix — can never nuke a sibling's in-flight
# collections. We use the OS PID: it is identical for every module in one
# process and distinct across concurrent processes, so a test module can compute
# the SAME prefix INDEPENDENTLY (``os.getpid()``) without importing this conftest
# — avoiding pytest's importlib double-import (which would hand a test a second
# conftest instance with a mismatched token). This replaces the old global
# ``lore_test_*`` sweep, and a reused PID later harmlessly reaps any prior leak.
_SESSION_TOKEN = str(os.getpid())
SESSION_COLLECTION_PREFIX = f"{TEST_COLLECTION_PREFIX}{_SESSION_TOKEN}_"


def session_slug() -> str:
    """A throwaway slug unique to this process → collection ``lore_test_<session>_<uuid>``.

    Use this (not a bare ``uuid4``) for any collection created through the shared
    ``qdrant_client`` fixture, so the fixture's prefix-scoped teardown matches it
    and a concurrent process's teardown does not.
    """
    return f"test_{_SESSION_TOKEN}_{uuid.uuid4().hex}"


def _qdrant_api_key() -> str:
    """Read the Qdrant API key from the env (process env first, then the file).

    Resolution order: an already-exported ``QDRANT__SERVICE__API_KEY`` wins;
    otherwise the value is parsed out of the dotenv file. The secret is never
    logged or echoed.

    Returns:
        The API key string.

    Raises:
        RuntimeError: If the key cannot be found in either place.
    """
    from_env = os.environ.get(_QDRANT_KEY_NAME)
    if from_env:
        return from_env
    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(f"{_QDRANT_KEY_NAME}="):
                value = stripped.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return value
    raise RuntimeError(
        f"{_QDRANT_KEY_NAME} not found in the environment or {_ENV_FILE}; "
        "the real-Qdrant tests require it."
    )


@pytest_asyncio.fixture()
async def qdrant_client() -> AsyncIterator[AsyncQdrantClient]:
    """An :class:`AsyncQdrantClient` against the real local server.

    Teardown: on exit, deletes only collections under THIS process's
    :data:`SESSION_COLLECTION_PREFIX` (``lore_test_<session>_*``) — never a bare
    ``lore_test_*`` sweep, which would nuke a concurrent pytest process's
    in-flight collections on the shared server. Collections created through this
    fixture must therefore be named via :func:`session_slug` (the ``_unique_slug``
    helper does this) so they carry the session token and are reaped here.
    """
    client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
    try:
        yield client
    finally:
        collections = await client.get_collections()
        for collection in collections.collections:
            if collection.name.startswith(SESSION_COLLECTION_PREFIX):
                await client.delete_collection(collection.name)
        await client.close()
