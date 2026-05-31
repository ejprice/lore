"""The generic, namespace-aware :class:`XmlChunker` and the ``SchemaProfile`` hook.

``XmlChunker`` is the schema-agnostic XML chunker. It parses with ``defusedxml``
(so a hostile document — an XXE external-entity reference or a billion-laughs
entity-expansion bomb — is *refused at parse time*, never expanded), and emits
:class:`~lorescribe.models.Chunk` objects under a **size-tiered** granularity
policy:

* A *small* file (the whole document fits under ``ctx.max_input_tokens``)
  collapses to a single whole-file chunk rooted at the document element.
* A *larger* file splits into one chunk per top-level child element.
* A child that is *still* over the cap is recursed into, one chunk per its own
  children, with a ``tag_path`` breadcrumb header carried in the metadata so the
  embedder retains the element's location in the tree.

Every chunk carries the generic XML metadata block (``root_tag``,
``element_tag``, ``tag_path``, ``id_attr``, ``name_attr``, ``namespaces``,
``attributes``, ``depth``, ``line_range``, ``child_count``) and a per-record
``identity`` of ``id_attr or tag_path``. The identity rule is the load-bearing
one: two sibling elements of the SAME tag carrying different ids get DISTINCT
identities, so they never collapse to one downstream point-ID — the
generalization of odoo-code's ``build_chunk_key`` XML-coarseness bug, designed
out here from day one.

A pluggable :data:`SchemaProfile` rides on top. A profile is any callable
``__call__(element, ctx) -> ProfileResult | None``. For each candidate element
the chunker consults every registered profile in order; the first non-``None``
result wins. Its ``chunk_type`` replaces the generic ``"xml_element"`` and its
``extra_metadata`` merges over (and so can augment, but the generic keys
survive) the generic block. A profile returning ``skip=True`` drops the element
from the output entirely. A profile returning ``force_own_chunk=True`` overrides
the size-tier *granularity*: the claimed element is emitted as its own chunk
even in a small document that would otherwise collapse to a single whole-file
chunk — letting a profile mark an element as semantically significant
regardless of file size. (The token cap still wins the other direction: a
forced element that is itself over the cap is still split for embeddability;
``force_own_chunk`` only overrides collapse-when-small, never split-when-big.)
This is the seam an Odoo-specific (``<record>`` / ``<menuitem>`` /
``<template>``) profile plugs into without the generic core ever importing
anything Odoo-specific.
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ElementTree
from collections.abc import Callable, Sequence
from typing import Any, Protocol, cast

from defusedxml.ElementTree import fromstring as safe_fromstring
from defusedxml.ElementTree import iterparse as safe_iterparse

from lorescribe.base import Chunker
from lorescribe.models import Chunk, ChunkContext, ProfileResult

# The chunk_type stamped on a chunk for which no SchemaProfile fired.
DEFAULT_XML_CHUNK_TYPE: str = "xml_element"

# Maximum element-nesting depth the chunker will accept / descend into. A
# document nested deeper than this is a denial-of-service hazard: serializing or
# walking it recurses in Python and exhausts the interpreter's call stack
# (``RecursionError``, default limit ~1000), crashing the worker — even when the
# document is tiny (a ~7KB, ~1000-deep file is well under the token cap, so no
# split is attempted, yet ``ElementTree.tostring`` alone blows the stack). The
# limit is enforced TWICE: a cheap pre-parse depth gate refuses an over-deep
# document before the first ``tostring`` (see ``_reject_if_too_deep``), and the
# recursive walk stops descending past it (see ``_emit``). 256 is far deeper
# than any legitimate hand- or machine-authored document and leaves a wide
# margin below the interpreter's recursion ceiling. NOTE: we deliberately do NOT
# raise the recursion limit via ``sys.setrecursionlimit`` — that converts a
# catchable ``RecursionError`` into an uncatchable C-stack segfault.
MAX_DEPTH: int = 256

# Metadata flag stamped on a chunk whose subtree was truncated at ``MAX_DEPTH``:
# the chunker stopped descending to avoid the recursion-DoS, so the chunk's
# ``source_text`` may not cover the element's full (over-deep) subtree.
DEPTH_TRUNCATED_METADATA_KEY: str = "depth_truncated"

# The attribute names, in precedence order, the chunker treats as a record's
# stable identifier. The first one present on an element supplies ``id_attr``.
# ``xml:id`` resolves to the Clark-notation form ElementTree stores.
_XML_ID_NAMESPACE_URI: str = "http://www.w3.org/XML/1998/namespace"
ID_ATTR_PRECEDENCE: tuple[str, ...] = (
    "id",
    "name",
    "key",
    f"{{{_XML_ID_NAMESPACE_URI}}}id",
)

# The attribute the chunker surfaces as the human-readable ``name_attr``.
NAME_ATTRIBUTE: str = "name"

# The breadcrumb separator joining tags into a ``tag_path``.
TAG_PATH_SEPARATOR: str = "/"

# The file extension this chunker claims (compared case-insensitively).
XML_EXTENSION: str = ".xml"


class SchemaProfile(Protocol):
    """A per-element hook the :class:`XmlChunker` consults to customise a chunk.

    A profile inspects a single element (and the per-file :class:`ChunkContext`)
    and returns a :class:`~lorescribe.models.ProfileResult` to claim it — a
    custom ``chunk_type``, ``extra_metadata`` merged over the generic block, an
    optional ``skip`` flag, and an optional ``force_own_chunk`` flag that emits
    the element as its own chunk regardless of the size tier — or ``None`` to
    decline, letting the next profile (or the generic default) handle the element.

    Profiles MUST be pure / side-effect-free and idempotent. ``XmlChunker`` may
    consult a profile more than once for the same element (e.g. once to decide
    descent/granularity, again when building the chunk), so a profile that mutates
    external state — counters, caches, logging — would double-fire. Always return
    the same :class:`ProfileResult` for the same ``(element, ctx)``.
    """

    def __call__(self, element: ElementTree.Element, ctx: ChunkContext) -> ProfileResult | None:
        """Claim ``element`` with a :class:`ProfileResult`, or decline with ``None``."""
        ...


# A profile may be supplied either as a class implementing the Protocol or as a
# bare function with the same signature; both are accepted.
ProfileCallable = Callable[[ElementTree.Element, ChunkContext], "ProfileResult | None"]


def _localname(tag: str) -> str:
    """Strip Clark-notation ``{uri}local`` to the bare ``local`` name.

    ElementTree stores a namespaced tag as ``{uri}localname``. Downstream
    consumers want the bare localname (and a separate URI map), so a tag with no
    namespace is returned unchanged and a namespaced one is reduced to the part
    after the closing brace.
    """
    if tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return tag


def _namespace_uri(tag: str) -> str | None:
    """Return the namespace URI embedded in a Clark-notation tag, or ``None``."""
    if tag.startswith("{"):
        return tag[1:].split("}", 1)[0]
    return None


class XmlChunker(Chunker):
    """Generic, namespace-aware, size-tiered XML chunker with a profile hook.

    Args:
        profiles: An ordered sequence of :data:`SchemaProfile` callables. For
            each candidate element the chunker consults them in order and the
            first non-``None`` :class:`ProfileResult` wins. Defaults to no
            profiles (pure generic behaviour).
    """

    def __init__(self, profiles: Sequence[ProfileCallable] | None = None) -> None:
        """Store the registered profiles (empty for pure generic behaviour)."""
        self._profiles: list[ProfileCallable] = list(profiles or [])

    def handles(self, path: str) -> bool:
        """Claim ``.xml`` files (case-insensitively); decline everything else."""
        return path.lower().endswith(XML_EXTENSION)

    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        """Split ``source`` into size-tiered, profile-customised XML chunks.

        Parses with ``defusedxml`` (raising on a hostile entity-bomb / XXE
        document rather than expanding it), then walks the tree under the
        size-tiered policy described in the module docstring.

        Security ordering matters: the cheap, bounded depth gate runs FIRST so a
        recursion-DoS document is refused before any ``ElementTree.tostring`` (the
        operation that actually exhausts the call stack) is attempted.

        Args:
            source: The full XML document text.
            ctx: Per-file context carrying the slug, file path, injected token
                counter, and the embedder's hard token cap.

        Returns:
            The emitted chunks.

        Raises:
            ValueError: If the document nests deeper than :data:`MAX_DEPTH` — a
                denial-of-service hazard refused before serialization.
            Exception: defusedxml raises (e.g. ``EntitiesForbidden`` /
                ``ExternalReferenceForbidden``) on a hostile entity-bomb or XXE
                document — it is never silently expanded.
        """
        # Defense 1 (DoS): refuse an over-deep document up front, BEFORE the
        # first ``tostring``. Uses the defused iterparse so the depth sweep
        # itself can never be turned into an entity-bomb amplifier.
        self._reject_if_too_deep(source)

        # Defense 2 (entity-bomb / XXE): defusedxml refuses to expand internal
        # entity bombs and to resolve external entities — it raises, never
        # expands. (The C expat parse here does not recurse in Python, so it is
        # not itself the recursion-DoS surface.)
        root = safe_fromstring(source)

        # The namespace map (prefix -> URI) is collected once for the whole
        # document so every chunk can carry the same authoritative map.
        namespaces = self._collect_namespaces(source)
        root_tag = _localname(root.tag)

        chunks: list[Chunk] = []
        self._emit(
            element=root,
            ctx=ctx,
            chunks=chunks,
            root_tag=root_tag,
            namespaces=namespaces,
            ancestry=[root_tag],
            depth=0,
        )
        self._assign_sub_ordinals(chunks)
        return chunks

    @staticmethod
    def _assign_sub_ordinals(chunks: list[Chunk]) -> None:
        """Stamp ``sub_ordinal`` so chunks sharing an ``identity`` stay distinct.

        Identity Contract rule (3) — sibling uniqueness: when records legitimately
        share a name (id-less same-tag siblings collapse to the same structural
        ``tag_path`` identity), the within-file natural key would otherwise
        collide downstream and one chunk would silently overwrite the other. The
        first occurrence of each identity keeps ``sub_ordinal == 0``; each
        subsequent occurrence increments, in document order, so every emitted
        chunk's ``(identity, sub_ordinal)`` pair is unique.
        """
        occurrences: dict[str, int] = {}
        for chunk in chunks:
            ordinal = occurrences.get(chunk.identity, 0)
            chunk.sub_ordinal = ordinal
            occurrences[chunk.identity] = ordinal + 1

    def _emit(
        self,
        *,
        element: ElementTree.Element,
        ctx: ChunkContext,
        chunks: list[Chunk],
        root_tag: str,
        namespaces: dict[str, str],
        ancestry: list[str],
        depth: int,
    ) -> None:
        """Recursively emit chunks for ``element`` under the size-tiered policy.

        When ``element`` (serialized) fits the token cap, it becomes a single
        chunk. Otherwise the chunker descends into its children, one chunk per
        child, recursing again into any child that is itself still over the cap.

        Profile-driven granularity overlays the size tiers: if any DIRECT child
        of ``element`` is claimed by a profile with ``force_own_chunk=True``, the
        chunker descends into ``element`` even when it would otherwise fit in a
        single chunk — so the profile-significant children become standalone
        chunks instead of collapsing into the parent. The token cap still wins
        the other direction: ``force_own_chunk`` only overrides the
        collapse-when-small decision, never the split-when-over-cap one, so every
        emitted chunk stays embeddable.

        Args:
            element: The element to (possibly) emit as a chunk.
            ctx: Per-file context (token counter + cap live here).
            chunks: The accumulator the emitted chunks are appended to.
            root_tag: The document root's localname (carried on every chunk).
            namespaces: The document-wide prefix->URI map.
            ancestry: The localname tag-path from the root down to ``element``.
            depth: ``element``'s depth below the root (root == 0).
        """
        source_text = ElementTree.tostring(element, encoding="unicode")
        children = list(element)
        over_cap = ctx.count_tokens(source_text) > ctx.max_input_tokens

        # Defense-in-depth (DoS): never recurse past ``MAX_DEPTH``. The pre-parse
        # gate already refuses documents deeper than this, so in practice the cap
        # is not reached — but if it ever were, descending further would risk the
        # very ``RecursionError`` the gate exists to prevent. Emit the node as-is
        # with a flag noting its subtree was not split, and stop descending.
        if depth >= MAX_DEPTH:
            chunk = self._build_chunk(
                element=element,
                source_text=source_text,
                ctx=ctx,
                root_tag=root_tag,
                namespaces=namespaces,
                ancestry=ancestry,
                depth=depth,
                depth_truncated=True,
            )
            if chunk is not None:
                chunks.append(chunk)
            return

        # Descend when the element is over the cap and still has children to
        # split on. A leaf that is over the cap cannot be split further by tree
        # structure, so it is emitted as-is (the embedder's own caught-422
        # sub-split is the backstop for that rare case).
        size_forces_descent = over_cap and len(children) > 0
        # Profile-driven granularity: descend (even under the cap) so a child a
        # profile claims with ``force_own_chunk=True`` becomes its own chunk
        # rather than collapsing into this parent. Only direct children are
        # consulted; the recursion carries the check to deeper levels.
        profile_forces_descent = len(children) > 0 and any(
            self._child_forces_own_chunk(child, ctx) for child in children
        )
        should_descend = size_forces_descent or profile_forces_descent
        if should_descend:
            for child in children:
                self._emit(
                    element=child,
                    ctx=ctx,
                    chunks=chunks,
                    root_tag=root_tag,
                    namespaces=namespaces,
                    ancestry=[*ancestry, _localname(child.tag)],
                    depth=depth + 1,
                )
            return

        chunk = self._build_chunk(
            element=element,
            source_text=source_text,
            ctx=ctx,
            root_tag=root_tag,
            namespaces=namespaces,
            ancestry=ancestry,
            depth=depth,
        )
        if chunk is not None:
            chunks.append(chunk)

    def _build_chunk(
        self,
        *,
        element: ElementTree.Element,
        source_text: str,
        ctx: ChunkContext,
        root_tag: str,
        namespaces: dict[str, str],
        ancestry: list[str],
        depth: int,
        depth_truncated: bool = False,
    ) -> Chunk | None:
        """Build one :class:`Chunk` for ``element``, applying any profile.

        Args:
            depth_truncated: When ``True`` the recursive walk stopped at
                :data:`MAX_DEPTH` without splitting this element's subtree; a
                metadata flag records that the chunk may not cover the full
                (over-deep) subtree.

        Returns ``None`` when a profile claims the element with ``skip=True``.
        """
        element_tag = _localname(element.tag)
        tag_path = TAG_PATH_SEPARATOR.join(ancestry)
        id_attr = self._id_attr(element)
        name_attr = element.get(NAME_ATTRIBUTE)

        # The generic metadata block. A profile's extra_metadata merges OVER
        # this, so generic keys survive unless a profile deliberately overrides.
        metadata: dict[str, Any] = {
            "root_tag": root_tag,
            "element_tag": element_tag,
            "tag_path": tag_path,
            "id_attr": id_attr,
            "name_attr": name_attr,
            "namespaces": namespaces,
            "attributes": dict(element.attrib),
            "depth": depth,
            "line_range": self._line_range(source_text),
            "child_count": len(list(element)),
            DEPTH_TRUNCATED_METADATA_KEY: depth_truncated,
        }

        chunk_type = DEFAULT_XML_CHUNK_TYPE
        result = self._first_profile_result(element, ctx)
        if result is not None:
            if result.skip:
                return None
            chunk_type = result.chunk_type
            metadata.update(result.extra_metadata)

        # Identity = the record's own id where one exists, else its structural
        # tag-path. This is what keeps same-tag siblings distinct downstream.
        identity = id_attr or tag_path

        # The breadcrumb header gives the embedder the element's location in the
        # tree; empty for the whole-file (root) chunk so no spurious newline.
        metadata_header = f"tag_path: {tag_path}" if depth > 0 else ""

        line_start, line_end = metadata["line_range"]
        return Chunk(
            chunk_type=chunk_type,
            source_text=source_text,
            identity=identity,
            line_start=line_start,
            line_end=line_end,
            metadata=metadata,
            metadata_header=metadata_header,
        )

    def _first_profile_result(
        self, element: ElementTree.Element, ctx: ChunkContext
    ) -> ProfileResult | None:
        """Return the first non-``None`` profile result, or ``None`` if all decline."""
        for profile in self._profiles:
            result = profile(element, ctx)
            if result is not None:
                return result
        return None

    def _child_forces_own_chunk(
        self, element: ElementTree.Element, ctx: ChunkContext
    ) -> bool:
        """Report whether a profile claims ``element`` with ``force_own_chunk``.

        A claimed-and-forced (non-skipped) element must be emitted as its own
        chunk, so its parent has to descend even when it would otherwise fit in a
        single whole-file chunk. A profile that claims the element only to drop
        it (``skip=True``) does not force a descent — there is nothing to emit.
        """
        result = self._first_profile_result(element, ctx)
        return result is not None and result.force_own_chunk and not result.skip

    @staticmethod
    def _id_attr(element: ElementTree.Element) -> str | None:
        """Return the first present id-like attribute value (id|name|key|xml:id)."""
        for attribute in ID_ATTR_PRECEDENCE:
            value = element.get(attribute)
            if value is not None:
                return value
        return None

    @staticmethod
    def _line_range(source_text: str) -> tuple[int, int]:
        """Return a 1-based ``(start, end)`` span for a serialized element.

        ElementTree does not preserve original source offsets through
        ``fromstring``, so the span is reported relative to the serialized
        element text: it always starts at line 1 and ends at its own newline
        count + 1. This keeps the contract (a 1-based ``start <= end`` 2-tuple)
        without inventing offsets the parser never gave us.
        """
        return (1, source_text.count("\n") + 1)

    @staticmethod
    def _collect_namespaces(source: str) -> dict[str, str]:
        """Collect the document's ``prefix -> URI`` namespace declarations.

        Uses the **defused** ``iterparse`` ``start-ns`` events on the raw source,
        which surface every ``xmlns``/``xmlns:prefix`` declaration. The default
        (unprefixed) namespace is keyed by the empty string, matching
        ElementTree's own convention.

        Security: this MUST use ``defusedxml``'s ``iterparse`` (``forbid_entities``
        / ``forbid_external`` on by default), NOT the stdlib one. The stdlib
        parser would expand an entity-bomb / resolve an external entity here; the
        only thing that previously made this path "safe" was the incidental
        ordering of a ``safe_fromstring`` call before it — fragile and not to be
        relied on. The defused parser is self-defending regardless of call order,
        so a hostile payload raises (e.g. ``EntitiesForbidden``) and is never
        expanded. A benign well-formed-but-namespace-free document still parses to
        an empty map; a genuine parse error contributes nothing (``{}``).
        """
        namespaces: dict[str, str] = {}
        try:
            for event, payload in safe_iterparse(
                io.BytesIO(source.encode("utf-8")), events=("start-ns",)
            ):
                if event == "start-ns":
                    # For ``start-ns`` events the payload is a ``(prefix, uri)``
                    # tuple; the typeshed stub only models the common ``Element``
                    # payload, so narrow it explicitly here.
                    prefix, uri = cast("tuple[str, str]", payload)
                    namespaces[prefix] = uri
        except ElementTree.ParseError:
            # A malformed-but-non-hostile sweep contributes nothing. Note we do
            # NOT catch ``defusedxml`` security exceptions (``EntitiesForbidden``,
            # ``ExternalReferenceForbidden``) — those MUST propagate so a hostile
            # document is refused, never silently downgraded to "no namespaces".
            return {}
        return namespaces

    @staticmethod
    def _reject_if_too_deep(source: str) -> None:
        """Refuse a document nested deeper than :data:`MAX_DEPTH` (recursion DoS).

        Streams ``start``/``end`` events through the **defused** ``iterparse``,
        tracking the live nesting depth. The moment the depth exceeds
        :data:`MAX_DEPTH` it raises — bounded work, it never walks the whole
        (potentially huge) tree, and it runs BEFORE any ``ElementTree.tostring``
        (the operation that exhausts the Python call stack). The defused parser
        also means this gate cannot itself be turned into an entity-bomb /
        external-entity amplifier.

        Args:
            source: The full XML document text.

        Raises:
            ValueError: If element nesting exceeds :data:`MAX_DEPTH`.
        """
        depth = 0
        try:
            for event, _element in safe_iterparse(
                io.BytesIO(source.encode("utf-8")), events=("start", "end")
            ):
                if event == "start":
                    depth += 1
                    if depth > MAX_DEPTH:
                        raise ValueError(
                            f"XML nesting depth exceeds the maximum of {MAX_DEPTH}; "
                            "refusing to process (recursion-DoS hazard)."
                        )
                else:  # "end"
                    depth -= 1
        except ElementTree.ParseError:
            # A malformed document is not a depth problem; leave it for the real
            # parse in ``chunk`` (``safe_fromstring``) to report. Security
            # exceptions (``EntitiesForbidden`` / external) are NOT caught here —
            # they propagate so a hostile document is refused at this gate too.
            return
