#!/usr/bin/bash
# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
#
# covmerge.sh
#
# Capture coverage info in a given directory and generate a HTML report.
# Assumes that the GCOV environment variable points to the cross-compiler's gcov binary.
#
# Usage: ./merge-coverage.sh <gcov_dir> [html_dir]
#

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Usage: $0 <gcov_dir> [html_dir]"
fi

GCOV_DIR="$(realpath "$1")"
HTML_DIR="$(realpath "${2:-cov_html}")"
INFO_PATH="$GCOV_DIR/coverage.info"

if [ ! -d "$GCOV_DIR" ]; then
    echo "merge-coverage: $GCOV_DIR: not a directory"
    exit 1
fi

if [ -z "${GCOV:-}" ]; then
    echo "merge-coverage: GCOV environment variable is not set"
    exit 1
fi

if ! command -v lcov >/dev/null 2>&1; then
    echo "merge-coverage: lcov is not installed"
    exit 1
fi

echo "capturing in $GCOV_DIR"
if ! lcov --gcov-tool "$GCOV" --capture --directory "$GCOV_DIR" \
          --output-file "$INFO_PATH" --rc lcov_branch_coverage=1; then
    echo "merge-coverage: lcov --capture failed"
    exit 1
fi

if [ ! -f "$INFO_PATH" ]; then
    echo "merge-coverage: expected info file $INFO_PATH not created"
    exit 1
fi

mkdir -p "$HTML_DIR"
if ! genhtml --branch-coverage "$INFO_PATH" --output-directory "$HTML_DIR"; then
    echo "merge-coverage: genhtml --branch-coverage failed, trying without the flag..."
    if ! genhtml "$INFO_PATH" --output-directory "$HTML_DIR"; then
        echo "merge-coverage: genhtml failed"
        exit 1
    fi
fi

echo "Done, open $HTML_DIR/index.html"
rm -f "$INFO_PATH"
