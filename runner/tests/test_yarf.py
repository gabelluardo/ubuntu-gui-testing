from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ubuntu_gui_testing_runner.yarf import (
    archive_artifacts,
    construct_yarf_command,
    run_test_via_yarf_with_process,
)


def test_construct_yarf_command_without_suite() -> None:
    command = construct_yarf_command("/usr/bin/yarf", "tests/foo", 2000)

    assert command[0] == "/usr/bin/yarf"
    assert "tests/foo" in command
    assert "CID:2000" in command
    assert "--suite" not in command


def test_construct_yarf_command_with_suite() -> None:
    command = construct_yarf_command(
        "/usr/bin/yarf", "tests/foo", 2000, suite="Installer"
    )

    assert "--suite" in command
    assert "Installer" in command


def test_run_test_via_yarf_with_process_sets_env_and_returns_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = MagicMock(spec=subprocess.Popen)
    process.poll.side_effect = [None, 0]
    process.returncode = 0

    popen_calls: list[dict[str, object]] = []

    def fake_popen(command: list[str], env: dict[str, str]) -> MagicMock:  # noqa: ANN001
        popen_calls.append({"command": command, "env": env})
        return process

    monkeypatch.setattr("ubuntu_gui_testing_runner.yarf.subprocess.Popen", fake_popen)
    monkeypatch.setattr("ubuntu_gui_testing_runner.yarf.sleep", lambda _: None)

    returned_process, exit_code = run_test_via_yarf_with_process(
        ["yarf", "tests/foo"], 5907
    )

    assert returned_process is process
    assert exit_code == 0
    env = popen_calls[0]["env"]
    assert isinstance(env, dict)
    assert env["VNC_PORT"] == "7"


def test_archive_artifacts_copies_all_present_paths(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"

    storage = tmp_path / "disk.qcow2"
    storage.write_text("disk", encoding="utf-8")

    tpm_dir = tmp_path / "tpm"
    tpm_dir.mkdir()
    (tpm_dir / "state").write_text("state", encoding="utf-8")

    ovmf_dir = tmp_path / "ovmf"
    ovmf_dir.mkdir()
    (ovmf_dir / "OVMF.fd").write_text("firmware", encoding="utf-8")

    recovery_key = tmp_path / "recovery-key.txt"
    recovery_key.write_text("key", encoding="utf-8")

    archive_artifacts(archive_dir, storage, tpm_dir, ovmf_dir, recovery_key)

    reference = archive_dir / "reference"
    assert (reference / "disk.qcow2").exists()
    assert (reference / "swtpm" / "state").exists()
    assert (reference / "ovmf" / "OVMF.fd").exists()
    assert (reference / "recovery-key.txt").exists()


def test_archive_artifacts_replaces_existing_archive(tmp_path: Path) -> None:
    archive_dir = tmp_path / "archive"
    (archive_dir / "stale").mkdir(parents=True)

    storage = tmp_path / "disk.qcow2"
    storage.write_text("disk", encoding="utf-8")

    archive_artifacts(
        archive_dir,
        storage,
        tmp_path / "missing-tpm",
        None,
        tmp_path / "missing-recovery-key.txt",
    )

    assert not (archive_dir / "stale").exists()
    assert (archive_dir / "reference" / "disk.qcow2").exists()
