#! /bin/bash
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

make clean
make build
make wheel

pip uninstall ttexalens -y
pip install build/ttlens_wheel/*.whl
