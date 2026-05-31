"""``python -m loremaster.index`` entrypoint — delegates to the batch-indexer CLI.

Lets the standalone batch indexer (plan AMENDMENT 1 / D6) be invoked as a module
in CI/deploy (``python -m loremaster.index --config lore.yaml [--tier T]``).
"""

from __future__ import annotations

import sys

from loremaster.index.cli import main

if __name__ == "__main__":
    sys.exit(main())
