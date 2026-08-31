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

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from loremaster.store._txn import (
    TxnFragment,
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
    # (1) pre-read the row's governed columns THROUGH the injected driver (acquire #1) — never a
    # raw connection (R4). An explicit projection reads a NONE option<> column back as None
    # (store-ref §2), so a legacy row yields a NONE-scope Resource (FORK 1).
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

    # (2) the Python gate. A row the filter EXCLUDES is a DENY (single-brain — the store guard in
    # step 3 is the SAME predicate, so a denied write never touches the store). A MISSING row is
    # NOT a deny — it falls through to the guarded mutation, which matches 0 rows → GovernedConflict
    # (the vanished-conflict path), so a no-row deny cannot masquerade as a conflict.
    requires_audit = False
    if rows:
        row = rows[0] if isinstance(rows[0], dict) else {}
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

    # (3) the guarded mutation: carry authorize_filter(action) in the WHERE (the SAME tree the
    # Python gate evaluated), so the write re-checks ownership in the SAME statement — no
    # read-then-write TOCTOU window on the governed columns. RETURN the affected rows so row_count
    # is read BACK from the actual stamp (the messages.py ack-CAS precedent), never a pre-read count.
    guard_fragment, guard_params = pdp.authorize_filter(subject, action, table).to_surql()
    if set_fragment is None:
        mutation = (
            f"DELETE type::record('{table}', $gw_id) WHERE ({guard_fragment}) RETURN BEFORE"
        )
    else:
        mutation = (
            f"UPDATE type::record('{table}', $gw_id) SET {set_fragment} "
            f"WHERE ({guard_fragment}) RETURN AFTER"
        )
    fragments = [TxnFragment(statements=[mutation], params={"gw_id": row_id, **guard_params})]

    # requires_audit → compose the audit append into the SAME transaction (61a built
    # append_fragment "for what 63/64 compose"): the audit RIDES the mutation's BEGIN…COMMIT, so a
    # rejected mutation rolls the audit back too (no landed audit for a write that never happened).
    audited = False
    if requires_audit and audit is not None:
        fragments.append(
            audit.append_fragment(
                actor_principal=subject.principal_id,
                actor_agent=subject.agent_id,
                # The Subject (lorerunes) carries only ids; the denormalized human email/name are
                # not on it, so the resolved ids stand in for the non-empty forensic columns.
                actor_email=subject.principal_id,
                actor_agent_name=subject.agent_id,
                action=action.value,
                target_table=table,
                target_row=f"{table}:{row_id}",
            )
        )
        audited = True

    statement_text, merged_params = compose(*fragments)
    # ONE verified BEGIN…COMMIT through the injected driver (acquire #2) — every statement checked
    # (store-ref §3). A domain rejection (the guarded set violating a schema ASSERT) rolls the whole
    # transaction — including the composed audit — back and PROPAGATES (not swallowed).
    results = await execute_read_transaction(
        statement_text,
        merged_params,
        acquire=store.acquire,
        drop=store.drop,
        url=store.url,
    )
    # row_count from the mutation's RETURN BY SHAPE: the BEGIN/COMMIT envelope carries None entries,
    # so the first LIST result is the mutation's affected rows (composed first, before the audit).
    row_payloads = [entry for entry in results if isinstance(entry, list)]
    row_count = len(row_payloads[0]) if row_payloads else 0
    if row_count == 0:
        raise GovernedConflict(
            f"the guarded {action.value} on {table}:{row_id} matched ZERO rows — a concurrent "
            "scope/owner change landed between the read and the guarded mutation (no silent no-op)"
        )
    return GuardedWriteResult(row_count=row_count, audited=audited)


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
