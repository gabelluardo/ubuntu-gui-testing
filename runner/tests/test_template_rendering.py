from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from ubuntu_gui_testing_runner.base import _BaseLibvirtRunner


def test_single_placeholder_is_replaced(tmp_path: Path) -> None:
    template = tmp_path / "template.xml"
    template.write_text("<pool><name>{pool_name}</name></pool>")

    result = _BaseLibvirtRunner._render_template(template, {"pool_name": "my-pool"})
    assert result == "<pool><name>my-pool</name></pool>"


def test_multiple_placeholders_are_replaced(tmp_path: Path) -> None:
    template = tmp_path / "template.xml"
    template.write_text(
        dedent("""\
            <domain>
              <name>{name}</name>
              <disk>{disk}</disk>
            </domain>""")
    )

    result = _BaseLibvirtRunner._render_template(
        template, {"name": "test-domain", "disk": "/pool/test.qcow2"}
    )
    assert "<name>test-domain</name>" in result
    assert "<disk>/pool/test.qcow2</disk>" in result
