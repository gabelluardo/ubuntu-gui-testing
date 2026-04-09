from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import MagicMock

import pytest

import ubuntu_gui_testing_runner.config as config
from ubuntu_gui_testing_runner.config import RunnerError
from ubuntu_gui_testing_runner.runner import QemuYarfRunner


def _build_args(tmp_path: Path) -> argparse.Namespace:
    iso = tmp_path / "ubuntu.iso"
    iso.touch()
    qemu_json = tmp_path / "qemu-args.json"
    qemu_json.write_text("{}", encoding="utf-8")

    return argparse.Namespace(
        test_suite="tests/desktop-installer/",
        cleanup_storage=False,
        tpm=False,
        iso=str(iso),
        qemu_args_json=str(qemu_json),
        memory="4096M",
        cores="2",
        storage_prefix=None,
        image_disk_size="20G",
        archive_dir=None,
        suite=None,
        disk_path=None,
        test_username="ubuntu",
        test_password="ubuntu",
    )


def test_require_executable_success_and_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.runner.shutil.which",
        lambda name: f"/usr/bin/{name}",
    )
    assert QemuYarfRunner._require_executable("qemu-img") == "/usr/bin/qemu-img"

    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.runner.shutil.which", lambda name: None
    )
    with pytest.raises(RunnerError):
        QemuYarfRunner._require_executable("missing")


def test_init_raises_when_iso_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    args = _build_args(tmp_path)
    args.iso = str(tmp_path / "missing.iso")
    monkeypatch.setattr("ubuntu_gui_testing_runner.runner.parse_args", lambda: args)
    monkeypatch.setattr("ubuntu_gui_testing_runner.runner.get_vnc_port", lambda: 5901)
    monkeypatch.setattr("ubuntu_gui_testing_runner.runner.get_guest_cid", lambda: 1111)

    with pytest.raises(RunnerError):
        QemuYarfRunner()


def test_init_builds_commands(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    args = _build_args(tmp_path)
    disk = tmp_path / "disk.qcow2"

    monkeypatch.setattr("ubuntu_gui_testing_runner.runner.parse_args", lambda: args)
    monkeypatch.setattr("ubuntu_gui_testing_runner.runner.get_vnc_port", lambda: 5905)
    monkeypatch.setattr("ubuntu_gui_testing_runner.runner.get_guest_cid", lambda: 2222)
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.runner.resolve_storage_path", lambda *_: disk
    )
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.runner.construct_qemu_args",
        lambda *_, **__: ["-nographic"],
    )
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.runner.construct_yarf_command",
        lambda *_, **__: ["/usr/bin/yarf", "tests/desktop-installer/"],
    )
    monkeypatch.setattr(
        QemuYarfRunner,
        "_require_executable",
        staticmethod(lambda name: f"/usr/bin/{name}"),
    )

    instance = QemuYarfRunner()

    assert instance.qemu_command[0] == "/usr/bin/qemu-system-x86_64"
    assert "-nographic" in instance.qemu_command
    assert instance.yarf_command[0] == "/usr/bin/yarf"


def test_spawn_vm_invokes_create_disk_and_popen(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    instance = QemuYarfRunner.__new__(QemuYarfRunner)
    instance.storage_path = tmp_path / "disk.qcow2"
    instance.args = argparse.Namespace(image_disk_size="20G")
    instance.qemu_img_path = "/usr/bin/qemu-img"
    instance.qemu_command = ["/usr/bin/qemu-system-x86_64", "-nographic"]

    create_calls: list[tuple[Path, str, str]] = []
    process = MagicMock(spec=subprocess.Popen)

    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.runner.create_disk",
        lambda storage, size, qemu_img: create_calls.append((storage, size, qemu_img)),
    )
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.runner.subprocess.Popen", lambda command: process
    )

    instance.spawn_vm()

    assert create_calls == [(instance.storage_path, "20G", "/usr/bin/qemu-img")]
    assert instance.vm_process is process


def test_run_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    instance = QemuYarfRunner.__new__(QemuYarfRunner)
    instance.args = argparse.Namespace(
        tpm=False,
        test_username="ubuntu",
        test_password="ubuntu",
    )
    instance.vnc_port = 5906
    instance.yarf_command = ["yarf", "tests/foo"]
    instance.guest_cid = 3333

    called: dict[str, object] = {}
    fake_yarf_proc = MagicMock(spec=subprocess.Popen)

    monkeypatch.setattr(instance, "spawn_vm", lambda: called.setdefault("spawn", True))
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.runner.wait_for_vnc_server",
        lambda port: called.setdefault("vnc_port", port),
    )
    monkeypatch.setattr("ubuntu_gui_testing_runner.runner.sleep", lambda _: None)
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.runner.run_test_via_yarf_with_process",
        lambda command, port: (fake_yarf_proc, 0),
    )
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.runner.collect_installer_logs",
        lambda cid, user, password: called.setdefault("logs", (cid, user, password)),
    )

    assert instance.run() == 0
    assert called["spawn"] is True
    assert called["vnc_port"] == 5906
    assert called["logs"] == (3333, "ubuntu", "ubuntu")


def test_exit_cleans_processes_and_temp_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    instance = QemuYarfRunner.__new__(QemuYarfRunner)

    yarf_proc = MagicMock(spec=subprocess.Popen)
    yarf_proc.poll.return_value = None
    vm_proc = MagicMock(spec=subprocess.Popen)
    vm_proc.poll.return_value = None
    swtpm_proc = MagicMock(spec=subprocess.Popen)
    swtpm_proc.poll.return_value = None

    instance.yarf_process = yarf_proc
    instance.vm_process = vm_proc
    instance.swtpm_process = swtpm_proc

    instance.archive_dir = None
    instance.tpm_dir = tmp_path / "tpm"
    instance.ovmf_dir = tmp_path / "ovmf"
    instance.recovery_key_path = tmp_path / "key.txt"

    cleanup_mock = MagicMock()
    instance.tpm_tmp_dir = cast(Any, SimpleNamespace(cleanup=cleanup_mock))

    storage = tmp_path / "disk.qcow2"
    storage.write_text("disk", encoding="utf-8")
    instance.cleanup_storage = True
    instance.storage_path = storage

    prefix_cleanup = MagicMock()
    ovmf_cleanup = MagicMock()
    instance.storage_prefix_tmp_dir = cast(Any, SimpleNamespace(cleanup=prefix_cleanup))
    instance.ovmf_tmp_dir = cast(Any, SimpleNamespace(cleanup=ovmf_cleanup))

    artifacts_dir = tmp_path / "artifacts"
    monkeypatch.setattr(config, "ARTIFACTS_DIR", artifacts_dir)

    monkeypatch.chdir(tmp_path)
    Path("qemu-debug-log").write_text("log", encoding="utf-8")

    instance.__exit__(None, None, None)

    yarf_proc.kill.assert_called_once()
    vm_proc.kill.assert_called_once()
    swtpm_proc.kill.assert_called_once()
    assert not storage.exists()
    cleanup_mock.assert_called_once()
    prefix_cleanup.assert_called_once()
    ovmf_cleanup.assert_called_once()
    assert (artifacts_dir / "qemu-debug-log").exists()
