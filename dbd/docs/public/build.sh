#!/bin/bash
set -u
apt-get install python3-sphinx
pip3 install --upgrade pip urllib3 chardet sphinx sphinx-rtd-theme sphinx-argparse
sphinx-build -M $BUILDER $SOURCE_DIR $INSTALL_DIR
