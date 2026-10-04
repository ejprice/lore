"""The shared GOVERNED SUBSTRATE (packet 63a; extended through 63c) — built, not a stub.

This is the ONE-IMPLEMENTATION address the design mandates
(``docs/design/2026-08-28-packet63-retrofit-rulings.md`` §1.1–§1.2):

- the Subject resolution: :func:`resolve_principal`, :func:`resolve_subject`, :func:`resolve_write_scope`;
- the read splice: :func:`read_filter`;
- the guarded write: :func:`authorize_guarded` → :func:`guarded_write`, with :func:`write_guard` /
  :class:`governed_exempt` attributing every governed write;
- the migration result models: :class:`MigratePreconditionCounts`, :class:`MigrateGovernedResult`;
- the forgotten-backfill count: :func:`report_unmigrated_governed_rows`;
- the GOVERNED SET (am-37 §13.4 / §13.4.1 / §13.4.2): :func:`governed_node_tables_of` (the ONE property —
  a table is governed iff its DDL defines the whole governed triple), :func:`ddl_governed_tables` (that
  property over the package's own DDL generators), :data:`PENDING_GOVERNED_TABLES` (the declared,
  self-destructing governed-by-intent set) and :func:`governed_tables` (their union — the REPORT domain);
  ``scripts/restore_prod_dump.py`` CONSUMES these (``scripts`` → ``loremaster`` only, never the reverse);
- the ONE ``--table`` validator: :func:`validate_governed_table`;
- the THREE fail-closed store-answer shape readers: :func:`group_all_count`, :func:`rows_of`,
  :func:`map_of` (packet 63c amendment 37 §13 B / §13.1 — no other function here or in
  ``principals.py`` tests a store answer's shape).

The memory retrofit (63a), comms (63b/63c) and tasks/findings (64) CALL these functions — never
patterns they clone (CLAUDE.md "ONE IMPLEMENTATION"). Store access routes through an injected
:class:`~loremaster.store._txn.StoreHandle` and ``run_query`` (R4: no raw connection, no direct SDK
call). It lives in ``loremaster`` (store-reading orchestration — the ESC-1 split: ``lorerunes``
holds predicates, ``loremaster`` holds entry points).
"""

from __future__ import annotations

import contextlib
import contextvars
import functools
import inspect
import logging
import re
import sys
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from loremaster.sanitise import sanitise_line
from loremaster.store import surreal_schema
from loremaster.store._txn import (
    SurrealStoreError,
    TxnFragment,
    TxnGovernedConflictError,
    compose,
    execute_read_transaction,
    run_query,
)
from lorerunes import pdp

if TYPE_CHECKING:  # pragma: no cover - typing only
    from lorerunes.pdp import Action, Subject

    from loremaster.store._txn import StoreHandle

logger = logging.getLogger(__name__)

# The deterministic natural key of the canonical PROJECT keep (design §2.2 — ``project:<slug>``).
# The ONE-IMPLEMENTATION home for this policy string: the memory backend's default-scope
# resolution (``LocalMemoryBackend._default_project_scope``) and the migration mint
# (``principals.migrate_governed``) BOTH address the project keep by THIS key, so they must agree —
# a second copy is where the fill-later pattern silently diverges.
# ⚠ 63a BOUND (slug hardcoded): the dogfooding fleet's ``lore.yaml`` slug is ``lore``, and neither
# the backend nor the migration verb is wired to the config slug at 63a, so the key is the literal
# ``project:lore``. Re-open trigger: the first lore deployment whose project slug is NOT ``lore`` —
# at which point the slug must be threaded from ``LoreConfig.project.slug`` into both sites.
PROJECT_KEEP_KEY = "project:lore"


class GovernedDenied(Exception):
    """A governed access was DENIED (fail-closed). Carries a TEACHING message naming the
    missing step (design §1.2 item 1: an absent/unverified capability, an unknown principal, or
    a keep-resolution failure → this, never an empty/partial Subject and never a silent empty
    result). The removed-behavior-1 identity-less DENY is this error."""


class GovernedConflict(Exception):
    """A guarded WRITE/DELETE matched ZERO rows — a concurrent scope/owner change landed between
    the substrate's read and its guarded mutation (design §1.2 item 3). LOUD, never a silent
    no-op: there is no read-then-write TOCTOU window on the governed columns."""


class GovernedAuditUnavailable(Exception):
    """An AUDITED governed write was required (``requires_audit`` fired — an admin BYPASS a member
    could not make) but NO :class:`~loremaster.audit.AuditStore` was supplied (``audit is None``),
    so the write would run UNAUDITED. REFUSED, never run: a mutation without its audit row is the
    §9 "compromised admin erases its trail" shape from the other side (design §10.6 rider ii),
    exactly the fail-OPEN a silent skip creates. This is a PROGRAMMING/CONFIG error — the subject
    IS authorized; the trail is what is missing — so it is a DISTINCT type from :class:`GovernedDenied`
    (a per-caller authorization refusal) and :class:`GovernedConflict` (a vanished row). Any consumer
    whose path can reach an admin bypass MUST wire a real audit sink.

    RES-2 (`docs/plans/v2/receipts/…/REPORT-cold-audit-63a.md` §RES). Raised by
    :func:`authorize_guarded` — the authorization leg of :func:`guarded_write` — BEFORE any durable
    effect, whenever the PDP decision ``requires_audit`` and no ``audit`` sink was supplied; the guarded
    mutation is never composed. (Before 63a-iii the write path silently skipped the audit and proceeded —
    the fail-open this type closes.)"""


@dataclass(frozen=True)
class GuardedWriteResult:
    """The outcome of :func:`guarded_write` (design §1.2 item 3). ``row_count`` is the guarded
    statement's returned-row count (0 ⇒ ``GovernedConflict`` was raised, never returned)."""

    row_count: int
    audited: bool


#: The closed domain of :attr:`MigratePreconditionCounts.owner_classification` (amendments 30 / 34 §2): who
#: owns the owned-but-unscoped agent rows — ``"empty"`` when the agent read ran and found none.
OwnerClassification = Literal["operator", "foreign", "mixed", "unclassified", "empty"]


class MigratePreconditionCounts(BaseModel):
    """The governed-migration precondition counts a run MEASURED (packet 63c-i-a, amendments 30–36).

    ``None`` = not measured on this run; a number = measured. Each field's ``json_schema_extra["read"]`` names
    the store read that measures it (``agent`` / ``message`` / ``operator``). A refusal's ``reason`` restates
    these counts, DERIVED from these fields. The owner triple (``owned_but_unscoped_agents``,
    ``distinct_owner_principals``, ``owner_classification``) is consistent by construction (amendment 34 §2).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    unscoped_agents: int | None = Field(default=None, json_schema_extra={"read": "agent"})
    owned_but_unscoped_agents: int | None = Field(default=None, json_schema_extra={"read": "agent"})
    scoped_but_ownerless_agents: int | None = Field(default=None, json_schema_extra={"read": "agent"})
    dangling_sender_messages: int | None = Field(default=None, json_schema_extra={"read": "message"})
    owned_but_unscoped_messages: int | None = Field(default=None, json_schema_extra={"read": "message"})
    scoped_but_ownerless_messages: int | None = Field(default=None, json_schema_extra={"read": "message"})
    distinct_owner_principals: int | None = Field(default=None, json_schema_extra={"read": "agent"})
    owner_classification: OwnerClassification | None = Field(
        default=None, json_schema_extra={"read": "agent"}
    )
    total_principals: int | None = Field(default=None, json_schema_extra={"read": "operator"})
    admin_principals: int | None = Field(default=None, json_schema_extra={"read": "operator"})

    @model_validator(mode="after")
    def _one_meaning_per_state(self) -> MigratePreconditionCounts:
        """amendment 34 §2: the owner triple is consistent by construction — all three unmeasured together;
        ``"empty"`` iff zero owned rows and zero owners; any other classification iff both are positive. A
        contradiction raises (a pydantic ``ValidationError``)."""
        owned, distinct, classification = (
            self.owned_but_unscoped_agents, self.distinct_owner_principals, self.owner_classification
        )
        if classification is None or owned is None or distinct is None:
            legal = classification is None and owned is None and distinct is None
        elif classification == "empty":
            legal = owned == 0 and distinct == 0
        else:
            legal = owned > 0 and distinct > 0
        if not legal:
            raise ValueError(f"contradictory owner triple: {owned=} {distinct=} {classification=}")
        return self


@dataclass(frozen=True)
class MigrateGovernedResult:
    """Receipts of a ``lore-adm migrate-governed`` run over ONE table (design §1.2 item 5 /
    §2.1) — receipts-printing: rows scanned / backfilled / already-migrated, and a LOUD
    ``refused`` (with ``reason``) on a precondition failure (the agent-first ORDER, or a
    multi-principal ``agent`` table). The migration is a one-shot cutover verb that always
    EXECUTES (the dry-run/--execute paradigm was struck 2026-08-20 — §10.7-W); the counts ARE
    the receipt. The read-only PREVIEW is the separate ``report-unmigrated`` verb.

    ``scanned`` / ``already_migrated`` are ``None`` on EVERY refusal (packet 63c-i-a, amendment 22
    §4 / amendment 24 FK-a / amendment 28 A4): they are the LEG's own counts of the target table, and every
    refusal returns before the leg counts it, so those two were NOT MEASURED — a ``0`` there would be a
    served count describing no set. The precondition reads a refusal DID run (``INFO FOR DB``, the agent
    facts, the message facts — which can read the target table itself) ride ``preconditions``, restated
    DERIVED in ``reason``. ``backfilled``
    stays an ``int``: a refusal stamped nothing, which IS measured (``0``). On a proceeding run
    ``backfilled`` is the number of rows the backfill actually stamped (the UPDATE's own return).

    ``table_defined`` (amendment 34 F-5 / amendment 36 FK-4 / amendment 37 §6 M-2): the MEASURED answer to
    "is the ``--table`` target defined in this store?", DERIVED once, by :func:`migrate_governed`, from the
    precondition read — ``table in defined_tables`` whenever ``INFO FOR DB`` ran (on EVERY result after that
    read: a proceeding leg, a leg's own refusal, the verb-level refusal, the undefined-table answer, the
    ``brief`` not-yet-supported refusal), and ``None`` iff it did not run (the zero-I/O invalid-table
    refusal). It has NO default: every construction states it (CLAUDE.md — never default a value the code
    branches on). ``False`` is the "nothing to migrate" answer (``scanned=0``, before any leg read).

    ``messages_left_unmigrated`` (amendment 37 §6 F-10, renamed §13 C F-4 — the input-fate law: every input
    is emitted, reported, or rejected-and-reported): the ``message`` rows still ``scope IS NONE AND
    owner_principal IS NONE`` AFTER the message leg's backfill UPDATE, MEASURED by one separate count read
    (``0`` when it ran and none remain). It is a SUPERSET of "unsound sender": commonly the row's sender has
    no owner or no scope (re-run after ``--table agent`` for those), but a row inserted during the run is
    counted here too. ``None`` iff that measurement did not run — every other leg, every
    refusal, and the undefined-table answer. Every production construction states it explicitly; the
    ``None`` default exists ONLY because a closed contract pin constructs this result without the field
    (``test_fixwave_a28c_63c_i_a.py``'s am-34 §4 CLI-render forgery) — and ``None`` there is the honest
    "not measured"."""

    table: str
    scanned: int | None
    backfilled: int
    already_migrated: int | None
    refused: bool
    reason: str | None = None
    preconditions: MigratePreconditionCounts | None = None
    table_defined: bool | None = field(kw_only=True)
    messages_left_unmigrated: int | None = field(default=None, kw_only=True)


@dataclass(frozen=True)
class LegacyMapping:
    """A per-table backfill mapping for ``lore-adm migrate-governed`` (design §2.1). ONE verb,
    N table rows: the disposition names how a legacy row's ``(owner_principal, owner_agent,
    scope)`` is derived — UNOWNED-LEGACY (memory/brief: NONE/NONE), OWNED-BY-THE-OPERATOR (agent:
    the ONE operator principal / the row's own id — packet 63c-i-a, ruling §6), OWNED-BY-LINK
    (message: sender / sender.owner_principal), STRING-UNRESOLVABLE (64: a bare name is never
    promoted).
    The scope is always the canonical project keep. The shapes are the contract; the builder
    fills the SurrealQL."""

    table: str
    disposition: str


async def resolve_principal(access_token: Any, *, principal_store: Any) -> Any:
    """Resolve the transport token's ADMITTED principal, or ``None`` (packet 63b-ii-a, ruling §3.1).

    The token→admitted-principal derivation LIFTED out of :func:`resolve_subject` step (2) so BOTH
    the send-owner (Q1, via ``resolve_subject``) and the keep-keeper (Q2, via
    ``AppContext._comms_register``) share ONE derivation — the SAME admitted principal iff the same
    token (ruling §3.3; #102 ONE IMPLEMENTATION, proven by mutation). Three legs:

    * the token is ABSENT **or** carries no ``subject`` (``if not email`` — falsiness, so ``""`` and
      ``None`` both take this leg) → return ``None`` at the SEAM, WITHOUT consulting the store (no
      email to look up — the None-decision is not a downstream lookup; adversary3 §D-NULLTOKEN);
    * a ``subject`` IS presented but ``principal_store.get_by_email`` admits none → raise
      :class:`GovernedDenied` (a presented-but-unadmitted principal is a DENY, NEVER degraded to
      ``None``/"ownerless");
    * an admitted principal → return it.

    The ``None`` policy differs per caller and is decided AT the call site: ``resolve_subject``
    turns ``None`` into a ``GovernedDenied`` (a governed identity requires a principal), while
    ``_comms_register`` turns it into reading α (an ownerless register, ruling §3.2).
    """
    email = getattr(access_token, "subject", None)
    if not email:
        return None
    principal = await principal_store.get_by_email(email)
    if principal is None:
        raise GovernedDenied(
            f"no principal is admitted for {email!r} — the transport token names an unknown "
            "principal; a governed identity requires an admitted principal"
        )
    return principal


def resolve_write_scope(subject: Subject, scope: str | None, *, default: str) -> str:
    """Resolve a governed WRITE's scope through the ONE shared grant predicate (ruling §4.A / §6).

    LIFTED out of ``LocalMemoryBackend._resolve_write_scope`` so ``remember`` (memory) and ``send``
    (comms) share ONE grant rule, not a pattern each clones (ROUTING-IS-NOT-SHARING; proven by
    mutation — perturb this seam and every caller's grant behaviour flips). PURE: the caller
    resolves the ``default`` and passes it in (``send`` passes the session-keep scope EXPLICITLY, so
    ``_grantable`` runs on every send; ``remember`` passes the canonical project scope only on the
    None leg). An OMITTED scope (``None``) returns ``default``; an EXPLICIT scope is checked by the
    SAME ``lorerunes.pdp._grantable`` predicate the SET_SCOPE action uses (the fixed scopes + the
    caller's OWN keeps are grantable) — a keep the caller is NOT householded in DENIES with a
    teaching :class:`GovernedDenied`, never a silent fallback to ``default``.
    """
    if scope is None:
        return default
    if not pdp._grantable(subject, scope):  # noqa: SLF001 - the ruled shared grant predicate
        raise GovernedDenied(
            f"scope {scope!r} is not grantable by {subject.principal_id}/{subject.agent_id} — "
            "you are not householded in that keep; run `lore-adm add-household` to join it first"
        )
    return scope


async def resolve_subject(
    access_token: Any,
    capability: Any,
    *,
    registry: Any,
    principal_store: Any,
    keep_store: Any,
) -> Subject:
    """THE one place a :class:`lorerunes.pdp.Subject` is constructed from a live call (design
    §1.2 item 1; R-a.2 — an AST pin allowlists this as the ONLY production ``Subject(`` site).

    ``principal_id`` + ``role`` from the token's principal (``PrincipalStore.get_by_email`` on
    ``access_token.subject``); the agent via ``stamp_owner`` (62's seam, ONE read after #425);
    ``visible_keep_ids`` via ``resolve_visible_keeps`` (61b). FAIL-CLOSED: an absent/unverified
    capability, an unknown principal, or a ``KeepStoreError`` → :class:`GovernedDenied` naming
    the missing step — never an empty or partial Subject.
    """
    from loremaster.keeps import KeepStoreError
    from loremaster.owner_stamp import OwnerStampError, stamp_owner
    from loremaster.visible_keeps import resolve_visible_keeps

    # (1) verify the capability + derive the owner agent in ONE round-trip (#425). An absent /
    # garbage / unverified / binding-mismatched capability fails closed (OwnerStampError) — DENY.
    try:
        _owner_principal, owner_agent = await stamp_owner(access_token, capability, registry=registry)
    except OwnerStampError as error:
        raise GovernedDenied(
            "the presented capability did not verify — register an owned agent first "
            "(`lore_comms action=register`) so a governed call carries a verifiable identity"
        ) from error

    # (2) the transport token's principal, resolved through the ONE lifted seam ``resolve_principal``
    # (ruling §3.1 / §3.3 — Q1 send-owner and Q2 keep-keeper share this derivation). A None result
    # (token absent / carries no subject) DENIES here — a Subject is NEVER constructed with a
    # guessed/empty principal (SEC-F3); a presented-but-unadmitted principal already raised inside.
    principal = await resolve_principal(access_token, principal_store=principal_store)
    if principal is None:
        raise GovernedDenied(
            "the transport token carries no principal subject — a governed identity requires an "
            "admitted principal (the token_verifier sets subject = principal.email)"
        )
    email = principal.email

    # (3) the keeps the principal can currently see. A resolver failure (a wrong-instance / dead
    # keep store) fails CLOSED — never a Subject built with a SHORTER keep set (which would
    # mis-authorize), and never a swallowed error.
    try:
        visible_keep_ids = await resolve_visible_keeps(keep_store, member_email=email)
    except KeepStoreError as error:
        raise GovernedDenied(
            "could not resolve the caller's visible keeps (the keep store is unreachable / a "
            "wrong instance) — failing closed rather than authorizing against a partial keep set"
        ) from error

    # THE one production Subject constructor (R-a.2 — an AST pin allowlists this single site).
    return pdp.Subject(
        principal_id=_bare(principal.id),
        agent_id=owner_agent,
        role=principal.role,
        visible_keep_ids=frozenset(visible_keep_ids),
    )


def read_filter(subject: Subject, table: str) -> tuple[str, dict[str, Any]]:
    """THE one read splice (design §1.2 item 2; R-a.3 — mutation-proven the single splice).

    A thin wrapper over ``authorize_filter(subject, Action.READ, table).to_surql()``: returns the
    self-contained fragment (61 #416 — parenthesised) + its content-addressed params, so every
    governed LIST read splices ``AND ({fragment})`` with MERGED params. The wrapper exists so the
    splice is ONE function, not a pattern each caller clones.
    """
    # THE one splice (R-a.3): byte-identical to authorize_filter(READ).to_surql(), so a hand-rolled
    # divergent fragment reddens the delegation pin, and a mutation of ``to_surql`` moves EVERY
    # governed list-read's oracle (a read that stays green under that mutation is a private copy).
    return pdp.authorize_filter(subject, pdp.Action.READ, table).to_surql()


# --------------------------------------------------------------------------- #
# F5 GUARDED-WRITE ATTRIBUTION (design §10.9-A layer 2) — the runtime guard-context.
#
# The enforcement-completeness instrument attributes every governed-table mutation to the FRAME that
# issued it. ``write_guard(label)`` is a stdlib-``contextvars`` context manager each allowlisted frame
# (and ``guarded_write``) enters around its store mutation; ``active_write_guard()`` reads the
# innermost active label. The F5 runtime seam (``_governed_contract.observe_governed_table_writes``)
# samples that label at each store seam, so a memory mutation running with label=None is UNCLASSIFIED
# (deny-by-default, L2b). ``contextvars`` is the exact primitive — task-local, async-safe (the label
# stays set across the ``await`` inside the ``with``), auto-reset — so no bespoke stack is hand-rolled.
# --------------------------------------------------------------------------- #

_ACTIVE_WRITE_GUARD: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "loremaster_active_write_guard", default=None
)


def active_write_guard() -> str | None:
    """The label of the innermost active :func:`write_guard`, or ``None`` outside every guard
    (design §10.9-A L2b — a mutation observed with ``None`` here is UNATTRIBUTED)."""
    return _ACTIVE_WRITE_GUARD.get()


@contextlib.contextmanager
def write_guard(label: str) -> Iterator[None]:
    """Attribute every governed-table mutation executed within the block to ``label`` (design
    §10.9-A layer 2). The label is task-local (``contextvars``), so it stays set across the ``await``
    that runs the store mutation and is reset on exit even if the mutation raises. Each allowlisted
    memory-write frame and :func:`guarded_write` enters this around its store seam so a runtime
    mutation is always attributable at the F5 seam (``ROUTING-IS-NOT-SHARING`` at runtime)."""
    token = _ACTIVE_WRITE_GUARD.set(label)
    try:
        yield
    finally:
        _ACTIVE_WRITE_GUARD.reset(token)


# --------------------------------------------------------------------------- #
# F5 EXEMPT ATTRIBUTION (design §1.4 / §1.9 item 3c/5, packet 63b-i-a — SUPERSEDES the 63a-v
# CORRECTION step 4 bare-name shape) — the admin-channel counterpart to :func:`write_guard`.
#
# A NON-member-reachable governed-table write (the ``lore-adm migrate-governed`` backfill in
# ``principals._migrate_memory_scope``) is NOT a per-caller guarded write, so it does not enter
# :func:`write_guard`. Instead it enters :func:`governed_exempt` with the NAMED admin token whose
# allowlist entry evidences the exemption (``migrate-governed``). 63b-i-a makes the exemption
# STATEMENT-SCOPED and ORIGIN-BEARING: ``governed_exempt(name, *, statement)`` is a CLASS context
# manager whose ``__enter__`` captures ``sys._getframe(1)`` — the frame executing the ``with``,
# exactly one up, with NO ``contextlib`` frame in between (so there is NO filename skip-list, the
# relocated-constant antipattern §1.9 item 3c removes) — as the token's ``origin`` ``(repo-relative
# file, co_name)``. WHY origin lives in the TOKEN and not in a call-time stack walk (§1.9 item 3c,
# measured GOTCHA-C): at SDK-call time the immediate production caller is ALWAYS the ``store._txn``
# driver, so leg-4's origin cannot come from the call-time stack; it must be captured where the
# business frame IS the immediate caller — context entry. The F5 runtime seam
# (``_governed_contract.observe_governed_table_writes``) samples :func:`active_exempt` and the
# classifier's leg 4 matches ``token.origin == (entry.site.file, entry.site.function)``; a helper
# borrowing the token on another frame's behalf yields a foreign origin → leg 4 RED. This stays a
# verbatim ``contextvars`` mirror of the ``write_guard`` idiom (task-local, async-safe-across-
# ``await``, auto-reset-on-exit); ``write_guard`` NEVER consults origin (the label leg has none).
# --------------------------------------------------------------------------- #

#: The workspace repo root — ``loremaster/loremaster/governed.py`` → ``parents[2]`` — the ONE place
#: the origin capture derives a repo-relative posix path from (the SAME key shape the F5 allowlist's
#: ``TreeMutationSite.file`` carries), never a hand-list.
_GOVERNED_REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ExemptToken:
    """The token an active :func:`governed_exempt` block installs in ``_ACTIVE_EXEMPT`` (design §1.9
    item 3c). Frozen: the channel ``name`` + the GOLDEN ``statement`` the exemption scopes to + the
    ``origin`` ``(repo-relative file, co_name)`` of the frame that ENTERED the ``with`` block.
    :func:`active_exempt` returns THIS or ``None``. The F5 classifier reads it BY ATTRIBUTE
    (``.name`` / ``.statement`` / ``.origin``), so a structurally-identical test-side twin flows
    through the SAME classifier — the field names are the contract."""

    name: str
    statement: str
    origin: tuple[str, str]  # (repo-relative file, co_name) of the frame that ENTERED the block


_ACTIVE_EXEMPT: contextvars.ContextVar[ExemptToken | None] = contextvars.ContextVar(
    "loremaster_active_exempt", default=None
)


def active_exempt() -> ExemptToken | None:
    """The :class:`ExemptToken` of the innermost active :func:`governed_exempt`, or ``None`` outside
    every exempt block (design §1.9 item 3c — the admin-attribution channel the F5 runtime seam
    samples; the classifier's four-leg exemption reads name ∧ golden statement ∧ effect ∧ origin)."""
    return _ACTIVE_EXEMPT.get()


def _exempt_repo_relative(filename: str) -> str:
    """A frame's ``co_filename`` as a repo-relative posix path (the ``TreeMutationSite.file`` shape),
    or the resolved absolute posix path when it lives outside the workspace (a synthetic/exec frame)."""
    resolved = Path(filename).resolve()
    try:
        return resolved.relative_to(_GOVERNED_REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


class governed_exempt:
    """Attribute every governed-table mutation executed within the block to the NAMED,
    STATEMENT-SCOPED admin exemption ``name`` (design §1.4 / §1.9 item 3c) — the exempt-channel
    counterpart to :func:`write_guard` for a governed write that is NOT member-reachable (so cannot
    ride a per-caller ``write_guard``) but IS evidenced by an allowlist entry (``migrate-governed``).

    A CLASS context manager (NOT ``@contextlib.contextmanager``) precisely so ``__enter__`` can
    capture ``sys._getframe(1)`` — the frame executing the ``with`` statement, exactly one up, with
    NO ``contextlib`` generator frame in between (§1.9 item 3c: the class form removes the filename
    skip-list). The installed :class:`ExemptToken` carries ``name`` + the GOLDEN ``statement`` + that
    frame's ``(repo-relative file, co_name)`` origin; the token is task-local (``contextvars``), so
    it stays set across the ``await`` that runs the store mutation and is reset on exit even if the
    mutation raises. A helper entering this on another frame's behalf yields a FOREIGN origin, so the
    F5 classifier's leg-4 origin match rejects a borrowed token."""

    def __init__(self, name: str, *, statement: str) -> None:
        self._name = name
        self._statement = statement
        self._reset: contextvars.Token[ExemptToken | None] | None = None

    def __enter__(self) -> ExemptToken:
        frame = sys._getframe(1)  # the frame executing the `with`, exactly one up (no contextlib frame)
        origin = (_exempt_repo_relative(frame.f_code.co_filename), frame.f_code.co_name)
        token = ExemptToken(self._name, self._statement, origin)
        self._reset = _ACTIVE_EXEMPT.set(token)
        return token

    def __exit__(self, *_exc: object) -> None:
        if self._reset is not None:
            _ACTIVE_EXEMPT.reset(self._reset)


@dataclass(frozen=True)
class GuardedPlan:
    """The frozen output of :func:`authorize_guarded` — the Python authorization leg, NO effect
    (design §2.2 step 1). Carries the guard fragment/params, ``requires_audit``, the pre-read row,
    and the identity the composed store transaction needs to build the guarded mutation + audit."""

    subject: Subject
    action: Action
    table: str
    row_id: str
    guard_fragment: str
    guard_params: dict[str, Any]
    requires_audit: bool
    audit: Any
    pre_read_row: dict[str, Any] | None

    def fragments(
        self, set_fragment: str | None, params: dict[str, Any] | None = None
    ) -> list[TxnFragment]:
        """The guarded mutation as composable fragments with the conflict guard IN-STORE (§2.2 step 2).

        ``LET $gw_hit = (UPDATE|DELETE type::record('<t>', $gw_id) [SET <set>] WHERE (<guard>)
        RETURN AFTER|BEFORE)`` then ``IF array::len($gw_hit) = 0 { THROW "governed_conflict:<t>:<id>"
        }`` (ONE fragment, two statements — ``compose`` supports it), plus the composed audit append
        when ``requires_audit``. ``params`` carries any bound values ``set_fragment`` references."""
        if set_fragment is None:
            guarded = (
                f"LET $gw_hit = (DELETE type::record('{self.table}', $gw_id) "
                f"WHERE ({self.guard_fragment}) RETURN BEFORE)"
            )
        else:
            guarded = (
                f"LET $gw_hit = (UPDATE type::record('{self.table}', $gw_id) SET {set_fragment} "
                f"WHERE ({self.guard_fragment}) RETURN AFTER)"
            )
        conflict_guard = (
            f'IF array::len($gw_hit) = 0 {{ THROW "governed_conflict:{self.table}:{self.row_id}" }}'
        )
        # Merge via a dict literal (NOT ``dict.update()``): the R4 no-raw-SDK scanner
        # (``test_governed_py_has_no_direct_sdk_call_site``) is NAME-keyed and would flag a
        # ``.update(`` here as a direct SDK ``update()`` call — a false positive on a dict method.
        fragment_params: dict[str, Any] = {
            "gw_id": self.row_id,
            **self.guard_params,
            **(params or {}),
        }
        fragments = [TxnFragment(statements=[guarded, conflict_guard], params=fragment_params)]
        if self.requires_audit:
            fragments.append(
                self.audit.append_fragment(
                    actor_principal=self.subject.principal_id,
                    actor_agent=self.subject.agent_id,
                    actor_email=self.subject.principal_id,
                    actor_agent_name=self.subject.agent_id,
                    action=self.action.value,
                    target_table=self.table,
                    target_row=f"{self.table}:{self.row_id}",
                )
            )
        return fragments


async def authorize_guarded(
    subject: Subject,
    action: Action,
    *,
    table: str,
    row_id: str,
    audit: Any,
    store: StoreHandle,
) -> GuardedPlan:
    """The PYTHON authorization leg split out of :func:`guarded_write` (design §2.2 step 1).

    Pre-reads the row's governed columns through the injected driver (acquire #1), runs the Python
    gate (deny → :class:`GovernedDenied`), and the RES-2 refuse (``requires_audit`` with no sink →
    :class:`GovernedAuditUnavailable`) — BEFORE any durable effect. It MUTATES NOTHING; it returns a
    frozen :class:`GuardedPlan` the caller composes into ONE store transaction."""
    pre_read = await run_query(
        acquire=store.acquire,
        drop=store.drop,
        url=store.url,
        noun="governed pre-read",
        label="governed.pre_read.rejected",
        statement=(
            f"SELECT owner_principal, owner_agent, scope FROM type::record('{table}', $gw_id)"
        ),
        params={"gw_id": row_id},
        logger=logger,
    )
    # am-37 §13.1 item 2 (B-D2): the ONE fail-closed row-list policy — a wrong-shaped pre-read raises
    # the store class instead of DECIDING this governed write as "row absent" (the fail-open shape).
    rows = rows_of(pre_read, noun="governed pre-read")
    requires_audit = False
    pre_read_row: dict[str, Any] | None = None
    if rows:
        row = rows[0]
        pre_read_row = row
        resource = pdp.Resource(
            table=table,
            owner_principal=_bare_or_none(row.get("owner_principal")),
            owner_agent=_bare_or_none(row.get("owner_agent")),
            scope=row.get("scope"),
        )
        decision = pdp.authorize(subject, action, resource)
        if not decision.allowed:
            raise GovernedDenied(
                f"{subject.role} {subject.principal_id}/{subject.agent_id} may not "
                f"{action.value} {table}:{row_id} — the row's owner/scope excludes it"
            )
        requires_audit = decision.requires_audit
    if requires_audit and audit is None:
        raise GovernedAuditUnavailable(
            f"the {action.value} on {table}:{row_id} is an audited bypass (requires_audit) but no "
            "AuditStore was supplied — refusing to run it UNAUDITED (RES-2 / §9 erase-the-trail); "
            "the consumer must wire a real audit sink for any bypass-reachable write"
        )
    guard_fragment, guard_params = pdp.authorize_filter(subject, action, table).to_surql()
    return GuardedPlan(
        subject=subject,
        action=action,
        table=table,
        row_id=row_id,
        guard_fragment=guard_fragment,
        guard_params=guard_params,
        requires_audit=requires_audit,
        audit=audit,
        pre_read_row=pre_read_row,
    )


async def guarded_write(
    subject: Subject,
    action: Action,
    *,
    table: str,
    row_id: str,
    set_fragment: str | None,
    audit: Any,
    store: StoreHandle,
) -> GuardedWriteResult:
    """THE single-row WRITE/DELETE/SET_SCOPE path (design §1.2 item 3 + §10.6) — single-brain on
    writes, reaching the store through the injected owner driver.

    ``store`` is the owning store's :class:`~loremaster.store._txn.StoreHandle` (design §10.6): the
    pre-read runs via ``run_query(acquire=store.acquire, drop=store.drop, url=store.url, …)`` and
    the guarded mutation + the ``requires_audit`` fragment compose via ``compose(mutation, audit)``
    → ``execute_transaction(…, acquire=store.acquire, drop=store.drop, url=store.url)`` — ONE
    verified multi-statement transaction (store-ref §3), every SDK call inside the retry/self-heal
    driver (R4; the ``_sdk_guard`` runtime gate sees no escape). NEVER a raw connection, NEVER a
    single-statement ``query=`` seam (it cannot run the mutation AND its audit CREATE as one
    verified ``BEGIN … COMMIT`` — design §10.6 "why the alternatives fail").

    Read the row's ``(owner_principal, owner_agent, scope)`` → build ``Resource`` → ``authorize()``
    (deny → :class:`GovernedDenied`; ``requires_audit`` → compose ``AuditStore.append_fragment``
    into the SAME transaction) → execute the mutation as a GUARDED statement carrying
    ``authorize_filter(subject, action, table).to_surql()`` in its WHERE and a ``RETURN``, and read
    ``row_count`` BACK from the guarded statement's returned rows (the ``messages.py`` ack-CAS
    precedent — the ACTUAL stamp, never a pre-read count; 0 ⇒ :class:`GovernedConflict`). The
    Python gate and the store guard are the SAME tree evaluated twice, so a write cannot land on a
    row the filter would exclude.

    ``set_fragment`` is the SurrealQL SET body for a WRITE/SET_SCOPE and ``None`` for a DELETE.
    """
    # ONE IMPLEMENTATION (design §2.2 step 3): guarded_write == authorize_guarded + GuardedPlan.
    # fragments + execute. The Python authorization leg (pre-read + gate + RES-2 refuse) lives in
    # authorize_guarded; the conflict guard moves IN-STORE (the LET/THROW GuardedPlan.fragments
    # emits), so the Python ``row_count == 0 → GovernedConflict`` branch is DELETED (unreachable —
    # the THROW fires first, §2.5). The store's typed TxnGovernedConflictError maps → GovernedConflict.
    plan = await authorize_guarded(
        subject, action, table=table, row_id=row_id, audit=audit, store=store
    )
    statement_text, merged_params = compose(*plan.fragments(set_fragment))
    # ONE verified BEGIN…COMMIT through the injected driver (acquire #2), inside write_guard so the
    # F5 runtime seam attributes it to this guarded frame. A THROW'd governed conflict aborts the
    # whole transaction and surfaces as the store's typed TxnGovernedConflictError (§2.5) → mapped to
    # GovernedConflict here (never text); any other domain rejection rolls back and PROPAGATES.
    with write_guard("guarded_write"):
        try:
            await execute_read_transaction(
                statement_text,
                merged_params,
                acquire=store.acquire,
                drop=store.drop,
                url=store.url,
            )
        except TxnGovernedConflictError as error:
            raise GovernedConflict(
                f"the guarded {action.value} on {table}:{row_id} matched ZERO rows — a concurrent "
                "scope/owner change landed between the read and the guarded mutation (no silent "
                "no-op)"
            ) from error
    # The in-store THROW fires on a zero-match, so reaching here means the single addressed record
    # was matched (0-or-1 by construction of ``type::record``): a successful guarded write is one row.
    return GuardedWriteResult(row_count=1, audited=plan.requires_audit)


def _bare(record_id: Any) -> str:
    """The bare id of a ``table:id`` record id string / RecordID (its ``id`` component)."""
    text = str(record_id)
    return text.split(":", 1)[-1] if ":" in text else text


def _bare_or_none(value: Any) -> str | None:
    """The bare id of an owner link, or ``None`` for a NONE (option<>) column (store-ref §2)."""
    return None if value is None else _bare(value)


#: The field a ``SELECT count() … GROUP ALL`` answer carries its total under (store-ref §5.1).
_GROUP_ALL_COUNT_KEY = "count"


def group_all_count(result: Any, *, noun: str) -> int:
    """THE one reader of a ``SELECT count() … GROUP ALL`` answer, with ONE fail-closed policy (packet 63c
    amendment 37 §8.3 — the §DRY ruling; §6 F-12 set the policy): an EMPTY list (a ``GROUP ALL`` over an
    empty set yields no group row — the engine's documented shape) is ``0``; ``[{"count": <int>}]`` is
    that int; ANY other shape — a non-list, a non-dict first row, a missing / non-int / bool ``count`` —
    raises :class:`SurrealStoreError` naming the read. A ``0`` there would be a served count describing
    no set, so a wrong-shaped dependency never reads as a count anything then decides from.

    Scope, as measured (am-37 §13 C F-2 — not a universal): every ``GROUP ALL`` count read in
    ``principals.py`` and ``governed.py`` calls THIS function rather than re-deciding the shape (ONE
    IMPLEMENTATION: a policy two callers must agree on is a function they call) — ``principals._scope_count``,
    the message migration's owner-leftover read, the SF-63-5 owned-row count and the cascaded-key count in
    ``PrincipalStore.delete``, and :func:`report_unmigrated_governed_rows` (am-37 §10.1 / §13 B F-1). Other
    ``GROUP ALL`` readers elsewhere in the package (findings, messages, tasks, diff, the store and manifest
    readers) still carry their own tolerant copies; they are routed to 64b's §DRY step (am-37 §8.3 / §10.1),
    decision point the 63c close-out.

    It is one of exactly THREE fail-closed shape readers in this module (am-37 §13 B / §13.1 item 1),
    beside :func:`rows_of` (a row list) and :func:`map_of` (an ``INFO FOR …`` map); no other function in
    ``governed.py`` / ``principals.py`` tests a store answer's shape itself.

    Args:
        result: The driver's answer to the ``GROUP ALL`` count.
        noun: What the read is, named in the raised message.

    Returns:
        The measured count.

    Raises:
        SurrealStoreError: The answer is not an empty list or a list whose first row carries an int
            ``count``.
    """
    if isinstance(result, list) and not result:
        return 0
    if isinstance(result, list) and isinstance(result[0], dict):
        count = result[0].get(_GROUP_ALL_COUNT_KEY)
        if isinstance(count, int) and not isinstance(count, bool):
            return count
    raise SurrealStoreError(
        f"the {noun} read answered a {type(result).__name__} without an integer `count` — "
        "nothing was decided from it"
    )


#: THE one post-write shape-fault text (am-37 §13.3 item 5): a write sink's answer read with ``landed=True``
#: that is not a row list. The write has already COMMITTED, so the text says so — a reader must never infer
#: "nothing happened" from a fault raised after the write landed.
_LANDED_SHAPE_FAULT = (
    "the {noun} LANDED (committed) but answered a {type} instead of its rows — nothing was decided from the "
    "answer; verify the stored state before re-running"
)


def rows_of(result: Any, *, noun: str, landed: bool = False) -> list[dict[str, Any]]:
    """THE one reader of a row-list answer (a ``SELECT`` / ``UPDATE … RETURN …`` result), with the ONE
    fail-closed shape policy (packet 63c amendment 37 §13 B): a list whose every member is a dict is
    returned WHOLE and in order; a non-list answer, or ANY non-dict member, raises
    :class:`SurrealStoreError` naming the read — never ``[]`` (which a caller would read as "no such row")
    and never a silent drop of the odd member (F-7: a filtered-out precondition row simply vanished).

    ``landed=True`` marks a POST-WRITE read — the answer of a write sink (``CREATE`` / ``UPDATE`` / a
    backfill) that has already committed. Its fault renders through the ONE template
    :data:`_LANDED_SHAPE_FAULT` (am-37 §13.3 item 5), so no call site writes its own post-write text.

    Args:
        result: The driver's answer.
        noun: What the read (or, with ``landed``, the write) is, named in the raised message.
        landed: ``True`` when ``result`` is a committed write's own answer.

    Returns:
        The answer's rows, unchanged.

    Raises:
        SurrealStoreError: The answer is not a list, or a member is not a dict.
    """
    if not isinstance(result, list):
        raise SurrealStoreError(_shape_fault(noun, result, landed=landed, position=None))
    for position, row in enumerate(result):
        if not isinstance(row, dict):
            raise SurrealStoreError(_shape_fault(noun, row, landed=landed, position=position))
    return result


def _shape_fault(noun: str, answered: Any, *, landed: bool, position: int | None) -> str:
    """:func:`rows_of`'s fault text: the ONE landed template for a post-write read, else the read's own
    wording (a whole answer, or the member at ``position``)."""
    kind = type(answered).__name__
    if landed:
        return _LANDED_SHAPE_FAULT.format(noun=noun, type=kind)
    if position is None:
        return f"the {noun} read answered a {kind}, not a row list — nothing was decided from it"
    return (
        f"the {noun} read answered a {kind} at row {position}, not a row object — nothing was decided from it"
    )


#: The ``INFO FOR …`` sub-maps :func:`map_of` checks when present (store-ref: ``INFO FOR DB`` carries
#: ``tables``; ``INFO FOR TABLE`` carries ``fields``).
_INFO_SUB_MAP_KEYS: tuple[str, ...] = ("tables", "fields")


def map_of(result: Any, *, noun: str, required: tuple[str, ...] = ()) -> dict[str, Any]:
    """THE one reader of an ``INFO FOR …`` answer, with the ONE fail-closed shape policy (packet 63c
    amendment 37 §13.1 item 1): a dict is returned WHOLE; a non-dict answer, or a ``tables`` / ``fields``
    sub-map that is present but not a dict, raises :class:`SurrealStoreError` naming the read — never an
    empty map, which a table gate would read as "no tables" and SKIP the guard it exists for (the
    fail-OPEN ``_table_exists`` shape B-D1 closed).

    Args:
        result: The driver's answer to an ``INFO FOR DB`` / ``INFO FOR TABLE`` statement.
        noun: What the read is, named in the raised message.
        required: Sub-map keys the caller DECIDES from, which must therefore be PRESENT (``("tables",)``
            for a table gate, ``("fields",)`` for a field gate) — an absent one is the wrong shape too.

    Returns:
        The answer's map, unchanged.

    Raises:
        SurrealStoreError: The answer is not a dict, a ``required`` key is absent, or its ``tables`` /
            ``fields`` sub-map is not one.
    """
    if not isinstance(result, dict):
        raise SurrealStoreError(
            f"the {noun} read answered a {type(result).__name__}, not an INFO map — nothing was "
            "decided from it"
        )
    for key in required:
        if key not in result:
            raise SurrealStoreError(
                f"the {noun} read answered a {type(result).__name__} without its `{key}` sub-map — nothing "
                "was decided from it"
            )
    for key in (*_INFO_SUB_MAP_KEYS, *required):
        if key in result and not isinstance(result[key], dict):
            raise SurrealStoreError(
                f"the {noun} read answered a {type(result[key]).__name__} `{key}` sub-map, not a "
                "map — nothing was decided from it"
            )
    return result


#: The DDL generators' naming contract (the membership rule — a new ``generate_<slice>_ddl`` joins the
#: derivation the day it lands; the test tree's ``schema_ddl_generators`` applies the same rule).
_DDL_GENERATOR_PREFIX = "generate_"
_DDL_GENERATOR_SUFFIX = "_ddl"

#: The width handed to a generator that takes ``dim``. Any positive width will do: the governed triple is
#: emitted identically at every width; only the vector index text varies.
_DERIVATION_DIM = 8

#: One ``DEFINE FIELD [OVERWRITE | IF NOT EXISTS] <column> ON [TABLE] <table>`` statement.
_DEFINE_FIELD_ON = re.compile(
    r"^DEFINE\s+FIELD\s+(?:OVERWRITE\s+|IF\s+NOT\s+EXISTS\s+)?(?P<column>\S+)\s+ON\s+(?:TABLE\s+)?"
    r"(?P<table>[^\s;]+)",
    re.IGNORECASE,
)


def governed_node_tables_of(ddl: str) -> frozenset[str]:
    """THE governed-table property over DDL TEXT (am-37 §13.4.1): a table is governed iff ``ddl`` defines
    EVERY column of the governed triple on it (``surreal_schema._governed_field_specs()`` — the ONE emitter
    of the triple, so the names are derived, never restated). A lone ``owner_principal`` is one of three
    and does not qualify. ``scripts/restore_prod_dump.py`` calls this for its synthetic-DDL and per-dump
    shape questions, so the property has one implementation."""
    triple = frozenset(name for name, _type, _constraint in surreal_schema._governed_field_specs())  # noqa: SLF001
    columns_by_table: dict[str, set[str]] = {}
    for statement in (part.strip() for part in ddl.split(";")):
        match = _DEFINE_FIELD_ON.match(statement)
        if match is not None:
            columns_by_table.setdefault(match.group("table"), set()).add(match.group("column"))
    return frozenset(table for table, columns in columns_by_table.items() if triple <= columns)


def _emitted_schema_ddl() -> str:
    """Every ``surreal_schema.generate_*_ddl`` function's output, joined — the ARTIFACT the image ships.
    ``dim`` is passed whenever a generator takes it; any OTHER required parameter RAISES naming it (fail
    closed: a skipped generator would silently shrink the governed set)."""
    outputs: list[str] = []
    for name, generator in sorted(inspect.getmembers(surreal_schema, inspect.isfunction)):
        if not (name.startswith(_DDL_GENERATOR_PREFIX) and name.endswith(_DDL_GENERATOR_SUFFIX)):
            continue
        kwargs: dict[str, Any] = {}
        for parameter in inspect.signature(generator).parameters.values():
            if parameter.name == "dim":
                kwargs["dim"] = _DERIVATION_DIM
            elif parameter.default is inspect.Parameter.empty:
                raise TypeError(
                    f"{name} requires {parameter.name!r}, which the governed-set derivation cannot supply"
                )
        outputs.append(generator(**kwargs))
    return "\n".join(outputs)


@functools.cache
def ddl_governed_tables() -> frozenset[str]:
    """The tables whose GENERATED DDL defines the governed triple (am-37 §13.4.2): today ``agent``,
    ``memory``, ``message``. Derived from the package's own generators, so the deployed image computes
    the same set the tests do. Cached: the generators are pure; ``cache_clear`` re-derives."""
    return governed_node_tables_of(_emitted_schema_ddl())


@dataclass(frozen=True)
class PendingGoverned:
    """Why a governed-by-intent table is governed before its DDL carries the triple, and which packet's
    migration will land it (am-37 §13.4.2)."""

    reason: str
    owning_packet: str


#: The DECLARED governed-by-intent tables (am-37 §13.4.2; moved here from ``scripts/restore_prod_dump.py``
#: so the image ships it and ``scripts`` consumes it): governed, reportable and restored, but with NO
#: governed columns in their DDL yet. SELF-DESTRUCTING: a pin reds BY MEMBER the day a table's DDL gains the
#: triple (``ddl_governed_tables() ∩ keys == ∅``), so this set can only shrink.
PENDING_GOVERNED_TABLES: Mapping[str, PendingGoverned] = MappingProxyType(
    {
        surreal_schema.BRIEF_TABLE: PendingGoverned(
            reason="the brief ledger is governed by intent; its governed columns and backfill land together",
            owning_packet="63c-ii",
        ),
        surreal_schema.FINDING_TABLE: PendingGoverned(
            reason="the finding ledger is governed by intent; its S2 leg migrates these rows",
            owning_packet="64b",
        ),
        surreal_schema.TASK_TABLE: PendingGoverned(
            reason="the task ledger is governed by intent; its S2 leg migrates these rows",
            owning_packet="64a",
        ),
    }
)


def governed_tables() -> frozenset[str]:
    """THE governed set — the REPORT domain (am-37 §13.4 / §13.4.2): :func:`ddl_governed_tables` ∪
    :data:`PENDING_GOVERNED_TABLES`."""
    return ddl_governed_tables() | frozenset(PENDING_GOVERNED_TABLES)


class GovernedTableRefusedError(ValueError):
    """A ``--table`` outside the verb's domain (am-37 §13.4): operator INPUT, so a ``ValueError`` — the
    lore-adm fault handler launders it to stderr + exit 1. Raised before any store I/O."""


def validate_governed_table(table: str, *, domain: Iterable[str], verb: str) -> None:
    """THE one ``--table`` validator (am-37 §13.4): ``table`` must be in ``domain``, else
    :class:`GovernedTableRefusedError` naming the verb and its domain (derived, sorted). Two domains, one
    function: ``report-unmigrated`` and :func:`report_unmigrated_governed_rows` pass :func:`governed_tables`;
    ``migrate-governed`` passes its leg-bearing set. ``table`` is interpolated into statements, so every
    caller validates BEFORE any I/O."""
    names = sorted(domain)
    if table not in names:
        raise GovernedTableRefusedError(
            f"{verb} does not support table {sanitise_line(table)!r} — its tables are "
            f"{', '.join(f'`{name}`' for name in names)}"
        )


async def report_unmigrated_governed_rows(store: StoreHandle, table: str) -> int:
    """Count ``table``'s rows that still carry a NONE ``scope`` — the forgotten-backfill measurement
    (design §1.2 item 5 / §2.3, §10.6 R4).

    ``table`` is interpolated into the statement, so it is validated HERE, before any I/O, through THE one
    validator :func:`validate_governed_table` over the GOVERNED set :func:`governed_tables` (am-37 §13.3
    item 4 / §13.4): every governed table — including a pending one — is accepted, whoever the caller is.

    Runs the bounded ``SELECT count() FROM <table> WHERE scope IS NONE GROUP ALL`` (IndexScan on
    3.2.4 — probe-63 P5) through the injected ``store`` :class:`~loremaster.store._txn.StoreHandle`
    (``run_query`` over ``store.acquire``/``store.drop``/``store.url`` — R4: no raw connection, no
    direct SDK call in ``governed.py``), reads the answer through :func:`group_all_count` (fail-closed),
    logs a non-zero count at WARNING with a DERIVED remedy, and returns it. The remedy (am-37 §13.3 item 6
    + §13.4.2 rider): a PENDING table names its entry's reason and owning packet (its rows read ``scope
    IS NONE`` because the column does not exist yet — nothing can migrate them today); a table a migrate
    LEG backfills (``principals._MIGRATING_TABLES``) names ``lore-adm migrate-governed --table <t>``; any
    other says no migrate verb accepts it yet. Never a verb that would refuse.

    Raises:
        GovernedTableRefusedError: ``table`` is not a governed table (a ``ValueError``; nothing was read).
        SurrealStoreError: The engine rejected the count, or answered it in the wrong shape.
    """
    # Function-local: ``principals`` imports this module (the house cycle-breaking idiom).
    from loremaster.principals import _MIGRATING_TABLES

    validate_governed_table(table, domain=governed_tables(), verb="report-unmigrated")
    result = await run_query(
        acquire=store.acquire,
        drop=store.drop,
        url=store.url,
        noun="governed unmigrated-scope count",
        label="governed.unmigrated_count.rejected",
        statement=f"SELECT count() FROM {table} WHERE scope IS NONE GROUP ALL",
        params={},
        logger=logger,
    )
    # am-37 §10.1(b): the ONE reader, fail-closed. A malformed answer raises the SAME
    # ``SurrealStoreError`` class ``run_query`` raises when the engine REJECTS this count, so it
    # takes the fate a rejected count already has (the ``report-unmigrated`` verb: stderr + exit 1)
    # — never a silent ``0``, which would be exactly the silent alarm #131 is about.
    count = group_all_count(result, noun="governed unmigrated-scope count")
    if count > 0:
        # LOUD, in the MESSAGE (not just structured extra): a forgotten backfill hides the fleet's
        # own data from the fleet, and a count nobody renders is a hope (#131 silent-(None,None)).
        pending = PENDING_GOVERNED_TABLES.get(table)
        if pending is not None:
            remedy = (
                f"`{table}` has no governed columns yet ({pending.reason}; packet {pending.owning_packet}) "
                f"— {count} row(s) will be scoped by that packet's migration"
            )
        elif table in _MIGRATING_TABLES:
            remedy = f"run `lore-adm migrate-governed --table {table}` to backfill"
        else:
            remedy = f"no migrate verb accepts `{table}` yet — {count} row(s) remain unscoped"
        logger.warning(
            "governed.unmigrated_rows: %d %s row(s) carry a NONE scope (member-invisible until "
            "migrated) — %s",
            count,
            table,
            remedy,
        )
    return count
