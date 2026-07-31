"""Tests for the DataFlow core bootstrap used by both profiles at runtime."""

from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace

import pytest

from app.core import dataflow_setup


def _set_core_dir(monkeypatch: pytest.MonkeyPatch, core_dir) -> None:
    monkeypatch.setattr(
        dataflow_setup,
        "settings",
        SimpleNamespace(DATAFLOW_CORE_DIR=str(core_dir)),
    )


def test_dataflow_core_ready_requires_the_runtime_directories(tmp_path):
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "api_pipelines").mkdir()

    assert dataflow_setup.dataflow_core_ready(core_dir) is False

    (core_dir / "example_data").mkdir()
    assert dataflow_setup.dataflow_core_ready(core_dir) is True


def test_setup_uses_the_backend_interpreter_and_verifies_output(monkeypatch, tmp_path):
    core_dir = tmp_path / "core"
    _set_core_dir(monkeypatch, core_dir)
    calls = []

    def fake_run(command, *, cwd, check):
        calls.append((command, cwd, check))
        (cwd / "api_pipelines").mkdir()
        (cwd / "example_data").mkdir()

    monkeypatch.setattr(dataflow_setup.subprocess, "run", fake_run)

    dataflow_setup.setup_dataflow_core()

    assert calls == [
        ([sys.executable, "-m", "dataflow.cli", "init"], core_dir, True)
    ]
    assert dataflow_setup.dataflow_core_ready(core_dir)


def test_setup_refuses_a_partial_directory(monkeypatch, tmp_path):
    core_dir = tmp_path / "core"
    core_dir.mkdir()
    (core_dir / "leftover.txt").write_text("partial", encoding="utf-8")
    _set_core_dir(monkeypatch, core_dir)

    def must_not_run(*_args, **_kwargs):
        raise AssertionError("an incomplete core must not be merged into")

    monkeypatch.setattr(dataflow_setup.subprocess, "run", must_not_run)

    with pytest.raises(RuntimeError, match="incomplete"):
        dataflow_setup.setup_dataflow_core()


def test_setup_surfaces_dataflow_cli_failure(monkeypatch, tmp_path):
    core_dir = tmp_path / "core"
    _set_core_dir(monkeypatch, core_dir)

    def fake_run(command, *, cwd, check):
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr(dataflow_setup.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="initialization failed"):
        dataflow_setup.setup_dataflow_core()
