"""Contract tests for the two framework lifecycle fixes (plan AMENDMENT 1 / D9 §A1.10).

The framework audit flagged two latent defects in the extension lifespan
runners (:meth:`LoreServer.run_startup_hooks` / :meth:`LoreServer.run_shutdown_hooks`).
These tests pin the fixed contract — both are *behavioural*, not cosmetic, and
each is capable of failing on the pre-fix implementation:

**Fix A — startup UNWINDS on partial failure.** If extension ``N``'s
``on_startup`` raises, every already-started extension ``0..N-1`` must have its
``on_shutdown`` run, in REVERSE registration order (last-started, first-stopped),
BEFORE the original error propagates. The half-started extension ``N`` itself is
NOT shut down (its startup never completed). No half-started state may leak: an
extension whose ``on_startup`` succeeded and then was never unwound is the exact
resource-leak the fix closes. The pre-fix runner simply ``await``\\ s each
``on_startup`` in a bare loop, so a raise leaves the prior extensions started —
this test fails on that.

**Fix B — per-extension ``state`` isolation.** Each extension's hooks see ONLY
their own ``state`` namespace. Extension A writing ``ctx.state["k"]`` in its
``on_startup`` must be invisible to extension B's hooks — the pre-fix runner
passes the SAME ``ExtensionContext`` (one shared ``state`` dict) to every
extension, so B would observe A's key (and could clobber it). The fix namespaces
each extension's ``state`` under its own name within the parent context, so the
isolation holds while the parent context still carries every extension's
namespace for the server to inspect.

The doubles here are extension-side fakes (sanctioned): real :class:`Extension`
subclasses with instrumented ``on_startup``/``on_shutdown`` that record the order
of calls and the visibility of cross-extension writes. The behaviour under test
is the SERVER's runner, driven over a real composed :class:`LoreServer`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from _extension_helpers import minimal_config
from loremaster.extension import Extension, ExtensionContext
from loremaster.server import LoreServer


def _config_path(tmp_path: Path, **kwargs: object) -> Path:
    """Write a minimal valid ``lore.yaml`` (no extension slice) to disk."""
    # No ``fake`` extension is registered here, so the extensions block is empty —
    # these tests register their OWN bespoke fakes that declare no config model.
    config = minimal_config(extensions={})
    path = tmp_path / "lore.yaml"
    path.write_text(yaml.safe_dump(config.model_dump(mode="json")), encoding="utf-8")
    return path


class _OrderRecordingExtension(Extension):
    """An extension that appends its name to a shared transcript on each hook.

    The transcript is a list shared across instances (passed in), so a test can
    read the exact order ``on_startup`` / ``on_shutdown`` fired across several
    registered extensions — the only way to prove the reverse-order unwind.
    """

    def __init__(self, name: str, transcript: list[str], *, fail_startup: bool = False) -> None:
        self._name = name
        self._transcript = transcript
        self._fail_startup = fail_startup

    @property
    def name(self) -> str:
        return self._name

    async def on_startup(self, ctx: ExtensionContext) -> None:
        if self._fail_startup:
            self._transcript.append(f"start-raise:{self._name}")
            raise RuntimeError(f"on_startup boom for {self._name}")
        self._transcript.append(f"start:{self._name}")

    async def on_shutdown(self, ctx: ExtensionContext) -> None:
        self._transcript.append(f"stop:{self._name}")


class _StateWritingExtension(Extension):
    """An extension whose ``on_startup`` writes a private key and snapshots what it sees.

    ``seen_keys`` captures the set of keys VISIBLE in ``ctx.state`` at the moment
    this extension's ``on_startup`` runs — the discriminator for fix B: if state
    is shared, a later extension sees an earlier extension's key; if isolated, it
    sees only its own.
    """

    def __init__(self, name: str, write_key: str) -> None:
        self._name = name
        self._write_key = write_key
        self.seen_keys: set[str] = set()

    @property
    def name(self) -> str:
        return self._name

    async def on_startup(self, ctx: ExtensionContext) -> None:
        # Snapshot what is already visible BEFORE writing our own key, so an
        # earlier extension's leaked write would show up here.
        self.seen_keys = set(ctx.state.keys())
        ctx.state[self._write_key] = f"value-from-{self._name}"


class TestStartupUnwindsOnPartialFailure:
    """Fix A: a failing ``on_startup`` unwinds the already-started extensions."""

    @pytest.mark.asyncio
    async def test_failing_startup_runs_prior_shutdowns_in_reverse(
        self, tmp_path: Path
    ) -> None:
        # Three extensions registered a, b, c; c's on_startup raises. a and b
        # started successfully, so they must be shut down in REVERSE order (b then
        # a) before the error propagates. c is NOT shut down (it never completed).
        transcript: list[str] = []
        ext_a = _OrderRecordingExtension("a", transcript)
        ext_b = _OrderRecordingExtension("b", transcript)
        ext_c = _OrderRecordingExtension("c", transcript, fail_startup=True)

        server = (
            LoreServer.from_config(_config_path(tmp_path))
            .register_extension(ext_a)
            .register_extension(ext_b)
            .register_extension(ext_c)
        )
        ctx = server.extension_context(store=object())

        with pytest.raises(RuntimeError, match="boom for c"):
            await server.run_startup_hooks(ctx)

        # a and b started in order; c attempted and raised; then b, a unwound.
        assert transcript == [
            "start:a",
            "start:b",
            "start-raise:c",
            "stop:b",
            "stop:a",
        ]

    @pytest.mark.asyncio
    async def test_first_extension_failing_unwinds_nothing(self, tmp_path: Path) -> None:
        # If the FIRST extension's on_startup raises, no prior extension started,
        # so NO on_shutdown runs — the unwind set is empty, not "all extensions".
        transcript: list[str] = []
        ext_a = _OrderRecordingExtension("a", transcript, fail_startup=True)
        ext_b = _OrderRecordingExtension("b", transcript)

        server = (
            LoreServer.from_config(_config_path(tmp_path))
            .register_extension(ext_a)
            .register_extension(ext_b)
        )
        ctx = server.extension_context(store=object())

        with pytest.raises(RuntimeError, match="boom for a"):
            await server.run_startup_hooks(ctx)

        # a attempted and raised; b never started; nothing unwound.
        assert transcript == ["start-raise:a"]

    @pytest.mark.asyncio
    async def test_clean_startup_runs_no_shutdowns(self, tmp_path: Path) -> None:
        # The happy path: all startups succeed, so the unwind path does NOT fire —
        # no on_shutdown is called by run_startup_hooks.
        transcript: list[str] = []
        ext_a = _OrderRecordingExtension("a", transcript)
        ext_b = _OrderRecordingExtension("b", transcript)

        server = (
            LoreServer.from_config(_config_path(tmp_path))
            .register_extension(ext_a)
            .register_extension(ext_b)
        )
        ctx = server.extension_context(store=object())
        await server.run_startup_hooks(ctx)

        assert transcript == ["start:a", "start:b"]


class TestPerExtensionStateIsolation:
    """Fix B: each extension's ``state`` namespace is private to that extension."""

    @pytest.mark.asyncio
    async def test_one_extension_state_write_is_invisible_to_another(
        self, tmp_path: Path
    ) -> None:
        # Extension a writes ``a_key``; extension b runs after and must NOT see
        # ``a_key`` in its state view (the pre-fix shared dict WOULD leak it).
        ext_a = _StateWritingExtension("a", "a_key")
        ext_b = _StateWritingExtension("b", "b_key")

        server = (
            LoreServer.from_config(_config_path(tmp_path))
            .register_extension(ext_a)
            .register_extension(ext_b)
        )
        ctx = server.extension_context(store=object())
        await server.run_startup_hooks(ctx)

        # b ran after a, yet a's write is invisible to b — isolation holds.
        assert "a_key" not in ext_b.seen_keys
        # Each only ever saw its own (empty at entry, since each writes after the
        # snapshot) — neither leaked into the other.
        assert ext_a.seen_keys == set()
        assert ext_b.seen_keys == set()

    @pytest.mark.asyncio
    async def test_each_extension_state_is_retrievable_under_its_namespace(
        self, tmp_path: Path
    ) -> None:
        # The parent context must still carry every extension's namespace so the
        # server can inspect what an extension stashed — isolation, not loss. The
        # value extension a wrote is reachable under a's namespace; b's under b's.
        ext_a = _StateWritingExtension("a", "a_key")
        ext_b = _StateWritingExtension("b", "b_key")

        server = (
            LoreServer.from_config(_config_path(tmp_path))
            .register_extension(ext_a)
            .register_extension(ext_b)
        )
        ctx = server.extension_context(store=object())
        await server.run_startup_hooks(ctx)

        a_state = server.extension_state(ctx, "a")
        b_state = server.extension_state(ctx, "b")
        assert a_state["a_key"] == "value-from-a"
        assert b_state["b_key"] == "value-from-b"
        # The namespaces are distinct dicts — a write to one is not in the other.
        assert "a_key" not in b_state
        assert "b_key" not in a_state

    @pytest.mark.asyncio
    async def test_shutdown_sees_the_same_per_extension_namespace(
        self, tmp_path: Path
    ) -> None:
        # An extension's on_shutdown must see the SAME private state its on_startup
        # populated (so it can tear down what it set up), and still not see a
        # sibling's. A shutdown-side reader proves the namespace persists across
        # the startup→shutdown boundary for the same extension.
        seen_at_shutdown: dict[str, set[str]] = {}

        class _Recorder(Extension):
            def __init__(self, name: str, write_key: str) -> None:
                self._name = name
                self._write_key = write_key

            @property
            def name(self) -> str:
                return self._name

            async def on_startup(self, ctx: ExtensionContext) -> None:
                ctx.state[self._write_key] = 1

            async def on_shutdown(self, ctx: ExtensionContext) -> None:
                seen_at_shutdown[self._name] = set(ctx.state.keys())

        ext_a = _Recorder("a", "a_key")
        ext_b = _Recorder("b", "b_key")
        server = (
            LoreServer.from_config(_config_path(tmp_path))
            .register_extension(ext_a)
            .register_extension(ext_b)
        )
        ctx = server.extension_context(store=object())
        await server.run_startup_hooks(ctx)
        await server.run_shutdown_hooks(ctx)

        # Each shutdown saw only its own startup-written key.
        assert seen_at_shutdown["a"] == {"a_key"}
        assert seen_at_shutdown["b"] == {"b_key"}
