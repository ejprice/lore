"""Contract — packet 49, the ``PrincipalKeyStore`` served surface (the trust core).

Written by ``contract-49-1`` (2026-08-20). The builder builds FROM this; it writes
NO production code. STUB surfaces exist (every ``PrincipalKeyStore`` method raises
``NotImplementedError``), so every behavioural pin is RED for the RIGHT reason — never
an ImportError.

DESIGN (the work order): ``docs/design/2026-08-20-packet49-cli-keys.md`` §F3 (verify
behaviour / resolution / typed result), §F4 (``<name>:<secret>`` wire format, sha512
hash, secret generator — OPERATOR-CONFIRMED), §F5 (DRY vs the kept ``ApiKeyVerifier``),
§F7 (the store surface). Consumer/Trust Law (repo CLAUDE.md): a suspended/expired human
must never authenticate; failures are UNIFORM (no oracle); the raw secret is NEVER
stored or logged.

THE FOUR VERIFY-DENY CONDITIONS (design §F3a), re-evaluated EVERY call (no cache — R12):
    (1) key.revoked_at IS NONE
    (2) key.expires_at IS NONE OR key.expires_at > now
    (3) principal.status == 'active'  (NOT suspended)
    (4) principal.expires_at IS NONE OR principal.expires_at > now
QUANTIFIER-LAW: each is pinned with an INDEPENDENT fixture forcing THAT condition to
fire while the other three pass — never one fixture satisfying the ∀ vacuously. A
positive all-clear control proves a deny is attributable to its condition, not to
verify denying everything.

WIRE FORMAT (design §F4): the presented credential is ``<name>:<secret>``; the stored
hash is ``sha512_hex(f"{name}:{secret}")`` (SHA-512 hex of the WHOLE string — correct
for a 256-bit high-entropy random secret, NOT password hashing). ``mint`` takes the
ALREADY-hashed secret; the store never sees the raw secret except transiently in
``verify``'s input. The test constructs its fixtures the SAME way the CLI will (so a
build that hashed only the secret, or only the name, is caught by the round-trip).

LIVE store: ws://127.0.0.1:18000 (NEVER :18500). NO skip marker.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, NamedTuple

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    run,
    unique_database,
)
from loremaster.index.records import sha512_hex
from loremaster.store import surreal_schema

from loremaster import principal_keys as pk_module
from loremaster import principals as p_module

_EMAIL_A = "alice@example.com"
_EMAIL_B = "bob@example.com"
_NAME_1 = "laptop"
_NAME_2 = "ci-runner"
_SECRET = "s3cr3t-token-value-not-really-random-but-distinct"
_SECRET_2 = "another-distinct-secret-value-for-the-second-key"
# ⚠ FINDING 1 (adversary): a key's stored hash is sha512(name:secret); two keys sharing
# BOTH name AND secret collide on UNIQUE(hash) and the 2nd mint is rejected on a CORRECT
# build. So every key that could co-exist in one DB gets a DISTINCT secret (the #206 and
# uniform-deny fixtures need distinct principals each holding A key, never identical creds).
_SECRET_3 = "a-third-distinct-secret-so-no-two-keys-share-one-hash"
_SECRET_4 = "a-fourth-distinct-secret-for-the-uniform-deny-fixture"


def _wire(name: str, secret: str) -> str:
    """The wire credential the CLI prints once at mint: ``<name>:<secret>``."""
    return f"{name}:{secret}"


def _hash_for(name: str, secret: str) -> str:
    """The stored hash the CLI computes for a wire credential — ``sha512_hex`` of the
    WHOLE ``<name>:<secret>`` string (design §F4). Constructed here exactly as the CLI
    will, so ``verify`` (which hashes the presented string) MUST hash the whole string
    to match — a build hashing only the secret, or only the name, denies a real key."""
    return sha512_hex(_wire(name, secret))


class _Stores(NamedTuple):
    principals: Any  # PrincipalStore
    keys: Any  # PrincipalKeyStore
    env: SurrealEnv


@pytest_asyncio.fixture()
async def stores() -> Any:
    """A ready ``PrincipalStore`` + ``PrincipalKeyStore`` on ONE fresh unique database.

    Both readied (principal FIRST — the record link's target). On the STUB
    ``PrincipalKeyStore.ensure_ready`` raises ``NotImplementedError``, so every pin is
    RED at fixture setup until the builder lands it; on a real build both tables exist
    and each pin exercises its own behaviour. ``env`` is yielded so the never-stored-raw
    pin can open its own admin connection to read the raw row.
    """
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup = await connect_admin(env)
    await setup.close()
    principal_store = p_module.PrincipalStore(
        url=env.url, namespace=env.namespace, database=env.database,
        user=env.user, password=env.password,
    )
    key_store = pk_module.PrincipalKeyStore(
        url=env.url, namespace=env.namespace, database=env.database,
        user=env.user, password=env.password,
    )
    await principal_store.ensure_ready()
    await key_store.ensure_ready()
    try:
        yield _Stores(principals=principal_store, keys=key_store, env=env)
    finally:
        await key_store.close()
        await principal_store.close()
        await drop_database(env)


async def _mint(
    s: _Stores,
    *,
    email: str,
    name: str,
    secret: str,
    key_expires_at: datetime | None = None,
) -> str:
    """Create a principal-owned key from a raw secret and return the WIRE credential.

    Computes the stored hash the CLI way (``sha512_hex(name:secret)``) and mints. The
    principal must already exist.
    """
    await s.keys.mint(
        email=email, name=name, secret_hash=_hash_for(name, secret), expires_at=key_expires_at
    )
    return _wire(name, secret)


def _past() -> datetime:
    return datetime.now(UTC) - timedelta(hours=1)


def _future() -> datetime:
    return datetime.now(UTC) + timedelta(days=30)


# --------------------------------------------------------------------------- #
# Value objects + exception hierarchy (structural — GREEN against the stub, which
# defines them; they redden only if a build breaks the frozen interface).
# --------------------------------------------------------------------------- #


class TestTypedSurface:
    def test_key_verification_is_frozen_and_forbids_extra(self) -> None:
        """``KeyVerification`` is a frozen, ``extra='forbid'`` value object carrying the
        resolved ``principal`` + ``key_name`` (design §F3c)."""
        principal = p_module.Principal(
            id="principal:x", email=_EMAIL_A, subject=None, display_name=None,
            status="active", role="member", expires_at=None, created_at=datetime.now(UTC),
        )
        verification = pk_module.KeyVerification(principal=principal, key_name=_NAME_1)
        assert verification.principal.email == _EMAIL_A
        assert verification.key_name == _NAME_1
        with pytest.raises(Exception):  # noqa: B017 - frozen model
            verification.key_name = "other"  # type: ignore[misc]
        with pytest.raises(Exception):  # noqa: B017 - extra='forbid'
            pk_module.KeyVerification(principal=principal, key_name=_NAME_1, extra="x")  # type: ignore[call-arg]

    def test_key_not_found_is_a_subclass_of_store_error(self) -> None:
        """A caller catching ``PrincipalKeyStoreError`` catches the not-found too."""
        assert issubclass(pk_module.PrincipalKeyNotFoundError, pk_module.PrincipalKeyStoreError)


# --------------------------------------------------------------------------- #
# mint / verify happy path + the typed result (#206 identity).
# --------------------------------------------------------------------------- #


class TestMintAndVerifyHappyPath:
    async def test_verify_returns_the_owning_principal_and_key_name(
        self, stores: _Stores
    ) -> None:
        """A minted key verifies to its OWNER principal + the key's name (design §F3).
        The all-clear control the deny pins lean on."""
        await stores.principals.create(email=_EMAIL_A)
        presented = await _mint(stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET)
        verification = await stores.keys.verify(presented)
        assert verification is not None
        assert verification.principal.email == _EMAIL_A
        assert verification.key_name == _NAME_1

    async def test_verify_hashes_the_WHOLE_wire_string(self, stores: _Stores) -> None:
        """Design §F4: the hash is ``sha512_hex(f'{name}:{secret}')``. A presented string
        whose hash matches the stored one verifies; a build that hashed only the secret
        (dropping the name) would compute a different digest and deny a real key. The
        fixture stores ``sha512_hex(name:secret)``, so a match PROVES verify hashed the
        whole string."""
        await stores.principals.create(email=_EMAIL_A)
        presented = await _mint(stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET)
        assert await stores.keys.verify(presented) is not None
        # A DIFFERENT name with the same secret has a DIFFERENT hash → no match → deny
        # (proves the name is part of the hashed material, not ignored).
        assert await stores.keys.verify(_wire("other-name", _SECRET)) is None

    async def test_mint_unknown_principal_raises_principal_not_found(self, stores: _Stores) -> None:
        """Minting a key for a NONEXISTENT principal raises ``PrincipalNotFoundError``
        (never silently creates an ownerless key). LEAD RULING #2 (2026-08-20): the
        MISSING-PRINCIPAL vocabulary is ``PrincipalNotFoundError`` (reuse principals'),
        distinct from ``PrincipalKeyNotFoundError`` which is ONLY for a missing KEY —
        no-such-person and no-such-key are honestly distinct."""
        with pytest.raises(p_module.PrincipalNotFoundError):
            await stores.keys.mint(
                email="nobody@example.com", name=_NAME_1, secret_hash=_hash_for(_NAME_1, _SECRET)
            )


# --------------------------------------------------------------------------- #
# Pin 6 — #206: per-PRINCIPAL identity (the exact defect the packet exists to avoid).
# --------------------------------------------------------------------------- #


class TestPerPrincipalIdentity206:
    async def test_distinct_principals_and_one_principal_two_keys(
        self, stores: _Stores
    ) -> None:
        """⚠ THE #206 COLLAPSE GUARD (design §F4). Fixture MUST have ≥2 principals AND
        ≥1 principal with ≥2 keys — a one-principal/one-key monoculture passes a broken
        constant-identity build.

        - Two DISTINCT principals each with a key → verify returns DISTINCT principals
          (a constant/per-key-name identity build returns the same → FAILS here).
        - ONE principal with TWO keys → verify on EITHER returns the SAME principal (a
          per-key identity build returns different → FAILS here)."""
        await stores.principals.create(email=_EMAIL_A)
        await stores.principals.create(email=_EMAIL_B)
        a_key1 = await _mint(stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET)
        a_key2 = await _mint(stores, email=_EMAIL_A, name=_NAME_2, secret=_SECRET_2)
        # ⚠ FINDING 1: a DISTINCT secret (not _SECRET) — else b's (laptop, _SECRET) hash
        # collides with a_key1's on UNIQUE(hash) and the mint is rejected on a correct build.
        # The #206 property is about PRINCIPAL identity, orthogonal to the secret value.
        b_key1 = await _mint(stores, email=_EMAIL_B, name=_NAME_1, secret=_SECRET_3)

        va1 = await stores.keys.verify(a_key1)
        va2 = await stores.keys.verify(a_key2)
        vb1 = await stores.keys.verify(b_key1)
        assert va1 is not None and va2 is not None and vb1 is not None
        # Distinct humans → distinct identities.
        assert va1.principal.id != vb1.principal.id
        assert va1.principal.email == _EMAIL_A and vb1.principal.email == _EMAIL_B
        # One human's two keys → ONE identity.
        assert va1.principal.id == va2.principal.id
        assert va1.principal.email == va2.principal.email == _EMAIL_A


# --------------------------------------------------------------------------- #
# Pins 1/4/5 — the FOUR verify-deny conditions, each isolated (QUANTIFIER-LAW).
# --------------------------------------------------------------------------- #


class TestTheFourDenyConditions:
    async def test_all_clear_key_is_allowed_the_positive_control(self, stores: _Stores) -> None:
        """POSITIVE CONTROL for the four deny pins: a key whose principal is
        active+unexpired and whose own state is unrevoked+unexpired VERIFIES. Without
        this, a build that denies everything would pass every deny pin silently."""
        await stores.principals.create(email=_EMAIL_A, expires_at=_future())
        presented = await _mint(
            stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET, key_expires_at=_future()
        )
        assert await stores.keys.verify(presented) is not None

    async def test_revoked_key_is_denied_on_the_next_verify(self, stores: _Stores) -> None:
        """(1) Pin 1: the SAME presented key that verified pre-revoke is denied
        post-revoke — no cache/TTL (R12). Mutation: break ``revoked_at IS NONE`` → this
        reddens. ⚠ FIXTURE-DISCRIMINATE: re-verify the SAME credential, not a fresh key."""
        await stores.principals.create(email=_EMAIL_A)
        presented = await _mint(stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET)
        assert await stores.keys.verify(presented) is not None  # allowed…
        await stores.keys.revoke(email=_EMAIL_A, name=_NAME_1)
        assert await stores.keys.verify(presented) is None  # …then denied, same key.

    async def test_expired_key_is_denied_principal_fine(self, stores: _Stores) -> None:
        """(2) A key whose OWN ``expires_at`` is in the past is denied even though its
        principal is active+unexpired. Isolates condition (2)."""
        await stores.principals.create(email=_EMAIL_A)  # active, never expires
        presented = await _mint(
            stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET, key_expires_at=_past()
        )
        assert await stores.keys.verify(presented) is None

    async def test_suspended_principal_denies_a_live_key(self, stores: _Stores) -> None:
        """(3) Pin 4: suspending the OWNER denies its live key; unsuspending re-allows —
        re-checked every call (Trust Law). Isolates condition (3)."""
        await stores.principals.create(email=_EMAIL_A)
        presented = await _mint(stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET)
        assert await stores.keys.verify(presented) is not None
        await stores.principals.set_status(email=_EMAIL_A, status="suspended")
        assert await stores.keys.verify(presented) is None
        await stores.principals.set_status(email=_EMAIL_A, status="active")
        assert await stores.keys.verify(presented) is not None  # re-allowed, no residual window

    async def test_expired_principal_denies_a_live_key(self, stores: _Stores) -> None:
        """(4) A principal whose ``expires_at`` is in the past denies even a live,
        unexpired, unrevoked key. Isolates condition (4). The principal is created
        already-expired via ``create(expires_at=past)`` (no ``set_expires`` needed)."""
        await stores.principals.create(email=_EMAIL_A, expires_at=_past())
        presented = await _mint(
            stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET, key_expires_at=_future()
        )
        assert await stores.keys.verify(presented) is None


# --------------------------------------------------------------------------- #
# Pin 7 — blank / malformed presented credential denied (terminal, via is_blank +
# split validation).
# --------------------------------------------------------------------------- #


class TestBlankAndMalformedDenied:
    @pytest.mark.parametrize(
        "presented",
        ["", "   ", "\t", ":secret-only", "name-only:", "nocolon", ": ", " :secret"],
    )
    async def test_blank_or_malformed_credentials_deny(
        self, stores: _Stores, presented: str
    ) -> None:
        """``verify`` denies (returns ``None``, never raises) for an empty/whitespace
        credential, a missing name (``:secret``), a missing secret (``name:``), and a
        colon-less string — terminal failure via ``is_blank`` + split-on-first-colon
        validation (design §F4)."""
        assert await stores.keys.verify(presented) is None


# --------------------------------------------------------------------------- #
# Pin 8 — uniform deny (no oracle) + the raw secret never leaks to a log.
# --------------------------------------------------------------------------- #


class TestUniformDenyNoOracle:
    async def test_every_denial_mode_returns_the_same_None(self, stores: _Stores) -> None:
        """Design §F8 / Trust Law: no-such-key, revoked, key-expired, principal-suspended,
        and principal-expired ALL return the SAME ``None`` to the caller — the denial
        REASON never reaches the caller (not in the return, not as an exception). A build
        that raised a reason-bearing exception, or returned a discriminable object, for
        any mode would fail here."""
        # no-such-key
        assert await stores.keys.verify(_wire("ghost", "nope")) is None
        # revoked
        await stores.principals.create(email=_EMAIL_A)
        revoked = await _mint(stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET)
        await stores.keys.revoke(email=_EMAIL_A, name=_NAME_1)
        # key-expired
        key_expired = await _mint(
            stores, email=_EMAIL_A, name=_NAME_2, secret=_SECRET_2, key_expires_at=_past()
        )
        # principal-suspended (⚠ FINDING 1: distinct secret — else collides with `revoked`)
        await stores.principals.create(email=_EMAIL_B)
        suspended = await _mint(stores, email=_EMAIL_B, name=_NAME_1, secret=_SECRET_3)
        await stores.principals.set_status(email=_EMAIL_B, status="suspended")
        # principal-expired (⚠ FINDING 1: distinct secret — every co-existing key's hash unique)
        await stores.principals.create(email="carol@example.com", expires_at=_past())
        p_expired = await _mint(stores, email="carol@example.com", name=_NAME_1, secret=_SECRET_4)

        results = [
            await stores.keys.verify(revoked),
            await stores.keys.verify(key_expired),
            await stores.keys.verify(suspended),
            await stores.keys.verify(p_expired),
        ]
        assert results == [None, None, None, None], (
            f"every denial mode must return an IDENTICAL None (no oracle); got {results!r}"
        )

    async def test_the_raw_secret_never_appears_in_a_log_record(
        self, stores: _Stores, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Trust Law: the denial reason is laundered into a LOG — but the raw secret is
        NEVER logged (design §F3a: "laundered — never the key value"). Verify a revoked
        key with logging captured and assert NO emitted record text contains the raw
        secret."""
        await stores.principals.create(email=_EMAIL_A)
        presented = await _mint(stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET)
        await stores.keys.revoke(email=_EMAIL_A, name=_NAME_1)
        with caplog.at_level("DEBUG"):
            assert await stores.keys.verify(presented) is None
        for record in caplog.records:
            assert _SECRET not in record.getMessage(), (
                "the raw secret leaked into a log record — verify must launder the denial "
                "reason and NEVER log the credential (design §F3a)"
            )


# --------------------------------------------------------------------------- #
# list_for / revoke — the management reads/writes (design §F7).
# --------------------------------------------------------------------------- #


class TestListForAndRevoke:
    async def test_list_for_shows_all_keys_including_revoked_flagged(
        self, stores: _Stores
    ) -> None:
        """``list_for`` returns every key a principal owns, revoked keys INCLUDED and
        flagged by ``revoked_at`` (design §F7 — the CLI's ``list-keys``)."""
        await stores.principals.create(email=_EMAIL_A)
        await _mint(stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET)
        await _mint(stores, email=_EMAIL_A, name=_NAME_2, secret=_SECRET_2)
        await stores.keys.revoke(email=_EMAIL_A, name=_NAME_1)
        keys = await stores.keys.list_for(email=_EMAIL_A)
        by_name = {k.name: k for k in keys}
        assert set(by_name) == {_NAME_1, _NAME_2}
        assert by_name[_NAME_1].revoked_at is not None  # revoked, flagged
        assert by_name[_NAME_2].revoked_at is None  # still live

    async def test_revoke_unknown_key_name_raises_key_not_found(self, stores: _Stores) -> None:
        """⚠ LEAD RULING #2: the principal EXISTS but the KEY does not → the KEY vocabulary
        ``PrincipalKeyNotFoundError`` (distinct from the missing-principal case below)."""
        await stores.principals.create(email=_EMAIL_A)
        with pytest.raises(pk_module.PrincipalKeyNotFoundError):
            await stores.keys.revoke(email=_EMAIL_A, name="no-such-key")

    async def test_revoke_unknown_principal_raises_principal_not_found(self, stores: _Stores) -> None:
        """⚠ LEAD RULING #2: revoking against a NONEXISTENT principal is
        ``PrincipalNotFoundError`` (no-such-PERSON) — NOT ``PrincipalKeyNotFoundError``
        (which is reserved for a real principal missing a named key). The two cases are
        honestly distinguished."""
        with pytest.raises(p_module.PrincipalNotFoundError):
            await stores.keys.revoke(email="nobody@example.com", name=_NAME_1)

    async def test_second_revoke_of_an_already_revoked_key_still_denies(
        self, stores: _Stores
    ) -> None:
        """Design §F7 (revoke idempotency — RULED): a second ``revoke`` of an
        already-revoked key does NOT raise ``PrincipalKeyNotFoundError`` (the row still
        exists) and the key STAYS denied. (The security-relevant invariant; the exact
        ``revoked_at`` re-stamp instant is not pinned.)"""
        await stores.principals.create(email=_EMAIL_A)
        presented = await _mint(stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET)
        await stores.keys.revoke(email=_EMAIL_A, name=_NAME_1)
        await stores.keys.revoke(email=_EMAIL_A, name=_NAME_1)  # must not raise
        assert await stores.keys.verify(presented) is None

    async def test_list_for_unknown_principal_raises_principal_not_found(self, stores: _Stores) -> None:
        """``list_for`` for a nonexistent principal raises ``PrincipalNotFoundError`` (LEAD
        RULING #2) — never a silent empty list that conflates "no such person" with
        "person with no keys"."""
        with pytest.raises(p_module.PrincipalNotFoundError):
            await stores.keys.list_for(email="nobody@example.com")


# --------------------------------------------------------------------------- #
# Pin 2 — the secret is NEVER stored raw.
# --------------------------------------------------------------------------- #


class TestSecretNeverStoredRaw:
    async def test_no_column_holds_the_raw_secret_only_the_hash(self, stores: _Stores) -> None:
        """Design §F4 / store law: after ``mint`` the stored ``principal_key`` row holds
        the sha512 HASH and NOWHERE the raw secret. Constructed-leak probe: read the raw
        row (all columns) via an admin connection and assert the raw secret substring
        appears in NO column. POSITIVE CONTROL: the stored hash == ``sha512_hex(name:secret)``
        IS present (so the probe can actually see stored content)."""
        await stores.principals.create(email=_EMAIL_A)
        await _mint(stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET)
        connection = await connect_admin(stores.env)
        try:
            rows = await run(
                connection, f"SELECT * FROM {surreal_schema.PRINCIPAL_KEY_TABLE}"
            )
        finally:
            await connection.close()
        assert rows, "no principal_key row was stored"
        blob = repr(rows)
        assert _SECRET not in blob, (
            f"the RAW secret was found in the stored row — a key must NEVER be stored raw "
            f"(design §F4); row={rows!r}"
        )
        assert _hash_for(_NAME_1, _SECRET) in blob, (
            "POSITIVE CONTROL failed: the stored sha512 hash of the credential is NOT in the "
            "row — the probe cannot see stored content, so its negative result is worthless"
        )


# --------------------------------------------------------------------------- #
# Pin 17 — ONE IMPLEMENTATION, proven by MUTATION.
# --------------------------------------------------------------------------- #


class TestSharingProvenByMutation:
    async def test_verify_routes_blank_check_through_the_shared_is_blank(
        self, stores: _Stores, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pin 17a: ``verify``'s blank check routes through the SHARED
        ``lorerunes.is_blank`` (module-level ``principal_keys.is_blank``, the house
        import idiom). Perturb it to classify EVERYTHING as blank; a previously-valid
        key is now denied — proving the shared predicate is really used, not a private
        re-implementation. Control leg: unpatched, the same key verifies."""
        await stores.principals.create(email=_EMAIL_A)
        presented = await _mint(stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET)
        assert await stores.keys.verify(presented) is not None  # control (unpatched)
        monkeypatch.setattr(pk_module, "is_blank", lambda _value: True)
        assert await stores.keys.verify(presented) is None, (
            "verify did not route its blank check through principal_keys.is_blank — a "
            "private blank re-implementation is a #102-class clone (design §F5)"
        )

    async def test_verify_maps_the_principal_through_the_shared_mapper(
        self, stores: _Stores, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Pin 17b: ``verify``'s resolved principal is mapped by the SAME code as
        ``PrincipalStore``'s (design §F3 — do NOT clone ``_row_to_principal``). Perturb
        ``PrincipalStore._row_to_principal``; BOTH ``get_by_email`` AND ``verify`` must
        reflect it. A private cloned mapper in ``PrincipalKeyStore`` would leave verify
        UNCHANGED — catching the clone.

        ⚠ CONTRACT RULING (decisions-needed): this pins that ``PrincipalKeyStore`` routes
        its principal mapping THROUGH ``PrincipalStore._row_to_principal`` (the design's
        "delegate to a PrincipalStore lookup" option, or keep ``_row_to_principal`` the
        shared entry). If the builder/operator promotes the mapping to a standalone
        shared module function instead, THAT function becomes the mutation target and
        this pin retargets — flag it, do not silently clone."""
        await stores.principals.create(email=_EMAIL_A)
        presented = await _mint(stores, email=_EMAIL_A, name=_NAME_1, secret=_SECRET)

        original = p_module.PrincipalStore._row_to_principal

        def _mutated(self: Any, row: dict[str, Any]) -> Any:
            return original(self, row).model_copy(update={"display_name": "MUTATION-PROBE"})

        monkeypatch.setattr(p_module.PrincipalStore, "_row_to_principal", _mutated)
        by_email = await stores.principals.get_by_email(_EMAIL_A)
        verification = await stores.keys.verify(presented)
        assert by_email is not None and by_email.display_name == "MUTATION-PROBE"
        assert verification is not None, "verify denied a valid key under the mapper mutation"
        assert verification.principal.display_name == "MUTATION-PROBE", (
            "verify's principal did NOT reflect the PrincipalStore._row_to_principal mutation — "
            "PrincipalKeyStore has a CLONED principal mapper (design §F3 ONE-IMPLEMENTATION)"
        )

    def test_principal_key_store_query_seam_is_covered_by_the_retry_suite(self) -> None:
        """Pin 17c (STRENGTHENED per adversary R2 — coverage, not mere existence):
        ``PrincipalKeyStore`` owns an ``async def _query`` seam AND
        ``test_retry_seam.py``'s package scan ACTUALLY DISCOVERS it, so its parametrised
        pins (which mutation-prove the seam rides the shared ``run_query`` — NO private
        retry/classification, #102/#120) cover it. Merely `hasattr(_query)` proves the
        seam EXISTS; asserting it is in ``_discover_query_seams()`` proves the shared
        retry suite PARAMETRIZES over it (a build hand-rolling queries inline evades that
        scan entirely). RED on the stub (no ``_query`` yet → not discovered)."""
        import inspect

        # test_retry_seam is a sibling test module on the tests path; a function-level
        # import keeps this file independently collectible.
        from test_retry_seam import _discover_query_seams  # noqa: PLC0415

        seam = getattr(pk_module.PrincipalKeyStore, "_query", None)
        assert seam is not None and inspect.iscoroutinefunction(seam), (
            "PrincipalKeyStore must own an `async def _query` seam (the shared retry policy, "
            "#102/#120)"
        )
        discovered = {cls.__name__ for _module_path, cls in _discover_query_seams()}
        assert "PrincipalKeyStore" in discovered, (
            "test_retry_seam.py's `_discover_query_seams()` does NOT include PrincipalKeyStore "
            "— its `async def _query` is not discovered, so the shared retry/backoff/exhaustion "
            "pins do not parametrize over it, and a private retry policy could ship unproven "
            "(#102/#120). The seam must be a real `async def _query` on the class."
        )
