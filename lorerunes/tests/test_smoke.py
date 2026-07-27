"""The `lorerunes` member's own test module — deliberately minimal, deliberately here.

`lorerunes` holds one predicate, and that predicate's SEMANTICS are pinned where its
two callers meet it: `loremaster/tests/test_secret_typing.py` covers every blank shape,
the stdlib-only import bound, and the cross-caller mutation proof that distinguishes
sharing from looks-like-sharing. Duplicating those assertions here would be a second
copy of a contract, which is the class of defect this package exists to prevent.

What is NOT covered anywhere else is the thing below: that `lorerunes/tests` is a real,
COLLECTED directory. It is listed in the root `pyproject.toml`'s `testpaths` as
consequence 4 of adding a workspace member (CLAUDE.md, "`lorerunes` — THE HOME FOR
SHARED CODE"), and a `testpaths` entry that collects nothing is a hope with a filename:
the entry would look like coverage while proving nothing. So this module stays even
though its assertion is weak, and its job is to be COLLECTED.

⚠ THE WEAKNESS THE REFACTOR PHASE FOUND IS NOW CLOSED (contract, 2026-07-27). It asked
the repo's own question — *what WRONG build would this still pass?* — and answered: a
bare `import lorerunes` passes against an empty NAMESPACE PACKAGE, which imports cleanly
with `__file__ = None` and no production code loaded. That is poison mode 3 of finding
#140, and it is exactly what a plain `uv sync` (without `--all-packages`) produces. The
refactorer correctly declined to fix it, because widening a pin is a contract act.

So this module no longer asserts that the NAME resolves. It asserts that the PRODUCTION
CODE is loaded and behaves, which a shell cannot fake.
"""

from lorerunes import is_blank


def test_the_installed_package_is_real_and_not_a_namespace_shell() -> None:
    """The package is INSTALLED, not merely importable as an empty shell.

    Three legs, each closing a different way the weak version passed:

    1. ``__file__`` is not ``None`` — a namespace package has no file (#140 mode 3).
    2. The predicate is importable — a shell exports nothing.
    3. The predicate WORKS — an importable stub that returns ``None`` would satisfy
       both legs above and satisfy nothing that matters.
    """
    import lorerunes

    assert lorerunes.__file__ is not None, (
        "lorerunes imported as an empty NAMESPACE PACKAGE — no production code is loaded. "
        "This is #140 poison mode 3, and a plain `uv sync` without --all-packages produces it."
    )
    assert is_blank("   ") is True
    assert is_blank("not-blank") is False
