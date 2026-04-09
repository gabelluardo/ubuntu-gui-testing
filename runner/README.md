# Runner

This directory contains the QEMU + YARF runner used to spawn a VM and execute a Robot Framework test suite over VNC.

## Prerequisites

- Python 3.12+
- `uv`
- `qemu-system-$(uname -m)`
- `qemu-img`
- `yarf`
- Optional (only when using `--tpm`): `swtpm`

## Install

From this directory (`runner/`):

```bash
cd runner
uv sync --group dev
```

## Run

Run via console script:

```bash
uv run ubuntu-gui-testing-runner \
  --iso /path/to/ubuntu.iso \
  --test-suite tests/desktop-installer/
  --suite resolute.entire-disk
```

### Common options

- `--suite`: Run one Robot suite name.
- `--tpm`: Enable software TPM emulation.
- `--cleanup-storage`: Remove created VM disk after run.
- `--disk-path`: Reuse or place VM disk at a specific `.qcow2` path.
- `--archive-dir`: Copy run artifacts (disk, OVMF vars, logs, TPM state) to a directory.
- `--qemu-args-json`: Override QEMU argument template (defaults to `runner/qemu-args.json`).

## Quality checks

Run from `runner/`:

```bash
uv run ruff format .
uv run ruff check .
uv run mypy .
```