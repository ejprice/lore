from pathlib import Path

target = Path("/home/ejprice/PycharmProjects/lore/loremaster/loremaster/server.py")
text = target.read_text(encoding="utf-8")

# --- Edit 1: module-level constants naming the yaml identifiers the wiring reads.
anchor_consts = '_JS_SUFFIXES: tuple[str, ...] = (".js",)\n'
consts_block = anchor_consts + (
    "\n"
    "# The ``lore.yaml`` ``chunkers`` block projects onto the registry's override\n"
    "# seam: each ENTRY is ``extension -> inner mapping`` and the boot wiring reads\n"
    "# ONLY the inner ``chunker`` key naming a registered chunker (permissive-ignore\n"
    "# -- extra inner keys are tolerated). Both names are the operator-facing yaml\n"
    "# identifiers the loud-failure messages must cite so a fix is a one-step edit.\n"
    "_CHUNKERS_CONFIG_FIELD: str = \"chunkers\"\n"
    "_CHUNKER_INNER_KEY: str = \"chunker\"\n"
)
assert text.count(anchor_consts) == 1, "consts anchor not unique"
text = text.replace(anchor_consts, consts_block, 1)

# --- Edit 2: call the wiring in __init__ AFTER the default registry is built.
anchor_call = "        self._registry = ChunkerRegistry()\n        self._build_default_registry()\n"
call_block = (
    "        self._registry = ChunkerRegistry()\n"
    "        self._build_default_registry()\n"
    "        # Route the ``lore.yaml`` ``chunkers`` block onto the now-populated\n"
    "        # registry: ordering matters -- the override targets (e.g. ``python_ast``)\n"
    "        # only exist AFTER ``_build_default_registry()``, so the wiring runs last.\n"
    "        self._apply_config_chunker_overrides()\n"
)
assert text.count(anchor_call) == 1, "init call anchor not unique"
text = text.replace(anchor_call, call_block, 1)

# --- Edit 3: the private helper, placed after ``_claim_suffixes`` in construction.
anchor_helper = (
    '    def _claim_suffixes(self, key: str, suffixes: Iterable[str]) -> None:\n'
    '        """Record ``key`` as the owner of each suffix (for the nit-1 guard)."""\n'
    '        for suffix in suffixes:\n'
    '            self._suffix_owner[suffix.lower()] = key\n'
)
helper_block = anchor_helper + (
    "\n"
    "    def _apply_config_chunker_overrides(self) -> None:\n"
    '        """Project ``config.chunkers`` onto the registry\'s ``apply_overrides`` seam.\n'
    "\n"
    "        The ``lore.yaml`` ``chunkers`` block maps a file extension to an inner\n"
    "        mapping carrying a ``chunker`` key that names an already-registered\n"
    "        chunker. This projects each entry to ``{extension: inner[\"chunker\"]}`` and\n"
    "        hands the WHOLE batch to :meth:`ChunkerRegistry.apply_overrides` in a\n"
    "        single call, so its two-pass validation gives all-or-nothing atomicity (a\n"
    "        single bad target leaves the routing table untouched). Only ``chunker`` is\n"
    "        read; any extra inner keys are tolerated and ignored (permissive-ignore),\n"
    "        and the source mappings are never mutated (no popping) so the block folds\n"
    "        into the embedding-schema fingerprint verbatim.\n"
    "\n"
    "        An empty block is a no-op. Failures are LOUD at construction:\n"
    "\n"
    "        Raises:\n"
    "            ValueError: If an inner mapping is missing the required ``chunker``\n"
    "                key (message names the extension and the key), or if an override\n"
    "                targets a chunker key that was never registered -- the registry's\n"
    "                ``KeyError`` is wrapped as a ``ValueError`` naming the yaml field,\n"
    "                the offending extension, and the offending key.\n"
    '        """\n'
    "        # Project extension -> inner[\"chunker\"], failing loud on a missing key so\n"
    "        # the operator sees ``chunker`` by name rather than a downstream\n"
    "        # ``None is unregistered`` confusion.\n"
    "        projected_overrides: dict[str, str] = {}\n"
    "        for extension, inner in self._config.chunkers.items():\n"
    "            if _CHUNKER_INNER_KEY not in inner:\n"
    "                raise ValueError(\n"
    "                    f\"config field {_CHUNKERS_CONFIG_FIELD!r} entry for extension \"\n"
    "                    f\"{extension!r} is missing the required {_CHUNKER_INNER_KEY!r} key \"\n"
    "                    f\"naming a registered chunker.\"\n"
    "                )\n"
    "            projected_overrides[extension] = inner[_CHUNKER_INNER_KEY]\n"
    "        # One call for all-or-nothing atomicity. The registry raises a bare\n"
    "        # KeyError on an unregistered target; wrap-and-rename it (precedent:\n"
    "        # ``load_config``, config.py:620) into a ValueError that also cites the yaml\n"
    "        # field the operator edits (the KeyError already names the extension/key).\n"
    "        try:\n"
    "            self._registry.apply_overrides(projected_overrides)\n"
    "        except KeyError as error:\n"
    "            raise ValueError(\n"
    "                f\"config field {_CHUNKERS_CONFIG_FIELD!r}: {error.args[0]}\"\n"
    "            ) from error\n"
)
assert text.count(anchor_helper) == 1, "helper anchor not unique"
text = text.replace(anchor_helper, helper_block, 1)

target.write_text(text, encoding="utf-8")
print("edits applied")
