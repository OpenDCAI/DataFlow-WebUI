"""Initialize the DataFlow files the backend reads at runtime."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.core.config import settings
from loguru import logger


_REQUIRED_CORE_DIRS = ("api_pipelines", "example_data")


def dataflow_core_ready(core_dir: Path) -> bool:
    """Return whether a core directory has the minimum usable DataFlow layout."""
    return all((core_dir / name).is_dir() for name in _REQUIRED_CORE_DIRS)


def setup_dataflow_core() -> None:
    """Create a usable core directory with the same interpreter as the backend.

    open-dataflow 1.0.10 registers ``dataflow`` as ``dataflow.cli:app`` and
    deliberately has no ``dataflow.__main__``.  ``python -m dataflow init`` is
    consequently invalid.  Avoiding ``os.system`` and process-wide ``chdir``
    also prevents a failed initialization from being mistaken for success.
    """
    core_dir = Path(settings.DATAFLOW_CORE_DIR)
    core_dir.mkdir(parents=True, exist_ok=True)

    if dataflow_core_ready(core_dir):
        logger.info(f"DataFlow core directory is ready at {core_dir}")
        return

    if any(core_dir.iterdir()):
        raise RuntimeError(
            f"DataFlow core directory is incomplete at {core_dir}; refusing to merge into it. "
            f"Restore {', '.join(_REQUIRED_CORE_DIRS)} or move the incomplete directory aside."
        )

    logger.info(f"Initializing DataFlow core directory at {core_dir}")
    try:
        subprocess.run(
            [sys.executable, "-m", "dataflow.cli", "init"],
            cwd=core_dir,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"DataFlow core initialization failed in {core_dir}. "
            "Fix the active Python environment and retry."
        ) from exc

    if not dataflow_core_ready(core_dir):
        raise RuntimeError(
            f"DataFlow initialization completed but {core_dir} is incomplete; "
            f"expected: {', '.join(_REQUIRED_CORE_DIRS)}"
        )

    logger.info(f"DataFlow core directory initialized at {core_dir}")
