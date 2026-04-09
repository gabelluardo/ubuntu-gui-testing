"""YARF test execution and artifact collection."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from time import sleep

from ubuntu_gui_testing_runner.config import ARTIFACTS_DIR, LOGGER


def construct_yarf_command(
    yarf_path: str, test_suite: str, guest_cid: int, suite: str | None = None
) -> list[str]:
    """Build the YARF command."""
    command = [
        yarf_path,
        "--platform=Vnc",
        test_suite,
        "--outdir",
        str(ARTIFACTS_DIR),
        "--",
        "--variable",
        f"CID:{guest_cid}",
    ]
    if suite:
        command.extend(["--suite", suite])
    LOGGER.info("YARF command: %s", command)
    return command


def _run_yarf_process(
    yarf_command: list[str], vnc_port: int
) -> tuple[subprocess.Popen[bytes], int]:
    """Start YARF and poll until it exits; return the process and exit code."""
    mod_env = os.environ.copy()
    mod_env["VNC_PORT"] = str(vnc_port - 5900)

    # Safe invocation: command is built internally from known flags and values.
    yarf_process = subprocess.Popen(yarf_command, env=mod_env)  # noqa: S603
    while yarf_process.poll() is None:
        LOGGER.info("YARF process still running")
        sleep(10)

    LOGGER.info("YARF exited with code %s", yarf_process.returncode)
    return yarf_process, yarf_process.returncode or 0


def run_test_via_yarf(yarf_command: list[str], vnc_port: int) -> int:
    """Run YARF test suite against the spawned VM."""
    _, exit_code = _run_yarf_process(yarf_command, vnc_port)
    return exit_code


def run_test_via_yarf_with_process(
    yarf_command: list[str], vnc_port: int
) -> tuple[subprocess.Popen[bytes], int]:
    """Run YARF test suite and return both process and exit code."""
    return _run_yarf_process(yarf_command, vnc_port)


def archive_artifacts(
    archive_dir: Path,
    storage_path: Path,
    tpm_dir: Path,
    ovmf_dir: Path | None,
    recovery_key_path: Path,
) -> None:
    """Archive disk, TPM state, OVMF vars, and recovery key if available."""
    if archive_dir.exists():
        shutil.rmtree(archive_dir)

    reference_dir = archive_dir / "reference"
    reference_dir.mkdir(parents=True, exist_ok=True)

    if storage_path.exists():
        shutil.copy2(storage_path, reference_dir / storage_path.name)

    if tpm_dir.exists():
        shutil.copytree(tpm_dir, reference_dir / "swtpm")

    if ovmf_dir and ovmf_dir.exists():
        shutil.copytree(ovmf_dir, reference_dir / "ovmf")

    if recovery_key_path.exists():
        shutil.copy2(
            recovery_key_path,
            reference_dir / recovery_key_path.name,
        )
