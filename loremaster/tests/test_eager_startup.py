"""RETIRED by packet 59 (fastmcp 3.x migration) — the eager-startup APPARATUS this
contract pinned was DELETED, so the tests that certified it would certify a corpse.

Design ``docs/design/2026-08-15-fastmcp-3x-migration.md`` §5b-C2 (the DUAL) + M11. This
file is a SUPERSEDED-HEADER TOMBSTONE (the archive-don't-delete / dangling-address law):
its content is retired but the address resolves, so a future reader meets the retirement
DELIBERATELY rather than rediscovering it from a green test that certifies deleted code.

────────────────────────────────────────────────────────────────────────────────────────────
WHY IT IS RETIRED

Every test here pinned a mechanism the migration DELETES:

* ``_ProcessLifespanGuard`` (the per-process refcounted lease) and ``_EagerStartupLifespan``
  (the ASGI lifespan-interceptor that hoisted the heavy build to process startup) existed
  SOLELY to paper over the mcp SDK's per-SESSION lifespan re-entry. fastmcp 3.x enters the
  user ``lifespan=`` **once per PROCESS** (ref-counted ``_lifespan_manager``), so both are
  dead weight and are removed (~150 LOC, spike Item 1 GO). ``mcp._lore_eager_guard`` (the
  attribute this file's ``TestBuildMcpServerSurfacesGuardAdditively`` asserted) is gone with
  them.
* ``_SpyGuard`` / ``_SpyInnerApp`` / the raw-ASGI-``lifespan``-protocol drivers modelled the
  interceptor's internals; there is no interceptor to model.

The properties this file cared about SURVIVE — they moved to where they are now testable:

* **eager-at-startup / once-per-process / concurrent-reuse / sequential-survival** — fastmcp
  native, and pinned as the ``@pytest.mark.wire`` once-per-process gate in
  ``test_fastmcp_migration.py::TestTheHeavyBuildRunsOncePerProcessEagerly`` (design DUAL
  #16/#17/#19). In-memory transport skips the ASGI lifespan (FG1), so this is a REAL-uvicorn
  gate, not an in-process unit pin — which is exactly why it cannot live here.
* **failed-build-does-not-wedge + bounded retry (FP-07, #21)** —
  ``test_fastmcp_migration.py::TestTheEagerHeavyBuildRetriesTransientFailures`` drives the
  re-homed ``loremaster.server._eager_build_with_retry`` directly (fail-then-succeed comes up;
  all-fail fails closed after the budget; the inter-attempt sleep routes through the shared
  ``loresigil.backoff`` — the #102/#207 routing-is-sharing mutation).
* **the apparatus stays deleted** — ``test_fastmcp_migration.py::TestTheHeavyBuildRunsOncePer
  ProcessEagerly::test_the_deleted_apparatus_is_gone`` reddens the day someone re-adds a
  hand-rolled per-session guard.
* **Origin/Bearer preserved** — ``test_auth_composition.py`` + the ``@wire`` auth gate.

────────────────────────────────────────────────────────────────────────────────────────────
⚠ ONE REMOVED BEHAVIOUR — RESTORED (operator ruling 2026-08-16; builder-59b / F2)

``TestEagerBuildFailureMessageDoesNotLeakSecrets`` (retired above) pinned that the interceptor
surfaced ``lifespan.startup.failed`` with a FIXED operator-safe phrase
(``_EAGER_BUILD_FAILED_MESSAGE``) — never ``str(exc)`` — so a credentialed exception (a
``surreal.url`` / embedding ``base_url`` carrying ``user:pass@host``) could not leak into
uvicorn's UNREDACTED startup log, while the real detail was logged through the redaction-
backstopped lore sink. builder-59 flagged its DROP; the operator RULED to RESTORE it (decision
30e56ac8, ``lore_recall("fastmcp migration")``), NOT accept the drop.

It is restored WITHOUT reviving the deleted ~150-LOC apparatus:
``loremaster.server._eager_build_or_operator_safe_error`` is the native ``lifespan=``'s
operator-safe layer over ``_eager_build_with_retry`` — on total (``Exception``) failure it logs
the redacted detail (``logger.error(exc_info=exc)``) and raises a fixed
``_EAGER_BUILD_FAILED_MESSAGE`` (``from None`` — no chained credentialed cause). The retry helper
itself still RE-RAISES the original exception (the FP-07 contract pinned by
``test_fastmcp_migration``/``test_backoff_seam``), so the conversion lives in the wrapper, not
the helper. The behavioural pin is re-homed HERE — see
``TestEagerBuildFailureMessageDoesNotLeakSecrets`` below (a live test again, not a tombstone).
This DUAL companion is complemented at the SOURCE by ``CredentialFreeUrl`` in ``config.py``
(security-59 F1): a userinfo URL is now rejected at config LOAD, so the credential never enters
a URL that a boot exception could carry.
"""

from __future__ import annotations

import importlib
import traceback

import pytest


def test_the_eager_startup_apparatus_this_contract_pinned_is_retired() -> None:
    """Anti-regression half of the tombstone (design §5b-C2 / M11): the apparatus stays gone.

    This file's entire rationale was the per-session ``_ProcessLifespanGuard`` +
    ``_EagerStartupLifespan`` eager-startup composition. Packet 59 deleted it (fastmcp enters
    the ``lifespan=`` once per process natively). If a later change re-adds a hand-rolled
    per-session lifespan guard/interceptor, its premise is back and a real (re-expressed)
    eager-startup contract is owed again — this pin goes RED to say so, and points at the
    surviving coverage rather than reviving this deleted-mechanism suite.
    """
    server = importlib.import_module("loremaster.server")
    for retired in ("_ProcessLifespanGuard", "_EagerStartupLifespan"):
        assert not hasattr(server, retired), (
            f"loremaster.server.{retired} is back. Packet 59 retired the eager-startup "
            f"apparatus (design §5b-C2) — fastmcp enters the user lifespan once per process. A "
            f"revived per-session guard/interceptor re-introduces the mechanism this suite "
            f"policed; re-express the eager-startup contract for the fastmcp world (the "
            f"once-per-process @wire gate + FP-07 unit pins in test_fastmcp_migration.py) "
            f"rather than reviving these tests, which pin deleted symbols."
        )


@pytest.mark.skip(
    reason="RETIRED by packet 59 — the eager-startup apparatus is deleted; its surviving "
    "properties are re-pinned in test_fastmcp_migration.py (once-per-process @wire gate + the "
    "FP-07 TestTheEagerHeavyBuildRetriesTransientFailures unit pins). See the superseded-header "
    "docstring."
)
def test_eager_startup_properties_are_re_pinned_by_the_migration_contract() -> None:
    """Placeholder recording the hand-off, kept visible so the coverage is not silently absent."""


class TestEagerBuildFailureMessageDoesNotLeakSecrets:
    """F2 — RESTORED (operator ruling 2026-08-16). A TOTAL eager-build failure surfaces a
    FIXED operator-safe message (never ``str(exc)``) out of the native ``lifespan=``, and
    logs the REAL detail through lore's REDACTING sink. So a credentialed boot exception
    (a ``surreal.url`` carrying ``user:pass@host`` in a ``SurrealConnectionError``) cannot
    leak into uvicorn's UNREDACTED startup log.

    Driven directly against the module-level
    ``loremaster.server._eager_build_or_operator_safe_error`` (the boot boundary's
    operator-safe layer). ``_eager_build_with_retry`` itself still re-raises the ORIGINAL
    exception (the FP-07 contract), which is why the conversion lives in the wrapper —
    these pins prove the wrapper, not a change to the helper.
    """

    _SECRET_URL = "ws://root:hunter2@db.internal:8000/rpc"

    async def _build_that_fails_with_a_credentialed_exception(self) -> None:
        # Mirrors SurrealConnectionError's shape (security-59 F4): config.surreal.url is
        # interpolated verbatim into the boot exception, so its credential is in str(exc).
        raise RuntimeError(f"could not connect to SurrealDB at {self._SECRET_URL!r}: refused")

    async def test_the_propagated_message_is_the_fixed_phrase_not_the_exception_string(self) -> None:
        server = importlib.import_module("loremaster.server")
        with pytest.raises(RuntimeError) as raised:
            await server._eager_build_or_operator_safe_error(
                self._build_that_fails_with_a_credentialed_exception,
                max_attempts=2,
                backoff_base_s=0.0,
            )
        assert str(raised.value) == server._EAGER_BUILD_FAILED_MESSAGE, (
            f"the propagated boot-failure message is {str(raised.value)!r}, not the fixed "
            f"operator-safe phrase {server._EAGER_BUILD_FAILED_MESSAGE!r} — a credentialed "
            f"str(exc) would reach uvicorn's UNREDACTED startup log (F2)."
        )

    async def test_no_credential_rides_the_propagated_traceback(self) -> None:
        # ``from None`` must suppress the chained cause: the FULL formatted traceback of the
        # propagated exception (Starlette/uvicorn format it via traceback.format_exc) must
        # NOT contain the credentialed URL. Drop ``from None`` and this reddens.
        server = importlib.import_module("loremaster.server")
        with pytest.raises(RuntimeError) as raised:
            await server._eager_build_or_operator_safe_error(
                self._build_that_fails_with_a_credentialed_exception,
                max_attempts=2,
                backoff_base_s=0.0,
            )
        formatted = "".join(
            traceback.format_exception(
                type(raised.value), raised.value, raised.value.__traceback__
            )
        )
        assert "hunter2" not in formatted and self._SECRET_URL not in formatted, (
            "the credentialed URL rode the propagated traceback (the chained cause was not "
            f"suppressed) — Starlette/uvicorn would log it unredacted. Traceback:\n{formatted}"
        )

    async def test_the_real_detail_is_logged_through_the_lore_sink_with_exc_info(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The other HALF: the operator diagnostic (WHY startup failed) must still be logged,
        # with exc_info, on the loremaster.server logger (lore's redaction-backstopped sink) —
        # so the real detail is kept, only OFF uvicorn's unredacted channel. Spy the logger's
        # error() directly (robust vs caplog + the lore sink's propagate=False).
        server = importlib.import_module("loremaster.server")
        logged_exc_infos: list[object] = []
        real_error = server.logger.error

        def _spy_error(msg: object, *args: object, **kwargs: object) -> None:
            logged_exc_infos.append(kwargs.get("exc_info"))

        monkeypatch.setattr(server.logger, "error", _spy_error)
        with pytest.raises(RuntimeError):
            await server._eager_build_or_operator_safe_error(
                self._build_that_fails_with_a_credentialed_exception,
                max_attempts=2,
                backoff_base_s=0.0,
            )
        # exactly the real (credentialed) exception is handed to the REDACTING sink — proving
        # BOTH halves are restored (detail logged there, fixed phrase raised to uvicorn).
        assert any(
            isinstance(exc_info, BaseException) and self._SECRET_URL in str(exc_info)
            for exc_info in logged_exc_infos
        ), (
            "the real boot-failure detail was NOT logged with exc_info on lore's sink — F2 "
            "restores BOTH halves (redacted diagnostic + fixed operator-safe raise), not one."
        )
        assert real_error is not None  # sanity: the spied attribute existed
