# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
"""
covmerge.py

Capture coverage info in a given directory and generate a HTML report.
Assumes that the GCOV environment variable points to the cross-compiler's gcov binary.

Usage: python covmerge.py <gcov_dir> [html_dir]

Arguments:
    gcov_dir - directory containing gcno-gcda pairs
    html_dir - output directory for HTML report (defaults to cov_html)
"""

from pathlib import Path
import os
import sys
import shutil
import subprocess


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <gcov_dir> [html_dir]\n")
        exit(1)

    gcov_dir = Path(sys.argv[1]).resolve()
    html_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "cov_html").resolve()
    info_path = gcov_dir / "coverage.info"

    if not gcov_dir.is_dir():
        print(f"covmerge: {gcov_dir}: not a directory")
        exit(1)

    gcov_tool = os.path.expandvars("$GCOV")
    if not shutil.which(gcov_tool):
        print(f"covmerge: {gcov_tool} not found, ensure GCOV environment variable is set to the cross-compiler gcov")
        exit(1)

    if not shutil.which("lcov"):
        print(f"covmerge: lcov is not installed")
        exit(1)

    print(f"covmerge: capturing coverage in {gcov_dir}")
    try:
        subprocess.run(
            [
                "lcov",
                "--gcov-tool",
                gcov_tool,
                "--capture",
                "--directory",
                str(gcov_dir),
                "--output-file",
                str(info_path),
                "--rc",
                "lcov_branch_coverage=1",
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"covmerge: lcov --capture failed: {e}")
        exit(1)

    if not info_path.exists():
        print(f"covmerge: expected info file {info_path} not created")
        exit(1)

    print(f"covmerge: info written to {info_path}")

    html_dir.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["genhtml", "--branch-coverage", str(info_path), "--output-directory", str(html_dir)], check=True
        )
    except subprocess.CalledProcessError:
        print("covmerge: genhtml --branch-coverage failed, trying without branch coverage flag...")
        try:
            subprocess.run(["genhtml", str(info_path), "--output-directory", str(html_dir)], check=True)
        except subprocess.CalledProcessError as e:
            print(f"covmerge: genhtml failed: {e}")
            exit(1)

    print(f"covmerge: done: open {html_dir / 'index.html'}")

    try:
        info_path.unlink()
        print(f"covmerge: deleted {info_path}")
    except Exception as e:
        print(f"covmerge: failed to delete {info_path}: {e}")


if __name__ == "__main__":
    main()
