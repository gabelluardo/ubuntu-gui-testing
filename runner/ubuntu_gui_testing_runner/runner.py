"""Main runner orchestration."""

from __future__ import annotations

import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from time import sleep

from ubuntu_gui_testing_runner.config import LOGGER, RunnerError, parse_args
from ubuntu_gui_testing_runner.qemu import (
    construct_qemu_args,
    create_disk,
    resolve_storage_path,
    stage_ovmf_files,
    start_swtpm,
)
from ubuntu_gui_testing_runner.ssh import collect_installer_logs
from ubuntu_gui_testing_runner.utils import get_guest_cid, get_vnc_port
from ubuntu_gui_testing_runner.vnc import wait_for_vnc_server
from ubuntu_gui_testing_runner.yarf import (
    archive_artifacts,
    construct_yarf_command,
    run_test_via_yarf_with_process,
)


class QemuYarfRunner:
    """Run YARF tests on a QEMU VM with a VNC backend."""

    @staticmethod
    def _require_executable(name: str) -> str:
        """Resolve an executable path or fail fast."""
        path = shutil.which(name)
        if path is None:
            raise RunnerError(f"Missing executable: {name}")
        return path

    def __init__(self) -> None:
        self.args = parse_args()

        self.ovmf_tmp_dir: tempfile.TemporaryDirectory[str] | None = None
        self.ovmf_dir: Path | None = None
        self.ovmf_code_path: Path | None = None
        self.ovmf_vars_path: Path | None = None
        if self.args.tpm:
            self.ovmf_tmp_dir = tempfile.TemporaryDirectory()
            self.ovmf_dir = Path(self.ovmf_tmp_dir.name)
            self.ovmf_code_path, self.ovmf_vars_path = stage_ovmf_files(
                self.ovmf_dir
            )

        self.vnc_port = get_vnc_port()
        self.guest_cid = get_guest_cid()

        self.cleanup_storage = self.args.cleanup_storage
        self.iso_path = Path(self.args.iso)
        if not self.iso_path.is_file():
            raise RunnerError(
                f"ISO path must point to an existing file: {self.iso_path}"
            )
        LOGGER.info("Using ISO: %s", self.iso_path)
        self.archive_dir = (
            Path(self.args.archive_dir) if self.args.archive_dir else None
        )

        # Create temporary directory for VM storage if not explicitly provided
        self.storage_prefix_tmp_dir: tempfile.TemporaryDirectory[str] | None = None
        if self.args.storage_prefix is None:
            self.storage_prefix_tmp_dir = tempfile.TemporaryDirectory()
            self.storage_prefix = Path(self.storage_prefix_tmp_dir.name)
        else:
            self.storage_prefix = Path(self.args.storage_prefix)

        self.storage_path = resolve_storage_path(
            self.args.disk_path, self.storage_prefix, self.vnc_port
        )
        self.recovery_key_path = self.storage_path.with_name(
            self.storage_path.stem + "-recovery-key.txt"
        )

        # swtpm state is ephemeral and stored in a temp directory for local VM runs
        self.tpm_tmp_dir: tempfile.TemporaryDirectory[str] | None = None
        if self.args.tpm:
            self.tpm_tmp_dir = tempfile.TemporaryDirectory()
            self.tpm_dir = (
                Path(self.tpm_tmp_dir.name) / f"swtpm-{self.vnc_port - 5900}"
            )
        else:
            self.tpm_dir = Path()
        self.tpm_socket = self.tpm_dir / "swtpm-sock"

        self.host_arch = platform.machine()
        self.qemu_executable_name = f"qemu-system-{self.host_arch}"
        self.qemu_args_json_file = Path(self.args.qemu_args_json)

        # Resolve required executable paths up front and fail fast if missing.
        self.qemu_path: str = self._require_executable(
            self.qemu_executable_name
        )
        self.qemu_img_path: str = self._require_executable("qemu-img")
        self.swtpm_path: str = self._require_executable("swtpm")
        self.yarf_path: str = self._require_executable("yarf")

        self.qemu_command = [
            self.qemu_path,
            *construct_qemu_args(
                self.qemu_args_json_file,
                self.iso_path,
                self.args.memory,
                self.args.cores,
                self.storage_path,
                self.vnc_port,
                self.guest_cid,
                self.args.tpm,
                self.tpm_socket if self.args.tpm else None,
                self.ovmf_code_path,
                self.ovmf_vars_path,
            ),
        ]
        self.yarf_command = construct_yarf_command(
            self.yarf_path, self.args.test_suite, self.guest_cid, self.args.suite
        )

        self.vm_process: subprocess.Popen[bytes] | None = None
        self.yarf_process: subprocess.Popen[bytes] | None = None
        self.swtpm_process: subprocess.Popen[bytes] | None = None

    def __enter__(self) -> QemuYarfRunner:
        return self

    def __exit__(self, *_: object) -> None:
        from ubuntu_gui_testing_runner.config import ARTIFACTS_DIR

        LOGGER.info("Exiting runner and terminating subprocesses")

        if Path("qemu-debug-log").exists():
            ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
            shutil.move("qemu-debug-log", ARTIFACTS_DIR / "qemu-debug-log")

        for proc in [self.yarf_process, self.vm_process, self.swtpm_process]:
            if proc and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()

        if self.archive_dir:
            archive_artifacts(
                self.archive_dir,
                self.storage_path,
                self.tpm_dir,
                self.ovmf_dir,
                self.recovery_key_path,
            )

        if self.tpm_tmp_dir:
            self.tpm_tmp_dir.cleanup()

        if self.cleanup_storage and self.storage_path.exists():
            self.storage_path.unlink()

        if self.storage_prefix_tmp_dir:
            self.storage_prefix_tmp_dir.cleanup()

        if self.ovmf_tmp_dir:
            self.ovmf_tmp_dir.cleanup()

    def spawn_vm(self) -> None:
        """Spawn QEMU VM subprocess."""
        create_disk(
            self.storage_path, self.args.image_disk_size, self.qemu_img_path
        )
        LOGGER.info("Spinning up QEMU VM")
        LOGGER.debug("QEMU command line: %s", " ".join(self.qemu_command))
        # Safe invocation: command is built from fixed flags and
        # validated executable paths.
        self.vm_process = subprocess.Popen(self.qemu_command)  # noqa: S603

    def run(self) -> int:
        """Run the full lifecycle: start VM, execute tests, and return exit code."""
        if self.args.tpm:
            self.swtpm_process = start_swtpm(
                self.tpm_dir, self.tpm_socket, self.swtpm_path
            )
            sleep(2)

        self.spawn_vm()
        wait_for_vnc_server(self.vnc_port)
        sleep(5)
        self.yarf_process, result = run_test_via_yarf_with_process(
            self.yarf_command, self.vnc_port
        )
        collect_installer_logs(
            self.guest_cid, self.args.test_username, self.args.test_password
        )
        return result
