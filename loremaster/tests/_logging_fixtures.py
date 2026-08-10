"""Shared logging-test plumbing — ONE implementation, two contracts.

``test_logging_setup.py`` (the sink/formatter contract, #211) and
``test_secret_leak_vectors.py`` (packet 42's leak-vector contract) both need to
build a real :class:`logging.LogRecord`, snapshot/restore the *global* lore
namespace logger state, and drive an emission through the REAL
``configure_logging`` handler.

Cloning that plumbing into the second file would be copy #2 of a POLICY, not of
trivia (CLAUDE.md, ONE IMPLEMENTATION — "if two call sites need the same policy,
it is a function they call"). The policy is load-bearing twice over:

* the snapshot/restore is what stops one test's handler leaking into the next
  (``configure_logging`` mutates process-global state), and
* :func:`emit_through_configured_logger` is the only honest way to assert what
  actually leaves the process — the pins that drive ``_scrub_text`` directly
  prove a string transform, not a served surface.

Nothing here asserts anything. It is fixture plumbing; the contracts live in the
two test modules that import it.
"""

from __future__ import annotations

import ast
import builtins
import functools
import io
import logging
import sys
import tomllib
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loremaster.logging_setup import LORE_NAMESPACES, configure_logging

# The third-party loggers ``configure_logging`` pins to WARNING. Their state is
# mutated by the same call, so it is restored with the lore namespaces or a
# level change leaks across tests.
SILENCED_THIRD_PARTY: tuple[str, ...] = ("httpx",)

# The namespace whose single handler the emit helper re-points at a buffer, and
# the child logger emissions are made through. Read from the production tuple
# rather than hardcoded, so a namespace rename moves this with it.
EMITTING_NAMESPACE: str = LORE_NAMESPACES[0]


@contextmanager
def restored_lore_logger_state() -> Iterator[None]:
    """Snapshot + restore every logger ``configure_logging`` touches.

    ``configure_logging`` mutates handlers, levels and ``propagate`` on the
    lore-namespace loggers and on the silenced third-party ones. Without a
    restore, a configure in one test leaks its handler into the next — the
    cross-contamination of shared global state the lifecycle rule forbids.
    """
    names = (*LORE_NAMESPACES, *SILENCED_THIRD_PARTY)
    saved: dict[str, tuple[list[logging.Handler], int, bool]] = {}
    for name in names:
        logger = logging.getLogger(name)
        saved[name] = (list(logger.handlers), logger.level, logger.propagate)
    try:
        yield
    finally:
        for name, (handlers, level, propagate) in saved.items():
            logger = logging.getLogger(name)
            logger.handlers = list(handlers)
            logger.setLevel(level)
            logger.propagate = propagate


def make_record(
    *,
    name: str = "loremaster.demo",
    level: int = logging.INFO,
    msg: str = "event.demo",
    extra: dict[str, object] | None = None,
) -> logging.LogRecord:
    """Build a real :class:`logging.LogRecord` with ``extra`` keys attached.

    Mirrors what ``logger.info(msg, extra={...})`` produces: each extra key is
    set as an attribute on the record (exactly how the stdlib threads ``extra``
    through), so a formatter sees the same shape it would in production.

    Args:
        name: The logger name recorded on the record.
        level: The numeric level.
        msg: The event string.
        extra: Caller-supplied fields, attached as record attributes.

    Returns:
        The populated record.
    """
    record = logging.LogRecord(
        name=name,
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )
    for key, value in (extra or {}).items():
        setattr(record, key, value)
    return record


def emit_through_configured_logger(
    fmt: str,
    action: Callable[[logging.Logger], None],
    *,
    child: str = "exc",
    level: str = "DEBUG",
) -> str:
    """Run ``action`` against a REAL configured lore logger; return the stream.

    This is the production path end to end — ``configure_logging`` builds the
    handler, attaches the real formatter and the real
    :class:`~loremaster.logging_setup.RedactingFilter`, and the only substitution
    is the handler's stream. A pin that calls ``_scrub_text`` directly proves a
    string transform; this proves what leaves the process.

    Args:
        fmt: ``"json"`` or ``"keyvalue"``.
        action: Receives the child logger and performs the emission.
        child: Suffix of the child logger name (distinct per test so records
            cannot be attributed to the wrong case).
        level: Minimum level to configure.

    Returns:
        Everything the handler wrote.
    """
    buffer = io.StringIO()
    configure_logging(level=level, fmt=fmt)
    namespace_logger = logging.getLogger(EMITTING_NAMESPACE)
    handler = namespace_logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler), (
        "configure_logging no longer attaches a StreamHandler — this helper "
        "re-points its stream and cannot capture anything else"
    )
    handler.setStream(buffer)
    action(logging.getLogger(f"{EMITTING_NAMESPACE}.{child}"))
    return buffer.getvalue()


# --------------------------------------------------------------------------- #
# THE ONE ROOT LIST THIS PACKET GOVERNS — derived, never hand-written
# --------------------------------------------------------------------------- #
# ⚠ **WHY THIS EXISTS, and it is this packet's EIGHTH instance of one shape.**
# Four scanners across three contract modules each carried a PRIVATE copy of
# "which roots do we govern": the ONE-ENTRY-POINT env gate, the M4 locals gate,
# the R2 function-name corpus, and the auth-holder sibling sweep. When ``lorerunes``
# was minted, ``_SCANNED_MEMBERS`` was widened and **the other four were not** —
# so three gates and one corpus silently stopped covering a workspace member,
# exactly the way the six R32 defects went stale.
#
# That is #102 in my own instruments: four call sites needing the same POLICY
# ("what does this packet govern?") each cloning it. The fix is not to widen four
# lists — it is that they CALL one, and that one is DERIVED from
# ``pyproject.toml`` so a fifth member is covered without anyone remembering.
#
# Proven by mutation: add a member to ``[tool.uv.workspace] members`` and every
# scanner must see it. See ``test_secret_typing`` /
# ``TestEveryScannerSharesOneRootList``.


def workspace_roots(*, include_scripts: bool = True, include_skills: bool = True) -> list[tuple[str, Path]]:
    """Every root this packet's ∀ scanners govern, as ``(label, path)``.

    Workspace members come from ``pyproject.toml``; ``scripts/`` and ``skills/``
    are non-package trees that carry production code and are opted in explicitly
    (``skills/`` is R14's stdlib-only deploy boundary — in scope for scanning,
    exempt from the typed-seam gate, which is a different question).

    A root that does not exist on disk is skipped: in the deployed image
    ``loremaster`` lives in site-packages with no siblings, and the scan simply
    covers less. The receipt that this does not degrade silently in a CHECKOUT is
    ``test_the_scan_reaches_every_workspace_member``.
    """
    import tomllib

    import loremaster

    package_file = loremaster.__file__
    assert package_file is not None, "loremaster imported as an empty namespace package"
    workspace_root = Path(package_file).resolve().parent.parent.parent
    manifest = tomllib.loads((workspace_root / "pyproject.toml").read_text(encoding="utf-8"))
    members: list[str] = manifest["tool"]["uv"]["workspace"]["members"]
    roots: list[tuple[str, Path]] = [
        (member, workspace_root / member / member) for member in sorted(members)
    ]
    if include_scripts:
        roots.append(("scripts", workspace_root / "scripts"))
    if include_skills:
        roots.append(("skills", workspace_root / "skills"))
    return [(label, path) for label, path in roots if path.is_dir()]


def production_sources(
    *, include_scripts: bool = True, include_skills: bool = True
) -> list[tuple[str, Path]]:
    """Every production ``.py`` file under :func:`workspace_roots`.

    Test files and ``tests/`` directories are excluded everywhere — they are not
    production sources, and ``scripts/``/``skills/`` carry theirs inline.
    """
    sources: list[tuple[str, Path]] = []
    for label, root in workspace_roots(include_scripts=include_scripts, include_skills=include_skills):
        sources += [
            (f"{label}/{path.relative_to(root)}", path)
            for path in sorted(root.rglob("*.py"))
            if "tests" not in path.parts and not path.name.startswith("test_")
        ]
    return sources


# ============================================================================ #
# F4 (A-SUB) — the ONE tree parser, the ONE coverage assertion, the L1 runtime
# parse-guard, and the promoted ``_rebind_everywhere``. Contract:
# ``loremaster/tests/test_ast_reach_helpers.py``; design
# ``docs/plans/v2/design/2026-08-09-defect-class-prevention.md`` §3/§9.6/§9.7/§12.
# These consolidate machinery cloned verbatim across ≥14 ∀-scan test files (lore #102 /
# the ONE-IMPLEMENTATION law, one level up).
# ============================================================================ #


def _workspace_root() -> Path:
    """The repo root — where the imported ``loremaster`` package executes FROM (asked of the
    module, never this file's path), exactly as :func:`workspace_roots` derives it."""
    import loremaster  # noqa: PLC0415

    package_file = loremaster.__file__
    assert package_file is not None, "loremaster imported as an empty namespace package"
    return Path(package_file).resolve().parent.parent.parent


def _declared_workspace_members() -> list[str]:
    """``[tool.uv.workspace] members`` read straight from ``pyproject.toml`` — the INDEPENDENT
    oracle every reach assertion reads (never a hand-list, lore #251)."""
    manifest = tomllib.loads((_workspace_root() / "pyproject.toml").read_text(encoding="utf-8"))
    return list(manifest["tool"]["uv"]["workspace"]["members"])


def parse_production_trees(
    *,
    include_scripts: bool = True,
    include_skills: bool = False,
    include_tests: bool = False,
) -> dict[str, ast.Module]:
    """THE ONE tree parser for the ∀-scan family (F4 / design §3 A-SUB).

    Returns ``{repo-relative-posix-path: ast.Module}`` for every ``*.py`` under
    :func:`workspace_roots` (the ``<member>/<member>`` package roots, plus ``scripts``/
    ``skills`` when opted in). ``include_tests=True`` additionally RE-ADDS each declared
    member's ``<member>/tests`` tree — ``workspace_roots`` yields only the package root, which
    structurally EXCLUDES ``<member>/tests`` (§10 R6.3 granularity hazard); without this
    re-add a ``prod-and-tests`` scan silently narrows.

    This is the parser cloned verbatim across ≥14 test files (e.g.
    ``test_anchored_pattern_seam._parse_production_trees``). Consolidating it makes the parse
    ONE implementation (CLAUDE.md, lore #102), so the runtime chokepoint
    (:func:`install_parse_guard`) can certify that no adopter parses the tree privately.
    """
    repo_root = _workspace_root()
    trees: dict[str, ast.Module] = {}
    for _label, root in workspace_roots(include_scripts=include_scripts, include_skills=include_skills):
        for path in sorted(root.rglob("*.py")):
            trees[path.relative_to(repo_root).as_posix()] = ast.parse(path.read_text(encoding="utf-8"))
    if include_tests:
        for member in _declared_workspace_members():
            tests_dir = repo_root / member / "tests"
            if not tests_dir.is_dir():
                continue
            for path in sorted(tests_dir.rglob("*.py")):
                trees[path.relative_to(repo_root).as_posix()] = ast.parse(path.read_text(encoding="utf-8"))
    return trees


def assert_scan_reached_every_member(
    scanned_trees: dict[str, ast.Module], *, extra_roots: tuple[str, ...] = ("scripts",)
) -> None:
    """THE ONE coverage assertion (F4 / design §3): a scan's REACH is a CHECKED VARIABLE.

    ``scanned_packages == declared_members ∪ extra_roots``, with ``declared_members`` read
    INDEPENDENTLY from ``pyproject.toml`` (never ``derived == derived`` — a subject that
    computed its own oracle stays green the day a member stops being scanned, lore #251).
    FAILS CLOSED on an empty scan (registration_sites.py's anti-vacuity: zero sites means the
    scanner is broken, not the tree clean).
    """
    expected = set(_declared_workspace_members()) | set(extra_roots)
    scanned_packages = {key.split("/", 1)[0] for key in scanned_trees}
    assert scanned_packages, (
        "assert_scan_reached_every_member received an EMPTY scan — a guard that green-lights "
        "{} certifies nothing (fail-closed anti-vacuity, registration_sites.py: zero sites "
        "means the scanner is broken, not the tree clean)."
    )
    assert scanned_packages == expected, (
        "a scan's REACH no longer matches the workspace it claims to govern "
        f"(declared members ∪ {sorted(extra_roots)}).\n"
        f"  declared-not-scanned (a member silently EXEMPT from this ∀-scan, lore #251): "
        f"{sorted(expected - scanned_packages)}\n"
        f"  scanned-not-declared (a stale / renamed root): {sorted(scanned_packages - expected)}"
    )


# ---------------------------------------------------------------------------- #
# LAYER 1 — the RUNTIME parse-guard (design §12.3), generalising
# ``_sdk_guard.install`` from the SDK-connection primitive to ``builtins.compile``. A
# private whole-tree parse escapes the sanctioned parser at the ``compile`` chokepoint,
# spelling- AND alias-agnostic (``os.walk``, a comprehension, ``ap = ast.parse`` — all die
# at once, because the check never looks at code).
# ---------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ParseEscape:
    """One ``PyCF_ONLY_AST`` compile made from a workspace ``.py`` SITE with NO
    ``parse_production_trees`` frame above it — a private parse that escaped the sanctioned
    parser (F4 / §12 Layer 1)."""

    site: str  # "<repo-rel>.py:<lineno> in <fn>()"
    primitive: str  # "ast.parse" | "compile"
    member: str  # the workspace member of the compiled SOURCE, or "" if unattributable

    def __str__(self) -> str:
        return f"{self.site} [{self.primitive}] member={self.member!r}"


@dataclass
class ParseGuardReport:
    """What the runtime parse-guard saw during one test — mirrors ``_sdk_guard.GuardReport``
    (F4 / §12.3)."""

    escapes: list[ParseEscape]
    observed: set[str]
    armed: bool
    watched_root: Path | None = None
    intercepted: int = 0

    def require_observations(self, flow: str) -> None:
        """Refuse a clean verdict this report cannot substantiate (#136): raise if the guard
        saw ZERO workspace parses — sanctioned OR escaping — while driving a flow that provably
        parses. "No escapes" having seen nothing is BLINDNESS wearing cleanliness."""
        if self.observed or self.escapes:
            return
        from _sdk_guard import GuardCannotSubstantiate  # noqa: PLC0415  (shared exception type, #136)

        raise GuardCannotSubstantiate(
            f"the parse-guard observed ZERO workspace parses (sanctioned or escaping) while "
            f"{flow} — a flow that provably parses. It intercepted {self.intercepted} "
            f"PyCF_ONLY_AST compile(s) and attributed NONE to a workspace .py site under "
            f"{self.watched_root}. A 'no escapes' verdict here is BLINDNESS, not cleanliness "
            "(finding #136)."
        )


@functools.cache
def _source_to_member_map(watched_root: Path) -> dict[str, str]:
    """``{source-text: member}`` over every workspace ``.py`` — the §12.8.3 escape-record
    extension, keyed by SOURCE TEXT not path: offenders call ``ast.parse(path.read_text())``
    with no ``filename``, so the compiled target is ``<unknown>`` and the member must be
    resolved from the compiled SOURCE. A value is a declared member name, ``"scripts"`` or
    ``"skills"``; a source matching nothing (a synthetic string, or a bytes/normalized source
    — KNOWN BOUND #351) resolves to ``""``."""
    mapping: dict[str, str] = {}
    for label, root in workspace_roots(include_scripts=True, include_skills=True):
        for path in root.rglob("*.py"):
            try:
                mapping[path.read_text(encoding="utf-8")] = label
            except (OSError, UnicodeDecodeError):  # pragma: no cover - unreadable source
                continue
    for member in _declared_workspace_members():
        tests_dir = watched_root / member / "tests"
        if not tests_dir.is_dir():
            continue
        for path in tests_dir.rglob("*.py"):
            try:
                mapping[path.read_text(encoding="utf-8")] = member
            except (OSError, UnicodeDecodeError):  # pragma: no cover - unreadable source
                continue
    return mapping


def _require_parse_root_runs(watched: Path, witness: Any) -> None:
    """Arm-time precondition (#136, mirroring ``_sdk_guard``): the code the guard must judge
    executes UNDER the watched root, else every verdict is vacuous."""
    code = getattr(witness, "__code__", witness)
    executes_from = Path(getattr(code, "co_filename", "")).resolve()
    if executes_from.is_relative_to(watched):
        return
    from _sdk_guard import GuardCannotSubstantiate  # noqa: PLC0415

    name = getattr(witness, "__qualname__", repr(witness))
    raise GuardCannotSubstantiate(
        f"the runtime parse-guard is watching {watched}, but `{name}` — code it must be able "
        f"to see — executes from {executes_from}; no frame of it can match the watched root, "
        "so every verdict would be vacuous (#136). USUAL CAUSE: an out-of-tree copy whose "
        "venv imports loremaster from the original checkout (finding #140)."
    )


def _first_workspace_site(frame: Any, watched: Path) -> str | None:
    """The first frame at or above ``frame`` whose ``co_filename`` is a workspace ``.py``
    (under ``watched``, excluding ``.venv``/``site-packages``) — the CALL SITE, §12.2/§12.3.
    Skips stdlib ``ast.py`` (so an ``ast.parse`` call attributes to the workspace caller, not
    the shim) and the guard's own wrapper (the walk starts at the compile's caller)."""
    current = frame
    while current is not None:
        code = current.f_code
        try:
            path = Path(code.co_filename).resolve()
        except (OSError, ValueError):  # pragma: no cover - synthetic co_filename
            current = current.f_back
            continue
        if (
            path.suffix == ".py"
            and path.is_relative_to(watched)
            and ".venv" not in path.parts
            and "site-packages" not in path.parts
        ):
            return f"{path.relative_to(watched).as_posix()}:{current.f_lineno} in {code.co_name}()"
        current = current.f_back
    return None


def _stack_has_frame(frame: Any, target_code: Any) -> bool:
    """True iff any frame at or above ``frame`` runs ``target_code`` (the sanctioned parser)."""
    current = frame
    while current is not None:
        if current.f_code is target_code:
            return True
        current = current.f_back
    return False


def install_parse_guard(
    monkeypatch: Any, *, watched_root: Path | None = None, witness: Any = None
) -> ParseGuardReport:
    """Arm the RUNTIME parse-guard for the current test (F4 / §12 Layer 1). GENERALISES
    ``_sdk_guard.install`` from the SDK-connection primitive to ``builtins.compile``.

    Wraps ``builtins.compile`` with a PLAIN ``def`` (the stack walk happens at CALL time —
    ``_sdk_guard``'s hard-won lesson). Every ``PyCF_ONLY_AST`` compile made from a workspace
    ``.py`` SITE (the caller frame's ``co_filename``, NOT the compile ``filename`` argument)
    with no ``parse_production_trees`` frame above it is recorded as an ESCAPE — file:line,
    its primitive (``ast.parse``/``compile`` from whether the immediate caller is
    ``ast.parse``), and the MEMBER of the compiled SOURCE. A compile routed THROUGH
    ``parse_production_trees`` is SANCTIONED (``observed``). On this Python (3.14.6) ``ast.parse``
    routes through the wrapped ``builtins.compile`` — VERIFIED, the routing pos-control
    (:meth:`...test_the_routing_verification...`) enshrines it — so wrapping ``compile`` alone
    suffices.

    ``armed=False`` (never raising) before ``parse_production_trees`` exists — the honest
    pre-build posture (``_sdk_guard``'s pre-driver shape)."""
    report = ParseGuardReport(escapes=[], observed=set(), armed=False)
    sanctioned = globals().get("parse_production_trees")
    if sanctioned is None:  # pragma: no cover - the pre-build posture (helper always defined here)
        return report

    watched = (_workspace_root() if watched_root is None else Path(watched_root)).resolve()
    _require_parse_root_runs(watched, sanctioned if witness is None else witness)
    report.watched_root = watched

    sanctioned_code = sanctioned.__code__
    ast_parse_code = ast.parse.__code__
    source_to_member = _source_to_member_map(watched)
    real_compile = builtins.compile

    def _guarded_compile(*args: Any, **kwargs: Any) -> Any:
        # PLAIN ``def``: the stack is walked when compile is CALLED, not later.
        flags = args[3] if len(args) > 3 else kwargs.get("flags", 0)
        if isinstance(flags, int) and (flags & ast.PyCF_ONLY_AST):
            report.intercepted += 1  # every AST compile — the guard's own reach
            caller = sys._getframe(1)  # the frame that called compile
            primitive = "ast.parse" if caller.f_code is ast_parse_code else "compile"
            site = _first_workspace_site(caller, watched)
            if site is not None:
                if _stack_has_frame(caller, sanctioned_code):
                    report.observed.add(site)  # sanctioned — routed through parse_production_trees
                else:
                    source = args[0] if args else kwargs.get("source")
                    member = source_to_member.get(source, "") if isinstance(source, str) else ""
                    report.escapes.append(ParseEscape(site=site, primitive=primitive, member=member))
        return real_compile(*args, **kwargs)

    monkeypatch.setattr(builtins, "compile", _guarded_compile)
    report.armed = True
    return report


# ---------------------------------------------------------------------------- #
# ``_rebind_everywhere`` — PROMOTED here (design §10 #3) from
# ``test_store_seam_one_derivation`` as the shared ≥2-reuser by-identity drop tool
# (F #279 + A-SUB F4). Both route through THIS one, proven by mutation.
# ---------------------------------------------------------------------------- #


@contextmanager
def _rebind_everywhere(real: object, fake: object) -> Iterator[None]:
    """Rebind every module attribute that IS ``real`` to ``fake`` for the duration, found BY
    IDENTITY across ``sys.modules`` — so the mutation reaches a FROM-import adopter (which
    binds the object locally) as well as a module-attribute one; a single-module
    ``monkeypatch`` does NOT (A-SUB-3/-5, lore #279). A caller that stays green under the drop
    never read the shared thing — a private copy wearing the shared name.
    """
    saved: list[tuple[Any, str]] = []
    for module in list(sys.modules.values()):
        try:
            attributes = list(vars(module).items())
        except TypeError:  # a None placeholder or a module without an ordinary __dict__
            continue
        for attribute, value in attributes:
            if value is real:
                saved.append((module, attribute))
    for module, attribute in saved:
        setattr(module, attribute, fake)
    try:
        yield
    finally:
        for module, attribute in saved:
            setattr(module, attribute, real)
