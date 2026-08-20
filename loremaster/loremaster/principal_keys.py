"""The ``principal_key`` substrate — lore's per-user API-key store (packet 49).

⚠⚠ RED STUB (contract-49-1, 2026-08-20). This module exists so the packet-49
contract IMPORTS cleanly and every pin fails BEHAVIOURALLY (never an ImportError).
The value objects + exception hierarchy + public signatures are the FROZEN
interface the builder implements against; every :class:`PrincipalKeyStore` method
body ``raise``s :class:`NotImplementedError`. NO logic lives here — the design
(``docs/design/2026-08-20-packet49-cli-keys.md`` §F3/§F4/§F7) is the work order,
and the builder PROBES the link-deref ``verify`` query itself (design §F3).

The design picture (why #206 is avoidable):
    A ``principal_key`` belongs to exactly one :class:`~loremaster.principals.Principal`
    and a principal may hold MANY keys (one-to-many via a required
    ``record<principal>`` link). The authenticated identity of an api-key request is
    therefore the **principal**, resolved from the presented key — NEVER the key's
    label and NEVER a constant. :meth:`PrincipalKeyStore.verify` returns the resolved
    :class:`Principal` + the key's ``name`` so packet 39 mints per-PRINCIPAL.

This store CLONES the :class:`~loremaster.principals.PrincipalStore` connection-owner
idiom VERBATIM (one lazily-opened signed-in WS connection; ``_ensure_connection``
double-checked locking; ``_drop_connection`` self-heal; ``_query`` delegating to the
shared :func:`loremaster.store._txn.run_query`) and introduces NO retry /
classification / query policy of its own (finding #102/#120). Its ``_query`` seam is
auto-discovered by ``test_retry_seam.py``'s scan, so the shared retry pins prove the
sharing by mutation.

The public surface (design §F7):

    PrincipalKey:                          # a frozen value object (pydantic model)
        id: str                            # str(RecordID)
        principal_id: str                  # str(RecordID) of the owning principal
        name: str                          # the key label (UNIQUE per principal)
        created_at: datetime               # tz-aware UTC, engine-stamped
        expires_at: datetime | None        # option<datetime>: NONE = never expires
        revoked_at: datetime | None        # option<datetime>: NONE until revoked

    KeyVerification:                       # verify's typed result
        principal: Principal               # the resolved owner (#206 fix)
        key_name: str                      # the label of the key that authenticated

    PrincipalKeyStore(*, url, namespace, database, user, password):
        async ensure_ready() -> None
        async mint(*, email, name, secret_hash, expires_at=None) -> PrincipalKey
        async list_for(*, email) -> list[PrincipalKey]
        async revoke(*, email, name) -> PrincipalKey
        async verify(presented) -> KeyVerification | None
        async _query(statement, params=None) -> Any    # the shared retry seam
        async close() -> None

    Exceptions: PrincipalKeyStoreError(RuntimeError);
                PrincipalKeyNotFoundError(PrincipalKeyStoreError).
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, SecretStr

# The shared predicates the builder's ``verify`` routes through (ONE
# IMPLEMENTATION — proven by the mutation pins in ``test_principal_keys_store.py``,
# which monkeypatch these MODULE-LEVEL names). Imported here — the house idiom
# (``from lorerunes import is_blank`` in config.py/findings.py;
# ``from loremaster.index.records import sha512_hex`` in store_read.py) — so they
# are attributes of THIS module for the patch to reach. ``blankness`` rejects an
# empty/whitespace credential; ``sha512_hex`` is the stored-hash helper (NOT a
# hand-rolled ``hashlib.sha512(...).hexdigest()`` — that clone is the packages /
# ONE-IMPLEMENTATION violation the DRY ledger forbids).
from loremaster.index.records import sha512_hex
from loremaster.principals import Principal
from lorerunes import is_blank

_STUB_MESSAGE = "packet-49 builder (see docs/design/2026-08-20-packet49-cli-keys.md)"


class PrincipalKey(BaseModel):
    """A single per-user API key in the durable ``principal_key`` store.

    Attributes:
        id: The key's ``str(RecordID)`` string id.
        principal_id: The ``str(RecordID)`` of the owning principal (the link).
        name: The key's label — UNIQUE within its principal (``UNIQUE(principal,
            name)``), reusable across principals.
        created_at: The tz-aware UTC instant the key was minted (engine-stamped).
        expires_at: An optional tz-aware expiry instant, or ``None`` to never expire.
        revoked_at: The tz-aware instant the key was revoked, or ``None`` while live.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    principal_id: str
    name: str
    created_at: datetime
    expires_at: datetime | None
    revoked_at: datetime | None


class KeyVerification(BaseModel):
    """The typed result of a successful :meth:`PrincipalKeyStore.verify` (design §F3c).

    Carries the resolved OWNER (the full :class:`Principal`, not a string) so packet
    39 can mint an ``AccessToken`` per-PRINCIPAL (the #206 fix) and reach the role /
    status / email for any downstream permission resolver, plus the label of the key
    that authenticated (audit only).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    principal: Principal
    key_name: str


class PrincipalKeyStoreError(RuntimeError):
    """Base class for every error :class:`PrincipalKeyStore` raises."""


class PrincipalKeyNotFoundError(PrincipalKeyStoreError):
    """Raised when a (principal, key-name) pair resolves to no ``principal_key`` row."""


class PrincipalKeyStore:
    """Durable per-user API-key store over a single SurrealDB database (packet 49).

    ⚠⚠ RED STUB — every method below ``raise``s :class:`NotImplementedError`. The
    builder clones the :class:`~loremaster.principals.PrincipalStore` connection-owner
    idiom (``_ensure_connection`` / ``_drop_connection`` / ``_query`` /
    ``_safe_close``), implements ``ensure_ready`` (applies
    :func:`~loremaster.store.surreal_schema.generate_principal_key_ddl`), and
    implements ``mint`` / ``list_for`` / ``revoke`` / ``verify`` per the design.
    ``__init__`` stores the wiring (no connection opened) so a test fixture can
    CONSTRUCT the store and fail behaviourally on the first method call.

    Args:
        url: The SurrealDB RPC URL (e.g. ``ws://127.0.0.1:18000/rpc``).
        namespace: The namespace the database lives under.
        database: The per-project database name.
        user: The root/username to sign in with.
        password: The password to sign in with.
    """

    def __init__(
        self,
        *,
        url: str,
        namespace: str,
        database: str,
        user: str,
        password: SecretStr,
    ) -> None:
        """Store the wiring. Does not open any connection yet (mirrors PrincipalStore)."""
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        self._connection: Any = None
        self._connect_lock = asyncio.Lock()

    async def ensure_ready(self) -> None:
        """STUB: connect + apply ``generate_principal_key_ddl`` inside one
        ``BEGIN … COMMIT`` (the builder clones ``PrincipalStore.ensure_ready``)."""
        raise NotImplementedError(f"PrincipalKeyStore.ensure_ready — {_STUB_MESSAGE}")

    async def mint(
        self,
        *,
        email: str,
        name: str,
        secret_hash: str,
        expires_at: datetime | None = None,
    ) -> PrincipalKey:
        """STUB: resolve the principal by ``email``, then ``CREATE principal_key``
        binding the owner as a RecordID (design §F7). Takes the ALREADY-hashed
        secret — the store never sees the raw secret except transiently in
        :meth:`verify`."""
        raise NotImplementedError(f"PrincipalKeyStore.mint — {_STUB_MESSAGE}")

    async def list_for(self, *, email: str) -> list[PrincipalKey]:
        """STUB: every key owned by the principal ``email`` (revoked keys shown,
        flagged by ``revoked_at``)."""
        raise NotImplementedError(f"PrincipalKeyStore.list_for — {_STUB_MESSAGE}")

    async def revoke(self, *, email: str, name: str) -> PrincipalKey:
        """STUB: stamp ``revoked_at = time::now()`` on the (principal, name) key."""
        raise NotImplementedError(f"PrincipalKeyStore.revoke — {_STUB_MESSAGE}")

    async def verify(self, presented: str) -> KeyVerification | None:
        """STUB: the load-bearing served surface (design §F3/§F4). The builder:
        (1) reject blank via :func:`is_blank`; (2) split on the FIRST colon;
        (3) ``sha512_hex(presented)``; (4) look up by ``hash``; (5) the four
        re-checks (key revoked / key expired / principal suspended / principal
        expired). ``None`` on ANY failure — UNIFORM deny, no oracle.

        The shared predicates are named here so they are module attributes the
        ONE-IMPLEMENTATION mutation pins can patch; the real routing is the
        builder's obligation."""
        _shared_predicates = (is_blank, sha512_hex)  # noqa: F841 - see docstring
        raise NotImplementedError(f"PrincipalKeyStore.verify — {_STUB_MESSAGE}")

    async def close(self) -> None:
        """Close the live connection (if any); tolerant of a never-connected store.

        A real no-op in the stub (no connection is ever opened) so a fixture's
        teardown does not mask the behavioural NotImplementedError from setup.
        """
        self._connection = None


def build_principal_key_store(config: Any) -> PrincipalKeyStore:
    """STUB: construct a :class:`PrincipalKeyStore` from ``config`` — the sibling of
    :func:`loremaster.store.surreal.build_store`, reading the SAME coordinate
    accessors (``config.surreal.{url,namespace,user_env,password_env}`` +
    ``config.effective_surreal_database``) MINUS ``dim`` (an identity store is never
    embedded). The builder implements it with
    ``resolve_config_value``/``resolve_secret`` exactly as ``build_store`` does
    (design §F6). RED now: it raises so the CLI-wiring pins fail behaviourally."""
    raise NotImplementedError(f"build_principal_key_store — {_STUB_MESSAGE}")
