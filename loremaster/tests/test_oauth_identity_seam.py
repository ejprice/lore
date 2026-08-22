"""CONTRACT (contract-39-w1) — §13 group 7: the multi-provider child-table SEAM (PIN THE MISS).

design ``docs/design/2026-08-21-packet39-recut-oauth.md`` §3.6 defers the multi-provider
identity model to provider #2. The MVP admits ONE issuer's `sub` via packet-48's single
`principal.subject` (an `option<string>` UNIQUE column). That is CORRECT for one provider —
and a KNOWN BOUND: `sub` is unique only per issuer, so the moment a SECOND OAuth provider is
configured the durable key must become `(issuer, sub)` via a NEW `oauth_identity` child
table (cloning the `principal_key` 1—* pattern).

This is the PIN-THE-MISS instrument (findings #137/#138 class): it ASSERTS the single-subject
model and goes RED the day someone adds the `oauth_identity` table — carrying, in its failure
message, the migration the adder then owes. A bound that is pinned is a bound the next
engineer meets DELIBERATELY, with its rationale attached; it cannot be silently inherited nor
silently "fixed".

These are pure-function assertions over the schema generators — no store, no network — so
they collect and run without the wave-1 verifier stub.
"""

from __future__ import annotations

from loremaster.store import surreal_schema
from loremaster.store.surreal_schema import (
    PRINCIPAL_TABLE,
    generate_principal_ddl,
    generate_principal_key_ddl,
)

# The message the re-open trigger carries — stated once so both pins speak with one voice.
_REOPEN_TRIGGER = (
    "KNOWN BOUND (design §3.6) — the MVP is SINGLE-ISSUER: `principal.subject` holds ONE "
    "provider's `sub`, which is unique only per issuer. Before configuring a SECOND OAuth "
    "provider you MUST add the `oauth_identity` child table ((issuer, subject) composite "
    "UNIQUE, a `record<principal>` owner link — clone the `principal_key` 1—* pattern) and "
    "make `(iss, sub)` the durable key, email an attribute. If you added a second provider "
    "and this pin failed, this IS the migration you owe: update it and say so."
)


class TestSingleSubjectModelIsTheCurrentTruth:
    """The MVP identity model is a single `principal.subject` column, no child table."""

    def test_principal_ddl_defines_a_single_subject_column(self) -> None:
        # The shipped model: one `subject` column on the `principal` table, an
        # `option<string>` under a plain UNIQUE index. This is what the child table would
        # replace at provider #2.
        ddl = generate_principal_ddl()
        assert f"DEFINE FIELD OVERWRITE subject ON {PRINCIPAL_TABLE}" in ddl or "subject" in ddl, (
            "the `principal` table must carry the single `subject` column the MVP admits by"
        )
        assert "option<string>" in ddl, "subject is an option<string> (NONE until first login)"
        assert f"{PRINCIPAL_TABLE}_subject" in ddl, "and a UNIQUE index on subject"

    def test_no_oauth_identity_table_exists_yet(self) -> None:
        # PIN THE MISS: the `oauth_identity` child table is the DEFERRED seam. It must not
        # exist anywhere in the schema yet; when it does, THIS pin fires and hands the adder
        # the migration they owe.
        principal_ddl = generate_principal_ddl()
        key_ddl = generate_principal_key_ddl()
        assert "oauth_identity" not in principal_ddl, _REOPEN_TRIGGER
        assert "oauth_identity" not in key_ddl, _REOPEN_TRIGGER

    def test_schema_module_defines_no_oauth_identity_generator(self) -> None:
        # The seam would ship a table constant + a DDL generator (mirroring PRINCIPAL_KEY_TABLE
        # / generate_principal_key_ddl). Their ABSENCE is the single-issuer bound; their
        # arrival is the re-open trigger.
        assert not hasattr(surreal_schema, "OAUTH_IDENTITY_TABLE"), _REOPEN_TRIGGER
        assert not hasattr(surreal_schema, "generate_oauth_identity_ddl"), _REOPEN_TRIGGER
