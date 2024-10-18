#!/bin/sh

REPO=jtag-access-library

if [ ! -d "$REPO" ]; then
    git clone "git@yyz-gitlab.local.tenstorrent.com:tenstorrent/$REPO"
    cd "$REPO"
    make
else
    echo "Repository already exists."
fi
