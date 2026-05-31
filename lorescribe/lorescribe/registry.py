"""The :class:`ChunkerRegistry` — filename/extension-to-chunker routing and dispatch.

The registry maps a file to the chunker that handles it and dispatches a source
string to that chunker. Selection follows an explicit precedence so a chunker
keyed on a file's *name* (``pyproject.toml``, ``Dockerfile``, ``Makefile``) — a
case no extension mapping can express — can claim a file, while operator config
keeps the final say where it is given. Contract:

* Dispatch returns the matching chunker's chunks; the registry is a thin router,
  not a re-chunker.
* **Precedence:** (1) a config override for the suffix wins; else (2) the first
  registered chunker whose :meth:`~lorescribe.base.Chunker.handles` predicate
  claims the path wins (registration order); else (3) the default suffix→chunker
  map; else (4) ``[]``.
* An unclaimed file (unknown extension, no predicate match, or a path with no
  extension) returns ``[]`` — NOT an exception — so directory walks skip
  unregistered files silently.
* A config override mapping can re-route an extension to a different registered
  chunker key, and an override wins over BOTH a chunker predicate and the
  default registration. ``apply_overrides`` is all-or-nothing: if any target key
  is unregistered it raises and applies none of the batch.
* Extension matching is case-insensitive (``.PY`` == ``.py``); predicate
  matching is whatever each chunker's ``handles`` decides.
"""

from __future__ import annotations

from pathlib import PurePosixPath

from lorescribe.base import Chunker
from lorescribe.models import Chunk, ChunkContext


def _normalise_extension(extension: str) -> str:
    """Lower-case an extension so matching is case-insensitive.

    A single normalisation point keeps registration, override, and dispatch in
    agreement: every extension is stored and looked up in the same case.
    """
    return extension.lower()


class ChunkerRegistry:
    """Maps file extensions to chunkers and dispatches sources to them.

    Holds chunker registrations keyed by a logical name (``"python"``,
    ``"markdown"``, ...), a mapping of file extension to chunker key, and any
    config overrides layered on top of the default extension mappings.
    """

    def __init__(self) -> None:
        """Initialise an empty registry with no chunkers or extension mappings.

        ``_registration_order`` records the keys in the order they were
        registered so the predicate tier of dispatch consults chunkers
        deterministically (first registered, first asked).
        """
        self._chunkers: dict[str, Chunker] = {}
        self._extensions: dict[str, str] = {}
        # Config overrides are kept SEPARATE from the default suffix map so the
        # override tier can outrank a chunker predicate (an override is the
        # operator's explicit instruction; a predicate is a chunker's own guess).
        self._overrides: dict[str, str] = {}
        self._registration_order: list[str] = []

    def register(self, key: str, chunker: Chunker, extensions: list[str]) -> None:
        """Register a chunker under ``key`` and bind it to ``extensions``.

        Args:
            key: The logical name the chunker is registered under (e.g.
                ``"python"``); override mappings target this key.
            chunker: The concrete :class:`~lorescribe.base.Chunker` instance.
            extensions: The file extensions (including the leading dot, e.g.
                ``[".py"]``) this chunker claims by default. Matching is
                case-insensitive.
        """
        if key not in self._chunkers:
            # Track first-registration order so the predicate dispatch tier asks
            # chunkers deterministically; re-registering a key keeps its slot.
            self._registration_order.append(key)
        self._chunkers[key] = chunker
        # Store extensions normalised so dispatch can look them up case-insensitively.
        for extension in extensions:
            self._extensions[_normalise_extension(extension)] = key

    def apply_overrides(self, overrides: dict[str, str]) -> None:
        """Re-route extensions to different registered chunker keys.

        The batch is applied all-or-nothing: every target key is validated
        against the registered chunkers BEFORE any routing entry is written, so
        a single unknown key leaves the routing table exactly as it was. A
        partial application would leave the registry half-configured with no
        other signal.

        Args:
            overrides: A mapping of file extension (e.g. ``".txt"``) to the
                logical key of an already-registered chunker. Override entries
                win over default registrations.

        Raises:
            KeyError: If any override targets a chunker key that was never
                registered — a config typo must fail loudly rather than silently
                dropping files. Nothing from the batch is applied in that case.
        """
        # First pass: validate the WHOLE batch before mutating any routing, so a
        # single unknown target key leaves the table exactly as it was.
        for extension, key in overrides.items():
            if key not in self._chunkers:
                raise KeyError(
                    f"override for extension {extension!r} targets unregistered chunker key {key!r}"
                )
        # Second pass: every target key is valid — only now record the overrides.
        # They live in their own map (consulted first by ``dispatch_file``) so an
        # explicit override beats both a chunker predicate and the default suffix.
        for extension, key in overrides.items():
            self._overrides[_normalise_extension(extension)] = key

    def dispatch_file(self, path: str, source: str, ctx: ChunkContext) -> list[Chunk]:
        """Route ``source`` to the chunker that claims ``path``.

        Selection follows an explicit precedence so a chunker keyed on a file's
        *name* (``pyproject.toml``, ``Dockerfile``, ``Makefile``) — which no
        extension mapping can express — can claim a file, while config-driven
        suffix routing keeps winning where the operator asked for it:

        1. **Config override for the suffix.** An extension re-routed via
           :meth:`apply_overrides` wins outright — operator config is the
           strongest, most explicit signal and must overrule a greedy predicate.
        2. **Predicate / ``handles`` match.** Otherwise the first registered
           chunker (registration order) whose
           :meth:`~lorescribe.base.Chunker.handles` claims ``path`` — EXCLUDING
           the chunker the suffix map already binds to ``path``'s extension,
           which is reached in tier 3 instead. This is the tier that lets a
           basename/pattern-keyed chunker (one owning no suffix) be reached at
           all, without a generic suffix chunker shadowing it.
        3. **Default suffix map.** Otherwise the chunker bound to ``path``'s
           extension by its default registration handles it.
        4. **Unknown -> ``[]``.** If nothing claims the file, return ``[]`` —
           NOT an exception — so directory walks skip unregistered files silently.

        Args:
            path: The file path selecting the chunker. Extension matching is
                case-insensitive; predicate matching is whatever each chunker's
                ``handles`` decides.
            source: The full text content of the file.
            ctx: Per-file context (slug, file path, injected token counter,
                token cap), passed through to the selected chunker.

        Returns:
            The chunks produced by the matching chunker, or ``[]`` if no chunker
            claims the file. Never raises on an unclaimed file.
        """
        # Tier 1: an operator override for this suffix is the strongest signal.
        # ``PurePosixPath.suffix`` yields the trailing extension (incl. the dot)
        # or "" when the path has none; normalise for case-insensitive lookup.
        extension = _normalise_extension(PurePosixPath(path).suffix)
        override_key = self._overrides.get(extension)
        if override_key is not None:
            return self._chunkers[override_key].chunk(source, ctx)

        # Tier 2: a chunker whose predicate claims the path by something OTHER
        # than the path's own suffix mapping. A chunker already bound to this
        # suffix in the default map is a tier-3 citizen — letting it win here
        # would just be the suffix map by another name and would make a generic
        # suffix chunker (whose ``handles`` is itself a suffix test) shadow a
        # more-specific basename claimant. Excluding the suffix-owner keeps tier 2
        # precisely the "claim a file the suffix map would NOT route to me" tier,
        # the basename/pattern use case. Registration order breaks ties.
        suffix_owner = self._extensions.get(extension)
        for key in self._registration_order:
            if key == suffix_owner:
                continue
            if self._chunkers[key].handles(path):
                return self._chunkers[key].chunk(source, ctx)

        # Tier 3: fall back to the default suffix map (already looked up above as
        # ``suffix_owner``).
        if suffix_owner is None:
            # Tier 4: unknown / extension-less path with no predicate match —
            # skip silently so directory walks never crash on an unknown type.
            return []
        return self._chunkers[suffix_owner].chunk(source, ctx)
