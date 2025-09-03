#! /bin/bash
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

make wheel

pip uninstall ttexalens -y
pip install build/ttexalens_wheel/*.whl
