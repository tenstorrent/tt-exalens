#!/bin/sh

REPO=jtag-access-library
REPO_PATH="third_party/$REPO"

if [ ! -d "$REPO_PATH" ]; then
    git clone "git@yyz-gitlab.local.tenstorrent.com:tenstorrent/$REPO" "$REPO_PATH"
else
    cd "$REPO_PATH"
    git pull
fi
