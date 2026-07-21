"""Finding #101 — ``configure_logging()`` permanently BLINDS ``caplog`` for every
later test in the same worker process, and the blindness is SILENT.

THE MECHANISM (diagnosed, not guessed — cold audit 102b §D-2):

``configure_logging()`` sets ``logger.propagate = False`` on every lore namespace
(``logging_setup.py:244``) — correct for production, where lore's structured stream
must not double-emit through uvicorn's root handler. But **pytest's ``caplog``
captures by installing a handler on the ROOT logger, which is reached ONLY by
propagation.** So the moment any test triggers ``configure_logging()`` — a server
startup does, via ``server.py:860`` / ``:6460`` — every subsequent ``caplog``
assertion in that worker process silently sees an EMPTY record list.

Nothing restores it. ``test_logging_setup.py`` has a restore fixture, but it is
MODULE-scoped: it protects only itself.

WHY THIS IS THE #102 CONTRACT'S PROBLEM. It compromises **three of finding #102's own
load-bearing pins** — including ``TestTxnConflictRootCauseIsTheMarkerBearingEntry``
``[marker-first]``, which asserts on a server-side log record. A pin that cannot see
the log it asserts on does not report a logging fault; it reports that the code under
test misbehaved. The signal is not just lost, it is *inverted*.

It fired in 2 of 8 full-suite runs (25%), one test each, a DIFFERENT victim each time —
because the victim is whichever caplog test the shard lottery schedules after a
logging-configuring one. **It is NOT flaky. It is deterministic given the ordering**,
and this repo's law forbids "flaky" as a verdict. A future builder will be tempted.

------------------------------------------------------------------------------
WHY THE PIN IS SHAPED THE WAY IT IS — I got this wrong once and caught it.

My first attempt asserted *"call ``configure_logging()``, then caplog still captures"*
in a single test. **It is RED against a CORRECT fix.** I proved that by building both
candidate fixes and running them: a root-conftest restore fixture (which genuinely
repairs the leak) still leaves that assertion red, because within that one test
propagation really has been turned off. A pin that stays red on a correct build teaches
a builder that red means nothing — the single worst thing a contract can do.

The defect is a **leak ACROSS a test boundary**, so the pin must observe a test
boundary. It runs the ordered pair in a **fresh, serial pytest subprocess**: order is
deterministic, the outer run's xdist sharding cannot split it, and the repo's real
``conftest.py`` — where the fix belongs — is still loaded. RED before 4c2efbf; GREEN the moment a
restore fixture exists.

The pair is skipped in the outer run (see ``_NESTED_RUN_ENV``) precisely so this module
does not commit the sin it is here to police.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

import pytest
from loremaster.logging_setup import LORE_NAMESPACES, configure_logging

# The lore logger a real pin actually asserts on: the transaction seam's, whose
# ``store.transaction.rolled_back`` record is the receipt three of finding #102's pins
# read. If caplog is blind to THIS one, those pins are blind.
_PROBE_LOGGER = "loremaster.store._txn"
_PROBE_EVENT = "caplog.isolation.probe"

_LEVEL = "INFO"
_FORMAT = "json"

# Set only inside the nested run. The ordered pair below would poison the worker that
# ran it, so in the OUTER suite it stays skipped and only the driver executes.
_NESTED_RUN_ENV = "LORE_CAPLOG_LEAK_PROBE"
_nested = os.environ.get(_NESTED_RUN_ENV) == "1"


@pytest.mark.skipif(not _nested, reason="runs only inside the nested serial probe")
class TestTheLeak:
    """The ordered pair. Executed ONLY by the nested pytest subprocess below."""

    def test_1_a_startup_test_configures_logging(self) -> None:
        """Stands in for any test that boots a server — ``server.py`` calls
        ``configure_logging()`` on startup, so a great many tests do this by accident.
        """
        configure_logging(_LEVEL, _FORMAT)
        assert not logging.getLogger(LORE_NAMESPACES[0]).propagate, (
            "configure_logging() no longer disables propagation — if that is a "
            "deliberate production change, this probe is obsolete and should be retired"
        )

    def test_2_a_later_test_can_still_use_caplog(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """THE VICTIM. It never touches logging config; it just wants to read a log
        record — exactly like finding #102's root-cause pins.

        RED before 4c2efbf: the previous test's ``propagate=False`` was still in force, caplog's
        root handler was never reached, and this saw an empty list while believing the
        code under test simply emitted nothing.
        """
        with caplog.at_level(logging.ERROR, logger=_PROBE_LOGGER):
            logging.getLogger(_PROBE_LOGGER).error(_PROBE_EVENT)

        assert any(record.getMessage() == _PROBE_EVENT for record in caplog.records), (
            "caplog is BLIND. An earlier test called configure_logging(), which sets "
            "propagate=False on the lore namespaces (logging_setup.py:244); caplog "
            "captures via a handler on the ROOT logger, reached only by propagation; and "
            "NOTHING restores it. Every later caplog test in this worker silently sees an "
            "empty record list. Restore lore-logger state around every test in the ROOT "
            "conftest, so every module is protected — not just the two that remembered."
        )


class TestCaplogIsNotLeakedAcrossTests:
    """The driver: proves the leak, or proves it is fixed."""

    def test_caplog_still_works_in_a_test_that_follows_configure_logging(self) -> None:
        """RED before 4c2efbf. GREEN once lore-logger state is restored at the test boundary.

        Runs the ordered pair in a FRESH, SERIAL pytest subprocess:

        * order is guaranteed (the outer ``-n auto`` shard lottery cannot split it — the
          very lottery that makes this defect look random);
        * the repo's real ``conftest.py`` still loads, so the fix is exercised where it
          will actually live, rather than a mock of it;
        * and the poison is confined to a process that dies immediately.
        """
        environment = dict(os.environ, **{_NESTED_RUN_ENV: "1"})
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                f"{Path(__file__).resolve()}::TestTheLeak",
                "-p",
                "no:randomly",
                "-q",
                "--no-header",
            ],
            capture_output=True,
            text=True,
            env=environment,
            cwd=Path(__file__).resolve().parents[2],
            check=False,
        )

        # POSITIVE CONTROL: the pair must actually RUN. If it were skipped or
        # collection-errored, a green result would be vacuous — the failure mode this
        # whole module exists to hunt.
        assert "2 passed" in completed.stdout or "1 failed" in completed.stdout, (
            f"the nested probe did not run its two tests — a green here would be "
            f"meaningless.\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )

        assert completed.returncode == 0, (
            "A test that calls configure_logging() BLINDS caplog for every later test in "
            "the same worker process — silently. Three of finding #102's own pins assert "
            "on log records and are exposed to it.\n\n"
            "Restore lore-logger handlers/level/propagate around every test, in the ROOT "
            "conftest (loremaster/tests/conftest.py), so every module is protected.\n\n"
            f"nested run output:\n{completed.stdout}"
        )


class TestTheProbeItselfCanSee:
    """POSITIVE CONTROL for the probe, in the OUTER process.

    If caplog could not see ``_PROBE_LOGGER`` at all — wrong name, wrong level, wrong
    usage — the nested failure above would prove nothing about propagation. This shows
    the instrument works before anything touches it.
    """

    def test_caplog_sees_the_probe_logger_in_a_pristine_process(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.ERROR, logger=_PROBE_LOGGER):
            logging.getLogger(_PROBE_LOGGER).error(_PROBE_EVENT)

        assert any(record.getMessage() == _PROBE_EVENT for record in caplog.records), (
            "caplog cannot see the probe logger even in a pristine process — the probe is "
            "broken and the nested result below cannot be trusted"
        )
