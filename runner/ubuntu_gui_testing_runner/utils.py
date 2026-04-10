"""Utility functions for Ubuntu GUI runner."""

from __future__ import annotations

import secrets
import socket

from ubuntu_gui_testing_runner.config import RunnerError


def get_vnc_port() -> int:
    """Return a free port between 5900 and 5999."""
    ports = list(range(5900, 6000))
    secrets.SystemRandom().shuffle(ports)

    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue

    raise RunnerError("No free ports available for a VNC server")


def get_guest_cid() -> int:
    """Return a random CID for virtio-vsock."""
    return secrets.randbelow(9000) + 1000
