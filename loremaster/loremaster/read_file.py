"""The ``read_file`` MCP read tool — a tier-aware, containment-guarded span reader.

``read_file(tier, path, line_start, line_end)`` is one half of the Deliverable-3
read-tool surface: an anti-hallucination primitive returning the EXACT on-disk
text of a file span with a ``[SOURCE:...]`` provenance header, so the model
quotes real source rather than recalling it.

It is **tier-aware** (plan AMENDMENT 1 / D8 — tier→location serving):

* a **live** tier (a host checkout the always-on server watches) reads from the
  injected live workspace root for that tier, and
* a **static** tier (community/enterprise/pip/stdlib, materialised under the
  snapshot root) resolves through the merged
  :class:`~loremaster.source.snapshot.SnapshotLayout`.

The security boundary (the C4 containment check) is load-bearing in BOTH
directions and is NEVER reimplemented here: the static path delegates to
:meth:`SnapshotLayout.resolve` (the audited resolver), and the live path applies
the SAME :meth:`SnapshotLayout.contained_path` containment to the live root —
rejecting a ``../`` traversal, an absolute path, or an escaping file/intermediate
symlink (CWE-22 / CWE-59) before any byte is read. A miss — unknown tier, missing
file, traversal, or an out-of-range span — raises :class:`ReadFileError`, never a
partial read and never a path escape.

Line addressing is 1-based and inclusive. ``line_start`` omitted ⇒ the whole
file; ``line_end`` omitted ⇒ to EOF. A ``line_end`` past EOF is clamped (a
tolerant "from line N onward" read); a ``line_start`` past EOF, a non-positive
start, or an inverted span (``end < start``) is a hard error.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from loremaster.source.snapshot import SnapshotLayout

# The provenance-header format the tool stamps on every result: a [SOURCE:...]
# citation the model can echo, naming the tier, the tier-relative path, and the
# resolved 1-based inclusive line span.
_SOURCE_HEADER_TEMPLATE = "[SOURCE:{tier}:{path}:{line_start}-{line_end}]"


class ReadFileError(Exception):
    """Raised on a missing file, unknown tier, traversal, or out-of-range span.

    The message describes the failure (and the offending tier/path/span) without
    ever leaking a resolved absolute path of an escape attempt — the clean-error
    contract: no partial read, no path escape.
    """


class FileSpan(BaseModel):
    """A resolved file span: the exact text plus its provenance.

    Attributes:
        tier: The tier the span was read from.
        path: The tier-relative path that was read.
        line_start: First line (1-based, inclusive) the ``text`` covers.
        line_end: Last line (1-based, inclusive) the ``text`` covers.
        text: The exact on-disk text of the span, byte-for-byte.
    """

    model_config = ConfigDict(extra="forbid")

    tier: str
    path: str
    line_start: int
    line_end: int
    text: str

    @property
    def header(self) -> str:
        """The ``[SOURCE:tier:path:start-end]`` provenance citation for this span."""
        return _SOURCE_HEADER_TEMPLATE.format(
            tier=self.tier,
            path=self.path,
            line_start=self.line_start,
            line_end=self.line_end,
        )

    def render(self) -> str:
        """Render the full tool output: the provenance header, then the span text."""
        return f"{self.header}\n{self.text}"


class ReadFileTool:
    """Tier-aware, containment-guarded file-span reader (dependency-injected).

    Args:
        live_roots: Map of live-tier name → that tier's live workspace root on
            disk (a host checkout the server watches). A tier present here is
            read directly from its root under the C4 containment guard.
        snapshot_layout: The :class:`~loremaster.source.snapshot.SnapshotLayout`
            over the snapshot root; every tier NOT in ``live_roots`` is treated
            as static and resolved through it (reusing its audited C4 resolver).
        known_tiers: The CONFIGURED tier names — used ONLY to disambiguate an
            error: an unknown tier (a typo, not in this set) raises a message that
            LISTS the configured tiers, distinct from a known tier whose file is
            merely missing. The live tiers are always treated as known. ``None``
            ⇒ only the live tiers are known.
    """

    def __init__(
        self,
        *,
        live_roots: dict[str, Path],
        snapshot_layout: SnapshotLayout,
        known_tiers: set[str] | None = None,
    ) -> None:
        self._live_roots = {tier: Path(root) for tier, root in live_roots.items()}
        self._snapshot_layout = snapshot_layout
        # The CONFIGURED tier names — the authority that tells an UNKNOWN tier (a
        # typo) apart from a known tier whose file is merely missing. Defaults to
        # the live tiers (the only tiers a bare tool knows for certain); a live
        # tier is always known. ``None`` ⇒ just the live tiers.
        self._known_tiers: set[str] = set(known_tiers) if known_tiers is not None else set()
        self._known_tiers.update(self._live_roots)

    def read_file(
        self,
        tier: str,
        path: str,
        line_start: int | None = None,
        line_end: int | None = None,
    ) -> FileSpan:
        """Return the requested span of ``(tier, path)`` with a provenance header.

        Resolves ``(tier, path)`` to a SAFE absolute path (live tier → the live
        root under the C4 guard; static tier → :meth:`SnapshotLayout.resolve`),
        reads the file, and slices the 1-based inclusive ``[line_start, line_end]``
        span. ``line_start`` omitted ⇒ from line 1; ``line_end`` omitted ⇒ to EOF.

        Args:
            tier: The tier to read from.
            path: The tier-relative file path.
            line_start: First line (1-based, inclusive); ``None`` ⇒ 1.
            line_end: Last line (1-based, inclusive); ``None`` ⇒ EOF.

        Returns:
            The resolved :class:`FileSpan`.

        Raises:
            ReadFileError: On an unknown tier, a missing file, a containment
                rejection (traversal / escaping symlink / absolute path), or an
                out-of-range / inverted span.
        """
        resolved = self._resolve(tier, path)
        lines = resolved.read_text(encoding="utf-8").splitlines(keepends=True)
        start, end = self._resolve_span(tier, path, len(lines), line_start, line_end)
        text = "".join(lines[start - 1 : end])
        return FileSpan(tier=tier, path=path, line_start=start, line_end=end, text=text)

    def _resolve(self, tier: str, path: str) -> Path:
        """Resolve ``(tier, path)`` to a SAFE, existing absolute path (C4-guarded).

        A live tier is contained against its live root via the SAME
        :meth:`SnapshotLayout.contained_path` the static resolver uses (never a
        reimplementation); a static tier delegates wholesale to
        :meth:`SnapshotLayout.resolve`. The C4 containment behaviour is identical;
        only the FAILURE messaging is disambiguated into three distinct, actionable
        kinds (Item 6):

        * **unknown tier** — ``tier`` is not a configured tier → an error LISTING
          the configured tiers (so a typo is correctable);
        * **containment rejection** — ``path`` is an absolute path, a ``../``
          traversal, or an escaping symlink → its own clear message (the guard
          still BLOCKS it — nothing is served);
        * **missing file** — a known tier and a contained path, but no such file
          → "not found in tier X" with a next step.

        Raises:
            ReadFileError: One of the three disambiguated kinds above.
        """
        if tier not in self._known_tiers:
            raise self._unknown_tier_error(tier)
        live_root = self._live_roots.get(tier)
        if live_root is not None:
            safe = SnapshotLayout.contained_path(live_root, path)
            if safe is None:
                raise self._containment_error(tier, path)
            if not safe.is_file():
                raise self._missing_file_error(tier, path)
            return safe
        # A KNOWN static tier. ``resolve`` returns None for BOTH a containment
        # rejection and a genuine miss; decompose to tell them apart. If NO tier
        # location even yields a contained candidate (every location rejected the
        # path), it is a containment rejection; otherwise the path was contained
        # but no location holds the file — a miss.
        resolved = self._snapshot_layout.resolve(tier, path)
        if resolved is not None and resolved.is_file():
            return resolved
        contained_anywhere = any(
            SnapshotLayout.contained_path(base, path) is not None
            for base in self._snapshot_layout.tier_locations(tier)
        )
        if not contained_anywhere:
            raise self._containment_error(tier, path)
        raise self._missing_file_error(tier, path)

    def _unknown_tier_error(self, tier: str) -> ReadFileError:
        """An unknown-tier error that LISTS the configured tiers (a correctable typo)."""
        valid = ", ".join(repr(name) for name in sorted(self._known_tiers))
        return ReadFileError(
            f"unknown tier {tier!r}; this project's configured tiers are: {valid}. "
            f"Check for a typo — the tier is the first field of a [SOURCE:tier:...] "
            f"citation."
        )

    @staticmethod
    def _missing_file_error(tier: str, path: str) -> ReadFileError:
        """A genuinely-missing-file error naming the tier + a next step (no path leak)."""
        return ReadFileError(
            f"file {path!r} not found in tier {tier!r}. Verify the path (it is "
            f"tier-relative), or run reindex / search_code to locate the current "
            f"file — the index may be ahead of or behind this path."
        )

    @staticmethod
    def _containment_error(tier: str, path: str) -> ReadFileError:
        """A containment-rejection error — its own clear message (never a path leak)."""
        return ReadFileError(
            f"path {path!r} in tier {tier!r} is rejected by the containment guard "
            f"(an absolute path, a '../' traversal, or an escaping symlink). Pass a "
            f"tier-relative path that stays within the tier root."
        )

    @staticmethod
    def _resolve_span(
        tier: str,
        path: str,
        total_lines: int,
        line_start: int | None,
        line_end: int | None,
    ) -> tuple[int, int]:
        """Validate and resolve the 1-based inclusive ``[start, end]`` span.

        ``line_start`` omitted ⇒ 1; ``line_end`` omitted ⇒ ``total_lines`` (EOF).
        A non-positive start, an inverted span, or a start past EOF is a hard
        :class:`ReadFileError`; an end past EOF is CLAMPED to ``total_lines`` (a
        tolerant open-ended read).
        """
        start = 1 if line_start is None else line_start
        if start < 1:
            raise ReadFileError(
                f"line_start must be >= 1 (1-based), got {start} for {tier!r}:{path!r}"
            )
        if start > total_lines:
            raise ReadFileError(
                f"line_start {start} is past end of file "
                f"({total_lines} lines) for {tier!r}:{path!r}"
            )
        end = total_lines if line_end is None else line_end
        if end < start:
            raise ReadFileError(
                f"line_end {end} is before line_start {start} for {tier!r}:{path!r}"
            )
        # An end past EOF is a tolerant "from start onward" read: clamp to EOF.
        end = min(end, total_lines)
        return start, end
