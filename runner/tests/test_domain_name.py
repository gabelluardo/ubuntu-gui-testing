from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import libvirt  # type: ignore[import-untyped]

from ubuntu_gui_testing_runner.base import _BaseLibvirtRunner


class _FakeRunner(_BaseLibvirtRunner):
    """Minimal concrete subclass for testing base class behaviour."""

    def _setup(self) -> None:
        pass

    async def _run_yarf(
        self, suite: str, test: str, vsock_cid: int, vnc_port: int
    ) -> None:
        pass


def _make_conn_with_existing_domains(names: list[str]) -> MagicMock:
    conn = MagicMock()

    def lookup(name: str) -> MagicMock:
        if name in names:
            return MagicMock()
        raise libvirt.libvirtError("not found")

    conn.lookupByName.side_effect = lookup
    return conn


def test_domain_name_includes_suite_test_and_date() -> None:
    conn = _make_conn_with_existing_domains([])
    today = date.today().isoformat()
    expected = f"ugt-desktop-installer-resolute.entire-disk-{today}"

    with patch("libvirt.open", return_value=conn):
        runner = _FakeRunner(
            suite_name="desktop-installer",
            test_name="resolute.entire-disk",
        )
        try:
            assert runner.domain_name == expected
        finally:
            runner.close()


def test_domain_name_appends_suffix_on_collision() -> None:
    today = date.today().isoformat()
    base = f"ugt-desktop-installer-resolute.entire-disk-{today}"
    existing = [base]
    conn = _make_conn_with_existing_domains(existing)

    with patch("libvirt.open", return_value=conn):
        runner = _FakeRunner(
            suite_name="desktop-installer",
            test_name="resolute.entire-disk",
        )
        try:
            assert runner.domain_name == f"{base}-2"
        finally:
            runner.close()


def test_domain_name_increments_suffix_until_unique() -> None:
    today = date.today().isoformat()
    base = f"ugt-desktop-installer-resolute.entire-disk-{today}"
    existing = [base, f"{base}-2", f"{base}-3"]
    conn = _make_conn_with_existing_domains(existing)

    with patch("libvirt.open", return_value=conn):
        runner = _FakeRunner(
            suite_name="desktop-installer",
            test_name="resolute.entire-disk",
        )
        try:
            assert runner.domain_name == f"{base}-4"
        finally:
            runner.close()
