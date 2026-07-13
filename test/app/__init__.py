# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import os
from ttexalens import Verbosity

try:
    Verbosity.set(Verbosity[os.getenv("LOGGER_LEVEL", "ERROR").upper()])
except KeyError:
    Verbosity.set(Verbosity.ERROR)
