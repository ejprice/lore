"""Contract — packet 42 steps 1 + 2, loresigil half: the config CARRIES a resolved secret.

**Operator ruling, 2026-07-26 (binding, not re-litigated here):** push secret
resolution UP to the composition root. ``loresigil`` stops resolving. Concretely:

* ``loresigil.factory._resolve_api_key`` is DELETED.
* ``EmbeddingConfig`` loses ``api_key_env: str`` and gains
  ``api_key: SecretStr`` — the key ARRIVES already resolved.
* ``loremaster.embedding.to_loresigil_config`` — the only production translator —
  is the one place that calls ``loremaster.config.resolve_secret``. Its half of
  the contract lives in ``loremaster/tests/test_secret_resolution_seam.py``.

This module is the loresigil half, and it exists to catch ONE wrong build above
all others:

    ``api_key`` becomes a ``SecretStr``, nobody unwraps it at the client seam,
    and every request goes out with ``Authorization: Bearer **********``.

That build type-checks, satisfies every "is it a SecretStr?" pin, and breaks
authentication 100% in production — the exact silhouette of #107. Nothing in the
tree catches it today: measured 2026-07-26 at ``9c08cac``, the ONLY assertions on
an outbound ``Authorization`` header anywhere in ``loresigil/tests`` are two in
``test_voyage_batch.py``, both on directly-constructed embedders and neither on
the TEI arm. ``test_tei.py``'s docstring claims *"Bearer auth on every request"*
and no test checks it.

So :class:`TestEveryBackendPutsTheRealCredentialBytesOnTheWire` drives a REAL
request through ALL THREE backend arms, each built through ``make_embedder`` from
a config carrying a ``SecretStr``, each with a DIFFERENT key value (a build that
hardcodes or caches one arm's key fails), and asserts the header EQUALS the
expected bytes. Equality, not containment: ``KEY in header`` passes for
``Bearer Bearer KEY``.

How to run:
    uv run pytest loresigil/tests/test_factory_secret_resolution.py -n auto -q
"""

from __future__ import annotations

import ast
import json
import math
from pathlib import Path
from typing import Any

import httpx
import pytest
from loresigil.factory import (
    BACKEND_TEI,
    BACKEND_VOYAGE_CLOUD,
    BACKEND_VOYAGE_CONTEXT,
    EmbeddingConfig,
    make_embedder,
)
from loresigil.tei import DEFAULT_DIM as EMBEDDING_DIM
from pydantic import SecretStr, ValidationError

import loresigil

# --------------------------------------------------------------------------- #
# Credential fixtures — one per backend arm, DELIBERATELY DIFFERENT
# --------------------------------------------------------------------------- #
# PARAMETER-VALUE MONOCULTURE is this repo's #1 fixture defect (CLAUDE.md: 37
# call sites all using ``name="project"`` let a build that branched on that one
# value pass an entire contract). Three arms therefore get three keys, so a build
# that resolves once and reuses, or that special-cases the arm its author tested,
# is visible.
#
# Shapes are the real Voyage/TEI bearer families: ``pa-`` + base64url.
TEI_KEY = "pa-T3iK9wQ2mV7bX4nR8yL5jH1dF6sA0cUeZpOiN2tVxYw"
CLOUD_KEY = "pa-C1oU8dK4wM9bV2nT7yR3jL6hF5sA0eZqPiO1tXvYnBw"
CONTEXT_KEY = "pa-X9tK2wN5mB8vC3nQ7yT4jR1hF6sA0dUeZpLiO2tVgYw"

# A key whose REAL bytes carry leading/trailing whitespace. Inventory B4:
# ``_resolve_api_key`` passed the value byte-exact and ``resolve_secret`` never
# strips either, so a key that was pasted with padding must survive to the wire.
# A build that "helpfully" strips would authenticate against a different string.
PADDED_KEY = "  pa-P4dD3dK9wQ2mV7bX4nR8yL5jH1dF6sA0cUeZpOiNw\t"

# The base URL the TEI arm requires. Any absolute URL works; the MockTransport
# never reaches the network.
TEI_BASE_URL = "http://embedder.test:8080"
CLOUD_API_URL = "https://api.voyageai.com/v1/embeddings"
CONTEXT_API_URL = "https://api.voyageai.com/v1/contextualizedembeddings"

# Real warehouse-ops prose, matching the sibling suites' fixture register — the
# embedders token-count their inputs, so a degenerate ``"x"`` exercises a
# different (shorter) path than production text.
DOCUMENT_TEXT = "The quarterly safety report summarizes incident rates across all warehouse facilities."


def _unit_vector(seed: float) -> list[float]:
    """A finite, L2-normalised ``EMBEDDING_DIM`` vector built independently of the impl."""
    raw = [seed + index * 1e-6 for index in range(EMBEDDING_DIM)]
    norm = math.sqrt(sum(component * component for component in raw))
    return [component / norm for component in raw]


class _AuthRecordingServer:
    """One MockTransport serving all three wire shapes, recording every auth header.

    ONE implementation rather than three near-identical recorders (CLAUDE.md,
    ONE IMPLEMENTATION): the shapes differ only in the response envelope, and the
    thing under test — the ``Authorization`` header — is identical across arms, so
    three copies would be three places a future assertion change reaches two of.
    """

    def __init__(self) -> None:
        self.auth_headers: list[str | None] = []

    def transport(self) -> httpx.MockTransport:
        def handler(request: httpx.Request) -> httpx.Response:
            self.auth_headers.append(request.headers.get("authorization"))
            body: dict[str, Any] = json.loads(request.content.decode())
            if "input" in body:  # voyage-cloud: {"input": [str, ...]}
                flat: list[str] = body["input"]
                return httpx.Response(
                    200, json={"data": [{"embedding": _unit_vector(float(i))} for i in range(len(flat))]}
                )
            grouped = body["inputs"]
            if grouped and isinstance(grouped[0], list):  # voyage-context: [[str, ...], ...]
                data = [
                    {
                        "index": doc_index,
                        "data": [
                            {"index": chunk_index, "embedding": _unit_vector(float(chunk_index))}
                            for chunk_index in range(len(chunks))
                        ],
                    }
                    for doc_index, chunks in enumerate(grouped)
                ]
                return httpx.Response(200, json={"data": data, "usage": {"total_tokens": 1}})
            # TEI: {"inputs": [str, ...]} -> a bare [[...]] response.
            return httpx.Response(200, json=[_unit_vector(float(i)) for i in range(len(grouped))])

        return httpx.MockTransport(handler)


def _config_for(backend: str, key: str) -> EmbeddingConfig:
    """Build the loresigil config for ``backend`` carrying ``key`` as a SecretStr.

    Every arm is constructed through the SAME factory seam the composition root
    uses, so a pin here is a statement about production's path, not about a
    directly-constructed embedder (which is what the two pre-existing header
    assertions in ``test_voyage_batch.py`` test, and why they cannot see this
    packet's wrong build).
    """
    fields: dict[str, Any] = {"backend": backend, "api_key": SecretStr(key)}
    if backend == BACKEND_TEI:
        fields["base_url"] = TEI_BASE_URL
    elif backend == BACKEND_VOYAGE_CLOUD:
        fields["api_url"] = CLOUD_API_URL
    else:
        fields["api_url"] = CONTEXT_API_URL
    return EmbeddingConfig(**fields)


# (backend, key) — every arm forced individually. The quantifier law: a property
# derived on one member of the set and stated over the whole set is the defect.
BACKEND_ARMS: list[tuple[str, str]] = [
    (BACKEND_TEI, TEI_KEY),
    (BACKEND_VOYAGE_CLOUD, CLOUD_KEY),
    (BACKEND_VOYAGE_CONTEXT, CONTEXT_KEY),
]
_ARM_IDS = [backend for backend, _ in BACKEND_ARMS]


class TestEveryBackendPutsTheRealCredentialBytesOnTheWire:
    """Inventory B9, and the single most important pin in packet 42.

    ``make_embedder`` passes ONE resolved key into all three backend arms. With
    the key becoming a ``SecretStr``, "it reaches the wire" stops being trivially
    true: a missing unwrap renders ``Bearer **********`` and every request 401s.
    """

    @pytest.mark.parametrize("backend,key", BACKEND_ARMS, ids=_ARM_IDS)
    async def test_the_authorization_header_is_exactly_bearer_plus_the_key(
        self, backend: str, key: str
    ) -> None:
        server = _AuthRecordingServer()
        embedder = make_embedder(_config_for(backend, key))
        # Injecting the transport post-construction mirrors what the sibling
        # suites do via constructor kwargs; the factory does not expose one, and
        # the client is the object that carries the header.
        embedder._client._transport = server.transport()  # type: ignore[attr-defined]
        await embedder.embed_documents([DOCUMENT_TEXT])
        # ANTI-VACUITY: a request was actually made. Without this, an embedder
        # that short-circuited would leave ``auth_headers`` empty and ``all(...)``
        # below would pass over nothing.
        assert server.auth_headers, f"{backend} made no request — this pin is vacuous"
        assert all(header == f"Bearer {key}" for header in server.auth_headers), (
            f"{backend} did not put the real credential bytes on the wire. Observed: "
            f"{server.auth_headers}. A SecretStr that is never unwrapped renders "
            f"'Bearer **********' — type-correct, gate-green, and 100% broken in production."
        )

    @pytest.mark.parametrize("backend", _ARM_IDS, ids=_ARM_IDS)
    async def test_a_key_with_real_whitespace_survives_byte_exact(self, backend: str) -> None:
        # Inventory B4: neither the old ``_resolve_api_key`` nor ``resolve_secret``
        # strips the VALUE (only the emptiness check looks past whitespace). A
        # credential pasted with padding must authenticate as its real bytes, so
        # the padding has to survive every hop to the header.
        server = _AuthRecordingServer()
        embedder = make_embedder(_config_for(backend, PADDED_KEY))
        embedder._client._transport = server.transport()  # type: ignore[attr-defined]
        await embedder.embed_documents([DOCUMENT_TEXT])
        assert server.auth_headers, f"{backend} made no request — this pin is vacuous"
        assert server.auth_headers[0] == f"Bearer {PADDED_KEY}"

    @pytest.mark.parametrize("backend,key", BACKEND_ARMS, ids=_ARM_IDS)
    def test_the_embedder_does_not_retain_the_raw_credential(self, backend: str, key: str) -> None:
        # The other half of the type migration: annotating is not storing. An
        # implementation that unwraps in ``__init__`` and keeps the ``str`` on an
        # attribute satisfies every header pin above and puts the credential back
        # into every ``repr`` and frame render — which is #211 exactly.
        embedder = make_embedder(_config_for(backend, key))
        rendered = f"{embedder!r} {embedder!s} {vars(embedder)!r}"
        assert key not in rendered, (
            f"{backend} retains the raw credential on the instance; hold the SecretStr and "
            f"unwrap only at the client seam"
        )


class TestTheConfigCarriesAResolvedSecretNotAnEnvVarName:
    """Inventory B8/B10: ``api_key_env`` leaves loresigil; ``api_key: SecretStr`` arrives."""

    def test_a_secretstr_api_key_is_accepted(self) -> None:
        config = _config_for(BACKEND_TEI, TEI_KEY)
        assert isinstance(config.api_key, SecretStr)
        assert config.api_key.get_secret_value() == TEI_KEY

    def test_model_dump_returns_the_SecretStr_object_not_a_string(self) -> None:
        # Adversary residual R6, closed as a note-with-a-pin: ``model_dump()``'s
        # SHAPE changes under this reshape. It used to yield ``api_key_env: str``;
        # it now yields a ``SecretStr`` OBJECT for ``api_key`` (``model_dump_json``
        # masks, ``model_dump`` does not stringify). Any consumer that round-trips
        # a dumped config through ``json.dumps`` or compares it to a plain dict is
        # affected — pinned so the shape change is met deliberately.
        dumped = _config_for(BACKEND_TEI, TEI_KEY).model_dump()
        assert isinstance(dumped["api_key"], SecretStr)
        assert "api_key_env" not in dumped

    def test_the_config_repr_and_json_hide_the_credential(self) -> None:
        # The reason the field is typed rather than merely renamed: a config
        # object logged for diagnostics must not carry the key.
        config = _config_for(BACKEND_VOYAGE_CLOUD, CLOUD_KEY)
        assert CLOUD_KEY not in repr(config)
        assert CLOUD_KEY not in str(config)
        assert CLOUD_KEY not in config.model_dump_json()

    def test_api_key_env_is_rejected_AS_AN_UNKNOWN_FIELD(self) -> None:
        # ⚠ REJECTED FOR THE RIGHT REASON. A bare ``pytest.raises(ValidationError)``
        # here passes on a build where ``api_key`` is ALSO missing — the error would
        # be about the missing field, not about the retired one. The lead measured
        # exactly this class of false pass on this packet ("an empty key is
        # rejected" passing on ``extra_forbidden``), so the error is inspected.
        with pytest.raises(ValidationError) as excinfo:
            EmbeddingConfig(  # type: ignore[call-arg]
                backend="tei",
                base_url=TEI_BASE_URL,
                api_key=SecretStr(TEI_KEY),
                api_key_env="LORE_TEI_KEY",
            )
        errors = excinfo.value.errors()
        assert any(
            error["type"] == "extra_forbidden" and error["loc"] == ("api_key_env",)
            for error in errors
        ), f"rejected, but not for carrying a retired ``api_key_env`` field: {errors}"

    def test_the_same_construction_without_the_retired_field_succeeds(self) -> None:
        # POSITIVE CONTROL for the pin above: prove the rejection is attributable
        # to the retired field and not to something else in the payload.
        config = EmbeddingConfig(backend="tei", base_url=TEI_BASE_URL, api_key=SecretStr(TEI_KEY))
        assert config.backend == BACKEND_TEI

    def test_a_differently_broken_payload_is_rejected_for_a_DIFFERENT_reason(self) -> None:
        # The third leg of the control (CLAUDE.md: pair a negative result with a
        # positive control AND a differently-broken input rejected for a different
        # reason). An unknown BACKEND must fail on ``backend``, not on extras.
        with pytest.raises(ValidationError) as excinfo:
            EmbeddingConfig(backend="qdrant-magic", api_key=SecretStr(TEI_KEY))  # type: ignore[arg-type]
        assert any(error["loc"] == ("backend",) for error in excinfo.value.errors())


class TestAnAbsentCredentialFailsLoudAndNeverBuildsAKeylessEmbedder:
    """Inventory B2, preserved as a PROPERTY rather than as its old exception type.

    B2's virtue is *"a missing/empty key fails loud and never builds a keyless
    embedder"*. The old mechanism (``_resolve_api_key``'s ``if not key``) is
    deleted, so the property must be re-established where the value now enters:
    the config boundary.

    ⚠ **This class encodes an ESCALATED reading — see the report's open rulings.**
    The operator ruling moves RESOLUTION to the composition root, which would put
    the emptiness check there too. But ``scripts/search_score_survey.py``
    constructs a loresigil ``EmbeddingConfig`` DIRECTLY, bypassing
    ``to_loresigil_config`` entirely — so a check that lives only at the
    composition root leaves that path unguarded and B2's property untrue over all
    construction paths. Validating at the config boundary satisfies B2 for EVERY
    caller and fails strictly EARLIER than B7's old ``make_embedder`` timing,
    which the inventory records as the intended direction.

    Inventory B3 is deliberately NOT re-pinned: the old ``if not key`` ACCEPTED a
    whitespace-only value. That is an old bug (``resolve_secret`` rejects it), and
    pinning it would re-certify it.
    """

    @pytest.mark.parametrize(
        "label,value",
        [("empty", ""), ("single space", " "), ("tabs and spaces", " \t ")],
        ids=["empty", "single-space", "whitespace-only"],
    )
    def test_a_blank_credential_is_rejected_AT_THE_API_KEY_FIELD(self, label: str, value: str) -> None:
        with pytest.raises(ValidationError) as excinfo:
            EmbeddingConfig(backend="tei", base_url=TEI_BASE_URL, api_key=SecretStr(value))
        errors = excinfo.value.errors()
        # REJECTED FOR THE RIGHT REASON, again: the failure must be attributed to
        # ``api_key``, not to a missing sibling field.
        assert any(error["loc"] == ("api_key",) for error in errors), (
            f"the {label} credential was rejected, but not because of ``api_key``: {errors}"
        )

    def test_no_embedder_is_constructed_when_the_credential_is_blank(self) -> None:
        # "Fails loud" is not enough — B2's property is that no HALF-BUILT client
        # exists. Asserted at the factory seam because that is where a keyless
        # client would be born.
        with pytest.raises(ValidationError):
            make_embedder(
                EmbeddingConfig(backend="tei", base_url=TEI_BASE_URL, api_key=SecretStr(""))
            )

    def test_a_credential_that_is_only_whitespace_INSIDE_is_still_accepted(self) -> None:
        # The narrow edge that keeps the emptiness check from becoming a stripper:
        # only a value that is blank ALL THROUGH is rejected. A key whose real
        # bytes contain interior or edge whitespace is legal and must construct.
        config = EmbeddingConfig(
            backend="tei", base_url=TEI_BASE_URL, api_key=SecretStr(PADDED_KEY)
        )
        assert config.api_key.get_secret_value() == PADDED_KEY


def _loresigil_sources() -> list[tuple[str, Path]]:
    """Every production ``.py`` file in the ``loresigil`` package.

    Derived from the imported package, so the scan provably covers the SAME tree
    the tests import (CLAUDE.md: prove which tree you are testing).
    """
    package_file = loresigil.__file__
    assert package_file is not None, "loresigil imported as an empty namespace package"
    root = Path(package_file).resolve().parent
    return [(str(path.relative_to(root)), path) for path in sorted(root.rglob("*.py"))]


class TestLoresigilResolvesNothing:
    """The ruled SHAPE, pinned structurally: loresigil reads no environment at all.

    Keyed on ``os.environ`` / ``os.getenv`` rather than on the retired function's
    NAME. A build that keeps the old resolver under a new name defeats a
    name-keyed pin and is caught by this one — the repo has six receipts on
    name-keyed instruments losing (CLAUDE.md, "the instrument lesson").

    The SAFE set here is EMPTY, which is the strongest form an allowlist can take.
    """

    def test_the_scan_sees_the_package(self) -> None:
        # POSITIVE CONTROL: a scan that silently found no files would make the
        # emptiness assertion below pass vacuously.
        sources = _loresigil_sources()
        assert len(sources) >= 8, f"the loresigil scan found only {len(sources)} files"
        assert any(display == "factory.py" for display, _ in sources)

    def test_no_loresigil_module_reads_an_environment_variable(self) -> None:
        offenders: list[str] = []
        for display, source_path in _loresigil_sources():
            tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr in {"environ", "getenv"}:
                    offenders.append(f"{display}:{node.lineno} os.{node.attr}")
        assert not offenders, (
            "loresigil still reads the environment. The 2026-07-26 operator ruling on #222 "
            "pushes secret resolution UP to the composition root — loresigil resolves "
            "nothing:\n  " + "\n  ".join(offenders)
        )

    @pytest.mark.parametrize("name", ["_resolve_api_key", "MissingApiKeyError"])
    def test_the_retired_symbol_is_gone(self, name: str) -> None:
        # Inventory B1 and B6. ``MissingApiKeyError`` is raised only by
        # ``_resolve_api_key`` and caught in ZERO production sites (re-derived
        # 2026-07-26 at 9c08cac); four test files import it and are migrated with
        # this packet.
        from loresigil import factory

        assert not hasattr(factory, name), f"{name} survives the ruled deletion"

    def test_the_factory_still_exports_what_it_keeps(self) -> None:
        # POSITIVE CONTROL for the retired-symbol scan — proves ``hasattr``
        # discriminates and the module under test is the right one.
        from loresigil import factory

        for kept in ("EmbeddingConfig", "make_embedder", "BACKEND_TEI"):
            assert hasattr(factory, kept)


class TestTheBearerHeaderPolicyHasOneImplementation:
    """CLAUDE.md ONE IMPLEMENTATION, applied to the unwrap-and-send policy.

    At base (measured 2026-07-26 at ``9c08cac``) the ``Authorization: Bearer …``
    header is built in TWO places: ``voyage_http.build_bearer_client`` (shared by
    the two cloud arms) and an inline ``httpx.AsyncClient(headers=...)`` in
    ``tei.py``. Once the value is a ``SecretStr``, that header construction stops
    being trivia and becomes POLICY — it is where the unwrap decision lives — and
    policy duplicated is policy a fix reaches one copy of.

    ⚠ This pin FORCES a consolidation the packet implies but does not spell out;
    it is called out in the report as a design consequence for the operator.
    """

    def test_the_bearer_header_string_is_built_in_exactly_one_module(self) -> None:
        builders: list[str] = []
        for display, source_path in _loresigil_sources():
            source = source_path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(source_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.JoinedStr):
                    rendered = "".join(
                        part.value
                        for part in node.values
                        if isinstance(part, ast.Constant) and isinstance(part.value, str)
                    )
                    if "Bearer" in rendered:
                        builders.append(f"{display}:{node.lineno}")
        assert len(builders) == 1, (
            "the bearer-header policy must have ONE implementation that every backend arm "
            "calls — a second copy is where the unwrap decision silently diverges "
            f"(CLAUDE.md, #102). Found: {builders}"
        )

    def test_exactly_one_unwrap_site_exists_in_loresigil(self) -> None:
        # The unwrap is the policy; the allowlist gate in
        # ``loremaster/tests/test_secret_typing.py`` governs the whole workspace,
        # and this is its loresigil-local, mutation-visible companion. Changing
        # the seam moves this pin with it; a private copy in a second arm does not.
        sites: list[str] = []
        for display, source_path in _loresigil_sources():
            tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "get_secret_value"
                ):
                    sites.append(f"{display}:{node.lineno}")
        assert len(sites) == 1, (
            "loresigil must unwrap the credential in exactly ONE place — the client seam. "
            f"Found {len(sites)}: {sites}"
        )
