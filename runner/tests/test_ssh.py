from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ubuntu_gui_testing_runner.ssh import collect_installer_logs


def test_collect_installer_logs_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    artifacts_dir = tmp_path / "artifacts"
    monkeypatch.setattr("ubuntu_gui_testing_runner.ssh.ARTIFACTS_DIR", artifacts_dir)
    monkeypatch.setattr("ubuntu_gui_testing_runner.ssh.sleep", lambda _: None)

    sock = MagicMock()
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.ssh.socket.socket", lambda *_, **__: sock
    )

    session = MagicMock()
    session.in_buffer = b"prompt"
    session.recv_ready.side_effect = [True, True, True, False, True, True, True, False]
    session.recv.return_value = b"logs"

    transport = MagicMock()
    transport.open_session.return_value = session

    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.ssh.paramiko.Transport",
        lambda passed_sock: transport,
    )

    collect_installer_logs(1001, "ubuntu", "ubuntu")

    transport.connect.assert_called_once_with(username="ubuntu", password="ubuntu")
    assert (artifacts_dir / "installer_logs.tar.gz").exists()
    assert (artifacts_dir / "journal.gz").exists()
    transport.close.assert_called_once()
    sock.close.assert_called_once()


def test_collect_installer_logs_handles_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.ssh.socket.socket",
        lambda *_, **__: (_ for _ in ()).throw(OSError("boom")),
    )
    error_mock = MagicMock()
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.ssh.LOGGER", MagicMock(error=error_mock)
    )

    collect_installer_logs(1001, "ubuntu", "ubuntu")

    error_mock.assert_called_once()
