from __future__ import annotations

import pytest

from ubuntu_gui_testing_runner.config import RunnerError
from ubuntu_gui_testing_runner.utils import get_guest_cid, get_vnc_port


class _FakeRandom:
    def shuffle(self, values: list[int]) -> None:
        # Keep deterministic order for tests.
        return


class _FakeSocket:
    def __init__(self, bind_errors: set[int]) -> None:
        self._bind_errors = bind_errors

    def __enter__(self) -> _FakeSocket:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return

    def bind(self, address: tuple[str, int]) -> None:
        if address[1] in self._bind_errors:
            raise OSError("port in use")


def test_get_vnc_port_returns_first_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.utils.secrets.SystemRandom", _FakeRandom
    )

    def fake_socket(*_: object, **__: object) -> _FakeSocket:
        return _FakeSocket({5900, 5901})

    monkeypatch.setattr("ubuntu_gui_testing_runner.utils.socket.socket", fake_socket)

    assert get_vnc_port() == 5902


def test_get_vnc_port_raises_when_all_ports_taken(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.utils.secrets.SystemRandom", _FakeRandom
    )

    def fake_socket(*_: object, **__: object) -> _FakeSocket:
        return _FakeSocket(set(range(5900, 6000)))

    monkeypatch.setattr("ubuntu_gui_testing_runner.utils.socket.socket", fake_socket)

    with pytest.raises(RunnerError):
        get_vnc_port()


def test_get_guest_cid_in_expected_range(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "ubuntu_gui_testing_runner.utils.secrets.randbelow",
        lambda upper: upper - 1,
    )

    cid = get_guest_cid()

    assert 1000 <= cid <= 9999
