#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
# -*- coding: utf-8 -*-
import re
import sys
from ttexalens.cli import main
from ttexalens.util import INFO

if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\.pyw|\.exe)?$", "", sys.argv[0])
    INFO("Please use tt-exalens.py instead of tt-lens.py. tt-lens.py will be deprecated in the future.")
    sys.exit(main())
