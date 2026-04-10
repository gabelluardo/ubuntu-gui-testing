"""Configuration, constants, and argument parsing for Ubuntu GUI runner."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.DEBUG if os.environ.get("DEBUG") else logging.INFO)
LOGGER = logging.getLogger(__name__)

RUNNER_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QEMU_ARGS_JSON = RUNNER_ROOT / "qemu-args.json"
ARTIFACTS_DIR = RUNNER_ROOT / "artifacts"
OVMF_SOURCE_CANDIDATES = [
    (
        Path("/usr/share/OVMF/OVMF_CODE_4M.ms.fd"),
        Path("/usr/share/OVMF/OVMF_VARS_4M.ms.fd"),
    ),
    (
        Path("/usr/share/OVMF/OVMF_CODE.fd"),
        Path("/usr/share/OVMF/OVMF_VARS.fd"),
    ),
    (
        Path("/usr/share/edk2-ovmf/OVMF_CODE.fd"),
        Path("/usr/share/edk2-ovmf/OVMF_VARS.fd"),
    ),
]


class RunnerError(RuntimeError):
    """Raised when the runner cannot proceed due to an unrecoverable error."""


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Spawns a QEMU VM and runs a test suite via YARF. Keys with values set "
            "to null in the JSON config are replaced from script defaults when "
            "available; otherwise, the key is passed to QEMU as a standalone flag."
        )
    )
    parser.add_argument(
        "--test-suite",
        type=str,
        required=True,
        help="Path to test suite directory",
    )
    parser.add_argument(
        "--cleanup-storage",
        action="store_true",
        help="Delete VM storage when test is complete.",
    )
    parser.add_argument(
        "--tpm",
        action="store_true",
        help="Emulate a TPM chip when starting QEMU",
    )
    parser.add_argument(
        "--iso",
        type=str,
        required=True,
        help="Path to an existing local ISO file",
    )
    parser.add_argument(
        "--qemu-args-json",
        type=str,
        required=False,
        default=str(DEFAULT_QEMU_ARGS_JSON),
        help="Path to JSON file containing QEMU args",
    )
    parser.add_argument(
        "--memory",
        type=str,
        required=False,
        default="16384M",
        help="-m in `man qemu-system-$(uname -m)`, default=16384M",
    )
    parser.add_argument(
        "--cores",
        type=str,
        required=False,
        default="8",
        help="-smp in `man qemu-system-$(uname -m)`, default=8",
    )
    parser.add_argument(
        "--storage-prefix",
        type=str,
        required=False,
        default=None,
        help="Directory path to store the VM disk (defaults to a temporary directory)",
    )
    parser.add_argument(
        "--image-disk-size",
        type=str,
        required=False,
        default="40G",
        help="Size of qcow2 disk, default=40G",
    )
    parser.add_argument(
        "--archive-dir",
        type=str,
        required=False,
        default=None,
        help="Directory to store VM artifacts",
    )
    parser.add_argument(
        "--suite",
        type=str,
        required=False,
        default=None,
        help="Specify a specific Robot suite",
    )
    parser.add_argument(
        "--disk-path",
        type=str,
        required=False,
        default=None,
        help="Desired path to VM disk (uses existing disk when present)",
    )
    parser.add_argument(
        "--test-username",
        type=str,
        required=False,
        default=os.environ.get("TEST_USERNAME", "ubuntu"),
        help="Username for test image SSH access (env: TEST_USERNAME)",
    )
    parser.add_argument(
        "--test-password",
        type=str,
        required=False,
        default=os.environ.get("TEST_PASSWORD", "ubuntu"),
        help="Password for test image SSH access (env: TEST_PASSWORD)",
    )
    return parser.parse_args()
