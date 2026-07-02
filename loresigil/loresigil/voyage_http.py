"""Low-level HTTP plumbing shared by the hosted Voyage AI backends.

Both :class:`~loresigil.voyage_cloud.VoyageCloudEmbedder` and
:class:`~loresigil.voyage_context.VoyageContextEmbedder` talk to
``api.voyageai.com`` with an IDENTICAL bearer-auth transport shape; this
module holds the one piece of plumbing that is genuinely shared between them.
Everything else — request/response shape, retry orchestration — differs
enough (flat vs. document-grouped inputs) that unifying it would obscure more
than it would save, so it stays in each backend.
"""

from __future__ import annotations

import httpx

# Generous HTTP timeout: a near-cap request can cost tens of seconds on the
# live Voyage endpoints (both cloud and contextualized share this budget).
DEFAULT_REQUEST_TIMEOUT_S: float = 120.0


def build_bearer_client(
    api_key: str,
    transport: httpx.AsyncBaseTransport | None,
    timeout: float = DEFAULT_REQUEST_TIMEOUT_S,
) -> httpx.AsyncClient:
    """Build an ``httpx.AsyncClient`` carrying a bearer ``Authorization`` header.

    Args:
        api_key: Bearer token baked into the client's headers. It is not
            retained by the caller afterward — needless secret surface
            otherwise.
        transport: Optional httpx transport (an offline ``MockTransport`` in
            tests); when ``None`` a real networked client is built.
        timeout: Per-request timeout in seconds.

    Returns:
        A configured, ready-to-use ``httpx.AsyncClient``.
    """
    return httpx.AsyncClient(
        timeout=timeout,
        transport=transport,
        headers={"Authorization": f"Bearer {api_key}"},
    )
