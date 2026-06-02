#!/usr/bin/env python3
"""Hard-probe the embedding ``/embed`` endpoint for a lore deploy.

A RAG server with an unreachable or wrong-dimension embedder is useless, so the
``setup`` and ``start`` verbs probe *before* indexing or launching the
container. The probe is deliberately strict (Unix philosophy: silent-ish on
success, loud on failure):

* unreachable / timeout / 5xx → exit 2 (with a remediation message on stderr);
* observed dimension ≠ ``--expect-dim`` → exit 3;
* success → print the observed dimension to stdout and exit 0.

The endpoint warms up slowly at fp32 (~20–40 s after a (re)start), so the probe
polls ``/health`` first (bounded), then issues one real ``/embed`` to read the
live dimension. The bearer key is read from the environment variable named by
``--api-key-env`` (never inlined) — the same env-ref convention the config uses.

This uses only the Python standard library so it runs anywhere (host or
container) without the loremaster venv.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

# A tiny sentinel input — its embedding's length is the live dimension.
_PROBE_SENTINEL = "probe"
# Exit codes (distinct so the caller can branch on the failure mode).
_EXIT_OK = 0
_EXIT_UNREACHABLE = 2
_EXIT_WRONG_DIM = 3
_EXIT_BAD_USAGE = 4


def _build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser for the embed probe."""
    parser = argparse.ArgumentParser(
        prog="probe_embed",
        description="Hard-probe the lore embedding /embed endpoint (dim + reachability).",
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Embedding service base URL, e.g. http://localhost:8080",
    )
    parser.add_argument(
        "--endpoint", default="/embed", help="Embed endpoint path (default: /embed)."
    )
    parser.add_argument(
        "--api-key-env",
        required=True,
        help="Name of the env var holding the bearer key (never the key itself).",
    )
    parser.add_argument(
        "--expect-dim",
        type=int,
        required=True,
        help="The dimension the deploy expects (config.dim). Mismatch → exit 3.",
    )
    parser.add_argument(
        "--health-timeout-s",
        type=float,
        default=60.0,
        help="Total seconds to poll /health for fp32 warmup before giving up.",
    )
    parser.add_argument(
        "--connect-timeout-s",
        type=float,
        default=5.0,
        help="Per-request timeout for the probe.",
    )
    return parser


def _resolve_key(api_key_env: str) -> str:
    """Read the bearer key from the named env var, failing loud if unset/empty."""
    key = os.environ.get(api_key_env)
    if not key:
        print(
            f"probe_embed: secret env var {api_key_env!r} is unset or empty; "
            f"export it (via the deploy --env-file) before probing.",
            file=sys.stderr,
        )
        sys.exit(_EXIT_BAD_USAGE)
    return key


def _poll_health(base_url: str, key: str, total_s: float, per_req_s: float) -> bool:
    """Poll ``{base_url}/health`` until it returns 200 or ``total_s`` elapses.

    Returns ``True`` once healthy, ``False`` if the budget is exhausted. A
    missing /health (404) is treated as "no health route" → proceed to the embed
    probe (some servers omit it).
    """
    deadline = time.monotonic() + total_s
    url = base_url.rstrip("/") + "/health"
    while time.monotonic() < deadline:
        request = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}"})
        try:
            with urllib.request.urlopen(request, timeout=per_req_s) as response:
                if response.status == 200:
                    return True
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return True  # no health route — proceed to the embed probe
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(2.0)
    return False


def _observe_dim(base_url: str, endpoint: str, key: str, per_req_s: float) -> int:
    """Issue one /embed and return the observed vector dimension.

    Exits with ``_EXIT_UNREACHABLE`` on any transport/HTTP/parse failure.
    """
    url = base_url.rstrip("/") + endpoint
    body = json.dumps({"inputs": [_PROBE_SENTINEL]}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=per_req_s) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError) as error:
        print(
            f"probe_embed: /embed at {url} unreachable or errored: {error}",
            file=sys.stderr,
        )
        sys.exit(_EXIT_UNREACHABLE)
    except (json.JSONDecodeError, ValueError) as error:
        print(f"probe_embed: /embed returned unparseable body: {error}", file=sys.stderr)
        sys.exit(_EXIT_UNREACHABLE)

    # TEI native returns a bare [[float, ...], ...]; tolerate the OpenAI shape too.
    vector = None
    if isinstance(payload, list) and payload and isinstance(payload[0], list):
        vector = payload[0]
    elif isinstance(payload, dict) and isinstance(payload.get("data"), list):
        first = payload["data"][0] if payload["data"] else None
        if isinstance(first, dict):
            vector = first.get("embedding")
    if not isinstance(vector, list) or not vector:
        print(
            f"probe_embed: could not locate an embedding vector in the response shape.",
            file=sys.stderr,
        )
        sys.exit(_EXIT_UNREACHABLE)
    return len(vector)


def main(argv: list[str] | None = None) -> int:
    """Probe the endpoint; print the observed dim on success, exit loud on failure."""
    args = _build_parser().parse_args(argv)
    key = _resolve_key(args.api_key_env)

    if not _poll_health(args.base_url, key, args.health_timeout_s, args.connect_timeout_s):
        print(
            f"probe_embed: {args.base_url}/health did not become ready within "
            f"{args.health_timeout_s}s — embedder unreachable. Refusing to proceed.",
            file=sys.stderr,
        )
        return _EXIT_UNREACHABLE

    observed = _observe_dim(args.base_url, args.endpoint, key, args.connect_timeout_s)
    if observed != args.expect_dim:
        print(
            f"probe_embed: DIMENSION MISMATCH — endpoint returned dim {observed}, "
            f"config.dim is {args.expect_dim}. Refusing to index (a wrong-dim index "
            f"silently corrupts retrieval). Fix the config or the embedder backend.",
            file=sys.stderr,
        )
        return _EXIT_WRONG_DIM

    print(observed)  # the one success-path stdout line: the verified dimension
    return _EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
