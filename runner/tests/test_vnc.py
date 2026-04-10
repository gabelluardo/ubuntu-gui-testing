from __future__ import annotations

import pytest

from ubuntu_gui_testing_runner.config import RunnerError
from ubuntu_gui_testing_runner.vnc import wait_for_vnc_server


class _ConnectSocket:
    def __init__(self, responses: list[int]) -> None:
        self._responses = responses

    def __enter__(self) -> _ConnectSocket:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return

    def connect_ex(self, address: tuple[str, int]) -> int:
        _ = address
        if self._responses:
            return self._responses.pop(0)
        return 1


def test_wait_for_vnc_server_eventually_connects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = [1, 1, 0]

    def fake_socket(*_: object, **__: object) -> _ConnectSocket:
        return _ConnectSocket(responses)

    times = iter([0.0, 0.1, 0.2, 0.3])
    monkeypatch.setattr("ubuntu_gui_testing_runner.vnc.socket.socket", fake_socket)
    monkeypatch.setattr("ubuntu_gui_testing_runner.vnc.time", lambda: next(times))
    monkeypatch.setattr("ubuntu_gui_testing_runner.vnc.sleep", lambda _: None)

    wait_for_vnc_server(5901, timeout_seconds=5)


def test_wait_for_vnc_server_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_socket(*_: object, **__: object) -> _ConnectSocket:
        return _ConnectSocket([1])

    times = iter([0.0, 0.6, 1.2, 1.8, 2.4])
    monkeypatch.setattr("ubuntu_gui_testing_runner.vnc.socket.socket", fake_socket)
    monkeypatch.setattr("ubuntu_gui_testing_runner.vnc.time", lambda: next(times))
    monkeypatch.setattr("ubuntu_gui_testing_runner.vnc.sleep", lambda _: None)

    with pytest.raises(RunnerError):
        wait_for_vnc_server(5901, timeout_seconds=1)
