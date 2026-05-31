"""Guard the ``python -m loremaster.server`` entrypoint against def-after-guard bugs.

A production-only ``NameError`` slipped past the entire import-based test suite +
two audits: ``_no_tokenizer`` was defined AFTER the ``if __name__ == "__main__"``
guard in ``server.py``. Run as ``python -m loremaster.server``, the guard fires
``sys.exit(main())`` and ``main()`` blocks in uvicorn, so module execution never
reached the def — the name was unbound in the running process, and ``search_code``
``NameError``'d on the live server. Import-based tests bind every def on import,
so they were blind to it.

This AST check enforces the structural invariant that prevents the whole class:
the ``__main__`` guard is the LAST top-level statement, so nothing runtime-needed
can be orphaned after it.
"""

from __future__ import annotations

import ast
from pathlib import Path

import loremaster.server


def _is_main_guard(node: ast.stmt) -> bool:
    """True if ``node`` is an ``if __name__ == "__main__":`` top-level guard."""
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    left = node.test.left
    return isinstance(left, ast.Name) and left.id == "__name__"


def test_main_guard_is_last_top_level_statement() -> None:
    """The ``__main__`` guard must be the final top-level statement in server.py.

    Anything after it (a def, a module-level binding) does NOT execute when the
    module runs as ``__main__`` (main() blocks first) — the exact shape of the
    search_code NameError this regression-tests against.
    """
    source = Path(loremaster.server.__file__).read_text(encoding="utf-8")
    body = ast.parse(source).body
    guard_positions = [i for i, node in enumerate(body) if _is_main_guard(node)]

    assert guard_positions, "server.py has no `if __name__ == '__main__'` guard"
    assert guard_positions[-1] == len(body) - 1, (
        "the `if __name__ == \"__main__\"` guard must be the LAST top-level "
        "statement in server.py; a def/binding placed after it will not execute "
        "under `python -m loremaster.server` (main() blocks in uvicorn first)."
    )
