from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ubuntu_gui_testing_runner.config import RunnerError
from ubuntu_gui_testing_runner.qemu import (
    construct_qemu_args,
    create_disk,
    resolve_storage_path,
    stage_ovmf_files,
    start_swtpm,
)


def test_stage_ovmf_files_copies_first_valid_pair(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    code_src = tmp_path / "CODE.fd"
    vars_src = tmp_path / "VARS.fd"
    code_src.write_text("code", encoding="utf-8")
    vars_src.write_text("vars", encoding="utf-8")
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.qemu.OVMF_SOURCE_CANDIDATES",
        [(code_src, vars_src)],
    )
    ovmf_dir = tmp_path / "ovmf"
    ovmf_dir.mkdir()

    code_target, vars_target = stage_ovmf_files(ovmf_dir)

    assert code_target.exists()
    assert vars_target.exists()


def test_stage_ovmf_files_raises_when_no_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.qemu.OVMF_SOURCE_CANDIDATES",
        [(Path("/no/code.fd"), Path("/no/vars.fd"))],
    )

    with pytest.raises(RunnerError):
        stage_ovmf_files(Path("/tmp"))


def test_resolve_storage_path_from_disk_path() -> None:
    path = resolve_storage_path("/tmp/vm.qcow2", Path("/tmp"), 5901)
    assert path == Path("/tmp/vm.qcow2")


def test_resolve_storage_path_raises_on_invalid_suffix() -> None:
    with pytest.raises(RunnerError):
        resolve_storage_path("/tmp/vm.raw", Path("/tmp"), 5901)


def test_resolve_storage_path_from_prefix() -> None:
    path = resolve_storage_path(None, Path("/tmp/storage"), 5903)
    assert path == Path("/tmp/storage/yarf-vm-5903.qcow2")


def test_construct_qemu_args_without_tpm(tmp_path: Path) -> None:
    qemu_json = tmp_path / "qemu-args.json"
    qemu_json.write_text(
        json.dumps({"-enable-kvm": None, "-m": None, "-cdrom": None}),
        encoding="utf-8",
    )

    args = construct_qemu_args(
        qemu_json,
        tmp_path / "u.iso",
        "4096M",
        "2",
        tmp_path / "disk.qcow2",
        5902,
        1234,
        False,
    )

    assert "-enable-kvm" in args
    assert "4096M" in args
    assert str(tmp_path / "u.iso") in args
    assert any("guest-cid=1234" in value for value in args)


def test_construct_qemu_args_with_tpm_requires_paths(tmp_path: Path) -> None:
    qemu_json = tmp_path / "qemu-args.json"
    qemu_json.write_text("{}", encoding="utf-8")

    with pytest.raises(RunnerError):
        construct_qemu_args(
            qemu_json,
            tmp_path / "u.iso",
            "4096M",
            "2",
            tmp_path / "disk.qcow2",
            5902,
            1234,
            True,
        )


def test_construct_qemu_args_with_tpm_adds_required_flags(tmp_path: Path) -> None:
    qemu_json = tmp_path / "qemu-args.json"
    qemu_json.write_text("{}", encoding="utf-8")
    tpm_socket = tmp_path / "swtpm.sock"

    args = construct_qemu_args(
        qemu_json,
        tmp_path / "u.iso",
        "4096M",
        "2",
        tmp_path / "disk.qcow2",
        5902,
        1234,
        True,
        tpm_socket=tpm_socket,
        ovmf_code_path=tmp_path / "CODE.fd",
        ovmf_vars_path=tmp_path / "VARS.fd",
    )

    assert "-tpmdev" in args
    assert "-machine" in args
    assert any(str(tpm_socket) in value for value in args)


def test_create_disk_runs_qemu_img(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[list[str]] = []

    def fake_run(command: list[str], check: bool) -> None:
        assert check is True
        calls.append(command)

    monkeypatch.setattr("ubuntu_gui_testing_runner.qemu.subprocess.run", fake_run)

    disk = tmp_path / "images" / "disk.qcow2"
    create_disk(disk, "20G", "/usr/bin/qemu-img")

    assert calls
    assert calls[0][0] == "/usr/bin/qemu-img"
    assert calls[0][-2] == str(disk)


def test_create_disk_skips_if_exists(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fail_run(command: list[str], check: bool) -> None:
        raise AssertionError("subprocess.run should not be called")

    monkeypatch.setattr("ubuntu_gui_testing_runner.qemu.subprocess.run", fail_run)
    disk = tmp_path / "disk.qcow2"
    disk.touch()

    create_disk(disk, "20G", "/usr/bin/qemu-img")


def test_start_swtpm_starts_process(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    process = MagicMock(spec=subprocess.Popen)

    def fake_popen(command: list[str]) -> MagicMock:
        assert command[0] == "/usr/bin/swtpm"
        return process

    monkeypatch.setattr("ubuntu_gui_testing_runner.qemu.subprocess.Popen", fake_popen)

    result = start_swtpm(tmp_path / "state", tmp_path / "sock", "/usr/bin/swtpm")

    assert result is process
