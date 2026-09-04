"""The shared GOVERNED SUBSTRATE — packet 63a (STUB / runnable-RED).

⚠ THIS IS A CONTRACT STUB, authored by ``contract-63a`` (Opus 4.8 contract author). Every
public symbol here exists so the RED contract COLLECTS and fails BEHAVIORALLY; the bodies raise
``NotImplementedError``. The builder (63a GREEN) replaces the bodies — it does NOT change the
shapes, which ARE the contract (design ``docs/design/2026-08-28-packet63-retrofit-rulings.md``
§1.2, items 1–3).

This is the ONE-IMPLEMENTATION address the design mandates: the Subject-resolution, the read
splice, and the guarded write are FUNCTIONS the memory retrofit (63a) and comms (63b/63c) and
tasks/findings (64) CALL — never patterns they clone (§1.1 countermand; CLAUDE.md
"ONE IMPLEMENTATION"). It lives in ``loremaster`` (store-reading orchestration — the ESC-1 split:
``lorerunes`` holds predicates, ``loremaster`` holds entry points).
"""

from __future__ import annotations

import contextlib
import contextvars
import logging
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loremaster.store._txn import (
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

    RES-2 (`docs/plans/v2/receipts/…/REPORT-cold-audit-63a.md` §RES). CONTRACT STUB authored by
    ``contract-63a-iii``: the ``raise`` site is a builder deliverable (63a-iii GREEN) inside
    :func:`guarded_write`, BEFORE composing the guarded mutation, when ``requires_audit and audit is
    None``. At HEAD ``dd5c9b2`` ``guarded_write`` SILENTLY SKIPS the audit (`if requires_audit and
    audit is not None`) and proceeds — the fail-open this type closes."""


@dataclass(frozen=True)
class GuardedWriteResult:
    """The outcome of :func:`guarded_write` (design §1.2 item 3). ``row_count`` is the guarded
    statement's returned-row count (0 ⇒ ``GovernedConflict`` was raised, never returned)."""

    row_count: int
    audited: bool


@dataclass(frozen=True)
class MigrateGovernedResult:
    """Receipts of a ``lore-adm migrate-governed`` run over ONE table (design §1.2 item 5 /
    §2.1) — receipts-printing: rows scanned / backfilled / already-migrated, and a LOUD
    ``refused`` (with ``reason``) on a precondition failure (the agent-first ORDER, or a
    multi-principal ``agent`` table). The migration is a one-shot cutover verb that always
    EXECUTES (the dry-run/--execute paradigm was struck 2026-08-20 — §10.7-W); the counts ARE
    the receipt. The read-only PREVIEW is the separate ``report-unmigrated`` verb."""

    table: str
    scanned: int
    backfilled: int
    already_migrated: int
    refused: bool
    reason: str | None = None


@dataclass(frozen=True)
class LegacyMapping:
    """A per-table backfill mapping for ``lore-adm migrate-governed`` (design §2.1). ONE verb,
    N table rows: the disposition names how a legacy row's ``(owner_principal, owner_agent,
    scope)`` is derived — UNOWNED-LEGACY (memory/brief: NONE/NONE), OWNED-BY-LINK (message:
    sender / sender.owner_principal), STRING-UNRESOLVABLE (64: a bare name is never promoted).
    The scope is always the canonical project keep. The shapes are the contract; the builder
    fills the SurrealQL."""

    table: str
    disposition: str


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

    # (2) the transport token's principal (its email IS access_token.subject). An unknown
    # principal DENIES — a Subject is NEVER constructed with a guessed/empty principal (SEC-F3).
    email = getattr(access_token, "subject", None)
    if not email:
        raise GovernedDenied(
            "the transport token carries no principal subject — a governed identity requires an "
            "admitted principal (the token_verifier sets subject = principal.email)"
        )
    principal = await principal_store.get_by_email(email)
    if principal is None:
        raise GovernedDenied(
            f"no principal is admitted for {email!r} — the transport token names an unknown "
            "principal; a governed identity requires an admitted principal"
        )

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
    rows = pre_read if isinstance(pre_read, list) else []
    requires_audit = False
    pre_read_row: dict[str, Any] | None = None
    if rows:
        row = rows[0] if isinstance(rows[0], dict) else {}
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


async def report_unmigrated_governed_rows(store: StoreHandle, table: str) -> int:
    """The §2.3 forgotten-backfill alarm (design §1.2 item 5 / §2.3, §10.6 R4) — STUB / runnable-RED.

    Runs the bounded ``SELECT count() FROM <table> WHERE scope IS NONE GROUP ALL`` (IndexScan on
    3.2.4 — probe-63 P5) through the injected ``store`` :class:`~loremaster.store._txn.StoreHandle`
    (``run_query`` over ``store.acquire``/``store.drop``/``store.url`` — R4: no raw connection, no
    direct SDK call in ``governed.py``), logs the non-zero count at WARNING naming the
    ``migrate-governed`` remedy (the #131 silent-``(None, None)`` class: a count nobody renders is a
    hope), and returns it. The builder fills the body; the SHAPE (a ``StoreHandle`` in, an int out)
    is the contract.
    """
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
    count = 0
    if isinstance(result, list) and result and isinstance(result[0], dict):
        count = int(result[0].get("count", 0) or 0)
    if count > 0:
        # LOUD, in the MESSAGE (not just structured extra): a forgotten backfill hides the fleet's
        # own data from the fleet, and a count nobody renders is a hope (#131 silent-(None,None)).
        logger.warning(
            "governed.unmigrated_rows: %d %s row(s) carry a NONE scope (member-invisible until "
            "migrated) — run `lore-adm migrate-governed --table %s` to backfill",
            count,
            table,
            table,
        )
    return count
