"""Contract — the packet-61a-w2 extraction: the record-substrate stores (Principal,
PrincipalKey, Keep) route their engine-rejection wrapping through the ONE two-layer seam
(``lorerunes.reclassify`` + ``loremaster.store._txn.wrap_store_rejection``), and NO
loremaster module carries a hand-rolled pure-translate wrap clone.

RED before the extraction build; authored by ``contract-61a-w2`` (session ``pkt61``) at HEAD
``fb68427``, REVISED per ``docs/design/2026-08-22-packet61-pdp-audit-rulings.md`` §"Fork I
addendum" (D2 — two-layer seam) + §"Fork I addendum-2" (shape-keyed guard + route
``principal_keys``) + §"Fork I addendum-4" (PRESERVE ``tasks.transitive_blockers`` — NOT a full
#400 clone — key the guard on the FULL idiom, not the bare translate line) + §"Fork I
addendum-5" (recognize the passthrough-first POLICY in BOTH house spellings — one tuple clause
OR two separate clauses — and pin the conditional-reraise evasion as an accepted bound). Store
law: ``docs/reference/surrealdb-31-capabilities.md`` §3 (error-classification hierarchy).

------------------------------------------------------------------------------
THE TWO-LAYER SEAM (D2), and WHY (finding #400 / ONE-IMPLEMENTATION):

  * **Layer 1 — ``lorerunes.reclassify``** (control-flow POLICY; semantics pinned in
    ``lorerunes/tests/test_engine_rejection.py``): stdlib-only, parameterised over the
    exception classes.
  * **Layer 2 — ``loremaster.store._txn.wrap_store_rejection(domain_error, context)``**: binds
    the surreal taxonomy ONCE (``passthrough=(SurrealConnectionError,
    TxnContentionExhaustedError)``, ``catch=(SurrealStoreError,)``,
    ``make_error=lambda: domain_error(context)``) and delegates to ``reclassify``.
  * Every store write-path calls Layer 2. Option (b) — stores calling ``reclassify`` directly,
    each passing the taxonomy — is REJECTED (it re-clones the taxonomy per store, #400 one
    level down). The two-layer mutation proof (§SHARING) enforces BOTH layers are shared.

W2 ROUTES EVERY FULL-#400 CLONE IN THE PACKAGE (addendum-4): PrincipalStore.{create,
set_subject} + PrincipalKeyStore.{mint} + KeepStore.{create_keep, add_household_member,
remove_household_member, set_rank, set_keeper, delete_keep} = 9 paths. (AuditStore.append is
born-wrapped in w4 — not here.) The scope boundary is the FULL #400 idiom (SHAPE), not a store
family — so a faithful clone in ANY store is in scope, and the shape-guard's allowlist is empty.

------------------------------------------------------------------------------
THE REACH GUARD IS SHAPE-KEYED, NOT A STORE HAND-LIST (addendum-2 item 1). The prior
contract's ``_CASES={keep, principal}`` was a 2-store hand-list — the reach-law defeat the
adversary caught. The replacement AST-walks EVERY loremaster module for the FULL #400 idiom
(``_try_has_full_idiom``: a passthrough-first ``except (SurrealConnectionError,
TxnContentionExhaustedError): raise`` PRECEDING a sole-body ``except SurrealStoreError as e:
raise <DomainError>(...) from e``) and asserts it appears NOWHERE outside the seam. The idiom
is the discriminator: the CAS-re-validation idiom (tasks/findings — a follow-up read +
``_validate_transition``), the fence-verdict idiom (floor_calibration — a branch), AND a
translate WITHOUT a passthrough-first clause (``transitive_blockers``) all fail to match, so
the shape structurally EXCLUDES them with no allowlist of stores.

⚠ WHY THE GUARD KEYS ON THE FULL IDIOM (addendum-4, the instrument-lesson). A prior revision
keyed on the bare translate LINE and matched a 10th site the addendum-2 hand-verification
missed — ``tasks.py::transitive_blockers``. Ground-truth (surfaced by this contract, CONFIRMED
by the sidecar): ``transitive_blockers`` has NO passthrough-first clause, so it DELIBERATELY
wraps transport faults too (a DIFFERENT policy — wrap-everything — that #400 must not change).
Keying on a FRAGMENT of the policy matched a site with a different WHOLE policy. So the guard
now keys on the full idiom, which excludes ``transitive_blockers`` BY SHAPE; it is PRESERVED,
and its transport-wrap consistency is ledgered separately (#408). The allowlist stays EMPTY
(``test_the_allowlist_is_empty``) — the shape is the sole discriminator, no per-site exemption.

WHY RED NOW (contract-first): ``lorerunes.reclassify`` + ``_txn.wrap_store_rejection`` do not
exist at HEAD, and at HEAD all 9 full-idiom paths wrap LOCALLY. Loaders ``pytest.fail`` CLEANLY
(finding #133 idiom); the reach + routing + mutation pins are RED against the private copies and
GREEN once all 9 route through the two-layer seam.
"""

from __future__ import annotations

import ast
import contextlib
import importlib
import sys
from collections.abc import Awaitable, Callable, Iterator
from pathlib import Path
from typing import Any

import loremaster.keeps as keeps_module
import loremaster.principal_keys as principal_keys_module
import loremaster.principals as principals_module
import pytest
import pytest_asyncio
from _enforced_relations_scaffold import ghost_id
from _surreal_harness import (
    PRODUCTION_DIM,
    SurrealEnv,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.keeps import KeepStore, KeepStoreError
from loremaster.principal_keys import PrincipalKeyStore, PrincipalKeyStoreError
from loremaster.principals import PrincipalStore, PrincipalStoreError
from loremaster.store._txn import (
    SurrealConnectionError,
    SurrealStoreError,
    TxnContentionExhaustedError,
)
from loremaster.store.surreal_schema import KEEP_TABLE

import loremaster

_LORERUNES = "lorerunes"
_RECLASSIFY = "reclassify"  # Layer 1 (lorerunes)
_WRAP_STORE = "wrap_store_rejection"  # Layer 2 (loremaster.store._txn) — the store-facing seam

# The store-facing seam name a store method routes through (Layer 2). The routed-set
# derivation keys on it. A store calling reclassify DIRECTLY (rejected option (b)) is caught
# by the Layer-2 mutation pin, not this derivation.
_SHARED_SEAM_NAMES = frozenset({_WRAP_STORE})

_KEEPER_EMAIL = "alice@example.com"
_MEMBER_EMAIL = "bob@example.com"
_FRESH_EMAIL = "new-principal@example.com"
_SUBJECT = "google-oauth2|118427905123456789012"


# ===========================================================================
# Loaders (lazy, clean RED — finding #133 idiom)
# ===========================================================================


def _load_reclassify() -> Any:
    """Return ``lorerunes.reclassify`` (Layer 1) once built, else ``pytest.fail`` CLEANLY."""
    package = importlib.import_module(_LORERUNES)
    reclassify = getattr(package, _RECLASSIFY, None)
    if reclassify is None:
        pytest.fail(
            f"{_LORERUNES}.{_RECLASSIFY} not yet built (packet 61a-w2) — RED until it lands",
            pytrace=False,
        )
    return reclassify


def _load_wrap_store() -> Any:
    """Return ``loremaster.store._txn.wrap_store_rejection`` (Layer 2) once built, else fail."""
    txn = importlib.import_module("loremaster.store._txn")
    wrap = getattr(txn, _WRAP_STORE, None)
    if wrap is None:
        pytest.fail(
            f"loremaster.store._txn.{_WRAP_STORE} not yet built (packet 61a-w2) — RED until it lands",
            pytrace=False,
        )
    return wrap


# ===========================================================================
# THE SHAPE DETECTOR — the FULL #400 idiom, keyed on the handler GROUP (addendum-4)
# ===========================================================================
# ⚠ THE KEY IS THE FULL POLICY, NOT A FRAGMENT (addendum-4, the instrument-lesson).
# The first shape-guard keyed on the bare translate LINE (a sole-body ``except
# SurrealStoreError: raise <Domain> from e``). That was too LOOSE: it matched a
# wrap-EVERYTHING site — ``tasks.transitive_blockers`` — that shares the translate substring
# but has NO passthrough-first clause, so it deliberately wraps transport faults too (a
# DIFFERENT policy #400 must not change; preserved + ledgered #408). Keying on a fragment of
# the policy matched a site with a different whole policy. So the guard now keys on the FULL
# #400 idiom: a handler GROUP where ``except (SurrealConnectionError,
# TxnContentionExhaustedError): raise`` (the passthrough-first re-raise of BOTH transport
# classes) PRECEDES a sole-body ``except SurrealStoreError as e: raise <Domain>(...) from e``.
# This structurally EXCLUDES transitive_blockers (no passthrough-first) and reds a future
# FULL-#400 clone.


def _handler_names(handler_type: ast.expr | None) -> set[str]:
    """The exception class NAMES an ``except`` clause catches (a bare ``Name``, or the members
    of a ``Tuple`` of ``Name``s). ``except SurrealStoreError`` → {'SurrealStoreError'};
    ``except (SurrealConnectionError, TxnContentionExhaustedError)`` → both names."""
    if handler_type is None:
        return set()
    nodes: list[ast.expr] = (
        list(handler_type.elts) if isinstance(handler_type, ast.Tuple) else [handler_type]
    )
    return {node.id for node in nodes if isinstance(node, ast.Name)}


def _handler_catches_store_error(handler: ast.ExceptHandler) -> bool:
    """``except SurrealStoreError`` (a bare Name, or a Tuple containing it)."""
    return "SurrealStoreError" in _handler_names(handler.type)


# The transport classes the passthrough-first policy must re-raise (store ref §3, _txn.py:120/156).
_PASSTHROUGH_CLASSES = frozenset({"SurrealConnectionError", "TxnContentionExhaustedError"})


def _bare_reraise_passthrough_classes(handler: ast.ExceptHandler) -> set[str]:
    """The transport classes a BARE-re-raise handler covers (sole body ``raise`` with no
    ``exc``). Returns the subset of :data:`_PASSTHROUGH_CLASSES` it re-raises, or empty if the
    handler is not a bare re-raise. Spelling-agnostic on purpose (addendum-5): it counts the
    classes covered whether the caller writes ONE tuple ``except (Conn, Contention): raise`` OR
    TWO separate ``except Conn: raise`` / ``except Contention: raise`` clauses — the caller's
    UNION over the handler list is what must cover both."""
    if not (
        len(handler.body) == 1
        and isinstance(handler.body[0], ast.Raise)
        and handler.body[0].exc is None  # a BARE re-raise, not `raise Something(...)`
    ):
        return set()
    return _handler_names(handler.type) & _PASSTHROUGH_CLASSES


def _is_pure_translate_handler(handler: ast.ExceptHandler) -> bool:
    """The translate clause: ``except SurrealStoreError as <e>:`` whose body is EXACTLY a single
    ``raise <DomainError>(...) from <e>``. Excludes CAS (multi-statement body), fence (a branch,
    body[0] not a bare Raise), and a raise chained from a different name."""
    if not _handler_catches_store_error(handler) or handler.name is None:
        return False
    if len(handler.body) != 1:
        return False
    stmt = handler.body[0]
    return (
        isinstance(stmt, ast.Raise)
        and isinstance(stmt.exc, ast.Call)
        and isinstance(stmt.cause, ast.Name)
        and stmt.cause.id == handler.name
    )


def _try_has_full_idiom(node: ast.Try) -> bool:
    """The FULL #400 idiom, keyed on the passthrough-first POLICY regardless of house SPELLING
    (addendum-5): a ``try`` whose handlers, BEFORE a sole-body ``SurrealStoreError`` translate,
    bare-re-raise BOTH transport classes (their UNION ⊇ :data:`_PASSTHROUGH_CLASSES`) — whether
    as one tuple clause or two separate clauses. The ORDER is load-bearing (the passthrough must
    precede the translate, since the transport classes subclass ``SurrealStoreError``), so only
    handlers BEFORE the translate count.

    Correctly EXCLUDES: ``transitive_blockers`` (no passthrough at all); a CAS/fence translate
    (multi-statement / branch body → not a sole-body translate); a PARTIAL passthrough (only one
    transport class covered, either spelling). ⚠ KNOWN BOUND (see
    ``test_the_conditional_reraise_shape_is_a_KNOWN_BOUND``): a full clone written as a
    CONDITIONAL re-raise INSIDE the single ``SurrealStoreError`` handler is a non-house structure
    that evades this by design."""
    translate_idx = next(
        (i for i, h in enumerate(node.handlers) if _is_pure_translate_handler(h)), None
    )
    if translate_idx is None:
        return False
    covered: set[str] = set()
    for handler in node.handlers[:translate_idx]:  # only handlers BEFORE the translate
        covered |= _bare_reraise_passthrough_classes(handler)
    return _PASSTHROUGH_CLASSES <= covered


# The seam function itself may legitimately carry the idiom IF a builder inlines the handlers
# into wrap_store_rejection rather than delegating to lorerunes.reclassify (D2 permits the
# ergonomic form). In the ruled two-layer build the handlers live in lorerunes.reclassify
# (OUTSIDE loremaster's scan scope), so this exemption never actually matches.
_SEAM_FUNCTION = _WRAP_STORE

# ⚠ THE ALLOWLIST IS EMPTY, AND THAT IS THE WHOLE POINT (Fork I addendum-3/4). The scope
# boundary is the FULL #400 idiom (SHAPE), not a store family — so a faithful clone in ANY
# store is in scope, and there are NO per-site exemptions. The first revisions found
# ``tasks.transitive_blockers`` via a too-loose bare-translate key; addendum-4 PRESERVES it
# (it is a DIFFERENT policy — wrap-everything, no passthrough-first — ledgered #408) and
# EXCLUDES it BY SHAPE via ``_try_has_full_idiom`` (no allowlist entry). A non-empty allowlist
# here is a RED FLAG: it means someone reintroduced a hand-list. ``test_the_allowlist_is_empty``
# reds if it grows.
_ALLOWLISTED_FULL_IDIOM: frozenset[tuple[str, str]] = frozenset()


def _loremaster_modules() -> list[Path]:
    """Every ``loremaster.loremaster`` source file — the guard's reach is DERIVED from the
    package tree, never a hand-list of modules (addendum-2 item 1: AST-walk EVERY module)."""
    root = Path(loremaster.__file__).resolve().parent
    return sorted(root.rglob("*.py"))


def _full_idiom_sites() -> list[tuple[str, str, int]]:
    """Every FULL #400-idiom ``try`` site in the loremaster package (a passthrough-first handler
    preceding a sole-body ``SurrealStoreError`` translate — ``_try_has_full_idiom``), EXCLUDING
    the seam function and the (empty) allowlist. Returns (module_basename, enclosing_function,
    lineno). The reach guard asserts this is EMPTY (every faithful clone routed through the
    seam). ``transitive_blockers`` — a translate WITHOUT a passthrough-first clause — does NOT
    match (addendum-4)."""
    sites: list[tuple[str, str, int]] = []
    for path in _loremaster_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for func in ast.walk(tree):
            if not isinstance(func, ast.AsyncFunctionDef | ast.FunctionDef):
                continue
            for node in ast.walk(func):
                if not (isinstance(node, ast.Try) and _try_has_full_idiom(node)):
                    continue
                if func.name == _SEAM_FUNCTION:
                    continue  # the seam is the ONE allowed home for the idiom
                if (path.name, func.name) in _ALLOWLISTED_FULL_IDIOM:
                    continue  # (empty) — a non-empty entry is a reintroduced hand-list
                sites.append((path.name, func.name, node.lineno))
    return sites


# ===========================================================================
# Per-store descriptors — for the routed-set coverage + mutation + behaviour ∀s.
# (NOT the reach guard, which is the shape scan above; these carry the invocations.)
# ===========================================================================


class _StoreCase:
    def __init__(
        self,
        *,
        label: str,
        module: Any,
        class_name: str,
        domain_error: type[Exception],
        invocations: dict[str, Callable[[Any], Awaitable[object]]],
        expected_wrappers: frozenset[str],
    ) -> None:
        self.label = label
        self.module = module
        self.class_name = class_name
        self.domain_error = domain_error
        self.invocations = invocations
        self.expected_wrappers = expected_wrappers


_KEEP_GHOST = f"{KEEP_TABLE}:{ghost_id('engine_rejection_seam_keep')}"

_KEEP_INVOCATIONS: dict[str, Callable[[KeepStore], Awaitable[object]]] = {
    "create_keep": lambda s: s.create_keep(keeper_email=_KEEPER_EMAIL, type="project", name="wrap"),
    "add_household_member": lambda s: s.add_household_member(
        keep_id=_KEEP_GHOST, member_email=_MEMBER_EMAIL
    ),
    "remove_household_member": lambda s: s.remove_household_member(
        keep_id=_KEEP_GHOST, member_email=_MEMBER_EMAIL
    ),
    "set_rank": lambda s: s.set_rank(
        keep_id=_KEEP_GHOST, member_email=_MEMBER_EMAIL, rank="contributor"
    ),
    "set_keeper": lambda s: s.set_keeper(keep_id=_KEEP_GHOST, new_keeper_email=_KEEPER_EMAIL),
    "delete_keep": lambda s: s.delete_keep(keep_id=_KEEP_GHOST),
    # packet 61b-w2 (Fork F / D1): the born-wrapped READ verb. Unlike the 6 write verbs
    # above, list_keeps_for_member is a SELECT-only read — but it FEEDS the PDP's
    # visible_keep_ids, so D1 made it born-wrapped (a raw engine error mid-authorization is
    # exactly the consumer-law leak). It routes through wrap_store_rejection, so the reach
    # pin (coverage-as-checked-variable) requires this fault-injection invocation. Resolves a
    # SEEDED email (via the composed, un-patched PrincipalStore), so under injection at the
    # keeps run_query seam the member_of SELECT is what raises.
    "list_keeps_for_member": lambda s: s.list_keeps_for_member(member_email=_KEEPER_EMAIL),
}

_PRINCIPAL_INVOCATIONS: dict[str, Callable[[PrincipalStore], Awaitable[object]]] = {
    "create": lambda s: s.create(email=_FRESH_EMAIL),
    "set_subject": lambda s: s.set_subject(email=_KEEPER_EMAIL, subject=_SUBJECT),
}

_PRINCIPAL_KEY_INVOCATIONS: dict[str, Callable[[PrincipalKeyStore], Awaitable[object]]] = {
    # mint resolves the owner via the COMPOSED PrincipalStore (principals seam, NOT patched),
    # so under fault injection at the principal_keys seam the CREATE is what raises.
    "mint": lambda s: s.mint(email=_KEEPER_EMAIL, name="laptop", secret_hash="deadbeef" * 8),
}

# ⚠ tasks.transitive_blockers is DELIBERATELY NOT a case here (addendum-4): it is NOT a full
# #400 clone (no passthrough-first clause — it wraps transport too), so #400 preserves it and
# the full-idiom guard excludes it BY SHAPE. Its transport-wrap consistency is ledgered #408.


_CASES: tuple[_StoreCase, ...] = (
    _StoreCase(
        label="keep",
        module=keeps_module,
        class_name="KeepStore",
        domain_error=KeepStoreError,
        invocations=_KEEP_INVOCATIONS,
        expected_wrappers=frozenset(_KEEP_INVOCATIONS),
    ),
    _StoreCase(
        label="principal",
        module=principals_module,
        class_name="PrincipalStore",
        domain_error=PrincipalStoreError,
        invocations=_PRINCIPAL_INVOCATIONS,
        expected_wrappers=frozenset(_PRINCIPAL_INVOCATIONS),
    ),
    _StoreCase(
        label="principal_key",
        module=principal_keys_module,
        class_name="PrincipalKeyStore",
        domain_error=PrincipalKeyStoreError,
        invocations=_PRINCIPAL_KEY_INVOCATIONS,
        expected_wrappers=frozenset(_PRINCIPAL_KEY_INVOCATIONS),
    ),
)
_CASES_BY_LABEL = {case.label: case for case in _CASES}
_CASE_METHODS: list[tuple[str, str]] = [
    (case.label, method) for case in _CASES for method in sorted(case.invocations)
]


def _case_ids() -> list[str]:
    return [case.label for case in _CASES]


# ===========================================================================
# AST — the routed set per store (methods referencing the Layer-2 seam)
# ===========================================================================


def _methods_routing_through_seam(module: Any, class_name: str) -> set[str]:
    """Methods whose body references ``wrap_store_rejection`` — the ROUTED set. Post-
    extraction it equals the invocation map (coverage-as-checked-variable: a new routed path
    forces a mutation invocation). RED at HEAD (nothing routes → empty)."""
    source = Path(module.__file__).read_text(encoding="utf-8")
    cls = next(
        n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.ClassDef) and n.name == class_name
    )
    out: set[str] = set()
    for method in cls.body:
        if not isinstance(method, ast.AsyncFunctionDef | ast.FunctionDef):
            continue
        for node in ast.walk(method):
            if isinstance(node, ast.Name) and node.id in _SHARED_SEAM_NAMES:
                out.add(method.name)
    return out


# ===========================================================================
# Fixture — the three record-substrate stores that own a routed wrap, keeper + member seeded.
# ===========================================================================


@pytest_asyncio.fixture()
async def stores() -> Any:
    """Ready PrincipalStore + PrincipalKeyStore + KeepStore on a fresh unique database, keeper
    + member principals seeded, reaped on exit (``principal`` table FIRST — endpoint + link
    target — then the key + keep slices)."""
    env: SurrealEnv = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    principal_store = PrincipalStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    key_store = PrincipalKeyStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    keep_store = KeepStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await principal_store.ensure_ready()
    await key_store.ensure_ready()
    await keep_store.ensure_ready()
    for email in (_KEEPER_EMAIL, _MEMBER_EMAIL):
        await principal_store.create(email=email)
    try:
        yield principal_store, key_store, keep_store, env
    finally:
        await keep_store.close()
        await key_store.close()
        await principal_store.close()
        await drop_database(env)


def _store_under_test(
    case: _StoreCase, principal: PrincipalStore, key: PrincipalKeyStore, keep: KeepStore
) -> Any:
    return {"principal": principal, "principal_key": key, "keep": keep}[case.label]


# ===========================================================================
# 1. REACH — the FULL-#400-IDIOM shape guard: no faithful clone outside the seam
# ===========================================================================


class TestNoFullIdiomCloneOutsideTheSeam:
    """THE REACH PIN (addendum-2 item 1, refined by addendum-4/5), keyed on the FULL #400 idiom
    — the passthrough-first POLICY (bare-re-raise of BOTH transport classes, in EITHER house
    spelling — one tuple clause OR two separate clauses) PRECEDING a sole-body
    ``SurrealStoreError`` translate — DERIVED over EVERY loremaster module (NOT a hand-list of
    stores; the reach-law defeat the adversary caught).

    ⚠ THREAT MODEL (a gate needs a threat model): this guard catches the HONEST COPY-PASTER who
    clones an existing HOUSE #400 wrap idiom (either of the two except-clause spellings). It is
    NOT a boundary against a deliberate obfuscator. One non-house structure — a CONDITIONAL
    re-raise inside a single ``except SurrealStoreError`` handler — evades it BY DESIGN and is
    pinned as an accepted bound (``test_the_conditional_reraise_shape_is_a_KNOWN_BOUND``);
    chasing further exotic spellings is the reach spiral the CLAUDE.md STOP-rule forbids."""

    def test_no_full_idiom_wrap_appears_outside_the_seam(self) -> None:
        """RED at HEAD (the 9 substrate clones carry the full idiom); GREEN once all route
        through ``wrap_store_rejection``; RED again if a future FULL-#400 clone is hand-rolled in
        EITHER house spelling. Mutation-provable: reintroduce a passthrough-first (tuple OR
        two-clause) + sole-body-translate ``try`` in any module → this reddens.
        ``transitive_blockers`` (translate WITHOUT any passthrough) does NOT match — addendum-4
        preserves it, ledgered #408."""
        sites = _full_idiom_sites()
        assert sites == [], (
            "FULL #400-idiom wrap clones (a bare-re-raise of BOTH SurrealConnectionError AND "
            "TxnContentionExhaustedError — one tuple clause OR two separate clauses — THEN a "
            "sole-body `except SurrealStoreError as e: raise <DomainError>(...) from e`) still "
            "exist OUTSIDE loremaster.store._txn.wrap_store_rejection — every such site must route "
            f"through the shared seam (finding #400, ROUTING-IS-NOT-SHARING): {sites}"
        )

    def test_the_detector_keys_on_the_policy_in_BOTH_house_spellings(self) -> None:
        """POSITIVE CONTROL ON THE DETECTOR (a probe needs a control): ``_try_has_full_idiom``
        flags the FULL idiom in BOTH house spellings — one tuple clause AND two separate clauses
        (addendum-5: a clone in either spelling must red) — and NOT the sibling shapes. GREEN
        throughout."""

        def _try(src: str) -> ast.Try:
            return next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Try))

        full_tuple = _try(  # HOUSE SPELLING 1 — one tuple clause (the substrate stores)
            "try:\n x()\n"
            "except (SurrealConnectionError, TxnContentionExhaustedError):\n raise\n"
            "except SurrealStoreError as e:\n raise KeepStoreError('m') from e\n"
        )
        full_two_clause = _try(  # HOUSE SPELLING 2 — two separate clauses (tasks/findings idiom)
            "try:\n x()\n"
            "except SurrealConnectionError:\n raise\n"
            "except TxnContentionExhaustedError:\n raise\n"
            "except SurrealStoreError as e:\n raise TaskLedgerError('m') from e\n"
        )
        translate_only = _try(  # transitive_blockers's shape — NO passthrough at all
            "try:\n x()\nexcept SurrealStoreError as e:\n raise TaskLedgerError('m') from e\n"
        )
        wrong_order = _try(  # translate BEFORE the passthrough — not the load-bearing order
            "try:\n x()\n"
            "except SurrealStoreError as e:\n raise KeepStoreError('m') from e\n"
            "except (SurrealConnectionError, TxnContentionExhaustedError):\n raise\n"
        )
        cas = _try(  # two-clause passthrough BUT a multi-statement translate → not a clone
            "try:\n x()\n"
            "except SurrealConnectionError:\n raise\n"
            "except TxnContentionExhaustedError:\n raise\n"
            "except SurrealStoreError as e:\n"
            " row = read()\n _validate_transition(row)\n raise TaskLedgerError('m') from e\n"
        )
        partial_tuple = _try(  # only ONE transport class (tuple of one) — not the full policy
            "try:\n x()\n"
            "except (SurrealConnectionError,):\n raise\n"
            "except SurrealStoreError as e:\n raise KeepStoreError('m') from e\n"
        )
        partial_two_clause = _try(  # only ONE separate clause — not the full policy
            "try:\n x()\n"
            "except SurrealConnectionError:\n raise\n"
            "except SurrealStoreError as e:\n raise KeepStoreError('m') from e\n"
        )
        assert _try_has_full_idiom(full_tuple) is True, "the full idiom (tuple spelling) must be flagged"
        assert _try_has_full_idiom(full_two_clause) is True, (
            "the full idiom in the TWO-CLAUSE house spelling must ALSO be flagged (addendum-5: "
            "keying on the single-tuple spelling let a two-clause clone evade)"
        )
        assert _try_has_full_idiom(translate_only) is False, (
            "a translate WITHOUT any passthrough (transitive_blockers's shape) must NOT be flagged"
        )
        assert _try_has_full_idiom(wrong_order) is False, "the passthrough must PRECEDE the translate"
        assert _try_has_full_idiom(cas) is False, "a multi-statement (CAS) translate must NOT be flagged"
        assert _try_has_full_idiom(partial_tuple) is False, (
            "a passthrough covering only ONE transport class (tuple spelling) is not the full policy"
        )
        assert _try_has_full_idiom(partial_two_clause) is False, (
            "a passthrough covering only ONE transport class (two-clause spelling) is not the policy"
        )

    def test_the_conditional_reraise_shape_is_a_KNOWN_BOUND(self) -> None:
        """PIN THE MISS (#137/#138 — when you cannot close a hole, pin it). A full-#400-EQUIVALENT
        clone written as a CONDITIONAL re-raise INSIDE a single ``except SurrealStoreError``
        handler —
            ``except SurrealStoreError as e:``
            ``    if isinstance(e, (SurrealConnectionError, TxnContentionExhaustedError)): raise``
            ``    raise KeepStoreError(...) from e``
        — is a NON-HOUSE structure that EVADES the AST detector by design: it is neither a
        separate bare-re-raise passthrough handler nor a sole-body translate (the handler body is
        an ``if`` + a raise). This is an ACCEPTED BOUND, not a defect: the threat model
        (``test_the_detector...`` docstring) is the honest copy-paster of a HOUSE spelling, and
        chasing exotic spellings is the reach spiral the CLAUDE.md STOP-rule forbids. This pin
        asserts the bound so the next engineer meets it DELIBERATELY.

        RE-OPEN TRIGGER: a full-#400 clone appears in this non-house conditional-reraise spelling,
        OR the threat model gains a deliberate obfuscator. If you then extend ``_try_has_full_idiom``
        to catch it, this pin reds — DELETE it and say so (a closed bound is not a silently
        inherited one). GREEN today (the detector returns False for the conditional shape)."""

        def _try(src: str) -> ast.Try:
            return next(n for n in ast.walk(ast.parse(src)) if isinstance(n, ast.Try))

        conditional_reraise = _try(
            "try:\n x()\n"
            "except SurrealStoreError as e:\n"
            " if isinstance(e, (SurrealConnectionError, TxnContentionExhaustedError)):\n  raise\n"
            " raise KeepStoreError('m') from e\n"
        )
        assert _try_has_full_idiom(conditional_reraise) is False, (
            "the conditional-reraise shape is a KNOWN, ACCEPTED bound (#137/#138) — if this now "
            "returns True the detector was extended to catch it; DELETE this bound pin and say so "
            "in the report (a closed bound must not be inherited as still-open)"
        )

    def test_the_allowlist_is_empty(self) -> None:
        """THE SHAPE IS THE SOLE DISCRIMINATOR — the allowlist stays EMPTY (Fork I addendum-3/4).
        A non-empty allowlist reintroduces the exact hand-list the shape-guard exists to KILL:
        the scope boundary is the FULL #400 idiom, not a store family, and every faithful clone
        routes through the seam with NO exemption. This pin reds the moment someone adds an
        allowlist entry. GREEN throughout."""
        assert _ALLOWLISTED_FULL_IDIOM == frozenset(), (
            "the full-idiom shape-guard allowlist must be EMPTY — an entry is a hand-list "
            "reintroduced (addendum-4: exclude by SHAPE, never a per-site allowlist). Present "
            f"entries: {sorted(_ALLOWLISTED_FULL_IDIOM)}"
        )


# ===========================================================================
# 2. COVERAGE — the routed set is DERIVED and matches the invocation map
# ===========================================================================


class TestTheRoutedSetIsDerivedAndComplete:
    """Coverage-as-checked-variable for the mutation ∀: after extraction the DERIVED routed set
    (methods referencing ``wrap_store_rejection``) equals the fault-injection invocation map
    AND the known wrapping verbs — so a new routed path forces a mutation invocation. RED at
    HEAD (nothing routes → derived empty ≠ non-empty map)."""

    @pytest.mark.parametrize("label", _case_ids())
    def test_the_routed_set_equals_the_invocation_map(self, label: str) -> None:
        case = _CASES_BY_LABEL[label]
        routed = _methods_routing_through_seam(case.module, case.class_name)
        assert routed == set(case.invocations), (
            f"{case.class_name}'s routed set (methods calling {sorted(_SHARED_SEAM_NAMES)}) has "
            f"drifted from the fault-injection map — a new routed write path must add a mutation "
            f"invocation (reach law). routed={sorted(routed)!r} mapped={sorted(case.invocations)!r}"
        )

    @pytest.mark.parametrize("label", _case_ids())
    def test_the_routed_set_equals_the_known_wrapping_verbs(self, label: str) -> None:
        case = _CASES_BY_LABEL[label]
        routed = _methods_routing_through_seam(case.module, case.class_name)
        assert routed == case.expected_wrappers, (
            f"{case.class_name}'s routed set {sorted(routed)} != the known wrapping verbs "
            f"{sorted(case.expected_wrappers)}"
        )


# ===========================================================================
# 3. SHARING PROVEN BY MUTATION — the two-layer DRY discriminator
# ===========================================================================


class _WrapInvokedMarker(RuntimeError):
    """Raised by the marker context manager the mutation swaps in for a seam layer. Its
    appearance PROVES the guarded block ran inside that shared layer; a store that raised its
    own domain error kept a private copy (ROUTING IS NOT SHARING)."""


@contextlib.contextmanager
def _marker_cm() -> Iterator[None]:
    try:
        yield
    except _WrapInvokedMarker:
        raise
    except Exception as error:  # noqa: BLE001 - the probe deliberately intercepts everything
        raise _WrapInvokedMarker(str(error)) from error


def _marker_factory(*_args: Any, **_kwargs: Any) -> Any:
    """A stand-in for either seam layer (accepts any call signature), returning the marker CM."""
    return _marker_cm()


def _patch_everywhere(monkeypatch: pytest.MonkeyPatch, name: str, replacement: Any) -> int:
    """Rebind ``name`` in EVERY loaded module that exposes it (the ``test_secret_typing.
    _patch_everywhere`` idiom). Covers both a direct import and a call-time delegator. A store
    with a genuinely private copy is not patched, does not change, and is caught. Returns the
    count patched (asserted non-zero so a no-op patch cannot pass vacuously)."""
    patched = 0
    for module in list(sys.modules.values()):
        if module is None or not hasattr(module, name):
            continue
        monkeypatch.setattr(module, name, replacement, raising=False)
        patched += 1
    return patched


def _inject_store_error(monkeypatch: pytest.MonkeyPatch, case: _StoreCase) -> None:
    """Make the store-under-test's write seams raise a raw ``SurrealStoreError`` (patched on
    the STORE's own module only, so a composed PrincipalStore's email resolution still
    succeeds — the FR-2 Q2b idiom)."""

    async def _raise_store_error(*_args: object, **_kwargs: object) -> object:
        raise SurrealStoreError(f"injected engine rejection ({case.label})")

    monkeypatch.setattr(case.module, "run_query", _raise_store_error, raising=False)
    monkeypatch.setattr(case.module, "execute_transaction", _raise_store_error, raising=False)


class TestSharingProvenByMutation:
    """THE two-layer DRY discriminator — ∀ over every routed path in ALL THREE substrate stores.
    Mutating EITHER seam layer must move every routed path (D2 two-layer mutation proof):
      * Layer 1 (``lorerunes.reclassify``) → a store not routing through the control-flow is a
        fully-private copy;
      * Layer 2 (``_txn.wrap_store_rejection``) → a store calling ``reclassify`` DIRECTLY with a
        cloned taxonomy (rejected option (b)) survives the Layer-1 patch but NOT this one.
    RED at HEAD (neither seam layer exists; the private copies route through neither)."""

    @pytest.mark.parametrize(("label", "method_name"), _CASE_METHODS)
    async def test_dropping_LAYER1_reclassify_moves_every_routed_path(
        self,
        stores: tuple[PrincipalStore, PrincipalKeyStore, KeepStore, SurrealEnv],
        monkeypatch: pytest.MonkeyPatch,
        label: str,
        method_name: str,
    ) -> None:
        _load_reclassify()  # clean RED if Layer 1 does not exist
        case = _CASES_BY_LABEL[label]
        principal, key, keep, _env = stores
        store = _store_under_test(case, principal, key, keep)
        patched = _patch_everywhere(monkeypatch, _RECLASSIFY, _marker_factory)
        assert patched, f"{_RECLASSIFY} exposed by NO module — the Layer-1 mutation patched nothing"
        _inject_store_error(monkeypatch, case)
        with pytest.raises(_WrapInvokedMarker):
            await case.invocations[method_name](store)

    @pytest.mark.parametrize(("label", "method_name"), _CASE_METHODS)
    async def test_dropping_LAYER2_wrap_store_rejection_moves_every_routed_path(
        self,
        stores: tuple[PrincipalStore, PrincipalKeyStore, KeepStore, SurrealEnv],
        monkeypatch: pytest.MonkeyPatch,
        label: str,
        method_name: str,
    ) -> None:
        _load_wrap_store()  # clean RED if Layer 2 does not exist
        case = _CASES_BY_LABEL[label]
        principal, key, keep, _env = stores
        store = _store_under_test(case, principal, key, keep)
        patched = _patch_everywhere(monkeypatch, _WRAP_STORE, _marker_factory)
        assert patched, f"{_WRAP_STORE} exposed by NO module — the Layer-2 mutation patched nothing"
        _inject_store_error(monkeypatch, case)
        with pytest.raises(_WrapInvokedMarker):
            await case.invocations[method_name](store)


class TestTheMutationProofDiscriminates:
    """CLAUDE.md "a probe needs a control": prove the mutation technique tells a router from a
    private clone, independent of the real build (GREEN now and after). A router looks the
    shared name up on a module at call time; a private clone froze its own wrap. Patching the
    module attr must move the router and NOT the clone — else the mutation pins above could not
    fail a private copy and would be decoration."""

    def test_the_technique_moves_a_router_and_not_a_private_clone(self) -> None:
        import types

        probe_module = types.ModuleType("_engine_rejection_probe_control")

        @contextlib.contextmanager
        def _real_seam(*_a: Any, **_k: Any) -> Iterator[None]:
            try:
                yield
            except Exception as error:  # noqa: BLE001
                raise _DomainStand(str(error)) from error

        setattr(probe_module, _WRAP_STORE, _real_seam)
        sys.modules[probe_module.__name__] = probe_module
        try:

            def router() -> None:
                with getattr(probe_module, _WRAP_STORE)():  # looks up at call time
                    raise SurrealStoreError("boom")

            def private_clone() -> None:
                with _real_seam():  # frozen — never re-reads the shared module
                    raise SurrealStoreError("boom")

            with pytest.raises(_DomainStand):
                router()
            with pytest.raises(_DomainStand):
                private_clone()

            with pytest.MonkeyPatch.context() as monkeypatch:
                monkeypatch.setattr(probe_module, _WRAP_STORE, _marker_factory)
                with pytest.raises(_WrapInvokedMarker):
                    router()
                with pytest.raises(_DomainStand):
                    private_clone()
        finally:
            del sys.modules[probe_module.__name__]


class _DomainStand(RuntimeError):
    """A stand-in domain error for the probe control (models a private wrap's raise)."""


# ===========================================================================
# 4. BEHAVIOUR-PRESERVATION — the old world's virtues survive (the DUAL, both layers)
# ===========================================================================


class TestEngineRejectionWrappingBehaviourIsPreserved:
    """The removed-behavior inventory / DUAL (CLAUDE.md): the rewrite must not lose the wrap's
    virtues. GREEN at HEAD (the local wraps do this) AND after (the two-layer seam does) —
    RED only against a WRONG extraction (a catch-all that masks transport faults, or one that
    stops wrapping). The end-to-end (real surreal classes, all three stores) counterpart to the
    synthetic-class pins in ``lorerunes/tests/test_engine_rejection.py``. These are ALSO the D2
    two-layer mutation observations: the chain/domain pins reflect Layer 1, the passthrough pins
    reflect Layer 2's taxonomy binding."""

    @pytest.mark.parametrize(("label", "method_name"), _CASE_METHODS)
    async def test_a_raw_store_error_surfaces_as_the_domain_error(
        self,
        stores: tuple[PrincipalStore, PrincipalKeyStore, KeepStore, SurrealEnv],
        monkeypatch: pytest.MonkeyPatch,
        label: str,
        method_name: str,
    ) -> None:
        case = _CASES_BY_LABEL[label]
        principal, key, keep, _env = stores
        store = _store_under_test(case, principal, key, keep)
        _inject_store_error(monkeypatch, case)
        with pytest.raises(case.domain_error):
            await case.invocations[method_name](store)

    @pytest.mark.parametrize("transport", ["connection", "contention"])
    @pytest.mark.parametrize(("label", "method_name"), _CASE_METHODS)
    async def test_transport_faults_propagate_untouched(
        self,
        stores: tuple[PrincipalStore, PrincipalKeyStore, KeepStore, SurrealEnv],
        monkeypatch: pytest.MonkeyPatch,
        label: str,
        method_name: str,
        transport: str,
    ) -> None:
        """The discriminator the coverage pin cannot see — REDS against a catch-all wrong
        extraction (one omitting the passthrough-FIRST ordering, since both transient classes
        subclass ``SurrealStoreError``). GREEN at HEAD and after."""
        case = _CASES_BY_LABEL[label]
        principal, key, keep, _env = stores
        store = _store_under_test(case, principal, key, keep)

        expected: type[SurrealStoreError]
        instance: SurrealStoreError
        if transport == "connection":
            expected = SurrealConnectionError
            instance = SurrealConnectionError("injected transport fault")
        else:
            expected = TxnContentionExhaustedError
            instance = TxnContentionExhaustedError(
                "injected exhausted contention", attempts=8, elapsed_seconds=1.0
            )

        async def _raise_transport(*_args: object, **_kwargs: object) -> object:
            raise instance

        monkeypatch.setattr(case.module, "run_query", _raise_transport, raising=False)
        monkeypatch.setattr(case.module, "execute_transaction", _raise_transport, raising=False)
        with pytest.raises(expected):
            await case.invocations[method_name](store)
