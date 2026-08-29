"""The in-process authorization Policy Decision Point (PDP) — packet 61b wave 1.

The single-brain authorization engine (design ``2026-08-22-packet61-pdp-audit-rulings.md``
Forks A/B/C/D/E/G/H + addenda). It answers one question two ways over ONE tree, so the two
answers cannot drift:

* ``authorize_filter(subject, action, table, *, target_scope=None) -> Predicate`` builds a
  closed-algebra predicate whose ``to_surql()`` emits the SurrealQL ``WHERE`` fragment that
  SELECTs exactly the rows ``subject`` may act on (a bulk read/list filter).
* ``authorize(subject, action, resource, *, target_scope=None) -> Decision`` is DEFINED as
  ``authorize_filter(...).matches(resource)`` (Fork A / §5), so the single-row gate and the
  bulk filter are the SAME expression evaluated two ways — ``authorize`` cannot allow a row
  the filter would exclude, by construction.

The residual risk — do the two interpreters MEAN the same thing on the real engine? — is
retired by the live-store oracle (``loremaster/tests/test_pdp_oracle_61b.py``), which
byte-compares the Python ``matches`` verdict against the store's ``SELECT ... WHERE
to_surql()`` verdict on the real 3.2.4 engine.

Charter (F3 / ``lorerunes`` — THE HOME FOR SHARED CODE): this module imports NOTHING but
the stdlib. The value objects are stdlib frozen dataclasses, never pydantic — a third-party
import here would break ``lorerunes``'s importability by every sibling.

The keep-read disjunct is EXPANDED to per-keep equality clauses, never a literal
``scope IN $set`` (finding #413 / ``scripts/probe_read_filter_61b.py`` /
``docs/reference/surrealdb-31-capabilities.md`` §2 — an ``IN`` inside an ``OR`` is a
TableScan trap: green on a virgin/small DB, a whole-table scan on a large dirty store).
"""

from __future__ import annotations

import enum
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# The shared authorization vocabulary the PDP owns (homed here in stdlib-only
# ``lorerunes`` — the ``scopes.py`` precedent — so the PDP and the store schema
# share ONE spelling; D2 re-home). Row-VISIBILITY scopes: distinct from the
# capability scopes (``LORE_READ``/``LORE_WRITE``) in ``scopes.py``.
# --------------------------------------------------------------------------- #

SCOPE_AGENT_PRIVATE = "agent-private"
SCOPE_PRINCIPAL_PRIVATE = "principal-private"
SCOPE_SERVER = "server"

KEEP_SCOPE_PREFIX = "keep:"


def keep_scope(keep_id: str) -> str:
    """The scope value naming a keep (household) — ``keep:<keep_id>``."""
    return f"{KEEP_SCOPE_PREFIX}{keep_id}"


PRINCIPAL_ROLE_MEMBER = "member"
PRINCIPAL_ROLE_ADMIN = "admin"
# The closed ``principal.role`` domain — principal-SPECIFIC (NEVER merged with the free
# ``agent.role`` / rank vocabulary). ``member`` is least-privilege; ``admin`` the explicit
# elevation. Imported by ``loremaster.store.surreal_schema`` so the DDL ASSERT and the PDP
# share one object (D2 — one-column-one-vocabulary).
PRINCIPAL_ROLES = (PRINCIPAL_ROLE_MEMBER, PRINCIPAL_ROLE_ADMIN)

# The append-only audit trail's table name (61a). Homed here so the admin audit carve-out
# (Fork G) and the store schema name the same table (D2).
AUDIT_TABLE = "audit"

# The record tables the governed ``owner_*`` links point at (Fork E — two indexed
# ``record<>`` owner fields). PUBLIC and RE-HOMED here (SEC-R4, the D2 pattern extended):
# ``loremaster.store.surreal_schema`` IMPORTS these so the emitter and the DDL share ONE
# spelling — never a private second copy that could drift.
PRINCIPAL_TABLE = "principal"
AGENT_TABLE = "agent"

_VALID_FIXED_SCOPES = frozenset({SCOPE_AGENT_PRIVATE, SCOPE_PRINCIPAL_PRIVATE, SCOPE_SERVER})


def _is_valid_scope(scope: str) -> bool:
    """A scope is one of the three fixed values or ``keep:<non-empty-id>`` (Fork D rider)."""
    if scope in _VALID_FIXED_SCOPES:
        return True
    return scope.startswith(KEEP_SCOPE_PREFIX) and len(scope) > len(KEEP_SCOPE_PREFIX)


def _param_name(prefix: str, value: str) -> str:
    """A stable, injection-safe bound-param NAME for ``value`` (never the value itself).

    Content-addressed: identical values share one name (so a value used in two disjuncts
    binds once), different values get distinct names, and a hostile value carrying SurrealQL
    can never leak into the fragment — only into ``params`` as a BOUND value (store-ref §2).
    """
    digest = hashlib.blake2s(value.encode("utf-8"), digest_size=8).hexdigest()
    return f"{prefix}_{digest}"


# =========================================================================== #
# Fork C — the action taxonomy (a closed domain of exactly five actions).
# =========================================================================== #


class Action(enum.Enum):
    """The five ruled actions (Fork C — the house closed-domain idiom). READ is never
    audited; the other four are the audited/mutating domain (Fork G)."""

    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"
    SET_SCOPE = "SET_SCOPE"
    SET_OWNER = "SET_OWNER"


# The MUTATING (audited) actions — DERIVED as every action MINUS READ (SEC-F4, reach law:
# a NEW mutating action auto-audits; a hand-list would silently miss it). Matches the shipped
# ``audit`` store's ``_AUDITED_ACTIONS`` domain (61a); the ``==`` cross-check is in the oracle.
_AUDITED_ACTIONS = frozenset(Action) - {Action.READ}


# =========================================================================== #
# Fork D — the value objects (stdlib frozen dataclasses; F3, NOT pydantic).
# =========================================================================== #


@dataclass(frozen=True, slots=True)
class Subject:
    """An authenticated actor: a ``(principal, agent)`` identity, a role, and the keep
    scopes the principal can currently see. Frozen + slots = immutable, no extra attrs;
    ``__post_init__`` validates the role domain. No field defaults (PKT-28 C1 — every call
    CHOOSES, so a build cannot hide behind a fixture monoculture)."""

    principal_id: str
    agent_id: str
    role: str
    visible_keep_ids: frozenset[str]

    def __post_init__(self) -> None:
        if not self.principal_id or not self.agent_id:
            raise ValueError(
                "Subject requires a non-empty principal_id and agent_id — an empty identity "
                "is a confused-deputy forgery vector (SEC-F3, §3.2)"
            )
        if self.role not in PRINCIPAL_ROLES:
            raise ValueError(
                f"role {self.role!r} is not in the principal role domain {PRINCIPAL_ROLES}"
            )


@dataclass(frozen=True, slots=True)
class Resource:
    """A governed row's authorization columns + its ``table`` (reading B2, lead-61
    confirmed). Frozen + slots; ``__post_init__`` validates the scope domain, a non-empty
    table, and (SEC-F2/F3) that each owner is either absent (``None`` — an ``option<>`` NONE
    column) or a non-empty id (never an empty-string forgery). No default for ``scope`` (PKT-28
    C1). An absent owner matches NO owner predicate (``None != any id``), but scope predicates
    still apply — a NONE-owner ``server`` row is readable by all, a NONE-owner private row by
    nobody. ``scope=None`` (FORK 1, packet 63a §10.1) means the ABSENT (unmigrated legacy) scope —
    NOT "any scope": it matches no member ``scope=$x`` disjunct (member-invisible, admin-visible),
    while the empty string stays a forgery that raises."""

    table: str
    owner_principal: str | None
    owner_agent: str | None
    scope: str | None

    def __post_init__(self) -> None:
        if not self.table:
            raise ValueError("Resource.table must be a non-empty table name")
        # SEC-F2/F3: an ABSENT owner (``None``) is legal (an ``option<>`` NONE column — an
        # unowned/legacy row); an EMPTY-STRING owner is a forgery vector and is rejected.
        for field_name, owner in (
            ("owner_principal", self.owner_principal),
            ("owner_agent", self.owner_agent),
        ):
            if owner is not None and not owner:
                raise ValueError(
                    f"Resource.{field_name} when present must be non-empty (SEC-F3) — "
                    "None means absent-owner, an empty string is a forgery vector"
                )
        # FORK 1 (packet 63a, design §10.1): ``scope=None`` is the ABSENT (unmigrated legacy)
        # scope — the ONE new branch. It constructs (a NONE-scope option<> column, §1.4/§2.3),
        # matches NO member ``scope=$x`` disjunct (so a legacy row is member-invisible /
        # admin-visible, fail-closed), and is scope-INDEPENDENT for DELETE (61 D4(a)). The
        # EMPTY-STRING forgery vector and every non-domain string STILL raise (the widening is
        # narrow: only the literal ``None`` is admitted). ``to_surql`` never reads a ``Resource``,
        # so the emitted SurrealQL is byte-identical — 63 adds nothing to the predicate.
        if self.scope is not None and not _is_valid_scope(self.scope):
            raise ValueError(
                f"scope {self.scope!r} is not one of {sorted(_VALID_FIXED_SCOPES)} "
                f"or {KEEP_SCOPE_PREFIX}<non-empty-id> (None = the absent/legacy scope, §10.1)"
            )


@dataclass(frozen=True, slots=True)
class Decision:
    """The single-row verdict: ``allowed`` and whether the action must be AUDITED (Fork G —
    fires iff an admin exercised a load-bearing bypass a member could not)."""

    allowed: bool
    requires_audit: bool


# =========================================================================== #
# Fork A — the closed predicate IR: ONE tree, TWO total interpreters.
# =========================================================================== #


class Predicate(ABC):
    """A node in the closed authorization-predicate algebra. Both interpreters are ABSTRACT,
    so a subclass implementing only one CANNOT be instantiated — the coverage guarantee is
    structural, not disciplinary (Fork A: no silent ``else: return True`` fall-through)."""

    @abstractmethod
    def to_surql(self) -> tuple[str, dict[str, str]]:
        """Emit ``(where_fragment, bound_params)`` — every value a BOUND param, never
        interpolated into the fragment (store-ref §2, injection-safe)."""

    @abstractmethod
    def matches(self, resource: Resource) -> bool:
        """Evaluate this predicate against a single ``Resource`` in Python."""


@dataclass(frozen=True)
class ScopeEq(Predicate):
    """``scope = <scope>``."""

    scope: str

    def to_surql(self) -> tuple[str, dict[str, str]]:
        name = _param_name("s", self.scope)
        return f"scope = ${name}", {name: self.scope}

    def matches(self, resource: Resource) -> bool:
        return resource.scope == self.scope


@dataclass(frozen=True)
class OwnerPrincipalEq(Predicate):
    """``owner_principal = principal:<principal_id>`` (record link, bare-string param)."""

    principal_id: str

    def to_surql(self) -> tuple[str, dict[str, str]]:
        name = _param_name("p", self.principal_id)
        return (
            f"owner_principal = type::record('{PRINCIPAL_TABLE}', ${name})",
            {name: self.principal_id},
        )

    def matches(self, resource: Resource) -> bool:
        return resource.owner_principal == self.principal_id


@dataclass(frozen=True)
class OwnerAgentEq(Predicate):
    """``owner_agent = agent:<agent_id>`` (record link, bare-string param)."""

    agent_id: str

    def to_surql(self) -> tuple[str, dict[str, str]]:
        name = _param_name("a", self.agent_id)
        return (
            f"owner_agent = type::record('{AGENT_TABLE}', ${name})",
            {name: self.agent_id},
        )

    def matches(self, resource: Resource) -> bool:
        return resource.owner_agent == self.agent_id


@dataclass(frozen=True)
class ScopeInKeeps(Predicate):
    """Membership in a keep set, EMITTED as per-keep equality disjuncts — never a literal
    ``scope IN $set`` (finding #413 / store-ref §2: ``IN`` inside an ``OR`` TableScans). The
    disjuncts are WRAPPED IN PARENS so the fragment is SELF-CONTAINED (#416): an
    unparenthesised OR would ESCAPE an enclosing ``And`` (SurrealQL binds AND tighter than OR:
    ``owner=$p AND scope=$k0 OR scope=$k1`` parses as ``(owner=$p AND scope=$k0) OR scope=$k1``,
    leaking other principals' rows). The parenthesised form still IndexScans as a top-level
    READ disjunct (SurrealDB flattens ``A OR (B OR C)`` — re-probed, no #413 regression). An
    empty keep set contributes nothing (``false``)."""

    keeps: frozenset[str]

    def to_surql(self) -> tuple[str, dict[str, str]]:
        if not self.keeps:
            return "false", {}
        clauses: list[str] = []
        params: dict[str, str] = {}
        for keep in sorted(self.keeps):
            name = _param_name("k", keep)
            clauses.append(f"scope = ${name}")
            params[name] = keep
        return "(" + " OR ".join(clauses) + ")", params

    def matches(self, resource: Resource) -> bool:
        return resource.scope in self.keeps


@dataclass(frozen=True)
class And(Predicate):
    """Conjunction of child predicates."""

    children: tuple[Predicate, ...]

    def to_surql(self) -> tuple[str, dict[str, str]]:
        fragments, params = _emit_children(self.children)
        return "(" + " AND ".join(fragments) + ")", params

    def matches(self, resource: Resource) -> bool:
        return all(child.matches(resource) for child in self.children)


@dataclass(frozen=True)
class Or(Predicate):
    """Disjunction of child predicates."""

    children: tuple[Predicate, ...]

    def to_surql(self) -> tuple[str, dict[str, str]]:
        fragments, params = _emit_children(self.children)
        return "(" + " OR ".join(fragments) + ")", params

    def matches(self, resource: Resource) -> bool:
        return any(child.matches(resource) for child in self.children)


@dataclass(frozen=True)
class AllRows(Predicate):
    """Selects every row (``WHERE true``) — the admin superuser short-circuit."""

    def to_surql(self) -> tuple[str, dict[str, str]]:
        return "true", {}

    def matches(self, resource: Resource) -> bool:
        return True


@dataclass(frozen=True)
class NoRows(Predicate):
    """Selects no row (``WHERE false``) — a denial expressed as a NODE inside the one
    expression (the audit carve-out, a non-grantable SET_SCOPE, a member SET_OWNER), so the
    §5 equivalence still holds rather than a bypass beside the tree."""

    def to_surql(self) -> tuple[str, dict[str, str]]:
        return "false", {}

    def matches(self, resource: Resource) -> bool:
        return False


def _emit_children(children: tuple[Predicate, ...]) -> tuple[list[str], dict[str, str]]:
    """Emit each child once and merge the bound params (identical names carry identical
    values, so a value shared across disjuncts binds exactly once)."""
    fragments: list[str] = []
    params: dict[str, str] = {}
    for child in children:
        fragment, child_params = child.to_surql()
        fragments.append(fragment)
        params.update(child_params)
    return fragments, params


# =========================================================================== #
# Fork C — the member predicates (identity-driven; role-independent).
# =========================================================================== #


def _grantable(subject: Subject, target_scope: str | None) -> bool:
    """Whether ``subject`` may GRANT ``target_scope`` on a SET_SCOPE (D4(b) / §3.2.3): the
    private scopes + server always; a keep scope ONLY if the subject is a member of it. A
    ``None`` target grants nothing (SET_SCOPE with no named target denies)."""
    if target_scope is None:
        return False
    if target_scope in _VALID_FIXED_SCOPES:
        return True
    return target_scope in subject.visible_keep_ids


def _member_filter(
    subject: Subject, action: Action, table: str, target_scope: str | None
) -> Predicate:
    """The predicate a MEMBER of ``subject``'s identity gets for ``action`` (Fork C / §4).

    Role-INDEPENDENT: this is the member policy, used both as the member branch of
    ``authorize_filter`` AND (unchanged, single-brain) to decide whether an admin's action
    was a load-bearing bypass in ``requires_audit`` (ROUTING-IS-NOT-SHARING — the SAME
    predicate, never a cloned/simplified copy).
    """
    principal = OwnerPrincipalEq(subject.principal_id)
    agent = OwnerAgentEq(subject.agent_id)
    keeps = ScopeInKeeps(subject.visible_keep_ids)

    if action is Action.READ:
        # own agent-private; own-principal principal-private (any sibling agent reads it);
        # all server; keep rows whose household the subject is in.
        return Or(
            (
                And((ScopeEq(SCOPE_AGENT_PRIVATE), principal, agent)),
                And((ScopeEq(SCOPE_PRINCIPAL_PRIVATE), principal)),
                ScopeEq(SCOPE_SERVER),
                keeps,
            )
        )
    if action is Action.WRITE:
        # EXACT (principal, agent) owner of a private/server row (reading 1); any household
        # member of a keep row.
        return Or(
            (
                And((ScopeEq(SCOPE_AGENT_PRIVATE), principal, agent)),
                And((ScopeEq(SCOPE_PRINCIPAL_PRIVATE), principal, agent)),
                And((ScopeEq(SCOPE_SERVER), principal, agent)),
                keeps,
            )
        )
    if action is Action.DELETE:
        # the row's OWNER only (exact stamp), ANY scope — D4(a): scope-INDEPENDENT so an
        # owner can clean up a keep row of a keep they have left (no un-deletable orphans).
        return And((principal, agent))
    if action is Action.SET_SCOPE:
        # owner only AND the TARGET scope is grantable by the subject (D4(b)).
        if _grantable(subject, target_scope):
            return And((principal, agent))
        return NoRows()
    # Action.SET_OWNER — admin-only for everyone; a member never gives away a row (§4.3).
    return NoRows()


# =========================================================================== #
# Fork A/G — the two entry points.
# =========================================================================== #


def authorize_filter(
    subject: Subject, action: Action, table: str, *, target_scope: str | None = None
) -> Predicate:
    """The row-visibility predicate for ``subject`` performing ``action`` on ``table``.

    Admin is a full superuser (§4.2) → ``AllRows``, EXCEPT the audit carve-out (Fork G / §9):
    admin canNOT mutate the audit trail, so a mutating action on ``AUDIT_TABLE`` is
    ``NoRows`` (a node inside the one expression, not a bypass beside it). A member gets the
    identity-driven Fork-C predicate.
    """
    if subject.role == PRINCIPAL_ROLE_ADMIN:
        if table == AUDIT_TABLE and action in _AUDITED_ACTIONS:
            return NoRows()
        return AllRows()
    return _member_filter(subject, action, table, target_scope)


def authorize(
    subject: Subject, action: Action, resource: Resource, *, target_scope: str | None = None
) -> Decision:
    """The single-row gate: ``authorize_filter(...).matches(resource)`` (Fork A / §5), so the
    gate and the bulk filter are ONE expression (no split brain).

    ``requires_audit`` fires iff the action was ALLOWED, the subject is an admin, the action
    is mutating, AND a member of the same identity could NOT have done it — i.e. the admin
    exercised a load-bearing superuser bypass (Fork G / §9). It reuses the SAME
    ``_member_filter`` (single-brain — a cloned member check that dropped grantability would
    under-audit a non-grantable SET_SCOPE).
    """
    predicate = authorize_filter(subject, action, resource.table, target_scope=target_scope)
    allowed = predicate.matches(resource)
    requires_audit = (
        allowed
        and subject.role == PRINCIPAL_ROLE_ADMIN
        and action in _AUDITED_ACTIONS
        and not _member_filter(subject, action, resource.table, target_scope).matches(resource)
    )
    return Decision(allowed=allowed, requires_audit=requires_audit)
