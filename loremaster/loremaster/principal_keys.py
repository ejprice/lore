"""The ``principal_key`` substrate — lore's per-user API-key store (packet 49).

:class:`PrincipalKeyStore` is the durable store over the ``principal_key`` table: one
row per per-user API key, owned by exactly one
:class:`~loremaster.principals.Principal` via a required ``record<principal>`` link. A
principal may hold MANY keys (one-to-many).

THE #206 IDENTITY PICTURE (why per-user keys are avoidable-collision-free): the
authenticated identity of an api-key request is the **principal**, resolved FROM the
presented key via the link — NEVER the key's label and NEVER a constant.
:meth:`PrincipalKeyStore.verify` returns the resolved :class:`Principal` + the key's
``name`` so packet 39 mints an ``AccessToken`` per-PRINCIPAL. ``principal.subject`` is
NOT used on the api-key path (it is the OAuth-login binding; an api-key-only principal
may have ``subject = NONE`` forever).

WIRE FORMAT + HASH (design §F4, operator-confirmed 2026-08-20): the presented
credential is ``<name>:<secret>``; the stored ``hash`` is
``sha512_hex(f"{name}:{secret}")`` — the SHA-512 hex of the WHOLE string. This is a
fast unsalted content hash, which is CORRECT here: the secret is a 256-bit
high-entropy random token, NOT a low-entropy password (a password needs a slow salted
KDF precisely because it is guessable — this is not). Constant-time credential
matching is provided by the UNIQUE ``hash`` INDEX lookup over a preimage-resistant
digest (uniform timing, no name-existence oracle), so there is NO in-memory
``hmac.compare_digest`` on this path — the DB equality on the digest IS the check.
``mint`` takes the ALREADY-hashed secret; the store never sees the raw secret except
transiently in :meth:`verify`'s input, which it hashes and discards.

This store CLONES the :class:`~loremaster.principals.PrincipalStore` connection-owner
idiom VERBATIM (one lazily-opened signed-in WS connection; ``_ensure_connection``
double-checked locking; ``_drop_connection`` self-heal; ``_safe_close``; ``_query``
delegating to the shared :func:`loremaster.store._txn.run_query`) and introduces NO
retry / classification / query policy of its own (finding #102/#120). Its ``_query``
seam is auto-discovered by ``test_retry_seam.py``'s scan, so the shared retry pins
prove the sharing by mutation. ⚠ To match that file's ``_SEAM_REJECTION_EVENTS`` /
``_SEAM_REJECTION_NOUNS`` maps (finding #353), ``_query`` calls ``run_query`` with
EXACTLY ``noun="principal key query"`` / ``label="principal.key.query.rejected"`` — the
same convention ``PrincipalStore._query`` uses.

Principal RESOLUTION (mint / list_for / revoke / verify) delegates to an OWNED
:class:`~loremaster.principals.PrincipalStore` (``self._principals``), so the
row → :class:`Principal` mapping is the ONE shared
:meth:`~loremaster.principals.PrincipalStore._row_to_principal` (design §F3 — never a
cloned mapper; proven by the mutation pin). A missing PRINCIPAL raises
:class:`~loremaster.principals.PrincipalNotFoundError` (no-such-PERSON); a missing KEY
raises :class:`PrincipalKeyNotFoundError` (no-such-KEY) — honestly distinct.

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
import logging
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, SecretStr
from surrealdb import AsyncSurreal

# The shared predicates ``verify`` routes through (ONE IMPLEMENTATION — proven by the
# mutation pins in ``test_principal_keys_store.py`` and the packet-62 seam contract,
# which monkeypatch these MODULE-LEVEL names). Imported here — the house idiom
# (``from lorerunes import is_blank`` in config.py/findings.py; ``from
# loremaster.index.records import sha512_hex`` in store_read.py) — so they are
# attributes of THIS module for the patch to reach. ``is_blank`` is the shared
# blankness predicate (pin 17a — verify's whole-credential blank check routes through
# it, never a private re-implementation, §F5); ``parse_credential`` is the shared
# ``<name>:<secret>`` wire-format parse (EXTRACTED to ``lorerunes`` in packet 62 W2.6
# so this store AND ``AgentRegistry.verify_capability`` split a credential the SAME
# way — a private inline parse would silently drift). The two guards OVERLAP on the
# blank check (parse_credential also rejects blank) but pin DISTINCT properties: pin
# 17a that the blank check is shared, the seam pin that the PARSE is shared — both
# route through ONE lorerunes predicate. ``sha512_hex`` is the stored-hash helper (NOT
# a hand-rolled ``hashlib.sha512(...).hexdigest()`` — that clone is the packages /
# ONE-IMPLEMENTATION violation the DRY ledger forbids).
from loremaster.config import LoreConfig, resolve_config_value, resolve_secret
from loremaster.index.records import sha512_hex
from loremaster.principals import Principal, PrincipalNotFoundError, PrincipalStore
from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    SurrealConnectionError,
    TxnContentionExhaustedError,
    _SurrealConnection,
    bootstrap_session,
    execute_transaction,
    run_query,
    signin_credentials,
    wrap_store_rejection,
)
from loremaster.store.surreal_schema import (
    _PRINCIPAL_STATUS_ACTIVE,
    PRINCIPAL_KEY_TABLE,
    PRINCIPAL_TABLE,
    generate_principal_key_ddl,
)
from lorerunes import is_blank, parse_credential

logger = logging.getLogger(__name__)

# The ``principal_key`` columns the store reads/writes — named once so a rename is a
# single edit, never a literal drifting between the write CONTENT, the guarded reads
# and the row → value-object mapping (the ``principal`` store's ``_COL_*`` idiom).
_COL_ID = "id"
_COL_PRINCIPAL = "principal"
_COL_HASH = "hash"
_COL_NAME = "name"
_COL_CREATED_AT = "created_at"
_COL_EXPIRES_AT = "expires_at"
_COL_REVOKED_AT = "revoked_at"

# The verify hot-path projection dereferences the owner link for the owner's email
# (the two-query resolution: fetch the key row + owner email by hash, then map the
# full principal through the shared ``PrincipalStore._row_to_principal`` via
# ``get_by_email``). Store law §2: an EXPLICIT projection reads a NONE ``option<>``
# column back as ``None`` (``SELECT *`` OMITS it — a KeyError trap).
_OWNER_EMAIL_ALIAS = "owner_email"


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

    Owns the ``principal_key`` table (see
    :func:`~loremaster.store.surreal_schema.generate_principal_key_ddl`) and rides the
    shared :mod:`loremaster.store._txn` transaction / error-classification seams. It
    clones the :class:`~loremaster.principals.PrincipalStore` connection-owner idiom
    verbatim and introduces NO query/retry policy of its own (#102/#120). Principal
    resolution delegates to an owned :class:`~loremaster.principals.PrincipalStore`, so
    the row → :class:`Principal` mapping is shared (design §F3), never cloned.

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
        # Opened on first use; ``None`` means "not yet connected / closed".
        self._connection: _SurrealConnection | None = None
        # Guards the connect-time check-then-set so N concurrent first-callers never
        # each open their own underlying SDK connection (mirrors ``PrincipalStore``).
        self._connect_lock = asyncio.Lock()
        # The OWNED principal store used to resolve/map owners (design §F3 — the
        # row → Principal mapping is the ONE shared ``PrincipalStore._row_to_principal``,
        # never a cloned mapper). Constructed with the SAME coordinates; its connection
        # is opened lazily on first resolution and closed by :meth:`close`.
        self._principals = PrincipalStore(
            url=url, namespace=namespace, database=database, user=user, password=password
        )

    # -- connection lifecycle ----------------------------------------------

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking cloned verbatim from
        :meth:`~loremaster.principals.PrincipalStore._ensure_connection`: the fast path
        never touches the lock, the session bootstrap is the ONE shared
        :func:`~loremaster.store._txn.bootstrap_session`, and any bootstrap failure —
        transport/auth fault OR exhausted contention alike — is wrapped as
        :class:`SurrealConnectionError` after the half-open socket is closed.

        Raises:
            SurrealConnectionError: The server is unreachable, rejected auth, or the
                session bootstrap exhausted its retry budget.
        """
        if self._connection is not None:
            return self._connection
        async with self._connect_lock:
            if self._connection is not None:
                # A concurrent caller connected while this one waited; mypy can't
                # model the cross-coroutine mutation across the ``await`` above.
                return self._connection  # type: ignore[unreachable]
            connection = AsyncSurreal(self._url)
            credentials = signin_credentials(user=self._user, password=self._password)
            try:
                await connection.signin(credentials)
                await bootstrap_session(connection, self._namespace, self._database, url=self._url)
            except TxnContentionExhaustedError as error:
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): "
                    f"the session bootstrap exhausted its retry budget"
                ) from error
            except _CONNECTION_ERRORS as error:
                # Close the half-open socket so a failed connect never leaks a
                # dangling connection, then surface a typed connection error.
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): {error}"
                ) from error
            self._connection = connection
            logger.debug(
                "principal.key.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect and apply the ``principal_key`` schema slice — idempotent, safe to
        re-run.

        Applies :func:`~loremaster.store.surreal_schema.generate_principal_key_ddl`
        (the ``principal_key`` table + its two UNIQUE indexes) inside ONE ``BEGIN …
        COMMIT`` via :func:`~loremaster.store._txn.execute_transaction`, which verifies
        EVERY statement's status (the SDK's plain ``query()`` inspects only the first).
        The table/indexes are ``IF NOT EXISTS`` (a second call neither raises nor wipes
        rows) while every FIELD is ``DEFINE FIELD OVERWRITE`` (finding #107). The
        ``principal`` table (the owner link's target) is defined by
        :meth:`~loremaster.principals.PrincipalStore.ensure_ready` or by the folded
        :func:`~loremaster.store.surreal_schema.generate_ddl`; a ``record<t>``
        field-def does not require the target table to pre-exist at DDL time.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: A DDL statement was rejected by the engine.
        """
        await self._ensure_connection()
        ddl = generate_principal_key_ddl()
        await execute_transaction(
            f"BEGIN;\n{ddl}COMMIT;\n",
            {},
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        logger.debug("principal.key.schema.ready", extra={"database": self._database})

    async def close(self) -> None:
        """Close the live connection (if any) AND the owned principal store; tolerant
        of a never-connected store."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None
        await self._principals.close()

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal).

        A compare-and-swap (cloned from
        :meth:`~loremaster.principals.PrincipalStore._drop_connection`):
        ``self._connection`` is cleared only when ``connection`` is STILL the cached
        handle, so a late caller holding a stale reference can never wipe out a
        freshly-reconnected one. The handed connection is always closed.
        """
        if self._connection is connection:
            self._connection = None
        await self._safe_close(connection)

    @staticmethod
    async def _safe_close(connection: _SurrealConnection) -> None:
        """Close ``connection``, swallowing an already-dead-socket failure."""
        try:
            await connection.close()
        except _CONNECTION_ERRORS:
            # The socket is already gone — nothing left to release.
            logger.debug("principal.key.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single statement on the (lazily opened) connection, self-healing.

        Delegates to :func:`~loremaster.store._txn.run_query` — the ONE shared
        single-statement attempt body every seam in the package calls (finding
        #120/#108). ``PrincipalKeyStore`` hand-rolls NO retry/classification of its
        own: this seam is auto-discovered by ``test_retry_seam.py``'s ``_query`` scan,
        so the shared retry/backoff/exhaustion pins prove the sharing by mutation. The
        ``noun``/``label`` MATCH that file's ``_SEAM_REJECTION_NOUNS`` /
        ``_SEAM_REJECTION_EVENTS`` maps (finding #353) — a different string passes the
        4-file contract but FAILS the full retry-seam attribution/monoculture gate.
        """
        return await run_query(
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
            noun="principal key query",
            label="principal.key.query.rejected",
            statement=statement,
            params=params or {},
            logger=logger,
        )

    # -- mint / list / revoke ----------------------------------------------

    async def mint(
        self,
        *,
        email: str,
        name: str,
        secret_hash: str,
        expires_at: datetime | None = None,
    ) -> PrincipalKey:
        """Mint a per-user API key owned by the principal ``email``.

        Resolves the owning principal by ``email`` (an unknown email is a typed
        :class:`~loremaster.principals.PrincipalNotFoundError` — never a silently
        ownerless key), then ``CREATE principal_key CONTENT`` binding the owner as a
        RecordID (store law §2/§4 — the probed ``type::record('principal', $pid)``
        shape; a bare id string may not coerce to a link). Takes the ALREADY-hashed
        secret — the store never sees the raw secret. A duplicate ``hash`` or a
        duplicate ``(principal, name)`` pair is rejected by the UNIQUE backstop and
        wrapped LOUD as :class:`PrincipalKeyStoreError` (Consumer Law — never a raw
        engine error bubbling through). ``created_at`` self-stamps; an omitted
        ``expires_at`` takes NONE (never expires).

        Args:
            email: The owning principal's UNIQUE admission key.
            name: The key's label (UNIQUE within the principal).
            secret_hash: The ``sha512_hex(f"{name}:{secret}")`` the CLI computed.
            expires_at: An optional tz-aware key-expiry instant (binds as a Python
                datetime — store law §2, never stringified).

        Returns:
            The minted :class:`PrincipalKey` (a FRESH value object).

        Raises:
            PrincipalNotFoundError: No principal carries ``email``.
            PrincipalKeyStoreError: The hash or (principal, name) collides with a
                UNIQUE index.
        """
        principal_id = await self._require_principal_id(email)
        fragments = [
            f"{_COL_PRINCIPAL}: type::record('{PRINCIPAL_TABLE}', $pid)",
            f"{_COL_HASH}: $hash",
            f"{_COL_NAME}: $name",
        ]
        params: dict[str, Any] = {"pid": principal_id, "hash": secret_hash, "name": name}
        if expires_at is not None:
            fragments.append(f"{_COL_EXPIRES_AT}: $expires_at")
            params["expires_at"] = expires_at
        statement = (
            f"CREATE {PRINCIPAL_KEY_TABLE} CONTENT {{ {', '.join(fragments)} }} RETURN AFTER"
        )
        # The UNIQUE backstop (credential hash or (principal, name)) — wrapped LOUD; a
        # transport fault / exhausted contention passes through untouched (it must not
        # masquerade as a UNIQUE collision). Finding #400: routed through the ONE seam.
        with wrap_store_rejection(
            PrincipalKeyStoreError,
            f"could not mint key {name!r} for principal {email!r}: a key with that "
            f"name already exists for this principal (or the credential hash collides)",
        ):
            result = await self._query(statement, params)
        rows = self._as_rows(result)
        if not rows:
            raise PrincipalKeyStoreError(
                f"key {name!r} for principal {email!r} vanished immediately after it was created"
            )
        return self._row_to_key(rows[0])

    async def list_for(self, *, email: str) -> list[PrincipalKey]:
        """Return every key the principal ``email`` owns, oldest first — revoked keys
        INCLUDED and flagged by ``revoked_at`` (design §F7 — the CLI's ``list-keys``).

        Args:
            email: The owning principal's UNIQUE admission key.

        Returns:
            The principal's keys as FRESH :class:`PrincipalKey` value objects.

        Raises:
            PrincipalNotFoundError: No principal carries ``email`` (never a silent
                empty list conflating "no such person" with "person with no keys").
        """
        principal_id = await self._require_principal_id(email)
        rows = self._as_rows(
            await self._query(
                f"SELECT {_COL_ID}, {_COL_PRINCIPAL}, {_COL_NAME}, {_COL_CREATED_AT}, "
                f"{_COL_EXPIRES_AT}, {_COL_REVOKED_AT} FROM {PRINCIPAL_KEY_TABLE} "
                f"WHERE {_COL_PRINCIPAL} = type::record('{PRINCIPAL_TABLE}', $pid) "
                f"ORDER BY {_COL_CREATED_AT}",
                {"pid": principal_id},
            )
        )
        return [self._row_to_key(row) for row in rows]

    async def revoke(self, *, email: str, name: str) -> PrincipalKey:
        """Revoke a principal's key by ``name`` — stamps ``revoked_at = time::now()``.

        Keyed on (principal, name). An unknown EMAIL is
        :class:`~loremaster.principals.PrincipalNotFoundError` (no-such-PERSON); a real
        principal with no such KEY is :class:`PrincipalKeyNotFoundError` (no-such-KEY) —
        the two are honestly distinguished (LEAD RULING #2). A second revoke of an
        already-revoked key does NOT raise (the row still exists) and re-stamps
        ``revoked_at`` — the key STAYS denied either way (the security invariant; the
        exact re-stamp instant is not pinned).

        Args:
            email: The owning principal's UNIQUE admission key.
            name: The label of the key to revoke.

        Returns:
            The revoked key's updated state (a FRESH value object).

        Raises:
            PrincipalNotFoundError: No principal carries ``email``.
            PrincipalKeyNotFoundError: The principal exists but owns no key ``name``.
        """
        principal_id = await self._require_principal_id(email)
        result = await self._query(
            f"UPDATE {PRINCIPAL_KEY_TABLE} SET {_COL_REVOKED_AT} = time::now() "
            f"WHERE {_COL_PRINCIPAL} = type::record('{PRINCIPAL_TABLE}', $pid) "
            f"AND {_COL_NAME} = $name RETURN AFTER",
            {"pid": principal_id, "name": name},
        )
        rows = self._as_rows(result)
        if not rows:
            raise PrincipalKeyNotFoundError(
                f"principal {email!r} has no key named {name!r}"
            )
        return self._row_to_key(rows[0])

    # -- verify (the load-bearing served surface) --------------------------

    async def verify(self, presented: str) -> KeyVerification | None:  # noqa: PLR0911
        """Verify a presented ``<name>:<secret>`` credential (design §F3/§F4).

        On EVERY call (no cache — R12, no residual window): reject blank → split on the
        FIRST colon → ``sha512_hex`` the WHOLE presented string → look up by ``hash``
        → re-evaluate the FOUR admission conditions, all against a single ``now``
        (tz-aware UTC captured once):

            (1) ``key.revoked_at IS NONE``
            (2) ``key.expires_at IS NONE OR key.expires_at > now``
            (3) ``principal.status == 'active'`` (NOT suspended)
            (4) ``principal.expires_at IS NONE OR principal.expires_at > now``

        Returns the resolved :class:`KeyVerification` (owner principal + key name) on
        success, or ``None`` on ANY failure — a UNIFORM deny with NO oracle: the denial
        REASON is laundered into a DEBUG log (never the raw credential — design §F3a)
        and never reaches the caller. The ``PLR0911`` too-many-returns lint is
        suppressed here (design §R-a): the deny-per-condition shape is the clearest
        expression of the four independent checks; collapsing it would obscure them.

        Args:
            presented: The raw ``<name>:<secret>`` wire credential.

        Returns:
            A :class:`KeyVerification` on success, else ``None``.
        """
        now = datetime.now(UTC)
        # TWO shared guards, both routing through ONE lorerunes predicate each (ONE
        # IMPLEMENTATION, referenced as module attributes so the mutation pins can patch
        # them): the whole-credential blank check via the shared ``is_blank`` (pin 17a,
        # §F5 — a private blank re-implementation is a #102-class clone), then the
        # wire-format parse via the shared ``parse_credential`` (W2.6 seam pin — the
        # SAME parse ``AgentRegistry.verify_capability`` uses, so a credential minted
        # one way parses the other). They overlap on blankness by design; a ``None`` /
        # blank is the uniform malformed deny (no per-shape oracle; the raw credential
        # is never logged, §F3a).
        if is_blank(presented):
            return self._deny("blank-credential")
        if parse_credential(presented) is None:
            return self._deny("malformed-credential")

        rows = self._as_rows(
            await self._query(
                f"SELECT {_COL_NAME}, {_COL_REVOKED_AT}, {_COL_EXPIRES_AT}, "
                f"{_COL_PRINCIPAL}.email AS {_OWNER_EMAIL_ALIAS} "
                f"FROM {PRINCIPAL_KEY_TABLE} WHERE {_COL_HASH} = $h",
                {"h": sha512_hex(presented)},
            )
        )
        if not rows:
            return self._deny("no-such-key")
        row = rows[0]
        key_name = str(row[_COL_NAME])

        revoked_at = PrincipalStore._to_aware_utc(row.get(_COL_REVOKED_AT))
        if revoked_at is not None:
            return self._deny("key-revoked")
        key_expires_at = PrincipalStore._to_aware_utc(row.get(_COL_EXPIRES_AT))
        if key_expires_at is not None and key_expires_at <= now:
            return self._deny("key-expired")

        owner_email = row.get(_OWNER_EMAIL_ALIAS)
        if owner_email is None:
            # A dangling owner link should never arise (delete cascades keys first),
            # but a defensive deny keeps a corrupt row from authenticating.
            return self._deny("dangling-owner")
        principal = await self._principals.get_by_email(str(owner_email))
        if principal is None:
            return self._deny("no-such-principal")
        if principal.status != _PRINCIPAL_STATUS_ACTIVE:
            return self._deny("principal-suspended")
        if principal.expires_at is not None and principal.expires_at <= now:
            return self._deny("principal-expired")

        return KeyVerification(principal=principal, key_name=key_name)

    @staticmethod
    def _deny(reason: str) -> None:
        """Log a LAUNDERED denial reason (a fixed vocabulary token — NEVER the raw
        credential, design §F3a). Returns ``None`` implicitly — ``verify``'s ``return
        self._deny(...)`` is the uniform deny."""
        logger.debug("principal.key.verify.denied", extra={"reason": reason})

    # -- reads / mapping ----------------------------------------------------

    async def _require_principal_id(self, email: str) -> str:
        """Resolve ``email`` to its owning principal's bare record id (the ``xyz`` of
        ``principal:xyz``), for binding through ``type::record('principal', $pid)``.

        Delegates to the owned :meth:`~loremaster.principals.PrincipalStore.get_by_email`
        (the ONE shared lookup + row→Principal mapper — never a cloned resolver).

        Raises:
            PrincipalNotFoundError: No principal carries ``email``.
        """
        principal = await self._principals.get_by_email(email)
        if principal is None:
            raise PrincipalNotFoundError(f"no principal with email {email!r}")
        return self._record_id_part(principal.id)

    def _row_to_key(self, row: dict[str, Any]) -> PrincipalKey:
        """Map a raw ``principal_key`` row into a FRESH :class:`PrincipalKey`.

        Uses ``row[…]`` for the REQUIRED columns (``id``/``principal``/``name``
        /``created_at`` — always present) and ``row.get(…)`` for the ``option<>`` ones
        (``expires_at``/``revoked_at`` — store law §2: a ``RETURN AFTER`` / ``SELECT *``
        omits a NONE ``option<>`` column, and even an explicit projection reads it back
        as ``None``). Datetimes are normalised to tz-aware UTC via the SHARED
        :meth:`~loremaster.principals.PrincipalStore._to_aware_utc` coercion (the
        fleet-comparable anchor — never a cloned coercion).
        """
        created_at = PrincipalStore._to_aware_utc(row.get(_COL_CREATED_AT))
        if created_at is None:
            raise PrincipalKeyStoreError(
                f"principal_key row column {_COL_CREATED_AT!r} is missing or not a datetime"
            )
        return PrincipalKey(
            id=str(row[_COL_ID]),
            principal_id=str(row[_COL_PRINCIPAL]),
            name=str(row[_COL_NAME]),
            created_at=created_at,
            expires_at=PrincipalStore._to_aware_utc(row.get(_COL_EXPIRES_AT)),
            revoked_at=PrincipalStore._to_aware_utc(row.get(_COL_REVOKED_AT)),
        )

    @staticmethod
    def _record_id_part(record_id: str) -> str:
        """The id portion of a ``str(RecordID)`` (``principal:xyz`` → ``xyz``), for
        binding through ``type::record('principal', $pid)`` (store law §2/§4). A bare
        id (no ``:``) passes through unchanged."""
        _, separator, id_part = record_id.partition(":")
        return id_part if separator else record_id

    @staticmethod
    def _as_rows(result: Any) -> list[dict[str, Any]]:
        """Narrow a ``SELECT``/``CREATE``/``UPDATE`` result to its list of dict rows."""
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]


def build_principal_key_store(config: LoreConfig) -> PrincipalKeyStore:
    """Construct a :class:`PrincipalKeyStore` from ``config`` — the sibling of
    :func:`loremaster.store.surreal.build_store`, reading the SAME coordinate accessors
    (``config.surreal.{url,namespace,user_env,password_env}`` +
    ``config.effective_surreal_database``) MINUS ``dim`` (an identity store is never
    embedded). Reads the ALREADY-VALIDATED ``config.surreal.url`` (config rejected any
    inline credentials at load); resolves the username via
    :func:`~loremaster.config.resolve_config_value` and the password via
    :func:`~loremaster.config.resolve_secret` exactly as ``build_store`` does.
    """
    return PrincipalKeyStore(
        url=config.surreal.url,
        namespace=config.surreal.namespace,
        database=config.effective_surreal_database,
        user=resolve_config_value(config.surreal.user_env),
        password=resolve_secret(config.surreal.password_env),
    )
