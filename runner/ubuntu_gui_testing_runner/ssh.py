"""SSH remote log collection via paramiko."""

from __future__ import annotations

import socket
from pathlib import Path
from time import sleep

import paramiko

from ubuntu_gui_testing_runner.config import ARTIFACTS_DIR, LOGGER


def collect_installer_logs(
    guest_cid: int, test_username: str, test_password: str
) -> None:
    """Copy installer and journal logs to the artifacts directory."""

    def save_remote_sudo_cmd_output(
        transport: paramiko.Transport, command: str, filename: Path
    ) -> None:
        session = transport.open_session()
        session.invoke_shell()

        sleep(1)
        if session.recv_ready():
            session.recv(len(session.in_buffer))

        session.sendall(f'sudo -p "" -S {command}\n'.encode())
        session.sendall(b"ubuntu\n")
        while not session.recv_ready():
            sleep(0.1)
        with filename.open("wb") as file_handle:
            while session.recv_ready():
                file_handle.write(session.recv(0xFFFF))
        session.close()

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        sock.connect((guest_cid, 22))
        transport = paramiko.Transport(sock)
        transport.connect(
            username=test_username,
            password=test_password,
        )

        save_remote_sudo_cmd_output(
            transport,
            "tar cz -C /var/log/installer .",
            ARTIFACTS_DIR / "installer_logs.tar.gz",
        )
        save_remote_sudo_cmd_output(
            transport,
            "sh -c 'journalctl --no-pager|gzip'",
            ARTIFACTS_DIR / "journal.gz",
        )

        transport.close()
        sock.close()
    except (OSError, paramiko.SSHException) as error:
        LOGGER.error("Could not collect installer logs: %s", error)
