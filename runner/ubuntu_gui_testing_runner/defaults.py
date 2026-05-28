from __future__ import annotations

from pathlib import Path

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"

DEFAULT_CONNECTION_URI = "qemu:///session"
DEFAULT_POOL_NAME = "ubuntu-gui-testing"
DEFAULT_POOL_DIR = Path("/pool")
DEFAULT_POOL_TEMPLATE = _TEMPLATE_DIR / "pool_template.xml"
DEFAULT_ARTIFACTS_DIR = Path("./artifacts")
DEFAULT_ISO_DOMAIN_TEMPLATE = _TEMPLATE_DIR / "iso_domain_template.xml"
DEFAULT_IMAGE_DOMAIN_TEMPLATE = _TEMPLATE_DIR / "image_domain_template.xml"
DEFAULT_VOLUME_TEMPLATE = _TEMPLATE_DIR / "volume_template.xml"
DEFAULT_OVERLAY_TEMPLATE = _TEMPLATE_DIR / "overlay_template.xml"
DEFAULT_SWTPM_STATE_DIR = Path.home() / ".config/libvirt/qemu/swtpm"
DEFAULT_TEST_USERNAME = "ubuntu"
DEFAULT_TEST_PASSWORD = "ubuntu"  # noqa: S105
