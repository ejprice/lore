"""Low-level HTTP plumbing shared by the hosted Voyage AI backends.

Both :class:`~loresigil.voyage_cloud.VoyageCloudEmbedder` and
:class:`~loresigil.voyage_context.VoyageContextEmbedder` talk to
``api.voyageai.com`` with an IDENTICAL bearer-auth transport shape; this
module holds the one piece of plumbing that is genuinely shared between them.
Everything else — request/response shape, retry orchestration — differs
enough (flat vs. document-grouped inputs) that unifying it would obscure more
than it would save, so it stays in each backend.

It also holds :func:`build_auth_headers`, ``loresigil``'s ONE typed auth-header
seam (ruling R26) — which the TEI backend imports too, even though that backend
builds its own client. The header string is POLICY, not trivia: it is where the
credential stops being a :class:`~pydantic.SecretStr`, and a second copy is a
second place that decision can silently diverge.
"""

from __future__ import annotations

import httpx
from pydantic import SecretStr

# Generous HTTP timeout: a near-cap request can cost tens of seconds on the
# live Voyage endpoints (both cloud and contextualized share this budget).
DEFAULT_REQUEST_TIMEOUT_S: float = 120.0


def build_auth_headers(credential: SecretStr) -> dict[str, str]:
    """Build the outgoing ``Authorization`` header for a bearer credential.

    **THE TYPED SEAM FOR ``loresigil`` (ruling R26), and the type IS the
    instrument.** Three earlier gates all keyed on NAMES — a credential parameter
    had to be called ``api_key`` or ``password``, an audit had to spot a
    ``.get_secret_value()`` call, a sweep had to find ``"api_key" in parameters``
    — and a class holding a bare ``str`` under any other name walked past all
    three. The set of names a credential can wear is unbounded; the TYPE is not.
    So this signature makes a bare ``str`` a mypy error at every call site
    whatever the caller named its variable, and an ``AttributeError`` at runtime
    if one is forced through anyway.

    ``loremaster`` has a seam of its own rather than importing this one, and that
    is deliberate (ruling R26 constraint 1): ``loresigil`` cannot import
    ``loremaster`` (#222), and **the shared thing is the TYPE, not an
    implementation** — two typed seams are not a DRY violation when what must
    agree is a signature.

    Args:
        credential: The bearer key, still wrapped.

    Returns:
        The ``Authorization`` header carrying the credential's real bytes.
    """
    return {"Authorization": f"Bearer {credential.get_secret_value()}"}


def build_bearer_client(
    api_key: SecretStr,
    transport: httpx.AsyncBaseTransport | None,
    timeout: float = DEFAULT_REQUEST_TIMEOUT_S,
) -> httpx.AsyncClient:
    """Build an ``httpx.AsyncClient`` carrying a bearer ``Authorization`` header.

    Args:
        api_key: Bearer credential, still wrapped. It is unwrapped only inside
            :func:`build_auth_headers` and baked into the client's headers; it is
            not retained by the caller afterward — needless secret surface
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
        headers=build_auth_headers(api_key),
    )
