from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

from ubuntu_gui_testing_runner.base import _BaseLibvirtRunner


class _FakeRunner(_BaseLibvirtRunner):
    """Minimal concrete subclass for testing _spawn_yarf."""

    def _setup(self) -> None:
        pass

    async def _run_yarf(
        self, suite: str, test: str, vsock_cid: int, vnc_port: int
    ) -> int:
        return 0


def test_yarf_command_includes_suite_and_test() -> None:
    captured_cmd: list[str] = []

    async def fake_exec(*args: str, **kwargs: Any) -> AsyncMock:
        captured_cmd.extend(args)
        return AsyncMock()

    with patch("asyncio.create_subprocess_exec", side_effect=fake_exec):
        runner = _FakeRunner.__new__(_FakeRunner)
        runner.artifacts_path = Path("/artifacts")
        asyncio.run(
            runner._spawn_yarf(
                suite="my-suite",
                test="my-test",
                vnc_port=5902,
                robot_variables={"CID": "3"},
            )
        )

    assert captured_cmd[0] == "yarf"
    assert "my-suite" in captured_cmd
    assert "my-test" in captured_cmd


def test_yarf_command_passes_vsock_cid_as_variable() -> None:
    captured_cmd: list[str] = []

    async def fake_exec(*args: str, **kwargs: Any) -> AsyncMock:
        captured_cmd.extend(args)
        return AsyncMock()

    with patch("asyncio.create_subprocess_exec", side_effect=fake_exec):
        runner = _FakeRunner.__new__(_FakeRunner)
        runner.artifacts_path = Path("/artifacts")
        asyncio.run(
            runner._spawn_yarf(
                suite="suite",
                test="test",
                vnc_port=5901,
                robot_variables={"CID": "99"},
            )
        )

    assert "CID:99" in captured_cmd


def test_yarf_command_passes_extra_variables() -> None:
    captured_cmd: list[str] = []

    async def fake_exec(*args: str, **kwargs: Any) -> AsyncMock:
        captured_cmd.extend(args)
        return AsyncMock()

    with patch("asyncio.create_subprocess_exec", side_effect=fake_exec):
        runner = _FakeRunner.__new__(_FakeRunner)
        runner.artifacts_path = Path("/artifacts")
        asyncio.run(
            runner._spawn_yarf(
                suite="suite",
                test="test",
                vnc_port=5901,
                robot_variables={
                    "CID": "99",
                    "RECOVERY_KEY": "12345-67890-11111-22222-33333-44444-55555-66666",
                },
            )
        )

    assert (
        "RECOVERY_KEY:12345-67890-11111-22222-33333-44444-55555-66666" in captured_cmd
    )


def test_yarf_sets_vnc_port_env_variable() -> None:
    captured_env: dict[str, str] = {}

    async def fake_exec(*args: str, **kwargs: Any) -> AsyncMock:
        env = kwargs.get("env")
        if isinstance(env, dict):
            captured_env.update(env)
        return AsyncMock()

    with patch("asyncio.create_subprocess_exec", side_effect=fake_exec):
        runner = _FakeRunner.__new__(_FakeRunner)
        runner.artifacts_path = Path("/artifacts")
        asyncio.run(
            runner._spawn_yarf(
                suite="suite",
                test="test",
                vnc_port=5902,
                robot_variables={"CID": "3"},
            )
        )

    # VNC port is offset by 5900 (5902 - 5900 = 2)
    assert captured_env["VNC_PORT"] == "2"


def test_yarf_command_uses_configured_artifacts_dir() -> None:
    captured_cmd: list[str] = []

    async def fake_exec(*args: str, **kwargs: Any) -> AsyncMock:
        captured_cmd.extend(args)
        return AsyncMock()

    with patch("asyncio.create_subprocess_exec", side_effect=fake_exec):
        runner = _FakeRunner.__new__(_FakeRunner)
        runner.artifacts_path = Path("/custom/output")
        asyncio.run(
            runner._spawn_yarf(
                suite="suite",
                test="test",
                vnc_port=5901,
                robot_variables={"CID": "3"},
            )
        )

    outdir_idx = captured_cmd.index("--outdir")
    assert captured_cmd[outdir_idx + 1] == "/custom/output"
