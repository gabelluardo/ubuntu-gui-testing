"""Module entrypoint for ubuntu_gui_testing_runner."""

from __future__ import annotations

import sys

from ubuntu_gui_testing_runner.config import RunnerError
from ubuntu_gui_testing_runner.runner import QemuYarfRunner


def main() -> None:
    """Entrypoint."""
    try:
        with QemuYarfRunner() as runner:
            code = runner.run()
            sys.exit(code)
    except RunnerError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
