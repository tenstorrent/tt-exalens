#!/bin/sh
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

TT_HOME="$(cd "$(dirname "$0")" && pwd)/.."
CMAKE_BINARY_DIR="$1"

if [ -z "$CMAKE_BINARY_DIR" ]; then
    echo "Usage: $0 <CMAKE_BINARY_DIR>"
    exit 1
fi

REPO=jtag-access-library
REPO_PATH="$TT_HOME/third_party/$REPO"
LIBJTAG="$CMAKE_BINARY_DIR/lib/libjtag.so"
LIBJTAG_SOURCE="$REPO_PATH/out/libjtag.so"
LIBJTAG_DEP="$CMAKE_BINARY_DIR/lib/libjlinkarm.so"
LIBJTAG_DEP_SOURCE="$REPO_PATH/lib/libjlinkarm.so"

if [ ! -d "$REPO_PATH" ]; then
	timeout 60 git clone "git@yyz-gitlab.local.tenstorrent.com:tenstorrent/$REPO" "$REPO_PATH" 2>/dev/null
	if [ ! $? -eq 0 ]; then
		echo "JTAG support not available"
		exit
	fi
fi

cd "$REPO_PATH"
git pull
git lfs pull
make

if ! cmp -s "${LIBJTAG_SOURCE}" "${LIBJTAG}"; then
	cp -f "${LIBJTAG_SOURCE}" "${LIBJTAG}"
fi

if ! cmp -s "${LIBJTAG_DEP_SOURCE}" "${LIBJTAG_DEP}"; then
	cp -f "${LIBJTAG_DEP_SOURCE}" "${LIBJTAG_DEP}"
fi
