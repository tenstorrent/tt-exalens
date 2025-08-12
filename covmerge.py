"""
covmerge.py

Look through the given directory for pairs of .gcno and .gcda files with the same name,
combine them into individual .info files, merge them into a single .info file, and call genhtml.

Assumes that the GCOV environment variable points to the cross-compiler's gcov binary.

You can safely ignore any Perl warnings and, at least for SFPI 6.11.1, the version mismatch warnings.
It's probable that this gcov port will remain valid for the foreseeable future, but it will require
maintenance in case SFPI is updated to an upstream GCC version where the gcda format is changed.

Usage: python covmerge.py <gcov_dir> [html_dir] [info_path]

Arguments:
    gcov_dir - directory containing gcno-gcda pairs (required)
    html_dir - output directory for HTML report (defaults to cov_html)
    info_path - output path for combined .info file (defaults to cov_final.info)

"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
import shutil

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <gcov_dir> [html_dir] [info_path]\n")
        sys.exit(1)

    gcov_dir = Path(sys.argv[1]).resolve()
    html_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "cov_html").resolve()
    info_path = Path(sys.argv[3] if len(sys.argv) > 3 else "cov_final.info").resolve()

    if not gcov_dir.is_dir():
        print(f"covmerge: {gcov_dir}: not a directory")
        sys.exit(1)

    # Intermediate .info files are stored in a temporary directory.
    tmp_root = Path(tempfile.mkdtemp())
    try:
        print(f"covmerge: {gcov_dir}: looking for gcno-gcda pairs...")
        pairs_found = 0

        # Recursively look for .gcda files.
        for gcda in gcov_dir.rglob("*.gcda"):
            gcno = gcda.with_suffix(".gcno")
            if not gcno.exists():
                print(f"covmerge: {gcda}: no matching .gcno, skipped")
                continue

            pairs_found += 1
            base = gcda.stem
            per_info = tmp_root / f"{base}.info"

            # Create a unique .info file in the temp directory.
            counter = 1
            while per_info.exists():
                per_info = tmp_root / f"{base}_{counter}.info"
                counter += 1

            # Run lcov with branch coverage info.
            print(f" - capturing {gcno} + {gcda}")
            subprocess.run(["lcov",
                "--gcov-tool", os.path.expandvars("$GCOV"),
                "--capture",
                "--directory", str(gcda.parent),
                "--output-file", str(per_info),
                "--rc", "lcov_branch_coverage=1"
            ], check=True)

            print(f"  {per_info}: {per_info.exists()}, size={per_info.stat().st_size}")


        if pairs_found == 0:
            print(f"covmerge: {gcov_dir}: no .gcda files found")
            return

        # Get all the individual .info files...
        info_files = sorted(tmp_root.glob("*.info"))
        if not info_files:
            print("covmerge: no .info files were generated")
            sys.exit(1)

        # ... and merge.
        merged_info = tmp_root / "merged.info"
        shutil.copy(info_files[0], merged_info)
        for next_info in info_files[1:]:
            merged_tmp = tmp_root / "merged_tmp.info"
            subprocess.run([
                "lcov", "-a", str(merged_info), "-a", str(next_info),
                "-o", str(merged_tmp), "--rc", "lcov_branch_coverage=1"
            ], check=True)
            merged_info.write_bytes(merged_tmp.read_bytes())

        shutil.copy(merged_info, info_path)
        print(f"covmerge: merged info written to {info_path}")

        # Call genhtml.
        html_dir.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run([
                "genhtml", "--branch-coverage", str(info_path),
                "--output-directory", str(html_dir)
            ], check=True)
        except subprocess.CalledProcessError:
            print("covmerge: genhtml --branch-coverage failed, trying without branch coverage info")
            subprocess.run([
                "genhtml", str(info_path),
                "--output-directory", str(html_dir)
            ], check=True)

        print(f"covmerge: done, open {html_dir / 'index.html'}")

    finally:
        shutil.rmtree(tmp_root)

if __name__ == "__main__":
    main()
