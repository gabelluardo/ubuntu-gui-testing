from __future__ import annotations

from textwrap import dedent

from ubuntu_gui_testing_runner.base import _BaseLibvirtRunner

DOMAIN_XML_WITH_VNC_AND_VSOCK = dedent("""\
    <domain type="kvm">
      <name>test</name>
      <devices>
        <graphics type="vnc" port="5901" autoport="yes">
          <listen type="address"/>
        </graphics>
        <vsock model="virtio">
          <cid auto="yes" address="42"/>
        </vsock>
      </devices>
    </domain>
""")

DOMAIN_XML_WITHOUT_VNC = dedent("""\
    <domain type="kvm">
      <name>test</name>
      <devices>
        <vsock model="virtio">
          <cid auto="yes" address="42"/>
        </vsock>
      </devices>
    </domain>
""")

DOMAIN_XML_WITHOUT_VSOCK = dedent("""\
    <domain type="kvm">
      <name>test</name>
      <devices>
        <graphics type="vnc" port="5901" autoport="yes">
          <listen type="address"/>
        </graphics>
      </devices>
    </domain>
""")


def test_extracts_vnc_port() -> None:
    vnc_port, _ = _BaseLibvirtRunner._extract_domain_runtime_info(
        DOMAIN_XML_WITH_VNC_AND_VSOCK
    )
    assert vnc_port == 5901


def test_extracts_vsock_cid() -> None:
    _, vsock_cid = _BaseLibvirtRunner._extract_domain_runtime_info(
        DOMAIN_XML_WITH_VNC_AND_VSOCK
    )
    assert vsock_cid == 42


def test_returns_none_when_vnc_missing() -> None:
    vnc_port, _ = _BaseLibvirtRunner._extract_domain_runtime_info(
        DOMAIN_XML_WITHOUT_VNC
    )
    assert vnc_port is None


def test_returns_none_when_vsock_missing() -> None:
    _, vsock_cid = _BaseLibvirtRunner._extract_domain_runtime_info(
        DOMAIN_XML_WITHOUT_VSOCK
    )
    assert vsock_cid is None
