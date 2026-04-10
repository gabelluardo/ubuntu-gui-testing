from __future__ import annotations

import argparse
from pathlib import Path

import pytest


@pytest.fixture
def runner_args(tmp_path: Path) -> argparse.Namespace:
    iso_path = tmp_path / "ubuntu.iso"
    iso_path.touch()

    return argparse.Namespace(
        test_suite="tests/desktop-installer/",
        cleanup_storage=False,
        tpm=False,
        iso=str(iso_path),
        qemu_args_json=str(tmp_path / "qemu-args.json"),
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
