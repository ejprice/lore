"""conform-sdk3-66 F1 option B (lead ruling #19145): run scripts/restore_prod_dump.py UNEDITED, as a library,
overriding ONLY ``DATABASE_STAMP_FORMAT`` and ``DATABASE_NAME_PATTERN`` to a lowercase stamp in-process, so the
minted DB name is a legal ``loremaster.config.SlugStr`` (finding #525). Every other driver guarantee is the
driver's own code. Pass the driver's argv through, e.g. ``--dump <file> --full`` or ``--reap <name>``.

Run from the repo root: ``uv run python <this file> --dump … --full``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_SCRIPTS = Path("/home/ejprice/PycharmProjects/lore/scripts")
LOWERCASE_STAMP_FORMAT = "%Y%m%dt%H%M%Sz"
LOWERCASE_NAME_PATTERN = re.compile(r"^test_dump_\d{8}t\d{6}z_[0-9a-f]{32}$")

sys.path.insert(0, str(REPO_SCRIPTS))
import restore_prod_dump  # noqa: E402  (path set above; the repo file is not modified)

restore_prod_dump.DATABASE_STAMP_FORMAT = LOWERCASE_STAMP_FORMAT
restore_prod_dump.DATABASE_NAME_PATTERN = LOWERCASE_NAME_PATTERN

if __name__ == "__main__":
    sys.exit(restore_prod_dump.main(sys.argv[1:]))
