"""The :class:`Chunker` abstract base class.

Every concrete chunker satisfies a two-method protocol:

* ``handles(path)`` — does this chunker claim this file?
* ``chunk(source, ctx)`` — split the source into :class:`~lorescribe.models.Chunk`
  objects, using the token counter injected via :class:`~lorescribe.models.ChunkContext`.

``Chunker`` is genuinely abstract: neither it nor a subclass that leaves either
method unimplemented can be instantiated. This prevents half-finished chunkers
from registering. There is no concrete logic at this layer — the abstract
methods exist solely to enforce the protocol on concrete chunkers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from lorescribe.models import Chunk, ChunkContext


class Chunker(ABC):
    """Abstract protocol every concrete chunker must satisfy.

    Subclasses MUST implement both :meth:`handles` and :meth:`chunk`. A subclass
    missing either method remains abstract and cannot be instantiated.
    """

    @abstractmethod
    def handles(self, path: str) -> bool:
        """Report whether this chunker claims the given file path.

        Args:
            path: The on-disk path (or relative path) of a candidate file.

        Returns:
            ``True`` if this chunker is responsible for chunking ``path``,
            otherwise ``False``.
        """
        raise NotImplementedError("concrete chunkers must implement handles()")

    @abstractmethod
    def chunk(self, source: str, ctx: ChunkContext) -> list[Chunk]:
        """Split a source string into chunks.

        Args:
            source: The full text content of the file to chunk.
            ctx: Per-file context carrying the slug, file path, injected token
                counter, and the embedder's hard token cap.

        Returns:
            A list of :class:`~lorescribe.models.Chunk` objects, each carrying a
            non-empty ``identity`` and a ``sub_ordinal`` distinguishing siblings.
        """
        raise NotImplementedError("concrete chunkers must implement chunk()")
