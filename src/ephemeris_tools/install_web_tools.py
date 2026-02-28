"""Install bundled web/tools files to a target directory.

Provides the install_ephemeris_tools_files entry point used when the package
is installed via pip. Copies all files from the bundled web/tools tree into
the given directory, preserving subdirectories (e.g. samples/).
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _source_root() -> Path:
    """Return the path to the bundled web/tools directory (ephemeris_tools._web_tools)."""
    from importlib import resources

    return Path(resources.files("ephemeris_tools._web_tools"))


def install_web_tools(dest_dir: Path) -> int:
    """Copy all files from the bundled web/tools into dest_dir.

    Preserves directory structure (e.g. samples/). Skips __init__.py.
    Creates dest_dir and any subdirectories as needed.

    Parameters:
        dest_dir: Target directory to copy files into.

    Returns:
        0 on success, 1 on error.
    """
    src = _source_root()
    if not src.is_dir():
        logger.error("Bundled web/tools source not found at %s", src)
        return 1

    dest_dir = dest_dir.resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    for path in src.rglob("*"):
        if path.is_dir():
            continue
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(src)
        target = dest_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied += 1
        logger.debug("Copied %s -> %s", rel, target)

    logger.info("Copied %d files to %s", copied, dest_dir)
    return 0


def main() -> int:
    """Entry point for the install_ephemeris_tools_files console script."""
    parser = argparse.ArgumentParser(
        description="Copy bundled web/tools files (HTML forms, samples) into a directory.",
        prog="install_ephemeris_tools_files",
    )
    parser.add_argument(
        "dir",
        type=Path,
        help="Target directory to copy web/tools files into (created if missing).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Log each file copied.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    return install_web_tools(args.dir)
