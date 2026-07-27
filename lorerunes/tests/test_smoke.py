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

⚠ KNOWN WEAKNESS, recorded rather than silently fixed (packet 42 REFACTOR, 2026-07-27).
Ask the repo's own question — *what WRONG build would this still pass?* — and the answer
is: a `lorerunes` installed as an empty NAMESPACE PACKAGE. That shell imports cleanly
with `__file__ = None` and no production code loaded; it is poison mode 3 of finding
#140, and it is exactly what a plain `uv sync` (without `--all-packages`) produces in a
scratch copy. Asserting on the predicate here instead of on the bare import would close
it. That is a CONTRACT change, not a refactor, so it is flagged in
`REPORT-refactor-pkt42-1.md` for the lead rather than made here.
"""

def test_import() -> None:
    import lorerunes  # noqa: F401
