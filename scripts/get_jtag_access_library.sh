#!/bin/sh

REPO=jtag-access-library
REPO_PATH="third_party/$REPO"

if [ ! -d "$REPO_PATH" ]; then
    git clone "git@yyz-gitlab.local.tenstorrent.com:tenstorrent/$REPO" "$REPO_PATH"
    cd "$REPO_PATH"
    make
else
    cd "$REPO_PATH"
    git pull
    make
    cp out/libjtag.so ../../build/lib/libjtag.so
fi
