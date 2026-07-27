"""Contract — packet 01a §A: the conformance provenance guard.

The conformance harness runs the baked test suite INSIDE the deployed image against
the ``:ro`` ``/workspace`` mount of this repo. The one trap it exists to close (#139,
the same root as #140/#131/#107): a test run that imports the MOUNTED source instead
of the BAKED artifact proves the *recipe*, never the *cake*. A green suite over the
mount is worse than a red one — it certifies code the deployed container does not run.

``conformance_provenance`` answers ONE question per workspace member and refuses to
guess: does ``import <member>`` — in the interpreter this guard is *run with* — resolve
to code BAKED into the image (``/app/...`` editable OR site-packages), or to the
``:ro`` ``/workspace`` MOUNT? It is the exact inverse of ``scripts/scratch_provenance.py``
(which asks "is this INSIDE the scratch tree?"); the sibling's shape is the model, but
the module is SELF-CONTAINED and must not import it (design doc LAYOUT).

These pins are BLIND to the implementation (it does not exist yet) — importing the
module is the first thing that goes RED. They define the interface:

* ``MemberProvenance`` — the ``(name, module_file, import_error)`` record per member.
* ``ConformanceGuard(mount_root)`` — ``.verdict(member) -> str | None`` (None == honest,
  else the reason it is not) and ``.audit(resolver, members=...) -> (failures, receipts)``
  which evaluates EVERY member even after the first failure.
* ``import_member(name) -> MemberProvenance`` — imports a member in THIS interpreter.
* ``WORKSPACE_MEMBERS`` — every ``[tool.uv.workspace] members`` entry. The value is
  NOT restated here: this line said ``("loremaster", "loresigil", "lorescribe")`` and
  went silently false the day packet 42 added ``lorerunes``, while the constant, the
  test names and the class docstrings below were all correctly widened. :data:`EXPECTED_MEMBERS`
  is the one place the expected value is written down.
* ``main(argv=None) -> int`` — the ``--mount-root``-parameterised CLI: exit 0 when every
  member is baked, non-zero + a loud headline NAMING the mount on a mount hit.

Run:
    cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path

# ``conformance_provenance`` lives in ``scripts/`` (not a package) — make it importable
# exactly as ``scripts/test_scratch_copy.py`` makes ``scratch_provenance`` importable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import conformance_provenance  # noqa: E402  (scripts/ is not a package)
import pytest  # noqa: E402

# ---------------------------------------------------------------------------
# Independent expected values (from the spec / design doc — never the impl).
# ---------------------------------------------------------------------------

# The uv-workspace members whose code the conformance run must prove it is actually
# running. From the design doc §A + ``[tool.uv.workspace] members``, NOT read back from
# the module (that would be tautological — the point of this constant is to catch a build
# that ships a different / shorter member list, e.g. "only loremaster").
#
# ``lorerunes`` joined in packet 42. Stated without a count, deliberately: a member count
# in prose — or in a test NAME — is the stale-natural-language class this repo pays for
# most often, and this file carried it in both places.
EXPECTED_MEMBERS: tuple[str, ...] = ("loremaster", "loresigil", "lorescribe", "lorerunes")

# The deploy topology binds the project tree read-only at /workspace (design doc
# "In-container run topology"). A member resolving UNDER here = grading the MOUNT = #139.
MOUNT_ROOT = Path("/workspace")

# A NON-default mount root, used to prove mount_root is a real PARAMETER and /workspace
# is not hardcoded. Fixture-value monoculture is this repo's #1 documented defect class,
# so at least one case drives the verdict off a mount root that is NOT the default.
NON_DEFAULT_MOUNT = Path("/mnt/other")

# The two BAKED forms measured on the real image (design doc "Ground truth"): the members
# bake to /app as editable installs OR could resolve into site-packages. BOTH are honest —
# the robust rule is "not under the mount", not "must be site-packages" (the packet's
# original, too-narrow wording, which this fixture pair exists to refute).
BAKED_APP_FILE = "/app/loremaster/loremaster/__init__.py"
BAKED_SITE_PACKAGES_FILE = "/usr/local/lib/python3.14/site-packages/loremaster/__init__.py"

# A member resolving to the read-only mount — the #139 defect, verbatim.
MOUNT_MEMBER_FILE = "/workspace/loremaster/loremaster/__init__.py"

# ---------------------------------------------------------------------------
# PIN 1 (adversary §MISSING-PINS) — the path-containment BOUNDARY. The two shapes below
# are the ONLY fixtures that exercise the ``.resolve()``-then-``is_relative_to`` semantics
# (every other fixture is a clean, already-resolved, non-prefix-colliding path), so without
# them the containment RULE is unpinned and two plausible wrong builds pass 13/13. The two
# module_file VALUES are deliberately DIFFERENT (fixture-monoculture is this repo's #1
# documented defect) and each kills a DIFFERENT wrong build — verified in pure Python:
#   (a) resolves to /workspace/... -> correct REJECT · no-resolve accept · startswith REJECT
#   (b) resolves to /workspace-decoy/... -> correct accept · no-resolve accept · startswith REJECT
#
# (a) A ``__file__`` that RESOLVES under the mount but is spelled non-canonically (a ``..``
#     segment; a symlink would do the same). A build that omits ``.resolve()`` and calls
#     ``is_relative_to`` on the RAW parts (``/``, ``app``, ``..``, ``workspace``, …) judges
#     it "not under /workspace" and ACCEPTS it — the run then grades the :ro mount and
#     conformance passes SILENTLY = the exact #139 defect. This is why the sibling
#     ``scripts/scratch_provenance.py`` resolves first and why #140 exists: ``__file__`` is
#     not trustworthy as written.
NONCANONICAL_MOUNT_FILE = "/app/../workspace/loremaster/loremaster/__init__.py"

# (b) A baked path that merely SHARES the mount-root STRING PREFIX ("/workspace") but is a
#     SIBLING directory, not under the mount. A build that tests
#     ``str(resolved).startswith(str(mount_root))`` REJECTS this honest baked path
#     ("/workspace-decoy".startswith("/workspace") is True) — a false conformance failure on
#     a correct image that pressures an operator to LOOSEN the guard. Containment is a
#     PATH-COMPONENT relation (``is_relative_to``): workspace-decoy is not the workspace dir.
SIBLING_PREFIX_FILE = "/workspace-decoy/loremaster/loremaster/__init__.py"


def _baked(name: str) -> conformance_provenance.MemberProvenance:
    """A MemberProvenance whose ``__file__`` is the member's baked /app editable path."""
    return conformance_provenance.MemberProvenance(
        name=name, module_file=f"/app/{name}/{name}/__init__.py"
    )


# ---------------------------------------------------------------------------
# The VERDICT rule (pure decision — no interpreter/container in the loop).
# ---------------------------------------------------------------------------
class TestVerdictRule:
    """``ConformanceGuard.verdict`` — honest iff ``__file__`` is real AND not under the mount."""

    def test_a_baked_app_editable_file_is_accepted(self) -> None:
        """The MEASURED reality: the members bake to /app as editable installs."""
        guard = conformance_provenance.ConformanceGuard(MOUNT_ROOT)
        member = conformance_provenance.MemberProvenance(
            name="loremaster", module_file=BAKED_APP_FILE
        )
        # Kills the too-narrow "must be site-packages" rule the packet first proposed:
        # the real image bakes to /app, and rejecting it would fail conformance on a
        # correct image.
        assert guard.verdict(member) is None

    def test_a_baked_site_packages_file_is_accepted(self) -> None:
        """A site-packages install is baked too — the rule is "not the mount", not "/app"."""
        guard = conformance_provenance.ConformanceGuard(MOUNT_ROOT)
        member = conformance_provenance.MemberProvenance(
            name="loremaster", module_file=BAKED_SITE_PACKAGES_FILE
        )
        assert guard.verdict(member) is None

    def test_a_workspace_mount_file_is_rejected_and_names_the_mount(self) -> None:
        """THE LOAD-BEARING PIN (#139): a member imported from the :ro mount is REFUSED,
        and the reason NAMES the mount so the operator knows the run graded the source."""
        guard = conformance_provenance.ConformanceGuard(MOUNT_ROOT)
        member = conformance_provenance.MemberProvenance(
            name="loremaster", module_file=MOUNT_MEMBER_FILE
        )

        reason = guard.verdict(member)

        # Kills a verdict that always returns None (accepts everything) — the entire
        # point of the guard is that grading the mount must fail LOUD.
        assert reason is not None
        assert str(MOUNT_ROOT) in reason, "the refusal must name the mount it detected"

    def test_a_noncanonical_mount_path_is_resolved_then_rejected(self) -> None:
        """PIN 1(a) — the LOAD-BEARING boundary (#139/#140): a ``__file__`` that RESOLVES
        under the mount but is spelled with a ``..`` segment MUST be rejected, and the reason
        names the mount.

        Kills the ``no-resolve`` build (``Path(module_file).is_relative_to(mount_root)``
        WITHOUT ``.resolve()``): it reads the raw path parts, judges the path "not under
        /workspace", and ACCEPTS it — the run then grades the :ro mount and conformance passes
        silently (13/13 on the existing fixtures). This is exactly why the sibling
        ``scripts/scratch_provenance.py`` resolves before comparing, and why #140 exists:
        ``__file__`` is not trustworthy as written. Latent in today's clean /app topology but
        reachable the moment any member resolves through a symlink — and unguarded is unguarded.
        """
        guard = conformance_provenance.ConformanceGuard(MOUNT_ROOT)
        member = conformance_provenance.MemberProvenance(
            name="loremaster", module_file=NONCANONICAL_MOUNT_FILE
        )

        reason = guard.verdict(member)

        # NONCANONICAL_MOUNT_FILE resolves to /workspace/loremaster/loremaster/__init__.py
        # (verified in pure Python) — a build that skips .resolve() accepts it. That is #139.
        assert reason is not None, (
            "a path that RESOLVES under the mount must be rejected even when spelled "
            "non-canonically (the guard must .resolve() before comparing — #139/#140)"
        )
        assert str(MOUNT_ROOT) in reason, "the refusal must name the mount it resolved into"

    def test_a_sibling_prefix_path_is_accepted_not_string_prefix_matched(self) -> None:
        """PIN 1(b) — a baked path that only SHARES the mount-root string prefix (a
        ``/workspace-decoy`` sibling) is HONEST and must be accepted.

        Kills the ``startswith`` build (``str(resolved).startswith(str(mount_root))``): a
        string-prefix test REJECTS this honest baked path
        (``/workspace-decoy``.startswith(``/workspace``) is True), failing conformance on a
        correct image (13/13 on the existing fixtures) and pressuring an operator to loosen
        the guard. Containment is a PATH-COMPONENT relation: ``workspace-decoy`` is not the
        ``workspace`` directory, so the correct ``is_relative_to`` rule accepts it.
        """
        guard = conformance_provenance.ConformanceGuard(MOUNT_ROOT)
        member = conformance_provenance.MemberProvenance(
            name="loremaster", module_file=SIBLING_PREFIX_FILE
        )

        # A sibling directory sharing the /workspace prefix is NOT under the mount -> honest.
        assert guard.verdict(member) is None, (
            "a /workspace-decoy sibling shares the /workspace string prefix but is NOT under "
            "the mount; a startswith test would wrongly reject this honest baked path"
        )

    def test_a_namespace_package_none_file_is_rejected(self) -> None:
        """``__file__ is None`` is a FAILURE, not a neutral value.

        A plain install (or a members-less sync) resolves ``import loremaster`` to an
        implicit NAMESPACE PACKAGE — ``__file__ is None`` — loading NONE of the member's
        production code. A guard that only compared paths would skip or crash on it.
        """
        guard = conformance_provenance.ConformanceGuard(MOUNT_ROOT)

        reason = guard.verdict(
            conformance_provenance.MemberProvenance(name="loremaster", module_file=None)
        )

        # Kills a build that treats None as honest (nothing of the member actually loaded).
        assert reason is not None

    def test_an_import_error_is_rejected(self) -> None:
        """A member that will not import at all is a provenance failure, not a skip."""
        guard = conformance_provenance.ConformanceGuard(MOUNT_ROOT)

        reason = guard.verdict(
            conformance_provenance.MemberProvenance(
                name="loresigil",
                import_error="ModuleNotFoundError: No module named 'loresigil'",
            )
        )

        # Kills a build that swallows an import failure and reports honest.
        assert reason is not None

    def test_mount_root_is_a_parameter_not_a_hardcoded_workspace(self) -> None:
        """mount_root drives the verdict: with a NON-default mount, a file under it is
        rejected AND a /workspace file is ACCEPTED (because /workspace is not the mount now).

        This is the fixture-monoculture killer: a build that hardcodes ``/workspace``
        instead of honouring the parameter passes every other test here and dies on this one.
        """
        guard = conformance_provenance.ConformanceGuard(NON_DEFAULT_MOUNT)

        under_the_real_mount = conformance_provenance.MemberProvenance(
            name="loremaster",
            module_file="/mnt/other/loremaster/loremaster/__init__.py",
        )
        a_workspace_file = conformance_provenance.MemberProvenance(
            name="loresigil", module_file=MOUNT_MEMBER_FILE
        )

        assert guard.verdict(under_the_real_mount) is not None, (
            "a file under the CONFIGURED mount root must be rejected"
        )
        assert guard.verdict(a_workspace_file) is None, (
            "with mount_root=/mnt/other, a /workspace path is NOT under the mount and must "
            "be accepted — proving /workspace is not hardcoded"
        )


# ---------------------------------------------------------------------------
# The AUDIT: every member evaluated, every input accounted (totality).
# ---------------------------------------------------------------------------
class TestAudit:
    """``audit`` evaluates ALL members even after a failure, and accounts for each input."""

    def test_audit_evaluates_every_member_and_accounts_for_each_one(self) -> None:
        """One resolver forces every fate at once: honest (loresigil and lorerunes,
        baked), mount-rejected (loremaster), and namespace-rejected (lorescribe).

        The totality assertion (failures + receipts == every member) is the input
        accounting: a build that stops at the first failure, or drops a member, leaves the
        counts short and goes RED. Fate coverage: the honest fate and BOTH reject fates
        each have a member forcing them here.

        The honest fate deliberately carries TWO members rather than one: with a single
        honest member, ``len(receipts)`` and "the honest member" are indistinguishable, so
        a build that returned only the FIRST receipt would pass.
        """
        guard = conformance_provenance.ConformanceGuard(MOUNT_ROOT)
        observed = {
            "loremaster": conformance_provenance.MemberProvenance(
                name="loremaster", module_file=MOUNT_MEMBER_FILE
            ),  # under the mount -> reject
            "loresigil": _baked("loresigil"),  # baked -> honest
            "lorescribe": conformance_provenance.MemberProvenance(
                name="lorescribe", module_file=None
            ),  # namespace package -> reject
            "lorerunes": _baked("lorerunes"),  # baked -> honest
        }

        failures, receipts = guard.audit(lambda name: observed[name])

        # Totality: every input member has exactly one accounted fate (honest OR rejected).
        assert len(failures) + len(receipts) == len(EXPECTED_MEMBERS)
        assert [receipt.name for receipt in receipts] == ["loresigil", "lorerunes"], (
            "exactly the baked members are honest, in member order"
        )
        # Each rejected member is NAMED in a failure — no input vanishes silently.
        assert any("loremaster" in reason for reason in failures), (
            "the mount-grading member must be reported by name"
        )
        assert any("lorescribe" in reason for reason in failures), (
            "the namespace-package member must be reported by name — a build that reports "
            "only the FIRST failure and stops leaves lorescribe unaccounted"
        )

    def test_audit_default_members_cover_every_workspace_member(self) -> None:
        """With no explicit ``members``, audit must evaluate EVERY one (not just loremaster).

        The resolver records every name it is asked for; a build whose default member set
        is short (or is "loremaster only") asks for fewer names and is caught here.
        """
        guard = conformance_provenance.ConformanceGuard(MOUNT_ROOT)
        asked: list[str] = []

        def _resolver(name: str) -> conformance_provenance.MemberProvenance:
            asked.append(name)
            return _baked(name)

        guard.audit(_resolver)

        assert set(asked) == set(EXPECTED_MEMBERS), (
            f"audit must resolve every workspace member by default; asked for {asked}"
        )


# ---------------------------------------------------------------------------
# The module surface: the member constant + the real import_member seam.
# ---------------------------------------------------------------------------
class TestModuleSurface:
    """The exported member list and the real import seam."""

    def test_workspace_members_are_the_uv_workspace_members(self) -> None:
        """The guard must check EVERY member — mirrors [tool.uv.workspace] members.

        Kills a build that only ever looks at ``loremaster`` and ignores its siblings
        (any of which could resolve to the mount independently).

        ⚠ This test and the one above used to carry the member COUNT in their NAMES
        (``..._are_the_three_uv_workspace_members``). Packet 42 added a fourth member and
        the names silently became false while the assertions still passed — a member count
        baked into a test name is the stale-natural-language class this repo pays for most
        often, one layer harder to see than prose. They are count-free now.
        """
        assert tuple(conformance_provenance.WORKSPACE_MEMBERS) == EXPECTED_MEMBERS

    def test_import_member_records_an_import_failure_instead_of_crashing(self) -> None:
        """``import_member`` on an unimportable name returns a record with ``import_error``
        set and ``module_file`` None — it never propagates the ImportError.

        Uses a guaranteed-missing module so the test is deterministic regardless of what is
        installed in the runner's venv (the real members' installed state is env-dependent).
        """
        result = conformance_provenance.import_member("lore_member_that_cannot_exist_xyz")

        assert result.import_error is not None, "an import failure must be captured as a reason"
        assert result.module_file is None


# ---------------------------------------------------------------------------
# The CLI: exit code + a loud, mount-naming headline on failure.
# ---------------------------------------------------------------------------
class TestCli:
    """``main`` audits via the module-level ``import_member`` (monkeypatchable) and exits
    0 when every member is baked, non-zero + loud when one grades the mount."""

    @staticmethod
    def _inject(
        monkeypatch: pytest.MonkeyPatch, mapping: Mapping[str, object]
    ) -> None:
        """Drive the CLI with a fake resolver (no real container / interpreter in the loop)."""
        monkeypatch.setattr(
            conformance_provenance, "import_member", lambda name: mapping[name]
        )

    def test_cli_exits_zero_when_every_member_is_baked(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """THE POSITIVE CONTROL: an all-baked image passes. Without it, the refusal pins
        below could be satisfied by a CLI that always fails."""
        mapping = {name: _baked(name) for name in EXPECTED_MEMBERS}
        self._inject(monkeypatch, mapping)

        exit_code = conformance_provenance.main(["--mount-root", str(MOUNT_ROOT)])

        assert exit_code == 0

    def test_cli_exits_nonzero_and_names_the_mount_on_a_mount_hit(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """One member resolves to the :ro mount -> non-zero exit + a LOUD (stderr) headline
        that NAMES the mount. This is the whole reason the guard exists (#139)."""
        mapping: dict[str, object] = {name: _baked(name) for name in EXPECTED_MEMBERS}
        mapping["loremaster"] = conformance_provenance.MemberProvenance(
            name="loremaster", module_file=MOUNT_MEMBER_FILE
        )
        self._inject(monkeypatch, mapping)

        exit_code = conformance_provenance.main(["--mount-root", str(MOUNT_ROOT)])

        captured = capsys.readouterr()
        combined = captured.out + captured.err
        # Kills a CLI that exits 0 while a member graded the mount (the silent-green defect).
        assert exit_code != 0
        assert str(MOUNT_ROOT) in combined, "the failure output must name the mount"
        assert captured.err.strip(), "the failure must be LOUD on stderr, not a silent code"

    def test_cli_exits_nonzero_on_a_non_mount_failure_namespace_package(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """PIN 2 (adversary §MISSING-PINS) — the CLI exit code is bound to the VERDICT (ANY
        member not honest), NOT to whether the mount was hit.

        A member that loaded NO code — ``__file__ is None`` (a namespace package: a plain or
        members-less sync) with NO mount hit ANYWHERE — MUST fail the run. Kills a ``main``
        whose exit is guarded by the mount fate, e.g.
        ``return 1 if any(str(mount_root) in reason for reason in failures) else 0``: that
        build passes every existing CLI pin (the failure fixture there IS a mount hit) yet
        EXITS 0 here — a genuinely broken image (loremaster imported as an empty namespace
        package, none of its production code loaded) conforms SILENTLY. This is the
        quantifier hole: the outcome "the process fails when ANY member is not honest" must
        hold for ALL rejection causes, and the cause here is deliberately NOT the mount.
        """
        mapping: dict[str, object] = {name: _baked(name) for name in EXPECTED_MEMBERS}
        # loremaster imports as a namespace package: no production code loaded, and NO path
        # under the mount is involved -- a mount-keyed exit would let this pass.
        mapping["loremaster"] = conformance_provenance.MemberProvenance(
            name="loremaster", module_file=None
        )
        self._inject(monkeypatch, mapping)

        exit_code = conformance_provenance.main(["--mount-root", str(MOUNT_ROOT)])

        captured = capsys.readouterr()
        combined = captured.out + captured.err
        assert exit_code != 0, (
            "a member that loaded NO code must fail conformance even with no mount hit — the "
            "CLI exit binds to the verdict, not to the mount fate"
        )
        assert captured.err.strip(), "the failure must be LOUD on stderr, not a silent code"
        # The audit reports each rejected member by name (see TestAudit); main prints those
        # reasons, so the broken member is named. A loud failure that hides WHICH member
        # failed is not loud.
        assert "loremaster" in combined, "the failure output must name the broken member"

    def test_cli_mount_root_flag_is_plumbed_through_not_hardcoded(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The SEAM: ``--mount-root`` must drive the CLI verdict, not just the guard.

        With ``--mount-root /mnt/other``: a member under /mnt/other fails and a member under
        /workspace passes — proving the flag is wired through and /workspace is not baked
        into the CLI.
        """
        mapping: dict[str, object] = {name: _baked(name) for name in EXPECTED_MEMBERS}
        mapping["loremaster"] = conformance_provenance.MemberProvenance(
            name="loremaster", module_file="/mnt/other/loremaster/loremaster/__init__.py"
        )
        mapping["loresigil"] = conformance_provenance.MemberProvenance(
            name="loresigil", module_file=MOUNT_MEMBER_FILE
        )  # a /workspace path is HONEST when the mount is /mnt/other
        self._inject(monkeypatch, mapping)

        exit_code = conformance_provenance.main(["--mount-root", str(NON_DEFAULT_MOUNT)])

        captured = capsys.readouterr()
        combined = captured.out + captured.err
        assert exit_code != 0, "the member under the configured mount root must fail the CLI"
        assert str(NON_DEFAULT_MOUNT) in combined, (
            "the failure must name the CONFIGURED mount root, proving the flag is honoured"
        )
