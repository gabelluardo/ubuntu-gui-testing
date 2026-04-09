"""QEMU VM management and configuration."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from ubuntu_gui_testing_runner.config import LOGGER, OVMF_SOURCE_CANDIDATES, RunnerError


def stage_ovmf_files(ovmf_dir: Path) -> tuple[Path, Path]:
    """Copy system OVMF firmware files into a temporary working directory."""
    for code_source, vars_source in OVMF_SOURCE_CANDIDATES:
        if code_source.exists() and vars_source.exists():
            code_target = ovmf_dir / "OVMF_CODE_4M.ms.fd"
            vars_target = ovmf_dir / "OVMF_VARS_4M.ms.fd"
            shutil.copy2(code_source, code_target)
            shutil.copy2(vars_source, vars_target)
            return code_target, vars_target

    searched = ", ".join(
        f"({code}, {vars_path})" for code, vars_path in OVMF_SOURCE_CANDIDATES
    )
    raise RunnerError(f"No usable OVMF firmware pair found. Checked: {searched}")


def resolve_storage_path(
    disk_path: str | None, storage_prefix: Path, vnc_port: int
) -> Path:
    """Resolve and validate disk path."""
    if disk_path:
        disk = Path(disk_path)
        if disk.suffix != ".qcow2":
            raise RunnerError(
                "Invalid image type for --disk-path: "
                f"{disk}. Only .qcow2 is supported"
            )
        return disk
    return storage_prefix / f"yarf-vm-{vnc_port}.qcow2"


def construct_qemu_args(
    qemu_args_json_file: Path,
    iso_path: Path,
    memory: str,
    cores: str,
    storage_path: Path,
    vnc_port: int,
    guest_cid: int,
    tpm_enabled: bool,
    tpm_socket: Path | None = None,
    ovmf_code_path: Path | None = None,
    ovmf_vars_path: Path | None = None,
) -> list[str]:
    """Build QEMU argument vector from JSON template and runtime values."""
    if not qemu_args_json_file.exists():
        raise RunnerError(
            f"QEMU args file does not exist: {qemu_args_json_file}"
        )

    replacers = {
        "-cdrom": str(iso_path),
        "-m": memory,
        "-smp": cores,
        "-hda": str(storage_path),
        "-vnc": f":{vnc_port - 5900},share=ignore",
    }

    qemu_config = json.loads(qemu_args_json_file.read_text(encoding="utf-8"))
    args: list[str] = []

    for arg, value in qemu_config.items():
        if value is None:
            if arg in replacers:
                args.extend([arg, replacers[arg]])
            else:
                args.append(arg)
        else:
            args.extend([arg, value])

    if tpm_enabled:
        if ovmf_code_path is None or ovmf_vars_path is None or tpm_socket is None:
            raise RunnerError(
                "TPM mode requested but OVMF or socket files are unavailable"
            )
        args.extend(
            [
                "-chardev",
                f"socket,id=chrtpm,path={tpm_socket}",
                "-tpmdev",
                "emulator,id=tpm0,chardev=chrtpm",
                "-device",
                "tpm-tis,tpmdev=tpm0",
                "-drive",
                f"if=pflash,format=raw,unit=0,file={ovmf_code_path},readonly=on",
                "-drive",
                f"if=pflash,format=raw,unit=1,file={ovmf_vars_path}",
                "-machine",
                "q35,smm=on",
                "-netdev",
                "user,id=netdev1",
                "-device",
                "virtio-net-pci,netdev=netdev1,romfile=",
            ]
        )

    args.extend(
        [
            "-device",
            f"vhost-vsock-pci,id=vhost-vsock-pci0,guest-cid={guest_cid}",
        ]
    )
    LOGGER.info("QEMU args: %s", " ".join(args))
    return args


def create_disk(
    storage_path: Path, image_disk_size: str, qemu_img_path: str
) -> None:
    """Create a QCOW2 disk image when one does not already exist."""
    if storage_path.exists():
        return

    storage_path.parent.mkdir(parents=True, exist_ok=True)
    # Safe invocation: executable is resolved by checks(), and args are fixed.
    subprocess.run(  # noqa: S603
        [
            qemu_img_path,
            "create",
            "-f",
            "qcow2",
            str(storage_path),
            image_disk_size,
        ],
        check=True,
    )


def start_swtpm(
    tpm_dir: Path, tpm_socket: Path, swtpm_path: str
) -> subprocess.Popen[bytes]:
    """Start software TPM emulation subprocess."""
    tpm_dir.mkdir(parents=True, exist_ok=True)
    # Safe invocation: executable is resolved by checks(), and args are fixed.
    return subprocess.Popen(  # noqa: S603
        [
            swtpm_path,
            "socket",
            "--tpmstate",
            f"dir={tpm_dir}",
            "--ctrl",
            f"type=unixio,path={tpm_socket}",
            "--tpm2",
        ]
    )
