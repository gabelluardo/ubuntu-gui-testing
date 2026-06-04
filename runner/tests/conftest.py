from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def templates_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "templates"


@pytest.fixture
def mock_libvirt_connection() -> MagicMock:
    """A mock libvirt connection with sensible defaults."""
    conn = MagicMock()
    conn.lookupByName.side_effect = Exception("domain not found")
    return conn


@pytest.fixture
def mock_libvirt_open(
    mock_libvirt_connection: MagicMock,
) -> Generator[Any, None, None]:
    """Patch libvirt.open to return the mock connection."""
    with patch("libvirt.open", return_value=mock_libvirt_connection) as m:
        yield m
