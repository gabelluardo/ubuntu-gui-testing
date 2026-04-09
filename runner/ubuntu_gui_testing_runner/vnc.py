"""VNC server management and connectivity."""

from __future__ import annotations

import socket
from time import sleep, time

from ubuntu_gui_testing_runner.config import LOGGER, RunnerError


def wait_for_vnc_server(vnc_port: int, timeout_seconds: int = 30) -> None:
    """Wait until the VNC TCP endpoint is available."""
    LOGGER.info("Waiting for VNC server on port %s", vnc_port)
    start_time = time()

    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(("127.0.0.1", vnc_port)) == 0:
                return

        if time() - start_time > timeout_seconds:
            raise RunnerError(
                f"Failed to connect to VNC server after {timeout_seconds} seconds"
            )

        sleep(0.5)
