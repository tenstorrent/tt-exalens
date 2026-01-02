# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

sudo apt-get update
sudo apt-get install rsync gdb libyaml-cpp-dev -y
pip install --extra-index-url https://test.pypi.org/simple/ -r ttexalens/requirements.txt
pip install -r test/test_requirements.txt
