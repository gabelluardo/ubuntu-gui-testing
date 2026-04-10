from __future__ import annotations

import sys

import pytest

from ubuntu_gui_testing_runner import config


def test_parse_args_required_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "runner",
            "--iso",
            "/tmp/u.iso",
            "--test-suite",
            "tests/desktop-installer/",
        ],
    )

    args = config.parse_args()

    assert args.iso == "/tmp/u.iso"
    assert args.test_suite == "tests/desktop-installer/"
    assert args.cleanup_storage is False
    assert args.tpm is False


def test_parse_args_env_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TEST_USERNAME", "alice")
    monkeypatch.setenv("TEST_PASSWORD", "secret")
    monkeypatch.setattr(
        sys,
        "argv",
        ["runner", "--iso", "/tmp/u.iso", "--test-suite", "tests/foo/"],
    )

    args = config.parse_args()

    assert args.test_username == "alice"
    assert args.test_password == "secret"


def test_parse_args_explicit_credentials_override_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TEST_USERNAME", "alice")
    monkeypatch.setenv("TEST_PASSWORD", "secret")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "runner",
            "--iso",
            "/tmp/u.iso",
            "--test-suite",
            "tests/foo/",
            "--test-username",
            "bob",
            "--test-password",
            "pw",
        ],
    )

    args = config.parse_args()

    assert args.test_username == "bob"
    assert args.test_password == "pw"


def test_parse_args_optional_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "runner",
            "--iso",
            "/tmp/u.iso",
            "--test-suite",
            "tests/foo/",
            "--cleanup-storage",
            "--tpm",
            "--suite",
            "Installer",
            "--disk-path",
            "/tmp/disk.qcow2",
        ],
    )

    args = config.parse_args()

    assert args.cleanup_storage is True
    assert args.tpm is True
    assert args.suite == "Installer"
    assert args.disk_path == "/tmp/disk.qcow2"
