"""Gate for ``scripts/restore_prod_dump.py`` — packet 64's S2 restore instrument (amendment 3 §D-3).

The driver carries its controls as ``SelfTest.leg_*`` methods (runnable standalone via ``--self-test``);
this file runs every one of them inside the standard suite, because ``scripts/`` is in ``testpaths`` and a
guard nobody runs is a hope with a filename (#199). The live legs mint and reap their own ``test_dump_*``
databases on the spike-surreal TEST store (``:18000``, the same store every ``[real]`` test uses) and
prove the EXACT database they minted is gone afterwards — never a namespace set-diff, which races
concurrent xdist workers.

What this does NOT run: the driver against a real production dump. That is the S2 receipt run (§D-3's
named bound — an environment dependency, run at 64b-i/64a close-outs and 65's dress rehearsal).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# ``scripts/`` is not a package, so make that directory importable before importing it — the idiom
# ``test_forgery_door_sweep.py`` / ``test_token_survey.py`` already use.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import restore_prod_dump as driver  # noqa: E402  (path insert must precede the import)


def _declared_legs() -> set[str]:
    return set(driver.SelfTest.OFFLINE_LEGS) | set(driver.SelfTest.LIVE_LEGS)


def test_every_leg_method_is_registered_to_run() -> None:
    """REACH IS A CHECKED VARIABLE: a ``leg_*`` method missing from both tuples would never run."""
    defined = {name for name in dir(driver.SelfTest) if name.startswith("leg_")}
    assert defined == _declared_legs(), (
        f"unregistered legs {sorted(defined - _declared_legs())}; "
        f"registered-but-undefined {sorted(_declared_legs() - defined)}"
    )
    assert not set(driver.SelfTest.OFFLINE_LEGS) & set(driver.SelfTest.LIVE_LEGS)


@pytest.mark.parametrize("leg", driver.SelfTest.OFFLINE_LEGS)
def test_offline_leg(leg: str, tmp_path: Path) -> None:
    """Each offline control holds (no store, no network)."""
    getattr(driver.SelfTest(tmp_path), leg)()


@pytest.mark.parametrize("leg", driver.SelfTest.LIVE_LEGS)
def test_live_leg(leg: str, tmp_path: Path) -> None:
    """Each live control holds against the TEST store (mints + reaps its own ``test_dump_*`` DBs)."""
    getattr(driver.SelfTest(tmp_path), leg)()


def test_cli_offline_self_test_exits_zero() -> None:
    """The committed CLI entry point runs the same legs and reports success by exit code."""
    assert driver.main(["--self-test", "--offline"]) == driver.EXIT_OK


def test_cli_reap_refuses_a_foreign_name_before_touching_the_store() -> None:
    """``--reap`` of a name the driver did not mint is refused (exit 2) before any credential is read."""
    assert driver.main(["--reap", "lore"]) == driver.EXIT_REFUSED
