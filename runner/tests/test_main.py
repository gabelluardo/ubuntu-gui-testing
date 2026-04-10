from __future__ import annotations

import pytest

import ubuntu_gui_testing_runner.__main__ as mainmod
from ubuntu_gui_testing_runner.config import RunnerError


class _RunnerSuccess:
    def __enter__(self) -> _RunnerSuccess:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return

    def run(self) -> int:
        return 3


class _RunnerError:
    def __enter__(self) -> _RunnerError:
        raise RunnerError("bad runner")

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return


def test_main_exits_with_runner_code(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mainmod, "QemuYarfRunner", _RunnerSuccess)

    with pytest.raises(SystemExit) as exc_info:
        mainmod.main()

    assert exc_info.value.code == 3


def test_main_prints_runner_error_and_exits_1(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(mainmod, "QemuYarfRunner", _RunnerError)

    with pytest.raises(SystemExit) as exc_info:
        mainmod.main()

    captured = capsys.readouterr()
    assert exc_info.value.code == 1
    assert "Error: bad runner" in captured.err
