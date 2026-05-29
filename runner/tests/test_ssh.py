from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from ubuntu_gui_testing_runner.ssh import collect_installer_logs


def test_collects_logs_to_artifacts_directory(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"

    session = MagicMock()
    session.recv_ready.return_value = True
    session.recv.side_effect = [b"installer-tar-data", b"", b"journal-data", b""]

    # recv_ready returns True on first call (data available),
    # then False to end the write loop
    sessions: list[MagicMock] = []

    def make_session() -> MagicMock:
        s = MagicMock()
        ready_sequence = iter([True, True, False])
        s.recv_ready.side_effect = lambda: next(ready_sequence, False)
        s.in_buffer = b""
        sessions.append(s)
        return s

    transport = MagicMock()
    transport.open_session.side_effect = make_session

    mock_sock = MagicMock()

    with (
        patch("socket.socket", return_value=mock_sock),
        patch("paramiko.Transport", return_value=transport),
        patch("ubuntu_gui_testing_runner.ssh.sleep"),
    ):
        sessions[0:] = []  # clear
        # Pre-configure recv data for each session
        collect_installer_logs(
            guest_cid=42,
            test_username="ubuntu",
            test_password="ubuntu",
            artifacts_dir=artifacts_dir,
        )

    # Verify connection was made to the right CID on port 22
    mock_sock.connect.assert_called_once_with((42, 22))

    # Verify transport was authenticated
    transport.connect.assert_called_once_with(
        username="ubuntu", password="ubuntu"
    )

    # Verify artifacts directory was created
    assert artifacts_dir.exists()

    # Verify two remote commands were executed (installer logs + journal)
    assert transport.open_session.call_count == 2


def test_handles_connection_failure_gracefully(
    tmp_path: Path,
) -> None:
    artifacts_dir = tmp_path / "artifacts"

    mock_sock = MagicMock()
    mock_sock.connect.side_effect = OSError("Connection refused")

    with (
        patch("socket.socket", return_value=mock_sock),
        patch("ubuntu_gui_testing_runner.ssh.sleep"),
    ):
        # Should not raise — logs the error instead
        collect_installer_logs(
            guest_cid=42,
            test_username="ubuntu",
            test_password="ubuntu",
            artifacts_dir=artifacts_dir,
        )

    # Socket was cleaned up
    mock_sock.close.assert_called_once()
