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

import importlib
from datetime import UTC, datetime
from typing import Any

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)

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
