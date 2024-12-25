#!/bin/sh

TT_HOME="$(cd "$(dirname "$0")" && pwd)/.."
CMAKE_BINARY_DIR="$1"

if [ -z "$CMAKE_BINARY_DIR" ]; then
    echo "Usage: $0 <CMAKE_BINARY_DIR>"
    exit 1
fi

REPO=jtag-access-library
REPO_URL=git@yyz-gitlab.local.tenstorrent.com
REPO_PATH="$TT_HOME/third_party/$REPO"
LIBJTAG="$CMAKE_BINARY_DIR/lib/libjtag.so"
LIBJTAG_SOURCE="$REPO_PATH/out/libjtag.so"
LIBJTAG_DEP="$CMAKE_BINARY_DIR/lib/libjlinkarm.so"
LIBJTAG_DEP_SOURCE="$REPO_PATH/lib/libjlinkarm.so"

if [ ! -d "$REPO_PATH" ]; then
	ssh -o BatchMode=yes -o ConnectTimeout=1 "$REPO_URL" > /dev/null 2>&1
	if [ ! $? -eq 0 ]; then
		echo "JTAG support not available. See docs/ttlens-jtag-tutorial."
		exit
	fi

	git clone "$REPO_URL:tenstorrent/$REPO" "$REPO_PATH" 2>/dev/null
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
