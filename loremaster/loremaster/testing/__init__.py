"""Test-support helpers shipped inside the ``loremaster`` package (finding #466).

Lives in the workspace member, not in a ``tests/`` tree, so that BOTH test idioms reach ONE copy:
the workspace ``testpaths`` run and the lore-deploy skill run
(``cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests``). A policy two trees
need is a module they import, never a pattern each clones (CLAUDE.md, ONE IMPLEMENTATION).

Modules:
    :mod:`loremaster.testing.loopback` — the race-free loopback listener and server-start helper.
"""
