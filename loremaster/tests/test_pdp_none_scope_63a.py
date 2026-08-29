"""Contract — packet 63a: FORK 1 (design §10.1) — ``lorerunes.pdp.Resource.scope: str | None``,
where ``None`` is the ABSENT (unmigrated legacy) scope. RED before the 63a build; authored by
``contract-63a-2`` (Opus 4.8 contract author — tests ONLY; the §10 rider fold).

SPEC: ``docs/design/2026-08-28-packet63-retrofit-rulings.md`` §10.1 (FORK 1 — widen
``Resource.scope`` to ``str | None``; ``None`` = the absent legacy scope, a NAMED ``lorerunes``
touch; the empty-string forgery and every non-domain string still RAISE; ``to_surql`` never reads a
``Resource`` so the emitted SurrealQL is byte-identical) + §10.1 RIDER (i) (a NEW lorerunes pin:
``Resource(scope=None)`` constructs; for every member Subject READ/WRITE/SET_SCOPE ``matches`` is
False and admin is True; ``Resource(scope="")`` still raises) + §2.3 (a NONE scope is fail-closed —
invisible to every member, visible to admin).

⚠ THE WIDENING ITSELF IS A BUILDER TASK — this module ADDS the pin only. The pins construct
``Resource(scope=absent_scope())`` where ``absent_scope()`` returns ``None`` typed ``Any`` so the
typecheck gate stays GREEN at HEAD (where ``Resource.scope: str``) AND after the widening (no stale
``type: ignore``); the RED at HEAD is BEHAVIOURAL (``__post_init__`` → ``_is_valid_scope(None)``
raises), never a mypy failure (design §10.1 riders (iii)/(iv); the C-DEF-trap avoidance the shipped
``python_allowed_ids`` already practises).

Store-free: pure PDP unit pins (``authorize`` is synchronous; no SurrealDB).
"""

from __future__ import annotations

import pytest
from _governed_contract import MEMORY_TABLE, absent_scope, admin, member

import lorerunes as pdp

# ≥2 principals × keep/no-keep members — the "every member Subject" the §10.1 rider names.
_MEMBERS = (
    ("alice/ag_a1/no-keeps", member("alice", "ag_a1")),
    ("bob/ag_b1/no-keeps", member("bob", "ag_b1")),
    ("alice/ag_a1/{k1}", member("alice", "ag_a1", frozenset({pdp.keep_scope("k1")}))),
)
# The scope-dependent member actions (§10.1 rider (i)). DELETE is DELIBERATELY EXCLUDED — it is
# scope-INDEPENDENT (61 D4(a)) and its NONE-scope owner-can-delete positive control lives in
# test_memory_retrofit_63a.py::TestF2DeleteIsScopeIndependentOnDirtyRows (design §10.1 rider (ii)).
_SCOPE_DEPENDENT_MEMBER_ACTIONS = (
    pdp.Action.READ,
    pdp.Action.WRITE,
    pdp.Action.SET_SCOPE,
)
_SCOPE_SERVER = "server"  # grantable by a member (61 _grantable; §2.4) — proves the OWNER check,
#                           not non-grantability, blocks a member's SET_SCOPE on a NONE-owner row.


def _none_scope_unowned_resource() -> pdp.Resource:
    """A NONE-owner, NONE-scope legacy row (the §2.3 grandfather / m12 shape). Owner ``None`` means
    NO owner predicate matches, so the member verdict is driven purely by the absent scope."""
    return pdp.Resource(
        table=MEMORY_TABLE, owner_principal=None, owner_agent=None, scope=absent_scope()
    )


class TestResourceNoneScopeIsTheAbsentLegacyScope:
    """§10.1 FORK 1 — ``Resource(scope=None)`` is the absent (unmigrated legacy) scope, NOT "any
    scope": it CONSTRUCTS, it is scope-invisible to every member, admin sees it, and the empty
    string is STILL a forgery that raises."""

    def test_resource_constructs_with_a_none_scope(self) -> None:
        """⚠ RED at HEAD — ``Resource.scope: str`` today, so ``__post_init__`` → ``_is_valid_scope
        (None)`` RAISES (behavioural RED; the widening is a BUILDER task). After FORK 1 the literal
        ``None`` branch constructs. REDDENS a build that never widens the type (the finding stays
        open) OR that widens it but keeps rejecting ``None``."""
        resource = _none_scope_unowned_resource()
        assert resource.scope is None, (
            "Resource(scope=None) must construct with scope None (the ABSENT/legacy scope, §10.1) — "
            f"got {resource.scope!r}"
        )

    def test_a_none_scope_legacy_row_is_scope_invisible_to_every_member(self) -> None:
        """⚠ RED at HEAD (``Resource(scope=None)`` raises). §2.3 fail-closed: a NONE-scope legacy
        row matches NO member ``scope=$x`` disjunct, so READ/WRITE/SET_SCOPE are all DENIED for
        EVERY member — even a grantable-target SET_SCOPE, because the OWNER check fails on the
        NONE-owner row. REDDENS a build whose widening leaks a NONE-scope row to a member via ANY
        scope-dependent action (a legacy row silently visible/mutable by the wrong principal)."""
        resource = _none_scope_unowned_resource()
        leaks: list[str] = []
        for label, subject in _MEMBERS:
            for action in _SCOPE_DEPENDENT_MEMBER_ACTIONS:
                target = _SCOPE_SERVER if action is pdp.Action.SET_SCOPE else None
                if pdp.authorize(subject, action, resource, target_scope=target).allowed:
                    leaks.append(f"{label} · {action.value}")
        assert not leaks, (
            "a NONE-scope legacy row is member-visible/mutable via a scope-dependent action — it "
            f"must be fail-closed to EVERY member (§2.3): {leaks}"
        )

    def test_admin_sees_and_may_act_on_a_none_scope_legacy_row(self) -> None:
        """⚠ RED at HEAD (``Resource(scope=None)`` raises). §2.3: a NONE-scope row is admin-VISIBLE
        (``AllRows`` = True for every action incl. DELETE) — the fail-closed direction's other half.
        REDDENS a build that special-cases ``None`` → "deny everything" (which would hide the legacy
        row from admin too, defeating the admin-only recovery the §2.3 boot backfill relies on)."""
        resource = _none_scope_unowned_resource()
        admin_subject = admin("alice", "ag_a1")
        denied: list[str] = []
        for action in (pdp.Action.READ, pdp.Action.WRITE, pdp.Action.DELETE, pdp.Action.SET_SCOPE):
            target = _SCOPE_SERVER if action is pdp.Action.SET_SCOPE else None
            if not pdp.authorize(admin_subject, action, resource, target_scope=target).allowed:
                denied.append(action.value)
        assert not denied, (
            "admin (AllRows) must see AND act on a NONE-scope legacy row for every action — a build "
            f"that special-cases None→deny-everything hides it from admin too: {denied}"
        )

    def test_resource_still_rejects_an_empty_string_scope(self) -> None:
        """⚠ GREEN CONTROL (GREEN at HEAD AND on the correct build). The widening is NARROW: only
        the literal ``None`` is admitted — the EMPTY STRING stays the SEC-F3 forgery vector and
        RAISES. REDDENS a WRONG build that widens ``scope`` sloppily (e.g. to accept ``""`` or any
        falsy value as "absent"), reopening the forgery door FORK 1 explicitly keeps shut."""
        with pytest.raises(ValueError):
            pdp.Resource(table=MEMORY_TABLE, owner_principal=None, owner_agent=None, scope="")
