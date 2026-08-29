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

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - typing only
    from lorerunes.pdp import Action, Subject


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
    multi-principal ``agent`` table). ``dry_run`` reports the counts without writing."""

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
    raise NotImplementedError("63a builder: resolve_subject (design §1.2 item 1)")


def read_filter(subject: Subject, table: str) -> tuple[str, dict[str, Any]]:
    """THE one read splice (design §1.2 item 2; R-a.3 — mutation-proven the single splice).

    A thin wrapper over ``authorize_filter(subject, Action.READ, table).to_surql()``: returns the
    self-contained fragment (61 #416 — parenthesised) + its content-addressed params, so every
    governed LIST read splices ``AND ({fragment})`` with MERGED params. The wrapper exists so the
    splice is ONE function, not a pattern each caller clones.
    """
    raise NotImplementedError("63a builder: read_filter (design §1.2 item 2)")


async def guarded_write(
    subject: Subject,
    action: Action,
    *,
    table: str,
    row_id: str,
    set_fragment: str | None,
    audit: Any,
) -> GuardedWriteResult:
    """THE single-row WRITE/DELETE/SET_SCOPE path (design §1.2 item 3) — single-brain on writes.

    Read the row's ``(owner_principal, owner_agent, scope)`` → build ``Resource`` → ``authorize()``
    (deny → :class:`GovernedDenied`; ``requires_audit`` → compose ``AuditStore.append_fragment``
    into the SAME transaction) → execute the mutation as a GUARDED statement carrying
    ``authorize_filter(subject, action, table).to_surql()`` in its WHERE, and check the returned
    row count (0 ⇒ :class:`GovernedConflict`). The Python gate and the store guard are the SAME
    tree evaluated twice, so a write cannot land on a row the filter would exclude.

    ``set_fragment`` is the SurrealQL SET body for a WRITE/SET_SCOPE and ``None`` for a DELETE.
    """
    raise NotImplementedError("63a builder: guarded_write (design §1.2 item 3)")
