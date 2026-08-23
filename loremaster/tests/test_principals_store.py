"""Contract — packet 48 Wave 48-B, the ``PrincipalStore`` CRUD surface.

Written by ``contract-48b`` (2026-08-20). The builder builds FROM this; it writes
NO production code.

SPEC: ``docs/design/2026-08-20-packet48-principals-substrate.md`` §5 (the CRUD
surface + ``Principal`` value object + ``PrincipalStoreError`` /
``PrincipalNotFoundError``) and §8 checklist items 8 + 8b (``set_status`` /
``set_subject`` pins). Model B (operator-confirmed): ``subject`` is
``option<string>`` UNIQUE; ``create`` allows email-only creation; ``set_subject``
is the UNCONDITIONAL email-keyed fill-on-login primitive 39 consumes.

WHAT THIS FILE DECIDES — ``loremaster.principals``::

    class Principal(BaseModel)  # id/email/subject/display_name/status/role/expires_at/created_at
    class PrincipalStoreError(RuntimeError)
    class PrincipalNotFoundError(PrincipalStoreError)
    class PrincipalStore:
        def __init__(self, *, url, namespace, database, user, password: SecretStr)
        async def ensure_ready(self) -> None
        async def create(self, *, email, subject=None, role=None,
                         display_name=None, expires_at=None) -> Principal
        async def get_by_subject(self, subject: str) -> Principal | None
        async def get_by_email(self, email: str) -> Principal | None
        async def list(self) -> list[Principal]
        async def set_status(self, *, email, status) -> Principal
        async def set_subject(self, *, email, subject) -> Principal

WHY RED NOW (contract-first): ``loremaster.principals`` does not exist. The
``principal_store`` fixture calls ``_require_principals()`` FIRST — an
``importlib.import_module`` gate (mypy-safe for a not-yet-existing MODULE, unlike a
top-level ``import``) that ``pytest.fail``s CLEANLY before any DB is created, so
this file stays collection- and typecheck-clean and every pin is RED for the RIGHT
reason.

LIVE store: ws://127.0.0.1:18000 (NEVER :18500). NO skip marker — an unreachable
store is a LOUD failure, not a skip.
"""

from __future__ import annotations

import ast
import importlib
import inspect
from datetime import UTC, datetime, timedelta
from typing import Any

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
from loremaster.store import surreal_schema

_REQUIRED_NAMES = (
    "PrincipalStore",
    "Principal",
    "PrincipalStoreError",
    "PrincipalNotFoundError",
)

_EMAIL_A = "alice@example.com"
_EMAIL_B = "bob@example.com"
_EMAIL_C = "carol@example.com"
_SUBJECT = "google-oauth2|118427905123456789012"
_SUBJECT_OTHER = "google-oauth2|998877665544332211009"
_UNKNOWN_EMAIL = "nobody@example.com"


def _require_principals() -> Any:
    """RED-now gate: return the ``loremaster.principals`` module once 48-B has built
    it, else ``pytest.fail`` CLEANLY.

    Uses ``importlib.import_module`` (a runtime string import) rather than a
    top-level ``import loremaster.principals`` so this file neither errors at
    COLLECTION nor reddens the mypy gate while the module does not yet exist (mypy
    does not resolve a string import). ``pytest.fail`` both when the MODULE is
    absent and when a required SYMBOL is missing.
    """
    try:
        principals = importlib.import_module("loremaster.principals")
    except ModuleNotFoundError:
        pytest.fail(
            "loremaster.principals not yet built (packet 48-B) — contract is RED until it lands",
            pytrace=False,
        )
    missing = [name for name in _REQUIRED_NAMES if not hasattr(principals, name)]
    if missing:
        pytest.fail(
            f"loremaster.principals is missing {missing} (packet 48-B) — contract is RED until it lands",
            pytrace=False,
        )
    return principals


@pytest_asyncio.fixture()
async def principals_module() -> Any:
    """The ``loremaster.principals`` module, gated (clean RED before any DB work)."""
    return _require_principals()


@pytest_asyncio.fixture()
async def principal_store(principals_module: Any) -> Any:
    """A ready ``PrincipalStore`` on a fresh unique database, reaped on exit.

    Mirrors ``test_findings``'s real-``FindingLedger`` branch: mint the database,
    construct the store from a :class:`SurrealEnv`, ``ensure_ready`` (applies
    ``generate_principal_ddl``), yield, then close + drop. Gated BEFORE the DB is
    minted (via ``principals_module``), so a RED run needs no store contact.
    """
    env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    store = principals_module.PrincipalStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await store.ensure_ready()
    try:
        yield store
    finally:
        await store.close()
        await drop_database(env)


# --------------------------------------------------------------------------- #
# create / get_by_* / list
# --------------------------------------------------------------------------- #


class TestCreateAndRead:
    async def test_email_only_create_defaults_to_active_member_none_subject(
        self, principal_store: Any
    ) -> None:
        """Model B email-only create: ``subject`` NONE, ``status`` DEFAULT
        ``active``, ``role`` DEFAULT ``member`` (least-privilege). Read back from a
        FRESH store read (``get_by_email``), so a build that hardcoded the defaults
        in the value object rather than letting the store DEFAULT fire — and mapped
        the row wrong — is caught."""
        created = await principal_store.create(email=_EMAIL_A)
        assert created.email == _EMAIL_A
        assert created.subject is None
        assert created.status == "active"
        assert created.role == "member"
        fetched = await principal_store.get_by_email(_EMAIL_A)
        assert fetched is not None
        assert fetched.email == _EMAIL_A
        assert fetched.subject is None
        assert fetched.status == "active"
        assert fetched.role == "member"

    async def test_create_with_subject_is_found_by_subject_and_email(
        self, principal_store: Any
    ) -> None:
        """The OAuth-direct path — created WITH a subject, found by both keys."""
        await principal_store.create(email=_EMAIL_A, subject=_SUBJECT)
        by_subject = await principal_store.get_by_subject(_SUBJECT)
        by_email = await principal_store.get_by_email(_EMAIL_A)
        assert by_subject is not None and by_subject.subject == _SUBJECT
        assert by_email is not None and by_email.subject == _SUBJECT
        assert by_subject.email == _EMAIL_A

    async def test_create_with_explicit_non_default_role_and_status_round_trips(
        self, principal_store: Any
    ) -> None:
        """FIXTURES-MUST-DISCRIMINATE: a build that IGNORED ``role``/``status`` and
        always stored the DEFAULT would pass the email-only pin. Force NON-default
        values (``admin`` / ``suspended``) and prove they round-trip."""
        await principal_store.create(email=_EMAIL_A, subject=_SUBJECT, role="admin")
        fetched = await principal_store.get_by_email(_EMAIL_A)
        assert fetched is not None
        assert fetched.role == "admin"

    async def test_create_round_trips_display_name_and_expires_at(
        self, principal_store: Any
    ) -> None:
        """MINOR (adversary r2): ``create``'s ``display_name`` / ``expires_at``
        params were unpinned — a build that dropped them from the write CONTENT
        would still pass every other pin. Provide both (``expires_at`` a tz-aware
        datetime — store law §2: it binds as a Python datetime, never stringified)
        and prove they round-trip through a fresh store read (``get_by_email`` uses
        an explicit projection, so a NONE-vs-value confusion is caught)."""
        expires = datetime(2027, 1, 1, 12, 0, tzinfo=UTC)
        created = await principal_store.create(
            email=_EMAIL_A, display_name="Alice Example", expires_at=expires
        )
        assert created.display_name == "Alice Example"
        assert created.expires_at == expires
        fetched = await principal_store.get_by_email(_EMAIL_A)
        assert fetched is not None
        assert fetched.display_name == "Alice Example"
        assert fetched.expires_at == expires

    async def test_get_by_unknown_subject_and_email_return_none_not_error(
        self, principal_store: Any
    ) -> None:
        """A miss is ``None`` (not found), never an exception — the design's read
        contract (39 branches on None to decide pre-create-vs-fill)."""
        assert await principal_store.get_by_subject(_SUBJECT) is None
        assert await principal_store.get_by_email(_UNKNOWN_EMAIL) is None

    async def test_two_email_only_creates_coexist_via_the_store_api(
        self, principal_store: Any
    ) -> None:
        """⚠ THE MODEL-B LOAD-BEARING PIN at the STORE layer (probe Q1): two
        email-only principals (both ``subject`` NONE) BOTH created successfully and
        BOTH readable. A store whose ``create`` rejected the second NONE subject
        would break admin pre-create for every principal after the first — and a
        single-create fixture cannot see it."""
        await principal_store.create(email=_EMAIL_A)
        await principal_store.create(email=_EMAIL_B)
        a = await principal_store.get_by_email(_EMAIL_A)
        b = await principal_store.get_by_email(_EMAIL_B)
        assert a is not None and a.subject is None
        assert b is not None and b.subject is None

    async def test_list_returns_all_principals(self, principal_store: Any) -> None:
        emails = {_EMAIL_A, _EMAIL_B, _EMAIL_C}
        for email in emails:
            await principal_store.create(email=email)
        listed = await principal_store.list()
        assert {principal.email for principal in listed} == emails

    async def test_duplicate_email_raises_principal_store_error(
        self, principals_module: Any, principal_store: Any
    ) -> None:
        """The UNIQUE email backstop, wrapped LOUD (Consumer Law): a duplicate email
        surfaces as ``PrincipalStoreError``, NOT a raw ``SurrealError`` bubbling
        through and NOT a silent success."""
        await principal_store.create(email=_EMAIL_A)
        with pytest.raises(principals_module.PrincipalStoreError):
            await principal_store.create(email=_EMAIL_A)

    async def test_duplicate_non_none_subject_on_create_raises_principal_store_error(
        self, principals_module: Any, principal_store: Any
    ) -> None:
        """Two principals may never claim ONE OAuth subject — wrapped LOUD."""
        await principal_store.create(email=_EMAIL_A, subject=_SUBJECT)
        with pytest.raises(principals_module.PrincipalStoreError):
            await principal_store.create(email=_EMAIL_B, subject=_SUBJECT)


# --------------------------------------------------------------------------- #
# set_status (email-keyed — 49's suspend/unsuspend verb; §8 item 8)
# --------------------------------------------------------------------------- #


class TestSetStatus:
    async def test_set_status_transitions_a_known_email(self, principal_store: Any) -> None:
        """Happy path + the positive control in one: a KNOWN email transitions, the
        returned ``Principal`` carries the new status, and a fresh read confirms it
        (so a no-op build that returned the old row is caught)."""
        await principal_store.create(email=_EMAIL_A)  # status 'active'
        updated = await principal_store.set_status(email=_EMAIL_A, status="suspended")
        assert updated.status == "suspended"
        fetched = await principal_store.get_by_email(_EMAIL_A)
        assert fetched is not None and fetched.status == "suspended"

    async def test_set_status_on_unknown_email_raises_not_found(
        self, principals_module: Any, principal_store: Any
    ) -> None:
        """An unknown email is a typed ``PrincipalNotFoundError`` — never a silent
        no-op (which a naive ``UPDATE … WHERE`` returning an empty set would be)."""
        with pytest.raises(principals_module.PrincipalNotFoundError):
            await principal_store.set_status(email=_UNKNOWN_EMAIL, status="suspended")

    async def test_not_found_is_a_subclass_of_store_error(self, principals_module: Any) -> None:
        """``PrincipalNotFoundError`` IS a ``PrincipalStoreError`` (design §5 error
        hierarchy) — a caller catching the base catches the not-found too."""
        assert issubclass(
            principals_module.PrincipalNotFoundError, principals_module.PrincipalStoreError
        )


# --------------------------------------------------------------------------- #
# set_subject (Model B fill-on-login — §8 item 8b)
# --------------------------------------------------------------------------- #


class TestSetSubject:
    async def test_fill_binds_a_pre_created_email_only_principal(
        self, principal_store: Any
    ) -> None:
        """(i) THE 39 fill-on-login primitive: an email-only principal (subject
        NONE) is bound to its OAuth subject, after which ``get_by_subject`` finds it
        and ``get_by_email`` shows the filled subject."""
        await principal_store.create(email=_EMAIL_A)  # subject NONE
        assert await principal_store.get_by_subject(_SUBJECT) is None  # not bound yet
        updated = await principal_store.set_subject(email=_EMAIL_A, subject=_SUBJECT)
        assert updated.subject == _SUBJECT
        found = await principal_store.get_by_subject(_SUBJECT)
        assert found is not None and found.email == _EMAIL_A
        by_email = await principal_store.get_by_email(_EMAIL_A)
        assert by_email is not None and by_email.subject == _SUBJECT

    async def test_set_subject_on_unknown_email_raises_not_found(
        self, principals_module: Any, principal_store: Any
    ) -> None:
        """(ii) Unknown email → ``PrincipalNotFoundError``. Positive control: a
        KNOWN email DOES fill, so the raise is attributable to the missing row and
        not to ``set_subject`` failing for every input."""
        with pytest.raises(principals_module.PrincipalNotFoundError):
            await principal_store.set_subject(email=_UNKNOWN_EMAIL, subject=_SUBJECT)
        # POSITIVE CONTROL — a known email fills fine.
        await principal_store.create(email=_EMAIL_A)
        filled = await principal_store.set_subject(email=_EMAIL_A, subject=_SUBJECT)
        assert filled.subject == _SUBJECT

    async def test_subject_theft_raises_store_error(
        self, principals_module: Any, principal_store: Any
    ) -> None:
        """(iii) ⚠ THE UPDATE-PATH UNIQUE BACKSTOP (probe Q3 from the store side):
        filling a subject ALREADY bound to ANOTHER principal is rejected LOUD as
        ``PrincipalStoreError`` — this is the pin a CREATE-only guard misses, and
        the store MUST wrap the engine's UNIQUE-on-UPDATE rejection (a raw
        ``SurrealError`` bubbling through would FAIL this pin, which is the point)."""
        await principal_store.create(email=_EMAIL_A, subject=_SUBJECT)  # owner holds _SUBJECT
        await principal_store.create(email=_EMAIL_B)  # subject NONE
        with pytest.raises(principals_module.PrincipalStoreError):
            await principal_store.set_subject(email=_EMAIL_B, subject=_SUBJECT)

    async def test_idempotent_re_fill_of_own_current_subject_succeeds(
        self, principal_store: Any
    ) -> None:
        """(iv) Setting a principal's subject to ITS OWN current value is NOT a
        UNIQUE conflict — idempotent re-login is safe (design §5). A build that
        naively treated any matching-subject row as a theft collision would reject
        the legitimate re-login and lock the user out."""
        await principal_store.create(email=_EMAIL_A, subject=_SUBJECT)
        again = await principal_store.set_subject(email=_EMAIL_A, subject=_SUBJECT)
        assert again.subject == _SUBJECT
        assert again.email == _EMAIL_A


# --------------------------------------------------------------------------- #
# Fork-6 module-docstring — the SERVED-PROSE instrument (design §6 / §8 item 9).
# "A DIAGNOSIS IS NOT AN INSTRUMENT": the one-column-one-identity-vocabulary law is
# guarded by NO gate unless a pin reads the prose. This pin makes the docstring
# NAME both sibling vocabularies AND the principal-specific constants, so a build
# that quietly conflated principal.role/status with the agent tuples goes RED.
# --------------------------------------------------------------------------- #


class TestModuleDocstringNamesBothVocabularies:
    async def test_docstring_distinguishes_principal_from_the_agent_vocabulary(
        self, principals_module: Any
    ) -> None:
        """Design §6: the ``loremaster.principals`` MODULE docstring must carry the
        clause that forbids conflating ``principal.role``/``status`` with the
        coincidentally-named ``agent`` columns. Discriminating tokens (a build that
        DROPPED the sibling-vocabulary clause — the exact defect — omits them):

        - ``agent`` — names the sibling table it must NOT be wired to;
        - ``input_required`` — an ``agent.status`` value ``principal`` does NOT have,
          so its presence proves the docstring describes the agent's DIFFERENT
          domain, not just principal's own;
        - ``_PRINCIPAL_ROLES`` + ``_PRINCIPAL_STATUSES`` — the principal-specific
          vocabulary TUPLES (proves it names THEM, never the agent tuples). ⚠ These
          are the SURVIVING constants after lead ruling A (2026-08-20) moved the
          closed-domain ASSERTs to CALL-TIME derivation: the module-level
          ``_PRINCIPAL_*_ALLOWED`` join constants were DELETED, so the corrected §6
          docstring names the tuples (design §3/§6 r2);
        - ``_TRACE_DECLARED_KEYS`` — the one-column-one-identity-vocabulary law
          anchor, cited by SYMBOL (design §6: never a bare line number).
        """
        doc = principals_module.__doc__ or ""
        required = (
            "agent",
            "input_required",
            "_PRINCIPAL_ROLES",
            "_PRINCIPAL_STATUSES",
            "_TRACE_DECLARED_KEYS",
        )
        missing = [token for token in required if token not in doc]
        assert not missing, (
            f"the loremaster.principals module docstring is missing the Fork-6 "
            f"vocabulary-distinction tokens {missing} (design §6): the served-prose law "
            f"that principal.role/status are NARROWER, own-constant domains and must never "
            f"be wired to the agent table's coincidentally-named columns"
        )


# =========================================================================== #
# PACKET 49 EXTENSION (contract-49-1, 2026-08-20): PrincipalStore.set_expires +
# PrincipalStore.delete. STUB surfaces raise NotImplementedError, so every pin below
# is RED for the RIGHT reason (behavioural, never ImportError). DESIGN:
# docs/design/2026-08-20-packet49-cli-keys.md §F1 (set-expiry) + §F2 (delete cascade).
# =========================================================================== #


def _future() -> datetime:
    return datetime(2027, 6, 1, 12, 0, tzinfo=UTC)


def _past() -> datetime:
    return datetime.now(UTC) - timedelta(hours=1)


# --------------------------------------------------------------------------- #
# set_expires (design §F1, Reading C — the standalone `set-expiry` verb).
# --------------------------------------------------------------------------- #


class TestSetExpires:
    async def test_set_expires_sets_a_value_on_a_known_principal(
        self, principal_store: Any
    ) -> None:
        """(set path) ``set_expires(email, at)`` sets the expiry; a FRESH read confirms it
        (get_by_email uses an explicit projection, so a NONE-vs-value confusion is caught).
        The returned Principal also carries the new value."""
        await principal_store.create(email=_EMAIL_A)  # expires_at NONE
        updated = await principal_store.set_expires(email=_EMAIL_A, expires_at=_future())
        assert updated.expires_at == _future()
        fetched = await principal_store.get_by_email(_EMAIL_A)
        assert fetched is not None and fetched.expires_at == _future()

    async def test_set_expires_clears_to_none_via_explicit_SET(
        self, principal_store: Any
    ) -> None:
        """⚠ (clear path) THE DISCRIMINATING PIN (design §F1): clearing must ``SET
        expires_at = NONE`` — an UPDATE that OMITS the column would leave the OLD value
        UNCHANGED. Create a principal WITH an expiry, then ``set_expires(clear)`` and
        assert it reads back ``None``. A build that "cleared" by omission fails here."""
        await principal_store.create(email=_EMAIL_A, expires_at=_future())
        precheck = await principal_store.get_by_email(_EMAIL_A)
        assert precheck is not None and precheck.expires_at == _future()  # it WAS set
        cleared = await principal_store.set_expires(email=_EMAIL_A, expires_at=None)
        assert cleared.expires_at is None
        fetched = await principal_store.get_by_email(_EMAIL_A)
        assert fetched is not None and fetched.expires_at is None

    async def test_set_expires_on_unknown_email_raises_not_found(
        self, principals_module: Any, principal_store: Any
    ) -> None:
        """An unknown email is a typed ``PrincipalNotFoundError`` — never a silent no-op
        (which a naive ``UPDATE … WHERE`` returning an empty set would be). Positive
        control: a KNOWN email DOES set, so the raise is attributable to the missing row."""
        with pytest.raises(principals_module.PrincipalNotFoundError):
            await principal_store.set_expires(email=_UNKNOWN_EMAIL, expires_at=_future())
        # POSITIVE CONTROL — a known email sets fine.
        await principal_store.create(email=_EMAIL_A)
        ok = await principal_store.set_expires(email=_EMAIL_A, expires_at=_future())
        assert ok.expires_at == _future()


# --------------------------------------------------------------------------- #
# delete (design §F2 — HARD delete + children-first cascade, one transaction).
# --------------------------------------------------------------------------- #


@pytest_asyncio.fixture()
async def principal_store_with_key_table(principals_module: Any) -> Any:
    """A ready ``PrincipalStore`` whose database ALSO carries the ``principal_key`` table
    (applied via an admin connection), so the delete-cascade pins can insert raw key rows
    without depending on ``PrincipalKeyStore``. On the STUB ``generate_principal_key_ddl``
    is empty, so this fixture reddens with a CLEAN message (the slice is unbuilt)."""
    env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    store = principals_module.PrincipalStore(
        url=env.url, namespace=env.namespace, database=env.database,
        user=env.user, password=env.password,
    )
    await store.ensure_ready()  # the principal table
    key_ddl = surreal_schema.generate_principal_key_ddl()
    assert key_ddl.strip(), (
        "generate_principal_key_ddl() is EMPTY — the principal_key slice is unbuilt "
        "(RED until packet 49 lands the emitter); the delete-cascade pins need the table"
    )
    admin = await connect_admin(env)
    try:
        await run(admin, key_ddl)  # the principal_key table
        # packet 61a-w1 (§FR-4): PrincipalStore.delete now READS the ``keep`` table
        # (refuse-while-keeping), so a store-level delete test must carry it too (principal
        # is readied first above, satisfying member_of's ENFORCED IN principal). Applied via
        # the admin connection like key_ddl. Production's sole caller readies it via the CLI
        # dispatch (D3); this aligns the store-level fixture with that dependency.
        await run(admin, surreal_schema.generate_keep_ddl())  # keep + member_of
    finally:
        await admin.close()
    try:
        yield store, env
    finally:
        await store.close()
        await drop_database(env)


async def _insert_raw_key(env: SurrealEnv, *, key_id: str, principal_id: str, name: str) -> None:
    """Insert a raw ``principal_key`` row owned by ``principal_id`` (a ``str(RecordID)``
    like ``principal:xxx``), binding the owner via ``type::record`` — no
    ``PrincipalKeyStore`` needed (the cascade is a ``PrincipalStore`` concern)."""
    rid = principal_id.split(":", 1)[1]  # the id part after the table name
    connection = await connect_admin(env)
    try:
        await run(
            connection,
            f"CREATE type::record('{surreal_schema.PRINCIPAL_KEY_TABLE}', $kid) CONTENT "
            f"{{ principal: type::record('{surreal_schema.PRINCIPAL_TABLE}', $pid), "
            f"hash: $hash, name: $name }}",
            {"kid": key_id, "pid": rid, "hash": key_id * 8, "name": name},
        )
    finally:
        await connection.close()


async def _count(env: SurrealEnv, table: str, where: str, params: dict[str, Any]) -> int:
    connection = await connect_admin(env)
    try:
        rows = await run(connection, f"SELECT count() FROM {table} WHERE {where} GROUP ALL", params)
    finally:
        await connection.close()
    if isinstance(rows, list) and rows:
        return int(rows[0].get("count", 0))
    return 0


class TestDelete:
    async def test_delete_cascades_all_keys_and_removes_the_principal(
        self, principal_store_with_key_table: tuple[Any, SurrealEnv]
    ) -> None:
        """Pin 13 (design §F2): a principal with N keys — after ``delete`` BOTH the
        principal row AND all N ``principal_key`` rows are gone (no orphans — record links
        do NOT auto-clean, §4). ``delete`` returns N (the cascaded-key count the CLI's
        audit line reports)."""
        store, env = principal_store_with_key_table
        created = await store.create(email=_EMAIL_A)
        await _insert_raw_key(env, key_id="k1", principal_id=created.id, name="laptop")
        await _insert_raw_key(env, key_id="k2", principal_id=created.id, name="ci")
        await _insert_raw_key(env, key_id="k3", principal_id=created.id, name="phone")

        removed = await store.delete(email=_EMAIL_A)
        assert removed == 3, f"delete must report the 3 cascaded keys, got {removed!r}"
        assert await store.get_by_email(_EMAIL_A) is None  # principal gone
        rid = created.id.split(":", 1)[1]
        remaining = await _count(
            env, surreal_schema.PRINCIPAL_KEY_TABLE,
            "principal = type::record('principal', $pid)", {"pid": rid},
        )
        assert remaining == 0, f"{remaining} orphaned principal_key rows survived the cascade"

    async def test_delete_of_a_keyless_principal_returns_zero(
        self, principal_store_with_key_table: tuple[Any, SurrealEnv]
    ) -> None:
        """A principal with NO keys deletes cleanly and reports 0 cascaded keys."""
        store, _env = principal_store_with_key_table
        await store.create(email=_EMAIL_A)
        removed = await store.delete(email=_EMAIL_A)
        assert removed == 0
        assert await store.get_by_email(_EMAIL_A) is None

    async def test_delete_only_touches_the_named_principals_keys(
        self, principal_store_with_key_table: tuple[Any, SurrealEnv]
    ) -> None:
        """⚠ FIXTURE-DISCRIMINATE: a second principal's keys MUST survive. A build whose
        cascade DELETE dropped its WHERE (``DELETE principal_key`` — every key) would wipe
        the bystander's key too. Two principals, each with a key; delete one; the other's
        key remains."""
        store, env = principal_store_with_key_table
        keep = await store.create(email=_EMAIL_B)
        drop = await store.create(email=_EMAIL_A)
        await _insert_raw_key(env, key_id="keep1", principal_id=keep.id, name="laptop")
        await _insert_raw_key(env, key_id="drop1", principal_id=drop.id, name="laptop")

        await store.delete(email=_EMAIL_A)

        assert await store.get_by_email(_EMAIL_B) is not None  # bystander principal survives
        keep_rid = keep.id.split(":", 1)[1]
        survivors = await _count(
            env, surreal_schema.PRINCIPAL_KEY_TABLE,
            "principal = type::record('principal', $pid)", {"pid": keep_rid},
        )
        assert survivors == 1, "the bystander principal's key was wrongly cascaded"

    async def test_delete_on_unknown_email_raises_not_found(
        self, principals_module: Any, principal_store_with_key_table: tuple[Any, SurrealEnv]
    ) -> None:
        """An unknown email is a typed ``PrincipalNotFoundError`` — never a silent no-op."""
        store, _env = principal_store_with_key_table
        with pytest.raises(principals_module.PrincipalNotFoundError):
            await store.delete(email=_UNKNOWN_EMAIL)

    def test_delete_runs_the_cascade_in_ONE_transaction(self, principals_module: Any) -> None:
        """Pin 13 (one transaction): the child + parent DELETEs run inside ONE
        ``execute_transaction`` (BEGIN … COMMIT) so a half-cascade can never leave orphaned
        keys (design §F2). A build issuing two separate ``_query`` DELETEs would fail here.
        AST over ``PrincipalStore.delete``'s OWN source (robust to line drift)."""
        source = inspect.getsource(principals_module.PrincipalStore.delete)
        tree = ast.parse(source.lstrip())
        called = {
            node.func.id if isinstance(node.func, ast.Name) else
            node.func.attr if isinstance(node.func, ast.Attribute) else None
            for node in ast.walk(tree) if isinstance(node, ast.Call)
        }
        assert "execute_transaction" in called, (
            "PrincipalStore.delete must run its children-first cascade inside ONE "
            "execute_transaction (BEGIN … COMMIT) — not two separate _query DELETEs — so a "
            "mid-cascade failure leaves neither half committed (design §F2)"
        )
